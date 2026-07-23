# 特性规格

> Func-05-13-01-Feat-02 XComponentController 表面与画布控制：固化 XComponentController 的 surfaceId 获取、Surface 尺寸/矩形/旋转/不透明配置、画布锁定/提交，以及节点 C-API NODE_XCOMPONENT_SURFACE_SIZE/SURFACE_RECT 的 set/get/reset 与错误码行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | XComponentController 表面与画布控制 |
| 特性编号 | Func-05-13-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 8+（ArkTS controller）/ API 15+（节点 C-API） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Controller 方法规格 | 补录 getXComponentSurfaceId、setXComponentSurfaceSize/Rect/Rotation/Config、lockCanvas/unlockCanvasAndPost |
| ADDED | 节点 C-API 表面属性规格 | 补录 NODE_XCOMPONENT_SURFACE_SIZE/SURFACE_RECT 的 set/get/reset 与错误码 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/13-platform-components/01-xcomponent/design.md` | Baselined |

---

## 用户故事

### US-1: 获取与配置表面

**作为** 应用开发者,
**我想要** 通过 XComponentController 获取 surfaceId、设置表面尺寸/矩形/旋转/不透明,
**以便** 精确控制承载表面。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `getXComponentSurfaceId()` 且表面已创建 THEN 返回 surfaceId 字符串（renderSurface 唯一 ID） | 正常 |
| AC-1.2 | WHEN 表面未创建或已销毁或设置了 screenId THEN 返回空字符串 `""` | 边界 |
| AC-1.3 | WHEN 调用 `setXComponentSurfaceSize(w, h)`（NODE_XCOMPONENT_SURFACE_SIZE, 2×u32） THEN 调用 ConfigSurface 配置表面缓冲尺寸 | 正常 |
| AC-1.4 | WHEN `setAttribute(NODE_XCOMPONENT_SURFACE_SIZE, ...)` 参数少于 2 个 THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID(401)` | 异常 |
| AC-1.5 | WHEN `getAttribute(NODE_XCOMPONENT_SURFACE_SIZE)` THEN 返回 drawSize 宽高（pattern null 时默认 0） | 正常 |
| AC-1.6 | WHEN `resetAttribute(NODE_XCOMPONENT_SURFACE_SIZE)` THEN 重置为 (0, 0) | 正常 |
| AC-1.7 | WHEN 调用 `setXComponentSurfaceRect(offsetX, offsetY, w, h)`（4×i32）且 w>0 且 h>0 THEN 设置理想偏移与尺寸并触发 UpdateSurfaceRect | 正常 |
| AC-1.8 | WHEN `setXComponentSurfaceRect` 的 w<=0 或 h<=0 THEN 提前返回 no-op（不修改） | 边界 |
| AC-1.9 | WHEN `setAttribute(NODE_XCOMPONENT_SURFACE_RECT, ...)` 参数少于 4 个 THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID(401)` | 异常 |
| AC-1.10 | WHEN `resetAttribute(NODE_XCOMPONENT_SURFACE_RECT)` THEN 偏移重置为 (0,0)，尺寸重置为节点自身宽高 | 正常 |
| AC-1.11 | WHEN 调用 `setXComponentSurfaceRotation(lock)` 且 type=SURFACE THEN 设置 surface 旋转锁；type≠SURFACE 时无效 | 正常 |
| AC-1.12 | WHEN 调用 `setXComponentSurfaceConfig(isOpaque)` THEN 对 SURFACE 设 renderContext 不透明、对 TEXTURE 设 surface 不透明；COMPONENT/NODE 无效 | 正常 |

### US-2: 画布锁定与提交（TEXTURE 模式）

**作为** 应用开发者,
**我想要** 通过 lockCanvas/unlockCanvasAndPost 在 TEXTURE 模式下直接绘制,
**以便** 自定义纹理内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `lockCanvas()` 且 nativeWindow 存在 THEN 返回 RSCanvas；nativeWindow 为 null 时返回 null | 正常 |
| AC-2.2 | WHEN 调用 `unlockCanvasAndPost(canvas)` 且 canvas/nativeWindow 非空 THEN 提交绘制并释放 | 正常 |
| AC-2.3 | WHEN `unlockCanvasAndPost` 的 canvas 或 nativeWindow 为 null THEN 静默 no-op | 异常 |

### US-3: 获取表面矩形

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `getXComponentSurfaceRect()` THEN 返回 {offsetX, offsetY, surfaceWidth, surfaceHeight}（pattern null 时全 0） | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.12 | R-1~R-8 | 已有实现 | 代码评审 + C-API 单测 | `xcomponent_controller_accessor.cpp`, `style_modifier.cpp:9786-9850` |
| AC-2.1~2.3 | R-9, R-10 | 已有实现 | 代码评审 | `xcomponent_pattern.cpp:2684-2703` |
| AC-3.1 | R-1 | 已有实现 | 代码评审 | `style_modifier.cpp:9829-9844` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | getXComponentSurfaceId | 返回 surfaceId（renderSurface 唯一 ID）；未创建/已销毁/有 screenId 时返回 "" | — | AC-1.1, AC-1.2 |
| R-2 | 行为 | setXComponentSurfaceSize(w,h) / NODE_XCOMPONENT_SURFACE_SIZE(2×u32) | ConfigSurface 配置缓冲尺寸 | get 返回 drawSize；reset→(0,0) | AC-1.3~1.6 |
| R-3 | 异常 | NODE_XCOMPONENT_SURFACE_SIZE 参数<2 | 返回 ARKUI_ERROR_CODE_PARAM_INVALID(401) | — | AC-1.4 |
| R-4 | 行为 | setXComponentSurfaceRect(x,y,w,h) 且 w>0,h>0 | 设理想偏移+尺寸，触发 UpdateSurfaceRect；缺省偏移居中 | — | AC-1.7 |
| R-5 | 边界 | setXComponentSurfaceRect w<=0 或 h<=0 | 提前返回 no-op | — | AC-1.8 |
| R-6 | 异常 | NODE_XCOMPONENT_SURFACE_RECT 参数<4 | 返回 401 | — | AC-1.9 |
| R-7 | 行为 | resetAttribute(NODE_XCOMPONENT_SURFACE_RECT) | 偏移→(0,0)，尺寸→节点自身宽高 | 非硬 0,0 | AC-1.10 |
| R-8 | 行为 | setXComponentSurfaceRotation(lock) / setXComponentSurfaceConfig(isOpaque) | 旋转仅 SURFACE；不透明对 SURFACE 设 renderContext、TEXTURE 设 surface；COMPONENT/NODE 无效 | 默认 isOpaque=false,isSurfaceLock=false | AC-1.11, AC-1.12 |
| R-9 | 行为 | lockCanvas() 且 nativeWindow 存在 | 返回 RSCanvas；nativeWindow null 返回 null | — | AC-2.1 |
| R-10 | 行为 | unlockCanvasAndPost(canvas) | 提交并释放；canvas/nativeWindow null 时 no-op | — | AC-2.2, AC-2.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.6, R-1~R-3 | C-API 单测 + 代码评审 | surfaceId 获取、SurfaceSize set/get/reset 与错误码 |
| VM-2 | AC-1.7~1.10, R-4~R-7 | C-API 单测 | SurfaceRect set/get/reset、w/h<=0 no-op、参数校验 |
| VM-3 | AC-1.11~1.12, R-8 | 代码评审 | 旋转/不透明按类型生效 |
| VM-4 | AC-2.1~2.3, R-9~R-10 | 代码评审 | lockCanvas/unlockCanvasAndPost |

---

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `getXComponentSurfaceId()` | Public | 无 | string | N/A | 获取 surfaceId | AC-1.1 |
| `setXComponentSurfaceSize(w,h)` | Public | u32,u32 | void | N/A | 设置表面尺寸 | AC-1.3 |
| `setAttribute(NODE_XCOMPONENT_SURFACE_SIZE)` | Public（NDK @since 15） | 2×u32 | ArkUI_ErrorCode | 401 | 节点 C-API 设尺寸 | AC-1.3 |
| `setAttribute(NODE_XCOMPONENT_SURFACE_RECT)` | Public（NDK @since 15） | 4×i32 | ArkUI_ErrorCode | 401 | 节点 C-API 设矩形 | AC-1.7 |

### 变更/废弃 API

无。

---

## 接口规格

### 接口定义

**setAttribute(NODE_XCOMPONENT_SURFACE_SIZE, item)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode setAttribute(node, NODE_XCOMPONENT_SURFACE_SIZE, {value[0].u32, value[1].u32})` |
| 返回值 | ArkUI_ErrorCode — 0=SUCCESS |
| 开放范围 | Public（节点 C-API） |
| 错误码 | ARKUI_ERROR_CODE_PARAM_INVALID(401) |
| 关联 AC | AC-1.3, AC-1.4 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 提供 2×u32 | ConfigSurface，返回 0 | AC-1.3 |
| 2 | 参数<2 或 null | 返回 401 | AC-1.4 |
| 3 | reset | 重置为 (0,0) | AC-1.6 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** ArkTS controller @since 8；节点 C-API NODE_XCOMPONENT_SURFACE_SIZE/RECT @since 15（RECT 另标 @since 18）
- **API 版本号策略:** ArkTS 公开；节点 C-API since 15+

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SurfaceRect 的 w/h<=0 为 no-op | 防止零尺寸表面 | AC-1.8 |
| SurfaceRect reset 尺寸取节点宽高 | 非硬 0,0，保持节点尺寸 | AC-1.10 |
| 旋转仅 SURFACE | type 守卫 | AC-1.11 |
| 不透明配置按类型分流 | SURFACE→renderContext，TEXTURE→surface | AC-1.12 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | surfaceId/Rect 可经 Controller 单测验证 | 单测 | `xcomponent_controller_accessor.cpp` |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | 集成测试 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 多窗口/分屏 | 是 | 表面矩形需响应窗口变化 | AC-1.7 |
| 其余 | 否 | — | — |

---

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC 使用 WHEN/THEN
- [x] 范围边界明确（不涉及输入事件/HDR/analyzer，属其它 Feat）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "XComponentController surfaceId/size/rect/rotation/config 与 lockCanvas 实现链路"
  - repo: "openharmony/ace_engine"
    query: "NODE_XCOMPONENT_SURFACE_SIZE/SURFACE_RECT set/get/reset 错误码"
```

**关键文档：** `xcomponent_controller_ng.cpp`、`inner_xcomponent_controller.h`、`style_modifier.cpp:9786-9850`
