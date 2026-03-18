"""
Módulo 4 - Processamento IA com GPT-4o mini

Responsável por:
1. Extrair entidades, tópicos, importance score e resumo de transcrições
2. Transformar dados brutos em memória estruturada
3. Gerenciar custo diário e rate limiting
"""

# Lazy import to avoid loading openai until needed
def __getattr__(name):
    if name == "BatchWorker":
        from modulo4_processamento.batch_worker import BatchWorker
        return BatchWorker
    raise AttributeError(f"Module {__name__!r} has no attribute {name!r}")

__all__ = ["BatchWorker"]
