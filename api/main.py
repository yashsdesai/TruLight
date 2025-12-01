from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import colorControl
from typing import Optional, Dict, Any

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
    #TODO logic 
    #colorControl.set_color(cmd)
    #return {"received": cmd.action, "payload": cmd.payload}
    return colorControl.set_color(cmd)

@app.get("/test")
def test():
    return {"test": "ok"}

