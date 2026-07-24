# 特性规格

> Func-05-14-02-Feat-06 Canvas 图像与像素交换存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Canvas 图像与像素交换 |
| 特性编号 | Func-05-14-02-Feat-06 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性覆盖 ImageBitmap、PixelMap、ImageData 与 Canvas 像素之间的输入、裁剪、缩放、读取、写入、数据 URL 导出和 PixelMap 转移规则，并记录 API 18 的 PixelMap 源区单位分界与资源/Builder 构造演进。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 图像输入 | ImageBitmap/PixelMap、三种 drawImage 重载 |
| ADDED | 像素读写 | create/get/putImageData、setPixelMap、transferFromImageBitmap |
| ADDED | 导出与构造 | toDataURL、ImageBitmap Resource/Builder 版本 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/02-canvas/design.md` | 并行补录 |
| SDK | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:1013-1278,1498-1597,1931-2046,2835-3007` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp` | 已核对 |
| Tests | `test/unittest/core/pattern/canvas/` | 已核对 |

## 用户故事

### US-1: 将图像绘制到 Canvas

**作为** 图形应用开发者  
**我想要** 绘制整图或裁剪缩放后的图像  
**以便** 合成位图内容

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN drawImage 接收有效 ImageBitmap/PixelMap 与目标坐标 THEN 将整图按当前状态绘制到目标位置 | 正常 |
| AC-1.2 | WHEN 提供目标宽高或完整源区/目标区参数 THEN 按指定区域裁剪并缩放到目标矩形 | 正常 |
| AC-1.3 | WHEN 图像为空、已失效，坐标含 NaN/Infinity，或尺寸非法 THEN 当前绘制无输出且不影响后续合法命令 | 异常 |
| AC-1.4 | WHEN image 为 PixelMap 且使用九参数 drawImage THEN 源区单位在 API 18 前为 px、API 18 起为 vp；ImageBitmap 维持 SDK 规定单位 | 边界 |

### US-2: 在字节像素与表面间交换

**作为** 图像处理开发者  
**我想要** 读取、构造、写回和导出像素  
**以便** 实现滤镜与跨组件交换

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN createImageData/getImageData 接收合法矩形 THEN 返回具有匹配宽高和 RGBA 数据长度的 ImageData，getImageData 读取当前表面像素 | 正常 |
| AC-2.2 | WHEN putImageData 提供有效 ImageData 与可选脏矩形 THEN 将相应原始像素写入目标区域，不套用当前变换、透明度或阴影 | 正常 |
| AC-2.3 | WHEN toDataURL 指定 png/jpeg/webp 与 [0,1] 质量 THEN 导出当前 Canvas 图像；WHEN 类型无效或 quality 越界、NaN、Infinity THEN SDK 契约使用默认 png/0.92；当前 Dynamic 实现仅重置越界和 Infinity，NaN 会穿透到 encoder，属于实现偏差 | 边界 |
| AC-2.4 | WHEN setPixelMap/transferFromImageBitmap 使用有效源 THEN 更新画布像素；源失效时安全无输出且所有权/对象状态按接口约定处理 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | drawImage 参数化 UT | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:1498-1597`; `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp:226-727` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | ImageData/PixelMap UT；导出特殊值审查/待补 UT | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:1931-2046,2835-3007`; `frameworks/bridge/declarative_frontend/jsview/canvas/js_canvas_renderer.cpp:1042-1048`; `frameworks/core/components_ng/pattern/canvas/custom_paint_util.cpp:31-41` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 有效源+目标点 | 绘制整图 | 当前状态生效 | AC-1.1 |
| R-2 | 行为 | 缩放/裁剪重载 | 映射源矩形到目标矩形 | 尺寸按 SDK 归一 | AC-1.2 |
| R-3 | 异常 | 失效源/非有限参数 | 不输出当前图像 | 后续命令可继续 | AC-1.3 |
| R-4 | 边界 | PixelMap 九参数源区 | API<18 px，API>=18 vp | ImageBitmap 独立 | AC-1.4 |
| R-5 | 行为 | create/getImageData | 返回匹配 RGBA 缓冲 | 越界区按实现处理 | AC-2.1 |
| R-6 | 行为 | putImageData | 原始像素写回 | 不消费绘制状态 | AC-2.2 |
| R-7 | 行为 | toDataURL | 按 SDK 对非法质量使用 0.92；当前 Dynamic NaN 未重置 | 格式默认 png | AC-2.3 |
| R-8 | 恢复 | set/transfer 源失效 | 安全跳过 | 不悬挂访问 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.3 | 图像裁剪缩放金图 UT | 三种重载和非法值 |
| VM-2 | AC-1.4 | API 17/18 单位对照 UT | PixelMap 源区坐标 |
| VM-3 | AC-2.1~AC-2.2 | RGBA 往返测试 | 缓冲长度、脏矩形、状态隔离 |
| VM-4 | AC-2.3~AC-2.4 | 源码审查+待补编码/PixelMap 生命周期 UT | NaN/Infinity/越界质量、Dynamic 偏差与失效源；现有相关 accessor/toDataURL 用例有禁用覆盖 |

## API 变更分析

### 新增 API

N/A；ImageBitmap、ImageData、PixelMap 和导出均为已有接口。

### 变更/废弃 API

N/A；API 18 单位差异是存量兼容分支，不在本次改变。

## 接口规格

### 接口定义

| 接口组 | 代表签名 | 约束 | 关联 AC |
|--------|----------|------|---------|
| 图像绘制 | `drawImage(image, dx, dy[, dw, dh])`; 九参数重载 | 源有效、参数有限 | AC-1.1~AC-1.4 |
| 像素缓冲 | `createImageData/getImageData/putImageData` | RGBA 缓冲 | AC-2.1~AC-2.2 |
| 表面交换 | `setPixelMap`; `transferFromImageBitmap` | 有效像素源 | AC-2.4 |
| 导出 | `toDataURL(type?, quality?)` | png/jpeg/webp；SDK 非法质量默认 0.92，当前 Dynamic NaN 例外 | AC-2.3 |

## 兼容性声明

- **最低支持版本:** API 8。
- **行为分界:** PixelMap 九参数 drawImage 源区单位于 API 18 从 px 变为 vp。
- **已知偏差:** Dynamic toDataURL 的 NaN quality 未按 SDK 回退 0.92，会继续传给 encoder；Infinity 会回退。
- **版本节点:** ImageBitmap Resource/Builder 构造 API 26；其余新增类型按 SDK since 门控。
- **数据格式:** ImageData 为 RGBA；data URL 编码格式不在本次改变。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 资源生命周期 | ImageBitmap/PixelMap 必须在命令消费时保持有效或被安全持有 | AC-1.3, AC-2.4 |
| 原始像素 | putImageData 不应用 transform/composition 等绘制状态 | AC-2.2 |
| 同步成本 | getImageData/toDataURL 涉及表面读回和内存拷贝 | AC-2.1, AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 避免频繁 getImageData/toDataURL 大块读回 | Benchmark | AC-2.1, AC-2.3 |
| 内存 | RGBA 缓冲约为 width*height*4，分配溢出需受控 | 边界测试 | VM-3 |
| 安全 | 尺寸乘法、脏矩形和失效资源不越界 | Fuzz | AC-1.3, AC-2.1 |
| 可靠性 | immediate/deferred 图像结果在容差内一致 | 对照金图 | VM-1 |
| 可测试性 | 像素可精确读回比较 | UT | VM-3 |
| 定界定位 | 解码、资源、命令、表面读回可分层定位 | Trace | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 内存受限 | 限制大 ImageData/导出频率 | 压力测试 | VM-3 |
| 平板 | 大图读回成本更高 | 保持同一编码和像素语义 | 性能测试 | VM-4 |
| 折叠屏 | 表面尺寸变化 | 尺寸变化后旧像素清除 | 折叠测试 | Feat-01 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 像素不自动生成语义 | VM-1 |
| 大字体 | 否 | 不涉及字体 | VM-1 |
| 深色模式 | 是 | 图片本身不自动变色 | AC-1.1 |
| 多窗口/分屏 | 是 | 尺寸变化后重绘/重读 | Feat-01 |
| 版本升级 | 是 | API 18 单位分界重点回归 | VM-2 |
| 生态兼容 | 是 | ImageData 和编码输出格式保持 | VM-3, VM-4 |

## Spec 自审清单

- [x] 三种 drawImage 重载和非法输入覆盖
- [x] API 18 PixelMap 单位分界明确
- [x] 原始像素与绘制状态边界明确
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Canvas drawImage ImageData PixelMap toDataURL"
  - repo: "openharmony/interface_sdk-js"
    query: "Canvas PixelMap drawImage API 18 ImageBitmap 26"
```

**关键文档：** `05-ui-components/14-drawing-components/02-canvas/design.md`
