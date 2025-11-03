"""
Server-Sent Events (SSE) Client Example for CycleTLS Python

This example demonstrates Server-Sent Events functionality in CycleTLS
using protocol="sse".

SSE is a server push technology enabling clients to receive automatic updates
from a server via HTTP connection. SSE is commonly used for:
- Real-time notifications
- Live feeds (news, stock prices, social media)
- Progress updates
- Server monitoring dashboards

Features demonstrated:
- Connecting to SSE endpoints
- Using protocol="sse" for SSE streams
- Receiving event data
- Parsing SSE format (event, data, id, retry fields)

TODO: Full SSE implementation notes
----------------------------------------------
The current CycleTLS API supports SSE connection establishment via:
    protocol="sse"

However, the following features may need additional implementation:
- Streaming response handling (receiving events as they arrive)
- Event type filtering
- Automatic reconnection with Last-Event-ID
- Real-time event callbacks
- Long-lived connection management

If these features are not yet available, you'll receive all events
in a single response body after the connection closes.
"""

from cycletls import CycleTLS
from cycletls.schema import Protocol, SSEEvent


def parse_sse_response(body):
    """
    Parse SSE format from response body.

    SSE Format:
        event: eventType
        id: eventId
        data: event data
        retry: reconnectionTime

        (empty line marks end of event)

    Args:
        body: Response body string containing SSE data

    Returns:
        List of parsed events
    """
    events = []
    current_event = {}

    lines = body.split('\n')

    for line in lines:
        line = line.strip()

        if line.startswith('event:'):
            current_event['event'] = line[6:].strip()
        elif line.startswith('data:'):
            # SSE supports multiline data
            if 'data' in current_event:
                current_event['data'] += '\n' + line[5:].strip()
            else:
                current_event['data'] = line[5:].strip()
        elif line.startswith('id:'):
            current_event['id'] = line[3:].strip()
        elif line.startswith('retry:'):
            current_event['retry'] = int(line[6:].strip())
        elif line.startswith(':'):
            # Comment line (used for keep-alive)
            continue
        elif line == '':
            # Empty line marks end of event
            if current_event:
                events.append(current_event.copy())
                current_event = {}

    # Add last event if not empty
    if current_event:
        events.append(current_event)

    return events


def example_sse_connection():
    """Example: Basic SSE connection"""
    print("\n=== Basic SSE Connection ===")

    try:
        client = CycleTLS()

        # Connect to SSE stream endpoint
        # httpbin.org/stream/N returns N JSON objects as a stream
        response = client.get(
            "https://httpbin.org/stream/5",
            protocol=Protocol.SSE,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")

        if response.status_code == 200:
            print("SSE connection established!")

            # Parse response body
            if response.body:
                # httpbin /stream returns JSON lines, not pure SSE format
                # but we can still process the streaming data
                lines = [line.strip() for line in response.body.split('\n') if line.strip()]
                print(f"\nReceived {len(lines)} data chunks")

                # Print first few chunks
                for i, line in enumerate(lines[:3], 1):
                    print(f"  Chunk {i}: {line[:100]}...")

        client.close()

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: SSE functionality may not be fully implemented.")


def example_sse_with_custom_headers():
    """Example: SSE connection with custom headers"""
    print("\n=== SSE with Custom Headers ===")

    try:
        client = CycleTLS()

        # Custom headers for SSE connection
        custom_headers = {
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }

        response = client.get(
            "https://httpbin.org/stream/3",
            protocol=Protocol.SSE,
            headers=custom_headers,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("SSE connection with custom headers successful!")

            if response.body:
                lines = [line.strip() for line in response.body.split('\n') if line.strip()]
                print(f"Received {len(lines)} events")

        client.close()

    except Exception as e:
        print(f"Error: {e}")


def example_sse_format_parsing():
    """Example: Parsing SSE format"""
    print("\n=== SSE Format Parsing ===")

    # Simulate SSE response
    sample_sse = """event: message
id: 1
data: Hello from SSE!

event: update
id: 2
data: Status: Processing
data: Progress: 50%

: This is a comment (keep-alive)

event: complete
id: 3
data: Task completed successfully

"""

    print("Parsing sample SSE data...")
    events = parse_sse_response(sample_sse)

    print(f"\nParsed {len(events)} events:")
    for i, event in enumerate(events, 1):
        print(f"\nEvent {i}:")
        print(f"  Type: {event.get('event', 'message')}")
        print(f"  Data: {event.get('data', 'N/A')}")
        print(f"  ID: {event.get('id', 'N/A')}")
        if 'retry' in event:
            print(f"  Retry: {event['retry']}ms")


def example_sse_with_last_event_id():
    """Example: SSE reconnection with Last-Event-ID"""
    print("\n=== SSE with Last-Event-ID ===")

    try:
        client = CycleTLS()

        # When reconnecting to SSE, send Last-Event-ID header
        # Server should resume from this event
        response = client.get(
            "https://httpbin.org/stream/5",
            protocol=Protocol.SSE,
            headers={
                "Last-Event-ID": "42",
                "Accept": "text/event-stream"
            },
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("SSE reconnection with Last-Event-ID successful!")
            print("Server should resume from event ID 42 (if supported)")

        client.close()

    except Exception as e:
        print(f"Error: {e}")


def example_sse_multiline_data():
    """Example: SSE with multiline data"""
    print("\n=== SSE Multiline Data ===")

    sample_sse = """event: log
id: 100
data: Line 1: Starting process
data: Line 2: Loading configuration
data: Line 3: Connecting to database
data: Line 4: Process complete

"""

    print("Parsing multiline SSE data...")
    events = parse_sse_response(sample_sse)

    if events:
        event = events[0]
        print(f"\nEvent Type: {event.get('event')}")
        print(f"Event ID: {event.get('id')}")
        print(f"Data (multiline):\n{event.get('data')}")


def example_sse_event_types():
    """Example: Different SSE event types"""
    print("\n=== SSE Event Types ===")

    sample_sse = """event: message
data: Default message event

event: userconnect
data: {"user": "john", "timestamp": 1234567890}

event: update
data: System status: OK

event: notification
data: You have 3 new messages

data: This is a message event (no explicit type)

"""

    print("Parsing events with different types...")
    events = parse_sse_response(sample_sse)

    print(f"\nFound {len(events)} events:")
    for event in events:
        event_type = event.get('event', 'message')  # default is 'message'
        data = event.get('data', '')
        print(f"  - {event_type}: {data}")


def example_sse_with_proxy():
    """Example: SSE connection through proxy"""
    print("\n=== SSE Connection Through Proxy ===")

    try:
        client = CycleTLS()

        response = client.get(
            "https://httpbin.org/stream/3",
            protocol=Protocol.SSE,
            proxy="socks5://127.0.0.1:9050",
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            print("SSE connection through proxy successful!")

        client.close()

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: This requires a SOCKS5 proxy on 127.0.0.1:9050")


def example_sse_event_model():
    """Example: Using SSEEvent model"""
    print("\n=== Using SSEEvent Model ===")

    # Create SSE events using the model
    event1 = SSEEvent(
        event="message",
        data="Hello World",
        id="1"
    )

    event2 = SSEEvent(
        event="notification",
        data='{"type": "alert", "message": "Important update"}',
        id="2",
        retry=5000
    )

    print("Created SSE events using SSEEvent model:")
    print(f"\nEvent 1:")
    print(f"  Type: {event1.event}")
    print(f"  Data: {event1.data}")
    print(f"  ID: {event1.id}")

    print(f"\nEvent 2:")
    print(f"  Type: {event2.event}")
    print(f"  Data: {event2.data}")
    print(f"  ID: {event2.id}")
    print(f"  Retry: {event2.retry}ms")


def example_sse_retry_field():
    """Example: SSE retry mechanism"""
    print("\n=== SSE Retry Mechanism ===")

    sample_sse = """retry: 10000
data: Retry timeout set to 10 seconds

event: error
data: Connection lost
retry: 5000

"""

    print("Parsing SSE with retry field...")
    events = parse_sse_response(sample_sse)

    for i, event in enumerate(events, 1):
        print(f"\nEvent {i}:")
        print(f"  Data: {event.get('data')}")
        if 'retry' in event:
            print(f"  Retry after: {event['retry']}ms ({event['retry']/1000}s)")


def example_sse_comments():
    """Example: SSE comments (keep-alive)"""
    print("\n=== SSE Comments (Keep-Alive) ===")

    sample_sse = """: This is a comment - used for keep-alive
: Comments start with a colon
data: Actual data

: Another keep-alive comment
data: More data

"""

    print("SSE comments are used to keep connections alive.")
    print("They start with ':' and are ignored by the parser.")
    print("\nSample SSE with comments:")
    print(sample_sse)


# TODO: These examples show what the API COULD look like
# if full SSE streaming is implemented

def example_sse_streaming_TODO():
    """
    TODO: Example of SSE streaming with real-time callbacks

    This is a placeholder showing what the API might look like
    when full SSE streaming support is implemented.
    """
    print("\n=== TODO: SSE Streaming with Callbacks ===")
    print("This feature may not be implemented yet.")
    print("\nProposed API:")
    print("""
    client = CycleTLS()

    def on_event(event):
        print(f"Received: {event.event} - {event.data}")

    def on_error(error):
        print(f"Error: {error}")

    def on_close():
        print("Connection closed")

    # Stream SSE events with callbacks
    client.sse_stream(
        "https://example.com/events",
        on_event=on_event,
        on_error=on_error,
        on_close=on_close
    )

    client.close()
    """)


def example_sse_event_filtering_TODO():
    """
    TODO: Example of SSE event type filtering

    This is a placeholder showing what the API might look like
    when event filtering is implemented.
    """
    print("\n=== TODO: SSE Event Filtering ===")
    print("This feature may not be implemented yet.")
    print("\nProposed API:")
    print("""
    client = CycleTLS()

    # Only listen for specific event types
    response = client.sse_listen(
        "https://example.com/events",
        event_types=["notification", "update"],
        timeout=30
    )

    client.close()
    """)


def main():
    """Run all SSE examples"""
    print("=" * 60)
    print("CycleTLS Server-Sent Events (SSE) Examples")
    print("=" * 60)

    # Working examples
    example_sse_connection()
    example_sse_with_custom_headers()
    example_sse_format_parsing()
    example_sse_with_last_event_id()
    example_sse_multiline_data()
    example_sse_event_types()
    example_sse_with_proxy()
    example_sse_event_model()
    example_sse_retry_field()
    example_sse_comments()

    # TODO examples (not implemented yet)
    example_sse_streaming_TODO()
    example_sse_event_filtering_TODO()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("\nKey Points:")
    print("- Use protocol=Protocol.SSE for Server-Sent Events")
    print("- SSE uses text/event-stream content type")
    print("- Events have format: event, id, data, retry fields")
    print("- Empty line marks end of event")
    print("- Comments start with ':' (used for keep-alive)")
    print("- Multiline data supported with multiple data: lines")
    print("\nSSE Format:")
    print("  event: eventType")
    print("  id: eventId")
    print("  data: event data")
    print("  retry: milliseconds")
    print("  ")
    print("  (empty line ends event)")
    print("\nTODO Features:")
    print("- Real-time streaming with callbacks may require additional implementation")
    print("- Event filtering by type")
    print("- Automatic reconnection handling")
    print("- Refer to test_sse.py for current implementation status")
    print("=" * 60)


if __name__ == "__main__":
    main()
