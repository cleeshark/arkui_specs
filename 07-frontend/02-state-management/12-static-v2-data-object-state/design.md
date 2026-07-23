# 架构设计

> 07-02-12 静态V2数据对象内状态管理功能域的架构设计文档（占位）。本域覆盖 ArkUI 静态前端（ArkTS 1.2 / arkoala / Panda VM）对 V2 数据对象级可观察能力的适配：静态侧 `@ObservedV2`/`@Trace`（通过 **UIPlugin 转换** 为对应的 `IMutableStateMeta`/`MutableStateMeta` 完成观测代理安装，不直接复用动态前端的 `trackInternal`/`ObserveV2`）、`@Computed`（惰性求值 + 缓存只读计算属性）、`@Monitor`/`@SyncMonitor`（路径感知变化监听，由 07-02-11 提供）。详细规格待后续补充。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-07-02-12 |
| 关联需求 | 待补充 |
| 关联 Epic | 无 |
| 目标 Feature | 待补充 |
| 复杂度 | 中等 |
| 目标版本 | 待定 |
| Owner | ArkUI SIG |
| 状态 | 待补充 |
| FuncID | 07-02-12 |
| 源码根 | 待定（静态前端 arkoala V2 数据对象观测适配，`frameworks/bridge/arkts_frontend/` 相关） |
| SDK 声明 | `interface/sdk-js/api/arkui/stateManagement/decorator.static.d.ets`（@ObservedV2/@Trace/@Computed/@Monitor，经 `@ohos.arkui.stateManagement.static.d.ets` 重导出） |
| 测试入口 | 待定 |
| 前置依赖 | 07-02-05（V2 数据对象 — 动态前端 @ObservedV2/@Trace 语义基线）、07-02-11（静态 V2 组件内 — ObserveV2 单例与 trackInternal 提供方） |
| 下游影响 | 07-02-14（互操作 — 静态可观察对象跨前端共享） |
| 关键错误码 | 待定 |

## 规划范围

本域计划覆盖以下内容（待 Feat 拆分）：

- 静态前端 `@ObservedV2` 类装饰器与 `@Trace` 属性观测：经 **UIPlugin 转换** 为 `MutableStateMeta`/`MutableKeyedStateMeta`（addRef/fireChange 通道）
- 静态前端 V2 数据对象的 getter/setter 响应式安装与惰性集合代理
- 与动态前端 V2 数据对象观测的语义对齐（与 07-02-05 协同）

> 注：`@Computed`/`@Monitor`/`@SyncMonitor` 归 07-02-11 静态 V2 组件内（装饰变量运行时类）；动态/静态前端互操作的具体机制归 07-02-14 状态管理互操作；本域聚焦静态前端 V2 数据对象级的观测行为。
