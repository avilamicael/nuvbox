import { useState, useEffect } from "react";
import { getCorrecoes, postCorrecao, deleteCorrecao } from "../../api/jarvis";

export default function CorrecoesTab() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [novoErrado, setNovoErrado] = useState("");
  const [novoCorreto, setNovoCorreto] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const data = await getCorrecoes();
      setItems(data.items || []);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd() {
    if (!novoErrado.trim() || !novoCorreto.trim()) return;
    setSaving(true);
    try {
      const result = await postCorrecao({
        texto_errado: novoErrado.trim(),
        texto_correto: novoCorreto.trim(),
      });
      setItems([result.item, ...items]);
      setNovoErrado("");
      setNovoCorreto("");
    } catch (err) {
      console.error(err);
      alert(`Erro: ${err.message}`);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id, errado) {
    if (!window.confirm(`Remover correção "${errado}"?`)) return;
    try {
      await deleteCorrecao(id);
      setItems(items.filter(item => item.id !== id));
    } catch (err) {
      console.error(err);
      alert("Erro ao remover correção.");
    }
  }

  if (loading) {
    return <div style={{ color: "#8B949E", fontSize: 14 }}>Carregando correções...</div>;
  }

  if (error) {
    return <div style={{ color: "#F85149", fontSize: 14 }}>Erro: {error}</div>;
  }

  return (
    <div>
      {/* Explicação */}
      <div style={{
        padding: 12,
        background: "rgba(0,255,178,0.05)",
        border: "1px solid rgba(0,255,178,0.2)",
        borderRadius: 2,
        marginBottom: 24,
        fontSize: 12,
        color: "#8B949E",
        lineHeight: 1.6,
      }}>
        <strong style={{ color: "#00FFB2" }}>Como funciona:</strong> Quando o Whisper errar uma
        palavra (ex: ouvir "prômitos" em vez de "prompts"), adicione aqui a correção. Antes de
        enviar cada transcrição ao LLM, o sistema substitui automaticamente o texto errado pelo
        correto — evitando que entidades ou tópicos errados sejam criados novamente.
      </div>

      {/* Formulário de adicionar */}
      <div style={{
        padding: 16,
        background: "#161B22",
        border: "1px solid #30363D",
        borderRadius: 2,
        marginBottom: 24,
      }}>
        <div style={{ fontSize: 11, color: "#00FFB2", letterSpacing: 2, marginBottom: 12, textTransform: "uppercase" }}>
          + Nova Correção
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <input
            type="text"
            placeholder="Texto errado (ex: prômitos)"
            value={novoErrado}
            onChange={(e) => setNovoErrado(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleAdd(); }}
            style={{
              flex: 1,
              minWidth: 140,
              padding: "8px 10px",
              fontSize: 12,
              fontFamily: "inherit",
              background: "#0D1117",
              border: "1px solid #30363D",
              color: "#E6EDF3",
              borderRadius: 2,
            }}
          />
          <span style={{ color: "#6E7681", fontSize: 16 }}>→</span>
          <input
            type="text"
            placeholder="Texto correto (ex: prompts)"
            value={novoCorreto}
            onChange={(e) => setNovoCorreto(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleAdd(); }}
            style={{
              flex: 1,
              minWidth: 140,
              padding: "8px 10px",
              fontSize: 12,
              fontFamily: "inherit",
              background: "#0D1117",
              border: "1px solid #30363D",
              color: "#E6EDF3",
              borderRadius: 2,
            }}
          />
          <button
            onClick={handleAdd}
            disabled={saving || !novoErrado.trim() || !novoCorreto.trim()}
            style={{
              padding: "8px 16px",
              fontSize: 12,
              background: saving ? "#30363D" : "#00FFB2",
              border: "none",
              color: "#0D1117",
              borderRadius: 2,
              cursor: saving ? "not-allowed" : "pointer",
              fontWeight: 600,
              fontFamily: "inherit",
              whiteSpace: "nowrap",
            }}
          >
            {saving ? "Salvando..." : "✔ Adicionar"}
          </button>
        </div>
      </div>

      {/* Lista de correções */}
      {items.length === 0 ? (
        <div style={{ color: "#8B949E", fontSize: 14 }}>
          Nenhuma correção cadastrada ainda.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {items.map((item) => (
            <div
              key={item.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "10px 12px",
                background: "#161B22",
                border: "1px solid #30363D",
                borderRadius: 2,
              }}
            >
              <span style={{ flex: 1, fontSize: 13, color: "#F85149", fontFamily: "monospace" }}>
                {item.texto_errado}
              </span>
              <span style={{ color: "#6E7681", fontSize: 16 }}>→</span>
              <span style={{ flex: 1, fontSize: 13, color: "#00FFB2", fontFamily: "monospace" }}>
                {item.texto_correto}
              </span>
              <span style={{ fontSize: 11, color: "#6E7681", whiteSpace: "nowrap" }}>
                {new Date(item.criado_em).toLocaleDateString("pt-BR")}
              </span>
              <button
                onClick={() => handleDelete(item.id, item.texto_errado)}
                style={{
                  padding: "4px 8px",
                  fontSize: 11,
                  background: "transparent",
                  border: "1px solid #F85149",
                  color: "#F85149",
                  borderRadius: 2,
                  cursor: "pointer",
                }}
              >
                🗑
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
