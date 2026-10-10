# magi-C — Lexical Analysis Web UI

A single-file Flask app that drives the existing `Lexer.py` scanner and renders
the token stream in the browser. It is a **pure lexical viewer**: no parsing,
grammar validation, AST building, or execution logic exists anywhere here.

## How to Run

1. If you haven't cloned the repo, clone the repo.

```bash
git clone https://github.com/ziii223/lexer-ui-.git
cd lexer-ui-
```
If you already have the repo in your machine, pull the latest repo.
```bash
git pull origin main
```

2. Create a virtual environment and activate it.

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate.

# Linux/macOS
source venv/bin/activate
```

3. Install the library (flask) required to run the app.

```bash
pip install -r requirements.txt
```

4. From the project root, run the app.

```bash
python ui/app.py
```

5. Then open **http://localhost:5000**.

## HTTP API

### `GET /`
Serves the single-page UI.

### `POST /tokenize`
Request body: `{"code": "<raw magi-C source>"}`

Runs `Lexer(code).tokenize()` and always answers with the same envelope:

```json
{ "ok": true, "tokens": [ { "type": "...", "value": "...", "line": 1, "column": 1 } ], "error": null }
```

On a `LexerError`, the HTTP status stays `200` (the request itself succeeded;
the lexical error is data) and the envelope becomes:

```json
{
  "ok": false,
  "tokens": [ /* tokens emitted before the failure */ ],
  "error": { "message": "...", "line": 4, "column": 18,
             "formatted": "Lexical Error [Line 4, Col 18: ...]" }
}
```

A malformed payload (non-string `code`) returns `400` with the same shape.

## Layout

| Region | Contents |
| ------ | -------- |
| Top nav bar | `LEXICAL` (active), `SYNTAX` / `RUN` (disabled headers) |
| Left pane | Source editor with line-number gutter, **LOAD SAMPLE**, **ANALYZE** |
| Right pane | Token table — `No.` \| `Lexeme` \| `Token Type` \| `Line` \| `Col` |
| Bottom pane | Diagnostics console — success / error output |

Design: light neo-brutalism — parchment page, white containers with `3px` solid
black borders and `4px 4px 0` hard shadows, buttons that sink `translate(2px,2px)`
on press, emerald success / crimson error output, monospace throughout.

## Behaviour

* The page tokenises the sample program on load; **ANALYZE** re-scans the editor.
* Success → `Lexically Successful! 0 Errors. Total Tokens: N`.
* A lexical error → the exact `Lexical Error [Line X, Col Y: message]` text, the
  offending gutter line marked crimson, and the tokens emitted before the
  failure retained in the table.
* `EOF` is listed last; token values are escaped so each stays on one row.

Shortcuts: `Ctrl+Enter` analyze · `Tab` inserts four spaces in the editor.

## Isolation

`Lexer.py` is imported read-only and is never modified. `ui/app.py` is the only
file in the project that imports it.
