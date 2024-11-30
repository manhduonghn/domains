import os
from src import info
from src.domain import DomainConverter

def create_customrules():
    domain_converter = DomainConverter()
    domains = domain_converter.process_urls()
    output_file = "customrules.txt"
    
    with open(output_file, "w") as file:
        for domain in domains:
            file.write(f"{domain}\n")

    info(f"Đã tạo file {output_file} với {len(domains)} tên miền.")

if __name__ == "__main__":
    create_customrules()
