# Spec Eval 报告归档

本目录保存 `spec_eval` 的 Function 级全量扫描结果，并随 specs 仓版本化。

## 目录约定

- `latest.json`：站点使用的归档指针，同时记录快照对应的源码 revision。
- `site-report.json`：静态站点归档，站点消费的最新全量汇总与 Function Findings，采用紧凑 JSON 格式；`generate_site.py` 经 `latest.json` 指针读取它作为 `spec_evaluation`。
- `site-evaluation-report.json`：语义站点归档，导自已确认 Review，`sourceRevision` 继承自 `site-report.json`；`generate_site.py` 直接读此文件作为 `semantic_evaluation`。
- `site-evaluation-history.json`：站点趋势与 Finding 差异历史，`currentRevision` 必须与语义归档的 `sourceRevision` 一致。
- `<source-revision>/<FuncID>/report.md`：单 Function 人类可读报告。
- `<source-revision>/<FuncID>/*.json`、`evidence/*.json`：静态结果、上下文与证据包。
- `<source-revision>/` 和 `.cache/`：本地原始报告与计算缓存，不入库。

## 更新归档

在包含 `foundation/arkui/ace_engine`、`interface/sdk-js` 和 `interface/sdk_c` 的完整 OpenHarmony 工作区中，从 `ace_engine` 根目录按顺序执行。**四步缺一不可**，跳过第 2、3 步会导致站点生成失败（见下节）。

```bash
# 1. 全量静态扫描，更新 site-report.json 与 latest.json
python3 specs/tools/spec_eval/cli.py \
  --output specs/.evaluator \
  --no-cache \
  --quiet \
  scan --all \
  --report-only

# 2. 用最新 site-report.json 重新导出语义归档（revision 自动对齐）
python3 specs/tools/spec_eval/cli.py --json site-evaluation \
  --reviews-root specs/evaluation/reviews \
  --site-report specs/.evaluator/site-report.json \
  --write specs/.evaluator/site-evaluation-report.json

# 3. 同步站点趋势与 Finding 差异历史
python3 specs/tools/spec_eval/cli.py --json site-evaluation-history \
  --site-evaluation-report specs/.evaluator/site-evaluation-report.json \
  --history specs/.evaluator/site-evaluation-history.json \
  --write specs/.evaluator/site-evaluation-history.json

# 4. 生成站点，验证能读取新归档
python3 specs/tools/generate_site.py
```

第 1 步会扫描 `registry/functions.yaml` 中的全部 Function，保留单 Function 异常并继续执行，最后更新 `latest.json`。`site-evaluation` 只读已确认 Review 与已归档的 `site-report.json`，不重扫源码、不调用模型，重跑是确定性输出。GitHub Pages 发布任务不执行全量扫描，只读取本目录已入库的最新报告。

## 站点归档的 revision 一致性

`generate_site.py` 要求静态归档与语义归档基于**同一个源码 revision**，否则拒绝生成站点并报错：

```
semantic and static site archives use different source revisions: <A> != <B>
```

两处归档及其 revision 来源（`sourceRevision` 一律记 ace_engine 仓 HEAD，不是 specs 仓）：

| 归档 | 变量 | 读取方式 | revision 来源 |
|---|---|---|---|
| 静态 | `spec_evaluation` | 经 `latest.json` 指针读 `site-report.json` | `scan` 时由 `config.git_revision()` 写入 |
| 语义 | `semantic_evaluation` | 直接读 `site-evaluation-report.json` | 从传入的 `site-report.json` 继承 |
| 历史 | `evaluation_history` | 直接读 `site-evaluation-history.json` | `currentRevision`，须与语义归档一致 |

因为语义归档的 revision 继承自静态归档，**只要第 1 步更新了 `site-report.json`，就必须依次重跑第 2、3 步**把两者对齐到同一 revision，否则 `generate_site.py` 会在 [`generate_site.py:366-381`](../tools/generate_site.py) 的两道一致性校验处报错退出。
