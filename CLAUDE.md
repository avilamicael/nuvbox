# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CEREBRO Checklist** is a React + Vite web application that tracks the development and implementation of the **Projeto Cerebro** — a voice-controlled personal assistant system (second brain) that:

- Captures everything you say via a passive microphone (always on)
- Transcribes automatically using local Whisper (privacy-first)
- Categorizes into hierarchical topics based on user profile
- Connects related conversations over time (knowledge graph)
- Allows natural language queries ("show me everything about X")
- Scales from personal use to enterprise (multi-user, SaaS, on-premise)

This repository contains only the **frontend checklist tracking tool**. The actual backend (Python-based with Whisper, VAD, PostgreSQL, OpenAI API, embeddings) is implemented separately and monitored through this checklist's task items.

## Technology Stack

- **Framework**: React 19.2.4
- **Build Tool**: Vite 8.0.0
- **Language**: JavaScript/JSX (no TypeScript)
- **Styling**: CSS (inline styles in components)
- **Linting**: ESLint with React hooks and refresh plugins
- **Package Manager**: npm

## Development Commands

All commands should be run from `/frontend/` directory:

```bash
npm run dev        # Start dev server with HMR (http://localhost:5173)
npm run build      # Build for production (outputs to /dist)
npm run lint       # Run ESLint on all .js and .jsx files
npm run preview    # Preview production build locally
```

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx           # Main checklist component (560 lines) - contains entire app
│   ├── main.jsx          # Entry point - mounts App to #root
│   ├── App.css           # Component styles
│   └── index.css         # Global styles
├── public/               # Static assets (favicon.svg, icons.svg, images)
├── index.html            # HTML entry point
├── vite.config.js        # Vite build config with React plugin
├── eslint.config.js      # ESLint config (flat config, new style)
└── package.json          # Dependencies and scripts
```

## Architecture

### Single-Page Application (SPA)
The entire application is contained in `App.jsx` as one stateful React component. This is appropriate for a checklist UI where:
- State is centralized: `checked` (task completion), `expanded` (section visibility), `expandedNotes` (note visibility), `filter` (view mode)
- No complex navigation or routing needed
- All data is hardcoded in the `data` object (not fetched from a backend)

### Data Structure — Mapping to Projeto Cerebro
The app uses a hierarchical checklist structure organized by **Cerebro modules and implementation phases**:

- **sections** (8 total): Cerebro modules + system ops
  - **Módulo 0** — User Profile & Context (categorization rules)
  - **Módulo 1** — Input (audio capture, VAD, activation context)
  - **Módulo 2** — Transcription (Whisper local + diarization future)
  - **Módulo 3** — Raw Storage (PostgreSQL)
  - **Módulo 4** — AI Processing (GPT-4o mini batch jobs)
  - **Módulo 5** — Structured Storage (topics, entities, relationships)
  - **Módulo 6** — Query Interface (web, WhatsApp, automations)
  - **Módulo 7** — Semantic Memory (embeddings, similarity search)
  - **SISTEMA & OPERAÇÃO** — Deployment, testing, security

- **groups** (multiple per section): Task categories per module (e.g., "Sistema Operacional & Python", "VAD Detection", "Batch Processing")
  - **items** (multiple per group): Individual checklist items with `id`, `text`, and implementation notes

### UI Features
- **Progress tracking**: Overall percentage and per-section progress bars
- **Filter modes**: Show all, pending only, or completed only
- **Expandable sections**: Click section headers to collapse/expand task groups
- **Notes system**: Each task can have a note that toggles on/off with a button
- **Color coding**: Each section has a unique color theme used in borders and highlights

### Styling Approach
All styles are defined as inline JavaScript objects passed to `style` props. No CSS Modules or CSS-in-JS libraries. Global styles in `index.css` and component-specific styles in `App.css`.

### Connection to Backend
This checklist is a **progress tracker tool** for implementing the actual Cerebro system:
- Each checklist item links to a backend implementation task (Python scripts, database schemas, API integrations)
- Checking off items represents completed backend work, not just UI updates
- The checklist drives the roadmap: Phase 1 (MVP Core) → Phase 2 (AI Processing) → Phase 3 (Query) → Phase 4-5 (Scale)
- User can filter by completion status to see what's done vs. pending

## ESLint Configuration

The project uses the new ESLint flat config format in `eslint.config.js`:
- Extends `@eslint/js` recommended rules
- Includes React hooks rules (`eslint-plugin-react-hooks`)
- Includes React refresh rules (`eslint-plugin-react-refresh`)
- Custom rule: `no-unused-vars` ignores PascalCase variables (Components)
- Ignores `/dist` directory

Run `npm run lint` to check, but note there's no auto-fix script configured.

## Key Implementation Notes

### State Management Pattern
Uses React's `useState` hook for local component state. Each state update function follows a consistent pattern:
```javascript
const toggle = (id) => setChecked(p => ({ ...p, [id]: !p[id] }));
```
This creates new state objects rather than mutating, maintaining React best practices.

### Performance Consideration
The component recalculates progress and section stats on every render:
- `getSectionProgress()` is called for each section during render
- This is acceptable for the current scale (7 sections × ~15 items) but would need optimization if data grows significantly

### No Backend Integration
All data is static. To connect to a real backend, you would need to:
1. Move the `data` object to a JSON file or API endpoint
2. Add `useEffect` hooks to fetch data on mount
3. Convert state updates to API calls
4. Add error handling for network requests

## Development Notes

- The project doesn't use TypeScript; types are managed through JSDoc comments and careful prop handling
- No routing library is needed for this single-page checklist
- The README.md in `/frontend` is a generic Vite template—actual project documentation is embedded in checklist items and the `visao_geral.pdf` in the root
- Vite uses Oxc parser by default (fast JSX parsing); React Compiler is not enabled
- HMR (Hot Module Replacement) is active in dev mode—changes save and refresh automatically
- **Data source**: All checklist content in `App.jsx` is the source of truth for Cerebro implementation tasks (hardcoded data structure—could be extracted to JSON later)
- **Purpose**: This is a MVP-phase documentation + progress tracker; as Cerebro backend scales to production, consider migrating to a proper task/project management tool if needed

## Cerebro Backend Stack (Reference)

This checklist tracks implementation of a Python-based system. Key technologies:

- **Backend Language**: Python
- **Voice Capture & VAD**: silero-vad
- **Transcription**: Whisper (small model locally, medium/API future)
- **Database**: PostgreSQL (raw + structured storage)
- **LLM Processing**: OpenAI API (GPT-4o mini, batch processing daily)
- **Future Components**: pyannote.audio (diarization), Ollama + LLaMA/Mistral (local LLM), pgvector (semantic search), sentence-transformers (embeddings)

The frontend checklist ensures all modules are properly tracked during development. See `visao_geral.pdf` for full Cerebro architecture details.

## Building for Production

```bash
npm run build    # Creates optimized bundle in /dist
npm run preview  # Test production build locally before deployment
```

The built assets are optimized by Vite and ready for static hosting (to accompany the Python backend).
