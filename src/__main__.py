import os
import subprocess
import json
from hashlib import sha256
from src import info, silent_error, error
from src.domains import DomainConverter

def get_file_hash(file_path):
    sha256_hash = sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def create_rules_json():
    domain_converter = DomainConverter()
    domains = domain_converter.process_urls()
    
    dynamic_rules = []
    for index, domain in enumerate(domains, start=1):
        rule = {
            "id": index,
            "priority": 1,
            "action": {"type": "block"},
            "condition": {
                "urlFilter": domain
            }
        }
        dynamic_rules.append(rule)
    
    temp_output_file = "temp_rules.json"
    old_hash = get_file_hash(temp_output_file)
    
    # Save the generated rules into temp_rules.json first
    with open(temp_output_file, "w") as file:
        json.dump(dynamic_rules, file, indent=4)
    
    new_hash = get_file_hash(temp_output_file)
    
    if old_hash == new_hash:
        silent_error("Không có thay đổi nào trong temp_rules.json. Không commit.")
        return
    
    info(f"Đã tạo file {temp_output_file} với {len(domains)} tên miền.")
    
    # Merge with custom rules and create a final rules.json
    merge_custom_rules(temp_output_file)
    commit_and_push("rules.json")

def merge_custom_rules(temp_rules_file):
    custom_rules_file = "custom_rules.json"
    
    # Load existing rules from temp_rules.json
    existing_rules = load_json(temp_rules_file)
    custom_rules = load_json(custom_rules_file)

    # Find the last ID in existing rules (temp_rules.json)
    max_existing_id = max((rule['id'] for rule in existing_rules), default=0)
    
    # Update custom rule IDs to continue from the highest existing ID
    for rule in custom_rules:
        rule['id'] += max_existing_id  # Adjust ID to avoid duplication

    # Append custom rules to existing rules
    existing_rules.extend(custom_rules)
    
    # Save the final combined rules to rules.json
    save_json("rules.json", existing_rules)

    info(f"Đã kết hợp {len(custom_rules)} custom rules vào rules.json.")

def load_json(file_path):
    """Load JSON data from a file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def save_json(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def commit_and_push(file_path):
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"], check=True)

        status_result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        status_output = status_result.stdout.strip()
        
        if status_output:
            info(f"Đã thay đổi file {file_path}. Tiến hành commit và push.")
            subprocess.run(["git", "add", file_path], check=True)
            subprocess.run(["git", "commit", "-m", f"Update {file_path}"], check=True)
            subprocess.run(["git", "push"], check=True)
        else:
            silent_error(f"Không có thay đổi trong {file_path}. Không cần commit.")
    
    except subprocess.CalledProcessError as e:
        error(f"Lỗi khi thực hiện lệnh git: {e}")

if __name__ == "__main__":
    create_rules_json()
