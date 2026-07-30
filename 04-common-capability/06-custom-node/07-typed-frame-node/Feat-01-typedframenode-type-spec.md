# 特性规格

> Func-04-06-07-Feat-01 TypedFrameNode 类型：固化 TypedFrameNode 接口/抽象类与 initialize/attribute。主角 ArkTS TypedFrameNode。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TypedFrameNode 类型 |
| 特性编号 | Func-04-06-07-Feat-01 |
| 所属 Epic | 自定义节点能力 / TypedFrameNode |
| 优先级 | P1 |
| 目标版本 | API 12（dynamic）；静态 @since 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单（L1） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | TypedFrameNode 接口(动态)/抽象类(静态) + initialize/attribute | API 12 / 23 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/07-typed-frame-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/FrameNode.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: TypedFrameNode 类型定义
**作为** 应用开发者，**我想要** 用 TypedFrameNode 获取类型化的 attribute 句柄，
**以便** 获取相关信息。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 动态 `interface TypedFrameNode<C,T> extends FrameNode` THEN 提供 initialize:C（构造参数）与 readonly attribute:T（属性配置） | 正常 |
| AC-1.2 | WHEN 静态 `abstract class TypedFrameNode<T> extends FrameNode` THEN 提供 get attribute():T | 正常 |
| AC-1.3 | WHEN 访问 attribute THEN 首次访问时懒创建 ArkComponent 句柄（延迟创建） | 正常 |
| AC-1.4 | WHEN TypedFrameNode 通过 typeNode.createNode 创建 THEN 返回类型化实例 | 正常 |

### US-2: initialize 与 attribute 用法

**作为** 应用开发者，
**我想要** initialize 初始化、attribute 获取属性句柄，
**以便** 配置类型化节点。
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 initialize(...args) THEN 委托 attribute.initialize(args) 初始化 | 正常 |
| AC-2.2 | WHEN 多次访问 attribute THEN 返回缓存的 ArkComponent 句柄 | 正常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2,R-3,R-4 | 单测 | frame_node.ts TypedFrameNode @1283 |
| AC-2.1..2.2 | R-5,R-6 | 单测 | frame_node.ts initialize/attribute |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 动态 TypedFrameNode\<C,T\> | 提供 initialize:C + readonly attribute:T | extends FrameNode | AC-1.1 |
| R-2 | 行为 | 静态 TypedFrameNode\<T\> | 提供 get attribute():T | abstract class | AC-1.2 |
| R-3 | 行为 | 访问 attribute | 首次懒创建 ArkComponent 句柄 | 延迟创建 | AC-1.3 |
| R-4 | 行为 | typeNode.createNode 创建 | 返回类型化实例 | — | AC-1.4 |
| R-5 | 行为 | initialize(...args) | 委托 attribute.initialize(args) | — | AC-2.1 |
| R-6 | 行为 | 多次访问 attribute | 返回缓存句柄 | — | AC-2.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-4 类型 | 单测 | 动态/静态差异、懒创建 |
| VM-2 | R-5..R-6 用法 | 单测 | initialize 委托、缓存 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| TypedFrameNode (动态接口) | Public | C: 构造参数, T: 属性 | — | — | 类型化节点接口 | AC-1 |
| TypedFrameNode (静态抽象类) | Public | T: 属性 | — | — | 类型化节点基类 | AC-1 |
| initialize | Public | ...args | T | — | 初始化 | AC-2 |
| attribute (get) | Public | — | T | — | 属性句柄 | AC-2 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**TypedFrameNode 类型**

| 属性 | 值 |
|------|-----|
| 函数签名 | 动态 `interface TypedFrameNode<C,T> extends FrameNode { initialize: C; readonly attribute: T; }`; 静态 `abstract class TypedFrameNode<T> extends FrameNode { get attribute(): T; }` |
| 返回值 | — |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1,2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 动态 TypedFrameNode | initialize:C + readonly attribute:T | AC-1.1 |
| 2 | 静态 TypedFrameNode | get attribute():T | AC-1.2 |
| 3 | 访问 attribute | 懒创建 | AC-1.3 |
| 4 | initialize | 委托 attribute.initialize | AC-2.1 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 12（dynamic）；静态 @since 23。
- **API 版本号策略:** @since 12 dynamic / 23 static。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| 动态 2 泛型 vs 静态 1 泛型 | 动态 \<C,T\>，静态 \<T\> | FrameNode.d.ts/.static.d.ets |
| attribute 懒创建 | 首次访问创建 | frame_node.ts |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| extends FrameNode | 基类方法属 04-06-02 | AC-1.1,1.2 |
| attribute 懒创建 | 首次访问构造 ArkComponent | AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | attribute 懒创建减少开销 | 单测 | frame_node.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | 动态12/静态23 演进 | AC-1 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（TypedFrameNode 类型；typeNode 工厂在 Feat-02/03）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "frame_node.ts TypedFrameNode class attribute 懒创建 attrCreator_ 与 initialize 委托"
```
