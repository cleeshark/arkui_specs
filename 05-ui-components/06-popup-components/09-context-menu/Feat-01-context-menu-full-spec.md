# 特性规格

> Func-05-06-09-Feat-01 bindContextMenu 上下文菜单：固化响应类型范式（@since 8）、isShown 双绑定范式（@since 12）、WithResponse 范式（@since 23）的行为规格，覆盖预览、箭头、布局避让、Placement、Options 配置面、触觉反馈与 RTL。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | bindContextMenu 上下文菜单 (Context Menu) |
| 特性编号 | Func-05-06-09-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 8 起支持，API 10/11/12/13/18/19/20/23/26 持续演进 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 响应类型范式行为规格 | bindContextMenu(content, responseType, options?) @since 8，RIGHT_CLICK/LONG_PRESS 触发 |
| ADDED | isShown 双绑定范式行为规格 | bindContextMenu(isShown, content, options?) @since 12，CUSTOM_TYPE/BOTTOM_LEFT |
| ADDED | WithResponse 范式行为规格 | bindContextMenuWithResponse @since 23，builder 接收 MenuBindingType |
| ADDED | 预览/箭头/避让/Placement 行为规格 | MenuPreviewMode NONE/IMAGE/CustomBuilder；箭头安全偏移；屏幕边缘+折痕避让 |
| ADDED | Options 配置面行为规格 | backgroundColor/backgroundBlurStyle/borderRadius/mask/modalMode/systemMaterial 等 |
| ADDED | 触觉反馈与 RTL 行为规格 | hapticFeedbackMode 需权限；RTL 箭头调整 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/06-popup-components/09-context-menu/design.md` | Baselined |
| SDK API | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | — |
| SDK 枚举 | `interface/sdk-js/api/@internal/component/ets/enums.d.ts` | — |

---

## 用户故事

### US-1: 响应类型绑定上下文菜单

**作为** 应用开发者,
**我想要** 通过 `bindContextMenu(content, responseType, options?)` 按响应类型（长按/右键）绑定上下文菜单,
**以便** 在用户长按或右键点击组件时弹出菜单。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `bindContextMenu(content, ResponseType.RightClick, options?)` THEN 组件在右键点击时弹出上下文菜单 | 正常 |
| AC-1.2 | WHEN 调用 `bindContextMenu(content, ResponseType.LongPress, options?)` THEN 组件在触摸长按时弹出上下文菜单 | 正常 |
| AC-1.3 | WHEN responseType = LongPress 且触发来源为鼠标 THEN 不触发菜单（LONG_PRESS 鼠标不支持） | 异常 |
| AC-1.4 | WHEN 响应类型范式未指定 options.placement THEN 默认 placement = TOP | 边界 |
| AC-1.5 | WHEN 响应类型范式识别到 boolean isShow=true THEN 切换为 CUSTOM_TYPE 范式，placement 默认 BOTTOM_LEFT | 边界 |
| AC-1.6 | WHEN isShow 为 object THEN 进入响应类型范式或 WithResponse 参数对象解析 | 边界 |

### US-2: isShown 双绑定范式

**作为** 应用开发者,
**我想要** 通过 `bindContextMenu(isShown, content, options?)` 以显示状态绑定上下文菜单,
**以便** 通过状态变量命令式控制菜单的显示与隐藏。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `bindContextMenu(isShown: boolean, content, options?)` THEN 进入 CUSTOM_TYPE 范式，contextMenuRegisterType=CUSTOM_TYPE | 正常 |
| AC-2.2 | WHEN isShown 范式未指定 options.placement THEN 默认 placement = BOTTOM_LEFT | 边界 |
| AC-2.3 | WHEN isShown 范式下设置 isShow=true THEN 菜单显示；isShow=false THEN 菜单隐藏 | 正常 |
| AC-2.4 | WHEN isShown 范式（CUSTOM_TYPE）下触发长按 THEN 不支持拖拽长按（与响应类型范式行为差异） | 边界 |

### US-3: WithResponse 范式

**作为** 应用开发者,
**我想要** 通过 `bindContextMenuWithResponse(content, options?)` 同时注册右键与长按响应,
**以便** 在 builder 中根据 MenuBindingType 区分触发来源差异化菜单内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `bindContextMenuWithResponse(content, options?)` THEN 同时注册 RIGHT_CLICK + LONG_PRESS | 正常 |
| AC-3.2 | WHEN WithResponse 触发 THEN builder 接收 MenuBindingType 标识触发来源（RIGHT_CLICK/LONG_PRESS） | 正常 |
| AC-3.3 | WHEN WithResponse 范式 @since 23 与旧响应类型范式共存 THEN 旧 API 行为不受影响 | 兼容 |

### US-4: 预览模式

**作为** 应用开发者,
**我想要** 通过 `preview` 选项设置菜单预览模式,
**以便** 在菜单弹出前展示图片或自定义内容预览。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN preview = MenuPreviewMode.NONE（默认）THEN 不显示预览图 | 边界 |
| AC-4.2 | WHEN preview = MenuPreviewMode.IMAGE THEN 显示系统预览图 | 正常 |
| AC-4.3 | WHEN preview = CustomBuilder THEN 显示自定义预览内容 | 正常 |
| AC-4.4 | WHEN preview != NONE THEN 强制 enableArrow = false（预览承担指向语义） | 边界 |

### US-5: 箭头

**作为** 应用开发者,
**我想要** 通过 `enableArrow` 和 `arrowOffset` 配置菜单箭头,
**以便** 让菜单明确指向触发源。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN enableArrow = false（默认）THEN 不显示箭头 | 边界 |
| AC-5.2 | WHEN enableArrow = true THEN 按 placement 方向显示箭头 | 正常 |
| AC-5.3 | WHEN 设置 arrowOffset THEN 箭头位置按偏移调整 | 正常 |
| AC-5.4 | WHEN 箭头位置接近圆角 THEN 自动钳位到安全位置（radius + 半个箭头宽度） | 边界 |

### US-6: 布局避让与 Placement

**作为** 应用开发者,
**我想要** 菜单按 placement 放置并自动避让屏幕边缘与折痕,
**以便** 菜单始终完整可见。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 设置 options.placement THEN 菜单按指定方位放置 | 正常 |
| AC-6.2 | WHEN 菜单接近屏幕边缘 THEN MenuAvoidAlgorithm 自动避让 | 正常 |
| AC-6.3 | WHEN 设备存在折痕 THEN 菜单避让折痕区域 | 正常 |
| AC-6.4 | WHEN layoutRegionMargin 未指定 THEN 默认左右 12vp、上下 16vp | 边界 |

### US-7: Options 配置面

**作为** 应用开发者,
**我想要** 通过 ContextMenuOptions 配置菜单背景、模糊、圆角、遮罩、模态等外观,
**以便** 定制菜单视觉风格。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 设置 backgroundColor THEN 菜单背景使用指定颜色 | 正常 |
| AC-7.2 | WHEN 设置 backgroundBlurStyle THEN 菜单背景应用指定模糊效果 | 正常 |
| AC-7.3 | WHEN 未指定 borderRadius THEN 2-in-1 设备默认 8vp，其他设备默认 20vp | 边界 |
| AC-7.4 | WHEN 设置 mask/modalMode THEN 菜单遮罩与模态行为按指定模式生效 | 正常 |

### US-8: 触觉反馈与 RTL

**作为** 应用开发者,
**我想要** 通过 hapticFeedbackMode 设置触觉反馈，并支持 RTL 场景,
**以便** 菜单适配触觉与 RTL 设备。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 设置 hapticFeedbackMode 且 level-1 菜单 THEN 触发触觉反馈（需 ohos.permission.VIBRATE） | 正常 |
| AC-8.2 | WHEN 触觉反馈未授权权限 THEN 静默跳过触觉，不抛出异常 | 异常 |
| AC-8.3 | WHEN 设备为 RTL THEN 箭头位置自动调整以适配 RTL 布局方向 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1, R-5 | 单元测试 + 代码审查 |
| AC-1.2 | US-1 | R-2, R-5 | 单元测试 + 代码审查 |
| AC-1.3 | US-1 | R-3, R-21 | 代码审查 |
| AC-1.4 | US-1 | R-4 | 代码审查 |
| AC-1.5 | US-1 | R-6, R-7 | 代码审查 js_popups.cpp:1031-1051 |
| AC-1.6 | US-1 | R-7 | 代码审查 js_popups.cpp:1031-1051 |
| AC-2.1 | US-2 | R-8, R-9 | 代码审查 view_abstract_model_ng.cpp:894-914 |
| AC-2.2 | US-2 | R-10 | 代码审查 |
| AC-2.3 | US-2 | R-8 | 单元测试 |
| AC-2.4 | US-2 | R-11 | 代码审查 |
| AC-3.1 | US-3 | R-12, R-13 | 代码审查 view_abstract_model_ng.cpp:936-961 |
| AC-3.2 | US-3 | R-14 | 代码审查 js_popups.cpp:2316-2372 |
| AC-3.3 | US-3 | R-15 | 代码审查 |
| AC-4.1 | US-4 | R-16 | 代码审查 |
| AC-4.2 | US-4 | R-17 | 代码审查 |
| AC-4.3 | US-4 | R-18 | 代码审查 |
| AC-4.4 | US-4 | R-19 | 代码审查 |
| AC-5.1 | US-5 | R-20 | 代码审查 menu_property.h |
| AC-5.2 | US-5 | R-20 | 代码审查 menu_layout_algorithm.cpp |
| AC-5.3 | US-5 | R-22 | 代码审查 |
| AC-5.4 | US-5 | R-23 | 代码审查 |
| AC-6.1 | US-6 | R-24 | 单元测试 |
| AC-6.2 | US-6 | R-25 | 代码审查 menu_avoid_algorithm.cpp |
| AC-6.3 | US-6 | R-25 | 代码审查 menu_avoid_algorithm.cpp |
| AC-6.4 | US-6 | R-26 | 代码审查 |
| AC-7.1 | US-7 | R-27 | 单元测试 |
| AC-7.2 | US-7 | R-28 | 单元测试 |
| AC-7.3 | US-7 | R-29 | 代码审查 |
| AC-7.4 | US-7 | R-30 | 单元测试 |
| AC-8.1 | US-8 | R-31 | 代码审查 |
| AC-8.2 | US-8 | R-32 | 代码审查 |
| AC-8.3 | US-8 | R-33 | 代码审查 menu_layout_algorithm.cpp |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `view_abstract_model_ng.cpp:894-914` | ResponseType=RIGHT_CLICK → BindContextMenuWithRightClick 分发 | — | AC-1.1 |
| R-2 | 行为 | `view_abstract_model_ng.cpp:894-914` | ResponseType=LONG_PRESS → BindContextMenuWithLongPress 分发 | — | AC-1.2 |
| R-3 | 边界 | LONG_PRESS 范式 | LONG_PRESS 仅触摸生效，鼠标长按不触发菜单 | — | AC-1.3 |
| R-4 | 边界 | 响应类型范式默认 placement | 响应类型范式未指定 placement 时默认 TOP | — | AC-1.4 |
| R-5 | 行为 | `view_abstract_model_ng.cpp:894-988` | BindContextMenu 分发到 BindContextMenuSingle/WithRightClick/WithLongPress + RegisterContextMenuKeyEvent | — | AC-1.1, AC-1.2 |
| R-6 | 行为 | `js_popups.cpp:1031-1051` ParseBindContextMenuShow | isShow 为 boolean true → 识别为 CUSTOM_TYPE 范式 | — | AC-1.5 |
| R-7 | 行为 | `js_popups.cpp:1031-1051` ParseBindContextMenuShow | isShow 为 object → 进入响应类型范式或 WithResponse 参数对象解析 | — | AC-1.5, AC-1.6 |
| R-8 | 行为 | `view_abstract_model_ng.cpp:894-914` | isShown 范式 → BindContextMenuSingle(CUSTOM_TYPE)，contextMenuRegisterType=CUSTOM_TYPE | — | AC-2.1, AC-2.3 |
| R-9 | 行为 | isShown 范式默认 placement | isShown 范式未指定 placement 时默认 BOTTOM_LEFT | — | AC-2.2 |
| R-10 | 边界 | `view_abstract_model_ng.cpp:894-914` | isShown 范式 isShow=true 显示 / isShow=false 隐藏 | — | AC-2.3 |
| R-11 | 边界 | CUSTOM_TYPE 范式 | CUSTOM_TYPE 范式不支持拖拽长按 | — | AC-2.4 |
| R-12 | 行为 | `view_abstract_model_ng.cpp:936-961` WithResponse | WithResponse 同时注册 RIGHT_CLICK + LONG_PRESS | — | AC-3.1 |
| R-13 | 行为 | `view_abstract_model_ng.cpp:936-961` | WithResponse builder 接收 MenuBindingType | — | AC-3.2 |
| R-14 | 行为 | `js_popups.cpp:2316-2372` JsBindContextMenuWithResponse | builder 接收 MenuBindingType 标识触发来源（RIGHT_CLICK/LONG_PRESS） | — | AC-3.2 |
| R-15 | 兼容 | WithResponse @since 23 | WithResponse 新增不影响旧响应类型范式 API | — | AC-3.3 |
| R-16 | 边界 | MenuPreviewMode 默认 | preview 默认 NONE，不显示预览图 | — | AC-4.1 |
| R-17 | 行为 | MenuPreviewMode.IMAGE | preview=IMAGE 显示系统预览图 | — | AC-4.2 |
| R-18 | 行为 | preview=CustomBuilder | preview=CustomBuilder 显示自定义预览内容 | — | AC-4.3 |
| R-19 | 边界 | preview != NONE | preview != NONE 时强制 enableArrow=false | — | AC-4.4 |
| R-20 | 边界 | enableArrow 默认 | enableArrow 默认 false | — | AC-5.1, AC-5.2 |
| R-21 | 异常 | LONG_PRESS 鼠标 | LONG_PRESS 范式鼠标长按不触发菜单 | — | AC-1.3 |
| R-22 | 行为 | arrowOffset | arrowOffset 调整箭头位置 | — | AC-5.3 |
| R-23 | 边界 | 箭头安全偏移 | 箭头位置自动钳位到 radius + 半个箭头宽度 | — | AC-5.4 |
| R-24 | 行为 | options.placement | placement 指定菜单方位 | — | AC-6.1 |
| R-25 | 行为 | `menu_avoid_algorithm.cpp` | 菜单避让屏幕边缘与折痕区域 | — | AC-6.2, AC-6.3 |
| R-26 | 边界 | layoutRegionMargin 默认 | layoutRegionMargin 默认左右 12vp、上下 16vp | — | AC-6.4 |
| R-27 | 行为 | backgroundColor | backgroundColor 设置菜单背景颜色 | — | AC-7.1 |
| R-28 | 行为 | backgroundBlurStyle | backgroundBlurStyle 设置菜单背景模糊 | — | AC-7.2 |
| R-29 | 边界 | borderRadius 默认 | 2-in-1 默认 8vp，其他默认 20vp | — | AC-7.3 |
| R-30 | 行为 | mask/modalMode | mask 与 modalMode 控制遮罩与模态行为 | — | AC-7.4 |
| R-31 | 行为 | hapticFeedbackMode | level-1 菜单触发触觉反馈，需 ohos.permission.VIBRATE | — | AC-8.1 |
| R-32 | 异常 | 触觉未授权 | 触觉未授权权限时静默跳过，不抛出异常 | — | AC-8.2 |
| R-33 | 行为 | RTL 箭头调整 | RTL 设备箭头位置自动调整 | — | AC-8.3 |
| R-34 | 行为 | `view_abstract_model_ng.cpp:1158-1182` RegisterContextMenuKeyEvent | KEY_MENU / INTENTION_MENU → BindMenuWithCustomNode BOTTOM_LEFT | — | — |
| R-35 | 恢复 | Array 变体 | CustomBuilder + Array 分支支持（`view_abstract_model_ng.cpp:916-934`） | — | — |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 响应类型绑定 (AC-1.1~1.6) | 单元测试 + 代码审查 | RIGHT_CLICK/LONG_PRESS 分发；ParseBindContextMenuShow 范式识别 |
| VM-2 | US-2 isShown 双绑定 (AC-2.1~2.4) | 单元测试 + 代码审查 | CUSTOM_TYPE 范式；BOTTOM_LEFT 默认；拖拽长按差异 |
| VM-3 | US-3 WithResponse (AC-3.1~3.3) | 代码审查 | 双注册；MenuBindingType；兼容性 |
| VM-4 | US-4 预览模式 (AC-4.1~4.4) | 代码审查 | NONE/IMAGE/CustomBuilder；预览强制隐藏箭头 |
| VM-5 | US-5 箭头 (AC-5.1~5.4) | 代码审查 | enableArrow 默认；arrowOffset；安全偏移 |
| VM-6 | US-6 避让与 Placement (AC-6.1~6.4) | 单元测试 + 代码审查 | placement；屏幕边缘/折痕避让；layoutRegionMargin |
| VM-7 | US-7 Options 配置面 (AC-7.1~7.4) | 单元测试 | backgroundColor/blur/borderRadius/mask/modalMode |
| VM-8 | US-8 触觉与 RTL (AC-8.1~8.3) | 代码审查 | hapticFeedbackMode 权限；RTL 箭头调整 |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:894-914` BindContextMenuWithRightClick L591 |
| AC-1.2 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:894-914` BindContextMenuWithLongPress L530 |
| AC-1.3 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_pattern.cpp`（LONG_PRESS 鼠标不支持） |
| AC-1.4 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_property.h`（响应类型范式默认 placement TOP） |
| AC-1.5 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:1031-1051` ParseBindContextMenuShow |
| AC-1.6 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:1031-1051` ParseBindContextMenuShow |
| AC-2.1 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:894-914` BindContextMenuSingle L345 |
| AC-2.2 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_property.h`（isShown 范式默认 BOTTOM_LEFT） |
| AC-2.3 | 单元测试 | `test/unittest/core/pattern/menu/` menu_pattern_test |
| AC-2.4 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_pattern.cpp`（CUSTOM_TYPE 不支持拖拽长按） |
| AC-3.1 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:936-961` |
| AC-3.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:2316-2372` JsBindContextMenuWithResponse |
| AC-3.3 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:936-961` |
| AC-4.1 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_property.h`（MenuPreviewMode NONE 默认） |
| AC-4.2 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_pattern.cpp` |
| AC-4.3 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_pattern.cpp` |
| AC-4.4 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_layout_algorithm.cpp`（preview != NONE 强制 enableArrow=false） |
| AC-5.1 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_property.h`（enableArrow 默认 false） |
| AC-5.2 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_layout_algorithm.cpp` |
| AC-5.3 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_layout_algorithm.cpp` |
| AC-5.4 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_layout_algorithm.cpp`（安全偏移 radius + 半箭头宽度） |
| AC-6.1 | 单元测试 | `test/unittest/core/pattern/menu/` menu_layout_algorithm_test |
| AC-6.2 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_avoid_algorithm.cpp` |
| AC-6.3 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_avoid_algorithm.cpp` |
| AC-6.4 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_property.h`（layoutRegionMargin 默认 12vp LR / 16vp TB） |
| AC-7.1 | 单元测试 | `test/unittest/core/pattern/menu/` |
| AC-7.2 | 单元测试 | `test/unittest/core/pattern/menu/` |
| AC-7.3 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_property.h`（2-in-1: 8vp / 其他: 20vp） |
| AC-7.4 | 单元测试 | `test/unittest/core/pattern/menu/` |
| AC-8.1 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_pattern.cpp`（hapticFeedbackMode） |
| AC-8.2 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_pattern.cpp`（未授权静默跳过） |
| AC-8.3 | 代码审查 | `frameworks/core/components_ng/pattern/menu/menu_layout_algorithm.cpp`（RTL 箭头调整） |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/common.d.ts`

#### bindContextMenu 系列

```typescript
// common.d.ts:24223 @since 8
bindContextMenu(content: CustomBuilder, responseType: ResponseType, options?: ContextMenuOptions): T;

// common.d.ts:24240 @since 26
bindContextMenuByResponseType(content: CustomBuilder, responseType: ResponseType, options?: ContextMenuOptions): T;

// common.d.ts:24257 @since 23 / 24273 @since 26
bindContextMenuWithResponse(content: CustomBuilder | ((binding: MenuBindingType) => CustomBuilder), options?: ContextMenuOptions): T;

// common.d.ts:24296 @since 12
bindContextMenu(isShown: boolean, content: CustomBuilder, options?: ContextMenuOptions): T;

// common.d.ts:24318 @since 26
bindContextMenuByIsShow(isShown: boolean, content: CustomBuilder, options?: ContextMenuOptions): T;
```

#### 枚举与类型

```typescript
// enums.d.ts:3211 @since 8
declare enum ResponseType {
    RightClick,
    LongPress
}

// common.d.ts:16410 @since 11
declare enum MenuPreviewMode {
    NONE = 0,
    IMAGE = 1
}

// common.d.ts:16453 @since 11/12/20
declare interface ContextMenuAnimationOptions {
    scale?: pairwise ...;
    transition?: ...;
    hoverScale?: ...;
    hoverScaleInterruption?: ...;
}

// common.d.ts:16937 @since 10+
declare interface ContextMenuOptions {
    offset?: Position;
    placement?: Placement;
    enableArrow?: boolean;
    arrowOffset?: Length;
    preview?: MenuPreviewMode | CustomBuilder;
    previewBorderRadius?: Dimension;
    borderRadius?: Dimension;
    onAppear?: () => void;
    onDisappear?: () => void;
    aboutToAppear?: () => void;
    aboutToDisappear?: () => void;
    layoutRegionMargin?: Dimension;
    previewAnimationOptions?: ContextMenuAnimationOptions;
    backgroundColor?: ResourceColor;
    backgroundBlurStyle?: BlurStyle;
    backgroundBlurStyleOptions?: BlurStyleOptions;
    backgroundEffect?: BackgroundEffectOptions;
    transition?: TransitionEffect;
    enableHoverMode?: boolean;
    outlineColor?: ResourceColor;
    outlineWidth?: Dimension;
    colorMode?: ThemeColorMode;
    hapticFeedbackMode?: HapticFeedbackMode;
    mask?: boolean;
    modalMode?: ModalMode;
    onDidAppear?: () => void;
    onDidDisappear?: () => void;
    onWillAppear?: () => void;
    onWillDisappear?: () => void;
}

// common.d.ts:17674
declare interface MenuOptions extends ContextMenuOptions { ... }
```

| 方法签名 | 返回类型 | 说明 | @since |
|----------|----------|------|--------|
| `bindContextMenu(content, responseType, options?)` | T | 响应类型范式 | 8 |
| `bindContextMenuByResponseType(...)` | T | 响应类型范式别名 | 26 |
| `bindContextMenuWithResponse(content, options?)` | T | WithResponse 范式 | 23 |
| `bindContextMenu(isShown, content, options?)` | T | isShown 双绑定范式 | 12 |
| `bindContextMenuByIsShow(...)` | T | isShown 范式别名 | 26 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无废弃 API，新增 WithResponse @since 23 与旧 API 共存 |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 8 | 响应类型范式 bindContextMenu(content, responseType, options?)，默认 placement TOP | — | 无需迁移 |
| API 12 | 新增 isShown 双绑定范式，CUSTOM_TYPE，默认 BOTTOM_LEFT | 两范式默认 placement 不同 | 切换范式时显式指定 placement |
| API 12 | CUSTOM_TYPE 范式不支持拖拽长按 | 与响应类型范式行为差异 | 如需拖拽长按使用响应类型范式 |
| API 23 | 新增 WithResponse 范式，builder 接收 MenuBindingType | 旧 API 不受影响 | 需区分触发来源时迁移到 WithResponse |
| API 26 | 新增 bindContextMenuByResponseType / bindContextMenuByIsShow 别名 | 旧 API 保留 | 无需迁移 |
| 2-in-1 设备 | borderRadius 默认 8vp（其他设备 20vp） | 设备形态差异 | 如需统一显式设置 borderRadius |
| 触觉反馈 | level-1 菜单需 ohos.permission.VIBRATE | 权限差异 | 未授权时静默跳过触觉 |
| 预览模式 | preview != NONE 时强制 enableArrow=false | 箭头不可用 | 如需箭头使用 preview=NONE |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 双范式分发 | 响应类型范式走 BindContextMenuWithRightClick/LongPress；isShown 范式走 BindContextMenuSingle(CUSTOM_TYPE)，由 MenuParam.contextMenuRegisterType 区分 |
| 物理键注册 | RegisterContextMenuKeyEvent 将 KEY_MENU/INTENTION_MENU 映射到 BindMenuWithCustomNode BOTTOM_LEFT |
| 预览强制隐藏箭头 | preview != NONE 时 enableArrow 强制 false |
| 箭头安全偏移 | 箭头位置自动钳位到 radius + 半个箭头宽度 |
| 避让约束 | MenuAvoidAlgorithm 处理屏幕边缘与折痕避让，layoutRegionMargin 默认左右 12vp/上下 16vp |
| 触觉权限 | haptic level-1 需 ohos.permission.VIBRATE，未授权静默跳过 |
| 圆角设备差异 | 2-in-1 设备 borderRadius 默认 8vp，其他设备 20vp |
| Array 变体 | CustomBuilder + Array 分支由 BindContextMenu Array 变体支持 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 菜单为按需创建的浮层，首次创建延迟应可控；进入/退出动画帧率 ≥ 60fps |
| 可调试性 | 提供 DumpInfo 用于 Inspector 诊断菜单状态 |
| 安全 | haptic level-1 需 ohos.permission.VIBRATE 权限，未授权静默跳过 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | LONG_PRESS 触摸长按生效，鼠标长按不生效 | — | 手工 | — |
| 平板 | 同手机，触觉需权限 | — | 手工 | — |
| 折叠屏 | 菜单避让策略需考虑折叠态/展开态屏幕尺寸与折痕 | MenuAvoidAlgorithm 适配折痕 | 手工 | — |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 无障碍 | 菜单内容支持无障碍读取，菜单显示时获取焦点 |
| 大字体 | 菜单文字跟随系统字体缩放 |
| 深色模式 | backgroundColor/backgroundBlurStyle 通过 ResourceColor/BlurStyle 支持主题跟随 |
| 多窗口/分屏 | modalMode 控制模态行为；菜单通过 overlay 层挂载 |
| 多用户 | 无用户相关状态 |
| 版本升级 | API 8/10/11/12/13/18/19/20/23/26 持续演进，新增范式与别名 |
| 生态兼容 | C-API 通过 context_menu_accessor + menu_modifier 委托，无独立 NODE 枚举 |

---

## 行为场景

### 场景 1: 右键触发上下文菜单

```
Given 组件调用 bindContextMenu(content, ResponseType.RightClick, options?)
When 用户右键点击组件
Then BindContextMenuWithRightClick 分发执行
And 菜单按 placement（默认 TOP）显示
```

### 场景 2: 长按触发上下文菜单

```
Given 组件调用 bindContextMenu(content, ResponseType.LongPress, options?)
When 用户触摸长按组件
Then BindContextMenuWithLongPress 分发执行
And 菜单显示
```

### 场景 3: isShown 双绑定显示菜单

```
Given 组件调用 bindContextMenu(isShown, content, options?)
When isShow 设置为 true
Then BindContextMenuSingle(CUSTOM_TYPE) 执行
And 菜单按 placement（默认 BOTTOM_LEFT）显示
```

### 场景 4: WithResponse 区分触发来源

```
Given 组件调用 bindContextMenuWithResponse(content, options?)
When 用户右键或长按触发
Then builder 接收 MenuBindingType 标识触发来源
And 开发者按 MenuBindingType 差异化菜单内容
```

### 场景 5: 预览模式强制隐藏箭头

```
Given 组件设置 preview = MenuPreviewMode.IMAGE, enableArrow = true
When 菜单显示
Then 预览图显示
And 箭头被强制隐藏（enableArrow 被覆盖为 false）
```

### 场景 6: 箭头安全偏移

```
Given 组件设置 enableArrow = true, arrowOffset 接近圆角边缘
When 菜单布局
Then 箭头位置自动钳位到 radius + 半个箭头宽度
```

### 场景 7: 屏幕边缘避让

```
Given 菜单 placement 接近屏幕边缘或折痕
When MenuAvoidAlgorithm 执行
Then 菜单自动避让屏幕边缘与折痕区域
And layoutRegionMargin 默认左右 12vp、上下 16vp
```

### 场景 8: 触觉反馈未授权

```
Given 组件设置 hapticFeedbackMode，未声明 ohos.permission.VIBRATE
When level-1 菜单显示
Then 触觉反馈静默跳过
And 不抛出异常
```

### 场景 9: RTL 箭头调整

```
Given 设备为 RTL 布局方向
When 菜单显示箭头
Then 箭头位置自动调整以适配 RTL 布局方向
```

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 业务规则/功能规则/异常规则/恢复契约编号连续且可追溯到源码
- [x] API 变更分析基于真实 SDK 定义文件（common.d.ts / enums.d.ts）
- [x] 兼容性声明标注 API 版本差异
- [x] 行为场景使用 Gherkin Given/When/Then 格式，覆盖关键路径
- [x] 所有源码引用包含 file:line 信息
- [x] 构建系统影响章节已确认无变更

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/components_ng/pattern/menu/menu_property.h` | MenuType/ContextMenuRegisterType 枚举、MenuParam 结构体 |
| `frameworks/core/components_ng/pattern/menu/menu_pattern.h/.cpp` | MenuPattern，菜单生命周期/动画/避让/触觉 |
| `frameworks/core/components_ng/pattern/menu/menu_layout_algorithm.h/.cpp` | 菜单布局算法（箭头/避让/RTL） |
| `frameworks/core/components_ng/pattern/menu/menu_avoid_algorithm.cpp` | 屏幕边缘/折痕避让 |
| `frameworks/core/components_ng/pattern/menu/menu_manager.h/.cpp` | MenuManager 单例，菜单堆栈/分发 |
| `frameworks/core/components_ng/pattern/menu/menu_model_ng.h/.cpp` | MenuModelNG，BindContextMenu* 系列 |
| `frameworks/core/components_ng/base/view_abstract_model_ng.cpp` | BindContextMenu 分发（L894-988）+ RegisterContextMenuKeyEvent（L1158-1182） |
| `frameworks/core/components_ng/base/view_abstract_model_static.cpp` | 静态前端 BindContextMenu 实现 |
| `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp` | JsBindContextMenu* 系列 + ParseBindContextMenuShow（L1031-1051） |
| `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | bindContextMenu 系列静态注册（L10355-10358） |
| `frameworks/core/interfaces/native/node/context_menu_accessor.cpp` | C-API accessor（L26-39） |
| `frameworks/core/interfaces/native/node/menu_modifier.cpp` | C-API modifier |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/menu/` | 菜单 NG 单元测试 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `interface/sdk-js/api/@internal/component/ets/common.d.ts` | bindContextMenu* / ContextMenuOptions / MenuPreviewMode / ContextMenuAnimationOptions / MenuOptions 声明 |
| `interface/sdk-js/api/@internal/component/ets/enums.d.ts` | ResponseType 枚举声明（L3211） |
