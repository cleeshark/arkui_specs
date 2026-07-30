# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DataPanel 基础构造参数 |
| 特性编号 | Func-05-10-01-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | DataPanel 构造参数规格补录 | 已有能力补录，无新增功能 |

## 输入文档

- 设计文档: `05-ui-components/10-information-display-components/01-data-panel/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/data_panel/`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 开发者使用 DataPanel 展示占比数据

**As a** 应用开发者  
**I want to** 通过 DataPanel 组件构造参数控制数据展示  
**So that** 能够以 Circle 或 Line 形式可视化数据占比

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 传入 values 数组且长度 ≤ 9 THEN 所有元素正常渲染 | 正常 |
| AC-1.2 | WHEN 传入 values 数组且长度 > 9 THEN 仅渲染前 9 个元素 | 边界 |
| AC-1.3 | WHEN values 数组包含负值 THEN 负值被钳制为 0.0 | 边界 |
| AC-1.4 | WHEN values 数组为空 THEN 默认渲染 [0.0] | 边界 |
| AC-1.5 | WHEN 未指定 max THEN 默认使用 100.0 作为最大值 | 正常 |
| AC-1.6 | WHEN 指定 max 且 max > 0 THEN 使用指定值作为最大值 | 正常 |
| AC-1.7 | WHEN 指定 max 且 max <= 0 THEN 使用所有 values 总和作为最大值 | 边界 |
| AC-1.8 | WHEN 未指定 type THEN 默认使用 Circle 类型 | 正常 |
| AC-1.9 | WHEN 指定 type 为 Line THEN 渲染为线性进度条 | 正常 |
| AC-1.10 | WHEN 创建后再次调用 SetDataPanelType THEN 类型不变 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-1 | 单元测试 | test_values_normal |
| AC-1.2 | R-2 | TASK-1 | 单元测试 | test_values_truncate |
| AC-1.3 | R-3 | TASK-1 | 单元测试 | test_values_negative |
| AC-1.4 | R-4 | TASK-1 | 单元测试 | test_values_empty |
| AC-1.5 | R-5 | TASK-1 | 单元测试 | test_max_default |
| AC-1.6 | R-6 | TASK-1 | 单元测试 | test_max_explicit |
| AC-1.7 | R-7 | TASK-1 | 单元测试 | test_max_fallback |
| AC-1.8 | R-8 | TASK-1 | 单元测试 | test_type_default |
| AC-1.9 | R-9 | TASK-1 | 单元测试 | test_type_line |
| AC-1.10 | R-10 | TASK-1 | 单元测试 | test_type_immutable |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | values 数组长度 1-9 | 按顺序渲染每个数据段 | 无 | AC-1.1 |
| R-2 | 边界 | values 数组长度 > 9 | 截断为前 9 个元素 | `MAX_COUNT = 9` | AC-1.2 |
| R-3 | 边界 | values[i] < 0 | 钳制为 0.0 | `DATA_PANEL_VALUE_MIN = 0.0` | AC-1.3 |
| R-4 | 边界 | values 数组为空或 undefined | 默认为 [0.0] | 无 | AC-1.4 |
| R-5 | 行为 | max 未指定或 undefined | 使用默认值 100.0 | `DEFAULT_MAX_VALUE = 100.0` | AC-1.5 |
| R-6 | 行为 | max > 0 | 使用指定值作为最大值 | 无 | AC-1.6 |
| R-7 | 边界 | max <= 0 | 使用 sum(values) 作为最大值 | 无 | AC-1.7 |
| R-8 | 行为 | type 未指定 | 默认使用 Circle (type=0) | 无 | AC-1.8 |
| R-9 | 行为 | type = Line (type=1) | 调用 PaintLinearProgress 渲染线性进度条 | 无 | AC-1.9 |
| R-10 | 边界 | 创建后再次调用 SetDataPanelType | 忽略后续调用，类型不变 | `isFirstCreate_` 标志 | AC-1.10 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | values 数组长度限制 | 单元测试 | 验证截断逻辑 |
| VM-2 | values 负值处理 | 单元测试 | 验证钳制逻辑 |
| VM-3 | max 默认值 | 单元测试 | 验证默认值 100.0 |
| VM-4 | max <= 0 回退 | 单元测试 | 验证总和计算 |
| VM-5 | type 默认值 | 单元测试 | 验证 Circle 默认 |
| VM-6 | type 不可变 | 单元测试 | 验证 isFirstCreate_ 标志 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| DataPanel(values: number[], max?: number, type?: DataPanelType) | Public | values: 数据数组；max: 最大值；type: 类型 | void | 无 | 构造 DataPanel 组件 | AC-1.1~1.10 |

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

**DataPanel 构造函数**

| 属性 | 值 |
|------|-----|
| 函数签名 | `DataPanel(options: DataPanelOptions)` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1 ~ AC-1.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| values | `number[]` | 是 | - | 最大 9 元素；负值钳制为 0；空数组默认 [0.0] |
| max | `number` | 否 | 100.0 | 若 <= 0 则使用 sum(values) |
| type | `DataPanelType` | 否 | Circle (0) | 创建后不可变 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | values = [10, 20, 30], max = 100, type = Circle | 渲染三个占比段，总和 60% | AC-1.1 |
| 2 | values = [1,2,3,4,5,6,7,8,9,10] | 仅渲染前 9 个值 | AC-1.2 |
| 3 | values = [-10, 20, 30] | 渲染为 [0.0, 20, 30] | AC-1.3 |
| 4 | values = [] | 渲染为 [0.0] | AC-1.4 |
| 5 | values = [50], max 未指定 | max = 100.0 | AC-1.5 |
| 6 | values = [50], max = 200 | max = 200 | AC-1.6 |
| 7 | values = [10, 20], max = -1 | max = 30（总和） | AC-1.7 |
| 8 | type 未指定 | 默认 Circle 类型 | AC-1.8 |
| 9 | type = Line | 渲染为线性进度条 | AC-1.9 |
| 10 | 创建后再次调用 SetDataPanelType | 类型不变 | AC-1.10 |

## 兼容性声明

- **已有 API 行为变更:** 否，纯补录规格
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8+
- **API 版本号策略:** 无 @since 标注，初始版本已包含

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| values/max/type 存储于 PaintProperty | 三者均影响绘制，不影响布局 | AC-1.1 ~ AC-1.10 |
| type 不可变 | `isFirstCreate_` 标志控制 | AC-1.10 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 无特殊要求 | N/A | N/A |
| 功耗 | 无特殊要求 | N/A | N/A |
| 内存 | 无特殊要求 | N/A | N/A |
| 安全 | 无权限校验 | 代码评审 | 无敏感数据 |
| 可靠性 | 负值/空数组静默处理 | 单元测试 | test_values_negative |
| 可测试性 | 支持单元测试覆盖边界场景 | 单元测试 | 100% AC 覆盖 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | N/A | N/A | N/A |
| 平板 | 无差异 | N/A | N/A | N/A |
| 折叠屏 | 无差异 | N/A | N/A | N/A |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 支持 focus 边框 | 无障碍聚焦 |
| 大字体 | 否 | 不涉及 | N/A |
| 深色模式 | 是 | valueColors 支持主题色 | 深色模式适配 |
| 多窗口/分屏 | 否 | 不涉及 | N/A |
| 多用户 | 否 | 不涉及 | N/A |
| 版本升级 | 否 | 不涉及 | N/A |
| 生态兼容 | 否 | 不涉及 | N/A |

## 行为场景（可选，Gherkin）

```gherkin
Feature: DataPanel 构造参数
  作为 应用开发者
  我想要 通过构造参数控制 DataPanel 数据展示
  以便 能够以 Circle 或 Line 形式可视化数据占比

  Scenario: 正常值数组渲染
    Given values 数组包含 [10, 20, 30]
    And max = 100
    And type = Circle
    When 渲染 DataPanel
    Then 显示三个数据段，占比分别为 10%、20%、30%

  Scenario: 超长数组截断
    Given values 数组包含 [1,2,3,4,5,6,7,8,9,10]
    When 渲染 DataPanel
    Then 仅显示前 9 个数据段

  Scenario: 负值钳制
    Given values 数组包含 [-10, 20, 30]
    When 渲染 DataPanel
    Then 负值被钳制为 0.0，渲染为 [0.0, 20, 30]

  Scenario: max 回退为总和
    Given values 数组包含 [10, 20]
    And max = -1
    When 渲染 DataPanel
    Then max 使用总和 30

  Scenario: 类型不可变
    Given 创建 DataPanel 时 type = Circle
    When 创建后调用 SetDataPanelType(Line)
    Then 类型仍为 Circle
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "DataPanel values 数组长度限制和负值处理逻辑"
  - repo: "openharmony/arkui_ace_engine"
    query: "DataPanel max <= 0 时的回退计算逻辑"
  - repo: "openharmony/arkui_ace_engine"
    query: "DataPanel type 不可变性的实现机制"
```

**关键文档：** design.md, DataPanelModifier 源码