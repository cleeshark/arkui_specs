# 特性规格：C-API UIContextHandle接口

## 概述

| 属性 | 值 |
|------|------|
| 特性名称 | C-API UIContextHandle接口 |
| 特性编号 | Func-04-12-01-Feat-04 |
| 所属 Epic | UI 上下文 (04-12) |
| 优先级 | P1 |
| 目标版本 | API 12~26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

本特性规格覆盖 ace_engine C-API 层与 `ArkUI_ContextHandle` 相关的全部接口集合，包括类型定义（`ArkUI_ContextHandle` typedef、`ArkUI_Context` 结构体、Arkoala 内部 `ArkUIContext` 结构体）、3 个创建 API（`OH_ArkUI_GetContextByNode`、`OH_ArkUI_GetContextFromNapiValue`、`OH_ArkUI_NativeModule_GetContextFromAniValue`）、6 个任务投递使用 API（`OH_ArkUI_RunTaskInScope`、`OH_ArkUI_PostUITask`、`OH_ArkUI_PostUITaskAndWait`、`OH_ArkUI_PostAsyncUITask`、`OH_ArkUI_PostFrameCallback`、`OH_ArkUI_PostIdleCallback`）、4 个焦点控制使用 API（`OH_ArkUI_FocusClear`、`OH_ArkUI_FocusActivate`、`OH_ArkUI_FocusSetAutoTransfer`、`OH_ArkUI_FocusSetKeyProcessingMode`）、4 个拖放使用 API（`OH_ArkUI_CreateDragActionWithContext`、`OH_ArkUI_SetDragEventStrictReportWithContext`、`OH_ArkUI_CancelDataLoading`、`OH_ArkUI_EnableDropDisallowedBadge`）、3 个动画使用 API（`animateTo`、`keyframeAnimateTo`、`createAnimator`）、3 个其他使用 API（`OH_ArkUI_SetForceDarkConfig`、`OH_ArkUI_EnableEventPassthrough`、`OH_ArkUI_NativeModule_GetPageRootNodeHandleByContext`）。共计 22 个接口 + 3 个类型定义。

**关键架构约束（须重点关注）**：

1. **MEMORY LEAK (P1)**：3 个创建 API 均通过 `new ArkUI_Context({ .id = instanceId })` 堆分配，但不存在任何 `OH_ArkUI_Context_Destroy/Release/Free/Dispose` API 释放该内存。每次调用产生 8 字节不可回收的堆对象，长期运行的 NDK 应用存在系统性内存泄漏。源码：`node_adapter_impl.cpp:256`、`native_node_napi.cpp:174`、`native_node_ani.cpp:229`

2. **TYPE CONFUSION (P1)**：`OH_ArkUI_CreateDragActionWithContext` 将 `ArkUI_Context*`（8 字节结构体 `{int32_t id}`）通过 `reinterpret_cast` 转换为 `ArkUIContext*`（丰富的 C++ 类），按 C++ 标准属于未定义行为（UB）。当前因内存布局巧合（`ArkUIContext` 的 `instanceId_` 字段恰好位于首 4 字节偏移处）而"运行正确"，但任何 `ArkUIContext` 类布局变更将导致崩溃。源码：`drag_and_drop_impl.cpp:184`

3. **NAMING INCONSISTENCY (P2)**：C-API 命名使用 `ArkUI_ContextHandle` 而非对应 ArkTS 层 `UIContextHandle` 语义名称；创建函数 `OH_ArkUI_GetContextByNode` 而非 `GetUIContextHandle`。命名与 ArkTS 层概念不对齐，增加开发者理解成本。源码：`native_type.h:194`、`native_node.h:13717`

4. **INCONSISTENT ROUTING (P2)**：大多数使用 API 通过 `contextHandle->id` 提取 `instanceId` 后使用 `ContainerScope(id)` 路由到正确 PipelineContext；但 `OH_ArkUI_CancelDataLoading` 和 `OH_ArkUI_EnableDropDisallowedBadge` 不实际路由通过 `instanceId`，破坏统一桥接模式一致性。源码：`drag_and_drop_impl.cpp:886`、`drag_and_drop_impl.cpp:983`

5. **DUAL TYPEDEF (P2)**：`ArkUI_ContextHandle` 在 `native_type.h:194` 和 `drag_and_drop.h:146` 中均有 `typedef struct ArkUI_Context* ArkUI_ContextHandle` 定义，完全相同但位于不同头文件，违反 ODR（One Definition Rule）原则。源码：`native_type.h:194`、`drag_and_drop.h:146`

6. **VESTIGIAL PARAM (P3)**：`OH_ArkUI_CancelDataLoading` 的 `uiContext` 参数在实现中未使用（残余参数），实现中参数名拼写为 `"uiContent"`（typo）。源码：`drag_and_drop_impl.cpp:886`

7. **NO NULL SAFETY**：大多数使用 API 对 `ArkUI_ContextHandle` 参数不做 null 检查，传入 nullptr 时直接解引用 `.id` 字段，导致段错误。唯一例外为 `OH_ArkUI_SetForceDarkConfig`，其 nullptr 参数有明确语义（应用级全局设置）。

## 本次变更范围（Delta）

本规格为既有 API 的 **补录规格（backfill）**，不引入新增/变更/废弃 API。所有接口均已存在于 ace_engine 实现中，本规格仅对实现行为进行规格化描述。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ArkUI_ContextHandle / ArkUI_Context 类型定义规格 | 已有实现补录（@since 12），标注重复 typedef ODR 风险 + 命名不一致风险 |
| ADDED | ArkUIContext (Arkoala 内部) 类型定义规格 | 已有实现补录（arkoala_api.h:2250-2252），标注与 ArkUI_Context 的布局巧合依赖 |
| ADDED | OH_ArkUI_GetContextByNode 规格 | 已有实现补录（@since 12），标注内存泄漏风险 |
| ADDED | OH_ArkUI_GetContextFromNapiValue 规格 | 已有实现补录（@since 12），标注内存泄漏风险 |
| ADDED | OH_ArkUI_NativeModule_GetContextFromAniValue 规格 | 已有实现补录（@since 22），标注内存泄漏风险 |
| ADDED | OH_ArkUI_RunTaskInScope 规格 | 已有实现补录（@since 20） |
| ADDED | OH_ArkUI_PostAsyncUITask 规格 | 已有实现补录（@since 22） |
| ADDED | OH_ArkUI_PostUITask 规格 | 已有实现补录（@since 22） |
| ADDED | OH_ArkUI_PostUITaskAndWait 规格 | 已有实现补录（@since 22） |
| ADDED | OH_ArkUI_PostFrameCallback 规格 | 已有实现补录（@since 16） |
| ADDED | OH_ArkUI_PostIdleCallback 规格 | 已有实现补录（@since 20） |
| ADDED | OH_ArkUI_FocusClear 规格 | 已有实现补录（@since 15） |
| ADDED | OH_ArkUI_FocusActivate 规格 | 已有实现补录（@since 15），含 isAutoInactive 参数 |
| ADDED | OH_ArkUI_FocusSetAutoTransfer 规格 | 已有实现补录（@since 15） |
| ADDED | OH_ArkUI_FocusSetKeyProcessingMode 规格 | 已有实现补录（@since 15） |
| ADDED | OH_ArkUI_CreateDragActionWithContext 规格 | 已有实现补录（@since 12），标注 TYPE CONFUSION 风险 |
| ADDED | OH_ArkUI_SetDragEventStrictReportWithContext 规格 | 已有实现补录（@since 12） |
| ADDED | OH_ArkUI_CancelDataLoading 规格 | 已有实现补录（@since 15），标注 vestigial param + typo + 不路由 instanceId |
| ADDED | OH_ArkUI_EnableDropDisallowedBadge 规格 | 已有实现补录（@since 20），标注不路由 instanceId |
| ADDED | animateTo 规格 | 已有实现补录（@since 12），vtable struct member |
| ADDED | keyframeAnimateTo 规格 | 已有实现补录（@since 12），vtable struct member |
| ADDED | createAnimator 规格 | 已有实现补录（@since 12），vtable struct member |
| ADDED | OH_ArkUI_SetForceDarkConfig 规格 | 已有实现补录（@since 20），标注 nullptr=应用级语义 |
| ADDED | OH_ArkUI_EnableEventPassthrough 规格 | 已有实现补录（@since 26） |
| ADDED | OH_ArkUI_NativeModule_GetPageRootNodeHandleByContext 规格 | 已有实现补录（@since 24） |

## 输入文档

| 文档类型 | 文档名称 | 版本/日期 | 备注 |
|----------|----------|-----------|------|
| C-API 头文件 | `native_type.h` | 当前 | ArkUI_ContextHandle typedef (@since 12, line 194) |
| C-API 头文件 | `native_node.h` | 当前 | GetContextByNode (line 13717) / RunTaskInScope (line 13957) / PostAsyncUITask (line 14018) / PostUITask (line 14032) / PostUITaskAndWait (line 14045) / SetForceDarkConfig (line 14062) / GetPageRootNodeHandleByContext (line 14343) 声明 |
| C-API 头文件 | `native_node_napi.h` | 当前 | GetContextFromNapiValue (line 58) / PostFrameCallback (line 375) / PostIdleCallback (line 394) / EnableEventPassthrough (line 409) 声明 |
| C-API 头文件 | `native_node_ani.h` | 当前 | GetContextFromAniValue (line 48) 声明 |
| C-API 头文件 | `native_interface_focus.h` | 当前 | FocusClear (line 77) / FocusActivate (line 89) / FocusSetAutoTransfer (line 98) / FocusSetKeyProcessingMode (line 107) 声明 |
| C-API 头文件 | `drag_and_drop.h` | 当前 | 重复 ArkUI_ContextHandle typedef (line 146) / CancelDataLoading (line 574) / SetDragEventStrictReportWithContext (line 627) / CreateDragActionWithContext (line 812) / EnableDropDisallowedBadge (line 1075) 声明 |
| C-API 头文件 | `native_animate.h` | 当前 | animateTo (line 98) / keyframeAnimateTo (line 101) / createAnimator (line 102) vtable 声明 |
| 内部结构定义 | `node_module_inner.h` | 当前 | ArkUI_Context 结构体定义 (line 21-23) |
| Arkoala IDL | `arkoala_api.h` | 当前 | ArkUIContext 结构体定义 (line 2250-2252) |
| C-API 实现 | `node_adapter_impl.cpp` | 当前 | OH_ArkUI_GetContextByNode 实现 (line 256-268) |
| C-API 实现 | `native_node_napi.cpp` | 当前 | OH_ArkUI_GetContextFromNapiValue / PostFrameCallback / PostIdleCallback / EnableEventPassthrough 实现 |
| C-API 实现 | `native_node_ani.cpp` | 当前 | OH_ArkUI_NativeModule_GetContextFromAniValue 实现 |
| C-API 实现 | `node_utils.cpp` | 当前 | RunTaskInScope / SetForceDarkConfig / GetPageRootNodeHandleByContext 实现 |
| C-API 实现 | `node_model_safely.cpp` | 当前 | PostAsyncUITask / PostUITask / PostUITaskAndWait 实现 |
| C-API 实现 | `native_interface_focus.cpp` | 当前 | FocusClear / FocusActivate / FocusSetAutoTransfer / FocusSetKeyProcessingMode 实现 |
| C-API 实现 | `drag_and_drop_impl.cpp` | 当前 | CancelDataLoading / SetDragEventStrictReportWithContext / CreateDragActionWithContext / EnableDropDisallowedBadge 实现 |
| C-API 实现 | `animate_impl.cpp` | 当前 | animateTo / keyframeAnimateTo / createAnimator 实现 |
| 单测文件 | `native_node_test.cpp` | 当前 | RunTaskInScope / FocusClear / FocusActivate 等 |
| 单测文件 | `native_node_napi_test.cpp` | 当前 | GetContextFromNapiValue / PostFrameCallback 等 |
| 单测文件 | `animate_impl_test.cpp` | 当前 | animateTo / keyframeAnimateTo / createAnimator |
| 单测文件 | `drag_and_drop_test.cpp` | 当前 | CreateDragActionWithContext 等 |

## 用户故事

| US-ID | 用户故事 | 关联 AC |
|-------|----------|---------|
| US-04.1 | 作为 NDK 应用开发者，我想要了解 `ArkUI_ContextHandle` 类型定义并通过 `OH_ArkUI_GetContextByNode`、`OH_ArkUI_GetContextFromNapiValue` 或 `OH_ArkUI_NativeModule_GetContextFromAniValue` 创建 `ArkUI_ContextHandle`，以便获取 UI 实例 ID 用于后续 C-API 调用 | AC-04.1.1~AC-04.1.11 |
| US-04.2 | 作为 NDK 应用开发者，我想要通过 `OH_ArkUI_RunTaskInScope`、`OH_ArkUI_PostUITask`、`OH_ArkUI_PostUITaskAndWait`、`OH_ArkUI_PostAsyncUITask`、`OH_ArkUI_PostFrameCallback`、`OH_ArkUI_PostIdleCallback` 在指定 UIContext 作用域下投递和执行任务，以便在多实例场景下确保任务在正确的 UI 实例中运行 | AC-04.2.1~AC-04.2.7 |
| US-04.3 | 作为 NDK 应用开发者，我想要通过 `OH_ArkUI_FocusClear`、`OH_ArkUI_FocusActivate`、`OH_ArkUI_FocusSetAutoTransfer`、`OH_ArkUI_FocusSetKeyProcessingMode` 进行焦点控制，以便在 NDK 场景下管理焦点行为 | AC-04.3.1~AC-04.3.5 |
| US-04.4 | 作为 NDK 应用开发者，我想要通过 `OH_ArkUI_CreateDragActionWithContext`、`OH_ArkUI_SetDragEventStrictReportWithContext`、`OH_ArkUI_CancelDataLoading`、`OH_ArkUI_EnableDropDisallowedBadge` 执行拖放操作，以便在 NDK 场景下管理拖放行为 | AC-04.4.1~AC-04.4.5 |
| US-04.5 | 作为 NDK 应用开发者，我想要通过 `animateTo`、`keyframeAnimateTo`、`createAnimator` 执行动画控制，以便在 NDK 场景下触发显式动画和关键帧动画 | AC-04.5.1~AC-04.5.4 |
| US-04.6 | 作为 NDK 应用开发者，我想要通过 `OH_ArkUI_SetForceDarkConfig`、`OH_ArkUI_EnableEventPassthrough`、`OH_ArkUI_NativeModule_GetPageRootNodeHandleByContext` 执行与 UIContext 相关的其他操作，以便控制强制暗色模式、事件穿透和获取页面根节点 | AC-04.6.1~AC-04.6.4 |
| US-04.7 | 作为 NDK 应用开发者/架构审查者，我想要了解 ArkUI_ContextHandle 从创建到使用的完整桥接模式、内存生命周期和命名一致性风险，以便评估内存泄漏影响、TYPE CONFUSION 风险等级和命名不一致的维护成本 | AC-04.7.1~AC-04.7.8 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-04.1.1 | R-04.1 | TASK-SPEC-04 | 源码审查 + 单测 | node_adapter_impl.cpp:256-268, native_node_test.cpp |
| AC-04.1.2 | R-04.2 | TASK-SPEC-04 | 边界分析 | 每次 new ArkUI_Context |
| AC-04.1.3 | R-04.3 | TASK-SPEC-04 | 源码审查 + 单测 | native_node_napi.cpp:174, native_node_napi_test.cpp |
| AC-04.1.4 | R-04.4 | TASK-SPEC-04 | 源码审查 | native_node_ani.cpp:229 |
| AC-04.1.5 | R-04.5 | TASK-SPEC-04 | 源码审查 | native_type.h:194 |
| AC-04.1.6 | R-04.6 | TASK-SPEC-04 | 源码审查 | node_module_inner.h:21-23 |
| AC-04.1.7 | R-04.7 | TASK-SPEC-04 | 源码审查 | arkoala_api.h:2250-2252 |
| AC-04.1.8 | R-04.8 | TASK-SPEC-04 | 源码审查 | drag_and_drop.h:146 vs native_type.h:194 |
| AC-04.1.9 | R-04.9 | TASK-SPEC-04 | API 缺失确认 | 全仓无 OH_ArkUI_Context_Destroy |
| AC-04.1.10 | R-04.10 | TASK-SPEC-04 | 源码审查 | node_adapter_impl.cpp:256 |
| AC-04.1.11 | R-04.11 | TASK-SPEC-04 | 命名分析 | native_type.h:194, native_node.h:13717 |
| AC-04.2.1 | R-04.12 | TASK-SPEC-04 | 源码审查 + 单测 | node_utils.cpp:793, native_node_test.cpp |
| AC-04.2.2 | R-04.13 | TASK-SPEC-04 | 源码审查 | node_model_safely.cpp:54 |
| AC-04.2.3 | R-04.14 | TASK-SPEC-04 | 源码审查 | node_model_safely.cpp:77 |
| AC-04.2.4 | R-04.15 | TASK-SPEC-04 | 源码审查 | node_model_safely.cpp:29 |
| AC-04.2.5 | R-04.16 | TASK-SPEC-04 | 源码审查 + 单测 | native_node_napi.cpp:684, native_node_napi_test.cpp |
| AC-04.2.6 | R-04.17 | TASK-SPEC-04 | 源码审查 + 单测 | native_node_napi.cpp:709, native_node_napi_test.cpp |
| AC-04.2.7 | R-04.10 | TASK-SPEC-04 | 源码审查 | 各实现无 null 检查 |
| AC-04.3.1 | R-04.18 | TASK-SPEC-04 | 源码审查 + 单测 | native_interface_focus.cpp:35, native_node_test.cpp |
| AC-04.3.2 | R-04.19 | TASK-SPEC-04 | 源码审查 | native_interface_focus.cpp:50 |
| AC-04.3.3 | R-04.20 | TASK-SPEC-04 | 源码审查 | native_interface_focus.cpp:65 |
| AC-04.3.4 | R-04.21 | TASK-SPEC-04 | 源码审查 | native_interface_focus.cpp:82 |
| AC-04.3.5 | R-04.10 | TASK-SPEC-04 | 源码审查 | native_interface_focus.cpp 各函数无 null 检查 |
| AC-04.4.1 | R-04.22 | TASK-SPEC-04 | 源码审查 + 单测 | drag_and_drop_impl.cpp:184, drag_and_drop_test.cpp |
| AC-04.4.2 | R-04.23 | TASK-SPEC-04 | 源码审查 | drag_and_drop_impl.cpp:631 |
| AC-04.4.3 | R-04.24 | TASK-SPEC-04 | 源码审查 | drag_and_drop_impl.cpp:886 |
| AC-04.4.4 | R-04.25 | TASK-SPEC-04 | 源码审查 | drag_and_drop_impl.cpp:983 |
| AC-04.4.5 | R-04.26 | TASK-SPEC-04 | 架构分析 | ArkUIContext 内存布局 |
| AC-04.5.1 | R-04.27 | TASK-SPEC-04 | 源码审查 | native_animate.h:98-102 |
| AC-04.5.2 | R-04.28 | TASK-SPEC-04 | 源码审查 + 单测 | animate_impl.cpp:25, animate_impl_test.cpp |
| AC-04.5.3 | R-04.29 | TASK-SPEC-04 | 源码审查 + 单测 | animate_impl.cpp:67 |
| AC-04.5.4 | R-04.30 | TASK-SPEC-04 | 源码审查 + 单测 | animate_impl.cpp:164 |
| AC-04.6.1 | R-04.31 | TASK-SPEC-04 | 源码审查 | node_utils.cpp:808 |
| AC-04.6.2 | R-04.31 | TASK-SPEC-04 | 源码审查 | node_utils.cpp:808 |
| AC-04.6.3 | R-04.32 | TASK-SPEC-04 | 源码审查 | native_node_napi.cpp:734 |
| AC-04.6.4 | R-04.33 | TASK-SPEC-04 | 源码审查 | node_utils.cpp:1068 |
| AC-04.7.1 | R-04.34 | TASK-SPEC-04 | 源码审查 | ArkUIFullNodeAPI 分发路径 |
| AC-04.7.2 | R-04.35 | TASK-SPEC-04 | 源码审查 | 各使用 API 的 reinterpret_cast + ContainerScope 路径 |
| AC-04.7.3 | R-04.9 | TASK-SPEC-04 | 内存分析 | sizeof(ArkUI_Context) = 8 |
| AC-04.7.4 | R-04.26 | TASK-SPEC-04 | 架构分析 | drag_and_drop_impl.cpp:184 |
| AC-04.7.5 | R-04.8 | TASK-SPEC-04 | 源码审查 | native_type.h:194 vs drag_and_drop.h:146 |
| AC-04.7.6 | R-04.24 | TASK-SPEC-04 | 源码审查 | drag_and_drop_impl.cpp:886 |
| AC-04.7.7 | R-04.25, R-04.36 | TASK-SPEC-04 | 源码审查 | drag_and_drop_impl.cpp:886, :983 |
| AC-04.7.8 | R-04.11 | TASK-SPEC-04 | 命名分析 | native_type.h:194 vs ArkTS UIContext 命名 |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|----------|----------|-----------|---------|
| R-04.1 | 行为 | OH_ArkUI_GetContextByNode 传入有效节点 | new ArkUI_Context({.id = instanceId}) 堆分配并返回 | node_adapter_impl.cpp:256-268 | AC-04.1.1 |
| R-04.2 | 边界 | 多次调用 OH_ArkUI_GetContextByNode | 每次调用均产生新的堆分配对象 | 不做缓存或复用 | AC-04.1.2 |
| R-04.3 | 行为 | OH_ArkUI_GetContextFromNapiValue 传入有效 env+value | 同 R-04.1，new ArkUI_Context 堆分配 | native_node_napi.cpp:174 | AC-04.1.3 |
| R-04.4 | 行为 | OH_ArkUI_NativeModule_GetContextFromAniValue 传入有效 ani_env+ani_ref | 同 R-04.1，new ArkUI_Context 堆分配 | native_node_ani.cpp:229 | AC-04.1.4 |
| R-04.5 | 行为 | ArkUI_ContextHandle typedef | `typedef struct ArkUI_Context* ArkUI_ContextHandle` | native_type.h:194 (@since 12) | AC-04.1.5 |
| R-04.6 | 行为 | ArkUI_Context 结构体定义 | 仅包含 `{ int32_t id; }` 字段 | node_module_inner.h:21-23 | AC-04.1.6 |
| R-04.7 | 行为 | ArkUIContext (Arkoala) 结构体定义 | 仅包含 `{ ArkUI_Int32 id; }` 字段，与 ArkUI_Context 偏移巧合依赖 | arkoala_api.h:2250-2252 | AC-04.1.7 |
| R-04.8 | 异常 | ArkUI_ContextHandle 重复 typedef | drag_and_drop.h:146 与 native_type.h:194 完全相同，ODR 风险 | drag_and_drop.h:146 (@since 12) | AC-04.1.8, AC-04.7.5 |
| R-04.9 | 异常 | 3 个创建 API 堆分配后无法释放 | 无 OH_ArkUI_Context_Destroy/Release/Free/Dispose API | 系统性内存泄漏，每次调用 8 字节不可回收 | AC-04.1.9, AC-04.7.3 |
| R-04.10 | 异常 | contextHandle 为 nullptr | 无 null 检查，直接解引用 ->id 导致段错误 | 所有使用 API 均无 null 检查（SetForceDarkConfig 除外） | AC-04.1.10, AC-04.2.7, AC-04.3.5 |
| R-04.11 | 边界 | C-API 命名使用 ArkUI_ContextHandle | 与 ArkTS 层 UIContextHandle 概念不对齐；创建函数命名 OH_ArkUI_GetContextByNode 而非 GetUIContextHandle | 增加开发者理解成本 | AC-04.1.11, AC-04.7.8 |
| R-04.12 | 行为 | OH_ArkUI_RunTaskInScope | ContainerScope::CurrentId(contextHandle->id) 设置作用域，执行 callback | node_utils.cpp:793 (@since 20) | AC-04.2.1 |
| R-04.13 | 行为 | OH_ArkUI_PostUITask | 向 UIContext 同步投递 UI 任务 | node_model_safely.cpp:54 (@since 22) | AC-04.2.2 |
| R-04.14 | 行为 | OH_ArkUI_PostUITaskAndWait | 投递 UI 任务并等待执行完成 | node_model_safely.cpp:77 (@since 22) | AC-04.2.3 |
| R-04.15 | 行为 | OH_ArkUI_PostAsyncUITask | 向 UIContext 异步投递 UI 任务 | node_model_safely.cpp:29 (@since 22) | AC-04.2.4 |
| R-04.16 | 行为 | OH_ArkUI_PostFrameCallback | 注册帧回调，每帧渲染后执行 | native_node_napi.cpp:684 (@since 16) | AC-04.2.5 |
| R-04.17 | 行为 | OH_ArkUI_PostIdleCallback | 注册空闲回调，UI 线程空闲时执行 | native_node_napi.cpp:709 (@since 20) | AC-04.2.6 |
| R-04.18 | 行为 | OH_ArkUI_FocusClear | 清除 UIContext 焦点 | native_interface_focus.cpp:35 (@since 15) | AC-04.3.1 |
| R-04.19 | 行为 | OH_ArkUI_FocusActivate | 设置焦点激活状态与自动失活模式（含 isAutoInactive 参数） | native_interface_focus.cpp:50 (@since 15) | AC-04.3.2 |
| R-04.20 | 行为 | OH_ArkUI_FocusSetAutoTransfer | 设置焦点自动转移 | native_interface_focus.cpp:65 (@since 15) | AC-04.3.3 |
| R-04.21 | 行为 | OH_ArkUI_FocusSetKeyProcessingMode | 设置按键处理模式 | native_interface_focus.cpp:82 (@since 15) | AC-04.3.4 |
| R-04.22 | 异常 | TYPE CONFUSION — OH_ArkUI_CreateDragActionWithContext | reinterpret_cast ArkUI_Context* 到 ArkUIContext*，C++ UB | drag_and_drop_impl.cpp:184 | AC-04.4.1, AC-04.4.5 |
| R-04.23 | 行为 | OH_ArkUI_SetDragEventStrictReportWithContext | 设置拖拽事件严格上报模式 | drag_and_drop_impl.cpp:631 (@since 12) | AC-04.4.2 |
| R-04.24 | 异常 | OH_ArkUI_CancelDataLoading vestigial param + typo + 不路由 instanceId | uiContext 参数未使用，实现中参数名拼写为 "uiContent"，不路由通过 instanceId | drag_and_drop_impl.cpp:886 | AC-04.4.3, AC-04.7.6 |
| R-04.25 | 边界 | OH_ArkUI_EnableDropDisallowedBadge 不路由 instanceId | 不通过 contextHandle->id 路由到 PipelineContext，破坏统一桥接模式一致性 | drag_and_drop_impl.cpp:983 | AC-04.4.4, AC-04.7.7 |
| R-04.26 | 边界 | TYPE CONFUSION 内存布局巧合 | ArkUI_Context* (8字节) 被当作 ArkUIContext* 使用，仅访问 instanceId_ 字段时因偏移巧合运行正常 | 任何 ArkUIContext 布局变更将导致崩溃 | AC-04.4.5, AC-04.7.4 |
| R-04.27 | 行为 | OH_ArkUI_QueryModuleInterfaceByName(ARKUI_NATIVE_ANIMATE) | 返回 ArkUI_NativeAnimateAPI_1 vtable 结构体 | native_animate.h:98-102 | AC-04.5.1 |
| R-04.28 | 行为 | animateTo vtable member | 通过 ArkUI_NativeAnimateAPI_1 vtable 触发显式动画 | animate_impl.cpp:25 (@since 12) | AC-04.5.2 |
| R-04.29 | 行为 | keyframeAnimateTo vtable member | 通过 vtable 触发关键帧动画 | animate_impl.cpp:67 (@since 12) | AC-04.5.3 |
| R-04.30 | 行为 | createAnimator vtable member | 通过 vtable 创建 Animator 对象 | animate_impl.cpp:164 (@since 12) | AC-04.5.4 |
| R-04.31 | 行为 | OH_ArkUI_SetForceDarkConfig | nullptr contextHandle = 应用级全局设置；非 nullptr = UIContext 级设置 | node_utils.cpp:808 (@since 20) | AC-04.6.1, AC-04.6.2 |
| R-04.32 | 行为 | OH_ArkUI_EnableEventPassthrough | 启用/禁用指定类型的事件穿透 | native_node_napi.cpp:734 (@since 26) | AC-04.6.3 |
| R-04.33 | 行为 | OH_ArkUI_NativeModule_GetPageRootNodeHandleByContext | 通过 contextHandle->id 获取 PipelineContext，返回页面根节点 | node_utils.cpp:1068 (@since 24) | AC-04.6.4 |
| R-04.34 | 行为 | ArkUIFullNodeAPI dispatches | 通过 getBasicAPI()/getAnimation()/getNodeModifiers()/getDragAdapterAPI()/getMultiThreadManagerAPI() 获取子模块 API | node_module.h | AC-04.7.1 |
| R-04.35 | 行为 | 大多数使用 API 桥接模式 | ArkUI_ContextHandle → reinterpret_cast<ArkUI_Context*>(handle) → extract id → ContainerScope(id) → access PipelineContext | ADR continuation | AC-04.7.2 |
| R-04.36 | 异常 | 不一致路由：部分 API 不路由 instanceId | CancelDataLoading 和 EnableDropDisallowedBadge 不通过 instanceId 路由，与大多数使用 API 行为不一致 | drag_and_drop_impl.cpp:886, :983 | AC-04.7.7 |

## 验证映射

| VM-ID | 验证方法 | 关联 US/AC/R | 验证重点 |
|-------|----------|-------------|----------|
| VM-04.1 | 源码审查 + 单测 | US-04.1 / AC-04.1.1~04.1.11 / R-04.1~04.11 | 堆分配模式、无 Destroy API、重复 typedef、nullptr 安全、命名不一致、Arkoala 偏移依赖 |
| VM-04.2 | 源码审查 + 单测 | US-04.2 / AC-04.2.1~04.2.7 / R-04.12~04.17, R-04.10 | RunTaskInScope ContainerScope 作用域设置、PostUITask/PostUITaskAndWait/PostAsyncUITask 投递逻辑、PostFrameCallback/PostIdleCallback 帧回调、nullptr 段错误 |
| VM-04.3 | 源码审查 + 单测 | US-04.3 / AC-04.3.1~04.3.5 / R-04.18~04.21, R-04.10 | FocusClear/FocusActivate(含isAutoInactive)/FocusSetAutoTransfer/FocusSetKeyProcessingMode 焦点控制、nullptr 安全 |
| VM-04.4 | 源码审查 + 单测 | US-04.4 / AC-04.4.1~04.4.5 / R-04.22~04.26 | CreateDragActionWithContext TYPE CONFUSION、CancelDataLoading vestigial param + typo + 不路由、EnableDropDisallowedBadge 不路由 |
| VM-04.5 | 源码审查 + 单测 | US-04.5 / AC-04.5.1~04.5.4 / R-04.27~04.30 | ArkUI_NativeAnimateAPI_1 vtable 获取、animateTo/keyframeAnimateTo/createAnimator 实现 |
| VM-04.6 | 源码审查 | US-04.6 / AC-04.6.1~04.6.4 / R-04.31~04.33 | SetForceDarkConfig nullptr=应用级语义、EnableEventPassthrough 事件穿透、GetPageRootNodeHandleByContext 页面根节点 |
| VM-04.7 | 架构分析 + 内存分析 | US-04.7 / AC-04.7.1~04.7.8 / R-04.34~04.36, R-04.8~04.9, R-04.11, R-04.24~04.26 | ArkUIFullNodeAPI 分发路径、统一桥接模式与不一致路由、内存泄漏量估算、TYPE CONFUSION UB 评估、ODR 风险、vestigial param typo、命名不一致 |

## API 变更分析

### 新增 API

#### 类型定义

| API 名称 | 开放范围 | 定义概要 | 功能描述 | 关联 AC |
|----------|----------|----------|----------|---------|
| ArkUI_ContextHandle | Public (@since 12) | `typedef struct ArkUI_Context* ArkUI_ContextHandle` (native_type.h:194) | 不透明上下文句柄 typedef | AC-04.1.5 |
| ArkUI_Context | Internal | `struct ArkUI_Context { int32_t id; }` (node_module_inner.h:21-23) | 仅含 instanceId 的轻量结构体 | AC-04.1.6 |
| ArkUIContext (Arkoala) | Internal | `struct ArkUIContext { ArkUI_Int32 id; }` (arkoala_api.h:2250-2252) | Arkoala 内部结构体，与 ArkUI_Context 偏移巧合依赖 | AC-04.1.7 |

#### 创建 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| OH_ArkUI_GetContextByNode | Public (@since 12) | node: ArkUI_NodeHandle | ArkUI_ContextHandle | 无错误码 | 通过节点获取上下文句柄（堆分配） | AC-04.1.1, AC-04.1.2 |
| OH_ArkUI_GetContextFromNapiValue | System (@since 12) | env: napi_env, value: napi_value | ArkUI_ContextHandle | 无错误码 | 从 NAPI 值获取上下文句柄（堆分配） | AC-04.1.3 |
| OH_ArkUI_NativeModule_GetContextFromAniValue | System (@since 22) | env: ani_env*, value: ani_object | ArkUI_ContextHandle | 无错误码 | 从 ANI 值获取上下文句柄（堆分配） | AC-04.1.4 |

#### 任务投递 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| OH_ArkUI_RunTaskInScope | Public (@since 20) | contextHandle: ArkUI_ContextHandle, callback: void(*)(void*), userData: void* | ArkUI_ErrorCode | 0 (SUCCESS) | 在 UIContext 作用域下执行回调 | AC-04.2.1 |
| OH_ArkUI_PostUITask | Public (@since 22) | contextHandle: ArkUI_ContextHandle, taskData: void*, task: void(*)(void*) | ArkUI_ErrorCode | 0 (SUCCESS) | 同步投递 UI 任务 | AC-04.2.2 |
| OH_ArkUI_PostUITaskAndWait | Public (@since 22) | contextHandle: ArkUI_ContextHandle, taskData: void*, task: void(*)(void*) | ArkUI_ErrorCode | 0 (SUCCESS) | 投递并等待 UI 任务完成 | AC-04.2.3 |
| OH_ArkUI_PostAsyncUITask | Public (@since 22) | contextHandle: ArkUI_ContextHandle, ... | ArkUI_ErrorCode | 0 (SUCCESS) | 异步投递 UI 任务 | AC-04.2.4 |
| OH_ArkUI_PostFrameCallback | Public (@since 16) | uiContext: ArkUI_ContextHandle, userData: void*, callback: ArkUI_FrameCallback* | int32_t | 0 (SUCCESS) | 注册帧回调 | AC-04.2.5 |
| OH_ArkUI_PostIdleCallback | Public (@since 20) | uiContext: ArkUI_ContextHandle, userData: void*, callback: ArkUI_IdleCallback* | int32_t | 0 (SUCCESS) | 注册空闲回调 | AC-04.2.6 |

#### 焦点控制 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| OH_ArkUI_FocusClear | Public (@since 15) | uiContext: ArkUI_ContextHandle | ArkUI_ErrorCode | 0 (SUCCESS) | 清除焦点 | AC-04.3.1 |
| OH_ArkUI_FocusActivate | Public (@since 15) | uiContext: ArkUI_ContextHandle, isActive: bool, isAutoInactive: bool | ArkUI_ErrorCode | 0 (SUCCESS) | 设置焦点激活状态与自动失活 | AC-04.3.2 |
| OH_ArkUI_FocusSetAutoTransfer | Public (@since 15) | uiContext: ArkUI_ContextHandle, autoTransfer: bool | ArkUI_ErrorCode | 0 (SUCCESS) | 设置焦点自动转移 | AC-04.3.3 |
| OH_ArkUI_FocusSetKeyProcessingMode | Public (@since 15) | uiContext: ArkUI_ContextHandle, mode: ArkUI_KeyProcessingMode | ArkUI_ErrorCode | 0 (SUCCESS) | 设置按键处理模式 | AC-04.3.4 |

#### 拖放 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| OH_ArkUI_CreateDragActionWithContext | Public (@since 12) | contextHandle: ArkUI_ContextHandle, ... | ArkUI_DragAction* | 0 (SUCCESS) | 创建拖拽动作（TYPE CONFUSION） | AC-04.4.1 |
| OH_ArkUI_SetDragEventStrictReportWithContext | Public (@since 12) | contextHandle: ArkUI_ContextHandle, enabled: bool | ArkUI_ErrorCode | 0 (SUCCESS) | 设置拖拽事件严格上报 | AC-04.4.2 |
| OH_ArkUI_CancelDataLoading | Public (@since 15) | uiContext: ArkUI_ContextHandle, key: int32_t | ArkUI_ErrorCode | 0 (SUCCESS) | 取消数据加载（uiContext 未使用 + 不路由 instanceId） | AC-04.4.3 |
| OH_ArkUI_EnableDropDisallowedBadge | Public (@since 20) | uiContext: ArkUI_ContextHandle, enabled: bool | ArkUI_ErrorCode | 0 (SUCCESS) | 设置禁止拖放徽章（不路由 instanceId） | AC-04.4.4 |

#### 动画 API（Module Interface）

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| OH_ArkUI_QueryModuleInterfaceByName(ARKUI_NATIVE_ANIMATE) | Public (@since 12) | moduleName: ARKUI_NATIVE_ANIMATE | ArkUI_NativeAnimateAPI_1* | 0 (SUCCESS) | 获取动画模块 API vtable | AC-04.5.1 |
| animateTo | Public (@since 12) | contextHandle: ArkUI_ContextHandle, option: ArkUI_AnimatableContextOption*, callback: void(*)(), completeCallback: void(*)() | ArkUI_ErrorCode | 0 (SUCCESS) | 触发显式动画 (vtable) | AC-04.5.2 |
| keyframeAnimateTo | Public (@since 12) | contextHandle: ArkUI_ContextHandle, option: ArkUI_KeyframeAnimateOption* | ArkUI_ErrorCode | 0 (SUCCESS) | 触发关键帧动画 (vtable) | AC-04.5.3 |
| createAnimator | Public (@since 12) | contextHandle: ArkUI_ContextHandle, option: ArkUI_AnimatorOption* | ArkUI_AnimatorHandle | 0 (SUCCESS) | 创建 Animator (vtable) | AC-04.5.4 |

#### 其他 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| OH_ArkUI_SetForceDarkConfig | Public (@since 20) | contextHandle: ArkUI_ContextHandle (可 nullptr), config: ArkUI_ForceDarkConfig* | ArkUI_ErrorCode | 0 (SUCCESS) | 设置强制暗色配置 | AC-04.6.1, AC-04.6.2 |
| OH_ArkUI_EnableEventPassthrough | Public (@since 26) | uiContext: ArkUI_ContextHandle, enabled: bool, type: ArkUI_EventPassthroughType | int32_t | 0 (SUCCESS) | 启用/禁用事件穿透 | AC-04.6.3 |
| OH_ArkUI_NativeModule_GetPageRootNodeHandleByContext | System (@since 24) | uiContext: ArkUI_ContextHandle | ArkUI_NodeHandle | 无错误码 | 通过上下文获取页面根节点 | AC-04.6.4 |

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

**ArkUI_ContextHandle typedef**

| 属性 | 值 |
|------|-----|
| 定义 | `typedef struct ArkUI_Context* ArkUI_ContextHandle` |
| 所在文件 | native_type.h:194 |
| 开放范围 | Public (@since 12) |
| 重复定义 | drag_and_drop.h:146（完全相同，ODR 风险） |
| 关联 AC | AC-04.1.5, AC-04.1.8 |

**类型约束**

| 约束 | 说明 |
|------|------|
| 不透明指针 | 调用者不应直接访问 ArkUI_Context 结构体内部字段 |
| 堆分配所有权 | 创建 API 返回堆分配指针，调用者需管理内存（当前无释放机制） |
| 命名不一致 | C-API 使用 ArkUI_ContextHandle 而非 UIContextHandle，与 ArkTS 层概念不对齐 |

---

**ArkUI_Context struct**

| 属性 | 值 |
|------|-----|
| 定义 | `struct ArkUI_Context { int32_t id; }` |
| 所在文件 | node_module_inner.h:21-23 |
| 开放范围 | Internal |
| sizeof | 8 字节（含 padding） |
| 关联 AC | AC-04.1.6 |

---

**ArkUIContext (Arkoala) struct**

| 属性 | 值 |
|------|-----|
| 定义 | `struct ArkUIContext { ArkUI_Int32 id; }` |
| 所在文件 | arkoala_api.h:2250-2252 |
| 开放范围 | Internal (Arkoala IDL) |
| 布局巧合 | instanceId_ 在首 4 字节偏移处，与 ArkUI_Context.id 偏移一致 |
| 关联 AC | AC-04.1.7 |

---

**OH_ArkUI_GetContextByNode**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ContextHandle OH_ArkUI_GetContextByNode(ArkUI_NodeHandle node)` |
| 返回值 | `ArkUI_ContextHandle` — 堆分配的 ArkUI_Context 指针（仅含 instanceId） |
| 开放范围 | Public (@since 12) |
| 错误码 | 无错误码 |
| 关联 AC | AC-04.1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| node | ArkUI_NodeHandle | 是 | 无 | 须为有效节点句柄；nullptr 时行为未定义 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效节点 | 返回堆分配的 ArkUI_Context，.id = instanceId | AC-04.1.1 |
| 2 | 多次调用同一节点 | 每次均 new ArkUI_Context，产生新对象 | AC-04.1.2 |
| 3 | 传入 nullptr | 无 null 检查，行为取决于底层实现 | AC-04.1.10 |
| 4 | 获取后尝试释放 | 无 Destroy API，内存泄漏 | AC-04.1.9 |

---

**OH_ArkUI_GetContextFromNapiValue**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ContextHandle OH_ArkUI_GetContextFromNapiValue(napi_env env, napi_value value)` |
| 返回值 | `ArkUI_ContextHandle` — 堆分配的 ArkUI_Context 指针 |
| 开放范围 | System (@since 12) |
| 错误码 | 无错误码 |
| 关联 AC | AC-04.1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| env | napi_env | 是 | 无 | NAPI 环境 |
| value | napi_value | 是 | 无 | NAPI 值，须包含 instanceId 信息 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 env+value | 返回堆分配的 ArkUI_Context，.id = instanceId | AC-04.1.3 |
| 2 | 获取后尝试释放 | 无 Destroy API，内存泄漏 | AC-04.1.9 |

---

**OH_ArkUI_NativeModule_GetContextFromAniValue**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ContextHandle OH_ArkUI_NativeModule_GetContextFromAniValue(ani_env* env, ani_object value)` |
| 返回值 | `ArkUI_ContextHandle` — 堆分配的 ArkUI_Context 指针 |
| 开放范围 | System (@since 22) |
| 错误码 | 无错误码 |
| 关联 AC | AC-04.1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| env | ani_env* | 是 | 无 | ANI 环境 |
| value | ani_object | 是 | 无 | ANI 对象引用，须包含 instanceId 信息 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 ani_env+ani_object | 返回堆分配的 ArkUI_Context，.id = instanceId | AC-04.1.4 |
| 2 | 获取后尝试释放 | 无 Destroy API，内存泄漏 | AC-04.1.9 |

---

**OH_ArkUI_RunTaskInScope**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_RunTaskInScope(ArkUI_ContextHandle uiContext, void* userData, void (*callback)(void*))` |
| 返回值 | `ArkUI_ErrorCode` — 0 表示成功 |
| 开放范围 | Public (@since 20) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr（无 null 检查） |
| userData | void* | 否 | nullptr | 回调参数 |
| callback | void (*)(void*) | 是 | 无 | 回调函数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 uiContext | ContainerScope::CurrentId(uiContext->id) 设置作用域后执行 callback | AC-04.2.1 |
| 2 | 传入 nullptr uiContext | 解引用 nullptr->id，段错误 | AC-04.2.7 |

---

**OH_ArkUI_PostUITask**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_PostUITask(ArkUI_ContextHandle context, void* taskData, void (*task)(void*))` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 22) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| context | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr |
| taskData | void* | 否 | nullptr | 任务数据 |
| task | void (*)(void*) | 是 | 无 | 同步回调函数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 context | 向 context->id 对应的 UIContext 同步投递 UI 任务 | AC-04.2.2 |

---

**OH_ArkUI_PostUITaskAndWait**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_PostUITaskAndWait(ArkUI_ContextHandle context, void* taskData, void (*task)(void*))` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 22) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| context | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr |
| taskData | void* | 否 | nullptr | 任务数据 |
| task | void (*)(void*) | 是 | 无 | 回调函数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 context | 投递 UI 任务并等待执行完成 | AC-04.2.3 |

---

**OH_ArkUI_PostAsyncUITask**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_PostAsyncUITask(ArkUI_ContextHandle context, ...)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 22) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| context | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 context | 向 context->id 对应的 UIContext 异步投递 UI 任务 | AC-04.2.4 |

---

**OH_ArkUI_PostFrameCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_PostFrameCallback(ArkUI_ContextHandle uiContext, void* userData, ArkUI_FrameCallback* callback)` |
| 返回值 | `int32_t` — 0 表示成功 |
| 开放范围 | Public (@since 16) |
| 错误码 | 0 (SUCCESS) |
| 关联 AC | AC-04.2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr |
| userData | void* | 否 | nullptr | 回调参数 |
| callback | ArkUI_FrameCallback* | 是 | 无 | 帧回调结构体 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 uiContext+callback | 注册帧回调，每帧渲染后执行 callback | AC-04.2.5 |

---

**OH_ArkUI_PostIdleCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_PostIdleCallback(ArkUI_ContextHandle uiContext, void* userData, ArkUI_IdleCallback* callback)` |
| 返回值 | `int32_t` — 0 表示成功 |
| 开放范围 | Public (@since 20) |
| 错误码 | 0 (SUCCESS) |
| 关联 AC | AC-04.2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr |
| userData | void* | 否 | nullptr | 回调参数 |
| callback | ArkUI_IdleCallback* | 是 | 无 | 空闲回调结构体 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 uiContext+callback | 注册空闲回调，UI 线程空闲时执行 callback | AC-04.2.6 |

---

**OH_ArkUI_FocusClear**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_FocusClear(ArkUI_ContextHandle uiContext)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 15) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr（无 null 检查） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 uiContext | 通过 uiContext->id 获取 PipelineContext，清除焦点 | AC-04.3.1 |
| 2 | 传入 nullptr | 解引用 nullptr->id，段错误 | AC-04.3.5 |

---

**OH_ArkUI_FocusActivate**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_FocusActivate(ArkUI_ContextHandle uiContext, bool isActive, bool isAutoInactive)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 15) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr |
| isActive | bool | 是 | 无 | 焦点激活状态 |
| isAutoInactive | bool | 是 | 无 | 焦点自动失活模式 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 uiContext+isActive+isAutoInactive | 设置焦点激活状态与自动失活模式 | AC-04.3.2 |

---

**OH_ArkUI_FocusSetAutoTransfer**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_FocusSetAutoTransfer(ArkUI_ContextHandle uiContext, bool autoTransfer)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 15) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr |
| autoTransfer | bool | 是 | 无 | 焦点自动转移开关 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 uiContext+autoTransfer | 设置焦点自动转移 | AC-04.3.3 |

---

**OH_ArkUI_FocusSetKeyProcessingMode**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_FocusSetKeyProcessingMode(ArkUI_ContextHandle uiContext, ArkUI_KeyProcessingMode mode)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 15) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr |
| mode | ArkUI_KeyProcessingMode | 是 | 无 | 按键处理模式枚举 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 uiContext+mode | 设置按键处理模式 | AC-04.3.4 |

---

**OH_ArkUI_CreateDragActionWithContext**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_DragAction* OH_ArkUI_CreateDragActionWithContext(ArkUI_ContextHandle uiContext, ...)` |
| 返回值 | `ArkUI_DragAction*` — 拖拽动作对象 |
| 开放范围 | Public (@since 12) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | TYPE CONFUSION: reinterpret_cast 到 ArkUIContext* |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入 uiContext | reinterpret_cast ArkUI_Context* → ArkUIContext*，创建拖拽动作 | AC-04.4.1 |
| 2 | TYPE CONFUSION cast | ArkUI_Context* (8字节) → ArkUIContext* (丰富C++类)，C++ UB | AC-04.4.5 |

---

**OH_ArkUI_SetDragEventStrictReportWithContext**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_SetDragEventStrictReportWithContext(ArkUI_ContextHandle uiContext, bool enabled)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 12) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr |
| enabled | bool | 是 | 无 | 严格上报模式开关 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 uiContext+enabled | 通过 uiContext->id 设置拖拽事件严格上报模式 | AC-04.4.2 |

---

**OH_ArkUI_CancelDataLoading**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_CancelDataLoading(ArkUI_ContextHandle uiContext, int32_t key)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 15) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | VESTIGIAL: 实现中未使用；参数名拼写为 "uiContent"；不路由通过 instanceId |
| key | int32_t | 是 | 无 | 数据加载 ID |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入任意 uiContext+有效 key | uiContext 参数被忽略，仅根据 key 取消数据加载 | AC-04.4.3 |

---

**OH_ArkUI_EnableDropDisallowedBadge**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_EnableDropDisallowedBadge(ArkUI_ContextHandle uiContext, bool enabled)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 20) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 不路由通过 instanceId（不一致路由） |
| enabled | bool | 是 | 无 | 禁止拖放徽章开关 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 uiContext+enabled | 设置禁止拖放徽章（不通过 instanceId 路由） | AC-04.4.4 |

---

**OH_ArkUI_QueryModuleInterfaceByName(ARKUI_NATIVE_ANIMATE)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void* OH_ArkUI_QueryModuleInterfaceByName(const char* moduleName)` |
| 返回值 | `ArkUI_NativeAnimateAPI_1*` — 动画模块 API vtable |
| 开放范围 | Public (@since 12) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.5.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| moduleName | const char* | 是 | ARKUI_NATIVE_ANIMATE | 模块名称常量 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入 ARKUI_NATIVE_ANIMATE | 返回包含 animateTo/keyframeAnimateTo/createAnimator 的 vtable 结构体 | AC-04.5.1 |

---

**animateTo (vtable struct member)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode animateTo(ArkUI_ContextHandle contextHandle, ArkUI_AnimatableContextOption* option, void (*contextCallback)(void*), void (*completeCallback)(void*))` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 12) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.5.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| contextHandle | ArkUI_ContextHandle | 是 | 无 | AnimatableContextOption vtable 中的 contextHandle |
| option | ArkUI_AnimatableContextOption* | 是 | 无 | 动画选项 |
| contextCallback | void (*)(void*) | 是 | 无 | 动画上下文回调 |
| completeCallback | void (*)(void*) | 是 | 无 | 动画完成回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 contextHandle + option + callbacks | 通过 vtable 触发显式动画 | AC-04.5.2 |

---

**keyframeAnimateTo (vtable struct member)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode keyframeAnimateTo(ArkUI_ContextHandle contextHandle, ArkUI_KeyframeAnimateOption* option)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 12) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| contextHandle | ArkUI_ContextHandle | 是 | 无 | vtable 中的 contextHandle |
| option | ArkUI_KeyframeAnimateOption* | 是 | 无 | 关键帧动画选项 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效参数 | 通过 vtable 触发关键帧动画 | AC-04.5.3 |

---

**createAnimator (vtable struct member)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_AnimatorHandle createAnimator(ArkUI_ContextHandle contextHandle, ArkUI_AnimatorOption* option)` |
| 返回值 | `ArkUI_AnimatorHandle` — Animator 对象句柄 |
| 开放范围 | Public (@since 12) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.5.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| contextHandle | ArkUI_ContextHandle | 是 | 无 | vtable 中的 contextHandle |
| option | ArkUI_AnimatorOption* | 是 | 无 | Animator 选项 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 contextHandle + option | 通过 vtable 创建 Animator 对象 | AC-04.5.4 |

---

**OH_ArkUI_SetForceDarkConfig**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_SetForceDarkConfig(ArkUI_ContextHandle contextHandle, ArkUI_ForceDarkConfig* config)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public (@since 20) |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR (0) |
| 关联 AC | AC-04.6.1, AC-04.6.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| contextHandle | ArkUI_ContextHandle | 否 | nullptr | nullptr = 应用级全局设置；非 nullptr = UIContext 级设置 |
| config | ArkUI_ForceDarkConfig* | 是 | 无 | 强制暗色配置结构体 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | contextHandle == nullptr | 应用级全局强制暗色配置 | AC-04.6.1 |
| 2 | contextHandle 有效 | UIContext 级强制暗色配置 | AC-04.6.2 |

---

**OH_ArkUI_EnableEventPassthrough**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_EnableEventPassthrough(ArkUI_ContextHandle uiContext, bool enabled, ArkUI_EventPassthroughType type)` |
| 返回值 | `int32_t` — 0 表示成功 |
| 开放范围 | Public (@since 26) |
| 错误码 | 0 (SUCCESS) |
| 关联 AC | AC-04.6.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr |
| enabled | bool | 是 | 无 | 事件穿透开关 |
| type | ArkUI_EventPassthroughType | 是 | 无 | 事件穿透类型 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 uiContext+enabled+type | 启用/禁用指定类型的事件穿透 | AC-04.6.3 |

---

**OH_ArkUI_NativeModule_GetPageRootNodeHandleByContext**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_NodeHandle OH_ArkUI_NativeModule_GetPageRootNodeHandleByContext(ArkUI_ContextHandle uiContext)` |
| 返回值 | `ArkUI_NodeHandle` — 页面根节点句柄 |
| 开放范围 | System (@since 24) |
| 错误码 | 无错误码 |
| 关联 AC | AC-04.6.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| uiContext | ArkUI_ContextHandle | 是 | 无 | 不可为 nullptr |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 uiContext | 通过 uiContext->id 获取 PipelineContext 返回页面根节点 | AC-04.6.4 |

## 兼容性声明

- **已有 API 行为变更:** 否，本规格为存量 API 补录，无行为变更
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12 (GetContextByNode / GetContextFromNapiValue / SetDragEventStrictReportWithContext / CreateDragActionWithContext / animateTo / keyframeAnimateTo / createAnimator); API 15~26 (其他 API)
- **API 版本号策略:** 覆盖 API 12~26 版本范围

**兼容性风险标注**：

1. **MEMORY LEAK (P1)**：3 个创建 API 均通过 `new ArkUI_Context({.id = instanceId})` 堆分配但无释放 API。每次调用产生 8 字节不可回收堆对象，长期运行 NDK 应用存在系统性内存泄漏。源码：`node_adapter_impl.cpp:256`、`native_node_napi.cpp:174`、`native_node_ani.cpp:229`

2. **TYPE CONFUSION (P1)**：`OH_ArkUI_CreateDragActionWithContext` 将 `ArkUI_Context*`（8字节 `{int32_t id}` 结构体）通过 `reinterpret_cast` 转换为 `ArkUIContext*`（丰富的 C++ 类），按 C++ 标准属于 UB。当前因 `ArkUIContext::instanceId_` 恰好在首 4 字节偏移处而"运行正确"，但任何 `ArkUIContext` 类布局变更将导致崩溃。源码：`drag_and_drop_impl.cpp:184`

3. **NAMING INCONSISTENCY (P2)**：C-API 命名使用 `ArkUI_ContextHandle` 而非与 ArkTS 层 `UIContextHandle` 语义对齐的名称；创建函数 `OH_ArkUI_GetContextByNode` 而非 `GetUIContextHandle`。命名不一致增加开发者跨层理解成本。源码：`native_type.h:194`、`native_node.h:13717`

4. **INCONSISTENT ROUTING (P2)**：大多数使用 API 通过 `contextHandle->id` 提取 `instanceId` 后使用 `ContainerScope(id)` 路由到正确 PipelineContext；但 `OH_ArkUI_CancelDataLoading` 和 `OH_ArkUI_EnableDropDisallowedBadge` 不实际路由通过 `instanceId`，破坏统一桥接模式一致性。源码：`drag_and_drop_impl.cpp:886`、`drag_and_drop_impl.cpp:983`

5. **DUAL TYPEDEF (P2)**：`ArkUI_ContextHandle` 在 `native_type.h:194` 和 `drag_and_drop.h:146` 中均有 `typedef struct ArkUI_Context* ArkUI_ContextHandle` 定义，完全相同但位于不同头文件，违反 ODR 原则。源码：`native_type.h:194`、`drag_and_drop.h:146`

6. **VESTIGIAL PARAM (P3)**：`OH_ArkUI_CancelDataLoading` 的 `uiContext` 参数在实现中未使用（残余参数），实现中参数名拼写为 `"uiContent"`（typo）。源码：`drag_and_drop_impl.cpp:886`

7. **NO NULL SAFETY**：大多数使用 API 对 `ArkUI_ContextHandle` 参数不做 null 检查，传入 nullptr 时直接解引用 `.id` 字段导致段错误。唯一例外为 `OH_ArkUI_SetForceDarkConfig`，其 nullptr 参数有明确语义（应用级全局设置）。

8. **版本跨度大 (API 12~26)**：22 个 API 跨越 API 12~26 版本范围，部分 API 在不同版本中行为可能不同（如 TYPE CONFUSION 风险在后续版本可能出现）。

## 架构约束

```mermaid
flowchart TD
    A[NDK Application] -->|OH_ArkUI_GetContextByNode| B[new ArkUI_Context<br/>{.id = instanceId}<br/>node_adapter_impl.cpp:256]
    A -->|OH_ArkUI_GetContextFromNapiValue| C[new ArkUI_Context<br/>{.id = instanceId}<br/>native_node_napi.cpp:174]
    A -->|OH_ArkUI_NativeModule_GetContextFromAniValue| D[new ArkUI_Context<br/>{.id = instanceId}<br/>native_node_ani.cpp:229]
    B --> E[ArkUI_ContextHandle<br/>typedef struct ArkUI_Context*<br/>native_type.h:194<br/>ODR duplicate: drag_and_drop.h:146]
    C --> E
    D --> E
    E -->|大多数使用 API| F[reinterpret_cast&lt;ArkUI_Context*&gt;<br/>extract .id<br/>ContainerScope(id)<br/>→ PipelineContext]
    E -->|CreateDragActionWithContext| G[reinterpret_cast&lt;ArkUIContext*&gt;<br/>TYPE CONFUSION UB<br/>drag_and_drop_impl.cpp:184]
    E -->|CancelDataLoading<br/>EnableDropDisallowedBadge| H[不路由 instanceId<br/>不一致路由<br/>drag_and_drop_impl.cpp:886,983]
    E -->|SetForceDarkConfig<br/>nullptr| I[应用级全局设置<br/>node_utils.cpp:808]
    F --> J[RunTaskInScope<br/>PostUITask<br/>PostUITaskAndWait<br/>PostAsyncUITask<br/>PostFrameCallback<br/>PostIdleCallback<br/>FocusClear/FocusActivate<br/>FocusSetAutoTransfer<br/>FocusSetKeyProcessingMode<br/>SetForceDarkConfig非nullptr<br/>EnableEventPassthrough<br/>GetPageRootNodeHandleByContext]
    G --> K[ArkUIContext 布局巧合<br/>instanceId_ 在首4字节偏移<br/>arkoala_api.h:2250]
    A -->|QueryModuleInterface<br/>ARKUI_NATIVE_ANIMATE| L[ArkUI_NativeAnimateAPI_1<br/>vtable: animateTo<br/>keyframeAnimateTo<br/>createAnimator<br/>native_animate.h:98-102]
    style G fill:#f66,stroke:#333,color:#fff
    style H fill:#f96,stroke:#333,color:#fff
    style K fill:#f66,stroke:#333,color:#fff
```

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| ArkUI_Context 仅含 id 字段 | 8 字节 `{int32_t id}` 结构体，无 vtable/方法/析构函数 | AC-04.1.6, AC-04.7.3 |
| 无 Destroy API | 3 个创建 API 堆分配后无法释放 | AC-04.1.9 |
| TYPE CONFUSION reinterpret_cast | OH_ArkUI_CreateDragActionWithContext 将 ArkUI_Context* cast 到 ArkUIContext* | AC-04.4.1, AC-04.4.5 |
| ArkUIContext 内存布局巧合 | instanceId_ 在首 4 字节偏移处 | AC-04.4.5, AC-04.7.4 |
| 统一桥接模式 | 大多数使用 API: contextHandle → extract id → ContainerScope(id) → PipelineContext | AC-04.7.2 |
| 不一致路由 | CancelDataLoading / EnableDropDisallowedBadge 不路由 instanceId | AC-04.7.7 |
| 双 typedef ODR 风险 | native_type.h 和 drag_and_drop.h 完全相同定义 | AC-04.1.8, AC-04.7.5 |
| 命名不一致 | ArkUI_ContextHandle 与 ArkTS UIContextHandle 语义不对齐 | AC-04.1.11, AC-04.7.8 |
| 大多数 API 无 null 检查 | contextHandle nullptr 时段错误 | AC-04.1.10, AC-04.2.7, AC-04.3.5 |
| SetForceDarkConfig nullptr 有语义 | nullptr = 应用级全局设置 | AC-04.6.1 |
| ArkUIFullNodeAPI 分发 | 通过 getBasicAPI()/getAnimation()/getNodeModifiers()/getDragAdapterAPI()/getMultiThreadManagerAPI() 获取子模块 API | AC-04.7.1 |
| 动画 API 通过 Module Interface | animateTo/keyframeAnimateTo/createAnimator 通过 OH_ArkUI_QueryModuleInterfaceByName 获取 vtable | AC-04.5.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | GetContextByNode 单次调用耗时 < 5μs | 微基准测试 | 堆分配 + instanceId 查询 |
| 内存 | 每次 GetContextByNode 产生 8 字节不可回收堆对象 | 内存分析 | sizeof(ArkUI_Context) = 8 (含 padding) |
| 安全 | contextHandle nullptr 安全性 | 源码审查 | 大多数 API 无 null 检查 |
| 类型安全 | TYPE CONFUSION UB 风险 | 架构分析 | reinterpret_cast 依赖内存布局巧合 |
| 路由一致性 | 大多数 API 统一桥接模式一致性 | 源码审查 | CancelDataLoading/EnableDropDisallowedBadge 不路由 instanceId |
| 命名一致性 | C-API 与 ArkTS 层命名对齐 | 命名分析 | ArkUI_ContextHandle vs UIContextHandle |
| 可测试性 | C-API 可通过 capi_* 单元测试独立测试 | 单元测试 | linux_unittest_capi |
| 定界定位 | TYPE CONFUSION 可通过 reinterpret_cast 路径定位 | 源码审查 | drag_and_drop_impl.cpp:184 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | ContextHandle 创建/使用行为一致 | C-API 单元测试 | — |
| 平板 | 无差异 | 同上 | C-API 单元测试 | — |
| 折叠屏 | 多实例场景增多 | RunTaskInScope / PostAsyncUITask / PostUITask 等在多实例下作用域切换更频繁 | C-API 单元测试 | — |
| 2in1 设备 | 无差异 | 同上 | C-API 单元测试 | — |
| 嵌入式 | 无差异 | 同上 | C-API 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | ContextHandle 不直接涉及无障碍 | — |
| 大字体 | 否 | ContextHandle 不受字体缩放影响 | — |
| 深色模式 | 是 | OH_ArkUI_SetForceDarkConfig 通过 contextHandle 控制强制暗色 | AC-04.6.1, AC-04.6.2 |
| 多窗口/分屏 | 是 | RunTaskInScope / PostUITask / PostAsyncUITask 等在多窗口场景下需指定正确 UIContext | AC-04.2.1~04.2.4 |
| 版本升级 | 是 | API 覆盖 API 12~26 版本范围 | AC-04全 |
| 生态兼容 | 是 | TYPE CONFUSION UB 风险影响使用 ArkUIContext 的 NDK 应用；命名不一致影响跨层代码移植 | AC-04.4.5, AC-04.1.11 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）
- [x] 所有规格声明均有源码 file:line 引用支撑
- [x] Delta 表使用 `| 类型 | 内容 | 说明 |` 格式且类型列仅使用 ADDED/MODIFIED/REMOVED
- [x] 架构约束包含 Mermaid 流程图
- [x] 规则类型标签仅使用 行为/边界/异常/恢复
- [x] 特性名称为 "C-API UIContextHandle接口"
- [x] 特性编号为 "Func-04-12-01-Feat-04"
- [x] context-references 使用 YAML 格式

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_GetContextByNode 在 node_adapter_impl.cpp:256-268 中 new ArkUI_Context 堆分配及无 Destroy API 的内存泄漏风险"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_GetContextFromNapiValue 在 native_node_napi.cpp:174 和 OH_ArkUI_NativeModule_GetContextFromAniValue 在 native_node_ani.cpp:229 中同样的堆分配模式"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_CreateDragActionWithContext 在 drag_and_drop_impl.cpp:184 中 reinterpret_cast ArkUI_Context* 到 ArkUIContext* 的 TYPE CONFUSION"
  - repo: "openharmony/ace_engine"
    query: "ArkUI_ContextHandle 重复 typedef 在 native_type.h:194 和 drag_and_drop.h:146 中的 ODR 风险"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_CancelDataLoading 在 drag_and_drop_impl.cpp:886 中 uiContext 参数未使用且参数名拼写为 uiContent，以及不路由通过 instanceId"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_EnableDropDisallowedBadge 在 drag_and_drop_impl.cpp:983 中不路由通过 instanceId 的不一致路由行为"
  - repo: "openharmony/ace_engine"
    query: "ArkUI_ContextHandle 命名与 ArkTS 层 UIContextHandle 概念不对齐的命名不一致风险"
  - repo: "openharmony/ace_engine"
    query: "ArkUIFullNodeAPI dispatch 机制: getBasicAPI/getAnimation/getNodeModifiers/getDragAdapterAPI/getMultiThreadManagerAPI"
  - repo: "openharmony/ace_engine"
    query: "Arkoala ArkUIContext 结构体在 arkoala_api.h:2250-2252 中与 ArkUI_Context 的偏移巧合依赖"
```