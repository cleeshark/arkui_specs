# 架构设计

> 07-02-11 静态V2组件内状态管理功能域的架构设计文档（占位）。本域覆盖 ArkUI 静态前端（ArkTS 1.2 / arkoala / Panda VM，`libarkts_frontend.z.so`）对 V2 组件级状态管理能力的适配：静态侧 `@Local`/`@Param`/`@Once`/`@Provider`/`@Consumer`/`@Monitor`/`@SyncMonitor`/`@Computed` 等 V2 装饰器声明、arkoala 编译产物对接装饰变量（`DecoratedV2VariableBase`）、依赖与通知提取到全局 `ObserveSingleton` 单例、变更调度经 `StateUpdateLoop` 合并到 VSync 批次。详细规格待后续补充。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-07-02-11 |
| 关联需求 | 待补充 |
| 关联 Epic | 无 |
| 目标 Feature | 待补充 |
| 复杂度 | 高 |
| 目标版本 | 待定 |
| Owner | ArkUI SIG |
| 状态 | 待补充 |
| FuncID | 07-02-11 |
| 源码根 | 待定（静态前端 arkoala V2 组件状态管理适配，`frameworks/bridge/arkts_frontend/` 相关） |
| SDK 声明 | `interface/sdk-js/api/arkui/stateManagement/decorator.static.d.ets`（V2 组件级装饰器，经 `@ohos.arkui.stateManagement.static.d.ets` 重导出） |
| 测试入口 | 待定 |
| 前置依赖 | 07-02-04（V2 组件内 — 动态前端 V2 装饰器与 ObserveV2 语义基线）、07-02-08（静态 V1 组件内 — V1/V2 共存基线） |
| 下游影响 | 07-02-12（静态 V2 数据对象 — @ObservedV2/@Trace 静态侧）、07-02-13（静态 V2 应用存储 — AppStorageV2 静态侧）、07-02-14（互操作 — Builder/Binding 静态侧参数）、07-03-07（静态自定义组件状态相关 — 复用机制） |
| 关键错误码 | 待定 |

## 规划范围

本域计划覆盖以下内容（待 Feat 拆分）：

- 静态前端 V2 组件级装饰器声明与编译产物（`@Local`/`@Param`/`@Once`/`@Provider`/`@Consumer`/`@Monitor`/`@SyncMonitor`/`@Computed`）
- V2 装饰变量基类 `DecoratedV2VariableBase` 与延迟更新队列 `StateUpdateLoop`
- `autoProxyObject` 自动为普通对象安装观测代理
- 静态前端 `ObserveSingleton` 全局单例依赖收集与异步调度
- 与动态前端 V2 的语义对齐（与 07-02-04 协同）

> 注：`@Env`/`@CustomEnv` 环境变量注入不属于状态管理范畴（归环境能力域）；`@ReusableV2`/`GlobalReusePool` 复用机制归 07-03-07 静态自定义组件状态相关；动态/静态前端互操作归 07-02-14；静态 V2 数据对象观测（`@ObservedV2`/`@Trace`）归 07-02-12；本域聚焦静态前端 V2 组件内部的状态管理行为。
