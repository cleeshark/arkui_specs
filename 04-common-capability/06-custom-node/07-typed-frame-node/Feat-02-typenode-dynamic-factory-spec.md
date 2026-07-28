# 特性规格

> Func-04-06-07-Feat-02 typeNode 动态工厂：固化 createNode/getAttribute/getEvent/bindController（string-literal 重载）。主角 ArkTS typeNode。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | typeNode 动态工厂 |
| 特性编号 | Func-04-06-07-Feat-02 |
| 所属 Epic | 自定义节点能力 / TypedFrameNode |
| 优先级 | P1 |
| 目标版本 | API 12（createNode）；getEvent @since 19；getAttribute @since 20；静态 @since 23-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂（L2，40 组件） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | createNode（string-literal 重载，40 组件） | API 12/14/18 |
| ADDED | getAttribute | API 20 |
| ADDED | getEvent（Scroll/List/WaterFlow/Grid） | API 19 |
| ADDED | bindController | API 15(Scroll)/20 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/07-typed-frame-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/FrameNode.d.ts` | — |

## 用户故事

### US-1: 创建类型化节点
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `typeNode.createNode(context, 'X')` THEN 经 __creatorMap__ 返回类型化 TypedFrameNode 实例 | 正常 |
| AC-1.2 | WHEN XComponent THEN 支持 3 重载（bare/options: XComponentOptions/parameters: NativeXComponentParameters） | 边界 |

### US-2: 获取属性/事件/控制器
| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `getAttribute(node, 'X')` 且 nodeType 匹配 + 跨语言检查通过 THEN 经 __attributeMap__ 返回属性句柄 | 正常 |
| AC-2.2 | WHEN nodeType 不匹配 THEN 返回 undefined | 异常 |
| AC-2.3 | WHEN `getEvent(node, 'X')`（Scroll/List/WaterFlow/Grid）THEN 经 __eventMap__ 返回事件句柄 | 正常 |
| AC-2.4 | WHEN `bindController(node, controller, 'X')` THEN 经 __bindControllerCallbackMap__ 绑定控制器 | 正常 |
| AC-2.5 | WHEN bindController 非法 node/type/controller THEN 抛 401/100023；非 scrollable 跨语言失败抛 100021 | 异常 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.2 | R-1,R-2 | 单测 | frame_node.ts typeNode.createNode @2016 |
| AC-2.1..2.5 | R-3,R-4,R-5,R-6,R-7 | 单测 | frame_node.ts getAttribute/getEvent/bindController |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | createNode(context, 'X') | 经 __creatorMap__ 返回类型化实例 | 40 组件 | AC-1.1 |
| R-2 | 边界 | XComponent 3 重载 | bare/XComponentOptions/NativeXComponentParameters | @since 12/19 | AC-1.2 |
| R-3 | 行为 | getAttribute(node, 'X') 匹配+跨语言通过 | 经 __attributeMap__ 返回属性句柄 | @since 20 | AC-2.1 |
| R-4 | 异常 | nodeType 不匹配 | 返回 undefined | — | AC-2.2 |
| R-5 | 行为 | getEvent(node, 'X')（Scroll/List/WaterFlow/Grid） | 经 __eventMap__ 返回事件句柄 | @since 19 | AC-2.3 |
| R-6 | 行为 | bindController(node, controller, 'X') | 经 __bindControllerCallbackMap__ 绑定 | @since 15(Scroll)/20 | AC-2.4 |
| R-7 | 异常 | bindController 非法 | 抛 401/100023；非 scrollable 跨语言失败抛 100021 | — | AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-2 createNode | 单测 | creatorMap、XComponent 重载 |
| VM-2 | R-3..R-7 accessor | 单测 | 匹配校验、undefined、错误码 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| typeNode.createNode(context, nodeType, options?) | Public | UIContext, string-literal | TypedFrameNode | — | 创建类型化节点 | AC-1 |
| typeNode.getAttribute(node, nodeType) | Public | FrameNode, string-literal | Attribute\|undefined | — | 获取属性 | AC-2 |
| typeNode.getEvent(node, nodeType) | Public | FrameNode, string-literal | Event\|undefined | — | 获取事件 | AC-2 |
| typeNode.bindController(node, controller, nodeType) | Public | FrameNode, Controller, string-literal | void | 401,100021,100023 | 绑定控制器 | AC-2 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**typeNode 动态工厂**

| 属性 | 值 |
|------|-----|
| 函数签名 | `createNode(context, nodeType, options?): TypedFrameNode`; `getAttribute(node, nodeType): Attribute\|undefined`; `getEvent(node, nodeType): Event\|undefined`; `bindController(node, controller, nodeType): void` |
| 返回值 | TypedFrameNode / Attribute\|undefined / Event\|undefined / void |
| 开放范围 | Public（@noninterop） |
| 错误码 | 401/100021/100023（bindController） |
| 关联 AC | AC-1,2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | createNode('X') | 返回类型化实例 | AC-1.1 |
| 2 | XComponent 3 重载 | bare/options/parameters | AC-1.2 |
| 3 | getAttribute 匹配 | 返回属性句柄 | AC-2.1 |
| 4 | nodeType 不匹配 | undefined | AC-2.2 |
| 5 | getEvent(Scroll 等) | 返回事件句柄 | AC-2.3 |
| 6 | bindController | 绑定 | AC-2.4 |
| 7 | bindController 非法 | 401/100023/100021 | AC-2.5 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** createNode @since 12/14/18；getEvent @since 19；getAttribute @since 20；bindController @since 15(Scroll)/20。
- **API 版本号策略:** 逐 API @since；typeNode @noninterop。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| accessor 纯 TS 无独立 C++ bridge | 经 dispatch map + 各组件 native modifier | frame_node.ts |
| bindController 错误码多样 | 401/100023/100021 | frame_node.ts |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| string-literal 重载 | 40 组件 nodeType 字面量 | AC-1.1 |
| accessor 纯 TS | dispatch map + native modifier | AC-2.1,2.3,2.4 |
| 跨语言检查 | getAttribute/bindController 需通过 | AC-2.1,2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | dispatch map 查找 | 单测 | frame_node.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | createNode(12/14/18)/accessor(19/20) 演进 | AC-1,2 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（动态工厂；静态工厂 Feat-03；矩阵 Feat-04）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "frame_node.ts typeNode class createNode/getAttribute/getEvent/bindController dispatch map 与错误码"
```
