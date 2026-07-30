# 特性规格

> Func-04-19-01-Feat-03 RecycleDummyNode 与 DisableRecycle 机制：固化引擎侧可回收节点包装 `RecycleDummyNode`（`RECYCLE_VIEW_ETS_TAG`、`WrapRecycleDummyNode`、`disableRecycle_` 标志、析构触发 `FireRecycleSelf`、`IsAtomicNode=true`）、`ForEachBaseNode::DisableRecycle` 静态递归（opt-out 子树回收）、与 ForEach/LazyForEach/Repeat 语法节点集成（`RecycleChildByIndex` DynamicCast、`DisableRecycle` 调用）行为规格。本特性 framework-internal。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | RecycleDummyNode 与 DisableRecycle 机制 |
| 特性编号 | Func-04-19-01-Feat-03 |
| 优先级 | P2 |
| 目标版本 | framework-internal（随 NG 渲染管线，无独立 `@since`） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-01（生命周期）/Feat-02（池+桥接）；本特性聚焦 RecycleDummyNode 包装与 DisableRecycle opt-out。@since26 公开池 API（Feat-04）由后续 Feat 承接。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/19-component-reuse/01-component-reuse-framework/design.md` | Baselined |
| RecycleDummyNode | `frameworks/core/components_ng/pattern/recycle_view/recycle_dummy_node.h` / `recycle_dummy_node.cpp` | — |
| DisableRecycle（ForEachBaseNode） | `frameworks/core/components_ng/syntax/for_each_base_node.h` | — |
| LazyForEach 集成 | `frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp` | — |
| Repeat 集成 | `frameworks/core/components_ng/syntax/repeat_virtual_scroll_2_node.cpp` / `repeat_virtual_scroll_node.cpp` | — |

> 需求基线详见 proposal.md。本特性 framework-internal，源码即规格。

---

## 用户故事

### US-1: RecycleDummyNode 包装

**作为** 框架维护者,
**我想要** RecycleDummyNode 包装可回收 CustomNode,
**以便** 节点出树时触发回收而非销毁。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 包装可回收节点 THEN `RecycleDummyNode`（`recycle_dummy_node.h:25`，tag `V2::RECYCLE_VIEW_ETS_TAG`）为 UINode 子类，`IsAtomicNode()=true` | 正常 |
| AC-1.2 | WHEN `WrapRecycleDummyNode` THEN 把 CustomNode 包入 RecycleDummyNode 作为子 | 正常 |
| AC-1.3 | WHEN RecycleDummyNode 析构（`recycle_dummy_node.cpp:42-61`）THEN 除非 `disableRecycle_`，调子 `FireRecycleSelf()`（触发回收入池）；否则直接销毁 | 正常 |
| AC-1.4 | WHEN `SetDisableRecycle(bool)`（`:37`）THEN 置 `disableRecycle_`；true 时析构不回收 | 边界 |

### US-2: DisableRecycle 机制

**作为** 框架维护者,
**我想要** ForEachBaseNode::DisableRecycle 递归 opt-out 子树回收,
**以便** 特定子树（如 repeatImmediately/非复用项）不回收。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `ForEachBaseNode::DisableRecycle(RefPtr<UINode>)`（`for_each_base_node.h:71-88`）static THEN 若节点为 RecycleDummyNode 则 `SetDisableRecycle(true)`；否则递归 `DisableChildrenAndCachesRecycle` | 正常 |
| AC-2.2 | WHEN `DisableChildrenAndCachesRecycle` THEN 递归子节点 + RecycleDummyNode SetDisableRecycle | 正常 |

### US-3: 语法节点集成

**作为** 框架维护者,
**我想要** LazyForEach/Repeat 经 RecycleDummyNode 回收 + 按需 DisableRecycle,
**以便** 语法节点离屏项正确回收/opt-out。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN LazyForEach `RecycleChildByIndex`（`lazy_for_each_builder.cpp:770-777`）THEN DynamicCast `RecycleDummyNode` 处理回收项 | 正常 |
| AC-3.2 | WHEN LazyForEach 回收检查 THEN `IsReusableNode` 判定（`:1263,1274`）决定是否入池 | 正常 |
| AC-3.3 | WHEN LazyForEach/Repeat opt-out THEN 调 `ForEachBaseNode::DisableRecycle`（lazy_for_each_builder.cpp:1484、repeat_virtual_scroll_2_node.cpp:728,746,1145） | 正常 |
| AC-3.4 | WHEN Repeat 节点 `OnRecycle`/`OnReuse`（repeat_virtual_scroll_node.cpp:450-463）THEN 递归缓存子节点回收/复用 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.4 | R-1,R-2 | T-3 | UT：RecycleDummyNode 包装/析构 | `recycle_dummy_node.cpp:42-61` |
| AC-2.1~2.2 | R-3 | T-3 | UT：DisableRecycle 递归 | `for_each_base_node.h:71-88` |
| AC-3.1~3.4 | R-4 | T-3 | UT：LazyForEach/Repeat 集成 | `lazy_for_each_builder.cpp:770-777,1484`、`repeat_virtual_scroll_2_node.cpp:728,746,1145` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | RecycleDummyNode 包装 | tag RECYCLE_VIEW_ETS_TAG；IsAtomicNode=true；包 CustomNode 为子 | — | AC-1.1,AC-1.2 |
| R-2 | 行为 | RecycleDummyNode 析构 | 非 disableRecycle_→FireRecycleSelf 回收；disableRecycle_→直接销毁 | — | AC-1.3,AC-1.4 |
| R-3 | 行为 | DisableRecycle | RecycleDummyNode→SetDisableRecycle(true)；否则递归子 | 静态 | AC-2.1,AC-2.2 |
| R-4 | 行为 | 语法节点集成 | LazyForEach RecycleChildByIndex DynamicCast + IsReusableNode 判定；Repeat OnRecycle/OnReuse 递归；opt-out 调 DisableRecycle | — | AC-3.1~3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x RecycleDummyNode | UT | 包装/析构 FireRecycleSelf/disableRecycle_ |
| VM-2 | AC-2.x DisableRecycle | UT | 递归 opt-out |
| VM-3 | AC-3.x 语法集成 | UT | LazyForEach/Repeat 回收/opt-out |

## API 变更分析

> framework-internal，无公开 API 变更。

### 新增 API

N/A（framework-internal）。

### 变更/废弃 API

N/A。

## 接口规格

> framework-internal，无公开接口规格。核心内部契约见「规则定义」与各 `recycle_dummy_node.h`/`for_each_base_node.h`。

## 兼容性声明

- **已有 API 行为变更:** 否（framework-internal 存量补录）。注意既有行为：RecycleDummyNode 析构默认 FireRecycleSelf 回收（`disableRecycle_` opt-out）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** framework-internal。
- **API 版本号策略:** N/A。

> **disableRecycle opt-out 风险（F-disable）：** RecycleDummyNode 默认析构回收；`disableRecycle_=true`（经 `ForEachBaseNode::DisableRecycle`）opt-out 直接销毁——下游勿假设所有 RecycleDummyNode 析构都入池（风险 RISK-F3-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| RecycleDummyNode 包装 | CustomNode 包入、析构 FireRecycleSelf | AC-1.2,AC-1.3 |
| disableRecycle_ opt-out | DisableRecycle 递归设 true | AC-1.4,AC-2.1 |
| 语法节点集成 | LazyForEach/Repeat 经 RecycleDummyNode 回收 | AC-3.1,AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | disableRecycle opt-out 保证非复用项正确销毁 | UT | `for_each_base_node.h:71-88` |

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
Feature: RecycleDummyNode 与 DisableRecycle 机制
  作为 框架维护者
  我想要 RecycleDummyNode 包装 + DisableRecycle opt-out
  以便 节点出树时回收或按需销毁

  Scenario: 析构回收
    Given RecycleDummyNode 包 CustomNode，disableRecycle_=false
    When 析构
    Then 子 FireRecycleSelf 回收入池

  Scenario: opt-out 销毁
    Given RecycleDummyNode disableRecycle_=true（经 DisableRecycle）
    When 析构
    Then 直接销毁，不回收

  Scenario: 语法节点集成
    Given LazyForEach 离屏项
    When RecycleChildByIndex
    Then DynamicCast RecycleDummyNode + IsReusableNode 判定入池
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 做 RecycleDummyNode/DisableRecycle；生命周期见 Feat-01、池见 Feat-02、@since26 公开 API 见 Feat-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RecycleDummyNode RECYCLE_VIEW_ETS_TAG WrapRecycleDummyNode disableRecycle_ 析构 FireRecycleSelf"
  - repo: "openharmony/arkui_ace_engine"
    query: "ForEachBaseNode DisableRecycle 递归 SetDisableRecycle DisableChildrenAndCachesRecycle"
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEach RecycleChildByIndex RecycleDummyNode Repeat DisableRecycle 集成"
```

**关键文档：** `frameworks/core/components_ng/pattern/recycle_view/recycle_dummy_node.cpp`、`frameworks/core/components_ng/syntax/for_each_base_node.h`、`frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp`
