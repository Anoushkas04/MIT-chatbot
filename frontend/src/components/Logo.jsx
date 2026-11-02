/**
 * Logo — Mitra brand mark
 * Renders the "M" badge + "MITra" wordmark.
 * light prop: use on dark/green backgrounds
 */
export default function Logo({ light = false, size = "md" }) {
  const sizes = {
    sm: { badge: 22, font: 16, gap: 7 },
    md: { badge: 28, font: 22, gap: 9 },
    lg: { badge: 36, font: 28, gap: 11 },
  };
  const s = sizes[size] || sizes.md;

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: s.gap,
        fontSize: s.font,
        fontWeight: 800,
        letterSpacing: "-0.07em",
        color: light ? "#f9faf5" : "#234f4a",
        userSelect: "none",
      }}
    >
      {/* Badge mark */}
      <span
        style={{
          display: "grid",
          placeItems: "center",
          width: s.badge,
          height: s.badge,
          background: "#d8ef68",
          color: "#234f4a",
          borderRadius: "9px 4px 9px 4px",
          fontSize: s.badge * 0.57,
          fontWeight: 800,
          letterSpacing: "-0.1em",
          flexShrink: 0,
        }}
      >
        M
      </span>

      {/* Wordmark */}
      <span>
        MIT
        <span style={{ color: "#e07b64" }}>ra</span>
      </span>
    </div>
  );
}
