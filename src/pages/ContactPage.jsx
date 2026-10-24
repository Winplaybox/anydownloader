import React, { useState } from 'react';
import { Mail, MessageSquare, Send, CheckCircle2, Clock, Shield, Loader2, AlertCircle } from 'lucide-react';

const BACKEND_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://anydownloader-backend-vvbj.onrender.com';

export default function ContactPage() {
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' });

  async function handleSubmit(e) {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const resp = await fetch(`${BACKEND_BASE}/api/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      });

      if (resp.ok) {
        const data = await resp.json();
        if (data.ok) {
          setSubmitted(true);
        } else {
          setSubmitError(data.error || 'Failed to submit inquiry.');
        }
      } else {
        const data = await resp.json().catch(() => ({}));
        setSubmitError(data.error || 'Server error. Please reach out to support@winplaybox.in.');
      }
    } catch (err) {
      setSubmitError('Connection interrupted. Please email us at support@winplaybox.in.');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="py-12 max-w-4xl mx-auto px-4 sm:px-6">
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 sm:p-10 shadow-xs">

        <div className="flex items-center gap-2 mb-3">
          <span className="px-2.5 py-0.5 rounded-md bg-[var(--positive-bg)] text-[var(--positive)] border border-[var(--positive)]/30 text-xs font-semibold uppercase tracking-wider">
            Help & Inquiries
          </span>
          <span className="text-xs text-[var(--text-muted)]">Official Helpdesk</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-black text-[var(--text)] tracking-tight mb-3">
          Contact & Support
        </h1>
        <p className="text-xs sm:text-sm text-[var(--text-muted)] mb-8 leading-relaxed max-w-2xl">
          Have technical questions, bug reports, feature requests, or partnership inquiries regarding OVD? Reach out directly through the form below or email us.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">

          {/* Contact Details Side */}
          <div className="md:col-span-5 space-y-3.5">
            <div className="p-4 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)]">
              <Mail className="w-5 h-5 text-[var(--accent)] mb-2" />
              <h3 className="font-bold text-[var(--text)] text-xs mb-0.5">Email Support</h3>
              <p className="text-xs text-[var(--text-muted)] font-mono">support@winplaybox.in</p>
            </div>

            <div className="p-4 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)]">
              <Clock className="w-5 h-5 text-[var(--positive)] mb-2" />
              <h3 className="font-bold text-[var(--text)] text-xs mb-0.5">Response Time</h3>
              <p className="text-xs text-[var(--text-muted)]">Within 24 to 48 business hours.</p>
            </div>

            <div className="p-4 rounded-xl bg-[var(--bg-alt)] border border-[var(--border)]">
              <Shield className="w-5 h-5 text-[var(--text)] mb-2" />
              <h3 className="font-bold text-[var(--text)] text-xs mb-0.5">DMCA Inquiries</h3>
              <p className="text-xs text-[var(--text-muted)] font-mono">dmca@winplaybox.in</p>
            </div>
          </div>

          {/* Form Side */}
          <div className="md:col-span-7">
            {submitted ? (
              <div className="p-8 rounded-xl bg-[var(--positive-bg)] border border-[var(--positive)]/30 text-center text-xs">
                <CheckCircle2 className="w-10 h-10 text-[var(--positive)] mx-auto mb-3" />
                <h3 className="font-bold text-[var(--text)] text-base mb-1">Message Sent!</h3>
                <p className="text-[var(--text-muted)] max-w-sm mx-auto">
                  Thank you for reaching out. Your inquiry has been dispatched to our engineering team and will be reviewed shortly.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4 text-xs">
                {submitError && (
                  <div className="p-3 rounded-lg bg-[var(--negative-bg)] border border-[var(--negative)]/20 text-[var(--negative)] flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{submitError}</span>
                  </div>
                )}

                <div>
                  <label className="block text-[var(--text-muted)] font-semibold mb-1">Your Name</label>
                  <input
                    type="text"
                    required
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="John Doe"
                    className="w-full bg-[var(--bg-alt)] border border-[var(--border)] rounded-lg px-3.5 py-2.5 text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)] transition"
                  />
                </div>

                <div>
                  <label className="block text-[var(--text-muted)] font-semibold mb-1">Your Email</label>
                  <input
                    type="email"
                    required
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    placeholder="name@example.com"
                    className="w-full bg-[var(--bg-alt)] border border-[var(--border)] rounded-lg px-3.5 py-2.5 text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)] transition"
                  />
                </div>

                <div>
                  <label className="block text-[var(--text-muted)] font-semibold mb-1">Subject</label>
                  <input
                    type="text"
                    required
                    value={form.subject}
                    onChange={(e) => setForm({ ...form, subject: e.target.value })}
                    placeholder="Feature feedback / Bug report"
                    className="w-full bg-[var(--bg-alt)] border border-[var(--border)] rounded-lg px-3.5 py-2.5 text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)] transition"
                  />
                </div>

                <div>
                  <label className="block text-[var(--text-muted)] font-semibold mb-1">Message</label>
                  <textarea
                    rows={4}
                    required
                    value={form.message}
                    onChange={(e) => setForm({ ...form, message: e.target.value })}
                    placeholder="Describe your question or issue in detail..."
                    className="w-full bg-[var(--bg-alt)] border border-[var(--border)] rounded-lg p-3 text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)] transition resize-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-2.5 rounded-lg bg-[var(--primary)] text-[var(--on-primary)] hover:opacity-90 font-semibold text-xs flex items-center justify-center gap-2 shadow-xs transition-opacity disabled:opacity-50 cursor-pointer"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Sending Message...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Send Message</span>
                    </>
                  )}
                </button>
              </form>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
