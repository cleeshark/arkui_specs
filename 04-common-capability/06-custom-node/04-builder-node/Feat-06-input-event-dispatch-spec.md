# 特性规格

> Func-04-06-04-Feat-06 BuilderNode 输入事件分发：固化 postTouchEvent/postInputEvent/postInputEventWithStrategy 行为。主角 ArkTS BuilderNode。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | BuilderNode 输入事件分发 |
| 特性编号 | Func-04-06-04-Feat-06 |
| 所属 Epic | 自定义节点能力 / BuilderNode |
| 优先级 | P2 |
| 目标版本 | API 11（postTouchEvent 起始）；postInputEvent API 20；postInputEventWithStrategy API 24 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | postTouchEvent | API 11 |
| ADDED | postInputEvent + InputEventType | API 20 |
| ADDED | postInputEventWithStrategy + CompetitionStrategy | API 24 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/04-builder-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/BuilderNode.d.ts` / `.static.d.ets` | — |

## 用户故事

### US-1: 触摸事件分发
**作为** 应用开发者，**我想要** 向 BuilderNode 的 FrameNode 分发触摸事件，
**以便** 调整节点树或事件流。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `postTouchEvent(event)` THEN 将事件分发至 FrameNode；坐标 px，转换到父坐标系 | 正常 |
| AC-1.2 | WHEN 同一 timestamp 多次调用 THEN 仅第一次有效 | 边界 |
| AC-1.3 | WHEN UIExtensionComponent THEN PostTouchEventToFrameNode（node_common_modifier.cpp:9421-9455）无 UIExtensionComponent 类型检查，事件照常 post；若 UIExtensionComponent 无组件响应 → 返回 ARKUI_ERROR_CODE_POST_CLONED_NO_COMPONENT_HIT_TO_RESPOND_TO_THE_EVENT。SDK 文档（BuilderNode.d.ts）注明事件分发不适用，但代码无类型拦截 | 边界 |
| AC-1.4 | WHEN 事件被消费 THEN 返回 true | 正常 |

### US-2: 输入事件分发
**作为** 应用开发者，**我想要** 分发触摸/鼠标/轴事件，
**以便** 调整节点树或事件流。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `postInputEvent(event)` THEN 分发事件；坐标相对窗口坐标系 | 正常 |
| AC-2.2 | WHEN 鼠标左键 THEN 自动转换为触摸事件 | 边界 |
| AC-2.3 | WHEN 单个事件多次转发 THEN 避免（与 WithStrategy 区分） | 边界 |

### US-3: 竞争策略分发
**作为** 应用开发者，**我想要** 用竞争策略多次转发同一事件，
**以便** 实现该能力。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `postInputEventWithStrategy(event, strategy?)` THEN 允许同一事件多次转发 | 正常 |
| AC-3.2 | WHEN 省略 strategy THEN 用默认竞争策略 | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.4 | R-1,R-2,R-3,R-4 | 单测 | builder_node.ts postTouchEvent |
| AC-2.1..2.3 | R-5,R-6,R-7 | 单测 | builder_node.ts postInputEvent |
| AC-3.1..3.2 | R-8,R-9 | 单测 | builder_node.ts postInputEventWithStrategy |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | postTouchEvent(event) | 分发至 FrameNode；px 坐标转父系 | — | AC-1.1 |
| R-2 | 边界 | 同 timestamp 多次 | 仅第一次有效 | — | AC-1.2 |
| R-3 | 边界 | UIExtensionComponent | 无类型检查；PostEvent 失败→返回 ARKUI_ERROR_CODE_POST_CLONED_NO_COMPONENT_HIT_TO_RESPOND_TO_THE_EVENT | SDK 文档注明不适用，代码无拦截 | AC-1.3 |
| R-4 | 行为 | 事件被消费 | 返回 true | — | AC-1.4 |
| R-5 | 行为 | postInputEvent(event) | 分发事件；窗口坐标系 | @since 20 | AC-2.1 |
| R-6 | 边界 | 鼠标左键 | 自动转触摸 | — | AC-2.2 |
| R-7 | 边界 | 单事件多次转发 | 避免（用 WithStrategy） | — | AC-2.3 |
| R-8 | 行为 | postInputEventWithStrategy(event, strategy?) | 允许同一事件多次转发 | @since 24 | AC-3.1 |
| R-9 | 边界 | 省略 strategy | 用默认竞争策略 | — | AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-4 postTouchEvent | 单测 | px 转父系、timestamp 一次、返 boolean |
| VM-2 | R-5..R-7 postInputEvent | 单测 | 窗口坐标、鼠标转触摸 |
| VM-3 | R-8..R-9 WithStrategy | 单测 | 多次转发、默认策略 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| postTouchEvent(event) | Public | TouchEvent | boolean | — | 触摸分发 | AC-1 |
| postInputEvent(event) | Public | InputEventType | boolean | — | 输入分发 | AC-2 |
| postInputEventWithStrategy(event, strategy?) | Public | InputEventType, CompetitionStrategy? | boolean | — | 竞争策略分发 | AC-3 |
| InputEventType | Public | TouchEvent \| MouseEvent \| AxisEvent | — | — | 输入事件类型 | AC-2,3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**postTouchEvent / postInputEvent / postInputEventWithStrategy**

| 属性 | 值 |
|------|-----|
| 函数签名 | `postTouchEvent(event: TouchEvent): boolean`; `postInputEvent(event: InputEventType): boolean`; `postInputEventWithStrategy(event: InputEventType, competitionStrategy?: CompetitionStrategy): boolean` |
| 返回值 | boolean |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1,2,3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | postTouchEvent | px 转父系，返是否消费 | AC-1.1,1.4 |
| 2 | 同 timestamp 多次 | 仅第一次 | AC-1.2 |
| 3 | UIExtensionComponent | 无类型检查；无组件响应→返回错误码 | AC-1.3 |
| 4 | postInputEvent 鼠标左键 | 自动转触摸 | AC-2.2 |
| 5 | WithStrategy | 多次转发 | AC-3.1 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** postTouchEvent API 11；postInputEvent/InputEventType API 20（静态 @since 24-26）；postInputEventWithStrategy API 24。
- **API 版本号策略:** 逐 API @since；InputEventType 动态@20/静态@24。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| UIExtensionComponent 无类型拦截 | 事件分发可能无组件响应→返回错误码 | BuilderNode.d.ts |
| postInputEvent 动态@20/静态@26 版本差 | 跨范式版本差异 | .d.ts/.static.d.ets |
| 同 timestamp 仅一次 | postTouchEvent 限制 | BuilderNode.d.ts |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 坐标系差异 | postTouchEvent 用 px 转父系；postInputEvent 用窗口坐标 | AC-1.1,2.1 |
| timestamp 唯一 | postTouchEvent 同 timestamp 仅一次 | AC-1.2 |
| instanceId 同步 | 分发前 syncInstanceId | AC-1.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | 返是否消费 | 单测 | builder_node.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | postInputEvent(20)/WithStrategy(24) 演进 | AC-2,3 |

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（输入事件；不含冻结 Feat-07）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "builder_node.ts postTouchEvent/postInputEvent instanceId 同步与坐标转换"
  - repo: "openharmony/arkui_ace_engine"
    query: "BuilderNode.d.ts InputEventType 与 CompetitionStrategy 同事件多次转发"
```
