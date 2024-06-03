import asyncio
import aiofiles
import websockets
from fastapi import WebSocket
from ahk import AHK
from PythonWrapper import Unicorn
from dataclasses import dataclass
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
    

@dataclass
class UnicornConfig:
    """
    Config For Experiment Instance
    RecordLength and BreakLength are in milliseconds
    """
    HeadsetConfig: Unicorn.UnicornAmplifierConfiguration = None
    HeadsetSerial: str = "UN-2021.12.19"



class UnicornHeadset:
    def __init__(self, config: UnicornConfig):
        self.config = config
        self.OutputQueue: asyncio.Queue[list[float]] = asyncio.Queue()

    def RecordContinuously(self, run = None):
        if self.config.HeadsetConfig is None:
            raise Exception("Headset Config Not Set")
        while True :
            getDataOutput = self.Unicorn.GetData(
                self.HandleVal, 1, len(self.config.HeadsetConfig.channels)
            )
            if getDataOutput[1] == Unicorn.UnicornReturnStatus.Success:
                # print("GOT DATA")
                # print(getDataOutput)
                self.OutputQueue.put(np.array(getDataOutput[0], dtype=np.float32))
            else:
                print("Failed to get Data", getDataOutput[1])

    def Config(self):
            self.Unicorn = Unicorn
            try:
                OpenDeviceOut = self.Unicorn.OpenDevice(self.config.HeadsetSerial)
                if OpenDeviceOut[2] != Unicorn.UnicornReturnStatus.Success:
                    raise Exception("Device Not Found")
                self.HandleRef = OpenDeviceOut[0]
                self.HandleVal = OpenDeviceOut[1]

                CurrentConfig = self.Unicorn.GetConfiguration(self.HandleVal)
                print("Current Config: ", CurrentConfig[1])
                if self.config.HeadsetConfig is not None:
                    setConfigOut = self.Unicorn.SetConfiguration(
                        self.HandleVal, self.config.HeadsetConfig
                    )
                    if setConfigOut != Unicorn.UnicornReturnStatus.Success:
                        raise Exception("Failed to set Configuration")
                else:
                    self.config.HeadsetConfig = CurrentConfig[0]
            except Exception as e:
                print(e)

## not done yet, a bit unclear, will do it in uni
async def headsetSignals(websocket: WebSocket):
    signal = UnicornHeadset()
    signal.config()
    return signal.OutputQueue    

async def reading(websocket: WebSocket, queue):
    async with aiofiles.open('Session7.csv', mode='r') as f:
        async for line in f:
            await websocket.send(line)
                
async def sending(websocket: WebSocket):
    while True:
        greeting = await websocket.recv()
        print(greeting)
        
async def all():
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
        
        
        ## will need optimization for sure bas di example 
        classification = await websocket.recv()
        
        ## check classification spelling (case sensitive)
        if (classification == "right"): 
            rightClass()
        elif (classification == "left"):
            leftClass()
        elif (classification == "up"):
            upClass()
        elif (classification == "down"):
            downClass()
        else: ## classification == "select"
            selectClass()

    
asyncio.run(all())

