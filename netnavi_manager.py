import os
import shutil
import subprocess

PROJECT_DIR = os.path.expanduser("~/Projects/NetNavi")
BASELINE_DIR = os.path.expanduser("~/.netnavi_original")
SNAPSHOTS_DIR = os.path.expanduser("~/.netnavi_snapshots")

def ensure_dirs():
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    if not os.path.exists(BASELINE_DIR):
        print("[*] Creating System Lock / Immutable Failsafe baseline...")
        shutil.copytree(PROJECT_DIR, BASELINE_DIR, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.netnavi_snapshots'))

def get_next_backup_name():
    ensure_dirs()
    existing = [d for d in os.listdir(SNAPSHOTS_DIR) if d.startswith("NetNavi")]
    if not existing:
        return "NetNavi001"
    
    numbers = []
    for name in existing:
        try:
            num = int(name.replace("NetNavi", ""))
            numbers.append(num)
        except ValueError:
            continue
            
    next_num = max(numbers) + 1 if numbers else 1
    return f"NetNavi{next_num:03d}"

def list_backups():
    ensure_dirs()
    backups = sorted([d for d in os.listdir(SNAPSHOTS_DIR) if d.startswith("NetNavi")])
    return backups

def save_project():
    ensure_dirs()
    choice = input("Wanna save the changes? (Yes/No): ").strip().lower()
    if choice not in ['y', 'yes']:
        print("[*] Save aborted.")
        return

    next_name = get_next_backup_name()
    target_path = os.path.join(SNAPSHOTS_DIR, next_name)
    
    print(f"[*] Packaging workspace into save file: {next_name}...")
    shutil.copytree(PROJECT_DIR, target_path, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.netnavi_snapshots'))
    print(f"[+] Project successfully saved as: {next_name}")

def restore_project():
    backups = list_backups()
    if not backups:
        print("[!] No saved backups found.")
        return

    print("\n=== Choose Restore Point to Access ===")
    for i, b in enumerate(backups, 1):
        latest_tag = " (Latest)" if i == len(backups) else ""
        print(f"{i}. {b}{latest_tag}")
    
    choice = input("\nEnter backup number to restore (or 0 to cancel): ").strip()
    if not choice.isdigit() or int(choice) == 0:
        return
    
    idx = int(choice) - 1
    if 0 <= idx < len(backups):
        selected_backup = backups[idx]
        target = os.path.join(SNAPSHOTS_DIR, selected_backup)
        
        confirm = input(f"[!] Warning: This will overwrite your active workspace with {selected_backup}. Proceed? (y/N): ").lower()
        if confirm == 'y':
            for item in os.listdir(PROJECT_DIR):
                if item in ['.git', '.netnavi_snapshots']:
                    continue
                item_path = os.path.join(PROJECT_DIR, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            
            for item in os.listdir(target):
                s_item = os.path.join(target, item)
                d_item = os.path.join(PROJECT_DIR, item)
                if os.path.isdir(s_item):
                    shutil.copytree(s_item, d_item)
                else:
                    shutil.copy2(s_item, d_item)
            print(f"[+] Workspace successfully restored from {selected_backup}!")

def purge_project():
    backups = list_backups()
    if not backups:
        print("[!] No saved backups to purge.")
        return

    print("\n=== Choose NetNavi Save File to Purge ===")
    for i, b in enumerate(backups, 1):
        print(f"{i}. {b}")
    
    choice = input("\nEnter backup number to delete (or 0 to cancel): ").strip()
    if not choice.isdigit() or int(choice) == 0:
        return
    
    idx = int(choice) - 1
    if 0 <= idx < len(backups):
        target_backup = backups[idx]
        target_path = os.path.join(SNAPSHOTS_DIR, target_backup)
        
        confirm = input(f"[!] Purge Protection: Are you sure you want to delete {target_backup}? (y/N): ").lower()
        if confirm == 'y':
            shutil.rmtree(target_path)
            print(f"[-] Successfully purged backup file: {target_backup}")

def github_cloud_backup():
    os.chdir(PROJECT_DIR)
    print("\n=== GitHub Cloud Backup ===")
    subprocess.run(["git", "status", "-s"])
    
    msg = input("Enter commit message for cloud backup: ").strip()
    if not msg:
        msg = "NetNavi automated cloud backup milestone"
        
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", msg])
    print("[*] Uploading changes to GitHub...")
    result = subprocess.run(["git", "push"])
    
    if result.returncode == 0:
        print("[+] System successfully backed up to the cloud (GitHub)!")
    else:
        print("[!] Git push encountered an error or needs authentication.")

def main():
    ensure_dirs()
    while True:
        print("\n========================================")
        print("        3 TIER FAILSAFE MANAGER         ")
        print("========================================")
        print("1. System Lock / Immutable Failsafe")
        print("2. Save (Create NetNavi00x Point)")
        print("3. Restore (Choose Restore Point)")
        print("4. Purge / Delete (Remove Unnecessary Saves)")
        print("5. GitHub (Cloud Backup)")
        print("6. Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == '1':
            print(f"[*] System Lock / Immutable baseline secured at: {BASELINE_DIR}")
        elif choice == '2':
            save_project()
        elif choice == '3':
            restore_project()
        elif choice == '4':
            purge_project()
        elif choice == '5':
            github_cloud_backup()
        elif choice == '6':
            print("[*] Exiting FailSafe Manager.")
            break
        else:
            print("[!] Invalid option. Please choose between 1 and 6.")

if __name__ == "__main__":
    main()
