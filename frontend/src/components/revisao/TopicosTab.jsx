import { useState, useEffect } from "react";
import { getTopicos, patchTopico, deleteTopico } from "../../api/jarvis";

export default function TopicosTab() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState({ caminho: "", descricao: "" });
  const [busca, setBusca] = useState("");
  const [feedback, setFeedback] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const data = await getTopicos(busca);
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
    setEditValue({
      caminho: item.caminho,
      descricao: item.descricao || "",
    });
  }

  async function handleSave(id) {
    try {
      const result = await patchTopico(id, editValue);
      setItems(items.map(item => item.id === id ? result.item : item));
      setEditingId(null);
      setEditValue({ caminho: "", descricao: "" });
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
    setEditValue({ caminho: "", descricao: "" });
  }

  async function handleDelete(id, caminho) {
    if (!window.confirm(`Deletar tópico "${caminho}"?`)) return;
    try {
      await deleteTopico(id);
      setItems(items.filter(item => item.id !== id));
    } catch (err) {
      console.error(err);
      alert("Erro ao deletar tópico.");
    }
  }

  if (loading) {
    return <div style={{ color: "#8B949E", fontSize: 14 }}>Carregando tópicos...</div>;
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
          placeholder="Buscar tópico..."
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
          <div style={{ color: "#8B949E", fontSize: 14 }}>Nenhum tópico encontrado</div>
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
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      <input
                        type="text"
                        value={editValue.caminho}
                        onChange={(e) => setEditValue({ ...editValue, caminho: e.target.value })}
                        placeholder="Caminho hierárquico (ex: Trabalho > Projetos > Jarvis)"
                        style={{
                          width: "100%",
                          padding: 6,
                          fontSize: 12,
                          fontFamily: "inherit",
                          background: "#0D1117",
                          border: "1px solid #00FFB2",
                          color: "#E6EDF3",
                          borderRadius: 2,
                        }}
                      />
                      <textarea
                        value={editValue.descricao}
                        onChange={(e) => setEditValue({ ...editValue, descricao: e.target.value })}
                        placeholder="Descrição (opcional)"
                        style={{
                          width: "100%",
                          padding: 6,
                          fontSize: 12,
                          fontFamily: "inherit",
                          background: "#0D1117",
                          border: "1px solid #00FFB2",
                          color: "#E6EDF3",
                          borderRadius: 2,
                          minHeight: 40,
                          resize: "none",
                        }}
                      />
                    </div>
                  ) : (
                    <>
                      <div style={{ fontSize: 13, fontWeight: 600, color: "#00FFB2", marginBottom: 4 }}>
                        {item.caminho}
                      </div>
                      {item.descricao && (
                        <div style={{ fontSize: 12, color: "#8B949E", marginBottom: 4 }}>
                          {item.descricao}
                        </div>
                      )}
                      <div style={{ fontSize: 11, color: "#6E7681" }}>
                        {new Date(item.criado_em).toLocaleDateString("pt-BR")}
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
                    <>
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
                      <button
                        onClick={() => handleDelete(item.id, item.caminho)}
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
                    </>
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
