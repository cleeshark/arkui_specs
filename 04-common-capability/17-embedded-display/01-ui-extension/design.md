# 架构设计

> 嵌入显示能力-UIExtension 功能域的架构设计文档，补录已有实现。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-04-17-01 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 无 |
| 目标 Feature | Feat-01 UIExtensionComponent 创建与事件, Feat-02 UIExtensionProxy 通信机制, Feat-03 SecurityUIExtensionComponent, Feat-04 DynamicComponent |
| 复杂度 | 复杂 |
| 目标版本 | Dynamic API 10+；Static 统一为 API 23 |
| Owner | ArkUI SIG |
| 状态 | Baselined（已有实现补录） |

## 需求基线

| 项 | 内容 |
|----|------|
| 问题陈述 | 需要在 ArkUI 组件树中嵌入其他 Ability 的 UI 内容，支持双向通信和生命周期管理 |
| 核心目标 | 提供 UIExtensionComponent / SecurityUIExtensionComponent / DynamicComponent 三种嵌入组件，支持 UIExtensionProxy 双向通信 |
| P0 AC | 正确创建 UIExtensionComponent 并嵌入远程 UI；onRemoteReady 回调正确触发；Proxy send/sendSync 通信正常 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 模块 | 当前职责 | 本 Feature 影响 |
|------|------|----------|-----------------|
| ace_engine | `frameworks/core/components_ng/pattern/ui_extension/` | 核心 Pattern 层（ui_extension_pattern, security_ui_extension_pattern, dynamic_pattern, isolated_pattern） | 核心实现 |
| ace_engine | `frameworks/core/components_ng/pattern/ui_extension/ui_extension_model.h/cpp` | 抽象模型接口 + NG 实现 | API 接口 |
| ace_engine | `frameworks/bridge/declarative_frontend/jsview/js_ui_extension.h/cpp` | JS 桥接（UIExtension/SecurityUIExtension/PreviewUIExtension） | 输入校验 |
| ace_engine | `frameworks/core/components_ng/pattern/ui_extension/session_wrapper.h` | SessionWrapper 抽象 + SessionType 枚举 | 会话管理 |
| ace_engine | `frameworks/core/components_ng/pattern/ui_extension/ui_extension_proxy.h/cpp` | UIExtensionProxy 通信 | 双向通信 |
| ace_engine | `adapter/ohos/osal/modal_ui_extension_impl.cpp` | OS 层 ModalUIExtension 创建 | 平台适配 |
| interface_sdk-js | API 类型定义 | 类型定义 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| JS Bridge | `js_ui_extension` / `js_security_ui_extension` | 解析 ArkTS 调用，创建 FrameNode + Proxy | 存量分析 |
| Model 层 | `ui_extension_model_ng` | 路由到对应 Pattern 子类 | 存量分析 |
| Pattern 层 | `ui_extension_pattern` / `security_ui_extension_pattern` / `dynamic_pattern` | 生命周期管理、Session 创建、事件分发 | 存量分析 |
| Session 层 | `session_wrapper_impl` / `security_session_wrapper_impl` | 跨进程会话管理 | 存量分析 |
| Proxy 层 | `ui_extension_proxy` / `security_ui_extension_proxy` | send/sendSync/on/off 双向通信 | 存量分析 |
| Renderer 层 | `dynamic_component_renderer_impl` | DynamicComponent 渲染 | 存量分析 |

### SessionType 枚举

| 值 | 类型 | 对应组件 |
|----|------|---------|
| 0 | EMBEDDED_UI_EXTENSION | 嵌入式 |
| 1 | UI_EXTENSION_ABILITY | UIExtensionComponent |
| 2 | CLOUD_CARD | 云卡片 |
| 3 | SECURITY_UI_EXTENSION_ABILITY | SecurityUIExtensionComponent |
| 4 | DYNAMIC_COMPONENT | DynamicComponent |
| 5 | ISOLATED_COMPONENT | IsolateComponent |
| 6 | PREVIEW_UI_EXTENSION_ABILITY | PreviewUIExtension |

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-LAYERING | 涉及 JS Bridge → Model → Pattern → Session → Proxy 多层调用 | 严格单向调用 | 代码评审 |
| OH-ARCH-IPC-SAF | UIExtension 涉及跨进程通信 | SessionWrapper 管理 IPC 通道 | 集成测试 |
| OH-ARCH-API-LEVEL | 多 API 版本演进 | 按 @since 版本标注 | API 评审 |

## 不涉及项承接

| 维度 | 设计结论 |
|------|----------|
| 性能 | DynamicComponent 约束：每 Worker 最多 4 个 |
| 安全与权限 | SecurityUIExtensionComponent 有额外安全校验 |
| 兼容性 | 声明式 + Static 双范式，部分 API 仅声明式支持 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 影响 |
|---------|------|----------|------|
| ADR-1 | UIExtension 子类型如何路由 | SessionType 枚举 + UIExtensionModelNG 按类型分发 | 统一 Model 接口，多 Pattern 子类 |
| ADR-2 | Proxy 通信模式 | send（异步）+ sendSync（同步）+ on/off（事件注册） | 双向通信 |
| ADR-3 | Placeholder 机制 | 支持 initPlaceholder/rotationPlaceholder/foldToExpandPlaceholder/undefinedPlaceholder | 状态占位 |

## 后续 Task 拆分

| Task ID | 目标 | 受影响文件 | 依赖 |
|---------|------|-----------|------|
| Feat-01 | UIExtensionComponent 创建与事件 | Feat-01-ui-extension-creation-events-spec.md | 无 |
| Feat-02 | UIExtensionProxy 通信机制 | Feat-02-ui-extension-proxy-communication-spec.md | Feat-01 |
| Feat-03 | SecurityUIExtensionComponent | Feat-03-security-ui-extension-spec.md | Feat-01 |
| Feat-04 | DynamicComponent | Feat-04-dynamic-component-spec.md | Feat-01 |

## API 签名、Kit 与权限

| API | 类型 | Kit |
|-----|------|-----|
| `UIExtensionComponent(want, options?)` | System | ArkUI |
| `SecurityUIExtensionComponent(want, options?)` | System | ArkUI |
| `DynamicComponent(options)` | System | ArkUI |
| `UIExtensionProxy.send(data)` | System | ArkUI |
| `UIExtensionProxy.sendSync(data)` | System | ArkUI |

## 构建系统影响

无 — 已有实现。

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| 跨进程通信稳定性 | 架构 | 高 | SessionWrapper 管理重连和超时 | ArkUI SIG |

## 设计审批

- [x] 需求基线已确认
- [x] 调用链层级分析完整
- [x] 适用架构规则已识别
- [x] 关键设计决策有理由和影响说明
- [x] 风险和开放问题有 Owner

**结论:** 通过（已有实现补录）