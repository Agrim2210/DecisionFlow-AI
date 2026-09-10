import { createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  Globe2,
  LockKeyhole,
  ScanLine,
  Sparkles,
  Zap,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

const VIDEO_SRC =
  "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_115001_bcdaa3b4-03de-47e7-ad63-ae3e392c32d4.mp4";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "DecisionFlow AI — Meetings into accountable momentum" },
      {
        name: "description",
        content:
          "Turn meeting transcripts into clear decisions, owned work, and momentum your team can see.",
      },
      { property: "og:title", content: "DecisionFlow AI" },
      {
        property: "og:description",
        content: "Make every meeting leave a trail of decisions and accountable next steps.",
      },
    ],
  }),
  component: Index,
});

function Index() {
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const landingRef = useRef<HTMLDivElement | null>(null);
  const [scrollY, setScrollY] = useState(0);
  const [pointer, setPointer] = useState({ x: 0, y: 0 });
  const [email, setEmail] = useState("");
  const [introDismissed, setIntroDismissed] = useState(false);

  useEffect(() => {
    let scrollRaf: number | null = null;
    let pointerRaf: number | null = null;

    const updateScroll = () => {
      if (scrollRaf === null) {
        scrollRaf = requestAnimationFrame(() => {
          setScrollY(window.scrollY);
          if (window.scrollY > 80 && !introDismissed) {
            setIntroDismissed(true);
          }
          scrollRaf = null;
        });
      }
    };

    const move = (event: PointerEvent) => {
      if (pointerRaf === null) {
        const x = (event.clientX / window.innerWidth - 0.5) * 2;
        const y = (event.clientY / window.innerHeight - 0.5) * 2;
        pointerRaf = requestAnimationFrame(() => {
          setPointer({ x, y });
          pointerRaf = null;
        });
      }
    };

    updateScroll();
    window.addEventListener("scroll", updateScroll, { passive: true });
    window.addEventListener("resize", updateScroll, { passive: true });
    window.addEventListener("pointermove", move, { passive: true });

    return () => {
      if (scrollRaf !== null) cancelAnimationFrame(scrollRaf);
      if (pointerRaf !== null) cancelAnimationFrame(pointerRaf);
      window.removeEventListener("scroll", updateScroll);
      window.removeEventListener("resize", updateScroll);
      window.removeEventListener("pointermove", move);
    };
  }, [introDismissed]);

  // Video background fade-in
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onLoaded = () => {
      video.style.opacity = "1";
    };

    video.addEventListener("loadeddata", onLoaded);
    if (video.readyState >= 2) {
      video.style.opacity = "1";
    }

    return () => {
      video.removeEventListener("loadeddata", onLoaded);
    };
  }, []);

  const scrollToLanding = () => {
    setIntroDismissed(true);
    if (landingRef.current) {
      landingRef.current.scrollIntoView({ behavior: "smooth" });
    } else {
      window.scrollTo({ top: window.innerHeight, behavior: "smooth" });
    }
  };

  const startAuth = (mode: "login" | "signup") =>
    navigate({
      to: mode === "login" ? "/login" : "/signup",
      search: email ? { email } : undefined,
    });

  const viewport = typeof window === "undefined" ? 1 : Math.max(window.innerHeight, 1);
  const introProgress = Math.min(1, Math.max(0, scrollY / (viewport * 0.75)));

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-[#05060a] text-white">
      {/* Cinematic Ambient Background */}
      <div className="df-film-stage fixed inset-0 z-0 overflow-hidden bg-black">
        <video
          ref={videoRef}
          className="absolute inset-0 h-full w-full object-cover transition-opacity duration-1000 opacity-60"
          src={VIDEO_SRC}
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
        />
        <div className="df-video-wash" />
        <div className="df-noise" />
        <div className="df-grid-glow opacity-30" />
      </div>

      {/* Hero Intro Section (lightning/stone animation) */}
      <IntroHero
        progress={introProgress}
        onEnter={scrollToLanding}
        pointer={pointer}
      />

      {/* Main Landing Page Content - fully loaded and accessible */}
      <div ref={landingRef} id="main-content" className="relative z-10">
        {/* Navigation */}
        <div className="sticky top-0 z-40 mx-auto max-w-[1440px] px-5 pt-4 sm:px-8 lg:px-12">
          <nav className="df-glass-panel flex items-center justify-between rounded-full px-4 py-3 sm:px-6 shadow-2xl">
            <a href="#top" className="flex items-center gap-3" aria-label="DecisionFlow AI home">
              <span className="df-brand-orb">
                <Globe2 size={17} strokeWidth={1.5} />
              </span>
              <span className="font-display text-sm font-semibold tracking-[0.14em] text-white/90">
                DECISIONFLOW <span className="text-cyan-200">AI</span>
              </span>
            </a>
            <div className="hidden items-center gap-7 md:flex">
              <a href="#how-it-works" className="df-nav-link">
                How it works
              </a>
              <a href="#signal" className="df-nav-link">
                Signal layer
              </a>
              <a href="#proof" className="df-nav-link">
                Why teams stay
              </a>
            </div>
            <div className="flex items-center gap-2 sm:gap-4">
              <button onClick={() => startAuth("login")} className="df-nav-link px-2">
                Log in
              </button>
              <button
                onClick={() => startAuth("signup")}
                className="df-pill-button hidden sm:inline-flex"
              >
                Get started <ArrowUpRight size={14} />
              </button>
            </div>
          </nav>
        </div>

        {/* Hero Section */}
        <main
          id="top"
          className="relative mx-auto flex min-h-[90vh] max-w-[1440px] flex-col items-center justify-center px-5 pb-16 pt-8 text-center sm:px-8 lg:px-12"
        >
          <div
            className="pointer-events-none absolute left-[9%] top-[21%] hidden text-left lg:block"
            style={{
              transform: `translate3d(${pointer.x * 12}px, ${pointer.y * 10}px, 80px)`,
            }}
          >
            <p className="df-kicker">THE ACCOUNTABILITY LAYER</p>
            <p className="mt-3 max-w-[170px] text-xs leading-5 text-white/45">
              From spoken intent to a visible trail of work.
            </p>
          </div>

          <div
            className="pointer-events-none absolute right-[9%] top-[30%] hidden text-left lg:block"
            style={{
              transform: `translate3d(${pointer.x * -18}px, ${pointer.y * -10}px, 120px)`,
            }}
          >
            <div className="df-status-dot" />
            <p className="mt-3 text-xs text-white/55">Signal acquired</p>
            <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.24em] text-cyan-200/60">
              00:03:18:44
            </p>
          </div>

          <div className="relative z-10 mx-auto max-w-5xl">
            <div className="df-kicker mb-7 flex items-center justify-center gap-3">
              <span className="df-kicker-line" /> <span>TRANSCRIPTS → MOMENTUM</span>{" "}
              <span className="df-kicker-line" />
            </div>
            <h1 className="df-hero-title">
              Make the meeting
              <br />
              <em>keep moving.</em>
            </h1>
            <p className="mx-auto mt-7 max-w-xl text-base leading-7 text-white/68 sm:text-lg">
              DecisionFlow AI turns the unstructured air of a meeting into decisions, owners,
              deadlines, and a clear next move.
            </p>

            <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  startAuth("signup");
                }}
                className="df-email-capsule flex w-full max-w-[390px] items-center gap-3 rounded-full p-1.5 pl-5"
              >
                <input
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  type="email"
                  placeholder="Your work email"
                  aria-label="Work email"
                  className="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-white/35"
                />
                <button aria-label="Continue with email" className="df-icon-button">
                  <ArrowRight size={18} />
                </button>
              </form>
              <button onClick={() => startAuth("signup")} className="df-secondary-button">
                See the signal <ArrowUpRight size={16} />
              </button>
            </div>

            <p className="mt-5 text-[11px] uppercase tracking-[0.22em] text-white/35">
              <LockKeyhole size={12} className="mr-1 inline" /> Built for teams that follow through
            </p>
          </div>
        </main>

        {/* Section 1: How It Works */}
        <section
          id="how-it-works"
          className="relative z-10 border-t border-white/[.08] px-5 pb-28 pt-24 sm:px-8 lg:px-12"
        >
          <div className="mx-auto max-w-[1180px]">
            <div className="mb-16 flex flex-col justify-between gap-8 md:flex-row md:items-end">
              <div>
                <p className="df-kicker">01 / THE HANDOFF</p>
                <h2 className="df-section-title mt-5 max-w-2xl">
                  The work starts
                  <br />
                  <em>where the call ends.</em>
                </h2>
              </div>
              <p className="max-w-sm text-sm leading-6 text-white/50">
                A meeting should not disappear into a document. Give every commitment a surface, a
                signal, and an owner.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <FeatureCard
                number="01"
                icon={<ScanLine size={20} />}
                title="Capture the signal"
                body="Upload a transcript or paste the notes. DecisionFlow reads the room without making your team change how they talk."
              />
              <FeatureCard
                number="02"
                icon={<Zap size={20} />}
                title="Name the next move"
                body="Decisions, risks, open questions, and action items become a shared map with accountable owners and dates."
              />
              <FeatureCard
                number="03"
                icon={<Check size={20} />}
                title="Keep the promise"
                body="See what is moving, what is blocked, and where attention is needed before momentum quietly decays."
              />
            </div>

            {/* Section 2: Signal Layer & Quote */}
            <div className="mt-20 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]" id="signal">
              <div className="df-signal-card rounded-[28px] p-7 sm:p-10">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="df-kicker">THE SIGNAL LAYER</p>
                    <h3 className="mt-4 max-w-lg font-display text-3xl font-semibold tracking-[-0.04em] text-white sm:text-4xl">
                      A calm, live view
                      <br />
                      of what matters.
                    </h3>
                  </div>
                  <span className="df-live-badge">
                    LIVE <span />
                  </span>
                </div>
                <div className="mt-12 grid gap-3 sm:grid-cols-3">
                  <Metric label="Decisions" value="18" trend="+24%" />
                  <Metric label="Owned work" value="42" trend="+11%" />
                  <Metric label="At risk" value="03" trend="needs focus" warm />
                </div>
                <div className="df-waveform mt-10">
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                </div>
              </div>

              <div className="df-quote-card rounded-[28px] p-7 sm:p-10 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 text-cyan-200/75">
                    <Sparkles size={15} />
                    <span className="df-kicker">WHY TEAMS STAY</span>
                  </div>
                  <p className="mt-8 font-display text-2xl leading-9 tracking-[-0.03em] text-white/90 sm:text-3xl">
                    “The clarity is not in the summary. It is in knowing what happens next.”
                  </p>
                </div>
                <p className="mt-8 text-xs uppercase tracking-[0.2em] text-white/35">
                  A better memory for the team
                </p>
              </div>
            </div>

            {/* Section 3: Bottom Proof / CTA */}
            <div
              id="proof"
              className="mt-20 flex flex-col items-start justify-between gap-8 border-t border-white/10 pt-10 sm:flex-row sm:items-center"
            >
              <p className="max-w-lg text-sm leading-6 text-white/45">
                When the trail is visible, accountability stops feeling like chasing and starts
                feeling like alignment.
              </p>
              <button onClick={() => startAuth("signup")} className="df-pill-button">
                Build your flow <ArrowRight size={15} />
              </button>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function IntroHero({
  progress,
  onEnter,
  pointer,
}: {
  progress: number;
  onEnter: () => void;
  pointer?: { x: number; y: number };
}) {
  const exit = Math.min(1, Math.max(0, (progress - 0.2) / 0.8));

  return (
    <section
      className="df-stone-intro relative z-20 flex h-screen items-center justify-center overflow-hidden cursor-pointer"
      onClick={onEnter}
      aria-label="DecisionFlow AI cinematic introduction"
      style={{
        opacity: Math.max(0, 1 - exit * 1.2),
        transform: `scale(${1 + exit * 0.15}) translateY(${exit * -40}px)`,
        pointerEvents: exit > 0.85 ? "none" : "auto",
      }}
    >
      <div className="df-stone-void" />
      <div className="df-stone-horizon" />
      <div className="df-electric-cloud cloud-a" />
      <div className="df-electric-cloud cloud-b" />
      <div className="df-weather-bolt" aria-hidden="true">
        <svg viewBox="0 0 120 220" role="presentation" preserveAspectRatio="none">
          <path
            className="weather-bolt-glow"
            pathLength="1"
            d="M112 0 L96 18 L103 34 L79 48 L89 63 L63 79 L73 95 L47 111 L58 127 L29 146 L41 163 L14 183 L23 201 L0 220"
          />
          <path
            className="weather-bolt-core"
            pathLength="1"
            d="M112 0 L96 18 L103 34 L79 48 L89 63 L63 79 L73 95 L47 111 L58 127 L29 146 L41 163 L14 183 L23 201 L0 220"
          />
          <path className="weather-bolt-branch branch-a" pathLength="1" d="M79 48 L57 39 L47 25" />
          <path className="weather-bolt-branch branch-b" pathLength="1" d="M63 79 L86 75 L99 59" />
          <path className="weather-bolt-branch branch-c" pathLength="1" d="M47 111 L23 103 L9 89" />
        </svg>
      </div>
      <div className="df-electric-spark spark-opposite" />
      <div className="df-reference-sparks" />
      <div className="df-stone-flash" />
      <div className="df-stone-dust" />
      <div className="df-stone-impact impact-one" />
      <div className="df-stone-impact impact-two" />
      <div className="df-stone-debris debris-one" />
      <div className="df-stone-debris debris-two" />
      <div className="df-stone-debris debris-three" />
      <div className="df-stone-fragment-field" aria-hidden="true">
        <span className="stone-fragment fragment-01" />
        <span className="stone-fragment fragment-02" />
        <span className="stone-fragment fragment-03" />
        <span className="stone-fragment fragment-04" />
        <span className="stone-fragment fragment-05" />
        <span className="stone-fragment fragment-06" />
        <span className="stone-fragment fragment-07" />
        <span className="stone-fragment fragment-08" />
        <span className="stone-fragment fragment-09" />
        <span className="stone-fragment fragment-10" />
        <span className="stone-fragment fragment-11" />
        <span className="stone-fragment fragment-12" />
      </div>
      <div className="df-stone-rock" aria-hidden="true">
        <span className="df-stone-face face-one" />
        <span className="df-stone-face face-two" />
        <span className="df-stone-crack crack-one" />
        <span className="df-stone-crack crack-two" />
      </div>
      <div className="df-stone-title-wrap">
        <p className="df-stone-kicker">THE SIGNAL BECOMES CLEAR</p>
        <h1 className="df-stone-title">
          DecisionFlow <em>AI</em>
        </h1>
        <div className="df-stone-rule" />
      </div>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onEnter();
        }}
        className="df-stone-scroll hover:text-white transition"
      >
        <span>Enter the flow</span>
        <ChevronDown size={15} className="scroll-hint text-cyan-200" />
      </button>
    </section>
  );
}

function FeatureCard({
  number,
  icon,
  title,
  body,
}: {
  number: string;
  icon: React.ReactNode;
  title: string;
  body: string;
  }) {
  return (
    <article className="df-feature-card rounded-[26px] p-6 sm:p-7">
      <div className="flex items-center justify-between text-white/45">
        <span className="font-mono text-xs">{number}</span>
        <span className="df-feature-icon">{icon}</span>
      </div>
      <h3 className="mt-16 font-display text-2xl font-semibold tracking-[-0.04em]">{title}</h3>
      <p className="mt-4 text-sm leading-6 text-white/48">{body}</p>
    </article>
  );
}

function Metric({
  label,
  value,
  trend,
  warm = false,
}: {
  label: string;
  value: string;
  trend: string;
  warm?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
      <p className="text-xs text-white/45">{label}</p>
      <div className="mt-4 flex items-end justify-between gap-2">
        <strong className="font-display text-3xl font-semibold">{value}</strong>
        <span className={warm ? "text-xs text-amber-200/75" : "text-xs text-cyan-200/70"}>
          {trend}
        </span>
      </div>
    </div>
  );
}
