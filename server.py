
import threading
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketState
import numpy as np
import asyncio
from Inference import load_models, Inference
from dataclasses import dataclass
from PythonWrapper import Unicorn
from queue import Queue, Empty

@dataclass(slots=True)
class SharedList:
    sl:list

app = FastAPI()



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
        self.OutputQueue: Queue[np.ndarray] = Queue()

    def RecordContinuously(self):
        if self.config.HeadsetConfig is None:
            raise Exception("Headset Config Not Set")
    
        self.Unicorn.StartAcquisition(self.HandleVal, False)
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
                print("FNOIFNIOEFN")
                if OpenDeviceOut[2] != Unicorn.UnicornReturnStatus.Success:
                    raise Exception("Device Not Found")
                print("DWNFNIWOFf")
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
def headsetSignals():
    hc = UnicornConfig()
    signal = UnicornHeadset(hc)
    signal.Config()
    print("CONFIG")
    return signal



async def receiveThread(clientSocket:WebSocket, inputQueue:SharedList):
    try:
        while clientSocket.client_state == WebSocketState.CONNECTED:
            # inputQueue.sl.append(np.frombuffer(await clientSocket.receive_bytes(),dtype=np.float32).reshape(1,8,1))
            await asyncio.sleep(0.010)
            await clientSocket.receive_text()
    except Exception as e:
        print(e)
        try:
            await clientSocket.close()
        except Exception:
            pass

async def inferenceThread(clientSocket:WebSocket,inputQueue:SharedList, HeadsetQueue:Queue[np.ndarray], batchSize: int = 1200):
    loaded_xgb, scaler, label_encoder, loaded_autoencoder = load_models()
    try:

        while clientSocket.client_state == WebSocketState.CONNECTED:
            
            try:
                signal = HeadsetQueue.get_nowait()
                print(signal.shape)
                inputQueue.sl.append(signal[:8].reshape(1,8,1))
                print(inputQueue.sl[-1].shape)
            except Empty:
                await asyncio.sleep(0.001)

            if len(inputQueue.sl) >= batchSize:
                batch = np.concatenate(inputQueue.sl[:batchSize],axis=2)
                inputQueue.sl=inputQueue.sl[batchSize:]
                yield Inference(batch, loaded_xgb, scaler, label_encoder, loaded_autoencoder)[0]
            else:
                await asyncio.sleep(0.010)
    except Exception as e:
        print(e)



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    inputQueue = SharedList(sl=[])
    headset = headsetSignals()
    recordThread = threading.Thread(target=headset.RecordContinuously)
    recordThread.start()
    recvTask = asyncio.create_task(receiveThread(websocket,inputQueue))
    async for out in inferenceThread(websocket,inputQueue, headset.OutputQueue):
        await websocket.send_text(out)
    await recvTask
