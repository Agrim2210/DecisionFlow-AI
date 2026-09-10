import { createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Clock,
  Copy,
  Crown,
  KeyRound,
  LoaderCircle,
  Mail,
  Plus,
  RefreshCw,
  Search,
  Send,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  UserCheck,
  UserPlus,
  UserRound,
  Users,
  X,
} from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, readArray, readValue, type ApiRecord } from "../../lib/api";
import { useSession } from "../../lib/session";

export const Route = createFileRoute("/app/people")({ component: PeoplePage });

const roleFilters = ["all", "admin", "member", "viewer"];

function generateSecurePassword(length = 14): string {
  const chars = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%&*";
  let pass = "";
  for (let i = 0; i < length; i++) {
    pass += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return pass;
}

function PeoplePage() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useSession();
  const isClient = typeof window !== "undefined";

  const usersQuery = useQuery({
    queryKey: ["workspace-users"],
    queryFn: () => api.users({ limit: 100 }),
    enabled: isClient,
    refetchInterval: 15_000,
  });

  const pendingQuery = useQuery({
    queryKey: ["workspace-pending-users"],
    queryFn: () => api.pendingUsers(),
    enabled: isClient,
    refetchInterval: 15_000,
  });

  const [activeTab, setActiveTab] = useState<"members" | "pending">("members");
  const [roleFilter, setRoleFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [deactivateTarget, setDeactivateTarget] = useState<ApiRecord | null>(null);
  const [cancelPendingTarget, setCancelPendingTarget] = useState<ApiRecord | null>(null);
  const [resendingEmail, setResendingEmail] = useState<string | null>(null);

  const allUsers = readArray(usersQuery.data);
  const allPending = readArray(pendingQuery.data);

  const currentUserRole = String(
    currentUser ? currentUser["role"] ?? "member" : "member",
  ).toLowerCase();
  const isAdminOrOwner = ["admin", "owner"].includes(currentUserRole);

  const filteredUsers = useMemo(() => {
    return allUsers.filter((u) => {
      const role = String(u["role"] ?? "member").toLowerCase();
      if (roleFilter !== "all" && role !== roleFilter) return false;
      if (!search.trim()) return true;
      const query = search.toLowerCase();
      const name = String(u["name"] ?? "").toLowerCase();
      const email = String(u["email"] ?? "").toLowerCase();
      return name.includes(query) || email.includes(query);
    });
  }, [allUsers, roleFilter, search]);

  const filteredPending = useMemo(() => {
    return allPending.filter((p) => {
      const role = String(p["invited_role"] ?? p["role"] ?? "member").toLowerCase();
      if (roleFilter !== "all" && role !== roleFilter) return false;
      if (!search.trim()) return true;
      const query = search.toLowerCase();
      const name = String(p["name"] ?? "").toLowerCase();
      const email = String(p["email"] ?? "").toLowerCase();
      return name.includes(query) || email.includes(query);
    });
  }, [allPending, roleFilter, search]);

  const totalMembers = allUsers.length;
  const pendingCount = allPending.length;
  const adminCount = allUsers.filter((u) =>
    ["admin", "owner"].includes(String(u["role"] ?? "").toLowerCase()),
  ).length;

  const changeRoleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: "viewer" | "member" | "admin" }) =>
      api.changeUserRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace-users"] });
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (userId: string) => api.deactivateUser(userId),
    onSuccess: () => {
      setDeactivateTarget(null);
      queryClient.invalidateQueries({ queryKey: ["workspace-users"] });
    },
  });

  const cancelPendingMutation = useMutation({
    mutationFn: (pendingId: string) => api.cancelInvitation(pendingId),
    onSuccess: () => {
      setCancelPendingTarget(null);
      queryClient.invalidateQueries({ queryKey: ["workspace-pending-users"] });
    },
  });

  const handleResend = async (pendingUser: ApiRecord) => {
    const email = String(pendingUser["email"] ?? "");
    const name = String(pendingUser["name"] ?? "Teammate");
    const role = (pendingUser["invited_role"] ?? pendingUser["role"] ?? "member") as "viewer" | "member" | "admin";
    if (!email) return;

    setResendingEmail(email);
    try {
      await api.inviteUser({
        email,
        name,
        role,
        temp_password: generateSecurePassword(),
      });
      queryClient.invalidateQueries({ queryKey: ["workspace-pending-users"] });
    } finally {
      setResendingEmail(null);
    }
  };

  return (
    <div>
      {/* Top Header */}
      <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
        <div>
          <p className="df-kicker">WORKSPACE / PEOPLE & ROLES</p>
          <h1 className="mt-4 font-display text-4xl font-semibold tracking-[-.06em] sm:text-6xl">
            Team &
            <br />
            <span className="text-white/45">permissions.</span>
          </h1>
          <p className="mt-5 max-w-lg text-sm leading-6 text-white/45">
            Every voice, role, and promise in your workspace. Invite teammates and grant the right level of flow.
          </p>
        </div>

        {isAdminOrOwner && (
          <button
            onClick={() => setShowInviteModal(true)}
            className="df-pill-button inline-flex items-center gap-2 self-start md:self-auto"
          >
            <UserPlus size={16} />
            <span>Invite member</span>
          </button>
        )}
      </div>

      {/* Mini Stats */}
      <div className="mt-10 grid gap-3 sm:grid-cols-3">
        <MiniStat label="Active Members" value={String(totalMembers).padStart(2, "0")} />
        <MiniStat label="Pending Invites" value={String(pendingCount).padStart(2, "0")} cool />
        <MiniStat label="Admins & Owners" value={String(adminCount).padStart(2, "0")} warm />
      </div>

      {/* View Tabs & Filter Bar */}
      <div className="mt-8 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 rounded-2xl border border-white/10 bg-white/[.03] p-1">
            <button
              onClick={() => setActiveTab("members")}
              className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                activeTab === "members"
                  ? "bg-white/[.12] text-white shadow-sm"
                  : "text-white/40 hover:text-white/75"
              }`}
            >
              Active members ({totalMembers})
            </button>
            <button
              onClick={() => setActiveTab("pending")}
              className={`rounded-xl px-4 py-2 text-xs font-semibold transition ${
                activeTab === "pending"
                  ? "bg-cyan-400/20 text-cyan-200 shadow-sm"
                  : "text-white/40 hover:text-white/75"
              }`}
            >
              Pending invitations ({pendingCount})
            </button>
          </div>

          <div className="flex items-center gap-1 overflow-x-auto rounded-2xl border border-white/10 bg-white/[.03] p-1">
            {roleFilters.map((item) => (
              <button
                key={item}
                onClick={() => setRoleFilter(item)}
                className={`whitespace-nowrap rounded-xl px-3 py-2 text-xs capitalize transition ${
                  roleFilter === item
                    ? "bg-white/[.1] text-white"
                    : "text-white/40 hover:text-white/70"
                }`}
              >
                {item === "all" ? "All roles" : `${item}s`}
              </button>
            ))}
          </div>
        </div>

        <div className="relative min-w-[240px]">
          <Search size={14} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or email…"
            className="df-app-input w-full rounded-2xl py-2 pl-9 pr-4 text-xs text-white placeholder:text-white/30"
          />
        </div>
      </div>

      {/* Main Directory Card */}
      {activeTab === "members" ? (
        <section className="df-app-card mt-5 overflow-hidden rounded-[26px]">
          <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
            <span className="text-xs font-medium uppercase tracking-[.18em] text-white/40">
              Active Member Directory
            </span>
            <span className="text-xs text-white/35">
              {filteredUsers.length} {filteredUsers.length === 1 ? "person" : "people"} showing
            </span>
          </div>

          {usersQuery.isLoading && allUsers.length === 0 ? (
            <div className="flex items-center justify-center p-16 text-center text-sm text-white/40">
              <LoaderCircle size={20} className="mr-2 animate-spin text-cyan-200" />
              Loading workspace team…
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="p-16 text-center">
              <Users size={32} className="mx-auto text-white/20" />
              <p className="mt-3 text-sm font-medium text-white/70">No members matched your filter</p>
              <p className="mt-1 text-xs text-white/35">Try adjusting your search terms or filters.</p>
            </div>
          ) : (
            <div className="divide-y divide-white/[.07]">
              {filteredUsers.map((member) => {
                const id = String(member["id"] ?? "");
                const name = String(member["name"] ?? member["full_name"] ?? "Workspace Member");
                const email = String(member["email"] ?? "");
                const role = String(member["role"] ?? "member").toLowerCase();
                const isOwner = role === "owner";
                const isSelf = String(currentUser?.["id"] ?? "") === id;
                const isVerified = member["is_email_verified"] !== false;
                const isActive = member["is_active"] !== false;
                const reliability = Number(member["reliability_score"] ?? 0);
                const initials =
                  name
                    .split(" ")
                    .map((part) => part[0])
                    .filter(Boolean)
                    .join("")
                    .slice(0, 2)
                    .toUpperCase() || "DF";

                return (
                  <div
                    key={id}
                    className="flex flex-col justify-between gap-4 p-5 transition hover:bg-white/[.015] sm:flex-row sm:items-center sm:px-6"
                  >
                    {/* Avatar & Member Details */}
                    <div className="flex items-center gap-4">
                      <div className="relative">
                        <span className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/[.04] font-display text-sm font-semibold text-cyan-100 shadow-inner">
                          {initials}
                        </span>
                        <span
                          className={`absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[#091118] ${
                            isActive && isVerified ? "bg-emerald-400" : "bg-amber-400"
                          }`}
                          title={isActive && isVerified ? "Active & Verified" : "Pending Verification"}
                        />
                      </div>

                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-sm font-semibold text-white/90">{name}</span>
                          {isSelf && (
                            <span className="rounded-md border border-cyan-400/20 bg-cyan-400/10 px-1.5 py-0.5 text-[10px] font-medium text-cyan-200">
                              You
                            </span>
                          )}
                        </div>
                        <p className="truncate text-xs text-white/40">{email}</p>
                      </div>
                    </div>

                    {/* Badges & Role Controls */}
                    <div className="flex flex-wrap items-center gap-3 self-end sm:self-center">
                      {reliability > 0 && (
                        <span className="hidden items-center gap-1 rounded-xl border border-white/10 bg-white/[.02] px-2.5 py-1 text-xs text-white/50 lg:inline-flex">
                          <CheckCircle2 size={12} className="text-cyan-200/70" />
                          {Math.round(reliability)}% score
                        </span>
                      )}

                      {/* Role Selector or Badge */}
                      {isAdminOrOwner && !isOwner && !isSelf ? (
                        <select
                          value={role}
                          disabled={changeRoleMutation.isPending}
                          onChange={(e) => {
                            const newRole = e.target.value as "viewer" | "member" | "admin";
                            changeRoleMutation.mutate({ userId: id, role: newRole });
                          }}
                          className={`cursor-pointer rounded-xl border px-3 py-1.5 text-xs font-semibold transition focus:outline-none ${getRoleBadgeStyle(
                            role,
                          )}`}
                        >
                          <option value="viewer" className="bg-[#0c141d] text-white">
                            Viewer
                          </option>
                          <option value="member" className="bg-[#0c141d] text-white">
                            Member
                          </option>
                          <option value="admin" className="bg-[#0c141d] text-white">
                            Admin
                          </option>
                        </select>
                      ) : (
                        <RoleBadge role={role} />
                      )}

                      {/* Deactivate Option */}
                      {isAdminOrOwner && !isOwner && !isSelf && (
                        <button
                          onClick={() => setDeactivateTarget(member)}
                          className="rounded-xl p-1.5 text-white/30 transition hover:bg-rose-500/10 hover:text-rose-300"
                          title="Deactivate member"
                        >
                          <Trash2 size={15} />
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      ) : (
        /* Pending Invitations Section */
        <section className="df-app-card mt-5 overflow-hidden rounded-[26px]">
          <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
            <span className="text-xs font-medium uppercase tracking-[.18em] text-cyan-200/70">
              Pending Workspace Invitations
            </span>
            <span className="text-xs text-white/35">
              {filteredPending.length} pending
            </span>
          </div>

          {pendingQuery.isLoading && allPending.length === 0 ? (
            <div className="flex items-center justify-center p-16 text-center text-sm text-white/40">
              <LoaderCircle size={20} className="mr-2 animate-spin text-cyan-200" />
              Loading pending invitations…
            </div>
          ) : filteredPending.length === 0 ? (
            <div className="p-16 text-center">
              <Mail size={32} className="mx-auto text-white/20" />
              <p className="mt-3 text-sm font-medium text-white/70">No pending invitations</p>
              <p className="mt-1 text-xs text-white/35">
                All invited teammates have verified and activated their workspace access.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-white/[.07]">
              {filteredPending.map((invitation) => {
                const id = String(invitation["id"] ?? "");
                const name = String(invitation["name"] ?? "Teammate");
                const email = String(invitation["email"] ?? "");
                const role = String(invitation["invited_role"] ?? invitation["role"] ?? "member").toLowerCase();
                const isBusy = resendingEmail === email;

                return (
                  <div
                    key={id}
                    className="flex flex-col justify-between gap-4 p-5 transition hover:bg-white/[.015] sm:flex-row sm:items-center sm:px-6"
                  >
                    <div className="flex items-center gap-4">
                      <div className="relative">
                        <span className="flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-400/20 bg-cyan-400/5 font-display text-sm font-semibold text-cyan-200 shadow-inner">
                          <Mail size={18} />
                        </span>
                        <span
                          className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[#091118] bg-amber-400 animate-pulse"
                          title="Pending Verification"
                        />
                      </div>

                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="truncate text-sm font-semibold text-white/90">{name}</span>
                          <span className="rounded-md border border-amber-400/30 bg-amber-400/10 px-2 py-0.5 text-[10px] font-medium text-amber-200">
                            Pending Verification (72h)
                          </span>
                        </div>
                        <p className="truncate text-xs text-white/40">{email}</p>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 self-end sm:self-center">
                      <RoleBadge role={role} />

                      {isAdminOrOwner && (
                        <>
                          <button
                            onClick={() => handleResend(invitation)}
                            disabled={isBusy}
                            className="inline-flex items-center gap-1.5 rounded-xl border border-cyan-400/30 bg-cyan-400/10 px-3 py-1.5 text-xs font-semibold text-cyan-200 transition hover:bg-cyan-400/20 disabled:opacity-50"
                            title="Resend invitation email with fresh 72-hour verification link"
                          >
                            {isBusy ? (
                              <LoaderCircle size={13} className="animate-spin" />
                            ) : (
                              <Send size={13} />
                            )}
                            <span>{isBusy ? "Resending…" : "Resend Invite"}</span>
                          </button>

                          <button
                            onClick={() => setCancelPendingTarget(invitation)}
                            className="rounded-xl p-1.5 text-white/30 transition hover:bg-rose-500/10 hover:text-rose-300"
                            title="Cancel / revoke invitation"
                          >
                            <Trash2 size={15} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      )}

      {/* Invite Member Modal */}
      {showInviteModal && (
        <InviteModal
          onClose={() => setShowInviteModal(false)}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["workspace-users"] });
            queryClient.invalidateQueries({ queryKey: ["workspace-pending-users"] });
          }}
        />
      )}

      {/* Deactivate User Modal */}
      {deactivateTarget && (
        <DeactivateModal
          member={deactivateTarget}
          busy={deactivateMutation.isPending}
          onClose={() => setDeactivateTarget(null)}
          onConfirm={() => {
            const id = String(deactivateTarget["id"] ?? "");
            if (id) deactivateMutation.mutate(id);
          }}
        />
      )}

      {/* Cancel Pending Invitation Modal */}
      {cancelPendingTarget && (
        <CancelInvitationModal
          invitation={cancelPendingTarget}
          busy={cancelPendingMutation.isPending}
          onClose={() => setCancelPendingTarget(null)}
          onConfirm={() => {
            const id = String(cancelPendingTarget["id"] ?? "");
            if (id) cancelPendingMutation.mutate(id);
          }}
        />
      )}
    </div>
  );
}

function MiniStat({
  label,
  value,
  cool,
  warm,
}: {
  label: string;
  value: string;
  cool?: boolean;
  warm?: boolean;
}) {
  return (
    <div className="df-app-card rounded-[22px] p-5">
      <p className="text-[10px] uppercase tracking-[.22em] text-white/35">{label}</p>
      <div className="mt-3 flex items-baseline gap-2">
        <span
          className={`font-display text-4xl font-semibold tracking-tight ${
            cool ? "text-cyan-200" : warm ? "text-amber-200" : "text-white"
          }`}
        >
          {value}
        </span>
      </div>
    </div>
  );
}

function getRoleBadgeStyle(role: string): string {
  switch (role) {
    case "owner":
      return "border-amber-400/30 bg-amber-400/10 text-amber-200";
    case "admin":
      return "border-cyan-400/30 bg-cyan-400/10 text-cyan-200";
    case "member":
      return "border-blue-400/30 bg-blue-400/10 text-blue-200";
    case "viewer":
    default:
      return "border-white/10 bg-white/5 text-white/60";
  }
}

function RoleBadge({ role }: { role: string }) {
  const isOwner = role === "owner";
  const isAdmin = role === "admin";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-1 text-xs font-semibold capitalize ${getRoleBadgeStyle(
        role,
      )}`}
    >
      {isOwner && <Crown size={12} className="text-amber-300" />}
      {isAdmin && <ShieldCheck size={12} className="text-cyan-300" />}
      {role}
    </span>
  );
}

function InviteModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"viewer" | "member" | "admin">("member");
  const [tempPassword, setTempPassword] = useState(() => generateSecurePassword());
  const [copiedPass, setCopiedPass] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [invitationResult, setInvitationResult] = useState<{
    message: string;
    verification_url?: string;
  } | null>(null);

  const inviteMutation = useMutation({
    mutationFn: () =>
      api.inviteUser({
        name: name.trim(),
        email: email.trim().toLowerCase(),
        role,
        temp_password: tempPassword,
      }),
    onSuccess: (res) => {
      setInvitationResult(res);
      onSuccess();
    },
    onError: (err: any) => {
      setError(err?.message || "Failed to send invitation. Please check the inputs.");
    },
  });

  const handleCopyPassword = () => {
    navigator.clipboard.writeText(tempPassword);
    setCopiedPass(true);
    setTimeout(() => setCopiedPass(false), 2000);
  };

  const handleCopyLink = () => {
    if (invitationResult?.verification_url) {
      navigator.clipboard.writeText(invitationResult.verification_url);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2500);
    }
  };

  const handleRegeneratePassword = () => {
    setTempPassword(generateSecurePassword());
    setCopiedPass(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter the member's full name.");
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      setError("Please enter a valid work email address.");
      return;
    }
    if (tempPassword.length < 8) {
      setError("Temporary password must be at least 8 characters.");
      return;
    }
    setError(null);
    inviteMutation.mutate();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-md">
      <div className="df-app-card w-full max-w-lg rounded-[28px] p-6 sm:p-8 shadow-2xl">
        <div className="flex items-center justify-between">
          <div>
            <p className="df-kicker">WORKSPACE ACCESS</p>
            <h2 className="mt-1 font-display text-2xl font-semibold text-white">Invite new teammate</h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-white/40 transition hover:bg-white/10 hover:text-white"
          >
            <X size={18} />
          </button>
        </div>

        {invitationResult ? (
          <div className="mt-6 space-y-4">
            <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-5 text-center">
              <CheckCircle2 size={32} className="mx-auto text-emerald-300" />
              <p className="mt-3 text-sm font-semibold text-emerald-200">Invitation Dispatched (Valid for 72h)</p>
              <p className="mt-1 text-xs text-emerald-300/70">{invitationResult.message}</p>
            </div>

            {invitationResult.verification_url && (
              <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold text-cyan-200">Direct Invitation Link</p>
                  <button
                    type="button"
                    onClick={handleCopyLink}
                    className="inline-flex items-center gap-1 rounded-xl bg-cyan-400/20 px-3 py-1 text-xs font-semibold text-cyan-100 hover:bg-cyan-400/30"
                  >
                    {copiedLink ? <Check size={13} /> : <Copy size={13} />}
                    <span>{copiedLink ? "Copied!" : "Copy Link"}</span>
                  </button>
                </div>
                <p className="mt-2 truncate font-mono text-[11px] text-white/40">
                  {invitationResult.verification_url}
                </p>
                <p className="mt-1 text-[10px] text-white/30">
                  Share this link directly on Slack / WhatsApp if email delivery takes time.
                </p>
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={onClose}
                className="df-pill-button px-6 py-2.5 text-xs font-semibold"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {/* Full Name */}
            <div>
              <label className="block text-xs font-medium text-white/70">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Sarah Connor"
                required
                className="df-app-input mt-1.5 w-full rounded-2xl px-4 py-2.5 text-sm text-white placeholder:text-white/25"
              />
            </div>

            {/* Email Address */}
            <div>
              <label className="block text-xs font-medium text-white/70">Work Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="sarah@company.com"
                required
                className="df-app-input mt-1.5 w-full rounded-2xl px-4 py-2.5 text-sm text-white placeholder:text-white/25"
              />
            </div>

            {/* Role Selection */}
            <div>
              <label className="block text-xs font-medium text-white/70">Permission Role</label>
              <div className="mt-1.5 grid grid-cols-3 gap-2">
                {(["viewer", "member", "admin"] as const).map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRole(r)}
                    className={`flex flex-col items-center justify-center rounded-2xl border p-3 text-center transition ${
                      role === r
                        ? "border-cyan-400/50 bg-cyan-400/10 text-white shadow-inner"
                        : "border-white/10 bg-white/[.02] text-white/50 hover:bg-white/[.04] hover:text-white/80"
                    }`}
                  >
                    <span className="text-xs font-semibold capitalize">{r}</span>
                    <span className="mt-0.5 text-[10px] text-white/35">
                      {r === "admin"
                        ? "Manage workspace"
                        : r === "member"
                        ? "Upload & assign"
                        : "View only"}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Initial Password */}
            <div>
              <div className="flex items-center justify-between">
                <label className="block text-xs font-medium text-white/70">Temporary Initial Password</label>
                <button
                  type="button"
                  onClick={handleRegeneratePassword}
                  className="inline-flex items-center gap-1 text-[11px] text-cyan-300 hover:text-cyan-200"
                >
                  <RefreshCw size={11} /> Regenerate
                </button>
              </div>
              <div className="relative mt-1.5">
                <input
                  type="text"
                  value={tempPassword}
                  onChange={(e) => setTempPassword(e.target.value)}
                  required
                  className="df-app-input w-full rounded-2xl py-2.5 pl-4 pr-12 font-mono text-xs text-white"
                />
                <button
                  type="button"
                  onClick={handleCopyPassword}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-xl p-1.5 text-white/40 transition hover:bg-white/10 hover:text-white"
                  title="Copy password"
                >
                  {copiedPass ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                </button>
              </div>
              <p className="mt-1 text-[11px] text-white/35">
                The member can replace this password with their own after verifying their email (72-hour validity).
              </p>
            </div>

            {error && <p className="text-xs text-rose-300">{error}</p>}

            {/* Actions */}
            <div className="mt-6 flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-full border border-white/15 px-5 py-2.5 text-xs font-semibold text-white/70 transition hover:bg-white/5 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={inviteMutation.isPending}
                className="df-pill-button inline-flex items-center gap-2 text-xs font-semibold disabled:opacity-40"
              >
                {inviteMutation.isPending ? (
                  <>
                    <LoaderCircle size={14} className="animate-spin" />
                    Sending Invite…
                  </>
                ) : (
                  <>
                    <Mail size={14} />
                    Send Workspace Invite
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

function DeactivateModal({
  member,
  busy,
  onClose,
  onConfirm,
}: {
  member: ApiRecord;
  busy: boolean;
  onClose: () => void;
  onConfirm: () => void;
}) {
  const name = String(member["name"] ?? "this member");
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-md">
      <div className="df-app-card w-full max-w-sm rounded-[26px] p-6 shadow-2xl">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-rose-500/20 bg-rose-500/10 text-rose-300">
          <AlertTriangle size={24} />
        </div>
        <h3 className="mt-4 font-display text-lg font-semibold text-white">Deactivate Member?</h3>
        <p className="mt-2 text-xs leading-5 text-white/50">
          Are you sure you want to deactivate <strong className="text-white/80">{name}</strong>? They will immediately lose access to this workspace.
        </p>

        <div className="mt-6 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-full border border-white/15 px-4 py-2 text-xs font-semibold text-white/70 transition hover:bg-white/5"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="rounded-full bg-rose-500 px-4 py-2 text-xs font-semibold text-white transition hover:bg-rose-600 disabled:opacity-40"
          >
            {busy ? "Deactivating…" : "Deactivate"}
          </button>
        </div>
      </div>
    </div>
  );
}

function CancelInvitationModal({
  invitation,
  busy,
  onClose,
  onConfirm,
}: {
  invitation: ApiRecord;
  busy: boolean;
  onClose: () => void;
  onConfirm: () => void;
}) {
  const email = String(invitation["email"] ?? "this email");
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-md">
      <div className="df-app-card w-full max-w-sm rounded-[26px] p-6 shadow-2xl">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-amber-500/20 bg-amber-500/10 text-amber-300">
          <AlertTriangle size={24} />
        </div>
        <h3 className="mt-4 font-display text-lg font-semibold text-white">Revoke Invitation?</h3>
        <p className="mt-2 text-xs leading-5 text-white/50">
          Are you sure you want to cancel the pending invitation for <strong className="text-white/80">{email}</strong>? The invitation link will be invalidated.
        </p>

        <div className="mt-6 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-full border border-white/15 px-4 py-2 text-xs font-semibold text-white/70 transition hover:bg-white/5"
          >
            Keep Invite
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="rounded-full bg-amber-500 px-4 py-2 text-xs font-semibold text-white transition hover:bg-amber-600 disabled:opacity-40"
          >
            {busy ? "Revoking…" : "Revoke Invitation"}
          </button>
        </div>
      </div>
    </div>
  );
}
