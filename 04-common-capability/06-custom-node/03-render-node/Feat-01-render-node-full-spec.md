# 特性规格

> Func-04-06-03-Feat-01 RenderNode 全量规格：固化 ArkTS `RenderNode` 类全部公开 API 的行为规格。主角为 ArkTS RenderNode（`render_node.ts` + SDK `RenderNode.d.ts`/`.static.d.ets`）；C++ NG::RenderNode 仅为底层能力提供者，非规格对象。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | RenderNode 全量规格 |
| 特性编号 | Func-04-06-03-Feat-01 |
| 所属 Epic | 自定义节点能力 / RenderNode |
| 优先级 | P1 |
| 目标版本 | API 11（dynamic 起始）— API 26.0.0 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂（L2，40+ 公开 API，10 能力簇） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | constructor/dispose/isDisposed/label、size/position/frame/lengthMetricsUnit | API 11-20 |
| ADDED | backgroundColor/shadowColor/Offset/Alpha/Elevation/Radius | API 11 |
| ADDED | borderStyle/Width/Color/Radius、shapeMask/shapeClip、clipToFrame | API 11-12 |
| ADDED | pivot/scale/translation/rotation/transform、opacity/markNodeGroup | API 11-12 |
| ADDED | draw/invalidate、appendChild/insertChildAfter/removeChild/clearChildren/getChild/getFirstChild/getNextSibling/getPreviousSibling | API 11 |
| ADDED | backgroundBlur/contentBlur/foregroundBlur | API 26.0.0 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/03-render-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/RenderNode.d.ts` / `RenderNode.static.d.ets` | — |
| 图形类型 | `interface/sdk-js/api/arkui/Graphics.d.ts` | — |

## 用户故事

### US-1: 创建、释放与标识
**作为** 应用开发者，**我想要** 创建 RenderNode、设置调试标签、释放引用，
**以便** 配置节点属性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `new RenderNode()` THEN 返回实例，持有底层强引用；`size`/`position` 默认 `{0,0}`，`opacity` 默认 1，`backgroundColor` 默认 0x00000000 | 正常 |
| AC-1.2 | WHEN `dispose()` THEN 幂等释放底层强引用，此后 `nodePtr` 为空 | 正常 |
| AC-1.3 | WHEN `isDisposed()` THEN 返回是否已释放（dispose 后 true） | 正常 |
| AC-1.4 | WHEN `set label("x")`/`get label()` THEN 设置/返回 inspector 标签（默认 `""`，仅 `new` 创建的节点显示） | 正常 |

### US-2: 帧与几何
**作为** 应用开发者，**我想要** 设置 RenderNode 的尺寸、位置、帧与单位，
**以便** 配置节点属性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `set size(s)`/`get size()` THEN 设置/返回尺寸（默认 `{0,0}`） | 正常 |
| AC-2.2 | WHEN `set position(p)`/`get position()` THEN 设置/返回位置（默认 `{0,0}`） | 正常 |
| AC-2.3 | WHEN `set frame(f)` THEN 同时设 size+position；后设置的 frame/position/size 胜出 | 正常 |
| AC-2.4 | WHEN `set lengthMetricsUnit(unit)` THEN 设置单位上下文（默认 DEFAULT），影响后续 length 型属性（size/position/borderWidth/borderRadius/shadowOffset）的 vp/px 解释 | 正常 |

### US-3: 背景色与阴影
**作为** 应用开发者，**我想要** 设置背景色与阴影，
**以便** 配置节点属性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `set backgroundColor(ARGB)` THEN 设置背景色（默认 0x00000000） | 正常 |
| AC-3.2 | WHEN `set shadowColor/Offset/Alpha/Elevation/Radius` THEN 设置阴影各属性（默认 color 0x00000000、offset {0,0}、alpha 0、elevation 0、radius 0） | 正常 |
| AC-3.3 | WHEN 设 shadowAlpha THEN 阴影 alpha 受 shadowAlpha 影响 | 边界 |

### US-4: 边框
**作为** 应用开发者，**我想要** 设置四边边框样式/宽度/颜色/圆角，
**以便** 配置节点属性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN `set borderStyle/Width/Color/Radius` THEN 设置四边（Edges，T/R/B/L 顺序）；默认 style NONE、width 0、color 0xFF000000、radius 0 | 正常 |
| AC-4.2 | WHEN borderWidth/borderRadius 为 vp 单位 THEN 受 lengthMetricsUnit 影响 | 边界 |

### US-5: 形状遮罩与裁剪
**作为** 应用开发者，**我想要** 设置遮罩形状、裁剪形状、帧裁剪，
**以便** 配置节点属性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN `set shapeMask(mask)` THEN 设置遮罩形状（rect/roundRect/circle/oval/path）+fillColor/strokeColor/strokeWidth | 正常 |
| AC-5.2 | WHEN `set shapeClip(clip)` THEN 设置裁剪形状（同上形状，无 fill/stroke） | 正常 |
| AC-5.3 | WHEN `set clipToFrame(bool)` THEN 设置是否裁剪至 frame（默认 true；API12 前默认 false） | 正常 |

### US-6: 变换
**作为** 应用开发者，**我想要** 设置锚点、缩放、平移、旋转、矩阵变换，
**以便** 配置节点属性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN `set pivot/scale/translation/rotation` THEN 设置变换属性（默认 pivot {0.5,0.5}、scale {1,1}、translation {0,0}、rotation {0,0,0}） | 正常 |
| AC-6.2 | WHEN `set transform(Matrix4)` THEN 设置 4×4 矩阵（默认单位矩阵）；clamp 至 16 元素 | 正常 |

### US-7: 透明度与绘制优先级
**作为** 应用开发者，**我想要** 设置透明度与节点组绘制优先级，
**以便** 配置节点属性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-7.1 | WHEN `set opacity(v)` THEN 设置透明度（<0→0, >1→1；默认 1） | 正常 |
| AC-7.2 | WHEN `set markNodeGroup(true)` THEN 启用节点组绘制优先级（默认 false） | 正常 |

### US-8: 自定义绘制与重绘
**作为** 应用开发者，**我想要** 重写 draw 自定义绘制并触发重绘，
**以便** 驱动对应行为。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-8.1 | WHEN 重写 `draw(context)` THEN 绘制时回调获 DrawContext（size vp / sizeInPixel px / canvas） | 正常 |
| AC-8.2 | WHEN `invalidate()` THEN 触发重绘 | 正常 |

### US-9: 子节点树
**作为** 应用开发者，**我想要** 管理子 RenderNode 树，
**以便** 管理节点树。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-9.1 | WHEN `appendChild(node)`/`insertChildAfter(child, sibling)` THEN 添加子节点；sibling null 插为首子 | 正常 |
| AC-9.2 | WHEN child 已 adopt THEN 抛 BusinessError(100025, "FrameNode cannot be adopted") | 异常 |
| AC-9.3 | WHEN `removeChild(node)`/`clearChildren()` THEN 移除子节点 | 正常 |
| AC-9.4 | WHEN `getChild(index)`/`getFirstChild()`/`getNextSibling()`/`getPreviousSibling()` THEN 返回对应子节点；无则 null | 正常 |

### US-10: 模糊效果（API26）
**作为** 应用开发者，**我想要** 设置背景/内容/前景模糊，
**以便** 配置节点属性。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-10.1 | WHEN `set backgroundBlur/contentBlur/foregroundBlur` THEN 设置模糊效果（radius + grayscale 可选）；undefined 移除效果 | 正常 |
| AC-10.2 | WHEN grayscale 范围 [0,127] | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2,R-3 | 单测 render_node | render_node.ts; bridge CreateRenderNode |
| AC-2.1..2.4 | R-4,R-5,R-6 | 单测 | render_node.ts SetSize/Position/Frame |
| AC-3.1..3.3 | R-7,R-8 | 单测 | render_node.ts SetShadow* |
| AC-4.1..4.2 | R-9 | 单测 | render_node.ts SetBorder* |
| AC-5.1..5.3 | R-10,R-11,R-12 | 单测 | render_node.ts shapeMask/Clip 分支 |
| AC-6.1..6.2 | R-13,R-14 | 单测 | render_node.ts SetRotation/Scale/Transform |
| AC-7.1..7.2 | R-15,R-16 | 单测 | render_node.ts SetOpacity/MarkNodeGroup |
| AC-8.1..8.2 | R-17,R-18 | 单测 | bridge FireDrawCallback; render_node.ts invalidate |
| AC-9.1..9.4 | R-19,R-20,R-21 | 单测 | render_node.ts childrenList; bridge AppendChild |
| AC-10.1..10.2 | R-22 | 单测 | render_node.ts SetBackgroundBlur 等 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `new RenderNode()` | 返回实例，持有底层强引用；属性取默认值 | — | AC-1.1 |
| R-2 | 行为 | `dispose()` | 幂等释放底层强引用 | 此后 nodePtr 空 | AC-1.2 |
| R-3 | 行为 | `isDisposed()` | 返回是否已释放 | — | AC-1.3 |
| R-4 | 行为 | `set size/position` | 设置尺寸/位置（默认 {0,0}） | getter 返回缓存值 | AC-2.1,2.2 |
| R-5 | 行为 | `set frame` | 同时设 size+position | 后设的 frame/position/size 胜出 | AC-2.3 |
| R-6 | 行为 | `set lengthMetricsUnit` | 设置单位上下文（默认 DEFAULT） | 仅本地缓存，影响后续 length 型属性 | AC-2.4 |
| R-7 | 行为 | `set backgroundColor` | 设置背景色（默认 0x00000000） | ARGB | AC-3.1 |
| R-8 | 行为 | `set shadow*` | 设置阴影 color/offset/alpha/elevation/radius | 默认均 0/{0,0}；shadowAlpha 影响 alpha | AC-3.2,3.3 |
| R-9 | 行为 | `set borderStyle/Width/Color/Radius` | 设置四边（Edges，T/R/B/L） | 默认 NONE/0/0xFF000000/0；width/radius 受单位影响 | AC-4.1,4.2 |
| R-10 | 行为 | `set shapeMask` | 设置遮罩形状+fillColor/strokeColor/strokeWidth | rect/roundRect/circle/oval/path 分支 | AC-5.1 |
| R-11 | 行为 | `set shapeClip` | 设置裁剪形状（无 fill/stroke） | 同形状分支 | AC-5.2 |
| R-12 | 行为 | `set clipToFrame` | 设置帧裁剪（默认 true；API12 前 false） | 版本差异 | AC-5.3 |
| R-13 | 行为 | `set pivot/scale/translation/rotation` | 设置变换属性 | 默认 {0.5,0.5}/{1,1}/{0,0}/{0,0,0} | AC-6.1 |
| R-14 | 行为 | `set transform` | 设置 4×4 矩阵 | 默认单位矩阵；clamp 16 元素 | AC-6.2 |
| R-15 | 行为 | `set opacity` | 设置透明度 | <0→0,>1→1；默认 1 | AC-7.1 |
| R-16 | 行为 | `set markNodeGroup` | 启用节点组绘制优先级 | 默认 false | AC-7.2 |
| R-17 | 行为 | 重写 `draw(context)` | 绘制时回调获 DrawContext（size vp/sizeInPixel px/canvas） | canvas 为临时命令录制 | AC-8.1 |
| R-18 | 行为 | `invalidate()` | 触发重绘 | — | AC-8.2 |
| R-19 | 行为 | `appendChild`/`insertChildAfter` | 添加子节点；sibling null 插首子 | — | AC-9.1 |
| R-20 | 异常 | child 已 adopt | 抛 100025 "FrameNode cannot be adopted" | — | AC-9.2 |
| R-21 | 行为 | `removeChild`/`clearChildren`/`getChild`/`getFirstChild`/`getNextSibling`/`getPreviousSibling` | 移除/查询子节点；无则 null | getter 操作 TS childrenList | AC-9.3,9.4 |
| R-22 | 行为 | `set backgroundBlur/contentBlur/foregroundBlur` | 设置模糊（radius+grayscale）；undefined 移除 | API26；grayscale [0,127] | AC-10.1,10.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-3 创建释放 | 单测 render_node | 默认值、幂等 dispose |
| VM-2 | R-4..R-6 帧几何 | 单测 | frame 优先级、单位上下文 |
| VM-3 | R-7..R-8 背景阴影 | 单测 | 默认值、shadowAlpha |
| VM-4 | R-9 边框 | 单测 | Edges 四边、单位影响 |
| VM-5 | R-10..R-12 遮罩裁剪 | 单测 | 形状分支、clipToFrame 版本 |
| VM-6 | R-13..R-14 变换 | 单测 | 默认值、矩阵 clamp |
| VM-7 | R-15..R-16 透明度/组 | 单测 | clamp [0,1] |
| VM-8 | R-17..R-18 绘制 | 单测 | DrawContext、invalidate |
| VM-9 | R-19..R-21 子树 | 单测 | 100025、getter 缓存 |
| VM-10 | R-22 模糊 | 单测 | API26、grayscale 范围 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| constructor() | Public | — | RenderNode | — | 创建 | AC-1 |
| dispose() | Public | — | void | — | 释放 | AC-1 |
| isDisposed() | Public | — | boolean | — | 释放状态 | AC-1 |
| label (get/set) | Public | string | string | — | inspector 标签 | AC-1 |
| size/position/frame (get/set) | Public | Size/Position/Frame | 同 | — | 帧几何 | AC-2 |
| lengthMetricsUnit (get/set) | Public | LengthMetricsUnit | 同 | — | 单位上下文 | AC-2 |
| backgroundColor (get/set) | Public | number(ARGB) | number | — | 背景色 | AC-3 |
| shadowColor/Offset/Alpha/Elevation/Radius (get/set) | Public | number/Offset | 同 | — | 阴影 | AC-3 |
| borderStyle/Width/Color/Radius (get/set) | Public | Edges\<T\> | 同 | — | 边框 | AC-4 |
| shapeMask/shapeClip (get/set) | Public | ShapeMask/ShapeClip | 同 | — | 形状遮罩/裁剪 | AC-5 |
| clipToFrame (get/set) | Public | boolean | boolean | — | 帧裁剪 | AC-5 |
| pivot/scale/translation/rotation (get/set) | Public | Pivot/Scale/Translation/Rotation | 同 | — | 变换 | AC-6 |
| transform (get/set) | Public | Matrix4 | Matrix4 | — | 矩阵变换 | AC-6 |
| opacity (get/set) | Public | number | number | — | 透明度 | AC-7 |
| markNodeGroup (get/set) | Public | boolean | boolean | — | 绘制优先级 | AC-7 |
| draw(context) | Public | DrawContext | void | — | 自定义绘制 | AC-8 |
| invalidate() | Public | — | void | — | 重绘 | AC-8 |
| appendChild/insertChildAfter/removeChild/clearChildren | Public | RenderNode | void | 100025 | 子树操作 | AC-9 |
| getChild/getFirstChild/getNextSibling/getPreviousSibling | Public | number | RenderNode\|null | — | 子树查询 | AC-9 |
| backgroundBlur/contentBlur/foregroundBlur (get/set) | Public | Blur\|undefined | Blur | — | 模糊(API26) | AC-10 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**创建/释放/标识**

| 属性 | 值 |
|------|-----|
| 函数签名 | `constructor()`; `dispose(): void`; `isDisposed(): boolean`; `label: string` (get/set) |
| 返回值 | RenderNode / void / boolean / string |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | new RenderNode() | 返回实例，属性默认值 | AC-1.1 |
| 2 | dispose() | 幂等释放 | AC-1.2 |
| 3 | set label | 设置 inspector 标签 | AC-1.4 |

**帧几何/背景阴影/边框/遮罩裁剪/变换/透明度/绘制/子树/模糊**：行为场景表见规则定义（R-4..R-22），每个 API 的参数约束与默认值见上方 API 变更分析与规则定义。

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 11（dynamic）；isDisposed API 20；border*/shapeMask/shapeClip/markNodeGroup API 12；静态 @since 23；模糊 API 26.0.0。
- **API 版本号策略:** 逐 API @since；clipToFrame 默认随 apiTargetVersion（API12 前后差异）；shadowRadius API26 默认哨兵 -1。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| getter 返回缓存非 native 实时 | getter 返回 TS 缓存值；与 native 一致（setter 同步） | render_node.ts |
| frame/position/size 后设胜出 | 文档明示顺序 | RenderNode.d.ts |
| clipToFrame 默认随版本 | API12 前 false，后 true | render_node.ts apiTargetVersion |
| shadowRadius API26 哨兵 -1 | 默认值版本差异 | RenderNode.d.ts |
| 无公开事件/动画 API | 事件在 BaseNode 不暴露；动画经属性隐式 | RenderNode.d.ts |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| getter 缓存 | getter 返回 TS 缓存，非 native 往返 | AC-2..7 |
| 单位上下文 | lengthMetricsUnit 影响后续 length 型属性 | AC-2.4,4.2 |
| draw 临时 canvas | canvas 为命令录制，save/clip/restore 包裹 | AC-8.1 |
| adopt 错误 | child 已 adopt 抛 100025 | AC-9.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | getter 缓存减少跨语言开销 | 单测 | render_node.ts |
| 可靠性 | dispose 幂等 | 单测 | render_node.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | API11-26 演进，模糊 API26、isDisposed API20 | AC-1.3,10 |

## 行为场景

```gherkin
Feature: RenderNode 全量规格
  Scenario: 默认值
    Given new RenderNode()
    Then size=={0,0}, opacity==1, backgroundColor==0x00000000

  Scenario: appendChild 已 adopt child
    Given child 已被 adopt
    When 调用 parent.appendChild(child)
    Then 抛出 BusinessError(100025)

  Scenario: opacity clamp
    When 调用 setOpacity(-1) 与 setOpacity(2)
    Then 实际值为 0 与 1
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（RenderNode 全部公开 API；无事件/显式动画）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "render_node.ts 属性 setter 缓存+下发 native 模式与 getter 缓存返回"
  - repo: "openharmony/arkui_ace_engine"
    query: "RenderNodeBridge FireDrawCallback 构建 DrawContext(size/sizeInPixel/canvas) save/clip/restore"
  - repo: "openharmony/arkui_ace_engine"
    query: "render_node.ts shapeMask/shapeClip 形状分支(rect/roundRect/circle/oval/path) 与 native setRectMask 等"
```
