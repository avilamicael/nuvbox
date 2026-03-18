/**
 * Jarvis API Client
 *
 * Wrapper fetch que injeta headers de autenticação e Content-Type
 * para comunicar com o backend dos endpoints /dados/*
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';
const API_SECRET = import.meta.env.VITE_API_SECRET || 'mude_antes_do_ngrok';

/**
 * Wrapper fetch com headers padrão
 * @param {string} path - caminho relativo (ex: "/dados/entidades")
 * @param {object} options - fetch options
 * @returns {Promise<Response>}
 */
async function apiFetch(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'X-Cerebro-Secret': API_SECRET,
    ...options.headers,
  };

  const url = `${API_URL}${path}`;

  try {
    const response = await fetch(url, { ...options, headers });
    return response;
  } catch (error) {
    console.error(`API request failed: ${path}`, error);
    throw error;
  }
}

// ─────────────────────────────────────────────────────────────
// FRAGMENTOS
// ─────────────────────────────────────────────────────────────

export async function getFragmentos(page = 1, busca = '') {
  const params = new URLSearchParams({ page, limit: 20 });
  if (busca) params.append('busca', busca);

  const response = await apiFetch(`/dados/fragmentos?${params}`);
  if (!response.ok) throw new Error(`Failed to fetch fragmentos: ${response.status}`);
  return response.json();
}

export async function patchFragmento(id, { resumo }) {
  const response = await apiFetch(`/dados/fragmentos/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ resumo }),
  });
  if (!response.ok) throw new Error(`Failed to update fragmento ${id}: ${response.status}`);
  return response.json();
}

// ─────────────────────────────────────────────────────────────
// ENTIDADES
// ─────────────────────────────────────────────────────────────

export async function getEntidades(tipo = '', status = '', busca = '') {
  const params = new URLSearchParams();
  if (tipo) params.append('tipo', tipo);
  if (status) params.append('status', status);
  if (busca) params.append('busca', busca);

  const queryStr = params.toString();
  const url = `/dados/entidades${queryStr ? '?' + queryStr : ''}`;

  const response = await apiFetch(url);
  if (!response.ok) throw new Error(`Failed to fetch entidades: ${response.status}`);
  return response.json();
}

export async function deleteEntidade(id) {
  const response = await apiFetch(`/dados/entidades/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error(`Failed to delete entidade ${id}: ${response.status}`);
  return response.json();
}

export async function patchEntidade(id, { nome, descricao, status, tipo, variante }) {
  const body = { nome };
  if (descricao) body.descricao = descricao;
  if (status) body.status = status;
  if (tipo) body.tipo = tipo;
  if (variante !== undefined) body.variante = variante;  // "" means clear it

  const response = await apiFetch(`/dados/entidades/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`Failed to update entidade ${id}: ${response.status}`);
  return response.json();
}

// ─────────────────────────────────────────────────────────────
// TÓPICOS
// ─────────────────────────────────────────────────────────────

export async function getTopicos(busca = '') {
  const params = new URLSearchParams();
  if (busca) params.append('busca', busca);

  const queryStr = params.toString();
  const url = `/dados/topicos${queryStr ? '?' + queryStr : ''}`;

  const response = await apiFetch(url);
  if (!response.ok) throw new Error(`Failed to fetch topicos: ${response.status}`);
  return response.json();
}

export async function deleteTopico(id) {
  const response = await apiFetch(`/dados/topicos/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error(`Failed to delete topico ${id}: ${response.status}`);
  return response.json();
}

export async function patchTopico(id, { caminho, descricao }) {
  const body = { caminho };
  if (descricao) body.descricao = descricao;

  const response = await apiFetch(`/dados/topicos/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`Failed to update topico ${id}: ${response.status}`);
  return response.json();
}

// ─────────────────────────────────────────────────────────────
// ACTION ITEMS (TAREFAS)
// ─────────────────────────────────────────────────────────────

// ─────────────────────────────────────────────────────────────
// CORREÇÕES DE TEXTO
// ─────────────────────────────────────────────────────────────

export async function getCorrecoes() {
  const response = await apiFetch('/dados/correcoes');
  if (!response.ok) throw new Error(`Failed to fetch correções: ${response.status}`);
  return response.json();
}

export async function postCorrecao({ texto_errado, texto_correto }) {
  const response = await apiFetch('/dados/correcoes', {
    method: 'POST',
    body: JSON.stringify({ texto_errado, texto_correto }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.message || `Failed to create correção: ${response.status}`);
  }
  return response.json();
}

export async function deleteCorrecao(id) {
  const response = await apiFetch(`/dados/correcoes/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error(`Failed to delete correção ${id}: ${response.status}`);
  return response.json();
}

export async function getActionItems(status = '') {
  const params = new URLSearchParams();
  if (status) params.append('status', status);

  const queryStr = params.toString();
  const url = `/dados/action-items${queryStr ? '?' + queryStr : ''}`;

  const response = await apiFetch(url);
  if (!response.ok) throw new Error(`Failed to fetch action items: ${response.status}`);
  return response.json();
}

// ─────────────────────────────────────────────────────────────
// CONSULTA (M6 — agentic query)
// ─────────────────────────────────────────────────────────────

export async function postConsulta(pergunta) {
  const resp = await apiFetch("/consulta", {
    method: "POST",
    body: JSON.stringify({ pergunta }),
  });
  if (!resp.ok) throw new Error(`Consulta falhou: ${resp.status}`);
  return resp.json();
  // retorna { resposta, fragmentos, ferramentas_usadas }
}

export async function patchActionItem(id, { status, texto }) {
  const body = {};
  if (status) body.status = status;
  if (texto) body.texto = texto;

  const response = await apiFetch(`/dados/action-items/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`Failed to update action item ${id}: ${response.status}`);
  return response.json();
}
