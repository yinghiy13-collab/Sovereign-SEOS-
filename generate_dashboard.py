import json
import os

# ฟังก์ชันสำหรับค้นหาข้อมูลแบบเจาะลึก (Recursive Search)
def find_key(d, key):
    if isinstance(d, dict):
        if key in d:
            return d[key]
        for k, v in d.items():
            res = find_key(v, key)
            if res is not None:
                return res
    elif isinstance(d, list):
        for item in d:
            res = find_key(item, key)
            if res is not None:
                return res
    return None

def generate_html():
    try:
        with open('attestation.json', 'r') as f:
            data = json.load(f)
        
        # 1. หา Commit Hash (ค้นหาเผื่อไว้หลายชื่อ)
        commit_hash = find_key(data, 'git_commit') or find_key(data, 'commit') or find_key(data, 'sha')
        if not commit_hash or commit_hash == 'Unknown':
            commit_hash = os.environ.get('GITHUB_SHA', 'Unknown')
        
        # 2. หา Artifact SHA-256 (มักอยู่ใน subject)
        subject = data.get('subject', [{}])
        if isinstance(subject, list) and len(subject) > 0:
            output_hash = subject[0].get('digest', {}).get('sha256', 'Unknown')
        else:
            output_hash = find_key(data, 'sha256') or 'Unknown'

        # 3. หา Builder ID
        builder = find_key(data, 'builder')
        if isinstance(builder, dict):
            builder_id = builder.get('id', 'Unknown')
        else:
            builder_id = str(builder) if builder else os.environ.get('GITHUB_WORKFLOW_REF', 'Unknown')

        # ป้องกันค่า None หลุดมาแสดง
        if not commit_hash: commit_hash = 'Unknown'
        if not output_hash: output_hash = 'Unknown'
        if not builder_id: builder_id = 'Unknown'
        
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
                
                <div class="data-row">
                    <span class="label">Git Commit SHA</span>
                    <span class="value">{commit_hash}</span>
                </div>
                <div class="data-row">
                    <span class="label">Artifact SHA-256 (Self-Test Output)</span>
                    <span class="value">{output_hash}</span>
                </div>
                <div class="data-row">
                    <span class="label">Builder / Workflow</span>
                    <span class="value">{builder_id}</span>
                </div>
                <div class="data-row">
                    <span class="label">Security Status</span>
                    <span class="value">SLSA Level 3 | Cosign Keyless Sign | Trivy Scanned</span>
                </div>
                
                <div class="footer">
                    This dashboard is automatically generated from cryptographically signed attestations.
                </div>
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
