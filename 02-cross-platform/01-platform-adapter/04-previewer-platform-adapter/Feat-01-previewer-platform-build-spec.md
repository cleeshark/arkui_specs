# 特性规格

> Func-02-01-04-Feat-01 预览器平台发现与构建配置存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 预览器平台发现与构建配置 |
| 特性编号 | Func-02-01-04-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 当前桌面 preview adapter |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 平台发现 | Windows/Linux/macOS 的 OS/CPU 条件 |
| ADDED | 公共配置 | preview feature flags、依赖和宏 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `02-cross-platform/01-platform-adapter/04-previewer-platform-adapter/design.md` | 已核对 |
| Platform | `adapter/preview/build/config.gni`、`platform.gni` | 已核对 |
| Common config | `adapter/preview/build/preview_common.gni` | 已核对 |

## 用户故事

### US-1: 选择受支持的预览平台

**作为** 预览器构建维护者
**我想要** 按宿主 OS 和 CPU 注册预览目标
**以便** 不为未支持的组合生成错误的预览构建图

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 目标为 mingw_x86_64 THEN 注册 windows preview platform | 正常 |
| AC-1.2 | WHEN 目标为 linux_x64/linux_arm64 或 mac_x64/mac_arm64 THEN 分别注册 linux 或 mac preview platform | 正常 |
| AC-1.3 | WHEN OS/CPU 不匹配上述组合 THEN 不向 `platforms` 追加 preview 平台 | 边界 |

### US-2: 应用预览构建特征配置

**作为** 预览器构建维护者
**我想要** 使用固定的公共 feature 开关和平台依赖
**以便** 预览运行时只包含当前支持的能力集合

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 导入 preview common config THEN 启用 preview、Rosen、Inspector 事件上报和自动填充控制对应宏 | 正常 |
| AC-2.2 | WHEN 使用默认 preview config THEN Web、Video、Plugin、远程窗口等关闭能力不生成对应支持宏 | 边界 |
| AC-2.3 | WHEN 入口 target 构建 THEN 依赖 entrance、external、inspector 和 osal 四个 preview source set | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1~AC-1.3 | R-1~R-3 | 已有实现 | GN args 矩阵 | `config.gni:15-26`; `platform.gni:17-43` |
| AC-2.1~AC-2.3 | R-4~R-6 | 已有实现 | GN target 审查 | `preview_common.gni:16-55,121-124` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | mingw_x86_64 | 追加 windows platform | 仅该 Windows 组合 | AC-1.1 |
| R-2 | 行为 | 受支持 Linux/mac 组合 | 追加对应 platform | CPU 组合必须匹配 | AC-1.2 |
| R-3 | 边界 | 非支持组合 | platforms 保持不含该预览 target | 不推断通用桌面支持 | AC-1.3 |
| R-4 | 行为 | preview common 生效 | 定义 PREVIEW、Rosen、Inspector 等宏 | 以现有默认值为准 | AC-2.1 |
| R-5 | 边界 | 默认关闭功能 | 不定义对应支持宏 | 不把宿主能力带入预览 | AC-2.2 |
| R-6 | 行为 | platform deps 解析 | 聚合四个 preview source set | target 名称固定 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.3 | GN args 矩阵 | OS/CPU 平台发现 |
| VM-2 | AC-2.1~AC-2.3 | target graph 审查 | flags、宏与依赖 |

## API 变更分析

### 新增 API

N/A；内部构建配置，不新增公开 API。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

N/A；本 Feat 的接口为 GN 平台描述与内部构建变量。

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 当前 preview adapter 的受支持 OS/CPU 组合。
- **API 版本号策略:** N/A。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| OS/CPU 精确匹配 | 平台注册不能只按 OS 判断 | AC-1.1~AC-1.3 |
| feature 定界 | 默认关闭能力不得被文档宣称支持 | AC-2.1, AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可构建性 | 受支持组合产生确定 target 图 | GN check | platform.gni |
| 可定位性 | flags 和 deps 位于公共配置 | 源码审查 | preview_common.gni |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| Windows 桌面 | mingw x86_64 | windows config | GN check | config_windows.gni |
| Linux 桌面 | x64/arm64 | linux config | GN check | config_linux.gni |
| macOS 桌面 | x64/arm64 | mac config | GN check | config_mac.gni |

## 全局特性影响

| 特性 | 是否适用 | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | feature flags 需随构建配置回归 | VM-2 |
| 生态兼容 | 是 | 不扩展未注册 OS/CPU | VM-1 |

## 行为场景（可选，Gherkin）

内部构建矩阵已由接口规格和 AC 覆盖。

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 平台组合和 feature 边界明确
- [x] AC、规则与 VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "adapter preview platform.gni preview_common.gni"
```

**关键文档：** `adapter/preview/build/platform.gni`
