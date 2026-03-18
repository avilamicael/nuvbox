export default function Header({ progress, checkedCount, totalItems, filter, setFilter, screen, setScreen }) {
  return (
    <div style={{
      background: "linear-gradient(135deg, #0D1117 0%, #161B22 50%, #0D1117 100%)",
      borderBottom: "1px solid #30363D",
      padding: "32px 24px 24px",
      position: "sticky",
      top: 0,
      zIndex: 100,
      backdropFilter: "blur(10px)",
    }}>
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
              <span style={{ fontSize: 11, letterSpacing: 4, color: "#00FFB2", textTransform: "uppercase", fontWeight: 700 }}>PROJETO</span>
            </div>
            <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0, letterSpacing: -1, color: "#F8FAFC" }}>
              CEREBRO <span style={{ color: "#00FFB2" }}>_</span> CHECKLIST
            </h1>
            <p style={{ margin: "6px 0 0", fontSize: 12, color: "#8B949E", letterSpacing: 1 }}>
              MVP CORE — SEGUNDO CÉREBRO COM VOZ
            </p>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 42, fontWeight: 700, color: "#00FFB2", lineHeight: 1, fontFamily: "monospace" }}>
              {screen === "checklist" ? (
                <>{progress}<span style={{ fontSize: 20, color: "#30363D" }}>%</span></>
              ) : screen === "revisao" ? "✏️" : "🔍"}
            </div>
            <div style={{ fontSize: 11, color: "#6E7681", marginTop: 4 }}>
              {screen === "checklist" ? `${checkedCount} / ${totalItems} concluídos`
                : screen === "revisao" ? "Curação de Dados"
                : "Query Interface"}
            </div>
          </div>
        </div>

        {/* Progress bar */}
        {screen === "checklist" && (
          <div style={{ marginTop: 20, background: "#30363D", borderRadius: 2, height: 4, overflow: "hidden" }}>
            <div style={{
              height: "100%",
              width: `${progress}%`,
              background: "linear-gradient(90deg, #00FFB2, #60A5FA)",
              transition: "width 0.5s ease",
              borderRadius: 2,
            }} />
          </div>
        )}

        {/* Screen toggle and filter buttons */}
        <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
          {/* Screen toggle */}
          <div style={{ display: "flex", gap: 8, marginRight: "auto" }}>
            {[
              { id: "checklist", label: "☑️ Checklist" },
              { id: "revisao",   label: "✏️ Curadoria" },
              { id: "consulta",  label: "🔍 Consulta" },
            ].map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setScreen(id)}
                style={{
                  padding: "4px 14px",
                  fontSize: 10,
                  letterSpacing: 2,
                  textTransform: "uppercase",
                  border: `1px solid ${screen === id ? "#00FFB2" : "#30363D"}`,
                  background: screen === id ? "rgba(0,255,178,0.08)" : "transparent",
                  color: screen === id ? "#00FFB2" : "#6E7681",
                  borderRadius: 2,
                  cursor: "pointer",
                  fontFamily: "inherit",
                  fontWeight: screen === id ? 600 : 400,
                }}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Filter buttons (only on checklist screen) */}
          {screen === "checklist" && (
            <>
              {["all", "pending", "done"].map(f => (
                <button key={f} onClick={() => setFilter(f)} style={{
                  padding: "4px 14px",
                  fontSize: 10,
                  letterSpacing: 2,
                  textTransform: "uppercase",
                  border: `1px solid ${filter === f ? "#00FFB2" : "#30363D"}`,
                  background: filter === f ? "rgba(0,255,178,0.08)" : "transparent",
                  color: filter === f ? "#00FFB2" : "#6E7681",
                  borderRadius: 2,
                  cursor: "pointer",
                  fontFamily: "inherit",
                }}>
                  {f === "all" ? "Todos" : f === "pending" ? "Pendentes" : "Feitos"}
                </button>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
