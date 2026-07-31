# 特性规格

> Func-04-04-04-Feat-01 组件组合键注册与触发：补录通用组件 `keyboardShortcut` 的 API、注册、匹配、分发、回调和清理行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 组件组合键注册与触发 |
| 特性编号 | Func-04-04-04-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 API 10 起支持，API 12 扩展功能键；静态 API 23 起支持 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 组件组合键完整行为规格 | 补录现有 `keyboardShortcut` API、参数约束、注册、匹配、分发、回调和清理语义 |
| ADDED | 动态/静态/CJ/InnerApi 通道差异 | 记录 API 10/12/23 版本边界和当前桥接差异，不修改产品实现 |
| ADDED | 现状风险与验证映射 | 固化大小写去重、单条清理和动态 attributeModifier 修饰键数组偏差 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/04-component-shortcuts/design.md` | Baselined |
| 动态 SDK API | `interface/sdk-js/api/@internal/component/ets/common.d.ts:24679` | 已核验 |
| 动态枚举 | `interface/sdk-js/api/@internal/component/ets/enums.d.ts:3657` | 已核验 |
| 静态 SDK API | `interface/sdk-js/api/arkui/component/common.static.d.ets:13781` | 已核验 |
| 动态前端入口 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:12276` | 已核验 |
| 核心注册与分发 | `frameworks/core/components_ng/base/view_abstract.cpp:7390`、`frameworks/core/common/key_event_manager.cpp:128` | 已核验 |

---

## 用户故事

### US-1: 配置字符键和功能键组合

**作为** ArkUI 应用开发者，
**我想要** 在任意通用组件上配置字符键或功能键组合，
**以便** 用户通过外接键盘快速触发组件操作。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 动态 API 传入单个可输入字符、1~3 个互不重复的 `CTRL`/`SHIFT`/`ALT` 和可选回调 THEN 当前 FrameNode 注册该组合键 | 正常 |
| AC-1.2 | WHEN `value` 为 `ESC` 或 `F1`~`F12` 且 `keys` 为空 THEN 组合键允许注册 | 边界 |
| AC-1.3 | WHEN API 12+ 使用 `TAB`、`DPAD_UP`、`DPAD_DOWN`、`DPAD_LEFT` 或 `DPAD_RIGHT` THEN 按对应功能键名称注册 | 正常 |
| AC-1.4 | WHEN `keys` 同时包含 `CTRL`、`SHIFT`、`ALT` 各一次 THEN 三个修饰键被编码为一个组合掩码 | 边界 |
| AC-1.5 | WHEN `keys` 数量大于 3 或包含重复修饰键 THEN 组合键不注册且不触发回调 | 异常 |
| AC-1.6 | WHEN 字符型 `value` 未配置有效修饰键 THEN 组合键不注册 | 异常 |
| AC-1.7 | WHEN 同一节点依次配置多个不同触发组合 THEN EventHub 保留多条组合键记录，节点只在全局列表注册一次 | 正常 |
| AC-1.8 | WHEN 任意已注册节点存在相同 `value` 与修饰键掩码 THEN 后续相同触发组合不再注册 | 边界 |

### US-2: 精确匹配并触发组件行为

**作为** 使用外接键盘的用户，
**我想要** 只在按键组合精确匹配时触发目标组件，
**以便** 避免额外按键或系统快捷键造成误触。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 按键动作是 `DOWN` 且字符/功能键与修饰键集合精确匹配 THEN 首个可用节点的组合键被触发并停止继续扫描 | 正常 |
| AC-2.2 | WHEN 注册项包含 `action` THEN 匹配后同步调用该回调并返回已消费 | 正常 |
| AC-2.3 | WHEN 注册项不包含 `action` 且组件可点击 THEN 匹配后通过 `KeyBoardShortCutClick` 触发组件点击 | 正常 |
| AC-2.4 | WHEN 注册项不包含 `action` 且组件不可点击 THEN 不产生回调或点击，继续检查其他注册项 | 边界 |
| AC-2.5 | WHEN 实际按键集合比注册组合多一个或少一个按键 THEN `IsExactlyKey` 判定不匹配 | 边界 |
| AC-2.6 | WHEN 按键动作不是 `DOWN` THEN 组合键不触发 | 异常 |
| AC-2.7 | WHEN目标节点非活动或 EventHub 被禁用 THEN 跳过该节点 | 异常 |
| AC-2.8 | WHEN 输入组合匹配系统热键或当前容器是安全 UIExtension THEN 组合键不分发 | 异常 |

### US-3: 遵循按键事件分发优先级

**作为** 组件与输入框架开发者，
**我想要** 组合键遵循 PreIME、Web 聚焦和重分发顺序，
**以便** 输入法、组件按键回调和组合键之间具有可预测的优先级。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `isPreIme=true` 且前置按键分发已消费事件 THEN 不再分发组合键 | 正常 |
| AC-3.2 | WHEN `isPreIme=true`、前置按键分发未消费且当前焦点不是 Web THEN 再尝试分发组合键 | 正常 |
| AC-3.3 | WHEN `isPreIme=true` 且当前焦点节点标签为 Web THEN 跳过组合键分发 | 边界 |
| AC-3.4 | WHEN 事件进入 `ReDispatch` THEN 先尝试组合键，再依次尝试 Tab 焦点移动、按键事件和 ESC 浮层移除 | 正常 |

### US-4: 清理组合键并随节点生命周期注销

**作为** 组件开发者，
**我想要** 在属性重置或节点离开主树时清理组合键，
**以便** 失效组件不再响应键盘输入。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN `value` 为空字符串且当前 EventHub 恰有一条组合键 THEN 清空该条记录 | 正常 |
| AC-4.2 | WHEN `value` 为空字符串但当前 EventHub 有两条或更多组合键 THEN `ClearSingleKeyboardShortcut` 不清除任何记录 | 边界 |
| AC-4.3 | WHEN attributeModifier 执行 reset-all THEN 清空 EventHub 全部组合键并从全局节点列表注销该节点 | 正常 |
| AC-4.4 | WHEN 节点从 PipelineContext 分离 THEN EventHub 自动从全局组合键节点列表注销该节点 | 正常 |
| AC-4.5 | WHEN 动态旧前端参数数量不是 2~3 THEN 调用直接返回，不新增或清理组合键 | 异常 |
| AC-4.6 | WHEN 动态旧前端参数类型非法或字符字符串长度不等于 1 THEN 通过空值路径执行单条清理语义 | 异常 |

### US-5: 跨版本和跨前端通道保持可识别的边界

**作为** ArkUI 框架维护者，
**我想要** 明确动态、静态、CJ 和内部 Modifier 通道的现有差异，
**以便** 回归测试和兼容性评估基于真实实现。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 使用动态 API 10+ THEN `keyboardShortcut(value, keys, action?)` 返回当前泛型组件 `T` | 正常 |
| AC-5.2 | WHEN 使用静态 API 23+ THEN `value` 和 `keys` 可为 `undefined` 且接口返回 `this` | 正常 |
| AC-5.3 | WHEN 静态桥收到缺失的 `value` 或 `keys` THEN 通过空值调用核心设置路径，继承单条清理语义 | 边界 |
| AC-5.4 | WHEN CJ 功能键入口的修饰键数量为 0 THEN 当前实现走空字符串清理路径，而不是注册无修饰键功能键 | 边界 |
| AC-5.5 | WHEN 使用内部 Node Modifier 设置组合键 THEN 可设置字符值和修饰键数组，但不携带 `action` 回调 | 边界 |
| AC-5.6 | WHEN 查询 `interfaces/native/` 的公开 Node C API THEN 此代码在 ace_engine 中未找到；该能力没有公开 C API 设置接口 | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.8 | R-1~R-9 | 已有实现 | 单测/源码审计 | `test/unittest/core/event/event_manager_test_ng.cpp:90`、`frameworks/core/components_ng/base/view_abstract.cpp:7390` |
| AC-2.1~AC-2.8 | R-10~R-15 | 已有实现 | 单测 | `test/unittest/core/event/event_manager_test_ng_three.cpp:435`、`test/unittest/core/event/gesture_event_hub_test_ng.cpp:1373` |
| AC-3.1~AC-3.4 | R-16~R-18 | 已有实现 | 单测 | `test/unittest/core/common/key_event_manager/key_event_manager_test.cpp:165` |
| AC-4.1~AC-4.6 | R-19~R-23 | 已有实现 | 单测/源码审计 | `test/unittest/core/event/event_hub_test_ng.cpp:1886`、`test/unittest/core/base/view_abstract_model_test_two_ng.cpp:857` |
| AC-5.1~AC-5.6 | R-24~R-29 | 已有实现 | SDK/源码审计 | SDK 声明、静态 Modifier 单测和 C API 搜索结果 |

## 规则定义

> 规则类型：**行为**、**边界**、**异常**、**恢复**。本规格固化当前实现；识别到的通道偏差只记录为风险，不在本次补录中修改。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 任意继承 `CommonMethod<T>` 的组件调用 `keyboardShortcut` | 组合键作为通用组件能力进入 ViewAbstract 注册链路 | 动态 API 10+ | AC-1.1, AC-5.1 |
| R-2 | 边界 | `value` 为字符串 | 动态旧前端仅接受长度等于 1 的字符串；空字符串或长度不等于 1 进入清理路径 | 字节长度必须为 1 | AC-1.1, AC-4.6 |
| R-3 | 行为 | `value` 为 `FunctionKey` | 将枚举转换为 `ESC`、`F1`~`F12`、`TAB` 或 `DPAD_*` 名称 | `TAB`/`DPAD_*` 自 API 12 | AC-1.2, AC-1.3 |
| R-4 | 边界 | 解析修饰键数组 | 最多接受 `CTRL`、`SHIFT`、`ALT` 各一次并编码为 bitmask | 数量上限为 3 | AC-1.4, AC-1.5 |
| R-5 | 异常 | 修饰键数量大于 3或任一修饰键重复 | `GetKeyboardShortcutKeys` 返回 0；字符键注册被拒绝 | 重复 `CTRL`/`SHIFT`/`ALT` 均非法 | AC-1.5 |
| R-6 | 边界 | 修饰键 bitmask 为 0 | 单字符不允许注册；功能键名称且输入修饰键数组为空时允许注册 | 字符与功能键分支不同 | AC-1.2, AC-1.6 |
| R-7 | 行为 | 同一节点注册不同触发组合 | EventHub 将多条 `KeyboardShortcut` 追加到 vector；全局节点弱引用只保留一项 | 节点级多记录 | AC-1.7 |
| R-8 | 行为 | EventHub 存储 `value` | 逐字符转换为大写后保存 `value`、bitmask 和回调 | ASCII 字符路径 | AC-1.1, AC-1.7 |
| R-9 | 边界 | 注册前检查全局重复 | 遍历已注册节点并按 `value` 与 bitmask 比较；命中则拒绝后续注册 | 输入比较发生在 EventHub 大写化之前 | AC-1.8 |
| R-10 | 行为 | 按键事件进入 `TriggerKeyboardShortcut` | 功能键/ESC 使用字符串相等；字符键使用输入代码字符串包含判断 | 最终仍需精确按键集合 | AC-2.1, AC-2.5 |
| R-11 | 行为 | 构造逻辑修饰键匹配集合 | 左右 Ctrl/Shift/Alt 均映射到同一逻辑修饰键，并遍历顺序排列 | `IsExactlyKey` 必须通过 | AC-2.1, AC-2.5 |
| R-12 | 行为 | 匹配项包含 `action` | 同步调用回调并立即返回 true | 首个成功项终止扫描 | AC-2.2 |
| R-13 | 行为 | 匹配项无 `action` | EventHub 存在可点击 GestureEventHub 时触发键盘快捷点击 | 不可点击时不消费 | AC-2.3, AC-2.4 |
| R-14 | 异常 | 事件不是 `DOWN`、节点非活动或 EventHub 禁用 | 跳过组合键触发 | 不产生回调或点击 | AC-2.6, AC-2.7 |
| R-15 | 异常 | 系统热键匹配或容器为安全 UIExtension | `DispatchKeyboardShortcut` 返回 false | 系统能力优先 | AC-2.8 |
| R-16 | 行为 | `isPreIme=true` | 先执行按键事件分发；未消费且非 Web 聚焦时再分发组合键 | 前置事件可拦截 | AC-3.1, AC-3.2 |
| R-17 | 边界 | 当前焦点 FrameNode 标签为 Web | 首次 PreIME 分发跳过组合键与焦点移动 | Web 自身处理输入 | AC-3.3 |
| R-18 | 行为 | `ReDispatch` 收到按键事件 | 顺序为组合键、Tab、按键事件、ESC 浮层处理 | 组合键优先 | AC-3.4 |
| R-19 | 恢复 | 空字符串进入 `ClearSingleKeyboardShortcut` 且 vector 大小为 1 | 清空唯一记录 | 不主动注销全局节点弱引用 | AC-4.1 |
| R-20 | 边界 | 空字符串进入 `ClearSingleKeyboardShortcut` 且 vector 大小不等于 1 | 保持原 vector 不变 | 0 条或 2 条以上均不清理 | AC-4.2 |
| R-21 | 恢复 | 调用 `ResetKeyboardShortcutAll` | 清空 vector 并按 nodeId 从全局列表删除节点 | 全量清理 | AC-4.3 |
| R-22 | 恢复 | EventHub 与 PipelineContext 分离 | 自动调用 `DelKeyboardShortcutNode` | 防止离树节点继续分发 | AC-4.4 |
| R-23 | 异常 | 动态旧前端参数数量或类型不合法 | 数量非法直接返回；类型/字符串长度非法走空值单条清理 | 不抛出错误码 | AC-4.5, AC-4.6 |
| R-24 | 行为 | 动态 API 声明 | `keyboardShortcut(value: string \| FunctionKey, keys: Array<ModifierKey>, action?: () => void): T` | API 10；Atomic Service 自 API 11 | AC-5.1 |
| R-25 | 行为 | 静态 API 声明 | `keyboardShortcut(value: string \| FunctionKey \| undefined, keys: Array<ModifierKey> \| undefined, action?: () => void): this` | API 23 static | AC-5.2 |
| R-26 | 恢复 | 静态桥收到空 Optional | 调用核心空值设置路径 | 继承 R-19/R-20 | AC-5.3 |
| R-27 | 边界 | CJ 功能键入口 `size == 0` | 调用空字符串设置路径 | 与 ArkTS 功能键可无修饰键的契约不同 | AC-5.4 |
| R-28 | 边界 | 内部 Node Modifier 设置组合键 | 传入字符和修饰键数组，回调固定为 null | InnerApi，不是公开 C API | AC-5.5 |
| R-29 | 边界 | 检查公开 Native Node API | `interfaces/native/` 未提供组合键设置函数、属性或事件注册项 | 此代码在 ace_engine 中未找到 | AC-5.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-2~R-6, AC-1.1~AC-1.6 | 单测 | 字符长度、功能键、0~3 个修饰键、重复和超限输入 |
| VM-2 | R-7~R-9, AC-1.7~AC-1.8 | 单测/源码审计 | 多快捷键、节点去重、全局触发去重和大小写存储 |
| VM-3 | R-10~R-13, AC-2.1~AC-2.5 | 单测 | 精确按键集合、左右修饰键、回调优先和点击降级 |
| VM-4 | R-14~R-15, AC-2.6~AC-2.8 | 单测/集成测试 | DOWN 限制、节点状态、系统热键和安全 UIExtension |
| VM-5 | R-16~R-18, AC-3.1~AC-3.4 | 单测 | PreIME 消费、Web 跳过和 ReDispatch 顺序 |
| VM-6 | R-19~R-23, AC-4.1~AC-4.6 | 单测 | 单条清理、全量清理、离树注销和非法输入 |
| VM-7 | R-24~R-29, AC-5.1~AC-5.6 | SDK/源码审计 | API 10/12/23、静态 Optional、CJ 和 InnerApi 差异 |
| VM-8 | AC-1.1~AC-5.6 | XTS/集成测试 | 外接键盘端到端注册、匹配、触发和清理 |

## API 变更分析

> 本特性为已有能力补录，不新增或修改 API。下表列出现有接口开放范围。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `keyboardShortcut(value: string \| FunctionKey, keys: Array<ModifierKey>, action?: () => void): T` | Public | 单字符/功能键、修饰键数组、可选回调 | 当前组件 `T` | N/A | 动态 ArkTS 组件组合键，API 10 | AC-1.1~AC-4.6, AC-5.1 |
| `keyboardShortcut(value: string \| FunctionKey \| undefined, keys: Array<ModifierKey> \| undefined, action?: () => void): this` | Public | 可选字符/功能键、可选修饰键数组、可选回调 | `this` | N/A | 静态 ArkTS 组件组合键，API 23 | AC-5.2, AC-5.3 |
| `ModifierKey` | Public | `CTRL`、`SHIFT`、`ALT` | 枚举值 | N/A | 逻辑修饰键枚举，动态 API 10、静态 API 23 | AC-1.1, AC-1.4 |
| `FunctionKey` | Public | `ESC`、`F1`~`F12`、`TAB`、`DPAD_*` | 枚举值 | N/A | 功能键枚举；`TAB`/`DPAD_*` 动态 API 12 | AC-1.2, AC-1.3 |
| 公开 C API | N/A | N/A | N/A | N/A | 此代码在 ace_engine 中未找到 | AC-5.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 已有能力补录，不产生接口变更 | 无需迁移 | AC-5.1~AC-5.6 |

## 接口规格

### 接口定义

**动态 ArkTS `CommonMethod.keyboardShortcut`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `keyboardShortcut(value: string \| FunctionKey, keys: Array<ModifierKey>, action?: () => void): T` |
| 返回值 | `T` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A；非法输入通过忽略或清理处理 |
| 关联 AC | AC-1.1~AC-4.6, AC-5.1 |

**静态 ArkTS `CommonMethod.keyboardShortcut`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `keyboardShortcut(value: string \| FunctionKey \| undefined, keys: Array<ModifierKey> \| undefined, action?: () => void): this` |
| 返回值 | `this` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A；`undefined` 进入重置路径 |
| 关联 AC | AC-5.2, AC-5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `value` | `string \| FunctionKey`；静态版可为 `undefined` | 动态是；静态否 | 无 | 字符串路径长度必须等于 1；空字符串表示清理；功能键按枚举映射 |
| `keys` | `Array<ModifierKey>`；静态版可为 `undefined` | 动态是；静态否 | 无 | 仅 `CTRL`/`SHIFT`/`ALT`，最多 3 个且不可重复；仅功能键可为空数组 |
| `action` | `() => void` | 否 | `undefined` | 有回调时优先执行；无回调时尝试组件点击 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法字符或功能键组合 | 注册到 EventHub 并加入全局节点列表 | AC-1.1~AC-1.8 |
| 2 | `DOWN` 且精确匹配 | 执行回调或点击降级 | AC-2.1~AC-2.5 |
| 3 | 系统/安全/禁用条件 | 不触发 | AC-2.6~AC-2.8 |
| 4 | PreIME 或 ReDispatch | 按既定顺序分发 | AC-3.1~AC-3.4 |
| 5 | 空字符串、reset-all 或节点分离 | 按单条/全量/生命周期规则清理 | AC-4.1~AC-4.6 |
| 6 | 不同 API/前端通道 | 遵循对应版本签名与现有通道差异 | AC-5.1~AC-5.6 |

## 兼容性声明

- **已有 API 行为变更:** 否，本规格补录当前实现。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；组合键仅保存在运行期 EventHub 中。
- **最低支持版本:** 动态 API 10；Atomic Service 自 API 11；静态 API 23。
- **API 版本号策略:** `ModifierKey`、`ESC` 和 `F1`~`F12` 按 API 10 标注；`TAB` 和 `DPAD_*` 按 API 12 标注；静态声明按 API 23 标注。

| 版本/通道 | 现有行为差异 | 证据 |
|-----------|--------------|------|
| 动态 API 10 | 支持单字符、`ESC`、`F1`~`F12` 和 `CTRL`/`SHIFT`/`ALT` | `common.d.ts:24679`、`enums.d.ts:3657` |
| 动态 API 12 | `FunctionKey` 增加 `TAB` 和四个方向键 | `enums.d.ts:3854` |
| 静态 API 23 | `value`/`keys` 支持 `undefined`，返回 `this` | `common.static.d.ets:13781` |
| 动态 attributeModifier | 修饰键 vector 先按长度构造后又追加，可能引入默认 `CTRL` 并使长度翻倍 | `arkts_native_common_bridge.cpp:7730` |
| CJ 功能键入口 | `size == 0` 时清理，不能按 ArkTS 契约注册无修饰键功能键 | `cj_view_abstract_ffi.cpp:1805` |
| InnerApi Node Modifier | 可设置 value/keys，但不传 action | `node_common_modifier.cpp:6052` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 通用属性分层 | SDK/前端桥只做类型转换，核心校验和注册集中在 ViewAbstract/KeyEventManager | AC-1.1~AC-1.8 |
| 节点局部存储 | 组合键数据归属 EventHub，不引入持久化或 Layout/Render 属性 | AC-1.7, AC-4.1~AC-4.4 |
| 全局分发管理 | KeyEventManager 只保存 FrameNode 弱引用并在事件到达时读取 EventHub | AC-2.1~AC-3.4 |
| 系统快捷键优先 | 系统热键和安全 UIExtension 不得被应用组合键覆盖 | AC-2.8 |
| 生命周期注销 | reset-all 和节点分离必须删除全局弱引用 | AC-4.3, AC-4.4 |
| API/ABI 边界 | 本次不新增或修改 Public/System/Native API | AC-5.1~AC-5.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增量化指标；全局节点按注册顺序扫描，首个成功触发后返回 | 单测/性能回归 | `key_event_manager.cpp:488` |
| 功耗 | 不新增周期任务，仅在按键事件到达时处理 | 源码审计 | `key_event_manager.cpp:488` |
| 内存 | 全局列表保存 WeakPtr；EventHub 持有组合键 vector 和回调 | 单测/源码审计 | `key_event_manager.h:80`、`event_hub.h:61` |
| 安全 | 安全 UIExtension 和系统热键不得触发应用组合键 | 单测/集成测试 | `key_event_manager.cpp:183`、`key_event_manager.cpp:488` |
| 可靠性 | 非活动、禁用、失效弱引用节点均跳过；离树节点注销 | 单测 | `key_event_manager.cpp:128`、`event_hub.cpp:51` |
| 可测试性 | 参数、存储、分发、清理和桥接均有独立单测入口 | 单测 | `test/unittest/core/event/`、`test/unittest/capi/modifiers/` |
| 自动化维测 | 沿用 `ACE_KEYBOARD` 日志标签，不新增埋点 | 日志审计 | `event_hub.cpp:1130`、`key_event_manager.cpp:205` |
| 定界定位 | 通过 value、keys、节点状态、分发入口和回调路径定位 | 单测/日志 | `event_hub.cpp:1130` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无设备专属分支；需要外接或可产生 KeyEvent 的键盘设备 | 遵循统一匹配与分发规则 | 外接键盘集成测试 | `key_event_manager.cpp:488` |
| 平板 | 无差异 | 同上 | 外接键盘集成测试 | 同上 |
| 折叠屏 | 折叠状态不参与组合键判断 | 窗口形态变化不得改变已注册触发组合 | 多窗口/折叠集成测试 | 同上 |
| 2-in-1 | 无实现分支差异，键盘为主要输入形态 | 系统热键仍优先 | 键盘集成测试 | `key_event_manager.cpp:183` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 无 `action` 时复用组件点击路径，不新增无障碍语义 | AC-2.3 |
| 大字体 | 否 | 不涉及布局与文本度量 | — |
| 深色模式 | 否 | 不涉及绘制或颜色 | — |
| 多窗口/分屏 | 是 | 注册数据归属各 PipelineContext/EventManager，按当前容器分发 | AC-2.8, AC-4.4 |
| 多用户 | 否 | 无持久化或用户数据 | — |
| 版本升级 | 是 | API 10/12/23 差异必须保留 | AC-5.1~AC-5.3 |
| 生态兼容 | 是 | 系统热键、Web 聚焦、CJ 和静态前端差异需要回归 | AC-2.8, AC-3.3, AC-5.2~AC-5.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 组件组合键注册与触发
  作为 ArkUI 应用开发者和键盘用户
  我想要为组件配置可预测的组合键
  以便快速触发组件操作且不覆盖系统输入规则

  Scenario: 字符组合键执行自定义回调
    Given 组件已注册字符 A、修饰键 CTRL 和 action
    When 收到 pressedCodes 精确为 CTRL+A 的 DOWN 事件
    Then action 被调用一次
    And 组合键分发返回已消费

  Scenario: 功能键无需修饰键
    Given 组件已注册 FunctionKey.F1 且 keys 为空
    When 收到仅包含 F1 的 DOWN 事件
    Then 该组合键被触发

  Scenario: 额外按键导致不匹配
    Given 组件已注册 CTRL+A
    When 收到 CTRL+SHIFT+A 的 DOWN 事件
    Then IsExactlyKey 判定失败
    And CTRL+A 的 action 不被调用

  Scenario: 无回调时触发组件点击
    Given 组件已注册 SHIFT+A 且未提供 action
    And 组件 GestureEventHub 可点击
    When 收到 SHIFT+A 的 DOWN 事件
    Then KeyBoardShortCutClick 触发组件点击

  Scenario: 多条组合键下空字符串不执行全量清理
    Given 同一 EventHub 已保存 CTRL+A 和 SHIFT+Q
    When 通过空字符串进入 ClearSingleKeyboardShortcut
    Then 两条组合键均保留
    When 再调用 ResetKeyboardShortcutAll
    Then 两条组合键被清空且节点从全局列表注销

  Scenario: 前置按键事件拦截组合键
    Given 当前事件 isPreIme 为 true
    And onKeyPreIme 已消费事件
    When KeyEventManager 处理该事件
    Then keyboardShortcut 不再触发

  Scenario: 系统热键优先
    Given 输入组合存在于系统热键列表
    When DispatchKeyboardShortcut 收到该 DOWN 事件
    Then 应用组件组合键不触发
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（“快速”“稳定”“尽可能”等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "keyboardShortcut 从 ArkTS CommonMethod 到 ViewAbstract、EventHub、KeyEventManager 的注册与分发链路"
  - repo: "openharmony/interface_sdk-js"
    query: "keyboardShortcut、ModifierKey、FunctionKey 的动态 API 10/12 与静态 API 23 声明差异"
```

**关键文档：** `specs/04-common-capability/04-common-events/04-component-shortcuts/design.md`
