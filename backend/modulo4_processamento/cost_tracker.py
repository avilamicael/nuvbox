"""
Cost tracking for Módulo 4.

Responsável por:
1. Rastrear custo diário de tokens
2. Impor limite diário ($2 default)
3. Registrar em modulo4_uso_diario no banco
"""

from datetime import datetime, date
from decimal import Decimal
from modulo3_armazenamento.db import get_connection
from utils import setup_logger

logger = setup_logger(__name__)


class CostTrackerError(Exception):
    """Base exception for cost tracking errors."""
    pass


class CostTracker:
    """
    Track daily OpenAI API costs and enforce limits.
    """

    def __init__(self, daily_limit_usd: float):
        """
        Initialize tracker with daily limit.

        Args:
            daily_limit_usd: Maximum cost per day in USD
        """
        self.daily_limit_usd = Decimal(str(daily_limit_usd))

    def check_and_log_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        fragmentos_processados: int = 0,
        fragmentos_skipped: int = 0,
    ) -> bool:
        """
        Check if cost is within daily limit and log to database.

        Args:
            input_tokens: Input tokens used in this call
            output_tokens: Output tokens used in this call
            cost_usd: Cost of this call in USD
            fragmentos_processados: Fragments processed in this call
            fragmentos_skipped: Fragments skipped (importance < threshold)

        Returns:
            True if within limit, False if would exceed

        Raises:
            CostTrackerError: If database operation fails
        """
        today = date.today()
        new_cost = Decimal(str(cost_usd))

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                # Get today's accumulated cost
                cursor.execute(
                    "SELECT custo_usd, tokens_input, tokens_output FROM modulo4_uso_diario WHERE data = %s",
                    (today,)
                )
                row = cursor.fetchone()

                if row:
                    current_cost = row[0]
                    current_input = row[1]
                    current_output = row[2]
                else:
                    current_cost = Decimal("0.0")
                    current_input = 0
                    current_output = 0

                # Check if adding this cost would exceed limit
                projected_cost = current_cost + new_cost
                if projected_cost > self.daily_limit_usd:
                    logger.error(
                        f"❌ COST LIMIT EXCEEDED: "
                        f"Current: ${current_cost}, New: ${new_cost}, "
                        f"Projected: ${projected_cost}, Limit: ${self.daily_limit_usd}"
                    )
                    return False

                # Log to database
                if row:
                    # Update existing record
                    cursor.execute(
                        """
                        UPDATE modulo4_uso_diario
                        SET tokens_input = tokens_input + %s,
                            tokens_output = tokens_output + %s,
                            custo_usd = custo_usd + %s,
                            fragmentos_processados = fragmentos_processados + %s,
                            fragmentos_skipped = fragmentos_skipped + %s,
                            atualizado_em = NOW()
                        WHERE data = %s
                        """,
                        (
                            input_tokens,
                            output_tokens,
                            new_cost,
                            fragmentos_processados,
                            fragmentos_skipped,
                            today,
                        )
                    )
                else:
                    # Insert new record
                    cursor.execute(
                        """
                        INSERT INTO modulo4_uso_diario
                        (data, tokens_input, tokens_output, custo_usd,
                         fragmentos_processados, fragmentos_skipped, atualizado_em)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        """,
                        (
                            today,
                            input_tokens,
                            output_tokens,
                            new_cost,
                            fragmentos_processados,
                            fragmentos_skipped,
                        )
                    )

                conn.commit()

                logger.info(
                    f"✅ Cost logged: ${new_cost} "
                    f"(daily total: ${projected_cost}/{self.daily_limit_usd})"
                )
                return True

        except Exception as e:
            logger.error(f"❌ Failed to log cost: {e}")
            raise CostTrackerError(f"Cost logging failed: {e}")

    @staticmethod
    def get_daily_usage(target_date: date = None) -> dict:
        """
        Get daily usage stats.

        Args:
            target_date: Date to query (default: today)

        Returns:
            Dict with usage stats or None if no data
        """
        if target_date is None:
            target_date = date.today()

        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT tokens_input, tokens_output, custo_usd,
                           fragmentos_processados, fragmentos_skipped, erros_count
                    FROM modulo4_uso_diario
                    WHERE data = %s
                    """,
                    (target_date,)
                )
                row = cursor.fetchone()

                if row:
                    return {
                        "data": target_date,
                        "tokens_input": row[0],
                        "tokens_output": row[1],
                        "custo_usd": float(row[2]),
                        "fragmentos_processados": row[3],
                        "fragmentos_skipped": row[4],
                        "erros_count": row[5],
                    }
                return None

        except Exception as e:
            logger.error(f"❌ Failed to get daily usage: {e}")
            return None
