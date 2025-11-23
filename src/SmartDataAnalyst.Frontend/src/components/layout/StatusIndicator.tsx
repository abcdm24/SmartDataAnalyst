import React, { useEffect, useState } from "react";
import apiClient from "../../api/apiClient";
import { useAppContext } from "../../context/AppContext";

// interface StatusProps {
//   filename?: string;
// }

// const StatusIndicator: React.FC<StatusProps> = ({ filename }) => {
const StatusIndicator: React.FC = () => {
  const { currentFilename } = useAppContext();
  const [status, setStatus] = useState("not_initialized");

  useEffect(() => {
    if (!currentFilename) return;

    const ws = new WebSocket(
      `${
        import.meta.env.VITE_WS_BASE_URL
      }/data/ws/agent-status?filename=${currentFilename}`
    );

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data.status);
    };

    ws.onclose = () => console.log("Status socket closed");
    ws.onerror = () => console.log("WebSocket error");

    const interval = setInterval(async () => {
      try {
        console.log(`Calling StatusIndicator: ${currentFilename}`);
        const res = await apiClient.get(
          `data/agent-status?filename=${currentFilename}`
        );

        console.log(`Status: ${res.data.status}`);
        setStatus(res.data.status);
      } catch {
        setStatus("not_initialized");
      }
    }, 2000);
    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, [currentFilename]);

  // if (status === "summarizing" || status === "analyzing") {
  //   alert(`status: ${status}`);
  // }

  const renderStatusBadge = () => {
    switch (status) {
      case "processing":
        return <span className="badge bg-primary pulse">⚙️ Processing...</span>;
      case "active":
        return <span className="badge bg-wraning pulse">🧠 AI Active</span>;
      case "summarizing":
        return (
          <span className="badge bg-wraning pulse">📝 Summarizing...</span>
        );
      case "analyzing":
        return <span className="badge bg-primary pulse">⚙️ Analyzing...</span>;
      case "idle":
        return <span className="badge bg-success pulse">✅ Idle</span>;
      default:
        return (
          <span className="badge bg-secondary pulse">⚪ Not Initialized</span>
        );
    }
  };

  return (
    <div className="d-flex align-items-center gap-2 text-white">
      {renderStatusBadge()}
    </div>
  );
};

export default StatusIndicator;
