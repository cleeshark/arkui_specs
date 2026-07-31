# 特性规格

> Func-04-17-01-Feat-02 UIExtensionProxy 通信机制：固化 UIExtensionProxy 的 send/sendSync/on/off 双向通信及 ModalUIExtensionProxy。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UIExtensionProxy 通信机制 |
| 特性编号 | Func-04-17-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 10+；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | UIExtensionProxy 双向通信 | 补录 send/sendSync/on/off 方法 |
| ADDED | ModalUIExtensionProxy | 补录 inner API 的 SendData 方法 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/17-embedded-display/01-ui-extension/design.md` | Baselined |

---

## 用户故事

### US-1: 发送数据到嵌入 UI

**作为** 应用开发者,
**我想要** 通过 `proxy.send(data)` 向嵌入 UI 发送数据,
**以便** 实现宿主与嵌入 UI 之间的数据同步。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `proxy.send(data)` 发送数据 THEN 异步发送到 UIExtensionAbility，不阻塞当前线程 | 正常 |
| AC-1.2 | WHEN 调用 `proxy.sendSync(data)` 发送数据 THEN 同步发送到 UIExtensionAbility，等待返回结果 | 正常 |

### US-2: 注册数据接收回调

**作为** 应用开发者,
**我想要** 通过 `proxy.on(type, callback)` 注册回调,
**以便** 接收来自嵌入 UI 的数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `proxy.on("sync", callback)` THEN 注册同步数据接收回调 | 正常 |
| AC-2.2 | WHEN 调用 `proxy.on("async", callback)` THEN 注册异步数据接收回调 | 正常 |
| AC-2.3 | WHEN 调用 `proxy.off(type, callback?)` THEN 取消注册对应类型的回调 | 正常 |

### US-3: ModalUIExtensionProxy 内部通信

**作为** 框架内部,
**我想要** 通过 `ModalUIExtensionProxy::SendData(params)` 发送实时数据,
**以便** 支持 Modal 模式下的数据通信。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `ModalUIExtensionProxy::SendData(params)` THEN 发送实时数据到 UIExtensionAbility | 正常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 单元测试 | `ui_extension_proxy.cpp` |
| AC-1.2 | R-1 | 单元测试 | 同上 |
| AC-2.1 | R-2 | 单元测试 | `ui_extension_proxy.cpp` |
| AC-2.2 | R-2 | 单元测试 | 同上 |
| AC-2.3 | R-2 | 单元测试 | 同上 |
| AC-3.1 | R-3 | 单元测试 | `modal_ui_extension_proxy_impl.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 调用 `proxy.send(data)` 或 `proxy.sendSync(data)` | send 异步发送，不阻塞；sendSync 同步发送，等待结果 | sendSync 可能阻塞 UI 线程，需谨慎使用 | AC-1.1, AC-1.2 |
| R-2 | 行为 | 调用 `proxy.on(type, callback)` 或 `proxy.off(type)` | 注册/取消注册 "sync" 或 "async" 类型的回调 | 回调在对应类型数据到达时触发 | AC-2.1, AC-2.2, AC-2.3 |
| R-3 | 行为 | 调用 `ModalUIExtensionProxy::SendData(params)` | 发送实时数据到 UIExtensionAbility | Inner API，非公开接口 | AC-3.1 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.2 | 单元测试 | send/sendSync 异步与同步差异 |
| VM-2 | AC-2.1 ~ AC-2.3 | 单元测试 | on/off 回调注册与取消 |
| VM-3 | AC-3.1 | 单元测试 | ModalUIExtensionProxy |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

### UIExtensionProxy

| 方法 | 签名 | 说明 |
|------|------|------|
| send | `send(data: Object): void` | 异步发送数据 |
| sendSync | `sendSync(data: Object): Object` | 同步发送数据，返回结果 |
| on | `on(type: string, callback: Function): void` | 注册回调（type: "sync"/"async"） |
| off | `off(type: string, callback?: Function): void` | 取消注册回调 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** API 10

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 性能 | sendSync 需注意避免 UI 线程阻塞 | 代码审查 |

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
    query: "UIExtensionProxy 中 SendData 和 SendDataSync 的 SessionWrapper 调用链"
```