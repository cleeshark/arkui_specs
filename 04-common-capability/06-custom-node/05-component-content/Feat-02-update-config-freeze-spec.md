# 特性规格

> Func-04-06-05-Feat-02 ComponentContent 更新配置冻结：固化 update/updateConfiguration/inheritFreezeOptions。主角 ArkTS ComponentContent。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ComponentContent 更新配置冻结 |
| 特性编号 | Func-04-06-05-Feat-02 |
| 所属 Epic | 自定义节点能力 / ComponentContent |
| 优先级 | P2 |
| 目标版本 | API 12（update/updateConfiguration）；inheritFreezeOptions API 20；静态 @since 23（无 inheritFreezeOptions） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单（L1） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | update/updateConfiguration | API 12 |
| ADDED | inheritFreezeOptions | API 20（仅动态） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/05-component-content/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/ComponentContent.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 更新参数
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `update(args)` THEN 用新 args 重新渲染（委托 BuilderNode.update）；args 类型须匹配 constructor | 正常 |
| AC-1.2 | WHEN Trans 变体调 update THEN 抛 BusinessError(100031) | 异常 |

### US-2: 配置变更与冻结
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `updateConfiguration()` THEN 通知系统环境变更并重新加载（委托 BuilderNode） | 正常 |
| AC-2.2 | WHEN `inheritFreezeOptions(enabled)` THEN 控制是否继承父冻结策略（委托 BuilderNode） | 正常 |
| AC-2.3 | WHEN 静态形式 THEN 无 inheritFreezeOptions | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.2 | R-1,R-2 | 单测 | component_content.ts update |
| AC-2.1..2.3 | R-3,R-4,R-5 | 单测 | component_content.ts updateConfiguration/inheritFreezeOptions |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | update(args) | 重新渲染（委托 BuilderNode.update） | args 类型须匹配 | AC-1.1 |
| R-2 | 异常 | Trans 变体调 update | 抛 100031 | — | AC-1.2 |
| R-3 | 行为 | updateConfiguration() | 通知环境变更重新加载（委托 BuilderNode） | — | AC-2.1 |
| R-4 | 行为 | inheritFreezeOptions(enabled) | 控制继承父冻结策略（委托 BuilderNode） | 仅动态 @since 20 | AC-2.2 |
| R-5 | 边界 | 静态形式 | 无 inheritFreezeOptions | — | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-2 update | 单测 | 委托、Trans 抛 100031 |
| VM-2 | R-3..R-5 配置冻结 | 单测 | 委托、静态无 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| update(args) | Public | args: Object | void | 100031(Trans) | 更新 | AC-1 |
| updateConfiguration() | Public | — | void | 100031(Trans) | 配置变更 | AC-2 |
| inheritFreezeOptions(enabled) | Public(仅动态) | enabled: boolean | void | 100031(Trans) | 冻结策略 | AC-2 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**update / updateConfiguration / inheritFreezeOptions**

| 属性 | 值 |
|------|-----|
| 函数签名 | `update(args: Object): void`; `updateConfiguration(): void`; `inheritFreezeOptions(enabled: boolean): void` |
| 返回值 | void |
| 开放范围 | Public（inheritFreezeOptions 仅动态） |
| 错误码 | 100031(Trans 变体) |
| 关联 AC | AC-1,2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | update(args) | 重新渲染 | AC-1.1 |
| 2 | Trans 调 update | 抛 100031 | AC-1.2 |
| 3 | updateConfiguration | 重新加载 | AC-2.1 |
| 4 | inheritFreezeOptions | 控制冻结 | AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** update/updateConfiguration API 12；inheritFreezeOptions API 20（仅动态）；静态 @since 23。
- **API 版本号策略:** inheritFreezeOptions 仅动态 @since 20。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| Trans 变体抛 100031 | 转换产生节点不可改 | component_content.ts |
| 静态无 inheritFreezeOptions | 动态/静态差异 | .static.d.ets |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 委托 BuilderNode | update/updateConfiguration/inheritFreezeOptions 均委托 | AC-1.1,2.1,2.2 |
| Trans 只读 | 抛 100031 | AC-1.2 |

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
| 版本升级 | 是 | inheritFreezeOptions(20) 演进 | AC-2.2 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（更新配置冻结；不含复用 Feat-03）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "component_content.ts update/updateConfiguration/inheritFreezeOptions 委托 BuilderNode 与 Trans 抛 100031"
```
