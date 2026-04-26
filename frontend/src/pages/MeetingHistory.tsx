import { useState } from "react";
import { Link } from "react-router-dom";
import { SearchBar } from "@/components/SearchBar";
import { StatusIndicator } from "@/components/StatusIndicator";
import { useMeetings } from "@/hooks/useMeetings";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function MeetingHistory() {
  const { meetings, loading, error, deleteMeeting } = useMeetings();
  const [query, setQuery] = useState("");

  const filtered = query
    ? meetings.filter((m) => m.title.toLowerCase().includes(query.toLowerCase()))
    : meetings;

  if (loading) return <div className="p-6 text-gray-400">Loading...</div>;
  if (error) return <div className="p-6 text-red-400">{error}</div>;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">Meeting History</h1>
        <span className="text-sm text-gray-400">{meetings.length} meetings</span>
      </div>
      <SearchBar onSearch={setQuery} />
      {filtered.length === 0 ? (
        <div className="py-12 text-center text-gray-500">No meetings found</div>
      ) : (
        <ul className="space-y-2">
          {filtered.map((m) => (
            <li key={m.id} className="flex items-center gap-4 rounded-xl bg-gray-800 px-4 py-3">
              <StatusIndicator status={m.status} />
              <Link to={`/meetings/${m.id}`} className="min-w-0 flex-1">
                <p className="truncate font-medium text-white">{m.title}</p>
                <p className="text-xs text-gray-400">{formatDate(m.started_at)}</p>
              </Link>
              <button
                onClick={() => deleteMeeting(m.id)}
                className="shrink-0 text-xs text-gray-500 hover:text-red-400"
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
