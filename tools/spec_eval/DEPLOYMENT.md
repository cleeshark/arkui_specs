# spec_eval GitCode MR CI — 部署指导

本指南用 `deploy_ci.py` 在一台 Linux 机器上一键部署/升级 spec_eval 的 GitCode MR CI 环境
（webhook 接收器 + CI Worker）。CI 是 **report-only、非阻塞** 的：PR 收到 hook 后跑静态评价、
归档报告、回写一条可更新评论，不阻塞合入。

---

## 1. 前置依赖

| 依赖 | 是否必需 | 安装 |
|---|---|---|
| Python ≥ 3.10 | 必需 | 系统包（`python3`） |
| git | 必需 | 系统包 |
| ripgrep (`rg`) | 强烈建议（缺失则退化 rglob，1.1G 树会很慢） | 系统包或 <https://github.com/BurntSushi/ripgrep> |
| PyYAML | 必需（评价器唯一第三方依赖） | `pip install pyyaml` |
| oh-gc CLI | 仅 PR 评论回写需要；report-only 归档可不要 | `npm install -g @oh-gc/cli@0.7.5`，再 `oh-gc auth login` |
| GitCode webhook 密码 (token) | 非 loopback 监听必需 | 在 GitCode 仓库 Webhook 设置里配置，见 §4 |

`doctor` 会逐项检查并给出缺失项的安装命令。

## 2. 一键部署

默认**跟随各仓 master**（评到最新代码）。`--frozen` 切到与冻结 Finding baseline 对齐的 golden SHA（可复现，
见 §6）。脚本自包含（纯 stdlib），支持先 `curl` 下载再跑：

```bash
# 选一个部署根（其下会长 foundation/ 和 interface/）
export OH_ROOT=/opt/ohos-spec-eval       # 或任意可写目录

# 用 GitCode API v5 的 raw 端点拉脚本（web 端 /raw/ 对 curl 返回 HTML 壳；默认分支是 main）。
# 私有仓追加 &access_token=<PAT>。
curl -fsSL -o deploy_ci.py \
  "https://api.gitcode.com/api/v5/repos/arkui_architecture/arkui-specs/raw/tools/spec_eval/deploy_ci.py?ref=main"

# 部署 4 个仓到正确目录结构 + 种入 webhook token（从环境变量读）
GITCODE_WEBHOOK_TOKEN='<你在 GitCode 配的 webhook 密码>' \
  python3 deploy_ci.py deploy --deploy-root "$OH_ROOT"

# 校验
python3 deploy_ci.py doctor --deploy-root "$OH_ROOT"
```

`deploy` 会在 `$OH_ROOT` 下克隆：

| 仓 | clone URL | 部署目录 | 默认/frozen |
|---|---|---|---|
| ace_engine | `gitcode.com/openharmony/arkui_ace_engine` | `foundation/arkui/ace_engine` | master / `d91b4e4…` |
| specs | `gitcode.com/arkui_architecture/arkui-specs` | `foundation/arkui/ace_engine/specs`（嵌套） | master / `ca45d1f…` |
| sdk-js | `gitcode.com/openharmony/interface_sdk-js` | `interface/sdk-js`（**连字符**） | master / `224c0c1…` |
| sdk_c | `gitcode.com/openharmony/interface_sdk_c` | `interface/sdk_c`（下划线） | master / `62b5e3d…` |

> **目录结构是强制的**：`config.py` 用 `oh_root = repo_root.parents[2]` 推导，ace_engine 必须落在
> `<OH_ROOT>/foundation/arkui/ace_engine`；sdk-js 部署目录必须用连字符 `sdk-js`（仓名是下划线
> `interface_sdk-js`），sdk_c 用下划线。`deploy_ci.py` 已处理这些细节，**不要手动改目录名**。

部署完磁盘占用约：ace_engine ~1.5G（含 .git）、sdk-js ~265M、sdk_c ~27M、specs ~530M。ace_engine
**必须全量**（basename/suffix 索引扫全树，稀疏会产生假引用失败）；`--shallow` 可缩小 .git 但工作树仍完整。

只部署部分仓：`--only ace_engine,specs,sdk-js,sdk_c`（逗号分隔或多次）。

## 3. 升级

```bash
python3 deploy_ci.py upgrade --deploy-root "$OH_ROOT"          # 跟随 master（默认）
python3 deploy_ci.py upgrade --deploy-root "$OH_ROOT" --frozen # 重新对齐 golden SHA
```

`upgrade` 对每个已部署仓 `git fetch` + 切到目标版本（master：`reset --hard origin/<默认分支>`；frozen：
`checkout <SHA>`），幂等。升级后**重启** `ci_service.sh` 生效。

查看当前各仓 HEAD：`python3 deploy_ci.py info --deploy-root "$OH_ROOT"`。

## 4. GitCode Webhook 配置

CI 监听 GitCode 仓库的 **Merge Request Hook**。在 GitCode 仓库 → 设置 → Webhooks：

- **URL**：你的公网回调地址 + `/webhooks/gitcode`（见 §5，例如 `http://<公网IP>:6003/webhooks/gitcode`）。
- **密码 (Password/Token)**：一个自定义 secret，填到这里，并把它作为 `GITCODE_WEBHOOK_TOKEN` 传给 deploy（写入 `~/.gitcode_webhook_token`）。接收器据此校验 `X-GitCode-Token`。
- **触发事件**：勾选 Merge Request Hook（Push Hook 可不勾，接收器会忽略并返回 202）。

GitCode 连通性探测（`GET /webhooks/gitcode`）返回 200 即配置成功。

## 5. 网络可达性（公网入口）

接收器默认绑 `127.0.0.1:8765`（loopback，无需 token 也能起，但 GitCode 从外网来）。你需要一个公网入口
把外部流量转发到 `127.0.0.1:8765`。任选其一：

- **frpc 隧道**（已验证）：frps 在公网，frpc 本地，把公网端口 `6003` 映射到本地 `127.0.0.1:8765`：
  ```toml
  serverAddr = "<frps 公网 IP>"
  serverPort = 7000
  [[proxies]]
  name = "webhook"
  type = "tcp"
  localIP = "127.0.0.1"
  localPort = 8765
  remotePort = 6003
  ```
  GitCode webhook URL 填 `http://<frps 公网 IP>:6003/webhooks/gitcode`。
- **反向代理**（nginx/caddy）→ `127.0.0.1:8765`。
- **云主机公网 IP**：用 `WEBHOOK_HOST=0.0.0.0` 让接收器监听全部接口（此时 **必须** 配 token）。

## 6. 跟随 master vs 冻结 baseline

- **默认跟随 master**：评到最新 ace_engine/specs/sdk，但 Finding baseline (`evaluation/baselines/current.json`)
  冻结在 `ace_engine d91b4e4 / rule v0.2.16`。若新代码改了被引用的源码位置，可能出现源码驱动的 delta
  （baseline 漂移）。`doctor` 会比对 baseline `rule_version` 与当前 orchestrator，不一致时告警。
- **`--frozen`**：各仓 checkout 到 golden SHA（与 baseline 同源），delta 纯粹由 specs PR 驱动、可复现。推荐
  用于回归基线一致的灰度。
- 重新生成 baseline（跟随 master 后对齐）：用全量扫描流程 `python3 cli.py scan --all --output <root>` 再
  `cli.py baseline --results <root> --write`（NEXT-002 流程），不在本部署脚本范围内。

## 7. 启动 CI 服务

```bash
cd "$OH_ROOT/foundation/arkui/ace_engine"
./specs/tools/spec_eval/ci_service.sh
```

`ci_service.sh` 后台起接收器、前台起 `ci_worker --watch`（每 10s 轮询 receipt），Ctrl-C 同时关闭两者，
token 自动读 `~/.gitcode_webhook_token`。环境变量覆盖：`WEBHOOK_HOST/PORT`、`SPEC_EVAL_REPO`（白名单
owner/repo，默认 `arkui_architecture/arkui-specs`）、`CI_POLL_INTERVAL`、`EXTRA_WORKER_ARGS`、
`CI_TEST_ON_PASS=1`（运行通过即调 `oh-gc pr test` 写入测试通过，见下）、`CI_FORCE_TEST=1`（配合前者加 `--force`）。

**通过即回写 CI 测试结果**：`CI_TEST_ON_PASS=1 ./ci_service.sh`。每次新的 MR Hook 被 Worker 消费时，先调用
GitCode `PATCH /repos/{owner}/{repo}/pulls/{n}/testers` 复位旧测试状态，再执行评价。普通模式使用
`reset_all=false`，要求 `oh-gc` 登录用户已经是该 PR 的 tester，仅复位自己；若 CI 使用管理员/非 tester 账号，必须
显式配置 `CI_FORCE_TEST=1`，此时使用管理员专属的 `reset_all=true` 复位全部 tester，并在通过时调用
`oh-gc pr test --force`。判定"通过"= 评价完成且 `delta.added == 0`（无新增错误，既有 baseline 债务不计）。写通过前会再次
读取 PR 当前 head，只有它仍等于本次 receipt 的 tested SHA 才调用
`oh-gc pr test <PR> --repo <REPO>`。因此后续 push 会先撤销旧的 bot 测试通过，旧任务也不能覆盖新 head 的状态。
有新增错误、评价未完成、复位失败或 head 已变化时均**不写测试通过**（评论仍照常发）。该流程不会调用代表人工代码
评审的 `oh-gc pr review`。`--dry-run` 下不执行复位或测试状态回写。

真实 API 验证（PR #60）：`sunfei2021` 对由 `arkui_architecture` 测试通过的 PR 调 `reset_all=false` 返回
HTTP 400 `Must be a tester of this merge request`，状态不变；同一管理员账号调 `reset_all=true` 成功，
`arkui_architecture.accept` 从 `true` 变为 `false`，`approval_testers_required_passed` 从 `true` 变为 `false`。

常驻方式由你选，例如 tmux / nohup，或一段 systemd unit（参考，不随包安装）：

```ini
# /etc/systemd/system/ohos-spec-eval.service  (示例，按需调整 User/ExecStart 路径)
[Unit]
Description=OpenHarmony spec_eval GitCode MR CI
After=network.target

[Service]
Type=simple
User=ci
WorkingDirectory=/opt/ohos-spec-eval/foundation/arkui/ace_engine
Environment=OH_ROOT=/opt/ohos-spec-eval
ExecStart=/opt/ohos-spec-eval/foundation/arkui/ace_engine/specs/tools/spec_eval/ci_service.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

只想 **report-only 归档、不发评论**（不要 oh-gc）：`EXTRA_WORKER_ARGS=--no-comment ./ci_service.sh`。

## 8. 排错

| 现象 | 原因 / 处理 |
|---|---|
| receipt 被 `skipped_mismatch` | specs 工作树 HEAD ≠ receipt 的 tested SHA（正常 SHA 门控）。要评该 PR，把 specs 切到 tested SHA，或 `ci_worker --auto-checkout`。 |
| doctor 报 `baseline rule_version ... != orchestrator` | baseline 与当前 specs 的规则版本不一致（漂移）。用 `--frozen` 或重新生成 baseline。 |
| `oh-gc` 评论失败 / `pr comment-edit` 输出 `undefined` | `comment-edit --json` 是 oh-gc 已知怪癖（实际成功）；Worker 已按 returncode 处理，不影响 edit-in-place。 |
| 评价很慢 | 缺 ripgrep → 退化 rglob。装 `rg`。 |
| `import yaml` 失败 | `pip install pyyaml`。 |
| `oh_root mismatch` | ace_engine 不在 `<OH_ROOT>/foundation/arkui/ace_engine`。用 `deploy_ci.py deploy` 重新部署，勿手改目录。 |
| 接收器启动报 token 缺失 | 非 loopback 监听必须配 token。`WEBHOOK_HOST=0.0.0.0` 时务必先种 `~/.gitcode_webhook_token`。 |

---

文件位置（部署后）：`$OH_ROOT/foundation/arkui/ace_engine/specs/tools/spec_eval/{deploy_ci.py,ci_service.sh,ci_worker.py,ci_runner.py,gitcode_webhook.py,DEPLOYMENT.md}`。
