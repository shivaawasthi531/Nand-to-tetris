import re
import sys

SYMBOL = re.compile(r"^[A-Za-z_.$:][A-Za-z0-9_.$:]*$")

PRESET = {"SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4, "SCREEN": 16384, "KBD": 24576}
for n in range(16):
    PRESET["R%d" % n] = n

BASE = {
    "0": "101010", "1": "111111", "-1": "111010", "D": "001100",
    "A": "110000", "!D": "001101", "!A": "110001", "-D": "001111",
    "-A": "110011", "D+1": "011111", "A+1": "110111", "D-1": "001110",
    "A-1": "110010", "D+A": "000010", "D-A": "010011", "A-D": "000111",
    "D&A": "000000", "D|A": "010101",
}
COMP = {}
for k, v in BASE.items():
    COMP[k] = "0" + v
    if "A" in k:
        COMP[k.replace("A", "M")] = "1" + v

JUMP = {"": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
        "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111"}


def clean(line):
    return "".join(line.split("//")[0].split())


def dest_bits(d):
    if d == "":
        return "000"
    if any(c not in "ADM" for c in d) or len(set(d)) != len(d):
        return None
    return "".join("1" if c in d else "0" for c in "ADM")


def assemble(path):
    with open(path) as f:
        raw = f.read().splitlines()

    errors = []
    symbols = dict(PRESET)
    lines = []

    for no, text in enumerate(raw, 1):
        s = clean(text)
        if not s:
            continue
        if s[0] == "(":
            name = s[1:-1]
            if not s.endswith(")") or not SYMBOL.match(name):
                errors.append("Line %d: invalid label" % no)
            else:
                symbols[name] = len(lines)
        else:
            lines.append((no, s))

    out = []
    nxt = 16

    for no, s in lines:
        if s[0] == "@":
            val = s[1:]
            if val.isdigit():
                n = int(val)
                if n > 32767:
                    errors.append("Line %d: address out of range" % no)
                    continue
            elif SYMBOL.match(val):
                if val not in symbols:
                    symbols[val] = nxt
                    nxt += 1
                n = symbols[val]
            else:
                errors.append("Line %d: invalid A-instruction" % no)
                continue
            out.append(format(n, "016b"))
        else:
            d, c, j = "", s, ""
            if "=" in s:
                d, c = s.split("=", 1)
            if ";" in c:
                c, j = c.split(";", 1)
            db = dest_bits(d)
            if db is None:
                errors.append("Line %d: invalid destination" % no)
            elif c not in COMP:
                errors.append("Line %d: invalid instruction" % no)
            elif j not in JUMP:
                errors.append("Line %d: invalid jump" % no)
            else:
                out.append("111" + COMP[c] + db + JUMP[j])

    return out, errors


def main():
    if len(sys.argv) != 2:
        print("usage: python assembler.py File.asm")
        sys.exit(1)
    src = sys.argv[1]
    try:
        out, errors = assemble(src)
    except FileNotFoundError:
        print("File not found: " + src)
        sys.exit(1)
    if errors:
        for e in errors:
            print(e)
        sys.exit(1)
    dst = src.rsplit(".", 1)[0] + ".hack"
    with open(dst, "w") as f:
        f.write("\n".join(out) + "\n")
    print("Wrote " + dst)


if __name__ == "__main__":
    main()