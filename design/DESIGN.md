# 玄机 · 设计规范（v1.0）

> 东方玄学 × 现代极简。让命盘像「一本装帧克制的书」，而不是「庙街门口的招牌」。
> 配套资产：`tokens.css`（变量）、`index.html`（390×844 移动端交互原型）。

---

## 一、设计定位

**一句话**：把复杂的命理结构，用安静、清晰、可信的排版呈现出来。

产品本质是「工具 + 阅读」：用户先填生辰（工具），再读命盘与解读（阅读）。因此界面必须做到两件事——**输入时零犹豫，读盘时零干扰**。

### 关键词

| 关键词 | 含义 | 落地手段 |
|---|---|---|
| 玄 | 有术数气息，但不装神弄鬼 | 衬线标题、干支大字、极淡的罗盘/经纬纹理 |
| 静 | 大面积留白，低饱和 | 纸白底、低对比描边、无重阴影 |
| 准 | 数据即权威，可核对 | 表格化排版、等宽数字、明确的校正明细 |
| 轻 | 移动优先，单手可操作 | 单列、底部主按钮、卡片化信息块 |

### 明确避免

- ❌ 金色渐变 + 龙凤纹理 + 大红大金的「风水罗盘风」
- ❌ 黑底血红、符咒笔刷的「阴森恐怖风」
- ❌ 玻璃拟态、霓虹光晕等与内容气质冲突的潮流特效
- ❌ 满天星斗动画、粒子背景（耗电、廉价、干扰阅读）

色彩上**不用金色作为主色**；金属感仅允许在「庙旺」标记等极小面积、低饱和的形式出现（用 `--color-tu` 土黄代替纯金）。

---

## 二、色彩系统

### 2.1 主色：玄青 `#1E6B5E`

取「青」——东方五行之色，冷静、有古意，又不像墨绿那样沉闷。承担所有可交互态：主按钮、选中态、命宫高亮、链接。

### 2.2 辅色：朱砂 `#B4402F`

仅用于**需要被看见的少数场景**：warning、四化「忌」、破格提示、危险操作。全站占比 < 5%。

### 2.3 色板

| Token | 亮色 | 用途 | 对比度 |
|---|---|---|---|
| `--color-bg` | `#F5F3EE` | 页面底色（宣纸） | — |
| `--color-surface` | `#FFFFFF` | 卡片、表单容器 | — |
| `--color-surface-2` | `#FAF8F4` | 卡内分区、表头 | — |
| `--color-border` | `#E6E0D4` | 常规描边、分隔线 | — |
| `--color-border-strong` | `#D2CABB` | 输入框、可交互边界 | — |
| `--color-text` | `#1F1D18` | 主文字（墨） | 15.2:1 on bg |
| `--color-text-secondary` | `#5C564B` | 说明、副标题 | 6.6:1 on bg |
| `--color-text-muted` | `#6F6A5E` | 标签、辅助信息 | 4.9:1 on bg |
| `--color-primary` | `#1E6B5E` | 主交互 | 6.3:1 on white |
| `--color-primary-soft` | `#E3EFEB` | 选中底、标签底 | — |
| `--color-accent` | `#B4402F` | 警示、忌 | 5.7:1 on white |
| `--color-success` | `#2A7049` | 吉、成功 | 5.2:1 on soft |
| `--color-warning` | `#8A6113` | 校正提示（偏黄褐，不用亮黄） | 4.8:1 on soft |
| `--color-danger` | `#B4402F` | 错误 | 4.9:1 on soft |

### 2.4 深色主题「墨夜」

不是纯黑，也不是纯灰，是**偏暖的墨绿黑** `#121310`，卡片 `#1A1C17`。主色反转为 `#5FBFAB`（对 `#121310` 为 8.5:1），保证暗背景下依然能「亮而不刺」。

切换方式：

```js
document.documentElement.dataset.theme = 'dark' // 或删除该属性回到亮色
```

### 2.5 五行色（仅用于标签/图例，不做大面积）

木 `#3F7D5C` · 火 `#B4573D` · 土 `#97723A` · 金 `#6F757F` · 水 `#39688A`
每色均配套 `-soft` 浅底版本，用于 chip。

### 2.6 四化色（紫微专用）

禄 `#2A7049`（绿）· 权 `#65559A`（紫）· 科 `#35618F`（蓝）· 忌 `#B4402F`（朱砂）。
规则：**只染字与 1px 描边，不填实心底**，否则 12 宫格里会变成调色盘。

---

## 三、字体与排印

### 3.1 字体栈

```css
--font-sans: -apple-system, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
             "Noto Sans SC", sans-serif;
--font-serif: "Songti SC", "Source Han Serif SC", "Noto Serif SC", "SimSun", serif;
```

- **正文、表单、按钮**：无衬线，保证小字号清晰
- **衬线仅用于**：品牌名、页面大标题、四柱天干地支、宫名。用衬线制造「书卷气」，用无衬线保证可用性
- 数字（大运年龄、年份）用 `font-variant-numeric: tabular-nums` 对齐

### 3.2 字号阶梯

| Token | 值 | 用途 |
|---|---|---|
| `--text-xs` | 12px | 藏干、四化角标、脚注（**下限，不得更小**） |
| `--text-sm` | 13px | 辅助说明、表格次级信息 |
| `--text-base` | 15px | 正文 |
| `--text-md` | 16px | 表单输入（≥16px 可避免 iOS 聚焦缩放） |
| `--text-lg` | 18px | 区块小标题 |
| `--text-xl` | 22px | 卡片标题 |
| `--text-2xl` | 26px | 页面标题 |
| `--text-3xl` | 32px | 命盘干支大字 |

行高：标题 1.25，正文 1.6，长解读文 1.75。中文字距保持默认，**不要加 letter-spacing**（会破坏汉字方块感）。

### 3.3 字重

只用 400 / 500 / 600。中文 600 已足够强调，避免 700 在 iOS 上发糊。

---

## 四、间距、圆角、阴影

- **基准 4px**：`--space-1` = 4px … `--space-16` = 64px
- 页面左右边距：**16px**（`--space-4`）；卡片内边距 **16px**；区块间距 **24px**
- 圆角：输入框/按钮 `10px`，卡片 `14px`，弹层 `20px`，chip `999px`
- 阴影克制：默认卡片用 `--shadow-xs`（1px 描边感），浮层才用 `--shadow-md`
- 栅格：移动端单列；`≥768px` 内容宽 `480px` 居中，双栏仅用于结果页「命盘 | 解读」

---

## 五、组件规范

### 5.1 按钮

| 类型 | 样式 | 用途 |
|---|---|---|
| Primary | 玄青实底 + 白字，高 48px，圆角 10px（`--radius-md`），全宽 | 页面唯一主操作（开始排盘） |
| Secondary | 白底 + `--color-border-strong` 1px + 主色字 | 次级操作（重新解读） |
| Ghost | 无底无边，主色字 | 行内操作（切换、查看全部） |
| Danger | 朱砂字 + 朱砂浅底 | 删除记录 |

状态：`hover` 亮度 −8%，`active` 缩放 0.98（`--dur-fast`），`disabled` 40% 透明度且 `cursor: not-allowed`。加载中：左侧 16px 环形进度，文案不变，禁用重复点击。

### 5.2 卡片

- 底 `--color-surface`，1px `--color-border`，圆角 14px，无阴影（或 `--shadow-xs`）
- 可点击卡片：按下时 `background: --color-surface-2`；禁用态整体 `opacity: .5` + 「开发中」徽标
- 卡片内标题 15–17px / 500，描述 13px / `--color-text-muted`，最多两行省略

### 5.3 表单控件

- 高度 **48px**（触控友好），内边距 12px 16px，字号 16px
- 边框 `--color-border-strong`，聚焦时边框转 `--color-primary` + `box-shadow: 0 0 0 3px --color-primary-soft`
- 原生 `select` 保留（移动端滚轮体验最好），仅做外观统一，必须保留右侧箭头
- 开关（Switch）：轨道 44×26px，开启 `--color-primary`，整行可点（热区 ≥44px）
- 分组标签 13px / `--color-text-secondary`，与控件间距 8px
- 校验错误：控件边框转 `--color-danger`，下方 12px 朱砂文案，**不要只靠颜色**，需带「!」图标

### 5.4 标签 / Chip

- 高度 26–28px，水平内边距 10px，圆角 pill，字号 12–13px
- 三类：中性（灰底）、体系色（五行 soft 底 + 对应文字色）、状态（开发中 = 虚线描边 + muted）
- 可点击的 chip 高度提升到 36px；选中态为玄青 soft 底 + 主色字 + 1px 主色描边

### 5.5 表格（八字四柱）

- 表头 12px muted，居中；正文干支 28–32px 衬线
- 单元格最小宽 **72px**，四柱刚好铺满 390px；超出时容器 `overflow-x: auto` 且 `-webkit-overflow-scrolling: touch`
- 横向滚动必须给**视觉提示**：右缘 24px 渐变遮罩 + 首屏可见「左右滑动」小字，滚到末尾时遮罩消失
- 日柱列加 `--color-primary-soft` 底 + 顶部 2px 主色条，标注「日主」
- 表体用 `--color-border` 分隔，不用斑马纹

### 5.6 紫微十二宫（核心组件）

固定 **4×4 环形布局**，中心 2×2 合并放基本信息（性别、农历、五行局、命主/身主）。

```
巳 | 午 | 未 | 申
辰 |  ╳    | 酉
卯 |  ╳    | 戌
寅 | 丑 | 子 | 亥
```

- 单宫宽 ≈ `(屏宽 − 32 − 2×gap) / 4`，390px 下约 84px；`gap: 2px`，用 1px 边框共用感
- 宫内层级：宫名（12px，左上）+ 大限（11px，右上，muted）→ 主星（17px 衬线，1–2 字一行，最多 2 颗）→ 辅星（11px，可换行，最多显示 3 个，多出显示 `+n`）→ 四化（右上角 12px 方标：禄/权/科/忌）
- 庙旺用 11px 上标紧跟星名，只标「庙/旺/陷」，不标全部等级
- **命宫**：`--color-primary-soft` 底 + 1.5px 主色内描边 + 左上角「命」小印；**身宫**：右上角一个 3px 圆点
- 小屏可读性兜底：
  1. 宫格内文字不小于 11px（含大限、亮度、四化角标），主星不小于 16px
  2. 点击任一宫 → 底部抽屉展示该宫全量星曜与四化（避免格子内塞满）
  3. 提供**「宫格 / 列表」切换**：列表模式每宫一行、可滚动，供小屏或读屏用户
  4. 禁止在格内放长文本；宫名用简称（兄、夫、子、财、疾、迁、友、官、田、福、父）

### 5.7 空状态

居中，上下 48px。一个 48px 线性图标（20% 透明度）+ 一句话说明（14px muted）+ 一个 Ghost 按钮。文案示例：「还没有排盘记录 / 去排一张」。

### 5.8 加载态

- 首屏骨架屏：矩形块，`--color-surface-2`，1.4s 呼吸（opacity .5→1）
- 局部加载：按钮内环形 spinner
- **排盘等待**用专门的仪式动效（见 6.2），时长上限 1.2s，超时显示「正在计算…」文案

### 5.9 Toast

底部距 TabBar 上 16px，深底浅字（`--color-surface-inverse`），圆角 10px，2.4s 自动消失，同一时刻仅一条。

---

## 六、动效原则

### 6.1 基本参数

- 时长：`120ms`（按钮反馈）/ `180ms`（常规切换）/ `240ms`（页面转场）/ `320ms`（弹层）
- 缓动：进场 `--ease-out`（快起慢收），退场 `--ease-in-out`；弹层/抽屉用 `--ease-spring` 轻微过冲
- 只动 `transform` 与 `opacity`，不动 `width/height/top/left`
- 一个视图内**只允许一个主运动**，避免多处同时动画

### 6.2 起盘动效（唯一允许「炫」的地方）

点击「开始排盘」→ 全屏遮罩（`--color-overlay`）+ 中央 160–170px 罗盘：外圈十二地支顺时针缓转（9s/圈），内圈虚线环反向（14s/圈），中心阴阳核自转（3.2s/圈），下方一行「正在排盘 / 定十二宫 · 布主辅星 · 起大运」。总时长 600–1000ms（原型取 1000ms），随后结果页自下而上 6–12px 淡入。
若接口返回更快，动效**最短保留 600ms**（否则像闪屏）；若更慢，圆环持续但停止文字轮换，改为「正在计算…」。

### 6.3 阅读类动效

AI 解读流式输出：新文本 `opacity 0→1`，不做逐字放大/弹跳。光标为 2px 主色竖线闪烁（1s）。

### 6.4 降级

`prefers-reduced-motion: reduce` 时所有时长变 1ms（tokens.css 已处理变量），排盘改为静态进度文案。

---

## 七、无障碍

| 项 | 要求 |
|---|---|
| 对比度 | 正文 ≥ 4.5:1，大字（≥18px/600）≥ 3:1；已按此校色（见 2.3 表） |
| 触控热区 | 所有可点元素 ≥ 44×44px，视觉可小、热区必须够（用 padding 或伪元素扩展） |
| 字号下限 | 常规界面 12px，紫微宫格等极密布局 11px；正文 15px 起；系统字号放大 200% 时不横向溢出 |
| 颜色不是唯一信息 | 四化除颜色外必须有「禄/权/科/忌」文字；错误除红色外必有图标 |
| 焦点可见 | `:focus-visible` 显示 2px 主色描边 + 2px 偏移，不用 `outline: none` |
| 语义 | 宫格用 `role="grid"`/`aria-label="十二宫"`；表格用真 `<table>` + `<th scope>` |
| 动效 | 尊重 `prefers-reduced-motion` |
| 暗色 | 独立调色，不是简单反色；深色下不使用纯白文字（用 `#ECE9DF`） |

---

## 八、给前端的接入建议

1. **先接 token，再写组件**：把 `tokens.css` 放在 `src/styles/tokens.css`，在 `main.ts` 或 `style.css` 首行 `@import`。
2. **Tailwind 映射**（`tailwind.config.ts`）：

```ts
theme: {
  extend: {
    colors: {
      bg: 'var(--color-bg)',
      surface: 'var(--color-surface)',
      line: 'var(--color-border)',
      ink: 'var(--color-text)',
      'ink-2': 'var(--color-text-secondary)',
      'ink-3': 'var(--color-text-muted)',
      primary: { DEFAULT: 'var(--color-primary)', soft: 'var(--color-primary-soft)' },
      accent: 'var(--color-accent)',
    },
    borderRadius: { md: 'var(--radius-md)', lg: 'var(--radius-lg)', xl: 'var(--radius-xl)' },
    spacing: { 4: 'var(--space-4)' }, // 可选，直接用 4px 倍数即可
  }
}
```

   > 注意：用 `var()` 而非固定色值，才能让 `data-theme="dark"` 一处生效。若 Tailwind 需要对透明度做修饰（`bg-primary/10`），改用 `rgb(var(--color-primary-rgb) / <alpha-value>)` 形式，或直接用 `--color-primary-soft`。

3. **主题切换**：`settings` store 存 `light | dark | system`，写 `document.documentElement.dataset.theme`；`system` 时监听 `prefers-color-scheme`。
4. **别自建色板**：新增颜色先加进 `tokens.css`，组件里只引用变量。
5. **组件落地顺序**：`Button` → `Field/Select/Switch` → `Card/Chip` → `PillarTable` → `ZiweiGrid`。
6. `index.html` 里的 CSS 是与 tokens 配套的参考实现，可直接抄成 Vue 组件样式（类名如 `.card` `.chip` `.pillar-table` 已按模块划分）。

---

## 九、原型文件

`design/index.html` —— 单文件、可离线双击打开：

- 390×844 手机视口，四屏切换（首页 / 起盘 / 八字结果 / 紫微结果），右上角「明/暗」切换主题；也可用 `index.html?screen=bazi|ziwei` 直接打开某一屏
- 演示了：时辰实时提示、真太阳时开关、城市联想、排盘过渡动效、八字宽表横向滚动遮罩、紫微宫格 + 点击宫位详情 + 宫格/列表切换、AI 流式打字、未配置 Key 的错误态

> 原型仅用于对齐视觉与交互，**不含真实接口**；数据为固定样例。
