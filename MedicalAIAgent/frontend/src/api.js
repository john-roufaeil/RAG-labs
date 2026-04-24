const API_BASE = "http://localhost:8000";

export async function analyzeCase(payload) {
  const form = new FormData();
  form.append("text_input", payload.textInput);
  form.append("mri_description", payload.mriDescription || "");
  form.append("session_id", payload.sessionId);
  if (payload.mriImage) form.append("mri_image", payload.mriImage);

  const response = await fetch(`${API_BASE}/api/analyze-case`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}

export async function getSessionHistory(sessionId) {
  const response = await fetch(`${API_BASE}/api/session-history/${encodeURIComponent(sessionId)}`);
  if (!response.ok) throw new Error(`History request failed: ${response.status}`);
  return response.json();
}

export async function clearSession(sessionId) {
  const response = await fetch(`${API_BASE}/api/session/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error(`Clear session failed: ${response.status}`);
  return response.json();
}
