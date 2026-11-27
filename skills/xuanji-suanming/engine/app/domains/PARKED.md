# 暂缓上线的体系

以下目录来自早期「全部占术」范围的实现，功能与测试仍在，但**不在当前上线清单**，
因此没有在 `app/domains/__init__.py` 注册，`/api/v1/systems` 不会返回，前端也没有入口。

- `daily/` 日运
- `monthly/` 月运
- `xiaoliuren/` 小六壬
- `daliuren/` 大六壬

如需重新上线，在 `app/domains/__init__.py` 的 import 与 `DOMAINS` 元组中各加一行即可；
前端会按 `category` 自动归组，但日运/月运还需要补回结果面板。
