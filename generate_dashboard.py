##### FILE: generate_dashboard.py
#!/usr/bin/env python3
"""Generate docs/index.html from attestation.json.

Shows only what the attestation records (build-time self-test of seos.py).
Fails the CI step if attestation.json is missing or unreadable.
"""
import html
import json
import os
import sys

CSS = """body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:20px;display:flex;justify-content:center}
.c{width:100%;max-width:800px;background:#161b22;padding:30px;border-radius:10px;border:1px solid #30363d}
h1{color:#58a6ff;text-align:center;margin-bottom:30px}
.badge{display:block;text-align:center;color:#fff;padding:12px;border-radius:6px;font-weight:bold;font-size:1.2em;margin-bottom:10px}
.ok{background:#238636}.bad{background:#da3633}
.note{text-align:center;color:#8b949e;font-size:.9em;margin-bottom:30px}
.row{border-bottom:1px solid #30363d;padding:15px 0;display:flex;flex-direction:column;gap:5px}
.l{font-weight:bold;color:#8b949e;font-size:.9em}
.v{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:#79c0ff;word-break:break-all}
.f{text-align:center;margin-top:40px;font-size:.8em;color:#8b949e;border-top:1px solid #30363d;padding-top:20px}"""


def known(*values):
    """First value that is set and not a placeholder."""
    for v in values:
        if v and v not in ("unknown", "local"):
            return str(v)
    return "unknown"


def main():
    try:
        with open("attestation.json", encoding="utf-8") as f:
            att = json.load(f)
    except (OSError, ValueError) as e:
        print(f"attestation.json unreadable: {e}", file=sys.stderr)
        return 1

    pred = att.get("predicate", {})
    result = pred.get("result", {})
    inv = pred.get("invocation", {})
    builder = pred.get("builder", {})
    subject = (att.get("subject") or [{}])[0]

    passed = result.get("passed") is True
    rows = [
        ("Git commit", known(inv.get("git_commit"), builder.get("sha"),
                             os.environ.get("GITHUB_SHA"))),
        ("seos.py SHA-256", known(subject.get("digest", {}).get("sha256"))),
        ("Self-test output SHA-256", known(result.get("output_sha256"))),
        ("Self-test exit code", known(str(result.get("exit_code", "")))),
        ("Builder / workflow", known(builder.get("id"),
                                     os.environ.get("GITHUB_WORKFLOW_REF"))),
        ("Run ID", known(builder.get("run_id"), os.environ.get("GITHUB_RUN_ID"))),
        ("Timestamp (UTC)", known(inv.get("timestamp"))),
    ]
    rows_html = "".join(
        f'<div class="row"><span class="l">{html.escape(k)}</span>'
        f'<span class="v">{html.escape(v)}</span></div>'
        for k, v in rows
    )
    cls, text = ("ok", "SELF-TEST PASSED") if passed else ("bad", "SELF-TEST FAILED")

    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sovereign SEOS - Build Record</title><style>{CSS}</style></head>
<body><div class="c">
<h1>Sovereign SEOS Build Record</h1>
<div class="badge {cls}">{text}</div>
<div class="note">Build-time self-test of seos.py only. Not a security audit.</div>
{rows_html}
<div class="row"><span class="l">Checks run before this page was built</span>
<span class="v">Cosign keyless signature verified | Trivy scan (known, fixable HIGH/CRITICAL) | No SLSA level claimed</span></div>
<div class="f">Generated from attestation.json by the workflow. See the README section "What this does NOT prove".</div>
</div></body></html>"""

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(page)
    print("Dashboard written to docs/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())

##### FILE: SECURITY.md
# Security Policy

## Supported versions

Only the latest release is supported. Older releases do not receive fixes.
Release v1.0.2 has no attestation; use v1.0.3 or later.

## Scope

This project is a small Python script with a CI pipeline that signs a record
of its own self-test. Security reports are welcome for:

- the release and runner workflows (`.github/workflows/`)
- the attestation format and verification instructions
- `seos.py` and `generate_dashboard.py`

Runtime security of anything built on top of this project is out of scope.

## Reporting a vulnerability

Use the "Report a vulnerability" button on this repository's Security tab
(private vulnerability reporting). Please do not open a public issue with
details.

This is maintained by one person. Expect a first reply on a best-effort basis;
there is no guaranteed response time. Accepted reports are fixed in a new
release and credited unless you ask otherwise.

##### FILE: README.md  (APPLY AS 2 EDITS, do not replace the whole file)
EDIT 1 - badge. Replace the 3-line block ("[", the badge image, "](https://...seos-runner.yml)") with this single line:
[

![Sovereign SEOS Runner](https://github.com/yinghiy13-collab/Sovereign-SEOS-/actions/workflows/seos-runner.yml/badge.svg)

](https://github.com/yinghiy13-collab/Sovereign-SEOS-/actions/workflows/seos-runner.yml)

EDIT 2 - under "Verify a release", replace:
grep sha256 attestation.json
with:
grep '"sha256"' attestation.json
