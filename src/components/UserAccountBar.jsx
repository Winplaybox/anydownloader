import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, LogIn, LogOut, Zap, Crown, Sparkles, ArrowRight, Mail } from 'lucide-react';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

function GoogleGIcon({ className = 'w-3.5 h-3.5' }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
    </svg>
  );
}

export default function UserAccountBar({ session, onSessionUpdate }) {
  const navigate = useNavigate();
  const isAuthenticated = session?.authenticated && !session?.is_guest;
  const plan = session?.plan || 'free';
  const planName = session?.plan_name || (plan === 'free' ? 'Free Trial (480p SD)' : plan.toUpperCase());
  const credits = session?.credits ?? 2;
  const maxRes = session?.max_resolution ?? 480;
  const isPaid = plan !== 'free';

  async function handleLogout() {
    try {
      await fetch(`${BACKEND_BASE}/api/auth/logout`, { method: 'POST', credentials: 'include' });
    } catch (e) {
      console.error(e);
    }
    localStorage.removeItem('wpb_token');
    const freshGuest = {
      authenticated: false,
      is_guest: true,
      plan: 'free',
      plan_name: 'Free Trial (480p SD)',
      credits: 2,
      max_resolution: 480
    };
    localStorage.setItem('wpb_session_data', JSON.stringify(freshGuest));
    if (onSessionUpdate) onSessionUpdate(freshGuest);
    window.dispatchEvent(new CustomEvent('session-updated', { detail: freshGuest }));
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-[var(--surface)] border border-[var(--border)] rounded-2xl mb-6 shadow-sm text-[var(--text)]">
      <div className="flex items-center gap-3">
        {/* Avatar circle */}
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 p-[2px] shadow-sm shrink-0">
          <div className="w-full h-full bg-[var(--bg)] rounded-[10px] flex items-center justify-center overflow-hidden">
            {session?.avatar ? (
              <img src={session.avatar} alt="Avatar" className="w-full h-full object-cover" />
            ) : isAuthenticated ? (
              <span className="text-[var(--text)] font-black text-sm uppercase">{(session?.name || session?.email || 'U')[0]}</span>
            ) : (
              <span className="text-base" role="img" aria-label="Guest avatar">🤖</span>
            )}
          </div>
        </div>

        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs sm:text-sm font-bold text-[var(--text)]">
              {isAuthenticated ? (session.name || session.email) : 'Guest Creator'}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider flex items-center gap-1 ${
              isPaid
                ? 'bg-amber-500/15 text-amber-500 border border-amber-500/30'
                : 'bg-[var(--bg-alt)] text-[var(--text-muted)] border border-[var(--border)]'
            }`}>
              {isPaid ? <Crown className="w-2.5 h-2.5 text-amber-500" /> : <Sparkles className="w-2.5 h-2.5 text-blue-500" />}
              {planName}
            </span>
          </div>
          <div className="text-[11px] text-[var(--text-muted)] flex flex-wrap items-center gap-1.5 mt-0.5">
            <span>Credits:</span>
            <strong className="text-amber-500 font-bold">{credits}</strong>
            <span className="opacity-40">•</span>
            <span>Max export: <strong className="text-[var(--text)] font-bold">{maxRes}p {maxRes <= 480 ? 'SD' : 'HD'}</strong></span>
            {maxRes <= 480 && (
              <span className="text-[10px] text-blue-500 font-semibold">(Below 720p on Free)</span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Link
          to="/pricing"
          className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-amber-500 via-orange-500 to-amber-600 hover:opacity-95 text-black text-xs font-black flex items-center gap-1.5 shadow-md shadow-orange-500/10 transition-all uppercase tracking-wide cursor-pointer"
        >
          <Crown className="w-3.5 h-3.5 text-black" />
          <span>{isPaid ? 'Add Credits' : '7-Tier Plans'}</span>
        </Link>

        {isAuthenticated ? (
          <button
            type="button"
            onClick={handleLogout}
            title="Log out"
            className="p-2 rounded-xl text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--bg-alt)] border border-[var(--border)] transition-colors cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        ) : (
          <div className="flex items-center gap-1.5">
            <Link
              to="/login?return=/ai-video-editor"
              className="px-3 py-2 rounded-xl bg-[var(--surface)] hover:bg-[var(--bg-alt)] text-[var(--text)] text-xs font-bold flex items-center gap-1.5 border border-[var(--border)] shadow-sm transition-colors cursor-pointer"
            >
              <GoogleGIcon />
              <span>Google</span>
            </Link>
            <Link
              to="/login?return=/ai-video-editor"
              className="px-3 py-2 rounded-xl bg-[var(--bg-alt)] hover:bg-[var(--border)] text-[var(--text)] text-xs font-semibold flex items-center gap-1.5 border border-[var(--border)] transition-colors cursor-pointer"
            >
              <Mail className="w-3.5 h-3.5 text-[var(--text-muted)]" />
              <span>Email</span>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
