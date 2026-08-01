# 特性规格

> Func-04-17-01-Feat-01 跨进程嵌入显示连接与生命周期：固化 UIExtensionComponent 的跨进程 Session 建立、Want 路由、生命周期同步和 Placeholder 状态机。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 跨进程嵌入显示连接与生命周期 |
| 特性编号 | Func-04-17-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 10+；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 跨进程 Session 建立机制 | 补录 Want 路由 → SessionType 分发 → SessionWrapper 创建流程 |
| ADDED | 跨进程生命周期同步 | 补录 onRemoteReady/onReceive/onRelease/onResult/onError/onTerminated/onDrawReady 的生命周期同步语义 |
| ADDED | Placeholder 状态机 | 补录跨进程初始化期间的 5 种 Placeholder 状态切换 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/17-embedded-display/01-ui-extension/design.md` | Baselined |

---

## 用户故事

### US-1: 跨进程 Session 建立

**作为** 框架,
**我想要** 通过 Want 路由建立与目标 Ability 的跨进程 Session,
**以便** 在宿主进程中嵌入并渲染远程 UI 内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 宿主调用 `UIExtensionComponent(want)` 传入目标 Ability 的 Want THEN 框架通过 `UIExtensionModelNG` 创建 `UIExtensionPattern`，解析 Want 提取 bundleName/abilityName，通过 `SessionWrapperFactory` 创建对应 SessionType 的 `SessionWrapper` 实例 | 正常 |
| AC-1.2 | WHEN SessionType 为 `UI_EXTENSION_ABILITY` (1) THEN 创建 `SessionWrapperImpl`，建立宿主与 UIExtensionAbility 之间的 IPC 通道 | 正常 |
| AC-1.3 | WHEN 构造选项 `isTransferringCaller: true` THEN 跨进程传递调用者身份标识，目标 Ability 可获取调用者信息 | 正常 |
| AC-1.4 | WHEN 构造选项 `isWindowModeFollowHost: true` THEN 嵌入 UI 的窗口模式跟随宿主窗口状态变化 | 正常 |
| AC-1.5 | WHEN 构造选项 `enableDensityDPI: 0` THEN 嵌入 UI 的密度跟随宿主屏幕密度；设为 1 时使用自身密度 | 正常 |

### US-2: 跨进程生命周期同步

**作为** 框架,
**我想要** 通过事件回调将嵌入 UI 的跨进程生命周期状态同步给宿主,
**以便** 宿主感知远程 UI 的创建、通信、异常和销毁。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 跨进程 Session 建立成功且远程 UI 初始化完成 THEN `onRemoteReady(proxy)` 触发，宿主获得 `UIExtensionProxy` 用于后续跨进程通信 | 正常 |
| AC-2.2 | WHEN 远程 Ability 通过 IPC 发送数据 THEN `onReceive(data)` 触发，数据从远程进程传递到宿主进程 | 正常 |
| AC-2.3 | WHEN 远程 Ability 正常返回结果 THEN `onResult(code, want)` 触发，携带跨进程返回码和 Want | 正常 |
| AC-2.4 | WHEN 远程 Ability 被系统终止 THEN `onTerminated(code, want)` 触发，宿主可感知远程进程销毁 | 正常 |
| AC-2.5 | WHEN 远程 Ability 主动释放 Session THEN `onRelease(code)` 触发，IPC 通道关闭 | 正常 |
| AC-2.6 | WHEN 跨进程通信或远程 Ability 发生异常 THEN `onError(code, name, message)` 触发，宿主可进行降级处理 | 异常 |
| AC-2.7 | WHEN 远程 UI 完成首次渲染绘制 THEN `onDrawReady()` 触发，宿主可移除 Placeholder 显示真实内容 | 正常 |

### US-3: Placeholder 状态机

**作为** 框架,
**我想要** 在跨进程嵌入 UI 的不同阶段显示对应的 Placeholder,
**以便** 在远程 UI 未就绪、旋转、折叠等状态期间提供视觉反馈。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 跨进程 Session 正在建立且远程 UI 未初始化 THEN 显示 `initPlaceholder`（PlaceholderType::INIT） | 正常 |
| AC-3.2 | WHEN 设备发生旋转且远程 UI 正在重建 Surface THEN 显示 `rotationPlaceholder`（PlaceholderType::ROTATION） | 正常 |
| AC-3.3 | WHEN 折叠屏设备展开/折叠且远程 UI 正在适配 THEN 显示 `foldToExpandPlaceholder`（PlaceholderType::FOLD_TO_EXPAND） | 正常 |
| AC-3.4 | WHEN 远程 UI 状态未定义（如 Session 异常中断）THEN 显示 `undefinedPlaceholder`（PlaceholderType::UNDEFINED） | 异常 |
| AC-3.5 | WHEN 跨进程初始化失败（Session 创建失败）THEN 不触发 `onRemoteReady`，Placeholder 保持 INIT 状态或进入 UNDEFINED 状态 | 异常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 集成测试 | `ui_extension_model_ng.cpp` → `SessionWrapperFactory` |
| AC-1.2 | R-1 | 集成测试 | `session_wrapper_impl.cpp` |
| AC-1.3 | R-1 | 集成测试 | `isTransferringCaller` |
| AC-1.4 | R-1 | 集成测试 | `isWindowModeFollowHost` |
| AC-1.5 | R-1 | 集成测试 | `enableDensityDPI` |
| AC-2.1 | R-2 | 集成测试 | `ui_extension_pattern.cpp` onRemoteReady |
| AC-2.2 | R-2 | 集成测试 | IPC 数据通道 |
| AC-2.3 | R-2 | 集成测试 | 跨进程返回码 |
| AC-2.4 | R-2 | 集成测试 | 远程进程销毁 |
| AC-2.5 | R-2 | 集成测试 | Session 释放 |
| AC-2.6 | R-2 | 集成测试 | 跨进程异常 |
| AC-2.7 | R-2 | 集成测试 | 首次绘制 |
| AC-3.1 | R-3 | 集成测试 | Placeholder 状态机 |
| AC-3.2 | R-3 | 集成测试 | 旋转状态 |
| AC-3.3 | R-3 | 集成测试 | 折叠屏状态 |
| AC-3.4 | R-3 | 集成测试 | 异常状态 |
| AC-3.5 | R-3 | 集成测试 | 初始化失败 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 宿主进程创建 `UIExtensionComponent` 节点 | 框架通过 Want 解析目标 Ability 标识，根据 `SessionType` 枚举（UI_EXTENSION_ABILITY=1）通过 `SessionWrapperFactory` 创建对应 `SessionWrapper` 实例，建立跨进程 IPC 通道 | 构造选项（isTransferringCaller/enableDensityDPI/isWindowModeFollowHost）在 Session 建立前配置；跨进程通信依赖系统 IPC 能力 | AC-1.1 ~ AC-1.5 |
| R-2 | 行为 | 跨进程 Session 状态变化 | 通过 `UIExtensionHub` 事件回调将远程进程状态同步到宿主进程：onRemoteReady（Session 就绪，获得 Proxy）、onReceive（IPC 数据到达）、onResult（远程返回）、onTerminated（远程进程销毁）、onRelease（Session 释放）、onError（跨进程异常）、onDrawReady（远程渲染完成） | 所有回调均为可选注册，未注册时静默忽略；回调在 UI 线程执行 | AC-2.1 ~ AC-2.7 |
| R-3 | 行为 | 跨进程嵌入 UI 处于非就绪状态 | 根据 `PlaceholderType` 状态机显示对应 Placeholder：INIT（初始化中）→ ROTATION（旋转重建）→ FOLD_TO_EXPAND（折叠适配）→ UNDEFINED（异常）；onDrawReady 触发后移除 Placeholder | 5 种 Placeholder 均为可选配置，未配置时对应状态无视觉反馈 | AC-3.1 ~ AC-3.5 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.5 | 集成测试 | 跨进程 Session 建立：Want 路由 → SessionType 分发 → SessionWrapper 创建 |
| VM-2 | AC-2.1 ~ AC-2.7 | 集成测试 | 跨进程生命周期同步：7 个事件回调的触发时序和跨进程数据传递 |
| VM-3 | AC-3.1 ~ AC-3.5 | 集成测试 | Placeholder 状态机：5 种状态切换与 onDrawReady 的联动 |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

> 本节描述跨进程嵌入显示的机制接口，而非组件属性清单。

### 跨进程连接建立

| 机制环节 | 关键模块 | 说明 |
|----------|---------|------|
| Want 路由 | `UIExtensionModelNG::CreateUIExtensionComponent` | 解析 Want → 提取 bundleName/abilityName |
| SessionType 分发 | `UIExtensionContainerHandler` | 根据 Want 类型路由到对应 SessionType 枚举值 |
| Session 创建 | `SessionWrapperFactory::Create` | 创建对应 SessionWrapper 子类，建立 IPC 通道 |
| 配置注入 | 构造选项 → `UIExtensionPattern` | isTransferringCaller/enableDensityDPI/isWindowModeFollowHost 在 Session 建立前配置 |

### 跨进程生命周期状态机

```
宿主创建 UIExtensionComponent
  → Session 建立中（Placeholder: INIT）
    → 成功 → onRemoteReady(proxy) → 远程渲染中
      → onDrawReady() → 正常显示（Placeholder 移除）
      → onReceive(data) → 处理 IPC 数据
      → onResult(code, want) → 处理返回
      → onError(code, name, msg) → 异常处理
      → onTerminated(code, want) → 远程进程销毁
      → onRelease(code) → Session 关闭
    → 失败 → Placeholder: UNDEFINED / onError
```

### PlaceholderType 状态枚举

| 状态 | 触发条件 | 说明 |
|------|---------|------|
| INIT | Session 建立中，远程 UI 未初始化 | 初始状态，显示 initPlaceholder |
| ROTATION | 设备旋转，远程 Surface 重建中 | 显示 rotationPlaceholder |
| FOLD_TO_EXPAND | 折叠屏展开/折叠，远程 UI 适配中 | 显示 foldToExpandPlaceholder |
| UNDEFINED | Session 异常中断或状态未知 | 显示 undefinedPlaceholder |
| NONE | onDrawReady 已触发 | 移除所有 Placeholder，显示真实内容 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** Dynamic API 10；Static API 23
- **API 版本号策略:** 以 SDK `.d.ts` 为 API 契约，各属性按实际引入版本标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| 跨进程 IPC 依赖系统能力 | Session 建立依赖系统 IPC 通道，系统服务不可用时创建失败 | AC-1.1, AC-1.2 |
| 回调在 UI 线程执行 | 所有生命周期回调在宿主 UI 线程触发，宿主不应在回调中执行长时间阻塞操作 | AC-2.1 ~ AC-2.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 可靠性 | Session 创建失败时触发 onError 或 Placeholder 保持 UNDEFINED，不崩溃 | 集成测试 |
| 性能 | 跨进程 Session 建立时间受系统 IPC 性能影响，非框架可控 | N/A |

## 多设备适配声明

| 设备类型 | 行为差异 | 说明 |
|----------|---------|------|
| 折叠屏 | 使用 foldToExpandPlaceholder | 折叠/展开状态切换时嵌入 UI 需重建 Surface |

## 全局特性影响

| 特性 | 适用？ | 结论 |
|------|--------|------|
| 多窗口/分屏 | 是 | isWindowModeFollowHost 控制嵌入 UI 窗口模式跟随宿主 |
| 版本升级 | 是 | 构造选项随版本演进 |

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "SessionWrapperFactory 如何根据 Want 类型和 SessionType 枚举创建对应的跨进程 Session 实例"
  - repo: "openharmony/arkui_ace_engine"
    query: "UIExtensionPattern 中跨进程生命周期回调的触发时序和 IPC 数据通道"
```