#!/usr/bin/env python3
"""Teaches the target-lexicon crate the llvmlibc environment.

Its build script parses the compiler's host triple and panics on anything
it does not recognise, so x86_64-unknown-linux-llvmlibc stops every crate
that depends on it. The environment is added beside musl, which is the
other libc it already names.

Usage: target-lexicon-crate-llvmlibc.py CRATE_DIR...
Running it again on a crate it has already changed changes nothing.
"""
import hashlib
import json
import os
import re
import sys

REL = "src/targets.rs"

EDITS = [
    ("    Musl,\n",
     "    Musl,\n    LlvmLibc,\n"),
    ('            Musl => Cow::Borrowed("musl"),\n',
     '            Musl => Cow::Borrowed("musl"),\n'
     '            LlvmLibc => Cow::Borrowed("llvmlibc"),\n'),
    ('            "musl" => Musl,\n',
     '            "musl" => Musl,\n'
     '            "llvmlibc" => LlvmLibc,\n'),
]


def patch(crate):
    manifest = open(os.path.join(crate, "Cargo.toml")).read()
    if not re.search(r'^name = "target-lexicon"$', manifest, re.M):
        raise SystemExit("%s is not the target-lexicon crate" % crate)
    path = os.path.join(crate, REL)
    if not os.path.exists(path):
        return []
    text = open(path).read()
    if "LlvmLibc" in text:
        return []
    for anchor, replacement in EDITS:
        if anchor not in text:
            raise SystemExit("%s: no %r to follow" % (path, anchor.strip()))
        text = text.replace(anchor, replacement, 1)
    open(path, "w").write(text)
    checksums = os.path.join(crate, ".cargo-checksum.json")
    if os.path.exists(checksums):
        record = json.load(open(checksums))
        if record.get("files"):
            data = open(path, "rb").read()
            record["files"][REL] = hashlib.sha256(data).hexdigest()
            json.dump(record, open(checksums, "w"), separators=(",", ":"))
    return [REL]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for crate in sys.argv[1:]:
        touched = patch(crate)
        print("%s: %s" % (crate, ", ".join(touched) or "nothing changed"))


main()
