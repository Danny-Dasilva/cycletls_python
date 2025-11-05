"""Configuration management for CycleTLS module-level defaults."""

import threading
from typing import Any, Dict, Optional

# Configuration storage
_config: Dict[str, Any] = {}

# Cache for merged defaults (optimization for empty kwargs)
_merged_cache: Optional[Dict[str, Any]] = None
_cache_lock = threading.Lock()

# Mapping from config keys to parameter names (pre-computed for performance)
_CONFIG_TO_PARAM_MAPPING = {
    'default_ja3': 'ja3',
    'default_ja4r': 'ja4r',
    'default_http2_fingerprint': 'http2_fingerprint',
    'default_quic_fingerprint': 'quic_fingerprint',
    'default_disable_grease': 'disable_grease',
    'default_user_agent': 'user_agent',
    'default_proxy': 'proxy',
    'default_timeout': 'timeout',
    'default_enable_connection_reuse': 'enable_connection_reuse',
    'default_insecure_skip_verify': 'insecure_skip_verify',
    'default_server_name': 'server_name',
    'default_force_http1': 'force_http1',
    'default_force_http3': 'force_http3',
    'default_protocol': 'protocol',
    'default_disable_redirect': 'disable_redirect',
    'default_header_order': 'header_order',
    'default_order_headers_as_provided': 'order_headers_as_provided',
}

# Valid configuration attributes
_CONFIGURABLE_ATTRS = {
    'default_ja3',
    'default_ja4r',
    'default_http2_fingerprint',
    'default_quic_fingerprint',
    'default_disable_grease',
    'default_user_agent',
    'default_proxy',
    'default_timeout',
    'default_port',
    'default_enable_connection_reuse',
    'default_insecure_skip_verify',
    'default_server_name',
    'default_force_http1',
    'default_force_http3',
    'default_protocol',
    'default_disable_redirect',
    'default_header_order',
    'default_order_headers_as_provided',
}


def _validate_config(name: str, value: Any) -> None:
    """Validate configuration values."""
    validators = {
        'default_timeout': lambda v: isinstance(v, (int, float)) and v > 0,
        'default_port': lambda v: isinstance(v, int) and 1 <= v <= 65535,
        'default_enable_connection_reuse': lambda v: isinstance(v, bool),
        'default_insecure_skip_verify': lambda v: isinstance(v, bool),
        'default_force_http1': lambda v: isinstance(v, bool),
        'default_force_http3': lambda v: isinstance(v, bool),
        'default_disable_redirect': lambda v: isinstance(v, bool),
        'default_disable_grease': lambda v: isinstance(v, bool),
        'default_order_headers_as_provided': lambda v: isinstance(v, bool),
        'default_proxy': lambda v: v is None or isinstance(v, str),
        'default_ja3': lambda v: v is None or isinstance(v, str),
        'default_ja4r': lambda v: v is None or isinstance(v, str),
        'default_user_agent': lambda v: v is None or isinstance(v, str),
        'default_server_name': lambda v: v is None or isinstance(v, str),
        'default_http2_fingerprint': lambda v: v is None or isinstance(v, str),
        'default_quic_fingerprint': lambda v: v is None or isinstance(v, str),
        'default_header_order': lambda v: v is None or isinstance(v, list),
    }

    validator = validators.get(name)
    if validator and not validator(value):
        raise ValueError(f"Invalid value for {name}: {value}")


def _merge_defaults(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge module-level defaults with per-request kwargs.

    Per-request kwargs take precedence over defaults.

    Args:
        kwargs: Request-specific keyword arguments

    Returns:
        Merged dictionary with defaults + kwargs
    """
    global _merged_cache

    # Fast path 1: if no defaults are set, just return kwargs
    if not _config:
        return kwargs

    # Fast path 2: if kwargs are empty, use cached merged defaults
    if not kwargs:
        if _merged_cache is not None:
            return _merged_cache

        # Build and cache the defaults-only result
        with _cache_lock:
            # Double-check after acquiring lock
            if _merged_cache is None:
                result = {}
                for config_key, param_key in _CONFIG_TO_PARAM_MAPPING.items():
                    if config_key in _config:
                        result[param_key] = _config[config_key]
                _merged_cache = result
            return _merged_cache

    # Slow path: merge defaults with non-empty kwargs
    result = {}

    # Apply defaults first (only if not in kwargs)
    for config_key, param_key in _CONFIG_TO_PARAM_MAPPING.items():
        if config_key in _config and param_key not in kwargs:
            result[param_key] = _config[config_key]

    # Override with kwargs
    result.update(kwargs)
    return result


def set_default(**kwargs) -> None:
    """
    Set default configuration values for module-level functions.

    Args:
        ja3: Default JA3 fingerprint string
        ja4r: Default JA4 raw format fingerprint
        http2_fingerprint: Default HTTP/2 fingerprint
        quic_fingerprint: Default QUIC fingerprint
        disable_grease: Default GREASE disable setting
        user_agent: Default User-Agent string
        proxy: Default proxy URL
        timeout: Default timeout in seconds
        port: Default WebSocket port for subprocess
        enable_connection_reuse: Default connection reuse setting
        insecure_skip_verify: Default TLS verification setting
        server_name: Default SNI override
        force_http1: Default HTTP/1.1 forcing
        force_http3: Default HTTP/3 forcing
        protocol: Default protocol selection
        disable_redirect: Default redirect handling
        header_order: Default header ordering
        order_headers_as_provided: Default header order preservation

    Example:
        >>> import cycletls
        >>> cycletls.set_default(
        ...     proxy='socks5://127.0.0.1:9050',
        ...     timeout=10,
        ...     ja3='771,4865-4866...'
        ... )
        >>> response = cycletls.get('https://example.com')  # Uses defaults
    """
    global _merged_cache

    for key, value in kwargs.items():
        config_key = f'default_{key}'
        if config_key not in _CONFIGURABLE_ATTRS:
            raise ValueError(f"Unknown configuration option: {key}")
        _validate_config(config_key, value)
        _config[config_key] = value

    # Invalidate cache when defaults change
    _merged_cache = None


def reset_defaults() -> None:
    """
    Reset all default configuration values.

    Example:
        >>> import cycletls
        >>> cycletls.set_default(proxy='socks5://127.0.0.1:9050')
        >>> cycletls.reset_defaults()  # Clear all defaults
    """
    global _merged_cache

    _config.clear()
    # Invalidate cache when defaults are reset
    _merged_cache = None


def get_default(key: str) -> Optional[Any]:
    """
    Get a default configuration value.

    Args:
        key: Configuration key (without 'default_' prefix)

    Returns:
        The configuration value, or None if not set

    Example:
        >>> import cycletls
        >>> cycletls.set_default(timeout=10)
        >>> cycletls.get_default('timeout')
        10
    """
    config_key = f'default_{key}'
    if config_key not in _CONFIGURABLE_ATTRS:
        raise ValueError(f"Unknown configuration option: {key}")
    return _config.get(config_key)
