# 🛡️ Sovereign SEOS (Software Engineering Operating System)

![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen)
![Security Level](https://img.shields.io/badge/SLSA-Level%203-blue)
![Zero-Trust](https://img.shields.io/badge/Security-Zero--Trust-red)

**Sovereign SEOS** is a highly secure, self-verifying software supply chain pipeline built on GitHub Actions. It implements **Zero-Trust principles** and **Keyless Cryptographic Signing** to ensure absolute code and test integrity.

## 🏗️ Architecture & Security Flow

This repository enforces a strict 4-pillar security model:

1. **Code Integrity**: Every execution generates a unique SHA-256 hash of the source code (`seos.py`).
2. **Test Integrity**: All self-tests must pass, and the results are hashed (`output_sha256`).
3. **Identity Integrity**: The pipeline utilizes **Sigstore/Cosign Keyless Signing**. The generated certificate proves that this specific artifact was built by *this exact GitHub Actions workflow* and *this exact commit*, eliminating the need to manage long-lived private keys.
4. **Continuous Verification**: The pipeline includes a built-in `Verify attestation` step. If the signature or the identity in the certificate does not match the expected constraints (e.g., wrong branch, wrong repo, tampered files), the build fails immediately.

## 📦 Artifacts Generated

Upon a successful run, the pipeline produces two critical files:
*   `attestation.json`: Contains metadata, source hashes, and test results.
*   `attestation.sigstore.json`: The cryptographic bundle containing the signature and the short-lived Fulcio certificate.

## 🔍 How to Verify (Trust, but Verify)

You can independently verify the authenticity of the generated artifacts offline using `cosign`. 

Run the following command in your terminal:

```bash
cosign verify-blob \
  --bundle attestation.sigstore.json \
  --certificate-identity 'https://github.com/yinghiy13-collab/Sovereign-SEOS-/.github/workflows/seos-runner.yml@refs/heads/main' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  attestation.json
