"""
Batch Worker for Módulo 4 - AI Processing with GPT-4o mini.

Orquestra o pipeline completo:
1. Polling a cada 3 min por transcrições pendentes
2. Envia lote de 15 para GPT-4o mini
3. Parse resposta com 3 níveis de fallback
4. Salva fragmentos, entidades, tópicos no banco
5. Rastreia custo e impõe limite diário
"""

import threading
import time
from typing import Dict, Any, List
from decimal import Decimal

from config import settings
from utils import setup_logger, is_shutdown_requested
from modulo4_processamento.openai_client import OpenAIClient, OpenAIClientError
from modulo4_processamento.prompt_builder import PromptBuilder, PromptBuilderError
from modulo4_processamento.response_parser import ResponseParser, ParserError
from modulo4_processamento.cost_tracker import CostTracker, CostTrackerError
from modulo4_processamento import db_queries
from modulo5_estruturado.entity_resolver import EntityResolver
from modulo5_estruturado import db_queries as m5_db
from modulo3_armazenamento.db import get_connection

logger = setup_logger(__name__)


def _apply_correcoes(pending: list, USUARIO_ID: int = 1) -> list:
    """
    Aplica correções de texto nas transcrições antes de enviar ao LLM.

    Carrega a tabela correcoes_texto do banco e substitui todas as
    ocorrências (case-insensitive) nas transcrições.

    Args:
        pending: Lista de dicts com campo 'texto' (transcrições brutas)
        USUARIO_ID: ID do usuário para filtrar correções

    Returns:
        Lista de transcrições com correções aplicadas
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT texto_errado, texto_correto FROM correcoes_texto WHERE usuario_id = %s",
            (USUARIO_ID,),
        )
        correcoes = cursor.fetchall()

    if not correcoes:
        return pending

    corrigidos = 0
    result = []
    for item in pending:
        texto = item.get("texto", "") or ""
        original = texto
        for errado, correto in correcoes:
            # Case-insensitive replacement preserving dict structure
            import re
            texto = re.sub(re.escape(errado), correto, texto, flags=re.IGNORECASE)
        if texto != original:
            corrigidos += 1
            item = dict(item, texto=texto)
        result.append(item)

    if corrigidos:
        logger.info(f"✏️ Correções aplicadas em {corrigidos}/{len(pending)} transcrições")

    return result


class BatchWorkerError(Exception):
    """Base exception for batch worker errors."""
    pass


class BatchWorker(threading.Thread):
    """
    Main worker thread for Module 4 AI processing.

    Runs a polling loop:
    - Every MODULO4_POLL_INTERVAL_SECONDS (default 180s)
    - Fetch up to MODULO4_BATCH_SIZE (default 15) pending transcriptions
    - Send to GPT-4o mini for extraction
    - Save results to database
    - Track cost and enforce daily limits
    """

    def __init__(self):
        """Initialize the batch worker."""
        super().__init__(daemon=False)
        self.name = "BatchWorker"

        try:
            self.openai_client = OpenAIClient()
            self.prompt_builder = PromptBuilder()
            self.cost_tracker = CostTracker(settings.modulo4.daily_cost_limit_usd)
            logger.info("✅ BatchWorker initialized")
        except (OpenAIClientError, PromptBuilderError) as e:
            raise BatchWorkerError(f"Failed to initialize: {e}")

    def run(self):
        """Main worker loop."""
        logger.info("BatchWorker started")

        # Reset stuck processing records on startup (recovery from crashes)
        try:
            reset_count = db_queries.reset_stuck_processing(timeout_minutes=10)
            if reset_count > 0:
                logger.info(f"🔄 Recovered {reset_count} stuck processing records")
        except Exception as e:
            logger.warning(f"⚠️  Could not reset stuck records: {e}")

        while not is_shutdown_requested():
            try:
                self._process_batch()
                # Sleep for configured interval
                time.sleep(settings.modulo4.poll_interval_seconds)

            except Exception as e:
                logger.error(f"❌ Unexpected error in BatchWorker: {e}", exc_info=True)
                time.sleep(10)  # Prevent tight loop on repeated errors

        logger.info("BatchWorker shutting down")

    def _process_batch(self):
        """
        Fetch pending transcriptions and process them in a batch.

        This is the main orchestration method.
        """
        try:
            # Fetch pending transcriptions
            pending = db_queries.fetch_pending_transcriptions(settings.modulo4.batch_size)

            if not pending:
                logger.debug("No pending transcriptions to process")
                return

            logger.info(f"Processing batch of {len(pending)} transcriptions...")

            # Mark all as processing
            for item in pending:
                db_queries.mark_processing(item["id"])

            # Fetch existing entities and topics for disambiguation context
            existing_entities = []
            existing_topics = []
            try:
                existing_entities = m5_db.fetch_existing_entities(limit=100)
                existing_topics = m5_db.fetch_existing_topics(limit=50)
                logger.debug(
                    f"Loaded {len(existing_entities)} entities and "
                    f"{len(existing_topics)} topics for context"
                )
            except m5_db.M5DBQueriesError as e:
                logger.warning(f"⚠️  Could not load entity/topic context: {e}")

            # Apply text corrections before sending to LLM
            # (fixes Whisper transcription errors: "prômitos" → "prompts")
            try:
                pending = _apply_correcoes(pending, USUARIO_ID=1)
            except Exception as e:
                logger.warning(f"⚠️  Could not apply text corrections: {e}")

            # Build prompts with entity/topic context
            system_prompt = self.prompt_builder.build_system_prompt(
                existing_entities=existing_entities,
                existing_topics=existing_topics,
            )
            user_message = self.prompt_builder.build_user_message(pending)

            # Call OpenAI
            response_text, input_tokens, output_tokens = self.openai_client.call_with_retry(
                system_prompt, user_message
            )

            # Calculate cost
            cost_usd = self.openai_client.calculate_cost(input_tokens, output_tokens)

            # Check cost limit
            if not self.cost_tracker.check_and_log_cost(
                input_tokens,
                output_tokens,
                cost_usd,
                fragmentos_processados=0,  # Will update below
                fragmentos_skipped=0,
            ):
                # Cost limit exceeded - mark all as error and return
                for item in pending:
                    db_queries.mark_error(
                        item["id"],
                        f"Daily cost limit (${settings.modulo4.daily_cost_limit_usd}) exceeded"
                    )
                logger.error("❌ Daily cost limit exceeded - stopping batch processing")
                return

            # Parse response
            try:
                parsed = ResponseParser.parse_response(response_text, len(pending))
            except ParserError as e:
                logger.error(f"❌ Failed to parse batch response: {e}")
                # Mark all as error
                for item in pending:
                    db_queries.mark_error(item["id"], f"Parse error: {str(e)[:200]}")
                return

            # Process each result
            fragmentos_processados = 0
            fragmentos_skipped = 0

            for result in parsed.get("resultados", []):
                try:
                    self._process_result(
                        result, pending, fragmentos_processados, fragmentos_skipped,
                        existing_entities=existing_entities,
                    )
                    if result["importance_score"] >= settings.modulo4.importance_threshold:
                        fragmentos_processados += 1
                    else:
                        fragmentos_skipped += 1
                except Exception as e:
                    logger.error(f"❌ Error processing result idx {result['idx']}: {e}")
                    if result["idx"] < len(pending):
                        db_queries.mark_error(
                            pending[result["idx"]]["id"],
                            f"Processing error: {str(e)[:200]}"
                        )

            # Update cost tracker with final counts
            try:
                self.cost_tracker.check_and_log_cost(
                    input_tokens,
                    output_tokens,
                    0,  # Cost already logged above
                    fragmentos_processados,
                    fragmentos_skipped,
                )
            except CostTrackerError:
                pass  # Already logged cost, don't fail

            logger.info(
                f"✅ Batch processed: {fragmentos_processados} saved, "
                f"{fragmentos_skipped} skipped"
            )

        except OpenAIClientError as e:
            logger.error(f"❌ OpenAI API error: {e}")
            # Don't mark as error - will retry on next cycle

        except db_queries.DBQueriesError as e:
            logger.error(f"❌ Database error: {e}")

    def _process_result(
        self,
        result: Dict[str, Any],
        pending: List[Dict[str, Any]],
        fragmentos_processados: int,
        fragmentos_skipped: int,
        existing_entities: List[Dict[str, Any]] = None,
    ):
        """
        Process a single extracted result.

        Args:
            result: Parsed result from OpenAI
            pending: List of original pending transcriptions
            fragmentos_processados: Counter (for logging)
            fragmentos_skipped: Counter (for logging)
            existing_entities: List of known entities for disambiguation (M5)
        """
        idx = result["idx"]
        if idx >= len(pending):
            raise ValueError(f"Result idx {idx} exceeds batch size {len(pending)}")

        transcricao = pending[idx]
        transcricao_id = transcricao["id"]

        # Normalize result
        normalized = ResponseParser.normalize_result(result)

        # Check importance threshold
        if normalized["importance_score"] < Decimal(str(settings.modulo4.importance_threshold)):
            db_queries.mark_skipped(
                transcricao_id,
                f"importance_score {normalized['importance_score']} < {settings.modulo4.importance_threshold}"
            )
            return

        # Dry run mode - don't insert
        if settings.modulo4.dry_run:
            logger.info(f"[DRY RUN] Would save fragment for transcricao {transcricao_id}")
            db_queries.mark_processed(transcricao_id)
            return

        # Save fragment with M5 fields
        fragmento_id = db_queries.save_fragment(
            transcricao_id,
            normalized["resumo"],
            normalized["importance_score"],
            input_tokens=0,  # Will be set by openai_client
            output_tokens=0,
            model_used=self.openai_client.model,
            sentimento=normalized.get("sentimento"),
            tem_decisao=normalized.get("tem_decisao", False),
            tem_pergunta=normalized.get("tem_pergunta", False),
        )
        logger.debug(f"Saved fragment {fragmento_id} for transcricao {transcricao_id}")

        # Save action items (M5)
        action_items = normalized.get("action_items", [])
        if action_items:
            try:
                saved = m5_db.save_action_items(fragmento_id, action_items)
                logger.debug(f"Saved {saved} action items for fragmento {fragmento_id}")
            except m5_db.M5DBQueriesError as e:
                logger.warning(f"⚠️  Could not save action items: {e}")

        # Save tópicos and link to fragment
        for topico_str in normalized["topicos"]:
            topico_id = db_queries.upsert_topico(topico_str)
            eh_principal = normalized["topicos"].index(topico_str) == 0  # First is main
            db_queries.save_fragmento_topico(
                fragmento_id,
                topico_id,
                Decimal("1.0"),
                eh_principal=eh_principal
            )

        # Save entidades with EntityResolver disambiguation (M5)
        resolver = EntityResolver(existing_entities or [])
        for ent in normalized["entidades"]:
            resolve_result = resolver.resolve(ent["nome"], ent["tipo"])

            if resolve_result.entidade_id and resolve_result.status in ("ativo", "pendente"):
                # Reutilize existing entity (identified by resolver)
                entidade_id = resolve_result.entidade_id
                # Mark as pendente if fuzzy match (needs human review)
                if resolve_result.status == "pendente":
                    try:
                        m5_db.update_entity_status(entidade_id, "pendente")
                    except m5_db.M5DBQueriesError as e:
                        logger.warning(f"⚠️  Could not mark entity as pendente: {e}")
            else:
                # New entity — create it
                entidade_id = db_queries.upsert_entidade(
                    ent["nome"],
                    ent["nome_normalizado"],
                    ent["tipo"],
                )

            db_queries.save_fragmento_entidade(
                fragmento_id,
                entidade_id,
                ent["contexto"]
            )

        # Mark transcription as processed
        db_queries.mark_processed(transcricao_id, fragmento_id)
        logger.debug(
            f"Processed: fragmento_id={fragmento_id}, "
            f"topicos={len(normalized['topicos'])}, "
            f"entidades={len(normalized['entidades'])}, "
            f"action_items={len(action_items)}"
        )
