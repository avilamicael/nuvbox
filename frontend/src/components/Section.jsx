import ChecklistItem from "./ChecklistItem";

export default function Section({ section, checked, isOpen, expandedNotes, filter, onToggleSection, onToggleItem, onToggleNote }) {
  const items = section.groups.flatMap(g => g.items);
  const done = items.filter(i => checked[i.id]).length;
  const total = items.length;
  const pct = Math.round((done / total) * 100);

  return (
    <div style={{ marginBottom: 16 }}>
      {/* Section Header */}
      <button
        onClick={() => onToggleSection(section.id)}
        style={{
          width: "100%",
          background: "rgba(22,27,34,0.9)",
          border: `1px solid ${isOpen ? section.color + "40" : "#30363D"}`,
          borderLeft: `3px solid ${section.color}`,
          padding: "16px 20px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderRadius: "0 4px 4px 0",
          transition: "all 0.2s",
          fontFamily: "inherit",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 16 }}>{section.icon}</span>
          <span style={{ fontSize: 11, letterSpacing: 3, color: section.color, fontWeight: 700 }}>
            {section.label}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 80, height: 2, background: "#30363D", borderRadius: 1, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${pct}%`, background: section.color, borderRadius: 1 }} />
            </div>
            <span style={{ fontSize: 10, color: "#8B949E", fontFamily: "monospace" }}>
              {done}/{total}
            </span>
          </div>
          <span style={{ color: "#30363D", fontSize: 14 }}>{isOpen ? "▲" : "▼"}</span>
        </div>
      </button>

      {/* Groups */}
      {isOpen && section.groups.map((group, gi) => {
        const filteredItems = group.items.filter(item => {
          if (filter === "pending") return !checked[item.id];
          if (filter === "done") return checked[item.id];
          return true;
        });

        if (filteredItems.length === 0) return null;

        return (
          <div key={gi} style={{ marginTop: 2 }}>
            <div style={{
              padding: "8px 20px",
              background: "#161B22",
              borderLeft: `3px solid ${section.color}20`,
              fontSize: 11,
              letterSpacing: 2,
              color: "#8B949E",
              textTransform: "uppercase",
            }}>
              {group.title}
            </div>

            {filteredItems.map((item) => (
              <ChecklistItem
                key={item.id}
                item={item}
                checked={!!checked[item.id]}
                expandedNote={!!expandedNotes[item.id]}
                onToggle={onToggleItem}
                onToggleNote={onToggleNote}
                sectionColor={section.color}
              />
            ))}
          </div>
        );
      })}
    </div>
  );
}
