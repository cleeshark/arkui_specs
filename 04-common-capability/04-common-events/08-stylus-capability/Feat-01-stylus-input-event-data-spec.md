# 特性规格

> Func-04-04-08-Feat-01 手写笔输入事件与数据暴露：固化手写笔工具类型、压力、X/Y 倾角与绕 Z 轴旋转角在 ArkTS 事件对象及 NDK 当前事件、历史事件、克隆事件中的现有行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 手写笔输入事件与数据暴露 |
| 特性编号 | Func-04-04-08-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | ArkTS 现有事件字段（版本待 canonical SDK 复核）；NDK API 12–24 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | L2（复杂） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ArkTS 事件数据契约 | 补录 `sourceTool`、`pressure`、`tiltX`、`tiltY`、`rollAngle` 在 Touch/Mouse/Hover/Click/Axis 事件对象中的现有暴露行为 |
| ADDED | NDK 当前事件读取契约 | 补录 tool type、pressure、tiltX/Y、rollAngle 的支持事件类型、返回值与 latest-status 行为 |
| ADDED | NDK 历史事件读取契约 | 补录历史 pressure、tiltX/Y 仅支持 Touch 存储的边界行为 |
| ADDED | NDK 克隆事件写入契约 | 补录 API 24 tool type、pressure、tiltX/Y、rollAngle setter 的事件类型、取值及错误码约束 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/08-stylus-capability/design.md` | 与本规格同步建立 |
| 静态生成契约 | `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/component/common.ets:94` | 已核对；非 canonical SDK 声明 |
| NDK API 声明 | `interfaces/native/ui_input_event.h:464`、`:741`、`:773`、`:1003`、`:1556`、`:1832` | 已核对 |
| NDK API 实现 | `interfaces/native/event/ui_input_event.cpp:336`、`:2215`、`:2254`、`:2334`、`:2843`、`:4268`、`:4315`、`:4861`、`:4892` | 已核对 |
| ArkTS 动态桥接 | `frameworks/bridge/declarative_frontend/engine/functions/js_touch_function.cpp:63`、`js_click_function.cpp:45`、`frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_common_bridge.cpp:9748` | 已核对 |

> 当前源码树未包含 `interface/sdk-js/api/@internal/component/ets/common.d.ts` 和 `interface/sdk-js/api/arkui/component/common.static.d.ets`。因此本规格中的动态 ArkTS 字段签名标记为“未经 canonical d.ts 验证”；NDK 签名及版本以仓内公开头文件为准。

## 用户故事

### US-1: 获取手写笔工具类型与基础姿态数据

**作为** ArkUI 应用开发者，  
**我想要** 从输入事件中读取工具类型、压力、倾角和旋转角，  
**以便** 根据手写笔姿态实现笔迹粗细、方向和工具模式交互。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN ArkTS Touch/Click 事件携带 pressure、tiltX、tiltY、rollAngle 和 sourceTool THEN 事件对象暴露对应数值，缺失 tilt/roll 的动态桥接值为 `0` | 正常 |
| AC-1.2 | WHEN 静态生成契约消费 `BaseEvent` THEN `pressure`、`tiltX`、`tiltY`、`sourceTool` 为必选字段，`rollAngle` 为可选字段 | 正常 |
| AC-1.3 | WHEN 内部工具类型为 FINGER、PEN、MOUSE、TOUCHPAD 或 JOYSTICK THEN 静态公开映射分别为 `1`、`2`、`7`、`9`、`10` | 正常 |
| AC-1.4 | WHEN 内部工具类型为 RUBBER、BRUSH、PENCIL、AIRBRUSH 或 LENS 且进入静态 ArkTS 转换 THEN 转换结果为 `-1`，不得按公开枚举声明顺序重新编号 | 边界 |

实现证据：`common.ets:94-104,8272-8279`、`reverse_converter_enums.cpp:1089-1103`、`mmi_event_convertor.cpp:120-145`、`js_touch_function.cpp:63-80`、`js_click_function.cpp:45-67`。

### US-2: 区分不同事件形态的数据暴露

**作为** ArkUI 应用开发者，  
**我想要** 明确 Touch、Mouse、Hover、Click 和 Axis 事件的数据差异，  
**以便** 不把某一事件类型的默认值误认为所有事件的统一能力。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 创建 ArkTS Hover 事件对象 THEN tiltX、tiltY、rollAngle 缺失时写入 `0`，pressure 固定写入 `0` | 正常 |
| AC-2.2 | WHEN 创建 ArkTS Axis 事件对象 THEN 输出 pressure、tiltX、tiltY、sourceTool，但不输出可选的 rollAngle | 边界 |
| AC-2.3 | WHEN Touch 或 Click 的 tiltX、tiltY、rollAngle 内部 optional 为空 THEN 动态桥接仍创建对应属性并写入 `0` | 正常 |
| AC-2.4 | WHEN SDK 类型把 rollAngle 声明为可选而运行时创建值为 `0` THEN 调用方必须区分“字段可缺省”的类型契约与“当前桥接常写 0”的实现行为 | 边界 |

实现证据：`arkts_native_common_bridge.cpp:9748-9762,11478-11513`、`js_touch_function.cpp:74-80`、`js_click_function.cpp:63-67`、`common.ets:94-104`。

### US-3: 通过 NDK 读取当前输入事件数据

**作为** Native 应用开发者，  
**我想要** 通过 NDK getter 读取当前事件的手写笔数据，  
**以便** 在 C/C++ 侧处理笔输入。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 调用 `OH_ArkUI_UIInputEvent_GetToolType` 且事件为 C touch/mouse/axis/focus-axis/hover/click 或内部 AxisEvent THEN 返回相应公开工具类型；空载荷返回 UNKNOWN 并设置 `PARAM_INVALID` | 正常 |
| AC-3.2 | WHEN 对普通 C touch 调用 `GetPressure`、`GetTiltX` 或 `GetTiltY` THEN 忽略传入的 pointerIndex 并读取 `touchPointSize - 1` 对应的最后触点 | 边界 |
| AC-3.3 | WHEN 对 hover-move 形态的 C touch 调用 `GetPressure` THEN 返回 `0.0f` 且 latest-status 为成功；调用 tiltX/Y 时读取 actionTouchPoint | 边界 |
| AC-3.4 | WHEN 对 C mouse 或 C click 调用 `GetPressure` THEN 分别读取 actionTouchPoint.pressure 或 clickEvent.pressure；其他不支持类型返回 `0.0f` 并设置 `TYPE_NOT_SUPPORT` | 正常 |
| AC-3.5 | WHEN 调用 `GetRollAngle` 且事件为 ON_TOUCH THEN 读取事件级 rollAngle；hover-move 读取 actionTouchPoint；其他 touch/click/hover 读取各自存储字段 | 正常 |
| AC-3.6 | WHEN getter 返回 `0.0f` 且调用方需要区分有效零值与错误默认值 THEN API 20+ 调用 `OH_ArkUI_UIInputEvent_GetLatestStatus` 获取最近状态 | 恢复 |

实现证据：`ui_input_event.cpp:336-453,2215-2252,2254-2332,2334-2383`、`ui_input_event.h:2150-2165`。

### US-4: 读取历史手写笔数据

**作为** Native 应用开发者，  
**我想要** 获取历史 Touch 采样中的压力和倾角，  
**以便** 重建更平滑的笔迹轨迹。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN C touch 的 historyIndex 和 pointerIndex 均有效 THEN 历史 pressure、tiltX、tiltY getter 返回指定历史事件、指定触点的数据 | 正常 |
| AC-4.2 | WHEN event 为空、历史数组为空、historyIndex 越界或 pointerIndex 越界 THEN 历史 getter 返回 `0.0f` 并设置 `PARAM_INVALID` | 异常 |
| AC-4.3 | WHEN 对非 C touch 事件调用历史 pressure/tilt getter THEN 返回 `0.0f` 并设置 `TYPE_NOT_SUPPORT` | 异常 |
| AC-4.4 | WHEN 调用方需要历史 tool type 或历史 rollAngle THEN 当前 NDK 不提供对应 API | 边界 |

实现证据：`ui_input_event.cpp:2843-2910`、`ui_input_event.h:1003-1041`。

### US-5: 修改克隆输入事件的手写笔数据

**作为** Native 框架或测试开发者，  
**我想要** 修改用户创建的克隆事件中的手写笔数据，  
**以便** 构造和转发具有明确笔姿态的输入事件。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN event 为空 THEN 任一手写笔克隆 setter 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`；WHEN event 不是用户创建的克隆事件 THEN 返回 `ARKUI_ERROR_CODE_NOT_CLONED_POINTER_EVENT` | 异常 |
| AC-5.2 | WHEN `SetToolType` 输入工具类型在 UNKNOWN 到 JOYSTICK 的公开枚举范围内且事件为 touch/mouse/axis THEN 写入对应动作触点工具类型 | 正常 |
| AC-5.3 | WHEN `SetPressure` 或 `SetPressureByIndex` 输入 pressure 小于 `0` THEN 返回 `PARAM_INVALID`；WHEN pressure 大于等于 `0` 且 Touch 目标有效 THEN 写入对应字段 | 边界 |
| AC-5.4 | WHEN `SetTiltAngle` 的任一角度小于 `-90` 或大于 `90` THEN 返回 `PARAM_INVALID`；边界值 `-90` 和 `90` 可写入 | 边界 |
| AC-5.5 | WHEN `SetRollAngle` 面向用户创建的 C touch THEN 写入事件级 rollAngle，当前实现不校验数值范围 | 正常 |
| AC-5.6 | WHEN hover-move C touch 先调用 `SetRollAngle` 再调用 `GetRollAngle` THEN setter 写事件级字段而 getter 读取 actionTouchPoint 字段，规格按该写读不对称记录风险 | 边界 |
| AC-5.7 | WHEN pressure/tilt/roll setter 面向非 Touch 事件 THEN 返回 `ARKUI_ERROR_INPUT_EVENT_TYPE_NOT_SUPPORT` | 异常 |

实现证据：`ui_input_event.cpp:4268-4384,4861-4920`、`ui_input_event.h:1556-1621,1832-1868`。

### US-6: 按 API 版本使用手写笔能力

**作为** 跨版本应用开发者，  
**我想要** 知道各接口的引入版本，  
**以便** 在低版本设备上进行正确的能力判断和降级。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN 目标版本低于 API 12 THEN 不调用 NDK tool type、pressure、tiltX/Y 及历史 pressure/tilt getter | 边界 |
| AC-6.2 | WHEN 目标版本低于 API 17 THEN 不调用 NDK `GetRollAngle` | 边界 |
| AC-6.3 | WHEN 目标版本低于 API 20 THEN 不依赖 `GetLatestStatus` 区分浮点零值；API 20+ 可使用 latest-status | 边界 |
| AC-6.4 | WHEN 目标版本低于 API 24 THEN 不调用克隆事件 tool type、pressure、tiltX/Y、rollAngle setter | 边界 |

实现证据：`ui_input_event.h:464-472,741-784,1003-1041,1556-1621,1832-1868,2150-2165`。

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1~R-4 | 已有实现 | 源码审查/ArkTS 集成测试 | `common.ets:94-104,8272-8279`、`reverse_converter_enums.cpp:1089-1103` |
| AC-2.1~2.4 | R-5~R-8 | 已有实现 | ArkTS 集成测试 | `arkts_native_common_bridge.cpp:9748-9762,11478-11513` |
| AC-3.1~3.6 | R-9~R-15 | 已有实现 | NDK 单测 | `test/unittest/interfaces/ace_ui_input_event/`、`ui_input_event.cpp:336-453,2215-2383` |
| AC-4.1~4.4 | R-16~R-19 | 已有实现 | NDK 单测 | `oh_arkui_pointerevent_gethistorypressure_test.cpp:44`、`ui_input_event.cpp:2843-2910` |
| AC-5.1~5.7 | R-20~R-26 | 已有实现 | NDK 单测/源码审查 | `oh_arkui_pointerevent_tdd_test.cpp:35-520`、`ui_input_event.cpp:4268-4920` |
| AC-6.1~6.4 | R-27~R-30 | 已有实现 | 头文件版本审查 | `interfaces/native/ui_input_event.h` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ArkTS Touch/Click 事件已完成桥接 | 输出 pressure、tiltX、tiltY、rollAngle、sourceTool | optional tilt/roll 缺失时写 `0`；`js_touch_function.cpp:74-80`、`js_click_function.cpp:63-67` | AC-1.1 |
| R-2 | 行为 | 消费静态生成 BaseEvent | pressure、tiltX、tiltY、sourceTool 必选，rollAngle 可选 | `common.ets:94-104`；动态 canonical d.ts 未随源码提供 | AC-1.2 |
| R-3 | 行为 | 内部工具类型可公开映射 | 保持 UNKNOWN=0、FINGER=1、PEN=2、MOUSE=7、TOUCHPAD=9、JOYSTICK=10 | 枚举值不连续；`common.ets:8272-8279` | AC-1.3 |
| R-4 | 边界 | 内部工具类型为 RUBBER/BRUSH/PENCIL/AIRBRUSH/LENS | 静态转换写 `-1` | 不扩展公开枚举；`reverse_converter_enums.cpp:1089-1103` | AC-1.4 |
| R-5 | 行为 | 构造 HoverInfo JS 对象 | tiltX/tiltY/rollAngle 缺失写 `0`，pressure 固定 `0` | `arkts_native_common_bridge.cpp:9748-9762` | AC-2.1 |
| R-6 | 行为 | 构造 AxisInfo JS 对象 | 输出 pressure、tiltX、tiltY、sourceTool | rollAngle 不在属性 key 列表；`arkts_native_common_bridge.cpp:11478-11513` | AC-2.2 |
| R-7 | 边界 | SDK 可选字段无上游值 | 当前 Touch/Click/Hover 动态桥创建 rollAngle 属性并写 `0` | 类型可选不等同于运行时永远缺省 | AC-2.3, AC-2.4 |
| R-8 | 边界 | 不同事件类型均继承 BaseEvent 数据语义 | 按具体桥接路径决定字段是否创建及取值来源 | 禁止以单一事件结果推导全部事件 | AC-2.1~2.4 |
| R-9 | 行为 | GetToolType 输入为支持事件 | 返回公开工具类型 | 支持 touch/mouse/axis/focus-axis/hover/click/AxisEvent；`ui_input_event.cpp:336-453` | AC-3.1 |
| R-10 | 异常 | GetToolType 的 event 或内部载荷为空 | 返回 UNKNOWN | latest-status 为 `PARAM_INVALID` | AC-3.1 |
| R-11 | 行为 | 普通 C touch 调用当前 pressure/tilt getter | 返回最后一个触点值 | pointerIndex 不参与触点选择；`ui_input_event.cpp:2215-2332` | AC-3.2 |
| R-12 | 边界 | hover-move C touch 调用当前 getter | pressure 返回 `0.0f`；tiltX/Y 从 actionTouchPoint 读取 | pressure 的 latest-status 为成功 | AC-3.3 |
| R-13 | 行为 | mouse/click 调用 pressure getter | 返回动作点或 clickEvent 的 pressure | 其他类型返回 `0.0f` + TYPE_NOT_SUPPORT | AC-3.4 |
| R-14 | 行为 | 调用 GetRollAngle | 按 subKind 和事件类型读取事件级、动作点或最后触点字段 | 空输出指针或空 event 返回 PARAM_INVALID；`ui_input_event.cpp:2334-2383` | AC-3.5 |
| R-15 | 恢复 | 浮点 getter 返回 `0.0f` | API 20+ 读取 latest-status 判别有效值与错误默认值 | 每次相关调用会先清除旧状态；`ui_input_event.h:2150-2165` | AC-3.6 |
| R-16 | 行为 | 历史 Touch 的两个索引均有效 | 返回指定 historyIndex、pointerIndex 的 pressure/tilt | 仅 C touch；`ui_input_event.cpp:2843-2910` | AC-4.1 |
| R-17 | 异常 | event/历史数组为空或任一索引越界 | 返回 `0.0f` | latest-status 为 PARAM_INVALID | AC-4.2 |
| R-18 | 异常 | 非 C touch 调用历史 pressure/tilt | 返回 `0.0f` | latest-status 为 TYPE_NOT_SUPPORT | AC-4.3 |
| R-19 | 边界 | 查询历史工具类型或历史旋转角 | 无对应 NDK API | 不以当前值 API 替代历史值 | AC-4.4 |
| R-20 | 异常 | 克隆 setter 的 event 为空或非用户创建 | 分别返回 PARAM_INVALID 或 NOT_CLONED_POINTER_EVENT | setter 不修改原事件 | AC-5.1 |
| R-21 | 行为 | SetToolType 输入公开枚举且目标为 touch/mouse/axis | 写入相应动作触点 toolType | 输入范围 UNKNOWN 到 JOYSTICK；`ui_input_event.cpp:4268-4313` | AC-5.2 |
| R-22 | 边界 | SetPressure 输入非负且目标 Touch 有效 | SetPressure 写 actionTouchPoint，ByIndex 写指定 touchPoint | 负值、负 index、越界 index 或 hover-move 返回 PARAM_INVALID | AC-5.3 |
| R-23 | 边界 | SetTiltAngle 输入 `[-90,90]` | 写 actionTouchPoint.tiltX/tiltY | 超出闭区间返回 PARAM_INVALID；`ui_input_event.cpp:4861-4890` | AC-5.4 |
| R-24 | 行为 | SetRollAngle 输入任意 float 且目标 Touch 有效 | 写事件级 rollAngle | 当前无数值范围校验；`ui_input_event.cpp:4892-4920` | AC-5.5 |
| R-25 | 边界 | hover-move Touch 写后再读 rollAngle | setter 写事件级字段，getter 读 actionTouchPoint 字段 | 维持现有写读不对称，不在规格中提出修复 | AC-5.6 |
| R-26 | 异常 | pressure/tilt/roll setter 目标不是 Touch | 返回 TYPE_NOT_SUPPORT | tool type setter 另支持 mouse/axis | AC-5.7 |
| R-27 | 边界 | 运行环境 API < 12 | NDK tool/pressure/tilt/current/history API 不可用 | `ui_input_event.h:464-472,741-773,1003-1041` | AC-6.1 |
| R-28 | 边界 | 运行环境 API < 17 | GetRollAngle 不可用 | `ui_input_event.h:773-784` | AC-6.2 |
| R-29 | 边界 | 运行环境 API < 20 | GetLatestStatus 不可用 | 调用方不可依赖该 API 消除 `0.0f` 歧义 | AC-6.3 |
| R-30 | 边界 | 运行环境 API < 24 | 手写笔克隆 setter 不可用 | `ui_input_event.h:1556-1621,1832-1868` | AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.4, R-1~R-4 | ArkTS 集成测试/源码审查 | 公开 SourceTool 非连续枚举、内部扩展工具的降级值、字段必选/可选性 |
| VM-2 | AC-2.1~2.4, R-5~R-8 | ArkTS 事件集成测试 | Touch/Click/Hover/Axis 的字段存在性、默认零值及压力差异 |
| VM-3 | AC-3.1~3.6, R-9~R-15 | NDK 单元测试 | 当前 getter 支持矩阵、最后触点行为、hover-move、latest-status |
| VM-4 | AC-4.1~4.4, R-16~R-19 | NDK 单元测试 | 历史数组和索引边界、非 Touch 类型、缺少历史 tool/roll API |
| VM-5 | AC-5.1~5.7, R-20~R-26 | NDK 单元测试 | 克隆标记、数值范围、事件类型、setter 写读字段一致性 |
| VM-6 | AC-6.1~6.4, R-27~R-30 | API 版本扫描 | API 12/17/20/24 的版本边界 |

## API 变更分析

> 本特性是已有能力补录，不新增或修改公开 API。下表列出本规格覆盖的现有 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `OH_ArkUI_UIInputEvent_GetToolType` | Public NDK | event | int32 工具类型 | latest-status: NO_ERROR/PARAM_INVALID/TYPE_NOT_SUPPORT | 获取当前事件工具类型 | AC-3.1 |
| `OH_ArkUI_PointerEvent_GetPressure` | Public NDK | event, pointerIndex | float 压力或 `0.0f` | latest-status: NO_ERROR/PARAM_INVALID/TYPE_NOT_SUPPORT | 获取当前压力 | AC-3.2~3.4, AC-3.6 |
| `OH_ArkUI_PointerEvent_GetTiltX/Y` | Public NDK | event, pointerIndex | float 角度或 `0.0f` | latest-status: NO_ERROR/PARAM_INVALID/TYPE_NOT_SUPPORT | 获取当前 X/Y 倾角 | AC-3.2~3.4, AC-3.6 |
| `OH_ArkUI_PointerEvent_GetRollAngle` | Public NDK | event, rollAngle 输出指针 | ArkUI_ErrorCode | NO_ERROR/PARAM_INVALID；latest-status 可为 TYPE_NOT_SUPPORT | 获取当前绕 Z 轴旋转角 | AC-3.5 |
| `OH_ArkUI_PointerEvent_GetHistoryPressure/TiltX/TiltY` | Public NDK | event, pointerIndex, historyIndex | float 或 `0.0f` | latest-status: NO_ERROR/PARAM_INVALID/TYPE_NOT_SUPPORT | 获取历史 Touch 数据 | AC-4.1~4.3 |
| `OH_ArkUI_ClonedEvent_SetToolType` | Public NDK | cloned event, toolType | ArkUI_ErrorCode | NO_ERROR/PARAM_INVALID/NOT_CLONED | 写克隆事件工具类型 | AC-5.1, AC-5.2 |
| `OH_ArkUI_ClonedEvent_SetPressure/SetPressureByIndex` | Public NDK | cloned event, pressure[, pointerIndex] | ArkUI_ErrorCode | NO_ERROR/PARAM_INVALID/NOT_CLONED/TYPE_NOT_SUPPORT | 写克隆 Touch 压力 | AC-5.1, AC-5.3, AC-5.7 |
| `OH_ArkUI_ClonedEvent_SetTiltAngle` | Public NDK | cloned event, tiltX, tiltY | ArkUI_ErrorCode | NO_ERROR/PARAM_INVALID/NOT_CLONED/TYPE_NOT_SUPPORT | 写克隆 Touch 倾角 | AC-5.1, AC-5.4, AC-5.7 |
| `OH_ArkUI_ClonedEvent_SetRollAngle` | Public NDK | cloned event, rollAngle | ArkUI_ErrorCode | NO_ERROR/PARAM_INVALID/NOT_CLONED/TYPE_NOT_SUPPORT | 写克隆 Touch 旋转角 | AC-5.1, AC-5.5~5.7 |

ArkTS 现有字段：`BaseEvent.pressure`、`tiltX`、`tiltY`、`rollAngle?`、`sourceTool`。仓内静态生成契约见 `common.ets:94-104`；动态 canonical d.ts 未随当前源码树提供，故签名未经 canonical d.ts 验证。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次仅补录现有能力 | 无迁移要求 | 全部 |

## 接口规格

### 接口定义

**当前事件读取接口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_UIInputEvent_GetToolType(const ArkUI_UIInputEvent* event)` |
| 函数签名 | `float OH_ArkUI_PointerEvent_GetPressure(const ArkUI_UIInputEvent* event, uint32_t pointerIndex)` |
| 函数签名 | `float OH_ArkUI_PointerEvent_GetTiltX/Y(const ArkUI_UIInputEvent* event, uint32_t pointerIndex)` |
| 函数签名 | `int32_t OH_ArkUI_PointerEvent_GetRollAngle(const ArkUI_UIInputEvent* event, double* rollAngle)` |
| 返回值 | 工具枚举、浮点数据或 ArkUI_ErrorCode |
| 开放范围 | Public NDK |
| 错误码 | `ARKUI_ERROR_CODE_NO_ERROR`、`ARKUI_ERROR_CODE_PARAM_INVALID`、`ARKUI_ERROR_INPUT_EVENT_TYPE_NOT_SUPPORT` |
| 关联 AC | AC-3.1~3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | `const ArkUI_UIInputEvent*` | 是 | 无 | 不得为空，事件类型必须位于对应 getter 支持矩阵 |
| pointerIndex | `uint32_t` | 是 | 无 | 当前普通 Touch pressure/tilt 实现忽略该值并取最后触点 |
| rollAngle | `double*` | 是 | 无 | 不得为空；成功时写入结果 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 支持事件、数据有效 | 返回对应当前值并设置成功状态 | AC-3.1~3.5 |
| 2 | 空 event/空载荷 | 返回 UNKNOWN、`0.0f` 或 PARAM_INVALID，并设置 PARAM_INVALID | AC-3.1, AC-3.4~3.6 |
| 3 | 不支持事件类型 | 返回默认值或 PARAM_INVALID，latest-status 为 TYPE_NOT_SUPPORT | AC-3.4~3.6 |

**历史数据读取接口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `float OH_ArkUI_PointerEvent_GetHistoryPressure/TiltX/TiltY(const ArkUI_UIInputEvent* event, uint32_t pointerIndex, uint32_t historyIndex)` |
| 返回值 | 指定历史触点的 float 数据；异常时 `0.0f` |
| 开放范围 | Public NDK |
| 错误码 | 通过 latest-status 返回 NO_ERROR/PARAM_INVALID/TYPE_NOT_SUPPORT |
| 关联 AC | AC-4.1~4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | `const ArkUI_UIInputEvent*` | 是 | 无 | 仅支持 C touch |
| pointerIndex | `uint32_t` | 是 | 无 | 小于目标历史事件的 touchPointSize |
| historyIndex | `uint32_t` | 是 | 无 | 小于 historySize 且 historyEvents 非空 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 两个索引有效 | 返回指定历史触点的数据 | AC-4.1 |
| 2 | 任一索引或历史数组无效 | 返回 `0.0f` + PARAM_INVALID | AC-4.2 |
| 3 | 非 Touch 事件 | 返回 `0.0f` + TYPE_NOT_SUPPORT | AC-4.3 |

**克隆事件写入接口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_ArkUI_ClonedEvent_SetToolType/SetPressure/SetPressureByIndex/SetTiltAngle/SetRollAngle(...)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public NDK |
| 错误码 | NO_ERROR/PARAM_INVALID/NOT_CLONED_POINTER_EVENT/TYPE_NOT_SUPPORT |
| 关联 AC | AC-5.1~5.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | `const ArkUI_UIInputEvent*` | 是 | 无 | 非空且 `isCreatedByUser=true` |
| toolType | `int32_t` | 是 | 无 | 公开工具枚举 UNKNOWN 至 JOYSTICK；仅 touch/mouse/axis |
| pressure | `float` | 是 | 无 | `pressure >= 0`；仅 Touch；ByIndex 还要求 index 有效 |
| tiltX/tiltY | `float` | 是 | 无 | 各自在闭区间 `[-90,90]`；仅 Touch |
| rollAngle | `float` | 是 | 无 | 当前无范围检查；仅 Touch |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 用户创建的支持事件且参数有效 | 写入对应字段并返回 NO_ERROR | AC-5.2~5.5 |
| 2 | 非克隆事件 | 返回 NOT_CLONED_POINTER_EVENT，不写入 | AC-5.1 |
| 3 | 数值越界、索引越界或空载荷 | 返回 PARAM_INVALID，不写入 | AC-5.1, AC-5.3, AC-5.4 |
| 4 | 不支持事件类型 | 返回 TYPE_NOT_SUPPORT | AC-5.7 |

## 兼容性声明

- **已有 API 行为变更:** 否；本规格记录现有实现。内部扩展工具类型在静态公开转换中为 `-1`，SDK 可选 rollAngle 与部分运行时默认 `0` 的差异保持可见。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** ArkTS 字段版本需由 canonical SDK 声明复核；本规格覆盖的 NDK 接口最低为 API 12。
- **API 版本号策略:** NDK tool type/pressure/tilt/history 为 API 12；rollAngle 为 API 17；latest-status 为 API 20；克隆事件 setter 为 API 24。
- **已知实现差异:** Hover pressure 固定为 `0`；Axis 动态桥不输出 rollAngle；普通 Touch 当前 pressure/tilt getter 忽略 pointerIndex；克隆 hover-move rollAngle 存在写读字段不对称。
- **SDK 交叉验证风险:** 当前 checkout 缺少 canonical `common.d.ts`/`common.static.d.ets`，静态字段形态仅由仓内生成文件验证，动态注释语义与 `@since` 需在具备 SDK 仓时复核。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 公开契约与内部工具枚举隔离 | 内部 SourceTool 可包含 RUBBER/BRUSH/PENCIL/AIRBRUSH/LENS，公开静态枚举仍仅暴露六类 | AC-1.3, AC-1.4 |
| 事件形态独立存储 | Touch、Mouse、Hover、Click、Axis 使用不同事件结构及字段来源，getter 不得假定统一布局 | AC-2.1~3.5 |
| 错误状态旁路 | 返回 `0.0f` 的 NDK getter 通过 latest-status 区分有效零值与错误 | AC-3.6, AC-4.2, AC-4.3 |
| 克隆事件边界 | setter 只允许用户创建的事件，且 pressure/tilt/roll 仅支持 Touch | AC-5.1~5.7 |
| 现有行为优先 | 对 pointerIndex 忽略、Hover pressure 为零、rollAngle 写读不对称仅记录风险，不在补录规格中改变实现 | AC-2.1, AC-3.2, AC-5.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次 getter/setter 不引入事件队列等待或跨线程阻塞 | 源码审查/性能回归 | `ui_input_event.cpp` 为同步结构字段访问 |
| 功耗 | 无额外轮询、定时器或后台任务 | 源码审查 | 当前实现按事件调用 |
| 内存 | getter 不创建持久对象；setter 原位修改克隆事件字段 | 源码审查 | `ui_input_event.cpp:2215-2383,4268-4920` |
| 安全 | 无新增权限；空指针、非法索引和非克隆事件必须返回错误 | NDK 单测 | AC-3.1, AC-4.2, AC-5.1 |
| 可靠性 | 错误路径不越界访问历史数组或触点数组 | 边界单测 | `isHistoryCTouchEventParamValid` 调用路径 |
| 可测试性 | 每类 getter/setter 可通过构造 ArkUI_UIInputEvent 独立验证 | 单元测试 | `test/unittest/interfaces/ace_ui_input_event/` |
| 自动化维测 | API 20+ 可读取 latest-status 定界默认零值 | NDK 单测 | `ui_input_event.h:2150-2165` |
| 定界定位 | 错误码区分参数错误、事件类型不支持和非克隆事件 | NDK 单测 | R-10, R-15, R-17, R-18, R-20, R-26 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 取决于是否存在支持 pressure/tilt/roll 的输入硬件 | 缺失姿态数据按事件桥接规则返回缺省或零值 | 真机输入测试 | ArkTS/NDK 默认值规则 |
| 平板 | 常见手写笔主设备形态；API 行为与手机一致 | 不根据设备类型改变数值范围和错误码 | 真机输入测试 | MMI 转换与事件桥无设备分支 |
| 折叠屏 | 坐标映射由其他能力负责，笔姿态字段规则不变 | 展开/折叠不改变 tool/pressure/tilt/roll 契约 | 折叠态集成测试 | 本特性不处理窗口坐标变换 |
| Preview | preview 输入模型包含 force/tilt/sourceTool，但未提供 rollAngle | rollAngle 可能缺失或为默认值，不视为真机能力等价 | Preview 集成测试 | `adapter/preview/external/multimodalinput/pointer_event.h:45`、`adapter/preview/entrance/event_dispatcher.cpp:76` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 本特性仅暴露输入数据，不新增无障碍语义 | 无 |
| 大字体 | 否 | 不涉及文本尺寸或布局 | 无 |
| 深色模式 | 否 | 不涉及颜色和渲染样式 | 无 |
| 多窗口/分屏 | 是 | tool/pressure/tilt/roll 数据契约保持不变；坐标换算不在本 Feat 范围 | 多窗口输入事件 |
| 多用户 | 否 | 事件数据不按系统用户区分 | 无 |
| 版本升级 | 是 | 应按 API 12/17/20/24 做符号可用性判断 | AC-6.1~6.4 |
| 生态兼容 | 是 | 内部工具类型多于公开枚举，调用方不得假定所有内部类型均可公开表示 | AC-1.3, AC-1.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 手写笔输入事件与数据暴露
  作为 ArkUI 应用开发者
  我想要稳定读取和构造手写笔输入数据
  以便实现跨 ArkTS 与 NDK 的笔输入交互

  Scenario: Hover 事件缺少压力但包含姿态
    Given 上游 HoverInfo 包含 tiltX、tiltY 和 rollAngle
    When ArkTS 动态桥创建 Hover 事件对象
    Then pressure 等于 0
    And tiltX、tiltY、rollAngle 使用上游值或缺失时的 0

  Scenario Outline: 克隆事件倾角边界
    Given 事件由用户创建且类型为 C touch
    When 调用 SetTiltAngle 传入 <tiltX> 和 <tiltY>
    Then 返回 <result>

    Examples:
      | tiltX | tiltY | result |
      | -90 | 90 | ARKUI_ERROR_CODE_NO_ERROR |
      | -90.1 | 0 | ARKUI_ERROR_CODE_PARAM_INVALID |
      | 0 | 90.1 | ARKUI_ERROR_CODE_PARAM_INVALID |

  Scenario: 当前 Touch getter 忽略 pointerIndex
    Given C touch 包含两个触点且最后触点 pressure 为 0.8
    When 使用 pointerIndex 0 调用 GetPressure
    Then 返回最后触点的 pressure 0.8

  Scenario: 通过 latest-status 判别零值
    Given API 20 或更高版本
    When 浮点 getter 返回 0.0
    Then 调用 GetLatestStatus 区分有效零值、参数错误和事件类型不支持
```

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：覆盖事件数据暴露，不覆盖悬停命中、手写检测服务和文本编辑命令
- [x] 无“快速”“稳定”“尽可能”等不可验证表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则具有可复现触发条件、可观测结果、边界值、关联 AC，且无冲突
- [x] ArkTS 与 NDK 通道分别描述，SDK 声明缺失风险已显式记录
- [x] 所有实现结论均关联仓内源码或公开头文件路径及行号

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "SourceTool pressure tiltX tiltY rollAngle 在 Touch Mouse Hover Click Axis 事件中的桥接与存储路径"
  - repo: "openharmony/arkui_ace_engine"
    query: "OH_ArkUI_UIInputEvent_GetToolType 与 PointerEvent current history cloned API 的支持类型、错误码和版本边界"
  - repo: "openharmony/arkui_ace_engine"
    query: "MMI 手写笔工具类型、压力、倾角、旋转角到 ArkUI TouchEvent 的转换路径"
```

**关键文档：** `interfaces/native/ui_input_event.h`、`interfaces/native/event/ui_input_event.cpp`、`frameworks/core/event/touch_event.cpp`、`adapter/ohos/entrance/mmi_event_convertor.cpp`。
