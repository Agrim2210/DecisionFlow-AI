import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AuthField, AuthShell, AuthSubmit } from "../components/auth-shell";
import { useSession } from "../lib/session";
import { ApiError } from "../lib/api";

export const Route = createFileRoute("/login")({ component: LoginPage });

function LoginPage() {
  const navigate = useNavigate();
  const { user, loading, signIn } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!loading && user) navigate({ to: "/app" });
  }, [loading, navigate, user]);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await signIn(email, password);
      navigate({ to: "/app" });
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Unable to sign in right now.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <AuthShell
      eyebrow="WELCOME BACK"
      title={
        <>
          Keep the
          <br />
          <em className="not-italic text-cyan-200">signal</em> alive.
        </>
      }
      description="Your team's decisions, owners, and next moves in one quiet, accountable workspace."
    >
      <div>
        <p className="df-kicker">SIGN IN TO YOUR FLOW</p>
        <h2 className="mt-4 font-display text-2xl font-semibold tracking-[-.04em]">
          Return to the room
        </h2>
        <p className="mt-2 text-sm leading-6 text-white/45">
          Pick up exactly where the last conversation left off.
        </p>
        <form onSubmit={submit} className="mt-8 space-y-4">
          <AuthField
            label="Work email"
            type="email"
            value={email}
            onChange={setEmail}
            placeholder="you@company.com"
          />
          <AuthField
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            placeholder="••••••••"
          />
          <div className="flex justify-end -mt-1">
            <button
              type="button"
              onClick={() => navigate({ to: "/forgot-password" })}
              className="text-xs text-cyan-200/70 hover:text-cyan-100 transition"
            >
              Forgot password?
            </button>
          </div>
          {error && (
            <p className="rounded-xl border border-rose-300/20 bg-rose-200/5 px-3 py-2 text-xs text-rose-100">
              {error}
            </p>
          )}
          <AuthSubmit busy={busy}>Sign in</AuthSubmit>
        </form>
        <p className="mt-6 text-center text-xs text-white/40">
          New to DecisionFlow?{" "}
          <button
            type="button"
            onClick={() => navigate({ to: "/signup" })}
            className="text-cyan-200 hover:text-white"
          >
            Create your workspace
          </button>
        </p>
      </div>
    </AuthShell>
  );
}
