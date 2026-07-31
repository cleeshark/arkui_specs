# 特性规格

> Func-05-09-01-Feat-01 创建与滚动参数：固化 MarqueeOptions 的 start/step/loop/fromStart/src/spacing/delay 七个构造参数以及滚动激活运行时逻辑（内容宽度+水平 padding≥组件宽度才启动、step>textWidth 回退默认 6vp、loop≤0 无限循环、卡片场景强制 loop=1 仅滚一次）的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 创建与滚动参数 (Creation & Scroll Parameters) |
| 特性编号 | Func-05-09-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 8 起支持（动态版），API 18 匿名对象 rectification，API 23 新增 spacing/delay，API 26 行为变化 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | start/step/loop/fromStart/src 五个构造参数行为规格 | API 8 起支持 |
| ADDED | spacing 轮间距参数行为规格 | API 23 起支持 |
| ADDED | delay 轮间延迟参数行为规格 | API 23 起支持 |
| ADDED | 滚动激活谓词 textWidth+padding>=marqueeWidth | 运行时逻辑 |
| ADDED | step>textWidth 回退默认 6vp 与时长公式 | 运行时逻辑 |
| ADDED | loop≤0 无限循环与卡片场景强制 1 | 运行时逻辑 |
| ADDED | start 不可重启已完成滚动 | 已知行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/01-marquee/design.md` | Baselined |

---

## 用户故事

### US-1: 创建 Marquee 组件并设置 src

**作为** 应用开发者,
**我想要** 通过 `Marquee({ start, src, ... })` 创建跑马灯并指定滚动文本,
**以便** 显示单行滚动文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `Marquee({ start: true, src: "文本" })` 且文本宽度+水平padding≥组件宽度 THEN 创建一个 Marquee 节点并启动滚动 | 正常 |
| AC-1.2 | WHEN src 为空字符串或未设置 THEN 使用空字符串作为内容（`marquee_pattern.cpp:847` GetSrc().value_or(" ")），不启动滚动 | 边界 |
| AC-1.3 | WHEN src 含换行符 `\n` THEN 换行符被替换为空格（`marquee_pattern.cpp:848`），按单行渲染 | 正常 |
| AC-1.4 | WHEN 文本宽度+水平padding < 组件宽度 THEN 不启动滚动，文本按对齐方式静态显示（`marquee_pattern.cpp:181-185`） | 边界 |
| AC-1.5 | WHEN 通过 ArkTS 动态版 `Marquee(options: MarqueeOptions)` THEN 桥接调用 `setInitialize(node, start, step, loop, fromStart, src, spacing, delay)`（`arkts_native_marquee_bridge.cpp:641-682`） | 正常 |

### US-2: start 控制滚动启停

**作为** 应用开发者,
**我想要** 通过 `start` 布尔值控制跑马灯的播放与暂停,
**以便** 程序化控制滚动状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN start=true 且 IsRunMarquee() 为真 THEN 触发 onStart 并开始滚动（`marquee_pattern.cpp:194-195`） | 正常 |
| AC-2.2 | WHEN start=false 且动画运行中 THEN 暂停动画（PauseAnimation，`marquee_pattern.cpp:588`），不触发 onFinish | 正常 |
| AC-2.3 | WHEN start 从 false 切 true 且无其他参数变更（OnlyPlayStatusChange）THEN 调用 ResumeAnimation 原地续播（`marquee_pattern.cpp:580-586`） | 正常 |
| AC-2.4 | WHEN 有限 loop（如 loop=1）动画自然完成后将 start 从 false 切 true THEN 仅 ResumeAnimation 不从头重放（animation_ 未 reset，`marquee_pattern.cpp:268-288`） | 边界 |
| AC-2.5 | WHEN 需重启已完成的滚动 THEN 必须触发 measure 或 step/loop/direction/delay 参数变更走 StopMarqueeAnimation(true) 从头播放（`marquee_pattern.cpp:166-172`） | 恢复 |
| AC-2.6 | WHEN 未显式设置 start THEN 运行时按 value_or(false) 处理（`marquee_pattern.cpp:114,598`），即不自动启动滚动 | 边界 |
| AC-2.7 | WHEN inspector/序列化读取未设置的 start THEN 显示 value_or(true)（`marquee_paint_property.h:65`），与运行时默认 false 不一致 | 异常 |

### US-3: step 步长

**作为** 应用开发者,
**我想要** 通过 `step` 设置每次滚动的步长（vp）,
**以便** 控制滚动速度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN step 为正数（vp）THEN 桥接转换为 px 存储到 ScrollAmount，按 step 计算时长（`arkts_native_marquee_bridge.cpp:39-51`） | 正常 |
| AC-3.2 | WHEN step 大于文本宽度 THEN step 回退默认 6vp（px）（`marquee_pattern.cpp:219-222`） | 边界 |
| AC-3.3 | WHEN 滚动时长计算 THEN duration = |calculateEnd - calculateStart| * 85 / step（ms），曲线 LINEAR（`marquee_pattern.cpp:31,243`） | 正常 |
| AC-3.4 | WHEN step 为 0 或负数或非数字 THEN 桥接 reset（`arkts_native_marquee_bridge.cpp:44` GreatNotEqual(step,0.0) 为假），使用默认 6vp | 异常 |
| AC-3.5 | WHEN 未设置 step THEN 使用 DEFAULT_MARQUEE_SCROLL_AMOUNT = 6.0_vp（`marquee_paint_property.h:26`） | 边界 |
| AC-3.6 | WHEN step 更大 THEN duration 更小，滚动更快（duration 与 step 成反比） | 正常 |

### US-4: loop 循环次数

**作为** 应用开发者,
**我想要** 通过 `loop` 设置滚动重复次数,
**以便** 控制循环行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN loop 为正整数 N THEN 滚动 N 轮后触发 onFinish 停止 | 正常 |
| AC-4.2 | WHEN loop ≤ 0（如 0、-1、-5）THEN 桥接钳制为 -1（DEFAULT_MARQUEE_LOOP）表示无限循环（`arkts_native_marquee_bridge.cpp:53-71,120-136`） | 边界 |
| AC-4.3 | WHEN loop 转换后为 INT32_MAX 或负值 THEN 回退 -1 无限循环（`arkts_native_marquee_bridge.cpp:128-130`） | 异常 |
| AC-4.4 | WHEN 未设置 loop THEN 使用默认 -1 无限循环（`marquee_pattern.cpp:33`） | 边界 |
| AC-4.5 | WHEN 处于卡片/服务卡片渲染场景（IsFormRenderExceptDynamicComponent() 为真）THEN repeatCount 强制为 1，仅滚一次（`marquee_pattern.cpp:191-193`） | 正常 |
| AC-4.6 | WHEN loop=1（needSecondPlay=false）THEN 单轮播完后触发 onStop→onFinish 终止（`marquee_pattern.cpp:275-278`） | 正常 |

### US-5: fromStart 起始方向

**作为** 应用开发者,
**我想要** 通过 `fromStart` 控制文本从头部还是尾部开始滚动,
**以便** 控制滚动进入方向。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN fromStart=true THEN 映射为 MarqueeDirection::LEFT，文本从右边缘进入向左滚动（`arkts_native_marquee_bridge.cpp:255-256`，`marquee_pattern.cpp:607-647` CalculateStart） | 正常 |
| AC-5.2 | WHEN fromStart=false THEN 映射为 MarqueeDirection::RIGHT，文本从左边缘进入向右滚动 | 正常 |
| AC-5.3 | WHEN 未设置 fromStart THEN 桥接默认 true（→LEFT，`arkts_native_marquee_bridge.cpp:144-146`），运行时 value_or(LEFT)（`marquee_pattern.cpp:546`） | 边界 |
| AC-5.4 | WHEN 文本方向为 RTL（如阿拉伯语）THEN directionMoveLeft = (direction==LEFT) ^ (textDir==RTL)，视觉滚动方向反转（`marquee_pattern.cpp:918-919`） | 正常 |
| AC-5.5 | WHEN inspector 读取未设置的 fromStart THEN 显示 value_or(RIGHT) 即 false（`marquee_paint_property.h:66-67`），与运行时默认 LEFT 不一致 | 异常 |

### US-6: spacing 轮间距

**作为** 应用开发者,
**我想要** 通过 `spacing` 设置两轮跑马灯之间的间距,
**以便** 实现无缝连续滚动。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 设置 spacing（LengthMetrics）THEN 启用第二文本子节点，走 PlayMarqueeDoubleAnimation 无缝双滚动（`marquee_pattern.cpp:923-930,198-203`） | 正常 |
| AC-6.2 | WHEN 未设置 spacing THEN 默认值等于组件宽度（`marquee_pattern.cpp:889-903` GetMarqueeSpacing） | 边界 |
| AC-6.3 | WHEN spacing 为负数或 PERCENT 单位 THEN reset 不生效（`marquee_pattern.cpp:1281-1287`，`marquee_dynamic_modifier.cpp:364-367`） | 异常 |
| AC-6.4 | WHEN spacing 生效 THEN textTotalLen = textWidth + max(spacing, 0)，两文本副本按此周期连续平铺（`marquee_pattern.cpp:1087`） | 正常 |
| AC-6.5 | WHEN spacing 是 API 23 新增参数 THEN 旧版本（API 8-22）不支持，需 @since 23 标注 | 边界 |

### US-7: delay 轮间延迟

**作为** 应用开发者,
**我想要** 通过 `delay` 设置每轮滚动之间的等待时间（ms）,
**以便** 在两轮之间插入停顿。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 设置 delay（正数 ms）THEN 启用第二文本子节点，在两轮间插入 no-op 关键帧（`marquee_pattern.cpp:1161`） | 正常 |
| AC-7.2 | WHEN 未设置 delay THEN 默认 0（`marquee_pattern.cpp:547,604`），无停顿 | 边界 |
| AC-7.3 | WHEN delay ≤ 0 THEN 桥接 reset 为 0（`arkts_native_marquee_bridge.cpp:73-83,172-182`） | 异常 |
| AC-7.4 | WHEN delay 生效 THEN totalDuration = firstDuration + delay + secondDuration（`marquee_pattern.cpp:1064-1069`） | 正常 |
| AC-7.5 | WHEN delay 是 API 23 新增参数 THEN 旧版本（API 8-22）不支持，需 @since 23 标注 | 边界 |

### US-8: 滚动激活条件

**作为** 应用开发者,
**我想要** Marquee 仅在文本内容超出组件宽度时才滚动,
**以便** 短文本静态显示、长文本自动滚动。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN textWidth + horizontalPadding ≥ marqueeFrameWidth THEN IsRunMarquee() 返回 true，启动滚动（`marquee_pattern.cpp:792`） | 正常 |
| AC-8.2 | WHEN textWidth + horizontalPadding < marqueeFrameWidth THEN IsRunMarquee() 返回 false，UpdateNodeInitialPos + StopAndResetAnimation，不触发 onStart（`marquee_pattern.cpp:181-185,772-793`） | 边界 |
| AC-8.3 | WHEN 设置水平 padding THEN padding 计入 textWidth 参与 IsRunMarquee 判定（`marquee_pattern.cpp:786-792`） | 正常 |
| AC-8.4 | WHEN Marquee 节点 attach 到帧节点 THEN 注册 OnWindowHide/Show 与 OnVisibleAreaChange 回调，SetClipToFrame(true)（`marquee_pattern.cpp:36-48`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1, R-8 | TASK-01 | UI 测试 | marquee_pattern.cpp:181-185,194-195 |
| AC-1.2 | R-2 | TASK-01 | 单测 | marquee_pattern.cpp:847 |
| AC-1.3 | R-3 | TASK-01 | 单测 | marquee_pattern.cpp:848 |
| AC-1.4 | R-8 | TASK-01 | UI 测试 | marquee_pattern.cpp:181-185 |
| AC-1.5 | R-1 | TASK-01 | 桥接测试 | arkts_native_marquee_bridge.cpp:641-682 |
| AC-2.1 | R-4 | TASK-01 | UI 测试 | marquee_pattern.cpp:194-195 |
| AC-2.2 | R-5 | TASK-01 | UI 测试 | marquee_pattern.cpp:588 |
| AC-2.3 | R-5 | TASK-01 | UI 测试 | marquee_pattern.cpp:580-586 |
| AC-2.4 | R-6 | TASK-01 | UI 测试 | marquee_pattern.cpp:268-288 |
| AC-2.5 | R-7 | TASK-01 | UI 测试 | marquee_pattern.cpp:166-172 |
| AC-2.6 | R-9 | TASK-01 | 单测 | marquee_pattern.cpp:114,598 |
| AC-2.7 | R-10 | TASK-01 | inspector 测试 | marquee_paint_property.h:65 |
| AC-3.1 | R-11 | TASK-01 | 单测 | arkts_native_marquee_bridge.cpp:39-51 |
| AC-3.2 | R-12 | TASK-01 | UI 测试 | marquee_pattern.cpp:219-222 |
| AC-3.3 | R-13 | TASK-01 | UI 测试 | marquee_pattern.cpp:31,243 |
| AC-3.4 | R-14 | TASK-01 | 单测 | arkts_native_marquee_bridge.cpp:44 |
| AC-3.5 | R-15 | TASK-01 | 单测 | marquee_paint_property.h:26 |
| AC-3.6 | R-13 | TASK-01 | UI 测试 | marquee_pattern.cpp:243 |
| AC-4.1 | R-16 | TASK-01 | UI 测试 | marquee_pattern.cpp:280-287 |
| AC-4.2 | R-17 | TASK-01 | 单测 | arkts_native_marquee_bridge.cpp:53-71 |
| AC-4.3 | R-17 | TASK-01 | 单测 | arkts_native_marquee_bridge.cpp:128-130 |
| AC-4.4 | R-18 | TASK-01 | 单测 | marquee_pattern.cpp:33 |
| AC-4.5 | R-19 | TASK-01 | 卡片测试 | marquee_pattern.cpp:191-193 |
| AC-4.6 | R-20 | TASK-01 | UI 测试 | marquee_pattern.cpp:275-278 |
| AC-5.1 | R-21 | TASK-01 | UI 测试 | marquee_pattern.cpp:607-647 |
| AC-5.2 | R-21 | TASK-01 | UI 测试 | marquee_pattern.cpp:607-647 |
| AC-5.3 | R-22 | TASK-01 | 单测 | arkts_native_marquee_bridge.cpp:144-146 |
| AC-5.4 | R-23 | TASK-01 | RTL 测试 | marquee_pattern.cpp:918-919 |
| AC-5.5 | R-10 | TASK-01 | inspector 测试 | marquee_paint_property.h:66-67 |
| AC-6.1 | R-24 | TASK-01 | UI 测试 | marquee_pattern.cpp:923-930,198-203 |
| AC-6.2 | R-25 | TASK-01 | 单测 | marquee_pattern.cpp:889-903 |
| AC-6.3 | R-26 | TASK-01 | 单测 | marquee_pattern.cpp:1281-1287 |
| AC-6.4 | R-27 | TASK-01 | UI 测试 | marquee_pattern.cpp:1087 |
| AC-6.5 | R-28 | TASK-01 | 版本测试 | marquee.d.ts:131 |
| AC-7.1 | R-29 | TASK-01 | UI 测试 | marquee_pattern.cpp:1161 |
| AC-7.2 | R-30 | TASK-01 | 单测 | marquee_pattern.cpp:547,604 |
| AC-7.3 | R-31 | TASK-01 | 单测 | arkts_native_marquee_bridge.cpp:73-83 |
| AC-7.4 | R-32 | TASK-01 | UI 测试 | marquee_pattern.cpp:1064-1069 |
| AC-7.5 | R-33 | TASK-01 | 版本测试 | marquee.d.ts:148 |
| AC-8.1 | R-8 | TASK-01 | UI 测试 | marquee_pattern.cpp:792 |
| AC-8.2 | R-8 | TASK-01 | UI 测试 | marquee_pattern.cpp:181-185 |
| AC-8.3 | R-8 | TASK-01 | UI 测试 | marquee_pattern.cpp:786-792 |
| AC-8.4 | R-34 | TASK-01 | 生命周期测试 | marquee_pattern.cpp:36-48 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 调用 `Marquee({ start, src, step, loop, fromStart, spacing, delay })` | 桥接 setInitialize 设置七参数到 Paint/Layout Property | 七参数顺序固定 | AC-1.1, AC-1.5 |
| R-2 | 边界 | src 为空字符串或未设置 | GetSrc().value_or(" ") 取单空格作为内容 | 不触发滚动 | AC-1.2 |
| R-3 | 行为 | src 含 `\n` 换行符 | 替换为空格后单行渲染 | 仅替换换行符 | AC-1.3 |
| R-4 | 行为 | start=true 且 IsRunMarquee()=true | hasStart_=true，FireStartEvent()，启动动画 | 文本须超出组件宽度 | AC-2.1 |
| R-5 | 行为 | start=false（动画运行中） | PauseAnimation 暂停，不触发 onFinish | 保留 animation_ 不 reset | AC-2.2, AC-2.3 |
| R-6 | 边界 | 有限 loop 自然完成后 start false→true | 仅 ResumeAnimation 原地续播不重放 | animation_ 未 reset | AC-2.4 |
| R-7 | 恢复 | 需重启已完成滚动 | 触发 measure 或 step/loop/direction/delay 变更走 StopMarqueeAnimation(true) | 必须有参数/布局变更 | AC-2.5 |
| R-8 | 行为 | IsRunMarquee() 判定 | textWidth + horizontalPadding ≥ marqueeFrameWidth 返回 true | 含等号、含水平 padding | AC-1.4, AC-8.1, AC-8.2, AC-8.3 |
| R-9 | 边界 | 未显式设置 start | 运行时 value_or(false) 不自动启动 | 与 inspector value_or(true) 不一致 | AC-2.6 |
| R-10 | 异常 | inspector 读取未设置的 start/fromStart | start 显示 true，fromStart 显示 false | 与运行时默认相反 | AC-2.7, AC-5.5 |
| R-11 | 行为 | step 为正数（vp） | 桥接转 px 存 ScrollAmount | step>0 才生效 | AC-3.1 |
| R-12 | 边界 | step 大于文本宽度 | step 回退 DEFAULT_MARQUEE_SCROLL_AMOUNT=6vp(px) | 防止 step 过大 | AC-3.2 |
| R-13 | 行为 | 时长计算 | duration = |end-start| * 85 / step (ms)，LINEAR 曲线 | step 为 px | AC-3.3, AC-3.6 |
| R-14 | 异常 | step ≤ 0 或非数字 | 桥接 reset，使用默认 6vp | GreatNotEqual(step,0.0) 为假 | AC-3.4 |
| R-15 | 边界 | 未设置 step | DEFAULT_MARQUEE_SCROLL_AMOUNT = 6.0_vp | marquee_paint_property.h:26 | AC-3.5 |
| R-16 | 行为 | loop 为正整数 N | 滚动 N 轮后 onFinish | N>0 | AC-4.1 |
| R-17 | 边界 | loop ≤ 0 | 钳制为 -1 无限循环 | 0/-1/-5 均钳制 -1 | AC-4.2, AC-4.3 |
| R-18 | 边界 | 未设置 loop | DEFAULT_MARQUEE_LOOP = -1 无限 | marquee_pattern.cpp:33 | AC-4.4 |
| R-19 | 行为 | 卡片场景 IsFormRenderExceptDynamicComponent()=true | repeatCount 强制 1 仅滚一次 | isFormRender_ && !isDynamicRender_ | AC-4.5 |
| R-20 | 行为 | loop=1 needSecondPlay=false | 单轮播完 onStop→onFinish 终止 | onStop 先于 onFinish | AC-4.6 |
| R-21 | 行为 | fromStart 设置 | true→LEFT 从右进向左滚；false→RIGHT 从左进向右滚 | 桥接映射 | AC-5.1, AC-5.2 |
| R-22 | 边界 | 未设置 fromStart | 桥接默认 true→LEFT | 运行时 value_or(LEFT) | AC-5.3 |
| R-23 | 行为 | 文本方向 RTL | directionMoveLeft = (direction==LEFT) ^ (textDir==RTL)，视觉方向反转 | 自动检测文本方向 | AC-5.4 |
| R-24 | 行为 | 设置 spacing | 启用第二文本子节点走双滚动 | NeedSecondChild()=true | AC-6.1 |
| R-25 | 边界 | 未设置 spacing | 默认值=组件宽度 | GetMarqueeSpacing | AC-6.2 |
| R-26 | 异常 | spacing 负数或 PERCENT | reset 不生效 | UpdatePropertyImpl 校验 | AC-6.3 |
| R-27 | 行为 | spacing 生效 | textTotalLen = textWidth + max(spacing,0) | 两副本连续平铺 | AC-6.4 |
| R-28 | 边界 | spacing @since 23 | API 8-22 不支持 | API 23 新增 | AC-6.5 |
| R-29 | 行为 | 设置 delay | 启用第二子节点，两轮间插 no-op 关键帧 | BuildAnimationKeyframes | AC-7.1 |
| R-30 | 边界 | 未设置 delay | 默认 0 无停顿 | marquee_pattern.cpp:547 | AC-7.2 |
| R-31 | 异常 | delay ≤ 0 | 桥接 reset 为 0 | delay>0 才生效 | AC-7.3 |
| R-32 | 行为 | delay 生效 | totalDuration = firstDuration + delay + secondDuration | CalcDuration | AC-7.4 |
| R-33 | 边界 | delay @since 23 | API 8-22 不支持 | API 23 新增 | AC-7.5 |
| R-34 | 行为 | Marquee attach 到帧节点 | 注册 OnWindowHide/Show + OnVisibleAreaChange，SetClipToFrame(true) | 生命周期回调 | AC-8.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|----------|----------|
| VM-1 | AC-1.1, AC-8.1, AC-8.2 | UI 集成测试 | 文本宽度边界下滚动激活/不激活 |
| VM-2 | AC-1.2, AC-1.3 | 单测 | src 空值与换行符处理 |
| VM-3 | AC-1.5 | 桥接测试 | setInitialize 七参数传递 |
| VM-4 | AC-2.1 ~ AC-2.5 | UI 测试 | start 启停/暂停/续播/重启 |
| VM-5 | AC-2.6, AC-2.7, AC-5.5 | 单测 + inspector 测试 | 默认值不一致问题 |
| VM-6 | AC-3.1 ~ AC-3.6 | 单测 + UI 测试 | step 回退与时长公式 |
| VM-7 | AC-4.1 ~ AC-4.6 | UI 测试 + 卡片测试 | loop 钳制与卡片强制 1 |
| VM-8 | AC-5.1 ~ AC-5.4 | UI 测试 + RTL 测试 | fromStart 与 RTL 反转 |
| VM-9 | AC-6.1 ~ AC-6.5 | UI 测试 + 版本测试 | spacing 双滚动与版本 |
| VM-10 | AC-7.1 ~ AC-7.5 | UI 测试 + 版本测试 | delay 停顿与版本 |
| VM-11 | AC-8.3 | UI 测试 | padding 计入激活判定 |
| VM-12 | AC-8.4 | 生命周期测试 | attach 回调注册 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|----------|----------|---------|
| `Marquee(options: MarqueeOptions)` (动态) | Public | MarqueeOptions{start,step,loop,fromStart,src,spacing,delay} | MarqueeAttribute | 无 | 创建跑马灯 | AC-1.1 |
| `Marquee(options: MarqueeOptions)` (静态) | Public | 同上 | MarqueeAttribute | 无 | 静态版创建 | AC-1.1 |
| `setMarqueeOptions(options)` (静态, @since 26.1) | InnerApi | Ark_MarqueeOptions | this | 无 | 整体设置构造参数 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| MarqueeOptions (API 8 object) | 变更 | API 18 匿名对象 rectification | 字段不变，类型化 | AC-1.1 |
| spacing/delay | 新增 | API 23 新增 | 旧版本不支持 | AC-6.5, AC-7.5 |

> API 签名、d.ts 位置、权限要求等实现细节见 design.md"API 签名、Kit 与权限"。SDK 声明见 `api/@internal/component/ets/marquee.d.ts`（动态）与 `api/arkui/component/marquee.static.d.ets`（静态）。

## 接口规格

### 接口定义

**Marquee (动态版)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Marquee(options: MarqueeOptions): MarqueeAttribute` |
| 返回值 | `MarqueeAttribute` — 属性链 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| start | boolean | 是 | false（运行时） | true 启动；false 暂停；不可重启已完成滚动 |
| step | number | 否 | 6 (vp) | 正数生效；>textWidth 回退默认；≤0 reset |
| loop | number | 否 | -1 (无限) | 正整数 N 滚 N 次；≤0 钳制 -1；卡片强制 1 |
| fromStart | boolean | 否 | true (→LEFT) | true 从右进向左滚；false 从左进向右滚 |
| src | string | 是 | "" (空) | 换行符替换为空格；单行 |
| spacing | LengthMetrics | 否 | 组件宽度 | 负数/PERCENT reset；@since 23 |
| delay | number | 否 | 0 (ms) | ≤0 reset；@since 23 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | start=true 且文本超出组件 | 启动滚动，触发 onStart | AC-1.1, AC-2.1 |
| 2 | start=true 但文本未超出 | 不滚动，静态显示 | AC-1.4, AC-8.2 |
| 3 | start=false | 暂停动画 | AC-2.2 |
| 4 | 有限 loop 完成后 start false→true | 仅续播不重放 | AC-2.4 |
| 5 | step>textWidth | 回退默认 6vp | AC-3.2 |
| 6 | loop≤0 | 无限循环 | AC-4.2 |
| 7 | 卡片场景 | 强制 loop=1 | AC-4.5 |
| 8 | 设置 spacing 或 delay | 启用第二子节点双滚动 | AC-6.1, AC-7.1 |

## 兼容性声明

- **已有 API 行为变更:** 是。`start` 运行时默认 false 与历史 inspector/legacy struct 默认 true 不一致（`marquee_paint_property.h:65` vs `marquee_pattern.cpp:114`）；`fromStart` 运行时默认 LEFT(true) 与 inspector 默认 RIGHT(false) 不一致。规格以运行时行为为准。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8（动态版）；spacing/delay 需 API 23；onStop 需 API 26
- **API 版本号策略:** 全量标注 @since。API 8 起支持 start/step/loop/fromStart/src；API 18 匿名对象 rectification（字段不变）；API 23 新增 spacing/delay；API 26 新增 onStop 行为变化

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 滚动激活谓词 | textWidth+horizontalPadding ≥ marqueeFrameWidth（含等号、含 padding） | AC-1.4, AC-8.1, AC-8.2, AC-8.3 |
| start 不可重启已完成滚动 | animation_ 自然完成后不 reset，需参数/布局变更触发 StopMarqueeAnimation(true) | AC-2.4, AC-2.5 |
| step>textWidth 回退 | 防止 step 过大导致动画异常 | AC-3.2 |
| loop≤0 钳制 -1 | 0 与负值统一为无限 | AC-4.2, AC-4.3 |
| 卡片场景强制 loop=1 | IsFormRenderExceptDynamicComponent() 为真时覆盖用户 loop | AC-4.5 |
| spacing/delay 启用双滚动 | 任一设置即创建第二文本子节点 | AC-6.1, AC-7.1 |
| 属性存储分层 | start/step/loop/fromStart 存 PaintProperty；src/spacing/delay 存 LayoutProperty | 全部 AC |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 滚动容器内 Marquee 数量建议≤4，否则建议用 Text 的 TextOverflow.MARQUEE（SDK 注释 marquee.d.ts:158-160） | 性能测试 | SDK 声明 |
| 可靠性 | 滚动帧率动态场景支持 MarqueeDynamicSyncScene 帧率范围设置 | 帧率测试 | marquee_pattern.h:124-127 |
| 可测试性 | DumpInfo 暴露 play status/loop/step（`marquee_pattern.cpp:730-748,795-807`） | Dump 测试 | 源码 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | loop 按用户值 | — | UI 测试 | — |
| 平板 | 同手机 | — | UI 测试 | — |
| 折叠屏 | 同手机；fold 状态切换触发 measure 重启 | — | UI 测试 | marquee_pattern.cpp:102-119 |
| 穿戴 | 字体默认值不同（fontSize 15fp vs 16fp；fontColor 白色） | 主题差异 | 主题测试 | text_theme.cpp:34, color.json:40 |
| 卡片/服务卡片 | loop 强制 1 仅滚一次 | IsFormRenderExceptDynamicComponent | 卡片测试 | marquee_pattern.cpp:191-193 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 仅暴露文本内容，不暴露滚动状态 | marquee_accessibility_property.cpp:21-30 |
| 大字体 | 是 | allowScale 默认 true，fp 字号随系统字号缩放；缩放变更触发 StopMarqueeAnimation 重启 | marquee_pattern.cpp:1227-1246 |
| 深色模式 | 是 | fontColor 默认 font_primary，深色模式切换走 OnColorConfigurationUpdate 重启 | marquee_pattern.cpp:700-728 |
| 多窗口/分屏 | 是 | OnWindowHide→Pause；OnWindowShow→Resume | marquee_pattern.cpp:86-100 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | spacing/delay 需 API 23；onStop 需 API 26 | SDK 声明 |
| 生态兼容 | 是 | Cangjie FFI 缺 spacing/delay/onStop；无公开 NDK | cj_marquee_ffi.h:26-35 |

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
    query: "Marquee 组件滚动状态机与 animation_ 生命周期，为何自然完成后不 reset 导致 start 不可重启"
  - repo: "openharmony/arkui_ace_engine"
    query: "Marquee IsRunMarquee 谓词为何包含水平 padding 与等号，与 CLAUDE.md 简化版差异"
  - repo: "openharmony/interface_sdk-js"
    query: "MarqueeOptions spacing/delay 的 @since 23 与 MarqueeOptions API 18 匿名对象 rectification"
```

**关键文档：** design.md（`specs/05-ui-components/09-text-components/01-marquee/design.md`）；SDK 声明 `api/@internal/component/ets/marquee.d.ts`、`api/arkui/component/marquee.static.d.ets`
