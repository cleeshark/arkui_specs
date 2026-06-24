# 特性规格

> Func-04-01-01-Feat-01 图片加载机制：固化 NG 图片加载管线（状态机、多源加载器、缓存体系、解码管线）的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 图片加载机制 (Image Loading Mechanism) |
| 特性编号 | Func-04-01-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有 NG 图片加载管线的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/01-image-loading/01-image-loading-mechanism/design.md` | Baselined |

---

## 用户故事

### US-1: 通过 URI 加载图片

**作为** 应用开发者,
**我想要** 通过 URI (文件路径/网络 URL/资源引用/asset/base64) 指定图片来源,
**以便** 在 Image 组件中显示不同来源的图片。

**验收标准：**

- **AC-1.1:** WHEN src 为 file:// 路径 THEN 通过 FileImageLoader 从本地文件系统读取图片
- **AC-1.2:** WHEN src 为 http:// 或 https:// URL THEN 通过 NetworkImageLoader 下载网络图片，下载结果可写入磁盘缓存
- **AC-1.3:** WHEN src 为 $r('app.media.xxx') 资源引用 THEN 通过 ResourceImageLoader 从应用资源加载
- **AC-1.4:** WHEN src 为 data:image/xxx;base64,... THEN 通过 Base64ImageLoader 解码内嵌 Base64 数据
- **AC-1.5:** WHEN src 为 PixelMap 对象 THEN 通过 PixelMapImageLoader 直接使用，无需文件 I/O
- **AC-1.6:** WHEN 工厂无法识别的 SrcType THEN CreateImageLoader 返回 nullptr，加载失败

### US-2: 图片加载状态机驱动

**作为** 框架开发者,
**我想要** 通过状态机管理图片加载的完整生命周期,
**以便** 确保 UNLOADED → DATA_LOADING → DATA_READY → MAKE_CANVAS_IMAGE → LOAD_SUCCESS 的严格顺序流转。

**验收标准：**

- **AC-2.1:** WHEN 发送 LOAD_DATA 命令且当前状态为 UNLOADED THEN 转移到 DATA_LOADING 并调用 OnDataLoading
- **AC-2.2:** WHEN 发送 LOAD_DATA_SUCCESS 命令且当前状态为 DATA_LOADING THEN 转移到 DATA_READY 并调用 OnDataReady
- **AC-2.3:** WHEN 发送 MAKE_CANVAS_IMAGE 命令且当前状态为 DATA_READY THEN 转移到 MAKE_CANVAS_IMAGE 并调用 OnMakeCanvasImage
- **AC-2.4:** WHEN 发送 MAKE_CANVAS_IMAGE_SUCCESS 命令且当前状态为 MAKE_CANVAS_IMAGE THEN 转移到 LOAD_SUCCESS 并调用 OnLoadSuccess
- **AC-2.5:** WHEN 任何阶段发送 LOAD_FAIL 命令 THEN 转移到 LOAD_FAIL 终态并调用 OnLoadFail
- **AC-2.6:** WHEN 任何状态发送 RESET_STATE 命令 THEN 回到 UNLOADED 状态
- **AC-2.7:** WHEN 当前状态为 LOAD_SUCCESS 且发送 MAKE_CANVAS_IMAGE 命令 THEN 重新进入 MAKE_CANVAS_IMAGE（支持重解码）
- **AC-2.8:** WHEN 当前状态为 LOAD_FAIL THEN 除 RESET_STATE 外的所有命令被静默忽略（包括 RETRY_LOADING）

### US-3: 多级缓存加速图片加载

**作为** 应用开发者,
**我想要** 已加载的图片被缓存以避免重复加载和解码,
**以便** 提升图片显示性能和减少网络请求。

**验收标准：**

- **AC-3.1:** WHEN 图片数据首次加载完成 THEN ImageObject 被缓存到 ImageCache（默认容量 2000）
- **AC-3.2:** WHEN 同一 URI 再次被请求 THEN 优先从 ImageObject 缓存获取，跳过数据加载阶段
- **AC-3.3:** WHEN 原始图片数据通过 GetImageData 获取 THEN 数据被缓存到 ImageData 缓存（默认禁用，容量为 0）
- **AC-3.4:** WHEN 网络图片下载完成 THEN 图片文件被写入 ImageFileCache 磁盘缓存（默认 100MB）
- **AC-3.5:** WHEN ImageFileCache 容量达到上限 THEN 按访问时间淘汰最旧的文件，直到总大小降至 50%
- **AC-3.6:** WHEN ImageObject 缓存容量达到上限 THEN 按 LRU 策略淘汰最旧的条目

### US-4: 图片解码与尺寸适配

**作为** 应用开发者,
**我想要** 图片根据组件尺寸自动解码到合适的分辨率,
**以便** 避免加载过大的图片浪费内存。

**验收标准：**

- **AC-4.1:** WHEN autoResize 启用且组件尺寸变化 THEN 目标解码宽度按功率对齐（原始宽度的 2^N 分之一），仅跨越边界时触发重解码
- **AC-4.2:** WHEN SystemProperties::GetImageFrameworkEnabled() 为 true THEN 使用 ImageFramework 解码路径（ImageSource::CreatePixelMap）
- **AC-4.3:** WHEN SystemProperties::GetImageFrameworkEnabled() 为 false THEN 使用 Skia 解码路径（SkCodec）
- **AC-4.4:** WHEN StaticImageObject 解码完成后 THEN CanvasImage 创建成功，原始 data 被清除（ClearData）释放内存
- **AC-4.5:** WHEN AnimatedImageObject 创建后 THEN 原始 data 被保留不清除（ClearData 为空操作），用于逐帧解码
- **AC-4.6:** WHEN SVG 图片加载 THEN 直接通过 SvgDomBase::DrawImage 渲染到 Canvas，不进行光栅化解码，忽略 resizeTarget 参数

### US-5: 加载任务去重

**作为** 框架开发者,
**我想要** 多个组件请求同一图片源时共享同一个后台加载任务,
**以便** 避免重复的网络请求或文件 I/O。

**验收标准：**

- **AC-5.1:** WHEN 多个 ImageLoadingContext 请求同一 URI 的数据加载 THEN 通过 RegisterTask 去重，仅创建一个后台任务
- **AC-5.2:** WHEN 去重任务完成 THEN 通过 EndTask 获取所有等待的 context 列表，逐个通知结果
- **AC-5.3:** WHEN 某个 context 被销毁且它是唯一等待者 THEN 通过 CancelTask 取消后台任务
- **AC-5.4:** WHEN 某个 context 被销毁但仍有其他等待者 THEN 仅从 ctxs_ 集合中移除该 context，任务继续执行

### US-6: 加载回调通知

**作为** 应用开发者,
**我想要** 在图片加载的关键阶段收到回调通知,
**以便** 在 UI 上显示加载状态或处理错误。

**验收标准：**

- **AC-6.1:** WHEN 状态进入 DATA_READY THEN 触发 onDataReady 回调，通知数据已就绪
- **AC-6.2:** WHEN 状态进入 LOAD_SUCCESS THEN 触发 onLoadSuccess 回调，通知图片可渲染
- **AC-6.3:** WHEN 状态进入 LOAD_FAIL THEN 触发 onLoadFail 回调，携带错误信息和 ImageErrorInfo
- **AC-6.4:** WHEN StaticImageObject 进入 LOAD_SUCCESS THEN 在 OnLoadSuccess 中自动调用 ClearData 释放原始字节

---

## 验收追溯

| AC ID | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.6 | FR-1 ~ FR-7 | — | 单元测试 | — |
| AC-2.1 ~ AC-2.8 | FR-8 ~ FR-15 | — | 单元测试 | — |
| AC-3.1 ~ AC-3.6 | FR-16 ~ FR-22 | — | 单元测试 + 性能测试 | — |
| AC-4.1 ~ AC-4.6 | FR-23 ~ FR-30 | — | 单元测试 | — |
| AC-5.1 ~ AC-5.4 | FR-31 ~ FR-34 | — | 单元测试 | — |
| AC-6.1 ~ AC-6.4 | FR-35 ~ FR-38 | — | 集成测试 | — |

---

## 业务规则

- **BR-1:** 图片加载管线分为两个独立阶段：数据加载（获取原始字节 → ImageObject）和画布图像制作（解码 → CanvasImage）。两阶段通过状态机严格隔离
- **BR-2:** 缓存层次从热到冷为：内存 ImageObject 缓存 → 内存 ImageData 缓存 → 磁盘文件缓存 → 网络。每一级未命中才访问下一级
- **BR-3:** Static 和 Animated 图片的内存策略不同：Static 在 CanvasImage 创建后释放原始数据；Animated 保留数据用于逐帧解码
- **BR-4:** SVG 图片不经过位图解码路径，直接通过 SVG DOM 渲染到 Canvas，矢量特性保留
- **BR-5:** autoResize 功率对齐机制将连续的尺寸变化离散化为 2^N 级别，减少重解码次数

---

## 功能规则

- **FR-1:** `ImageLoader::CreateImageLoader()` 工厂根据 SrcType 返回对应 Loader 实例 → `image_loader.cpp:116-161`
- **FR-2:** `FileImageLoader` 处理 FILE 和 INTERNAL 源类型 → `image_loader.cpp:120-123`
- **FR-3:** `NetworkImageLoader` 处理 NETWORK 源类型，支持磁盘缓存写入 → `image_loader.cpp:124-126`
- **FR-4:** `ResourceImageLoader` 处理 RESOURCE 源类型（$r 引用） → `image_loader.cpp:133-135`
- **FR-5:** `Base64ImageLoader` 处理 BASE64 源类型 → `image_loader.cpp:130-132`
- **FR-6:** `PixelMapImageLoader` 处理 PIXMAP 源类型，直接使用现有 PixelMap → `image_loader.cpp:148-150`
- **FR-7:** UNSUPPORTED 源类型返回 nullptr → `image_loader.cpp:157-160`
- **FR-8:** `ImageLoadingState` 枚举：UNLOADED(0), DATA_LOADING(1), DATA_READY(2), MAKE_CANVAS_IMAGE(3), LOAD_SUCCESS(4), LOAD_FAIL(5) → `image_state_manager.h:26-33`
- **FR-9:** `ImageLoadingCommand` 枚举：LOAD_DATA(0), LOAD_FAIL(1), LOAD_DATA_SUCCESS(2), MAKE_CANVAS_IMAGE(3), MAKE_CANVAS_IMAGE_SUCCESS(4), RETRY_LOADING(5), RESET_STATE(6) → `image_state_manager.h:35-43`
- **FR-10:** UNLOADED + LOAD_DATA → DATA_LOADING → `image_state_manager.cpp:74-79`
- **FR-11:** DATA_LOADING + LOAD_DATA_SUCCESS → DATA_READY → `image_state_manager.cpp:82-89`
- **FR-12:** DATA_READY + MAKE_CANVAS_IMAGE → MAKE_CANVAS_IMAGE → `image_state_manager.cpp:91-96`
- **FR-13:** MAKE_CANVAS_IMAGE + MAKE_CANVAS_IMAGE_SUCCESS → LOAD_SUCCESS → `image_state_manager.cpp:99-106`
- **FR-14:** LOAD_SUCCESS + MAKE_CANVAS_IMAGE → MAKE_CANVAS_IMAGE（重解码） → `image_state_manager.cpp:108-114`
- **FR-15:** LOAD_FAIL 对所有命令（含 RETRY_LOADING）均忽略，仅 RESET_STATE 回到 UNLOADED → `image_state_manager.cpp:116-121`
- **FR-16:** ImageObject 缓存默认容量 2000 → `image_cache.h:120`
- **FR-17:** ImageData 缓存默认容量 0（禁用） → `image_cache.h:113-114`
- **FR-18:** 解码图像缓存默认容量 0（禁用） → `image_cache.h:107, 109-110`
- **FR-19:** ImageFileCache 默认 100MB，淘汰比例 50% → `image_file_cache.h:80-82`
- **FR-20:** ImageFileCache 按 FileInfo::accessTime LRU 排序，最旧优先淘汰 → `image_file_cache.h:34-37`
- **FR-21:** `ImageLoader::GetImageData()` 先查内存缓存，未命中再加载 → `image_loader.cpp:214-236`
- **FR-22:** PIXMAP 源跳过缓存直接加载；STREAM 源跳过缓存直接调用 LoadImageData → `image_loader.cpp:218-223`
- **FR-23:** `RoundUp(value)` 从原始图像宽度反复减半，返回 >= value 的最小 2^N 分之一 → `image_loading_context.cpp:319-328`
- **FR-24:** autoResize 尺寸变化仅在 `RoundUp(dstSize.Width()) != sizeLevel_` 时触发重解码 → `image_loading_context.cpp:330-360`
- **FR-25:** `SystemProperties::GetImageFrameworkEnabled()` 决定解码路径 → `image_provider.cpp:674-677`
- **FR-26:** Skia 路径使用 `SkCodec` 解码，输出 `DrawingImage` → `image_decoder.cpp:101-127`
- **FR-27:** ImageFramework 路径使用 `ImageSource::CreatePixelMap` 解码，输出 `PixelMapImage` → `image_decoder.cpp:144-201`
- **FR-28:** `StaticImageObject` 继承基类 ClearData（`data_.Reset()`） → `image_object.cpp:53-57`
- **FR-29:** `AnimatedImageObject::ClearData()` 为空操作，保留数据用于帧解码 → `animated_image_object.h:36-39`
- **FR-30:** `SvgImageObject::MakeCanvasImage` 创建 SvgCanvasImage，忽略 resizeTarget → `svg_image_object.cpp:45-54`
- **FR-31:** `ImageProvider::RegisterTask(key, ctx)` 去重检查 → `image_provider.cpp:250-266`
- **FR-32:** `ImageProvider::EndTask(key)` 返回所有等待的 context → `image_provider.cpp:268-286`
- **FR-33:** `ImageProvider::CancelTask(key, ctx)` 唯一等待者时取消任务 → `image_provider.cpp:288-309`
- **FR-34:** 多等待者时仅移除 context，任务继续 → `image_provider.cpp:296-308`
- **FR-35:** `LoadNotifier` 包含 onDataReady_、onLoadSuccess_、onLoadFail_ 三个回调 → `image_provider.h:38-49`
- **FR-36:** onDataReady_ 在 DATA_READY 状态触发 → `image_loading_context.cpp:115-117`
- **FR-37:** onLoadSuccess_ 在 LOAD_SUCCESS 状态触发 → `image_loading_context.cpp:100-102`
- **FR-38:** onLoadFail_ 在 LOAD_FAIL 状态触发，携带 errorMsg 和 errorInfo → `image_loading_context.cpp:108-110`

---

## 异常/豁免规则

- **ER-1:** RETRY_LOADING 命令已定义（ordinal 5）但 LOAD_FAIL 处理器无对应 case，重试功能未实现 → `image_state_manager.cpp:116-121`
- **ER-2:** ImageData 缓存和解码图像缓存默认容量为 0（禁用），需通过 `SetCapacity()` / `SetDataSizeLimit()` 显式启用 → `image_cache.h:107-117`
- **ER-3:** ImageObject 缓存中存储的是克隆对象（数据已清除），原始数据由源 context 持有 → `image_provider.cpp` 中 CacheImgObjNG 逻辑

---

## 恢复契约

- **RC-1:** 任何状态发送 RESET_STATE 命令可回到 UNLOADED，清除所有中间状态
- **RC-2:** LOAD_FAIL 状态下仅接受 RESET_STATE 命令恢复；RETRY_LOADING 不生效
- **RC-3:** ImageFileCache 磁盘缓存可被系统自动清理或通过 `ClearCacheFile()` 手动清除

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|------|
| VM-1 | US-1 多源加载器 | 单元测试 | 12 种 SrcType 工厂映射 |
| VM-2 | US-2 状态机 | 单元测试 | 状态转移完整性和非法命令忽略 |
| VM-3 | US-3 缓存 | 单元测试 + 性能测试 | LRU 淘汰策略、容量限制、磁盘缓存 I/O |
| VM-4 | US-4 解码 | 单元测试 | 功率对齐、双路径分支、Static/Animated/SVG 差异 |
| VM-5 | US-5 去重 | 单元测试 | RegisterTask/EndTask/CancelTask 三种场景 |
| VM-6 | US-6 回调 | 集成测试 | 三个回调的触发时机和参数 |

---

## API 变更分析

### 新增 API

本特性为框架内部能力，无外部 Public API 变更。Image 组件的 `src` 属性是外部入口。

### 变更/废弃 API

无。

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否 — 磁盘缓存格式为自定义 AstcHeader + 原始文件，非公共格式
- **最低支持版本:** API 7
- **API 版本号策略:** 无外部 API 版本差异

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| UI/后台线程分离 | 数据加载和解码在后台线程执行，回调通过 PostToUI 回到 UI 线程 | AC-6.1 ~ AC-6.4 |
| 缓存线程安全 | ImageCache 使用 timed_mutex，ImageFileCache 使用文件锁，weakPixelMapCache 使用 shared_mutex | AC-3.1 ~ AC-3.6 |
| 状态机不可跳跃 | DATA_LOADING 不可直接跳到 MAKE_CANVAS_IMAGE，必须经过 DATA_READY | AC-2.1 ~ AC-2.8 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | autoResize 功率对齐减少 80%+ 的重解码次数（相比逐像素重解码） | 性能测试 | `image_loading_context.cpp:319-328` |
| 内存 | StaticImageObject 解码后 ClearData 释放原始字节；内存缓存容量可配置 | 内存分析 | `image_object.cpp:53-57` |
| 安全 | 网络图片下载结果写入磁盘缓存，文件路径由框架控制 | 代码审查 | `image_file_cache.h` |
| 可靠性 | 任务去重避免重复网络请求；缓存未命中自动降级到下一级 | 单元测试 | `image_provider.cpp:250-309` |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 图片加载完成后触发 onComplete 回调，可用于无障碍描述 | AC-6.2 |
| 大字体 | 是 | autoResize 功率对齐在组件尺寸变化时自动适配 | AC-4.1 |
| 深色模式 | 否 | 图片加载不涉及颜色主题 |
| 多窗口/分屏 | 是 | 缓存为进程级共享，多窗口共享同一缓存实例 | AC-3.1 ~ AC-3.6 |
| 版本升级 | 否 | 无外部 API 版本差异 |
| 生态兼容 | 是 | ImageFramework 路径支持 OHOS 平台解码器；Skia 路径支持跨平台 | AC-4.2, AC-4.3 |

---

## 行为场景

```
Feature: 图片加载状态机
  作为 框架开发者
  我想要 通过状态机驱动图片加载生命周期
  以便 保证加载阶段的严格顺序

  Scenario: 首次加载图片成功
    Given ImageLoadingContext 处于 UNLOADED 状态
    When 发送 LOAD_DATA 命令
    Then 状态变为 DATA_LOADING，调用 OnDataLoading
    And 数据加载成功后发送 LOAD_DATA_SUCCESS
    Then 状态变为 DATA_READY，触发 onDataReady 回调
    And 发送 MAKE_CANVAS_IMAGE 命令
    Then 状态变为 MAKE_CANVAS_IMAGE，调用 OnMakeCanvasImage
    And 解码成功后发送 MAKE_CANVAS_IMAGE_SUCCESS
    Then 状态变为 LOAD_SUCCESS，触发 onLoadSuccess 回调

  Scenario: 加载失败不可恢复
    Given ImageLoadingContext 处于 LOAD_FAIL 状态
    When 发送 RETRY_LOADING 命令
    Then 命令被静默忽略，状态保持 LOAD_FAIL
    When 发送 RESET_STATE 命令
    Then 状态回到 UNLOADED
```

```
Feature: 任务去重
  作为 框架开发者
  我想要 共享同一图片源的加载任务
  以便 避免重复的网络请求

  Scenario: 多个组件请求同一网络图片
    Given 组件 A 已开始加载 "https://example.com/img.png"
    When 组件 B 也请求加载同一 URL
    Then 组件 B 的 context 被添加到同一任务的 ctxs_ 集合
    And 不创建新的网络请求
    When 网络下载完成
    Then 组件 A 和组件 B 都收到 DataReadyCallback 通知
```

```
Feature: autoResize 功率对齐
  作为 应用开发者
  我想要 图片根据组件尺寸自动适配解码分辨率
  以便 避免加载过大的图片浪费内存

  Scenario: 组件尺寸连续变化不触发重解码
    Given 原始图片宽度为 2048px
    And 组件宽度从 300 变为 350
    When RoundUp(300) = 512, RoundUp(350) = 512（同一级别）
    Then 不触发重解码，复用已有 CanvasImage

  Scenario: 组件尺寸跨越级别边界触发重解码
    Given 原始图片宽度为 2048px
    And 组件宽度从 300 变为 600
    When RoundUp(300) = 512, RoundUp(600) = 1024（跨级别）
    Then 触发重解码，以 1024 宽度重新解码
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（状态机、多源加载器、缓存体系、解码管线）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

---

## context-references

```yaml
context-queries:
  - repo: "arkui/ace_engine"
    query: "NG ImageProvider pipeline: ImageLoadingContext state machine and task deduplication"
  - repo: "arkui/ace_engine"
    query: "ImageLoader factory: CreateImageLoader and 12 concrete loader subclasses"
  - repo: "arkui/ace_engine"
    query: "ImageCache four compartments and ImageFileCache LRU eviction"
  - repo: "arkui/ace_engine"
    query: "ImageDecoder dual path: Skia (SkCodec) vs ImageFramework (ImageSource::CreatePixelMap)"
  - repo: "arkui/ace_engine"
    query: "StaticImageObject vs AnimatedImageObject ClearData memory strategy"
```

**关键文档：** `specs/04-common-capability/01-image-loading/01-image-loading-mechanism/design.md`
