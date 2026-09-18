# GSC API 接入 — 设置指南（V2.3 P2.0 版）

> 按下面 5 步做完，`seo-intel` 的每日同步就能开始落库。
> 全部做完之前，fetcher 会以 `status='skipped'` 记录并正常退出 —— 不会伪造数据，也不会每天晚上报错。

---

## 关键变化（对比上一版）

| | 旧版 | 现在 |
|---|---|---|
| GSC 属性 | URL 前缀 `https://www.suppbridge.com/` | **域属性 `sc-domain:suppbridge.com`**（一次覆盖 `suppbridge.com` 与 `www.suppbridge.com`） |
| 密钥位置 | `scripts/gsc-service-account.json`（仓库内） | **`/etc/suppbridge/seo-intel/gsc-service-account.json`**（仓库外，600） |
| 产出 | 打印到终端 + 缓存 JSON | **校验后写入 `seo_intel` 库**，每次运行留 `seo_runs` 审计行 |

仓库里**不再放任何密钥**。旧路径仅作为兼容回退保留，一旦被使用脚本会打印警告。

---

## Step 1：创建 Google Cloud 项目

1. 打开 <https://console.cloud.google.com>
2. 顶部 **Select a project** → **New Project**
3. 名称建议 `suppbridge-seo`，记下 Project ID

## Step 2：启用 Search Console API

1. **APIs & Services** → **Library**
2. 搜索 `Google Search Console API` → **Enable**

## Step 3：创建 Service Account

1. **APIs & Services** → **Credentials** → **+ Create Credentials** → **Service Account**
2. 名称 `gsc-reader` → **Done**（无需分配 GCP 角色）

## Step 4：生成 JSON 密钥并放到服务器（仓库外）

1. 进入该 Service Account 详情 → **Keys** → **Add Key** → **Create New Key** → **JSON**
2. 浏览器会下载一个 `.json`。**把它直接放到服务器上**，不要放进仓库：

```bash
sudo install -d -m 700 -o jun -g jun /etc/suppbridge/seo-intel
sudo install -m 600 -o jun -g jun ~/Downloads/<下载的文件>.json \
  /etc/suppbridge/seo-intel/gsc-service-account.json
sudo rm ~/Downloads/<下载的文件>.json        # 别留在下载目录
```

校验：

```bash
sudo ls -l /etc/suppbridge/seo-intel/gsc-service-account.json   # 应为 -rw------- jun jun
```

## Step 5：在 GSC 中授权该 Service Account（域属性）

1. 打开 <https://search.google.com/search-console>
2. 选择 **`suppbridge.com`** 属性 —— 确认类型是 **Domain property**（不是 URL 前缀）
3. 左侧 **Settings** → **Users and permissions** → **Add user**
4. 粘贴 Service Account 邮箱（形如 `gsc-reader@suppbridge-seo.iam.gserviceaccount.com`）
5. 权限选 **Full**（只读权限看不到完整的 Search Analytics）
6. **Add**

> 域属性同样支持 Service Account。旧版脚本注释里"域属性不支持 SA"的说法是错的，
> 当时的问题在于属性本身没验证，而不在于属性类型。

---

## 验证

```bash
cd ~/Harness/seo-intel/backend

# 1) 建表（幂等，可重复执行）
venv/bin/python gsc-fetcher.py --init-db

# 2) 先干跑：只抓取与校验，不写库
venv/bin/python gsc-fetcher.py --dry-run

# 3) 正式首次同步：过去 7 天
venv/bin/python gsc-fetcher.py
```

成功时输出 GSC connection / 属性 / 日期区间 / 行数 / 页面数 / 查询数 / clicks / impressions，
以及前 20 条明细。

凭据缺失时输出：

```
GSC connection: BLOCKED
No service-account credentials found.
```

并写入一行 `seo_runs(status='skipped')`。想让它硬失败（例如放进 CI）就加 `--strict`。

---

## 落库后的检查

```bash
docker exec slh-postgres psql -U slh -d seo_intel -c \
  "SELECT status, rows_fetched, rows_written, rows_rejected, started_at
     FROM seo_runs ORDER BY started_at DESC LIMIT 5;"

docker exec slh-postgres psql -U slh -d seo_intel -c \
  "SELECT count(*) FROM seo_gsc_daily;"
```

---

## 自动化

已装 `seo-intel-gsc-sync.timer`（systemd 用户单元），每天同步一次。

```bash
systemctl --user list-timers seo-intel-gsc-sync.timer
systemctl --user start seo-intel-gsc-sync.service   # 手动跑一次
tail -n 40 ~/Harness/seo-intel/data/logs/gsc-sync.log
```

刻意**没有**建：crawler、opportunity engine、AI advisor、week/month 报表 —— 那些属于 P2.1+。
