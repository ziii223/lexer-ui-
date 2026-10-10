import string
from dataclasses import dataclass
from typing import List, Optional

# ========== DELIMITERS & CHARACTER DEFINITIONS ==========

# CHARACTER SETS
LETTERS = set(string.ascii_letters)
NONZERO = set("123456789")
NUMBERS = set("0123456789")
ASCII = set(string.printable)
INSC_ASCII = ASCII - {'"', "\\"}
ESCAPE_CHARS = {"n", "t", "r", "\\", '"'}
UNDERSCORE = {"_"}
ID_CHAR = LETTERS | NUMBERS | UNDERSCORE

# WHITESPACE & PUNCTUATION
WHITESPACE = {" ", "\t"}
NEWLINE = {"\n", "\r"}
TERMINATOR = {";"}
COMMA = {","}
DOT = {"."}

# OPERATORS
MATH_OP = {"+", "-", "*", "/", "%"}
NEG_OP = {"~"}
REL_OP = {"<", ">", "="}
EQUAL_OP = {"="}
AND_OR_OP = {"&", "|"}
NOT_OP = {"!"}

# GROUPINGS & QUOTES
OPEN_PAREN = {"("}
CLOSE_PAREN = {")"}
OPEN_CURLY = {"{"}
CLOSE_CURLY = {"}"}
OPEN_BRACKET = {"["}
CLOSE_BRACKET = {"]"}
OPEN_QUOTE = {'"'}

# GENERAL DELIMITERS
SPACE_DEL = WHITESPACE | NEWLINE
LIT_DEL = (
    WHITESPACE | TERMINATOR | COMMA | CLOSE_PAREN | CLOSE_CURLY | AND_OR_OP | EQUAL_OP
)
PAREN_DEL = WHITESPACE | OPEN_PAREN
CURLY_DEL = WHITESPACE | OPEN_CURLY
TRANSFER_DEL = WHITESPACE | TERMINATOR
CONJURE_DEL = LETTERS | WHITESPACE

# GROUPING DELIMITERS
OPEN_PAREN_DEL = (
    LETTERS | NUMBERS | NEG_OP | NOT_OP | CLOSE_PAREN | OPEN_QUOTE | PAREN_DEL
)
CLOSE_PAREN_DEL = (
    TERMINATOR
    | COMMA
    | MATH_OP
    | REL_OP
    | AND_OR_OP
    | CLOSE_PAREN
    | OPEN_CURLY
    | CLOSE_CURLY
    | CLOSE_BRACKET
    | SPACE_DEL
)
OPEN_CURLY_DEL = (
    LETTERS | NUMBERS | NEG_OP | OPEN_CURLY | CLOSE_CURLY | OPEN_QUOTE | SPACE_DEL
)
CLOSE_CURLY_DEL = LETTERS | TERMINATOR | COMMA | CLOSE_CURLY | SPACE_DEL
OPEN_BRACKET_DEL = LETTERS | NUMBERS | PAREN_DEL
CLOSE_BRACKET_DEL = (
    TERMINATOR
    | COMMA
    | MATH_OP
    | REL_OP
    | EQUAL_OP
    | CLOSE_PAREN
    | CLOSE_CURLY
    | OPEN_BRACKET
    | CLOSE_BRACKET
    | SPACE_DEL
)

# OPERATOR DELIMITERS
MATH_DEL = LETTERS | NUMBERS | NEG_OP | PAREN_DEL
CREMENT_DEL = (
    WHITESPACE | TERMINATOR | COMMA | CLOSE_PAREN | CLOSE_CURLY | CLOSE_BRACKET
)
REL_LOG_DEL = LETTERS | NUMBERS | WHITESPACE | NEG_OP | OPEN_PAREN
NOT_DEL = LETTERS | PAREN_DEL

ASSIGN_DEL = LETTERS | NUMBERS | WHITESPACE | NEG_OP | OPEN_PAREN
BASE_ASSIGN_DEL = OPEN_CURLY | OPEN_QUOTE | ASSIGN_DEL

# PUNCTUATION DELIMITERS
TERMINATOR_DEL = CLOSE_CURLY | SPACE_DEL
COMMA_DEL = (
    LETTERS | NUMBERS | NEG_OP | OPEN_PAREN | OPEN_CURLY | OPEN_QUOTE | SPACE_DEL
)
CLOSE_QUOTE_DEL = (
    WHITESPACE | TERMINATOR | COMMA | CLOSE_PAREN | OPEN_CURLY | CLOSE_CURLY
)

# IDENTIFIER & LITERAL DELIMITERS
ID_DEL = (
    TERMINATOR
    | COMMA
    | DOT
    | MATH_OP
    | REL_OP
    | EQUAL_OP
    | AND_OR_OP
    | NOT_OP
    | OPEN_PAREN
    | CLOSE_PAREN
    | OPEN_CURLY
    | CLOSE_CURLY
    | OPEN_BRACKET
    | CLOSE_BRACKET
    | SPACE_DEL
)
AETHER_LIT_DEL = (
    TERMINATOR
    | COMMA
    | MATH_OP
    | REL_OP
    | AND_OR_OP
    | NOT_OP
    | CLOSE_PAREN
    | CLOSE_CURLY
    | CLOSE_BRACKET
    | SPACE_DEL
)
ESSENCE_LIT_DEL = (
    TERMINATOR
    | COMMA
    | MATH_OP
    | REL_OP
    | AND_OR_OP
    | NOT_OP
    | CLOSE_PAREN
    | CLOSE_CURLY
    | SPACE_DEL
)
GLYPH_LIT_DEL = TERMINATOR | COMMA | CLOSE_PAREN | OPEN_CURLY | CLOSE_CURLY | SPACE_DEL
INSCRIPTION_LIT_DEL = TERMINATOR | COMMA | CLOSE_PAREN | CLOSE_CURLY | SPACE_DEL
AURA_LIT_DEL = (
    TERMINATOR
    | COMMA
    | EQUAL_OP
    | AND_OR_OP
    | NOT_OP
    | CLOSE_PAREN
    | CLOSE_CURLY
    | SPACE_DEL
)

# Characters that can begin a token (used to resynchronize after an error)
TOKEN_START = (
    LETTERS
    | NUMBERS
    | NEG_OP
    | MATH_OP
    | REL_OP
    | AND_OR_OP
    | NOT_OP
    | OPEN_PAREN
    | CLOSE_PAREN
    | OPEN_CURLY
    | CLOSE_CURLY
    | OPEN_BRACKET
    | CLOSE_BRACKET
    | OPEN_QUOTE
    | DOT
    | TERMINATOR
    | COMMA
    | {"#"}
)

# False: an inscription must close on the line it opened (an unterminated one stops at the end of that line).
# True : a newline is allowed inside an inscription (an unterminated one runs to the end of the file).
STRINGS_MAY_SPAN_LINES = False

# ========== TOKEN STRUCTURE & CURSOR NAVIGATION ==========


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

    def __repr__(self):
        return f"Token({self.type:<18}, {repr(self.value):<15}, Line: {self.line:<2}, Col: {self.column:<2})"


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int, skip_number: bool = False):
        super().__init__(f"Lexical Error [Line {line}, Col {column}: {message}]")
        self.message = message
        self.line = line
        self.column = column
        self.skip_number = (
            skip_number  # recovery hint: skip the rest of a malformed number
        )


class Lexer:
    def __init__(self, source_code: str):
        self.source: str = source_code
        self.pos: int = 0
        self.line: int = 1
        self.col: int = 1
        self.tokens: List[Token] = []
        self.errors: List[LexerError] = []

    def current(self) -> Optional[str]:
        """Returns the character under the cursor without consuming it."""
        return self.source[self.pos] if self.pos < len(self.source) else None

    def peek(self) -> Optional[str]:
        """Returns the 1-character lookahead without consuming it."""
        next_pos = self.pos + 1
        return self.source[next_pos] if next_pos < len(self.source) else None

    def advance(self) -> str:
        """Consumes the current character and updates coordinate tracking."""
        ch = self.current()
        if ch is not None:
            self.pos += 1
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            return ch
        return ""

    # ========== RESERVED WORDS SCANNER (KEYWORDS, IDENTIFIERS) ==========
    def scan_word(self) -> Token:
        state = 0
        start_col = self.col
        lexeme = ""

        while True:
            ch = self.current()

            # ROOT STATE 0
            if state == 0:
                if ch == "a":
                    lexeme += self.advance()
                    state = 1
                elif ch == "b":
                    lexeme += self.advance()
                    state = 12
                elif ch == "c":
                    lexeme += self.advance()
                    state = 20
                elif ch == "d":
                    lexeme += self.advance()
                    state = 68
                elif ch == "e":
                    lexeme += self.advance()
                    state = 77
                elif ch == "f":
                    lexeme += self.advance()
                    state = 85
                elif ch == "g":
                    lexeme += self.advance()
                    state = 94
                elif ch == "i":
                    lexeme += self.advance()
                    state = 103
                elif ch == "m":
                    lexeme += self.advance()
                    state = 120
                elif ch == "n":
                    lexeme += self.advance()
                    state = 129
                elif ch == "p":
                    lexeme += self.advance()
                    state = 134
                elif ch == "r":
                    lexeme += self.advance()
                    state = 142
                elif ch == "s":
                    lexeme += self.advance()
                    state = 157
                elif ch == "y":
                    lexeme += self.advance()
                    state = 188
                elif ch in LETTERS:
                    lexeme += self.advance()
                    state = 262
                else:
                    raise LexerError(
                        f"Unexpected character {repr(ch)}", self.line, start_col
                    )

            # AETHER (2-7), AURA (8-11)
            elif state == 1:
                if ch == "e":
                    lexeme += self.advance()
                    state = 2
                elif ch == "u":
                    lexeme += self.advance()
                    state = 8
                else:
                    state = 262

            # aether (2 -> 6)
            elif state == 2:
                if ch == "t":
                    lexeme += self.advance()
                    state = 3
                else:
                    state = 264
            elif state == 3:
                if ch == "h":
                    lexeme += self.advance()
                    state = 4
                else:
                    state = 266
            elif state == 4:
                if ch == "e":
                    lexeme += self.advance()
                    state = 5
                else:
                    state = 268
            elif state == 5:
                if ch == "r":
                    lexeme += self.advance()
                    state = 6
                else:
                    state = 270
            elif state == 6:
                if ch is None or ch in WHITESPACE:
                    state = 7
                    return Token("RW_AETHER", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 272
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # aura (8 -> 10)
            elif state == 8:
                if ch == "r":
                    lexeme += self.advance()
                    state = 9
                else:
                    state = 264
            elif state == 9:
                if ch == "a":
                    lexeme += self.advance()
                    state = 10
                else:
                    state = 266
            elif state == 10:
                if ch is None or ch in WHITESPACE:
                    state = 11
                    return Token("RW_AURA", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 268
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # blessed (12-18)
            elif state == 12:
                if ch == "l":
                    lexeme += self.advance()
                    state = 13
                else:
                    state = 262
            elif state == 13:
                if ch == "e":
                    lexeme += self.advance()
                    state = 14
                else:
                    state = 264
            elif state == 14:
                if ch == "s":
                    lexeme += self.advance()
                    state = 15
                else:
                    state = 266
            elif state == 15:
                if ch == "s":
                    lexeme += self.advance()
                    state = 16
                else:
                    state = 268
            elif state == 16:
                if ch == "e":
                    lexeme += self.advance()
                    state = 17
                else:
                    state = 270
            elif state == 17:
                if ch == "d":
                    lexeme += self.advance()
                    state = 18
                else:
                    state = 272
            elif state == 18:
                if ch is None or ch in LIT_DEL:
                    state = 19
                    return Token("RW_BLESSED", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 274
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # CAST (21-24), CHANT (25-29), CHARGE (30-33), CIRCLE (34-39), CONJURE (40-46), COUNTER (47-52), CROSSROAD (53-61), CURSED (62-67)
            elif state == 20:
                if ch == "a":
                    lexeme += self.advance()
                    state = 21
                elif ch == "h":
                    lexeme += self.advance()
                    state = 25
                elif ch == "i":
                    lexeme += self.advance()
                    state = 34
                elif ch == "o":
                    lexeme += self.advance()
                    state = 40
                elif ch == "r":
                    lexeme += self.advance()
                    state = 53
                elif ch == "u":
                    lexeme += self.advance()
                    state = 62
                else:
                    state = 262

            # cast (21-23)
            elif state == 21:
                if ch == "s":
                    lexeme += self.advance()
                    state = 22
                else:
                    state = 264
            elif state == 22:
                if ch == "t":
                    lexeme += self.advance()
                    state = 23
                else:
                    state = 266
            elif state == 23:
                if ch is None or ch in PAREN_DEL:
                    state = 24
                    return Token("RW_CAST", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 268
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # chant (25-28)
            elif state == 25:
                if ch == "a":
                    lexeme += self.advance()
                    state = 26
                else:
                    state = 264
            elif state == 26:
                if ch == "n":
                    lexeme += self.advance()
                    state = 27
                elif ch == "r":
                    lexeme += self.advance()
                    state = 30
                else:
                    state = 266
            elif state == 27:
                if ch == "t":
                    lexeme += self.advance()
                    state = 28
                else:
                    state = 268
            elif state == 28:
                if ch is None or ch in PAREN_DEL:
                    state = 29
                    return Token("RW_CHANT", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 270
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # charge (30-32)
            elif state == 30:
                if ch == "g":
                    lexeme += self.advance()
                    state = 31
                else:
                    state = 268
            elif state == 31:
                if ch == "e":
                    lexeme += self.advance()
                    state = 32
                else:
                    state = 270
            elif state == 32:
                if ch is None or ch in PAREN_DEL:
                    state = 33
                    return Token("RW_CHARGE", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 272
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # circle (34-38)
            elif state == 34:
                if ch == "r":
                    lexeme += self.advance()
                    state = 35
                else:
                    state = 264
            elif state == 35:
                if ch == "c":
                    lexeme += self.advance()
                    state = 36
                else:
                    state = 266
            elif state == 36:
                if ch == "l":
                    lexeme += self.advance()
                    state = 37
                else:
                    state = 268
            elif state == 37:
                if ch == "e":
                    lexeme += self.advance()
                    state = 38
                else:
                    state = 270
            elif state == 38:
                if ch is None or ch in WHITESPACE:
                    state = 39
                    return Token("RW_CIRCLE", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 272
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # conjure (40-45)
            elif state == 40:
                if ch == "n":
                    lexeme += self.advance()
                    state = 41
                elif ch == "u":
                    lexeme += self.advance()
                    state = 47
                else:
                    state = 264
            elif state == 41:
                if ch == "j":
                    lexeme += self.advance()
                    state = 42
                else:
                    state = 266
            elif state == 42:
                if ch == "u":
                    lexeme += self.advance()
                    state = 43
                else:
                    state = 268
            elif state == 43:
                if ch == "r":
                    lexeme += self.advance()
                    state = 44
                else:
                    state = 270
            elif state == 44:
                if ch == "e":
                    lexeme += self.advance()
                    state = 45
                else:
                    state = 272
            elif state == 45:
                if ch is None or ch in WHITESPACE:
                    state = 46
                    return Token("RW_CONJURE", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 274
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # counter (47-51)
            elif state == 47:
                if ch == "n":
                    lexeme += self.advance()
                    state = 48
                else:
                    state = 266
            elif state == 48:
                if ch == "t":
                    lexeme += self.advance()
                    state = 49
                else:
                    state = 268
            elif state == 49:
                if ch == "e":
                    lexeme += self.advance()
                    state = 50
                else:
                    state = 270
            elif state == 50:
                if ch == "r":
                    lexeme += self.advance()
                    state = 51
                else:
                    state = 272
            elif state == 51:
                if ch is None or ch in CURLY_DEL:
                    state = 52
                    return Token("RW_COUNTER", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 274
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # crossroad (53-60)
            elif state == 53:
                if ch == "o":
                    lexeme += self.advance()
                    state = 54
                else:
                    state = 264
            elif state == 54:
                if ch == "s":
                    lexeme += self.advance()
                    state = 55
                else:
                    state = 266
            elif state == 55:
                if ch == "s":
                    lexeme += self.advance()
                    state = 56
                else:
                    state = 268
            elif state == 56:
                if ch == "r":
                    lexeme += self.advance()
                    state = 57
                else:
                    state = 270
            elif state == 57:
                if ch == "o":
                    lexeme += self.advance()
                    state = 58
                else:
                    state = 272
            elif state == 58:
                if ch == "a":
                    lexeme += self.advance()
                    state = 59
                else:
                    state = 274
            elif state == 59:
                if ch == "d":
                    lexeme += self.advance()
                    state = 60
                else:
                    state = 276
            elif state == 60:
                if ch is None or ch in PAREN_DEL:
                    state = 61
                    return Token("RW_CROSSROAD", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 278
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # cursed (62-66)
            elif state == 62:
                if ch == "r":
                    lexeme += self.advance()
                    state = 63
                else:
                    state = 264
            elif state == 63:
                if ch == "s":
                    lexeme += self.advance()
                    state = 64
                else:
                    state = 266
            elif state == 64:
                if ch == "e":
                    lexeme += self.advance()
                    state = 65
                else:
                    state = 268
            elif state == 65:
                if ch == "d":
                    lexeme += self.advance()
                    state = 66
                else:
                    state = 270
            elif state == 66:
                if ch is None or ch in LIT_DEL:
                    state = 67
                    return Token("RW_CURSED", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 272
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # darkness (68-76)
            elif state == 68:
                if ch == "a":
                    lexeme += self.advance()
                    state = 69
                else:
                    state = 262
            elif state == 69:
                if ch == "r":
                    lexeme += self.advance()
                    state = 70
                else:
                    state = 264
            elif state == 70:
                if ch == "k":
                    lexeme += self.advance()
                    state = 71
                else:
                    state = 266
            elif state == 71:
                if ch == "n":
                    lexeme += self.advance()
                    state = 72
                else:
                    state = 268
            elif state == 72:
                if ch == "e":
                    lexeme += self.advance()
                    state = 73
                else:
                    state = 270
            elif state == 73:
                if ch == "s":
                    lexeme += self.advance()
                    state = 74
                else:
                    state = 272
            elif state == 74:
                if ch == "s":
                    lexeme += self.advance()
                    state = 75
                else:
                    state = 274
            elif state == 75:
                if ch is None or ch in WHITESPACE:
                    state = 76
                    return Token("RW_DARKNESS", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 276
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # essence (77-76)
            elif state == 77:
                if ch == "s":
                    lexeme += self.advance()
                    state = 78
                else:
                    state = 262
            elif state == 78:
                if ch == "s":
                    lexeme += self.advance()
                    state = 79
                else:
                    state = 264
            elif state == 79:
                if ch == "e":
                    lexeme += self.advance()
                    state = 80
                else:
                    state = 266
            elif state == 80:
                if ch == "n":
                    lexeme += self.advance()
                    state = 81
                else:
                    state = 268
            elif state == 81:
                if ch == "c":
                    lexeme += self.advance()
                    state = 82
                else:
                    state = 270
            elif state == 82:
                if ch == "e":
                    lexeme += self.advance()
                    state = 83
                else:
                    state = 272
            elif state == 83:
                if ch is None or ch in WHITESPACE:
                    state = 84
                    return Token("RW_ESSENCE", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 274
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # fallback (85-93)
            elif state == 85:
                if ch == "a":
                    lexeme += self.advance()
                    state = 86
                else:
                    state = 262
            elif state == 86:
                if ch == "l":
                    lexeme += self.advance()
                    state = 87
                else:
                    state = 264
            elif state == 87:
                if ch == "l":
                    lexeme += self.advance()
                    state = 88
                else:
                    state = 266
            elif state == 88:
                if ch == "b":
                    lexeme += self.advance()
                    state = 89
                else:
                    state = 268
            elif state == 89:
                if ch == "a":
                    lexeme += self.advance()
                    state = 90
                else:
                    state = 270
            elif state == 90:
                if ch == "c":
                    lexeme += self.advance()
                    state = 91
                else:
                    state = 272
            elif state == 91:
                if ch == "k":
                    lexeme += self.advance()
                    state = 92
                else:
                    state = 274
            elif state == 92:
                if ch is None or ch in CURLY_DEL:
                    state = 93
                    return Token("RW_FALLBACK", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 276
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # grimoire (94-102)
            elif state == 94:
                if ch == "r":
                    lexeme += self.advance()
                    state = 95
                else:
                    state = 262
            elif state == 95:
                if ch == "i":
                    lexeme += self.advance()
                    state = 96
                else:
                    state = 264
            elif state == 96:
                if ch == "m":
                    lexeme += self.advance()
                    state = 97
                else:
                    state = 266
            elif state == 97:
                if ch == "o":
                    lexeme += self.advance()
                    state = 98
                else:
                    state = 268
            elif state == 98:
                if ch == "i":
                    lexeme += self.advance()
                    state = 99
                else:
                    state = 270
            elif state == 99:
                if ch == "r":
                    lexeme += self.advance()
                    state = 100
                else:
                    state = 272
            elif state == 100:
                if ch == "e":
                    lexeme += self.advance()
                    state = 101
                else:
                    state = 274
            elif state == 101:
                if ch is None or ch in PAREN_DEL:
                    state = 102
                    return Token("RW_GRIMOIRE", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 276
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # INSCRIPTION (103-114), INVOKE (115-119)
            # inscription (103 - 113)
            elif state == 103:
                if ch == "n":
                    lexeme += self.advance()
                    state = 104
                else:
                    state = 262
            elif state == 104:
                if ch == "s":
                    lexeme += self.advance()
                    state = 105
                elif ch == "v":
                    lexeme += self.advance()
                    state = 115
                else:
                    state = 264
            elif state == 105:
                if ch == "c":
                    lexeme += self.advance()
                    state = 106
                else:
                    state = 266
            elif state == 106:
                if ch == "r":
                    lexeme += self.advance()
                    state = 107
                else:
                    state = 268
            elif state == 107:
                if ch == "i":
                    lexeme += self.advance()
                    state = 108
                else:
                    state = 270
            elif state == 108:
                if ch == "p":
                    lexeme += self.advance()
                    state = 109
                else:
                    state = 272
            elif state == 109:
                if ch == "t":
                    lexeme += self.advance()
                    state = 110
                else:
                    state = 274
            elif state == 110:
                if ch == "i":
                    lexeme += self.advance()
                    state = 111
                else:
                    state = 276
            elif state == 111:
                if ch == "o":
                    lexeme += self.advance()
                    state = 112
                else:
                    state = 278
            elif state == 112:
                if ch == "n":
                    lexeme += self.advance()
                    state = 113
                else:
                    state = 280
            elif state == 113:
                if ch is None or ch in WHITESPACE:
                    state = 114
                    return Token("RW_INSCRIPTION", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 282
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # invoke (115-118)
            elif state == 115:
                if ch == "o":
                    lexeme += self.advance()
                    state = 116
                else:
                    state = 266
            elif state == 116:
                if ch == "k":
                    lexeme += self.advance()
                    state = 117
                else:
                    state = 268
            elif state == 117:
                if ch == "e":
                    lexeme += self.advance()
                    state = 118
                else:
                    state = 270
            elif state == 118:
                if ch is None or ch in CURLY_DEL:
                    state = 119
                    return Token("RW_INVOKE", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 272
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # manifest (200-208)
            elif state == 120:
                if ch == "a":
                    lexeme += self.advance()
                    state = 121
                else:
                    state = 262
            elif state == 121:
                if ch == "n":
                    lexeme += self.advance()
                    state = 122
                else:
                    state = 264
            elif state == 122:
                if ch == "i":
                    lexeme += self.advance()
                    state = 123
                else:
                    state = 266
            elif state == 123:
                if ch == "f":
                    lexeme += self.advance()
                    state = 124
                else:
                    state = 268
            elif state == 124:
                if ch == "e":
                    lexeme += self.advance()
                    state = 125
                else:
                    state = 270
            elif state == 125:
                if ch == "s":
                    lexeme += self.advance()
                    state = 126
                else:
                    state = 272
            elif state == 126:
                if ch == "t":
                    lexeme += self.advance()
                    state = 127
                else:
                    state = 274
            elif state == 127:
                if ch is None or ch in PAREN_DEL:
                    state = 128
                    return Token("RW_MANIFEST", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 276
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # null (209-213)
            elif state == 129:
                if ch == "u":
                    lexeme += self.advance()
                    state = 130
                else:
                    state = 262
            elif state == 130:
                if ch == "l":
                    lexeme += self.advance()
                    state = 131
                else:
                    state = 264
            elif state == 131:
                if ch == "l":
                    lexeme += self.advance()
                    state = 132
                else:
                    state = 266
            elif state == 132:
                if ch is None or ch in LIT_DEL:
                    state = 133
                    return Token("RW_NULL", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 268
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # persist (214-221)
            elif state == 134:
                if ch == "e":
                    lexeme += self.advance()
                    state = 135
                else:
                    state = 262
            elif state == 135:
                if ch == "r":
                    lexeme += self.advance()
                    state = 136
                else:
                    state = 264
            elif state == 136:
                if ch == "s":
                    lexeme += self.advance()
                    state = 137
                else:
                    state = 266
            elif state == 137:
                if ch == "i":
                    lexeme += self.advance()
                    state = 138
                else:
                    state = 268
            elif state == 138:
                if ch == "s":
                    lexeme += self.advance()
                    state = 139
                else:
                    state = 270
            elif state == 139:
                if ch == "t":
                    lexeme += self.advance()
                    state = 140
                else:
                    state = 272
            elif state == 140:
                if ch is None or ch in TRANSFER_DEL:
                    state = 141
                    return Token("RW_PERSIST", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 274
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # RUNE (142-146), REMANIFEST (147-156)
            elif state == 142:
                if ch == "u":
                    lexeme += self.advance()
                    state = 143
                elif ch == "e":
                    lexeme += self.advance()
                    state = 147
                else:
                    state = 262

            # rune (142-145)
            elif state == 143:
                if ch == "n":
                    lexeme += self.advance()
                    state = 144
                else:
                    state = 264
            elif state == 144:
                if ch == "e":
                    lexeme += self.advance()
                    state = 145
                else:
                    state = 266
            elif state == 145:
                if ch is None or ch in WHITESPACE:
                    state = 146
                    return Token("RW_RUNE", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 268
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # remanifest (147-155)
            elif state == 147:
                if ch == "m":
                    lexeme += self.advance()
                    state = 148
                else:
                    state = 264
            elif state == 148:
                if ch == "a":
                    lexeme += self.advance()
                    state = 149
                else:
                    state = 266
            elif state == 149:
                if ch == "n":
                    lexeme += self.advance()
                    state = 150
                else:
                    state = 268
            elif state == 150:
                if ch == "i":
                    lexeme += self.advance()
                    state = 151
                else:
                    state = 270
            elif state == 151:
                if ch == "f":
                    lexeme += self.advance()
                    state = 152
                else:
                    state = 272
            elif state == 152:
                if ch == "e":
                    lexeme += self.advance()
                    state = 153
                else:
                    state = 274
            elif state == 153:
                if ch == "s":
                    lexeme += self.advance()
                    state = 154
                else:
                    state = 276
            elif state == 154:
                if ch == "t":
                    lexeme += self.advance()
                    state = 155
                else:
                    state = 278
            elif state == 155:
                if ch is None or ch in PAREN_DEL:
                    state = 156
                    return Token("RW_REMANIFEST", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 280
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # SCROLL (157-163), SEALED (164-169), SHATTER (170-176), SPELL (177-181), SUMMON (182-187)
            elif state == 157:
                if ch == "c":
                    lexeme += self.advance()
                    state = 158
                elif ch == "e":
                    lexeme += self.advance()
                    state = 164
                elif ch == "h":
                    lexeme += self.advance()
                    state = 170
                elif ch == "p":
                    lexeme += self.advance()
                    state = 177
                elif ch == "u":
                    lexeme += self.advance()
                    state = 182
                else:
                    state = 262

            # scroll (158-162)
            elif state == 158:
                if ch == "r":
                    lexeme += self.advance()
                    state = 159
                else:
                    state = 264
            elif state == 159:
                if ch == "o":
                    lexeme += self.advance()
                    state = 160
                else:
                    state = 266
            elif state == 160:
                if ch == "l":
                    lexeme += self.advance()
                    state = 161
                else:
                    state = 268
            elif state == 161:
                if ch == "l":
                    lexeme += self.advance()
                    state = 162
                else:
                    state = 270
            elif state == 162:
                if ch is None or ch in PAREN_DEL:
                    state = 163
                    return Token("RW_SCROLL", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 272
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # sealed (164-168)
            elif state == 164:
                if ch == "a":
                    lexeme += self.advance()
                    state = 165
                else:
                    state = 264
            elif state == 165:
                if ch == "l":
                    lexeme += self.advance()
                    state = 166
                else:
                    state = 266
            elif state == 166:
                if ch == "e":
                    lexeme += self.advance()
                    state = 167
                else:
                    state = 268
            elif state == 167:
                if ch == "d":
                    lexeme += self.advance()
                    state = 168
                else:
                    state = 270
            elif state == 168:
                if ch is None or ch in WHITESPACE:
                    state = 169
                    return Token("RW_SEALED", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 272
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # shatter (170-175)
            elif state == 170:
                if ch == "a":
                    lexeme += self.advance()
                    state = 171
                else:
                    state = 264
            elif state == 171:
                if ch == "t":
                    lexeme += self.advance()
                    state = 172
                else:
                    state = 266
            elif state == 172:
                if ch == "t":
                    lexeme += self.advance()
                    state = 173
                else:
                    state = 268
            elif state == 173:
                if ch == "e":
                    lexeme += self.advance()
                    state = 174
                else:
                    state = 270
            elif state == 174:
                if ch == "r":
                    lexeme += self.advance()
                    state = 175
                else:
                    state = 272
            elif state == 175:
                if ch is None or ch in TRANSFER_DEL:
                    state = 176
                    return Token("RW_SHATTER", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 274
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # spell (177-180)
            elif state == 177:
                if ch == "e":
                    lexeme += self.advance()
                    state = 178
                else:
                    state = 264
            elif state == 178:
                if ch == "l":
                    lexeme += self.advance()
                    state = 179
                else:
                    state = 266
            elif state == 179:
                if ch == "l":
                    lexeme += self.advance()
                    state = 180
                else:
                    state = 268
            elif state == 180:
                if ch is None or ch in WHITESPACE:
                    state = 181
                    return Token("RW_SPELL", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 270
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # summon (182-186)
            elif state == 182:
                if ch == "m":
                    lexeme += self.advance()
                    state = 183
                else:
                    state = 264
            elif state == 183:
                if ch == "m":
                    lexeme += self.advance()
                    state = 184
                else:
                    state = 266
            elif state == 184:
                if ch == "o":
                    lexeme += self.advance()
                    state = 185
                else:
                    state = 268
            elif state == 185:
                if ch == "n":
                    lexeme += self.advance()
                    state = 186
                else:
                    state = 270
            elif state == 186:
                if ch is None or ch in WHITESPACE:
                    state = 187
                    return Token("RW_SUMMON", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 272
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # yield (188-193)
            elif state == 188:
                if ch == "i":
                    lexeme += self.advance()
                    state = 189
                else:
                    state = 262
            elif state == 189:
                if ch == "e":
                    lexeme += self.advance()
                    state = 190
                else:
                    state = 264
            elif state == 190:
                if ch == "l":
                    lexeme += self.advance()
                    state = 191
                else:
                    state = 266
            elif state == 191:
                if ch == "d":
                    lexeme += self.advance()
                    state = 192
                else:
                    state = 268
            elif state == 192:
                if ch is None or ch in TRANSFER_DEL:
                    state = 193
                    return Token("RW_YIELD", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    state = 270
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after keyword '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # IDENTIFIER STATES: 262-298
            elif 262 <= state <= 292 and state % 2 == 0:
                if ch in ID_DEL or ch is None:
                    state = state + 1
                    return Token("IDENTIFIER", lexeme, self.line, start_col)
                elif ch in ID_CHAR:
                    if state == 292:
                        raise LexerError(
                            f"'{lexeme}' has invalid delimiter '{ch}'",
                            self.line,
                            self.col,
                        )
                    lexeme += self.advance()
                    state = state + 2
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after identifier '{lexeme}'",
                        self.line,
                        self.col,
                    )

    # ========== RESERVED SYMBOLS SCANNER ==========
    def scan_symbol(self) -> Token:
        state = 0
        start_col = self.col
        lexeme = ""

        while True:
            ch = self.current()

            if state == 0:
                if ch == "(":
                    lexeme += self.advance()
                    state = 194
                elif ch == ")":
                    lexeme += self.advance()
                    state = 196
                elif ch == "{":
                    lexeme += self.advance()
                    state = 198
                elif ch == "}":
                    lexeme += self.advance()
                    state = 200
                elif ch == "[":
                    lexeme += self.advance()
                    state = 202
                elif ch == "]":
                    lexeme += self.advance()
                    state = 204
                elif ch == "~":
                    lexeme += self.advance()
                    state = 206
                elif ch == "+":
                    lexeme += self.advance()
                    state = 208
                elif ch == "-":
                    lexeme += self.advance()
                    state = 214
                elif ch == "*":
                    lexeme += self.advance()
                    state = 220
                elif ch == "/":
                    lexeme += self.advance()
                    state = 224
                elif ch == "%":
                    lexeme += self.advance()
                    state = 228
                elif ch == ">":
                    lexeme += self.advance()
                    state = 232
                elif ch == "<":
                    lexeme += self.advance()
                    state = 236
                elif ch == "=":
                    lexeme += self.advance()
                    state = 240
                elif ch == "!":
                    lexeme += self.advance()
                    state = 244
                elif ch == "&":
                    lexeme += self.advance()
                    state = 248
                elif ch == "|":
                    lexeme += self.advance()
                    state = 251
                elif ch == ".":
                    lexeme += self.advance()
                    state = 254
                elif ch == ";":
                    lexeme += self.advance()
                    state = 256
                elif ch == ",":
                    lexeme += self.advance()
                    state = 258
                elif ch == "#":
                    lexeme += self.advance()
                    state = 260
                else:
                    raise LexerError(
                        f"Unexpected symbol character {repr(ch)}", self.line, start_col
                    )

            # '(' (194 -> 195*)
            elif state == 194:
                if ch in OPEN_PAREN_DEL:
                    state = 195
                    return Token("RS_OPEN_PARENTHESIS", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '('", self.line, self.col
                )

            # ')' (196 -> 197*)
            elif state == 196:
                if ch is None or ch in CLOSE_PAREN_DEL:
                    state = 197
                    return Token("RS_CLOSE_PARENTHESIS", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after ')'", self.line, self.col
                )

            # '{' (198 -> 199*)
            elif state == 198:
                if ch in OPEN_CURLY_DEL:
                    state = 199
                    return Token("RS_OPEN_CURLY_BRACE", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '{{'", self.line, self.col
                )

            # '}' (200 -> 201*)
            elif state == 200:
                if ch is None or ch in CLOSE_CURLY_DEL:
                    state = 201
                    return Token("RS_CLOSE_CURLY_BRACE", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '}}'", self.line, self.col
                )

            # '[' (202 -> 203*)
            elif state == 202:
                if ch in OPEN_BRACKET_DEL:
                    state = 203
                    return Token("RS_OPEN_BRACKET", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '['", self.line, self.col
                )

            # ']' (204 -> 205*)
            elif state == 204:
                if ch is None or ch in CLOSE_BRACKET_DEL:
                    state = 205
                    return Token("RS_CLOSE_BRACKET", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after ']'", self.line, self.col
                )

            # '~' (206 -> 207*)
            elif state == 206:
                if ch in NUMBERS:
                    state = 207
                    return Token("RS_NEGATIVE", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '~'", self.line, self.col
                )

            # '+' branch (208 -> 213*)
            elif state == 208:
                if ch == "+":
                    lexeme += self.advance()
                    state = 210
                elif ch == "=":
                    lexeme += self.advance()
                    state = 212
                elif ch in MATH_DEL:
                    state = 209
                    return Token("RS_ADD", lexeme, self.line, start_col)
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after '+'", self.line, self.col
                    )

            # '++' (210 -> 211*)
            elif state == 210:
                if ch is None or ch in CREMENT_DEL:
                    state = 211
                    return Token("RS_INCREMENT", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '++'", self.line, self.col
                )

            # '+=' (212 -> 213*)
            elif state == 212:
                if ch in ASSIGN_DEL:
                    state = 213
                    return Token("RS_ADD_ASSIGN", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '+='", self.line, self.col
                )

            # '-' branch (214 -> 219*)
            elif state == 214:
                if ch == "-":
                    lexeme += self.advance()
                    state = 216
                elif ch == "=":
                    lexeme += self.advance()
                    state = 218
                elif ch in MATH_DEL:
                    state = 215
                    return Token("RS_MINUS", lexeme, self.line, start_col)
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after '-'", self.line, self.col
                    )

            # '--' (216 -> 217*)
            elif state == 216:
                if ch is None or ch in CREMENT_DEL:
                    state = 217
                    return Token("RS_DECREMENT", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '--'", self.line, self.col
                )

            # '-=' (218 -> 219*)
            elif state == 218:
                if ch in ASSIGN_DEL:
                    state = 219
                    return Token("RS_SUB_ASSIGN", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '-='", self.line, self.col
                )

            # '*' branch (220 -> 223*)
            elif state == 220:
                if ch == "=":
                    lexeme += self.advance()
                    state = 222
                elif ch in MATH_DEL:
                    state = 221
                    return Token("RS_MULTIPLY", lexeme, self.line, start_col)
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after '*'", self.line, self.col
                    )

            # '*=' (222 -> 223*)
            elif state == 222:
                if ch in ASSIGN_DEL:
                    state = 223
                    return Token("RS_MULTIPLY_ASSIGN", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '*='", self.line, self.col
                )

            # '/' branch (224 -> 227*)
            elif state == 224:
                if ch == "=":
                    lexeme += self.advance()
                    state = 226
                elif ch in MATH_DEL:
                    state = 225
                    return Token("RS_DIVIDE", lexeme, self.line, start_col)
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after '/'", self.line, self.col
                    )

            # '/=' (226 -> 227*)
            elif state == 226:
                if ch in ASSIGN_DEL:
                    state = 227
                    return Token("RS_DIVIDE_ASSIGN", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '/='", self.line, self.col
                )

            # '%' branch (228 -> 231*)
            elif state == 228:
                if ch == "=":
                    lexeme += self.advance()
                    state = 230
                elif ch in MATH_DEL:
                    state = 229
                    return Token("RS_MODULO", lexeme, self.line, start_col)
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after '%'", self.line, self.col
                    )

            # '%=' (230 -> 231*)
            elif state == 230:
                if ch in ASSIGN_DEL:
                    state = 231
                    return Token("RS_MODULO_ASSIGN", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '%='", self.line, self.col
                )

            # '>' branch (232 -> 235*)
            elif state == 232:
                if ch == "=":
                    lexeme += self.advance()
                    state = 234
                elif ch in REL_LOG_DEL:
                    state = 233
                    return Token("RS_GREATER_THAN", lexeme, self.line, start_col)
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after '>'", self.line, self.col
                    )

            # '>=' (234 -> 235*)
            elif state == 234:
                if ch in REL_LOG_DEL:
                    state = 235
                    return Token("RS_GREATER_THAN_EQUAL", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '>='", self.line, self.col
                )

            # '<' branch (236 -> 239*)
            elif state == 236:
                if ch == "=":
                    lexeme += self.advance()
                    state = 238
                elif ch in REL_LOG_DEL:
                    state = 237
                    return Token("RS_LESS_THAN", lexeme, self.line, start_col)
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after '<'", self.line, self.col
                    )

            # '<=' (238 -> 239*)
            elif state == 238:
                if ch in REL_LOG_DEL:
                    state = 239
                    return Token("RS_LESS_THAN_EQUAL", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '<='", self.line, self.col
                )

            # '=' branch (240 -> 243*)
            elif state == 240:
                if ch == "=":
                    lexeme += self.advance()
                    state = 242
                elif ch in BASE_ASSIGN_DEL:
                    state = 241
                    return Token("RS_ASSIGN", lexeme, self.line, start_col)
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after '='", self.line, self.col
                    )

            # '==' (242 -> 243*)
            elif state == 242:
                if ch in REL_LOG_DEL:
                    state = 243
                    return Token("RS_EQUAL", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '=='", self.line, self.col
                )

            # '!' branch (244 -> 247*)
            elif state == 244:
                if ch == "=":
                    lexeme += self.advance()
                    state = 246
                elif ch in NOT_DEL:
                    state = 245
                    return Token("RS_NOT", lexeme, self.line, start_col)
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after '!'", self.line, self.col
                    )

            # '!=' (246 -> 247*)
            elif state == 246:
                if ch in REL_LOG_DEL:
                    state = 247
                    return Token("RS_NOT_EQUAL", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '!='", self.line, self.col
                )

            # '&&' (248 -> 250*)
            elif state == 248:
                if ch == "&":
                    lexeme += self.advance()
                    state = 249
                else:
                    raise LexerError(
                        f"Unexpected character '{ch}' after '&'. Expected '&&'",
                        self.line,
                        self.col,
                    )

            elif state == 249:
                if ch in REL_LOG_DEL:
                    state = 250
                    return Token("RS_AND", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '&&'", self.line, self.col
                )

            # '||' (251 -> 253*)
            elif state == 251:
                if ch == "|":
                    lexeme += self.advance()
                    state = 252
                else:
                    raise LexerError(
                        f"Unexpected character '{ch}' after '|'. Expected '||'",
                        self.line,
                        self.col,
                    )

            elif state == 252:
                if ch in REL_LOG_DEL:
                    state = 253
                    return Token("RS_OR", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '||'", self.line, self.col
                )

            # '.' (254 -> 255*)
            elif state == 254:
                if ch in LETTERS:
                    state = 255
                    return Token("RS_DOT", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '.'", self.line, self.col
                )

            # ';' (256 -> 257*)
            elif state == 256:
                if ch is None or ch in SPACE_DEL:
                    state = 257
                    return Token("RS_TERMINATOR", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after ';'", self.line, self.col
                )

            # ',' (258 -> 259*)
            elif state == 258:
                if ch in COMMA_DEL:
                    state = 259
                    return Token("RS_COMMA", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after ','", self.line, self.col
                )

            # '#' (260 -> 261*)
            elif state == 260:
                if ch in CONJURE_DEL:
                    state = 261
                    return Token("RS_HASH", lexeme, self.line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after '#'", self.line, self.col
                )

    # ========== LITERALS SCANNER ==========
    def scan_number(self) -> Token:
        state = 0
        start_col = self.col
        lexeme = ""

        while True:
            ch = self.current()

            # ROOT STATE 0: '0' -> 294, or optional '~' (or nothing) -> 296
            if state == 0:
                if ch == "0":
                    lexeme += self.advance()
                    state = 294
                elif ch == "~":
                    lexeme += self.advance()
                    state = 296
                elif ch is not None and ch in NONZERO:
                    lexeme += self.advance()
                    state = 298
                else:
                    raise LexerError(
                        f"Unexpected character {repr(ch)} in number",
                        self.line,
                        start_col,
                    )

            # after '~' (296): '0' -> 297, nonzero -> 298
            elif state == 296:
                if ch == "0":
                    lexeme += self.advance()
                    state = 297
                elif ch is not None and ch in NONZERO:
                    lexeme += self.advance()
                    state = 298
                else:
                    raise LexerError(
                        f"Expected a digit after '~' in '{lexeme}'", self.line, self.col
                    )

            # '~0' (297): only valid as the start of a float ('~0.'), never as an aether literal
            elif state == 297:
                if ch == ".":
                    lexeme += self.advance()
                    state = 329
                elif ch is not None and ch in NUMBERS:
                    raise LexerError(
                        f"Leading zeros are not allowed ('{lexeme}{ch}')",
                        self.line,
                        start_col,
                        skip_number=True,
                    )
                else:
                    raise LexerError(
                        f"'{lexeme}' must be followed by '.' (negative zero is not a valid aether literal)",
                        self.line,
                        self.col,
                    )

            # '0' (294 -> 295*) or '0.' (-> 329)
            elif state == 294:
                if ch == ".":
                    lexeme += self.advance()
                    state = 329
                elif ch is None or ch in AETHER_LIT_DEL:
                    state = 295
                    return Token("AETHER_LITERAL", lexeme, self.line, start_col)
                elif ch in NUMBERS:
                    raise LexerError(
                        f"Leading zeros are not allowed ('{lexeme}{ch}')",
                        self.line,
                        start_col,
                        skip_number=True,
                    )
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after aether literal '{lexeme}'",
                        self.line,
                        self.col,
                    )

            elif state == 298 or (299 <= state <= 327 and state % 2 == 1):
                if ch is not None and ch in NUMBERS:
                    if state == 327:
                        raise LexerError(
                            f"'{lexeme}' has invalid delimiter '{ch}'",
                            self.line,
                            self.col,
                        )
                    lexeme += self.advance()
                    state = 299 if state == 298 else state + 2
                elif ch == ".":
                    lexeme += self.advance()
                    state = 329
                elif ch is None or ch in AETHER_LIT_DEL:
                    state = state + 1
                    return Token("AETHER_LITERAL", lexeme, self.line, start_col)
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after aether literal '{lexeme}'",
                        self.line,
                        self.col,
                    )

            # after '.' (329): need at least one fractional digit.
            # Diagram: '0' -> 330* (".0"), otherwise digits (331 ... 352) ending in a nonzero digit.
            elif state == 329:
                if ch is not None and ch in NUMBERS:
                    lexeme += self.advance()
                    frac_len = 1
                    state = 331
                else:
                    raise LexerError(
                        f"Expected a digit after '.' in '{lexeme}'", self.line, self.col
                    )

            # fractional digits (331 -> 352): rows 331, 334, ..., 352 = digit 1..8
            # any digit may be consumed (the 'numbers' edge), the literal may only END on a
            # nonzero digit (the 'nonzero' edge), except the lone ".0" (329 -'0'-> 330*).
            elif state == 331:
                if ch is not None and ch in NUMBERS:
                    if frac_len == 8:
                        raise LexerError(
                            f"'{lexeme}' has invalid delimiter '{ch}'",
                            self.line,
                            self.col,
                        )
                    lexeme += self.advance()
                    frac_len += 1
                elif ch is None or ch in ESSENCE_LIT_DEL:
                    frac = lexeme.split(".")[1]
                    if frac != "0" and frac[-1] == "0":
                        raise LexerError(
                            f"Essence literal '{lexeme}' cannot end in 0",
                            self.line,
                            start_col,
                        )
                    return Token("ESSENCE_LITERAL", lexeme, self.line, start_col)
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after essence literal '{lexeme}'",
                        self.line,
                        self.col,
                    )

    def scan_string(self) -> Optional[Token]:
        state = 0
        start_line = self.line
        start_col = self.col
        lexeme = ""
        bad = False  # an invalid escape/character was found; the string is still read to its end

        while True:
            ch = self.current()

            if state == 0:
                if ch == '"':
                    lexeme += self.advance()
                    state = 349
                else:
                    raise LexerError(
                        f"Unexpected character {repr(ch)} (expected '\"')",
                        self.line,
                        start_col,
                    )

            elif state == 349:
                if ch is None or (ch in NEWLINE and not STRINGS_MAY_SPAN_LINES):
                    raise LexerError(
                        f"Unterminated inscription literal: {lexeme!r}",
                        start_line,
                        start_col,
                    )
                elif ch == '"':
                    lexeme += self.advance()
                    state = 350
                elif ch == "\\":
                    lexeme += self.advance()
                    esc = self.current()
                    if esc is None or (esc in NEWLINE and not STRINGS_MAY_SPAN_LINES):
                        raise LexerError(
                            f"Unterminated inscription literal: {lexeme!r}",
                            start_line,
                            start_col,
                        )
                    if esc not in ESCAPE_CHARS:
                        self.errors.append(
                            LexerError(
                                f"Invalid escape sequence '\\{esc}'",
                                self.line,
                                self.col,
                            )
                        )
                        bad = True
                    lexeme += self.advance()
                elif ch in INSC_ASCII:
                    lexeme += self.advance()
                else:
                    self.errors.append(
                        LexerError(
                            f"Invalid character {repr(ch)} in inscription literal",
                            self.line,
                            self.col,
                        )
                    )
                    bad = True
                    lexeme += self.advance()

            elif state == 350:
                if ch is None or ch in INSCRIPTION_LIT_DEL:
                    state = 351
                    return (
                        None
                        if bad
                        else Token("LIT_INSCRIPTION", lexeme, start_line, start_col)
                    )
                raise LexerError(
                    f"Invalid delimiter '{ch}' after inscription literal",
                    self.line,
                    self.col,
                )

    def scan_comment(self) -> Token:
        state = 0
        start_line = self.line
        start_col = self.col
        lexeme = ""

        while True:
            ch = self.current()

            if state == 0:
                if ch == "#":
                    lexeme += self.advance()
                    state = 352
                else:
                    raise LexerError(
                        f"Unexpected character {repr(ch)} (expected '#/')",
                        self.line,
                        start_col,
                    )

            elif state == 352:
                if ch == "/":
                    lexeme += self.advance()
                    state = 353
                else:
                    raise LexerError(
                        f"Invalid delimiter '{ch}' after '#'", self.line, self.col
                    )

            elif state == 353:
                if ch is None:
                    raise LexerError(
                        f"Unterminated comment: {lexeme!r}", start_line, start_col
                    )
                elif ch == "/":
                    lexeme += self.advance()
                    state = 354
                elif ch in ASCII:
                    lexeme += self.advance()
                else:
                    # report it, but stay inside the comment so the rest isn't tokenized as code
                    self.errors.append(
                        LexerError(
                            f"Invalid character {repr(ch)} in comment",
                            self.line,
                            self.col,
                        )
                    )
                    lexeme += self.advance()

            elif state == 354:
                if ch == "#":
                    lexeme += self.advance()
                    state = 355
                else:
                    state = 353

            elif state == 355:
                if ch is None or ch in SPACE_DEL:
                    state = 356
                    return Token("COMMENT", lexeme, start_line, start_col)
                raise LexerError(
                    f"Invalid delimiter '{ch}' after comment", self.line, self.col
                )

    # ========== TOKENIZER ==========
    def tokenize(self) -> List[Token]:
        """Scans the whole source. Lexical errors are collected in self.errors instead of stopping the scan."""
        while True:
            ch = self.current()
            if ch is None:
                break
            if ch in WHITESPACE or ch in NEWLINE:
                self.advance()
                continue

            start_pos = self.pos
            try:
                if ch in LETTERS:
                    token = self.scan_word()
                elif ch in NUMBERS or (ch == "~" and self.peek() in NUMBERS):
                    token = self.scan_number()
                elif ch in OPEN_QUOTE:
                    token = self.scan_string()
                elif ch == "#" and self.peek() == "/":
                    token = self.scan_comment()
                else:
                    token = self.scan_symbol()
            except LexerError as err:
                self.errors.append(err)
                self.recover(err, start_pos)
                continue

            if token is not None and token.type != "COMMENT":
                self.tokens.append(token)

        return self.tokens

    def recover(self, err: LexerError, start_pos: int) -> None:
        """Moves the cursor to where scanning can safely resume after an error.

        Most errors leave the cursor ON the offending character, so scanning resumes there
        (e.g. 'abcdefghabcdefghij' -> error at 'i', then 'ij' is read as a new identifier).
        """
        if err.skip_number:
            while self.current() is not None and (
                self.current() in NUMBERS or self.current() == "."
            ):
                self.advance()
        ch = self.current()
        # always make progress; and drop an offending character that cannot start any token
        # (it was already reported), so one bad character doesn't produce two errors
        if self.pos == start_pos or (
            ch is not None and ch not in TOKEN_START and ch not in SPACE_DEL
        ):
            self.advance()


def tokenize(lexer: "Lexer") -> List[Token]:
    """Module-level entry point kept for app.py, which calls tokenize(lexer)."""
    return lexer.tokenize()
