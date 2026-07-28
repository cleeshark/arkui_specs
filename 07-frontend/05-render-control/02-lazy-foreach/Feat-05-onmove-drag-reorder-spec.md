# 特性规格

> Func-07-05-02-Feat-05 拖拽排序 onMove：固化 `.onMove(callback)`（`@since12`，链式属性方法，绑定于 `LazyForEachAttribute` 返回值）作为 List/Grid 直接父容器拖拽排序的**门控与通知**、可选第二参细粒度拖拽处理器（onLongPress/onDragStart/onMoveThrough/onDrop）、framework 内部 `MoveData` 实时重排（`OnDataMoveToNewPlace`+`UpdateMoveFromTo`）、`ListItemDragManager` 驱动的长按/拖动/交换动画/落下时序、应用侧 `onMove(from,to)` 同步 `IDataSource` 行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 拖拽排序 onMove |
| 特性编号 | Func-07-05-02-Feat-05 |
| 优先级 | P2 |
| 目标版本 | dynamic `@since12`（`.onMove` 链式属性 + `LazyForEachAttribute` 拖拽排序支持）；static 经 `LazyForEachAttribute` 同形态 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-01~04；本特性聚焦 `.onMove` 拖拽排序。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/05-render-control/02-lazy-foreach/design.md` | Baselined |
| Dynamic API | `interface/sdk-js/api/@internal/component/ets/lazy_for_each.d.ts` | — |
| JS 桥接（onMove 绑定/解析） | `frameworks/bridge/declarative_frontend/jsview/js_lazy_foreach.cpp` | — |
| NG Model（OnMove/SetItemDragHandler） | `frameworks/core/components_ng/syntax/lazy_for_each_model_ng.h` / `lazy_for_each_model.h` | — |
| NG 节点（SetOnMove/MoveData/FireOnMove/InitDragManager） | `frameworks/core/components_ng/syntax/lazy_for_each_node.cpp` / `.h` | — |
| NG Builder（OnDataMoveToNewPlace/UpdateMoveFromTo） | `frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp` / `.h` | — |
| 父容器拖拽（ListItemPattern/ListItemDragManager） | `frameworks/core/components_ng/pattern/list/list_item_pattern.cpp` / `list_item_drag_manager.cpp` | — |
| ForEach 基类 | `frameworks/core/components_ng/syntax/for_each_base_node.h` | — |

> 需求基线详见 proposal.md。design.md 与本文档增量合并，互不依赖。

---

## 用户故事

### US-1: onMove 门控与回调

**作为** 应用开发者,
**我想要** 给 LazyForEach 链式调用 `.onMove((from,to)=>{...})` 开启 List/Grid 拖拽排序,
**以便** 用户长按拖动列表项重排，并在落下时同步我的 dataSource。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 链式调用 `.onMove(callback)` THEN 经 `JSLazyForEach::OnMove`（`js_lazy_foreach.cpp:379-395`）解析 `arg[0]` 为 `void(int32_t from,int32_t to)` 回调（`CallJsFuncWithFromTo`，`:288-292`），`LazyForEachModel::GetInstance()->OnMove`（`:300` StaticMethod 绑定） | 正常 |
| AC-1.2 | WHEN `onMoveEvent_` 由空变非空 THEN `LazyForEachNode::SetOnMove`（`:664-672`）调 `InitAllChilrenDragManager(true)` 为已构建子节点挂拖拽；由非空变空则 `InitAllChilrenDragManager(false)` 卸载 | 正常 |
| AC-1.3 | WHEN `arg[0]` 非 function THEN 清空 onMove（`OnMove(nullptr)`）并 `SetItemDragHandler(nullptr,...)`（`:386-389`），拖拽排序关闭 | 异常 |
| AC-1.4 | WHEN `.onMove` 未调用 THEN `onMoveEvent_` 为空，子节点构建时 `if (onMoveEvent_) InitDragManager(...)`（`lazy_for_each_node.cpp:470-472`）不挂拖拽，List/Grid 不支持拖拽排序 | 边界 |

### US-2: 细粒度拖拽处理器

**作为** 应用开发者,
**我想要** 通过第二参对象提供 onLongPress/onDragStart/onMoveThrough/onDrop 细粒度回调,
**以便** 在拖拽各阶段执行自定义逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `.onMove` 第二参为 object THEN `JsParseItemDragEventHandler`（`js_lazy_foreach.cpp:397-429`）解析 `onLongPress(int32_t)`/`onDragStart(int32_t)`/`onMoveThrough(int32_t,int32_t)`/`onDrop(int32_t)` 四处理器，经 `SetItemDragHandler` 下发 | 正常 |
| AC-2.2 | WHEN `SetItemDragHandler` 下发 THEN `LazyForEachNode::SetItemDragHandler`（`:674-684`）**仅当 `onMoveEvent_` 已设置**才存储四处理器；onMove 未设则忽略 | 边界 |
| AC-2.3 | WHEN `.onMove` 仅一参（无第二参）或非 function THEN `SetItemDragHandler(nullptr,...)` 清空四处理器（`:384-385,389`） | 边界 |

### US-3: 拖拽时序与 framework 内部重排

**作为** 应用开发者,
**我想要** 拖拽过程中列表项实时交换动画、落下时收到 onMove(from,to) 通知,
**以便** 视觉反馈流畅且数据可同步。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 长按列表项 THEN `ListItemDragManager::HandleOnItemLongPress`（`list_item_drag_manager.cpp:193-204`）→`forEach->FireOnLongPress(index)` | 正常 |
| AC-3.2 | WHEN 拖动开始 THEN `HandleOnItemDragStart`（`:162-191`）记录 `fromIndex_=index`（`:189`）+`FireOnDragStart(fromIndex_)`（`:190`） | 正常 |
| AC-3.3 | WHEN 拖动移动 THEN `HandleOnItemDragUpdate`（`:570-602`）计算目标 `to`，`HandleSwapAnimation(from,to)`（`:627-658`，30ms `InterpolatingSpring` 内）调 `forEach->MoveData(from,to)`（`:650`）实时重排并 `FlushUITasks`，再 `FireOnMoveThrough(fromIndex_,to)`（`:601`） | 正常 |
| AC-3.4 | WHEN `MoveData(from,to)` 触发 THEN `LazyForEachNode::MoveData`（`:686-703`）调 `builder_->OnDataMoveToNewPlace(from,to)`（`lazy_for_each_builder.cpp:269-298`）+`UpdateMoveFromTo(from,to)`（`:876-883`）重排 `cachedItems_`/`expiringItem_`，swap children，`MarkNeedSyncRenderTree(true)`+`PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT`；**不调 onMove 回调** | 正常 |
| AC-3.5 | WHEN 落下 THEN `HandleOnItemDragEnd`（`:752-774`）→`FireOnMove(fromIndex_,to)`（`:768`）触发应用 onMove(from,to)+`FireOnDrop(to)`（`:769`） | 正常 |
| AC-3.6 | WHEN `FireOnMove(from,to)` 且 `from==to` THEN 基类 `ForEachBaseNode::FireOnMove`（`for_each_base_node.h:31-36`）不触发回调（仅 from!=to 触发），并先 `builder_->ResetMoveFromTo`（`lazy_for_each_node.cpp:705-711`） | 边界 |
| AC-3.7 | WHEN 拖拽取消（cancel）THEN `HandleOnItemDragCancel`（`:776-800`）若状态为 DRAGGING 则 `FireOnMove(fromIndex_,to)`+`FireOnDrop(to)`（`:793-794`） | 边界 |

### US-4: 父容器约束与应用同步职责

**作为** 应用开发者,
**我想要** 了解 onMove 仅在 List/Grid 直接父下生效、且应用须在 onMove 中同步 dataSource,
**以便** 正确使用拖拽排序。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN LazyForEach 直接父为 `LIST_ETS_TAG` 或 `GRID_ETS_TAG` THEN `InitDragManager`（`lazy_for_each_node.cpp:730-747`）对 List 调 `ListItemPattern::InitDragManager`、对 Grid 调 `NodeModifier::GetGridItemCustomModifier()->initDragManager` | 正常 |
| AC-4.2 | WHEN 直接父非 List/Grid THEN `InitDragManager`/`InitAllChilrenDragManager`（`:735-737,753-755`）提前 return，不挂拖拽，拖拽排序不可用 | 边界 |
| AC-4.3 | WHEN 应用 onMove(from,to) 触发 THEN 应用须自行同步 `IDataSource`（如 `dataSource.moveData(from,to)`+`listener.onDataMove(from,to)` 或 `onDatasetChange([{type:MOVE,index:{from,to}}])`）；framework 内部缓存已由 `MoveData` 重排，后续通知仅用于 index/key 一致性 | 正常 |
| AC-4.4 | WHEN `ListItemPattern::InitDragManager`（`list_item_pattern.cpp:100-114`）THEN 创建 `ListItemDragManager(GetHost(),forEach)`+`InitDragDropEvent`，每 ListItem 一个 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.4 | R-1,R-2 | T-5 | UT：`lazy_for_each_model_test_ng` onMove 绑定/门控 | `js_lazy_foreach.cpp:300,379-395`、`lazy_for_each_node.cpp:664-672,470-472` |
| AC-2.1~2.3 | R-3 | T-5 | UT：细粒度处理器解析 | `js_lazy_foreach.cpp:397-429`、`lazy_for_each_node.cpp:674-684` |
| AC-3.1~3.7 | R-4,R-5 | T-5 | UT：`lazy_for_each_syntax_test_ng` MoveData/FireOnMove；XTS 拖拽 | `lazy_for_each_node.cpp:686-711`、`list_item_drag_manager.cpp:162-800` |
| AC-4.1~4.4 | R-6,R-7 | T-5 | UT + XTS | `lazy_for_each_node.cpp:730-788`、`list_item_pattern.cpp:100-114` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `.onMove(callback)` | 解析 from/to 回调，SetOnMove，InitAllChilrenDragManager(true) | onMoveEvent_ 由空→非空才挂 | AC-1.1,AC-1.2 |
| R-2 | 边界 | onMove 未调或 arg 非函数 | onMoveEvent_ 为空，不挂拖拽，List/Grid 不支持拖拽排序 | 拖拽门控=onMoveEvent_ 非空 | AC-1.3,AC-1.4 |
| R-3 | 边界 | 第二参细粒度处理器 | 仅 onMoveEvent_ 已设才存储；否则清空 | 四处理器依赖 onMove | AC-2.1~2.3 |
| R-4 | 行为 | 拖拽时序 | 长按→FireOnLongPress；start→记 fromIndex_+FireOnDragStart；update→MoveData 实时重排+FireOnMoveThrough；end→FireOnMove+FireOnDrop | MoveData 不调 onMove 回调 | AC-3.1~3.5 |
| R-5 | 边界 | FireOnMove from==to | 不触发回调；先 ResetMoveFromTo | 仅 from!=to 触发 | AC-3.6 |
| R-6 | 边界 | 直接父非 List/Grid | InitDragManager 提前 return | 仅 List/Grid 直接父 | AC-4.1,AC-4.2 |
| R-7 | 行为 | onMove 触发 | 应用须同步 IDataSource | framework 内部已重排，通知供 index/key 一致 | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 门控 | `lazy_for_each_model_test_ng` | onMoveEvent_ 门控、InitAllChilrenDragManager |
| VM-2 | AC-2.x 处理器 | UT | 四细粒度处理器依赖 onMove |
| VM-3 | AC-3.x 时序 | `lazy_for_each_syntax_test_ng` + XTS 拖拽 | MoveData 实时重排、FireOnMove from!=to、cancel 路径 |
| VM-4 | AC-4.x 父约束 | UT + XTS | 仅 List/Grid 直接父、应用同步职责 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `.onMove(callback)` 链式属性（`@since12`） | 既有 | List/Grid 拖拽排序门控+通知 | 绑定于 `LazyForEachAttribute` 返回值 | AC-1.1 |
| `LazyForEachAttribute`（empty class，拖拽排序属性承载，`@since12`） | 既有 | 拖拽排序支持 | dynamic empty class（`lazy_for_each.d.ts:951-961`） | AC-1.1 |

> SDK：dynamic `lazy_for_each.d.ts:951-961,1015-1040`。`.onMove` 为合成属性方法（ArkUI 全局属性机制），C++ `StaticMethod("onMove")` 绑定。

## 接口规格

### 接口定义

**`.onMove`（链式属性，`js_lazy_foreach.cpp:300`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `LazyForEachAttribute.onMove(callback: (from: number, to: number) => void, handlers?: { onLongPress?, onDragStart?, onMoveThrough?, onDrop? }): LazyForEachAttribute` |
| 返回值 | `LazyForEachAttribute`（链式） |
| 开放范围 | Public（`@since12`） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | `(from,to)=>void` | 是（function） | — | 非 function→清空 onMove+handlers |
| handlers.onLongPress/onDragStart/onDrop | `(index)=>void` | 否 | — | 仅 onMoveEvent_ 已设才生效 |
| handlers.onMoveThrough | `(from,to)=>void` | 否 | — | 同上 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `.onMove(cb)` | SetOnMove→InitAllChilrenDragManager(true) | AC-1.2 |
| 2 | 拖动移动 | MoveData(from,to) 实时重排+FireOnMoveThrough | AC-3.3,AC-3.4 |
| 3 | 落下 from≠to | FireOnMove(from,to)→应用同步 dataSource+FireOnDrop | AC-3.5,AC-4.3 |
| 4 | 直接父非 List/Grid | 不挂拖拽，排序不可用 | AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。`.onMove` 为 `@since12` 既有；拖拽排序仅在 List/Grid 直接父下生效。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** `@since12`（dynamic）。
- **API 版本号策略:** 按 SDK `@since12` 标注。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| onMove 门控 | 拖拽仅在 onMoveEvent_ 非空时挂载 | AC-1.2,AC-1.4 |
| 仅 List/Grid 直接父 | InitDragManager 仅对 LIST_ETS_TAG/GRID_ETS_TAG 父 | AC-4.1,AC-4.2 |
| framework 内部重排 vs 应用同步 | MoveData 重排缓存；应用 onMove 同步 dataSource | AC-3.4,AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 拖拽交换动画 30ms InterpolatingSpring 流畅 | XTS 拖拽 + benchmark | `list_item_drag_manager.cpp:627-658` |
| 可靠性 | from==to/cancel 路径不误触发回调 | UT | `for_each_base_node.h:31-36`、`list_item_drag_manager.cpp:776-800` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 触摸拖拽一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 无差异 | 同上 | XTS | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 拖拽为交互，无直接无障碍映射 | — |
| 大字体 | 否 | 无独立处理 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | `.onMove` `@since12` | AC-1.1 |
| 生态兼容 | 是 | dynamic `@since12` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 拖拽排序 onMove
  作为 应用开发者
  我想要 用 .onMove 开启 List/Grid 拖拽排序并同步 dataSource
  以便 用户长按拖动重排列表项

  Scenario: 开启拖拽排序
    Given LazyForEach 直接父为 List
    When 链式调用 .onMove(cb)
    Then onMoveEvent_ 非空，已构建子节点挂 ListItemDragManager

  Scenario: 拖拽落下同步数据
    Given 用户长按 index=2 项拖到 index=5
    When 拖动移动
    Then MoveData(2,5) 实时重排缓存（交换动画）
    And 落下时 FireOnMove(2,5) 触发 cb(2,5)，应用须同步 dataSource

  Scenario: 非法父容器
    Given LazyForEach 直接父为 Column
    When 链式调用 .onMove(cb)
    Then InitDragManager 提前 return，拖拽排序不可用

  Scenario: from 等于 to
    Given 用户拖动后落回原位
    When FireOnMove(3,3)
    Then 不触发 onMove 回调（仅 from!=to 触发）
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-05 做 .onMove 拖拽排序；数据通知见 Feat-02/03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachNode SetOnMove onMoveEvent_ 门控 InitAllChilrenDragManager"
  - repo: "openharmony/arkui_ace_engine"
    query: "ListItemDragManager HandleSwapAnimation MoveData 实时重排 FireOnMove 拖拽时序"
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachNode InitDragManager 仅 LIST_ETS_TAG GRID_ETS_TAG 直接父"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/lazy_for_each.d.ts`、`frameworks/bridge/declarative_frontend/jsview/js_lazy_foreach.cpp`、`frameworks/core/components_ng/syntax/lazy_for_each_node.cpp`、`frameworks/core/components_ng/pattern/list/list_item_drag_manager.cpp`
