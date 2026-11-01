import os

hub_path = os.path.expanduser("~/Projects/NetNavi/hub.py")

with open(hub_path, "r") as f:
    content = f.read()

# 1. Add import at the top if not present
import_line = "from netnavi_manager import save_project, restore_project, purge_project, github_cloud_backup"
if import_line not in content:
    content = import_line + "\n" + content

# 2. Inject failsafe command handlers before the final fallback else block
target_block = "else:\n            print(f\"Hello. How can I assist?\\n\")"

failsafe_injection = """# NetNavi Failsafe Command Handlers
        elif "save project" in user_input_lower:
            print(f"\\n{C_CYAN}[[*] NetNavi Failsafe Triggered]{C_RESET}")
            save_project()
        elif "restore project" in user_input_lower:
            print(f"\\n{C_CYAN}[[*] NetNavi Failsafe Triggered]{C_RESET}")
            restore_project()
        elif "purge project" in user_input_lower:
            print(f"\\n{C_CYAN}[[*] NetNavi Failsafe Triggered]{C_RESET}")
            purge_project()
        elif "github backup" in user_input_lower or "cloud backup" in user_input_lower:
            print(f"\\n{C_CYAN}[[*] NetNavi Failsafe Triggered]{C_RESET}")
            github_cloud_backup()
        else:
            print(f"Hello. How can I assist?\\n")"""

if "save project" not in content:
    if target_block in content:
        content = content.replace(target_block, failsafe_injection)
        with open(hub_path, "w") as f:
            f.write(content)
        print("[+] Successfully patched hub.py with failsafe commands!")
    else:
        print("[!] Could not automatically locate the fallback block in hub.py. Please check structure.")
else:
    print("[*] Failsafe commands are already present in hub.py.")
