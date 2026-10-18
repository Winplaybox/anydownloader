import React from 'react';
import { ShieldCheck, Lock, Eye, Cookie, FileText } from 'lucide-react';

export default function PrivacyPolicyPage() {
  return (
    <div className="py-14 max-w-4xl mx-auto px-4 sm:px-6 text-slate-300">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-10 shadow-2xl">
        
        <div className="flex items-center gap-2 mb-4">
          <span className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-bold uppercase tracking-wider">
            Legal & Compliance
          </span>
          <span className="text-xs text-slate-500">Updated: October 2026</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-6">
          Privacy Policy
        </h1>

        <div className="space-y-6 text-xs sm:text-sm leading-relaxed text-slate-400">
          <p>
            At <strong className="text-white">OVD.winplaybox.in</strong> ("OVD", "we", "us", or "our"), accessible from <a href="https://ovd.winplaybox.in/" className="text-rose-400 underline">https://ovd.winplaybox.in/</a>, one of our main priorities is the privacy of our visitors. This Privacy Policy document outlines the types of information collected and recorded by OVD and how we use it, in compliance with GDPR, CCPA, and Google AdSense policies.
          </p>

          <h2 className="text-base sm:text-lg font-bold text-white pt-2">1. Information We Do Not Collect</h2>
          <p>
            OVD does not require user registration or account creation. We do not collect personal identifying information like passwords, credit card numbers, or physical addresses. URL links submitted into the downloader tool are processed in real-time to locate direct streams and are never stored or associated with personal identities.
          </p>

          <h2 className="text-base sm:text-lg font-bold text-white pt-2">2. Log Files & Analytics</h2>
          <p>
            Like many web services, OVD follows a standard procedure of using log files. These files log visitors when they visit websites. The information collected by log files includes internet protocol (IP) addresses, browser type, Internet Service Provider (ISP), date and time stamp, referring/exit pages, and possibly the number of clicks. These are not linked to any information that is personally identifiable. The purpose of the information is for analyzing trends, administering the site, tracking users' movement on the website, and gathering demographic information.
          </p>

          <h2 className="text-base sm:text-lg font-bold text-white pt-2">3. Cookies & Google AdSense DoubleClick DART Cookies</h2>
          <p>
            Google is one of a third-party vendor on our site. It also uses cookies, known as DART cookies, to serve ads to our site visitors based upon their visit to our site and other sites on the internet. However, visitors may choose to decline the use of DART cookies by visiting the Google ad and content network Privacy Policy at the following URL: <a href="https://policies.google.com/technologies/ads" target="_blank" rel="noreferrer" className="text-rose-400 underline">https://policies.google.com/technologies/ads</a>.
          </p>
          <p>
            Some of our advertising partners may use cookies and web beacons on our site. Third-party ad servers or ad networks use technologies like cookies, JavaScript, or Web Beacons that are used in their respective advertisements and links that appear on OVD, which are sent directly to users' browser. They automatically receive your IP address when this occurs.
          </p>

          <h2 className="text-base sm:text-lg font-bold text-white pt-2">4. Third-Party Privacy Policies</h2>
          <p>
            OVD's Privacy Policy does not apply to other advertisers or websites. Thus, we are advising you to consult the respective Privacy Policies of these third-party ad servers for more detailed information. It may include their practices and instructions about how to opt-out of certain options.
          </p>

          <h2 className="text-base sm:text-lg font-bold text-white pt-2">5. GDPR & CCPA Privacy Rights</h2>
          <p>
            Under the General Data Protection Regulation (GDPR) and California Consumer Privacy Act (CCPA), you have rights regarding your personal data. Because we do not store personal profiles, we do not sell personal information. If you make a request regarding any log records, we have one month to respond to you.
          </p>

          <h2 className="text-base sm:text-lg font-bold text-white pt-2">6. Contact Information</h2>
          <p>
            If you have additional questions or require more information about our Privacy Policy, do not hesitate to contact our administrative team at <a href="mailto:support@winplaybox.in" className="text-rose-400 underline">support@winplaybox.in</a>.
          </p>
        </div>

      </div>
    </div>
  );
}
