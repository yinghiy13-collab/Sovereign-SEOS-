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
