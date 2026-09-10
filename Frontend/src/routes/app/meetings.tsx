import { createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  FileAudio,
  FileText,
  Filter,
  LoaderCircle,
  Plus,
  RefreshCw,
  Sparkles,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, readArray, readNumber, readValue, type ApiRecord } from "../../lib/api";

export const Route = createFileRoute("/app/meetings")({ component: MeetingsPage });

const statusFilters = ["all", "completed", "processing", "uploaded", "failed"];

function MeetingsPage() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("all");
  const [selectedMeetingId, setSelectedMeetingId] = useState<string | null>(null);
  const [showIngest, setShowIngest] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const meetingsQuery = useQuery({
    queryKey: ["all-my-meetings"],
    queryFn: () => api.myMeetings({ limit: 50 }),
    enabled: typeof window !== "undefined",
    refetchInterval: 10_000,
  });

  const rawMeetings = readArray(meetingsQuery.data);

  const meetings = useMemo(() => {
    return rawMeetings.filter((m) => {
      if (filter === "all") return true;
      const status = readValue(m, ["status", "stage_name"]).toLowerCase();
      return status === filter;
    });
  }, [rawMeetings, filter]);

  const completedCount = rawMeetings.filter(
    (m) => readValue(m, ["status"]).toLowerCase() === "completed",
  ).length;
  const processingCount = rawMeetings.filter((m) =>
    ["processing", "queued", "uploaded"].includes(readValue(m, ["status"]).toLowerCase()),
  ).length;
  const failedCount = rawMeetings.filter(
    (m) => readValue(m, ["status"]).toLowerCase() === "failed",
  ).length;

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteMeeting(id),
    onSuccess: () => {
      setDeleteConfirmId(null);
      if (selectedMeetingId === deleteConfirmId) setSelectedMeetingId(null);
      queryClient.invalidateQueries({ queryKey: ["all-my-meetings"] });
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const retryMutation = useMutation({
    mutationFn: (id: string) => api.retryMeeting(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["all-my-meetings"] });
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
    },
  });

  const ingest = useMutation({
    mutationFn: async ({ file, title, text }: { file?: File; title: string; text: string }) => {
      if (file) {
        const form = new FormData();
        form.append("file", file);
        form.append("title", title || file.name);
        return api.uploadMeeting(form);
      }
      return api.pasteMeeting({ title, text, source: "paste" });
    },
    onSuccess: () => {
      setShowIngest(false);
      queryClient.invalidateQueries({ queryKey: ["all-my-meetings"] });
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  return (
    <div>
      <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
        <div>
          <p className="df-kicker">CONVERSATION MEMORY / MEETINGS</p>
          <h1 className="mt-4 font-display text-4xl font-semibold tracking-[-.06em] sm:text-6xl">
            Every room,
            <br />
            <span className="text-white/45">mapped to action.</span>
          </h1>
          <p className="mt-5 max-w-lg text-sm leading-6 text-white/45">
            Upload transcripts or recordings. Review extracted decisions, owners, risks, and next moves.
          </p>
        </div>
        <button onClick={() => setShowIngest(true)} className="df-pill-button self-start md:self-auto">
          <Plus size={15} /> Add a meeting
        </button>
      </div>

      <div className="mt-10 grid gap-3 sm:grid-cols-4">
        <MiniStat label="Total mapped" value={String(rawMeetings.length).padStart(2, "0")} />
        <MiniStat label="Completed" value={String(completedCount).padStart(2, "0")} cool />
        <MiniStat label="In pipeline" value={String(processingCount).padStart(2, "0")} />
        <MiniStat label="Needs attention" value={String(failedCount).padStart(2, "0")} warm={failedCount > 0} />
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-1 overflow-x-auto rounded-2xl border border-white/10 bg-white/[.03] p-1">
          {statusFilters.map((item) => (
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
          <Filter size={14} /> {meetings.length} showing
        </span>
      </div>

      <section className="df-app-card mt-5 overflow-hidden rounded-[26px]">
        <div className="hidden grid-cols-[1fr_120px_140px_130px_110px] gap-4 border-b border-white/[.08] px-6 py-4 text-[10px] uppercase tracking-[.2em] text-white/30 md:grid">
          <span>Meeting</span>
          <span>Source</span>
          <span>Date</span>
          <span>Status</span>
          <span className="text-right">Actions</span>
        </div>
        <div className="divide-y divide-white/[.07]">
          {meetingsQuery.isLoading ? (
            <div className="flex items-center justify-center gap-2 px-6 py-16 text-sm text-white/40">
              <LoaderCircle size={16} className="animate-spin" /> Loading your rooms…
            </div>
          ) : meetings.length ? (
            meetings.map((meeting) => {
              const id = readValue(meeting, ["id", "meeting_id"]);
              const title = readValue(meeting, ["title", "name"], "Untitled meeting");
              const source = readValue(meeting, ["source"], "transcript");
              const status = readValue(meeting, ["status"], "processing").toLowerCase();
              const dateStr = readValue(meeting, ["meeting_date", "created_at"], "");
              const formattedDate = dateStr ? new Date(dateStr).toLocaleDateString() : "Recent";

              return (
                <div
                  key={id || Math.random().toString()}
                  className="flex flex-col gap-3 px-6 py-4 transition hover:bg-white/[.02] md:grid md:grid-cols-[1fr_120px_140px_130px_110px] md:items-center"
                >
                  <div className="min-w-0">
                    <button
                      onClick={() => id && setSelectedMeetingId(id)}
                      className="text-left font-medium text-white/90 hover:text-cyan-200 transition"
                    >
                      <p className="truncate text-sm">{title}</p>
                    </button>
                    <p className="text-xs text-white/30 md:hidden mt-0.5">{formattedDate} · {source}</p>
                  </div>

                  <div className="hidden text-xs text-white/50 capitalize md:block">
                    {source}
                  </div>

                  <div className="hidden text-xs text-white/40 md:block">
                    {formattedDate}
                  </div>

                  <div>
                    <StatusBadge status={status} />
                  </div>

                  <div className="flex items-center justify-end gap-2">
                    {status === "failed" && (
                      <button
                        title="Retry extraction"
                        onClick={() => id && retryMutation.mutate(id)}
                        disabled={retryMutation.isPending}
                        className="rounded-lg p-1.5 text-white/40 hover:bg-white/10 hover:text-white transition"
                      >
                        <RefreshCw size={14} className={retryMutation.isPending ? "animate-spin" : ""} />
                      </button>
                    )}
                    <button
                      title="View extraction"
                      onClick={() => id && setSelectedMeetingId(id)}
                      className="rounded-lg p-1.5 text-white/40 hover:bg-white/10 hover:text-cyan-200 transition"
                    >
                      <Sparkles size={14} />
                    </button>
                    <button
                      title="Delete meeting"
                      onClick={() => id && setDeleteConfirmId(id)}
                      className="rounded-lg p-1.5 text-white/30 hover:bg-rose-500/10 hover:text-rose-400 transition"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="px-6 py-16 text-center text-sm text-white/40">
              No meetings found in this view. Click "Add a meeting" to map your first transcript.
            </div>
          )}
        </div>
      </section>

      {/* Extraction Modal */}
      {selectedMeetingId && (
        <MeetingDetailModal
          meetingId={selectedMeetingId}
          onClose={() => setSelectedMeetingId(null)}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-md">
          <div className="df-app-card w-full max-w-md rounded-[28px] p-6 sm:p-8">
            <h3 className="font-display text-xl font-semibold text-white">Delete meeting?</h3>
            <p className="mt-2 text-sm text-white/50">
              This will remove the transcript and all associated decisions, tasks, and risks extracted from this meeting.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setDeleteConfirmId(null)}
                className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/70 hover:bg-white/5 transition"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deleteMutation.isPending}
                onClick={() => deleteMutation.mutate(deleteConfirmId)}
                className="rounded-xl bg-rose-500/20 border border-rose-500/30 px-4 py-2.5 text-xs font-semibold text-rose-300 hover:bg-rose-500/30 transition"
              >
                {deleteMutation.isPending ? "Deleting…" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add meeting modal */}
      {showIngest && (
        <IngestDialog
          busy={ingest.isPending}
          error={ingest.error ? "We could not map that meeting. Try again." : ""}
          onClose={() => setShowIngest(false)}
          onSubmit={(payload) => ingest.mutate(payload)}
        />
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "completed") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-0.5 text-[11px] font-medium text-emerald-300">
        <CheckCircle2 size={12} /> Ready
      </span>
    );
  }
  if (status === "failed") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-rose-400/20 bg-rose-400/10 px-2.5 py-0.5 text-[11px] font-medium text-rose-300">
        <AlertTriangle size={12} /> Failed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-2.5 py-0.5 text-[11px] font-medium text-cyan-300">
      <LoaderCircle size={12} className="animate-spin" /> Processing
    </span>
  );
}

function MeetingDetailModal({ meetingId, onClose }: { meetingId: string; onClose: () => void }) {
  const detailQuery = useQuery({
    queryKey: ["meeting-detail", meetingId],
    queryFn: () => api.meetingDetail(meetingId),
  });

  const extractionQuery = useQuery({
    queryKey: ["meeting-extraction", meetingId],
    queryFn: () => api.meetingExtraction(meetingId),
  });

  const meeting = detailQuery.data;
  const extraction = extractionQuery.data;

  const decisions = readRecordArray(extraction?.decisions);
  const tasks = readRecordArray(extraction?.tasks);
  const risks = readRecordArray(extraction?.risks);
  const questions = readRecordArray(extraction?.open_questions);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-md">
      <div className="df-app-card w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-[28px] p-6 sm:p-8">
        <div className="flex items-start justify-between border-b border-white/[.08] pb-5">
          <div>
            <p className="df-kicker">EXTRACTED SIGNALS</p>
            <h2 className="mt-2 font-display text-2xl font-semibold text-white">
              {readValue(meeting, ["title"], "Meeting details")}
            </h2>
            <p className="mt-1 text-xs text-white/40">
              Source: {readValue(meeting, ["source"], "transcript")} · Created {readValue(meeting, ["created_at"], "recently")}
            </p>
          </div>
          <button onClick={onClose} className="rounded-xl p-2 text-white/40 hover:bg-white/10 hover:text-white transition">
            <X size={18} />
          </button>
        </div>

        {extractionQuery.isLoading ? (
          <div className="flex items-center justify-center py-20 text-sm text-white/40">
            <LoaderCircle size={20} className="animate-spin mr-2" /> Loading signals…
          </div>
        ) : (
          <div className="mt-6 space-y-6">
            {/* Decisions */}
            <div>
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-cyan-200">
                  Decisions ({decisions.length})
                </h3>
              </div>
              <div className="mt-3 space-y-2">
                {decisions.length ? (
                  decisions.map((d, i) => (
                    <div key={i} className="rounded-xl border border-white/[.08] bg-white/[.02] p-3.5">
                      <p className="text-sm font-medium text-white/90">{readValue(d, ["title", "decision"])}</p>
                      {readValue(d, ["description", "content"]) && (
                        <p className="mt-1 text-xs text-white/40 leading-5">{readValue(d, ["description", "content"])}</p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-white/30 italic">No decisions extracted.</p>
                )}
              </div>
            </div>

            {/* Action Items / Tasks */}
            <div>
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-emerald-200">
                  Action Items ({tasks.length})
                </h3>
              </div>
              <div className="mt-3 space-y-2">
                {tasks.length ? (
                  tasks.map((t, i) => (
                    <div key={i} className="rounded-xl border border-white/[.08] bg-white/[.02] p-3.5 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-white/90">{readValue(t, ["title", "name"])}</p>
                        <p className="mt-0.5 text-xs text-white/40">
                          Owner: {readValue(t, ["owner_name"], "Unassigned")} · Due: {readValue(t, ["due_date"], "None")}
                        </p>
                      </div>
                      <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border border-white/10 text-white/60">
                        {readValue(t, ["status"], "pending")}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-white/30 italic">No action items extracted.</p>
                )}
              </div>
            </div>

            {/* Risks */}
            <div>
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-200">
                  Risks & Caveats ({risks.length})
                </h3>
              </div>
              <div className="mt-3 space-y-2">
                {risks.length ? (
                  risks.map((r, i) => (
                    <div key={i} className="rounded-xl border border-white/[.08] bg-white/[.02] p-3.5">
                      <p className="text-sm font-medium text-amber-200/90">{readValue(r, ["description", "title"])}</p>
                      {readValue(r, ["recommendation"]) && (
                        <p className="mt-1 text-xs text-white/40 leading-5">Recommendation: {readValue(r, ["recommendation"])}</p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-white/30 italic">No risks identified.</p>
                )}
              </div>
            </div>

            {/* Open Questions */}
            <div>
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-violet-200">
                  Open Questions ({questions.length})
                </h3>
              </div>
              <div className="mt-3 space-y-2">
                {questions.length ? (
                  questions.map((q, i) => (
                    <div key={i} className="rounded-xl border border-white/[.08] bg-white/[.02] p-3.5">
                      <p className="text-sm font-medium text-white/90">{readValue(q, ["question", "title"])}</p>
                      {readValue(q, ["context", "answer"]) && (
                        <p className="mt-1 text-xs text-white/40 leading-5">{readValue(q, ["context", "answer"])}</p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-white/30 italic">No open questions detected.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MiniStat({
  label,
  value,
  cool = false,
  warm = false,
}: {
  label: string;
  value: string;
  cool?: boolean;
  warm?: boolean;
}) {
  return (
    <div className="df-app-card rounded-2xl p-5">
      <span className="text-xs text-white/45">{label}</span>
      <div className="mt-4 flex items-end justify-between">
        <strong className="font-display text-3xl font-semibold tracking-[-.05em]">{value}</strong>
        <span
          className={`text-[10px] uppercase tracking-wider ${
            warm ? "text-amber-200/70" : cool ? "text-cyan-200/70" : "text-white/35"
          }`}
        >
          rooms
        </span>
      </div>
    </div>
  );
}

function IngestDialog({
  busy,
  error,
  onClose,
  onSubmit,
}: {
  busy: boolean;
  error: string;
  onClose: () => void;
  onSubmit: (payload: { file?: File; title: string; text: string }) => void;
}) {
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File>();
  const inputRef = useRef<HTMLInputElement | null>(null);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-md">
      <div className="df-app-card w-full max-w-xl rounded-[28px] p-6 sm:p-8">
        <div className="flex items-start justify-between">
          <div>
            <p className="df-kicker">NEW SIGNAL</p>
            <h2 className="mt-3 font-display text-2xl font-semibold">Bring the room in.</h2>
            <p className="mt-2 text-sm text-white/45">
              Upload a transcript or paste the raw conversation. We will map the next moves.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white"
            aria-label="Close dialog"
          >
            <X size={18} />
          </button>
        </div>
        <div className="mt-7 space-y-4">
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Meeting title"
            className="df-app-input w-full rounded-2xl px-4 py-3 text-sm text-white placeholder:text-white/25"
          />
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="flex w-full items-center gap-3 rounded-2xl border border-dashed border-cyan-100/20 bg-cyan-100/[.04] px-4 py-4 text-left text-sm text-white/55 hover:border-cyan-100/45"
          >
            <Upload size={17} className="text-cyan-100/70" />
            <span>{file ? file.name : "Choose a transcript file"}</span>
            <input
              ref={inputRef}
              type="file"
              accept=".txt,.md,.doc,.docx,.vtt,.srt,audio/*,video/*"
              className="hidden"
              onChange={(event) => setFile(event.target.files?.[0])}
            />
          </button>
          <div className="relative">
            <textarea
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="Or paste your meeting transcript here…"
              rows={6}
              className="df-app-input w-full resize-none rounded-2xl px-4 py-3 text-sm leading-6 text-white placeholder:text-white/25"
            />
            <span className="pointer-events-none absolute bottom-3 right-3 text-[10px] uppercase tracking-[.16em] text-white/20">
              paste
            </span>
          </div>
          {error && <p className="text-xs text-rose-100/75">{error}</p>}
          <button
            disabled={busy || (!file && text.trim().length < 12)}
            onClick={() => onSubmit({ file, title, text })}
            className="df-pill-button w-full disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? (
              <>
                <LoaderCircle size={15} className="animate-spin" /> Mapping the room…
              </>
            ) : (
              <>
                Create signal <ArrowRight size={15} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function readRecordArray(value: unknown): ApiRecord[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is ApiRecord => Boolean(item && typeof item === "object"));
}
