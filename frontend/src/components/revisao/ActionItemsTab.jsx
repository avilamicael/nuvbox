import { useState, useEffect } from "react";
import { getActionItems, patchActionItem } from "../../api/jarvis";

const STATUS_COLORS = {
  pendente: "#FFCC00",
  concluido: "#00FFB2",
  cancelado: "#8B949E",
};

export default function ActionItemsTab() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState({ status: "", texto: "" });
  const [filtroStatus, setFiltroStatus] = useState("");
  const [feedback, setFeedback] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const data = await getActionItems(filtroStatus);
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
      status: item.status,
      texto: item.texto,
    });
  }

  async function handleSave(id) {
    try {
      const result = await patchActionItem(id, editValue);
      setItems(items.map(item => item.id === id ? result.item : item));
      setEditingId(null);
      setEditValue({ status: "", texto: "" });
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
    setEditValue({ status: "", texto: "" });
  }

  async function handleQuickToggle(item) {
    // Quick toggle: pendente → concluido → cancelado → pendente
    const statusCycle = { pendente: "concluido", concluido: "cancelado", cancelado: "pendente" };
    const novoStatus = statusCycle[item.status] || "pendente";

    try {
      const result = await patchActionItem(item.id, { status: novoStatus, texto: item.texto });
      setItems(items.map(i => i.id === item.id ? result.item : i));
      setFeedback({ [item.id]: "success" });
      setTimeout(() => setFeedback({}), 2000);
    } catch (err) {
      console.error(err);
      setFeedback({ [item.id]: "error" });
      setTimeout(() => setFeedback({}), 2000);
    }
  }

  if (loading) {
    return <div style={{ color: "#8B949E", fontSize: 14 }}>Carregando tarefas...</div>;
  }

  if (error) {
    return <div style={{ color: "#F85149", fontSize: 14 }}>Erro: {error}</div>;
  }

  return (
    <div>
      {/* Filter bar */}
      <div style={{ marginBottom: 24 }}>
        <select
          value={filtroStatus}
          onChange={(e) => {
            setFiltroStatus(e.target.value);
          }}
          style={{
            padding: "8px 12px",
            fontSize: 12,
            fontFamily: "inherit",
            background: "#161B22",
            border: "1px solid #30363D",
            color: "#E6EDF3",
            borderRadius: 2,
            cursor: "pointer",
          }}
        >
          <option value="">Todos os status</option>
          <option value="pendente">Pendentes</option>
          <option value="concluido">Concluídas</option>
          <option value="cancelado">Canceladas</option>
        </select>
      </div>

      {/* Items list */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {items.length === 0 ? (
          <div style={{ color: "#8B949E", fontSize: 14 }}>Nenhuma tarefa encontrada</div>
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
                opacity: item.status === "cancelado" ? 0.6 : 1,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  {editingId === item.id ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      <textarea
                        value={editValue.texto}
                        onChange={(e) => setEditValue({ ...editValue, texto: e.target.value })}
                        placeholder="Descrição da tarefa"
                        style={{
                          width: "100%",
                          padding: 6,
                          fontSize: 12,
                          fontFamily: "inherit",
                          background: "#0D1117",
                          border: "1px solid #00FFB2",
                          color: "#E6EDF3",
                          borderRadius: 2,
                          minHeight: 50,
                          resize: "none",
                        }}
                      />
                      <select
                        value={editValue.status}
                        onChange={(e) => setEditValue({ ...editValue, status: e.target.value })}
                        style={{
                          padding: 6,
                          fontSize: 12,
                          fontFamily: "inherit",
                          background: "#0D1117",
                          border: "1px solid #00FFB2",
                          color: "#E6EDF3",
                          borderRadius: 2,
                          cursor: "pointer",
                        }}
                      >
                        <option value="pendente">Pendente</option>
                        <option value="concluido">Concluído</option>
                        <option value="cancelado">Cancelado</option>
                      </select>
                    </div>
                  ) : (
                    <>
                      <div style={{ fontSize: 13, color: "#E6EDF3", marginBottom: 4 }}>
                        {item.texto}
                      </div>
                      <div style={{ display: "flex", gap: 12, fontSize: 11, color: "#6E7681" }}>
                        <span>
                          <span
                            style={{
                              display: "inline-block",
                              padding: "2px 6px",
                              background: STATUS_COLORS[item.status],
                              color: item.status === "pendente" ? "#0D1117" : item.status === "concluido" ? "#0D1117" : "#E6EDF3",
                              borderRadius: 2,
                              fontWeight: 600,
                              marginRight: 6,
                            }}
                          >
                            {item.status.toUpperCase()}
                          </span>
                        </span>
                        <span>Por: {item.atualizado_por}</span>
                        <span>{new Date(item.criado_em).toLocaleDateString("pt-BR")}</span>
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
                        onClick={() => handleQuickToggle(item)}
                        title="Alternar status (pendente → concluído → cancelado)"
                        style={{
                          padding: "4px 8px",
                          fontSize: 11,
                          background: "transparent",
                          border: `1px solid ${STATUS_COLORS[item.status]}`,
                          color: STATUS_COLORS[item.status],
                          borderRadius: 2,
                          cursor: "pointer",
                        }}
                      >
                        ⟳ Toggle
                      </button>
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
