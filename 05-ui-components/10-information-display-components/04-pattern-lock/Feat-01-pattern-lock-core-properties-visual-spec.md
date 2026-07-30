# 特性规格

## 概述

| Field | Content |
|-------|---------|
| 特性名称 | PatternLock 创建、核心属性与视觉样式 |
| 特性编号 | Func-05-10-04-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | PatternLock 组件核心属性规格 | sideLength, circleRadius, strokeWidth, selectedColor, pathColor, activeColor, regularColor, activeCircleColor, activeCircleRadius |
| ADDED | 9 宫格视觉样式规格 | 单元格中心计算、圆点绘制、路径连接 |

## 输入文档

- 设计文档: `specs/05-ui-components/10-information-display-components/04-pattern-lock/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/patternlock/`

## 用户故事

### US-1: 创建基础图案锁组件

**作为** 应用开发者  
**我想要** 创建一个 PatternLock 组件并设置基本尺寸  
**以便** 在应用中提供图案解锁功能

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 PatternLock() 创建组件 THEN 返回 PatternLockController 实例 | 正常 |
| AC-1.2 | WHEN 未设置 sideLength THEN 使用主题默认值（通常为 300vp） | 正常 |
| AC-1.3 | WHEN sideLength 设置为有效正值 THEN 组件尺寸为该值的正方形 | 正常 |
| AC-1.4 | WHEN sideLength 设置为 <=0 THEN 使用主题默认值 | 边界 |

### US-2: 设置圆点样式

**作为** 应用开发者  
**我想要** 自定义圆点的大小和颜色  
**以便** 匹配应用的整体视觉风格

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 circleRadius 为有效正值 THEN 9 个圆点使用该半径绘制 | 正常 |
| AC-2.2 | WHEN circleRadius 依赖 sideLength 进行 px 转换 THEN 圆点大小与组件尺寸成比例 | 正常 |
| AC-2.3 | WHEN 设置 selectedColor THEN 选中状态的圆点使用该颜色 | 正常 |
| AC-2.4 | WHEN 设置 regularColor THEN 未选中状态的圆点使用该颜色 | 正常 |
| AC-2.5 | WHEN 未设置颜色属性 THEN 使用主题默认颜色 | 正常 |

### US-3: 设置路径样式

**作为** 应用开发者  
**我想要** 自定义连接线的颜色和宽度  
**以便** 突出显示用户绘制的图案路径

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 pathColor THEN 连接路径使用该颜色 | 正常 |
| AC-3.2 | WHEN 设置 strokeWidth THEN 连接线使用该宽度 | 正常 |
| AC-3.3 | WHEN 连接多个点 THEN 路径线段端点为圆形（ROUND_CAP） | 正常 |

### US-4: 设置激活样式

**作为** 应用开发者  
**我想要** 自定义激活状态的视觉效果  
**以便** 提供清晰的交互反馈

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 设置 activeColor THEN 激活状态的圆点使用该颜色 | 正常 |
| AC-4.2 | WHEN 设置 activeCircleColor THEN 选中点的背景圆使用该颜色 | 正常 |
| AC-4.3 | WHEN 设置 activeCircleRadius THEN 选中点的背景圆使用该半径 | 正常 |
| AC-4.4 | WHEN 未设置 activeCircleRadius THEN 默认为 0vp（不显示背景圆） | 边界 |

### US-5: 组件布局行为

**作为** 应用开发者  
**我想要** PatternLock 组件自动适应容器大小  
**以便** 在不同屏幕尺寸下正常显示

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 测量组件尺寸 THEN 返回正方形（宽高相等） | 正常 |
| AC-5.2 | WHEN 容器宽度小于 sideLength THEN 组件宽度受容器限制 | 边界 |
| AC-5.3 | WHEN 设置 layoutPolicy 为固定宽度/高度 THEN 使用 sideLength 作为该维度尺寸 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-1 | 单元测试 | patternlock_test_ng.cpp |
| AC-1.2 | R-2 | TASK-1 | 渲染测试 | layout_algorithm 测试 |
| AC-1.3 | R-3 | TASK-1 | 布局测试 | MeasureContent 验证 |
| AC-1.4 | R-4 | TASK-1 | 边界测试 | sideLength<=0 测试 |
| AC-2.1 | R-5 | TASK-1 | 渲染测试 | modifier 圆点绘制验证 |
| AC-2.2 | R-6 | TASK-1 | 比例测试 | ConvertToPxWithSize 验证 |
| AC-2.3 | R-7 | TASK-1 | 颜色测试 | selectedColor 绘制验证 |
| AC-2.4 | R-8 | TASK-1 | 颜色测试 | regularColor 绘制验证 |
| AC-2.5 | R-9 | TASK-1 | 默认值测试 | 主题获取验证 |
| AC-3.1 | R-10 | TASK-1 | 渲染测试 | pathColor 绘制验证 |
| AC-3.2 | R-11 | TASK-1 | 渲染测试 | strokeWidth 绘制验证 |
| AC-3.3 | R-12 | TASK-1 | 渲染测试 | ROUND_CAP 验证 |
| AC-4.1 | R-13 | TASK-1 | 颜色测试 | activeColor 绘制验证 |
| AC-4.2 | R-14 | TASK-1 | 颜色测试 | activeCircleColor 绘制验证 |
| AC-4.3 | R-15 | TASK-1 | 渲染测试 | activeCircleRadius 验证 |
| AC-4.4 | R-16 | TASK-1 | 边界测试 | 默认值验证 |
| AC-5.1 | R-17 | TASK-1 | 布局测试 | 正方形验证 |
| AC-5.2 | R-18 | TASK-1 | 边界测试 | 容器限制测试 |
| AC-5.3 | R-19 | TASK-1 | 布局测试 | layoutPolicy 测试 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 PatternLock() | 返回 PatternLockController 实例 | 无 | AC-1.1 |
| R-2 | 行为 | 未设置 sideLength | 使用 patternLockTheme->GetSideLength() | 默认约 300vp | AC-1.2 |
| R-3 | 行为 | sideLength > 0 | 存储到 LayoutProperty，触发 PROPERTY_UPDATE_MEASURE | 无 | AC-1.3 |
| R-4 | 边界 | sideLength <= 0 | 使用主题默认值，不报错 | 最小有效值 >0 | AC-1.4 |
| R-5 | 行为 | circleRadius > 0 | 存储到 PaintProperty，触发 PROPERTY_UPDATE_RENDER | 无 | AC-2.1 |
| R-6 | 行为 | 绘制圆点时 | 调用 circleRadius.ConvertToPxWithSize(sideLength) | 依赖 sideLength | AC-2.2 |
| R-7 | 行为 | 设置 selectedColor | 存储到 PaintProperty + SetSelectedColorSetByUser=true | 触发 RENDER | AC-2.3 |
| R-8 | 行为 | 设置 regularColor | 存储到 PaintProperty + SetRegularColorSetByUser=true | 触发 RENDER | AC-2.4 |
| R-9 | 行为 | 未设置颜色 | 使用 patternLockTheme->Get*Color() | 从主题获取 | AC-2.5 |
| R-10 | 行为 | 设置 pathColor | 存储到 PaintProperty，传递给 Modifier | 触发 RENDER | AC-3.1 |
| R-11 | 行为 | 设置 strokeWidth | 存储到 PaintProperty，传递给 Modifier | 触发 RENDER | AC-3.2 |
| R-12 | 行为 | 绘制连接线 | 设置 RSPen::CapStyle::ROUND_CAP | 圆形端点 | AC-3.3 |
| R-13 | 行为 | 设置 activeColor | 存储到 PaintProperty + SetActiveColorSetByUser=true | 触发 RENDER | AC-4.1 |
| R-14 | 行为 | 设置 activeCircleColor | 存储到 PaintProperty + SetActiveCircleColorSetByUser=true | 触发 RENDER | AC-4.2 |
| R-15 | 行为 | 设置 activeCircleRadius | 存储到 PaintProperty，传递给 Modifier | 触发 RENDER | AC-4.3 |
| R-16 | 边界 | 未设置 activeCircleRadius | 使用 Dimension(0.0f, DimensionUnit::VP)，不显示背景圆 | 默认值 0vp | AC-4.4 |
| R-17 | 行为 | MeasureContent() | 返回 SizeF(length, length)，length 为正方形边长 | 宽高相等 | AC-5.1 |
| R-18 | 边界 | 容器宽度 < sideLength | 使用 min(selfIdealWidth, selfIdealHeight) 作为上限 | 受容器限制 | AC-5.2 |
| R-19 | 行为 | layoutPolicy.IsWidthFix/IsHeightFix | 使用 sideLength 作为对应维度尺寸 | 固定尺寸模式 | AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1（组件创建） | 单元测试 | Controller 返回值验证 |
| VM-2 | AC-1.2~1.4（sideLength） | 布局测试 | 默认值、有效值、边界值 |
| VM-3 | AC-2.1~2.5（圆点样式） | 渲染测试 | 圆点半径、颜色绘制验证 |
| VM-4 | AC-3.1~3.3（路径样式） | 渲染测试 | 路径颜色、线宽、端点样式 |
| VM-5 | AC-4.1~4.4（激活样式） | 渲染测试 | 激活颜色、背景圆 |
| VM-6 | AC-5.1~5.3（布局行为） | 布局测试 | 正方形、容器限制、固定尺寸 |

## API 变更分析

### 新增 API

> 已有实现补录，无新增 API。

### 变更/废弃 API

> 无变更或废弃 API。

## 接口规格

### 接口定义

**PatternLock()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `PatternLock(): PatternLockController` |
| 返回值 | `PatternLockController` — 控制器实例，用于重置图案 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 创建 FrameNode，返回 PatternLockController | AC-1.1 |
| 2 | 多次调用 | 每次返回新的 Controller 实例 | AC-1.1 |

---

**SetSideLength()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `sideLength(length: Length): PatternLock` |
| 返回值 | `PatternLock` — 组件本身，支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.2, AC-1.3, AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| length | Length | 否 | 主题默认值（约 300vp） | <=0 时使用默认值 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | length > 0 | 存储到 LayoutProperty，触发 PROPERTY_UPDATE_MEASURE | AC-1.3 |
| 2 | length <= 0 | 使用主题默认值，不报错 | AC-1.4 |
| 3 | 未调用 | 使用主题默认值 | AC-1.2 |

---

**SetCircleRadius()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `circleRadius(radius: Length): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| radius | Length | 否 | 主题默认值（约 14vp） | <=0 时使用默认值；依赖 sideLength 进行 px 转换 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | radius > 0 | 存储到 PaintProperty，触发 PROPERTY_UPDATE_RENDER | AC-2.1 |
| 2 | 绘制时 | 调用 ConvertToPxWithSize(sideLength) 进行比例转换 | AC-2.2 |

---

**SetSelectedColor()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `selectedColor(color: ResourceColor): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| color | ResourceColor | 否 | 主题默认值 | 支持颜色值、资源引用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置有效颜色 | 存储到 PaintProperty + SetSelectedColorSetByUser=true | AC-2.3 |
| 2 | 绘制选中点 | 使用 selectedColor 绘制选中状态的圆点 | AC-2.3 |

---

**SetRegularColor()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `regularColor(color: ResourceColor): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| color | ResourceColor | 否 | 主题默认值 | 支持颜色值、资源引用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置有效颜色 | 存储到 PaintProperty + SetRegularColorSetByUser=true | AC-2.4 |
| 2 | 绘制未选中点 | 使用 regularColor 绘制未选中状态的圆点 | AC-2.4 |

---

**SetPathColor()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pathColor(color: ResourceColor): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| color | ResourceColor | 否 | 主题默认值 | 支持颜色值、资源引用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置有效颜色 | 存储到 PaintProperty + SetPathColorSetByUser=true | AC-3.1 |
| 2 | 绘制连接线 | 使用 pathColor 绘制点之间的连接路径 | AC-3.1 |

---

**SetStrokeWidth()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `strokeWidth(width: Length): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| width | Length | 否 | 主题默认值（约 2vp） | <=0 时使用默认值 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | width > 0 | 存储到 PaintProperty，触发 PROPERTY_UPDATE_RENDER | AC-3.2 |
| 2 | 绘制连接线 | 设置 RSPen 的宽度 | AC-3.2 |
| 3 | 线段端点 | 使用 ROUND_CAP（圆形端点） | AC-3.3 |

---

**SetActiveColor()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `activeColor(color: ResourceColor): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| color | ResourceColor | 否 | 主题默认值 | 支持颜色值、资源引用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置有效颜色 | 存储到 PaintProperty + SetActiveColorSetByUser=true | AC-4.1 |
| 2 | 绘制激活点 | 最后一个选中点（移动中）使用 activeColor | AC-4.1 |

---

**SetActiveCircleColor()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `activeCircleColor(color: ResourceColor): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| color | ResourceColor | 否 | 使用 pathColor | 支持颜色值、资源引用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置有效颜色 | 存储到 PaintProperty + SetActiveCircleColorSetByUser=true | AC-4.2 |
| 2 | 绘制选中点背景 | 使用 activeCircleColor 绘制选中点的背景圆 | AC-4.2 |

---

**SetActiveCircleRadius()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `activeCircleRadius(radius: Length): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.3, AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| radius | Length | 否 | 0vp | <=0 时不显示背景圆 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | radius > 0 | 存储到 PaintProperty，触发 PROPERTY_UPDATE_RENDER | AC-4.3 |
| 2 | radius <= 0 或未设置 | 不显示选中点的背景圆 | AC-4.4 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** @since 8 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 属性分层存储 | sideLength 存 LayoutProperty（MEASURE），其他存 PaintProperty（RENDER） | AC-1.3, 所有属性 |
| 颜色追踪机制 | 每个 SetByUser 标志用于区分用户设置和主题默认值 | AC-2.3~2.5, AC-4.1, AC-4.2 |
| 依赖顺序 | circleRadius 需在 sideLength 确定后进行 px 转换 | AC-2.2 |
| 正方形约束 | 组件始终为正方形（宽高相等） | AC-5.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 属性设置不触发冗余重绘 | SetByUser 追踪机制 | 代码审查 |
| 内存 | 每点 4 个动画属性（共 36 个 AnimatablePropertyFloat） | 静态分析 | modifier.cpp:120-136 |
| 可测试性 | 支持 Host 单元测试 | 测试框架验证 | patternlock_test_ng.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 标准行为 | 渲染测试 | - |
| 平板 | 无差异 | 标准行为 | 渲染测试 | - |
| 折叠屏 | 无差异 | 标准行为 | 渲染测试 | - |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 支持 AccessibilityProperty，为每个点创建虚拟节点 | 无障碍朗读 |
| 大字体 | 否 | 组件尺寸由 sideLength 决定，不受大字体影响 | - |
| 深色模式 | 是 | 颜色属性支持主题切换，SetByUser 标志控制覆盖优先级 | 主题切换 |
| 多窗口/分屏 | 否 | 组件无状态依赖窗口 | - |
| 多用户 | 否 | 无用户状态 | - |
| 版本升级 | 是 | API 10+ 支持前景/背景模式切换 | 版本兼容 |
| 生态兼容 | 否 | 无外部依赖 | - |

## 行为场景（可选，Gherkin）

> L1 标准复杂度，使用"接口规格 → 行为场景"表覆盖，无需 Gherkin。

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
    query: "PatternLock 单元格中心计算公式的数学推导"
  - repo: "openharmony/arkui_ace_engine"
    query: "circleRadius 依赖 sideLength 进行 px 转换的实现细节"
  - repo: "openharmony/arkui_ace_engine"
    query: "颜色属性 SetByUser 追踪机制在主题切换时的行为"
```

**关键文档：**
- design.md: `specs/05-ui-components/10-information-display-components/04-pattern-lock/design.md`
- 源码: `frameworks/core/components_ng/pattern/patternlock/`