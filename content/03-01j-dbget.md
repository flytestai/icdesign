---
id: 03-01j-dbget
no: 31j
stage: 3
title: dbGet：从对象关系查找宏实例
en: Innovus Legacy Database Queries
hours: 0
tags: [Innovus, dbGet, Tcl, 数据库]
summary: 用对象路径和回溯定位宏实例，判断空结果，并区分数据库读取与状态修改。
---

## 先画对象关系，再写查询 {#objects}

:::fig innovus-practice-j.svg | 原创教学示意图 · dbGet：筛选的位置不等于返回的对象
:::

:::note 原创专题
本讲参考钉钉目录第 14 项的主题独立编写，不转载原文、图或项目参数。实例名、报告和验收数据均为合成。Innovus legacy `dbGet` 命令用于讲解查询思路，未在 Innovus 中实测，属性名和选项以本机版本帮助为准。
:::

先区分**实例**和**库单元**。`top` 指当前顶层设计；`top.insts` 是实例集合；实例的 `name` 是设计中的名字，实例的 `cell` 则指向所引用的库单元。一个库单元可以被多个实例引用。核对宏的放置数量时，计数单位是实例；核对设计用了几种宏时，计数单位才是库单元类型。前者可以发现漏放一份宏，后者无法发现漏掉一个同型号的副本。

```text
                         +--> inst: u_sram0 --+
top: core_demo -- insts -+--> inst: u_sram1 --+--> cell: SRAM_TINY --> baseClass: block
                         +--> inst: u_buf --------> cell: BUFX2 -----> baseClass: core
```

读取链条时，给每一段标注它返回的是对象还是值：`insts`、`cell` 指向对象，`name`、`baseClass` 是属性值。GUI 里看到的一个名字也可能来自层级、实例或母版。先确定交付物每行代表什么，再选具体属性，避免在导出后用去重掩盖对象选错的问题。

## 查询宏实例：筛选属性，再回溯 {#macro-query}

示例用 `baseClass == block` 界定本练习的宏。先读全部实例名判断当前范围，再检查设计中确实存在该类别；最后沿库单元属性筛选并回到实例层。不要把“项目要盘点的宏”直接等同于数据库的某个值：真实项目还可能需要按母版清单纳入或排除特定单元。

```tcl
dbGet top.insts.name
dbGet top.insts.cell.baseClass
set blocks [dbGet -p2 top.insts.cell.baseClass block]
set macroNames {}
foreach inst $blocks {
    if {$inst eq "0x0"} { continue }
    set name [dbGet ${inst}.name]
    if {$name eq "" || $name eq "0x0"} {
        error "macro instance name unavailable: $inst"
    }
    lappend macroNames $name
}
puts [lsort $macroNames]
```

`-p` 回溯一层：在这个路径上返回库单元对象；`-p2` 回溯两层，返回引用这些库单元的实例对象。**在哪一层筛选，与要返回哪一层，是两件事。** `lsort` 只让清单顺序稳定，不能去掉错误重复项；若报告出现重复实例名，应先核查作用范围以及名字是不是真正的全名，而不是默默压成一行。

## 空结果不等于设计里没有宏 {#empty-results}

将“工具报错”“查询成功但无匹配”“核对完成后确实没有宏”分成三种状态。报错优先检查设计是否加载、路径和属性是否受本机版本支持，不能捕获错误后输出一份看似正常的空清单。无匹配先检查 `top.insts` 和实际类别分布，再用一个已知的实例名反查母版与类别。已知宏也找不到时，先核对设计快照、层级范围和名字匹配方式；实例找得到但不属 `block` 时，再跟目录维护者确认分类标准。

Tcl 的 `llength 0x0` 是 `1`，但 `0x0` 是空指针标记，不能认作一个实例。若报告显示零行，仍应保留快照标识、基准实例总数及类别检查结果，让复核者能分辨“有效的零”和“漏查”。设计查询和 `puts` 不修改数据库，别为排查混入 `dbSet` 等写操作。类似的端口读取见 [Floorplan 实操](/lesson/03-01a-flp-lab/#ports)。

## 实验输入：实例清单为什么少了一行？ {#lab-input}

练习从交接表开始：`F07` 快照内有三条实例记录，宏清单应列出 `u_sram0`、`u_sram1`，两者母版均为 `SRAM_TINY`，另有 `u_buf` 引用 `BUFX2`。旧脚本的导出只有一行 `SRAM_TINY`，列名却是“宏实例”，导致下游只登记了一个放置对象。另提供 `F06_stdonly` 对照快照，里面只有 `u_buf`，预期宏清单为空。两个快照分开判读，不能拿对照快照的零行解释 `F07` 的缺行。

操作顺序：先写出交接表的预期实例名，再核对旧脚本查询从哪个对象取 `.name`。然后分别列出全部实例、筛中库单元和筛中实例，记下每一步的对象粒度。旧结果不一定是筛选失败：它筛对了类别，但错把母版当成交付对象，随后对母版名称去重，只剩一行。这条证据比“重新运行一次得到两行”更能说明根因。

## 本地练习：只用 Tcl 复现清单差异 {#lab-tcl}

下方是可单独交给 `tclsh` 的教学 mock，只依赖标准 Tcl。它用三列记录模拟对象引用，不调用 Innovus，也不模拟 `dbGet` 的语法、空指针或真实数据库结构。`legacy` 模拟旧导出对母版去重，`fixed` 模拟修正后取实例名；两者看相同的原始输入。

```tcl
proc inventory {rows} {
    set legacy {}
    set fixed {}
    foreach row $rows {
        lassign $row inst cell baseClass
        if {$baseClass ne "block"} { continue }
        lappend legacy $cell
        lappend fixed $inst
    }
    return [list [lsort -unique $legacy] [lsort $fixed]]
}
set f07 {{u_buf BUFX2 core} {u_sram0 SRAM_TINY block} {u_sram1 SRAM_TINY block}}
set f06 {{u_buf BUFX2 core}}
foreach {snapshot rows} [list F07 $f07 F06_stdonly $f06] {
    lassign [inventory $rows] legacy fixed
    puts "$snapshot legacy=[list $legacy] ([llength $legacy]) fixed=[list $fixed] ([llength $fixed])"
}
```

阅读输出时先对清单再对数量。即使新版凑巧输出两条，如果第二条属于其他实例，还是不合格。可把对照中的 `u_buf` 换成一个类别同为 `block` 的测试记录，再预测新旧两种输出；这只是改变 mock 输入，不代表生产数据库或真实工艺属性发生变化。

## 对照验收与回退清单 {#lab-verify}

```text
合成验收预期                     旧列值 (数量)          新列值 (数量)
F07: 宏实例清单                  SRAM_TINY (1)         u_sram0 u_sram1 (2)
F06_stdonly: 宏实例清单          <空> (0)              <空> (0)
F07: 输入实例总数                3                     3
F06_stdonly: 输入实例总数        1                     1
```

验收时再随机挑一个输出实例反查母版：这里两条均指向 `SRAM_TINY`，所以一套完整的交接记录可以同时包含“两个宏实例”和“一种宏母版”，但不能把这两个统计字段互换。另检查排序、列名和上一版消费脚本的读取方式；若下游确实要的是唯一母版列表，应保留原口径并另交付实例清单，而不是让同名字段悄悄变义。

- 改动前：保留旧查询、导出、所用设计标识和预期清单，确认它们不是来自不同快照。
- 改动后：同快照双跑，保留准确名单、错误输出和有效零结果；确认 `u_buf` 没混入宏清单。
- 若实例范围或下游契约未获确认：撤回新导出，恢复原查询版本并标注原口径的已知缺陷，暂停用旧结果做放置判断。这里只更改脚本与报告，无需回滚物理设计。

## 扩展排查：清单对不上时从哪里下手？ {#lab-triage}

在实际交接中，可以把预期和实际清单并列，标出“只在预期”“只在实际”和“双方都有但母版不同”三类差异。第一类优先确认快照标识、设计名和层级范围；第二类复核筛选条件是否把交接表未纳入的单元类型也抓进来；第三类检查实例是否被合法换版，以及工程清单的母版列是否尚未更新。这三类证据指向不同责任方，不能用一句“数量差一”代替。也不要拿同名但不同层级的对象凑齐清单；若数据库返回的名称和交接表层级表示不同，应先明确各自的命名规则，再对照一条实际对象记录。

对象引用适合留在当前工具查询中，不宜作为跨快照的交接主键；清单至少应带上设计标识、实例名称和母版名称。对于本例，可以借 `F06_stdonly` 测空清单，再使旧脚本和新脚本在 `F07` 看同一份输入：前者检查正常的零行不会被误报为故障，后者检查同一母版的多个实例不会被折叠。若交接表本身有错，先修订预期并让责任人确认，再回到实例查询验收，不要为了让结果看起来对齐而改筛选。

## 自检：你数的是哪一层对象？ {#review}

:::quiz
两个 SRAM 实例引用同一母版，筛选后为什么不能停在 -p？| 在该查询路径上，-p 返回库单元层；需用 -p2 返回实例层，再读取各实例的 name。
查询返回 0x0，为什么不能把 Tcl 列表长度记作宏数量？| 0x0 是空指针标记；应先过滤哨兵，再核对设计、范围及类别后判断是否确实无匹配。
新版清单恰好有两行，为什么还要逐名对照？| 数量正确也可能包含错误实例或重复记录；要核对实际实例名及其母版，必要时检查快照和层级范围。
:::
