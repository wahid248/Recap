import { useCallback, useEffect, useState } from "react";
import { api } from "@/services/api";
import type { RecordingState } from "@/types";

const INITIAL: RecordingState = { isRecording: false, meetingId: null, startedAt: null };

export function useRecording() {
  const [state, setState] = useState<RecordingState>(INITIAL);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getCaptureStatus().then((s) => {
      if (s.is_recording) {
        setState({ isRecording: true, meetingId: s.meeting_id, startedAt: s.started_at });
      }
    }).catch(() => {});
  }, []);

  const start = useCallback(async () => {
    try {
      const res = await api.startCapture();
      setState({ isRecording: true, meetingId: res.meeting_id, startedAt: res.started_at });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start recording");
    }
  }, []);

  const stop = useCallback(async () => {
    try {
      await api.stopCapture();
      setState(INITIAL);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to stop recording");
    }
  }, []);

  return { ...state, start, stop, error };
}
