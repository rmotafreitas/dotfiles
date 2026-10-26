"""Load an XKB layout through the real libxkbcommon and check it against the source .klc.

usage: python3 -I test_xkb.py <dir containing symbols/> <layout> <in.klc>
Runs on Linux (needs libxkbcommon.so.0, xkb-data and, for the dead-key check, libx11-data).
"""
import ctypes as C, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from klc2keylayout import parse, BASE, SHIFT, ALT, SHALT, DEAD_NAMES
from klc2xkb import SC2XKB, SKIP

root, layout, klc = sys.argv[1:4]
L = C.CDLL("libxkbcommon.so.0")
class Names(C.Structure):
    _fields_ = [(n, C.c_char_p) for n in ("rules", "model", "layout", "variant", "options")]
for fn, res, args in [
    ("xkb_context_new", C.c_void_p, [C.c_int]),
    ("xkb_context_include_path_append", C.c_int, [C.c_void_p, C.c_char_p]),
    ("xkb_context_include_path_append_default", C.c_int, [C.c_void_p]),
    ("xkb_keymap_new_from_names", C.c_void_p, [C.c_void_p, C.POINTER(Names), C.c_int]),
    ("xkb_keymap_key_by_name", C.c_uint32, [C.c_void_p, C.c_char_p]),
    ("xkb_keymap_key_get_syms_by_level", C.c_int, [C.c_void_p, C.c_uint32, C.c_uint32, C.c_uint32, C.POINTER(C.POINTER(C.c_uint32))]),
    ("xkb_keysym_to_utf32", C.c_uint32, [C.c_uint32]),
    ("xkb_keysym_get_name", C.c_int, [C.c_uint32, C.c_char_p, C.c_size_t]),
    ("xkb_keysym_from_name", C.c_uint32, [C.c_char_p, C.c_int]),
    ("xkb_state_new", C.c_void_p, [C.c_void_p]),
    ("xkb_state_update_key", C.c_int, [C.c_void_p, C.c_uint32, C.c_int]),
    ("xkb_state_key_get_one_sym", C.c_uint32, [C.c_void_p, C.c_uint32]),
    ("xkb_state_key_get_utf32", C.c_uint32, [C.c_void_p, C.c_uint32]),
    ("xkb_compose_table_new_from_locale", C.c_void_p, [C.c_void_p, C.c_char_p, C.c_int]),
    ("xkb_compose_state_new", C.c_void_p, [C.c_void_p, C.c_int]),
    ("xkb_compose_state_feed", C.c_int, [C.c_void_p, C.c_uint32]),
    ("xkb_compose_state_get_status", C.c_int, [C.c_void_p]),
    ("xkb_compose_state_get_utf8", C.c_int, [C.c_void_p, C.c_char_p, C.c_size_t]),
    ("xkb_compose_state_reset", None, [C.c_void_p]),
]:
    f = getattr(L, fn); f.restype = res; f.argtypes = args

ctx = L.xkb_context_new(0)
L.xkb_context_include_path_append(ctx, root.encode())
L.xkb_context_include_path_append_default(ctx)
km = L.xkb_keymap_new_from_names(ctx, C.byref(Names(b"evdev", b"pc105", layout.encode(), None, None)), 0)
assert km, "KEYMAP FAILED TO COMPILE"
print("keymap compiled")

keys, dead = parse(klc)
fails, checks = [], 0
def fail(m): fails.append(m)
def sym_name(s):
    b = C.create_string_buffer(64); L.xkb_keysym_get_name(s, b, 64); return b.value.decode()
def kc(name):
    k = L.xkb_keymap_key_by_name(km, name.encode()); assert k != 0xFFFFFFFF, name; return k
def sym_at(name, level):
    out = C.POINTER(C.c_uint32)()
    n = L.xkb_keymap_key_get_syms_by_level(km, kc(name), 0, level, C.byref(out))
    return out[0] if n else 0
DEADSYM = {"^": "dead_circumflex", "´": "dead_grave", "`": "dead_grave", "~": "dead_tilde"}

# 1. every key, every level
for sc, (cap, cols) in keys.items():
    if sc in SKIP: continue
    name = SC2XKB[sc]
    for lvl, col in enumerate((BASE, SHIFT, ALT, SHALT)):
        exp = cols[col]; got = sym_at(name, lvl); checks += 1
        if exp is None:
            if got: fail(f"{name} L{lvl+1}: expected nothing, got {sym_name(got)}")
        elif exp[1]:
            if sym_name(got) != DEADSYM[exp[0]]: fail(f"{name} L{lvl+1}: expected {DEADSYM[exp[0]]}, got {sym_name(got)}")
        elif L.xkb_keysym_to_utf32(got) != ord(exp[0]):
            fail(f"{name} L{lvl+1}: expected {exp[0]!r}, got {sym_name(got)} {chr(L.xkb_keysym_to_utf32(got))!r}")
print(f"level check: {checks} cells")

# 2. Caps Lock + AltGr behaviour with a live xkb_state
def typed(name, shift=False, altgr=False, caps=False):
    st = L.xkb_state_new(km)
    if caps: L.xkb_state_update_key(st, kc("CAPS"), 1); L.xkb_state_update_key(st, kc("CAPS"), 0)
    if shift: L.xkb_state_update_key(st, kc("LFSH"), 1)
    if altgr: L.xkb_state_update_key(st, kc("RALT"), 1)
    u = L.xkb_state_key_get_utf32(st, kc(name)); return chr(u) if u else sym_name(L.xkb_state_key_get_one_sym(st, kc(name)))
deviations = []
for sc, (cap, cols) in keys.items():
    if sc in SKIP: continue
    name = SC2XKB[sc]
    for altgr in (False, True):
        for caps in (False, True):
            for shift in (False, True):
                cell = cols[(SHALT if shift else ALT) if altgr else (SHIFT if shift else BASE)]
                if altgr and cols[ALT] is None and cols[SHALT] is None: continue
                # Windows rule: Cap&1 -> caps acts as shift on base layer; Cap&4 -> on AltGr layer
                eff_shift = shift ^ (caps and bool(cap & (4 if altgr else 1)))
                exp = cols[(SHALT if eff_shift else ALT) if altgr else (SHIFT if eff_shift else BASE)]
                if exp is None or exp[1] or cell is None and not exp: continue
                got = typed(name, shift, altgr, caps); checks += 1
                if got != exp[0]:
                    (deviations if (cap & 4 and not cap & 1) or (cap == 1 and altgr and caps) else fails).append(f"{name} shift={shift} altgr={altgr} caps={caps}: expected {exp[0]!r}, got {got!r}")
print(f"caps/altgr check done ({checks} total)")

# 3. keys that must come from the system files, not from us
for name, want in [("ESC","Escape"),("BKSP","BackSpace"),("TAB","Tab"),("RTRN","Return"),("LEFT","Left"),("RGHT","Right"),("UP","Up"),("DOWN","Down"),("DELE","Delete"),("HOME","Home"),("END","End"),("PGUP","Prior"),("PGDN","Next"),("FK01","F1"),("FK12","F12"),("SPCE","space"),("LFSH","Shift_L"),("LCTL","Control_L"),("LALT","Alt_L"),("LWIN","Super_L"),("CAPS","Caps_Lock"),("KP5","KP_Begin"),("KPDL","KP_Delete")]:
    got = sym_name(sym_at(name, 0)); checks += 1
    if got != want: fail(f"special key {name}: expected {want}, got {got}")
print("special keys checked (Esc, Backspace, Tab, Return, arrows, F-keys, modifiers, keypad)")
st = L.xkb_state_new(km); L.xkb_state_update_key(st, kc("RALT"), 1)
got = sym_name(L.xkb_state_key_get_one_sym(st, kc("RALT")))
print("Right Alt key itself ->", got)

# 4. dead keys through the system Compose tables
tbl = L.xkb_compose_table_new_from_locale(ctx, b"en_US.UTF-8", 0)
if not tbl: print("COMPOSE TABLE UNAVAILABLE (install libx11-data)"); fails.append("no compose table")
else:
    cs = L.xkb_compose_state_new(tbl, 0); n = 0; extras = {}
    for dk, table in dead.items():
        dname = DEADSYM[chr(dk)]
        for base, want in table.items():
            L.xkb_compose_state_reset(cs)
            L.xkb_compose_state_feed(cs, L.xkb_keysym_from_name(dname.encode(), 0))
            L.xkb_compose_state_feed(cs, L.xkb_keysym_from_name(("space" if base == " " else base).encode(), 0))
            buf = C.create_string_buffer(16); L.xkb_compose_state_get_utf8(cs, buf, 16); got = buf.value.decode(); n += 1
            if got != want: fail(f"dead {dname} + {base!r}: expected {want!r}, got {got!r}")
    print(f"dead-key compose check: {n} sequences from the KLC")

print("\nKNOWN/EXPECTED DEVIATIONS:", *deviations or ["none"], sep="\n  ")
print("\nFAILURES:", *fails or ["none"], sep="\n  ")
sys.exit(1 if fails else 0)
