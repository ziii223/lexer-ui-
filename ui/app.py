"""magi-C Lexical Analyzer -- single-file Flask web app.

Run with:   python ui/app.py        ->  http://localhost:5000

Strictly lexical: the server hands raw source to ``Lexer(source).tokenize()``
and serialises the resulting tokens.  No parsing, grammar checks, ASTs or
execution logic exist anywhere in this file.

Routes
------
GET  /           the single-page UI (``PAGE``, below)
POST /tokenize   {"code": <source>}  ->  {"ok", "tokens", "error"}

All HTML / CSS / JS is inlined through ``render_template_string`` -- there are
no ``templates/`` or ``static/`` directories to deploy.
"""

from __future__ import annotations

import os
import sys

from flask import Flask, jsonify, render_template_string, request

# --- make ``Lexer.py`` (one level up) importable, however we are launched --- #
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Lexer import Lexer, LexerError          # noqa: E402  (path set above)

app = Flask(__name__)


# --- Helpers --------------------------------------------------------------- #
def serialize(tokens) -> list[dict]:
    """Token -> plain JSON object (exactly type / value / line / column)."""
    return [
        {"type": t.type, "value": t.value, "line": t.line, "column": t.column}
        for t in tokens
    ]


def inner_message(exc: LexerError) -> str:
    """Return only the diagnostic text, without LexerError's ``[...]`` wrapper.

    LexerError renders itself as "Lexical Error [Line L, Col C: <message>]",
    but the UI re-formats errors as "line #L:C - <message>", so it needs just
    the bare <message>.  Falls back to the raw text if the shape is unexpected.
    """
    raw = str(exc)
    prefix = f"Lexical Error [Line {exc.line}, Col {exc.column}: "
    if raw.startswith(prefix) and raw.endswith("]"):
        return raw[len(prefix):-1]
    return raw


# --- Routes ---------------------------------------------------------------- #
@app.get("/")
def index():
    return render_template_string(PAGE)


@app.post("/tokenize")
def tokenize():
    """Lexically scan raw source; failures are returned as JSON, never raised.

    Request  : {"code": "<source text>"}
    Response : {"ok": bool, "tokens": [...], "error": null | {...}}

    On a LexerError the tokens gathered so far are still returned (so the UI
    can show the partial stream) and ``error`` carries line/column/message.
    """
    payload = request.get_json(silent=True)
    source = (payload or {}).get("code", "")

    if not isinstance(source, str):
        return jsonify({
            "ok": False,
            "tokens": [],
            "error": {
                "message": "'code' must be a string.",
                "line": 0,
                "column": 0,
                "formatted": "Invalid request payload.",
            },
        }), 400

    lexer = Lexer(source)
    try:
        tokens = lexer.tokenize()
    except LexerError as exc:
        # Keep whatever was scanned before the failure -- it helps debugging.
        return jsonify({
            "ok": False,
            "tokens": serialize(lexer.tokens),
            "error": {
                "message": inner_message(exc),
                "line": exc.line,
                "column": exc.column,
                "formatted": str(exc),
            },
        })
    except Exception as exc:                       # defensive: never 500 mid-scan
        return jsonify({
            "ok": False,
            "tokens": serialize(getattr(lexer, "tokens", [])),
            "error": {
                "message": f"{type(exc).__name__}: {exc}",
                "line": 0,
                "column": 0,
                "formatted": f"Backend failure -- {type(exc).__name__}: {exc}",
            },
        })

    return jsonify({"ok": True, "tokens": serialize(tokens), "error": None})


# --- Inline page (light neo-brutalism) ------------------------------------- #
PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>magi-C &middot; Lexical Analyzer</title>
<style>
  :root {
    --parchment: #F4F1EA;
    --panel: #FFFFFF;
    --header: #F7F5EE;
    --ink: #000000;
    --emerald: #0E9F6E;
    --crimson: #D92D4B;
    --violet: #7C3AED;
    --teal: #0E7C8A;
    --muted: #6B6B63;
    --faint: #A9A493;
    --rule: #E7E4DA;
    --shadow: 4px 4px 0 var(--ink);
    --mono: "JetBrains Mono", "Fira Code", "Cascadia Code", Consolas, "Courier New", monospace;
  }

  * { box-sizing: border-box; }

  html, body { height: 100%; margin: 0; }

  body {
    background: var(--parchment);
    color: #141414;
    font-family: var(--mono);
    -webkit-font-smoothing: antialiased;
    /* scale the whole layout up so it fills the screen at 100% browser zoom */
    zoom: 1.08;
    transform-origin: top left;
  }

  .app {
    /* 100vh divided by the zoom factor -> renders exactly one viewport tall */
    height: calc(100vh / 1.08);
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }

  /* ---------------- navigation ---------------- */
  .nav {
    flex: none;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 10px 16px;
    background: var(--panel);
    border: 3px solid var(--ink);
    box-shadow: var(--shadow);
  }

  .brand { display: flex; align-items: baseline; gap: 10px; }
  .mark { font-size: 24px; line-height: 1; color: var(--violet); }
  .name { font-size: 20px; font-weight: 800; letter-spacing: .5px; color: var(--teal); }
  .sub { font-size: 9px; font-weight: 700; letter-spacing: 2px; color: var(--faint); }
  .meta { font-size: 10px; letter-spacing: 1px; color: var(--faint); margin-left: 4px; }

  .tabs { display: flex; gap: 12px; margin-left: auto; }

  .tab {
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
    border: 3px solid var(--ink);
    user-select: none;
  }
  .tab.active { background: #00F0FF; color: var(--ink); box-shadow: var(--shadow); }
  .tab.disabled {
    background: #EDEAE1;
    color: #A9A493;
    border-color: #BDB8A8;
    cursor: not-allowed;
  }

  /* ---------------- workspace ---------------- */
  .workspace {
    flex: 1;
    min-height: 0;
    display: grid;
    grid-template-columns: 42% 58%;
    gap: 16px;
  }

  .pane {
    display: flex;
    flex-direction: column;
    min-width: 0;
    min-height: 0;
    background: var(--panel);
    border: 3px solid var(--ink);
    box-shadow: var(--shadow);
  }

  .pane-header {
    flex: none;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: var(--panel);
    border-bottom: 3px solid var(--ink);
  }
  .pane-header h2 {
    margin: 0;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
    color: var(--teal);
  }
  .pane-tokens .pane-header h2 { color: var(--violet); }

  .actions { display: flex; gap: 10px; margin-left: auto; }

  /* ---------------- buttons ---------------- */
  .btn {
    font-family: inherit;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
    padding: 9px 16px;
    color: var(--ink);
    background: var(--panel);
    border: 3px solid var(--ink);
    box-shadow: var(--shadow);
    cursor: pointer;
    transition: transform .05s ease, box-shadow .05s ease;
  }
  .btn:hover:not(:disabled) { filter: brightness(.95); }
  .btn:active:not(:disabled) { transform: translate(2px, 2px); box-shadow: 2px 2px 0 var(--ink); }
  .btn:disabled { cursor: wait; opacity: .6; }
  .btn.primary { background: #00F0FF; }
  .btn.violet { background: #A855F7; color: #fff; }

  /* ---------------- editor ---------------- */
  .editor { flex: 1; min-height: 0; display: flex; background: var(--panel); }

  .gutter {
    flex: none;
    width: 56px;
    padding: 14px 12px 14px 0;
    text-align: right;
    background: var(--header);
    border-right: 3px solid var(--ink);
    font-size: 14px;
    line-height: 22px;
    color: var(--faint);
    overflow: hidden;
    user-select: none;
  }
  .ln { display: block; height: 22px; line-height: 22px; }
  .ln.err { background: var(--crimson); color: #fff; font-weight: 800; }

  #code {
    flex: 1;
    min-width: 0;
    padding: 14px;
    border: 0;
    outline: 0;
    resize: none;
    background: var(--panel);
    color: #141414;
    font-family: inherit;
    font-size: 14px;
    line-height: 22px;
    tab-size: 4;
    white-space: pre;
    overflow: auto;
  }
  #code::selection { background: #00F0FF; color: var(--ink); }

  /* ---------------- token table ---------------- */
  .table-wrap { flex: 1; min-height: 0; overflow: auto; }

  table { width: 100%; border-collapse: collapse; font-size: 13px; }

  thead th {
    position: sticky;
    top: 0;
    z-index: 1;
    padding: 9px 12px;
    text-align: left;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
    color: var(--teal);
    background: var(--header);
    border-bottom: 3px solid var(--ink);
  }

  tbody td { padding: 6px 12px; border-bottom: 1px solid var(--rule); white-space: nowrap; }
  tbody tr.alt { background: #FBFAF6; }
  tbody tr:hover { background: #F0FBFD; }
  td.num { text-align: center; color: var(--muted); }
  td.lex { font-weight: 600; }
  td.type { font-weight: 700; }
  td.empty { padding: 30px 14px; text-align: center; color: var(--faint); }
  .c-no { width: 64px; text-align: center; }
  .c-sm { width: 72px; text-align: center; }

  /* ---------------- console ---------------- */
  .console-pane {
    flex: none;
    height: 184px;
    display: flex;
    flex-direction: column;
    background: var(--panel);
    border: 3px solid var(--ink);
    box-shadow: var(--shadow);
  }

  .console-body {
    flex: 1;
    min-height: 0;
    overflow: auto;
    padding: 10px 14px;
    background: #FBFAF6;
    font-size: 12.5px;
    line-height: 1.75;
  }
  .log { white-space: pre-wrap; }
  .log .pre { margin-right: 8px; font-weight: 800; }
  .log.ok { color: var(--emerald); font-weight: 700; }
  .log.err { color: var(--crimson); font-weight: 700; }
  .log.warn { color: #B45309; }
  .log.info { color: var(--muted); }
  .log.dim { color: var(--faint); }

  .badge {
    margin-left: auto;
    padding: 4px 10px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
    background: #00F0FF;
    color: var(--ink);
    border: 2px solid var(--ink);
  }
  .badge.idle { background: #EDEAE1; color: var(--muted); border-color: #BDB8A8; }
  .badge.work { background: #FFC94D; }
  .badge.ok { background: #39D98A; }
  .badge.error { background: var(--crimson); color: #fff; }

  /* ---------------- responsive ---------------- */
  @media (max-width: 1100px) { .sub, .meta { display: none; } }

  @media (max-width: 900px) {
    .app { height: auto; }
    .workspace { grid-template-columns: 1fr; grid-template-rows: 420px 420px; }
    .nav { flex-wrap: wrap; }
    .tabs { margin-left: 0; }
  }
</style>
</head>
<body>
<div class="app">

  <header class="nav">
    <div class="brand">
      <span class="mark">&#9672;</span>
      <span class="name">magi-C</span>
      <span class="sub">LEXICAL ANALYZER</span>
    </div>
    <nav class="tabs">
      <span class="tab active">LEXICAL</span>
    </nav>
  </header>

  <main class="workspace">

    <section class="pane pane-editor">
      <div class="pane-header">
        <div class="actions">
          <button id="runBtn" class="btn primary" type="button">&#9654; RUN</button>
        </div>
      </div>
      <div class="editor">
        <div class="gutter" id="gutter">1</div>
        <textarea id="code" spellcheck="false" wrap="off"
                  autocomplete="off" autocapitalize="off" autocorrect="off"></textarea>
      </div>
    </section>

    <section class="pane pane-tokens">
      <div class="pane-header">
        <h2>&#9671; LEXICAL TOKEN STREAM</h2>
        <span class="badge" id="tokBadge">0 TOKENS</span>
      </div>
      <div class="table-wrap" id="tableWrap">
        <table>
          <thead>
            <tr>
              <th class="c-no">No.</th>
              <th>Lexeme</th>
              <th>Token Type</th>
              <th class="c-sm">Line</th>
            </tr>
          </thead>
          <tbody id="tokBody"></tbody>
        </table>
      </div>
    </section>

  </main>

  <footer class="console-pane">
    <div class="pane-header">
      <h2>Error Messages:</h2>
      <span class="badge idle" id="statusBadge">IDLE</span>
    </div>
    <div class="console-body" id="consoleEl"></div>
  </footer>

</div>

<script>
(function () {
  "use strict";

  // Must match the line-height:22px used by .gutter and #code in the CSS above,
  // otherwise the gutter numbers drift out of sync with the code as you scroll.
  var LINE_H = 22;

  var codeEl     = document.getElementById("code");
  var gutterEl   = document.getElementById("gutter");
  var tokBody    = document.getElementById("tokBody");
  var tableWrap  = document.getElementById("tableWrap");
  var consoleEl  = document.getElementById("consoleEl");
  var tokBadge   = document.getElementById("tokBadge");
  var statusBadge = document.getElementById("statusBadge");
  var runBtn     = document.getElementById("runBtn");

  var errorLine = 0;   // 1-based source line flagged red in the gutter; 0 = none

  /* ---- lexical token-type colours (by type only, never by grammar) ---- */
  var TYPE_COLORS = {
    KEYWORD: "#7C3AED", IDENTIFIER: "#1F2937", EOF: "#A9A493",
    AURA_LIT: "#0E7C8A", NULL_LIT: "#0E7C8A", AETHER_LIT: "#0E7C8A",
    ESSENCE_LIT: "#0E7C8A", GLYPH_LIT: "#0E7C8A", INSCRIPTION_LIT: "#0E7C8A",
    MATH_OP: "#B45309", REL_OP: "#B45309", LOG_OP: "#B45309", NOT_OP: "#B45309",
    ASSIGN_OP: "#0E9F6E", ADD_ASSIGN: "#0E9F6E", SUB_ASSIGN: "#0E9F6E",
    MUL_ASSIGN: "#0E9F6E", DIV_ASSIGN: "#0E9F6E", MOD_ASSIGN: "#0E9F6E",
    INC_OP: "#0E9F6E", DEC_OP: "#0E9F6E",
    OPEN_PAREN: "#1D4ED8", CLOSE_PAREN: "#1D4ED8", OPEN_CURLY: "#1D4ED8",
    CLOSE_CURLY: "#1D4ED8", OPEN_BRACKET: "#1D4ED8", CLOSE_BRACKET: "#1D4ED8",
    TERMINATOR: "#BE185D", COMMA: "#BE185D", DOT: "#BE185D", DIRECTIVE_HASH: "#BE185D"
  };

  function typeColor(type) { return TYPE_COLORS[type] || "#6B6B63"; }

  /* Escape control characters so every lexeme stays on one table row.
     EOF carries no source text, so its type name stands in for the value. */
  function displayLexeme(tok) {
    if (tok.type === "EOF") { return "EOF"; }
    return String(tok.value)
      .replace(/\\/g, "\\\\")
      .replace(/\n/g, "\\n")
      .replace(/\r/g, "\\r")
      .replace(/\t/g, "\\t");
  }

  /* ------------------------- line-number gutter ------------------------- */
  function updateGutter() {
    var lines = codeEl.value.split("\n").length;
    var html = "";
    for (var i = 1; i <= lines; i++) {
      html += '<span class="ln' + (i === errorLine ? " err" : "") + '">' + i + "</span>";
    }
    gutterEl.innerHTML = html;
    syncScroll();
  }

  function syncScroll() { gutterEl.scrollTop = codeEl.scrollTop; }

  function scrollToLine(line) {
    if (!line || line < 1) { return; }
    codeEl.scrollTop = Math.max(0, (line - 1) * LINE_H - LINE_H * 2);
    syncScroll();
  }

  /* ------------------------------ console ------------------------------- */
  function clearConsole() { consoleEl.innerHTML = ""; }

  function log(kind, text) {
    var row = document.createElement("div");
    row.className = "log " + kind;
    row.textContent = text;
    consoleEl.appendChild(row);
    consoleEl.scrollTop = consoleEl.scrollHeight;
  }

  function setStatus(label, kind) {
    statusBadge.textContent = label;
    statusBadge.className = "badge " + kind;
  }

  /* ---------------------------- token table ----------------------------- */
  /* Cells are filled with textContent, not innerHTML, so lexeme text (which
     may contain markup-like source) is always rendered literally, never parsed. */
  function cell(text, className) {
    var td = document.createElement("td");
    if (className) { td.className = className; }
    td.textContent = text;
    return td;
  }

  function renderTokens(tokens) {
    tokBody.innerHTML = "";

    if (!tokens.length) {
      var emptyRow = document.createElement("tr");
      var emptyCell = cell("No tokens — press RUN to scan the source.", "empty");
      emptyCell.colSpan = 4;
      emptyRow.appendChild(emptyCell);
      tokBody.appendChild(emptyRow);
      tableWrap.scrollTop = 0;
      return;
    }

    var frag = document.createDocumentFragment();
    for (var i = 0; i < tokens.length; i++) {
      var tok = tokens[i];
      var tr = document.createElement("tr");
      if (i % 2) { tr.className = "alt"; }
      tr.appendChild(cell(i + 1, "num"));
      tr.appendChild(cell(displayLexeme(tok), "lex"));
      var typeCell = cell(tok.type, "type");
      typeCell.style.color = typeColor(tok.type);
      tr.appendChild(typeCell);
      tr.appendChild(cell(tok.line, "num"));
      frag.appendChild(tr);
    }
    tokBody.appendChild(frag);
    tableWrap.scrollTop = 0;
  }

  function setTokenBadge(count, isError) {
    tokBadge.textContent = count + (count === 1 ? " TOKEN" : " TOKENS");
    tokBadge.className = "badge" + (isError ? " error" : "");
  }

  /* ------------------------------ results ------------------------------- */
  function handleResult(data) {
    var tokens = data.tokens || [];

    if (data.error) {
      errorLine = data.error.line || 0;
      renderTokens(tokens);
      updateGutter();
      setTokenBadge(tokens.length, true);
      setStatus("ERROR", "error");
      clearConsole();
      // Fixed diagnostic format:  line #<line>:<col> - <message>
      log("err", "line #" + data.error.line + ":" + data.error.column +
                 " - " + data.error.message);
      scrollToLine(errorLine);
      return;
    }

    errorLine = 0;
    renderTokens(tokens);
    updateGutter();
    setTokenBadge(tokens.length, false);
    setStatus("SUCCESS", "ok");
    clearConsole();
    log("ok", "Lexically Successful! 0 Errors. Total Tokens: " + tokens.length);
  }

  /* ------------------------------ actions ------------------------------- */
  function analyze() {
    var source = codeEl.value;

    if (!source.trim()) {
      renderTokens([]);
      errorLine = 0;
      updateGutter();
      setTokenBadge(0, false);
      setStatus("IDLE", "idle");
      clearConsole();
      log("warn", "Nothing to analyze — the source editor is empty.");
      return;
    }

    runBtn.disabled = true;
    runBtn.textContent = "… RUNNING";
    clearConsole();
    setStatus("WORKING", "work");
    log("info", "Scanning " + source.length + " characters…");

    fetch("/tokenize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: source })
    })
      .then(function (response) { return response.json(); })
      .then(handleResult)
      .catch(function (err) {
        clearConsole();
        setStatus("ERROR", "error");
        log("err", "Request failed — " + err);
      })
      .then(function () {
        runBtn.disabled = false;
        runBtn.textContent = "▶ RUN";
      });
  }

  /* ------------------------------ events -------------------------------- */
  codeEl.addEventListener("input", updateGutter);
  codeEl.addEventListener("scroll", syncScroll);
  window.addEventListener("resize", syncScroll);

  codeEl.addEventListener("keydown", function (event) {
    if (event.key === "Tab") {
      event.preventDefault();
      var start = codeEl.selectionStart;
      codeEl.setRangeText("    ", start, codeEl.selectionEnd, "end");
      updateGutter();
    } else if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      analyze();
    }
  });

  runBtn.addEventListener("click", analyze);

  /* ------------------------------- boot --------------------------------- */
  // Start with a blank editor: just lay out the empty gutter and token table.
  updateGutter();
  renderTokens([]);
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print("magi-C lexical analyzer running at  http://localhost:5000")
    print("Press CTRL+C to stop.")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
