# 特性规格

> Func-05-01-11-Feat-01 Stack 叠放布局、尺寸与对齐：补录 Stack 创建、子节点覆盖顺序、内容尺寸、九宫格对齐、RTL 镜像与安全区分支的存量行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Stack 叠放布局、尺寸与对齐 |
| 特性编号 | Func-05-01-11-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

Stack 是允许多个子组件共享同一内容框的叠放容器。`StackModelNG` 创建 Stack Pattern，`StackLayoutAlgorithm` 以 Box 测量结果确定容器尺寸，再按容器 Alignment 或子项 `layoutGravity` 写入每个子节点偏移；后声明节点保持后绘制覆盖关系。核心实现见 `frameworks/core/components_ng/pattern/stack/stack_model_ng.cpp:23-39` 和 `frameworks/core/components_ng/pattern/stack/stack_layout_algorithm.cpp:26-103`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Stack 创建与叠放顺序规格 | 固化容器身份、多子节点和后节点覆盖行为 |
| ADDED | Stack 测量与尺寸规格 | 覆盖显式理想尺寸、包裹子项、padding/border 和约束 |
| ADDED | 九宫格、RTL 与安全区对齐规格 | 覆盖容器对齐、子项覆盖优先级和特殊分支 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/11-stack/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/stack.d.ts` | 已核对 |
| Stack Model | `frameworks/core/components_ng/pattern/stack/stack_model_ng.cpp` | 已核对 |
| Stack Algorithm | `frameworks/core/components_ng/pattern/stack/stack_layout_algorithm.cpp` | 已核对 |

> 本文档是存量能力补录。当前实现即规格；若实现细节与 canonical SDK 描述存在偏差，只在兼容风险中记录，不据此扩展接口。

## 用户故事

### US-1: 创建叠放容器

**作为** ArkUI 应用开发者  
**我想要** 在同一矩形区域依次叠放多个子组件  
**以便** 构建背景、内容和前景覆盖层

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `Stack()` THEN 创建可包含多个子节点的 Stack FrameNode，并使用 Stack Pattern、StackLayoutProperty 与 StackLayoutAlgorithm | 正常 |
| AC-1.2 | WHEN 多个普通流子节点参与布局 THEN 子节点共享同一内容框独立对齐，UI 树中后声明节点保持后绘制并覆盖先声明节点 | 正常 |
| AC-1.3 | WHEN Stack 没有子节点 THEN 容器仍按父约束、显式理想尺寸和 padding/border 得到合法非负尺寸，不访问不存在的子项 | 边界 |

### US-2: 按约束确定容器和子项尺寸

**作为** 布局开发者  
**我想要** Stack 在显式尺寸和包裹内容之间遵守统一测量约束  
**以便** 获得稳定可预测的叠放区域

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Stack 提供有效 self ideal width/height THEN 容器内容框以理想尺寸为基础并受 min/max 约束夹紧，子项在该内容框内测量 | 正常 |
| AC-2.2 | WHEN 某一轴没有有效 self ideal size THEN 该轴以参与测量子项在该轴的最大占用尺寸为基础，加 padding/border 后受父约束夹紧 | 正常 |
| AC-2.3 | WHEN 子项尺寸大于可用内容框 THEN 容器不得突破父 max 约束；子项的裁剪或溢出由通用属性处理，本 Feat 不改变其测量结果 | 边界 |
| AC-2.4 | WHEN 子项为 GONE 或不参与当前布局 THEN 该子项不扩大 Stack 的包裹内容尺寸，也不影响其他子项偏移 | 边界 |

### US-3: 对齐叠放子节点

**作为** ArkUI 应用开发者  
**我想要** 使用九宫格对齐并允许单个子项覆盖容器对齐  
**以便** 在同一 Stack 内定位不同覆盖层

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 未传入有效 `alignContent` THEN Stack 使用 `Alignment.Center` 对齐普通子项 | 边界 |
| AC-3.2 | WHEN 设置九宫格 Alignment THEN 每个子项基于 `contentSize - childSize` 计算对应水平和垂直偏移，并叠加 padding/border 起点 | 正常 |
| AC-3.3 | WHEN 子项设置有效 `layoutGravity` THEN 该子项使用自身 gravity，覆盖 Stack 的容器 Alignment；未设置的兄弟仍使用容器值 | 正常 |
| AC-3.4 | WHEN 布局方向为 RTL 且 Alignment 使用 Start/End 语义 THEN 水平方向镜像；垂直方向和子节点声明/覆盖顺序不改变 | 边界 |
| AC-3.5 | WHEN 子项命中安全区扩展布局分支 THEN 算法使用安全区计算的偏移路径，同时保持该子项的最终 Alignment 优先级 | 边界 |
| AC-3.6 | WHEN `alignContent` 输入非法 THEN 对外入口按 SDK 约定使用默认 Center，不写入越界对齐状态 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.3 | R-1~R-3 | 已有实现 | NG 创建/空容器 UT | `frameworks/core/components_ng/pattern/stack/stack_model_ng.cpp:23-39`; `frameworks/core/components_ng/pattern/stack/stack_pattern.h:26-85` |
| AC-2.1~AC-2.4 | R-4~R-7 | 已有实现 | Layout 约束矩阵 UT | `frameworks/core/components_ng/layout/box_layout_algorithm.cpp:27-61`; `frameworks/core/components_ng/pattern/stack/stack_layout_algorithm.cpp:105-121` |
| AC-3.1~AC-3.6 | R-8~R-12 | 已有实现 | Alignment/RTL/safe-area UT | `frameworks/core/components_ng/pattern/stack/stack_layout_algorithm.cpp:26-103`; `test/unittest/core/pattern/stack/stack_new_test_ng.cpp:31-156,768-886` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Stack 创建入口执行 | 创建 Stack FrameNode 并安装 Stack Pattern | `StackModelNG::Create` 是 NG 生产入口 | AC-1.1 |
| R-2 | 行为 | 多个子节点完成布局 | 每个子项独立计算偏移；不因叠放而重排 UI 树 | 绘制覆盖沿用 UI 树后序语义 | AC-1.2 |
| R-3 | 边界 | 子节点列表为空 | 只解析容器约束并结束，不迭代空子项 | 最终尺寸不得为负 | AC-1.3 |
| R-4 | 行为 | self ideal size 有效 | 以显式轴尺寸作为容器测量基准 | 仍受 min/max 及 padding/border 约束 | AC-2.1 |
| R-5 | 行为 | 某轴未指定理想尺寸 | 包裹该轴最大有效子项占用尺寸 | 多子项取最大值而非求和 | AC-2.2 |
| R-6 | 边界 | 子项超出内容框或父 max | 容器遵守父约束，溢出交由通用绘制/裁剪语义 | 本 Feat 不定义 clip 属性 | AC-2.3 |
| R-7 | 边界 | 子项 GONE/不参与布局 | 从包裹尺寸与定位遍历中跳过 | 不改变其他子项 Alignment | AC-2.4 |
| R-8 | 行为 | 未设置容器对齐 | 使用 Center | SDK 默认值见 `interface/sdk-js/api/@internal/component/ets/stack.d.ts:34-48` | AC-3.1 |
| R-9 | 行为 | 有效容器 Alignment | 按内容框与子项尺寸计算九宫格偏移 | 偏移叠加 padding/border 起点 | AC-3.2 |
| R-10 | 行为 | 子项具有 layoutGravity | 子项 gravity 覆盖容器 Alignment | 只影响该子项 | AC-3.3 |
| R-11 | 边界 | RTL 或安全区扩展 | RTL 镜像水平语义；安全区使用专用偏移分支 | 不反转绘制顺序 | AC-3.4, AC-3.5 |
| R-12 | 异常 | 对外输入 Alignment 非法 | 回退 Center 或执行入口既有 reset | 不传播非法枚举到布局计算 | AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-3, AC-1.1~AC-1.3 | NG UT | 节点身份、多子项、空容器与覆盖顺序 |
| VM-2 | R-4~R-7, AC-2.1~AC-2.4 | Layout UT + 约束矩阵 | ideal/min/max、最大子项、GONE 与溢出边界 |
| VM-3 | R-8~R-10, AC-3.1~AC-3.3 | 九宫格参数化 UT | 默认 Center、九种位置和 child gravity 优先 |
| VM-4 | R-11~R-12, AC-3.4~AC-3.6 | RTL/safe-area/非法值 UT | 水平镜像、专用分支和默认回退 |

## API 变更分析

> 本文档补录已发布接口，不引入新的 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `Stack(options?: StackOptions)` | Public Dynamic | `alignContent?: Alignment` | `StackAttribute` | N/A | API 7 创建叠放容器；API 18 规范化 options 类型 | AC-1.1~AC-3.2 |
| `alignContent(value: Alignment)` | Public Dynamic | 九宫格 Alignment | `StackAttribute` | N/A | 设置子项默认对齐 | AC-3.1~AC-3.6 |
| Static `Stack(options?, content_?)` | Public Static | options 与内容 builder | `StackAttribute` | N/A | API 23 Static 构造叠放容器 | AC-1.1~AC-3.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次仅补录现有 Stack 布局行为 | 无需迁移 | AC-1.1~AC-3.6 |

## 接口规格

### 接口定义

**Stack(options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Stack(options?: StackOptions): StackAttribute` |
| 返回值 | `StackAttribute` — 可继续设置 Stack 和通用属性 |
| 开放范围 | Public Dynamic；API 23+ 另有 Static builder |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | StackOptions | 否 | 空 options | API 18 完成匿名对象规范化 |
| options.alignContent | Alignment | 否 | Alignment.Center | 非法值按默认值处理；属性调用晚于构造时属性值优先 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 无 options/空子项 | 创建 Center 对齐容器并按约束得到合法尺寸 | AC-1.1, AC-1.3, AC-3.1 |
| 2 | 多子项与显式 Alignment | 独立定位并保持后节点覆盖 | AC-1.2, AC-3.2 |
| 3 | child gravity、RTL 或 safe-area | 使用相应优先级和专用偏移路径 | AC-3.3~AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否；API 7 基本行为、API 18 类型规范化和 API 23 Static 表面均按既有版本保留。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；Alignment 随 LayoutProperty 存在。
- **最低支持版本:** Dynamic Stack 为 API 7；Static Stack 为 API 23。
- **API 版本号策略:** 对外版本以 canonical SDK `@since` 为准，源码内部注释不单独形成公开版本。

| 版本 | 契约 | 证据 |
|------|------|------|
| API 7 | Dynamic Stack 与 `alignContent` | `interface/sdk-js/api/@internal/component/ets/stack.d.ts:58-113` |
| API 18 | `StackOptions` 命名接口规范化，不改变历史可用性 | `interface/sdk-js/api/@internal/component/ets/stack.d.ts:21-48` |
| API 23 | Static Stack builder 和 Static alignContent | `interface/sdk-js/api/arkui/component/stack.static.d.ets:28-72,121-139` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| UI 树顺序稳定 | Stack 只计算几何，不为叠放效果重排子节点 | AC-1.2 |
| 布局属性分层 | Alignment 由 StackLayoutProperty 持有并由 Algorithm 消费 | AC-3.1~AC-3.6 |
| 子项优先级 | layoutGravity 只覆盖当前子项的容器 Alignment | AC-3.3 |
| RTL 局部镜像 | 只镜像水平 Start/End，不改变垂直轴和绘制顺序 | AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 正常布局对每个有效子项执行一次测量和一次偏移计算，复杂度 O(n) | Trace/基准 | `frameworks/core/components_ng/pattern/stack/stack_layout_algorithm.cpp:26-121` |
| 功耗 | 不新增定时器、后台线程或持续任务 | 代码审查 | VM-1~VM-4 |
| 内存 | 不复制子树；每个子项只写既有 GeometryNode | 内存检查 | VM-1, VM-2 |
| 安全 | 不处理敏感数据，不需要权限 | 代码审查 | SDK SysCap |
| 可靠性 | 空容器、GONE、非法 Alignment 和极端约束不得崩溃 | 边界 UT/fuzz | AC-1.3, AC-2.3~AC-3.6 |
| 可测试性 | 九宫格与 RTL 能以确定尺寸参数化验证 | 参数化 UT | VM-3, VM-4 |
| 自动化维测 | Inspector/布局树可观测容器尺寸和子项 offset | Inspector 测试 | GeometryNode |
| 定界定位 | 可按 Model、Property、Algorithm 三层区分创建、状态和计算问题 | 源码追溯 | `design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无专有差异 | 受窗口约束和 layoutDirection 影响 | 多尺寸/RTL UT | AC-2.1~AC-3.4 |
| 平板 | 无专有差异 | 大窗口只改变可用内容框，不改变公式 | 可变窗口测试 | AC-2.1~AC-2.3 |
| 折叠屏 | 可能出现安全区扩展子项 | 使用既有 safe-area 专用偏移路径 | 折叠态安全区测试 | AC-3.5 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 叠放不改变语义树/焦点树声明顺序；可见覆盖由应用负责 | AC-1.2 |
| 大字体 | 是 | 子项尺寸变化可扩大未显式轴的包裹尺寸 | AC-2.2 |
| 深色模式 | 否 | 本 Feat 不处理颜色 | N/A |
| 多窗口/分屏 | 是 | 约束变化后重新测量并对齐 | AC-2.1~AC-3.2 |
| 多用户 | 否 | 无用户级状态 | N/A |
| 版本升级 | 是 | API 7/18/23 表面差异需回归 | 兼容矩阵 |
| 生态兼容 | 是 | 默认 Center、child gravity 和 RTL 语义不得漂移 | AC-3.1~AC-3.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Stack 叠放布局、尺寸与对齐
  Scenario: 后声明子项覆盖但不改变几何规则
    Given 一个 100x100vp 的 Stack 且 alignContent 为 Center
    And 两个 20x20vp 的普通子项依次声明
    When 完成 Measure 和 Layout
    Then 两个子项偏移均为 40x40vp
    And 第二个子项保持后绘制覆盖第一个子项

  Scenario: 子项 gravity 覆盖容器对齐
    Given Stack alignContent 为 TopStart
    And 第二个子项 layoutGravity 为 BottomEnd
    When 完成 Layout
    Then 第一个子项位于 TopStart
    And 第二个子项位于 BottomEnd

  Scenario: RTL 镜像
    Given 布局方向为 RTL 且 alignContent 为 TopStart
    When 完成 Layout
    Then 水平位置按 TopEnd 镜像
    And 子节点声明顺序保持不变
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖 Stack 创建、测量、叠放和对齐
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则满足可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] syncLoad、多范式接口和 PointLight 已路由至 Feat-02/03

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "StackModelNG StackLayoutAlgorithm alignment layoutGravity RTL safe area"
  - repo: "openharmony/interface_sdk-js"
    query: "Stack StackOptions alignContent API 7 API 18 API 23"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/stack.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/component/stack.static.d.ets`
- 架构设计：`05-ui-components/01-layout-components/11-stack/design.md`
