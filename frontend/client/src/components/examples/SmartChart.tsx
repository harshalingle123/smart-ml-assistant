import { SmartChart } from "../SmartChart";

export default function SmartChartExample() {
  const pieChart = {
    type: "pie" as const,
    title: "Sentiment Distribution",
    data: { Positive: 0.65, Negative: 0.25, Neutral: 0.10 },
  };

  const barChart = {
    type: "bar" as const,
    title: "Prediction Confidence",
    data: { Positive: 0.92, Negative: 0.08 },
  };

  const lineChart = {
    type: "line" as const,
    title: "Sentiment Over Time",
    data: [
      { date: "Jan", positive: 65, negative: 35 },
      { date: "Feb", positive: 70, negative: 30 },
      { date: "Mar", positive: 75, negative: 25 },
      { date: "Apr", positive: 72, negative: 28 },
    ],
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
      <SmartChart chart={pieChart} />
      <SmartChart chart={barChart} />
      <div className="md:col-span-2">
        <SmartChart chart={lineChart} />
      </div>
    </div>
  );
}
