# IC 后端学院 · 交互式学习平台

线上地址：**https://ic.feice.net**

一个可部署的前后端学习站：课程目录在左侧，每一课是一组可交互的章节；进度通过匿名设备 ID 同步到服务端。

---

## 目录结构

```
catalog.json              课程总清单（唯一数据源：课程/章节/顺序/状态）
web/
  home.html               首页模板（构建时生成 web/index.html）
  assets/
    platform.css          平台外壳样式
    platform.js           目录 / 进度 / 搜索 / iframe 章节桥
    lesson-bridge.js      课程页接入平台用的桥接脚本
  lessons/<id>/index.html 课程内容页（纯前端，可独立打开）
  lesson/<id>/index.html  课程壳页面（构建产物，iframe 承载内容）
  data/catalog.json       构建产物，供 /api/catalog 读取
server/
  app.py                  FastAPI：目录 / 进度 / 笔记 / 统计 + 静态托管
deploy/
  icacademy.service       systemd 单元
  ic.conf                 nginx 站点（HTTPS + 反代 8710）
  ic-cert-sync.sh         证书续期后同步到 nginx 并 reload
tools/
  build.py                构建静态站点
  deploy.py               打包上传 + 重启服务
  ingest_ppt.py           把 PPTX/PDF 拆成课程素材
  remote.py               极简 SSH 执行/上传（凭据读 .deploy.env）
```

## 架构要点

- **外壳与内容分离**：`lesson/<id>/index.html` 只负责导航与进度，内容在 iframe 里。
  课程页只要引入 `lesson-bridge.js` 并暴露 `window.ICLAB = { chapters, go(id), ready }`，
  就能被平台目录驱动、并把完成情况回传给平台。所以新课可以用任何技术写。
- **进度**：本地 `localStorage` 即时生效，服务端 SQLite 汇总；断网时排队，联网后补传。
- **免登录**：首次访问生成 `icl.uid`，用于跨浏览器恢复进度；不需要账号体系。

## 加一课（三步）

1. **拆素材**
   ```bash
   python tools/ingest_ppt.py "课件.pptx" 03-sta
   ```
   产物在 `web/lessons/03-sta/src/`：`slides/`、`text.txt`、`outline.json`、`REPORT.md`。
   截图型课件（无文字层）需要逐页识别后再编排内容。

2. **写内容** `web/lessons/03-sta/index.html`
   - 章节用 `<section class="ch" id="...">`，同一时间只显示一个；
   - 页尾加桥接：
     ```html
     <script src="../../assets/lesson-bridge.js"></script>
     ```
   - 若章节不是 `#nav a[data-go]` 结构，自己实现：
     ```js
     window.ICLAB = { chapters: [{id:'intro', title:'…'}], ready: true, go(id){ /* 切章节 */ } };
     ```

3. **登记 + 构建 + 发布**
   - 在 `catalog.json` 里把该课的 `status` 改成 `live`，补上 `chapters`（`id` 必须与页面里的章节 id 一致）；
   - `python tools/build.py`；
   - `python tools/deploy.py`。

> 平台的左侧目录、搜索、进度统计全部由 `catalog.json` 驱动，不需要改代码。

## 部署

```bash
cp .deploy.env.example .deploy.env   # 首次：填入服务器地址 / 账号 / 密码（该文件不入库）
python tools/build.py     # 生成 lesson/*/index.html 与 index.html
python tools/deploy.py    # 打包上传到 /home/weizhen/icacademy 并重启服务
```

服务器（Oracle Linux 9 / aarch64）：

| 项 | 值 |
|---|---|
| 应用目录 | `/home/weizhen/icacademy` |
| 运行时 | `venv/bin/uvicorn`，监听 `127.0.0.1:8710` |
| 服务 | `systemctl status icacademy` |
| 反向代理 | `/etc/nginx/conf.d/ic.conf` |
| 证书 | acme.sh（ECC），续期后由 `/usr/local/bin/ic-cert-sync.sh` 同步并 reload |
| 数据 | `data/app.db`（SQLite，进度 + 笔记） |

**SELinux 注意**：从 home 目录执行二进制会被拒绝（`203/EXEC`）。部署脚本已对
`venv/bin` 打 `bin_t` 标签；若重建 venv，需要重新执行：

```bash
sudo chcon -R -t bin_t /home/weizhen/icacademy/venv/bin
```

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查 |
| GET | `/api/catalog` | 课程清单 |
| GET | `/api/progress/{uid}` | 拉取某设备已完成的章节 |
| POST | `/api/progress` | 批量上报 `{uid, items:[{lesson,chapter,done}]}` |
| DELETE | `/api/progress/{uid}` | 清空该设备进度 |
| GET/PUT | `/api/notes/{uid}/{lesson}` | 课后笔记 |
| GET | `/api/stats` | 学习者数 / 完成条目数 |
| GET | `/api/docs` | OpenAPI 文档 |

## 内容进度

| 课 | 主题 | 状态 |
|---|---|---|
| 01 | IC 后端设计全景（8 章：流程 / 排序 / 文件 / PPA 沙盘 / 签核 / 术语 / 测验） | 已上线 |
| 02 | VCS × Verdi 验证与调试（13 章，含终端、DVE、Verdi 模拟器） | 已上线 |
| 03 | 静态时序分析 STA | 待课件 |
| 04 | 布局布线实战 | 待课件 |
| 05 | 低功耗设计 | 待课件 |
| 06 | 物理验证与 Signoff | 待课件 |
