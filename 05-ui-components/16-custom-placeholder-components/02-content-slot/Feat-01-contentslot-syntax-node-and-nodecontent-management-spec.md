# 特性规格

> Func-05-16-02-Feat-01 ContentSlot 语法节点与 NodeContent 内容管理：固化 `ContentSlot(content: Content)`（dynamic `@since12`/static `@since23` + `@since26 staticonly` style-builder）、`ContentSlotNode`（**UINode 非 FrameNode**、`"NodeSlot"` tag、`IsSyntaxNode/IsAtomicNode=true`、无 Pattern/Layout）、`NodeContent`（多子节点管理器、`children_` 脱离时为真值源、attach 重放/detach 回收）、所有权守卫（content 仅绑一个 slot、`IsAdopted` 拒绝已领养节点 `ERROR_CODE_NODE_IS_ADOPTED=106206`/`BusinessError 100025`）、生命周期传播（`OnAttachToMainTree`/`OnDetachFromMainTree` 转发 + callbacks）、脏标记双路径（slot 侧 `PROPERTY_UPDATE_BY_CHILD_REQUEST` 上传 + extender 侧 `MEASURE_SELF_AND_PARENT`）、`XComponentType.NODE` 废弃（`@deprecated since 20`→ContentSlot）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ContentSlot 语法节点与 NodeContent 内容管理 |
| 特性编号 | Func-05-16-02-Feat-01 |
| 优先级 | P1 |
| 目标版本 | dynamic `@since12`（ContentSlot/NodeContent/addFrameNode·removeFrameNode，`BusinessError 100025 @since22`）；static `@since23`（ContentSlot/NodeContent 整套）+ `@since26 staticonly`（style-builder + `debugLine`/`setContentSlotOptions`/`applyAttributesFinish`）；`XComponentType.NODE @deprecated since 20` |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。本特性为 Func-05-16-02（ContentSlot）首个 Feat。`Content`/`NodeContent` 为与 `ComponentContent`/NodeContainer 共享的内容管理类型（`@since12`），本规格聚焦 ContentSlot 语法节点 + NodeContent 在 ContentSlot 语境下的行为。NodeContainer（05-16-01）为独立 FuncID。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/16-custom-placeholder-components/02-content-slot/design.md` | Baselined |
| Dynamic API（ContentSlot） | `interface/sdk-js/api/@internal/component/ets/content_slot.d.ts` | — |
| Dynamic API（NodeContent/Content） | `interface/sdk-js/api/arkui/NodeContent.d.ts`、`Content.d.ts` | — |
| Static API | `interface/sdk-js/api/arkui/component/contentSlot.static.d.ets`、`NodeContent.static.d.ets` | — |
| NODE 废弃 | `interface/sdk-js/api/@internal/component/ets/enums.d.ts`（XComponentType.NODE `@deprecated since 20`） | — |
| NG 语法节点 | `frameworks/core/components_ng/syntax/content_slot_node.h` / `content_slot_node.cpp` | — |
| NG Model | `frameworks/core/components_ng/syntax/content_slot_model_ng.h` / `content_slot_model_ng.cpp` | — |
| NodeContent 管理器 | `frameworks/core/components_ng/syntax/node_content.h` / `node_content.cpp` | — |
| JS 桥接 | `frameworks/bridge/declarative_frontend/jsview/js_content_slot.h` / `js_content_slot.cpp` | — |
| NDK Modifier | `frameworks/core/interfaces/native/node/node_content_modifier.cpp` | — |
| Extender Accessor | `frameworks/core/interfaces/native/implementation/node_content_extender_accessor.cpp` | — |
| ANI Modifier | `frameworks/core/interfaces/native/ani/content_slot_ani_modifier.cpp` / `.h` | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 构造与绑定

**作为** 应用开发者,
**我想要** 用 `ContentSlot(content)` 在声明式 UI 中嵌入命令式构建的 NodeContent 子节点,
**以便** 混合开发（ArkTS 容器 + C-API/native 子节点）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN dynamic 调用 `ContentSlot(content: Content)`（`content_slot.d.ts:58-90` `@since12`）THEN 返回 `ContentSlotAttribute`（空类 `:42`，仅占位防递归） | 正常 |
| AC-1.2 | WHEN static 调用 `ContentSlot(content)`（`contentSlot.static.d.ets:81` `@since23` `@ComponentBuilder`）THEN 返回 `ContentSlotAttribute`（`:37-69` 含 `debugLine`/`setContentSlotOptions`/`applyAttributesFinish` `@since26 staticonly`） | 正常 |
| AC-1.3 | WHEN static 用 style-builder `ContentSlot(style)`（`:96` `@since26 staticonly` `@Builder`）THEN 须首调 `setContentSlotOptions(content)`（`:59`）末调 `applyAttributesFinish()`（`:68`） | 边界 |
| AC-1.4 | WHEN `ContentSlotModel::Create(NodeContent* content)`（`content_slot_model_ng.cpp:23-34`）THEN `ClaimNodeId`→`GetOrCreateContentSlot`→`Push`；content 非空→`AttachNodeContent`，null→`DetachNodeContent` | 正常 |
| AC-1.5 | WHEN `AttachNodeContent(content)`（`content_slot_node.h:49-58`）THEN 若旧 `content_` 绑别 slot 则先 `DetachFromNode`；置 `content_`+`AttachToNode(this)`——**所有权守卫：content 仅绑一个 slot** | 正常 |

### US-2: 命令式内容管理（NodeContent）

**作为** 应用开发者,
**我想要** 经 `NodeContent.addFrameNode`/`removeFrameNode` 动态增删子节点,
**以便** 运行时管理 slot 内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调 `NodeContent.addFrameNode(node)`（`NodeContent.d.ts:66` `@since12`，无效节点抛 `BusinessError 100025 @since22`）THEN 经 extender `AddFrameNodeImpl`（`node_content_extender_accessor.cpp:53-76`）→`NodeContent::AddNode`（`node_content.cpp:59-76`）→`slot->AddChild(child,position)`+`children_` 维护 | 正常 |
| AC-2.2 | WHEN `AddNode` THEN 先 `slot->AddChild`+`BuilderUtils::AddBuilderToParent`+`slot->MarkNeedFrameFlushDirty(PROPERTY_UPDATE_BY_CHILD_REQUEST)`（`:66`），后 dedup+`children_.insert`（position=-1 追加） | 正常 |
| AC-2.3 | WHEN 调 `removeFrameNode(node)` THEN `RemoveFrameNodeImpl`（`:78-93`）→`NodeContent::RemoveNode`（`:78-92`）→`slot->RemoveChild`+`BuilderUtils::RemoveBuilderFromParent`+`MarkNeedFrameFlushDirty`+`children_.erase` | 正常 |
| AC-2.4 | WHEN 节点已领养（`IsAdopted()` `ui_node.h:391`）THEN `AddFrameNodeImpl` 返回 `ERROR_CODE_NODE_IS_ADOPTED=106206`（`:60`），TS 映射 `BusinessError(100025)`（`NodeContent.ets:46`）——**IsAdopted 守卫：不可重复领养** | 异常 |
| AC-2.5 | WHEN NDK 路径 `node_content_modifier.cpp:AddChild`（`:24-46`）THEN null 检查+`IsAdopted`→`nodeContent->AddNode`（无额外 MarkDirtyNode，依赖 slot 上传） | 边界 |
| AC-2.6 | WHEN `NodeContent::AddBuilderToSlot()`（`node_content.h:68`）THEN **声明但未实现**（grep 全 frameworks 无 body）——死代码，不做 AC | 边界 |

### US-3: 生命周期传播

**作为** 应用开发者,
**我想要** ContentSlot 进出主树时通知 NodeContent,
**以便** native 侧感知 attach/detach。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN ContentSlotNode `OnAttachToMainTree`（`content_slot_node.h:68-74`）THEN `UINode::OnAttachToMainTree` + 转发 `content_->OnAttachToMainTree()` | 正常 |
| AC-3.2 | WHEN `OnDetachFromMainTree`（`:76-82`）THEN 转发 `content_->OnDetachFromMainTree()` | 正常 |
| AC-3.3 | WHEN `NodeContent::OnAttachToMainTree/OnDetachFromMainTree`（`node_content.cpp:94-114`）THEN `onMainTree_` 守卫防重复；触发 `onAttachCallback_`/`onDetachCallback_` | 边界 |
| AC-3.4 | WHEN NDK `RegisterEvent`（`node_content_modifier.cpp:89-112`）THEN 设 `SetAttachToMainTreeCallback`/`SetDetachFromMainTreeCallback`，事件判别 `{0=attach,1=detach}` | 正常 |

### US-4: 脏标记与重布局

**作为** 框架维护者,
**我想要** 了解 ContentSlot 无 Pattern/Layout 下如何触发重布局,
**以便** 理解子节点增删的渲染影响。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN ContentSlotNode 增删子 THEN **无自身 dirty**（UINode 非 FrameNode，无 Pattern/Layout）；经 `NodeContent::AddNode/RemoveNode`→`slot->MarkNeedFrameFlushDirty(PROPERTY_UPDATE_BY_CHILD_REQUEST)` 上传父链（`ui_node.cpp:1250-1256` `UINode::MarkNeedFrameFlushDirty` 遍历 parent） | 边界 |
| AC-4.2 | WHEN extender ArkTS 路径（`node_content_extender_accessor.cpp:74,90`）THEN 额外对子 FrameNode `MarkDirtyNode(PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT)`——**NDK 路径无此额外标记** | 边界 |
| AC-4.3 | WHEN `NodeContent::AttachToNode`（`node_content.cpp:22-39`）THEN 遍历 `children_`→`node->AddChild`+`MarkNeedFrameFlushDirty(BY_CHILD_REQUEST)`；slot 在主树则 `OnAttachToMainTree` | 正常 |
| AC-4.4 | WHEN `NodeContent::DetachFromNode`（`:41-57`）THEN 回收 `children_ = slot->GetChildren()`+`slot->Clean()`+`OnDetachFromMainTree` | 正常 |

### US-5: 多前端桥接与 static @since26

**作为** 框架维护者,
**我想要** ContentSlot 经 JS/NDK/ANI 多前端绑定 + static @since26 属性面,
**以便** 多范式兼容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN JS 桥接 `JSContentSlot::Create`（`js_content_slot.cpp:35-50`）THEN 读 JS 对象 `nativePtr_` 属性→`reinterpret_cast<NG::NodeContent*>`→`ContentSlotModel::Create(content)` | 正常 |
| AC-5.2 | WHEN NDK `node_content_modifier` vtable（`:134-147`）THEN 暴露 addChild/insertChild/removeChild/registerEvent/setUserData/getUserData（`ArkUINodeContentModifier`+`CJUINodeContentModifier`） | 正常 |
| AC-5.3 | WHEN ANI `ContentSlotConstruct(id)`（`content_slot_ani_modifier.cpp:24-30`）THEN `GetOrCreateContentSlot`+`IncRefCount`→`ArkUIContentSlot`；`SetContentSlotOptions`（`:32-45`）→`AttachNodeContent`/`DetachNodeContent` | 正常 |
| AC-5.4 | WHEN `XComponentType.NODE`（`enums.d.ts:4199`）THEN `@deprecated since 20 @useinstead ContentSlot`——ContentSlot 为 NODE 继任 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.5 | R-1,R-2,R-8 | T-1 | UT + SDK 比对 | `content_slot.d.ts:42-90`、`content_slot_model_ng.cpp:23-34`、`content_slot_node.h:49-58` |
| AC-2.1~2.6 | R-3,R-4,R-9,R-10 | T-1 | UT + XTS：addFrameNode/removeFrameNode/IsAdopted | `node_content.cpp:59-92`、`node_content_extender_accessor.cpp:53-93` |
| AC-3.1~3.4 | R-5 | T-1 | UT：生命周期转发 | `content_slot_node.h:68-82`、`node_content.cpp:94-114` |
| AC-4.1~4.4 | R-6,R-7 | T-1 | UT：脏标记/attach·detach 重放 | `node_content.cpp:22-57,66,85`、`ui_node.cpp:1250-1256` |
| AC-5.1~5.4 | R-11,R-12 | T-1 | UT + SDK：JS/NDK/ANI + NODE 废弃 | `js_content_slot.cpp:35-50`、`content_slot_ani_modifier.cpp:24-45`、`enums.d.ts:4199` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | ContentSlot(content) | 返回 ContentSlotAttribute；Create 经 ClaimNodeId+GetOrCreate+Push+attach/detach | dyn @since12/static @since23 | AC-1.1,AC-1.2,AC-1.4 |
| R-2 | 行为 | AttachNodeContent | 所有权守卫：旧 content 绑别 slot 则先 detach；content 仅绑一个 slot | — | AC-1.5 |
| R-3 | 行为 | addFrameNode | AddNode→slot AddChild+children_ 维护+BY_CHILD_REQUEST | 无效节点 BusinessError 100025 @since22 | AC-2.1,AC-2.2 |
| R-4 | 异常 | IsAdopted 节点 | ERROR_CODE_NODE_IS_ADOPTED=106206/BusinessError 100025 | 不可重复领养 | AC-2.4 |
| R-5 | 行为 | OnAttachToMainTree/Detach | ContentSlotNode 转发给 NodeContent；onMainTree_ 守卫+callbacks | — | AC-3.1~3.3 |
| R-6 | 边界 | ContentSlotNode 无 dirty | UINode 非 FrameNode；经 MarkNeedFrameFlushDirty(BY_CHILD_REQUEST) 上传父链 | — | AC-4.1 |
| R-7 | 行为 | extender 脏标记 | 子 FrameNode MarkDirtyNode(MEASURE_SELF_AND_PARENT)；NDK 路径无此额外 | 两路径差异 | AC-4.2 |
| R-8 | 边界 | static style-builder | 须 setContentSlotOptions+applyAttributesFinish | @since26 staticonly | AC-1.3 |
| R-9 | 行为 | removeFrameNode | RemoveNode→slot RemoveChild+children_.erase | — | AC-2.3 |
| R-10 | 边界 | AddBuilderToSlot | 声明但未实现（死代码） | 不做 AC | AC-2.6 |
| R-11 | 行为 | NodeContent attach/detach 重放 | attach→children_ replay AddChild；detach→reclaim children_+Clean | children_ 为脱离时真值源 | AC-4.3,AC-4.4 |
| R-12 | 行为 | XComponentType.NODE | @deprecated since 20 @useinstead ContentSlot | 继任 | AC-5.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 构造/绑定 | UT + SDK | ContentSlot/NodeContent、所有权守卫、@since12/23/26 |
| VM-2 | AC-2.x 内容管理 | UT + XTS | addFrameNode/removeFrameNode、IsAdopted 106206/100025、AddBuilderToSlot 死代码 |
| VM-3 | AC-3.x 生命周期 | UT | OnAttachToMainTree/Detach 转发、onMainTree_ 守卫 |
| VM-4 | AC-4.x 脏标记 | UT | BY_CHILD_REQUEST 上传、extender MEASURE_SELF_AND_PARENT、attach/detach 重放 |
| VM-5 | AC-5.x 多前端/NODE 废弃 | UT + SDK | JS/NDK/ANI 桥接、NODE @deprecated since 20 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `ContentSlot(content)`（dyn `@since12`/static `@since23`） | 既有 | 声明式占位 | — | AC-1.1,AC-1.2 |
| `ContentSlot(style)` + `setContentSlotOptions`/`applyAttributesFinish`/`debugLine`（static `@since26 staticonly`） | 既有 | 静态 style-builder | 须 setContentSlotOptions+applyAttributesFinish | AC-1.3 |
| `NodeContent.addFrameNode`/`removeFrameNode`（dyn `@since12`，无效→`BusinessError 100025 @since22`） | 既有 | 命令式内容管理 | IsAdopted→106206 | AC-2.1,AC-2.4 |
| `XComponentType.NODE` | 废弃（`@deprecated since 20`） | 命令式挂载 | `@useinstead ContentSlot` | AC-5.4 |

> SDK：dynamic `content_slot.d.ts:42-90`、`NodeContent.d.ts:40-78`；static `contentSlot.static.d.ets:37-99`；废弃 `enums.d.ts:4199`。

## 接口规格

### 接口定义

**ContentSlot（dynamic，`content_slot.d.ts:90`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `declare const ContentSlot: ContentSlotInterface`（`(content: Content): ContentSlotAttribute`） |
| 返回值 | `ContentSlotAttribute`（dyn 空类；static 含 3 方法 `@since26 staticonly`） |
| 开放范围 | Public（`@since12`，`@noninterop`、stagemodelonly、crossplatform、atomicservice） |
| 错误码 | addFrameNode 无效/IsAdopted→`BusinessError 100025`（`@since22`）/`ERROR_CODE_NODE_IS_ADOPTED=106206` |
| 关联 AC | AC-1.1,AC-2.1,AC-2.4 |

**NodeContent（`NodeContent.d.ts:40`）**

| 属性 | 值 |
|------|-----|
| 方法 | `constructor()`、`addFrameNode(node: FrameNode): void`、`removeFrameNode(node: FrameNode): void` |
| 开放范围 | Public（`@since12`） |
| 错误码 | 无效节点→`BusinessError 100025`（`@since22`） |
| 关联 AC | AC-2.1,AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| content | Content（NodeContent） | 是 | — | 须 NodeContent 实例；仅绑一个 slot |
| node（addFrameNode） | FrameNode | 是 | — | 须未被领养（IsAdopted=false）；否则 106206/100025 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | content 绑别 slot 后再绑新 slot | 旧 slot 先 DetachFromNode | AC-1.5 |
| 2 | addFrameNode 已领养节点 | ERROR_CODE_NODE_IS_ADOPTED/BusinessError 100025 | AC-2.4 |
| 3 | ContentSlot 进主树 | 转发 NodeContent OnAttachToMainTree+callback | AC-3.1 |
| 4 | 增删子节点 | slot MarkNeedFrameFlushDirty(BY_CHILD_REQUEST) 上传父链；extender 额外 MEASURE_SELF_AND_PARENT | AC-4.1,AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。注意既有行为：ContentSlotNode 为 **UINode 非 FrameNode**（无 Pattern/Layout，经上传父链重布局）；NodeContent `children_` 为脱离时真值源（attach 重放/detach 回收）；extender ArkTS 路径额外 `MarkDirtyNode(MEASURE_SELF_AND_PARENT)` 而 NDK 路径无；`AddBuilderToSlot()` 声明但未实现（死代码）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic `@since12`；static `@since23`；style-builder `@since26 staticonly`。
- **API 版本号策略:** 按 SDK `@since12/22/23/26` 标注。

> **UINode 非 FrameNode 风险（F-uinode）：** ContentSlotNode 继承 UINode 而非 FrameNode（`content_slot_node.h:30`），**无 Pattern/Layout/EventHub**，子节点增删经 `MarkNeedFrameFlushDirty(PROPERTY_UPDATE_BY_CHILD_REQUEST)` 上传父链到最近 FrameNode 祖先触发重布局（`ui_node.cpp:1250-1256`）——与 NodeContainer（FrameNode，自带 Layout）架构不同（风险 RISK-1）。**两路径脏标记差异**：extender ArkTS 路径对子 FrameNode 额外 `MarkDirtyNode(MEASURE_SELF_AND_PARENT)`（`node_content_extender_accessor.cpp:74,90`），NDK 路径无此额外标记（RISK-2）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| ContentSlotNode = UINode | 非 FrameNode、无 Pattern/Layout、IsSyntaxNode/IsAtomicNode | AC-4.1 |
| 所有权守卫 | content 仅绑一个 slot（AttachNodeContent 先 detach 旧） | AC-1.5 |
| IsAdopted 守卫 | 已领养节点不可重复 addFrameNode（106206/100025） | AC-2.4 |
| children_ 重放/回收 | attach→AddChild replay；detach→reclaim+Clean | AC-4.3,AC-4.4 |
| 两路径脏标记 | extender MEASURE_SELF_AND_PARENT vs NDK 仅 BY_CHILD_REQUEST | AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | IsAdopted 守卫防重复领养；所有权守卫防多 slot 绑定 | UT 异常 | `node_content_extender_accessor.cpp:60`、`content_slot_node.h:49-58` |
| 性能 | UINode 非 FrameNode 无布局开销；脏标记上传父链 | UT | `ui_node.cpp:1250-1256` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 无差异 | 同上 | XTS | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 子 FrameNode 入无障碍树 | — |
| 大字体 | 否 | 无独立处理 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | dyn `@since12/22`、static `@since23/26 staticonly`；`XComponentType.NODE @deprecated since 20` | AC-1.1,AC-5.4 |
| 生态兼容 | 是 | dyn `@since12`、crossplatform、atomicservice | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: ContentSlot 语法节点与 NodeContent 内容管理
  作为 应用开发者
  我想要 用 ContentSlot(content) 嵌入命令式 NodeContent 子节点
  以便 混合开发（ArkTS 容器 + native 子节点）

  Scenario: 所有权守卫
    Given NodeContent 已绑 slotA
    When 绑 slotB
    Then slotA 先 DetachFromNode，slotB AttachNodeContent

  Scenario: IsAdopted 守卫
    Given FrameNode 已被领养（IsAdopted=true）
    When addFrameNode(node)
    Then ERROR_CODE_NODE_IS_ADOPTED(106206)/BusinessError(100025)

  Scenario: 生命周期转发
    Given ContentSlotNode 进主树
    When OnAttachToMainTree
    Then 转发 content_->OnAttachToMainTree()+onAttachCallback_

  Scenario Outline: 脏标记路径
    Given 增删子节点
    When <路径>
    Then <标记>

    Examples:
      | 路径 | 标记 |
      | slot 侧 | MarkNeedFrameFlushDirty(BY_CHILD_REQUEST) 上传父链 |
      | extender ArkTS | 额外 MarkDirtyNode(MEASURE_SELF_AND_PARENT) |
      | NDK | 仅 slot 上传，无额外 |

  Scenario: attach/detach 重放
    Given NodeContent children_ 有 3 项
    When AttachToNode(slot)
    Then 3 项 replay slot->AddChild
    When DetachFromNode
    Then reclaim children_+slot->Clean()
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做 ContentSlot 语法节点+NodeContent 管理；NodeContainer 见 05-16-01）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ContentSlotNode UINode 非 FrameNode IsSyntaxNode IsAtomicNode AttachNodeContent 所有权守卫"
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeContent AddNode RemoveNode children_ AttachToNode DetachFromNode replay reclaim"
  - repo: "openharmony/arkui_ace_engine"
    query: "node_content_extender_accessor AddFrameNodeImpl IsAdopted ERROR_CODE_NODE_IS_ADOPTED 106206 MarkDirtyNode"
  - repo: "openharmony/arkui_ace_engine"
    query: "ContentSlotNode MarkNeedFrameFlushDirty PROPERTY_UPDATE_BY_CHILD_REQUEST 上传父链 UINode"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/content_slot.d.ts`、`frameworks/core/components_ng/syntax/content_slot_node.h`、`frameworks/core/components_ng/syntax/node_content.cpp`、`frameworks/core/interfaces/native/implementation/node_content_extender_accessor.cpp`
