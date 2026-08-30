import { useState } from "react";

/* ----------------------------------------------------------------
   Lightweight markdown → HTML converter
   Handles: **bold**, ## headings, - bullets, tables, line breaks
   ---------------------------------------------------------------- */
function renderMarkdown(raw) {
  if (!raw) return "";
  const lines = raw.split("\n");
  const output = [];
  let tableBuffer = [];
  let listBuffer = [];

  const flushList = () => {
    if (listBuffer.length) {
      output.push(`<ul>${listBuffer.map((l) => `<li>${l}</li>`).join("")}</ul>`);
      listBuffer = [];
    }
  };

  const flushTable = () => {
    if (tableBuffer.length) {
      const rows = tableBuffer.filter((r) => !/^\|[-:\s|]+\|$/.test(r.trim()));
      const html = rows.map((row, i) => {
        const cells = row
          .split("|")
          .filter(Boolean)
          .map((c) => c.trim());
        const tag = i === 0 ? "th" : "td";
        return `<tr>${cells.map((c) => `<${tag}>${applyInline(c)}</${tag}>`).join("")}</tr>`;
      });
      output.push(`<table class="msg-table"><tbody>${html.join("")}</tbody></table>`);
      tableBuffer = [];
    }
  };

  const applyInline = (t) =>
    t
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(
        /`([^`]+)`/g,
        `<code style="font-family:monospace;background:rgba(37,99,235,0.07);padding:1px 5px;border-radius:4px;font-size:0.85em">$1</code>`
      );

  for (const line of lines) {
    const trimmed = line.trim();

    // Table row
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      flushList();
      tableBuffer.push(trimmed);
      continue;
    } else {
      flushTable();
    }

    // Headings
    if (trimmed.startsWith("### ")) {
      flushList();
      output.push(`<h3>${applyInline(trimmed.slice(4))}</h3>`);
      continue;
    }
    if (trimmed.startsWith("## ")) {
      flushList();
      output.push(`<h2>${applyInline(trimmed.slice(3))}</h2>`);
      continue;
    }
    if (trimmed.startsWith("# ")) {
      flushList();
      output.push(`<h2>${applyInline(trimmed.slice(2))}</h2>`);
      continue;
    }

    // Bullets
    if (trimmed.startsWith("- ") || trimmed.startsWith("• ")) {
      listBuffer.push(applyInline(trimmed.slice(2)));
      continue;
    } else {
      flushList();
    }

    // Empty line → paragraph break
    if (!trimmed) {
      output.push("<br/>");
      continue;
    }

    output.push(`<p>${applyInline(trimmed)}</p>`);
  }

  flushList();
  flushTable();

  return output.join("");
}

export default function MessageBubble({ msg, t, roleMeta, onInspectCitation, onOpenFeedback, language }) {
  const [copied, setCopied] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const isUser = msg.role === "user";

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSpeak = () => {
    if (!("speechSynthesis" in window)) return;
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    } else {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(msg.text.replace(/[*#`|]/g, ""));
      utterance.lang = language === "hi" ? "hi-IN" : language === "kn" ? "kn-IN" : "en-US";
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
      setIsSpeaking(true);
    }
  };

  return (
    <div
      className={`msg-row ${isUser ? "msg-row--user" : "msg-row--ai"}`}
      role="article"
      aria-label={isUser ? "Your message" : "AI response"}
    >
      {!isUser && (
        <div className="msg-avatar msg-avatar--ai" aria-hidden="true">
          AI
        </div>
      )}

      <div className="msg-group">
        <div className={`msg-bubble ${isUser ? "msg-bubble--user" : "msg-bubble--ai"}`}>
          {isUser ? (
            <p className="msg-text">{msg.text}</p>
          ) : (
            <>
              <div
                className="msg-text msg-text--ai"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
              />

              {/* Message Action Toolbar */}
              <div className="msg-actions-toolbar">
                <button
                  className="msg-action-btn"
                  onClick={handleSpeak}
                  title={isSpeaking ? "Stop Voice Narration" : "Read Aloud"}
                >
                  {isSpeaking ? "Stop" : "Listen"}
                </button>

                <button
                  className="msg-action-btn"
                  onClick={handleCopy}
                  title="Copy text to clipboard"
                >
                  {copied ? "Copied" : "Copy"}
                </button>

                <button
                  className="msg-action-btn"
                  onClick={() => onOpenFeedback && onOpenFeedback("AI Answer", "Thumbs Up (Helpful)", msg.text)}
                  title="Mark response as helpful"
                >
                  Helpful
                </button>

                <button
                  className="msg-action-btn"
                  onClick={() => onOpenFeedback && onOpenFeedback("AI Answer", "Thumbs Down (Not Helpful)", msg.text)}
                  title="Mark response as not helpful"
                >
                  Not helpful
                </button>

                <button
                  className="msg-action-btn report-flag-btn"
                  onClick={() => onOpenFeedback && onOpenFeedback("AI Answer", "Information Outdated", msg.text)}
                  title="Report outdated info or suggest an update"
                >
                  Report
                </button>
              </div>
            </>
          )}
        </div>

        {/* Meta: timestamp + confidence */}
        <div className={`msg-meta ${isUser ? "msg-meta--right" : "msg-meta--left"}`}>
          <time className="msg-timestamp" dateTime={msg.timestamp}>
            {msg.timestamp}
          </time>
          {!isUser && (
            <span
              className={`confidence-chip ${
                msg.confidence === "high"
                  ? "confidence-chip--high"
                  : msg.confidence === "medium" || msg.confidence === "moderate"
                  ? "confidence-chip--moderate"
                  : msg.confidence === "low"
                  ? "confidence-chip--low"
                  : "confidence-chip--no-evidence"
              }`}
              role="note"
            >
              {msg.confidence === "high"
                ? "High confidence — official source"
                : msg.confidence === "medium" || msg.confidence === "moderate"
                ? "Medium confidence"
                : msg.confidence === "low"
                ? "Low confidence"
                : "No reliable evidence found"}
            </span>
          )}
        </div>

        {/* AI-to-Community Bridge Button & Demand Signal (When evidence is Low or Missing) */}
        {!isUser && (msg.confidence === "no_evidence" || msg.confidence === "low" || msg.text?.includes("couldn't find reliable")) && (
          <div className="ai-community-bridge-wrap">
            <div className="demand-signal-pill">
              🔥 <strong>This question has been asked by {msg.demand_count ?? msg.question_count ?? 0} students.</strong>
            </div>
            <button
              className="ai-community-bridge-btn"
              onClick={() => {
                const event = new CustomEvent("open_handoff_modal", { detail: { prompt: msg.text } });
                window.dispatchEvent(event);
              }}
            >
              💬 Ask the Student Community →
            </button>
          </div>
        )}

        {/* Provenance & Attribution Banner — only shown when there's a real
            source/citation behind it; never fabricate a document name */}
        {!isUser && (
          <div className="provenance-banner-block">
            {msg.confidenceType === "community_grounded" ? (
              <div
                className="provenance-community-pill"
                onClick={() =>
                  onInspectCitation &&
                  onInspectCitation({
                    sources: msg.sources,
                    citations: msg.citations,
                    confidence: msg.confidence,
                    confidenceType: msg.confidenceType,
                    messageText: msg.text,
                  })
                }
              >
                <span className="prov-icon">🟡</span>
                <span className="prov-text">
                  <strong>Community Insight</strong> • Based on {msg.response_count ?? msg.sample_size ?? 0} student responses
                </span>
                <span className="prov-link">Inspect →</span>
              </div>
            ) : msg.sources?.length > 0 ? (
              <div className="inst-trust-card">
                <div className="inst-meta-grid">
                  <div className="inst-meta-row">
                    <span className="inst-meta-label">📄 Source:</span>
                    <span className="inst-meta-val">{msg.sources[0]}</span>
                  </div>
                  <div className="inst-meta-row">
                    <span className="inst-meta-label">🟢 Confidence:</span>
                    <span className="inst-meta-val highlight-green">
                      {msg.confidence === "high" ? "High (Official Source Confirmed)" : "Medium Grounding"}
                    </span>
                  </div>
                </div>

                <button
                  className="inst-view-source-btn"
                  onClick={() =>
                    onInspectCitation &&
                    onInspectCitation({
                      sources: msg.sources,
                      citations: msg.citations,
                      confidence: msg.confidence,
                      confidenceType: msg.confidenceType,
                      messageText: msg.text,
                    })
                  }
                >
                  View Source 🔍
                </button>
              </div>
            ) : null}
          </div>
        )}
      </div>

      {isUser && (
        <div className="msg-avatar msg-avatar--user" aria-hidden="true">
          {roleMeta?.icon || "👤"}
        </div>
      )}
    </div>
  );
}
