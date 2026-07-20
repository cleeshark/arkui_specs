# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | ArcSlider 圆弧滑动选择器全量规格 |
| 特性编号 | Func-10-01-01-Feat-01 |
| FuncID | 10-01-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 18 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出 ArcSlider 自引入以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ArcSlider 动态组件 (@ComponentV2) | @since 18, Dynamic API |
| ADDED | ArcSliderValueOptions (@ObservedV2, @Trace): progress, min, max | 值选项 |
| ADDED | ArcSliderLayoutOptions (@ObservedV2, @Trace): reverse, position | 布局选项 |
| ADDED | ArcSliderStyleOptions (@ObservedV2, @Trace): trackThickness, activeTrackThickness, trackColor, selectedColor, trackBlur | 样式选项 |
| ADDED | ArcSliderOptions (@ObservedV2, @Trace): valueOptions, layoutOptions, styleOptions, digitalCrownSensitivity, onTouch, onChange, onEnlarge | 主选项 |
| ADDED | ArcSliderPosition enum: LEFT=0, RIGHT=1 | 位置枚举 |
| ADDED | MyFullDrawModifier (DrawModifier 子类) | 自定义弧形绘制 |
| ADDED | Digital Crown 支持: onDigitalCrown, CrownSensitivity | 表冠交互 |
| ADDED | Haptic feedback: vibrator.startVibration (watchhaptic.feedback.crown.strength2) | 触觉反馈 |
| ADDED | Static API (ArcSlider) | @since 23 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/10-product-customization/01-wearable/01-arc-component/design.md`
- **KB 路由**: `docs/kb/components/selector/arc_slider.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.advanced.ArcSlider.d.ets`
  - Static: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.advanced.ArcSlider.static.d.ets`
  - CAPI / NDK: 无

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: ArcSlider 基础创建与值设置

**角色**: 应用开发者
**期望**: 我想要创建圆弧滑动选择器并设置值范围
**价值**: 以便在穿戴式圆形设备上提供滑动选择交互

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 `ArcSlider({ options: new ArcSliderOptions({}) })` THEN 渲染默认配置的圆弧滑动器，progress=0(min), min=0, max=100（`arcslider.ets:118-122, 163-174`） | 正常 |
| AC-1.2 | WHEN 设置 valueOptions `{ progress: 50, min: 0, max: 100 }` THEN 选中区域占弧形轨道的 50%（`arcslider.ets:608-616`） | 正常 |
| AC-1.3 | WHEN 设置 max ≤ min THEN 参数校验重置 max=100, min=0, progress=0（`arcslider.ets:493-498`） | 异常 |
| AC-1.4 | WHEN 设置 progress 超出 [min, max] 范围 THEN clamp 到 [min, max]（`arcslider.ets:499-500`） | 边界 |

### US-2: ArcSlider 样式定制

**角色**: 应用开发者
**期望**: 我想要自定义弧形轨道的颜色、厚度和模糊
**价值**: 以便匹配应用的视觉设计

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 未设置 styleOptions THEN 使用默认值 trackThickness=5, activeTrackThickness=24, trackColor=#33FFFFFF, selectedColor=#FF5EA1FF, trackBlur=20（`arcslider.ets:36-51, 145-150`） | 正常 |
| AC-2.2 | WHEN 设置 trackThickness 为 3(< 5) THEN 回退到默认值 5（`arcslider.ets:503-504`） | 异常 |
| AC-2.3 | WHEN 设置 trackThickness 为 20(> 16) THEN 回退到默认值 5（`arcslider.ets:504`） | 异常 |
| AC-2.4 | WHEN 设置 activeTrackThickness 为 20(< 24) THEN 回退到默认值 24（`arcslider.ets:505-506`） | 异常 |
| AC-2.5 | WHEN 设置 trackBlur 为负数 THEN 回退到默认值 20（`arcslider.ets:501-502`） | 异常 |

### US-3: ArcSlider 触摸交互与动画

**角色**: 终端用户
**期望**: 我想要通过触摸弧形区域来滑动调整值
**价值**: 以便在圆形表盘上自然地调节参数

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 触摸点在热区内（normalRadius - activeTrackThickness < radius < normalRadius 且角度在轨道范围内）THEN isHotRegion 返回 true，触发 startTouchAnimator（200ms friction 动画放大轨道）（`arcslider.ets:917-944, 967-972`） | 正常 |
| AC-3.2 | WHEN 触摸点不在热区内 THEN isHotRegion 返回 false，不触发触摸动画 | 正常 |
| AC-3.3 | WHEN 触摸抬起后 3000ms 无操作 THEN 触发 startRestoreAnimator（167ms friction 动画缩回轨道）（`arcslider.ets:978-985`） | 边界 |
| AC-3.4 | WHEN 触摸放大动画完成（isTouchAnimatorFinished=true）后移动 THEN 调用 calcValue 计算新值，触发 onChange 回调（`arcslider.ets:966, 987-992`） | 正常 |

### US-4: ArcSlider 拖拽值计算

**角色**: 终端用户
**期望**: 我想要通过垂直拖拽改变弧形滑动器的值
**价值**: 以便精确调节滑动选择器的值

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 垂直拖拽（reverse=true）THEN delta = touchY - moveY，valueNow += delta / (radius × sqrt(3))（`arcslider.ets:719-727`） | 正常 |
| AC-4.2 | WHEN 垂直拖拽（reverse=false）THEN valueNow -= delta / (radius × sqrt(3))（`arcslider.ets:726-727`） | 正常 |
| AC-4.3 | WHEN 拖拽导致 valueNow > 1 THEN clamp 到 1（progress = max）；valueNow < 0 THEN clamp 到 0（progress = min）（`arcslider.ets:728-731`） | 边界 |

### US-5: ArcSlider 数字表冠交互

**角色**: 终端用户
**期望**: 我想要通过旋转数字表冠来调整弧形滑动器的值
**价值**: 以便在不遮挡屏幕的情况下精确调节

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN CrownAction.BEGIN 且未放大 THEN clearTimeout + isEnlarged=true + startTouchAnimator（`arcslider.ets:1098-1102`） | 正常 |
| AC-5.2 | WHEN CrownAction.UPDATE 且已放大 THEN crownDeltaAngle = px2vp(-degree × ratio) / radius，调用 calcCrownValue（`arcslider.ets:1103-1108`） | 正常 |
| AC-5.3 | WHEN digitalCrownSensitivity 为 LOW THEN ratio = CROWN_CONTROL_RATIO × 0.5 = 2.10 × 0.5 = 1.05（`arcslider.ets:947-948`） | 边界 |
| AC-5.4 | WHEN digitalCrownSensitivity 为 HIGH THEN ratio = CROWN_CONTROL_RATIO × 2 = 2.10 × 2 = 4.20（`arcslider.ets:951-952`） | 边界 |
| AC-5.5 | WHEN 表冠旋转触发振动且距上次振动 ≥ 30ms 且非 max/min THEN vibrator.startVibration(watchhaptic.feedback.crown.strength2)（`arcslider.ets:1122-1135`） | 正常 |

### US-6: ArcSlider 点击值跳转

**角色**: 终端用户
**期望**: 我想要通过点击弧形上的位置直接跳转到对应值
**价值**: 以便快速设置目标值

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 已放大状态下再次触摸按下（TouchType.Down）且动画完成 THEN 调用 calcClickValue 计算点击位置对应值（`arcslider.ets:1010-1011`） | 正常 |
| AC-6.2 | WHEN calcClickValue 计算时 clickY 超出 radius 范围 THEN clamp clickY 到 [normalRadius - radius, normalRadius + radius]（`arcslider.ets:685-689`） | 边界 |
| AC-6.3 | WHEN calcClickValue 角度计算完成 THEN selectRatioNow clamp 到 [0, 1]，映射回 [min, max]（`arcslider.ets:708-712`） | 边界 |

### US-7: ArcSlider 布局方向

**角色**: 应用开发者
**期望**: 我想要设置弧形滑动器在左侧或右侧，以及拖拽方向
**价值**: 以便适配不同 UI 布局需求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 设置 position=RIGHT, reverse=true THEN isAntiClock=true，使用右侧逆时针角度布局（`arcslider.ets:571-576`） | 正常 |
| AC-7.2 | WHEN 设置 position=LEFT, reverse=true THEN isAntiClock=false，使用左侧顺时针角度布局（`arcslider.ets:583-588`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2, R-3 | TASK-ARC-01 | UT | `advanced_ui_component/arcslider/source/arcslider.ets` |
| AC-2.1 ~ AC-2.5 | R-4, R-5 | TASK-ARC-01 | UT | 样式参数测试 |
| AC-3.1 ~ AC-3.4 | R-6, R-7, R-8 | TASK-ARC-01 | UT + 手工 | 热区和动画测试 |
| AC-4.1 ~ AC-4.3 | R-9 | TASK-ARC-01 | UT + 手工 | 拖拽值计算测试 |
| AC-5.1 ~ AC-5.5 | R-10, R-11, R-12 | TASK-ARC-01 | 手工 | 数字表冠测试 |
| AC-6.1 ~ AC-6.3 | R-13 | TASK-ARC-01 | UT + 手工 | 点击跳转测试 |
| AC-7.1 ~ AC-7.2 | R-14 | TASK-ARC-01 | UT | 布局方向测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `arcslider.ets:113-123` ArcSliderValueOptions | progress 默认 0(=min), min 默认 0, max 默认 100 | — | AC-1.1 |
| R-2 | 异常 | `arcslider.ets:493-498` checkParam | max ≤ min 或 max < min 时重置 max=100, min=0, progress=0 | — | AC-1.3 |
| R-3 | 边界 | `arcslider.ets:499-500` checkParam | progress clamp 到 [min, max]：Math.min(max, progress) + Math.max(min, progress) | — | AC-1.4 |
| R-4 | 行为 | `arcslider.ets:36-51` 默认样式值 | trackThickness=5, activeTrackThickness=24, trackColor=#33FFFFFF, selectedColor=#FF5EA1FF, trackBlur=20 | — | AC-2.1 |
| R-5 | 异常 | `arcslider.ets:501-506` setLimitValues | trackThickness < 5 或 > 16 → 回退 5；activeTrackThickness < 24 或 > 36 → 回退 24；trackBlur < 0 → 回退 20 | 范围: [5,16], [24,36], ≥0 | AC-2.2 ~ AC-2.5 |
| R-6 | 行为 | `arcslider.ets:917-944` isHotRegion | 触摸点到圆心距离 radius 需满足 normalRadius - activeTrackThickness < radius < normalRadius（圆环区域），且角度在轨道范围内 | — | AC-3.1, AC-3.2 |
| R-7 | 行为 | `arcslider.ets:357-378` setTouchAnimator | 触摸放大动画 200ms friction，begin=0, end=1，lineWidth: trackThickness→activeTrackThickness，角度: normal→active | duration=200ms | AC-3.1 |
| R-8 | 恢复 | `arcslider.ets:446-474, 978-985` setRestoreAnimator | 触摸抬起后 3000ms 超时触发恢复动画 167ms friction，lineWidth: active→track，角度: active→normal | RESTORE_TIMEOUT=3000ms, duration=167ms | AC-3.3 |
| R-9 | 行为 | `arcslider.ets:718-736` calcValue | delta = touchY - moveY，total = radius × sqrt(3)，reverse: valueNow += delta/total, !reverse: -=，clamp [0,1] | — | AC-4.1 ~ AC-4.3 |
| R-10 | 行为 | `arcslider.ets:1094-1120` onDigitalCrownEvent | BEGIN: startTouchAnimator; UPDATE: calcCrownValue; END: 3000ms 超时 startRestoreAnimator | — | AC-5.1, AC-5.2 |
| R-11 | 边界 | `arcslider.ets:946-955` calcDisplayControlRatio | LOW=2.10×0.5=1.05, MEDIUM=2.10×1=2.10, HIGH=2.10×2=4.20 | CROWN_CONTROL_RATIO=2.10 | AC-5.3, AC-5.4 |
| R-12 | 行为 | `arcslider.ets:1122-1135` setVibration | 30ms 节流 + 非 max/min → vibrator.startVibration(watchhaptic.feedback.crown.strength2) | CROWN_TIME_FLAG=30 | AC-5.5 |
| R-13 | 行为 | `arcslider.ets:684-716` calcClickValue | 通过 asin 计算角度，四象限修正，selectRatioNow clamp [0,1]，映射回 [min,max] | — | AC-6.1 ~ AC-6.3 |
| R-14 | 行为 | `arcslider.ets:562-596` setLayoutState | reverse × position 四种组合决定 isAntiClock 和角度值 | RIGHT: ±15°~±45°, LEFT: -165°~-135° | AC-7.1, AC-7.2 |
| R-15 | 恢复 | `arcslider.ets:349-355` aboutToDisappear | clearTimeout + 清理 4 个 animator 引用 | — | AC-3.4 |
| R-16 | 边界 | `arcslider.ets:765-795` calcMaxValue | 达到 max 角度时通过 calcMaxValueDeltaIsPositive/IsNegative 减小角度和线宽，提供边界阻尼效果 | ANGLE_OVER_MIN=10°, LENGTH_OVER_MIN=0.15 | AC-4.3 |
| R-17 | 边界 | `arcslider.ets:842-915` calcMinValue | 达到 min 角度时通过 calcMinValueDeltaIsNegative/IsPositive 减小角度和线宽，提供边界阻尼效果 | 同上 | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT | 值选项创建和参数校验 |
| VM-2 | AC-2.1 ~ AC-2.5 | UT | 样式参数默认值和边界 |
| VM-3 | AC-3.1 ~ AC-3.4 | UT + 手工 | 热区判定、触摸动画、恢复超时 |
| VM-4 | AC-4.1 ~ AC-4.3 | UT + 手工 | 拖拽值计算和 clamp |
| VM-5 | AC-5.1 ~ AC-5.5 | 手工 | 数字表冠灵敏度和振动反馈 |
| VM-6 | AC-6.1 ~ AC-6.3 | UT + 手工 | 点击跳转值计算 |
| VM-7 | AC-7.1 ~ AC-7.2 | UT | 布局方向四组合 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC | @since |
|----------|------|----------|---------|--------|
| @ComponentV2 struct ArcSlider | Public | ArcSlider 组件入口 | 全部 | 18 |
| ArcSliderValueOptions (@ObservedV2) | Public | 值选项 (progress/min/max) | AC-1.1 ~ AC-1.4 | 18 |
| ArcSliderLayoutOptions (@ObservedV2) | Public | 布局选项 (reverse/position) | AC-7.1 ~ AC-7.2 | 18 |
| ArcSliderStyleOptions (@ObservedV2) | Public | 样式选项 (trackThickness/activeTrackThickness/trackColor/selectedColor/trackBlur) | AC-2.1 ~ AC-2.5 | 18 |
| ArcSliderOptions (@ObservedV2) | Public | 主选项 (valueOptions/layoutOptions/styleOptions/digitalCrownSensitivity/onTouch/onChange/onEnlarge) | 全部 | 18 |
| ArcSliderPosition enum | Public | 位置枚举 (LEFT=0, RIGHT=1) | AC-7.1 ~ AC-7.2 | 18 |
| ArcSlider Static API | Public | 静态前端 ArcSlider | 全部 | 23 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| 无 | — | — |

> 截至当前版本，ArcSlider 未发现任何 @deprecated 或 @useinstead 标注的 API。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否
  - ArcSlider Dynamic API @since 18, Static API @since 23
  - 无破坏性变更
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 18
- **API 版本号策略:** Dynamic @since 18, Static @since 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 穿戴设备专用 | SysCap = SystemCapability.ArkUI.ArkUI.Circle，面向圆形屏幕 | 全部 |
| 无独立 Pattern | ArcSlider 基于 Stack + Circle + Button + DrawModifier + PathShape 组合，不涉及 components_ng/pattern/ | 全部 |
| State V2 组件 | @ComponentV2 + @ObservedV2/@Trace + @Param/@Local + @Monitor | 全部 |
| 无 C API | 高级组件无 NDK 接口 | — |
| 无静态前端聚合 | advanced_ui_component_static/ 中不存在 ArcSlider 聚合源码 | — |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 触摸放大动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 功耗 | 3000ms 无操作后自动缩回，减少持续渲染 | 代码审查 | RESTORE_TIMEOUT=3000 |
| 内存 | aboutToDisappear 清理 4 个 animator 引用 | UT | 组件单测 |
| 安全 | vibrator 需声明权限，通过 isSupportEffectSync 检查 | 代码审查 | `arcslider.ets:1138` |
| 可靠性 | display API 异常时回退默认直径 233vp | UT | DIAMETER_DEFAULT=233 |
| 问题定位 | hilog 标签 0x3900 覆盖振动和绘制异常路径 | 代码审查 | `arcslider.ets:210, 236` |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 不适用 | SysCap 为 ArkUI.Circle，仅穿戴设备 | — | — |
| 平板 | 不适用 | 同上 | — | — |
| 穿戴设备 | 专为圆形屏幕设计 | 使用 display.width 作为表盘直径 | 手工 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | ArcSlider 无专门无障碍支持 | — |
| 大字体 | 否 | ArcSlider 不涉及文字渲染 | — |
| 深色模式 | 否 | 使用固定颜色默认值，不跟随主题 | — |
| 多窗口/分屏 | 否 | 穿戴设备无多窗口 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | Dynamic @since 18, Static @since 23 | 全部 |
| 生态兼容 | 否 | 无 C API | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: ArcSlider 圆弧滑动选择器
  作为穿戴设备用户
  我想要通过触摸和表冠调节圆弧滑动器
  以便在圆形屏幕上精确选择值

  Scenario: 触摸热区判定
    Given ArcSlider 已渲染，position=RIGHT, reverse=true
    When 触摸点距离圆心在 (normalRadius - activeTrackThickness, normalRadius) 之间
    And 触摸角度在轨道范围内
    Then isHotRegion 返回 true
    And 触发 startTouchAnimator (200ms friction)

  Scenario: 触摸非热区
    Given ArcSlider 已渲染
    When 触摸点距离圆心 < normalRadius - activeTrackThickness
    Then isHotRegion 返回 false
    And 不触发触摸动画

  Scenario: 拖拽值计算
    Given ArcSlider 已放大且动画完成
    When 用户垂直拖拽，delta = touchY - moveY
    Then valueNow += delta / (radius × sqrt(3))
    And progress 映射回 [min, max] 范围
    And onChange 回调触发

  Scenario: 恢复超时
    Given ArcSlider 已放大，用户抬起触摸
    When 3000ms 内无操作
    Then 触发 startRestoreAnimator (167ms friction)
    And onEnlarge 回调返回 false

  Scenario Outline: 数字表冠灵敏度
    Given ArcSlider 设置 digitalCrownSensitivity = <sensitivity>
    When 表冠旋转
    Then 控制比率为 CROWN_CONTROL_RATIO × <multiplier> = <expected_ratio>

    Examples:
      | sensitivity | multiplier | expected_ratio |
      | LOW         | 0.5        | 1.05           |
      | MEDIUM      | 1          | 2.10           |
      | HIGH        | 2          | 4.20           |

  Scenario: 振动反馈
    Given ArcSlider 表冠旋转且距上次振动 ≥ 30ms
    And progress 不等于 max 或 min
    Then vibrator.startVibration 触发 watchhaptic.feedback.crown.strength2

  Scenario: 参数校验异常
    Given ArcSlider 设置 max=50, min=50
    When checkParam 执行
    Then max 重置为 100, min 重置为 0, progress 重置为 0
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
    query: "ArcSlider MyFullDrawModifier 自定义弧形绘制实现"
  - repo: "openharmony/ace_engine"
    query: "ArcSlider 触摸交互热区判定和值计算算法"
  - repo: "openharmony/ace_engine"
    query: "ArcSlider 数字表冠 CrownSensitivity 灵敏度和振动反馈"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@ohos.arkui.advanced.ArcSlider.d.ets`
- KB 路由: `docs/kb/components/selector/arc_slider.md`
- 源码入口: `advanced_ui_component/arcslider/source/arcslider.ets`
