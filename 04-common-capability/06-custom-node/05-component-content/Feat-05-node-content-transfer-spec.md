# 特性规格

> Func-04-06-05-Feat-05 NodeContent 与 Transfer：固化 NodeContent(addFrameNode/removeFrameNode) 与 Transfer 变体(100031)。主角 ArkTS NodeContent/TransComponentContent。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | NodeContent 与 Transfer |
| 特性编号 | Func-04-06-05-Feat-05 |
| 所属 Epic | 自定义节点能力 / ComponentContent |
| 优先级 | P2 |
| 目标版本 | API 12（NodeContent）；Transfer 100031 @since 22；静态 @since 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | NodeContent(addFrameNode/removeFrameNode) | API 12 |
| ADDED | Transfer 变体（isTransferred=true + 100031） | API 22 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/05-component-content/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/NodeContent.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: NodeContent 管理 FrameNode
**作为** 应用开发者，**我想要** 用 NodeContent 管理 FrameNode 子节点（ContentSlot）。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `new NodeContent()` THEN 返回实例（ContentSlot 管理器） | 正常 |
| AC-1.2 | WHEN `addFrameNode(node)` 且 node 未 adopt THEN 添加 node 为子节点（去重） | 正常 |
| AC-1.3 | WHEN node 已 adopt THEN 抛 BusinessError(100025, "cannot be adopted") | 异常 |
| AC-1.4 | WHEN `removeFrameNode(node)` THEN 移除 node | 正常 |

### US-2: Transfer 转换变体
**作为** 应用开发者，**我想要** 了解经 transferDynamic 转换产生的只读 ComponentContent。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN TransComponentContent/TransReactiveComponentContent THEN isTransferred() 返回 true | 正常 |
| AC-2.2 | WHEN Trans 变体调 reuse/update/recycle/updateConfiguration/inheritFreezeOptions/flushState THEN 抛 BusinessError(100031, "...created by transferDynamic not support...") | 异常 |
| AC-2.3 | WHEN createComponentContentByTrans/createReactiveComponentContentByTrans THEN 从现有 native 指针构建（不重新创建） | 正常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2,R-3,R-4 | 单测 | node_content.ts |
| AC-2.1..2.3 | R-5,R-6,R-7 | 单测 | trans_component_content.ts |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | new NodeContent() | 返回实例（ContentSlot 管理器） | — | AC-1.1 |
| R-2 | 行为 | addFrameNode(node) 未 adopt | 添加 node 为子节点（去重） | — | AC-1.2 |
| R-3 | 异常 | node 已 adopt | 抛 100025 | "cannot be adopted" | AC-1.3 |
| R-4 | 行为 | removeFrameNode(node) | 移除 node | — | AC-1.4 |
| R-5 | 行为 | Trans 变体 | isTransferred() 返回 true | — | AC-2.1 |
| R-6 | 异常 | Trans 变体调 reuse/update/recycle/updateConfiguration/inheritFreezeOptions/flushState | 抛 100031 | 转换产生节点只读 | AC-2.2 |
| R-7 | 行为 | createComponentContentByTrans/createReactiveComponentContentByTrans | 从现有 native 指针构建 | 不重新创建 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-4 NodeContent | 单测 | add/remove、100025、去重 |
| VM-2 | R-5..R-7 Transfer | 单测 | isTransferred、100031、trans 工厂 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| NodeContent constructor | Public | — | NodeContent | — | ContentSlot 管理器 | AC-1 |
| addFrameNode(node) | Public | node: FrameNode | void | 100025 | 添加子节点 | AC-1 |
| removeFrameNode(node) | Public | node: FrameNode | void | — | 移除子节点 | AC-1 |
| (Transfer 变体) | Public | — | — | 100031 | 只读转换变体 | AC-2 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**NodeContent / addFrameNode / removeFrameNode**

| 属性 | 值 |
|------|-----|
| 函数签名 | `constructor()`; `addFrameNode(node: FrameNode): void`; `removeFrameNode(node: FrameNode): void` |
| 返回值 | NodeContent / void |
| 开放范围 | Public |
| 错误码 | 100025(adopt) |
| 关联 AC | AC-1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | new NodeContent | 返回 ContentSlot 管理器 | AC-1.1 |
| 2 | addFrameNode 未 adopt | 添加子节点（去重） | AC-1.2 |
| 3 | addFrameNode 已 adopt | 抛 100025 | AC-1.3 |
| 4 | removeFrameNode | 移除子节点 | AC-1.4 |
| 5 | Trans 变体 | isTransferred=true，变更 API 抛 100031 | AC-2.1,2.2 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** NodeContent API 12；Transfer 100031 @since 22；静态 @since 23。
- **API 版本号策略:** NodeContent @since 12 dynamic / 23 static；100031 @since 22。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| Trans 变体抛 100031 | 转换产生节点只读 | trans_component_content.ts |
| NodeContent adopt 100025 | 防止重复挂载 | node_content.ts |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| NodeContent 是 ContentSlot 管理器 | 管理 FrameNode 子节点 | AC-1.1 |
| Trans 变体只读 | 变更 API 抛 100031 | AC-2.2 |
| addFrameNode 去重 | 重复添加幂等 | AC-1.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | adopt/Trans 明确抛错 | 单测 | node_content.ts/trans_component_content.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | NodeContent(12)/Transfer 100031(22) 演进 | AC-1,2 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（NodeContent + Transfer；ComponentContent 本体在 Feat-01..04）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "node_content.ts addFrameNode/removeFrameNode 去重与 100025 adopt"
  - repo: "openharmony/arkui_ace_engine"
    query: "trans_component_content.ts Trans 变体 isTransferred=true 与变更 API 抛 100031"
```
