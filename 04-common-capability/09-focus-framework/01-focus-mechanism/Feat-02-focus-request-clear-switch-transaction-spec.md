# 特性规格

> Func-04-09-01-Feat-02 焦点请求、清除与切换事务：固化 NG 焦点请求的调度、准入、层级切换、结果回传、失焦清理、事务提交与 FreeNode 最终一致性行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 焦点请求、清除与切换事务 |
| 特性编号 | Func-04-09-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 当前 NG 实现；本特性核心路径无 Target API 分支 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性定义 NG 焦点框架从请求入口到事务提交的完整闭环，包括普通异步请求、按 ID 同步/异步请求、立即请求准入、SCOPE 层级切换、失败结果回传、失焦与节点移除、`FocusManager::FocusGuard` 最外层提交、窗口切换合并，以及 FreeNode 挂树后的延迟清理。

本特性使用 Feat-01 定义的 `currentFocus_`、`lastWeakFocusNode_`、`FocusType` 与可聚焦性判定，但不重新定义这些状态。本特性只规定 `RemoveChild` 调用导航策略后的恢复顺序，不展开 TAB/方向键候选算法；FocusView 栈、默认焦点和历史恢复目标归 Feat-05；焦点框样式与绘制算法归 Feat-06。

## 本次变更范围（Delta）

> 历史规格补齐，当前实现即规格；同步返回值、回调时序、FreeNode 延迟状态及测试缺口按现状记录，不修改产品代码。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 请求调度与准入 | 补录 NODE/SCOPE/按 ID 三槽位、Frame 调度、modal/Tab/whole-path 检查 |
| ADDED | 按 ID 请求与结果回传 | 补录同步预检查、异步入队、子窗口查找、一次性回调和整数错误码 |
| ADDED | 层级切换事务 | 补录 SCOPE `SwitchFocus`、最外层 FocusGuard、提交顺序和窗口事务合并 |
| ADDED | 失焦与节点移除 | 补录 LostFocus、LostSelfFocus、RemoveSelf、RemoveChild 及恢复顺序 |
| ADDED | FreeNode 最终一致性 | 补录 RemoveSelf 挂树后执行及 attach 前的中间状态 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/design.md` | 增量合并 |
| 前置状态模型规格 | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/Feat-01-focus-tree-node-state-model-spec.md` | Baselined |
| 焦点请求与清除核心实现 | `frameworks/core/components_ng/event/focus_hub.cpp:478-715,1263-1280,1384-1407,1478-1485,2480-2539` | 已核验 |
| Pipeline 调度实现 | `frameworks/core/pipeline_ng/pipeline_context.cpp:1803-1881,5436-5480`、`frameworks/core/pipeline_ng/pipeline_context.h:1541-1543` | 已核验 |
| FocusManager 事务实现 | `frameworks/core/components_ng/manager/focus/focus_manager.cpp:276-289,398-451,485-569`、`focus_manager.h:219-250` | 已核验 |
| ArkTS/ANI/NAPI 入口 | `interfaces/ets/ani/focuscontroller/ets/@ohos.arkui.focusController.ets:17-26`、`interfaces/napi/kits/focus_controller/js_focus_controller.cpp:26-101` | 仓内接口面已核验；canonical SDK 声明未随当前检出提供 |
| Native C API | `interfaces/native/native_interface_focus.h:16-77`、`interfaces/native/node/native_interface_focus.cpp:24-48` | 已核验 |
| FreeNode 多线程实现 | `frameworks/base/utils/multi_thread.h:19-29`、`frameworks/core/components_ng/event/focus_hub_multithread.cpp:22-57`、`frameworks/core/components_ng/base/ui_node_multi_thread.cpp:39-51,105-130` | 已核验 |
| 焦点 UT | `test/unittest/core/event/focus_core/`、`test/unittest/core/manager/focus_manager_test_ng.cpp`、`test/unittest/core/pipeline/pipeline_context_test_ng_two.cpp` | 已核验 |

## 用户故事

### US-1: 调度并执行焦点请求

**作为** ArkUI 焦点框架调用方，  
**我想要** 通过异步或立即入口请求节点获焦，并获得一致的准入检查，  
**以便** 请求在 UI Pipeline 中按确定顺序执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 已聚焦 FocusHub 调用 `RequestFocus()` THEN 不写入 dirty focus 槽且不请求新帧 | 边界 |
| AC-1.2 | WHEN 未聚焦 FocusHub 调用 `RequestFocus()` THEN 按 NODE 或 SCOPE 写入对应单槽位并请求帧；WHEN 宿主未挂主树 THEN 仅记录警告，仍继续调度 | 正常 |
| AC-1.3 | WHEN 调用 `RequestFocusImmediately()` 且 modal FocusView 不允许当前节点获焦 THEN 返回 false 且不进入 Inner 请求 | 异常 |
| AC-1.4 | WHEN处于 Tab 聚焦流程且目标不可由 Tab 聚焦 THEN 立即请求返回 false，并通过一次性回调报告 `NON_FOCUSABLE_BY_TAB` | 异常 |
| AC-1.5 | WHEN 目标已经是当前焦点 THEN 立即请求幂等返回 true，不创建新的层级切换 | 边界 |
| AC-1.6 | WHEN 目标整条焦点路径不可聚焦 THEN 立即请求返回 false，回调报告 `NON_FOCUSABLE_ANCESTOR`，整数结果写入 `150002` | 异常 |
| AC-1.7 | WHEN 立即请求通过全部准入检查 THEN 目标先置 `currentFocus_=true` 并记录 FocusReason，再通过父 SCOPE 传播切换，更新事务候选并触发 HandleFocus | 正常 |

### US-2: 处理按 ID 请求与结果通道

**作为** ArkTS、ANI、JSI 或 Pipeline 请求入口，  
**我想要** 按节点 ID 发起同步或异步请求并区分预检查、调度和错误结果，  
**以便** 上层不会把请求返回值误解为最终提交结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN Pipeline 按 ID 请求焦点 THEN 优先使用 focused WindowScene 根，否则使用普通根；WHEN 当前 Pipeline 是子 Pipeline 且未找到目标 THEN 递归查询父 Pipeline | 正常 |
| AC-2.2 | WHEN 当前 Container 不是 sub-container 且主树未找到 ID THEN 枚举其子容器根查找；WHEN 当前 Container 已是 sub-container THEN 不反向枚举子容器 | 边界 |
| AC-2.3 | WHEN ID 在当前树与允许的子窗口中均不存在 THEN 返回 false，并通过一次性回调报告 `NON_EXIST` | 异常 |
| AC-2.4 | WHEN 同步按 ID 请求的目标不可见、禁用、自身不可聚焦或祖先不可聚焦 THEN 不写 dirty request，并分别报告 `150003`、`150001` 或 `150002` | 异常 |
| AC-2.5 | WHEN 同步按 ID 请求预检查通过 THEN 写入按 ID 槽、同步 Flush 并返回 true；该返回值表示预检查通过，不保证 Flush 阶段未被 modal 或运行时状态再次拦截 | 边界 |
| AC-2.6 | WHEN 异步按 ID 请求找到目标但当前 `IsFocusable()` 返回 false THEN 函数返回 false但仍写入按 ID 槽并请求帧，下一帧按届时状态重新执行立即请求 | 恢复 |
| AC-2.7 | WHEN 同一类别在一帧内多次写 dirty focus THEN 后一次覆盖前一次；WHEN 按 ID 槽有效 THEN Flush 优先处理该槽并清空 NODE、SCOPE 与按 ID 三个槽位 | 边界 |
| AC-2.8 | WHEN失败结果触发 `RequestFocusCallback` THEN 回调执行一次后立即清空；WHEN调用成功 THEN 不显式触发成功回调，整数结果保持或恢复为 `0` | 边界 |

### US-3: 在焦点层级中切换并提交事务

**作为** 焦点 Scope 和 FocusManager，  
**我想要** 将一条父子焦点链的变化合并为一个最外层事务，  
**以便** 监听者、当前焦点和下游绘制观察到一致的提交结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 非 SCOPE FocusHub 调用 `SwitchFocus` THEN 记录警告并保持状态不变 | 异常 |
| AC-3.2 | WHEN SCOPE 切换到新子节点 THEN 先将 `lastWeakFocusNode_` 更新为新子；WHEN SCOPE 已聚焦 THEN 更新事务候选并使不同的旧子失焦；WHEN新旧子相同 THEN 不重复失焦 | 正常 |
| AC-3.3 | WHEN SCOPE 尚未聚焦却收到子节点切换 THEN 递归执行自身立即请求，使切换继续沿父链传播 | 恢复 |
| AC-3.4 | WHEN 最外层 FocusGuard 已启动后再次创建嵌套 FocusGuard THEN 内层不获得提交权；内层 `UpdateCurrentFocus` 仍可覆盖候选终点，最外层 startReason 保持不变 | 边界 |
| AC-3.5 | WHEN普通事务结束且最终候选有效 THEN 依次清理最终候选的历史后代链、通知 old/new 监听者、提交 Manager current 并复位事务字段、执行焦点状态重绘、整理 modal 栈 | 正常 |
| AC-3.6 | WHEN切换监听者在通知回调内调用 `GetCurrentFocus()` THEN Manager 仍返回提交前的旧焦点；回调参数中的 switching focus 表示候选新焦点 | 边界 |
| AC-3.7 | WHEN目标 HandleFocus 或旧节点 LostFocus 执行 THEN内部 onFocus/onBlur 同步发生，开发者回调进入 after-layout task；WHEN 最外层请求返回 THEN Manager 已提交但开发者回调可以尚未执行 | 边界 |

### US-4: 清除焦点并处理节点移除

**作为** 节点生命周期和 FocusView 清焦流程，  
**我想要** 在节点禁用、隐藏、移除或显式清焦时按层级恢复，  
**以便** 焦点状态不会停留在失效节点上。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `LostFocus(reason)` 作用于当前聚焦节点 THEN 写入 BlurReason、清 `currentFocus_` 并触发 OnBlur；WHEN节点已非当前焦点 THEN 不重复触发 | 正常 |
| AC-4.2 | WHEN 当前节点调用 `LostSelfFocus()` THEN 依次显式设置 focusable 为 false 和 true，通过 false 阶段触发移除事务；完成后节点保持 focusable=true 且 currentFocus=false | 恢复 |
| AC-4.3 | WHEN普通节点调用 `RemoveSelf` 且存在非 Screen 父 SCOPE且自身不是 FocusView THEN 委托父 SCOPE 执行 `RemoveChild`；WHEN父为 Screen 或自身为 FocusView THEN 不继续向上迁移，仅在自身当前聚焦时失焦 | 边界 |
| AC-4.4 | WHEN `RemoveChild` 的入参为空或不是当前 SCOPE 的直接焦点子节点 THEN 不修改任何焦点状态 | 异常 |
| AC-4.5 | WHEN当前聚焦子节点被移除且未要求跳过迁移 THEN 依次尝试 TAB 后继和 SHIFT_TAB 前驱；候选节点的计算算法由 Feat-03 定义 | 恢复 |
| AC-4.6 | WHEN TAB 与 SHIFT_TAB 均失败且当前 SCOPE 是当前 FocusView 根 THEN 清历史子引用并将焦点停留标记设为 ViewRoot；WHEN不是 ViewRoot THEN 递归 `RemoveSelf` | 恢复 |
| AC-4.7 | WHEN `LostFocusToViewRoot` 通过 FocusGuard 清除当前 ViewRoot 子节点 THEN 保留 ViewRoot 的历史焦点链；WHEN普通切换事务提交 THEN 清理最终候选的历史后代链 | 边界 |

### US-5: 合并窗口事务并延迟 FreeNode 清理

**作为** 窗口焦点切换和多线程节点构建流程，  
**我想要** 合并窗口内的多步焦点移动，并将 FreeNode 的不安全清理延后，  
**以便** 对外仅观察到最终焦点且主焦点树只在安全时机修改。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN WindowFocusMoveStart 后发生一个或多个焦点更新 THEN各 FocusGuard 结束时只记录候选和结束原因，不立即 report/paint；WHEN WindowFocusMoveEnd THEN以最后候选执行一次 `WINDOW_FOCUS` report 和 paint | 正常 |
| AC-5.2 | WHEN FreeNode 调用 `RemoveSelf` THEN通过 `FREE_NODE_CHECK` 转入 `RemoveSelfMultiThread`，把清理加入 after-attach tasks，挂树前不立即修改父焦点树 | 正常 |
| AC-5.3 | WHEN FreeNode 被标记为非 Free 并执行 after-attach tasks THEN运行 `RemoveSelfExecuteFunction`，按普通 RemoveSelf 规则完成失焦、迁移与 scope 注册清理 | 恢复 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.2 | R-1 | TASK-SKELETON-F2-1 | UT + 源码审查 | `focus_hub.cpp:1263-1280`、`pipeline_context.cpp:5463-5480` |
| AC-1.3~1.7 | R-2, R-3 | TASK-SKELETON-F2-1 | UT | `focus_hub.cpp:505-584`、`focus_hub_modalUEC_test_ng.cpp:283-614` |
| AC-2.1~2.3 | R-4 | TASK-SKELETON-F2-2 | UT + 源码审查 | `pipeline_context.cpp:5436-5460`、`focus_hub.cpp:2480-2539` |
| AC-2.4~2.6 | R-5, R-6 | TASK-SKELETON-F2-2 | UT | `focus_hub.cpp:937-956,2480-2509`、`focus_hub_test_ng.cpp:793-834` |
| AC-2.7 | R-7 | TASK-SKELETON-F2-2 | UT | `pipeline_context.cpp:1803-1881,5463-5480`、`pipeline_context_test_ng_two.cpp:661-703` |
| AC-2.8 | R-8 | TASK-SKELETON-F2-2 | UT | `focus_manager.h:219-250`、`focus_manager_test_ng.cpp:143-168` |
| AC-3.1~3.3 | R-9 | TASK-SKELETON-F2-3 | UT | `focus_hub.cpp:1384-1407`、`focus_hub_test_ng_new.cpp:24-59` |
| AC-3.4~3.6 | R-10, R-11 | TASK-SKELETON-F2-3 | UT + 补充 UT | `focus_manager.cpp:398-451,485-569` |
| AC-3.7 | R-12 | TASK-SKELETON-F2-3 | UT + 时序审查 | `focus_hub.cpp:540-584,641-650,1547-1659` |
| AC-4.1~4.2 | R-13 | TASK-SKELETON-F2-4 | UT | `focus_hub.cpp:641-659,889-913`、`focus_hub_test_ng.cpp:208-254,443-503` |
| AC-4.3~4.6 | R-14, R-15 | TASK-SKELETON-F2-4 | UT + 补充 UT | `focus_hub.cpp:661-715`、`passive_last_focus_test.cpp:119-180` |
| AC-4.7 | R-11, R-16 | TASK-SKELETON-F2-4 | UT | `focus_hub.cpp:595-621,1478-1485`、`focus_manager.cpp:503-507` |
| AC-5.1 | R-17 | TASK-SKELETON-F2-5 | UT + 补充 UT | `focus_manager.cpp:485-538,579-585` |
| AC-5.2~5.3 | R-18 | TASK-SKELETON-F2-5 | 线程场景 UT | `focus_hub_multithread.cpp:22-57`、`ui_node_multi_thread.cpp:39-51,105-130` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 非当前焦点调用 `RequestFocus()` | 按 FocusType 写入 NODE 或 SCOPE 单槽位并请求帧（`focus_hub.cpp:1263-1280`） | off-main-tree 仅告警；同类后写覆盖前写 | AC-1.1, AC-1.2 |
| R-2 | 异常 | `RequestFocusImmediately()` 进入准入检查 | modal 拦截、Tab 不可聚焦或 whole-path 不可聚焦时返回 false（`focus_hub.cpp:505-560`） | 已当前聚焦时幂等返回 true | AC-1.3~1.6 |
| R-3 | 行为 | 立即请求通过准入 | 置目标 current/reason，建立 FocusGuard，递归父 Scope，更新候选并 HandleFocus（`focus_hub.cpp:563-584`） | 父链状态模型由 Feat-01 定义 | AC-1.7 |
| R-4 | 行为 | Pipeline 按 ID 查找目标 | 从 focused WindowScene/root、允许的子容器、父 Pipeline 依次查找（`pipeline_context.cpp:5436-5460`、`focus_hub.cpp:2512-2539`） | modal 栈有效时 Pipeline 入口直接拦截 | AC-2.1~2.3 |
| R-5 | 异常 | 同步请求调用 `IsSyncRequestFocusable` | 不存在/不可见/禁用为 150003，自身不可聚焦为 150001，祖先不可聚焦为 150002（`focus_hub.cpp:937-956`） | 检查失败不写 dirty request | AC-2.4 |
| R-6 | 边界 | 按 ID 同步或异步调度 | 同步仅预检查通过时入槽并 Flush；异步找到目标即入槽，即使当前返回 false（`focus_hub.cpp:2495-2509`） | 返回值不是最终事务提交证明 | AC-2.5, AC-2.6 |
| R-7 | 边界 | 一帧存在多个 dirty focus | 三类请求均为 WeakPtr 单槽位；按 ID 先 Flush 并清三槽（`pipeline_context.h:1541-1543`、`pipeline_context.cpp:1803-1881`） | 不提供 FIFO 保证 | AC-2.7 |
| R-8 | 异常 | 请求失败需要回报 | 一次性 callback 触发后清空；整数错误码独立维护（`focus_manager.h:219-250`） | Tab 失败只触发回调；成功不触发成功回调 | AC-1.4, AC-2.8 |
| R-9 | 行为 | SCOPE 执行 `SwitchFocus` | 先更新 lastWeakFocusNode；已聚焦则更新候选并 blur 不同旧子，未聚焦则请求自身（`focus_hub.cpp:1384-1407`） | 非 SCOPE 不执行；调用方需提供有效新子节点 | AC-3.1~3.3 |
| R-10 | 边界 | 已处于切换事务时创建 FocusGuard | 内层 guard 不启动/结束事务，但 UpdateCurrentFocus 可覆盖候选（`focus_manager.cpp:398-404,541-569`） | 仅最外层 startReason 和析构拥有提交权 | AC-3.4 |
| R-11 | 行为 | 普通 FocusGuard 结束 | 清历史、通知监听、提交 current/reset、clear→paint、整理 modal 栈（`focus_manager.cpp:276-289,440-451,485-510`） | 监听期间 GetCurrentFocus 仍为旧焦点 | AC-3.5, AC-3.6, AC-4.7 |
| R-12 | 边界 | 节点触发 Focus/Blur | Hub 状态与内部回调同步更新，开发者回调排入 after-layout（`focus_hub.cpp:1547-1659`） | Manager 提交早于 after-layout 开发者回调 | AC-3.7 |
| R-13 | 恢复 | 当前节点 LostFocus 或 LostSelfFocus | LostFocus 幂等清 current 并 OnBlur；LostSelfFocus 通过显式 false→true 触发移除（`focus_hub.cpp:641-659,889-913`） | LostSelfFocus 完成后保留显式 focusable=true | AC-4.1, AC-4.2 |
| R-14 | 恢复 | 节点调用 RemoveSelf | 普通子委托父 Scope；Screen 直系子或 FocusView 自身仅本地失焦（`focus_hub.cpp:661-684`） | scope id/priority 清理与当前聚焦状态无关 | AC-4.3 |
| R-15 | 恢复 | 直接聚焦子节点被 RemoveChild | 按 TAB、SHIFT_TAB、ViewRoot 停留、父 Scope 递归移除的顺序恢复（`focus_hub.cpp:686-715`） | 非直接子节点无操作；导航候选算法归 Feat-03 | AC-4.4~4.6 |
| R-16 | 边界 | `LOST_FOCUS_TO_VIEW_ROOT` 事务结束 | 不清最终 ViewRoot 的历史链（`focus_manager.cpp:503-507`） | 其他普通事务递归清 lastWeakFocusNode 链 | AC-4.7 |
| R-17 | 行为 | 窗口焦点移动期间结束事务 | 延迟 report/paint，WindowFocusMoveEnd 以最后候选一次提交（`focus_manager.cpp:485-538`） | FocusReason 固定为 WINDOW_FOCUS | AC-5.1 |
| R-18 | 恢复 | FreeNode 调用 RemoveSelf | 缓存 after-attach task；MarkNodeNotFree 时执行普通清理（`focus_hub_multithread.cpp:22-57`、`ui_node_multi_thread.cpp:39-51,105-130`） | attach 前存在焦点树副作用尚未完成的中间态 | AC-5.2, AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | R-1~R-3, AC-1.1~1.7 | UT | 普通调度、off-main-tree、modal/Tab/whole-path 准入和幂等请求 |
| VM-2 | R-4~R-6, AC-2.1~2.6 | UT + 集成测试 | WindowScene/root/subwindow/父 Pipeline 查找及同步/异步返回语义 |
| VM-3 | R-7, AC-2.7 | Pipeline UT | 三单槽后写覆盖、按 ID 优先和清槽行为 |
| VM-4 | R-8, AC-2.8 | UT | callback 一次性、双结果通道、Tab 失败不写整数码 |
| VM-5 | R-9, AC-3.1~3.3 | UT | 非 SCOPE、首次子、同子重入、不同子切换、父 Scope 未聚焦 |
| VM-6 | R-10, AC-3.4 | 补充 UT | 双层 FocusGuard 仅提交一次、内层 reason 不覆盖、最后 update 胜出 |
| VM-7 | R-11, AC-3.5~3.6 | 补充 UT | history→listener→current→paint 顺序及监听回调内查询旧 current |
| VM-8 | R-12, AC-3.7 | 补充 UT | 内部回调、Manager 提交和 after-layout 开发者回调的相对时序 |
| VM-9 | R-13, AC-4.1~4.2 | UT + 补充 UT | LostFocus 幂等、LostSelfFocus 最终状态及显式标记 |
| VM-10 | R-14, R-15, AC-4.3~4.6 | 参数化 UT | Screen/FocusView 边界和 TAB→SHIFT_TAB→ViewRoot→递归移除矩阵 |
| VM-11 | R-16, AC-4.7 | 对照 UT | 普通事务清历史与 LostFocusToViewRoot 保历史 |
| VM-12 | R-17, AC-5.1 | UT | 窗口内多次 Update 仅一次 report/paint，最后候选提交 |
| VM-13 | R-18, AC-5.2~5.3 | 线程场景 UT | FreeNode attach 前状态、MarkNodeNotFree 和任务执行后清理结果 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| N/A | N/A | N/A | N/A | N/A | 已有焦点请求与清除能力补录，不新增 ArkTS、System API、InnerAPI 或 C API | AC-1.1~5.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|---------|
| N/A | N/A | 无 API 变更或废弃 | 无需迁移 | AC-1.1~5.3 |

## 接口规格

### 接口定义

本特性不新增接口。以下既有开放入口和内部入口用于限定当前实现行为；ArkTS canonical SDK 类型目录未随当前源码检出提供，ArkTS 签名仅以仓内 ETS/ANI 声明交叉核验，不扩张为新的 API 承诺。

**focusController.requestFocus**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void focusController.requestFocus(string key)` |
| 返回值 | `void`；失败通过业务错误异常表达 |
| 开放范围 | Public |
| 错误码 | `150001` 不可聚焦；`150002` 存在不可聚焦祖先；`150003` 不存在、不可见或禁用 |
| 关联 AC | AC-2.1~2.5, AC-2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| key | string | 是 | 无 | 必须匹配可搜索树或允许子窗口中的节点 ID；NAPI 入口要求恰好一个 string 参数（`js_focus_controller.cpp:54-68`） |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | 同步按 ID 请求成功或预检查失败 | Scenario Outline 2 | AC-2.3~2.5 |
| 2 | callback 映射业务错误 | Scenario 3 | AC-2.8 |

**focusController.clearFocus**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void focusController.clearFocus()` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| N/A | N/A | N/A | N/A | 当前 FocusView、ViewRoot 和历史子节点必须有效，否则按空检查提前返回（`focus_hub.cpp:595-621`） |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | 清焦到 ViewRoot | Scenario 6 | AC-4.7 |

**OH_ArkUI_FocusRequest**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_FocusRequest(ArkUI_NodeHandle node)` |
| 返回值 | `ArkUI_ErrorCode` — 请求预检查结果 |
| 开放范围 | Public C API，ArkUI Kit，`SystemCapability.ArkUI.ArkUI.Full`，since 15 |
| 错误码 | `0`、`150001`、`150002`、`150003` |
| 关联 AC | AC-1.3~1.7, AC-2.4, AC-2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| node | ArkUI_NodeHandle | 是 | 无 | 空句柄或无 FrameNode 返回 `150003`；有效节点经 ViewAbstract 同步预检查（`native_interface_focus.cpp:24-32`、`view_abstract.cpp:10338-10354`） |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | 节点直接请求 | Scenario Outline 2 | AC-2.4 |

**OH_ArkUI_FocusClear**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void OH_ArkUI_FocusClear(ArkUI_ContextHandle uiContext)` |
| 返回值 | `void` |
| 开放范围 | Public C API，ArkUI Kit，`SystemCapability.ArkUI.ArkUI.Full`，since 15 |
| 错误码 | 参数错误写入 native error message；函数无返回值 |
| 关联 AC | AC-4.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 空 Context 不执行清焦；有效 Context 转交 ViewAbstract::ClearFocus（`native_interface_focus.cpp:35-48`） |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | Native Context 清焦 | Scenario 6 | AC-4.7 |

**PipelineContext::RequestFocus**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool PipelineContext::RequestFocus(const std::string& targetNodeId, bool isSyncRequest = false)` |
| 返回值 | `bool` — 目标查找与当前快照预检查结果，不保证最终事务提交 |
| 开放范围 | 框架内部 |
| 错误码 | 通过 FocusManager callback/result code 旁路返回 |
| 关联 AC | AC-2.1~2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| targetNodeId | std::string | 是 | 无 | 在当前根、允许子窗口或父 Pipeline 中查找 |
| isSyncRequest | bool | 否 | false | true 执行严格同步预检查并立即 Flush；false 允许当前不可聚焦目标入槽 |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | 同步/异步按 ID 请求 | Scenario Outline 2 | AC-2.1~2.7 |

**FocusHub::RemoveSelf / RemoveChild / SwitchFocus**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void FocusHub::RemoveSelf(BlurReason reason)`；`void FocusHub::RemoveChild(const RefPtr<FocusHub>& child, BlurReason reason)`；`void FocusHub::SwitchFocus(const RefPtr<FocusHub>& child, FocusReason reason)` |
| 返回值 | `void` |
| 开放范围 | 框架内部 |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.3, AC-4.3~4.6, AC-5.2~5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| child | RefPtr<FocusHub> | 是 | 无 | RemoveChild 校验直接父关系；SwitchFocus 仅允许 SCOPE 且源码要求有效 child |
| reason | BlurReason/FocusReason | 是 | 对应枚举默认值由调用点决定 | BlurReason 沿失焦链传播；FocusReason 记录请求来源 |

**行为场景索引**

| # | 触发条件 | 对应 Gherkin | 关联 AC |
|---|----------|----------------|---------|
| 1 | Scope 子节点切换 | Scenario 4 | AC-3.1~3.4 |
| 2 | 聚焦子节点移除 | Scenario Outline 5 | AC-4.3~4.6 |
| 3 | FreeNode 延迟移除 | Scenario 8 | AC-5.2~5.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；本次仅补录当前实现。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；焦点请求和事务状态仅存在于运行时对象。
- **最低支持版本:** 与 NG 焦点框架现有支持范围一致；Native 焦点 C API 自 API 15 提供（`interfaces/native/native_interface_focus.h:16-77`）。
- **API 版本号策略:** Feat-02 核心请求、清除、切换和事务路径未发现 Target API 分支，不新增 `@since`。
- **ArkTS 声明核验:** 当前 ace_engine 检出不含 `interface/sdk-js/api/` canonical SDK 类型目录；`focusController.requestFocus/clearFocus` 已依据仓内 ANI ETS 与 NAPI 实现核验，仍标记为“未经 canonical d.ts 验证”。
- **运行时返回兼容性:** 同步按 ID 的 bool 仅代表预检查结果；异步 false 不代表未调度；callback 与整数错误码是独立通道。
- **生命周期兼容性:** FreeNode 的 RemoveSelf 在 attach 前后采用最终一致性，不承诺同步清理。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| UI Pipeline 串行化 | dirty focus 的写入和 Flush 必须在 UI 线程执行，且三类请求均为单槽位 | AC-1.2, AC-2.7 |
| 状态模型复用 | 准入必须复用 Feat-01 的 FocusType、focusable 和 whole-path 判定，不建立第二套状态 | AC-1.3~1.7, AC-2.4 |
| 最外层事务提交 | 嵌套 FocusGuard 不新建事务；最后一次 UpdateCurrentFocus 决定候选终点 | AC-3.4~3.6 |
| 层级一致性 | SwitchFocus 和 RemoveChild 只在 SCOPE 与直接焦点子关系上修改历史链 | AC-3.1~3.3, AC-4.4~4.6 |
| 关注点分离 | 导航候选算法归 Feat-03，FocusView 恢复目标归 Feat-05，视觉绘制细节归 Feat-06 | AC-4.5~4.7 |
| FreeNode 线程隔离 | FreeNode 不直接修改主焦点树，必须通过 after-attach task 执行 | AC-5.2, AC-5.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|---------|------|
| 性能 | 每次按 ID 请求在单个根内进行一次树查找；dirty focus 每类只保留一个弱引用，不形成无界请求队列 | 源码审查 + 性能回归 | `focus_hub.cpp:2480-2539`、`pipeline_context.h:1541-1543` |
| 功耗 | 每次异步请求最多触发一次 Pipeline RequestFrame，不新增周期任务 | 源码审查 | `pipeline_context.cpp:5463-5480` |
| 内存 | 事务仅持有当前/候选焦点弱引用或短生命周期 RefPtr；FreeNode pending task 随 attach 执行并移出列表 | 源码审查 + UT | `focus_manager.cpp:432-451`、`ui_node_multi_thread.cpp:120-130` |
| 安全 | 不新增权限或敏感数据；按 ID 请求不跨越未授权的 Container 搜索边界 | 架构审查 | `focus_hub.cpp:2512-2539` |
| 可靠性 | 失败返回、错误码、历史链清理与 ViewRoot 保留例外均有确定结果 | UT + 集成测试 | VM-2, VM-4, VM-7, VM-11 |
| 可测试性 | 18 条规则全部映射 VM；嵌套事务、通知时序和 FreeNode attach 场景需补充定向 UT | UT | VM-1~VM-13 |
| 自动化维测 | 保留 FocusReason、BlurReason、start/update/end reason 和节点 ID 日志 | 日志回归 | `focus_hub.cpp:533-579,1391-1398`、`focus_manager.cpp:493-502` |
| 定界定位 | 请求失败可区分不存在、自身不可聚焦、祖先不可聚焦；普通 Inner whole-path 失败粒度固定为祖先不可聚焦 | UT + 日志检查 | `focus_hub.cpp:546-560,937-956` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|---------|------|
| 手机 | 无差异 | 使用相同请求槽、FocusGuard 和移除事务 | UT | 核心实现无设备类型分支 |
| 平板 | 无差异 | 多窗口场景仍按 WindowFocusMoveStart/End 合并事务 | 多窗口集成测试 | `focus_manager.cpp:516-538` |
| 折叠屏 | 无差异 | 折叠状态不改变焦点请求、清除和提交语义 | 窗口切换回归 | 核心实现无折叠状态分支 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 普通焦点事务不替代无障碍焦点；节点移除时需确保两类焦点状态由各自子系统处理 | RemoveSelf/RemoveChild |
| 大字体 | 否 | 不涉及字体和布局度量 | N/A |
| 深色模式 | 否 | 焦点框颜色与样式由 Feat-06 定义 | N/A |
| 多窗口/分屏 | 是 | WindowScene 根选择、父 Pipeline 回退及窗口事务合并影响请求目标和通知次数 | AC-2.1, AC-5.1 |
| 多用户 | 否 | 无持久化和用户隔离数据 | N/A |
| 版本升级 | 是 | 核心路径无 Target API 分支，升级不得改变返回值与事务时序语义 | AC-2.5~2.8, AC-3.4~3.7 |
| 生态兼容 | 是 | 既有 ArkTS/C API 依赖错误码和清焦到 ViewRoot 的行为 | AC-2.4, AC-4.7 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 焦点请求、清除与切换事务
  作为 ArkUI 焦点框架调用方
  我想要请求、切换和清除操作按确定事务提交
  以便所有层级观察到一致的当前焦点

  Scenario: 普通异步请求进入 Pipeline
    Given 目标 FocusHub 当前未聚焦且 FocusType 为 NODE
    When 调用 RequestFocus
    Then Pipeline 的 dirtyFocusNode 单槽位指向该节点
    And Pipeline 请求下一帧

  Scenario Outline: 按 ID 请求返回语义
    Given ID 对应的目标节点当前状态为 <state>
    When 以 <mode> 模式调用 RequestFocusImmediatelyById
    Then 返回值为 <result>
    And 是否写入 dirtyRequestFocusNode 为 <scheduled>

    Examples:
      | state | mode | result | scheduled |
      | 可聚焦 | 同步 | true | true并立即Flush |
      | 不可聚焦 | 同步 | false | false |
      | 可聚焦 | 异步 | true | true |
      | 不可聚焦 | 异步 | false | true |

  Scenario: 同步请求失败映射
    Given 同步目标存在但自身 focusable 为 false
    When focusController.requestFocus 请求该目标
    Then 一次性回调报告 NON_FOCUSABLE
    And 公共入口抛出错误码 150001

  Scenario: SCOPE 切换不同子节点
    Given SCOPE 已聚焦且历史子节点为 oldChild
    When SwitchFocus 指向 newChild
    Then lastWeakFocusNode 更新为 newChild
    And oldChild 同步 LostFocus
    And FocusManager 的 switchingFocus 更新为该 SCOPE

  Scenario Outline: 聚焦子节点移除恢复
    Given 当前 SCOPE 的直接聚焦子节点将被移除
    When TAB 后继结果为 <tab> 且 SHIFT_TAB 前驱结果为 <shiftTab> 且当前 SCOPE 是 ViewRoot 为 <viewRoot>
    Then 恢复动作是 <action>

    Examples:
      | tab | shiftTab | viewRoot | action |
      | 成功 | 不执行 | false | 切换到TAB后继 |
      | 失败 | 成功 | false | 切换到SHIFT_TAB前驱 |
      | 失败 | 失败 | true | 停留在ViewRoot并设置根聚焦标记 |
      | 失败 | 失败 | false | 递归RemoveSelf |

  Scenario: 清焦到 ViewRoot 保留历史
    Given 当前 ViewRoot 的历史子节点正在聚焦
    When 调用 LostFocusToViewRoot
    Then 历史子节点 LostFocus
    And ViewRoot 的 lastWeakFocusNode 链被保留

  Scenario: 嵌套 FocusGuard 仅提交一次
    Given 最外层 FocusGuard 已以 REQUEST_FOCUS 启动
    When 内层请求创建 FocusGuard 并多次 UpdateCurrentFocus
    Then 内层 guard 不提交事务
    And 最外层析构时以最后一次 Update 的节点提交一次

  Scenario: FreeNode 延迟移除
    Given FocusHub 宿主是 FreeNode 且当前持有焦点状态
    When 调用 RemoveSelf
    Then 清理任务加入 after-attach tasks
    And 挂树前父焦点树尚未被修改
    When MarkNodeNotFree 执行 pending tasks
    Then 按普通 RemoveSelf 规则完成焦点迁移和清理
```

## Spec 自审清单

- [x] 无未关闭占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围明确覆盖请求、清除、切换与事务，并排除导航算法、FocusView 恢复策略和视觉细节
- [x] 无“快速”“稳定”“尽可能”等不可验证要求
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查
- [x] 同步/异步返回值、一次性回调、整数错误码和 Target API 扫描结论已记录
- [x] ArkTS canonical SDK 类型缺失已显式标注，Native C API 已按公开头文件核验
- [x] FreeNode attach 前后最终一致性和现有 UT 缺口已纳入 VM

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FocusHub RequestFocusImmediately、RequestFocusImmediatelyById 与 Pipeline dirty focus 调度语义"
  - repo: "openharmony/arkui_ace_engine"
    query: "FocusManager FocusGuard 嵌套事务、提交顺序、history 清理和窗口焦点合并"
  - repo: "openharmony/arkui_ace_engine"
    query: "FocusHub RemoveSelf RemoveChild LostFocusToViewRoot 与 FreeNode after-attach 清理"
```

**关键文档：** `frameworks/core/components_ng/event/focus_hub.cpp`、`frameworks/core/components_ng/manager/focus/focus_manager.cpp`、`frameworks/core/pipeline_ng/pipeline_context.cpp`、`interfaces/native/native_interface_focus.h`
