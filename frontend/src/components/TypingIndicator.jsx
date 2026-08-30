export default function TypingIndicator({ t }) {
  return (
    <div className="msg-row msg-row--ai" role="status" aria-label={t.typing}>
      <div className="msg-avatar msg-avatar--ai" aria-hidden="true">🤖</div>
      <div className="msg-group">
        <div className="msg-bubble msg-bubble--ai typing-bubble">
          <div className="typing-dots" aria-hidden="true">
            <span /><span /><span />
          </div>
          <span className="typing-label">{t.typing}</span>
        </div>
      </div>
    </div>
  );
}
