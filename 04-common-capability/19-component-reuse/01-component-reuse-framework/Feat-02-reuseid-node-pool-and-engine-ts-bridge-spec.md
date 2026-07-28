# 特性规格

> Func-04-19-01-Feat-02 reuseId 节点池与 engine↔TS 桥接：固化引擎侧 C++ reuseId 节点池（`LazyForEachBuilder::recyclableNodeSet_` 双层 map：reuseId→itemKey→WeakPtr<UINode> 集；`RecordRecyclableNode`/`TryRecordRecyclableNodeRecursively`/`ReleaseExpiringNode(reuseId)`/`GetReuseIdsCanBeRecycled`）、JS 桥接（`JSView` CreateRecycle 包装 RecycleDummyNode+SetReuseId、`TryReleaseExpiringNode`）、TS hooks（`__releaseRecyclePool__Internal`/`__enableReleaseExpiringNodes__Internal`/`__ClearAllRecyle__PUV2ViewBase__Internal`）、`CustomNode::EnableReleaseExpiringNode`/`DisableReleaseExpiringNode`/`ReleaseExpiringNode(reuseId)` 行为规格。本特性 framework-internal（源码即规格，无 SDK 公开 API）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | reuseId 节点池与 engine↔TS 桥接 |
| 特性编号 | Func-04-19-01-Feat-02 |
| 优先级 | P1 |
| 目标版本 | framework-internal（随 NG 渲染管线，无独立 `@since`） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-01（UINode 复用生命周期）；本特性聚焦 C++ reuseId 节点池与 engine↔TS 桥接。RecycleDummyNode/DisableRecycle（Feat-03）、@since26 公开池 API（Feat-04）由后续 Feat 承接。TS @Reusable 池逻辑（RecyclePoolV2/__ReusePool__）由 07-03-03 承接。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/19-component-reuse/01-component-reuse-framework/design.md` | Baselined |
| C++ 节点池（LazyForEachBuilder） | `frameworks/core/components_ng/syntax/lazy_for_each_builder.h` / `lazy_for_each_builder.cpp` | — |
| JS 桥接（JSView） | `frameworks/bridge/declarative_frontend/jsview/js_view.cpp` / `js_view.h` | — |
| JS ViewFunctions 桥接 | `frameworks/bridge/declarative_frontend/jsview/js_view_functions.cpp` | — |
| CustomNode 释放 | `frameworks/core/components_ng/pattern/custom/custom_node.cpp` / `custom_node.h` | — |
| NG Model（TryReleaseExpiringNode） | `frameworks/core/components_ng/base/view_partial_update_model_ng.cpp` / `view_partial_update_model.h` | — |
| Cangjie 镜像 | `frameworks/bridge/cj_frontend/cppview/native_view.cpp` | — |

> 需求基线详见 proposal.md。本特性 framework-internal，源码即规格。

---

## 用户故事

### US-1: C++ reuseId 节点池

**作为** 框架维护者,
**我想要** 引擎侧维护 reuseId→itemKey→节点的池,
**以便** LazyForEach/Repeat 离屏节点按 reuseId 复用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN LazyForEachBuilder 持有 reuseId 池 THEN `recyclableNodeSet_`（`lazy_for_each_builder.h:385`）为 `std::map<string, std::map<string, std::set<WeakPtr<UINode>>>>`（外层 key=reuseId、内层 key=itemKey） | 正常 |
| AC-1.2 | WHEN `RecordRecyclableNode(reuseId,key,node)`（`lazy_for_each_builder.cpp:1577`）THEN 按 reuseId+key 记入 `recyclableNodeSet_` | 正常 |
| AC-1.3 | WHEN `TryRecordRecyclableNodeRecursively`（`:1597`）THEN 遍历 `RECYCLE_VIEW_ETS_TAG`（RecycleDummyNode）子节点递归记录可回收节点 | 正常 |
| AC-1.4 | WHEN `ReleaseExpiringNode(reuseId)`（`:1533`）THEN 按 reuseId 释放池中节点（父 CustomNode 请求时批量释放，`MIN_RELEASE_COUNT=5`） | 正常 |
| AC-1.5 | WHEN `GetReuseIdsCanBeRecycled()`（`:1615`）THEN 返回池中存在可回收节点的 reuseId 集（供父 CustomNode 决策释放） | 正常 |

### US-2: JS 桥接（CreateRecycle/TryReleaseExpiringNode）

**作为** 框架维护者,
**我想要** JSView 桥接 TS @Reusable 与引擎池,
**以便** TS 回收/释放经引擎执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `JSViewPartialUpdate::CreateRecycle`（`js_view.cpp:1166-1286`）THEN 包装节点入 `RecycleDummyNode`+`SetReuseId(nodeName)`（`:1281`）+接 recycle/reuse 回调（`:780-879`） | 正常 |
| AC-2.2 | WHEN `JSView::TryReleaseExpiringNode`（`js_view.cpp`）THEN 经 `ViewPartialUpdateModelNG::TryReleaseExpiringNode(node,reuseId)`（`view_partial_update_model_ng.cpp:111`）→`CustomNode::ReleaseExpiringNode(reuseId)` | 正常 |
| AC-2.3 | WHEN NodeInfoPU 构造（`view_partial_update_model.h:32-58`）THEN 含所有 recycle/reuse 回调签名（recycleCustomNode/releaseRecyclePool/enableReleaseExpiringNodes/clearAllRecycle/recycle/reuse），经 `ViewPartialUpdateModelNG::CreateNode`（`:85-93`）注入 CustomNode | 正常 |

### US-3: TS hooks（__*__Internal）

**作为** 框架维护者,
**我想要** ViewFunctions 桥接引擎→TS 内部 hooks,
**以便** 引擎触发 TS 池清理/释放。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 引擎调 `releaseRecyclePoolFunc_` THEN `ViewFunctions`（`js_view_functions.cpp:391`）调 TS `__releaseRecyclePool__Internal` | 正常 |
| AC-3.2 | WHEN 引擎调 `enableReleaseExpiringNodesFunc_` THEN `ViewFunctions`（`:396`）调 TS `__enableReleaseExpiringNodes__Internal` | 正常 |
| AC-3.3 | WHEN 引擎调 `clearAllRecycleFunc_` THEN `ViewFunctions`（`:426`）调 TS `__ClearAllRecyle__PUV2ViewBase__Internal` | 正常 |
| AC-3.4 | WHEN Cangjie 路径 THEN `native_view.cpp:164-193,315-339`（`CreateRecycle`/`AboutToRecycle/Reuse`）镜像 JS 桥接 | 边界 |

### US-4: CustomNode 释放

**作为** 框架维护者,
**我想要** CustomNode 能启用/禁用/触发离屏节点释放,
**以便** 父容器按需释放池节点。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `CustomNode::EnableReleaseExpiringNode`（`custom_node.cpp:606-640`）THEN 注册父 LazyForEachNode 为释放方（`EnableParentCustomNodeReleaseExpiringNode`） | 正常 |
| AC-4.2 | WHEN `CustomNode::DisableReleaseExpiringNode` THEN 取消注册父释放方 | 正常 |
| AC-4.3 | WHEN `CustomNode::ReleaseExpiringNode(reuseId)` THEN 转发父 LazyForEachNode `ReleaseExpiringNode`（按 reuseId 释放池节点） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.5 | R-1 | T-2 | UT：recyclableNodeSet_ 池操作 | `lazy_for_each_builder.cpp:1533-1622` |
| AC-2.1~2.3 | R-2,R-3 | T-2 | UT：JSView CreateRecycle/TryReleaseExpiringNode | `js_view.cpp:780-1286`、`view_partial_update_model_ng.cpp:85-111` |
| AC-3.1~3.4 | R-4 | T-2 | UT：ViewFunctions hooks | `js_view_functions.cpp:391-428` |
| AC-4.1~4.3 | R-5 | T-2 | UT：CustomNode 释放 | `custom_node.cpp:606-640` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | recyclableNodeSet_ 池 | reuseId→itemKey→WeakPtr 集；Record/TryRecord/Release/GetReuseIds | 双层 map | AC-1.1~1.5 |
| R-2 | 行为 | CreateRecycle | 包装 RecycleDummyNode+SetReuseId+接回调；NodeInfoPU 注入 CustomNode | — | AC-2.1,AC-2.3 |
| R-3 | 行为 | TryReleaseExpiringNode | 经 ModelNG→CustomNode::ReleaseExpiringNode(reuseId) | — | AC-2.2 |
| R-4 | 行为 | TS hooks | releaseRecyclePool/__enableReleaseExpiringNodes/__ClearAllRecyle 经 ViewFunctions 调 TS | 引擎→TS | AC-3.1~3.3 |
| R-5 | 行为 | CustomNode 释放 | Enable/Disable/Release ExpiringNode；转发父 LazyForEachNode | — | AC-4.1~4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x C++ 池 | UT | recyclableNodeSet_ 结构、Record/Release |
| VM-2 | AC-2.x JS 桥接 | UT | CreateRecycle/TryReleaseExpiringNode/NodeInfoPU |
| VM-3 | AC-3.x TS hooks | UT | __*__Internal 调用 |
| VM-4 | AC-4.x CustomNode 释放 | UT | Enable/Disable/Release |

## API 变更分析

> framework-internal，无公开 API 变更。

### 新增 API

N/A（framework-internal）。

### 变更/废弃 API

N/A。

## 接口规格

> framework-internal，无公开接口规格。核心内部契约见「规则定义」与各 `lazy_for_each_builder.h`/`js_view.cpp`/`custom_node.cpp`。

## 兼容性声明

- **已有 API 行为变更:** 否（framework-internal 存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** framework-internal（随 NG 管线）。
- **API 版本号策略:** N/A。

> **池与 TS 池边界风险（F-pool）：** 引擎 `recyclableNodeSet_`（C++ reuseId 池，LazyForEachBuilder 持有）与 TS `RecyclePoolV2`/`__ReusePool__Internal__`（07-03-03）是**两层不同池**——引擎池存 WeakPtr<UINode> 供 LazyForEach/Repeat 离屏复用，TS 池存 @Reusable 组件状态；下游勿混淆（风险 RISK-F2-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| recyclableNodeSet_ 双层 map | reuseId→itemKey→WeakPtr 集 | AC-1.1 |
| JSView 桥接 | CreateRecycle 包装+SetReuseId+回调 | AC-2.1 |
| __*__Internal hooks | 引擎→TS 池清理/释放 | AC-3.1~3.3 |
| CustomNode 释放转发 | 父 LazyForEachNode ReleaseExpiringNode | AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | ReleaseExpiringNode 批量释放（MIN_RELEASE_COUNT=5）减少逐节点开销 | UT | `lazy_for_each_builder.cpp:1533` |
| 可靠性 | WeakPtr 池自动清理失效节点 | UT | `lazy_for_each_builder.h:385` |

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
| 大字体 | 否 | 无直接关联 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 否 | framework-internal | — |
| 生态兼容 | 否 | 无公开 API | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: reuseId 节点池与 engine↔TS 桥接
  作为 框架维护者
  我想要 引擎 C++ reuseId 池 + JS/TS 桥接
  以便 LazyForEach/Repeat 离屏节点按 reuseId 复用

  Scenario: 池记录与释放
    Given LazyForEachBuilder recyclableNodeSet_
    When RecordRecyclableNode(reuseId,key,node)
    Then 入池 reuseId→key→node
    When ReleaseExpiringNode(reuseId)
    Then 按 reuseId 释放（批量≥5）

  Scenario: JS 桥接 CreateRecycle
    Given TS @Reusable 节点
    When JSViewPartialUpdate::CreateRecycle
    Then 包装 RecycleDummyNode+SetReuseId+接 recycle/reuse 回调

  Scenario: TS hooks
    Given 引擎触发 releaseRecyclePoolFunc_
    When ViewFunctions
    Then 调 TS __releaseRecyclePool__Internal
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做 C++ 池+桥接；生命周期见 Feat-01、RecycleDummyNode 见 Feat-03、@since26 公开 API 见 Feat-04；TS 池见 07-03-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachBuilder recyclableNodeSet_ reuseId 池 RecordRecyclableNode ReleaseExpiringNode"
  - repo: "openharmony/arkui_ace_engine"
    query: "JSViewPartialUpdate CreateRecycle SetReuseId RecycleDummyNode TryReleaseExpiringNode"
  - repo: "openharmony/arkui_ace_engine"
    query: "ViewFunctions __releaseRecyclePool__Internal __enableReleaseExpiringNodes__Internal __ClearAllRecyle"
  - repo: "openharmony/arkui_ace_engine"
    query: "CustomNode EnableReleaseExpiringNode ReleaseExpiringNode 父 LazyForEachNode"
```

**关键文档：** `frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp`、`frameworks/bridge/declarative_frontend/jsview/js_view.cpp`、`frameworks/bridge/declarative_frontend/jsview/js_view_functions.cpp`、`frameworks/core/components_ng/pattern/custom/custom_node.cpp`
