const DECISIONFLOW_VIDEO_SRC =
  "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_115001_bcdaa3b4-03de-47e7-ad63-ae3e392c32d4.mp4";

import { createFileRoute, Link, Outlet, useLocation, useNavigate } from "@tanstack/react-router";
import {
  Activity,
  Bell,
  ClipboardCheck,
  FileAudio,
  LayoutDashboard,
  LogOut,
  Menu,
  Search,
  Settings2,
  Users,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useSession } from "../lib/session";
import { api, readArray, readNumber, readValue, type ApiRecord } from "../lib/api";
import { useQuery } from "@tanstack/react-query";

export const Route = createFileRoute("/app")({ component: AppShell });

function AppShell() {
  const { user, loading, signOut } = useSession();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  // Topbar search state
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  const unreadQuery = useQuery({
    queryKey: ["notifications-unread"],
    queryFn: api.notificationsUnread,
    enabled: Boolean(user),
    staleTime: 15_000,
  });

  const searchResultsQuery = useQuery({
    queryKey: ["topbar-search", searchQuery],
    queryFn: async () => {
      const response = await api.search(searchQuery, {
        mode: "hybrid",
        limit: 5,
      });
      return readArray(response).slice(0, 5);
    },
    enabled: searchQuery.trim().length > 2,
    staleTime: 30_000,
  });

  // Click outside listener for search popup
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsSearchOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (!loading && !user) navigate({ to: "/login" });
  }, [loading, navigate, user]);

  if (loading || !user)
    return (
      <div className="df-app-shell flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="df-brand-orb mx-auto animate-pulse">
            <span className="text-xs">◌</span>
          </div>
          <p className="mt-4 font-mono text-[10px] uppercase tracking-[.3em] text-white/40">
            Restoring your flow
          </p>
        </div>
      </div>
    );

  const displayName = String(user.name ?? user.full_name ?? user.email ?? "Workspace");
  const initials = displayName
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  const unread = readNumber(unreadQuery.data as Record<string, unknown> | undefined, [
    "unread_count",
    "count",
  ]);

  const isOwnerOrAdmin = ["owner", "admin"].includes(String(user?.role ?? "").toLowerCase());

  const navItems = [
    { to: "/app", label: "Overview", icon: LayoutDashboard },
    { to: "/app/meetings", label: "Meetings", icon: FileAudio },
    { to: "/app/tasks", label: "My tasks", icon: ClipboardCheck },
    { to: "/app/people", label: "People & roles", icon: Users },
    { to: "/app/notifications", label: "Notifications", icon: Bell, badge: unread > 0 ? unread : undefined },
    ...(isOwnerOrAdmin ? [{ to: "/app/audit", label: "Audit log", icon: Activity }] : []),
    { to: "/app/settings", label: "Settings", icon: Settings2 },
  ];

  return (
    <div className="df-app-shell flex min-h-screen text-white">
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

      <aside
        className={`${
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        } df-sidebar fixed inset-y-0 left-0 z-40 flex w-[260px] flex-col px-4 py-5 transition-transform lg:static`}
      >
        <div className="flex items-center justify-between px-2">
          <Link to="/" className="flex items-center gap-3">
            <span className="df-brand-orb">
              <span className="font-display text-xs font-bold">D</span>
            </span>
            <span className="font-display text-sm font-semibold tracking-[.13em]">
              DECISIONFLOW <span className="text-cyan-200">AI</span>
            </span>
          </Link>
          <button
            className="text-white/45 lg:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Close menu"
          >
            <X size={18} />
          </button>
        </div>

        <div className="mt-9 rounded-2xl border border-white/10 bg-white/[.035] p-3">
          <p className="px-2 text-[10px] uppercase tracking-[.22em] text-white/35">Workspace</p>
          <div className="mt-3 flex items-center gap-3">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-cyan-200/10 text-xs font-semibold text-cyan-100">
              {initials || "DF"}
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-white/85">{displayName}</p>
              <p className="truncate text-xs text-white/35">
                {String(user.email ?? "Personal workspace")}
              </p>
            </div>
          </div>
        </div>

        <nav className="mt-8 space-y-1">
          {navItems.map((item) => (
            <NavItem
              key={item.to}
              to={item.to}
              label={item.label}
              icon={item.icon}
              current={location.pathname === item.to}
              badge={item.badge}
              onClick={() => setMobileOpen(false)}
            />
          ))}
        </nav>

        <div className="mt-auto">
          <div className="mb-3 rounded-2xl border border-cyan-200/10 bg-cyan-200/[.04] p-4">
            <p className="text-xs font-medium text-cyan-100/85">Make the room lighter.</p>
            <p className="mt-2 text-xs leading-5 text-white/38">
              Upload your next transcript and let the follow-through take shape.
            </p>
          </div>
          <button
            onClick={async () => {
              await signOut();
              navigate({ to: "/" });
            }}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-sm text-white/45 transition hover:bg-white/[.05] hover:text-white"
          >
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </aside>

      {mobileOpen && (
        <button
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-label="Close navigation overlay"
        />
      )}

      <main className="df-app-content min-w-0 flex-1 overflow-x-hidden">
        <header className="df-app-topbar flex h-[76px] items-center justify-between border-b border-white/[.08] px-5 sm:px-8">
          <div className="flex items-center gap-3">
            <button
              className="text-white/55 lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <Menu size={21} />
            </button>

            {/* Live Search Bar */}
            <div ref={searchRef} className="relative hidden sm:block">
              <Search
                className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30"
                size={14}
              />
              <input
                value={searchQuery}
                onFocus={() => setIsSearchOpen(true)}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setIsSearchOpen(true);
                }}
                placeholder="Search your flow…"
                className="df-app-input w-72 rounded-xl py-2 pl-9 pr-3 text-xs text-white placeholder:text-white/25 focus:w-80 transition-all"
              />

              {/* Autocomplete / Search Dropdown */}
              {isSearchOpen && searchQuery.trim().length > 2 && (
                <div className="absolute left-0 top-full mt-2 w-96 rounded-2xl border border-white/10 bg-[#0d1424] p-3 shadow-2xl backdrop-blur-xl z-50">
                  <p className="px-2 text-[10px] uppercase tracking-wider text-white/30">
                    Results for "{searchQuery}"
                  </p>
                  <div className="mt-2 space-y-1 max-h-60 overflow-y-auto">
                    {searchResultsQuery.isLoading ? (
                      <p className="px-2 py-3 text-xs text-white/40">Searching your workspace…</p>
                    ) : readArray(searchResultsQuery.data).length ? (
                      readArray(searchResultsQuery.data).map((item, idx) => (
                        <div
                          key={idx}
                          className="rounded-xl p-2.5 hover:bg-white/5 transition cursor-pointer"
                          onClick={() => {
                            setIsSearchOpen(false);
                            const type = readValue(item, ["source_type"]);
                            if (type === "meeting") navigate({ to: "/app/meetings" });
                            else if (type === "action_item" || type === "task") navigate({ to: "/app/tasks" });
                            else navigate({ to: "/app" });
                          }}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] uppercase font-semibold text-cyan-300">
                              {readValue(item, ["source_type"], "signal")}
                            </span>
                          </div>
                          <p className="mt-1 text-xs text-white/80 line-clamp-1">
                            {readValue(item, ["title", "content"], "Untitled")}
                          </p>
                        </div>
                      ))
                    ) : (
                      <p className="px-2 py-3 text-xs text-white/40">No matching signals found.</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Notification Bell with direct link */}
            <Link
              to="/app/notifications"
              className="relative text-white/45 transition hover:text-white"
              aria-label="Notifications"
            >
              <Bell size={18} />
              {unread > 0 && (
                <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_10px_rgba(160,240,244,.85)]" />
              )}
            </Link>

            <div className="h-5 w-px bg-white/10" />

            <Link to="/app/settings" className="flex items-center gap-2 hover:opacity-80 transition">
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/15 bg-white/[.07] text-[10px] font-semibold text-cyan-100">
                {initials || "DF"}
              </span>
              <span className="hidden text-xs text-white/60 sm:block">
                {displayName.split(" ")[0]}
              </span>
            </Link>
          </div>
        </header>

        <div className="mx-auto max-w-[1400px] p-5 sm:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

function NavItem({
  to,
  label,
  icon: Icon,
  current,
  badge,
  onClick,
}: {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  current: boolean;
  badge?: number;
  onClick?: () => void;
}) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${
        current
          ? "bg-cyan-200/10 text-cyan-100 font-medium"
          : "text-white/45 hover:bg-white/[.05] hover:text-white/80"
      }`}
    >
      <Icon size={16} />
      <span>{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="ml-auto rounded-full bg-cyan-400/20 px-2 py-0.5 text-[10px] font-semibold text-cyan-200">
          {badge}
        </span>
      )}
    </Link>
  );
}
