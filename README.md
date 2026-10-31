# Sovereign SEOS

A small Python project with a CI pipeline that tests itself, signs a record of the result, and publishes that record with each release.

[

[

![Sovereign SEOS Runner](https://github.com/yinghiy13-collab/Sovereign-SEOS-/actions/workflows/seos-runner.yml/badge.svg)

](https://github.com/yinghiy13-collab/Sovereign-SEOS-/actions/workflows/seos-runner.yml)

## What the pipeline does

On every tagged release (`v*`), `release.yml` runs:

1. Self-test (`python3 seos.py self`)
2. Trivy filesystem scan (fails the job on HIGH or CRITICAL findings that have a fix available)
3. Generates `attestation.json` (hash of `seos.py`, test result, commit, workflow identity)
4. Signs it with Sigstore keyless signing (`cosign sign-blob`)
5. Verifies its own signature, then publishes the files to the GitHub release

Release assets: `attestation.json`, `attestation.sigstore.json`, `seos.py`.

## What this proves

- `attestation.json` was signed by this repository's `release.yml` workflow, running from the release tag.
- `attestation.json` has not been modified since signing.
- The `sha256` of `seos.py` recorded in it can be compared with the `seos.py` attached to the release.

## What this does NOT prove

- **The code is safe.** Trivy only reports known, fixable vulnerabilities. It does not review logic.
- **A second person reviewed it.** The `main` branch requires a pull request and passing checks, but required approvals is set to 0.
- **The build environment is hardened.** Builds run on GitHub-hosted runners. No SLSA level is claimed.
- **Third-party actions are immutable.** Workflow actions are referenced by version tag, not commit SHA (planned improvement).
- **Privacy.** Sigstore keyless signing writes the repository name and workflow identity to the public Rekor transparency log.
- **Runtime security.** Everything above applies to build time only.

Release `v1.0.2` has no attestation. Use `v1.0.3` or later.

## Verify a release

Requires [cosign](https://github.com/sigstore/cosign). Replace `v1.0.3` with the release you want.

```bash
TAG=v1.0.3
BASE=https://github.com/yinghiy13-collab/Sovereign-SEOS-/releases/download/$TAG
curl -sLO $BASE/attestation.json
curl -sLO $BASE/attestation.sigstore.json
curl -sLO $BASE/seos.py

cosign verify-blob \
  --bundle attestation.sigstore.json \
  --certificate-identity "https://github.com/yinghiy13-collab/Sovereign-SEOS-/.github/workflows/release.yml@refs/tags/$TAG" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  attestation.json

sha256sum seos.py
grep '"sha256"' attestation.json
```

Expected: `Verified OK`, and the two hashes match.

## Repository protections

`main` is protected by a ruleset: pull request required, checks `run` and `Analyze (python)` must pass, branches must be up to date, force pushes and deletions blocked, and the bypass list is empty. Tags are not yet protected.

## Security

See [SECURITY.md](SECURITY.md).
