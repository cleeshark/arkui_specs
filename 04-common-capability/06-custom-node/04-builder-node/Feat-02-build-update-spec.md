# 特性规格

> Func-04-06-04-Feat-02 BuilderNode 构建与更新：固化 build/update/updateConfiguration 与 BuildOptions 的行为规格。主角 ArkTS BuilderNode。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | BuilderNode 构建与更新 |
| 特性编号 | Func-04-06-04-Feat-02 |
| 所属 Epic | 自定义节点能力 / BuilderNode |
| 优先级 | P1 |
| 目标版本 | API 11（build/update 起始）；BuildOptions 字段 API 12-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | build/update | API 11 |
| ADDED | updateConfiguration | API 12 |
| ADDED | BuildOptions.nestingBuilderSupported | API 12 dynamiconly |
| ADDED | BuildOptions.localStorage/enableProvideConsumeCrossing | API 20 dynamic |
| ADDED | BuildOptions.useParallel | API 23 staticonly |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/04-builder-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/BuilderNode.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 构建组件树
**作为** 应用开发者，**我想要** 用 WrappedBuilder 构建组件树，
**以便** 使用该节点。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `build(builder, arg?, options?)` THEN 从 @Builder 创建组件树并持有根；arg 按值传递 | 正常 |
| AC-1.2 | WHEN 传 BuildOptions.nestingBuilderSupported=true THEN 支持嵌套 builder；params 包 Proxy，写抛 BusinessError(140109) | 边界 |
| AC-1.3 | WHEN 传 BuildOptions.localStorage THEN 子自定义组件共享 LocalStorage（构造传入优先） | 正常 |
| AC-1.4 | WHEN 传 BuildOptions.enableProvideConsumeCrossing=true THEN 启用 @Consume(V1)/@Consumer(V2) 与外部 @Provide/@Provider 双向同步 | 正常 |
| AC-1.5 | WHEN 静态 BuildOptions.useParallel=true THEN 启用并行创建 | 边界 |

### US-2: 更新参数
**作为** 应用开发者，**我想要** 用新参数重新渲染，
**以便** 实现该能力。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `update(arg)` 且非冻结 THEN 用新 arg 重新渲染；arg 类型须匹配 build | 正常 |
| AC-2.2 | WHEN 节点冻结 THEN update 参数暂存，解冻后执行 | 边界 |
| AC-2.3 | WHEN 内部变量用 @Prop THEN 可响应 update | 正常 |

### US-3: 配置变更
**作为** 应用开发者，**我想要** 系统环境变更时重新加载，
**以便** 实现该能力。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `updateConfiguration()` THEN 重跑 update funcs + forceCompleteRerender + native updateConfiguration | 正常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.5 | R-1,R-2,R-3,R-4,R-5,R-6 | 单测 | builder_node.ts build/JSBuilderNode |
| AC-2.1..2.3 | R-7,R-8,R-9 | 单测 | builder_node.ts update |
| AC-3.1 | R-10 | 单测 | builder_node.ts updateConfiguration |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | build(builder, arg?, options?) | 从 @Builder 创建组件树并持有根 | arg 按值传递 | AC-1.1 |
| R-2 | 行为 | nestingBuilderSupported=true | 支持嵌套 builder | params Proxy，写抛 140109 | AC-1.2 |
| R-3 | 行为 | localStorage | 子组件共享 LocalStorage | 构造传入优先 | AC-1.3 |
| R-4 | 行为 | enableProvideConsumeCrossing=true | @Consume/@Consumer 与外部双向同步 | V1 @since20，V2 @since23 | AC-1.4 |
| R-5 | 边界 | useParallel(staticonly) | 启用并行创建 | 默认 false | AC-1.5 |
| R-6 | 边界 | @Builder 无状态 | 状态更新须显式 update() | — | AC-1.1 |
| R-7 | 行为 | update(arg) 非冻结 | 用新 arg 重新渲染 | arg 类型须匹配 | AC-2.1 |
| R-8 | 边界 | 节点冻结 | update 参数暂存，解冻后执行 | — | AC-2.2 |
| R-9 | 行为 | 内部 @Prop | 可响应 update | — | AC-2.3 |
| R-10 | 行为 | updateConfiguration() | 重跑 update funcs + forceCompleteRerender + native | — | AC-3.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-6 build | 单测 | 按值传递、nesting Proxy、localStorage |
| VM-2 | R-7..R-9 update | 单测 | 冻结暂存、@Prop |
| VM-3 | R-10 updateConfiguration | 单测 | forceCompleteRerender |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| build(builder, arg?, options?) | Public | WrappedBuilder; arg?: Object; options?: BuildOptions | void | — | 构建组件树 | AC-1 |
| update(arg) | Public | arg: Object | void | — | 重新渲染 | AC-2 |
| updateConfiguration() | Public | — | void | — | 配置变更重载 | AC-3 |
| BuildOptions | Public | {nestingBuilderSupported?, localStorage?, enableProvideConsumeCrossing?(dynamic); useParallel?(static)} | — | — | 构建选项 | AC-1 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**build / update / updateConfiguration**

| 属性 | 值 |
|------|-----|
| 函数签名 | `build(builder, arg?, options?): void`; `update(arg: Object): void`; `updateConfiguration(): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | 140109(nesting Proxy 写) |
| 关联 AC | AC-1,2,3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | build | 创建组件树，arg 按值 | AC-1.1 |
| 2 | nestingBuilderSupported | Proxy 写抛 140109 | AC-1.2 |
| 3 | update 非冻结 | 重新渲染 | AC-2.1 |
| 4 | update 冻结 | 暂存 | AC-2.2 |
| 5 | updateConfiguration | forceCompleteRerender | AC-3.1 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** build/update API 11；updateConfiguration/nestingBuilderSupported API 12；localStorage/enableProvideConsumeCrossing API 20；静态 build @since 23；useParallel @since 23 staticonly。
- **API 版本号策略:** 逐字段 @since；动态静态 BuildOptions 字段不同。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| @Builder 无状态 | 须显式 update | BuilderNode.d.ts |
| nesting Proxy 写抛 140109 | 仅 nestingBuilderSupported 时 | builder_node.ts |
| 动态/静态 BuildOptions 字段不同 | useParallel 仅静态，enableProvideConsumeCrossing 仅动态 | .d.ts/.static.d.ets |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 按值传递 | arg 按值，状态须 update | AC-1.1,2.1 |
| @Prop 响应 | 内部 @Prop 可响应 update | AC-2.3 |
| 冻结暂存 | 冻结时 update 暂存 | AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | useParallel 并行创建 | 单测 | builder_node.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | BuildOptions 字段 12-26 演进 | AC-1.2..1.5 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（构建更新；不含 FrameNode 访问 Feat-03）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "JSBuilderNode build/buildWithNestingBuilder Proxy 写抛 140109 与 localStorage 共享"
  - repo: "openharmony/arkui_ace_engine"
    query: "builder_node.ts update 冻结暂存 updateParams_ 与 @Prop 响应"
```
