import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { CheckCircle2, Crown, Sparkles, Wand2, ArrowRight, UserPlus, ShieldAlert, Check, RefreshCw, Zap } from 'lucide-react';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

export default function PaymentSuccessPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  const query = new URLSearchParams(location.search);
  const planQuery = query.get('plan') || '';
  const sessionId = query.get('session_id') || '';

  useEffect(() => {
    document.title = 'Payment Successful — Plan Activated | OVD';

    async function refreshSession() {
      try {
        const token = localStorage.getItem('wpb_token');
        const guestId = localStorage.getItem('wpb_guest_id');
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        if (guestId) headers['x-guest-id'] = guestId;

        const res = await fetch(`${BACKEND_BASE}/api/auth/session`, {
          credentials: 'include',
          headers
        });
        const data = await res.json();
        if (data.ok && (data.identity || data.session)) {
          const s = data.identity || data.session;
          setSession(s);
          localStorage.setItem('wpb_session_data', JSON.stringify(s));
          window.dispatchEvent(new CustomEvent('session-updated', { detail: s }));
        }
      } catch (err) {
        console.error('Session refresh notice:', err);
      } finally {
        setLoading(false);
      }
    }

    refreshSession();
  }, []);

  const isAuthenticated = session?.authenticated && !session?.is_guest;
  const isGuest = session?.is_guest || !session?.authenticated;
  const plan = session?.plan || planQuery || 'starter';
  const planName = session?.plan_name || (plan === 'free' ? 'Starter Plan' : plan.toUpperCase());
  const credits = session?.credits ?? 30;
  const maxRes = session?.max_resolution ?? (plan === 'free' ? 720 : 1080);

  return (
    <div className="py-12 sm:py-20 max-w-3xl mx-auto px-4 sm:px-6">
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-3xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 grid place-items-center mx-auto mb-5 shadow-lg shadow-emerald-500/10">
          <CheckCircle2 className="w-9 h-9" />
        </div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-bold mb-3 border border-emerald-500/25">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Payment Verified & Plan Activated</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-[var(--text)] tracking-tight">
          Congratulations! You're Upgraded
        </h1>
        <p className="text-xs sm:text-sm text-[var(--text-muted)] mt-2 max-w-lg mx-auto">
          Your payment was processed successfully. Your rendering queue priority, high-resolution exports, and monthly credits have been unlocked!
        </p>
      </div>

      {/* Plan Entitlements Card */}
      <div className="rounded-3xl bg-[var(--surface)] border border-[var(--border)] p-6 sm:p-8 mb-6 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-[var(--border)]">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">Active Subscription</span>
            <div className="flex items-center gap-2 mt-1">
              <Crown className="w-5 h-5 text-amber-500" />
              <h2 className="text-xl sm:text-2xl font-black text-[var(--text)]">{planName}</h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-500/15 text-amber-500 border border-amber-500/30">
                ACTIVE
              </span>
            </div>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">Available Balance</span>
            <div className="text-2xl sm:text-3xl font-black text-amber-500 mt-1">
              {credits} credits
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 my-6">
          <div className="p-3.5 rounded-2xl bg-[var(--bg-alt)] border border-[var(--border)] text-center">
            <span className="text-[11px] text-[var(--text-muted)] block">Max Resolution</span>
            <strong className="text-sm sm:text-base font-extrabold text-[var(--text)] mt-0.5 block">
              {maxRes}p {maxRes >= 1080 ? 'Full HD' : 'HD'}
            </strong>
          </div>
          <div className="p-3.5 rounded-2xl bg-[var(--bg-alt)] border border-[var(--border)] text-center">
            <span className="text-[11px] text-[var(--text-muted)] block">Render Queue</span>
            <strong className="text-sm sm:text-base font-extrabold text-emerald-400 mt-0.5 block">
              Priority Slot
            </strong>
          </div>
          <div className="p-3.5 rounded-2xl bg-[var(--bg-alt)] border border-[var(--border)] text-center">
            <span className="text-[11px] text-[var(--text-muted)] block">License</span>
            <strong className="text-sm sm:text-base font-extrabold text-[var(--text)] mt-0.5 block">
              Full Commercial
            </strong>
          </div>
        </div>

        {/* Guest Warning / Account Link Prompt */}
        {isGuest && (
          <div className="p-4 sm:p-5 rounded-2xl bg-amber-500/10 border border-amber-500/35 mb-4 text-left">
            <div className="flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
              <div>
                <h3 className="text-xs sm:text-sm font-black text-[var(--text)]">
                  You purchased as a Guest — Link your plan now!
                </h3>
                <p className="text-xs text-[var(--text-muted)] mt-1 leading-relaxed">
                  Your <strong className="text-[var(--text)]">{credits} credits</strong> and upgraded resolution are tied to your current browser cookies. If you clear browsing data or use a different device, you could lose access.
                </p>
                <div className="mt-3.5 flex flex-wrap items-center gap-3">
                  <Link
                    to="/signup?return=/ai-video-editor"
                    className="py-2 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-blue-500/20"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    <span>Create Free Account (+5 Bonus Credits)</span>
                  </Link>
                  <Link
                    to="/login?return=/ai-video-editor"
                    className="text-xs font-semibold text-blue-400 hover:underline"
                  >
                    Already have an account? Sign in to merge
                  </Link>
                </div>
              </div>
            </div>
          </div>
        )}

        {isAuthenticated && (
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center gap-3 text-xs text-emerald-400 font-semibold mb-4">
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              Linked securely to your account: <strong className="text-[var(--text)] font-bold">{session.email}</strong>
            </span>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          <Link
            to="/ai-video-editor"
            className="py-3 px-4 rounded-xl bg-[var(--primary)] hover:opacity-90 text-[var(--on-primary)] text-xs font-bold flex items-center justify-center gap-2 shadow-md transition-all text-center"
          >
            <Wand2 className="w-4 h-4" />
            <span>Start Editing with {maxRes}p HD</span>
          </Link>
          <Link
            to="/pricing"
            className="py-3 px-4 rounded-xl border border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--bg-alt)] text-[var(--text)] text-xs font-bold flex items-center justify-center gap-2 transition-colors text-center"
          >
            <span>View All 7 Plans & Invoices</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
