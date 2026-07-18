# 特性规格

> Func-05-01-12-Feat-02 FolderStack 折叠与悬停状态事件：补录折叠监听生命周期、转换去重、`onFolderStateChange` 与 `onHoverStatusChange` payload、回调 reset 和多线程主树注册。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FolderStack 折叠与悬停状态事件 |
| 特性编号 | Func-05-01-12-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 11–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

FolderStack 通过 Pattern 注册折叠状态监听，并在状态变化后触发布局与事件。`onFolderStateChange` 输出当前 `foldStatus`；API 12 的 `onHoverStatusChange` 输出 foldStatus、isHoverMode、appRotation 和 windowStatusType。事件只在可观察状态转换时派发，EventInfo 定义见 `frameworks/core/components_ng/pattern/folder_stack/folder_stack_event_info.h:27-58`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 折叠状态监听与生命周期规格 | 覆盖 attach/appear、detach/disappear、去抖和多线程主树 |
| ADDED | Folder 状态事件规格 | 覆盖横向生效条件、foldStatus payload 和 reset |
| ADDED | Hover 状态事件规格 | 覆盖四字段 payload、转换去重、Dynamic/Static 兼容风险 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/12-folder-stack/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/folderStack.static.d.ets` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_pattern.cpp` | 已核对 |
| EventInfo/EventHub | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_event_info.h`、`frameworks/core/components_ng/pattern/folder_stack/folder_stack_event_hub.h` | 已核对 |

> 对外 payload 以 canonical SDK 为准。Static bridge 的字段填充偏差属于实现风险，不降低本文验收要求。

## 用户故事

### US-1: 监听折叠状态变化

**作为** 折叠屏应用开发者  
**我想要** 在设备折叠状态改变时收到当前 foldStatus  
**以便** 调整业务内容而无需自行访问平台折叠服务

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN FolderStack 进入主树/可见生命周期且平台折叠能力可用 THEN Pattern 注册一次折叠状态监听，不因重复 attach 建立重复有效监听 | 正常 |
| AC-1.2 | WHEN 折叠状态发生变化且符合 `onFolderStateChange` 的横向生效条件 THEN 回调被调用并收到 `{ foldStatus: 当前状态 }` | 正常 |
| AC-1.3 | WHEN 平台重复通知与上次相同状态且没有可观察转换 THEN 不重复派发同一 Folder 状态事件 | 边界 |
| AC-1.4 | WHEN callback 为 undefined/reset 或从未注册 THEN 状态变化仍可驱动内部布局，但不得调用应用回调 | 边界 |
| AC-1.5 | WHEN 节点 detach、disappear 或销毁 THEN 注销/失效监听；之后到达的迟到通知不得访问已销毁节点 | 边界 |

### US-2: 监听悬停状态和窗口上下文

**作为** 半折悬停界面开发者  
**我想要** 同时获得悬停、方向和窗口模式  
**以便** 区分进入/退出悬停以及窗口环境变化

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN hover 状态由 false 转为 true 或由 true 转为 false THEN `onHoverStatusChange` 回调收到当前 foldStatus、isHoverMode、appRotation、windowStatusType 四个字段 | 正常 |
| AC-2.2 | WHEN fold、rotation 或 window mode 的变化形成新的 hover 事件快照 THEN payload 反映派发时的当前值，不使用上一次状态残留字段 | 正常 |
| AC-2.3 | WHEN 布局帧内 hover 判定与上一次完全相同 THEN 不在每次 Measure/Layout 重复派发回调 | 边界 |
| AC-2.4 | WHEN 平台信息暂不可用或枚举无法形成合法 payload THEN 不构造未初始化事件；内部按非悬停/安全回退路径继续 | 异常 |
| AC-2.5 | WHEN handler reset THEN EventHub 清除当前 handler，后续状态变化不调用旧函数对象 | 边界 |

### US-3: 保持不同运行模式下的回调安全

**作为** ArkUI 框架维护者  
**我想要** 事件在普通和多线程构建路径下遵守同一生命周期  
**以便** 避免重复监听、跨线程回调和悬空引用

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 使用多线程 Pattern 构建 THEN 仅在节点进入主树的正确阶段注册平台监听，并在离树时对应注销 | 正常 |
| AC-3.2 | WHEN 平台通知来自非 UI 上下文 THEN 通过既有 Pipeline/TaskExecutor 约束在 UI 生命周期内更新 Pattern 和派发 EventHub，不并发修改布局树 | 正常 |
| AC-3.3 | WHEN 回调内部修改应用状态导致再次布局 THEN 当前事件派发完成，新的 FolderStack 判定在后续管线处理，不同步重入当前 LayoutAlgorithm | 边界 |
| AC-3.4 | WHEN Static `onHoverStatusChange` 被使用 THEN 公开预期仍为四字段 payload；若 bridge 只填 foldStatus，应由兼容测试识别为实现偏差 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | Pattern 生命周期/事件 UT | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_pattern.cpp:34-61,140-208`; `test/unittest/core/pattern/folder_stack/folder_stack_test_ng.cpp:1539-1844` |
| AC-2.1~AC-2.5 | R-6~R-10 | 已有实现 | EventInfo/EventHub/状态转换 UT | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_layout_algorithm.cpp:342-374`; `frameworks/core/components_ng/pattern/folder_stack/folder_stack_event_info.h:27-58`; `frameworks/core/components_ng/pattern/folder_stack/folder_stack_event_hub.h:31-57` |
| AC-3.1~AC-3.4 | R-11~R-14 | 已有实现 | multithread/Static 集成测试 | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_multithread_pattern.cpp:19-53`; `frameworks/core/components_ng/pattern/folder_stack/bridge/arkts_native_folder_stack_bridge.cpp:121-229`; `frameworks/core/components_ng/pattern/folder_stack/bridge/folder_stack_static_modifier.cpp:77-92` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Pattern 进入有效树生命周期 | 注册一个折叠监听 | 重复 attach 不重复持有 | AC-1.1 |
| R-2 | 行为 | fold 状态转换且横向条件成立 | 派发当前 foldStatus | payload 对象字段必填 | AC-1.2 |
| R-3 | 边界 | 与上次 fold 快照相同 | 不重复派发 | 内部布局可按其他 dirty 原因执行 | AC-1.3 |
| R-4 | 边界 | callback 未注册/reset | 跳过应用调用 | 不阻断内部状态更新 | AC-1.4 |
| R-5 | 恢复 | detach/disappear/destroy | 注销或使监听失效，迟到通知安全退出 | 不持有悬空 Pattern | AC-1.5 |
| R-6 | 行为 | hover 状态转换 | 派发四字段 HoverEventParam | 四字段均为当前快照 | AC-2.1 |
| R-7 | 行为 | fold/rotation/window 形成新快照 | 重新读取并填充 payload | 不复用残留字段 | AC-2.2 |
| R-8 | 边界 | hover 快照未变化 | 不按布局帧重复派发 | 事件与状态转换绑定 | AC-2.3 |
| R-9 | 异常 | 平台信息不足 | 不派发未初始化 payload，内部安全降级 | 不伪造枚举 | AC-2.4 |
| R-10 | 恢复 | handler reset | EventHub 清除旧 handler | 后续不调用旧函数 | AC-2.5 |
| R-11 | 行为 | multithread 节点进入/离开主树 | 在主树阶段注册/注销 | 线程模型不改变 payload | AC-3.1 |
| R-12 | 行为 | 平台通知需更新 UI 状态 | 经现有执行器进入 UI 生命周期 | 不并发修改 UI 树 | AC-3.2 |
| R-13 | 边界 | 应用回调引发状态修改 | 在后续 Pipeline 处理新布局 | 禁止同步重入当前算法 | AC-3.3 |
| R-14 | 异常 | Static payload 字段不完整 | 视为实现偏差并由测试报告 | canonical SDK 四字段不变 | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | Pattern 生命周期与 fold 序列 UT | 单次注册、横向条件、去重、reset、注销 |
| VM-2 | R-6~R-10, AC-2.1~AC-2.5 | Hover 快照参数化 UT | 四字段、进入/退出、窗口/方向变化和缺失平台信息 |
| VM-3 | R-11~R-13, AC-3.1~AC-3.3 | multithread/TaskExecutor UT | 主树注册、UI 串行和回调重入隔离 |
| VM-4 | R-14, AC-3.4 | Static SDK+bridge 集成测试 | Static payload 必须满足四字段 SDK 契约 |

## API 变更分析

> 下表补录已有事件接口，不引入新的回调或平台权限。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `onFolderStateChange(callback)` | Public Dynamic | `(event: {foldStatus}) => void` | `FolderStackAttribute` | N/A | API 11 监听折叠状态 | AC-1.1~AC-1.5 |
| `onHoverStatusChange(handler)` | Public Dynamic | `(param: HoverEventParam) => void` | `FolderStackAttribute` | N/A | API 12 监听悬停/方向/窗口状态 | AC-2.1~AC-2.5 |
| Static `onFolderStateChange(callback?)` | Public Static | callback/undefined | `this` | N/A | API 23 Static 注册/reset | AC-1.2~AC-1.5 |
| Static `onHoverStatusChange(handler?)` | Public Static | handler/undefined | `this` | N/A | API 23 Static 注册/reset | AC-2.1~AC-3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | API 18 仅规范化匿名对象/回调类型，历史可用性保留 | 无需迁移 | AC-1.2, AC-2.1 |

## 接口规格

### 接口定义

**onFolderStateChange(callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `(callback: (event: OnFoldStatusChangeInfo) => void): FolderStackAttribute` |
| 返回值 | 当前 FolderStackAttribute |
| 开放范围 | Public、Stage 模型，API 11 |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.5 |

**onHoverStatusChange(handler)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `(handler: (param: HoverEventParam) => void): FolderStackAttribute` |
| 返回值 | 当前 FolderStackAttribute |
| 开放范围 | Public、Stage 模型，API 12 |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-3.4 |

**参数与 payload 约束**

| 参数/字段 | 类型 | 必填 | 默认值 | 约束条件 |
|-----------|------|------|--------|----------|
| callback/handler | function | Dynamic 是；Static 可 undefined | 无回调 | undefined 表示 reset |
| foldStatus | FoldStatus | 是 | 无 | 派发时当前折叠状态 |
| isHoverMode | boolean | Hover 事件必填 | 无 | 当前是否进入悬停布局 |
| appRotation | AppRotation | Hover 事件必填 | 无 | 当前应用方向 |
| windowStatusType | WindowStatusType | Hover 事件必填 | 无 | 当前窗口模式 |

## 兼容性声明

- **已有 API 行为变更:** 否；API 18 对匿名对象命名规范化不改变历史 API 11/12 可用性。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；上次状态和回调只存在内存。
- **最低支持版本:** onFolderStateChange API 11；onHoverStatusChange API 12；Static API 23。
- **API 版本号策略:** payload 字段和版本以 canonical SDK 为准；Static 实现字段偏差不作为契约。

| 版本 | 契约 | 证据 |
|------|------|------|
| API 11 | Folder 状态回调 | `interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts:165-179` |
| API 12 | Hover 回调与四字段 payload | `interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts:181-193,230-277` |
| API 18 | OnFoldStatusChangeInfo/Callback 命名规范化 | `interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts:86-136` |
| API 23 | Static 两类 callback/reset | `interface/sdk-js/api/arkui/component/folderStack.static.d.ets:53-93,105-137` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| EventHub 边界 | Bridge 只注册函数，Pattern/Layout 构造状态，EventHub 负责派发 | AC-1.2, AC-2.1 |
| 状态转换驱动 | 不按帧广播相同快照 | AC-1.3, AC-2.3 |
| UI 线程串行 | 平台通知不得并发修改 Pattern/LayoutProperty | AC-3.1~AC-3.3 |
| SDK payload 完整性 | HoverEventParam 四字段均为必填 | AC-2.1, AC-2.2, AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 相同状态不重复回调；每次转换最多各派发一次已注册事件 | 回调计数 UT | AC-1.3, AC-2.3 |
| 功耗 | 节点离树后注销监听，不保留无效平台订阅 | 生命周期测试 | AC-1.5 |
| 内存 | EventHub reset 释放旧函数引用；监听不延长销毁节点生命周期 | 内存/弱引用 UT | AC-1.5, AC-2.5 |
| 安全 | payload 不含敏感数据，不新增权限 | API 审查 | SDK 类型 |
| 可靠性 | 快速折叠/旋转/窗口变化、迟到通知和回调重入不得崩溃 | 压力/故障注入 | AC-2.2~AC-3.3 |
| 可测试性 | 平台状态和 TaskExecutor 可 mock，回调次数/字段可断言 | Pattern UT | VM-1~VM-4 |
| 自动化维测 | 可记录监听注册、快照、去重原因和派发次数 | hilog/trace | Pattern/EventHub |
| 定界定位 | 区分平台通知、Pattern 快照、Layout hover 判定、Bridge payload | 源码追溯 | `design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 直板设备通常不产生 hover=true | 回调存在但按实际平台状态派发/不派发 | 非折叠设备测试 | AC-2.1~AC-2.4 |
| 平板 | 无半折悬停事件 | 窗口状态变化不得伪造 hover | 多窗口测试 | AC-2.2 |
| 折叠屏 | 提供 fold/hover/rotation/window 快照 | 覆盖进入、退出和快速状态序列 | 真机/模拟状态矩阵 | AC-1.2~AC-2.3 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 事件不直接修改语义树；应用修改在后续构建生效 | AC-3.3 |
| 大字体 | 否 | 不改变字体属性 | N/A |
| 深色模式 | 否 | 不涉及颜色 | N/A |
| 多窗口/分屏 | 是 | windowStatusType 是 Hover payload 必填字段 | AC-2.1, AC-2.2 |
| 多用户 | 否 | 无用户持久状态 | N/A |
| 版本升级 | 是 | API 11/12/18/23 与 Static payload 必须回归 | 兼容矩阵 |
| 生态兼容 | 是 | callback reset、去重和四字段 payload 是稳定契约 | AC-1.3~AC-3.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: FolderStack 折叠与悬停状态事件
  Scenario: 进入悬停派发完整快照
    Given FolderStack 已注册两类回调
    And 设备从展开切换为受支持 HALF_FOLD 悬停
    When 状态转换完成
    Then Folder 回调收到当前 foldStatus
    And Hover 回调收到 foldStatus、true、appRotation、windowStatusType

  Scenario: 相同状态不重复派发
    Given 上一次 hover 快照与当前完全相同
    When 因其他原因再次执行布局
    Then onHoverStatusChange 不增加调用次数

  Scenario: 离树后迟到通知
    Given FolderStack 已 detach 并注销监听
    When 平台迟到通知到达
    Then 不调用旧应用 callback
    And 不访问已销毁 Pattern
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖折叠/悬停事件和监听生命周期
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则满足可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] Static payload 偏差仅作为风险，canonical 四字段契约未降低

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FolderStackPattern fold listener EventHub HoverEventParam multithread onHoverStatusChange"
  - repo: "openharmony/interface_sdk-js"
    query: "onFolderStateChange onHoverStatusChange HoverEventParam foldStatus appRotation windowStatusType"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/component/folderStack.static.d.ets`
- 架构设计：`05-ui-components/01-layout-components/12-folder-stack/design.md`
