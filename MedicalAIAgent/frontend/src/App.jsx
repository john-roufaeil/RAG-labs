import React, { useMemo, useState } from "react";
import { analyzeCase } from "./api";

export default function App() {
  const [textInput, setTextInput] = useState("");
  const [mriDescription, setMriDescription] = useState("");
  const [mriImage, setMriImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const sessionId = useMemo(() => {
    const key = "medical-agent-session-id";
    let id = localStorage.getItem(key);
    if (!id) {
      id = "session-" + Math.random().toString(36).slice(2, 10);
      localStorage.setItem(key, id);
    }
    return id;
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const data = await analyzeCase({ textInput, mriDescription, mriImage, sessionId });
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container">
      <h1>Medical AI Assistant Agent</h1>
      <p className="muted">This is not a medical diagnosis. Consult a doctor.</p>

      <form onSubmit={submit} className="card">
        <label>Symptoms (required)</label>
        <textarea required value={textInput} onChange={(e) => setTextInput(e.target.value)}
          placeholder="Example: severe headache, nausea, and blurred vision. Find nearby hospital in Beirut." />
        <label>MRI/Scan Description (optional)</label>
        <textarea value={mriDescription} onChange={(e) => setMriDescription(e.target.value)}
          placeholder="Example: T2 hyperintense lesion in right temporal lobe..." />
        <label>MRI/Scan File (optional image upload)</label>
        <input type="file" accept="image/*" onChange={(e) => setMriImage(e.target.files?.[0] || null)} />
        <button disabled={loading}>{loading ? "Analyzing..." : "Analyze Case"}</button>
      </form>

      {result && (
        <section className="card">
          {"error" in result ? (
            <p className="error">{result.error}</p>
          ) : (
            <>
              <h2>Case Summary</h2>
              <p>{result.case_summary}</p>
              <h3>Safe Insights</h3>
              <ul>{result.safe_insights.map((s, i) => <li key={i}>{s}</li>)}</ul>
              <h3>Tools Used</h3>
              <p>{result.tools_used.join(", ")}</p>
              <h3>Nearby Hospitals</h3>
              {result.hospital_results.length === 0 ? <p>No search performed or no results.</p> : (
                <ul>{result.hospital_results.map((h, i) => <li key={i}>{h.name} — {h.address}</li>)}</ul>
              )}
              <h3>Memory Summary</h3>
              <p>{result.memory_summary || "(not needed yet)"}</p>
              <p className="muted">{result.disclaimer}</p>
            </>
          )}
        </section>
      )}
    </main>
  );
}
