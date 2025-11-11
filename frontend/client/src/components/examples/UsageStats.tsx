import { UsageStats } from "../UsageStats";

export default function UsageStatsExample() {
  return (
    <div className="p-6">
      <UsageStats
        queriesUsed={432}
        queriesLimit={1000}
        fineTuneJobs={3}
        fineTuneLimit={5}
        datasetsCount={2}
        datasetsLimit={5}
      />
    </div>
  );
}
