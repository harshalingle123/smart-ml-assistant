import { PlanCard } from "../PlanCard";

export default function PlanCardExample() {
  const plans = [
    {
      name: "Free",
      price: "$0",
      period: "/month",
      features: ["100 queries/month", "1 fine-tune job", "1 dataset", "Community support"],
      id: "free",
    },
    {
      name: "Pro",
      price: "$9.99",
      period: "/month",
      features: ["1,000 queries/month", "5 fine-tune jobs", "5 datasets", "Priority support", "API access"],
      id: "pro",
      popular: true,
      currentPlan: true,
    },
    {
      name: "Enterprise",
      price: "Custom",
      period: "",
      features: ["Unlimited queries", "Unlimited fine-tuning", "Custom models", "SLA guarantee"],
      id: "enterprise",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-6">
      {plans.map((plan) => (
        <PlanCard
          key={plan.id}
          {...plan}
          onSelect={(id) => console.log("Selected plan:", id)}
        />
      ))}
    </div>
  );
}
