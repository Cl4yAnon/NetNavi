import subprocess
import datetime
import re
import os
import json
import socket
import sys
import math

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ANSI Color Codes for Termux
C_BLUE = "\033[94m"
C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_CYAN = "\033[96m"
C_RESET = "\033[0m"

# External Storage Vault Path & Registry File
VAULT_DIR = os.path.expanduser("~/.netnavi_storage")
os.makedirs(VAULT_DIR, exist_ok=True)
REGISTRY_FILE = "nodes_registry.json"

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

def get_vault_filepath(gateway_ip, ssid_name):
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', ssid_name)
    return os.path.join(VAULT_DIR, f"{gateway_ip.replace('.', '_')}_{safe_name}.json")

def load_nodes_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}

def save_nodes_registry(registry):
    try:
        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry, f, indent=4)
    except Exception as e:
        print(f"[!] Error saving nodes registry: {e}")

def resolve_active_ssid(gateway_ip):
    """Handles the once-per-session SSID prompt workflow."""
    registry = load_nodes_registry()
    gateway_data = registry.get(gateway_ip, {"ssids": []})
    existing_ssids = gateway_data.get("ssids", [])

    selected_ssid = ""

    if existing_ssids:
        print(f"\n{C_GREEN}[?] Gateway Recognized: {gateway_ip}{C_RESET}")
        is_new = input("Are you new to this SSID? (y/n): ").strip().lower()
        
        if is_new in ["y", "yes"]:
            selected_ssid = prompt_new_ssid_entry(gateway_ip, existing_ssids, registry)
        else:
            print("\nSelect an existing SSID profile:")
            for idx, ssid in enumerate(existing_ssids, 1):
                print(f"  {C_CYAN}{idx}){C_RESET} {ssid}")
            
            choice = input(f"\nNetNavi > Select [1-{len(existing_ssids)}]: ").strip()
            try:
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(existing_ssids):
                    selected_ssid = existing_ssids[choice_idx - 1]
                    print(f"{C_CYAN}[+] Loaded Profile: {selected_ssid}{C_RESET}\n")
            except ValueError:
                pass
            
            if not selected_ssid:
                selected_ssid = existing_ssids[0]
                print(f"{C_RED}[!] Invalid choice. Defaulting to: {selected_ssid}{C_RESET}\n")
    else:
        print(f"\n{C_GREEN}[!] New or Unregistered Gateway Detected ({gateway_ip}){C_RESET}")
        selected_ssid = prompt_new_ssid_entry(gateway_ip, [], registry)

    return selected_ssid

def load_or_init_vault(gateway_ip, active_ssid):
    path = get_vault_filepath(gateway_ip, active_ssid)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                vault_data = json.load(f)
                if "slots" in vault_data:
                    return vault_data
        except Exception:
            pass

    vault_data = {
        "gateway": gateway_ip,
        "ssid_name": active_ssid,
        "slots": {
            "quick_router": {"type": "None", "results": [], "timestamp": ""},
            "quick_network": {"type": "None", "results": [], "timestamp": ""},
            "deep_router": {"type": "None", "results": [], "timestamp": ""},
            "deep_network": {"type": "None", "results": [], "timestamp": ""}
        }
    }
    save_vault(vault_data)
    return vault_data

def prompt_new_ssid_entry(gateway_ip, existing_ssids, registry):
    new_ssid = input("Enter a Brand New SSID Name > ").strip()
    if not new_ssid:
        new_ssid = f"GATEWAY_{gateway_ip.replace('.', '_')}"
    
    if new_ssid not in existing_ssids:
        existing_ssids.append(new_ssid)

    registry[gateway_ip] = {"ssids": existing_ssids}
    save_nodes_registry(registry)
    print(f"{C_CYAN}[*] Profile '{new_ssid}' successfully bound and registered.{C_RESET}\n")
    return new_ssid

def save_vault(data):
    path = get_vault_filepath(data["gateway"], data["ssid_name"])
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[!] Error saving to offline vault: {e}")

def get_dir_size(path='.'):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass
    except Exception:
        pass
    return total_size

def format_size(size_bytes):
    if size_bytes == 0:
        return "0.00 KB"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_netnavi_resource_usage():
    ram_usage_bytes = 0
    if PSUTIL_AVAILABLE:
        try:
            proc = psutil.Process(os.getpid())
            ram_usage_bytes = proc.memory_info().rss
        except Exception:
            pass
    else:
        try:
            with open(f"/proc/{os.getpid()}/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        parts = line.split()
                        if len(parts) >= 2:
                            ram_usage_bytes = int(parts[1]) * 1024
                            break
        except Exception:
            pass

    workspace_path = os.path.dirname(os.path.abspath(__file__))
    storage_usage_bytes = get_dir_size(workspace_path)
    return ram_usage_bytes, storage_usage_bytes

def render_dashboard(active_ssid):
    node_ip, gateway, isp = get_network_info()
    vault_data = load_or_init_vault(gateway, active_ssid)
    
    ram_bytes, storage_bytes = get_netnavi_resource_usage()
    ram_str = format_size(ram_bytes)
    storage_str = format_size(storage_bytes)

    print(f"[ NETNAVI v1.5 [Secured C2 Matrix] ]  -> [ Active Profile: {C_CYAN}{vault_data['ssid_name']} ({gateway}){C_RESET} ]\n")
    print(f"[*] System Time // {datetime.datetime.now().strftime('%H:%M:%S | %a, %b %d %Y')}")
    print("## WLAN Status (Live Sweep)")
    print(f" - Node IP Address     : {node_ip}")
    print(f" - Router Gateway      : {gateway}")
    print(f" - ISP Provider        : {isp}")
    
    print("\n## NetNavi Resources")
    print(f" - RAM     : {C_GREEN}{ram_str}{C_RESET}")
    print(f" - Storage : {C_GREEN}{storage_str}{C_RESET}")
    
    print("\n## Interactive CLI")
    print(f" 1: {C_BLUE}Transcend{C_RESET} - This is Where the Magic Begins\n")

def run_and_store_scan(cmd_args, scan_name, slot_key, active_ssid):
    node_ip, gateway_ip, _ = get_network_info()
    vault_data = load_or_init_vault(gateway_ip, active_ssid)
    
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

# --- INITIAL BOOT SEQUENCE ---
node_ip_init, gateway_init, _ = get_network_info()
CURRENT_SSID = resolve_active_ssid(gateway_init)

subprocess.run(["clear"])
render_dashboard(CURRENT_SSID)

while True:
    try:
        user_input = input("NetNavi > ").strip()
        lower_input = user_input.lower()
        
        if not user_input:
            subprocess.run(["clear"])
            render_dashboard(CURRENT_SSID)
            continue
            
        if lower_input in ["exit", "quit"]:
            print("[*] Shutting down matrix session.")
            break
            
        elif lower_input in ["clear", "cls"]:
            subprocess.run(["clear"])
            render_dashboard(CURRENT_SSID)

        elif lower_input in ["wlan", "refresh", "status"]:
            print("\n[*] Re-sweeping WLAN interface and routing table...")
            subprocess.run(["clear"])
            render_dashboard(CURRENT_SSID)

        # SCANS
        elif lower_input in ["quick scan router", "router quick scan"]:
            gateway_ip = get_network_info()[1]
            cmd = ["nmap", "-F", "-T4", "-n", gateway_ip]
            run_and_store_scan(cmd, f"Quick Router Scan ({gateway_ip})", "quick_router", CURRENT_SSID)

        elif lower_input in ["quick scan", "quick scan network", "transcend", "1"]:
            node_ip, gateway_ip, _ = get_network_info()
            subnet_prefix = ".".join(node_ip.split('.')[:3]) + ".0/24"
            cmd = ["nmap", "-F", "-T4", "-n", subnet_prefix]
            run_and_store_scan(cmd, f"Quick Network-Wide Sweep ({subnet_prefix})", "quick_network", CURRENT_SSID)

        elif lower_input in ["deep scan router", "router deep scan"]:
            gateway_ip = get_network_info()[1]
            cmd = ["nmap", "-p-", "-sV", "-T4", gateway_ip]
            run_and_store_scan(cmd, f"Deep Router Scan ({gateway_ip})", "deep_router", CURRENT_SSID)

        elif lower_input in ["deep scan", "deep scan network"]:
            node_ip, gateway_ip, _ = get_network_info()
            subnet_prefix = ".".join(node_ip.split('.')[:3]) + ".0/24"
            cmd = ["nmap", "-p-", "-sV", "-T4", subnet_prefix]
            run_and_store_scan(cmd, f"Deep Network-Wide Sweep ({subnet_prefix})", "deep_network", CURRENT_SSID)

        # SHOW RESULTS (4 Decoupled Slots)
        elif lower_input in ["show quick router", "show quick scan router", "show router quick"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip, CURRENT_SSID)
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
            vault_data = load_or_init_vault(gateway_ip, CURRENT_SSID)
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
            vault_data = load_or_init_vault(gateway_ip, CURRENT_SSID)
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
            vault_data = load_or_init_vault(gateway_ip, CURRENT_SSID)
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
            vault_data = load_or_init_vault(gateway_ip, CURRENT_SSID)
            vault_data["slots"]["quick_router"] = {"type": "None", "results": [], "timestamp": ""}
            save_vault(vault_data)
            print(f"{C_GREEN}[*] Quick Router slot cleared successfully.{C_RESET}\n")

        elif lower_input in ["delete quick network", "clear quick network", "delete quick scan"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip, CURRENT_SSID)
            vault_data["slots"]["quick_network"] = {"type": "None", "results": [], "timestamp": ""}
            save_vault(vault_data)
            print(f"{C_GREEN}[*] Quick Network slot cleared successfully.{C_RESET}\n")

        elif lower_input in ["delete deep router", "clear deep router"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip, CURRENT_SSID)
            vault_data["slots"]["deep_router"] = {"type": "None", "results": [], "timestamp": ""}
            save_vault(vault_data)
            print(f"{C_GREEN}[*] Deep Router slot cleared successfully.{C_RESET}\n")

        elif lower_input in ["delete deep network", "clear deep network", "delete deep scan"]:
            gateway_ip = get_network_info()[1]
            vault_data = load_or_init_vault(gateway_ip, CURRENT_SSID)
            vault_data["slots"]["deep_network"] = {"type": "None", "results": [], "timestamp": ""}
            save_vault(vault_data)
            print(f"{C_GREEN}[*] Deep Network slot cleared successfully.{C_RESET}\n")

        elif lower_input in ["purge vault", "delete profile"]:
            gateway_ip = get_network_info()[1]
            path = get_vault_filepath(gateway_ip, CURRENT_SSID)
            if os.path.exists(path):
                os.remove(path)
                print(f"{C_RED}[*] Active profile vault for '{CURRENT_SSID}' deleted.{C_RESET}\n")
            else:
                print(" [!] No vault file found to purge.")

        # IMMERSIVE SCI-FI TARGET CONNECT & HYDRA WORKFLOW
        elif lower_input.startswith("connect") or lower_input in ["jump", "audit", "crack"]:
            gateway_ip = get_network_info()[1]
            
            # Allow inline target parsing (e.g., 'connect 192.168.1.1')
            parts = user_input.split()
            if len(parts) > 1 and parts[1].count('.') == 3:
                target_ip = parts[1]
            else:
                print(f"\n{C_GREEN}[*] Found Target Cache to Connect{C_RESET}")
                target_ip = input("Awaiting Target to Connect > ").strip() or gateway_ip
                
            target_port = input("Choose your Poison (Port e.g. 80, 21) > ").strip()
            
            username = input("Enter target username (default 'admin'): ").strip() or "admin"
            wordlist = input("Enter path to wordlist (default 'wordlists/rockyou.txt'): ").strip() or "wordlists/rockyou.txt"
            
            if not os.path.exists(wordlist):
                print(f"[!] Warning: Wordlist '{wordlist}' not found. Check path.")
            
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
