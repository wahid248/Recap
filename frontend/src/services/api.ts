import type { Meeting, MeetingDetail, Summary } from "@/types";

const BASE = "http://localhost:8420";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getMeetings: () => request<Meeting[]>("/meetings/"),

  getMeeting: (id: string) => request<MeetingDetail>(`/meetings/${id}`),

  deleteMeeting: (id: string) =>
    request<{ status: string }>(`/meetings/${id}`, { method: "DELETE" }),

  getCaptureStatus: () =>
    request<{ is_recording: boolean; meeting_id: string | null; started_at: string | null }>(
      "/capture/status"
    ),

  startCapture: () =>
    request<{ meeting_id: string; started_at: string }>("/capture/start", {
      method: "POST",
    }),

  stopCapture: () =>
    request<{ meeting_id: string; status: string }>("/capture/stop", {
      method: "POST",
    }),

  summarizeMeeting: (id: string) =>
    request<Summary>(`/meetings/${id}/summarize`, { method: "POST" }),
};
