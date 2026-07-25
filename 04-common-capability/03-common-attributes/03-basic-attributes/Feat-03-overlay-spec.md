# 特性规格

> Func-04-03-03-Feat-03 浮层属性：固化 overlay(string/CustomBuilder/NodeHandle) 及 OverlayOptions 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 浮层 (Overlay) |
| 特性编号 | Func-04-03-03-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7 起支持，API 12/21 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | overlay 行为规格全文 | 补录 overlay API 从 API 7 至 API 21 的完整行为规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/03-basic-attributes/design.md` | Draft |

---

## 用户故事

### US-1: 设置文本浮层

**作为** 应用开发者,
**我想要** 通过 `.overlay(value: string)` 在组件上方叠加一段纯文本浮层,
**以便** 在组件表面显示简短提示或标注信息。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.overlay("提示文本")` THEN 在宿主组件上方渲染一段纯文本浮层，文本内容为 "提示文本" | 正常 |
| AC-1.2 | WHEN 调用 `.overlay("提示文本", { alignment: Alignment.TopLeft })` THEN 浮层文本定位在宿主组件边框的 TopLeft 对齐点 | 正常 |
| AC-1.3 | WHEN 调用 `.overlay(undefined)` THEN 清除已设置的 overlay，宿主组件恢复为无浮层状态 | 异常 |
| AC-1.4 | WHEN 文本浮层使用 RenderContext 的 OverlayText 属性存储 THEN 浮层文本通过 OverlayTextModifier 绘制在宿主组件 RenderNode 上 | 正常 |

### US-2: 设置 CustomBuilder 浮层并对齐定位

**作为** 应用开发者,
**我想要** 通过 `.overlay(value: CustomBuilder, options?: OverlayOptions)` 在组件上方叠加由 CustomBuilder 构建的富内容浮层，并指定对齐方式,
**以便** 在组件表面叠加自定义 UI 内容并精确控制其位置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.overlay(builderFn, { alignment: Alignment.Center })` THEN CustomBuilder 构建的 FrameNode 以 Center 对齐方式挂载为宿主组件的 overlayNode | 正常 |
| AC-2.2 | WHEN overlay 值为 CustomBuilder 类型 THEN overlayNode 作为宿主 FrameNode 的 overlayNode_ 子节点挂载，SetParent 指向宿主节点 | 正常 |
| AC-2.3 | WHEN overlay 值为 CustomBuilder 类型 THEN overlayNode 的 RenderContext ZIndex 被设置为 INT32_MAX，确保浮层内容在宿主自身内容之上绘制 | 正常 |
| AC-2.4 | WHEN overlay 值为 CustomBuilder 类型 THEN overlayNode 的 FocusHub 设置为不可聚焦（SetFocusable(false)） | 正常 |
| AC-2.5 | WHEN overlay 值为 CustomBuilder 类型 且 builderFn 返回非 FrameNode 的 UINode THEN 自动包裹为 StackFrameNode（V2::STACK_ETS_TAG），再将 Stack 节点作为 overlayNode 挂载 | 正常 |
| AC-2.6 | WHEN 不指定 alignment THEN 默认对齐方式为 Alignment.TopLeft（ArkTS 层默认 TopStart） | 边界 |

### US-3: 设置浮层偏移量

**作为** 应用开发者,
**我想要** 通过 OverlayOptions 的 offset 参数微调浮层的像素偏移位置,
**以便** 在对齐锚点基础上进一步精确控制浮层位移。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.overlay(value, { alignment: Alignment.Center, offset: { x: 10, y: 20 } })` THEN 浮层先按 Center 对齐锚点定位，再向右偏移 10vp、向下偏移 20vp | 正常 |
| AC-3.2 | WHEN offset.x 或 offset.y 为负数 THEN 浮层向相反方向偏移（x 负值向左，y 负值向上） | 边界 |
| AC-3.3 | WHEN offset.x 或 offset.y 为 0 THEN 无额外偏移，等同于仅按 alignment 定位 | 正常 |
| AC-3.4 | WHEN 不指定 offset THEN offset.x 和 offset.y 默认为 0 | 边界 |
| AC-3.5 | WHEN layoutDirection 为 RTL THEN overlay 的 offsetX 在布局计算中被取反（-offsetX），实现 RTL 适配 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1 | R-1, R-2 | — | UT：overlay string 渲染 | view_abstract.cpp:7006 |
| AC-1.2 | R-3 | — | UT：alignment 定位 | view_abstract.cpp:7111 |
| AC-1.3 | R-6 | — | UT：undefined 清除 | js_view_abstract.cpp:3189 |
| AC-1.4 | R-2 | — | 代码检查 | rosen_render_context.cpp:997-998 |
| AC-2.1 | R-3 | — | UT：CustomBuilder overlay | view_abstract.cpp:7014-7041 |
| AC-2.2 | R-1 | — | 代码检查 | view_abstract.cpp:7103-7104 |
| AC-2.3 | R-2 | — | 代码检查 | view_abstract.cpp:7116 |
| AC-2.4 | R-1 | — | 代码检查 | view_abstract.cpp:7080 |
| AC-2.5 | R-1 | — | 代码检查 | view_abstract.cpp:7030-7035 |
| AC-2.6 | R-3 | — | UT：默认 alignment | native_node.h:952 |
| AC-3.1 | R-4 | — | UT：offset 位移 | frame_node.cpp:6835-6856 |
| AC-3.2 | R-4 | — | UT：负数 offset | frame_node.cpp:6847 |
| AC-3.3 | R-4 | — | UT：零 offset | — |
| AC-3.4 | R-4 | — | 代码检查 | view_abstract.cpp:7111 |
| AC-3.5 | R-3 | — | 代码检查 | frame_node.cpp:6844-6846 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 overlay(CustomBuilder/NodeHandle) 设置浮层 | overlayNode 作为宿主 FrameNode 的 overlayNode_ 子节点挂载（SetParent→宿主节点），overlayNode 的 MeasureType 为 MATCH_PARENT，layoutProperty.SetIsOverlayNode(true) | overlayNode_ 是 FrameNode 上的单一 RefPtr 字段，同一宿主仅持有一个 overlayNode | AC-2.2, AC-2.4, AC-2.5 |
| R-2 | 行为 | overlay 内容绘制顺序 | 文本浮层：宿主组件自身内容绘制完成后，通过 OverlayTextModifier 在 RenderNode 上追加绘制文本；CustomBuilder 浮层：overlayNode 的 ZIndex 为 INT32_MAX，在渲染树中排列于宿主子节点列表尾部，保证浮层绘制在宿主内容之上 | ZIndex=INT32_MAX 为引擎内部硬编码值，开发者不可通过 overlay API 修改 | AC-1.4, AC-2.3 |
| R-3 | 行为 | overlay alignment 定位 | alignment 决定 overlayNode 相对宿主组件边框的对齐锚点，通过 Alignment::GetAlignPosition / GetAlignPositionWithDirection 计算偏移；未指定时默认为 Alignment.TopLeft（ArkTS 层映射为 TopStart） | alignment 值域：TopLeft/TopCenter/TopRight/CenterLeft/Center/CenterRight/BottomLeft/BottomCenter/BottomRight（共 9 种） | AC-1.2, AC-2.1, AC-2.6, AC-3.5 |
| R-4 | 边界 | overlay offset 偏移量 | offset.x 和 offset.y 为 Dimension 类型，在对齐锚点位置基础上叠加像素偏移；RTL 方向下 offsetX 取反；未指定时默认为 0 | offset 支持 vp 单位（Dimension），x/y 为 0 时无额外偏移，负值向反方向偏移 | AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5 |
| R-5 | 行为 | overlay 多次调用行为 | 同一宿主组件上多次调用 overlay() 时，overlayNode_ 单一指针被覆盖为新值，旧 overlayNode 被释放（最后一次调用生效） | overlayNode_ 是 RefPtr<FrameNode> 单值字段，不支持叠加多个 overlay | AC-1.3 |
| R-6 | 边界 | overlay(undefined) 重置行为 | 调用 overlay(undefined) 时，引擎传入 OverlayType::RESET，清除 OverlayText RenderContext 属性并置 overlayNode_ 为 nullptr | 重置后宿主组件恢复为无浮层状态，下次帧调度不再 Measure/Layout overlayNode | AC-1.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | R-1 overlayNode 挂载机制 | 代码检查 + Inspector 验证 | overlayNode_ 指向宿主节点，SetParent 正确 |
| VM-2 | R-2 overlay 绘制顺序 | 渲染结果对比 | overlayNode 在宿主内容上方 |
| VM-3 | R-3 alignment 定位 | 9 种 alignment 值遍历 UT | 每种 alignment 位置与预期一致 |
| VM-4 | R-4 offset 偏移 | 正数/负数/零值 offset UT | 偏移量按 vp 转换为 px 后叠加 |
| VM-5 | R-5 多次调用覆盖 | 两次 overlay() 调用 UT | 第二次调用结果可见，第一次 overlay 被清除 |
| VM-6 | R-6 undefined 重置 | overlay(undefined) UT | overlayNode_ 为 nullptr，无浮层渲染 |

---

## API 变更分析

N/A，已有能力补录，API 行为无变化。

### 新增 API

N/A

### 变更/废弃 API

N/A

---

## 接口规格

### 接口定义

**overlay (ArkTS)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `overlay(value: string | CustomBuilder, options?: OverlayOptions)` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-2.1, AC-3.1 |

**OverlayOptions**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OverlayOptions { alignment?: Alignment, offset?: { x?: number, y?: number } }` |
| 返回值 | N/A（结构体） |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.2, AC-3.1 |

**NODE_OVERLAY (C API)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `NODE_OVERLAY` (ArkUI_NodeAttributeType enum value) |
| 返回范围 | @since 12 (string overlay); @since 21 (NodeHandle overlay 扩展版) |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value (string) | string | 是（string 形式必填） | — | overlay 文本内容；undefined 触发 RESET 行为 |
| value (CustomBuilder) | CustomBuilder | 是（builder 形式必填） | — | CustomBuilder 函数返回 UINode；若非 FrameNode 则被自动包裹为 Stack |
| value (NodeHandle) | ArkUI_NodeHandle | 否 | nullptr | C API @since 21；与 .string 冲突时 .string 优先级更高 |
| alignment | Alignment | 否 | TopLeft (ArkTS: TopStart) | 9 种对齐值：TopLeft/TopCenter/TopRight/CenterLeft/Center/CenterRight/BottomLeft/BottomCenter/BottomRight |
| offset.x | number (vp) | 否 | 0 | 支持正数/负数/0；RTL 方向下取反 |
| offset.y | number (vp) | 否 | 0 | 支持正数/负数/0 |
| direction | ArkUI_Direction | 否 | LTR | C API @since 21；对应 ArkTS overlay 的 layoutDirection 参数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 overlay("text") 不带 options | overlayNode 以 TopLeft 对齐、零偏移挂载到宿主 | AC-1.1, AC-2.6, AC-3.4 |
| 2 | 调用 overlay("text", { alignment: Alignment.Center }) | overlayNode 以 Center 对齐、零偏移挂载 | AC-1.2 |
| 3 | 调用 overlay(builderFn, { alignment: Alignment.BottomRight, offset: { x: 5, y: -3 } }) | overlayNode 以 BottomRight 对齐锚点定位，叠加 x=5vp 右偏、y=-3vp 上偏 | AC-2.1, AC-3.1, AC-3.2 |
| 4 | 调用 overlay(undefined) | 清除 OverlayText 属性，overlayNode_ = nullptr，无浮层渲染 | AC-1.3 |
| 5 | 连续调用 overlay("A") 再 overlay("B") | overlayNode_ 指向 "B" 的 overlayNode，"A" 的 overlay 被释放 | AC-1.3 |
| 6 | CustomBuilder 返回非 FrameNode UINode | 自动包裹为 StackFrameNode 再挂载 | AC-2.5 |
| 7 | C API NODE_OVERLAY 设定 .string + .object(NodeHandle) | .string 优先级高于 .object，按 string overlay 处理 | — |

---

## 兼容性声明

- **已有 API 行为变更:** 否，补录规格，无行为变更
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:**
  - overlay(value: string): @since 7
  - overlay(value: CustomBuilder): @since 12
  - NODE_OVERLAY (C API string 版): @since 12
  - NODE_OVERLAY (C API NodeHandle 扩展版, 含 direction 参数): @since 21

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| overlayNode_ 单值字段 | FrameNode.overlayNode_ 为 RefPtr<FrameNode> 单值字段，同一宿主最多持有一个 overlayNode | AC-1.3, AC-2.2 |
| ZIndex=INT32_MAX 硬编码 | CustomBuilder overlayNode 的 RenderContext ZIndex 固定为 INT32_MAX，不可通过 overlay API 自定义 | AC-2.3 |
| overlayNode 不可聚焦 | overlayNode 的 FocusHub.SetFocusable(false) 为硬编码行为 | AC-2.4 |
| text overlay 与 builder overlay 互斥 | 同一宿主上 overlay(string) 设置 OverlayText RenderContext 属性，overlay(CustomBuilder) 设置 overlayNode_；两者分别独立但 overlayNode_ 单值字段导致后设覆盖前设 | AC-1.3 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | overlay 设置不引起额外帧延迟 | UT + 渲染时序分析 | — |
| 功耗 | 无显著功耗影响 | — | — |
| 内存 | overlayNode_ 单值指针，无额外内存池 | 代码检查 | frame_node.h:1952 |
| 安全 | 无安全风险 | — | — |
| 可靠性 | overlay(undefined) 正确清除浮层 | UT | js_view_abstract.cpp:3189 |
| 可测试性 | 9 种 alignment + 3 种 offset 状态均可独立验证 | UT | — |
| 自动化维测 | Inspector 输出 overlay 属性 | Inspector 功能 | overlay_property.h:45-62 |
| 定界定位 | overlayNode_ 字段可通过 GetOverlayNode() 获取 | 代码检查 | frame_node.h:986-989 |

---

## 多设备适配声明

无差异。overlay 行为在手机、平板、折叠屏上一致，alignment 和 offset 按 vp 单位计算，自适应屏幕密度。

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|---------|
| 无障碍 | 是 | overlayNode 不参与无障碍焦点获取（SetFocusable(false)） | AC-2.4 |
| 大字体 | 是 | text overlay 文本受系统字体缩放影响 | — |
| 深色模式 | 是 | text overlay 文本颜色跟随系统深色模式 | — |
| 多窗口/分屏 | 否 | overlay 行为不受多窗口影响 | — |
| 多用户 | 否 | overlay 行为不受多用户影响 | — |
| 版本升级 | 是 | API 7→12 引入 CustomBuilder，API 12→21 引入 NodeHandle/direction 扩展 | — |
| 生态兼容 | 是 | C API NODE_OVERLAY 与 ArkTS overlay 行为一致 | — |

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（overlay 挂载机制、对齐定位、偏移量、多次调用行为均已覆盖）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "overlay 属性实现：OverlayOptions 存储、overlayNode_ 挂载机制、alignment 定位算法、offset 偏移计算"
  - repo: "openharmony/ace_engine"
    query: "NODE_OVERLAY C API：string/builder/NodeHandle 三种 overlay 模式及 direction 参数"
```

**关键文档：**

- ArkTS overlay API: `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:3187` (JsOverlay)
- overlay 属性存储: `frameworks/core/components_ng/property/overlay_property.h:30` (OverlayOptions struct)
- overlayNode 挂载: `frameworks/core/components_ng/base/view_abstract.cpp:7093` (AddOverlayToFrameNode)
- overlay 布局: `frameworks/core/components_ng/base/frame_node.cpp:6835` (LayoutOverlay)
- overlay 渲染: `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:997` (PaintOverlayText)
- C API NODE_OVERLAY: `interfaces/native/native_node.h:946-1003`
- C API style modifier: `interfaces/native/node/style_modifier.cpp:3376` (SetOverlay)
- Alignment 定义: `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:3228` (ParseAlignment)
