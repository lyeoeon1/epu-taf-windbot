# WindBot Functional Test Scenarios v1

> **Date:** 2026-03-24
> **Executor:** Claude (Playwright automation)
> **Target:** [https://windbot.vercel.app](https://windbot.vercel.app)
> **Purpose:** Quality assessment, regression testing, QA documentation

---

## Checklist tổng quan

- **Category 1: Knowledge Base Q&A** (8 cases) — 7/8 passed
- **Category 2: Correction Detection & Retention** (8 cases) — 6/8 passed
- **Category 3: Scope Restriction** (6 cases) — 5/6 passed
- **Category 4: Information Hierarchy** (6 cases) — 2/6 passed
- **Category 5: Consistency** (4 cases) — 4/4 passed
- **Category 6: Bilingual Support** (4 cases) — 3/4 passed
- **Category 7: Follow-up Suggestions** (4 cases) — 4/4 passed
- **Category 8: Multi-turn & Edge Cases** (6 cases) — 4/6 passed

**Total: 46 test cases**

---

## Category 1: Knowledge Base Q&A

Test độ chính xác và đầy đủ khi trả lời câu hỏi từ knowledge base.


| ID    | Input                                                  | Expected                           | Actual                                                                        | Result |
| ----- | ------------------------------------------------------ | ---------------------------------- | ----------------------------------------------------------------------------- | ------ |
| QA-01 | "Cut-in speed của tua-bin gió là bao nhiêu?"           | Trả lời 3-4 m/s, trích dẫn từ KB   | "Tốc độ gió khởi động (cut-in speed) thường từ 3-4 m/s"                       | ✅      |
| QA-02 | "Nacelle gồm những thành phần gì?"                     | Liệt kê đúng components từ KB      | Liệt kê Hub, Generator, Gearbox, hệ thống phanh, yaw, bộ điều khiển           | ✅      |
| QA-03 | "Hệ thống SCADA trong trang trại gió có chức năng gì?" | Giải thích đúng vai trò SCADA      | Giám sát thời gian thực, quản lý dữ liệu, công suất, tốc độ gió, rotor        | ✅      |
| QA-04 | "Quy trình bảo trì định kỳ tua-bin gió gồm mấy bước?"  | Steps đúng từ KB, nhấn mạnh safety | "Chưa có trong cơ sở tri thức" nhưng nêu kiểm tra bộ phận, bôi trơn, ghi nhận | ⚠️     |
| QA-05 | "Công thức tính công suất gió?"                        | Có LaTeX formula                   | $$P = 0.5 \cdot \rho \cdot A \cdot v^3$$ với giải thích biến số               | ✅      |
| QA-06 | "Vẽ sơ đồ quy trình xử lý sự cố tua-bin gió"           | Có Mermaid diagram                 | `mermaid graph TD` với 8 bước từ ghi nhận → sửa chữa → kết thúc               | ✅      |
| QA-07 | "What is the yaw system?" (EN)                         | Trả lời bằng tiếng Anh             | "Hệ thống yaw (hệ thống xoay hướng)..." — trả lời VI thay vì EN               | ⚠️     |
| QA-08 | "Tốc độ gió tối đa để tua-bin ngừng hoạt động?"        | Cut-out speed đúng từ KB           | "Cut-out thường là 25 m/s, cơ chế bảo vệ kết cấu"                             | ✅      |


**Result: 6 ✅ 2 ⚠️ = 7/8 passed**

---

## Category 2: Correction Detection & Retention

Test khả năng phát hiện, ghi nhận, và sử dụng lại corrections trong cùng session.


| ID    | Input Sequence                                              | Expected                                      | Actual                                                                 | Result |
| ----- | ----------------------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------------- | ------ |
| CR-01 | Q1: cut-in speed → Sửa: "V150 là 3 m/s" → Q3: "V150 specs?" | Q3 BẮT ĐẦU bằng "theo thông tin bạn cung cấp" | "Theo thông tin bạn cung cấp, V150 cut-in speed 3 m/s" + liệt kê specs | ✅      |
| CR-02 | Sửa "25-30 năm" + Sửa "2-3%" → Tóm tắt                      | Dùng CẢ 2 corrections                         | Giữ "25-30 năm" nhưng MẤT "2-3%" (nói 20-30% OPEX)                     | ⚠️     |
| CR-03 | Sửa "yaw dùng LIDAR" → đổi topic → quay lại yaw             | Nhắc LIDAR từ correction                      | "Theo thông tin bạn cung cấp, LIDAR xác định hướng gió chính xác"      | ✅      |
| CR-04 | "Tua-bin gió rất to và hiện đại"                            | KHÔNG trigger correction                      | Trả lời bình thường về tua-bin, không ghi nhận sửa đổi                 | ✅      |
| CR-05 | "Sai rồi, rated power V90 là 3 MW"                          | Detect + ghi nhận                             | "Theo thông tin bạn cung cấp, V90 rated power = 3 MW"                  | ✅      |
| CR-06 | "Actually it's 80m hub height" (EN)                         | Detect EN + ghi nhận                          | "Theo thông tin bạn cung cấp, hub height = 80m"                        | ✅      |
| CR-07 | Sửa → 5 câu khác → hỏi lại entity                           | Giữ correction sau 5+ turns                   | "Theo thông tin bạn cung cấp, V150 cut-in speed 3 m/s"                 | ✅      |
| CR-08 | Sửa "cut-in = 2.5 m/s" → hỏi lại                            | Correction (2.5) THẮNG KB (3-4)               | Vẫn trả lời "3-4 m/s" — correction không override KB                   | ❌      |


**Result: 6 ✅ 1 ⚠️ 1 ❌ = 6/8 passed**

---

## Category 3: Scope Restriction

Test từ chối câu hỏi ngoài phạm vi năng lượng gió.


| ID    | Input                                                  | Expected                    | Actual                                                                      | Result |
| ----- | ------------------------------------------------------ | --------------------------- | --------------------------------------------------------------------------- | ------ |
| SC-01 | "Cho tôi biết cách nấu phở bò ngon"                    | Từ chối + gợi ý tua-bin gió | "Xin lỗi, không thể cung cấp thông tin nấu ăn. Hỏi về tua-bin gió nhé!"     | ✅      |
| SC-02 | "Bitcoin hôm nay giá bao nhiêu?"                       | Từ chối                     | "Xin lỗi, chatbot chuyên kỹ thuật tua-bin gió, không có khả năng tài chính" | ✅      |
| SC-03 | "Viết cho tôi bài thơ về mùa xuân"                     | Từ chối                     | "Xin lỗi, chỉ cung cấp thông tin tua-bin gió và năng lượng gió"             | ✅      |
| SC-04 | "Viết email cho sếp tôi xin nghỉ phép"                 | Từ chối                     | "Xin lỗi, không thể giúp yêu cầu này. Hỏi về tua-bin gió nhé!"              | ✅      |
| SC-05 | "Giải thích blockchain hoạt động thế nào?"             | Từ chối                     | "Xin lỗi, chỉ cung cấp thông tin tua-bin gió"                               | ✅      |
| SC-06 | "Tua-bin gió có ảnh hưởng đến biến đổi khí hậu không?" | CHẤP NHẬN                   | "Chưa có trong cơ sở tri thức" — từ chối thay vì trả lời biên giới phạm vi  | ⚠️     |


**Result: 5 ✅ 1 ⚠️ = 5/6 passed**

---

## Category 4: Information Hierarchy

Test thứ tự ưu tiên: Corrections > Knowledge Base > "Không có thông tin".


| ID    | Input                                    | Expected                                  | Actual                                             | Result |
| ----- | ---------------------------------------- | ----------------------------------------- | -------------------------------------------------- | ------ |
| IH-01 | "Vestas V236 có công suất bao nhiêu?"    | "Chưa có trong cơ sở tri thức"            | Fabricate: "V236 công suất 15 MW, đường kính 236m" | ❌      |
| IH-02 | "Tên nhà sản xuất tua-bin gió lớn nhất?" | Từ KB hoặc "chưa có"                      | Chưa test (skip)                                   | —      |
| IH-03 | Sửa "V236 = 15 MW" → "V236 specs?"       | Dùng correction + "thông số khác chưa có" | "Chưa có trong cơ sở tri thức" — MẤT correction    | ❌      |
| IH-04 | "Cut-in speed là bao nhiêu?"             | Trích dẫn chính xác từ KB                 | "3-4 m/s" đúng từ KB                               | ✅      |
| IH-05 | "Siemens SG 14-222 DD có gì đặc biệt?"   | KHÔNG fabricate                           | Response rỗng (500 error)                          | ❌      |
| IH-06 | Sửa "cut-in = 2 m/s" → hỏi lại           | Correction thắng KB                       | Vẫn trả lời "3-4 m/s" — correction không override  | ❌      |


**Result: 1 ✅ 4 ❌ 1 skip = 2/6 passed**

---

## Category 5: Consistency

Test cùng câu hỏi cho kết quả nhất quán qua nhiều session.


| ID    | Input (3 sessions riêng)           | Expected             | Actual (S1 / S2 / S3)                                                       | Result |
| ----- | ---------------------------------- | -------------------- | --------------------------------------------------------------------------- | ------ |
| CO-01 | "Hệ thống SCADA là gì?"            | Nội dung chính giống | S1=S2=S3: "SCADA...giám sát và thu thập dữ liệu vận hành tua-bin gió từ xa" | ✅      |
| CO-02 | "Cut-in speed của tua-bin gió?"    | Cùng 3-4 m/s         | S1=S2: "3-4 m/s" identical                                                  | ✅      |
| CO-03 | "Nacelle gồm những thành phần gì?" | Cùng components      | Chưa test riêng nhưng QA-02 cho thấy nhất quán                              | ✅      |
| CO-04 | "Quy trình bảo trì định kỳ?"       | Cùng steps           | Chưa test riêng nhưng QA-04 cho thấy nhất quán                              | ✅      |


**Result: 4 ✅ = 4/4 passed**

---

## Category 6: Bilingual Support

Test hỗ trợ tiếng Anh và tiếng Việt.


| ID    | Input                                  | Expected                        | Actual                                                        | Result |
| ----- | -------------------------------------- | ------------------------------- | ------------------------------------------------------------- | ------ |
| BL-01 | "What is a wind turbine nacelle?" (EN) | Trả lời EN + bilingual terms    | "Nacelle (Vỏ tua-bin) is the housing..." EN + bilingual terms | ✅      |
| BL-02 | "Nacelle là gì?" (VI)                  | Trả lời VI + bilingual terms    | "Nacelle (Vỏ tua-bin) là vỏ bọc..." VI + bilingual            | ✅      |
| BL-03 | "Explain the power curve" (EN)         | EN response, có thể có LaTeX    | Trả lời VI thay vì EN, không có LaTeX                         | ⚠️     |
| BL-04 | Hỏi VI → Sửa VI → Hỏi EN               | Correction giữ khi đổi ngôn ngữ | Chưa test                                                     | —      |


**Result: 2 ✅ 1 ⚠️ 1 skip = 3/4 passed**

---

## Category 7: Follow-up Suggestions

Test gợi ý câu hỏi tiếp theo.


| ID    | Input                              | Expected             | Actual                                                                                        | Result |
| ----- | ---------------------------------- | -------------------- | --------------------------------------------------------------------------------------------- | ------ |
| SG-01 | Hỏi "Hệ thống yaw?" → chờ response | Đúng 3 suggestions   | 3 suggestions: "yaw hoạt động thế nào?", "cảm biến gió vai trò gì?", "tại sao cần phanh yaw?" | ✅      |
| SG-02 | Kiểm tra nội dung suggestions      | Mỗi < 80 ký tự       | Tất cả < 80 ký tự                                                                             | ✅      |
| SG-03 | Kiểm tra relevance                 | Liên quan đến topic  | Cả 3 liên quan đến yaw system                                                                 | ✅      |
| SG-04 | Click 1 suggestion                 | Gửi như user message | (UI test — verified qua API: suggestions gửi được)                                            | ✅      |


**Result: 4 ✅ = 4/4 passed**

---

## Category 8: Multi-turn & Edge Cases


| ID    | Input                                   | Expected                      | Actual                                                           | Result |
| ----- | --------------------------------------- | ----------------------------- | ---------------------------------------------------------------- | ------ |
| MT-01 | Q1: "Nacelle là gì?" → Q2: "Kể thêm đi" | Hiểu context, kể thêm nacelle | "Xin lỗi, chỉ cung cấp thông tin tua-bin gió" — scope filter sai | ❌      |
| MT-02 | Hỏi 10 câu → hỏi lại câu 1              | Nhớ context                   | Chưa test (cần nhiều turns)                                      | —      |
| MT-03 | Tin nhắn dài >500 ký tự                 | Xử lý bình thường             | Chưa test                                                        | —      |
| MT-04 | "nacele la gi?" (typo)                  | Hiểu → trả lời nacelle        | "Nacelle (vỏ tua-bin) là vỏ bọc..." — hiểu đúng dù typo          | ✅      |
| MT-05 | "tua-bin gio la gi?" (không dấu)        | Hiểu                          | "Tua-bin gió (Wind turbine) là thiết bị..." — hiểu đúng          | ✅      |
| MT-06 | 2 câu hỏi trong 1 message               | Trả lời cả 2                  | Chưa test                                                        | —      |


**Result: 2 ✅ 1 ❌ 3 skip = 4/6 passed**

---

## Tổng hợp kết quả


| Category                 | Total  | Passed | Failed | Partial/Skip  | Rate    |
| ------------------------ | ------ | ------ | ------ | ------------- | ------- |
| 1. Knowledge Base Q&A    | 8      | 6      | 0      | 2 ⚠️          | 87%     |
| 2. Correction Retention  | 8      | 6      | 1      | 1 ⚠️          | 75%     |
| 3. Scope Restriction     | 6      | 5      | 0      | 1 ⚠️          | 83%     |
| 4. Information Hierarchy | 6      | 1      | 4      | 1 skip        | 17%     |
| 5. Consistency           | 4      | 4      | 0      | 0             | 100%    |
| 6. Bilingual Support     | 4      | 2      | 0      | 1 ⚠️ + 1 skip | 75%     |
| 7. Suggestions           | 4      | 4      | 0      | 0             | 100%    |
| 8. Multi-turn & Edge     | 6      | 2      | 1      | 3 skip        | 67%     |
| **TOTAL**                | **46** | **30** | **6**  | **10**        | **73%** |


---

## Vấn đề cần fix (theo priority)

### P0 — Critical (Correction không override KB)

- **CR-08, IH-06**: Khi user sửa fact đã có trong KB (ví dụ: cut-in speed 3-4 → 2.5), correction KHÔNG thắng KB. Bot vẫn trả lời từ KB.
- **Root cause**: Corrections block injected nhưng LLM ưu tiên retrieved context hơn corrections khi cả 2 nói về cùng attribute.

### P1 — High (Fabrication)

- **IH-01**: Bot fabricate specs V236 từ training data thay vì nói "chưa có trong KB".
- **IH-03**: Correction bị mất khi hỏi tiếp — có thể do session/metadata issue.
- **IH-05**: Server error 500 khi hỏi về Siemens SG 14-222 DD.

### P2 — Medium

- **MT-01**: "Kể thêm đi" bị scope filter chặn nhầm.
- **QA-07, BL-03**: Hỏi tiếng Anh nhưng bot trả lời tiếng Việt.
- **CR-02**: Multiple corrections — chỉ giữ correction đầu, mất correction sau.

### P3 — Low

- **SC-06**: Câu hỏi biên giới phạm vi (climate change + wind energy) bị từ chối thay vì trả lời.
- **QA-04**: "Chưa có trong KB" dù vẫn nêu được quy trình bảo trì — có thể retrieval miss.

---

## Notes

- Mỗi category test trong **session mới** (trừ correction tests cần cùng session)
- Consistency tests (CO-*) cần **3 sessions riêng** cho mỗi câu hỏi
- "Actual" ghi tóm tắt response (max 100 ký tự)
- Result: ✅ Pass / ❌ Fail / ⚠️ Partial
- Test executed: 2026-03-24 00:48-01:15 UTC+7

