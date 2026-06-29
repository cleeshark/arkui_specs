# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 事件回调 (onCopy/onWillCopy/onTextSelectionChange/onMarqueeStateChange) |
| 特性编号 | Feat-07 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 11 起支持，API 18/26.0.0 有新增 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | onCopy 事件回调规格 | 复制完成后通知开发者已复制的文本内容 |
| ADDED | onWillCopy 事件回调规格 | 复制前拦截，开发者可取消复制操作 |
| ADDED | onTextSelectionChange 事件回调规格 | 选区变化通知，覆盖 20+ 触发场景 |
| ADDED | onMarqueeStateChange 事件回调规格 | 跑马灯状态机三状态（START/BOUNCE/FINISH）变化通知 |

## 输入文档

| 类型 | 路径 |
|------|------|
| 需求基线 | 已有能力补录（无独立 proposal.md） |
| 设计文档 | `specs/05-ui-components/09-text-components/04-text/design.md` |
| SDK 类型定义（动态版） | `interface/sdk-js/api/@internal/component/ets/text.d.ts` |
| SDK 类型定义（静态版） | `interface/sdk-js/api/arkui/component/text.static.d.ets` |

## 用户故事

### US-1: 复制内容拦截与感知

> 作为开发者，我想要在用户复制文本前拦截复制操作并在复制完成后获取已复制的文本内容，以便实现复制内容审计、脱敏或自定义复制行为。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-1.1 | WHEN 用户通过选择菜单点击"复制"或按 Ctrl+C 触发复制操作 THEN `onWillCopy` 回调先于剪贴板写入被调用，参数 `value` 为选中文本的 `std::u16string` 内容（`text_pattern.cpp:1094`） |
| AC-1.2 | WHEN `onWillCopy` 回调返回 `true` THEN 复制操作继续执行——剪贴板写入、菜单关闭、`onCopy` 回调依次触发 |
| AC-1.3 | WHEN `onWillCopy` 回调返回 `false` THEN 复制操作被取消——不执行剪贴板写入、不触发 `onCopy` 回调，仅关闭选择菜单（`text_pattern.cpp:1097-1099`） |
| AC-1.4 | WHEN 未注册 `onWillCopy` 回调 THEN 默认行为等同返回 `true`（`text_event_hub.h:55` `FireOnWillCopy` 在回调为空时返回 `true`） |
| AC-1.5 | WHEN 复制操作成功完成（剪贴板已写入） THEN `onCopy` 回调被调用，参数 `value` 为已复制的文本内容（`text_pattern.cpp:1113`） |
| AC-1.6 | WHEN 选区有效但 `start == end`（零宽选区）且非 AI 实体选中 THEN 不触发 onWillCopy/onCopy，而是调用 `HandleSelectionChange(-1, -1)` 清除选区（`text_pattern.cpp:1081-1083`） |
| AC-1.7 | WHEN `clipboard_` 为空或 `GetDataDetectorAdapter()` 返回 null THEN HandleOnCopy 立即返回，不触发任何回调（`text_pattern.cpp:1079-1080`） |
| AC-1.8 | WHEN 选中文本为空（`value.empty()`） THEN 跳过 `onWillCopy` 调用但仍尝试执行剪贴板写入流程（`text_pattern.cpp:1090-1101`）；最终 `FireOnCopy` 被 `CHECK_NULL_VOID(!value.empty())` 守卫阻止（`text_pattern.cpp:1110`） |

### US-2: 选区变化监听

> 作为开发者，我想要在文本选区范围发生变化时收到通知，以便实时更新关联的 UI（如字数统计、选区高亮、工具栏状态）。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-2.1 | WHEN 用户长按文本触发初始选区（词边界选中） THEN `onTextSelectionChange` 回调被调用，`selectionStart` 和 `selectionEnd` 为选中范围的起止索引（`text_pattern.cpp:363`） |
| AC-2.2 | WHEN 用户双击文本选中词 THEN `onTextSelectionChange` 回调被调用，参数为词边界索引 |
| AC-2.3 | WHEN 用户鼠标左键按下并拖动 THEN 每次鼠标移动更新选区时触发回调（`text_pattern.cpp:3415`） |
| AC-2.4 | WHEN 用户拖动选择手柄改变选区 THEN 每次手柄位置变化触发回调（`text_pattern.cpp:968,973`） |
| AC-2.5 | WHEN 用户按 Ctrl+A 全选 THEN 回调参数为 `(0, textSize)`（`text_pattern.cpp:3645`） |
| AC-2.6 | WHEN 通过 `selection(startIndex, endIndex)` API 编程式设置选区 THEN 触发回调，参数为钳位后的索引（`text_pattern.cpp:5018`） |
| AC-2.7 | WHEN 通过 `setTextSelection(selectionStart, selectionEnd)` 控制器方法设置选区 THEN 触发回调（`text_pattern.cpp:7220`） |
| AC-2.8 | WHEN 用户按 Shift+方向键扩展选区（SELECTABLE_FOCUSABLE 模式） THEN 每次按键触发回调（`text_pattern.cpp:3763`） |
| AC-2.9 | WHEN 选区被清除（点击空白区域、复制后取消选区等） THEN 回调参数为 `(-1, -1)`（`text_pattern.cpp:314, 1082`） |
| AC-2.10 | WHEN AI 实体被选中 THEN 触发回调，参数为实体的 `(aiSpan.start, aiSpan.end)`（`text_pattern.cpp:2328`） |
| AC-2.11 | WHEN 连续两次设置完全相同的 `(start, end)` 值 THEN 第二次不触发回调（去重机制，`text_pattern.cpp:7033-7035`） |
| AC-2.12 | WHEN 鼠标按住 Shift 键点击扩展选区 THEN 回调参数的 start 保持为上次有效选区起点 `lastValidStart`（`text_pattern.cpp:3272`） |
| AC-2.13 | WHEN 鼠标自动滚动选择（鼠标移出可视区域） THEN 持续触发回调（`text_pattern.cpp:8034`） |
| AC-2.14 | WHEN 拖拽失败需恢复选区 THEN 触发回调，参数为 `(recoverStart_, recoverEnd_)`（`text_pattern.cpp:4068`） |
| AC-2.15 | WHEN AI 实体长按选中 THEN 触发回调，参数为实体范围（`text_pattern.cpp:515`） |
| AC-2.16 | WHEN `textSelectable == UNSELECTABLE` 或 `copyOption == None` THEN `selection()` API 调用被忽略（`text_pattern.cpp:1589` 守卫），不触发回调 |

### US-3: 跑马灯状态监听

> 作为开发者，我想要在跑马灯动画的各个状态变化时收到通知，以便控制关联 UI 或记录跑马灯行为。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-3.1 | WHEN 跑马灯动画启动（首次或从非 bounce 状态启动） THEN `onMarqueeStateChange` 回调被调用，参数为 `MarqueeState.START`（值 0）（`text_content_modifier.cpp:1765`） |
| AC-3.2 | WHEN 跑马灯一轮滚动到达终点（`racePercent == marqueeRaceMaxPercent_`） THEN 回调参数为 `MarqueeState.BOUNCE`（值 1），`marqueeCount_` 递增（`text_content_modifier.cpp:1821-1822`） |
| AC-3.3 | WHEN `AllowTextRace()` 返回 false（循环次数耗尽或 ON_FOCUS 策略下失焦） THEN 回调参数为 `MarqueeState.FINISH`（值 2）（`text_content_modifier.cpp:1824-1825`） |
| AC-3.4 | WHEN `marqueeOptions.loop > 0` 且 `marqueeCount_ >= loop` THEN `AllowTextRace()` 返回 false → 触发 FINISH（`text_content_modifier.cpp:1865`） |
| AC-3.5 | WHEN `marqueeOptions.loop == -1`（无限循环） THEN `AllowTextRace()` 中 loop 条件始终不满足 → 永远不触发 FINISH，仅重复 BOUNCE → START 循环 |
| AC-3.6 | WHEN 最后一轮动画结束 THEN 先触发 BOUNCE 再触发 FINISH（同一轮动画结束回调中依次触发，`text_content_modifier.cpp:1820-1826`） |
| AC-3.7 | WHEN START 状态触发 THEN 自动关闭选择覆盖层并重置选区（`text_pattern.cpp:6996-6999`），`isMarqueeRunning_` 置为 true |
| AC-3.8 | WHEN FINISH 状态触发 THEN `isMarqueeRunning_` 置为 false（`text_pattern.cpp:7000-7001`） |
| AC-3.9 | WHEN 任意状态变化后 THEN 调用 `RecoverCopyOption()` 恢复复制能力（`text_pattern.cpp:7004`） |
| AC-3.10 | WHEN `marqueeOption_.startPolicy == MarqueeStartPolicy.ON_FOCUS` 且组件失焦且未 hovered THEN `AllowTextRace()` 返回 false → 触发 FINISH（`text_content_modifier.cpp:1868-1869`） |
| AC-3.11 | WHEN `marqueeSet_ == false` 或 `marqueeOption_.start == false` THEN `AllowTextRace()` 返回 false，不启动跑马灯，不触发任何状态回调（`text_content_modifier.cpp:1862`） |
| AC-3.12 | WHEN 动画中 `marqueeAnimationId` 与当前 `marqueeAnimationId_` 不匹配（动画被替代） THEN 旧动画的完成回调直接返回，不触发 BOUNCE/FINISH（`text_content_modifier.cpp:1815-1816`） |

## 验收追溯

| AC ID | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 | R-8, R-1 | TASK-7 | 单测 | HandleOnCopy test |
| AC-1.2 | R-8, R-9 | TASK-7 | 单测 | onWillCopy returns true test |
| AC-1.3 | R-9, R-2 | TASK-7 | 单测 | onWillCopy returns false test |
| AC-1.4 | R-9, R-18 | TASK-7 | 单测 | no onWillCopy callback test |
| AC-1.5 | R-8 | TASK-7 | 单测 | onCopy value test |
| AC-1.6 | R-19 | TASK-7 | 单测 | zero-width selection test |
| AC-1.7 | R-20 | TASK-7 | 代码审查 | null guard test |
| AC-1.8 | R-21 | TASK-7 | 单测 | empty value test |
| AC-2.1 | R-10 | TASK-7 | 单测 | long press selection test |
| AC-2.2 | R-10 | TASK-7 | 单测 | double click selection test |
| AC-2.3 | R-10 | TASK-7 | 单测 | mouse drag selection test |
| AC-2.4 | R-10 | TASK-7 | 单测 | handle drag test |
| AC-2.5 | R-10 | TASK-7 | 单测 | select all test |
| AC-2.6 | R-10, R-11 | TASK-7 | 单测 | programmatic selection test |
| AC-2.7 | R-10, R-11 | TASK-7 | 单测 | controller setTextSelection test |
| AC-2.8 | R-10 | TASK-7 | 单测 | keyboard selection test |
| AC-2.9 | R-10, R-12 | TASK-7 | 单测 | deselect test |
| AC-2.10 | R-10 | TASK-7 | 单测 | AI entity selection test |
| AC-2.11 | R-13 | TASK-7 | 单测 | dedup test |
| AC-2.12 | R-10 | TASK-7 | 单测 | shift-click extend test |
| AC-2.13 | R-10 | TASK-7 | 单测 | auto-scroll selection test |
| AC-2.14 | R-10 | TASK-7 | 单测 | drag recover selection test |
| AC-2.15 | R-10 | TASK-7 | 单测 | AI entity long press test |
| AC-2.16 | R-3 | TASK-7 | 单测 | unselectable guard test |
| AC-3.1 | R-14, R-4 | TASK-7 | 单测 | marquee start test |
| AC-3.2 | R-15 | TASK-7 | 单测 | marquee bounce test |
| AC-3.3 | R-16 | TASK-7 | 单测 | marquee finish test |
| AC-3.4 | R-16, R-5 | TASK-7 | 单测 | loop count finish test |
| AC-3.5 | R-5 | TASK-7 | 单测 | infinite loop test |
| AC-3.6 | R-15, R-16 | TASK-7 | 单测 | bounce then finish sequence test |
| AC-3.7 | R-17, R-6 | TASK-7 | 单测 | start side effects test |
| AC-3.8 | R-17 | TASK-7 | 单测 | finish side effects test |
| AC-3.9 | R-17, R-6 | TASK-7 | 单测 | RecoverCopyOption test |
| AC-3.10 | R-16, R-7 | TASK-7 | 单测 | ON_FOCUS policy finish test |
| AC-3.11 | R-22 | TASK-7 | 代码审查 | marquee not started test |
| AC-3.12 | R-23 | TASK-7 | 单测 | stale animation id test |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | onWillCopy → 剪贴板写入 → onCopy 的调用顺序是固定的。onWillCopy 在剪贴板操作之前调用，onCopy 在剪贴板操作之后调用。两者共享同一个 `value` 值（`GetSelectedText` 的返回值）（`text_pattern.cpp:1089-1113`） | — | AC-1.1, AC-1.2, AC-1.5 |
| R-2 | 行为 | — | onWillCopy 是唯一的复制操作取消点——返回 false 时整条流水线中断，菜单关闭但选区保持不变 | — | AC-1.3 |
| R-3 | 行为 | — | onTextSelectionChange 的触发受 `textSelectable` 和 `copyOption` 的联合控制：当 `textSelectable == UNSELECTABLE` 或 `copyOption == None` 时，`selection()` API 不生效（`text_pattern.cpp:1589` 守卫），自然不触发选区变化回调 | — | AC-2.16 |
| R-4 | 行为 | — | onMarqueeStateChange 的 START 状态具有副作用：自动关闭选择覆盖层（`CloseSelectOverlay`）并重置选区（`ResetSelection`），确保跑马灯滚动期间不显示选择 UI（`text_pattern.cpp:6996-6999`） | — | AC-3.7 |
| R-5 | 行为 | — | `marqueeOptions.loop` 控制 FINISH 触发条件：`loop > 0` 时 `marqueeCount_ >= loop` 触发 FINISH；`loop == -1`（无限循环）时永远不触发 FINISH | — | AC-3.4, AC-3.5 |
| R-6 | 行为 | — | 每次状态变化后均调用 `RecoverCopyOption()` 恢复复制能力——MARQUEE 运行期间 copyOption 被强制为 None（Feat-03 ADR-F5-1/Feat-05 AC-1.5），状态变化后需要重新评估 | — | AC-3.7, AC-3.9 |
| R-7 | 行为 | — | `MarqueeStartPolicy.ON_FOCUS` 策略下，跑马灯的启停由焦点和 hover 状态联合控制：`marqueeFocused_ | — | — |
| R-8 | 行为 | — | `onCopy` 回调在 `HandleOnCopy()` 末尾通过 `eventHub->FireOnCopy(value)` 触发（`text_pattern.cpp:1113`），参数为 `std::u16string` 类型的选中文本内容 | — | AC-1.1, AC-1.5 |
| R-9 | 行为 | — | `onWillCopy` 回调通过 `eventHub->FireOnWillCopy(value)` 触发（`text_pattern.cpp:1094`），返回 `bool`：true 允许复制，false 取消复制。未注册时 `FireOnWillCopy` 默认返回 true（`text_event_hub.h:55`） | — | AC-1.2, AC-1.3, AC-1.4 |
| R-10 | 行为 | — | `onTextSelectionChange` 通过 `TextPattern::HandleSelectionChange(start, end)` → `FireOnSelectionChange(min(start,end), max(start,end))` 触发（`text_pattern.cpp:7057`），参数自动归一化为 `(min, max)` 顺序 | — | AC-2.1~AC-2.15 |
| R-11 | 行为 | — | 编程式选区设置（`selection()` API 和 `setTextSelection()` 控制器方法）同样触发 `HandleSelectionChange`，与用户手势触发走相同路径 | — | AC-2.6, AC-2.7 |
| R-12 | 行为 | — | 取消选区使用特殊值 `(-1, -1)` 表示无选区状态——由 `HandleSelectionChange(-1, -1)` 触发，回调参数即为 `(-1, -1)`（`text_pattern.cpp:314, 1082`） | — | AC-2.9 |
| R-13 | 行为 | — | `HandleSelectionChange` 内置去重机制：如果新的 `(start, end)` 与 `textSelector_.GetStart(), textSelector_.GetEnd()` 完全相同，则直接 return 不触发回调（`text_pattern.cpp:7033-7035`） | — | AC-2.11 |
| R-14 | 行为 | — | `onMarqueeStateChange(START)` 在 `ResumeTextRace(bounce=false)` 中触发（`text_content_modifier.cpp:1765`），此时 `marqueeCount_` 被重置为 0 | — | AC-3.1 |
| R-15 | 行为 | — | `onMarqueeStateChange(BOUNCE)` 在动画完成回调中、当 `racePercent == marqueeRaceMaxPercent_` 时触发（`text_content_modifier.cpp:1821`），随后 `marqueeCount_++` | — | AC-3.2, AC-3.6 |
| R-16 | 行为 | — | `onMarqueeStateChange(FINISH)` 在动画完成回调中、当 `!AllowTextRace()` 时触发（`text_content_modifier.cpp:1824-1825`）；`AllowTextRace()` 检查三个条件：marqueeSet_ && start、loop 计数、ON_FOCUS 策略（`text_content_modifier.cpp:1860-1872`） | — | AC-3.3, AC-3.4, AC-3.10 |
| R-17 | 行为 | — | `FireOnMarqueeStateChange` 执行后根据状态执行副作用（`text_pattern.cpp:6996-7004`）：START → CloseSelectOverlay + ResetSelection + isMarqueeRunning_=true；FINISH → isMarqueeRunning_=false；所有状态 → RecoverCopyOption() | — | AC-3.7, AC-3.8, AC-3.9 |
| R-18 | 异常 | — | 未注册 onWillCopy 回调时，`FireOnWillCopy` 默认返回 true，复制流程正常进行 | — | AC-1.4 |
| R-19 | 异常 | — | 选区有效但 `start == end`（零宽选区）时，`HandleOnCopy` 不触发复制回调，而是调用 `HandleSelectionChange(-1, -1)` 清除选区 | — | AC-1.6 |
| R-20 | 异常 | — | `clipboard_` 为 null 或 `GetDataDetectorAdapter()` 返回 null 时，`HandleOnCopy` 通过 `CHECK_NULL_VOID` 立即返回，不触发任何回调 | — | AC-1.7 |
| R-21 | 异常 | — | 选中文本为空字符串时，`onWillCopy` 不被调用（`value.empty()` 守卫）；后续 `FireOnCopy` 被 `CHECK_NULL_VOID(!value.empty())` 阻止 | — | AC-1.8 |
| R-22 | 异常 | — | `marqueeSet_ == false` 或 `marqueeOption_.start == false` 时，`AllowTextRace()` 返回 false，`ResumeTextRace` 在入口处直接返回，不触发任何状态回调 | — | AC-3.11 |
| R-23 | 异常 | — | 动画被替代（新动画启动导致 `marqueeAnimationId` 不匹配）时，旧动画的完成回调检测到 ID 不匹配后直接返回，不触发 BOUNCE/FINISH | — | AC-3.12 |
| R-24 | 恢复 | — | onWillCopy 返回 false 取消复制后，选区状态不变，菜单关闭。用户可重新打开菜单再次尝试复制 | — | AC-1.3 |
| R-25 | 恢复 | — | 跑马灯 FINISH 后，`isMarqueeRunning_` 置 false，`RecoverCopyOption()` 恢复复制能力。如果 `marqueeOption_.start` 仍为 true 且满足条件，可重新启动 | — | AC-3.8, AC-3.9 |
| R-26 | 恢复 | — | 拖拽失败时通过 `HandleSelectionChange(recoverStart_, recoverEnd_)` 恢复之前的选区，触发 onTextSelectionChange 回调 | — | AC-2.14 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~AC-1.8, R-8, R-9, R-1, R-2 | 单测 | onWillCopy/onCopy 调用顺序、参数值、拦截能力、边界条件 |
| VM-2 | AC-2.1~AC-2.16, R-10~R-13, R-3 | 单测 | onTextSelectionChange 全场景触发、去重机制、特殊值语义、门控条件 |
| VM-3 | AC-3.1~AC-3.12, R-14~R-17, R-4~R-7 | 单测 | 跑马灯三状态触发时机、副作用、loop 控制、ON_FOCUS 策略、动画 ID 防护 |
| VM-4 | R-18~R-23 | 单测 + 代码审查 | 空回调默认行为、空值守卫、marquee 未启动守卫 |
| VM-5 | R-24~R-26 | 单测 | 拦截后恢复、FINISH 后恢复、拖拽失败恢复 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `onCopy(callback: (value: string) => void): TextAttribute` | Public | 复制完成后回调，参数为已复制文本 | AC-1.5 |
| `onWillCopy(callback: Callback<string, boolean>): TextAttribute` | Public | 复制前拦截回调，返回 false 取消复制 | AC-1.1~AC-1.4 |
| `onTextSelectionChange(callback: (selectionStart: number, selectionEnd: number) => void): TextAttribute` | Public | 选区变化回调 | AC-2.1~AC-2.16 |
| `onMarqueeStateChange(callback: Callback<MarqueeState>): TextAttribute` | Public | 跑马灯状态变化回调 | AC-3.1~AC-3.12 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** onCopy @since 11（动态版）/ @since 23（静态版）；onWillCopy @since 26.0.0（动态版和静态版）；onTextSelectionChange @since 11（动态版）/ @since 12 增加 atomicservice / @since 23（静态版）；onMarqueeStateChange @since 18（动态版）/ @since 23（静态版）
- **API 版本号策略:** 各回调 API 独立标注 @since 版本；静态版统一 @since 23 起支持

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 回调在 UI 线程触发 | 所有 4 个事件回调均在 UI 线程同步调用，回调中不应执行耗时操作 | AC-1.1~AC-3.12 |
| TextEventHub 存储 | 4 个回调存储在 `TextEventHub`（`text_event_hub.h:83-86`），每个回调至多注册一个实例，后注册覆盖前注册 | AC-1.1~AC-3.12 |
| HandleSelectionChange 去重 | `HandleSelectionChange` 在 `(start, end)` 与上次完全相同时直接返回，不触发回调（`text_pattern.cpp:7033-7035`） | AC-2.11 |
| 跑马灯动画 ID 防护 | `marqueeAnimationId_` 用于区分新旧动画，旧动画完成回调中检测到 ID 不匹配则不触发状态变化（`text_content_modifier.cpp:1815-1816`） | AC-3.12 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 回调在 UI 线程同步触发，应确保回调执行时间 < 1ms 避免阻塞渲染 | 代码审查 | 框架不做强制限制，由开发者保证 |
| 内存 | TextEventHub 4 个 `std::function` 成员，未注册时 sizeof 为空（无堆分配） | 代码审查 | text_event_hub.h |
| 安全 | N/A | - | - |
| 可靠性 | 去重机制防止重复触发；动画 ID 防护防止过期回调 | 单测 | text_pattern.cpp:7033, text_content_modifier.cpp:1815 |
| 问题定位 | `HandleSelectionChange` 在 `TextTraceEnabled` 时输出 `[id][start][end]` 日志（`text_pattern.cpp:7029-7031`）；`HandleOnCopy` 输出 `isAllowCopy` 日志（`text_pattern.cpp:1096`） | 代码审查 | 日志 tag: ACE_TEXT |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 事件回调不直接影响无障碍行为；选区变化由 `ReportSelectedText()` 独立上报 | - |
| 大字体 | 否 | 回调参数为文本索引/内容，不受字体大小影响 | - |
| 深色模式 | 否 | 回调不涉及颜色 | - |
| 多窗口/分屏 | 否 | 回调机制不受窗口模式影响 | - |
| 多用户 | 否 | 回调机制不受用户切换影响 | - |
| 版本升级 | 是 | 各回调 @since 版本不同（11/18/26.0.0），低版本不支持的回调在 SDK 层面不可用 | AC-1.1, AC-2.1, AC-3.1 |
| 生态兼容 | 是 | 静态版 @since 23 起支持，动态版和静态版参数类型略有差异（静态版 `int` vs 动态版 `number`） | 兼容性声明 |

## 行为场景（Gherkin）

```gherkin
Feature: Text 事件回调
  作为开发者
  我想要监听 Text 组件的复制、选区变化和跑马灯状态
  以便实现自定义交互逻辑

  Scenario: onWillCopy 拦截复制操作
    Given Text 组件已设置 copyOption(CopyOptions.InApp)
    And 已注册 onWillCopy 回调返回 false
    And 用户选中了部分文本
    When 用户点击选择菜单中的"复制"
    Then onWillCopy 被调用，参数为选中文本内容
    And 剪贴板内容不变
    And onCopy 不被调用
    And 选择菜单关闭

  Scenario: onWillCopy 允许复制后触发 onCopy
    Given Text 组件已设置 copyOption(CopyOptions.InApp)
    And 已注册 onWillCopy 回调返回 true
    And 已注册 onCopy 回调
    And 用户选中了部分文本
    When 用户按 Ctrl+C
    Then onWillCopy 先被调用
    And 选中文本写入剪贴板
    And onCopy 被调用，参数为相同文本内容

  Scenario: 选区变化去重
    Given Text 组件已注册 onTextSelectionChange 回调
    And 当前选区为 (5, 10)
    When 通过 selection(5, 10) 再次设置相同选区
    Then onTextSelectionChange 不被调用

  Scenario: 取消选区通知
    Given Text 组件已注册 onTextSelectionChange 回调
    And 当前有有效选区
    When 用户点击空白区域取消选区
    Then onTextSelectionChange 被调用，参数为 (-1, -1)

  Scenario: 跑马灯完整生命周期（有限循环）
    Given Text 组件 textOverflow 为 MARQUEE
    And marqueeOptions 设置 loop=2
    And 已注册 onMarqueeStateChange 回调
    When 跑马灯启动
    Then 依次触发：START → BOUNCE → BOUNCE → (BOUNCE + FINISH)
    And START 时选区被清除
    And FINISH 后 isMarqueeRunning 为 false

  Scenario: 跑马灯无限循环不触发 FINISH
    Given Text 组件 textOverflow 为 MARQUEE
    And marqueeOptions 设置 loop=-1
    And 已注册 onMarqueeStateChange 回调
    When 跑马灯运行多轮
    Then 每轮触发 BOUNCE
    And 永远不触发 FINISH

  Scenario Outline: 不同用户操作触发选区变化
    Given Text 组件内容为 "Hello World"
    And 已注册 onTextSelectionChange 回调
    When 用户执行 <操作>
    Then onTextSelectionChange 被调用，参数为 <预期选区>

    Examples:
      | 操作 | 预期选区 |
      | 长按 "World" | (6, 11) |
      | 双击 "Hello" | (0, 5) |
      | Ctrl+A | (0, 11) |
      | 点击取消选区 | (-1, -1) |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "TextEventHub 事件回调注册与触发机制"
  - repo: "openharmony/ace_engine"
    query: "TextContentModifier 跑马灯动画状态机"
  - repo: "openharmony/ace_engine"
    query: "HandleSelectionChange 全触发场景"
```

**关键文档：**
- SDK 类型定义：`interface/sdk-js/api/@internal/component/ets/text.d.ts`
- SDK 静态版类型定义：`interface/sdk-js/api/arkui/component/text.static.d.ets`
- TextEventHub：`frameworks/core/components_ng/pattern/text/text_event_hub.h`
- HandleOnCopy 流程：`frameworks/core/components_ng/pattern/text/text_pattern.cpp:1077-1114`
- HandleSelectionChange：`frameworks/core/components_ng/pattern/text/text_pattern.cpp:7025-7061`
- FireOnMarqueeStateChange：`frameworks/core/components_ng/pattern/text/text_pattern.cpp:6988-7005`
- 跑马灯动画状态机：`frameworks/core/components_ng/pattern/text/text_content_modifier.cpp:1752-1842`
