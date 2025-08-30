$py = "C:\Users\Admin\Desktop\Tiktokshop_Update\.venv\Scripts\python.exe"
$root = "C:\Users\Admin\Desktop\Tiktokshop_Update"

# Refresh token
& $py "$root\refresh_env_token.py"
if ($LASTEXITCODE -ne 0) {
  Write-Error "Refresh token thất bại. Dừng job để tránh gọi API với token hết hạn."
  exit 1
}

# Chạy lấy đơn
& $py "$root\orders_search_7days.py"
exit $LASTEXITCODE
