# 架构设计

## 一、总览

```
算命/
├─ backend/            FastAPI + uv（Python 3.12/3.13）
│  ├─ app/
│  │  ├─ main.py           应用入口、CORS、异常处理
│  │  ├─ core/              配置、通用类型、错误
│  │  ├─ api/              路由层（薄，只做校验与编排）
│  │  ├─ domains/          领域层（厚，纯算法）
│  │  │  ├─ shared/        生辰模型、真太阳时、城市经纬度、干支工具
│  │  │  ├─ bazi/          八字
│  │  │  ├─ ziwei/         紫微斗数
│  │  │  ├─ liuyao/        六爻
│  │  │  ├─ tarot/         塔罗
│  │  │  └─ astrology/     西方占星
│  │  └─ data/             静态数据（城市表、牌库、典籍）
│  └─ tests/
└─ frontend/           Vue 3 + Vite + TS + Pinia + Tailwind
```

## 二、领域模块契约（强制）

每个体系目录必须包含同样四个文件，保持可预测：

| 文件 | 职责 | 禁止事项 |
|---|---|---|
| `engine.py` | 纯函数排盘，无 IO、无网络、无全局状态 | 不读环境变量、不写文件 |
| `text.py` | 把 chart 转成给 LLM 读的规范文本 | 不调用 LLM |
| `constants.py` | 命名映射、星曜分类等静态表 | 不做计算 |
| `api.py` | 导出 `SPEC`、`compute(birth, options)`、`render_text(chart)` | 不写业务算法 |

注册方式：在 `app/domains/__init__.py` 的 `DOMAINS` 中登记该模块的 `api`。

`SystemSpec` 字段：

| 字段 | 说明 |
|---|---|
| `id` / `name` / `tagline` | 标识与展示文案 |
| `requires_birth` | 是否需要生辰 |
| `requires_time` | 是否需要精确时刻（否则可用时辰中点） |
| `requires_secondary` | 合盘类体系需要第二个人（请求体 `secondary`） |
| `category` | `chart` / `synastry` / `divination` / `fortune` / `fun`，前端据此分组 |
| `fields` | 非生辰类体系的表单 schema，前端通用渲染 |
| `status` | `ready` / `beta` / `planned` |

## 三、统一生辰模型 `BirthInput`

```json
{
  "calendar": "solar",
  "year": 1990, "month": 5, "day": 15,
  "hour": 14, "minute": 30,
  "shichen": null,
  "gender": "male",
  "true_solar_time": true,
  "place": { "name": "北京市", "longitude": 116.4, "latitude": 39.9, "timezone": 8 }
}
```

- `calendar`: `solar` | `lunar`；农历闰月用 `is_leap_month`
- `hour/minute` 可为空，此时参考 `shichen`；两者都空按「时辰未知」处理并记 warning
- `true_solar_time` 为真时：真太阳时 = 钟表时 + (经度 − 120) × 4 分钟 + 均时差
- `gender`: `male` | `female`

## 四、HTTP 契约

### `GET /api/v1/systems`
```json
[{
  "id": "bazi", "name": "四柱八字", "tagline": "...",
  "requires_birth": true, "requires_time": true, "requires_secondary": false,
  "category": "chart", "fields": [], "status": "ready"
}]
```

### `POST /api/v1/charts/{system}`
请求：`{ "birth": BirthInput, "secondary": BirthInput, "options": {} }`

- 占卜类（六爻/塔罗/梅花/孔明神卦）只用 `options`
- 命盘类（八字/紫微/占星/奇门终身局）用 `birth`；奇门终身局按出生时刻起局
- 合盘类（`requires_secondary=true`）必须同时给 `birth` 与 `secondary`

响应（统一信封）：
```json
{
  "system": "bazi",
  "engine_version": "0.1.0",
  "input": { "..." : "回显 birth" },
  "chart": { "...": "体系各自的 canonical JSON" },
  "text": "给 AI 读的规范文本",
  "warnings": []
}
```

### `GET /api/v1/quizzes/mbti`
返回 `{ scale, dimensions, questions }`，供前端渲染量表；答案通过
`POST /charts/mbti` 的 `options.answers`（1–5 的整数数组，顺序与题目一致）提交。

### `GET /api/v1/geo/cities?q=北京`
```json
[{ "name": "北京市", "province": "北京", "longitude": 116.407, "latitude": 39.904, "timezone": 8 }]
```

### `POST /api/v1/interpret`（SSE）
请求：`{ "system": "bazi", "chart": {...}, "question": "今年事业如何", "style": "concise" }`
响应：`text/event-stream`，事件 `delta`（文本增量）/ `done` / `error`

错误统一：`{ "error": { "code": "invalid_birth", "message": "..." } }`

## 五、前端结构

```
frontend/src/
├─ main.ts / App.vue
├─ router/index.ts       /   /chart/:system   /result/:system   /history   /settings
├─ stores/               birth.ts（当前生辰） charts.ts（当前结果） settings.ts
├─ api/client.ts         fetch 封装 + 类型
├─ components/
│  ├─ layout/            AppHeader / TabBar（移动端底部导航）
│  ├─ birth/             BirthForm / PlacePicker / DateTimePicker
│  └─ chart/             各体系命盘展示组件（按 system 动态加载）
└─ views/                HomeView / ChartView / ResultView / HistoryView / SettingsView
```

- 移动优先：默认窄屏单列，`md:` 以上双栏
- 命盘区固定为可横向缩放容器，避免小屏挤压
- 游客态存 `localStorage`，登录后同步（账号体系后置）
- 样式统一走 Tailwind + CSS 变量主题（明暗两套）

## 六、AI 解读

- 后端统一 `app/core/llm.py`：OpenAI 兼容协议（base_url / api_key / model 可配）
- 提示词 = 规范文本(`text.py`) + 结构化 chart JSON + 用户问题 + 解读者人设
- 绝不把「排盘结果」交给模型自由生成；模型只解释已有事实
- 未配置 API Key 时，接口返回明确提示，前端降级为「本地规则解读」

## 七、质量约束

- 排盘引擎必须有测试：边界时辰（子时换日）、立春换年、闰月、闰秒无关
- 每个体系至少 3 个固定样例快照测试
- 后端 `ruff` + `pytest`；前端 `vue-tsc` + `vite build` 必须通过
