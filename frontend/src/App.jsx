import { useState } from "react";
import { initialChecked, checklistData } from "./data/checklist";
import Header from "./components/Header";
import Section from "./components/Section";

export default function CerebroChecklist() {
  const [checked, setChecked] = useState(() => {
    const saved = localStorage.getItem('cerebroChecked');
    return saved ? JSON.parse(saved) : initialChecked;
  });
  const [expanded, setExpanded] = useState(() => {
    const saved = localStorage.getItem('cerebroExpanded');
    return saved ? JSON.parse(saved) : { ambiente: true };
  });
  const [expandedNotes, setExpandedNotes] = useState(() => {
    const saved = localStorage.getItem('cerebroExpandedNotes');
    return saved ? JSON.parse(saved) : {};
  });
  const [filter, setFilter] = useState("all");

  const toggle = (id) => setChecked(p => {
    const updated = { ...p, [id]: !p[id] };
    localStorage.setItem('cerebroChecked', JSON.stringify(updated));
    return updated;
  });
  const toggleSection = (id) => setExpanded(p => {
    const updated = { ...p, [id]: !p[id] };
    localStorage.setItem('cerebroExpanded', JSON.stringify(updated));
    return updated;
  });
  const toggleNote = (id) => setExpandedNotes(p => {
    const updated = { ...p, [id]: !p[id] };
    localStorage.setItem('cerebroExpandedNotes', JSON.stringify(updated));
    return updated;
  });

  const totalItems = checklistData.sections.flatMap(s => s.groups.flatMap(g => g.items)).length;
  const checkedCount = Object.values(checked).filter(Boolean).length;
  const progress = Math.round((checkedCount / totalItems) * 100);

  return (
    <div style={{
      background: "#0D1117",
      minHeight: "100vh",
      fontFamily: "'Courier New', 'Lucida Console', monospace",
      color: "#E6EDF3",
      padding: "0",
    }}>
      <Header
        progress={progress}
        checkedCount={checkedCount}
        totalItems={totalItems}
        filter={filter}
        setFilter={setFilter}
      />

      <div style={{ maxWidth: 900, margin: "0 auto", padding: "24px 16px 80px" }}>
        {checklistData.sections.map(section => (
          <Section
            key={section.id}
            section={section}
            checked={checked}
            isOpen={!!expanded[section.id]}
            expandedNotes={expandedNotes}
            filter={filter}
            onToggleSection={toggleSection}
            onToggleItem={toggle}
            onToggleNote={toggleNote}
          />
        ))}
      </div>
    </div>
  );
}
