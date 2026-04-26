import type { Summary } from "@/types";

interface Props {
  summary: Summary;
}

export function SummaryCard({ summary }: Props) {
  return (
    <div className="space-y-4 rounded-xl bg-gray-800 p-5">
      <div>
        <h3 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-400">
          Overview
        </h3>
        <p className="text-sm text-gray-200">{summary.overview}</p>
      </div>

      {summary.key_points.length > 0 && (
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
            Key Points
          </h3>
          <ul className="space-y-1">
            {summary.key_points.map((point, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-200">
                <span className="shrink-0 text-blue-400">•</span>
                {point}
              </li>
            ))}
          </ul>
        </div>
      )}

      {summary.action_items.length > 0 && (
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">
            Action Items
          </h3>
          <ul className="space-y-1">
            {summary.action_items.map((item, i) => (
              <li key={i} className="flex gap-2 text-sm text-gray-200">
                <span className="shrink-0 text-emerald-400">✓</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
