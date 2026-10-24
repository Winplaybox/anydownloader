import React, { useState } from 'react';
import { Mail, MessageSquare, Send, CheckCircle2, Clock, Shield } from 'lucide-react';

export default function ContactPage() {
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' });

  function handleSubmit(e) {
    e.preventDefault();
    setSubmitted(true);
  }

  return (
    <div className="py-14 max-w-4xl mx-auto px-4 sm:px-6">
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl p-6 sm:p-10 shadow-[var(--shadow-2)]">

        <div className="flex items-center gap-2 mb-4">
          <span className="px-3 py-1 rounded-full bg-[var(--positive-bg)] text-[var(--positive)] border border-[var(--border)] text-xs font-bold uppercase tracking-wider">
            Help & Inquiries
          </span>
          <span className="text-xs text-[var(--text-muted)]">Official Winplaybox Helpdesk</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-black text-[var(--text)] tracking-tight mb-4">
          Contact Us & Support
        </h1>
        <p className="text-xs sm:text-sm text-[var(--text-muted)] mb-8 leading-relaxed max-w-2xl">
          Have questions, technical feedback, bug reports, or partnership inquiries regarding OVD? Reach out directly through the form below or email us.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">

          {/* Info Side */}
          <div className="md:col-span-5 space-y-4">
            <div className="p-4 rounded-2xl bg-[var(--bg-alt)] border border-[var(--border)]">
              <Mail className="w-5 h-5 text-[var(--accent)] mb-2" />
              <h4 className="font-bold text-[var(--text)] text-xs mb-1">Email Support</h4>
              <p className="text-[11px] text-[var(--text-muted)] font-mono">support@winplaybox.in</p>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--bg-alt)] border border-[var(--border)]">
              <Clock className="w-5 h-5 text-[var(--positive)] mb-2" />
              <h4 className="font-bold text-[var(--text)] text-xs mb-1">Response Time</h4>
              <p className="text-[11px] text-[var(--text-muted)]">Within 24 to 48 business hours.</p>
            </div>

            <div className="p-4 rounded-2xl bg-[var(--bg-alt)] border border-[var(--border)]">
              <Shield className="w-5 h-5 text-[var(--accent)] mb-2" />
              <h4 className="font-bold text-[var(--text)] text-xs mb-1">DMCA Inquiries</h4>
              <p className="text-[11px] text-[var(--text-muted)] font-mono">dmca@winplaybox.in</p>
            </div>
          </div>

          {/* Form Side */}
          <div className="md:col-span-7">
            {submitted ? (
              <div className="p-8 rounded-2xl bg-[var(--positive-bg)] border border-[var(--border)] text-center text-xs">
                <CheckCircle2 className="w-10 h-10 text-[var(--positive)] mx-auto mb-3" />
                <h3 className="font-bold text-[var(--text)] text-base mb-1">Message Sent!</h3>
                <p className="text-[var(--text-muted)]">Thank you for reaching out. Our team will review your inquiry shortly.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4 text-xs">
                {[
                  { label: 'Your Name', key: 'name', type: 'text', placeholder: 'John Doe' },
                  { label: 'Your Email', key: 'email', type: 'email', placeholder: 'name@example.com' },
                  { label: 'Subject', key: 'subject', type: 'text', placeholder: 'Feature feedback / Support request' },
                ].map(({ label, key, type, placeholder }) => (
                  <div key={key}>
                    <label className="block text-[var(--text-muted)] font-semibold mb-1">{label}</label>
                    <input
                      type={type}
                      required
                      value={form[key]}
                      onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                      placeholder={placeholder}
                      className="w-full bg-[var(--bg)] border border-[var(--border)] rounded-xl px-3.5 py-2.5 text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)] transition"
                    />
                  </div>
                ))}

                <div>
                  <label className="block text-[var(--text-muted)] font-semibold mb-1">Message</label>
                  <textarea
                    rows={4}
                    required
                    value={form.message}
                    onChange={(e) => setForm({ ...form, message: e.target.value })}
                    placeholder="Describe your question or issue in detail..."
                    className="w-full bg-[var(--bg)] border border-[var(--border)] rounded-xl px-3.5 py-2.5 text-[var(--text)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-strong)] transition resize-none"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-3 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] font-bold text-xs hover:opacity-90 active:scale-[0.99] transition flex items-center justify-center gap-2 shadow-[var(--shadow-1)]"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Send Message</span>
                </button>
              </form>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}
