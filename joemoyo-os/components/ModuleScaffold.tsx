import PageHeader from "./PageHeader";

interface Feature {
  title: string;
  desc: string;
}

export default function ModuleScaffold({
  title,
  subtitle,
  phase,
  icon,
  features,
  wiring,
}: {
  title: string;
  subtitle: string;
  phase: string;
  icon: string;
  features: Feature[];
  wiring: string[];
}) {
  return (
    <>
      <PageHeader title={title} subtitle={subtitle} />
      <div className="p-6">
        <div className="glass animate-fade-up flex items-center gap-4 p-6">
          <span className="text-4xl">{icon}</span>
          <div>
            <div className="text-xs uppercase tracking-widest text-accent-soft">{phase}</div>
            <p className="mt-1 max-w-2xl text-sm text-slate-400">
              The module shell is ready. Below is what it will do and exactly what it plugs into.
            </p>
          </div>
        </div>

        <h3 className="mb-3 mt-8 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Planned features
        </h3>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {features.map((f, i) => (
            <div
              key={f.title}
              style={{ animationDelay: `${i * 50}ms` }}
              className="glass animate-fade-up p-5"
            >
              <div className="text-sm font-semibold text-white">{f.title}</div>
              <p className="mt-1 text-sm leading-relaxed text-slate-400">{f.desc}</p>
            </div>
          ))}
        </div>

        <h3 className="mb-3 mt-8 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Wires into
        </h3>
        <ul className="glass space-y-2 p-5 text-sm text-slate-400">
          {wiring.map((w) => (
            <li key={w} className="flex items-start gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              {w}
            </li>
          ))}
        </ul>
      </div>
    </>
  );
}
