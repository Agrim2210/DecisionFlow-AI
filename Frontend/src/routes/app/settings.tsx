import { createFileRoute } from "@tanstack/react-router";
import {
  Building,
  Check,
  KeyRound,
  LoaderCircle,
  Lock,
  Save,
  Shield,
  Sparkles,
  User,
} from "lucide-react";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, readValue } from "../../lib/api";
import { useSession } from "../../lib/session";

export const Route = createFileRoute("/app/settings")({ component: SettingsPage });

type SettingsTab = "profile" | "password" | "workspace";

function SettingsPage() {
  const queryClient = useQueryClient();
  const { user, organization } = useSession();
  const [tab, setTab] = useState<SettingsTab>("profile");

  // Profile Form State
  const [name, setName] = useState(String(user?.name ?? ""));
  const [avatarUrl, setAvatarUrl] = useState(String(user?.avatar_url ?? ""));
  const [profileMsg, setProfileMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Password Form State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMsg, setPasswordMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Org Settings Query & Form State
  const orgQuery = useQuery({
    queryKey: ["org-settings"],
    queryFn: api.orgSettings,
    enabled: typeof window !== "undefined",
  });
  const orgData = orgQuery.data;
  const [orgName, setOrgName] = useState(String(organization?.name ?? ""));
  const [orgMsg, setOrgMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Profile Mutation
  const updateProfileMutation = useMutation({
    mutationFn: (body: { name?: string; avatar_url?: string }) => api.updateProfile(body),
    onSuccess: () => {
      setProfileMsg({ type: "success", text: "Profile updated successfully." });
      queryClient.invalidateQueries({ queryKey: ["auth-me"] });
    },
    onError: (err) => {
      setProfileMsg({
        type: "error",
        text: err instanceof ApiError ? err.message : "Failed to update profile.",
      });
    },
  });

  // Password Mutation
  const changePasswordMutation = useMutation({
    mutationFn: (body: { current_password: string; new_password: string }) =>
      api.changePassword(body),
    onSuccess: () => {
      setPasswordMsg({ type: "success", text: "Password changed successfully." });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    },
    onError: (err) => {
      setPasswordMsg({
        type: "error",
        text: err instanceof ApiError ? err.message : "Failed to change password.",
      });
    },
  });

  // Org Mutation
  const updateOrgMutation = useMutation({
    mutationFn: (body: { name?: string }) => api.updateOrgSettings(body),
    onSuccess: () => {
      setOrgMsg({ type: "success", text: "Workspace settings saved." });
      queryClient.invalidateQueries({ queryKey: ["org-settings"] });
    },
    onError: (err) => {
      setOrgMsg({
        type: "error",
        text: err instanceof ApiError ? err.message : "Failed to update workspace.",
      });
    },
  });

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMsg(null);
    updateProfileMutation.mutate({ name: name.trim(), avatar_url: avatarUrl.trim() || undefined });
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);
    if (newPassword.length < 8) {
      setPasswordMsg({ type: "error", text: "New password must be at least 8 characters." });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: "error", text: "New passwords do not match." });
      return;
    }
    changePasswordMutation.mutate({ current_password: currentPassword, new_password: newPassword });
  };

  const handleOrgSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setOrgMsg(null);
    updateOrgMutation.mutate({ name: orgName.trim() });
  };

  const isOwnerOrAdmin = ["owner", "admin"].includes(String(user?.role ?? "").toLowerCase());

  return (
    <div>
      <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
        <div>
          <p className="df-kicker">PREFERENCES & CONTROLS</p>
          <h1 className="mt-4 font-display text-4xl font-semibold tracking-[-.06em] sm:text-6xl">
            Settings &<br />
            <span className="text-white/45">security.</span>
          </h1>
          <p className="mt-5 max-w-lg text-sm leading-6 text-white/45">
            Manage your personal profile, security credentials, and workspace configuration.
          </p>
        </div>
      </div>

      <div className="mt-10 flex border-b border-white/[.08] gap-8">
        <button
          onClick={() => setTab("profile")}
          className={`flex items-center gap-2 pb-4 text-sm font-medium transition ${
            tab === "profile"
              ? "border-b-2 border-cyan-300 text-cyan-200"
              : "text-white/40 hover:text-white/80"
          }`}
        >
          <User size={16} /> Profile
        </button>
        <button
          onClick={() => setTab("password")}
          className={`flex items-center gap-2 pb-4 text-sm font-medium transition ${
            tab === "password"
              ? "border-b-2 border-cyan-300 text-cyan-200"
              : "text-white/40 hover:text-white/80"
          }`}
        >
          <Lock size={16} /> Password & Security
        </button>
        {isOwnerOrAdmin && (
          <button
            onClick={() => setTab("workspace")}
            className={`flex items-center gap-2 pb-4 text-sm font-medium transition ${
              tab === "workspace"
                ? "border-b-2 border-cyan-300 text-cyan-200"
                : "text-white/40 hover:text-white/80"
            }`}
          >
            <Building size={16} /> Workspace Settings
          </button>
        )}
      </div>

      <div className="mt-8 max-w-2xl">
        {/* Profile Tab */}
        {tab === "profile" && (
          <form onSubmit={handleProfileSubmit} className="df-app-card rounded-[26px] p-6 sm:p-8 space-y-6">
            <div>
              <h2 className="font-display text-xl font-semibold text-white">Your Profile</h2>
              <p className="mt-1 text-xs text-white/40">Update your personal account details.</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-white/60 mb-2">Display Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your full name"
                  className="df-app-input w-full rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/25"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-white/60 mb-2">Email Address</label>
                <input
                  type="email"
                  disabled
                  value={String(user?.email ?? "")}
                  className="df-app-input w-full rounded-xl px-4 py-3 text-sm text-white/40 bg-white/[.02] cursor-not-allowed"
                />
                <span className="mt-1 text-[11px] text-white/30">Email cannot be changed directly.</span>
              </div>

              <div>
                <label className="block text-xs font-medium text-white/60 mb-2">Role in Workspace</label>
                <div className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[.03] px-3.5 py-2 text-xs text-cyan-200 capitalize">
                  <Shield size={14} /> {String(user?.role ?? "member")}
                </div>
              </div>
            </div>

            {profileMsg && (
              <p
                className={`rounded-xl border px-3.5 py-2.5 text-xs ${
                  profileMsg.type === "success"
                    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
                    : "border-rose-500/20 bg-rose-500/10 text-rose-300"
                }`}
              >
                {profileMsg.text}
              </p>
            )}

            <button
              type="submit"
              disabled={updateProfileMutation.isPending}
              className="df-pill-button flex items-center gap-2 text-xs"
            >
              {updateProfileMutation.isPending ? (
                <>
                  <LoaderCircle size={14} className="animate-spin" /> Saving…
                </>
              ) : (
                <>
                  <Save size={14} /> Save Profile
                </>
              )}
            </button>
          </form>
        )}

        {/* Password Tab */}
        {tab === "password" && (
          <form onSubmit={handlePasswordSubmit} className="df-app-card rounded-[26px] p-6 sm:p-8 space-y-6">
            <div>
              <h2 className="font-display text-xl font-semibold text-white">Change Password</h2>
              <p className="mt-1 text-xs text-white/40">Ensure your account is using a secure, strong password.</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-white/60 mb-2">Current Password</label>
                <input
                  type="password"
                  required
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••"
                  className="df-app-input w-full rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/25"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-white/60 mb-2">New Password</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  className="df-app-input w-full rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/25"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-white/60 mb-2">Confirm New Password</label>
                <input
                  type="password"
                  required
                  minLength={8}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="df-app-input w-full rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/25"
                />
              </div>
            </div>

            {passwordMsg && (
              <p
                className={`rounded-xl border px-3.5 py-2.5 text-xs ${
                  passwordMsg.type === "success"
                    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
                    : "border-rose-500/20 bg-rose-500/10 text-rose-300"
                }`}
              >
                {passwordMsg.text}
              </p>
            )}

            <button
              type="submit"
              disabled={changePasswordMutation.isPending}
              className="df-pill-button flex items-center gap-2 text-xs"
            >
              {changePasswordMutation.isPending ? (
                <>
                  <LoaderCircle size={14} className="animate-spin" /> Updating…
                </>
              ) : (
                <>
                  <KeyRound size={14} /> Update Password
                </>
              )}
            </button>
          </form>
        )}

        {/* Workspace Settings Tab */}
        {tab === "workspace" && isOwnerOrAdmin && (
          <form onSubmit={handleOrgSubmit} className="df-app-card rounded-[26px] p-6 sm:p-8 space-y-6">
            <div>
              <h2 className="font-display text-xl font-semibold text-white">Workspace Configuration</h2>
              <p className="mt-1 text-xs text-white/40">Manage global workspace details for your organization.</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-white/60 mb-2">Workspace Name</label>
                <input
                  type="text"
                  required
                  value={orgName}
                  onChange={(e) => setOrgName(e.target.value)}
                  placeholder="Workspace name"
                  className="df-app-input w-full rounded-xl px-4 py-3 text-sm text-white placeholder:text-white/25"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-white/60 mb-2">Workspace Slug</label>
                <input
                  type="text"
                  disabled
                  value={readValue(orgData, ["slug"], String(organization?.slug ?? ""))}
                  className="df-app-input w-full rounded-xl px-4 py-3 text-sm text-white/40 bg-white/[.02] cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-white/60 mb-2">Current Plan</label>
                <div className="inline-flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/10 px-3.5 py-2 text-xs font-semibold text-cyan-200 capitalize">
                  <Sparkles size={14} /> {readValue(orgData, ["plan"], "pro")}
                </div>
              </div>
            </div>

            {orgMsg && (
              <p
                className={`rounded-xl border px-3.5 py-2.5 text-xs ${
                  orgMsg.type === "success"
                    ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
                    : "border-rose-500/20 bg-rose-500/10 text-rose-300"
                }`}
              >
                {orgMsg.text}
              </p>
            )}

            <button
              type="submit"
              disabled={updateOrgMutation.isPending}
              className="df-pill-button flex items-center gap-2 text-xs"
            >
              {updateOrgMutation.isPending ? (
                <>
                  <LoaderCircle size={14} className="animate-spin" /> Saving…
                </>
              ) : (
                <>
                  <Save size={14} /> Save Workspace Settings
                </>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
