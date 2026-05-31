import Link from "next/link";
import PageHeader from "@/components/PageHeader";

const MODULES = [
  {
    href: "/hub",
    icon: "🧠",
    title: "AI Hub",
    desc: "Ask once, get answers from Claude, ChatGPT & Perplexity side by side.",
    status: "Live",
  },
  {
    href: "/studio",
    icon: "🎬",
    title: "Content Studio",
    desc: "Generate video scripts, thumbnail concepts and a content calendar.",
    status: "Phase 2",
  },
  {
    href: "/investing",
    icon: "📈",
    title: "Investing",
    desc: "Portfolio, live market data and AI-driven alerts & suggestions.",
    status: "Phase 3",
  },
  {
    href: "/social",
    icon: "📡",
    title: "Social",
    desc: "YouTube & socials analytics, plus draft and schedule posts.",
    status: "Phase 4",
  },
];

export default function Dashboard() {
  return (
    <>
      <PageHeader title="Dashboard" subtitle="Good to see you. Everything in one place." />
      <div className="p-6">
        <div className="mb-8 animate-fade-up glass p-6">
          <div className="text-sm uppercase tracking-widest text-accent-soft">Welcome</div>
          <h2 className="mt-1 text-2xl font-semibold text-white">
            This is your OS — content, money, and AI, unified.
          </h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-400">
            Start in the AI Hub to talk to every model at once. The other modules light up as
            we wire them to your Supabase vault and accounts.
          </p>
          <Link
            href="/hub"
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-sm font-medium text-white shadow-glow transition hover:bg-accent-soft"
          >
            Open AI Hub →
          </Link>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {MODULES.map((m, i) => (
            <Link
              key={m.href}
              href={m.href}
              style={{ animationDelay: `${i * 60}ms` }}
              className="group animate-fade-up glass glass-hover flex flex-col gap-3 p-5"
            >
              <div className="flex items-center justify-between">
                <span className="text-2xl">{m.icon}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                    m.status === "Live"
                      ? "bg-emerald-400/15 text-emerald-300"
                      : "bg-white/5 text-slate-500"
                  }`}
                >
                  {m.status}
                </span>
              </div>
              <div className="text-base font-semibold text-white">{m.title}</div>
              <p className="text-sm leading-relaxed text-slate-400">{m.desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
