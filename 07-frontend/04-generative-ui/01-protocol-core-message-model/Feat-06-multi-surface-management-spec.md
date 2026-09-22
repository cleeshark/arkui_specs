# 特性规格

> Func-07-04-01-Feat-06 多 Surface 管理：固化 `MultiSurfaceController` 栈语义、C++ `SurfaceManager` 栈所有权（`surfaces_`/`surfaceOrder_`/`latestSurfaceId_`）、`pop`/`canPop`/`getSurfaceList` 转发、上限 `MULTI_SURFACE_MAX_COUNT=15`、返回手势开关、pop 错误码。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 多 Surface 管理 |
| 特性编号 | Func-07-04-01-Feat-06 |
| 优先级 | P1 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | Feat-06 承接 design.md 多 Surface 章节 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/01-protocol-core-message-model/design.md` | Baselined |
| 多 Surface 接口 | `genui/src/main/ets/interface/MultiSurfaceController.ets` | — |
| 多 Surface 实现 | `genui/src/main/ets/core/base/MultiSurfaceControllerImpl.ets` | — |
| Surface 管理 | `genui/src/main/cpp/SurfaceManager.cpp` / `SurfaceManager.h` | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 多 Surface 栈行为

**作为** 生成式 UI 宿主开发者,
**我想要** 用栈管理多个 Surface,
**以便** 支持逐层导航返回。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `MultiSurfaceControllerImpl` 构造 THEN `supportsMultipleSurfaces()=true`、`getMaxSurfaceCount()=15`（`MultiSurfaceControllerImpl.ets:41-47`） | 正常 |
| AC-1.2 | WHEN `getSurfaceList()` THEN 返回 native `SurfaceManager::GetSurfaceIds()`（栈序）（`MultiSurfaceControllerImpl.ets:49-51`） | 正常 |
| AC-1.3 | WHEN `getLatestSurfaceId()` THEN 返回 native `GetLatestSurface`（`SurfaceManager.h:59`） | 正常 |

### US-2: pop 与 canPop

**作为** 生成式 UI 宿主开发者,
**我想要** 从栈顶弹出并返回上一个 Surface,
**以便** 实现返回导航。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 栈内 surface 数 > 1 THEN `canPop()` 返回 true（`MultiSurfaceControllerImpl.ets:73-75`） | 正常 |
| AC-2.2 | WHEN 栈内 surface 数 ≤ 1 THEN `canPop()` 返回 false（`MultiSurfaceControllerImpl.ets:73-75`） | 边界 |
| AC-2.3 | WHEN `pop()` 成功 THEN 返回 native pop 结果 code（`MultiSurfaceControllerImpl.ets:77-82,121-151`） | 正常 |
| AC-2.4 | WHEN `pop()` 在控制器已销毁 THEN 返回 `MULTI_SURFACE_EMPTY_STACK`(11003)（`MultiSurfaceControllerImpl.ets:122-126`） | 异常 |
| AC-2.5 | WHEN `pop()` 在 apiSupported=false THEN 返回 `NATIVE_PROCESS_FAILED`(1002)（`MultiSurfaceControllerImpl.ets:127-131`） | 边界 |
| AC-2.6 | WHEN native `popSurface` 返回 undefined THEN 返回 `NATIVE_PROCESS_FAILED`(1002)（`MultiSurfaceControllerImpl.ets:132-137`） | 异常 |

### US-3: 返回手势

**作为** 生成式 UI 宿主开发者,
**我想要** 开关返回手势,
**以便** 控制物理返回键行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `setBackGestureEnabled(true/false)` 且值变化 THEN 更新标志并 `notifyBackGestureEnabledChanged`（`MultiSurfaceControllerImpl.ets:53-67`） | 正常 |
| AC-3.2 | WHEN 设置相同值 THEN no-op（`MultiSurfaceControllerImpl.ets:54-60`） | 边界 |
| AC-3.3 | WHEN 注册/注销监听器 THEN 维护监听器列表，重复注册忽略（`MultiSurfaceControllerImpl.ets:84-106`） | 正常 |

### US-4: 栈所有权与上限

**作为** 生成式 UI 宿主开发者,
**我想要** 栈状态由 native 单源持有,
**以便** ArkTS 转发不产生状态分叉。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN C++ `SurfaceManager::CreateSurface` THEN 追加到 `surfaces_` 与 `surfaceOrder_` 并更新 `latestSurfaceId_`（`SurfaceManager.h:145-147`） | 正常 |
| AC-4.2 | WHEN `SurfaceManager::RemoveSurface`/`Back` THEN 移除并回退（`SurfaceManager.h:44,80`） | 正常 |
| AC-4.3 | WHEN surface 数达到 `MULTI_SURFACE_MAX_COUNT`(=15) 再创建 THEN 触发 `MULTI_SURFACE_MAX_SURFACE_LIMIT_REACHED`(11004)（`SurfaceErrorCodes.h:46`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-6 | ArkTS 单测：栈行为 | `MultiSurfaceControllerImpl.ets:41-51` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 | R-2 | T-6 | ArkTS 单测：pop/canPop | `MultiSurfaceControllerImpl.ets:73-151` |
| AC-3.1,AC-3.2,AC-3.3 | R-3 | T-6 | ArkTS 单测：返回手势 | `MultiSurfaceControllerImpl.ets:53-106` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-6 | C++ UT：栈上限 | `SurfaceManager.h:145-147` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 多 Surface 控制 | 栈由 native 持有，ArkTS 转发 | 上限 15 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | pop/canPop | 栈数>1 可 pop；返回 native code | 销毁/不支持→错误码 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |
| R-3 | 行为 | 返回手势 | 变化才通知，重复注册忽略 | — | AC-3.1,AC-3.2,AC-3.3 |
| R-4 | 边界 | 栈上限 | 达 15 拒绝新 surface | MULTI_SURFACE_MAX_COUNT=15 | AC-4.1,AC-4.2,AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 栈行为 | ArkTS 单测 | 栈转发 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 pop | ArkTS 单测 | 错误码 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 返回手势 | ArkTS 单测 | 监听器 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 栈上限 | C++ UT | 15 上限 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `MultiSurfaceController`（canPop/pop/getSurfaceList/setBackGestureEnabled） | 既有 | 多 Surface 导航 | — | AC-1.1,AC-1.2,AC-1.3,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-3.1,AC-3.2,AC-3.3 |

## 接口规格

### 接口定义

**`MultiSurfaceController.pop()`（`MultiSurfaceController.ets:37`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pop(): SurfaceErrorCode` |
| 返回值 | `SurfaceErrorCode` — 操作状态码 |
| 开放范围 | Public（ArkTS） |
| 错误码 | NO_ERROR / MULTI_SURFACE_EMPTY_STACK(11003) / NATIVE_PROCESS_FAILED(1002) 等 |
| 关联 AC | AC-2.3,AC-2.4,AC-2.5,AC-2.6 |

**`MultiSurfaceController.canPop()`（`MultiSurfaceController.ets:30`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `canPop(): boolean` |
| 返回值 | `boolean` — 栈内 surface 数 > 1 |
| 开放范围 | Public（ArkTS） |
| 关联 AC | AC-2.1,AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enable（返回手势） | boolean | 是 | false | 变化才通知 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 栈数>1 pop | 返回上一个 surface | AC-2.3 |
| 2 | 栈数≤1 pop | 返回 11003 | AC-2.4 |
| 3 | 达 15 上限 | 11004 | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 设备 SDK API 20。
- **API 版本号策略:** 无新增 API。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 栈单源 | native SurfaceManager 持有 | AC-1.1,AC-1.2,AC-1.3,AC-4.1,AC-4.2,AC-4.3 |
| 上限 15 | MULTI_SURFACE_MAX_COUNT | AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | pop 销毁后安全降级 | ArkTS 单测 | `MultiSurfaceControllerImpl.ets:122-126` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | — | ohosTest | — |
| 平板 | 无差异 | — | ohosTest | — |
| 折叠屏 | 无差异 | — | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | — | — |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 是 | 多 Surface 栈导航 | AC-1.1,AC-1.2,AC-1.3 |
| 多用户 | 否 | — | — |
| 版本升级 | 否 | — | — |
| 生态兼容 | 否 | — | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 多 Surface 管理
  作为 生成式 UI 宿主开发者
  我想要 栈管理多个 Surface 并支持返回
  以便 实现分层导航

  Scenario: 返回导航
    Given 栈内 surfaceIds=["main","detail"]
    When 调用 pop()
    Then 移除 "detail"，latestSurfaceId 回到 "main"

  Scenario: 栈空拒绝 pop
    Given 栈内 surfaceIds=["main"]
    When 调用 pop()
    Then 返回 MULTI_SURFACE_EMPTY_STACK(11003)
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（导航容器组件归 07-04-13）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过质量检查

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "MultiSurfaceControllerImpl pop canPop getSurfaceList 返回手势"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceManager surfaces_ surfaceOrder_ latestSurfaceId_ Back CreateSurface"
```

**关键文档：** `genui/src/main/ets/core/base/MultiSurfaceControllerImpl.ets`、`genui/src/main/cpp/SurfaceManager.cpp`、`genui/src/main/ets/interface/MultiSurfaceController.ets`