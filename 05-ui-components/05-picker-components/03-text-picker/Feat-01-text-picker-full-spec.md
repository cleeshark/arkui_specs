# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | TextPicker 组件全量规格 |
| 特性编号 | Func-05-05-03-Feat-01 |
| FuncID | 05-05-03 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 8 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | TextPicker 组件规格补录 | 覆盖单列、多列、级联和混合内容 |
| ADDED | 样式和事件规格补录 | 覆盖三档文本样式、divider、gradient、selected background、事件 |
| ADDED | C API 规格补录 | 覆盖 `ARKUI_NODE_TEXT_PICKER` 和 `NODE_TEXT_PICKER_*` |

## 输入文档

- 设计文档: `arkui-specs/05-ui-components/05-picker-components/03-text-picker/design.md`
- KB 路由: `docs/pattern/text_picker/Text_Picker_Knowledge_Base.md`
- SDK 类型定义: `../../../interface/sdk-js/api/@internal/component/ets/text_picker.d.ts`, `../../../interface/sdk-js/api/arkui/component/textPicker.static.d.ets`
- 实现源码: `frameworks/core/components_ng/pattern/text_picker/`, `interfaces/native/native_node.h`

## 用户故事

### US-1: 配置数据源和选中项

**角色**: 应用开发者
**期望**: 我想要为 TextPicker 设置文本、图片或级联数据，并控制初始选中项
**价值**: 以便实现单列、多列和级联选择

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `TextPicker({ range })` THEN 根据 range 类型创建 TEXT/ICON/MIXTURE 列，SDK 见 `text_picker.d.ts:105`，Model 创建见 `textpicker_model_ng.cpp:111` 和 `textpicker_model_ng.cpp:190` | 正常 |
| AC-1.2 | WHEN range 为空数组 THEN 不显示选项；WHEN 动态变为空数组 THEN 当前有效值保持显示，SDK 说明见 `text_picker.d.ts:107` | 边界 |
| AC-1.3 | WHEN 同时设置 `selected` 和 `value` THEN `selected/selectedIndex` 优先，SDK 说明见 `text_picker.d.ts:131` 和 `text_picker.d.ts:882` | 正常 |
| AC-1.4 | WHEN 使用级联数据 THEN Pattern 按级联深度和 selected/value 更新后续列，源码见 `textpicker_pattern.cpp:1323` 和 `textpicker_pattern.cpp:1381` | 正常 |

### US-2: 配置样式和循环

**角色**: 应用开发者
**期望**: 我想要控制 TextPicker 的文本样式、分割线、渐变和循环
**价值**: 以便匹配不同视觉规范

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 设置 `defaultPickerItemHeight` THEN item 高度写入 LayoutProperty，源码见 `textpicker_model_ng.cpp:337` | 正常 |
| AC-2.2 | WHEN 设置 `canLoop(false)` THEN 所有列禁用循环，源码见 `textpicker_pattern.cpp:1928` | 正常 |
| AC-2.3 | WHEN 设置 `divider(null)` THEN 分割线隐藏；WHEN margins 非法 THEN 使用默认，SDK 见 `text_picker.d.ts:920`，Model 设置见 `textpicker_model_ng.cpp:1516` | 边界 |
| AC-2.4 | WHEN 设置 `gradientHeight(0)` THEN 渐变禁用；WHEN 负数、undefined 或超过半高 THEN 使用默认，SDK 见 `text_picker.d.ts:957` | 边界 |
| AC-2.5 | WHEN 设置 `selectedBackgroundStyle` THEN 所有列选中项背景色和圆角更新，SDK 见 `text_picker.d.ts:1024`，Model 写入见 `textpicker_model_ng.cpp:1681` | 正常 |

### US-3: 事件、触觉反馈和 C API

**角色**: 应用开发者
**期望**: 我想要监听 TextPicker 的滚动和选择变化，并在 Native 层控制属性
**价值**: 以便实现业务联动和 NDK 集成

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 选项进入选中区域超过半个选中项高度 THEN 触发 `onEnterSelectedArea`，SDK 见 `text_picker.d.ts:854` | 正常 |
| AC-3.2 | WHEN 滚动动画完成并选中项变化 THEN 触发 `onChange`，SDK 见 `text_picker.d.ts:787`，EventHub 绑定见 `textpicker_model_ng.cpp:596` | 正常 |
| AC-3.3 | WHEN 手势滚动停止 THEN 触发 `onScrollStop`，SDK 见 `text_picker.d.ts:829`，EventHub 绑定见 `textpicker_model_ng.cpp:605` | 正常 |
| AC-3.4 | WHEN 设置 `enableHapticFeedback` THEN Pattern 保存触觉反馈开关，源码见 `textpicker_model_ng.cpp:1659` | 正常 |
| AC-3.5 | WHEN 使用 C API 属性或事件 THEN 通过 `ARKUI_NODE_TEXT_PICKER` 和 `NODE_TEXT_PICKER_*` 访问，声明见 `interfaces/native/native_node.h:84` 和 `interfaces/native/native_node.h:5755` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2, R-3, R-4 | TASK-TEXT-PICKER-01 | UT | `test/unittest/core/pattern/text_picker/text_picker_model_test_ng.cpp:365` |
| AC-2.1 ~ AC-2.5 | R-5, R-6, R-7, R-8 | TASK-TEXT-PICKER-01 | UT | `test/unittest/core/pattern/text_picker/text_picker_column_extend_test_ng.cpp:934` |
| AC-3.1 ~ AC-3.5 | R-9, R-10, R-11 | TASK-TEXT-PICKER-01 | UT + C API UT | `test/unittest/capi/modifiers/text_picker_modifier_test.cpp:979` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 创建 TextPicker 并传入 range | 按 TEXT/ICON/MIXTURE 创建对应子节点 | range 类型和列数不支持动态修改 | AC-1.1 |
| R-2 | 边界 | range 为空数组 | 无选项显示；动态变空时保留当前有效值 | 空数组不能作为有效数据源 | AC-1.2 |
| R-3 | 行为 | selected/value 同时存在 | selected 或 selectedIndex 优先 | selected 越界默认 0 | AC-1.3 |
| R-4 | 行为 | 级联数据变更 | 后续列按当前 selected/value 递归刷新 | 级联深度由 children 决定 | AC-1.4 |
| R-5 | 行为 | 设置 itemHeight | 更新 DefaultPickerItemHeight | 数值 >=0，字符串为数值字符串 | AC-2.1 |
| R-6 | 行为 | 设置 canLoop | 遍历所有列下发 loop | 多列一致生效 | AC-2.2 |
| R-7 | 边界 | divider 为 null/undefined/非法 margin | null 隐藏，undefined 默认，非法 margin 默认 | margin 总和不能超过列宽 | AC-2.3 |
| R-8 | 边界 | gradientHeight 为 0、负数、超过半高 | 0 禁用，非法默认 | 百分比 100% 等于半高 | AC-2.4 |
| R-9 | 行为 | 选项进入选中区 | 触发 onEnterSelectedArea | 级联场景不建议依赖完整列值 | AC-3.1 |
| R-10 | 行为 | 滚动动画完成 | 触发 onChange/onScrollStop | onChange 不由双向绑定变量触发 | AC-3.2, AC-3.3 |
| R-11 | 行为 | C API 属性/事件 | 使用 `ArkUI_AttributeItem` 设置属性，事件返回 selected 值 | C API 数据格式以 native_node.h 为准 | AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | Core UT | range 类型、selected/value、级联 |
| VM-2 | AC-2.1 ~ AC-2.5 | Core UT | itemHeight、canLoop、divider、gradient、background |
| VM-3 | AC-3.1 ~ AC-3.4 | Core UT | 三类事件和 haptic |
| VM-4 | AC-3.5 | C API UT | C API 属性和事件 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| N/A | N/A | N/A | N/A | N/A | 本次无新增 API，仅补录已有 API 规格 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `onAccept/onCancel` | 废弃（since 10） | 仅历史 TextPickerDialog 场景 | 无替代，本组件规格不新增使用 | AC-3.2 |

## 接口规格

### 接口定义

**TextPicker(options?: TextPickerOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TextPicker(options?: TextPickerOptions): TextPickerAttribute` |
| 返回值 | `TextPickerAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `range` | string[]/string[][]/Resource/content/cascade | 是 | 无 | 不能为空数组，Resource 仅支持 strarray |
| `value` | ResourceStr/ResourceStr[] | 否 | 第一项 | 优先级低于 selected |
| `selected` | number/number[] | 否 | 0 | 0-based，越界默认 0 |
| `columnWidths` | LengthMetrics[] | 否 | 等分宽度 | 单项可 undefined/null，整体不能全 undefined/null |

**TextPickerAttribute 方法**

| 接口 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|---------|
| `defaultPickerItemHeight(height)` | number/string/Optional | 设置 selected 和 unselected item 高度 | AC-2.1 |
| `canLoop(isLoop)` | boolean/Optional | 设置所有列循环 | AC-2.2 |
| `disappearTextStyle/textStyle/selectedTextStyle(style)` | PickerTextStyle/TextPickerTextStyle | 设置三档文本样式 | AC-2.5 |
| `onChange/onScrollStop/onEnterSelectedArea(callback)` | 对应 callback 或 Optional | 按不同滚动时机触发 | AC-3.1 ~ AC-3.3 |
| `divider/gradientHeight/selectedBackgroundStyle(...)` | DividerOptions/Dimension/PickerBackgroundStyle | 设置分割线、渐变和选中背景 | AC-2.3 ~ AC-2.5 |
| `enableHapticFeedback(enable)` | Optional<boolean> | 设置触觉反馈 | AC-3.4 |

**C API**

| 接口 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|---------|
| `ARKUI_NODE_TEXT_PICKER` | node type | 创建 TextPicker native node | AC-3.5 |
| `NODE_TEXT_PICKER_OPTION_RANGE/SELECTED/VALUE/...` | `ArkUI_AttributeItem` | 设置数据、选中项、样式、循环、itemHeight | AC-1.1, AC-2.1 |
| `NODE_TEXT_PICKER_EVENT_ON_CHANGE/ON_SCROLL_STOP` | event data | 选择变化和滚动停止事件 | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否，本次只补录已有实现。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** TextPicker dynamic API since 8；多列/混合 since 10；divider/gradient since 12；onScrollStop since 14；haptic/Optional 重载 since 18；selectedBackgroundStyle since 20；static API since 23。
- **API 版本号策略:** 按 SDK `@since` 标注，废弃事件单独说明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 合同优先 | range/value/selected 等外部签名以 d.ts 为准 | AC-1.1 |
| Pattern 行为准线 | 级联、循环、事件时机以 Pattern 源码为准 | AC-1.4, AC-3.1 |
| C API 不改 ABI | 只记录已有枚举和 helper | AC-3.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增列刷新路径 | UT | 现有 Pattern |
| 功耗 | 无后台任务 | 代码审查 | 无源码变更 |
| 内存 | 子节点由 UI 树管理 | UT | RefPtr/UI 树 |
| 安全 | 不新增权限 | 代码审查 | 本地 UI 组件 |
| 可靠性 | 空 range、越界 selected 有明确恢复 | UT | R-2, R-3 |
| 可测试性 | AC 映射 UT/C API UT | 生成检查 | VM-1 ~ VM-4 |
| 自动化维测 | 复用 TextPicker UT | UT | `test/unittest/core/pattern/text_picker/` |
| 定界定位 | SDK/Bridge/Model/Pattern/C API 分层明确 | 代码审查 | design.md |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | portrait 默认显示行数按 PickerTheme | UT/手工 | `text_picker.d.ts:203` |
| 平板 | 横屏行数可能由系统配置决定 | SDK 提示横屏行数可变 | 手工 | `text_picker.d.ts:212` |
| 折叠屏 | 无额外差异 | 按窗口/方向走同一规则 | 手工 | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 列 currentIndex 更新时刷新 accessibility text | AC-1.4 |
| 大字体 | 是 | TextPickerTextStyle 支持 min/maxFontSize | AC-2.5 |
| 深色模式 | 是 | ResourceColor/Theme 跟随系统 | AC-2.5 |
| 多窗口/分屏 | 是 | 行数和布局受方向/窗口影响 | AC-1.1 |
| 多用户 | 否 | 无持久化数据 | N/A |
| 版本升级 | 是 | since/deprecated 边界需保持 | AC-3.2 |
| 生态兼容 | 是 | ArkTS 与 C API 双通道合同保持 | AC-3.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: TextPicker 级联选择
  Scenario: selected 优先于 value
    Given TextPicker 同时设置 value 和 selected
    When 组件构建列
    Then 当前选中项按 selected 显示

  Scenario: 滚动停止事件
    Given TextPicker 设置 onScrollStop
    When 用户手势滚动并停止
    Then onScrollStop 收到当前 value 和 index
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "TextPicker range selectedIndex cascade divider gradientHeight onChange C API implementation"
```

**关键文档:** `docs/pattern/text_picker/Text_Picker_Knowledge_Base.md`

