# 特性规格

> Func-04-17-01-Feat-01 UIExtensionComponent 创建与事件：固化 UIExtensionComponent 的创建、构造选项和 7 个事件回调。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UIExtensionComponent 创建与事件 |
| 特性编号 | Func-04-17-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 10+；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | UIExtensionComponent 创建行为 | 补录 create(want, options?) 及构造选项 |
| ADDED | 7 个事件回调 | 补录 onRemoteReady/onReceive/onRelease/onResult/onError/onTerminated/onDrawReady |
| ADDED | 构造选项 | 补录 isTransferringCaller/enableDensityDPI/isWindowModeFollowHost/placeholder |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/17-embedded-display/01-ui-extension/design.md` | Baselined |

---

## 用户故事

### US-1: 创建 UIExtensionComponent

**作为** 应用开发者,
**我想要** 通过 `UIExtensionComponent(want, options?)` 嵌入远程 UI,
**以便** 在当前页面中展示其他 Ability 的 UI 内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `UIExtensionComponent(want, {isTransferringCaller: true})` THEN 创建 UIExtensionPattern，传递 Want 和配置选项 | 正常 |
| AC-1.2 | WHEN 设置 `isWindowModeFollowHost: true` THEN 嵌入 UI 的窗口模式跟随宿主 | 正常 |
| AC-1.3 | WHEN 设置 `enableDensityDPI: 0` THEN 嵌入 UI 跟随宿主密度；设为 1 则不跟随 | 正常 |
| AC-1.4 | WHEN 设置 `placeholder: ComponentContent` THEN 嵌入 UI 未就绪时显示占位内容 | 正常 |
| AC-1.5 | WHEN 设置 `rotationPlaceholder` / `foldToExpandPlaceholder` / `undefinedPlaceholder` THEN 对应状态下显示对应占位 | 正常 |

### US-2: 监听远程就绪事件

**作为** 应用开发者,
**我想要** 通过 `.onRemoteReady()` 获取 UIExtensionProxy,
**以便** 与嵌入的 UI 进行双向通信。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 嵌入 UI 初始化完成 THEN `onRemoteReady(proxy)` 回调被触发，传入 UIExtensionProxy 实例 | 正常 |
| AC-2.2 | WHEN 嵌入 UI 初始化失败 THEN `onRemoteReady` 不触发 | 异常 |

### US-3: 监听生命周期事件

**作为** 应用开发者,
**我想要** 通过生命周期回调监听嵌入 UI 的状态变化,
**以便** 在嵌入 UI 异常时做出响应。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 嵌入 UI 发送数据 THEN `onReceive(data)` 被触发 | 正常 |
| AC-3.2 | WHEN 嵌入 UI 被释放 THEN `onRelease(code)` 被触发，code 为 int32_t | 正常 |
| AC-3.3 | WHEN 嵌入 UI 返回结果 THEN `onResult(code, want)` 被触发 | 正常 |
| AC-3.4 | WHEN 嵌入 UI 发生错误 THEN `onError(code, name, message)` 被触发 | 异常 |
| AC-3.5 | WHEN 嵌入 UI 被终止 THEN `onTerminated(code, want)` 被触发 | 正常 |
| AC-3.6 | WHEN 嵌入 UI 首次绘制完成 THEN `onDrawReady()` 被触发 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 单元测试 | `js_ui_extension.cpp:423` |
| AC-1.2 | R-1 | 单元测试 | `isWindowModeFollowHost` |
| AC-1.3 | R-1 | 单元测试 | `enableDensityDPI` |
| AC-1.4 | R-1 | 单元测试 | Placeholder 机制 |
| AC-1.5 | R-1 | 单元测试 | 多种 Placeholder |
| AC-2.1 | R-2 | 单元测试 | `js_ui_extension.cpp:334` |
| AC-2.2 | R-2 | 单元测试 | 初始化失败 |
| AC-3.1 | R-3 | 单元测试 | `js_ui_extension.cpp:335` |
| AC-3.2 | R-3 | 单元测试 | `js_ui_extension.cpp:336` |
| AC-3.3 | R-3 | 单元测试 | `js_ui_extension.cpp:337` |
| AC-3.4 | R-3 | 单元测试 | `js_ui_extension.cpp:338` |
| AC-3.5 | R-3 | 单元测试 | `js_ui_extension.cpp:339` |
| AC-3.6 | R-3 | 单元测试 | `js_ui_extension.cpp:340` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 调用 `UIExtensionComponent(want, options?)` | 创建 UIExtensionPattern，解析 Want 和配置选项（isTransferringCaller/enableDensityDPI/isWindowModeFollowHost/placeholder/rotationPlaceholder/foldToExpandPlaceholder/undefinedPlaceholder） | SessionType = UI_EXTENSION_ABILITY (1) | AC-1.1 ~ AC-1.5 |
| R-2 | 行为 | 嵌入 UI 初始化完成 | `onRemoteReady(proxy)` 回调触发，传入 UIExtensionProxy 实例 | 初始化失败时不触发 | AC-2.1, AC-2.2 |
| R-3 | 行为 | 嵌入 UI 生命周期事件触发 | 对应回调被调用：onReceive(Object)/onRelease(int32_t)/onResult(int32_t, Want)/onError(int32_t, string, string)/onTerminated(int32_t, Want)/onDrawReady() | 回调均为可选注册 | AC-3.1 ~ AC-3.6 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.5 | 单元测试 | 创建 + 构造选项 |
| VM-2 | AC-2.1 ~ AC-2.2 | 集成测试 | onRemoteReady |
| VM-3 | AC-3.1 ~ AC-3.6 | 集成测试 | 7 个事件回调 |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

### UIExtensionComponent 构造选项

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| want | Want | 是 | 目标 Ability 的 Want |
| options.isTransferringCaller | boolean | 否 | 传递调用者身份 |
| options.enableDensityDPI | number | 否 | 0=跟随宿主密度, 1=不跟随 |
| options.isWindowModeFollowHost | boolean | 否 | 跟随宿主窗口模式 |
| options.placeholder | ComponentContent | 否 | 初始占位内容 |
| options.rotationPlaceholder | ComponentContent | 否 | 旋转占位 |
| options.foldToExpandPlaceholder | ComponentContent | 否 | 折叠展开占位 |
| options.undefinedPlaceholder | ComponentContent | 否 | 未定义状态占位 |

### 事件回调

| 回调 | 参数 | 触发时机 |
|------|------|---------|
| onRemoteReady | proxy: UIExtensionProxy | 远程 UI 就绪 |
| onReceive | data: Object | 收到远程数据 |
| onRelease | code: number | 远程 UI 释放 |
| onResult | code: number, want: Want | 远程 UI 返回结果 |
| onError | code: number, name: string, message: string | 远程 UI 错误 |
| onTerminated | code: number, want: Want | 远程 UI 终止 |
| onDrawReady | — | 首次绘制完成 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** API 10

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 可靠性 | 所有回调可选注册，未注册时不崩溃 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 |
|------|--------|------|
| 版本升级 | 是 | 构造选项随版本演进 |

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "js_ui_extension.cpp 中 UIExtensionComponent 的创建和事件注册逻辑"
```