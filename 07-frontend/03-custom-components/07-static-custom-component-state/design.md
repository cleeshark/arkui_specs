# 架构设计

> 07-03-07 静态自定义组件状态相关功能域的架构设计文档（占位）。本域覆盖 ArkUI 静态前端（ArkTS 1.2 / arkoala / Panda VM，`libarkts_frontend.z.so`）下 `@Component`/`@ComponentV2` 自定义组件的状态相关行为：静态前端自定义组件的创建与状态变量初始化、`build`/`build2` 渲染入口、`aboutToAppear`/`aboutToDisappear`/`aboutToReuse` 等生命周期回调中状态管理的接入、`@ReusableV2`/`@Reusable` 静态侧复用机制的状态恢复、静态前端 Builder 与状态变量的绑定。详细规格待后续补充。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-07-03-07 |
| 关联需求 | 待补充 |
| 关联 Epic | 无 |
| 目标 Feature | 待补充 |
| 复杂度 | 高 |
| 目标版本 | 待定 |
| Owner | ArkUI SIG |
| 状态 | 待补充 |
| FuncID | 07-03-07 |
| 源码根 | 待定（静态前端 arkoala 自定义组件状态适配，`frameworks/bridge/arkts_frontend/` 相关） |
| SDK 声明 | `interface/sdk-js/api/arkui/stateManagement/decorator.static.d.ets`（@Component/@ComponentV2 自定义组件装饰器，经 `@ohos.arkui.stateManagement.static.d.ets` 重导出） |
| 测试入口 | 待定 |
| 前置依赖 | 07-03-01（组件化 — @Component/@ComponentV2 自定义组件声明与创建基线）、07-03-02（自定义组件生命周期 — 静态前端生命周期接入基线）、07-03-03（自定义组件复用 — @Reusable 复用基线）、07-02-08（静态 V1 组件内 — @Component 状态装饰器）、07-02-11（静态 V2 组件内 — @ComponentV2 状态装饰器） |
| 下游影响 | 07-02-14（互操作 — 静态前端自定义组件与动态前端互操作） |
| 关键错误码 | 待定 |

## 规划范围

本域计划覆盖以下内容（待 Feat 拆分）：

- 静态前端 `@Component`/`@ComponentV2` 自定义组件创建与状态变量初始化
- 静态前端 `build`/`build2` 渲染入口与状态变量依赖收集
- 静态前端 `aboutToAppear`/`aboutToDisappear`/`aboutToReuse` 等生命周期回调中的状态管理接入
- 静态前端 `@ReusableV2`/`@Reusable` 复用机制的状态恢复
- 静态前端 Builder 与状态变量的绑定

> 注：自定义组件通用机制（声明、生命周期、复用、冻结、测量布局）归 07-03-01~05；本域聚焦静态前端下自定义组件与状态管理相关的差异与适配行为。
