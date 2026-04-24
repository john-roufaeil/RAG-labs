import React, { useEffect, useMemo, useRef, useState } from "react";
import { analyzeCase, clearSession, getSessionHistory } from "./api";

function formatTimestamp(timestamp) {
  if (!timestamp) return "";
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString();
}

export default function App() {
  const [textInput, setTextInput] = useState("");
  const [mriDescription, setMriDescription] = useState("");
  const [mriImage, setMriImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [clearing, setClearing] = useState(false);
  const [showClearModal, setShowClearModal] = useState(false);
  const [error, setError] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [memorySummary, setMemorySummary] = useState("");
  const [lastResult, setLastResult] = useState(null);
  const chatEndRef = useRef(null);

  const sessionId = useMemo(() => {
    const key = "medical-agent-session-id";
    let value = localStorage.getItem(key);
    if (!value) {
      value = "session-" + Math.random().toString(36).slice(2, 10);
      localStorage.setItem(key, value);
    }
    return value;
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  useEffect(() => {
    let active = true;
    async function loadHistory() {
      try {
        const data = await getSessionHistory(sessionId);
        if (!active) return;
        setChatHistory(data.chat_history || []);
        setMemorySummary(data.memory_summary || "");
      } catch {
        if (!active) return;
        setError("Could not load existing session history.");
      } finally {
        if (active) setLoadingHistory(false);
      }
    }
    loadHistory();
    return () => {
      active = false;
    };
  }, [sessionId]);

  const submit = async (event) => {
    event.preventDefault();
    setError("");

    if (mriImage && !mriDescription.trim()) {
      setError("MRI/scan description is required when an image is provided.");
      return;
    }

    setLoading(true);
    try {
      const data = await analyzeCase({ textInput, mriDescription, mriImage, sessionId });
      setChatHistory(data.chat_history || []);
      setMemorySummary(data.memory_summary || "");
      setLastResult(data);
      setTextInput("");
      setMriDescription("");
      setMriImage(null);
    } catch (submitError) {
      setError(submitError.message || "Failed to analyze case.");
    } finally {
      setLoading(false);
    }
  };

  const confirmClearChat = async () => {
    setError("");
    setClearing(true);
    try {
      await clearSession(sessionId);
      setChatHistory([]);
      setMemorySummary("");
      setLastResult(null);
      setShowClearModal(false);
    } catch (clearError) {
      setError(clearError.message || "Failed to clear session memory.");
    } finally {
      setClearing(false);
    }
  };

  return (
    <main className="container">
      <header className="topBar card">
        <div>
          <h1>Medical AI Assistant Agent</h1>
          <p className="muted">Session: {sessionId}</p>
        </div>
        <button
          className="danger"
          type="button"
          onClick={() => setShowClearModal(true)}
          disabled={clearing || loading}
        >
          {clearing ? "Clearing..." : "Clear Chat + Memory"}
        </button>
      </header>

      <p className="warning">This is not a medical diagnosis. Consult a doctor.</p>

      <section className="card chatCard">
        <h2>Chat History</h2>
        <div className="chatWindow">
          {loadingHistory ? (
            <p className="muted">Loading session history...</p>
          ) : chatHistory.length === 0 ? (
            <p className="muted">No messages yet. Start by describing symptoms and MRI findings.</p>
          ) : (
            chatHistory.map((message, index) => (
              <article key={`${message.timestamp}-${index}`} className={`bubble ${message.role === "assistant" ? "assistant" : "user"}`}>
                <div className="bubbleMeta">
                  <strong>{message.role === "assistant" ? "Assistant" : "You"}</strong>
                  <span>{formatTimestamp(message.timestamp)}</span>
                </div>
                <pre>{message.content}</pre>
              </article>
            ))
          )}
          <div ref={chatEndRef} />
        </div>
      </section>

      <form onSubmit={submit} className="card">
        <label>Symptoms (required)</label>
        <textarea
          required
          value={textInput}
          onChange={(event) => setTextInput(event.target.value)}
          placeholder="Example: severe headache and blurred vision, find nearest hospital in Beirut."
        />

        <label>MRI/Scan Description (required when image is uploaded)</label>
        <textarea
          required={Boolean(mriImage)}
          value={mriDescription}
          onChange={(event) => setMriDescription(event.target.value)}
          placeholder="Example: T2 hyperintense lesion with mild edema in temporal lobe."
        />

        <label>MRI/Scan Image (optional upload)</label>
        <input type="file" accept="image/*" onChange={(event) => setMriImage(event.target.files?.[0] || null)} />

        <button type="submit" disabled={loading || clearing}>{loading ? "Analyzing..." : "Send"}</button>
      </form>

      <section className="card resultGrid">
        <div>
          <h3>Memory Summary</h3>
          <p>{memorySummary || "No summarization needed yet."}</p>
        </div>

        <div>
          <h3>MRI Interpretation</h3>
          {lastResult?.mri_interpretation?.length ? (
            <ul>{lastResult.mri_interpretation.map((item, index) => <li key={index}>{item}</li>)}</ul>
          ) : (
            <p className="muted">Submit a case to view MRI interpretation.</p>
          )}
        </div>

        <div>
          <h3>Tool Decisions</h3>
          {lastResult?.tool_decisions ? (
            <ul>
              {Object.entries(lastResult.tool_decisions).map(([name, used]) => (
                <li key={name}>{name}: {used ? "used" : "skipped"}</li>
              ))}
            </ul>
          ) : (
            <p className="muted">No tool decision yet.</p>
          )}
        </div>
      </section>

      {error ? <p className="error">{error}</p> : null}

      {showClearModal ? (
        <div className="modalBackdrop" role="dialog" aria-modal="true" aria-labelledby="clear-modal-title">
          <div className="modalCard">
            <h3 id="clear-modal-title">Clear this session?</h3>
            <p>This will remove chat history and summarized memory for the current session.</p>
            <div className="modalActions">
              <button type="button" className="secondary" onClick={() => setShowClearModal(false)} disabled={clearing}>
                Cancel
              </button>
              <button type="button" className="danger" onClick={confirmClearChat} disabled={clearing}>
                {clearing ? "Clearing..." : "Confirm Clear"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}
