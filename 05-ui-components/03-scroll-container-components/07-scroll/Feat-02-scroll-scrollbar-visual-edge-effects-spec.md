# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Scroll 滚动条与视觉边缘效果 |
| 特性编号 | Func-05-03-07-Feat-02 |
| 优先级 | P1 |
| 目标版本 | API 7 ~ 26+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 scrollBar/scrollBarColor/scrollBarWidth/scrollBarMargin/autoAdjustScrollBarMargin、edgeEffect、fadingEdge、clipContent 及对应 C-API。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/07-scroll/design.md` |
| SDK Dynamic | `ets/dynamic/component/scroll.d.ts` + `common.d.ts`(ScrollableCommonMethod) |
| BasePattern | `frameworks/core/components_ng/pattern/scrollable/scrollable_pattern.h/.cpp` |
| EdgeEffect | `frameworks/core/components_ng/pattern/scroll/scroll_edge_effect.h` + `effect/*` |
| InnerScrollBar | `frameworks/core/components_ng/pattern/scroll/inner/scroll_bar*.{h,cpp}` |
| Native Header | `interfaces/native/native_node.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 滚动条显示与样式

作为**应用开发者**，我想要**用 scrollBar/scrollBarColor/scrollBarWidth 控制滚动条显隐与外观**，以便**匹配视觉风格**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `scrollBar(BarState.Auto)`（默认） THEN 滚动时显示、静止隐藏 | 正常 |
| AC-1.2 | WHEN 设置 `scrollBar(BarState.On)` THEN 常显 | 正常 |
| AC-1.3 | WHEN 设置 `scrollBar(BarState.Off)` THEN 常隐 | 正常 |
| AC-1.4 | WHEN 设置 `scrollBarColor(color)`（@since 7，Color\|number\|string） THEN 滚动条颜色更新 | 正常 |
| AC-1.5 | WHEN 设置 `scrollBarColor(Color\|number\|string\|Resource)`（@since 22 Resource 重载） THEN 资源解析颜色 | 正常 |
| AC-1.6 | WHEN 设置 `scrollBarWidth(value)`（默认 4vp，@since 7） THEN 滚动条宽度更新 | 正常 |
| AC-1.7 | WHEN 设置 `scrollBarWidth(number\|string\|Resource)`（@since 26 Resource 重载） THEN 资源解析 | 正常 |

### US-2: 滚动条边距与自动避让

作为**应用开发者**，我想要**用 scrollBarMargin/autoAdjustScrollBarMargin 控制滚动条边距与自动避让**，以便**避开安全区/导航**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `scrollBarMargin(margin)`（@since 20） THEN 滚动条边距生效 | 正常 |
| AC-2.2 | WHEN 设置 `autoAdjustScrollBarMargin(enable)`（@since 26） THEN 自动根据布局调整边距 | 正常 |
| AC-2.3 | WHEN 不设 scrollBarWidth THEN 默认 4vp | 边界 |

### US-3: 边缘效果

作为**应用开发者**，我想要**用 edgeEffect 控制到达边缘的回弹/渐隐效果**，以便**提供物理反馈**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 不设 edgeEffect THEN 默认 `EdgeEffect.None`（构造 `ScrollablePattern(EdgeEffect::NONE,true)`，`scroll_pattern.h:48`） | 正常 |
| AC-3.2 | WHEN 设置 `edgeEffect(EdgeEffect.Spring, options?)` THEN 到达边缘弹簧回弹（scroll_spring_effect） | 正常 |
| AC-3.3 | WHEN 设置 `edgeEffect(EdgeEffect.Fade)` THEN 到达边缘渐隐（scroll_fade_effect，@since 11 options 可配 alwaysEnabled） | 正常 |
| AC-3.4 | WHEN 设置 `edgeEffect(EdgeEffect.None)` THEN 无边缘效果 | 正常 |

### US-4: 渐隐边缘与内容裁剪

作为**应用开发者**，我想要**用 fadingEdge/clipContent 控制内容渐隐与裁剪**，以便**视觉过渡与内容约束**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 设置 `fadingEdge(enabled, options?)`（@since 14） THEN 边缘渐隐渲染分支生效 | 正常 |
| AC-4.2 | WHEN 设置 `clipContent(clip: ContentClipMode\|RectShape)`（@since 14） THEN 内容按模式裁剪 | 正常 |
| AC-4.3 | WHEN C-API 设置 `NODE_SCROLL_BAR_*`/`NODE_SCROLL_EDGE_EFFECT`/`NODE_SCROLL_FADING_EDGE`/`NODE_SCROLL_CLIP_CONTENT`/`NODE_SCROLL_BAR_MARGIN`/`NODE_SCROLL_BAR_HEIGHT` THEN 经 node_modifier 写基类字段 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-2 | 单元测试：Auto 显隐 | `scrollable_pattern.cpp` |
| AC-1.2 | R-1 | TASK-SKELETON-2 | 单元测试：On 常显 | `scrollable_pattern.cpp` |
| AC-1.3 | R-1 | TASK-SKELETON-2 | 单元测试：Off 常隐 | `scrollable_pattern.cpp` |
| AC-1.4 | R-2 | TASK-SKELETON-2 | 单元测试：颜色 | `scroll.d.ts:1757` |
| AC-1.5 | R-2 | TASK-SKELETON-2 | 单元测试：Resource | `scroll.d.ts:1771` |
| AC-1.6 | R-3 | TASK-SKELETON-2 | 单元测试：宽度 4vp | `scroll.d.ts:1800` |
| AC-1.7 | R-3 | TASK-SKELETON-2 | 单元测试：Resource | `scroll.d.ts:1816` |
| AC-2.1 | R-4 | TASK-SKELETON-2 | 单元测试：margin | `common.d.ts:35056` |
| AC-2.2 | R-5 | TASK-SKELETON-2 | 单元测试：auto adjust | `common.d.ts:35070` |
| AC-2.3 | R-3 | TASK-SKELETON-2 | 单元测试：默认 4vp | `scroll.d.ts:1800` |
| AC-3.1 | R-6 | TASK-SKELETON-2 | 单元测试：默认 None | `scroll_pattern.h:48` |
| AC-3.2 | R-7 | TASK-SKELETON-2 | 单元测试：Spring | `scroll_spring_effect.cpp` |
| AC-3.3 | R-8 | TASK-SKELETON-2 | 单元测试：Fade | `scroll_fade_effect.cpp` |
| AC-3.4 | R-6 | TASK-SKELETON-2 | 单元测试：None | `scroll_pattern.h:48` |
| AC-4.1 | R-9 | TASK-SKELETON-2 | 单元测试：fadingEdge | `scrollable_pattern.cpp` |
| AC-4.2 | R-10 | TASK-SKELETON-2 | 单元测试：clipContent | `scrollable_pattern.cpp` |
| AC-4.3 | R-11 | TASK-SKELETON-2 | 单元测试：C-API 写入 | `node_scroll_modifier.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | scrollBar(Auto/On/Off) | 显隐策略；默认 Auto | BarState | AC-1.1~1.3 |
| R-2 | 行为 | scrollBarColor | 写滚动条颜色；@22 Resource | 颜色/资源 | AC-1.4, AC-1.5 |
| R-3 | 行为 | scrollBarWidth | 写宽度；默认 4vp；@26 Resource | 默认 4vp | AC-1.6, AC-1.7, AC-2.3 |
| R-4 | 行为 | scrollBarMargin | 边距生效 | @since 20 | AC-2.1 |
| R-5 | 行为 | autoAdjustScrollBarMargin | 自动避让 | @since 26 | AC-2.2 |
| R-6 | 行为 | edgeEffect(None 默认) | 无边缘效果 | 构造默认 NONE | AC-3.1, AC-3.4 |
| R-7 | 行为 | edgeEffect(Spring) | 弹簧回弹 | scroll_spring_effect | AC-3.2 |
| R-8 | 行为 | edgeEffect(Fade) | 渐隐；@11 options.alwaysEnabled | scroll_fade_effect | AC-3.3 |
| R-9 | 行为 | fadingEdge | 边缘渐隐渲染 | @since 14 | AC-4.1 |
| R-10 | 行为 | clipContent | 按 ContentClipMode/RectShape 裁剪 | @since 14 | AC-4.2 |
| R-11 | 行为 | C-API NODE_SCROLL_BAR_*/EDGE_EFFECT/FADING_EDGE/CLIP_CONTENT/BAR_MARGIN/BAR_HEIGHT | node_modifier 写基类字段 | — | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-3 滚动条显隐与样式 | 单元测试 | BarState/Color/Width |
| VM-2 | R-4~R-5 边距避让 | 单元测试 | margin/auto |
| VM-3 | R-6~R-8 边缘效果 | 单元测试 | None/Spring/Fade |
| VM-4 | R-9~R-11 渐隐裁剪与 C-API | 单元测试 | fadingEdge/clipContent/C-API |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `scrollBar(value)` | Public（@since 7） | `BarState` | `ScrollAttribute` | 无 | 滚动条显隐 | AC-1.1~1.3 |
| `scrollBarColor(color)` | Public（@since 7/22） | `Color\|number\|string` / `+Resource` | `ScrollAttribute` | 无 | 滚动条颜色 | AC-1.4, AC-1.5 |
| `scrollBarWidth(value)` | Public（@since 7/26） | `number\|string` / `+Resource` | `ScrollAttribute` | 无 | 滚动条宽度 | AC-1.6, AC-1.7 |
| `scrollBarMargin(margin)` | Public（@since 20，继承） | `ScrollBarMargin` | `ScrollAttribute` | 无 | 滚动条边距 | AC-2.1 |
| `autoAdjustScrollBarMargin(enable)` | Public（@since 26，继承） | `boolean\|undefined` | `ScrollAttribute` | 无 | 自动避让 | AC-2.2 |
| `edgeEffect(value, options?)` | Public（@since 7/11） | `EdgeEffect, EdgeEffectOptions?` | `ScrollAttribute` | 无 | 边缘效果 | AC-3.1~3.4 |
| `fadingEdge(enabled, options?)` | Public（@since 14，继承） | `Optional<boolean>, FadingEdgeOptions?` | `ScrollAttribute` | 无 | 渐隐边缘 | AC-4.1 |
| `clipContent(clip)` | Public（@since 14，继承） | `ContentClipMode\|RectShape` | `ScrollAttribute` | 无 | 内容裁剪 | AC-4.2 |
| C-API `NODE_SCROLL_BAR_*/EDGE_EFFECT/FADING_EDGE/CLIP_CONTENT/BAR_MARGIN/BAR_HEIGHT/AUTO_ADJUST_MARGIN` | Public | 属性枚举 | — | 无 | NDK 通道 | AC-4.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无废弃 | — |

## 接口规格

### 接口定义

**edgeEffect(value, options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ScrollAttribute::edgeEffect(edgeEffect: EdgeEffect, options?: EdgeEffectOptions): ScrollAttribute` |
| 返回值 | `ScrollAttribute` |
| 开放范围 | Public（@since 7；options @11） |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| edgeEffect | `EdgeEffect` | 是 | None | None/Spring/Fade |
| options | `EdgeEffectOptions` | 否 | `{alwaysEnabled:true}` | @since 11 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | None | 无效果 | AC-3.1 |
| 2 | Spring | 弹簧回弹 | AC-3.2 |
| 3 | Fade | 渐隐 | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** scrollBar/Color/Width/edgeEffect @7；edgeEffect options @11；fadingEdge/clipContent @14；scrollBarMargin @20；scrollBarColor Resource @22；scrollBarWidth/autoAdjust Resource @26
- **API 版本号策略:** 各属性标注 @since；Resource 重载门槛

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 基类提供滚动条 plumbing | ScrollablePattern SetScrollBar/UpdateScrollBarOffset/ScrollBarProxy | AC-1.x |
| 默认 edgeEffect None | 构造 EdgeEffect::NONE | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 渐隐/裁剪渲染分支单帧 | 单元测试 | `scrollable_pattern.cpp` |
| 内存 | 滚动条主题资源轻量 | 代码审查 | `inner/scroll_bar.h` |
| 可测试性 | 显隐/颜色/宽度/边缘可单测 | 单元测试 | TASK-SKELETON-2 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 滚动条样式不影响无障碍 | — |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 是 | 滚动条颜色随主题 | AC-1.4 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | @14/20/22/26 门槛 | AC-2.1, AC-1.5, AC-1.7, AC-2.2 |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（滚动条/边缘/渐隐/裁剪；几何在 Feat-01）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollablePattern 滚动条 plumbing 与 edgeEffect Spring/Fade 分支"
```

**关键文档:** `scroll.d.ts`、`scrollable_pattern.h/.cpp`、`scroll_edge_effect.h`、`design.md`
