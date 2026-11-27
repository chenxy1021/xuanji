# 来源与许可

本技能是开源项目 **ziwei-doushu**（https://github.com/Renhuai123/ziwei-doushu）的排盘能力的封装。
技能本身不含网络请求，不做数据上传，全部计算在本机完成。

## 代码

| 组件 | 来源 | 许可 |
|---|---|---|
| 排盘内核 `scripts/chart-core.mjs` | ziwei-doushu 的 `lib/ziwei/*`（安星、四化、亮度流派、格局识别、真太阳时、十二神）打包而成 | MIT，Copyright (c) 2026 紫微研究 |
| 同一文件内打包的 iztro | https://github.com/SylarLong/iztro | MIT |
| 同一文件内打包的 lunar-javascript | https://github.com/6tail/lunar-javascript | MIT |
| `scripts/paipan.mjs`、`scripts/render.mjs` | 为本技能新写的 CLI 与传统版式渲染 | MIT |

MIT 许可要求保留版权与许可声明，上述声明即为履行该义务。

## 语料

`references/quotes-ni.md` 摘自 ziwei-doushu 仓库 `docs/tianji-ziwei`（倪海厦先生《天纪》紫微斗数部分原话，全量 1848 条），
本技能收录其中 329 条节选，每条带讲次与时间戳以便回放核对，摘编不改原文。

- 原始音视频与讲授内容的权利归倪海厦先生及权利人所有。
- 该语料明确限定**非商用**：引用时请注明出处，不得用于商业出版或付费产品。
- 仓库数据集部分为 CC BY 4.0。

## 免责

紫微斗数属中国传统命理，本技能提供的是**倾向性分析与传统文化解读**，不是事实陈述，
不构成医疗、法律、投资或婚姻决策建议。使用者对自身决定负全部责任。
