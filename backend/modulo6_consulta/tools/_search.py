"""
Helpers de busca para as ferramentas do M6.

unaccent_ilike: substitui  col ILIKE %s  por  unaccent(col) ILIKE unaccent(%s)
Isso permite que buscas sem acento encontrem registros com acento e vice-versa.
Exemplo: buscar "Marcio" encontra "Márcio"; buscar "irmao" encontra "irmão".

Requer a extensão PostgreSQL `unaccent` instalada no banco.
"""


def ui(column: str) -> str:
    """
    Retorna a expressão SQL para busca accent-insensitive.

    Args:
        column: nome da coluna ou expressão SQL (ex: 'e.nome', 'resumo')

    Returns:
        Ex: "unaccent(e.nome) ILIKE unaccent(%s)"
    """
    return f"unaccent({column}) ILIKE unaccent(%s)"
