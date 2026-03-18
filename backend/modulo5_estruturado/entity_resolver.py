"""
Entity Resolver for Módulo 5 — Armazenamento Estruturado.

Responsável por decidir, dado um nome vindo do LLM, se é entidade nova,
existente (match exato) ou ambígua (fuzzy match).

Usa difflib (stdlib) — sem dependências externas.
"""

import difflib
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from utils import setup_logger

logger = setup_logger(__name__)


@dataclass
class ResolveResult:
    """Result from EntityResolver.resolve()."""
    entidade_id: Optional[int]   # None = criar nova
    status: str                  # 'ativo' | 'pendente' | 'novo'
    matched_nome: Optional[str]  # nome da entidade existente que fez match
    score: float                 # 0.0-1.0, fuzzy score (1.0 = exato)


class EntityResolver:
    """
    Resolve entity names to existing DB entries using exact + fuzzy matching.

    Usage:
        resolver = EntityResolver(existing_entities)
        result = resolver.resolve("Juliana", "pessoa")
        if result.entidade_id:
            # reutilizar existente
        else:
            # criar nova
    """

    FUZZY_THRESHOLD = 0.85

    def __init__(self, existing_entities: List[Dict[str, Any]]):
        """
        Args:
            existing_entities: List of dicts with keys:
                id, nome, nome_normalizado, tipo, descricao, variante (optional)
        """
        # Index entities by tipo for faster lookup
        self._by_type: Dict[str, List[Dict]] = {}
        for ent in existing_entities:
            tipo = ent.get("tipo", "").strip().lower()
            if tipo not in self._by_type:
                self._by_type[tipo] = []
            self._by_type[tipo].append(ent)

    def resolve(self, nome: str, tipo: str, variante: str = None, descricao: str = None) -> ResolveResult:
        """
        Decide if the entity is new, existing, or ambiguous.

        Steps:
        1. Exact match by nome_normalizado + tipo + variante → status='ativo'
        2. Fuzzy match (threshold=0.85) by tipo + variante → status='pendente'
        3. No match → status='novo', entidade_id=None

        When variante is provided, only candidates with the same variante are
        considered — preventing "Juliana (mãe)" from matching "Juliana (amiga)".

        Args:
            nome: Entity name as it came from the LLM
            tipo: Entity type (pessoa, empresa, projeto, etc.)
            variante: Optional qualifier (e.g., 'mãe', 'amiga', 'pai')
            descricao: Optional description (for future use)

        Returns:
            ResolveResult with decision
        """
        nome_norm = nome.strip().lower()
        tipo_norm = tipo.strip().lower()
        variante_norm = (variante or "").strip().lower()

        all_candidates = self._by_type.get(tipo_norm, [])

        # Filter candidates by variante: if variante is provided, only match
        # candidates with the same variante; otherwise only match those without variante.
        # This prevents same-name entities with different variants from colliding.
        if variante_norm:
            candidates = [
                c for c in all_candidates
                if (c.get("variante") or "").strip().lower() == variante_norm
            ]
        else:
            candidates = [
                c for c in all_candidates
                if not c.get("variante")
            ]

        # Step 1: Exact match by nome_normalizado (+ variante already filtered)
        for ent in candidates:
            if ent.get("nome_normalizado", "").lower() == nome_norm:
                logger.debug(
                    f"EntityResolver: exact match '{nome}' ({tipo}) variante={variante} → id={ent['id']}"
                )
                return ResolveResult(
                    entidade_id=ent["id"],
                    status="ativo",
                    matched_nome=ent["nome"],
                    score=1.0,
                )

        # Step 2: Fuzzy match (within same variante bucket)
        best_score = 0.0
        best_match: Optional[Dict] = None
        for ent in candidates:
            candidate_norm = ent.get("nome_normalizado", "")
            score = difflib.SequenceMatcher(None, nome_norm, candidate_norm).ratio()
            if score > best_score:
                best_score = score
                best_match = ent

        if best_score >= self.FUZZY_THRESHOLD and best_match:
            logger.debug(
                f"EntityResolver: fuzzy match '{nome}' ({tipo}) variante={variante} → "
                f"'{best_match['nome']}' (score={best_score:.2f}) id={best_match['id']}"
            )
            return ResolveResult(
                entidade_id=best_match["id"],
                status="pendente",
                matched_nome=best_match["nome"],
                score=best_score,
            )

        # Step 3: No match → create new
        logger.debug(
            f"EntityResolver: no match for '{nome}' ({tipo}) variante={variante} — will create new"
        )
        return ResolveResult(
            entidade_id=None,
            status="novo",
            matched_nome=None,
            score=0.0,
        )
