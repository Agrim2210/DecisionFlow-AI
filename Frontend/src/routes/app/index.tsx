import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Clock3,
  FileText,
  LoaderCircle,
  Plus,
  Search,
  Sparkles,
  Upload,
  X,
} from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, readArray, readNumber, readValue, type ApiRecord } from "../../lib/api";

export const Route = createFileRoute("/app/")({ component: DashboardPage });

function DashboardPage() {
  const queryClient = useQueryClient();
  const isClient = typeof window !== "undefined";
  const dashboardQuery = useQuery({
    queryKey: ["dashboard"],
    queryFn: api.dashboard,
    enabled: isClient,
  });
  const tasksQuery = useQuery({
    queryKey: ["my-tasks"],
    queryFn: api.myTasks,
    enabled: isClient,
  });
  const meetingsQuery = useQuery({
    queryKey: ["meetings"],
    queryFn: api.meetings,
    enabled: isClient,
    refetchInterval: 15_000,
  });
  const [showIngest, setShowIngest] = useState(false);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [searchScope, setSearchScope] = useState<"signals" | "meeting">("signals");
  const searchQuery = useQuery({
    queryKey: ["search", query, searchScope],
    queryFn: async () => {
      const response = await api.search(query, {
        mode: "semantic",
        source_type: searchScope === "meeting" ? "meeting" : undefined,
        limit: 8,
      });
      return readArray(response).slice(0, 8);
    },
    enabled: query.length > 2,
    staleTime: 30_000,
  });
  const dashboard = dashboardQuery.data;
  const tasks = readArray(tasksQuery.data).slice(0, 5);
  const meetings = readArray(meetingsQuery.data).slice(0, 5);
  const latestCompletedMeeting = meetings.find(
    (meeting) => readValue(meeting, ["status"]).toLowerCase() === "completed",
  );
  const latestMeetingId = latestCompletedMeeting
    ? readValue(latestCompletedMeeting, ["id", "meeting_id"])
    : "";
  const extractionQuery = useQuery({
    queryKey: ["meeting-extraction", latestMeetingId],
    queryFn: () => api.meetingExtraction(latestMeetingId),
    enabled: Boolean(latestMeetingId),
    staleTime: 60_000,
  });
  const extraction = extractionQuery.data;
  const decisions = readRecordArray(extraction?.decisions);
  const extractedTasks = readRecordArray(extraction?.tasks);
  const risks = readRecordArray(extraction?.risks);
  const openQuestions = readRecordArray(extraction?.open_questions);
  const completion = Math.round(
    readNumber(
      dashboard,
      [
        "my_completion_rate",
        "completion_rate",
        "my_reliability_score",
        "reliability_score",
        "on_time_rate",
      ],
      72,
    ),
  );
  const openTasks = readNumber(
    dashboard,
    ["my_tasks_pending", "pending_tasks", "open_tasks", "active_tasks", "task_count"],
    tasks.length || 12,
  );
  const atRisk = readNumber(
    dashboard,
    ["my_tasks_overdue", "overdue_tasks", "at_risk", "at_risk_tasks", "risk_count"],
    tasks.filter(
      (task) =>
        ["blocked", "overdue"].includes(readValue(task, ["status"]).toLowerCase()) ||
        task["is_overdue"] === true ||
        task["is_unassigned"] === true,
    ).length || 3,
  );
  const meetingsProcessed = readNumber(
    dashboard,
    ["my_meetings_count", "meetings_processed", "meeting_count", "total_meetings"],
    meetings.length || 8,
  );
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
      queryClient.invalidateQueries({ queryKey: ["meetings"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["meeting-extraction"] });
    },
  });
  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault();
    setQuery(search.trim());
  };
  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    return hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  }, []);
  return (
    <div>
      <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
        <div>
          <p className="df-kicker">OVERVIEW / LIVE SIGNAL</p>
          <h1 className="mt-4 font-display text-4xl font-semibold tracking-[-.06em] sm:text-6xl">
            {greeting},<br />
            <span className="text-white/45">keep the room moving.</span>
          </h1>
        </div>
        <button
          onClick={() => setShowIngest(true)}
          className="df-pill-button self-start md:self-auto"
        >
          <Plus size={15} /> Add a meeting
        </button>
      </div>
      <div className="mt-10 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Follow-through"
          value={`${completion}%`}
          trend="this cycle"
          icon={<CheckCircle2 size={16} />}
        />
        <StatCard
          label="Open work"
          value={String(openTasks).padStart(2, "0")}
          trend="owned tasks"
          icon={<Clock3 size={16} />}
        />
        <StatCard
          label="At risk"
          value={String(atRisk).padStart(2, "0")}
          trend="needs a look"
          warm
          icon={<Sparkles size={16} />}
        />
        <StatCard
          label="Meetings mapped"
          value={String(meetingsProcessed).padStart(2, "0")}
          trend="in your flow"
          icon={<FileText size={16} />}
        />
      </div>
      <div className="mt-6 grid gap-5 xl:grid-cols-[1.3fr_.7fr]">
        <section className="df-app-card rounded-[26px] p-5 sm:p-7">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
            <div>
              <p className="df-kicker">MY NEXT MOVES</p>
              <h2 className="mt-3 font-display text-2xl font-semibold tracking-[-.04em]">
                Work with a pulse.
              </h2>
            </div>
            <Link
              to="/app/tasks"
              className="inline-flex items-center gap-2 text-xs text-cyan-100/70 hover:text-white"
            >
              View all tasks <ArrowRight size={14} />
            </Link>
          </div>
          <div className="mt-7 space-y-2">
            {tasks.length ? (
              tasks.map((task) => (
                <TaskPreview
                  key={readValue(task, ["id", "task_id"], Math.random().toString())}
                  task={task}
                />
              ))
            ) : (
              <EmptyState text="Your next action will appear here after the first transcript is mapped." />
            )}
          </div>
        </section>
        <section className="df-app-card rounded-[26px] p-5 sm:p-7">
          <div className="flex items-start justify-between">
            <div>
              <p className="df-kicker">RECENT ROOMS</p>
              <h2 className="mt-3 font-display text-2xl font-semibold tracking-[-.04em]">
                Conversation memory.
              </h2>
            </div>
            <CalendarDays size={18} className="text-white/35" />
          </div>
          <div className="mt-7 space-y-3">
            {meetings.length ? (
              meetings.map((meeting) => (
                <MeetingRow
                  key={readValue(meeting, ["id", "meeting_id"], Math.random().toString())}
                  meeting={meeting}
                />
              ))
            ) : (
              <EmptyState text="Upload a meeting to start building the trail." />
            )}
          </div>
        </section>
      </div>
      <section className="df-app-card mt-5 rounded-[26px] p-5 sm:p-7">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
          <div>
            <p className="df-kicker">EXTRACTED SIGNALS</p>
            <h2 className="mt-3 font-display text-2xl font-semibold tracking-[-.04em]">
              From the last room.
            </h2>
            <p className="mt-2 text-sm text-white/40">
              Decisions, owners, risks, and unanswered threads mapped from the completed transcript.
            </p>
          </div>
          {latestCompletedMeeting && (
            <span className="rounded-full border border-cyan-100/15 bg-cyan-100/[.05] px-3 py-1.5 text-[10px] uppercase tracking-[.16em] text-cyan-100/65">
              {readValue(latestCompletedMeeting, ["title"], "Completed meeting")}
            </span>
          )}
        </div>
        {extractionQuery.isFetching && !extraction ? (
          <p className="mt-6 text-sm text-white/45">Reading the mapped signals…</p>
        ) : extractionQuery.isError ? (
          <p className="mt-6 text-sm text-rose-100/70">
            The transcript is complete, but extracted signals could not be loaded yet.
          </p>
        ) : !latestCompletedMeeting ? (
          <EmptyState text="Signals will appear when the first meeting finishes processing." />
        ) : (
          <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <ExtractionGroup
              label="Decisions"
              accent="text-cyan-100"
              items={decisions}
              titleKeys={["title", "decision"]}
              bodyKeys={["description", "content"]}
              empty="No decisions detected."
            />
            <ExtractionGroup
              label="Action items"
              accent="text-emerald-200"
              items={extractedTasks}
              titleKeys={["title", "name"]}
              bodyKeys={["description", "content"]}
              empty="No action items detected."
            />
            <ExtractionGroup
              label="Risks"
              accent="text-amber-200"
              items={risks}
              titleKeys={["description", "title"]}
              bodyKeys={["recommendation", "risk_type"]}
              empty="No risks detected."
            />
            <ExtractionGroup
              label="Open questions"
              accent="text-violet-200"
              items={openQuestions}
              titleKeys={["question", "title"]}
              bodyKeys={["context", "answer"]}
              empty="No open questions detected."
            />
          </div>
        )}
      </section>
      <section className="df-app-card mt-5 rounded-[26px] p-5 sm:p-7">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="df-kicker">FIND THE THREAD</p>
            <h2 className="mt-3 font-display text-2xl font-semibold tracking-[-.04em]">
              Search across the room.
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              ["signals", "Semantic signals"],
              ["meeting", "Meeting memory"],
            ].map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => setSearchScope(value as "signals" | "meeting")}
                className={`rounded-full border px-3 py-1.5 text-[10px] uppercase tracking-[.14em] transition ${
                  searchScope === value
                    ? "border-cyan-100/25 bg-cyan-100/[.08] text-cyan-100"
                    : "border-white/10 text-white/35 hover:text-white/70"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <form onSubmit={submitSearch} className="relative w-full md:max-w-sm">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-white/30"
              size={15}
            />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="What did we decide about…"
              className="df-app-input w-full rounded-2xl py-3 pl-9 pr-4 text-sm text-white placeholder:text-white/25"
            />
          </form>
        </div>
        {query && (
          <div className="mt-6 border-t border-white/[.08] pt-5">
            {searchQuery.isFetching ? (
              <p className="text-sm text-white/45">Following the thread…</p>
            ) : searchQuery.isError ? (
              <p className="text-sm text-rose-100/75">Search is unavailable right now.</p>
            ) : (
              <div className="space-y-2">
                {readArray(searchQuery.data).map((result) => (
                  <div
                    key={readValue(result, ["source_id", "id"], Math.random().toString())}
                    className="rounded-2xl border border-white/[.08] bg-white/[.025] p-4"
                  >
                    <p className="text-xs uppercase tracking-[.16em] text-cyan-100/60">
                      {readValue(result, ["source_type"], "signal")}
                    </p>
                    <p className="mt-2 text-sm leading-6 text-white/70">
                      {readValue(
                        result,
                        ["content", "title"],
                        "No matching thread content returned.",
                      )}
                    </p>
                  </div>
                ))}
                {!readArray(searchQuery.data).length && (
                  <p className="text-sm text-white/45">
                    No focused match yet. Try a decision, owner, task, risk, or question.
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </section>
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
function readRecordArray(value: unknown): ApiRecord[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is ApiRecord => Boolean(item && typeof item === "object"));
}

function ExtractionGroup({
  label,
  accent,
  items,
  titleKeys,
  bodyKeys,
  empty,
}: {
  label: string;
  accent: string;
  items: ApiRecord[];
  titleKeys: string[];
  bodyKeys: string[];
  empty: string;
}) {
  return (
    <div className="rounded-2xl border border-white/[.08] bg-white/[.025] p-4">
      <div className="flex items-center justify-between gap-3">
        <p className={`text-xs uppercase tracking-[.16em] ${accent}`}>{label}</p>
        <span className="font-mono text-[10px] text-white/30">
          {String(items.length).padStart(2, "0")}
        </span>
      </div>
      <div className="mt-4 space-y-3">
        {items.length ? (
          items.slice(0, 4).map((item) => (
            <div
              key={readValue(item, ["id"], Math.random().toString())}
              className="border-t border-white/[.07] pt-3 first:border-t-0 first:pt-0"
            >
              <p className="text-sm leading-5 text-white/75">
                {readValue(item, titleKeys, "Untitled signal")}
              </p>
              <p className="mt-1 line-clamp-2 text-xs leading-5 text-white/35">
                {readValue(item, bodyKeys, "Mapped from transcript")}
              </p>
            </div>
          ))
        ) : (
          <p className="text-xs leading-5 text-white/35">{empty}</p>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  trend,
  icon,
  warm = false,
}: {
  label: string;
  value: string;
  trend: string;
  icon: React.ReactNode;
  warm?: boolean;
}) {
  return (
    <div className="df-app-card rounded-2xl p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs text-white/45">{label}</span>
        <span className={warm ? "text-amber-200/70" : "text-cyan-100/65"}>{icon}</span>
      </div>
      <div className="mt-5 flex items-end justify-between">
        <strong className="font-display text-3xl font-semibold tracking-[-.05em]">{value}</strong>
        <span className={warm ? "text-[10px] text-amber-200/65" : "text-[10px] text-cyan-100/60"}>
          {trend}
        </span>
      </div>
    </div>
  );
}
function TaskPreview({ task }: { task: ApiRecord }) {
  const status = readValue(task, ["status", "state"], "pending").replaceAll("_", " ");
  const tone =
    status === "completed"
      ? "text-emerald-200/75"
      : status === "blocked" || status === "overdue"
        ? "text-amber-200/75"
        : "text-cyan-100/65";
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-white/[.07] bg-white/[.025] px-4 py-3">
      <span
        className={`h-2 w-2 rounded-full ${status === "completed" ? "bg-emerald-300" : status === "blocked" || status === "overdue" ? "bg-amber-300" : "bg-cyan-200"}`}
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-white/75">
          {readValue(task, ["title", "name", "content"], "Untitled action")}
        </p>
        <p className="mt-1 truncate text-xs text-white/30">
          {readValue(task, ["owner_name", "assignee_name"], "Unassigned")} ·{" "}
          {readValue(task, ["due_date", "deadline"], "No date")}
        </p>
      </div>
      <span className={`hidden text-[10px] uppercase tracking-[.12em] sm:block ${tone}`}>
        {status}
      </span>
    </div>
  );
}
function MeetingRow({ meeting }: { meeting: ApiRecord }) {
  return (
    <div className="flex items-center gap-3">
      <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-white/[.08] bg-white/[.035] text-cyan-100/65">
        <FileText size={15} />
      </span>
      <div className="min-w-0">
        <p className="truncate text-sm text-white/70">
          {readValue(meeting, ["title", "name"], "Untitled meeting")}
        </p>
        <p className="mt-1 text-xs text-white/30">
          {readValue(meeting, ["status", "stage_name"], "processing")} ·{" "}
          {readValue(meeting, ["meeting_date", "created_at"], "recent")}
        </p>
      </div>
    </div>
  );
}
function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-white/10 px-4 py-7 text-center text-sm leading-6 text-white/35">
      {text}
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
