from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from colorControl import set_color, set_mode
from typing import Optional, Dict, Any
import json

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # add Pi URLs later:
    "http://raspberrypi.local",
    "http://raspberrypi.local:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Command(BaseModel):
    action: str
    payload: Optional[Dict[str, Any]] = None 

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/color")
def color(cmd: Command):
    if cmd.action == "set_color" and cmd.payload:
       col = json.dumps(cmd.payload)
       colDict = json.loads(col)
       r, g, b = colDict["r"], colDict["g"], colDict["b"]
       set_color(r, g, b)
       return {"status": "ok", "mode": cmd.action}
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action {cmd.action!r}")

@app.post("/command")
def command(cmd: Command):
    if cmd.action == "set_mode" and cmd.payload:
        mode = cmd.payload.get("mode")
        set_mode(mode)
        return {"status": "ok", "mode": mode}

@app.post("/test")
def test_lights(cmd: Command):
    if cmd.action == "test":
        set_mode("test")
        return {"status": "ok"}


