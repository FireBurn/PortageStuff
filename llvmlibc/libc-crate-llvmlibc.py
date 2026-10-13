#!/usr/bin/env python3
"""Gives the libc crate LLVM's libc's definitions on x86_64-unknown-linux-llvmlibc.

That target builds the way the gnu target does and sets
target_abi = "llvmlibc", so the crate would otherwise take its glibc
definitions, and some of LLVM's libc's types and values are not glibc's.
Each glibc definition that differs is put behind
cfg(not(target_abi = "llvmlibc")), and llvmlibc.rs, which sits beside this
script, is added to the gnu module in their place.

Usage: libc-crate-llvmlibc.py CRATE_DIR...
Running it again on a crate it has already changed changes nothing.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = '#[cfg(not(target_abi = "llvmlibc"))]'
MODULE = "src/unix/linux_like/linux/gnu/llvmlibc.rs"
GNU = "src/unix/linux_like/linux/gnu/mod.rs"
INCLUDE = """
// LLVM's libc on x86_64: see llvmlibc.rs.
cfg_if! {
    if #[cfg(target_abi = "llvmlibc")] {
        mod llvmlibc;
        pub use self::llvmlibc::*;
    }
}
"""


def replaced_names(module):
    """The names llvmlibc.rs defines, by kind."""
    structs = set(re.findall(r"^\s*pub struct (\w+)", module, re.M))
    others = set(re.findall(r"^pub (?:type|const) (\w+)", module, re.M))
    return structs, others


MACRO_OPEN = re.compile(r"^(\s*)([a-z_][a-z0-9_]*)! \{\s*$")


def indent_of(line):
    return len(line) - len(line.lstrip(" "))


def item_start(lines, i, ind):
    """The first line of the item at line i, taking in its attributes and
    comments but not a gate already put there."""
    start = i
    k = i - 1
    while k >= 0:
        stripped = lines[k].strip()
        if not stripped or stripped == GATE:
            break
        if indent_of(lines[k]) > ind:
            # A continuation of an attribute, indented past its first line.
            m = attribute_opening(lines, k, ind)
            if m is None:
                break
            start = m
            k = m - 1
            continue
        if indent_of(lines[k]) != ind:
            break
        if stripped.startswith("#[") or stripped.startswith("//"):
            start = k
            k -= 1
            continue
        if stripped.endswith(")]"):
            # The end of an attribute spread over several lines.
            m = attribute_opening(lines, k, ind)
            if m is None:
                break
            start = m
            k = m - 1
            continue
        break
    return start


def attribute_opening(lines, k, ind):
    """The line at the item's indentation that opens the attribute line k
    continues, or None if k is not inside one."""
    m = k
    while m >= 0:
        stripped = lines[m].strip()
        if not stripped:
            return None
        if indent_of(lines[m]) == ind and stripped.startswith("#["):
            return m
        if indent_of(lines[m]) < ind:
            return None
        m -= 1
    return None


def item_end(lines, i, ind):
    if lines[i].rstrip().endswith("}"):
        return i
    closing = " " * ind + "}"
    for j in range(i + 1, len(lines)):
        if lines[j].rstrip() == closing:
            return j
    raise SystemExit("no end to the item at line %d" % (i + 1))


def enclosing(lines, start, ind):
    for k in range(start - 1, -1, -1):
        if lines[k].strip() and indent_of(lines[k]) < ind:
            return k
    return None


def gate(text, structs, others):
    """Keeps the glibc definitions of the replaced names from the llvmlibc
    target.

    A struct inside one of the crate's struct macros is moved into an
    invocation of its own with the cfg on it. Older versions of those macros
    emit the struct's trait impls beside it, and a cfg on the struct alone
    would leave them behind. Anything else takes the cfg as an attribute."""
    lines = text.split("\n")
    changed = 0
    struct_re = re.compile(r"^(\s*)pub (?:struct|union) (?:%s)\b" %
                           "|".join(sorted(structs)))
    other_re = re.compile(r"^(\s*)pub (?:type|const) (?:%s)\b(?!\s*\()" %
                          "|".join(sorted(others)))
    impl_re = re.compile(r"^(\s*)impl\b[^{]*\bfor (?:crate::|::)?(?:%s)\b" %
                         "|".join(sorted(structs)))
    progress = True
    while progress:
        progress = False
        for i, line in enumerate(lines):
            if struct_re.match(line):
                ind = indent_of(line)
                start = item_start(lines, i, ind)
                k = enclosing(lines, start, ind)
                opener = MACRO_OPEN.match(lines[k]) if k is not None else None
                if opener:
                    if k > 0 and lines[k - 1].strip() == GATE:
                        continue
                    outer, macro = opener.group(1), opener.group(2)
                    end = item_end(lines, i, ind)
                    lines[start:end + 1] = (
                        [outer + "}", outer + GATE, outer + macro + "! {"] +
                        lines[start:end + 1] +
                        [outer + "}", outer + macro + "! {"])
                else:
                    if start > 0 and lines[start - 1].strip() == GATE:
                        continue
                    lines.insert(start, " " * ind + GATE)
                changed += 1
                progress = True
                break
            m = other_re.match(line) or impl_re.match(line)
            if m:
                if i > 0 and lines[i - 1].strip() == GATE:
                    continue
                lines.insert(i, m.group(1) + GATE)
                changed += 1
                progress = True
                break
    return "\n".join(lines), changed


def patch(crate):
    manifest = open(os.path.join(crate, "Cargo.toml")).read()
    if not re.search(r'^name = "libc"$', manifest, re.M) or \
            not re.search(r'^version = "0\.2\.\d+"$', manifest, re.M):
        raise SystemExit("%s is not the libc crate at 0.2" % crate)
    module = open(os.path.join(HERE, "llvmlibc.rs")).read()
    structs, others = replaced_names(module)
    touched = []

    target = os.path.join(crate, MODULE)
    if not os.path.exists(target) or open(target).read() != module:
        open(target, "w").write(module)
        touched.append(MODULE)

    roots = [os.path.join(crate, "src/unix/linux_like")]
    for sub in ("src/new/glibc", "src/new/common"):
        if os.path.isdir(os.path.join(crate, sub)):
            roots.append(os.path.join(crate, sub))
    for root in roots:
        for d, _, files in os.walk(root):
            for f in files:
                path = os.path.join(d, f)
                rel = os.path.relpath(path, crate)
                if not f.endswith(".rs") or rel == MODULE:
                    continue
                text = open(path).read()
                new, changed = gate(text, structs, others)
                if changed:
                    open(path, "w").write(new)
                    touched.append(rel)

    gnu = os.path.join(crate, GNU)
    text = open(gnu).read()
    if "mod llvmlibc;" not in text:
        open(gnu, "w").write(text.rstrip("\n") + "\n" + INCLUDE)
        if GNU not in touched:
            touched.append(GNU)

    checksums = os.path.join(crate, ".cargo-checksum.json")
    if touched and os.path.exists(checksums):
        record = json.load(open(checksums))
        if record.get("files"):
            for rel in touched:
                data = open(os.path.join(crate, rel), "rb").read()
                record["files"][rel] = hashlib.sha256(data).hexdigest()
            json.dump(record, open(checksums, "w"), separators=(",", ":"))
    return touched


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for crate in sys.argv[1:]:
        touched = patch(crate)
        print("%s: %d files changed" % (crate, len(touched)))


main()
