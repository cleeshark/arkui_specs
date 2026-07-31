# 特性规格

> Func-04-03-09-Feat-05 Span无障碍与C-API：固化 Span 组件专用无障碍属性、原生 C-API 无障碍接口、AccessibilityRoleType 枚举体系。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Span无障碍与C-API (Span Accessibility & Native C-API) |
| 特性编号 | Func-04-03-09-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 10+（Span @since 10）；C-API @since 13/15/23/24；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Span 组件无障碍属性行为规格 | 补录 Span 专用的 accessibilityText/Description/Level（3 API 子集） |
| ADDED | 原生 C-API 无障碍接口体系 | 补录 native_interface_accessibility.h 的 Provider/ElementInfo/EventInfo 体系 |
| ADDED | AccessibilityRoleType 枚举体系 | 补录 125 个角色的完整枚举及 GetRoleByType 映射 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/09-accessibility-attributes/design.md` | Baselined |
| C-API Header | `interfaces/native/native_interface_accessibility.h` | `@since 13` |
| SDK | `interface_sdk-js/api/arkui/component/common.static.d.ets` | `@since 23 static` |

---

## 用户故事

### US-1: Span 组件无障碍属性

**作为** 应用开发者,
**我想要** 为 Span 文本片段设置无障碍属性,
**以便** 屏幕阅读器正确播报富文本中的每个片段。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `Span.accessibilityText("文本")` THEN 通过 `SpanModel::SetAccessibilityText` → `spanItem->accessibilityProperty->SetAccessibilityText(text)` 存储 | 正常 |
| AC-1.2 | WHEN 调用 `Span.accessibilityDescription("描述")` THEN 通过 `SpanModel::SetAccessibilityDescription` → `accessibilityProperty->SetAccessibilityDescription(description)` 存储 | 正常 |
| AC-1.3 | WHEN 调用 `Span.accessibilityLevel("yes")` THEN 通过 `SpanModel::SetAccessibilityImportance` → `accessibilityProperty->SetAccessibilityLevel(importance)` 存储 | 正常 |
| AC-1.4 | WHEN Span 无障碍属性与 CommonMethod 对比 THEN Span 仅支持 3 个无障碍属性（text/description/level），不支持 role/group/hint/callbacks 等 | 边界 |

### US-2: 原生 C-API 无障碍提供者

**作为** NDK 开发者,
**我想要** 通过 `OH_ArkUI_AccessibilityProvider` 注册无障碍提供者,
**以便** 自绘组件接入无障碍服务。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `OH_ArkUI_AccessibilityProviderRegisterCallback(provider, callbacks)` THEN 注册 7 个回调（findById/findByText/findFocused/findNextFocus/executeAction/clearFocus/getCursorPosition），返回 `SUCCESSFUL(0)` | 正常 |
| AC-2.2 | WHEN 调用 `OH_ArkUI_AccessibilityProviderRegisterCallbackWithInstance(instanceId, provider, callbacks)` (@since 15) THEN 带 instanceId 的注册 | 正常 |
| AC-2.3 | WHEN 调用 `OH_ArkUI_SendAccessibilityAsyncEvent(provider, eventInfo, callback)` THEN 异步发送无障碍事件 | 正常 |
| AC-2.4 | WHEN 调用 `OH_ArkUI_AccessibilityElementInfoSet*` 系列方法设置元素信息 THEN 设置对应字段（componentType/contents/hintText/accessibilityText/accessibilityDescription/rect/checkable/checked/focusable 等 30+ 属性） | 正常 |
| AC-2.5 | WHEN 传入非法参数（null provider、非法 eventType）THEN 返回 `BAD_PARAMETER(-2)` 或 `FAILED(-1)` | 异常 |

### US-3: AccessibilityRoleType 枚举体系

**作为** 应用开发者,
**我想要** 了解所有可用的 AccessibilityRoleType 枚举值,
**以便** 为组件选择正确的无障碍角色。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 使用 `AccessibilityRoleType.BUTTON` (5) THEN `GetRoleByType` 映射为 `"Button"` 字符串 | 正常 |
| AC-3.2 | WHEN 使用 `AccessibilityRoleType.ROLE_NONE` (124) THEN 映射为 `"NULL"`，表示无特定角色 | 正常 |
| AC-3.3 | WHEN 枚举值不在 0-124 范围内 THEN `GetRoleByType` 返回空字符串，触发 reset | 边界 |
| AC-3.4 | WHEN 组件未设置 accessibilityRole THEN 系统根据组件标签自动判定角色（如 Text → TEXT, Button → BUTTON） | 正常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 单元测试 | `span_model_ng.cpp:368-375` |
| AC-1.2 | R-1 | 单元测试 | `span_model_ng.cpp:380-385` |
| AC-1.3 | R-1 | 单元测试 | `span_model_ng.cpp:390-395` |
| AC-1.4 | R-1 | 代码审查 | Span 仅暴露 3 个无障碍 API |
| AC-2.1 | R-2 | 集成测试 | `native_interface_accessibility.h:505` |
| AC-2.2 | R-2 | 集成测试 | `native_interface_accessibility.h:517` |
| AC-2.3 | R-2 | 集成测试 | `native_interface_accessibility.h:528` |
| AC-2.4 | R-2 | 集成测试 | 30+ `Set*` 方法 |
| AC-2.5 | R-2 | 单元测试 | `ArkUI_AcessbilityErrorCode` 枚举 |
| AC-3.1 | R-3 | 单元测试 | `accessibility_utils.cpp:308-315` |
| AC-3.2 | R-3 | 单元测试 | `accessibility_utils.cpp:305` |
| AC-3.3 | R-3 | 单元测试 | 空字符串 → reset |
| AC-3.4 | R-3 | 集成测试 | 组件标签自动判定 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | Span 调用 `SetAccessibilityText/Description/Importance` | 通过 `SpanModelNG` 路由到 `SpanItem->accessibilityProperty`（`CustomAccessibilityProperty`），而非 FrameNode 的 AccessibilityProperty | Span 仅支持 text/description/level 三个无障碍属性，不支持 role/group/hint/callbacks 等 | AC-1.1 ~ AC-1.4 |
| R-2 | 行为 | NDK 调用 `OH_ArkUI_AccessibilityProviderRegisterCallback` | 注册 7 个回调函数指针；错误返回 `BAD_PARAMETER(-2)` 或 `FAILED(-1)` | `@since 13` 基础 API；`@since 15` 新增带 instanceId 版本；`@since 23` 新增 `OH_ArkUI_NativeModule_GetNativeAccessibilityProvider`；`@since 24` 新增 `SetComponentIdentifier` | AC-2.1 ~ AC-2.5 |
| R-3 | 行为 | 调用 `accessibilityRole(roleType)` 设置角色 | 枚举值通过 `GetRoleByType` 映射为字符串；125 个角色覆盖常用组件类型；非法值触发 reset | 系统角色 `accessibilityRole_` 由组件标签自动判定，`accessibilityCustomRole_` 由用户设置 | AC-3.1 ~ AC-3.4 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.4 | 单元测试 | Span 无障碍属性子集与 CommonMethod 差异 |
| VM-2 | AC-2.1 ~ AC-2.5 | 集成测试 | C-API Provider 注册、ElementInfo 设置、错误码 |
| VM-3 | AC-3.1 ~ AC-3.4 | 单元测试 | 125 角色枚举映射完整性 |

---

## API 变更分析

### 新增 API

N/A — 已有实现补录。

### Span 无障碍 API 清单

| API | Span 支持 | CommonMethod 支持 |
|-----|----------|-------------------|
| accessibilityText | 是 | 是 |
| accessibilityDescription | 是 | 是 |
| accessibilityLevel | 是 | 是 |
| accessibilityRole | 否 | 是 |
| accessibilityGroup | 否 | 是 |
| 其他 | 否 | 是 |

### C-API 版本矩阵

| @since | 新增内容 |
|--------|---------|
| 13 | 完整基础 API：Provider/ElementInfo/EventInfo/ActionArgs/7 回调/30+ ElementInfo Set* 方法 |
| 15 | `ProviderCallbacksWithInstance`、`RegisterCallbackWithInstance`、`NEXT/PREVIOUS_HTML_ITEM` |
| 23 | `ArkUI_NodeHandle`、`GetNativeAccessibilityProvider` |
| 24 | `SetComponentIdentifier` |

## 接口规格

> 精简覆盖。

### AccessibilityRoleType 枚举（部分代表性值）

| 枚举值 | 数值 | 映射字符串 |
|--------|------|-----------|
| BUTTON | 5 | "Button" |
| CHECKBOX | 13 | "Checkbox" |
| TEXT | 108 | "Text" |
| IMAGE | 40 | "Image" |
| SLIDER | 96 | "Slider" |
| SWITCH | 103 | "Switch" |
| LIST | 47 | "List" |
| GRID | 34 | "Grid" |
| ROLE_NONE | 124 | "NULL" |

完整 125 角色定义见 `accessibility_constants.h:21-147`。

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** API 10 (Span), API 13 (C-API)
- **API 版本号策略:** Public Static 统一为 `@since 23`

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| Span 使用 CustomAccessibilityProperty 而非 FrameNode AccessibilityProperty | Span 是文本片段，不是独立 FrameNode | AC-1.1 ~ AC-1.4 |
| C-API 回调在非 UI 线程调用 | Provider 回调需注意线程安全 | AC-2.1 ~ AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 性能 | C-API ElementInfo 复用池避免频繁分配 | 代码审查 |
| 安全 | C-API 所有 Set* 方法返回错误码，调用方需检查 | 集成测试 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 |
|------|--------|------|
| 无障碍 | 是 | 本特性为无障碍核心能力 |
| 版本升级 | 是 | C-API @since 13/15/23/24 版本演进 |

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "SpanModelNG 中 CustomAccessibilityProperty 与 FrameNode AccessibilityProperty 的差异"
  - repo: "openharmony/arkui_ace_engine"
    query: "native_interface_accessibility.h 中 Provider 回调的线程模型"
  - repo: "openharmony/arkui_ace_engine"
    query: "accessibility_utils.cpp 中 accessibilityRoleMap 和 accessibilityAceRoleMap 的完整映射"
```