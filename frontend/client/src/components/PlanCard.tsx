import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";

interface PlanCardProps {
  name: string;
  price: string;
  period: string;
  features: string[];
  id: string;
  popular?: boolean;
  currentPlan?: boolean;
  onSelect?: (planId: string) => void;
}

export function PlanCard({
  name,
  price,
  period,
  features,
  id,
  popular,
  currentPlan,
  onSelect,
}: PlanCardProps) {
  return (
    <Card
      className={`relative ${popular ? "border-primary shadow-md" : ""}`}
      data-testid={`card-plan-${id}`}
    >
      {popular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2">
          <Badge className="px-3 py-1">Most Popular</Badge>
        </div>
      )}

      <CardHeader className="text-center pb-4">
        <CardTitle className="text-2xl font-semibold">{name}</CardTitle>
        <div className="mt-4">
          <span className="text-4xl font-bold">{price}</span>
          <span className="text-muted-foreground">{period}</span>
        </div>
      </CardHeader>

      <CardContent>
        <ul className="space-y-3">
          {features.map((feature, index) => (
            <li key={index} className="flex items-start gap-2">
              <Check className="h-5 w-5 text-primary shrink-0 mt-0.5" />
              <span className="text-sm">{feature}</span>
            </li>
          ))}
        </ul>
      </CardContent>

      <CardFooter>
        <Button
          className="w-full"
          variant={currentPlan ? "outline" : popular ? "default" : "outline"}
          onClick={() => onSelect?.(id)}
          disabled={currentPlan}
          data-testid={`button-select-${id}`}
        >
          {currentPlan ? "Current Plan" : "Select Plan"}
        </Button>
      </CardFooter>
    </Card>
  );
}
