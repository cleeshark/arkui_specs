# 特性规格

> Func-05-06-02-Feat-01 AlertDialog 警告弹窗：固化 AlertDialog.show() 命令式 API 的三种按钮模式、对齐与 RTL、遮罩与模态、子窗口、层级模式、生命周期回调和废弃迁移的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | AlertDialog 警告弹窗 (Alert Dialog) |
| 特性编号 | Func-05-06-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 10 subtitle/buttonDirection/maskRect，API 11 isModal/backgroundBlurStyle，API 12 textStyle，API 14 enableHoverMode，API 15 immersiveMode/levelMode，API 18 levelOrder + 废弃，API 19 生命周期回调 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | AlertDialog 完整行为规格 | 补录三种按钮模式、对齐与 RTL、遮罩与模态、子窗口、层级模式、生命周期回调、废弃迁移 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/06-popup-components/02-alert-dialog/design.md` | Baselined |
| SDK API | `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | — |
| SDK 组件 | `docs/sdk/Component_API_Knowledge_Base_CN.md` | — |

---

## 用户故事

### US-1: 创建确认弹窗

**作为** 应用开发者,
**我想要** 使用 `AlertDialog.show({confirm})` 创建单按钮确认弹窗,
**以便** 向用户展示重要信息并获取确认。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `AlertDialog.show({message, confirm})` THEN 创建包含 1 个确认按钮的弹窗 | 正常 |
| AC-1.2 | WHEN confirm 未设置 THEN 弹窗不显示确认按钮 | 边界 |
| AC-1.3 | WHEN confirm.action 被调用 THEN 按钮点击后执行回调并关闭弹窗 | 正常 |

### US-2: 创建双按钮弹窗

**作为** 应用开发者,
**我想要** 使用 `AlertDialog.show({primaryButton, secondaryButton})` 创建双按钮弹窗,
**以便** 提供主/次两种操作选项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `AlertDialog.show({primaryButton, secondaryButton})` THEN 创建包含 2 个按钮的弹窗 | 正常 |
| AC-2.2 | WHEN primaryButton.defaultFocus=false THEN 该按钮 isPrimary=true | 边界 |
| AC-2.3 | WHEN 按钮设置 enabled=false THEN 该按钮不可点击 | 正常 |

### US-3: 创建多按钮弹窗

**作为** 应用开发者,
**我想要** 使用 `AlertDialog.show({buttons, buttonDirection})` 创建多按钮弹窗,
**以便** 提供两个以上的操作选项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `AlertDialog.show({buttons: [...]})` THEN 创建包含 N 个按钮的弹窗 | 正常 |
| AC-3.2 | WHEN buttonDirection=AUTO THEN 按钮方向自动布局 | 正常 |
| AC-3.3 | WHEN buttonDirection=HORIZONTAL/VERTICAL THEN 按钮水平/垂直排列 | 正常 |

### US-4: 对齐方式与 RTL

**作为** 应用开发者,
**我想要** 设置弹窗对齐方式并支持 RTL 镜像,
**以便** 控制弹窗在屏幕中的位置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 alignment THEN 弹窗按指定位置展示（Top/Center/Bottom/Default 及 Start/End 变体） | 正常 |
| AC-4.2 | WHEN RTL 模式 THEN UpdateAlertAlignment 交换 TopStart<->TopEnd、CenterStart<->CenterEnd、BottomStart<->BottomEnd | 边界 |

### US-5: 遮罩与模态

**作为** 应用开发者,
**我想要** 控制弹窗的遮罩和模态行为,
**以便** 控制弹窗是否阻塞背景交互。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN isModal=true（默认）THEN 显示遮罩并阻塞背景交互 | 正常 |
| AC-5.2 | WHEN maskRect 被设置 THEN 遮罩区域限定为指定矩形 | 边界 |

### US-6: 子窗口显示

**作为** 应用开发者,
**我想要** 通过 showInSubWindow 在子窗口中展示弹窗,
**以便** 实现独立窗口的弹窗。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN showInSubWindow=true THEN 通过 SubwindowManager 创建子窗口展示弹窗 | 正常 |

### US-7: 层级模式

**作为** 应用开发者,
**我想要** 通过 levelMode 控制弹窗层级,
**以便** 区分全局弹窗和页面级弹窗。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN levelMode=OVERLAY（默认）THEN 通过 DialogManager 创建全局弹窗 | 正常 |
| AC-7.2 | WHEN levelMode=EMBEDDED THEN 通过 DialogManager::GetEmbeddedOverlay 创建页面级弹窗 | 正常 |

### US-8: 生命周期回调

**作为** 应用开发者,
**我想要** 监听弹窗的生命周期事件,
**以便** 在弹窗出现/消失时执行业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 弹窗即将出现 THEN onWillAppear 回调被触发 (API 19+) | 正常 |
| AC-8.2 | WHEN 弹窗已出现 THEN onDidAppear 回调被触发 (API 19+) | 正常 |
| AC-8.3 | WHEN 弹窗即将消失 THEN onWillDisappear/onDidDisappear 回调被触发 (API 19+) | 正常 |

### US-9: 废弃迁移与按钮样式

**作为** 应用开发者,
**我想要** 了解废弃迁移路径和按钮样式优先级,
**以便** 迁移到新 API 并控制按钮外观。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN API >= 18 调用 AlertDialog.show THEN 标记为废弃，建议使用 UIContext.showAlertDialog() | 边界 |
| AC-9.2 | WHEN 按钮设置 fontColor+backgroundColor THEN 样式优先级高于 style 和 defaultFocus | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1, R-2 | 代码审查 js_alert_dialog.cpp:189-239, 458-590 |
| AC-1.2 | US-1 | R-3 | 代码审查 js_alert_dialog.cpp:189-215 |
| AC-1.3 | US-1 | R-4 | 代码审查 js_alert_dialog.cpp:189-215 |
| AC-2.1 | US-2 | R-5 | 代码审查 js_alert_dialog.cpp:189-215, 458-590 |
| AC-2.2 | US-2 | R-6 | 代码审查 js_alert_dialog.cpp:189-215 |
| AC-2.3 | US-2 | R-7 | 代码审查 js_alert_dialog.cpp:189-215 |
| AC-3.1 | US-3 | R-5 | 代码审查 js_alert_dialog.cpp:189-215 |
| AC-3.2 | US-3 | R-8 | 代码审查 dialog_properties.h:186-282 |
| AC-3.3 | US-3 | R-8 | 代码审查 dialog_properties.h:186-282 |
| AC-4.1 | US-4 | R-9 | 代码审查 js_alert_dialog.cpp:307-318 |
| AC-4.2 | US-4 | R-10 | 代码审查 js_alert_dialog.cpp:307-318 |
| AC-5.1 | US-5 | R-11 | 代码审查 alert_dialog_model_ng.cpp:47-105 |
| AC-5.2 | US-5 | R-12 | 代码审查 js_alert_dialog.cpp:357-370 |
| AC-6.1 | US-6 | R-13 | 代码审查 alert_dialog_model_ng.cpp:47-105 |
| AC-7.1 | US-7 | R-14 | 代码审查 alert_dialog_model_ng.cpp:47-105 |
| AC-7.2 | US-7 | R-14 | 代码审查 alert_dialog_model_ng.cpp:47-105 |
| AC-8.1 | US-8 | R-15 | 代码审查 dialog_properties.h:186-282 |
| AC-8.2 | US-8 | R-15 | 代码审查 dialog_properties.h:186-282 |
| AC-8.3 | US-8 | R-15 | 代码审查 dialog_properties.h:186-282 |
| AC-9.1 | US-9 | R-16 | 代码审查 alert_dialog.d.ts |
| AC-9.2 | US-9 | R-17 | 代码审查 js_alert_dialog.cpp:189-215 |

---

## 规则定义

> **统一规则表。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `js_alert_dialog.cpp:458-590` | JSAlertDialog::Show 创建 DialogProperties{type=ALERT_DIALOG, isAlertDialog=true} | — | AC-1.1 |
| R-2 | 行为 | `js_alert_dialog.cpp:217-239` | 解析 title/subtitle/message 存入 DialogProperties | — | AC-1.1 |
| R-3 | 边界 | `js_alert_dialog.cpp:189-215` | confirm 模式下 buttons 数组仅 1 个元素 | — | AC-1.2 |
| R-4 | 行为 | `js_alert_dialog.cpp:189-215` | confirm.action 在按钮点击后执行并关闭弹窗 | — | AC-1.3 |
| R-5 | 行为 | `js_alert_dialog.cpp:189-215` | primary+secondary 和 buttons array 模式最终都转换为 buttons 数组 | — | AC-2.1, AC-3.1 |
| R-6 | 边界 | `js_alert_dialog.cpp:189-215` | primaryButton.defaultFocus=false 时 isPrimary=true | — | AC-2.2 |
| R-7 | 行为 | `js_alert_dialog.cpp:189-215` | 按钮 enabled=false 时不可点击 | — | AC-2.3 |
| R-8 | 行为 | `dialog_properties.h:186-282` | buttonDirection 默认 AUTO，可选 HORIZONTAL/VERTICAL | — | AC-3.2, AC-3.3 |
| R-9 | 行为 | `js_alert_dialog.cpp:307-318` | alignment 解析并设置到 DialogProperties | — | AC-4.1 |
| R-10 | 边界 | `js_alert_dialog.cpp:307-318` | RTL 下 UpdateAlertAlignment 交换 Start/End 变体 | — | AC-4.2 |
| R-11 | 行为 | `alert_dialog_model_ng.cpp:47-105` | isModal=true 时创建遮罩阻塞背景交互 | — | AC-5.1 |
| R-12 | 边界 | `js_alert_dialog.cpp:357-370` | maskRect 限定遮罩区域为指定矩形 | — | AC-5.2 |
| R-13 | 行为 | `alert_dialog_model_ng.cpp:47-105` | showInSubWindow=true 时通过 SubwindowManager 创建子窗口 | — | AC-6.1 |
| R-14 | 行为 | `alert_dialog_model_ng.cpp:47-105` | levelMode=OVERLAY→全局弹窗，EMBEDDED→页面级弹窗 | — | AC-7.1, AC-7.2 |
| R-15 | 行为 | `dialog_properties.h:186-282` | onWillAppear/onDidAppear/onWillDisappear/onDidDisappear 生命周期回调 | — | AC-8.1~8.3 |
| R-16 | 边界 | `alert_dialog.d.ts` | API 18 起废弃 AlertDialog.show，建议迁移到 UIContext.showAlertDialog() | — | AC-9.1 |
| R-17 | 行为 | `js_alert_dialog.cpp:189-215` | 按钮样式优先级：fontColor+backgroundColor > style > defaultFocus | — | AC-9.2 |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 确认弹窗 (AC-1.1~1.3) | 代码审查 | confirm 模式解析；单按钮创建 |
| VM-2 | US-2 双按钮 (AC-2.1~2.3) | 代码审查 | primary+secondary 模式；isPrimary 逻辑 |
| VM-3 | US-3 多按钮 (AC-3.1~3.3) | 代码审查 | buttons 数组；buttonDirection 布局 |
| VM-4 | US-4 对齐与 RTL (AC-4.1~4.2) | 代码审查 | alignment 解析；RTL 镜像 |
| VM-5 | US-5 遮罩与模态 (AC-5.1~5.2) | 代码审查 | isModal 默认值；maskRect 限定 |
| VM-6 | US-6 子窗口 (AC-6.1) | 代码审查 | SubwindowManager 创建子窗口 |
| VM-7 | US-7 层级模式 (AC-7.1~7.2) | 代码审查 | OVERLAY vs EMBEDDED |
| VM-8 | US-8 生命周期 (AC-8.1~8.3) | 代码审查 | onWillAppear/onDidAppear/onWillDisappear/onDidDisappear |
| VM-9 | US-9 废弃迁移与样式 (AC-9.1~9.2) | 代码审查 | 废弃标记；样式优先级 |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp:189-239, 458-590` |
| AC-1.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp:189-215` |
| AC-1.3 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp:189-215` |
| AC-2.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp:189-215, 458-590` |
| AC-2.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp:189-215` |
| AC-2.3 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp:189-215` |
| AC-3.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp:189-215` |
| AC-3.2 | 代码审查 | `frameworks/core/components/dialog/dialog_properties.h:186-282` |
| AC-3.3 | 代码审查 | `frameworks/core/components/dialog/dialog_properties.h:186-282` |
| AC-4.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp:307-318` |
| AC-4.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp:307-318` |
| AC-5.1 | 代码审查 | `frameworks/core/components_ng/pattern/dialog/alert_dialog_model_ng.cpp:47-105` |
| AC-5.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp:357-370` |
| AC-6.1 | 代码审查 | `frameworks/core/components_ng/pattern/dialog/alert_dialog_model_ng.cpp:47-105` |
| AC-7.1 | 代码审查 | `frameworks/core/components_ng/pattern/dialog/alert_dialog_model_ng.cpp:47-105` |
| AC-7.2 | 代码审查 | `frameworks/core/components_ng/pattern/dialog/alert_dialog_model_ng.cpp:47-105` |
| AC-8.1 | 代码审查 | `frameworks/core/components/dialog/dialog_properties.h:186-282` |
| AC-8.2 | 代码审查 | `frameworks/core/components/dialog/dialog_properties.h:186-282` |
| AC-8.3 | 代码审查 | `frameworks/core/components/dialog/dialog_properties.h:186-282` |
| AC-9.1 | 代码审查 | `interface/sdk-js/api/@internal/component/ets/alert_dialog.d.ts` |
| AC-9.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp:189-215` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/alert_dialog.d.ts`

#### AlertDialog.show 静态方法

```typescript
// alert_dialog.d.ts
class AlertDialog {
  static show(options: AlertDialogParamWithConfirm | AlertDialogParamWithButtons | AlertDialogParamWithOptions): void;
}
```

- **@since**: API 7，废弃于 API 18

#### 核心类型

| 类型 | 说明 | @since |
|------|------|--------|
| `DialogAlignment` | Top/Center/Bottom/Default + Start/End 变体 | 7/8 |
| `DialogButtonDirection` | AUTO=0/HORIZONTAL=1/VERTICAL=2 | 10 |
| `AlertDialogParam` | 基础参数接口 | 7 |
| `AlertDialogParamWithConfirm` | 确认弹窗参数 | 7 |
| `AlertDialogParamWithButtons` | 双按钮弹窗参数 | 7 |
| `AlertDialogParamWithOptions` | 多按钮弹窗参数 | 10 |
| `AlertDialogButtonBaseOptions` | 按钮基础选项 | 10(revised 18) |
| `AlertDialogButtonOptions` | 按钮选项（含 primary） | 12 |

---

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| `AlertDialog.show()` | 废弃(API 18) | AC-9.1 |
| `UIContext.showAlertDialog()` | 新增(API 18) | AC-9.1 |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API < 10 | 无 subtitle/maskRect/buttonDirection 属性 | 无法设置副标题、遮罩区域和按钮方向 | API 10 起支持 |
| API < 11 | 无 isModal/backgroundBlurStyle | 无法控制模态和背景模糊 | API 11 起支持 |
| API < 12 | 无 textStyle | 无法设置文本样式 | API 12 起支持 |
| API < 14 | 无 enableHoverMode | 不支持悬停模式 | API 14 起支持 |
| API < 15 | 无 immersiveMode/levelMode | 不支持页面级弹窗 | API 15 起支持 |
| API 18 | AlertDialog.show 废弃 | 标记为废弃 | 迁移到 UIContext.showAlertDialog() |
| API 19 | 新增生命周期回调 | 无 onWillAppear 等回调 | API 19 起支持 |
| API < 20 | title 左对齐 | 标题左对齐 | API 20 起居中对齐 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 统一存储 | DialogProperties 为所有弹窗类型的统一存储结构，type=ALERT_DIALOG |
| 按钮模式 | 三种按钮模式最终都转换为 buttons 数组 |
| 层级模式 | OVERLAY（全局）与 EMBEDDED（页面级）通过 levelMode 区分 |
| 模态默认 | isModal 默认 true，阻塞背景交互 |
| 子窗口 | showInSubWindow 通过 SubwindowManager 创建独立窗口 |
| 废弃兼容 | 废弃 API 保留功能，引导迁移到 UIContext 实例方法 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | SetShowDialog 投递到 UI 线程执行，创建开销可接受 |
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
| 无障碍 | 需关注 — 弹窗按钮需支持辅助技术焦点和操作 |
| 大字体 | 需关注 — 按钮文本和消息需支持大字体适配 |
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
- [x] API 变更分析基于真实 SDK 定义文件（alert_dialog.d.ts）
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file:line 信息
- [x] 构建系统影响章节已确认无变更

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/jsview/dialog/js_alert_dialog.cpp/.h` | JS 桥接层，Show 解析和参数构造 |
| `frameworks/core/components_ng/pattern/dialog/alert_dialog_model_ng.cpp/.h` | NG Model 层，SetShowDialog 实现 |
| `frameworks/core/components/dialog/dialog_properties.h` | DialogProperties 统一存储结构 |
| `frameworks/bridge/declarative_frontend/jsview/dialog/alert_dialog_model.h` | Model 抽象层 |
| `frameworks/core/components_ng/pattern/dialog/alert_dialog_accessor.cpp` | C-API accessor |
| `frameworks/core/components_ng/pattern/dialog/alert_dialog_static_accessor.cpp` | 静态桥接 accessor |
| `interface/sdk-js/api/@internal/component/ets/alert_dialog.d.ts` | SDK 公开 API 定义 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/dialog/alert_dialog_test_ng.cpp` | NG 单元测试 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | SDK API 知识库 |
| `docs/sdk/Component_API_Knowledge_Base_CN.md` | 组件 API 知识库 |
