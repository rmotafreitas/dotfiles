"""Convert a Microsoft Keyboard Layout Creator .klc into a Linux XKB symbols file.

usage: python3 -I klc2xkb.py in.klc out_dir [layout_name] [display name]

Writes out_dir/symbols/<layout_name> (the layout) and out_dir/rules/evdev.xml (so GUI settings can
list it). The layout is built on top of us(basic): only keys the KLC defines are overridden, so Esc,
Backspace, arrows, F-keys and modifiers keep coming from the system's own XKB files.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from klc2keylayout import parse, BASE, SHIFT, ALT, SHALT  # noqa: E402

# Windows scancode -> XKB key name
SC2XKB = {
    0x29: "TLDE", 0x02: "AE01", 0x03: "AE02", 0x04: "AE03", 0x05: "AE04", 0x06: "AE05",
    0x07: "AE06", 0x08: "AE07", 0x09: "AE08", 0x0A: "AE09", 0x0B: "AE10", 0x0C: "AE11",
    0x0D: "AE12",
    0x10: "AD01", 0x11: "AD02", 0x12: "AD03", 0x13: "AD04", 0x14: "AD05", 0x15: "AD06",
    0x16: "AD07", 0x17: "AD08", 0x18: "AD09", 0x19: "AD10", 0x1A: "AD11", 0x1B: "AD12",
    0x2B: "BKSL",
    0x1E: "AC01", 0x1F: "AC02", 0x20: "AC03", 0x21: "AC04", 0x22: "AC05", 0x23: "AC06",
    0x24: "AC07", 0x25: "AC08", 0x26: "AC09", 0x27: "AC10", 0x28: "AC11",
    0x56: "LSGT",
    0x2C: "AB01", 0x2D: "AB02", 0x2E: "AB03", 0x2F: "AB04", 0x30: "AB05", 0x31: "AB06",
    0x32: "AB07", 0x33: "AB08", 0x34: "AB09", 0x35: "AB10",
}
SKIP = {0x39: "space is identical on every level, inherited from us(basic)",
        0x53: "numpad decimal: keep the system's NumLock-aware KP_Delete/KP_Decimal"}

DEAD = {"^": "dead_circumflex", "´": "dead_grave", "`": "dead_grave", "~": "dead_tilde"}
# NOTE: the KLC's U+00B4 dead key maps a/e/i/o/u to grave letters (a->à), exactly like U+0060,
# so it is a second grave dead key; dead_grave reproduces that with the system Compose tables.

ASCII_NAMES = {
    " ": "space", "!": "exclam", '"': "quotedbl", "#": "numbersign", "$": "dollar",
    "%": "percent", "&": "ampersand", "'": "apostrophe", "(": "parenleft", ")": "parenright",
    "*": "asterisk", "+": "plus", ",": "comma", "-": "minus", ".": "period", "/": "slash",
    ":": "colon", ";": "semicolon", "<": "less", "=": "equal", ">": "greater",
    "?": "question", "@": "at", "[": "bracketleft", "\\": "backslash", "]": "bracketright",
    "^": "asciicircum", "_": "underscore", "`": "grave", "{": "braceleft", "|": "bar",
    "}": "braceright", "~": "asciitilde",
}
LATIN_NAMES = {
    0xA1: "exclamdown", 0xA3: "sterling", 0xA4: "currency", 0xA5: "yen", 0xA6: "brokenbar",
    0xA7: "section", 0xAA: "ordfeminine", 0xAB: "guillemotleft", 0xAC: "notsign",
    0xAE: "registered", 0xB2: "twosuperior", 0xB3: "threesuperior", 0xB4: "acute",
    0xB5: "mu", 0xB9: "onesuperior", 0xBA: "masculine", 0xBB: "guillemotright",
    0xBC: "onequarter", 0xBD: "onehalf", 0xBE: "threequarters", 0xBF: "questiondown",
    0xC4: "Adiaeresis", 0xC5: "Aring", 0xC6: "AE", 0xC7: "Ccedilla", 0xC9: "Eacute",
    0xCD: "Iacute", 0xD0: "ETH", 0xD1: "Ntilde", 0xD3: "Oacute", 0xD6: "Odiaeresis",
    0xD7: "multiply", 0xD8: "Ooblique", 0xDA: "Uacute", 0xDC: "Udiaeresis", 0xDE: "THORN",
    0xDF: "ssharp", 0xE1: "aacute", 0xC1: "Aacute", 0xE4: "adiaeresis", 0xE5: "aring",
    0xE6: "ae", 0xE7: "ccedilla", 0xE9: "eacute", 0xED: "iacute", 0xF0: "eth", 0xF1: "ntilde",
    0xF3: "oacute", 0xF6: "odiaeresis", 0xF7: "division", 0xF8: "oslash", 0xFA: "uacute",
    0xFC: "udiaeresis", 0xFE: "thorn",
    0x20AC: "EuroSign", 0x2018: "leftsinglequotemark", 0x2019: "rightsinglequotemark",
}


def keysym(cell):
    if cell is None:
        return "NoSymbol"
    ch, is_dead = cell
    if is_dead:
        return DEAD[ch]
    if ch.isascii() and ch.isalnum():
        return ch
    if ch in ASCII_NAMES:
        return ASCII_NAMES[ch]
    return LATIN_NAMES.get(ord(ch), "U%04X" % ord(ch))


def key_type(cap, cols):
    """Pick the XKB type matching the KLC's Caps Lock rules (bit 1: caps shifts the base layer,
    bit 4: caps shifts the AltGr layer). Cap=4 alone (the comma key: Caps+AltGr+, -> Ç) has no stock
    XKB type, so that key uses plain FOUR_LEVEL and Caps+AltGr+, gives ç. Known deviation."""
    has_alt = cols[ALT] is not None or cols[SHALT] is not None
    if cap & 1:
        return "FOUR_LEVEL_ALPHABETIC" if cap & 4 else (
            "FOUR_LEVEL_SEMIALPHABETIC" if has_alt else "ALPHABETIC")
    return "FOUR_LEVEL" if has_alt else "TWO_LEVEL"


def build(keys, name):
    out = [
        "// %s - generated from a Microsoft KLC file by klc2xkb.py" % name,
        "// Install: ~/.config/xkb/symbols/<this file name> (see README).",
        "// AltGr = Right Alt. Dead keys: Shift+6 (^), Shift+` (~), ` (grave), AltGr+' (grave).",
        "default partial alphanumeric_keys",
        'xkb_symbols "basic" {',
        '    include "us(basic)"',
        '    include "level3(ralt_switch)"',
        '    name[Group1] = "%s";' % name,
        "",
    ]
    rows = []
    for sc, (cap, cols) in keys.items():
        if sc in SKIP:
            continue
        xkb = SC2XKB[sc]
        ktype = key_type(cap, cols)
        syms = [keysym(cols[i]) for i in (BASE, SHIFT, ALT, SHALT)]
        if ktype in ("TWO_LEVEL", "ALPHABETIC"):
            syms = syms[:2]
        comment = " ".join(c[0] if c else "-" for c in (cols[i] for i in (BASE, SHIFT, ALT, SHALT)))
        rows.append((xkb, '    key <%s> { type[Group1] = "%s", [ %s ] };  // %s'
                     % (xkb, ktype, ", ".join(syms), comment)))
    out.extend(line for _, line in sorted(rows, key=lambda r: SC2XKB_ORDER.index(r[0])))
    out.append("};")
    return "\n".join(out) + "\n"


SC2XKB_ORDER = [SC2XKB[k] for k in sorted(SC2XKB)]

EVDEV = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xkbConfigRegistry SYSTEM "xkb.dtd">
<xkbConfigRegistry version="1.1">
  <layoutList>
    <layout>
      <configItem>
        <name>{layout}</name>
        <shortDescription>{layout}</shortDescription>
        <description>{name}</description>
      </configItem>
    </layout>
  </layoutList>
</xkbConfigRegistry>
"""

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    layout = sys.argv[3] if len(sys.argv) > 3 else "tmf"
    name = sys.argv[4] if len(sys.argv) > 4 else "TMF Keyboard"
    keys, _dead = parse(src)
    os.makedirs(os.path.join(dst, "symbols"), exist_ok=True)
    os.makedirs(os.path.join(dst, "rules"), exist_ok=True)
    with open(os.path.join(dst, "symbols", layout), "w", encoding="utf-8") as f:
        f.write(build(keys, name))
    with open(os.path.join(dst, "rules", "evdev.xml"), "w", encoding="utf-8") as f:
        f.write(EVDEV.format(layout=layout, name=name))
    print("wrote", dst, "layout:", layout)
