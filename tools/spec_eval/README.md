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

这些判断由后续评价 Skill 消费本工具生成的证据包完成。NEXT-005 已经冻结候选版机器协议，但尚未实现评价 Skill 和实际聚合器，因此当前 `check`、`evidence`、`scan` 仍不输出语义总分。静态工具不会自动修改任何 spec、design 或 registry 文件。

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

### 3.4 根据变更文件评价受影响 Function

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

### 3.5 全仓扫描

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

### 3.6 冻结稳定 Finding 基线

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

### 3.7 对比当前结果和基线

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

当前协议状态为`candidate`。工程字段已经版本化并由自动化测试保护；当前Pilot采用单次评价、一次确认的入库方式。当前Rubric为`0.3.0`，包含20项Criterion。修改权重、扣分、门禁封顶或结论语义时必须继续提升Rubric版本，不能在同一版本下静默改变含义。

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

NEXT-006使用12个Function作为Pilot。样本、输入revision和Function指纹位于`evaluation/golden/manifest.yaml`；每个Function只在`evaluation/reviews/`保留一份当前评价文件。Rubric升级后，旧版本Review必须按v0.3补齐Function建模Criterion并重新确认，不能沿用旧可维护性分数。

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
└── ci_runner.py   # 变更Function的CI入口
```

新增检查器时应保持以下约束：

- 检查器只产生 `Finding`，不直接决定退出码或门禁。
- Finding必须包含稳定规则ID、严重度、路径、行号和FuncID。
- Feature内部ID必须以FeatID作为Function级命名空间。
- 不直接修改spec、design、registry或生产源码。
- 新规则必须补充正反例、Mutation或参考样本测试。
