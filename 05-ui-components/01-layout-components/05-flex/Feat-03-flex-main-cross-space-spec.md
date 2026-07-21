# 特性规格

> Func-05-01-05-Feat-03 Flex 主轴与交叉轴间距：固化 API 12+ `space.main`/`space.cross` 的输入、有效子项/行计算、对齐组合和非法值边界。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Flex 主轴与交叉轴间距 |
| 特性编号 | Func-05-01-05-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 12–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

FlexSpaceOptions 自 API 12 提供 `main` 与 `cross` 两个 Length。main space 用于单行或每一行相邻有效子项；cross space 用于相邻有效行。FlexModelNG 只接受非负 Dimension，布局算法把间距转换为 px 并与主轴/多行空间分布组合。证据见 `interface/sdk-js/api/@internal/component/ets/flex.d.ts:97-147`、`frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp:287-336`、`frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1628-1657` 和 `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:464-536`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | main space 规格 | 覆盖 NoWrap/每行有效子项、单子项与 Space* 组合 |
| ADDED | cross space 规格 | 覆盖多行、单行、WrapReverse 与 alignContent 组合 |
| ADDED | 输入与通道边界规格 | 覆盖单位、负值、percentage/CALC、Dynamic/Static/Native |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/05-flex/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/flex.d.ts` | 已核对 |
| NG Model | `frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp` | 已核对 |
| Flex/Wrap algorithms | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp`; `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp` | 已核对 |

## 用户故事

### US-1: 设置主轴固定间距

**作为** ArkUI 应用开发者  
**我想要** 为相邻子项设置统一主轴间距  
**以便** 避免逐项配置 margin

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN API 12+ Flex 接收非负 `space.main` THEN 转换为 px，并在每个 NoWrap 行或 Wrap 行的相邻有效子项之间形成固定基础间距 | 正常 |
| AC-1.2 | WHEN 一行有 n 个有效子项且 justifyContent 为 Start/Center/End THEN 该行固定 main space 总占用为 `main * max(n-1, 0)` | 正常 |
| AC-1.3 | WHEN justifyContent 为 SpaceBetween/SpaceAround/SpaceEvenly THEN 主轴最终间距由剩余空间公式决定，显式 main space 不重复叠加 | 边界 |
| AC-1.4 | WHEN 子项为 GONE、离流或被布局策略排除 THEN 不贡献 main space 的有效连接数 | 边界 |

### US-2: 设置多行交叉轴间距

**作为** 响应式界面开发者  
**我想要** 为相邻 Flex 行设置统一间距  
**以便** 控制多行内容密度

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Wrap Flex 形成 m 个有效行且 m>1 THEN cross space 在相邻行之间形成 `cross * (m-1)` 的基础交叉轴占用 | 正常 |
| AC-2.2 | WHEN 只形成 0 或 1 行 THEN cross space 不产生可见间距或额外行连接 | 边界 |
| AC-2.3 | WHEN alignContent 分配交叉轴剩余空间 THEN cross space 先作为行集合基础占用，剩余空间再依当前 alignContent 公式分配 | 正常 |
| AC-2.4 | WHEN wrap=WrapReverse THEN cross space 数值不变，只随行集合反向出现在相邻行之间 | 正常 |

### US-3: 处理单位、非法值和版本边界

**作为** 跨范式开发者  
**我想要** 间距输入在各公开通道中有可追溯边界  
**以便** 避免非法输入导致崩溃

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN main/cross 是合法 number 或支持的 Length 字符串 THEN number 按 vp、显式单位按 Dimension 规则转为 px | 正常 |
| AC-3.2 | WHEN direct FlexModelNG 收到负 main/cross space THEN 记录错误且不覆盖对应既有属性 | 异常 |
| AC-3.3 | WHEN SDK 输入使用百分比 THEN 按公开契约视为不支持；内部 PERCENT/CALC 在无参 `ConvertToPx()` 路径不得被解释为相对 Flex 尺寸 | 边界 |
| AC-3.4 | WHEN 目标 API 低于 12 THEN `FlexSpaceOptions` 不属于公开契约，应用不得依赖该字段 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | NoWrap/Wrap 行内 Layout UT | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1628-1657`; `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:571-718` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | Wrap 行集合参数矩阵 | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:464-536` |
| AC-3.1~AC-3.4 | R-9~R-12 | 已有实现 | parser/Model/API level UT | `interface/sdk-js/api/@internal/component/ets/flex.d.ts:97-147`; `frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp:287-336` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 合法 main space | 写入 FlexLayoutProperty 并触发 Measure | `frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp:287-336` | AC-1.1 |
| R-2 | 行为 | Start/Center/End 且 n 个有效子项 | 形成 n-1 个固定 main gap | `frameworks/core/components_ng/pattern/flex/flex_layout_algorithm.cpp:1628-1657` | AC-1.2 |
| R-3 | 边界 | 主轴 Space* 模式 | 使用剩余空间公式，不叠加 main | 同上 | AC-1.3 |
| R-4 | 边界 | 无效子项 | 不计入 main gap 连接数 | Flex/Wrap 子项遍历路径 | AC-1.4 |
| R-5 | 行为 | 合法 cross space 且 m>1 | 在相邻行之间形成 m-1 个基础 gap | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:464-536` | AC-2.1 |
| R-6 | 边界 | m<=1 | cross 不产生额外可见占用 | 同上 | AC-2.2 |
| R-7 | 行为 | cross 与 alignContent 同时存在 | 先扣基础 cross 占用，再分配剩余空间 | 同上 | AC-2.3 |
| R-8 | 行为 | WrapReverse | 反转行推进方向，不改变 gap 大小 | `frameworks/core/components_ng/pattern/flex/wrap_layout_algorithm.cpp:571-718` | AC-2.4 |
| R-9 | 行为 | number/支持 Length | 按 vp/Dimension 规则转换 | Dynamic/Static converter 路径 | AC-3.1 |
| R-10 | 异常 | Model 收到负值 | 不覆盖对应属性并记录错误 | `frameworks/core/components_ng/pattern/flex/flex_model_ng.cpp:287-336` | AC-3.2 |
| R-11 | 边界 | percentage/CALC | SDK 不支持 percentage；无参换算不建立容器参照 | `interface/sdk-js/api/@internal/component/ets/flex.d.ts:97-147` | AC-3.3 |
| R-12 | 边界 | API<12 | 不公开 FlexSpaceOptions | 同上 | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | Layout UT | n=0/1/多子项、无效子项、三类 Space* |
| VM-2 | R-5~R-8, AC-2.1~AC-2.4 | Wrap Layout UT | m=0/1/多行、alignContent、WrapReverse |
| VM-3 | R-9~R-12, AC-3.1~AC-3.4 | parser/Model/SDK 编译测试 | 单位、负值、percentage/CALC、API 12 可见性 |

## API 变更分析

> 本文补录 API 12 已有接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `FlexOptions.space` | Public | `{ main?: Length; cross?: Length }` | 构造 options 字段 | N/A | 配置主轴与交叉轴固定间距 | AC-1.1~AC-3.4 |
| `NODE_FLEX_SPACE` | Public C API | 两个 Dimension 值及单位 | `ArkUI_AttributeItem` | NO_ERROR/PARAM_INVALID | Native set/reset/get 双轴间距 | AC-1.1, AC-2.1, AC-3.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 存量间距能力补录 | API 12 以下不使用 space 字段 | AC-3.4 |

## 接口规格

### 接口定义

**FlexSpaceOptions**

| 属性 | 值 |
|------|-----|
| 类型签名 | `{ main?: Length; cross?: Length }` |
| 使用位置 | `FlexOptions.space` |
| 开放范围 | Public，API 12+ |
| 错误码 | ArkTS N/A；Native 由属性接口返回 |
| 关联 AC | AC-1.1~AC-3.4 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| main | Length | 否 | 0vp | 非负；percentage 不支持 |
| cross | Length | 否 | 0vp | 非负；仅多行形成可见行距 |

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | NoWrap/Wrap 行内 + main | 形成有效子项间基础 gap | AC-1.1~AC-1.4 |
| 2 | 多行 + cross + alignContent | 先计基础行距，再分配余量 | AC-2.1~AC-2.4 |
| 3 | 负值/percentage/API<12 | 不覆盖、不可依赖或按不支持处理 | AC-3.2~AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** `space` 为 API 12；Flex 基础能力为 API 7。
- **API 版本号策略:** canonical SDK `@since 12` 为公开边界。

| 风险 | 当前证据 | 兼容处理 |
|------|----------|----------|
| Dynamic ArkTS Bridge 的 main 解析位置读取 `crossArg` | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_flex_bridge.cpp:53-67` | 仅作为实现风险记录；用 main≠cross 用例定界，不把偏差写成公开契约 |
| options reset 与独立 space reset 不完全绑定 | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_flex_bridge.cpp:72-79`; `frameworks/core/interfaces/native/node/flex_modifier.cpp:113-160` | 生命周期行为由 Feat-04 记录，本 Feat 不推导新的 reset 语义 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 属性共享 | main/cross 存于 FlexLayoutProperty，由单行/Wrap 算法分别消费 | AC-1.1, AC-2.1 |
| Measure 脏标记 | 间距变化影响换行和尺寸，必须触发 Measure | AC-1.1~AC-2.3 |
| 行内/行间分离 | main 连接子项，cross 连接行 | AC-1.1~AC-2.4 |
| 公共契约优先 | 实现偏差只列风险，不覆盖 SDK 非负/非百分比契约 | AC-3.2~AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增复杂度；gap 计算随子项/行线性完成 | Layout trace | VM-1~VM-2 |
| 功耗 | 不新增任务或帧循环 | 代码审查 | VM-1~VM-3 |
| 内存 | 仅增加两个 LayoutProperty Dimension 状态 | 内存审查 | `frameworks/core/components_ng/pattern/flex/flex_layout_property.h:56-75` |
| 安全 | 不涉及权限或敏感数据 | 代码审查 | VM-1~VM-3 |
| 可靠性 | 负值、0/1 子项、0/1 行和无效单位不得崩溃 | 边界 UT/fuzz | AC-1.2~AC-3.3 |
| 可测试性 | main/cross 使用非对称值，尺寸与 offset 可直接断言 | 参数矩阵 | VM-1~VM-3 |
| 自动化维测 | 沿用属性 dump，无新协议 | Inspector/Dump | FlexLayoutProperty |
| 定界定位 | 区分 parser、Model、单行算法、Wrap 算法 | 源码定位 | `05-ui-components/01-layout-components/05-flex/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无专有差异 | vp/fp 等单位按设备上下文转 px | 多密度测试 | AC-3.1 |
| 平板 | 可能减少行数 | cross 只连接实际形成的行 | 可变窗口测试 | AC-2.1~AC-2.2 |
| 折叠屏 | 行数随约束变化 | 重新 Measure 后重算 main/cross 连接数 | 折叠态测试 | AC-1.2, AC-2.1 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 间距只改变几何位置，不改变语义树 | N/A |
| 大字体 | 是 | 子项增大可能改变行数和 cross 连接数 | AC-2.1~AC-2.2 |
| 深色模式 | 否 | 不涉及颜色 | N/A |
| 多窗口/分屏 | 是 | 约束变化会改变换行与间距总占用 | AC-1.2, AC-2.1 |
| 多用户 | 否 | 无持久用户状态 | N/A |
| 版本升级 | 是 | API 12 可见性和通道偏差需回归 | AC-3.4 |
| 生态兼容 | 是 | main/cross 非对称值用于防止通道映射漂移 | AC-1.1, AC-2.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Flex 主轴与交叉轴间距
  Scenario: 多行使用非对称间距
    Given Flex space.main 为 8vp 且 space.cross 为 20vp
    And Wrap 布局形成两行且每行两个有效子项
    When Layout 完成
    Then 每行内部形成一个 8vp 基础间距
    And 两行之间形成一个 20vp 基础间距

  Scenario: SpaceBetween 不叠加 main
    Given 一行有三个子项并设置 main 为 10vp
    When justifyContent 为 SpaceBetween
    Then 最终相邻间距仅按剩余空间公式计算
```

## Spec 自审清单

- [x] 无占位文本
- [x] main/cross、单行/多行、0/1 边界和非法输入均有 AC
- [x] 实现偏差仅在兼容风险表中记录
- [x] 每个 AC 映射到规则和 VM
- [x] API 12 以下明确为不公开能力

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Flex main space cross space FlexModelNG WrapLayoutAlgorithm"
  - repo: "openharmony/interface_sdk-js"
    query: "FlexSpaceOptions main cross API 12 percentage unsupported"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/flex.d.ts`
- 架构设计：`05-ui-components/01-layout-components/05-flex/design.md`
