# 架构设计

> 07-02-10 静态V1应用内状态管理功能域的架构设计文档（占位）。本域覆盖 ArkUI 静态前端（ArkTS 1.2 / arkoala / Panda VM）对 V1 应用级状态承载与持久化的适配：静态侧 `LocalStorage`（页面级多实例存储）、`AppStorage`（应用级全局单例）、`PersistentStorage`（磁盘持久化）、`Environment`（设备环境变量），以及存储联动装饰器 `@StorageLink`/`@StorageProp`/`@LocalStorageLink`/`@LocalStorageProp` 经 `__createSync` 工厂的静态前端对接。详细规格待后续补充。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-07-02-10 |
| 关联需求 | 待补充 |
| 关联 Epic | 无 |
| 目标 Feature | 待补充 |
| 复杂度 | 中等 |
| 目标版本 | 待定 |
| Owner | ArkUI SIG |
| 状态 | 待补充 |
| FuncID | 07-02-10 |
| 源码根 | 待定（静态前端 arkoala V1 应用存储适配，`frameworks/bridge/arkts_frontend/` 相关） |
| SDK 声明 | `interface/sdk-js/api/@ohos.arkui.stateManagement.static.d.ets`（AppStorage/LocalStorage/PersistentStorage/Environment + 存储联动装饰器，重导出于 `arkui/stateManagement/storage/*.static.d.ets`） |
| 测试入口 | 待定 |
| 前置依赖 | 07-02-03（V1 应用存储 — 动态前端 LocalStorage/AppStorage 语义基线）、07-02-08（静态 V1 组件内 — 存储联动装饰器接收方） |
| 下游影响 | 07-02-14（互操作 — 跨前端存储 `InteropStorage` 双向可见） |
| 关键错误码 | 待定 |

## 规划范围

本域计划覆盖以下内容（待 Feat 拆分）：

- 静态前端 `LocalStorage` / `AppStorage` 创建、读写与多实例行为
- 静态前端 `PersistentStorage` 磁盘持久化与 `Environment` 设备环境变量
- 静态前端存储联动装饰器（`@StorageLink`/`@StorageProp`/`@StoragePropRef`/`@LocalStorageLink`/`@LocalStoragePropRef`）的 `__createSync` 对接
- 与动态前端 V1 应用存储的语义对齐（与 07-02-03 协同）

> 注：动态/静态前端互操作的具体机制归 07-02-14 状态管理互操作（`InteropStorage` 跨前端存储双向可见）；本域聚焦静态前端 V1 应用存储行为。
