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
    """Tạo file rules.json từ các tên miền lấy được từ DomainConverter"""
    domain_converter = DomainConverter()
    domains = domain_converter.process_urls()
    
    dynamic_rules = []
    for index, domain in enumerate(domains, start=1):
        rule = {
            "id": index,
            "priority": 1,
            "action": {"type": "block"},
            "condition": {
                "urlFilter": domain,
                "resourceTypes": ["script", "image", "xmlhttprequest"]
            }
        }
        dynamic_rules.append(rule)
    
    output_file = "rules.json"
    old_hash = get_file_hash(output_file)
    
    with open(output_file, "w") as file:
        json.dump(dynamic_rules, file, indent=4)
    
    new_hash = get_file_hash(output_file)
    
    if old_hash == new_hash:
        silent_error("Không có thay đổi nào trong rules.json. Không commit.")
        return
    
    info(f"Đã tạo file {output_file} với {len(domains)} tên miền.")
    
    commit_and_push(output_file)

def commit_and_push(file_path):
    try:
        status_result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        status_output = status_result.stdout.strip()
        
        if status_output:
            info(f"Đã thay đổi file {file_path}. Tiến hành commit và push.")
            subprocess.run(["git", "add", file_path], check=True)  # Thêm file vào staging
            subprocess.run(["git", "commit", "-m", f"Update {file_path}"], check=True)  # Commit
            subprocess.run(["git", "push"], check=True)  # Push thay đổi lên remote repository
        else:
            silent_error(f"Không có thay đổi trong {file_path}. Không cần commit.")
    
    except subprocess.CalledProcessError as e:
        error(f"Lỗi khi thực hiện lệnh git: {e}")

if __name__ == "__main__":
    create_rules_json()
