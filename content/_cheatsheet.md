---
title: 命令速查
summary: 按工具分组的常用命令。写脚本时不用翻课文，搜这一页就够。
---

## Linux：文件与目录 {#linux-file}

| 命令 | 作用 | 常用写法 |
|---|---|---|
| `pwd` | 我在哪个目录 | `pwd` |
| `ls` | 列出目录内容 | `ls -l`（详细）`ls -a`（含隐藏）`ls -lh`（人读大小） |
| `cd` | 切目录 | `cd ~`（回家）`cd ..`（上一层）`cd -`（回上一个目录） |
| `mkdir` | 建目录 | `mkdir -p a/b/c`（逐级建） |
| `cp` | 复制 | `cp -r dir1 dir2`（递归） |
| `mv` | 移动/改名 | `mv a.tcl b.tcl` |
| `rm` | 删除 | `rm -rf work/`（危险，确认再敲） |
| `cat` | 看整个文件 | `cat file.log` |
| `head` / `tail` | 看头/尾 | `head -n 20 f` `tail -n 50 f` `tail -f f`（跟读日志） |
| `chmod` | 改权限 | `chmod +x run.sh` `chmod 755 run.sh` |
| `find` | 找文件 | `find . -name "*.rpt"` |
| `du` / `df` | 目录大小 / 磁盘剩余 | `du -sh *` `df -h` |

## Linux：文本处理（后端最常用的四个）{#linux-text}

| 命令 | 作用 | 例子 |
|---|---|---|
| `grep` | 按内容找行 | `grep -n VIOLATED timing.rpt`（带行号）`grep -c`（计数）`grep -v`（反选）`grep -i`（忽略大小写） |
| `sed` | 替换 / 取行 | `sed 's/old/new/g' f` `sed -n '10,20p' f` |
| `awk` | 按列取数 | `awk '{print $1, $3}' f` `awk -F: '{print $1}' f` `awk '$2 < 0'` |
| `sort` / `uniq` | 排序 / 去重 | `sort -k2 -n f` `sort -nr f` `uniq -c` |
| `wc` | 计数 | `wc -l f`（多少行） |
| `cut` | 按分隔符取列 | `cut -d/ -f2 f` |
| `tr` | 字符转换 | `tr a-z A-Z` |

:::tip 管道的思维模型
`a | b` = 把 a 的输出当作 b 的输入。后端读报告几乎都是这个套路：

```bash
grep "slack" timing.rpt | awk '{print $3}' | sort -n | head -3
# 取出所有 slack 值 -> 按数值排序 -> 看最小的三个
```
:::

## Linux：进程与环境 {#linux-proc}

| 命令 | 作用 |
|---|---|
| `ps -ef \| grep icc2` | 看工具还在不在跑 |
| `top` / `htop` | 看 CPU / 内存占用 |
| `kill -9 PID` | 强杀进程 |
| `env` / `echo $VAR` | 看环境变量 |
| `export A=1` | 设环境变量（bash） |
| `setenv A 1` | 设环境变量（tcsh） |
| `which icc2_shell` | 命令在哪 |
| `nohup ... &` | 后台跑，断开 SSH 也不停 |
| `2>&1 \| tee log` | 屏幕和文件同时留 |

## Tcsh：与 bash 的差异 {#tcsh}

| 动作 | bash | tcsh |
|---|---|---|
| 设变量 | `export A=1` | `setenv A 1` |
| 设 shell 变量 | `A=1` | `set A = 1` |
| 引用变量 | `$A` | `$A`（setenv）/ `$A`（set） |
| 循环 | `for i in 1 2 3; do ...; done` | `foreach i (1 2 3) ... end` |
| 条件 | `if [ -f x ]; then ...; fi` | `if ( -f x ) then ... endif` |
| 别名 | `alias ll='ls -l'` | `alias ll 'ls -l'` |
| 取上条命令参数 | `!!:$` | `!$` |
| 脚本首行 | `#!/bin/bash` | `#!/bin/tcsh -f` |

## 综合：Design Compiler {#dc}

| 命令 | 作用 |
|---|---|
| `read_verilog x.v` | 读 RTL |
| `current_design top` | 指定顶层 |
| `link` | 把网表和库绑起来（有 unresolved 会报） |
| `source x.sdc` | 读约束 |
| `compile_ultra` | 综合（高质量） |
| `report_timing` / `report_area` / `report_power` | 报告 |
| `write -f verilog -hierarchy -output net.v` | 出网表 |
| `write_sdc x.sdc` | 出约束（给 PR 用） |
| `write_svf x.svf` | 出引导文件（给 FM 用） |

## 时序签核：PrimeTime {#pt}

| 命令 | 作用 |
|---|---|
| `read_verilog net.v` | 读网表 |
| `read_parasitics -format SPEF x.spef` | 读寄生（带真实 RC） |
| `read_sdc x.sdc` | 读约束 |
| `report_timing -max_paths 20 -significant_digits 4` | setup 报告 |
| `report_timing -delay_type min` | hold 报告 |
| `report_qor` | WNS/TNS/面积/功耗汇总 |
| `report_timing -unconstrained` | 找漏约束的路径 |
| `fix_eco_timing -type hold -methods {insert_buffer}` | 生成 ECO 建议 |
| `write_changes -format icctcl -output eco.tcl` | 导出 ECO 脚本 |

## 等价性：Formality {#fm}

| 命令 | 作用 |
|---|---|
| `read_verilog -container r -libname WORK {rtl.v}` | 读参考设计（RTL） |
| `read_db lib.db` | 读库 |
| `set_top top` | 指定顶层 |
| `read_svf x.svf` | 读引导文件（关键） |
| `verify` | 验证 |
| `report_status` | 看通过/失败点数 |

## 布局布线：ICC2 {#icc2}

| 命令 | 作用 |
|---|---|
| `open_lib work` / `open_block top` | 打开库与 block |
| `read_verilog net.v` / `link_design` | 读网表并链接 |
| `create_placement -effort high` | 布局 |
| `legalize_placement` | 合法化（去重叠） |
| `refine_placement` | 局部再优化 |
| `clock_opt -only_cts` / `clock_opt` | 时钟树 / 时钟树+优化 |
| `route_auto` | 全局+详细布线 |
| `route_detail -incremental true` | 增量布线（修 DRC） |
| `route_opt` | 布线后优化（需寄生信息） |
| `place_opt` | 布局同时优化时序（需时序库） |
| `check_routes` | DRC 检查 |
| `report_qor` / `report_timing` | 报告 |
| `write_parasitics -format SPEF -output x.spef` | 出 SPEF |
| `write_verilog` / `write_def` / `write_gds` | 出交付物 |
| `save_block` | 存盘 |

## 布局布线：Innovus {#innovus}

| 命令 | 作用 |
|---|---|
| `read_netlist` / `read_lef` / `read_libs` / `read_sdc` | 读输入 |
| `init_design` | 初始化 |
| `floorPlan -site ... -d ...` | 布局规划 |
| `place_opt_design` | 布局+优化 |
| `ccopt_design -cts` | 只建时钟树 |
| `optDesign -postCTS` / `-postCTS -hold` | 树后优化 / 修 hold |
| `routeDesign` | 布线 |
| `optDesign -postRoute` | 布线后优化 |
| `addFiller` / `addMetalFill` | 收尾填充 |
| `saveDesign x.enc` / `restoreDesign x.enc` | 存/取 |
| `report_timing` / `report_area` / `reportCongestion` | 报告 |

## 物理验证 {#pv}

| 工具 | 命令 | 作用 |
|---|---|---|
| Calibre | `calibre -drc rules.cal` | DRC |
| Calibre | `calibre -lvs rules.cal` | LVS |
| KLayout | `klayout -b -r drc.lydrc` | 开源 DRC（本课程用这个） |
| ICC2 | `check_lvs` / `check_routes` | 工具内检查 |

## 版本与自动化 {#git}

| 命令 | 作用 |
|---|---|
| `git init` / `git status` | 初始化 / 看状态 |
| `git add f` / `git commit -m "why"` | 暂存 / 提交 |
| `git log --oneline` / `git diff` | 看历史 / 看改动 |
| `git checkout HEAD~1 -- f` | 单文件回退（覆盖当前改动！） |
| `git checkout -b exp` / `git merge exp` | 开分支 / 合并 |
| `git tag v1.0` | 打标签（标记可签核版本） |
| `make` / `make pnr` / `make clean` | 跑流程 / 跑到某步 / 清理 |
