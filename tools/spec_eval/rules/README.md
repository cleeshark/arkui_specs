# Spec Evaluator 规则说明

本文档说明 `spec_eval` 当前已经实现的确定性规则、严重度与门禁机制、规则配置方式、临时豁免要求，以及新增规则时必须完成的开发和测试步骤。

工具使用 Function（FuncID）作为最小评价单元。每条规则可以定位到某个 Feature、共享 Design、Registry 或 Function，但最终门禁始终聚合到整个 Function。

当前共实现 49 条规则，分为以下类别：

| 前缀 | 类别 | 数量 | 检查器 |
|---|---|---:|---|
| `REG-*` | Registry与磁盘一致性 | 12 | `RegistryChecker` |
| `SPEC-STRUCT-*` | Feature Spec固定结构 | 10 | `SpecStructureChecker` |
| `DESIGN-STRUCT-*` | Function共享Design固定结构 | 9 | `DesignStructureChecker` |
| `HYGIENE-*`、`LINK-*`、`DIAGRAM-*` | 文档卫生、链接和图表 | 6 | `HygieneChecker` |
| `TRACE-*` | Function内追溯闭环 | 4 | `TraceabilityChecker` |
| `REF-*` | 源码引用机械有效性 | 6 | `ReferenceChecker` |
| `SDK-*` | canonical SDK声明定位 | 2 | `SdkContractChecker` |

## 1. Finding 数据协议

检查器只产生 `Finding`，不直接决定进程退出码。每条 Finding 的主要字段如下：

| 字段 | 必填 | 说明 |
|---|---|---|
| `rule_id` | 是 | 稳定规则ID，例如 `TRACE-AC-NO-VM-001` |
| `severity` | 是 | 检查器建议严重度；规则引擎可根据YAML覆盖 |
| `message` | 是 | 面向整改人员的问题描述 |
| `path` | 是 | 仓库相对文件路径 |
| `line` | 否 | 可以确定时给出1开始的原文行号 |
| `func_id` | 是 | Finding所属完整Function |
| `feat_id` | 否 | 问题属于具体Feature时填写 |
| `claim_id` | 否 | 问题关联证据Claim时填写 |
| `recommendation` | 否 | 可机械给出时提供整改建议 |
| `details` | 否 | 规则专有结构化信息，例如缺失章节、无效范围或目标路径 |

Finding必须能够归属到FuncID。Feature内部使用的AC、Rule和VM局部ID不能作为正式门禁单元。

## 2. 严重度与Function门禁

严重度从低到高为：

```text
Info < Minor < Major < Critical
```

默认门禁策略：

| 严重度 | 默认门禁 | 含义 |
|---|---|---|
| Info | `pass` | 仅记录信息 |
| Minor | `warn` | Function可继续，但应整改 |
| Major | `fail` | Function静态门禁失败 |
| Critical | `fail` | Function静态门禁失败，优先处理 |

Function门禁取所有未豁免Finding中的最高门禁：

```text
pass < warn < fail < error
```

规则引擎处理顺序：

1. 检查器产生原始Finding和建议严重度。
2. 按 `gate_rules.yaml` 中匹配的规则覆盖严重度或门禁。
3. 检查该FuncID是否存在有效豁免。
4. 未豁免Finding参与Function门禁聚合。
5. 所有Finding仍保留在报告中，并参与严重度数量统计。

当前显式覆盖策略：

| 规则模式 | 最终严重度 | 最终门禁 |
|---|---|---|
| `HYGIENE-ABSOLUTE-PATH-*` | Minor | warn |
| `LINK-*` | Minor | warn |
| `DIAGRAM-*` | Minor | warn |
| `SDK-ROOT-MISSING-*` | Major | fail |

其他规则使用检查器严重度和默认门禁。目前除上述Minor规则外，已实现规则主要按Major/fail处理。

## 3. Registry规则

实现位置：[`checks/registry_checks.py`](../checks/registry_checks.py)

| 规则ID | 触发条件 | 严重度/门禁 | 定位与整改 |
|---|---|---|---|
| `REG-FUNC-ID-001` | FuncID不符合 `NN-NN-NN` 格式 | Major/fail | 定位 `functions.yaml`；修正Function ID |
| `REG-FUNC-PATH-001` | Registry登记的Function目录不存在 | Major/fail | 定位Function Registry条目；修正路径或补齐目录 |
| `REG-DESIGN-MISSING-001` | Registry登记了design，但文件不存在 | Major/fail | 定位 `functions.yaml`；修正design路径或补齐文件 |
| `REG-DESIGN-UNREGISTERED-001` | 磁盘存在 `design.md`，但Function未登记 | Major/fail | 定位实际design；在Registry中登记正确路径 |
| `REG-FEAT-ID-001` | FeatID不符合 `Feat-NN` 格式 | Major/fail | 定位 `features.yaml`；修正FeatID |
| `REG-SPEC-PATH-EMPTY-001` | 非Draft Feature没有spec路径 | Major/fail | 定位Feature条目；登记spec或将真实状态改为Draft |
| `REG-SPEC-MISSING-001` | Registry登记的Feature spec不存在 | Major/fail | 定位Feature条目；修正路径或补齐spec |
| `REG-SPEC-PATH-MISMATCH-001` | Registry路径与磁盘同FeatID文件不一致 | Major/fail | 对齐Registry和磁盘实际文件路径 |
| `REG-FEAT-CONTIGUOUS-001` | FeatID没有从Feat-01开始连续编号 | Major/fail | 定位Function的Feature集合；补齐或重新编号 |
| `REG-SPEC-UNREGISTERED-001` | 磁盘存在Feature spec，但未登记 | Major/fail | 定位实际spec；补充Feature Registry条目 |
| `REG-SPEC-METADATA-ID-001` | Spec元数据“特性编号”与FuncID/FeatID不一致 | Major/fail | 定位Spec元数据行；使用 `Func-<FuncID>-Feat-NN` |
| `REG-DESIGN-METADATA-ID-001` | Design元数据“Design ID”与FuncID不一致，或ID被Markdown反引号包裹 | Major/fail | 定位Design元数据行；以纯文本填写 `DESIGN-Func-<FuncID>`，不得使用反引号 |

Registry检查不会修改Registry，也不会自动生成索引。

## 4. Spec结构规则

实现位置：[`checks/spec_structure_checks.py`](../checks/spec_structure_checks.py)

| 规则ID | 触发条件 | 严重度/门禁 | 整改方向 |
|---|---|---|---|
| `SPEC-STRUCT-H1-001` | Spec H1不是“特性规格”或缺失 | Major/fail | 使用唯一H1 `# 特性规格` |
| `SPEC-STRUCT-H2-MISSING-001` | 缺少任一标准H2章节 | Major/fail | 补齐 `structure_rules.yaml` 中的标准章节 |
| `SPEC-STRUCT-H2-ORDER-001` | 已存在的标准H2顺序错误 | Major/fail | 按标准章节顺序重新排列 |
| `SPEC-STRUCT-METADATA-001` | 缺少特性名称、编号、优先级、目标版本、状态或复杂度 | Major/fail | 补齐概述元数据表字段 |
| `SPEC-STRUCT-STATUS-001` | 状态不是Draft、Baselined或Deprecated | Major/fail | 使用固定状态值，不附加说明文字 |
| `SPEC-STRUCT-PRIORITY-001` | 优先级不是P0、P1、P2或P3 | Major/fail | 使用固定优先级枚举 |
| `SPEC-STRUCT-TABLE-001` | 用户故事、验收追溯、规则定义或验证映射章节内没有表格 | Major/fail | 在对应章节增加标准表格 |
| `SPEC-STRUCT-TABLE-FIELD-001` | 章节内存在表格，但字段名称、数量或顺序与标准表头不一致；Finding会列出缺失字段、非标准字段，或预期/实际字段顺序 | Major/fail | 按标准字段名和顺序修正表头；验收追溯首列统一使用 `AC编号` |
| `SPEC-STRUCT-AC-TYPE-001` | AC类型不是正常、异常、边界或恢复 | Major/fail | 使用固定AC类型枚举 |
| `SPEC-STRUCT-RULE-TYPE-001` | Rule类型不是行为、边界、异常或恢复 | Major/fail | 使用固定Rule类型枚举 |
| `SPEC-STRUCT-USER-STORY-001` | 用户故事缺少 `### US-N`，或US块未按顺序提供非空的 `**作为**`、`**我想要**`、`**以便**` | Major/fail | 为每个US块补齐角色、目标和价值三行结构化描述 |

当前标准Spec H2顺序：

1. 概述
2. 本次变更范围（Delta）
3. 输入文档
4. 用户故事
5. 验收追溯
6. 规则定义
7. 验证映射
8. API 变更分析
9. 接口规格
10. 兼容性声明
11. 架构约束
12. 非功能性需求
13. 多设备适配声明
14. 全局特性影响
15. Spec 自审清单
16. context-references

标准表头：

| 章节 | 必需表头 |
|---|---|
| 用户故事 | `AC编号`、`验收标准`、`类型` |
| 验收追溯 | `AC编号`、`关联规则`、`关联 Task`、`验证方式`、`证据` |
| 规则定义 | `规则ID`、`类型`、`触发条件`、`预期行为`、`边界/约束`、`关联AC` |
| 验证映射 | `编号`、`对应规格项`、`验证方式`、`验证重点` |

每个用户故事必须使用以下结构，三行顺序固定且内容不能为空：

```markdown
### US-1: 用户故事标题

**作为** 目标用户或角色
**我想要** 完成的能力或行为
**以便** 获得的业务价值或结果
```

允许三行之间存在空行，但不允许缺失、重复、交换顺序或只填写标点。规则只验证结构和非空内容，不判断角色、目标和价值是否具有充分语义质量。

## 5. Design结构规则

实现位置：[`checks/design_structure_checks.py`](../checks/design_structure_checks.py)

| 规则ID | 触发条件 | 严重度/门禁 | 整改方向 |
|---|---|---|---|
| `DESIGN-STRUCT-MISSING-001` | Function没有可读取的 `design.md` | Major/fail | 为Function补齐共享Design并登记 |
| `DESIGN-STRUCT-H1-001` | Design H1不是“架构设计”或缺失 | Major/fail | 使用唯一H1 `# 架构设计` |
| `DESIGN-STRUCT-H2-MISSING-001` | 缺少任一标准Design H2 | Major/fail | 补齐标准章节 |
| `DESIGN-STRUCT-H2-ORDER-001` | 已存在的标准H2顺序错误 | Major/fail | 按标准顺序重新排列 |
| `DESIGN-STRUCT-FEAT-H2-001` | 使用 `## Feat-XX ...` 建立独立顶级章节 | Major/fail | 将增量内容合并进共享Design固定章节 |
| `DESIGN-STRUCT-ID-001` | Design ID不是纯文本 `DESIGN-Func-<FuncID>`；Markdown反引号包裹也属于格式错误 | Major/fail | 修正Design元数据，移除ID两侧反引号 |
| `DESIGN-STRUCT-TARGET-FEAT-001` | “目标 Feature”没有覆盖某个Registry Feature | Major/fail | 在元数据中显式列出全部目标FeatID |
| `DESIGN-STRUCT-ADR-ID-001` | ADR编号既不符合 `ADR-N`，也不符合 `ADR-FN-N` | Major/fail | 基础ADR用 `ADR-N`，增量ADR用 `ADR-F<Feat序号>-N` |
| `DESIGN-STRUCT-ADR-FEAT-001` | 增量ADR引用了未登记的Feature | Major/fail | 修正ADR中的Feature序号或补齐Registry |

当前标准Design H2顺序：

1. 设计元数据
2. 需求基线
3. 上下文和现状
4. 不涉及项承接
5. 关键设计决策
6. 设计骨架
7. 后续 Task 拆分
8. API 签名、Kit 与权限
9. 构建系统影响
10. 可选设计扩展
11. 详细设计
12. 风险和开放问题
13. 设计审批

Design结构规则只验证固定结构、ID和显式Feature覆盖，不判断调用链或ADR内容是否具有语义设计价值。

## 6. 文档卫生、链接和图表规则

实现位置：[`checks/hygiene_checks.py`](../checks/hygiene_checks.py)

| 规则ID | 触发条件 | 严重度/门禁 | 整改方向 |
|---|---|---|---|
| `HYGIENE-PLACEHOLDER-001` | Baselined文档仍包含TODO、TBD、待定或待补充 | Major/fail | 用真实结论替换占位内容；审计声明中的否定描述不会误报 |
| `HYGIENE-ABSOLUTE-PATH-001` | 出现 `/home/<user>/`、`C:\Users\...` 或 `file://...` | Minor/warn | 改为仓库相对路径或可复现URI |
| `HYGIENE-UNCHECKED-AUDIT-001` | Baselined文档存在未勾选自审项 | Minor/warn | 完成自审后勾选，或将文档保持真实Draft状态 |
| `LINK-DEAD-001` | Markdown本地链接按当前文档目录、`specs/`目录或`ace_engine/`仓库根目录解析后均不存在 | Minor/warn | 修正相对路径、文件名或锚点前的文件路径 |
| `DIAGRAM-ASCII-001` | 检测到ASCII/Unicode框线架构图 | Minor/warn | 改用Mermaid等可维护图表 |
| `DIAGRAM-MERMAID-HEADER-001` | Mermaid代码块没有支持的首行指令 | Minor/warn | 使用graph、flowchart、sequenceDiagram、stateDiagram等指令 |

以下链接不会执行本地存在性检查：

- `http://`、`https://`
- 当前文档锚点 `#...`
- `mailto:`

本地链接支持以下路径基准：

- 相对当前Markdown文档所在目录，例如`design.md`
- 相对`specs/`目录，例如`03-engine-framework/08-dfx-foundation/01-logging/design.md`
- 相对`ace_engine/`仓库根目录，例如`docs/architecture/UISession/example.md`或`specs/03-engine-framework/example.md`

## 7. 追溯规则

实现位置：[`checks/traceability_checks.py`](../checks/traceability_checks.py)

| 规则ID | 触发条件 | 严重度/门禁 | 整改方向 |
|---|---|---|---|
| `TRACE-RANGE-ID-001` | 使用 `AC-1.1-AC-2.4`、`AC-1.1~1.12`、`AC-1.1~AC-1.12`、`R-1~R-12` 等范围，连接符两侧可有空格 | Major/fail | 展开成逗号分隔的显式ID列表；范围覆盖节点的NO-VM/NO-RULE连锁Finding会被抑制 |
| `TRACE-AC-NO-RULE-001` | AC没有任何 `specified_by` Rule边 | Major/fail | 在规则表或验收追溯表中显式关联Rule |
| `TRACE-AC-NO-VM-001` | AC没有任何 `verified_by` VM边 | Major/fail | 在验证映射表中逐项关联AC |
| `TRACE-RULE-ORPHAN-001` | Rule没有被任何AC关联 | Major/fail | 关联真实AC，或删除不属于本Feature的规则 |

追溯节点使用Feature命名空间，例如：

```text
Feat-01/AC-1.1
Feat-01/R-1
Feat-01/VM-1
Feat-02/AC-1.1
```

因此不同Feature中相同的局部ID不会冲突。当前闭环率要求一个AC同时存在Rule和VM关联；Task和Evidence边会进入追溯图，但暂不单独产生缺失门禁规则。

## 8. 源码引用规则

实现位置：[`checks/reference_checks.py`](../checks/reference_checks.py)

| 规则ID | 触发条件 | 严重度/门禁 | 整改方向 |
|---|---|---|---|
| `REF-ABSOLUTE-PATH-001` | 源码证据使用个人绝对路径 | Major/fail | 使用ace_engine或OpenHarmony根目录下的仓库相对路径 |
| `REF-NOT-FOUND-001` | 精确引用无法解析到任何文件或目录 | Major/fail | 修正路径、文件扩展名或仓库根目录基准；模板、通配符和外部根路径不应写成本仓精确引用 |
| `REF-AMBIGUOUS-001` | 仅使用文件名等不完整引用，导致可以解析到多个候选文件；`*.d.ts`、`*.d.ets`、`*.static.d.ets` 会同时搜索ace_engine和OpenHarmony `interface/sdk-js`，但排除文档副本目录 `interface/sdk-js/zh-cn` | Major/fail | 使用完整仓内相对路径，例如 `frameworks/.../animator.cpp` 或 `interface/sdk-js/.../common.d.ts`；Finding会直接提示该写法 |
| `REF-LINE-RANGE-001` | 引用行号或范围超出文件边界 | Major/fail | 更新为当前revision下的有效行号 |
| `REF-DISALLOWED-SOURCE-001` | 引用生成文件或site副本作为权威证据 | Major/fail | 改为真实实现或canonical声明来源 |

SDK声明文件名中的 `@` 属于路径本身，例如 `@ohos.arkui.UIContext.d.ts` 和
`@internal/component/ets/enums.d.ts`；解析器会保留该字符。完整的
`interface/sdk-js/...` 引用只解析一次，不再额外产生去掉 `@` 的嵌套短路径。
SDK声明也允许相对`interface/sdk-js/`根目录的`api/...`路径，例如
`api/@internal/component/ets/common.d.ts`。
SDK裸文件名搜索和API声明扫描均以canonical声明为准，不将
`interface/sdk-js/zh-cn` 下的本地化副本计入候选数量。

支持的主要引用形式：

```text
frameworks/core/example.cpp
frameworks/core/example.cpp:120
frameworks/core/example.cpp:120-135
frameworks/core/example.cpp:120-135,150
adapter/ohos/entrance/ace_container.h/cpp
adapter/ohos/build
api/@internal/component/ets/common.d.ts
```

源码文件引用允许使用 `.h/cpp`、`.hpp/cpp`、`.h/.cpp` 等头文件/源文件扩展名合写，工具会展开后分别检查。源码文件引用允许不带行号；行号仅作为可选的定位信息。提供行号或范围时，工具仍会校验其在当前文件中是否有效。精确目录引用会校验目录是否存在，但不要求行号。GN target（例如
`adapter/ohos/build:ace_packages`）会校验 target 所在目录。`<ROOT>`、`*`、`{...}` 等外部根或模板路径，以及 Mermaid 图中的示意节点，不参与本仓精确路径检查。
中文语句中的普通分隔斜杠不会被当作绝对路径起点；仓内路径位于中文全角括号内时，解析会在右括号前结束。

引用机械可解析只表示证据位置有效，不表示该源码真正支持文档结论。事实正确性仍需评价Skill判断。

## 9. SDK规则

实现位置：[`checks/sdk_contract_checks.py`](../checks/sdk_contract_checks.py)

| 规则ID | 触发条件 | 严重度/门禁 | 整改方向 |
|---|---|---|---|
| `SDK-ROOT-MISSING-001` | 文档声明Public/System API，但ArkTS与NDK canonical SDK根目录均不可用 | Major/fail | 检查OpenHarmony源码树中的 `interface/sdk-js/api` 和 `interface/sdk_c` |
| `SDK-API-NOT-FOUND-001` | 明确标记为Public/System的API名在canonical SDK中没有声明，或API表只写`@ohos...`模块/说明性占位而没有列出具体API；InnerApi及未声明开放范围的行不纳入此审计 | Major/fail | 逐项列出具体Public/System API名称或签名；ArkTS API核对 `.d.ts/.d.ets/.static.d.ets`，NDK API核对 `interface/sdk_c` 下的 `.h/.hpp`；两类扫描均排除 `zh-cn` |

SDK检查只处理API表格中开放范围包含Public或System的行。开放范围明确为InnerApi等内部类型时不会执行canonical SDK要求。
API表不能用“已有实现补录”、“具体签名见 Feature spec”或单纯`@ohos...`模块名代替具体API列表；此类写法会继续触发`SDK-API-NOT-FOUND-001`，并提示逐项列出API名称或签名。

当前脚本执行机械声明定位，不直接裁决以下内容：

- 参数和返回值语义是否完全一致。
- 默认值、错误码和版本行为是否一致。
- dynamic、static和Modifier渠道之间的语义差异。

SDK搜索依赖 `rg` 和UTF-8可解码的搜索结果。遇到非UTF-8文件或超大搜索结果时可能产生工具错误或长耗时，应通过退出码 `2/3` 与普通质量门禁区分。

## 10. 规则配置

配置目录：[`specs/evaluation`](../../../evaluation/)

| 文件 | 当前作用 |
|---|---|
| `gate_rules.yaml` | 规则版本、默认门禁、规则模式覆盖 |
| `structure_rules.yaml` | 标准Spec和Design章节基线 |
| `citation_rules.yaml` | 允许的仓库前缀、SDK前缀和禁用路径片段 |
| `sdk_rules.yaml` | canonical SDK根目录、扩展名和渠道声明 |
| `exemptions.yaml` | Function级临时规则豁免 |

### 10.1 门禁覆盖

`gate_rules.yaml` 使用Shell风格通配符匹配规则ID：

```yaml
version: 0.1.0
defaults:
  Critical: fail
  Major: fail
  Minor: warn
  Info: pass
rules:
  - pattern: LINK-*
    severity: Minor
    gate: warn
```

同一规则匹配多个配置项时，后出现的匹配项优先。规则版本会进入输出和缓存指纹，修改规则后相关缓存自动失效。

### 10.2 临时豁免

豁免必须限定到FuncID和规则模式，并包含原因、Owner和到期日期：

```yaml
version: 0.1.0
exemptions:
  - func_id: 05-03-10
    rule_id: LINK-DEAD-*
    reason: 历史链接迁移中，计划在指定版本完成修复
    owner: arkui-spec-owner
    expires: 2026-08-31
```

豁免行为：

- 仅在 `expires >= 当前日期` 时有效。
- 只影响匹配FuncID的Function门禁聚合。
- Finding仍保留在JSON和Markdown报告中。
- 严重度统计仍包含被豁免Finding。
- `exempted_count` 记录有效豁免命中数。
- 到期后豁免自动失效，原规则重新参与门禁。

豁免不能用于掩盖伪造证据、错误SDK契约或结论与源码相反等Critical问题。语义问题也不应通过静态规则豁免绕过评价Skill。

## 11. 如何阅读规则结果

单Function结果主要查看：

```text
<output>/<git-revision>/<FuncID>/static-result.json
<output>/<git-revision>/<FuncID>/report.md
```

建议处理顺序：

1. 先处理Critical和Major/fail问题。
2. 先修Registry、缺文件和结构错误，保证评价输入完整。
3. 再修追溯断链、源码引用和SDK定位问题。
4. 最后处理Minor/warn的可移植性、链接和图表问题。
5. 修复后使用 `--no-cache` 重跑，确认Finding实际消失。

示例：

```bash
python3 specs/tools/spec_eval/cli.py \
  --output /tmp/spec-evaluation \
  --no-cache --json check --func-id 05-03-10
```

退出码 `1` 表示质量门禁失败但报告已成功生成；退出码 `2/3` 才表示工具或评价完整性问题。

## 12. 新增或修改规则

新增规则必须完成以下闭环：

1. 确认问题是结果唯一、可重复执行的确定性问题；语义判断应留给评价Skill。
2. 在对应 `checks/*_checks.py` 中产生结构化Finding。
3. 使用稳定规则ID，格式建议为 `<类别>-<问题>-NNN`。
4. 给出精确文件、行号、FuncID，适用时给出FeatID。
5. 检查器只提供建议严重度，不直接退出或决定Function门禁。
6. 如需覆盖默认策略，在 `gate_rules.yaml` 增加规则模式。
7. 为规则补充最小正例和反例测试。
8. 高风险解析规则补充Mutation测试。
9. 会影响真实Function预期时更新Golden清单。
10. 运行全量单测和代表性Function回归。

规则ID一旦进入报告或历史基线，应保持稳定。语义变化较大时新增规则ID，不要复用旧ID表达不同问题。

推荐测试命令：

```bash
PYTHONPATH=specs/tools python3 -m unittest discover \
  -s specs/tools/spec_eval/tests -v

python3 specs/tools/spec_eval/cli.py \
  --output /tmp/spec-evaluation \
  --no-cache check --func-id 05-03-10
```

## 13. 当前实现边界

- 规则不会根据文档长度、表格数量、图数量或引用数量直接评分。
- 结构存在不代表内容正确或完整。
- 引用存在不代表引用能够支持结论。
- SDK声明存在不代表参数、返回值和版本语义完全一致。
- 追溯边存在不代表AC、Rule或VM本身具有充分质量。
- 当前静态阶段不输出完整语义质量总分。
- Script Finding不能被后续评价Skill改写为通过；Skill只能增加语义判断和证据。

完整工具使用方式参见 [`spec_eval/README.md`](../README.md)。
