# KẾ HOẠCH BÀN GIAO DỰ ÁN WINDBOT

**Dự án:** AI Chatbot Tua-bin Gió (WINDBOT) — Qualcomm VR Lab
**Ngày bàn giao dự kiến:** [Ngày H]
**Bên giao:** [Nhóm phát triển]
**Bên nhận:** EPU/TAF

---

## 1. Tổng quan

### Mục tiêu

Bàn giao hoàn chỉnh hệ thống WINDBOT cho EPU/TAF, bao gồm: source code, tài liệu, knowledge base, credentials, và đào tạo vận hành. Sau bàn giao, EPU/TAF có thể tự vận hành hệ thống với sự hỗ trợ theo SLA 3 tháng.

### Phạm vi

- Source code (Frontend + Backend)
- Database & Knowledge base
- Tài liệu kỹ thuật + hướng dẫn quản trị
- Access credentials
- Buổi đào tạo trực tiếp (3-3.5 giờ)
- Hỗ trợ sau bàn giao (SLA 3 tháng)

### Tài liệu liên quan

| Tài liệu | Đường dẫn | Mục đích |
|---|---|---|
| Checklist bàn giao | `docs/handover/handover-checklist.md` | Danh sách hạng mục bàn giao |
| Biên bản bàn giao | `docs/handover/handover-report.md` | Xác nhận chính thức |
| Thỏa thuận hỗ trợ | `docs/handover/sla.md` | SLA 3 tháng |
| Outline đào tạo | `docs/handover/training-outline.md` | Nội dung buổi training |
| Bản gửi client | `docs/handover/client-preparation.md` | Gửi trước cho EPU/TAF |

---

## 2. Giai đoạn 1: Chuẩn bị (Tuần -2 đến Tuần -1)

### Tuần -2: Liên hệ & xác nhận

**Liên hệ client:**

- [ ] Gửi email EPU/TAF xác nhận ngày bàn giao (xem mẫu email ở mục 7.1)
- [ ] Gửi file `docs/handover/client-preparation.md` để client chuẩn bị
- [ ] Hỏi client: danh sách người tham dự (tên, vai trò, email)
- [ ] Hỏi client: phòng họp + thiết bị (projector, wifi, ổ cắm điện)
- [ ] Hỏi client: muốn tạo OpenAI account riêng hay nhận key từ nhóm phát triển?
- [ ] Hỏi client: cần GitHub repo access hay nhận USB offline?

**Xác nhận nội bộ:**

- [ ] Xác nhận ai trong nhóm sẽ tham dự buổi bàn giao
- [ ] Phân công: ai trình bày phần nào (Lead / Tech)
- [ ] Xác nhận có đủ thiết bị demo (laptop, internet backup 4G)

### Tuần -1: Chuẩn bị kỹ thuật

**Hoàn thiện tài liệu:**

- [ ] Điền placeholder trong `docs/handover/sla.md` (email hỗ trợ, GitHub Issues URL)
- [ ] Điền placeholder trong `README.md` (email liên hệ)
- [ ] Điền thông tin "Bên giao" trong `docs/handover/handover-report.md`
- [ ] Cập nhật `[VPS-IP]` trong docs nếu đã biết IP cố định
- [ ] Review lần cuối tất cả tài liệu trong `docs/handover/`

**Chuẩn bị kỹ thuật:**

- [ ] Test hệ thống production (https://windbot.vercel.app) — hỏi 5 câu test
- [ ] Chạy `export_data.py --include-vectors` để backup toàn bộ data
- [ ] Tạo OpenAI account cho client (nếu client chọn key riêng)
- [ ] Chuẩn bị danh sách credentials bàn giao (viết ra giấy hoặc file mã hóa)
- [ ] Push final version lên GitHub delivery repo
- [ ] Chuẩn bị 1 file PDF mẫu để demo nạp tài liệu trong buổi training

**Chuẩn bị vật lý:**

- [ ] In tài liệu (mỗi bộ 2 bản):
  - `docs/guides/admin-guide.md`
  - `docs/handover/sla.md`
  - `docs/guides/disaster-recovery.md`
- [ ] In biên bản + SLA để ký (2 bản mỗi loại):
  - `docs/handover/handover-report.md`
  - `docs/handover/sla.md`
- [ ] Chuẩn bị USB chứa:
  - Zip source code toàn bộ repo
  - Data export (từ `export_data.py`)
  - File `.env.example`
- [ ] Chuẩn bị bút ký
- [ ] Backup internet: hotspot 4G nếu wifi phòng họp không ổn định

---

## 3. Giai đoạn 2: Ngày bàn giao (Ngày H)

### Trước buổi họp (30 phút trước)

- [ ] Đến sớm 30 phút, setup thiết bị
- [ ] Kiểm tra hệ thống live hoạt động bình thường
- [ ] Mở sẵn các tab trên trình duyệt:
  - https://windbot.vercel.app (chatbot)
  - Supabase Dashboard (database)
  - OpenAI Dashboard (API usage)
  - Terminal SSH vào VPS (sẵn sàng demo)
- [ ] Test nhanh chatbot: hỏi 2 câu tiếng Việt + tiếng Anh
- [ ] Đặt USB, tài liệu in, biên bản lên bàn
- [ ] Kiểm tra projector/màn hình hoạt động

### Kịch bản buổi bàn giao (3-3.5 giờ)

| Thời gian | Phần | Nội dung chi tiết | Người trình bày | Tài liệu tham chiếu |
|-----------|------|-------------------|-----------------|---------------------|
| 0:00-0:05 | Mở đầu | Chào hỏi, giới thiệu thành viên, mục tiêu buổi bàn giao | Lead | — |
| 0:05-0:30 | Tổng quan | Demo live chatbot (Việt + Anh), giải thích kiến trúc, sơ đồ các thành phần | Lead | `README.md` |
| 0:30-1:15 | Quản trị | Demo: thêm tài liệu mới (nạp file PDF mẫu), xem chat history, glossary, API keys, chi phí | Lead/Tech | `admin-guide.md` |
| 1:15-1:25 | **Nghỉ giải lao** | | | |
| 1:25-2:10 | Sự cố | Demo: restart backend, check logs, rebuild index, các lỗi thường gặp | Tech | `admin-guide-advanced.md` |
| 2:10-2:40 | Hạ tầng | VPS management, Vercel dashboard, Supabase dashboard, chi phí hàng tháng, backup schedule | Tech | `disaster-recovery.md` |
| 2:40-2:55 | Q&A | Giải đáp thắc mắc, giới thiệu disaster recovery, nhắc SLA, thảo luận post-SLA | Lead | `sla.md`, `disaster-recovery.md` |
| 2:55-3:15 | **Bàn giao chính thức** | Bàn giao credentials, trao USB, ký biên bản, ký SLA | Lead + Client | `handover-report.md`, `sla.md` |
| 3:15-3:30 | Kết thúc | Chụp ảnh lưu niệm, xác nhận kênh liên hệ, cảm ơn | Tất cả | — |

### Checklist bàn giao credentials (thực hiện tại mục 2:55-3:15)

Bàn giao trực tiếp, **KHÔNG gửi qua email:**

- [ ] **VPS:** IP address, SSH user (root + botai), password/SSH key
- [ ] **OpenAI:** API key + link dashboard (platform.openai.com)
- [ ] **Supabase:** Project URL, service key, dashboard login
- [ ] **LlamaCloud:** API key
- [ ] **Vercel:** Mời vào team (email) hoặc transfer project ownership
- [ ] **GitHub:** Mời collaborator vào repo hoặc transfer ownership
- [ ] **USB:** Trao USB backup (source code + data export)

### Ký biên bản

- [ ] Đọc qua biên bản cùng client (highlight các mục chưa hoàn thành)
- [ ] Ký biên bản bàn giao: 2 bản — mỗi bên giữ 1 bản gốc
- [ ] Ký SLA: 2 bản — mỗi bên giữ 1 bản gốc
- [ ] Ghi ngày bàn giao thực tế vào biên bản

---

## 4. Giai đoạn 3: Sau bàn giao (SLA 3 tháng)

### Tuần +1 (ngay sau bàn giao)

- [ ] Gửi email xác nhận hoàn thành bàn giao (xem mẫu email ở mục 7.2)
- [ ] Đính kèm: bản scan biên bản đã ký (backup digital)
- [ ] Nhắc lại: kênh liên hệ, response time theo SLA
- [ ] Kiểm tra client đã access được hệ thống (GitHub, Supabase, VPS)
- [ ] Hỗ trợ nếu client gặp vấn đề setup ban đầu

### Hàng tháng (tháng 1, 2, 3)

- [ ] Gửi email check-in: "Hệ thống có ổn định không? Cần hỗ trợ gì?"
- [ ] Nhắc client backup dữ liệu hàng tuần (`export_data.py`)
- [ ] Xử lý bug/request theo SLA (Critical ≤4h, Normal ≤2 ngày)
- [ ] Ghi nhận mọi support request vào log

### 2 tuần trước khi hết SLA

- [ ] Gửi email thông báo SLA sắp hết (xem mẫu email ở mục 7.3)
- [ ] Đề xuất 3 phương án: gia hạn / tự vận hành / thuê bên thứ 3
- [ ] Hẹn meeting nếu client muốn thảo luận

### Kết thúc SLA

- [ ] Gửi email xác nhận kết thúc SLA
- [ ] Cung cấp final backup nếu client yêu cầu
- [ ] Ghi nhận bài học kinh nghiệm (lessons learned)

---

## 5. Chi phí vận hành hàng tháng (cho client)

| Dịch vụ | Chi phí | Ghi chú |
|---------|---------|---------|
| OpenAI API | ~$5-20/tháng | Tùy lượng sử dụng, xem platform.openai.com/usage |
| Supabase | $0 (Free) hoặc $25 (Pro) | Free tier tự pause sau 7 ngày không dùng |
| VPS | Tùy provider | Chi phí hiện tại: [___]/tháng |
| Vercel | $0 (Hobby) | Frontend hosting miễn phí |
| LlamaCloud | $0 (Free tier) | Chỉ tốn khi nạp tài liệu mới |
| **Tổng ước tính** | **~$5-45/tháng** | |

---

## 6. Rủi ro & Phương án dự phòng

| Rủi ro | Xác suất | Phương án dự phòng |
|--------|----------|-------------------|
| Internet phòng họp không ổn định | Trung bình | Chuẩn bị hotspot 4G backup |
| Demo chatbot lỗi (OpenAI outage) | Thấp | Chuẩn bị screenshots/video demo dự phòng |
| Client không cử đủ người (thiếu kỹ thuật) | Trung bình | Ghi hình buổi training, gửi video sau |
| Client muốn thay đổi yêu cầu tại buổi bàn giao | Trung bình | Ghi nhận, hẹn xử lý sau — không thay đổi scope tại chỗ |
| Quên USB/tài liệu in | Thấp | Kiểm tra checklist trước khi ra khỏi nhà |
| VPS down ngay buổi bàn giao | Rất thấp | Demo trên localhost hoặc dùng screenshots |

---

## 7. Template email

### 7.1. Email xác nhận ngày bàn giao (gửi tuần -2)

```
Tiêu đề: [WINDBOT] Xác nhận lịch bàn giao dự án

Kính gửi [Tên người nhận],

Chúng tôi xin xác nhận lịch bàn giao dự án AI Chatbot Tua-bin Gió (WINDBOT)
như sau:

- Ngày: [Ngày H]
- Thời gian: [giờ bắt đầu] - [giờ kết thúc] (khoảng 3-3.5 giờ)
- Địa điểm: [___]
- Nội dung: Bàn giao hệ thống + đào tạo vận hành

Đính kèm tài liệu chuẩn bị để quý vị tham khảo trước buổi bàn giao.

Kính nhờ quý vị xác nhận:
1. Ngày giờ trên có phù hợp không?
2. Danh sách người tham dự (tên, vai trò, email)
3. Phòng họp có projector và wifi không?
4. Quý vị muốn tạo tài khoản OpenAI riêng hay nhận API key từ chúng tôi?

Trân trọng,
[Tên]
```

### 7.2. Email xác nhận hoàn thành bàn giao (gửi tuần +1)

```
Tiêu đề: [WINDBOT] Xác nhận hoàn thành bàn giao

Kính gửi [Tên người nhận],

Chúng tôi xin xác nhận đã hoàn thành bàn giao dự án WINDBOT vào ngày [Ngày H].

Đính kèm: Bản scan biên bản bàn giao đã ký.

Nhắc lại thông tin hỗ trợ (SLA 3 tháng, đến [ngày kết thúc SLA]):
- Email: [email hỗ trợ]
- Response time: Critical ≤4 giờ, Normal ≤2 ngày làm việc
- Giờ hỗ trợ: 9:00-17:00 (GMT+7), Thứ 2-6

Tài liệu hướng dẫn có sẵn trong repository đã bàn giao:
- Quản trị hệ thống: docs/guides/admin-guide.md
- Xử lý sự cố: docs/guides/disaster-recovery.md

Nếu có bất kỳ vấn đề nào, vui lòng liên hệ qua email trên.

Trân trọng,
[Tên]
```

### 7.3. Email nhắc hết SLA (gửi 2 tuần trước khi hết)

```
Tiêu đề: [WINDBOT] Thông báo SLA sắp hết hạn

Kính gửi [Tên người nhận],

Thỏa thuận hỗ trợ (SLA) cho dự án WINDBOT sẽ hết hạn vào ngày [ngày kết thúc].

Quý vị có 3 lựa chọn:
1. Gia hạn SLA — chúng tôi sẽ gửi đề xuất hợp đồng mới
2. Tự vận hành — quý vị đã có đầy đủ tài liệu hướng dẫn
3. Chuyển giao cho đơn vị CNTT khác — toàn bộ source code và tài liệu
   thuộc về quý vị

Nếu quý vị muốn thảo luận, chúng tôi sẵn sàng hẹn meeting.

Trân trọng,
[Tên]
```

---

> **Lưu ý:** Cập nhật kế hoạch này khi có thay đổi. Sau khi hoàn thành mỗi mục, đánh dấu ☑.
