# 特性规格

## 概述

| Field | Content |
|-------|---------|
| 特性名称 | PatternLock 交互行为、事件与控制器 |
| 特性编号 | Func-05-10-04-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 交互行为属性 | autoReset, enableWaveEffect, skipUnselectedPoint |
| ADDED | 事件回调 | onPatternComplete, onDotConnect |
| ADDED | 控制器接口 | PatternLockController.reset() |
| ADDED | 手势检测逻辑 | 多点触控、热区检测、点选逻辑 |

## 输入文档

- 设计文档: `specs/05-ui-components/10-information-display-components/04-pattern-lock/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/patternlock/`

## 用户故事

### US-1: 手势交互

**作为** 应用用户  
**我想要** 通过滑动手势连接九宫格点  
**以便** 绘制解锁图案

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 手指按下屏幕 THEN 初始化手势状态（isMoveEventValid_=true） | 正常 |
| AC-1.2 | WHEN 手指移动经过某个点 THEN 自动选中该点并触发 dotConnect 事件 | 正常 |
| AC-1.3 | WHEN 手指抬起 THEN 结束手势并触发 patternComplete 事件 | 正常 |
| AC-1.4 | WHEN 多个手指同时触摸 THEN 只跟踪第一个按下的手指 | 边界 |
| AC-1.5 | WHEN 触摸位置在点的热区内 THEN 选中该点（distance <= handleCircleRadius） | 正常 |

### US-2: 自动重置行为

**作为** 应用开发者  
**我想要** 控制图案是否自动重置  
**以便** 提供不同的用户体验

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN autoReset=true（默认）THEN 每次按下时清空之前的选择 | 正常 |
| AC-2.2 | WHEN autoReset=false THEN 保留之前的选择状态 | 正常 |
| AC-2.3 | WHEN autoReset=false 且存在已选点 THEN 新手势开始时不清空 | 边界 |

### US-3: 跳过未选中点

**作为** 应用用户  
**我想要** 从对角点连线时自动跳过中间点  
**以便** 快速绘制复杂图案

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN skipUnselectedPoint=true THEN 自动添加共线的中间点 | 正常 |
| AC-3.2 | WHEN skipUnselectedPoint=false THEN 不自动添加中间点 | 正常 |
| AC-3.3 | WHEN 从(1,1)连到(1,3)THEN 自动选中(1,2) | 正常 |
| AC-3.4 | WHEN 从(1,1)连到(3,3)THEN 自动选中(2,2) | 正常 |

### US-4: 波纹效果

**作为** 应用开发者  
**我想要** 控制选中点是否显示波纹动画  
**以便** 调整视觉效果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN enableWaveEffect=true（默认）THEN 选中点显示光环扩散动画 | 正常 |
| AC-4.2 | WHEN enableWaveEffect=false THEN 不显示光环动画 | 正常 |
| AC-4.3 | WHEN 波纹动画执行 THEN 光环半径从 circleRadius 扩展，透明度渐变 | 正常 |

### US-5: 图案完成事件

**作为** 应用开发者  
**我想要** 在用户完成图案绘制时收到回调  
**以便** 验证图案是否正确

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 手指抬起且选择了至少一个点 THEN 触发 onPatternComplete 回调 | 正常 |
| AC-5.2 | WHEN 未选择任何点 THEN 不触发 onPatternComplete 回调 | 边界 |
| AC-5.3 | WHEN 触发回调 THEN 参数包含选中点的 code 数组 | 正常 |
| AC-5.4 | WHEN 成功图案 THEN 通常需要选择 >=4 个点（应用层判断） | 正常 |

### US-6: 点连接事件

**作为** 应用开发者  
**我想要** 在每次连接新点时收到回调  
**以便** 实时追踪绘制过程

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN 连接新点 THEN 触发 onDotConnect 回调 | 正常 |
| AC-6.2 | WHEN 回调触发 THEN 参数为当前点的 code（int32_t） | 正常 |
| AC-6.3 | WHEN 跳过中间点时 THEN 为每个中间点也触发回调 | 正常 |

### US-7: 控制器重置

**作为** 应用开发者  
**我想要** 通过控制器手动重置图案  
**以便** 提供清除按钮

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-7.1 | WHEN 调用 controller.reset() THEN 清空已选点 | 正常 |
| AC-7.2 | WHEN 重置后 THEN 触发取消动画（线条收回） | 正常 |
| AC-7.3 | WHEN 重置后 THEN 标记需要重绘（PROPERTY_UPDATE_RENDER） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-2 | 单元测试 | patternlock_pattern_test |
| AC-1.2 | R-2, R-12 | TASK-2 | 交互测试 | AddChoosePoint 验证 |
| AC-1.3 | R-3, R-10 | TASK-2 | 事件测试 | OnTouchUp 验证 |
| AC-1.4 | R-4 | TASK-2 | 多点触控测试 | HandleTouchEvent 测试 |
| AC-1.5 | R-5 | TASK-2 | 热区测试 | CheckInHotSpot 测试 |
| AC-2.1 | R-6 | TASK-2 | 自动重置测试 | autoReset=true 测试 |
| AC-2.2 | R-7 | TASK-2 | 保留状态测试 | autoReset=false 测试 |
| AC-2.3 | R-8 | TASK-2 | 边界测试 | CheckAutoReset 测试 |
| AC-3.1 | R-9 | TASK-2 | 跳过测试 | skipUnselectedPoint=true 测试 |
| AC-3.2 | R-10 | TASK-2 | 不跳过测试 | skipUnselectedPoint=false 测试 |
| AC-3.3 | R-11 | TASK-2 | 垂直跳过测试 | (1,1)->(1,3) 测试 |
| AC-3.4 | R-12 | TASK-2 | 对角跳过测试 | (1,1)->(3,3) 测试 |
| AC-4.1 | R-13 | TASK-2 | 波纹动画测试 | enableWaveEffect=true 测试 |
| AC-4.2 | R-14 | TASK-2 | 无波纹测试 | enableWaveEffect=false 测试 |
| AC-4.3 | R-15 | TASK-2 | 动画参数测试 | 光环参数验证 |
| AC-5.1 | R-16 | TASK-2 | 事件触发测试 | patternComplete 测试 |
| AC-5.2 | R-17 | TASK-2 | 空选择测试 | 无点时不触发 |
| AC-5.3 | R-18 | TASK-2 | 参数验证测试 | code 数组验证 |
| AC-5.4 | R-19 | TASK-2 | 成功条件测试 | >=4 点判断 |
| AC-6.1 | R-20 | TASK-2 | 连接事件测试 | dotConnect 测试 |
| AC-6.2 | R-21 | TASK-2 | 参数验证测试 | code 参数验证 |
| AC-6.3 | R-22 | TASK-2 | 中间点回调测试 | 跳过时多回调 |
| AC-7.1 | R-23 | TASK-2 | 重置功能测试 | controller.reset() 测试 |
| AC-7.2 | R-24 | TASK-2 | 取消动画测试 | StartModifierCanceledAnimate 验证 |
| AC-7.3 | R-25 | TASK-2 | 重绘标记测试 | MarkDirtyNode 验证 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 触摸按下（TouchType::DOWN） | 设置 isMoveEventValid_=true，尝试添加起始点 | 无 | AC-1.1 |
| R-2 | 行为 | 触摸移动经过热点 | 调用 AddChoosePoint() 选中点 | 无 | AC-1.2 |
| R-3 | 行为 | 触摸抬起（TouchType::UP） | 调用 OnTouchUp()，触发 AddPointEnd() | 无 | AC-1.3 |
| R-4 | 边界 | 多个手指触摸 | 只跟踪 fingerId_ 匹配的第一个手指 | fingerId_ == -1 时初始化 | AC-1.4 |
| R-5 | 行为 | 触摸点在热点内 | CheckInHotSpot() 返回 true | distance <= handleCircleRadius | AC-1.5 |
| R-6 | 行为 | autoReset=true | OnTouchDown() 调用 HandleReset() 清空状态 | 默认值 true | AC-2.1 |
| R-7 | 行为 | autoReset=false | 不清空 choosePoint_，保留选择状态 | 无 | AC-2.2 |
| R-8 | 边界 | autoReset=false 且 choosePoint_ 非空 | CheckAutoReset() 返回 false，跳过重置 | isMoveEventValid_=false 时 | AC-2.3 |
| R-9 | 行为 | skipUnselectedPoint=true | AddPassPoint() 检测并添加共线中间点 | 无 | AC-3.1 |
| R-10 | 行为 | skipUnselectedPoint=false | AddPassPoint() 直接返回，不添加中间点 | 无 | AC-3.2 |
| R-11 | 行为 | 从(1,1)连到(1,3) | 检测并添加(1,2) | 垂直共线 | AC-3.3 |
| R-12 | 行为 | 从(1,1)连到(3,3) | 检测并添加(2,2) | 对角共线 | AC-3.4 |
| R-13 | 行为 | enableWaveEffect=true | StartConnectedCircleAnimate() 启动光环动画 | 默认值 true | AC-4.1 |
| R-14 | 行为 | enableWaveEffect=false | SetBackgroundCircleRadius() 直接设置值，无动画 | 无 | AC-4.2 |
| R-15 | 行为 | 光环动画执行 | lightRingRadius 从 circleRadius 扩展，lightRingAlphaF 渐变 | 持续 500ms | AC-4.3 |
| R-16 | 行为 | 手指抬起且 choosePoint_ 非空 | 触发 eventHub->UpdateCompleteEvent() | 无 | AC-5.1 |
| R-17 | 边界 | choosePoint_ 为空 | OnTouchUp() 直接返回，不触发回调 | count < 1 | AC-5.2 |
| R-18 | 行为 | 触发 patternComplete | 参数为 std::vector<int> chooseCellVec | code 数组 | AC-5.3 |
| R-19 | 行为 | 成功图案判定 | 应用层判断 chooseCellVec.size() >= 4 | 组件不强制 | AC-5.4 |
| R-20 | 行为 | 连接新点 | UpdateDotConnectEvent() 触发回调 | 无 | AC-6.1 |
| R-21 | 行为 | dotConnect 回调参数 | choosePoint_.back().GetCode() | int32_t code | AC-6.2 |
| R-22 | 行为 | 跳过中间点时 | AddPassPointToChoosePoint() 为每个中间点触发回调 | 无 | AC-6.3 |
| R-23 | 行为 | 调用 controller.reset() | 触发 SetResetImpl() 注册的回调 → HandleReset() | 无 | AC-7.1 |
| R-24 | 行为 | 重置时 | StartModifierCanceledAnimate() 启动取消动画 | 线条收回 | AC-7.2 |
| R-25 | 行为 | 重置后 | host->MarkDirtyNode(PROPERTY_UPDATE_RENDER) | 触发重绘 | AC-7.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.5（手势交互） | 交互测试 | 触摸事件处理流程 |
| VM-2 | AC-2.1~2.3（自动重置） | 状态测试 | autoReset 开关行为 |
| VM-3 | AC-3.1~3.4（跳过逻辑） | 算法测试 | 共线检测正确性 |
| VM-4 | AC-4.1~4.3（波纹效果） | 动画测试 | 光环动画参数 |
| VM-5 | AC-5.1~5.4（完成事件） | 事件测试 | 回调触发和参数 |
| VM-6 | AC-6.1~6.3（连接事件） | 事件测试 | 实时回调触发 |
| VM-7 | AC-7.1~7.3（控制器） | 接口测试 | reset() 功能验证 |

## API 变更分析

### 新增 API

> 已有实现补录，无新增 API。

### 变更/废弃 API

> 无变更或废弃 API。

## 接口规格

### 接口定义

**SetAutoReset()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `autoReset(isReset: boolean): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2, AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| isReset | boolean | 否 | true | 无 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | isReset=true | 每次触摸按下清空选择状态 | AC-2.1 |
| 2 | isReset=false | 保留选择状态，不清空 | AC-2.2 |
| 3 | 未调用 | 使用默认值 true | AC-2.1 |

---

**SetEnableWaveEffect()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableWaveEffect(enable: boolean): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1, AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enable | boolean | 否 | true | 无 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | enable=true | 选中点显示光环扩散动画 | AC-4.1 |
| 2 | enable=false | 不显示光环动画 | AC-4.2 |

---

**SetSkipUnselectedPoint()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `skipUnselectedPoint(skip: boolean): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| skip | boolean | 否 | false | 无 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | skip=true | 自动添加共线中间点 | AC-3.1 |
| 2 | skip=false | 不自动添加中间点 | AC-3.2 |

---

**SetOnPatternComplete()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onPatternComplete(callback: (result: PatternCompleteResult) => void): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1, AC-5.2, AC-5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | function | 否 | 无 | 参数为 PatternCompleteResult |

**PatternCompleteResult 结构**

| 属性 | 类型 | 说明 |
|------|------|------|
| input | number[] | 选中点的 code 数组 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 手指抬起且 choosePoint_ 非空 | 触发回调，传入选中点 code 数组 | AC-5.1, AC-5.3 |
| 2 | choosePoint_ 为空 | 不触发回调 | AC-5.2 |

---

**SetOnDotConnect()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onDotConnect(callback: (index: number) => void): PatternLock` |
| 返回值 | `PatternLock` — 组件本身 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.1, AC-6.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | function | 否 | 无 | 参数为点的 code（number） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 连接新点 | 触发回调，传入当前点 code | AC-6.1, AC-6.2 |
| 2 | 跳过中间点时 | 为每个中间点也触发回调 | AC-6.3 |

---

**PatternLockController.reset()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `reset(): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-7.1, AC-7.2, AC-7.3 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 reset() | 清空 choosePoint_，重置状态 | AC-7.1 |
| 2 | 重置时 | 触发取消动画（线条收回） | AC-7.2 |
| 3 | 重置后 | 标记 PROPERTY_UPDATE_RENDER 触发重绘 | AC-7.3 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** @since 8 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 多点触控限制 | 只跟踪第一个按下的手指（fingerId_） | AC-1.4 |
| 热区检测公式 | distance <= handleCircleRadius | AC-1.5 |
| 跳过逻辑条件 | skipUnselectedPoint=true 时才检测共线 | AC-3.1, AC-3.2 |
| 波纹动画依赖 | 依赖每点的 lightRingRadius 和 lightRingAlphaF 动画属性 | AC-4.3 |
| code 计算公式 | `COL_COUNT * (row - 1) + (column - 1)` | AC-5.3, AC-6.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 触摸响应延迟 < 16ms | 帧率测试 | 渲染管线分析 |
| 内存 | 跳过逻辑不额外分配内存 | 静态分析 | AddPassPoint 复用现有向量 |
| 可测试性 | 支持模拟触摸事件 | 单元测试框架 | patternlock_test_ng.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 标准行为 | 交互测试 | - |
| 平板 | 无差异 | 标准行为 | 交互测试 | - |
| 折叠屏 | 无差异 | 标准行为 | 交互测试 | - |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 支持键盘导航（方向键、Enter、ESC）和 hover 事件 | 键盘交互 |
| 大字体 | 否 | 组件尺寸由 sideLength 决定 | - |
| 深色模式 | 否 | 颜色由用户设置，不受主题影响 | - |
| 多窗口/分屏 | 否 | 组件无窗口状态依赖 | - |
| 多用户 | 否 | 无用户状态 | - |
| 版本升级 | 是 | API 14+ 支持 TouchType::CANCEL 作为 UP 处理 | 版本兼容 |
| 生态兼容 | 否 | 无外部依赖 | - |

## 行为场景（可选，Gherkin）

> L1 标准复杂度，使用"接口规格 → 行为场景"表覆盖，无需 Gherkin。

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
  - repo: "openharmony/arkui_ace_engine"
    query: "PatternLock 多点触控行为的 fingerId_ 追踪机制实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "跳过未选中点的共线检测算法详细实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "波纹效果的光环动画参数和时序控制"
```

**关键文档：**
- design.md: `specs/05-ui-components/10-information-display-components/04-pattern-lock/design.md`
- 源码: `frameworks/core/components_ng/pattern/patternlock/`