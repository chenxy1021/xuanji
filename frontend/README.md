# 命理排盘前端

Vue 3 + TypeScript + Vite + Vue Router + Pinia + Tailwind CSS v4，移动优先。

## 启动

先起后端（默认 `http://127.0.0.1:8000`）：

```bash
cd ../backend && uv run uvicorn app.main:app --port 8000
```

再起前端：

```bash
npm install
npm run dev        # http://localhost:5173 ，/api 自动代理到 127.0.0.1:8000
```

后端地址不同时用环境变量覆盖：`SM_API_TARGET=http://host:port npm run dev`。

## 检查与构建

```bash
npx vue-tsc --noEmit   # 类型检查
npm run build          # vue-tsc -b && vite build → dist/
```

## 目录

```
src/
├─ main.ts / App.vue
├─ styles.css            Tailwind v4 接入 + @theme 映射到 token
├─ styles/tokens.css     设计令牌，唯一色板来源（明暗走 data-theme="dark"）
├─ router/index.ts       /  /chart/:system  /result  /history  /settings
├─ api/
│  ├─ client.ts          fetch 封装、SSE 流解析（POST /interpret）
│  └─ types.ts           与后端 HTTP 契约对应的类型
├─ stores/               birth（当前生辰，本地持久化）/ charts（当前结果 + 历史）/ settings（主题）
├─ lib/                  shichen.ts（时辰换算与提示）、storage.ts（localStorage 工具）
├─ components/
│  ├─ layout/            AppHeader、TabBar（移动端底部导航）
│  ├─ birth/             BirthForm、PlacePicker（走 /geo/cities 搜索）、TarotForm、LiuyaoForm
│  ├─ chart/             BaziChart / ZiweiChart（4×4 环形十二宫）/ TarotSpread / LiuyaoChart / SynastryChart，InterpretPanel（AI 流式解读）
│  └─ SystemCard.vue     首页体系卡片
└─ views/                Home / Chart / Result / History / Settings
```

## 说明

- 所有请求走相对路径 `/api/v1/...`，由 Vite 代理；前端不写死后端地址。
- 未登录时排盘结果与生辰只存在 `localStorage`（历史最多 50 条），不上传第三方；登录后按账号存服务端。
- AI 解读用个人配置（浏览器内）或本站默认 / `SM_LLM_API_KEY`；未配置时接口返回 `llm_not_configured`，前端显示降级提示，排盘结果不受影响。
- 结果页按 chart 结构分派命盘组件（bazi / ziwei / tarot / liuyao / 合盘），都不匹配时回退为 JSON 展示；新体系接入只需加一个组件。
- `requires_birth === false` 的体系不渲染出生表单：塔罗 → TarotForm，六爻 → LiuyaoForm（铜钱 / 时间 / 数字起卦）。
- `requires_secondary === true` 的合盘体系在同一表单卡片内切换「甲方 / 乙方」两份生辰，提交时带 `birth` + `secondary`。
- 颜色、字号、圆角一律取 `styles/tokens.css` 变量（Tailwind 类名 `bg-surface` / `text-muted` / `text-primary` 等都映射到变量）；不要在组件里写死色值。
- 主题：`settings` store 存 `system | light | dark`，写 `document.documentElement.dataset.theme`；默认跟随系统。
- 紫微十二宫按地支子→亥顺时针绕外圈（子在下中），支持宫格 / 列表切换、点宫看详情。
