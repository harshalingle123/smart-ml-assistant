import { memo, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp } from 'lucide-react';

interface UsageChartProps {
  data: Array<{
    timestamp: string;
    requests: number;
  }>;
  timeframe: '24h' | '7d' | '30d';
  title?: string;
  description?: string;
}

export const UsageChart = memo<UsageChartProps>(({ data, timeframe, title, description }) => {
  const formattedData = useMemo(() => {
    return data.map((item) => {
      const date = new Date(item.timestamp);
      let label = '';

      switch (timeframe) {
        case '24h':
          label = date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
          });
          break;
        case '7d':
          label = date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
          });
          break;
        case '30d':
          label = date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
          });
          break;
      }

      return {
        ...item,
        label,
        timestamp: item.timestamp,
      };
    });
  }, [data, timeframe]);

  const totalRequests = useMemo(() => {
    return data.reduce((sum, item) => sum + item.requests, 0);
  }, [data]);

  const avgRequests = useMemo(() => {
    return data.length > 0 ? Math.round(totalRequests / data.length) : 0;
  }, [totalRequests, data.length]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              {title || 'API Usage Over Time'}
            </CardTitle>
            {description && <CardDescription>{description}</CardDescription>}
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold">{totalRequests.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">Total Requests</p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <div className="flex items-center justify-center h-64 border-2 border-dashed rounded-lg">
            <p className="text-muted-foreground">No usage data available</p>
          </div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={formattedData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="label"
                  className="text-xs"
                  tick={{ fill: 'hsl(var(--muted-foreground))' }}
                />
                <YAxis
                  className="text-xs"
                  tick={{ fill: 'hsl(var(--muted-foreground))' }}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: 'hsl(var(--foreground))' }}
                  itemStyle={{ color: 'hsl(var(--primary))' }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="requests"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={{ fill: 'hsl(var(--primary))', r: 4 }}
                  activeDot={{ r: 6 }}
                  name="Requests"
                />
              </LineChart>
            </ResponsiveContainer>

            <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t">
              <div className="text-center">
                <p className="text-2xl font-bold">{totalRequests.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground mt-1">Total</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">{avgRequests.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Avg per {timeframe === '24h' ? 'hour' : 'day'}
                </p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">
                  {Math.max(...data.map((d) => d.requests)).toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground mt-1">Peak</p>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
});

UsageChart.displayName = 'UsageChart';
