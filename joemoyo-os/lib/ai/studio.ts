import { Brand, brandContext } from "@/lib/brands";
import { runProvider } from "@/lib/ai/providers";
import { ProviderId } from "@/lib/ai/types";

export type StudioTask = "script" | "titles" | "thumbnails" | "repurpose" | "calendar";

export interface StudioTaskMeta {
  id: StudioTask;
  label: string;
  icon: string;
  needsTopic: boolean;
  placeholder: string;
}

export const STUDIO_TASKS: StudioTaskMeta[] = [
  { id: "script", label: "Script", icon: "📝", needsTopic: true, placeholder: "Video topic, e.g. The Fall of Constantinople" },
  { id: "titles", label: "Titles & Hooks", icon: "🎯", needsTopic: true, placeholder: "Video topic to brainstorm titles for" },
  { id: "thumbnails", label: "Thumbnails", icon: "🖼️", needsTopic: true, placeholder: "Video topic for thumbnail concepts" },
  { id: "repurpose", label: "Repurpose", icon: "♻️", needsTopic: true, placeholder: "Topic or paste a script to repurpose" },
  { id: "calendar", label: "Calendar", icon: "🗓️", needsTopic: false, placeholder: "Optional theme, e.g. summer growth push" },
];

const BASE_SYSTEM =
  "You are the Content Studio inside JoeMoyo OS — an expert YouTube strategist and scriptwriter. " +
  "Always write strictly in the brand's voice described below. Output clean Markdown. " +
  "Be specific and ready-to-use, never generic.";

function buildPrompt(task: StudioTask, brand: Brand, topic: string): string {
  const ctx = brandContext(brand);
  const t = topic.trim();
  switch (task) {
    case "script":
      return `${ctx}\n\nWrite a complete YouTube video script about: "${t}".\nInclude: a strong 15-second HOOK, an intro, 3-5 well-structured sections with on-screen cues in [brackets], a memorable conclusion, and the brand's call to action. Aim for an 8-12 minute video.`;
    case "titles":
      return `${ctx}\n\nBrainstorm 10 high-CTR YouTube titles for a video about: "${t}".\nFor each: give the title, a 1-line hook, and a click-through score out of 10 with a short reason. Put the strongest pick first as a table.`;
    case "thumbnails":
      return `${ctx}\n\nGive 4 distinct thumbnail concepts for a video about: "${t}".\nFor each concept describe: the main visual/scene, the focal subject, the color/mood, and the 2-4 word overlay text. Number them and explain why each would stop the scroll.`;
    case "repurpose":
      return `${ctx}\n\nRepurpose this topic/script into a multi-platform bundle: "${t}".\nProduce: (1) a 45-second YouTube Shorts/TikTok script, (2) a 6-tweet X thread, (3) a short email newsletter blurb, (4) 5 hashtags. Use clear Markdown headings for each.`;
    case "calendar":
      return `${ctx}\n\nCreate a 4-week content calendar${t ? ` themed around "${t}"` : ""}.\nFor each week give 2 video ideas: working title, the angle, and why it fits the audience now. Format as a Markdown table with columns: Week, Title, Angle, Why now.`;
  }
}

export interface StudioResult {
  task: StudioTask;
  brand: string;
  provider: ProviderId;
  markdown: string;
  error?: string;
}

export async function runStudioTask(
  task: StudioTask,
  brand: Brand,
  topic: string,
  provider: ProviderId = "claude",
): Promise<StudioResult> {
  const prompt = buildPrompt(task, brand, topic);
  const res = await runProvider(provider, [{ role: "user", content: prompt }], BASE_SYSTEM);
  return {
    task,
    brand: brand.id,
    provider,
    markdown: res.text,
    error: res.error,
  };
}
