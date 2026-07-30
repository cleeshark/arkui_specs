# 特性规格

> Func-04-06-04-Feat-08 BuilderNode 响应式变体：固化 ReactiveBuilderNode 与 flushState 行为。主角 ArkTS ReactiveBuilderNode。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | BuilderNode 响应式变体 |
| 特性编号 | Func-04-06-04-Feat-08 |
| 所属 Epic | 自定义节点能力 / BuilderNode |
| 优先级 | P2 |
| 目标版本 | API 22（dynamic 起始）；静态 @since 26.0.0 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ReactiveBuilderNode（多参数 @Builder + V2 自动更新 + flushState） | API 22 dynamic / 26 static |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/04-builder-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/BuilderNode.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 响应式构建
**作为** 应用开发者，**我想要** 用多参数 @Builder 构建响应式节点，
**以便** 使用该节点。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `new ReactiveBuilderNode(uiContext, options?)` 且 uiContext 有效 THEN 返回实例 | 正常 |
| AC-1.2 | WHEN `build(builder, config, ...args)` THEN 用多参数 @Builder 创建组件树 | 正常 |
| AC-1.3 | WHEN 绑定参数用 @ObservedV2(V2) THEN 数据变化自动更新（无须 flushState） | 正常 |
| AC-1.4 | WHEN 绑定参数用 @Observed(V1) THEN 须手动 `flushState()` 刷新 | 正常 |

### US-2: 生命周期与事件（复用 BuilderNode 语义）
**作为** 应用开发者，**我想要** ReactiveBuilderNode 复用 BuilderNode 的生命周期/事件语义，
**以便** 实现该能力。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `getFrameNode()`/`dispose()`/`reuse(param?)`/`recycle()`/`updateConfiguration()` THEN 行为同 BuilderNode 对应 API | 正常 |
| AC-2.2 | WHEN `postTouchEvent`/`postInputEvent`/`postInputEventWithStrategy` THEN 行为同 BuilderNode 事件分发 | 正常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2,R-3,R-4 | 单测 | builder_node.ts ReactiveBuilderNode/ReactiveBuilderNodeBase |
| AC-2.1..2.2 | R-5,R-6 | 单测 | builder_node.ts（复用 JSBuilderNode 语义） |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | new ReactiveBuilderNode(uiContext, options?) | 返回实例 | uiContext 须有效 | AC-1.1 |
| R-2 | 行为 | build(builder, config, ...args) | 多参数 @Builder 创建组件树 | — | AC-1.2 |
| R-3 | 行为 | V2(@ObservedV2) 绑定参数 | 数据变化自动更新 | 无须 flushState | AC-1.3 |
| R-4 | 行为 | V1(@Observed) 绑定参数 | 须手动 flushState() 刷新 | — | AC-1.4 |
| R-5 | 行为 | getFrameNode/dispose/reuse/recycle/updateConfiguration | 行为同 BuilderNode | 复用语义 | AC-2.1 |
| R-6 | 行为 | postTouchEvent/postInputEvent/postInputEventWithStrategy | 行为同 BuilderNode 事件分发 | 复用语义 | AC-2.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-4 响应式构建 | 单测 | 多参数、V2 自动、V1 flushState |
| VM-2 | R-5..R-6 复用语义 | 单测 | 同 BuilderNode |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| ReactiveBuilderNode constructor | Public | uiContext, options? | ReactiveBuilderNode | 401 | 创建 | AC-1 |
| build(builder, config, ...args) | Public | WrappedBuilder, BuildOptions, ...args | void | — | 多参数构建 | AC-1 |
| flushState() | Public | — | void | — | V1 状态刷新 | AC-1 |
| getFrameNode/dispose/reuse/recycle/updateConfiguration | Public | 同 BuilderNode | 同 | — | 生命周期 | AC-2 |
| postTouchEvent/postInputEvent/postInputEventWithStrategy | Public | 同 BuilderNode | boolean | — | 事件分发 | AC-2 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**ReactiveBuilderNode / build / flushState**

| 属性 | 值 |
|------|-----|
| 函数签名 | `constructor(uiContext, options?)`; `build(builder, config, ...args): void`; `flushState(): void` |
| 返回值 | ReactiveBuilderNode / void |
| 开放范围 | Public |
| 错误码 | 401(uiContext 无效) |
| 关联 AC | AC-1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | constructor | 返回实例 | AC-1.1 |
| 2 | build 多参数 | 创建组件树 | AC-1.2 |
| 3 | V2 参数变化 | 自动更新 | AC-1.3 |
| 4 | V1 参数 | 须 flushState | AC-1.4 |
| 5 | 生命周期/事件 | 同 BuilderNode | AC-2.1,2.2 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 22（dynamic）；静态 @since 26.0.0。
- **API 版本号策略:** @since 22 dynamic / 26 static；V2 复用 @since 26。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| V1/V2 更新差异 | V1 须 flushState，V2 自动 | BuilderNode.d.ts |
| 静态无 generic/无 inheritFreezeOptions | 静态 ReactiveBuilderNode 简化 | BuilderNode.static.d.ets |
| 静态 build 单重载 | 与动态多重载不同 | .static.d.ets |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 多参数 @Builder | 区别于 BuilderNode 单参数 | AC-1.2 |
| V2 自动更新 | @ObservedV2 无须 flushState | AC-1.3 |
| 复用语义 | 生命周期/事件同 BuilderNode | AC-2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | V2 自动更新减少手动调用 | 单测 | builder_node.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | ReactiveBuilderNode(22)/静态(26)/V2(26) 演进 | AC-1.3 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（响应式变体；不含 BuilderNode 本体 Feat-01..07）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "builder_node.ts ReactiveBuilderNode/ReactiveBuilderNodeBase build 多参数 createReactive 与 flushState V1/V2"
  - repo: "openharmony/arkui_ace_engine"
    query: "BuilderNode.d.ts ReactiveBuilderNode @since 22/26 与静态无 generic 差异"
```
