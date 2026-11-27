"""MBTI 题库与 16 型简表。

这是通俗性格测评，不是心理诊断工具；题库为自撰，未使用受版权保护的量表。
"""

from __future__ import annotations

SCALE = {
    "min": 1,
    "max": 5,
    "labels": ["非常不同意", "不同意", "说不好", "同意", "非常同意"],
}

DIMENSIONS: list[dict[str, str]] = [
    {"key": "EI", "left": "E", "right": "I", "left_name": "外向", "right_name": "内向"},
    {"key": "SN", "left": "S", "right": "N", "left_name": "实感", "right_name": "直觉"},
    {"key": "TF", "left": "T", "right": "F", "left_name": "思考", "right_name": "情感"},
    {"key": "JP", "left": "J", "right": "P", "left_name": "判断", "right_name": "知觉"},
]

# pole = 同意该题时倾向的那一极
QUESTIONS: list[dict[str, str]] = [
    {"id": "q1", "dim": "EI", "pole": "E", "text": "聚会上我通常会主动和陌生人搭话。"},
    {"id": "q2", "dim": "EI", "pole": "I", "text": "独处一段时间能让我恢复精力。"},
    {"id": "q3", "dim": "EI", "pole": "E", "text": "我喜欢边想边说，而不是先想清楚再开口。"},
    {"id": "q4", "dim": "EI", "pole": "I", "text": "人多的场合会让我消耗得很快。"},
    {"id": "q5", "dim": "EI", "pole": "E", "text": "和别人讨论会帮我理清思路。"},
    {"id": "q6", "dim": "EI", "pole": "I", "text": "周末我更愿意待在家里做自己的事。"},
    {"id": "q7", "dim": "EI", "pole": "E", "text": "认识新朋友让我感到兴奋。"},
    {"id": "q8", "dim": "EI", "pole": "I", "text": "我更喜欢和少数熟人深聊，而不是认识很多新面孔。"},
    {"id": "q9", "dim": "SN", "pole": "S", "text": "我更关注眼前具体的事实，而不是未来的可能性。"},
    {"id": "q10", "dim": "SN", "pole": "N", "text": "我常去想事情背后的深层含义。"},
    {"id": "q11", "dim": "SN", "pole": "S", "text": "做事时我更信任经验和被验证过的方法。"},
    {"id": "q12", "dim": "SN", "pole": "N", "text": "我喜欢讨论抽象概念和理论。"},
    {"id": "q13", "dim": "SN", "pole": "S", "text": "我注意细节，能记住具体的数字和描述。"},
    {"id": "q14", "dim": "SN", "pole": "N", "text": "我常常同时想到很多种可能。"},
    {"id": "q15", "dim": "SN", "pole": "S", "text": "有明确步骤的说明会让我安心。"},
    {"id": "q16", "dim": "SN", "pole": "N", "text": "我容易从一件小事联想到更远的图景。"},
    {"id": "q17", "dim": "TF", "pole": "T", "text": "做决定时，我优先考虑逻辑是否成立。"},
    {"id": "q18", "dim": "TF", "pole": "F", "text": "朋友难过时，我先共情而不是给建议。"},
    {"id": "q19", "dim": "TF", "pole": "T", "text": "我能比较直接地指出别人的错误。"},
    {"id": "q20", "dim": "TF", "pole": "F", "text": "团队氛围比结果更让我在意。"},
    {"id": "q21", "dim": "TF", "pole": "T", "text": "我倾向用客观标准评价一件事。"},
    {"id": "q22", "dim": "TF", "pole": "F", "text": "我容易被别人的情绪影响。"},
    {"id": "q23", "dim": "TF", "pole": "T", "text": "争论时我更在意谁的道理站得住。"},
    {"id": "q24", "dim": "TF", "pole": "F", "text": "做重要决定时，我会先考虑它对身边人的影响。"},
    {"id": "q25", "dim": "JP", "pole": "J", "text": "我喜欢提前做好计划再行动。"},
    {"id": "q26", "dim": "JP", "pole": "P", "text": "临时改变计划会让我觉得有趣。"},
    {"id": "q27", "dim": "JP", "pole": "J", "text": "待办清单能让我安心。"},
    {"id": "q28", "dim": "JP", "pole": "P", "text": "我常拖到最后一刻才完成任务。"},
    {"id": "q29", "dim": "JP", "pole": "J", "text": "我倾向把事情尽快定下来。"},
    {"id": "q30", "dim": "JP", "pole": "P", "text": "保留多种选择比早早决定更舒服。"},
    {"id": "q31", "dim": "JP", "pole": "J", "text": "我的东西通常摆放得比较有条理。"},
    {"id": "q32", "dim": "JP", "pole": "P", "text": "我更喜欢随性安排，而不是把日程排满。"},
]

# ---- 英文文案（前端中英切换用；中文为默认语言）----

SCALE_EN = {
    "min": 1,
    "max": 5,
    "labels": ["Strongly disagree", "Disagree", "Not sure", "Agree", "Strongly agree"],
}

DIMENSIONS_EN: list[dict[str, str]] = [
    {"key": "EI", "left": "E", "right": "I", "left_name": "Extraverted", "right_name": "Introverted"},
    {"key": "SN", "left": "S", "right": "N", "left_name": "Sensing", "right_name": "Intuitive"},
    {"key": "TF", "left": "T", "right": "F", "left_name": "Thinking", "right_name": "Feeling"},
    {"key": "JP", "left": "J", "right": "P", "left_name": "Judging", "right_name": "Perceiving"},
]

# 与 QUESTIONS 一一对应的英文题干（键为题目 id，顺序与文案都以此表为准）
QUESTION_TEXT_EN: dict[str, str] = {
    "q1": "At gatherings I usually start conversations with strangers.",
    "q2": "Spending time alone restores my energy.",
    "q3": "I like to think out loud rather than work it out before I speak.",
    "q4": "Crowded places drain me quickly.",
    "q5": "Talking things over with others helps me clarify my thoughts.",
    "q6": "On weekends I would rather stay home doing my own things.",
    "q7": "Meeting new people makes me excited.",
    "q8": "I prefer deep talks with a few close friends over meeting many new faces.",
    "q9": "I pay more attention to concrete facts in front of me than to future possibilities.",
    "q10": "I often think about the deeper meaning behind things.",
    "q11": "I trust experience and proven methods when I get things done.",
    "q12": "I enjoy discussing abstract ideas and theories.",
    "q13": "I notice details and remember specific numbers and descriptions.",
    "q14": "I often see many possibilities at the same time.",
    "q15": "Clear step-by-step instructions put me at ease.",
    "q16": "A small detail easily leads me to a bigger picture.",
    "q17": "When deciding, I first check whether the logic holds.",
    "q18": "When a friend is upset, I sit with their feeling before giving advice.",
    "q19": "I can point out other people's mistakes quite directly.",
    "q20": "Team atmosphere matters to me more than the result.",
    "q21": "I tend to judge things by objective standards.",
    "q22": "I am easily affected by other people's moods.",
    "q23": "In an argument I care more about whose reasoning holds up.",
    "q24": "Before a big decision I first consider how it affects people close to me.",
    "q25": "I like to plan ahead before taking action.",
    "q26": "Last-minute changes to a plan feel interesting to me.",
    "q27": "A to-do list puts me at ease.",
    "q28": "I often put tasks off until the last moment.",
    "q29": "I prefer to settle things as soon as possible.",
    "q30": "Keeping options open feels better than deciding early.",
    "q31": "My things are usually kept in order.",
    "q32": "I prefer going with the flow over filling my schedule.",
}

TYPES: dict[str, dict[str, object]] = {
    "ISTJ": {
        "name": "检查者",
        "summary": "重秩序、讲信用，习惯用已验证的方法把事情做扎实。",
        "strengths": ["可靠", "注重细节", "执行稳定"],
        "blind_spots": ["不易接受新方法", "表达情绪偏少", "容易过度承担"],
        "fit": "流程清晰、有明确标准的环境",
    },
    "ISFJ": {
        "name": "守卫者",
        "summary": "温和细致，习惯先照顾身边人的需要，再考虑自己。",
        "strengths": ["体贴", "有耐心", "记忆力好"],
        "blind_spots": ["不擅长拒绝", "容易委屈自己", "变化面前偏被动"],
        "fit": "服务、教育、医护等需要长期陪伴的领域",
    },
    "INFJ": {
        "name": "提倡者",
        "summary": "对人的动机敏感，心里有一套想长期坚持的价值。",
        "strengths": ["洞察力强", "有理想", "善于倾听"],
        "blind_spots": ["容易内耗", "理想与现实落差大", "过度自省"],
        "fit": "咨询、写作、公益等能投入意义的领域",
    },
    "INTJ": {
        "name": "建筑师",
        "summary": "习惯先在脑子里建模型，再按自己的路径推进。",
        "strengths": ["战略眼光", "独立", "学习快"],
        "blind_spots": ["显得疏离", "不耐烦低效", "忽略他人感受"],
        "fit": "研究、架构、战略规划",
    },
    "ISTP": {
        "name": "鉴赏家",
        "summary": "动手能力强，遇到问题先拆开看清楚再说。",
        "strengths": ["冷静", "实操强", "应变快"],
        "blind_spots": ["不喜欢长期承诺", "表达偏少", "容易临时起意"],
        "fit": "工程、机械、应急与现场类工作",
    },
    "ISFP": {
        "name": "探险家",
        "summary": "对美和感受敏锐，更喜欢用行动而不是语言表达。",
        "strengths": ["审美", "真诚", "随和"],
        "blind_spots": ["回避冲突", "计划性弱", "容易被情绪带走"],
        "fit": "设计、手作、艺术与自由职业",
    },
    "INFP": {
        "name": "调停者",
        "summary": "内心有一套价值排序，重视真实多过效率。",
        "strengths": ["共情", "创造力", "忠于价值"],
        "blind_spots": ["执行拖延", "过度理想化", "不擅长争抢"],
        "fit": "创作、心理、教育等自主性高的领域",
    },
    "INTP": {
        "name": "逻辑学家",
        "summary": "喜欢追问原理，享受把复杂问题拆成结构的过程。",
        "strengths": ["分析力", "好奇", "独立判断"],
        "blind_spots": ["落地慢", "忽略人际", "容易半途转向"],
        "fit": "科研、算法、产品分析",
    },
    "ESTP": {
        "name": "企业家",
        "summary": "反应快、敢试，习惯在真实场景里边做边调。",
        "strengths": ["行动力", "谈判", "抗压"],
        "blind_spots": ["耐心不足", "风险偏好高", "容易忽略长期"],
        "fit": "销售、创业、现场运营",
    },
    "ESFP": {
        "name": "表演者",
        "summary": "能量外放，善于把气氛带起来，也更活在当下。",
        "strengths": ["感染力", "适应力", "亲和"],
        "blind_spots": ["规划不足", "回避沉重话题", "易冲动消费"],
        "fit": "市场、活动、内容与表演",
    },
    "ENFP": {
        "name": "竞选者",
        "summary": "点子多、热情足，容易被新的可能性点亮。",
        "strengths": ["创意", "感染力", "善于连接人"],
        "blind_spots": ["收尾困难", "注意力分散", "情绪起伏"],
        "fit": "品牌、内容、培训与早期项目",
    },
    "ENTP": {
        "name": "辩论家",
        "summary": "喜欢挑战既有说法，享受把问题重新定义。",
        "strengths": ["思辨", "快速学习", "应变"],
        "blind_spots": ["争辩上瘾", "执行不细", "容易得罪人"],
        "fit": "咨询、产品、创业与创新岗位",
    },
    "ESTJ": {
        "name": "总经理",
        "summary": "目标清楚、推进有力，习惯把混乱整理成秩序。",
        "strengths": ["组织力", "负责", "决断"],
        "blind_spots": ["偏强硬", "不耐情绪", "容易僵化"],
        "fit": "管理、运营、项目管理",
    },
    "ESFJ": {
        "name": "执政官",
        "summary": "重视关系与归属，愿意为团队的稳定付出。",
        "strengths": ["协调", "照顾他人", "可靠"],
        "blind_spots": ["在意评价", "回避冲突", "易过度付出"],
        "fit": "人力、教育、客户成功",
    },
    "ENFJ": {
        "name": "主人公",
        "summary": "擅长看见别人的潜力，并愿意推着大家一起往前走。",
        "strengths": ["鼓舞他人", "表达", "组织"],
        "blind_spots": ["揽事过多", "忽略自身需要", "对批评敏感"],
        "fit": "管理、培训、公共表达",
    },
    "ENTJ": {
        "name": "指挥官",
        "summary": "目标导向，习惯快速定方向并调动资源推进。",
        "strengths": ["统筹", "决断", "抗压"],
        "blind_spots": ["强势", "忽略情绪", "对慢节奏不耐"],
        "fit": "高管、战略、创业",
    },
}
