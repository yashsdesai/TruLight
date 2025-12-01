import React, { useState, useMemo } from "react";
import { RgbColorPicker } from "react-colorful";
import throttle from "lodash.throttle";
import { healthCheck, sendCommand, setColor } from "./api";

function App() {
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [color, setColorState] = useState({ r: 255, g: 255, b: 255 }); 

  const handleHealth = async () => {
    try {
      const data = await healthCheck();
      setStatus(JSON.stringify(data));
    } catch (e) {
      setStatus("error");
    }
  };

  const setColorThrottled = useMemo(
    () => 
      throttle(async (nextColor) => {
        try {
          const res = await setColor(nextColor);
          setResult(res);
        } catch (e) {
          setResult({ error: e.message });
        }
      }, 50),
    []
  );

  const handleCommand = async () => {
    try {
      const data = await sendCommand("example_action", { foo: "bar" });
      setResult(data);
    } catch (e) {
      setResult({ error: `${e} command failed` });
    }
  };

  const handleColorChange = (nextColor) => {
    setColorState(nextColor);
    setColorThrottled(nextColor);
  };

  const rgbString = `rgb(${color.r}, ${color.g}, ${color.b})`;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#0f172a",
        color: "#e5e7eb",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <header
        style={{
          height: 64,
          borderBottom: "1px solid #1f2937",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px",
          background: "rgba(15,23,42,0.9)",
          backdropFilter: "blur(12px)",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: "999px",
              background:
                "conic-gradient(from 180deg, #f97316, #ec4899, #3b82f6, #22c55e, #f97316)",
            }}
          />
          <span style={{ fontSize: 18, fontWeight: 600 }}>TruLight</span>
        </div>
        <nav style={{ display: "flex", gap: 16, fontSize: 14 }}>
          <span style={{ opacity: 0.9 }}>Live Control</span>
          <span style={{ opacity: 0.6 }}>Scenes</span>
          <span style={{ opacity: 0.6 }}>Settings</span>
        </nav>
      </header>

      <main
        style={{
          flex: 1,
          padding: "32px 24px",
          display: "flex",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            width: "100%",
            maxWidth: 960,
            display: "grid",
            gridTemplateColumns: "minmax(0, 2fr) minmax(0, 1.2fr)",
            gap: 24,
          }}
        >
          <section
            style={{
              background: "rgba(15,23,42,0.85)",
              borderRadius: 16,
              border: "1px solid #1f2937",
              padding: 24,
              boxShadow: "0 20px 40px rgba(0,0,0,0.35)",
            }}
          >
            <h2 style={{ margin: 0, marginBottom: 8, fontSize: 18 }}>
              Color Wheel
            </h2>
            <p
              style={{
                margin: 0,
                marginBottom: 24,
                fontSize: 13,
                opacity: 0.7,
              }}
            >
              Drag the picker to stream RGB updates live to the controller.
            </p>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "minmax(0, 1.3fr) minmax(0, 1fr)",
                gap: 24,
                alignItems: "center",
              }}
            >
              <div
                style={{
                  background: "#020617",
                  borderRadius: 16,
                  padding: 16,
                  border: "1px solid #1f2937",
                }}
              >
                <RgbColorPicker color={color} onChange={handleColorChange} />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div>
                  <div
                    style={{
                      fontSize: 12,
                      textTransform: "uppercase",
                      letterSpacing: 0.08,
                      opacity: 0.7,
                      marginBottom: 4,
                    }}
                  >
                    Live Preview
                  </div>
                  <div
                    style={{
                      height: 80,
                      borderRadius: 16,
                      border: "1px solid #1f2937",
                      background: rgbString,
                      boxShadow: "0 10px 25px rgba(0,0,0,0.4)",
                    }}
                  />
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
                    gap: 8,
                  }}
                >
                  <div
                    style={{
                      padding: 10,
                      borderRadius: 12,
                      border: "1px solid #1f2937",
                      background: "#020617",
                    }}
                  >
                    <div style={{ fontSize: 11, opacity: 0.6 }}>R</div>
                    <div style={{ fontSize: 16, fontWeight: 600 }}>
                      {color.r}
                    </div>
                  </div>
                  <div
                    style={{
                      padding: 10,
                      borderRadius: 12,
                      border: "1px solid #1f2937",
                      background: "#020617",
                    }}
                  >
                    <div style={{ fontSize: 11, opacity: 0.6 }}>G</div>
                    <div style={{ fontSize: 16, fontWeight: 600 }}>
                      {color.g}
                    </div>
                  </div>
                  <div
                    style={{
                      padding: 10,
                      borderRadius: 12,
                      border: "1px solid #1f2937",
                      background: "#020617",
                    }}
                  >
                    <div style={{ fontSize: 11, opacity: 0.6 }}>B</div>
                    <div style={{ fontSize: 16, fontWeight: 600 }}>
                      {color.b}
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    fontSize: 12,
                    opacity: 0.7,
                    padding: 10,
                    borderRadius: 12,
                    border: "1px dashed #1f2937",
                    background: "rgba(15,23,42,0.8)",
                    wordBreak: "break-all",
                  }}
                >
                  {rgbString}
                </div>
              </div>
            </div>
          </section>

          <section
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 16,
            }}
          >
            <div
              style={{
                background: "rgba(15,23,42,0.85)",
                borderRadius: 16,
                border: "1px solid #1f2937",
                padding: 20,
                boxShadow: "0 16px 30px rgba(0,0,0,0.35)",
              }}
            >
              <h3 style={{ margin: 0, marginBottom: 8, fontSize: 16 }}>
                System
              </h3>
              <p
                style={{
                  margin: 0,
                  marginBottom: 16,
                  fontSize: 13,
                  opacity: 0.7,
                }}
              >
                Health checks and example commands against the backend.
              </p>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={handleHealth}
                  style={{
                    padding: "8px 14px",
                    borderRadius: 999,
                    border: "1px solid #22c55e",
                    background: "#16a34a",
                    color: "#e5e7eb",
                    fontSize: 13,
                    cursor: "pointer",
                  }}
                >
                  Check Health
                </button>
                <button
                  onClick={handleCommand}
                  style={{
                    padding: "8px 14px",
                    borderRadius: 999,
                    border: "1px solid #1d4ed8",
                    background: "#1d4ed8",
                    color: "#e5e7eb",
                    fontSize: 13,
                    cursor: "pointer",
                  }}
                >
                  Example Command
                </button>
              </div>
              {status && (
                <pre
                  style={{
                    marginTop: 12,
                    fontSize: 12,
                    background: "#020617",
                    borderRadius: 8,
                    padding: 8,
                    border: "1px solid #1f2937",
                  }}
                >
                  {status}
                </pre>
              )}
            </div>

            <div
              style={{
                flex: 1,
                background: "rgba(15,23,42,0.85)",
                borderRadius: 16,
                border: "1px solid #1f2937",
                padding: 20,
                boxShadow: "0 16px 30px rgba(0,0,0,0.35)",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <h3 style={{ margin: 0, marginBottom: 8, fontSize: 16 }}>
                Live Response
              </h3>
              <p
                style={{
                  margin: 0,
                  marginBottom: 16,
                  fontSize: 13,
                  opacity: 0.7,
                }}
              >
                Latest payload returned by the backend.
              </p>
              <div
                style={{
                  flex: 1,
                  overflow: "auto",
                  background: "#020617",
                  borderRadius: 8,
                  border: "1px solid #1f2937",
                  padding: 10,
                  fontSize: 12,
                }}
              >
                {result ? (
                  <pre style={{ margin: 0 }}>
                    {JSON.stringify(result, null, 2)}
                  </pre>
                ) : (
                  <span style={{ opacity: 0.5 }}>No data yet</span>
                )}
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}


export default App;
