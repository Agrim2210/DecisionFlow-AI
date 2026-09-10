import { createFileRoute } from "@tanstack/react-router";
import {
  AlertTriangle,
  ArrowUpRight,
  Calendar,
  Check,
  CheckCircle2,
  Circle,
  Clock3,
  Edit2,
  Filter,
  LoaderCircle,
  Plus,
  UserCheck,
  UserRound,
  Users,
  X,
} from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, readArray, readValue, type ApiRecord } from "../../lib/api";
import { useSession } from "../../lib/session";

export const Route = createFileRoute("/app/tasks")({ component: TasksPage });
const statusFilters = ["all", "pending", "in_progress", "completed", "blocked", "overdue"];

function TasksPage() {
  const queryClient = useQueryClient();
  const { user } = useSession();
  const [scope, setScope] = useState<"mine" | "all">("mine");
  const [filter, setFilter] = useState("all");
  const [editingTask, setEditingTask] = useState<ApiRecord | null>(null);
  const [assigningTask, setAssigningTask] = useState<ApiRecord | null>(null);

  // Queries
  const myTasksQuery = useQuery({
    queryKey: ["my-tasks"],
    queryFn: api.myTasks,
    enabled: typeof window !== "undefined" && scope === "mine",
    refetchInterval: 15_000,
  });

  const allTasksQuery = useQuery({
    queryKey: ["all-tasks"],
    queryFn: () => api.allTasks({ limit: 50 }),
    enabled: typeof window !== "undefined" && scope === "all",
    refetchInterval: 15_000,
  });

  const usersQuery = useQuery({
    queryKey: ["workspace-users"],
    queryFn: () => api.users({ limit: 50 }),
    enabled: typeof window !== "undefined",
  });

  const activeQuery = scope === "mine" ? myTasksQuery : allTasksQuery;
  const rawTasks = readArray(activeQuery.data);
  const workspaceUsers = usersQuery.data?.users || [];

  // Mutations
  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.updateTaskStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["all-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const updateTask = useMutation({
    mutationFn: ({
      id,
      title,
      description,
      dueDate,
    }: {
      id: string;
      title: string;
      description: string;
      dueDate?: string;
    }) =>
      api.updateTask(id, {
        title,
        description,
        due_date: dueDate || undefined,
      }),
    onSuccess: () => {
      setEditingTask(null);
      queryClient.invalidateQueries({ queryKey: ["my-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["all-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const assignTask = useMutation({
    mutationFn: ({ taskId, ownerId }: { taskId: string; ownerId: string }) =>
      api.assignTask(taskId, { owner_id: ownerId }),
    onSuccess: () => {
      setAssigningTask(null);
      queryClient.invalidateQueries({ queryKey: ["my-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["all-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });

  const tasks = useMemo(
    () =>
      rawTasks.filter((task) => {
        if (filter === "all") return true;
        const status = readValue(task, ["status", "state"], "pending");
        if (filter === "overdue") return status === "overdue" || task["is_overdue"] === true;
        return status === filter;
      }),
    [rawTasks, filter],
  );

  const completed = rawTasks.filter(
    (task) => readValue(task, ["status", "state"]) === "completed",
  ).length;
  const blocked = rawTasks.filter(
    (task) =>
      ["blocked", "overdue"].includes(readValue(task, ["status", "state"])) ||
      task["is_overdue"] === true,
  ).length;

  return (
    <div>
      <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
        <div>
          <p className="df-kicker">WORK / COMMITMENTS</p>
          <h1 className="mt-4 font-display text-4xl font-semibold tracking-[-.06em] sm:text-6xl">
            Make ownership<br />
            <span className="text-white/45">visible.</span>
          </h1>
          <p className="mt-5 max-w-lg text-sm leading-6 text-white/45">
            The meeting is over. This is where every decision gets a clear owner, a firm deadline, and trackable momentum.
          </p>
        </div>

        {/* Scope Switcher */}
        <div className="flex items-center gap-1 rounded-2xl border border-white/10 bg-white/[.03] p-1 self-start md:self-auto">
          <button
            onClick={() => setScope("mine")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs transition ${
              scope === "mine" ? "bg-white/[.1] text-white font-medium" : "text-white/40 hover:text-white/70"
            }`}
          >
            <UserRound size={14} /> My Tasks
          </button>
          <button
            onClick={() => setScope("all")}
            className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs transition ${
              scope === "all" ? "bg-white/[.1] text-white font-medium" : "text-white/40 hover:text-white/70"
            }`}
          >
            <Users size={14} /> Workspace Tasks
          </button>
        </div>
      </div>

      <div className="mt-10 grid gap-3 sm:grid-cols-3">
        <MiniStat label="Total tracked" value={String(rawTasks.length).padStart(2, "0")} />
        <MiniStat label="Completed" value={String(completed).padStart(2, "0")} cool />
        <MiniStat label="Needs attention" value={String(blocked).padStart(2, "0")} warm={blocked > 0} />
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-1 overflow-x-auto rounded-2xl border border-white/10 bg-white/[.03] p-1">
          {statusFilters.map((item) => (
            <button
              key={item}
              onClick={() => setFilter(item)}
              className={`whitespace-nowrap rounded-xl px-3 py-2 text-xs capitalize transition ${
                filter === item ? "bg-white/[.1] text-white" : "text-white/40 hover:text-white/70"
              }`}
            >
              {item.replace("_", " ")}
            </button>
          ))}
        </div>
        <span className="inline-flex items-center gap-2 text-xs text-white/35">
          <Filter size={14} /> {tasks.length} showing
        </span>
      </div>

      <section className="df-app-card mt-5 overflow-hidden rounded-[26px]">
        <div className="hidden grid-cols-[1fr_150px_140px_130px_90px] gap-4 border-b border-white/[.08] px-6 py-4 text-[10px] uppercase tracking-[.2em] text-white/30 md:grid">
          <span>Action</span>
          <span>Owner</span>
          <span>Due</span>
          <span>Status</span>
          <span className="text-right">Actions</span>
        </div>
        <div className="divide-y divide-white/[.07]">
          {activeQuery.isLoading ? (
            <div className="flex items-center justify-center gap-2 px-6 py-16 text-sm text-white/40">
              <LoaderCircle size={16} className="animate-spin" /> Loading tasks…
            </div>
          ) : tasks.length ? (
            tasks.map((task) => {
              const id = readValue(task, ["id", "task_id"]);
              return (
                <TaskDetail
                  key={id || JSON.stringify(task)}
                  task={task}
                  busy={updateStatus.isPending}
                  onStatus={(status) => {
                    if (id) updateStatus.mutate({ id, status });
                  }}
                  onEdit={() => setEditingTask(task)}
                  onAssign={() => setAssigningTask(task)}
                />
              );
            })
          ) : (
            <div className="px-6 py-16 text-center text-sm text-white/40">
              No tasks in this view. Commitments mapped from transcripts will appear here.
            </div>
          )}
        </div>
      </section>

      {/* Edit Task Modal */}
      {editingTask && (
        <EditTaskModal
          task={editingTask}
          busy={updateTask.isPending}
          onClose={() => setEditingTask(null)}
          onSave={(payload) => {
            const id = readValue(editingTask, ["id", "task_id"]);
            if (id) updateTask.mutate({ id, ...payload });
          }}
        />
      )}

      {/* Assign Task Modal */}
      {assigningTask && (
        <AssignTaskModal
          task={assigningTask}
          users={workspaceUsers}
          busy={assignTask.isPending}
          onClose={() => setAssigningTask(null)}
          onAssign={(ownerId) => {
            const taskId = readValue(assigningTask, ["id", "task_id"]);
            if (taskId) assignTask.mutate({ taskId, ownerId });
          }}
        />
      )}
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
      <p className="text-xs text-white/40">{label}</p>
      <strong
        className={`mt-4 block font-display text-3xl font-semibold tracking-[-.05em] ${
          cool ? "text-cyan-100" : warm ? "text-amber-100" : "text-white"
        }`}
      >
        {value}
      </strong>
    </div>
  );
}

function TaskDetail({
  task,
  busy,
  onStatus,
  onEdit,
  onAssign,
}: {
  task: ApiRecord;
  busy: boolean;
  onStatus: (status: string) => void;
  onEdit: () => void;
  onAssign: () => void;
}) {
  const title = readValue(task, ["title", "name", "content"], "Untitled action");
  const status = readValue(task, ["status", "state"], "pending");
  const owner = readValue(task, ["owner_name", "assignee_name", "assigned_to"], "Unassigned");
  const due = readValue(task, ["due_date", "deadline", "due_at"], "No due date");
  const description = readValue(
    task,
    ["description", "details", "context"],
    "No additional context provided.",
  );
  const completed = status === "completed";
  const danger = status === "blocked" || status === "overdue";
  const statusIcon: ReactNode = completed ? (
    <Check size={14} />
  ) : danger ? (
    <AlertTriangle size={14} />
  ) : (
    <Circle size={14} />
  );
  const badgeClass = completed
    ? "border-emerald-200/20 bg-emerald-200/10 text-emerald-200"
    : danger
      ? "border-amber-200/20 bg-amber-200/10 text-amber-200"
      : "border-cyan-100/15 bg-cyan-100/[.04] text-cyan-100/60";

  return (
    <article className="grid gap-3 px-5 py-5 sm:px-6 md:grid-cols-[1fr_150px_140px_130px_90px] md:items-center md:gap-4">
      <div className="flex gap-3">
        <span
          className={`mt-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-xl border ${badgeClass}`}
        >
          {statusIcon}
        </span>
        <div className="min-w-0">
          <h3 className="text-sm font-medium text-white/80">{title}</h3>
          <p className="mt-1 line-clamp-2 text-xs leading-5 text-white/35">{description}</p>
          <span className="mt-2 inline-flex items-center gap-1 text-[10px] text-white/30 md:hidden">
            <UserRound size={11} /> {owner} · {due}
          </span>
        </div>
      </div>

      <div className="hidden items-center justify-between gap-2 text-xs text-white/45 md:flex">
        <span className="truncate flex items-center gap-1.5">
          <UserRound size={13} className="shrink-0 text-white/25" /> {owner}
        </span>
      </div>

      <span
        className={`hidden items-center gap-2 text-xs md:flex ${
          danger ? "text-amber-100/70" : "text-white/45"
        }`}
      >
        <Clock3 size={13} /> {due}
      </span>

      <label className="relative">
        <span className="sr-only">Update task status</span>
        <select
          value={status}
          disabled={busy}
          onChange={(event) => onStatus(event.target.value)}
          className="w-full appearance-none rounded-xl border border-white/10 bg-white/[.05] px-3 py-2 text-xs capitalize text-white/65 outline-none hover:border-white/20"
        >
          <option value="pending" className="bg-[#0e1726]">Pending</option>
          <option value="in_progress" className="bg-[#0e1726]">In progress</option>
          <option value="completed" className="bg-[#0e1726]">Completed</option>
          <option value="blocked" className="bg-[#0e1726]">Blocked</option>
          <option value="cancelled" className="bg-[#0e1726]">Cancelled</option>
        </select>
        <ArrowUpRight
          size={12}
          className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-white/25"
        />
      </label>

      <div className="flex items-center justify-end gap-1">
        <button
          title="Reassign owner"
          onClick={onAssign}
          className="rounded-lg p-1.5 text-white/30 hover:bg-white/10 hover:text-cyan-200 transition"
        >
          <UserCheck size={14} />
        </button>
        <button
          title="Edit task"
          onClick={onEdit}
          className="rounded-lg p-1.5 text-white/30 hover:bg-white/10 hover:text-white transition"
        >
          <Edit2 size={14} />
        </button>
      </div>
    </article>
  );
}

function EditTaskModal({
  task,
  busy,
  onClose,
  onSave,
}: {
  task: ApiRecord;
  busy: boolean;
  onClose: () => void;
  onSave: (payload: { title: string; description: string; dueDate?: string }) => void;
}) {
  const [title, setTitle] = useState(readValue(task, ["title", "name"], ""));
  const [description, setDescription] = useState(readValue(task, ["description"], ""));
  const [dueDate, setDueDate] = useState(readValue(task, ["due_date"], ""));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ title: title.trim(), description: description.trim(), dueDate: dueDate || undefined });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-md">
      <div className="df-app-card w-full max-w-lg rounded-[28px] p-6 sm:p-8">
        <div className="flex items-start justify-between border-b border-white/[.08] pb-4">
          <div>
            <p className="df-kicker">UPDATE ACTION</p>
            <h2 className="mt-1 font-display text-xl font-semibold text-white">Edit Task</h2>
          </div>
          <button onClick={onClose} className="rounded-xl p-1.5 text-white/40 hover:bg-white/10 hover:text-white transition">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-white/60 mb-2">Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="df-app-input w-full rounded-xl px-4 py-3 text-sm text-white"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-white/60 mb-2">Description</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="df-app-input w-full rounded-xl px-4 py-3 text-sm text-white resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-white/60 mb-2">Due Date</label>
            <input
              type="date"
              value={dueDate ? dueDate.split("T")[0] : ""}
              onChange={(e) => setDueDate(e.target.value)}
              className="df-app-input w-full rounded-xl px-4 py-3 text-sm text-white"
            />
          </div>

          <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-white/[.08]">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/70 hover:bg-white/5 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={busy || !title.trim()}
              className="df-pill-button text-xs"
            >
              {busy ? "Saving…" : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function AssignTaskModal({
  task,
  users,
  busy,
  onClose,
  onAssign,
}: {
  task: ApiRecord;
  users: ApiRecord[];
  busy: boolean;
  onClose: () => void;
  onAssign: (ownerId: string) => void;
}) {
  const currentOwnerId = readValue(task, ["owner_id"]);
  const [selectedOwnerId, setSelectedOwnerId] = useState(currentOwnerId);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-md">
      <div className="df-app-card w-full max-w-md rounded-[28px] p-6 sm:p-8">
        <div className="flex items-start justify-between border-b border-white/[.08] pb-4">
          <div>
            <p className="df-kicker">CHANGE RESPONSIBILITY</p>
            <h2 className="mt-1 font-display text-xl font-semibold text-white">Assign Task Owner</h2>
            <p className="mt-1 text-xs text-white/40 truncate max-w-xs">{readValue(task, ["title"])}</p>
          </div>
          <button onClick={onClose} className="rounded-xl p-1.5 text-white/40 hover:bg-white/10 hover:text-white transition">
            <X size={18} />
          </button>
        </div>

        <div className="mt-5 space-y-2 max-h-64 overflow-y-auto pr-1">
          {users.map((user) => {
            const userId = readValue(user, ["id"]);
            const userName = readValue(user, ["name"], "User");
            const userEmail = readValue(user, ["email"], "");
            const userRole = readValue(user, ["role"], "member");
            const isSelected = selectedOwnerId === userId;

            return (
              <button
                key={userId}
                type="button"
                onClick={() => setSelectedOwnerId(userId)}
                className={`w-full flex items-center justify-between rounded-xl p-3 text-left transition ${
                  isSelected ? "bg-cyan-400/15 border border-cyan-400/30" : "border border-white/5 bg-white/[.02] hover:bg-white/5"
                }`}
              >
                <div>
                  <p className="text-sm font-medium text-white">{userName}</p>
                  <p className="text-xs text-white/40">{userEmail} · {userRole}</p>
                </div>
                {isSelected && <Check size={16} className="text-cyan-300" />}
              </button>
            );
          })}
        </div>

        <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-white/[.08]">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-white/10 px-4 py-2.5 text-xs text-white/70 hover:bg-white/5 transition"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={busy || !selectedOwnerId || selectedOwnerId === currentOwnerId}
            onClick={() => selectedOwnerId && onAssign(selectedOwnerId)}
            className="df-pill-button text-xs disabled:opacity-40"
          >
            {busy ? "Assigning…" : "Assign Owner"}
          </button>
        </div>
      </div>
    </div>
  );
}
