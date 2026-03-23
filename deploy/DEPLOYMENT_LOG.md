# BotAI Deployment Log

Ghi chép quá trình triển khai thực tế trên VPS.

---

## Lần 1 — Ngày: 23/03/2026

### Mục tiêu
Chuyển BotAI backend từ chạy dưới root (single uvicorn + pm2) sang user `botai` riêng + systemd + gunicorn.

### Trạng thái trước khi triển khai
- BotAI chạy dưới **root**, single uvicorn, port 8000, quản lý bởi **pm2**
- Repo tại `/root/botai/`, venv tại `/root/botai/venv/`
- Không có systemd service
- SOOP đã chạy ổn định trên port 8001 (user `soop`, systemd, gunicorn)

### Các bước thực hiện

| Bước | Lệnh | Kết quả | Ghi chú |
|------|-------|---------|---------|
| 1. Commit & push code | `git push -u origin lyeoeon1/vps-multi-app-setup` | ✅ | PR #26 |
| 2. Merge PR | Merge trên GitHub | ✅ | |
| 3. SSH vào VPS | `ssh root@62.146.236.156` | ✅ | |
| 4. Tạo user botai | `useradd -m -s /bin/bash botai` | ✅ | uid=1001 |
| 5. Clone repo | `su - botai` rồi `git clone https://<TOKEN>@github.com/...` | ✅ | Cần GitHub token vì repo private |
| 6. Tạo venv | `python3 -m venv .../backend/venv` | ✅ | |
| 7. Cài dependencies | `pip install -r requirements.txt` | ✅ | |
| 8. Cài gunicorn | `pip install gunicorn` | ✅ | Thiếu trong requirements.txt, cài thêm |
| 9. Copy .env | `cp /root/botai/backend/.env ...` (chạy ở root) | ✅ | User botai không có quyền đọc /root/ |
| 10. Cài systemd service | `cp .../botai-backend.service /etc/systemd/system/` | ✅ | `Created symlink ...` |
| 11. Dừng pm2 backend cũ | `pm2 stop backend && pm2 delete backend && pm2 save` | ✅ | Uvicorn root cũ quản lý bởi pm2, không phải systemd |
| 12. Start service mới | `systemctl restart botai-backend` | ✅ | |
| 13. Verify | `lsof -i :8000`, `systemctl status botai-backend` | ✅ | 4 workers, user botai, active (running) |

### Kết quả
- ✅ **Thành công**
- Service `botai-backend` chạy ổn định dưới user `botai`
- Gunicorn 1 master + 4 workers trên `0.0.0.0:8000`
- Frontend windbot.vercel.app kết nối backend qua `http://62.146.236.156:8000` — hoạt động OK
- Warning `Could not create vector index: replace is set to False` — không ảnh hưởng (index đã tồn tại)

### Vấn đề gặp phải
1. **Repo private** → không clone được bằng `sudo -u botai git clone`. Giải pháp: `su - botai` rồi clone với GitHub token
2. **Gunicorn chưa cài** → service lỗi `status=203/EXEC`. Giải pháp: cài thêm `pip install gunicorn`
3. **Uvicorn root cũ tự restart** → pm2 đang quản lý, kill process không đủ. Giải pháp: `pm2 stop/delete backend`
4. **Copy .env cần quyền root** → user botai không đọc được `/root/`. Giải pháp: chạy `cp` từ root
5. **Gunicorn bind 127.0.0.1** → frontend Vercel không kết nối được (NEXT_PUBLIC_API_URL trỏ trực tiếp vào IP VPS). Giải pháp: đổi bind sang `0.0.0.0:8000`

### Bài học rút ra
1. Thêm `gunicorn` vào `requirements.txt` để không phải cài tay
2. Kiểm tra pm2/supervisor/systemd trước khi kill process — process có thể tự restart
3. Phân biệt rõ lệnh nào chạy ở root, lệnh nào ở user botai
4. Repo private cần setup GitHub token hoặc SSH key cho user mới
5. Kiểm tra cách frontend kết nối backend (IP trực tiếp vs ngrok vs tunnel) trước khi quyết định bind address

---

## Trạng thái hiện tại

| App | User | Port | Process Manager | Service Name |
|-----|------|------|-----------------|--------------|
| BotAI | `botai` | 8000 | systemd | `botai-backend.service` |
| SOOP | `soop` | 8001 | systemd | `soop-backend.service` |

### Lệnh quản lý nhanh

```bash
# BotAI
sudo systemctl status botai-backend
sudo systemctl restart botai-backend
sudo journalctl -u botai-backend -f

# SOOP
sudo systemctl status soop-backend
sudo systemctl restart soop-backend
sudo journalctl -u soop-backend -f
```

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
