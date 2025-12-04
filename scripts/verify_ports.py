import re
import os
import socket
import subprocess

def get_ports_from_compose(compose_path):
    ports = set()
    with open(compose_path, "r") as f:
        for line in f:
            match = re.match(r'\s*-\s*"(\d+):', line)
            if match:
                ports.add(int(match.group(1)))
    return sorted(ports)

def get_port_process(port):
    try:
        result = subprocess.run(
            ["sudo", "lsof", "-i", f":{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            return result.stdout.strip()
        else:
            return None
    except Exception as e:
        return f"Error: {e}"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    compose_file = os.path.join(os.path.dirname(__file__), "..", "docker-compose.yml")
    ports = get_ports_from_compose(compose_file)
    print(f"Ports found in {compose_file}: {ports}\n")
    for port in ports:
        if is_port_in_use(port):
            print(f"Port {port}: IN USE")
            proc_info = get_port_process(port)
            if proc_info:
                print(proc_info)
            else:
                print("  No process info found.")
        else:
            print(f"Port {port}: free")

if __name__ == "__main__":
    main()