import React from 'react';
import { Copy, Link as LinkIcon, Download } from 'lucide-react';

export default function HowItWorks() {
  const steps = [
    {
      num: '01',
      title: 'Copy Post Link',
      desc: 'Copy the URL of the public video or photo post from X (Twitter), YouTube, Facebook, Instagram, or TikTok.',
      icon: Copy
    },
    {
      num: '02',
      title: 'Paste into Box',
      desc: 'Paste the link into the OVD input box above. Our intelligent normalizer automatically detects the platform.',
      icon: LinkIcon
    },
    {
      num: '03',
      title: 'Download Media',
      desc: 'Choose your desired video resolution or image quality and click Download for instant, high-speed transfer.',
      icon: Download
    }
  ];

  return (
    <section className="w-full max-w-5xl mx-auto px-4 py-16 border-t border-[var(--border)]">
      <div className="text-center space-y-2 mb-12">
        <h2 className="base-heading text-2xl sm:text-3xl font-extrabold text-[var(--text)]">
          How to Download in 3 Simple Steps
        </h2>
        <p className="base-paragraph text-sm sm:text-base text-[var(--text-muted)] max-w-xl mx-auto">
          No sign-ups, no software installation, and no complex configurations.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {steps.map(step => {
          const Icon = step.icon;
          return (
            <div 
              key={step.num}
              className="p-6 rounded-2xl bg-[var(--surface)] border-2 border-[var(--border)] hover:border-[var(--border-strong)] transition-all shadow-[var(--shadow-1)] flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-[var(--primary)] text-[var(--on-primary)] flex items-center justify-center font-bold">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-2xl font-black text-[var(--text-muted)] opacity-50">
                    {step.num}
                  </span>
                </div>
                <h3 className="font-bold text-lg text-[var(--text)] mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-[var(--text-muted)] leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
