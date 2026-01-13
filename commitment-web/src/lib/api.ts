const API_BASE = "http://127.0.0.1:8000";

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const text = await res.text();

  if (!res.ok) {
  let message = "API error";

  try {
    const err = await res.json();

    if (typeof err.detail === "string") {
      message = err.detail;
    } else if (Array.isArray(err.detail)) {
      message = err.detail.map((e: any) => e.msg).join(", ");
    } else if (err.message) {
      message = err.message;
    }
  } catch {}

  throw new Error(message);
}


  return text ? JSON.parse(text) : ({} as T);
}
