import signal
import threading
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Global event for coordinated shutdown
shutdown_event = threading.Event()


def setup_signal_handlers():
    """
    Register SIGINT (Ctrl+C) and SIGTERM handlers to gracefully shutdown.
    This allows all threads to finish current tasks before exit.
    """
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}. Initiating graceful shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination


def is_shutdown_requested() -> bool:
    """Check if shutdown has been requested."""
    return shutdown_event.is_set()


def wait_for_shutdown():
    """Block until shutdown is requested (useful for main thread)."""
    shutdown_event.wait()
