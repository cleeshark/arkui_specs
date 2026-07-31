# 特性规格

> Func-04-09-01-Feat-06 焦点激活与视觉指示：固化窗口焦点激活状态、输入驱动切换、focused 状态样式和焦点框选择、绘制与清理行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 焦点激活与视觉指示 |
| 特性编号 | Func-04-09-01-Feat-06 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 当前 NG 实现；键盘点击门槛包含 Target API 18 分支；Native 激活 API 自 API 15 提供 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性定义 Pipeline/FocusManager 的 focus active 状态机，API、Tab、手柄、activeMark、触摸和鼠标输入的激活/失活规则，跨主/子窗口同步和监听通知，以及 `UI_STATE_FOCUSED`、`FocusStyleType`、`FocusPaintParam`、`FocusBoxStyle`、自定义内部区域和兜底焦点框在焦点链上的选择、绘制与清理。

本特性不定义焦点目标如何请求和切换，也不定义页面恢复目标；它们由 Feat-02 与 Feat-05 承接。公共普通焦点属性的声明由 `Func-04-03-03-Feat-05` 承接。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 激活状态机 | 补录 FocusActiveReason、系统/主题准入、API 自动失活策略和幂等行为 |
| ADDED | 输入驱动切换 | 补录 Tab、方向键、手柄、activeMark、触摸和鼠标右键路径 |
| ADDED | 跨窗口与监听 | 补录主/子窗口同步、两类回调通知以及激活时 paint、失活时 clear |
| ADDED | focused 状态样式 | 补录 `UI_STATE_FOCUSED` 的更新、优先级与清理 |
| ADDED | 焦点框样式与参数 | 补录 FocusStyleType、FocusPaintParam、FocusBox 的颜色、宽度、边距和矩形优先级 |
| ADDED | 焦点链绘制与兜底 | 补录沿历史链选择视觉节点、FORCE_BORDER、ViewRoot 例外、z-index 和清理恢复 |
| ADDED | Target API 18 点击门槛 | 补录 inactive 状态下键盘 SELECT/SPACE 点击的版本与主题差异 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/design.md` | Baselined |
| 请求事务规格 | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/Feat-02-focus-request-clear-switch-transaction-spec.md` | Baselined |
| 导航规格 | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/Feat-03-focus-navigation-traversal-algorithm-spec.md` | Baselined |
| FocusView 恢复规格 | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/Feat-05-default-focus-focusview-recovery-spec.md` | Baselined |
| 激活状态实现 | `frameworks/core/components_ng/manager/focus/focus_manager.h:89-107,343-358`、`focus_manager.cpp:626-751` | 已核验 |
| 输入接入 | `frameworks/core/common/key_event_manager.cpp:707-717`、`frameworks/core/pipeline_ng/pipeline_context.cpp:3915-3929,5138-5142` | 已核验 |
| 视觉状态实现 | `frameworks/core/components_ng/event/focus_hub.cpp:1662-1679,1773-2071` | 已核验 |
| 样式模型 | `frameworks/core/components_ng/event/focus_type.h:23-37`、`focus_hub.h:91-252`、`focus_box.h:30-80` | 已核验 |
| 公共入口 | `interfaces/native/native_interface_focus.h:79-98`、`interfaces/native/node/native_interface_focus.cpp:50-63`、`js_view_abstract.cpp:9563-9595` | 已核验 |
| 键盘点击版本分支 | `frameworks/core/components_ng/event/focus_event_handler.cpp:190-225` | 已核验 |

## 用户故事

### US-1: 切换焦点激活状态

**作为** 窗口焦点管理器或 API 调用方，  
**我想要** 显式或自动切换 focus active，  
**以便** 键盘导航和视觉焦点框按输入模式启停。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN请求状态等于当前状态 THEN不重复通知、绘制或清理；但 USE_API 仍先更新 `autoFocusInactive` 策略 | 边界 |
| AC-1.2 | WHEN USE_API 设置 active/inactive THEN不受系统可激活开关或 Tab 主题门槛特殊豁免，仅按普通 active 准入；同时保存 isAutoInactive | 正常 |
| AC-1.3 | WHEN ACTIVE_MARK 请求状态变化 THEN直接允许切换，绕过系统 `focusCanBeActive`、Tab 主题和 pointer 自动失活拦截 | 正常 |
| AC-1.4 | WHEN普通激活且系统禁止 focus active THEN拒绝；WHEN原因是 KEY_TAB 且 AppTheme 禁止 Tab 激活 THEN拒绝 | 边界 |
| AC-1.5 | WHEN pointer 请求失活且 `autoFocusInactive=false` THEN拒绝自动失活；其他失活原因不受该开关限制 | 正常 |

### US-2: 由输入事件激活或失活

**作为** 键盘、手柄、触摸或鼠标用户，  
**我想要** 输入模式自动影响焦点视觉，  
**以便** 焦点框只在合适的交互模式显示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN key DOWN 携带 activeMark=true/false THEN分别扩展或激活焦点、或以 ACTIVE_MARK 失活 | 正常 |
| AC-2.2 | WHEN key DOWN 是 Tab THEN以 KEY_TAB 原因扩展 ViewRoot 或激活；WHEN是 joystick 方向键 THEN以 JOYSTICK_DPAD 激活 | 正常 |
| AC-2.3 | WHEN普通方向键且当前 Entry FocusView 开启 directionalKeyFocus THEN扩展 ViewRoot 或以 DEFAULT 原因激活 | 正常 |
| AC-2.4 | WHEN当前 ViewRoot 以 SELF 承接焦点 THEN激活前先 `TriggerFocusMove` 扩展到首个 tabIndex 或子焦点；返回值是扩展或激活任一成功 | 正常 |
| AC-2.5 | WHEN触摸 DOWN THEN以 POINTER_EVENT 请求失活；WHEN鼠标右键 PRESS THEN同样请求失活 | 正常 |
| AC-2.6 | WHEN focus inactive THEN普通焦点 travel 不执行，focus scroll 不触发 | 边界 |

### US-3: 同步状态、通知并刷新视觉

**作为** FocusManager，  
**我想要** 将激活状态同步到关联窗口并通知订阅组件，  
**以便** 主窗口、子窗口和自定义组件视觉一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN状态变化 THEN先写本窗口状态并同步关联主/子窗口，避免相同状态递归调用 | 正常 |
| AC-3.2 | WHEN同步完成 THEN依次通知 FocusActiveChangeCallback 和 IsFocusActiveUpdateEvent 两类监听器 | 正常 |
| AC-3.3 | WHEN最终 active THEN从根 FocusHub 执行 PaintAllFocusState；WHEN inactive THEN执行 ClearAllFocusState | 正常 |
| AC-3.4 | WHEN焦点切换事务结束且 Pipeline inactive THEN `PaintFocusState` 不重绘；active 时先清全链再绘制当前链 | 正常 |
| AC-3.5 | WHEN Pipeline/Root/FocusHub 缺失 THEN状态可能已经写入并完成同步/通知，但当前调用返回 false且无视觉刷新 | 异常 |

### US-4: 选择焦点状态样式或焦点框

**作为** 获焦组件，  
**我想要** 使用 focused 状态样式、内外边框、自定义矩形或自定义区域，  
**以便** 视觉反馈符合组件设计。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN节点存在 `UI_STATE_FOCUSED` 状态样式 THEN激活绘制时更新该状态并直接视为已处理，不再绘制 FocusStyle 边框 | 正常 |
| AC-4.2 | WHEN FocusStyleType=NONE THEN节点自身不处理；FORCE_NONE THEN视为已处理但不画边框 | 正常 |
| AC-4.3 | WHEN CUSTOM_REGION THEN回调必须返回有效 RoundRect，使用内部焦点框绘制；无回调或矩形无效返回 false | 边界 |
| AC-4.4 | WHEN CUSTOM_BORDER THEN必须存在 FocusPaintParam paintRect，直接按该矩形绘制；缺少矩形返回 false | 边界 |
| AC-4.5 | WHEN INNER_BORDER THEN默认 padding 为负主题宽度；OUTER_BORDER/FORCE_BORDER THEN默认 padding 为主题外边距；其他类型默认 0 | 正常 |
| AC-4.6 | WHEN节点有 FocusBox 自定义样式 THEN strokeColor、strokeWidth、margin 分别优先于 FocusPaintParam 和主题值 | 正常 |

### US-5: 沿焦点链绘制、兜底和清理

**作为** 焦点视觉系统，  
**我想要** 在焦点链上只选择合适节点显示指示，  
**以便** Scope 和叶节点不会重复绘制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN当前节点自身有可处理视觉 THEN记录为 lastFocusStateNode、必要时提升 z-index，并停止向子链查找 | 正常 |
| AC-5.2 | WHEN自身未处理且历史子 current、可聚焦 THEN递归到历史子；WHEN回调能绘制 THEN按回调结果结束 | 正常 |
| AC-5.3 | WHEN整条非 ViewRoot 焦点链都没有样式 THEN在尾节点临时设置 FORCE_BORDER 兜底；ViewRoot 不强制生成边框 | 正常 |
| AC-5.4 | WHEN paintWidth 近零 THEN视为视觉已处理但不提交描边；该节点仍可成为 lastFocusStateNode | 边界 |
| AC-5.5 | WHEN清理焦点状态 THEN复位 focused UI state、调用清理回调、清 RenderContext；若曾提升 z-index则复位并让父节点重排 | 恢复 |
| AC-5.6 | WHEN ClearAllFocusState 完成 THEN沿历史链递归清理，并把临时 FORCE_BORDER 恢复为 NONE | 恢复 |

### US-6: 约束 inactive 下的键盘点击

**作为** 键盘操作用户，  
**我想要** 激活状态同时约束焦点点击，  
**以便** inactive 模式不会误触发组件动作。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN内部或用户 key 回调已消费事件 THEN不再执行焦点点击门槛和 OnClick | 正常 |
| AC-6.2 | WHEN Target API 大于等于 18 且 focus inactive THEN SELECT/SPACE 不触发焦点 OnClick | 兼容 |
| AC-6.3 | WHEN Target API 小于 18 且主题 `NeedFocusHandleClick=true` THEN inactive 仍可继续焦点点击；主题为 false 时 inactive 拒绝 | 兼容 |
| AC-6.4 | WHEN SELECT 且节点不是 TabStop THEN先转换为 SPACE 再调用 OnClick；TabStop SELECT 不转换 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-4 | TASK-SKELETON-F6-1 | FocusManager 状态矩阵 UT | `focus_manager.cpp:626-715` |
| AC-2.1~2.6 | R-5~R-7 | TASK-SKELETON-F6-2 | Key/Pointer/FocusView UT | `focus_manager.cpp:718-751`、`pipeline_context.cpp:3915-3929,5138-5142` |
| AC-3.1~3.5 | R-8~R-10 | TASK-SKELETON-F6-3 | 多窗口/监听/绘制计数 UT | `focus_manager.cpp:411-420,626-685` |
| AC-4.1~4.6 | R-11~R-15 | TASK-SKELETON-F6-4 | FocusStyle/参数化渲染 UT | `focus_hub.cpp:1662-1679,1773-1923` |
| AC-5.1~5.6 | R-16~R-19 | TASK-SKELETON-F6-5 | 焦点链/z-index/clear UT | `focus_hub.cpp:1936-2071` |
| AC-6.1~6.4 | R-20 | TASK-SKELETON-F6-6 | API 17/18 键盘点击 UT | `focus_event_handler.cpp:190-225` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 状态 | USE_API | 先更新 autoFocusInactive，再判断状态幂等 | active 仍受系统普通准入 | AC-1.1, AC-1.2 |
| R-2 | 状态 | ACTIVE_MARK | 状态变化时直接允许 | 绕过后续准入检查 | AC-1.3 |
| R-3 | 准入 | 普通 active | 检查系统开关与 Tab 主题 | KEY_TAB 有额外主题门槛 | AC-1.4 |
| R-4 | 准入 | pointer inactive | autoFocusInactive=false 时拒绝 | 只拦 POINTER_EVENT | AC-1.5 |
| R-5 | 输入 | key DOWN | activeMark、Tab、joystick、directionalKeyFocus 映射原因 | 非 DOWN 不处理 | AC-2.1~2.3 |
| R-6 | 扩展 | ViewRoot SELF | 先 TriggerFocusMove，再激活 | 返回 OR 结果 | AC-2.4 |
| R-7 | 输入 | touch/mouse 与 travel | pointer 失活；inactive 禁止 travel/scroll | 右键单独处理 | AC-2.5, AC-2.6 |
| R-8 | 同步 | 状态变化 | 同步关联窗口并避免同值递归 | Weak/Container 缺失可失败 | AC-3.1 |
| R-9 | 通知 | 同步后 | 通知两类 active 监听器 | 通知先于本窗口 paint/clear | AC-3.2, AC-3.5 |
| R-10 | 视觉 | active/inactive | 根链 paint/clear；事务 active 才重绘 | 先 clear 后 paint | AC-3.3, AC-3.4 |
| R-11 | 样式 | focused state style | 更新 UI_STATE_FOCUSED 并短路边框 | clear 时复位 | AC-4.1 |
| R-12 | 样式 | NONE/FORCE_NONE | 不处理/静默处理 | FORCE_NONE 阻止下钻 | AC-4.2 |
| R-13 | 样式 | CUSTOM_REGION/CUSTOM_BORDER | 验证回调或 paintRect | 无效返回 false | AC-4.3, AC-4.4 |
| R-14 | 参数 | padding | INNER 负宽度、OUTER/FORCE 主题外边距 | 自定义 margin 优先 | AC-4.5 |
| R-15 | 参数 | color/width/margin | FocusBox→FocusPaintParam→Token/AppTheme | width 近零不画 | AC-4.6, AC-5.4 |
| R-16 | 焦点链 | 当前节点处理视觉 | 记录节点、提升 z-index、停止下钻 | 回调可决定继续返回值 | AC-5.1 |
| R-17 | 焦点链 | 当前节点未处理 | 沿 current 历史子递归 | 子必须可聚焦 | AC-5.2 |
| R-18 | 兜底 | 全链无样式 | 非 ViewRoot 尾节点临时 FORCE_BORDER | ViewRoot 例外 | AC-5.3 |
| R-19 | 清理 | Clear/ ClearAll | 清 UI state、RenderContext、z-index、临时类型 | FRAME_DESTROY 跳过清理回调 | AC-5.5, AC-5.6 |
| R-20 | 兼容 | inactive 键盘点击 | API 18 起拒绝；旧版本还受主题开关控制 | 回调已消费时不进入 | AC-6.1~6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | R-1~R-4 | 状态参数化 UT | 六种 reason、同值、系统开关、Tab 主题、autoInactive |
| VM-2 | R-5~R-7 | 输入集成 UT | activeMark、Tab、手柄、方向键、touch、右键、inactive travel/scroll |
| VM-3 | R-8~R-10 | 多窗口与监听 UT | 主/子窗口、通知顺序、缺 Pipeline、paint/clear 次数 |
| VM-4 | R-11~R-15 | 视觉样式 UT | UI state、六种 FocusStyleType、矩形有效性、三层参数优先级 |
| VM-5 | R-16~R-19 | 焦点链 UT | Scope/叶节点、全 NONE、ViewRoot、零宽、z-index、FORCE_BORDER 恢复 |
| VM-6 | R-20 | 版本兼容 UT | API 17/18、主题 true/false、active/inactive、SELECT/SPACE、TabStop |
| VM-7 | focusBox API | ArkTS/Native 属性 UT | object/size=3、负 margin、正 strokeWidth、颜色、reset 与资源更新 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| N/A | N/A | N/A | N/A | N/A | 已有 API 补录，不新增 API | AC-1.1~6.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|---------|
| N/A | N/A | 无 API 变更或废弃 | 无需迁移 | AC-1.1~6.4 |

## 接口规格

### 接口定义

| API | 签名 | 版本/范围 | 行为 | 关联 AC |
|-----|------|-----------|------|---------|
| Native focus activate | `void OH_ArkUI_FocusActivate(ArkUI_ContextHandle uiContext, bool isActive, bool isAutoInactive)` | Public C，since 15 | 设置当前 UI 实例激活状态和 pointer 自动失活策略 | AC-1.1~1.5, AC-3.1~3.5 |
| ArkTS focusBox | `focusBox(style: FocusBoxStyle): T` | Public ArkTS；目标仓库基线未纳入 canonical SDK | 配置 margin、strokeWidth、strokeColor | AC-4.5~4.6, AC-5.4 |
| Native focus box attribute | size=3：margin、strokeWidth、color | Public Native Attribute | size 非 3 返回参数错误；reset 清自定义样式 | AC-4.6, VM-7 |

`FocusStyleType`、`FocusPaintParam`、内部 Rect 回调和 FocusManager reason 为 Inner C++ 模型，不构成 SDK 稳定性承诺。

## 兼容性声明

- **已有 API 行为变更:** 否；本次仅补录当前实现。
- **最低支持版本:** `OH_ArkUI_FocusActivate` 自 API 15 提供。
- **Target API 18:** inactive 时不再允许焦点键盘点击；旧版本还受 AppTheme 兼容开关影响。
- **样式兼容:** FocusBox 自定义字段优先于组件 FocusPaintParam 和主题；未配置字段继续逐级回退。
- **跨窗口:** 激活状态会向关联主/子窗口传播；监听器可能在本窗口视觉完成前观察到新状态。
- **SDK 核验:** 目标仓库基线未纳入 canonical `interface/sdk-js/api/`，ArkTS `focusBox` 发布注解未经 canonical d.ts/d.ets 验证。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Pipeline 级状态 | 一个 FocusManager 保存一个 active 状态，并同步关联窗口 | AC-1.1~3.5 |
| 输入与视觉解耦 | 输入只改变 active/扩展状态，实际视觉由焦点链统一 paint/clear | AC-2.1~3.4 |
| 焦点链单点视觉 | 第一个可处理视觉的 current 节点阻断祖先/后代重复边框 | AC-4.1~5.3 |
| 主题回退 | 自定义样式缺项必须回退 TokenTheme/AppTheme，不得使用未初始化值 | AC-4.5~4.6 |
| 临时兜底可恢复 | FORCE_BORDER 只用于全链无样式，ClearAll 后恢复 NONE | AC-5.3, AC-5.6 |

## 非功能性需求

| 维度 | 要求 | 验证 |
|------|------|------|
| 性能 | active 状态不变时不重复遍历焦点链；状态变化仅遍历当前历史链 | VM-1, VM-5 |
| 可靠性 | 无 Pipeline、Root、Theme、RenderContext、回调或无效 Rect 时安全返回 | VM-3, VM-4 |
| 可观测性 | active reason、视觉切换和 OnClick 保持 ACE_FOCUS 日志；组件可订阅 active 更新 | 日志/监听 UT |
| 安全 | UI context 空指针由 Native 入口报告参数错误；不涉及权限、IPC 或敏感数据 | API 审查 |

## 多设备适配声明

- Tab 键、普通方向键和 joystick D-pad 使用不同激活原因，主题可单独禁止 Tab 激活。
- touch DOWN 与鼠标右键 PRESS 触发自动失活；`isAutoInactive=false` 可保持 API 激活状态。
- 焦点框颜色、宽度和外边距随 Token/AppTheme 与资源配置变化，不新增设备专属常量。

## 全局特性影响

| 影响面 | 结论 |
|--------|------|
| 焦点导航 | inactive 阻止 Feat-03 travel；Tab/手柄可先激活或扩展 ViewRoot |
| FocusView 恢复 | Feat-05 API 26 UIExtensionWindow 分支读取 active 状态 |
| 组件视觉 | 组件可通过 focused state style、Pattern style、FocusBox 或回调接入 |
| 点击行为 | API 18 起 inactive 禁止焦点键盘点击 |
| 多窗口 | 主/子窗口 active 状态同步，组件监听收到同一布尔值 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 焦点激活与视觉指示

  Scenario: API 激活并禁止 pointer 自动失活
    Given 当前焦点状态为 inactive
    When 调用 OH_ArkUI_FocusActivate(active=true, isAutoInactive=false)
    Then 当前及关联窗口切为 active
    And 当前焦点链绘制视觉指示
    When 后续收到 touch down
    Then active 状态保持不变

  Scenario: 全焦点链无样式时兜底
    Given 当前叶节点及祖先 FocusStyleType 都为 NONE
    And 当前节点不是 ViewRoot
    When active 状态触发 PaintAllFocusState
    Then 焦点链尾节点临时使用 FORCE_BORDER
    When ClearAllFocusState
    Then 临时类型恢复为 NONE

  Scenario Outline: inactive 键盘点击兼容
    Given Target API 为 <api>
    And focus active 为 false
    And NeedFocusHandleClick 为 <theme>
    When 焦点节点收到 SPACE
    Then OnClick 结果为 <result>

    Examples:
      | api | theme | result |
      | 17  | true  | 可调用 |
      | 17  | false | 不调用 |
      | 18  | true  | 不调用 |
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] active reason、输入、跨窗口、监听、样式、焦点链和版本分支均有 AC
- [x] Delta 表头和类型符合仓库规则
- [x] API 15 与 Target API 18 边界已区分
- [x] Inner C++ 样式类型未误写为 Public SDK 契约
- [x] 风险行为以当前实现为准，未夹带产品修复

## context-references

- `frameworks/core/components_ng/manager/focus/focus_manager.h`
- `frameworks/core/components_ng/manager/focus/focus_manager.cpp`
- `frameworks/core/components_ng/event/focus_type.h`
- `frameworks/core/components_ng/event/focus_box.h`
- `frameworks/core/components_ng/event/focus_hub.h`
- `frameworks/core/components_ng/event/focus_hub.cpp`
- `frameworks/core/components_ng/event/focus_event_handler.cpp`
- `frameworks/core/common/key_event_manager.cpp`
- `frameworks/core/pipeline_ng/pipeline_context.cpp`
- `frameworks/core/components_ng/base/view_abstract.cpp`
- `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp`
- `interfaces/native/native_interface_focus.h`
- `interfaces/native/node/native_interface_focus.cpp`
- `interfaces/native/node/style_modifier.cpp`
- `test/unittest/core/manager/focus_manager_test_ng.cpp`
- `test/unittest/core/event/focus_core/focus_core_test.cpp`
