import { useState } from "react";

export default function CompletionModal({ itemId, itemText, isOpen, onClose, onSave }) {
  const [note, setNote] = useState("");
  const [completionDate] = useState(new Date().toLocaleDateString('pt-BR'));

  const handleSave = () => {
    onSave(itemId, note);
    setNote("");
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      background: "rgba(0,0,0,0.7)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 1000,
    }}>
      <div style={{
        background: "#161B22",
        border: "1px solid #30363D",
        borderRadius: 8,
        padding: "24px",
        maxWidth: "500px",
        width: "90%",
      }}>
        <h2 style={{
          fontSize: 16,
          fontWeight: 700,
          color: "#E6EDF3",
          margin: "0 0 8px 0",
        }}>
          ✅ Marcar como concluído
        </h2>

        <p style={{
          fontSize: 13,
          color: "#8B949E",
          margin: "0 0 16px 0",
          lineHeight: 1.5,
        }}>
          {itemText}
        </p>

        <div style={{
          fontSize: 11,
          color: "#6E7681",
          marginBottom: 16,
        }}>
          Data: <strong>{completionDate}</strong>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{
            display: "block",
            fontSize: 12,
            color: "#8B949E",
            marginBottom: 8,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: 1,
          }}>
            Nota de conclusão (opcional)
          </label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Ex: Implementado em backend/modulo4_processamento/batch_worker.py. Testes em prod com Groq."
            style={{
              width: "100%",
              minHeight: 80,
              padding: "10px 12px",
              background: "#0D1117",
              border: "1px solid #30363D",
              borderRadius: 6,
              color: "#E6EDF3",
              fontSize: 12,
              fontFamily: "inherit",
              resize: "vertical",
              boxSizing: "border-box",
            }}
          />
        </div>

        <div style={{
          display: "flex",
          gap: 8,
          justifyContent: "flex-end",
        }}>
          <button
            onClick={onClose}
            style={{
              padding: "8px 16px",
              fontSize: 12,
              background: "#0D1117",
              border: "1px solid #30363D",
              color: "#8B949E",
              borderRadius: 6,
              cursor: "pointer",
              fontFamily: "inherit",
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => e.target.style.borderColor = "#475569"}
            onMouseLeave={(e) => e.target.style.borderColor = "#30363D"}
          >
            Cancelar
          </button>
          <button
            onClick={handleSave}
            style={{
              padding: "8px 16px",
              fontSize: 12,
              background: "#00FFB2",
              border: "1px solid #00FFB2",
              color: "#0D1117",
              borderRadius: 6,
              cursor: "pointer",
              fontFamily: "inherit",
              fontWeight: 600,
              transition: "all 0.2s",
            }}
            onMouseEnter={(e) => {
              e.target.style.background = "#00E6A0";
              e.target.style.borderColor = "#00E6A0";
            }}
            onMouseLeave={(e) => {
              e.target.style.background = "#00FFB2";
              e.target.style.borderColor = "#00FFB2";
            }}
          >
            Salvar
          </button>
        </div>
      </div>
    </div>
  );
}
