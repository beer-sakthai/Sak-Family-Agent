import React from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, BookOpen, FileText, CheckCircle2, Shield } from "lucide-react";
import { getAllDocSlugs, getDocBySlug } from "@/lib/docs";

interface DocsPageProps {
  params: Promise<{ page: string }> | { page: string };
}

export async function generateStaticParams() {
  const slugs = getAllDocSlugs();
  return slugs.map((page) => ({ page }));
}

export default async function DocsPage(props: DocsPageProps) {
  const params = await Promise.resolve(props.params);
  const { page } = params;

  const doc = getDocBySlug(page);
  if (!doc) {
    notFound();
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Navigation Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>
        <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-800/50 px-3 py-1.5 rounded-md border border-slate-700/50">
          <FileText className="h-3.5 w-3.5 text-cyan-400" />
          <code>{doc.relativePath}</code>
        </div>
      </div>

      {/* Doc Header Card */}
      <div className="rounded-xl border border-slate-800/80 bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-slate-950/80 p-6 shadow-xl backdrop-blur-md">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <BookOpen className="h-3 w-3" />
              Documentation
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-100 font-display">
              {doc.title}
            </h1>
            <p className="text-xs text-slate-400">
              Canonical reference article for Sak-Family-Agent architecture and practices.
            </p>
          </div>
        </div>
      </div>

      {/* Document Content View */}
      <div className="rounded-xl border border-slate-800/80 bg-slate-900/50 p-6 sm:p-8 shadow-lg">
        <article className="prose prose-invert max-w-none prose-headings:font-display prose-headings:text-slate-100 prose-p:text-slate-300 prose-code:text-cyan-300 prose-code:bg-slate-950/80 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-pre:bg-slate-950 prose-pre:border prose-pre:border-slate-800">
          <pre className="whitespace-pre-wrap font-sans text-sm text-slate-200 leading-relaxed bg-transparent p-0 border-0">
            {doc.content}
          </pre>
        </article>
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between text-xs text-slate-500 pt-4 border-t border-slate-800/60">
        <div className="flex items-center gap-1.5">
          <Shield className="h-3.5 w-3.5 text-emerald-400" />
          Path verified & secured against traversal attacks
        </div>
        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="h-3.5 w-3.5 text-cyan-400" />
          House of Sak Standards
        </div>
      </div>
    </div>
  );
}
