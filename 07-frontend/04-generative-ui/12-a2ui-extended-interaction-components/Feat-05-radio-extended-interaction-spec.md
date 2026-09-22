# 特性规格

> Func-07-04-12-Feat-05 Radio 扩展交互组件：固化 A2UI 扩展协议交互组件 Radio 的属性契约（`value` 必填/`checked`/`group`）、同组互斥语义、样式契约（选中背景色/未选中边框色/指示器色）、变化事件（`onChange {isChecked}`）与绑定回写。Radio 存在双实现（C++ 原生 `ExtendedRadioComponent` + ArkTS 自定义 `ExtendedRadio`，注册时 ArkTS 覆盖原生），契约以 schema + ArkTS 覆盖路径为准。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Radio 扩展交互组件 |
| 特性编号 | Func-07-04-12-Feat-05 |
| 优先级 | P1 |
| 目标版本 | A2UI 扩展协议 1.0.0 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 存量特性（lineage: new-on-legacy） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/12-a2ui-extended-interaction-components/design.md` | Baselined |
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（`components.Radio`） | — |
| 原生组件（C++） | `genui/src/main/cpp/components/extended/ExtendedRadioComponent.h/.cpp` | — |
| 自定义组件（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedRadio.ets` | — |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 文档参考 | `reference/extended-components/radio.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 值/组/选中属性契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `value`/`group`/`checked` 配置单选按钮，
**以便** 呈现互斥单选并区分选项值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `value` 字符串 THEN `SetValue` 写入 `value_` 并 `SetNodeRadioValue`（`ExtendedRadioComponent.cpp:384-392`） | 正常 |
| AC-1.2 | WHEN `value` 缺失 THEN 回落 `""` 并 `ResetNodeRadioValue`（`ExtendedRadioComponent.cpp:163-166,387-389`） | 边界 |
| AC-1.3 | WHEN `group` 字符串 THEN `SetGroup` 写入 `group_`（`ExtendedRadioComponent.cpp:394-402`），空串 `ResetNodeRadioGroup` | 正常 |
| AC-1.4 | WHEN `checked=true` THEN `SetChecked(true)` 置选中并同步同组（`ExtendedRadioComponent.cpp:111-120,378-382`） | 正常 |
| AC-1.5 | WHEN `checked` 缺失 THEN 回落 `false`（`fallbackBool=false`，`ExtendedRadioComponent.cpp:169-176`） | 边界 |

### US-2: 同组互斥语义

**作为** 生成式 UI 宿主开发者，
**我想要** 同 `group` 单选按钮互斥，
**以便** 仅一个 Radio 保持选中。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 某 Radio `checked=true` 且同 Surface 存在同 `group` 选中 peer THEN `SyncSiblingCheckedState` 将 peer 置 false（`ExtendedRadioComponent.cpp:410-428`） | 正常 |
| AC-2.2 | WHEN 用户选中某 Radio THEN `HandleRadioChange` 选中后同步 sibling 并回写绑定、派发事件（`ExtendedRadioComponent.cpp:349-361`） | 正常 |
| AC-2.3 | WHEN 不同 `group` 的 Radio THEN 互不影响（`SyncSiblingCheckedState` 仅匹配 `peer->group_==group_`，`ExtendedRadioComponent.cpp:422`） | 边界 |

### US-3: 变化事件与绑定回写

**作为** 生成式 UI 宿主开发者，
**我想要** 监听选中变化，
**以便** 处理单选结果并回写绑定。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 用户选中变化 THEN 派发 `onChange`，负载 `{isChecked:boolean}`（`ExtendedRadioComponent.cpp:360,45-55`） | 正常 |
| AC-3.2 | WHEN `checked` 有 path 绑定 THEN `SyncCheckedToBoundDataModel` 回写（`ExtendedRadioComponent.cpp:441-469`） | 正常 |
| AC-3.3 | THEN 监听始终注册（`UpdateChangeEventRegistration` 无条件注册，备 getRadioValue 读取）（`ExtendedRadioComponent.cpp:363-376`） | 正常 |

### US-4: 样式契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `styles` 控制单选样式，
**以便** 定制选中/未选中/指示器颜色。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `styles.checkedBackgroundColor`/`unCheckedBorderColor`/`indicatorColor` 合法 THEN 经 `ApplyRadioStyle` 应用（`ExtendedRadioComponent.cpp:237-249,404-408`） | 正常 |
| AC-4.2 | WHEN 颜色非法 THEN 告警回落默认（light `0xFF0A59F7`/`0x33FFFFFF`/`0xFFFFFFFF`）（`ExtendedRadioComponent.cpp:198-230,40-44`） | 异常 |
| AC-4.3 | WHEN 传入 `styles.uncheckedBorderColor`（小写 checked）THEN 告警「undefined for Radio」并忽略（`ExtendedRadioComponent.cpp:203-207`） | 异常 |

### US-5: ArkTS 覆盖路径与 indicatorType

**作为** 生成式 UI 宿主开发者，
**我想要** 了解 Radio 的 ArkTS 自定义实现，
**以便** 明确 `indicatorType` 等 ArkTS 独有能力。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 目录注册 THEN `createRadioDefinition` 生成的 custom item 覆盖原生 Radio（`A2UIExtendedComponents.ets:168-183,185-192`） | 正常 |
| AC-5.2 | WHEN `indicatorType="dot"` THEN 映射 `RadioIndicatorType.DOT`，否则 `TICK`（`ExtendedRadio.ets:111-123`） | 正常 |
| AC-5.3 | WHEN 用户点击 Radio THEN `dispatchClick` 派发 `onClick{offsetX,offsetY}` 且 `onChange` 派发 `{checked}`（`ExtendedRadio.ets:186-192`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-5 | C++ UT（`GetValueForTest`/`GetCheckedForTest`） | `ExtendedRadioComponent.cpp:378-402` |
| AC-2.1,AC-2.2,AC-2.3 | R-2 | T-5 | C++ UT | `ExtendedRadioComponent.cpp:410-428` |
| AC-3.1,AC-3.2,AC-3.3 | R-3 | T-5 | C++ UT + ohosTest | `ExtendedRadioComponent.cpp:349-376` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-5 | C++ UT + 告警 | `ExtendedRadioComponent.cpp:198-249` |
| AC-5.1,AC-5.2,AC-5.3 | R-5 | T-5 | ArkTS 单测 | `ExtendedRadio.ets:111-123,186-192` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `value`/`group`/`checked` 设置 | 写入内部态并同步 ArkUI 节点 | value/group 缺失回落 "" | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | 同组多选 | 仅一个保持 checked，peer 置 false | 匹配 `group_` | AC-2.1,AC-2.2,AC-2.3 |
| R-3 | 行为 | 选中变化 | 派发 onChange `{isChecked}` + 回写绑定 | 监听始终注册 | AC-3.1,AC-3.2,AC-3.3 |
| R-4 | 异常 | 颜色非法/`uncheckedBorderColor` | 告警回落默认/忽略 | schema 键为 `unCheckedBorderColor` | AC-4.1,AC-4.2,AC-4.3 |
| R-5 | 行为 | 目录注册/ArkTS | ArkTS 覆盖原生；indicatorType dot/tick | ArkTS 独有能力 | AC-5.1,AC-5.2,AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 属性 | C++ UT | value/group/checked 回落 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 互斥 | C++ UT | 同组互斥、跨组独立 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 事件 | C++ UT + ohosTest | onChange 负载 + 绑定回写 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 样式 | C++ UT + 告警 | 三色默认 + case 分歧 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 ArkTS | ArkTS 单测 | indicatorType/覆盖路径 |

## API 变更分析

> 存量补录，无新增/变更 API。Radio 双实现，注册时 ArkTS 覆盖原生。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 扩展协议组件 `Radio`（`extended_catalog.json`） | 既有 | 单选渲染 | 描述符契约，无迁移 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-4.1,AC-4.2,AC-4.3,AC-5.1,AC-5.2,AC-5.3 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`Radio` 组件描述符（`components.Radio`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | 组件描述符（JSON object），`GetType()=="Radio"`（`ExtendedRadioComponent.cpp:106-109`） |
| 返回值 | 原生 `RADIO` 节点（C++）/ ArkUI `Radio` 组件（ArkTS 覆盖路径） |
| 开放范围 | 扩展协议组件契约（非 ArkTS/C-API） |
| 错误码 | N/A（非法样式经 `ReportExtendedSchemaWarning` 上报告警） |
| 关联 AC | AC-1.1,AC-5.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 是 | `""` | 任一字符串 |
| checked | boolean | 否 | `false` | 缺失回落 false |
| group | string | 否 | `""` | 空串不入组 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 选中某 Radio | 同组 peer 置 false，派发 onChange + 回写 | AC-2.2,AC-3.1 |
| 2 | indicatorType=dot | ArkTS 呈现点型指示器 | AC-5.2 |
| 3 | 传入 uncheckedBorderColor | 告警忽略 | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 1.0.0。
- **API 版本号策略:** 双实现（ArkTS 覆盖原生）见风险表 RISK-1；`indicatorType` 为 ArkTS 实现独有，schema/C++ 未声明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 同组互斥 | 同 `group` 仅一个 checked | AC-2.1,AC-2.2,AC-2.3 |
| 双实现覆盖 | ArkTS 注册时覆盖原生 Radio | AC-5.1 |
| 绑定回写 | checked 绑定变化回写 | AC-3.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法输入不抛异常，告警回落 | C++ UT | `ExtendedRadioComponent.cpp:198-230` |
| 性能 | 同组扫描 O(n) 且仅切换选中 peer | C++ UT | `ExtendedRadioComponent.cpp:410-428` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 组件契约设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 通用 `accessibility.label/description` | 概述「组件公共结构」 |
| 大字体 | 否 | 无文字字号配置 | — |
| 深色模式 | 是 | 选中/未选中色按主题 | AC-4.1,AC-4.2,AC-4.3 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 1.0.0 | 概述「目标版本」 |
| 生态兼容 | 是 | 同组互斥基于 ArkUI Radio group | AC-2.1,AC-2.2,AC-2.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Radio 扩展交互组件
  作为 生成式 UI 宿主开发者
  我想要 单选按钮支持同组互斥与选中监听
  以便 提供互斥单选交互

  Scenario: 同组互斥
    Given Radio A(group="g", checked=true) 与 Radio B(group="g", checked=false)
    When 用户选中 B
    Then A 置 false，B 置 true，派发 onChange{isChecked:true}

  Scenario: 跨组独立
    Given Radio A(group="g1") 与 Radio B(group="g2")
    When 选中 A 再选中 B
    Then 两者均保持 checked=true

  Scenario: ArkTS indicatorType
    Given Radio 描述符 indicatorType="dot"
    When ArkTS 渲染
    Then 呈现点型指示器 DOT
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-05 做 Radio 组件契约；`getRadioValue` 归 07-04-16）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedRadioComponent value group checked 同组互斥 SyncSiblingCheckedState onChange 绑定回写"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedRadio.ets indicatorType RadioIndicatorType 目录注册覆盖 A2UIExtendedComponents createRadioDefinition"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/cpp/components/extended/ExtendedRadioComponent.cpp`、`genui/src/main/ets/core/components/extended/ExtendedRadio.ets`、`reference/extended-components/radio.md`