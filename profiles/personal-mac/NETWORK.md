# Cursor 与 Veee 分流

Veee 智能模式只覆盖其支持的网站；模型请求可能因出口地区不同而不可用。本配置保留 Veee 全局模式，在 macOS 系统代理层让常用国内网站直连，并为 Cursor 显式指定本地代理和 HTTP/1.1。它是可选 profile，bootstrap 不会自动改编辑器或网络设置。

## 准备与应用

本人在 Veee 中完成登录、选择可用线路并开启全局模式。账号、订阅、Cookies、App 数据与会话不能提交到 dotfiles；脚本不复制或修改这些内容，也不自动操作 Veee。

[配置文件](./cursor-network.json) 默认使用本地 HTTP 端口 `15236`。核对当前 Veee 端口，再从 dotfiles 根目录预览：

```sh
python3.12 tools/cursor_network.py
python3.12 tools/cursor_network.py --apply
python3.12 tools/cursor_network.py --check
```

HTTP 端口不同则为三条命令都加 `--proxy-url http://127.0.0.1:实际端口`。只接受无凭证的本机 HTTP 代理；不要传 SOCKS 端口、订阅链接或账号。新机自行安装和登录 Veee，不能从旧机搬认证数据。

默认网络服务为 `Wi-Fi`；有线网络先运行 `networksetup -listallnetworkservices`，再使用 `--network-service "实际服务名称"`。系统已有代理须指向当前 Veee；脚本只合并绕过规则，不开启、改写或关闭系统 HTTP/SOCKS 代理。

Cursor 只合并四个键：禁用 HTTP/2、代理地址、`http.proxySupport = override` 和 `http.proxyStrictSSL = true`。其他编辑器设置保留；有 JSONC 注释或非标准 JSON 时停止，手动合并这四个键，避免丢失注释。`--apply` 会备份原文件、保存部分完成状态并读回两处配置；重复应用没有改动时不创建新备份。

绕过列表保留已有条目，追加本地地址、`.cn` / 中国域名及百度、QQ、B 站、淘宝、天猫、京东、支付宝、抖音、小红书、美团。可先审查并编辑 profile 的 `bypass_domains`；删除 profile 中的条目不会自动删除机器上已存在的规则。

## 读回与使用验收

`--check` 检查 Cursor 键、绕过规则及代理端口是否可连接，不读取 Veee 账号，也不证明模型或地区资格。Veee 仍须在 App 中确认全局模式和线路。

```sh
networksetup -getproxybypassdomains Wi-Fi
scutil --proxy
curl --noproxy '' --proxy http://127.0.0.1:15236 \
  --connect-timeout 8 --max-time 15 https://www.cloudflare.com/cdn-cgi/trace
```

最后一个请求是可选联网诊断，会显示公网 IP；输出只留本机，不提交到仓库。出口地区成功也不等于某个模型必然可用。按 [Cursor 地区说明](https://cursor.com/docs/account/regions) 检查提供商资格；本人在 Cursor 发一个有界真实请求验收。仍使用旧连接时先保存任务，再完全退出和重开 Cursor。

HTTP/1.1 主要适用于 Chat / Agent；HTTP/2-only 功能不在此保证范围。流式连接按 [Cursor 官方网络诊断](https://cursor.com/docs/enterprise/network-configuration) 检查，始终保留 TLS 证书校验，不通过删除缓存、账号或内部 feature gate 修复。

这不是完整 GeoIP 或进程分流：名单外的国内 `.com` 网站可能仍走代理；显式使用 `HTTP_PROXY` / `ALL_PROXY` 的终端工具不一定读取系统绕过列表。VPN 重连、App 升级或切换网络后先 `--check`，有漂移再预览和 `--apply`；不添加后台轮询或偷偷重启任务。

## 回滚

应用返回的 receipt 位于当前 home 的 `~/.local/state/dotfiles/network/`，备份只留本机，目录权限为 700、备份和 receipt 为 600：

```sh
python3.12 tools/cursor_network.py --rollback /实际路径/receipt.json
python3.12 tools/cursor_network.py --rollback /实际路径/receipt.json --apply
```

回滚先核对当前配置与原/新快照；发现后续修改则拒绝覆盖。应用中断也用同一个 receipt 检查部分完成状态。回滚只恢复本次编辑器设置和绕过规则，不退出 Veee、不删除账号或会话，也不改系统代理开关。新机备份没有跨设备恢复含义。
