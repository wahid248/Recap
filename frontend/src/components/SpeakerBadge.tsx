const COLORS = [
  "bg-blue-600",
  "bg-purple-600",
  "bg-emerald-600",
  "bg-orange-600",
  "bg-pink-600",
  "bg-cyan-600",
];

function speakerColor(speaker: string): string {
  let hash = 0;
  for (let i = 0; i < speaker.length; i++) {
    hash = speaker.charCodeAt(i) + ((hash << 5) - hash);
  }
  return COLORS[Math.abs(hash) % COLORS.length];
}

interface Props {
  speaker: string;
}

export function SpeakerBadge({ speaker }: Props) {
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-semibold text-white ${speakerColor(speaker)}`}>
      {speaker}
    </span>
  );
}
