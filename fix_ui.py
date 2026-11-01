with open("hub.py", "r") as f:
    code = f.read()

# Replace the bulky recon dashboard render with the clean original layout
old_dashboard = """    print(f"[ NETNAVI v2.0 [Network Recon Matrix] ]  -> [ Active Profile: {C_CYAN}{vault_data['ssid_name']} ({gateway}){C_RESET} ]\\n")
    print(f"[*] System Time // {datetime.datetime.now().strftime('%H:%M:%S | %a, %b %d %Y')}")
    print("## WLAN Status (Live Sweep)")
    print(f" - Node IP Address     : {node_ip}")
    print(f" - Router Gateway      : {gateway}")
    print(f" - ISP Provider        : {isp}")
    
    print("\\n## NetNavi Resources")
    print(f" - RAM     : {C_GREEN}{ram_str}{C_RESET}")
    print(f" - Storage : {C_GREEN}{storage_str}{C_RESET}")
    
    print("\\n## Recon Commands")
    print(f" 1: {C_BLUE}quick scan router{C_RESET}  - Fast Nmap scan on Gateway")
    print(f" 2: {C_BLUE}quick scan network{C_RESET} - Fast Subnet-wide Sweep")
    print(f" 3: {C_BLUE}deep scan router{C_RESET}   - Full Port & Service Scan on Gateway")
    print(f" 4: {C_BLUE}deep scan network{C_RESET}  - Full Subnet Enumeration")
    print(f" Type {C_CYAN}help{C_RESET} for a full list of vault and recon commands.\\n")"""

new_dashboard = """    print(f"[ NETNAVI v2.0 ]  -> [ Active Profile: {C_CYAN}{vault_data['ssid_name']} ({gateway}){C_RESET} ]\\n")
    print(f"[*] System Time // {datetime.datetime.now().strftime('%H:%M:%S | %a, %b %d %Y')}")
    print("## WLAN Status (Live Sweep)")
    print(f" - Node IP Address     : {node_ip}")
    print(f" - Router Gateway      : {gateway}")
    print(f" - ISP Provider        : {isp}")
    
    print("\\n## NetNavi Resources")
    print(f" - RAM     : {C_GREEN}{ram_str}{C_RESET}")
    print(f" - Storage : {C_GREEN}{storage_str}{C_RESET}")
    
    print("\\n## Interactive CLI")
    print(f" 1: Transcend - This is Where the Magic Begins\\n")"""

if old_dashboard in code:
    code = code.replace(old_dashboard, new_dashboard)
    with open("hub.py", "w") as f:
        f.write(code)
    print("[+] Successfully restored your original clean dashboard UI!")
else:
    print("[!] Dashboard block already modified or not found.")
