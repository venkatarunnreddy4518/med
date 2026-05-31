"""
Medico.AI — FastAPI backend
"""
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.database.db import init_db
from backend.routes.auth import router as auth_router
from backend.routes.upload import router as upload_router
from backend.routes.medicines import router as medicines_router

app = FastAPI(
    title="Medico.AI API",
    description="AI-powered prescription decoder & generic medicine cost optimizer for India",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api/v1", tags=["Upload & OCR"])
app.include_router(medicines_router, prefix="/api/v1", tags=["Medicines"])
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])


def _frontend_html() -> str:
    frontend_file = Path(__file__).resolve().parents[1] / "frontend" / "app.py"
    try:
        source = frontend_file.read_text(encoding="utf-8")
        start_marker = 'html_app = dedent(\n    f"""'
        end_marker = '    """\n)\n\ncomponents.html'
        start = source.index(start_marker) + len(start_marker)
        end = source.index(end_marker, start)
        template = source[start:end]
        template = template.replace("{{", "{").replace("}}", "}")
        template = template.replace('"{API_BASE}"', '"/api/v1"')
        template = template.replace('"{HEALTH_URL}"', '"/health"')
        return template.strip()
    except Exception as exc:
        return f"""
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Medico.AI</title>
          </head>
          <body>
            <main style="font-family:Arial,sans-serif;max-width:720px;margin:64px auto;line-height:1.5">
              <h1>Medico.AI</h1>
              <p>The API is running, but the frontend template could not be loaded.</p>
              <p>Error: {exc}</p>
              <p><a href="/docs">Open API Docs</a></p>
            </main>
          </body>
        </html>
        """


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return _frontend_html()
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Medico.AI</title>
        <style>
          :root {
            --green: #16a34a;
            --blue: #2563eb;
            --ink: #122033;
            --muted: #64748b;
            --line: #d9e2ec;
            --bg: #f6f8fb;
            --card: #ffffff;
          }
          * { box-sizing: border-box; }
          body {
            margin: 0;
            min-height: 100vh;
            font-family: Arial, sans-serif;
            background: var(--bg);
            color: var(--ink);
          }
          header {
            background: #122033;
            color: white;
            padding: 18px 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
          }
          header strong { font-size: 22px; }
          header a { color: white; text-decoration: none; font-weight: 700; }
          main {
            width: min(1120px, calc(100% - 32px));
            margin: 36px auto;
          }
          .hero {
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 24px;
            align-items: stretch;
          }
          .panel {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 28px;
            box-shadow: 0 14px 36px rgba(15, 23, 42, 0.08);
          }
          h1 { margin: 0 0 12px; font-size: clamp(34px, 5vw, 58px); line-height: 1; }
          h2 { margin: 0 0 14px; font-size: 22px; }
          p { color: var(--muted); line-height: 1.55; }
          .actions, form { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 18px; }
          input[type="text"], input[type="file"] {
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: 12px;
            min-height: 44px;
            font: inherit;
            background: white;
          }
          input[type="text"] { flex: 1 1 260px; }
          button, .button {
            border: 0;
            color: white;
            background: var(--green);
            text-decoration: none;
            border-radius: 6px;
            padding: 12px 16px;
            font-weight: 700;
            cursor: pointer;
            min-height: 44px;
          }
          button.secondary, .button.secondary { background: var(--blue); }
          button:disabled { opacity: 0.65; cursor: wait; }
          .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-top: 24px; }
          .stat { border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: white; }
          .stat b { display: block; font-size: 24px; }
          #results { margin-top: 24px; display: grid; gap: 14px; }
          .result { background: white; border: 1px solid var(--line); border-radius: 8px; padding: 18px; }
          .result h3 { margin: 0 0 6px; }
          .tag { display: inline-block; background: #e8f5ee; color: #166534; border-radius: 999px; padding: 4px 9px; font-size: 12px; font-weight: 700; }
          table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }
          th, td { text-align: left; border-bottom: 1px solid var(--line); padding: 10px 8px; vertical-align: top; }
          th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
          .notice { color: var(--muted); background: #eef6ff; border: 1px solid #cfe5ff; border-radius: 8px; padding: 14px; }
          .error { color: #991b1b; background: #fff1f2; border: 1px solid #fecdd3; border-radius: 8px; padding: 14px; }
          @media (max-width: 780px) {
            header { align-items: flex-start; flex-direction: column; }
            .hero, .grid { grid-template-columns: 1fr; }
            main { margin-top: 20px; }
          }
        </style>
      </head>
      <body>
        <header>
          <strong>Medico.AI</strong>
          <nav>
            <a href="/docs">API Docs</a>
          </nav>
        </header>
        <main>
          <section class="hero">
            <div class="panel">
              <h1>Find cheaper medicine alternatives</h1>
              <p>Upload a prescription image or search a medicine name to compare generic options and estimated savings.</p>
              <div class="grid">
                <div class="stat"><b id="status">...</b><span>API status</span></div>
                <div class="stat"><b id="count">...</b><span>Medicines loaded</span></div>
                <div class="stat"><b>FastAPI</b><span>Live backend</span></div>
              </div>
              <div class="actions">
                <a class="button" href="#search">Search Medicine</a>
                <a class="button secondary" href="#upload">Upload Prescription</a>
              </div>
            </div>
            <div class="panel" id="search">
              <h2>Search by medicine name</h2>
              <p>Try examples like Crocin, Dolo 650, Augmentin, Pan 40, or Benadryl Cough.</p>
              <form id="searchForm">
                <input id="medicineName" type="text" placeholder="Enter medicine name" required />
                <button type="submit">Search</button>
              </form>
            </div>
          </section>

          <section class="panel" id="upload" style="margin-top:24px">
            <h2>Upload prescription</h2>
            <p>Choose a JPG, PNG, WebP, BMP, or TIFF prescription image.</p>
            <form id="uploadForm">
              <input id="prescriptionFile" type="file" accept="image/jpeg,image/png,image/webp,image/bmp,image/tiff" required />
              <button type="submit">Analyse Prescription</button>
            </form>
            <p class="notice">For handwriting OCR on Vercel, set GEMINI_API_KEY in your Vercel environment variables.</p>
          </section>

          <section id="results"></section>
        </main>
        <script>
          const apiBase = "/api/v1";
          const results = document.getElementById("results");

          function esc(value) {
            return String(value ?? "").replace(/[&<>"']/g, c => ({
              "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
            }[c]));
          }

          function money(value) {
            return Number(value || 0).toLocaleString("en-IN", {
              style: "currency", currency: "INR", maximumFractionDigits: 2
            });
          }

          function setLoading(message) {
            results.innerHTML = `<div class="notice">${esc(message)}</div>`;
          }

          function setError(message) {
            results.innerHTML = `<div class="error">${esc(message)}</div>`;
          }

          function renderMatch(match) {
            const alternatives = match.alternatives || [];
            const rows = alternatives.length
              ? alternatives.map(a => `
                <tr>
                  <td><b>${esc(a.brand_name)}</b><br><span>${esc(a.manufacturer)}</span></td>
                  <td>${esc(a.generic_name)}<br><span>${esc(a.strength || a.form)}</span></td>
                  <td>${a.price_available === false ? "Unavailable" : money(a.brand_price)}</td>
                  <td>${Number(a.savings_pct || 0).toFixed(1)}%</td>
                </tr>
              `).join("")
              : `<tr><td colspan="4">No alternatives found.</td></tr>`;

            return `
              <article class="result">
                <h3>${esc(match.query || match.matched_brand || "Medicine")}</h3>
                <span class="tag">${esc(match.match_type || "searched")}</span>
                ${match.salt_composition ? `<p>${esc(match.salt_composition)}</p>` : ""}
                ${match.error ? `<p class="error">${esc(match.error)}</p>` : ""}
                <table>
                  <thead><tr><th>Alternative</th><th>Generic</th><th>Price</th><th>Savings</th></tr></thead>
                  <tbody>${rows}</tbody>
                </table>
              </article>
            `;
          }

          function renderUpload(data) {
            const meds = data.extracted_medicines || [];
            const matches = data.results || [];
            results.innerHTML = `
              <div class="result">
                <h3>Prescription analysed</h3>
                <p>OCR engine: ${esc(data.ocr_engine)} | Confidence: ${esc(data.ocr_confidence)}%</p>
                <p><b>Medicines found:</b> ${meds.length ? meds.map(esc).join(", ") : "None"}</p>
              </div>
              ${matches.map(renderMatch).join("")}
            `;
          }

          async function checkHealth() {
            try {
              const res = await fetch("/health", { cache: "no-store" });
              const data = await res.json();
              document.getElementById("status").textContent = data.status || "ok";
              document.getElementById("count").textContent = data.medicines_in_db ?? "0";
            } catch {
              document.getElementById("status").textContent = "offline";
              document.getElementById("count").textContent = "0";
            }
          }

          document.getElementById("searchForm").addEventListener("submit", async event => {
            event.preventDefault();
            const name = document.getElementById("medicineName").value.trim();
            if (!name) return;
            setLoading("Searching alternatives...");
            try {
              const res = await fetch(`${apiBase}/medicines/search?name=${encodeURIComponent(name)}`);
              const data = await res.json();
              if (!res.ok) throw new Error(data.detail || "Search failed");
              results.innerHTML = renderMatch(data);
            } catch (err) {
              setError(err.message || "Cannot search right now.");
            }
          });

          document.getElementById("uploadForm").addEventListener("submit", async event => {
            event.preventDefault();
            const file = document.getElementById("prescriptionFile").files[0];
            if (!file) return;
            setLoading("Uploading and reading prescription...");
            const form = new FormData();
            form.append("file", file);
            form.append("ocr_engine", "auto");
            try {
              const res = await fetch(`${apiBase}/upload`, { method: "POST", body: form });
              const data = await res.json();
              if (!res.ok) throw new Error(data.detail || "Upload failed");
              renderUpload(data);
            } catch (err) {
              setError(err.message || "Cannot upload right now.");
            }
          });

          checkHealth();
        </script>
      </body>
    </html>
    """


@app.on_event("startup")
def startup():
    import threading
    try:
        # Run database initialization in a background thread to prevent blocking Vercel cold-boots
        threading.Thread(target=init_db, daemon=True).start()
        print("[Medico.AI] Database initialization started in the background.")
    except Exception as e:
        print(f"[Medico.AI] ERROR starting background database init: {e}")


@app.get("/health")
def health():
    """Full health check including database status."""
    from backend.database.db import Medicine, SessionLocal

    db = SessionLocal()
    try:
        medicine_count = db.query(Medicine).count()
        return {
            "status": "ok",
            "service": "Medico.AI",
            "database": "connected",
            "medicines_in_db": medicine_count
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "Medico.AI",
            "database": "disconnected",
            "error": str(e)
        }
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
