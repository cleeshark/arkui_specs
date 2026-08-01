# 特性规格

> Func-04-03-09-Feat-02 无障碍焦点与导航：固化 accessibilityNextFocusId / accessibilityNextFocusParams / accessibilityDefaultFocus / onAccessibilityFocus / accessibilityFocusDrawLevel 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无障碍焦点与导航 (Accessibility Focus & Navigation) |
| 特性编号 | Func-04-03-09-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 18+；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | accessibilityNextFocusId 行为规格 | 补录焦点导航链设置及 AccessibilityNextFocusParams 行为 |
| ADDED | accessibilityDefaultFocus 行为规格 | 补录默认焦点注册（直接路由到 AccessibilityManager） |
| ADDED | onAccessibilityFocus 回调行为规格 | 补录焦点变化回调（双回调：内部+用户） |
| ADDED | accessibilityFocusDrawLevel 行为规格 | 补录焦点绘制层级（SELF/TOP） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/09-accessibility-attributes/design.md` | Baselined |
| Public SDK | `interface_sdk-js/api/arkui/component/common.static.d.ets` | `@since 23 static` |

---

## 用户故事

### US-1: 设置无障碍焦点导航链

**作为** 应用开发者,
**我想要** 通过 `.accessibilityNextFocusId()` 指定焦点导航链,
**以便** 屏幕阅读器用户按顺序导航组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.accessibilityNextFocusId("nextId")` 设置下一个焦点目标 THEN `accessibilityNextFocusParams_` 被创建并存储 `nextFocusInspectorKey = "nextId"`，触发 `ELEMENT_INFO_CHANGE` 事件 | 正常 |
| AC-1.2 | WHEN 调用 `.accessibilityNextFocusId("nextId", {isConsiderDescendants: true})` 设置第二个参数 THEN `descendantMode = true`，通过 `UpdateAccessibilityNextFocusIdMap` 注册到 AccessibilityManager | 正常 |
| AC-1.3 | WHEN 传入 `undefined` 或非字符串 THEN 声明式桥接 `ParseJsString` 失败直接返回，Native 桥接触发 `resetAccessibilityNextFocusId` | 异常 |

### US-2: 设置默认无障碍焦点

**作为** 应用开发者,
**我想要** 通过 `.accessibilityDefaultFocus()` 将组件标记为默认焦点,
**以便** 页面打开时屏幕阅读器自动聚焦到该组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.accessibilityDefaultFocus(true)` THEN 直接调用 `AccessibilityManager::AddFrameNodeToDefaultFocusList(frameNode, true)`（不存储在 AccessibilityProperty 中） | 正常 |
| AC-2.2 | WHEN 调用 `.accessibilityDefaultFocus(false)` 或传入非布尔值 THEN 调用 `AddFrameNodeToDefaultFocusList(frameNode, false)` 移除默认焦点 | 边界 |
| AC-2.3 | WHEN 通过 Static API 路径调用 THEN 支持 `PostAfterAttachMainTreeTask` 多线程延迟注册 | 正常 |

### US-3: 监听无障碍焦点变化

**作为** 应用开发者,
**我想要** 通过 `.onAccessibilityFocus()` 监听焦点变化,
**以便** 在组件获得/失去无障碍焦点时执行自定义逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.onAccessibilityFocus((isFocus: boolean) => {...})` 注册回调 THEN 存储到 `onUserAccessibilityFocusCallbackImpl_`，焦点变化时与内部回调先后调用 | 正常 |
| AC-3.2 | WHEN 调用 `.onAccessibilityFocus(undefined)` THEN 调用 `ResetUserOnAccessibilityFocusCallback` 清除用户回调 | 异常 |
| AC-3.3 | WHEN 焦点状态变化（`isAccessibilityFocused_` 变更）THEN `OnAccessibilityFocusCallback(bool)` 依次调用内部回调和用户回调 | 正常 |

### US-4: 设置焦点绘制层级

**作为** 应用开发者,
**我想要** 通过 `.accessibilityFocusDrawLevel()` 控制焦点框绘制层级,
**以便** 焦点框不被其他组件遮挡。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.accessibilityFocusDrawLevel(FocusDrawLevel.SELF)` (0) THEN 焦点框在组件自身层级绘制 | 正常 |
| AC-4.2 | WHEN 调用 `.accessibilityFocusDrawLevel(FocusDrawLevel.TOP)` (1) THEN 焦点框在顶层绘制，不被遮挡 | 正常 |
| AC-4.3 | WHEN 传入非数字或 > 1 的值 THEN 声明式桥接默认设为 0 (SELF)；Native 桥接触发 reset | 边界 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 单元测试 | `accessibility_property.cpp:1501-1516` |
| AC-1.2 | R-1 | 单元测试 | `accessibility_property.cpp:421-436` |
| AC-1.3 | R-1 | 单元测试 | `js_accessibility.cpp:87-106` |
| AC-2.1 | R-2 | 单元测试 | `view_abstract_model_ng.cpp:1399-1408` |
| AC-2.2 | R-2 | 单元测试 | `js_accessibility.cpp:279-288` |
| AC-2.3 | R-2 | 单元测试 | `view_abstract_model_static.cpp:1055-1077` |
| AC-3.1 | R-3 | 单元测试 | `accessibility_property.cpp:1630-1668` |
| AC-3.2 | R-3 | 单元测试 | `js_accessibility.cpp:260-277` |
| AC-3.3 | R-3 | 单元测试 | `accessibility_property.cpp:1456-1464` |
| AC-4.1 | R-4 | 单元测试 | `accessibility_property.cpp:1817-1828` |
| AC-4.2 | R-4 | 单元测试 | `FocusDrawLevel::TOP` |
| AC-4.3 | R-4 | 单元测试 | `js_accessibility.cpp:306-320` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 调用 `SetAccessibilityNextFocusInspectorKey(key)` | 创建/更新 `AccessibilityNextFocusParams`，设置 `nextFocusInspectorKey`；若有 `descendantMode` 则注册到 AccessibilityManager | `AccessibilityNextFocusParams` 为 `std::optional`，默认 `nullopt`；`descendantMode` 默认 `false` | AC-1.1, AC-1.2, AC-1.3 |
| R-2 | 行为 | 调用 `SetAccessibilityDefaultFocus(bool)` | 直接路由到 `AccessibilityManager::AddFrameNodeToDefaultFocusList`，不存储在 AccessibilityProperty 中 | 与其余无障碍属性存储方式不同，不走 AccessibilityProperty 成员变量 | AC-2.1, AC-2.2, AC-2.3 |
| R-3 | 行为 | 焦点状态变化 (`isAccessibilityFocused_` 变更) | 依次调用 `onAccessibilityFocusCallbackImpl_`（内部）和 `onUserAccessibilityFocusCallbackImpl_`（用户） | 双回调模式：内部回调先于用户回调执行 | AC-3.1, AC-3.2, AC-3.3 |
| R-4 | 边界 | 调用 `SetFocusDrawLevel(int32_t)` 且值在 [0,1] 范围内 | 更新 `focusDrawLevel_` 为对应 `FocusDrawLevel` 枚举值 | 超出范围时声明式桥接默认设为 0（SELF）；Native 桥接触发 reset | AC-4.1, AC-4.2, AC-4.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.3 | 单元测试 | accessibilityNextFocusId 参数存储 + descendantMode |
| VM-2 | AC-2.1 ~ AC-2.3 | 单元测试 | accessibilityDefaultFocus 直接路由到 AccessibilityManager |
| VM-3 | AC-3.1 ~ AC-3.3 | 单元测试 | onAccessibilityFocus 双回调机制 |
| VM-4 | AC-4.1 ~ AC-4.3 | 单元测试 | FocusDrawLevel 枚举校验 |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

> 精简覆盖，核心接口行为见规则定义。

### accessibilityNextFocusId

| 属性 | 值 |
|------|-----|
| 函数签名 | `CommonMethod.accessibilityNextFocusId(nextId: string, nextFocusParams?: AccessibilityNextFocusParams): this` |
| 开放范围 | Public |
| 关联 AC | AC-1.1 ~ AC-1.3 |

### accessibilityDefaultFocus

| 属性 | 值 |
|------|-----|
| 函数签名 | `CommonMethod.accessibilityDefaultFocus(focus: boolean \| undefined): this` |
| 开放范围 | Public |
| 关联 AC | AC-2.1 ~ AC-2.3 |

### onAccessibilityFocus

| 属性 | 值 |
|------|-----|
| 函数签名 | `CommonMethod.onAccessibilityFocus(callback: AccessibilityFocusCallback \| undefined): this` |
| 开放范围 | Public |
| 关联 AC | AC-3.1 ~ AC-3.3 |

### accessibilityFocusDrawLevel

| 属性 | 值 |
|------|-----|
| 函数签名 | `CommonMethod.accessibilityFocusDrawLevel(drawLevel: FocusDrawLevel \| undefined): this` |
| 开放范围 | Public |
| 关联 AC | AC-4.1 ~ AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** API 18
- **API 版本号策略:** 以 SDK `.d.ts` 为 API 契约，各属性 @since 18；Static 统一为 @since 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| accessibilityDefaultFocus 不存储在 AccessibilityProperty | 直接路由到 AccessibilityManager，不走 Property 层 | AC-2.1 ~ AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 性能 | 焦点回调不阻塞 UI 线程 | 代码审查 |
| 可靠性 | `CHECK_NULL_VOID` 保护 FrameNode 空指针 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 |
|------|--------|------|
| 无障碍 | 是 | 本特性为无障碍核心能力 |
| 版本升级 | 是 | SDK 版本差异见兼容性声明 |

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityNextFocusParams 和 UpdateAccessibilityNextFocusIdMap 的注册逻辑"
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityManager::AddFrameNodeToDefaultFocusList 的调度机制"
```