import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import {
  PieChart,
  Pie,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface ChartData {
  type: "pie" | "bar" | "line";
  title: string;
  data: any;
}

interface SmartChartProps {
  chart: ChartData;
}

const COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

export function SmartChart({ chart }: SmartChartProps) {
  const handleDownload = () => {
    console.log("Download chart:", chart.title);
  };

  const renderChart = () => {
    switch (chart.type) {
      case "pie":
        const pieData = Object.entries(chart.data).map(([name, value]) => ({
          name,
          value,
        }));
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name}: ${(percent * 100).toFixed(0)}%`
                }
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        );

      case "bar":
        const barData = Array.isArray(chart.data)
          ? chart.data
          : Object.entries(chart.data).map(([name, value]) => ({
              name,
              value,
            }));
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="hsl(var(--chart-1))" />
            </BarChart>
          </ResponsiveContainer>
        );

      case "line":
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chart.data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="positive"
                stroke="hsl(var(--chart-2))"
                strokeWidth={2}
              />
              <Line
                type="monotone"
                dataKey="negative"
                stroke="hsl(var(--chart-5))"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      default:
        return null;
    }
  };

  return (
    <Card data-testid={`chart-${chart.type}`}>
      <CardHeader className="flex flex-row items-center justify-between gap-4 space-y-0 pb-4">
        <CardTitle className="text-lg font-semibold">{chart.title}</CardTitle>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleDownload}
          data-testid="button-download-chart"
        >
          <Download className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>{renderChart()}</CardContent>
    </Card>
  );
}
