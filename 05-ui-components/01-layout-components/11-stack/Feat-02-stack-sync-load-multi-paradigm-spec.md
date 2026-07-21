# 特性规格

> Func-05-01-11-Feat-02 Stack 子节点分帧加载与多范式接口：补录 `syncLoad` 的默认值、启用条件、截止时间续帧，以及 Dynamic、Static、Modifier 和 native 入口的存量映射。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Stack 子节点分帧加载与多范式接口 |
| 特性编号 | Func-05-01-11-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

Stack 默认在一个布局帧内同步测量全部子节点。API 26 的 `syncLoad(false)` 在容器已有确定 self ideal size 时允许 Box 测量遍历受帧截止时间约束；超时后 `StackPattern` 标记并安排后续帧继续 Measure。接口表面同时覆盖 API 7 Dynamic、API 12 Modifier、API 23 Static 和 API 26 Static 扩展，最终收敛到 `StackLayoutProperty`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | syncLoad 同步/分帧加载规格 | 覆盖默认值、启用条件、截止时间和多帧收敛 |
| ADDED | Dynamic/Static/Modifier 接口映射 | 覆盖构造、属性、style builder、ExtendableStack 和 reset |
| ADDED | 版本与遗留接口风险 | 区分 canonical SDK 能力与 legacy 空实现 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/11-stack/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/stack.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/stack.static.d.ets` | 已核对 |
| Stack Pattern/Property | `frameworks/core/components_ng/pattern/stack/stack_pattern.cpp`、`frameworks/core/components_ng/pattern/stack/stack_layout_property.h` | 已核对 |
| Box Algorithm | `frameworks/core/components_ng/layout/box_layout_algorithm.cpp` | 已核对 |

> 本文档不设计新的异步布局机制，也不纳入 LazyDynamicLayout 或 NDK。当前实现与已发布 SDK 是本次补录范围。

## 用户故事

### US-1: 控制子节点是否在单帧同步加载

**作为** 包含大量 Stack 子节点的应用开发者  
**我想要** 选择同步完成或跨帧完成子节点测量  
**以便** 在首帧完整性与帧耗时之间取舍

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 未调用 `syncLoad`、传入 undefined 后 reset 或显式设置 true THEN Stack 的有效 `syncLoad` 为 true，并在当前测量遍历中同步处理全部可测子项 | 边界 |
| AC-1.2 | WHEN 设置 `syncLoad(false)` 且 Stack 具有有效 self ideal size THEN 子项测量启用帧截止时间，允许期限到达后停止本帧剩余子项 | 正常 |
| AC-1.3 | WHEN 设置 `syncLoad(false)` 但 self ideal size 不完整或无效 THEN 算法不进入分帧期限路径，继续按普通 Stack 测量语义确定容器尺寸 | 边界 |
| AC-1.4 | WHEN 在分帧进行中把 `syncLoad` 改回 true THEN 下一次 Measure 不再因期限提前结束，并最终测量全部剩余有效子项 | 边界 |

### US-2: 在后续帧完成未测子节点

**作为** ArkUI 框架维护者  
**我想要** 分帧中断后可靠安排下一帧重测  
**以便** 布局最终收敛且节点销毁时不访问失效状态

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Box 子项遍历在截止时间到达前尚未完成 THEN 当前帧停止后续子项测量，并把 Stack 标记为需要异步续测 | 正常 |
| AC-2.2 | WHEN Pattern 检测到异步续测需求 THEN 通过 Pipeline 安排下一帧并将节点标记为 Measure dirty，后续帧继续处理未完成子项 | 正常 |
| AC-2.3 | WHEN 后续帧已测量全部子项 THEN 清除继续调度条件，不因历史超时无限请求帧 | 正常 |
| AC-2.4 | WHEN Stack 在续帧任务执行前离开树或销毁 THEN 任务在节点/上下文不可用时安全退出，不解引用失效对象 | 异常 |

### US-3: 通过多种 ArkUI 范式设置同一能力

**作为** 使用不同 ArkUI 编程范式的开发者  
**我想要** 通过对应版本支持的 Stack API 获得一致的最终布局状态  
**以便** 在 Dynamic、Static 和 Modifier 代码间迁移

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN API 7+ Dynamic 调用 Stack/alignContent THEN 参数经 JS/ArkTS bridge 与 node modifier 写入同一 Stack FrameNode | 正常 |
| AC-3.2 | WHEN API 12+ 使用 `StackModifier.applyNormalAttribute` THEN modifier 可应用 StackAttribute 支持的普通属性，最终状态与直接属性调用共享 Model/Property | 正常 |
| AC-3.3 | WHEN API 23+ Static 使用 `Stack(options, content_)` THEN Static 构造建立 Stack 并执行 content builder；API 26 可使用 style builder、`setStackOptions` 和 `ExtendableStack` | 正常 |
| AC-3.4 | WHEN API 26 Dynamic/Static 设置或 reset `syncLoad` THEN boolean 写入/恢复有效默认 true，并触发需要的布局更新 | 正常 |
| AC-3.5 | WHEN legacy `stackFit` 或 `overflow` 绑定被调用 THEN 不将其视为 canonical Stack 新能力；NG 空实现不得写入本文定义的布局状态 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Property/Algorithm UT | `frameworks/core/components_ng/pattern/stack/stack_layout_property.h:33-68`; `frameworks/core/components_ng/pattern/stack/stack_layout_algorithm.cpp:105-121` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | Deadline/续帧/生命周期 UT | `frameworks/core/components_ng/layout/box_layout_algorithm.cpp:27-61`; `frameworks/core/components_ng/pattern/stack/stack_pattern.cpp:35-66`; `test/unittest/core/pattern/stack/stack_new_test_ng.cpp:1132-1192,1279-1323` |
| AC-3.1~AC-3.5 | R-9~R-13 | 已有实现 | SDK 编译 + modifier UT | `frameworks/core/interfaces/native/node/node_stack_modifier.cpp:32-155`; `frameworks/core/interfaces/native/implementation/stack_modifier.cpp:44-128` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | syncLoad 未设置/true/reset | 有效值为 true，当前遍历同步测量全部子项 | LayoutProperty 默认 true | AC-1.1 |
| R-2 | 行为 | syncLoad=false 且 self ideal size 有效 | 向 Box 测量提供截止时间，允许提前结束 | 必须同时满足两个条件 | AC-1.2 |
| R-3 | 边界 | syncLoad=false 但 self ideal size 无效 | 不启用截止时间中断 | 包裹内容需先获得完整子项尺寸 | AC-1.3 |
| R-4 | 恢复 | 分帧中切回 true | 后续 Measure 同步完成剩余子项 | 已完成子项可按框架脏标记规则复用 | AC-1.4 |
| R-5 | 行为 | 子项遍历达到 deadline | 停止本帧继续测量并记录未完成 | 不在后台线程继续 | AC-2.1 |
| R-6 | 行为 | StackPattern 发现未完成 | 请求下一帧并标记 Measure dirty | 复用 Pipeline 调度 | AC-2.2 |
| R-7 | 恢复 | 全部子项完成 | 不再建立续帧任务 | 防止空转调度 | AC-2.3 |
| R-8 | 异常 | 节点/上下文在任务执行前失效 | 安全退出 | 不延长节点生命周期 | AC-2.4 |
| R-9 | 行为 | Dynamic Stack 调用 | Bridge/modifier 下沉到 StackModelNG | API 7 起可用 | AC-3.1 |
| R-10 | 行为 | Modifier 应用普通属性 | 通过 StackAttribute 更新同一节点状态 | Modifier API 12 起 | AC-3.2 |
| R-11 | 行为 | Static 构造/样式/扩展类 | 调用 Static 构造并更新共享 FrameNode | 基础 API 23；扩展 API 26 | AC-3.3 |
| R-12 | 行为 | Dynamic/Static syncLoad set/reset | 写 boolean；reset 恢复 true并触发布局更新 | API 26 | AC-3.4 |
| R-13 | 边界 | legacy stackFit/overflow | 不进入 canonical 规格，NG no-op 不产生状态 | 仅兼容风险 | AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | NG Property/Layout UT | 默认 true、false 启用条件、动态切换 |
| VM-2 | R-5~R-8, AC-2.1~AC-2.4 | 模拟 Deadline 的多帧 UT | 中断位置、dirty、收敛与节点销毁 |
| VM-3 | R-9~R-12, AC-3.1~AC-3.4 | SDK 编译 + Dynamic/Static/Modifier UT | API 可见性、set/reset 和最终属性一致性 |
| VM-4 | R-13, AC-3.5 | legacy 回归 + 代码审查 | 空实现不形成公开契约 |

## API 变更分析

> 下表是已有 API 的补录，不表示本轮提交新增接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `syncLoad(enable: boolean)` | Public Dynamic | 是否单帧同步加载 | `StackAttribute` | N/A | API 26 控制子节点同步/分帧测量 | AC-1.1~AC-2.4 |
| Static `syncLoad(enable?: boolean)` | Public Static | boolean/undefined | `this` | N/A | API 26 Static 设置或 reset | AC-1.1, AC-3.4 |
| `setStackOptions(options?)` | Public Static | StackOptions | `this` | N/A | API 26 Static 更新构造 options | AC-3.3 |
| Static style `Stack(style, content_?)` | Public Static | 属性 builder 与内容 builder | `StackAttribute` | N/A | API 26 样式构造 | AC-3.3 |
| `ExtendableStack` | Public Static | factory/options/content/style | 实例/void | N/A | API 26 可扩展 Stack | AC-3.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `stackFit` / `overflow` legacy 绑定 | 非 canonical 风险 | 旧前端符号存在但 NG 不承载行为 | 不用于新代码；以 Stack SDK 公开项为准 | AC-3.5 |

## 接口规格

### 接口定义

**StackAttribute.syncLoad(enable)**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic `syncLoad(enable: boolean): StackAttribute`；Static `syncLoad(enable: boolean \| undefined): this` |
| 返回值 | 当前 Stack 属性对象 |
| 开放范围 | Public，Stage 模型；Dynamic/Static API 26 |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.4, AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| enable | boolean | Dynamic 是；Static 可 undefined | true | false 只有在 self ideal size 有效时启用期限中断 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | true/缺省/reset | 同一帧遍历全部子项 | AC-1.1 |
| 2 | false + 有效 self ideal size + 超期 | 停止本帧并安排下一帧 | AC-1.2, AC-2.1~AC-2.3 |
| 3 | false + 包裹内容尺寸 | 不启用分帧期限路径 | AC-1.3 |
| 4 | 节点销毁 | 待执行任务安全退出 | AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；`syncLoad` 是 API 26 扩展，早期 Stack 行为保持同步加载。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；属性和续帧状态不持久化。
- **最低支持版本:** Stack Dynamic API 7；Modifier API 12；Static API 23；syncLoad/Static 扩展 API 26。
- **API 版本号策略:** 以 canonical SDK 动态/静态标记为准；legacy 符号不提升为公开能力。

| 表面 | 版本 | 证据 |
|------|------|------|
| Dynamic Stack | API 7 | `interface/sdk-js/api/@internal/component/ets/stack.d.ts:58-80` |
| StackModifier | API 12；crossplatform dynamic 注记 API 20 | `interface/sdk-js/api/arkui/StackModifier.d.ts:24-57` |
| Static Stack | API 23 | `interface/sdk-js/api/arkui/component/stack.static.d.ets:121-139` |
| syncLoad 与 Static 扩展 | API 26 | `interface/sdk-js/api/@internal/component/ets/stack.d.ts:125-137`; `interface/sdk-js/api/arkui/component/stack.static.d.ets:73-107,141-197` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| UI 线程分帧 | 分帧只跨 Pipeline frame，不把布局迁移到后台线程 | AC-1.2, AC-2.1~AC-2.3 |
| 确定尺寸前提 | self ideal size 无效时不得只测部分子项确定包裹尺寸 | AC-1.3 |
| 属性单一来源 | 所有范式最终读写 StackLayoutProperty | AC-3.1~AC-3.4 |
| 弱生命周期 | 续帧任务不得拥有已销毁节点的强生命周期 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | syncLoad=false 时单帧测量在截止时间处停止；总测量复杂度仍为 O(n) | Trace/大量子项基准 | `frameworks/core/components_ng/layout/box_layout_algorithm.cpp:27-61` |
| 功耗 | 完成全部子项后不得继续请求空帧 | 帧调度计数 UT | AC-2.3 |
| 内存 | 续帧不复制子树，不因任务延长已销毁节点生命周期 | 生命周期/内存 UT | AC-2.4 |
| 安全 | 不涉及权限或敏感数据 | 代码审查 | SDK SysCap |
| 可靠性 | 切换 true/false、超时和销毁路径不得丢失最终 Measure | 多帧压力 UT | VM-1, VM-2 |
| 可测试性 | Deadline 可注入，完成子项数和 dirty 状态可观测 | 单元测试 | `test/unittest/core/pattern/stack/stack_new_test_ng.cpp:1132-1323` |
| 自动化维测 | 可记录每帧完成子项数和是否再次 dirty | Trace/日志 | Pattern/Pipeline |
| 定界定位 | 区分参数解析、Property 条件、Box 中断、Pattern 调度四层 | 源码追溯 | `design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无接口差异 | 帧预算由当前 Pipeline 决定 | 大子树性能测试 | AC-2.1~AC-2.3 |
| 平板 | 无接口差异 | 更大窗口可能增加子节点数量但不改变条件 | 多窗口压力测试 | AC-1.2 |
| 折叠屏 | 无 Stack 专有差异 | 折叠导致重新布局时仍按当前 syncLoad 执行 | 状态切换测试 | AC-1.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 分帧期间语义节点生命周期保持，不重排子树 | AC-2.1~AC-2.4 |
| 大字体 | 是 | 字体导致 Measure dirty 后按当前 syncLoad 重新测量 | AC-1.1~AC-1.3 |
| 深色模式 | 否 | 不涉及颜色 | N/A |
| 多窗口/分屏 | 是 | 约束变化触发新一轮同步或分帧测量 | AC-1.2, AC-1.3 |
| 多用户 | 否 | 无持久用户状态 | N/A |
| 版本升级 | 是 | API 7/12/23/26 可见性必须保持 | AC-3.1~AC-3.4 |
| 生态兼容 | 是 | 默认 true 和 Static/Dynamic reset 语义不得漂移 | AC-1.1, AC-3.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Stack 子节点分帧加载
  Scenario: 确定尺寸下跨帧完成
    Given 一个具有显式宽高且包含大量子项的 Stack
    And syncLoad 为 false
    When 第一帧测量到达截止时间
    Then 停止测量剩余子项
    And Stack 被安排在下一帧继续 Measure
    When 全部子项完成
    Then 不再请求额外续帧

  Scenario: 包裹内容时保持完整测量
    Given 一个没有有效 self ideal size 的 Stack
    And syncLoad 为 false
    When 执行 Measure
    Then 不使用截止时间提前结束

  Scenario: reset 恢复同步
    Given Static Stack 已设置 syncLoad(false)
    When 调用 syncLoad(undefined)
    Then 有效值恢复 true
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖 syncLoad、续帧和 Stack 多范式接口
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则满足可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] legacy stackFit/overflow 只列风险，NDK 与 LazyDynamicLayout 明确排除

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Stack syncLoad deadline BoxLayoutAlgorithm StackPattern next frame node modifier"
  - repo: "openharmony/interface_sdk-js"
    query: "Stack syncLoad Static ExtendableStack StackModifier API 12 23 26"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/stack.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/component/stack.static.d.ets`
- 架构设计：`05-ui-components/01-layout-components/11-stack/design.md`
