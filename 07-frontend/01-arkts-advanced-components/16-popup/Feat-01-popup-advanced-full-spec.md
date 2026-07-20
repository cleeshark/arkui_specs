# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Popup 高级组件全量规格 (v1/v2) |
| 特性编号 | Func-07-01-16-Feat-01 |
| FuncID | 07-01-16 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 11 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出 Popup v1/v2 自引入以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Popup v1: @Builder Popup(options: PopupOptions) | @since 11, atomicservice 12 |
| ADDED | PopupTextOptions (text, fontSize, fontColor, fontWeight) | v1 消息/标题文本选项 |
| ADDED | PopupButtonOptions (text, action, fontSize, fontColor) | v1 按钮选项 |
| ADDED | PopupIconOptions (image, width=32VP, height=32VP, fillColor, borderRadius) | v1 图标选项 |
| ADDED | PopupOptions: icon?, title?, message, showClose?(default true), onClose?, buttons?, direction? | v1 主选项 |
| ADDED | direction (Direction.Auto) | @since 12 |
| ADDED | maxWidth (default 400vp) | @since 18 |
| ADDED | Static API (Popup v1) | @since 23 |
| ADDED | Popup v2: @Builder PopupV2(options: PopupV2InitInfo) | @since 26 |
| ADDED | PopupV2Button (text, buttonTextModifier?: TextModifier, action) | v2 按钮选项 |
| ADDED | PopupV2InitInfo: onClose?, title?(ResourceStr), titleModifier?, showClose?, buttons?, message(ResourceStr), messageModifier?, maxWidth?, icon?(ResourceStr), iconModifier?, direction? | v2 主选项，简化为 ResourceStr + Modifier |
| ADDED | Static API (Popup v2) | @since 26 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/07-frontend/01-arkts-advanced-components/16-popup/design.md`
- **KB 路由**: `docs/kb/components/overlay/popup_advanced.md`
- **SDK 类型定义**:
  - Popup v1 Dynamic: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.advanced.Popup.d.ets`
  - Popup v1 Static: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.advanced.Popup.static.d.ets`
  - Popup v2 Dynamic: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.advanced.PopupV2.d.ets`
  - Popup v2 Static: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.advanced.PopupV2.static.d.ets`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: Popup v1 基础弹窗创建

**角色**: 应用开发者
**期望**: 我想要使用 Popup v1 高级组件创建包含图标、标题、消息和按钮的弹窗
**价值**: 以便快速实现符合系统设计规范的弹窗交互

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 `Popup({ message: { text: '提示消息' } })` THEN 渲染包含消息文本的弹窗，无标题时消息使用 plainFontColor（fontPrimary）（`popup.ets:390-401`） | 正常 |
| AC-1.2 | WHEN 创建带 icon 的 Popup `Popup({ icon: { image: 'app.media.icon' }, message: { text: '消息' } })` THEN 弹窗左侧渲染 Image，默认尺寸 32×32vp（`popup.ets:90-91, 296-297`） | 正常 |
| AC-1.3 | WHEN 创建带 title 的 Popup THEN 标题使用 PopupTextOptions（text/fontSize/fontColor/fontWeight），消息字体颜色降级为 fontSecondary（`popup.ets:102-108, 395-398`） | 正常 |
| AC-1.4 | WHEN 未设置 fontSize/fontColor 时 THEN 标题使用 theme 默认值（fontSize=ohos_id_text_size_sub_title2, fontColor=font_primary, fontWeight=Medium），消息使用 theme 默认值（fontSize=ohos_id_text_size_body2, fontWeight=Regular）（`popup.ets:102-108, 136-141`） | 正常 |

### US-2: Popup v1 布局约束

**角色**: 应用开发者
**期望**: 我想要 Popup 弹窗有合理的尺寸约束
**价值**: 以便弹窗在不同屏幕尺寸下都能正确显示

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 未设置 maxWidth THEN 弹窗最大宽度为 400vp（`popup.ets:210, 698`） | 边界 |
| AC-2.2 | WHEN 屏幕宽度 < 400vp THEN 弹窗最大宽度回退为屏幕宽度（`popup.ets:717-722`） | 边界 |
| AC-2.3 | WHEN 屏幕高度 > 480vp THEN 弹窗最大高度为 480vp；否则为屏幕高度减 80vp（`popup.ets:727-731`） | 边界 |
| AC-2.4 | WHEN 设置 maxWidth 为负数 THEN 回退到默认值 400vp（`popup.ets:711-712`） | 异常 |
| AC-2.5 | WHEN 设置 maxWidth（@since 18）为有效值 THEN 弹窗最大宽度使用该值，但不超过屏幕宽度（`popup.ets:709-710, 717-718`） | 正常 |

### US-3: Popup v1 按钮

**角色**: 应用开发者
**期望**: 我想要在弹窗中添加最多两个操作按钮
**价值**: 以便用户可以在弹窗中进行操作选择

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 buttons 为 `[{ text: '取消', action: cancelFn }, { text: '确定', action: confirmFn }]` THEN 弹窗底部渲染两个按钮，使用 FlexWrap.Wrap 布局（`popup.ets:835-906`） | 正常 |
| AC-3.2 | WHEN 按钮文本为空字符串 THEN 该按钮不渲染（`popup.ets:836, 871`） | 边界 |
| AC-3.3 | WHEN 点击按钮 THEN 触发对应 button.action 回调（`popup.ets:861-865, 896-900`） | 正常 |
| AC-3.4 | WHEN 鼠标悬停按钮 THEN 背景色切换为 hoverColor（ohos_id_color_hover），移出时恢复为 backgroundColor（ohos_id_color_background_transparent）（`popup.ets:854-860, 889-895`） | 正常 |
| AC-3.5 | WHEN 按钮实际尺寸小于 responseRegion 值 THEN 扩展响应区域并居中偏移（`popup.ets:507-530`） | 边界 |

### US-4: Popup v1 关闭按钮与滚动

**角色**: 应用开发者
**期望**: 我想要弹窗有关闭按钮和消息滚动能力
**价值**: 以便用户可以关闭弹窗并查看长文本消息

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN showClose 为 true（默认）或未设置 THEN 渲染关闭按钮（SymbolGlyph xmark，22×22vp）（`popup.ets:150-151, 774-778`） | 正常 |
| AC-4.2 | WHEN showClose 为 false THEN 不渲染关闭按钮 | 正常 |
| AC-4.3 | WHEN 消息文本高度 > 可用滚动高度 + 1 THEN 启用 Scroll 组件，scrollMaxHeight 限制滚动区域；否则不启用 Scroll（`popup.ets:602-606`） | 边界 |
| AC-4.4 | WHEN 点击关闭按钮 THEN 触发 onClose 回调（`popup.ets:799-803`） | 正常 |
| AC-4.5 | WHEN 横竖屏切换 THEN MediaQuery listener 触发 setScrollMaxHeight 重新计算（`popup.ets:571-577`） | 正常 |

### US-5: Popup v1 主题与 RTL

**角色**: 应用开发者
**期望**: 我想要 Popup 支持深色模式和 RTL 布局
**价值**: 以便弹窗在不同语言和主题下正确显示

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 主题切换 THEN onWillApplyTheme 被调用，更新 title.fontColor=fontPrimary, button.fontColor=fontEmphasize, message.fontColor=fontSecondary, message.plainFontColor=fontPrimary, closeButtonFillColor=iconSecondary（`popup.ets:563-569`） | 正常 |
| AC-5.2 | WHEN Configuration.getLocale().dir === 'rtl' 且 direction=Auto THEN 标题对齐为 TextAlign.End（`popup.ets:738-743`） | 正常 |
| AC-5.3 | WHEN direction 设置为 Ltr 或 Rtl THEN 所有子组件应用该 direction 属性（`popup.ets:750, 762, 806, 827, 850, 907, 1074`） | 正常 |

### US-6: Popup v2 状态管理升级

**角色**: 应用开发者
**期望**: 我想要使用 State V2 的 Popup v2 组件，支持 attributeModifier
**价值**: 以便以更灵活的方式定制弹窗样式

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 创建 `PopupV2({ message: '消息' })` THEN 使用 @ComponentV2 PopupV2ComponentV2，通过 @Param 接收参数，@Local 管理内部状态（`popupv2.ets:255-270`） | 正常 |
| AC-6.2 | WHEN 设置 iconModifier(ImageModifier) THEN Image 组件应用 attributeModifier（`popupv2.ets:742-752`） | 正常 |
| AC-6.3 | WHEN 设置 titleModifier/messageModifier(TextModifier) THEN 对应 Text 组件应用 attributeModifier（`popupv2.ets:769, 819, 941`） | 正常 |
| AC-6.4 | WHEN 设置 buttonTextModifier(TextModifier) THEN 按钮内 Text 应用 attributeModifier（`popupv2.ets:847, 884, 1004, 1041`） | 正常 |
| AC-6.5 | WHEN PopupV2 v2 选项中 title 为 ResourceStr（非 PopupTextOptions）THEN 标题直接作为 Text 内容，样式通过 titleModifier 设置（`popupv2.ets:181-184, 263`） | 正常 |

### US-7: Popup v2 大字体支持

**角色**: 终端用户
**期望**: 我想要在系统设置大字体时弹窗文字不会溢出
**价值**: 以便在辅助功能场景下弹窗仍可用

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 系统字体缩放 > 2 THEN v2 通过 `maxFontScale(Math.min(appMaxFontScale, MAX_FONT_SCALE))` 将字体缩放限制为 2（`popupv2.ets:198, 770, 820`） | 边界 |
| AC-7.2 | WHEN aboutToAppear 执行 THEN 通过 `uiContext.getMaxFontScale()` 获取系统字体缩放并存储到 appMaxFontScale（`popupv2.ets:564`） | 正常 |
| AC-7.3 | WHEN v1 Popup 运行 THEN 不支持 maxFontScale 限制（v1 不调用 maxFontScale），v1 为已知限制 | 边界 |
| AC-7.4 | WHEN v2 的标题/消息/按钮文本渲染 THEN 均应用 maxFontScale(Math.min(appMaxFontScale, 2))（`popupv2.ets:770, 820, 848, 885, 942, 1005, 1042`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2, R-3, R-7 | TASK-POPUP-01 | UT | `advanced_ui_component/popup/source/popup.ets` |
| AC-2.1 ~ AC-2.5 | R-4, R-5 | TASK-POPUP-01 | UT | 布局约束测试 |
| AC-3.1 ~ AC-3.5 | R-6, R-8 | TASK-POPUP-01 | UT | 按钮交互测试 |
| AC-4.1 ~ AC-4.5 | R-9, R-10, R-11 | TASK-POPUP-01 | UT | 关闭按钮和滚动测试 |
| AC-5.1 ~ AC-5.3 | R-12, R-13 | TASK-POPUP-01 | UT + 手工 | 主题和 RTL 测试 |
| AC-6.1 ~ AC-6.5 | R-14, R-15 | TASK-POPUP-01 | UT | v2 状态管理测试 |
| AC-7.1 ~ AC-7.4 | R-16, R-17 | TASK-POPUP-01 | 手工 | 大字体限制测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `popup.ets:174-179` PopupTextOptions | text 为必填，fontSize/fontColor/fontWeight 可选，未设置时使用 theme 默认值 | — | AC-1.1, AC-1.4 |
| R-2 | 行为 | `popup.ets:188-194` PopupIconOptions | image 为必填，width/height 默认 32vp，fillColor 默认空字符串，borderRadius 默认 ohos_id_corner_radius_default_s | — | AC-1.2 |
| R-3 | 行为 | `popup.ets:196-205` PopupOptions | message 为必填，icon/title/direction/showClose/onClose/buttons/maxWidth 可选 | — | AC-1.1, AC-1.3 |
| R-4 | 行为 | `popup.ets:210, 698` POPUP_DEFAULT_MAXWIDTH | 默认最大宽度 400vp，当 maxWidth 未设置时使用 | — | AC-2.1 |
| R-5 | 边界 | `popup.ets:709-712, 717-731` getApplyMaxSize | maxWidth < 0 回退 400vp；屏幕宽/高小于阈值时使用屏幕尺寸；maxHeight 上限 480vp | — | AC-2.2 ~ AC-2.5 |
| R-6 | 行为 | `popup.ets:181-186, 835-906` PopupButtonOptions + Flex 布局 | 最多 2 个按钮，空文本不渲染，使用 FlexWrap.Wrap 布局 | buttons 数组长度 ≤ 2 | AC-3.1, AC-3.2 |
| R-7 | 行为 | `popup.ets:390-401` getMessageFontColor | 有标题时消息使用 fontSecondary，无标题时使用 plainFontColor(fontPrimary) | — | AC-1.1, AC-1.3 |
| R-8 | 行为 | `popup.ets:861-865, 896-900, 507-530` 按钮点击 + 响应区域 | 点击触发 action 回调；按钮尺寸 < responseRegion 时扩展响应区域 | — | AC-3.3, AC-3.5 |
| R-9 | 行为 | `popup.ets:150-151, 774-804` 关闭按钮 | showClose=true 或未设置时渲染 SymbolGlyph xmark（22×22vp），点击触发 onClose | showClose 默认 true | AC-4.1, AC-4.4 |
| R-10 | 边界 | `popup.ets:584-607` setScrollMaxHeight | textHeight > scrollMaxHeight + 1 时启用 Scroll，否则不启用 | scrollMaxHeight = 可用高度 - title - button - padding | AC-4.3 |
| R-11 | 行为 | `popup.ets:571-577` MediaQuery listener | 横竖屏切换时延迟 10ms 重新计算 scrollMaxHeight | — | AC-4.5 |
| R-12 | 行为 | `popup.ets:563-569` onWillApplyTheme | 主题切换时更新 title/button/message/closeButton 颜色属性 | — | AC-5.1 |
| R-13 | 行为 | `popup.ets:738-743` getTitleTextAlign | RTL + Auto direction → TextAlign.End；否则 TextAlign.Start | — | AC-5.2, AC-5.3 |
| R-14 | 行为 | `popupv2.ets:255-270` @ComponentV2 PopupV2ComponentV2 | @Param 接收外部参数，@Local 管理内部状态，@Require @Param 标注必传参数 | — | AC-6.1 |
| R-15 | 行为 | `popupv2.ets:742-752, 769, 819, 847, 884` attributeModifier | v2 支持 iconModifier(ImageModifier)、titleModifier/messageModifier(TextModifier)、buttonTextModifier(TextModifier) | — | AC-6.2 ~ AC-6.5 |
| R-16 | 边界 | `popupv2.ets:198, 770, 820, 848, 885, 942, 1005, 1042` maxFontScale | v2 限制字体缩放上限为 MAX_FONT_SCALE=2，通过 Math.min(appMaxFontScale, 2) | MAX_FONT_SCALE = 2 | AC-7.1, AC-7.4 |
| R-17 | 行为 | `popupv2.ets:564` aboutToAppear | 通过 uiContext.getMaxFontScale() 获取系统字体缩放存储到 appMaxFontScale | — | AC-7.2 |
| R-18 | 异常 | `popupv2.ets:694-699` getApplyMaxSize 异常 | display.getDefaultDisplaySync() 抛异常时回退到 maxWidth=400, maxHeight=480 | — | AC-2.4 |
| R-19 | 恢复 | `popup.ets:579-582` aboutToDisappear | 组件销毁时清理 MediaQuery listener | — | AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT | v1 基础弹窗创建和默认值 |
| VM-2 | AC-2.1 ~ AC-2.5 | UT | 布局约束和 maxWidth 边界 |
| VM-3 | AC-3.1 ~ AC-3.5 | UT | 按钮渲染、交互和响应区域 |
| VM-4 | AC-4.1 ~ AC-4.5 | UT | 关闭按钮、滚动和屏幕切换 |
| VM-5 | AC-5.1 ~ AC-5.3 | UT + 手工 | 主题更新和 RTL 对齐 |
| VM-6 | AC-6.1 ~ AC-6.5 | UT | v2 State V2 和 attributeModifier |
| VM-7 | AC-7.1 ~ AC-7.4 | 手工 | v2 maxFontScale 限制 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC | @since |
|----------|------|----------|---------|--------|
| @Builder Popup(options: PopupOptions) | Public | Popup v1 高级组件入口 | AC-1.1 ~ AC-5.3 | 11 |
| PopupTextOptions | Public | v1 文本选项接口 | AC-1.1, AC-1.3 | 11 |
| PopupButtonOptions | Public | v1 按钮选项接口 | AC-3.1 | 11 |
| PopupIconOptions | Public | v1 图标选项接口 | AC-1.2 | 11 |
| PopupOptions.direction | Public | 弹窗方向 | AC-5.3 | 12 |
| PopupOptions.maxWidth | Public | 弹窗最大宽度 | AC-2.5 | 18 |
| Popup v1 Static API | Public | 静态前端 Popup v1 | 全部 | 23 |
| @Builder PopupV2(options: PopupV2InitInfo) | Public | Popup v2 高级组件入口 | AC-6.1 ~ AC-7.4 | 26 |
| PopupV2Button | Public | v2 按钮选项（含 buttonTextModifier） | AC-6.4 | 26 |
| PopupV2InitInfo | Public | v2 主选项（ResourceStr + Modifier） | AC-6.1 ~ AC-6.5 | 26 |
| Popup v2 Static API | Public | 静态前端 Popup v2 | 全部 | 26 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| 无 | — | — |

> 截至当前版本，Popup v1/v2 未发现任何 @deprecated 或 @useinstead 标注的 API。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否
  - Popup v1 基础 API @since 11，direction @since 12，maxWidth @since 18，Static API @since 23
  - Popup v2 全量 @since 26，无破坏性变更
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 11 (v1), API 26 (v2)
- **API 版本号策略:** v1 基础 API @since 11, direction @since 12, maxWidth @since 18, Static @since 23; v2 全量 @since 26

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 高级组件无独立 Pattern | Popup v1/v2 基于 Row/Column/Flex/Text/Scroll/Button/SymbolGlyph/Image 组合，不涉及 components_ng/pattern/ | 全部 |
| v1 不支持 attributeModifier | v1 使用 PopupTextOptions 复合选项，不支持 TextModifier/ImageModifier | AC-6.2 ~ AC-6.5 |
| v1 不支持 maxFontScale | v1 不调用 maxFontScale API，v2 通过 MAX_FONT_SCALE=2 限制 | AC-7.3 |
| @Require @Param 约束 | v2 中 maxWidth/iconModifier/titleModifier/messageModifier 标注为 @Require @Param | AC-6.1 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 弹窗渲染首帧 ≤ 100ms | 手工 + Trace | Trace 打点 |
| 内存 | 弹窗关闭后 MediaQuery listener 正确清理 | UT | aboutToDisappear 验证 |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | 横竖屏切换后弹窗布局正确重算 | UT + 手工 | MediaQuery listener 测试 |
| 问题定位 | console.error 覆盖 display 异常路径 | 代码审查 | `popup.ets:419, 702` |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 横竖屏切换时重新计算布局 | MediaQuery listener 触发 setScrollMaxHeight | 手工 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 关闭按钮设置 accessibilityText，按钮设置 focusable(true) | AC-4.1, AC-3.1 |
| 大字体 | 是 | v2 通过 maxFontScale 限制字体缩放上限为 2；v1 不支持（已知限制） | AC-7.1 ~ AC-7.4 |
| 深色模式 | 是 | 通过 onWillApplyTheme 回调更新颜色属性 | AC-5.1 |
| 多窗口/分屏 | 否 | Popup 无窗口相关特殊行为 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | direction @since 12, maxWidth @since 18 需版本判断 | AC-2.5, AC-5.3 |
| 生态兼容 | 否 | 无 C API | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Popup 高级组件
  作为应用开发者
  我想要使用 Popup 高级组件创建弹窗
  以便快速实现符合系统设计规范的弹窗交互

  Scenario: Popup v1 基础弹窗
    Given 应用调用 Popup({ message: { text: '提示消息' } })
    When PopupComponent 渲染
    Then 显示包含消息文本的弹窗
    And 无标题时消息字体颜色为 plainFontColor (fontPrimary)

  Scenario: Popup v1 带图标和标题
    Given 应用调用 Popup({ icon: { image: 'icon' }, title: { text: '标题' }, message: { text: '消息' } })
    When PopupComponent 渲染
    Then 左侧显示 32x32vp 图标
    And 标题使用 sub_title2 字号和 fontPrimary 颜色
    And 消息字体颜色降级为 fontSecondary

  Scenario: maxWidth 边界处理
    Given 应用设置 maxWidth 为负数
    When getApplyMaxSize 执行
    Then maxWidth 回退到默认值 400vp

  Scenario: 屏幕宽度小于 400vp
    Given 设备屏幕宽度为 360vp
    When getApplyMaxSize 执行
    Then 弹窗最大宽度为 360vp (屏幕宽度)

  Scenario: 消息滚动启用
    Given 消息文本高度超过可用滚动高度
    When setScrollMaxHeight 执行
    Then 启用 Scroll 组件限制滚动区域

  Scenario: Popup v2 maxFontScale 限制
    Given 系统字体缩放设置为 3
    When PopupV2ComponentV2 aboutToAppear 执行
    Then appMaxFontScale 获取为 3
    And 文本渲染时 maxFontScale 限制为 2

  Scenario: Popup v2 attributeModifier
    Given 应用设置 titleModifier(TextModifier)
    When PopupV2ComponentV2 渲染
    Then 标题 Text 组件应用 attributeModifier

  Scenario: 主题切换
    Given Popup 组件已渲染
    When 系统主题切换
    Then onWillApplyTheme 被调用
    And title/button/message/closeButton 颜色属性更新

  Scenario: RTL 布局
    Given 系统语言为 RTL 语言且 direction=Auto
    When getTitleTextAlign 执行
    Then 返回 TextAlign.End
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
    query: "Popup v1 PopupComponent 组件实现和 PopupOptions 接口定义"
  - repo: "openharmony/ace_engine"
    query: "Popup v2 PopupV2ComponentV2 State V2 状态管理和 attributeModifier 支持"
  - repo: "openharmony/ace_engine"
    query: "Popup 高级组件 onWillApplyTheme 主题机制和 RTL 布局支持"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@ohos.arkui.advanced.Popup.d.ets`, `@ohos.arkui.advanced.PopupV2.d.ets`
- KB 路由: `docs/kb/components/overlay/popup_advanced.md`
- 源码入口: `advanced_ui_component/popup/source/popup.ets`, `advanced_ui_component/popupv2/source/popupv2.ets`
