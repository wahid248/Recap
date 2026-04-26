import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { StatusIndicator } from "@/components/StatusIndicator";
import { SummaryCard } from "@/components/SummaryCard";
import { TranscriptView } from "@/components/TranscriptView";
import { api } from "@/services/api";
import type { MeetingDetail as MeetingDetailType } from "@/types";

export function MeetingDetail() {
  const { id } = useParams<{ id: string }>();
  const [meeting, setMeeting] = useState<MeetingDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [summarizing, setSummarizing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!id) return;
    try {
      setMeeting(await api.getMeeting(id));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load meeting");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleSummarize() {
    if (!id) return;
    setSummarizing(true);
    try {
      await api.summarizeMeeting(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Summarization failed");
    } finally {
      setSummarizing(false);
    }
  }

  if (loading) return <div className="p-6 text-gray-400">Loading...</div>;
  if (error) return <div className="p-6 text-red-400">{error}</div>;
  if (!meeting) return null;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center gap-4">
        <Link to="/history" className="text-gray-400 hover:text-white">
          ←
        </Link>
        <div className="min-w-0 flex-1">
          <h1 className="truncate text-xl font-semibold text-white">{meeting.title}</h1>
          <p className="text-xs text-gray-400">{new Date(meeting.started_at).toLocaleString()}</p>
        </div>
        <StatusIndicator status={meeting.status} />
      </div>

      {meeting.summary ? (
        <SummaryCard summary={meeting.summary} />
      ) : (
        <button
          onClick={handleSummarize}
          disabled={summarizing || meeting.status !== "completed"}
          className="self-start rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
        >
          {summarizing ? "Generating summary..." : "Generate Summary"}
        </button>
      )}

      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-gray-400">
          Transcript
        </h2>
        <div className="rounded-xl bg-gray-900 p-4">
          <TranscriptView segments={meeting.segments} />
        </div>
      </div>
    </div>
  );
}
