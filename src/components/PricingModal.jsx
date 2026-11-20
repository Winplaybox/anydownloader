import React, { useState } from 'react';
import { X, Check, Zap, Sparkles, Shield, Loader2, ArrowRight, Crown, Clock, Globe2 } from 'lucide-react';
import {
  MONTHLY_PLANS,
  YEARLY_PLANS,
  CREDIT_PACKS,
  DAY_PASS,
  CURRENCIES,
  formatPrice,
  detectDefaultCurrency
} from '../pages/PricingPage.jsx';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

export default function PricingModal({ isOpen, onClose, userPlan = 'free', onPlanUpgraded }) {
  const [currency, setCurrency] = useState(() => {
    try {
      return localStorage.getItem('ovd_currency') || detectDefaultCurrency();
    } catch {
      return 'INR';
    }
  });

  const [billingTab, setBillingTab] = useState('monthly'); // 'monthly' | 'yearly' | 'daypass' | 'packs'
  const [loadingPlan, setLoadingPlan] = useState('');
  const [error, setError] = useState('');

  if (!isOpen) return null;

  function handleCurrencyChange(c) {
    setCurrency(c);
    try { localStorage.setItem('ovd_currency', c); } catch {}
  }

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
          currency: currency,
          return_url: window.location.origin + '/payment/success'
        })
      });

      const data = await res.json();
      if (res.ok && data.ok && data.checkout_url) {
        window.location.href = data.checkout_url;
      } else if (res.status === 401 && data.auth_required) {
        // Paid credits belong to an account, so sign in first and come back here.
        window.location.href = `/login?return=${encodeURIComponent(window.location.pathname + window.location.search)}`;
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

          {/* Currency Switcher */}
          <div className="flex flex-wrap items-center justify-center gap-1.5 p-1 bg-[var(--bg-alt)] rounded-2xl border border-[var(--border)] mt-4 shadow-sm">
            {CURRENCIES.map((c) => (
              <button
                key={c.code}
                type="button"
                onClick={() => handleCurrencyChange(c.code)}
                className={`px-2.5 py-1 rounded-xl text-xs font-bold transition-colors cursor-pointer flex items-center gap-1 ${
                  currency === c.code
                    ? 'bg-[var(--primary)] text-[var(--on-primary)] shadow'
                    : 'text-[var(--text-muted)] hover:text-[var(--text)]'
                }`}
              >
                <span>{c.flag}</span>
                <span>{c.code} ({c.symbol})</span>
              </button>
            ))}
          </div>

          {/* Billing Tabs */}
          <div className="inline-flex flex-wrap items-center justify-center p-1 bg-[var(--surface)] rounded-xl border border-[var(--border)] mt-4 shadow-sm gap-1">
            <button
              type="button"
              onClick={() => setBillingTab('monthly')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                billingTab === 'monthly' ? 'bg-blue-600 text-white shadow' : 'text-[var(--text-muted)] hover:text-[var(--text)]'
              }`}
            >
              Monthly
            </button>
            <button
              type="button"
              onClick={() => setBillingTab('yearly')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1 ${
                billingTab === 'yearly' ? 'bg-blue-600 text-white shadow' : 'text-[var(--text-muted)] hover:text-[var(--text)]'
              }`}
            >
              <span>Yearly</span>
              <span className="px-1.5 py-0.2 rounded-full bg-emerald-500 text-white text-[9px] font-black uppercase">Save 20%</span>
            </button>
            <button
              type="button"
              onClick={() => setBillingTab('daypass')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1 ${
                billingTab === 'daypass' ? 'bg-blue-600 text-white shadow' : 'text-[var(--text-muted)] hover:text-[var(--text)]'
              }`}
            >
              <Clock className="w-3 h-3" />
              <span>24h Pass ({formatPrice(DAY_PASS.price_inr, currency)})</span>
            </button>
            <button
              type="button"
              onClick={() => setBillingTab('packs')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center gap-1 ${
                billingTab === 'packs' ? 'bg-blue-600 text-white shadow' : 'text-[var(--text-muted)] hover:text-[var(--text)]'
              }`}
            >
              <Zap className="w-3 h-3 text-amber-500" />
              <span>Credit Packs</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs text-center font-medium">
            {error}
          </div>
        )}

        {/* TAB 1: MONTHLY */}
        {billingTab === 'monthly' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {MONTHLY_PLANS.map((plan) => {
              const isCurrent = userPlan === plan.id;
              const isFeatured = plan.id === 'plan2' || plan.id === 'plan3';
              const price = formatPrice(plan.price_inr, currency);

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
                      <span className="text-2xl font-black text-[var(--text)]">{price}</span>
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
        )}

        {/* TAB 2: YEARLY (SAVE 20%) */}
        {billingTab === 'yearly' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {YEARLY_PLANS.map((plan) => {
              const isFeatured = plan.id === 'plan2_yearly' || plan.id === 'plan3_yearly';
              const price = formatPrice(plan.price_inr, currency);
              const monthlyEquiv = formatPrice(plan.monthly_inr, currency);

              return (
                <div
                  key={plan.id}
                  className={`relative flex flex-col justify-between rounded-2xl p-5 border transition-all ${
                    isFeatured
                      ? 'bg-[var(--surface)] border-blue-500 shadow-md ring-2 ring-blue-500/20'
                      : 'bg-[var(--surface)] border-[var(--border)]'
                  }`}
                >
                  <span className="absolute top-4 right-4 px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-500 text-white shadow">
                    {plan.badge}
                  </span>

                  <div>
                    <h3 className="text-base font-bold text-[var(--text)] mb-1">{plan.name}</h3>
                    <div className="flex items-baseline gap-1 mb-1">
                      <span className="text-2xl font-black text-[var(--text)]">{price}</span>
                      <span className="text-xs font-semibold text-[var(--text-muted)]">/year</span>
                    </div>
                    <div className="text-[11px] text-emerald-500 font-bold mb-3">
                      Effectively {monthlyEquiv} / mo (Save 20%)
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
                    </div>

                    <ul className="space-y-1.5 mb-5">
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
                    disabled={loadingPlan === plan.id}
                    onClick={() => handleCheckout(plan)}
                    className="w-full py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white shadow-md transition-all cursor-pointer"
                  >
                    {loadingPlan === plan.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <>
                        <span>Upgrade Annual</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* TAB 3: 24-HOUR PASS */}
        {billingTab === 'daypass' && (
          <div className="max-w-xl mx-auto rounded-2xl p-6 border border-amber-500 bg-[var(--surface)] shadow-lg ring-1 ring-amber-500/20 text-center">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-amber-500 text-black mb-3">
              <Clock className="w-3.5 h-3.5" /> {DAY_PASS.badge}
            </div>
            <h3 className="text-xl font-black text-[var(--text)] mb-2">{DAY_PASS.name}</h3>
            <p className="text-xs text-[var(--text-muted)] mb-4">{DAY_PASS.tagline}</p>

            <div className="text-3xl font-black text-[var(--text)] mb-4">
              {formatPrice(DAY_PASS.price_inr, currency)}{' '}
              <span className="text-xs text-[var(--text-muted)] font-normal">/ 24 hours (One-time)</span>
            </div>

            <div className="grid grid-cols-3 gap-2 p-3 bg-[var(--bg-alt)] rounded-xl border border-[var(--border)] mb-5 text-xs">
              <div>
                <span className="text-[var(--text-muted)] block">Credits</span>
                <strong className="text-amber-500 font-bold">{DAY_PASS.credits}</strong>
              </div>
              <div>
                <span className="text-[var(--text-muted)] block">Resolution</span>
                <strong className="text-[var(--text)] font-bold">{DAY_PASS.max_res}</strong>
              </div>
              <div>
                <span className="text-[var(--text-muted)] block">Max Clip</span>
                <strong className="text-[var(--text)] font-bold">{DAY_PASS.max_duration}</strong>
              </div>
            </div>

            <button
              type="button"
              disabled={loadingPlan === DAY_PASS.id}
              onClick={() => handleCheckout(DAY_PASS)}
              className="w-full py-3 px-4 rounded-xl text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:opacity-95 text-black shadow-md transition-all cursor-pointer"
            >
              {loadingPlan === DAY_PASS.id ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <span>Activate 24-Hour Pass ({formatPrice(DAY_PASS.price_inr, currency)})</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        )}

        {/* TAB 4: CREDIT PACKS */}
        {billingTab === 'packs' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {CREDIT_PACKS.map((pack) => {
              const isBest = pack.id === 'pack_500' || pack.id === 'pack_300';
              const price = formatPrice(pack.price_inr, currency);

              return (
                <div
                  key={pack.id}
                  className={`relative flex flex-col justify-between rounded-2xl p-5 border transition-all ${
                    isBest
                      ? 'bg-[var(--surface)] border-amber-500 shadow-md ring-1 ring-amber-500/20'
                      : 'bg-[var(--surface)] border-[var(--border)]'
                  }`}
                >
                  <span className={`absolute top-4 right-4 px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                    isBest ? 'bg-amber-500 text-black shadow' : 'bg-[var(--bg-alt)] text-[var(--text-muted)] border border-[var(--border)]'
                  }`}>
                    {pack.badge}
                  </span>

                  <div>
                    <h3 className="text-base font-bold text-[var(--text)] mb-1">{pack.name}</h3>
                    <div className="flex items-baseline gap-1 mb-1">
                      <span className="text-2xl font-black text-[var(--text)]">{price}</span>
                      <span className="text-xs font-semibold text-[var(--text-muted)]">one-time</span>
                    </div>
                    <div className="text-[11px] text-amber-500 font-bold mb-4">
                      {pack.credits} Credits • Never Expire
                    </div>

                    <ul className="space-y-1.5 mb-5">
                      {pack.features.map((f, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs font-medium text-[var(--text)]">
                          <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                          <span>{f}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <button
                    type="button"
                    disabled={loadingPlan === pack.id}
                    onClick={() => handleCheckout(pack)}
                    className="w-full py-2.5 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 bg-gradient-to-r from-amber-500 to-orange-500 hover:opacity-95 text-black shadow-sm transition-all cursor-pointer"
                  >
                    {loadingPlan === pack.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <>
                        <span>Buy {pack.credits} Credits</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        )}

        <div className="mt-6 pt-4 border-t border-[var(--border)] flex flex-wrap items-center justify-between text-xs text-[var(--text-muted)] gap-3">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-500" />
            <span>Secure 256-bit encryption • Global cards, UPI & NetBanking accepted in 150+ countries via Dodo Payments</span>
          </div>
          <button type="button" onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text)] underline cursor-pointer">
            Continue with current plan
          </button>
        </div>
      </div>
    </div>
  );
}
