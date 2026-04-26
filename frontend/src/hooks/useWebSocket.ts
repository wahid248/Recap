import { useEffect, useRef } from "react";
import type { LiveSegment } from "@/types";

const WS_URL = "ws://localhost:8420/ws";

export function useWebSocket(onSegment: (segment: LiveSegment) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const onSegmentRef = useRef(onSegment);
  const closedRef = useRef(false);
  onSegmentRef.current = onSegment;

  useEffect(() => {
    closedRef.current = false;

    function connect() {
      if (closedRef.current) return;
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data as string) as LiveSegment;
          onSegmentRef.current(data);
        } catch {
          // ignore malformed messages
        }
      };

      ws.onclose = () => {
        if (!closedRef.current) setTimeout(connect, 2000);
      };
    }

    connect();

    return () => {
      closedRef.current = true;
      wsRef.current?.close();
    };
  }, []);
}
