# 特性规格

> Func-04-17-01-Feat-03 安全隔离跨进程嵌入显示：固化 SecurityUIExtensionComponent 的安全跨进程 Session 建立、安全代理通信和 PreviewUIExtension 预览机制。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 安全隔离跨进程嵌入显示 |
| 特性编号 | Func-04-17-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 10+；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 安全跨进程 Session 机制 | 补录 SecurityUIExtensionComponent 的安全 Session 建立（SessionType=3）和安全会话包装 |
| ADDED | 安全代理通信 | 补录 SecurityUIExtensionProxy 的跨进程安全数据通道 |
| ADDED | 预览嵌入显示机制 | 补录 PreviewUIExtension 的预览模式跨进程连接（SessionType=6） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/17-embedded-display/01-ui-extension/design.md` | Baselined |

---

## 用户故事

### US-1: 安全跨进程 Session 建立

**作为** 框架,
**我想要** 通过 `SecurityUIExtensionComponent` 建立安全隔离的跨进程嵌入显示连接,
**以便** 在安全敏感场景下嵌入远程 UI 时保证进程隔离。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 宿主调用 `SecurityUIExtensionComponent(want)` THEN 框架创建 `SecurityUIExtensionPattern`，SessionType 为 `SECURITY_UI_EXTENSION_ABILITY` (3)，通过 `SecuritySessionWrapperImpl` 建立安全 IPC 通道 | 正常 |
| AC-1.2 | WHEN 安全 Session 建立后 THEN 与普通 UIExtensionComponent 相比，额外进行安全校验（如调用者身份验证） | 正常 |
| AC-1.3 | WHEN 安全 Session 创建失败 THEN 触发 `onError` 回调，不暴露安全敏感信息 | 异常 |

### US-2: 安全跨进程生命周期与通信

**作为** 宿主进程,
**我想要** 通过安全代理与远程 Ability 通信,
**以便** 在安全隔离的前提下完成跨进程数据交换。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 安全 Session 就绪 THEN `onRemoteReady(proxy)` 触发，传入 `SecurityUIExtensionProxy` 实例 | 正常 |
| AC-2.2 | WHEN 宿主调用 `SecurityUIExtensionProxy.send(data)` THEN 数据通过安全 IPC 通道异步发送到远程安全 Ability | 正常 |
| AC-2.3 | WHEN 宿主调用 `SecurityUIExtensionProxy.sendSync(data)` THEN 数据通过安全 IPC 通道同步发送，等待返回 | 正常 |
| AC-2.4 | WHEN 远程安全 Ability 终止或异常 THEN `onTerminated` 或 `onError` 触发，宿主可感知安全连接断开 | 异常 |

### US-3: 预览嵌入显示机制

**作为** 预览场景,
**我想要** 通过 `PreviewUIExtension` 建立轻量级的跨进程预览连接,
**以便** 在预览模式下快速展示嵌入 UI。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `PreviewUIExtension(want)` THEN 创建 `PreviewUIExtensionPattern`，SessionType 为 `PREVIEW_UI_EXTENSION_ABILITY` (6)，使用 `PreviewSessionWrapperImpl` | 正常 |
| AC-3.2 | WHEN 预览连接发生错误 THEN `onError(code, name, message)` 触发 | 异常 |
| AC-3.3 | WHEN PreviewUIExtension 与 SecurityUIExtensionComponent 对比 THEN 预览模式仅支持 onError 回调，不支持完整的生命周期事件和 Proxy 通信 | 边界 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 集成测试 | `security_ui_extension_pattern.cpp` |
| AC-1.2 | R-1 | 集成测试 | 安全校验逻辑 |
| AC-1.3 | R-1 | 集成测试 | onError |
| AC-2.1 | R-2 | 集成测试 | SecurityUIExtensionProxy |
| AC-2.2 | R-2 | 集成测试 | 安全 IPC send |
| AC-2.3 | R-2 | 集成测试 | 安全 IPC sendSync |
| AC-2.4 | R-2 | 集成测试 | 安全连接断开 |
| AC-3.1 | R-3 | 集成测试 | `preview_ui_extension_pattern.cpp` |
| AC-3.2 | R-3 | 集成测试 | onError |
| AC-3.3 | R-3 | 代码审查 | 功能子集 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 宿主创建 `SecurityUIExtensionComponent` 节点 | 创建 `SecurityUIExtensionPattern`，通过 `SecuritySessionWrapperImpl` 建立安全 IPC 通道（SessionType=3），额外执行安全校验 | 安全校验失败时触发 onError，不暴露敏感信息；与普通 UIExtensionComponent 共享相同的生命周期事件集 | AC-1.1 ~ AC-1.3 |
| R-2 | 行为 | 宿主通过 `SecurityUIExtensionProxy` 通信 | 使用安全 IPC 通道进行 send/sendSync/on/off 操作，与 UIExtensionProxy 通信机制一致，但底层使用 `SecuritySessionWrapperImpl` | 安全通道的加密和认证由系统 IPC 层保证 | AC-2.1 ~ AC-2.4 |
| R-3 | 行为 | 预览场景创建 `PreviewUIExtension` | 创建 `PreviewUIExtensionPattern`，使用 `PreviewSessionWrapperImpl`（SessionType=6），仅支持 onError 回调 | 功能子集：不支持完整生命周期事件和 Proxy 通信 | AC-3.1 ~ AC-3.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.3 | 集成测试 | 安全 Session 建立与安全校验 |
| VM-2 | AC-2.1 ~ AC-2.4 | 集成测试 | 安全代理跨进程通信 |
| VM-3 | AC-3.1 ~ AC-3.3 | 集成测试 | 预览模式与安全模式的差异 |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

### 跨进程嵌入显示子类型对比

| 机制 | SessionType | SessionWrapper | 安全校验 | 生命周期事件 | Proxy 通信 |
|------|------------|---------------|---------|-------------|-----------|
| UIExtensionComponent | 1 (UI_EXTENSION_ABILITY) | SessionWrapperImpl | 无 | 7 个事件 | UIExtensionProxy |
| SecurityUIExtensionComponent | 3 (SECURITY_UI_EXTENSION_ABILITY) | SecuritySessionWrapperImpl | 是 | 6 个事件 | SecurityUIExtensionProxy |
| PreviewUIExtension | 6 (PREVIEW_UI_EXTENSION_ABILITY) | PreviewSessionWrapperImpl | 否 | 仅 onError | 无 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** Dynamic API 10；Static API 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| 安全校验由框架层执行 | 安全 Session 的加密和认证由系统 IPC 层保证，框架层进行身份验证 | AC-1.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 安全 | 安全校验失败时不泄露敏感信息 | 集成测试 |

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
    query: "SecuritySessionWrapperImpl 与 SessionWrapperImpl 的安全校验差异"
  - repo: "openharmony/arkui_ace_engine"
    query: "PreviewSessionWrapperImpl 的功能限制和与安全模式的差异"
```