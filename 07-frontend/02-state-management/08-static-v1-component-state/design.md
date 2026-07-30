# 架构设计

> 07-02-08 静态V1组件内状态管理功能域的架构设计文档（占位）。本域覆盖 ArkUI 静态前端（ArkTS 1.2 / arkoala / Panda VM，`libarkts_frontend.z.so`）对 V1 组件级状态管理能力的适配，包括静态侧 `@State`/`@Prop`/`@PropRef`/`@Link`/`@Watch`/`@Provide`/`@Consume`/`@ObjectLink` 等装饰器声明（`@ohos.arkui.stateManagement.static.d.ets` 重导出于 `arkui/stateManagement/decorator.static.d.ets`）、arkoala 编译产物对 PU 渲染路径的对接、静态前端的渲染期依赖收集与变更通知行为。详细规格待后续补充。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-07-02-08 |
| 关联需求 | 待补充 |
| 关联 Epic | 无 |
| 目标 Feature | 待补充 |
| 复杂度 | 高 |
| 目标版本 | 待定 |
| Owner | ArkUI SIG |
| 状态 | 待补充 |
| FuncID | 07-02-08 |
| 源码根 | 待定（静态前端 arkoala V1 组件状态管理适配，`frameworks/bridge/arkts_frontend/` 相关） |
| SDK 声明 | `interface/sdk-js/api/arkui/stateManagement/decorator.static.d.ets`（V1 组件级装饰器，经 `@ohos.arkui.stateManagement.static.d.ets` 重导出） |
| 测试入口 | 待定 |
| 前置依赖 | 07-02-01（V1 组件内 — 动态前端 V1 装饰器语义基线） |
| 下游影响 | 07-02-09（静态 V1 数据对象 — @Observed/@ObjectLink 静态侧）、07-02-10（静态 V1 应用存储 — @StorageLink 静态侧）、07-02-14（互操作 — 静态/动态前端状态互操作）、07-03-07（静态自定义组件状态相关） |
| 关键错误码 | 待定 |

## 规划范围

本域计划覆盖以下内容（待 Feat 拆分）：

- 静态前端 V1 组件级装饰器声明与编译产物（`@State`/`@Prop`/`@PropRef`/`@Link`/`@Watch`/`@Provide`/`@Consume`/`@ObjectLink`）
- V1 装饰变量基类 `DecoratedV1VariableBase` 与 `IStateMgmtFactory` 工厂分发
- arkoala 状态管理代码生成与 PU 渲染路径对接
- 静态前端渲染期依赖收集、变更通知与局部重渲染行为
- 与动态前端 V1 的语义对齐（与 07-02-01 协同）

> 注：动态/静态前端互操作的具体机制归 07-02-14 状态管理互操作；存储联动装饰器（`@StorageLink`/`@StorageProp`/`@StoragePropRef`/`@LocalStorageLink`/`@LocalStoragePropRef`）归 07-02-10 静态 V1 应用存储；V1 数据对象观测（`@Observed`/`@Track`）归 07-02-09；本域聚焦静态前端 V1 组件内部的状态管理行为。
