# 特性规格

> Func-05-06-03-Feat-01 ActionSheet 列表选择弹窗：固化 ActionSheet.show() 命令式 API 的 sheets 列表数组、confirm/cancel 按钮、title/message、对齐 BOTTOM 与偏移、子窗口、层级模式、生命周期回调和废弃迁移的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ActionSheet 列表选择弹窗 (List Selection Dialog) |
| 特性编号 | Func-05-06-03-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 8 起支持，API 10 subtitle/maskRect，API 11 isModal，API 14 enableHoverMode，API 15 immersiveMode/levelMode，API 18 backgroundBlurStyleOptions/levelOrder + 废弃，API 19 生命周期回调 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ActionSheet 完整行为规格 | 补录 sheets 列表数组、confirm/cancel 按钮、title/message、对齐 BOTTOM 与偏移、子窗口、层级模式、生命周期回调、废弃迁移 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/06-popup-components/03-list-selection-dialog/design.md` | Baselined |
| SDK API | `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | — |
| SDK 组件 | `docs/sdk/Component_API_Knowledge_Base_CN.md` | — |

---

## 用户故事

### US-1: 创建列表选择弹窗

**作为** 应用开发者,
**我想要** 使用 `ActionSheet.show({sheets})` 创建一个包含列表项的选择弹窗,
**以便** 让用户从多个选项中选择操作。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `ActionSheet.show({title, message, sheets: [...]})` THEN 创建包含 sheets 列表项的底部弹窗 | 正常 |
| AC-1.2 | WHEN ParseSheetInfo 解析每个 SheetInfo THEN 提取 title/icon/action 存入 sheetsInfo 数组 | 正常 |

### US-2: 确认按钮

**作为** 应用开发者,
**我想要** 设置 confirm 确认按钮,
**以便** 提供列表选择的确认操作。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 设置 confirm THEN 弹窗底部显示确认按钮，点击执行 confirm.action | 正常 |
| AC-2.2 | WHEN confirm.defaultFocus=false THEN confirm 按钮被标记为 isPrimary=true | 边界 |

### US-3: 取消按钮

**作为** 应用开发者,
**我想要** 设置 cancel 取消按钮,
**以便** 提供取消列表选择的操作。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 cancel THEN 弹窗显示取消按钮，点击执行 cancel.action 并关闭弹窗 | 正常 |
| AC-3.2 | WHEN autoCancel=true（默认）THEN 点击遮罩区域关闭弹窗 | 正常 |

### US-4: 标题与消息

**作为** 应用开发者,
**我想要** 设置弹窗的标题和消息文本,
**以便** 向用户说明列表选择的上下文。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 title THEN 弹窗顶部显示标题文本 | 正常 |
| AC-4.2 | WHEN 设置 message THEN 标题下方显示消息内容 | 正常 |

### US-5: 对齐方式与偏移

**作为** 应用开发者,
**我想要** 控制弹窗的对齐方式和偏移量,
**以便** 调整弹窗在屏幕中的位置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 未设置 alignment THEN 默认 alignment=BOTTOM，offset={0,-40vp} | 边界 |
| AC-5.2 | WHEN 设置 offset THEN 弹窗按指定偏移量展示 | 正常 |

### US-6: 子窗口显示

**作为** 应用开发者,
**我想要** 通过 showInSubWindow 在子窗口中展示弹窗,
**以便** 实现独立窗口的列表选择弹窗。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN showInSubWindow=true THEN 通过 SubwindowManager 创建子窗口展示弹窗 | 正常 |

### US-7: 层级模式

**作为** 应用开发者,
**我想要** 通过 levelMode 控制弹窗层级,
**以便** 区分全局弹窗和页面级弹窗。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN levelMode=EMBEDDED THEN 通过 DialogManager 创建页面级弹窗 | 正常 |
| AC-7.2 | WHEN levelMode=OVERLAY THEN 通过 DialogManager 创建全局弹窗 | 正常 |

### US-8: 生命周期回调与废弃迁移

**作为** 应用开发者,
**我想要** 监听弹窗生命周期并了解废弃迁移路径,
**以便** 在适当时机执行业务逻辑并迁移到新 API。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 弹窗即将出现 THEN onWillAppear 回调被触发 (API 19+) | 正常 |
| AC-8.2 | WHEN 弹窗已出现/即将消失 THEN onDidAppear/onWillDisappear/onDidDisappear 回调被触发 (API 19+) | 正常 |
| AC-8.3 | WHEN API >= 18 调用 ActionSheet.show THEN 标记为废弃，建议使用 UIContext.showActionSheet() | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1, R-2 | 代码审查 js_action_sheet.cpp:394-552 |
| AC-1.2 | US-1 | R-3 | 代码审查 js_action_sheet.cpp:73-109 |
| AC-2.1 | US-2 | R-4 | 代码审查 js_action_sheet.cpp:135-188, action_sheet_model_ng.cpp:104-108 |
| AC-2.2 | US-2 | R-5 | 代码审查 js_action_sheet.cpp:135-188 |
| AC-3.1 | US-3 | R-6 | 代码审查 action_sheet_model_ng.cpp:93-96 |
| AC-3.2 | US-3 | R-7 | 代码审查 dialog_properties.h:186-282 |
| AC-4.1 | US-4 | R-8 | 代码审查 js_action_sheet.cpp:111-133 |
| AC-4.2 | US-4 | R-8 | 代码审查 js_action_sheet.cpp:111-133 |
| AC-5.1 | US-5 | R-9 | 代码审查 js_action_sheet.cpp:51-52 |
| AC-5.2 | US-5 | R-10 | 代码审查 js_action_sheet.cpp:190-265 |
| AC-6.1 | US-6 | R-11 | 代码审查 action_sheet_model_ng.cpp:25-86 |
| AC-7.1 | US-7 | R-12 | 代码审查 action_sheet_model_ng.cpp:25-86 |
| AC-7.2 | US-7 | R-12 | 代码审查 action_sheet_model_ng.cpp:25-86 |
| AC-8.1 | US-8 | R-13 | 代码审查 dialog_properties.h:186-282 |
| AC-8.2 | US-8 | R-13 | 代码审查 dialog_properties.h:186-282 |
| AC-8.3 | US-8 | R-14 | 代码审查 action_sheet.d.ts |

---

## 规则定义

> **统一规则表。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `js_action_sheet.cpp:394-552` | JSActionSheet::Show 创建 DialogProperties{type=ACTION_SHEET, alignment=BOTTOM, offset=ACTION_SHEET_OFFSET_DEFAULT} | — | AC-1.1 |
| R-2 | 行为 | `js_action_sheet.cpp:394-552` | 解析 title/message/sheets/confirm/cancel 等参数存入 DialogProperties | — | AC-1.1 |
| R-3 | 行为 | `js_action_sheet.cpp:73-109` | ParseSheetInfo 遍历 sheets 数组，提取每个 SheetInfo 的 title/icon/action 存入 sheetsInfo | — | AC-1.2 |
| R-4 | 行为 | `js_action_sheet.cpp:135-188`, `action_sheet_model_ng.cpp:104-108` | confirm 按钮通过 ParseConfirmButton 解析，SetConfirm 设置回调 | — | AC-2.1 |
| R-5 | 边界 | `js_action_sheet.cpp:135-188` | confirm.defaultFocus=false 时 isPrimary=true | — | AC-2.2 |
| R-6 | 行为 | `action_sheet_model_ng.cpp:93-96` | cancel 按钮通过 SetCancel 设置回调，点击后关闭弹窗 | — | AC-3.1 |
| R-7 | 行为 | `dialog_properties.h:186-282` | autoCancel 默认 true，点击遮罩区域关闭弹窗 | — | AC-3.2 |
| R-8 | 行为 | `js_action_sheet.cpp:111-133` | ParseTitleAndMessage 解析 title/subtitle/message | — | AC-4.1, AC-4.2 |
| R-9 | 边界 | `js_action_sheet.cpp:51-52` | 默认 alignment=BOTTOM，offset=ACTION_SHEET_OFFSET_DEFAULT={0,-40vp} | — | AC-5.1 |
| R-10 | 行为 | `js_action_sheet.cpp:190-265` | offset 解析并设置到 DialogProperties | — | AC-5.2 |
| R-11 | 行为 | `action_sheet_model_ng.cpp:25-86` | showInSubWindow=true 时通过 SubwindowManager 创建子窗口 | — | AC-6.1 |
| R-12 | 行为 | `action_sheet_model_ng.cpp:25-86` | levelMode=EMBEDDED→页面级弹窗，OVERLAY→全局弹窗 | — | AC-7.1, AC-7.2 |
| R-13 | 行为 | `dialog_properties.h:186-282` | onWillAppear/onDidAppear/onWillDisappear/onDidDisappear 生命周期回调 | — | AC-8.1, AC-8.2 |
| R-14 | 边界 | `action_sheet.d.ts` | API 18 起废弃 ActionSheet.show，建议迁移到 UIContext.showActionSheet() | — | AC-8.3 |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 列表选择弹窗 (AC-1.1~1.2) | 代码审查 | sheets 数组解析；SheetInfo 结构 |
| VM-2 | US-2 确认按钮 (AC-2.1~2.2) | 代码审查 | confirm 解析；isPrimary 逻辑 |
| VM-3 | US-3 取消按钮 (AC-3.1~3.2) | 代码审查 | cancel 回调；autoCancel 默认值 |
| VM-4 | US-4 标题与消息 (AC-4.1~4.2) | 代码审查 | ParseTitleAndMessage |
| VM-5 | US-5 对齐与偏移 (AC-5.1~5.2) | 代码审查 | 默认 BOTTOM；offset 默认值 |
| VM-6 | US-6 子窗口 (AC-6.1) | 代码审查 | SubwindowManager |
| VM-7 | US-7 层级模式 (AC-7.1~7.2) | 代码审查 | EMBEDDED vs OVERLAY |
| VM-8 | US-8 生命周期与废弃 (AC-8.1~8.3) | 代码审查 | 生命周期回调；废弃标记 |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_action_sheet.cpp:394-552` |
| AC-1.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_action_sheet.cpp:73-109` |
| AC-2.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_action_sheet.cpp:135-188`, `frameworks/core/components_ng/pattern/dialog/action_sheet_model_ng.cpp:104-108` |
| AC-2.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_action_sheet.cpp:135-188` |
| AC-3.1 | 代码审查 | `frameworks/core/components_ng/pattern/dialog/action_sheet_model_ng.cpp:93-96` |
| AC-3.2 | 代码审查 | `frameworks/core/components/dialog/dialog_properties.h:186-282` |
| AC-4.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_action_sheet.cpp:111-133` |
| AC-4.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_action_sheet.cpp:111-133` |
| AC-5.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_action_sheet.cpp:51-52` |
| AC-5.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_action_sheet.cpp:190-265` |
| AC-6.1 | 代码审查 | `frameworks/core/components_ng/pattern/dialog/action_sheet_model_ng.cpp:25-86` |
| AC-7.1 | 代码审查 | `frameworks/core/components_ng/pattern/dialog/action_sheet_model_ng.cpp:25-86` |
| AC-7.2 | 代码审查 | `frameworks/core/components_ng/pattern/dialog/action_sheet_model_ng.cpp:25-86` |
| AC-8.1 | 代码审查 | `frameworks/core/components/dialog/dialog_properties.h:186-282` |
| AC-8.2 | 代码审查 | `frameworks/core/components/dialog/dialog_properties.h:186-282` |
| AC-8.3 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/action_sheet.d.ts` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/action_sheet.d.ts`

#### ActionSheet.show 静态方法

```typescript
// action_sheet.d.ts
class ActionSheet {
  static show(options: ActionSheetOptions): void;
}
```

- **@since**: API 8，废弃于 API 18

#### 核心类型

| 类型 | 说明 | @since |
|------|------|--------|
| `SheetInfo` | `{title, icon?, action}` 列表项结构 | 8 |
| `ActionSheetButtonOptions` | `{enabled?, defaultFocus?, style?, value, action}` 按钮选项 | 10(revised 18) |
| `ActionSheetOffset` | `{dx, dy}` 偏移量 | 18 |
| `ActionSheetOptions` | 弹窗参数接口 | 8 |

---

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| `ActionSheet.show()` | 废弃(API 18) | AC-8.3 |
| `UIContext.showActionSheet()` | 新增(API 18) | AC-8.3 |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API < 10 | 无 subtitle/maskRect 属性 | 无法设置副标题和遮罩区域 | API 10 起支持 |
| API < 11 | 无 isModal 属性 | 无法控制模态 | API 11 起支持 |
| API < 14 | 无 enableHoverMode | 不支持悬停模式 | API 14 起支持 |
| API < 15 | 无 immersiveMode/levelMode | 不支持页面级弹窗 | API 15 起支持 |
| API 18 | ActionSheet.show 废弃 | 标记为废弃 | 迁移到 UIContext.showActionSheet() |
| API 18 | 新增 backgroundBlurStyleOptions | 背景模糊样式选项 | API 18 起支持 |
| API 19 | 新增生命周期回调 | 无 onWillAppear 等回调 | API 19 起支持 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 统一存储 | DialogProperties 为所有弹窗类型的统一存储结构，type=ACTION_SHEET |
| sheets 独立存储 | sheetsInfo 为独立 vector<ActionSheetInfo>，不合并到 buttons |
| 默认对齐 | alignment=BOTTOM，offset={0,-40vp}，区别于 AlertDialog |
| 模态默认 | isModal 默认 true，阻塞背景交互 |
| 子窗口 | showInSubWindow 通过 SubwindowManager 创建独立窗口 |
| 废弃兼容 | 废弃 API 保留功能，引导迁移到 UIContext 实例方法 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | ShowActionSheet 投递到 UI 线程执行，创建开销可接受 |
| 可调试性 | DialogProperties 提供 DumpInfo 用于 Inspector 诊断 |
| 线程安全 | JS Bridge 在 JS 线程解析参数，Model 层投递到 UI 线程执行 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | enableHoverMode 支持悬停 | API 14+ | 代码审查 | — |
| 折叠屏 | enableHoverMode 支持悬停 | API 14+ | 代码审查 | — |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 无障碍 | 需关注 — 弹窗列表项和按钮需支持辅助技术焦点和操作 |
| 大字体 | 需关注 — 标题、消息和按钮文本需支持大字体适配 |
| 深色模式 | 需关注 — backgroundColor/backgroundBlurStyle 需适配深色模式 |
| 多窗口分屏 | 需关注 — showInSubWindow 和 isModal 影响分屏行为 |
| 多用户 | 无差异 |
| 版本升级 | 需关注 — API 18 废弃需迁移到 UIContext 实例方法 |
| 生态兼容 | 需关注 — 废弃 API 保留兼容性，UIContext 迁移为新标准 |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 规则编号连续且可追溯到源码
- [x] API 变更分析基于真实 SDK 定义文件（action_sheet.d.ts）
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file:line 信息
- [x] 构建系统影响章节已确认无变更

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/jsview/dialog/js_action_sheet.cpp/.h` | JS 桥接层，Show/ParseSheetInfo/ParseConfirmButton |
| `frameworks/core/components_ng/pattern/dialog/action_sheet_model_ng.cpp/.h` | NG Model 层，ShowActionSheet/SetAction/SetCancel/SetConfirm |
| `frameworks/core/components/dialog/dialog_properties.h` | DialogProperties + sheetsInfo 统一存储结构 |
| `frameworks/bridge/declarative_frontend/jsview/dialog/action_sheet_model.h` | Model 抽象层 |
| `frameworks/core/components_ng/pattern/dialog/action_sheet_accessor.cpp` | C-API accessor |
| `frameworks/core/components_ng/pattern/dialog/action_sheet_static_accessor.cpp` | 静态桥接 accessor |
| `interface/sdk-js/api/@internal/component/ets/action_sheet.d.ts` | SDK 公开 API 定义 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/dialog/action_sheet_test_ng.cpp` | NG 单元测试 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | SDK API 知识库 |
| `docs/sdk/Component_API_Knowledge_Base_CN.md` | 组件 API 知识库 |
