import asyncio
from websockets import serve
import json

async def echo(websocket):
    async for message in websocket:

        # message = json.loads(message)
        await websocket.send(json.dumps({"request_id": "localhols", "status_code": 200, "body": message, "headers": {"user-agent": "test"}}))

async def main():
    async with serve(echo, "localhost", 9112):
        await asyncio.Future()  # run forever

asyncio.run(main())
