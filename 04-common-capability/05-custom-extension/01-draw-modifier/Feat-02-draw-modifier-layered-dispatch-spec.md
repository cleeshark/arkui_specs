# 特性规格

> Func-04-05-01-Feat-02 分层绘制回调分发：固化 drawBehind/drawContent/drawFront/drawForeground/drawOverlay 分层回调的执行顺序、替换/叠加语义、Inner 回退、PaintWrapper 管线衔接、DrawContext 入参构造，以及与 ContentModifier 体系共存的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 分层绘制回调分发 (Layered Draw Callback Dispatch) |
| 特性编号 | Func-04-05-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | drawBehind/drawContent/drawFront 动态 @since 12、静态 @since 23；drawForeground 动态 @since 20、静态 @since 26.0.0；drawOverlay 动态/静态 @since 23；DrawContext 动态 @since 11/12、静态 @since 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/05-custom-extension/01-draw-modifier/design.md` | Baselined |

---

## 用户故事

### US-1: 分层绘制按固定顺序执行

**作为** 应用开发者,
**我想要** DrawModifier 的 5 个回调按 Behind→Content→Front→Foreground→Overlay 固定顺序执行,
**以便** 在组件绘制的不同阶段插入自定义逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN ExtensionHandler::OnDraw 执行 THEN 按 drawBehindFunc→drawContentFunc→drawFrontFunc 顺序调用（extension_handler.cpp:125-140） | 正常 |
| AC-1.2 | WHEN drawContentFunc 存在 THEN 替换原生内容绘制，不调用 InnerDraw；不存在 THEN 回退 InnerDraw 保留原生内容绘制（:131-135） | 正常 |
| AC-1.3 | WHEN drawBehindFunc 存在 THEN 在内容之前绘制（背景层），无回退（不存在则跳过）；drawFrontFunc 存在 THEN 在内容之后绘制，无回退 | 正常 |
| AC-1.4 | WHEN OnForegroundDraw 执行 THEN drawForegroundFunc 存在则调用替换原生前景，否则回退 InnerForegroundDraw（:116-123） | 正常 |
| AC-1.5 | WHEN OnOverlayDraw 执行 THEN drawOverlayFunc 存在则调用替换原生 overlay，否则回退 InnerOverlayDraw（:142-149） | 正常 |
| AC-1.6 | WHEN Draw/ForegroundDraw/OverlayDraw 入口被调用 THEN 各自复位 needRender_=false 后调对应 On* 方法（:52-68） | 正常 |

### US-2: PaintWrapper 管线衔接

**作为** 框架开发者,
**我想要** PaintWrapper 在 ExtensionHandler 存在时接管绘制回调装配,
**以便** DrawModifier 经由标准 RenderContext 绘制管线执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN extensionHandler_ 存在 THEN FlushContentDrawFunction/FlushForegroundDrawFunction/FlushOverlayDrawFunction 回调替换为构造 DrawingContext{canvas,width,height} 后调 ExtensionHandler::Draw/ForegroundDraw/OverlayDraw（paint_wrapper.cpp:197-225） | 正常 |
| AC-2.2 | WHEN extensionHandler_ 存在且原生 contentDraw/foregroundDraw/overlayDraw 存在 THEN 经 SetInnerDrawImpl/SetInnerForegroundDrawImpl/SetInnerOverlayDrawImpl 注入为 Inner 回退实现（:194-196, :205-207, :217-219） | 正常 |
| AC-2.3 | WHEN extensionHandler_ 不存在 THEN 走原 Flush*DrawFunction(contentDraw) 路径，不经 ExtensionHandler（:227-237） | 正常 |
| AC-2.4 | WHEN 构造 DrawingContext THEN width/height 取自 GetGeometryNode()->GetFrameSize()（:189-191） | 边界 |

### US-3: DrawContext 绘制上下文

**作为** 应用开发者,
**我想要** DrawContext 提供画布尺寸和 Canvas 对象,
**以便** 在回调内执行自定义绘制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 回调执行 THEN DrawContext.size 返回经 Px2VpWithCurrentDensity 转换为 vp 的宽高（js_view_abstract.cpp:12948-12949） | 正常 |
| AC-3.2 | WHEN 回调执行 THEN DrawContext.sizeInPixel 返回 px 单位宽高（:12953-12954） | 正常 |
| AC-3.3 | WHEN 回调执行 THEN DrawContext.canvas 经 JsCanvas::CreateJsCanvas 包装，并调用 SaveCanvas+ClipCanvas(width,height) 裁剪到组件 bounds（:12963-12968） | 正常 |
| AC-3.4 | WHEN 回调执行完毕 THEN 调用 RestoreCanvas+ResetCanvas 恢复画布状态（:12982-12984） | 恢复 |
| AC-3.5 | WHEN modifier 对象为空（IsEmpty）THEN 回调直接 return，不执行绘制（:12941-12943） | 异常 |

### US-4: 与 ContentModifier 体系共存

**作为** 应用开发者,
**我想要** DrawModifier 与 ContentModifier/OverlayModifier/ForegroundModifier 共存,
**以便** 在使用既有 Modifier 体系的同时叠加 DrawModifier 自定义回调。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 存在 contentModifier THEN PaintWrapper 跳过原生 contentDraw 的 InnerDrawImpl 注入（!contentModifier 守卫，paint_wrapper.cpp:192），但 ExtensionHandler::Draw 仍被调用 | 边界 |
| AC-4.2 | WHEN ContentModifier 经 SetExtensionHandler 绑定 THEN 其 onDraw 成为 InnerDraw 回退实现（modifier.cpp:31-37），与 DrawModifier.drawContentFunc 互为回退 | 正常 |
| AC-4.3 | WHEN foregroundModifier/overlayModifier 存在 THEN 同理以 !foregroundModifier/!overlayModifier 守卫跳过原生注入（:203, :215），Modifier.onDraw 经 SetInner*Impl 成为对应 Inner 回退 | 正常 |

### US-5: drawOverlay 越界能力（实际不能，doc 矛盾）

**作为** 应用开发者,
**我想要** drawOverlay 能在组件 bounds 之外绘制,
**以便** 绘制超出组件边界的装饰效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN drawOverlay 回调执行 THEN 画布经 ClipCanvas(width,height) 裁剪到组件 bounds（js_view_abstract.cpp:13023），实际不能绘制到组件外 | 正常 |
| AC-5.2 | WHEN SDK 文档声明 overlay "can draw outside the bounds"（common.d.ts:6307, common.static.d.ets:2802）与实际实现矛盾 THEN 实现裁剪画布不能越界，定义为风险 R-18 | 边界 |
| AC-5.3 | WHEN drawFront 执行 THEN 动态注释为 "after drawing associated Node"，静态扩展为 "after associated Node and its children"（common.d.ts:6276 vs common.static.d.ets:2777），以静态版为准 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1~R-5 | 已有实现 | 单测 | `extension_handler.cpp:52-149` |
| AC-2.1~2.4 | R-6~R-9 | 已有实现 | 单测 | `paint_wrapper.cpp:188-237` |
| AC-3.1~3.5 | R-10~R-14 | 已有实现 | 单测 | `js_view_abstract.cpp:12935-12988` |
| AC-4.1~4.3 | R-15~R-17 | 已有实现 | 单测 | `paint_wrapper.cpp:192-215`, `modifier.cpp:22-77` |
| AC-5.1~5.3 | R-18~R-19 | 已有实现 | XTS/契约 | `common.d.ts:6307/6276`, `common.static.d.ets:2777` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ExtensionHandler::OnDraw | 按 drawBehindFunc→drawContentFunc→drawFrontFunc 顺序；每个回调存在才调用 | content 段无回调回退 InnerDraw | AC-1.1 |
| R-2 | 行为 | drawContentFunc 存在 | 调用 drawContentFunc 替换原生内容；不调 InnerDraw | SDK 注释 "default drawContent method will be replaced if this method is set" | AC-1.2 |
| R-3 | 行为 | drawBehindFunc/drawFrontFunc 存在 | drawBehind 在 content 前、drawFront 在 content 后调用；不存在则跳过，无 Inner 回退 | 仅叠加，不替换原生 | AC-1.3 |
| R-4 | 行为 | OnForegroundDraw | drawForegroundFunc 存在则调用，否则回退 InnerForegroundDraw | 前景段替换语义 | AC-1.4 |
| R-5 | 行为 | OnOverlayDraw | drawOverlayFunc 存在则调用，否则回退 InnerOverlayDraw | overlay 段替换语义 | AC-1.5 |
| R-6 | 行为 | PaintWrapper 且 extensionHandler_ 存在 | Flush*DrawFunction 回调替换为构造 DrawingContext 后调 ExtensionHandler::Draw/ForegroundDraw/OverlayDraw | 三段各自独立装配 | AC-2.1 |
| R-7 | 行为 | extensionHandler_ 存在且原生 draw 存在 | 原生 contentDraw/foregroundDraw/overlayDraw 经 SetInner*Impl 注入为 Inner 回退 | 作为 DrawModifier 无回调时的回退 | AC-2.2 |
| R-8 | 行为 | extensionHandler_ 不存在 | 走原 Flush*DrawFunction(contentDraw) 直通路径 | 无 ExtensionHandler 介入 | AC-2.3 |
| R-9 | 边界 | 构造 DrawingContext | width/height 取自 GetGeometryNode()->GetFrameSize() | 像素值 | AC-2.4 |
| R-10 | 行为 | 回调执行 | DrawContext.size 返回 Px2VpWithCurrentDensity 转换后的 vp 宽高 | size getter 动态 @since 11 | AC-3.1 |
| R-11 | 行为 | 回调执行 | DrawContext.sizeInPixel 返回 px 宽高 | sizeInPixel getter 动态 @since 12 | AC-3.2 |
| R-12 | 行为 | 回调执行 | DrawContext.canvas 经 JsCanvas::CreateJsCanvas 包装 + SaveCanvas + ClipCanvas(width,height) | 画布裁剪到组件 bounds | AC-3.3 |
| R-13 | 恢复 | 回调执行完毕 | RestoreCanvas + ResetCanvas 恢复画布状态 | 保证画布状态不泄漏 | AC-3.4 |
| R-14 | 异常 | modifier 对象 IsEmpty | 回调直接 return，不执行绘制 | 对象已销毁 | AC-3.5 |
| R-15 | 边界 | 存在 contentModifier | !contentModifier 守卫跳过原生 contentDraw 的 InnerDrawImpl 注入，但 ExtensionHandler::Draw 仍调用 | Modifier 与 DrawModifier 共用 ExtensionHandler | AC-4.1 |
| R-16 | 行为 | ContentModifier::SetExtensionHandler | 把 InvalidateRenderImpl/SetContentChange 绑定，onDraw 经 SetInnerDrawImpl 成为 InnerDraw 回退（modifier.cpp:31-37） | Modifier.onDraw 即 InnerDraw | AC-4.2 |
| R-17 | 边界 | 存在 foregroundModifier/overlayModifier | 同理 !foregroundModifier/!overlayModifier 守卫；Modifier.onDraw 经 SetInner*Impl 成对应 Inner 回退 | foreground/overlay 段对称 | AC-4.3 |
| R-18 | 边界 | drawOverlay 实际不能绘制到组件外（doc 与实现矛盾） | SDK 文档声明 overlay "can draw outside the bounds"（common.d.ts:6307, common.static.d.ets:2802）可越界；但 GetDrawOverlayCallback 调 ClipCanvas(width,height)（js_view_abstract.cpp:13023）裁剪画布到 bounds，实际不能越界。doc 与实现矛盾，定义为风险（不修改实现） | AC-5.1, AC-5.2 |
| R-19 | 边界 | drawFront 语义版本差异 | 动态注释 "after drawing associated Node"，静态扩展 "after associated Node and its children"；以静态版为准 | 文档演进 | AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-3, AC-1.1~1.3 | 单测 | OnDraw 三层顺序与 content 替换/回退 |
| VM-2 | R-4, R-5, AC-1.4~1.5 | 单测 | OnForegroundDraw/OnOverlayDraw 替换与回退 |
| VM-3 | R-6~R-9, AC-2.1~2.4 | 单测 | PaintWrapper 衔接与 Inner 注入 |
| VM-4 | R-10~R-14, AC-3.1~3.5 | 单测 | DrawContext 三 getter 与画布裁剪/恢复 |
| VM-5 | R-15~R-17, AC-4.1~4.3 | 单测 | Modifier 共存守卫 |
| VM-6 | R-18~R-19, AC-5.1~5.3 | XTS/契约 | drawOverlay 不能越界(doc 矛盾风险)与 drawFront 语义 |
| VM-7 | 全量 | XTS/集成 | 端到端分层绘制渲染正确 |

---

## API 变更分析

> 补录已有 API，非新增。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `drawBehind?(drawContext: DrawContext): void` (动态 @since 12 / 静态 @since 23) | Public | drawContext: DrawContext | void | 无 | 在关联 Node 绘制前执行（背景层） | AC-1.1, AC-1.3 |
| `drawContent?(drawContext: DrawContext): void` (动态 @since 12 / 静态 @since 23) | Public | drawContext: DrawContext | void | 无 | 关联 Node 绘制时执行；设置后替换默认 drawContent | AC-1.2 |
| `drawFront?(drawContext: DrawContext): void` (动态 @since 12 / 静态 @since 23) | Public | drawContext: DrawContext | void | 无 | 关联 Node 及其子节点绘制后执行 | AC-1.1, AC-1.3, AC-5.3 |
| `drawForeground(drawContext: DrawContext): void` (动态 @since 20 / 静态 @since 26.0.0) | Public | drawContext: DrawContext | void | 无 | 关联 Node 及子节点绘制后执行，叠加在已渲染内容之上 | AC-1.4 |
| `drawOverlay(drawContext: DrawContext): void` (动态 @since 23 / 静态 @since 23) | Public | drawContext: DrawContext | void | 无 | overlay 层绘制，实际画布裁剪到 bounds 不能越界（与 SDK doc 矛盾，见风险 R-18） | AC-1.5, AC-5.1 |
| `class DrawContext` (动态 @since 11 / 静态 @since 23) | Public | — | — | 无 | 提供画布宽高与 Canvas | AC-3.1~3.3 |
| `get size(): Size` (动态 @since 11 / 静态 @since 23) | Public | 无 | Size | 无 | 画布宽高（vp） | AC-3.1 |
| `get sizeInPixel(): Size` (动态 @since 12 / 静态 @since 23) | Public | 无 | Size | 无 | 画布宽高（px） | AC-3.2 |
| `get canvas(): drawing.Canvas` (动态 @since 11 / 静态 @since 23) | Public | 无 | drawing.Canvas | 无 | 绘制用画布 | AC-3.3 |

### 变更/废弃 API

无变更或废弃。drawForeground 静态 API 26.0.0 补齐（动态侧 20 已有），属版本对齐。

> **d.ts 交叉验证：** 5 回调签名与 `@internal/component/ets/common.d.ts:6260/6273/6285/6299/6316`、`arkui/component/common.static.d.ets:2763/2774/2783/2795/2808` 一致。DrawContext 签名与 `arkui/Graphics.d.ts:81/93/105/117` 一致。分层顺序文档见 `common.static.d.ets:2800-2802`。

---

## 接口规格

### 接口定义

**drawBehind / drawContent / drawFront / drawForeground / drawOverlay**

| 属性 | 值 |
|------|-----|
| 函数签名 | `drawBehind?(drawContext: DrawContext): void` 等 5 个（动态可选带 `?`，静态不带 `?` 默认实现） |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1~1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| drawContext | DrawContext | 是 | 无（框架构造） | 框架在绘制时构造，非 null；size 为 vp 宽高，sizeInPixel 为 px 宽高，canvas 为 drawing.Canvas |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 绘制 content 段（OnDraw） | drawBehind→drawContent→drawFront 顺序；drawContent 无则 InnerDraw 回退 | AC-1.1~1.3 |
| 2 | 绘制 foreground 段 | drawForeground 有则替换，无则 InnerForegroundDraw | AC-1.4 |
| 3 | 绘制 overlay 段 | drawOverlay 有则替换，无则 InnerOverlayDraw | AC-1.5 |
| 4 | modifier 对象已销毁 | 回调 return 不绘制 | AC-3.5 |

---

## 兼容性声明

- **已有 API 行为变更:** 否。分层回调各自 @since 版本稳定。drawForeground 动态 20 / 静态 26.0.0、drawOverlay 动态/静态 23 为既有版本演进。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** drawBehind/Content/Front 动态 API 12、静态 API 23；drawForeground 动态 API 20、静态 API 26.0.0；drawOverlay 动态/静态 API 23；DrawContext 动态 API 11（size/canvas）、sizeInPixel API 12，静态 API 23
- **API 版本号策略:** 各回调独立 @since 标注；动态版本 drawBehind/Content/Front/invalidate 同为 12，drawForeground 后增于 20，drawOverlay 后增于 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 分层固定顺序 | Behind→Content→Front→Foreground→Overlay，不可重排 | AC-1.1 |
| drawContent 替换语义 | 设置即替换原生 content，无回调才回退 | AC-1.2 |
| Inner 互为回退 | DrawModifier 无回调时回退 Inner*Impl（原生 draw 或 Modifier.onDraw） | AC-1.2, AC-4.2 |
| 画布裁剪 | GetDrawCallback/GetDrawOverlayCallback 均 ClipCanvas 到 bounds | AC-3.3, AC-5.2 |
| Modifier 共用 ExtensionHandler | !contentModifier 等守卫，Modifier 与 DrawModifier 互为回退 | AC-4.1~4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 分层顺序同步绘制，无额外帧 | 单测 | extension_handler.cpp:125 |
| 内存 | DrawingContext 栈上构造，无堆分配 | 单测 | paint_wrapper.cpp:199 |
| 可靠性 | 画布状态 Save/Restore 配对，不泄漏 | 单测 | js_view_abstract.cpp:12967/12983 |
| 可测试性 | 各层回退可独立单测 | 单测 | extension_handler.cpp:116-149 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | size 取实时 FrameSize，折叠态自动更新 | 单测 | paint_wrapper.cpp:189 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 绘制层不影响无障碍语义 | — |
| 大字体 | 否 | DrawContext.size 以 vp 返回，跟随 density | AC-3.1 |
| 深色模式 | 否 | 回调绘制内容由开发者决定 | — |
| 多窗口/分屏 | 否 | 绘制管线与窗口无关 | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | drawForeground/drawOverlay 跨版本分阶段引入 | AC-1.4, AC-1.5 |
| 生态兼容 | 是 | DrawContext/DrawModifier @crossplatform | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（分层分发/管线衔接/DrawContext/Modifier 共存/overlay 不能越界风险；装配见 Feat-01、刷新见 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ExtensionHandler OnDraw/OnForegroundDraw/OnOverlayDraw 分层分发与 Inner 回退"
  - repo: "openharmony/arkui_ace_engine"
    query: "PaintWrapper ExtensionHandler 衔接与 ContentModifier 共存守卫"
  - repo: "openharmony/interface/sdk-js"
    query: "DrawModifier 5 回调与 DrawContext @since 版本及分层绘制顺序文档"
```

**关键文档：** design.md（DESIGN-Func-04-05-01），SDK `common.d.ts:6260-6316`、`Graphics.d.ts:81-117`
