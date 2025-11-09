import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { MessageSquare, Zap, Database, TrendingUp } from "lucide-react";

interface UsageStatsProps {
  queriesUsed: number;
  queriesLimit: number;
  fineTuneJobs: number;
  fineTuneLimit: number;
  datasetsCount: number;
  datasetsLimit: number;
}

export function UsageStats({
  queriesUsed,
  queriesLimit,
  fineTuneJobs,
  fineTuneLimit,
  datasetsCount,
  datasetsLimit,
}: UsageStatsProps) {
  const stats = [
    {
      title: "Queries Used",
      value: queriesUsed,
      limit: queriesLimit,
      icon: MessageSquare,
      color: "hsl(var(--chart-1))",
    },
    {
      title: "Fine-tune Jobs",
      value: fineTuneJobs,
      limit: fineTuneLimit,
      icon: Zap,
      color: "hsl(var(--chart-2))",
    },
    {
      title: "Datasets",
      value: datasetsCount,
      limit: datasetsLimit,
      icon: Database,
      color: "hsl(var(--chart-3))",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        const percentage = (stat.value / stat.limit) * 100;
        const limitText = stat.limit === Infinity ? "Unlimited" : stat.limit;

        return (
          <Card key={stat.title} data-testid={`card-stat-${stat.title.toLowerCase().replace(" ", "-")}`}>
            <CardHeader className="flex flex-row items-center justify-between gap-4 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" data-testid={`text-value-${stat.title.toLowerCase().replace(" ", "-")}`}>
                {stat.value.toLocaleString()}
                <span className="text-sm text-muted-foreground font-normal">
                  {" / "}{limitText}
                </span>
              </div>
              {stat.limit !== Infinity && (
                <div className="mt-3">
                  <Progress value={percentage} style={{ "--progress-color": stat.color } as any} />
                  <p className="text-xs text-muted-foreground mt-2">
                    {percentage.toFixed(0)}% used
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
