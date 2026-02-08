**cycletls**
============

Python HTTP client with advanced TLS fingerprinting. Make your requests
indistinguishable from real browser traffic using JA3, JA4, HTTP/2, and
HTTP/3 fingerprints.

.. code-block:: python

   import cycletls

   # Simple API -- zero boilerplate, auto-setup, auto-cleanup
   response = cycletls.get("https://example.com")
   print(response.status_code)  # 200
   print(response.json())

Unlike ``requests`` or ``httpx``, CycleTLS uses a Go shared library under the
hood to perform TLS handshakes that exactly match real browsers, bypassing
anti-bot detection that relies on TLS fingerprinting.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   overview

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   api
   advanced

.. toctree::
   :maxdepth: 1
   :caption: Project

   CHANGELOG
   License <https://github.com/Danny-Dasilva/cycletls_python/blob/main/LICENSE>
   GitHub Repository <https://github.com/Danny-Dasilva/cycletls_python>

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
