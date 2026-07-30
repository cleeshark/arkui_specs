# 特性规格

> Func-04-06-05-Feat-03 ComponentContent 复用与回收：固化 reuse/recycle。主角 ArkTS ComponentContent。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ComponentContent 复用与回收 |
| 特性编号 | Func-04-06-05-Feat-03 |
| 所属 Epic | 自定义节点能力 / ComponentContent |
| 优先级 | P2 |
| 目标版本 | API 12（reuse/recycle）；V2 @ReusableV2 since 26；静态 @since 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单（L1） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | reuse/recycle | API 12 |
| ADDED | V2 @ReusableV2 复用 | API 26 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/05-component-content/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/ComponentContent.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 复用与回收

**作为** 应用开发者，
**我想要** reuse/recycle 复用回收内部自定义组件，
**以便** 节点复用降低开销。
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `reuse(param?)` THEN 同步触发内部自定义组件 aboutToReuse(param)；param 须含构造参数；默认 undefined 用原始数据源 | 正常 |
| AC-1.2 | WHEN `recycle()` THEN 触发 aboutToRecycle（复用机制配对） | 正常 |
| AC-1.3 | WHEN Trans 变体调 reuse/recycle THEN 抛 100031 | 异常 |
| AC-1.4 | WHEN API26 且用 @ReusableV2 THEN 支持 V2 复用 | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2,R-3,R-4 | 单测 | component_content.ts reuse/recycle |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | reuse(param?) | 同步触发 aboutToReuse(param)（委托 BuilderNode.reuse） | param 须含构造参数；默认 undefined 用原始数据源 | AC-1.1 |
| R-2 | 行为 | recycle() | 触发 aboutToRecycle（委托 BuilderNode.recycle） | 与 reuse 配对 | AC-1.2 |
| R-3 | 异常 | Trans 变体调 reuse/recycle | 抛 100031 | — | AC-1.3 |
| R-4 | 边界 | API26 + @ReusableV2 | 支持 V2 复用 | V2 since 26 | AC-1.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-4 复用回收 | 单测 | aboutToReuse/Recycle、Trans 抛 100031、V2 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| reuse(param?) | Public | param?: Object(动态)/RecordData(静态) | void | 100031(Trans) | 复用 | AC-1 |
| recycle() | Public | — | void | 100031(Trans) | 回收 | AC-1 |

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
| 错误码 | 100031(Trans 变体) |
| 关联 AC | AC-1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | reuse(param) | 同步触发 aboutToReuse | AC-1.1 |
| 2 | recycle | 触发 aboutToRecycle | AC-1.2 |
| 3 | Trans 调 reuse/recycle | 抛 100031 | AC-1.3 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** reuse/recycle API 12；静态 @since 23；V2 @ReusableV2 API 26。
- **API 版本号策略:** @since 12 dynamic / 23 static；V2 @since 26。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| Trans 变体抛 100031 | 转换产生节点不可复用 | component_content.ts |
| V2 复用 API26 | @ReusableV2 since 26 | ComponentContent.d.ts |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 委托 BuilderNode | reuse/recycle 委托 | AC-1.1,1.2 |
| 同步触发 | reuse 同步触发 aboutToReuse | AC-1.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | Trans 明确抛错 | 单测 | component_content.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | V2 复用 API26 | AC-1.4 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（复用回收；不含 Reactive Feat-04）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "component_content.ts reuse/recycle 同步触发 aboutToReuse/Recycle 与 Trans 抛 100031"
```
