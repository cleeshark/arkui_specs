# 特性规格

> Func-05-13-01-Feat-04 SurfaceHolder/SurfaceCallback V2 表面模型：固化 OH_ArkUI_SurfaceHolder 创建/释放、SurfaceCallback 注册、Initialize/Finalize/SetAutoInitialize 显式生命周期、SurfaceConfig（@since 18/20/22）的行为规格，以及与 legacy NativeXComponent 路径的互斥关系。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SurfaceHolder/SurfaceCallback V2 表面模型 |
| 特性编号 | Func-05-13-01-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | @since 18（Holder/Callback/Initialize）/ 20（Show/Hide 回调）/ 22（SurfaceConfig） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | SurfaceHolder 生命周期规格 | Create/Dispose/SetUserData/GetUserData/GetNativeWindow |
| ADDED | SurfaceCallback 规格 | Create/Dispose、Set Created/Changed/Destroyed/Show/Hide、Add/Remove（去重） |
| ADDED | 显式生命周期规格 | SetAutoInitialize（默认 true）、Initialize/Finalize/IsInitialized（状态机 + XCOMPONENT_STATE_INVALID） |
| ADDED | SurfaceConfig 规格 | Create/Dispose/SetIsOpaque/SetSurfaceConfig（@since 22） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/13-platform-components/01-xcomponent/design.md` | Baselined |

---

## 用户故事

### US-1: 创建与使用 SurfaceHolder

**作为** NDK 开发者,
**我想要** 通过 OH_ArkUI_SurfaceHolder 获取并管理 XComponent 节点的表面,
**以便** 采用现代（since 18）表面模型。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `OH_ArkUI_SurfaceHolder_Create(node)` 且 node 为有效 XComponent 节点 THEN 返回 SurfaceHolder 指针 | 正常 |
| AC-1.2 | WHEN node 无效 / modifier 为 null / 创建失败 THEN 返回 nullptr 并设错误码（PARAM_INVALID 或 INTERNAL_ERROR） | 异常 |
| AC-1.3 | WHEN `OH_ArkUI_SurfaceHolder_Dispose(holder)` 且 holder 非空 THEN 调用 modifier dispose、从 config 集移除、delete holder；holder null 返回 PARAM_INVALID | 正常 |
| AC-1.4 | WHEN `OH_ArkUI_XComponent_GetNativeWindow(holder)` THEN 返回 holder 的 nativeWindow（未创建时 nullptr） | 正常 |
| AC-1.5 | WHEN SetUserData/GetUserData THEN 存取 userData（默认 nullptr）；holder null 返回 PARAM_INVALID | 正常 |

### US-2: 注册 SurfaceCallback

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `SurfaceCallback_Create` THEN 返回空回调对象（5 个函数指针）；失败返回 nullptr + INTERNAL_ERROR | 正常 |
| AC-2.2 | WHEN SetSurfaceCreatedEvent/ChangedEvent(w,h)/DestroyedEvent（@since 18）THEN 赋对应函数指针；callback null 返回 PARAM_INVALID | 正常 |
| AC-2.3 | WHEN SetSurfaceShowEvent/HideEvent（@since 20） THEN 赋 onSurfaceShow/onSurfaceHide | 正常 |
| AC-2.4 | WHEN `AddSurfaceCallback(holder, cb)` 且 cb 未在列表 THEN 加入返回 NO_ERROR；已存在返回 PARAM_INVALID（拒绝重复） | 正常 |
| AC-2.5 | WHEN `RemoveSurfaceCallback(holder, cb)` 且 cb 在列表 THEN 移除返回 NO_ERROR；不存在返回 PARAM_INVALID | 正常 |

### US-3: 显式表面生命周期（Initialize/Finalize）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `SetAutoInitialize(node, true)`（默认 true） THEN 挂载自动触发 OnSurfaceCreated、卸载触发 OnSurfaceDestroyed | 正常 |
| AC-3.2 | WHEN `SetAutoInitialize(node, false)` THEN 不自动触发，需显式 Initialize/Finalize | 正常 |
| AC-3.3 | WHEN `Initialize(node)` 且未初始化 THEN InitSurface、isInitialized=true、派发 OnSurfaceCreated（必要时 OnSurfaceChanged） | 正常 |
| AC-3.4 | WHEN `Initialize(node)` 且已初始化 THEN 返回 ARKUI_ERROR_CODE_XCOMPONENT_STATE_INVALID(103501) | 异常 |
| AC-3.5 | WHEN `Finalize(node)` 且已初始化 THEN isInitialized=false、派发 OnSurfaceDestroyed、DisposeSurface | 正常 |
| AC-3.6 | WHEN `Finalize(node)` 且未初始化 THEN 返回 XCOMPONENT_STATE_INVALID(103501) | 异常 |
| AC-3.7 | WHEN `IsInitialized(node, &flag)` THEN 返回当前 isInitialized_ | 正常 |

### US-4: SurfaceConfig（@since 22）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `XComponentSurfaceConfig_Create` THEN 返回 config（isOpaque 默认 false） | 正常 |
| AC-4.2 | WHEN `SetIsOpaque(config, v)` THEN 设 isOpaque 并对所有关联 holder 重应用 | 正常 |
| AC-4.3 | WHEN `SurfaceHolder_SetSurfaceConfig(holder, config)` THEN holder 关联 config，经 SurfaceConfigInterface 设不透明 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.x | R-1~R-3 | C-API 单测 + 代码评审 | `native_interface_xcomponent.cpp:521-679` |
| AC-2.x | R-4~R-6 | 代码评审 | `native_interface_xcomponent.cpp:601-669` |
| AC-3.x | R-7~R-10 | 代码评审 | `xcomponent_pattern_v2.cpp:429-499` |
| AC-4.x | R-11 | 代码评审 | `native_interface_xcomponent.cpp:917-966` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | SurfaceHolder_Create 有效节点 | 返回 holder；失败 nullptr+错误码 | @since 18 | AC-1.1, AC-1.2 |
| R-2 | 行为 | Dispose / GetNativeWindow / UserData | dispose 释放；GetNativeWindow 返回 nativeWindow_；UserData 默认 nullptr | holder null→PARAM_INVALID | AC-1.3~1.5 |
| R-3 | 边界 | 已走 legacy NativeXComponent 路径 | createSurfaceHolder 被拒（IsCreateSurfaceHolderForbidden） | hasGotNativeXComponent_ 或 usesSuperMethod_ | — |
| R-4 | 行为 | SurfaceCallback_Create + Set*Event | 5 函数指针（Created/Changed/Destroyed @since 18，Show/Hide @since 20） | null→PARAM_INVALID | AC-2.1~2.3 |
| R-5 | 行为 | AddSurfaceCallback 去重 | 未在列表→加入 NO_ERROR；已存在→PARAM_INVALID | — | AC-2.4 |
| R-6 | 行为 | RemoveSurfaceCallback | 在列表→移除 NO_ERROR；不存在→PARAM_INVALID | — | AC-2.5 |
| R-7 | 行为 | SetAutoInitialize 默认 true | 挂载/卸载自动触发 Created/Destroyed | — | AC-3.1, AC-3.2 |
| R-8 | 行为 | Initialize 未初始化 | InitSurface、isInitialized=true、派发 Created | — | AC-3.3 |
| R-9 | 异常 | Initialize 已初始化 / Finalize 未初始化 | 返回 XCOMPONENT_STATE_INVALID(103501) | — | AC-3.4, AC-3.6 |
| R-10 | 行为 | Finalize 已初始化 | isInitialized=false、派发 Destroyed、DisposeSurface | — | AC-3.5 |
| R-11 | 行为 | SurfaceConfig（@since 22） | Create(isOpaque 默认 false)、SetIsOpaque 重应用、SetSurfaceConfig 经 Interface | — | AC-4.x |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.x, R-1~R-3 | C-API 单测 | Holder 生命周期、与 legacy 互斥 |
| VM-2 | AC-2.x, R-4~R-6 | 代码评审 | Callback 去重与 5 事件 |
| VM-3 | AC-3.x, R-7~R-10 | 代码评审 | 状态机 103501 |
| VM-4 | AC-4.x, R-11 | 代码评审 | SurfaceConfig @since 22 |

---

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| OH_ArkUI_SurfaceHolder_Create | Public（NDK @since 18） | node | SurfaceHolder* | PARAM_INVALID/INTERNAL_ERROR | 创建 holder | AC-1.1 |
| OH_ArkUI_XComponent_Initialize | Public（NDK @since 18） | node | ArkUI_ErrorCode | 0/401/103501 | 显式初始化表面 | AC-3.3 |
| OH_ArkUI_XComponentSurfaceConfig_SetIsOpaque | Public（NDK @since 22） | config, bool | void | PARAM_INVALID | 设不透明 | AC-4.2 |

### 变更/废弃 API

无。

---

## 接口规格

### 接口定义

**OH_ArkUI_XComponent_Initialize(node)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode OH_ArkUI_XComponent_Initialize(ArkUI_NodeHandle node)` |
| 返回值 | ArkUI_ErrorCode — 0=NO_ERROR |
| 开放范围 | Public（NDK） |
| 错误码 | PARAM_INVALID(401), XCOMPONENT_STATE_INVALID(103501) |
| 关联 AC | AC-3.3, AC-3.4 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** Holder/Callback/Initialize @since 18；Show/Hide @since 20；SurfaceConfig @since 22
- **互斥约束:** 已走 legacy NativeXComponent（since 8/13）路径时，V2 holder 创建被拒

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| V2 与 legacy 互斥 | hasGotNativeXComponent_ 时禁止 SurfaceHolder | AC-1.2, R-3 |
| 状态机 103501 | Initialize/Finalize 重复调用返回 XCOMPONENT_STATE_INVALID | AC-3.4, AC-3.6 |
| Callback 去重 | 重复 Add 返回 PARAM_INVALID | AC-2.4 |
| usesSuperMethod_ 路由 | Initialize/Finalize/SetAutoInitialize/IsInitialized 仅 usesSuperMethod_=true 时受理 | AC-3.x |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 状态机/去重可经单测验证 | 单测 | `xcomponent_pattern_v2.cpp` |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | 集成测试 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 多窗口/分屏 | 是 | autoInitialize 与挂载/卸载绑定 | AC-3.1 |
| 其余 | 否 | — | — |

---

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC 使用 WHEN/THEN
- [x] 范围边界明确（不涉及输入事件/HDR/analyzer/无障碍）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "XComponentPatternV2 SurfaceHolder/Callback 与 Initialize/Finalize 状态机、usesSuperMethod_ 路由"
  - repo: "openharmony/ace_engine"
    query: "V2 holder 与 legacy NativeXComponent 路径互斥 IsCreateSurfaceHolderForbidden"
```

**关键文档：** `native_interface_xcomponent.h/.cpp`、`xcomponent_surface_holder.h`、`xcomponent_pattern_v2.cpp`
