# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | UIPickerComponent/Picker 组件全量规格 |
| 特性编号 | Feat-01 |
| FuncID | 05-05-06 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 22 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | UIPickerComponent/Picker 规格补录 | 覆盖 API 名称、ContainerPicker 实现映射、子组件限制 |
| ADDED | 滚轮参数和事件规格补录 | 覆盖 selectedIndex、loop、haptic、indicator、itemHeight、displayedItemCount |
| ADDED | C API 规格补录 | 覆盖 `ARKUI_NODE_PICKER` 和 `NODE_PICKER_*` |

## 输入文档

- 设计文档: `arkui-specs/05-ui-components/05-picker-components/06-picker/design.md`
- KB 路由: `docs/pattern/container_picker/Container_Picker_Knowledge_Base.md`
- SDK 类型定义: `../../../interface/sdk-js/api/@internal/component/ets/ui_picker_component.d.ts`, `../../../interface/sdk-js/api/arkui/component/uiPickerComponent.static.d.ets`
- 实现源码: `frameworks/core/components_ng/pattern/container_picker/`, `frameworks/bridge/declarative_frontend/jsview/js_container_picker.cpp`, `interfaces/native/native_node.h`

## 用户故事

### US-1: 创建 UIPickerComponent 并承载子组件

**角色**: 应用开发者
**期望**: 我想要使用 UIPickerComponent 承载有限选项并通过 selectedIndex 指定初始项
**价值**: 以便构建自定义内容的滚轮选择器

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `UIPickerComponent(options?: UIPickerComponentOptions)` THEN JS binding 使用 `"UIPickerComponent"`，实现节点为 ContainerPicker，SDK 见 `ui_picker_component.d.ts:91`，绑定见 `js_container_picker.cpp:276` | 正常 |
| AC-1.2 | WHEN 设置 `selectedIndex` 为合法整数 THEN 选中对应 child；WHEN 越界 THEN 默认 0；WHEN 为小数 THEN 向下取整，SDK 见 `ui_picker_component.d.ts:30` | 边界 |
| AC-1.3 | WHEN 子组件为 Text、Image、Row、SymbolGlyph THEN 支持显示；WHEN Row 内包含非 Text/Image/SymbolGlyph 基础组件 THEN 可能影响显示或滑动，SDK 限制见 `ui_picker_component.d.ts:496` | 正常 |
| AC-1.4 | WHEN 未设置高度 THEN 推荐高度 200vp，子项默认 40vp 且最多 7 项完整显示，SDK 见 `ui_picker_component.d.ts:55`，常量见 `container_picker_utils.h:35` | 正常 |

### US-2: 配置滚轮参数和选择指示器

**角色**: 应用开发者
**期望**: 我想要配置 UIPickerComponent 的循环、触觉反馈、选中指示器、显示项数和 item 高度
**价值**: 以便调整滚轮体验和视觉样式

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 设置 `canLoop(undefined)` THEN 默认 true；WHEN 子组件数量少于 8 THEN 不发生循环滚动，SDK 见 `ui_picker_component.d.ts:378` | 边界 |
| AC-2.2 | WHEN 设置 `enableHapticFeedback(undefined)` THEN 默认 true；是否生效取决于硬件支持和应用权限，SDK 见 `ui_picker_component.d.ts:399` | 正常 |
| AC-2.3 | WHEN 设置 `displayedItemCount` 为 2~9 的偶数 THEN 归一化为下一个奇数；WHEN 越界 THEN 回 7，源码见 `container_picker_utils.h:81` | 边界 |
| AC-2.4 | WHEN 设置 `itemHeight` 小于 40vp 或大于 64vp THEN 回 40vp，源码见 `container_picker_utils.h:94` | 边界 |
| AC-2.5 | WHEN 设置 `selectionIndicator` 为 BACKGROUND 或 DIVIDER THEN 对应背景或分割线属性写入 LayoutProperty，Model 见 `container_picker_model.cpp:103` | 正常 |

### US-3: 事件和 C API

**角色**: 应用开发者
**期望**: 我想要监听 UIPickerComponent 选中项变化和滚动停止，并通过 Native 层使用 Picker
**价值**: 以便完成业务联动和 NDK 集成

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 中间项变化且不同于当前 selectedIndex THEN 触发 `onChange(selectedIndex)`，SDK 见 `ui_picker_component.d.ts:337`，Pattern 见 `container_picker_pattern.cpp:413` | 正常 |
| AC-3.2 | WHEN 滚动动画结束且未被打断 THEN 触发 `onScrollStop(selectedIndex)`，SDK 见 `ui_picker_component.d.ts:361`，Pattern 见 `container_picker_pattern.cpp:426` | 正常 |
| AC-3.3 | WHEN 使用 C API `ARKUI_NODE_PICKER` THEN 通过 `NODE_PICKER_*` 设置 selectedIndex、haptic、loop、selectionIndicator、displayedItemCount、itemHeight，声明见 `interfaces/native/native_node.h:155` 和 `interfaces/native/native_node.h:9434` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2, R-3 | TASK-UIPICKER-01 | UT | `test/unittest/core/pattern/container_picker/container_picker_model_test.cpp:2559` |
| AC-2.1 ~ AC-2.5 | R-4, R-5, R-6, R-7 | TASK-UIPICKER-01 | UT | `test/unittest/core/pattern/container_picker/container_picker_supplement_test.cpp:104` |
| AC-3.1 ~ AC-3.3 | R-8, R-9 | TASK-UIPICKER-01 | UT | `test/unittest/core/pattern/container_picker/container_picker_event_hub_test.cpp:78` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 UIPickerComponent | JS binding 名称为 `UIPickerComponent`，实现为 ContainerPicker | 此代码在 ace_engine 中未找到独立 `UIComponentPicker` 符号 | AC-1.1 |
| R-2 | 边界 | selectedIndex 合法/越界/小数 | 合法选中对应 child，越界默认 0，小数向下取整 | 0 ~ childCount - 1 | AC-1.2 |
| R-3 | 行为 | 子组件为 SDK 支持类型 | 支持 Text/Image/Row/SymbolGlyph 和 if/else/ForEach | 当前不支持 wearables | AC-1.3, AC-1.4 |
| R-4 | 边界 | canLoop=true 但 childCount < 8 | 不发生循环滚动 | 默认 true 仍受 child 数限制 | AC-2.1 |
| R-5 | 行为 | enableHapticFeedback 设置 | 写入 LayoutProperty，硬件支持时产生触觉反馈 | 默认 true | AC-2.2 |
| R-6 | 边界 | displayedItemCount 为 2~9、偶数、越界 | 2~9 有效，偶数 +1，越界 7 | 最大 9 | AC-2.3 |
| R-7 | 边界 | itemHeight 为 40~64vp 外 | 越界恢复 40vp | 合法范围 40vp ~ 64vp | AC-2.4 |
| R-8 | 行为 | 中间项变化 | 触发 onChange | callback undefined 时不使用 | AC-3.1 |
| R-9 | 行为 | 滚动动画结束 | 未打断时触发 onScrollStop | animationBreak 时不触发 | AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | Core UT | API/实现映射、selectedIndex、子组件限制 |
| VM-2 | AC-2.1 ~ AC-2.5 | Core UT | loop、haptic、indicator、count、height |
| VM-3 | AC-3.1 ~ AC-3.2 | Core UT | onChange/onScrollStop |
| VM-4 | AC-3.3 | 静态检查 + 后续测试补齐 | C API 枚举和测试缺口 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| N/A | N/A | N/A | N/A | N/A | 本次无新增 API，仅补录已有 API 规格 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| N/A | N/A | 本次无 API 声明变更或废弃 | N/A | AC-1.1 |

## 接口规格

### 接口定义

**UIPickerComponent(options?: UIPickerComponentOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIPickerComponent(options?: UIPickerComponentOptions): UIPickerComponentAttribute` |
| 返回值 | `UIPickerComponentAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `selectedIndex` | number | 否 | 0 | 0 ~ childCount - 1，小数向下取整，越界默认 0 |

**UIPickerComponentAttribute 方法**

| 接口 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|---------|
| `onChange(callback)` | Optional callback | 中间项变化时触发 | AC-3.1 |
| `onScrollStop(callback)` | Optional callback | 滚动结束且未打断时触发 | AC-3.2 |
| `canLoop(isLoop)` | Optional<boolean> | 控制循环，子项少于 8 不循环 | AC-2.1 |
| `enableHapticFeedback(enable)` | Optional<boolean> | 控制触觉反馈 | AC-2.2 |
| `selectionIndicator(style)` | PickerIndicatorStyle | BACKGROUND 或 DIVIDER | AC-2.5 |
| `itemHeight(height)` | LengthMetrics Optional | 40vp ~ 64vp | AC-2.4 |
| `displayedItemCount(count)` | int Optional | 2 ~ 9，偶数归一化 | AC-2.3 |

**C API**

| 接口 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|---------|
| `ARKUI_NODE_PICKER` | node type | 创建 Picker native node | AC-3.3 |
| `NODE_PICKER_OPTION_SELECTED_INDEX/ENABLE_HAPTIC_FEEDBACK/CAN_LOOP/SELECTION_INDICATOR/DISPLAYED_ITEM_COUNT/ITEM_HEIGHT` | `ArkUI_AttributeItem` | 设置或读取 Picker 属性 | AC-3.3 |
| `NODE_PICKER_EVENT_ON_CHANGE/ON_SCROLL_STOP` | event data | 选择变化和滚动停止事件 | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否，本次只补录已有实现。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** UIPickerComponent dynamic API since 22；C API node since 23；itemHeight/displayedItemCount dynamic since 26；static API since 23/26。
- **API 版本号策略:** 按 SDK `@since` 和 C API 注释记录。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 名称映射必须明确 | `UIPickerComponent` 公开 API 对应 ContainerPicker 实现 | AC-1.1 |
| Utils 为边界准线 | displayedItemCount/itemHeight 以 `ContainerPickerUtils` 为准 | AC-2.3, AC-2.4 |
| C API 不改 ABI | 只记录 `ARKUI_NODE_PICKER` 既有枚举 | AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增滚轮布局或动画路径 | UT | 现有 Pattern |
| 功耗 | 无后台任务 | 代码审查 | 无源码变更 |
| 内存 | 子组件由 UI 树管理 | UT | RefPtr/UI 树 |
| 安全 | haptic 权限按 SDK 提示由应用声明 | 代码审查 | `ui_picker_component.d.ts:399` |
| 可靠性 | count/height/selectedIndex 有明确恢复 | UT | R-2, R-6, R-7 |
| 可测试性 | AC 映射 UT，C API 标注测试缺口 | 生成检查 | VM-1 ~ VM-4 |
| 自动化维测 | 复用 ContainerPicker UT | UT | `test/unittest/core/pattern/container_picker/` |
| 定界定位 | SDK/JS/Model/Pattern/C API 分层明确 | 代码审查 | design.md |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 推荐高度 200vp，默认 7 项 | UT/手工 | `ui_picker_component.d.ts:63` |
| 平板 | 无差异 | 宽度未设置时取可见子组件最大宽度 | 手工 | `ui_picker_component.d.ts:73` |
| 折叠屏 | 无额外差异 | 按同一布局规则 | 手工 | 同上 |
| 穿戴 | 不支持 | SDK 明示当前不支持 wearables | 静态检查 | `ui_picker_component.d.ts:81` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Pattern 设置 accessibility action | AC-3.1 |
| 大字体 | 是 | Text 子组件 fontSize 默认 20fp，用户设置覆盖 | AC-1.3 |
| 深色模式 | 是 | selectionIndicator 支持 ResourceColor | AC-2.5 |
| 多窗口/分屏 | 是 | 高度和宽度按布局约束裁剪 | AC-1.4 |
| 多用户 | 否 | 无持久化数据 | N/A |
| 版本升级 | 是 | 22/23/26 API 边界需保持 | AC-2.3 |
| 生态兼容 | 是 | `UIPickerComponent` 与 `ARKUI_NODE_PICKER` 双通道保持现有合同 | AC-3.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: UIPickerComponent 滚轮选择
  Scenario: displayedItemCount 偶数归一化
    Given UIPickerComponent 设置 displayedItemCount(4)
    When 组件读取布局参数
    Then 实际 displayCount 为 5

  Scenario: 滚动结束事件
    Given UIPickerComponent 设置 onScrollStop
    When 滚动动画完成且未被打断
    Then onScrollStop 收到 selectedIndex
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
    query: "UIPickerComponent ContainerPicker selectedIndex displayedItemCount itemHeight C API implementation"
```

**关键文档:** `docs/pattern/container_picker/Container_Picker_Knowledge_Base.md`
