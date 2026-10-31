import subprocess
import datetime
import re
import os
import json
import socket

# ANSI Color Codes for Termux
C_BLUE = "\033[94m"
C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_CYAN = "\033[96m"
C_RESET = "\033[0m"

# External Storage Vault Path (Outside NetNavi directory)
VAULT_DIR = os.path.expanduser("~/.netnavi_storage")
os.makedirs(VAULT_DIR, exist_ok=True)

def get_network_info():
    node_ip = "127.0.0.1"
    gateway = "192.168.1.1"
    isp = "PLDT / Smart"
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        node_ip = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            res_ip = subprocess.run(["ip", "addr", "show", "wlan0"], capture_output=True, text=True, timeout=1)
            match_ip = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", res_ip.stdout)
            if match_ip:
                node_ip = match_ip.group(1)
        except Exception:
            pass

    try:
        res = subprocess.run(["ip", "route"], capture_output=True, text=True, timeout=1)
        match = re.search(r"via\s+(\d+\.\d+\.\d+\.\d+)", res.stdout)
        if match:
            gateway = match.group(1)
    except Exception:
        pass

    if node_ip != "127.0.0.1":
        subnet_prefix = ".".join(node_ip.split('.')[:3])
        if not gateway.startswith(subnet_prefix):
            if "192.168.100." in node_ip:
                gateway = "192.168.100.1"
            elif "192.168.254." in node_ip:
                gateway = "192.168.254.254"
            else:
                gateway = subnet_prefix + ".1"
    
    if "192.168.100." in node_ip or "192.168.100." in gateway:
        isp = "Globe Fiber (192.168.100.x)"
    elif "192.168.254." in node_ip or "192.168.254." in gateway:
        isp = "Globe Default (192.168.254.x)"
    elif "192.168.1." in node_ip or "192.168.0." in node_ip:
        isp = "PLDT / Smart"
    else:
        isp = f"Custom Gateway ({gateway.rsplit('.', 1)[0]}.x)"
        
    return node_ip, gateway, isp

def get_vault_filepath(gateway_ip):
    return os.path.join(VAULT_DIR, f"{gateway_ip.replace('.', '_')}.json")

def load_or_init_vault(gateway_ip):
    path = get_vault_filepath(gateway_ip)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                vault_data = json.load(f)
                # Migration check: if old format, upgrade to 4-slot structure automatically
                if "slots" not in vault_data:
                    vault_data["slots"] = {
                        "quick_router": {"type": vault_data.get("quick_scan_type", "None"), "results": vault_data.get("quick_results", []), "timestamp": vault_data.get("quick_timestamp", "")},
                        "quick_network": {"type": "None", "results": [], "timestamp": ""},
                        "deep_router": {"type": vault_data.get("deep_scan_type", "None"), "results": vault_data.get("deep_results", []), "timestamp": vault_data.get("deep_timestamp", "")},
                        "deep_network": {"type": "None", "results": [], "timestamp": ""}
                    }
                return vault_data
        except Exception:
            pass
            
    # Option B Immersive Prompt for new networks
    print(f"\n{C_GREEN}[!] New Network Gateway Detected ({gateway_ip}){C_RESET}")
    ssid_name = input("Awaiting Matrix Designation / SSID Name > ").strip() or f"Network_{gateway_ip}"
    
    vault_data = {
        "gateway": gateway_ip,
        "ssid_name": ssid_name,
        "slots": {
            "quick_router": {"type": "None", "results": [], "timestamp": ""},
            "quick_network": {"type": "None", "results": [], "timestamp": ""},
            "deep_router": {"type": "None", "results": [], "timestamp": ""},
            "deep_network": {"type": "None", "results": [], "timestamp": ""}
        }
    }
    save_vault(vault_data)
    print(f"{C_CYAN}[*] Profile '{ssid_name}' successfully bound to offline vault.{C_RESET}\n")
    return vault_data

def save_vault(data):
    path = get_vault_filepath(data["gateway"])
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[!] Error saving to offline vault: {e}")

def render_dashboard():
    node_ip, gateway, isp = get_network_info()
    vault_data = load_or_init_vault(gateway)
    print(f"[ NETNAVI v1.5 [Secured C2 Matrix] ]  -> [ Active Profile: {C_CYAN}{vault_data['ssid_name']} ({gateway}){C_RESET} ]\n")
    print(f"[*] System Time // {datetime.datetime.now().strftime('%H:%M:%S | %a, %b %d %Y')}")
    print("## WLAN Status (Live Sweep)")
    print(f" - Node IP Address     : {node_ip}")
    print(f" - Router Gateway      : {gateway}")
    print(f" - ISP Provider        : {isp}")
    print("\n## Interactive CLI")
    print(f" 1: {C_BLUE}Transcend{C_RESET} - This is Where the Magic Begins\n")

def run_and_store_scan(cmd_args, scan_name, slot_key):
    node_ip, gateway_ip, _ = get_network_info()
    vault_data = load_or_init_vault(gateway_ip)
    
    slot = vault_data["slots"][slot_key]
    if slot["results"]:
        print(f"\n{C_RED}[!] Scan logs already exist in slot '{slot_key}' for '{vault_data['ssid_name']}' (Scanned: {slot['timestamp']}){C_RESET}")
        choice = input(f"[*] Overwrite existing logs in slot '{slot_key}'? (y/n): ").strip().lower()
        if choice not in ["y", "yes"]:
            print(f"[*] Scan aborted. Preserving existing vault logs.\n")
            return

    print(f"\n[*] Running {scan_name}...\n")
    results = []
    try:
        process = subprocess.run(cmd_args, capture_output=True, text=True)
        lines = process.stdout.splitlines()
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("SF-"):
                continue
            if any(keyword in stripped for keyword in ["PORT", "/tcp", "/udp", "open", "closed", "filtered", "unrecognized", "Host is up", "Nmap scan report", "report"]):
                print(f" {line}")
                results.append(line)
        print()
        
        timestamp = datetime.datetime.now().strftime('%b %d, %Y - %H:%M:%S')
        slot["type"] = scan_name
        slot["results"] = results
        slot["timestamp"] = timestamp
            
        save_vault(vault_data)
        print(f"{C_CYAN}[*] Results permanently archived to slot '{slot_key}' in profile '{vault_data['ssid_name']}'{C_RESET}\n")
    except Exception as e:
        print(f"[!] Error executing scan: {e}\n")

render_dashboard()

while True:
    try:
        user_input = input("NetNavi > ").strip()
        lower_input = user_input.lower()
        
        if not user_input:
            continue
            
        if lower_input in ["exit", "quit"]:
            print("[*] Shutting down matrix session.")
            break
            
        elif lower_input in ["clear", "cls"]:
            subprocess.run(["clear"])
            render_dashboard()

        elif lower_input in ["wlan", "refresh", "status"]:
            print("\n[*] Re-sweeping WLAN interface and routing table...")
            render_dashboard()

        # SCANS
        elif lower_input in ["quick scan router", "router quick scan"]:
            gateway_ip = get_network_info()[1]
            cmd = ["nmap", "-F", "-T4", "-n", gateway_ip]
            run_and_store_scan(cmd, f"Quick Router Scan ({gateway_ip})", "quick_router")

        elif lower_input in ["quick scan", "quick scan network", "transcend", "1"]:
            node_ip, gateway_ip, _ = get_network_info()
            subnet_prefix = ".".join(node_ip.split('.')[:3]) + ".0/24"
            cmd = ["nmap", "-F", "-T4", "-n", subnet_prefix]
            run_and_store_scan(cmd, f"Quick Network-Wide Sweep ({subnet_prefix})", "quick_network")

        elif lower_input in ["deep scan router", "router deep scan"]:
            gateway_ip = get_network_info()[1]
            cmd = ["nmap", "-p-", "-sV", "-T4", gateway_ip]
            run_and_store_scan(cmd, f"Deep Router Scan ({gateway_ip})", "deep_router")

        elif lower_input in ["deep scan", "deep scan network"]:
            node_ip, gateway_ip, _ = get_network_info()
            subnet_prefix = ".".join(node_ip.split('.')[:3]) + ".0/24"
            cmd = ["nmap", "-p-", "-sV", "-T4", subnet_prefix]
            run_and_store_scan(cmd, f"Deep Network-Wide Sweep ({subnet_prefix})", "deep_network")

        # SHOW RESULTS (4 Decoupled Slots)
        elif lower_input in ["show quick router", "show quick scan router", "show router quick"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip)
            slot = vault_data["slots"]["quick_router"]
            print(f"\n{C_BLUE}========================================{C_RESET}")
            print(f"{C_BLUE}[*] QUICK ROUTER VAULT [{vault_data['ssid_name']}]: {slot['type']} ({slot['timestamp'] or 'No timestamp'}){C_RESET}")
            print(f"{C_BLUE}========================================{C_RESET}")
            if slot["results"]:
                for res in slot["results"]:
                    print(f" {res}")
            else:
                print(" [!] No quick router records found.")
            print(f"{C_BLUE}========================================{C_RESET}\n")

        elif lower_input in ["show quick network", "show quick scan", "show network quick"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip)
            slot = vault_data["slots"]["quick_network"]
            print(f"\n{C_BLUE}========================================{C_RESET}")
            print(f"{C_BLUE}[*] QUICK NETWORK VAULT [{vault_data['ssid_name']}]: {slot['type']} ({slot['timestamp'] or 'No timestamp'}){C_RESET}")
            print(f"{C_BLUE}========================================{C_RESET}")
            if slot["results"]:
                for res in slot["results"]:
                    print(f" {res}")
            else:
                print(" [!] No quick network records found.")
            print(f"{C_BLUE}========================================{C_RESET}\n")

        elif lower_input in ["show deep router", "show deep scan router", "show router deep"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip)
            slot = vault_data["slots"]["deep_router"]
            print(f"\n{C_BLUE}========================================{C_RESET}")
            print(f"{C_BLUE}[*] DEEP ROUTER VAULT [{vault_data['ssid_name']}]: {slot['type']} ({slot['timestamp'] or 'No timestamp'}){C_RESET}")
            print(f"{C_BLUE}========================================{C_RESET}")
            if slot["results"]:
                for res in slot["results"]:
                    print(f" {res}")
            else:
                print(" [!] No deep router records found.")
            print(f"{C_BLUE}========================================{C_RESET}\n")

        elif lower_input in ["show deep network", "show deep scan", "show network deep"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip)
            slot = vault_data["slots"]["deep_network"]
            print(f"\n{C_BLUE}========================================{C_RESET}")
            print(f"{C_BLUE}[*] DEEP NETWORK VAULT [{vault_data['ssid_name']}]: {slot['type']} ({slot['timestamp'] or 'No timestamp'}){C_RESET}")
            print(f"{C_BLUE}========================================{C_RESET}")
            if slot["results"]:
                for res in slot["results"]:
                    print(f" {res}")
            else:
                print(" [!] No deep network records found.")
            print(f"{C_BLUE}========================================{C_RESET}\n")

        # GRANULAR DELETION / PURGE COMMANDS
        elif lower_input in ["delete quick router", "clear quick router"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip)
            vault_data["slots"]["quick_router"] = {"type": "None", "results": [], "timestamp": ""}
            save_vault(vault_data)
            print(f"{C_GREEN}[*] Quick Router slot cleared successfully.{C_RESET}\n")

        elif lower_input in ["delete quick network", "clear quick network", "delete quick scan"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip)
            vault_data["slots"]["quick_network"] = {"type": "None", "results": [], "timestamp": ""}
            save_vault(vault_data)
            print(f"{C_GREEN}[*] Quick Network slot cleared successfully.{C_RESET}\n")

        elif lower_input in ["delete deep router", "clear deep router"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip)
            vault_data["slots"]["deep_router"] = {"type": "None", "results": [], "timestamp": ""}
            save_vault(vault_data)
            print(f"{C_GREEN}[*] Deep Router slot cleared successfully.{C_RESET}\n")

        elif lower_input in ["delete deep network", "clear deep network", "delete deep scan"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip)
            vault_data["slots"]["deep_network"] = {"type": "None", "results": [], "timestamp": ""}
            save_vault(vault_data)
            print(f"{C_GREEN}[*] Deep Network slot cleared successfully.{C_RESET}\n")

        elif lower_input in ["purge vault", "delete profile"]:
            gateway_ip = get_network_info()[1]
            path = get_vault_filepath(gateway_ip)
            if os.path.exists(path):
                os.remove(path)
                print(f"{C_RED}[*] Entire offline profile for gateway {gateway_ip} deleted from vault.{C_RESET}\n")
            else:
                print(" [!] No profile file found to purge.")

        # IMMERSIVE SCI-FI TARGET JUMP & HYDRA WORKFLOW
        elif lower_input in ["jump", "audit", "crack"]:
            gateway_ip = get_network_info()[1]
            
            print(f"\n{C_GREEN}[*] Found Target Cache to Connect{C_RESET}")
            target_ip = input("Awaiting Target to Jump > ").strip() or gateway_ip
            target_port = input("Choose your Poison (Port e.g. 80, 21) > ").strip()
            
            username = input("Enter target username (default 'admin'): ").strip() or "admin"
            wordlist = input("Enter path to wordlist (default 'wordlists/rockyou.txt'): ").strip() or "wordlists/rockyou.txt"
            
            if not os.path.exists(wordlist):
                print(f"[!] Warning: Wordlist '{wordlist}' not found. Check path inside your wordlists dir.")
            
            print(f"\n{C_BLUE}[*] Jacking into target {target_ip}:{target_port} with user '{username}'...{C_RESET}")
            
            if target_port == "80":
                hydra_cmd = ["hydra", "-l", username, "-P", wordlist, target_ip, "http-get", "/index.html", "-t", "4"]
            elif target_port == "21":
                hydra_cmd = ["hydra", "-l", username, "-P", wordlist, f"ftp://{target_ip}", "-t", "4"]
            else:
                hydra_cmd = ["hydra", "-l", username, "-P", wordlist, target_ip, "-t", "4"]
                
            try:
                subprocess.run(hydra_cmd)
                print(f"\n{C_GREEN}[*] Audit routine finished.{C_RESET}\n")
            except Exception as e:
                print(f"[!] Execution error: {e}\n")
                
        else:
            print(f"Hello. How can I assist?\n")
            
    except KeyboardInterrupt:
        print("\n[*] Session interrupted.")
        break
