# 生成式 UI（GenUI / A2UI）规格子树说明

> **独立仓声明**：本域（07-04 生成式 UI）归 GenUI 独立前端部件仓
> （`GenerativeUI/A2UIRender`、`GenerativeUI/Docs` 等），**非 ArkUI
> `ace_engine` 主仓库**。规格落点至本 ArkUI Specs 仓仅为全域归档，
> 实现与契约以 GenUI 独立仓为准。

本目录承载「07-04 生成式 UI」功能域的长期规格（每个 L3 功能域一份 `design.md` + 若干 `Feat-NN-*.md`）。

GenUI 是基于 OpenHarmony ArkUI 的 A2UI（Agent-to-UI）渲染框架，实现分布在多个独立仓：

| 仓 | 职责 |
|---|---|
| `GenerativeUI/Docs` | 开发者文档（概念 / 指南 / API 参考） |
| `GenerativeUI/genui_protocol_analysis` | 协议规范（spec / JSON Schema / EBNF）+ LLM 亲和性评估 + GAP 治理 |
| `GenerativeUI/A2UIRender` | 全量渲染引擎 `@arkui-genius/genui`（ArkTS + C++ `liba2ui_native.so`） |
| `GenerativeUI/genui_form` | Form 卡片渲染（裁剪协议，服务 / 桌面卡片） |

## 协议分层

```
A2UI 原生协议 v0.9（Google 标准，平台无关）
  └── 鸿蒙 A2UI 扩展协议（全量，catalogId = ohos.a2ui.extended.catalog）
        └── Form 卡片协议（裁剪，catalogId = ohos.a2ui.extended.catalog.form）
```

## 元约定（本子树所有 spec / design 遵循）

1. **spec = 契约，不写实现**：`Feat-NN-*.md` 只呈现可验收的行为契约（AC / 规则 / API 契约 / 兼容 / 验证映射），不写内部实现流程；实现与架构归 `design.md`（涉及仓和模块 / 调用链层级 / ADR / 数据模型）。

2. **基准实现声明**：共享契约域以 A2UIRender 全量为基准实现，genui_form 为裁剪变体。

3. **协议 spec 优先于任一仓实现**：实现分叉时以 genui_protocol_analysis 的 spec / schema / EBNF 为准，偏差记入 spec 的兼容 / 风险表。

4. **裁剪差异显式化 + 扩展域只写差异**：`07-04-25 生成式卡片`、`07-04-27 扩展域-1`、`07-04-28 扩展域-2` 等扩展域只承载独有 / 裁剪差异；重叠的组件 / 样式 / 表达式语义引用外域 Feat，不在扩展域内重复书写。

## 补录注意

- FuncID 按「行为 / 契约」切分，实现差异归 design + 风险表，不因两仓实现不同而拆域。
- 组件 / 函数域一成员一 Feat；能力域按行为契约划分。
- 跨平台 android / ios（ArkUI-X）不在本 ArkUI specs 覆盖范围内，标 N/A。
