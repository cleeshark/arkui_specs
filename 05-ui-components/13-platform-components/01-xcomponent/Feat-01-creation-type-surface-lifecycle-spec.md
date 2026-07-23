# 特性规格

> Func-05-13-01-Feat-01 XComponent 创建、类型与表面生命周期：固化 XComponent 构造参数解析、XComponentType 四种类型（SURFACE/COMPONENT/TEXTURE/NODE）的行为差异、onLoad/onDestroy 回调时序、以及 ArkTS XComponentController 与经典 NDK OH_NativeXComponent 两套表面生命周期通道的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | XComponent 创建、类型与表面生命周期（核心） |
| 特性编号 | Func-05-13-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 8+（NDK）/ API 12+（ArkUI 节点 C-API） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 构造参数规格 | 补录 id/type/libraryName/soPath/controller/screenId 构造参数解析、默认值与校验规格 |
| ADDED | 类型枚举规格 | 补录 SURFACE/COMPONENT/TEXTURE/NODE 四类型的 IsAtomicNode/Paint/Focus/属性可用性差异规格 |
| ADDED | onLoad/onDestroy 规格 | 补录 onLoad/onDestroy 触发时序与回调参数规格 |
| ADDED | 表面生命周期双通道规格 | 补录 ArkTS XComponentController 与经典 NDK OH_NativeXComponent_Callback 两套表面回调规格 |
| ADDED | 节点 C-API 属性规格 | 补录 NODE_XCOMPONENT_ID/TYPE 的 set/get/reset 与错误码规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/13-platform-components/01-xcomponent/design.md` | Baselined |
| KB 上下文 | `docs/kb/components/platform/x_component.md` | active（ace_engine 仓） |
| SDK 声明 | `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/x_component.d.ts` | 需 SDK 仓核验 |

---

## 用户故事

### US-1: 创建 XComponent 并传入构造参数

**作为** 应用开发者,
**我想要** 通过 XComponent 构造参数指定 id、type、libraryName、soPath、controller、screenId,
**以便** 控制表面承载方式、native 模块加载与目标屏幕。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 以 `XComponent({ id: 'xc', type: XComponentType.SURFACE, libraryName: 'libname' })` 创建 THEN 节点以 `XComponentPattern` 创建，`id_` 存储 'xc'，`type_`=SURFACE，`libraryname_`='libname'，注册到 XComponentClient | 正常 |
| AC-1.2 | WHEN `id` 为空字符串或未提供 THEN `GetId()` 返回合成值 `nodeId_<nodeId>`（内部永不为空），仍作为 XComponentClient map key 使用 | 边界 |
| AC-1.3 | WHEN `type` 为未识别字符串（含空串）或未提供 THEN 类型解析为 SURFACE（默认值） | 边界 |
| AC-1.4 | WHEN 提供 `libraryName` 且 type=SURFACE/TEXTURE THEN `InitNativeXComponent` 创建 OH_NativeXComponent，走 NDK 回调通道 | 正常 |
| AC-1.5 | WHEN 未提供 `libraryName`（且提供 controller）THEN 不创建 NativeXComponent，改走 ArkTS XComponentController `onSurface*` 回调通道 | 正常 |
| AC-1.6 | WHEN 提供 `soPath` 且 type≠COMPONENT/NODE THEN `soPath` 作为 `LoadModuleByName` 的加载路径覆盖（libraryName 仍是模块标识） | 正常 |
| AC-1.7 | WHEN type=COMPONENT 或 NODE 时调用 SetSoPath THEN 提前返回（no-op），soPath 不生效 | 边界 |
| AC-1.8 | WHEN 提供 `screenId` 且 type=SURFACE THEN 经 `ConvertScreenIdToRsScreenId` 转换后存于 pattern；type≠SURFACE 时忽略 | 正常 |
| AC-1.9 | WHEN controller 为 null THEN 创建正常进行（graceful 处理，无崩溃） | 异常 |

### US-2: 依据 XComponentType 获得对应类型行为

**作为** 应用开发者,
**我想要** SURFACE/COMPONENT/TEXTURE/NODE 四种类型表现出各自约定的渲染、焦点与可用能力差异,
**以便** 按场景选择正确的承载类型。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN type=SURFACE 或 TEXTURE 或 NODE THEN `IsAtomicNode()` 返回 true（叶子节点） | 正常 |
| AC-2.2 | WHEN type=COMPONENT THEN `IsAtomicNode()` 返回 false（可包含子节点） | 正常 |
| AC-2.3 | WHEN type=TEXTURE THEN `CreateNodePaintMethod()` 返回 XComponentPaintMethod（将 surface 绘制进 RS canvas）；其它类型返回 nullptr | 正常 |
| AC-2.4 | WHEN type=NODE THEN `GetFocusPattern()` 返回 `{SCOPE, true}`（可聚焦子树）；其它类型返回 NODE 级非默认聚焦 | 正常 |
| AC-2.5 | WHEN type=COMPONENT 或 NODE THEN SetOnLoad/SetSoPath/EnableAnalyzer/SetControllerOn* 等表面/控制器/事件 setter 提前返回（no-op） | 边界 |
| AC-2.6 | WHEN type=NODE THEN opacity/灰度等视觉效果生效；其它类型这些视觉 setter 返回 Undefined（被忽略） | 正常 |

### US-3: 通过 onLoad/onDestroy 监听加载与销毁

**作为** 应用开发者,
**我想要** 通过 onLoad 和 onDestroy 回调感知 XComponent 的加载完成与销毁,
**以便** 在 surface 就绪/销毁时执行初始化与清理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 节点挂载且首帧布局得到正尺寸（drawSize_>0）THEN `XComponentSizeInit` 触发，按序：InitNativeWindow → FireSurfaceInitEvent → FireLoadEvent(onLoad) → FireControllerCreatedEvent | 正常 |
| AC-3.2 | WHEN onLoad 回调被触发且 XComponentClient 已映射 native JS 值 THEN 回调收到该 OH_NativeXComponent JS 代理对象作为参数；未映射时回调以零参数调用 | 正常 |
| AC-3.3 | WHEN 节点从 FrameNode 分离（OnDetachFromFrameNode，type=SURFACE/TEXTURE 且已 init）THEN 按序：OnSurfaceDestroyed → FireDestroyEvent(onDestroy) → FireDetachEvent → FireControllerDestroyedEvent | 正常 |
| AC-3.4 | WHEN 节点尚未正尺寸（未 init）即被分离 THEN 不触发 onDestroy（hasXComponentInit_ 为 false，提前返回） | 边界 |

### US-4: 通过 ArkTS XComponentController 监听表面生命周期

**作为** 应用开发者,
**我想要** 通过 XComponentController 的 onSurfaceCreated/onSurfaceChanged/onSurfaceDestroyed 监听表面状态（libraryName 未提供时）,
**以便** 在纯 ArkTS 场景管理表面。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 未提供 libraryName 且表面创建 THEN `FireControllerCreatedEvent(surfaceId, xcomponentId)` 触发，ArkTS 回调收到 1 个参数：surfaceId（字符串，取自 renderSurface 唯一 ID） | 正常 |
| AC-4.2 | WHEN 表面尺寸在首帧后变化 THEN `FireControllerChangedEvent(surfaceId, rect)` 触发，ArkTS 回调收到 2 个参数：surfaceId（字符串）与 rect 对象 `{offsetX, offsetY, surfaceWidth, surfaceHeight}` | 正常 |
| AC-4.3 | WHEN 首帧初始化（preSurfaceSize 为零）THEN 首次尺寸变化被抑制（needFireNativeEvent=false），不触发 onSurfaceChanged | 边界 |
| AC-4.4 | WHEN 表面销毁 THEN `FireControllerDestroyedEvent(surfaceId, xcomponentId)` 触发，ArkTS 回调收到 1 个参数：surfaceId（字符串） | 正常 |

### US-5: 通过经典 NDK OH_NativeXComponent 监听表面生命周期

**作为** NDK 开发者,
**我想要** 通过 `OH_NativeXComponent_RegisterCallback` 注册的 `OH_NativeXComponent_Callback`（OnSurfaceCreated/OnSurfaceChanged/OnSurfaceDestroyed）监听表面（提供 libraryName 时）,
**以便** 在 native 层接管 EGL/纹理表面。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `OH_NativeXComponent_RegisterCallback(component, &callbacks)` 且 impl 非空 THEN 返回 `OH_NATIVEXCOMPONENT_RESULT_SUCCESS(0)` 并存储回调指针（重复注册直接覆盖，不报错） | 正常 |
| AC-5.2 | WHEN impl 为 null THEN 返回 `OH_NATIVEXCOMPONENT_RESULT_BAD_PARAMETER(-2)` | 异常 |
| AC-5.3 | WHEN TypedNode/CAPI/static 节点表面创建（isNativeXComponent_=true）THEN 模式在回调前将 width/height/surface 设置到 impl，随后调用 `OnSurfaceCreated(component, window)`，window 为 native 窗口指针 | 正常 |
| AC-5.4 | WHEN 表面尺寸变化 THEN 模式先 SetXComponentWidth/Height 到 impl 再调用 `OnSurfaceChanged(component, window)` | 正常 |
| AC-5.5 | WHEN 表面销毁 THEN 调用 `OnSurfaceDestroyed(component, surface)`，随后 `SetSurface(nullptr)` | 正常 |

### US-6: 通过节点 C-API 设置 ID/TYPE 属性

**作为** NDK 开发者,
**我想要** 通过 `setAttribute(NODE_XCOMPONENT_ID/TYPE, ...)` 设置 XComponent 节点 ID 与类型,
**以便** 在节点命令式 API 下配置组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `setAttribute(NODE_XCOMPONENT_ID, {.string="xc"})` THEN 写入 pattern `id_`；读取返回该字符串 | 正常 |
| AC-6.2 | WHEN `setAttribute(NODE_XCOMPONENT_ID, nullptr 或无 .string)` THEN 返回 `ERROR_CODE_PARAM_INVALID(401)` | 异常 |
| AC-6.3 | WHEN `setAttribute(NODE_XCOMPONENT_TYPE, {i32=0 或 2})` THEN 写入 XComponentType 并触发 `PROPERTY_UPDATE_MEASURE` | 正常 |
| AC-6.4 | WHEN `setAttribute(NODE_XCOMPONENT_TYPE, {i32=1 或 3 或其它})` THEN 返回 `ERROR_CODE_PARAM_INVALID(401)`（NDK 不暴露 COMPONENT/NODE） | 异常 |
| AC-6.5 | WHEN `resetAttribute(NODE_XCOMPONENT_TYPE)` THEN 类型重置为 `ARKUI_XCOMPONENT_TYPE_SURFACE(0)` | 正常 |
| AC-6.6 | WHEN `resetAttribute(NODE_XCOMPONENT_ID)` THEN 静默 no-op（ID 无 resetter） | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.9 | R-1, R-2, R-3, R-4, R-5, R-6, R-7 | 已有实现 | 代码评审 + 单测 | `arkts_native_xcomponent_bridge.cpp`, `xcomponent_model_ng.cpp` |
| AC-2.1~2.6 | R-8, R-9, R-10, R-11, R-12 | 已有实现 | 代码评审 | `xcomponent_pattern.h`, `xcomponent_model.h` |
| AC-3.1~3.4 | R-13, R-14, R-15 | 已有实现 | 代码评审 | `xcomponent_pattern.cpp:1118-1142, 807-846` |
| AC-4.1~4.4 | R-16, R-17, R-18 | 已有实现 | 代码评审 | `xcomponent_pattern.cpp`, `xcomponent_event_hub.h` |
| AC-5.1~5.5 | R-19, R-20, R-21 | 已有实现 | C-API 单测 + 代码评审 | `native_interface_xcomponent_impl.cpp`, `xcomponent_pattern.cpp:2118-2232` |
| AC-6.1~6.6 | R-22, R-23, R-24, R-25 | 已有实现 | C-API 单测 | `style_modifier.cpp:9738-9784`, `native_node_test.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `XComponent({id, type, libraryName, controller})` 创建 | 创建 XComponentPattern，id_/type_/libraryname_ 存储，注册 XComponentClient map | id 默认合成 nodeId_<n> | AC-1.1 |
| R-2 | 边界 | id 空或未提供 | GetId() 返回 `nodeId_<nodeId>`，仍作 map key | 内部永不为空 | AC-1.2 |
| R-3 | 边界 | type 为未识别字符串/空/未提供 | 解析为 SURFACE | TEXTURE 无字符串别名 | AC-1.3 |
| R-4 | 行为 | libraryName 有值且 type=SURFACE/TEXTURE | InitNativeXComponent 创建 OH_NativeXComponent，走 NDK 通道 | — | AC-1.4 |
| R-5 | 行为 | libraryName 无值且 controller 有值 | 走 ArkTS Controller onSurface* 通道 | 二选一开关 | AC-1.5 |
| R-6 | 行为 | 提供 soPath 且 type≠COMPONENT/NODE | soPath 作为 LoadModuleByName 加载路径覆盖 | libraryName 仍是模块标识 | AC-1.6 |
| R-7 | 边界 | type=COMPONENT/NODE 调 SetSoPath | 提前返回 no-op | — | AC-1.7 |
| R-8 | 行为 | type=SURFACE/TEXTURE/NODE | IsAtomicNode 返回 true | COMPONENT 例外 | AC-2.1, AC-2.2 |
| R-9 | 行为 | type=TEXTURE | CreateNodePaintMethod 返回 XComponentPaintMethod | 仅 TEXTURE 返回非 null | AC-2.3 |
| R-10 | 行为 | type=NODE | GetFocusPattern 返回 {SCOPE, true} | NODE 原子但 SCOPE 焦点 | AC-2.4 |
| R-11 | 边界 | type=COMPONENT/NODE 的表面/控制器/事件 setter | 提前返回 no-op | — | AC-2.5 |
| R-12 | 行为 | type=NODE 的 opacity/视觉 setter | 生效；其它类型返回 Undefined | 仅 NODE | AC-2.6 |
| R-13 | 行为 | 首帧正尺寸（drawSize_>0） | XComponentSizeInit 顺序：InitNativeWindow→FireSurfaceInitEvent→FireLoadEvent→FireControllerCreatedEvent | 仅触发一次（hasXComponentInit_） | AC-3.1 |
| R-14 | 行为 | onLoad 触发且 Client 已映射 JS 值 | 回调收 OH_NativeXComponent JS 代理；未映射则零参 | — | AC-3.2 |
| R-15 | 行为 | OnDetachFromFrameNode（已 init，SURFACE/TEXTURE） | OnSurfaceDestroyed→FireDestroyEvent(onDestroy)→FireDetachEvent→FireControllerDestroyedEvent | 未 init 不触发 | AC-3.3, AC-3.4 |
| R-16 | 行为 | 无 libraryName，表面创建 | FireControllerCreatedEvent(surfaceId, xcomponentId)，回调收 1 参 surfaceId | surfaceId=renderSurface 唯一 ID | AC-4.1 |
| R-17 | 行为 | 表面尺寸首帧后变化 | FireControllerChangedEvent(surfaceId, rect)，回调收 2 参（surfaceId, {offsetX,offsetY,surfaceWidth,surfaceHeight}） | 首帧抑制 | AC-4.2, AC-4.3 |
| R-18 | 行为 | 表面销毁 | FireControllerDestroyedEvent(surfaceId, xcomponentId)，回调收 1 参 surfaceId | — | AC-4.4 |
| R-19 | 行为 | OH_NativeXComponent_RegisterCallback，impl 非空 | 返回 SUCCESS(0)，存储回调（重复覆盖） | — | AC-5.1 |
| R-20 | 异常 | impl 为 null | 返回 BAD_PARAMETER(-2) | — | AC-5.2 |
| R-21 | 行为 | TypedNode/CAPI/static 表面创建/变化/销毁 | 回调前设 width/height/surface 到 impl，再调用 OnSurfaceCreated/Changed/Destroyed(component, window) | window=native 窗口指针 | AC-5.3~5.5 |
| R-22 | 行为 | setAttribute(NODE_XCOMPONENT_ID, .string) | 写入 id_，读取返回该串 | — | AC-6.1 |
| R-23 | 异常 | setAttribute(NODE_XCOMPONENT_ID, null/无.string) | 返回 ERROR_CODE_PARAM_INVALID(401) | — | AC-6.2 |
| R-24 | 行为 | setAttribute(NODE_XCOMPONENT_TYPE, i32=0/2) | 写入并触发 PROPERTY_UPDATE_MEASURE | 仅 0/2 合法 | AC-6.3 |
| R-25 | 异常/边界 | setAttribute(NODE_XCOMPONENT_TYPE, i32=1/3) / reset(ID) | TYPE 非 0/2 返回 401；reset TYPE→SURFACE(0)；reset ID 静默 no-op | NDK 不暴露 COMPONENT/NODE | AC-6.4~6.6 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.9, R-1~R-7 | 代码评审 + 单测 | 构造参数解析与默认值 |
| VM-2 | AC-2.1~2.6, R-8~R-12 | 代码评审 | 四类型行为差异（原子/Paint/Focus/可用 setter） |
| VM-3 | AC-3.1~3.4, R-13~R-15 | 代码评审 | onLoad/onDestroy 时序与回调参数 |
| VM-4 | AC-4.1~4.4, R-16~R-18 | 代码评审 | ArkTS Controller 表面回调参数形态与首帧抑制 |
| VM-5 | AC-5.1~5.5, R-19~R-21 | C-API 单测 + 代码评审 | NDK RegisterCallback 返回值与 OnSurface* 派发 |
| VM-6 | AC-6.1~6.6, R-22~R-25 | C-API 单测 | NODE_XCOMPONENT_ID/TYPE 的 set/get/reset 与错误码 |

---

## API 变更分析

### 新增 API

> 本特性为已有能力补录，API 均已存在；以下为规格固化涉及的关键 API 清单。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `XComponent(options)` | Public | id/type/libraryName/soPath/controller/screenId | XComponentAttribute | N/A | 创建 XComponent | AC-1.1 |
| `onLoad(callback)` | Public | `(ctx?) => void` | XComponentAttribute | N/A | 加载完成回调 | AC-3.1 |
| `onDestroy(callback)` | Public | `() => void` | XComponentAttribute | N/A | 销毁回调 | AC-3.3 |
| `OH_NativeXComponent_RegisterCallback` | Public（NDK, @since 8） | component, OH_NativeXComponent_Callback* | OH_NativeXComponent_Result | 0/-2 | 注册表面/触摸回调 | AC-5.1 |
| `setAttribute(NODE_XCOMPONENT_ID)` | Public（NDK, @since 15） | .string | ArkUI_ErrorCode | 401/106102 | 设置节点 ID | AC-6.1 |
| `setAttribute(NODE_XCOMPONENT_TYPE)` | Public（NDK, @since 15） | .i32(0/2) | ArkUI_ErrorCode | 401/106102 | 设置节点类型 | AC-6.3 |

### 变更/废弃 API

无变更/废弃 API。

---

## 接口规格

### 接口定义

**OH_NativeXComponent_RegisterCallback(component, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_NativeXComponent_Result OH_NativeXComponent_RegisterCallback(OH_NativeXComponent* component, OH_NativeXComponent_Callback* callback)` |
| 返回值 | `OH_NativeXComponent_Result` — 0=SUCCESS, -2=BAD_PARAMETER |
| 开放范围 | Public（NDK） |
| 错误码 | SUCCESS(0), BAD_PARAMETER(-2) |
| 关联 AC | AC-5.1, AC-5.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| component | OH_NativeXComponent* | 是 | — | 非空；底层 impl 非空才返回 SUCCESS |
| callback | OH_NativeXComponent_Callback* | 是 | — | 存储 OnSurfaceCreated/Changed/Destroyed/DispatchTouchEvent 指针；重复注册直接覆盖 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | impl 非空注册 | 返回 SUCCESS(0)，存储回调 | AC-5.1 |
| 2 | impl 为 null | 返回 BAD_PARAMETER(-2) | AC-5.2 |

### 接口定义

**setAttribute(NODE_XCOMPONENT_TYPE, item)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode setAttribute(ArkUI_NodeHandle node, ArkUI_NodeAttribute attribute, const ArkUI_AttributeItem* item)`（attribute=NODE_XCOMPONENT_TYPE） |
| 返回值 | `ArkUI_ErrorCode` — 0=SUCCESS |
| 开放范围 | Public（节点 C-API） |
| 错误码 | ERROR_CODE_PARAM_INVALID(401), ERROR_CODE_NATIVE_IMPL_TYPE_NOT_SUPPORTED(106102) |
| 关联 AC | AC-6.3, AC-6.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| item.value[0].i32 | ArkUI_XComponentType | 是 | ARKUI_XCOMPONENT_TYPE_SURFACE | 仅 0(SURFACE)/2(TEXTURE) 合法；1/3 返回 401 |

---

## 兼容性声明

- **已有 API 行为变更:** 否（纯补录）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** NDK OH_NativeXComponent_Callback @since 8；ArkUI 节点 C-API NODE_XCOMPONENT_* @since 15；ARKUI_NODE_XCOMPONENT_TEXTURE @since 16；NODE_XCOMPONENT_SURFACE_RECT/ENABLE_ANALYZER @since 18
- **API 版本号策略:** 经典 NDK since 8；节点 C-API 类型枚举 since 12、属性 since 15+
- **源码 vs SDK 偏差（风险）:** `ResetOnLoad`/`ResetOnDestroy`（ArkTS bridge）为 no-op，不清除 event hub 回调；若 SDK 期望 reset 清除回调，则为偏差（见风险项）

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| libraryName 是 NDK 通道与 ArkTS Controller 通道的开关 | 有 libraryName→OH_NativeXComponent（NDK 回调）；无→ArkTS Controller onSurface* | AC-1.4, AC-1.5, AC-5.3 |
| NDK 类型枚举只暴露 SURFACE(0)/TEXTURE(2)，数值有间隔 | COMPONENT/NODE 无法经 NDK 设置（设 1/3 返回 401）；数值间隔对齐内部枚举 | AC-6.4 |
| TEXTURE 无字符串别名 | 仅数字或 ARKUI_NODE_XCOMPONENT_TEXTURE 可达；未知字符串→SURFACE | AC-1.3 |
| NODE 原子但 SCOPE 焦点 | IsAtomicNode=true 与 GetFocusPattern={SCOPE,true} 并存（已知设计张力） | AC-2.1, AC-2.4 |
| COMPONENT 是唯一非原子类型 | 多数表面/控制器/事件 setter 对 COMPONENT/NODE 为 no-op | AC-2.2, AC-2.5 |
| NDK 表面回调派发分裂 | NG pattern 直接派发经典 OH_NativeXComponent_Callback 仅限 TypedNode/CAPI/static；声明式+libraryname 走 legacy render 层 | AC-5.3 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 表面创建延迟由 native 窗口与图形栈决定，不设量化指标 | 集成测试 | `xcomponent_pattern.cpp` |
| 安全 | NDK 句柄经 XComponentClient map 隔离 | 代码评审 | `arkts_native_xcomponent_bridge.cpp` |
| 可测试性 | onLoad/onDestroy、Controller 回调可通过 Mock 验证 | 单测 | `test/unittest/core/pattern/xcomponent/` |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | 集成测试 | — |
| 平板 | 无差异 | — | 集成测试 | — |
| 折叠屏 | screenId 机制可用于定向屏幕；表面尺寸响应折叠变化 | SetScreenId 仅 SURFACE | 集成测试 | `xcomponent_model_ng.cpp:407` |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | XComponent 提供独立 AccessibilityProvider（详 Feat-08）；NODE 类型可承载子树无障碍 | AC-2.4 |
| 大字体 | 否 | XComponent 不直接渲染文本 | — |
| 深色模式 | 否 | 表面内容由外部 native 渲染 | — |
| 多窗口/分屏 | 是 | 表面需响应窗口/分屏尺寸变化（onSurfaceChanged） | AC-4.2 |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | NDK 与节点 C-API @since 版本差异需标注 | 兼容性声明 |
| 生态兼容 | 是 | 经典 NDK（since 8）与节点 C-API（since 12+）双通道并存 | AC-5.x, AC-6.x |

---

## 行为场景

```gherkin
Feature: XComponent 创建、类型与表面生命周期
  作为 应用开发者/NDK 开发者
  我想要 创建 XComponent、按类型获得对应行为、并通过双通道监听表面生命周期
  以便 在 ArkTS 与 native 层正确承载 EGL/纹理表面

  # ─── 创建与类型 ─────────────────────────

  Scenario: 创建带 libraryName 的 SURFACE 组件
    Given 一个宿主页面
    When 调用 XComponent({ id: 'xc', type: XComponentType.SURFACE, libraryName: 'lib' })
    Then 创建 XComponentPattern，InitNativeXComponent 创建 OH_NativeXComponent
    And 后续走 NDK OnSurface* 回调通道

  Scenario: 未识别 type 字符串回退 SURFACE
    Given 一个宿主页面
    When 调用 XComponent({ id: 'xc', type: 'unknown' })
    Then 类型解析为 SURFACE

  Scenario: type 为空
    Given 一个宿主页面
    When 调用 XComponent({ id: '' })
    Then 类型默认 SURFACE
    And GetId() 返回合成值 nodeId_<n>

  Scenario: NODE 类型获得 SCOPE 焦点
    Given 一个 type=NODE 的 XComponent
    Then IsAtomicNode 返回 true
    And GetFocusPattern 返回 {SCOPE, true}

  # ─── onLoad/onDestroy ──────────────────

  Scenario: 首帧正尺寸触发 onLoad
    Given 一个已挂载的 SURFACE XComponent
    When 首帧布局得到正尺寸
    Then XComponentSizeInit 顺序执行 InitNativeWindow→FireSurfaceInitEvent→onLoad→ControllerCreated
    And onLoad 仅触发一次

  Scenario: 分离触发 onDestroy
    Given 一个已 init 的 SURFACE XComponent
    When 节点从 FrameNode 分离
    Then OnSurfaceDestroyed→onDestroy→FireDetachEvent→ControllerDestroyed

  Scenario: 未 init 即分离不触发 onDestroy
    Given 一个尚未正尺寸的 XComponent
    When 节点被分离
    Then 不触发 onDestroy

  # ─── ArkTS Controller 通道 ──────────────

  Scenario: Controller onSurfaceCreated 收到 surfaceId
    Given 一个无 libraryName、带 controller 的 SURFACE XComponent
    When 表面创建
    Then onSurfaceCreated 回调收到 1 个参数 surfaceId（字符串）

  Scenario: 首帧尺寸变化被抑制
    Given 一个刚创建的 SURFACE XComponent
    When 首帧尺寸从零变为正
    Then 不触发 onSurfaceChanged（needFireNativeEvent=false）

  Scenario: 非首帧尺寸变化触发 onSurfaceChanged
    Given 一个已有正尺寸的 SURFACE XComponent
    When 表面尺寸再次变化
    Then onSurfaceChanged 收到 surfaceId 与 rect{offsetX,offsetY,surfaceWidth,surfaceHeight}

  # ─── 经典 NDK 通道 ──────────────────────

  Scenario: 注册 NDK 回调成功
    Given 一个 OH_NativeXComponent（impl 非空）
    When 调用 OH_NativeXComponent_RegisterCallback(component, &callbacks)
    Then 返回 OH_NATIVEXCOMPONENT_RESULT_SUCCESS(0)

  Scenario: impl 为 null 注册失败
    Given 一个底层 impl 为 null 的 OH_NativeXComponent
    When 调用 OH_NativeXComponent_RegisterCallback
    Then 返回 OH_NATIVEXCOMPONENT_RESULT_BAD_PARAMETER(-2)

  Scenario: TypedNode 表面创建派发 NDK 回调
    Given 一个 isNativeXComponent_=true 的 TypedNode
    When 表面创建
    Then 模式先设 width/height/surface 到 impl
    And 调用 OnSurfaceCreated(component, window)

  # ─── 节点 C-API ─────────────────────────

  Scenario: NDK 设置合法类型
    Given 一个 XComponent 节点
    When 调用 setAttribute(NODE_XCOMPONENT_TYPE, {i32: 2})
    Then 写入 TEXTURE 并触发 PROPERTY_UPDATE_MEASURE

  Scenario: NDK 设置非法类型报错
    Given 一个 XComponent 节点
    When 调用 setAttribute(NODE_XCOMPONENT_TYPE, {i32: 1})
    Then 返回 ERROR_CODE_PARAM_INVALID(401)

  Scenario: reset ID 为 no-op
    Given 一个已设 ID 的 XComponent 节点
    When 调用 resetAttribute(NODE_XCOMPONENT_ID)
    Then 静默无操作（ID 无 resetter）

  Scenario: reset TYPE 回到 SURFACE
    Given 一个 type=TEXTURE 的 XComponent 节点
    When 调用 resetAttribute(NODE_XCOMPONENT_TYPE)
    Then 类型重置为 ARKUI_XCOMPONENT_TYPE_SURFACE(0)
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：创建/类型/onLoad/双通道表面生命周期/节点 ID-TYPE；不做什么：控制器表面尺寸/画布、输入事件、HDR、analyzer、SurfaceHolder V2、帧率、无障碍 provider —— 分别属 Feat-02~08）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "XComponentBridge::Create 如何按 id/controller/type 选择 V2 param-less 路径 vs V1 parametrized 路径"
  - repo: "openharmony/ace_engine"
    query: "InitNativeXComponent 如何以 libraryName 是否有值为开关创建 OH_NativeXComponent"
  - repo: "openharmony/ace_engine"
    query: "XComponentSizeInit 的 InitNativeWindow→FireSurfaceInitEvent→FireLoadEvent→FireControllerCreatedEvent 时序"
  - repo: "openharmony/ace_engine"
    query: "isNativeXComponent_ 与 isTypedNode_ 如何决定 OnSurfaceCreated 派发 NDK 回调还是 Controller 事件"
  - repo: "openharmony/ace_engine"
    query: "NODE_XCOMPONENT_TYPE 为何只接受 0/2，COMPONENT/NODE 为何不经 NDK 暴露"
```

**关键文档：**
- SDK API：`interface/sdk-js/api/@internal/component/ets/x_component.d.ts`（需 SDK 仓核验）
- NDK：`interfaces/native/native_interface_xcomponent.h`、`interfaces/native/node_attributes/xcomponent.h`
- Pattern：`frameworks/core/components_ng/pattern/xcomponent/xcomponent_pattern.cpp/.h`
- Bridge：`frameworks/core/components_ng/pattern/xcomponent/bridge/arkts_native_xcomponent_bridge.cpp`
