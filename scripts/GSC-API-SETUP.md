# GSC API 实时数据接入 — 设置指南

> 按以下 5 步操作后，我就能直接拉取你的 Search Console 数据，替代手动截图。

---

## Step 1：创建 Google Cloud 项目

1. 打开 [https://console.cloud.google.com](https://console.cloud.google.com)
2. 顶部点 **Select a project** → **New Project**
3. 项目名：`suppbridge-seo`（任意名称都可以）
4. 记下 **Project ID**（之后会用到）

---

## Step 2：启用 Search Console API

1. 在 Cloud Console 左侧菜单 → **APIs & Services** → **Library**
2. 搜索 `Google Search Console API`
3. 点击 → **Enable**

---

## Step 3：创建 Service Account

1. 左侧菜单 → **APIs & Services** → **Credentials**
2. 顶部点 **+ Create Credentials** → **Service Account**
3. Service account name: `gsc-reader`
4. Service account ID: 自动生成即可
5. 点 **Done**（不需要添加角色）

---

## Step 4：生成 JSON 密钥

1. 在 Credentials 页面，找到刚创建的 Service Account
2. 点它的邮箱地址进入详情页
3. 点 **Keys** 标签 → **Add Key** → **Create New Key**
4. 选 **JSON** → **Create**
5. 会自动下载一个 `.json` 文件

**把下载的 JSON 文件发给我**（或放到项目里），路径为：
```
scripts/gsc-service-account.json
```

⚠️ 这个文件包含密钥信息，已加入 `.gitignore`，不会被推送到 GitHub。

---

## Step 5：在 GSC 中授权 Service Account

1. 打开 [https://search.google.com/search-console](https://search.google.com/search-console)
2. 选择 `suppbridge.com` 属性
3. 左侧菜单 → **Settings**（设置）
4. 点 **Users and permissions**（用户和权限）
5. 点 **Add user**
6. 粘贴 Service Account 的邮箱（类似 `gsc-reader@suppbridge-seo.iam.gserviceaccount.com`）
7. 权限选择 **Full**（完整）— 需要这样才能查看搜索分析数据
8. 点 **Add**

---

## 验证

设置完成后告诉我，我运行以下命令验证：

```bash
cd scripts
pip install google-auth google-api-python-client
python3 gsc-fetcher.py --full
```

成功后会输出类似：
```
INDEX STATUS REPORT
  Homepage .......... Submitted and indexed

SEARCH PERFORMANCE (last 28 days)
  Total Clicks .... 12
  Total Impressions. 340
  Avg CTR ......... 3.5%
  Avg Position .... 18.2

SITEMAP STATUS
  https://suppbridge.com/sitemap.xml
    Submitted: 2026-06-08
    Indexed: 2
```

---

## 后续自动化

一旦接入成功，我会：
1. **每日 SEO 监控** 改用真实 GSC 数据，不再只做 HTTP 检查
2. **每周博文** 基于真实搜索查询来选题（而非"推测"）
3. **月度趋势图** 展示 impressions/clicks/CTR 增长曲线
