import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AuthField, AuthShell, AuthSubmit } from "../components/auth-shell";
import { useSession } from "../lib/session";
import { ApiError } from "../lib/api";

export const Route = createFileRoute("/signup")({ component: SignupPage });

function SignupPage() {
  const navigate = useNavigate();
  const { user, loading, signUp } = useSession();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  useEffect(() => {
    if (!loading && user) navigate({ to: "/app" });
  }, [loading, navigate, user]);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setBusy(true);
    try {
      const payload = await signUp(name, email, password);
      const hasSession = Boolean(payload.tokens || payload.access_token || payload.user);
      if (hasSession) {
        navigate({ to: "/app" });
      } else {
        setSuccess(
          "Your workspace request was received. Check your email to verify the account, then sign in.",
        );
      }
    } catch (cause) {
      setError(
        cause instanceof ApiError ? cause.message : "Unable to create your workspace right now.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <AuthShell
      eyebrow="START WITH CLARITY"
      title={
        <>
          Turn talk
          <br />
          into <em className="not-italic text-cyan-200">traction.</em>
        </>
      }
      description="Create the shared memory your team needs to turn good conversations into reliable movement."
    >
      <div>
        <p className="df-kicker">CREATE YOUR FLOW</p>
        <h2 className="mt-4 font-display text-2xl font-semibold tracking-[-.04em]">
          Your next step starts here
        </h2>
        <p className="mt-2 text-sm leading-6 text-white/45">
          Set up your workspace and give every meeting a next move.
        </p>
        <form onSubmit={submit} className="mt-8 space-y-4">
          <AuthField label="Your name" value={name} onChange={setName} placeholder="Alex Morgan" />
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
            placeholder="At least 8 characters"
          />
          {error && (
            <p className="rounded-xl border border-rose-300/20 bg-rose-200/5 px-3 py-2 text-xs text-rose-100">
              {error}
            </p>
          )}
          {success && (
            <p className="rounded-xl border border-cyan-200/20 bg-cyan-200/5 px-3 py-2 text-xs leading-5 text-cyan-100">
              {success}
            </p>
          )}
          <AuthSubmit busy={busy}>Create workspace</AuthSubmit>
        </form>
        <p className="mt-6 text-center text-xs text-white/40">
          Already have a flow?{" "}
          <button
            type="button"
            onClick={() => navigate({ to: "/login" })}
            className="text-cyan-200 hover:text-white"
          >
            Sign in
          </button>
        </p>
      </div>
    </AuthShell>
  );
}
