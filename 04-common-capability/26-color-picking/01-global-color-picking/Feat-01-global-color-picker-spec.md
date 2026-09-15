# 特性规格

> Func-04-26-01-Feat-01 全局取色器（colorPickerController）取色全流程规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 全局取色器（colorPickerController） |
| 特性编号 | Func-04-26-01-Feat-01 |
| 所属 Epic | FEAT-COLORPICKER / 20260807938436 |
| 优先级 | P1 |
| 目标版本 | OpenHarmony-7.1（@since 26.2.0） |
| SIG 归属 | ArkUI SIG + API SIG |
| 状态 | Draft |
| 复杂度 | 中等（5 人月） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | NAPI 绑定模块 | 新建 `eyedropper_picker` 目录，导出 `colorPickerController` 命名空间，实现参数校验与 Promise |
| ADDED | 取色 Service | 新建 `ColorPickerService`，管理 Subwindow、截图获取、像素读取、Promise resolve/reject |
| ADDED | 圆环 UI Pattern | 新建 `ColorPickerRingPattern`，实现圆环渲染、触摸跟随、RGB 显示 |
| ADDED | C/NDK API | `OH_ArkUI_ColorPickerController_PickForResult` + `ArkUI_PickedColorInfo` + `ArkUI_PickForResultCallback` |
| ADDED | 文档 | docs PR #162671 新增 `js-apis-arkui-graphics.md` 和 `capi-arkui-nativemodule-arkui-colorPickerController.md` |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/26-color-picking/01-global-color-picking/design.md` | 已核对 |
| design-docs proposal | `codespec/changes/arkui_ace_engine/20260807938436/proposal.md` | Approved |
| design-docs spec-for-validation | `codespec/changes/arkui_ace_engine/20260807938436/spec-for-validation.md` | Approved |
| d.ts | `interface/sdk-js/api/@ohos.arkui.colorPickerController.d.ts:1-132` | 已声明 |
| 文档 PR | [openharmony/docs#162671](https://gitcode.com/openharmony/docs/pull/162671) | open |

## 用户故事

### US-1: 启动取色并显示取色圆环

**作为** ArkUI 应用开发者
**我想要** 调用全局取色 API 启动取色并看到取色圆环 UI
**以便** 在屏幕上实时选取颜色

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 应用已获取截屏权限 AND 调用 `colorPickerController.pickForResult(x, y)` THEN 屏幕指定位置 `(x, y)` 出现取色圆环 UI，圆环跟随触摸/触控笔移动 | 正常 |
| AC-1.2 | WHEN `pickForResult` 未传入 `x`/`y` THEN 圆环出现在默认位置 `(100, 100)` px | 边界 |
| AC-1.3 | WHEN `showValue=true` AND 取色进行中 THEN 圆环 UI 实时显示当前触点 RGB 值 | 正常 |
| AC-1.4 | WHEN `showValue=false`（或未传入） AND 取色进行中 THEN 圆环 UI 不显示 RGB 值 | 正常 |

### US-2: 获取触点颜色值

**作为** ArkUI 应用开发者
**我想要** 获取触点位置的颜色值（RGB，Alpha=1）
**以便** 精确读取屏幕像素颜色

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 取色圆环已显示 AND 用户抬起手指/触控笔 THEN `pickForResult` 的 Promise resolve 为 `PickedColorInfo` 对象，其中 `color` 为触点像素 RGB 值，Alpha 固定为 1 | 正常 |
| AC-2.2 | WHEN 触点像素为 HDR 内容 AND 用户抬起 THEN `PickedColorInfo.brightness` 返回亮度值（nit），非 HDR 时 `brightness` 为 0 或 undefined | 边界 |
| AC-2.3 | WHEN `pickForResult` 返回 THEN 检查 `PickedColorInfo.colorSpace` 返回截屏像素对应的色彩空间 | 正常 |
| AC-2.4 | WHEN `pickForResult` 返回 THEN 检查 `PickedColorInfo.timestamp` 返回取色时刻的系统启动时间（ms） | 正常 |

### US-3: 截图遮盖底图，视频音频不暂停

**作为** ArkUI 应用开发者
**我想要** 取色时截图遮盖底图但不暂停视频音频
**以便** 正常使用取色功能

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 取色启动 AND 截图获取成功 THEN 全屏截图作为遮盖底图显示，取色圆环叠加于截图之上 | 正常 |
| AC-3.2 | WHEN 取色进行中 AND 底层有视频/音频播放 THEN 视频音频不暂停，仅视觉被截图遮盖 | 正常 |
| AC-3.3 | WHEN 取色结束 AND 圆环和遮盖消失 THEN 截图 PixelMap 立即释放，不持久化存储，不传输到应用层 | 恢复 |

### US-4: 取色性能达到业界主流水平

**作为** 平台开发者
**我想要** 取色性能达到业界主流水平
**以便** 不影响用户体验

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 取色进行中 AND 用户移动手指/触控笔 THEN 圆环跟随延迟≤业界基线值，无卡顿 | 非功能 |

### US-5: 接口定义完整含参数约束和错误码

**作为** 应用开发者
**我想要** JS 和 CPP 接口定义完整含参数约束和错误码
**以便** 正确集成

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN `pickForResult` 参数类型正确 THEN 正常启动取色 | 正常 |
| AC-5.2 | WHEN `pickForResult` 参数类型错误（如 `x` 传入字符串） THEN 抛出 `BusinessError` 401（参数错误） | 异常 |
| AC-5.3 | WHEN 设备不支持触摸/触控笔 AND 调用 `pickForResult` THEN 抛出 `BusinessError` 801（设备不支持） | 异常 |

### US-6: 截图获取失败容错

**作为** 应用开发者
**我想要** 截图获取失败时取色 API 返回错误码不崩溃
**以便** 应用稳定运行

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN `TakeSurfaceCapture` 调用失败 AND 取色启动 THEN `pickForResult` 的 Promise reject，返回错误码，圆环不显示，应用不崩溃 | 异常 |

### US-7: 权限未授予容错

**作为** 应用开发者
**我想要** 取色权限未授予时 API 返回权限错误
**以便** 正确处理权限缺失场景

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-7.1 | WHEN 应用未获取截屏权限 AND 调用 `pickForResult` THEN `pickForResult` 的 Promise reject，返回权限错误码，不崩溃 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1~AC-1.4 | BR-1, BR-3 | TASK-002, TASK-003 | 集成测试 | Pending |
| AC-2.1~AC-2.4 | BR-2, BR-6 | TASK-002, TASK-003 | 集成测试 | Pending |
| AC-3.1~AC-3.3 | BR-4, BR-5, BR-8 | TASK-003 | 集成测试 | Pending |
| AC-4.1 | NFR-1 | TASK-003 | 性能测试 | Pending |
| AC-5.1~AC-5.3 | BR-7 | TASK-001 | 单元测试 | Pending |
| AC-6.1 | BR-7, EX-4 | TASK-003 | 集成测试 | Pending |
| AC-7.1 | BR-7, EX-3 | TASK-001, TASK-003 | 集成测试 | Pending |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| BR-1 | 行为 | 调用 `pickForResult(x?, y?, showValue?)` | 启动取色，显示圆环 UI，返回 `Promise<PickedColorInfo>` | `x`/`y` 为 `number`（px），默认 100；`showValue` 为 boolean，默认 false | AC-1.1~1.4, AC-5.1 |
| BR-2 | 行为 | 取色完成返回结果 | `PickedColorInfo` 含 `color`/`colorSpace`/`timestamp`/`brightness?` | `color` Alpha 固定为 1 | AC-2.1~2.4 |
| BR-3 | 行为 | 取色圆环 UI 承载 | 通过 SubwindowManager 创建 subwindow | `SubwindowType::TYPE_SYSTEM_TOP_MOST_TOAST` | AC-1.1, AC-3.1 |
| BR-4 | 行为 | 获取全屏截图 | 通过 `TakeSurfaceCaptureWithAllWindows` | 支持 SDR+HDR | AC-3.1, AC-2.2 |
| BR-5 | 恢复 | 截图 PixelMap 生命周期 | 取色完成后立即释放 | 不持久化、不传输到应用层 | AC-3.3 |
| BR-6 | 行为 | 像素值读取 | 直接从截图 PixelMap 读取触点坐标像素 | 非使用 effectKit ColorPicker；Alpha 固定为 1 | AC-2.1 |
| BR-7 | 异常 | 错误码 | 401=参数错误、801=设备不支持；截图/权限失败返回对应 BusinessError | d.ts 已声明 | AC-5.2, AC-5.3, AC-6.1, AC-7.1 |
| BR-8 | 行为 | 截图遮盖底图 | 底层视频/音频不暂停 | 仅视觉遮盖 | AC-3.2 |

## 异常与边界规则

| 编号 | 场景 | 触发条件 | 系统行为 | 关联 AC |
|------|------|----------|----------|---------|
| EX-1 | `pickForResult` 参数类型错误 | `x`/`y` 非 `number`，`showValue` 非 boolean | 抛出 `BusinessError` 401 | AC-5.2 |
| EX-2 | 设备不支持触摸/触控笔 | 非触摸/触控笔设备 | 抛出 `BusinessError` 801 | AC-5.3 |
| EX-3 | 截屏权限未授予 | 应用无截屏权限 | Promise reject，返回权限错误码 | AC-7.1 |
| EX-4 | `TakeSurfaceCapture` 失败 | RenderService 截屏调用失败 | Promise reject，返回截图失败错误码，圆环不显示 | AC-6.1 |
| EX-5 | 取色中应用被切到后台 | 系统将应用切后台 | 取色取消，截图释放，Promise reject | AC-3.3 |
| EX-6 | `x`/`y` 超出屏幕范围 | 坐标值超过实际屏幕宽/高 | 使用实际屏幕宽/高钳制 | AC-1.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | 集成测试 | 圆环显示、跟随、默认位置、showValue 显示/隐藏 |
| VM-2 | AC-2.1~AC-2.4 | 集成测试 | RGB 值准确、Alpha=1、HDR brightness、colorSpace、timestamp |
| VM-3 | AC-3.1~AC-3.3 | 集成测试 | 截图遮盖、视频不暂停、PixelMap 释放 |
| VM-4 | AC-4.1 | 性能测试 | 圆环跟随延迟≤业界基线值 |
| VM-5 | AC-5.1~AC-5.3 | 单元测试 | 参数正确启动、参数错误 401、设备不支持 801 |
| VM-6 | AC-6.1 | 集成测试 | 截图失败 reject、不崩溃 |
| VM-7 | AC-7.1 | 集成测试 | 无权限 reject、不崩溃 |

## API 变更分析

### 新增 API

**ArkTS（d.ts 已声明）**

| 属性 | 值 |
|------|-----|
| 命名空间 | `colorPickerController` |
| 函数签名 | `pickForResult(x?: number, y?: number, showValue?: boolean): Promise<PickedColorInfo>` |
| 返回值 | `Promise<PickedColorInfo>` |
| 开放范围 | Public |
| @since | 26.2.0 |
| 系统能力 | SystemCapability.ArkUI.ArkUI.Full |
| 原子化服务 | 从 26.2.0 起支持 |
| 错误码 | 401（参数错误）、801（设备不支持） |
| 关联 AC | AC-1.1~1.4, AC-2.1~2.4, AC-5.1~5.3 |

**PickedColorInfo 接口**

| 属性 | 值 |
|------|-----|
| color | `common2D.Color`（RGB，Alpha 固定 1） |
| colorSpace | `colorSpaceManager.ColorSpace` |
| timestamp | `number`（ms，自系统启动） |
| brightness | `number?`（nit，仅 HDR） |

**C/NDK API**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_ColorPickerController_PickForResult(int32_t x, int32_t y, bool showValue, ArkUI_PickForResultCallback callback)` |
| 头文件 | `native_type.h` |
| 返回值 | `int32_t`（ArkUI_ErrorCode，0 表示成功） |
| @since | 26.2.0 |
| 系统能力 | SystemCapability.ArkUI.ArkUI.Full |
| 关联 AC | AC-1.1~1.4, AC-2.1~2.4, AC-5.1~5.3 |

### 变更/废弃 API

N/A；本次为全新 API。

## 接口规格

### 参数约束

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| x | number | 否 | 100 | 取值范围 0~屏幕实际宽度，超出取屏幕宽度，单位 px |
| y | number | 否 | 100 | 取值范围 0~屏幕实际高度，超出取屏幕高度，单位 px |
| showValue | boolean | 否 | false | true 显示 RGB 值，false 不显示 |

### 行为场景

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|----------|
| 1 | 参数正确 + 有权限 + 触摸设备 | 启动取色，显示圆环 | AC-1.1, AC-5.1 |
| 2 | 未传入 x/y | 圆环出现在 (100, 100) | AC-1.2 |
| 3 | showValue=true | 圆环显示 RGB | AC-1.3 |
| 4 | 抬起手指 | Promise resolve PickedColorInfo | AC-2.1 |
| 5 | 参数类型错误 | 抛出 401 | AC-5.2 |
| 6 | 非触摸设备 | 抛出 801 | AC-5.3 |
| 7 | 截图失败 | Promise reject | AC-6.1 |
| 8 | 无权限 | Promise reject | AC-7.1 |

## 兼容性声明

- **已有 API 行为变更:** 否。新增 opt-in API，不影响现有应用。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 26.2.0。
- **API 版本号策略:** ArkTS 和 C API 均 `@since 26.2.0`。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| d.ts 权威 | 对外签名以 d.ts 为真相源 | AC-1.1, AC-5.1 |
| 截图不持久化 | PixelMap 取色完成后立即释放 | AC-3.3 |
| Alpha 固定为 1 | 不从 PixelMap 读取 Alpha | AC-2.1 |
| 复用 TakeSurfaceCapture | 不新建截图接口 | AC-3.1 |
| 复用 SubwindowManager | 不新建窗口管理机制 | AC-1.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 圆环跟随延迟≤业界基线值 | 性能测试 | AC-4.1 |
| 隐私合规 | 截图 PixelMap 不持久化、不传输到应用层 | 集成测试 | AC-3.3 |
| 可靠性 | 截图失败/权限缺失时 reject 不崩溃 | 集成测试 | AC-6.1, AC-7.1 |
| 可测试性 | 参数校验、设备检查可独立断言 | 单元测试 | AC-5.2, AC-5.3 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 |
|----------|----------|----------|----------|
| 手机（触摸屏） | 正常取色 | 无特殊约束 | 集成测试 |
| 平板（触摸屏+触控笔） | 正常取色，支持触控笔 | 无特殊约束 | 集成测试 |
| 非触摸设备 | 抛出 801 | 启动时检查设备类型 | 单元测试 |

## 全局特性影响

| 特性 | 是否适用 | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 取色圆环为系统 UI，不涉及无障碍 | N/A |
| 大字体 | 否 | 无文字语义 | N/A |
| 深色模式 | 否 | 取色读取实际像素值 | N/A |
| 多窗口/分屏 | 是 | 截图含所有窗口 | AC-3.1 |
| HDR | 是 | 支持 HDR brightness | AC-2.2 |

## 行为场景（Gherkin）

Feature: 全局取色器
  作为 ArkUI 应用开发者
  我想要调用全局取色 API 启动取色并获取颜色值
  以便在屏幕上实时选取颜色

  Scenario: 正常取色流程
    Given 应用已获取截屏权限
    And 设备支持触摸/触控笔
    When 调用 colorPickerController.pickForResult(100, 100, true)
    Then 屏幕位置 (100, 100) 出现取色圆环
    And 圆环实时显示 RGB 值
    When 用户抬起手指
    Then Promise resolve 为 PickedColorInfo
    And color 的 Alpha 固定为 1
    And 截图 PixelMap 被释放

  Scenario: 参数类型错误
    When 调用 colorPickerController.pickForResult("abc", 100)
    Then 抛出 BusinessError 401

  Scenario: 非触摸设备
    Given 设备不支持触摸/触控笔
    When 调用 colorPickerController.pickForResult()
    Then 抛出 BusinessError 801

## Spec 自审清单

- [x] 无占位文本（TODO/TBD/待定）
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 参数约束、错误码、异常路径边界明确
- [x] 截图不持久化、Alpha 固定为 1 约束明确
- [x] AC、规则与 VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "colorPickerController pickForResult PickedColorInfo ColorPickerService eyedropper_picker SubwindowManager TakeSurfaceCapture"
  - repo: "openharmony/interface_sdk-js"
    query: "@ohos.arkui.colorPickerController.d.ts colorPickerController PickedColorInfo"
  - repo: "openharmony/docs"
    query: "js-apis-arkui-graphics colorPickerController pickForResult capi-arkui-nativemodule-arkui-colorPickerController"
```

**关键文档：** design-docs PR [OpenHarmonyAI/design-docs#109](https://gitcode.com/OpenHarmonyAI/design-docs/pull/109)，docs PR [openharmony/docs#162671](https://gitcode.com/openharmony/docs/pull/162671)
