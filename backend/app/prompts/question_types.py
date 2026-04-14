"""Type-specific prompt instructions for different question categories.

Each instruction is ~100-150 tokens and guides the LLM on format, depth,
and structure appropriate for that question type. Injected into the system
prompt BEFORE the context block.
"""

QUESTION_TYPE_INSTRUCTIONS = {
    "STRUCTURE": {
        "en": (
            "[RESPONSE MODE: STRUCTURE / DEFINITION]\n"
            "This question asks about a component or system structure. You MUST:\n"
            "- Describe the component: what it is, its main function, its position in the turbine\n"
            "- List ALL sub-components mentioned in context, each with 1-2 sentences explaining its role\n"
            "- Include specific technical data from context (dimensions, weight, power rating, materials)\n"
            "- End with the component's importance in the overall system\n"
            "Prioritize DEPTH over BREADTH. Answer at least 300 words if context is rich enough."
        ),
        "vi": (
            "[CHẾ ĐỘ TRẢ LỜI: CẤU TRÚC / ĐỊNH NGHĨA]\n"
            "Câu hỏi này yêu cầu giải thích chi tiết về thành phần/hệ thống. Bạn PHẢI:\n"
            "- Mô tả thành phần: nó là gì, chức năng chính, vị trí trong tuabin\n"
            "- Liệt kê TẤT CẢ bộ phận con mà context đề cập, mỗi bộ phận kèm 1-2 câu giải thích vai trò\n"
            "- Nêu số liệu kỹ thuật cụ thể từ context (kích thước, trọng lượng, công suất, vật liệu)\n"
            "- Kết thúc bằng tầm quan trọng/vai trò trong hệ thống tổng thể\n"
            "Ưu tiên ĐỘ SÂU hơn ĐỘ RỘNG. Trả lời ít nhất 300 từ nếu context đủ phong phú."
        ),
    },
    "PRINCIPLE": {
        "en": (
            "[RESPONSE MODE: OPERATING PRINCIPLE]\n"
            "This question asks how something works. You MUST:\n"
            "- Explain the FULL PROCESS from start to end: energy/signal flows from where → through what → produces what\n"
            "- Include mathematical formulas (use LaTeX) if context provides them\n"
            "- Provide specific technical data (ratios, speeds, efficiency, parameter ranges)\n"
            "- Explain WHY the design works this way (engineering advantages)\n"
            "Use a Mermaid diagram if the process has multiple sequential steps."
        ),
        "vi": (
            "[CHẾ ĐỘ TRẢ LỜI: NGUYÊN LÝ HOẠT ĐỘNG]\n"
            "Câu hỏi này yêu cầu giải thích nguyên lý hoạt động. Bạn PHẢI:\n"
            "- Giải thích QUY TRÌNH từ đầu đến cuối: năng lượng/tín hiệu đi từ đâu → qua đâu → ra gì\n"
            "- Nêu công thức toán học (dùng LaTeX) nếu context có\n"
            "- Cung cấp số liệu kỹ thuật cụ thể (tỷ lệ, tốc độ, hiệu suất, dải thông số)\n"
            "- Giải thích TẠI SAO thiết kế như vậy (ưu điểm kỹ thuật)\n"
            "Dùng sơ đồ Mermaid nếu quy trình có nhiều bước tuần tự."
        ),
    },
    "PROCEDURE": {
        "en": (
            "[RESPONSE MODE: PROCEDURE / MAINTENANCE]\n"
            "This question asks about a procedure or process. You MUST:\n"
            "- List steps in NUMBERED ORDER by time sequence\n"
            "- Each step: specific action + tools/equipment needed if mentioned in context\n"
            "- State FREQUENCY of execution (daily/weekly/monthly/yearly) if context provides it\n"
            "- Mark SAFETY WARNINGS at dangerous steps\n"
            "- Mention applicable technical standards (IEC, AWEA...) if context provides them"
        ),
        "vi": (
            "[CHẾ ĐỘ TRẢ LỜI: QUY TRÌNH / BẢO TRÌ]\n"
            "Câu hỏi này yêu cầu mô tả quy trình. Bạn PHẢI:\n"
            "- Liệt kê các bước ĐÁNH SỐ theo thứ tự thời gian\n"
            "- Mỗi bước: hành động cụ thể + dụng cụ/thiết bị cần thiết nếu context đề cập\n"
            "- Ghi rõ TẦN SUẤT thực hiện (hàng ngày/tuần/tháng/năm) nếu context có\n"
            "- CẢNH BÁO AN TOÀN ở các bước nguy hiểm\n"
            "- Nêu tiêu chuẩn kỹ thuật áp dụng (IEC, AWEA...) nếu context có"
        ),
    },
    "COMPARISON": {
        "en": (
            "[RESPONSE MODE: COMPARISON]\n"
            "This question asks for a comparison. You MUST:\n"
            "- Create a COMPARISON TABLE with at least 4-5 criteria\n"
            "- Each criterion: briefly explain the difference, not just list values\n"
            "- State ADVANTAGES and DISADVANTAGES of each option clearly\n"
            "- Conclude: which option suits which use case\n"
            "Use markdown table for readability."
        ),
        "vi": (
            "[CHẾ ĐỘ TRẢ LỜI: SO SÁNH]\n"
            "Câu hỏi này yêu cầu so sánh. Bạn PHẢI:\n"
            "- Tạo BẢNG SO SÁNH với ít nhất 4-5 tiêu chí\n"
            "- Mỗi tiêu chí: giải thích ngắn gọn sự khác biệt, không chỉ ghi giá trị\n"
            "- Nêu rõ ƯU ĐIỂM và NHƯỢC ĐIỂM của mỗi phương án\n"
            "- Kết luận: trường hợp nào nên dùng phương án nào\n"
            "Dùng markdown table cho dễ đọc."
        ),
    },
    "TROUBLESHOOT": {
        "en": (
            "[RESPONSE MODE: TROUBLESHOOTING]\n"
            "This question asks about fault handling. You MUST:\n"
            "- Describe SYMPTOMS and possible ROOT CAUSES\n"
            "- List DIAGNOSTIC steps from simple to complex\n"
            "- Propose specific SOLUTIONS for each cause\n"
            "- State URGENCY level (can the turbine keep running, or must it stop immediately?)\n"
            "- Include SAFETY WARNINGS (high voltage, height, weather conditions)"
        ),
        "vi": (
            "[CHẾ ĐỘ TRẢ LỜI: XỬ LÝ SỰ CỐ]\n"
            "Câu hỏi này yêu cầu xử lý sự cố. Bạn PHẢI:\n"
            "- Mô tả TRIỆU CHỨNG và NGUYÊN NHÂN có thể\n"
            "- Liệt kê bước CHẨN ĐOÁN theo thứ tự từ đơn giản đến phức tạp\n"
            "- Đề xuất GIẢI PHÁP cụ thể cho từng nguyên nhân\n"
            "- Nêu độ KHẨN CẤP (tuabin có thể tiếp tục chạy không, hay phải dừng ngay?)\n"
            "- CẢNH BÁO AN TOÀN đặc biệt (điện áp cao, độ cao, thời tiết)"
        ),
    },
    "GENERAL": {
        "en": "",
        "vi": "",
    },
}


def get_question_type_instruction(question_type: str, language: str) -> str:
    """Get the type-specific prompt instruction for injection into system prompt.

    Args:
        question_type: One of STRUCTURE, PRINCIPLE, PROCEDURE, COMPARISON, TROUBLESHOOT, GENERAL.
        language: "en" or "vi".

    Returns:
        The instruction string, or empty string for GENERAL type.
    """
    type_dict = QUESTION_TYPE_INSTRUCTIONS.get(question_type, QUESTION_TYPE_INSTRUCTIONS["GENERAL"])
    return type_dict.get(language, type_dict.get("en", ""))
