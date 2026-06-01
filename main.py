#!/usr/bin/env python3
"""
JoeMoyo Business Agent System
==============================
AI agents for your YouTube channels, music studio, and Shopify store.

Usage:
  python main.py history  --topic "The Fall of Constantinople"
  python main.py finance  --topic "Bitcoin ETF Analysis"
  python main.py shopify  --report weekly
  python main.py leads    --type studio --name "Artist Name" --genre "R&B"
  python main.py leads    --type sponsor --name "Brand Name" --channel history
  python main.py market   --brand history_channel --topic "New video out now"
  python main.py ideas    --weeks 4
"""

import sys
import click
from rich.console import Console
from rich.panel import Panel

console = Console()


def get_orchestrator():
    """Lazy-load orchestrator to show errors clearly."""
    try:
        from orchestrator.orchestrator import BusinessOrchestrator
        return BusinessOrchestrator()
    except EnvironmentError as e:
        console.print(f"[bold red]Setup Error:[/bold red] {e}")
        console.print("\n[dim]Steps to fix:")
        console.print("  1. Copy .env.example to .env")
        console.print("  2. Add your ANTHROPIC_API_KEY")
        console.print("  3. Run the command again[/dim]")
        sys.exit(1)


@click.group()
def cli():
    """
    \b
    JoeMoyo Business Agent System
    Powered by Claude AI
    """
    console.print(Panel(
        "[bold cyan]JoeMoyo Business Agent System[/bold cyan]\n"
        "[dim]Powered by Claude claude-sonnet-4-6[/dim]",
        style="cyan",
        padding=(0, 2),
    ))


# ------------------------------------------------------------------ #
#  HISTORY CHANNEL                                                     #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--topic", "-t",
    required=True,
    help='Historical topic (e.g. "The Fall of Rome")',
)
@click.option(
    "--script-only",
    is_flag=True,
    help="Skip research, write script from Claude knowledge only",
)
def history(topic: str, script_only: bool):
    """
    Produce a complete historical YouTube video package.

    Runs: Research → Script → Social Media Bundle
    Outputs saved to outputs/scripts/ and outputs/marketing/
    """
    orch = get_orchestrator()
    if script_only:
        console.print(f"[bold]Writing script for:[/bold] {topic}")
        result = orch.script_history.write_script(topic_or_research=topic)
        console.print(result)
    else:
        result = orch.produce_history_video(topic)
        console.print(f"\n[bold green]Done![/bold green] Script: {len(result['script'].split())} words")


# ------------------------------------------------------------------ #
#  FINANCE CHANNEL                                                     #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--topic", "-t",
    required=True,
    help='Financial topic (e.g. "Bitcoin ETF Analysis")',
)
@click.option(
    "--ideas-only",
    is_flag=True,
    help="Generate video ideas instead of a full analysis",
)
@click.option(
    "--count",
    default=10,
    show_default=True,
    help="Number of ideas to generate (used with --ideas-only)",
)
def finance(topic: str, ideas_only: bool, count: int):
    """
    Produce financial YouTube content.

    Runs: Financial Research → Script → Social Media Bundle
    Or: Generate video ideas list (with --ideas-only)
    """
    orch = get_orchestrator()
    if ideas_only:
        console.print(f"[bold]Generating {count} video ideas for:[/bold] {topic}")
        result = orch.financial_agent.generate_video_ideas(niche=topic, count=count)
        console.print(result)
    else:
        result = orch.produce_finance_video(topic)
        console.print(f"\n[bold green]Done![/bold green] Script: {len(result['script'].split())} words")


# ------------------------------------------------------------------ #
#  SHOPIFY REPORTING                                                   #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--report", "-r",
    default="weekly",
    type=click.Choice(["weekly", "monthly"]),
    show_default=True,
    help="Report type",
)
def shopify(report: str):
    """
    Generate Shopify store performance reports.

    Requires: SHOPIFY_SHOP_NAME and SHOPIFY_ACCESS_TOKEN in .env
    Outputs saved to outputs/reports/
    """
    orch = get_orchestrator()
    try:
        if report == "weekly":
            result = orch.weekly_shopify_report()
        else:
            result = orch.monthly_shopify_report()
        console.print(result)
    except EnvironmentError as e:
        console.print(f"[bold red]Shopify Error:[/bold red] {e}")
        sys.exit(1)


# ------------------------------------------------------------------ #
#  LEAD GENERATION                                                     #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--type", "lead_type",
    required=True,
    type=click.Choice(["studio", "sponsor"]),
    help="studio = music studio client | sponsor = YouTube sponsorship",
)
@click.option("--name", "-n", required=True, help="Prospect/brand name")
@click.option("--genre", default="", help="Music genre (for studio leads)")
@click.option("--followers", default="", help="Social media following size")
@click.option("--industry", default="", help="Industry (for sponsorship leads)")
@click.option(
    "--channel",
    default="history_channel",
    type=click.Choice(["history_channel", "finance_channel"]),
    help="Which channel to pitch for (sponsor only)",
)
def leads(lead_type: str, name: str, genre: str, followers: str, industry: str, channel: str):
    """
    Generate sales outreach sequences.

    For music studio: cold email sequence to book recording clients.
    For sponsors: YouTube sponsorship pitch package.

    Outputs saved to outputs/leads/
    """
    orch = get_orchestrator()
    if lead_type == "studio":
        prospect = {"name": name, "genre": genre, "followers": followers}
        result = orch.studio_outreach(prospect)
    else:
        brand_info = {"name": name, "industry": industry}
        result = orch.sponsorship_pitch(brand_info, channel=channel)
    console.print(result)


# ------------------------------------------------------------------ #
#  MARKETING CONTENT                                                   #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--brand", "-b",
    required=True,
    type=click.Choice(["history_channel", "finance_channel", "music_studio", "shopify_store"]),
    help="Which brand to create content for",
)
@click.option("--topic", "-t", required=True, help="Content topic or angle")
@click.option(
    "--type", "content_type",
    default="social",
    type=click.Choice(["social", "email", "ads"]),
    show_default=True,
    help="Type of content to generate",
)
def market(brand: str, topic: str, content_type: str):
    """
    Generate marketing content for any brand.

    social = Social media bundle (all platforms)
    email  = Full email newsletter
    ads    = Ad copy variations

    Outputs saved to outputs/marketing/
    """
    orch = get_orchestrator()
    if content_type == "social":
        result = orch.marketing_agent.create_social_bundle(brand, topic)
    elif content_type == "email":
        result = orch.marketing_agent.write_email_newsletter(brand, topic)
    else:
        result = orch.marketing_agent.write_ad_copy(brand, topic)
    console.print(result)


# ------------------------------------------------------------------ #
#  CONTENT CALENDAR                                                    #
# ------------------------------------------------------------------ #

@cli.command()
@click.option(
    "--weeks", "-w",
    default=4,
    show_default=True,
    help="Number of weeks to plan",
)
def ideas(weeks: int):
    """
    Generate a content ideas calendar for all YouTube channels.

    Outputs video ideas for both history and finance channels.
    Outputs saved to outputs/scripts/
    """
    orch = get_orchestrator()
    result = orch.generate_content_calendar(weeks=weeks)
    console.print("\n[bold]HISTORY CHANNEL IDEAS[/bold]")
    console.print(result["history_channel_ideas"])
    console.print("\n[bold]FINANCE CHANNEL IDEAS[/bold]")
    console.print(result["finance_channel_ideas"])


# ------------------------------------------------------------------ #
#  VIDEO PRODUCTION CREW                                              #
# ------------------------------------------------------------------ #

def get_video_producer(channel: str):
    """Lazy-load the video producer with clear setup errors."""
    try:
        from orchestrator.video_producer import VideoProducer
        return VideoProducer(channel=channel)
    except EnvironmentError as e:
        console.print(f"[bold red]Setup Error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.option("--topic", "-t", default=None, help='Video topic (e.g. "Great Zimbabwe")')
@click.option("--from-idea", "from_idea", default=None,
              help="Produce from a content_ideas backlog id (topic optional)")
@click.option(
    "--channel", "-c",
    default="history_channel",
    type=click.Choice(["history_channel", "finance_channel"]),
    show_default=True,
    help="Which channel preset/voice to use",
)
@click.option("--minutes", "-m", default=12, show_default=True, help="Target runtime (minutes)")
@click.option("--no-research", is_flag=True, help="Skip web research; script from the topic/archive only")
@click.option("--render", is_flag=True, help="Render the finished mp4 (needs narration audio)")
@click.option(
    "--engine",
    default="remotion",
    type=click.Choice(["remotion", "ffmpeg"]),
    show_default=True,
    help="Render engine (falls back to ffmpeg if Remotion isn't set up)",
)
def produce(topic, from_idea, channel, minutes, no_research, render, engine):
    """
    Run the full video production crew for a topic.

    Research -> Script -> Packaging -> Thumbnail -> Visuals -> Voiceover ->
    Motion -> Manifest, persisted to Supabase and materialized to
    outputs/videos/. Pull the topic from your backlog with --from-idea, or
    pass --topic directly. Use --render to also produce the mp4.
    """
    if not topic and not from_idea:
        raise click.UsageError("Provide --topic or --from-idea.")
    producer = get_video_producer(channel)
    result = producer.produce(
        topic, from_idea_id=from_idea, target_minutes=minutes,
        do_research=not no_research, render=render, engine=engine,
    )
    console.print(f"\n[bold green]Done![/bold green] Package: {result['package_dir']}")
    if result.get("episode_id"):
        console.print(f"Supabase episode: {result['episode_id']}")


@cli.command()
@click.option("--status", default=None, help="Filter by status (idea/researching/scripting/production)")
@click.option("--limit", "-n", default=20, show_default=True, help="How many ideas to show")
def backlog(status, limit):
    """List content_ideas from the archive (highest estimated views first)."""
    from tools import supabase_client as sb
    ideas = sb.list_content_ideas(status=status, limit=limit)
    if not ideas:
        console.print(f"[yellow]{sb.unavailable_reason() or 'No ideas found.'}[/yellow]")
        return
    from rich.table import Table
    table = Table(title="Content backlog")
    table.add_column("id", style="dim", no_wrap=True)
    table.add_column("title")
    table.add_column("status")
    table.add_column("est. views", justify="right")
    for i in ideas:
        table.add_row(i["id"], i.get("title", ""), i.get("status", ""),
                      str(i.get("estimated_views") or ""))
    console.print(table)
    console.print("\n[dim]Produce one with:[/dim] python main.py produce --from-idea <id>")


@cli.command(name="embed-archive")
@click.option("--batch-size", default=64, show_default=True, help="Texts per OpenAI call")
@click.option("--max-rows", default=None, type=int, help="Stop after N rows (default: drain all)")
def embed_archive(batch_size, max_rows):
    """Drain embedding_queue: embed pending rows so the archive is searchable.

    Needs OPENAI_API_KEY + SUPABASE_*. Safe to re-run; only 'pending' rows are
    processed. This calls the OpenAI embeddings API (small per-row cost).
    """
    from tools import supabase_client as sb
    console.print("[bold]Embedding the ORIGINEX archive...[/bold]")
    result = sb.drain_embedding_queue(
        batch_size=batch_size, max_rows=max_rows,
        progress=lambda d, f: console.print(f"  embedded={d} failed={f}", end="\r"),
    )
    if result.get("error"):
        console.print(f"[red]{result['error']}[/red]")
    else:
        console.print(f"\n[green]Done — embedded {result['done']}, failed {result['failed']}.[/green]")


@cli.command()
@click.argument("episode_id")
@click.option(
    "--channel", "-c",
    default="history_channel",
    type=click.Choice(["history_channel", "finance_channel"]),
)
def materialize(episode_id, channel):
    """Re-export an existing episode's package folder from Supabase."""
    producer = get_video_producer(channel)
    producer.materialize(episode_id)


if __name__ == "__main__":
    cli()
