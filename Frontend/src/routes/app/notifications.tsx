import { createFileRoute } from "@tanstack/react-router";
import {
  Bell,
  Check,
  CheckCheck,
  Clock,
  Filter,
  Inbox,
  LoaderCircle,
  Sparkles,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, readArray, readNumber, readValue, type ApiRecord } from "../../lib/api";

export const Route = createFileRoute("/app/notifications")({ component: NotificationsPage });

function NotificationsPage() {
  const queryClient = useQueryClient();
  const [unreadOnly, setUnreadOnly] = useState(false);

  const notificationsQuery = useQuery({
    queryKey: ["notifications-list", unreadOnly],
    queryFn: () => api.notifications({ unread_only: unreadOnly, limit: 50 }),
    enabled: typeof window !== "undefined",
    refetchInterval: 15_000,
  });

  const unreadCountQuery = useQuery({
    queryKey: ["notifications-unread"],
    queryFn: api.notificationsUnread,
    enabled: typeof window !== "undefined",
  });

  const rawNotifications = readArray(notificationsQuery.data);
  const unreadCount = readNumber(unreadCountQuery.data as ApiRecord | undefined, [
    "unread_count",
    "count",
  ]);

  const markReadMutation = useMutation({
    mutationFn: (id: string) => api.markNotificationRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications-list"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread"] });
    },
  });

  const markAllMutation = useMutation({
    mutationFn: () => api.markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications-list"] });
      queryClient.invalidateQueries({ queryKey: ["notifications-unread"] });
    },
  });

  return (
    <div>
      <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
        <div>
          <p className="df-kicker">UPDATES & ALERTS / INBOX</p>
          <h1 className="mt-4 font-display text-4xl font-semibold tracking-[-.06em] sm:text-6xl">
            Signal,<br />
            <span className="text-white/45">not noise.</span>
          </h1>
          <p className="mt-5 max-w-lg text-sm leading-6 text-white/45">
            Real-time updates on assignments, deadline risks, decision reviews, and workspace mentions.
          </p>
        </div>

        {unreadCount > 0 && (
          <button
            onClick={() => markAllMutation.mutate()}
            disabled={markAllMutation.isPending}
            className="df-pill-button flex items-center gap-2 self-start md:self-auto text-xs"
          >
            <CheckCheck size={15} /> Mark all read
          </button>
        )}
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-1 rounded-2xl border border-white/10 bg-white/[.03] p-1">
          <button
            onClick={() => setUnreadOnly(false)}
            className={`rounded-xl px-4 py-2 text-xs transition ${
              !unreadOnly ? "bg-white/[.1] text-white" : "text-white/40 hover:text-white/70"
            }`}
          >
            All updates
          </button>
          <button
            onClick={() => setUnreadOnly(true)}
            className={`rounded-xl px-4 py-2 text-xs transition flex items-center gap-1.5 ${
              unreadOnly ? "bg-white/[.1] text-white" : "text-white/40 hover:text-white/70"
            }`}
          >
            Unread
            {unreadCount > 0 && (
              <span className="rounded-full bg-cyan-400/20 text-cyan-200 px-1.5 py-0.2 text-[10px] font-semibold">
                {unreadCount}
              </span>
            )}
          </button>
        </div>

        <span className="inline-flex items-center gap-2 text-xs text-white/35">
          <Bell size={14} /> {rawNotifications.length} updates
        </span>
      </div>

      <section className="df-app-card mt-5 overflow-hidden rounded-[26px]">
        <div className="divide-y divide-white/[.07]">
          {notificationsQuery.isLoading ? (
            <div className="flex items-center justify-center gap-2 px-6 py-16 text-sm text-white/40">
              <LoaderCircle size={16} className="animate-spin" /> Loading your inbox…
            </div>
          ) : rawNotifications.length ? (
            rawNotifications.map((notification) => {
              const id = readValue(notification, ["id", "notification_id"]);
              const subject = readValue(notification, ["subject", "title"], "Notification");
              const body = readValue(notification, ["body", "message", "content"], "");
              const eventType = readValue(notification, ["event_type", "type"], "alert");
              const isRead = notification["is_read"] === true;
              const dateStr = readValue(notification, ["created_at", "sent_at"], "");
              const formattedDate = dateStr ? new Date(dateStr).toLocaleString() : "Recently";

              return (
                <div
                  key={id || Math.random().toString()}
                  className={`flex flex-col gap-3 p-5 sm:p-6 transition hover:bg-white/[.02] sm:flex-row sm:items-center sm:justify-between ${
                    !isRead ? "bg-cyan-400/[.02]" : ""
                  }`}
                >
                  <div className="flex items-start gap-4 min-w-0">
                    <span
                      className={`mt-1 h-2.5 w-2.5 rounded-full shrink-0 ${
                        !isRead
                          ? "bg-cyan-300 shadow-[0_0_8px_rgba(160,240,244,.8)]"
                          : "bg-white/10"
                      }`}
                    />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className={`text-sm ${!isRead ? "font-semibold text-white" : "text-white/70"}`}>
                          {subject}
                        </p>
                        <span className="rounded-full border border-white/10 bg-white/[.04] px-2 py-0.5 text-[9px] uppercase tracking-wider text-white/40">
                          {eventType.replace("_", " ")}
                        </span>
                      </div>
                      {body && <p className="mt-1 text-xs text-white/50 leading-relaxed">{body}</p>}
                      <p className="mt-2 text-[11px] text-white/30">{formattedDate}</p>
                    </div>
                  </div>

                  {!isRead && (
                    <button
                      onClick={() => id && markReadMutation.mutate(id)}
                      disabled={markReadMutation.isPending}
                      className="self-end sm:self-center shrink-0 rounded-xl border border-white/10 px-3 py-1.5 text-xs text-white/50 hover:bg-white/5 hover:text-white transition flex items-center gap-1.5"
                    >
                      <Check size={13} /> Mark read
                    </button>
                  )}
                </div>
              );
            })
          ) : (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <Inbox size={32} className="text-white/20 mb-3" />
              <p className="text-sm text-white/40">You're all caught up.</p>
              <p className="mt-1 text-xs text-white/25">New notifications will appear here as activity occurs in your flow.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
