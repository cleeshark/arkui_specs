# 特性规格

> Func-07-04-04-Feat-04 Slider 交互组件：固化 A2UI v0.9 标准 `Slider` 组件的标签（`label`）、当前值（`value`）、最小值（`min`，默认 0）、最大值（`max`，默认 100）、边界约束（`min>=max` 回退默认 0/100；`value` 夹取到 `[min,max]`）与客户端校验（`checks` 失败即禁用）。基准实现：`@arkui-genius/genui`（A2UIRender），原生组件 `SliderComponent`（`markInnerNative(true)`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Slider 交互组件 |
| 特性编号 | Func-07-04-04-Feat-04 |
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
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UISlider.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/components/A2UI/slider/SliderComponent.cpp`、`SliderComponent.h` | — |
| 主题（C++） | `genui/src/main/cpp/components/A2UI/slider/SliderTheme.cpp/h` | — |
| 组件参考（Docs） | `reference/standard-components/slider.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** Slider 组件以 `component="Slider"` 注册为标准原生组件,
**以便** DSL 声明被引擎正确实例化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN DSL 声明 `"component":"Slider"` THEN `A2UISlider.asCatalogItem()` 注册，`type='Slider'`（`A2UISlider.ets:24,30-35`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `markCategory(A2UI_STANDARD)` 且 `markInnerNative(true)`（`A2UISlider.ets:33`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadA2UISchema(version,'components/Slider.json')` 命中 v0.9 schema（`A2UISlider.ets:26-28`） | 正常 |

### US-2: 标签与数值

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `label`/`value`/`min`/`max` 设置滑块标签与范围,
**以便** 表达可调节的进度值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 描述符含 `label` THEN `SetLabel` 写 `label_` 并 `SetNodeTextContent(textNode_)`（`SliderComponent.cpp:182-186`） | 正常 |
| AC-2.2 | WHEN 描述符含 `value` THEN `SetValue` 写 `value_` 并 `SetNodeSliderValue`（`SliderComponent.cpp:200-204`） | 正常 |
| AC-2.3 | WHEN 描述符含 `min` THEN `SetMinValue` 写 `minValue_` 并 `SetNodeSliderMinValue`（`SliderComponent.cpp:188-192`） | 正常 |
| AC-2.4 | WHEN min/max 缺省 THEN 默认 `min=0.0`、`max=100.0`（`DEFAULT_MIN/DEFAULT_MAX`，`SliderComponent.cpp:25-26`） | 边界 |
| AC-2.5 | WHEN `max`/`value` 缺失 THEN 触发必填告警（`GetComponentDirectRequiredPropertyKeys` 返回 `{"max","value"}`，`SliderComponent.cpp:121-124`） | 异常 |

### US-3: 边界约束

**作为** 生成式 UI 宿主开发者,
**我想要** 滑块对非法范围做回退与夹取,
**以便** 始终得到合法的可调范围。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `min >= max` THEN 回退 `min=0`、`max=100` 并打 warn 日志（`SliderComponent.cpp:236-240`） | 异常 |
| AC-3.2 | WHEN `value < min` THEN `ClampValue` 返回 `min`（`SliderComponent.cpp:30-32`） | 边界 |
| AC-3.3 | WHEN `value > max` THEN `ClampValue` 返回 `max`（`SliderComponent.cpp:33-35`） | 边界 |
| AC-3.4 | WHEN `value` 在 `[min,max]` 内 THEN 原样返回（`SliderComponent.cpp:36`） | 正常 |
| AC-3.5 | WHEN 属性应用后 THEN `value` 经 `SetValue(ClampValue(value_, minValue_, maxValue_))` 夹取（`SliderComponent.cpp:242-243`） | 正常 |
| AC-3.6 | WHEN min/max/value 动态更新 THEN `OnDataUpdate` 重新校验 `>=` 并重新夹取（`SliderComponent.cpp:256-276`） | 正常 |

### US-4: 视觉与步进

**作为** 生成式 UI 宿主开发者,
**我想要** Slider 采用固定步进与样式,
**以便** 呈现统一视觉。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 属性应用 THEN `SetStep(1.0f)`（`SliderComponent.cpp:245`） | 正常 |
| AC-4.2 | WHEN 属性应用 THEN `SetStyle(OUT_SET)`（`SliderComponent.cpp:246`） | 正常 |
| AC-4.3 | WHEN 主题存在 THEN 选中色取 `GetSelectedColor()`（`SliderComponent.cpp:247-251`） | 正常 |
| AC-4.4 | WHEN 主题配置变化 THEN `OnConfigChange` 重设选中色（`SliderComponent.cpp:353-362`） | 正常 |

### US-5: 客户端校验（checks）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `checks` 约束可滑动状态,
**以便** 校验不通过时禁用滑块。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 描述符含 `checks` THEN `ParseChecks` 解析规则并注册绑定路径（`SliderComponent.cpp:288-297`） | 正常 |
| AC-5.2 | WHEN `ValidateChecks()` 返回 false THEN `SetEnabled(false)` 禁用 slider 节点（`SliderComponent.cpp:283-286,278-281`） | 正常 |
| AC-5.3 | WHEN 校验失败 THEN 打 `Slider check failed` warn 日志（`SliderComponent.cpp:322-325`） | 异常 |
| AC-5.4 | WHEN 绑定路径数据更新且属性名以 `__checks_dep_` 前缀 THEN `RefreshEnabledState` 重新校验（`SliderComponent.cpp:256-262`） | 正常 |
| AC-5.5 | WHEN `checks` 未设置 THEN `ValidateChecks` 恒 true（`SliderComponent.cpp:316-320`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-4 | ArkTS 单测：目录注册 | `A2UISlider.ets:24-35` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-4 | C++ UT：SetLabel/SetMin/SetMax/SetValue | `SliderComponent.cpp:182-204` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 | R-3,R-4 | T-4 | C++ UT：ClampValue + ApplyPrivateAttributes | `SliderComponent.cpp:28-37,236-276` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-5 | T-4 | C++ UT：SetStep/SetStyle/选中色 | `SliderComponent.cpp:245-251,353-362` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-6,R-7 | T-4 | C++ UT：ValidateChecks/RefreshEnabledState | `SliderComponent.cpp:278-328` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | DSL `component="Slider"` | 注册为标准原生组件 | type 固定 Slider | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | label/value/min/max 设置 | 写入标签/值与范围 | max、value 必填 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 异常 | min>=max | 回退 min=0/max=100 | 打 warn 日志 | AC-3.1 |
| R-4 | 边界 | value 越界 | 夹取到 [min,max] | 小于 min 取 min，大于 max 取 max | AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| R-5 | 行为 | 属性应用 | 固定 step=1.0、style=OUT_SET、选中色主题化 | — | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-6 | 异常 | checks 校验失败 | 禁用 slider 节点 | message 记录 warn 日志 | AC-5.2,AC-5.3 |
| R-7 | 边界 | checks 缺失 | 校验恒通过，可滑动 | checksEngine 为空返回 true | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测 | type、markInnerNative |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 标签数值 | C++ UT | label/value/min/max 写节点 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 边界 | C++ UT | min>=max 回退、value 夹取 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 视觉 | C++ UT | step/style/选中色 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 checks | C++ UT | 禁用刷新、缺省可滑动 |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `Slider`（DSL 组件） | 既有 | `component` 字段匹配 | 经 `CatalogItem.forComponent` 注册 | AC-1.1,AC-1.2,AC-1.3 |

> d.ts 位置：组件 schema `rawfile/schema/A2UI/v0.9/components/Slider.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`SliderComponent`（原生，`component="Slider"`）**

| 属性 | 值 |
|------|-----|
| 组件签名 | `SliderComponent : public A2UIComponent`，`GetType()="Slider"`（`SliderComponent.cpp:143-146`） |
| 必填属性 | `max`、`value`（`GetComponentDirectRequiredPropertyKeys` 返回 `{"max","value"}`，`SliderComponent.cpp:121-124`） |
| 开放范围 | DSL 标准组件（inner-native） |
| 错误码 | N/A（min>=max 回退默认，不打 schema 告警） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-2.5 |

**属性约束**

| 属性 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| label | DynamicString | 否 | "" | 任意字符串 |
| value | DynamicNumber | 是 | 0.0 | 夹取到 [min,max] |
| min | number | 否 | 0 | 任意数字 |
| max | number | 是 | 100 | min < max |
| checks | CheckRule[] | 否 | [] | required/regex/length/numeric/email |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 label/value/min/max | 展示标签与可调范围 | AC-2.1,AC-2.2,AC-2.3 |
| 2 | min>=max | 回退 min=0/max=100 | AC-3.1 |
| 3 | value<min 或 value>max | 夹取到边界 | AC-3.2,AC-3.3 |
| 4 | checks 失败 | 禁用滑块 | AC-5.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** schema 随版本加载。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 原生实现路径 | Slider 标记 `markInnerNative(true)` | AC-1.2 |
| min>=max 回退 | 非法范围回退默认 0/100 | AC-3.1 |
| value 夹取 | 越界值夹取到 [min,max] | AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法范围/越界值不崩溃，回退或夹取 | C++ UT | `SliderComponent.cpp:28-37,236-243` |
| 性能 | 值更新单节点设置（SetNodeSliderValue） | C++ UT | `SliderComponent.cpp:203` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 交互行为设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 依赖底层 Slider 无障碍语义 | AC-1.1,AC-1.2,AC-1.3 |
| 大字体 | 否 | 标签由内部 TEXT 节点承载 | — |
| 深色模式 | 是 | `OnConfigChange` 重设选中色（`SliderComponent.cpp:353-362`） | AC-4.4 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | A2UI v0.9 Slider 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Slider 交互组件
  作为 生成式 UI 宿主开发者
  我想要 Slider 支持范围/夹取/校验
  以便 表达可调节滑块

  Scenario: min>=max 回退默认
    Given Slider 声明 min=200 max=100
    When 应用私有属性
    Then min 回退 0、max 回退 100

  Scenario Outline: 越界值夹取
    Given Slider min=0 max=100
    When value=<value>
    Then 夹取后为 <clamped>
    Examples:
      | value | clamped |
      | -10   | 0       |
      | 150   | 100     |
      | 50    | 50      |

  Scenario: 校验失败禁用
    Given Slider 声明 checks 且条件不满足
    When 引擎校验 checks
    Then slider 节点 SetEnabled(false)
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Slider 组件行为；值绑定回写高层未实现，仅展示）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "SliderComponent min max value ClampValue checks RefreshEnabledState"
  - repo: "GenerativeUI/A2UIRender"
    query: "A2UISlider asCatalogItem markInnerNative schemaProvider"
  - repo: "GenerativeUI/Docs"
    query: "Slider 组件 label value min max checks"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/A2UISlider.ets`、`genui/src/main/cpp/components/A2UI/slider/SliderComponent.cpp`、`reference/standard-components/slider.md`