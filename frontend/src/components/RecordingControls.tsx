import { StatusIndicator } from "./StatusIndicator";

interface Props {
  isRecording: boolean;
  onStart: () => void;
  onStop: () => void;
  disabled?: boolean;
  error?: string | null;
}

export function RecordingControls({ isRecording, onStart, onStop, disabled, error }: Props) {
  return (
    <div className="flex flex-col items-center gap-3">
      <StatusIndicator status={isRecording ? "recording" : "idle"} />
      <button
        onClick={isRecording ? onStop : onStart}
        disabled={disabled}
        className={`rounded-full px-8 py-3 font-semibold text-white transition-colors disabled:opacity-50 ${
          isRecording ? "bg-red-600 hover:bg-red-500" : "bg-blue-600 hover:bg-blue-500"
        }`}
      >
        {isRecording ? "Stop Recording" : "Start Recording"}
      </button>
      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  );
}
