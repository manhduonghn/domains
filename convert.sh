#!/bin/bash

# Danh sách các URL tải file
urls=(
  "https://abpvn.com/android/abpvn.txt"
  #"https://example.com/another_file.txt"
)

# Duyệt qua từng URL trong danh sách
for url in "${urls[@]}"; do
  file_name=$(basename "$url")

  # Tải file từ URL
  echo "Đang tải file từ $url..."
  curl -s -o "$file_name" "$url"

  # Kiểm tra nếu file tải về thành công
  if [ ! -f "$file_name" ]; then
    echo "Không thể tải file từ URL: $url"
    continue  # Tiếp tục với URL tiếp theo nếu có lỗi
  fi

  # Đầu ra
  output_file="customrules.txt"

  # Lọc, sắp xếp và lưu vào file domains.txt
  grep -Eo '0\.0\.0\.0 [a-zA-Z0-9.-]+' "$file_name" | awk '{print $2}' | sort >> "$output_file"
  echo "Đã thêm tên miền từ $file_name vào $output_file"
done

# Thông báo hoàn tất
if [ -s "$output_file" ]; then
  echo "File '$output_file' đã được tạo thành công."
else
  echo "Không tìm thấy dữ liệu hợp lệ trong các file tải về."
  exit 1
fi
