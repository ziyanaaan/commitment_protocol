const API_BASE = "http://127.0.0.1:8000";

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  // Get auth token from sessionStorage (same key as auth.ts)
  const token = typeof window !== "undefined" ? sessionStorage.getItem("pledgos_access_token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  // Add Authorization header if token exists
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const text = await res.text();

  if (!res.ok) {
    let message = "API error";

    try {
      // Parse the already-read text, not the response again
      const err = JSON.parse(text);

      if (typeof err.detail === "string") {
        message = err.detail;
      } else if (err.detail?.message) {
        message = err.detail.message;
      } else if (Array.isArray(err.detail)) {
        message = err.detail.map((e: { msg: string }) => e.msg).join(", ");
      } else if (err.error) {
        message = err.error;
      } else if (err.message) {
        message = err.message;
      }

    } catch {
      // If JSON parsing fails, use the raw text
      message = text || `API error (${res.status})`;
    }

    throw new Error(message);
  }

  return text ? JSON.parse(text) : ({} as T);
}
