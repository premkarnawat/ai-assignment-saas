"use client";
// frontend/app/pricing/page.tsx
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import toast from "react-hot-toast";
import { CheckCircle, Zap, Loader2, CreditCard } from "lucide-react";
import { payments } from "@/lib/api";
import { useAuthStore } from "@/lib/store";

declare global {
  interface Window {
    Razorpay: new (options: Record<string, unknown>) => { open: () => void };
  }
}

const PLANS = [
  {
    key: "free",
    name: "Free",
    price: "₹0",
    period: "forever",
    highlight: false,
    features: ["3 assignments per day","2 handwriting styles","Notebook + white paper","Watermarked PDF"],
    cta: "Start Free",
    href: "/register",
    isPayment: false,
  },
  {
    key: "pro",
    name: "Student Pro",
    price: "₹99",
    period: "per month",
    highlight: true,
    features: ["Unlimited assignments","All 4 handwriting styles","All paper types","Full Notebook Generator","No watermark","Priority processing","OCR photo upload"],
    cta: "Upgrade to Pro",
    isPayment: true,
    plan: "pro",
  },
  {
    key: "team",
    name: "Team / College",
    price: "₹499",
    period: "per month",
    highlight: false,
    features: ["Everything in Pro","10 student accounts","Teacher style mimicry","Custom PDF branding","API access","Analytics","Priority support"],
    cta: "Get Team Plan",
    isPayment: true,
    plan: "team",
  },
];

function loadRazorpayScript(): Promise<boolean> {
  return new Promise((resolve) => {
    if (window.Razorpay) { resolve(true); return; }
    const s = document.createElement("script");
    s.src = "https://checkout.razorpay.com/v1/checkout.js";
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.body.appendChild(s);
  });
}

export default function PricingPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);

  const handlePayment = async (plan: string) => {
    if (!user) { router.push("/register?plan=" + plan); return; }
    setLoadingPlan(plan);
    try {
      const loaded = await loadRazorpayScript();
      if (!loaded) { toast.error("Could not load payment system. Check internet."); return; }
      const { data } = await payments.createOrder(plan);
      const rzp = new window.Razorpay({
        key: data.key,
        amount: data.amount,
        currency: data.currency,
        name: "WriteAI",
        description: data.plan_name,
        order_id: data.order_id,
        prefill: { name: data.user_name, email: data.user_email },
        theme: { color: "#2563eb" },
        modal: { ondismiss: () => { setLoadingPlan(null); } },
        handler: async (res: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }) => {
          try {
            await payments.verifyPayment({ ...res, plan });
            toast.success("🎉 Upgrade successful!");
            router.push("/dashboard");
          } catch { toast.error("Verification failed. Email support@writeai.com"); }
          finally { setLoadingPlan(null); }
        },
      });
      rzp.open();
    } catch (err: unknown) {
      toast.error((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Payment error.");
      setLoadingPlan(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white py-16 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-green-500/10 border border-green-500/20 rounded-full px-4 py-1.5 text-green-400 text-sm mb-6">
            <CreditCard className="w-3.5 h-3.5" /> Secure payments via Razorpay
          </div>
          <h1 className="text-5xl font-black mb-4">Simple Pricing</h1>
          <p className="text-slate-400 text-lg">One chai per month. Unlimited handwritten assignments.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-10">
          {PLANS.map((plan) => (
            <div key={plan.key} className={`rounded-2xl p-8 relative border transition-all hover:-translate-y-1 ${plan.highlight ? "bg-blue-600 border-blue-500 shadow-2xl shadow-blue-500/20" : "bg-slate-900 border-slate-800"}`}>
              {plan.highlight && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-amber-400 text-amber-900 text-xs font-black px-4 py-1.5 rounded-full">
                  MOST POPULAR
                </div>
              )}
              <div className={`text-xs font-bold tracking-widest uppercase mb-2 ${plan.highlight ? "text-blue-200" : "text-slate-500"}`}>{plan.name}</div>
              <div className="flex items-end gap-1 mb-6">
                <span className="text-4xl font-black">{plan.price}</span>
                <span className={`text-sm pb-1.5 ${plan.highlight ? "text-blue-200" : "text-slate-500"}`}>/{plan.period}</span>
              </div>
              <ul className="space-y-3 mb-8">
                {plan.features.map((f, i) => (
                  <li key={i} className={`flex items-start gap-2.5 text-sm ${plan.highlight ? "text-blue-50" : "text-slate-300"}`}>
                    <CheckCircle className={`w-4 h-4 mt-0.5 flex-shrink-0 ${plan.highlight ? "text-blue-200" : "text-green-500"}`} />
                    {f}
                  </li>
                ))}
              </ul>
              {plan.isPayment ? (
                <button onClick={() => handlePayment(plan.plan!)} disabled={loadingPlan === plan.plan}
                  className={`w-full py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-60 ${plan.highlight ? "bg-white text-blue-600 hover:bg-blue-50" : "bg-blue-600 text-white hover:bg-blue-700"}`}>
                  {loadingPlan === plan.plan ? <><Loader2 className="w-4 h-4 animate-spin" />Processing...</> : <><Zap className="w-4 h-4" />{plan.cta}</>}
                </button>
              ) : (
                <Link href={plan.href!} className="block w-full py-3 rounded-xl font-bold text-sm text-center bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 transition-colors">
                  {plan.cta}
                </Link>
              )}
            </div>
          ))}
        </div>

        <div className="text-center mb-10">
          <p className="text-slate-500 text-sm mb-3">All Indian payment methods accepted</p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            {["UPI / GPay", "PhonePe", "Paytm", "Visa / Mastercard", "RuPay", "Net Banking"].map((m) => (
              <span key={m} className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-400">{m}</span>
            ))}
          </div>
        </div>

        <div className="max-w-2xl mx-auto space-y-3">
          <h2 className="text-2xl font-black text-center mb-6">FAQ</h2>
          {[
            { q: "Can I pay with UPI?", a: "Yes! Razorpay supports UPI, GPay, PhonePe, Paytm, all debit/credit cards, and net banking." },
            { q: "How do I cancel?", a: "Dashboard → Settings → Cancel. No questions asked. Access continues till end of billing period." },
            { q: "Is my payment safe?", a: "Yes. Razorpay is PCI-DSS Level 1 compliant. We never see your card details." },
            { q: "What is the Notebook Generator?", a: "Enter Subject + Topic + Pages → get a full handwritten notebook with diagrams and examples. Pro feature." },
          ].map((f, i) => (
            <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h3 className="font-semibold text-slate-100 mb-1.5">{f.q}</h3>
              <p className="text-slate-400 text-sm">{f.a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
