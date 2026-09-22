# 特性规格

> Func-07-04-04-Feat-03 CheckBox 交互组件：固化 A2UI v0.9 标准 `CheckBox` 组件的标签（`label`）、选中状态（`value`，DynamicBoolean，默认 false）、客户端校验（`checks` 失败即禁用）与圆形选中色。基准实现：`@arkui-genius/genui`（A2UIRender），原生组件 `CheckboxComponent`（`markInnerNative(true)`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | CheckBox 交互组件 |
| 特性编号 | Func-07-04-04-Feat-03 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9（API Version 20） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 存量特性补录 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/04-a2ui-standard-interaction-components/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UICheckbox.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/components/A2UI/checkbox/CheckboxComponent.cpp`、`CheckboxComponent.h` | — |
| 主题（C++） | `genui/src/main/cpp/components/A2UI/checkbox/CheckboxTheme.cpp/h`、`CheckboxGroupTheme.cpp/h` | — |
| 组件参考（Docs） | `reference/standard-components/checkbox.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** CheckBox 组件以 `component="CheckBox"` 注册为标准原生组件,
**以便** DSL 声明被引擎正确实例化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN DSL 声明 `"component":"CheckBox"` THEN `A2UICheckbox.asCatalogItem()` 注册，`type='CheckBox'`（`A2UICheckbox.ets:24,30-35`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `markCategory(A2UI_STANDARD)` 且 `markInnerNative(true)`（`A2UICheckbox.ets:33`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadA2UISchema(version,'components/CheckBox.json')` 命中 v0.9 schema（`A2UICheckbox.ets:26-28`） | 正常 |

### US-2: 标签与选中状态

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `label`/`value` 设置选择框名称与选中态,
**以便** 展示选项文案与勾选状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 描述符含 `label` THEN `SetLabel` 写 `label_` 并 `SetNodeTextContent(textNode_)`（`CheckboxComponent.cpp:153-157`） | 正常 |
| AC-2.2 | WHEN 描述符含 `value` THEN `SetSelect` 写 `value_` 并 `SetNodeCheckboxSelect`（`CheckboxComponent.cpp:159-163`） | 正常 |
| AC-2.3 | WHEN `value` 缺省 THEN 默认 `false`（`GetPrivatePropertyDeclaration` 中 `fallbackBool=false`，`CheckboxComponent.cpp:51-60`） | 边界 |
| AC-2.4 | WHEN `label`/`value` 为动态绑定 THEN 属性声明 `allowDynamic=true`（`CheckboxComponent.cpp:41-60`） | 正常 |
| AC-2.5 | WHEN `label`/`value` 缺失 THEN 触发必填告警（`GetComponentDirectRequiredPropertyKeys` 返回 `{"label","value"}`，`CheckboxComponent.cpp:85-88`） | 异常 |

### US-3: 视觉样式

**作为** 生成式 UI 宿主开发者,
**我想要** CheckBox 采用圆形勾选与主题选中色,
**以便** 呈现统一视觉。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 属性应用 THEN `SetCheckboxShape(CIRCLE)`（`CheckboxComponent.cpp:192`） | 正常 |
| AC-3.2 | WHEN 属性应用 THEN 选中色取主题 `GetSelectedColor()`，无主题回退 `0xFF007DFF`（`CheckboxComponent.cpp:189-191`） | 正常 |
| AC-3.3 | WHEN 主题配置变化 THEN `OnConfigChange` 重设 `SetSelectColor`（`CheckboxComponent.cpp:281-290`） | 正常 |
| AC-3.4 | WHEN 内部节点初始化 THEN 文本字号 14.0、checkbox 右侧 margin 12.0（`CheckboxComponent.cpp:123-125`） | 正常 |

### US-4: 客户端校验（checks）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `checks` 约束可勾选状态,
**以便** 校验不通过时禁用选择框。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 描述符含 `checks` THEN `ParseChecks` 解析规则并注册绑定路径（`CheckboxComponent.cpp:216-225`） | 正常 |
| AC-4.2 | WHEN `ValidateChecks()` 返回 false THEN `SetEnabled(false)` 禁用 checkbox 节点（`CheckboxComponent.cpp:211-214,206-209`） | 正常 |
| AC-4.3 | WHEN 校验失败 THEN 打 `Checkbox check failed` warn 日志（`CheckboxComponent.cpp:250-254`） | 异常 |
| AC-4.4 | WHEN 绑定路径数据更新且属性名以 `__checks_dep_` 前缀 THEN `RefreshEnabledState` 重新校验（`CheckboxComponent.cpp:197-204`） | 正常 |
| AC-4.5 | WHEN `checks` 未设置 THEN `ValidateChecks` 恒 true（`CheckboxComponent.cpp:244-248`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-3 | ArkTS 单测：目录注册 | `A2UICheckbox.ets:24-35` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-3 | C++ UT：SetLabel/SetSelect | `CheckboxComponent.cpp:153-163` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-3 | C++ UT：ApplyPrivateAttributes | `CheckboxComponent.cpp:175-195` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-4,R-5 | T-3 | C++ UT：ValidateChecks/RefreshEnabledState | `CheckboxComponent.cpp:206-256` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | DSL `component="CheckBox"` | 注册为标准原生组件 | type 固定 CheckBox | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | label/value 设置 | 写入文本/勾选态 | label、value 均必填 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 行为 | 属性应用 | 圆形勾选 + 主题选中色 | 默认色 0xFF007DFF | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 异常 | checks 校验失败 | 禁用 checkbox 节点 | message 记录 warn 日志 | AC-4.2,AC-4.3 |
| R-5 | 边界 | checks 缺失 | 校验恒通过，可勾选 | checksEngine 为空返回 true | AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测 | type、markInnerNative |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 标签选中 | C++ UT | label/value 写节点、必填 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 视觉 | C++ UT | CIRCLE、选中色 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 checks | C++ UT | 禁用刷新、缺省可勾选 |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `CheckBox`（DSL 组件） | 既有 | `component` 字段匹配 | 经 `CatalogItem.forComponent` 注册 | AC-1.1,AC-1.2,AC-1.3 |

> d.ts 位置：组件 schema `rawfile/schema/A2UI/v0.9/components/CheckBox.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`CheckboxComponent`（原生，`component="CheckBox"`）**

| 属性 | 值 |
|------|-----|
| 组件签名 | `CheckboxComponent : public A2UIComponent`，`GetType()="CheckBox"`（`CheckboxComponent.cpp:148-151`） |
| 必填属性 | `label`、`value`（`GetComponentDirectRequiredPropertyKeys` 返回 `{"label","value"}`，`CheckboxComponent.cpp:85-88`） |
| 开放范围 | DSL 标准组件（inner-native） |
| 错误码 | N/A（结构问题经 schema 告警 2001 上报） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-2.5 |

**属性约束**

| 属性 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| label | DynamicString | 是 | "" | 任意字符串 |
| value | DynamicBoolean | 是 | false | true/false |
| checks | CheckRule[] | 否 | [] | required/regex/length/numeric/email |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 label/value | 展示文案与勾选态 | AC-2.1,AC-2.2 |
| 2 | value 缺省 | 默认未选中 false | AC-2.3 |
| 3 | checks 失败 | 禁用 checkbox | AC-4.2 |
| 4 | 主题变化 | 重设选中色 | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** schema 随版本加载。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 原生实现路径 | CheckBox 标记 `markInnerNative(true)` | AC-1.2 |
| 圆形勾选 | shape 固定 CIRCLE | AC-3.1 |
| checks 失败即禁用 | 与 TextField/ChoicePicker 语义不同 | AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 value 回退 false，不崩溃 | C++ UT | `CheckboxComponent.cpp:57` |
| 性能 | 勾选状态单节点更新 | C++ UT | `CheckboxComponent.cpp:162` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 交互行为设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 依赖底层 Checkbox 无障碍语义 | AC-1.1,AC-1.2,AC-1.3 |
| 大字体 | 否 | 标签字号固定 14.0 | — |
| 深色模式 | 是 | `OnConfigChange` 重设选中色（`CheckboxComponent.cpp:281-290`） | AC-3.3 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | A2UI v0.9 CheckBox 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: CheckBox 交互组件
  作为 生成式 UI 宿主开发者
  我想要 CheckBox 支持选中/校验
  以便 表达二值选项

  Scenario: 校验失败禁用
    Given CheckBox 声明 checks 且条件不满足
    When 引擎校验 checks
    Then checkbox 节点 SetEnabled(false)

  Scenario: 主题变化重设选中色
    Given CheckBox 已应用默认选中色
    When 主题配置变化
    Then 重新应用主题 GetSelectedColor

  Scenario: value 缺省未选中
    Given CheckBox 未声明 value
    When 应用属性
    Then 选中态为 false
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（CheckBox 组件行为；CheckBoxGroup 归扩展域 07-04-12）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "CheckboxComponent label value checks RefreshEnabledState SetSelect"
  - repo: "GenerativeUI/A2UIRender"
    query: "A2UICheckbox asCatalogItem markInnerNative schemaProvider"
  - repo: "GenerativeUI/Docs"
    query: "CheckBox 组件 label value checks"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/A2UICheckbox.ets`、`genui/src/main/cpp/components/A2UI/checkbox/CheckboxComponent.cpp`、`reference/standard-components/checkbox.md`