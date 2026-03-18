import { useState, useEffect } from "react";
import { getFragmentos, patchFragmento } from "../../api/jarvis";

export default function FragmentosTab() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");
  const [busca, setBusca] = useState("");
  const [feedback, setFeedback] = useState({}); // { id: "success"|"error" }

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const data = await getFragmentos(1, busca);
      setItems(data.items || []);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleEdit(item) {
    setEditingId(item.id);
    setEditValue(item.resumo);
  }

  async function handleSave(id) {
    try {
      const result = await patchFragmento(id, { resumo: editValue });
      // Update local state
      setItems(items.map(item => item.id === id ? result.item : item));
      setEditingId(null);
      setEditValue("");
      // Show success feedback
      setFeedback({ [id]: "success" });
      setTimeout(() => setFeedback({}), 2000);
    } catch (err) {
      console.error(err);
      setFeedback({ [id]: "error" });
      setTimeout(() => setFeedback({}), 2000);
    }
  }

  function handleCancel() {
    setEditingId(null);
    setEditValue("");
  }

  if (loading) {
    return <div style={{ color: "#8B949E", fontSize: 14 }}>Carregando fragmentos...</div>;
  }

  if (error) {
    return <div style={{ color: "#F85149", fontSize: 14 }}>Erro: {error}</div>;
  }

  return (
    <div>
      {/* Search bar */}
      <div style={{ marginBottom: 24 }}>
        <input
          type="text"
          placeholder="Buscar fragmento..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") fetchData();
          }}
          style={{
            width: "100%",
            padding: "8px 12px",
            fontSize: 12,
            fontFamily: "inherit",
            background: "#161B22",
            border: "1px solid #30363D",
            color: "#E6EDF3",
            borderRadius: 2,
          }}
        />
      </div>

      {/* Items list */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {items.length === 0 ? (
          <div style={{ color: "#8B949E", fontSize: 14 }}>Nenhum fragmento encontrado</div>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              style={{
                padding: 12,
                background: "#161B22",
                border: feedback[item.id] === "success"
                  ? "1px solid #00FFB2"
                  : feedback[item.id] === "error"
                    ? "1px solid #F85149"
                    : "1px solid #30363D",
                borderRadius: 2,
                transition: "border-color 0.2s",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  {editingId === item.id ? (
                    <textarea
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      style={{
                        width: "100%",
                        padding: 8,
                        fontSize: 12,
                        fontFamily: "inherit",
                        background: "#0D1117",
                        border: "1px solid #00FFB2",
                        color: "#E6EDF3",
                        borderRadius: 2,
                        minHeight: 60,
                        resize: "none",
                      }}
                    />
                  ) : (
                    <>
                      <div style={{ fontSize: 12, color: "#E6EDF3", marginBottom: 4 }}>
                        {item.resumo}
                      </div>
                      <div style={{ fontSize: 11, color: "#6E7681" }}>
                        Score: {typeof item.importance_score === 'number' ? item.importance_score.toFixed(2) : item.importance_score} • {new Date(item.criado_em).toLocaleDateString("pt-BR")}
                      </div>
                    </>
                  )}
                </div>

                <div style={{ display: "flex", gap: 4, whiteSpace: "nowrap" }}>
                  {editingId === item.id ? (
                    <>
                      <button
                        onClick={() => handleSave(item.id)}
                        style={{
                          padding: "4px 8px",
                          fontSize: 11,
                          background: "#00FFB2",
                          border: "none",
                          color: "#0D1117",
                          borderRadius: 2,
                          cursor: "pointer",
                          fontWeight: 600,
                        }}
                      >
                        ✔ Salvar
                      </button>
                      <button
                        onClick={handleCancel}
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
                        ✖ Cancelar
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => handleEdit(item)}
                      style={{
                        padding: "4px 8px",
                        fontSize: 11,
                        background: "transparent",
                        border: "1px solid #00FFB2",
                        color: "#00FFB2",
                        borderRadius: 2,
                        cursor: "pointer",
                      }}
                    >
                      ✎ Editar
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
