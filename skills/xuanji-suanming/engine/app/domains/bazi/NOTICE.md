# 第三方代码声明

## bazi-skill

- 来源：https://github.com/jinchenma94/bazi-skill
- 许可：MIT License
- 用途：`_vendor_pai_pan.py` 为该项目的 `scripts/pai_pan.py` 原样引入，作为八字排盘核心算法。
- 本项目的 `engine.py` / `text.py` / `api.py` 在其外层做了适配：统一入参、真太阳时校正、
  canonical JSON 规整与提示词渲染。

MIT License 允许商用、修改与再分发，但要求在副本中保留版权与许可声明。
若后续修改 `_vendor_pai_pan.py`，请在本文件记录改动点。
