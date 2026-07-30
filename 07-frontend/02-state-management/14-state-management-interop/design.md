# 架构设计

> 07-02-14 状态管理互操作功能域的架构设计文档（占位）。本域覆盖 ArkUI 状态管理的跨范式/跨前端/跨实例基础设施：动态/静态前端互操作（`InteropStorage`/`ViewInterop`/`BuilderViewV2`）、elmtId 全链路同步（`ElementRegister`/`UINodeRegisterProxy`/`moveDeletedElmtIds`）、`WeakRefPool` 依赖图 GC、C++ 宿主集成（`CustomNode`/`isV2_`/`ViewFunctions`/`PUV2ViewBase` 共享）、横切基础设施（`ConfigureStateMgmt`/`stateMgmtConsole`/`stateMgmtDFX`/`Profiler`/`SubscribableAbstract`）。详细规格待后续补充。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-07-02-14 |
| 关联需求 | 待补充 |
| 关联 Epic | 无 |
| 目标 Feature | 待补充 |
| 复杂度 | 高 |
| 目标版本 | 待定 |
| Owner | ArkUI SIG |
| 状态 | 待补充 |
| FuncID | 07-02-14 |
| 源码根 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/interop/`（interop_configure.ts / interop_module.ts / interop.ts / interop_storage.ts / interop_view.ts / interop_builder.ts / v2_interop_storage.ts / v2_builder.ts） |
| SDK 声明 | 无独立 SDK 声明（互操作是引擎内部机制，不暴露公开 API） |
| 测试入口 | 待定 |
| 前置依赖 | 07-02-01（V1 组件内 — 动态前端状态管理基础）、07-02-04（V2 组件内 — 动态前端 V2 基础）、07-02-08~10（静态 V1 组件内/数据对象/应用存储 — 静态前端 V1 状态管理基础）、07-02-11~13（静态 V2 组件内/数据对象/应用存储 — 静态前端 V2 状态管理基础） |
| 下游影响 | 无（互操作是引擎内部终端层） |
| 关键错误码 | 无专属（互操作为引擎内部机制，错误经 stateMgmtConsole 输出） |

## 规划范围

本域计划覆盖以下内容（待 Feat 拆分）：

### 动态/静态前端互操作
- `InteropConfigureStateMgmt`（`needsInterop`/`openInterop`/`closeInterop`）控制反转
- `InteropExtractorModule`（约 13 回调槽）+ `StaticInteropHook`
- `InteropStorage`/`InteropStorageV2` 跨前端存储双向可见
- `ViewInterop` 跨世界 `@Consumer` 查找中转（`findProviderForInterop`）
- Builder 桥（`BuilderViewV2` + `createCompatibleNodeWithFunc1..10` 严格类型重载）
- `isStaticProxy` 检测与 `deepCopyStaticProxy` 拷贝
- `staticStateBindObservedObject` 兼容 / `@Track` 模式双路径
- `OpenStateMgmtInterop` 启用入口

> 注：UIUtils 对外 API 归 07-02-07；`WeakRefPool`（V2 依赖图 GC）+ `ConfigureStateMgmt`（特性开关）归 07-02-04 V2；`SubscribableAbstract` + `stateMgmtConsole`/`stateMgmtDFX`/`stateMgmtProfiler` + `UpdateFuncRecord` + elmtId 全链路同步（`ElementRegister`/`UINodeRegisterProxy`/`moveDeletedElmtIds`/`OnIdle`）+ C++ 宿主集成（`CustomNode`/`ViewFunctions`/`JSLocalStorage`/`JSPersistent`/`JSEnvironment`）归 07-02-01 V1（Feat-09）；本域仅聚焦动态/静态前端互操作。
