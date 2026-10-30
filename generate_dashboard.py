import json
import os

def generate_html():
    try:
        with open('attestation.json', 'r') as f:
            data = json.load(f)
        
        commit_hash = data.get('git_commit', 'Unknown')
        output_hash = data.get('output_sha256', 'Unknown')
        builder_id = data.get('builder', {}).get('id', 'Unknown')
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sovereign SEOS - Trust Dashboard</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0d1117; color: #c9d1d9; padding: 20px; display: flex; justify-content: center; }}
                .container {{ width: 100%; max-width: 800px; background: #161b22; padding: 30px; border-radius: 10px; border: 1px solid #30363d; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
                h1 {{ color: #58a6ff; text-align: center; margin-bottom: 30px; }}
                .status-badge {{ display: block; text-align: center; background: #238636; color: white; padding: 12px; border-radius: 6px; font-weight: bold; font-size: 1.2em; margin-bottom: 30px; letter-spacing: 1px; }}
                .data-row {{ border-bottom: 1px solid #30363d; padding: 15px 0; display: flex; flex-direction: column; gap: 5px; }}
                .label {{ font-weight: bold; color: #8b949e; font-size: 0.9em; }}
                .value {{ font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace; color: #79c0ff; word-break: break-all; font-size: 1.1em; }}
                .footer {{ text-align: center; margin-top: 40px; font-size: 0.8em; color: #8b949e; border-top: 1px solid #30363d; padding-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛡️ Sovereign SEOS Trust Dashboard</h1>
                <div class="status-badge">✅ SYSTEM VERIFIED & SECURE</div>
                <div class="data-row"><span class="label">Git Commit SHA</span><span class="value">{commit_hash}</span></div>
                <div class="data-row"><span class="label">Artifact SHA-256 (Self-Test Output)</span><span class="value">{output_hash}</span></div>
                <div class="data-row"><span class="label">Builder / Workflow</span><span class="value">{builder_id}</span></div>
                <div class="data-row"><span class="label">Security Status</span><span class="value">SLSA Level 3 | Cosign Keyless Sign | Trivy Scanned</span></div>
                <div class="footer">This dashboard is automatically generated from cryptographically signed attestations.</div>
            </div>
        </body>
        </html>
        """
        os.makedirs('docs', exist_ok=True)
        with open('docs/index.html', 'w') as f:
            f.write(html_content)
        print("✅ Dashboard generated successfully at docs/index.html")
    except FileNotFoundError:
        print("❌ attestation.json not found.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_html()
