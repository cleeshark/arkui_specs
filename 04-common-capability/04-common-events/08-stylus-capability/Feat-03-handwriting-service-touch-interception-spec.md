# 特性规格

> Func-04-04-08-Feat-03 手写检测服务接入与触控拦截：固化可选手写服务动态装载、可编辑文本/Web 命中资格、扩展响应区、Notify 决策、触摸取消清理和平台降级行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 手写检测服务接入与触控拦截 |
| 特性编号 | Func-04-04-08-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 内部手写服务协同能力；无公开 ArkTS/NDK 版本声明 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | L3（关键） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 服务动态装载与默认降级 | 补录 libstylus_innerapi 运行时装载、符号解析及默认实现行为 |
| ADDED | 原生文本组件拦截 | 补录 TextInput/TextArea/Search/RichEditor 节点登记、资格判断、Notify 和 CANCEL 清理 |
| ADDED | Web 拦截 | 补录网页可编辑位置检测、resourceName 通知及后续 MOVE/UP/CANCEL 吞噬行为 |
| ADDED | 响应区和生命周期 | 补录 Pen DOWN 纵向 20vp 扩展、注册/注销、进程级单例和 Preview 差异 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/08-stylus-capability/design.md` | 共享设计，增量合并 |
| 服务接口 | `interfaces/inner_api/ace/stylus/stylus_detector_interface.h:25` | 已核对 |
| OHOS 管理器 | `adapter/ohos/osal/stylus_detector_mgr.cpp:52` | 已核对 |
| 动态装载 | `adapter/ohos/osal/stylus_detector_loader.cpp:24` | 已核对 |
| Pipeline 拦截 | `frameworks/core/pipeline_ng/pipeline_context.cpp:3934`、`frameworks/core/common/event_manager.cpp:1416` | 已核对 |
| Web 协同 | `frameworks/core/components_ng/pattern/web/web_pattern.cpp:5345` | 已核对 |
| Preview 降级 | `adapter/preview/osal/stylus_detector_mgr.cpp:26` | 已核对 |

## 用户故事

### US-1: 可选装载手写检测服务

**作为** ArkUI 平台集成者，  
**我想要** 在系统存在手写服务时动态接入、缺失时安全降级，  
**以便** 同一 ace_engine 构建适配不同产品形态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 64 位进程初始化 StylusDetectorMgr THEN尝试 dlopen `/system/lib64/libstylus_innerapi.z.so`；WHEN 32 位进程 THEN使用 `/system/lib/libstylus_innerapi.z.so` | 正常 |
| AC-1.2 | WHEN SO 和 Create/Destroy 导出符号均存在 THEN创建 StylusDetectorInterface 实例并由 loader deleter 销毁 | 正常 |
| AC-1.3 | WHEN SO、任一符号或实例创建失败 THEN管理器使用进程内 StylusDetectorDefault，且本次单例生命周期不再重新装载 | 恢复 |
| AC-1.4 | WHEN默认实现未被调试命令启用 THEN `IsEnable()` 返回 false，事件继续普通触摸派发 | 正常 |

实现证据：`stylus_detector_loader.cpp:24-87`、`stylus_detector_mgr.cpp:204-211`、`stylus_detector_default.h:40-45`、`stylus_detector_default.cpp:34-62`。

### US-2: 命中可手写编辑的原生文本组件

**作为** 手写笔用户，  
**我想要** 在可编辑文本区域落笔时启用手写服务，  
**以便** 在 TextInput、TextArea、Search 和 RichEditor 中输入或编辑文本。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN TextInput/TextArea/SearchField/RichEditor 挂载 THEN向进程级管理器登记 FrameNode 和 LayoutInfo；节点销毁时移除登记 | 正常 |
| AC-2.2 | WHEN事件不是 PEN DOWN、没有当前 pointer 命中结果、目标仅为 GestureRecognizer 或没有 TextBase THEN不进入服务通知 | 边界 |
| AC-2.3 | WHEN TextField 不可聚焦、不可见、opacity=0、使用自定义键盘、密码模式或 OTP 模式 THEN不可用于手写检测 | 正常 |
| AC-2.4 | WHEN RichEditor 不可聚焦、不可见、opacity=0 或使用自定义键盘 THEN不可用于手写检测 | 正常 |
| AC-2.5 | WHEN SearchField 参与判断 THEN使用父 Search 节点的 focusable、visible 和 opacity 状态，并要求无自定义键盘 | 正常 |
| AC-2.6 | WHEN PEN DOWN 命中 TextInput 的可见清除按钮或 TextField 的可见语音按钮 THEN不通知手写服务，保留按钮原始行为 | 边界 |

实现证据：`stylus_detector_mgr.cpp:23-29,82-120,175-202,212-230`、`text_field_pattern.cpp:12185-12203`、`rich_editor_pattern.cpp:13850-13867`、`search_text_field.cpp:107-126`。

### US-3: 扩展手写笔响应区并拦截原生触摸

**作为** 手写笔用户，  
**我想要** 在文本上下边缘附近落笔仍能命中编辑组件，  
**以便** 提升落笔命中的容错范围。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN PEN DOWN 面向可聚焦、可见、opacity 非零的 TextField/RichEditor THEN默认响应区仅在纵向上、下各扩展 20vp，水平方向不扩展 | 正常 |
| AC-3.2 | WHEN TextField 为密码模式 THEN不扩展响应区；WHEN其使用自定义键盘或 OTP THEN仍可能参与扩展命中，但后续编辑资格检查拒绝服务通知 | 边界 |
| AC-3.3 | WHEN命中组件且服务 IsEnable=true THEN以当前 bundle、componentId 和 screenX/screenY 构造 NotifyInfo，并将 float 坐标收窄为 int | 正常 |
| AC-3.4 | WHEN RegisterStylusInteractionListener 返回 false 但 Notify 返回 true THEN仍判定触摸被拦截；注册结果只保存到 isRegistered_ | 边界 |
| AC-3.5 | WHEN Notify 返回 false THEN不拦截，继续后续普通触摸派发 | 恢复 |
| AC-3.6 | WHEN Notify 返回 true THEN Pipeline 清理当前触点手势域和命中目标，将事件标为 falsified CANCEL，并向 downFingerIds_ 中所有活动 pointer 派发 CANCEL 后提前返回 | 正常 |
| AC-3.7 | WHEN显式 PostEvent DOWN 满足同样条件 THEN执行同一检测和清理逻辑 | 正常 |

实现证据：`stylus_detector_mgr.h:35-36`、`text_field_pattern.cpp:11744-11767`、`rich_editor_pattern.cpp:13681-13699`、`stylus_detector_mgr.cpp:122-172`、`pipeline_context.cpp:3934-3953`、`event_manager.cpp:1416-1435`、`post_event_manager.cpp:600-623`。

### US-4: 在 Web 可编辑位置接入手写服务

**作为** 手写笔用户，  
**我想要** 在网页可编辑区域使用系统手写服务，  
**以便** 向 Web 输入焦点位置写入内容。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN Web 收到 PEN DOWN 且 `SetFocusByPosition(x,y)` 返回 true、服务启用且 Notify=true THEN设置拦截标志、请求 Web 焦点并不把 DOWN 交给 NWeb | 正常 |
| AC-4.2 | WHEN网页位置不可编辑、服务禁用或 Notify=false THEN按现有 Web Stylus/Touch 路径继续派发 | 恢复 |
| AC-4.3 | WHEN Web 拦截标志为 true 且收到 PEN MOVE THEN直接返回，不交给 NWeb | 正常 |
| AC-4.4 | WHEN Web 拦截标志为 true 且收到 PEN UP 或 CANCEL THEN清除标志并返回，不交给 NWeb | 正常 |
| AC-4.5 | WHEN Web 构造 NotifyInfo THEN componentId=-1、resourceName 为 Web inspector id，x/y 使用 Web 局部触点坐标并收窄为 int | 正常 |

实现证据：`web_pattern.cpp:5345-5373,5389-5400,5455-5462,5528-5537`、`stylus_detector_mgr.cpp:232-254`。

### US-5: 管理监听器和多实例状态

**作为** ArkUI 框架维护者，  
**我想要** 明确手写管理器的节点、bundle 和监听器生命周期，  
**以便** 定位多窗口和跨实例问题。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN每次满足资格的原生或 Web PEN DOWN 到达 THEN重新创建 callback 并调用 Register；注册不在组件挂载时发生 | 正常 |
| AC-5.2 | WHEN已登记文本节点全部移除 THEN使用当时 `Container::Current()` 的 bundleName 调用 UnRegister，并将 isRegistered_ 设为 false | 恢复 |
| AC-5.3 | WHEN仅 Web 使用手写服务 THEN当前 Web 路径没有对应的 Web 生命周期注销调用 | 边界 |
| AC-5.4 | WHEN多个 Container/bundle 共存 THEN共享同一个进程级 StylusDetectorMgr、nodeId_、layoutInfo_、选择状态和 isRegistered_ | 边界 |
| AC-5.5 | WHEN原生文本命中后记录节点 THEN后续服务回调通过管理器保存的最近 nodeId_ 和 layoutInfo_ 定位组件，而不是由 Notify 后续命令携带节点 ID | 正常 |

实现证据：`stylus_detector_mgr.cpp:52-75,154-202,232-254`、`stylus_detector_mgr.h:65-105`。

### US-6: Preview 和服务异常降级

**作为** 跨平台开发者，  
**我想要** Preview 不具备系统手写服务时保持普通触摸行为，  
**以便** 预览环境不会错误吞掉触摸事件。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN运行于 Preview THEN IsEnable、Register、Notify、IsNeedInterceptedTouchEvent 均返回 false，节点登记和注销为 no-op | 正常 |
| AC-6.2 | WHEN服务 SO 装载失败或默认实现禁用 THEN原生文本和 Web 均不拦截触摸 | 恢复 |
| AC-6.3 | WHEN真实服务注册失败但 Notify=true THEN仍可能拦截但后续命令回调不可达，该行为作为服务协同风险记录 | 边界 |

实现证据：`adapter/preview/osal/stylus_detector_mgr.cpp:26-65`、`stylus_detector_mgr.cpp:143-172,232-254`。

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1~R-4 | 已有实现 | Loader/降级集成测试 | `stylus_detector_loader.cpp:24-87` |
| AC-2.1~2.6 | R-5~R-10 | 已有实现 | 组件资格单测 | TextField/RichEditor/Search pattern tests |
| AC-3.1~3.7 | R-11~R-17 | 已有实现 | FrameNode/Pipeline/EventManager 单测 | `frame_node_test_ng_coverage_new.cpp:1477`、`event_manager.cpp:1416` |
| AC-4.1~4.5 | R-18~R-21 | 已有实现 | Web 集成测试 | `web_pattern.cpp:5345-5537` |
| AC-5.1~5.5 | R-22~R-25 | 已有实现 | 生命周期/多实例测试 | `stylus_detector_mgr.cpp:154-202` |
| AC-6.1~6.3 | R-26~R-28 | 已有实现 | Preview/故障注入 | `adapter/preview/osal/stylus_detector_mgr.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 管理器首次构造 | 按进程位宽装载 system libstylus_innerapi | 路径固定；`stylus_detector_loader.cpp:24-31` | AC-1.1 |
| R-2 | 行为 | SO 和两个导出符号有效 | 创建真实服务实例 | deleter 捕获 loader 和 destroy 函数 | AC-1.2 |
| R-3 | 恢复 | 装载/符号/实例任一步失败 | 使用 StylusDetectorDefault | 单例构造后不重试装载 | AC-1.3 |
| R-4 | 行为 | 默认实现 isEnable_=false | 不通知、不拦截 | 调试 ExecuteCommand 可改变默认状态，不属于应用公开 API | AC-1.4 |
| R-5 | 行为 | 支持文本组件 attach/destroy | 登记或移除 node/layout | 仅四类 tag | AC-2.1 |
| R-6 | 边界 | 非 PEN DOWN 或无有效命中 | 返回 false | 只处理当前 pointer id 结果 | AC-2.2 |
| R-7 | 行为 | TextField 资格检查 | 同时满足键盘、焦点、可见、opacity、非密码/OTP | 任一失败均拒绝 | AC-2.3 |
| R-8 | 行为 | RichEditor 资格检查 | 无自定义键盘、可聚焦、可见、opacity 非零 | 不检查密码/OTP | AC-2.4 |
| R-9 | 行为 | SearchField 资格检查 | 使用父 Search 节点状态 | 子 TextField 自身状态不是最终依据 | AC-2.5 |
| R-10 | 边界 | 命中可见清除/语音响应区 | 跳过该 TextField | 使用变换后的全局矩形和当前 vsync time | AC-2.6 |
| R-11 | 行为 | 可扩展 Pen DOWN | 响应区上、下各增加 20vp | 水平扩展=0；`HOT_AREA_ADJUST_SIZE` | AC-3.1 |
| R-12 | 边界 | TextField 密码/自定义键盘/OTP | 密码不扩展；后两者可扩展但服务资格拒绝 | 命中资格与编辑资格分两阶段 | AC-3.2 |
| R-13 | 行为 | 服务启用且命中原生文本 | NotifyInfo 使用 componentId、bundle、screen 坐标 | float 隐式收窄到 int | AC-3.3 |
| R-14 | 边界 | Register=false、Notify=true | 返回 true 并拦截 | 注册结果不参与返回值 | AC-3.4, AC-6.3 |
| R-15 | 恢复 | Notify=false | 返回 false，继续普通派发 | 不执行 CANCEL 清理 | AC-3.5 |
| R-16 | 行为 | Notify=true | 清 gesture scope、命中结果，改写 CANCEL 并向全部 downFingerIds 派发 | 不只取消当前 Pen id | AC-3.6 |
| R-17 | 行为 | PostEvent PEN DOWN | 复用同一 manager 检测和清理 | 使用 postEventTouchTestResults_ | AC-3.7 |
| R-18 | 行为 | Web 可编辑且 Notify=true | 吞 DOWN、设拦截标志、请求焦点 | Web 路径不使用原生 FrameNode nodeId | AC-4.1 |
| R-19 | 恢复 | Web 资格或服务通知失败 | 继续 NWeb Stylus/Touch 分发 | AC-4.2 |
| R-20 | 行为 | Web 拦截标志=true | MOVE 被吞；UP/CANCEL 清状态并被吞 | 只对 PEN 分支生效 | AC-4.3, AC-4.4 |
| R-21 | 行为 | Web Notify | componentId=-1、resourceName=inspectorId、局部坐标收窄为 int | 与原生 screen 坐标不同 | AC-4.5 |
| R-22 | 行为 | 每次可拦截 DOWN | 重新 Register callback | 组件 attach 仅登记节点 | AC-5.1 |
| R-23 | 恢复 | 最后一个文本节点移除 | 用 Current bundle 注销 | Web 无对称注销 | AC-5.2, AC-5.3 |
| R-24 | 边界 | 多 Container/bundle | 共享单例和单份当前状态 | 注销 bundle 取调用时 Current | AC-5.4 |
| R-25 | 行为 | 原生 Notify 成功 | 保存最近 nodeId/layoutInfo | 后续命令不携带 node id | AC-5.5 |
| R-26 | 行为 | Preview 调用 manager | 返回 false/no-op | 永不拦截 | AC-6.1 |
| R-27 | 恢复 | 服务不可用或禁用 | 正常触摸链继续 | 无运行时重连承诺 | AC-6.2 |
| R-28 | 边界 | 注册失败但 Notify 成功 | 触摸仍被拦截 | 命令 callback 可达性无保障 | AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.4, R-1~R-4 | 故障注入/集成测试 | 32/64 位路径、缺 SO/符号、默认降级、无重载 |
| VM-2 | AC-2.1~2.6, R-5~R-10 | 组件单元测试 | 四类组件、密码/OTP/自定义键盘、焦点/可见/opacity、按钮排除 |
| VM-3 | AC-3.1~3.7, R-11~R-17 | Pipeline/EventManager 单测 | 20vp 扩展、Register/Notify 分离、全活动 pointer CANCEL、PostEvent |
| VM-4 | AC-4.1~4.5, R-18~R-21 | Web 集成测试 | 可编辑位置、局部坐标、MOVE/UP/CANCEL 吞噬 |
| VM-5 | AC-5.1~5.5, R-22~R-25 | 多窗口/生命周期测试 | 重复注册、最后节点注销、Web 无注销、跨 bundle 共享状态 |
| VM-6 | AC-6.1~6.3, R-26~R-28 | Preview/服务故障测试 | Preview no-op、Notify=false 降级、注册失败+Notify=true |

## API 变更分析

> 未发现面向应用的 ArkTS/NDK 手写服务启用或拦截 API。本特性使用 ace Inner API，不承诺应用侧直接调用版本。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `StylusDetectorInterface::IsEnable` | InnerApi | 无 | bool | N/A | 查询系统手写服务是否启用 | AC-1.4, AC-3.3, AC-4.1 |
| `RegisterStylusInteractionListener` | InnerApi | bundleName, callback | bool | N/A | 注册手写服务命令回调 | AC-3.4, AC-5.1 |
| `UnRegisterStylusInteractionListener` | InnerApi | bundleName | void | N/A | 注销 bundle 监听器 | AC-5.2, AC-5.3 |
| `Notify` | InnerApi | NotifyInfo | bool | N/A | 通知服务命中位置，并作为是否拦截的最终判定 | AC-3.3~3.6, AC-4.1~4.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次仅补录现有 Inner API | 无迁移要求 | 全部 |

## 接口规格

### 接口定义

**StylusDetectorInterface 服务接口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool IsEnable()` |
| 函数签名 | `bool RegisterStylusInteractionListener(const std::string&, const std::shared_ptr<IStylusDetectorCallback>&)` |
| 函数签名 | `void UnRegisterStylusInteractionListener(const std::string&)` |
| 函数签名 | `bool Notify(const NotifyInfo&)` |
| 返回值 | bool/void；Notify bool 是最终触摸拦截判定 |
| 开放范围 | InnerApi |
| 错误码 | 无结构化错误码 |
| 关联 AC | AC-1.1~6.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| bundleName | std::string | 是 | 无 | 取当前 Container bundle；注销也取调用时 Current bundle |
| callback | shared_ptr | 是 | 无 | 每次合格 DOWN 新建；Register 结果不阻断 Notify |
| componentId | int | 是 | 无 | 原生为 FrameNode id，Web 为 -1 |
| x/y | int | 是 | 无 | 原生来自 screenX/Y，Web 来自局部坐标；float 收窄为 int |
| resourceName | std::string | Web 是 | 空 | Web 使用 inspector id，原生为空 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 服务不可用或禁用 | 返回 false，普通触摸继续 | AC-1.3, AC-1.4, AC-6.2 |
| 2 | Register=false、Notify=true | 触摸仍被拦截 | AC-3.4, AC-6.3 |
| 3 | Notify=false | 不执行 CANCEL 清理 | AC-3.5 |
| 4 | 原生 Notify=true | 清理目标并取消全部活动 pointer | AC-3.6 |
| 5 | Web Notify=true | 维持 Web 拦截状态直至 UP/CANCEL | AC-4.1~4.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；本规格补录现有 Inner API 和触摸链行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；节点表和当前状态均为进程内存。
- **最低支持版本:** 无公开 ArkTS/NDK 版本；不能以 2024 文件版权年份推导 API level。
- **API 版本号策略:** Inner API 无公开 `@since`，应用不得直接依赖。
- **平台差异:** OHOS 尝试动态装载系统 SO；Preview 全部返回 false/no-op。
- **坐标差异:** 原生文本发送 screen 坐标，Web 发送局部坐标，两者都收窄为 int。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 适配层隔离 | dlopen、服务接口和 Preview 差异位于 adapter/osal，Core 通过 StylusDetectorMgr 使用 | AC-1.1~1.4, AC-6.1 |
| Inner API 边界 | 服务能力不作为 Public ArkTS/NDK API 暴露 | 全部 |
| 拦截最终判定 | Notify 返回值是唯一最终拦截判定，Register 返回值不参与 | AC-3.4, AC-3.5, AC-6.3 |
| UI 触摸一致性 | 原生拦截后必须清理手势域和目标，并向所有活动 pointer 发送 CANCEL | AC-3.6 |
| 单例共享 | 节点、bundle 注册状态和当前命令目标是进程级共享状态 | AC-5.2~5.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 每次合格 PEN DOWN 最多执行一次服务 Register 和一次 Notify | Trace/集成测试 | `stylus_detector_mgr.cpp:154-172` |
| 功耗 | 无后台轮询；服务调用仅由 PEN DOWN 触发 | 源码审查 | `IsStylusTouchEvent` |
| 内存 | 仅保存支持文本节点 WeakPtr、LayoutInfo WeakPtr 和一份当前状态 | 内存检查 | `stylus_detector_mgr.h:96-105` |
| 安全 | 密码/OTP TextField 不进入服务通知，清除/语音按钮保留原始行为 | 单测 | AC-2.3, AC-2.6 |
| 可靠性 | 服务缺失/禁用/Notify=false 时不吞触摸 | 故障注入 | AC-1.3, AC-3.5, AC-6.2 |
| 可测试性 | 服务接口可替换为 mock/default；触摸目标和组件资格可构造 | 单元/集成测试 | Inner API 抽象 |
| 自动化维测 | ACE_STYLUS 日志记录命中位置、节点和服务禁用原因 | 日志测试 | `stylus_detector_mgr.cpp:128-146` |
| 定界定位 | Register 与 Notify 结果需分别记录，当前仅 isRegistered_ 保存注册结果 | 故障注入 | AC-3.4, AC-6.3 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 取决于产品是否提供系统手写服务和 Pen 输入 | SO/服务缺失时不拦截 | 真机测试 | loader/default |
| 平板 | 主要支持形态；覆盖文本组件、Web 和 20vp 扩展响应区 | 必须测试笔指并发 CANCEL | 真机测试 | AC-3.1, AC-3.6 |
| 折叠屏 | 进程级单例跨窗口共享状态 | 多窗口/多 bundle 注销归属需验证 | 多窗口测试 | AC-5.4 |
| Preview | 明确不支持 | 所有接口 false/no-op，普通触摸继续 | Preview 测试 | AC-6.1 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 手写服务拦截不新增无障碍语义 | 无 |
| 大字体 | 是 | 字体/布局变化会改变文本节点和按钮命中区域 | AC-2.6, AC-3.1 |
| 深色模式 | 否 | 不处理颜色 | 无 |
| 多窗口/分屏 | 是 | 单例、Current bundle 注销和当前 node 状态跨窗口共享 | AC-5.2, AC-5.4 |
| 多用户 | 否 | 接口使用 bundle，不显式区分系统用户 | 无 |
| 版本升级 | 是 | 系统 SO/符号缺失必须降级，不承诺热重载 | AC-1.3 |
| 生态兼容 | 是 | Web 与原生使用不同坐标空间；Preview 不支持 | AC-4.5, AC-6.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 手写检测服务接入与触控拦截
  Scenario: 服务缺失时保持普通触摸
    Given 系统未提供 libstylus_innerapi 或导出符号不完整
    When PEN DOWN 命中可编辑 TextInput
    Then StylusDetectorMgr 使用默认禁用实现
    And 事件继续普通触摸派发

  Scenario: Notify 成功后取消活动触摸
    Given PEN DOWN 命中可编辑文本组件
    And 服务 IsEnable 返回 true
    And Notify 返回 true
    When Pipeline 执行手写检测
    Then 当前手势域和命中结果被清理
    And downFingerIds 中每个活动 pointer 收到 falsified CANCEL

  Scenario: 注册失败但仍拦截
    Given RegisterStylusInteractionListener 返回 false
    And Notify 返回 true
    When PEN DOWN 命中文本组件
    Then 触摸仍被拦截

  Scenario: Web 手写序列
    Given Web 位置可编辑且 Notify 返回 true
    When PEN DOWN MOVE UP 依次到达
    Then DOWN 和 MOVE 不交给 NWeb
    And UP 清除拦截标志后返回
```

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 覆盖服务装载、原生文本、Web、响应区、拦截清理、生命周期和 Preview
- [x] 不展开服务回调的文本编辑命令，命令由 Feat-04 覆盖
- [x] Register 与 Notify、原生与 Web 坐标、真实设备与 Preview 差异均显式分离
- [x] 每个 AC 关联规则、验证方式及源码证据
- [x] 现有异常行为仅记录风险，不提出实现修复

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "StylusDetectorLoader StylusDetectorMgr 动态装载、默认降级、Register Notify 和触摸拦截调用链"
  - repo: "openharmony/arkui_ace_engine"
    query: "TextField RichEditor Search 手写编辑资格、20vp 扩展响应区、清除语音按钮排除"
  - repo: "openharmony/arkui_ace_engine"
    query: "WebPattern 手写服务 Notify、拦截状态和 MOVE UP CANCEL 行为"
```

**关键文档：** `adapter/ohos/osal/stylus_detector_mgr.cpp`、`adapter/ohos/osal/stylus_detector_loader.cpp`、`frameworks/core/pipeline_ng/pipeline_context.cpp`、`frameworks/core/common/event_manager.cpp`。
