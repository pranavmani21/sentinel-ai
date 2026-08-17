"use client";

import { useEffect, useState } from "react";

type Health = "checking" | "online" | "offline";

export function HealthStatus() {
  const [health, setHealth] = useState<Health>("checking");

  useEffect(() => {
    const controller = new AbortController();
    const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

    fetch(`${baseUrl}/health`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        setHealth("online");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setHealth("offline");
      });

    return () => controller.abort();
  }, []);

  return (
    <div className={`status ${health}`} role="status">
      <span /> API {health}
    </div>
  );
}

