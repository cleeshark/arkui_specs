# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 动画桥接适配 |
| 特性编号 | Func-02-02-01-Feat-03 |
| 所属 Epic | 跨平台适配层 |
| 优先级 | P1 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单 |

## 本次变更范围（Delta）

> 全新特性补录，无存量变更。本节跳过。

## 输入文档

- 源码路径：`frameworks/core/animation/` + `frameworks/core/animation/rosen_animation_utils.cpp` + `frameworks/core/animation/fake_animation_utils.cpp`
- 设计文档：`02-cross-platform/02-render-backend-adapter/01-rosen-render-backend-adapter/design.md`

## 用户故事

### US-1: AnimationUtils 编译时双实现选择

作为一个 ACE 引擎开发者，我希望 AnimationUtils 通过编译宏选择 rosen_animation_utils（真实实现）或 fake_animation_utils（空操作 stub），使 NG 动画层能在有无 Rosen 后端时分别正常编译链接。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN ENABLE_ROSEN_BACKEND 定义 THEN AnimationUtils 使用 rosen_animation_utils.cpp 提供的真实实现 | 正常 |
| AC-1.2 | WHEN #ifndef ENABLE_ROSEN_BACKEND THEN AnimationUtils 使用 fake_animation_utils.cpp 提供的空操作 stub | 边界 |
| AC-1.3 | WHEN 无后端可用 THEN AnimationUtils::CloseImplicitAnimation 返回 false | 边界 |
| AC-1.4 | WHEN 无后端可用 THEN AnimationUtils::StartAnimation 返回 nullptr | 边界 |
| AC-1.5 | WHEN Rosen 后端可用 THEN CloseImplicitAnimation 调用 RS 层 ImplicitAnimationClose | 正常 |
| AC-1.6 | WHEN Rosen 后端可用 THEN StartAnimation 创建 RSAnimation 并返回控制指针 | 正常 |

### US-2: AnimationUtils 核心方法适配

作为一个 ACE 引擎开发者，我希望 AnimationUtils 的 Open/CloseImplicitAnimation、StartAnimation、Animate/AnimateWithCurrentOptions/AnimateWithCurrentCallback 等核心方法（源码方法名；对外概念名分别为 AnimateTo/AnimateToWithCurrent）在 Rosen 后端下适配为 RS 层的对应 API，使 NG 动画指令能映射到 RS 动画管线。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN OpenImplicitAnimation(node) THEN 通过 RS 层 ImplicitAnimationOpen 开启隐式动画 | 正常 |
| AC-2.2 | WHEN CloseImplicitAnimation(node) THEN 通过 RS 层 ImplicitAnimationClose 关闭隐式动画 | 正常 |
| AC-2.3 | WHEN StartAnimation(option) THEN 创建 RSAnimation、设置参数、返回 Animation<> 控制 | 正常 |
| AC-2.4 | WHEN Animate(option, finishCallback) THEN 启动动画并注册 finishCallback（源码方法名 Animate；对外概念名 AnimateTo） | 正常 |
| AC-2.5 | WHEN AnimateWithCurrentOptions(option, finishCallback) THEN 以当前值作为起点启动动画（源码方法名 AnimateWithCurrentOptions；对外概念名 AnimateToWithCurrent） | 正常 |
| AC-2.6 | WHEN AnimateWithCurrentCallback(option, finishCallback) THEN 以当前值起点 + 回调启动动画（源码方法名 AnimateWithCurrentCallback；无对应对外概念名） | 正常 |
| AC-2.7 | WHEN AnimateFrom(option, finishCallback) THEN 从指定值启动动画 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1~6 | TASK-F03-01 | 编译检查 | rosen_animation_utils.cpp, fake_animation_utils.cpp |
| AC-2.1~2.7 | R-7~13 | TASK-F03-02 | 单测 | animation_utils.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ENABLE_ROSEN_BACKEND 定义 | 使用 rosen_animation_utils 真实实现 | 编译时选择 | AC-1.1 |
| R-2 | 边界 | #ifndef ENABLE_ROSEN_BACKEND | 使用 fake_animation_utils 空操作 | stub 层 | AC-1.2 |
| R-3 | 边界 | 无后端可用 | CloseImplicitAnimation 返回 false | 无隐式动画能力 | AC-1.3 |
| R-4 | 边界 | 无后端可用 | StartAnimation 返回 nullptr | 无动画创建能力 | AC-1.4 |
| R-5 | 行为 | Rosen 后端 CloseImplicitAnimation | 调用 RS ImplicitAnimationClose | RS 层 API | AC-1.5 |
| R-6 | 行为 | Rosen 后端 StartAnimation | 创建 RSAnimation 并返回指针 | Animation<> 控制 | AC-1.6 |
| R-7 | 行为 | OpenImplicitAnimation | 通过 RS ImplicitAnimationOpen 开启 | RS 层 API | AC-2.1 |
| R-8 | 行为 | CloseImplicitAnimation(node) | 通过 RS ImplicitAnimationClose 关闭 | RS 层 API | AC-2.2 |
| R-9 | 行为 | StartAnimation(option) | 创建 RSAnimation + 设置参数 | Animation<> 返回 | AC-2.3 |
| R-10 | 行为 | Animate | 启动动画 + finishCallback | 源码方法名；对外概念名 AnimateTo | AC-2.4 |
| R-11 | 行为 | AnimateWithCurrentOptions | 当前值起点 + finishCallback | 源码方法名；对外概念名 AnimateToWithCurrent | AC-2.5 |
| R-12 | 行为 | AnimateWithCurrentCallback | 当前值起点 + 回调 | 源码方法名；无对应对外概念名 | AC-2.6 |
| R-13 | 行为 | AnimateFrom | 从指定值启动 + finishCallback | 动画指令 | AC-2.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.6 编译时双实现 | 编译检查 | 宏选择、空操作 fallback |
| VM-2 | AC-2.1~2.7 核心方法适配 | 单测 | RS 层 API 映射、finishCallback 注册、Animate 三方法源码名 vs 对外概念名 |

## API 变更分析

N/A，框架内部适配层，无 SDK API 变更。

## 接口规格

N/A，简单复杂度，框架内部动画桥接层，无新增接口规格。

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** InnerApi

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 编译时双实现 | rosen/fake_animation_utils 通过宏编译时选择 | AC-1.1~1.4 |
| 空操作 Stub | fake_animation_utils 所有方法为空操作，无后端时链接不失败 | AC-1.3~1.4 |
| RS 层映射 | Rosen 实现将 NG AnimationUtils 指令映射到 RS Animation API | AC-2.1~2.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | AnimationUtils::StartAnimation ≤1ms | 单测计时 | rosen_animation_utils.cpp |
| 可测试性 | fake_animation_utils 可在 ACE_UNITTEST 下替代真实实现 | 单测覆盖率 | UT 报告 |

## 多设备适配声明

无差异。所有设备类型使用相同的动画桥接适配代码。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 适配层不直接影响 | N/A |
| 大字体 | 否 | 适配层不直接影响 | N/A |
| 深色模式 | 否 | 适配层不直接影响 | N/A |
| 多窗口/分屏 | 否 | 适配层不直接影响 | N/A |
| 版本升级 | 否 | 适配层内部变更 | N/A |
| 生态兼容 | 是 | CROSS_PLATFORM 编译控制动画适配层选择 | AC-1.1 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "AnimationUtils 编译时双实现选择 rosen_animation_utils / fake_animation_utils 机制"
  - repo: "openharmony/ace_engine"
    query: "AnimationUtils 核心方法 Open/CloseImplicitAnimation, StartAnimation, Animate（对外概念名 AnimateTo）的 RS 层映射"
```

**关键文档：** ace_engine `frameworks/core/animation/`
