# 特性规格

> Func-05-16-01-Feat-03 复用与纹理导出：固化 NodeContainer 复用生命周期（`NodeContainerNode::OnRecycle`/`OnReuse` 覆写**不调基类**（无子节点递归）、`destroyCallbacksMap_`+`ResetGeometryTransition`+`Pattern::OnRecycle`（NodeContainerPattern 不覆写为 no-op）、developer-mode debug boundary；**NodeController 无公开复用 API**、复用单元为 NodeContainerNode FrameNode、不支持跨实例复用）与纹理导出（embed node surface sharing：`SetExportTextureInfoIfNeeded`/`HandleTextureExport`、`surfaceId_` 键入 ElementRegister、`DoTextureExport`/`StopTextureExport` Rosen `RSTextureExport`、防嵌套、after-layout 触发、accessibility 消费）行为规格。本特性 framework-internal 为主（复用无公开 API）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 复用与纹理导出 |
| 特性编号 | Func-05-16-01-Feat-03 |
| 优先级 | P2 |
| 目标版本 | framework-internal（复用随 `@Reusable` 管线；纹理导出随 NG 渲染，无独立 `@since`）；SDK NodeController 仅有「不支持跨实例复用」caveat（`NodeController.d.ts:57-62`），无公开复用方法 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-01（渲染宿主）/Feat-02（生命周期回调）；本特性聚焦复用与纹理导出（embed node）。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/16-custom-placeholder-components/01-node-container/design.md` | Baselined |
| Dynamic API（NodeController 复用 caveat） | `interface/sdk-js/api/arkui/NodeController.d.ts` | — |
| NG Node（复用） | `frameworks/core/components_ng/pattern/node_container/node_container_node.cpp` / `.h` | — |
| NG Pattern（纹理导出） | `frameworks/core/components_ng/pattern/node_container/node_container_pattern.cpp` / `.h` | — |
| Pattern 基类（no-op hooks） | `frameworks/core/components_ng/pattern/pattern.h` | — |
| ElementRegister（embed node） | `frameworks/core/pipeline/base/element_register.cpp` | — |
| RenderContext（DoTextureExport） | `frameworks/core/components_ng/render/render_context.h`、`adapter/rosen_render_context.cpp` | — |
| ExportTextureInfo | `frameworks/core/components_ng/export_texture_info/export_texture_info.h` | — |
| Accessibility 消费 | `frameworks/core/accessibility/accessibility_manager_ng.cpp`、`adapter/ohos/osal/js_accessibility_manager.cpp` | — |

> 需求基线详见 proposal.md。复用部分 framework-internal（源码即规格，无 SDK 公开 API）；纹理导出 framework-internal。

---

## 用户故事

### US-1: 复用生命周期

**作为** 框架维护者,
**我想要** NodeContainerNode 经 @Reusable 回收/复用,
**以便** 在 ListItem/FlowItem 等可复用容器中复用 NodeContainer。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN NodeContainerNode 经 @Reusable 回收 THEN `OnRecycle`（`node_container_node.cpp:41-50`）触发 `destroyCallbacksMap_` 回调（`frame_node.h:1637/842/847`）、`GetLayoutProperty()->ResetGeometryTransition()`、`Pattern::OnRecycle()` | 正常 |
| AC-1.2 | WHEN `NodeContainerNode::OnRecycle` 执行 THEN **不调基类** `FrameNode::OnRecycle`/`UINode::OnRecycle`（与标准 FrameNode `frame_node.cpp:5432-5446` 不同）——**不递归子节点 OnRecycle、不 ClearAccessibilityFocus** | 边界 |
| AC-1.3 | WHEN NodeContainerNode 复用 THEN `OnReuse`（`node_container_node.cpp:52-61`）调 `pattern->OnReuse()`（NodeContainerPattern **不覆写**→空基 no-op `pattern.h:427-428`）+ developer-mode 下 `PaintDebugBoundary`（`:55-59`） | 正常 |
| AC-1.4 | WHEN `NodeContainerNode::OnReuse` 执行 THEN **不调基类** `FrameNode::OnReuse`/`UINode::OnReuse`——**不递归子节点 OnReuse** | 边界 |
| AC-1.5 | WHEN NodeContainerNode 析构 THEN `~NodeContainerNode`（`:32-39`）收集子树 BuilderNode 经 `BuilderUtils::ClearChildInBuilderContainer` 清理 | 正常 |
| AC-1.6 | WHEN 复用单元 THEN 为 **NodeContainerNode FrameNode**（tag `NODE_CONTAINER_ETS_TAG`，`GetOrCreateNodeContainerNode:19-30`），**非 NodeController**；由标准可复用容器（ListItem/FlowItem）驱动 | 边界 |
| AC-1.7 | WHEN 查 NodeController 公开复用 API THEN **无** `getReuseType`/`onReuse`/`aboutToReuse`（grep `NodeController.d.ts` 仅 NOTE caveat）；SDK caveat「NodeContainer does not support cross-instance reuse」（`:57-62`） | 边界 |

### US-2: 纹理导出 embed node

**作为** 框架维护者,
**我想要** NodeContainer 子节点可经纹理导出为 embed node surface,
**以便** 跨 surface 边界共享渲染（嵌入场景）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `SetExportTextureInfoIfNeeded`（`node_container_pattern.cpp:161-187`）THEN `ResetExportTextureInfo`+取 `GetChildAtIndex(0)`；子节点 `IsNeedExportTexture()` 为假则 return | 正常 |
| AC-2.2 | WHEN 设置 export info THEN 置 `exportTextureNode_`（WeakPtr，`:182`）+`surfaceId_=StringToLongUint(child ExportTextureInfo::GetSurfaceId())`（`:186`，`uint64` 成员 `pattern.h:144`） | 正常 |
| AC-2.3 | WHEN 防嵌套检查 THEN 若最近祖先 NodeContainer 的子节点已 `RENDER_TYPE_TEXTURE` 则 return（不重复导出，`:170-179`） | 边界 |
| AC-2.4 | WHEN `HandleTextureExport(false,start,...)`（`:114-136`）THEN `ElementRegister::RegisterEmbedNode(surfaceId_,WeakPtr(exportTextureNode))`（`:133`）+`RenderContext::DoTextureExport(surfaceId_)`（`:135`）；host `SetIsNeedRebuildRSTree(false)`（`:123`） | 正常 |
| AC-2.5 | WHEN `HandleTextureExport(true,stop,...)` THEN `ElementRegister::UnregisterEmbedNode(surfaceId_,...)`（`:128`）+`RenderContext::StopTextureExport()`（`:130`）；host `SetIsNeedRebuildRSTree(true)` | 正常 |
| AC-2.6 | WHEN Rosen 后端 `DoTextureExport`（`rosen_render_context.cpp:6773-6785`）THEN `rsNode->RemoveFromTree`+建/复用 `RSTextureExport`+`RSSurfaceNode::SetTextureExport(true)`（surface sharing） | 正常 |
| AC-2.7 | WHEN `GetExportTextureNode`（`:143-153`）THEN 从 `exportTextureNode_` 向下走到首个 FrameNode；消费方为 `HandleTextureExport` + ElementRegister embed node | 正常 |

### US-3: 纹理导出触发

**作为** 框架维护者,
**我想要** 纹理导出在正确时机启停,
**以便** surface 共享随节点生命周期正确管理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `OnAddBaseNode`（`:189-194`）THEN `HandleTextureExport(true,host)`（停旧）+`SetExportTextureInfoIfNeeded()`（设新）；**不在此时 start** | 正常 |
| AC-3.2 | WHEN `OnMountToParentDone`（`:196-199`）THEN `SetExportTextureInfoIfNeeded()` | 正常 |
| AC-3.3 | WHEN `OnDetachFromFrameNode`（`:138-141`）THEN `HandleTextureExport(true,frameNode)`（停止） | 正常 |
| AC-3.4 | WHEN `OnDirtyLayoutWrapperSwap`（`:82-112`）且 `surfaceId_!=0 && !exportTextureNode_.Invalid()` THEN 投 after-layout task 调 `HandleTextureExport(false,host)`（start/重导出）；失败日志 `DoTextureExport fail`（`:100-110`） | 正常 |
| AC-3.5 | WHEN 纹理路径 THEN **不置 dirty**（start 由 OnDirtyLayoutWrapperSwap after-layout 驱动，非内联；OnAddBaseNode/MountToParent/Detach 不调 MarkNeedFrameFlushDirty）；`OnDirtyLayoutWrapperSwap` return false（`:111`） | 边界 |
| AC-3.6 | WHEN `surfaceId_==0` 或 exportTextureNode 无效 THEN after-layout 不触发 DoTextureExport | 边界 |

### US-4: embed node 消费

**作为** 框架维护者,
**我想要** embed node 经 surfaceId 被无障碍等下游消费,
**以便** 跨 surface 边界正确遍历。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN embed node 注册 THEN ElementRegister 建**双向映射** `surfaceIdEmbedNodeMap_[surfaceId]=node`+`embedNodeSurfaceIdMap_[node]=surfaceId`（`element_register.cpp:474-480`） | 正常 |
| AC-4.2 | WHEN 下游查询 THEN `GetEmbedNodeBySurfaceId`/`GetSurfaceIdByEmbedNode`（`element_register.cpp:491-514`）供无障碍 manager 跨 surface 边界遍历（`accessibility_manager_ng.cpp:167-172,520`、`js_accessibility_manager.cpp:927-938`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.7 | R-1,R-2,R-3,R-9 | T-3 | UT：NodeContainerNode OnRecycle/OnReuse | `node_container_node.cpp:32-61`、`NodeController.d.ts:57-62` |
| AC-2.1~2.7 | R-4,R-5,R-6 | T-3 | UT：纹理导出 + Rosen mock | `node_container_pattern.cpp:114-187`、`rosen_render_context.cpp:6773-6797` |
| AC-3.1~3.6 | R-7,R-8 | T-3 | UT：触发时机 | `node_container_pattern.cpp:82-112,138-199` |
| AC-4.1~4.2 | R-10 | T-3 | UT + accessibility | `element_register.cpp:474-514` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | NodeContainerNode OnRecycle | destroyCallbacksMap_+ResetGeometryTransition+Pattern::OnRecycle；不调基类（无子递归/无 ClearAccessibilityFocus） | 与标准 FrameNode 不同 | AC-1.1,AC-1.2 |
| R-2 | 行为 | NodeContainerNode OnReuse | pattern->OnReuse()（空 no-op）+ developer-mode PaintDebugBoundary；不调基类 | NodeContainerPattern 不覆写 OnReuse/OnRecycle | AC-1.3,AC-1.4 |
| R-3 | 行为 | 析构 | 收集 BuilderNode 子树+ClearChildInBuilderContainer | — | AC-1.5 |
| R-4 | 行为 | SetExportTextureInfoIfNeeded | 取 child[0] IsNeedExportTexture→置 exportTextureNode_+surfaceId_ | 子非 need-export 则 return | AC-2.1,AC-2.2 |
| R-5 | 边界 | 防嵌套 | 最近祖先 NodeContainer 子已 RENDER_TYPE_TEXTURE 则 return | 不重复导出 | AC-2.3 |
| R-6 | 行为 | HandleTextureExport | start: RegisterEmbedNode+DoTextureExport；stop: UnregisterEmbedNode+StopTextureExport；host SetIsNeedRebuildRSTree | Rosen RSTextureExport surface sharing | AC-2.4~2.6 |
| R-7 | 行为 | 触发 | OnAddBaseNode(stop+set)/OnMountToParentDone(set)/OnDetachFromFrameNode(stop)/OnDirtyLayoutWrapperSwap(after-layout start) | start 不在 OnAddBaseNode | AC-3.1~3.4 |
| R-8 | 边界 | 纹理路径 dirty | 不置 dirty；start 由 after-layout 驱动 | surfaceId_==0 不触发 | AC-3.5,AC-3.6 |
| R-9 | 边界 | 复用单元/API | 复用单元为 NodeContainerNode FrameNode；NodeController 无公开复用 API；不支持跨实例复用 | SDK caveat | AC-1.6,AC-1.7 |
| R-10 | 行为 | embed node 消费 | 双向映射 surfaceId↔node；供 accessibility 跨 surface 遍历 | — | AC-4.1,AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 复用 | UT | OnRecycle/OnReuse 不调基类、destroyCallbacksMap、无公开复用 API |
| VM-2 | AC-2.x 纹理导出 | UT + Rosen mock | exportTextureNode/surfaceId、RegisterEmbedNode、DoTextureExport |
| VM-3 | AC-3.x 触发 | UT | OnAddBaseNode/MountToParent/Detach/after-layout start、防嵌套 |
| VM-4 | AC-4.x 消费 | UT + accessibility | 双向映射、accessibility 跨 surface |

## API 变更分析

> 本特性 framework-internal，无公开 API 变更（复用无公开 API；纹理导出为内部机制）。

### 新增 API

N/A（framework-internal）。

### 变更/废弃 API

N/A。

## 接口规格

> framework-internal，无公开接口规格（内部 C++ 机制）。核心内部契约见「规则定义」与各 `node_container_node.cpp`/`node_container_pattern.cpp`。

## 兼容性声明

- **已有 API 行为变更:** 否（framework-internal 存量补录）。注意既有行为：NodeContainerNode OnRecycle/OnReuse **不调基类**（无子递归）；NodeController 无公开复用 API、**不支持跨实例复用**（SDK caveat `NodeController.d.ts:57-62`）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** framework-internal（随 NG 管线）。
- **API 版本号策略:** N/A。

> **不调基类风险（F-nobase）：** `NodeContainerNode::OnRecycle/OnReuse` **不调 FrameNode/UINode 基类**（不递归子节点、不 ClearAccessibilityFocus），与标准 FrameNode 复用语义不同——下游勿假设子节点 OnRecycle 自动触发（风险 RISK-F3-1）。**跨实例复用不支持**：SDK caveat 明确 NodeContainer 不支持跨实例复用，复用单元为 NodeContainerNode FrameNode（RISK-F3-2）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| OnRecycle/OnReuse 不调基类 | 无子递归、无 ClearAccessibilityFocus | AC-1.2,AC-1.4 |
| 复用单元=NodeContainerNode | 非 controller；无公开复用 API；不支持跨实例 | AC-1.6,AC-1.7 |
| surfaceId_ 键 embed node | ElementRegister 双向映射 | AC-2.4,AC-4.1 |
| 防嵌套 | 祖先 NodeContainer 已纹理渲染则不重复 | AC-2.3 |
| start 由 after-layout 驱动 | OnAddBaseNode 仅 stop+set，start 在 OnDirtyLayoutWrapperSwap | AC-3.1,AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | surfaceId_==0/exportTextureNode 无效不触发导出；防嵌套 | UT | `node_container_pattern.cpp:178,100-110` |
| 可维护性 | embed node 双向映射供 accessibility 跨 surface 复用 | 架构评审 | `element_register.cpp:474-514` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | framework-internal 一致 | UT | — |
| 平板 | 无差异 | 同上 | UT | — |
| 折叠屏 | 无差异 | 同上 | UT | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | embed node 经 surfaceId 供 accessibility 跨 surface 边界遍历 | AC-4.2 |
| 大字体 | 否 | 无直接关联 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 否 | framework-internal，随管线演进 | — |
| 生态兼容 | 否 | 无公开 API | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: NodeContainer 复用与纹理导出
  作为 框架维护者
  我想要 NodeContainerNode 经 @Reusable 复用、子节点可纹理导出为 embed node
  以便 可复用容器复用 + 跨 surface 共享渲染

  Scenario Outline: 复用生命周期
    Given NodeContainerNode <事件>
    When @Reusable 触发
    Then <行为>

    Examples:
      | 事件 | 行为 |
      | OnRecycle | destroyCallbacksMap_+ResetGeometryTransition+Pattern::OnRecycle，不调基类 |
      | OnReuse | pattern->OnReuse()(no-op)+debug boundary，不调基类 |

  Scenario: 不支持跨实例复用
    Given NodeController 实例
    When 尝试跨实例复用 NodeContainer
    Then 不支持（SDK caveat），复用单元为 NodeContainerNode FrameNode

  Scenario Outline: 纹理导出触发
    Given 子节点 IsNeedExportTexture=true
    When <时机>
    Then <行为>

    Examples:
      | 时机 | 行为 |
      | OnAddBaseNode | HandleTextureExport(stop)+SetExportTextureInfoIfNeeded |
      | OnDirtyLayoutWrapperSwap(after-layout) | HandleTextureExport(start)+RegisterEmbedNode+DoTextureExport |
      | OnDetachFromFrameNode | HandleTextureExport(stop)+UnregisterEmbedNode |

  Scenario: 防嵌套
    Given 最近祖先 NodeContainer 子已 RENDER_TYPE_TEXTURE
    When SetExportTextureInfoIfNeeded
    Then return（不重复导出）
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 做复用+纹理导出；渲染宿主见 Feat-01、生命周期见 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeContainerNode OnRecycle OnReuse 不调基类 destroyCallbacksMap ResetGeometryTransition"
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeContainerPattern SetExportTextureInfoIfNeeded HandleTextureExport surfaceId_ RegisterEmbedNode DoTextureExport"
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeContainer 纹理导出 防嵌套 OnAddBaseNode OnMountToParentDone OnDirtyLayoutWrapperSwap after-layout"
  - repo: "openharmony/arkui_ace_engine"
    query: "ElementRegister RegisterEmbedNode surfaceIdEmbedNodeMap accessibility GetEmbedNodeBySurfaceId"
```

**关键文档：** `frameworks/core/components_ng/pattern/node_container/node_container_node.cpp`、`frameworks/core/components_ng/pattern/node_container/node_container_pattern.cpp`、`frameworks/core/pipeline/base/element_register.cpp`、`frameworks/core/components_ng/render/adapter/rosen_render_context.cpp`
