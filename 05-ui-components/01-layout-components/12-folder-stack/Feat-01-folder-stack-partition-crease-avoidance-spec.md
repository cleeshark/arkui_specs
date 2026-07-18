# 特性规格

> Func-05-01-12-Feat-01 FolderStack 创建、分区与折痕避让：补录内部上下 Stack 结构、悬停启用条件、`upperItems` 分区、折痕/安全区计算和普通 Stack 降级行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FolderStack 创建、分区与折痕避让 |
| 特性编号 | Func-05-01-12-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 11–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

FolderStack 在普通状态下按 Stack 叠放子项；在受支持双折设备、HALF_FOLD、支持方向且组件占据全窗口时，根据 crease rect 将内容分为上/下区域。构造参数 `upperItems` 用 inspector ID 指定进入上区的子组件，其余进入下区。内部结构和分区分别由 `frameworks/core/components_ng/pattern/folder_stack/folder_stack_model_ng.cpp:23-52` 与 `frameworks/core/components_ng/pattern/folder_stack/folder_stack_layout_algorithm.cpp:184-340` 实现。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | FolderStack 创建和内部节点规格 | 覆盖 GroupNode、HoverStackNode、ControlPartsStackNode |
| ADDED | 悬停启用/降级规格 | 覆盖半折、全窗口、产品、方向、父节点和 crease 条件 |
| ADDED | upperItems 分区与折痕避让规格 | 覆盖 ID 匹配、上下区域、对齐、RTL 和安全区 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/12-folder-stack/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts` | 已核对 |
| FolderStack Model | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_model_ng.cpp` | 已核对 |
| Layout Algorithm | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_layout_algorithm.cpp` | 已核对 |

> registry 中正式组件名为 FolderStack。本文档补录已有能力，不把用户早期称呼 FoldStack 扩展为另一组件。

## 用户故事

### US-1: 创建可悬停分区的叠放容器

**作为** 折叠屏应用开发者  
**我想要** 使用一个组件声明上下区域内容  
**以便** 界面可在普通窗口和半折悬停之间自动切换

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `FolderStack(options?)` THEN 创建 FolderStackGroupNode，并建立用于上区和下区控制的内部 Stack 节点，外部仍表现为可包含多个子组件的单一容器 | 正常 |
| AC-1.2 | WHEN 未设置 FolderStack 专有属性 THEN `alignContent=Center`、`enableAnimation=true`、`autoHalfFold=true`，`upperItems` 为空 | 边界 |
| AC-1.3 | WHEN 当前环境不进入悬停模式 THEN FolderStack 按普通 Stack 测量和叠放所有子项，不人为形成上下折痕间隔 | 正常 |
| AC-1.4 | WHEN FolderStack 节点或必要 Pipeline/DisplayInfo 不可用 THEN 创建或布局路径安全退出/降级，不访问空上下文 | 异常 |

### US-2: 判定是否进入半折悬停布局

**作为** 折叠屏窗口开发者  
**我想要** 仅在设备和窗口条件都满足时启用悬停  
**以便** 普通设备、非全屏窗口和不支持方向不会被错误切分

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设备为实现支持的双折/悬停产品、foldStatus 为 HALF_FOLD、方向受支持且 FolderStack 占据全窗口 THEN 允许进入悬停分区判定 | 正常 |
| AC-2.2 | WHEN foldStatus 不是 HALF_FOLD、产品/方向不支持或组件不满足全窗口条件中的任意一项 THEN 不进入悬停，使用普通 Stack 布局 | 边界 |
| AC-2.3 | WHEN FolderStack 的直接父节点是 SDK 所述 if/else 条件渲染节点 THEN 悬停能力禁用，组件继续按非悬停布局工作 | 边界 |
| AC-2.4 | WHEN crease rect 为空、越界或不能形成有效上下区域 THEN 不使用该折痕切分内容，安全回退非悬停布局 | 异常 |
| AC-2.5 | WHEN 全窗口判定包含 safe-area/fullscreen 状态 THEN 以当前 Pipeline 窗口与安全区信息为准，不只比较组件裸宽高 | 边界 |

### US-3: 将子项分配到折痕上下区域

**作为** 应用界面开发者  
**我想要** 通过 `upperItems` 指定需要位于折痕上方的子组件  
**以便** 控件和内容在悬停形态下避开折痕

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 进入悬停且子项 inspector ID 出现在 `upperItems` THEN 将该子项归入 HoverStackNode 上区；未命中项归入 ControlPartsStackNode 下区 | 正常 |
| AC-3.2 | WHEN `upperItems` 为空或某 ID 不存在 THEN 不存在的 ID 被忽略，实际子项保持可布局且默认进入下区，不抛异常 | 边界 |
| AC-3.3 | WHEN 同一 ID 重复出现 THEN 子项只具有一个实际父归属，不重复创建或重复布局 | 边界 |
| AC-3.4 | WHEN 从普通状态切入或退出悬停 THEN 复用原有子节点并调整内部父归属，应用子组件状态和声明身份保持 | 正常 |
| AC-3.5 | WHEN 计算上下区域 THEN 上区终止于 crease 上边界、下区起始于 crease 下边界，并结合 safe-area/容器 padding 得到可用内容框 | 正常 |
| AC-3.6 | WHEN 设置 `alignContent` 或 RTL 方向 THEN 上下内部 Stack 按继承的 Stack 对齐语义定位子项，ID 分区结果不因 RTL 改变 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Model/空环境 UT | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_model_ng.cpp:23-52`; `frameworks/core/components_ng/pattern/folder_stack/folder_stack_layout_property.h:24-78` |
| AC-2.1~AC-2.5 | R-5~R-9 | 已有实现 | 设备/窗口/方向矩阵 UT | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_layout_algorithm.cpp:211-270,311-340`; `test/unittest/core/pattern/folder_stack/folder_stack_test_ng.cpp:711-760` |
| AC-3.1~AC-3.6 | R-10~R-15 | 已有实现 | upperItems/crease/RTL Layout UT | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_layout_algorithm.cpp:56-143,184-209,273-300`; `test/unittest/core/pattern/folder_stack/folder_stack_test_ng.cpp:941-983` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | FolderStack 创建 | 创建 GroupNode 和上/下内部 Stack | 对外仍是一个容器 | AC-1.1 |
| R-2 | 边界 | 专有属性缺省 | Center、animation=true、autoHalfFold=true、upperItems 空 | 默认值由 Property/SDK 共同确认 | AC-1.2 |
| R-3 | 行为 | 未进入悬停 | 调用普通 Stack 路径测量/布局 | 不保留可见折痕间隔 | AC-1.3 |
| R-4 | 异常 | 节点/Pipeline/DisplayInfo 为空 | 安全退出或降级普通布局 | 不解引用空对象 | AC-1.4 |
| R-5 | 行为 | 全部悬停前提成立 | 允许进入上下分区 | HALF_FOLD + 全窗口 + 支持产品/方向 | AC-2.1 |
| R-6 | 边界 | 任一悬停前提不成立 | 使用普通 Stack | 条件为逻辑与 | AC-2.2 |
| R-7 | 边界 | 直接父为 if/else 条件节点 | 禁用 hover | 以 canonical SDK 说明为黑盒契约 | AC-2.3 |
| R-8 | 异常 | crease rect 无效 | 不切分，回退普通 Stack | 避免负区域/越界 | AC-2.4 |
| R-9 | 边界 | 判定全窗口 | 同时考虑窗口、safe-area 与 fullscreen | 不以单一宽高近似 | AC-2.5 |
| R-10 | 行为 | ID 命中 upperItems | 子项归入上区；其他归入下区 | inspector ID 字符串匹配 | AC-3.1 |
| R-11 | 边界 | 空/不存在/重复 ID | 忽略无效映射且每个子项只布局一次 | 不创建占位子节点 | AC-3.2, AC-3.3 |
| R-12 | 恢复 | hover 状态转换 | 调整现有节点内部归属并保持应用状态 | 不重建应用子组件 | AC-3.4 |
| R-13 | 行为 | crease 有效 | 上下内容框避开 crease 并结合 safe-area | 区域不得相交 | AC-3.5 |
| R-14 | 行为 | 容器 Alignment 设置 | 内部 Stack 使用一致对齐 | 子项属性仍可按 Stack 规则覆盖 | AC-3.6 |
| R-15 | 边界 | RTL 生效 | 镜像内部水平对齐，不改变 upperItems 匹配 | 分区依据 ID 而非方向 | AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | NG Model/Property UT | 内部节点、默认值、普通 Stack 降级和空环境 |
| VM-2 | R-5~R-9, AC-2.1~AC-2.5 | 平台状态组合矩阵 | fold/product/orientation/window/if-else/crease |
| VM-3 | R-10~R-12, AC-3.1~AC-3.4 | upperItems 参数化 UT | 命中、不存在、重复、状态切换与身份保持 |
| VM-4 | R-13~R-15, AC-3.5~AC-3.6 | Layout/RTL/safe-area UT | 上下边界、折痕不相交和对齐继承 |

## API 变更分析

> 本文档补录现有 API，不引入新的设备或窗口接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `FolderStack(options?: FolderStackOptions)` | Public Dynamic | `upperItems?: string[]` | `FolderStackAttribute` | N/A | API 11 创建容器；API 18 规范化 options | AC-1.1~AC-3.4 |
| `alignContent(value: Alignment)` | Public Dynamic | Alignment | `FolderStackAttribute` | N/A | 设置上下内部 Stack 对齐 | AC-1.2, AC-3.6 |
| Static `FolderStack(options?, content_?)` | Public Static | options + content builder | `FolderStackAttribute` | N/A | API 23 Static 构造 | AC-1.1~AC-3.6 |
| `setFolderStackOptions(options?)` | Public Static | FolderStackOptions | `this` | N/A | API 26 Static 更新 upperItems | AC-3.1~AC-3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次仅补录已有创建与分区行为 | 无需迁移 | AC-1.1~AC-3.6 |

## 接口规格

### 接口定义

**FolderStack(options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FolderStack(options?: FolderStackOptions): FolderStackAttribute` |
| 返回值 | `FolderStackAttribute` |
| 开放范围 | Public、Stage 模型；Dynamic API 11，Static API 23 |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | FolderStackOptions | 否 | 空 options | API 18 规范化命名类型 |
| options.upperItems | Array<string> | 否 | 空数组 | 字符串应对应子组件 inspector ID；无匹配安全忽略 |
| alignContent | Alignment | 否 | Alignment.Center | 非法值按默认值处理 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 普通设备/非半折/非全窗口 | 退化为普通 Stack | AC-1.3, AC-2.2 |
| 2 | 悬停前提全部成立 | 计算 crease 并建立上下区 | AC-2.1, AC-3.5 |
| 3 | upperItems 命中/未命中 | 分别进入上/下内部 Stack | AC-3.1~AC-3.3 |
| 4 | 状态切换 | 迁移现有子项并保持状态 | AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；保留 API 11 历史匿名对象、API 18 规范类型和 API 23/26 Static 表面。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；upperItems 和运行态不持久化。
- **最低支持版本:** Dynamic API 11；Static API 23。
- **API 版本号策略:** canonical SDK 为准；双折/方向支持属于运行时能力条件。

| 版本/能力 | 行为 | 证据 |
|-----------|------|------|
| API 11 | Dynamic FolderStack 构造和对齐 | `interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts:60-83,148-163` |
| API 18 | `FolderStackOptions.upperItems` 命名接口 | `interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts:31-58` |
| API 23 | Static FolderStack | `interface/sdk-js/api/arkui/component/folderStack.static.d.ets:227-242` |
| API 26 | `setFolderStackOptions` | `interface/sdk-js/api/arkui/component/folderStack.static.d.ets:158-167` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 平台状态只读 | FolderStack 消费 fold/crease/window，不改变设备折叠状态 | AC-2.1~AC-2.5 |
| 内部节点封装 | 上/下 Stack 属于实现结构，不暴露为应用子组件 API | AC-1.1, AC-3.4 |
| 普通 Stack 降级 | 前提失败时必须保留基本布局能力 | AC-1.3, AC-2.2~AC-2.4 |
| ID 稳定映射 | upperItems 只按 inspector ID 分区，不按索引或 RTL | AC-3.1~AC-3.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 每次状态布局对 n 个子项执行一次 ID 分类，复杂度 O(n) | Trace/大子树测试 | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_layout_algorithm.cpp:273-300` |
| 功耗 | 普通状态不建立持续布局循环；只在平台状态变化时重测 | 帧计数 | Pattern 监听 |
| 内存 | 复用子节点；内部 Group/Stack 随 FolderStack 生命周期 | 生命周期 UT | `frameworks/core/components_ng/pattern/folder_stack/folder_stack_model_ng.cpp:23-52` |
| 安全 | 不新增权限，不暴露设备敏感数据 | 代码审查 | SDK SysCap |
| 可靠性 | 无效 crease/ID/上下文和不支持设备不得崩溃 | fuzz/故障注入 | AC-1.4, AC-2.4, AC-3.2 |
| 可测试性 | 平台状态、窗口和 crease 可 mock | NG/Layout UT | VM-2~VM-4 |
| 自动化维测 | 可 dump hover 判定、fold status、区域和子项归属 | Inspector/trace | Layout/Pattern |
| 定界定位 | 区分平台条件、全窗口判定、ID 分类和 Stack 对齐 | 源码追溯 | `design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 非受支持折叠产品退化普通 Stack | 不形成上下分区 | 直板机测试 | AC-1.3, AC-2.2 |
| 平板 | 默认退化普通 Stack | 大窗口不等同受支持悬停产品 | 多窗口测试 | AC-2.1, AC-2.2 |
| 折叠屏 | 仅受支持双折/半折/方向/全窗口启用 | crease 与 safe-area 决定分区 | 设备姿态矩阵 | AC-2.1~AC-3.6 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 子组件身份/语义状态保持；内部迁移不应重复语义节点 | AC-3.4 |
| 大字体 | 是 | 子项尺寸变化在对应上/下内容框内重新测量 | AC-3.5 |
| 深色模式 | 否 | 本 Feat 不处理颜色 | N/A |
| 多窗口/分屏 | 是 | 非全窗口时按普通 Stack，窗口变化重新判定 | AC-2.2, AC-2.5 |
| 多用户 | 否 | 无用户级状态 | N/A |
| 版本升级 | 是 | API 11/18/23/26 和设备能力矩阵需回归 | 兼容矩阵 |
| 生态兼容 | 是 | if/else 禁用、无效 ID 忽略和普通降级必须保持 | AC-2.3, AC-3.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: FolderStack 分区与折痕避让
  Scenario: 半折全窗口进入上下分区
    Given 受支持折叠设备处于 HALF_FOLD
    And FolderStack 占据全窗口且 crease rect 有效
    And upperItems 包含标题组件 ID
    When 完成 Measure 和 Layout
    Then 标题位于 crease 上方内容区
    And 其他组件位于 crease 下方内容区
    And 两个内容区不与 crease 相交

  Scenario: 非全窗口降级
    Given 设备处于 HALF_FOLD
    But FolderStack 位于分屏窗口
    When 完成布局
    Then 所有子项按普通 Stack 叠放

  Scenario: 不存在的 upperItems ID
    Given upperItems 包含不存在的 ID
    When 进入悬停布局
    Then 该 ID 被忽略
    And 实际子项仍各布局一次
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖创建、悬停判定、分区和折痕避让
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则满足可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] 事件、动画和旋转已路由至 Feat-02/03；NDK 已排除

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FolderStackGroupNode upperItems crease IsFullWindow IsIntoFolderStack HALF_FOLD"
  - repo: "openharmony/interface_sdk-js"
    query: "FolderStack FolderStackOptions upperItems hover dual-fold if else"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/folder_stack.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/component/folderStack.static.d.ets`
- 架构设计：`05-ui-components/01-layout-components/12-folder-stack/design.md`
