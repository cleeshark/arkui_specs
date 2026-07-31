# 特性规格

> Func-04-17-01-Feat-03 SecurityUIExtensionComponent：固化 SecurityUIExtensionComponent 和 PreviewUIExtension 的创建、事件和安全代理。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SecurityUIExtensionComponent |
| 特性编号 | Func-04-17-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 10+；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | SecurityUIExtensionComponent 创建与事件 | 补录安全 UI 扩展的 create + 6 个事件 + Proxy |
| ADDED | PreviewUIExtension | 补录预览 UI 扩展的 create + onError |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/17-embedded-display/01-ui-extension/design.md` | Baselined |

---

## 用户故事

### US-1: 创建 SecurityUIExtensionComponent

**作为** 应用开发者,
**我想要** 通过 `SecurityUIExtensionComponent(want, options?)` 嵌入安全 UI,
**以便** 在安全场景下展示其他 Ability 的 UI。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `SecurityUIExtensionComponent(want)` THEN 创建 SecurityUIExtensionPattern，SessionType = SECURITY_UI_EXTENSION_ABILITY (3) | 正常 |
| AC-1.2 | WHEN 设置 `width(value)` / `height(value)` / `backgroundColor(value)` THEN 对应属性生效 | 正常 |

### US-2: 监听安全 UI 事件

**作为** 应用开发者,
**我想要** 通过 SecurityUIExtensionComponent 的事件回调监听状态,
**以便** 响应安全 UI 的生命周期变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 安全 UI 就绪 THEN `onRemoteReady(proxy)` 触发，传入 SecurityUIExtensionProxy | 正常 |
| AC-2.2 | WHEN 安全 UI 发生错误 THEN `onError(code, name, message)` 触发 | 异常 |
| AC-2.3 | WHEN 安全 UI 被终止 THEN `onTerminated(code, want)` 触发 | 正常 |
| AC-2.4 | WHEN 安全 UI 收到数据 THEN `onReceive(data)` 触发 | 正常 |

### US-3: SecurityUIExtensionProxy 通信

**作为** 应用开发者,
**我想要** 通过 SecurityUIExtensionProxy 与安全 UI 通信,
**以便** 实现安全场景下的双向数据交换。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `proxy.send(data)` THEN 异步发送数据到 SecurityUIExtensionAbility | 正常 |
| AC-3.2 | WHEN 调用 `proxy.sendSync(data)` THEN 同步发送数据 | 正常 |
| AC-3.3 | WHEN 调用 `proxy.on(type, callback)` THEN 注册 "sync" 或 "async" 回调 | 正常 |

### US-4: PreviewUIExtension

**作为** 预览场景,
**我想要** 通过 `PreviewUIExtension(want, options?)` 创建预览 UI 扩展,
**以便** 在预览模式下展示 UI。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `PreviewUIExtension(want)` THEN 创建 PreviewUIExtensionPattern，SessionType = PREVIEW_UI_EXTENSION_ABILITY (6) | 正常 |
| AC-4.2 | WHEN 预览 UI 发生错误 THEN `onError(code, name, message)` 触发 | 异常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 单元测试 | `js_security_ui_extension.cpp` |
| AC-1.2 | R-1 | 单元测试 | width/height/backgroundColor |
| AC-2.1 | R-2 | 单元测试 | onRemoteReady |
| AC-2.2 | R-2 | 单元测试 | onError |
| AC-2.3 | R-2 | 单元测试 | onTerminated |
| AC-2.4 | R-2 | 单元测试 | onReceive |
| AC-3.1 | R-3 | 单元测试 | SecurityUIExtensionProxy |
| AC-3.2 | R-3 | 单元测试 | sendSync |
| AC-3.3 | R-3 | 单元测试 | on/off |
| AC-4.1 | R-4 | 单元测试 | PreviewUIExtension |
| AC-4.2 | R-4 | 单元测试 | onError |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 调用 `SecurityUIExtensionComponent(want, options?)` | 创建 SecurityUIExtensionPattern，比 UIExtensionComponent 多安全校验 | SessionType = SECURITY_UI_EXTENSION_ABILITY (3)；支持 width/height/backgroundColor | AC-1.1, AC-1.2 |
| R-2 | 行为 | 安全 UI 生命周期事件 | 触发 onRemoteReady/onReceive/onError/onTerminated/onResult/onRelease/onDrawReady | 与 UIExtensionComponent 事件集相同 | AC-2.1 ~ AC-2.4 |
| R-3 | 行为 | SecurityUIExtensionProxy 通信 | send/sendSync/on/off 与 UIExtensionProxy 行为一致 | 使用 SecuritySessionWrapperImpl | AC-3.1 ~ AC-3.3 |
| R-4 | 行为 | 调用 `PreviewUIExtension(want, options?)` | 创建 PreviewUIExtensionPattern，仅支持 onError 事件 | SessionType = PREVIEW_UI_EXTENSION_ABILITY (6)；功能子集 | AC-4.1, AC-4.2 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.2 | 单元测试 | 安全 UI 创建 |
| VM-2 | AC-2.1 ~ AC-2.4 | 集成测试 | 安全 UI 事件 |
| VM-3 | AC-3.1 ~ AC-3.3 | 单元测试 | SecurityProxy 通信 |
| VM-4 | AC-4.1 ~ AC-4.2 | 单元测试 | PreviewUIExtension |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

| 组件 | SessionType | 事件数 | 特殊属性 |
|------|------------|--------|---------|
| UIExtensionComponent | 1 | 7 | 全部构造选项 |
| SecurityUIExtensionComponent | 3 | 6 | width/height/backgroundColor |
| PreviewUIExtension | 6 | 1 (onError) | width/height |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** API 10

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 安全 | SecurityUIExtensionComponent 有额外安全校验 | 代码审查 |

## 多设备适配声明

无差异。

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "SecurityUIExtensionPattern 与 UIExtensionPattern 的安全校验差异"
```