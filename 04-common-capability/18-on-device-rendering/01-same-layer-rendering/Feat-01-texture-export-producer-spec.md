# 特性规格

> Func-04-18-01-Feat-01 同层渲染纹理生产者（ArkUI 子树纹理导出）：固化公开触发入口 `BuilderNode(uiContext, { surfaceId, type: NodeRenderType.RENDER_TYPE_TEXTURE })`（`interface/sdk-js/api/arkui/BuilderNode.d.ts` `@since 11 dynamic` / `@atomicservice 12`，`NodeRenderType{DISPLAY=0,TEXTURE=1}`、`RenderOptions{selfIdealSize?,type?(默认 DISPLAY),surfaceId?(默认 ""，仅 type=TEXTURE 生效)}`）、ArkTS 桥 `JSBaseNode`（`js_base_node.cpp`）与静态 BuilderNode Native 实现 `builder_node_ops_accessor.cpp` 两条入口在 build 时置 `ViewStackProcessor::SetIsExportTexture(true)` 使子树 RSNode 以 `isTextureExportNode=true` 创建、并在 build 后将消费者 `surfaceId` 经 `ExportTextureInfo`（`export_texture_info.h`，仅元数据）挂到子树根视图节点；生产者注册由 `NodeContainerPattern::HandleTextureExport`→`RosenRenderContext::DoTextureExport(surfaceId)`（`rosen_render_context.cpp:6773`）将子树 `rsNode_->RemoveFromTree()` 从主 RS 显示树分离、交付 `Rosen::RSTextureExport`（ace_engine 边界到此为止）；buffer 生产（专用 `RSUIDirector` 把子树逐帧合成进消费者 surface）由跨仓 Rosen（graphic_2d）完成，不在本 Feat 详细描述。此外，`isTextureExportNode=true` 具**向下传染**特性（graphic_2d/Rosen 侧实现）：当一个 rsNode 挂载在 `isTextureExportNode=true` 的 rsNode 之下时，该子 rsNode 也会被置为 `isTextureExportNode=true`——ArkUI 侧无需感知其内部实现，但需了解此特性（只需把导出子树根 RSNode 以 `isTextureExportNode=true` 创建，其下整个子树即整体进入纹理导出渲染通路）。本 Feat 只覆盖**生产者**行为，不覆盖消费者（开启 `NativeEmbedMode` 的 Web、应用开发者 XComponent 自绘制）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 同层渲染纹理生产者（ArkUI 子树纹理导出） |
| 特性编号 | Func-04-18-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | `@since 11 dynamic` / `@atomicservice 12`（`NodeRenderType` / `RenderOptions` / `BuilderNode` 构造） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂（ace_engine 生产者侧为主：渲染树分离/生产者交付/布局驱动尺寸；buffer 生产为跨仓 Rosen(graphic_2d) 外部依赖，不在本 Feat 详细描述） |

## 本次变更范围（Delta）

无新增变更，已有实现补录。本特性为 Func-04-18-01（同层渲染机制）首个 Feat，聚焦**生产者侧**：BuilderNode 子树如何被翻转为纹理导出（buffer 生产者）模式、如何连同消费者 surfaceId 一起交付给 rs（Rosen）。范围边界：

- **本 Feat 覆盖**：纹理导出触发与资格门控、RS 子树纹理化与从显示树分离、生产者注册与 buffer 生产交付、布局驱动生产触发与尺寸同步、生命周期与异常。
- **本 Feat 不覆盖**：① 消费者行为——开启 `NativeEmbedMode` 的 Web（`web_pattern.cpp` `SameLayerSurface` 注册表 `:472-493`、`IsNeedExportTexture` `:4382-4388`）、应用开发者用 XComponent 自绘制持有 surface；② Rosen（graphic_2d）内部 `RSUIDirector` 渲染线程合成、BufferQueue 生产消费时序（ace_engine 边界在 `DoTextureExport`→`RSTextureExport` 交付处）；③ XComponent 作为并行生产者宿主（`xcomponent_pattern.cpp:1893-1984`，与 NodeContainer 共享同一 `RSTextureExport` 机制）仅作交叉引用，不单独立 AC。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/18-on-device-rendering/01-same-layer-rendering/design.md` | Baselined |
| SDK 公开声明 | `interface/sdk-js/api/arkui/BuilderNode.d.ts`（L84-193 枚举/RenderOptions，L317 构造） | — |
| SDK re-export | `interface/sdk-js/api/@ohos.arkui.node.d.ts` | — |
| Native 枚举 | `frameworks/core/components/common/layout/constants.h`（L936-939） | — |
| 元数据载体 | `frameworks/core/components_ng/export_texture_info/export_texture_info.h` | — |
| UINode 持有 | `frameworks/core/components_ng/base/ui_node.h`（L737-744,L1384）/ `ui_node.cpp`（L2162-2172） | — |
| ArkTS 入口 | `frameworks/bridge/declarative_frontend/jsview/js_base_node.{h,cpp}` | — |
| 静态 BuilderNode Native 实现 | `frameworks/core/interfaces/native/implementation/builder_node_ops_accessor.cpp` | — |
| 构建栈标志 | `frameworks/core/components_ng/base/view_stack_processor.h`（L547-555,L627） | — |
| 自定义节点传播 | `frameworks/core/components_ng/pattern/custom/custom_node.cpp`（L92-95） | — |
| 生产者注册（宿主） | `frameworks/core/components_ng/pattern/node_container/node_container_pattern.{h,cpp}` | — |
| NodeContainer 入口桥 | `frameworks/bridge/declarative_frontend/jsview/js_node_container.cpp`（L246-280） | — |
| 纹理导出/分离（ace_engine 边界） | `frameworks/core/components_ng/render/adapter/rosen_render_context.{h,cpp}` | — |
| surfaceId 解析 | `frameworks/base/utils/string_utils.{h,cpp}`（L92,L255-265） | — |
| embed 注册表 | `frameworks/core/pipeline/base/element_register.{h,cpp}`（L137-145,L474-489） | — |
| 生命周期触发 | `frameworks/core/components_ng/base/frame_node.cpp`（L800,L3480-3483,L7264-7272）/ `frameworks/core/components_ng/base/pattern.cpp`（L373-379） | — |
| Rosen 生产者（graphic_2d，跨仓） | buffer 生产由跨仓 Rosen 完成（专用 `RSUIDirector` 把子树逐帧合成进消费者 surface）；ace_engine 边界止于 `DoTextureExport`→`RSTextureExport` 交付，不在本 Feat 详细描述 | 跨仓外部依赖 |

> 需求基线见 design.md「需求基线」、不涉及项见 design.md「不涉及项承接」（已有能力补录，无独立 proposal.md）。

---

## 用户故事

### US-1: 纹理导出模式触发与资格门控

**作为** ArkUI 框架，
**我想要** 在 BuilderNode 以 `{ surfaceId, type: RENDER_TYPE_TEXTURE }` 构建自定义视图子树时，把子树根节点标记为纹理导出（buffer 生产者）模式，
**以便** 后续把该子树纹理交付给持有 surfaceId 的消费者 surface。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 以 `type: NodeRenderType.RENDER_TYPE_TEXTURE` 构造 BuilderNode THEN `RenderOptions.type` 默认为 `RENDER_TYPE_DISPLAY`（`BuilderNode.d.ts:171,178`），`surfaceId` 默认 `""` 且**仅当 `type=RENDER_TYPE_TEXTURE` 时生效**（`BuilderNode.d.ts:184,193`）；`NodeRenderType` 枚举 `DISPLAY=0/TEXTURE=1`，`@since 11 dynamic`/`@atomicservice 12`（`BuilderNode.d.ts:87-141`） | 正常 |
| AC-1.2 | WHEN（ArkTS 路径）BuilderNode `.build()` 执行惰性 builder THEN builder lambda 内置 `ViewStackProcessor::GetInstance()->SetIsExportTexture(renderType == RENDER_TYPE_TEXTURE)`（单参 `js_base_node.cpp:86`、多参 `:111`），使 builder 期间创建的 RSNode 以纹理导出节点身份创建 | 正常 |
| AC-1.3 | WHEN（静态 BuilderNode Native 实现路径）BuilderNode `CreateImpl` 执行 builder THEN 同样置 `ViewStackProcessor::SetIsExportTexture(renderType == RENDER_TYPE_TEXTURE)`（`builder_node_ops_accessor.cpp:77`）并 `SetIsBuilderNode(true)`（`:76`） | 正常 |
| AC-1.4 | WHEN build 后判定子树根是否受支持 THEN ArkTS 路径按 `EXPORT_TEXTURE_SUPPORT_TYPES = { JS_VIEW_ETS_TAG, COMMON_VIEW_ETS_TAG }`（`js_base_node.cpp:53`，判定 `:153`）命中才 `CreateExportTextureInfoIfNeeded()`+`SetSurfaceId(surfaceId_)`+`SetCurrentRenderType(renderType_)`（`js_base_node.cpp:247-251`）；静态 BuilderNode Native 实现路径 `IsSupportExportTexture`（`builder_node_ops_accessor.cpp:40-48`）要求 `renderType==TEXTURE` 且 content 节点 tag 在同集合，命中才 attach（`:98-102`） | 正常 |
| AC-1.5 | WHEN 子树根 tag 不在 `{JS_VIEW_ETS_TAG, COMMON_VIEW_ETS_TAG}` THEN 不创建 `ExportTextureInfo`、不进入生产者路径（`js_base_node.cpp:153`；`builder_node_ops_accessor.cpp:47`） | 边界 |
| AC-1.6 | WHEN build 嵌套自定义组件 THEN `CustomNode::BuildItem` 以 `parent->IsNeedExportTexture() \|\| IsNeedExportTexture()` 向下传播 `SetIsExportTexture`（`custom_node.cpp:93-95`），保证嵌套子树 RSNode 同为纹理导出节点 | 正常 |
| AC-1.7 | WHEN `ExportTextureInfo` 已 attach THEN `UINode::IsNeedExportTexture()` 返回 `exportTextureInfo_ && exportTextureInfo_->GetCurrentRenderType() == RENDER_TYPE_TEXTURE`（`ui_node.cpp:2169-2172`）；`CreateExportTextureInfoIfNeeded()` 懒创建（`:2162-2167`） | 正常 |

### US-2: RS 子树纹理化与从显示树分离

**作为** ArkUI 框架，
**我想要** 让纹理导出子树的 RSNode 以生产者身份创建、并把它从主 RS 显示树分离，
**以便** 子树渲染被导出为纹理而非上屏。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 子树节点初始化渲染上下文 THEN `RosenRenderContext::InitContext` 读 `ViewStackProcessor::IsExportTexture()`（`rosen_render_context.cpp:650`），并以 `isTextureExportNode` 透传进各 `Rosen::*Node::Create`：根节点 `RSRootNode::Create(false, isTextureExportNode, rsContext)`（`:653`）、普通节点 `RSCanvasNode::Create(...)`（`:655`）、`CreateNodeByType`（`:658`，于 `:679` 进入 `RSSurfaceNodeConfig.isTextureExportNode`） | 正常 |
| AC-2.2 | WHEN `DoTextureExport(surfaceId)` 被调用 THEN 先 `rsNode_->RemoveFromTree()` 把子树移出主 RS 显示树（`rosen_render_context.cpp:6776`），再 `std::make_shared<Rosen::RSTextureExport>(rsNode_, surfaceId)`（`:6778`），并 `rsSurfaceNode->SetTextureExport(true)`（`:6782`）、`return rsTextureExport_->DoTextureExport()`（`:6784`） | 正常 |
| AC-2.3 | WHEN 子树已从主树分离 THEN 宿主（NodeContainer）渲染上下文被置 `SetIsNeedRebuildRSTree(false)`（`node_container_pattern.cpp:120-124`），使 `ReCreateRsNodeTree/ReCreateMixedRsNodeTree/ReCreateRsNodeTreeByTargetList` 在 `!isNeedRebuildRSTree_`（默认 true，`render_context.h:907`）时提前 return（`rosen_render_context.cpp:5361,5381,5402`），防止 flush 时把分离子树重新挂回 | 边界 |
| AC-2.4 | WHEN 基类 `RenderContext::DoTextureExport` 未覆写 THEN 默认 no-op 返 false（`render_context.cpp:563-566`）——只有 Rosen 后端实现真正分流 | 边界 |

### US-3: 生产者注册与 buffer 生产交付

**作为** ArkUI 框架，
**我想要** 把子树 + 消费者 surfaceId 一起交付给 rs，由 rs 作为 buffer 生产者把纹理投递给持有该 surface 的消费者，
**以便** 完成同层渲染生产者侧职责（ace_engine 边界到此为止）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN NodeContainer 完成子树挂载并进入首次脏布局 THEN `OnDirtyLayoutWrapperSwap` 在 `surfaceId_ != 0U && !exportTextureNode_.Invalid()` 时 post after-layout task 调 `HandleTextureExport(false, host)`（`node_container_pattern.cpp:100-109`） | 正常 |
| AC-3.2 | WHEN `HandleTextureExport(false, ...)` THEN `elementRegister->RegisterEmbedNode(surfaceId_, WeakPtr(exportTextureNode))`（`node_container_pattern.cpp:133`）登记 surfaceId↔FrameNode 映射（`element_register.cpp:474-489`），随后 `exportTextureRenderContext->DoTextureExport(surfaceId_)`（`:135`） | 正常 |
| AC-3.3 | WHEN `DoTextureExport(surfaceId)` 完成子树交付 THEN ace_engine 侧职责到此为止——buffer 生产（把子树逐帧合成进消费者 surface）由跨仓 Rosen（graphic_2d）完成，ace_engine 边界止于 `DoTextureExport`→`RSTextureExport` 交付；Rosen 内部 `RSUIDirector`/`RSSurfaceNode`/`SurfaceUtils` 实现不在本 Feat 详细描述 | 边界 |

### US-4: 布局驱动生产触发与尺寸同步

**作为** ArkUI 框架，
**我想要** 以布局为驱动重复触发生产、并把节点 paint 矩形连续同步为纹理尺寸，
**以便** 标签宽高变化时纹理随之更新、无独立 flush pass。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN NodeContainer 每次脏布局交换 THEN `OnDirtyLayoutWrapperSwap` 重 post after-layout task 调 `HandleTextureExport(false, ...)`（`node_container_pattern.cpp:100-109`）——生产是**布局驱动**，pipeline_ng 无独立 texture-export flush pass（确认 pipeline_ng 无 `TextureExport`/`RemoveFromTree`/`IsNeedRebuildRSTree` 引用） | 正常 |
| AC-4.2 | WHEN 几何同步且 `rsTextureExport_` 存在 THEN `RosenRenderContext::SyncGeometryFrame(paintRect)` 调 `rsTextureExport_->UpdateBufferInfo(x, y, w, h)`（`rosen_render_context.cpp:893-898`），由 `SyncGeometryProperties`（`:940,942`）/`SetFrameWithoutAnimation`（`:871-872`）触发 | 正常 |
| AC-4.3 | WHEN 几何同步持续触发 THEN **纹理尺寸=导出节点 paint/frame 矩形（布局派生）**，非显式宽高参数；buffer 侧尺寸更新由跨仓 Rosen 完成，不在本 Feat 详细描述 | 正常 |
| AC-4.4 | WHEN BuilderNode 选项给定 `selfIdealSize` THEN 静态 BuilderNode Native 实现路径 `newNode->SetParentLayoutConstraint(peer->size_.ConvertToSizeT())`（`builder_node_ops_accessor.cpp:105-107`，实现 `frame_node.cpp:7264-7272`）约束测量→影响 paintRect→影响纹理尺寸 | 正常 |
| AC-4.5 | WHEN 布局期间 `config.frameSizeChange` THEN `OnDirtyLayoutWrapperSwap` 触发 `FireOnResize(size)`（`node_container_pattern.cpp:91-99`）并重跑 `HandleTextureExport(false, ...)`（`:100-110`） | 正常 |
| AC-4.6 | WHEN 导出子树被测量 THEN `NodeContainerLayoutAlgorithm::Measure` 把导出子树与普通子树同等对待（`node_container_layout_algorithm.cpp:30-71`，无 `IsNeedExportTexture` 分支），帧矩形即由正常栈式布局得出 | 边界 |

### US-5: 生命周期与异常

**作为** ArkUI 框架，
**我想要** 在子树挂载/卸载与异常输入下正确注册/释放生产者、并避免重复生产，
**以便** 资源不泄漏、异常不崩溃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 子树首次挂载 THEN 生产**不在构造期发生**：`AddBaseNode`（`node_container_pattern.cpp:46-72`）挂 child0→`OnAddBaseNode`（`:189-194`）先 `HandleTextureExport(true)` 停旧再 `SetExportTextureInfoIfNeeded()`（解析 surfaceId、缓存 `exportTextureNode_`，`:161-187`）→`OnMountToParentDone`（`:196-199`，由 `frame_node.cpp:3480-3483` 派发）→`MarkNeedFrameFlushDirty(MEASURE)`（`:71`）调度布局→`OnDirtyLayoutWrapperSwap` 首次 post `HandleTextureExport(false)`（`:100-109`）才真正生产+`RegisterEmbedNode` | 正常 |
| AC-5.2 | WHEN `SetExportTextureInfoIfNeeded` 解析 surfaceId THEN `surfaceId_ = StringUtils::StringToLongUint(exportTextureInfo->GetSurfaceId())`（`node_container_pattern.cpp:186`），`StringToLongUint` 以十进制 `strtoull` 解析、失败/溢出返回默认 0（`string_utils.cpp:255-265`） | 正常 |
| AC-5.3 | WHEN surfaceId 为空/非数字/溢出（解析得 0）THEN 生产循环因 `surfaceId_ != 0U`（`node_container_pattern.cpp:100`）不进入，**静默禁用导出、无错误、无日志（ace_engine 侧）** | 异常 |
| AC-5.4 | WHEN FrameNode 析构 THEN `frame_node.cpp:800`→`Pattern::DetachFromFrameNode`（`pattern.cpp:373-379`）→`OnDetachFromFrameNode`（`node_container_pattern.cpp:138-141`）→`HandleTextureExport(true, frameNode)`→`UnregisterEmbedNode(surfaceId_, exportTextureNode)`（`:128`）+`StopTextureExport()`（`:130`） | 正常 |
| AC-5.5 | WHEN `StopTextureExport()` THEN `rsTextureExport_->StopTextureExport()`+`rsSurfaceNode->SetTextureExport(false)`（`rosen_render_context.cpp:6787-6797`）；Rosen 侧资源回收（RSUIDirector 销毁、子树清理）由跨仓 Rosen 完成，不在本 Feat 详细描述 | 正常 |
| AC-5.6 | WHEN `~RosenRenderContext` 析构 THEN 不显式调 `StopTextureExport`（`:407-418`），`rsTextureExport_`（`shared_ptr`，成员 `rosen_render_context.h:1023`）由 shared_ptr 释放；显式停/注销依赖 `OnDetachFromFrameNode` 先跑（经由 FrameNode 析构路径，AC-5.4） | 边界 |
| AC-5.7 | WHEN 嵌套 NodeContainer 且祖先 NodeContainer 的 child 已是 `RENDER_TYPE_TEXTURE` THEN 当前容器 `SetExportTextureInfoIfNeeded` 让步、提前 return（`node_container_pattern.cpp:171-183`），避免重复生产 | 边界 |
| AC-5.8 | WHEN remake/子树交换 THEN `AddBaseNode` 先 `RemoveChildAtIndex(0)`+`BuilderUtils::RemoveBuilderFromParent`（`node_container_pattern.cpp:62-63`），`OnAddBaseNode` 停旧导出再注册新导出；`CleanChild`（`:74-80`）移 child0 并 `ResetExportTextureInfo`（`:155-159`）清零 surfaceId/exportTextureNode | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.7 | R-1,R-2,R-3,R-4 | T-1 | SDK d.ts 核对 + UT（JSBaseNode/builder_node_ops_accessor Mock ViewStackProcessor） | `BuilderNode.d.ts:87-193`；`constants.h:936-939`；`js_base_node.cpp:53,86,111,153,247-251`；`builder_node_ops_accessor.cpp:40-48,77,98-102`；`custom_node.cpp:93-95`；`ui_node.cpp:2162-2172` |
| AC-2.1~2.4 | R-5,R-6,R-7 | T-1 | UT（RosenRenderContext InitContext/DoTextureExport） | `rosen_render_context.cpp:650-659,5361,5381,5402,6773-6785`；`render_context.h:907`；`render_context.cpp:563-566` |
| AC-3.1~3.3 | R-8,R-9 | T-1 | UT（NodeContainerPattern HandleTextureExport） | `node_container_pattern.cpp:100-109,114-136`；`element_register.cpp:474-489` |
| AC-4.1~4.6 | R-10,R-11,R-12 | T-1 | UT（OnDirtyLayoutWrapperSwap/SyncGeometryFrame）+ XTS（宽高变化） | `node_container_pattern.cpp:82-112`；`rosen_render_context.cpp:871-872,893-898,940-942`；`builder_node_ops_accessor.cpp:105-107`；`node_container_layout_algorithm.cpp:30-71` |
| AC-5.1~5.8 | R-13,R-14,R-15,R-16,R-17 | T-1 | UT（生命周期/异常）+ XTS（销毁/重挂） | `node_container_pattern.cpp:46-80,100,138-141,155-199`；`string_utils.cpp:255-265`；`frame_node.cpp:800,3480-3483,7264-7272`；`pattern.cpp:373-379`；`rosen_render_context.cpp:407-418,6787-6797` |

## 规则定义

> 统一规则表，类型标签：行为/边界/异常/恢复。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | BuilderNode 以 `type=RENDER_TYPE_TEXTURE` 构造 | `surfaceId` 仅在 TEXTURE 模式生效；build 时 builder lambda 置 `ViewStackProcessor::SetIsExportTexture(true)` | type 默认 DISPLAY；surfaceId 默认 "" | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | build 后子树根 tag ∈ `{JS_VIEW_ETS_TAG, COMMON_VIEW_ETS_TAG}` 且 renderType=TEXTURE | `CreateExportTextureInfoIfNeeded`+`SetSurfaceId`+`SetCurrentRenderType` 挂到根视图节点 | ArkTS 按根 tag 判；静态 BuilderNode Native 实现按 `firstChild.firstChild` tag 判 | AC-1.4 |
| R-3 | 边界 | 子树根 tag 不在支持集合 | 不创建 ExportTextureInfo、不进生产者路径 | 仅自定义视图/common-view 根可生产 | AC-1.5 |
| R-4 | 行为 | 嵌套自定义组件 build | `SetIsExportTexture(parent\|\|self)` 向下传播 | 保证嵌套子树 RSNode 同为纹理导出 | AC-1.6,AC-1.7 |
| R-5 | 行为 | 子树节点 InitContext | 以 `isTextureExportNode=IsExportTexture()` 创建 RSNode（RSRootNode/RSCanvasNode/RSSurfaceNode） | 标志源自 ViewStackProcessor | AC-2.1 |
| R-6 | 行为 | `DoTextureExport(surfaceId)` | `RemoveFromTree()` 分离子树→建 `RSTextureExport(rsNode_, surfaceId)`→`SetTextureExport(true)`→`DoTextureExport()` | 基类默认 no-op 返 false | AC-2.2,AC-2.4 |
| R-7 | 边界 | 子树已分离 | 宿主 `SetIsNeedRebuildRSTree(false)`，rebuild 站点跳过重挂 | isNeedRebuildRSTree_ 默认 true | AC-2.3 |
| R-8 | 行为 | NodeContainer 首次脏布局（surfaceId_≠0） | after-layout task 调 `HandleTextureExport(false)`→`RegisterEmbedNode`+`DoTextureExport` | 生产不在构造期发生 | AC-3.1,AC-3.2,AC-5.1 |
| R-9 | 边界 | `DoTextureExport(surfaceId)` 完成交付 | buffer 生产（把子树逐帧合成进消费者 surface）由跨仓 Rosen（graphic_2d）完成；ace_engine 边界止于 `DoTextureExport`→`RSTextureExport` 交付 | Rosen 内部实现不在本 Feat 详细描述 | AC-3.3 |
| R-10 | 行为 | NodeContainer 每次脏布局交换 | 重 post after-layout task 调 `HandleTextureExport(false)` | 布局驱动；pipeline_ng 无独立 flush | AC-4.1,AC-4.5 |
| R-11 | 行为 | 几何同步（rsTextureExport_ 存在） | `SyncGeometryFrame(paintRect)`→`UpdateBufferInfo(x,y,w,h)` | 每次 geometry sync 触发，尺寸连续跟踪 | AC-4.2 |
| R-12 | 行为 | 几何同步 | **纹理尺寸=导出节点 paint/frame 矩形（布局派生）**，经 `SyncGeometryFrame` 连续同步 | buffer 侧尺寸更新由跨仓 Rosen 完成 | AC-4.3,AC-4.4,AC-4.6 |
| R-13 | 行为 | FrameNode 析构 | dtor→DetachFromFrameNode→OnDetachFromFrameNode→`HandleTextureExport(true)`→`UnregisterEmbedNode`+`StopTextureExport` | 顺序固定 | AC-5.4,AC-5.5 |
| R-14 | 边界 | `~RosenRenderContext` | 不显式 StopTextureExport；rsTextureExport_ shared_ptr 释放；显式停依赖 OnDetach 先跑 | 依赖 FrameNode 析构路径 | AC-5.6 |
| R-15 | 异常 | surfaceId 空/非数字/溢出（解析得 0） | 生产循环因 `surfaceId_ != 0U` 不进入；静默禁用导出，ace_engine 侧无错误无日志 | strtoull 失败返 0 | AC-5.2,AC-5.3 |
| R-16 | 边界 | 嵌套 NodeContainer 且祖先 child 已 TEXTURE | 当前容器让步、提前 return，不重复生产 | 嵌套导出去重，祖先优先 | AC-5.7 |
| R-17 | 恢复 | remake/子树交换/destroy | 先停旧导出（Unregister+Stop）再注册新导出；CleanChild→ResetExportTextureInfo 清零 | 避免悬垂生产者 | AC-5.8 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | 触发与资格门控（US-1） | SDK d.ts 核对 + UT | SetIsExportTexture 时机、ExportTextureInfo attach 条件、tag 白名单、嵌套传播 |
| VM-2 | RS 子树分离（US-2） | UT | InitContext isTextureExportNode 透传、RemoveFromTree、SetIsNeedRebuildRSTree 守卫 |
| VM-3 | 生产者注册与交付（US-3） | UT（ace_engine 边界） | HandleTextureExport→DoTextureExport 交付、embed 注册表（buffer 生产在跨仓 Rosen） |
| VM-4 | 布局驱动与尺寸（US-4） | UT + XTS | OnDirtyLayoutWrapperSwap 驱动、SyncGeometryFrame→UpdateBufferInfo=paintRect |
| VM-5 | 生命周期与异常（US-5） | UT + XTS | 首产延迟到首次布局、销毁停注、非法 surfaceId 静默、嵌套去重 |

## API 变更分析

> 存量补录，无新增/变更/废弃。公开 API 已与 `interface/sdk-js/api/arkui/BuilderNode.d.ts` 权威声明交叉核对。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---------|---------|---------|--------|----------|---------|--------|
| `enum NodeRenderType` | Public | — | `RENDER_TYPE_DISPLAY=0`/`RENDER_TYPE_TEXTURE=1` | 无 | 渲染类型枚举；TEXTURE 触发纹理导出生产者模式（`BuilderNode.d.ts:87-141`） | AC-1.1 |
| `interface RenderOptions` | Public | `selfIdealSize?: Size`、`type?: NodeRenderType`、`surfaceId?: string` | — | 无 | BuilderNode 构造选项；`surfaceId` 仅 type=TEXTURE 生效（`BuilderNode.d.ts:153-193`） | AC-1.1,AC-4.4 |
| `constructor(uiContext, options?)` | Public | `uiContext: UIContext`、`options?: RenderOptions` | `BuilderNode` | 无 | 构造 BuilderNode（`BuilderNode.d.ts:317`） | AC-1.1~1.4 |

### 变更/废弃 API

无。

> SDK 权威声明：`interface/sdk-js/api/arkui/BuilderNode.d.ts`（枚举 L87-141、RenderOptions L153-193、构造 L317），`@since 11 dynamic`/`@atomicservice 12`；re-export `@ohos.arkui.node.d.ts:36`。源码与 SDK 一致，无偏差。注意：公开 API 仅触发生产者模式；真正 buffer 生产发生在跨仓 Rosen（graphic_2d），不在公开 API 表达范围。

## 接口规格

### 接口定义

**NodeRenderType / RenderOptions（公开触发入口，`@since 11 dynamic`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enum NodeRenderType { RENDER_TYPE_DISPLAY = 0, RENDER_TYPE_TEXTURE = 1 }`；`interface RenderOptions { selfIdealSize?: Size; type?: NodeRenderType; surfaceId?: string }`；`constructor(uiContext: UIContext, options?: RenderOptions)` |
| 返回值 | 枚举值 / BuilderNode 实例 |
| 开放范围 | Public |
| 错误码 | 无（触发型 API；非法 surfaceId 在 ace_engine 侧静默禁用，见 R-17） |
| 关联 AC | AC-1.1,AC-1.4,AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `options.type` | NodeRenderType | 否 | `RENDER_TYPE_DISPLAY` | 仅 `RENDER_TYPE_TEXTURE` 触发纹理导出；其余值等同 DISPLAY |
| `options.surfaceId` | string | 否 | `""` | 仅 type=TEXTURE 生效；须为十进制 uint64 字面量，空/非数字/溢出解析为 0→静默禁用（R-15） |
| `options.selfIdealSize` | Size | 否 | `{width:0,height:0}` | 约束子树测量→影响纹理尺寸（R-12） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `type=RENDER_TYPE_TEXTURE` + 合法 surfaceId + 自定义视图根 | build 时标记子树为纹理导出节点；首次布局后注册生产者、分离显示树、交付 RSTextureExport | AC-1.2~1.4,AC-3.1,AC-3.2 |
| 2 | `type=RENDER_TYPE_TEXTURE` 但根非自定义视图 | 不创建 ExportTextureInfo，不生产 | AC-1.5 |
| 3 | `surfaceId=""` 或非法 | 解析得 0，生产循环不进入，静默禁用 | AC-5.3 |
| 4 | 标签宽高变化（UPDATE） | SyncGeometryFrame→UpdateBufferInfo=paintRect，纹理尺寸连续跟踪；OnDirtyLayoutWrapperSwap 重跑生产 | AC-4.2,AC-4.3,AC-4.5 |
| 5 | 子树销毁 | OnDetach→StopTextureExport+UnregisterEmbedNode | AC-5.4,AC-5.5 |

> 内部生产者接口（非公开，框架内部特性，源码即规格）：`ExportTextureInfo{GetSurfaceId/SetSurfaceId/GetCurrentRenderType/SetCurrentRenderType}`（`export_texture_info.h:33-51`）、`UINode::IsNeedExportTexture/CreateExportTextureInfoIfNeeded`（`ui_node.cpp:2162-2172`）、`NodeContainerPattern::HandleTextureExport`（`node_container_pattern.cpp:114-136`）、`RosenRenderContext::DoTextureExport/StopTextureExport/SyncGeometryFrame`（`rosen_render_context.cpp:893-898,6773-6797`）。

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** `@since 11 dynamic` / `@atomicservice 12`（`NodeRenderType`/`RenderOptions`/`BuilderNode` 构造）。
- **API 版本号策略:** `NodeRenderType`、`RenderOptions.{selfIdealSize,type,surfaceId}`、`BuilderNode` 构造均 `@since 11 dynamic`/`@atomicservice 12`（`BuilderNode.d.ts`）。本 Feat 不引入新 API 版本。

> 跨仓兼容性：ace_engine 生产者侧交付边界（`DoTextureExport`→`RSTextureExport`）依赖 Rosen（graphic_2d）`RSTextureExport`/`RSSurfaceNode::CreateNodeAndSurface`/`RSUIDirector` 的稳定契约；Rosen 侧接口变更不在本仓控管范围，作为外部依赖记录。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 跨仓边界 | ace_engine 只到 `DoTextureExport`→`RSTextureExport` 交付；buffer 生产在 Rosen | AC-3.3 |
| ExportTextureInfo 仅元数据 | 真正生产者 `RSTextureExport` 挂在 RosenRenderContext，不在 ExportTextureInfo | AC-1.4,AC-3.3 |
| 生产=布局驱动 | 无独立 flush pass；随 NodeContainer 脏布局触发 | AC-4.1 |
| 纹理尺寸=布局 paintRect | 无显式宽高；经 SyncGeometryFrame 连续同步 | AC-4.2,AC-4.3 |
| 资格白名单 | 仅自定义视图根（JS_VIEW_ETS_TAG/COMMON_VIEW_ETS_TAG）+TEXTURE 可生产 | AC-1.5 |
| 嵌套去重 | 祖先优先，子容器让步 | AC-5.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 生产随布局触发，无额外 flush pass；尺寸经 geometry sync 连续更新，无独立 resize 调用 | UT 帧调度 + XTS 帧率 | `node_container_pattern.cpp:82-112`；`rosen_render_context.cpp:893-898` |
| 内存 | `rsTextureExport_` shared_ptr 随 RosenRenderContext 生命周期释放；销毁经 OnDetach 显式 Stop+Unregister | 内存测试 | `rosen_render_context.h:1023`；`node_container_pattern.cpp:138-141` |
| 安全 | Public 无权限；生产者只向消费者**已注册**的 surface 投递，不创建/越权访问任意 surface | 代码评审 | ace_engine 仅以 `surfaceId` 经 `DoTextureExport` 交付，不创建/持有任意 surface（"只向已注册 surface 投递"由跨仓 Rosen 保证） |
| 可靠性 | 非法 surfaceId 静默禁用不崩溃；销毁顺序保证先停注后释放 shared_ptr | UT | `node_container_pattern.cpp:100`；AC-5.4~5.6 |
| 可测试性 | 内部接口可经 Mock RosenRenderContext/NodeContainerPattern 单测；端到端经 XTS 同层渲染用例 | UT + XTS | 本 spec 全篇 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机/平板/折叠屏 | 无差异 | 生产者行为与设备无关，纹理尺寸随节点 paintRect | XTS | `rosen_render_context.cpp:893-898`（paintRect 驱动） |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|---------|
| 无障碍 | 否（透传） | 导出子树无障碍由各自 FrameNode 承担；embed 注册表供无障碍反查（`accessibility_manager_ng.cpp:167-172,520`） | — |
| 大字体 | 否（透传） | 随子树 paintRect 影响纹理尺寸 | — |
| 深色模式 | 否（透传） | 随子树渲染 | — |
| 多窗口/分屏 | 否 | 生产者行为与窗口无关（surfaceId 由消费者提供） | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | `@since 11 dynamic`/`@atomicservice 12` | 兼容性声明 |
| 生态兼容 | 是 | 跨范式：ArkTS 动态（`js_base_node.cpp`）/静态 BuilderNode Native 实现（`builder_node_ops_accessor.cpp`）两入口共用同一 Rosen 交付机制 | design.md ADR-1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 同层渲染纹理生产者（ArkUI 子树纹理导出）
  作为 ArkUI 框架
  我想要 把 BuilderNode 子树翻转为 buffer 生产者并连同 surfaceId 交付 rs
  以便 把子树纹理投递给持有 surfaceId 的消费者 surface

  Scenario: TEXTURE 模式正常触发生产者
    Given BuilderNode 以 { type: RENDER_TYPE_TEXTURE, surfaceId: "<合法uint64>" } 构建自定义视图子树
    When build 期间 builder lambda 置 SetIsExportTexture(true)
    Then 子树 RSNode 以 isTextureExportNode=true 创建
    And build 后 ExportTextureInfo{surfaceId, TEXTURE} 挂到根视图节点
    And 首次布局后 HandleTextureExport(false)→DoTextureExport 分离显示树并交付 RSTextureExport

  Scenario: 根非自定义视图不生产
    Given BuilderNode 子树根 tag 不在 {JS_VIEW_ETS_TAG, COMMON_VIEW_ETS_TAG}
    When build 完成
    Then 不创建 ExportTextureInfo，不进入生产者路径

  Scenario Outline: 非法 surfaceId 静默禁用
    Given options.surfaceId = "<id>"
    When SetExportTextureInfoIfNeeded 以 StringToLongUint 解析
    Then 解析得 0，生产循环因 surfaceId_ != 0U 不进入
    And ace_engine 侧无错误、无日志
    Examples:
      | id |
      | "" |
      | "abc" |
      | "99999999999999999999999999" |

  Scenario: 标签宽高变化连续同步纹理尺寸
    Given 已注册生产者的导出子树
    When 节点 paintRect 因布局变化
    Then SyncGeometryFrame→UpdateBufferInfo(x,y,w,h) 连续同步纹理尺寸（=paintRect）
    And OnDirtyLayoutWrapperSwap 重跑 HandleTextureExport(false)

  Scenario: 子树销毁释放生产者
    Given 已注册生产者的导出子树
    When FrameNode 析构
    Then OnDetachFromFrameNode→HandleTextureExport(true)→UnregisterEmbedNode+StopTextureExport
    And rsTextureExport_ shared_ptr 随后释放

  Scenario: 嵌套导出去重
    Given 祖先 NodeContainer 的 child 已是 RENDER_TYPE_TEXTURE
    When 嵌套 NodeContainer 进入 SetExportTextureInfoIfNeeded
    Then 当前容器让步、提前 return，不重复生产
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（仅生产者；消费者/Web/XComponent 自绘制、Rosen 内部合成、XComponent 并行宿主为不覆盖/交叉引用）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "BuilderNode RENDER_TYPE_TEXTURE 触发纹理导出：JSBaseNode/builder_node_ops_accessor 如何置 ViewStackProcessor::SetIsExportTexture 并 attach ExportTextureInfo{surfaceId}"
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeContainerPattern HandleTextureExport→RosenRenderContext::DoTextureExport 的显示树分离与 RSTextureExport 交付链路"
  - repo: "openharmony/arkui_ace_engine"
    query: "ExportTextureInfo 元数据载体与 UINode::IsNeedExportTexture 门控、嵌套导出去重"
```

**关键文档：** `interface/sdk-js/api/arkui/BuilderNode.d.ts`（L84-193,L317）、`frameworks/core/components_ng/export_texture_info/export_texture_info.h`、`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp`（L650-659,L893-898,L6773-6797）、`frameworks/core/components_ng/pattern/node_container/node_container_pattern.cpp`（L82-199）
