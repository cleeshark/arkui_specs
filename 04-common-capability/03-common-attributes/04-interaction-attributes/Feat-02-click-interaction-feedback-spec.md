# 特性规格

> Func-04-03-04-Feat-02 点击交互反馈：固化 `clickEffect` 的 ArkTS、Modifier、Static、内部 Native 和渲染行为，不包含 `onClick`。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 点击交互反馈 (Click Interaction Feedback) |
| 特性编号 | Func-04-03-04-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | ArkTS API 10 起；API 18 支持 Optional/undefined reset |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `clickEffect` 行为规格 | 补录已有实现的档位、scale、触摸状态机、reset 和兼容行为 |
| ADDED | 多前端差异声明 | 固化 Dynamic、Modifier、Static、TypedNode、CJ 与 Legacy 的现状差异 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/04-interaction-attributes/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:17659,23064` | 外部 checkout 核验 |
| 枚举 SDK | `interface/sdk-js/api/@internal/component/ets/enums.d.ts:8482` | 外部 checkout 核验 |

> 目标 ace_engine checkout 不含 `interface/sdk-js`。Dynamic SDK 来自本机 `/Users/piggyguy/workspace/arkui_x/interface/sdk-js`；Static canonical `common.static.d.ets` 缺失，Static 仅按生成实现记录，不推断公开版本。

## 用户故事

### US-1: 配置点击反馈档位和缩放

**作为** 应用开发者，  
**我想要** 选择 LIGHT/MIDDLE/HEAVY 点击反馈并可选指定 scale，  
**以便** 为触摸按压提供不同力度的缩放反馈。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 LIGHT 且未提供合法 scale THEN 使用 scale 0.90 和 spring(v=10,m=1,k=410,d=38) | 正常 |
| AC-1.2 | WHEN 设置 MIDDLE 且未提供合法 scale THEN 使用 scale 0.95 和 spring(v=10,m=1,k=350,d=35) | 正常 |
| AC-1.3 | WHEN 设置 HEAVY 且未提供合法 scale THEN 使用 scale 0.95 和 spring(v=0,m=1,k=240,d=28) | 正常 |
| AC-1.4 | WHEN scale 位于闭区间 [0,1] THEN DOWN 动画目标为 `sqrt(scale)` | 边界 |
| AC-1.5 | WHEN Dynamic/Modifier scale 小于 0 或大于 1 THEN 按档位回退 0.90 或 0.95 | 异常 |
| AC-1.6 | WHEN Static 显式 scale 超出 [0,1] THEN Static 前端直接透传；渲染层再次按档位回退合法默认值 | 异常 |

### US-2: 播放和恢复点击反馈

**作为** 用户，  
**我想要** 按下时看到反馈、抬起或取消时恢复，  
**以便** 明确感知组件已接收触摸交互。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 首次收到 DOWN THEN 捕获当前 transform scale，并以 100ms 弹簧动画设置为 `sqrt(configuredScale)` | 正常 |
| AC-2.2 | WHEN DOWN 后再次收到 DOWN 且尚未 UP/CANCEL THEN 不重新捕获 scale，也不重复播放按下动画 | 边界 |
| AC-2.3 | WHEN 收到 UP 或 CANCEL 且 level 有效 THEN 恢复首次 DOWN 捕获的 scale | 恢复 |
| AC-2.4 | WHEN 节点未注册 `onClick` 但设置了 `clickEffect` THEN 内部 TouchEvent 仍可使普通节点成为触摸目标并播放反馈 | 正常 |
| AC-2.5 | WHEN 节点 disabled 或 inactive THEN TouchTest 前置返回，不触发点击反馈 | 边界 |
| AC-2.6 | WHEN触摸类型为 MOVE 或其他非 DOWN/UP/CANCEL 类型 THEN 不改变点击反馈 scale | 边界 |

### US-3: 更新和重置点击反馈

**作为** 应用开发者，  
**我想要** 更新或清除 `clickEffect`，  
**以便** 按组件状态控制点击视觉反馈。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN Dynamic 传入 `null` 或 API 18+ 传入 `undefined` THEN 写入 UNDEFINED + 0.90，后续触摸不播放动画 | 恢复 |
| AC-3.2 | WHEN Dynamic 参数为非 object 且非 null/undefined THEN 忽略本次设置并保留旧值 | 异常 |
| AC-3.3 | WHEN level 缺失、非 number 或超出 LIGHT~HEAVY THEN Dynamic/Modifier 归一为 LIGHT | 异常 |
| AC-3.4 | WHEN 重设有效 clickEffect THEN 仅更新 RenderContext 属性，内部 touch listener 不重复注册 | 正常 |
| AC-3.5 | WHEN reset clickEffect THEN 内部 touch listener 保留，但因 level=UNDEFINED 跳过动画分支 | 恢复 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1~R-4 | 已有实现 | Bridge/Rosen UT | `js_view_abstract.cpp:12002-12045`; `rosen_render_context.cpp:7625-7662` |
| AC-2.1~2.6 | R-5~R-9 | 已有实现 | Gesture/Rosen 交互测试 | `rosen_render_context.cpp:7569-7623`; `gesture_event_hub.cpp:342-360` |
| AC-3.1~3.5 | R-10~R-13 | 已有实现 | Bridge/Modifier/Static UT | `arkts_native_common_bridge.cpp:7637-7683`; `common_method_modifier.cpp:1982-2000` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | level=LIGHT/MIDDLE/HEAVY 且 scale 缺失或无效 | 默认 scale 分别为 0.90/0.95/0.95 | 三档 spring 参数固定 | AC-1.1~1.3 |
| R-2 | 边界 | scale∈[0,1] | 渲染目标为 `sqrt(scale)` | 0 和 1 均合法 | AC-1.4 |
| R-3 | 异常 | Dynamic/Modifier scale<0 或 >1 | 按档位回退默认 scale | NaN 的比较行为由数值转换路径决定，不额外承诺 | AC-1.5 |
| R-4 | 异常 | Static 显式 scale 越界 | Static 透传，Rosen 层最终回退档位默认值 | Static canonical SDK 缺失 | AC-1.6 |
| R-5 | 行为 | clickEffect 首次生效或 OnModifyDone | 在 GestureEventHub 注册一个内部 TouchEventImpl | 不依赖 onClick/IsClickable | AC-2.4 |
| R-6 | 行为 | 首次 DOWN | 捕获当前 scale，设置 `isTouchUpFinished_=false` 并播放按下动画 | listener 读取 touches 首项 | AC-2.1 |
| R-7 | 边界 | 未结束按压时再次 DOWN | 不重复处理 | 直到 UP/CANCEL 才恢复可再次按下 | AC-2.2 |
| R-8 | 恢复 | UP 或 CANCEL 且 level!=UNDEFINED | 恢复首次 DOWN 捕获的 scale | MOVE 等类型忽略 | AC-2.3, AC-2.6 |
| R-9 | 边界 | disabled 或 inactive | FrameNode TouchTest 前置返回，反馈不触发 | 与 onClick 是否注册无关 | AC-2.4, AC-2.5 |
| R-10 | 恢复 | Dynamic null/undefined 或 Modifier/Static reset | 写入 UNDEFINED + 0.90 | undefined 的公开契约自 API 18 | AC-3.1 |
| R-11 | 异常 | Dynamic 非 object | 保留旧值 | null/undefined 是 reset，不属于此分支 | AC-3.2 |
| R-12 | 异常 | level 缺失、非 number 或越界 | Dynamic/Modifier 归一 LIGHT；Static 非法枚举转为 UNDEFINED | 多前端存在差异 | AC-3.3 |
| R-13 | 恢复 | 重设或 reset | 仅更新属性；touch listener 只初始化一次且 reset 后仍驻留 | UNDEFINED 使动画分支跳过 | AC-3.4, AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.4, R-1/R-2 | Rosen UT | 三档 spring、默认值、0/1 和 sqrt |
| VM-2 | AC-1.5~1.6, R-3/R-4 | Bridge/Static/Rosen UT | 越界 scale 的前端差异及最终回退 |
| VM-3 | AC-2.1~2.3, R-6~R-8 | 触摸序列 UT | DOWN、重复 DOWN、UP、CANCEL 恢复 |
| VM-4 | AC-2.4~2.6, R-5/R-9 | Gesture/FrameNode UT | 无 onClick、disabled/inactive、其他触摸类型 |
| VM-5 | AC-3.1~3.5, R-10~R-13 | Bridge/Modifier/Static UT | reset、非法类型、listener 生命周期 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `clickEffect(value: ClickEffect | null): T` | Public | level 必填，scale 可选；null reset | T | N/A | API 10+ 点击反馈 | AC-1.1~3.5 |
| `clickEffect(effect: Optional<ClickEffect | null>): T` | Public | 支持 undefined/null reset | T | N/A | API 18+ Optional 重载 | AC-3.1 |
| `ArkUICommonModifier::setClickEffect/resetClickEffect` | InnerApi | node, level, scale | void | N/A | 内部 Native modifier ABI | AC-1.1~3.5 |

> 当前没有 Public Native `NODE_CLICK_EFFECT` 或 `ArkUI_ClickEffect`。内部 modifier ABI 不作为公共 C API 承诺。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | 已有能力补录，无接口变更 | — | — |

## 接口规格

### 接口定义

**clickEffect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `clickEffect(value: ClickEffect | null): T`；API 18+ `clickEffect(effect: Optional<ClickEffect | null>): T` |
| 返回值 | `T` — 当前组件属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value/effect | ClickEffect/null/undefined | 是 | null/undefined 表示 reset | undefined 的 Public 契约自 API 18 |
| level | ClickEffectLevel | 是 | Dynamic 非法值归一 LIGHT | LIGHT/MIDDLE/HEAVY |
| scale | number | 否 | LIGHT 0.90；MIDDLE/HEAVY 0.95 | 渲染层最终限定 [0,1] |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | LIGHT + scale 0.81 + DOWN | 以 100ms spring 动画缩放到 0.9 | AC-1.1, AC-1.4, AC-2.1 |
| 2 | DOWN 后 UP/CANCEL | 恢复 DOWN 前捕获的 scale | AC-2.3 |
| 3 | null/undefined reset | 写 UNDEFINED，后续触摸不播放 | AC-3.1, AC-3.5 |
| 4 | 非 object | 保留旧 clickEffect | AC-3.2 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文固化现有多前端和 Legacy 差异。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** ArkTS API 10；API 18 起公开 Optional/undefined reset。
- **API 版本号策略:** `ClickEffect`、`ClickEffectLevel`、基础 `clickEffect` 自 API 10；原子化服务自 API 11；Modifier 入口至少 API 12；Static 版本不从生成源码推断。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 与 onClick 解耦 | clickEffect 使用内部 TouchEventImpl，不依赖点击回调 | AC-2.4 |
| RenderContext 持有状态 | ClickEffectInfo、listener 和按压恢复 scale 均由 RenderContext 管理 | AC-1.1~3.5 |
| Public Native 不开放 | 只能登记内部 modifier ABI，不得宣称存在 Public Native clickEffect | 全部 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次 DOWN/UP 动画 duration 固定 100ms | Rosen UT | `rosen_render_context.cpp:148-159,7625-7662` |
| 可靠性 | UP/CANCEL 在 level 有效时恢复 DOWN 前 scale | 触摸序列 UT | `rosen_render_context.cpp:7587-7623` |
| 可测试性 | 三档、scale 边界、reset 和触摸序列可独立注入 | Host UT | `rosen_render_context_test_new.cpp:403-422` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 触摸 DOWN/UP/CANCEL 触发 | 按本规格处理 | 真机交互 | `rosen_render_context.cpp:7569-7623` |
| 平板 | 触摸行为一致 | 鼠标 click 不替代 TouchEvent 路径 | 真机交互 | 同上 |
| 折叠屏 | 折叠状态不改变档位和动画参数 | 仅当前节点 transform scale 参与 | 真机交互 | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不改变节点语义和操作定义 | 全部 |
| 大字体 | 否 | 不改变布局和文字度量 | 全部 |
| 深色模式 | 否 | 点击反馈仅操作 transform scale | AC-1.1~2.3 |
| 多窗口/分屏 | 否 | 无窗口级共享状态 | 全部 |
| 多用户 | 否 | 无持久化数据 | 全部 |
| 版本升级 | 是 | API 10 基础能力，API 18 Optional reset | AC-3.1 |
| 生态兼容 | 是 | Dynamic/Static/TypedNode/Legacy 能力和参数归一化不一致 | AC-1.5~3.5 |

## 风险 / Risks

| 项 | 类型 | 影响 | 处理方式 | 关联 AC |
|----|------|------|----------|---------|
| reset 发生在 DOWN 与 UP/CANCEL 之间时可能不恢复 scale | 行为 | 高 | 按现状登记；UP/CANCEL 读取最新 UNDEFINED 后跳过恢复 | AC-2.3, AC-3.1 |
| 按压期间外部修改 transform，恢复会覆盖为 DOWN 时旧值 | 行为 | 中 | 按缓存恢复语义固化 | AC-2.3 |
| 多指使用 `touches.front()` 且无空列表保护 | 可靠性 | 中 | 多指和空 touches 列为验证缺口 | AC-2.1~2.3 |
| ArkComponent `checkObjectDiff()` 对 null 无条件访问字段 | 前端 | 中 | 保留源码风险，不宣称 null diff 路径安全 | AC-3.1 |
| Static inner_api 类型不含 null，generated 入口包含 null | API | 中 | 记录 Static 类型面不一致 | AC-3.1 |
| `ArkBaseNode.clickEffect()` 当前直接返回且不下发 | 兼容 | 高 | TypedNode 通道按 no-op 现状登记 | AC-1.1~3.5 |
| Legacy `SetClickEffectLevel` 为空实现 | 兼容 | 高 | Legacy 管线不承诺点击反馈 | 全部 |
| Static 合法/非法 clickEffect 测试均被禁用 | 测试 | 中 | VM-1/VM-2/VM-5 要求补足有效断言 | AC-1.1~3.5 |

## 行为场景（可选，Gherkin）

本特性复杂度为标准，采用“接口规格 → 行为场景”表，不重复编写 Gherkin。

## Spec 自审清单

- [x] 无“TBD”“TODO”“待定”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确，仅覆盖 `clickEffect`，不覆盖 `onClick`
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "clickEffect RenderContext storage, touch listener and DOWN-UP-CANCEL state machine (frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:7569-7662)"
  - repo: "openharmony/arkui_ace_engine"
    query: "Dynamic clickEffect parameter normalization (frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:12002-12045)"
  - repo: "openharmony/arkui_ace_engine"
    query: "Static clickEffect conversion and default scale behavior (frameworks/core/interfaces/native/implementation/common_method_modifier.cpp:1982-2000,4671-4688)"
```

**关键文档:** Dynamic SDK `common.d.ts:17659-17713,23064-23095`；枚举 SDK `enums.d.ts:8482-8562`；内部 modifier `frameworks/core/interfaces/arkoala/arkoala_api.h:3520-3524`。
