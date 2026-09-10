import { createFileRoute } from "@tanstack/react-router";
import {
  Activity,
  Calendar,
  Filter,
  History,
  LoaderCircle,
  Shield,
  User,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, readArray, readValue, type ApiRecord } from "../../lib/api";

export const Route = createFileRoute("/app/audit")({ component: AuditPage });

const aggregateFilters = ["all", "user", "meeting", "task", "decision", "organization"];

function AuditPage() {
  const [filter, setFilter] = useState("all");

  const auditQuery = useQuery({
    queryKey: ["audit-logs", filter],
    queryFn: () =>
      api.auditLogs({
        aggregate_type: filter === "all" ? undefined : filter,
        limit: 50,
      }),
    enabled: typeof window !== "undefined",
    refetchInterval: 20_000,
  });

  const rawLogs = readArray(auditQuery.data);

  return (
    <div>
      <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
        <div>
          <p className="df-kicker">GOVERNANCE & COMPLIANCE / AUDIT</p>
          <h1 className="mt-4 font-display text-4xl font-semibold tracking-[-.06em] sm:text-6xl">
            Activity trail,<br />
            <span className="text-white/45">immutable record.</span>
          </h1>
          <p className="mt-5 max-w-lg text-sm leading-6 text-white/45">
            Full forensic timeline of role changes, member invitations, task assignments, and security events.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-white/40">
          <Shield size={14} className="text-cyan-200" /> Tamper-evident ledger
        </div>
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-1 overflow-x-auto rounded-2xl border border-white/10 bg-white/[.03] p-1">
          {aggregateFilters.map((item) => (
            <button
              key={item}
              onClick={() => setFilter(item)}
              className={`whitespace-nowrap rounded-xl px-3.5 py-2 text-xs capitalize transition ${
                filter === item ? "bg-white/[.1] text-white" : "text-white/40 hover:text-white/70"
              }`}
            >
              {item}
            </button>
          ))}
        </div>

        <span className="inline-flex items-center gap-2 text-xs text-white/35">
          <History size={14} /> {rawLogs.length} events logged
        </span>
      </div>

      <section className="df-app-card mt-5 overflow-hidden rounded-[26px]">
        <div className="hidden grid-cols-[160px_1fr_130px_150px] gap-4 border-b border-white/[.08] px-6 py-4 text-[10px] uppercase tracking-[.2em] text-white/30 md:grid">
          <span>Event Type</span>
          <span>Details & Scope</span>
          <span>Actor Type</span>
          <span className="text-right">Timestamp</span>
        </div>

        <div className="divide-y divide-white/[.07]">
          {auditQuery.isLoading ? (
            <div className="flex items-center justify-center gap-2 px-6 py-16 text-sm text-white/40">
              <LoaderCircle size={16} className="animate-spin" /> Fetching activity logs…
            </div>
          ) : rawLogs.length ? (
            rawLogs.map((log) => {
              const id = readValue(log, ["id", "log_id"]);
              const eventType = readValue(log, ["event_type"], "event");
              const aggregateType = readValue(log, ["aggregate_type"], "resource");
              const actorType = readValue(log, ["actor_type"], "user");
              const dateStr = readValue(log, ["occurred_at", "created_at"], "");
              const formattedDate = dateStr ? new Date(dateStr).toLocaleString() : "Recently";
              const ipAddress = readValue(log, ["ip_address"], "");

              return (
                <div
                  key={id || Math.random().toString()}
                  className="flex flex-col gap-2 px-6 py-4 transition hover:bg-white/[.02] md:grid md:grid-cols-[160px_1fr_130px_150px] md:items-center"
                >
                  <div>
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-2.5 py-0.5 text-[11px] font-medium text-cyan-200">
                      <Activity size={11} /> {eventType.replace(/_/g, " ")}
                    </span>
                  </div>

                  <div className="min-w-0">
                    <p className="truncate text-sm text-white/80">
                      Target: <span className="font-mono text-xs text-white/50">{aggregateType}</span>
                    </p>
                    {ipAddress && <p className="text-[11px] text-white/30">IP: {ipAddress}</p>}
                  </div>

                  <div className="hidden text-xs text-white/50 capitalize md:block">
                    {actorType}
                  </div>

                  <div className="text-xs text-white/40 md:text-right">
                    {formattedDate}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="px-6 py-16 text-center text-sm text-white/40">
              No audit logs found for this filter.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
