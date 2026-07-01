# Previewer Package

本目录用于归档 Linux 平台 Previewer 完整包，并说明如何在 `spec-test` HostPreview 用例框架中使用。

## 包内容

当前归档：

```text
previewer-20260625.tar.gz
```

该文件通过 Git LFS 管理。首次拉取仓库后，如果本地只有 LFS pointer 或文件内容不完整，执行：

```bash
git lfs pull
```

解压：

```bash
cd /path/to/arkui-specs
mkdir -p previewer/runtime
tar -xzf previewer/previewer-20260625.tar.gz -C previewer/runtime
```

解压后的关键目录：

```text
previewer/runtime/previewer/common/bin/
├── Previewer
├── PreviewerCLI
└── ...
```

`Previewer` 和 `PreviewerCLI` 必须同时存在且可执行。

## 在 spec-test 中使用

推荐通过 `PREVIEWER_BIN` 显式指定 Previewer 目录：

```bash
cd /path/to/arkui-specs/spec-test
PREVIEWER_BIN="$(pwd)/../previewer/runtime/previewer/common/bin" \
./tools/host_preview/run_feature.sh --openharmony-root /path/to/openharmony
```

按 suite 或 case 执行：

```bash
PREVIEWER_BIN="$(pwd)/../previewer/runtime/previewer/common/bin" \
./tools/host_preview/run_feature.sh --suite-id suite-01-width-height-basic --openharmony-root /path/to/openharmony

PREVIEWER_BIN="$(pwd)/../previewer/runtime/previewer/common/bin" \
./tools/host_preview/run_feature.sh --case-id case-001-width-height-basic --openharmony-root /path/to/openharmony
```

`PREVIEWER_BIN` 优先级最高。未设置时，脚本会按以下顺序查找：

1. `${OHOS_BASE_SDK_HOME}/previewer/common/bin`
2. `${DEVECO_SDK_HOME}/previewer/common/bin`
3. `${OPENHARMONY_ROOT}/out/sdk/ohos-sdk/linux/previewer/common/bin`
4. `${OPENHARMONY_ROOT}/prebuilts/ohos-sdk/linux/previewer/common/bin`

## 环境依赖

Previewer 是图形程序。无显示器的 Linux 命令行环境需要 `Xvfb`：

```bash
# Ubuntu/Debian
sudo apt-get install -y xvfb

# openEuler/CentOS/RHEL
sudo yum install -y xorg-x11-server-Xvfb
```

验证：

```bash
command -v xvfb-run
xvfb-run --help
```

`spec-test` 脚本会通过 `xvfb-run -a` 自动启动 Previewer，无需手动配置 `DISPLAY`。

## 从 OpenHarmony 编译生成 Previewer

如需使用本地 OpenHarmony 补丁后的 Previewer，可在 OpenHarmony 源码根目录编译 SDK：

```bash
cd /path/to/openharmony
./build.sh --export-para PYCACHE_ENABLE:true --product-name ohos-sdk --ccache
```

编译完成后检查：

```bash
ls out/sdk/ohos-sdk/linux/previewer/common/bin/Previewer
ls out/sdk/ohos-sdk/linux/previewer/common/bin/PreviewerCLI
```

预期目录：

```text
out/sdk/ohos-sdk/linux/previewer/common/bin/
```

如果二进制不存在，需要检查 SDK 编译日志中 previewer 相关 `BUILD.gn` 是否被正确包含。

使用自编译 Previewer：

```bash
cd /path/to/arkui-specs/spec-test
PREVIEWER_BIN=/path/to/openharmony/out/sdk/ohos-sdk/linux/previewer/common/bin \
./tools/host_preview/run_feature.sh --openharmony-root /path/to/openharmony
```

## 手动启动 Previewer

通常不需要手动执行以下命令，`spec-test/tools/host_preview/*.sh` 已封装启动、Inspector 采集、截图和清理逻辑。调试 Previewer 本身时可参考：

```bash
export PREVIEWER_BIN=/path/to/previewer/common/bin
export PREVIEWER_NAME="${PREVIEWER_INSTANCE_NAME:-previewer_${USER}}"

cd "${PREVIEWER_BIN}"

xvfb-run -a ./Previewer \
  -s "${PREVIEWER_NAME}" \
  -gui \
  -hap /path/to/entry-default-unsigned.hap \
  -refresh region \
  -cpm false \
  -device phone \
  -shape rect \
  -sd 160 \
  -or 432 936 \
  -cr 432 936 \
  -n entry \
  -av ACE_2_0 \
  -url pages/Index \
  -pages main_pages \
  -pm Stage \
  -l en_US \
  -cm light \
  -o portrait
```

常用参数：

| 参数 | 说明 | 常用值 |
|---|---|---|
| `-hap` | HAP 文件路径 | `entry-default-unsigned.hap` |
| `-url` | 加载页面 URL | `pages/Index` 或 spec case URL |
| `-or` | 设备分辨率，宽 高 | `432 936` |
| `-cr` | 内容区域分辨率，宽 高 | `432 936` |
| `-av` | ArkUI 版本 | `ACE_2_0` |
| `-pm` | 页面模型 | `Stage` |
| `-n` | module 名称 | `entry` |
| `-s` | Previewer 实例名 | `previewer_${USER}` |

## PreviewerCLI 常用命令

Previewer 启动后，可使用 `PreviewerCLI` 发送 action 命令：

```bash
# 采集 Inspector 树
./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command inspector --version 1.0.1

# 采集默认 Inspector
./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command inspectorDefault --version 1.0.1

# 截图
./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command ScreenShot --version 1.0.1

# 退出 Previewer
./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command exit --version 1.0.1
```

### Router 路由控制

Previewer 支持通过 CLI 触发 stage 应用的 router 路由跳转，语义等同于 ArkTS `router.pushUrl` / `router.replaceUrl` / `router.back`：

```bash
# router.pushUrl({ url: 'pages/Detail', params: { id: '42' } })
./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command RouterPush \
  --version 1.0.1 --args -url pages/Detail -params '{"id":"42"}'

# router.replaceUrl({ url: 'pages/Login' })
./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command RouterReplace \
  --version 1.0.1 --args -url pages/Login

# router.back()
./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command RouterBack --version 1.0.1
```

参数说明：

| 命令 | 必填 | 可选 | 说明 |
|---|---|---|---|
| `RouterPush` | `-url <page>` | `-params '<JSON>'` | 入栈新页面，`params` 为 JSON 字符串（例如 `'{"id":"42"}'`），可省略 |
| `RouterReplace` | `-url <page>` | `-params '<JSON>'` | 替换当前页面，不入栈 |
| `RouterBack` | — | — | 回退一页，等价于 `BackClicked`；栈空时行为由应用决定 |

跳转后可用 `CurrentRouter` 查询当前页：

```bash
./PreviewerCLI --name "${PREVIEWER_NAME}" -- --type action --command CurrentRouter --version 1.0.1
```

在 `spec-test` 的 operations JSON 中，用现有 `action` op 即可，无需额外框架改动：

```json
[
  { "op": "action", "command": "RouterPush",    "args": { "url": "pages/Detail", "params": "{\"id\":\"42\"}" } },
  { "op": "wait",   "durationMs": 300 },
  { "op": "action", "command": "RouterBack" }
]
```

注意：

- `Previewer -s` 与 `PreviewerCLI --name` 必须完全一致。
- CLI 通过 `/tmp/${PREVIEWER_NAME}_commandPipe` 与 Previewer 通信。
- `connect socket failed` 通常表示实例名不一致、Previewer 尚未启动完成、进程已退出，或旧进程残留占用了通信管道。
- `spec-test` 默认实例名为 `previewer_<当前用户名>`，可通过 `PREVIEWER_INSTANCE_NAME` 覆盖。

## 与 SDK 的关系

`PREVIEWER_BIN` 只决定 HostPreview 执行时使用哪个 Previewer。HAP 编译仍需要 SDK 与 Node：

- `OHOS_BASE_SDK_HOME` 或 `local.properties` 中的 `sdk.dir`
- `NODE_HOME` 或 `local.properties` 中的 `nodejs.dir`
- `--openharmony-root` 指向 OpenHarmony 源码根目录，用于定位 `hvigorw.js`

`sdk.dir` / `OHOS_BASE_SDK_HOME` 应指向 SDK 的 `linux` 根目录，而不是 `linux/<api-version>` 子目录。
