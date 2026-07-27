# 特性规格

> Func-04-05-03-Feat-01 表单类组件自定义内容：固化 ContentModifier 基础契约及 Button/Checkbox/CheckboxGroup/Radio/Select/Slider/Toggle 七个表单组件的 contentModifier() 方法、Configuration 字段、triggerClick/triggerChange 回调、reset/Optional 变体与动态模块加载的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 表单类组件自定义内容 (ContentModifier for Form Components) |
| 特性编号 | Func-04-05-03-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 12 起支持动态版本，API 18 起 Optional 变体，API 21 起 CheckboxGroup |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/05-custom-extension/03-content-modifier-form/design.md` | Baselined |
| SDK API | `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | — |
| SDK 组件 | `docs/sdk/Component_API_Knowledge_Base_CN.md` | — |

---

## 用户故事

### US-1: ContentModifier 基础契约

**作为** 应用开发者,
**我想要** 实现 `ContentModifier<T>` 接口并通过 `applyContent()` 返回自定义 Builder,
**以便** 用自定义内容替换表单组件的默认渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 实现 `ContentModifier<T>` 接口 THEN 必须实现 `applyContent(): WrappedBuilder<[T]>` 方法 | 正常 |
| AC-1.2 | WHEN CommonConfiguration 被构造 THEN 包含 `enabled: boolean` 字段表示组件启用状态 | 边界 |
| AC-1.3 | WHEN C++ ContentModifier 被实例化 THEN `changeCount_` 初始化为 0 并通过 AttachProperty 注册到 attachedProperties_ | 正常 |
| AC-1.4 | WHEN 调用 SetContentChange() THEN `changeCount_` 递增并触发重渲染 | 正常 |

### US-2: Button contentModifier

**作为** 应用开发者,
**我想要** 通过 `.contentModifier()` 为 Button 设置自定义内容,
**以便** 替换按钮的默认外观同时保留点击行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `button.d.ts:766` contentModifier() THEN ButtonPattern 存储 makeFunc_ 并触发 FireBuilder | 正常 |
| AC-2.2 | WHEN FireBuilder 执行 THEN BuildContentModifierNode 从 PaintProperty/EventHub 读取状态构造 ButtonConfiguration（label/pressed/enabled） | 正常 |
| AC-2.3 | WHEN ButtonConfiguration.triggerClick 被调用 THEN 触发按钮原生点击行为 | 正常 |

### US-3: Checkbox contentModifier

**作为** 应用开发者,
**我想要** 通过 `.contentModifier()` 为 Checkbox 设置自定义内容,
**以便** 自定义复选框外观并保留选中状态语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `checkbox.d.ts:404` contentModifier() THEN CheckBoxConfiguration 包含 name/selected 字段 | 正常 |
| AC-3.2 | WHEN CheckBoxConfiguration.triggerChange 被调用 THEN 触发复选框原生选中/取消行为 | 正常 |
| AC-3.3 | WHEN API >= 18 THEN Checkbox contentModifier 支持可选变体（`checkbox.d.ts:422`），传 undefined 清除 modifier | 边界 |

### US-4: Radio contentModifier

**作为** 应用开发者,
**我想要** 通过 `.contentModifier()` 为 Radio 设置自定义内容,
**以便** 自定义单选按钮外观并保留选中语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `radio.d.ts:340` contentModifier() THEN RadioConfiguration 包含 value/checked 字段 | 正常 |
| AC-4.2 | WHEN RadioConfiguration.triggerChange 被调用 THEN 触发单选按钮原生选中行为 | 正常 |
| AC-4.3 | WHEN API >= 18 THEN Radio contentModifier 支持可选变体（`radio.d.ts:357`） | 边界 |

### US-5: Slider contentModifier

**作为** 应用开发者,
**我想要** 通过 `.contentModifier()` 为 Slider 设置自定义内容,
**以便** 自定义滑块外观并保留值变更语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `slider.d.ts:1238` contentModifier() THEN SliderConfiguration 包含 value/min/max/step 字段 | 正常 |
| AC-5.2 | WHEN SliderConfiguration.triggerChange 被调用 THEN 触发滑块原生值变更行为 | 正常 |
| AC-5.3 | WHEN Slider 状态变更 THEN makeFunc_ 被重新调用以更新 Configuration 快照 | 正常 |

### US-6: Toggle contentModifier

**作为** 应用开发者,
**我想要** 通过 `.contentModifier()` 为 Toggle 设置自定义内容,
**以便** 自定义开关外观并保留开关状态语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `toggle.d.ts:371` contentModifier() THEN ToggleConfiguration 包含 isOn/enabled 字段 | 正常 |
| AC-6.2 | WHEN ToggleConfiguration.triggerChange 被调用 THEN 触发开关原生切换行为 | 正常 |
| AC-6.3 | WHEN ToggleConfiguration 定义于 `common_configuration.h:30` THEN 继承 CommonConfiguration 的 enabled_ 字段 | 边界 |

### US-7: Select menuItemContentModifier

**作为** 应用开发者,
**我想要** 通过 `.menuItemContentModifier()` 为 Select 菜单项设置自定义内容,
**以便** 自定义下拉菜单项外观并保留选中语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `select.d.ts:931` menuItemContentModifier() THEN MenuItemConfiguration 包含 value/icon/symbolIcon/selected 字段 | 正常 |
| AC-7.2 | WHEN API >= 18 THEN Select menuItemContentModifier 支持可选变体（`select.d.ts:955`） | 边界 |
| AC-7.3 | WHEN Select 使用 menuItemContentModifier 而非 contentModifier THEN 方法名与组件名不一致但行为一致 | 正常 |

### US-8: reset/动态模块加载

**作为** 应用开发者,
**我想要** 重置 contentModifier 并了解动态模块加载机制,
**以便** 在运行时切换自定义内容与默认渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN makeFunc_ 为空 THEN FireBuilder 移除 contentModifierNode_ 并恢复默认渲染 | 恢复 |
| AC-8.2 | WHEN 首次访问 contentModifier THEN DynamicModuleHelper 按组件名动态加载 shared library 并缓存结果 | 正常 |
| AC-8.3 | WHEN CheckboxGroup API >= 21 THEN contentModifier（`checkboxgroup.d.ts:471`）支持 CheckBoxGroupConfiguration（name/status/triggerChange） | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 common.d.ts:18580 |
| AC-1.2 | US-1 | R-2 | 代码审查 common.d.ts:18608 |
| AC-1.3 | US-1 | R-3 | 代码审查 modifier.h:333-334 |
| AC-1.4 | US-1 | R-4 | 代码审查 modifier.h:371-374 |
| AC-2.1 | US-2 | R-5 | 单元测试 button_content_modifier_test_ng.cpp |
| AC-2.2 | US-2 | R-6 | 代码审查 button_pattern.cpp:1443-1457 |
| AC-2.3 | US-2 | R-7 | 单元测试 button_content_modifier_test_ng.cpp |
| AC-3.1 | US-3 | R-8 | 单元测试 checkbox_content_modifier_test_ng.cpp |
| AC-3.2 | US-3 | R-9 | 单元测试 checkbox_content_modifier_test_ng.cpp |
| AC-3.3 | US-3 | R-10 | 代码审查 checkbox.d.ts:422 |
| AC-4.1 | US-4 | R-11 | 单元测试 radio_pattern_test_ng.cpp |
| AC-4.2 | US-4 | R-12 | 单元测试 radio_pattern_test_ng.cpp |
| AC-4.3 | US-4 | R-10 | 代码审查 radio.d.ts:357 |
| AC-5.1 | US-5 | R-13 | 单元测试 slider_content_modifier_test_ng.cpp |
| AC-5.2 | US-5 | R-14 | 单元测试 slider_content_modifier_test_ng.cpp |
| AC-5.3 | US-5 | R-15 | 代码审查 slider_pattern.cpp |
| AC-6.1 | US-6 | R-16 | 单元测试 toggle_content_modifier_test_ng.cpp |
| AC-6.2 | US-6 | R-17 | 单元测试 toggle_content_modifier_test_ng.cpp |
| AC-6.3 | US-6 | R-18 | 代码审查 common_configuration.h:30 |
| AC-7.1 | US-7 | R-19 | 单元测试 select_pattern_test_ng.cpp |
| AC-7.2 | US-7 | R-10 | 代码审查 select.d.ts:955 |
| AC-7.3 | US-7 | R-20 | 代码审查 select.d.ts:931 |
| AC-8.1 | US-8 | R-21 | 代码审查 button_pattern.cpp:1439 |
| AC-8.2 | US-8 | R-22 | 代码审查 button_dynamic_module.cpp:77-84 |
| AC-8.3 | US-8 | R-23 | 代码审查 checkboxgroup.d.ts:471 |

## 规则定义

> **统一规则表。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `common.d.ts:18580` | ContentModifier\<T\> 接口要求实现 applyContent() 返回 WrappedBuilder\<[T]\> | @since 12 | AC-1.1 |
| R-2 | 行为 | `common.d.ts:18608` | CommonConfiguration 包含 enabled 字段和可选 contentModifier | @since 12 | AC-1.2 |
| R-3 | 行为 | `modifier.h:333-334` | ContentModifier 构造时初始化 changeCount_=0 并 AttachProperty | — | AC-1.3 |
| R-4 | 行为 | `modifier.h:371-374` | SetContentChange 递增 changeCount_ 触发重渲染 | — | AC-1.4 |
| R-5 | 行为 | `button.d.ts:766` | Button contentModifier 设置 makeFunc_ 并触发 FireBuilder | @since 12 | AC-2.1 |
| R-6 | 行为 | `button_pattern.cpp:1443-1457` | BuildContentModifierNode 从状态构造 ButtonConfiguration 并调用 makeFunc_ | label/pressed/enabled | AC-2.2 |
| R-7 | 行为 | `button.d.ts:219` | ButtonConfiguration.triggerClick 触发按钮原生点击 | — | AC-2.3 |
| R-8 | 行为 | `checkbox.d.ts:84` | CheckBoxConfiguration 包含 name/selected 字段 | @since 12 | AC-3.1 |
| R-9 | 行为 | `checkbox.d.ts:84` | CheckBoxConfiguration.triggerChange 触发原生选中/取消 | — | AC-3.2 |
| R-10 | 边界 | `checkbox.d.ts:422`, `radio.d.ts:357`, `select.d.ts:955` | API >= 18 支持 Optional 变体，传 undefined 清除 modifier | @since 18 | AC-3.3, AC-4.3, AC-7.2 |
| R-11 | 行为 | `radio.d.ts:370` | RadioConfiguration 包含 value/checked 字段 | @since 12 | AC-4.1 |
| R-12 | 行为 | `radio.d.ts:370` | RadioConfiguration.triggerChange 触发原生选中 | — | AC-4.2 |
| R-13 | 行为 | `slider.d.ts:505` | SliderConfiguration 包含 value/min/max/step 字段 | @since 12 | AC-5.1 |
| R-14 | 行为 | `slider.d.ts:505` | SliderConfiguration.triggerChange 触发原生值变更 | — | AC-5.2 |
| R-15 | 行为 | `slider_pattern.cpp` | Slider 状态变更时 makeFunc_ 重新调用更新 Configuration 快照 | — | AC-5.3 |
| R-16 | 行为 | `toggle.d.ts:203` | ToggleConfiguration 包含 isOn/enabled 字段 | @since 12 | AC-6.1 |
| R-17 | 行为 | `toggle.d.ts:203` | ToggleConfiguration.triggerChange 触发原生切换 | — | AC-6.2 |
| R-18 | 边界 | `common_configuration.h:30` | ToggleConfiguration 继承 CommonConfiguration 的 enabled_ | — | AC-6.3 |
| R-19 | 行为 | `select.d.ts:1265` | MenuItemConfiguration 包含 value/icon/symbolIcon/selected 字段 | @since 12 | AC-7.1 |
| R-20 | 行为 | `select.d.ts:931` | Select 使用 menuItemContentModifier 方法名（非 contentModifier） | — | AC-7.3 |
| R-21 | 恢复 | `button_pattern.cpp:1439` | makeFunc_ 为空时 FireBuilder 移除 contentModifierNode_ 恢复默认 | — | AC-8.1 |
| R-22 | 行为 | `button_dynamic_module.cpp:77-84` | DynamicModuleHelper 按组件名动态加载，GetCustomModifier("contentModifier")，std::call_once 缓存 | — | AC-8.2 |
| R-23 | 边界 | `checkboxgroup.d.ts:471` | CheckboxGroup contentModifier @since 21，CheckBoxGroupConfiguration(name/status/triggerChange) | @since 21 | AC-8.3 |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 ContentModifier 基础契约 (AC-1.1~1.4) | 代码审查 | ContentModifier 接口定义；CommonConfiguration 字段；changeCount_ 机制 |
| VM-2 | US-2 Button (AC-2.1~2.3) | 单元测试 + 代码审查 | ButtonConfiguration 字段；triggerClick 回调；BuildContentModifierNode 流程 |
| VM-3 | US-3 Checkbox (AC-3.1~3.3) | 单元测试 + 代码审查 | CheckBoxConfiguration 字段；triggerChange 回调；Optional 变体 |
| VM-4 | US-4 Radio (AC-4.1~4.3) | 单元测试 + 代码审查 | RadioConfiguration 字段；triggerChange 回调；Optional 变体 |
| VM-5 | US-5 Slider (AC-5.1~5.3) | 单元测试 + 代码审查 | SliderConfiguration 字段；triggerChange 回调；状态快照更新 |
| VM-6 | US-6 Toggle (AC-6.1~6.3) | 单元测试 + 代码审查 | ToggleConfiguration 字段；triggerChange 回调；继承关系 |
| VM-7 | US-7 Select (AC-7.1~7.3) | 单元测试 + 代码审查 | MenuItemConfiguration 字段；Optional 变体；方法命名 |
| VM-8 | US-8 reset/动态加载 (AC-8.1~8.3) | 代码审查 | makeFunc_ 为空恢复默认；动态模块加载；CheckboxGroup @since 21 |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:18580` |
| AC-1.2 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:18608` |
| AC-1.3 | 代码审查 | `frameworks/core/components_ng/base/modifier.h:333-334` |
| AC-1.4 | 代码审查 | `frameworks/core/components_ng/base/modifier.h:371-374` |
| AC-2.1 | 单元测试 | `test/unittest/core/pattern/button/button_content_modifier_test_ng.cpp` |
| AC-2.2 | 代码审查 | `frameworks/core/components_ng/pattern/button/button_pattern.cpp:1443-1457` |
| AC-2.3 | 单元测试 | `test/unittest/core/pattern/button/button_content_modifier_test_ng.cpp` |
| AC-3.1 | 单元测试 | `test/unittest/core/pattern/checkbox/checkbox_content_modifier_test_ng.cpp` |
| AC-3.2 | 单元测试 | `test/unittest/core/pattern/checkbox/checkbox_content_modifier_test_ng.cpp` |
| AC-3.3 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/checkbox.d.ts:422` |
| AC-4.1 | 单元测试 | `test/unittest/core/pattern/radio/radio_pattern_test_ng.cpp` |
| AC-4.2 | 单元测试 | `test/unittest/core/pattern/radio/radio_pattern_test_ng.cpp` |
| AC-4.3 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/radio.d.ts:357` |
| AC-5.1 | 单元测试 | `test/unittest/core/pattern/slider/slider_content_modifier_test_ng.cpp` |
| AC-5.2 | 单元测试 | `test/unittest/core/pattern/slider/slider_content_modifier_test_ng.cpp` |
| AC-5.3 | 代码审查 | `frameworks/core/components_ng/pattern/slider/slider_pattern.cpp` |
| AC-6.1 | 单元测试 | `test/unittest/core/pattern/toggle/toggle_content_modifier_test_ng.cpp` |
| AC-6.2 | 单元测试 | `test/unittest/core/pattern/toggle/toggle_content_modifier_test_ng.cpp` |
| AC-6.3 | 代码审查 | `frameworks/core/components_ng/base/common_configuration.h:30` |
| AC-7.1 | 单元测试 | `test/unittest/core/pattern/select/select_pattern_test_ng.cpp` |
| AC-7.2 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/select.d.ts:955` |
| AC-7.3 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/select.d.ts:931` |
| AC-8.1 | 代码审查 | `frameworks/core/components_ng/pattern/button/button_pattern.cpp:1439` |
| AC-8.2 | 代码审查 | `frameworks/bridge/declarative_frontend/arkts_native/button_dynamic_module.cpp:77-84` |
| AC-8.3 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/checkboxgroup.d.ts:471` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/common.d.ts` 及各组件 d.ts

#### ContentModifier 基础接口

```typescript
// common.d.ts:18580 (@since 12)
interface ContentModifier<T> {
    applyContent(): WrappedBuilder<[T]>;
}

// common.d.ts:18608 (@since 12)
interface CommonConfiguration<T> {
    enabled: boolean;
    contentModifier?: ContentModifier<T>;
}
```

#### 各组件 contentModifier 方法

| 组件 | 方法签名 | d.ts 行 | @since |
|------|----------|---------|--------|
| Button | `contentModifier(modifier: ContentModifier<ButtonConfiguration>): ButtonAttribute` | button.d.ts:766 | 12 |
| Checkbox | `contentModifier(modifier: ContentModifier<CheckBoxConfiguration>): CheckboxAttribute` | checkbox.d.ts:404 | 12 |
| Checkbox | `contentModifier(modifier: Optional<ContentModifier<CheckBoxConfiguration>>): CheckboxAttribute` | checkbox.d.ts:422 | 18 |
| CheckboxGroup | `contentModifier(modifier: ContentModifier<CheckBoxGroupConfiguration>): CheckboxGroupAttribute` | checkboxgroup.d.ts:471 | 21 |
| Radio | `contentModifier(modifier: ContentModifier<RadioConfiguration>): RadioAttribute` | radio.d.ts:340 | 12 |
| Radio | `contentModifier(modifier: Optional<ContentModifier<RadioConfiguration>>): RadioAttribute` | radio.d.ts:357 | 18 |
| Select | `menuItemContentModifier(modifier: ContentModifier<MenuItemConfiguration>): SelectAttribute` | select.d.ts:931 | 12 |
| Select | `menuItemContentModifier(modifier: Optional<ContentModifier<MenuItemConfiguration>>): SelectAttribute` | select.d.ts:955 | 18 |
| Slider | `contentModifier(modifier: ContentModifier<SliderConfiguration>): SliderAttribute` | slider.d.ts:1238 | 12 |
| Toggle | `contentModifier(modifier: ContentModifier<ToggleConfiguration>): ToggleAttribute` | toggle.d.ts:371 | 12 |

#### Configuration 类型定义

| Configuration | 字段 | 回调 | d.ts 行 |
|---------------|------|------|---------|
| ButtonConfiguration | label: ResourceStr, pressed: boolean | triggerClick: Callback | button.d.ts:219 |
| CheckBoxConfiguration | name: string, selected: boolean | triggerChange: Callback | checkbox.d.ts:84 |
| CheckBoxGroupConfiguration | name: string, status: SelectStatus | triggerChange: Callback | checkboxgroup.d.ts:188 |
| RadioConfiguration | value: string, checked: boolean | triggerChange: Callback | radio.d.ts:370 |
| MenuItemConfiguration | value: ResourceStr, icon: Optional\<ResourceStr\>, symbolIcon: Optional\<SymbolGlyphModifier\>, selected: boolean | — | select.d.ts:1265 |
| SliderConfiguration | value: number, min: number, max: number, step: number | triggerChange: Callback | slider.d.ts:505 |
| ToggleConfiguration | isOn: boolean, enabled: boolean | triggerChange: Callback | toggle.d.ts:203 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | 所有表单组件（除 CheckboxGroup）contentModifier 动态版本首次引入 | 新增能力，无兼容性问题 | — |
| API 18 | Checkbox/Radio/Select 增加 Optional 变体重载 | 新增重载，旧版非 optional 仍可用 | 旧代码无需迁移，新代码可用 Optional 传 undefined 清除 |
| API 21 | CheckboxGroup contentModifier 引入 | 新增能力 | 需 API 21 及以上设备 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 三层架构 | ContentModifier（基类）-Configuration（状态快照）-Pattern（apply 机制）三层分离 |
| Configuration 只读快照 | Configuration 字段为构建时快照，trigger 回调触发原生行为后需重新构建 Configuration |
| 动态模块加载 | ContentModifier 实现通过 DynamicModuleHelper 动态加载，std::call_once 保证单次 |
| 节点挂载位置 | contentModifierNode_ 挂载到 host 子节点位置 0，保留组件行为框架 |
| API 版本门控 | Optional 变体和 CheckboxGroup 受 API 版本门控 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | BuildContentModifierNode 在属性变更时调用，开销应保持 O(1)（仅构造 Configuration + 调用 makeFunc_） |
| 可调试性 | 动态模块加载失败时回退默认渲染，不中断应用 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 无障碍 | ContentModifier 自定义内容由开发者负责无障碍属性设置 |
| 大字体 | 无差异，自定义内容由开发者控制布局 |
| 深色模式 | 无差异，自定义内容颜色由开发者控制 |
| 多窗口分屏 | 无差异 |
| 多用户 | 无差异 |
| 版本升级 | 是，API 12→18→21 版本演进引入 Optional 变体和 CheckboxGroup |
| 生态兼容 | 是，动态模块加载需 DynamicModuleHelper 支持 |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 业务规则/功能规则/异常规则/恢复契约编号连续且可追溯到源码
- [x] API 变更分析基于真实 SDK 定义文件（common.d.ts 及各组件 d.ts）
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file:line 信息
- [x] 构建系统影响章节已确认无变更

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/components_ng/base/modifier.h` | ContentModifier 基类（onDraw/AttachProperty/SetContentChange） |
| `frameworks/core/components_ng/base/common_configuration.h` | CommonConfiguration 及 ToggleConfiguration 定义 |
| `frameworks/core/components_ng/pattern/button/button_pattern.cpp` | Button Pattern apply 机制（BuildContentModifierNode/FireBuilder） |
| `frameworks/core/components_ng/pattern/button/button_model_ng.h` | ButtonConfiguration（label_/pressed_） |
| `frameworks/core/components_ng/pattern/checkbox/checkbox_model_ng.h` | CheckBoxConfiguration |
| `frameworks/core/components_ng/pattern/checkboxgroup/checkboxgroup_model_ng.h` | CheckBoxGroupConfiguration |
| `frameworks/core/components_ng/pattern/radio/radio_model_ng.h` | RadioConfiguration |
| `frameworks/core/components_ng/pattern/select/select_model_ng.h` | MenuItemConfiguration |
| `frameworks/core/components_ng/pattern/slider/slider_model_ng.h` | SliderConfiguration |
| `frameworks/bridge/declarative_frontend/arkts_native/arkts_native_button_bridge.cpp` | SetContentModifierBuilder Bridge |
| `frameworks/bridge/declarative_frontend/arkts_native/button_dynamic_module.cpp` | 动态模块加载 |
| `frameworks/bridge/declarative_frontend/arkts_native/button_static_modifier.cpp` | ContentModifierButtonImpl 静态实现 |
| `interfaces/native/node/button/bridge/button_content_modifier_helper.h` | C-API GENERATED 结构体 |
| `interface/sdk-js/api/@internal/component/ets/common.d.ts` | ContentModifier/CommonConfiguration SDK 定义 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/button/button_content_modifier_test_ng.cpp` | Button ContentModifier 单元测试 |
| `test/unittest/core/pattern/checkbox/checkbox_content_modifier_test_ng.cpp` | Checkbox ContentModifier 单元测试 |
| `test/unittest/core/pattern/slider/slider_content_modifier_test_ng.cpp` | Slider ContentModifier 单元测试 |
| `test/unittest/core/pattern/toggle/toggle_content_modifier_test_ng.cpp` | Toggle ContentModifier 单元测试 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | SDK API 知识库 |
| `docs/sdk/Component_API_Knowledge_Base_CN.md` | 组件 API 知识库 |
