import React, { useState } from 'react';
import { X, Check, Zap, Sparkles, Shield, Loader2, ArrowRight, Crown } from 'lucide-react';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

export const PLANS_DATA = [
  {
    id: 'free',
    name: 'Free Trial',
    price_inr: 0,
    price_usd: 0,
    max_res: '480p SD',
    max_duration: '30s',
    credits: 2,
    badge: 'Current',
    features: ['Below 720p (480p SD output)', '2 free credits daily', 'Standard voices & captions', 'Community render queue']
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
    features: ['2K QHD ultra resolution', '150 render credits / mo', '2-minute video clips', 'Dedicated worker priority', 'Custom brand highlights']
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
    name: 'Agency',
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
    if (plan.id === 'free') {
      onClose();
      return;
    }

    setError('');
    setLoadingPlan(plan.id);

    try {
      const token = localStorage.getItem('wpb_token');
      const guestId = localStorage.getItem('wpb_guest_id');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      if (guestId) headers['x-guest-id'] = guestId;

      const res = await fetch(`${BACKEND_BASE}/api/payments/dodo/checkout`, {
        method: 'POST',
        credentials: 'include',
        headers,
        body: JSON.stringify({
          plan_id: plan.id,
          return_url: window.location.origin + '/payment/success'
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
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-3 sm:p-4 bg-black/75 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-5xl bg-[var(--surface)] border border-[var(--border)] rounded-2xl sm:rounded-3xl p-5 sm:p-8 my-8 shadow-2xl text-[var(--text)]">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 sm:top-6 sm:right-6 p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--bg-alt)] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center max-w-2xl mx-auto mb-6 sm:mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/30 text-xs font-bold mb-3 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" /> Dodo Payments Powered
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-[var(--text)] tracking-tight mb-2">
            Upgrade Your AI Video Editor Plan
          </h2>
          <p className="text-xs sm:text-sm text-[var(--text-muted)]">
            Higher resolution exports, up to 1,500 credits, zero queue wait times, and cinema 4K/8K rendering.
          </p>

          <div className="inline-flex items-center gap-1 p-1 bg-[var(--bg-alt)] rounded-xl border border-[var(--border)] mt-4 shadow-sm">
            <button
              type="button"
              onClick={() => setCurrency('INR')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                currency === 'INR' ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow' : 'text-[var(--text-muted)] hover:text-[var(--text)]'
              }`}
            >
              INR (₹)
            </button>
            <button
              type="button"
              onClick={() => setCurrency('USD')}
              className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                currency === 'USD' ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow' : 'text-[var(--text-muted)] hover:text-[var(--text)]'
              }`}
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
            const price = currency === 'INR' ? `₹${plan.price_inr}` : `$${plan.price_usd}`;

            return (
              <div
                key={plan.id}
                className={`relative flex flex-col justify-between rounded-2xl p-5 border transition-all ${
                  isFeatured
                    ? 'bg-[var(--surface)] border-blue-500 shadow-md ring-2 ring-blue-500/20'
                    : 'bg-[var(--surface)] border-[var(--border)] hover:border-[var(--text-muted)]'
                }`}
              >
                {plan.badge && (
                  <span className={`absolute top-4 right-4 px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                    isFeatured ? 'bg-blue-600 text-white shadow' : 'bg-[var(--bg-alt)] text-[var(--text-muted)] border border-[var(--border)]'
                  }`}>
                    {plan.badge}
                  </span>
                )}

                <div>
                  <h3 className="text-base font-bold text-[var(--text)] mb-1">{plan.name}</h3>
                  <div className="flex items-baseline gap-1 mb-3">
                    <span className="text-2xl font-black text-[var(--text)]">{plan.price_inr === 0 ? 'Free' : price}</span>
                    {plan.price_inr > 0 && <span className="text-xs font-semibold text-[var(--text-muted)]">/mo</span>}
                  </div>

                  <div className="p-2.5 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)] mb-4 text-xs space-y-1">
                    <div className="flex justify-between text-[var(--text-muted)]">
                      <span>Resolution:</span>
                      <strong className="text-[var(--text)] font-bold">{plan.max_res}</strong>
                    </div>
                    <div className="flex justify-between text-[var(--text-muted)]">
                      <span>Credits:</span>
                      <strong className="text-amber-500 font-bold">{plan.credits} / mo</strong>
                    </div>
                    <div className="flex justify-between text-[var(--text-muted)]">
                      <span>Max Clip:</span>
                      <strong className="text-[var(--text)] font-bold">{plan.max_duration}</strong>
                    </div>
                  </div>

                  <ul className="space-y-2 mb-5">
                    {plan.features.map((f, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs font-medium text-[var(--text)]">
                        <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <button
                  type="button"
                  disabled={loadingPlan === plan.id || isCurrent}
                  onClick={() => handleCheckout(plan)}
                  className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                    isCurrent
                      ? 'bg-[var(--bg-alt)] text-[var(--text-muted)] border border-[var(--border)] cursor-default'
                      : isFeatured
                      ? 'bg-blue-600 hover:bg-blue-700 text-white font-bold shadow-md'
                      : 'bg-[var(--primary)] hover:opacity-90 text-[var(--on-primary)] font-bold shadow-sm'
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

        <div className="mt-6 pt-4 border-t border-[var(--border)] flex flex-wrap items-center justify-between text-xs text-[var(--text-muted)] gap-3">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-500" />
            <span>Secure 256-bit encryption • Global cards, UPI & NetBanking accepted via Dodo Payments</span>
          </div>
          <button type="button" onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text)] underline cursor-pointer">
            Continue with current plan
          </button>
        </div>
      </div>
    </div>
  );
}
