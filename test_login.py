import urllib.request
import urllib.parse
import http.cookiejar
import ssl
import re

base_url = "https://192.168.1.1"
login_url = f"{base_url}/PLDTadminLogin"
token_url = f"{base_url}/?_type=loginData&_tag=login_token"

username = "adminpldt"
password = "Bulanit101"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cj),
    urllib.request.HTTPSHandler(context=ctx)
)

# 1. Get token
req = urllib.request.Request(
    token_url, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': login_url
    }
)
with opener.open(req, timeout=10) as res:
    content = res.read().decode('utf-8', errors='ignore')
    match = re.search(r'<ajax_response_xml_root>(.*?)</ajax_response_xml_root>', content)
    token = match.group(1).strip() if match else None

print(f"[*] Fetched Token: {token}")

# 2. Submit login
post_data = urllib.parse.urlencode({
    '_sessionTOKEN': token,
    'username': username,
    'password': password
}).encode('utf-8')

req = urllib.request.Request(
    login_url, 
    data=post_data, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36', 
        'Referer': login_url,
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest'
    }
)

with opener.open(req, timeout=10) as res:
    print(f"[*] Response URL: {res.url}")
    print(f"[*] Response Status: {res.status}")
    body = res.read().decode('utf-8', errors='ignore')
    print(f"[*] Response Body:\n{body[:500]}")
    print(f"[*] Cookies: {[c.name + '=' + c.value for c in cj]}")
