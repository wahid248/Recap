import { useCallback, useState } from "react";
import { RecordingControls } from "@/components/RecordingControls";
import { TranscriptView } from "@/components/TranscriptView";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { LiveSegment, RecordingState } from "@/types";

interface Props {
  recording: RecordingState & { start: () => Promise<void>; stop: () => Promise<void>; error: string | null };
}

export function LiveSession({ recording }: Props) {
  const [segments, setSegments] = useState<LiveSegment[]>([]);
  const { isRecording, start, stop, error } = recording;

  const handleSegment = useCallback((seg: LiveSegment) => {
    setSegments((prev) => [...prev, seg]);
  }, []);

  useWebSocket(handleSegment);

  function handleStart() {
    setSegments([]);
    start();
  }

  return (
    <div className="flex h-full flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">Live Session</h1>
        <RecordingControls
          isRecording={isRecording}
          onStart={handleStart}
          onStop={stop}
          error={error}
        />
      </div>
      <div className="flex-1 overflow-y-auto rounded-xl bg-gray-900 p-4">
        <TranscriptView segments={segments} autoScroll />
      </div>
    </div>
  );
}
