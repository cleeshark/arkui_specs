# 特性规格

> Func-04-04-11-Feat-01 按键意图归一化：固化 KeyIntention / IntentionCode 从 MMI 输入到 ArkTS、NDK 与框架消费端的既有行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 按键意图归一化（KeyIntention / IntentionCode） |
| 特性编号 | Func-04-04-11-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | ArkTS 动态 API 10 起；NDK API 14 起；ArkTS 静态 API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 按键意图公开契约 | 补录 IntentionCode、KeyEvent.intentionCode 与 ArkUI_KeyIntension 的存量行为 |
| ADDED | 输入、分发与消费规则 | 补录 MMI 透传、默认 UNKNOWN、焦点消费和上下文菜单消费规则 |
| ADDED | 多通道及跨环境兼容性 | 补录 ArkTS 动态/静态、NDK 与 Preview 的差异 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | specs/04-common-capability/04-common-events/11-interaction-normalization/design.md | Baselined |
| ArkTS SDK | interface_sdk-js/api/@ohos.multimodalInput.intentionCode.d.ts | 已核验 |
| ArkTS Common API | interface_sdk-js/api/@internal/component/ets/common.d.ts | 已核验 |
| ArkTS Static API | interface_sdk-js/api/arkui/component/common.static.d.ets | 已核验 |
| NDK API | interfaces/native/native_key_event.h | 已核验 |
| Source locator | adapter/ohos/entrance/mmi_event_convertor.cpp | 已核验 |

## 用户故事

### US-1: 在 ArkTS 按键事件中读取归一化意图

**作为** ArkTS 应用开发者，  
**我想要** 从 KeyEvent.intentionCode 读取与物理按键无关的交互意图，  
**以便** 使用统一的方向、选择、退出、导航、翻页和缩放语义处理键盘输入。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN OHOS 平台 MMI KeyEvent 携带一个意图码 THEN ACE KeyEvent.keyIntention 等于 MMI GetKeyIntention() 的原值，不执行二次映射 | 正常 |
| AC-1.2 | WHEN KeyEvent 未被平台转换路径写入意图码 THEN KeyEvent.intentionCode 为 IntentionCode.INTENTION_UNKNOWN（-1） | 边界 |
| AC-1.3 | WHEN ArkTS 回调接收到 KeyEvent THEN intentionCode 为非可选 IntentionCode 字段，并可取 SDK 公开的 14 个枚举值之一 | 正常 |
| AC-1.4 | WHEN 应用使用 onKeyEvent、onKeyPreIme 或 onKeyEventDispatch 接收同一按键事件 THEN 回调对象中的 intentionCode 保持该事件携带的意图码 | 正常 |

### US-2: 通过 NDK 获取按键意图

**作为** Native 应用开发者，  
**我想要** 通过 OH_ArkUI_KeyEvent_GetKeyIntensionCode 获取 ArkUI_UIInputEvent 的按键意图，  
**以便** 在 C/C++ 侧使用与 ArkUI 事件一致的归一化语义。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 输入为有效 C_KEY_EVENT_ID 且 inputEvent 非空 THEN OH_ArkUI_KeyEvent_GetKeyIntensionCode 返回 ArkUIKeyEvent.intentionCode 对应的 ArkUI_KeyIntension 值 | 正常 |
| AC-2.2 | WHEN event 为空、inputEvent 为空或 eventTypeId 不是 C_KEY_EVENT_ID THEN 接口返回 -1 并记录 ARKUI_ERROR_CODE_PARAM_INVALID | 异常 |
| AC-2.3 | WHEN NDK 事件携带 HOME、媒体、音量、通话或相机意图 THEN getter 按 ArkUI_KeyIntension 的公开数值原样返回，即使该值不属于 ArkTS IntentionCode 的 14 值集合 | 边界 |

### US-3: 使用意图码驱动框架通用行为

**作为** 使用键盘或遥控设备的用户，  
**我想要** 组件焦点和上下文菜单识别统一的按键意图，  
**以便** 不同物理按键可以触发一致的交互结果。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 按键事件是 PreIME 事件或 action 不是 DOWN THEN 焦点意图解析结果为 NONE | 边界 |
| AC-3.2 | WHEN 原始 KeyCode 可直接解析为方向、Tab、Home、End、Enter 或 Space THEN 焦点处理优先使用原始 KeyCode，不以 keyIntention 覆盖该结果 | 正常 |
| AC-3.3 | WHEN 原始 KeyCode 未命中焦点规则且 pressedCodes 仅含一个按键 THEN INTENTION_SELECT、INTENTION_ESCAPE、INTENTION_HOME 分别回退为 SELECT、ESC、HOME，其他意图回退为 NONE | 正常 |
| AC-3.4 | WHEN action 为 DOWN 且 event.code 为 KEY_MENU 或 keyIntention 为 INTENTION_MENU THEN 已绑定上下文菜单的组件打开菜单；其他 action 或意图不触发 | 正常 |

### US-4: 获得明确的版本与环境兼容行为

**作为** 跨版本和跨环境应用开发者，  
**我想要** 明确 ArkTS 动态、NDK、ArkTS 静态及 Preview 的能力边界，  
**以便** 对不支持的通道进行兼容处理。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 使用 ArkTS 动态接口且 API >= 10 THEN IntentionCode 与 KeyEvent.intentionCode 可用；API < 10 不依赖该字段 | 边界 |
| AC-4.2 | WHEN 使用 NDK 且 API >= 14 THEN ArkUI_KeyIntension 与 OH_ArkUI_KeyEvent_GetKeyIntensionCode 可用 | 边界 |
| AC-4.3 | WHEN 使用 ArkTS 静态接口且 API >= 23 THEN KeyEvent.intentionCode 及三个按键事件入口可用 | 边界 |
| AC-4.4 | WHEN 在当前 Preview 转换路径接收按键事件 THEN 因转换未写入 keyIntention，框架观察到默认 INTENTION_UNKNOWN | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-5 | 已有实现补录 | 源码审查/ArkTS 集成测试 | adapter/ohos/entrance/mmi_event_convertor.cpp:867-875；frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_frame_node_bridge.cpp:1465-1483 |
| AC-2.1~AC-2.3 | R-6~R-8 | 已有实现补录 | NDK 单测 | test/unittest/interfaces/ace_key_event/oh_arkui_keyevent_getkeyintensioncode_test.cpp:24-79 |
| AC-3.1~AC-3.4 | R-9~R-12 | 已有实现补录 | 框架单测 | test/unittest/core/event/focus_event_handler_test_ng.cpp:180-194；test/unittest/core/base/view_abstract_model_test_ng.cpp:1023-1033 |
| AC-4.1~AC-4.3 | R-13~R-15 | 已有实现补录 | SDK 声明审查/API 测试 | interface_sdk-js/api/@ohos.multimodalInput.intentionCode.d.ts:21-171；interfaces/native/native_key_event.h:425-537 |
| AC-4.4 | R-16 | 已有实现补录 | Preview 集成测试/源码审查 | adapter/preview/entrance/event_dispatcher.cpp:110-126 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | OHOS ConvertKeyEvent 收到非空 MMI::KeyEvent | 将 GetKeyIntention() 直接转换为 KeyIntention 并写入事件 | ACE 不维护另一份生产映射表 | AC-1.1 |
| R-2 | 边界 | 新建 KeyEvent 且没有写入意图码 | keyIntention 初始化为 INTENTION_UNKNOWN | 数值固定为 -1 | AC-1.2, AC-4.4 |
| R-3 | 行为 | KeyEvent 转换为 KeyEventInfo 或 ArkTS 回调对象 | keyIntention 被复制并以 intentionCode 数值输出 | 字段在 ArkTS API 10+ 非可选 | AC-1.3, AC-1.4 |
| R-4 | 行为 | ArkTS 动态 API 10+ 读取 IntentionCode | 公开 UNKNOWN、UP、DOWN、LEFT、RIGHT、SELECT、ESCAPE、BACK、FORWARD、MENU、PAGE_UP、PAGE_DOWN、ZOOM_OUT、ZOOM_IN 共 14 值 | 不包含 HOME、媒体、通话和相机值 | AC-1.3, AC-4.1 |
| R-5 | 行为 | onKeyEvent、onKeyPreIme 或 onKeyEventDispatch 收到 KeyEvent | 各入口读取同一 KeyEvent.intentionCode 字段 | 三个入口的引入版本不同 | AC-1.4, AC-4.1, AC-4.3 |
| R-6 | 行为 | NDK getter 收到有效 C_KEY_EVENT_ID | 返回 inputEvent.intentionCode 的 ArkUI_KeyIntension 转换值 | 不修改事件内容 | AC-2.1 |
| R-7 | 异常 | NDK getter 收到空 event、空 inputEvent 或非按键 eventTypeId | 返回 -1，错误状态为 ARKUI_ERROR_CODE_PARAM_INVALID | 不解引用无效指针 | AC-2.2 |
| R-8 | 边界 | NDK getter 收到 NDK 扩展意图值 | 原样返回 ArkUI_KeyIntension 中公开的 HOME、媒体、音量、CALL、CAMERA 等值 | NDK 枚举范围大于 ArkTS IntentionCode | AC-2.3 |
| R-9 | 边界 | 焦点解析收到 isPreIme=true 或 action!=DOWN | 返回 FocusIntension::NONE | 不继续解析原始 KeyCode 或意图码 | AC-3.1 |
| R-10 | 行为 | 焦点解析收到可识别的原始 KeyCode | 优先返回原始按键对应焦点意图 | 方向键不受 pressedCodes 数量限制；其他按键要求单按键或 Shift+Tab 特例 | AC-3.2 |
| R-11 | 行为 | 原始 KeyCode 未命中且允许执行意图回退 | SELECT、ESCAPE、HOME 转为对应焦点意图，其他值返回 NONE | 回退集合仅 3 个内部意图 | AC-3.3 |
| R-12 | 行为 | 已绑定上下文菜单且 action=DOWN | KEY_MENU 或 INTENTION_MENU 任一命中即打开菜单 | 非 DOWN 不触发 | AC-3.4 |
| R-13 | 边界 | ArkTS 动态 API 版本检查 | API 10 起提供 IntentionCode 和 KeyEvent.intentionCode | onKeyEvent 自 API 7 存在，但 API 10 起才可依赖 intentionCode | AC-4.1 |
| R-14 | 边界 | NDK API 版本检查 | API 14 起提供 ArkUI_KeyIntension 和 getter | Public C API 名称保留历史拼写 Intension | AC-4.2 |
| R-15 | 边界 | ArkTS 静态 API 版本检查 | API 23 起提供 intentionCode、onKeyEvent、onKeyPreIme、onKeyEventDispatch | 静态接口不回溯到更早 API | AC-4.3 |
| R-16 | 恢复 | Preview ConvertKeyEvent 未写入 keyIntention | 保留 KeyEvent 默认 INTENTION_UNKNOWN，应用可按未知意图降级 | 当前 Preview 不与 OHOS MMI 透传路径等价 | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, R-1 | OHOS 适配层单测/源码审查 | MMI 意图码不经二次映射地写入 KeyEvent |
| VM-2 | AC-1.2, R-2 | KeyEvent 构造单测 | 未赋值时固定为 UNKNOWN=-1 |
| VM-3 | AC-1.3~AC-1.4, R-3~R-5 | ArkTS API/XTS | 14 个公开值和三个事件入口均输出 intentionCode |
| VM-4 | AC-2.1~AC-2.3, R-6~R-8 | NDK Level0 单测 | 有效值透传及三类非法输入返回 -1 |
| VM-5 | AC-3.1~AC-3.3, R-9~R-11 | FocusEventHandler 单测 | PreIME/action 门禁、KeyCode 优先级和三种意图回退 |
| VM-6 | AC-3.4, R-12 | ViewAbstractModelNG 单测 | DOWN + KEY_MENU/INTENTION_MENU 打开菜单 |
| VM-7 | AC-4.1~AC-4.3, R-13~R-15 | SDK/API 版本审查 | 动态 10、NDK 14、静态 23 的边界 |
| VM-8 | AC-4.4, R-16 | Preview 集成测试 | Preview 事件保持 UNKNOWN 并可安全降级 |

## API 变更分析

> 本文档补录存量能力，不产生新的 API 代码变更；下表记录本特性的既有公开接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| IntentionCode | Public | N/A，枚举类型 | 14 个 ArkTS 公开意图值 | N/A | 定义动态/静态 ArkTS 归一化意图契约 | AC-1.3, AC-4.1, AC-4.3 |
| KeyEvent.intentionCode | Public | N/A，事件只读语义字段 | IntentionCode | N/A | 在 ArkTS 按键回调中暴露意图码 | AC-1.3, AC-1.4 |
| OH_ArkUI_KeyEvent_GetKeyIntensionCode | Public | const ArkUI_UIInputEvent* event | ArkUI_KeyIntension；非法输入返回 -1 | ARKUI_ERROR_CODE_NO_ERROR / ARKUI_ERROR_CODE_PARAM_INVALID | 在 NDK 中读取按键意图 | AC-2.1, AC-2.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次为已有能力补录 | 无需迁移 | AC-1.1~AC-4.4 |

## 接口规格

### 接口定义

**IntentionCode 与 KeyEvent.intentionCode**

| 属性 | 值 |
|------|-----|
| 函数签名 | export enum IntentionCode；KeyEvent.intentionCode: IntentionCode |
| 返回值 | IntentionCode — 当前按键事件的归一化意图 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.4, AC-4.1, AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| intentionCode | IntentionCode | 是 | INTENTION_UNKNOWN (-1) | ArkTS 公开范围为 14 个 SDK 枚举值 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | OHOS MMI 输入携带公开意图值 | ArkTS KeyEvent 输出相同数值 | AC-1.1, AC-1.3 |
| 2 | 事件没有可用意图 | 输出 INTENTION_UNKNOWN | AC-1.2 |
| 3 | 通过任一按键回调入口读取事件 | intentionCode 保持事件值 | AC-1.4 |

**OH_ArkUI_KeyEvent_GetKeyIntensionCode**

| 属性 | 值 |
|------|-----|
| 函数签名 | ArkUI_KeyIntension OH_ArkUI_KeyEvent_GetKeyIntensionCode(const ArkUI_UIInputEvent* event) |
| 返回值 | ArkUI_KeyIntension — 有效事件的意图码；非法输入为 -1 |
| 开放范围 | Public |
| 错误码 | ARKUI_ERROR_CODE_NO_ERROR / ARKUI_ERROR_CODE_PARAM_INVALID |
| 关联 AC | AC-2.1~AC-2.3, AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | const ArkUI_UIInputEvent* | 是 | 无 | eventTypeId 必须为 C_KEY_EVENT_ID 且 inputEvent 非空 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 C key event | 返回事件中的 ArkUI_KeyIntension | AC-2.1, AC-2.3 |
| 2 | event 或 inputEvent 为空 | 返回 -1，记录参数错误 | AC-2.2 |
| 3 | eventTypeId 非 C_KEY_EVENT_ID | 返回 -1，记录参数错误 | AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文档仅补录既有行为。ArkTS 与 NDK 的公开枚举集合不同，调用方不得假设二者完全等价。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；意图码仅随瞬态 KeyEvent 传递。
- **最低支持版本:** ArkTS 动态 API 10；NDK API 14；ArkTS 静态 API 23。
- **API 版本号策略:** 按 canonical SDK 的 @since 声明区分 dynamic/static，并保留 NDK 头文件 @since 14。
- **跨环境差异:** OHOS 适配层透传 MMI 意图码；当前 Preview 适配层不写入意图码，返回默认 UNKNOWN。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 上游语义权威 | OHOS 生产路径以 MMI GetKeyIntention() 为结果源，ACE 不重定义物理键到意图的生产映射 | AC-1.1 |
| 事件模型单值传递 | keyIntention 作为 KeyEvent 的 int32 枚举字段跨适配、分发、桥接和 NDK 传递 | AC-1.1~AC-2.3 |
| SDK 契约优先 | ArkTS 公开范围以 interface_sdk-js 的 14 值 IntentionCode 为准，内部扩展值不得静默加入 ArkTS 规格 | AC-1.3, AC-2.3 |
| 消费端优先级 | 焦点先按原始 KeyCode 解析，仅在未命中时回退指定意图码 | AC-3.1~AC-3.3 |
| 无效输入安全 | NDK getter 必须先校验 event、eventTypeId 与 inputEvent | AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | ACE 适配路径仅执行一次枚举值复制，不增加额外映射遍历 | 源码审查/性能回归 | adapter/ohos/entrance/mmi_event_convertor.cpp:867-875 |
| 功耗 | 无新增定时器、轮询或后台任务 | 源码审查 | 同步事件转换与分发路径 |
| 内存 | 每个 KeyEvent 仅持有一个 KeyIntention 枚举字段，不新增持久化缓存 | 结构体审查 | frameworks/core/event/key_event.h:153-169 |
| 安全 | NDK 空指针和错误事件类型不得被解引用 | NDK 单测 | interfaces/native/event/key_event_impl.cpp:145-167 |
| 可靠性 | 无意图或不支持环境统一降级为 UNKNOWN=-1 | 单测/Preview 集成测试 | frameworks/core/event/key_event.h:162；adapter/preview/entrance/event_dispatcher.cpp:110-126 |
| 可测试性 | ArkTS/NDK、焦点消费、菜单消费和 Preview 差异均具有独立验证点 | 单测/集成测试 | VM-1~VM-8 |
| 自动化维测 | NDK 非法输入写入参数错误状态 | NDK 单测 | key_event_impl.cpp:147-167 |
| 定界定位 | 通过环境、API 通道、eventTypeId 和原始 KeyCode 可区分输入、暴露与消费问题 | 日志/源码定位 | design.md 调用链层级分析 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无设备专属分支；有物理键输入时使用 MMI 意图码 | 遵循 AC-1.1 | 外接键盘集成测试 | mmi_event_convertor.cpp:867-875 |
| 平板 | 与手机一致 | 遵循 AC-1.1 | 外接键盘集成测试 | 同上 |
| 折叠屏 | 与手机一致，折叠状态不改变意图码 | 遵循 AC-1.1 | 折叠态键盘测试 | 同上 |
| Preview | 不写入 keyIntention，保持 UNKNOWN | 遵循 AC-4.4 | Preview 集成测试 | adapter/preview/entrance/event_dispatcher.cpp:110-126 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 焦点消费使用统一 SELECT、ESCAPE、HOME 意图，但原始方向键和 Tab 规则优先 | AC-3.1~AC-3.3 |
| 大字体 | 否 | 不涉及字体或布局度量 | N/A |
| 深色模式 | 否 | 不涉及颜色和渲染 | N/A |
| 多窗口/分屏 | 否 | 意图码为事件级数据，不依赖窗口尺寸 | AC-1.1 |
| 多用户 | 否 | 不存储用户数据 | N/A |
| 版本升级 | 是 | 需按动态 API 10、NDK API 14、静态 API 23 做能力判断 | AC-4.1~AC-4.3 |
| 生态兼容 | 是 | ArkTS、NDK 与 Preview 的枚举/行为范围不完全一致 | AC-2.3, AC-4.4 |

## 行为场景（可选，Gherkin）

本特性复杂度为标准，行为场景已在“接口规格”中给出，不重复维护 Gherkin。

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（全链路、全公开意图值、全版本通道和 Preview 差异）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查
- [x] ArkTS API 已通过 canonical d.ts / d.ets 核验
- [x] NDK API 已通过 native_key_event.h 与单测核验

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "KeyEvent.keyIntention 从 MMI 适配、EventManager 分发到 ArkTS/NDK 暴露的调用链"
  - repo: "openharmony/arkui_ace_engine"
    query: "FocusEvent 和上下文菜单对 KeyIntention 的消费优先级与边界"
  - repo: "openharmony/interface_sdk-js"
    query: "IntentionCode、KeyEvent.intentionCode 动态/静态 API 契约及版本"
```

**关键文档：** interface_sdk-js/api/@ohos.multimodalInput.intentionCode.d.ts；interfaces/native/native_key_event.h；specs/04-common-capability/04-common-events/11-interaction-normalization/design.md
