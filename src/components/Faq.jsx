import React, { useState } from 'react';
import { ChevronDown, HelpCircle } from 'lucide-react';

export default function Faq() {
  const [openIdx, setOpenIdx] = useState(0);

  const faqs = [
    {
      q: 'Which platforms are supported in OVD Phase 1?',
      a: 'OVD supports public videos and images from Twitter/X, YouTube, Facebook, Instagram, and TikTok. Other sites like Pinterest and Reddit will be added in upcoming phases.'
    },
    {
      q: 'Is there any download limit or subscription fee?',
      a: 'No. OVD is 100% free with unlimited downloads for all users. No registration, account creation, or payment is required.'
    },
    {
      q: 'Can I download Twitter multi-image posts and Instagram carousels?',
      a: 'Yes. OVD parses 4-image tweets and Instagram photo/video carousels so you can download individual photos in original resolution or download all items with one click.'
    },
    {
      q: 'Can I download private, age-restricted, or DRM-protected content?',
      a: 'No. OVD strictly respects privacy and copyright protections. Only public posts that do not require private logins or DRM decryption can be resolved.'
    },
    {
      q: 'Are the downloads safe and direct?',
      a: 'Yes. All downloads are proxied through cryptographically signed HMAC tokens with strict SSRF protection and direct streaming.'
    }
  ];

  return (
    <section className="w-full max-w-4xl mx-auto px-4 py-16 border-t border-[var(--border)]">
      <div className="text-center space-y-2 mb-10">
        <h2 className="base-heading text-2xl sm:text-3xl font-extrabold text-[var(--text)]">
          Frequently Asked Questions
        </h2>
        <p className="base-paragraph text-sm sm:text-base text-[var(--text-muted)]">
          Everything you need to know about downloading videos and images with OVD.
        </p>
      </div>

      <div className="space-y-3">
        {faqs.map((faq, idx) => {
          const isOpen = openIdx === idx;
          return (
            <div 
              key={idx}
              className="rounded-xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden transition-colors"
            >
              <button
                type="button"
                onClick={() => setOpenIdx(isOpen ? null : idx)}
                className="w-full flex items-center justify-between p-4 sm:p-5 text-left font-bold text-base text-[var(--text)] hover:bg-[var(--bg-alt)] transition-colors"
              >
                <span>{faq.q}</span>
                <ChevronDown className={`w-5 h-5 shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
              </button>

              {isOpen && (
                <div className="px-5 pb-5 pt-1 text-sm text-[var(--text-muted)] leading-relaxed border-t border-[var(--border)]/50 animate-in fade-in duration-150">
                  {faq.a}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
