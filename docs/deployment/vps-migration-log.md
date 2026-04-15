# Nhật ký chuyển đổi VPS sang repo deliverables

**Ngày:** 16/04/2026
**Thực hiện bởi:** Nhóm phát triển
**VPS:** 103.82.39.253

---

## Bối cảnh

VPS đang chạy backend từ repo dev gốc (cấu trúc file chưa clean). Cần chuyển sang repo deliverables (`epu-taf-windbot`) đã được restructure và bổ sung tài liệu bàn giao, để khi client SSH vào sẽ thấy cấu trúc chuyên nghiệp.

## Thông tin hệ thống

| Thông tin | Giá trị |
|---|---|
| VPS IP | 103.82.39.253 |
| OS | Ubuntu (instance-87375054) |
| User | botai |
| Service | botai-backend (systemd) |
| Port | 8001 (bind 127.0.0.1) |
| Port 8000 | Dự án khác, không liên quan |
| Repo cũ | `/home/botai/botai/repo/` (dev) |
| Repo mới | `https://github.com/lyeoeon1/epu-taf-windbot.git` |

## Quy trình thực hiện

### Bước 1: Backup repo dev hiện tại

```bash
cp -r /home/botai/botai/repo /home/botai/botai/repo-dev-backup
```

### Bước 2: Clone repo deliverables

```bash
cd /home/botai/botai/
git clone https://github.com/lyeoeon1/epu-taf-windbot.git repo-new
```

### Bước 3: Copy .env từ repo cũ

```bash
cp /home/botai/botai/repo/backend/.env /home/botai/botai/repo-new/backend/.env
```

### Bước 4: Setup Python venv

```bash
cd /home/botai/botai/repo-new/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Bước 5: Dừng service, swap thư mục, restart

```bash
sudo systemctl stop botai-backend
mv /home/botai/botai/repo /home/botai/botai/repo-dev-old
mv /home/botai/botai/repo-new /home/botai/botai/repo
sudo systemctl restart botai-backend
```

### Sự cố: Service crash (status=203/EXEC)

**Nguyên nhân:** Venv được tạo khi thư mục còn tên `repo-new`, shebang trong `venv/bin/uvicorn` trỏ tới `/home/botai/botai/repo-new/...` — path không còn tồn tại sau khi rename.

**Fix:** Tạo lại venv tại đúng path mới:

```bash
cd /home/botai/botai/repo/backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart botai-backend
```

### Kết quả

```bash
$ curl -s http://127.0.0.1:8001/api/health
{"status":"ok","version":"0.1.0"}
```

Frontend https://windbot.vercel.app hoạt động bình thường — chatbot phản hồi, streaming OK, follow-up suggestions hiển thị.

## Trạng thái thư mục sau migration

```
/home/botai/botai/
├── repo/               ← Repo deliverables (ĐANG CHẠY)
├── repo-dev-old/       ← Repo dev cũ (backup, xóa sau khi ổn định)
├── repo-dev-backup/    ← Backup trước migration (xóa sau khi ổn định)
```

## Bài học kinh nghiệm

1. **Tạo venv SAU khi rename thư mục** — shebang trong venv scripts encode đường dẫn tuyệt đối tại thời điểm tạo.
2. **Luôn backup trước khi swap** — `cp -r` repo cũ trước khi di chuyển.
3. **Test health endpoint ngay sau restart** — `curl localhost:8001/api/health` để xác nhận nhanh.

## Cleanup (thực hiện sau vài ngày ổn định)

```bash
rm -rf /home/botai/botai/repo-dev-old
rm -rf /home/botai/botai/repo-dev-backup
```
