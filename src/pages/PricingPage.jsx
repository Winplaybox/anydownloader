import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Crown, Check, Zap, Sparkles, Shield, Loader2, ArrowRight, Video, Flame, Film, HelpCircle, Clock, Gift, RefreshCw, Globe2, CreditCard } from 'lucide-react';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

export const CURRENCIES = [
  { code: 'INR', symbol: '₹', name: 'India (INR)', flag: '🇮🇳', rate: 1 },
  { code: 'USD', symbol: '$', name: 'United States (USD)', flag: '🇺🇸', rate: 0.012 },
  { code: 'EUR', symbol: '€', name: 'Europe (EUR)', flag: '🇪🇺', rate: 0.011 },
  { code: 'GBP', symbol: '£', name: 'United Kingdom (GBP)', flag: '🇬🇧', rate: 0.0095 },
  { code: 'AED', symbol: 'AED ', name: 'UAE (AED)', flag: '🇦🇪', rate: 0.044 },
  { code: 'CAD', symbol: 'CA$', name: 'Canada (CAD)', flag: '🇨🇦', rate: 0.0165 },
  { code: 'AUD', symbol: 'AU$', name: 'Australia (AUD)', flag: '🇦🇺', rate: 0.0185 },
];

export function formatPrice(priceInr, currCode) {
  if (priceInr === 0) return 'Free';
  const c = CURRENCIES.find((item) => item.code === currCode) || CURRENCIES[0];
  if (currCode === 'INR') return `₹${priceInr.toLocaleString('en-IN')}`;
  const converted = Math.round(priceInr * c.rate);
  return `${c.symbol}${converted.toLocaleString()}`;
}

export function detectDefaultCurrency() {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
    const lang = (navigator.language || '').toLowerCase();
    if (tz.includes('Calcutta') || tz.includes('Kolkata') || lang.startsWith('hi') || lang.includes('-in')) {
      return 'INR';
    }
    if (tz.includes('London') || tz.includes('Belfast') || lang === 'en-gb') {
      return 'GBP';
    }
    if (tz.includes('Europe') || tz.includes('Paris') || tz.includes('Berlin') || tz.includes('Madrid') || tz.includes('Rome')) {
      return 'EUR';
    }
    if (tz.includes('Dubai') || tz.includes('Muscat') || tz.includes('Riyadh')) {
      return 'AED';
    }
    if (tz.includes('Toronto') || tz.includes('Vancouver') || lang.includes('-ca')) {
      return 'CAD';
    }
    if (tz.includes('Sydney') || tz.includes('Melbourne') || lang.includes('-au')) {
      return 'AUD';
    }
  } catch {}
  return 'USD';
}

// 1. Monthly Plans (7 Tiers)
export const MONTHLY_PLANS = [
  {
    id: 'free',
    name: 'Free Trial',
    tagline: 'Get started and test video rendering',
    price_inr: 0,
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

// 2. Yearly Plans (Save 20% / 2 Months Free)
export const YEARLY_PLANS = [
  {
    id: 'plan1_yearly',
    name: 'Starter (Annual)',
    tagline: 'Ideal for social media creators',
    price_inr: 2870,
    monthly_inr: 239,
    max_res: '720p HD',
    max_duration: '60s',
    credits: 30,
    badge: 'Save 20%',
    features: [
      '720p HD crisp exports',
      '30 render credits every month',
      '60-second video duration',
      'Full voice library',
      'Save ₹718 annually (2 Months Free)',
      'Billed annually'
    ]
  },
  {
    id: 'plan2_yearly',
    name: 'Creator (Annual)',
    tagline: 'Best for active YouTube & TikTok creators',
    price_inr: 5750,
    monthly_inr: 479,
    max_res: '1080p FHD',
    max_duration: '90s',
    credits: 75,
    badge: 'Best Value (Save 20%)',
    features: [
      '1080p Full HD video exports',
      '75 render credits every month',
      '90-second video clips',
      'All 50+ voices & captions',
      'Priority render queue',
      'Save ₹1,438 annually (2 Months Free)'
    ]
  },
  {
    id: 'plan3_yearly',
    name: 'Pro (Annual)',
    tagline: 'For power creators & growing channels',
    price_inr: 9590,
    monthly_inr: 799,
    max_res: '2K QHD (1440p)',
    max_duration: '120s',
    credits: 150,
    badge: 'Save 20%',
    features: [
      '2K QHD (1440p) ultra-sharp output',
      '150 render credits every month',
      '2-minute video clips',
      'Dedicated worker priority',
      'Save ₹2,398 annually (2 Months Free)'
    ]
  },
  {
    id: 'plan4_yearly',
    name: 'Studio (Annual)',
    tagline: 'For production studios & content agencies',
    price_inr: 16300,
    monthly_inr: 1358,
    max_res: '3K Ultra (1800p)',
    max_duration: '180s',
    credits: 300,
    badge: 'Save 20%',
    features: [
      '3K Ultra (1800p) resolution',
      '300 render credits every month',
      '3-minute long clips',
      'Zero queue wait times',
      'Save ₹4,088 annually (2 Months Free)'
    ]
  },
  {
    id: 'plan5_yearly',
    name: 'Agency (Annual)',
    tagline: 'For marketing teams & daily video publishing',
    price_inr: 28790,
    monthly_inr: 2399,
    max_res: '4K UHD (2160p)',
    max_duration: '300s',
    credits: 600,
    badge: 'Save 20%',
    features: [
      '4K Cinema UHD (2160p) master exports',
      '600 render credits every month',
      '5-minute longform clips',
      'Top tier queue priority',
      'Save ₹7,198 annually (2 Months Free)'
    ]
  },
  {
    id: 'plan6_yearly',
    name: 'Enterprise (Annual)',
    tagline: 'Maximum fidelity & hardware-isolated GPU',
    price_inr: 57590,
    monthly_inr: 4799,
    max_res: '8K Ultra (4320p)',
    max_duration: '300s',
    credits: 1500,
    badge: 'VIP 8K (Save 20%)',
    features: [
      '8K Ultra (4320p) maximum fidelity',
      '1,500 render credits every month',
      'Hardware-isolated GPU rendering',
      'VIP 24/7 dedicated queue',
      'Save ₹14,398 annually (2 Months Free)'
    ]
  }
];

// 3. One-Time Credit Packs (Never Expire)
export const CREDIT_PACKS = [
  {
    id: 'pack_100',
    name: '100 Credits Pack',
    tagline: 'Quick top-up for short projects and quick edits',
    price_inr: 299,
    credits: 100,
    badge: 'Starter Top-up',
    per_credit_inr: '₹2.99 / credit',
    features: [
      '100 Render Credits added instantly',
      'Credits never expire',
      'Usable on all unlocked resolutions',
      'Full voice library & captions',
      'One-time payment, no recurring charge'
    ]
  },
  {
    id: 'pack_300',
    name: '300 Credits Pack',
    tagline: 'Great for weekly creators making shorts & reels',
    price_inr: 699,
    credits: 300,
    badge: 'Popular',
    per_credit_inr: '₹2.33 / credit',
    features: [
      '300 Render Credits added instantly',
      'Credits never expire',
      'Up to 1440p 2K export support',
      'Fast queue priority',
      'One-time payment, no recurring charge'
    ]
  },
  {
    id: 'pack_500',
    name: '500 Credits Studio Pack',
    tagline: 'Best value for high-volume creators and agencies',
    price_inr: 999,
    credits: 500,
    badge: 'Best Value',
    per_credit_inr: '₹1.99 / credit',
    features: [
      '500 Render Credits added instantly',
      'Credits never expire',
      'Up to 4K Cinema UHD export eligible',
      'Commercial usage license included',
      'One-time payment, no recurring charge'
    ]
  },
  {
    id: 'pack_1500',
    name: '1,500 Credits VIP Pack',
    tagline: 'Maximum volume for production houses & studios',
    price_inr: 2499,
    credits: 1500,
    badge: 'VIP Volume',
    per_credit_inr: '₹1.66 / credit',
    features: [
      '1,500 Render Credits added instantly',
      'Credits never expire',
      'All resolutions (up to 8K Ultra)',
      'Hardware-isolated GPU priority',
      'One-time payment, no recurring charge'
    ]
  }
];

// 4. 24-Hour Creator Pass
export const DAY_PASS = {
  id: 'day_pass',
  name: '24-Hour Creator Pass',
  tagline: 'Need high-res rendering right now without any monthly commitment? Instant 24-hour full access.',
  price_inr: 99,
  max_res: '1080p Full HD',
  max_duration: '90s',
  credits: 15,
  badge: '1-Day Pass (No Subscription)',
  features: [
    '15 Render Credits unlocked immediately',
    '1080p Full HD crystal-clear exports',
    '90-second video clips length',
    'All 50+ AI voices & captions unlocked',
    'Priority render queue for 24 hours',
    'Single one-time payment of ₹99 / $1.50'
  ]
};

export default function PricingPage() {
  const [currency, setCurrency] = useState(() => {
    try {
      const saved = localStorage.getItem('ovd_currency');
      return saved || detectDefaultCurrency();
    } catch {
      return 'INR';
    }
  });

  const [billingTab, setBillingTab] = useState('monthly'); // 'monthly' | 'yearly' | 'daypass' | 'packs'
  const [session, setSession] = useState(null);
  const [loadingPlan, setLoadingPlan] = useState('');
  const [error, setError] = useState('');
  const [resetting, setResetting] = useState(false);

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

  function handleCurrencyChange(c) {
    setCurrency(c);
    try { localStorage.setItem('ovd_currency', c); } catch {}
  }

  function handleResetSession() {
    setResetting(true);
    localStorage.removeItem('wpb_token');
    localStorage.removeItem('wpb_guest_id');
    localStorage.removeItem('wpb_session_data');
    setTimeout(() => {
      window.location.reload();
    }, 400);
  }

  async function handleCheckout(item) {
    if (item.id === 'free') {
      window.location.href = '/ai-video-editor';
      return;
    }

    setError('');
    setLoadingPlan(item.id);

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
          plan_id: item.id,
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
  const isGuest = session?.is_guest ?? true;
  const currObj = CURRENCIES.find((c) => c.code === currency) || CURRENCIES[0];

  return (
    <div className="py-10 sm:py-16 max-w-7xl mx-auto px-4 sm:px-6">
      {/* Header Banner */}
      <div className="text-center max-w-3xl mx-auto mb-10 sm:mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-500 text-xs font-bold mb-4 uppercase tracking-wider">
          <Crown className="w-4 h-4 text-amber-500" />
          <span>7-Tier Output Quality & Render Plans</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-black text-[var(--text)] tracking-tight mb-4">
          Choose the Perfect Plan for Your Content
        </h1>
        <p className="text-sm sm:text-base text-[var(--text-muted)] max-w-2xl mx-auto leading-relaxed">
          Unlock 720p HD, 1080p FHD, 2K, 3K, 4K Cinema, and 8K Ultra exports. Powered by Dodo Payments with global card & UPI support.
        </p>

        {/* Currency Selector with Auto-Detect */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-6">
          <span className="text-xs font-semibold text-[var(--text-muted)] flex items-center gap-1.5 mr-1">
            <Globe2 className="w-4 h-4 text-blue-500" /> Currency:
          </span>
          <div className="inline-flex flex-wrap items-center justify-center gap-1 p-1 bg-[var(--surface)] rounded-2xl border border-[var(--border)] shadow-sm">
            {CURRENCIES.map((c) => (
              <button
                key={c.code}
                type="button"
                onClick={() => handleCurrencyChange(c.code)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                  currency === c.code
                    ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--bg-alt)]'
                }`}
              >
                <span>{c.flag}</span>
                <span>{c.code} ({c.symbol})</span>
              </button>
            ))}
          </div>
        </div>

        {/* Billing Tabs */}
        <div className="inline-flex flex-wrap items-center justify-center p-1.5 bg-[var(--surface)] rounded-2xl border border-[var(--border)] mt-6 shadow-sm gap-1">
          <button
            type="button"
            onClick={() => setBillingTab('monthly')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer ${
              billingTab === 'monthly'
                ? 'bg-blue-600 text-white shadow'
                : 'text-[var(--text-muted)] hover:text-[var(--text)]'
            }`}
          >
            Monthly Plans
          </button>
          <button
            type="button"
            onClick={() => setBillingTab('yearly')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
              billingTab === 'yearly'
                ? 'bg-blue-600 text-white shadow'
                : 'text-[var(--text-muted)] hover:text-[var(--text)]'
            }`}
          >
            <span>Yearly (Save 20%)</span>
            <span className="px-1.5 py-0.5 rounded-full bg-emerald-500 text-white text-[10px] font-black uppercase">2 Mos Free</span>
          </button>
          <button
            type="button"
            onClick={() => setBillingTab('daypass')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
              billingTab === 'daypass'
                ? 'bg-blue-600 text-white shadow'
                : 'text-[var(--text-muted)] hover:text-[var(--text)]'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>24-Hour Pass (₹99)</span>
          </button>
          <button
            type="button"
            onClick={() => setBillingTab('packs')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
              billingTab === 'packs'
                ? 'bg-blue-600 text-white shadow'
                : 'text-[var(--text-muted)] hover:text-[var(--text)]'
            }`}
          >
            <Zap className="w-3.5 h-3.5 text-amber-500" />
            <span>Credit Packs</span>
          </button>
        </div>

        {/* Guest Session Reset Pill */}
        {isGuest && (
          <div className="mt-4 flex items-center justify-center gap-2">
            <span className="text-[11px] text-[var(--text-muted)]">
              Current Session: Guest ({session?.credits ?? 2} credits, {session?.plan || 'free'})
            </span>
            <button
              type="button"
              onClick={handleResetSession}
              disabled={resetting}
              className="text-[11px] text-blue-500 hover:underline font-bold flex items-center gap-1 cursor-pointer"
            >
              <RefreshCw className={`w-3 h-3 ${resetting ? 'animate-spin' : ''}`} />
              <span>Reset to Fresh Free Guest</span>
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="max-w-xl mx-auto mb-8 p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-500 text-sm text-center font-medium">
          {error}
        </div>
      )}

      {/* TAB 1: MONTHLY 7-TIER PLANS */}
      {billingTab === 'monthly' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {MONTHLY_PLANS.map((plan) => {
            const isCurrent = userPlan === plan.id;
            const isPopular = plan.id === 'plan2' || plan.id === 'plan1';
            const price = formatPrice(plan.price_inr, currency);

            return (
              <div
                key={plan.id}
                className={`relative flex flex-col justify-between rounded-3xl p-6 sm:p-7 border transition-all ${
                  isPopular
                    ? 'bg-[var(--surface)] border-blue-500 shadow-xl shadow-blue-500/10 ring-2 ring-blue-500/20'
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
                      {price}
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
                      <strong className="text-amber-500 font-extrabold">{plan.credits} credits</strong>
                    </div>
                    <div className="flex justify-between items-center text-[var(--text-muted)]">
                      <span>Max Video Length:</span>
                      <strong className="text-[var(--text)] font-extrabold">{plan.max_duration}</strong>
                    </div>
                  </div>

                  {/* Features List */}
                  <ul className="space-y-2.5 mb-6 text-xs text-[var(--text-muted)]">
                    {plan.features.map((feat, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-xs font-medium text-[var(--text)]">
                        <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
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
                        ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20'
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
      )}

      {/* TAB 2: YEARLY PLANS (SAVE 20%) */}
      {billingTab === 'yearly' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {YEARLY_PLANS.map((plan) => {
            const isFeatured = plan.id === 'plan2_yearly' || plan.id === 'plan3_yearly';
            const price = formatPrice(plan.price_inr, currency);
            const monthlyEquiv = formatPrice(plan.monthly_inr, currency);

            return (
              <div
                key={plan.id}
                className={`relative flex flex-col justify-between rounded-3xl p-6 sm:p-7 border transition-all ${
                  isFeatured
                    ? 'bg-[var(--surface)] border-blue-500 shadow-xl shadow-blue-500/10 ring-2 ring-blue-500/20'
                    : 'bg-[var(--surface)] border-[var(--border)] hover:border-[var(--text-muted)]'
                }`}
              >
                <span className="absolute top-5 right-5 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-500 text-white shadow">
                  {plan.badge}
                </span>

                <div>
                  <h2 className="text-lg font-bold text-[var(--text)] mb-1">{plan.name}</h2>
                  <p className="text-xs text-[var(--text-muted)] mb-4 min-h-[32px]">{plan.tagline}</p>

                  <div className="flex items-baseline gap-1.5 mb-1">
                    <span className="text-3xl sm:text-4xl font-black text-[var(--text)]">
                      {price}
                    </span>
                    <span className="text-xs text-[var(--text-muted)] font-medium">/ year</span>
                  </div>
                  <div className="text-xs text-emerald-500 font-bold mb-5">
                    Effectively {monthlyEquiv} / month (Save 20%)
                  </div>

                  <div className="p-3.5 rounded-2xl bg-[var(--bg-alt)] border border-[var(--border)] mb-5 text-xs space-y-2">
                    <div className="flex justify-between items-center text-[var(--text-muted)]">
                      <span>Export Quality:</span>
                      <strong className="text-[var(--text)] font-extrabold">{plan.max_res}</strong>
                    </div>
                    <div className="flex justify-between items-center text-[var(--text-muted)]">
                      <span>Monthly Credits:</span>
                      <strong className="text-amber-500 font-extrabold">{plan.credits} credits / mo</strong>
                    </div>
                    <div className="flex justify-between items-center text-[var(--text-muted)]">
                      <span>Max Video Length:</span>
                      <strong className="text-[var(--text)] font-extrabold">{plan.max_duration}</strong>
                    </div>
                  </div>

                  <ul className="space-y-2.5 mb-6 text-xs text-[var(--text-muted)]">
                    {plan.features.map((feat, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-xs font-medium text-[var(--text)]">
                        <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <button
                    type="button"
                    disabled={loadingPlan === plan.id}
                    onClick={() => handleCheckout(plan)}
                    className="w-full py-3 px-4 rounded-xl text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-500/20 transition-all cursor-pointer"
                  >
                    {loadingPlan === plan.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <>
                        <span>Upgrade to Annual (Save 20%)</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TAB 3: 24-HOUR CREATOR DAY PASS */}
      {billingTab === 'daypass' && (
        <div className="max-w-2xl mx-auto">
          <div className="relative rounded-3xl p-8 sm:p-10 border border-amber-500 bg-[var(--surface)] shadow-2xl ring-2 ring-amber-500/20">
            <div className="flex items-center justify-between gap-4 mb-4">
              <span className="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-amber-500 text-black">
                {DAY_PASS.badge}
              </span>
              <span className="text-xs font-bold text-amber-500 flex items-center gap-1">
                <Clock className="w-4 h-4" /> 24-Hour Access
              </span>
            </div>

            <h2 className="text-2xl sm:text-3xl font-black text-[var(--text)] mb-2">{DAY_PASS.name}</h2>
            <p className="text-xs sm:text-sm text-[var(--text-muted)] mb-6 leading-relaxed">{DAY_PASS.tagline}</p>

            <div className="flex items-baseline gap-2 mb-6">
              <span className="text-4xl sm:text-5xl font-black text-[var(--text)]">
                {formatPrice(DAY_PASS.price_inr, currency)}
              </span>
              <span className="text-sm text-[var(--text-muted)] font-medium">/ 24 hours (One-time, no subscription)</span>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--bg-alt)] border border-[var(--border)] mb-6 grid sm:grid-cols-3 gap-3 text-xs text-center">
              <div>
                <span className="text-[var(--text-muted)] block">Credits Unlocked</span>
                <strong className="text-amber-500 text-base font-extrabold">{DAY_PASS.credits} credits</strong>
              </div>
              <div>
                <span className="text-[var(--text-muted)] block">Export Resolution</span>
                <strong className="text-[var(--text)] text-base font-extrabold">{DAY_PASS.max_res}</strong>
              </div>
              <div>
                <span className="text-[var(--text-muted)] block">Max Clip Length</span>
                <strong className="text-[var(--text)] text-base font-extrabold">{DAY_PASS.max_duration}</strong>
              </div>
            </div>

            <ul className="space-y-3 mb-8 text-sm">
              {DAY_PASS.features.map((feat, idx) => (
                <li key={idx} className="flex items-start gap-3 font-medium text-[var(--text)]">
                  <Check className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <span>{feat}</span>
                </li>
              ))}
            </ul>

            <button
              type="button"
              disabled={loadingPlan === DAY_PASS.id}
              onClick={() => handleCheckout(DAY_PASS)}
              className="w-full py-3.5 px-6 rounded-2xl text-sm font-black uppercase tracking-wider flex items-center justify-center gap-2 bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 hover:opacity-95 text-black shadow-xl shadow-orange-500/20 transition-all cursor-pointer"
            >
              {loadingPlan === DAY_PASS.id ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <span>Activate 24-Hour Pass ({formatPrice(DAY_PASS.price_inr, currency)})</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* TAB 4: CREDIT TOP-UP PACKS (NEVER EXPIRE) */}
      {billingTab === 'packs' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {CREDIT_PACKS.map((pack) => {
            const isBest = pack.id === 'pack_500' || pack.id === 'pack_300';
            const price = formatPrice(pack.price_inr, currency);

            return (
              <div
                key={pack.id}
                className={`relative flex flex-col justify-between rounded-3xl p-6 sm:p-7 border transition-all ${
                  isBest
                    ? 'bg-[var(--surface)] border-amber-500 shadow-xl shadow-amber-500/10 ring-2 ring-amber-500/20'
                    : 'bg-[var(--surface)] border-[var(--border)] hover:border-[var(--text-muted)]'
                }`}
              >
                <span className={`absolute top-5 right-5 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                  isBest ? 'bg-amber-500 text-black shadow' : 'bg-[var(--bg-alt)] text-[var(--text-muted)] border border-[var(--border)]'
                }`}>
                  {pack.badge}
                </span>

                <div>
                  <h2 className="text-lg font-bold text-[var(--text)] mb-1">{pack.name}</h2>
                  <p className="text-xs text-[var(--text-muted)] mb-4 min-h-[32px]">{pack.tagline}</p>

                  <div className="flex items-baseline gap-1.5 mb-1">
                    <span className="text-3xl sm:text-4xl font-black text-[var(--text)]">
                      {price}
                    </span>
                    <span className="text-xs text-[var(--text-muted)] font-medium">one-time</span>
                  </div>
                  <div className="text-xs text-amber-500 font-bold mb-5">
                    {pack.credits} Credits • Never Expire
                  </div>

                  <ul className="space-y-2.5 mb-6 text-xs text-[var(--text-muted)]">
                    {pack.features.map((feat, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 text-xs font-medium text-[var(--text)]">
                        <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                        <span>{feat}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <button
                    type="button"
                    disabled={loadingPlan === pack.id}
                    onClick={() => handleCheckout(pack)}
                    className="w-full py-3 px-4 rounded-xl text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:opacity-90 text-black shadow-md transition-all cursor-pointer"
                  >
                    {loadingPlan === pack.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <>
                        <span>Buy {pack.credits} Credits</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* International Payments & Security Banner */}
      <div className="mt-16 sm:mt-20 max-w-4xl mx-auto rounded-3xl bg-[var(--surface)] border border-[var(--border)] p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row items-center gap-5 pb-6 border-b border-[var(--border)]">
          <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/25 flex items-center justify-center shrink-0">
            <Globe2 className="w-7 h-7 text-blue-500" />
          </div>
          <div>
            <h3 className="text-lg font-black text-[var(--text)]">Global Payments in 150+ Countries via Dodo Payments</h3>
            <p className="text-xs text-[var(--text-muted)] mt-1 leading-relaxed">
              Accepting <strong>UPI (GPay, PhonePe, Paytm, BHIM)</strong>, <strong>RuPay</strong>, <strong>NetBanking</strong>, and international <strong>Visa, MasterCard, American Express, Apple Pay & Google Pay</strong> with instant automated entitlement delivery.
            </p>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-4 text-xs text-[var(--text-muted)]">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-500" />
            <span>256-Bit Bank Grade SSL Encryption</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-500" />
            <span>Credits Added Instantly Upon Payment</span>
          </div>
          <div className="flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-purple-500" />
            <span>Multi-Currency Auto Billing</span>
          </div>
        </div>
      </div>

      {/* Frequently Asked Questions */}
      <div className="mt-12 max-w-4xl mx-auto rounded-3xl bg-[var(--surface)] border border-[var(--border)] p-6 sm:p-10 shadow-sm">
        <h3 className="text-xl font-black text-[var(--text)] mb-6">Frequently Asked Questions</h3>
        <div className="grid sm:grid-cols-2 gap-6 text-xs text-[var(--text-muted)]">
          <div>
            <h4 className="font-bold text-sm text-[var(--text)] mb-1">What resolution do I get on the Free plan?</h4>
            <p className="leading-relaxed">Free users get up to 480p SD (below 720p) with 2 free credits refreshed every day. Upgrade to 720p, 1080p, 2K, 4K, or 8K anytime.</p>
          </div>
          <div>
            <h4 className="font-bold text-sm text-[var(--text)] mb-1">What is the 24-Hour Creator Pass?</h4>
            <p className="leading-relaxed">If you just have a single video to render and don't want a recurring subscription, the 24-Hour Pass gives you 15 credits and 1080p FHD for ₹99 ($1.50) without any renewal.</p>
          </div>
          <div>
            <h4 className="font-bold text-sm text-[var(--text)] mb-1">Do credit packs expire?</h4>
            <p className="leading-relaxed">No! All one-time credit top-up packs (100, 300, 500, 1500 credits) never expire and remain in your account balance permanently.</p>
          </div>
          <div>
            <h4 className="font-bold text-sm text-[var(--text)] mb-1">Can I pay from outside India?</h4>
            <p className="leading-relaxed">Yes! Dodo Payments supports customers worldwide with international credit/debit cards, Apple Pay, and Google Pay in USD, EUR, GBP, AED, CAD, AUD and local currencies.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
