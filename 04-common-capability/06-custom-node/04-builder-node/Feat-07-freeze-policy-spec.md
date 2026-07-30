# 特性规格

> Func-04-06-04-Feat-07 BuilderNode 冻结策略：固化 inheritFreezeOptions 行为。主角 ArkTS BuilderNode。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | BuilderNode 冻结策略 |
| 特性编号 | Func-04-06-04-Feat-07 |
| 所属 Epic | 自定义节点能力 / BuilderNode |
| 优先级 | P3 |
| 目标版本 | API 20（dynamic 起始）；静态 @since 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单（L1） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | inheritFreezeOptions | API 20 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/04-builder-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/BuilderNode.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 继承父冻结策略
**作为** 应用开发者，**我想要** 控制 BuilderNode 是否继承父冻结策略，
**以便** 实现该能力。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `inheritFreezeOptions(true)` 且父为自定义组件/BuilderNode/ComponentContent/ReactiveBuilderNode/ReactiveComponentContent THEN 继承父冻结策略 | 正常 |
| AC-1.2 | WHEN 继承冻结 THEN 子自定义组件不再进一步继承 | 边界 |
| AC-1.3 | WHEN `inheritFreezeOptions(false)` THEN 节点不激活时保持不冻结 | 正常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.3 | R-1,R-2,R-3 | 单测 | builder_node.ts inheritFreezeOptions |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | inheritFreezeOptions(true) 且父为指定类型 | 继承父冻结策略 | 父须为自定义组件/BuilderNode/ComponentContent/ReactiveBuilderNode/ReactiveComponentContent | AC-1.1 |
| R-2 | 边界 | 继承冻结后 | 子自定义组件不再进一步继承 | — | AC-1.2 |
| R-3 | 行为 | inheritFreezeOptions(false) | 不激活时保持不冻结 | 默认行为 | AC-1.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-3 冻结策略 | 单测 | 继承父、子不再继承、false 不冻结 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| inheritFreezeOptions(enabled) | Public | enabled: boolean | void | — | 继承父冻结策略 | AC-1 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**inheritFreezeOptions**

| 属性 | 值 |
|------|-----|
| 函数签名 | `inheritFreezeOptions(enabled: boolean): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | true + 父指定类型 | 继承父冻结 | AC-1.1 |
| 2 | 继承后 | 子不再继承 | AC-1.2 |
| 3 | false | 不冻结 | AC-1.3 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 20（dynamic）；静态 @since 23。
- **API 版本号策略:** @since 20 dynamic / 23 static。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| 子不再继承 | 继承冻结后子自定义组件不进一步继承 | BuilderNode.d.ts |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 父类型限制 | 须为自定义组件/BuilderNode/ComponentContent/ReactiveBuilderNode/ReactiveComponentContent | AC-1.1 |
| 单层继承 | 子不再继承 | AC-1.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | false 保持不冻结 | 单测 | builder_node.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | API20 引入 | AC-1 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（冻结策略；不含响应式 Feat-08）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "builder_node.ts inheritFreezeOptions 与 freeze flags(inheritFreeze/allowFreezeWhenInactive/parentallowFreeze/isFreeze)"
```
