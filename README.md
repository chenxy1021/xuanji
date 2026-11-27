# 算命 · 多体系命理排盘与 AI 解读

一个可切换多种术数体系的在线算命网站。**排盘交给代码，解读交给 AI。**

- 前端：Vue 3 + TypeScript + Vite + Tailwind（**玄夜星金**暗黑星盘风默认，支持一键切换**鎏金宣纸**浅色；桌面 / 平板 / 手机三档自适应；中英切换）
- 后端：Python 3.12/3.13 + FastAPI + [uv](https://docs.astral.sh/uv/)
- 体系：八字、紫微斗数、西方占星、奇门终身局、八字合盘、紫微合盘、六爻、塔罗、梅花易数、孔明神卦、MBTI 测试
- 出生地：国内城市 + 41 个国外主要城市（支持英文别名），也可手动填经纬度与 UTC 时区
- 账号：用户名 + 密码注册登录，记录与 AI 解读按账号隔离；未登录也能设置自己的模型、排盘和解读，记录只留在浏览器

## 界面预览

### 首页 · 玄夜星金（深色）与 鎏金宣纸（浅色）

| 玄夜星金 · 暗黑星盘风（默认） | 鎏金宣纸 · 雅集星盘风（浅色） |
| :---: | :---: |
| ![首页 · 玄夜星金](docs/screenshots/home-dark.png) | ![首页 · 鎏金宣纸](docs/screenshots/home-light.png) |

### 在线排盘结果页（四柱八字）

![在线排盘结果页 · 四柱八字](docs/screenshots/result-bazi.png)

### 离线技能单文件 HTML 命盘（`skills/xuanji-suanming`）

| 紫微斗数 · 双栏交互命盘（三方四正联动） | 西方占星 · 黄道本命星轮 |
| :---: | :---: |
| ![紫微斗数命盘](docs/screenshots/skill-ziwei.png) | ![西方占星本命盘](docs/screenshots/skill-astrology.png) |

## 功能要点

- **出生地与时区**：城市搜索支持国内城市和国外主要城市（输入 `Tokyo`、`New York` 都能命中，
  结果行会显示国家与 `UTC+9` 一类的偏移）；找不到城市时可用「手动输入坐标」，
  填经度（-180..180）、纬度（-90..90）、UTC 时区（-12..14，默认 +8）和可选名称，越界会就地报错。
  真太阳时按当地时区推标准子午线（`时区 × 15°`）后再做经度差与均时差修正，八字、奇门终身局、
  紫微用的是同一套口径。
- **AI 解读**：流式输出，可多选解读方向（默认「命格总览」），方向区有一键**全选 / 取消全选**；
  生成结果会**自动保存**——登录后存到账号，未登录存到当前浏览器，回到同一条记录都能恢复，并显示「已保存」。
  解读要求先给结论、术语用大白话解释，避免 AI 套话与固定三段式；**用英文提问就用英文回答**，
  不提问时跟随界面语言。
- **模型自配置**：任何人都能在设置页填写自己的接口地址、模型名和密钥（不登录也行），配置只存当前浏览器；
  管理员保存的「本站默认」作为后备。个人配置优先于本站默认。
- **账号与记录隔离**：注册即可用，第一个注册的账号是管理员；登录后每个人只看得到自己的排盘记录与解读。
  未登录时排盘、占卜、AI 解读都能用，记录与解读只写浏览器 `localStorage`，不上传服务器。
- **双主题与双语**：默认「玄夜星金」暗黑星盘风，右上角可一键切换「鎏金宣纸」浅色模式，支持中英切换；主题与语言偏好存在本机 `localStorage`。

## 账号与记录

- **注册 / 登录**：用户名 3–32 位（字母、数字、`_`、`.`、`-`），密码 8–128 位。密码用 scrypt 加盐存储，
  会话是 HttpOnly + SameSite=Lax 的 `sm_session` Cookie（30 天），服务端只存 token 的 SHA-256。
- **第一个注册的账号就是管理员**。如果想指定管理员，在启动后端前设置 `SM_ADMIN_USERNAME=<用户名>`，
  该用户名注册时直接成为管理员（大小写不敏感）。
- **模型配置**：所有用户（含未登录）都能在 **设置 → AI 解读** 填自己的接口地址、模型和密钥，
  配置只存在当前浏览器；管理员额外可以把当前填写保存为「本站默认」，写入后端 `.local/llm.json`。
  设置接口 `GET/PUT/DELETE /settings/llm` 只对管理员开放（未登录 401、非管理员 403）；
  `/meta` 公开，但只暴露「是否已配置」和接口/模型名，不含密钥。
- **记录隔离**：登录后起盘会自动存到服务端，历史页可回看、删除、清空；每个人只能看到自己的账号记录，
  跨账号访问一律当作不存在（404）。每个账号最多保留 50 条，更旧的自动淘汰。
- **未登录时**：排盘、占卜、MBTI、AI 解读都能正常用；记录与 AI 解读只写当前浏览器的 `localStorage`
  （同样最多 50 条），历史页可以查看、删除、清空，但换设备或换浏览器不会同步。
- **AI 解读**按记录保存：回到同一条记录会自动恢复上次正文与所选方向；中途停止、出错或空输出不落盘。
  早期版本存在浏览器里的 `sm_history` / `sm_ai_readings` 已不再读写（数据保留，不自动删除）。

## 快速开始

```bash
# 一条命令同时起前后端（Ctrl-C 一起停）
bash scripts/dev.sh
# 前端：http://127.0.0.1:5173    后端：http://127.0.0.1:8000/docs
# 端口被占用时：SM_BE_PORT=8010 SM_FE_PORT=5183 bash scripts/dev.sh
```

脚本会先检查依赖（缺 `backend/.venv` 就 `uv sync`、缺 `node_modules` 就 `npm install`），
并把前端 `/api` 代理到本次启动的后端端口；PATH 上的 node 不可用时会自动退回 fnm 的 default 版本。

也可以手动分开起：

```bash
# 后端（终端 1）
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
# 文档：http://127.0.0.1:8000/docs

# 前端（终端 2）
cd frontend
npm install
npm run dev
# 打开：http://127.0.0.1:5173
```

## 配置 AI 解读（可选）

三档优先级：**个人配置 > 本站默认 > 环境变量**。

1. **个人配置（所有人，含未登录）**：打开 **设置 → AI 解读**，填写接口地址、模型名和 API Key。
   配置只存在当前浏览器的 `localStorage`（`sm_llm_personal`），每次解读随请求发给后端，
   不写服务器数据库；保存后回到结果页切到「AI 解读」点「开始解读」即可。
   不要把密钥保存在公共电脑上。
2. **本站默认（管理员）**：在同一个设置页把当前填写保存为本站默认，写入后端
   `backend/.local/llm.json`（权限 0600，已 gitignore），接口只回显尾号。
   没有个人配置的访问者会使用这份配置。
3. 或使用 `.env` / 环境变量（兼容任何 OpenAI 协议服务）：

```bash
SM_LLM_BASE_URL=https://api.deepseek.com
SM_LLM_API_KEY=sk-...
SM_LLM_MODEL=deepseek-chat
```

未配置时排盘照常可用，AI 面板会提前提示并给出「去设置里填写」入口。
`/settings/llm` 这三个设置接口只对管理员开放（未登录 401、非管理员 403）；`/meta` 仍公开但只报「是否已配置」。
个人配置与本站默认都允许任意 http(s) 地址（方便接本机 Ollama / Magpie / 自建网关），
公网部署前建议再加出站白名单。

## 数据存在哪里

**登录后的账号、排盘记录与 AI 解读都存在后端的 SQLite 里**，按账号隔离；未登录时的记录、解读与个人模型配置只在本浏览器（见下表）：

| 位置 | 内容 | 说明 |
|---|---|---|
| `backend/.local/app.db` | 账号、会话、排盘记录、AI 解读 | 目录 0700 / 文件 0600；可用 `SM_DB_PATH` 换位置；**备份这个文件就等于备份全部账号与记录** |
| 浏览器 `sm_session` Cookie | 登录会话（30 天） | HttpOnly + SameSite=Lax，`SM_COOKIE_SECURE=1` 时加 `Secure` |
| 浏览器 `localStorage` | `sm_theme` / `sm_locale` 主题语言偏好、`sm_birth` / `sm_birth_b` 上次填写的生辰 | 只存本机，与账号无关 |
| 浏览器 `localStorage` | `sm_guest_records` / `sm_guest_readings`：未登录时的排盘记录与 AI 解读 | 只在本浏览器，最多 50 条；不上传服务器 |
| 浏览器 `localStorage` | `sm_llm_personal`：个人模型配置（含 API Key） | 只在本浏览器；公共电脑上用完请在设置页清除 |

每个账号最多 50 条记录，未登录时浏览器里同样最多 50 条，更旧的自动淘汰。
旧的 `sm_history` / `sm_ai_readings` 两个 key 已不再读写，里面的历史数据不会被删除，需要的话可以自己导出。

> 说明：国外城市的内置时区是**标准时固定偏移，不含夏令时（DST）**。如果出生地实行夏令时，
> 用「手动输入坐标」把 UTC 时区改成当时的实际偏移即可。

## 自测

```bash
# 后端单测
cd backend && uv run pytest -q && uv run ruff check app tests

# 全量端到端冒烟（27 条）：自动起临时库 + 临时 AI 配置 + 8001/5183，跑完清理，不碰真实服务与真实数据
bash scripts/smoke-isolated.sh
# 端口被占用时可改：SMOKE_BE_PORT=8011 SMOKE_FE_PORT=5213 bash scripts/smoke-isolated.sh

# 只对当前 8000/5173 跑（需要预置记录的用例会自动跳过并提示）
node scripts/smoke.mjs
```

冒烟脚本零依赖（Node 原生 WebSocket 直驱 headless Chrome），失败时会把现场文本落到 `/tmp/smoke-fail-*.txt`，
截图在 `/tmp/smoke-*.png`。

## Telegram Mini App（临时公网地址）

本机站点可以直接当 Telegram Mini App（Web App）打开。思路是：先挂一个手机能访问的 HTTPS 地址，再把它设成机器人聊天界面左下角的菜单按钮。

```bash
# 前置：5173 前端与 8000 后端已在运行（脚本不负责启动服务）
bash scripts/telegram-miniapp.sh
```

脚本做的事：

1. 检查 `127.0.0.1:5173` 与 `127.0.0.1:8000/api/v1/meta` 是否 200，不通就报错退出并给出启动命令；
2. 后台起 `cloudflared tunnel --url http://127.0.0.1:5173 --no-autoupdate`，日志落临时文件，正则解析 `https://*.trycloudflare.com`（最多等 30 秒，失败打印日志尾部）；
3. 经隧道回访 `/` 与 `/api/v1/meta`，确认都是 200（quick tunnel 域名刚生成时解析会失败一阵，脚本会先等几秒再重试）；
4. 调用 Telegram `setChatMenuButton`，把地址设成菜单按钮（`type: web_app`）。token 从 `backend/.local/telegram.json`（0600）或 `SM_TELEGRAM_BOT_TOKEN` 读，只在 python 进程内存里用，不进命令行、不进日志；
5. 前台常驻隧道，`Ctrl-C` 会结束 cloudflared 并清理临时日志。

常用变体：

```bash
bash scripts/telegram-miniapp.sh --dry-run    # 只起隧道 + 打印将发送的 JSON，不调 Telegram
bash scripts/telegram-miniapp.sh --no-menu    # 只起隧道，不动菜单按钮
SM_MINIAPP_TEXT='玄机算命' bash scripts/telegram-miniapp.sh
SM_TUNNEL_PORT=5183 bash scripts/telegram-miniapp.sh          # 隧道指向别的端口
SM_TUNNEL_HOLD_SECONDS=20 bash scripts/telegram-miniapp.sh --dry-run   # 20 秒后自动退出（自动化用）
```

打开方式：Telegram 里进 `t.me/cxy_muse_bot`，点底部菜单按钮。

几个必须知道的点：

- **quick tunnel 地址每次重启都会变**。变了必须重跑脚本，否则菜单按钮还指着旧地址，点开是打不开的。
- 隧道只在本机运行：本机关机、`5173`/`8000` 停了，Mini App 立刻打不开。
- 想要固定地址：自有域名 + Cloudflare **named tunnel**（`cloudflared tunnel create` / `tunnel route dns`），或者部署到 VPS 后用自建 HTTPS 反代，把 URL 写死一次。
- **BotFather `/newapp` 和 Bot API 菜单按钮不是一回事**：`/newapp` 是给 bot 登记一个独立的 Web App 入口（有自己的短名字）；`setChatMenuButton` 改的是聊天输入框左下角的菜单按钮。两者可以并存，但在 quick tunnel 场景下建议只配菜单按钮，免得两处地址不一致。
- 本轮**没有**做 Telegram 登录 / `initData` 校验：Mini App 里就是本站的账号密码登录，这个地址用普通浏览器也能直接打开（只是临时地址不公开、会很快失效）。

前端适配点：`frontend/vite.config.ts` 已配 `server.allowedHosts: ['.trycloudflare.com']`（否则 dev server 会以 403 拦掉隧道域名）；`Telegram WebApp SDK` 已接入（`frontend/src/lib/telegram.ts`），在 Telegram 内调用 `ready()` / `expand()`，标题栏与背景跟随站内明暗主题；顶部按 `safeAreaInset + contentSafeAreaInset` 让开 Telegram 标题栏，底部 TabBar 让开 home indicator；普通浏览器打开时这些逻辑自动跳过。

## 目录

```
backend/    FastAPI 服务与各体系排盘引擎（账号与记录在 .local/app.db）
frontend/   Vue 单页应用
scripts/    端到端冒烟（smoke.mjs / 全量 smoke-isolated.sh）与 Telegram Mini App 隧道（telegram-miniapp.sh）
docs/       产品计划（PLAN.md）、架构契约（ARCHITECTURE.md）与界面预览图（screenshots/）
```

> 命理内容属于传统文化学习参考，不构成医疗、法律或投资建议。
