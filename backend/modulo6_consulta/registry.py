"""
Tool Registry for Módulo 6 — Query Agent.

Manages the tool catalog (JSON schemas) and dispatches calls to Python functions.
The LLM picks which tool to call; usuario_id is always injected server-side (never from LLM).
"""

from utils import setup_logger

logger = setup_logger(__name__)

_schemas: dict = {}     # nome → OpenAI-format tool schema
_functions: dict = {}   # nome → Python callable


class M6RegistryError(Exception):
    pass


def register_tool(name: str, description: str, parameters: dict):
    """
    Decorator that registers a function as a callable tool for the query agent.

    Args:
        name: Tool name (used by LLM in tool_calls)
        description: Human/LLM-readable description of what this tool does
        parameters: Dict of JSON Schema properties (without the outer "type": "object" envelope)

    Usage:
        @register_tool(
            name="my_tool",
            description="Does something useful",
            parameters={
                "query": {"type": "string", "description": "Search term"}
            }
        )
        def my_tool(query: str, usuario_id: int) -> list[dict]:
            ...
    """
    def decorator(fn):
        _schemas[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": list(parameters.keys()),
                },
            },
        }
        _functions[name] = fn
        logger.debug(f"Registered tool: {name}")
        return fn
    return decorator


def get_all_tools() -> list:
    """Return all registered tools in OpenAI tools=[...] format."""
    return list(_schemas.values())


def dispatch(nome: str, args: dict, usuario_id: int):
    """
    Execute a registered tool by name, injecting usuario_id server-side.

    Args:
        nome: Tool name from LLM tool_call
        args: Arguments from LLM (usuario_id excluded — injected here)
        usuario_id: Always injected server-side for security

    Returns:
        Tool result (list[dict] or any JSON-serializable value)

    Raises:
        M6RegistryError: If tool name is not registered
    """
    if nome not in _functions:
        raise M6RegistryError(f"Tool '{nome}' não registrada. Disponíveis: {list(_functions.keys())}")

    logger.info(f"🔧 Dispatch: {nome}({args})")
    return _functions[nome](**args, usuario_id=usuario_id)
