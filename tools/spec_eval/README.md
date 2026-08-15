# ArkUI Function Spec Evaluator 使用指南

`spec_eval` 是面向 `ace_engine/specs/` 的 Function（FuncID）级确定性评价工具。

工具以一个完整功能域作为最小评价单元。输入任意一个 Feature spec、共享 `design.md` 或 FuncID 后，都会加载该 Function 下的全部 Feature、共享 Design 和 Registry 元数据，再统一执行结构、追溯、引用、SDK 定位和文档卫生检查。

## 1. 能力边界

当前工具负责可以稳定、重复执行的机械检查：

- Function、Feature、Registry 和磁盘文件的一致性。
- Spec、Design 的章节、表格、ID 和固定字段结构。
- AC、Rule、VM、Task、Evidence 的 Function 级追溯关系。
- 源码引用路径、可选行号、范围和证据片段解析。
- Public/System API 在 canonical SDK 声明中的定位。
- TODO、绝对路径、死链接、未勾选自审项等文档卫生问题。
- Function 级静态门禁、证据包、Markdown 报告和仓级汇总。

当前工具不负责以下语义判断：

- 源码是否真正支持文档结论。
- AC 是否可复现、可观测和具有充分测试价值。
- Feature 拆分、Design 调用链或 ADR 是否合理、完整。
- N/A、兼容性、设备差异和系统影响结论是否成立。
- 完整五维语义质量评分。

这些判断由评价 Skill 消费本工具生成的证据包完成。`score` 命令可以将一份完成态 `semantic-result.json` 与同一 Function、同一源码 revision 的静态结果和证据清单确定性聚合为 `score-result.json`。`check`、`evidence`、`scan` 本身仍不调用语义评价，也不输出语义总分。工具不会自动修改任何 spec、design 或 registry 文件。

## 2. 环境要求

从 `ace_engine` 仓库根目录运行命令。

基础依赖：

- Python 3.10 或兼容版本。
- PyYAML。
- Git，用于记录源码 revision 和计算变更文件。
- ripgrep（`rg`），用于一次性枚举源码和 SDK 声明文件并建立进程级索引。

快速检查：

```bash
python3 --version
python3 -c 'import yaml; print(yaml.__version__)'
git --version
rg --version
```

工具直接通过仓内源码运行，不需要安装 Python package：

```bash
python3 specs/tools/spec_eval/cli.py --help
python3 specs/tools/spec_eval/ci_runner.py --help
```

## 3. 快速开始

### 3.1 定位完整 Function

通过 FuncID 定位：

```bash
python3 specs/tools/spec_eval/cli.py --json \
  discover --func-id 05-03-10
```

通过任意 spec、design 或 Function 目录反查：

```bash
python3 specs/tools/spec_eval/cli.py --json \
  discover --path \
  specs/05-ui-components/03-scroll-container-components/10-water-flow-flow-item/Feat-01-creation-footer-flowitem-spec.md
```

输出的 `FunctionContext` 包含：

- `func_id` 和 Function 目录。
- 共享 `design.md`。
- 属于该 FuncID 的全部 Feature spec。
- Function 和 Feature Registry 条目。
- Git revision、工具版本和规则版本。

### 3.2 检查单个 Function

```bash
python3 specs/tools/spec_eval/cli.py \
  --output /tmp/spec-evaluation \
  check --func-id 05-03-10
```

需要在终端获取完整 JSON 时：

```bash
python3 specs/tools/spec_eval/cli.py \
  --output /tmp/spec-evaluation \
  --json check --func-id 05-03-10
```

质量门禁失败时命令返回 `1`，但仍会生成完整报告。这表示文档存在确定性质量问题，不表示工具运行失败。

### 3.3 构建证据包

```bash
python3 specs/tools/spec_eval/cli.py \
  --output /tmp/spec-evaluation \
  evidence --func-id 05-03-10
```

`check` 和 `evidence` 都会执行完整 Function 评价并写入相同的报告文件。两者的区别主要是终端输出：

- `check` 输出静态门禁和 Findings。
- `evidence` 输出证据声明、源码引用和 SDK 定位结果。

### 3.4 聚合单个 Function 的确定性评分

语义评价完成后，使用同一 Function、同一源码 revision 的三个输入生成最终评分：

```bash
python3 specs/tools/spec_eval/cli.py --json score \
  --static-result /tmp/spec-evaluation/<revision>/05-03-10/static-result.json \
  --evidence-manifest /tmp/spec-evaluation/<revision>/05-03-10/evidence-manifest.json \
  --semantic-result /tmp/semantic-result.json \
  --write /tmp/score-result.json \
  --analysis-write /tmp/function-analysis.json
```

聚合器会先校验 FuncID、源码 revision、Rubric/复杂度规则/协议版本及 `static_complete`、`evidence_complete`、`semantic_complete` 执行状态，再按冻结 Rubric 计算维度得分、发布分封顶、有效 Gate、置信度和准入状态。相同输入会生成完全相同的 JSON 内容。

可选的 `--analysis-write` 不改变冻结的 `score-result.json` 协议，而是额外生成确定性的 Function 分析文件，包含：

- static tool/rule、Evaluator Skill/协议、Rubric、复杂度规则和 Aggregator 的完整版本包。
- static、evidence manifest、全部 evidence shard 和 semantic 输入的 SHA-256 指纹。
- 按严重度、问题规模和稳定身份排序的 Top 5 整改项，以及 Finding、Criterion、Rule、Feat、Claim、Evidence 和路径下钻索引。
- 各 Feat 的静态/语义 Finding 数、最高风险等级、证据支持率、追溯闭环率和关联整改项。
- 无法精确归属到单个 Feat 的 Function-shared 风险。

质量 Gate 为 `fail` 时，命令仍会写出合法的 `score-result.json`，并返回退出码 `1`；输入不一致、协议不合法或语义执行未完成时不生成评分结果，返回退出码 `2`。

### 3.5 分析多次独立语义评价的稳定性

同一 Function、同一源码 revision、同一 Evaluator 版本至少完成三次独立评价后，可以生成稳定性元数据：

```bash
python3 specs/tools/spec_eval/cli.py --json stability \
  --static-result /tmp/spec-evaluation/<revision>/05-03-10/static-result.json \
  --evidence-manifest /tmp/spec-evaluation/<revision>/05-03-10/evidence-manifest.json \
  --semantic-result /tmp/run-1/semantic-result.json \
  --semantic-result /tmp/run-2/semantic-result.json \
  --semantic-result /tmp/run-3/semantic-result.json \
  --selected-run-id run-3 \
  --write /tmp/stability-result.json
```

结果包含原始分最小值、最大值、range、均值、总体标准差，20项 Criterion 的结论分布、2/3共识、无共识项、各 run 的同伴一致率和离群标记。输入顺序不影响输出。

离群标记只使用 Criterion 共识偏离，不使用分数高低猜测：某个 run 必须是唯一最高偏离者，偏离至少20%的 Criterion，且比次高 run 至少多2项，才标记为 `OUTLIER`。分数统计、共识和离群信息仅作为稳定性元数据；正式发布分始终来自 `--selected-run-id` 明确选择的单次 semantic result，多数投票不会改写其结论。

`stability` 是分析命令，合法生成结果时返回 `0`，不会因为被分析 run 的质量 Gate 为 `fail` 而返回 `1`。

### 3.6 组装 Function 总报告

评分、分析和稳定性结果可以组装为冻结 Schema 兼容的 `evaluation-report.json`，并同时生成包含整改项、Feat 风险和稳定性摘要的 Markdown 报告：

```bash
python3 specs/tools/spec_eval/cli.py --json report \
  --static-result /tmp/spec-evaluation/<revision>/05-03-10/static-result.json \
  --semantic-result /tmp/run-3/semantic-result.json \
  --score-result /tmp/score-result.json \
  --analysis-result /tmp/function-analysis.json \
  --stability-result /tmp/stability-result.json \
  --json-write /tmp/evaluation-report.json \
  --markdown-write /tmp/function-report.md
```

`evaluation-report.json` 只包含冻结协议允许的 static、semantic、score 和 summary 字段；`function-analysis.json` 与 `stability-result.json` 保持为伴随机器输入，不扩展冻结 Schema。显式选定的 semantic run 必须与 stability 的 `selected_run` 一致，多数 Criterion 共识不会改写正式结论或分数。

### 3.7 导出 confirmed Review 站点语义归档

站点发布使用已确认 Review 和已归档静态 `site-report.json`，不重新扫描源码、SDK 或调用模型：

```bash
python3 specs/tools/spec_eval/cli.py --json site-evaluation \
  --reviews-root specs/evaluation/reviews \
  --site-report specs/.evaluator/site-report.json \
  --write specs/.evaluator/site-evaluation-report.json
```

只有 `status: confirmed` 的 Review 会进入归档。Review 的 `func_id + source_revision` 与静态报告不一致时保留记录但标记为 `EXPIRED`，不会计入当前 revision 的 `findingCount`。输出通过 `evaluation/schemas/site-evaluation-report.schema.json` 校验，并包含人工分数、20 项 Criterion 摘要、静态/语义 Finding、recommendation、证据路径和确认信息。

站点详情页将五维分数绘制为 SVG 雷达图，并同时显示 published/raw 总分；对 `CONTRADICTED` 和 `PARTIALLY_SUPPORTED` Criterion，在同一 Criterion 区块内展示具体 Finding、关联证据路径和 recommendation，不再把建议和证据拆成独立列表。详情页支持下载单个 Function JSON 输入包，作为负责人后续优化的上下文输入。

### 3.8 更新站点趋势和 Finding 差异归档

confirmed Review 站点归档生成后，可更新轻量历史文件：

```bash
python3 specs/tools/spec_eval/cli.py --json site-evaluation-history \
  --site-evaluation-report specs/.evaluator/site-evaluation-report.json \
  --history specs/.evaluator/site-evaluation-history.json \
  --write specs/.evaluator/site-evaluation-history.json
```

历史文件只保留最多 52 个 revision 汇总快照、当前活跃 Finding 的紧凑身份索引和最近一次差异，
不会重复保存每个 revision 的完整报告。差异基于 `source + func_id + finding_id` 和严重度/消息分类，
输出新增、已解决、持续存在和重新分类数量，以及受影响 Function 和有限数量的下钻详情。

同一 revision、同一 confirmed Review 指纹重复运行时输出保持不变；源码 revision 变化或同 revision
下人工 Review 发生变化时才追加/更新快照并重新计算差异。站点生成器会移除 `activeFindings`，只把约
数 KB 的趋势摘要打入页面数据。

### 3.9 根据变更文件评价受影响 Function

准备一份每行一个仓库相对路径的文件列表：

```text
specs/05-ui-components/03-scroll-container-components/10-water-flow-flow-item/Feat-02-layout-config-item-constraint-spec.md
specs/04-common-capability/06-custom-node/01-placeholder-component/design.md
```

执行：

```bash
python3 specs/tools/spec_eval/cli.py \
  --output /tmp/spec-evaluation \
  changed --files-from changed-files.txt
```

任一 Feature 发生变化时，工具都会重新评价它所属的整个 Function。多个文件映射到同一 FuncID 时只运行一次。

### 3.10 全仓扫描

```bash
python3 specs/tools/spec_eval/cli.py \
  --output /tmp/spec-evaluation \
  --quiet scan --all
```

单个 Function 发生异常时，扫描会继续处理其他 Function，并在最终结果中将该 Function 标记为 `error`。全仓模式还会生成 `baseline-summary.json`。

全仓扫描会先为源码 basename/suffix 和本批次涉及的 SDK API 建立只读进程级索引，随后由全部 Function 共享，不再为每条引用或每个 API 单独启动 `rg`。扫描结束后可在 `<output>/<revision>/performance-summary.json` 查看：

- 全仓总耗时，以及 Function P50/P95/最大耗时。
- parser、各 checker、证据构建和写盘等阶段累计耗时。
- 源码与 SDK 索引的文件数、查询数、扫描字节数和建索引耗时。
- 每个 Function 的阶段耗时和缓存命中状态。

当 299 个 Function 全部命中精确输入缓存时，工具会跳过 Markdown 解析和 SDK/源码索引构建。

生成可入库的全量报告归档：

```bash
python3 specs/tools/spec_eval/cli.py \
  --output specs/.evaluator \
  --no-cache \
  --quiet \
  scan --all \
  --report-only
```

- 扫描对象严格来自 `registry/functions.yaml`，包含未落盘、无 Feature 或缺少 Design 的已注册 Function。
- 单个 Function 异常不会中止后续 Function，异常会以 `gate: error` 写入报告。
- 默认 `scan --all` 保持严格退出码：Gate FAIL 返回 `1`，扫描异常返回 `3`。
- `--report-only` 仅把全量命令退出码调整为成功，检查结果和 Gate 不会被改写，适用于集中生成归档报告。
- 完整站点快照固定写入 `<output>/site-report.json`，并更新 `<output>/latest.json` 指针；快照内部和指针都记录 source revision。
- 使用 `--output specs/.evaluator` 时，只需将 `site-report.json`、`latest.json` 和可选 README 随 specs 仓入库。revision 原始报告和 `.cache/` 保留本地；站点生成器不在 GitHub Pages 发布任务中重新扫描源码仓和 SDK 仓。

### 3.11 冻结稳定 Finding 基线

全量无错误扫描完成后，将 revision 原始结果和同一次扫描产生的 `site-report.json` 冻结为小型 manifest：

```bash
python3 specs/tools/spec_eval/cli.py baseline \
  --results specs/.evaluator/<source-revision> \
  --site-report specs/.evaluator/site-report.json \
  --write specs/evaluation/baselines/current.json
```

只有以下条件同时成立时才允许生成正式基线：

- `site-report.json` 和原始结果的 source revision、tool version、rule version 一致。
- 注册 Function 数、完成 Function 数和原始结果数相同。
- 工具错误数为 0。

基线按稳定 Finding 身份压缩重复问题，只保存比较所需摘要，不复制证据包和完整 Function 报告。

### 3.11 对比当前结果和基线

```bash
python3 specs/tools/spec_eval/cli.py --json compare \
  --current /tmp/spec-evaluation/current \
  --baseline specs/evaluation/baselines/current.json
```

`--current` 可以是一个或多个 Function 的结果目录，也可以是 manifest。对比结果按 FuncID 给出：

- `added`：新增问题。
- `resolved`：已解决的存量问题。
- `unchanged`：身份和分类均未变化的问题。
- `reclassified`：同一问题的严重度或规范化消息发生变化。

Finding 身份不包含 Markdown 定位行号和严重度，因此只移动文档内容不会产生伪新增/伪解决。当前结果只扫描部分 Function 时，仅在该 Function 范围内比较，不会把未扫描 Function 误判为 resolved。identity version 或 rule version 不一致时命令明确失败，禁止跨版本静默混算。

## 4. 通用命令参数

| 参数 | 作用 |
|---|---|
| `--output <dir>` | 指定报告和缓存根目录，默认是 `out/spec-evaluation` |
| `--json` | 将终端输出改为机器可读 JSON |
| `--quiet` | 只保留错误和最终状态，适合全仓扫描 |
| `--no-cache` | 禁用精确输入缓存，用于规则开发和回归验证 |

全局参数必须放在子命令之前，例如：

```bash
python3 specs/tools/spec_eval/cli.py \
  --json --no-cache check --func-id 05-03-10
```

## 5. CI 使用

CI 推荐使用独立入口 `ci_runner.py`。它只评价变更影响的完整 Function，并生成稳定的 `ci-summary.json`。

### 5.1 Report-only 模式

初期灰度推荐使用只报告模式：

```bash
python3 specs/tools/spec_eval/ci_runner.py \
  --files-from changed-files.txt \
  --output out/spec-evaluation \
  --json
```

在 report-only 模式下，Function 门禁失败仍返回 `0`；工具或Function执行错误不会被隐藏。

提供 `--baseline` 时，report-only模式还会计算绝对Gate和增量Gate，但质量问题仍不改变退出码。

### 5.2 绝对 Enforce 模式

规则和历史基线完成校准后，可以启用阻塞：

```bash
python3 specs/tools/spec_eval/ci_runner.py \
  --files-from changed-files.txt \
  --output out/spec-evaluation \
  --enforce --json
```

只要任一受影响 Function 的门禁为 `fail`，命令返回 `1`。

### 5.3 增量 Enforce 模式

历史Function推荐使用“不新增、不恶化”门禁：

```bash
python3 specs/tools/spec_eval/ci_runner.py \
  --files-from changed-files.txt \
  --output out/spec-evaluation \
  --baseline specs/evaluation/baselines/current.json \
  --delta-enforce --json
```

增量策略：

- baseline中已有的Function只阻塞新增Critical/Major和严重度升级问题。
- 新增Minor或同严重度消息重分类产生warn，不阻塞退出码。
- resolved、unchanged和严重度降低不阻塞。
- baseline中没有的新增Function继续使用绝对Gate。
- 相同Finding数量增加时，增加部分按added处理。
- 有效的Function/Rule豁免同时适用于增量Gate。
- baseline缺失、不完整、identity version或rule version不一致时返回工具错误`2`。
- Function执行不完整时返回`3`，不会伪装成增量通过。

`--enforce`和`--delta-enforce`互斥。CI只读取baseline，不会自动改写`current.json`。

### 5.4 直接使用 Git revision

```bash
python3 specs/tools/spec_eval/ci_runner.py \
  --base origin/master \
  --head HEAD \
  --output out/spec-evaluation \
  --json
```

工具内部执行 `git diff --name-only <base> <head> --` 获取变更文件。

### 5.5 CI 摘要

`ci-summary.json` 包含：

- report-only、enforce或delta-enforce运行模式。
- source revision 和变更文件列表。
- 受影响 Function 数量。
- 每个Function的绝对Gate、增量Gate、baseline状态、Feature数、文档数和Finding数。
- added、resolved、reclassified和unchanged数量。
- Top新增、解决和重分类Finding，以及机器可读reason code。
- 严重度统计和 Top Findings。
- Function 完整报告路径。
- 门禁失败数和工具错误数。

使用 `--top <N>` 控制每个 Function 在摘要中展示的问题数量。

全局Registry、规则配置或核心检查代码发生变化时，工具会评价全部已注册Function；最终仍根据所选绝对或增量模式决定是否阻塞。

### 5.6 GitCode Webhook 消息接收

NEXT-010 第一阶段提供独立的 GitCode Merge Request Webhook 接收器。当前只负责接收、鉴权、
去重和保存最小事件记录，不会检出仓库、执行评价或回写 Pull Request。

本机无鉴权启动：

```bash
python3 specs/tools/spec_eval/gitcode_webhook.py \
  --events-file specs/.evaluator/webhook/receipts.ndjson
```

健康检查：

```bash
curl http://127.0.0.1:8765/healthz
```

`GET /webhooks/gitcode` 同样返回 `200`，用于 GitCode 或反向代理在保存 Webhook 配置时执行
连通性探测；事件投递仍使用 `POST /webhooks/gitcode`。

使用 GitCode WebHook 密码启动：

```bash
export GITCODE_WEBHOOK_TOKEN='<configured-secret>'
python3 specs/tools/spec_eval/gitcode_webhook.py \
  --host 0.0.0.0 \
  --port 8765 \
  --events-file specs/.evaluator/webhook/receipts.ndjson
```

非 loopback 地址必须配置 `GITCODE_WEBHOOK_TOKEN` 或
`GITCODE_WEBHOOK_SIGNATURE_SECRET`。如果两者都配置，接收器会同时校验
`X-GitCode-Token` 和 `X-GitCode-Signature-256`。签名按原始请求正文计算
HMAC-SHA256，并使用 `sha256=<hex>` 格式比对；首次连接真实 GitCode Webhook 时仍需用测试投递
确认服务端与平台的签名正文完全一致。

Webhook 地址默认为：

```text
POST /webhooks/gitcode
```

接收器要求：

- `Content-Type: application/json`。
- `X-GitCode-Event: Merge Request Hook`。
- 非空的 `X-GitCode-Delivery`，用于跨重启去重。
- `event_type` 和 `object_kind` 均为 `merge_request`。

GitCode 的真实 `update` 事件可能省略顶层 `git_commit_no` 或
`git_target_branch_commit_no`。接收器优先使用顶层 SHA，缺失时使用
`object_attributes.last_commit.id` 作为待测 revision；仍缺失的目标 SHA 保留为 `null`，由后续
CI Worker 通过 PR API 或 fetch 后补齐，不因此拒绝基本事件接收。

成功事件返回 HTTP `202`。重复 Delivery 也返回 `202`，但响应中
`duplicate` 为 `true`，NDJSON 中不会重复写入。接收记录不保存 PR 描述、提交消息、作者姓名或邮箱；
只保留后续 CI 路由需要的项目、PR、分支和 revision 字段。

如果同一个 GitCode Webhook 同时启用了 Push Event，接收器会对
`X-GitCode-Event: Push Hook` 返回 HTTP `202` 和 `status: ignored`，不写入 MR receipt，避免
GitCode 将无关事件标记为失败或持续重试。

### 5.7 CI 服务：接收器 + Worker（receipt 后自动触发评价）

接收器只负责入队 receipt 并快速返回 202；**实际评价由独立的 CI Worker**
（`ci_worker.py`）消费 receipt 完成。两者解耦：接收器保持轻量，Worker 串行执行、
崩溃自愈（未标记完成的 delivery 下一轮自动补跑），可独立重启。

一键同时拉起两者：

```bash
./specs/tools/spec_eval/ci_service.sh
```

`ci_service.sh` 会在后台启动接收器（默认 `127.0.0.1:8765`），前台启动
`ci_worker.py --watch`（默认每 10s 轮询 receipt），Ctrl-C 同时关闭两者。
Token 优先取 `GITCODE_WEBHOOK_TOKEN`，否则读 `~/.gitcode_webhook_token`。可用的环境变量覆盖：
`WEBHOOK_HOST`、`WEBHOOK_PORT`、`SPEC_EVAL_REPO`（白名单 owner/repo，默认
`arkui_architecture/arkui-specs`）、`CI_POLL_INTERVAL`、`EXTRA_WORKER_ARGS`
（如 `EXTRA_WORKER_ARGS=--dry-run` 只归档不发评论）。

只起 Worker（不接 webhook，消费已有 receipt 后退出）：

```bash
python3 specs/tools/spec_eval/ci_worker.py \
  --repo arkui_architecture/arkui-specs --allow-project arkui_architecture/arkui-specs --json
```

Worker 常驻轮询模式（无接收器也可，配合外部写入 receipt）：

```bash
python3 specs/tools/spec_eval/ci_worker.py \
  --repo arkui_architecture/arkui-specs --allow-project arkui_architecture/arkui-specs \
  --watch --poll-interval 10
```

Worker 处理每条 receipt 时：校验项目白名单 → 解析 tested/target SHA → 校验 specs 工作树
在 tested SHA（不匹配则跳过，可选 `--auto-checkout`）→ `git -C specs diff` 取变更文件并加
`specs/` 前缀 → 以 report-only、非阻塞方式运行 `ci_runner.py`（对冻结 baseline 做 delta）
→ 按 PR/按 delivery 归档到 `specs/.evaluator/ci/pr-<iid>/<delivery>/` → 通过 `oh-gc`
回写**可更新**的 PR 评论（首条创建，后续按隐藏标记 edit-in-place）。幂等：receipt 入库去重
+ `processed.ndjson` 处理去重。report-only 永远不阻塞 PR。

## 6. 输出目录

默认输出位于 `out/spec-evaluation/`。建议本地试验使用 `/tmp`，避免污染工作区。

```text
<output>/
├── .cache/
│   └── <FuncID>/<fingerprint>.json
└── <git-revision>/
    ├── ci-summary.json
    ├── baseline-summary.json
    ├── performance-summary.json
    └── <FuncID>/
        ├── function-context.json
        ├── static-result.json
        ├── evidence-manifest.json
        ├── performance.json
        ├── report.md
        └── evidence/
            ├── Feat-01.json
            ├── Feat-02.json
            └── design.json
```

主要文件作用：

| 文件 | 作用 |
|---|---|
| `function-context.json` | 完整 Function 输入、Registry 条目和版本信息 |
| `static-result.json` | Function 门禁、Findings、指标和追溯图 |
| `evidence-manifest.json` | 证据分片清单和证据覆盖指标 |
| `evidence/*.json` | 按 Feature/Design 切分的 Claim、源码和 SDK 证据 |
| `score-result.json` | `score` 命令基于完成态语义结果生成的确定性维度得分、发布分、Gate、置信度和准入状态 |
| `function-analysis.json` | `score --analysis-write` 生成的版本/输入指纹、Top整改项、Feat风险分布和下钻索引 |
| `stability-result.json` | `stability` 命令生成的多run分数波动、Criterion共识、同伴一致率、离群标记和显式选定run |
| `evaluation-report.json` | `report` 命令生成的冻结 Schema 兼容 Function 核心报告 |
| `function-report.md` | `report` 命令生成的整改项、Feat 风险和稳定性 Markdown 总报告 |
| `site-evaluation-report.json` | `site-evaluation` 命令导出的 confirmed Review 语义站点归档 |
| `performance.json` | 单 Function 的 parser/checker/证据/写盘阶段耗时 |
| `report.md` | 面向人工阅读的 Function 静态评价报告 |
| `ci-summary.json` | 变更影响Function的CI摘要 |
| `baseline-summary.json` | 全仓Function门禁和规则命中分布 |
| `performance-summary.json` | 全仓或CI批次的总耗时、P50/P95、阶段累计和索引指标 |
| `evaluation/baselines/current.json` | 完整扫描冻结的稳定Finding身份与分类摘要 |

### 6.1 证据归档预算

为防止高频通用 SDK 标识符导致证据重复膨胀，工具执行以下限制：

- 每个具体 API 最多归档 20 条代表性 canonical 声明；API 是否存在的判定不依赖归档条数。
- 单条源码证据片段最多 12,000 个字符，文件哈希仍基于完整原文件。
- 单个 evidence shard 预算为 2 MiB，单 Function 全部 shard 预算为 8 MiB。
- 超限不会改变质量 Gate，但会在 `evidence-manifest.json.archive.warnings` 中输出明确告警。

## 7. 门禁和退出码

默认门禁策略：

| 严重度 | 默认门禁 |
|---|---|
| Critical | fail |
| Major | fail |
| Minor | warn |
| Info | pass |

部分规则可以在 `gate_rules.yaml` 中覆盖默认严重度和门禁。例如绝对路径、死链接和图表问题当前按 `warn` 处理。

统一退出码：

| 退出码 | 含义 |
|---:|---|
| `0` | 门禁通过；或CI report-only模式仅存在质量问题 |
| `1` | Function质量门禁失败 |
| `2` | 输入、配置、Registry、Git或底层工具错误 |
| `3` | Function评价不完整或全仓/CI中存在Function执行错误 |

CI脚本中，执行不完整的优先级高于质量门禁失败，不会因为report-only模式而隐藏工具错误。

## 8. 配置和数据协议

正式配置位于 [`specs/evaluation`](../../evaluation/)：

| 文件/目录 | 作用 |
|---|---|
| `gate_rules.yaml` | 严重度和Function门禁策略 |
| `structure_rules.yaml` | Spec/Design结构规则配置 |
| `citation_rules.yaml` | 源码引用检查配置 |
| `sdk_rules.yaml` | SDK声明定位配置 |
| `exemptions.yaml` | 带Owner、原因和到期时间的临时豁免 |
| `rule_applicability.yaml` | 活跃静态规则的适用性、前置条件、抑制条件和推荐Gate |
| `rubric.yaml` | Rubric v0.3候选版：五维权重、20项Criterion、扣分、封顶、置信度和准入规则 |
| `complexity_rules.yaml` | Feature复杂度归一和Function级聚合、评审深度及N/A资格 |
| `design_completeness_rules.yaml` | Design六项完整性Criterion的Function/Feat覆盖要求及脚本/Skill分工 |
| `schemas/` | Function Context、静态结果、证据、报告、Baseline和单Function评价JSON Schema |
| `baselines/current.json` | 当前可比较的完整Finding存量基线 |
| `golden/manifest.yaml` | 参考评价Pilot、冻结revision和Function输入指纹 |
| `golden/static_expectations.yaml` | Top 10 Rule的30个跨域校准样本和精确Finding计数 |
| `reviews/<func_id>.yaml` | 每个Function唯一的待评价或已确认参考评价 |

临时方案和任务拆分位于 [`specs/.evaluator`](../../.evaluator/)；它们不属于正式 Feature/Design 基线。

### 8.1 校验 Rubric v0.3 协议

协议校验不依赖第三方 `jsonschema` 包。仓内校验器会同时检查：

- 五个维度权重总和、维度内Criterion满分和稳定ID唯一性。
- 六种语义结论、每种结论的扣分上限和Critical/Major证据要求。
- N/A允许条件、最低可评价比例和`NOT_VERIFIABLE`保护。
- Critical/Major/Minor发布分封顶与静态Gate优先级。
- 四项置信度权重、工具完整性和准入阈值。
- Rubric、复杂度规则、Evaluator/Aggregator协议和JSON Schema版本一致性。
- Design六项Criterion、必检项顺序、Function/逐Feat覆盖范围和完整性规则版本一致性。

执行：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.protocol_validator \
  --evaluation-root specs/evaluation
```

当前协议状态为`frozen`，已由`sunfei2021`于`2026-08-07`完成单次确认。工程字段已经版本化并由自动化测试保护；当前Pilot采用单次评价、一次确认的入库方式。当前Rubric为`0.3.0`，包含20项Criterion。修改权重、扣分、门禁封顶或结论语义时必须继续提升Rubric版本，不能在同一版本下静默改变含义。

Design维度仍为25分，但从原4项拆分为6项：架构上下文与分层调用链4分、逐Feat端到端运行设计5分、关键算法/数据/状态4分、ADR候选与取舍4分、构建/产物/注册/部署3分、验证与风险闭环5分。标题、表格、图数量、篇幅和自审勾选不能作为`SUPPORTED`证据。

五维固定权重：

| 维度 | 满分 |
|---|---:|
| 事实正确性与证据 | 30 |
| Spec可执行性 | 25 |
| Design设计质量 | 25 |
| 兼容性与系统影响 | 10 |
| Function功能建模质量 | 10 |

Function功能建模质量完全由Skill评价：Feat覆盖完整性4分、Feat拆分与颗粒度3分、Feat职责边界3分。该维度直接复用Registry、Spec、Design、源码和测试证据，不要求维护独立能力基线清单，也不以Feat数量、文档篇幅或AC数量作为质量信号。

发布分使用最严格未豁免问题封顶：Critical最高39分、Major最高59分、Minor最高79分、无Gate问题最高100分。语义评价只能增加问题，不能删除静态Finding或把静态Gate降级。

### 8.2 单Function参考评价

NEXT-006使用12个Function作为Pilot，当前已全部完成一次评价确认。样本、冻结输入revision和Function指纹位于`evaluation/golden/manifest.yaml`；每个Function只在`evaluation/reviews/`保留一份当前评价文件。Rubric升级后，旧版本Review必须按v0.3补齐Function建模Criterion并重新确认，不能沿用旧可维护性分数。

`revisions.specs`记录选择Pilot输入时的仓库revision，不与当前`specs`仓HEAD强制相等；评价协议和Review也位于同一仓库，正常提交不应使冻结输入失效。Registry、Spec和Design内容漂移由每个Function的`input_fingerprint`检查，ace_engine、sdk-js和sdk_c仍执行严格revision核验。

校验Pilot覆盖和输入是否漂移：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator
```

生成单个待评价草稿：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator \
  --template 03-07-01 \
  --evaluator-id sunfei2021 \
  > specs/evaluation/reviews/03-07-01.yaml
```

Rubric升级后批量刷新已有草稿（不会修改`confirmed`或`superseded`记录）：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator --refresh-drafts
```

校验单份评价：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator \
  --evaluation specs/evaluation/reviews/03-07-01.yaml
```

草稿允许20项Criterion暂时为`NOT_VERIFIABLE`且分数为`null`。确认入库前必须完成真实结论、证据和精确分数，并记录一次`accepted`确认。静态信号分层仅用于选样，不能代替质量等级。

规则修改后除普通单测外，还必须运行：

```bash
PYTHONPATH=specs/tools python3 -m unittest \
  specs.tools.spec_eval.tests.test_rule_calibration -v
```

该测试验证34条活跃规则的适用性矩阵、30个Top 10跨域样本，以及已确认误报的最小复现和真实Function回归。

## 9. 缓存行为

缓存键由以下内容共同决定：

- FuncID。
- Git source revision。
- 工具版本和规则版本。
- Function下全部spec/design内容。
- Function和Feature Registry内容。
- 评价规则YAML内容。

任一 Feature 变化都会使整个 Function 重新聚合。规则版本、Registry或源码revision变化也会使对应缓存失效。

排查缓存问题时使用：

```bash
python3 specs/tools/spec_eval/cli.py \
  --no-cache check --func-id 05-03-10
```

## 10. 测试

运行全部测试：

```bash
PYTHONPATH=specs/tools python3 -m unittest discover \
  -s specs/tools/spec_eval/tests -v
```

运行新增的参考评价、Mutation和CI测试：

```bash
PYTHONPATH=specs/tools python3 -m unittest \
  specs.tools.spec_eval.tests.test_infra_016_017 -v
```

运行Rubric和语义协议边界测试：

```bash
PYTHONPATH=specs/tools python3 -m unittest \
  specs.tools.spec_eval.tests.test_next_005_protocol -v
```

运行Function输入冻结和单次评价确认协议测试：

```bash
PYTHONPATH=specs/tools python3 -m unittest \
  specs.tools.spec_eval.tests.test_next_006_evaluation -v
```

执行语法检查：

```bash
PYTHONPATH=specs/tools python3 -m compileall -q \
  specs/tools/spec_eval
```

测试产生的 `__pycache__` 不属于评价产物，可以安全清理。

## 11. 推荐落地流程

1. 开发者在本地使用 `discover` 确认变更映射的完整 Function。
2. 使用 `check --func-id` 查看确定性问题并打开 `report.md` 整改。
3. 使用 `evidence --func-id` 检查后续评价 Skill 所需证据是否完整。
4. PR阶段先使用 `ci_runner.py` report-only模式统计运行时间和误报。
5. 历史Function建立基线后，再启用 `--enforce` 阻塞新增问题。
6. 每日使用 `scan --all` 更新全仓基线和规则命中分布。

## 12. 已知限制与排障

### 门禁失败但报告已生成

这是正常质量结果。检查 `static-result.json` 或 `report.md`，不要将退出码 `1` 当成工具崩溃。

### SDK或源码定位失败

检查：

- 是否从正确的OpenHarmony源码树运行。
- SDK声明仓是否存在。
- `rg` 是否可用。
- 引用是否使用仓库相对路径；如果提供行号，范围是否有效。
- 被搜索文件是否包含非UTF-8内容。

SDK索引和源码读取统一使用UTF-8替换模式处理不可解码字节。超大Function仍可能出现较长运行时间；CI应保留 `ci-summary.json` 和 `performance-summary.json`，并通过退出码 `2/3` 区分工具错误和普通质量问题。

### 历史Function全部或大量失败

在历史基线和规则尚未校准前应使用report-only模式。不要直接启用全量enforce；应优先治理新增Function、新增Critical/Major问题和相对基线恶化。

### 评价结果不包含语义总分

当前报告只包含确定性门禁、追溯率、引用成功率和证据覆盖率。完整语义评分需要后续评价 Skill 对源码事实、AC质量和Design深度进行判断。

## 13. 代码结构

```text
spec_eval/
├── discovery/     # Function和Registry发现
├── parser/        # Markdown、表格、ID和引用解析
├── checks/        # 确定性规则检查器
├── evidence/      # 源码、SDK和Claim证据构建
├── models/        # Function、Finding、TraceGraph和结果模型
├── rules/         # 规则加载、严重度和门禁聚合
├── report/        # JSON、Markdown和基线报告
├── cache/         # Function输入指纹和结果缓存
├── tests/         # 单元、Fixture、参考评价、Mutation和CI测试
├── protocol_validator.py  # Rubric、复杂度、Schema和结果跨字段校验
├── evaluation_validator.py # Function输入指纹、评价模板和单次确认校验
├── cli.py         # 本地和全仓统一入口
├── ci_runner.py   # 变更Function的CI入口
├── gitcode_webhook.py # GitCode Merge Request Webhook接收入口
├── service/       # 本地语义评价服务（domain/store/scheduler/pipeline/executors/http/ui）
├── service_cli.py # 语义评价服务入口（serve/metrics/cleanup/backup）
└── SEMANTIC_SERVICE.md # 语义服务部署、Executor配置、数据目录和治理手册
```

新增检查器时应保持以下约束：

- 检查器只产生 `Finding`，不直接决定退出码或门禁。
- Finding必须包含稳定规则ID、严重度、路径、行号和FuncID。
- Feature内部ID必须以FeatID作为Function级命名空间。
- 不直接修改spec、design、registry或生产源码。
- 新规则必须补充正反例、Mutation或参考样本测试。

## 14. 本地语义评价服务（手动滚动刷新，TASK-011 / NEXT-012）

`service_cli.py` 把 evidence → staged semantic → 聚合 → 归档流程工程化为一个本地、
可恢复、可观测的服务。当前版本以**手动指定 FuncID 刷新**为唯一调度入口；定时滚动扫描、
每日 token 额度和自动挑选过期 Function 尚未实现。服务复用已有评价 Skill 和
`spec_eval` 的 evidence/score/report 能力，不重写 Rubric，也不修改 Spec、Design、Registry
或 confirmed Review。详细部署、API、数据目录和排障见
[`SEMANTIC_SERVICE.md`](./SEMANTIC_SERVICE.md)。

### 14.1 启动和界面

从 `ace_engine` 根目录运行：

```bash
# 分别确认 CLI 可执行和登录状态
codex --version
codex login status

# 默认数据目录：specs/.evaluator/service-data/
# 默认绑定 127.0.0.1:8790
python3 specs/tools/spec_eval/service_cli.py serve --port 8790 --max-workers 2
```

浏览器打开 `http://127.0.0.1:8790/`。界面支持：

- 输入 FuncID、run 数量和可选 ace_engine revision，手动启动刷新。
- 按 `--max-workers` 并行执行不同任务，每 2 秒刷新 Job 状态、阶段和事件；执行中的任务显示旋转/流光动效，持续时间每秒更新。
- 在任务列表、详情和顶部统计卡中查看总历时、Executor 累计耗时、调用次数、Token 消耗与 usage 上报覆盖率。
- evaluator 0.1.12 起会把 Skill 校验器同源的字段级契约注入 Codex prompt；若 observation 候选仅有 `EV-`、`sha256:`、evidence type、Criterion ID 或 defect ownership 等白名单格式错误，服务最多执行一次不重读证据的机械修复。
- evaluator 0.1.13 会在聚合前生成 `aggregation-context.json`，固定 observation/Claim/atomic unit 到 Criterion 的映射；若 aggregation 候选仅违反映射结论或 Claim 引用规则，服务最多执行一次只读取候选、模板、输出契约和映射上下文的受限对账，不会重读源码或改写 observation。
- evaluator 0.1.14 将 observation outcome 对 evidence 最小条数的要求写入机器契约：除 `NOT_VERIFIABLE` 外均至少 1 条，`NOT_APPLICABLE` 也必须引用证明不适用的冻结证据。若候选仅有空 evidence，服务最多执行一次读取原始作用域输入的补证；任何 outcome、fact、映射、ownership 或非目标 evidence 漂移都会被拒绝。
- evaluator 0.1.15 将最终 Finding/criterion-result Schema 同源发布到聚合机器契约，并在发布 aggregation 前构建内存 final candidate 执行最终校验。服务可进行一次不调用模型的确定性结构修复：无歧义地迁移 `problem` 到 `message`、补齐已有证据支持的 N/A 原因，并按 FuncID/defect/Criterion/Claim 稳定身份重写 Finding ID 与 ownership 引用；冲突别名或其他语义漂移会直接失败。
- evaluator 0.1.16 将 Finding ID 和 `secondary_criterion_ids` 明确为服务端归一化字段：模型只提供唯一临时 Finding 关联键，不再计算或猜测 SHA-256；服务在首次聚合校验前固定执行一次 canonical ID、ownership 引用和 secondary 集合归一化，再处理剩余校验或进入 mapping reconciliation。secondary 语义影响必须由同一 ownership 下的实际 Finding 表达，服务不会自动生成语义 Finding。
- 查看全部 Function 的当前报告、版本、分数、Gate、刷新状态和历史数量。
- 按新鲜度筛选 `FRESH`、`EXPIRING`、`EXPIRED_TIME`、`STALE_INPUT` 和 `MISSING`。
- 取消活动任务、重试失败任务，并查看单 Function 的历史报告和 Finding delta。

非 loopback 监听必须配置 token，并由 API 客户端发送
`Authorization: Bearer <token>`。内置界面当前没有 token 输入框，远程使用时应通过能注入
认证头的反向代理访问，或直接调用 API：

```bash
python3 specs/tools/spec_eval/service_cli.py serve \
  --host 0.0.0.0 --port 8790 --max-workers 2 --token "$TOKEN"
```

### 14.2 推荐的手动刷新 API

滚动报告应使用 Function refresh API。它会在提交时冻结四仓 revision、对活动任务去重，
并为该 Function 分配单调递增的 generation：

```bash
# source_revision 省略时使用当前 ace_engine HEAD；也可传完整 SHA、分支或 tag
curl -sX POST http://127.0.0.1:8790/api/functions/04-01-01/refresh \
  -H 'Content-Type: application/json' \
  -d '{"run_count":1,"source_revision":"HEAD"}'

# Function 当前状态、历史和新鲜度
curl -s  http://127.0.0.1:8790/api/functions/04-01-01
curl -s  http://127.0.0.1:8790/api/functions/04-01-01/history
curl -s  http://127.0.0.1:8790/api/functions/04-01-01/freshness
curl -s 'http://127.0.0.1:8790/api/functions?freshness=EXPIRING'
```

相同 FuncID、四仓 revision、Evaluator/协议版本和 `run_count` 的活动请求返回已有 Job
（HTTP 200，`deduplicated: true`）；新请求返回 HTTP 202。较旧 generation 即使更晚完成，
也只进入历史记录，不能覆盖更新的 Function 当前报告。

`POST /api/jobs` 是兼容的底层 Job 入口，不建立 refresh target，因此不应作为滚动报告刷新
入口。Job 查询和控制接口如下：

```bash
curl -s 'http://127.0.0.1:8790/api/jobs?status=completed'
curl -s  http://127.0.0.1:8790/api/jobs/<job_id>
curl -s 'http://127.0.0.1:8790/api/jobs/<job_id>/events?since_seq=0'
curl -sX POST http://127.0.0.1:8790/api/jobs/<job_id>/cancel
curl -sX POST http://127.0.0.1:8790/api/jobs/<job_id>/retry
curl -s  http://127.0.0.1:8790/api/jobs/<job_id>/artifacts/score-result -o score.json
```

取消接口按 Job 生命周期返回结构化结果：`queued`/`awaiting_executor` 立即落为
`cancelled` 并返回 HTTP 200；semantic/aggregation 等活动 worker 返回 HTTP 202
`cancellation_requested`，由 worker 在退出前持久化终态；已完成或不可取消阶段返回
HTTP 409，并携带准确的 `outcome`、`status` 和 `error`。内置 UI 会展示 Cancel/Retry
失败信息，不再静默吞掉 409/5xx。

内置 UI 的 Function reports 和 Jobs 表格分别独立分页。分页在新鲜度/状态筛选之后执行，
默认每页 10 条，可切换为 10/50/100 条；筛选条件或每页条数变化时回到第一页，后台轮询
刷新时保留当前页，数据减少导致页码越界时自动回退到最后一个有效页。

### 14.3 Revision 隔离和并行约束

手动刷新提交时会解析并记录 `ace_engine`、`specs`、`sdk-js`、`sdk_c` 四个仓库的精确
commit。每个 Job 在 `<data-root>/workspaces/<job_id>/` 下创建一套 OpenHarmony 形状的
detached Git worktree，evidence、评价 Skill、Rubric 和 SDK 读取均来自这套冻结工作区：

- 用户原始 checkout 即使有未提交修改也不会被读取或切换。
- reservation manifest 在创建 worktree 前写入；进程中断后 retry 复用同一组 revision。
- Job 进入 `completed`、`failed` 或 `cancelled` 后释放 worktree，但保留 manifest 用于追溯。
- `--max-workers` 控制 Job 并发数；同一 FuncID 的执行仍受 Function 资源锁约束。

### 14.4 报告、新鲜度和静态导出

完成态自动报告位于
`<data-root>/archives/automated/<ace-revision>/<func-id>/<job-id>/`。归档通过临时目录原子
发布，并用 `archive-manifest.json` 保存文件 SHA-256；发布后的归档不会被 retry 覆盖。
SQLite 只保存报告索引、Function 当前指针、revision/fingerprint、刷新 generation、新鲜度
策略、delta 摘要和轻量 `job_statistics`。统计表只记录开始/结束时间、Executor 毫秒数、
调用/上报次数及 input/cached/cache-write/output/reasoning/total Token 整数；不记录 Prompt、
回复正文、凭据或认证状态。大型 evidence、日志和报告仍在文件系统中。

Codex JSONL 在日志脱敏前提取 usage。当前兼容 `turn.completed.usage` 和
`token_count.info.total_token_usage` 两类已观测格式；CLI 未上报或出现未知格式时界面明确显示
`not reported`，不会把估算值伪装成精确消耗。可通过以下接口查看单任务和全局统计：

```bash
curl -s http://127.0.0.1:8790/api/jobs/<job_id>
curl -s http://127.0.0.1:8790/api/metrics
```

默认新鲜度策略是 30 天有效、到期前 7 天进入 `EXPIRING`。FuncID 专属策略优先于全局
策略，且要求 `0 <= warning_days < max_age_days`：

```bash
curl -s http://127.0.0.1:8790/api/freshness-policies
curl -sX PUT http://127.0.0.1:8790/api/freshness-policies/global \
  -H 'Content-Type: application/json' \
  -d '{"max_age_days":30,"warning_days":7}'
curl -sX PUT http://127.0.0.1:8790/api/freshness-policies/04-01-01 \
  -H 'Content-Type: application/json' \
  -d '{"max_age_days":14,"warning_days":3}'
```

各状态含义：

| 状态 | 含义 |
|---|---|
| `MISSING` | 该 Function 尚无当前自动报告 |
| `FRESH` | 报告输入与期望目标一致，且未进入预警期 |
| `EXPIRING` | 报告尚未过期，但已进入 `warning_days` 预警窗口 |
| `EXPIRED_TIME` | 报告完成时间已超过 `max_age_days` |
| `STALE_INPUT` | 已登记更新的 revision/输入目标，当前报告仍对应旧输入 |

按需生成站点消费的确定性静态 JSON：

```bash
curl -sX POST http://127.0.0.1:8790/api/site/export
```

输出位于 `<data-root>/exports/`，包括 Function 索引、站点摘要和每个 FuncID 的历史文件。
允许不同 Function 的当前报告来自不同 revision；摘要会显式给出 `mixed_revisions` 和
`report_revisions`。自动归档、自动 history 和 export 均位于 service data root，不覆盖
`evaluation/reviews/`、confirmed Review 站点归档或 CI delta baseline。

### 14.5 治理子命令和边界

```bash
python3 specs/tools/spec_eval/service_cli.py metrics --write metrics.json [--format csv]
python3 specs/tools/spec_eval/service_cli.py cleanup --retention-days 14   # 只清临时 run，不删归档
python3 specs/tools/spec_eval/service_cli.py backup                        # WAL checkpoint + 恢复校验
```

- Codex 不可用时，semantic 阶段进入 `awaiting_executor`；修复本机 CLI 后调度器会重新探测。
- 本阶段只有 Codex CLI Executor；不会调用 Claude CLI、远程 Agent API 或其他模型后端。
- `metrics` 同时导出任务/排队/Executor 耗时、Executor 调用次数、Token 分类汇总和 usage 上报覆盖率。
- 当前不会自动扫描过期 Function，也没有每日 token 配额；这些属于后续滚动调度阶段。
- 本服务不修改冻结的 Spec/Design/Registry、CI delta 门禁或父仓 `ace_engine` 生产代码。
