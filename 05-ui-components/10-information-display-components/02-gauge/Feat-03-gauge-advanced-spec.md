# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Gauge 高级能力 |
| 特性编号 | Func-05-10-02-Feat-03 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Gauge 高级能力规格补录 | contentModifier/privacySensitive/C-API |

## 输入文档

- 设计文档: `05-ui-components/10-information-display-components/02-gauge/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/gauge/`, `frameworks/core/interfaces/native/node/`

## 用户故事

### US-1: 开发者使用 ContentModifier 自定义渲染

**As a** 应用开发者  
**I want to** 通过 ContentModifier 完全自定义 Gauge 渲染  
**So that** 能够实现特殊视觉效果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 contentModifier THEN 默认渲染被跳过 | 正常 |
| AC-1.2 | WHEN ContentModifier 回调执行 THEN 接收 GaugeConfiguration（value/min/max/enabled） | 正常 |
| AC-1.3 | WHEN API 版本 < 12 THEN contentModifier 不生效 | 边界 |

### US-2: 开发者设置隐私敏感模式

**As a** 应用开发者  
**I want to** 通过 privacySensitive 隐藏数据  
**So that** 能够保护敏感信息

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN privacySensitive = true THEN 数据以遮罩显示 | 正常 |
| AC-2.2 | WHEN privacySensitive = false THEN 数据正常显示 | 正常 |

### US-3: Native 开发者通过 C-API 使用 Gauge

**As a** Native 开发者  
**I want to** 通过 C-API 创建和控制 Gauge  
**So that** 能够在 Native 层使用仪表盘组件

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 调用 GetGaugeModifier() THEN 返回有效修饰器指针 | 正常 |
| AC-3.2 | WHEN 调用 SetGaugeValue() THEN 值被更新 | 正常 |
| AC-3.3 | WHEN 调用 SetGaugeColors() THEN 颜色被应用 | 正常 |
| AC-3.4 | WHEN 调用 SetGaugeTrackShadow() THEN 阴影被应用 | 正常 |

## 验收追溯

| AC | 关联规则 | 验证方式 |
|----|----------|----------|
| AC-1.1 | R-1 | 单元测试 |
| AC-1.2 | R-2 | 单元测试 |
| AC-1.3 | R-3 | API 版本测试 |
| AC-2.1 | R-4 | 单元测试 |
| AC-2.2 | R-5 | 单元测试 |
| AC-3.1 | R-6 | C-API 单元测试 |
| AC-3.2 | R-7 | C-API 单元测试 |
| AC-3.3 | R-8 | C-API 单元测试 |
| AC-3.4 | R-9 | C-API 单元测试 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 关联AC |
|--------|------|----------|----------|--------|
| R-1 | 行为 | 设置 contentModifier | 跳过默认渲染 | AC-1.1 |
| R-2 | 行为 | ContentModifier 回调 | 接收 GaugeConfiguration | AC-1.2 |
| R-3 | 边界 | API < 12 | contentModifier 不生效 | AC-1.3 |
| R-4 | 行为 | privacySensitive = true | 数据遮罩显示 | AC-2.1 |
| R-5 | 行为 | privacySensitive = false | 数据正常显示 | AC-2.2 |
| R-6 | 行为 | GetGaugeModifier() | 返回有效指针 | AC-3.1 |
| R-7 | 行为 | SetGaugeValue() | 更新 value | AC-3.2 |
| R-8 | 行为 | SetGaugeColors() | 应用颜色 | AC-3.3 |
| R-9 | 行为 | SetGaugeTrackShadow() | 应用阴影 | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 |
|------|------------|----------|
| VM-1 | ContentModifier 跳过默认渲染 | 单元测试 |
| VM-2 | privacySensitive 遮罩效果 | 单元测试 |
| VM-3 | C-API 接口 | C-API 单元测试 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|----------|---------|
| `contentModifier(value: ContentModifier<GaugeConfiguration>)` | Public | ContentModifier | void | 自定义渲染 | AC-1.1~1.3 |
| `privacySensitive(value: Optional<boolean>)` | Public | boolean | void | 隐私模式 | AC-2.1, AC-2.2 |

### C-API 接口

| API 名称 | 开放范围 | 功能描述 | 关联 AC |
|----------|----------|----------|---------|
| `GetGaugeModifier()` | System | 获取修饰器 | AC-3.1 |
| `SetGaugeValue(node, value)` | System | 设置值 | AC-3.2 |
| `SetGaugeColors(node, colors)` | System | 设置颜色 | AC-3.3 |
| `SetGaugeTrackShadow(node, shadow)` | System | 设置阴影 | AC-3.4 |

## 接口规格

### contentModifier

| 属性 | 值 |
|------|-----|
| 函数签名 | `contentModifier<GaugeConfiguration>(value: ContentModifier): void` |
| 开放范围 | Public |
| 关联 AC | AC-1.1 ~ AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束 |
|------|------|------|--------|------|
| value | ContentModifier | 是 | - | API 12+ |

### privacySensitive

| 属性 | 值 |
|------|-----|
| 函数签名 | `privacySensitive(value: Optional<boolean>): void` |
| 开放范围 | Public |
| 关联 AC | AC-2.1, AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束 |
|------|------|------|--------|------|
| value | boolean | 是 | false | 无 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** API 12+ (contentModifier/privacySensitive)
- **API 版本号策略:** contentModifier 和 privacySensitive 需 API 12+

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| ContentModifier 跳过默认渲染 | useContentModifier 标志控制 | AC-1.1 |
| C-API 双范式支持 | Dynamic + Static modifier | AC-3.1~3.4 |

## 非功能性需求

| 类型 | 指标 | 验证方式 |
|------|------|----------|
| 性能 | 无特殊要求 | N/A |
| 安全 | 无权限校验 | 代码评审 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 |
|------|--------|------|
| 无障碍 | 是 | privacySensitive 影响无障碍 |
| 深色模式 | 是 | contentModifier 支持自定义 |

## Spec 自审清单

- [x] 无占位符
- [x] AC 使用 WHEN/THEN 格式
- [x] 范围边界明确
- [x] AC 与规则一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Gauge ContentModifier 跳过默认渲染机制"
  - repo: "openharmony/arkui_ace_engine"
    query: "Gauge privacySensitive 隐私敏感模式实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "Gauge C-API GetGaugeModifier 和属性设置接口"
```