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

这些判断由后续评价 Skill 消费本工具生成的证据包完成。静态工具不会自动修改任何 spec、design 或 registry 文件。

## 2. 环境要求

从 `ace_engine` 仓库根目录运行命令。

基础依赖：

- Python 3.10 或兼容版本。
- PyYAML。
- Git，用于记录源码 revision 和计算变更文件。
- ripgrep（`rg`），用于源码和 SDK 声明定位。

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

### 3.6 对比两个基线

```bash
python3 specs/tools/spec_eval/cli.py --json compare \
  --current /tmp/spec-evaluation/current \
  --baseline /tmp/spec-evaluation/baseline
```

对比结果按 FuncID 给出新增、解决和未变化的确定性问题。

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

### 5.2 Enforce 模式

规则和历史基线完成校准后，可以启用阻塞：

```bash
python3 specs/tools/spec_eval/ci_runner.py \
  --files-from changed-files.txt \
  --output out/spec-evaluation \
  --enforce --json
```

只要任一受影响 Function 的门禁为 `fail`，命令返回 `1`。

### 5.3 直接使用 Git revision

```bash
python3 specs/tools/spec_eval/ci_runner.py \
  --base origin/master \
  --head HEAD \
  --output out/spec-evaluation \
  --json
```

工具内部执行 `git diff --name-only <base> <head> --` 获取变更文件。

### 5.4 CI 摘要

`ci-summary.json` 包含：

- report-only 或 enforce 运行模式。
- source revision 和变更文件列表。
- 受影响 Function 数量。
- 每个 Function 的门禁、Feature 数、文档数和 Finding 数。
- 严重度统计和 Top Findings。
- Function 完整报告路径。
- 门禁失败数和工具错误数。

使用 `--top <N>` 控制每个 Function 在摘要中展示的问题数量。

## 6. 输出目录

默认输出位于 `out/spec-evaluation/`。建议本地试验使用 `/tmp`，避免污染工作区。

```text
<output>/
├── .cache/
│   └── <FuncID>/<fingerprint>.json
└── <git-revision>/
    ├── ci-summary.json
    ├── baseline-summary.json
    └── <FuncID>/
        ├── function-context.json
        ├── static-result.json
        ├── evidence-manifest.json
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
| `report.md` | 面向人工阅读的 Function 静态评价报告 |
| `ci-summary.json` | 变更影响Function的CI摘要 |
| `baseline-summary.json` | 全仓Function门禁和规则命中分布 |

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
| `schemas/` | Function Context、静态结果、证据和报告JSON Schema |
| `golden/manifest.yaml` | 真实Function Golden样本及确定性预期 |
| `golden/static_expectations.yaml` | Top 10 Rule的30个跨域校准样本和精确Finding计数 |

临时方案和任务拆分位于 [`specs/.evaluator`](../../.evaluator/)；它们不属于正式 Feature/Design 基线。

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

运行新增的Golden、Mutation和CI测试：

```bash
PYTHONPATH=specs/tools python3 -m unittest \
  specs.tools.spec_eval.tests.test_infra_016_017 -v
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

目前SDK搜索遇到非UTF-8输出时可能返回工具错误；超大Function也可能出现较长运行时间。CI应保留 `ci-summary.json`，并通过退出码 `2/3` 区分工具错误和普通质量问题。

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
├── tests/         # 单元、Fixture、Golden、Mutation和CI测试
├── cli.py         # 本地和全仓统一入口
└── ci_runner.py   # 变更Function的CI入口
```

新增检查器时应保持以下约束：

- 检查器只产生 `Finding`，不直接决定退出码或门禁。
- Finding必须包含稳定规则ID、严重度、路径、行号和FuncID。
- Feature内部ID必须以FeatID作为Function级命名空间。
- 不直接修改spec、design、registry或生产源码。
- 新规则必须补充正反例、Mutation或Golden测试。
