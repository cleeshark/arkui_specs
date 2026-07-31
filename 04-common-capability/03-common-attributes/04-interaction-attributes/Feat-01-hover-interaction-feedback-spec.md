# 特性规格

> Func-04-03-04-Feat-01 悬停交互反馈：固化 `hoverEffect` 的 ArkTS、Modifier、Static、Native 和渲染行为，不包含 `onHover`。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 悬停交互反馈 (Hover Interaction Feedback) |
| 特性编号 | Func-04-03-04-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | ArkTS API 8 起；Public Native API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `hoverEffect` 行为规格 | 补录已有实现的设置、重置、命中分发、动画和兼容行为 |
| ADDED | Public Native 属性规格 | 补录 API 23 `NODE_HOVER_EFFECT` 的 set/get/reset 和错误处理 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/04-interaction-attributes/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:20478` | 外部 checkout 核验 |
| 枚举 SDK | `interface/sdk-js/api/@internal/component/ets/enums.d.ts:7141` | 外部 checkout 核验 |

> 目标 ace_engine checkout 不含 `interface/sdk-js`。SDK 声明来自本机 `/Users/piggyguy/workspace/arkui_x/interface/sdk-js`；无法证明与目标源码完全同基线，版本差异作为风险保留。

## 用户故事

### US-1: 选择悬停反馈类型

**作为** 应用开发者，  
**我想要** 通过 `hoverEffect` 选择自动、缩放、高亮或无反馈，  
**以便** 为鼠标悬停提供与组件语义匹配的视觉提示。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `hoverEffect(HoverEffect.Scale)` 且鼠标进入命中节点 THEN 节点按 AppTheme 参数从 1.0 缩放至 1.05 | 正常 |
| AC-1.2 | WHEN 设置 `hoverEffect(HoverEffect.Highlight)` 且鼠标进入命中节点 THEN 节点播放背景叠色动画并调用 `Pattern::OnHoverWithHightLight(true)` | 正常 |
| AC-1.3 | WHEN 设置 `hoverEffect(HoverEffect.None)` THEN 鼠标进入或离开均不播放通用悬停动画 | 正常 |
| AC-1.4 | WHEN 设置 `hoverEffect(HoverEffect.Auto)` THEN 通用管线使用组件提供的 `hoverEffectAuto` 解析实际类型；无法解析时不播放通用动画 | 边界 |
| AC-1.5 | WHEN 悬停状态下收到鼠标 PRESS THEN 当前通用悬停效果退出；WHEN 随后 RELEASE 且指针仍命中 THEN 效果重新进入 | 正常 |
| AC-1.6 | WHEN 鼠标离开窗口 THEN 当前和上一悬停节点均退出通用悬停效果 | 恢复 |

### US-2: 更新和重置悬停反馈

**作为** 应用开发者，  
**我想要** 动态更新或清除 `hoverEffect`，  
**以便** 组件状态变化后恢复一致的交互反馈。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 将已设置类型改为另一类型 THEN 框架先按旧类型执行退出动画，再保存新类型 | 恢复 |
| AC-2.2 | WHEN 重复设置相同类型 THEN 不额外执行旧类型退出动画 | 边界 |
| AC-2.3 | WHEN Dynamic ArkTS 传入 `undefined`、`null` 或非 number THEN 属性重置为 Auto | 异常 |
| AC-2.4 | WHEN Modifier/Static 传入 `undefined` THEN 属性重置为 Auto | 恢复 |
| AC-2.5 | WHEN Dynamic ArkTS 传入任意 number THEN 数值直接转换为内部枚举；非受支持数值不产生通用动画 | 异常 |
| AC-2.6 | WHEN Static 枚举转换收到非法值 THEN 转换失败并最终重置为 Auto | 异常 |

### US-3: 通过 Native Node 设置悬停反馈

**作为** Native 应用开发者，  
**我想要** 使用公共 Node 属性设置、查询和重置悬停反馈，  
**以便** 在 Native UI 中获得与 ArkTS 对齐的能力。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN API 23+ 以 `NODE_HOVER_EFFECT` 设置 AUTO/SCALE/HIGHLIGHT/NONE THEN adapter 映射到内部 AUTO/SCALE/BOARD/NONE | 正常 |
| AC-3.2 | WHEN 查询 `NODE_HOVER_EFFECT` THEN 返回公共枚举 0~3；未知内部值回退为 AUTO | 边界 |
| AC-3.3 | WHEN 重置 `NODE_HOVER_EFFECT` THEN 属性写为 AUTO | 恢复 |
| AC-3.4 | WHEN item 为空、size 不等于 1 或枚举越界 THEN adapter 先写入 AUTO 并返回参数错误 401 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1~R-4 | 已有实现 | Host UT/交互测试 | `frame_node.cpp:4594-4620`; `rosen_render_context.cpp:5520-5583` |
| AC-1.5~1.6 | R-5 | 已有实现 | EventManager UT/交互测试 | `event_manager.cpp:2196-2254` |
| AC-2.1~2.6 | R-6~R-9 | 已有实现 | Bridge/Static UT | `input_event_hub.cpp:140-150`; `js_view_abstract.cpp:11717-11728` |
| AC-3.1~3.4 | R-10~R-12 | 已有实现 | NativeNode UT | `style_modifier.cpp:1744-1810`; `native_node_test.cpp:12308-12460` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 鼠标命中结果包含 HoverEffectTarget | EventManager 仅选命中序列中的第一个目标作为当前通用 hover 节点 | 嵌套目标同一时刻只播放一个通用效果 | AC-1.1~1.4 |
| R-2 | 行为 | 最终类型为 SCALE | 使用 AppTheme 的 1.0→1.05、250ms、cubic(0.2,0,0.2,1) 设置 RenderContext scale | 直接写主题起止 scale，不保存用户原 scale | AC-1.1 |
| R-3 | 行为 | 最终类型为 BOARD | 混合背景色和 5% 黑色 hover 色并调用 Pattern 高亮扩展钩子 | 与 SCALE 的组件副作用不同 | AC-1.2 |
| R-4 | 边界 | 类型为 AUTO/UNKNOWN/NONE/OPACITY | AUTO/UNKNOWN 先用 `hoverEffectAuto` 解析；最终非 SCALE/BOARD 时无通用动画 | OPACITY 是内部值，Public ArkTS 不暴露 | AC-1.3, AC-1.4 |
| R-5 | 恢复 | PRESS/RELEASE/WINDOW_LEAVE | PRESS 退出；RELEASE 且仍命中时进入；WINDOW_LEAVE 清理当前和上一节点 | Pen hover 不收集 HoverEffectTarget | AC-1.5, AC-1.6 |
| R-6 | 恢复 | 设置类型与旧类型不同 | 先执行旧类型退出，再保存新类型 | 同类型重设不退出 | AC-2.1, AC-2.2 |
| R-7 | 异常 | Dynamic 参数非 number | 重置 AUTO | 包含 `undefined`、`null`、对象和字符串 | AC-2.3 |
| R-8 | 异常 | Dynamic 参数为 number | 不校验范围，直接 static_cast；无法识别的值不进入 SCALE/BOARD 分支 | Static 非法枚举会转为空并重置 AUTO | AC-2.5, AC-2.6 |
| R-9 | 恢复 | Modifier/Static 属性删除或值为 undefined | 调用 reset，写入 AUTO | reset 不是 UNKNOWN | AC-2.4 |
| R-10 | 行为 | Public Native 传入 0~3 | 显式映射 AUTO/SCALE/HIGHLIGHT/NONE 到内部 AUTO/SCALE/BOARD/NONE | 公共与内部枚举数值不同 | AC-3.1 |
| R-11 | 异常 | Public Native 参数无效 | 写入 AUTO 后返回 401 | item 非空、size=1、值域 0~3 | AC-3.4 |
| R-12 | 恢复 | Public Native get/reset | get 反向映射，未知值返回 AUTO；reset 写 AUTO | API 23+ | AC-3.2, AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, R-2 | Rosen/交互测试 | Scale 的主题参数和最终 RS scale |
| VM-2 | AC-1.2, R-3 | Rosen/Pattern 测试 | Highlight 叠色和组件扩展钩子 |
| VM-3 | AC-1.3~1.6, R-1/R-4/R-5 | EventManager 测试 | 类型分派、首目标选择和鼠标状态机 |
| VM-4 | AC-2.1~2.6, R-6~R-9 | Bridge/Static 测试 | 重注册、undefined、非法类型差异 |
| VM-5 | AC-3.1~3.4, R-10~R-12 | NativeNode 测试 | set/get/reset、枚举映射和 401 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `hoverEffect(value: HoverEffect): T` | Public | Auto/Scale/Highlight/None | T | N/A | 设置 ArkTS 悬停反馈 | AC-1.1~2.6 |
| `NODE_HOVER_EFFECT` | Public Native | `.value[0].i32`，0~3 | attribute item/401 | 0, 401 | Native set/get/reset 悬停反馈 | AC-3.1~3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | 已有能力补录，无接口变更 | — | — |

## 接口规格

### 接口定义

**hoverEffect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `hoverEffect(value: HoverEffect): T` |
| 返回值 | `T` — 当前组件属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | HoverEffect | 是 | Auto（reset 后） | SDK 公开 Auto/Scale/Highlight/None；不同前端对非法值处理不同 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Scale + 鼠标进入 | 播放主题缩放动画 | AC-1.1 |
| 2 | Highlight + 鼠标进入 | 播放叠色动画并通知 Pattern | AC-1.2 |
| 3 | Dynamic 非 number | 重置 Auto | AC-2.3 |
| 4 | Public Native 非法参数 | 重置 Auto 并返回 401 | AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文固化现有多前端差异。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** ArkTS API 8；Public Native API 23。
- **API 版本号策略:** Dynamic `hoverEffect`/`HoverEffect` 自 API 8，跨平台自 API 10，原子化服务自 API 11；Static canonical SDK 缺失，不从生成源码推断版本。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 输入与渲染分层 | 前端只解析/映射类型，InputEventHub 存储，EventManager 分发，RenderContext 动画 | AC-1.1~2.6 |
| 鼠标专属触发 | 通用 hoverEffect 由 MouseEvent 命中链驱动，不由 onHover 回调、Pen 或无障碍悬停驱动 | AC-1.1~1.6 |
| Public Native 显式映射 | 不得直接复用公共枚举数值作为内部枚举 | AC-3.1~3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次鼠标状态变化只选择一个通用 HoverEffectTarget | EventManager UT | `event_manager.cpp:2006-2043` |
| 可靠性 | 同一进入/退出状态重复调用不重复播放动画 | Rosen UT | `rosen_render_context.cpp:5520-5583` |
| 可测试性 | 四种公开枚举、reset、非法值和 Native 401 可独立注入 | Host UT/NativeNode UT | `input_event_hub_test_ng.cpp:1155-1225` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无鼠标输入时不触发通用悬停反馈 | 属性可设置但需鼠标命中链 | 真机交互 | `event_manager.cpp:2196-2254` |
| 平板 | 外接鼠标时按本规格触发 | 同手机/桌面模式 | 真机交互 | 同上 |
| 折叠屏 | 折叠状态不改变类型映射 | 按当前窗口鼠标命中结果处理 | 真机交互 | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 通用 hoverEffect 不由无障碍悬停触发 | AC-1.1~1.6 |
| 大字体 | 否 | 不改变布局和文字度量 | AC-1.1~1.4 |
| 深色模式 | 是 | Highlight 的最终颜色由背景色和主题 hover 色共同决定 | AC-1.2 |
| 多窗口/分屏 | 是 | WINDOW_LEAVE 清理当前和上一节点 | AC-1.6 |
| 多用户 | 否 | 无用户级持久化数据 | 全部 |
| 版本升级 | 是 | API 8 ArkTS 与 API 23 Public Native 分层开放 | AC-3.1~3.4 |
| 生态兼容 | 是 | Dynamic、Static、Public Native 的非法值策略和枚举数值不同 | AC-2.3~3.4 |

## 风险 / Risks

| 项 | 类型 | 影响 | 处理方式 | 关联 AC |
|----|------|------|----------|---------|
| 目标仓缺少同基线 SDK | 版本 | 中 | 记录外部 checkout 路径，不推断 Static @since | AC-2.3~2.6 |
| Auto 可见行为依赖组件 Pattern | 行为 | 中 | 规格限定通用管线只在解析为 SCALE/BOARD 后动画 | AC-1.4 |
| 悬停中禁用且无后续鼠标事件可能保留视觉状态 | 行为 | 中 | 按现状登记；`SetEnabled` 本身不执行退出动画 | AC-1.6 |
| Scale 直接覆盖用户 transform scale | 兼容 | 中 | 按主题起止值固化，不宣称组合保留用户 scale | AC-1.1 |
| Static hover 专项测试被禁用 | 测试 | 中 | 验证映射要求补足 reset/非法枚举断言 | AC-2.4, AC-2.6 |

## 行为场景（可选，Gherkin）

本特性复杂度为标准，采用“接口规格 → 行为场景”表，不重复编写 Gherkin。

## Spec 自审清单

- [x] 无“TBD”“TODO”“待定”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确，仅覆盖 `hoverEffect`，不覆盖 `onHover`
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "hoverEffect InputEventHub storage and EventManager first HoverEffectTarget selection (frameworks/core/components_ng/event/input_event_hub.cpp:31-46; frameworks/core/common/event_manager.cpp:2006-2043)"
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode hover type dispatch and Rosen theme animation (frameworks/core/components_ng/base/frame_node.cpp:4594-4620; frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:5520-5583)"
  - repo: "openharmony/arkui_ace_engine"
    query: "Public Native NODE_HOVER_EFFECT mapping and validation (interfaces/native/node/style_modifier.cpp:1744-1810)"
```

**关键文档:** Dynamic SDK `common.d.ts:20478-20505`；枚举 SDK `enums.d.ts:7141-7256`；Native API `interfaces/native/native_node.h:9576-9590`。
