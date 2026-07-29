# 特性规格

> Func-04-06-04-Feat-05 BuilderNode 复用与回收：固化 reuse/recycle 与 @Reusable 限制。主角 ArkTS BuilderNode。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | BuilderNode 复用与回收 |
| 特性编号 | Func-04-06-04-Feat-05 |
| 所属 Epic | 自定义节点能力 / BuilderNode |
| 优先级 | P2 |
| 目标版本 | API 12（dynamic 起始）；V2 @ReusableV2 since 26；静态 @since 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | reuse/recycle | API 12 |
| ADDED | @Reusable 限制（抛 100030） | API 12 |
| ADDED | V2 @ReusableV2 复用 | API 26 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/04-builder-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/BuilderNode.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 复用
**作为** 应用开发者，**我想要** 复用 BuilderNode 内部自定义组件，
**以便** 实现该能力。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `reuse(param?)` THEN 触发内部自定义组件 aboutToReuse(param)；param 须含全部构造参数 | 正常 |
| AC-1.2 | WHEN param 默认 undefined THEN 使用原始构造数据源 | 边界 |
| AC-1.3 | WHEN API26 且内部用 @ReusableV2 THEN 支持 V2 复用 | 边界 |

### US-2: 回收
**作为** 应用开发者，**我想要** 回收内部自定义组件，
**以便** 释放或撤销状态。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `recycle()` THEN 触发内部自定义组件 aboutToRecycle（复用机制一部分） | 正常 |

### US-3: @Reusable 限制
**作为** 应用开发者，**我想要** 了解 @Reusable 限制，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN builder 内自定义组件用 @Reusable THEN 抛 BusinessError(100030, "custom component in @Builder used by BuilderNode does not support @Reusable") | 异常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.3 | R-1,R-2,R-3 | 单测 | builder_node.ts reuse/aboutToReuseInternal |
| AC-2.1 | R-4 | 单测 | builder_node.ts recycle/aboutToRecycleInternal |
| AC-3.1 | R-5 | 单测 | builder_node.ts observeRecycleComponentCreation |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | reuse(param?) | 触发 aboutToReuse(param) | param 须含构造参数 | AC-1.1 |
| R-2 | 边界 | param undefined | 使用原始构造数据源 | 默认 undefined | AC-1.2 |
| R-3 | 边界 | API26 + @ReusableV2 | 支持 V2 复用 | V2 since 26 | AC-1.3 |
| R-4 | 行为 | recycle() | 触发 aboutToRecycle | 复用机制一部分 | AC-2.1 |
| R-5 | 异常 | builder 内 @Reusable | 抛 100030 | 不支持 @Reusable | AC-3.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-3 reuse | 单测 | aboutToReuse、V2 |
| VM-2 | R-4 recycle | 单测 | aboutToRecycle |
| VM-3 | R-5 @Reusable | 单测 | 100030 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| reuse(param?) | Public | param?: Object(动态)/RecordData(静态) | void | — | 复用 | AC-1 |
| recycle() | Public | — | void | — | 回收 | AC-2 |
| (@Reusable 限制) | Public | — | — | 100030 | 不支持 @Reusable | AC-3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**reuse / recycle**

| 属性 | 值 |
|------|-----|
| 函数签名 | `reuse(param?: Object): void`; `recycle(): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | 100030(@Reusable) |
| 关联 AC | AC-1,2,3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | reuse(param) | 触发 aboutToReuse | AC-1.1 |
| 2 | param undefined | 用原始数据源 | AC-1.2 |
| 3 | recycle | 触发 aboutToRecycle | AC-2.1 |
| 4 | @Reusable | 抛 100030 | AC-3.1 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** reuse/recycle API 12；静态 @since 23；V2 @ReusableV2 API 26。
- **API 版本号策略:** @since 12 dynamic / 23 static；V2 @since 26。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| @Reusable 抛 100030 | builder 内自定义组件不支持 | builder_node.ts |
| V2 复用 API26 | @ReusableV2 since 26 | BuilderNode.d.ts |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 复用由 BuilderNode 统一管理 | @Reusable 不允许 | AC-3.1 |
| param 须含构造参数 | reuse 触发 aboutToReuse | AC-1.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | @Reusable 明确抛错 | 单测 | builder_node.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | reuse(12)/V2(26) 演进 | AC-1.3 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（复用回收；不含输入事件 Feat-06）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "builder_node.ts reuse/recycle aboutToReuseInternal/aboutToRecycleInternal 与 @Reusable 抛 100030"
```
