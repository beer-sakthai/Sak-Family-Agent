import { useDashboardData } from "@/hooks/useDashboardData";
import { DashboardHeader } from "@/components/DashboardHeader";
import { KPICard } from "@/components/KPICard";
import { GrowthChart } from "@/components/GrowthChart";
import { CategoryChart } from "@/components/CategoryChart";
import { FactsTable } from "@/components/FactsTable";
import { ObservationsTable } from "@/components/ObservationsTable";
import { Loader2, Database, Lightbulb } from "lucide-react";

export default function Home() {
  const { data, loading } = useDashboardData();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
          <p className="text-slate-400 font-mono">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <DashboardHeader source={data.source} generatedAt={data.generated_at} />

      <main className="container mx-auto px-4 py-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <KPICard
            label="Total Facts"
            value={data.kpis.total_facts}
            delta={data.kpis.total_facts_delta}
            icon={<Database className="w-5 h-5" />}
          />
          <KPICard
            label="Observations"
            value={data.kpis.total_observations}
            delta={data.kpis.total_observations_delta}
            icon={<Lightbulb className="w-5 h-5" />}
          />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <GrowthChart data={data.growth} />
          </div>
          <div>
            <CategoryChart categories={data.categories} />
          </div>
        </div>

        {/* Tables Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <FactsTable facts={data.recent_facts} />
          <ObservationsTable observations={data.top_observations} />
        </div>

        {/* Footer */}
        <div className="mt-12 pt-8 border-t border-slate-700/50 text-center text-xs text-slate-500 font-mono">
          <p>
            Data exported from SakThai Agent · {data.source === "live" ? "Real-time memory snapshot" : "Demo data"}
          </p>
        </div>
      </main>
    </div>
  );
}
