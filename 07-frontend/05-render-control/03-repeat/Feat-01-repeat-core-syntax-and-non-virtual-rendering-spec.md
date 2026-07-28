# 特性规格

> Func-07-05-03-Feat-01 Repeat 核心语法与非虚拟渲染：固化 `Repeat<T>(arr)`（dynamic `@since12` / static `@since23`）构造与链式 `.each()`（必填，缺省抛 `BusinessError(103802)`）/`.key()`、`RepeatItem<T>`（item/index）、`RepeatAttribute<T>`、非虚拟 `RepeatNode` 的 diff 渲染（`tempIds_`/`tempChildren_`/`tempChildrenOfRepeat_` + TS 驱动 `moveChild`/`createNewChild` 三 case）、**TS 侧 key 生成**（默认 `funcWithIndex`=`${index}__${itemKey}`、用户自定义、重复 key 静默回退+全量重渲染）、onMove 拖拽（仅 List/Grid、`FireOnMove` 共享 `from!=to`）、动画门控（`LazyForEachUtils::GetEnableRepeatAnimation` metadata 标志 + parent==List）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Repeat 核心语法与非虚拟渲染 |
| 特性编号 | Func-07-05-03-Feat-01 |
| 优先级 | P1 |
| 目标版本 | dynamic `@since12`（`Repeat`/`each`/`key`/`RepeatItem`/`RepeatAttribute`）/ `@since18`（`RepeatArray`/`RepeatInterface` readonly 扩展）；static `@since23`（同套）；`@since26 staticonly`（style-builder 重载，详见 Feat-05 范畴，本 Feat 涉及 arr 重载） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。本特性为 Func-07-05-03（Repeat）首个 Feat，作为该功能域 design.md 基线。虚拟滚动（Feat-02，v1 已废弃）、模板化渲染（Feat-03）、内存优化（Feat-04）由后续 Feat 承接。静态范式 `@since26 staticonly` surface（style-builder/debugLine/setRepeatOptions/applyAttributesFinish）按用户决策不单独成 Feat，其 static/dynamic 差异在相关 Feat 版本矩阵中标注。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/05-render-control/03-repeat/design.md` | Baselined |
| Dynamic API（SDK 契约） | `interface/sdk-js/api/@internal/component/ets/repeat.d.ts` | — |
| Static API（SDK 契约） | `interface/sdk-js/api/arkui/component/repeat.static.d.ets` | — |
| TS 侧 API/diff 驱动 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_repeat.ts` / `pu_repeat_impl.ts` | — |
| JS 桥接 | `frameworks/bridge/declarative_frontend/jsview/js_repeat.cpp` / `js_repeat.h` | — |
| NG 非虚拟节点 | `frameworks/core/components_ng/syntax/repeat_node.cpp` / `repeat_node.h` | — |
| NG Model 工厂 | `frameworks/core/components_ng/syntax/repeat_model_ng.cpp` / `repeat_model.h` | — |
| 共享基类（onMove/drag） | `frameworks/core/components_ng/syntax/for_each_base_node.h` | — |
| 全局动画标志 | `frameworks/core/components_ng/syntax/lazy_for_each_utils.cpp` / `.h` | — |
| metadata 读取 | `adapter/ohos/entrance/ui_content_impl.cpp` | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Repeat 构造与链式调用

**作为** 应用开发者,
**我想要** 用 `Repeat(arr).each(itemGen).key(keyGen)` 声明数组驱动的循环列表,
**以便** 以声明式、可 key 复用的方式渲染可变长数组。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在 dynamic 范式（`@since12`）调用 `Repeat(arr)` THEN 返回 `RepeatAttribute<T>`（`repeat.d.ts:317,459`）；`@since18` 起 `arr` 类型放宽为 `RepeatArray<T>`（含 Readonly，`repeat.d.ts:430,444`），`Repeat` const 类型变为 `RepeatInterface` | 正常 |
| AC-1.2 | WHEN 在 static 范式（`@since23`）调用 `Repeat<T>(arr: RepeatArray<T>)` THEN 经 `@ComponentBuilder export function Repeat<T>` 返回 `RepeatAttribute<T>`（`repeat.static.d.ets:318-319,215`） | 正常 |
| AC-1.3 | WHEN 链式调用 `.each(itemGenerator: (repeatItem: RepeatItem<T>)=>void)` THEN 设置 item 构建器（dynamic `repeat.d.ts:342` / static `:226`，均 `@since12`/`@since23`）；`itemGenerator` 接收 `RepeatItem<T>{item,index}`（`repeat.d.ts:65,77,89`） | 正常 |
| AC-1.4 | WHEN 未调用 `.each()` THEN 运行时抛 `BusinessError(103802)`（`pu_repeat.ts:282`），文档标注 each 为 mandatory（`repeat.d.ts:326`） | 异常 |
| AC-1.5 | WHEN 在 itemGenerator 内解构 RepeatItem THEN 文档禁止（"Do not destructure RepeatItem"，`repeat.d.ts:341`），应直接用 `repeatItem.item`/`.index` | 边界 |

### US-2: key 生成（TS 侧）

**作为** 应用开发者,
**我想要** 通过 `.key(keyGen)` 提供稳定唯一 key（或用默认 key）,
**以便** Repeat 按项复用、数组变更时正确 diff。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 省略 `.key()` THEN 默认 `__RepeatDefaultKeyGen.funcWithIndex(item,index)` 返回 `` `${index}__${itemKey}` ``（`pu_repeat.ts:129-131,186-187`），其中 `itemKey` 由 `funcImpl` 生成（基本类型→`JSON.stringify`，对象/符号→WeakMap 数值键，`pu_repeat.ts:133-144`） | 正常 |
| AC-2.2 | WHEN 提供 `.key(keyGen)` THEN `config.keyGenFunc=keyGen`、`keyGenFuncSpecified=true`（`pu_repeat.ts:213-217`），用户函数原样使用 | 正常 |
| AC-2.3 | WHEN 默认 `func(item)`（无 index）THEN 仅按 item 引用生成稳定 key（`pu_repeat.ts:120,133-144`），用于无 index 场景 | 边界 |
| AC-2.4 | WHEN 用户 keyGen 产生重复 key（`key2Item.size < arr.length`）THEN 警告 "Duplicates detected, fallback to index-based keyGen"，重置 `keyGenFunction_=funcWithIndex` 并重跑 `genKeys()`（**导致全部项重渲染**）（`pu_repeat_impl.ts:62-67`） | 异常 |
| AC-2.5 | WHEN C++ 侧消费 key THEN 仅接收已解析的 id 字符串（`repeat_node.h:84` `ids_`、`SetIds` `:61`），RepeatNode **无 keyGen 字段**，key 生成完全在 TS（`RepeatNative.createNewChildStart(key)`→`js_repeat.cpp:93`→`repeat_model_ng.cpp:58`） | 正常 |

### US-3: 非虚拟 diff 渲染

**作为** 应用开发者,
**我想要** 数组变更时 Repeat 增量 diff（非虚拟模式）,
**以便** 仅更新变化的项，复用未变项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 渲染开始（`StartRender`，`repeat_model_ng.cpp:28-38`）THEN `CreateTempItems`（`repeat_node.cpp:44-51`）把旧 `ids_`/`ModifyChildren()` 交换到 `tempIds_`/`tempChildren_`，并复制为 `tempChildrenOfRepeat_`（vector，O(1) 随机访问） | 正常 |
| AC-3.2 | WHEN TS `reRender` 命中 retained case（key 存在）THEN `updateIndex(index)`+`RepeatNative.moveChild(oldIndex)`（`pu_repeat_impl.ts:123-141`）→`RepeatNode::MoveChild`（`repeat_node.cpp:103-111`）经 `AdjustFromIndex`（`:308-321`）补偿在途 MoveData 偏移后 silent re-attach | 正常 |
| AC-3.3 | WHEN 命中 reused-slot case（旧 key 槽复用）THEN `updateItem`+`updateIndex`+`moveChild(oldKeyIndex)`（`pu_repeat_impl.ts:143-170`） | 正常 |
| AC-3.4 | WHEN 命中 brand-new case（新 key）THEN `mkRepeatItem_`+`initialRenderItem` 创建新 C++ SyntaxItem（`pu_repeat_impl.ts:171-178`） | 正常 |
| AC-3.5 | WHEN `FinishRender`（`repeat_model_ng.cpp:40-47`）THEN `FinishRepeatRender`（`repeat_node.cpp:54-93`）对 `tempChildrenOfRepeat_` 中不在新 children 集的旧节点 silent re-attach+`RemoveChild`+`CollectRemovedChildren`，清 temp 并 `frameNode->ChildrenUpdatedFrom(0)` | 正常 |
| AC-3.6 | WHEN 渲染完成 THEN `FlushUpdateAndMarkDirty`（`repeat_node.cpp:186-192`）`MarkNeedSyncRenderTree(true)`+`MarkNeedFrameFlushDirty(PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT | PROPERTY_UPDATE_BY_CHILD_REQUEST)` | 正常 |
| AC-3.7 | WHEN 该节点为非虚拟 THEN `DumpInfo` 硬编码 `"VirtualScroll: false"`（`repeat_node.cpp:323-328`），区别于虚拟滚动节点 | 边界 |

### US-4: onMove 拖拽排序

**作为** 应用开发者,
**我想要** 用 `.onMove` 在 List/Grid 中开启拖拽排序,
**以便** 用户长按拖动重排，落下时同步数组。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `onMove` 由空变非空 THEN `RepeatNode::SetOnMove`（`repeat_node.cpp:114-137`）若有父 `InitAllChildrenDragManager(true)`，无父则 PostTask(UI) 后初始化；由非空变空则 `InitAllChildrenDragManager(false)` | 正常 |
| AC-4.2 | WHEN 直接父非 `LIST_ETS_TAG`/`GRID_ETS_TAG` THEN `InitDragManager`（`:200-220`，gate `:208`）/`InitAllChildrenDragManager`（`:222-261`，gate `:226`）提前 return，且 `onMoveEvent_` 被置空（`:227`），拖拽不可用 | 边界 |
| AC-4.3 | WHEN `MoveData(from,to)` THEN `repeat_node.cpp:152-184` 早退 `from==to||from<0||to<0`；记录 `from_`/`to_`；`ModifyChildren()` erase@from+insert@to；`MarkNeedSyncRenderTree(true)`+`MarkNeedFrameFlushDirty(...)`；`isNeedUpdate` 则 `parentFrame->ChildrenUpdatedFrom(min(from,to))` | 正常 |
| AC-4.4 | WHEN 落下 `FireOnMove(from,to)` THEN 基类 `ForEachBaseNode::FireOnMove`（`for_each_base_node.h:31-36`）仅 `from!=to && onMoveEvent_` 触发回调；RepeatNode **不覆写** FireOnMove（与 ForEach/LazyForEach 共享同一机制） | 边界 |
| AC-4.5 | WHEN `.onMove` 第二参为 object THEN `JsParseItemDragEventHandler`（`js_repeat.cpp:141-173`）解析 onLongPress/onDragStart/onMoveThrough/onDrop；缺省或 onMove 非函数则 `SetItemDragHandler(nullptr×4)`（`repeat_node.cpp:139-149` 仅 onMoveEvent_ 已设才存） | 边界 |

### US-5: 动画门控

**作为** 应用开发者,
**我想要** 了解 Repeat 的项复用动画何时启用,
**以便** 在动画进行时避免突兀的节点复用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `IsAllowAnimation()` THEN `repeat_node.cpp:263-272` 返回 `LazyForEachUtils::GetEnableRepeatAnimation() && parent->GetTag()==LIST_ETS_TAG`（无父返回 false；**Grid 不在动画路径**） | 正常 |
| AC-5.2 | WHEN 应用 metadata 含 `enableRepeatAnimation=="true"` THEN `ui_content_impl.cpp:2271-2274` 在 UI 内容初始化时一次性设 `LazyForEachUtils::SetEnableRepeatAnimation(true)`；默认 `false`（`lazy_for_each_utils.cpp:22`） | 正常 |
| AC-5.3 | WHEN 动画允许且（隐式动画开启 或 子项仍在动画）THEN TS `reRender` 的 4 条复用抑制规则（`pu_repeat_impl.ts:110-117,127-135,148-155`）跳过 moveChild 复用，强制 `mkRepeatItem_`+`initialRenderItem` 新建 | 正常 |
| AC-5.4 | WHEN `IsChildInAnimation(fromIndex)` THEN 仅 Rosen 后端读 `tempChildrenOfRepeat_[fromIndex]` 子 FrameNode 的 `RosenRenderContext::GetRSNode()->GetAnimationsCount()>0`（`:274-293`），非 Rosen 返回 false | 边界 |
| AC-5.5 | WHEN `IsImplicitAnimationOpen()` THEN `repeat_model_ng.cpp:113-116` 委托 `AnimationUtils::IsImplicitAnimationOpen()`（全局动画状态，非节点状态） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.5 | R-1,R-2,R-8 | T-1 | UT：Repeat 构造/链式 + 缺 each 抛错；SDK 比对 | `repeat.d.ts:317-459`、`pu_repeat.ts:282` |
| AC-2.1~2.5 | R-3,R-4,R-9 | T-1 | UT：默认/自定义 key、重复 key 回退；TS 单测 | `pu_repeat.ts:115-217`、`pu_repeat_impl.ts:56-69` |
| AC-3.1~3.7 | R-5,R-6 | T-1 | UT：`repeat_node` diff 三 case + FinishRepeatRender | `repeat_node.cpp:44-111,186-192`、`pu_repeat_impl.ts:91-201` |
| AC-4.1~4.5 | R-7,R-10,R-11 | T-1 | UT：onMove 门控/MoveData/FireOnMove；XTS 拖拽 | `repeat_node.cpp:114-261`、`for_each_base_node.h:31-36` |
| AC-5.1~5.5 | R-12,R-13 | T-1 | UT：动画门控 + metadata 注入 | `repeat_node.cpp:263-306`、`lazy_for_each_utils.cpp:22-42` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `Repeat(arr)` 构造 | 返回 RepeatAttribute<T>；@since18 arr 放宽 RepeatArray（readonly） | static @since23 | AC-1.1,AC-1.2 |
| R-2 | 异常 | 未调 `.each()` | 运行时抛 BusinessError(103802) | each 为 mandatory | AC-1.4 |
| R-3 | 行为 | 省略 `.key()` | 默认 `funcWithIndex`=`${index}__${itemKey}`（对象用 WeakMap） | key 生成在 TS 侧 | AC-2.1,AC-2.3 |
| R-4 | 异常 | 用户 keyGen 产生重复 key | 警告+回退 `funcWithIndex`+全量重渲染 | key2Item.size<arr.length | AC-2.4 |
| R-5 | 行为 | 数组变更 reRender | 三 case：retained→moveChild；reused-slot→updateItem+moveChild；new→initialRenderItem | TS 驱动，C++ 仅消费 id 串 | AC-3.2~3.4 |
| R-6 | 行为 | 渲染完成 | FlushUpdateAndMarkDirty: MEASURE_SELF_AND_PARENT\|BY_CHILD_REQUEST + MarkNeedSyncRenderTree | 非虚拟 DumpInfo="VirtualScroll:false" | AC-3.6,AC-3.7 |
| R-7 | 行为 | onMove 由空变非空 | InitAllChildrenDragManager(true)（无父则 PostTask） | 仅 List/Grid 直接父 | AC-4.1,AC-4.2 |
| R-8 | 边界 | 解构 RepeatItem | 文档禁止，应用 repeatItem.item/.index | — | AC-1.5 |
| R-9 | 行为 | C++ 消费 key | 仅接收 id 字符串（ids_），无 keyGen 字段 | 与 LazyForEach（C++ keyGen）不同 | AC-2.5 |
| R-10 | 边界 | MoveData from==to/负 | 早退不处理 | from_/to_ 记录在途偏移 | AC-4.3 |
| R-11 | 边界 | FireOnMove | 仅 from!=to 触发；RepeatNode 不覆写（共享 ForEachBaseNode） | 与 ForEach/LazyForEach 同机制 | AC-4.4 |
| R-12 | 行为 | IsAllowAnimation | GetEnableRepeatAnimation(metadata) && parent==List | 默认 false；Grid 不在路径 | AC-5.1,AC-5.2 |
| R-13 | 行为 | 动画允许+隐式开/子动画中 | 4 TS 复用抑制规则跳过 moveChild，强制新建 | Rosen 后端才查子动画 | AC-5.3,AC-5.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 构造/链式 | UT + SDK 比对 | Repeat/each/key/RepeatItem、缺 each 抛错、@since12/18/23 版本 |
| VM-2 | AC-2.x key | TS 单测 + UT | 默认 funcWithIndex、自定义、重复 key 回退、TS-only |
| VM-3 | AC-3.x 非虚拟 diff | UT | CreateTempItems/FinishRender/三 case/FlushUpdateAndMarkDirty |
| VM-4 | AC-4.x onMove | UT + XTS 拖拽 | List/Grid 门控、MoveData、FireOnMove from!=to |
| VM-5 | AC-5.x 动画门控 | UT + metadata 注入 | metadata 标志默认 false、parent==List、4 复用抑制规则 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `Repeat<T>(arr)` + `.each`/`.key`（dynamic `@since12`） | 既有 | 核心构造与链式 | each 必填 | AC-1.1,AC-1.3 |
| `Repeat<T>(arr: RepeatArray<T>)`（dynamic `@since18`） | 既有版本扩展 | arr 放宽 readonly | — | AC-1.1 |
| `Repeat<T>(arr)`（static `@since23`） | 既有 | static 范式 | `@ComponentBuilder`、返回 `this` | AC-1.2 |
| `RepeatItem<T>` / `RepeatAttribute<T>` | 既有 | 类型契约 | static index 为 int | AC-1.1,AC-1.3 |

> SDK：dynamic `repeat.d.ts:65,317,342,361,430,444,459`；static `repeat.static.d.ets:69,215,226,237,318`。

## 接口规格

### 接口定义

**Repeat（dynamic，`repeat.d.ts:459`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `declare const Repeat: RepeatInterface`（`<T>(arr: RepeatArray<T>) => RepeatAttribute<T>`，`@since18`；`@since12-17` 为 `<T>(arr: Array<T>) => RepeatAttribute<T>`） |
| 返回值 | `RepeatAttribute<T>` |
| 开放范围 | Public（`@since12`，`@noninterop`） |
| 错误码 | 缺 `.each()` → `BusinessError(103802)` |
| 关联 AC | AC-1.1,AC-1.4 |

**RepeatAttribute\<T\>.each / .key**

| 属性 | 值 |
|------|-----|
| 函数签名 | `each(itemGenerator: (repeatItem: RepeatItem<T>) => void): RepeatAttribute<T>`；`key(keyGenerator: (item: T, index: number) => string): RepeatAttribute<T>` |
| 返回值 | `RepeatAttribute<T>`（链式） |
| 开放范围 | Public（`@since12`） |
| 错误码 | each 缺省→`BusinessError(103802)`；重复 key→静默回退（无错误码） |
| 关联 AC | AC-1.3,AC-2.2,AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| arr | `RepeatArray<T>` | 是 | — | `@since18` 含 Readonly；不可解构 RepeatItem |
| itemGenerator | `(RepeatItem<T>)=>void` | 是 | — | 缺省抛 BusinessError(103802) |
| keyGenerator | `(item,index)=>string` | 否 | `${index}__${itemKey}` | 重复 key 静默回退默认+全量重渲染 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 缺 `.each()` | 抛 BusinessError(103802) | AC-1.4 |
| 2 | 省略 `.key()` | 默认 `${index}__${itemKey}`（TS 侧） | AC-2.1 |
| 3 | 用户 key 重复 | 静默回退默认+全量重渲染 | AC-2.4 |
| 4 | 数组变更 | reRender 三 case diff（moveChild/initialRenderItem） | AC-3.2~3.4 |
| 5 | onMove + 父非 List/Grid | 拖拽不可用，onMoveEvent_ 置空 | AC-4.2 |
| 6 | 动画允许+子动画中 | 跳过 moveChild 复用强制新建 | AC-5.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。注意既有行为：key 生成在 **TS 侧**（与 LazyForEach C++ 侧不同）；默认 key 为 `index__itemKey`（与 LazyForEach 的 `viewId-index` 不同）。
- **配置文件格式变更:** 否（仅 app metadata `enableRepeatAnimation` 既有读取）。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic `@since12`；static `@since23`。
- **API 版本号策略:** 按 SDK `@since12/18/23` 标注；`@since26 staticonly` surface 按用户决策不单独成 Feat。

> **TS-only key 风险（F1）：** Repeat 的 key 生成完全在 TS（`pu_repeat.ts`），C++ 仅消费解析后的 id 字符串（`repeat_node.h:84 ids_`），与 LazyForEach 的 C++ keyGen 路径不同；下游 C-API/Arkoala 路径若直接构造 RepeatNode 须自行提供 id 串（风险 RISK-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| key 生成在 TS 侧 | 默认 `funcWithIndex`、C++ 仅消费 id 串 | AC-2.1,AC-2.5 |
| 非虚拟 diff 由 TS 驱动 | reRender 三 case 经 moveChild/createNewChild，C++ RepeatNode 仅执行 | AC-3.2~3.5 |
| onMove 共享 ForEachBaseNode | FireOnMove 仅 from!=to；List/Grid 直接父 | AC-4.2,AC-4.4 |
| 动画门控 metadata+List | enableRepeatAnimation 默认 false，仅 List 父 | AC-5.1,AC-5.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 非虚拟 diff 仅更新变化项（moveChild 复用） | UT + benchmark | `repeat_node.cpp:103-111`、`pu_repeat_impl.ts:91-201` |
| 可靠性 | 重复 key 静默回退不崩溃 | UT 异常 | `pu_repeat_impl.ts:62-67` |
| 可测试性 | 暴露 getActiveRange/isAllowAnimation 供 TS 复用抑制判定 | UT | `repeat_node.cpp:263-298` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 无差异 | 同上 | XTS | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 子节点随父容器，无直接映射 | — |
| 大字体 | 否 | 无独立处理 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | dynamic `@since12/18`、static `@since23`；key TS-only 与 LazyForEach 差异 | AC-1.1,AC-2.1 |
| 生态兼容 | 是 | dynamic `@since12`、static `@since23` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Repeat 核心语法与非虚拟渲染
  作为 应用开发者
  我想要 用 Repeat(arr).each().key() 声明数组循环并按 key diff
  以便 数组变更时仅更新变化项

  Scenario: 缺 each 抛错
    Given Repeat(arr) 未链式 .each()
    When 运行时构建
    Then 抛 BusinessError(103802)

  Scenario: 默认 key
    Given 未调 .key()
    When 生成 index=2、item={id:5} 的 key
    Then key 形如 "2__<itemKey>"（对象经 WeakMap）

  Scenario: 重复用户 key
    Given .key(k) 产生两个相同 key
    When genKeys 检测 key2Item.size < arr.length
    Then 警告+回退默认 funcWithIndex 并全量重渲染

  Scenario Outline: onMove 父容器
    Given Repeat 直接父为 <父>
    When .onMove(cb)
    Then <结果>

    Examples:
      | 父 | 结果 |
      | List | 挂 ListItemDragManager，拖拽可用 |
      | Grid | 挂 GridItemCustomModifier，拖拽可用 |
      | Column | InitDragManager 提前 return，onMoveEvent_ 置空 |

  Scenario: 动画门控
    Given metadata enableRepeatAnimation=true 且父为 List
    When 拖拽中子项仍有动画
    Then reRender 跳过 moveChild 复用，强制新建项
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做构造/key/非虚拟 diff/onMove/动画；虚拟滚动见 Feat-02、模板见 Feat-03、内存优化见 Feat-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "pu_repeat __RepeatDefaultKeyGen funcWithIndex TS 侧 key 生成与重复 key 回退"
  - repo: "openharmony/arkui_ace_engine"
    query: "RepeatNode CreateTempItems FinishRepeatRender MoveChild 非虚拟 diff 三 case"
  - repo: "openharmony/arkui_ace_engine"
    query: "RepeatNode SetOnMove InitDragManager LIST_ETS_TAG GRID_ETS_TAG 门控"
  - repo: "openharmony/arkui_ace_engine"
    query: "RepeatNode IsAllowAnimation LazyForEachUtils GetEnableRepeatAnimation metadata"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/repeat.d.ts`、`interface/sdk-js/api/arkui/component/repeat.static.d.ets`、`frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_repeat.ts`、`frameworks/core/components_ng/syntax/repeat_node.cpp`、`docs/syntax/Repeat_Knowledge_Base.md`
