# 特性规格

> Func-04-03-09-Feat-01 基础无障碍属性：固化 accessibilityText / accessibilityDescription / accessibilityGroup / accessibilityLevel / accessibilityRole 五个核心无障碍属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 基础无障碍属性 (Core Accessibility Attributes) |
| 特性编号 | Func-04-03-09-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 10+（accessibilityText @since 10, accessibilityDescription @since 10, accessibilityGroup @since 12, accessibilityLevel @since 11, accessibilityRole @since 18）；Static 统一为 API 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | accessibilityText 属性行为规格 | 补录无障碍文本设置/获取/事件通知行为 |
| ADDED | accessibilityDescription 属性行为规格 | 补录无障碍描述设置/JSON侧信道解析行为 |
| ADDED | accessibilityGroup 属性行为规格 | 补录无障碍分组及 AccessibilityOptions 行为 |
| ADDED | accessibilityLevel 属性行为规格 | 补录无障碍级别白名单校验及 accessibilityImportance 别名 |
| ADDED | accessibilityRole 属性行为规格 | 补录无障碍角色枚举映射及重置行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/09-accessibility-attributes/design.md` | 待生成 |
| Public SDK | `interface_sdk-js/api/arkui/component/common.static.d.ets` | `@since 23 static` |
| Internal SDK | `interface_sdk-js/zh-cn/api/@internal/component/ets/common.d.ts` | 含版本历史 |

---

## 用户故事

### US-1: 设置无障碍文本

**作为** 应用开发者,
**我想要** 通过 `.accessibilityText()` 为组件设置无障碍文本,
**以便** 屏幕阅读器能够播报用户可理解的内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.accessibilityText("确定按钮")` 设置非空字符串 THEN 组件无障碍文本更新为"确定按钮"，并触发 `TEXT_CHANGE` 事件通知无障碍子系统 | 正常 |
| AC-1.2 | WHEN 调用 `.accessibilityText("")` 设置空字符串 THEN 无障碍文本被清空，不触发事件（因 `SetAccessibilityTextWithEvent` 内部去重：空字符串与 `std::nullopt` 的 `value_or("")` 相同） | 边界 |
| AC-1.3 | WHEN 连续两次调用 `.accessibilityText("确定")` 设置相同值 THEN 第二次调用不触发 `TEXT_CHANGE` 事件（去重机制） | 正常 |
| AC-1.4 | WHEN 调用 `.accessibilityText($r('app.string.ok'))` 使用 Resource 类型 THEN 从资源文件解析为对应字符串后设置 | 正常 |
| AC-1.5 | WHEN 传入 `undefined` THEN 声明式桥接因 `ParseJsString` 失败直接返回（无操作），Native 桥接触发 `resetAccessibilityText` | 异常 |
| AC-1.6 | WHEN 组件同时具有文本内容（如 Text 组件）和无障碍文本 THEN 无障碍服务优先播报无障碍文本，忽略组件自身文本 | 正常 |

### US-2: 设置无障碍描述

**作为** 应用开发者,
**我想要** 通过 `.accessibilityDescription()` 为组件添加无障碍描述,
**以便** 屏幕阅读器在选中组件后播报额外的上下文信息。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.accessibilityDescription("点击后将跳转到设置页面")` 设置非空字符串 THEN 描述被存储，选中时先播报文本再播报描述 | 正常 |
| AC-2.2 | WHEN 调用 `.accessibilityDescription('{"$accessibilityDescription":"自定义描述","$autoEventParam":"参数"}')` 传入 JSON 格式字符串 THEN 声明式桥接解析出 `$accessibilityDescription` 和 `$autoEventParam` 子字段分别设置（JSON 侧信道解析） | 正常 |
| AC-2.3 | WHEN 通过 Native 桥接（Static API）传入相同 JSON 字符串 THEN JSON 不被解析，整个原始字符串作为描述值设置（Native 桥接不支持 JSON 侧信道） | 边界 |
| AC-2.4 | WHEN 传入 `undefined` THEN 声明式桥接无操作，Native 桥接触发 `resetAccessibilityDescription` | 异常 |

### US-3: 设置无障碍分组

**作为** 应用开发者,
**我想要** 通过 `.accessibilityGroup()` 将多个子组件标记为一个无障碍分组,
**以便** 屏幕阅读器将它们作为一个整体播报。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.accessibilityGroup(true)` 且组件无文本/无障碍文本 THEN 系统深度优先拼接子组件的通用文本属性形成合并文本，并触发 `ELEMENT_INFO_CHANGE` 事件 | 正常 |
| AC-3.2 | WHEN 调用 `.accessibilityGroup(false)` 或未设置 THEN 不进行子组件文本拼接，组件独立参与无障碍树 | 正常 |
| AC-3.3 | WHEN 调用 `.accessibilityGroup(true, {accessibilityPreferred: true})` THEN 系统优先拼接子组件的无障碍文本属性而非通用文本属性 | 正常 |
| AC-3.4 | WHEN 调用 `.accessibilityGroup(true, {stateControllerRoleType: AccessibilityRoleType.BUTTON, stateControllerId: "btn1"})` THEN 设置分组状态控制器（按类型+ID） | 正常 |
| AC-3.5 | WHEN 通过 Native 桥接调用 `setAccessibilityGroup(node, true)` THEN 仅设置布尔值，`AccessibilityOptions` 对象不被解析（Native 桥接仅支持 boolean 参数） | 边界 |
| AC-3.6 | WHEN 父节点为 Group 且子节点未显式设置 `accessibilityLevel("yes")` THEN 子节点被合并入父 Group，不作为独立无障碍元素（`ancestorGroupFlag` 机制） | 边界 |

### US-4: 设置无障碍级别

**作为** 应用开发者,
**我想要** 通过 `.accessibilityLevel()` 控制组件在无障碍树中的可见性,
**以便** 精细控制屏幕阅读器的导航范围。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.accessibilityLevel("yes")` THEN 组件始终可被无障碍服务识别，触发 `ELEMENT_INFO_CHANGE` 事件 | 正常 |
| AC-4.2 | WHEN 调用 `.accessibilityLevel("no")` THEN 组件不可被识别，但其子组件仍可被搜索到 | 正常 |
| AC-4.3 | WHEN 调用 `.accessibilityLevel("no-hide-descendants")` THEN 组件及其所有子组件均不可被无障碍服务识别 | 正常 |
| AC-4.4 | WHEN 调用 `.accessibilityLevel("auto")` 或传入非法字符串（如 `"invalid"`） THEN 值被静默转为 `"auto"`（白名单校验：仅 `"yes"/"no"/"no-hide-descendants"` 被接受，其余均转为 `"auto"`） | 边界 |
| AC-4.5 | WHEN 未显式设置 accessibilityLevel THEN 默认值为 `"auto"`，由无障碍分组服务和 ArkUI 运行时决定可识别性 | 正常 |
| AC-4.6 | WHEN 调用 `.accessibilityImportance("yes")` THEN 行为与 `.accessibilityLevel("yes")` 完全一致（两者为同一底层属性的别名，均调用 `SetAccessibilityImportance`） | 正常 |
| AC-4.7 | WHEN 传入 `undefined` THEN Native 桥接触发 `resetAccessibilityLevel`（恢复为 `"auto"`） | 异常 |

### US-5: 设置无障碍角色

**作为** 应用开发者,
**我想要** 通过 `.accessibilityRole()` 为组件指定无障碍角色类型,
**以便** 屏幕阅读器按正确的语义播报组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.accessibilityRole(AccessibilityRoleType.BUTTON)` THEN 角色枚举值 5 通过 `AccessibilityUtils::GetRoleByType` 映射为字符串 `"Button"` 并存储到 `accessibilityCustomRole_` | 正常 |
| AC-5.2 | WHEN 调用 `.accessibilityRole(AccessibilityRoleType.ROLE_NONE)` (124) THEN 角色映射为对应字符串并存储 | 正常 |
| AC-5.3 | WHEN 传入非法枚举值（超出 0-124 范围）THEN `GetRoleByType` 返回空字符串，触发 `resetValue=true`，调用 `ResetAccessibilityCustomRole` | 异常 |
| AC-5.4 | WHEN 传入非数字类型（如字符串）THEN 声明式桥接检测到 `!info[0]->IsNumber()` 后调用 `SetAccessibilityRole("", true)` 重置角色 | 异常 |
| AC-5.5 | WHEN 未设置 accessibilityRole THEN 组件使用系统根据组件标签自动判定的角色（如 Text 组件自动为 `TEXT` 角色） | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1 | R-1, R-2 | — | 单元测试 | `accessibility_property_test` |
| AC-1.2 | R-1 | — | 单元测试 | 去重逻辑在 `accessibility_property.cpp:1494-1495` |
| AC-1.3 | R-1 | — | 单元测试 | 去重逻辑在 `accessibility_property.cpp:1520-1521` |
| AC-1.4 | R-1 | — | 集成测试 | Resource 解析在 JS 桥接层 |
| AC-1.5 | R-1, R-17 | — | 单元测试 | `js_accessibility.cpp:72-80` |
| AC-1.6 | R-2 | — | 集成测试 | 无障碍子系统播报优先级 |
| AC-2.1 | R-3 | — | 单元测试 | `accessibility_property.cpp:1534-1541` |
| AC-2.2 | R-4, R-16 | — | 单元测试 | `js_accessibility.cpp:108-126` JSON 解析 |
| AC-2.3 | R-4, R-16 | — | 单元测试 | Native 桥接不解析 JSON |
| AC-2.4 | R-3 | — | 单元测试 | `arkts_native_common_bridge.cpp:5277-5291` |
| AC-3.1 | R-5, R-6 | — | 单元测试 | `accessibility_property.cpp:457-497` |
| AC-3.2 | R-5 | — | 单元测试 | 默认 `accessibilityGroup_ = false` |
| AC-3.3 | R-5, R-7 | — | 单元测试 | `accessibilityTextPreferred` 标志 |
| AC-3.4 | R-5, R-8 | — | 单元测试 | `AccessibilityGroupOptions` 解析 |
| AC-3.5 | R-16 | — | 单元测试 | Native 桥接仅处理 boolean |
| AC-3.6 | R-6, R-9 | — | 单元测试 | `accessibility_property.cpp:949-974` |
| AC-4.1 | R-10 | — | 单元测试 | `accessibility_property.cpp:1599-1615` |
| AC-4.2 | R-10 | — | 单元测试 | `Level::NO_STR` |
| AC-4.3 | R-10 | — | 单元测试 | `Level::NO_HIDE_DESCENDANTS` |
| AC-4.4 | R-11, R-12 | — | 单元测试 | 白名单校验逻辑 |
| AC-4.5 | R-10 | — | 单元测试 | 默认 `Level::AUTO` |
| AC-4.6 | R-13 | — | 单元测试 | `js_accessibility.cpp:165-173` 别名 |
| AC-4.7 | R-10 | — | 单元测试 | Native 桥接 reset |
| AC-5.1 | R-14 | — | 单元测试 | `accessibility_utils.cpp:308-315` 映射 |
| AC-5.2 | R-14 | — | 单元测试 | 125 个角色覆盖 |
| AC-5.3 | R-15 | — | 单元测试 | 空字符串 → reset |
| AC-5.4 | R-15 | — | 单元测试 | `js_accessibility.cpp:243-258` |
| AC-5.5 | R-14 | — | 集成测试 | 组件标签自动判定 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 调用 `SetAccessibilityTextWithEvent(text)` 且 `text != accessibilityText_.value_or("")` | 更新 `accessibilityText_` 并触发 `NotifyComponentChangeEvent(TEXT_CHANGE)` | 空字符串 `""` 与 `std::nullopt` 的 `value_or("")` 等价，不会触发事件 | AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5 |
| R-2 | 行为 | 组件同时具有文本内容和无障碍文本 | 无障碍服务优先播报无障碍文本，忽略组件自身文本内容 | 仅影响无障碍播报，不影响视觉渲染 | AC-1.6 |
| R-3 | 行为 | 调用 `SetAccessibilityDescriptionWithEvent(desc)` 且 `desc != accessibilityDescription_.value_or("")` | 更新 `accessibilityDescription_` 并触发 `TEXT_CHANGE` 事件 | 选中时先播报文本再播报描述 | AC-2.1, AC-2.4 |
| R-4 | 行为 | 声明式桥接收到 `{...}` 格式的 JSON 字符串 | 解析 `$accessibilityDescription` 和 `$autoEventParam` 子字段，分别调用 `SetAccessibilityDescription` 和 `SetAutoEventParam` | Native 桥接不解析 JSON，直接传递原始字符串；JSON 解析仅在第一层 `{}` 包裹时触发 | AC-2.2, AC-2.3 |
| R-5 | 行为 | 调用 `SetAccessibilityGroup(true)` | 设置 `accessibilityGroup_ = true`，触发 `ELEMENT_INFO_CHANGE` 事件，系统通过 `GetGroupTextRecursive` 深度优先拼接子组件文本 | 默认值为 `false`；去重：相同值不触发事件 | AC-3.1, AC-3.2, AC-3.3, AC-3.4 |
| R-6 | 边界 | 父节点 `accessibilityGroup == true` 且子节点 `accessibilityLevel != "yes"` | `ancestorGroupFlag` 为 true，子节点 `shouldSearchSelf` 设为 false，子节点文本合并入父 Group | 子节点显式设置 `accessibilityLevel("yes")` 可覆盖此行为，保持独立可搜索 | AC-3.6 |
| R-7 | 行为 | `AccessibilityOptions.accessibilityPreferred == true` | 系统优先拼接子组件的无障碍文本属性，而非通用文本属性 | 仅在与 `accessibilityGroup(true)` 联用时生效 | AC-3.3 |
| R-8 | 行为 | 设置 `AccessibilityOptions` 中的 `stateControllerRoleType` + `stateControllerId` | 建立按类型+ID 的分组状态控制器 | 声明式桥接专属；Native 桥接不解析 `AccessibilityOptions` | AC-3.4 |
| R-9 | 行为 | 父节点 `accessibilityGroup == true` 且子节点 `accessibilityLevel == "no-hide-descendants"` | 子节点 `shouldSearchSelf = false, shouldSearchChildren = false`，该子节点及其后代完全从无障碍树中隐藏 | 优先级高于 `ancestorGroupFlag` 的合并逻辑 | AC-3.6 |
| R-10 | 行为 | 调用 `SetAccessibilityLevel(level)` 且 `level` 为 `"yes"/"no"/"no-hide-descendants"` | 更新 `accessibilityLevel_` 并触发 `ELEMENT_INFO_CHANGE` 事件 | 默认值为 `"auto"`；去重：相同值不触发事件 | AC-4.1, AC-4.2, AC-4.3, AC-4.5, AC-4.7 |
| R-11 | 边界 | 调用 `SetAccessibilityLevel(level)` 且 `level` 不为 `"yes"/"no"/"no-hide-descendants"` | 值被静默转为 `"auto"`（白名单校验） | 传入 `"auto"` 字符串本身也被视为非法值，同样转为 `"auto"`（即 `"auto"` 不是合法输入，而是默认回退值） | AC-4.4 |
| R-12 | 边界 | 连续两次调用 `SetAccessibilityLevel` 传入相同合法值 | 第二次调用不触发事件（去重） | 去重基于 `backupLevel != accessibilityLevel_.value_or("")` 比较 | AC-4.4 |
| R-13 | 行为 | 调用 `accessibilityImportance` 或 `accessibilityLevel` | 两者均调用 `SetAccessibilityImportance`，行为完全一致 | 两个 JS 方法名是同一底层属性的别名 | AC-4.6 |
| R-14 | 行为 | 调用 `SetAccessibilityRole(role, false)` 且 `role` 非空 | 调用 `SetAccessibilityCustomRole(role)` 设置 `accessibilityCustomRole_` | 系统角色 `accessibilityRole_` 由组件标签自动判定，不受此 API 影响 | AC-5.1, AC-5.2, AC-5.5 |
| R-15 | 异常 | `accessibilityRole` 传入非法值（非数字、超出枚举范围、空映射） | 声明式桥接调用 `SetAccessibilityRole("", true)` → `ResetAccessibilityCustomRole`；Native 桥接调用 `resetAccessibilityCustomRole` | 非法枚举值通过 `GetRoleByType` 返回空字符串触发重置 | AC-5.3, AC-5.4 |
| R-16 | 边界 | Native 桥接（Static API）调用无障碍属性 | 仅传递基础类型值（boolean/string/int），不解析 JSON 侧信道（`$accessibilityDescription`）、不解析 `AccessibilityOptions` 对象 | 声明式桥接和 Native 桥接行为不对称，需在 API 文档中标注 | AC-2.3, AC-3.5 |
| R-17 | 异常 | 任意无障碍属性 `Set*` 方法接收到 `nullptr` FrameNode | `CHECK_NULL_VOID` 宏提前返回，无操作，无崩溃 | 适用于所有 `ViewAbstractModelNG::SetAccessibility*` 方法 | AC-1.5 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.6 | 单元测试 (`accessibility_property_test`) | accessibilityText 设置/去重/事件通知 |
| VM-2 | AC-2.1 ~ AC-2.4 | 单元测试 + 集成测试 | accessibilityDescription JSON 侧信道解析差异 |
| VM-3 | AC-3.1 ~ AC-3.6 | 单元测试 (`accessibility_property_test`) | accessibilityGroup 文本拼接 + ancestorGroupFlag 交互 |
| VM-4 | AC-4.1 ~ AC-4.7 | 单元测试 | accessibilityLevel 白名单校验 + 别名一致性 |
| VM-5 | AC-5.1 ~ AC-5.5 | 单元测试 | accessibilityRole 枚举映射 + 非法值重置 |
| VM-6 | R-16 | 集成测试 (Static API 路径) | 声明式 vs Native 桥接行为差异 |

---

## API 变更分析

> 本特性为已有能力补录，所有 API 均为已有实现，无新增/变更/废弃 API。

### 新增 API

N/A — 本特性涉及的 5 个 API 均为已有实现，补录行为规格。

### 变更/废弃 API

无。

---

## 接口规格

### 接口定义

**accessibilityText**

| 属性 | 值 |
|------|-----|
| 函数签名 | `CommonMethod.accessibilityText(text: Resource \| string \| undefined): this` |
| 返回值 | `this` — 支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| text | `Resource \| string \| undefined` | 否 | `""` | 非空字符串触发事件；相同值去重；`undefined` 无操作 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入非空字符串 `"确定"` | 存储 `accessibilityText_`，触发 `TEXT_CHANGE` 事件 | AC-1.1 |
| 2 | 传入空字符串 `""` | 与默认值相同，不触发事件（去重） | AC-1.2 |
| 3 | 连续两次传入相同字符串 | 第二次不触发事件 | AC-1.3 |
| 4 | 传入 `Resource` 类型 | 解析后设置 | AC-1.4 |
| 5 | 传入 `undefined` | 声明式：无操作；Native：reset | AC-1.5 |

---

**accessibilityDescription**

| 属性 | 值 |
|------|-----|
| 函数签名 | `CommonMethod.accessibilityDescription(description: Resource \| string \| undefined): this` |
| 返回值 | `this` — 支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 ~ AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| description | `Resource \| string \| undefined` | 否 | `""` | JSON 格式 `{...}` 在声明式桥接中触发侧信道解析 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入普通字符串 | 存储 `accessibilityDescription_`，触发 `TEXT_CHANGE` | AC-2.1 |
| 2 | 传入 `{"$accessibilityDescription":"X","$autoEventParam":"Y"}` (声明式) | 分别设置描述和自动事件参数 | AC-2.2 |
| 3 | 传入相同 JSON 字符串 (Native) | 整个字符串作为描述值，不解析子字段 | AC-2.3 |
| 4 | 传入 `undefined` | 声明式：无操作；Native：reset | AC-2.4 |

---

**accessibilityGroup**

| 属性 | 值 |
|------|-----|
| 函数签名 | `CommonMethod.accessibilityGroup(isGroup: boolean \| undefined, accessibilityOptions?: AccessibilityOptions): this` |
| 返回值 | `this` — 支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1 ~ AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| isGroup | `boolean \| undefined` | 否 | `false` | `true` 时触发子组件文本拼接 |
| accessibilityOptions | `AccessibilityOptions` | 否 | `{}` | 仅声明式桥接支持；Native 桥接忽略此参数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `accessibilityGroup(true)` | 触发 `ELEMENT_INFO_CHANGE`，深度优先拼接子组件文本 | AC-3.1 |
| 2 | `accessibilityGroup(false)` | 取消分组，组件独立参与无障碍树 | AC-3.2 |
| 3 | `accessibilityGroup(true, {accessibilityPreferred: true})` | 优先拼接子组件无障碍文本 | AC-3.3 |
| 4 | Native 桥接 `setAccessibilityGroup(node, true)` | 仅设置 boolean，options 被忽略 | AC-3.5 |

---

**accessibilityLevel**

| 属性 | 值 |
|------|-----|
| 函数签名 | `CommonMethod.accessibilityLevel(value: string \| undefined): this` |
| 返回值 | `this` — 支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1 ~ AC-4.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `string \| undefined` | 否 | `"auto"` | 仅接受 `"yes"` / `"no"` / `"no-hide-descendants"`；其余值静默转为 `"auto"` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `accessibilityLevel("yes")` | 触发 `ELEMENT_INFO_CHANGE`，组件始终可识别 | AC-4.1 |
| 2 | `accessibilityLevel("no")` | 组件隐藏，子组件仍可搜索 | AC-4.2 |
| 3 | `accessibilityLevel("no-hide-descendants")` | 组件及后代全部隐藏 | AC-4.3 |
| 4 | `accessibilityLevel("auto")` 或 `"invalid"` | 静默转为 `"auto"` | AC-4.4 |
| 5 | `accessibilityImportance("yes")` | 与 `accessibilityLevel("yes")` 行为一致 | AC-4.6 |

---

**accessibilityRole**

| 属性 | 值 |
|------|-----|
| 函数签名 | `CommonMethod.accessibilityRole(role: AccessibilityRoleType \| undefined): this` |
| 返回值 | `this` — 支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1 ~ AC-5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| role | `AccessibilityRoleType \| undefined` | 否 | 组件自动判定 | 枚举值 0-124；超范围或非数字触发重置；`undefined` 重置 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `accessibilityRole(AccessibilityRoleType.BUTTON)` (5) | 映射为 `"Button"` 存储到 `accessibilityCustomRole_` | AC-5.1 |
| 2 | 传入非法枚举值 (如 999) | `GetRoleByType` 返回空，触发 reset | AC-5.3 |
| 3 | 传入非数字类型 | 声明式桥接检测后调用 reset | AC-5.4 |
| 4 | 未设置 | 使用组件标签自动判定的角色 | AC-5.5 |

---

## 兼容性声明

- **已有 API 行为变更:** 否 — 补录已有行为，无变更
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10
- **API 版本号策略:**
  - 以 SDK `.d.ts` 为 API 契约：`accessibilityText` @since 10, `accessibilityDescription` @since 10, `accessibilityGroup` @since 12, `accessibilityLevel` @since 11, `accessibilityRole` @since 18

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| 无障碍属性不参与标准属性更新管线 | 不使用 `PROPERTY_UPDATE_*` 标志，不触发测量/布局/渲染重算；通过 `NotifyComponentChangeEvent` → `pipeline->AddAccessibilityCallbackEvent` 通知无障碍子系统 | 全部 AC |
| 无障碍属性懒初始化 | `GetOrCreateAccessibilityProperty()` 在首次访问时创建，由 `pattern_->CreateAccessibilityProperty()` 决定子类类型 | AC-1.1 ~ AC-5.5 |
| 声明式与 Native 桥接行为不对称 | `accessibilityDescription` 的 JSON 侧信道和 `accessibilityGroup` 的 `AccessibilityOptions` 仅在声明式桥接中生效 | AC-2.2, AC-2.3, AC-3.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 无障碍属性设置不触发布局重算 | 代码审查 | 无 `PROPERTY_UPDATE_*` 标志 |
| 内存 | 无障碍属性对象懒初始化，未设置时不分配 | 代码审查 | `GetOrCreateAccessibilityProperty` 懒初始化 |
| 安全 | 无外部输入的安全风险（字符串为内部使用） | 代码审查 | 无敏感数据处理 |
| 可靠性 | `CHECK_NULL_VOID` 保护 FrameNode 空指针 | 代码审查 | `view_abstract_model_ng.cpp` |
| 可测试性 | 每个属性有独立 set/get 接口 | 单元测试 | `accessibility_property_test` |
| 自动化维测 | `TEXT_CHANGE` / `ELEMENT_INFO_CHANGE` 事件可追踪 | 代码审查 | Dump 机制支持 |
| 定界定位 | 每个属性独立，互不干扰 | 代码审查 | 独立成员变量和事件类型 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|---------|----------|---------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|---------|
| 无障碍 | 是 | 本特性即为无障碍能力的核心部分 | 全部 AC |
| 大字体 | 否 | 无障碍属性不涉及字体缩放 | — |
| 深色模式 | 否 | 无障碍属性不涉及颜色主题 | — |
| 多窗口/分屏 | 否 | 无障碍属性在窗口内独立生效 | — |
| 多用户 | 否 | 无障碍属性不涉及用户数据 | — |
| 版本升级 | 是 | SDK 版本差异见兼容性声明 | AC-1.1 ~ AC-5.5 |
| 生态兼容 | 否 | 无外部依赖 | — |

## 行为场景（可选，Gherkin）

> 本特性复杂度为"标准"（L1），使用"接口规格 → 行为场景"表已覆盖，无需 Gherkin。

## Spec 自审清单

- [ ] 无"待定""TBD""TODO"等占位符
- [ ] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [ ] 范围边界明确（做什么/不做什么清晰）
- [ ] 无语义模糊表述（"快速""稳定""尽可能"等）
- [ ] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [ ] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityProperty 类中 accessibilityText_/accessibilityDescription_/accessibilityGroup_/accessibilityLevel_/accessibilityCustomRole_ 的存储和事件通知机制"
  - repo: "openharmony/arkui_ace_engine"
    query: "GetGroupTextRecursive 和 GetSearchStrategy 中 accessibilityGroup 与 accessibilityLevel 的交互逻辑"
  - repo: "openharmony/interface_sdk-js"
    query: "common.static.d.ets 与 common.d.ts 中无障碍属性的 @since 版本差异原因"
```

**关键文档:**
- `frameworks/core/components_ng/property/accessibility_property.h` — 属性存储和接口定义
- `frameworks/core/components_ng/property/accessibility_property.cpp` — 属性设置/获取/事件通知实现
- `frameworks/bridge/declarative_frontend/jsview/js_accessibility.cpp` — 声明式 JS 桥接
- `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_common_bridge.cpp` — Native 桥接
- `frameworks/core/components_ng/base/view_abstract_model_ng.cpp` — NG 模型层
- `interface_sdk-js/api/arkui/component/common.static.d.ets` — Public Static SDK 类型定义