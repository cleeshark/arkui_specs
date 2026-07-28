# 特性规格

> Func-04-06-05-Feat-04 ReactiveComponentContent：固化响应式内容变体与 flushState。主角 ArkTS ReactiveComponentContent。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ReactiveComponentContent |
| 特性编号 | Func-04-06-05-Feat-04 |
| 所属 Epic | 自定义节点能力 / ComponentContent |
| 优先级 | P2 |
| 目标版本 | API 22（dynamic）；静态 @since 26.0.0；isTransferred API 24 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ReactiveComponentContent（多参数 + flushState） | API 22 dynamic / 26 static |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/05-component-content/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/ComponentContent.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 响应式创建
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `new ReactiveComponentContent(uiContext, builder, config, ...args)` THEN 返回实例（内部建 ReactiveBuilderNode） | 正常 |
| AC-1.2 | WHEN 静态 `new ReactiveComponentContent(uiContext, builder, options?)` THEN 返回实例（builder 为 CustomBuilder，options 可选） | 边界 |

### US-2: 状态刷新
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `flushState()` 且 V1(@Observed) 绑定参数 THEN 手动刷新状态 | 正常 |
| AC-2.2 | WHEN V2(@ObservedV2) 绑定参数 THEN 自动更新（无须 flushState） | 正常 |
| AC-2.3 | WHEN Trans 变体调 flushState THEN 抛 100031 | 异常 |

### US-3: 生命周期（复用 ComponentContent 语义）
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN reuse/recycle/dispose/updateConfiguration/inheritFreezeOptions/isDisposed/isTransferred THEN 行为同 ComponentContent 对应 API | 正常 |
| AC-3.2 | WHEN 静态形式 THEN 无 update、无 inheritFreezeOptions | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.2 | R-1,R-2 | 单测 | component_content.ts ReactiveComponentContent |
| AC-2.1..2.3 | R-3,R-4,R-5 | 单测 | component_content.ts flushState |
| AC-3.1..3.2 | R-6,R-7 | 单测 | component_content.ts（复用语义） |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | constructor(uiContext, builder, config, ...args) | 返回实例（建 ReactiveBuilderNode） | 多参数 @Builder | AC-1.1 |
| R-2 | 边界 | 静态 constructor(uiContext, builder, options?) | 返回实例 | builder CustomBuilder；options 可选 | AC-1.2 |
| R-3 | 行为 | flushState() V1(@Observed) | 手动刷新状态 | — | AC-2.1 |
| R-4 | 行为 | V2(@ObservedV2) 绑定参数 | 自动更新 | 无须 flushState | AC-2.2 |
| R-5 | 异常 | Trans 变体调 flushState | 抛 100031 | — | AC-2.3 |
| R-6 | 行为 | reuse/recycle/dispose/updateConfiguration/inheritFreezeOptions/isDisposed/isTransferred | 行为同 ComponentContent | 复用语义 | AC-3.1 |
| R-7 | 边界 | 静态形式 | 无 update、无 inheritFreezeOptions | — | AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-2 创建 | 单测 | 多参数、静态差异 |
| VM-2 | R-3..R-5 flushState | 单测 | V1 手动/V2 自动、Trans 抛 |
| VM-3 | R-6..R-7 复用语义 | 单测 | 同 ComponentContent、静态差异 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| ReactiveComponentContent constructor | Public | uiContext, builder, config, ...args(动态)/builder, options?(静态) | ReactiveComponentContent | 401 | 创建 | AC-1 |
| flushState() | Public | — | void | 100031(Trans) | V1 状态刷新 | AC-2 |
| (复用 ComponentContent API) | Public | 同 | 同 | 同 | 生命周期 | AC-3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**ReactiveComponentContent / flushState**

| 属性 | 值 |
|------|-----|
| 函数签名 | `constructor(uiContext, builder, config, ...args)`(动态)/`constructor(uiContext, builder, options?)`(静态); `flushState(): void` |
| 返回值 | ReactiveComponentContent / void |
| 开放范围 | Public |
| 错误码 | 401(uiContext); 100031(Trans flushState) |
| 关联 AC | AC-1,2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | constructor | 返回实例 | AC-1.1 |
| 2 | flushState V1 | 手动刷新 | AC-2.1 |
| 3 | V2 参数 | 自动更新 | AC-2.2 |
| 4 | Trans flushState | 抛 100031 | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 22（dynamic）；静态 @since 26.0.0；isTransferred API 24。
- **API 版本号策略:** @since 22 dynamic / 26 static。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| V1/V2 更新差异 | V1 须 flushState，V2 自动 | ComponentContent.d.ts |
| 静态无 update/inheritFreezeOptions | 动态/静态差异 | .static.d.ets |
| 静态 ctor 签名不同 | CustomBuilder + options? | .static.d.ets |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 内部用 ReactiveBuilderNode | 建响应式节点 | AC-1.1 |
| V1/V2 差异 | V1 须 flushState | AC-2.1,2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | V2 自动更新 | 单测 | component_content.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | ReactiveCC(22)/静态(26)/V2(26) 演进 | AC-1.2,2.2 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（ReactiveComponentContent；不含 NodeContent/Transfer Feat-05）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "component_content.ts ReactiveComponentContent 建 ReactiveBuilderNode + flushState V1/V2 与静态差异"
```
