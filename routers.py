import os
import importlib.util
import sys

def list_registered_models(isp_dir):
    if not os.path.exists(isp_dir):
        return []
    files = [f[:-3] for f in os.listdir(isp_dir) if f.endswith('.py') and f != '__init__.py']
    return files

def display_poison_pill_taxonomy():
    while True:
        print("\n[+] === NETNAVI: POISON PILL TAXONOMY ===")
        
        pldt_dir = "modules/router_audits/pldt"
        globe_dir = "modules/router_audits/globe"
        os.makedirs(pldt_dir, exist_ok=True)
        os.makedirs(globe_dir, exist_ok=True)
        
        pldt_custom = list_registered_models(pldt_dir)
        globe_custom = list_registered_models(globe_dir)
        
        print("\n## [1] PLDT / Smart Matrix")
        if not pldt_custom:
            print(" [!] No custom models registered")
        for idx, m in enumerate(pldt_custom, 1):
            print(f" [{idx}] {m}.py")
            
        print("\n## [2] Globe Telecom Matrix")
        if not globe_custom:
            print(" [!] No custom models registered")
        for idx, m in enumerate(globe_custom, 1):
            print(f" [{idx}] {m}.py")
            
        print("\n[Controls]")
        print(" add <pldt|globe> <model>")
        print(" delete <pldt|globe> <model>")
        print(" x (exit)")
        
        action = input("\nTaxonomy > ").strip()
        
        if action.lower() in ["exit", "quit", "x"]:
            break
        elif action.lower().startswith("add "):
            parts = action.split()
            if len(parts) >= 3:
                isp_target = parts[1].lower()
                model_name = parts[2].lower().replace(".py", "")
                target_dir = pldt_dir if isp_target in ["pldt", "1"] else globe_dir if isp_target in ["globe", "2"] else None
                
                if target_dir:
                    file_path = os.path.join(target_dir, f"{model_name}.py")
                    with open(file_path, "w") as f:
                        f.write(f"# Router Model Stub: {model_name}\n")
                        f.write("TARGET_PATH = \"/login.html\"\n\n")
                        f.write("def run_audit(target_ip, username, wordlist_path):\n")
                        f.write("    import subprocess\n")
                        f.write(f"    print('[*] Executing audit for {model_name}')\n")
                        f.write("    target_url = f\"http-get://{target_ip}{TARGET_PATH}\"\n")
                        f.write("    hydra_cmd = [\"hydra\", \"-l\", username, \"-P\", wordlist_path, target_url, \"-t\", \"4\"]\n")
                        f.write("    subprocess.run(hydra_cmd)\n")
                    print(f"[✔] Added: {model_name}.py")
                else:
                    print("[!] Use 'pldt' or 'globe'.")
            else:
                print("[!] Format: add pldt <model>")
        elif action.lower().startswith("delete "):
            parts = action.split()
            if len(parts) >= 3:
                isp_target = parts[1].lower()
                model_name = parts[2].lower().replace(".py", "")
                target_dir = pldt_dir if isp_target in ["pldt", "1"] else globe_dir if isp_target in ["globe", "2"] else None
                
                if target_dir:
                    file_path = os.path.join(target_dir, f"{model_name}.py")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"[✔] Purged: {model_name}.py")
                    else:
                        print(f"[!] '{model_name}.py' not found.")
                else:
                    print("[!] Use 'pldt' or 'globe'.")
            else:
                print("[!] Format: delete pldt <model>")
        else:
            print("[!] Unknown command.")

def handle_router_matrix(target_ip):
    print("\n[*] Initializing Target Taxonomy Fingerprint...")
    print("[?] Select ISP Architecture:")
    print("    [1] PLDT / Smart Matrix")
    print("    [2] Globe Telecom Matrix")
    
    isp_choice = input("NetNavi [ISP Selection] > ").strip()
    
    if isp_choice in ["1", "2"]:
        isp_name = "PLDT / Smart" if isp_choice == "1" else "Globe Telecom"
        target_dir = "modules/router_audits/pldt" if isp_choice == "1" else "modules/router_audits/globe"
        os.makedirs(target_dir, exist_ok=True)
        
        custom_models = list_registered_models(target_dir)
        
        if not custom_models:
            print("[!] No custom router models registered in this matrix yet.")
            print("    Use the 'taxonomy' command to add models first.")
            return None
            
        print(f"\n[+] Target locked to: {isp_name} Architecture")
        print("    Select Hardware Firmware Module:")
        for idx, model_name in enumerate(custom_models, 1):
            print(f"    [{idx}] {model_name}.py")
            
        model_choice = input(f"NetNavi [{isp_name} Model] > ").strip()
        
        if model_choice.isdigit():
            choice_idx = int(model_choice)
            if 1 <= choice_idx <= len(custom_models):
                selected_model = custom_models[choice_idx - 1]
                print(f"\n[*] Selected Router Profile: {selected_model}.py")
                
                username = input("Enter target username (default 'admin'): ").strip() or "admin"
                wordlist = input("Enter path to wordlist (default 'wordlists/rockyou.txt'): ").strip() or "wordlists/rockyou.txt"
                
                if not os.path.exists(wordlist):
                    print(f"[!] Warning: Wordlist '{wordlist}' not found. Check path.")

                module_path = os.path.join(target_dir, f"{selected_model}.py")
                spec = importlib.util.spec_from_file_location(selected_model, module_path)
                router_mod = importlib.util.module_from_spec(spec)
                sys.modules[selected_model] = router_mod
                spec.loader.exec_module(router_mod)
                
                if hasattr(router_mod, "run_audit"):
                    router_mod.run_audit(target_ip, username, wordlist)
                else:
                    print(f"[!] Error: {selected_model}.py lacks a run_audit() function.")
            else:
                print("[!] Invalid model index selection.")
    else:
        print("[!] Invalid ISP selection.")
    return None
