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
        print(f"Total HTML length: {len(html)}")
        matches = re.findall(r'.{0,50}token.{0,50}', html, re.IGNORECASE)
        print(f"Found {len(matches)} matches for 'token':")
        for m in matches[:10]:
            print(f"  -> {m.strip()}")
except Exception as e:
    print(f"Error: {e}")
