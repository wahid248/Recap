export interface Meeting {
  id: string;
  title: string;
  started_at: string;
  ended_at: string | null;
  status: "recording" | "processing" | "completed";
}

export interface Segment {
  id: string;
  meeting_id: string;
  speaker: string;
  text: string;
  start_time: number;
  end_time: number;
  confidence: number | null;
}

export interface Summary {
  overview: string;
  key_points: string[];
  action_items: string[];
  generated_at: string;
}

export interface MeetingDetail extends Meeting {
  segments: Segment[];
  summary: Summary | null;
}

export interface LiveSegment {
  speaker: string;
  text: string;
  start_time: number;
  end_time: number;
  confidence: number;
}

export interface RecordingState {
  isRecording: boolean;
  meetingId: string | null;
  startedAt: string | null;
}
