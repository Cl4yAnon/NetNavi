# We can patch or update hub.py to handle 'connect'
with open("hub.py", "r") as f:
    code = f.read()

# Replace the jump command block with a flexible connect handler
old_jump_block = """        # IMMERSIVE SCI-FI TARGET JUMP & HYDRA WORKFLOW
        elif lower_input in ["jump", "audit", "crack"]:
            gateway_ip = get_network_info()[1]
            
            print(f"\\n{C_GREEN}[*] Found Target Cache to Connect{C_RESET}")
            target_ip = input("Awaiting Target to Jump > ").strip() or gateway_ip
            target_port = input("Choose your Poison (Port e.g. 80, 21) > ").strip()"""

new_connect_block = """        # IMMERSIVE SCI-FI TARGET CONNECT & HYDRA WORKFLOW
        elif lower_input.startswith("connect") or lower_input in ["jump", "audit", "crack"]:
            gateway_ip = get_network_info()[1]
            
            # Allow inline target parsing (e.g., 'connect 192.168.1.1')
            parts = user_input.split()
            if len(parts) > 1 and parts[1].count('.') == 3:
                target_ip = parts[1]
            else:
                print(f"\\n{C_GREEN}[*] Found Target Cache to Connect{C_RESET}")
                target_ip = input("Awaiting Target to Connect > ").strip() or gateway_ip
                
            target_port = input("Choose your Poison (Port e.g. 80, 21) > ").strip()"""

if old_jump_block in code:
    code = code.replace(old_jump_block, new_connect_block)
    with open("hub.py", "w") as f:
        f.write(code)
    print("[+] Successfully updated hub.py to support 'connect' (both inline and interactive)!")
else:
    print("[!] Could not auto-patch automatically, let's rewrite it cleanly if needed.")
