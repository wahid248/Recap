type Status = "recording" | "processing" | "completed" | "idle";

const CONFIG: Record<Status, { color: string; label: string; pulse: boolean }> = {
  recording: { color: "bg-red-500", label: "Recording", pulse: true },
  processing: { color: "bg-yellow-500", label: "Processing", pulse: true },
  completed: { color: "bg-green-500", label: "Completed", pulse: false },
  idle: { color: "bg-gray-500", label: "Idle", pulse: false },
};

interface Props {
  status: Status;
}

export function StatusIndicator({ status }: Props) {
  const { color, label, pulse } = CONFIG[status];
  return (
    <div className="flex items-center gap-2">
      <span className={`inline-block h-2.5 w-2.5 rounded-full ${color} ${pulse ? "animate-pulse" : ""}`} />
      <span className="text-sm text-gray-400">{label}</span>
    </div>
  );
}
