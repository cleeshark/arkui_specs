# 特性规格

> Func-04-03-09-Feat-03 无障碍组选项与状态：固化 accessibilityGroupOptions / accessibilityTextPreferred / accessibilityUseSamePage / accessibilitySelected / accessibilityChecked / accessibilityStateDescription / accessibilityScrollTriggerable 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无障碍组选项与状态 (Accessibility Group Options & State) |
| 特性编号 | Func-04-03-09-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 10+（accessibilityTextPreferred @since 10, 其余 @since 18）；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | accessibilityGroupOptions 行为规格 | 补录 AccessibilityGroupOptions 结构体（stateController/actionController） |
| ADDED | accessibilityTextPreferred 行为规格 | 补录分组文本优先策略 |
| ADDED | accessibilityUseSamePage 行为规格 | 补录 AccessibilitySamePageMode 枚举（SEMI_SILENT/FULL_SILENT） |
| ADDED | accessibilitySelected/Checked 行为规格 | 补录选中/勾选状态设置及与 Group 的交互 |
| ADDED | accessibilityStateDescription 行为规格 | 补录状态描述（最大1000字符截断） |
| ADDED | accessibilityScrollTriggerable 行为规格 | 补录可滚动触发控制（默认 true） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/09-accessibility-attributes/design.md` | Baselined |
| Public SDK | `interface_sdk-js/api/arkui/component/common.static.d.ets` | `@since 23 static` |

---

## 用户故事

### US-1: 配置无障碍分组选项

**作为** 应用开发者,
**我想要** 通过 `accessibilityGroup` 的第二参数配置分组选项,
**以便** 指定分组的状态控制器和动作控制器。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.accessibilityGroup(true, {accessibilityPreferred: true})` THEN `accessibilityTextPreferred_` 设为 true，分组文本拼接时优先使用子组件无障碍文本 | 正常 |
| AC-1.2 | WHEN 调用 `.accessibilityGroup(true, {stateControllerRoleType: BUTTON, stateControllerId: "btn1"})` THEN 设置 `AccessibilityGroupOptions` 按类型+ID 指定状态控制器 | 正常 |
| AC-1.3 | WHEN 通过 Native 桥接调用 THEN `AccessibilityOptions` 对象不被解析（仅处理 boolean） | 边界 |

### US-2: 控制无障碍页面模式

**作为** 应用开发者,
**我想要** 通过 `.accessibilityUseSamePage()` 控制无障碍页事件,
**以便** 在特定场景下减少页面切换事件的播报。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.accessibilityUseSamePage(AccessibilitySamePageMode.SEMI_SILENT)` (0) THEN 忽略初始页面加载事件和根节点页面事件 | 正常 |
| AC-2.2 | WHEN 调用 `.accessibilityUseSamePage(AccessibilitySamePageMode.FULL_SILENT)` (1) THEN 忽略所有页面事件 | 正常 |
| AC-2.3 | WHEN 传入非法索引值 THEN 声明式桥接传入空字符串触发重置 | 异常 |

### US-3: 设置组件选中/勾选状态

**作为** 应用开发者,
**我想要** 通过 `.accessibilitySelected()` / `.accessibilityChecked()` 标记组件状态,
**以便** 屏幕阅读器正确播报组件的选中/勾选状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.accessibilitySelected(true)` THEN `isSelected_` 设为 true，无障碍服务可查询到选中状态 | 正常 |
| AC-3.2 | WHEN 调用 `.accessibilityChecked(true)` THEN `checkedType_` 设为 true 且 `isUserCheckable_` 设为 true | 正常 |
| AC-3.3 | WHEN 传入 `undefined` THEN 触发 Reset（`ResetUserSelected` / `ResetUserCheckedType` + `ResetUserCheckable`） | 异常 |
| AC-3.4 | WHEN 组件为 Group 且设置了 `stateController` THEN 状态控制器的选中/勾选状态传播到 Group 的状态播报 | 正常 |

### US-4: 设置状态描述与滚动控制

**作为** 应用开发者,
**我想要** 通过 `.accessibilityStateDescription()` 和 `.accessibilityScrollTriggerable()` 设置状态描述和滚动控制,
**以便** 屏幕阅读器播报组件的自定义状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.accessibilityStateDescription("已选中2项")` 设置 ≤ 1000 字符的描述 THEN 存储并去重 | 正常 |
| AC-4.2 | WHEN 传入 > 1000 字符的描述 THEN 截断到前 1000 字符后存储 | 边界 |
| AC-4.3 | WHEN 调用 `.accessibilityScrollTriggerable(false)` THEN 禁用子节点在无障碍模式下的滚动触发 | 正常 |
| AC-4.4 | WHEN 未设置 `accessibilityScrollTriggerable` THEN 默认为 true（可滚动） | 正常 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 | R-1 | 单元测试 | `accessibility_property.cpp:1477-1480` |
| AC-1.2 | R-1, R-2 | 单元测试 | `js_accessibility.cpp:53-69` |
| AC-1.3 | R-1 | 单元测试 | Native 桥接仅处理 boolean |
| AC-2.1 | R-3 | 单元测试 | `accessibility_property.cpp:1203-1206` |
| AC-2.2 | R-3 | 单元测试 | `AccessibilitySamePageMode::FULL_SILENT` |
| AC-2.3 | R-3 | 单元测试 | `js_accessibility.cpp:290-304` |
| AC-3.1 | R-4 | 单元测试 | `accessibility_property.cpp:1271-1289` |
| AC-3.2 | R-4 | 单元测试 | `view_abstract_model_ng.cpp:1490-1503` |
| AC-3.3 | R-4 | 单元测试 | `js_accessibility.cpp:195-225` |
| AC-3.4 | R-4 | 集成测试 | stateController 与 Group 状态传播 |
| AC-4.1 | R-5 | 单元测试 | `accessibility_property.cpp:1218-1227` |
| AC-4.2 | R-5 | 单元测试 | 1000 字符截断逻辑 |
| AC-4.3 | R-6 | 单元测试 | `accessibility_property.cpp:1331-1349` |
| AC-4.4 | R-6 | 单元测试 | 默认 `isUserScrollTriggerable_ = true` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 设置 `AccessibilityGroupOptions` 通过 `accessibilityGroup` 第二参数 | `accessibilityTextPreferred` 单独存储为 bool；`stateController`/`actionController` 存储为 `AccessibilityGroupOptions` 结构体 | 仅声明式桥接支持；Native 桥接仅处理 boolean | AC-1.1, AC-1.2, AC-1.3 |
| R-2 | 行为 | `accessibilityTextPreferred == true` 且 Group 拼接子组件文本 | `GetGroupPreferAccessibilityText()` 优先使用子组件无障碍文本，而非通用文本 | 需与 `accessibilityGroup(true)` 联用 | AC-1.1 |
| R-3 | 边界 | 调用 `SetAccessibilitySamePage(mode)` 且 `mode` 为 "FULL_SILENT" 或 "SEMI_SILENT" | 更新 `accessibilityUseSamePage_`；非法值传入空字符串 | `SEMI_SILENT=0` 忽略初始加载和根节点事件；`FULL_SILENT=1` 忽略所有页面事件 | AC-2.1, AC-2.2, AC-2.3 |
| R-4 | 行为 | 调用 `SetAccessibilitySelected(selected, resetValue)` / `SetAccessibilityChecked(checked, resetValue)` | `resetValue=true` 时 Reset；否则 Set 对应 `optional<bool>` 或 `optional<int32_t>` | `checkedType_` 为 int32（非 bool），`SetAccessibilityChecked` 同时设置 `isUserCheckable_ = true` | AC-3.1, AC-3.2, AC-3.3, AC-3.4 |
| R-5 | 边界 | 调用 `SetAccessibilityStateDescription(desc)` | 去重后存储；长度 > 1000 时截断到前 1000 字符 | `STATE_DESCRIPTION_MAX_LENGTH = 1000` | AC-4.1, AC-4.2 |
| R-6 | 行为 | 调用 `SetAccessibilityScrollTriggerable(bool)` | 存储 `isUserScrollTriggerable_`；`false` 时阻止子节点无障碍滚动 | 默认 `true`；`ResetUserScrollTriggerable` 恢复为 `true` | AC-4.3, AC-4.4 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.3 | 单元测试 | AccessibilityGroupOptions 结构体 + 双范式差异 |
| VM-2 | AC-2.1 ~ AC-2.3 | 单元测试 | AccessibilitySamePageMode 枚举映射 |
| VM-3 | AC-3.1 ~ AC-3.4 | 单元测试 | Selected/Checked 与 Group stateController 交互 |
| VM-4 | AC-4.1 ~ AC-4.4 | 单元测试 | 状态描述截断 + 滚动触发默认值 |

---

## API 变更分析

N/A — 已有实现补录。

## 接口规格

> 精简覆盖，核心接口行为见规则定义。

| API | 签名 | @since |
|-----|------|--------|
| `accessibilityGroupOptions` | 通过 `accessibilityGroup(isGroup, options)` 第二参数设置 | @since 12 |
| `accessibilityUseSamePage` | `(pageMode: AccessibilitySamePageMode \| undefined): this` | 23 static |
| `accessibilitySelected` | `(isSelect: boolean \| undefined): this` | 23 static |
| `accessibilityChecked` | `(isCheck: boolean \| undefined): this` | 23 static |
| `accessibilityScrollTriggerable` | `(isTriggerable: boolean \| undefined): this` | 23 static |
| `accessibilityStateDescription` | `(description: string \| Resource \| undefined): this` | 23 static |

## 兼容性声明

- **已有 API 行为变更:** 否
- **最低支持版本:** API 10 (accessibilityTextPreferred), API 18 (其他)
- **API 版本号策略:** 以 SDK `.d.ts` 为 API 契约，各属性按实际引入版本标注；Static 统一为 @since 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| `accessibilityGroupOptions` 仅声明式桥接支持 | Native 桥接的 `accessibilityGroup` 仅处理 boolean | AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|----------|---------|
| 性能 | 状态变更不触发布局重算 | 代码审查 |
| 可靠性 | 字符串截断保护（1000字符） | 单元测试 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 |
|------|--------|------|
| 无障碍 | 是 | 本特性为无障碍核心能力 |

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式
- [ ] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityGroupOptions 中 stateController 和 actionController 的传播机制"
  - repo: "openharmony/arkui_ace_engine"
    query: "GetGroupPreferAccessibilityText 与 GetGroupText 的区别"
```