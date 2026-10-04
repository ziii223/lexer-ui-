# magi-C — Lexical Analysis Web UI

A single-file Flask app that drives the existing `Lexer.py` scanner and renders
the token stream in the browser. It is a **pure lexical viewer**: no parsing,
grammar validation, AST building, or execution logic exists anywhere here.

## Run

From the project root (the folder containing `Lexer.py`):

```bash
python ui/app.py
```

Then open **http://localhost:5000**.

Requires Flask (`pip install flask`). All HTML / CSS / JS is inlined via
`render_template_string` — there are no `templates/` or `static/` directories.

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
