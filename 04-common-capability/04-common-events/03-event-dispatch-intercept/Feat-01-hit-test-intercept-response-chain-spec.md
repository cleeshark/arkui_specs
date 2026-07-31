# 特性规格

> Func-04-04-03-Feat-01 命中测试、拦截与响应链构建：固化 NG 事件入口、递归命中、动态拦截、子节点定向转发、分发目标链与响应链构建，以及 ArkTS/C API 多通道行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 命中测试、拦截与响应链构建 |
| 特性编号 | Func-04-04-03-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 7–26，Static API 23 起，C API 12–22 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 命中测试主链规格 | 补录 `PipelineContext`、`EventManager`、`FrameNode` 的现有行为 |
| ADDED | ArkTS/C API 拦截接口规格 | 补录设置、重置、非法值和版本差异 |
| ADDED | 双链模型与恢复规格 | 区分 `TouchTestResult` 与 `ResponseLinkResult`，补录超时重测 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/03-event-dispatch-intercept/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核验 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets` | 已核验 |
| C API | `interfaces/native/native_node.h`, `interfaces/native/ui_input_event.h`, `interfaces/native/native_gesture.h` | 已核验 |
| 核心实现 | `frameworks/core/pipeline_ng/pipeline_context.cpp`, `frameworks/core/common/event_manager.cpp`, `frameworks/core/components_ng/base/frame_node.cpp` | 已核验 |
| 关联规格 | `specs/04-common-capability/04-common-events/06-gesture-capability/Feat-04-gesture-intercept-spec.md` | 仅承接手势识别与竞争语义 |

---

## 用户故事

### US-1: 在触摸序列开始时建立稳定目标链

**作为** ArkUI 事件框架,
**我想要** 在触摸按下时完成命中测试并缓存目标链,
**以便** 同一指针序列的后续事件发送给一致的目标集合。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `PipelineContext` 收到 `TouchType::DOWN` THEN 构造包含输入源、工具类型和原始事件的 `TouchRestrict` 并调用 `EventManager::TouchTest` | 正常 |
| AC-1.2 | WHEN 同一指针 ID 后续收到 MOVE/UP/CANCEL 且目标链有效 THEN 不重新执行常规命中测试并复用 `touchTestResults_[id]` | 正常 |
| AC-1.3 | WHEN `EventManager` 中不存在当前指针 ID 的目标链 THEN `DispatchTouchEvent` 返回 false，且不向任意目标分发 | 异常 |
| AC-1.4 | WHEN 输入源变化或仲裁状态超过清理阈值仍未就绪 THEN 旧链先收到伪造 CANCEL，框架清理状态并重新执行完整命中测试 | 异常 |

### US-2: 按渲染层级和响应区域递归命中

**作为** 应用开发者,
**我想要** 事件按照实际可见层级、变换和响应区域命中组件,
**以便** 叠层、越界子节点和不同输入工具得到可预测结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 节点处于 inactive 或 EventHub disabled 状态 THEN 该节点返回 `OUT_OF_REGION`，不收集自身事件目标 | 正常 |
| AC-2.2 | WHEN 多个子节点在同一区域重叠 THEN 按 `frameChildren_` 的逆序，即高 Z 顺序优先递归命中 | 正常 |
| AC-2.3 | WHEN 父节点自身不在响应区但未启用裁剪且子节点命中 THEN 子树仍可贡献命中目标 | 边界 |
| AC-2.4 | WHEN 响应区域受矩阵变换、输入源、输入工具或触控笔扩区影响 THEN 使用转换后的本地坐标和对应响应区域进行判断 | 正常 |
| AC-2.5 | WHEN `clipEdge=true` 且触点位于裁剪区域外 THEN 不继续收集被裁剪的越界目标 | 边界 |

### US-3: 通过静态模式和动态回调控制命中

**作为** 应用开发者,
**我想要** 使用 `hitTestBehavior` 或 `onTouchIntercept` 控制当前组件参与命中的方式,
**以便** 动态决定事件是否向自身、子节点、兄弟或祖先传播。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 未设置 `hitTestBehavior` 或执行重置 THEN 节点使用 `HitTestMode.Default` | 正常 |
| AC-3.2 | WHEN Dynamic ArkTS `onTouchIntercept` 返回合法 `HitTestMode` THEN 返回值写回节点并覆盖静态命中模式，影响当前及后续命中 | 正常 |
| AC-3.3 | WHEN 输入为鼠标按键命中或 `HOVER_ENTER` THEN 不触发 `onTouchIntercept` 回调 | 边界 |
| AC-3.4 | WHEN Dynamic ArkTS 回调执行失败或返回值不是 number THEN Bridge 回退到 `HTMDEFAULT` | 异常 |
| AC-3.5 | WHEN Static ArkTS 参数为 `undefined` 或 Native modifier 执行 reset THEN 清空回调或恢复 `HTMDEFAULT` | 异常 |
| AC-3.6 | WHEN使用公开 ArkTS API设置模式 THEN 仅按六种公开枚举处理；内部 `HTMTRANSPARENT_SELF` 不作为 ArkTS 公共接口值承诺 | 边界 |

### US-4: 通过父节点回调定向选择子节点

**作为** 应用开发者,
**我想要** 使用 `onChildTouchTest` 根据命中信息选择或竞争指定子节点,
**以便** 父组件定制复杂子树的触摸路由。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 父节点设置 `onChildTouchTest` THEN 回调输入仅包含显式设置 `id` 的候选子节点信息 | 正常 |
| AC-4.2 | WHEN 回调返回 `FORWARD` 或 `FORWARD_COMPETITION` 且提供有效子节点 ID THEN 对指定子节点以 `isDispatch=true` 执行命中，并记录该 ID | 正常 |
| AC-4.3 | WHEN strategy 不是 DEFAULT 但 ID 为空 THEN 框架将 strategy 降级为 DEFAULT | 异常 |
| AC-4.4 | WHEN `onTouchIntercept` 已返回 BLOCK 或 BLOCK_DESCENDANTS THEN 不调用 `onChildTouchTest` | 正常 |
| AC-4.5 | WHEN Dynamic Bridge 返回值不是 object、strategy 不是 number 或 id 不是 string THEN 返回 `{DEFAULT, ""}` | 异常 |

### US-5: 分别构建分发目标链与手势响应链

**作为** ArkUI 事件框架,
**我想要** 分离实际事件目标与手势关联候选,
**以便** 命中分发、手势组合和并行响应各自保持清晰边界。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 节点完成自身和子节点命中 THEN `TouchTestResult` 保存实际分发和仲裁目标，`ResponseLinkResult` 保存响应关联候选 | 正常 |
| AC-5.2 | WHEN 手势优先级、并行、互斥或 IgnoreInternal 规则重组最终识别器 THEN 响应链递归写入最终识别器，但不把两类结果合并为同一容器 | 正常 |
| AC-5.3 | WHEN 命中节点注册 `onTouchTestDone` THEN 在响应链设置完成后、加入 `GestureReferee` 前调用回调 | 正常 |
| AC-5.4 | WHEN 节点未注册公开或内部 touch-test-done 回调 THEN 不加入回调节点列表，也不收到完成通知 | 边界 |
| AC-5.5 | WHEN C API `OH_ArkUI_SetTouchTestDoneCallback` 的 node 或实现入口为空 THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`；callback 为空时注销回调 | 异常 |

### US-6: 保持多通道和 API 版本兼容

**作为** 多范式 ArkUI 开发者,
**我想要** Dynamic、Static 和 Native 通道遵循各自公开版本与重置约定,
**以便** 跨版本迁移时能够识别真实支持范围和能力缺口。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 使用 Dynamic API 7 的 `touchable` THEN 可设置是否参与触摸；WHEN API 9 及以后迁移 THEN 使用 `hitTestBehavior` 替代已废弃接口 | 正常 |
| AC-6.2 | WHEN 使用 Dynamic API THEN `hitTestBehavior` 自 9、`onChildTouchTest` 自 11、`onTouchIntercept` 自 12、`onTouchTestDone` 自 20 开放 | 边界 |
| AC-6.3 | WHEN 使用 Static API THEN 四个对应接口均自 API 23 开放并接受 `undefined` 重置，Static 不声明 `touchable` | 边界 |
| AC-6.4 | WHEN Native Node 设置 `NODE_HIT_TEST_BEHAVIOR` 且 size 为 0 或枚举超出公开范围 THEN style modifier 返回参数错误 | 异常 |
| AC-6.5 | WHEN 调用 `OH_ArkUI_PointerEvent_SetInterceptHitTestMode` 且 event 为空或事件类型不支持 THEN 返回对应参数或类型错误；当前实现不额外校验 mode 范围 | 异常 |
| AC-6.6 | WHEN 通过 Static typedNode 路径调用 `onChildTouchTest` THEN 当前手写 `ArkBaseNode` 路径不转发该设置，规格将其声明为已知通道缺口 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1~R-4 | 已有实现 | 单测/源码审查 | `pipeline_context.cpp:3915`, `event_manager.cpp:380` |
| AC-2.1~2.5 | R-5~R-9 | 已有实现 | FrameNode 单测 | `frame_node_test_ng.cpp`, `frame_node_test_ng_coverage_new.cpp` |
| AC-3.1~3.6 | R-10~R-15 | 已有实现 | SDK 审查/Bridge 单测 | `common.d.ts`, `js_view_abstract.cpp:11842` |
| AC-4.1~4.5 | R-16~R-20 | 已有实现 | FrameNode/Bridge 单测 | `frame_node_test_ng_new.cpp:348`, `js_view_abstract.cpp:12209` |
| AC-5.1~5.5 | R-21~R-25 | 已有实现 | EventManager/C API 单测 | `event_manager_test_ng_two.cpp:51`, `gesture_impl.cpp:829` |
| AC-6.1~6.6 | R-26~R-31 | 已有实现 | SDK/C API/静态桥接审查 | canonical SDK 与 Native 实现 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 输入事件类型等于 DOWN | 创建 `TouchRestrict` 并执行一次命中测试 | 每个指针 ID 独立建链 | AC-1.1 |
| R-2 | 行为 | 同一 ID 的 MOVE/UP/CANCEL 且缓存存在 | 复用缓存目标链分发 | 不因坐标移动重新选目标 | AC-1.2 |
| R-3 | 异常 | `touchTestResults_` 不含当前 ID | 分发返回 false | 不调用空目标 | AC-1.3 |
| R-4 | 恢复 | 仲裁未就绪且事件间隔达到清理阈值 | CANCEL 旧链、清理、重测并重新登记 | `onTouchTestDone` 可能再次触发 | AC-1.4 |
| R-5 | 行为 | 节点 inactive 或 EventHub disabled | 返回 OUT_OF_REGION | tips 特殊路径按源码保留 | AC-2.1 |
| R-6 | 行为 | 多个 frame child 重叠 | 从 `rbegin()` 开始命中 | 高 Z 优先 | AC-2.2 |
| R-7 | 边界 | 父节点区域外、未裁剪且子节点命中 | 保留子节点目标 | 父节点自身可不收集 | AC-2.3 |
| R-8 | 行为 | 节点存在变换或输入工具特定区域 | 使用逆矩阵后的本地坐标和工具对应区域 | 触控笔可扩展默认响应区 | AC-2.4 |
| R-9 | 边界 | clipEdge 开启且触点在裁剪区外 | 剪除越界命中 | 子节点不穿透裁剪 | AC-2.5 |
| R-10 | 行为 | 未配置或重置静态模式 | 使用 HTMDEFAULT | Dynamic 默认等价 HitTestMode.Default | AC-3.1 |
| R-11 | 行为 | 动态拦截回调返回合法模式 | 写回节点 HitTestMode | 结果具有后续命中的持久影响 | AC-3.2 |
| R-12 | 边界 | MOUSE_BUTTON 或 HOVER_ENTER | 跳过动态拦截回调 | 使用已有静态模式 | AC-3.3 |
| R-13 | 异常 | JS 回调异常或返回非 number | 使用 HTMDEFAULT | 不抛出新的 ArkUI 业务错误 | AC-3.4 |
| R-14 | 恢复 | Static 参数 undefined 或 Native reset | 清空回调/恢复默认模式 | 后续命中按默认处理 | AC-3.5 |
| R-15 | 边界 | ArkTS 公共枚举输入 | 公开范围为 0~5 六种模式 | HTMTRANSPARENT_SELF 仅内部使用 | AC-3.6 |
| R-16 | 行为 | 父节点存在子命中回调 | 仅序列化显式 id 子节点信息 | 未命名节点不进入数组 | AC-4.1 |
| R-17 | 行为 | FORWARD/FORWARD_COMPETITION 且 ID 有效 | 定向命中并记录转发 ID | 可绕过目标节点常规区域拒绝 | AC-4.2 |
| R-18 | 异常 | 非 DEFAULT strategy 且 ID 为空 | 降级 DEFAULT | 不执行定向命中 | AC-4.3 |
| R-19 | 行为 | intercept 返回 BLOCK/BLOCK_DESCENDANTS | 跳过子回调和常规子递归 | 拦截优先于子路由 | AC-4.4 |
| R-20 | 异常 | Dynamic Bridge 返回结构或字段类型非法 | 返回 DEFAULT 空结果 | 实现对 DEFAULT 也要求 string id | AC-4.5 |
| R-21 | 行为 | 命中过程收集目标 | 分别保存目标链和响应链 | 两种容器职责不可互换 | AC-5.1 |
| R-22 | 行为 | 识别器完成组合/优先级重组 | 响应候选递归写入最终识别器 | 不改变实际目标容器类型 | AC-5.2 |
| R-23 | 行为 | 注册完成回调的节点被命中 | 响应链设置后、仲裁登记前回调 | 公开回调和内部回调依次执行 | AC-5.3 |
| R-24 | 边界 | 节点无完成回调 | 不登记、不回调 | 避免无效遍历 | AC-5.4 |
| R-25 | 异常 | C API node/impl 为空或 callback 为空 | 前两者返回 PARAM_INVALID；callback 为空执行注销 | 不创建悬空回调 | AC-5.5 |
| R-26 | 行为 | Dynamic API 7~8 使用 touchable | 保持旧触摸开关行为 | API 9 标记废弃 | AC-6.1 |
| R-27 | 边界 | Dynamic API 版本低于接口 @since | 对应 API 不开放 | 版本分别为 9/11/12/20 | AC-6.2 |
| R-28 | 边界 | Static API 版本低于 23 | 四接口不开放 | API 23 起支持 undefined 重置 | AC-6.3 |
| R-29 | 异常 | Native style mode size=0 或值不在 0~5 | 返回参数错误 | 新增模式 4/5 自 API20 | AC-6.4 |
| R-30 | 异常 | PointerEvent C API event 为空或类型不支持 | 返回参数/类型错误 | 当前不校验 mode 范围 | AC-6.5 |
| R-31 | 边界 | Static typedNode 设置 onChildTouchTest | 当前手写路径无转发副作用 | 标记为实现缺口，不推断修复 | AC-6.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.4, R-1~R-4 | `pipeline_context_test_ng.cpp`, `event_manager_test_ng_new.cpp` | DOWN 建链、缓存复用、缺链与重测 |
| VM-2 | AC-2.1~2.5, R-5~R-9 | `frame_node_test_ng.cpp`, `ui_node_test_ng.cpp` | 逆 Z、响应区域、裁剪和变换 |
| VM-3 | AC-3.1~3.6, R-10~R-15 | SDK 声明审查 + FrameNode 单测 | 模式范围、动态覆盖和跳过条件 |
| VM-4 | AC-4.1~4.5, R-16~R-20 | `frame_node_test_ng_new.cpp`, Bridge 审查 | 定向转发、非法返回、拦截优先级 |
| VM-5 | AC-5.1~5.5, R-21~R-25 | `event_manager_test_ng_two.cpp`, C API 单测 | 双链、完成回调时序和注销 |
| VM-6 | AC-6.1~6.6, R-26~R-31 | Dynamic/Static SDK + Native 接口审查 | API 版本、错误码和通道缺口 |

## API 变更分析

> 本次为已有能力补录，不新增或修改产品 API。下表记录现存接口契约。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|--------|
| `hitTestBehavior` | Public | `HitTestMode` | 当前组件 | N/A | 设置静态命中模式 | AC-3.1, AC-3.6 |
| `onChildTouchTest` | Public | 子节点信息回调 | 当前组件 | N/A | 定制子节点命中路由 | AC-4.1~4.5 |
| `onTouchIntercept` | Public | `Callback<TouchEvent, HitTestMode>` | 当前组件 | N/A | 动态覆盖命中模式 | AC-3.2~3.5 |
| `onTouchTestDone` | Public | `TouchTestDoneCallback` | 当前组件 | N/A | 命中完成后接收响应链 | AC-5.3~5.4 |
| `NODE_HIT_TEST_BEHAVIOR` | Public C API | 属性项 mode | `int32_t` | PARAM_INVALID | 设置 Native 节点命中模式 | AC-6.4 |
| `OH_ArkUI_PointerEvent_SetInterceptHitTestMode` | Public C API | event, mode | `int32_t` | 参数/事件类型错误 | 在 Native 拦截回调中设置结果 | AC-6.5 |
| `OH_ArkUI_SetTouchTestDoneCallback` | Public C API | node, userData, callback | `ArkUI_ErrorCode` | PARAM_INVALID | 注册或注销命中完成回调 | AC-5.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|--------|
| `touchable(value: boolean)` | 废弃（API 9） | Dynamic ArkTS 旧代码控制触摸参与 | 迁移到 `hitTestBehavior` | AC-6.1 |

## 接口规格

### 接口定义

**hitTestBehavior**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `hitTestBehavior(value: HitTestMode): T`; Static: `hitTestBehavior(value: HitTestMode \| undefined): this` |
| 返回值 | 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.6, AC-6.2~6.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | HitTestMode | Dynamic 是；Static 否 | Default | ArkTS 公开值为 0~5；Static `undefined` 表示重置 |

**行为场景索引**：SC-1、SC-2、SC-5。

**onTouchIntercept**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `onTouchIntercept(callback: Callback<TouchEvent, HitTestMode>): T`; Static: `onTouchIntercept(callback: Callback<TouchEvent, HitTestMode> \| undefined): this` |
| 返回值 | 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.2~3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | Callback | Dynamic 是；Static 否 | 无回调 | 返回模式写回节点；Static `undefined` 注销 |

**行为场景索引**：SC-2、SC-3。

**onChildTouchTest**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `onChildTouchTest(event: (value: Array<TouchTestInfo>) => TouchResult): T`; Static: `onChildTouchTest(event: ((value: Array<TouchTestInfo>) => TouchResult) \| undefined): this` |
| 返回值 | 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| event | Function | Dynamic 是；Static 否 | DEFAULT 路由 | FORWARD/FORWARD_COMPETITION 需要有效 id；Static `undefined` 注销 |

**行为场景索引**：SC-3、SC-4。

**onTouchTestDone**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `onTouchTestDone(callback: TouchTestDoneCallback): T`; Static: `onTouchTestDone(callback: TouchTestDoneCallback \| undefined): this` |
| 返回值 | 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.3~5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | TouchTestDoneCallback | Dynamic 是；Static 否 | 无回调 | 输入为 BaseGestureEvent 和识别器数组；Static `undefined` 注销 |

**行为场景索引**：SC-5、SC-6。

## 兼容性声明

- **已有 API 行为变更:** 无本次代码变更；规格按 canonical SDK 修正旧文档偏差。Dynamic `touchable` 自 API 9 废弃；`HitTestMode` 的 BLOCK_HIERARCHY/BLOCK_DESCENDANTS 自 API 20 开放。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic API 7（兼容 `touchable`）；核心替代接口 `hitTestBehavior` 自 API 9。
- **API 版本号策略:** 分通道记录 `@since`；Static 四接口统一自 API 23，C API 分别自 API 12/20/22。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| UI 线程串行 | `PipelineContext::OnTouchEvent` 在 UI 线程执行，命中回调不得引入跨线程状态竞争 | AC-1.1, AC-3.2 |
| 层级单向调用 | SDK/Bridge → ViewAbstract/EventHub → Pipeline/EventManager → FrameNode/GestureEventHub | 全部 |
| DOWN 建链 | 正常触摸序列不得在每个 MOVE 上重做全树命中 | AC-1.1~1.2 |
| 双链分离 | 分发目标与响应关联候选不得混为同一数据模型 | AC-5.1~5.2 |
| 现状即规格 | typedNode 缺口和通道差异仅记录风险，不在本文提出产品修改 | AC-6.5~6.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 正常单指序列的全树命中次数为 1 次（DOWN），MOVE/UP 复用缓存链 | Pipeline 单测/Trace | `pipeline_context.cpp:3915` |
| 功耗 | 无新增轮询、定时器或后台任务 | 静态审查 | 存量同步调用链 |
| 内存 | UP/CANCEL 后清理对应指针目标链和仲裁作用域 | EventManager 单测 | `event_manager.cpp:1260` 附近清理路径 |
| 安全 | 回调数据仅暴露公开事件字段；C API 空指针返回错误 | C API 单测 | `gesture_impl.cpp:829` |
| 可靠性 | 仲裁污染/超时可通过 CANCEL、清理和重测恢复 | 故障路径单测 | `event_manager.cpp:380` |
| 可测试性 | 每个公共接口至少具备 SDK 契约审查和核心路径单测入口 | 追溯表 | VM-1~VM-6 |
| 自动化维测 | 命中结果可进入 EventTree/Inspector 记录 | Dump 单测 | `event_dump_test_ng.cpp` |
| 定界定位 | 日志区分命中为空、仲裁污染和重测路径 | hilog/事件树 | `event_manager.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无设备特有差异 | 按输入源、工具和窗口坐标命中 | 单测/集成测试 | `TouchRestrict` |
| 平板 | 无设备特有差异 | 多窗口场景仍使用目标窗口坐标和实例 ID | 多窗口集成测试 | `PipelineContext`, `ContainerScope` |
| 折叠屏 | 折叠状态本身不改变规则 | 窗口/布局变化后的新 DOWN 使用最新矩阵和响应区 | 折叠窗口集成测试 | `FrameNode` 矩阵缓存刷新 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|----------|
| 无障碍 | 是 | 无障碍 hover 使用独立分发路径；普通触摸命中不替代无障碍命中 | SC-1 |
| 大字体 | 否 | 字体缩放不直接改变命中算法，组件布局变化可间接改变响应区 | SC-1 |
| 深色模式 | 否 | 不影响事件命中与拦截 | 全部 |
| 多窗口/分屏 | 是 | 实例 ID、根节点偏移和坐标转换影响目标链 | SC-6 |
| 多用户 | 否 | 无持久化用户数据 | 全部 |
| 版本升级 | 是 | 必须按 Dynamic/Static/C API 的 @since 与废弃关系迁移 | SC-5 |
| 生态兼容 | 是 | 旧 `touchable`、旧规格枚举偏差和 typedNode 缺口需显式声明 | SC-5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 命中测试、拦截与响应链构建

  Scenario: SC-1 按下时建立目标链
    Given 根节点包含两个响应区重叠且 Z 序不同的子节点
    When 指针发送 DOWN 事件
    Then 框架按逆 Z 序执行命中测试
    And 为该指针 ID 缓存 TouchTestResult

  Scenario: SC-2 动态拦截覆盖静态模式
    Given 节点静态模式为 Default
    And onTouchIntercept 回调返回 Block
    When 节点执行触摸命中测试
    Then 节点模式写回为 Block
    And 子节点命中与 onChildTouchTest 均被跳过

  Scenario: SC-3 鼠标按键不触发触摸拦截回调
    Given 节点已注册 onTouchIntercept
    When 输入类型为 MOUSE_BUTTON
    Then 不调用 onTouchIntercept
    And 使用节点当前 HitTestMode

  Scenario: SC-4 子节点定向转发
    Given 父节点 onChildTouchTest 返回 FORWARD 和有效子节点 ID
    When 触点位于该子节点常规响应区外
    Then 仍以 isDispatch=true 对该子节点执行命中
    And 将子节点 ID 记录到 childTouchTestList

  Scenario: SC-5 命中完成回调时序
    Given 命中节点注册 onTouchTestDone
    When 目标链和 ResponseLinkResult 构建完成
    Then 先把响应链写入最终识别器
    And 在加入 GestureReferee 前调用 onTouchTestDone

  Scenario: SC-6 仲裁污染恢复
    Given 当前 Referee 超过清理阈值仍未就绪
    When 新 DOWN 到达
    Then 向旧目标链发送伪造 CANCEL
    And 清理旧仲裁与响应控制状态
    And 重做命中、响应链设置和完成回调
```

## Spec 自审清单

- [x] 无未决占位内容
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：本 Feat 负责命中和响应链构建，不重复手势识别/竞争语义
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 规则表每条满足可复现、可观测、边界明确、关联 AC、无冲突
- [x] Dynamic/Static/C API 均以 canonical 声明和真实实现交叉核验

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "PipelineContext OnTouchEvent EventManager TouchTest FrameNode TouchTest responseLink"
  - repo: "openharmony/interface_sdk-js"
    query: "hitTestBehavior onChildTouchTest onTouchIntercept onTouchTestDone API version"
```

**关键文档：** `specs/04-common-capability/04-common-events/03-event-dispatch-intercept/design.md`、`specs/04-common-capability/04-common-events/06-gesture-capability/Feat-04-gesture-intercept-spec.md`。
