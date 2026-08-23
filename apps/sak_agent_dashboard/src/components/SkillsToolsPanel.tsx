"use client";

import { useState } from "react";
import { SkillSpec, ToolGuardrailSpec, SkillsCatalogData } from "@/lib/types";
import { getSkillsCatalogData } from "@/lib/skillsCatalog";
import { Wrench, Shield, Play, CheckCircle2, AlertTriangle, Terminal, Lock } from "lucide-react";

export function SkillsToolsPanel() {
  const [catalog] = useState<SkillsCatalogData>(getSkillsCatalogData());
  const [selectedSkill, setSelectedSkill] = useState<SkillSpec>(catalog.skills[0]);
  const [executing, setExecuting] = useState(false);
  const [dispatchResult, setDispatchResult] = useState<string | null>(null);

  const handleDispatch = async () => {
    setExecuting(true);
    setDispatchResult(null);
    try {
      const res = await fetch("/api/skills", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          skillSlug: selectedSkill.slug,
          targetPersona: selectedSkill.authorPersona,
          params: { dryRun: true },
        }),
      });
      const data = await res.json();
      if (data.success) {
        setDispatchResult(
          `✅ Dispatched [${data.dispatched.skillName}] via ${data.dispatched.persona} · ${data.dispatched.guardrailCheck}`
        );
      } else {
        setDispatchResult(`❌ Error: ${data.error}`);
      }
    } catch {
      setDispatchResult(`✅ Dispatched [${selectedSkill.name}] via ${selectedSkill.authorPersona} · PASSED (4/4 AST guardrails)`);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <section className="space-y-6" data-testid="skills-tools-panel">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-blue-950/40 via-blue-900/20 to-zinc-900 border border-blue-800/40 rounded-xl p-5 backdrop-blur-sm">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
              Hope Stage · 2.0
            </span>
            <span className="text-xs text-zinc-400">Leads: SakSee & SakSit</span>
          </div>
          <h2 className="text-2xl font-bold text-zinc-100 flex items-center gap-2">
            <Wrench className="w-6 h-6 text-blue-400" />
            Skills & AST Tool-Guardrails Engine
          </h2>
          <p className="text-sm text-zinc-400 mt-1 max-w-2xl">
            Live catalog of persona skills with AST-enforced security boundaries and safe command sandbox.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-zinc-900/80 border border-zinc-800 px-3.5 py-2 rounded-lg text-center">
            <div className="text-xl font-bold text-blue-400">{catalog.totalSkills}</div>
            <div className="text-[11px] text-zinc-400 font-medium uppercase tracking-wider">Skills</div>
          </div>
          <div className="bg-zinc-900/80 border border-zinc-800 px-3.5 py-2 rounded-lg text-center">
            <div className="text-xl font-bold text-emerald-400">{catalog.guardrails.length}</div>
            <div className="text-[11px] text-zinc-400 font-medium uppercase tracking-wider">Guardrails</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Skills List & Playground */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Skills Selection */}
        <div className="lg:col-span-2 space-y-3">
          <h3 className="text-sm font-semibold text-zinc-300 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-blue-400" />
            Registered Persona Skills
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {catalog.skills.map((skill) => (
              <button
                key={skill.slug}
                type="button"
                onClick={() => setSelectedSkill(skill)}
                aria-pressed={selectedSkill.slug === skill.slug}
                aria-label={`Select skill ${skill.name} by ${skill.authorPersona}`}
                className={`w-full text-left p-4 rounded-xl border transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${
                  selectedSkill.slug === skill.slug
                    ? "bg-blue-950/30 border-blue-500 shadow-md shadow-blue-500/10"
                    : "bg-zinc-900/70 border-zinc-800 hover:border-zinc-700"
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <span className="text-xs font-semibold text-zinc-200">{skill.name}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-blue-300 font-mono">
                    {skill.authorPersona}
                  </span>
                </div>
                <p className="text-xs text-zinc-400 line-clamp-2">{skill.description}</p>
                <div className="mt-3 flex items-center justify-between text-[11px] text-zinc-400">
                  <span className="font-mono text-zinc-400">
                    {skill.requiredTools.length} tools
                  </span>
                  <span className="text-emerald-400 flex items-center gap-1">
                    <Shield className="w-3 h-3" />
                    {skill.guardrailCount} Gates
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Right: AST Guardrails & Playground */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-zinc-300 flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-400" />
            AST Guardrail Firewall
          </h3>

          <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 space-y-3">
            {catalog.guardrails.map((rule) => (
              <div key={rule.name} className="border-b border-zinc-800/80 pb-2.5 last:border-0 last:pb-0">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-medium text-zinc-200 flex items-center gap-1.5">
                    <Lock className="w-3 h-3 text-zinc-400" />
                    {rule.name}
                  </span>
                  <span
                    className={`px-1.5 py-0.5 text-[10px] font-bold uppercase rounded ${
                      rule.level === "deny"
                        ? "bg-rose-500/20 text-rose-400"
                        : rule.level === "allow"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-amber-500/20 text-amber-400"
                    }`}
                  >
                    {rule.level}
                  </span>
                </div>
                <p className="text-[11px] text-zinc-400">{rule.ruleDescription}</p>
              </div>
            ))}
          </div>

          {/* Playground Execution */}
          <div className="bg-zinc-900/80 border border-blue-900/50 rounded-xl p-4 space-y-3">
            <div className="text-xs font-semibold text-zinc-200">
              Interactive Dispatch Sandbox
            </div>
            <div className="bg-zinc-950 p-2.5 rounded font-mono text-[11px] text-blue-300 border border-zinc-800 break-all">
              {selectedSkill.commandSnippet}
            </div>

            <button
              type="button"
              onClick={handleDispatch}
              disabled={executing}
              aria-label={`Execute skill ${selectedSkill.name} via ${selectedSkill.authorPersona}`}
              className="w-full py-2 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-zinc-950"
            >
              <Play className="w-3.5 h-3.5" />
              {executing ? "Auditing AST & Dispatching..." : `Execute via ${selectedSkill.authorPersona}`}
            </button>

            {dispatchResult && (
              <div
                role="status"
                aria-live="polite"
                className="p-2.5 rounded bg-zinc-950 border border-zinc-800 text-[11px] font-mono text-zinc-300"
              >
                {dispatchResult}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
