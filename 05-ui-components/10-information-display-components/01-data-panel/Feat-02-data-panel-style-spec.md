# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DataPanel 样式属性 |
| 特性编号 | Func-05-10-01-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+（borderRadius 需 API 12+） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | DataPanel 样式属性规格补录 | 已有能力补录，无新增功能 |

## 输入文档

- 设计文档: `05-ui-components/10-information-display-components/01-data-panel/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/data_panel/`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。

## 用户故事

### US-1: 开发者自定义 DataPanel 视觉样式

**As a** 应用开发者  
**I want to** 通过样式属性控制 DataPanel 的颜色、宽度和效果  
**So that** 能够适配应用的视觉风格

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 closeEffect(false) THEN 启用动画和阴影效果 | 正常 |
| AC-1.2 | WHEN 设置 closeEffect(true) THEN 关闭动画和阴影效果 | 正常 |
| AC-1.3 | WHEN valueColors 数组长度 ≤ 9 THEN 每段使用对应颜色 | 正常 |
| AC-1.4 | WHEN valueColors 数组长度 > 9 THEN 仅应用前 9 个颜色 | 边界 |
| AC-1.5 | WHEN valueColors 包含 LinearGradient THEN 渐变偏移量钳制在 [0.0, 1.0] | 边界 |
| AC-1.6 | WHEN valueColors 未指定 THEN 使用主题默认颜色 | 正常 |
| AC-1.7 | WHEN 设置 trackBackgroundColor THEN 轨道背景使用指定颜色 | 正常 |
| AC-1.8 | WHEN strokeWidth 为正数 THEN 环形宽度使用指定值 | 正常 |
| AC-1.9 | WHEN strokeWidth 为负数或百分比 THEN 回退为主题默认厚度 | 边界 |
| AC-1.10 | WHEN borderRadius 设置于 LINE 类型 THEN 线性进度条使用圆角 | 正常 |
| AC-1.11 | WHEN borderRadius 设置于 CIRCLE 类型 THEN 圆角被忽略 | 边界 |
| AC-1.12 | WHEN borderRadius 在 API < 12 THEN 不生效 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-2 | 单元测试 | test_closeEffect_false |
| AC-1.2 | R-2 | TASK-2 | 单元测试 | test_closeEffect_true |
| AC-1.3 | R-3 | TASK-2 | 单元测试 | test_valueColors_normal |
| AC-1.4 | R-4 | TASK-2 | 单元测试 | test_valueColors_truncate |
| AC-1.5 | R-5 | TASK-2 | 单元测试 | test_gradient_offset |
| AC-1.6 | R-6 | TASK-2 | 单元测试 | test_valueColors_default |
| AC-1.7 | R-7 | TASK-2 | 单元测试 | test_trackBackgroundColor |
| AC-1.8 | R-8 | TASK-2 | 单元测试 | test_strokeWidth_positive |
| AC-1.9 | R-9 | TASK-2 | 单元测试 | test_strokeWidth_invalid |
| AC-1.10 | R-10 | TASK-2 | 单元测试 | test_borderRadius_line |
| AC-1.11 | R-11 | TASK-2 | 单元测试 | test_borderRadius_circle |
| AC-1.12 | R-12 | TASK-2 | 单元测试 | test_borderRadius_api_version |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | closeEffect = false | 启用动画和阴影（Effect = true） | 存储反转 | AC-1.1 |
| R-2 | 行为 | closeEffect = true | 关闭动画和阴影（Effect = false） | 存储反转 | AC-1.2 |
| R-3 | 行为 | valueColors 长度 1-9 | 每段使用对应颜色 | 无 | AC-1.3 |
| R-4 | 边界 | valueColors 长度 > 9 | 仅应用前 9 个颜色 | `MAX_COUNT = 9` | AC-1.4 |
| R-5 | 边界 | LinearGradient offset < 0 或 > 1 | 钳制到 [0.0, 1.0] | 无 | AC-1.5 |
| R-6 | 行为 | valueColors 未指定 | 使用主题 9 色对 | 无 | AC-1.6 |
| R-7 | 行为 | trackBackgroundColor 指定 | 轨道背景使用指定颜色 | 无 | AC-1.7 |
| R-8 | 行为 | strokeWidth > 0 且非百分比 | 使用指定厚度 | 无 | AC-1.8 |
| R-9 | 边界 | strokeWidth <= 0 或百分比 | 回退主题默认厚度 | 无 | AC-1.9 |
| R-10 | 行为 | borderRadius + LINE 类型 | 应用圆角到线性进度条 | 需 API 12+ | AC-1.10 |
| R-11 | 边界 | borderRadius + CIRCLE 类型 | 忽略圆角设置 | 无 | AC-1.11 |
| R-12 | 边界 | borderRadius + API < 12 | 不生效 | 无 | AC-1.12 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | closeEffect 反转存储 | 单元测试 | 验证 Effect = !closeEffect |
| VM-2 | valueColors 长度限制 | 单元测试 | 验证截断逻辑 |
| VM-3 | gradient offset 钳制 | 单元测试 | 验证边界值 |
| VM-4 | strokeWidth 约束 | 单元测试 | 验证负数/百分比回退 |
| VM-5 | borderRadius 类型限制 | 单元测试 | 验证 LINE/CIRCLE 差异 |
| VM-6 | borderRadius API 版本 | 单元测试 | 验证 API 12+ 约束 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| closeEffect(value: boolean) | Public | value: 是否关闭效果 | void | 无 | 控制动画和阴影 | AC-1.1, AC-1.2 |
| valueColors(value: Array\<ResourceColor \| LinearGradient\>) | Public | value: 颜色数组 | void | 无 | 设置每段颜色 | AC-1.3 ~ AC-1.6 |
| trackBackgroundColor(value: ResourceColor) | Public | value: 背景色 | void | 无 | 设置轨道背景 | AC-1.7 |
| strokeWidth(value: Length) | Public | value: 环形宽度 | void | 无 | 设置环形宽度 | AC-1.8, AC-1.9 |
| borderRadius(value: Length \| BorderRadiuses) | Public | value: 圆角 | void | 无 | 设置线性进度条圆角 | AC-1.10 ~ AC-1.12 |

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

**closeEffect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `closeEffect(value: boolean): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `boolean` | 是 | - | 无 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | closeEffect(false) | 启用动画和阴影 | AC-1.1 |
| 2 | closeEffect(true) | 关闭动画和阴影 | AC-1.2 |

---

**valueColors**

| 属性 | 值 |
|------|-----|
| 函数签名 | `valueColors(value: Array<ResourceColor \| LinearGradient>): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.3 ~ AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `Array<ResourceColor \| LinearGradient>` | 是 | 主题 9 色对 | 最大 9 元素；渐变 offset ∈ [0, 1] |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | valueColors([Color.Red, Color.Blue]) | 前两段使用红蓝 | AC-1.3 |
| 2 | valueColors([...] 长度 10) | 仅应用前 9 色 | AC-1.4 |
| 3 | LinearGradient offset < 0 | 钳制为 0.0 | AC-1.5 |
| 4 | LinearGradient offset > 1 | 钳制为 1.0 | AC-1.5 |
| 5 | valueColors 未调用 | 使用主题默认色 | AC-1.6 |

---

**strokeWidth**

| 属性 | 值 |
|------|-----|
| 函数签名 | `strokeWidth(value: Length): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.8, AC-1.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `Length` | 是 | 主题厚度 | 不能为负数或百分比 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | strokeWidth(24) | 环形宽度 24vp | AC-1.8 |
| 2 | strokeWidth(-10) | 回退主题厚度 | AC-1.9 |
| 3 | strokeWidth('50%') | 回退主题厚度 | AC-1.9 |

---

**borderRadius**

| 属性 | 值 |
|------|-----|
| 函数签名 | `borderRadius(value: Length \| BorderRadiuses): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.10 ~ AC-1.12 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `Length \| BorderRadiuses` | 是 | 8.0vp | 仅 LINE 类型生效；需 API 12+ |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | borderRadius(16) + LINE type | 线性进度条圆角 16vp | AC-1.10 |
| 2 | borderRadius(16) + CIRCLE type | 忽略圆角 | AC-1.11 |
| 3 | borderRadius(16) + API 11 | 不生效 | AC-1.12 |

## 兼容性声明

- **已有 API 行为变更:** 否，纯补录规格
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8+（borderRadius 需 API 12+）
- **API 版本号策略:** borderRadius 有 API 12 版本约束

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| closeEffect 存储反转 | PaintProperty 存储为 Effect = !closeEffect | AC-1.1, AC-1.2 |
| borderRadius 不在 PaintProperty | 直接调用 ViewAbstract::SetBorderRadius | AC-1.10 ~ AC-1.12 |
| 用户设置标志 | 阻止主题更新覆盖用户值 | 所有样式 AC |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 无特殊要求 | N/A | N/A |
| 功耗 | 无特殊要求 | N/A | N/A |
| 内存 | 无特殊要求 | N/A | N/A |
| 安全 | 无权限校验 | 代码评审 | 无敏感数据 |
| 可靠性 | 负值/百分比静默回退 | 单元测试 | test_strokeWidth_invalid |
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
| 深色模式 | 是 | valueColors/trackBackgroundColor 支持主题色 | 深色模式适配 |
| 多窗口/分屏 | 否 | 不涉及 | N/A |
| 多用户 | 否 | 不涉及 | N/A |
| 版本升级 | 是 | borderRadius 需 API 12+ | 版本兼容 |
| 生态兼容 | 否 | 不涉及 | N/A |

## 行为场景（可选，Gherkin）

```gherkin
Feature: DataPanel 样式属性
  作为 应用开发者
  我想要 通过样式属性控制 DataPanel 视觉效果
  以便 能够适配应用的视觉风格

  Scenario: 关闭动画效果
    Given 创建 DataPanel 组件
    When 调用 closeEffect(true)
    Then 组件不显示动画和阴影效果

  Scenario: 自定义颜色
    Given values = [10, 20, 30]
    When valueColors = [Color.Red, Color.Green, Color.Blue]
    Then 三段分别显示红、绿、蓝色

  Scenario: 渐变颜色
    Given values = [50]
    When valueColors = [LinearGradient({ colors: [[Color.Red, 0], [Color.Blue, 1]] })]
    Then 该段从红渐变到蓝

  Scenario: strokeWidth 无效值回退
    Given 创建 DataPanel 组件
    When strokeWidth = -10
    Then 使用主题默认厚度

  Scenario: borderRadius 类型限制
    Given type = CIRCLE
    When borderRadius = 16
    Then 圆角被忽略

  Scenario: borderRadius API 版本限制
    Given API 版本 < 12
    When borderRadius = 16
    Then 圆角不生效
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
    query: "DataPanel closeEffect 反转存储机制"
  - repo: "openharmony/arkui_ace_engine"
    query: "DataPanel valueColors 渐变处理和边界逻辑"
  - repo: "openharmony/arkui_ace_engine"
    query: "DataPanel strokeWidth 负数和百分比约束"
  - repo: "openharmony/arkui_ace_engine"
    query: "DataPanel borderRadius LINE 类型限制和 API 版本约束"
```

**关键文档：** design.md, DataPanelPaintProperty 源码