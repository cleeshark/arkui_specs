# 特性规格

> Func-04-04-03-Feat-03 跨容器事件分发：固化正常触摸序列在主 Pipeline 与 Plugin/Form 子 Pipeline 之间的目标链追加、坐标恢复、实例上下文恢复和统一分发能力。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 跨容器事件分发 (Cross-Container Event Dispatch) |
| 特性编号 | Func-04-04-03-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 当前主干；内部 Pipeline/EventManager 能力 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 跨 Pipeline 目标链规格 | 补录 Plugin/Form 子 Pipeline 递归命中、目标链追加和统一分发 |
| ADDED | 跨容器坐标规格 | 补录目标级 offset/viewScale 保存及 Dispatch/Handle 坐标恢复 |
| ADDED | 实例上下文恢复规格 | 补录递归子 Pipeline 后的 instanceId 与 ContainerScope 恢复 |
| REMOVED | 自定义输入构造与 PostEvent 投递规格 | 迁移至 Func-04-04-03-Feat-04，本文不再重复 BuilderNode、Native Post 和事件构造规则 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| 功能域设计 | `specs/04-common-capability/04-common-events/03-event-dispatch-intercept/design.md` | 与本 Spec 增量同步 |
| 前置命中规格 | `Feat-01-hit-test-intercept-response-chain-spec.md` | Baselined |
| 前置分发规格 | `Feat-02-touch-sequence-dispatch-propagation-spec.md` | Baselined |
| Pipeline 入口 | `frameworks/core/pipeline_ng/pipeline_context.cpp:3915-4017` | 已核验 |
| 目标链追加 | `frameworks/core/common/event_manager.cpp:112-181` | 已核验 |
| 坐标恢复 | `frameworks/core/event/touch_event.cpp:445-468,842-872` | 已核验 |

## 用户故事

### US-1: 合并跨 Pipeline 的触摸目标链

**作为** ArkUI 事件框架，
**我想要** 在 Plugin/Form 子 Pipeline 命中时把子目标追加到当前触摸链，
**以便** 跨容器组件与外层组件参与同一次确定性的分发和手势仲裁。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 主 Pipeline 的 DOWN 命中已登记的 Plugin/Form 子 Pipeline THEN 将事件按子 Pipeline offset/viewScale 换算并递归调用子 Pipeline `OnTouchEvent(..., true)` | 正常 |
| AC-1.2 | WHEN 子 Pipeline 以 `isSubPipe=true` 完成命中 THEN 只完成目标链构建与全局事件处理，不进入 MOVE 缓存、无障碍处理或最终分发 | 边界 |
| AC-1.3 | WHEN `needAppend=true` THEN 新命中的子 Pipeline 目标置于链前部，原父 Pipeline 目标拼接到链尾部 | 正常 |
| AC-1.4 | WHEN 合并链进入两阶段分发 THEN 父层目标先参与逆序 Dispatch，子 Pipeline 目标先参与正序 Handle | 正常 |
| AC-1.5 | WHEN 子 Pipeline 追加 DOWN THEN 不执行新序列的全局活动识别器清理，合并结果复用当前 Referee 和 GestureScope | 边界 |
| AC-1.6 | WHEN 所有子 Pipeline 递归完成 THEN 父 Pipeline 恢复 EventManager instanceId，且回调在对应 `ContainerScope` 中执行 | 恢复 |

### US-2: 恢复跨容器目标的局部坐标

**作为** 跨容器事件目标，
**我想要** 在收到 Dispatch 和 Handle 前恢复自己的坐标系，
**以便** 子 Pipeline 内部手势与回调读取正确的位置。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `needAppend=true` 且为标准系统构建 THEN 为每个新增 `TouchEventTarget` 保存子 Pipeline 全局 offset 与 viewScale | 正常 |
| AC-2.2 | WHEN 目标 offset 非零 THEN Dispatch 和 Handle 分别使用 `(坐标-offset)/scale` 的临时事件副本，不修改原始共享事件 | 正常 |
| AC-2.3 | WHEN viewScale 近零 THEN 坐标只减 offset，并使用 scale=1 的事件副本 | 边界 |
| AC-2.4 | WHEN offset 为零或非 `OHOS_STANDARD_SYSTEM` 构建 THEN 目标直接处理原始事件，不执行多容器坐标换算 | 边界 |
| AC-2.5 | WHEN 事件家族为普通 Mouse 或 Axis THEN 不套用 Touch 专用的 `needAppend`/`SetSubPipelineGlobalOffset` 机制 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.2 | R-1, R-2 | 已有实现 | Pipeline 子管线集成测试 | `pipeline_context.cpp:3941-4017` |
| AC-1.3~AC-1.5 | R-3~R-5 | 已有实现 | EventManager 目标链单测 | `event_manager.cpp:123-181` |
| AC-1.6 | R-6 | 已有实现 | 多实例 ContainerScope 测试 | `pipeline_context.cpp:3998-4011` |
| AC-2.1~AC-2.5 | R-7~R-11 | 已有实现 | TouchEventTarget 坐标参数化测试 | `event_manager.cpp:161-170`；`touch_event.cpp:445-468,842-872` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 主 Pipeline DOWN 遍历到有效子 Pipeline | 换算事件并递归 `OnTouchEvent(..., true)` | 仅已登记且可升级的 PipelineContext | AC-1.1 |
| R-2 | 边界 | 子 Pipeline 的 `isSubPipe=true` | 完成建链后提前返回 | 不执行最终 Dispatch 和 MOVE 缓存 | AC-1.2 |
| R-3 | 行为 | `EventManager::TouchTest` 的 `needAppend=true` | 子目标在前、父目标在后形成单一结果链 | 以 pointer ID 保存 | AC-1.3 |
| R-4 | 行为 | 合并目标链进入两阶段分发 | 父目标先 Dispatch、子目标先 Handle | 顺序由链拼接及逆序/正序共同决定 | AC-1.4 |
| R-5 | 边界 | 子 Pipeline 追加现有 DOWN | 跳过新序列级全局清理 | 复用当前触摸 ID 的仲裁状态 | AC-1.5 |
| R-6 | 恢复 | 子 Pipeline 递归结束 | 恢复父 EventManager instanceId | 回调仍受对应 ContainerScope 约束 | AC-1.6 |
| R-7 | 行为 | 标准系统且追加子目标 | 为每个新增目标保存 offset/viewScale | 不写入原父目标 | AC-2.1 |
| R-8 | 行为 | 目标 offset 非零且 scale 非零 | 使用坐标转换后的事件副本执行 Dispatch/Handle | 原事件保持不变 | AC-2.2 |
| R-9 | 边界 | `NearZero(viewScale)` | 仅减 offset，scale 回退为1 | 避免除零 | AC-2.3 |
| R-10 | 边界 | offset 为零或非标准系统构建 | 直接使用原事件 | 不构造跨容器副本 | AC-2.4 |
| R-11 | 边界 | Mouse/Axis 普通分发 | 不应用 Touch 子 Pipeline 坐标状态 | 仅 TouchEventTarget 路径 | AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.2, R-1~R-2 | 主/子 Pipeline 集成测试 | 递归入口与只建链返回 |
| VM-2 | AC-1.3~AC-1.5, R-3~R-5 | EventManager 目标顺序单测 | 拼链顺序和 Referee 复用 |
| VM-3 | AC-1.6, R-6 | 多 Container 实例测试 | instanceId 恢复和回调作用域 |
| VM-4 | AC-2.1~AC-2.5, R-7~R-11 | offset/scale/build 参数化测试 | 临时副本、NearZero 和事件家族边界 |

## API 变更分析

> 本特性为内部 Pipeline/EventManager 能力补录，不新增或修改 ArkTS/Native 公共 API。

### 新增 API

N/A。

### 变更/废弃 API

N/A。原本文档中的 BuilderNode/PostEvent 公共接口已迁移至 Func-04-04-03-Feat-04。

## 接口规格

### 接口定义

**PipelineContext/EventManager 跨容器内部入口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `PipelineContext::OnTouchEvent(const TouchEvent&, bool isSubPipe)`；`EventManager::TouchTest(..., bool needAppend)` |
| 返回值 | void |
| 开放范围 | InnerApi |
| 错误码 | N/A；无效节点或 Pipeline 直接跳过 |
| 关联 AC | AC-1.1~AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| touchEvent | TouchEvent | 是 | 无 | 跨 Pipeline 追加从 DOWN 建链 |
| isSubPipe/needAppend | bool | 是 | false | true 表示追加目标且子 Pipeline 只建链 |
| offset | Offset | 是 | 0 | 子 Pipeline 相对主 Pipeline 全局偏移 |
| viewScale | float | 是 | 1 | 近零时坐标恢复按1处理 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 主 Pipeline 命中子 Pipeline | 递归建链、追加目标并恢复实例上下文 | AC-1.1~AC-1.6 |
| 2 | 子目标具有 offset/viewScale | Dispatch/Handle 使用目标自己的临时坐标副本 | AC-2.1~AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；仅重新划分规格归属。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；目标链只存在于当前触摸序列。
- **最低支持版本:** 内部能力随当前 ace_engine 主干。
- **API 版本号策略:** 不形成新的公共 API 版本承诺。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 正常序列复用 | 跨容器目标加入当前真实触摸目标链，不建立独立 PostEvent 状态 | AC-1.3~AC-1.5 |
| 目标级坐标 | offset/viewScale 保存在新增目标上，不改写共享事件 | AC-2.1~AC-2.4 |
| 实例隔离 | 递归调用结束必须恢复父 instanceId 和 ContainerScope | AC-1.6 |
| 范围隔离 | BuilderNode/Native 自定义输入投递由 Feat-04 承接 | AC-1.1~AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 每个已登记子 Pipeline 在 DOWN 阶段最多递归命中一次 | Pipeline trace/单测 | `pipeline_context.cpp:3998-4008` |
| 功耗 | 不新增周期任务，只随正常触摸 DOWN 执行 | 架构审查 | `pipeline_context.cpp:3915-4017` |
| 内存 | 复用同一 pointer ID 目标链，仅为目标保存 offset/viewScale | 单测/泄漏检查 | `event_manager.cpp:161-170` |
| 安全 | 无跨进程数据注入和新增权限 | 架构审查 | Pipeline 内部调用链 |
| 可靠性 | 无效弱引用子 Pipeline 被跳过，递归完成后恢复父实例 | 异常路径测试 | `pipeline_context.cpp:3998-4011` |
| 可测试性 | offset、scale、build 宏和目标顺序均可独立参数化 | Host 单测 | EventManager/Pipeline 测试 |
| 自动化维测 | 复用现有输入 trace 和 TouchTest 记录 | Trace 验证 | `pipeline_context.cpp:3941-3946` |
| 定界定位 | Pipeline 负责递归，EventManager 负责拼链，TouchEventTarget 负责坐标副本 | 源码审查 | 三层 source evidence |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板 | 标准主/子 Pipeline 拼链 | 按 offset/viewScale 恢复坐标 | Plugin/Form 集成测试 | `pipeline_context.cpp:3998-4008` |
| 折叠屏/多窗口 | 容器 offset 和缩放更易不同 | 每目标独立保存坐标上下文 | 多窗口测试 | `event_manager.cpp:161-170` |
| 非标准系统构建 | 不安装子目标 offset/viewScale | 目标处理原事件 | 编译宏测试 | `event_manager.cpp:161-168` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 子 Pipeline 模式不会在子入口重复执行无障碍处理 | AC-1.2 |
| 大字体 | 否 | 与字体无关 | N/A |
| 深色模式 | 否 | 与颜色模式无关 | N/A |
| 多窗口/分屏 | 是 | offset/viewScale 和 ContainerScope 影响坐标及回调上下文 | AC-1.6、AC-2.1~AC-2.4 |
| 多用户 | 否 | 无持久化或跨用户状态 | N/A |
| 版本升级 | 否 | 不形成公共版本边界 | N/A |
| 生态兼容 | 是 | 链顺序和坐标恢复影响 Plugin/Form 内既有手势 | AC-1.3~AC-2.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 跨容器事件分发
  作为 ArkUI 事件框架
  我想要把子 Pipeline 目标合并到当前触摸链
  以便跨容器组件参与同一次分发

  Scenario: 子 Pipeline 只建链并追加到当前结果
    Given 主 Pipeline 的 DOWN 命中已登记子 Pipeline
    When 子 Pipeline 以 isSubPipe=true 递归处理
    Then 子目标被追加到当前 pointer ID 的目标链
    And 子 Pipeline 不独立执行最终分发

  Scenario: 子目标恢复自己的坐标
    Given 子目标 offset 非零且 viewScale 为 2
    When 目标执行 Dispatch 或 Handle
    Then 使用 (坐标-offset)/2 的临时事件副本
    And 原始共享事件保持不变

  Scenario: 递归结束恢复父实例
    Given 子 Pipeline 处理期间修改了 EventManager instanceId
    When 所有子 Pipeline 返回
    Then instanceId 恢复为父 Pipeline 的实例
```

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围仅包含跨 Pipeline 拼链和坐标恢复
- [x] 自定义输入构造与 PostEvent 已迁移到 Feat-04
- [x] AC 与规则表交叉一致
- [x] 每条规则均可复现、可观测并标注边界

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "PipelineContext touchPluginPipelineContext isSubPipe EventManager needAppend"
  - repo: "openharmony/arkui_ace_engine"
    query: "SetSubPipelineGlobalOffset viewScale TouchEventTarget"
```

**关键文档：** `specs/04-common-capability/04-common-events/03-event-dispatch-intercept/design.md`；`frameworks/core/pipeline_ng/pipeline_context.cpp`；`frameworks/core/common/event_manager.cpp`
