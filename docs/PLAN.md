# 命理排盘与 AI 解读平台 · 项目计划

> 一个可切换多种术数体系的在线算命网站。前端 Vue 3，后端 Python (FastAPI + uv)，移动端自适应。
>
> **历史文档**：本文是最初的计划与里程碑，表中的「待接」「⏳」状态已被实际进度取代。
> 当前上线范围与完成度以 [`STATUS.md`](STATUS.md) 为准。

## 一、产品定位

**排盘交给代码，解读交给 AI。**

- 代码负责历法换算、干支、星曜、卦象等确定性计算，保证结果可复现、可核对
- AI 只负责在结构化命盘之上做解读，不参与排盘
- 同一套生辰输入，切换不同体系（八字 / 紫微 / 六爻 / 星座 / 塔罗 …）得到不同维度的结果

## 二、参考项目与许可边界

| 项目 | 许可 | 我们对它的使用方式 |
|---|---|---|
| [bazi-skill](https://github.com/jinchenma94/bazi-skill) | MIT | ✅ 直接 vendor 八字引擎（`backend/app/domains/bazi/_vendor_pai_pan.py`） |
| [ziwei-doushu](https://github.com/Renhuai123/ziwei-doushu) | MIT（数据 CC BY 4.0） | ✅ 可移植紫微排盘算法 |
| [taibu](https://github.com/hhszzzz/taibu) | core MIT / app AGPL | ✅ 借鉴模块架构；❌ 不搬应用层代码 |
| [mingyu](https://github.com/Brhiza/mingyu) | AGPL-3.0 | ❌ 仅参考产品思路 |
| [ziwei-chart](https://github.com/ziweiknows/ziwei-chart) | GPLv3 | ❌ 仅参考交互与可视化创意 |
| [MingLi-Bench](https://github.com/DestinyLinker/MingLi-Bench) | MIT | ✅ 数据模型与样例参考 |

## 三、MVP 范围（第一阶段）

| 体系 | 输入 | 输出 | 状态 |
|---|---|---|---|
| 八字 | 生辰 + 性别 + 地点 | 四柱、十神、藏干、神煞、大运、流年 | 🚧 引擎已就位（MIT vendor），待接 API |
| 紫微斗数 | 生辰 + 性别 | 十二宫、主辅星、四化、大限流年 | ⏳ 移植 ziwei-doushu 算法 |
| 六爻 | 起卦方式（铜钱/时间/数字） | 本卦、变卦、六亲六神、世应 | ⏳ 自研 |
| 星座 | 生辰 + 地点 | 太阳/月亮/上升、行星落座、相位 | ⏳ pyswisseph |
| 塔罗 | 牌阵 + 问题 | 抽牌 + 正逆位 + 牌义 | ⏳ 牌库自研 |

第二阶段（不在本阶段承诺）：奇门、大六壬、小六壬、梅花、合盘、择日、黄历。

## 四、里程碑

1. **M1 骨架**：前后端骨架、统一生辰输入模型、八字端到端跑通、移动端布局
2. **M2 多体系**：紫微 / 六爻 / 塔罗 / 星座 接入
3. **M3 AI 解读**：SSE 流式解读、知识库检索、解读历史
4. **M4 打磨**：分享卡片、暗色模式、性能与 SEO、部署

## 五、非目标（当前阶段）

- 不做用户支付与会员体系
- 不做原生 App（Web 自适应优先，后续可套 Capacitor）
- 不做社区、评论、命例广场
