import React, { useState } from 'react';
import { X, Check, Zap, Sparkles, Shield, Crown, Loader2, ArrowRight } from 'lucide-react';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

export const PLANS_DATA = [
  {
    id: 'free',
    name: 'Free Trial',
    price_inr: 0,
    price_usd: 0,
    max_res: '720p',
    max_duration: '30s',
    credits: 2,
    badge: 'Current',
    features: ['Up to 720p output', '2 free edits daily', 'Standard voices & captions', 'Community queue']
  },
  {
    id: 'plan1',
    name: 'Starter',
    price_inr: 299,
    price_usd: 4,
    max_res: '720p HD',
    max_duration: '60s',
    credits: 30,
    badge: 'Popular',
    features: ['720p HD exports', '30 render credits / mo', 'Full voice library', 'No watermark', 'Standard queue']
  },
  {
    id: 'plan2',
    name: 'Creator',
    price_inr: 599,
    price_usd: 8,
    max_res: '1080p Full HD',
    max_duration: '90s',
    credits: 75,
    badge: 'Best Value',
    features: ['1080p Full HD exports', '75 render credits / mo', 'All 50+ voices & styles', 'Priority render queue', 'Audio mastering (-14 LUFS)']
  },
  {
    id: 'plan3',
    name: 'Pro',
    price_inr: 999,
    price_usd: 13,
    max_res: '2K QHD (1440p)',
    max_duration: '120s',
    credits: 150,
    badge: 'Pro Tier',
    features: ['2K QHD crisp resolution', '150 render credits / mo', '2-minute video clips', 'Dedicated worker priority', 'Custom brand highlights']
  },
  {
    id: 'plan4',
    name: 'Studio',
    price_inr: 1699,
    price_usd: 22,
    max_res: '3K Ultra (1800p)',
    max_duration: '180s',
    credits: 300,
    badge: 'Studio',
    features: ['3K Ultra resolution', '300 render credits / mo', '3-minute video clips', 'Instant render slot', 'Commercial usage rights']
  },
  {
    id: 'plan5',
    name: 'Business',
    price_inr: 2999,
    price_usd: 40,
    max_res: '4K UHD (2160p)',
    max_duration: '300s',
    credits: 600,
    badge: 'Agency',
    features: ['4K Cinema UHD exports', '600 render credits / mo', '5-minute longform clips', 'Top queue priority', 'Unlimited voice previews']
  },
  {
    id: 'plan6',
    name: 'Enterprise',
    price_inr: 5999,
    price_usd: 80,
    max_res: '8K Ultra (4320p)',
    max_duration: '300s',
    credits: 1500,
    badge: 'VIP 8K',
    features: ['8K Maximum fidelity', '1,500 render credits / mo', 'Hardware-isolated rendering', 'VIP 24/7 dedicated queue', 'Custom AI voice cloning access']
  }
];

export default function PricingModal({ isOpen, onClose, userPlan = 'free', onPlanUpgraded }) {
  const [currency, setCurrency] = useState('INR');
  const [loadingPlan, setLoadingPlan] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  async function handleCheckout(plan) {
    if (plan.id === 'free' || plan.id === userPlan) {
      onClose();
      return;
    }
    setError('');
    setLoadingPlan(plan.id);
    try {
      const res = await fetch(`${BACKEND_BASE}/api/payments/dodo/checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan_id: plan.id,
          return_url: window.location.href
        })
      });
      const data = await res.json();
      if (res.ok && data.ok && data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        setError(data.error || 'Failed to start payment. Please try again.');
        setLoadingPlan('');
      }
    } catch (err) {
      setError(err.message || 'Payment server unreachable.');
      setLoadingPlan('');
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-5xl bg-[var(--surface,#12141a)] border border-[var(--border,#262934)] rounded-2xl sm:rounded-3xl p-5 sm:p-8 my-8 shadow-2xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 sm:top-6 sm:right-6 p-2 rounded-xl text-[var(--text-muted,#9ca3af)] hover:text-white hover:bg-[var(--surface-hover,#1c1f2b)] transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center max-w-2xl mx-auto mb-6 sm:mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--accent,#facc15)]/10 text-[var(--accent,#facc15)] border border-[var(--accent,#facc15)]/30 text-xs font-bold mb-3 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" /> Dodo Payments Powered
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight mb-2">
            Upgrade Your AI Video Editor Plan
          </h2>
          <p className="text-sm text-[var(--text-muted,#9ca3af)]">
            Higher resolution exports, up to 1,500 credits, zero queue wait times, and cinema 4K/8K rendering.
          </p>

          <div className="inline-flex items-center gap-1 p-1 bg-[var(--bg-alt,#1b1e27)] rounded-xl border border-[var(--border,#262934)] mt-4">
            <button
              type="button"
              onClick={() => setCurrency('INR')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${currency === 'INR' ? 'bg-[var(--primary,#2563eb)] text-white shadow' : 'text-zinc-400 hover:text-white'}`}
            >
              INR (&#8377;)
            </button>
            <button
              type="button"
              onClick={() => setCurrency('USD')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${currency === 'USD' ? 'bg-[var(--primary,#2563eb)] text-white shadow' : 'text-zinc-400 hover:text-white'}`}
            >
              USD ($)
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs text-center font-medium">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {PLANS_DATA.map((plan) => {
            const isCurrent = userPlan === plan.id;
            const isFeatured = plan.id === 'plan2' || plan.id === 'plan3';
            const price = currency === 'INR' ? `\u20B9${plan.price_inr}` : `$${plan.price_usd}`;

            return (
              <div
                key={plan.id}
                className={`relative flex flex-col justify-between rounded-2xl p-5 border transition-all ${
                  isFeatured
                    ? 'bg-gradient-to-b from-blue-950/30 to-[var(--surface,#12141a)] border-blue-500/40 shadow-lg shadow-blue-500/5'
                    : 'bg-[var(--surface,#12141a)] border-[var(--border,#262934)] hover:border-zinc-700'
                }`}
              >
                {plan.badge && (
                  <span className={`absolute top-4 right-4 px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                    isFeatured ? 'bg-blue-500 text-white' : 'bg-zinc-800 text-zinc-300'
                  }`}>
                    {plan.badge}
                  </span>
                )}

                <div>
                  <h3 className="text-base font-bold text-white mb-1">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mb-3">
                    <span className="text-2xl font-black text-white">{plan.price_inr === 0 ? 'Free' : price}</span>
                    {plan.price_inr > 0 && <span className="text-xs text-zinc-400">/mo</span>}
                  </div>

                  <div className="p-2.5 rounded-xl bg-zinc-900/60 border border-zinc-800/80 mb-4 text-xs space-y-1">
                    <div className="flex justify-between text-zinc-300">
                      <span>Resolution:</span>
                      <strong className="text-white font-bold">{plan.max_res}</strong>
                    </div>
                    <div className="flex justify-between text-zinc-300">
                      <span>Credits:</span>
                      <strong className="text-amber-400 font-bold">{plan.credits} / mo</strong>
                    </div>
                    <div className="flex justify-between text-zinc-300">
                      <span>Max Clip:</span>
                      <strong className="text-white font-bold">{plan.max_duration}</strong>
                    </div>
                  </div>

                  <ul className="space-y-2 mb-5">
                    {plan.features.map((f, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-zinc-300">
                        <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <button
                  type="button"
                  disabled={loadingPlan === plan.id || isCurrent}
                  onClick={() => handleCheckout(plan)}
                  className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                    isCurrent
                      ? 'bg-zinc-800 text-zinc-400 cursor-default'
                      : isFeatured
                      ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/30'
                      : 'bg-zinc-800 hover:bg-zinc-700 text-white'
                  }`}
                >
                  {loadingPlan === plan.id ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : isCurrent ? (
                    'Active Plan'
                  ) : (
                    <>
                      <span>{plan.price_inr === 0 ? 'Use Free' : 'Upgrade Plan'}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>

        <div className="mt-6 pt-4 border-t border-zinc-800/60 flex flex-wrap items-center justify-between text-xs text-zinc-400 gap-3">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-400" />
            <span>Secure 256-bit encryption • Global cards, UPI & NetBanking accepted via Dodo Payments</span>
          </div>
          <button type="button" onClick={onClose} className="text-zinc-400 hover:text-white underline">
            Continue with current plan
          </button>
        </div>
      </div>
    </div>
  );
}
