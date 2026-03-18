import { useState, useEffect } from "react";
import { getEntidades, patchEntidade, deleteEntidade } from "../../api/jarvis";

const STATUS_COLORS = {
  ativo: "#00FFB2",
  pendente: "#FFCC00",
  ambiguo: "#FF6B6B",
};

const TIPOS = ["pessoa", "empresa", "projeto", "tecnologia", "outro"];

export default function EntidadesTab() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState({ nome: "", descricao: "", status: "" });
  const [busca, setBusca] = useState("");
  const [filtroStatus, setFiltroStatus] = useState("");
  const [feedback, setFeedback] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    setLoading(true);
    setError(null);
    try {
      const data = await getEntidades("", filtroStatus, busca);
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
      nome: item.nome,
      descricao: item.descricao || "",
      status: item.status,
    });
  }

  async function handleSave(id) {
    try {
      const result = await patchEntidade(id, editValue);
      setItems(items.map(item => item.id === id ? result.item : item));
      setEditingId(null);
      setEditValue({ nome: "", descricao: "", status: "" });
      setFeedback({ [id]: "success" });
      setTimeout(() => setFeedback({}), 2000);
    } catch (err) {
      console.error(err);
      // Check if it's a duplicate name error
      if (err.message?.includes("409") || err.message?.includes("duplicate")) {
        alert("⚠️ Nome já existe!\n\nOutra entidade do mesmo tipo já tem este nome.");
      }
      setFeedback({ [id]: "error" });
      setTimeout(() => setFeedback({}), 2000);
    }
  }

  function handleCancel() {
    setEditingId(null);
    setEditValue({ nome: "", descricao: "", status: "" });
  }

  async function handleDelete(id, nome) {
    if (!window.confirm(`Deletar entidade "${nome}"?\n\nOs vínculos com fragmentos serão mantidos.`)) return;
    try {
      await deleteEntidade(id);
      setItems(items.filter(item => item.id !== id));
    } catch (err) {
      console.error(err);
      alert("Erro ao deletar entidade.");
    }
  }

  if (loading) {
    return <div style={{ color: "#8B949E", fontSize: 14 }}>Carregando entidades...</div>;
  }

  if (error) {
    return <div style={{ color: "#F85149", fontSize: 14 }}>Erro: {error}</div>;
  }

  return (
    <div>
      {/* Search and filters */}
      <div style={{ display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap" }}>
        <input
          type="text"
          placeholder="Buscar entidade..."
          value={busca}
          onChange={(e) => setBusca(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") fetchData();
          }}
          style={{
            flex: 1,
            minWidth: 150,
            padding: "8px 12px",
            fontSize: 12,
            fontFamily: "inherit",
            background: "#161B22",
            border: "1px solid #30363D",
            color: "#E6EDF3",
            borderRadius: 2,
          }}
        />
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
          <option value="ativo">Ativo</option>
          <option value="pendente">Pendente</option>
          <option value="ambiguo">Ambíguo</option>
        </select>
      </div>

      {/* Items list */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {items.length === 0 ? (
          <div style={{ color: "#8B949E", fontSize: 14 }}>Nenhuma entidade encontrada</div>
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
                        value={editValue.nome}
                        onChange={(e) => setEditValue({ ...editValue, nome: e.target.value })}
                        placeholder="Nome"
                        style={{
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
                        <option value="ativo">Ativo</option>
                        <option value="pendente">Pendente</option>
                        <option value="ambiguo">Ambíguo</option>
                      </select>
                    </div>
                  ) : (
                    <>
                      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                        <span style={{ fontSize: 14, fontWeight: 600, color: "#E6EDF3" }}>
                          {item.nome}
                        </span>
                        <span
                          style={{
                            fontSize: 10,
                            padding: "2px 6px",
                            background: STATUS_COLORS[item.status],
                            color: item.status === "ambiguo" || item.status === "pendente" ? "#0D1117" : "#0D1117",
                            borderRadius: 2,
                            fontWeight: 600,
                          }}
                        >
                          {item.status.toUpperCase()}
                        </span>
                        <span style={{ fontSize: 10, color: "#6E7681", marginLeft: "auto" }}>
                          {item.tipo}
                        </span>
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
                        onClick={() => handleDelete(item.id, item.nome)}
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
