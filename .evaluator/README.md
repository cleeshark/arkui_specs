# Spec Eval 报告归档

本目录保存 `spec_eval` 的 Function 级全量扫描结果，并随 specs 仓版本化。

## 目录约定

- `latest.json`：站点使用的归档指针，同时记录快照对应的源码 revision。
- `site-report.json`：站点消费的最新全量汇总与 Function Findings，采用紧凑 JSON 格式。
- `<source-revision>/<FuncID>/report.md`：单 Function 人类可读报告。
- `<source-revision>/<FuncID>/*.json`、`evidence/*.json`：静态结果、上下文与证据包。
- `<source-revision>/` 和 `.cache/`：本地原始报告与计算缓存，不入库。

## 更新归档

在包含 `foundation/arkui/ace_engine`、`interface/sdk-js` 和 `interface/sdk_c` 的完整 OpenHarmony 工作区中，从 `ace_engine` 根目录执行：

```bash
python3 specs/tools/spec_eval/cli.py \
  --output specs/.evaluator \
  --no-cache \
  --quiet \
  scan --all \
  --report-only
```

命令会扫描 `registry/functions.yaml` 中的全部 Function，保留单 Function 异常并继续执行，最后更新 `latest.json`。完成后运行 `python3 specs/tools/generate_site.py` 验证站点能够读取新归档。

GitHub Pages 发布任务不执行全量扫描，只读取本目录已入库的最新报告。
