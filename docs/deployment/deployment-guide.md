# Hướng dẫn Triển khai BotAI

Tài liệu này hướng dẫn cách triển khai BotAI backend lên VPS production và cách chạy local cho development.

---

## Production: Deploy lên VPS

### Kiến trúc

```
Vercel (Frontend Next.js) → Cloudflare Tunnel / Ngrok → VPS (port 8000)
                                                         ├── botai-backend.service (gunicorn + uvicorn workers)
                                                         └── soop-backend.service  (port 8001, app khác)
```

### Thông tin VPS

| Thành phần | Chi tiết |
|---|---|
| VPS | Contabo, Ubuntu 24.04, 4 CPU, 8GB RAM |
| User | `botai` (user riêng, không dùng root) |
| Repo | `/home/botai/repo/` |
| Port | 8000 |
| Process | gunicorn + UvicornWorker (multi-worker) |
| Service | `botai-backend.service` (systemd) |

### Setup lần đầu

```bash
# SSH vào VPS
ssh root@<VPS_IP>

# Clone repo và chạy setup script
git clone https://github.com/lyeoeon1/botai.git /tmp/botai-setup
sudo bash /tmp/botai-setup/deploy/setup-vps.sh
rm -rf /tmp/botai-setup
```

Script sẽ tự động: tạo user `botai`, clone repo, tạo venv, cài dependencies, cài systemd service, và khởi động.

### Deploy/Update code mới

```bash
sudo bash /home/botai/repo/deploy/deploy.sh
```

### Quản lý service

```bash
# Xem trạng thái
sudo systemctl status botai-backend

# Xem logs
sudo journalctl -u botai-backend -f

# Restart
sudo systemctl restart botai-backend

# Stop
sudo systemctl stop botai-backend
```

### Cấu hình .env

File `.env` tại `/home/botai/repo/backend/.env` cần các biến sau:

```env
OPENAI_API_KEY=sk-...
LLAMA_CLOUD_API_KEY=llx-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_CONNECTION_STRING=postgresql://...
FRONTEND_URL=https://your-frontend.vercel.app
BACKEND_PORT=8000
```

---

## Development: Vercel Frontend + Local Backend

Hướng dẫn chạy local cho development.

## 1. Chuẩn bị Backend (Local)

Trước tiên, hãy đảm bảo backend của bạn đang chạy ổn định ở port 8000.

### Bước 1.1: Chạy Backend

Mở terminal tại thư mục backend và chạy lệnh khởi động server (ví dụ dùng uvicorn):

```bash
cd backend
# Kích hoạt virtual env nếu có (ví dụ: source venv/bin/activate)
# Cài đặt dependencies nếu chưa cài
pip install -r requirements.txt
# Chạy server
uvicorn app.main:app --reload --port 8000
```

> Lưu ý: Thay `app.main:app` bằng đường dẫn tới file chạy chính của bạn nếu khác.

## 2. Cài đặt và Chạy Ngrok

Ngrok giúp tạo một đường hầm (tunnel) để người ngoài (ví dụ: Vercel) có thể truy cập vào localhost của bạn.

### Bước 2.1: Cài đặt Ngrok

Nếu bạn chưa có Ngrok, hãy cài đặt (trên macOS):

```bash
brew install ngrok/ngrok/ngrok
```

Hoặc tải từ trang chủ: ngrok.com

### Bước 2.2: Đăng ký và kết nối tài khoản

Đăng ký tài khoản miễn phí tại dashboard.ngrok.com.
Lấy Authtoken từ dashboard.
Chạy lệnh sau để kết nối tài khoản:

```bash
ngrok config add-authtoken <TOKEN_CỦA_BẠN>
```

### Bước 2.3: Tạo đường hầm (Tunnel)

Mở một terminal mới (giữ terminal backend chạy) và gõ:

```bash
ngrok http 8000
```

Màn hình sẽ hiện ra thông tin, hãy copy dòng Forwarding có dạng `https://xxxx-xxxx.ngrok-free.app`. Đây chính là Public URL của backend.

## 3. Deploy Frontend lên Vercel

### Bước 3.1: Đẩy code lên GitHub/GitLab

Đảm bảo code frontend của bạn đã được đẩy lên một repository trên GitHub.

### Bước 3.2: Tạo Project trên Vercel

Truy cập vercel.com và đăng nhập.
Nhấn "Add New..." > "Project".
Chọn repository của bạn và nhấn Import.

### Bước 3.3: Cấu hình Biến môi trường (Environment Variables)

Trong màn hình cấu hình trước khi deploy:

1. Tìm mục **Environment Variables**.
2. Thêm biến sau:
   - **Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** Dán đường link Ngrok bạn vừa copy (ví dụ: `https://xxxx-xxxx.ngrok-free.app`).

> Lưu ý: Không có dấu `/` ở cuối.
> Ví dụ đúng: `https://1234.ngrok-free.app`
> Ví dụ sai: `https://1234.ngrok-free.app/`

3. Nhấn **Deploy**.

## 4. Kiểm thử

Đợi Vercel deploy xong và truy cập vào trang web (Domain do Vercel cấp).

- Thử tính năng Chat hoặc gọi API.
- Quan sát terminal chạy Backend và Ngrok trên máy bạn:
  - Bạn sẽ thấy các request xuất hiện trên terminal của Ngrok và Backend.
  - Nếu thấy status `200 OK`, tức là kết nối thành công!

## 5. Lưu ý quan trọng

- Mỗi lần chạy lại Ngrok, URL sẽ thay đổi (với tài khoản miễn phí).
- Khi URL thay đổi, bạn cần vào **Settings** của Project trên Vercel > **Environment Variables** để cập nhật lại `NEXT_PUBLIC_API_URL`, sau đó **Redeploy** (hoặc Promote) để áp dụng thay đổi.
- Để tránh việc này, bạn có thể mua gói trả phí của Ngrok để có Static Domain (tên miền cố định).
