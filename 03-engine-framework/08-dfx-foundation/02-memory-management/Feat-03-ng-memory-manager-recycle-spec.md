# 特性规格

> Func-03-08-02-Feat-03 NG MemoryManager内存回收管线：固化 `MemoryManager` 在窗口后台时对不可见页面 Image 数据进行延迟回收与按需重建的完整行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | NG MemoryManager 内存回收管线 (NG MemoryManager Recycle Pipeline) |
| 特性编号 | Func-03-08-02-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录 `MemoryManager` + `ImagePattern::RecycleImageData` 已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | MemoryManager 回收管线规格 | 补录窗口后台 → 延迟回收 → 不可见页面 Image 数据释放的完整链路 |
| ADDED | 单页回收上限规格 | 补录每页最多回收 20 张图像（`RECYCLE_PAGE_IMAGE_NUM`）的行为约束 |
| ADDED | 回收前置开关规格 | 补录应用级 `GetIsRecycleInvisibleImageMemory` 与系统级 `GetRecycleImageEnabled` 双开关 |
| ADDED | 图像重建规格 | 补录 `RebuildImageByPage` → `LoadImageDataIfNeed` 的按需重建路径 |
| ADDED | SceneBoard 跳过规格 | 补录 SceneBoard 窗口不参与后台回收管线的行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/03-engine-framework/08-dfx-foundation/02-memory-management/design.md` | Baselined |

---

## 用户故事

### US-1: 后台窗口触发不可见页面图像回收

**作为** 系统开发者,
**我想要** 在窗口切入后台时自动延迟回收不可见页面的 Image 数据,
**以便** 降低应用后台内存占用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN PipelineContext::OnHide 执行 THEN 调用 `memoryMgr_->PostMemRecycleTask()` | 行为 |
| AC-1.2 | WHEN PostMemRecycleTask 执行 THEN 投递延迟 `BACKGROUND_RECYCLE_WAIT_TIME_MS`(500)ms 的 UI 线程任务，任务名为 `"TrimMemManagerToRecycleImage"` | 行为 |
| AC-1.3 | WHEN 延迟任务触发 THEN 执行 TrimMemRecycle 遍历 `pageNodes_` 列表 | 行为 |
| AC-1.4 | WHEN 页面节点 `IsVisible()==false` 且 `IsTrimMemRecycle()==false` THEN 对该页面执行 `RecycleImageByPage` | 边界 |
| AC-1.5 | WHEN 页面节点 `IsVisible()==true` 或 `IsTrimMemRecycle()==true` THEN 跳过该页面不回收 | 边界 |

### US-2: 单页图像回收数量限制

**作为** 系统开发者,
**我想要** 对单个页面限制最多回收的图像数量,
**以便** 避免一次性回收过多导致后续重建时产生帧抖动。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN RecycleImageByPage 执行 THEN 先调用 `node->SetTrimMemRecycle(true)` | 行为 |
| AC-2.2 | WHEN 对单页执行回收 THEN 最多回收 `RECYCLE_PAGE_IMAGE_NUM`(20) 张图像 | 边界 |
| AC-2.3 | WHEN 回收计数 `recycleNum` 递减至 0 THEN 停止遍历剩余 Image 子节点 | 边界 |
| AC-2.4 | WHEN 页面 Image 数量少于 20 THEN 回收全部可回收 Image 后正常返回 | 行为 |

### US-3: 图像数据回收前置检查

**作为** 应用开发者,
**我想要** 通过开关控制不可见图像是否参与回收,
**以便** 在内存敏感场景启用、在需要频繁切换的场景关闭。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN RecycleImageData 执行 THEN 优先读取 `pipeline->GetIsRecycleInvisibleImageMemory()` 判断回收开关 | 行为 |
| AC-3.2 | WHEN 应用未设置回收开关（返回 `std::nullopt`）THEN 回退到 `SystemProperties::GetRecycleImageEnabled()` | 行为 |
| AC-3.3 | WHEN 回收开关判定结果为 false THEN `RecycleImageData` 返回 false，不执行回收 | 异常 |
| AC-3.4 | WHEN `loadingCtx_` 存在且 `IsNetworkImageSafeToRecycle()==false` THEN 返回 false，不回收网络图像 | 边界 |
| AC-3.5 | WHEN 回收成功 THEN 释放 `loadingCtx_`、`image_`、`altLoadingCtx_`、`altImage_`、`altErrorCtx_`、`altErrorImage_` 并移除 `contentMod_` | 行为 |
| AC-3.6 | WHEN 回收成功 THEN 设置 `isRecycledImage_=true` | 行为 |

### US-4: 回收后图像按需重建

**作为** 系统开发者,
**我想要** 在页面重新可见或 Image 重新挂载时按需重建图像数据,
**以便** 保证回收后的图像能恢复显示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN RebuildImageByPage 调用且 `isTrimMemWork_==false` THEN 直接返回不重建 | 异常 |
| AC-4.2 | WHEN 节点 `IsTrimMemRecycle()==false` THEN 直接返回不重建 | 边界 |
| AC-4.3 | WHEN 重建执行 THEN 清除 `SetTrimMemRecycle(false)` 后调用 `RebuildImage` | 行为 |
| AC-4.4 | WHEN 重建遍历发现 `IsTrimMemRecycle()==true` 的 Image 节点 THEN 调用 `imagePattern->LoadImageDataIfNeed()` 并清除该节点 TrimMemRecycle 标记 | 行为 |
| AC-4.5 | WHEN Image 节点 `IsTrimMemRecycle()==false` THEN 跳过该节点不重建 | 边界 |
| AC-4.6 | WHEN `isRecycledImage_==true` 的 Image 节点重新挂载到主渲染树 THEN 触发 `LoadImageDataIfNeed` | 恢复 |

### US-5: SceneBoard 窗口跳过回收管线

**作为** 系统开发者,
**我想要** SceneBoard 系统窗口不参与后台图像回收,
**以便** 避免对系统桌面渲染进程产生干扰。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `container->IsSceneBoardWindow()==true` THEN `PostMemRecycleTask` 直接返回不投递任务 | 边界 |
| AC-5.2 | WHEN `isTrimMemWork_==false` THEN `PostMemRecycleTask` 直接返回不投递任务 | 异常 |

### US-6: 页面节点注册与生命周期管理

**作为** 系统开发者,
**我想要** MemoryManager 维护参与回收的页面节点弱引用列表,
**以便** 在回收时按页精确遍历并自动清理失效引用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `AddRecyclePageNode` 调用且 `isTrimMemWork_==true` THEN 将弱引用加入 `pageNodes_`（去重） | 行为 |
| AC-6.2 | WHEN `RemoveRecyclePageNode(nodeId)` 调用 THEN 移除指定 `nodeId` 对应节点及已失效弱引用 | 行为 |
| AC-6.3 | WHEN TrimMemRecycle 中弱引用 `Upgrade` 失败 THEN 从 `pageNodes_` 移除该条目 | 异常 |
| AC-6.4 | WHEN PipelineContext 销毁 THEN 调用 `memoryMgr_.Reset()`，`pageNodes_` 被清空 | 恢复 |

### US-7: 窗口隐藏时主动回收当前 Image

**作为** 系统开发者,
**我想要** Image 组件在窗口隐藏时主动回收自身数据,
**以便** 在 MemoryManager 管线之外提供即时回收补充。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `OnWindowHide` 触发且 `isRecycledImage_==false` 且节点非 pending THEN 主动调用 `RecycleImageData` | 行为 |
| AC-7.2 | WHEN `isRecycledImage_==true` THEN 不重复调用 `RecycleImageData` | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1, R-2, R-6 | TASK-03 | 单测 | `frameworks/core/components_ng/manager/memory/memory_manager.cpp:119-158` |
| AC-2.1~2.4 | R-3, R-4 | TASK-03 | 单测 | `memory_manager.cpp:77-83, 53-75` |
| AC-3.1~3.6 | R-5, R-10, R-11 | TASK-03 | 单测 | `image_pattern.cpp:1622-1661` |
| AC-4.1~4.6 | R-9, R-11 | TASK-03 | 单测 | `memory_manager.cpp:85-117`; `image_pattern.cpp:1743-1758` |
| AC-5.1~5.2 | R-7, R-8 | TASK-03 | 单测 | `memory_manager.cpp:119-124` |
| AC-6.1~6.4 | R-8, R-12 | TASK-03 | 单测 | `memory_manager.cpp:31-51, 160-166`; `pipeline_context.cpp:5919` |
| AC-7.1~7.2 | R-13 | TASK-03 | 单测 | `image_pattern.cpp:1732-1741` |

---

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | PipelineContext::OnHide | 调用 `memoryMgr_->PostMemRecycleTask()` 启动后台回收管线 | `pipeline_context.cpp:5670-5672` | AC-1.1 |
| R-2 | 行为 | PostMemRecycleTask 获取 TaskExecutor | 延迟 `BACKGROUND_RECYCLE_WAIT_TIME_MS`(500)ms 投递 UI 任务 `"TrimMemManagerToRecycleImage"` → TrimMemRecycle | `memory_manager.cpp:22, 129-136` | AC-1.2, AC-1.3 |
| R-3 | 行为 | RecycleImageByPage 执行 | 先 `SetTrimMemRecycle(true)`，再以 `RECYCLE_PAGE_IMAGE_NUM`(20) 为上限调用 RecycleImage | `memory_manager.cpp:23, 77-83` | AC-2.1, AC-2.2 |
| R-4 | 行为 | RecycleImage 递归遍历子树 | 仅对 `V2::IMAGE_ETS_TAG` 节点调用 `imagePattern->RecycleImageData()`；成功后 `recycleNum--`；非 Image 节点递归向下 | `memory_manager.cpp:53-75` | AC-2.3, AC-2.4 |
| R-5 | 行为 | RecycleImageData 判断回收开关 | 优先 `pipeline->GetIsRecycleInvisibleImageMemory()`；为 `nullopt` 时回退 `SystemProperties::GetRecycleImageEnabled()`；关闭则返回 false | `image_pattern.cpp:1633-1636` | AC-3.1~3.3 |
| R-6 | 边界 | TrimMemRecycle 遍历 pageNodes_ | 跳过 `IsVisible()==true` 或 `IsTrimMemRecycle()==true` 的页面；仅对不可见未回收页面执行回收 | `memory_manager.cpp:151-155` | AC-1.4, AC-1.5 |
| R-7 | 边界 | PostMemRecycleTask 检测窗口类型 | `container->IsSceneBoardWindow()==true` 时直接返回，不投递任务 | `memory_manager.cpp:122` | AC-5.1 |
| R-8 | 异常 | `isTrimMemWork_==false` | AddRecyclePageNode / RemoveRecyclePageNode / PostMemRecycleTask / Reset 全部短路返回 | `memory_manager.cpp:33, 45, 122, 162` | AC-5.2, AC-6.1 |
| R-9 | 恢复 | RebuildImageByPage → RebuildImage | 对 `IsTrimMemRecycle()==true` 的 Image 节点调用 `LoadImageDataIfNeed()` 重建并清除标记 | `memory_manager.cpp:85-117` | AC-4.1~4.5 |
| R-10 | 边界 | RecycleImageData 检查网络图像安全性 | `loadingCtx_` 存在时需 `IsNetworkImageSafeToRecycle()==true` 才回收，避免重新下载 | `image_pattern.cpp:1639-1641` | AC-3.4 |
| R-11 | 行为 | 回收成功 | 释放 `loadingCtx_`/`image_`/`alt*` 成员，移除 `contentMod_`，设置 `isRecycledImage_=true` | `image_pattern.cpp:1642-1660` | AC-3.5, AC-3.6 |
| R-12 | 恢复 | PipelineContext 销毁 | 调用 `memoryMgr_.Reset()` 清空 `pageNodes_` 列表 | `pipeline_context.cpp:5919`; `memory_manager.cpp:160-166` | AC-6.4 |
| R-13 | 行为 | ImagePattern::OnWindowHide | `isRecycledImage_==false` 且节点非 pending 时主动调用 `RecycleImageData` | `image_pattern.cpp:1736-1739` | AC-7.1, AC-7.2 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1, R-2, AC-1.1~1.3 | 单测 | OnHide → PostMemRecycleTask → 延迟 500ms 任务投递链路 |
| VM-2 | R-3, R-4, AC-2.1~2.4 | 单测 | 单页回收上限 20 张 + 递归遍历子树逻辑 |
| VM-3 | R-5, AC-3.1~3.3 | 单测 | 应用级/系统级回收开关优先级 |
| VM-4 | R-10, R-11, AC-3.4~3.6 | 单测 | 网络图像安全回收判断 + 成员释放 |
| VM-5 | R-9, AC-4.1~4.6 | 单测 | RebuildImageByPage 重建路径 + TrimMemRecycle 标记清除 |
| VM-6 | R-6, R-7, AC-1.4~1.5, AC-5.1 | 单测 | 可见性/已回收跳过 + SceneBoard 跳过 |
| VM-7 | R-8, R-12, AC-5.2, AC-6.1~6.4 | 单测 | isTrimMemWork_ 守护 + Reset 清空 |
| VM-8 | R-13, AC-7.1~7.2 | 单测 | OnWindowHide 主动回收 |
| VM-9 | 全量 | 集成/hidumper | 多页面后台场景内存下降可观测 |

---

## API 变更分析

### 新增 API

N/A，无新增 Public/System/InnerApi。

### 变更/废弃 API

无。

---

## 接口规格

### 接口定义

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 无
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9+
- **ABI 影响:** 无（`MemoryManager` 为 `PipelineContext` 内部持有的 `RefPtr<MemoryManager>`，不跨模块导出）

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| PipelineContext 持有 MemoryManager | `memoryMgr_` 在 `InitManagers()` 中构造（`pipeline_context.cpp:8398`），通过 `GetMemoryManager()`（`pipeline_context.h:853`）暴露 | 全部 |
| 弱引用页面列表 | `pageNodes_` 使用 `std::list<WeakPtr<FrameNode>>`，避免延长页面生命周期，失效引用在遍历时清理 | AC-6.1~6.3 |
| 回收与重建对称 | RecycleImage（释放）↔ RebuildImage（重建）共享相同的子树遍历策略，仅 Image 节点参与 | AC-2.4, AC-4.4 |
| UI 线程投递 | 延迟回收任务通过 `TaskExecutor::TaskType::UI` 投递，确保回收在 UI 线程执行 | AC-1.2 |
| FrameNode 标记驱动 | `isTrimMemRecycle_`（`frame_node.h:1829`）作为页面级回收状态标记，贯穿回收与重建 | AC-2.1, AC-4.2, AC-4.3 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 延迟回收任务在 500ms 后单次执行；单页回收 ≤20 张 Image，遍历为 O(子树节点数) | benchmark / trace | `memory_manager.cpp:22-23` |
| 内存 | 回收后释放 CanvasImage（GPU 纹理）+ ImageLoadingContext + PixelMap；单页最多回收 20 张 | hidumper | `image_pattern.cpp:1642-1657` |
| 稳定性 | 弱引用列表自动清理失效引用，不产生野指针 | 单测 | `memory_manager.cpp:147-149` |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | N/A | 内存回收不直接影响无障碍语义 | — |
| 大字体 | N/A | 回收管线与字体缩放无关 | — |
| 深色模式 | N/A | 内存回收与颜色无关 | — |
| 多窗口/分屏 | 是 | 每个窗口的 PipelineContext 独立持有 MemoryManager，OnHide 独立触发回收 | AC-1.1 |
| 多用户 | N/A | 回收管线无用户态差异 | — |
| 版本升级 | N/A | 本特性自 API 9 起存在，无版本守护分支 | — |
| SceneBoard | 是 | SceneBoard 系统窗口显式跳过回收管线（`IsSceneBoardWindow`） | AC-5.1 |

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（MemoryManager 回收管线 + ImagePattern::RecycleImageData/OnWindowHide 重建路径；不含 OnNotifyMemoryLevel、ImageCache 多级缓存、LazyForEach 节点回收）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致
- [x] 所有数值来自真实源码（500ms、20、行号引用均可追溯）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "MemoryManager PostMemRecycleTask TrimMemRecycle RecycleImageByPage implementation"
  - repo: "openharmony/ace_engine"
    query: "ImagePattern RecycleImageData LoadImageDataIfNeed OnWindowHide recycle memory"
  - repo: "openharmony/ace_engine"
    query: "PipelineContext OnHide memoryMgr PostMemRecycleTask Reset InitManagers"
```

**关键文档：**
- `frameworks/core/components_ng/manager/memory/memory_manager.h` — MemoryManager 类定义
- `frameworks/core/components_ng/manager/memory/memory_manager.cpp` — 回收管线实现
- `frameworks/core/components_ng/pattern/image/image_pattern.cpp` — RecycleImageData / LoadImageDataIfNeed / OnWindowHide
- `frameworks/core/pipeline_ng/pipeline_context.cpp` — MemoryManager 持有与生命周期
- `frameworks/core/components_ng/base/frame_node.h` — isTrimMemRecycle_ 标记
- 架构设计：`specs/03-engine-framework/08-dfx-foundation/02-memory-management/design.md`
