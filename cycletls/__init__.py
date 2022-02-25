import asyncio
import websockets
import json
import asyncio
missing = object()

my_task = asyncio.Event()

        
class CycleTLS():
    def __init__(self):
        start_server = websockets.serve(self.request, '127.0.0.1', 9112)
        self.det = None
        self.request = None
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
        
    

    async def producer(self):
        message = "Hello, World!"
        await asyncio.sleep(1) # sleep for 5 seconds before returning message
        return self.request
    async def resp(self):
        while True:
            if self.message:
                return message
            else:
                await asyncio.sleep(.1)
    async def get(self):
        self.request = "hello"
        print("1")
        await self.wait_until_done()
        print("e")
        return  self.det
    async def wait_until_done(self):
        await my_task.wait()  # await until event would be .set()
        print("Finally, the task is done")

    async def request(self, websocket, path):
        while True:
            message = await self.producer()
            print(message)
            if message is None:
                pass
            else:

                await websocket.send(json.dumps({
                        "requestId": "https://example.com/102938471234", 
                    "options": {
                        "url": "https://example.com",
                        "body": "",
                        "ja3":  "771,4865-4867-4866-49195-49199-52393-52392-49196-49200-49162-49161-49171-49172-51-57-47-53-10,0-23-65281-10-11-35-16-5-51-43-13-45-28-21,29-23-24-25-256-257,0",
                        "userAgent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0"
                    }})
                    )
                name = await websocket.recv()
                self.request = None
                self.det = name
                my_task.set()
                if name:
                    print("sent")
if __name__ == "__main__":
    cycle = CycleTLS()
    print("init")
    response = cycle.get("hi")
