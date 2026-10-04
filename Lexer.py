import string
from dataclasses import dataclass
from typing import List, Optional

# ========== DELIMITERS & CHARACTER DEFINITIONS ==========

# CHARACTER SETS
LETTERS = set(string.ascii_letters)
NONZERO = set("123456789")
NUMBERS = set("0123456789")
ASCII = set(string.printable)
GLYPH_ASCII = ASCII - {"'", "\n", "\r"}
INSC_ASCII = ASCII - {'"', "\n", "\r"}
ESCAPE_MAP = {'n': '\n', 't': '\t', 'r': '\r', "'": "'", '"': '"', '\\': '\\'}

# WHITESPACE & PUNCTUATION
WHITESPACE = {" ", "\t"}
NEWLINE = {"\n", "\r"}
TERMINATOR = {"~"}
COMMA = {","}
DOT = {"."}

# OPERATORS
MATH_OP = {"+", "-", "*", "/", "%"}
NEG_OP = {"-"}
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
OPEN_QUOTE = {"'", '"'}

# GENERAL DELIMITERS
SPACE_DEL = WHITESPACE | NEWLINE
PAREN_DEL = WHITESPACE | OPEN_PAREN
CURLY_DEL = WHITESPACE | OPEN_CURLY
TRANSFER_DEL = WHITESPACE | TERMINATOR
CONJURE_DEL = LETTERS | WHITESPACE
LIT_DEL = (
    TERMINATOR | COMMA | CLOSE_PAREN | CLOSE_CURLY | AND_OR_OP | EQUAL_OP | SPACE_DEL
)

# GROUPING DELIMITERS
OPEN_PAREN_DEL = (
    LETTERS | NUMBERS | NEG_OP | NOT_OP | CLOSE_PAREN | OPEN_QUOTE | PAREN_DEL
)
CLOSE_PAREN_DEL = (
    WHITESPACE
    | NEWLINE
    | TERMINATOR
    | COMMA
    | MATH_OP
    | REL_OP
    | AND_OR_OP
    | CLOSE_PAREN
    | OPEN_CURLY
    | CLOSE_CURLY
    | CLOSE_BRACKET
)
OPEN_CURLY_DEL = (
    LETTERS
    | NUMBERS
    | WHITESPACE
    | NEWLINE
    | NEG_OP
    | OPEN_CURLY
    | CLOSE_CURLY
    | OPEN_QUOTE
)
CLOSE_CURLY_DEL = LETTERS | WHITESPACE | NEWLINE | TERMINATOR | COMMA | CLOSE_CURLY
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
MINUS_DEL = LETTERS | NUMBERS | PAREN_DEL
MATH_DEL = NEG_OP | MINUS_DEL
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
    WHITESPACE | TERMINATOR | COMMA | CLOSE_PAREN | CLOSE_CURLY | SPACE_DEL
)
CLOSE_SINGLE_QUOTE_DEL = OPEN_CURLY | CLOSE_QUOTE_DEL

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
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Lexical Error [Line {line}, Col {column}: {message}]")
        self.line = line
        self.column = column


class Lexer:
    def __init__(self, source_code: str):
        self.source: str = source_code
        self.pos: int = 0
        self.line: int = 1
        self.col: int = 1
        self.tokens: List[Token] = []

        self.keywords = {
            # PRIMITIVE DATA TYPES
            "aether": WHITESPACE,
            "aura": WHITESPACE,
            "essence": WHITESPACE,
            "glyph": WHITESPACE,
            "inscription": WHITESPACE,
            # LITERALS
            "blessed": LIT_DEL,
            "cursed": LIT_DEL,
            "null": LIT_DEL,
            # TYPE QUALIFIERS & STRUCTURE
            "circle": WHITESPACE,
            "sealed": WHITESPACE,
            "spell": WHITESPACE,
            # INPUT/OUTPUT STATEMENTS
            "cast": PAREN_DEL,
            "scroll": PAREN_DEL,
            # CONDITIONAL STATEMENTS
            "crossroad": PAREN_DEL,
            "counter": CURLY_DEL,
            "fallback": CURLY_DEL,
            "manifest": PAREN_DEL,
            "remanifest": PAREN_DEL,
            "rune": WHITESPACE,
            # LOOPING STATEMENTS
            "chant": PAREN_DEL,
            "charge": PAREN_DEL,
            "invoke": CURLY_DEL,
            # CONTROL TRANSFER
            "persist": TRANSFER_DEL,
            "shatter": TRANSFER_DEL,
            "yield": TRANSFER_DEL,
            # PROGRAM STRUCTURE & DIRECTIVES
            "conjure": WHITESPACE,
            "darkness": WHITESPACE,
            "grimoire": PAREN_DEL,
            "summon": WHITESPACE,
        }

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

    def match(self, expected: str) -> bool:
        """Consumes the current character if it matches expected."""
        if self.current() == expected:
            self.advance()
            return True
        return False

    def verify_delimiter(self, token_name: str, allowed_delims: set):
        """Strict 1-character lookahead delimiter verification."""
        lookahead = self.current()
        if lookahead is None:
            return
        if lookahead not in allowed_delims:
            raise LexerError(
                f"Invalid delimiter '{lookahead}' after {token_name}.",
                self.line,
                self.col,
            )

# ========== WHITESPACE AND COMMENTS TRIMMER ==========
    def skip_whitespace_and_comments(self):
        """Silently consumes spaces, tabs, newlines, and block commments (#/ /#)."""
        while self.current() is not None:
            ch = self.current()
            if ch in SPACE_DEL:
                self.advance()
            elif ch == "#" and self.peek() == "/":
                (
                    start_line,
                    start_col,
                ) = self.line, self.col
                self.advance()
                self.advance()
                closed = False
                while self.current() is not None:
                    if self.current() == "/" and self.peek() == "#":
                        self.advance()
                        self.advance()
                        closed = True
                        break
                    self.advance()
                if not closed:
                    raise LexerError(
                        "Unclosed comment block '#/'", start_line, start_col
                    )
            else:
                break

# ========== WORDS SCANNER (KEYWORDS, AURA LITERAL, NULL, IDENTIFIERS) ==========
    def scan_identifier_or_keyword(self) -> Token:
        start_col = self.col
        word = ""

        while self.current() is not None and (
            self.current() in LETTERS
            or self.current() in NUMBERS
            or self.current() == "_"
        ):
            word += self.advance()

        if word in self.keywords:
            self.verify_delimiter(f"keyword '{word}'", self.keywords[word])
            if word in {"blessed", "cursed"}:
                return Token("AURA_LIT", word, self.line, start_col)
            elif word == "null":
                return Token("NULL_LIT", word, self.line, start_col)
            return Token("KEYWORD", word, self.line, start_col)

        if len(word) > 16:
            raise LexerError(
                f"Identifier '{word}' exceeds maximum length of 16 characters ({len(word)} chars)",
                self.line,
                start_col,
            )
        
        self.verify_delimiter(f"identifier '{word}'", ID_DEL)
        return Token("IDENTIFIER", word, self.line, start_col)

# ========== LITERALS SCANNER (NUMBERS, GLYPHS, INSCRIPTION) ==========
    def scan_number(self) -> Token:
        start_col = self.col
        num_str = ""
        is_essence = False

        while self.current() is not None and self.current() in NUMBERS:
            num_str += self.advance()

        if self.current() == "." and self.peek() in NUMBERS:
            is_essence = True
            num_str += self.advance()
            while self.current() is not None and self.current() in NUMBERS:
                num_str += self.advance()

        if is_essence:
            self.verify_delimiter(f"essence literal '{num_str}'", ESSENCE_LIT_DEL)
            return Token("ESSENCE_LIT", num_str, self.line, start_col)
        else:
            self.verify_delimiter(f"aether literal '{num_str}'", AETHER_LIT_DEL)
            return Token("AETHER_LIT", num_str, self.line, start_col)

    def scan_inscription(self) -> Token:
            start_col = self.col
            self.advance()  # consume opening '"'
            val = ""
    
            while self.current() is not None and self.current() != '"':
                # Disallow raw newline/carriage return inside strings
                if self.current() in {'\n', '\r'}:
                    raise LexerError(
                        "Unclosed inscription literal before newline", self.line, start_col
                    )
    
                # Handle Escape Sequences (\n, \t, \r, \", \', \\)
                if self.current() == "\\":
                    self.advance()  # consume '\'
                    esc = self.current()
    
                    if esc is None:
                        raise LexerError(
                            "Unclosed inscription literal after escape character",
                            self.line,
                            start_col,
                        )
    
                    if esc in ESCAPE_MAP:
                        val += ESCAPE_MAP[esc]
                        self.advance()
                    else:
                        raise LexerError(
                            f"Invalid escape sequence '\\{esc}' in inscription literal",
                            self.line,
                            self.col,
                        )
    
                # Standard ASCII content validation
                else:
                    if self.current() not in INSC_ASCII:
                        raise LexerError(
                            f"Invalid character {repr(self.current())} in inscription literal",
                            self.line,
                            self.col,
                        )
                    val += self.advance()
    
            if self.current() is None:
                raise LexerError(
                    "Unclosed inscription literal at EOF", self.line, start_col
                )
    
            self.advance() 
            self.verify_delimiter("inscription literal", INSCRIPTION_LIT_DEL)
            return Token("INSCRIPTION_LIT", val, self.line, start_col)

    def scan_glyph(self) -> Token:
            start_col = self.col
            self.advance()  # consume opening "'"
            val = ""
    
            while self.current() is not None and self.current() != "'":
                # Disallow raw newline/carriage return inside glyphs
                if self.current() in {'\n', '\r'}:
                    raise LexerError(
                        "Unclosed glyph literal before newline", self.line, start_col
                    )
    
                # Handle Escape Sequences (\n, \t, \r, \', \", \\)
                if self.current() == "\\":
                    self.advance()  # consume '\'
                    esc = self.current()
    
                    if esc is None:
                        raise LexerError(
                            "Unclosed glyph literal after escape character",
                            self.line,
                            start_col,
                        )
    
                    if esc in ESCAPE_MAP:
                        val += ESCAPE_MAP[esc]
                        self.advance()
                    else:
                        raise LexerError(
                            f"Invalid escape sequence '\\{esc}' in glyph literal",
                            self.line,
                            self.col,
                        )
    
                # Standard ASCII content validation
                else:
                    if self.current() not in GLYPH_ASCII:
                        raise LexerError(
                            f"Invalid character {repr(self.current())} in glyph literal",
                            self.line,
                            self.col,
                        )
                    val += self.advance()
    
            if self.current() is None:
                raise LexerError(
                    "Unclosed glyph literal at EOF", self.line, start_col
                )
    
            self.advance()  # consume closing "'"
    
            # Enforce glyph length limit: at most 1 character (allows 0 for '' or 1 for 'a' / '\n')
            if len(val) > 1:
                raise LexerError(
                    f"Glyph literal cannot exceed 1 character (got {len(val)})",
                    self.line,
                    start_col,
                )
    
            self.verify_delimiter("glyph literal", GLYPH_LIT_DEL)
            return Token("GLYPH_LIT", val, self.line, start_col)

# ========== SYMBOLS SCANNING ==========
    def scan_symbol(self) -> Token:
        start_col = self.col
        ch = self.advance()

        # MATH & ASSIGNMENT OPERATORS
        if ch == "+":
            if self.match("+"):
                self.verify_delimiter("operator '++'", CREMENT_DEL)
                return Token("INC_OP", "++", self.line, start_col)
            elif self.match("="):
                self.verify_delimiter("operator '+='", ASSIGN_DEL)
                return Token("ADD_ASSIGN", "+=", self.line, start_col)
            else:
                self.verify_delimiter("operator '+'", MATH_DEL)
                return Token("MATH_OP", "+", self.line, start_col)

        elif ch == "-":
            if self.match("-"):
                self.verify_delimiter("operator '--'", CREMENT_DEL)
                return Token("DEC_OP", "--", self.line, start_col)
            elif self.match("="):
                self.verify_delimiter("operator '-='", ASSIGN_DEL)
                return Token("SUB_ASSIGN", "-=", self.line, start_col)
            else:
                self.verify_delimiter("operator '-'", MINUS_DEL)
                return Token("MATH_OP", "-", self.line, start_col)

        elif ch == "*":
            if self.match("="):
                self.verify_delimiter("*=", ASSIGN_DEL)
                return Token("MUL_ASSIGN", "*=", self.line, start_col)
            else:
                self.verify_delimiter("operator '*'", MATH_DEL)
                return Token("MATH_OP", "*", self.line, start_col)

        elif ch == "/":
            if self.match("="):
                self.verify_delimiter("operator '/='", ASSIGN_DEL)
                return Token("DIV_ASSIGN", "/=", self.line, start_col)
            else:
                self.verify_delimiter("operator '/'", MATH_DEL)
                return Token("MATH_OP", "/", self.line, start_col)

        elif ch == "%":
            if self.match("="):
                self.verify_delimiter("operator '%='", ASSIGN_DEL)
                return Token("MOD_ASSIGN", "%=", self.line, start_col)
            else:
                self.verify_delimiter("operator '%'", MATH_DEL)
                return Token("MATH_OP", "%", self.line, start_col)

        
        # RELATIONAL OPERATORS
        elif ch == "=":
            if self.match("="):
                self.verify_delimiter("operator '='", REL_LOG_DEL)
                return Token("REL_OP", "==", self.line, start_col)
            else:
                self.verify_delimiter("operator '='", BASE_ASSIGN_DEL)
                return Token("ASSIGN_OP", "=",self.line, start_col)
            
        elif ch == "!":
            if self.match("="):
                self.verify_delimiter("operator '!='", REL_LOG_DEL)
                return Token("REL_OP", "!=",self.line, start_col)
            else:
                self.verify_delimiter("operator '!'", NOT_DEL)
                return Token("NOT_OP", "!",self.line, start_col)

        elif ch == "<":
            if self.match("="):
                self.verify_delimiter("operator '<='", REL_LOG_DEL)
                return Token("REL_OP", "<=",self.line, start_col)
            else:
                self.verify_delimiter("operator '<'", REL_LOG_DEL)
                return Token("REL_OP", "<",self.line, start_col)

        elif ch == ">":
            if self.match("="):
                self.verify_delimiter("operator '>='", REL_LOG_DEL)
                return Token("REL_OP", ">=",self.line, start_col)
            else:
                self.verify_delimiter("operator '>'", REL_LOG_DEL)
                return Token("REL_OP", ">",self.line, start_col)

        # LOGICAL OPERATORS
        elif ch == "&":
            if self.match("&"):
                self.verify_delimiter("operator '&&'", REL_LOG_DEL)
                return Token("LOG_OP", "&&",self.line, start_col)
            else:
                raise LexerError("Standalone '&' is invalid", self.line, start_col)

        elif ch == "|":
            if self.match("|"):
                self.verify_delimiter("operator '||'", REL_LOG_DEL)
                return Token("LOG_OP", "||",self.line, start_col)
            else:
                raise LexerError("Standalone '|' is invalid", self.line, start_col)

        # GROUPING & INDEXING
        elif ch == "(":
            self.verify_delimiter("symbol '('", OPEN_PAREN_DEL)
            return Token("OPEN_PAREN", "(",self.line, start_col)
        elif ch == ")":
            self.verify_delimiter("symbol ')'", CLOSE_PAREN_DEL)
            return Token("CLOSE_PAREN", ")",self.line, start_col)
        elif ch == "{":
            self.verify_delimiter("symbol '{'", OPEN_CURLY_DEL)
            return Token("OPEN_CURLY", "{",self.line, start_col)
        elif ch == "}":
            self.verify_delimiter("symbol '}'", CLOSE_CURLY_DEL)
            return Token("CLOSE_CURLY", "}",self.line, start_col)
        elif ch == "[":
            self.verify_delimiter("symbol '['", OPEN_BRACKET_DEL)
            return Token("OPEN_BRACKET", "[",self.line, start_col)
        elif ch == "]":
            self.verify_delimiter("symbol ']'", CLOSE_BRACKET_DEL)
            return Token("CLOSE_BRACKET", "]",self.line, start_col)

        # PUNCTUATION & DIRECTIVES
        elif ch == "~":
            self.verify_delimiter("terminator '~'", TERMINATOR_DEL)
            return Token("TERMINATOR", "~",self.line, start_col)
        elif ch == ",":
            self.verify_delimiter("separator ','", COMMA_DEL)
            return Token("COMMA", ",",self.line, start_col)
        elif ch == ".":
            self.verify_delimiter("symbol '.'", LETTERS)
            return Token("DOT", ".",self.line, start_col)
        elif ch == "#":
            self.verify_delimiter("directive hash '#'", CONJURE_DEL)
            return Token("DIRECTIVE_HASH", "#",self.line, start_col)


        raise LexerError(f"Unexpected character '{ch}'", self.line, start_col)

# ========== TOKENIZER ==========
    def tokenize(self) -> List[Token]:
        """Main driver loop iterating through the source string."""
        while self.pos < len(self.source):
            self.skip_whitespace_and_comments()
            ch = self.current()
            if ch is None:
                break

            if ch in LETTERS:
                self.tokens.append(self.scan_identifier_or_keyword())
            elif ch in NUMBERS:
                self.tokens.append(self.scan_number())
            elif ch == '"':
                self.tokens.append(self.scan_inscription())
            elif ch == "'":
                self.tokens.append(self.scan_glyph())
            else:
                self.tokens.append(self.scan_symbol())

        self.tokens.append(Token("EOF", "EOF", self.line, self.col))
        return self.tokens


# ===================================================================================================
# TESTING
# ===================================================================================================

if __name__ == "__main__":
    sample_program = """
    #/ Program Initialization /#
    #conjure "combat"~

    circle Mage {
        spell aether health[3] = {100, 75, 50}~
        essence mana = 25.5~
        glyph rank = 'S'~
        aura isAlive = blessed~
    }~

    grimoire() {
        manifest (mana != 0.0) {
            mana -= 5.0~
        } counter {
            shatter~
        }
    }
    """

    print("--- TOKENIZING MAGI-C PROGRAM ---\n")
    try:
        lexer = Lexer(sample_program)
        token_stream = lexer.tokenize()
        for tok in token_stream:
            print(tok)
        print("\nLexical Analysis Completed Successfully: 0 Errors.")
    except LexerError as err:
        print(err)