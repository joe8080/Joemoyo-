import ModuleScaffold from "@/components/ModuleScaffold";

export default function Social() {
  return (
    <ModuleScaffold
      title="Social"
      subtitle="Your channels and socials in one command center."
      phase="Phase 4"
      icon="📡"
      features={[
        { title: "YouTube analytics", desc: "Views, watch time, subs and top videos across your channels." },
        { title: "Unified inbox", desc: "Comments and mentions from connected platforms in one place." },
        { title: "Post scheduler", desc: "Draft with AI and schedule posts across socials from one composer." },
        { title: "Cross-posting", desc: "Push a clip or update to multiple platforms at once." },
        { title: "Growth insights", desc: "AI weekly report on what's working and what to double down on." },
      ]}
      wiring={[
        "YouTube Data API via Google OAuth (added first — most useful)",
        "Instagram Graph API and other platforms as you connect them",
        "Supabase vault for tokens, scheduled posts and analytics history",
        "Content Studio so a finished script flows straight to scheduling",
      ]}
    />
  );
}
