# 特性规格

> Func-05-01-09-Feat-01 Row 创建、尺寸与子项间距：固化水平容器创建、内容自适应尺寸、显式 space、API 18 Resource 更新及非法输入。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Row 创建、尺寸与子项间距 |
| 特性编号 | Func-05-01-09-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

Row 创建 `LinearLayoutPattern(false)` 并固定 `FlexDirection::ROW`，通过继承 FlexLayoutAlgorithm 的 LinearLayoutAlgorithm 测量和定位。未显式宽高时，水平主轴按有效子项累计、垂直交叉轴取最大子项尺寸；space 只连接相邻有效子项。证据见 `frameworks/core/components_ng/pattern/linear_layout/row_model_ng.cpp:24-83,141-212`、`frameworks/core/components_ng/pattern/linear_layout/linear_layout_algorithm.h:27-36` 和 `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1163-1364`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Row 容器创建规格 | 覆盖 ROW FrameNode、Pattern、Property、Algorithm、默认方向和 Focus Scope |
| ADDED | 内容自适应尺寸规格 | 覆盖空容器、有效子项、padding/border、min/max 与 API 26 单轴 match-parent |
| ADDED | space/Resource 规格 | 覆盖默认值、单位、非法值、API 18 配置更新和生命周期 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/09-row/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/row.d.ts` | 已核对 |
| NG Model | `frameworks/core/components_ng/pattern/linear_layout/row_model_ng.cpp` | 已核对 |
| Shared layout algorithm | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp` | 已核对 |

> 对齐、RTL、reverse、多范式和 PointLight 分别由 Feat-02~04 承接。

## 用户故事

### US-1: 创建水平线性容器

**作为** ArkUI 应用开发者  
**我想要** 创建可包含多个子项的 Row  
**以便** 按声明顺序组织水平内容

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `Row()` THEN 创建 tag 为 ROW 的非原子 FrameNode，Pattern 为 horizontal `LinearLayoutPattern`，布局方向固定为 `FlexDirection::ROW` | 正常 |
| AC-1.2 | WHEN Pattern 创建布局对象 THEN 使用 LinearLayoutProperty 与 LinearLayoutAlgorithm；后者启用 linear feature 并复用 FlexLayoutAlgorithm | 正常 |
| AC-1.3 | WHEN 未提供 Row 专有属性 THEN space=0、主轴 Start、交叉轴 Center、reverse=false；本 Feat 验收 space 和容器身份，其余路由 Feat-02 | 边界 |
| AC-1.4 | WHEN Row 参与焦点遍历 THEN 作为水平 Flex 类型 Focus Scope，保持子项可遍历且不作为原子节点截断 | 正常 |

### US-2: 按内容和约束确定尺寸

**作为** UI 布局开发者  
**我想要** Row 在未显式设置宽高时按子项自适应  
**以便** 获得可预测的包裹内容尺寸

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Row 未得到显式主轴理想尺寸且包含有效子项 THEN 水平主轴累计子项宽度与有效间距，并在 infinite/auto/wrap/fix 场景收敛到累计值 | 正常 |
| AC-2.2 | WHEN Row 未得到显式交叉轴理想尺寸 THEN 垂直交叉轴以最大有效子项高度为基础，加上下 padding/border 后受 min/max 约束夹紧 | 正常 |
| AC-2.3 | WHEN Row 没有子项 THEN 采用 LayoutConstraint、calc constraint 和 measure type 解析出的理想尺寸并安全结束 | 边界 |
| AC-2.4 | WHEN 内容尺寸加 padding/border 超出约束区间 THEN 主轴与交叉轴分别夹紧到对应 min/max | 边界 |
| AC-2.5 | WHEN API 26+ Row 子项使用单轴 match-parent 策略 THEN 算法分类并重测对应子项后再确定 final size；低版本沿既有路径处理 | 边界 |

### US-3: 配置显式子项间距

**作为** ArkUI 应用开发者  
**我想要** 为相邻有效子项设置固定间距  
**以便** 无需逐项设置 margin

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN space 为非负 number 或可转换 string THEN number 按 vp、显式单位按 Dimension 规则转 px，在 n 个有效子项间累计 `space * max(n-1,0)` | 正常 |
| AC-3.2 | WHEN 子项为 GONE、离流或被 layout-policy 排除 THEN 不增加有效数量、已占用主轴尺寸或间距连接数 | 边界 |
| AC-3.3 | WHEN API 10+ Dynamic space 无法解析或为非法值 THEN 构造入口按 0 处理且不抛异常 | 异常 |
| AC-3.4 | WHEN direct RowModelNG 收到负 space THEN 记录错误且不覆盖既有 space 属性 | 异常 |
| AC-3.5 | WHEN space 内部为 PERCENT/CALC Dimension THEN 无百分比参照的 `ConvertToPx()` 路径不得表现为相对 Row 宽度间距 | 边界 |
| AC-3.6 | WHEN justifyContent 为 SpaceBetween/SpaceAround/SpaceEvenly THEN 显式 space 不生效，具体分布由 Feat-02 验收 | 边界 |

### US-4: 响应 Resource space 配置变化

**作为** 使用资源化尺寸的应用开发者  
**我想要** Row 在资源配置变化时更新间距  
**以便** 适配密度和资源限定符变化

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API 18+ `RowOptionsV2.space` 是可解析 Resource THEN 首次解析并以 `row.space` 为 key 注册弱引用资源更新器 | 正常 |
| AC-4.2 | WHEN 配置变化后 Resource 解析为非负值 THEN 更新 space 并标记 `PROPERTY_UPDATE_MEASURE` | 正常 |
| AC-4.3 | WHEN Resource 首次或更新解析为负值 THEN 按当前入口的忽略/reset 路径处理，不把负值作为正常间距 | 异常 |
| AC-4.4 | WHEN FrameNode 已销毁或 Pattern 不可用 THEN updater 弱引用升级失败后退出，不访问失效节点 | 异常 |
| AC-4.5 | WHEN 后续切换为普通数值或执行 reset THEN 移除 `row.space` ResourceObject，避免旧资源回调覆盖新值 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-3 | 已有实现 | NG 创建/焦点 UT | `frameworks/core/components_ng/pattern/linear_layout/row_model_ng.cpp:24-83,141-212`; `frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:34-69` |
| AC-2.1~AC-2.5 | R-4~R-7 | 已有实现 | Layout 约束矩阵 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:28-40,1163-1364` |
| AC-3.1~AC-3.6 | R-8~R-12 | 已有实现 | parser/Model/Layout UT | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:23-70`; FlexLayoutAlgorithm 间距路径 |
| AC-4.1~AC-4.5 | R-13~R-16 | 已有实现 | Resource 配置更新 UT | `frameworks/core/components_ng/pattern/linear_layout/row_model_ng.cpp:24-139`; `frameworks/core/interfaces/native/node/row_modifier.cpp:20-135` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Row 创建 | 创建 ROW FrameNode、`LinearLayoutPattern(false)`，固定 ROW direction | `frameworks/core/components_ng/pattern/linear_layout/row_model_ng.cpp:24-83,141-212` | AC-1.1 |
| R-2 | 行为 | Pattern 创建 Property/Algorithm | 返回 LinearLayoutProperty 与 LinearLayoutAlgorithm | `frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:34-55`; `frameworks/core/components_ng/pattern/linear_layout/linear_layout_algorithm.h:27-36` | AC-1.2 |
| R-3 | 行为 | 焦点遍历 | 返回水平 Flex ScopeFocusAlgorithm | `frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:57-69` | AC-1.3, AC-1.4 |
| R-4 | 行为 | 无显式水平主轴尺寸 | 最终主轴使用有效子项累计 allocatedSize | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1163-1227` | AC-2.1 |
| R-5 | 行为 | 测量有效子项 | 主轴累计宽度，交叉轴维护最大高度 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1287-1364` | AC-2.1, AC-2.2 |
| R-6 | 边界 | 空容器或尺寸越界 | 空容器直接写合法尺寸；最终尺寸 clamp 到 min/max | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1230-1285,1311-1313` | AC-2.3, AC-2.4 |
| R-7 | 边界 | API 26+ 单轴 match-parent 子项 | 分类重测后写最终尺寸 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:28-40,1351-1363` | AC-2.5 |
| R-8 | 行为 | n 个有效子项且非 Space* | 形成 n-1 个固定 space | FlexLayoutAlgorithm space 统计路径 | AC-3.1 |
| R-9 | 边界 | GONE/离流/被排除子项 | 跳过尺寸和间距连接统计 | FlexLayoutAlgorithm 子项遍历路径 | AC-3.2 |
| R-10 | 异常 | Dynamic 解析失败或 Model 负值 | API 10+ 回退 0；direct Model 不覆盖旧值 | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:23-70`; `frameworks/core/components_ng/pattern/linear_layout/row_model_ng.cpp:85-139` | AC-3.3, AC-3.4 |
| R-11 | 边界 | PERCENT/CALC | 无参换算不建立 Row 宽度参照 | 共享 Dimension/算法路径 | AC-3.5 |
| R-12 | 边界 | justify 为三种 Space* | 忽略显式 space，使用余量公式 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1628-1657` | AC-3.6 |
| R-13 | 行为 | Resource 首次设置 | 注册 `row.space` updater 并写合法值 | `frameworks/core/components_ng/pattern/linear_layout/row_model_ng.cpp:24-83` | AC-4.1 |
| R-14 | 行为 | Resource 配置更新合法 | 更新属性并显式标记 Measure | `frameworks/core/components_ng/pattern/linear_layout/row_model_ng.cpp:85-139` | AC-4.2 |
| R-15 | 异常 | Resource 解析为负值 | 按首次/更新路径忽略或 reset | 同上 | AC-4.3 |
| R-16 | 恢复 | 节点失效或切换普通值/reset | WeakPtr 失败退出，移除 keyed ResourceObject | `frameworks/core/components_ng/pattern/linear_layout/row_model_ng.cpp:24-139`; `frameworks/core/interfaces/native/node/row_modifier.cpp:20-135` | AC-4.4, AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-3, AC-1.1~AC-1.4 | NG UT | FrameNode、Pattern、Property、Algorithm、默认值和 Focus Scope |
| VM-2 | R-4~R-7, AC-2.1~AC-2.5 | Layout UT | 水平自适应、空容器、padding/border、min/max、API 26 |
| VM-3 | R-8~R-12, AC-3.1~AC-3.6 | parser/Model/Layout 参数矩阵 | 有效子项、0/负值、单位、Space* |
| VM-4 | R-13~R-16, AC-4.1~AC-4.5 | Resource UT | 初次解析、配置变化、负值、弱引用和移除 |

## API 变更分析

> 本文补录已有接口，不引入新 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `Row(options?: RowOptions)` | Public | `space?: string \| number` | RowAttribute | N/A | API 7 创建水平容器并设置间距 | AC-1.1~AC-3.6 |
| `Row(options?: RowOptions \| RowOptionsV2)` | Public | V2 space 增加 Resource | RowAttribute | N/A | API 18 支持资源化间距 | AC-4.1~AC-4.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| anonymous constructor options | API 18 命名规范化 | 类型名称从历史匿名对象明确为 RowOptions/V2 | 既有 API 7–17 调用保持可用 | AC-4.1 |

## 接口规格

### 接口定义

**Row(options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Row(options?: RowOptions \| RowOptionsV2): RowAttribute` |
| 返回值 | RowAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-4.5 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | RowOptions/RowOptionsV2 | 否 | 空 options | Dynamic 构造；Static 更新由 Feat-03 验收 |
| options.space | string/number/Resource | 否 | 0vp | 非负；Resource 仅 V2/API 18+ |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 无 options/合法固定值/非法值 | 使用默认、转换或回退路径 | AC-1.3, AC-3.1~AC-3.5 |
| 2 | Resource 首次设置/配置变化/reset | 注册、更新或移除 updater | AC-4.1~AC-4.5 |

## 兼容性声明

- **已有 API 行为变更:** 否；API 18 仅规范化命名并增加 V2 Resource 类型。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；space/updater 随节点生命周期存在。
- **最低支持版本:** API 7；Resource space 为 API 18。
- **API 版本号策略:** canonical SDK `@since` 为权威，API 10/26 算法分支按目标版本隔离。

| API/目标版本 | 既有行为 | 证据 | 关联 AC |
|--------------|----------|------|---------|
| API 7 | Row 与 number/string space | `interface/sdk-js/api/@internal/component/ets/row.d.ts:21-145` | AC-1.1, AC-3.1 |
| API 10 | cross-platform；Dynamic space 失败回退 0 | `frameworks/bridge/declarative_frontend/jsview/js_row.cpp:23-70` | AC-3.3 |
| API 18 | RowOptions/V2 正式命名，V2 支持 Resource | `interface/sdk-js/api/@internal/component/ets/row.d.ts:21-145` | AC-4.1 |
| API 26 | 单轴 match-parent 子项重测 | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:28-40,1351-1363` | AC-2.5 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 共享 Flex 算法 | Row 通过 LinearLayoutAlgorithm 复用 Flex 测量/定位 | AC-1.2, AC-2.1~AC-3.6 |
| 水平固定方向 | RowModelNG 固定 FlexDirection::ROW | AC-1.1, AC-2.1 |
| Measure 脏标记 | space/Resource 更新必须触发 Measure | AC-3.1, AC-4.2 |
| 弱引用资源 | updater 不拥有 FrameNode | AC-4.4~AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增指标；继续按有效子项线性测量 | Trace/benchmark | FlexLayoutAlgorithm |
| 功耗 | Resource updater 不建立轮询或后台任务 | 代码审查 | RowModelNG resource path |
| 内存 | 每节点最多一个 keyed `row.space` updater，回调持 WeakPtr | 生命周期 UT | AC-4.1~AC-4.5 |
| 安全 | 不涉及权限或敏感数据 | 代码审查 | VM-1~VM-4 |
| 可靠性 | 空容器、负值、资源失败和销毁回调不得崩溃 | 异常 UT/fuzz | AC-2.3, AC-3.3~AC-4.5 |
| 可测试性 | 属性、dirty flag、frame size 与 updater 均可观测 | 追溯审查 | VM-1~VM-4 |
| 自动化维测 | Pattern dump 输出 linear layout 关键空间状态 | Inspector/Dump | `frameworks/core/components_ng/pattern/linear_layout/linear_layout_pattern.h:94-120` |
| 定界定位 | 区分 parser、Model、Pattern、Property、Algorithm | 源码定位 | `05-ui-components/01-layout-components/09-row/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无 Row 专有差异 | density 和父约束影响 px 与自适应尺寸 | 多密度测试 | AC-2.1~AC-3.5 |
| 平板 | 无 Row 专有差异 | 大窗口仅改变可用约束 | 可变窗口测试 | AC-2.1~AC-2.4 |
| 折叠屏 | 资源/约束可随状态变化 | 配置更新和重测后使用新值 | 折叠态测试 | AC-4.2 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Row 是水平 Focus Scope，保持子项声明身份 | AC-1.4 |
| 大字体 | 是 | 子项增大改变自适应尺寸和总占用 | AC-2.1~AC-2.2 |
| 深色模式 | 否 | 不涉及颜色 | N/A |
| 多窗口/分屏 | 是 | 父约束变化触发重新测量 | AC-2.1~AC-2.5 |
| 多用户 | 否 | 无用户持久状态 | N/A |
| 版本升级 | 是 | API 7/10/18/26 需回归 | AC-2.5, AC-3.3, AC-4.1 |
| 生态兼容 | 是 | Resource 和非法值处理需保持当前路径 | AC-3.3~AC-4.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Row 创建、尺寸与子项间距
  Scenario: 按子项水平自适应
    Given 一个未显式设置宽高的 Row
    And 两个子项尺寸为 40x20vp 与 60x30vp
    And space 为 10vp
    When Measure 完成
    Then 内容主轴尺寸以 110vp 为基础
    And 内容交叉轴尺寸以 30vp 为基础

  Scenario: GONE 子项不形成额外间距
    Given 三个子项中间一个为 GONE
    And Row space 为 8vp
    When Measure 完成
    Then 只在两个有效子项之间累计一次 8vp

  Scenario: Resource 配置更新
    Given API 18 Row 使用 Resource space
    When 资源值由 8vp 变为 12vp
    Then row.space 更新为 12vp
    And 节点标记 PROPERTY_UPDATE_MEASURE
```

## Spec 自审清单

- [x] 无占位文本
- [x] 创建、水平自适应、固定 space、Resource 和非法输入均有 AC
- [x] 对齐/reverse、多范式、PointLight 已明确路由
- [x] 每个 AC 映射规则和 VM
- [x] 版本与 SDK 正式命名信息一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RowModelNG LinearLayoutPattern horizontal adaptive size space Resource updater"
  - repo: "openharmony/interface_sdk-js"
    query: "RowOptions RowOptionsV2 space Resource API 7 API 18"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/row.d.ts`
- 架构设计：`05-ui-components/01-layout-components/09-row/design.md`
