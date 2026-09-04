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

在有 CI 运行时归档（`.evaluator/service-data/archives/automated/`）的本机，从 `ace_engine` 根目录执行：

```bash
# 从真实 CI 运行时归档生成静态站点快照（推荐，覆盖全部 Function）
python3 specs/tools/generate_site.py --publish-archive

# 可选：验证 static 模式能读取新快照（一致性校验）
python3 specs/tools/generate_site.py
```

`--publish-archive` 复用 `--mode dynamic` 的构建路径（读取每 Function 的最新 CI 评估归档），将构建的 spec/semantic/history 三件套落盘到 `.evaluator/` 提交快照。快照为**混合 revision**：每 Function 反映其最新 CI 评估，顶层 `sourceRevision` 取模数 revision；语义状态基于新鲜度（>30 天判 EXPIRED），`confirmation` 由 automated-evaluator 合成，非人工确认。revision 一致性天然满足（三者源自同一 `observed_revision`）。GitHub Pages 发布任务（`.github/workflows/deploy-pages.yml`）以 static 模式读取本目录已入库的最新快照。

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
