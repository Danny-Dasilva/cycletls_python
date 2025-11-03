"""
WebSocket Client Example for CycleTLS Python

This example demonstrates WebSocket functionality in CycleTLS using protocol="websocket".

Features demonstrated:
- Connecting to WebSocket servers
- Using wss:// (secure) and ws:// (insecure) URLs
- Setting protocol="websocket" for WebSocket upgrade
- Custom headers for WebSocket handshake

TODO: Full WebSocket implementation notes
----------------------------------------------
The current CycleTLS API supports WebSocket connection establishment via:
    protocol="websocket"

However, the following features may need additional implementation:
- Sending text messages to the WebSocket server
- Sending binary messages to the WebSocket server
- Receiving messages from the WebSocket server
- Bidirectional message streaming
- WebSocket ping/pong mechanism
- Graceful connection close with status codes

If these features are not yet available, you'll need to extend the API
or use the WebSocket connection for initial handshake only.
"""

from cycletls import CycleTLS
from cycletls.schema import Protocol


def example_websocket_connection():
    """Example: Basic WebSocket connection"""
    print("\n=== Basic WebSocket Connection ===")

    try:
        client = CycleTLS()

        # Connect to WebSocket echo server
        # Using protocol="websocket" for WebSocket upgrade
        response = client.get(
            "wss://echo.websocket.org",
            protocol=Protocol.WEBSOCKET
        )

        print(f"Connection Status: {response.status_code}")
        print(f"Headers: {response.headers}")

        # WebSocket upgrade should return 101 Switching Protocols
        if response.status_code == 101:
            print("WebSocket connection established successfully!")
        elif response.status_code == 200:
            print("Connection established (status 200)")
        else:
            print(f"Unexpected status code: {response.status_code}")

        # TODO: Send and receive messages
        # Currently, you would need additional API methods like:
        # client.ws_send(response.request_id, "Hello WebSocket!")
        # message = client.ws_receive(response.request_id)

        client.close()

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: WebSocket functionality may not be fully implemented.")
        print("Check if the underlying Go binary supports WebSocket protocol.")


def example_websocket_with_headers():
    """Example: WebSocket connection with custom headers"""
    print("\n=== WebSocket with Custom Headers ===")

    try:
        client = CycleTLS()

        # Custom headers for WebSocket handshake
        custom_headers = {
            "User-Agent": "CycleTLS-Python-WebSocket-Client",
            "Origin": "https://example.com",
            # WebSocket subprotocols
            "Sec-WebSocket-Protocol": "chat, superchat"
        }

        response = client.get(
            "wss://echo.websocket.org",
            protocol=Protocol.WEBSOCKET,
            headers=custom_headers
        )

        print(f"Connection Status: {response.status_code}")
        print(f"Response Headers: {response.headers}")

        if response.status_code in [101, 200]:
            print("WebSocket connection with custom headers successful!")

        client.close()

    except Exception as e:
        print(f"Error: {e}")


def example_websocket_insecure():
    """Example: Insecure WebSocket connection (ws://)"""
    print("\n=== Insecure WebSocket Connection (ws://) ===")

    try:
        client = CycleTLS()

        # Note: Using ws:// instead of wss:// (not recommended for production)
        # This example assumes a local WebSocket server
        response = client.get(
            "ws://localhost:8080/ws",
            protocol=Protocol.WEBSOCKET,
            timeout=5
        )

        print(f"Connection Status: {response.status_code}")
        print("Connected to local WebSocket server!")

        client.close()

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: This example requires a local WebSocket server")
        print("running on ws://localhost:8080/ws")


def example_websocket_with_proxy():
    """Example: WebSocket connection through proxy"""
    print("\n=== WebSocket Connection Through Proxy ===")

    try:
        client = CycleTLS()

        # Connect to WebSocket through SOCKS5 proxy
        response = client.get(
            "wss://echo.websocket.org",
            protocol=Protocol.WEBSOCKET,
            proxy="socks5://127.0.0.1:9050",
            timeout=10
        )

        print(f"Connection Status: {response.status_code}")

        if response.status_code in [101, 200]:
            print("WebSocket connection through proxy successful!")

        client.close()

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: This requires a SOCKS5 proxy on 127.0.0.1:9050")


def example_websocket_with_ja3():
    """Example: WebSocket with JA3 fingerprinting"""
    print("\n=== WebSocket with JA3 Fingerprint ===")

    try:
        client = CycleTLS()

        # Chrome-like JA3 fingerprint
        ja3_chrome = "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-49171-49172-156-157-47-53,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"

        response = client.get(
            "wss://echo.websocket.org",
            protocol=Protocol.WEBSOCKET,
            ja3=ja3_chrome,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        print(f"Connection Status: {response.status_code}")
        print("WebSocket with custom JA3 fingerprint!")

        client.close()

    except Exception as e:
        print(f"Error: {e}")


def example_websocket_url_validation():
    """Example: WebSocket URL format validation"""
    print("\n=== WebSocket URL Validation ===")

    # Valid WebSocket URLs
    valid_urls = [
        "ws://localhost:8080",
        "wss://echo.websocket.org",
        "ws://example.com/ws",
        "wss://example.com:443/websocket/v1"
    ]

    print("Valid WebSocket URLs:")
    for url in valid_urls:
        scheme = "secure" if url.startswith("wss://") else "insecure"
        print(f"  {url} ({scheme})")

    # Invalid WebSocket URLs
    invalid_urls = [
        "http://example.com",  # Should be ws:// or wss://
        "https://example.com",  # Should be ws:// or wss://
    ]

    print("\nInvalid WebSocket URLs:")
    for url in invalid_urls:
        print(f"  {url} (use ws:// or wss:// for WebSocket)")


def example_websocket_protocol_constant():
    """Example: Using Protocol enum for WebSocket"""
    print("\n=== Using Protocol Enum ===")

    # Import Protocol enum
    from cycletls.schema import Protocol

    print(f"Protocol.WEBSOCKET = '{Protocol.WEBSOCKET}'")
    print(f"Protocol.HTTP1 = '{Protocol.HTTP1}'")
    print(f"Protocol.HTTP2 = '{Protocol.HTTP2}'")
    print(f"Protocol.SSE = '{Protocol.SSE}'")

    print("\nYou can use Protocol.WEBSOCKET instead of the string 'websocket'")
    print("Example: protocol=Protocol.WEBSOCKET")


# TODO: These examples show what the API COULD look like
# if full WebSocket message sending/receiving is implemented

def example_websocket_send_message_TODO():
    """
    TODO: Example of sending WebSocket messages

    This is a placeholder showing what the API might look like
    when full WebSocket support is implemented.
    """
    print("\n=== TODO: WebSocket Send Message ===")
    print("This feature may not be implemented yet.")
    print("\nProposed API:")
    print("""
    client = CycleTLS()

    # Connect
    response = client.get(
        "wss://echo.websocket.org",
        protocol=Protocol.WEBSOCKET
    )

    # Send text message
    client.ws_send(response.request_id, "Hello WebSocket!")

    # Send binary message
    binary_data = b'\\x00\\x01\\x02\\x03'
    client.ws_send_binary(response.request_id, binary_data)

    client.close()
    """)


def example_websocket_receive_message_TODO():
    """
    TODO: Example of receiving WebSocket messages

    This is a placeholder showing what the API might look like
    when full WebSocket support is implemented.
    """
    print("\n=== TODO: WebSocket Receive Message ===")
    print("This feature may not be implemented yet.")
    print("\nProposed API:")
    print("""
    client = CycleTLS()

    # Connect
    response = client.get(
        "wss://echo.websocket.org",
        protocol=Protocol.WEBSOCKET
    )

    # Send a message
    client.ws_send(response.request_id, "Hello!")

    # Receive echo response
    message = client.ws_receive(response.request_id, timeout=5)
    print(f"Received: {message.data}")

    client.close()
    """)


def example_websocket_ping_pong_TODO():
    """
    TODO: Example of WebSocket ping/pong

    This is a placeholder showing what the API might look like
    when full WebSocket support is implemented.
    """
    print("\n=== TODO: WebSocket Ping/Pong ===")
    print("This feature may not be implemented yet.")
    print("\nProposed API:")
    print("""
    client = CycleTLS()

    response = client.get(
        "wss://echo.websocket.org",
        protocol=Protocol.WEBSOCKET
    )

    # Send ping
    client.ws_ping(response.request_id)

    # Wait for pong
    pong = client.ws_receive(response.request_id, timeout=5)
    print("Received pong!")

    client.close()
    """)


def main():
    """Run all WebSocket examples"""
    print("=" * 60)
    print("CycleTLS WebSocket Client Examples")
    print("=" * 60)

    # Working examples
    example_websocket_connection()
    example_websocket_with_headers()
    example_websocket_insecure()
    example_websocket_with_proxy()
    example_websocket_with_ja3()
    example_websocket_url_validation()
    example_websocket_protocol_constant()

    # TODO examples (not implemented yet)
    example_websocket_send_message_TODO()
    example_websocket_receive_message_TODO()
    example_websocket_ping_pong_TODO()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("\nKey Points:")
    print("- Use protocol=Protocol.WEBSOCKET for WebSocket connections")
    print("- Use wss:// for secure WebSocket, ws:// for insecure")
    print("- WebSocket handshake returns status 101 (Switching Protocols)")
    print("- Custom headers can be passed during WebSocket upgrade")
    print("\nTODO Features:")
    print("- Message sending/receiving may require additional API implementation")
    print("- Check the underlying Go binary for full WebSocket support")
    print("- Refer to test_websocket.py for current implementation status")
    print("=" * 60)


if __name__ == "__main__":
    main()
