# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 命中测试与事件目标链构建 |
| 特性编号 | Func-03-04-01-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 9-23，当前主干 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

本规格固化 FrameNode 命中测试、响应区域、HitTestMode、手势目标收集、目标链缓存及 PostEvent 隔离行为。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | NG 命中测试规格 | 覆盖坐标变换、响应区域、子节点遍历与拦截回调 |
| ADDED | 目标链构建规格 | 覆盖 TouchTarget、Recognizer 和 ResponseLinkResult 的组合 |
| ADDED | 缓存和 PostEvent 规格 | 固化 pointer ID 缓存与独立事件处理域 |

## 输入文档

- 共享设计：`specs/03-engine-framework/04-event-framework/01-event-base-framework/design.md`。
- 实现：`frameworks/core/common/event_manager.cpp:112-232`、`frameworks/core/components_ng/base/frame_node.cpp:3888,4256`、`frameworks/core/components_ng/event/gesture_event_hub.cpp:296,573,739`。
- 枚举：`frameworks/core/components_ng/event/event_constants.h:38`。
- SDK：`interface/sdk-js/api/@internal/component/ets/common.d.ts:19829,19862`、`interface/sdk-js/api/@internal/component/ets/enums.d.ts:3549`、`interface/sdk-js/api/arkui/component/common.static.d.ets:11603`。

## 用户故事

### US-1: 按节点树和响应区域确定目标

作为事件框架开发者，我希望命中测试考虑节点变换、响应区域、输入工具和 HitTestMode，以便构建确定且可复现的事件目标链。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN DOWN 坐标进入节点有效响应区域 THEN FrameNode 按树层级收集自身、子节点和事件中心提供的目标 | 正常 |
| AC-1.2 | WHEN 节点为不同 SourceTool 配置 responseRegion THEN 使用匹配工具的区域；WHEN 未匹配 THEN 回退节点矩形 | 边界 |
| AC-1.3 | WHEN HitTestMode 为 None、Block、Transparent、BlockHierarchy 或 BlockDescendants THEN 按枚举语义控制自身和层级传播 | 正常 |
| AC-1.4 | WHEN onChildTouchTest 返回指定子节点和策略 THEN 目标链按回调结果调整 | 正常 |

### US-2: 缓存和隔离目标链

作为输入分发开发者，我希望同一指针交互复用 DOWN 阶段的目标链，并让 PostEvent 使用独立处理域，以便 MOVE/UP 稳定到达初始目标且不会误清理其他事件。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN TouchTest 完成 THEN 结果按 pointer ID 缓存并加入对应 GestureReferee scope | 正常 |
| AC-2.2 | WHEN 后续 MOVE 到达 THEN DispatchTouchEvent 读取已缓存目标链而不重新执行整树命中测试 | 正常 |
| AC-2.3 | WHEN UP 或 CANCEL 完成交互 THEN 清理该 pointer 的目标链和仲裁 scope | 恢复 |
| AC-2.4 | WHEN PostEvent 或带 eventHandle 的事件执行 THEN 使用独立结果表或按 eventHandle 分组的 GestureReferee，清理不影响其他组 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1, AC-1.2 | R-1, R-2 | TASK-F2-1 | FrameNode 命中单测 | `frame_node.cpp:3888,4256` |
| AC-1.3 | R-3 | TASK-F2-1 | HitTestMode 参数化测试 | `event_constants.h:38`、SDK enums |
| AC-1.4 | R-4 | TASK-F2-2 | onChildTouchTest 桥接测试 | `common.d.ts:19862` |
| AC-2.1, AC-2.2 | R-5, R-6 | TASK-F2-3 | EventManager 交互序列测试 | `event_manager.cpp:183-192,1208-1235` |
| AC-2.3 | R-7 | TASK-F2-3 | UP/CANCEL 清理测试 | `event_manager.cpp:1263-1281` |
| AC-2.4 | R-8 | TASK-F2-4 | PostEvent 多处理域测试 | `event_manager.cpp:218-231,530-568,612-631,1586-1644` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | DOWN 进入 FrameNode::TouchTest | 将全局点转换到父/本地坐标并按节点层级收集命中目标 | 不可见、不可命中或被模式排除的节点不加入链 | AC-1.1 |
| R-2 | 边界 | responseRegionMap 存在 SourceTool 键 | 优先使用工具专属区域，无匹配时使用节点 rect | SourceTool::UNKNOWN 按通用回退处理 | AC-1.2 |
| R-3 | 行为 | 设置有效 HitTestMode | Default 按默认层级；Block/Transparent/None 及 API 20 扩展模式按枚举控制传播 | Dynamic 基础模式自 API 9，层级阻断模式自 API 20；Static 自 API 23 | AC-1.3 |
| R-4 | 行为 | onChildTouchTest 返回 TouchResult | 按指定 strategy 和 id 调整子节点命中结果 | 回调无有效目标时保持框架默认结果 | AC-1.4 |
| R-5 | 行为 | TouchTest 产生 recognizer/target | SetResponseLinkRecognizers 后加入 GestureReferee scope，并写入 touchTestResults_[pointerId] | 同一 pointer 的 needAppend 可追加子管线结果 | AC-2.1 |
| R-6 | 行为 | MOVE/UP/CANCEL 进入 DispatchTouchEvent | 通过 pointer ID 查找缓存；不存在时返回 false | MOVE 不重新构建完整目标链 | AC-2.2 |
| R-7 | 恢复 | 非伪造 UP/CANCEL 完成 | 主动清理 gesture state、scope，并在 sendOnTouch 时删除缓存 | 伪造 CANCEL 遵循专用清理路径 | AC-2.3 |
| R-8 | 边界 | eventHandleId/EVENT_HANDLE 大于 0 或 PostEvent 派发 | 选择独立/继承的 referee；结果清理仅删除映射到同一 referee 的组 | 普通事件 key=0 使用主 referee | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, AC-1.2 | FrameNode 单测 | 坐标、工具响应区、回退矩形 |
| VM-2 | AC-1.3 | Dynamic/Static API 与命中参数化测试 | API 9/20/23 模式边界 |
| VM-3 | AC-1.4 | JS bridge 测试 | 子节点选择和无效返回回退 |
| VM-4 | AC-2.1, AC-2.2, AC-2.3 | Touch DOWN-MOVE-UP/CANCEL 序列测试 | 缓存复用和清理 |
| VM-5 | AC-2.4 | PostEvent 与 eventHandle 并发组测试 | 独立 referee 和定向清理 |

## API 变更分析

### 新增 API

无新增 API。现有公共入口包括 `hitTestBehavior`、`onChildTouchTest` 和 Native 触摸拦截事件。

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

**hitTestBehavior（现有 ArkTS API）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `hitTestBehavior(value: HitTestMode): T` |
| 返回值 | 当前组件属性链 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.3 |

**onChildTouchTest（现有 ArkTS API）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onChildTouchTest(event: (value: Array<TouchTestInfo>) => TouchResult): T` |
| 返回值 | 当前组件属性链 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | HitTestMode | 是 | Default | 必须是 SDK 声明枚举；扩展层级模式要求对应 API 版本 |
| event | TouchTest 回调 | 是 | 无 | 返回的 id 应对应候选子节点 |

行为索引：模式语义见 VM-2；子节点选择见 VM-3；缓存与 PostEvent 属 InnerApi 行为，见 VM-4/VM-5。

## 兼容性声明

- **已有 API 行为变更:** 否；HitTestMode 基础值自 API 9，BlockHierarchy/BlockDescendants 自 API 20，Static 声明自 API 23。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** `hitTestBehavior` API 9；`onChildTouchTest` API 11。
- **API 版本号策略:** 保持现有 SDK `@since`。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 树遍历归属 | FrameNode 负责树和几何命中，GestureEventHub 负责事件目标收集 | AC-1.1 |
| 结果稳定性 | 一轮 pointer 交互使用缓存目标链 | AC-2.1, AC-2.2 |
| 仲裁同步 | 命中的 recognizer 必须加入与事件处理域对应的 referee scope | AC-2.1, AC-2.4 |
| 公开能力边界 | 公开触摸拦截语义由通用事件规格承接，本规格聚焦引擎构链 | AC-1.3, AC-1.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | MOVE/UP 复用 pointer 缓存，不执行完整树 TouchTest | 调用计数单测 | `event_manager.cpp:1208` |
| 内存 | UP/CANCEL 后删除对应结果和冗余 scope | 泄漏与容器大小测试 | `event_manager.cpp:1263` |
| 可靠性 | PostEvent 清理不得影响其他 referee 组 | 多组交互测试 | `event_manager.cpp:218` |
| 可测试性 | HitTestMode 和 SourceTool 可参数化 | 单元测试 | `frame_node.cpp:4256` |
| 定界定位 | 命中结果和 recognizer 状态可进入 EventTree | Dump 测试 | `event_manager.cpp:195` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 主要使用触摸响应区 | 多指分别按 pointer ID 缓存 | 多指测试 | EventManager |
| 平板 | 鼠标、触控笔可使用工具专属 responseRegion | SourceTool 匹配优先 | 鼠标/笔测试 | `frame_node.cpp:4256` |
| 折叠屏 | 几何变化后新一轮 DOWN 使用新布局命中 | 当前交互仍保持原目标链 | 折叠过程交互测试 | AC-2.2 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 无障碍 Hover 有独立结果，触摸开始可触发其取消 | AC-1.1 |
| 大字体 | 是 | 布局尺寸变化会影响下一轮命中区域 | AC-1.1 |
| 深色模式 | 否 | 不影响命中算法 | - |
| 多窗口/分屏 | 是 | 子管线结果需携带全局偏移和 viewScale | AC-2.1 |
| 多用户 | 否 | 无持久化状态 | - |
| 版本升级 | 是 | HitTestMode 枚举存在版本扩展 | AC-1.3 |
| 生态兼容 | 是 | Legacy 分发与 NG 构链共存 | AC-2.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 命中测试与事件目标链构建
  Scenario: 一轮触摸复用目标链
    Given DOWN 已完成 FrameNode 命中测试
    When 同一 pointer ID 依次产生 MOVE 和 UP
    Then MOVE 和 UP 使用 DOWN 阶段缓存的目标链
    And UP 完成后删除该 pointer 的缓存与仲裁 scope

  Scenario: PostEvent 处理域隔离
    Given 两个 eventHandle 映射到不同 GestureReferee
    When 其中一组交互结束并执行清理
    Then 仅删除映射到该 referee 的命中结果
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则满足 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode TouchTest HitTestMode responseRegion GestureEventHub target chain PostEvent referee"
```

**关键文档：** `design.md`、`event_manager.cpp`、`frame_node.cpp`、SDK `common.d.ts`。
