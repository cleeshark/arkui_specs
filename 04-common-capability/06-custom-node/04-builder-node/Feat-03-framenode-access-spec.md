# 特性规格

> Func-04-06-04-Feat-03 BuilderNode FrameNode 访问：固化 getFrameNode 与 BuilderRootFrameNode 不可改性。主角 ArkTS BuilderNode。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | BuilderNode FrameNode 访问 |
| 特性编号 | Func-04-06-04-Feat-03 |
| 所属 Epic | 自定义节点能力 / BuilderNode |
| 优先级 | P1 |
| 目标版本 | API 11（dynamic 起始）；静态 @since 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单（L1） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | getFrameNode | API 11 |
| ADDED | BuilderRootFrameNode 不可改性 | API 11 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/04-builder-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/BuilderNode.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 获取 FrameNode
**作为** 应用开发者，**我想要** 获取 BuilderNode 持有的 FrameNode 以挂载到其他节点，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `getFrameNode()` 且已 build THEN 返回持有的 FrameNode | 正常 |
| AC-1.2 | WHEN 未 build THEN 返回 null | 边界 |
| AC-1.3 | WHEN 该 FrameNode 用于挂载到其他 FrameNode 子节点 THEN 允许 | 正常 |

### US-2: 不可改根节点约束
**作为** 应用开发者，**我想要** 了解 BuilderRootFrameNode 的不可改约束，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 对 getFrameNode() 返回的节点调 appendChild/insertChildAfter/removeChild/clearChildren THEN 抛 BusinessError(100021, "The FrameNode is not modifiable.") | 异常 |
| AC-2.2 | WHEN 设置该 FrameNode 属性/操作其子节点 THEN 行为未定义（SDK 警告） | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.3 | R-1,R-2,R-3 | 单测 | builder_node.ts getFrameNode |
| AC-2.1..2.2 | R-4,R-5 | 单测 | frame_node.ts BuilderRootFrameNode |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | getFrameNode() 已 build | 返回持有的 FrameNode | — | AC-1.1 |
| R-2 | 边界 | 未 build | 返回 null | — | AC-1.2 |
| R-3 | 行为 | 用于挂载到其他 FrameNode | 允许 | — | AC-1.3 |
| R-4 | 异常 | 对返回节点调树操作 | 抛 100021 | BuilderRootFrameNode 不可改 | AC-2.1 |
| R-5 | 边界 | 设置属性/操作子节点 | 行为未定义 | SDK 警告 | AC-2.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-3 getFrameNode | 单测 | build 后返回、未 build null |
| VM-2 | R-4..R-5 不可改 | 单测 | 100021 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| getFrameNode() | Public | — | FrameNode\|null | — | 获取持有 FrameNode | AC-1 |
| (BuilderRootFrameNode 不可改) | Public | — | — | 100021 | 根节点不可改约束 | AC-2 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**getFrameNode**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getFrameNode(): FrameNode \| null` |
| 返回值 | FrameNode\|null |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 已 build | 返回 FrameNode | AC-1.1 |
| 2 | 未 build | 返回 null | AC-1.2 |
| 3 | 树操作 | 抛 100021 | AC-2.1 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 11；静态 @since 23。
- **API 版本号策略:** @since 11 dynamic / 23 static。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| 设置 FrameNode 属性行为未定义 | SDK 警告 | BuilderNode.d.ts |
| BuilderRootFrameNode 不可改 | 树操作抛 100021 | frame_node.ts |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 不可改根 | BuilderRootFrameNode 树操作抛 100021 | AC-2.1 |
| 仅用于挂载 | getFrameNode 返回的节点用于挂载，不操作子树 | AC-1.3,2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | getFrameNode 未 build 返 null 不崩溃 | 单测 | builder_node.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 否 | 全部 API 11/23 | — |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（FrameNode 访问；不含渲染类型 Feat-04）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "builder_node.ts getFrameNode 返回 frameNode_ 与 BuilderRootFrameNode 不可改抛 100021"
```
