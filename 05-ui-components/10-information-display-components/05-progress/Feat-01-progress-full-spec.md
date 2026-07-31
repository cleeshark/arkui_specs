# 特性规格

## 概述

| 字段 | 值 |
|------|----|
| 特性名称 | Progress 进度条组件全量规格 |
| 特性编号 | Func-05-10-05-Feat-01 |
| 所属 Epic | 信息展示类组件 |
| 优先级 | P2 |
| 目标版本 | API 7-26 |
| SIG 归属 | SIG_ArkUI |
| 状态 | Baselined |
| 复杂度 | 复杂 |

Progress 组件用于展示操作完成比例。当前实现支持 Linear、Ring、ScaleRing、Eclipse、Capsule 五类进度形态，覆盖动态 ArkTS、静态 ArkTS、Modifier、C API Linear style option、主题刷新、RTL、隐私遮蔽和 contentModifier。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 新增 Progress 长期规格基线 | 仅补录已有实现，不修改代码。 |
| ADDED | 新增 Progress 功能域 design.md | 建立 `05-10-05` 共享设计基线。 |
| MODIFIED | 注册表补齐 `05-10-05 / Feat-01` | 将 `functions.yaml` 的 design 路径和 `features.yaml` 的 spec 路径补齐。 |

## 输入文档

| 文档 | 来源 |
|------|------|
| 设计基线 | `05-ui-components/10-information-display-components/05-progress/design.md` |
| 动态 SDK 声明 | `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/progress.d.ts` |
| 静态 SDK 声明 | `<OH_ROOT>/interface/sdk-js/api/arkui/component/progress.static.d.ets` |
| Modifier 声明 | `<OH_ROOT>/interface/sdk-js/api/arkui/ProgressModifier.d.ts`、`ProgressModifier.static.d.ets` |
| 组件源码 | `frameworks/core/components_ng/pattern/progress/` |
| C API | `interfaces/native/node/progress_option.h`、`interfaces/native/node/progress_option.cpp` |
| 测试 | `test/unittest/core/pattern/progress/`、`test/unittest/capi/modifiers/progress_modifier_test.cpp`、`test/unittest/capi/modifiers/generated/progress_modifier_test.cpp` |
| KB | `docs/kb/components/data_display/progress.md` |

## 用户故事

### US-1: 创建并初始化 Progress

As a ArkUI 应用开发者  
I want 使用 `Progress({ value, total, type })` 创建进度条  
So that 用户可以看到操作完成比例

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `Progress({ value: 50, total: 100, type: ProgressType.Linear })` THEN 创建 Progress FrameNode，并写入 Value、MaxValue、ProgressType 和 LayoutProperty Type。 | 正常 |
| AC-1.2 | WHEN `type` 未指定 THEN Progress 使用 Linear 默认类型。 | 正常 |
| AC-1.3 | WHEN `value < 0` THEN 实现侧写入值被截断为 0。 | 边界 |
| AC-1.4 | WHEN `value > total` THEN 实现侧写入值被截断为 total。 | 边界 |
| AC-1.5 | WHEN `type` 为 Capsule THEN 创建内部 Text FrameNode，并将 Progress 设置为可聚焦；WHEN 非 Capsule THEN 移除内部 Text 子节点并取消可聚焦。 | 正常 |

### US-2: 更新数值和前景色

As a ArkUI 应用开发者  
I want 使用 `.value()` 和 `.color()` 更新进度显示  
So that 进度和视觉颜色可以响应业务状态变化

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 调用 `.value(v)` THEN ProgressPaintProperty.Value 更新，Capsule 非用户文本会重新计算百分比文本。 | 正常 |
| AC-2.2 | WHEN 调用 `.color(ResourceColor)` THEN ProgressPaintProperty.Color 更新并标记用户主动设置颜色。 | 正常 |
| AC-2.3 | WHEN 调用 `.color(LinearGradient)` THEN ProgressPaintProperty.GradientColor 更新，绘制阶段按类型使用渐变。 | 正常 |
| AC-2.4 | WHEN 重置 color THEN 用户主动设置颜色标记清除，并允许后续主题色接管。 | 正常 |

### US-3: 设置类型专属 style

As a ArkUI 应用开发者  
I want 使用 `.style()` 设置 Linear/Ring/ScaleRing/Eclipse/Capsule 专属样式  
So that 每种进度形态可以独立配置

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN Linear style 设置 `strokeWidth`、`strokeRadius`、`enableScanEffect` THEN 分别写入布局厚度、圆角和 Linear 扫光属性。 | 正常 |
| AC-3.2 | WHEN Ring style 设置 `strokeWidth`、`shadow`、`status`、`enableScanEffect` THEN 分别写入厚度、阴影、进度状态和 Ring 扫光属性。 | 正常 |
| AC-3.3 | WHEN ScaleRing style 设置 `scaleCount`、`scaleWidth`、`strokeWidth` THEN 写入刻度数量、刻度宽度和厚度。 | 正常 |
| AC-3.4 | WHEN Capsule style 设置 `borderColor`、`borderWidth`、`borderRadius` THEN 写入 Capsule 边框颜色、边框宽度和圆角。 | 正常 |
| AC-3.5 | WHEN Capsule style 设置 `content`、`font`、`fontColor`、`showDefaultPercentage` THEN 更新内部 Text 子节点内容和文本样式。 | 正常 |
| AC-3.6 | WHEN `strokeRadius > strokeWidth / 2` THEN 绘制阶段按 `strokeWidth / 2` 上限处理。 | 边界 |

### US-4: 渲染五类 Progress

As a ArkUI 应用开发者  
I want Progress 根据类型分派到不同绘制路径  
So that Linear/Ring/ScaleRing/Eclipse/Capsule 具有各自的视觉形态

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN type 为 Linear THEN 使用 Linear 绘制路径，并在存在渐变时使用 Linear 渐变绘制。 | 正常 |
| AC-4.2 | WHEN type 为 Ring THEN 使用 Ring 背景、进度、阴影和扫光绘制路径。 | 正常 |
| AC-4.3 | WHEN type 为 ScaleRing THEN 使用 ScaleRing 绘制路径；当刻度不足以独立展示时可退化为 Ring 绘制。 | 边界 |
| AC-4.4 | WHEN type 为 Eclipse THEN C++ 内部按 MOON 形态绘制。 | 正常 |
| AC-4.5 | WHEN type 为 Capsule THEN 使用 Capsule 横向或纵向绘制路径，并处理边框、渐变和扫光。 | 正常 |

### US-5: 支持动画、可见区和 RTL

As a ArkUI 应用开发者  
I want Progress 的动画和方向适配系统状态  
So that 进度显示在不同语言方向和可见性下保持正确

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN Ring style `status=LOADING` THEN ProgressModifier 启动 loading 动画。 | 正常 |
| AC-5.2 | WHEN Progress 不在可见区域 THEN Pattern 停止循环动画。 | 异常 |
| AC-5.3 | WHEN 系统语言方向切换为 RTL THEN Pattern 更新 RTL 状态，Linear/Ring/Moon/Capsule 绘制方向相应调整。 | 正常 |
| AC-5.4 | WHEN 主题 scope 更新且颜色/背景色不是用户主动设置 THEN Progress 使用新主题颜色刷新。 | 正常 |

### US-6: 支持 Capsule 交互

As a ArkUI 应用开发者  
I want Capsule Progress 支持焦点、悬停、按下反馈  
So that Capsule 形态具备可感知交互状态

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN Capsule 获得焦点 THEN Text 颜色、缩放和阴影按焦点态更新。 | 正常 |
| AC-6.2 | WHEN Capsule 悬停 THEN modifier 进入 hovered 状态。 | 正常 |
| AC-6.3 | WHEN Capsule 按下 THEN 背景、选中色和边框色与 touchEffect 混合。 | 正常 |
| AC-6.4 | WHEN Capsule 释放或取消 THEN 背景、选中色和边框色恢复原值。 | 恢复 |
| AC-6.5 | WHEN Capsule disabled THEN Progress 透明度应用禁用态系数。 | 异常 |

### US-7: 支持 contentModifier 和隐私模式

As a ArkUI 应用开发者  
I want 使用 contentModifier 自定义 UI，并在敏感场景启用 privacySensitive  
So that Progress 能在自定义和隐私场景中正确展示

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-7.1 | WHEN 设置 `contentModifier` THEN Pattern 保存 makeFunc 并进入自定义内容模式。 | 正常 |
| AC-7.2 | WHEN `contentModifier` 重置为空 THEN Progress 回退到默认绘制路径。 | 恢复 |
| AC-7.3 | WHEN contentModifier 生效 THEN LayoutAlgorithm 对默认内容测量返回空结果，由自定义内容负责展示。 | 正常 |
| AC-7.4 | WHEN `privacySensitive(true)` THEN PaintProperty.IsSensitive 为 true，绘制值遮蔽并联动 Capsule 内部 Text 遮蔽。 | 正常 |

### US-8: 使用 C API Linear style option

As a Native 开发者  
I want 使用 `OH_ArkUI_ProgressLinearStyleOption_*` 配置 Linear Progress  
So that NDK 场景可设置 Linear 扫光、平滑动画、厚度和圆角

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-8.1 | WHEN 调用 `OH_ArkUI_ProgressLinearStyleOption_Create` THEN 返回包含默认值的 option。 | 正常 |
| AC-8.2 | WHEN 对非 null option 调用 Set/Get THEN 对应字段被写入并可读回。 | 正常 |
| AC-8.3 | WHEN option 为 null 调用 Destroy/Set THEN 函数安全返回。 | 边界 |
| AC-8.4 | WHEN option 为 null 调用 Get THEN 返回默认 false 或 -1.0。 | 边界 |

### US-9: 支持静态 ArkTS 范式

As a 静态 ArkTS 应用开发者  
I want 使用 static `Progress`、Builder 和 `setProgressOptions()`  
So that 静态编译范式可使用同一 Progress 能力

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-9.1 | WHEN 调用静态 `Progress(options)` THEN 通过 static modifier 初始化 value、total、type。 | 正常 |
| AC-9.2 | WHEN 调用 `setProgressOptions(options?)` THEN 静态实现重新初始化 Progress options。 | 正常 |
| AC-9.3 | WHEN 静态 style 参数为 undefined THEN 对应属性重置。 | 恢复 |

### US-10: 提供调试和无障碍入口

As a ArkUI 框架维护者  
I want Progress 能被 Inspector、Dump、Accessibility 定位  
So that 问题排查和无障碍值读取有稳定入口

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-10.1 | WHEN 调用 Inspector/ToJson THEN 输出 Progress style、ringStyle、linearStyle、capsuleStyle 和隐私相关字段。 | 正常 |
| AC-10.2 | WHEN 无障碍读取 Progress THEN 可访问性属性提供 range/value/text 信息。 | 正常 |

## 验收追踪

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_model_ng.cpp:31`、`progress_model_static.cpp` |
| AC-1.2 | R-2 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.h:244` |
| AC-1.3 | R-3 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_model_ng.cpp:103`、`progress_model_static.cpp` |
| AC-1.4 | R-3 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_model_ng.cpp:103`、`progress_model_static.cpp` |
| AC-1.5 | R-4 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_model_ng.cpp:31`、`progress_model_static.cpp` |
| AC-2.1 | R-5 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_model_ng.cpp:103` |
| AC-2.2 | R-6 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_model_ng.cpp:121` |
| AC-2.3 | R-7 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/progress_paint_property.h:97`、`progress_modifier.cpp:941` |
| AC-2.4 | R-8 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_model_ng.cpp:131`、`progress_pattern.cpp:866` |
| AC-3.1 | R-9 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/bridge/progress_static_modifier.cpp:38` |
| AC-3.2 | R-10 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/bridge/progress_static_modifier.cpp:56` |
| AC-3.3 | R-11 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/bridge/progress_static_modifier.cpp:105` |
| AC-3.4 | R-12 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/bridge/progress_static_modifier.cpp:72` |
| AC-3.5 | R-13 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/progress_model_static.cpp` |
| AC-3.6 | R-14 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/progress_paint_method.h:106` |
| AC-4.1 | R-15 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/progress_modifier.cpp:829` |
| AC-4.2 | R-16 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/progress_modifier.cpp:832` |
| AC-4.3 | R-17 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/progress_modifier.cpp:1593` |
| AC-4.4 | R-18 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/bridge/progress_static_modifier.cpp:195` |
| AC-4.5 | R-19 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/progress_modifier.cpp:844` |
| AC-5.1 | R-20 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/progress_modifier.cpp:324` |
| AC-5.2 | R-21 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:152` |
| AC-5.3 | R-22 | TASK-05-10-05-F01 | VM-2 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:604`、`progress_modifier.cpp:899` |
| AC-5.4 | R-23 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:866` |
| AC-6.1 | R-24 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:212` |
| AC-6.2 | R-25 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:353` |
| AC-6.3 | R-26 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:409` |
| AC-6.4 | R-27 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:409` |
| AC-6.5 | R-28 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:409` |
| AC-7.1 | R-29 | TASK-05-10-05-F01 | VM-3 | `frameworks/core/components_ng/pattern/progress/progress_model_ng.cpp:667` |
| AC-7.2 | R-30 | TASK-05-10-05-F01 | VM-3 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp` |
| AC-7.3 | R-31 | TASK-05-10-05-F01 | VM-3 | `frameworks/core/components_ng/pattern/progress/progress_layout_algorithm.cpp:39` |
| AC-7.4 | R-32 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:759`、`progress_paint_method.h:62` |
| AC-8.1 | R-33 | TASK-05-10-05-F01 | VM-4 | `interfaces/native/node/progress_option.cpp:27` |
| AC-8.2 | R-34 | TASK-05-10-05-F01 | VM-4 | `interfaces/native/node/progress_option.cpp:46`、`progress_option.cpp:78` |
| AC-8.3 | R-35 | TASK-05-10-05-F01 | VM-4 | `interfaces/native/node/progress_option.cpp:38`、`progress_option.cpp:46` |
| AC-8.4 | R-36 | TASK-05-10-05-F01 | VM-4 | `interfaces/native/node/progress_option.cpp:78` |
| AC-9.1 | R-37 | TASK-05-10-05-F01 | VM-5 | `frameworks/core/components_ng/pattern/progress/bridge/progress_static_modifier.cpp:238` |
| AC-9.2 | R-38 | TASK-05-10-05-F01 | VM-5 | `<OH_ROOT>/interface/sdk-js/api/arkui/component/progress.static.d.ets:491` |
| AC-9.3 | R-39 | TASK-05-10-05-F01 | VM-5 | `frameworks/core/components_ng/pattern/progress/bridge/progress_static_modifier.cpp:136` |
| AC-10.1 | R-40 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:182`、`progress_pattern.cpp:577` |
| AC-10.2 | R-41 | TASK-05-10-05-F01 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_accessibility_property.h` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 创建 Progress | 写入 Value、MaxValue、ProgressType、LayoutProperty Type | `ProgressModelNG::Create` 为入口 | AC-1.1 |
| R-2 | 行为 | type 未指定 | 使用 Linear | Pattern 默认字段为 Linear | AC-1.2 |
| R-3 | 边界 | value 小于 0 或大于 total | 截断到 `[0,total]` | total 缺省 100 | AC-1.3, AC-1.4 |
| R-4 | 行为 | type 为 Capsule/非 Capsule | Capsule 创建 Text 子节点并可聚焦；非 Capsule 移除子节点 | API 10 后 Capsule 初始化交互 | AC-1.5 |
| R-5 | 行为 | 调用 `.value(v)` | 更新 Value 并在 Capsule 非用户文本时刷新百分比 | `v` 继续受 R-3 约束 | AC-2.1 |
| R-6 | 行为 | 调用 `.color(ResourceColor)` | 更新 Color 并标记用户设置 | reset 后标记清除 | AC-2.2 |
| R-7 | 行为 | 调用 `.color(LinearGradient)` | 更新 GradientColor | 渐变绘制按类型分派 | AC-2.3 |
| R-8 | 恢复 | 重置 color | 回退到主题控制 | 用户设置标记清除 | AC-2.4 |
| R-9 | 行为 | Linear style option 设置 | 更新 strokeWidth、strokeRadius、scan、smooth | strokeRadius 受 R-14 约束 | AC-3.1 |
| R-10 | 行为 | Ring style option 设置 | 更新 strokeWidth、shadow、status、scan、smooth | LOADING 受 R-20 约束 | AC-3.2 |
| R-11 | 行为 | ScaleRing style option 设置 | 更新 scaleCount、scaleWidth、strokeWidth、smooth | 刻度绘制可退化 | AC-3.3 |
| R-12 | 行为 | Capsule border style 设置 | 更新 borderColor、borderWidth、borderRadius | borderRadius 受高度约束 | AC-3.4 |
| R-13 | 行为 | Capsule text style 设置 | 更新内部 Text content/font/fontColor/showDefaultPercentage | content 设置后标记用户文本 | AC-3.5 |
| R-14 | 边界 | strokeRadius 超过 strokeWidth/2 | 按 strokeWidth/2 上限绘制 | 负值按绘制逻辑收敛 | AC-3.6 |
| R-15 | 行为 | Linear 绘制 | 分派 Linear 或 LinearGradient 绘制 | RTL 受 R-22 约束 | AC-4.1 |
| R-16 | 行为 | Ring 绘制 | 绘制背景、进度、阴影、扫光 | status 可为 LOADING | AC-4.2 |
| R-17 | 边界 | ScaleRing 绘制刻度不可独立展示 | 可退化为 Ring 绘制 | 由 ScaleRing 绘制逻辑判定 | AC-4.3 |
| R-18 | 行为 | SDK Eclipse 类型进入 C++ | 映射为内部 MOON 绘制 | 仅内部命名差异 | AC-4.4 |
| R-19 | 行为 | Capsule 绘制 | 分派 Capsule 横向/纵向、渐变、边框、扫光路径 | 高度大于宽度可走纵向路径 | AC-4.5 |
| R-20 | 行为 | Ring status=LOADING | 启动 loading 动画 | loading 优先于普通 value 展示 | AC-5.1 |
| R-21 | 异常 | Progress 离开可见区域 | 停止循环动画 | 可见区恢复后按状态继续 | AC-5.2 |
| R-22 | 行为 | 语言方向为 RTL | 更新 RTL 状态并影响绘制方向 | 影响 Linear/Ring/Moon/Capsule | AC-5.3 |
| R-23 | 行为 | 主题 scope 更新且颜色非用户设置 | 使用主题色刷新 | 用户主动设置颜色不被覆盖 | AC-5.4 |
| R-24 | 行为 | Capsule 获得焦点 | 文本颜色、缩放、阴影进入焦点态 | 仅 Capsule 注册 | AC-6.1 |
| R-25 | 行为 | Capsule 悬停 | hovered 状态更新 | 仅 Capsule 注册 | AC-6.2 |
| R-26 | 行为 | Capsule 按下 | 颜色混合 touchEffect | 保存原值以恢复 | AC-6.3 |
| R-27 | 恢复 | Capsule 释放或取消 | 恢复按下前颜色 | 依赖 Optional 原值 | AC-6.4 |
| R-28 | 异常 | Capsule disabled | 透明度应用禁用态系数 | 主题提供系数 | AC-6.5 |
| R-29 | 行为 | 设置 contentModifier | 保存 makeFunc 并进入自定义内容模式 | 自定义内容负责展示 | AC-7.1 |
| R-30 | 恢复 | contentModifier 为空 | 回退默认绘制 | clip 和默认布局恢复 | AC-7.2 |
| R-31 | 行为 | contentModifier 生效时测量默认内容 | 默认 MeasureContent 返回空 | 避免默认内容与自定义内容冲突 | AC-7.3 |
| R-32 | 行为 | privacySensitive=true | 绘制值遮蔽并联动 Capsule Text 遮蔽 | 不修改实际业务 value | AC-7.4 |
| R-33 | 行为 | C API Create | 返回默认 option | 默认 scan=false、smooth=true、strokeWidth=4.0、strokeRadius=-1.0 | AC-8.1 |
| R-34 | 行为 | C API Set/Get 非 null | 字段可写入并读回 | 调用方持有 option 生命周期 | AC-8.2 |
| R-35 | 边界 | C API Destroy/Set null | 安全返回 | 无异常、无崩溃 | AC-8.3 |
| R-36 | 边界 | C API Get null | 返回 false 或 -1.0 | 与函数返回类型匹配 | AC-8.4 |
| R-37 | 行为 | 静态 Progress(options) | 通过 static modifier 初始化属性 | static API since 23 | AC-9.1 |
| R-38 | 行为 | setProgressOptions(options?) | 重新设置 Progress options | staticonly since 26.0.0 | AC-9.2 |
| R-39 | 恢复 | 静态 style undefined/null | 重置对应属性 | static modifier reset path | AC-9.3 |
| R-40 | 行为 | Inspector/Dump 调用 | 输出 Progress 调试字段 | 不作为公开 API | AC-10.1 |
| R-41 | 行为 | 无障碍读取 | 返回 Progress range/value/text | 依赖 AccessibilityProperty | AC-10.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | 创建、value、Pattern、Capsule、调试、无障碍 | `test/unittest/core/pattern/progress/` | Progress FrameNode、属性写入、Pattern 生命周期、ToJson/Dump、Accessibility。 |
| VM-2 | 绘制、style、动画、RTL、渐变 | `test/unittest/core/pattern/progress/progress_modifier_test_ng.cpp`、`progress_modifier_plug_test_ng.cpp` | Linear/Ring/Scale/Moon/Capsule 绘制分派和 modifier 状态。 |
| VM-3 | contentModifier | `test/unittest/core/pattern/progress/progress_content_modifier_test_ng.cpp`、`progress_builder_test_ng.cpp` | 自定义内容模式、builder、默认测量回退。 |
| VM-4 | C API Linear style option | `interfaces/native/node/progress_option.cpp` 源码审阅、`test/unittest/capi/modifiers/progress_modifier_test.cpp` | option 默认值、null 安全、Set/Get。 |
| VM-5 | 静态/生成 Modifier | `test/unittest/capi/modifiers/progress_modifier_test.cpp`、`test/unittest/capi/modifiers/generated/progress_modifier_test.cpp` | static modifier 的 setProgressOptions/value/color/style/privacySensitive。 |

## API 变更分析

### 新增 API

本次无新增 API；下表列出现有 API 开放范围。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `Progress(options)` | Public | `ProgressOptions` | `ProgressAttribute` | N/A | 创建 Progress 组件 | AC-1.1 |
| `.value(value)` | Public | number/double/undefined(static) | `ProgressAttribute`/`this` | N/A | 更新当前进度值 | AC-2.1 |
| `.color(value)` | Public | `ResourceColor` 或 `LinearGradient` | `ProgressAttribute`/`this` | N/A | 更新前景色或渐变色 | AC-2.2, AC-2.3 |
| `.style(value)` | Public | Progress style option | `ProgressAttribute`/`this` | N/A | 更新类型专属样式 | AC-3.1 |
| `.privacySensitive(value)` | Public | boolean/Optional boolean | `ProgressAttribute`/`this` | N/A | 启用隐私遮蔽 | AC-7.4 |
| `.contentModifier(modifier)` | Public | `ContentModifier<ProgressConfiguration>` | `ProgressAttribute`/`this` | N/A | 自定义 Progress 内容 | AC-7.1 |
| `.setProgressOptions(options?)` | Public static | `ProgressOptions?` | `this` | N/A | 静态范式更新 options | AC-9.2 |
| `OH_ArkUI_ProgressLinearStyleOption_*` | Public C API | `ArkUI_ProgressLinearStyleOption*` 和字段值 | pointer/bool/float/void | N/A | 配置 Linear style option | AC-8.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `ProgressOptions.style?: ProgressStyle` | 废弃 | 动态 API 历史创建参数 | 使用 `type?: ProgressType` | AC-1.1 |
| `ProgressStyle` | 变更 | 历史 style 枚举兼容 | 新代码优先使用 `ProgressType` | AC-1.2 |
| `CapsuleStyleOptions.content` | 变更 | API 20 dynamic 从 string 扩展为 `ResourceStr` | 动态 API 可传资源字符串，静态 API 23 仍声明 string | AC-3.5 |
| `CapsuleStyleOptions.borderRadius` | 变更 | API 18 dynamic / API 23 static 后可配置 Capsule 圆角 | 使用 `LengthMetrics` | AC-3.4 |
| `setProgressOptions(options?)` | 变更 | API 26 staticonly 静态 Builder 形态 | 静态 Builder 起始属性设置时调用 | AC-9.2 |

## 接口规格

### 接口定义

**Progress 组件创建**

| 属性 | 值 |
|------|----|
| 函数签名 | `Progress(options: ProgressOptions): ProgressAttribute` |
| 返回值 | `ProgressAttribute`，用于链式设置属性 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | number/double | 是 | 0 | 实现侧截断到 `[0,total]` |
| total | number/double | 否 | 100 | 作为最大值参与截断和百分比计算 |
| type | ProgressType | 否 | Linear | Linear/Ring/Eclipse/ScaleRing/Capsule |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 创建 Linear Progress | 写入 ProgressType.LINEAR 并走 Linear 布局/绘制 | AC-1.1 |
| 2 | 创建 Capsule Progress | 创建内部 Text 子节点并注册交互 | AC-1.5 |
| 3 | value 越界 | 截断到边界值 | AC-1.3, AC-1.4 |

**Progress 属性方法**

| 属性 | 值 |
|------|----|
| 函数签名 | `.value(value)`、`.color(value)`、`.style(value)`、`.privacySensitive(value)`、`.contentModifier(modifier)` |
| 返回值 | `ProgressAttribute` 或 `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 至 AC-7.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | number/double/undefined | 是 | undefined 时 static 重置 | value 小于 0 或大于 total 由实现截断 |
| color | ResourceColor/LinearGradient/undefined | 是 | undefined 时重置 | gradient 进入 GradientColor |
| style | Linear/Ring/ScaleRing/Capsule/Progress style option | 是 | undefined 时重置 | 与类型匹配；静态声明 union 不单列 EclipseStyleOptions |
| privacySensitive | boolean/Optional boolean | 是 | false | true 时遮蔽绘制和 Capsule Text |
| contentModifier | ContentModifier/undefined | 是 | undefined 时重置 | 生效后默认内容测量回退 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 更新 | ProgressPaintProperty.Value 更新 | AC-2.1 |
| 2 | color 更新 | Color 或 GradientColor 更新 | AC-2.2, AC-2.3 |
| 3 | style 更新 | 类型专属属性更新 | AC-3.1 |
| 4 | contentModifier 设置 | 自定义内容接管 | AC-7.1 |
| 5 | privacySensitive=true | 视觉值和文本遮蔽 | AC-7.4 |

**C API Linear style option**

| 属性 | 值 |
|------|----|
| 函数签名 | `OH_ArkUI_ProgressLinearStyleOption_Create/Destroy/Set*/Get*` |
| 返回值 | pointer、bool、float 或 void |
| 开放范围 | Public C API |
| 错误码 | N/A |
| 关联 AC | AC-8.1 至 AC-8.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| option | `ArkUI_ProgressLinearStyleOption*` | 是 | null 安全 | Set/Destroy null 直接返回；Get null 返回默认 |
| scanEffect | bool | 否 | false | 控制 Linear 扫光 |
| smoothEffect | bool | 否 | true | 控制平滑动画 |
| strokeWidth | float | 否 | 4.0 | 单位由 Native Node style 消费 |
| strokeRadius | float | 否 | -1.0 | -1.0 表示默认圆角 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Create | 返回默认 option | AC-8.1 |
| 2 | 非 null Set/Get | 字段写入并读回 | AC-8.2 |
| 3 | null Set/Destroy/Get | 安全返回或默认值 | AC-8.3, AC-8.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；本次只补录已有实现。已存在 API 版本差异包括动态 API 7/8/10/12/18/20 与静态 API 23/26。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 动态 Progress 创建 API 7；ProgressType API 8；类型专属 style、ProgressStatus、scan/smooth API 10；contentModifier/隐私/C API option API 12；Capsule borderRadius API 18；静态 Progress API 23；静态 Builder/setProgressOptions API 26。
- **API 版本号策略:** 公开契约以 SDK `@since` 为准；C++ 内部枚举和字段名只作为实现证据。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 组件化路径 | Progress 已按 `pattern/progress/bridge/` 和 dynamic module 组织。 | AC-9.1 |
| 状态分层 | type/strokeWidth 进入 LayoutProperty，value/color/style 多数进入 PaintProperty。 | AC-2.1, AC-3.1 |
| Capsule 内部 Text | Capsule 文本由 Progress 内部 Text 子节点承载。 | AC-1.5, AC-3.5 |
| SDK 权威 | 外部 API 签名和 since 版本以 interface_sdk-js 声明为准。 | AC-9.2 |
| C API 范围 | 当前仅记录 Linear style option C API。 | AC-8.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 可见区外停止循环动画，避免无效动画持续运行 | VM-1/VM-2 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:152` |
| 功耗 | Ring loading 和扫光动画受可见性控制 | VM-2 | `frameworks/core/components_ng/pattern/progress/progress_modifier.cpp:324` |
| 内存 | Capsule Text 子节点只在 Capsule 类型保留 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_model_ng.cpp:31` |
| 安全 | privacySensitive 不改变真实 value，仅遮蔽视觉输出 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:759` |
| 可靠性 | C API option null 安全 | VM-4 | `interfaces/native/node/progress_option.cpp:38` |
| 可测试性 | Core、ContentModifier、C API modifier 均有稳定测试入口 | VM-1 至 VM-5 | `test/unittest/core/pattern/progress/` |
| 自动化维测 | Inspector/Dump 输出 Progress 状态 | VM-1 | `frameworks/core/components_ng/pattern/progress/progress_pattern.cpp:182` |
| 定界定位 | KB 路由到 SDK、bridge、model、layout、paint、C API、测试 | KB 校验 | `docs/kb/components/data_display/progress.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无组件级设备差异；尺寸由约束、主题和 API 版本决定 | Linear/Capsule 可因宽高关系呈现横向或纵向 | VM-1/VM-2 | `frameworks/core/components_ng/pattern/progress/progress_layout_algorithm.cpp:39` |
| 平板 | 同手机 | 布局约束决定尺寸 | VM-1/VM-2 | `frameworks/core/components_ng/pattern/progress/progress_layout_algorithm.cpp:39` |
| 折叠屏 | 同手机；窗口尺寸变化会重新布局 | 依赖 FrameNode/layout pipeline 重新测量 | VM-1/VM-2 | `frameworks/core/components_ng/pattern/progress/progress_layout_algorithm.cpp:39` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | ProgressAccessibilityProperty 提供 range/value/text 定位入口。 | AC-10.2 |
| 大字体 | 是 | Capsule 文本布局读取 fontScale 并可增加 padding。 | AC-3.5 |
| 深色模式 | 是 | 颜色未由用户主动设置时跟随主题 scope 更新。 | AC-5.4 |
| 多窗口/分屏 | 是 | 按布局约束重新测量，无独立窗口状态。 | AC-4.1 |
| 多用户 | 否 | 无用户隔离数据。 | N/A |
| 版本升级 | 是 | 动态/静态 API since 差异已列入兼容性。 | AC-9.2 |
| 生态兼容 | 是 | 保留 `ProgressStyle` 和废弃 `style` 创建参数兼容历史用法。 | AC-1.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Progress full behavior
  作为 ArkUI 应用开发者
  我想要 Progress 正确处理数值、类型、样式、动画和隐私
  以便在信息展示场景稳定呈现进度

  Scenario: Clamp progress value
    Given a Progress with total 100
    When value is set to 150
    Then stored visual value becomes 100

  Scenario: Capsule internal text follows value
    Given a Capsule Progress with showDefaultPercentage enabled
    When value changes and content is not set by user
    Then the internal Text percentage is recalculated

  Scenario: Ring loading animation
    Given a Ring Progress
    When style status is LOADING
    Then the loading animation state starts

  Scenario: Privacy sensitive rendering
    Given a Progress with privacySensitive true
    When the component is painted
    Then visual progress is obscured
    And Capsule text is obscured when present
```

## Spec 自检清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（已有能力补录，不新增 API，不改 ABI）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/foundation/arkui/ace_engine"
    query: "Progress component pattern model layout paint bridge C API"
  - repo: "OpenHarmony/interface_sdk-js"
    query: "Progress API declarations dynamic static modifier"
```

**关键文档:** `docs/kb/components/data_display/progress.md`
