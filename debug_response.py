import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

token_url = "https://192.168.1.1/?_type=loginData&_tag=login_token"
req = urllib.request.Request(token_url, headers={'User-Agent': 'Mozilla/5.0', 'X-Requested-With': 'XMLHttpRequest'})

try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as res:
        print(f"Status: {res.status}")
        content = res.read().decode('utf-8', errors='ignore')
        print(f"Response Content:\n{content}")
except Exception as e:
    print(f"Error: {e}")
