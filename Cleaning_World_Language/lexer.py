import re
import sys
import os

TOKEN_DEFS = [
    ("EQ", r"==", False), ("NEQ", r"!=", False), ("LE", r"<=", False), ("GE", r">=", False),
    ("AND", r"&&", False), ("OR", r"\|\|", False),
    ("ASSIGN", r"=", False), ("LT", r"<", False), ("GT", r">", False),
    ("PLUS", r"\+", False), ("MINUS", r"-", False), ("STAR", r"\*", False), ("SLASH", r"/", False),
    ("NOT", r"!", False),
    ("SEMI", r";", False), ("COMMA", r",", False), ("COLON", r":", False),
    ("LPAREN", r"\(", False), ("RPAREN", r"\)", False),

    ("PROGRAM", r"\bprogram\b", True),
    ("BEGIN", r"\bbegin\b", True),
    ("END", r"\bend\b", True),
    ("VAR", r"\bvar\b", True),
    ("FUNC", r"\bfunc\b", True),
    ("RETURN", r"\breturn\b", True),
    ("IF", r"\bif\b", True),
    ("THEN", r"\bthen\b", True),
    ("ELSE", r"\belse\b", True),
    ("WHILE", r"\bwhile\b", True),
    ("DO", r"\bdo\b", True),
    ("PRINT", r"\bprint\b", True),
    ("BREAK", r"\bbreak\b", True),
    ("WORLD", r"\bworld\b", True),
    ("AGENT", r"\bagent\b", True),
    
    ("TYPE", r"\bint\b|\bbool\b|\bstring\b", True),
    ("BOOL", r"\btrue\b|\bfalse\b", True),
    ("DIR", r"\bN\b|\bE\b|\bS\b|\bW\b", True),

    ("INT", r"\d+", False),
    ("STR", r"\"([^\"\\\n]|\\.)*\"", False),  
    ("ID", r"[A-Za-z_][A-Za-z0-9_]*", False),
]

TOK_RES = [(name, re.compile(pattern)) for name, pattern, _ in TOKEN_DEFS]

TOKEN_ID = {name: i + 1 for i, (name, _, _) in enumerate(TOKEN_DEFS)}
TOKEN_ID["ERROR"] = 999

RESERVED = set()
for name, pattern, is_reserved in TOKEN_DEFS:
    if is_reserved:
        clean_pat = pattern.replace(r"\b", "")
        for word in clean_pat.split("|"):
            if word.isalnum():
                RESERVED.add(word)

RE_WS    = re.compile(r"[ \t\r\n]+")
RE_LINE  = re.compile(r"//[^\n]*")
RE_BLOCK = re.compile(r"/\*[\s\S]*?\*/")

def tokenize(src):
    tokens = []
    i, n, line = 0, len(src), 1
    
    symtab = {}
    littab = []

    while i < n:
        m = RE_WS.match(src, i)
        if m:
            line += src[i:m.end()].count("\n")
            i = m.end()
            continue
        m = RE_LINE.match(src, i)
        if m:
            i = m.end()
            continue
        m = RE_BLOCK.match(src, i)
        if m:
            line += src[i:m.end()].count("\n")
            i = m.end()
            continue

        matched = False
        for kind, rx in TOK_RES:
            m = rx.match(src, i)
            if not m: continue
            lex = m.group(0)

            if kind == "ID" and lex not in RESERVED:
                symtab.setdefault(lex, {"kind": "id"})
            if kind == "STR":
                littab.append(lex)

            tid = TOKEN_ID[kind]
            tokens.append({
                "line": line,
                "tid": tid,
                "kind": kind,
                "lexeme": lex
            })

            line += lex.count("\n")
            i = m.end()
            matched = True
            break

        if not matched:
            bad = src[i]
            tokens.append({
                "line": line,
                "tid": 999,
                "kind": "ERROR",
                "lexeme": bad
            })
            if bad == "\n": line += 1
            i += 1
            
    return tokens

def main():
    src = ""
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        filename = sys.argv[1]
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' not found.")
            return
        with open(filename, "r", encoding="utf-8") as fh:
            src = fh.read()
    else:
        src = sys.stdin.read()
        
    tokens = tokenize(src)
    for t in tokens:
        print(f"{t['line']:>3}  {t['tid']:>3}  {t['kind']:<7} {t['lexeme']}")

if __name__ == "__main__":
    main()
