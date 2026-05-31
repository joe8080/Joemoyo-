"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Dark-themed Markdown renderer for Studio output (handles GFM tables). */
export default function Markdown({ children }: { children: string }) {
  return (
    <div className="prose-invert max-w-none text-sm leading-relaxed text-slate-300">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: (p) => <h1 className="mb-2 mt-4 text-lg font-bold text-white" {...p} />,
          h2: (p) => <h2 className="mb-2 mt-4 text-base font-semibold text-white" {...p} />,
          h3: (p) => <h3 className="mb-1 mt-3 text-sm font-semibold text-accent-soft" {...p} />,
          p: (p) => <p className="my-2" {...p} />,
          strong: (p) => <strong className="font-semibold text-white" {...p} />,
          ul: (p) => <ul className="my-2 list-disc space-y-1 pl-5" {...p} />,
          ol: (p) => <ol className="my-2 list-decimal space-y-1 pl-5" {...p} />,
          a: (p) => <a className="text-accent-soft underline" target="_blank" rel="noreferrer" {...p} />,
          code: (p) => <code className="rounded bg-white/10 px-1 py-0.5 text-[12px]" {...p} />,
          hr: () => <hr className="my-4 border-white/10" />,
          table: (p) => (
            <div className="my-3 overflow-x-auto">
              <table className="w-full border-collapse text-left text-[13px]" {...p} />
            </div>
          ),
          th: (p) => (
            <th className="border-b border-white/15 bg-white/5 px-3 py-2 font-semibold text-white" {...p} />
          ),
          td: (p) => <td className="border-b border-white/10 px-3 py-2 align-top" {...p} />,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
