# ## bring it all together

# from fastapi import FastAPI, WebSocket
# from ahk import AHK
# import json
# import base64
# import numpy as np

# app = FastAPI()
# ahk = AHK()

# def openGPT():
#     ahk.run_script('Run https://chatgpt.com/') 
    

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         numbers = await websocket.receive_text()
#         await websocket.send_text("Message text was: success")
        
#         as_dict = json.loads(numbers)
#         toByte = base64.b64decode(as_dict["base_64"])
#         byteArray = np.frombuffer(toByte, dtype=as_dict["datatype"]).reshape(as_dict["shape"])
#         resultByte = np.sum(byteArray)
#         resultInt = int(resultByte)
#         resultBytes = resultInt.to_bytes((resultInt.bit_length() + 7) // 8, byteorder="little")
#         await websocket.send_bytes(resultBytes)
        
#         final_result = await websocket.receive_text()
        
#         if (final_result == "60"):
#             print("GO")
#             ahk.add_hotkey('#n', callback=openGPT)
#             ahk.start_hotkeys() 
#             ahk.block_forever()
        
from fastapi import FastAPI, WebSocket
from ahk import AHK
import asyncio

app = FastAPI()
ahk = AHK()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        csvFile = await websocket.receive_text()
        await websocket.send_text("Message text was: success")
        
async def main():
    task = asyncio.create_task(websocket_endpoint())
    
    await task
    print(task.done())  # Will print True
    
    #print(task.result())  # Will print Hello World!

# asyncio.run(main())
        