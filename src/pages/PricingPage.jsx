import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Crown, Check, Zap, Sparkles, Shield, Loader2, ArrowRight, Video, Flame, Film, HelpCircle } from 'lucide-react';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

export const PLANS = [
  {
    id: 'free',
    name: 'Free Trial',
    tagline: 'Get started and test video rendering',
    price_inr: 0,
    price_usd: 0,
    max_res: '480p SD',
    max_res_val: 480,
    max_duration: '30s',
    credits: 2,
    badge: 'Free Forever',
    features: [
      'Up to 480p SD output (below 720p)',
      '2 free credits daily',
      'Standard voices & styles',
      'Community render queue',
      'Subtitles & SRT download',
    ]
  },
  {
    id: 'plan1',
    name: 'Starter',
    tagline: 'Ideal for social media creators',
    price_inr: 299,
    price_usd: 4,
    max_res: '720p HD',
    max_res_val: 720,
    max_duration: '60s',
    credits: 30,
    badge: 'Popular',
    features: [
      '720p HD crisp exports',
      '30 render credits per month',
      '60-second video duration',
      'Full voice library',
      'Standard priority queue',
      'No watermark & full rights',
    ]
  },
  {
    id: 'plan2',
    name: 'Creator',
    tagline: 'Best for active YouTube & TikTok creators',
    price_inr: 599,
    price_usd: 8,
    max_res: '1080p FHD',
    max_res_val: 1080,
    max_duration: '90s',
    credits: 75,
    badge: 'Best Value',
    features: [
      '1080p Full HD video exports',
      '75 render credits per month',
      '90-second video clips',
      'All 50+ voices & captions',
      'Priority render queue',
      'Broadcast audio mastering (-14 LUFS)',
    ]
  },
  {
    id: 'plan3',
    name: 'Pro',
    tagline: 'For power creators & growing channels',
    price_inr: 999,
    price_usd: 13,
    max_res: '2K QHD (1440p)',
    max_res_val: 1440,
    max_duration: '120s',
    credits: 150,
    badge: 'Pro Choice',
    features: [
      '2K QHD (1440p) ultra-sharp output',
      '150 render credits per month',
      '2-minute video clips',
      'Dedicated worker render priority',
      'Custom brand highlight colors',
      'Export SRT, WAV & TXT assets',
    ]
  },
  {
    id: 'plan4',
    name: 'Studio',
    tagline: 'For production studios & content agencies',
    price_inr: 1699,
    price_usd: 22,
    max_res: '3K Ultra (1800p)',
    max_res_val: 1800,
    max_duration: '180s',
    credits: 300,
    badge: 'Studio',
    features: [
      '3K Ultra (1800p) resolution',
      '300 render credits per month',
      '3-minute long clips',
      'Zero queue wait / Instant render slot',
      'Commercial usage license',
      'Priority customer support',
    ]
  },
  {
    id: 'plan5',
    name: 'Business',
    tagline: 'For marketing teams & daily video publishing',
    price_inr: 2999,
    price_usd: 40,
    max_res: '4K UHD (2160p)',
    max_res_val: 2160,
    max_duration: '300s',
    credits: 600,
    badge: 'Agency',
    features: [
      '4K Cinema UHD (2160p) master exports',
      '600 render credits per month',
      '5-minute longform clips',
      'Top tier queue priority',
      'Unlimited instant voice previews',
      'Bulk batch rendering eligible',
    ]
  },
  {
    id: 'plan6',
    name: 'Enterprise',
    tagline: 'Maximum fidelity & hardware-isolated performance',
    price_inr: 5999,
    price_usd: 80,
    max_res: '8K Ultra (4320p)',
    max_res_val: 4320,
    max_duration: '300s',
    credits: 1500,
    badge: 'VIP 8K',
    features: [
      '8K Ultra (4320p) maximum fidelity',
      '1,500 render credits per month',
      'Hardware-isolated GPU rendering',
      'VIP 24/7 dedicated queue',
      'Custom AI voice cloning access',
      'Dedicated account manager',
    ]
  }
];

export default function PricingPage() {
  const [currency, setCurrency] = useState('INR');
  const [session, setSession] = useState(null);
  const [loadingPlan, setLoadingPlan] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    document.title = 'Plans & Pricing — AI Video Editor (480p to 8K) | OVD';
    const cached = localStorage.getItem('wpb_session_data');
    if (cached) {
      try { setSession(JSON.parse(cached)); } catch {}
    }

    const token = localStorage.getItem('wpb_token');
    const guestId = localStorage.getItem('wpb_guest_id');
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (guestId) headers['x-guest-id'] = guestId;

    fetch(`${BACKEND_BASE}/api/auth/session`, { credentials: 'include', headers })
      .then((r) => r.json())
      .then((d) => {
        if (d.ok && (d.identity || d.session)) {
          const s = d.identity || d.session;
          setSession(s);
          localStorage.setItem('wpb_session_data', JSON.stringify(s));
        }
      })
      .catch(console.error);
  }, []);

  async function handleCheckout(plan) {
    if (plan.id === 'free') {
      window.location.href = '/ai-video-editor';
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
        setError(data.error || 'Failed to start Dodo Payments checkout. Please try again.');
        setLoadingPlan('');
      }
    } catch (err) {
      setError(err.message || 'Payment server unreachable.');
      setLoadingPlan('');
    }
  }

  const userPlan = session?.plan || 'free';

  return (
    <div className="py-10 sm:py-16 max-w-7xl mx-auto px-4 sm:px-6">
      {/* Header Banner */}
      <div className="text-center max-w-3xl mx-auto mb-10 sm:mb-14">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-bold mb-4 uppercase tracking-wider">
          <Crown className="w-4 h-4 text-amber-400" />
          <span>7-Tier Output Quality & Render Plans</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-[var(--text)] tracking-tight mb-4">
          Choose the Perfect Plan for Your Content
        </h1>
        <p className="text-sm sm:text-base text-[var(--text-muted)] max-w-2xl mx-auto leading-relaxed">
          Free tier offers up to 480p SD with 2 free credits daily. Upgrade to unlock 720p HD, 1080p FHD, 2K, 3K, 4K Cinema, and 8K Ultra exports powered by Dodo Payments.
        </p>

        {/* Currency Switcher */}
        <div className="inline-flex items-center gap-1 p-1.5 bg-[var(--surface)] rounded-2xl border border-[var(--border)] mt-6 shadow-sm">
          <button
            type="button"
            onClick={() => setCurrency('INR')}
            className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              currency === 'INR' ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow' : 'text-[var(--text-muted)] hover:text-[var(--text)]'
            }`}
          >
            INR (₹)
          </button>
          <button
            type="button"
            onClick={() => setCurrency('USD')}
            className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              currency === 'USD' ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow' : 'text-[var(--text-muted)] hover:text-[var(--text)]'
            }`}
          >
            USD ($)
          </button>
        </div>
      </div>

      {error && (
        <div className="max-w-xl mx-auto mb-8 p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center font-medium">
          {error}
        </div>
      )}

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {PLANS.map((plan) => {
          const isCurrent = userPlan === plan.id;
          const isPopular = plan.id === 'plan2' || plan.id === 'plan1';
          const price = currency === 'INR' ? `₹${plan.price_inr}` : `$${plan.price_usd}`;

          return (
            <div
              key={plan.id}
              className={`relative flex flex-col justify-between rounded-3xl p-6 sm:p-7 border transition-all ${
                isPopular
                  ? 'bg-gradient-to-b from-blue-950/20 via-[var(--surface)] to-[var(--surface)] border-blue-500/50 shadow-xl shadow-blue-500/5 ring-1 ring-blue-500/30'
                  : 'bg-[var(--surface)] border-[var(--border)] hover:border-[var(--text-muted)]'
              }`}
            >
              {plan.badge && (
                <span className={`absolute top-5 right-5 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                  isPopular ? 'bg-blue-600 text-white shadow' : 'bg-[var(--bg-alt)] text-[var(--text-muted)] border border-[var(--border)]'
                }`}>
                  {plan.badge}
                </span>
              )}

              <div>
                <h2 className="text-lg font-bold text-[var(--text)] mb-1">{plan.name}</h2>
                <p className="text-xs text-[var(--text-muted)] mb-4 min-h-[32px]">{plan.tagline}</p>

                <div className="flex items-baseline gap-1.5 mb-5">
                  <span className="text-3xl sm:text-4xl font-black text-[var(--text)]">
                    {plan.price_inr === 0 ? 'Free' : price}
                  </span>
                  {plan.price_inr > 0 && (
                    <span className="text-xs text-[var(--text-muted)] font-medium">/ month</span>
                  )}
                </div>

                {/* Key Spec Card */}
                <div className="p-3.5 rounded-2xl bg-[var(--bg-alt)] border border-[var(--border)] mb-5 text-xs space-y-2">
                  <div className="flex justify-between items-center text-[var(--text-muted)]">
                    <span>Export Quality:</span>
                    <strong className="text-[var(--text)] font-extrabold">{plan.max_res}</strong>
                  </div>
                  <div className="flex justify-between items-center text-[var(--text-muted)]">
                    <span>Monthly Credits:</span>
                    <strong className="text-amber-400 font-extrabold">{plan.credits} credits</strong>
                  </div>
                  <div className="flex justify-between items-center text-[var(--text-muted)]">
                    <span>Max Video Length:</span>
                    <strong className="text-[var(--text)] font-extrabold">{plan.max_duration}</strong>
                  </div>
                </div>

                {/* Features List */}
                <ul className="space-y-2.5 mb-6 text-xs text-[var(--text-muted)]">
                  {plan.features.map((feat, idx) => (
                    <li key={idx} className="flex items-start gap-2.5">
                      <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{feat}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Action Button */}
              <div>
                <button
                  type="button"
                  disabled={loadingPlan === plan.id}
                  onClick={() => handleCheckout(plan)}
                  className={`w-full py-3 px-4 rounded-xl text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 transition-all cursor-pointer ${
                    isCurrent
                      ? 'bg-[var(--bg-alt)] text-[var(--text-muted)] border border-[var(--border)] cursor-default'
                      : isPopular
                      ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/20'
                      : 'bg-gradient-to-r from-amber-500 to-orange-500 hover:opacity-90 text-black shadow-md'
                  }`}
                >
                  {loadingPlan === plan.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : isCurrent ? (
                    'Current Plan'
                  ) : plan.id === 'free' ? (
                    'Use Free Trial'
                  ) : (
                    <>
                      <span>Upgrade Plan</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Guarantee & FAQs */}
      <div className="mt-16 sm:mt-24 max-w-4xl mx-auto rounded-3xl bg-[var(--surface)] border border-[var(--border)] p-6 sm:p-10 shadow-sm">
        <div className="flex flex-col sm:flex-row items-center gap-4 mb-8 pb-8 border-b border-[var(--border)]">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center shrink-0">
            <Shield className="w-6 h-6 text-amber-400" />
          </div>
          <div>
            <h3 className="text-lg font-black text-[var(--text)]">Secure Checkout via Dodo Payments</h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Supports UPI, Credit/Debit cards, Net Banking, and International Cards with instant credit activation. Cancel or switch plans anytime.
            </p>
          </div>
        </div>

        <h3 className="text-xl font-black text-[var(--text)] mb-6">Frequently Asked Questions</h3>
        <div className="grid sm:grid-cols-2 gap-6 text-xs text-[var(--text-muted)]">
          <div>
            <h4 className="font-bold text-sm text-[var(--text)] mb-1">What resolution do I get on the Free plan?</h4>
            <p className="leading-relaxed">Free users get up to 480p SD (below 720p) with 2 free credits refreshed every day. Upgrade to Plan 1 (720p HD) or Plan 2 (1080p FHD) for crystal-clear social media exports.</p>
          </div>
          <div>
            <h4 className="font-bold text-sm text-[var(--text)] mb-1">How do credits work?</h4>
            <p className="leading-relaxed">1 credit renders a standard video up to 1080p. Higher resolution exports like 2K (2 credits), 4K (3 credits), and 8K (5 credits) consume corresponding hardware capacity.</p>
          </div>
          <div>
            <h4 className="font-bold text-sm text-[var(--text)] mb-1">Can I use the generated videos commercially?</h4>
            <p className="leading-relaxed">Yes! All videos rendered on paid plans include full commercial broadcast rights for YouTube, Instagram Reels, TikTok, and client work with zero watermarks.</p>
          </div>
          <div>
            <h4 className="font-bold text-sm text-[var(--text)] mb-1">Do unused credits roll over?</h4>
            <p className="leading-relaxed">Monthly plan credits are added to your balance upon renewal. You can also top up credits anytime without changing your quality tier.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
