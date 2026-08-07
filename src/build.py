#!/usr/bin/env python3
"""Rebuild ../index.html by inlining the datasets into the template.
Run the pipeline in order:  crunch.py  ->  embed.py  ->  build.py
(crunch + embed expect a shallow clone of CL4R1T4S in this folder.)"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
tpl = open(os.path.join(HERE, "page.template.html")).read()
tpl = tpl.replace("__DATA__",  open(os.path.join(ROOT, "data", "data.json")).read())
tpl = tpl.replace("__TEXTS__", open(os.path.join(ROOT, "data", "texts.json")).read())
out = os.path.join(ROOT, "index.html")
open(out, "w").write(tpl)
print(f"built {out}  ({os.path.getsize(out)/1e6:.2f} MB)")
