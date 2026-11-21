"""解读提示词。

原则：排盘事实由代码给出，模型只做解释。提示词里明确禁止改写干支与星曜。
"""

from __future__ import annotations

SYSTEM_PROMPT = """你是一位严谨的中国传统命理研读者，具备八字、紫微斗数、六爻、西方占星与塔罗的知识。

工作要求：
1. 排盘结果由程序计算，是唯一事实来源。你绝不能改写、补算或推翻其中的干支、星曜、卦象、牌面。
2. 先复述关键结构化事实，再给出解读，让用户能核对。
3. 解读要具体到宫位/十神/行星/牌位，避免空泛套话。
4. 用平实中文，像一位耐心的老师，不用夸张营销语气，不做宿命论断言。
5. 不下死亡、疾病诊断、法律、投资的确定性结论；涉及健康、财务时提示「仅供参考」。
6. 命理属于传统文化范畴，请把它当作自我反思的镜子，而不是决定论。

输出使用 Markdown，小标题简洁。
"""

STYLE_HINTS = {
    "concise": "篇幅控制在 500 字以内，只讲最关键的 3 点。",
    "detailed": "篇幅可以到 1200 字，逐项展开，但不要重复。",
}


def build_messages(
    system: str,
    chart_text: str,
    chart_json: str,
    question: str | None = None,
    style: str = "concise",
    focus: list[str] | None = None,
) -> list[dict[str, str]]:
    parts = [
        f"体系：{system}",
        "",
        "## 排盘规范文本",
        chart_text.strip(),
        "",
        "## 结构化数据（供你引用，不要复述整段 JSON）",
        chart_json,
    ]
    if focus:
        parts += [
            "",
            "## 解读重点",
            "用户选择了这些方向：" + "、".join(focus),
            "请按上面的顺序组织小标题，每个方向都先引用对应盘面证据，再给出解读；"
            "未选中的方向只在确有盘面依据时用一句话带过。开头用两三句话交代整体格局。",
        ]
    if question:
        parts += ["", "## 用户问题", question.strip()]
    elif focus:
        parts += ["", "## 用户问题", "请围绕上述重点解读这张盘。"]
    else:
        parts += ["", "## 用户问题", "请对这张盘做一个整体解读。"]
    parts += ["", "## 表达要求", STYLE_HINTS.get(style, STYLE_HINTS["concise"])]
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(parts)},
    ]
