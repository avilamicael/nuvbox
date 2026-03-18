import { useState } from "react";
import { postConsulta } from "../api/jarvis";

const TOOL_COLORS = {
  buscar_fragmentos: "#60A5FA",
  buscar_entidades: "#F59E0B",
  buscar_topicos: "#A78BFA",
  buscar_por_data: "#34D399",
};

function ToolBadge({ name }) {
  const color = TOOL_COLORS[name] || "#8B949E";
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 10px",
      fontSize: 10,
      letterSpacing: 1,
      textTransform: "uppercase",
      fontFamily: "inherit",
      border: `1px solid ${color}`,
      color,
      borderRadius: 2,
      background: `${color}18`,
    }}>
      {name}
    </span>
  );
}

function FragmentoCard({ f }) {
  const score = f.importance_score != null ? f.importance_score : f.score;
  const data = f.criado_em || f.data || f.timestamp;
  const dataStr = data ? new Date(data).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" }) : null;

  return (
    <div style={{
      border: "1px solid #30363D",
      borderRadius: 4,
      padding: "12px 16px",
      marginBottom: 8,
      background: "#0D1117",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, marginBottom: f.topicos ? 8 : 0 }}>
        <p style={{ margin: 0, fontSize: 13, color: "#E6EDF3", lineHeight: 1.6, flex: 1 }}>
          {f.resumo || f.transcricao || "(sem resumo)"}
        </p>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4, flexShrink: 0 }}>
          {score != null && (
            <span style={{ fontSize: 10, color: "#00FFB2", fontFamily: "monospace", whiteSpace: "nowrap" }}>
              ★ {typeof score === "number" ? score.toFixed(2) : score}
            </span>
          )}
          {dataStr && (
            <span style={{ fontSize: 10, color: "#6E7681", whiteSpace: "nowrap" }}>{dataStr}</span>
          )}
        </div>
      </div>
      {f.topicos && f.topicos.length > 0 && (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          {f.topicos.map((t, i) => (
            <span key={i} style={{
              fontSize: 10,
              padding: "1px 8px",
              border: "1px solid #30363D",
              borderRadius: 2,
              color: "#8B949E",
            }}>
              {t}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ConsultaScreen() {
  const [pergunta, setPergunta] = useState("");
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  async function handleConsulta() {
    const q = pergunta.trim();
    if (!q || loading) return;
    setLoading(true);
    setError(null);
    setResultado(null);
    try {
      const data = await postConsulta(q);
      setResultado(data);
    } catch (err) {
      setError(err.message || "Erro ao consultar o backend.");
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleConsulta();
    }
  }

  const ferramentas = resultado?.ferramentas_usadas || [];
  const fragmentos = resultado?.fragmentos || [];

  return (
    <div style={{
      background: "#0D1117",
      minHeight: "100vh",
      fontFamily: "'Courier New', 'Lucida Console', monospace",
      color: "#E6EDF3",
      padding: "0",
    }}>
      {/* Search bar */}
      <div style={{
        position: "sticky",
        top: 0,
        zIndex: 10,
        background: "#161B22",
        borderBottom: "1px solid #30363D",
        padding: "16px 24px",
      }}>
        <div style={{ maxWidth: 900, margin: "0 auto" }}>
          <div style={{ fontSize: 11, letterSpacing: 4, color: "#00FFB2", textTransform: "uppercase", fontWeight: 700, marginBottom: 10 }}>
            🔍 Consulta
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <input
              type="text"
              value={pergunta}
              onChange={e => setPergunta(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite sua pergunta..."
              disabled={loading}
              style={{
                flex: 1,
                background: "#0D1117",
                border: "1px solid #30363D",
                borderRadius: 2,
                padding: "8px 12px",
                fontSize: 13,
                color: "#E6EDF3",
                fontFamily: "inherit",
                outline: "none",
              }}
            />
            <button
              onClick={handleConsulta}
              disabled={loading || !pergunta.trim()}
              style={{
                padding: "8px 20px",
                fontSize: 11,
                letterSpacing: 2,
                textTransform: "uppercase",
                fontFamily: "inherit",
                fontWeight: 600,
                border: "1px solid #00FFB2",
                background: loading ? "transparent" : "rgba(0,255,178,0.08)",
                color: loading ? "#6E7681" : "#00FFB2",
                borderColor: loading ? "#30363D" : "#00FFB2",
                borderRadius: 2,
                cursor: loading ? "not-allowed" : "pointer",
                whiteSpace: "nowrap",
              }}
            >
              {loading ? "Consultando..." : "Consultar"}
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px 16px 80px" }}>
        {error && (
          <div style={{
            border: "1px solid #F85149",
            borderRadius: 4,
            padding: "12px 16px",
            color: "#F85149",
            fontSize: 13,
            marginBottom: 20,
          }}>
            {error}
          </div>
        )}

        {!resultado && !error && !loading && (
          <div style={{ textAlign: "center", color: "#6E7681", fontSize: 13, marginTop: 60 }}>
            Aguardando consulta...
          </div>
        )}

        {loading && (
          <div style={{ textAlign: "center", color: "#8B949E", fontSize: 13, marginTop: 60 }}>
            Processando...
          </div>
        )}

        {resultado && (
          <>
            {/* Ferramentas usadas */}
            {ferramentas.length > 0 && (
              <div style={{ marginBottom: 16, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                <span style={{ fontSize: 10, color: "#6E7681", letterSpacing: 1, textTransform: "uppercase" }}>Ferramentas:</span>
                {ferramentas.map((t, i) => <ToolBadge key={i} name={t} />)}
              </div>
            )}

            {/* Resposta */}
            <div style={{
              border: "1px solid #00FFB2",
              borderRadius: 4,
              padding: "16px 20px",
              background: "rgba(0,255,178,0.04)",
              marginBottom: 24,
              fontSize: 14,
              lineHeight: 1.7,
              color: "#E6EDF3",
              whiteSpace: "pre-wrap",
            }}>
              {resultado.resposta || "(sem resposta)"}
            </div>

            {/* Fragmentos */}
            <div style={{ marginBottom: 12 }}>
              <span style={{ fontSize: 11, letterSpacing: 2, color: "#8B949E", textTransform: "uppercase" }}>
                Fragmentos — {fragmentos.length} encontrado{fragmentos.length !== 1 ? "s" : ""}
              </span>
            </div>
            {fragmentos.length === 0 && (
              <p style={{ fontSize: 13, color: "#6E7681" }}>Nenhum fragmento retornado.</p>
            )}
            {fragmentos.map((f, i) => <FragmentoCard key={f.id || i} f={f} />)}
          </>
        )}
      </div>
    </div>
  );
}
