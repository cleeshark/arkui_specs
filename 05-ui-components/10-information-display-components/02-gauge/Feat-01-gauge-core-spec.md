# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Gauge 核心属性 |
| 特性编号 | Func-05-10-02-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Gauge 核心属性规格补录 | 已有能力补录，无新增功能 |

## 输入文档

- 设计文档: `05-ui-components/10-information-display-components/02-gauge/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/gauge/`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。

## 用户故事

### US-1: 开发者使用 Gauge 展示数据进度

**As a** 应用开发者  
**I want to** 通过 Gauge 组件核心属性控制数据展示  
**So that** 能够可视化展示数据的当前进度和范围

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 value 在 [min, max] 范围内 THEN 正确显示对应进度 | 正常 |
| AC-1.2 | WHEN value < min THEN 显示为 min 位置 | 边界 |
| AC-1.3 | WHEN value > max THEN 显示为 max 位置 | 边界 |
| AC-1.4 | WHEN 未设置 min THEN 默认使用 0 | 正常 |
| AC-1.5 | WHEN 未设置 max THEN 默认使用 100 | 正常 |
| AC-1.6 | WHEN min >= max THEN 重置为默认值 0/100 | 边界 |
| AC-1.7 | WHEN 设置 startAngle/endAngle THEN 弧形从指定角度开始绘制 | 正常 |
| AC-1.8 | WHEN startAngle == endAngle THEN 绘制完整 360 度圆 | 边界 |
| AC-1.9 | WHEN colors 为单色 THEN 使用 GaugeType.MONOCHROME 渲染 | 正常 |
| AC-1.10 | WHEN colors 为 LinearGradient THEN 使用 GaugeType.SINGLE_SEGMENT 渲染 | 正常 |
| AC-1.11 | WHEN colors 为 [color, weight] 数组 THEN 使用 GaugeType.MULTI_SEGMENT 渲染 | 正常 |
| AC-1.12 | WHEN strokeWidth 为正值且非百分比 THEN 使用指定厚度 | 正常 |
| AC-1.13 | WHEN strokeWidth 为负数或百分比 THEN 忽略或使用默认值 | 边界 |
| AC-1.14 | WHEN strokeWidth 超过半径 THEN 钳制到半径值 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-1 | 单元测试 | test_value_normal |
| AC-1.2 | R-2 | TASK-1 | 单元测试 | test_value_below_min |
| AC-1.3 | R-3 | TASK-1 | 单元测试 | test_value_above_max |
| AC-1.4 | R-4 | TASK-1 | 单元测试 | test_min_default |
| AC-1.5 | R-5 | TASK-1 | 单元测试 | test_max_default |
| AC-1.6 | R-6 | TASK-1 | 单元测试 | test_min_max_invalid |
| AC-1.7 | R-7 | TASK-1 | 单元测试 | test_angle_custom |
| AC-1.8 | R-8 | TASK-1 | 单元测试 | test_angle_equal |
| AC-1.9 | R-9 | TASK-1 | 单元测试 | test_colors_monochrome |
| AC-1.10 | R-10 | TASK-1 | 单元测试 | test_colors_gradient |
| AC-1.11 | R-11 | TASK-1 | 单元测试 | test_colors_multi_segment |
| AC-1.12 | R-12 | TASK-1 | 单元测试 | test_strokeWidth_normal |
| AC-1.13 | R-13 | TASK-1 | 单元测试 | test_strokeWidth_invalid |
| AC-1.14 | R-14 | TASK-1 | 单元测试 | test_strokeWidth_exceed_radius |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | value ∈ [min, max] | 显示对应进度 | 无 | AC-1.1 |
| R-2 | 边界 | value < min | 显示在 min 位置 | 钳制处理 | AC-1.2 |
| R-3 | 边界 | value > max | 显示在 max 位置 | 钳制处理 | AC-1.3 |
| R-4 | 行为 | min 未指定 | 默认值 0 | `DEFAULT_MIN_VALUE = 0` | AC-1.4 |
| R-5 | 行为 | max 未指定 | 默认值 100 | `DEFAULT_MAX_VALUE = 100` | AC-1.5 |
| R-6 | 边界 | min >= max | 重置为 0/100 | 无 | AC-1.6 |
| R-7 | 行为 | startAngle/endAngle 指定 | 从指定角度绘制弧形 | 归一化到 [0, 360) | AC-1.7 |
| R-8 | 边界 | startAngle == endAngle | 绘制完整 360 度圆 | `sweepDegree = WHOLE_CIRCLE` | AC-1.8 |
| R-9 | 行为 | colors 为单色 | 使用 MONOCHROME 类型 | GaugeType = 2 | AC-1.9 |
| R-10 | 行为 | colors 为 LinearGradient | 使用 SINGLE_SEGMENT 类型 | GaugeType = 1 | AC-1.10 |
| R-11 | 行为 | colors 为 [color, weight] 数组 | 使用 MULTI_SEGMENT 类型 | GaugeType = 0，权重归一化 | AC-1.11 |
| R-12 | 行为 | strokeWidth 为正值且非百分比 | 使用指定厚度 | 无 | AC-1.12 |
| R-13 | 边界 | strokeWidth 为负数或百分比 | 忽略或使用默认值 | 不支持百分比 | AC-1.13 |
| R-14 | 边界 | strokeWidth > 半径 | 钳制到半径值 | `thickness <= radius` | AC-1.14 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | value 范围钳制 | 单元测试 | 验证 [min, max] 边界 |
| VM-2 | min/max 默认值和重置 | 单元测试 | 验证 min >= max 处理 |
| VM-3 | 角度归一化 | 单元测试 | 验证 startAngle == endAngle |
| VM-4 | GaugeType 分发 | 单元测试 | 验证颜色类型判断 |
| VM-5 | strokeWidth 约束 | 单元测试 | 验证百分比和超限处理 |
| VM-6 | 权重归一化 | 单元测试 | 验证总和为 0 处理 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `Gauge(options?: GaugeOptions)` | Public | value/min/max | void | 无 | 构造 Gauge 组件 | AC-1.1 ~ AC-1.6 |
| `value(value: number)` | Public | value: 当前值 | void | 无 | 设置当前数据值 | AC-1.1 ~ AC-1.3 |
| `min(min: number)` | Public | min: 最小值 | void | 无 | 设置最小值 | AC-1.4, AC-1.6 |
| `max(max: number)` | Public | max: 最大值 | void | 无 | 设置最大值 | AC-1.5, AC-1.6 |
| `startAngle(angle: number)` | Public | angle: 起始角度 | void | 无 | 设置弧形起始角度 | AC-1.7, AC-1.8 |
| `endAngle(angle: number)` | Public | angle: 结束角度 | void | 无 | 设置弧形结束角度 | AC-1.7, AC-1.8 |
| `colors(colors: ...)` | Public | colors: 颜色配置 | void | 无 | 设置环颜色 | AC-1.9 ~ AC-1.11 |
| `strokeWidth(length: Length)` | Public | length: 环厚度 | void | 无 | 设置环形宽度 | AC-1.12 ~ AC-1.14 |

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

**Gauge 构造函数**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Gauge(options?: GaugeOptions)` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1 ~ AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options.value | `number` | 否 | 0 | 钳制到 [min, max] |
| options.min | `number` | 否 | 0 | 必须 < max |
| options.max | `number` | 否 | 100 | 必须 > min |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Gauge({ value: 50 }) | value=50, min=0, max=100 | AC-1.1 |
| 2 | Gauge({ value: -10 }) | value=0 | AC-1.2 |
| 3 | Gauge({ value: 150 }) | value=100 | AC-1.3 |
| 4 | Gauge({ min: 10 }) | min=10 | AC-1.4 |
| 5 | Gauge({ max: 200 }) | max=200 | AC-1.5 |
| 6 | Gauge({ min: 100, max: 50 }) | 重置为 min=0, max=100 | AC-1.6 |

---

**startAngle / endAngle**

| 属性 | 值 |
|------|-----|
| 函数签名 | `startAngle(angle: number): void` / `endAngle(angle: number): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.7, AC-1.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| angle | `number` | 是 | 0 (start) / 360 (end) | 角度值（度） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | startAngle(0), endAngle(180) | 绘制半圆 | AC-1.7 |
| 2 | startAngle(90), endAngle(270) | 从 90° 到 270° | AC-1.7 |
| 3 | startAngle(180), endAngle(180) | 绘制完整 360° 圆 | AC-1.8 |

---

**colors**

| 属性 | 值 |
|------|-----|
| 函数签名 | `colors(colors: ResourceColor \| LinearGradient \| Array<[ResourceColor \| LinearGradient, number]>): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.9 ~ AC-1.11 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| colors | 见签名 | 是 | 绿黄红渐变 | 三种类型 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | colors(Color.Red) | 单色红色环 | AC-1.9 |
| 2 | colors(LinearGradient(...)) | 渐变环 | AC-1.10 |
| 3 | colors([[Color.Red, 0.3], [Color.Blue, 0.7]]) | 多段按权重绘制 | AC-1.11 |

---

**strokeWidth**

| 属性 | 值 |
|------|-----|
| 函数签名 | `strokeWidth(length: Length): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.12 ~ AC-1.14 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| length | `Length` | 是 | 4vp | 正值；不支持百分比；不超过半径 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | strokeWidth(24) | 环宽度 24vp | AC-1.12 |
| 2 | strokeWidth(-10) | 使用默认值 | AC-1.13 |
| 3 | strokeWidth('50%') | 使用默认值 | AC-1.13 |
| 4 | strokeWidth(1000) (超半径) | 钳制到半径 | AC-1.14 |

## 兼容性声明

- **已有 API 行为变更:** 否，纯补录规格
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8+
- **API 版本号策略:** 无 @since 标注，初始版本已包含

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| value 两级钳制 | JS Bridge 和 Modifier 双重验证 | AC-1.1 ~ AC-1.3 |
| GaugeType 三种类型 | 按 colors 参数类型自动分发 | AC-1.9 ~ AC-1.11 |
| strokeWidth 不支持百分比 | 解析时拒绝百分比单位 | AC-1.13 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 无特殊要求 | N/A | N/A |
| 功耗 | 无特殊要求 | N/A | N/A |
| 内存 | 无特殊要求 | N/A | N/A |
| 安全 | 无权限校验 | 代码评审 | 无敏感数据 |
| 可靠性 | 范围外值静默钳制 | 单元测试 | test_value_out_of_range |
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
| 无障碍 | 是 | 支持范围值访问 | 无障碍聚焦 |
| 大字体 | 否 | 不涉及 | N/A |
| 深色模式 | 是 | colors 支持主题色 | 深色模式适配 |
| 多窗口/分屏 | 否 | 不涉及 | N/A |
| 多用户 | 否 | 不涉及 | N/A |
| 版本升级 | 否 | 不涉及 | N/A |
| 生态兼容 | 否 | 不涉及 | N/A |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Gauge 核心属性
  作为 应用开发者
  我想要 通过核心属性控制 Gauge 数据展示
  以便 能够可视化展示数据的当前进度和范围

  Scenario: 正常值显示
    Given value = 50, min = 0, max = 100
    When 渲染 Gauge
    Then 显示在 50% 位置

  Scenario: 值超出范围钳制
    Given value = -10, min = 0, max = 100
    When 渲染 Gauge
    Then 显示在 0% 位置

  Scenario: min >= max 重置
    Given min = 100, max = 50
    When 渲染 Gauge
    Then 使用默认值 min=0, max=100

  Scenario: 角度相等绘制完整圆
    Given startAngle = 180, endAngle = 180
    When 渲染 Gauge
    Then 绘制完整 360 度圆

  Scenario: 多段颜色权重归一化
    Given colors = [[Red, 30], [Blue, 70]]
    When 渲染 Gauge
    Then 红色占 30%，蓝色占 70%

  Scenario: strokeWidth 超限钳制
    Given strokeWidth = 1000 (超过半径)
    When 渲染 Gauge
    Then 厚度钳制到半径值
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
    query: "Gauge value 范围钳制和 min/max 默认值处理"
  - repo: "openharmony/arkui_ace_engine"
    query: "Gauge GaugeType 三种颜色类型分发机制"
  - repo: "openharmony/arkui_ace_engine"
    query: "Gauge startAngle/endAngle 归一化和完整圆处理"
  - repo: "openharmony/arkui_ace_engine"
    query: "Gauge strokeWidth 百分比拒绝和半径钳制"
```

**关键文档：** design.md, GaugeModifier 源码