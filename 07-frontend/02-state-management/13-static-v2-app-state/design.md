# 架构设计

> 07-02-13 静态V2应用内状态管理功能域的架构设计文档（占位）。本域覆盖 ArkUI 静态前端（ArkTS 1.2 / arkoala / Panda VM）对 V2 应用级状态承载与持久化的适配：静态侧 `AppStorageV2`（内存全局存储，仅 class 类型，typeKey 机制，`@Trace` 属性自动刷新）、`PersistenceV2`（磁盘持久化，可配置 `IStorage` 后端，`ObserveV2` 依赖图自动追踪 `@Trace` 变化，`DataCoder` 保持原型链序列化）、`PersistenceV2.globalConnect` 的 EL1-EL5 加密级别支持。详细规格待后续补充。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-07-02-13 |
| 关联需求 | 待补充 |
| 关联 Epic | 无 |
| 目标 Feature | 待补充 |
| 复杂度 | 中等 |
| 目标版本 | 待定 |
| Owner | ArkUI SIG |
| 状态 | 待补充 |
| FuncID | 07-02-13 |
| 源码根 | 待定（静态前端 arkoala V2 应用存储适配，`frameworks/bridge/arkts_frontend/` 相关） |
| SDK 声明 | `interface/sdk-js/api/arkui/stateManagement/storage/appStorageV2.static.d.ets` + `persistenceV2.static.d.ets`（AppStorageV2/PersistenceV2，经 `@ohos.arkui.stateManagement.static.d.ets` 重导出） |
| 测试入口 | 待定 |
| 前置依赖 | 07-02-06（V2 应用存储 — 动态前端 AppStorageV2/PersistenceV2 语义基线）、07-02-11（静态 V2 组件内 — ObserveV2 单例提供方）、07-02-12（静态 V2 数据对象 — @Trace 触发自动刷新） |
| 下游影响 | 07-02-14（互操作 — 跨前端存储 `InteropStorageV2` 双向可见） |
| 关键错误码 | 待定 |

## 规划范围

本域计划覆盖以下内容（待 Feat 拆分）：

- 静态前端 `AppStorageV2` 创建、读写、typeKey 机制与 `@Trace` 自动刷新
- 静态前端 `PersistenceV2` 磁盘持久化、`IStorage` 后端与 `DataCoder` 序列化
- 静态前端 `PersistenceV2.globalConnect` EL1-EL5 加密级别支持
- 与动态前端 V2 应用存储的语义对齐（与 07-02-06 协同）

> 注：动态/静态前端互操作的具体机制归 07-02-14 状态管理互操作（`InteropStorageV2` 跨前端存储双向可见）；本域聚焦静态前端 V2 应用存储行为。
