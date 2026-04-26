import { useCallback, useEffect, useState } from "react";
import { api } from "@/services/api";
import type { Meeting } from "@/types";

export function useMeetings() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      setMeetings(await api.getMeetings());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load meetings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const deleteMeeting = useCallback(
    async (id: string) => {
      await api.deleteMeeting(id);
      await refresh();
    },
    [refresh],
  );

  return { meetings, loading, error, refresh, deleteMeeting };
}
