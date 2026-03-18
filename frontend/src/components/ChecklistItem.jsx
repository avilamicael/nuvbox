export default function ChecklistItem({ item, checked, expandedNote, onToggle, onToggleNote, sectionColor }) {
  return (
    <div style={{
      borderLeft: `3px solid ${checked ? sectionColor + "60" : "#30363D"}`,
      background: checked ? "rgba(22,27,34,0.5)" : "#1C2128",
      marginBottom: 1,
      transition: "all 0.15s",
    }}>
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: 12,
          padding: "14px 20px",
          cursor: "pointer",
        }}
        onClick={() => onToggle(item.id)}
      >
        {/* Checkbox */}
        <div style={{
          width: 18,
          height: 18,
          border: `1px solid ${checked ? sectionColor : "#30363D"}`,
          background: checked ? sectionColor : "transparent",
          borderRadius: 2,
          flexShrink: 0,
          marginTop: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "all 0.15s",
        }}>
          {checked && <span style={{ fontSize: 11, color: "#0D1117", fontWeight: 900 }}>✓</span>}
        </div>

        {/* Text */}
        <div style={{ flex: 1 }}>
          <span style={{
            fontSize: 14,
            color: checked ? "#6E7681" : "#E6EDF3",
            textDecoration: checked ? "line-through" : "none",
            lineHeight: 1.5,
          }}>
            {item.text}
          </span>

          {/* Note toggle button */}
          {item.note && (
            <button
              onClick={(e) => { e.stopPropagation(); onToggleNote(item.id); }}
              style={{
                marginLeft: 10,
                fontSize: 10,
                letterSpacing: 1,
                color: expandedNote ? sectionColor : "#30363D",
                background: "transparent",
                border: `1px solid ${expandedNote ? sectionColor + "40" : "#30363D"}`,
                padding: "1px 6px",
                borderRadius: 2,
                cursor: "pointer",
                fontFamily: "inherit",
                verticalAlign: "middle",
              }}
            >
              {expandedNote ? "▲ NOTA" : "▼ NOTA"}
            </button>
          )}
        </div>
      </div>

      {/* Note expanded */}
      {item.note && expandedNote && (
        <div style={{
          margin: "0 20px 12px 50px",
          padding: "10px 14px",
          background: "rgba(0,0,0,0.3)",
          borderLeft: `2px solid ${sectionColor}30`,
          fontSize: 12,
          color: "#8B949E",
          lineHeight: 1.7,
          borderRadius: "0 2px 2px 0",
        }}>
          <span style={{ color: sectionColor, fontSize: 9, letterSpacing: 2, marginRight: 8 }}>NOTA</span>
          {item.note}
        </div>
      )}
    </div>
  );
}
