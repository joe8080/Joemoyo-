import ModuleScaffold from "@/components/ModuleScaffold";

export default function Studio() {
  return (
    <ModuleScaffold
      title="Content Studio"
      subtitle="Scripts, thumbnails and planning for your channels."
      phase="Phase 2 — next up"
      icon="🎬"
      features={[
        { title: "Script generator", desc: "Long-form video scripts for your History & Finance channels, in your voice." },
        { title: "Thumbnail concepts", desc: "AI-generated thumbnail directions and copy, ready to hand to a designer or image model." },
        { title: "Content calendar", desc: "A 4-week planner that schedules ideas across brands and saves to your vault." },
        { title: "Hook & title lab", desc: "Generate and score titles/hooks before you commit to a video." },
        { title: "Repurpose engine", desc: "Turn one script into Shorts, a tweet thread, and a newsletter." },
      ]}
      wiring={[
        "Your existing Python agents: script_writer.py, content_research.py, financial_content.py",
        "Supabase vault: ogx/ content pipeline + a content_calendar table",
        "AI Hub providers for drafting and scoring",
      ]}
    />
  );
}
