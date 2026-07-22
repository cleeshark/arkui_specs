# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 路径动画 (Motion Path) 全量规格 |
| 特性编号 | Func-03-02-08-Feat-01 |
| FuncID | 03-02-08 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 7 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 7 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | motionPath(value: MotionPathOptions) 属性方法 | @since 7，common.d.ts:23727 |
| ADDED | MotionPathOptions 接口（path/from/to/rotatable） | @since 7，common.d.ts:4553 |
| ADDED | MotionPathOption C++ 结构体（path/begin/end/rotate） | `motion_path_option.h:24` |
| ADDED | MotionPathEvaluator 求值器 + 5 种子 Evaluator | `motion_path_evaluator.h:39` |
| MODIFIED | MotionPathOptions 跨平台支持 | @since 10，@crossplatform |
| MODIFIED | MotionPathOptions 原子化服务支持 | @since 11，@atomicservice |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/02-animation-capability/08-motion-path/design.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基础路径动画

**角色**: 应用开发者
**期望**: 我想要让组件沿 SVG 路径移动
**价值**: 以便实现弧线、波浪等非直线动画效果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 设置 `motionPath({ path: "Mstart.x start.y L100 100 Lend.x end.y" })` THEN 组件沿 SVG 路径移动，start/end 占位符替换为实际坐标（`motion_path_evaluator.cpp:40-47`） | 正常 |
| AC-1.2 | WHEN path 中包含 `start.x`/`start.y`/`end.x`/`end.y` 占位符 THEN Preprocess 将其替换为 start/end Offset 的实际坐标值（`motion_path_evaluator.cpp:42-45`） | 正常 |
| AC-1.3 | WHEN path 为空字符串 THEN IsValid() 返回 false，不设置路径动画（`motion_path_option.h:70-73`） | 边界 |
| AC-1.4 | WHEN motionPath 未设置 THEN 组件使用默认属性动画，不走路径 | 正常 |

### US-2: begin/end 范围映射

**角色**: 应用开发者
**期望**: 我想要控制动画在路径上的子区间执行
**价值**: 以便实现部分路径动画

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 设置 `from: 0.0, to: 1.0`（默认）THEN Evaluate 计算 `progress = begin*(1-fraction) + end*fraction`，覆盖完整路径（`motion_path_evaluator.cpp:67`） | 正常 |
| AC-2.2 | WHEN 设置 `from: 0.0, to: 0.5` THEN progress 从 0.0 到 0.5，动画仅覆盖路径前半段 | 正常 |
| AC-2.3 | WHEN 设置 `from: 0.3, to: 0.7` THEN progress 从 0.3 到 0.7，动画覆盖路径中段 | 正常 |
| AC-2.4 | WHEN from < 0.0 或 > 1.0 THEN 归一化为默认值 0.0（`common.d.ts:4577`） | 边界 |
| AC-2.5 | WHEN to < 0.0 或 > 1.0 THEN 归一化为默认值 1.0，归一化后 to 必须 >= from（`common.d.ts:4594-4595`） | 边界 |

### US-3: 无效路径降级

**角色**: 框架开发者
**期望**: 我想要了解路径无效时的降级行为
**价值**: 以便确保动画不中断

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN IsValid() 返回 false（path 为空）THEN Evaluate 返回 `startPoint_ * (1-fraction) + endPoint_ * fraction` 线性插值（`motion_path_evaluator.cpp:64-65`） | 异常 |
| AC-3.2 | WHEN RosenSvgPainter::GetMotionPathPosition 返回 false（SVG 解析失败）THEN Evaluate 返回 `MotionPathPosition { offset: Offset(), rotate: 0.0f }` 零偏移（`motion_path_evaluator.cpp:76`） | 异常 |
| AC-3.3 | WHEN fraction = 1.0 THEN NearEqual 判定为 true，fraction 固定为 1.0（`motion_path_evaluator.cpp:61-63`） | 边界 |

### US-4: rotate 旋转

**角色**: 应用开发者
**期望**: 我想要组件在路径动画中沿路径切线方向旋转
**价值**: 以便实现更自然的运动方向效果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 `rotatable: true` THEN GetMotionPathPosition 返回的 rotate 为路径切线角度，RotateEvaluator 返回该角度（`motion_path_evaluator.cpp:105-112`） | 正常 |
| AC-4.2 | WHEN 设置 `rotatable: false`（默认）THEN 不创建 rotate 动画，组件仅沿路径平移不旋转 | 正常 |
| AC-4.3 | WHEN rotatable=true 且 SharedTransition Exchange 复用 MotionPath THEN SharedTransitionExchange 额外创建 CurveAnimation<float>，listener 调用 UpdateTransformRotate（`shared_transition_effect.cpp:139-152`） | 正常 |

### US-5: 多维度 Evaluator 适配

**角色**: 框架开发者
**期望**: 我想要了解 MotionPathEvaluator 如何适配不同动画维度
**价值**: 以便理解 translate/position/rotate/transform 的路径动画集成方式

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 属性动画运行在 translate(x/y) THEN 使用 CreateXEvaluator/CreateYEvaluator，返回 position.offset.GetX()/GetY()（`motion_path_evaluator.h:50-58, cpp:79-91`） | 正常 |
| AC-5.2 | WHEN 属性动画运行在 position/offset THEN 使用 CreateDimensionOffsetEvaluator，返回 DimensionOffset(x, y)（`motion_path_evaluator.h:60-63, cpp:93-103`） | 正常 |
| AC-5.3 | WHEN 属性动画运行在 rotate THEN 使用 CreateRotateEvaluator，返回 position.rotate（`motion_path_evaluator.h:65-68, cpp:105-112`） | 正常 |
| AC-5.4 | WHEN 属性动画运行在 transform THEN 使用 CreateTransformOperationsEvaluator，返回 ROTATE 类型 TransformOperation（`motion_path_evaluator.h:70-73, cpp:114-126`） | 正常 |
| AC-5.5 | WHEN positionType_ == PositionType::PTOFFSET THEN position.offset += startPoint_（`motion_path_evaluator.cpp:71-72`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2 | TASK-MOTION-PATH-01 | UT | MotionPathOption 单测 |
| AC-2.1 ~ AC-2.5 | R-3, R-4 | TASK-MOTION-PATH-01 | UT | begin/end 范围测试 |
| AC-3.1 ~ AC-3.3 | R-5, R-6 | TASK-MOTION-PATH-01 | UT | 降级测试 |
| AC-4.1 ~ AC-4.3 | R-7, R-8 | TASK-MOTION-PATH-01 | UT + 手工 | rotate 测试 |
| AC-5.1 ~ AC-5.5 | R-9, R-10 | TASK-MOTION-PATH-01 | UT | 子 Evaluator 测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | motionPath 设置有效 SVG path | 组件沿路径移动，start/end 占位符替换为实际坐标 | path 非空 | AC-1.1, AC-1.2 |
| R-2 | 边界 | path 为空字符串 | IsValid() 返回 false，不设置路径动画 | `motion_path_option.h:70-73` | AC-1.3 |
| R-3 | 行为 | from=0.0, to=1.0（默认） | progress = 0*(1-f) + 1*f = f，覆盖完整路径 | begin=0.0, end=1.0 | AC-2.1 |
| R-4 | 边界 | from <0 或 >1 | 归一化为默认值 0.0 | SDK d.ts:4577 | AC-2.4 |
| R-5 | 异常 | IsValid()=false（path 为空） | Evaluate 返回 `startPoint_*(1-f) + endPoint_*f` 线性插值 | `motion_path_evaluator.cpp:64-65` | AC-3.1 |
| R-6 | 异常 | GetMotionPathPosition 返回 false | Evaluate 返回零偏移 `MotionPathPosition{Offset(), 0.0f}` | `motion_path_evaluator.cpp:76` | AC-3.2 |
| R-7 | 行为 | rotatable=true | GetMotionPathPosition 返回 rotate 角度，RotateEvaluator 返回该角度 | `motion_path_evaluator.cpp:105-112` | AC-4.1 |
| R-8 | 边界 | rotatable=false（默认） | 不创建 rotate 动画，仅平移 | 默认值 false | AC-4.2 |
| R-9 | 行为 | 属性动画运行在 translate(x/y) | 使用 CreateXEvaluator/CreateYEvaluator，返回 offset.GetX()/GetY() | `motion_path_evaluator.h:50-58` | AC-5.1 |
| R-10 | 行为 | positionType_==PTOFFSET | position.offset += startPoint_，叠加起点偏移 | `motion_path_evaluator.cpp:71-72` | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT | SVG path 设置、占位符替换、空 path 降级 |
| VM-2 | AC-2.1 ~ AC-2.5 | UT | begin/end 范围映射、超范围归一化 |
| VM-3 | AC-3.1 ~ AC-3.3 | UT | 无效路径降级、SVG 解析失败处理 |
| VM-4 | AC-4.1 ~ AC-4.3 | UT + 手工 | rotate 切线角度计算 |
| VM-5 | AC-5.1 ~ AC-5.5 | UT | 5 种子 Evaluator 适配 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| motionPath(value) | Public | value: MotionPathOptions | T | N/A | 设置路径动画 | AC-1.1 |
| MotionPathOptions | Public | path: string, from?: number, to?: number, rotatable?: boolean | — | N/A | 路径动画配置 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| MotionPathOptions | MODIFIED | @crossplatform since 10 | 新增跨平台支持，行为兼容 | AC-1.1 |
| MotionPathOptions | MODIFIED | @atomicservice since 11 | 新增原子化服务支持，行为兼容 | AC-1.1 |

> 截至当前版本，motionPath 未发现任何 @deprecated 标注的 API。

## 接口规格

### 接口定义

**motionPath**

| 属性 | 值 |
|------|-----|
| 函数签名 | `motionPath(value: MotionPathOptions): T` |
| 返回值 | `T` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.path | string | 是 | — | 有效 SVG path 语法；空字符串 → 无路径动画；支持 start.x/start.y/end.x/end.y 占位符 |
| value.from | number | 否 | 0.0 | [0.0, 1.0]，<0 或 >1 → 默认 0.0 |
| value.to | number | 否 | 1.0 | [0.0, 1.0]，<0 或 >1 → 默认 1.0，归一化后 to >= from |
| value.rotatable | boolean | 否 | false | true → 沿路径切线旋转 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 SVG path | Preprocess 替换占位符，Evaluate 沿路径求值 | AC-1.1, AC-1.2 |
| 2 | path 为空 | IsValid()=false，降级为线性插值 | AC-1.3, AC-3.1 |
| 3 | rotatable=true | 额外创建 rotate 动画 | AC-4.1 |
| 4 | from/to 超范围 | 归一化为默认值 | AC-2.4, AC-2.5 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 基础 API @since 7，@crossplatform @since 10，@atomicservice @since 11

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SVG 路径解析依赖 | RosenSvgPainter::GetMotionPathPosition 负责 SVG 解析，路径无效时降级 | AC-3.1, AC-3.2 |
| begin/end 范围 | progress = begin*(1-fraction) + end*fraction，映射到路径子区间 | AC-2.1 |
| 5 种子 Evaluator | 不同动画维度使用不同子 Evaluator，全部转发到核心 Evaluate | AC-5.1 ~ AC-5.4 |
| SharedTransition 复用 | Exchange translate 可直接使用 MotionPathEvaluator | AC-4.3 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 路径动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | MotionPathEvaluator 在动画结束后释放 | UT | 生命周期检查 |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | SVG 路径解析失败不崩溃，降级处理 | UT | 降级测试 |
| 问题定位 | 代码审查覆盖 Evaluate 关键路径 | 代码审查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 路径动画为视觉效果，不影响无障碍属性 | — |
| 大字体 | 否 | 路径动画不涉及字体 | — |
| 深色模式 | 否 | 路径动画不涉及颜色属性 | — |
| 多窗口/分屏 | 否 | 路径动画无窗口相关特殊行为 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | @since 7/10/11 版本策略 | AC-1.1 |
| 生态兼容 | 否 | 无 C API | — |

## 行为场景（Gherkin）

```gherkin
Feature: 路径动画
  作为应用开发者
  我想要让组件沿 SVG 路径移动
  以便实现弧线等非直线动画效果

  Scenario: 基础路径动画
    Given 组件设置了 motionPath({ path: "Mstart.x start.y L100 100 Lend.x end.y" })
    When 属性动画运行
    Then Preprocess 将 start.x/start.y/end.x/end.y 替换为实际坐标
    And Evaluate(fraction) 返回路径上的位置
    And 组件沿 SVG 路径移动

  Scenario: 空 path 降级
    Given 组件设置了 motionPath({ path: "" })
    When 属性动画运行
    Then IsValid() 返回 false
    And Evaluate 返回 start*(1-f) + end*f 线性插值

  Scenario: from/to 子区间
    Given 组件设置了 motionPath({ path: "...", from: 0.3, to: 0.7 })
    When 动画 fraction 从 0 到 1
    Then progress 从 0.3 到 0.7
    And 组件仅沿路径中段移动

  Scenario Outline: from/to 超范围归一化
    Given 组件设置了 motionPath({ path: "...", from: <from>, to: <to> })
    When 归一化处理
    Then from 归一化为 <from_result>
    And to 归一化为 <to_result>

    Examples:
      | from  | to    | from_result | to_result |
      | -0.5  | 1.0   | 0.0         | 1.0       |
      | 1.5   | 2.0   | 0.0         | 1.0       |
      | 0.0   | -0.5  | 0.0         | 1.0       |

  Scenario: rotate 路径切线旋转
    Given 组件设置了 motionPath({ path: "...", rotatable: true })
    When 属性动画运行
    Then GetMotionPathPosition 返回路径切线角度
    And 组件沿切线方向旋转

  Scenario: SVG 解析失败降级
    Given 组件设置了无效 SVG path
    When Evaluate 执行
    Then GetMotionPathPosition 返回 false
    And Evaluate 返回零偏移 MotionPathPosition{Offset(), 0.0f}
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "MotionPathEvaluator Evaluate 和 Preprocess 实现"
  - repo: "openharmony/ace_engine"
    query: "MotionPathEvaluator 5 种子 Evaluator（DoubleEvaluator/DimensionOffsetEvaluator/RotateEvaluator/TransformOperationsEvaluator）"
  - repo: "openharmony/ace_engine"
    query: "RosenSvgPainter::GetMotionPathPosition SVG 路径解析"
  - repo: "openharmony/ace_engine"
    query: "RosenRenderContext::OnMotionPathUpdate 和 RSMotionPathOption 集成"
  - repo: "openharmony/ace_engine"
    query: "SharedTransitionExchange 中 MotionPathEvaluator 复用"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/common.d.ts`
- 源码入口: `frameworks/core/components/common/properties/motion_path_evaluator.h/.cpp`
- Option 定义: `frameworks/core/components/common/properties/motion_path_option.h`
