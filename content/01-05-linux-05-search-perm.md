---
id: 01-05-linux-05-search-perm
no: 5
stage: 1
title: Linux 第 5 课 · 搜索、权限、打包与正则表达式
en: Linux 5 - grep, chmod, tar & Regex
hours: 2
minutes: 60
tags: [Linux, grep, chmod, tar, 正则表达式, sed]
summary: grep 全家用法（-n / -A / -B / -R / -E / zgrep）；mv / cp / find / 软链接 / du；chmod / chown / chgrp 与用户组管理；md5sum / which；tar 打包压缩；:%! 在 vi 里调用命令；正则表达式与 vi 内替换删除；批量注释；课后练习三。
---

## 1. grep：搜索关键字 {#grep}

**语法**：`grep 关键字 文件`。

| 命令 | 作用 |
|---|---|
| `grep 关键字 文件` | 搜索关键字所在的行 |
| `grep -n 关键字 文件名` | 搜索关键字并且**显示行号** |
| `grep -10n 关键字 文件名` | 搜索关键字，**前后各显示 10 行** |
| `grep -A10 关键字 文件名` | 显示关键字**后面** 10 行（After） |
| `grep -B10 关键字 文件名` | 显示关键字**前面** 10 行（Before） |
| `grep -R 关键字 目录/*` | **递归搜索**目录下所有文件（含子目录） |

比如 `/var/logs/` 下有 `a1 a2 a3`、`D1/b1 D2/b2`、`D1/F1/c1` 多层结构，`grep -R error /var/logs/*` 会一层层搜下去，把每个文件里带 error 的行都揪出来。

:::tip 工作使用场景
搜索 log 里面的 error、搜索 rpt 里的内容，全靠 grep。配合下一节的 -A/-B 上下文选项，报错前后的线索一目了然。
:::

## 2. 文件处理：移动 / 复制 / 搜索 {#move}

:::goal grep 常用选项全部掌握；权限数字含义会算会改；tar 打包解压一条龙；正则表达式入门并能在 vi 里实战。
:::

**移动 / 重命名文件 mv**：

```
mv  文件/目录   目录            # 移动
mv  old_name    new_name       # 重命名
```

**复制文件 cp**：

```
cp  -option  文件/目录   保存地址
```

| 选项 | 作用 |
|---|---|
| `-r` / `-R` | 递归复制目录 + 里面所有文件子目录 |
| `-a` | 递归复制、保留权限、时间戳、软链接等全部属性 |
| `-i` | 覆盖文件前询问 y/n，防止误删 |
| `-f` | 强制覆盖，不提示，直接覆盖已有文件 |
| `-n` | 不覆盖已经存在的文件，直接跳过 |

**常用组合**：`cp -rf`（强制递归覆盖，不保留属性）；`cp -rfa`（强制递归覆盖，保留属性）。

**搜索文件/目录 find**：

```
find  路径  -type  f         # 搜索文件
find  路径  -type  d         # 搜索目录
find  路径  -name  名字      # 按名字搜索（如 -name k1）
find  路径  -user  用户名    # 按文件的 owner 搜索
find  路径  -maxdepth 6      # 限制搜索深度
```

**link 软链接的创建**：

```
cd  目的地的目录     # 例如 /proj/NLA
ln  -s  a  b        # 将 a 创建为 link，取名为 b
```

**磁盘空间查看**：`du -sh ~/`，查看自己家目录的空间占用情况。

## 3. 权限的修改 {#chmod}

**数字控制权限**：`r=4　w=2　x=1　-=0`

```
chmod  757  目录/文件
chmod  -R  757  目录      # 递归修改权限（如 a/b/c/d）
```

**字母控制权限**：

```
chmod  u+rwx   目录
chmod  g+rw-x  目录
chmod  o+r-wx  目录
```

**修改所属用户**：

```
chown  用户名  目录/文件名
chown  -R  用户名  目录      # 递归修改
```

**修改所属组**：

```
chgrp  组名  目录
chgrp  -R  组名  目录
```

**创建用户组 / 添加用户到组 / 从组里删除**：

```
groupadd  组名                  # 创建用户组
gpasswd  -a  用户名  组名       # 添加用户到组里
gpasswd  -d  用户名  组名       # 从组里删除用户
```

:::fig linux-16 | 用户与权限管理命令实操
:::

## 4. md5sum / which {#misc}

**md5sum**：检查文件是否发生改动。

```
md5sum  文件名      # 会返回一串 md5 的校验码
```

**which**：快速搜索命令所在位置。

```
which  命令/文件
```

## 5. 打包压缩文件 {#tar}

```
tar  -cvf  包名.tar      需要打包的内容    # 只打包
tar  -czvf 包名.tar.gz   需要打包的内容    # 打包 + 压缩
tar  -tvf  压缩包名                        # 查看包里面有什么内容
tar  -xvf  包名                            # 解压文件
tar  -xvf  datas.tar.gz  -C  A1            # 解压到指定目录下
```

:::fig linux-17 | tar 打包与解压实操
:::

## 6. 去重排序 / 扩展正则 {#sort}

```
sort  -u  文件名          # 去重并排序
grep  -E  正则  文件名     # 使用扩展正则表达式
```

**特殊场景——在 vi 打开文件之后想搜索**：

```
:%!              # 调用 linux 的命令
:%! grep opt     # 过滤，只展示符合要求的内容；按字母 u 撤销
:%! sort -u      # 排序去重
```

:::fig linux-18 | :%! 调用 Linux 命令过滤
:::

**工作使用场景**：搜索 log 里面的 error、搜索 rpt 里面的内容。

**注意**：grep 只能搜索普通文件中的内容；如果文件是压缩格式（如 Place.log.gz），不能使用 grep，要使用 **zgrep**。

## 7. 正则表达式 {#regex}

参考：https://blog.csdn.net/lbyNO_1/article/details/140626397

:::fig linux-19 | 正则表达式速查
:::

### 基本正则表达式实操

1、在家目录下创建目录 `bre_demo`；
2、在 bre_demo 下创建文件 `bre_pt.txt`，输入以下内容：

```
test
tesst
tessssst
tesaaatk
tes1234tk
1213123
atest
```

3、搜索练习：

| 题目 | 正则 |
|---|---|
| 搜索以 a 开头的行 | `^a` |
| 过滤以 3 结尾的行 | `3$` |
| 搜索以 t 开头以 k 结尾的行 | `t.*k` |
| 搜索 tes 后面 2-3 个 a 再接 tk | `tesa\{2,3\}tk` |
| 搜索纯数字的行 | `[0-9]` |
| 搜索不包含字母的行 | `[^a-z]` |
| 搜索空行 | `^$` |
| 搜索 tes 中间 s 出现 3 次以上的行 | `tes\{3,\}` |

:::fig linux-20 | 基本正则表达式实操结果
:::

### 正则表达式进行替换（vi 内）

```
:%s/old/new/g      # 全局替换
:%s/old/new/gc     # 忽略大小写全部替换
:%s/a/b/2          # 只替换匹配到的第二个关键字
:g/正则表达式/d    # 按正则删除行
```

**批量插入**（文件内容如 a1a2a3a4，`^$` 表示空行）：

```
:%s/^/要插入的值 /g    # 在每一行开头插入内容
:%s/$/要插入的值 /g    # 在每一行结尾插入内容
```

### grep 搭配正则表达式

```
grep  -E  "Startpoint|Endpoint|slack"    # 多关键字任一匹配
grep  -E  "b$"                            # 以 b 结尾
```

**应用场景**（在 vi 内）：

```
:%! grep -E "Startpoint|Endpoint|slack"
:%! awk '{print $2}'
:%s/^/ecoAddReapetar /g
:%s/$/ -cells BUFD4LVT/g
```

### 批量注释和取消注释（块处理文本）

**加注释**：`ctrl+v` 进入 block 块模式 → 上下方向键选择区域 → `shift+i` 回到开头行输入 `#` → 按 `esc` 批量应用所有行。

**取消注释**：`ctrl+v` → 方向键选择区域 → 直接按 `d`。

:::fig linux-21 | vi 块模式批量注释
:::

## 动手练：练习三 {#lab}

:::lab grep & 正则表达式练习
1、将 .bash_history 写入到一个文件 demo_003.txt 中
2）在文件外部进行搜索的练习
2.1 搜索文件中是否包含关键字 history
2.2 搜索文件中以 c 开头的行
2.3 搜索文件以 f 结尾的行
2.4 搜索包含 cd 的行，要求显示行号，并且显示 cd 的前后 10 行
2.5 搜索包含字母 abc 的行
2.6 搜索包含数字 0-9 的行
2.7 搜索不包含数字的行
3）在文件内部练习（vi 打开 demo_003.txt）
3.1 在每一行的开头插入内容 test！！！
3.2 在每一行的结尾插入 finish！！！
3.3 在文件内部搜索关键字 demo
3.4 在文件内部搜索所有字母开头的行
3.5 在文件内替换所有 cd 为 KKK
3.6 删除所有 a 开头的行
3.7 删除所有 s 结尾的行
4、在文件内部使用 grep 过滤出所有的 KKK 的行
:::

:::tip 别忘了
alias 的配置（用户自定义快捷指令）写在 `~/.bashrc` / `~/.alias` 里；`source` 命令用来执行脚本，使配置文件生效：`source ~/.bashrc`。
:::

:::quiz
grep 搜关键字并显示它前后各 10 行用哪个选项？| grep -10n 关键字 文件名；-A10 只显示后面 10 行，-B10 只显示前面 10 行。
r w x 的数字分别是什么？| r=4、w=2、x=1。757 = rwx r-x rwx。
cp -r 和 cp -a 的区别？| -r 只递归复制；-a 递归复制且保留权限、时间戳、软链接等全部属性。
tar 打包并压缩用什么参数？| -czvf（c 创建 z 压缩 v 显示过程 f 指定包名）；解压用 -xvf，解压到指定目录加 -C。
压缩过的 log 为什么 grep 搜不了？| grep 只能搜普通文件；压缩文件（如 Place.log.gz）要用 zgrep。
:::

:::check
- grep 的 -n / -A10 / -B10 / -R / -E 用法全部练过
- 会用数字法和字母法改权限，会算 757
- tar 四件套（cvf / czvf / tvf / xvf）一条龙
- 八个基本正则题全部在 bre_pt.txt 上验证过
- 练习三全部完成
:::
