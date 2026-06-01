"""VideoProducer: the Director that runs the video production crew end-to-end.

Deterministic Python (like BusinessOrchestrator) that sequences the role
agents, persists every stage to Supabase (source of truth), generates media
when API keys are present, materializes a self-contained package folder, and
optionally renders the finished mp4.

Pipeline: research -> script -> packaging -> thumbnail -> visual shot list ->
voiceover -> motion graphics -> manifest/editor -> (images, narration) ->
render.
"""

from __future__ import annotations

import json
import os

from rich.console import Console
from rich.panel import Panel

from agents.content_research import ContentResearchAgent
from agents.script_writer import ScriptWriterAgent
from agents.video._utils import slugify
from agents.video.manifest_editor import ManifestEditorAgent
from agents.video.motion_graphics import MotionGraphicsAgent
from agents.video.thumbnail import ThumbnailAgent
from agents.video.title_packaging import TitlePackagingAgent
from agents.video.visual_director import VisualDirectorAgent
from agents.video.voiceover import VoiceoverAgent
from config.settings import settings
from tools import supabase_client as sb

console = Console()


class VideoProducer:
    """Top-level director for the JoeMoyo video production crew."""

    def __init__(self, channel: str = "history_channel"):
        self.channel = channel
        self.research_agent = ContentResearchAgent()
        self.script_agent = ScriptWriterAgent(channel=channel)
        self.packaging_agent = TitlePackagingAgent(channel=channel)
        self.thumbnail_agent = ThumbnailAgent(channel=channel)
        self.visual_agent = VisualDirectorAgent(channel=channel)
        self.motion_agent = MotionGraphicsAgent(channel=channel)
        self.voiceover_agent = VoiceoverAgent(channel=channel)
        self.editor = ManifestEditorAgent(crossfade=1.0)

    # ------------------------------------------------------------------ #
    #  Main pipeline                                                       #
    # ------------------------------------------------------------------ #
    def produce(
        self,
        topic: str | None = None,
        *,
        from_idea_id: str | None = None,
        target_minutes: float = 12,
        do_research: bool = True,
        render: bool = False,
        engine: str = "remotion",
    ) -> dict:
        # Resolve the topic from a backlog idea, if given.
        content_idea_id = None
        idea_related: dict[str, list[str]] = {}
        if from_idea_id:
            idea = sb.get_content_idea(from_idea_id)
            if not idea:
                raise ValueError(f"content idea {from_idea_id} not found (or no Supabase).")
            content_idea_id = idea["id"]
            topic = topic or idea["title"]
            for k in ("related_documents", "related_people", "related_events"):
                if idea.get(k):
                    idea_related[k] = idea[k]
            console.print(f"[dim]From backlog idea: {idea['title']}[/dim]")
        if not topic:
            raise ValueError("produce() needs a topic or a from_idea_id.")

        console.print(Panel(
            f"[bold]Video Production Crew[/bold]\nTopic: {topic}\nChannel: {self.channel}",
            style="blue",
        ))

        slug = slugify(topic)
        pkg_dir = self._make_package_dir(slug)
        img_dir = os.path.join(pkg_dir, "img")
        os.makedirs(img_dir, exist_ok=True)

        # --- Archive context (semantic + name-match) -------------------
        archive_ctx, related = sb.archive_context(topic)
        for k, v in idea_related.items():  # merge idea links with discovered ones
            related.setdefault(k, [])
            related[k] = list(dict.fromkeys(related[k] + v))

        # --- Episode row (source of truth) -----------------------------
        episode = sb.create_episode(
            title=topic, slug=f"{slug}-{os.path.basename(pkg_dir)[-6:]}",
            channel=self.channel, topic=topic, target_minutes=target_minutes,
            content_idea_id=content_idea_id, related=related or None,
        )
        episode_id = episode["id"] if episode else None
        if episode_id:
            console.print(f"[dim]Supabase episode {episode_id}[/dim]")
            if content_idea_id:
                sb.set_content_idea_status(content_idea_id, "production")
        else:
            console.print(f"[yellow]{sb.unavailable_reason() or 'No DB'} — specs-only.[/yellow]")

        # --- 1. Research (archive + web) --------------------------------
        self._step(1, "Research")
        sb.set_episode_status(episode_id, "researching") if episode_id else None
        research_input = topic if not archive_ctx else (
            f"{topic}\n\nKNOWN ARCHIVE FACTS (cite these where relevant):\n{archive_ctx}"
        )
        if do_research:
            research = self.research_agent.research_topic(research_input)["research"]
        else:
            research = research_input
        self._write(pkg_dir, "research.md", research)
        self._persist(episode_id, "research", content_md=research)

        # --- 2. Script --------------------------------------------------
        self._step(2, "Script")
        sb.set_episode_status(episode_id, "scripting") if episode_id else None
        script = self.script_agent.write_script(research, target_minutes=int(target_minutes))
        self._write(pkg_dir, "script.md", script)
        self._persist(episode_id, "script", content_md=script)

        # --- 3. Packaging ----------------------------------------------
        self._step(3, "Packaging / SEO")
        packaging = self.packaging_agent.create_packaging(script)
        self._write_json(pkg_dir, "packaging.json", packaging)
        self._persist(episode_id, "packaging", payload=packaging)

        # --- 4. Thumbnail ----------------------------------------------
        self._step(4, "Thumbnail")
        thumbnail = self.thumbnail_agent.design(topic, script)
        self._write_json(pkg_dir, "thumbnail.json", thumbnail)
        self._persist(episode_id, "thumbnail", payload=thumbnail)

        # --- 5. Visual shot list ---------------------------------------
        self._step(5, "Visual shot list")
        sb.set_episode_status(episode_id, "visualizing") if episode_id else None
        shotlist = self.visual_agent.build_shotlist(script, target_minutes=target_minutes)
        self._write_json(pkg_dir, "shotlist.json", shotlist)
        self._persist(episode_id, "visual", payload=shotlist)

        # --- 6. Voiceover ----------------------------------------------
        self._step(6, "Voiceover (narration)")
        sb.set_episode_status(episode_id, "voicing") if episode_id else None
        narration = self.voiceover_agent.prepare_narration(script)
        self._write(pkg_dir, "narration.txt", narration)
        narration_mp3 = os.path.join(pkg_dir, "narration.mp3")
        synthed = self.voiceover_agent.synthesize(narration, narration_mp3)
        narration_seconds = self._narration_seconds(synthed, narration)
        self._persist(episode_id, "voiceover",
                      payload={"seconds": narration_seconds, "synthesized": bool(synthed)},
                      content_md=narration)
        if synthed and episode_id:
            sb.upload_asset(episode_id, synthed, kind="narration", content_type="audio/mpeg")

        # --- 7. Motion graphics ----------------------------------------
        self._step(7, "Motion graphics")
        motion = self.motion_agent.build_props(script, packaging)
        self._write_json(pkg_dir, "motion.json", motion)
        self._persist(episode_id, "motion", payload=motion)

        # --- 8. Manifest / editor --------------------------------------
        self._step(8, "Edit / assemble manifest")
        sb.set_episode_status(episode_id, "assembling") if episode_id else None
        assembled = self.editor.assemble(shotlist, narration_seconds)
        self._write_json(pkg_dir, "manifest.json", assembled["manifest"])
        self._write(pkg_dir, "captions.srt", assembled["srt"])

        # --- 9. Generate stills (if configured) ------------------------
        self._step(9, "Generate stills")
        generated = self._generate_images(assembled["image_plan"], img_dir, episode_id)

        # --- 10. Generate thumbnail image (if configured) --------------
        thumb_path = self._generate_thumbnail(thumbnail, pkg_dir, episode_id)

        # --- 11. Remotion props + persist manifest ---------------------
        remotion_props = self._build_remotion_props(
            assembled["manifest"], motion, narration_mp3 if synthed else None,
            assembled["srt"], img_dir,
        )
        self._write_json(pkg_dir, "remotion-props.json", remotion_props)
        if episode_id:
            sb.upsert_manifest(
                episode_id, manifest=assembled["manifest"],
                remotion_props=remotion_props, srt=assembled["srt"],
            )
        self._persist(episode_id, "manifest", payload={"manifest": assembled["manifest"]})

        # --- 12. Render (optional) -------------------------------------
        out_mp4 = None
        if render:
            self._step(12, f"Render ({engine})")
            out_mp4 = self._render(
                engine, remotion_props, assembled["manifest"], img_dir,
                narration_mp3 if synthed else None, assembled["srt"], pkg_dir, episode_id,
            )

        # --- Package index ---------------------------------------------
        index = {
            "topic": topic, "channel": self.channel, "slug": slug,
            "episode_id": episode_id, "target_minutes": target_minutes,
            "narration_seconds": narration_seconds, "images_generated": generated,
            "thumbnail": thumb_path, "rendered": out_mp4, "package_dir": pkg_dir,
        }
        self._write_json(pkg_dir, "package.json", index)
        if episode_id:
            sb.set_episode_status(episode_id, "rendered" if out_mp4 else "assembling")

        console.print(Panel(
            f"[bold green]Package ready[/bold green]\n{pkg_dir}",
            style="green",
        ))
        return index

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #
    def _make_package_dir(self, slug: str) -> str:
        from datetime import datetime
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(settings.video_output_dir, f"{self.channel}_{slug}_{stamp}")
        os.makedirs(path, exist_ok=True)
        return path

    def _step(self, n: int, label: str) -> None:
        console.print(f"\n[bold][Step {n}/12][/bold] {label}...")

    def _write(self, pkg_dir: str, name: str, content: str) -> None:
        with open(os.path.join(pkg_dir, name), "w", encoding="utf-8") as f:
            f.write(content or "")

    def _write_json(self, pkg_dir: str, name: str, data) -> None:
        with open(os.path.join(pkg_dir, name), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _persist(self, episode_id, role, *, payload=None, content_md=None) -> None:
        if episode_id:
            sb.save_agent_output(episode_id, role, payload=payload, content_md=content_md)

    def _narration_seconds(self, mp3_path: str | None, narration: str) -> float:
        if mp3_path and os.path.exists(mp3_path):
            try:
                from video_agent.audio import probe_duration
                from pathlib import Path
                return float(probe_duration(Path(mp3_path)))
            except Exception:
                pass
        # Estimate ~150 spoken words per minute.
        words = len(narration.split())
        return round(words / 150 * 60, 1) if words else 0.0

    def _generate_images(self, image_plan: list[dict], img_dir: str, episode_id) -> int:
        from tools.images import generate_image, is_configured
        if not is_configured():
            console.print("[dim]No image provider configured — prompts saved only.[/dim]")
            return 0
        count = 0
        for i, item in enumerate(image_plan, start=1):
            prompt = item.get("image_prompt", "")
            if not prompt:
                continue
            out = os.path.join(img_dir, item["image"])
            try:
                if generate_image(prompt, out):
                    count += 1
                    if episode_id:
                        sb.upload_asset(episode_id, out, kind="image", sequence=i,
                                        prompt=prompt, content_type="image/png")
            except Exception as e:
                console.print(f"[yellow]image {i} failed: {e}[/yellow]")
        console.print(f"[green]Generated {count} stills[/green]")
        return count

    def _generate_thumbnail(self, thumbnail: dict, pkg_dir: str, episode_id) -> str | None:
        from tools.images import generate_image, is_configured
        prompt = thumbnail.get("image_prompt")
        if not (prompt and is_configured()):
            return None
        out = os.path.join(pkg_dir, "thumbnail.png")
        try:
            if generate_image(prompt, out, size="1536x1024"):
                if episode_id:
                    sb.upload_asset(episode_id, out, kind="thumbnail",
                                    prompt=prompt, content_type="image/png")
                return out
        except Exception as e:
            console.print(f"[yellow]thumbnail failed: {e}[/yellow]")
        return None

    def _build_remotion_props(self, manifest, motion, narration_path, srt, img_dir) -> dict:
        clips = []
        for c in manifest["clips"]:
            clips.append({
                "src": os.path.join(img_dir, c["image"]),
                "duration": c["duration"],
                "pan": c["pan"],
                "caption": c.get("caption", ""),
            })
        return {
            "fps": 30, "width": 1920, "height": 1080,
            "narrationUrl": narration_path,
            "srt": srt,
            "clips": clips,
            "intro": motion.get("intro"),
            "lowerThirds": motion.get("lower_thirds", []),
            "statCards": motion.get("stat_cards", []),
            "quoteCards": motion.get("quote_cards", []),
            "outro": motion.get("outro"),
        }

    def _render(self, engine, props, manifest, img_dir, narration_path, srt, pkg_dir, episode_id):
        out = os.path.join(pkg_dir, "out.mp4")
        job = sb.create_render_job(episode_id, engine) if episode_id else None
        job_id = job["id"] if job else None
        if episode_id:
            sb.set_episode_status(episode_id, "rendering")
        try:
            result = None
            if engine == "remotion":
                from tools.remotion import render as remotion_render, is_available
                if is_available():
                    result = remotion_render(props, out)
                else:
                    console.print("[yellow]Remotion project not set up — trying ffmpeg.[/yellow]")
            if result is None:
                result = self._render_ffmpeg(manifest, img_dir, narration_path, srt, out)
            if job_id:
                sb.finish_render_job(job_id, status="succeeded" if result else "failed",
                                     out_path=result)
            if result and episode_id:
                sb.upload_asset(episode_id, result, kind="mp4", content_type="video/mp4")
            return result
        except Exception as e:
            console.print(f"[red]Render failed: {e}[/red]")
            if job_id:
                sb.finish_render_job(job_id, status="failed", logs=str(e))
            return None

    def _render_ffmpeg(self, manifest, img_dir, narration_path, srt, out):
        if not narration_path:
            console.print("[yellow]No narration audio — cannot ffmpeg-render. "
                          "Set ELEVENLABS_API_KEY/VOICE_ID.[/yellow]")
            return None
        from video_agent.channels import get_preset
        from video_agent.pipeline import plan_render, render
        from video_agent.utils.manifest import parse_manifest
        srt_path = None
        if srt:
            srt_path = out.replace("out.mp4", "captions.srt")
        preset = get_preset(self.channel.replace("_channel", ""))  # 'history' / 'finance'
        plan = plan_render(
            preset=preset, images_dir=img_dir, narration=narration_path,
            output=out, captions_srt=srt_path, manifest=parse_manifest(manifest),
        )
        return str(render(plan))

    # ------------------------------------------------------------------ #
    #  Re-export an episode's package from Supabase                        #
    # ------------------------------------------------------------------ #
    def materialize(self, episode_id: str) -> str | None:
        """Rebuild a package folder for an existing episode from Supabase."""
        episode = sb.get_episode(episode_id)
        if not episode:
            console.print("[red]Episode not found (or Supabase not configured).[/red]")
            return None
        pkg_dir = self._make_package_dir(episode["slug"])
        client = sb.get_client()
        outputs = client.table("video_agent_outputs").select("*").eq(
            "episode_id", episode_id).order("created_at").execute().data
        for row in outputs:
            if row.get("content_md"):
                self._write(pkg_dir, f"{row['role']}.md", row["content_md"])
            if row.get("payload"):
                self._write_json(pkg_dir, f"{row['role']}.json", row["payload"])
        man = client.table("video_manifest").select("*").eq(
            "episode_id", episode_id).limit(1).execute().data
        if man:
            self._write_json(pkg_dir, "manifest.json", man[0].get("manifest") or {})
            self._write_json(pkg_dir, "remotion-props.json", man[0].get("remotion_props") or {})
            self._write(pkg_dir, "captions.srt", man[0].get("srt") or "")
        console.print(Panel(f"[green]Materialized → {pkg_dir}[/green]", style="green"))
        return pkg_dir
