# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Slider 提示、自定义内容与无障碍内容 |
| 特性编号 | Func-05-04-05-Feat-04 |
| FuncID | 05-04-05 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | Dynamic API 7+ / Static API 23+ / NDK API 20+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出与 Feat-04 相关的历史能力范围。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `showTips(value, content?)` | Dynamic API `@since 7`，拖动/悬停/轴操作时显示提示气泡，content `@since 10`。 |
| ADDED | `contentModifier(modifier)` 与 `SliderConfiguration` | Dynamic API `@since 12`，自定义 Slider 内容，提供 value/min/max/step/enabled/triggerChange。 |
| ADDED | `SliderStepItemAccessibility`, `SliderShowStepOptions` | Dynamic API `@since 20`，为步点虚拟节点提供无障碍文本映射。 |
| ADDED | `prefix(content, options?)`, `suffix(content, options?)` 与 `SliderCustomContentOptions` | Dynamic API `@since 20`，设置首尾自定义内容及无障碍信息。 |
| ADDED | Static `contentModifier`, `prefix`, `suffix`, `showTips` | Static API `@since 23`。 |
| ADDED | NDK `NODE_SLIDER_PREFIX`, `NODE_SLIDER_SUFFIX` | NDK `@since 20`，通过 `.object` 传入子节点句柄。 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/04-input-form-components/05-slider/design.md`
- **KB 路由**: `python3 docs/kb_search.py Slider` 未命中现有 KB 条目
- **SDK 类型定义**:
  - Dynamic: `/home/sunfei/workspace/openHarmony/interface/sdk-js/api/@internal/component/ets/slider.d.ts:586`
  - Static: `/home/sunfei/workspace/openHarmony/interface/sdk-js/api/arkui/component/slider.static.d.ets:344`
- **源码定位**:
  - `frameworks/core/components_ng/pattern/slider/slider_model_ng.cpp:162`
  - `frameworks/core/components_ng/pattern/slider/slider_pattern.h:153`
  - `frameworks/core/components_ng/pattern/slider/slider_pattern.cpp:604`
  - `frameworks/core/components_ng/pattern/slider/bridge/arkts_native_slider_bridge.cpp:1219`
  - `frameworks/core/components_ng/pattern/slider/bridge/slider_static_modifier.cpp:479`
  - `frameworks/core/components_ng/pattern/slider/slider_accessibility_property.cpp:34`
  - `interfaces/native/native_node.h:6239`
  - `interfaces/native/node/style_modifier.cpp:19964`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 显示 Slider 提示气泡

**角色**: 应用开发者  
**期望**: 我想在用户拖动、悬停或轴操作 Slider 时显示当前百分比或自定义提示内容。  
**价值**: 以便用户能直观看到当前进度。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `showTips(true)` 且用户进入支持提示的交互状态 THEN 显示提示气泡，默认内容为当前百分比。 | 正常 |
| AC-1.2 | WHEN 调用 `showTips(true, content)` THEN 保存自定义 content；WHEN content 缺失 THEN reset `CustomContent` 并使用百分比内容。 | 正常 |
| AC-1.3 | WHEN `showTips(false)` THEN 不初始化提示气泡，也不更新提示文本。 | 正常 |
| AC-1.4 | WHEN 鼠标离开、交互结束且无焦点激活 THEN `bubbleFlag` 关闭，提示气泡隐藏。 | 正常 |
| AC-1.5 | WHEN direction 为 Horizontal/Vertical THEN 提示位置基于滑块中心、轨道厚度和安全区偏移计算；空间不足可能被边界裁剪。 | 边界 |

### US-2: 自定义 Slider 内容并触发值变更

**角色**: 应用开发者  
**期望**: 我想通过 `contentModifier` 自定义 Slider 内容，并在自定义内容中调用 `triggerChange` 改变 Slider。  
**价值**: 以便构建定制视觉但仍复用 Slider 的数值、事件和可访问性能力。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `contentModifier(modifier)` THEN Pattern 保存 builderFunc，并在构建时提供 `SliderConfiguration`。 | 正常 |
| AC-2.2 | WHEN `SliderConfiguration.triggerChange(value, mode)` 被调用 THEN 通过 `SliderModelNG::SetChangeValue` 更新 Slider value 并触发对应事件。 | 正常 |
| AC-2.3 | WHEN contentModifier 为 undefined 或 reset THEN 清除 builderFunc。 | 正常 |
| AC-2.4 | WHEN 使用 contentModifier THEN `HasPrefix()` 和 `HasSuffix()` 返回 false，prefix/suffix 不作为首尾内容参与布局。 | 边界 |

### US-3: 配置 prefix/suffix 与无障碍内容

**角色**: 应用开发者和无障碍用户  
**期望**: 我想为 Slider 首尾添加自定义组件，并为步点、首尾内容配置无障碍文本、描述、级别和分组。  
**价值**: 以便 Slider 在可视化定制后仍能被辅助服务正确识别和操作。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 `prefix(content, options)` 或 `suffix(content, options)` THEN Pattern 保存对应 UINode 和 `SliderCustomContentOptions`。 | 正常 |
| AC-3.2 | WHEN content 为空或 reset prefix/suffix THEN 对应节点被清除并重新布局。 | 正常 |
| AC-3.3 | WHEN 设置 `showSteps(true, { stepsAccessibility })` 且 key 为 `[0, INT32_MAX]` 整数 THEN 对应步点虚拟节点使用自定义无障碍文本。 | 正常 |
| AC-3.4 | WHEN `stepsAccessibility` key 为负数、小数、超过 INT32_MAX 或 text 缺失 THEN 该映射不生效。 | 异常 |
| AC-3.5 | WHEN prefix/suffix 存在且首尾步点虚拟节点生成 THEN prefix/suffix 的 accessibilityText/Description/Level/Group 覆盖首尾步点对应无障碍属性。 | 正常 |
| AC-3.6 | WHEN Slider 自身 accessibilityLevel 为 `no` 或 `no-hide-descendants` THEN 清理 Slider 步点虚拟节点。 | 正常 |
| AC-3.7 | WHEN NDK 设置 `NODE_SLIDER_PREFIX/SUFFIX` 且 `.object` 为空 THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1 ~ R-5 | TASK-SLIDER-04 | Core UT + 手工交互 | `slider_model_ng.cpp:162`, `slider_pattern.cpp:1416`, `slider_pattern.cpp:2100` |
| AC-2.1 ~ AC-2.4 | R-6 ~ R-9 | TASK-SLIDER-04 | Static/Dynamic UT | `arkts_native_slider_bridge.cpp:1219`, `slider_static_modifier.cpp:479`, `slider_pattern.h:153` |
| AC-3.1, AC-3.2 | R-10, R-11 | TASK-SLIDER-04 | Core UT | `slider_model_ng.cpp:270`, `slider_dynamic_modifier.cpp:710` |
| AC-3.3, AC-3.4 | R-12, R-13 | TASK-SLIDER-04 | Core UT + 无障碍测试 | `slider_static_modifier.cpp:64`, `slider_pattern.cpp:860` |
| AC-3.5, AC-3.6 | R-14, R-15 | TASK-SLIDER-04 | 无障碍测试 | `slider_pattern.cpp:883`, `slider_pattern.cpp:542` |
| AC-3.7 | R-16 | TASK-SLIDER-04 | C API UT | `style_modifier.cpp:19964` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `showTips(true)` 且进入交互/悬停/轴操作状态 | `bubbleFlag=true`，初始化提示气泡 | 默认内容为 `round(valueRatio*100)%` | AC-1.1 |
| R-2 | 行为 | `showTips(true, content)` | 保存 `CustomContent`；无 content 时 reset `CustomContent` | Dynamic content 从 API 10 起可用 | AC-1.2 |
| R-3 | 行为 | `showTips(false)` | 不初始化气泡，不更新提示文本 | `InitializeBubble()` 首行检查 showTips | AC-1.3 |
| R-4 | 行为 | 鼠标离开或交互结束且无焦点激活 | 关闭 bubbleFlag 并取消 hovered 状态 | focus active 时保留提示状态 | AC-1.4 |
| R-5 | 边界 | 计算提示位置 | 基于 block center、trackThickness、blockSize 和安全区偏移计算 overlay 位置 | SDK 声明空间不足可能被裁剪 | AC-1.5 |
| R-6 | 行为 | 设置 contentModifier | 保存 builderFunc，构建 `SliderConfiguration` 传给自定义 builder | Static 和 Dynamic 均提供 value/min/max/step/enabled/triggerChange | AC-2.1 |
| R-7 | 行为 | 调用 `triggerChange(value, mode)` | 转发到 `SliderModelNG::SetChangeValue`，由 Pattern 更新 value 与事件 | mode 使用 SliderChangeMode | AC-2.2 |
| R-8 | 恢复 | contentModifier 为 undefined/reset | 清除 builderFunc | 下次构建不使用自定义内容节点 | AC-2.3 |
| R-9 | 边界 | contentModifier 节点存在 | `HasPrefix()`/`HasSuffix()` 返回 false | prefix/suffix 不参与首尾布局和首尾步点覆盖 | AC-2.4 |
| R-10 | 行为 | 设置 prefix/suffix | Pattern 保存 UINode 弱引用与无障碍 options，触发布局刷新 | options 默认 text/description 为空、level auto、group false | AC-3.1 |
| R-11 | 恢复 | reset prefix/suffix 或 content 为空 | 清除对应节点和 options，重新计算首尾位置 | NDK reset 调用 modifier reset | AC-3.2 |
| R-12 | 行为 | `stepsAccessibility` key 为合法整数且 text 存在 | 对应步点虚拟节点使用自定义 accessibilityText | 仅 showSteps options 写入后生效 | AC-3.3 |
| R-13 | 异常 | `stepsAccessibility` key 非法或 text 缺失 | 跳过该映射，不影响其他合法映射 | key 范围 `[0, INT32_MAX]` 且必须为整数 | AC-3.4 |
| R-14 | 行为 | prefix/suffix 存在且虚拟节点首尾对应 | 覆盖首/尾步点 accessibilityText、Description、Level、Group | 仅在 `HasPrefix/HasSuffix` 为 true 时覆盖 | AC-3.5 |
| R-15 | 行为 | Slider accessibilityLevel 为 `no` 或 `no-hide-descendants` | 清理 Slider 虚拟节点并清除无障碍 hover | 不创建步点虚拟节点 | AC-3.6 |
| R-16 | 异常 | NDK prefix/suffix `.object` 为空 | 返回 `ARKUI_ERROR_CODE_PARAM_INVALID` | 合法 object 必须是 `ArkUI_NodeHandle` | AC-3.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | Core UT + 手工交互 | showTips 开关、自定义内容、气泡显示/隐藏和安全区位置。 |
| VM-2 | AC-2.1 ~ AC-2.4 | Dynamic/Static UT | contentModifier builderFunc、SliderConfiguration、triggerChange、prefix/suffix 互斥。 |
| VM-3 | AC-3.1, AC-3.2 | Core UT | prefix/suffix 设置、reset 和重新布局。 |
| VM-4 | AC-3.3 ~ AC-3.6 | 无障碍测试 | 步点虚拟节点、首尾覆盖、非法 key 跳过、level 清理。 |
| VM-5 | AC-3.7 | C API UT | NDK prefix/suffix object 校验。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `SliderAttribute.showTips(value, content?)` | Public | boolean, `ResourceStr` | `SliderAttribute/this` | N/A | 控制 Slider 提示气泡及自定义内容。 | AC-1.1 ~ AC-1.5 |
| `SliderAttribute.contentModifier(modifier)` | Public | `ContentModifier<SliderConfiguration>` | `SliderAttribute/this` | N/A | 自定义 Slider 内容。 | AC-2.1 ~ AC-2.4 |
| `SliderConfiguration.triggerChange(value, mode)` | Public callback | value, `SliderChangeMode` | void | N/A | 自定义内容触发 Slider 值变化。 | AC-2.2 |
| `SliderAttribute.prefix(content, options?)` / `suffix(content, options?)` | Public | `ComponentContent`, `SliderPrefixOptions/SliderSuffixOptions` | `SliderAttribute/this` | N/A | 设置 Slider 首尾自定义内容与无障碍配置。 | AC-3.1, AC-3.2, AC-3.5 |
| `SliderShowStepOptions.stepsAccessibility` | Public | `Map<number, SliderStepItemAccessibility>` | N/A | N/A | 配置步点无障碍文本映射。 | AC-3.3, AC-3.4 |
| `NODE_SLIDER_PREFIX/SUFFIX` | NDK/Public | `.object` 为 `ArkUI_NodeHandle` | set 返回 `int32_t` | `ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | Native 设置 Slider 首尾自定义节点。 | AC-3.7 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次为已有能力补录，不改变 API | N/A | N/A |

## 接口规格

### 接口定义

**showTips(value: boolean, content?: ResourceStr)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SliderAttribute.showTips(value: boolean, content?: ResourceStr): SliderAttribute` |
| 返回值 | `SliderAttribute/this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | boolean | 是 | false | true 时允许交互过程中显示气泡。 |
| content | ResourceStr | 否 | 当前百分比 | 缺失时 reset `CustomContent`。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | showTips=true 且拖动 | 显示气泡，默认百分比内容 | AC-1.1 |
| 2 | showTips=true 且 content 存在 | 保存自定义 content | AC-1.2 |
| 3 | showTips=false | 不显示气泡 | AC-1.3 |
| 4 | 交互结束 | 按焦点/hover 状态关闭气泡 | AC-1.4 |

**contentModifier(modifier) / SliderConfiguration**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SliderAttribute.contentModifier(modifier: ContentModifier<SliderConfiguration>): SliderAttribute` |
| 返回值 | `SliderAttribute/this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 ~ AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| modifier | ContentModifier | 是 | N/A | undefined/reset 清除 builderFunc。 |
| SliderConfiguration.value/min/max/step | double | 系统生成 | 当前 Slider 属性 | 只读配置值，来自 Pattern/Property。 |
| SliderConfiguration.enabled | boolean | 系统生成 | 当前 enabled | 表示组件可用状态。 |
| SliderConfiguration.triggerChange | callback | 系统生成 | N/A | 调用后进入 Slider value 更新和事件路径。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 contentModifier | 构建自定义内容节点 | AC-2.1 |
| 2 | triggerChange 被调用 | 更新 Slider value 并触发 mode 事件 | AC-2.2 |
| 3 | reset contentModifier | 清除 builderFunc | AC-2.3 |
| 4 | contentModifier 存在 | prefix/suffix 不作为首尾内容生效 | AC-2.4 |

**prefix/suffix 与无障碍 options**

| 属性 | 值 |
|------|-----|
| 函数签名 | `prefix(content: ComponentContent, options?: SliderPrefixOptions)`, `suffix(content: ComponentContent, options?: SliderSuffixOptions)` |
| 返回值 | `SliderAttribute/this` |
| 开放范围 | Public / NDK Public |
| 错误码 | NDK object 为空返回 `ARKUI_ERROR_CODE_PARAM_INVALID` |
| 关联 AC | AC-3.1 ~ AC-3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| content | ComponentContent / ArkUI_NodeHandle | 是 | N/A | ArkTS content 为空时 reset；NDK `.object` 不能为空。 |
| accessibilityText | ResourceStr | 否 | `""` | 非空时覆盖首/尾步点文本。 |
| accessibilityDescription | ResourceStr | 否 | `""` | 非空时覆盖首/尾步点描述。 |
| accessibilityLevel | string | 否 | `auto` | 写入对应虚拟节点 level。 |
| accessibilityGroup | boolean | 否 | false | 写入对应虚拟节点 group。 |
| stepsAccessibility | Map<number, SliderStepItemAccessibility> | 否 | `{}` | key 必须是 `[0, INT32_MAX]` 整数，text 必须存在。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 prefix/suffix | 保存节点和 options，刷新布局 | AC-3.1 |
| 2 | reset prefix/suffix | 清除节点 | AC-3.2 |
| 3 | 合法 stepsAccessibility | 覆盖对应步点文本 | AC-3.3 |
| 4 | 非法 stepsAccessibility key | 跳过该映射 | AC-3.4 |
| 5 | Slider accessibilityLevel 为 no | 清理虚拟节点 | AC-3.6 |

## 兼容性声明

- **已有 API 行为变更:** 否，本次为已有实现规格补录。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** `showTips` Dynamic API 7；`contentModifier` Dynamic API 12；`prefix/suffix` 与步点无障碍 Dynamic API 20；Static API 23；NDK prefix/suffix API 20。
- **API 版本号策略:** 以 SDK `@since` 和 NDK `native_node.h` 为准；prefix/suffix 与 contentModifier 的互斥为实现规格。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 提示气泡属于 overlay 绘制 | showTips 通过 PaintProperty 与 TipModifier/overlay 位置计算实现，不新增独立组件 API。 | AC-1.1 ~ AC-1.5 |
| contentModifier 优先于 prefix/suffix | Pattern 中 contentModifierNode 存在时 `HasPrefix/HasSuffix` 返回 false。 | AC-2.4 |
| 无障碍虚拟节点依赖 showSteps/step | 步点虚拟节点基于 stepPoints 和 step 生成，step 为 0 或节点为空时不更新。 | AC-3.3 ~ AC-3.6 |
| NDK prefix/suffix 只公开节点句柄 | NDK 公开属性不包含 accessibility options，默认 options 为空/auto/false。 | AC-3.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | contentModifier 构建通过已有 builder/FrameNode 路径，不新增同步阻塞。 | Static/Dynamic UT | `slider_static_modifier.cpp:479` |
| 功耗 | showTips 只在交互/hover/focus 状态更新，不引入后台任务。 | 代码评审 | `slider_pattern.cpp:2100` |
| 内存 | contentModifier、prefix、suffix 节点由 UINode/FrameNode 引用计数管理，reset 清理引用。 | Core UT | `slider_model_ng.cpp:1061` |
| 安全 | NDK prefix/suffix 校验 `.object` 非空。 | C API UT | `style_modifier.cpp:19964` |
| 可靠性 | accessibilityLevel 为 no/no-hide-descendants 时清理虚拟节点，避免无效可访问对象。 | 无障碍测试 | `slider_pattern.cpp:542` |
| 可测试性 | showTips、contentModifier、prefix/suffix、虚拟节点文本均可通过 UT/无障碍属性验证。 | UT + 无障碍测试 | `slider_pattern.cpp:811` |
| 自动化维测 | 不新增日志、埋点或 DFX 事件。 | 代码评审 | N/A |
| 定界定位 | Bridge、Pattern、AccessibilityProperty、NDK style_modifier 均可追溯。 | 文档自审 | 本规格验收追溯表 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | showTips 默认在水平 Slider 上方显示，空间不足可能裁剪。 | 验证安全区和边界位置。 | 手工/组件测试 | `slider_pattern.cpp:1534` |
| 平板 | 无功能差异，气泡和 prefix/suffix 随布局尺寸重新计算。 | 验证横纵向布局。 | 组件测试 | `slider_pattern.cpp:448` |
| 折叠屏 | 无功能差异，窗口尺寸变化后重新布局。 | 验证多窗口/旋转场景。 | 组件测试 | `slider_pattern.cpp:1075` |
| 穿戴 | 与 Feat-03 表冠交互结合时，showTips 可随表冠移动更新。 | 验证表冠 Moving 下气泡更新。 | 设备验证 | `slider_pattern.h:320` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 本 Feat 定义步点虚拟节点、prefix/suffix 覆盖和 Slider accessibility value。 | AC-3.3 ~ AC-3.6 |
| 大字体 | 是 | showTips 文本字体来自 SliderTheme；步点虚拟文本启用小语种截断。 | AC-1.1, AC-3.3 |
| 深色模式 | 间接适用 | showTips tipColor/textColor 来自 theme，颜色刷新沿用主题机制。 | AC-1.1 |
| 多窗口/分屏 | 是 | prefix/suffix 和虚拟节点大小随布局重新计算。 | AC-3.1 |
| 多用户 | 否 | 不涉及用户态存储。 | N/A |
| 版本升级 | 是 | 需要保留 Dynamic 7/10/12/20、Static 23、NDK 20 的版本边界。 | API 变更分析 |
| 生态兼容 | 是 | contentModifier 与 prefix/suffix 互斥属于现有实现行为，需避免未来变更破坏既有应用。 | AC-2.4 |

## 行为场景（可选，Gherkin）

Feature: Slider 提示、自定义内容与无障碍内容
  作为 ArkUI 开发者
  我想定制 Slider 提示、内容和无障碍文本
  以便视觉定制后仍保持可访问和可交互

  Scenario: showTips 默认显示百分比
    Given Slider 设置 showTips(true)
    When 用户拖动 Slider
    Then 提示气泡显示
    And 文本为当前 valueRatio 四舍五入百分比

  Scenario: contentModifier 覆盖 prefix/suffix
    Given Slider 已设置 prefix 和 suffix
    When 设置 contentModifier
    Then HasPrefix 返回 false
    And HasSuffix 返回 false

  Scenario: prefix 覆盖首个步点无障碍文本
    Given Slider 设置 showSteps(true)
    And 设置 prefix 的 accessibilityText
    When 步点虚拟节点更新
    Then 首个步点虚拟节点 accessibilityText 使用 prefix 配置

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
  - repo: "OpenHarmony/foundation/arkui/ace_engine"
    query: "Slider showTips contentModifier prefix suffix accessibility virtual node implementation"
  - repo: "OpenHarmony/interface/sdk-js"
    query: "Slider showTips contentModifier SliderConfiguration prefix suffix accessibility since"
```

**关键文档：** `slider.d.ts`, `slider.static.d.ets`, `native_node.h`, `slider_model_ng.cpp`, `slider_pattern.cpp`, `slider_accessibility_property.cpp`, `style_modifier.cpp`
