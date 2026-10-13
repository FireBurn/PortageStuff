#!/usr/bin/env python3
"""Teaches the cc crate the x86_64-unknown-linux-llvmlibc target.

That target sets target_abi = "llvmlibc", which cc would join to the gnu
environment and hand to clang as x86_64-unknown-linux-gnullvmlibc. To clang
it is the gnu target, so the abi is dropped the way cc already drops "llvm".
A triple cc parses itself, without cargo's variables to go on, is given the
gnu environment too.

Usage: cc-crate-llvmlibc.py CRATE_DIR...
Running it again on a crate it has already changed changes nothing.
"""
import hashlib
import json
import os
import re
import sys

EDITS = [
    ("src/target/llvm.rs",
     '"llvm" | "softfloat"',
     '"llvm" | "llvmlibc" | "softfloat"'),
    ("src/target/parser.rs",
     '        // Environments\n',
     '        // Environments\n        "llvmlibc" => ("gnu", ""),\n'),
]


def patch(crate):
    manifest = open(os.path.join(crate, "Cargo.toml")).read()
    if not re.search(r'^name = "cc"$', manifest, re.M):
        raise SystemExit("%s is not the cc crate" % crate)
    touched = []
    for rel, anchor, replacement in EDITS:
        path = os.path.join(crate, rel)
        if not os.path.exists(path):
            continue
        text = open(path).read()
        if '"llvmlibc"' in text or anchor not in text:
            continue
        open(path, "w").write(text.replace(anchor, replacement, 1))
        touched.append(rel)
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
        print("%s: %s" % (crate, ", ".join(touched) or "nothing changed"))


main()
