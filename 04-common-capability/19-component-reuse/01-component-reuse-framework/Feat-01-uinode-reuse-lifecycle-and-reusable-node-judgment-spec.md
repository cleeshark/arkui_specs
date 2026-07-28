# 特性规格

> Func-04-19-01-Feat-01 UINode 复用生命周期与可复用节点判定：固化引擎侧 C++ 复用生命周期——`UINode::OnRecycle/OnReuse` virtual（递归子节点默认实现、节点可覆写）、`IsReusableNode` 判定（isCNode_/isArkTsFrameNode_/isRootBuilderNode_/isArkTsRenderNode_ 四标志 OR、各创建路径设置）、`AllowReusableV2Descendant` 门控（Repeat 模板内禁用 @ReusableV2）、`CustomNodeBase` 回调槽与生命周期驱动（`FireRecycleSelf`/`FireRecycleRenderFunc` 序列、LifeCycleEvent 枚举、reuseId/creatorId/recycleInfo_）、C++ `RecycleManager`（pipeline-owned，**非 TS RecycleManager**，config-change 延迟交付）、销毁与可复用节点清理（`ProcessIsInDestroyingForReuseableNode`）行为规格。本特性 framework-internal（源码即规格，无 SDK 公开 API）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UINode 复用生命周期与可复用节点判定 |
| 特性编号 | Func-04-19-01-Feat-01 |
| 优先级 | P1 |
| 目标版本 | framework-internal（随 NG 渲染管线，无独立 `@since`；无 API 版本门控） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。本特性为 Func-04-19-01（组件复用框架）首个 Feat，作为该功能域 design.md 基线。reuseId 节点池与桥接（Feat-02）、RecycleDummyNode/DisableRecycle（Feat-03）、@since26 公开池 API 与内存优化（Feat-04）由后续 Feat 承接。TS `@Reusable`/`@ReusableV2` 装饰器与 state-mgmt 池由 07-03-03 承接，本特性仅覆盖引擎侧 C++ 框架。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/19-component-reuse/01-component-reuse-framework/design.md` | Baselined |
| UINode 基类（复用 virtual/标志） | `frameworks/core/components_ng/base/ui_node.h` / `ui_node.cpp` | — |
| CustomNodeBase（回调槽/驱动） | `frameworks/core/components_ng/pattern/custom/custom_node_base.h` / `custom_node_base.cpp` | — |
| C++ RecycleManager | `frameworks/core/components_ng/pattern/recycle_view/recycle_manager.h` / `recycle_manager.cpp` | — |
| AllowReusableV2Descendant 消费方 | `frameworks/core/components_ng/base/view_partial_update_model_ng.cpp` | — |
| PipelineContext（RecycleManager 持有） | `frameworks/core/pipeline_ng/pipeline_context.h` / `pipeline_context.cpp` | — |
| 各节点创建路径（标志设置证据） | `arkts_native_frame_node_bridge.cpp`、`frame_node_modifier.cpp`、`arkts_native_render_node_bridge.cpp`、`js_base_node.cpp`、`node_api.cpp` | — |

> 需求基线、不涉及项详见 proposal.md。本特性 framework-internal，源码即规格，无 SDK 公开 API 交叉校验。

---

## 用户故事

### US-1: UINode 复用生命周期 virtual

**作为** 框架维护者,
**我想要** UINode 提供 OnRecycle/OnReuse 生命周期 virtual,
**以便** 复用框架驱动节点子树的回收/复用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 复用框架触发回收 THEN `UINode::OnRecycle()`（`ui_node.h:536-538` 声明、`ui_node.cpp:2209-2214` 实现）**递归遍历子节点**调 `child->OnRecycle()` | 正常 |
| AC-1.2 | WHEN 复用框架触发复用 THEN `UINode::OnReuse()`（`ui_node.cpp:2252-2257`）**递归遍历子节点**调 `child->OnReuse()` | 正常 |
| AC-1.3 | WHEN 子类覆写 OnRecycle/OnReuse THEN 可改变递归行为（如 NodeContainerNode 不调基类、不递归子） | 边界 |
| AC-1.4 | WHEN `UpdateRecycleElmtId(newElmtId)`（`ui_node.h:651-654`）THEN 重写 `nodeId_=newElmtId`（复用后更新 elmtId） | 正常 |

### US-2: IsReusableNode 判定与节点类型标志

**作为** 框架维护者,
**我想要** 统一判定节点是否可复用,
**以便** 复用框架区分可复用节点（C-API/FrameNode/BuilderNode/RenderNode）与声明式节点。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `IsReusableNode()`（`ui_node.h:956-959`）THEN 返回 `isCNode_ \|\| isArkTsFrameNode_ \|\| isRootBuilderNode_ \|\| isArkTsRenderNode_`（四标志 OR） | 正常 |
| AC-2.2 | WHEN C-API 创建节点 THEN `setIsCNode(true)`（`node_api.cpp:260`） | 正常 |
| AC-2.3 | WHEN ArkTS FrameNode bridge/extender 或 C-API frame_node 创建 THEN `SetIsArkTsFrameNode(true)`（`arkts_native_frame_node_bridge.cpp:298,325,498,720`、`frame_node_modifier.cpp:80`、`frame_node_extender_accessor.cpp:198,1342,1572`） | 正常 |
| AC-2.4 | WHEN RenderNode 创建 THEN `SetIsArkTsRenderNode(true)`（`arkts_native_render_node_bridge.cpp:181`、`render_node_peer_impl.h:43,51`） | 正常 |
| AC-2.5 | WHEN BuilderNode 创建 THEN `SetIsRootBuilderNode(true)`（`js_base_node.cpp:244`、`builder_node_ops_accessor.cpp:96,390,393`） | 正常 |
| AC-2.6 | WHEN 四标志皆假（声明式节点）THEN `IsReusableNode()` 返回 false，不可入复用池 | 边界 |

### US-3: AllowReusableV2Descendant 门控

**作为** 框架维护者,
**我想要** Repeat 模板内能禁用 @ReusableV2 复用,
**以便** Repeat 自身复用池为唯一复用路径，避免与 @ReusableV2 冲突。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 节点设 `SetAllowReusableV2Descendant(allow)`（`ui_node.h:1001-1008`，成员 `allowReusableV2Descendant_` 默认 **true** `:1416`）THEN 置标志（`ui_node.cpp:2828-2836`） | 正常 |
| AC-3.2 | WHEN `AllowReusableV2Descendant`（`view_partial_update_model_ng.cpp:125-147`）判定 THEN 沿父链走到 `RepeatVirtualScrollNode`/`RepeatVirtualScroll2Node`/`JS_VIEW_ETS_TAG`/null；结果 = 停在 root/JSView **或** 停止祖先的 `IsAllowReusableV2Descendant()` 为 true | 正常 |
| AC-3.3 | WHEN RepeatVirtualScroll 祖先 `allowReusableV2Descendant_=false` THEN `AllowReusableV2Descendant` 返回 false，该子树 @ReusableV2/@ComponentV2 不能按 reuseId 入复用池 | 边界 |

### US-4: CustomNodeBase 回调槽与生命周期驱动

**作为** 框架维护者,
**我想要** CustomNodeBase 提供回收/复用回调槽与生命周期驱动,
**以便** 连接引擎复用框架与 TS @Reusable 回调。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN CustomNodeBase 持有回调槽 THEN `recycleCustomNodeFunc_`/`recycleRenderFunc_`/`clearAllRecycleFunc_`/`onRecycleFunc_`/`onReuseFunc_`（`custom_node_base.h:189-198`）+`SetOnRecycleFunc`/`FireOnRecycleFunc`/`SetOnReuseFunc`/`FireOnReuseFunc`（`:97-110`） | 正常 |
| AC-4.2 | WHEN `FireRecycleSelf()`（`custom_node_base.cpp:347-356`）THEN 序列：`UINode::OnRecycle()`（递归子）→若有 TS 回调：`recycleInfo_.Recycle(id)`+`RecycleManager::Push(id,WeakClaim(this))`+`recycleCustomNodeFunc_` | 正常 |
| AC-4.3 | WHEN `FireRecycleRenderFunc()`（复用路径，`:358-372`）THEN 序列：`recycleInfo_.Reuse()`+`RecycleManager::Pop(id)`（replay config）→`ScopedViewStackProcessor` 内 `recycleRenderFunc_()`（re-render）→`UINode::OnReuse()`→`SetJSViewActive(true,false,true)`（isReuse/suppressActiveLifecycle）→清 `recycleRenderFunc_` | 正常 |
| AC-4.4 | WHEN LifeCycleEvent 枚举 THEN `ON_APPEAR=0/ON_BUILD=1/ON_RECYCLE=2/ON_REUSE=3/ON_DISAPPEAR=4`（`custom_node_base.h:149-155`），`FireTriggerLifecycleFunc(eventId)` 派发 | 正常 |
| AC-4.5 | WHEN reuseId/creatorId THEN `SetReuseId/GetReuseId/SetCreatorId/GetCreatorId`（`:159-163`，成员 `reuseId_:176`/`creatorId_:177`） | 正常 |
| AC-4.6 | WHEN `FireClearAllRecycleFunc()`（`:296-303`）THEN `RecycleManager::ClearAll()`+`clearAllRecycleFunc_` | 正常 |
| AC-4.7 | WHEN CustomNodeBase 析构（`:23-38`）THEN `RecycleManager::Erase(recycleInfo_.elemtId)`（移除陈旧条目） | 正常 |

### US-5: C++ RecycleManager 与 config-change 延迟交付

**作为** 框架维护者,
**我想要** pipeline 级 C++ RecycleManager 记录回收期 config 变更并在复用时 replay,
**以便** 回收节点不丢失配置更新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 节点回收 THEN `RecycleManager::Push(elmtId,WeakPtr<CustomNodeBase>)`（`recycle_manager.h:53-68` 静态门面→pipeline 单例；`PushNode recycle_manager.cpp:58-61` `try_emplace`） | 正常 |
| AC-5.2 | WHEN 节点复用 THEN `RecycleManager::Pop(elmtId)`（`PopNode :68-81`）：若池条目 `config.IsNeedUpdate()` 则 `UINode::UpdateConfigurationUpdate(config)` replay 后 erase | 正常 |
| AC-5.3 | WHEN 配置变更（onShow 分支）THEN `RecycleManager::Notify(configurationChange)`（`pipeline_context.cpp:5924`）→`NotifyConfigurationChange`（`recycle_manager.cpp:88-93`）合并入**所有**池节点 `RecycleNodeState.config` | 正常 |
| AC-5.4 | WHEN RecycleManager 持有 THEN pipeline-owned（`PipelineContext::recycleManager_` `pipeline_context.h:877,1624`，pipeline 构造时 `make_unique`）；**非 TS RecycleManager**（TS 侧 @Reusable 池见 07-03-03） | 边界 |
| AC-5.5 | WHEN RecycleNodeInfo（每节点，存 CustomNodeBase `recycleInfo_` `:202`）THEN `elemtId`/`hasBeenRecyled`，`Recycle(id)` 标回收、`Reuse()` 清（`recycle_manager.h:39-52`） | 正常 |

### US-6: 销毁与可复用节点清理

**作为** 框架维护者,
**我想要** 可复用节点不被父销毁遍历误清,
**以便** 复用节点销毁标志正确管理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 子节点挂入父（`ui_node.cpp:771,840`）THEN 调 `ProcessIsInDestroyingForReuseableNode(child)`（`ui_node.h:1098`/`cpp:2869-2877`）：子可复用且父非销毁而子销毁则 `child->SetDestroying(false,false)` | 正常 |
| AC-6.2 | WHEN `UINode::SetDestroying`（`ui_node.cpp:2838-2853`）递归 THEN 可复用子 `SetDestroying(isDestroying,false)`、其余 `(isDestroying,cleanStatus)` | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.4 | R-1 | T-1 | UT：UINode OnRecycle/OnReuse 递归 | `ui_node.cpp:2209-2257,651-654` |
| AC-2.1~2.6 | R-2,R-3 | T-1 | UT：IsReusableNode + 各创建路径标志 | `ui_node.h:956-959,1375-1394`、`node_api.cpp:260` 等 |
| AC-3.1~3.3 | R-4 | T-1 | UT：AllowReusableV2Descendant 门控 | `ui_node.h:1001-1008`、`view_partial_update_model_ng.cpp:125-147` |
| AC-4.1~4.7 | R-5,R-6 | T-1 | UT：CustomNodeBase FireRecycleSelf/FireRecycleRenderFunc | `custom_node_base.cpp:347-372,296-303` |
| AC-5.1~5.5 | R-7,R-8 | T-1 | UT：C++ RecycleManager Push/Pop/Notify | `recycle_manager.cpp:58-93`、`pipeline_context.cpp:5924` |
| AC-6.1~6.2 | R-9 | T-1 | UT：ProcessIsInDestroyingForReuseableNode | `ui_node.cpp:2869-2877,2838-2853` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | OnRecycle/OnReuse | 递归遍历子节点；子类可覆写改变行为 | 非纯虚，有默认实现 | AC-1.1~1.3 |
| R-2 | 行为 | IsReusableNode | 四标志 OR（isCNode_/isArkTsFrameNode_/isRootBuilderNode_/isArkTsRenderNode_） | 默认全 false | AC-2.1,AC-2.6 |
| R-3 | 行为 | 标志设置 | 各创建路径设对应标志 true（C-API/FrameNode/RenderNode/BuilderNode） | 声明式节点不设 | AC-2.2~2.5 |
| R-4 | 边界 | AllowReusableV2Descendant | 默认 true；RepeatVirtualScroll 祖先 false 则禁用子树 @ReusableV2 reuseId 复用 | 沿父链走到 Repeat/JSView | AC-3.1~3.3 |
| R-5 | 行为 | FireRecycleSelf | OnRecycle→recycleInfo_.Recycle+RecycleManager::Push+TS 回调 | 仅在有 TS 回调时入池 | AC-4.2 |
| R-6 | 行为 | FireRecycleRenderFunc | Reuse+Pop(replay config)+re-render+OnReuse+SetJSViewActive(true,false,true) | 复用驱动 | AC-4.3 |
| R-7 | 行为 | C++ RecycleManager | pipeline-owned；Push/Pop/Erase/Notify/ClearAll；Pop replay config | 非 TS RecycleManager | AC-5.1,AC-5.2,AC-5.4 |
| R-8 | 行为 | config-change 延迟交付 | Notify 合并入所有池节点；复用 Pop replay | 回收期不丢配置 | AC-5.3 |
| R-9 | 行为 | ProcessIsInDestroyingForReuseableNode | 可复用子+父非销毁+子销毁→清子销毁标志；SetDestroying 可复用子不 cleanStatus | 避免误清 | AC-6.1,AC-6.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 生命周期 virtual | UT | 递归默认实现、覆写 |
| VM-2 | AC-2.x IsReusableNode | UT | 四标志 OR、各创建路径 |
| VM-3 | AC-3.x AllowReusableV2Descendant | UT | 门控、Repeat 祖先 false |
| VM-4 | AC-4.x CustomNodeBase | UT | FireRecycleSelf/FireRecycleRenderFunc 序列 |
| VM-5 | AC-5.x C++ RecycleManager | UT | Push/Pop/Notify config replay |
| VM-6 | AC-6.x 销毁清理 | UT | ProcessIsInDestroyingForReuseableNode |

## API 变更分析

> 本特性 framework-internal，无公开 API 变更（UINode/CustomNodeBase/RecycleManager 为内部 C++ 类，非 SDK 契约）。

### 新增 API

N/A（framework-internal）。

### 变更/废弃 API

N/A。

## 接口规格

> framework-internal，无公开接口规格（内部 C++ 契约）。核心内部契约见「规则定义」与各 `ui_node.h`/`custom_node_base.h`/`recycle_manager.h`。

## 兼容性声明

- **已有 API 行为变更:** 否（framework-internal 存量补录）。注意既有行为：UINode OnRecycle/OnReuse **递归子节点**（子类可覆写，如 NodeContainerNode 不调基类）；C++ `RecycleManager`（pipeline-owned，config-change 延迟交付）**非** TS `RecycleManager`（07-03-03）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** framework-internal（随 NG 管线，无独立版本）。
- **API 版本号策略:** N/A（内部类，无 API 版本门控）。

> **C++ RecycleManager ≠ TS RecycleManager 风险（F-cppmgr）：** 引擎侧 `RecycleManager`（`pattern/recycle_view/recycle_manager.*`，pipeline-owned，记录回收期 config 变更并在复用 Pop 时 replay）与 07-03-03 的 TS `RecycleManager`（state-mgmt 层 @Reusable 池）是**两个不同类**，下游勿混淆（风险 RISK-1）。OnRecycle/OnReuse 递归子节点为默认行为，子类（如 NodeContainerNode）可覆写不递归（RISK-2）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| OnRecycle/OnReuse 递归默认 | 子节点遍历，子类可覆写 | AC-1.1~1.3 |
| IsReusableNode 四标志 OR | 区分命令式可复用 vs 声明式 | AC-2.1 |
| AllowReusableV2Descendant 门控 | Repeat 模板内禁用 @ReusableV2 | AC-3.3 |
| FireRecycleSelf/FireRecycleRenderFunc 驱动 | 引擎↔TS 回调连接 | AC-4.2,AC-4.3 |
| C++ RecycleManager config 延迟交付 | 回收期 config 不丢 | AC-5.2,AC-5.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 可复用节点销毁标志不被父误清（ProcessIsInDestroyingForReuseableNode） | UT | `ui_node.cpp:2869-2877` |
| 可维护性 | pipeline 级 C++ RecycleManager 集中管理回收 config，复用 replay | 架构评审 | `recycle_manager.cpp:58-93` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | framework-internal 一致 | UT | — |
| 平板 | 无差异 | 同上 | UT | — |
| 折叠屏 | 无差异 | 同上 | UT | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | framework-internal | — |
| 大字体 | 是 | config-change（含字体）经 RecycleManager 延迟交付并 replay | AC-5.3 |
| 深色模式 | 是 | config-change 经 RecycleManager 延迟交付 | AC-5.3 |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 否 | framework-internal，随管线演进 | — |
| 生态兼容 | 否 | 无公开 API | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: UINode 复用生命周期与可复用节点判定
  作为 框架维护者
  我想要 引擎侧 C++ 复用框架驱动节点回收/复用
  以便 命令式可复用节点正确回收复用

  Scenario Outline: OnRecycle/OnReuse
    Given UINode <事件>
    When 复用框架触发
    Then <行为>

    Examples:
      | 事件 | 行为 |
      | OnRecycle | 递归子节点 child->OnRecycle() |
      | OnReuse | 递归子节点 child->OnReuse() |

  Scenario: IsReusableNode 判定
    Given 节点创建路径
    When 检查四标志
    Then C-API/FrameNode/RenderNode/BuilderNode 任一 true → IsReusableNode=true

  Scenario: AllowReusableV2Descendant 门控
    Given RepeatVirtualScroll 祖先 allowReusableV2Descendant_=false
    When AllowReusableV2Descendant 判定
    Then 返回 false，子树 @ReusableV2 不能按 reuseId 入池

  Scenario: FireRecycleSelf 序列
    Given CustomNodeBase 回收
    When FireRecycleSelf
    Then OnRecycle→recycleInfo_.Recycle+RecycleManager::Push+TS 回调

  Scenario: config-change 延迟交付
    Given 节点回收期发生配置变更
    When RecycleManager::Notify
    Then 合并入池节点 config；复用 Pop 时 replay UpdateConfigurationUpdate
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做 UINode 复用生命周期/判定/门控/驱动/C++ RecycleManager；池与桥接见 Feat-02、RecycleDummyNode 见 Feat-03、@since26 公开 API 见 Feat-04；TS @Reusable 见 07-03-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "UINode OnRecycle OnReuse 递归子节点 默认实现 覆写"
  - repo: "openharmony/arkui_ace_engine"
    query: "UINode IsReusableNode isCNode isArkTsFrameNode isRootBuilderNode isArkTsRenderNode 标志设置路径"
  - repo: "openharmony/arkui_ace_engine"
    query: "CustomNodeBase FireRecycleSelf FireRecycleRenderFunc OnRecycle RecycleManager Push Pop 序列"
  - repo: "openharmony/arkui_ace_engine"
    query: "C++ RecycleManager pipeline_context NotifyConfigurationChange PopNode replay config 非 TS RecycleManager"
```

**关键文档：** `frameworks/core/components_ng/base/ui_node.h`、`frameworks/core/components_ng/pattern/custom/custom_node_base.cpp`、`frameworks/core/components_ng/pattern/recycle_view/recycle_manager.cpp`、`frameworks/core/components_ng/base/view_partial_update_model_ng.cpp`
