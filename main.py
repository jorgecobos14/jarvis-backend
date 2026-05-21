from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import json, os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = """Eres Jarvis, un asistente personal de IA avanzado. 
Ayudas al usuario con tareas del dispositivo Android, gestión de archivos, 
programación, y conversación natural. Siempre verificas la seguridad antes 
de ejecutar acciones. Respondes en español. Eres conciso e inteligente."""

conversations = {}

@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    await websocket.accept()
    if device_id not in conversations:
        conversations[device_id] = []
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            conversations[device_id].append({"role": "user", "content": msg["text"]})
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversations[device_id][-20:],
                max_tokens=1024
            )
            reply = response.choices[0].message.content
            conversations[device_id].append({"role": "assistant", "content": reply})
            await websocket.send_text(json.dumps({"reply": reply}))
    except WebSocketDisconnect:
        pass

@app.get("/")
def root():
    return {"status": "Jarvis online"}
