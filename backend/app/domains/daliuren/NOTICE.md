# 第三方来源

本目录的起课算法来自 **kinliuren（堅六壬）**：

- 项目：https://github.com/kentang2017/kinliuren
- 许可：MIT（PyPI classifier 标注）
- 包名与版本：`kinliuren==0.1.2.9`（纯 Python，无运行时依赖）

我们只做三件事：

1. 用 `lunar_python` 把起课时刻换算成节气、农历月、日干支、时干支
2. 调用 `Liuren(节气, 农历月, 日干支, 时干支).result(num)`；`num=0` 为昼贵（卯至申时），`num=1` 为夜贵
3. 把繁体/单字天将、六亲、格局转成简体全称

已知口径：

- 月将按太阳过宫（节气）推算，不由农历月直接推
- 三传由九宗门依次判定，库内返回的第一个成立课体即为课体
