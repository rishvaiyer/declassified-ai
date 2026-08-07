#!/usr/bin/env python3
"""Rebuild ../index.html by inlining the datasets into the template.
Run the pipeline in order:  crunch.py  ->  embed.py  ->  build.py
(crunch + embed expect a shallow clone of CL4R1T4S in this folder.)"""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
def js_safe(json_text):
    """Make already-valid JSON safe to inline inside a <script> tag.
    '<' -> '\\u003c' keeps </script>, <!--, etc. from ending the script early;
    the escapes are valid JSON and parse straight back to the original chars."""
    return (json_text.replace("<", "\\u003c").replace(">", "\\u003e")
                     .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))

tpl = open(os.path.join(HERE, "page.template.html")).read()
tpl = tpl.replace("__DATA__",  js_safe(open(os.path.join(ROOT, "data", "data.json")).read()))
tpl = tpl.replace("__TEXTS__", js_safe(open(os.path.join(ROOT, "data", "texts.json")).read()))
out = os.path.join(ROOT, "index.html")
open(out, "w").write(tpl)
print(f"built {out}  ({os.path.getsize(out)/1e6:.2f} MB)")
