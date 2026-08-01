# 特性规格

> Func-04-17-01-Feat-02 跨进程双向数据通道：固化 UIExtensionProxy 的跨进程 send/sendSync 数据通道和 on/off 事件注册机制。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 跨进程双向数据通道 |
| 特性编号 | Func-04-17-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 10+；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 跨进程异步数据通道 | 补录 `send()` 通过 IPC 异步发送数据到远程 Ability 的机制 |
| ADDED | 跨进程同步数据通道 | 补录 `sendSync()` 同步发送并等待远程返回的机制 |
| ADDED | 跨进程事件注册 | 补录 `on/off` 注册远程 Ability 回调的机制 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/17-embedded-display/01-ui-extension/design.md` | Baselined |

---

## 用户故事

### US-1: 跨进程异步数据发送

**作为** 宿主进程,
**我想要** 通过 `proxy.send(data)` 异步发送数据到远程 Ability,
**以便** 不阻塞宿主 UI 线程的情况下完成跨进程数据传递。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 宿主调用 `proxy.send(data)` 传入业务数据 THEN 数据通过 `UIExtensionProxy::SendData` → `SessionWrapper::SendData` 经 IPC 通道异步发送到远程 Ability，宿主 UI 线程不阻塞 | 正常 |
| AC-1.2 | WHEN 跨进程 IPC 通道尚未建立（Session 未就绪）THEN `send()` 调用失败，数据不发送 | 异常 |

### US-2: 跨进程同步数据发送

**作为** 宿主进程,
**我想要** 通过 `proxy.sendSync(data)` 同步发送数据并等待远程返回,
**以便** 在需要远程确认的场景下获取返回值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 宿主调用 `proxy.sendSync(data)` THEN 数据通过 IPC 同步发送到远程 Ability，宿主线程阻塞等待远程返回结果后继续执行 | 正常 |
| AC-2.2 | WHEN 远程 Ability 在超时时间内未返回 THEN `sendSync()` 超时返回，宿主线程恢复 | 边界 |

### US-3: 跨进程事件回调注册

**作为** 宿主进程,
**我想要** 通过 `proxy.on(type, callback)` 注册对远程 Ability 数据的监听,
**以便** 在远程 Ability 主动发送数据时接收通知。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 宿主调用 `proxy.on("sync", callback)` THEN 注册同步数据接收回调，远程 Ability 通过 sync 通道发送数据时宿主回调被触发 | 正常 |
| AC-3.2 | WHEN 宿主调用 `proxy.on("async", callback)` THEN 注册异步数据接收回调，远程 Ability 通过 async 通道发送数据时宿主回调被触发 | 正常 |
| AC-3.3 | WHEN 宿主调用 `proxy.off(type, callback?)` THEN 取消注册对应类型的回调，后续远程数据不再触发该回调 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 集成测试 | `ui_extension_proxy.cpp` → `SessionWrapper::SendData` |
| AC-1.2 | R-1 | 集成测试 | Session 未就绪时返回错误 |
| AC-2.1 | R-2 | 集成测试 | `ui_extension_proxy.cpp` → `SendDataSync` |
| AC-2.2 | R-2 | 集成测试 | 超时机制 |
| AC-3.1 | R-3 | 集成测试 | sync 回调注册 |
| AC-3.2 | R-3 | 集成测试 | async 回调注册 |
| AC-3.3 | R-3 | 集成测试 | off 取消注册 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 宿主调用 `proxy.send(data)` 且跨进程 Session 已就绪 | 数据经 `UIExtensionProxy::SendData` → `SessionWrapper::SendData` 通过 IPC 异步发送到远程 Ability，宿主线程不阻塞 | Session 未就绪时发送失败，无崩溃 | AC-1.1, AC-1.2 |
| R-2 | 行为 | 宿主调用 `proxy.sendSync(data)` 且跨进程 Session 已就绪 | 数据经 IPC 同步发送，宿主线程阻塞等待远程返回结果；超时或失败时返回错误 | 同步阻塞可能影响宿主 UI 响应，需谨慎使用；超时由系统 IPC 机制控制 | AC-2.1, AC-2.2 |
| R-3 | 行为 | 宿主调用 `proxy.on(type, callback)` 注册跨进程回调 | 回调注册到 `UIExtensionProxy` 内部，当远程 Ability 通过对应类型（sync/async）发送数据时触发 | 支持 "sync" 和 "async" 两种类型；`off(type)` 取消注册 | AC-3.1, AC-3.2, AC-3.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.2 | 集成测试 | 跨进程异步数据通道：IPC 发送 → 远程接收 → 不阻塞宿主线程 |
| VM-2 | AC-2.1 ~ AC-2.2 | 集成测试 | 跨进程同步数据通道：阻塞等待 → 超时处理 |
| VM-3 | AC-3.1 ~ AC-3.3 | 集成测试 | 跨进程事件注册：sync/async 回调注册与取消 |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

> 本节描述跨进程数据通道的机制接口。

### 跨进程数据通道架构

```
宿主进程                                    远程 Ability 进程
  UIExtensionProxy                           UIExtensionAbility
    ├─ send(data) ──IPC 异步通道──→            onReceive(data)
    ├─ sendSync(data) ──IPC 同步通道──→         onSyncReceive(data) → return result
    ├─ on("sync", cb) ←──IPC 同步通道──         sendSync(data)
    └─ on("async", cb) ←──IPC 异步通道──        send(data)
```

### 通道类型

| 通道 | 方向 | 阻塞 | 适用场景 |
|------|------|------|---------|
| send (异步) | 宿主 → 远程 | 否 | 通知类数据，无需确认 |
| sendSync (同步) | 宿主 → 远程 | 是 | 需远程确认的操作 |
| on("async") | 远程 → 宿主 | 否 | 远程主动推送数据 |
| on("sync") | 远程 → 宿主 | 否 | 远程同步通知 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** Dynamic API 10；Static API 23
- **API 版本号策略:** 以 SDK `.d.ts` 为 API 契约

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| sendSync 阻塞宿主线程 | 同步发送在 IPC 响应返回前阻塞当前线程，不应在主线程长时间等待 | AC-2.1, AC-2.2 |
| 跨进程数据序列化 | 数据通过 IPC 传递需支持序列化，不支持序列化的对象无法传递 | AC-1.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 可靠性 | Sync 超时后宿主线程正常恢复，不产生死锁 | 集成测试 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 |
|------|--------|------|
| IPC/跨进程 | 是 | 本特性即为跨进程通信机制的核心 |

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "UIExtensionProxy 中 SendData 和 SendDataSync 如何通过 SessionWrapper 实现跨进程 IPC 通信"
```