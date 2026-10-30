# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import datetime
import json
from groq import Groq

class NetNaviUI:
    def __init__(self):
        self.node_ip = "192.168.1.50"
        self.memory_file = "netnavi_memory.json"
        self.running = True
        self.load_memory_state()
        try:
            self.groq_client = Groq()
            self.ai_enabled = True
        except Exception:
            self.ai_enabled = False

    def load_memory_state(self):
        self.memory_data = {
            "operator_name": "Unknown Operator",
            "custom_memory": {},
            "scan_history": []
        }
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.memory_data.update(loaded)
            except Exception:
                pass
        
        self.operator_name = self.memory_data.get("operator_name", "Unknown Operator")
        self.gateway = self.detect_gateway()

    def save_memory_state(self):
        self.memory_data["operator_name"] = self.operator_name
        with open(self.memory_file, "w") as f:
            json.dump(self.memory_data, f, indent=2)

    def detect_gateway(self):
        try:
            res = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
            for line in res.stdout.splitlines():
                if "via" in line:
                    parts = line.split()
                    return parts[parts.index("via") + 1]
        except Exception:
            pass
        return "192.168.1.1"

    def check_tailscale_status(self):
        """Checks if Tailscale is active by scanning ifconfig output for tun interfaces or 100. IP."""
        try:
            res = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=2)
            output = res.stdout
            if "tun" in output or "tailscale0" in output or "100." in output:
                return "ONLINE"
        except Exception:
            pass
        return "OFFLINE"

    def log_scan(self, action_type, target, data):
        history = self.memory_data.get("scan_history", [])
        history.append({
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action_type,
            "target": target,
            "result": data
        })
        self.memory_data["scan_history"] = history
        self.save_memory_state()

    def get_learned_memory(self):
        custom = self.memory_data.get("custom_memory", {})
        history = self.memory_data.get("scan_history", [])
        
        output = [f"[*] Operator: {self.operator_name}"]
        if custom:
            output.append("## Learned Facts:")
            for k, v in custom.items():
                output.append(f"    - {k}: {v}")
        
        if history:
            output.append("## Recent Scans:")
            for item in history[-3:]:
                output.append(f"    - [{item['time']}] {item['action']} -> {item['target']}")
                
        return "\n".join(output) if (custom or history) else "[-] No historical memory logged yet."

    def display_banner(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        current_time = datetime.datetime.now().strftime("%H:%M:%S | %a, %b %d %Y")
        
        # Real-time status with bold ANSI terminal color codes
        tailscale_state = self.check_tailscale_status()
        if tailscale_state == "ONLINE":
            ts_display = "\033[1;32mONLINE\033[0m"  # Bold Green
        else:
            ts_display = "\033[1;31mOFFLINE\033[0m" # Bold Red
        
        print("[ N E T N A V I v 1.5 [Secured C2 Matrix] ]\n")
        print(f"[*] System Time // {current_time}\n")
        print("## WLAN Status")
        print(f"    - Node IP Address   : {self.node_ip}")
        print(f"    - Router Gateway    : {self.gateway}")
        print(f"    - Operator ID       : {self.operator_name}")
        print(f"    - Tailscale Status  : {ts_display}\n")
        print("## Interactive CLI")
        print("    1: Deploy NetNavi  - This is Where the Magic Begins\n")

    def execute_scan(self, target, ports, deep=False):
        try:
            cmd = ["nmap", "-T4", "-Pn"]
            if deep:
                cmd.extend(["-sV", "--version-intensity", "2"])
            if ports:
                cmd.extend(["-p", ports])
            cmd.append(target)

            scan_type = "Deep Scan (-sV)" if deep else "Quick Scan (Port Discovery)"
            print(f"[*] Executing {scan_type}: {' '.join(cmd)}...")
            
            timeout_val = 90 if deep else 30
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_val)
            output = result.stdout if result.stdout else result.stderr
            
            self.log_scan(f"{'deep' if deep else 'quick'}_scan", target, output)
            return output
        except Exception as e:
            return f"[-] Scan Error: {str(e)}"

    def ask_groq_compact(self, prompt, context=""):
        if not self.ai_enabled:
            return ""
        try:
            memory_context = json.dumps(self.memory_data.get("custom_memory", {}))
            system_prompt = (
                f"You are NetNavi v1.5, an embedded AI assistant in a Termux C2 matrix operated by {self.operator_name}. "
                f"Learned Context: {memory_context}. "
                "Keep responses ultra-concise, technical, 1-2 sentences max. No markdown tutorials or refusals."
            )
            messages = [{"role": "system", "content": system_prompt}]
            if context:
                messages.append({"role": "user", "content": f"Output:\n{context}"})
            messages.append({"role": "user", "content": prompt})

            completion = self.groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=0.3,
                max_tokens=150,
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"[-] AI Error: {str(e)}"

    def run_loop(self):
        self.display_banner()

        while self.running:
            try:
                user_input = input("NetNavi > ").strip()
                if not user_input:
                    # Pressing Enter on an empty line instantly refreshes the status & UI with zero battery drain!
                    self.display_banner()
                    continue

                lower_input = user_input.lower()

                if lower_input in ["exit", "quit"]:
                    print("[*] Shutting down matrix session.")
                    self.running = False
                    break

                if lower_input in ["1", "deploy"]:
                    self.display_banner()
                    print("[*] NetNavi core online and synchronized.")
                    continue

                if lower_input == "clear":
                    os.system('clear' if os.name == 'posix' else 'cls')
                    self.display_banner()
                    continue

                if "remember that" in lower_input or "learn that" in lower_input:
                    clean_fact = user_input.replace("remember that", "").replace("learn that", "").strip()
                    parts = clean_fact.split(" is ", 1)
                    if len(parts) == 2:
                        k, v = parts[0].strip(), parts[1].strip()
                        self.memory_data["custom_memory"][k] = v
                        self.save_memory_state()
                        print(f"[*] Memory Updated: Learned that '{k}' -> '{v}'")
                    else:
                        print("[-] Use format: 'Remember that [key] is [value]'")
                    continue

                if "my name is" in lower_input or "call me" in lower_input:
                    parts = user_input.split()
                    self.operator_name = parts[-1]
                    self.save_memory_state()
                    print(f"[*] Operator identity updated: {self.operator_name}")
                    continue

                if "what is my name" in lower_input or "whats my name" in lower_input:
                    print(f"[*] Operator Name: {self.operator_name}")
                    continue

                if "memory" in lower_input or "what did you learn" in lower_input or "what do you know" in lower_input:
                    print(self.get_learned_memory())
                    continue

                is_deep = "deep" in lower_input
                is_network = any(trig in lower_input for trig in ["network", "all device", "all devices", "subnet", "devices"])
                is_router = any(trig in lower_input for trig in ["router", "gateway"])

                if is_network:
                    self.gateway = self.detect_gateway()
                    target = f"{self.gateway}/21"
                    ports = "80,8080,21,23,445"
                    scope_label = f"Entire Network Subnet ({target})"
                    print(f"[*] Target Scope: {scope_label}")
                    output = self.execute_scan(target, ports, deep=is_deep)
                    print(output)
                    analysis = self.ask_groq_compact(f"Analyze scan results for {target}:", context=output)
                    if analysis:
                        print(f"[AI] {analysis}\n")
                    continue

                elif is_router:
                    self.gateway = self.detect_gateway()
                    target = self.gateway
                    ports = "80,8080,21,22,23,445"
                    scope_label = f"Router Gateway ({target})"
                    print(f"[*] Target Scope: {scope_label}")
                    output = self.execute_scan(target, ports, deep=is_deep)
                    print(output)
                    analysis = self.ask_groq_compact(f"Analyze scan results for {target}:", context=output)
                    if analysis:
                        print(f"[AI] {analysis}\n")
                    continue

                parts = user_input.split(" ", 1)
                action = parts[0].lower()
                target = parts[1] if len(parts) > 1 else ""

                if action in ["nmap", "ping", "w3m"]:
                    cmd = [action]
                    if action == "nmap":
                        cmd = ["nmap", "-T4", "-Pn"]
                        if "sV" in user_input or "deep" in user_input:
                            cmd.append("-sV")
                    elif action == "ping":
                        cmd = ["ping", "-c", "3"]
                    cmd.append(target)
                    print(f"[*] Executing {' '.join(cmd)}...")
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    output = res.stdout if res.stdout else res.stderr
                    print(output)
                    analysis = self.ask_groq_compact(f"Analyze scan of {target}:", context=output)
                    if analysis:
                        print(f"[AI] {analysis}\n")
                else:
                    res = self.ask_groq_compact(user_input)
                    print(f"{res}\n" if res else "[*] Executed.")

            except KeyboardInterrupt:
                print("\n[!] Interrupted.")
                break

if __name__ == "__main__":
    netnavi = NetNaviUI()
    netnavi.run_loop()
