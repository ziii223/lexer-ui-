"""magi-C Lexical Analyzer -- single-file Flask web app.

Run with:   python ui/app.py        ->  http://localhost:5000
"""

from __future__ import annotations

import os
import re
import sys
import threading

from flask import Flask, jsonify, render_template_string, request, send_from_directory

# --- the ``ui/`` folder itself; the navbar PNGs live beside this file --- #
_UI_DIR = os.path.dirname(os.path.abspath(__file__))

# --- make ``Lexer.py`` (one level up) importable, however we are launched --- #
_PROJECT_ROOT = os.path.dirname(_UI_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Lexer import Lexer, LexerError, Token, tokenize   # noqa: E402  (path set above)

app = Flask(__name__)

# The scanner-only Lexer builds expose ``scan_word`` but no top-level driver, so
# app.py supplies one here (Lexer.py itself stays untouched).  A scan that never
# returns (e.g. a keyword-looking prefix with no valid delimiter) is abandoned
# after this many seconds so the web worker can never hang forever.
SCAN_TIMEOUT_SECONDS = 5.0

# --- Editor starts blank (no preloaded sample program) --- #
SAMPLE_PROGRAM = ""


# --- Helpers --------------------------------------------------------------- #
def serialize(tokens: list[Token]) -> list[dict]:
    """Token -> plain JSON object (exactly type / value / line / column)."""
    return [
        {"type": t.type, "value": t.value, "line": t.line, "column": t.column}
        for t in tokens
    ]


def _run_lexer(lexer: Lexer) -> list[Token]:
    """Drive the backend tokenizer and return every token it produced.

    ``Lexer.py`` defines ``tokenize`` as a *module-level* function taking the
    lexer instance as its argument (``def tokenize(self)``), so it must be
    called as ``tokenize(lexer)`` -- calling ``lexer.tokenize()`` would raise
    ``AttributeError: 'Lexer' object has no attribute 'tokenize'``.

    Tokens accumulate on ``lexer.tokens`` as they are emitted, so a mid-scan
    ``LexerError`` still leaves the partial stream on the instance for the
    caller to serialize.
    """
    return tokenize(lexer)


def _scan_into(lexer: Lexer, result: dict) -> None:
    """Thread body: run the scan and stash either tokens or the exception."""
    try:
        result["tokens"] = _run_lexer(lexer)
    except Exception as exc:                     # noqa: BLE001 (re-raised via JSON)
        result["error"] = exc


def error_line(exc: Exception) -> int:
    """Line of a LexerError, tolerant of builds that omit/rename the field."""
    return int(getattr(exc, "line", 0) or 0)


def error_column(exc: Exception) -> int:
    """Column of a LexerError, accepting either ``.column`` or ``.col``."""
    return int(getattr(exc, "column", getattr(exc, "col", 0)) or 0)


_ERROR_TEXT_RE = re.compile(r"^Lexical Error \[Line \d+, Col \d+: (.*)\]$", re.DOTALL)


def inner_message(exc: LexerError) -> str:
    """Return only the diagnostic text, without LexerError's ``[...]`` wrapper.

    LexerError renders itself as "Lexical Error [Line L, Col C: <message>]",
    but the UI re-formats errors as "line #L:C - <message>", so it needs just
    the bare <message>.  Prefers an explicit ``.message`` when a build stores
    one, then unwraps the rendered form, and finally falls back to raw text.
    """
    message = getattr(exc, "message", None)
    if isinstance(message, str) and message:
        return message
    raw = str(exc)
    match = _ERROR_TEXT_RE.match(raw)
    if match:
        return match.group(1)
    return raw


# --- Routes ---------------------------------------------------------------- #
@app.get("/")
def index():
    return render_template_string(PAGE, sample_program=SAMPLE_PROGRAM)


@app.get("/LOGO TOPLEFT.png")
def serve_logo_topleft():
    """Top-left navbar mark -- route mirrors the on-disk name in ``ui/``."""
    return send_from_directory(_UI_DIR, "LOGO TOPLEFT.png")


@app.get("/MIDDLE.png")
def serve_middle_logo():
    """Centered navbar wordmark -- route mirrors the on-disk name in ``ui/``."""
    return send_from_directory(_UI_DIR, "MIDDLE.png")


@app.post("/tokenize")
def tokenize_endpoint():
    """Lexically scan raw source; failures are returned as JSON, never raised.

    Named ``tokenize_endpoint`` (not ``tokenize``) so the view never shadows the
    module-level ``tokenize`` driver imported from ``Lexer.py``.

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

    # Run the scan on a worker thread so a scanner that never returns (a keyword
    # prefix sitting against an invalid delimiter, say) cannot wedge the request.
    result: dict = {}
    worker = threading.Thread(
        target=_scan_into, args=(lexer, result), daemon=True
    )
    worker.start()
    worker.join(SCAN_TIMEOUT_SECONDS)

    if worker.is_alive():                          # abandoned; report, don't hang
        return jsonify({
            "ok": False,
            "tokens": serialize(list(lexer.tokens)),
            "error": {
                "message": ("Scanning timed out -- the source may contain input "
                            "the scanner cannot advance past."),
                "line": error_line(lexer),
                "column": error_column(lexer),
                "formatted": "Lexical Error: scan timed out.",
            },
        })

    exc = result.get("error")
    if isinstance(exc, LexerError):
        # Keep whatever was scanned before the failure -- it helps debugging.
        return jsonify({
            "ok": False,
            "tokens": serialize(lexer.tokens),
            "error": {
                "message": inner_message(exc),
                "line": error_line(exc),
                "column": error_column(exc),
                "formatted": str(exc),
            },
        })
    if exc is not None:                            # defensive: never 500 mid-scan
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

    return jsonify({
        "ok": True,
        "tokens": serialize(result.get("tokens", lexer.tokens)),
        "error": None,
    })


# --- Inline page (light neo-brutalism) ------------------------------------- #
PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>magi-C &middot; Lexical Analyzer</title>
<style>
  :root {
    --parchment: #F6F3FB;
    --panel: #FFFFFF;
    --header: #F0EAFB;
    --ink: #3E236E;
    --ink-strong: #1E1035;
    --royal: #51308B;
    --nav: #5A398A;
    --gold: #F5D166;
    --emerald: #10B981;
    --emerald-text: #059669;
    --crimson: #DC2626;
    --violet: #8B5CF6;
    --teal: #3E236E;
    --muted: #51308B;
    --faint: #8E7BC0;
    --rule: #E4DCF5;
    --shadow: 4px 4px 0 var(--ink);
    --shadow-strong: 4px 4px 0 var(--ink-strong);
    --mono: "JetBrains Mono", "Fira Code", "Cascadia Code", Consolas, "Courier New", monospace;
  }

  * { box-sizing: border-box; }

  html, body { height: 100%; margin: 0; }

  body {
    background: var(--parchment);
    color: #1E1035;
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
    position: relative;             /* anchors the absolutely-centered middle mark */
    flex: none;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 10px 16px;
    background: var(--nav);
    border: 3px solid var(--ink-strong);
    box-shadow: var(--shadow-strong);
  }

  .brand { display: flex; align-items: center; gap: 10px; }

  /* Both PNGs are >=90% flat #5A398A padding — pixel-identical to the nav fill —
     so at their natural aspect the actual artwork is a tiny speck floating in a
     big empty purple box (which is exactly the "empty navbar" symptom). Crop to
     the artwork band and scale it up: each slot clips its padding via
     overflow:hidden and negative margins centre the oversized img on the art.
       LOGO TOPLEFT.png 682x685 : art x[168..523] y[187..498] = 356x312
       MIDDLE.png       685x204 : art x[157..545] y[ 45..166] = 389x122
     Any overflow is the same purple as the bar, so edges never show a seam. */
  .brand-slot {
    flex: none;
    width: 76px;
    height: 62px;
    overflow: hidden;                 /* clips padding; also stops margin collapse */
  }
  .brand-slot img {
    display: block;
    height: 136.1px;                  /* 62 * 685/312 -> art fills the 62px slot */
    width: auto;                      /* renders 135.5px wide, art 70.7px */
    margin: -37.05px 0 0 -30.6px;     /* centres the 70.7x62 art in the 76x62 slot */
  }

  /* Wordmark slot, dead-centred in the bar. Absolute + symmetric negative
     margins centre it deterministically (no transform, no flex-overflow quirks). */
  .nav-mid-slot {
    position: absolute;
    left: 50%;
    top: 50%;
    margin: -20px 0 0 -68px;          /* exact centre: -(h/2) -(w/2) */
    width: 136px;
    height: 40px;
    overflow: hidden;
    pointer-events: none;
  }
  .nav-mid-slot img {
    display: block;
    height: 66.9px;                   /* 40 * 204/122 -> art fills the 40px slot */
    width: auto;                      /* renders 224.6px wide, art 127.6px */
    margin: -14.6px 0 0 -47.1px;      /* centres the 127.6x40 art in the 136x40 slot */
  }

  .tabs { display: flex; gap: 12px; margin-left: auto; }

  .tab {
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
    color: #FFFFFF;
    border: 3px solid var(--ink-strong);
    user-select: none;
  }
  .tab.active { background: var(--violet); color: var(--ink-strong); box-shadow: var(--shadow-strong); }
  .tab.disabled {
    background: #EDE7F9;
    color: var(--royal);
    border-color: #B9A7E0;
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
    border-bottom: 3px solid var(--royal);
  }
  .pane-header h2 {
    margin: 0;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1px;
    color: var(--teal);
  }

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
  .btn.primary { background: var(--gold); color: #000000; }
  .btn.violet { background: #6D28D9; color: #fff; }

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
    color: #1E1035;
    font-family: inherit;
    font-size: 14px;
    line-height: 22px;
    tab-size: 4;
    white-space: pre;
    overflow: auto;
  }
  #code::selection { background: var(--gold); color: #000000; }

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
    color: #FFFFFF;
    background: var(--violet);
    border-bottom: 3px solid var(--ink);
  }

  tbody td { padding: 6px 12px; border-bottom: 1px solid var(--rule); white-space: nowrap; }
  tbody tr.alt { background: #F4F0FC; }
  tbody tr:hover { background: #EDE7F9; }
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
    background: #F4F0FC;
    font-size: 12.5px;
    line-height: 1.75;
  }
  .log { white-space: pre-wrap; }
  .log .pre { margin-right: 8px; font-weight: 800; }
  .log.ok { color: var(--emerald-text); font-weight: 700; }
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
    background: var(--violet);
    color: var(--ink-strong);
    border: 2px solid var(--ink-strong);
  }
  .badge.idle { background: #EDE7F9; color: var(--royal); border-color: #B9A7E0; }
  .badge.work { background: var(--gold); color: var(--ink-strong); }
  .badge.ok { background: var(--emerald); color: var(--ink-strong); }
  .badge.error { background: var(--crimson); color: #fff; }

  /* ---------------- responsive ---------------- */
  @media (max-width: 900px) {
    .app { height: auto; }
    .workspace { grid-template-columns: 1fr; grid-template-rows: 420px 420px; }
    .nav { flex-wrap: wrap; }
    .tabs { margin-left: 0; }
    .nav-mid-slot { display: none; }   /* would collide with the wrapped row */
  }
</style>
</head>
<body>
<div class="app">

  <header class="nav">
    <div class="brand">
      <div class="brand-slot"><img src="/LOGO%20TOPLEFT.png" alt="Magi-C Logo"></div>
    </div>
    <div class="nav-mid-slot"><img src="/MIDDLE.png" alt="Magi-C Lexical Analyzer"></div>
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

  // Server-rendered initial editor contents (empty by default); Jinja's
  // ``tojson`` escapes it safely into a JS string literal (no manual quoting).
  var SAMPLE = {{ sample_program | tojson }};

  var codeEl     = document.getElementById("code");
  var gutterEl   = document.getElementById("gutter");
  var tokBody    = document.getElementById("tokBody");
  var tableWrap  = document.getElementById("tableWrap");
  var consoleEl  = document.getElementById("consoleEl");
  var statusBadge = document.getElementById("statusBadge");
  var runBtn     = document.getElementById("runBtn");

  var errorLine = 0;   // 1-based source line flagged red in the gutter; 0 = none

  /* ---- lexical token-type colours (by type only, never by grammar) ----
     Reserved words (RW_*) and reserved symbols/operators (RS_*) are matched
     by prefix, so every newly introduced member of those families is coloured
     automatically.  Literals and identifiers carry exact entries, and anything
     unmapped still falls back to a readable default -- no token is unstyled. */
  var TYPE_COLORS = {
    IDENTIFIER:      "#4F46E5",   // indigo       (variables)
    AETHER_LITERAL:  "#2563EB",   // royal blue   (integer literal)
    ESSENCE_LITERAL: "#0284C7",   // sky blue     (float literal)
    LIT_INSCRIPTION: "#D97706",   // warm amber   (string literal)
    COMMENT:         "#8E7BC0",   // muted violet (filtered out upstream)
    EOF:             "#8E7BC0"
  };

  var PREFIX_COLORS = [
    ["RW_", "#7C3AED"],   // reserved words            -> deep lavender
    ["RS_", "#059669"],   // reserved symbols/operators -> emerald green
    ["LIT_", "#D97706"]   // string literals           -> warm gold / amber
  ];

  var DEFAULT_COLOR = "#51308B";   // any unlisted type still renders styled

  function typeColor(type) {
    if (typeof type === "string") {
      if (Object.prototype.hasOwnProperty.call(TYPE_COLORS, type)) {
        return TYPE_COLORS[type];
      }
      for (var i = 0; i < PREFIX_COLORS.length; i++) {
        if (type.indexOf(PREFIX_COLORS[i][0]) === 0) {
          return PREFIX_COLORS[i][1];
        }
      }
    }
    return DEFAULT_COLOR;
  }

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

  /* ------------------------------ results ------------------------------- */
  function handleResult(data) {
    var tokens = data.tokens || [];

    if (data.error) {
      errorLine = data.error.line || 0;
      renderTokens(tokens);
      updateGutter();
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
  codeEl.value = SAMPLE;
  updateGutter();
  renderTokens([]);   // blank editor -> show the empty-state row, don't auto-scan
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print("magi-C lexical analyzer running at  http://localhost:5000")
    print("Press CTRL+C to stop.")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
