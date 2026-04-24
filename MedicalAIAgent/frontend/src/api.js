const API_BASE = "http://localhost:8000";

export async function analyzeCase(payload) {
  const form = new FormData();
  form.append("text_input", payload.textInput);
  form.append("mri_description", payload.mriDescription || "");
  form.append("session_id", payload.sessionId);
  if (payload.mriImage) form.append("mri_image", payload.mriImage);

  const res = await fetch(`${API_BASE}/api/analyze-case`, {
    method: "POST",
    body: form
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}
