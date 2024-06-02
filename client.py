# import websockets
# import asyncio
# import numpy as np
# import base64
# import json

# async def pingpong():
#     numbers = np.array([10, 11, 12, 13, 14], dtype=np.int64)
#     numbers_bytes = numbers.tobytes()
#     data = {"shape": numbers.shape, "base_64": base64.b64encode(numbers_bytes).decode(), "datatype": "int64"}
#     as_json = json.dumps(data)
#     print(type(as_json))
    
#     async with websockets.connect("ws://localhost:8090/ws") as websocket:
#         await websocket.send(as_json)
        
#         greeting = await websocket.recv()
#         print(greeting)
        
#         result = await websocket.recv()
#         result = int.from_bytes(result, byteorder='little')
        
#         print(result)
        
#         await websocket.send(str(result))
        
# asyncio.run(pingpong())

import asyncio
import aiofiles
import websockets
from fastapi import WebSocket



async def reading(websocket: WebSocket):
        async with aiofiles.open('Session7.csv', mode='r') as f:
            async for line in f:
                await websocket.send(line)
                
async def sending(websocket: WebSocket):
    while True:
        greeting = await websocket.recv()
        print(greeting)
        
async def both():
    async with websockets.connect("ws://localhost:8090/ws") as websocket:

        queue = asyncio.Queue()

        sending_task = asyncio.create_task(sending(websocket))
        reading_task = asyncio.create_task(reading(websocket))
        
        await queue.put(sending_task)
        await queue.put(reading_task)
        
        sendingQ = await queue.get()
        await sendingQ
        queue.task_done()
        
        readingQ = await queue.get()
        await readingQ
        queue.task_done()
        
        await queue.join()
    
asyncio.run(both())

