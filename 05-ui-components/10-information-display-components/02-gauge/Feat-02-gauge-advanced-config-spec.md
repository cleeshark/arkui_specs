# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Gauge 高级配置 |
| 特性编号 | Func-05-10-02-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 11+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Gauge 高级配置规格补录 | description/trackShadow/indicator（API 11+） |

## 输入文档

- 设计文档: `05-ui-components/10-information-display-components/02-gauge/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/gauge/`

## 用户故事

### US-1: 开发者为 Gauge 添加自定义描述

**As a** 应用开发者  
**I want to** 通过 description 添加自定义说明内容  
**So that** 能够为仪表盘提供更多上下文信息

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 description CustomBuilder THEN 内容显示在环形底部 | 正常 |
| AC-1.2 | WHEN 未设置 description THEN 不显示描述区域 | 正常 |
| AC-1.3 | WHEN API 版本 < 11 THEN description 不生效 | 边界 |

### US-2: 开发者为 Gauge 添加阴影效果

**As a** 应用开发者  
**I want to** 通过 trackShadow 添加阴影  
**So that** 能够增强视觉层次感

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 trackShadow({ radius: 20 }) THEN 显示模糊阴影 | 正常 |
| AC-2.2 | WHEN 设置 trackShadow({ offsetX: 5, offsetY: 5 }) THEN 阴影偏移 5x5 | 正常 |
| AC-2.3 | WHEN trackShadow.isShadowVisible = false THEN 不显示阴影 | 边界 |
| AC-2.4 | WHEN API 版本 < 11 THEN trackShadow 不生效 | 边界 |

### US-3: 开发者自定义 Gauge 指示器

**As a** 应用开发者  
**I want to** 通过 indicator 自定义指针图标  
**So that** 能够匹配应用风格

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 未设置 indicator THEN 使用默认三角形指针 | 正常 |
| AC-3.2 | WHEN 设置 indicator({ icon: 'path/to/icon.svg' }) THEN 使用自定义 SVG 图标 | 正常 |
| AC-3.3 | WHEN 指定非 SVG 图标 THEN 回退到默认三角形 | 边界 |
| AC-3.4 | WHEN 设置 indicator({ space: 10 }) THEN 指针距环边 10vp | 正常 |
| AC-3.5 | WHEN API 版本 < 11 THEN indicator 不生效 | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 |
|----|----------|----------|
| AC-1.1 | R-1 | 单元测试 |
| AC-1.2 | R-2 | 单元测试 |
| AC-1.3 | R-3 | API 版本测试 |
| AC-2.1 | R-4 | 单元测试 |
| AC-2.2 | R-5 | 单元测试 |
| AC-2.3 | R-6 | 单元测试 |
| AC-2.4 | R-7 | API 版本测试 |
| AC-3.1 | R-8 | 单元测试 |
| AC-3.2 | R-9 | 单元测试 |
| AC-3.3 | R-10 | 单元测试 |
| AC-3.4 | R-11 | 单元测试 |
| AC-3.5 | R-12 | API 版本测试 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 关联AC |
|--------|------|----------|----------|--------|
| R-1 | 行为 | 设置 description | CustomBuilder 内容显示在底部 | AC-1.1 |
| R-2 | 行为 | 未设置 description | 不显示描述区域 | AC-1.2 |
| R-3 | 边界 | API < 11 | description 不生效 | AC-1.3 |
| R-4 | 行为 | trackShadow({ radius }) | 显示模糊阴影 | AC-2.1 |
| R-5 | 行为 | trackShadow({ offsetX/Y }) | 阴影偏移 | AC-2.2 |
| R-6 | 边界 | isShadowVisible = false | 不显示阴影 | AC-2.3 |
| R-7 | 边界 | API < 11 | trackShadow 不生效 | AC-2.4 |
| R-8 | 行为 | 未设置 indicator | 默认三角形指针 | AC-3.1 |
| R-9 | 行为 | indicator({ icon: SVG }) | 自定义 SVG 图标 | AC-3.2 |
| R-10 | 边界 | 非 SVG 图标 | 回退默认三角形 | AC-3.3 |
| R-11 | 行为 | indicator({ space }) | 指针距环边指定值 | AC-3.4 |
| R-12 | 边界 | API < 11 | indicator 不生效 | AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 |
|------|------------|----------|
| VM-1 | description 节点创建 | 单元测试 |
| VM-2 | trackShadow 阴影绘制 | 单元测试 |
| VM-3 | indicator SVG 加载 | 单元测试 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|--------|----------|---------|
| `description(value: CustomBuilder)` | Public | CustomBuilder | void | 无 | 底部描述内容 | AC-1.1~1.3 |
| `trackShadow(value: GaugeShadowOptions)` | Public | {radius?, offsetX?, offsetY?} | void | 无 | 阴影配置 | AC-2.1~2.4 |
| `indicator(value: GaugeIndicatorOptions)` | Public | {icon?, space?} | void | 无 | 指针配置 | AC-3.1~3.5 |

## 接口规格

### description

| 属性 | 值 |
|------|-----|
| 函数签名 | `description(value: CustomBuilder): void` |
| 开放范围 | Public |
| 关联 AC | AC-1.1 ~ AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束 |
|------|------|------|--------|------|
| value | CustomBuilder | 是 | - | API 11+ |

### trackShadow

| 属性 | 值 |
|------|-----|
| 函数签名 | `trackShadow(value: GaugeShadowOptions): void` |
| 开放范围 | Public |
| 关联 AC | AC-2.1 ~ AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束 |
|------|------|------|--------|------|
| radius | number | 否 | 20.0 | 模糊半径 |
| offsetX | number | 否 | 5.0 | X 偏移 |
| offsetY | number | 否 | 5.0 | Y 偏移 |

### indicator

| 属性 | 值 |
|------|-----|
| 函数签名 | `indicator(value: GaugeIndicatorOptions): void` |
| 开放范围 | Public |
| 关联 AC | AC-3.1 ~ AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束 |
|------|------|------|--------|------|
| icon | ResourceStr | 否 | 三角形 | 仅 SVG |
| space | Dimension | 否 | 8vp | 距环边距离 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** API 11+
- **API 版本号策略:** 三个属性均需 API 11+

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| description 布局位置 | 使用主题常量计算位置 | AC-1.1 |
| indicator 仅支持 SVG | 非 SVG 回退默认 | AC-3.3 |

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
| 无障碍 | 是 | description 支持自定义内容 |
| 深色模式 | 是 | 阴影颜色支持主题 |

## Spec 自审清单

- [x] 无占位符
- [x] AC 使用 WHEN/THEN 格式
- [x] 范围边界明确
- [x] AC 与规则一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Gauge description 节点创建和布局位置"
  - repo: "openharmony/arkui_ace_engine"
    query: "Gauge trackShadow 阴影绘制实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "Gauge indicator SVG 加载和默认三角形"
```