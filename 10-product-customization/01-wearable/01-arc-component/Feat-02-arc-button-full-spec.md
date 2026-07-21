# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | ArcButton 圆弧按钮全量规格 |
| 特性编号 | Func-10-01-01-Feat-02 |
| FuncID | 10-01-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 18 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出 ArcButton 自引入以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ArcButton 动态组件 (@ComponentV2) | @since 18, Dynamic API |
| ADDED | ArcButtonPosition enum: TOP_EDGE=0, BOTTOM_EDGE=1 | 位置枚举 |
| ADDED | ArcButtonStyleMode enum: EMPHASIZED_LIGHT=0, EMPHASIZED_DARK=1, NORMAL_LIGHT=2, NORMAL_DARK=3, CUSTOM=4 | 样式模式枚举 |
| ADDED | ArcButtonStatus enum: NORMAL=0, PRESSED=1, DISABLED=2 | 状态枚举 |
| ADDED | ArcButtonProgressConfig (@ObservedV2, @Trace): value, total?, color? | 进度配置 |
| ADDED | ArcButtonOptions (@ObservedV2, @Trace): position, styleMode, status, label, backgroundBlurStyle, backgroundColor, shadowColor, shadowEnabled, fontSize, fontColor, pressedFontColor, fontStyle, fontFamily, fontMargin, progressConfig?, onTouch?, onClick? | 主选项 |
| ADDED | DataProcessUtil: 两圆相交路径计算 | SVG 路径裁剪 |
| ADDED | Text auto-fit: measureText + 13-19fp 自适应 + MARQUEE | 文字自适应 |
| ADDED | Press animation: InterpolatingSpring(10, 1, 350, 35) | 按压弹簧动画 |
| ADDED | Progress mode: ProgressType.Capsule + clipShape(Path) | 进度条模式 |
| ADDED | Static API (ArcButton) | @since 23 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/10-product-customization/01-wearable/01-arc-component/design.md`
- **KB 路由**: `docs/kb/components/selector/arc_button.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.advanced.ArcButton.d.ets`
  - Static: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.advanced.ArcButton.static.d.ets`
  - CAPI / NDK: 无

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: ArcButton 基础创建与配置

**角色**: 应用开发者
**期望**: 我想要创建圆弧按钮并配置位置、样式和状态
**价值**: 以便在穿戴式圆形设备上提供弧形按钮交互

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 `ArcButton({ options: new ArcButtonOptions({}) })` THEN 使用默认配置：position=BOTTOM_EDGE, styleMode=EMPHASIZED_LIGHT, status=NORMAL, label='' （`arcbutton.ets:217-248`） | 正常 |
| AC-1.2 | WHEN 设置 position=TOP_EDGE THEN isUp=true，组件 rotate 180°（`arcbutton.ets:379, 568`） | 正常 |
| AC-1.3 | WHEN 设置 status=DISABLED THEN 组件 enabled=false，EMPHASIZED_LIGHT 模式下 opacity=0.4（`arcbutton.ets:581-583`） | 正常 |
| AC-1.4 | WHEN 设置 label='确定' THEN 按钮中心渲染 Text，使用 maxFontSize(19fp)/minFontSize(13fp) 自适应（`arcbutton.ets:504-523`） | 正常 |

### US-2: ArcButton SVG 路径裁剪

**角色**: 应用开发者
**期望**: 我想要按钮形状精确匹配圆形表盘边缘
**价值**: 以便弧形按钮与表盘外形无缝融合

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN aboutToAppear 执行 THEN DataProcessUtil.initData() 初始化 dial 圆（表盘）和 arc 圆（弧形），calculate() 计算两圆相交路径点（`arcbutton.ets:422-431`） | 正常 |
| AC-2.2 | WHEN generatePath 执行 THEN 生成 SVG Path：M → A(上弧) → Q(倒角) → A(下弧) → Q(倒角)，通过 clipShape(Path) 裁剪 Button/Progress（`arcbutton.ets:439-479, 569`） | 正常 |
| AC-2.3 | WHEN sys.float 主题资源获取失败（arcButtonTheme 值为 0）THEN aboutToAppear 直接返回，console.error 输出错误（`arcbutton.ets:423-425`） | 异常 |

### US-3: ArcButton 按压交互与动画

**角色**: 终端用户
**期望**: 我想要在按压按钮时获得弹性反馈动画
**价值**: 以便获得自然的按压交互体验

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 触摸按下（TouchType.Down）THEN scaleX/scaleY 设为 scaleValue(1)，btnColor 切换为 btnPressColor，fontColor 切换为 textPressColor（`arcbutton.ets:611-615`） | 正常 |
| AC-3.2 | WHEN 触摸抬起（TouchType.Up）THEN scaleX/scaleY 恢复为 1，btnColor 恢复为 btnNormalColor，fontColor 恢复为 textNormalColor（`arcbutton.ets:617-621`） | 正常 |
| AC-3.3 | WHEN 按压动画使用 InterpolatingSpring(10, 1, 350, 35) 弹簧曲线 THEN 缩放动画通过 .animation({ curve: this.curves }) 应用（`arcbutton.ets:274, 584`） | 正常 |
| AC-3.4 | WHEN status 设置为 PRESSED THEN 直接使用 btnPressColor 和 textPressColor，不切换 TouchType（`arcbutton.ets:604-608`） | 正常 |

### US-4: ArcButton 文字自适应

**角色**: 应用开发者
**期望**: 我想要按钮文字在容器宽度内自动适配
**价值**: 以便不同长度的文字都能正确显示

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN judgeTextWidth 执行 THEN 使用 measure.measureText 以 13fp 测量文字宽度，与容器宽度比较（`arcbutton.ets:410-420`） | 正常 |
| AC-4.2 | WHEN 文字宽度 ≤ 容器宽度 THEN isExceed=false，使用 TextBuilderNormal：maxFontSize(19fp)/minFontSize(13fp) + maxLines(1) 自动缩放（`arcbutton.ets:504-523`） | 正常 |
| AC-4.3 | WHEN 文字宽度 > 容器宽度 THEN isExceed=true，使用 TextBuilderIsExceed：固定 13fp + textOverflow(MARQUEE)（`arcbutton.ets:482-501`） | 边界 |
| AC-4.4 | WHEN 设置 options.fontSize THEN TextBuilderNormal 使用固定字号（cover 方法转换），不启用 maxFontSize/minFontSize 自适应（`arcbutton.ets:510-512`） | 正常 |

### US-5: ArcButton 颜色方案

**角色**: 应用开发者
**期望**: 我想要选择不同的颜色风格模式
**价值**: 以便按钮在不同场景下使用合适的视觉风格

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN styleMode=EMPHASIZED_LIGHT THEN btnNormal=comp_background_emphasize, textNormal=#FFFFFF, btnPress=normal+#1AFFFFFF混合, btnDisable=#1F71FF, textDisable=#FFFFFF（`arcbutton.ets:315-323`） | 正常 |
| AC-5.2 | WHEN styleMode=EMPHASIZED_DARK THEN btnNormal=#BF2629, textNormal=#FFFFFF, btnDisable=#4C0f10, textDisable=#99FFFFFF（`arcbutton.ets:345-353`） | 正常 |
| AC-5.3 | WHEN styleMode=CUSTOM THEN 使用 options.backgroundColor/fontColor/pressedFontColor，btnPress = backgroundColor.blendColor(#1AFFFFFF)（`arcbutton.ets:355-362`） | 正常 |
| AC-5.4 | WHEN status=DISABLED + styleMode=EMPHASIZED_LIGHT THEN btnColor=btnDisableColor, fontColor=textDisableColor, opacity=0.4（`arcbutton.ets:363-365, 582-583`） | 正常 |

### US-6: ArcButton 进度条模式

**角色**: 应用开发者
**期望**: 我想要按钮显示加载进度
**价值**: 以便在异步操作时提供视觉反馈

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 设置 progressConfig `{ value: 30, total: 100 }` THEN 渲染 Progress(ProgressType.Capsule) 替代 Button，value=30, total=100（`arcbutton.ets:553-563`） | 正常 |
| AC-6.2 | WHEN progressConfig.color 未设置 THEN 使用 backgroundColor 或默认 #1F71FF（`arcbutton.ets:296-304`） | 正常 |
| AC-6.3 | WHEN progressConfig.total 未设置 THEN 默认 100（`arcbutton.ets:305-309`） | 边界 |
| AC-6.4 | WHEN 进度条模式渲染 THEN Progress 应用 clipShape(Path) 裁剪为弧形，rotate(TOP_EDGE 时 180°)，backgroundBlurStyle 和 shadow 生效（`arcbutton.ets:556-563`） | 正常 |

### US-7: ArcButton 阴影与模糊

**角色**: 应用开发者
**期望**: 我想要按钮有阴影和背景模糊效果
**价值**: 以便增强按钮的视觉层次感

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN shadowEnabled=true THEN 按钮应用 shadow：radius=4, color=shadowColor, offsetY=3（`arcbutton.ets:540-549`） | 正常 |
| AC-7.2 | WHEN shadowEnabled=false THEN getShadow 返回 undefined，不应用阴影（`arcbutton.ets:541-543`） | 正常 |
| AC-7.3 | WHEN 设置 backgroundBlurStyle THEN Button/Progress 应用 backgroundBlurStyle，disableSystemAdaptation=true（`arcbutton.ets:571-572, 562`） | 正常 |

### US-8: ArcButton 响应式更新

**角色**: 应用开发者
**期望**: 我想要在运行时动态修改按钮属性并立即生效
**价值**: 以便根据应用状态更新按钮外观

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN @Monitor 监听的 options 字段变化（label/type/fontSize/styleMode/status/backgroundColor/fontColor/progressConfig.*）THEN optionsChange 执行：更新 fontSize, judgeTextWidth, changeStatus, progressOptionsChange（`arcbutton.ets:285-293`） | 正常 |
| AC-8.2 | WHEN options.label 变化 THEN judgeTextWidth 重新测量文字宽度，切换 TextBuilderNormal/TextBuilderIsExceed（`arcbutton.ets:289-290`） | 正常 |
| AC-8.3 | WHEN options.progressConfig.value 变化 THEN progressValue 更新，Progress 组件重新渲染（`arcbutton.ets:296-297`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2, R-3 | TASK-ARC-02 | UT | `advanced_ui_component/arcbutton/source/arcbutton.ets` |
| AC-2.1 ~ AC-2.3 | R-4, R-5, R-6 | TASK-ARC-02 | UT | SVG 路径测试 |
| AC-3.1 ~ AC-3.4 | R-7, R-8, R-9 | TASK-ARC-02 | UT + 手工 | 按压动画测试 |
| AC-4.1 ~ AC-4.4 | R-10, R-11 | TASK-ARC-02 | UT + 手工 | 文字自适应测试 |
| AC-5.1 ~ AC-5.4 | R-12, R-13 | TASK-ARC-02 | UT | 颜色方案测试 |
| AC-6.1 ~ AC-6.4 | R-14, R-15 | TASK-ARC-02 | UT + 手工 | 进度条模式测试 |
| AC-7.1 ~ AC-7.3 | R-16 | TASK-ARC-02 | UT | 阴影和模糊测试 |
| AC-8.1 ~ AC-8.3 | R-17 | TASK-ARC-02 | UT | 响应式更新测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `arcbutton.ets:217-248` ArcButtonOptions 构造 | position 默认 BOTTOM_EDGE, styleMode 默认 EMPHASIZED_LIGHT, status 默认 NORMAL, label 默认 '', backgroundBlurStyle 默认 NONE | — | AC-1.1 |
| R-2 | 行为 | `arcbutton.ets:379` isUp 计算 | position=TOP_EDGE → isUp=true, rotate 180°；BOTTOM_EDGE → isUp=false, rotate 0° | — | AC-1.2 |
| R-3 | 边界 | `arcbutton.ets:581-583` DISABLED 状态 | status=DISABLED → enabled=false, EMPHASIZED_LIGHT 模式 opacity=0.4, 其他模式 opacity=1 | DEFAULT_TRANSPARENCY=0.4 | AC-1.3 |
| R-4 | 行为 | `arcbutton.ets:630-649` DataProcessUtil.initData | 初始化 dial 圆（半径=DIAL_CIRCLE_DIAMETER/2）和 arc 圆（圆心在 dial 下方） | — | AC-2.1 |
| R-5 | 行为 | `arcbutton.ets:652-667` DataProcessUtil.calculate | 计算 innerDial/innerArc（减去倒角半径），findCircleIntersections 得到交点，calculateIntersection 得到四角点 | — | AC-2.1 |
| R-6 | 行为 | `arcbutton.ets:439-479` generatePath | SVG Path: M(起点) → A(上弧, ARC_CIRCLE_DIAMETER 半径) → Q(右倒角) → A(下弧, DIAL_CIRCLE_DIAMETER 半径) → Q(左倒角) | — | AC-2.2 |
| R-7 | 行为 | `arcbutton.ets:610-615` TouchType.Down | scaleX/scaleY=scaleValue(1), btnColor=btnPressColor, fontColor=textPressColor | — | AC-3.1 |
| R-8 | 行为 | `arcbutton.ets:617-621` TouchType.Up | scaleX/scaleY=1, btnColor=btnNormalColor, fontColor=textNormalColor | — | AC-3.2 |
| R-9 | 行为 | `arcbutton.ets:274, 584` InterpolatingSpring | 按压动画使用 Curves.interpolatingSpring(10, 1, 350, 35) 弹簧曲线 | mass=10, stiffness=1, damping=350, velocity=35 | AC-3.3 |
| R-10 | 行为 | `arcbutton.ets:410-420` judgeTextWidth | 使用 measure.measureText 以 13fp 测量文字宽度，超过 textWidth 则 isExceed=true | MIN_FONT_SIZE=13 | AC-4.1 |
| R-11 | 边界 | `arcbutton.ets:482-523` 文字自适应 | isExceed=false → maxFontSize(19fp)/minFontSize(13fp) 自适应；isExceed=true → 固定 13fp + MARQUEE | MAX=19fp, MIN=13fp | AC-4.2, AC-4.3 |
| R-12 | 行为 | `arcbutton.ets:313-362` changeStatus | 5 种 styleMode 各有 normal/press/disable 颜色；btnPressColor = normalColor.blendColor(#1AFFFFFF) | PRESS_MERGE_COLOR=#1AFFFFFF | AC-5.1 ~ AC-5.3 |
| R-13 | 边界 | `arcbutton.ets:363-372` status 颜色切换 | DISABLED → btnDisable/textDisable；PRESSED → btnPress/textPress；NORMAL → btnNormal/textNormal | — | AC-5.4 |
| R-14 | 行为 | `arcbutton.ets:553-563` 进度条模式 | progressConfig 设置时渲染 Progress(Capsule) 替代 Button，clipShape(Path) 裁剪 | — | AC-6.1, AC-6.4 |
| R-15 | 边界 | `arcbutton.ets:295-311` progressOptionsChange | progressConfig.color 未设置 → 使用 backgroundColor 或默认 #1F71FF；total 未设置 → 默认 100 | EMPHASIZED_DISABLE_BTN_COLOR=#1F71FF | AC-6.2, AC-6.3 |
| R-16 | 行为 | `arcbutton.ets:540-549` getShadow | shadowEnabled=true → {radius=4, color=shadowColor, offsetY=3}；shadowEnabled=false → undefined | SHADOW_BLUR=4, SHADOW_OFFSET_Y=3 | AC-7.1 ~ AC-7.2 |
| R-17 | 行为 | `arcbutton.ets:285-293` @Monitor optionsChange | 监听 label/type/fontSize/styleMode/status/backgroundColor/fontColor/progressConfig.* 变化，触发 fontSize 更新 + judgeTextWidth + changeStatus + progressOptionsChange | — | AC-8.1 ~ AC-8.3 |
| R-18 | 异常 | `arcbutton.ets:423-425` aboutToAppear | arcButtonTheme 值为 0（sys.float 获取失败）→ console.error 输出，直接 return | — | AC-2.3 |
| R-19 | 行为 | `arcbutton.ets:231-236` fontMargin 默认值 | 默认 {start:24vp, top:10vp, end:24vp, bottom:16vp} | TEXT_HORIZONTAL_MARGIN=24, TEXT_MARGIN_TOP=10, TEXT_MARGIN_BOTTOM=16 | AC-1.4 |
| R-20 | 行为 | `arcbutton.ets:587` scale centerY | BOTTOM_EDGE → centerY=canvasHeight（底部缩放）；TOP_EDGE → centerY=0（顶部缩放） | — | AC-3.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT | 基础创建和配置 |
| VM-2 | AC-2.1 ~ AC-2.3 | UT | SVG 路径计算 |
| VM-3 | AC-3.1 ~ AC-3.4 | UT + 手工 | 按压动画和颜色切换 |
| VM-4 | AC-4.1 ~ AC-4.4 | UT + 手工 | 文字自适应和 MARQUEE |
| VM-5 | AC-5.1 ~ AC-5.4 | UT | 颜色方案和状态 |
| VM-6 | AC-6.1 ~ AC-6.4 | UT + 手工 | 进度条模式 |
| VM-7 | AC-7.1 ~ AC-7.3 | UT | 阴影和背景模糊 |
| VM-8 | AC-8.1 ~ AC-8.3 | UT | 响应式更新 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC | @since |
|----------|------|----------|---------|--------|
| @ComponentV2 struct ArcButton | Public | ArcButton 组件入口 | 全部 | 18 |
| ArcButtonPosition enum | Public | 位置枚举 (TOP_EDGE=0, BOTTOM_EDGE=1) | AC-1.2 | 18 |
| ArcButtonStyleMode enum | Public | 样式模式 (5 个值) | AC-5.1 ~ AC-5.3 | 18 |
| ArcButtonStatus enum | Public | 状态枚举 (NORMAL/PRESSED/DISABLED) | AC-1.3, AC-3.4 | 18 |
| ArcButtonProgressConfig (@ObservedV2) | Public | 进度配置 (value/total?/color?) | AC-6.1 ~ AC-6.4 | 18 |
| ArcButtonOptions (@ObservedV2) | Public | 主选项 | 全部 | 18 |
| ArcButton Static API | Public | 静态前端 ArcButton | 全部 | 23 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| 无 | — | — |

> 截至当前版本，ArcButton 未发现任何 @deprecated 或 @useinstead 标注的 API。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否
  - ArcButton Dynamic API @since 18, Static API @since 23
  - 无破坏性变更
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 18
- **API 版本号策略:** Dynamic @since 18, Static @since 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 穿戴设备专用 | SysCap = SystemCapability.ArkUI.ArkUI.Circle，面向圆形屏幕 | 全部 |
| 无独立 Pattern | ArcButton 基于 Stack + Button/Progress + Text + Path 组合，不涉及 components_ng/pattern/ | 全部 |
| State V2 组件 | @ComponentV2 + @ObservedV2/@Trace + @Require @Param + @Local + @Monitor | 全部 |
| 无 C API | 高级组件无 NDK 接口 | — |
| 无静态前端聚合 | advanced_ui_component_static/ 中不存在 ArcButton 聚合源码 | — |
| sys.float 资源依赖 | arcButtonTheme 从 sys.float 资源获取尺寸值，获取失败时组件不初始化 | AC-2.3 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 按压弹簧动画帧率 ≥ 60fps | 手工 + Trace | InterpolatingSpring 动画 |
| 内存 | @Monitor 监听 10 个路径，响应式更新开销可控 | UT | optionsChange 性能测试 |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | sys.float 资源获取失败时安全降级 | UT | aboutToAppear 错误处理 |
| 问题定位 | console.error 覆盖 sys.float 获取失败路径 | 代码审查 | `arcbutton.ets:424` |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 不适用 | SysCap 为 ArkUI.Circle，仅穿戴设备 | — | — |
| 平板 | 不适用 | 同上 | — | — |
| 穿戴设备 | 专为圆形屏幕设计 | 表盘圆和弧形圆基于 sys.float 主题值 | 手工 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | ArcButton 无专门无障碍支持 | — |
| 大字体 | 是 | 文字自适应 13-19fp，超过容器时使用 MARQUEE | AC-4.1 ~ AC-4.3 |
| 深色模式 | 是 | 颜色通过 sys.color/sys.float 资源获取，部分使用固定颜色值 | AC-5.1 ~ AC-5.3 |
| 多窗口/分屏 | 否 | 穿戴设备无多窗口 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | Dynamic @since 18, Static @since 23 | 全部 |
| 生态兼容 | 否 | 无 C API | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: ArcButton 圆弧按钮
  作为穿戴设备用户
  我想要使用弧形按钮进行交互
  以便在圆形屏幕上获得自然的操作体验

  Scenario: 基础创建
    Given 应用创建 ArcButton({ options: new ArcButtonOptions({}) })
    When ArcButton 渲染
    Then 使用 BOTTOM_EDGE 位置
    And 使用 EMPHASIZED_LIGHT 样式
    And 使用 NORMAL 状态

  Scenario: TOP_EDGE 旋转
    Given ArcButton 设置 position=TOP_EDGE
    When 组件渲染
    Then rotate 180°
    And 文字 margin top/bottom 交换

  Scenario: 按压动画
    Given ArcButton 已渲染
    When 用户触摸按下
    Then scale 设为 scaleValue(1)
    And btnColor 切换为 btnPressColor
    And 使用 InterpolatingSpring(10, 1, 350, 35) 弹簧动画

  Scenario: 触摸抬起
    Given ArcButton 处于按压状态
    When 用户触摸抬起
    Then scale 恢复为 1
    And btnColor 恢复为 btnNormalColor

  Scenario: 文字自适应（正常）
    Given ArcButton label = "OK"
    When judgeTextWidth 测量 13fp 文字宽度 ≤ 容器宽度
    Then 使用 TextBuilderNormal
    And maxFontSize(19fp)/minFontSize(13fp) 自动缩放

  Scenario: 文字溢出
    Given ArcButton label = "这是一个很长的按钮文字"
    When judgeTextWidth 测量 13fp 文字宽度 > 容器宽度
    Then 使用 TextBuilderIsExceed
    And 固定 13fp + MARQUEE 滚动

  Scenario Outline: 颜色方案
    Given ArcButton styleMode = <style_mode>
    When changeStatus 执行
    Then btnNormalColor = <normal_color>
    And textNormalColor = <text_color>

    Examples:
      | style_mode       | normal_color              | text_color |
      | EMPHASIZED_LIGHT | comp_background_emphasize  | #FFFFFF    |
      | EMPHASIZED_DARK  | #BF2629                   | #FFFFFF    |
      | NORMAL_LIGHT     | #17273F                   | #5EA1FF    |
      | NORMAL_DARK      | #252525                   | #5EA1FF    |

  Scenario: 进度条模式
    Given ArcButton 设置 progressConfig = { value: 30, total: 100 }
    When 组件渲染
    Then 渲染 Progress(Capsule) 替代 Button
    And clipShape(Path) 裁剪为弧形
    And progressValue = 30

  Scenario: 阴影效果
    Given ArcButton shadowEnabled = true
    When getShadow 执行
    Then 返回 { radius: 4, color: shadowColor, offsetY: 3 }

  Scenario: sys.float 资源获取失败
    Given arcButtonTheme.BUTTON_HEIGHT = 0
    When aboutToAppear 执行
    Then console.error 输出错误
    And 组件不初始化
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
  - repo: "openharmony/ace_engine"
    query: "ArcButton DataProcessUtil 两圆相交 SVG 路径计算实现"
  - repo: "openharmony/ace_engine"
    query: "ArcButton changeStatus 颜色方案和 styleMode 映射"
  - repo: "openharmony/ace_engine"
    query: "ArcButton 文字自适应 measureText 和 maxFontSize/minFontSize"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@ohos.arkui.advanced.ArcButton.d.ets`
- KB 路由: `docs/kb/components/selector/arc_button.md`
- 源码入口: `advanced_ui_component/arcbutton/source/arcbutton.ets`
