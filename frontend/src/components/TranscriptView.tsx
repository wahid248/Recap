import { useEffect, useRef } from "react";
import { SpeakerBadge } from "./SpeakerBadge";
import type { LiveSegment, Segment } from "@/types";

interface Props {
  segments: (Segment | LiveSegment)[];
  autoScroll?: boolean;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60).toString().padStart(2, "0");
  const s = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

export function TranscriptView({ segments, autoScroll = false }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [segments, autoScroll]);

  if (segments.length === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-gray-500">
        No transcript yet
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {segments.map((seg, i) => (
        <div key={"id" in seg ? seg.id : i} className="flex gap-3">
          <span className="mt-0.5 w-10 shrink-0 text-right text-xs text-gray-500">
            {formatTime(seg.start_time)}
          </span>
          <div className="flex-1">
            <SpeakerBadge speaker={seg.speaker} />
            <p className="mt-1 text-sm text-gray-200">{seg.text}</p>
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
