# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | CalendarPickerDialog 完整能力 |
| 特性编号 | Func-05-06-05-Feat-01 |
| FuncID | 05-06-05 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | Dynamic API 10+ / Static API 23+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |
| lineage | new-on-legacy（已有实现规格补录） |

## 本次变更范围（Delta）

> 本文档补录现有实现，不修改产品行为。

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | CalendarPickerDialog 完整 options 和事件 | 存量能力补录 |
| MODIFIED | API 版本扩展与迁移 | 按 SDK @since/deprecated |

## 输入文档

- **设计文档**: `05-ui-components/06-popup-components/05-calendar-picker-dialog/design.md`
- **SDK 类型定义**:
  - `interface/sdk-js/api/@internal/component/ets/calendar_picker.d.ts`
  - `interface/sdk-js/api/arkui/component/calendarPicker.static.d.ets`
- **实现证据**:
  - `frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:296`
  - `frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:734`
  - `frameworks/core/components_ng/pattern/calendar_picker/bridge/calendar_picker_dialog_static_modifier.cpp:183`
  - `frameworks/core/components_ng/pattern/calendar_picker/calendar_dialog_view.cpp:1195`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md；本特性为存量能力补录，无独立 proposal.md。

## 用户故事

### US-1: 配置并显示弹窗

**角色**: 应用开发者  
**期望**: 使用 CalendarPickerDialog 配置完整数据、样式和弹窗行为  
**价值**: 获得标准选择交互

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN调用 CalendarPickerDialog.show 或对应 UIContext API 并传入合法 options THEN创建并显示选择弹窗 | 正常 |
| AC-1.2 | WHEN设置数据选项 hintRadius, selected, start, end, disabledDateRange, markToday THEN按 SDK 默认值、范围和优先级初始化选择器 | 正常 |
| AC-1.3 | WHEN设置弹窗和样式选项 backgroundColor, backgroundBlurStyle, backgroundBlurStyleOptions, backgroundEffect, acceptButtonStyle, cancelButtonStyle, shadow, enableHoverMode, hoverModeArea, systemMaterial, distortionMode, edgeLightMode THEN转换为 DialogProperties/SettingData/ButtonInfo | 正常 |

### US-2: 接收事件并处理版本迁移

**角色**: 应用开发者  
**期望**: 接收选择与生命周期事件并使用正确 UI 实例  
**价值**: 保持行为和实例归属可预测

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN用户选择、确认或取消 THEN分别触发 onAccept, onCancel, onChange, onWillAppear, onDidAppear | 正常 |
| AC-2.2 | WHEN弹窗正常显示和消失 THEN生命周期顺序为 onWillAppear、onDidAppear、交互事件、onWillDisappear、onDidDisappear | 正常 |
| AC-2.3 | WHEN selected/start/end 超出 Date('0001-01-01') 到 Date('5000-12-31') 或 disabledDateRange 无效 THEN按 SDK 默认值或忽略无效区间 | 异常 |
| AC-2.4 | WHEN使用 Static ArkTS CalendarPickerDialog.show THEN经 generated accessor 在 UI 线程提交 ShowCalendarDialog；当前无 UIContext 等价 API | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1 | R-1 | TASK-050605-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:296<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:734<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/calendar_picker_dialog_static_modifier.cpp:183 |
| AC-1.2 | R-1 | TASK-050605-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:296<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:734<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/calendar_picker_dialog_static_modifier.cpp:183 |
| AC-1.3 | R-1, R-3 | TASK-050605-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:296<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:734<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/calendar_picker_dialog_static_modifier.cpp:183 |
| AC-2.1 | R-2 | TASK-050605-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:296<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:734<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/calendar_picker_dialog_static_modifier.cpp:183 |
| AC-2.2 | R-2 | TASK-050605-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:296<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:734<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/calendar_picker_dialog_static_modifier.cpp:183 |
| AC-2.3 | R-3 | TASK-050605-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:296<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:734<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/calendar_picker_dialog_static_modifier.cpp:183 |
| AC-2.4 | R-4 | TASK-050605-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:296<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:734<br>frameworks/core/components_ng/pattern/calendar_picker/bridge/calendar_picker_dialog_static_modifier.cpp:183 |

## 规则定义

> 类型标签：行为、边界、异常、恢复。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 合法 options | Bridge/Accessor 将 options 转为 DialogProperties、SettingData、事件和 ButtonInfo 后调用 Model/Overlay | 所有字段以 SDK 声明为准 | AC-1.1, AC-1.2, AC-1.3 |
| R-2 | 行为 | 用户交互或生命周期阶段到达 | 触发已注册回调 | 回调未配置时不调用 | AC-2.1, AC-2.2 |
| R-3 | 边界 | 按钮 primary 冲突或 picker 专有边界条件出现 | 按 SDK 定义忽略冲突值、采用优先级或关闭相关行为 | 最多一个 primary=true；具体 picker 边界见 AC-2.3 | AC-1.3, AC-2.3 |
| R-4 | 边界 | API/前端版本不同 | 按 Dynamic/Static SDK 声明选择入口和可用字段 | generated accessor 不是公开 NDK API | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1 ~ AC-1.3 | 定向 UT/预览用例 + 源码审查 | 配置并显示弹窗 |
| VM-2 | AC-2.1 ~ AC-2.4 | 定向 UT/预览用例 + 源码审查 | 接收事件并处理版本迁移 |

## API 变更分析

### 新增 API

> 本次不新增 API；下表记录本特性的现有开放面。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| CalendarPickerDialog.show | Public | CalendarPickerDialogOptions | void | N/A | 显示选择弹窗 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| CalendarPickerDialog.show | 无 | CalendarPickerDialog 仍保留全局入口 | 当前无 UIContext 对应方法 | AC-2.4 |

## 接口规格

### 接口定义

**CalendarPickerDialog.show**

| 属性 | 值 |
|---|---|
| 函数签名 | `static show(options?: CalendarPickerDialogOptions): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| options | CalendarPickerDialogOptions | 否 | {} | 覆盖全部数据、样式、事件和生命周期字段 |
| 数据字段 | 组合类型 | 否 | SDK 默认值 | hintRadius, selected, start, end, disabledDateRange, markToday |
| 样式/弹窗字段 | 组合类型 | 否 | 主题默认值 | backgroundColor, backgroundBlurStyle, backgroundBlurStyleOptions, backgroundEffect, acceptButtonStyle, cancelButtonStyle, shadow, enableHoverMode, hoverModeArea, systemMaterial, distortionMode, edgeLightMode |
| 事件字段 | Callback | 否 | 无 | onAccept, onCancel, onChange, onWillAppear, onDidAppear, onWillDisappear, onDidDisappear |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 合法 options | 显示弹窗 | AC-1.1 |
| 2 | 选择/确认/取消 | 触发对应事件 | AC-2.1 |
| 3 | 生命周期变化 | 按顺序触发 | AC-2.2 |
| 4 | 版本边界 | 使用对应入口 | AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 是；字段按 @since 增量开放，CalendarPickerDialog 无 UIContext 等价入口
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** Dynamic API 10+ / Static API 23+
- **API 版本号策略:** Dynamic 按组件 d.ts；Static API 23+；内部 generated accessor 不作为 NDK

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 前端收敛 | Dynamic Bridge 和 Static Extender/Accessor 最终进入 Model/DialogView/Overlay | AC-1.1 |
| 事件转换 | ArkTS Callback 转换为 std::function 后由弹窗节点触发 | AC-2.1, AC-2.2 |
| 接口边界 | generated accessor 仅供 Static 前端，不是公开 NDK API | AC-2.4 |

> 架构规则适用性及调用链见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 无新增指标；沿用现有 Overlay/DialogView | 源码审查 | frameworks/core/components_ng/pattern/calendar_picker/calendar_dialog_view.cpp:1195 |
| 功耗 | 无后台任务；仅在弹窗显示期间参与布局和绘制 | 源码审查 | CalendarDialogView |
| 内存 | 关闭后由 OverlayManager 释放节点 | 节点树检查 | DialogView |
| 安全 | 无新增权限要求 | SDK 审查 | calendar_picker.d.ts |
| 可靠性 | 非法可选字段按现有默认值/忽略处理 | 边界用例 | Bridge converter |
| 可测试性 | options 和回调可通过 previewer/UT 验证 | 定向用例 | dialog tests |
| 自动化维测 | 选择事件可被回调观测 | 事件用例 | Model callbacks |
| 定界定位 | 节点树和日志沿用 Dialog 能力 | Dump/hilog | OverlayManager |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | hoverMode 在半折叠设备按 enableHoverMode/hoverModeArea 生效 | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 平板 | hoverMode 在半折叠设备按 enableHoverMode/hoverModeArea 生效 | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 折叠屏 | hoverMode 在半折叠设备按 enableHoverMode/hoverModeArea 生效 | 涉及 hover 时按 SDK 配置 | 折叠屏验证 | SDK options 定义 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | 沿用组件/图像现有无障碍语义 | 主路径 |
| 大字体 | 是 | 文本和弹窗样式沿用系统字体缩放；固定按钮高度以 SDK 声明为准 | 样式验证 |
| 深色模式 | 是 | ResourceColor/主题资源随主题切换 | 主题验证 |
| 多窗口/分屏 | 是 | 布局受当前窗口约束 | 窗口尺寸变化 |
| 多用户 | 否 | 无用户态持久化 | N/A |
| 版本升级 | 是 | 全局与 UIContext 入口、Dynamic/Static 字段版本需要兼容 | 兼容性矩阵 |
| 生态兼容 | 是 | Dynamic/Static 声明按各自 API 版本保持一致 | 双前端审查 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: CalendarPickerDialog 完整能力
  Scenario: 主路径
    Given 当前运行环境满足对应 API、资源和平台前置条件
    When 调用 CalendarPickerDialog.show 或对应 UIContext API 并传入合法 options
    Then 创建并显示选择弹窗
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "CalendarPickerDialog options callback bridge"
  - repo: "openharmony/ace_engine"
    query: "CalendarPickerDialog Model DialogView OverlayManager"
```

**关键文档:**
- `interface/sdk-js/api/@internal/component/ets/calendar_picker.d.ts`
- `interface/sdk-js/api/arkui/component/calendarPicker.static.d.ets`
- `frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:296`
- `frameworks/core/components_ng/pattern/calendar_picker/bridge/arkts_native_calendar_picker_dialog_bridge.cpp:734`
- `frameworks/core/components_ng/pattern/calendar_picker/bridge/calendar_picker_dialog_static_modifier.cpp:183`
