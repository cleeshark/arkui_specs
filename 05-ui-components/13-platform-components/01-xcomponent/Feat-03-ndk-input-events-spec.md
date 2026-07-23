# 特性规格

> Func-05-13-01-Feat-03 经典 NDK 输入事件：固化 OH_NativeXComponent 的 touch/mouse/key/focus/blur/hover/touch-intercept/UI-input-event 回调注册、事件查询、坐标/工具类型/历史点/修饰键状态查询，及统一返回码与空回调策略的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 经典 NDK 输入事件（touch/mouse/key/focus/blur/hover） |
| 特性编号 | Func-05-13-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | NDK @since 8（touch/surface）/ 9（mouse）/ 10（key/focus/blur/intercept）/ 12（UIInputEvent）/ 14（KeyEventWithResult）/ 20（modifier/lock 状态） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | touch 事件规格 | RegisterCallback(DispatchTouchEvent)、GetTouchEvent、类型/工具/倾斜/历史点/坐标/源类型 |
| ADDED | mouse 事件规格 | RegisterMouseEventCallback、GetMouseEvent、动作/按钮枚举、额外信息+修饰键（@since 20） |
| ADDED | key 事件规格 | RegisterKeyEventCallback/WithResult、GetKeyEvent+Action/Code/SourceType/DeviceId/Timestamp、修饰键/锁状态（@since 20） |
| ADDED | focus/blur/intercept/UIInputEvent 规格 | 各 Register 回调、HitTestMode 返回、仅 AXIS 类型 UIInputEvent |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/13-platform-components/01-xcomponent/design.md` | Baselined |

---

## 用户故事

### US-1: 注册与接收触摸事件

**作为** NDK 开发者,
**我想要** 通过 RegisterCallback 注册 DispatchTouchEvent 并查询触摸详情,
**以便** 在 native 层处理触摸。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `OH_NativeXComponent_RegisterCallback(component, &cb)` 且 component/impl 非空 THEN 返回 SUCCESS(0)，存储回调 | 正常 |
| AC-1.2 | WHEN component 或 callback 为 null THEN 返回 BAD_PARAMETER(-2)，不存储 | 异常 |
| AC-1.3 | WHEN 触摸事件发生且已注册 DispatchTouchEvent THEN pattern 将 touchEvent/touchPoints 设入 impl 后调用 DispatchTouchEvent(component, surface) | 正常 |
| AC-1.4 | WHEN 未注册 DispatchTouchEvent THEN 触摸事件为静默 no-op（null 守卫） | 边界 |
| AC-1.5 | WHEN `GetTouchEvent(component, window, &event)` 且 window 匹配 THEN 填充 OH_NativeXComponent_TouchEvent（含 touchPoints[10]）返回 SUCCESS；window 不匹配返回 FAILED(-1)；任一 null 返回 BAD_PARAMETER | 正常 |
| AC-1.6 | WHEN TouchEventType THEN 取值 DOWN(0)/UP(1)/MOVE(2)/CANCEL(3)/UNKNOWN(4) | 边界 |
| AC-1.7 | WHEN `GetTouchPointToolType(pointIndex, &tool)` 且 pointIndex 越界（>=10 或 >=size） THEN 返回 SUCCESS 但 *tool=UNKNOWN(0)（不报错） | 边界 |
| AC-1.8 | WHEN `GetTouchPointTiltX/TiltY(pointIndex, &tilt)` 越界 THEN 返回 SUCCESS 但 *tilt=0.0f | 边界 |
| AC-1.9 | WHEN `GetHistoricalPoints(component, window, &size, &points)` 且 window 匹配 THEN *size=历史点数，*points=数组首址，返回 SUCCESS | 正常 |
| AC-1.10 | WHEN `GetTouchEventSourceType(pointId, &src)` 且 pointId 匹配最后触摸 fingerId THEN 返回 SUCCESS；不匹配返回 BAD_PARAMETER | 正常 |
| AC-1.11 | WHEN `GetTouchPointWindowX/Y` 或 `DisplayX/Y`(pointIndex) 越界 THEN 返回 SUCCESS 但输出 0.0f | 边界 |

### US-2: 注册与接收鼠标事件

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `RegisterMouseEventCallback(component, &cb)` 非空 THEN 返回 SUCCESS，存储 DispatchMouseEvent/DispatchHoverEvent | 正常 |
| AC-2.2 | WHEN 鼠标悬停 THEN 触发 DispatchHoverEvent(component, isHover)；鼠标动作 THEN 触发 DispatchMouseEvent(component, surface) | 正常 |
| AC-2.3 | WHEN `GetMouseEvent(component, window, &event)` 且 window 匹配 THEN 填充 MouseEvent（x,y,screenX,screenY,timestamp,action,button）返回 SUCCESS | 正常 |
| AC-2.4 | WHEN `GetExtraMouseEventInfo(component, &info)`（@since 20） THEN 返回含 modifierKeyStates 的信息；`GetMouseEventModifierKeyStates(info, &keys)` 返回位掩码 | 正常 |
| AC-2.5 | WHEN MouseEventAction 取值 THEN NONE(0)/PRESS(1)/RELEASE(2)/MOVE(3)/CANCEL(4)；Button 位掩码 LEFT(0x01)/RIGHT(0x02)/MIDDLE(0x04)/BACK(0x08)/FORWARD(0x10) | 边界 |

### US-3: 注册与接收按键事件

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `RegisterKeyEventCallback(component, cb)` THEN 存储回调；按键发生时调用，pattern 返回 false（不消费） | 正常 |
| AC-3.2 | WHEN `RegisterKeyEventCallbackWithResult(component, cb)`（@since 14）已注册 THEN 其优先于普通 key 回调，bool 返回决定是否消费 | 正常 |
| AC-3.3 | WHEN `GetKeyEvent(component, &keyEvent)` THEN 返回 OH_NativeXComponent_KeyEvent 指针 | 正常 |
| AC-3.4 | WHEN GetKeyEventAction/Code/SourceType/DeviceId/Timestamp THEN 分别返回对应字段，任一入参 null 返回 BAD_PARAMETER | 正常 |
| AC-3.5 | WHEN `GetKeyEventModifierKeyStates/NumLockState/CapsLockState/ScrollLockState`（@since 20） THEN 返回对应状态，任一入参 null 返回 ERROR_CODE_PARAM_INVALID(401) | 正常 |

### US-4: 焦点/失焦/触摸拦截/UIInputEvent

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `RegisterFocusEventCallback` / `RegisterBlurEventCallback`（@since 10）非空 THEN 返回 SUCCESS，焦点/失焦时触发 | 正常 |
| AC-4.2 | WHEN `RegisterOnTouchInterceptCallback(component, cb)`（@since 10）非空 THEN 返回 ERROR_CODE_NO_ERROR(0)；拦截时调用 cb 返回 HitTestMode | 正常 |
| AC-4.3 | WHEN component 或 cb 为 null THEN RegisterOnTouchInterceptCallback 返回 ERROR_CODE_PARAM_INVALID(401) | 异常 |
| AC-4.4 | WHEN `RegisterUIInputEventCallback(component, cb, type)`（@since 12）且 type=ARKUI_UIINPUTEVENT_TYPE_AXIS THEN 存储为 axis 回调返回 0；其它 type 返回 401（"event type is not supported"） | 边界 |

---

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1~1.11 | R-1~R-7 | C-API 单测 + 代码评审 | `native_interface_xcomponent.cpp:132-217,444-452` |
| AC-2.1~2.5 | R-8~R-10 | 代码评审 | `native_interface_xcomponent.cpp:219-227,743-761` |
| AC-3.1~3.5 | R-11~R-13 | 代码评审 | `native_interface_xcomponent.cpp:259-333,763-797` |
| AC-4.1~4.4 | R-14~R-16 | 代码评审 | `native_interface_xcomponent.cpp:248-277,390-442` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | RegisterCallback 非空 | 返回 SUCCESS(0)，存储回调（重复覆盖） | @since 8 | AC-1.1 |
| R-2 | 异常 | RegisterCallback component/cb null | 返回 BAD_PARAMETER(-2)，不存储 | — | AC-1.2 |
| R-3 | 行为 | 触摸发生且已注册 | 设 touchEvent/Points 到 impl，调 DispatchTouchEvent | 未注册则 no-op | AC-1.3, AC-1.4 |
| R-4 | 行为 | GetTouchEvent window 匹配 | 填充 TouchEvent（touchPoints[10]）返回 SUCCESS；不匹配 FAILED；null BAD_PARAMETER | OH_NATIVE_XCOMPONENT_MAX_TOUCH_POINTS=10 | AC-1.5 |
| R-5 | 边界 | TouchEventType | DOWN(0)/UP(1)/MOVE(2)/CANCEL(3)/UNKNOWN(4) | — | AC-1.6 |
| R-6 | 边界 | GetTouchPointToolType/TiltX/Y/WindowX/Y/DisplayX/Y 越界 | 返回 SUCCESS 但输出默认（UNKNOWN/0.0f） | 不报错 | AC-1.7, AC-1.8, AC-1.11 |
| R-7 | 行为 | GetHistoricalPoints / GetTouchEventSourceType | 历史点返回 size+首址；sourceType 需 pointId 匹配最后 fingerId 否则 BAD_PARAMETER | @since 10/12 | AC-1.9, AC-1.10 |
| R-8 | 行为 | RegisterMouseEventCallback 非空 | 返回 SUCCESS，存储 DispatchMouseEvent/HoverEvent | @since 9 | AC-2.1 |
| R-9 | 行为 | 鼠标悬停/动作 | 分别触发 DispatchHoverEvent / DispatchMouseEvent | — | AC-2.2 |
| R-10 | 行为 | GetMouseEvent / GetExtraMouseEventInfo+ModifierKeyStates | window 匹配填充；modifier 位掩码（@since 20） | Action/Button 枚举 | AC-2.3~2.5 |
| R-11 | 行为 | RegisterKeyEventCallback | 存储回调，按键时调用，pattern 返回 false | @since 10 | AC-3.1 |
| R-12 | 行为 | RegisterKeyEventCallbackWithResult（@since 14） | 优先于普通 key，bool 返回决定消费 | — | AC-3.2 |
| R-13 | 行为 | GetKeyEvent + Action/Code/SourceType/DeviceId/Timestamp/Modifier/Lock | 返回各字段；@since 20 状态任一 null 返回 401 | KeyAction UNKNOWN(-1)/DOWN(0)/UP(1) | AC-3.3~3.5 |
| R-14 | 行为 | RegisterFocus/BlurEventCallback（@since 10） | 非空返回 SUCCESS，焦点/失焦触发 | — | AC-4.1 |
| R-15 | 行为 | RegisterOnTouchInterceptCallback（@since 10） | 非空返回 0，返回 HitTestMode；null 返回 401 | 用 ArkUI 错误码 | AC-4.2, AC-4.3 |
| R-16 | 边界 | RegisterUIInputEventCallback（@since 12） | 仅 AXIS 类型受理返回 0；其它 type 返回 401 | — | AC-4.4 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.x, R-1~R-7 | C-API 单测 | 触摸注册/查询/越界默认值 |
| VM-2 | AC-2.x, R-8~R-10 | 代码评审 | 鼠标回调与修饰键 |
| VM-3 | AC-3.x, R-11~R-13 | 代码评审 | 按键 WithResult 优先与状态查询 |
| VM-4 | AC-4.x, R-14~R-16 | 代码评审 | focus/blur/intercept/UIInputEvent AXIS 限制 |

---

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| OH_NativeXComponent_RegisterCallback | Public（NDK @since 8） | component, Callback* | OH_NativeXComponent_Result | 0/-2 | 注册表面+触摸回调 | AC-1.1 |
| OH_NativeXComponent_GetTouchEvent | Public（NDK @since 8） | component, window, *event | Result | 0/-1/-2 | 查询触摸事件 | AC-1.5 |
| OH_NativeXComponent_RegisterMouseEventCallback | Public（NDK @since 9） | component, MouseEvent_Callback* | Result | 0/-2 | 注册鼠标回调 | AC-2.1 |
| OH_NativeXComponent_RegisterKeyEventCallback | Public（NDK @since 10） | component, cb | Result | 0/-2 | 注册按键回调 | AC-3.1 |
| OH_NativeXComponent_RegisterOnTouchInterceptCallback | Public（NDK @since 10） | component, cb→HitTestMode | ArkUI_ErrorCode | 0/401 | 触摸拦截 | AC-4.2 |

### 变更/废弃 API

无。

---

## 接口规格

### 接口定义

**OH_NativeXComponent_RegisterCallback(component, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_NativeXComponent_Result OH_NativeXComponent_RegisterCallback(OH_NativeXComponent*, OH_NativeXComponent_Callback*)` |
| 返回值 | OH_NativeXComponent_Result — 0=SUCCESS, -2=BAD_PARAMETER |
| 开放范围 | Public（NDK） |
| 错误码 | SUCCESS(0), BAD_PARAMETER(-2) |
| 关联 AC | AC-1.1, AC-1.2 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** touch/surface @since 8；mouse @since 9；key/focus/blur/intercept @since 10；UIInputEvent @since 12；KeyEventWithResult @since 14；modifier/lock 状态 @since 20
- **返回码分裂:** @since 8–12 用 OH_NATIVEXCOMPONENT_RESULT_*(0/-1/-2)；@since 10 intercept 与 @since 20 系列 ArkUI 错误码(0/401)
- **越界访问器不报错:** ToolType/Tilt/WindowX/Y/DisplayX/Y 越界返回 SUCCESS+默认值（UNKNOWN/0.0f）

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 越界 pointIndex 不报错 | 索引访问器返回 SUCCESS+默认值 | AC-1.7, AC-1.8, AC-1.11 |
| KeyEventWithResult 优先 | 同时注册时 WithResult 生效 | AC-3.2 |
| UIInputEvent 仅 AXIS | 其它 type 返回 401 | AC-4.4 |
| 返回码双轨制 | 旧 NDK 0/-1/-2 vs 新 ArkUI 0/401 | 兼容性声明 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 各 Register/Get 可经 Mock NativeXComponentImpl 验证 | 单测 | `native_interface_xcomponent_impl.cpp` |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | 集成测试 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 输入事件不经无障碍树 | — |
| 多窗口/分屏 | 否 | 坐标已含 window/display 维度 | — |
| 其余 | 否 | — | — |

---

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC 使用 WHEN/THEN
- [x] 范围边界明确（不涉及表面生命周期/控制器/HDR/analyzer）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "OH_NativeXComponent 各 Register 回调的存储与派发链路、越界访问器默认值策略"
  - repo: "openharmony/ace_engine"
    query: "RegisterKeyEventCallbackWithResult 优先于 RegisterKeyEventCallback 的处理"
```

**关键文档：** `interfaces/native/native_interface_xcomponent.h/.cpp`、`native_interface_xcomponent_impl.cpp/.h`、`xcomponent_pattern.cpp`（HandleTouchEvent/MouseEvent/KeyEvent/FocusEvent/BlurEvent）
