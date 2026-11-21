# 项目状态

更新时间：2026-11-21

## 一、上线范围

用户最终确认的清单（11 个入口）：

八字、紫微斗数、西方占星、奇门终身局、八字合盘、紫微合盘、六爻、塔罗、梅花易数、孔明神卦、MBTI 测试。

日运、月运、小六壬、大六壬**不在本期范围**：代码保留在 `backend/app/domains/`，
但未在 `app/domains/__init__.py` 注册，不对外提供接口，前端也无入口。

## 二、已完成

### 后端（FastAPI + uv）

| 体系 | id | 实现 | 关键点 |
|---|---|---|---|
| 四柱八字 | `bazi` | `app/domains/bazi` | MIT 引擎 vendor（bazi-skill）；真太阳时 + 均时差；四柱/十神/藏干/神煞/大运/流年 |
| 紫微斗数 | `ziwei` | `app/domains/ziwei` | `ziwei` 库（MIT）；十二宫、36 星、四化、大限、《全书》卷二亮度 |
| 西方占星 | `astrology` | `app/domains/astrology` | Swiss Ephemeris；日月行星、上升/MC、普拉西度宫位、相位、元素模式 |
| 奇门终身局 | `qimen` | `app/domains/qimen` | `qimen-rs`（MIT，Rust）；按**出生时刻**起拆补转盘局；年命/日干/时干三宫用神、门星神象意、干宫生克 |
| 八字合盘 | `bazi_hepan` | `app/domains/bazi_hepan` | 日主十神、夫妻宫、生肖合冲刑害、五行互补、启发式评分 |
| 紫微合盘 | `ziwei_hepan` | `app/domains/ziwei_hepan` | 命宫地支、命宫↔夫妻宫主星互见、四化飞入对方命/夫/福 |
| 六爻纳甲 | `liuyao` | `app/domains/liuyao` | 铜钱/时间/数字三种起卦；本卦·变卦·互卦；纳甲、六亲、六神、世应 |
| 塔罗 | `tarot` | `app/domains/tarot` | 78 张牌；单张/三张/五张/凯尔特十字；seed 可复现 |
| 梅花易数 | `meihua` | `app/domains/meihua` | 时间/数字起卦；本卦·互卦·变卦；体用生克；`numbers` 兼容字符串 |
| 孔明神卦 | `kongming` | `app/domains/kongming` | 诸葛神数：三字 → 康熙笔画 → 384 签；简繁折算；签级/卦爻/签文/断语 |
| MBTI 测试 | `mbti` | `app/domains/mbti` | 32 题五级量表，四维百分比 + 16 型简表 |

- 统一信封：`{system, engine_version, input, chart, text, warnings}`
- 契约：`SystemSpec` 含 `category`（chart/synastry/divination/fun）、`requires_secondary`、`fields`（通用表单 schema）
- 合盘入参：`POST /charts/{system}` body 增加 `secondary`
- 量表接口：`GET /api/v1/quizzes/mbti`
- 解读方向：`GET /api/v1/focus/{system}` 返回体系对应的方向目录（紫微为命格总览 + 十二宫主题）；`POST /interpret` 接受 `focus` id 列表，后端按目录映射为受控标签后写入提示词，未知 id 丢弃
- 模型设置：`GET/PUT/DELETE /api/v1/settings/llm` 读写接口地址、模型与密钥；密钥只写不读，对外只回显尾号；保存到 `backend/.local/llm.json`（0600，已 gitignore），页面设置优先于环境变量；`/meta` 同步返回来源与掩码；**这三个接口现在只有管理员能调用**（未登录 401、已登录非管理员 403，见下方「账号与权限」）
- 出生地与时区：`/geo/cities` 除国内城市外返回 41 个国外城市（东京/首尔/新加坡/伦敦/纽约/悉尼等），带英文别名，大小写不敏感，返回值新增 `timezone`（UTC 偏移小时数，兼容扩展）；`Place.timezone` 范围 `-12..14`（默认 8.0），越界由 `/charts/{system}` 直接返回 422
- 真太阳时按出生地时区推标准子午线（`timezone * 15`）：八字、奇门终身局同步该口径，warnings 交代基准时区（如「按 UTC+9 标准时 + 经度差 + 均时差」）；紫微起盘用出生地时区（`FixedOffset`），无出生地时回落北京时间；`SolarTimeInfo` 增加 `standard_meridian`，原有字段保留
- 测试：**167 passed**（含「上线清单恰好 11 项」的锁定用例、占星降级、英文元数据与 MBTI 英文题干、`/meta` 能力探测、方向目录与提示词、模型设置校验/掩码/环境变量回落、国外城市检索与时区、非法经纬度/时区 422；本轮新增 41 条：账号与会话 20、记录与解读隔离 15、存储底座 5、设置接口权限 1）；`uv run ruff check app tests` 干净
- 占星降级：缺出生地/时刻、或纬度约 66.6° 以上普拉西度无解时，接口仍返回 200，上升与宫位为 null 并给出中文提示，行星落座与相位照常
- AI 解读：`POST /api/v1/interpret`，SSE 流式，OpenAI 兼容协议，未配 key 时明确降级；`GET /api/v1/meta` 暴露 `llm_configured` 与接口/模型来源，前端据此提前提示、置灰入口并给出设置页链接
- 解读按方向组织：前端可选多方向（命格总览/财运/事业/感情/性格/健康/兄弟合伙/子女/迁移外出/人际贵人/田宅/福德/父母长辈等），后端按目录顺序写入提示词，要求先引盘面证据再解读

### 账号与权限

- 开放注册：用户名 + 密码，用户名 3–32 位 `[A-Za-z0-9_.-]`、唯一且大小写不敏感，密码 8–128 字符；密码用 `hashlib.scrypt`（n=16384, r=8, p=1，16 字节随机盐）存成 `scrypt$n$r$p$salt_hex$hash_hex`，校验用 `hmac.compare_digest`；用户不存在时也跑一次等价哈希，登录失败一律「用户名或密码不正确」，不泄露账号是否存在
- 接口：`POST /auth/register`（201，重名 409）、`POST /auth/login`（200 / 失败 401）、`POST /auth/logout`（204）、`GET /auth/me`（匿名也 200，返回 `{user: null}`）
- 会话：`secrets.token_urlsafe(32)`，库里只存 token 的 SHA-256，有效期 30 天；Cookie `sm_session` 为 HttpOnly + SameSite=Lax + Path=/ + Max-Age=30 天，`Secure` 由 `SM_COOKIE_SECURE=1` 打开（默认关，适配本机 http）
- 登录节流：同一 IP + 用户名 5 分钟内 10 次失败返回 429 `too_many_attempts`；内存字典 + 锁，进程重启清零，成功登录清零
- 管理员：**首个注册用户自动成为管理员**；启动前设 `SM_ADMIN_USERNAME=<用户名>` 可让该用户名注册时也是管理员（大小写不敏感）；`/settings/llm` 的 GET/PUT/DELETE 仅管理员（未登录 401、非管理员 403），`/meta` 保持公开且只暴露 `llm_configured` 与接口/模型名，不含密钥
- 排盘不受影响：`/charts/*`、`/interpret`、`/focus/*`、`/geo/*` 保持公开，未登录照样能起盘

### 记录存储与隔离

- 服务端 SQLite：默认 `backend/.local/app.db`，`SM_DB_PATH` 可覆盖；目录 0700、库文件（含 `-wal`/`-shm`）0600，权限在每次连接时校验并按需收紧（文件预先存在也会修正），WAL + `foreign_keys=ON`，每请求独立连接，所有 SQL 参数化；四张表 `users` / `sessions` / `records` / `readings`，外键均 ON DELETE CASCADE
- 记录接口：`GET/POST /records`、`GET/DELETE /records/{id}`、`DELETE /records` 清空；`HistoryRecord` 与前端类型一致（`id/createdAt/title/system/engine_version/input/chart/text/warnings`，时间为毫秒），`id` 与 `createdAt` 由服务端生成、不信任客户端传入
- 归属校验：所有查询都带 `user_id`，列表 / 单条 / 删除 / 解读一处不漏；跨用户访问统一 404，不区分「不存在」与「不是你的」；未登录访问记录接口一律 401 `auth_required`
- 配额与体积：每用户最多 50 条（插入后按 `created_at` 淘汰更旧的）；text ≤ 20 万字、payload 序列化 ≤ 500KB，超出 413
- AI 解读：按记录存 `readings` 表（`GET/PUT/DELETE /records/{id}/reading`），登录才保存与恢复，未登录只在当前页面停留、中途停止不落盘；旧的 `localStorage.sm_history` / `sm_ai_readings` 已不再读写（历史数据保留不删）

### 前端（Vue 3 + Vite + TS + Tailwind）

- 路由：`/`、`/chart/:system`、`/result`、`/history`、`/settings`、`/login`（`?mode=register` 进注册 Tab）
- 深色数据工作台（默认深色，浅色可切）：桌面 ≥1024 顶部 DeskNav + 1280 容器；768–1023 顶部栏；<768 顶部栏 + 底部 TabBar
- 结果页桌面：左栏 380px sticky 独立滚动（盘面 + 大运/流年 + 修改/隐藏生辰/重新起盘），右栏「命盘分析 / AI 对话」滑动胶囊 Tab + 盘头（标题/生辰/摘要/分类印章）+ 盘面要点卡 + 锚点 + 分布图 + Markdown 长文 + 风险块
- 右栏动效：盘头光晕缓慢漂移、印章入场、要点卡错峰上浮、五行/元素条从左生长、Tab 胶囊滑动、面板切换淡入、方向 chip 悬浮与选中脉冲、AI 输出光标与骨架屏；`prefers-reduced-motion` 下自动收敛
- AI 面板：方向多选（默认命格总览）、已选计数/清空、快捷问题、详略切换、流式输出复制；未配密钥时提前提示并可跳转设置页
- 解读方向一键全选：方向区「已选 n 个」旁提供全选/取消全选，未全选时选满全部方向、已全选时清空；仍保留 `data-focus-id`、已选计数与默认命格总览
- AI 解读按记录持久化：登录后以记录 id 逐条存到服务端 `readings`（`text/focus/style/question/system/updatedAt`），回到同一记录自动恢复正文与方向并显示「已保存」；切换记录不串内容，重新生成覆盖同一条存档，出错/空输出/中途停止不落盘，清空输出不删存档；未登录时解读只在当前页面，不保存也不恢复
- 设置页新增「AI 解读」：服务商预设（DeepSeek/OpenAI/自定义）、接口地址、模型名、密钥（password + 显示/隐藏）、保存/清除、来源状态；密钥只存后端
- 盘面摘要按体系取真实字段（日主与五行计数 / 日月升 / 命宫与主星 / 三宫干支 / 签号 / MBTI 类型等）；不吃生辰的体系不显示「隐藏生辰」，入口改为「修改信息」
- 盘面视觉：四柱改为单一「命盘」卡（盘头元信息 + 细线分栏四柱 + 五行短条 + 可展开校正明细），移除与面板重复的大运/流年块；紫微宫格支持点选高亮三方四正（本宫 + 对宫 + 两三合）
- 中英切换：`src/i18n/` 轻量 `t()`，`sm_locale` 持久化，`html.lang` 同步；体系名/tagline/表单 label 优先用后端 `name_en`/`tagline_en`/`label_en`，MBTI 走 `?lang=en`；盘面术语保持中文
- 隐藏生辰：左栏盘面与出生行打码，右栏长文、引用、复制文本中的公历日期/时刻/出生地一并替换，避免二次泄露
- 设计 tokens 已落地，明暗两套，深色为默认（`tokens-v2.css`）
- 首页四组：命盘 4 / 合盘 2 / 占卜 4 / 趣味 1，共 11 卡
- 起盘表单：生辰表单（公历/农历、时辰、城市、真太阳时）、双人合盘、六爻、塔罗、MBTI 测评、通用 OptionForm（梅花/孔明）
- 出生地选择：城市搜索支持国内城市与 41 个国外城市（英文名/别名不区分大小写，结果行显示国家与 `UTC+9` 一类的偏移）；另有「手动输入坐标」，填经度（-180..180）、纬度（-90..90）、UTC 时区（-12..14，默认 8）与可选名称，越界就地报错且不可确认；确认后与搜索模式互斥切换，已选行显示经纬度与时区
- 结果页：八字四柱、紫微环状十二宫、占星盘面（上升定左、行星环、相位线、行星表、元素/模式平衡）、塔罗牌阵、六爻卦象、合盘双人对照、奇门三宫 + 九宫格、梅花卦画、孔明签文、MBTI 四维条
- AI 解读区：流式 Markdown、快捷问题、未配 key 的友好提示
- 账号 UI：`/login` 页内登录/注册两个 Tab（注册需二次确认密码），顶栏与桌面导航显示登录态与退出；设置页对非管理员只读并提示需要管理员
- 历史记录走服务端：登录后从 `/records` 取列表、单条、删除与清空；未登录时首页/起盘仍可用，但结果不入库，历史页显示登录引导
- 主题、语言与明暗仍存本地（`sm_theme`/`sm_locale`），账号与记录不再写 localStorage
- 构建：`npm run build` 通过，`npx vue-tsc --noEmit` 无错

### 工程

- `scripts/smoke.mjs`：零依赖端到端冒烟（Node 原生 WebSocket + CDP 驱动本机 Chrome）
  - **27 条用例全部通过**（用 `bash scripts/smoke-isolated.sh` 跑全量）：体系清单与首页卡片数、八字/紫微/塔罗/孔明/奇门/梅花/MBTI/占星/八字合盘的结果页断言、19 处页面 390px 无横向溢出、历史记录
  - 本轮新增 23–26：解读方向一键全选/取消全选（按 `[data-focus-id]` 的 `aria-pressed` 断言，不依赖 LLM key）、解读按记录持久化（以临时账号写入一条固定文本的解读存档 → 刷新恢复并显示「已保存」，换记录不串内容，结束清理）、出生地手动经纬度（东京坐标 + `UTC+9` 出盘，经度 200 就地报错）、国外城市检索（输入 `Tokyo` 选中「东京 / 日本」，坐标行与结果页均带时区）
  - 27 双用户隔离：A/B 两个账号各自建记录，断言两边列表互不可见、跨用户取单条 / 删除 / 解读均为 404，且未登录访问记录接口为 401
  - 全体系桌面审计：11 个体系在 1440 下无溢出、左栏 380 sticky、标题下盘面摘要非空；打码按钮只出现在吃生辰的体系；1024 仍双栏 sticky，768 单列非 sticky
  - 右栏审计：盘头/印章渲染、盘面要点卡数量与高度、AI 方向标签 ≥5 且默认选中 1 个、可多选到 2 个并更新计数、未配 key 时有设置页入口
  - 设置页审计：AI 表单回填、密钥输入为 password、保存后状态变「已配置」且只回显 `••••1234`、页面 HTML 无明文密钥、清除后回到未配置
  - 验收用例：视口矩阵（1440/1024/768/390 壳层断点 + 六页无溢出）、结果页桌面（左栏 sticky 自滚、双 Tab、AI 未配 key 友好提示、隐藏生辰含右栏打码、修改/重新起盘）、手机盘面展开收起与 TabBar 不遮挡、主题默认深色/浅色持久化/对比度（最低 4.83:1）、英文矩阵（后端英文名、英文表单与 MBTI 题干、无中文 UI 残留、刷新保持）
  - 占星用例从结果页 DOM 读取行星/星座/宫位，同时校验上升与相位数量；行星行带 `data-retrograde` 钩子
  - 另有占星降级用例：缺出生地、高纬度两张盘先以临时账号写入服务端记录，再打开结果页，断言「本命盘 + 未算出上升与宫位」提示、10 颗行星仍在、宫位为空且无横向溢出
  - 逆行用例以接口返回的 `retrograde` 为期望值，逐颗比对表格标记，并数盘面 `R` 上标数量，不硬编码哪几颗
- `scripts/smoke-isolated.sh`：全量冒烟入口。自动起临时库（`mktemp` 目录下的 `smoke.db`）+ 临时 AI 配置 + 后端 8001 + 前端 5183（`SMOKE_BE_PORT` / `SMOKE_FE_PORT` 可改），跑完（含 Ctrl-C 与失败）清理子进程和临时文件，全程不碰真实的 8000/5173 与 `backend/.local/app.db`；`node scripts/smoke.mjs` 直连真实 8000 时，需要预置记录才能跑的用例会跳过并打印提示
- 数据说明：孔明神卦的康熙笔画来自 Unihan，384 签为通行本（见 `kongming/NOTICE.md`）
- 幂等性：`tests/test_determinism.py` 覆盖 11 个体系「同一入参 → 同一 chart/text/warnings」；跨体系调用不串状态。显式传时刻/种子的起卦才幂等，未传种子（塔罗）或未传时刻（六爻/梅花默认当前时间）是刻意随机
- 四柱交叉校验：`tests/test_bazi_crosscheck.py` 用 lunar_python 独立实现比对 10 组日期（含立春前后、23:00 日界），全部一致；本项目采用「晚子时归次日」，对应 `getDayInGanZhiExact()`
- 不依赖 AI 的规则解读方案与所需资料清单：`docs/INTERPRETATION-RULES.md`

### 运维与 Telegram Mini App

- `scripts/telegram-miniapp.sh`：一条命令把本机站点挂成 Cloudflare quick tunnel 的 HTTPS 地址，并设为机器人底部菜单按钮（`setChatMenuButton`，`type: web_app`）
  - 前置自检：`127.0.0.1:5173` 与 `127.0.0.1:8000/api/v1/meta` 必须 200，否则直接报错并打印启动命令（脚本不负责拉服务）
  - 起 `cloudflared tunnel --url http://127.0.0.1:5173 --no-autoupdate`，从日志正则取 `https://*.trycloudflare.com`，最多等 30 秒；拿不到就打印日志尾部 20 行
  - 经隧道回访 `/` 与 `/api/v1/meta`，先等 4 秒再重试到 200：quick tunnel 域名刚生成时会被系统缓存一次 NXDOMAIN，实测要等 4–10 秒才通，所以脚本必须等而不是一探到底
  - token 从 `backend/.local/telegram.json`（0600，字段 `bot_token` / `proxy`）或 `SM_TELEGRAM_BOT_TOKEN` 读，只在 python 进程内使用；失败只报 Telegram 的 `description` 或异常类型名，绝不打印含 token 的 URL
  - 参数：`--dry-run`（只起隧道 + 打印将发送的 payload）、`--no-menu`、`SM_MINIAPP_TEXT`（默认「玄机算命」）、`SM_TUNNEL_PORT`（默认 5173）、`SM_MINIAPP_API_PORT`（默认 8000）、`SM_TUNNEL_HOLD_SECONDS`（到点自动退出，便于自动化）
  - 前台常驻，`trap EXIT/INT/TERM` 结束 cloudflared 并删临时日志；实测 `--dry-run` 回访 `/` 与 `/api/v1/meta` 均 200，到时/Ctrl-C 退出后 `pgrep -fl cloudflared` 无残留
- Mini App 适配点：`frontend/vite.config.ts` 已有 `server.allowedHosts: ['.trycloudflare.com']`（否则 Vite 的 host 校验会用 403 拦掉隧道域名）；`frontend/src/lib/telegram.ts` 接入 Telegram WebApp SDK，在 Telegram 内 `ready()` / `expand()`、标题栏与背景跟随站内明暗主题、`safe-area-inset-bottom` 避开全面屏手势区，普通浏览器打开时全部跳过
- 本轮未做 Telegram 登录与 `initData` 校验：Mini App 内仍是本站账号密码登录，临时地址用普通浏览器也能直接访问

### 设计

- `design/DESIGN.md` 设计规范（东方玄学 × 现代极简）
- `design/DESIGN-EXT.md` 扩展规范（首页分组、双人卡、评分条、九宫格、卦画）
- `design/DESIGN-V2.md` 深色数据工作台规范（结果页线框、图表硬约束、三档断点、验收清单）
- `design/tokens.css` 明暗两套变量
- `design/index.html`、`design/prototype-ext.html` 390×844 交互原型
- `design/prototype-v2.html` 桌面/手机响应式工作台原型（首页 / 起盘 / 结果 / 中英切换）

## 三、待办

- AI 解读知识库（把 `text` + 牌义/星曜/卦辞/签文做成检索增强）
- 多设备同步 / 云备份（当前是单机 SQLite，备份 `backend/.local/app.db` 即可迁移）
- 部署（Docker Compose：uvicorn + 静态站点）
- 固定域名暴露：Cloudflare named tunnel（自有域名）或 VPS + HTTPS 反代，替换掉 quick tunnel；同时补 Telegram `initData` 校验
- SEO 与分享卡片
- 奇门终身局的流派差异说明与更多用神（当前固定年命/日干/时干三宫）

## 四、已知限制

- 紫微库覆盖 36 颗星曜，未含三台八座、恩光天贵、博士十二神等杂曜
- 六爻暂未计算旬空、月破等细节（已在 warnings 说明）
- 西方占星使用热带黄道 + 普拉西度，未提供其他分宫制切换；高纬度下普拉西度无解时不给上升/宫位（已提示）
- 塔罗牌义为关键词，细读依赖 AI
- 奇门终身局沿用拆补转盘，未做置闰、刻家、日家；三宫口径为常见一说
- 孔明神卦简繁折算取 Unihan 首选繁体，多音多义字（如「干」）可能与手算不同，页面会显示折算字
- 合盘分数为启发式权重，只用于横向比较
- 国外城市时区按标准时给固定偏移，不含夏令时（DST）；需要精确到夏令时的盘请用「手动输入坐标」自行填当前实际 UTC 偏移，warnings 里的基准时区即为参与计算的偏移
- AI 解读与记录存在服务端 SQLite（`backend/.local/app.db`）里，按账号隔离；但只有这一份单机库，没有多副本与云备份，换机器需要手动搬文件
- 账号能力仅到「注册 / 登录 / 登出」：无邮箱验证、无找回密码、无账号注销与自助删号；管理员也不能在界面上停用其它账号
- 登录节流按 `request.client.host` 计数、不解析 `X-Forwarded-For`；放到反向代理后面时所有用户会共用同一 IP 计数，需要先配受信代理再读转发头
- 存储是 SQLite 单机 + 单进程友好设计（WAL 只解决并发读写），不适合多实例/横向扩容
- CSRF 防护只依赖 Cookie 的 SameSite=Lax，没有独立的 CSRF token；跨站脚本注入场景仍需靠前端转义
- AI 输出目前仍用 `v-html` 渲染 Markdown，尚未引入 HTML 消毒库，属于已知风险（上游是用户自配的模型，内容不可全信）
- 设置页的模型配置接口现由管理员独占，但仍允许填写任意 http(s) 地址（便于接本机 Ollama/自建网关）；公网部署前建议额外加出站白名单
- 运行时密钥以明文保存在后端 `.local/llm.json`（权限 0600，已 gitignore），生产环境建议改用密钥管理服务
- Telegram Mini App 走 Cloudflare quick tunnel：地址每次重启都变（菜单按钮会失效，需要重跑 `scripts/telegram-miniapp.sh`），隧道只转发本机 5173，本机关机或前后端停止时 Mini App 立即打不开，也没有 Telegram 登录校验
- 「解读方向」只是提示词约束，不是规则引擎；规则化解读所需资料见 `docs/INTERPRETATION-RULES.md`
