"""Convert a Microsoft Keyboard Layout Creator .klc into a macOS .keylayout.

usage: python3 -I klc2keylayout.py in.klc out.keylayout [display name]
"""
import sys
from collections import OrderedDict

# Windows scancode -> Mac virtual keycode (ANSI positions)
SC2MAC = {
    0x02: 18, 0x03: 19, 0x04: 20, 0x05: 21, 0x06: 23, 0x07: 22, 0x08: 26,
    0x09: 28, 0x0A: 25, 0x0B: 29, 0x0C: 27, 0x0D: 24,
    0x10: 12, 0x11: 13, 0x12: 14, 0x13: 15, 0x14: 17, 0x15: 16, 0x16: 32,
    0x17: 34, 0x18: 31, 0x19: 35, 0x1A: 33, 0x1B: 30,
    0x1E: 0, 0x1F: 1, 0x20: 2, 0x21: 3, 0x22: 5, 0x23: 4, 0x24: 38,
    0x25: 40, 0x26: 37, 0x27: 41, 0x28: 39, 0x2B: 42,
    0x2C: 6, 0x2D: 7, 0x2E: 8, 0x2F: 9, 0x30: 11, 0x31: 45, 0x32: 46,
    0x33: 43, 0x34: 47, 0x35: 44,
    0x39: 49, 0x53: 65,
}
# sc 29 is the grave/tilde key. Its Mac keycode is 50 on ANSI hardware but 10 on ISO hardware, and
# the hardware ID that selects between them is unreliable, so it is mapped to both. sc 56 (the ISO
# extra key) is a duplicate of sc 2b in the KLC, so it is skipped.
SC_GRAVE, SC_102 = 0x29, 0x56
# Keys with no entry in a KLC: macOS needs them defined or they type nothing.
SPECIAL = {
    36: "\r", 48: "\t", 51: "\x08", 52: "\x03", 53: "\x1b", 71: "\x1b", 76: "\x03",
    114: "\x05", 115: "\x01", 116: "\x0b", 117: "\x7f", 119: "\x04", 121: "\x0c",
    123: "\x1c", 124: "\x1d", 125: "\x1f", 126: "\x1e",
    66: "\x1d", 70: "\x1c", 72: "\x1f", 77: "\x1e",
    102: "\x10", 104: "\x10", 108: "\x10", 110: "\x10", 112: "\x10",
    # F1-F20
    **{c: "\x10" for c in (122, 120, 99, 118, 96, 97, 98, 100, 101, 109, 103, 111, 105,
                            107, 113, 106, 64, 79, 80, 90)},
    # keypad
    67: "*", 69: "+", 75: "/", 78: "-", 81: "=",
    82: "0", 83: "1", 84: "2", 85: "3", 86: "4", 87: "5", 88: "6", 89: "7", 91: "8", 92: "9",
}
DEAD_NAMES = {0x5E: "circumflex", 0xB4: "acute", 0x60: "grave", 0x7E: "tilde"}

# column order in the KLC LAYOUT rows after Cap: base, shift, ctrl, ctrl+alt, shift+ctrl+alt
BASE, SHIFT, CTRL, ALT, SHALT = range(5)


def parse(path):
    text = open(path, encoding="utf-16").read().replace("\r", "")
    keys, dead, section, cur = OrderedDict(), OrderedDict(), None, None
    for raw in text.split("\n"):
        line = raw.split("//")[0].rstrip()
        if not line.strip():
            continue
        parts = line.split("\t")
        head = parts[0].strip()
        if head in ("LAYOUT", "KEYNAME", "KEYNAME_EXT", "KEYNAME_DEAD", "DESCRIPTIONS",
                    "LANGUAGENAMES", "ENDKBD", "SHIFTSTATE", "KBD"):
            section = head
            continue
        if head == "DEADKEY":
            cur = int(parts[1], 16)
            dead[cur] = {}
            section = "DEADKEY"
            continue
        if section == "LAYOUT":
            f = [p for p in parts if p != ""]
            sc, cap = int(f[0], 16), int(f[2])
            cols = []
            for v in f[3:8]:
                if v == "-1":
                    cols.append(None)
                    continue
                is_dead = v.endswith("@")
                v = v.rstrip("@")
                ch = chr(int(v, 16)) if len(v) > 1 else v
                cols.append((ch, is_dead))
            while len(cols) < 5:
                cols.append(None)
            keys[sc] = (cap, cols)
        elif section == "DEADKEY":
            f = [p for p in parts if p != ""]
            dead[cur][chr(int(f[0], 16))] = chr(int(f[1], 16))
    return keys, dead


def esc(s):
    return "".join(c if c.isascii() and (c.isalnum() or c == "_") else "&#x%04X;" % ord(c) for c in s)


def build(keys, dead, name):
    states = {chr(k): DEAD_NAMES.get(k, "dead%04x" % k) for k in dead}
    actions = OrderedDict()

    # re-key dead maps by char for lookup
    dead_by_char = {chr(k): v for k, v in dead.items()}

    def ref(cell):
        if cell is None:
            return None
        ch, is_dead = cell
        if is_dead:
            aid = "dead_" + states[ch]
            actions[aid] = [("none", "next", states[ch])]
            return ("action", aid)
        whens = [(states[d], dead_by_char[d][ch]) for d in states if ch in dead_by_char[d]]
        if not whens:
            return ("output", ch)
        aid = "a_%04x" % ord(ch)
        actions[aid] = [("none", "output", ch)] + [(s, "output", out) for s, out in whens]
        return ("action", aid)

    def ctrl_char(cell, base):
        if cell is not None:
            return cell
        if base and not base[1] and base[0].isalpha() and base[0].isascii():
            return (chr(ord(base[0].lower()) & 0x1F), False)
        return base

    # keymap indices: 0 base, 1 shift, 2 caps, 3 option, 4 shift+option, 5 caps+option,
    # 6 control, 7 command
    def per_key(cap, cols):
        base, shift, ctrl, alt, shalt = cols
        caps = shift if (cap & 1) else base
        capsalt = shalt if (cap & 4) else alt
        return [base, shift, caps, alt, shalt, capsalt, ctrl_char(ctrl, base), base]

    def keymap_xml(index, mapping):
        out = ['    <keyMap index="%d">' % index]
        for code in sorted(mapping):
            kind, val = mapping[code][index]
            out.append('      <key code="%d" %s="%s"/>' % (code, kind, esc(val)))
        out.append("    </keyMap>")
        return out

    def build_mapping():
        m = {}
        for sc, (cap, cols) in keys.items():
            if sc == SC_102:
                continue
            codes = [10, 50] if sc == SC_GRAVE else [SC2MAC.get(sc)]
            if codes[0] is None:
                continue
            row = per_key(cap, cols)
            refs = [ref(c) for c in row]
            if refs[0] is None:
                continue
            fallback = {1: 0, 2: 0, 3: 0, 4: 1, 5: 2, 6: 0, 7: 0}
            for i in range(1, 8):
                if refs[i] is None:
                    refs[i] = refs[fallback[i]]
            for code in codes:
                m[code] = refs
        for code, ch in SPECIAL.items():
            m.setdefault(code, [("output", ch)] * 8)
        return m

    mapping = build_mapping()

    x = ['<?xml version="1.1" encoding="UTF-8"?>',
         '<!DOCTYPE keyboard SYSTEM "file://localhost/System/Library/DTDs/KeyboardLayout.dtd">',
         '<keyboard group="126" id="-23456" name="%s" maxout="3">' % name.replace('"', ""),
         '  <layouts>',
         '    <layout first="0" last="255" modifiers="Modifiers" mapSet="Keys"/>',
         '  </layouts>',
         '  <modifierMap id="Modifiers" defaultIndex="0">',
         '    <keyMapSelect mapIndex="0"><modifier keys=""/></keyMapSelect>',
         '    <keyMapSelect mapIndex="1"><modifier keys="anyShift"/></keyMapSelect>',
         '    <keyMapSelect mapIndex="2"><modifier keys="caps"/></keyMapSelect>',
         '    <keyMapSelect mapIndex="3"><modifier keys="anyOption"/></keyMapSelect>',
         '    <keyMapSelect mapIndex="4"><modifier keys="anyShift anyOption"/></keyMapSelect>',
         '    <keyMapSelect mapIndex="5"><modifier keys="caps anyOption"/></keyMapSelect>',
         '    <keyMapSelect mapIndex="6"><modifier keys="anyControl anyShift? anyOption? caps?"/></keyMapSelect>',
         '    <keyMapSelect mapIndex="7"><modifier keys="command anyShift? caps? anyOption? anyControl?"/></keyMapSelect>',
         '  </modifierMap>']
    for set_id in ("Keys",):
        x.append('  <keyMapSet id="%s">' % set_id)
        for i in range(8):
            x.extend(keymap_xml(i, mapping))
        x.append("  </keyMapSet>")

    x.append("  <actions>")
    for aid, whens in actions.items():
        x.append('    <action id="%s">' % aid)
        for state, attr, val in whens:
            if attr == "next":
                x.append('      <when state="%s" next="%s"/>' % (state, esc(val)))
            else:
                x.append('      <when state="%s" output="%s"/>' % (state, esc(val)))
        x.append("    </action>")
    x.append("  </actions>")

    x.append("  <terminators>")
    for ch, st in states.items():
        term = dead_by_char[ch].get(" ", ch)
        x.append('    <when state="%s" output="%s"/>' % (st, esc(term)))
    x.append("  </terminators>")
    x.append("</keyboard>")
    return "\n".join(x) + "\n"


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else "US-Intern.No dead PT-US"
    keys, dead = parse(src)
    open(dst, "w", encoding="utf-8").write(build(keys, dead, name))
    print("wrote", dst, "keys:", len(keys), "dead keys:", len(dead))
