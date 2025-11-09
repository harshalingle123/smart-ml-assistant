import { PlanCard } from "@/components/PlanCard";
import { UsageStats } from "@/components/UsageStats";
import { PLANS, MOCK_USER, PLAN_LIMITS } from "@/lib/mock-data";

export default function Billing() {
  const currentPlan = MOCK_USER.currentPlan;
  const limits = PLAN_LIMITS[currentPlan as keyof typeof PLAN_LIMITS];

  const handleSelectPlan = (planId: string) => {
    console.log("Selected plan:", planId);
  };

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-semibold">Billing & Usage</h1>
        <p className="text-muted-foreground mt-1">
          Manage your subscription and monitor usage
        </p>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">Current Usage</h2>
        <UsageStats
          queriesUsed={MOCK_USER.queriesUsed}
          queriesLimit={limits.queries}
          fineTuneJobs={MOCK_USER.fineTuneJobs}
          fineTuneLimit={limits.fineTunes}
          datasetsCount={MOCK_USER.datasetsCount}
          datasetsLimit={limits.datasets}
        />
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">Subscription Plans</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PLANS.map((plan) => (
            <PlanCard
              key={plan.id}
              {...plan}
              currentPlan={plan.id === currentPlan}
              onSelect={handleSelectPlan}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
