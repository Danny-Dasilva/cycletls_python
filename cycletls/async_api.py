"""Async API for CycleTLS - backward compatibility shim.

AsyncCycleTLS is now a thin subclass of CycleTLS that maps sync method names
to their async equivalents (e.g. .get() -> .aget()). This allows existing code
using ``await AsyncCycleTLS().get(url)`` to continue working.

For new code, use CycleTLS directly with a-prefixed async methods:
    async with CycleTLS() as client:
        response = await client.aget(url)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Union

from .api import CycleTLS, ParamsType
from .fingerprints import TLSFingerprint
from .schema import Response


class AsyncCycleTLS(CycleTLS):
    """Backward-compatible async client.

    Use ``CycleTLS`` directly for new code — it supports both sync and async.
    """

    async def request(  # type: ignore[override]
        self,
        method: str,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        auth: Optional[Tuple[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        """Async request -- delegates to CycleTLS.arequest()."""
        return await self.arequest(
            method,
            url,
            params=params,
            data=data,
            json_data=json_data,
            files=files,
            fingerprint=fingerprint,
            **kwargs,
        )

    async def get(  # type: ignore[override]
        self,
        url: str,
        params: Optional[ParamsType] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        auth: Optional[Tuple[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        return await self.aget(url, params=params, fingerprint=fingerprint, **kwargs)

    async def options(  # type: ignore[override]
        self,
        url: str,
        params: Optional[ParamsType] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        auth: Optional[Tuple[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        return await self.aoptions(url, params=params, fingerprint=fingerprint, **kwargs)

    async def head(  # type: ignore[override]
        self,
        url: str,
        params: Optional[ParamsType] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        auth: Optional[Tuple[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        return await self.ahead(url, params=params, fingerprint=fingerprint, **kwargs)

    async def post(  # type: ignore[override]
        self,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        auth: Optional[Tuple[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        return await self.apost(
            url, params=params, data=data, json_data=json_data, fingerprint=fingerprint, **kwargs
        )

    async def put(  # type: ignore[override]
        self,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        auth: Optional[Tuple[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        return await self.aput(
            url, params=params, data=data, json_data=json_data, fingerprint=fingerprint, **kwargs
        )

    async def patch(  # type: ignore[override]
        self,
        url: str,
        params: Optional[ParamsType] = None,
        data: Optional[Union[Dict[str, Any], str, bytes]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        auth: Optional[Tuple[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        return await self.apatch(
            url, params=params, data=data, json_data=json_data, fingerprint=fingerprint, **kwargs
        )

    async def delete(  # type: ignore[override]
        self,
        url: str,
        params: Optional[ParamsType] = None,
        fingerprint: Optional[Union[str, TLSFingerprint]] = None,
        auth: Optional[Tuple[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        return await self.adelete(url, params=params, fingerprint=fingerprint, **kwargs)

    async def close(self) -> None:  # type: ignore[override]
        """Async close -- delegates to sync close (which is trivial)."""
        super().close()


# Convenience functions (retained for backward compatibility)
async def async_get(url: str, params: Optional[ParamsType] = None, **kwargs: Any) -> Response:
    """Send an async GET request (convenience function)."""
    async with CycleTLS() as client:
        return await client.aget(url, params=params, **kwargs)


async def async_post(
    url: str,
    params: Optional[ParamsType] = None,
    data: Optional[Union[Dict[str, Any], str, bytes]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Response:
    """Send an async POST request (convenience function)."""
    async with CycleTLS() as client:
        return await client.apost(url, params=params, data=data, json_data=json_data, **kwargs)


async def async_put(
    url: str,
    params: Optional[ParamsType] = None,
    data: Optional[Union[Dict[str, Any], str, bytes]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Response:
    """Send an async PUT request (convenience function)."""
    async with CycleTLS() as client:
        return await client.aput(url, params=params, data=data, json_data=json_data, **kwargs)


async def async_delete(url: str, params: Optional[ParamsType] = None, **kwargs: Any) -> Response:
    """Send an async DELETE request (convenience function)."""
    async with CycleTLS() as client:
        return await client.adelete(url, params=params, **kwargs)


__all__ = [
    "AsyncCycleTLS",
    "async_get",
    "async_post",
    "async_put",
    "async_delete",
]
