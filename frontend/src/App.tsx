import { BrowserRouter, Navigate, NavLink, Route, Routes } from "react-router-dom";
import { useRecording } from "@/hooks/useRecording";
import { LiveSession } from "@/pages/LiveSession";
import { MeetingDetail } from "@/pages/MeetingDetail";
import { MeetingHistory } from "@/pages/MeetingHistory";

function NavItem({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
          isActive ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white"
        }`
      }
    >
      {label}
    </NavLink>
  );
}

export default function App() {
  const recording = useRecording();

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-950 text-white">
        <nav className="flex w-48 shrink-0 flex-col gap-1 border-r border-gray-800 p-4 pt-8">
          <span className="mb-4 px-3 text-lg font-bold text-white">Recap</span>
          <NavItem to="/live" label="Live Session" />
          <NavItem to="/history" label="History" />
        </nav>
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/live" replace />} />
            <Route path="/live" element={<LiveSession recording={recording} />} />
            <Route path="/history" element={<MeetingHistory />} />
            <Route path="/meetings/:id" element={<MeetingDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
