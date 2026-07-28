# 特性规格

> Func-04-06-07-Feat-03 typeNode 静态工厂：固化 createXxxNode/getXxxAttribute/getXxxEvent/bindXxxController（命名函数）+ XxxFrameNode 抽象类。主角 ArkTS typeNode 静态。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | typeNode 静态工厂 |
| 特性编号 | Func-04-06-07-Feat-03 |
| 所属 Epic | 自定义节点能力 / TypedFrameNode |
| 优先级 | P1 |
| 目标版本 | API 23（静态基线）；文本输入 accessor @since 24；滚动容器 @since 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂（L2，40 组件） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | createXxxNode + XxxFrameNode 抽象类 + type 别名 | @since 23 static |
| ADDED | getXxxAttribute/getXxxEvent/bindXxxController | @since 23/24/26 |
| ADDED | options?: FrameNodeOptions 参数 | @since 26.0.0 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/07-typed-frame-node/design.md` | Baselined |
| SDK 静态 | `interface/sdk-js/api/arkui/FrameNode.static.d.ets` | — |

## 用户故事

### US-1: 静态命名工厂创建
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `typeNode.createXxxNode(context, options?)` THEN 返回类型化 XxxFrameNode 实例 | 正常 |
| AC-1.2 | WHEN options?: FrameNodeOptions（@since 26.0.0）THEN 配置创建选项 | 边界 |
| AC-1.3 | WHEN XComponent THEN 拆 3 函数：createXComponentNodeDefault/WithOptions/WithNativeParameters | 边界 |

### US-2: 静态 accessor
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `getXxxAttribute(node)` THEN 返回属性句柄（@since 23 基线/24 文本输入/26 滚动容器） | 正常 |
| AC-2.2 | WHEN `getXxxEvent(node)`（Scroll/List/Grid/WaterFlow）THEN 返回事件句柄 | 正常 |
| AC-2.3 | WHEN `bindXxxController(node, controller)` THEN 绑定控制器 | 正常 |

### US-3: 抽象类与类型别名
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 定义 abstract class XxxFrameNode extends TypedFrameNode\<XxxAttribute\> THEN 提供 abstract initialize | 正常 |
| AC-3.2 | WHEN `type Xxx = XxxFrameNode` THEN 类型别名 | 正常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.3 | R-1,R-2,R-3 | 单测 | FrameNode.static.d.ets createXxxNode |
| AC-2.1..2.3 | R-4,R-5,R-6 | 单测 | FrameNode.static.d.ets getXxxAttribute 等 |
| AC-3.1..3.2 | R-7,R-8 | 单测 | FrameNode.static.d.ets XxxFrameNode |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | createXxxNode(context, options?) | 返回类型化 XxxFrameNode | 40 组件 | AC-1.1 |
| R-2 | 边界 | options?: FrameNodeOptions | 配置创建选项 | @since 26.0.0 | AC-1.2 |
| R-3 | 边界 | XComponent 3 函数 | Default/WithOptions/WithNativeParameters | — | AC-1.3 |
| R-4 | 行为 | getXxxAttribute(node) | 返回属性句柄 | @since 23 基线/24 文本输入/26 滚动容器 | AC-2.1 |
| R-5 | 行为 | getXxxEvent(node) | 返回事件句柄 | Scroll/List/Grid/WaterFlow @since 26 | AC-2.2 |
| R-6 | 行为 | bindXxxController(node, controller) | 绑定控制器 | @since 23 基线/24 文本输入/26 滚动容器 | AC-2.3 |
| R-7 | 行为 | abstract XxxFrameNode extends TypedFrameNode | 提供 abstract initialize | @since 23 | AC-3.1 |
| R-8 | 行为 | type Xxx = XxxFrameNode | 类型别名 | @since 23 | AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-3 创建 | 单测 | 命名工厂、options、XComponent 3 函数 |
| VM-2 | R-4..R-6 accessor | 单测 | 版本分波 |
| VM-3 | R-7..R-8 抽象类 | 单测 | initialize、别名 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| typeNode.createXxxNode(context, options?) | Public | UIContext, FrameNodeOptions? | XxxFrameNode | — | 静态创建 | AC-1 |
| typeNode.getXxxAttribute(node) | Public | FrameNode | XxxAttribute\|undefined | — | 静态属性 | AC-2 |
| typeNode.getXxxEvent(node) | Public | FrameNode | XxxEvent\|undefined | — | 静态事件 | AC-2 |
| typeNode.bindXxxController(node, controller) | Public | FrameNode, Controller | void | — | 静态绑定 | AC-2 |
| XxxFrameNode abstract class | Public | — | — | — | 类型化基类 | AC-3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**typeNode 静态工厂**

| 属性 | 值 |
|------|-----|
| 函数签名 | `createXxxNode(context, options?): Xxx`; `getXxxAttribute(node): XxxAttribute\|undefined`; `getXxxEvent(node): XxxEvent\|undefined`; `bindXxxController(node, controller): void` |
| 返回值 | Xxx / Attribute\|undefined / Event\|undefined / void |
| 开放范围 | Public（@noninterop） |
| 错误码 | — |
| 关联 AC | AC-1,2,3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | createXxxNode | 返回类型化实例 | AC-1.1 |
| 2 | options @since 26 | 配置选项 | AC-1.2 |
| 3 | getXxxAttribute | 返回属性（版本分波） | AC-2.1 |
| 4 | abstract XxxFrameNode | 提供 initialize | AC-3.1 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** createXxxNode/XxxFrameNode/type 别名 @since 23；文本输入 accessor @since 24；滚动容器 accessor + options @since 26.0.0。
- **API 版本号策略:** @since 23 基线；24/26 分波。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| accessor 版本分波复杂 | 23 基线/24 文本输入/26 滚动容器 | FrameNode.static.d.ets |
| XComponent 3 函数 | Default/WithOptions/WithNativeParameters | FrameNode.static.d.ets |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 命名函数（非重载） | 静态用 createXxxNode 命名 | AC-1.1 |
| abstract initialize | XxxFrameNode 提供 | AC-3.1 |
| 版本分波 | accessor 23/24/26 | AC-2.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 编译期类型安全 | 单测 | FrameNode.static.d.ets |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | 23/24/26 分波 | AC-2 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（静态工厂；动态 Feat-02；矩阵 Feat-04）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode.static.d.ets typeNode createXxxNode/getXxxAttribute/getXxxEvent/bindXxxController 与 XxxFrameNode abstract"
```
