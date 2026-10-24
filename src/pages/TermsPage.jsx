import React from 'react';
import { Scale, AlertCircle, Shield, FileCheck } from 'lucide-react';

export default function TermsPage() {
  return (
    <div className="py-14 max-w-4xl mx-auto px-4 sm:px-6 text-[var(--text)]">
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl p-6 sm:p-10 shadow-[var(--shadow-2)]">
        
        <div className="flex items-center gap-2 mb-4">
          <span className="px-3 py-1 rounded-full bg-cyan-500/10 text-[var(--accent)] border border-cyan-500/20 text-xs font-bold uppercase tracking-wider">
            Terms of Service
          </span>
          <span className="text-xs text-[var(--text-muted)]">Effective: October 2026</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-black text-[var(--text)] tracking-tight mb-6">
          Terms of Service & Fair Use Policy
        </h1>

        <div className="space-y-6 text-xs sm:text-sm leading-relaxed text-[var(--text-muted)]">
          <p>
            Welcome to <strong className="text-[var(--text)]">OVD.winplaybox.in</strong> ("OVD"). By accessing or using our website, tools, and services, you agree to be bound by these Terms of Service. If you disagree with any part of the terms, you may not access the service.
          </p>

          <h2 className="text-base sm:text-lg font-bold text-[var(--text)] pt-2">1. Service Nature & Non-Hosting Disclaimer</h2>
          <p>
            OVD is a web-based protocol extraction and analytical utility. <strong className="text-[var(--accent)]">OVD does NOT host, save, store, or stream any copyrighted media or audio files on its servers.</strong> All stream endpoints and thumbnail images are loaded directly from the respective third-party content delivery networks (e.g. YouTube, Instagram, Facebook, TikTok) to the user's client browser.
          </p>

          <h2 className="text-base sm:text-lg font-bold text-[var(--text)] pt-2">2. Permitted & Fair Use</h2>
          <p>
            Our tools are intended strictly for personal, non-commercial, archival, and fair-use educational purposes (such as offline playback of your own created media, copyright-free content, public domain materials, or educational lectures). You agree not to use this service to infringe upon the intellectual property rights of any individual, artist, creator, or entity.
          </p>

          <h2 className="text-base sm:text-lg font-bold text-[var(--text)] pt-2">3. DMCA & Copyright Infringement Claims</h2>
          <p>
            OVD respects the intellectual property rights of others. Since OVD does not host any content, any request to delete copyright material from the internet must be directed to the third-party platforms hosting the content. However, if you are a copyright holder and wish to request blocking of a specific URL domain on our utility, please contact our agent at <a href="mailto:dmca@winplaybox.in" className="text-[var(--accent)] underline">dmca@winplaybox.in</a>.
          </p>

          <h2 className="text-base sm:text-lg font-bold text-[var(--text)] pt-2">4. Disclaimer of Warranties</h2>
          <p>
            The services provided by OVD are provided on an "AS IS" and "AS AVAILABLE" basis without warranties of any kind, whether express or implied. We do not warrant that the service will be uninterrupted, error-free, or free of bugs.
          </p>

          <h2 className="text-base sm:text-lg font-bold text-[var(--text)] pt-2">5. Governing Law</h2>
          <p>
            These terms shall be governed and construed in accordance with standard international web regulations and the applicable legal jurisdiction of Winplaybox.
          </p>
        </div>

      </div>
    </div>
  );
}

