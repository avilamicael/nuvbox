"""
Response parser for Módulo 4 OpenAI outputs.

Responsável por:
1. Parse JSON da resposta do GPT-4o mini
2. Validação de esquema com 3 níveis de fallback
3. Normalização de dados (lowercase, tipos válidos)
"""

import json
import re
from typing import List, Dict, Any, Optional
from decimal import Decimal
from utils import setup_logger

logger = setup_logger(__name__)


class ParserError(Exception):
    """Base exception for parsing errors."""
    pass


class ResponseParser:
    """
    Parse and validate OpenAI response for batch processing.
    """

    # Valid entity types
    VALID_ENTITY_TYPES = {
        "pessoa", "empresa", "projeto", "lugar",
        "conceito", "ferramenta", "evento", "tarefa",
        "decisao", "ideia", "produto",
    }

    @staticmethod
    def parse_response(response_text: str, batch_size: int) -> Dict[str, Any]:
        """
        Parse OpenAI response with 3 levels of fallback.

        Level 1: Direct json.loads()
        Level 2: Regex to extract JSON block
        Level 3: Reprocess individual transcriptions (fallback to 1-by-1)

        Args:
            response_text: Raw response from OpenAI
            batch_size: Number of transcriptions in the batch

        Returns:
            Validated dict with "resultados" key

        Raises:
            ParserError: If all 3 levels fail
        """
        # Level 1: Direct parse
        try:
            data = json.loads(response_text)
            ResponseParser._validate_schema(data, batch_size)
            logger.debug("✅ Level 1 parse: Direct json.loads() succeeded")
            return data
        except (json.JSONDecodeError, ParserError) as e:
            logger.debug(f"⚠️  Level 1 failed: {e}")

        # Level 2: Regex extraction
        try:
            match = re.search(r'\{[\s\S]*"resultados"[\s\S]*\}', response_text)
            if match:
                json_block = match.group(0)
                data = json.loads(json_block)
                ResponseParser._validate_schema(data, batch_size)
                logger.debug("✅ Level 2 parse: Regex extraction succeeded")
                return data
        except (json.JSONDecodeError, ParserError, AttributeError) as e:
            logger.debug(f"⚠️  Level 2 failed: {e}")

        # Level 3: Individual reprocessing (will be handled by caller)
        logger.warning(
            f"❌ Levels 1-2 failed. "
            f"Transcriptions from this batch will need individual reprocessing."
        )
        raise ParserError(
            f"Could not parse response after 2 levels. "
            f"Response: {response_text[:200]}..."
        )

    @staticmethod
    def _validate_schema(data: Dict, batch_size: int) -> None:
        """
        Validate the response schema.

        Args:
            data: Parsed JSON dict
            batch_size: Expected number of results

        Raises:
            ParserError: If schema is invalid
        """
        if not isinstance(data, dict):
            raise ParserError(f"Response must be a dict, got {type(data)}")

        if "resultados" not in data:
            raise ParserError("Missing 'resultados' key")

        resultados = data["resultados"]
        if not isinstance(resultados, list):
            raise ParserError(f"'resultados' must be list, got {type(resultados)}")

        if len(resultados) != batch_size:
            raise ParserError(
                f"Expected {batch_size} results, got {len(resultados)}"
            )

        # Validate each result
        for i, result in enumerate(resultados):
            ResponseParser._validate_result(result, i)

    @staticmethod
    def _validate_result(result: Dict, idx: int) -> None:
        """
        Validate a single result object.

        Args:
            result: Result object
            idx: Index in batch

        Raises:
            ParserError: If result is invalid
        """
        if not isinstance(result, dict):
            raise ParserError(f"Result {idx} must be dict, got {type(result)}")

        # Required fields
        required = ["idx", "resumo", "importance_score", "topicos", "entidades"]
        for field in required:
            if field not in result:
                raise ParserError(f"Result {idx} missing required field: {field}")

        # Validate idx
        if result["idx"] != idx:
            raise ParserError(
                f"Result idx mismatch: expected {idx}, got {result['idx']}"
            )

        # Validate resumo — permitir vazio apenas para itens triviais (score == 0.0)
        if not isinstance(result["resumo"], str):
            raise ParserError(f"Result {idx}: resumo must be string")
        score_zero = float(result.get("importance_score", 0)) == 0.0
        if len(result["resumo"].strip()) < 1 and not score_zero:
            raise ParserError(f"Result {idx}: resumo must be non-empty for non-trivial items")

        # Validate importance_score
        try:
            score = float(result["importance_score"])
            if not 0.0 <= score <= 1.0:
                raise ParserError(
                    f"Result {idx}: importance_score must be 0.0-1.0, got {score}"
                )
        except (ValueError, TypeError) as e:
            raise ParserError(
                f"Result {idx}: importance_score must be float: {e}"
            )

        # Validate topicos
        if not isinstance(result["topicos"], list):
            raise ParserError(f"Result {idx}: topicos must be list")

        for topico in result["topicos"]:
            if not isinstance(topico, str) or len(topico) < 2:
                raise ParserError(f"Result {idx}: invalid topico: {topico}")

        # Validate entidades
        if not isinstance(result["entidades"], list):
            raise ParserError(f"Result {idx}: entidades must be list")

        for ent in result["entidades"]:
            if not isinstance(ent, dict):
                raise ParserError(f"Result {idx}: entidade must be dict")

            for field in ["nome", "tipo", "contexto"]:
                if field not in ent:
                    raise ParserError(
                        f"Result {idx}: entidade missing field: {field}"
                    )

            # Accept any type — new types may emerge; log unknown ones
            if ent["tipo"] not in ResponseParser.VALID_ENTITY_TYPES:
                logger.debug(
                    f"Result {idx}: unknown entity type '{ent['tipo']}' — accepting anyway"
                )

        # Validate optional fields (new — don't fail if missing)
        if "action_items" in result and not isinstance(result["action_items"], list):
            raise ParserError(f"Result {idx}: action_items must be list")

        if "sentimento" in result and result["sentimento"] not in (
            "positivo", "negativo", "neutro", "misto", None
        ):
            logger.debug(f"Result {idx}: unexpected sentimento '{result['sentimento']}'")

    @staticmethod
    def normalize_result(result: Dict) -> Dict[str, Any]:
        """
        Normalize a parsed result for database insertion.

        Converts:
        - importance_score to Decimal
        - Entity names to lowercase for deduplication
        - Handles missing optional fields

        Args:
            result: Parsed result from OpenAI

        Returns:
            Normalized result dict
        """
        normalized = {
            "idx": result["idx"],
            "resumo": result["resumo"].strip() or "[conteúdo trivial]",
            "importance_score": Decimal(str(result["importance_score"])),
            "topicos": [t.strip() for t in result.get("topicos", [])],
            "entidades": [],
            "action_items": result.get("action_items", []),
            "sentimento": result.get("sentimento", "neutro"),
            "tem_decisao": bool(result.get("tem_decisao", False)),
            "tem_pergunta": bool(result.get("tem_pergunta", False)),
        }

        # Normalize entidades
        for ent in result.get("entidades", []):
            variante_raw = ent.get("variante", "")
            normalized_ent = {
                "nome": ent["nome"].strip(),
                "nome_normalizado": ent["nome"].strip().lower(),
                "tipo": ent["tipo"].strip().lower(),
                "contexto": ent.get("contexto", "").strip(),
                "variante": variante_raw.strip() if variante_raw else None,
            }
            normalized["entidades"].append(normalized_ent)

        return normalized
