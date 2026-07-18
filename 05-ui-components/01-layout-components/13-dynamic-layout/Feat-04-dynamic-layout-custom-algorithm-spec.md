# 特性规格

> Func-05-01-13-Feat-04 DynamicLayout 自定义测量与布局算法：补录 onMeasure/onLayout 回调、FrameNode 操作优先级、缺失回调的 Box/Stack 分阶段回退、脚本上下文生命周期和运行时切换。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DynamicLayout 自定义测量与布局算法 |
| 特性编号 | Func-05-01-13-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 24 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

`CustomLayoutAlgorithm` 允许应用在布局阶段接收 DynamicLayout 的 FrameNode 及 LayoutConstraint/Position，通过 FrameNode API 测量、设置容器尺寸并定位子项。`DynamicLayoutAlgorithm` 按阶段委托 callback：缺失 onMeasure 时使用 Box 测量，缺失 onLayout 时使用 Stack 布局。SDK 规定回调内不应修改状态变量，并明确自定义 FrameNode 操作相对通用尺寸、border 和 safe-area 属性的优先级。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | onMeasure 自定义测量规格 | 覆盖 self/constraint、子项 measure、setMeasuredSize 和优先级 |
| ADDED | onLayout 自定义定位规格 | 覆盖 self/position、子项 layout 和 safe-area 优先级 |
| ADDED | callback fallback 与生命周期规格 | 覆盖四种组合、VM/弱引用、异常、算法切换和状态修改约束 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/13-dynamic-layout/design.md` | 已补录 |
| DynamicLayout SDK | `interface/sdk-js/api/@ohos.arkui.components.ArkDynamicLayout.d.ts` | 已核对 |
| LayoutAlgorithm SDK | `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts` | 已核对 |
| Custom Algorithm | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_algorithm.cpp` | 已核对 |
| Dynamic/Static bridges | `frameworks/core/components_ng/pattern/dynamiclayout/bridge/arkts_native_dynamic_layout_bridge.cpp`、`frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/src/ani/native/dynamiclayout/dynamiclayout_module.cpp` | 已核对 |

> 本文档不新增 FrameNode 方法，也不为应用 custom 算法正确性提供自动排版保证；它只定义框架调用和回退契约。

## 用户故事

### US-1: 自定义测量容器和子组件

**作为** 高级布局开发者  
**我想要** 在 onMeasure 中读取约束并显式测量子节点  
**以便** 实现预置算法无法表达的瀑布流或几何策略

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN DynamicLayout 使用具有 onMeasure 的 CustomLayoutAlgorithm THEN 每次有效 Measure 阶段调用一次 onMeasure，并传入当前 DynamicLayout FrameNode self 与当前 LayoutConstraint | 正常 |
| AC-1.2 | WHEN 回调通过 `self.getChild(...)` 获得子 FrameNode 并调用 child.measure(constraint) THEN 子项按应用传入约束测量，结果可用于计算容器尺寸 | 正常 |
| AC-1.3 | WHEN 回调调用 `self.setMeasuredSize(size)` THEN 该显式 measured size 对 DynamicLayout 容器的优先级高于通用 sizing 和 border styling 对最终测量尺寸的推导 | 正常 |
| AC-1.4 | WHEN 回调没有为 self 设置合法尺寸、传入负/非有限值或访问不存在 child THEN 框架/FrameNode 既有校验不得产生崩溃或未初始化 Geometry | 异常 |
| AC-1.5 | WHEN onMeasure 内修改 ArkTS 状态变量 THEN 该用法违反 SDK 约束；框架不保证同步重入结果，测试应识别潜在重复布局风险 | 边界 |

### US-2: 自定义定位子组件

**作为** 高级布局开发者  
**我想要** 在 onLayout 中按已测尺寸定位每个子组件  
**以便** 形成任意二维排列

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN CustomLayoutAlgorithm 具有 onLayout THEN 每次有效 Layout 阶段调用一次 onLayout，并传入当前 self FrameNode 与 DynamicLayout 的 Position | 正常 |
| AC-2.2 | WHEN 回调对 child FrameNode 调用 `layout(position)` THEN 子项按该位置提交布局，且该显式 measure/layout 操作优先于子项 `ignoreLayoutSafeArea` 的自动处理 | 正常 |
| AC-2.3 | WHEN 多个子项被定位到相同区域 THEN 框架保留应用指定几何和既有子节点绘制顺序，不自动消解重叠 | 边界 |
| AC-2.4 | WHEN child 不存在、已销毁或 position 非法 THEN FrameNode/bridge 安全拒绝或忽略该操作，不使其他合法子项无法布局 | 异常 |
| AC-2.5 | WHEN onLayout 内修改状态变量引发新 dirty THEN 当前回调不得同步重入自身；新布局只可由后续 Pipeline 处理，且该写法不受 SDK 推荐 | 边界 |

### US-3: 在回调缺失或上下文失效时回退

**作为** ArkUI 框架维护者  
**我想要** custom 算法始终有合法的测量/布局路径  
**以便** 部分实现、算法切换或脚本销毁不会导致空几何

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN CustomLayoutAlgorithm 缺少 onMeasure 但有 onLayout THEN Measure 阶段使用 BoxLayoutAlgorithm 默认测量，Layout 阶段仍执行应用 onLayout | 边界 |
| AC-3.2 | WHEN 有 onMeasure 但缺少 onLayout THEN Measure 执行应用 callback，Layout 阶段使用 StackLayoutAlgorithm 默认定位 | 边界 |
| AC-3.3 | WHEN 两个 callback 都缺失/不可调用 THEN 分别使用 Box measure 与 Stack layout，容器仍得到合法默认几何 | 边界 |
| AC-3.4 | WHEN 两个 callback 都有效 THEN 不额外执行阶段 fallback 覆盖应用结果 | 正常 |
| AC-3.5 | WHEN 节点、VM、weak self 或脚本函数在回调前失效 THEN wrapper 安全退出并由阶段可用的 fallback/既有几何处理，不访问悬空上下文 | 异常 |
| AC-3.6 | WHEN 从 Custom 切换到 preset 或替换为新的 Custom 实例 THEN 旧 callbacks 不再用于后续布局，节点与子组件状态继续保持 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | Custom Measure/FrameNode UT | `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:42-86`; `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_algorithm.cpp:25-38`; `test/unittest/core/pattern/dynamiclayout/dynamic_layout_pattern_test_ng.cpp:46-199` |
| AC-2.1~AC-2.5 | R-6~R-10 | 已有实现 | Custom Layout/FrameNode UT | `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:87-113`; `interface/sdk-js/api/@ohos.arkui.components.ArkDynamicLayout.d.ts:62-69`; `test/unittest/core/pattern/dynamiclayout/dynamic_layout_pattern_test_ng.cpp:46-199` |
| AC-3.1~AC-3.6 | R-11~R-16 | 已有实现 | 四组合/VM 销毁/切换 UT | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_algorithm.cpp:25-38`; `frameworks/core/components_ng/pattern/dynamiclayout/bridge/arkts_native_dynamic_layout_bridge.cpp:326-415`; `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/src/ani/native/dynamiclayout/dynamiclayout_module.cpp:333-399,427-479`; `test/unittest/core/pattern/dynamiclayout/frame_node_test_dynamic_layout.cpp:61-162` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | onMeasure 有效 | 传 self + constraint 调用一次 | 布局阶段/有效 VM 上下文 | AC-1.1 |
| R-2 | 行为 | 回调测量 child | 使用应用传入 constraint 更新 child measured geometry | child 通过 FrameNode API 获取 | AC-1.2 |
| R-3 | 行为 | self.setMeasuredSize | 显式容器尺寸优先于 sizing/border 推导 | 仍受 FrameNode 合法值检查 | AC-1.3 |
| R-4 | 异常 | self size/child/数值非法 | 安全拒绝/回退，不留下未初始化 Geometry | 不使其他 child 崩溃 | AC-1.4 |
| R-5 | 边界 | callback 修改状态 | 不保证同步结果且不得同步重入 | SDK 明确不应修改 | AC-1.5 |
| R-6 | 行为 | onLayout 有效 | 传 self + position 调用一次 | Layout 阶段 | AC-2.1 |
| R-7 | 行为 | child.layout(position) | 提交应用位置；显式操作优先 safe-area 自动处理 | 应用负责合法几何 | AC-2.2 |
| R-8 | 边界 | 多 child 重叠 | 保留应用位置和绘制顺序 | 不自动避让 | AC-2.3 |
| R-9 | 异常 | child/position 非法 | 安全忽略/拒绝该操作 | 其他 child 可继续 | AC-2.4 |
| R-10 | 边界 | onLayout 修改状态 | 后续 Pipeline 处理，不同步重入 | SDK 不推荐 | AC-2.5 |
| R-11 | 恢复 | measure callback 缺失 | Box 默认 measure | layout callback 可独立存在 | AC-3.1 |
| R-12 | 恢复 | layout callback 缺失 | Stack 默认 layout | measure callback 可独立存在 | AC-3.2 |
| R-13 | 恢复 | 两 callback 都缺失 | Box + Stack 组合 fallback | 产生合法默认几何 | AC-3.3 |
| R-14 | 行为 | 两 callback 都有效 | 各阶段只执行应用回调 | fallback 不覆盖 | AC-3.4 |
| R-15 | 异常 | node/VM/function 失效 | 弱引用/上下文检查失败后退出 | 不访问悬空对象 | AC-3.5 |
| R-16 | 恢复 | Custom 切换/替换 | 停止旧 callback 并使用新 Pattern/函数 | node/children 保持 | AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | FrameNode Measure mock | self/constraint、child.measure、measured size 优先级和非法值 |
| VM-2 | R-6~R-10, AC-2.1~AC-2.5 | FrameNode Layout mock | self/position、child.layout、safe-area 优先级、重叠和重入 |
| VM-3 | R-11~R-14, AC-3.1~AC-3.4 | 四种 callback 组合参数化 UT | Box/Stack fallback 与不覆盖有效结果 |
| VM-4 | R-15~R-16, AC-3.5~AC-3.6 | VM/node 销毁和算法快速切换 UT | 弱生命周期、旧 callback 隔离、状态保持 |

## API 变更分析

> 本文档补录 API 24 已有 CustomLayoutAlgorithm。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `CustomLayoutAlgorithm` | Public | 无构造 options | CustomLayoutAlgorithm | N/A | DynamicLayout 自定义算法对象 | AC-1.1~AC-3.6 |
| `onMeasure(self, constraint)` | Public callback | FrameNode、LayoutConstraint | void | N/A | 自定义测量 | AC-1.1~AC-1.5 |
| `onLayout(self, position)` | Public callback | FrameNode、Position | void | N/A | 自定义定位 | AC-2.1~AC-2.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | API 24 首次提供 | 无需迁移 | AC-1.1~AC-3.6 |

## 接口规格

### 接口定义

**CustomLayoutAlgorithm.onMeasure**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onMeasure(self: FrameNode, constraint: LayoutConstraint): void` |
| 返回值 | void；通过 FrameNode 操作写几何 |
| 开放范围 | Public、API 24 |
| 错误码 | N/A；缺失时 Box fallback |
| 关联 AC | AC-1.1~AC-1.5, AC-3.1, AC-3.3~AC-3.5 |

**CustomLayoutAlgorithm.onLayout**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onLayout(self: FrameNode, position: Position): void` |
| 返回值 | void；通过 child FrameNode layout 写位置 |
| 开放范围 | Public、API 24 |
| 错误码 | N/A；缺失时 Stack fallback |
| 关联 AC | AC-2.1~AC-2.5, AC-3.2~AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 约束 |
|------|------|------|------|
| self | FrameNode | 框架传入 | 当前 DynamicLayout 实体节点；只在回调有效期使用 |
| constraint | LayoutConstraint | onMeasure 传入 | 当前测量约束；应用传给 child 时需构造合法约束 |
| position | Position | onLayout 传入 | 当前容器布局位置；child position 由应用计算 |

**优先级**

| 操作 | 优先于 | 证据 |
|------|--------|------|
| self.setMeasuredSize | DynamicLayout sizing 与 border styling 对尺寸推导 | `interface/sdk-js/api/@ohos.arkui.components.ArkDynamicLayout.d.ts:62-67` |
| child.measure / child.layout | child `ignoreLayoutSafeArea` 自动行为 | `interface/sdk-js/api/@ohos.arkui.components.ArkDynamicLayout.d.ts:67-69` |

## 兼容性声明

- **已有 API 行为变更:** 否；CustomLayoutAlgorithm 和回调均为 API 24。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；callback/FrameNode 状态不持久化。
- **最低支持版本:** API 24。
- **API 版本号策略:** Dynamic/Static callback 签名都以 API 24 SDK 为准，不向低版本模拟。

| 表面 | SDK 位置 |
|------|----------|
| Dynamic custom class/callbacks | `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:42-113` |
| Static custom class/callbacks | `interface/sdk-js/api/arkui/LayoutAlgorithm.static.d.ets:28-107` |
| DynamicLayout 优先级说明 | `interface/sdk-js/api/@ohos.arkui.components.ArkDynamicLayout.d.ts:50-80` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| FrameNode API 边界 | callback 不直接访问 C++ GeometryNode，仅经公开 FrameNode 方法 | AC-1.2~AC-2.4 |
| 阶段隔离 | onMeasure 只负责测量，onLayout 只负责定位 | AC-1.1, AC-2.1, AC-3.1~AC-3.4 |
| 分阶段 fallback | 一个 callback 缺失不禁用另一个 | AC-3.1~AC-3.4 |
| UI/VM 生命周期 | callback 只在有效节点和脚本上下文执行 | AC-3.5, AC-3.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 框架每阶段至多调用一次对应 callback；应用算法复杂度由应用负责 | 回调计数/trace | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_algorithm.cpp:25-38` |
| 功耗 | 无后台任务；只在布局 dirty 时调用 callback | 帧计数 | VM-1~VM-3 |
| 内存 | callback wrapper 不强持有已销毁 FrameNode/VM | 泄漏/弱引用 UT | AC-3.5, AC-3.6 |
| 安全 | 非法 FrameNode/数值/脚本异常不得导致 native 悬空访问 | fuzz/故障注入 | AC-1.4, AC-2.4, AC-3.5 |
| 可靠性 | 四种 callback 组合都产生合法几何或安全 fallback | 参数化 UT | VM-3 |
| 可测试性 | callback 次数、参数、FrameNode 调用和 Geometry 可 mock/断言 | Algorithm UT | VM-1~VM-4 |
| 自动化维测 | trace callback 进入/退出、fallback 原因和耗时 | trace/hilog | Bridge/Algorithm |
| 定界定位 | 区分应用算法错误、Bridge callback、FrameNode 校验和 fallback | 源码追溯 | `design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无框架语义差异 | 应用按当前约束实现算法 | 多尺寸测试 | AC-1.1, AC-1.2 |
| 平板 | 更大约束可能增加应用算法工作量 | 框架仍各阶段一次回调 | 大子树性能测试 | NFR 性能 |
| 折叠屏 | 约束/position 随姿态变化 | callback 收到最新参数，节点状态保持 | 姿态切换测试 | AC-1.1, AC-2.1, AC-3.6 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 框架保留子节点身份；自定义视觉顺序/重叠需应用保证可访问性 | AC-2.2, AC-2.3 |
| 大字体 | 是 | 字体变化触发新 constraint，应用必须重新测量 | AC-1.1, AC-1.2 |
| 深色模式 | 否 | 不涉及颜色 | N/A |
| 多窗口/分屏 | 是 | constraint/position 变化后回调再次执行 | AC-1.1, AC-2.1 |
| 多用户 | 否 | 无持久状态 | N/A |
| 版本升级 | 是 | API 24 前不可见 | API 声明 |
| 生态兼容 | 是 | callback 参数、优先级和 Box/Stack fallback 需稳定 | AC-1.3, AC-2.2, AC-3.1~AC-3.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: DynamicLayout 自定义算法
  Scenario: 完整自定义测量和布局
    Given CustomLayoutAlgorithm 同时实现 onMeasure 与 onLayout
    When Pipeline 执行布局
    Then onMeasure 收到 self 和当前 constraint
    And onLayout 收到 self 和当前 position
    And fallback 不覆盖应用设置的尺寸和位置

  Scenario: 只实现 onLayout
    Given CustomLayoutAlgorithm 没有可调用 onMeasure
    And 实现 onLayout
    When Pipeline 执行布局
    Then Measure 使用 Box fallback
    And Layout 调用应用 onLayout

  Scenario: 切换后旧回调失效
    Given 当前使用 CustomLayoutAlgorithm A
    When 切换到 RowLayoutAlgorithm
    Then 后续布局不再调用 A
    And DynamicLayoutNode 与子组件状态保持
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖 CustomLayoutAlgorithm 调用、优先级、fallback 和生命周期
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则满足可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] SDK“不修改状态变量”约束、四种 callback 组合和多设备影响均已声明

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "DynamicLayoutAlgorithm custom onMeasure onLayout Box fallback Stack fallback weak FrameNode"
  - repo: "openharmony/interface_sdk-js"
    query: "CustomLayoutAlgorithm FrameNode setMeasuredSize measure layout priority safe area API 24"
```

**关键文档：**

- DynamicLayout SDK：`interface/sdk-js/api/@ohos.arkui.components.ArkDynamicLayout.d.ts`
- LayoutAlgorithm SDK：`interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts`
- 架构设计：`05-ui-components/01-layout-components/13-dynamic-layout/design.md`
