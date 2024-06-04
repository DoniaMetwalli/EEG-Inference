import asyncio
import threading
import websockets
from ahk import AHK

import numpy as np
ahk = AHK()

def rightClass():
    ahk.run_script("Run https://chatgpt.com/")
    
def leftClass():
    ahk.run_script("Run https://scholar.google.com/")
    
def upClass():
    ahk.run_script("Run https://www.google.com/")

def downClass():
    ahk.run_script("Run https://www.youtube.com/")

def selectClass():
    ahk.run_script("Run https://github.com/")
    

async def recvThread(websocket: websockets.WebSocketClientProtocol):
    while True:
        classification = await websocket.recv()
        yield classification

async def sendThread(websocket: websockets.WebSocketClientProtocol):
    while True:
        await websocket.send("Hello")
        await asyncio.sleep(0.1)


async def all():
    async with websockets.connect("ws://localhost:8090/ws") as websocket:


        sending_task = asyncio.create_task(sendThread(websocket))

        async for classification in recvThread(websocket):
            ## check classification spelling (case sensitive)
            if (classification == "Right"): 
                rightClass()
            elif (classification == "Left"):
                leftClass()
            elif (classification == "Up"):
                upClass()
            elif (classification == "Down"):
                downClass()
            elif classification == "Select":
                selectClass()
            else:
                print(classification)
                print("Invalid Classification")
        await sending_task


    
asyncio.run(all())

