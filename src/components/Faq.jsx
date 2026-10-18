import React from 'react';

const FAQS = [
  {
    q: 'Is AnyDownloader completely free to use?',
    a: 'Yes, AnyDownloader is 100% free with no hidden charges, no software installation, and no subscription required.'
  },
  {
    q: 'Does it support downloading TikTok videos without watermark?',
    a: 'Yes! When you paste a TikTok URL, our Python backend extracts the clean HD MP4 stream without the TikTok watermark.'
  },
  {
    q: 'Can I download audio as MP3?',
    a: 'Absolutely. Every video supports extraction to MP3 audio up to 320 kbps high-fidelity quality.'
  },
  {
    q: 'Where are the downloaded files saved?',
    a: 'Files are saved directly to your device\'s default "Downloads" folder (on Android, iPhone/iPad, Mac, and Windows PC).'
  },
  {
    q: 'Do I need to install any app or extension?',
    a: 'No, AnyDownloader works directly in any modern browser including Chrome, Safari, Edge, Firefox, and Brave on all devices.'
  }
];

export default function Faq() {
  return (
    <section id="faq" className="py-16 max-w-4xl mx-auto px-4">
      <div className="text-center mb-10">
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-2">
          Frequently Asked Questions
        </h2>
        <p className="text-slate-400 text-sm">
          Everything you need to know about using AnyDownloader.
        </p>
      </div>

      <div className="space-y-4">
        {FAQS.map((f, idx) => (
          <div key={idx} className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="font-bold text-white text-sm sm:text-base mb-2">
              {f.q}
            </h3>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              {f.a}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
