# 第三方来源

本目录的排盘算法来自 **qimen-rs**：

- 项目：https://github.com/SpenserCai/qimen-rs
- 许可：MIT
- 包名与版本：`qimen-rs==0.2.1`（PyPI，Rust 实现 + PyO3 绑定）

我们做四件事：

1. 把出生时刻（可选真太阳时校正）解析成 UTC+8 民用时间
2. 调用 `qimen_rs.calculate()`，采用默认的 **时家奇门·拆补转盘**（`shi_jia_chai_bu_zhuan_pan`）
3. 把英文枚举转成中文 canonical JSON，并按 `4/9/2/3/5/7/8/1/6` 排出九宫格
4. 在盘面上补出终身局用神：年命（年干地盘落宫）、日干、时干三宫，
   以及门/星/神的象意与干宫生克。第 4 步为本项目自撰，不属于 qimen-rs。

口径说明：

- 换日：23:00（`zi_start`）
- 中宫：天禽随天芮，中宫恒寄坤二
- 旬空按时辰计算

算法本身不在此仓库，升级 `qimen-rs` 即可获得规则修订。
