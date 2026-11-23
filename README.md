# IC 后端学院 v2（ic.feice.net）

面向**零基础**的 IC 数字后端课程站点，按《数字中后端课程表》9 阶段 113 学时组织。当前已上线：**阶段一 Linux 占位规划 + TCL 基础和编程 6 课（浏览器内 Tcl 练习台 + 独立练习场，内置 JS 版 Tcl 解释器）**，其余阶段按课表占位、逐阶段上线。

- 线上：https://ic.feice.net
- 设计说明（原站点评 + 课纲映射 + 本轮补齐清单）：见 `DESIGN.md`
- 写作规范（八段结构、深度指标、代码注释要求）：见 `tools/WRITING_SPEC.md`
- 课程体检（结构/密度/注释/术语/题量逐课打分）：`python tools/audit.py`
- 服务器：`132.226.110.78` → `/home/weizhen/icacademy`，systemd 服务 `icacademy`，nginx 反代 8710

## 当前规模（`tools/audit.py` 实测）

| 指标 | 数值 |
|---|---|
| 课程 / 章节 | 15 / 43（阶段一正文 + 其余阶段规划页） |
| 学时 | 课表 113（阶段一 Linux 12 + TCL 6 已上线） |
| 自测题 | 44 道 |
| Tcl 练习台 | 课程内嵌 :::tclrun 一键运行 + /playground/ 独立练习场 |
| 解释器 | web/assets/tcl.js：60+ 用例回归测试通过，报错对齐真实 tclsh |

## 目录

```
content/                课程内容（唯一数据源，一课一个 .md）
content/_cheatsheet.md  命令速查页（下划线开头：不进课程目录，单独成页）
tools/build.py          构建：md → 课程页 / 首页 / 5 个子页面 / 4 份 JSON 数据
tools/deploy3.py        部署：构建 → 打包 → 8KB 分块上传 → 原子切换（推荐）
tools/deploy.py         旧版部署（大块上传，链路不稳时会失败）
web/assets/app.css      统一外壳样式（浅色，长文阅读优先）
web/assets/app.js       课程页交互：进度 / 目录 / 术语卡 / 自测 / 复制 / 笔记
web/assets/page.js      子页面交互：题库 / 术语表 / 搜索 / 进度看板
web/assets/shell.js     浏览器内模拟终端（虚拟文件系统 + 30 多个命令）
web/assets/tcl.js       浏览器内 Tcl 解释器（课程全部命令 + EDA 命令桩）
server/app.py           线上服务：FastAPI + SQLite（/api/progress、/api/notes）
deploy/                 nginx 反代、systemd unit、证书同步
web/lesson/<id>/        构建产物（不要手改，会被覆盖；已随仓库提交，便于直接托管）
```

## 从仓库开始

```bash
git clone https://github.com/flytestai/icdesign.git
cd icdesign
python tools/build.py                     # 只依赖 Python 3，无第三方库
cd web && python -m http.server 8713      # http://127.0.0.1:8713/
```

改了 `content/*.md` 或 `tools/build.py` 之后重新构建，再把 `web/` 一起提交——生成的页面随仓库走，克隆下来就能直接看。

## 写一课

`content/` 下新建 `.md`：

```markdown
---
id: 03-13-xxx          # 目录名，建议 阶段-序号-英文
no: "36"               # 显示编号（可用 tools/_renumber.py 批量重排）
stage: 3               # 阶段 0~9
title: 课名
en: English Title
hours: 3
minutes: 40
tags: [标签1, 标签2]
summary: 一句话说清这一课解决什么问题（会显示在首页与课头）
status: live           # draft = 不构建
---

## 章节标题 {#anchor}

正文……

:::goal 一句话目标
:::scene 场景标题
:::term English | 中文
:::pitfall 坑标题
:::lab 动手标题
:::quiz
问题|答案
:::
:::check
- 过关项
:::
```

块必须以单独一行 `:::` 结束。`:::term` 自动进术语表，`:::quiz` 自动进题库，章节正文自动进搜索索引。

## 构建与部署

```bash
python tools/build.py                 # 只构建，产物在 web/
ICL_PASS=*** python tools/deploy3.py  # 构建并部署（推荐）
ICL_PASS=*** python tools/deploy3.py --no-build   # 只部署现有 web/
```

构建输出会打印课数 / 章数 / 题数 / 术语数；部署会做 md5 校验、解到 `site_new` 后原子切换，失败不会让站点空白。

## 本地预览

```bash
cd web && python -m http.server 8713 --bind 127.0.0.1
# 打开 http://127.0.0.1:8713/
```

注意：本地静态服务没有 `/api/*`（进度同步、笔记会走本机缓存兜底），线上才有。
