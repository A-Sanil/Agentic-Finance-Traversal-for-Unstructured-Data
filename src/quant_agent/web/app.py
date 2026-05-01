from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/ui", response_class=HTMLResponse)
def frontend() -> str:
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Agentic Traversal of Unstructured Data</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #08111f;
      --panel: #101c33;
      --panel-2: #0d1729;
      --text: #eef4ff;
      --muted: #9fb0d1;
      --accent: #7dd3fc;
      --accent-2: #a78bfa;
      --border: rgba(125, 211, 252, 0.18);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(167, 139, 250, 0.14), transparent 30%),
        radial-gradient(circle at top right, rgba(125, 211, 252, 0.12), transparent 34%),
        var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 32px;
    }
    .wrap {
      max-width: 1200px;
      margin: 0 auto;
      display: grid;
      gap: 24px;
      grid-template-columns: 420px minmax(0, 1fr);
    }
    .hero, .card {
      background: linear-gradient(180deg, rgba(16, 28, 51, 0.95), rgba(13, 23, 41, 0.98));
      border: 1px solid var(--border);
      border-radius: 20px;
      box-shadow: 0 20px 80px rgba(0, 0, 0, 0.3);
    }
    .hero { padding: 28px; }
    .card { padding: 24px; }
    h1 { margin: 0 0 12px; font-size: 2.1rem; letter-spacing: -0.03em; }
    h2 { margin: 0 0 12px; font-size: 1.1rem; }
    p { color: var(--muted); line-height: 1.6; }
    label { display:block; margin: 14px 0 6px; color: var(--muted); font-size: 0.92rem; }
    input, textarea, button {
      width: 100%;
      border-radius: 14px;
      border: 1px solid rgba(159, 176, 209, 0.2);
      background: rgba(6, 13, 26, 0.75);
      color: var(--text);
      padding: 12px 14px;
      font-size: 0.98rem;
    }
    textarea { min-height: 120px; resize: vertical; }
    button {
      background: linear-gradient(90deg, var(--accent), var(--accent-2));
      color: #07111f;
      font-weight: 700;
      cursor: pointer;
      margin-top: 16px;
    }
    button:hover { filter: brightness(1.03); }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      background: rgba(6, 13, 26, 0.75);
      padding: 20px;
      border-radius: 18px;
      border: 1px solid rgba(159, 176, 209, 0.16);
      overflow: auto;
      min-height: 420px;
    }
    .grid { display: grid; gap: 16px; }
    .small { font-size: 0.9rem; }
    .pill {
      display:inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(125, 211, 252, 0.12);
      border: 1px solid rgba(125, 211, 252, 0.22);
      color: var(--accent);
      font-size: 0.82rem;
      margin-bottom: 12px;
    }
    @media (max-width: 980px) {
      .wrap { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"hero\">
      <div class=\"pill\">Live frontend test</div>
      <h1>Agentic Traversal of Unstructured Data</h1>
      <p>Generate a public-source recommendation digest from SEC filings, web sources, and Twitter context. This UI is meant for research and system testing, not live investment advice.</p>
      <label for=\"tickers\">Tickers</label>
      <input id=\"tickers\" value=\"AAPL,MSFT\" />
      <label for=\"ciks\">CIK map JSON</label>
      <textarea id=\"ciks\">{\"AAPL\": \"320193\", \"MSFT\": \"789019\"}</textarea>
      <label style=\"display:flex; gap:10px; align-items:center; margin-top:14px;\">
        <input id=\"live_sources\" type=\"checkbox\" style=\"width:auto; margin:0;\" />
        Use live SEC/web/Twitter sources
      </label>
      <button id=\"run\">Generate recommendation markdown</button>
      <p class=\"small\" id=\"status\"></p>
    </section>
    <section class=\"card\">
      <h2>Recommendation output</h2>
      <pre id=\"output\">Run the form to generate a markdown digest.</pre>
    </section>
  </div>
  <script>
    const statusEl = document.getElementById('status');
    const outputEl = document.getElementById('output');
    const button = document.getElementById('run');

    button.addEventListener('click', async () => {
      statusEl.textContent = 'Generating...';
      outputEl.textContent = 'Working...';
      const tickers = document.getElementById('tickers').value.split(',').map(s => s.trim()).filter(Boolean);
      let sec_ciks = {};
      try {
        sec_ciks = JSON.parse(document.getElementById('ciks').value || '{}');
      } catch (error) {
        statusEl.textContent = 'CIK JSON is invalid.';
        outputEl.textContent = String(error);
        return;
      }
      const response = await fetch('/recommendations/markdown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tickers, sec_ciks, live_sources: document.getElementById('live_sources').checked })
      });
      const payload = await response.json();
      if (!response.ok) {
        statusEl.textContent = 'Request failed.';
        outputEl.textContent = JSON.stringify(payload, null, 2);
        return;
      }
      statusEl.textContent = 'Done.';
      outputEl.textContent = payload.markdown;
    });
  </script>
</body>
</html>"""
