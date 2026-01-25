"""Global session management for CycleTLS module-level functions."""

import atexit
import os
import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .api import CycleTLS

# Lazy import to avoid circular dependency
_CycleTLS = None


def _import_cycletls():
    """Lazy import to avoid circular dependency."""
    global _CycleTLS
    if _CycleTLS is None:
        from .api import CycleTLS

        _CycleTLS = CycleTLS


# Global state
_global_session: Optional["CycleTLS"] = None
_global_lock = threading.Lock()
_cleanup_registered = False
_parent_pid = os.getpid()


def get_global_session():
    """
    Get or create the global CycleTLS session.

    The session is lazily initialized on first use and automatically
    cleaned up on program exit.

    Returns:
        CycleTLS: The global session instance
    """
    global _global_session, _cleanup_registered, _parent_pid

    # Check if we're in a forked child process
    current_pid = os.getpid()
    if current_pid != _parent_pid:
        # We're in a forked child - reset to avoid sharing WebSocket
        _global_session = None
        _parent_pid = current_pid

    if _global_session is None:
        with _global_lock:  # Double-checked locking
            if _global_session is None:
                _import_cycletls()
                _global_session = _CycleTLS()

                # Register cleanup ONCE
                if not _cleanup_registered:
                    atexit.register(_cleanup_global_session)
                    _cleanup_registered = True

    return _global_session


def _cleanup_global_session():
    """
    Cleanup function called by atexit.

    Closes the global session and cleans up resources.
    """
    global _global_session
    if _global_session is not None:
        try:
            _global_session.close()
        except Exception:
            # Silently ignore cleanup errors during shutdown
            pass
        finally:
            _global_session = None


def close_global_session():
    """
    Manually close the global session.

    Useful for explicit cleanup in notebooks or when you want to
    reset the global session with different settings.

    Example:
        >>> import cycletls
        >>> response = cycletls.get('https://example.com')
        >>> cycletls.close_global_session()  # Explicit cleanup
        >>> response = cycletls.get('https://example.com')  # New session
    """
    global _global_session
    if _global_session is not None:
        with _global_lock:
            if _global_session is not None:
                try:
                    _global_session.close()
                except Exception:
                    pass
                finally:
                    _global_session = None
