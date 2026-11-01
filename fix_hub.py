import os

hub_path = os.path.expanduser("~/Projects/NetNavi/hub.py")

with open(hub_path, "r") as f:
    lines = f.readlines()

# Clean up any broken floating failsafe blocks we previously added
cleaned_lines = []
skip = False
for line in lines:
    if "# NetNavi Failsafe Command Handlers" in line:
        skip = True
    if skip and "else:" in line and "Hello" not in line:
        skip = False
        continue
    if not skip:
        cleaned_lines.append(line)

content = "".join(cleaned_lines)

# Ensure import is at the top
import_line = "from netnavi_manager import save_project, restore_project, purge_project, github_cloud_backup"
if import_line not in content:
    content = import_line + "\n" + content

# Find where NetNavi reads user chat prompt (usually `user_input = input("NetNavi > ")`)
# Let's inject our check right where user input is evaluated.
target_str = 'NetNavi > "' # or whatever prompt your input uses

# Alternative: Let's inject right before the final fallback print statement
fallback_target = 'print(f"Hello. How can I assist?\\n")'

failsafe_code = """        # NetNavi Failsafe Command Handlers
        user_input_lower = user_input.strip().lower() if 'user_input' in locals() or 'user_input' in globals() else ""
        if "save project" in user_input_lower:
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

if fallback_target in content:
    content = content.replace(fallback_target, failsafe_code)
    with open(hub_path, "w") as f:
        f.write(content)
    print("[+] hub.py successfully cleaned and re-patched!")
else:
    print("[!] Target fallback block not found.")
