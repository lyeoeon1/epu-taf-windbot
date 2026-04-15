# BIÊN BẢN BÀN GIAO DỰ ÁN

---

<div align="center">

## BIÊN BẢN BÀN GIAO DỰ ÁN

**Tên dự án:** AI Chatbot Tua-bin Gió (WINDBOT) — Qualcomm VR Lab

**Phiên bản:** 2.1

**Ngày bàn giao:** [\_\_\_\_\_/\_\_\_\_/2026]

</div>

---

## 1. Các bên liên quan

### Bên giao

| Hạng mục     | Thông tin                  |
| ------------ | -------------------------- |
| Đơn vị       | [Tên nhóm phát triển]     |
| Đại diện     | [\_\_\_\_\_\_\_\_\_\_\_\_]  |
| Chức vụ      | [\_\_\_\_\_\_\_\_\_\_\_\_]  |

### Bên nhận

| Hạng mục     | Thông tin                  |
| ------------ | -------------------------- |
| Đơn vị       | EPU/TAF                    |
| Đại diện     | [\_\_\_\_\_\_\_\_\_\_\_\_]  |
| Chức vụ      | [\_\_\_\_\_\_\_\_\_\_\_\_]  |

---

## 2. Danh mục sản phẩm bàn giao

| STT | Sản phẩm                                      | Mô tả chi tiết                                                                  | Ghi chú           |
| --- | ---------------------------------------------- | -------------------------------------------------------------------------------- | ------------------ |
| 1   | Mã nguồn (Source code)                         | Frontend Next.js 16 + Backend FastAPI                                            | Đầy đủ             |
| 2   | Database schema & migrations                   | Supabase PostgreSQL + pgvector                                                   | Đầy đủ             |
| 3   | Kho kiến thức (Knowledge base)                 | 25 chunks PDF + 150 Q&A + 87 glossary terms + 2900+ chunks từ tài liệu bổ sung  | Đầy đủ             |
| 4   | Tài liệu kỹ thuật                             | README, deployment guide, architecture docs                                      | Đầy đủ             |
| 5   | Tài liệu hướng dẫn                            | Admin guide, correction learning guide, migration guide                          | Đầy đủ             |
| 6   | Tài liệu bàn giao                             | Biên bản, SLA, checklist, training outline                                       | Đầy đủ             |
| 7   | Deploy scripts                                 | deploy.sh, setup-vps.sh, botai-backend.service                                  | Đầy đủ             |
| 8   | Benchmark & kết quả kiểm thử                  | 150 Q&A benchmark, 46 test cases — 85% pass                                     | Đầy đủ             |

---

## 3. Trạng thái yêu cầu nghiệp vụ

### A) PHÂN TÍCH YÊU CẦU

| STT | Yêu cầu                                  | Trạng thái          |
| --- | ----------------------------------------- | -------------------- |
| 1   | Thu thập và chuẩn hóa tài liệu kỹ thuật | ⚠️ Một phần         |
| 2   | Xác định kịch bản Q&A chính              | ✅ Đã đáp ứng       |
| 3   | Đánh giá tích hợp Web và VR360           | ⚠️ Một phần         |

### B) THIẾT KẾ & PHÁT TRIỂN

| STT | Yêu cầu                                  | Trạng thái          |
| --- | ----------------------------------------- | -------------------- |
| 4   | Xây dựng AI chatbot NLP song ngữ         | ✅ Đã đáp ứng       |
| 5   | Xây dựng kho kiến thức chuyên biệt       | ✅ Đã đáp ứng       |
| 6   | Thiết kế giao diện thân thiện            | ⚠️ Một phần         |

### C) QUẢN LÝ DỮ LIỆU & BẢO MẬT

| STT | Yêu cầu                                  | Trạng thái          |
| --- | ----------------------------------------- | -------------------- |
| 7   | Chiến lược dữ liệu                       | ⚠️ Một phần         |
| 8   | Dataset Card                              | ✅ Đã đáp ứng       |
| 9   | HTTPS/TLS                                 | ⚠️ Một phần         |
| 10  | Versioning dữ liệu                       | ❌ Chưa có          |
| 11  | Quyền sở hữu dữ liệu EPU/TAF            | ❌ Chưa có          |
| 12  | Tuân thủ bảo mật ISO 27001               | ❌ Chưa có          |

### D) TÍCH HỢP HỆ THỐNG

| STT | Yêu cầu                                  | Trạng thái          |
| --- | ----------------------------------------- | -------------------- |
| 13  | Tích hợp Web và VR360                     | ⚠️ Một phần         |
| 14  | Context awareness trong VR                | ❌ Chưa có          |
| 15  | Hiệu năng FPS ≥72Hz, latency ≤0.5s      | ❌ Chưa có          |
| 16  | API/SDK mở                                | ✅ Đã đáp ứng       |

### E) ĐÀO TẠO & HỖ TRỢ

| STT | Yêu cầu                                  | Trạng thái          |
| --- | ----------------------------------------- | -------------------- |
| 17  | Tài liệu kỹ thuật và hướng dẫn          | ⚠️ Một phần         |
| 18  | Bàn giao AI model, dataset, pipeline     | ⚠️ Một phần         |
| 19  | Hỗ trợ sau triển khai 3 tháng            | ❌ Chưa có          |

### Tổng hợp

| Trạng thái          | Số lượng | Tỷ lệ |
| -------------------- | -------- | ------ |
| ✅ Đã đáp ứng       | 5        | 26%    |
| ⚠️ Một phần         | 8        | 42%    |
| ❌ Chưa có          | 6        | 32%    |

---

## 4. Các hạng mục chưa hoàn thành

Danh sách 6 yêu cầu chưa được đáp ứng và lộ trình khuyến nghị:

| STT | Hạng mục                          | Lộ trình / Ghi chú                                  |
| --- | ---------------------------------- | ---------------------------------------------------- |
| 1   | Tích hợp VR360                    | Cần đánh giá WebXR API + POC                         |
| 2   | Versioning dữ liệu                | Cần thêm version tracking vào Supabase               |
| 3   | Quyền sở hữu dữ liệu EPU/TAF    | Cần ký DPA, xem xét self-host                        |
| 4   | Tuân thủ bảo mật ISO 27001       | Cần auth layer, audit log, rate limiting             |
| 5   | Context awareness trong VR        | Phụ thuộc VR360 implementation                       |
| 6   | Hiệu năng VR (FPS/latency)       | Phụ thuộc VR360 implementation                       |
| 7   | Hỗ trợ sau triển khai 3 tháng    | Theo thỏa thuận SLA đính kèm                         |

---

## 5. Thông tin triển khai hiện tại

| Thành phần | Công nghệ / Địa chỉ                              |
| ---------- | -------------------------------------------------- |
| Frontend   | Vercel (https://windbot.vercel.app)                |
| Backend    | VPS (Gunicorn 4 workers + systemd)                 |
| Database   | Supabase PostgreSQL + pgvector                     |
| LLM        | OpenAI gpt-4.1-mini                                |
| Embedding  | text-embedding-3-small (1536 dimensions)           |

---

## 6. Điều khoản hỗ trợ

Theo thỏa thuận SLA đính kèm tại `docs/handover/sla.md`, thời hạn hỗ trợ là **3 tháng** kể từ ngày bàn giao.

---

## 7. Chữ ký xác nhận

<br>

<table width="100%">
<tr>
<td width="50%" align="center"><strong>BÊN GIAO</strong></td>
<td width="50%" align="center"><strong>BÊN NHẬN</strong></td>
</tr>
<tr>
<td align="center"><br><br><br><br><em>(Ký tên, ghi rõ họ tên)</em></td>
<td align="center"><br><br><br><br><em>(Ký tên, ghi rõ họ tên)</em></td>
</tr>
<tr>
<td align="center">Họ tên: ________________________</td>
<td align="center">Họ tên: ________________________</td>
</tr>
<tr>
<td align="center">Ngày: ____/____/2026</td>
<td align="center">Ngày: ____/____/2026</td>
</tr>
</table>
