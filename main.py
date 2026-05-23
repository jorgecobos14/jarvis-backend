from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import json, os, re

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

client = Groq(api_key=os.environ["GROQ_API_KEY"])

SYSTEM_PROMPT = """Eres Jarvis, un asistente personal de IA avanzado instalado en el dispositivo Android del usuario.
Tienes acceso real al dispositivo. Cuando el usuario te mande una lista de archivos, analízala y responde basándote en ella.
Siempre verificas seguridad antes de ejecutar acciones destructivas.
Respondes en español, sin markdown."""

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
                model="gpt-oss-120b",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversations[device_id][-20:],
                max_tokens=1024
            )
            reply = response.choices[0].message.content
            reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL).strip()
            conversations[device_id].append({"role": "assistant", "content": reply})
            await websocket.send_text(json.dumps({"reply": reply}))
    except WebSocketDisconnect:
        pass

@app.get("/")
def root():
    return {"status": "Jarvis online"}
