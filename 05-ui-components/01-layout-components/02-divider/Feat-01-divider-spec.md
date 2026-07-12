# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Divider 组件全量规格 |
| 特性编号 | Func-05-01-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7+ (crossplatform since 10, form since 9, atomicservice since 11) |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单 |

Divider 是 ArkUI 提供的分割线组件，用于分隔不同内容块。组件不支持子组件，提供 4 个专属属性：`vertical`（方向）、`color`（颜色）、`strokeWidth`（线宽）、`lineCap`（端点样式）。

## 本次变更范围（Delta）

> 存量特性补录，lineage: new-on-legacy。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Divider 全量 4 属性规格 | 覆盖 vertical/color/strokeWidth/lineCap 的行为、布局、绘制、主题适配 |
| ADDED | C-API 双通道规格 | 覆盖 legacy arkoala modifier 和 generated modifier 两套路径 |
| ADDED | API 版本行为差异 | strokeWidth 默认值在 API 10 前后的变化 |

## 输入文档

- 需求基线：已有能力补录（无独立 proposal.md）
- 设计文档：`specs/05-ui-components/01-layout-components/02-divider/design.md`
- SDK 类型定义：`interface/sdk-js/api/@internal/component/ets/divider.d.ts`
- SDK 静态类型定义：`interface/sdk-js/api/arkui/component/divider.static.d.ets`

## 用户故事

### US-1: 使用分割线分隔内容

**作为** ArkUI 应用开发者
**我想要** 在页面中使用分割线组件分隔不同内容块
**以便** 页面具有清晰的视觉层次

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `Divider()` 创建组件且不设任何属性 THEN 渲染一条水平分割线，颜色为主题色 `#33182431`，线宽 1px（API>=10）或 theme strokeWidth（API<10），端点样式为 Butt | 正常 |
| AC-1.2 | WHEN 设置 `vertical(true)` THEN 分割线变为垂直方向，宽度（主轴）由 strokeWidth 决定，高度（交叉轴）填充可用高度 | 正常 |
| AC-1.3 | WHEN 设置 `vertical(false)` 或不设 vertical THEN 分割线为水平方向，高度由 strokeWidth 决定，宽度填充可用宽度 | 正常 |
| AC-1.4 | WHEN 设置 `color(Color.Red)` THEN 分割线颜色变为红色；切换系统深色/浅色模式时颜色不变（用户显式设置优先） | 正常 |
| AC-1.5 | WHEN 未设置 color 且系统从浅色模式切换到深色模式 THEN 分割线颜色自动跟随 DividerTheme 更新 | 正常 |
| AC-1.6 | WHEN 设置 `strokeWidth(10)` THEN 分割线线宽变为 10vp | 正常 |
| AC-1.7 | WHEN 设置 `lineCap(LineCapStyle.Round)` THEN 分割线两端显示圆形端点，分割线实际长度增加一个 strokeWidth（端点各半个 strokeWidth 的延伸） | 正常 |
| AC-1.8 | WHEN 设置 `lineCap(LineCapStyle.Square)` THEN 分割线两端显示方形端点，分割线实际长度增加一个 strokeWidth | 正常 |

### US-2: 异常输入处理

**作为** ArkUI 应用开发者
**我想要** 组件在接收无效输入时有可预期的降级行为
**以便** 应用不因参数错误而崩溃

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 传入无效 color 值（如 `color(undefined)`） THEN 颜色重置为 DividerTheme 默认色 | 异常 |
| AC-2.2 | WHEN 传入无效 strokeWidth 值（如负数、NaN、百分比） THEN 线宽回退为默认值 1px（API>=10）或 theme strokeWidth（API<10） | 异常 |
| AC-2.3 | WHEN 传入无效 lineCap 整数值（非 0/1/2） THEN 端点样式回退为 `LineCapStyle.Butt` | 异常 |
| AC-2.4 | WHEN strokeWidth 设置值大于分割线长度（dividerLength）且 strokeWidthLimitation 为 true THEN strokeWidth 被裁剪为 dividerLength | 边界 |
| AC-2.5 | WHEN strokeWidth 设置值大于父容器约束的交叉轴尺寸 THEN strokeWidth 被裁剪为父容器约束值 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-----|---------|-----------|---------|------|
| AC-1.1 | R-1, R-2, R-3, R-10 | TASK-01 | UT + 手动验证 | divider_pattern_test |
| AC-1.2 | R-1, R-4 | TASK-01 | UT | divider_layout_algorithm_test |
| AC-1.3 | R-1, R-4 | TASK-01 | UT | divider_layout_algorithm_test |
| AC-1.4 | R-5, R-8 | TASK-01 | UT + 手动验证 | divider_pattern_test |
| AC-1.5 | R-5, R-9 | TASK-01 | UT + 手动验证 | divider_pattern_test |
| AC-1.6 | R-2 | TASK-01 | UT | divider_layout_algorithm_test |
| AC-1.7 | R-6, R-7 | TASK-01 | UT + 手动验证 | divider_paint_method_test |
| AC-1.8 | R-6, R-7 | TASK-01 | UT + 手动验证 | divider_paint_method_test |
| AC-2.1 | R-11 | TASK-01 | UT | js_divider_test |
| AC-2.2 | R-12 | TASK-01 | UT | js_divider_test |
| AC-2.3 | R-13 | TASK-01 | UT | js_divider_test |
| AC-2.4 | R-14 | TASK-01 | UT | divider_layout_algorithm_test |
| AC-2.5 | R-15 | TASK-01 | UT | divider_layout_algorithm_test |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 调用 `Divider()` 创建组件 | 创建 FrameNode（tag: `V2::DIVIDER_ETS_TAG`），关联 DividerPattern，默认水平方向 | 组件不支持子组件；FocusType 为 NODE、不可获焦 | AC-1.1, AC-1.2, AC-1.3 |
| R-2 | 行为 | 设置 `strokeWidth(value)` 传入合法正数 Dimension | 值存入 DividerLayoutProperty::StrokeWidth，触发 PROPERTY_UPDATE_MEASURE | 不支持百分比。API>=10 默认 1.0_px；API<10 默认 DividerTheme::GetStokeWidth()（通常 1.0_vp） | AC-1.1, AC-1.6 |
| R-3 | 行为 | 设置 `lineCap(LineCapStyle.Butt)` 或不设 lineCap，且 strokeWidthLimitation 为 true（默认） | lineCap 存储为 BUTT，但在 DividerModifier::onDraw 时被隐式替换为 SQUARE 再传给 DividerPainter | 仅当 strokeWidthLimitation=true 时发生此隐式升级 | AC-1.1 |
| R-4 | 行为 | 设置 `vertical(true)` | 布局算法：dividerLength 取 selfIdealSize.Height() 或 percentReference.Height()；最终尺寸为 SizeF(constrainStrokeWidth, dividerLength) | vertical 存入 DividerLayoutProperty，触发 PROPERTY_UPDATE_MEASURE | AC-1.2, AC-1.3 |
| R-5 | 行为 | 设置 `color(ResourceColor)` 传入合法颜色值 | 颜色存入 DividerRenderProperty::DividerColor，触发 PROPERTY_UPDATE_RENDER；同时设置 DividerColorSetByUser=true（当 ConfigChangePerform 开启时） | 支持 ResourceObject 动态资源更新（暗色模式切换等） | AC-1.4, AC-1.5 |
| R-6 | 行为 | 设置 `lineCap(LineCapStyle.Round)` 或 `lineCap(LineCapStyle.Square)` | DividerPaintMethod 中 dividerLength 增加一个 constrainStrokeWidth，offset 沿主轴前移半个 strokeWidth，确保端点视觉居中在布局边界内 | boundsRect 被设置为调整后的尺寸 | AC-1.7, AC-1.8 |
| R-7 | 行为 | DividerPainter::DrawLine 执行绘制 | 使用 RSPen，AntiAlias=true，笔宽=constrainStrokeWidth，CapStyle=映射后的 RSCapStyle，颜色=dividerColor。BUTT 端点时起止点偏移半个 strokeWidth；SQUARE/ROUND 端点时起止点偏移整个 strokeWidth 且终点长度减去一个 strokeWidth 补偿端点延伸 | N/A | AC-1.7, AC-1.8 |
| R-8 | 行为 | DividerColorSetByUser=true 时系统颜色配置变更（深色/浅色切换） | DividerPattern::OnColorConfigurationUpdate 检测到 DividerColorSetByUser=true，跳过颜色更新，保持用户设置的颜色 | N/A | AC-1.4 |
| R-9 | 行为 | DividerColorSetByUser=false（未显式设 color）时系统颜色配置变更 | DividerPattern::OnColorConfigurationUpdate 调用 UpdateDividerColorByTheme 更新为新主题色 | 同时 OnThemeScopeUpdate 也返回 true 触发重绘 | AC-1.5 |
| R-10 | 行为 | Token Theme 应用时（DividerThemeWrapper::ApplyTokenTheme） | 仅覆盖 DividerTheme::color_（取 theme.Colors()->CompDivider()），不覆盖 strokeWidth | strokeWidth 不随 token theme 变化 | AC-1.1 |
| R-11 | 异常 | 调用 `color(undefined)` 或传入无法解析的颜色值（ParseJsColor 返回 false） | 调用 DividerModel::ResetDividerColor()，颜色重置为 DividerTheme 默认色，DividerColorSetByUser 清除为 false | N/A | AC-2.1 |
| R-12 | 异常 | 调用 `strokeWidth(负数)` 或 `strokeWidth(NaN)` 或 `strokeWidth("50%")` | ParseJsDimensionVpNG 失败或值不为正，回退为默认值 1.0_px（API>=10）或 theme strokeWidth（API<10）；百分比在 ParseJsDimensionVpNG 中被显式禁止 | 转换为像素后值<=0 也触发此回退 | AC-2.2 |
| R-13 | 异常 | 调用 `lineCap(无效整数)` 如 lineCap(99) | JSDivider::SetLineCap 中三路分支均不匹配，lineCapStyle 默认为 LineCap::BUTT | 仅识别 SQUARE(int值) 和 ROUND(int值)，其余一律回退 | AC-2.3 |
| R-14 | 边界 | strokeWidth 值大于 dividerLength 且 strokeWidthLimitation=true | DividerLayoutAlgorithm::MeasureContent 中 constrainStrokeWidth = min(strokeWidth, dividerLength_) | strokeWidthLimitation 默认为 true | AC-2.4 |
| R-15 | 边界 | strokeWidth 值大于父容器交叉轴约束（height for horizontal / width for vertical） | constrainStrokeWidth 进一步裁剪为 selfIdealSize 的交叉轴值（如已设置） | 最终还受 contentConstraint.Constrain() 约束 | AC-2.5 |

## 验证映射

| VM编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | R-1, R-4 | UT: DividerLayoutAlgorithm::MeasureContent | vertical=true/false 时尺寸计算正确 |
| VM-2 | R-2, R-12 | UT: StrokeWidth 设置/默认/回退 | API 版本分支默认值；百分比被拒绝；负数/NaN 回退 |
| VM-3 | R-3 | UT: DividerModifier::onDraw | strokeWidthLimitation=true 时 BUTT→SQUARE 隐式升级 |
| VM-4 | R-5, R-8, R-9, R-11 | UT: color 设置/重置/主题跟随 | 用户设色后主题不覆盖；未设色时主题跟随 |
| VM-5 | R-6, R-7 | UT: DividerPaintMethod + DividerPainter | ROUND/SQUARE 端点时长度补偿和偏移计算正确 |
| VM-6 | R-14, R-15 | UT: constrainStrokeWidth 裁剪逻辑 | strokeWidth > dividerLength 和 > 父容器约束时的裁剪 |
| VM-7 | R-10 | UT: DividerThemeWrapper::ApplyTokenTheme | token theme 仅影响 color 不影响 strokeWidth |

## API 变更分析

> 本特性为已有能力补录，API 行为无变更。

### 新增 API

N/A — Divider 全部 API 自 API 7 起已存在。

### 变更/废弃 API

N/A — 无 API 变更或废弃。

## 接口规格

### 接口定义

**Divider()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `DividerAttribute Divider()` |
| 返回值 | `DividerAttribute` — Divider 组件属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---------|---------|--------|
| 1 | 调用 Divider() | 创建水平分割线，默认参数：vertical=false, color=主题色, strokeWidth=1px(API>=10), lineCap=Butt | AC-1.1 |

---

**vertical(value: boolean)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `DividerAttribute vertical(value: boolean)` |
| 返回值 | `DividerAttribute` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.2, AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 否 | false | true=垂直分割线，false=水平分割线。无效值按 false 处理 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---------|---------|--------|
| 1 | vertical(true) | 分割线垂直显示，宽度=strokeWidth，高度填充可用空间 | AC-1.2 |
| 2 | vertical(false) 或不设置 | 分割线水平显示，高度=strokeWidth，宽度填充可用空间 | AC-1.3 |

---

**color(value: ResourceColor)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `DividerAttribute color(value: ResourceColor)` |
| 返回值 | `DividerAttribute` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.4, AC-1.5, AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceColor | 否 | '#33182431'（主题色） | 支持 Color 枚举、十六进制字符串、Resource 对象。无效值触发重置为主题默认色 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---------|---------|--------|
| 1 | color(Color.Red) | 分割线颜色变为红色，标记 DividerColorSetByUser=true | AC-1.4 |
| 2 | 未设 color + 系统主题切换 | 颜色自动跟随 DividerTheme 更新 | AC-1.5 |
| 3 | color(undefined) | 颜色重置为 DividerTheme 默认色，清除 DividerColorSetByUser 标记 | AC-2.1 |

---

**strokeWidth(value: number | string)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `DividerAttribute strokeWidth(value: number \| string)` |
| 返回值 | `DividerAttribute` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.6, AC-2.2, AC-2.4, AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number \| string | 否 | 1px (API>=10) / theme值 (API<10) | 单位 vp。不支持百分比。负数/NaN/非正值回退为默认值。实际渲染受 min(strokeWidth, dividerLength) 和父容器约束裁剪 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---------|---------|--------|
| 1 | strokeWidth(10) | 线宽设为 10vp，触发重新布局 | AC-1.6 |
| 2 | strokeWidth(-1) 或 strokeWidth("50%") | 回退为默认值 | AC-2.2 |
| 3 | strokeWidth(999) 但 dividerLength=100 | constrainStrokeWidth 裁剪为 100 | AC-2.4 |

---

**lineCap(value: LineCapStyle)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `DividerAttribute lineCap(value: LineCapStyle)` |
| 返回值 | `DividerAttribute` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.7, AC-1.8, AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | LineCapStyle | 否 | LineCapStyle.Butt | 枚举值：Butt/Round/Square。无效整数值回退为 Butt |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---------|---------|--------|
| 1 | lineCap(LineCapStyle.Round) | 两端圆形端点，线条长度增加一个 strokeWidth 补偿 | AC-1.7 |
| 2 | lineCap(LineCapStyle.Square) | 两端方形端点，线条长度增加一个 strokeWidth 补偿 | AC-1.8 |
| 3 | lineCap(99) 无效值 | 回退为 LineCapStyle.Butt | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更：** 是 — strokeWidth 默认值在 API 10 发生变化：API<10 使用 DividerTheme::GetStokeWidth()（通常 1.0_vp），API>=10 固定为 1.0_px。两者在不同 DPI 设备上可能产生不同渲染结果。
- **配置文件格式变更：** 否
- **数据存储格式变更：** 否
- **最低支持版本：** API 7
- **API 版本号策略：** Divider 全部 4 属性 @since 7；@crossplatform since 10；@form since 9；@atomicservice since 11。静态版本 @since 23 static。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 不支持子组件 | Divider 为叶子节点，不接受子组件 | AC-1.1 |
| 不支持百分比 strokeWidth | ParseJsDimensionVpNG 显式禁止百分比参数 | AC-2.2 |
| strokeWidthLimitation 为内部属性 | 默认 true，非公开 API，控制 strokeWidth 是否被 dividerLength 裁剪 | AC-2.4 |
| DividerColorSetByUser 为内部标志 | 控制主题/暗色模式切换是否覆盖颜色 | AC-1.4, AC-1.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | N/A — 纯绘制组件，无复杂计算 | N/A | N/A |
| 功耗 | N/A | N/A | N/A |
| 内存 | N/A — 无额外内存分配 | N/A | N/A |
| 安全 | N/A — 无敏感数据处理 | N/A | N/A |
| 可靠性 | 无效输入不崩溃，回退到默认值 | UT | AC-2.1~2.5 |
| 可测试性 | 全部属性可通过 UT 验证 | UT + C-API test | V-1~V-7 |
| 自动化维测 | DumpInfo 输出 divider color 信息 | Inspector | divider_pattern.cpp:59-67 |
| 定界定位 | N/A | N/A | N/A |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 标准行为 | UT | N/A |
| 平板 | 无差异 | 标准行为 | UT | N/A |
| 折叠屏 | 无差异 | 标准行为 | UT | N/A |

> 注：SDK 文档提到"部分设备硬件限制下 1px 分割线取整后可能不显示"，建议使用 2px。此为硬件限制而非组件行为差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | Divider 为纯视觉分割线，FocusType=NODE 不可获焦，无无障碍 action | N/A |
| 大字体 | 否 | Divider 不含文本内容 | N/A |
| 深色模式 | 是 | 未显式设 color 时自动跟随主题色切换（R-9）；显式设 color 后不跟随（R-8）。Token theme 仅覆盖 color（R-10） | AC-1.4, AC-1.5 |
| 多窗口/分屏 | 否 | Divider 随父容器布局自适应，无特殊处理 | N/A |
| 多用户 | 否 | 无用户相关状态 | N/A |
| 版本升级 | 是 | strokeWidth 默认值在 API 10 前后不同，见兼容性声明 | AC-1.1, AC-2.2 |
| 生态兼容 | 否 | 无跨生态差异 | N/A |

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
    query: "Divider 组件 pattern/layout/paint 全链路实现"
```

**关键文档：**
- SDK 动态版本: `interface/sdk-js/api/@internal/component/ets/divider.d.ts`
- SDK 静态版本: `interface/sdk-js/api/arkui/component/divider.static.d.ets`
- 设计文档: `specs/05-ui-components/01-layout-components/02-divider/design.md`
