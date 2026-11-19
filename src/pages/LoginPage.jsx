import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Mail, Lock, Loader2, AlertCircle, ArrowRight, Eye, EyeOff, CheckCircle2 } from 'lucide-react';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://api.winplaybox.in';

const GOOGLE_CLIENT_ID = typeof window !== 'undefined'
  ? (window.__GOOGLE_CLIENT_ID__ || (import.meta.env && import.meta.env.VITE_GOOGLE_CLIENT_ID) || '259545227984-tq7m462dc4vkqfv1g1ch66mou7uhigki.apps.googleusercontent.com')
  : '259545227984-tq7m462dc4vkqfv1g1ch66mou7uhigki.apps.googleusercontent.com';

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

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [gsiLoaded, setGsiLoaded] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const googleBtnRef = useRef(null);

  // Read return path if passed
  const returnTo = new URLSearchParams(location.search).get('return') || '/ai-video-editor';

  useEffect(() => {
    document.title = 'Sign In — OVD & WinPlayBox';

    // If user is already logged in, redirect
    try {
      const cached = localStorage.getItem('wpb_session_data');
      if (cached) {
        const s = JSON.parse(cached);
        if (s.authenticated && !s.is_guest) {
          navigate(returnTo, { replace: true });
        }
      }
    } catch {}
  }, [navigate, returnTo]);

  // Google Identity Services (GSI) init & personalized button rendering
  useEffect(() => {
    let mounted = true;

    function renderGsi() {
      if (typeof window === 'undefined' || !window.google?.accounts?.id || !googleBtnRef.current) return;
      try {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true,
          context: 'signin'
        });

        if (mounted && googleBtnRef.current) {
          googleBtnRef.current.innerHTML = '';
          window.google.accounts.id.renderButton(googleBtnRef.current, {
            theme: 'outline',
            size: 'large',
            type: 'standard',
            shape: 'rectangular',
            text: 'signin_with',
            logo_alignment: 'left',
            width: 320
          });
          setGsiLoaded(true);
        }

        // Show One Tap if eligible
        try {
          window.google.accounts.id.prompt();
        } catch (_) {}
      } catch (e) {
        console.warn('GSI render notice:', e);
      }
    }

    if (window.google?.accounts?.id) {
      renderGsi();
    } else {
      const interval = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(interval);
          renderGsi();
        }
      }, 200);
      const timeout = setTimeout(() => clearInterval(interval), 5000);
      return () => {
        clearInterval(interval);
        clearTimeout(timeout);
        mounted = false;
      };
    }

    return () => { mounted = false; };
  }, []);

  async function handleGoogleCredentialResponse(response) {
    if (!response?.credential) return;
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
        setSuccessMsg('Signed in with Google successfully!');
        setTimeout(() => navigate(returnTo), 600);
      } else {
        setError(data.error || 'Google authentication failed.');
      }
    } catch (err) {
      setError(err.message || 'Google authentication unreachable.');
    } finally {
      setGoogleLoading(false);
    }
  }

  function handleGoogleFallbackClick() {
    if (typeof window !== 'undefined' && window.google?.accounts?.id) {
      try {
        window.google.accounts.id.prompt();
        return;
      } catch (_) {}
    }
    setError('Google Sign-In is unavailable or blocked by your browser/adblocker. Please sign in using your email and password below.');
  }

  async function handleEmailLogin(e) {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${BACKEND_BASE}/api/auth/login`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();

      if (res.ok && data.ok && data.user) {
        if (data.token) localStorage.setItem('wpb_token', data.token);
        localStorage.setItem('wpb_session_data', JSON.stringify(data.user));
        window.dispatchEvent(new CustomEvent('session-updated', { detail: data.user }));
        setSuccessMsg('Logged in successfully!');
        setTimeout(() => navigate(returnTo), 500);
      } else {
        setError(data.error || 'Invalid email or password.');
      }
    } catch (err) {
      setError(err.message || 'Unable to connect to authentication server.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6">
      <div className="w-full max-w-md bg-[var(--surface)] border border-[var(--border)] rounded-3xl p-6 sm:p-9 shadow-2xl">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-4 select-none">
            <span className="w-10 h-10 rounded-2xl bg-[var(--primary)] text-[var(--on-primary)] grid place-items-center font-extrabold text-xl shadow-md">
              o
            </span>
            <span className="font-extrabold text-2xl tracking-tight text-[var(--text)]">ovd</span>
          </Link>
          <h1 className="text-2xl font-black text-[var(--text)] tracking-tight">Welcome Back</h1>
          <p className="text-xs text-[var(--text-muted)] mt-1.5">
            Log in to manage credits, 7-tier plans and HD/4K video exports
          </p>
        </div>

        {/* Error / Success Notifications */}
        {error && (
          <div className="mb-5 p-3 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {successMsg && (
          <div className="mb-5 p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* System 1: Single Unified Google Auth Button */}
        <div className="mb-6">
          <div className="flex justify-center min-h-[44px]">
            <div ref={googleBtnRef} className="flex justify-center w-full" />
          </div>
          {!gsiLoaded && (
            <button
              type="button"
              onClick={handleGoogleFallbackClick}
              disabled={googleLoading}
              className="w-full py-2.5 px-4 rounded-xl bg-[var(--surface)] hover:bg-[var(--bg-alt)] text-[var(--text)] text-xs font-bold flex items-center justify-center gap-2.5 border border-[var(--border)] shadow-sm transition-all cursor-pointer"
            >
              {googleLoading ? <Loader2 className="w-4 h-4 animate-spin text-[var(--text)]" /> : <GoogleGIcon className="w-4 h-4" />}
              <span>Sign in with Google</span>
            </button>
          )}
        </div>

        {/* Divider */}
        <div className="relative flex items-center justify-center mb-6">
          <div className="border-t border-[var(--border)] w-full" />
          <span className="bg-[var(--surface)] px-3 text-[10px] uppercase font-bold text-[var(--text-muted)] shrink-0">
            or sign in with email
          </span>
          <div className="border-t border-[var(--border)] w-full" />
        </div>

        {/* System 2: Valid Email & Password Form */}
        <form onSubmit={handleEmailLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-[var(--text)] mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-[var(--text-muted)] absolute left-3.5 top-3" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full rounded-xl border border-[var(--border)] bg-[var(--bg)] pl-10 pr-3.5 py-2.5 text-xs text-[var(--text)] placeholder:text-[var(--text-muted)] outline-none focus:border-[var(--primary)] transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text)] mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-[var(--text-muted)] absolute left-3.5 top-3" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Your password"
                className="w-full rounded-xl border border-[var(--border)] bg-[var(--bg)] pl-10 pr-10 py-2.5 text-xs text-[var(--text)] placeholder:text-[var(--text-muted)] outline-none focus:border-[var(--primary)] transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-3 text-[var(--text-muted)] hover:text-[var(--text)]"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-[var(--primary)] hover:opacity-90 text-[var(--on-primary)] text-xs font-bold flex items-center justify-center gap-2 shadow-md transition-all cursor-pointer mt-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
            <span>Sign In</span>
          </button>
        </form>

        {/* Switch to Sign Up */}
        <div className="mt-6 pt-5 border-t border-[var(--border)] text-center">
          <p className="text-xs text-[var(--text-muted)]">
            Don't have an account?{' '}
            <Link to={`/signup?return=${encodeURIComponent(returnTo)}`} className="text-blue-400 hover:underline font-bold">
              Sign up for +5 Free Credits
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
