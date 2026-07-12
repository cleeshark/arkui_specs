# 特性规格
## 概述
| 字段 | 内容 |
|------|------|
| 特性名称 | ImageAnimator 事件回调与多范式接口 |
| 特性编号 | Func-05-08-02-Feat-03 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | Dynamic API 7+；ImageAnimatorModifier Dynamic API 12+/20 crossplatform；Static API 23+；Static style builder API 26+；NDK API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 补录 `onStart/onPause/onRepeat/onCancel/onFinish` 事件规格 | 覆盖 SDK、EventHub、ControlledAnimator listener 和 reset 行为。 |
| ADDED | 补录 ArkTS dynamic/static modifier 与 static builder | 覆盖 `ImageAnimatorModifier`、static generated modifier 和 API 26 style builder。 |
| ADDED | 补录 NDK node 类型、属性和 async event 映射 | 覆盖 `ARKUI_NODE_IMAGE_ANIMATOR`、`NODE_IMAGE_ANIMATOR_EVENT_ON_*`。 |

## 输入文档
- 设计文档: `arkui-specs/05-ui-components/08-image-components/02-image-animator/design.md`
- 动态 SDK: `/srv/workspace/openharmony_master_default_20260709175431_huawei_a631ac547/code/interface/sdk-js/api/@internal/component/ets/image_animator.d.ts:342`
- 动态 modifier SDK: `/srv/workspace/openharmony_master_default_20260709175431_huawei_a631ac547/code/interface/sdk-js/api/arkui/ImageAnimatorModifier.d.ts:24`
- 静态 SDK: `/srv/workspace/openharmony_master_default_20260709175431_huawei_a631ac547/code/interface/sdk-js/api/arkui/component/imageAnimator.static.d.ets:225`
- 静态 modifier SDK: `/srv/workspace/openharmony_master_default_20260709175431_huawei_a631ac547/code/interface/sdk-js/api/arkui/ImageAnimatorModifier.static.d.ets:24`
- EventHub: `frameworks/core/components_ng/pattern/image_animator/image_animator_event_hub.h:24`
- Model/Event implementation: `frameworks/core/components_ng/pattern/image_animator/image_animator_model_ng.cpp:116`
- Pattern event binding: `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:446`
- Dynamic bridge: `frameworks/core/components_ng/pattern/image_animator/bridge/arkts_native_image_animator_bridge.cpp:505`
- Dynamic/static modifier: `frameworks/core/components_ng/pattern/image_animator/bridge/image_animator_dynamic_modifier.cpp:327`；`frameworks/core/components_ng/pattern/image_animator/bridge/image_animator_static_modifier.cpp:194`
- NDK/native event: `interfaces/native/native_node.h:11796`；`frameworks/core/interfaces/native/node/node_api.cpp:700`
- 测试参考: `test/unittest/interfaces/native_node_test.cpp:2900`；`test/unittest/interfaces/native_node_test.cpp:3154`

## 用户故事
### US-1: 开发者监听 ImageAnimator 播放事件
As a ArkUI 开发者, I want 注册开始、暂停、重复、取消和完成回调, So that 应用能响应图片动画生命周期变化。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 注册 `onStart`, THEN animator 开始播放时调用对应 callback。 | 正常 |
| AC-1.2 | WHEN 注册 `onPause`, THEN animator 暂停时调用对应 callback。 | 正常 |
| AC-1.3 | WHEN 注册 `onRepeat`, THEN animator 重复播放时调用对应 callback。 | 正常 |
| AC-1.4 | WHEN 注册 `onCancel`, THEN animator 回到初始状态或 cancel 时调用对应 callback。 | 正常 |
| AC-1.5 | WHEN 注册 `onFinish`, THEN animator 完成或停止时调用对应 callback，内部映射到 stop listener。 | 正常 |
| AC-1.6 | WHEN 动态 ArkTS event 参数为 undefined、null 或非 function, THEN bridge reset 对应事件。 | 异常 |

### US-2: NDK 开发者使用 native node 事件
As a NDK 开发者, I want 通过 `NODE_IMAGE_ANIMATOR_EVENT_ON_*` 注册事件, So that native node 场景可以接收 ImageAnimator 生命周期事件。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 创建 native node 类型 `ARKUI_NODE_IMAGE_ANIMATOR`, THEN node type id 为 19。 | 正常 |
| AC-2.2 | WHEN 注册 native `NODE_IMAGE_ANIMATOR_EVENT_ON_START/PAUSE/REPEAT/CANCEL/FINISH`, THEN event subKind 分别映射到 ImageAnimator ext event setter。 | 正常 |
| AC-2.3 | WHEN native ImageAnimator event 触发, THEN `ArkUI_NodeEvent` 的 component event 不携带额外 payload。 | 正常 |
| AC-2.4 | WHEN reset native ImageAnimator event, THEN reset 分发到对应 reset handler。 | 正常 |
| AC-2.5 | WHEN event subKind 超出 ImageAnimator event handler 表长度, THEN native node 分发记录未实现并返回，不调用空 handler。 | 异常 |

### US-3: 静态 ArkTS 与 modifier 场景构建 ImageAnimator
As a ArkTS static 或 attribute modifier 使用者, I want 使用静态 builder 和 ImageAnimatorModifier, So that 编译时范式能复用同一组件行为。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN static API 23+ 调用 `ImageAnimator()`, THEN 返回 `ImageAnimatorAttribute` 并创建 static FrameNode。 | 正常 |
| AC-3.2 | WHEN static API 26+ 调用 `ImageAnimator(style)`, THEN SDK 要求 style 过程开始调用 `setImageAnimatorOptions`、结束调用 `applyAttributeFinish`；native `setImageAnimatorOptions` 本身无实现。 | 正常 |
| AC-3.3 | WHEN 使用 dynamic `ImageAnimatorModifier`, THEN `applyNormalAttribute` 可接收 `ImageAnimatorAttribute` 实例应用普通属性。 | 正常 |
| AC-3.4 | WHEN static modifier 注册事件且 callback undefined, THEN static modifier 将对应 EventHub callback 置空。 | 正常 |

## 验收追溯
| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-05-08-02-03 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:451` |
| AC-1.2 | R-2 | TASK-05-08-02-03 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:462` |
| AC-1.3 | R-3 | TASK-05-08-02-03 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:467` |
| AC-1.4 | R-4 | TASK-05-08-02-03 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:472` |
| AC-1.5 | R-5 | TASK-05-08-02-03 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_model_ng.cpp:152`; `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:457` |
| AC-1.6 | R-6 | TASK-05-08-02-03 | bridge 源码审查 | `frameworks/core/components_ng/pattern/image_animator/bridge/arkts_native_image_animator_bridge.cpp:505` |
| AC-2.1 | R-7 | TASK-05-08-02-03 | NDK header 审查 | `interfaces/native/native_node.h:92` |
| AC-2.2 | R-8 | TASK-05-08-02-03 | native node 源码审查 + native UT | `frameworks/core/interfaces/native/node/node_api.cpp:700`; `test/unittest/interfaces/native_node_test.cpp:2900` |
| AC-2.3 | R-9 | TASK-05-08-02-03 | NDK header 审查 | `interfaces/native/native_node.h:11790` |
| AC-2.4 | R-10 | TASK-05-08-02-03 | native node 源码审查 | `frameworks/core/interfaces/native/node/node_api.cpp:951` |
| AC-2.5 | R-11 | TASK-05-08-02-03 | native node 源码审查 | `frameworks/core/interfaces/native/node/node_api.cpp:1226` |
| AC-3.1 | R-12 | TASK-05-08-02-03 | SDK + static model 源码审查 | `/interface/sdk-js/api/arkui/component/imageAnimator.static.d.ets:292`; `frameworks/core/components_ng/pattern/image_animator/image_animator_model_static.cpp:31` |
| AC-3.2 | R-13 | TASK-05-08-02-03 | SDK + static modifier 源码审查 | `/interface/sdk-js/api/arkui/component/imageAnimator.static.d.ets:304`; `frameworks/core/components_ng/pattern/image_animator/bridge/image_animator_static_modifier.cpp:113` |
| AC-3.3 | R-14 | TASK-05-08-02-03 | SDK 审查 | `/interface/sdk-js/api/arkui/ImageAnimatorModifier.d.ts:45` |
| AC-3.4 | R-15 | TASK-05-08-02-03 | static modifier 源码审查 | `frameworks/core/components_ng/pattern/image_animator/bridge/image_animator_static_modifier.cpp:194` |

## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `ImageAnimatorEventHub::startEvent_` 非空且 Pattern 更新事件绑定 | `ControlledAnimator::AddStartListener` 注册 callback。 | `UpdateEventCallback` 会先 ClearAllListeners。 | AC-1.1 |
| R-2 | 行为 | `pauseEvent_` 非空且 Pattern 更新事件绑定 | 注册 pause listener。 | Pause 可由 state 或 visible area 触发。 | AC-1.2 |
| R-3 | 行为 | `repeatEvent_` 非空且 Pattern 更新事件绑定 | 注册 repeat listener。 | 具体 repeat 时机由 ControlledAnimator 管理。 | AC-1.3 |
| R-4 | 行为 | `cancelEvent_` 非空且 Pattern 更新事件绑定 | 注册 cancel listener。 | Initial/cancel 路径可触发。 | AC-1.4 |
| R-5 | 行为 | `onFinish` 设置 callback | ModelNG 写入 stop event，Pattern 注册 stop listener。 | SDK 描述为完成或停止时触发。 | AC-1.5 |
| R-6 | 异常 | 动态 event 参数 undefined/null/非 function | bridge 调用 reset 对应事件并返回 undefined。 | 所有五个事件遵循同类校验。 | AC-1.6 |
| R-7 | 行为 | NDK 创建 ImageAnimator node | 使用 `ARKUI_NODE_IMAGE_ANIMATOR = 19`。 | node type 与属性 scope 都以 19 为基础。 | AC-2.1 |
| R-8 | 行为 | native event 注册 subKind 0 至 4 | 按 start、pause、repeat、cancel、finish 顺序分发到 ext setter。 | handler 表长度为 5。 | AC-2.2 |
| R-9 | 行为 | native ImageAnimator event 回调发生 | `ArkUI_NodeComponentEvent` 不包含参数。 | native header 对五个事件均说明无参数。 | AC-2.3 |
| R-10 | 行为 | native event reset subKind 0 至 4 | 按同样顺序分发到 reset handler。 | reset handler 表长度为 5。 | AC-2.4 |
| R-11 | 异常 | native event subKind 超出 handler 表长度 | 记录未实现日志并返回，不调用 handler。 | 适用于 set 和 reset 分发。 | AC-2.5 |
| R-12 | 行为 | static API `ImageAnimator()` | static model 创建 FrameNode、内部 Image 子节点，并设置 Pattern static 标志。 | static API since 23。 | AC-3.1 |
| R-13 | 行为 | static API `ImageAnimator(style)` | SDK 要求 style builder 流程调用 `setImageAnimatorOptions`；native `SetImageAnimatorOptionsImpl` 无副作用。 | API since 26 staticonly。 | AC-3.2 |
| R-14 | 行为 | dynamic `ImageAnimatorModifier` | modifier 继承 `ImageAnimatorAttribute` 并可实现 `applyNormalAttribute`。 | since 12；crossplatform since 20 dynamic。 | AC-3.3 |
| R-15 | 行为 | static event callback optional 为空 | static modifier 调用 ModelNG 将对应 callback 置空。 | onStart/onPause/onRepeat/onCancel/onFinish 均适用。 | AC-3.4 |

## 验证映射
| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1 至 AC-1.6 | SDK + EventHub/Pattern/bridge 源码审查 | 事件签名、callback 存储、listener 注册、invalid callback reset。 |
| VM-2 | AC-2.1 至 AC-2.5 | NDK header + node_api 源码审查 + native UT | node type、event enum、event subKind 映射和 reset。 |
| VM-3 | AC-3.1, AC-3.2 | static SDK + static modifier/model 源码审查 | static builder 和 `setImageAnimatorOptions` 空实现。 |
| VM-4 | AC-3.3, AC-3.4 | modifier SDK + static modifier 源码审查 | dynamic/static modifier 行为和 undefined callback reset。 |

## API 变更分析
### 新增 API
| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|--------|
| `onStart(event: () => void)` | Public | callback | `ImageAnimatorAttribute` / `this` | N/A | 动画开始播放事件。 | AC-1.1 |
| `onPause(event: () => void)` | Public | callback | `ImageAnimatorAttribute` / `this` | N/A | 动画暂停事件。 | AC-1.2 |
| `onRepeat(event: () => void)` | Public | callback | `ImageAnimatorAttribute` / `this` | N/A | 动画重复播放事件。 | AC-1.3 |
| `onCancel(event: () => void)` | Public | callback | `ImageAnimatorAttribute` / `this` | N/A | 动画回到初始状态事件。 | AC-1.4 |
| `onFinish(event: () => void)` | Public | callback | `ImageAnimatorAttribute` / `this` | N/A | 动画完成或停止事件。 | AC-1.5 |
| `ImageAnimatorModifier` | Public | `applyNormalAttribute?(instance)` | void | N/A | attribute modifier 扩展点。 | AC-3.3 |
| `ImageAnimator(style: CustomBuilderT<ImageAnimatorAttribute>)` | Public staticonly | style builder | `ImageAnimatorAttribute` | N/A | 静态范式 style builder 构造入口。 | AC-3.2 |
| `NODE_IMAGE_ANIMATOR_EVENT_ON_*` | Public NDK | native node event registration | `ArkUI_ErrorCode` | event subKind 越界不注册 | NDK ImageAnimator 事件。 | AC-2.2 |

### 变更/废弃 API
| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|--------|
| N/A | N/A | 本 Feat 补录已有事件和多范式接口，不新增或废弃 API。 | N/A | N/A |

## 接口规格
### 接口定义
**ImageAnimator event callbacks**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onStart(event: () => void)`, `onPause(event: () => void)`, `onRepeat(event: () => void)`, `onCancel(event: () => void)`, `onFinish(event: () => void)` |
| 返回值 | `ImageAnimatorAttribute` / static `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 至 AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `event` | `() => void` / static `(() => void) | undefined` | 动态是；静态否 | 无 callback | 动态 undefined/null/non-function reset；static undefined 置空。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | start/pause/repeat/cancel listener 触发 | 调用对应 EventHub callback。 | AC-1.1 至 AC-1.4 |
| 2 | stop listener 触发 | 调用 `onFinish` callback。 | AC-1.5 |
| 3 | 动态 event 入参非法 | reset 对应 callback。 | AC-1.6 |

**Native ImageAnimator events**

| 属性 | 值 |
|------|-----|
| 函数签名 | `NODE_IMAGE_ANIMATOR_EVENT_ON_START`, `ON_PAUSE`, `ON_REPEAT`, `ON_CANCEL`, `ON_FINISH` |
| 返回值 | native node event registration/reset 结果 |
| 开放范围 | Public NDK |
| 错误码 | subKind 越界时分发不调用 handler |
| 关联 AC | AC-2.1 至 AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `nodeType` | `ArkUI_NodeType` | 是 | N/A | 必须为 `ARKUI_NODE_IMAGE_ANIMATOR`。 |
| `eventType` | `ArkUI_NodeEventType` | 是 | N/A | event id 19000 至 19004。 |
| `extraParam` | pointer/intptr | 否 | 0 | 通过 ext event setter 传递，payload 不包含额外业务数据。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 注册 event subKind 0 | 路由到 `SetImageAnimatorOnStart`。 | AC-2.2 |
| 2 | reset event subKind 4 | 路由到 `ResetImageAnimatorOnFinish`。 | AC-2.4 |
| 3 | subKind 超表长 | 不注册 handler。 | AC-2.5 |

**Static builder and modifier**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ImageAnimator(): ImageAnimatorAttribute`; `ImageAnimator(style: CustomBuilderT<ImageAnimatorAttribute>): ImageAnimatorAttribute`; `ImageAnimatorModifier` |
| 返回值 | `ImageAnimatorAttribute` 或 modifier void |
| 开放范围 | Public static / Public modifier |
| 错误码 | N/A |
| 关联 AC | AC-3.1 至 AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `style` | `CustomBuilderT<ImageAnimatorAttribute>` | API 26 style overload 是 | 无 | SDK 要求开始调用 `setImageAnimatorOptions`，结束调用 `applyAttributeFinish`。 |
| `modifier` | `ImageAnimatorModifier` | 否 | 无 | dynamic modifier 可实现 `applyNormalAttribute`。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | static construct | 创建 static FrameNode 和内部 Image 子节点。 | AC-3.1 |
| 2 | `setImageAnimatorOptions` 被调用 | native static 实现无副作用。 | AC-3.2 |
| 3 | static event optional 为空 | 清空对应 EventHub callback。 | AC-3.4 |

## 兼容性声明
- **已有 API 行为变更:** 否。本 Feat 仅记录已有事件和多范式接口。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic event API 7；dynamic modifier API 12；static API 23；static style builder API 26；NDK API 12。
- **API 版本号策略:** 以 SDK `@since`、`@crossplatform`、`@staticonly` 和 NDK header 注释为准。

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 事件存储在 EventHub | Pattern 不直接保存用户 callback，统一从 `ImageAnimatorEventHub` 读取。 | AC-1.1 至 AC-1.5 |
| `onFinish` 是 stop event | 没有独立 finish 字段，`onFinish` 绑定 stop listener。 | AC-1.5 |
| native event 无 payload | NDK header 对五个事件均声明 component event 不包含参数。 | AC-2.3 |
| static options 无副作用 | `setImageAnimatorOptions` 是 static builder 流程占位。 | AC-3.2 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 事件注册只在首次 OnModifyDone 更新；static Pattern 每次 OnModifyDone 可更新事件以适配静态范式。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:362` |
| 功耗 | 事件本身不启动额外定时器。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:446` |
| 内存 | callback 以 `std::function<void()>` 保存，reset 置空。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_event_hub.h:24` |
| 安全 | 动态 bridge 非 function 参数 reset，不执行非函数对象。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/bridge/arkts_native_image_animator_bridge.cpp:513` |
| 可靠性 | 更新事件前清除旧 animator listeners，避免重复回调。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:451` |
| 可测试性 | native event 类型双向转换已有 UT。 | 单测审查 | `test/unittest/interfaces/native_node_test.cpp:2900` |
| 自动化维测 | 事件无属性输出；通过 native event UT 和 callback setter 源码验证。 | 源码审查 | `frameworks/core/interfaces/native/node/node_api.cpp:700` |
| 定界定位 | 事件入口集中在 bridge setter、ModelNG setter 和 `UpdateEventCallback`。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_model_ng.cpp:116` |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 事件和 modifier 行为与设备无关。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:446` |
| 平板 | 无差异 | 事件和 modifier 行为与设备无关。 | 源码审查 | 同上 |
| 折叠屏 | 无差异 | 事件和 modifier 行为与设备无关。 | 源码审查 | 同上 |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 本 Feat 不新增无障碍事件。 | N/A |
| 大字体 | 否 | 不涉及文本。 | N/A |
| 深色模式 | 否 | 事件和 modifier 不改变颜色策略。 | N/A |
| 多窗口/分屏 | 是 | 可见性导致的 pause/resume 可能触发 onPause/onStart/finish 类事件，但具体可见性规则由 Feat-02 定义。 | AC-1.2 |
| 多用户 | 否 | 不涉及用户数据。 | N/A |
| 版本升级 | 是 | static API 23/26 与 dynamic modifier 12/20 版本边界需保留。 | AC-3.1 至 AC-3.3 |
| 生态兼容 | 是 | NDK 事件 payload 为空，不能在后续设计中假定有事件参数。 | AC-2.3 |

## 行为场景（可选，Gherkin）
Feature: ImageAnimator events and interfaces
  作为 ArkUI 或 NDK 开发者
  我想要注册 ImageAnimator 生命周期事件并使用多范式接口
  以便 在动态、静态和 native node 场景中获得一致生命周期通知

  Scenario: onFinish is backed by stop listener
    Given ImageAnimator has an onFinish callback
    When ModelNG stores the callback
    Then it is stored as stop event
    When Pattern updates event callbacks
    Then the callback is registered as ControlledAnimator stop listener

  Scenario: native event subKind routes to ext callback
    Given native ImageAnimator event subKind is ON_FINISH
    When node_api dispatches component async event
    Then it calls SetImageAnimatorOnFinish ext handler
    And the component event has no payload

## Spec 自审清单
- [x] 无占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references
```yaml
context-queries:
  - repo: "OpenHarmony/foundation_arkui_ace_engine"
    query: "ImageAnimator onStart onPause onRepeat onCancel onFinish NDK event modifier static builder"
```

**关键文档:** `docs/pattern/image_animator/Image_Animator_Knowledge_Base.md`
