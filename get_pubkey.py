import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(
    "https://192.168.1.1/PLDTadminLogin", 
    headers={'User-Agent': 'Mozilla/5.0'}
)
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as res:
        html = res.read().decode('utf-8', errors='ignore')
        match = re.search(r'-----BEGIN PUBLIC KEY-----(.*?)-----END PUBLIC KEY-----', html, re.DOTALL)
        if match:
            pub_key = "-----BEGIN PUBLIC KEY-----\n" + match.group(1).strip() + "\n-----END PUBLIC KEY-----"
            print("[+] Found Public Key:")
            print(pub_key)
        else:
            print("[!] Searching external script files for public key...")
            scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            for s in scripts:
                script_url = "https://192.168.1.1" + (s if s.startswith('/') else '/' + s) if not s.startswith('http') else s
                try:
                    s_req = urllib.request.Request(script_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(s_req, context=ctx, timeout=5) as s_res:
                        s_content = s_res.read().decode('utf-8', errors='ignore')
                        s_match = re.search(r'-----BEGIN PUBLIC KEY-----(.*?)-----END PUBLIC KEY-----', s_content, re.DOTALL)
                        if s_match:
                            pub_key = "-----BEGIN PUBLIC KEY-----\n" + s_match.group(1).strip() + "\n-----END PUBLIC KEY-----"
                            print(f"[+] Found Public Key in script {script_url}:")
                            print(pub_key)
                            break
                except Exception:
                    pass
except Exception as e:
    print(f"Error: {e}")
