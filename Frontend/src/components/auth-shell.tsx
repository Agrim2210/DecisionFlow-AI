import { ArrowLeft, ArrowUpRight, Check, Globe2, Sparkles } from "lucide-react";
import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";

const DECISIONFLOW_VIDEO_SRC =
  "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_115001_bcdaa3b4-03de-47e7-ad63-ae3e392c32d4.mp4";

export function AuthShell({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: ReactNode;
  description: string;
  children: ReactNode;
}) {
  return (
    <div className="df-auth-bg relative overflow-hidden text-white">
      <video
        className="df-workspace-video"
        src={DECISIONFLOW_VIDEO_SRC}
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
        aria-hidden="true"
      />
      <div className="df-workspace-video-wash" />
      <div className="df-workspace-noise" />
      <div className="pointer-events-none absolute -left-24 top-16 h-72 w-72 rounded-full bg-cyan-200/10 blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[34rem] w-[34rem] rounded-full bg-violet-300/10 blur-3xl" />
      <div className="df-auth-content relative mx-auto flex min-h-screen max-w-7xl flex-col px-5 py-5 sm:px-8">
        <header className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <span className="df-brand-orb">
              <Globe2 size={17} strokeWidth={1.5} />
            </span>
            <span className="font-display text-sm font-semibold tracking-[.14em]">
              DECISIONFLOW <span className="text-cyan-200">AI</span>
            </span>
          </Link>
          <Link to="/" className="df-nav-link inline-flex items-center gap-2">
            <ArrowLeft size={14} /> Back to landing
          </Link>
        </header>
        <main className="df-workflow-stage relative flex flex-1 items-center justify-center py-16">
          <section className="df-auth-copy max-w-xl">
            <p className="df-kicker">{eyebrow}</p>
            <h1 className="mt-6 font-display text-5xl font-semibold leading-[.96] tracking-[-.06em] sm:text-7xl">
              {title}
            </h1>
            <p className="mt-7 max-w-md text-base leading-7 text-white/55">{description}</p>
            <div className="mt-10 space-y-4">
              <Signal text="Transcript in. Ownership out." />
              <Signal text="One live trail for the whole team." />
              <Signal text="Built for the follow-through." />
            </div>
          </section>
          <section className="df-auth-card df-app-card relative mx-auto w-full max-w-md rounded-[30px] p-6 shadow-2xl shadow-cyan-950/20 sm:p-8">
            {children}
          </section>
        </main>
        <footer className="flex items-center justify-between border-t border-white/10 py-5 text-[11px] text-white/35">
          <span>DecisionFlow AI · make the meeting keep moving</span>
          <span className="hidden items-center gap-2 sm:flex">
            <Sparkles size={12} /> Secure team workspace
          </span>
        </footer>
      </div>
    </div>
  );
}
function Signal({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-white/55">
      <span className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-cyan-200/35 text-cyan-100">
        <Check size={12} />
      </span>
      {text}
    </div>
  );
}
export function AuthField({
  label,
  type = "text",
  value,
  onChange,
  placeholder,
}: {
  label: string;
  type?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-medium text-white/58">{label}</span>
      <input
        required
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="df-app-input w-full rounded-2xl px-4 py-3.5 text-sm text-white placeholder:text-white/28"
      />
    </label>
  );
}
export function AuthSubmit({ children, busy }: { children: ReactNode; busy: boolean }) {
  return (
    <button
      disabled={busy}
      className="mt-2 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[#c9fbfc] px-4 py-3.5 text-sm font-bold text-[#071014] transition hover:bg-white disabled:cursor-wait disabled:opacity-60"
    >
      {busy ? "Connecting…" : children}
      <ArrowUpRight size={15} />
    </button>
  );
}
