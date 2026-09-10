import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { AuthField, AuthShell, AuthSubmit } from "../components/auth-shell";
import { api, ApiError } from "../lib/api";

export const Route = createFileRoute("/forgot-password")({ component: ForgotPasswordPage });

function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setBusy(true);
    try {
      const result = await api.forgotPassword({ email });
      setSuccess(
        result.message ||
          "If an account exists for that email, a password reset link has been sent. Check your inbox.",
      );
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "Unable to send reset link right now. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthShell
      eyebrow="ACCOUNT RECOVERY"
      title={
        <>
          Reset your
          <br />
          <em className="not-italic text-cyan-200">password.</em>
        </>
      }
      description="Enter the email address linked to your workspace and we'll send you a reset link."
    >
      <div>
        <p className="df-kicker">FORGOT YOUR PASSWORD?</p>
        <h2 className="mt-4 font-display text-2xl font-semibold tracking-[-.04em]">
          We'll get you back in
        </h2>
        <p className="mt-2 text-sm leading-6 text-white/45">
          Enter your work email and we'll send a secure link to reset your password.
        </p>
        <form onSubmit={submit} className="mt-8 space-y-4">
          <AuthField
            label="Work email"
            type="email"
            value={email}
            onChange={setEmail}
            placeholder="you@company.com"
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
          <AuthSubmit busy={busy}>Send reset link</AuthSubmit>
        </form>
        <p className="mt-6 text-center text-xs text-white/40">
          Remember your password?{" "}
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
