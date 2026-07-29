# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Scroll 分页与吸附对齐 |
| 特性编号 | Func-05-03-07-Feat-06 |
| 优先级 | P2 |
| 目标版本 | API 10 ~ 11+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 scrollSnap(ScrollSnapOptions)/enablePaging/ScrollSnapOptions/ScrollSnapAlign 及 C-API。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/07-scroll/design.md` |
| SDK Dynamic | `ets/dynamic/component/scroll.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/scroll/scroll_pattern.cpp` |
| Native Header | `interfaces/native/native_node.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 吸附点对齐

作为**应用开发者**，我想要**用 scrollSnap 配置吸附点对齐**，以便**滚动停在指定点**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `scrollSnap({snapAlign, snapPagination, enableSnapToStart, enableSnapToEnd})`（@since 10/11） THEN 按对齐与分页计算吸附点 | 正常 |
| AC-1.2 | WHEN snapAlign=START THEN 滚动停在分页起始边界 | 正常 |
| AC-1.3 | WHEN snapAlign=CENTER THEN 滚动停在分页中心 | 正常 |
| AC-1.4 | WHEN snapAlign=END THEN 滚动停在分页末边界 | 正常 |
| AC-1.5 | WHEN snapAlign=NONE THEN 不吸附 | 边界 |
| AC-1.6 | WHEN snapPagination 为 interval THEN `CaleSnapOffsetsByInterval` 生成分页间隔吸附点 | 正常 |
| AC-1.7 | WHEN snapPagination 为具体数组 THEN `CaleSnapOffsetsByPaginations` 按数组吸附 | 正常 |
| AC-1.8 | WHEN enableSnapToStart=false THEN 不强制吸附到起始 | 边界 |
| AC-1.9 | WHEN enableSnapToEnd=false THEN 不强制吸附到末端 | 边界 |
| AC-1.10 | WHEN 滚动停止 THEN `StartSnapAnimation`/`StartScrollSnapAnimation` 触发吸附动画 | 正常 |

### US-2: 分页模式

作为**应用开发者**，我想要**用 enablePaging 启用整页滚动**，以便**类似翻页体验**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `enablePaging(true)`（@since 11） THEN 启用分页，每次滚动一页 | 正常 |
| AC-2.2 | WHEN enablePaging=false（默认） THEN 自由滚动不强制分页 | 边界 |
| AC-2.3 | WHEN 分页模式与 snap 共存 THEN `ScrollPageCheck`/`GetPagingOffset`/`GetPagingDelta` 协调 | 正常 |
| AC-2.4 | WHEN C-API `NODE_SCROLL_SNAP/ENABLE_PAGING/PAGE` THEN 经 node_modifier 写 snap 字段 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-6 | 单元测试：scrollSnap | `scroll.d.ts:1983` |
| AC-1.2 | R-2 | TASK-SKELETON-6 | 单元测试：START | `scroll_pattern.cpp` |
| AC-1.3 | R-2 | TASK-SKELETON-6 | 单元测试：CENTER | `scroll_pattern.cpp` |
| AC-1.4 | R-2 | TASK-SKELETON-6 | 单元测试：END | `scroll_pattern.cpp` |
| AC-1.5 | R-2 | TASK-SKELETON-6 | 单元测试：NONE | `scroll_pattern.cpp` |
| AC-1.6 | R-3 | TASK-SKELETON-6 | 单元测试：interval | `scroll_pattern.cpp` CaleSnapOffsetsByInterval |
| AC-1.7 | R-3 | TASK-SKELETON-6 | 单元测试：数组 | `scroll_pattern.cpp` CaleSnapOffsetsByPaginations |
| AC-1.8 | R-4 | TASK-SKELETON-6 | 单元测试：enableSnapToStart | `scroll.d.ts:1084` |
| AC-1.9 | R-4 | TASK-SKELETON-6 | 单元测试：enableSnapToEnd | `scroll.d.ts:1084` |
| AC-1.10 | R-5 | TASK-SKELETON-6 | 单元测试：吸附动画 | `scroll_pattern.cpp` StartSnapAnimation |
| AC-2.1 | R-6 | TASK-SKELETON-6 | 单元测试：enablePaging | `scroll.d.ts:2006` |
| AC-2.2 | R-6 | TASK-SKELETON-6 | 单元测试：默认 false | `scroll.d.ts:2006` |
| AC-2.3 | R-7 | TASK-SKELETON-6 | 单元测试：共存协调 | `scroll_pattern.cpp` ScrollPageCheck |
| AC-2.4 | R-8 | TASK-SKELETON-6 | 单元测试：C-API | `node_scroll_modifier.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | scrollSnap(ScrollSnapOptions) | 按对齐与分页计算吸附点 | @since 10/11 | AC-1.1 |
| R-2 | 行为 | snapAlign=START/CENTER/END/NONE | 对应边界吸附/不吸附 | — | AC-1.2~1.5 |
| R-3 | 行为 | snapPagination interval/数组 | CaleSnapOffsetsByInterval/Paginations | — | AC-1.6, AC-1.7 |
| R-4 | 边界 | enableSnapToStart/End=false | 不强制吸附首尾 | — | AC-1.8, AC-1.9 |
| R-5 | 行为 | 滚动停止 | StartSnapAnimation/StartScrollSnapAnimation | 吸附动画 | AC-1.10 |
| R-6 | 行为 | enablePaging(true/false) | 整页滚动/自由滚动 | @since 11，默认 false | AC-2.1, AC-2.2 |
| R-7 | 行为 | paging 与 snap 共存 | ScrollPageCheck/GetPagingOffset/GetPagingDelta 协调 | — | AC-2.3 |
| R-8 | 行为 | C-API NODE_SCROLL_SNAP/ENABLE_PAGING/PAGE | node_modifier 写 snap 字段 | — | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-5 吸附 | 单元测试 | align/pagination/动画 |
| VM-2 | R-6~R-8 分页与 C-API | 单元测试 | enablePaging/共存/C-API |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `scrollSnap(value)` | Public（@since 10/11） | `ScrollSnapOptions` | `ScrollAttribute` | 无 | 吸附对齐 | AC-1.1~1.10 |
| `enablePaging(value)` | Public（@since 11） | `boolean` | `ScrollAttribute` | 无 | 整页滚动 | AC-2.1, AC-2.2 |
| C-API `NODE_SCROLL_SNAP/ENABLE_PAGING/PAGE` | Public | 属性枚举 | — | 无 | NDK 通道 | AC-2.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无废弃 | — |

## 接口规格

### 接口定义

**scrollSnap(value: ScrollSnapOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ScrollAttribute::scrollSnap(value: ScrollSnapOptions): ScrollAttribute` |
| 返回值 | `ScrollAttribute` |
| 开放范围 | Public（@since 10/11） |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.snapAlign | `ScrollSnapAlign` | 是 | NONE | START/CENTER/END/NONE |
| value.snapPagination | `number\|Array<number>` | 否 | — | interval 或具体数组 |
| value.enableSnapToStart | `boolean` | 否 | true | 是否强制吸附起始 |
| value.enableSnapToEnd | `boolean` | 否 | true | 是否强制吸附末端 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | snapAlign START/CENTER/END | 对应吸附 | AC-1.2~1.4 |
| 2 | snapPagination interval | 间隔吸附点 | AC-1.6 |
| 3 | snapPagination 数组 | 数组吸附点 | AC-1.7 |
| 4 | enableSnapToStart/End false | 不强制首尾 | AC-1.8, AC-1.9 |
| 5 | 滚动停止 | 吸附动画 | AC-1.10 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** scrollSnap @10/11；enablePaging @11
- **API 版本号策略:** 各属性标注 @since

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| snap 与 paging 协调 | ScrollPageCheck/GetPagingOffset | AC-2.3 |
| 吸附动画 | StartSnapAnimation | AC-1.10 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 吸附动画单帧 | 单元测试 | `scroll_pattern.cpp` |
| 可测试性 | snap/paging 可单测 | 单元测试 | TASK-SKELETON-6 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 无差异 | — |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | scrollSnap @10/11；enablePaging @11 | AC-1.x~2.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（分页吸附；缩放在 Feat-07）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollPattern CaleSnapOffsets/ByInterval/ByPaginations 与 StartScrollSnapAnimation 吸附动画"
```

**关键文档:** `scroll.d.ts`、`scroll_pattern.cpp`、`design.md`
