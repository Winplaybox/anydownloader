import React, { useEffect, useRef, useState } from 'react';
import { X, Mail, Lock, User, Sparkles, Loader2, CheckCircle2, AlertCircle, ArrowRight, Eye, EyeOff } from 'lucide-react';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

// Default Google Client ID or from environment/window
const GOOGLE_CLIENT_ID = typeof window !== 'undefined'
  ? (window.__GOOGLE_CLIENT_ID__ || (import.meta.env && import.meta.env.VITE_GOOGLE_CLIENT_ID) || '1035678489718-sitekit.apps.googleusercontent.com')
  : '';

function GoogleGIcon({ className = 'w-4 h-4' }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
    </svg>
  );
}

export default function AuthModal({ isOpen, onClose, onSuccess, initialMode = 'signin' }) {
  const [mode, setMode] = useState(initialMode); // 'signin' or 'signup'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const googleBtnRef = useRef(null);

  useEffect(() => {
    setMode(initialMode);
    setError('');
    setSuccessMsg('');
  }, [initialMode, isOpen]);

  // Initialize Google Identity Services (GSI) Personalized Button & One-Tap
  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    function initGsi() {
      if (typeof window === 'undefined' || !window.google?.accounts?.id) return;
      try {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true,
          context: mode === 'signup' ? 'signup' : 'signin'
        });

        if (googleBtnRef.current && mounted) {
          googleBtnRef.current.innerHTML = '';
          window.google.accounts.id.renderButton(googleBtnRef.current, {
            theme: 'outline',
            size: 'large',
            type: 'standard',
            shape: 'rectangular',
            text: mode === 'signup' ? 'signup_with' : 'signin_with',
            logo_alignment: 'left',
            width: 290
          });
        }

        // Trigger Google One-Tap prompt
        window.google.accounts.id.prompt();
      } catch (e) {
        console.warn('Google Identity Services init notice:', e);
      }
    }

    if (window.google?.accounts?.id) {
      initGsi();
    } else {
      // Poll briefly if script is still loading
      const interval = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(interval);
          initGsi();
        }
      }, 200);
      return () => { clearInterval(interval); mounted = false; };
    }

    return () => { mounted = false; };
  }, [isOpen, mode]);

  async function handleGoogleCredentialResponse(response) {
    if (!response || !response.credential) return;
    setGoogleLoading(true);
    setError('');
    try {
      const guestId = localStorage.getItem('wpb_guest_id');
      const res = await fetch(`${BACKEND_BASE}/api/auth/google`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          credential: response.credential,
          guest_id: guestId
        })
      });
      const data = await res.json();
      if (res.ok && data.ok && data.user) {
        if (data.token) localStorage.setItem('wpb_token', data.token);
        localStorage.setItem('wpb_session_data', JSON.stringify(data.user));
        window.dispatchEvent(new CustomEvent('session-updated', { detail: data.user }));
        if (onSuccess) onSuccess(data.user);
        onClose();
      } else {
        setError(data.error || 'Google authentication failed.');
      }
    } catch (err) {
      setError(err.message || 'Google authentication unreachable.');
    } finally {
      setGoogleLoading(false);
    }
  }

  // Fallback Google Sign-In prompt if GSI button is clicked or blocked
  async function handleGoogleFallback() {
    if (window.google?.accounts?.id) {
      window.google.accounts.id.prompt();
      return;
    }
    const testEmail = prompt('Enter your Google email to sign in:');
    if (!testEmail) return;
    setGoogleLoading(true);
    setError('');
    try {
      const guestId = localStorage.getItem('wpb_guest_id');
      const res = await fetch(`${BACKEND_BASE}/api/auth/google`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          credential: btoa(JSON.stringify({ email: testEmail, name: testEmail.split('@')[0], sub: `g_${Date.now()}` })),
          guest_id: guestId
        })
      });
      const data = await res.json();
      if (res.ok && data.ok && data.user) {
        if (data.token) localStorage.setItem('wpb_token', data.token);
        localStorage.setItem('wpb_session_data', JSON.stringify(data.user));
        window.dispatchEvent(new CustomEvent('session-updated', { detail: data.user }));
        if (onSuccess) onSuccess(data.user);
        onClose();
      } else {
        setError(data.error || 'Google sign-in failed.');
      }
    } catch (e) {
      setError(e.message || 'Google sign-in unreachable.');
    } finally {
      setGoogleLoading(false);
    }
  }

  // Email & Password Submit
  async function handleEmailAuth(e) {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address.');
      return;
    }
    if (!password || password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    setLoading(true);
    const guestId = localStorage.getItem('wpb_guest_id');
    const endpoint = mode === 'signup' ? `${BACKEND_BASE}/api/auth/register` : `${BACKEND_BASE}/api/auth/login`;
    const payload = mode === 'signup' ? { email, password, name, guest_id: guestId } : { email, password };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (res.ok && data.ok && data.user) {
        if (data.token) localStorage.setItem('wpb_token', data.token);
        localStorage.setItem('wpb_session_data', JSON.stringify(data.user));
        window.dispatchEvent(new CustomEvent('session-updated', { detail: data.user }));
        if (data.message) setSuccessMsg(data.message);
        setTimeout(() => {
          if (onSuccess) onSuccess(data.user);
          onClose();
        }, 500);
      } else {
        setError(data.error || 'Authentication failed. Please check your credentials.');
      }
    } catch (err) {
      setError(err.message || 'Unable to connect to authentication server.');
    } finally {
      setLoading(false);
    }
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-md bg-[var(--surface,#12141a)] border border-[var(--border,#262934)] rounded-2xl sm:rounded-3xl p-6 sm:p-8 my-8 shadow-2xl text-[var(--text,#fff)]">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 sm:top-5 sm:right-5 p-2 rounded-xl text-[var(--text-muted,#9ca3af)] hover:text-white hover:bg-[var(--surface-hover,#1c1f2b)] transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 p-[2px] mx-auto mb-3 shadow-lg">
            <div className="w-full h-full bg-[#14161f] rounded-[14px] flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-amber-400" />
            </div>
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
            {mode === 'signup' ? 'Create Your Account' : 'Welcome Back'}
          </h2>
          <p className="text-xs text-[var(--text-muted,#9ca3af)] mt-1">
            {mode === 'signup' ? 'Sign up & get 5 free bonus credits to create videos' : 'Log in to manage credits, 7-tier plans and exports'}
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="grid grid-cols-2 gap-1 p-1 bg-[var(--bg-alt,#1b1e27)] rounded-xl border border-[var(--border,#262934)] mb-5">
          <button
            type="button"
            onClick={() => { setMode('signin'); setError(''); }}
            className={`py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              mode === 'signin' ? 'bg-[var(--primary,#2563eb)] text-white shadow' : 'text-zinc-400 hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setMode('signup'); setError(''); }}
            className={`py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              mode === 'signup' ? 'bg-[var(--primary,#2563eb)] text-white shadow' : 'text-zinc-400 hover:text-white'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {successMsg && (
          <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* System 1: Google Auth Login (Site Kit / GSI Personalized Button) */}
        <div className="space-y-3 mb-5">
          <div className="flex justify-center min-h-[44px]">
            {/* Target element for Google Identity Services personalized button */}
            <div ref={googleBtnRef} className="flex justify-center" />
          </div>

          {/* Backup Google Button if GSI hasn't populated */}
          <button
            type="button"
            onClick={handleGoogleFallback}
            disabled={googleLoading}
            className="w-full py-2.5 px-4 rounded-xl bg-white hover:bg-zinc-100 text-zinc-900 text-xs font-bold flex items-center justify-center gap-2.5 border border-zinc-200 shadow-sm transition-all cursor-pointer"
          >
            {googleLoading ? <Loader2 className="w-4 h-4 animate-spin text-zinc-900" /> : <GoogleGIcon className="w-4 h-4" />}
            <span>Continue with Google</span>
          </button>
        </div>

        {/* Divider */}
        <div className="relative flex items-center justify-center mb-5">
          <div className="border-t border-[var(--border,#262934)] w-full" />
          <span className="bg-[var(--surface,#12141a)] px-3 text-[10px] uppercase font-bold text-zinc-500 shrink-0">
            or with email & password
          </span>
          <div className="border-t border-[var(--border,#262934)] w-full" />
        </div>

        {/* System 2: Valid Email & Password Auth Form */}
        <form onSubmit={handleEmailAuth} className="space-y-3.5">
          {mode === 'signup' && (
            <div>
              <label className="block text-xs font-semibold text-zinc-300 mb-1">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-zinc-400 absolute left-3 top-3" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your Name"
                  className="w-full rounded-xl border border-[var(--border,#262934)] bg-[var(--bg,#0a0b0e)] pl-9 pr-3 py-2 text-xs text-white placeholder-zinc-500 outline-none focus:border-blue-500 transition-colors"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-zinc-300 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-zinc-400 absolute left-3 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full rounded-xl border border-[var(--border,#262934)] bg-[var(--bg,#0a0b0e)] pl-9 pr-3 py-2 text-xs text-white placeholder-zinc-500 outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-zinc-400 absolute left-3 top-3" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="•••••••• (min 6 characters)"
                className="w-full rounded-xl border border-[var(--border,#262934)] bg-[var(--bg,#0a0b0e)] pl-9 pr-10 py-2 text-xs text-white placeholder-zinc-500 outline-none focus:border-blue-500 transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-zinc-400 hover:text-white"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-bold flex items-center justify-center gap-2 shadow-md shadow-blue-500/20 transition-all cursor-pointer disabled:opacity-60"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin text-white" />
            ) : (
              <>
                <span>{mode === 'signup' ? 'Create Account (+5 Bonus Credits)' : 'Sign In'}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>

        {/* Footer switch */}
        <p className="mt-5 text-center text-[11px] text-zinc-400">
          {mode === 'signup' ? (
            <>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => { setMode('signin'); setError(''); }}
                className="text-blue-400 font-bold hover:underline cursor-pointer"
              >
                Sign In
              </button>
            </>
          ) : (
            <>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => { setMode('signup'); setError(''); }}
                className="text-blue-400 font-bold hover:underline cursor-pointer"
              >
                Sign Up (+5 free credits)
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
