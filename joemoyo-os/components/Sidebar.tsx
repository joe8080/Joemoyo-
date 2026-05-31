"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Dashboard", icon: "◆" },
  { href: "/hub", label: "AI Hub", icon: "🧠" },
  { href: "/studio", label: "Content Studio", icon: "🎬" },
  { href: "/investing", label: "Investing", icon: "📈" },
  { href: "/social", label: "Social", icon: "📡" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-60 shrink-0 flex-col gap-2 border-r border-white/10 bg-ink-900/60 p-4 backdrop-blur-xl md:flex">
      <div className="mb-6 px-2">
        <div className="text-lg font-semibold tracking-tight text-white">JoeMoyo OS</div>
        <div className="text-xs text-slate-500">your personal command center</div>
      </div>
      <nav className="flex flex-col gap-1">
        {NAV.map((item) => {
          const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
                active
                  ? "bg-accent/20 text-white shadow-glow"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-100"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto px-2 text-[11px] leading-relaxed text-slate-600">
        Connected to your Supabase vault &amp; AI models.
      </div>
    </aside>
  );
}
