import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, AlertTriangle, Lock, CheckCircle2, Terminal, ArrowLeft, ShieldCheck, Download } from 'lucide-react';

export default function SecurityPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12 text-[var(--text)]">
      
      {/* Back button */}
      <div className="mb-6">
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text)] transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Home</span>
        </Link>
      </div>

      {/* Main Hero Card */}
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl p-6 sm:p-10 shadow-[var(--shadow-2)] relative overflow-hidden mb-10">
        
        {/* Glow Orb */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-red-600/10 blur-[90px] rounded-full pointer-events-none" />

        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[var(--negative-bg)] border border-red-500/20 text-[var(--negative)] text-xs font-bold w-fit mb-6">
          <ShieldAlert className="w-4 h-4" />
          <span>Official Security Bulletin & Advisory</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-black text-[var(--text)] tracking-tight mb-4 leading-tight">
          Understanding Self-XSS & Developer Console Security
        </h1>

        <p className="text-[var(--text-muted)] text-sm sm:text-base leading-relaxed mb-6">
          If you opened your browser's Developer Tools (Console) and saw a large red <strong className="text-[var(--negative)] font-bold">"Stop!"</strong> message, 
          do not panic. That notice is an automated defensive warning designed to protect your accounts and sensitive credentials from cyber scams known as <strong className="text-[var(--text)]">Self-XSS</strong> (Self Cross-Site Scripting).
        </p>

        {/* Console Mock Box */}
        <div className="bg-[var(--bg)] border border-[var(--border)] rounded-2xl p-4 sm:p-5 font-mono text-xs mb-8 overflow-x-auto shadow-inner">
          <div className="flex items-center gap-1.5 text-[var(--text-muted)] mb-3 pb-2 border-b border-[var(--border)]">
            <Terminal className="w-4 h-4" />
            <span>Developer Console Output (Preview)</span>
          </div>
          <div className="text-red-500 font-extrabold text-2xl mb-2">Stop!</div>
          <div className="text-[var(--text)] leading-relaxed mb-2">
            This is a browser feature intended for developers. If someone told you to copy and paste something here to enable an OVD feature or &quot;hack&quot; someone&apos;s account, it is a scam and will give them unauthorized access to your account.
          </div>
          <div className="text-sky-400 font-bold">See https://ovd.winplaybox.in/security for more information.</div>
        </div>

        {/* Section 1: What is Self-XSS? */}
        <div className="space-y-6 text-sm text-[var(--text)] leading-relaxed">
          <h2 className="text-xl font-bold text-[var(--text)] flex items-center gap-2 pt-2 border-t border-[var(--border)]">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <span>What is Self-XSS and How Does the Scam Work?</span>
          </h2>
          <p>
            The browser Developer Console allows programmers to test code directly within the web page. 
            Because code executed in the console runs with your full browser privileges, attackers frequently exploit users who do not understand technical scripting:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[var(--bg-alt)] border border-[var(--border)] p-4 rounded-xl">
              <div className="text-[var(--negative)] font-bold mb-1">1. The Bait</div>
              <div className="text-xs text-[var(--text-muted)]">
                A scammer or video promises a &quot;secret script to unlock private Instagram stories, private Facebook posts, or get unlimited game credits.&quot;
              </div>
            </div>
            <div className="bg-[var(--bg-alt)] border border-[var(--border)] p-4 rounded-xl">
              <div className="text-amber-400 font-bold mb-1">2. The Trap</div>
              <div className="text-xs text-[var(--text-muted)]">
                They ask you to press <code className="bg-[var(--bg-alt)] px-1 py-0.5 rounded text-[var(--text)]">F12</code> or <code className="bg-[var(--bg-alt)] px-1 py-0.5 rounded text-[var(--text)]">Ctrl+Shift+I</code>, navigate to the &quot;Console&quot; tab, and paste a block of obfuscated JavaScript.
              </div>
            </div>
            <div className="bg-[var(--bg-alt)] border border-[var(--border)] p-4 rounded-xl">
              <div className="text-purple-400 font-bold mb-1">3. The Theft</div>
              <div className="text-xs text-[var(--text-muted)]">
                The moment you press Enter, their script steals your active login cookies, session tokens, and passwords, sending them straight to the attacker&apos;s server.
              </div>
            </div>
          </div>

          <h2 className="text-xl font-bold text-[var(--text)] flex items-center gap-2 pt-6 border-t border-[var(--border)]">
            <ShieldCheck className="w-5 h-5 text-[var(--positive)]" />
            <span>How OVD Downloader Protects You</span>
          </h2>
          <p>
            OVD Downloader adheres to strict cybersecurity best practices to ensure your browsing experience remains private, unmonitored, and safe:
          </p>

          <ul className="space-y-3">
            <li className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-[var(--positive)] shrink-0 mt-0.5" />
              <div>
                <strong className="text-[var(--text)]">Zero-Cookie & Zero-Login Policy:</strong> We never ask for your social media passwords, 2FA codes, or account access. You can download all public media completely anonymously.
              </div>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-[var(--positive)] shrink-0 mt-0.5" />
              <div>
                <strong className="text-[var(--text)]">Origin-Guarded API Endpoints:</strong> Our extraction endpoints only communicate with our official verified web domains (<code className="bg-[var(--bg-alt)] px-1 py-0.5 rounded text-sky-300">ovd.winplaybox.in</code>) and authorized browser extension IDs.
              </div>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-[var(--positive)] shrink-0 mt-0.5" />
              <div>
                <strong className="text-[var(--text)]">No Arbitrary Console Scripts:</strong> We will <em className="text-amber-300">NEVER</em> ask you to paste any code into your developer console to use OVD Downloader.
              </div>
            </li>
          </ul>

          <h2 className="text-xl font-bold text-[var(--text)] flex items-center gap-2 pt-6 border-t border-[var(--border)]">
            <Lock className="w-5 h-5 text-sky-400" />
            <span>How to Download Private or Restricted Media Safely</span>
          </h2>
          <p>
            When a video, reel, or story is private (such as private Facebook groups or follower-only Instagram posts), public web downloaders cannot access them because public cloud servers lack your login session.
          </p>
          <p>
            The safe, legitimate solution is the <strong className="text-[var(--text)]">Official OVD Browser Extension</strong>. Because the extension operates on your local browser machine, it allows you to download videos directly from your active session without sharing your password with any third-party server.
          </p>

          <div className="pt-6 flex flex-col sm:flex-row items-center gap-4">
            <Link
              to="/"
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-gradient-to-r from-red-600 via-rose-600 to-pink-600 hover:from-red-500 hover:to-pink-500 text-[var(--text)] font-bold text-sm flex items-center justify-center gap-2 shadow-lg shadow-red-600/25 transition"
            >
              <span>Back to OVD Downloader</span>
            </Link>
            <a
              href="https://ovd.winplaybox.in"
              className="w-full sm:w-auto px-6 py-3 rounded-xl bg-[var(--bg-alt)] hover:bg-slate-700 text-[var(--text)] font-bold text-sm flex items-center justify-center gap-2 transition"
            >
              <Download className="w-4 h-4 text-sky-400" />
              <span>Get Official Browser Extension</span>
            </a>
          </div>

        </div>

      </div>

    </div>
  );
}

