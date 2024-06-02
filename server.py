
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketState
import numpy as np
import asyncio
from Inference import load_models, Inference
from dataclasses import dataclass

@dataclass(slots=True)
class SharedList:
    sl:list

app = FastAPI()



async def receiveThread(clientSocket:WebSocket, inputQueue:SharedList):
    try:
        while clientSocket.client_state == WebSocketState.CONNECTED:
            inputQueue.sl.append(np.frombuffer(await clientSocket.receive_bytes(),dtype=np.float32).reshape(1,8,1))
    except Exception as e:
        print(e)
        try:
            await clientSocket.close()
        except Exception:
            pass

async def inferenceThread(clientSocket:WebSocket,inputQueue:SharedList, batchSize: int = 1200):
    loaded_xgb, scaler, label_encoder, loaded_autoencoder = load_models()
    try:
        while clientSocket.client_state == WebSocketState.CONNECTED:
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
    recvTask = asyncio.create_task(receiveThread(websocket,inputQueue))
    async for out in inferenceThread(websocket,inputQueue):
        await websocket.send_text(out)
    await recvTask
