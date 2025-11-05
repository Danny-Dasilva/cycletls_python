"""
Data structures for CycleTLS.

This module contains utility classes for handling HTTP-related data structures
in a way that's consistent with the requests library.
"""

from collections.abc import MutableMapping
from typing import List, Optional, Iterator, Tuple, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .schema import Cookie


def _get_cookie_class():
    """Import Cookie lazily to avoid circular imports."""
    from .schema import Cookie

    return Cookie


class CaseInsensitiveDict(MutableMapping):
    """A case-insensitive dict-like object.

    Implements all methods and operations of MutableMapping as well as dict's .copy().
    All keys are expected to be strings. The structure remembers the case of the last
    key to be set, and iter(instance), keys(), items(), iterkeys(), and iteritems()
    will contain case-sensitive keys. However, querying and contains testing is case
    insensitive::

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the value of a
    ``'Content-Encoding'`` response header, regardless of how the header name
    was originally stored.

    If the constructor, .update, or equality comparison operations are given keys
    that have equal ``.lower()``s, the behavior is undefined.
    """

    def __init__(self, data=None, **kwargs):
        self._store = {}
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return (
            (lowerkey, keyval[1])
            for (lowerkey, keyval)
            in self._store.items()
        )

    def __eq__(self, other):
        if isinstance(other, MutableMapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return str(dict(self.items()))


class CookieJar:
    """A dict-like container for managing cookies.

    This class provides a convenient interface for working with Cookie objects,
    allowing both dict-like access and Cookie object manipulation.

    Example::

        jar = CookieJar([Cookie(name='session', value='abc123')])
        jar['session']  # Returns 'abc123'
        jar.set('user', 'john', domain='.example.com')
        jar.get_dict()  # Returns {'session': 'abc123', 'user': 'john'}
    """

    def __init__(self, cookies: Optional[List['Cookie']] = None):
        """Initialize a CookieJar with an optional list of Cookie objects.

        Args:
            cookies: A list of Cookie objects to initialize the jar with.
        """
        self._cookies = {}
        if cookies:
            for cookie in cookies:
                self._cookies[cookie.name] = cookie

    def __getitem__(self, name: str) -> str:
        """Get a cookie's value by name.

        Args:
            name: The name of the cookie.

        Returns:
            The value of the cookie.

        Raises:
            KeyError: If the cookie doesn't exist.
        """
        return self._cookies[name].value

    def __setitem__(self, name: str, value: str):
        """Set a cookie with just a name and value.

        Args:
            name: The name of the cookie.
            value: The value of the cookie.
        """
        cookie_cls = _get_cookie_class()
        self._cookies[name] = cookie_cls(name=name, value=value)

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a cookie's value by name, returning a default if not found.

        Args:
            name: The name of the cookie.
            default: The value to return if the cookie doesn't exist.

        Returns:
            The cookie's value, or the default value if not found.
        """
        cookie = self._cookies.get(name)
        return cookie.value if cookie else default

    def set(self, name: str, value: str, **kwargs) -> None:
        """Set a cookie with full attributes.

        Args:
            name: The name of the cookie.
            value: The value of the cookie.
            **kwargs: Additional Cookie attributes (path, domain, expires, etc.).
        """
        cookie_cls = _get_cookie_class()
        self._cookies[name] = cookie_cls(name=name, value=value, **kwargs)

    def items(self) -> Iterator[Tuple[str, str]]:
        """Return an iterator of (name, value) tuples for all cookies.

        Yields:
            Tuples of (cookie_name, cookie_value).
        """
        for cookie in self._cookies.values():
            yield (cookie.name, cookie.value)

    def get_dict(self) -> dict:
        """Return a simple dict of cookie names to values.

        Returns:
            A dictionary mapping cookie names to their values.
        """
        return {name: cookie.value for name, cookie in self._cookies.items()}

    def get_cookies(self) -> List['Cookie']:
        """Return a list of all Cookie objects.

        Returns:
            A list of all Cookie objects in the jar.
        """
        return list(self._cookies.values())

    def __iter__(self) -> Iterator[str]:
        """Iterate over cookie names.

        Yields:
            Cookie names.
        """
        return iter(self._cookies.keys())

    def __len__(self) -> int:
        """Return the number of cookies in the jar.

        Returns:
            The number of cookies.
        """
        return len(self._cookies)

    def __contains__(self, name: str) -> bool:
        """Check if a cookie exists in the jar.

        Args:
            name: The name of the cookie.

        Returns:
            True if the cookie exists, False otherwise.
        """
        return name in self._cookies

    def __eq__(self, other: Any) -> bool:
        """Compare two CookieJars for equality.

        Args:
            other: Another CookieJar or dict to compare with.

        Returns:
            True if the cookies are equal, False otherwise.
        """
        if isinstance(other, CookieJar):
            return self.get_dict() == other.get_dict()
        elif isinstance(other, dict):
            return self.get_dict() == other
        return NotImplemented

    def __repr__(self) -> str:
        """Return a string representation of the CookieJar.

        Returns:
            A string representation showing all cookies.
        """
        return f"<CookieJar({len(self)} cookies)>"

    def __str__(self) -> str:
        """Return a user-friendly string representation.

        Returns:
            A string showing the cookie dict.
        """
        return str(self.get_dict())
