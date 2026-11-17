import React, { useState } from 'react';
import { User, LogIn, LogOut, Zap, Crown, Sparkles, Loader2 } from 'lucide-react';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

export default function UserAccountBar({ session, onOpenPricing, onSessionUpdate }) {
  const [loggingIn, setLoggingIn] = useState(false);

  const isAuthenticated = session?.authenticated && !session?.is_guest;
  const plan = session?.plan || 'free';
  const planName = session?.plan_name || (plan === 'free' ? 'Free Plan' : plan.toUpperCase());
  const credits = session?.credits ?? 2;
  const isPaid = plan !== 'free';

  function handleGoogleLogin() {
    // If Google Client ID is configured, trigger standard Google OAuth flow or prompt
    const clientId = window.__GOOGLE_CLIENT_ID__ || 'YOUR_GOOGLE_CLIENT_ID';
    if (window.google?.accounts?.id) {
      window.google.accounts.id.prompt();
    } else {
      // Mock / preview sign-in for seamless verification
      const email = prompt('Enter your Google email to sign in:');
      if (!email) return;
      setLoggingIn(true);
      fetch(`${BACKEND_BASE}/api/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          credential: btoa(JSON.stringify({ email, name: email.split('@')[0], sub: `g_${Date.now()}` }))
        })
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.ok && onSessionUpdate) {
            onSessionUpdate(data.session);
          }
        })
        .catch(console.error)
        .finally(() => setLoggingIn(false));
    }
  }

  async function handleLogout() {
    try {
      await fetch(`${BACKEND_BASE}/api/auth/logout`, { method: 'POST' });
      if (onSessionUpdate) {
        onSessionUpdate({
          authenticated: false,
          is_guest: true,
          plan: 'free',
          plan_name: 'Free',
          credits: 2,
          max_resolution: 720
        });
      }
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 bg-[var(--surface,#12141a)] border border-[var(--border,#262934)] rounded-2xl mb-6 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-zinc-800 border border-zinc-700/60 flex items-center justify-center text-zinc-300 overflow-hidden shrink-0">
          {session?.avatar ? (
            <img src={session.avatar} alt="Avatar" className="w-full h-full object-cover" />
          ) : (
            <User className="w-4 h-4 text-zinc-400" />
          )}
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-white">
              {isAuthenticated ? session.name || session.email : 'Guest Session'}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider flex items-center gap-1 ${
              isPaid
                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
            }`}>
              {isPaid && <Crown className="w-2.5 h-2.5 text-amber-400" />}
              {planName}
            </span>
          </div>
          <div className="text-[11px] text-zinc-400 flex items-center gap-1.5 mt-0.5">
            <span>Available credits:</span>
            <strong className="text-amber-400 font-bold">{credits}</strong>
            <span className="text-zinc-600">•</span>
            <span>Max export: <strong className="text-zinc-300">{session?.max_resolution || 720}p</strong></span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onOpenPricing}
          className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-blue-500/20 transition-all"
        >
          <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
          <span>{isPaid ? 'Add Credits' : 'Upgrade Plan'}</span>
        </button>

        {isAuthenticated ? (
          <button
            type="button"
            onClick={handleLogout}
            title="Log out"
            className="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 border border-zinc-700/60 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleGoogleLogin}
            disabled={loggingIn}
            className="px-3 py-1.5 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold flex items-center gap-1.5 border border-zinc-700/60 transition-colors"
          >
            {loggingIn ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <LogIn className="w-3.5 h-3.5" />}
            <span>Sign in</span>
          </button>
        )}
      </div>
    </div>
  );
}
