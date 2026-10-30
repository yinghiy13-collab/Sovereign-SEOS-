# 🛡️ Sovereign SEOS (Software Engineering Operating System)

![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen)
![Security Level](https://img.shields.io/badge/SLSA-Level%203-blue)
![Zero-Trust](https://img.shields.io/badge/Security-Zero--Trust-red)
![License](https://img.shields.io/badge/License-MIT-green)

**Sovereign SEOS** is a highly secure, self-verifying software supply chain pipeline built on GitHub Actions. It implements **Zero-Trust principles** and **Keyless Cryptographic Signing** using Sigstore to ensure absolute code, test, and build integrity.

## 🏗️ Architecture & Security Flow

This repository enforces a strict 4-pillar security model:

1. **Code Integrity**: Every execution generates a unique SHA-256 hash of the source code (`seos.py`).
2. **Test Integrity**: All self-tests must pass, and the results are hashed (`output_sha256`).
3. **Identity Integrity**: The pipeline utilizes **Sigstore/Cosign Keyless Signing**. The generated certificate proves that this specific artifact was built by *this exact GitHub Actions workflow* and *this exact commit*, eliminating the need to manage long-lived private keys.
4. **Continuous Verification**: The pipeline includes a built-in `Verify attestation` step. If the signature or the identity in the certificate does not match the expected constraints (e.g., wrong branch, wrong repo, tampered files), the build fails immediately.

## 📦 Artifacts & Daily Health Checks

Upon a successful run, the pipeline produces two critical files as downloadable artifacts:
*   `attestation.json`: Contains metadata, source hashes, and test results.
*   `attestation.sigstore.json`: The cryptographic bundle containing the signature and the short-lived Fulcio certificate.

> ⏰ **Automated Daily Run:** This workflow is scheduled to run automatically every day at 00:00 ICT (17:00 UTC) to perform continuous health checks and ensure the integrity of the system over time.

## 🔍 How to Verify (Trust, but Verify)

You can independently verify the authenticity of the generated artifacts offline using `cosign`. 

1. Download the artifacts (`attestation.json` and `attestation.sigstore.json`) from a recent workflow run.
2. Install [Cosign](https://docs.sigstore.dev/cosign/installation/).
3. Run the following command:

```bash
cosign verify-blob \
  --bundle attestation.sigstore.json \
  --certificate-identity 'https://github.com/yinghiy13-collab/Sovereign-SEOS-/.github/workflows/seos-runner.yml@refs/heads/main' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  attestation.json
