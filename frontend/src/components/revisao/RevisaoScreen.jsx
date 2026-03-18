import { useState } from "react";
import FragmentosTab from "./FragmentosTab";
import EntidadesTab from "./EntidadesTab";
import TopicosTab from "./TopicosTab";
import ActionItemsTab from "./ActionItemsTab";
import CorrecoesTab from "./CorrecoesTab";

export default function RevisaoScreen() {
  const [activeTab, setActiveTab] = useState("fragmentos");

  const tabs = [
    { id: "fragmentos", label: "Fragmentos", count: "📄" },
    { id: "entidades", label: "Entidades", count: "👤" },
    { id: "topicos", label: "Tópicos", count: "🏷️" },
    { id: "tarefas", label: "Tarefas", count: "✓" },
    { id: "correcoes", label: "Correções", count: "🔧" },
  ];

  return (
    <div style={{
      background: "#0D1117",
      minHeight: "100vh",
      fontFamily: "'Courier New', 'Lucida Console', monospace",
      color: "#E6EDF3",
      padding: "0",
    }}>
      {/* Sticky header with tabs */}
      <div style={{
        background: "linear-gradient(135deg, #0D1117 0%, #161B22 50%, #0D1117 100%)",
        borderBottom: "1px solid #30363D",
        padding: "32px 24px 24px",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}>
        <div style={{ maxWidth: 900, margin: "0 auto" }}>
          <h2 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 24px 0", letterSpacing: -1, color: "#F8FAFC" }}>
            ✏️ Curadoria de Dados
          </h2>

          {/* Tab buttons */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: "8px 16px",
                  fontSize: 12,
                  letterSpacing: 1,
                  textTransform: "uppercase",
                  border: `1px solid ${activeTab === tab.id ? "#00FFB2" : "#30363D"}`,
                  background: activeTab === tab.id ? "rgba(0,255,178,0.08)" : "transparent",
                  color: activeTab === tab.id ? "#00FFB2" : "#6E7681",
                  borderRadius: 2,
                  cursor: "pointer",
                  fontFamily: "inherit",
                  fontWeight: activeTab === tab.id ? 600 : 400,
                }}
              >
                {tab.count} {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tab content */}
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px 16px 80px" }}>
        {activeTab === "fragmentos" && <FragmentosTab />}
        {activeTab === "entidades" && <EntidadesTab />}
        {activeTab === "topicos" && <TopicosTab />}
        {activeTab === "tarefas" && <ActionItemsTab />}
        {activeTab === "correcoes" && <CorrecoesTab />}
      </div>
    </div>
  );
}
