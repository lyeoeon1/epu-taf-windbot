# BotAI Deployment Log

Ghi chép quá trình triển khai thực tế trên VPS.

---

## Lần 1 — Ngày: ___/___/2026

### Mục tiêu
Chuyển BotAI backend từ chạy dưới root (single uvicorn) sang user `botai` riêng + systemd + gunicorn.

### Trạng thái trước khi triển khai
- BotAI chạy dưới root, single uvicorn, port 8000
- Repo tại `/root/botai/`
- Không có systemd service

### Các bước thực hiện

| Bước | Lệnh | Kết quả | Ghi chú |
|------|-------|---------|---------|
| 1. Commit & push code | `git push` | ⬜ | |
| 2. SSH vào VPS | `ssh root@62.146.236.156` | ⬜ | |
| 3. Tạo user botai | `useradd -m -s /bin/bash botai` | ⬜ | |
| 4. Clone repo | `sudo -u botai git clone ...` | ⬜ | |
| 5. Tạo venv | `python3 -m venv ...` | ⬜ | |
| 6. Cài dependencies | `pip install -r requirements.txt` | ⬜ | |
| 7. Copy .env | `cp /root/botai/backend/.env ...` | ⬜ | |
| 8. Cài systemd service | `cp ... /etc/systemd/system/` | ⬜ | |
| 9. Dừng process cũ | `kill <PID>` | ⬜ | |
| 10. Start service mới | `systemctl start botai-backend` | ⬜ | |
| 11. Verify | `curl localhost:8000/api/health` | ⬜ | |

### Kết quả
- ⬜ Thành công / ❌ Thất bại

### Vấn đề gặp phải
_(ghi lại nếu có)_

### Bài học rút ra
_(ghi lại nếu có)_

---

<!--
## Template cho lần deploy tiếp theo

## Lần N — Ngày: ___/___/2026

### Mục tiêu
_Mô tả thay đổi_

### Các bước thực hiện

| Bước | Lệnh | Kết quả | Ghi chú |
|------|-------|---------|---------|
| 1. | | ⬜ | |

### Kết quả
- ⬜ Thành công / ❌ Thất bại

### Vấn đề gặp phải

### Bài học rút ra
-->
