import React from 'react';
import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <section className="max-w-xl mx-auto px-4 py-24 text-center">
      <p className="text-sm font-semibold text-[var(--text-muted)]">Error 404</p>
      <h1 className="mt-2 text-4xl font-extrabold text-[var(--text)]">This page does not exist</h1>
      <p className="mt-3 text-[var(--text-muted)]">The link may be old or mistyped. Paste your video link on the home page instead.</p>
      <Link to="/" className="mt-7 inline-flex h-12 items-center gap-2 rounded-2xl bg-[var(--primary)] px-6 font-bold text-[var(--on-primary)]"><Home className="w-5 h-5" /> Go to home</Link>
    </section>
  );
}
