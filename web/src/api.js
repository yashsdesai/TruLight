const DEFAULT_API = `${window.location.protocol}//${window.location.hostname}:8000`;
const BASE_URL = process.env.REACT_APP_TRULIGHT_API_URL || DEFAULT_API;

export async function healthCheck() {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function sendColor(action, payload=null) {
  const res = await fetch(`${BASE_URL}/color`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, payload }),
  });
  if (!res.ok) throw new Error("Command failed");
  return res.json();
}

export async function sendCommand(action, payload=null) {
  const res = await fetch(`${BASE_URL}/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, payload }),
  });
  if (!res.ok) throw new Error("Command failed");
  return res.json();
}

export async function setColor(color) {
  return sendColor("set_color", color); 
}

export async function setMode(mode) {
  return sendCommand("set_mode", { mode });
}