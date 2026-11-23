/* IC 后端学院 · 浏览器内模拟终端（MiniShell）
 *
 * 目的：阶段一的 Linux 课不装环境也能练。虚拟文件系统按真实工程目录建的
 *      （/home/autumn/backend_lab/...），命令行为尽量贴近真实 bash，
 *      包括报错原文（No such file or directory / command not found ...）。
 *
 * 用法：<div class="sbx" data-preset="basic">…</div>，由 Shell.mount 自动接管。
 * 测试：node -e "const {Shell}=require('./shell.js'); const s=new Shell(null,'basic'); console.log(s.run('ls -l'))"
 */
(function (global) {
  'use strict';

  /* ============================================================ 虚拟文件系统 */
  function dir(c) { return { t: 'd', c: c || {}, mode: '755' }; }
  function file(s, mode) { return { t: 'f', s: s, mode: mode || '644' }; }

  function build(obj) {
    if (typeof obj === 'string') return file(obj);
    var d = dir();
    for (var k in obj) if (Object.prototype.hasOwnProperty.call(obj, k)) d.c[k] = build(obj[k]);
    return d;
  }

  var VERILOG = [
    '// soc_top 的综合后网表（节选）',
    'module soc_top (clk, rst_n, din, dout);',
    '  input        clk;',
    '  input        rst_n;',
    '  input  [7:0] din;',
    '  output [7:0] dout;',
    '',
    '  wire   [7:0] alu_out;',
    '  wire         zero;',
    '',
    '  alu  u_alu (.a(din), .b(8\'h01), .op(3\'b000), .y(alu_out), .zero(zero));',
    '  dff  u_r0  (.d(alu_out), .clk(clk), .rst_n(rst_n), .q(dout));',
    'endmodule'
  ].join('\n');

  var SDC = [
    '# 时序约束：告诉工具时钟多快、外部器件多慢',
    'create_clock -name clk -period 2.0 [get_ports clk]   ;# 500MHz',
    'set_clock_uncertainty 0.05 [get_clocks clk]',
    'set_input_delay  0.30 -clock clk [all_inputs]',
    'set_output_delay 0.30 -clock clk [all_outputs]',
    'set_load 0.02 [all_outputs]',
    '# 复位是异步的，不做时序检查',
    'set_false_path -from [get_ports rst_n]'
  ].join('\n');

  var DCLOG = [
    'Information: Checking out license dc_shell (1 of 1).',
    'Loading target library: tt_1v0_25c.db',
    'Warning: Undriven net \'u_ctrl/en\'. (LINT-2)',
    'Information: Beginning mapping (4 cores).',
    'Information: Area = 1842.7 um^2, cells = 1614.',
    'Information: Critical path slack = 0.95 ns (MET).',
    'Information: Writing netlist to soc_net.v',
    'Information: dc_shell finished, 00:02:41 elapsed.'
  ].join('\n');

  var PNRTCL = [
    '# 布局布线主脚本（ICC2）',
    'set DESIGN ipa_top',
    'open_lib ./work',
    'open_block $DESIGN',
    '',
    '# 布局：先粗放，再细化',
    'set_app_options -name place.coarse.pin_density_aware -value true',
    'create_placement -effort high',
    'legalize_placement',
    'refine_placement',
    '',
    '# 布线：先全局，再逐轮增量修 DRC',
    'route_auto',
    'foreach it {1 2 3 4 5 6 7 8 9 10} {',
    '  route_detail -incremental true',
    '  check_routes > reports/drc_pass$it.rpt',
    '}',
    'save_block'
  ].join('\n');

  var TIMING = [
    '****************************************',
    'Report : timing -path_type max',
    'Design : ipa_top',
    'Corner : tt_1v0_25c',
    '****************************************',
    '',
    'Startpoint: u_core/u_alu/reg_a[3]  (rising edge-triggered flip-flop clocked by clk)',
    'Endpoint:   u_core/u_alu/reg_b[3]  (rising edge-triggered flip-flop clocked by clk)',
    'Path Group: clk',
    'Path Type:  max',
    '',
    '  Point                                Incr       Path',
    '  ----------------------------------------------------------',
    '  clock clk (rise edge)                0.00       0.00',
    '  u_core/u_alu/reg_a[3]/CK             0.00       0.00',
    '  u_core/u_alu/reg_a[3]/Q              0.11       0.11',
    '  u_core/u_alu/U12/ZN                  0.04       0.15',
    '  u_core/u_alu/U57/ZN                  0.06       0.21',
    '  u_core/u_alu/U88/Z                   0.09       0.30',
    '  u_core/u_alu/reg_b[3]/D              0.02       0.32',
    '  data arrival time                               0.32',
    '  ----------------------------------------------------------',
    '  clock clk (rise edge)                2.00       2.00',
    '  clock uncertainty                   -0.05       1.95',
    '  u_core/u_alu/reg_b[3]/CK             0.00       1.95',
    '  library setup time                  -0.05       1.90',
    '  data required time                              1.90',
    '  ----------------------------------------------------------',
    '  data required time                              1.90',
    '  data arrival time                              -0.32',
    '  ----------------------------------------------------------',
    '  slack (MET)                                     1.58'
  ].join('\n');

  var PATHS = [
    '# endpoint                        slack    cells  length(um)',
    'u_core/u_alu/reg_b[3]             -0.12     42     118.4',
    'u_core/u_alu/reg_c[0]              0.31     28      76.2',
    'u_core/u_mul/reg_p[7]             -0.35     57     203.8',
    'u_core/u_ctrl/state_reg[2]         0.04     19      41.6',
    'u_ram/u_sram/DO[31]               -0.08     33      92.5',
    'u_core/u_alu/reg_a[5]              0.22     24      63.1',
    'u_core/u_mul/reg_p[6]             -0.21     51     187.3',
    'u_dma/u_fifo/wr_ptr[4]             0.15     26      70.9'
  ].join('\n');

  var DRC = [
    '# 每一轮增量布线后的 DRC 数量',
    'iteration  DRC   opens   short',
    '1          6000  0       0',
    '2          156   0       0',
    '3          119   0       0',
    '4          72    0       0',
    '5          58    0       0',
    '6          47    0       0',
    '7          25    0       0',
    '8          17    0       0',
    '9          12    0       0',
    '10         0     0       0'
  ].join('\n');

  var ROUTELOG = [
    '[10:02:11] [INFO] start route_auto, 10225 nets',
    '[10:03:40] [WARN] congestion in region (120.5 88.2 180.9 140.0), overflow 12',
    '[10:04:02] [INFO] global route done, wirelength 812340 um',
    '[10:04:30] [INFO] detailed route iteration 1: DRC 6000',
    '[10:05:12] [INFO] detailed route iteration 2: DRC 156',
    '[10:06:01] [INFO] detailed route iteration 3: DRC 119',
    '[10:07:20] [INFO] detailed route iteration 9: DRC 12',
    '[10:08:05] [INFO] detailed route iteration 10: DRC 0',
    '[10:08:06] [INFO] total wirelength 798112 um, vias 214530'
  ].join('\n');

  var LIB = [
    '/* Nangate45 typical corner, 节选 */',
    'library (NangateOpenCellLibrary) {',
    '  delay_model : table_lookup;',
    '  nom_voltage : 1.0;',
    '  nom_temperature : 25.0;',
    '  cell (INV_X1) {',
    '    area : 0.760;',
    '    pin (A) { direction : input; capacitance : 0.002; }',
    '    pin (ZN) { direction : output;',
    '      timing () { related_pin : "A"; cell_rise (delay_template) { /* ... */ } }',
    '    }',
    '  }',
    '}'
  ].join('\n');

  var FS_SRC = {
    home: {
      autumn: {
        'README.md': [
          '# IPA 后端练习工程',
          '',
          '这里的目录结构就是一个真实项目的缩影：',
          '- backend_lab/soc/dc      综合脚本、约束、日志',
          '- backend_lab/soc/pnr     布局布线脚本与报告',
          '- pdk/nangate45           工艺库（标准单元、时序库）',
          '- logs                    运行日志',
          '- run.sh                  一键跑全流程的示例脚本',
          '',
          '练习建议：把每个目录都 ls 一遍，cat 一个日志，再 grep 一次 VIOLATED。'
        ].join('\n'),
        'run.sh': [
          '#!/bin/bash',
          '# 一键跑完整个流程（示例，真实项目每一步都要几小时）',
          'set -e                      # 任何一步失败就停下，别带着错继续跑',
          '',
          'echo "[1/3] 综合 ..."',
          'dc_shell -f dc/dc.tcl | tee dc/dc.log',
          '',
          'echo "[2/3] 布局布线 ..."',
          'cd pnr',
          'icc2_shell -f pnr.tcl | tee pnr.log',
          '',
          'echo "[3/3] 完成，报告在 pnr/reports/"'
        ].join('\n'),
        '.bashrc': [
          '# 每开一个终端，bash 都会先执行这个文件',
          'export PDK_ROOT=/home/autumn/pdk/nangate45',
          'export PATH=$PATH:$PDK_ROOT/bin',
          'alias ll="ls -l"'
        ].join('\n'),
        'notes.txt': [
          '2026-11-20  跑通第一版布局布线，DRC 6000，几乎全是引脚访问冲突',
          '2026-11-21  打开 pin_density_aware，DRC 降到 156',
          '2026-11-22  refine_placement + 10 轮增量布线，DRC 归零'
        ].join('\n'),
        backend_lab: {
          soc: {
            dc: {
              'dc.tcl': [
                '# 综合脚本：RTL -> 门级网表',
                'set_app_var search_path ". ../lib/db"',
                'set target_library "tt_1v0_25c.db"',
                'set link_library   "* $target_library"',
                'read_verilog ../rtl/soc_top.v',
                'current_design soc_top',
                'link',
                'source soc.sdc',
                'compile_ultra',
                'report_timing > reports/timing.rpt',
                'write -f verilog -hierarchy -output soc_net.v'
              ].join('\n'),
              'soc.sdc': SDC,
              'soc_net.v': VERILOG,
              'dc.log': DCLOG
            },
            pnr: {
              'pnr.tcl': PNRTCL,
              reports: {
                'timing.rpt': TIMING,
                'paths.rpt': PATHS,
                'drc.rpt': DRC
              }
            },
            rtl: {
              'soc_top.v': [
                '// RTL：综合的输入，人写的代码',
                'module soc_top (input clk, input rst_n, input [7:0] din, output reg [7:0] dout);',
                '  wire [7:0] alu_out;',
                '  assign alu_out = din + 8\'d1;',
                '  always @(posedge clk or negedge rst_n)',
                '    if (!rst_n) dout <= 8\'d0;',
                '    else         dout <= alu_out;',
                'endmodule'
              ].join('\n')
            }
          }
        },
        pdk: {
          nangate45: {
            'README.md': '# Nangate45 开源工艺库（45nm）\nlib/ 放时序库，lef/ 放物理抽象，tlup/ 放寄生参数。',
            lib: { 'NangateOpenCellLibrary_typical.lib': LIB },
            lef: { 'NangateOpenCellLibrary.lef': 'VERSION 5.8 ;\nMACRO INV_X1\n  CLASS CORE ;\n  SIZE 0.76 BY 1.4 ;\nEND INV_X1' }
          }
        },
        logs: { 'route.log': ROUTELOG },
        // 第 3 课练习一用的 PT 目录：预置一份，任何一组练习单独跑都能直接用
        PT: {
          P1: { txt1: '' },
          D2: { txt2: '' },
          K3: {},
          poi111: {}, lkjs222: {}, mnb333: {}, psaik61: {},
          asd111: '', asd444: '', asd555: '',
          qwe222: '', zxc333: ''
        }
      }
    },
    etc: { hosts: '127.0.0.1   localhost\n10.20.30.40 eda-server' },
    usr: { bin: {} },
    tmp: {}
  };

  var ROOT = build(FS_SRC);
  ROOT.c.home.c.autumn.c['run.sh'].mode = '755';

  /** 把文件系统恢复到初始状态（练习场「重置环境」用） */
  function resetFs() {
    ROOT = build(FS_SRC);
    ROOT.c.home.c.autumn.c['run.sh'].mode = '755';
  }

  var NOW = 'Nov 22 20:14';

  /* ============================================================ 词法/路径 */
  var SPECIAL = { '|': 1, '>': 1, '<': 1, ';': 1, '&': 1 };

  function lex(line) {
    var out = [], cur = '', q = null, quoted = false, i = 0, ch;
    // \u0002 前缀 = 这个参数被引号包过，后面不要再做通配符展开（和真 bash 一致）
    function push() {
      if (cur !== '') { out.push((quoted ? '\u0002' : '') + cur); cur = ''; }
      quoted = false;
    }
    while (i < line.length) {
      ch = line.charAt(i);
      if (q) {
        if (ch === q) q = null; else cur += ch;
        i++;
        continue;
      }
      // 行内注释：不在引号内、且位于词首（行首/空白/命令分隔符之后）的 # 之后全部忽略
      if (ch === '#' && cur === '' && (i === 0 || /[\s|;&]/.test(line.charAt(i - 1)))) break;
      if (ch === '"' || ch === "'") {
        quoted = true;
        if (ch === "'" && cur === '') cur = '\u0001';   // 标记：单引号内不展开 $变量
        q = ch; i++; continue;
      }
      if (ch === '>') {
        push();
        if (line.charAt(i + 1) === '>') { out.push('>>'); i += 2; }
        else { out.push('>'); i++; }
        continue;
      }
      if (SPECIAL[ch]) { push(); out.push(ch); i++; continue; }
      if (ch === ' ' || ch === '\t') { push(); i++; continue; }
      cur += ch; i++;
    }
    push();
    return out;
  }

  function expand(tok, sh) {
    var mark = '';
    if (tok.charAt(0) === '\u0002') { mark = '\u0002'; tok = tok.slice(1); }
    if (tok.charAt(0) === '\u0001') return mark + tok.slice(1);
    return mark + tok.replace(/\$\{(\w+)\}|\$(\w+)/g, function (m, a, b) {
      var k = a || b;
      if (k === 'PWD') return sh.pwd();
      if (k === 'HOME') return '/home/autumn';
      if (k === 'USER') return 'autumn';
      if (k === '?') return '0';
      return Object.prototype.hasOwnProperty.call(sh.env, k) ? sh.env[k] : '';
    });
  }

  /**
   * 通配符展开：ls asd*  /  rm -f *.txt  /  find backend_lab/*.tcl
   * 规则和真 bash 一致：* 不跨目录、不匹配隐藏文件；一个都没匹配上就把原样交还给命令。
   * 返回字符串数组（可能多个），没有通配符时返回原字符串。
   */
  function globOne(tok, sh) {
    var noGlob = false;
    while (tok.charAt(0) === '\u0002' || tok.charAt(0) === '\u0001') {
      if (tok.charAt(0) === '\u0002') noGlob = true;
      tok = tok.slice(1);
    }
    if (noGlob) return tok;
    if (tok.indexOf('*') < 0 && tok.indexOf('?') < 0) return tok;
    var slash = tok.lastIndexOf('/');
    var dirPart = slash >= 0 ? tok.slice(0, slash) : '';
    var namePart = slash >= 0 ? tok.slice(slash + 1) : tok;
    if (!namePart) return tok;
    var dnode = nodeAt(sh, dirPart ? segsOf(sh.cwd, dirPart) : sh.cwd.slice());
    if (!dnode || dnode.t !== 'd') return tok;
    var re = new RegExp('^' + namePart.replace(/[.+^${}()|[\]\\]/g, '\\$&')
      .replace(/\*/g, '[^/]*').replace(/\?/g, '[^/]') + '$');
    var hits = [];
    for (var k in dnode.c) {
      if (!Object.prototype.hasOwnProperty.call(dnode.c, k)) continue;
      if (k.charAt(0) === '.') continue;
      if (re.test(k)) hits.push(k);
    }
    if (!hits.length) return tok;
    hits.sort();
    return hits.map(function (h) { return dirPart ? dirPart + '/' + h : h; });
  }

  function segsOf(cwd, p) {
    if (p === '~') p = '/home/autumn';
    else if (p.indexOf('~/') === 0) p = '/home/autumn' + p.slice(1);
    var segs = p.charAt(0) === '/' ? [] : cwd.slice();
    var parts = p.split('/');
    for (var i = 0; i < parts.length; i++) {
      var s = parts[i];
      if (!s || s === '.') continue;
      if (s === '..') { if (segs.length) segs.pop(); continue; }
      segs.push(s);
    }
    return segs;
  }

  function nodeAt(sh, segs) {
    var n = ROOT;
    for (var i = 0; i < segs.length; i++) {
      if (!n || n.t !== 'd') return null;
      n = n.c[segs[i]];
    }
    return n || null;
  }

  function permStr(n) {
    var m = n.mode || (n.t === 'd' ? '755' : '644');
    var s = n.t === 'd' ? 'd' : '-';
    for (var i = 0; i < 3; i++) {
      var d = parseInt(m.charAt(i), 10) || 0;
      s += (d & 4 ? 'r' : '-') + (d & 2 ? 'w' : '-') + (d & 1 ? 'x' : '-');
    }
    return s;
  }

  function sizeOf(n) { return n.t === 'd' ? 4096 : n.s.length; }

  function fmtLs(n, name) {
    var pad = '                ';
    var sz = String(sizeOf(n));
    sz = pad.slice(sz.length) + sz;
    return permStr(n) + ' 1 autumn autumn ' + sz + ' ' + NOW + ' ' + name;
  }

  function splitLines(s) {
    if (!s) return [];
    var a = s.replace(/\n$/, '').split('\n');
    return a;
  }

  /** 把一行命令拆成「命令 + 行尾注释」，注释单独上色（练习场回显用） */
  function splitLineNote(s) {
    var q = null;
    for (var i = 0; i < s.length; i++) {
      var c = s.charAt(i);
      if (q) { if (c === q) q = null; continue; }
      if (c === '"' || c === "'") { q = c; continue; }
      if (c === '#' && (i === 0 || /\s/.test(s.charAt(i - 1)))) {
        return { cmd: s.slice(0, i).replace(/\s+$/, ''), note: s.slice(i).replace(/^#\s?/, '') };
      }
    }
    return { cmd: s, note: '' };
  }

  function rx(pat, flags) {
    try { return new RegExp(pat, flags); } catch (e) { return null; }
  }

  /* ============================================================ 命令表 */
  var CMDS = {};

  CMDS.pwd = function (sh) { return { o: sh.pwd() }; };

  CMDS.cd = function (sh, a) {
    var target = a[0] || '/home/autumn';
    // cd - ：回到上一次的目录（真 bash 里会顺手把路径打出来）
    if (target === '-') {
      if (!sh.oldpwd) return { e: 'cd: OLDPWD not set', c: 1 };
      target = sh.oldpwd;
      sh.cwd = segsOf([], target);
      sh.oldpwd = sh.pwd();
      return { o: target };
    }
    var segs = segsOf(sh.cwd, target);
    var n = nodeAt(sh, segs);
    if (!n) return { e: 'cd: ' + target + ': No such file or directory', c: 1 };
    if (n.t !== 'd') return { e: 'cd: ' + target + ': Not a directory', c: 1 };
    if (!(parseInt(n.mode || '755', 10) & 1)) return { e: 'cd: ' + target + ': Permission denied', c: 1 };
    sh.oldpwd = sh.pwd();
    sh.cwd = segs;
    return {};
  };

  CMDS.ls = function (sh, a) {
    var fl = {}, paths = [], i;
    for (i = 0; i < a.length; i++) {
      if (a[i].charAt(0) === '-' && a[i].length > 1) {
        for (var j = 1; j < a[i].length; j++) fl[a[i].charAt(j)] = 1;
      } else paths.push(a[i]);
    }
    if (!paths.length) paths.push('.');
    var out = [], multi = paths.length > 1;
    for (i = 0; i < paths.length; i++) {
      var segs = segsOf(sh.cwd, paths[i]);
      var n = nodeAt(sh, segs);
      if (!n) return { e: "ls: cannot access '" + paths[i] + "': No such file or directory", c: 2 };
      // -d：目录本身当成一个条目显示，不进去列内容（ls -d p* 就是这么用的）
      if (fl.d) { out.push(fl.l ? fmtLs(n, paths[i]) : paths[i]); continue; }
      // 真 ls 的规矩：只有目录参数才打 "名字:" 抬头，文件是直接排出来的
      if (multi && n.t === 'd') { if (out.length) out.push(''); out.push(paths[i] + ':'); }
      if (n.t === 'f') { out.push(fl.l ? fmtLs(n, paths[i]) : paths[i]); continue; }
      var names = [];
      for (var k in n.c) if (Object.prototype.hasOwnProperty.call(n.c, k)) {
        if (k.charAt(0) === '.' && !fl.a) continue;
        names.push(k);
      }
      names.sort();
      if (fl.a) names = ['.', '..'].concat(names);
      if (fl.l) {
        var blk = 0;
        for (var q = 0; q < names.length; q++) blk += (names[q] === '.' || names[q] === '..') ? 4 : 4;
        out.push('total ' + blk);
        for (q = 0; q < names.length; q++) {
          var nn = names[q] === '.' ? n : (names[q] === '..' ? (nodeAt(sh, segs.slice(0, -1)) || n) : n.c[names[q]]);
          out.push(fmtLs(nn, names[q]));
        }
      } else if (names.length) {
        // 一行多个，像真 ls 那样分列
        var line = '', colw = 0, cells = [];
        for (q = 0; q < names.length; q++) cells.push(names[q]);
        out.push(cells.join('  '));
      }
    }
    return { o: out.join('\n') };
  };

  CMDS.cat = function (sh, a, stdin) {
    if (!a.length) return { o: stdin || '' };
    var out = [];
    for (var i = 0; i < a.length; i++) {
      var n = nodeAt(sh, segsOf(sh.cwd, a[i]));
      if (!n) return { e: 'cat: ' + a[i] + ': No such file or directory', c: 1 };
      if (n.t === 'd') return { e: 'cat: ' + a[i] + ': Is a directory', c: 1 };
      out.push(n.s);
    }
    return { o: out.join('\n') };
  };

  CMDS.less = CMDS.cat;
  CMDS.more = CMDS.cat;
  CMDS.nl = function (sh, a) {
    var r = CMDS.cat(sh, a);
    if (r.e) return r;
    var l = splitLines(r.o);
    return { o: l.map(function (x, i) { return (i + 1) + '\t' + x; }).join('\n') };
  };

  function headTail(sh, a, fromEnd) {
    var n = 10, files = [], i;
    for (i = 0; i < a.length; i++) {
      if (a[i] === '-n') { n = parseInt(a[++i], 10) || 10; }
      else if (/^-\d+$/.test(a[i])) n = parseInt(a[i].slice(1), 10);
      else if (/^-\d+$/.test(a[i]) === false && a[i].charAt(0) === '-' && isNaN(parseInt(a[i].slice(1), 10))) { }
      else files.push(a[i]);
    }
    var src;
    if (!files.length || files[0] === '-') src = sh.stdin || '';
    else {
      var r = CMDS.cat(sh, files);
      if (r.e) return r;
      src = r.o;
    }
    var l = splitLines(src);
    var out = fromEnd ? l.slice(Math.max(0, l.length - n)) : l.slice(0, n);
    return { o: out.join('\n') };
  }
  CMDS.head = function (sh, a, stdin) { sh.stdin = stdin; return headTail(sh, a, false); };
  CMDS.tail = function (sh, a, stdin) { sh.stdin = stdin; return headTail(sh, a, true); };

  CMDS.wc = function (sh, a, stdin) {
    var fl = {}, i, files = [];
    for (i = 0; i < a.length; i++) {
      if (a[i].charAt(0) === '-') { for (var j = 1; j < a[i].length; j++) fl[a[i].charAt(j)] = 1; }
      else files.push(a[i]);
    }
    var src = files.length ? CMDS.cat(sh, files) : { o: stdin || '' };
    if (src.e) return src;
    var l = splitLines(src.o);
    var lines = l.length, words = (src.o.match(/\S+/g) || []).length, chars = src.o.length;
    if (fl.l && !fl.w && !fl.c) return { o: String(lines) };
    if (fl.w && !fl.l && !fl.c) return { o: String(words) };
    if (fl.c && !fl.l && !fl.w) return { o: String(chars) };
    return { o: lines + ' ' + words + ' ' + chars };
  };

  CMDS.grep = function (sh, a, stdin) {
    var fl = {}, i, rest = [];
    for (i = 0; i < a.length; i++) {
      if (a[i].charAt(0) === '-' && a[i].length > 1) {
        for (var j = 1; j < a[i].length; j++) fl[a[i].charAt(j)] = 1;
        continue;
      }
      rest.push(a[i]);
    }
    if (!rest.length) return { e: 'Usage: grep [OPTION]... PATTERN [FILE]...', c: 2 };
    var pat = rest.shift();
    var re = rx(pat, fl.i ? 'i' : '');
    if (!re) return { e: 'grep: Invalid regular expression', c: 2 };
    var files = rest.slice();
    // -R / -r：目录参数展开成它下面所有文件，和真 grep -R 一致
    if (fl.R || fl.r) {
      var expanded = [];
      for (i = 0; i < files.length; i++) {
        var dn = nodeAt(sh, segsOf(sh.cwd, files[i]));
        if (dn && dn.t === 'd') {
          (function walk(node, path) {
            for (var k in node.c) if (Object.prototype.hasOwnProperty.call(node.c, k)) {
              var p = (path === '/' ? '' : path) + '/' + k;
              if (node.c[k].t === 'f') expanded.push(p);
              else walk(node.c[k], p);
            }
          })(dn, files[i].replace(/\/+$/, ''));
        } else expanded.push(files[i]);
      }
      files = expanded;
    }
    var multi = files.length > 1, hits = [], n = 0;
    // 没有文件参数就读管道/stdin；有文件就逐个处理（多个文件时前缀文件名，行号按文件重数）
    var targets = files.length ? files : [null];
    for (var fi = 0; fi < targets.length; fi++) {
      var srcTxt;
      if (targets[fi] === null) srcTxt = stdin || '';
      else {
        var dnode = nodeAt(sh, segsOf(sh.cwd, targets[fi]));
        if (dnode && dnode.t === 'd') return { e: 'grep: ' + targets[fi] + ': Is a directory', c: 2 };
        var fr = CMDS.cat(sh, [targets[fi]]);
        if (fr.e) return fr;
        srcTxt = fr.o;
      }
      var ls = splitLines(srcTxt);
      for (i = 0; i < ls.length; i++) {
        var hit = re.test(ls[i]);
        if (fl.v ? !hit : hit) {
          n++;
          if (!fl.c) {
            hits.push((multi ? targets[fi] + ':' : '') + (fl.n ? (i + 1) + ':' : '') + ls[i]);
          }
        }
      }
    }
    if (fl.c) return { o: String(n) };
    if (!hits.length) return { o: '', c: 1 };
    return { o: hits.join('\n') };
  };

  CMDS.sed = function (sh, a, stdin) {
    var quiet = false, i = 0, script = null, files = [];
    for (; i < a.length; i++) {
      if (a[i] === '-n') { quiet = true; continue; }
      if (a[i] === '-e') { script = a[++i]; continue; }
      if (script === null) { script = a[i]; continue; }
      files.push(a[i]);
    }
    if (script === null) return { e: 'sed: no script specified', c: 1 };
    var src, r;
    if (files.length) { r = CMDS.cat(sh, files); if (r.e) return r; src = r.o; }
    else src = stdin || '';

    var lines = splitLines(src), out = [];
    var sm = script.match(/^s(.)(.*?)\1(.*?)\1([gi]*)$/);
    var pm = script.match(/^(\d+)(?:,(\d+))?([pd])$/);
    if (sm) {
      var re = rx(sm[2], sm[4] && sm[4].indexOf('g') >= 0 ? 'g' : '');
      if (!re) return { e: 'sed: invalid regular expression', c: 1 };
      var rep = sm[3].replace(/\\1/g, '$1').replace(/&/g, '$&');
      for (i = 0; i < lines.length; i++) {
        var nl = lines[i].replace(re, rep);
        if (quiet) { if (nl !== lines[i]) out.push(nl); }
        else out.push(nl);
      }
    } else if (pm) {
      var lo = parseInt(pm[1], 10), hi = pm[2] ? parseInt(pm[2], 10) : lo;
      for (i = 0; i < lines.length; i++) {
        var no = i + 1, inR = no >= lo && no <= hi;
        if (pm[3] === 'p') { if (inR) out.push(lines[i]); }
        else if (pm[3] === 'd') { if (!inR) out.push(lines[i]); }
      }
    } else {
      return { e: "sed: -e expression #1, char 1: unknown command: '" + script.charAt(0) + "'", c: 1 };
    }
    return { o: out.join('\n') };
  };

  CMDS.awk = function (sh, a, stdin) {
    var fs = null, prog = null, files = [], i = 0;
    for (; i < a.length; i++) {
      if (a[i] === '-F') { fs = a[++i]; continue; }
      if (a[i].indexOf('-F') === 0 && a[i].length > 2) { fs = a[i].slice(2); continue; }
      if (prog === null) { prog = a[i]; continue; }
      files.push(a[i]);
    }
    if (prog === null) return { e: 'usage: awk [-F fs] program [file ...]', c: 2 };
    var src, r;
    if (files.length) { r = CMDS.cat(sh, files); if (r.e) return r; src = r.o; }
    else src = stdin || '';

    if (fs === '\\t') fs = '\t';
    var sep = fs ? new RegExp(fs.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) : /\s+/;

    var body = prog, cond = null;
    var bm = prog.match(/^(.*?)\{([\s\S]*)\}\s*$/);
    if (bm) { cond = bm[1].trim(); body = bm[2]; }
    var stmts = body.split(';').map(function (s) { return s.trim(); }).filter(Boolean);

    var lines = splitLines(src), out = [], NR = 0;
    for (i = 0; i < lines.length; i++) {
      NR++;
      var f = lines[i].split(sep);
      if (fs) f = lines[i].split(fs);
      if (cond) {
        var c = cond;
        c = c.replace(/\$(\d+)/g, function (m, d) { return JSON.stringify(f[parseInt(d, 10) - 1] || ''); });
        c = c.replace(/\bNR\b/g, NR).replace(/\bNF\b/g, f.length);
        c = c.replace(/([^=!<>])=([^=])/g, '$1==$2');
        c = c.replace(/~/g, '.indexOf(');
        try { if (!eval(c)) continue; } catch (e) { return { e: 'awk: syntax error near ' + cond, c: 2 }; }
      }
      for (var s = 0; s < stmts.length; s++) {
        var st = stmts[s];
        var pm = st.match(/^print\s*(.*)$/);
        if (pm) {
          var args = pm[1] ? splitArgs(pm[1]) : ['$0'];
          var vals = args.map(function (x) {
            x = x.trim();
            var fm = x.match(/^\$(\d+)$/);
            if (fm) { var k = parseInt(fm[1], 10); return k === 0 ? lines[i] : (f[k - 1] || ''); }
            if (x === '$NF') return f[f.length - 1] || '';
            if (x === 'NR') return String(NR);
            if (x === 'NF') return String(f.length);
            if (/^".*"$/.test(x)) return x.slice(1, -1);
            return x;
          });
          out.push(vals.join(fs || ' '));
        }
      }
    }
    return { o: out.join('\n') };
  };

  function splitArgs(s) {
    var out = [], cur = '', q = null;
    for (var i = 0; i < s.length; i++) {
      var ch = s.charAt(i);
      if (q) { if (ch === q) q = null; else cur += ch; continue; }
      if (ch === '"' || ch === "'") { q = ch; continue; }
      if (ch === ',') { out.push(cur); cur = ''; continue; }
      cur += ch;
    }
    if (cur) out.push(cur);
    return out;
  }


  function readInput(sh, args, stdin) {
    var files = [];
    for (var i = 0; i < args.length; i++) {
      if (args[i].charAt(0) !== '-' && args[i] !== '') files.push(args[i]);
    }
    if (!files.length) return stdin || '';
    var r = CMDS.cat(sh, files);
    return r.e ? '' : r.o;
  }

  function srcOf(sh, files, stdin) {
    if (!files.length) return { o: stdin || '' };
    return CMDS.cat(sh, files);
  }

  CMDS.sort = function (sh, a, stdin) {
    var num = false, rev = false, uniq = false, key = 0, files = [], i;
    for (i = 0; i < a.length; i++) {
      var x = a[i];
      if (x === '-n') num = true;
      else if (x === '-r') rev = true;
      else if (x === '-u') uniq = true;
      else if (x === '-k') key = (parseInt(a[++i], 10) || 1) - 1;
      else if (/^-k\d+$/.test(x)) key = parseInt(x.slice(2), 10) - 1;
      else if (/^-[nrku]+$/.test(x)) {
        if (x.indexOf('n') > 0) num = true;
        if (x.indexOf('r') > 0) rev = true;
        if (x.indexOf('u') > 0) uniq = true;
      }
      else files.push(x);
    }
    var r = srcOf(sh, files, stdin);
    if (r.e) return r;
    var lines = splitLines(r.o);
    lines.sort(function (x, y) {
      var xa = x.split(/\s+/)[key] || '', ya = y.split(/\s+/)[key] || '';
      var d = num ? (parseFloat(xa) || 0) - (parseFloat(ya) || 0) : (xa > ya ? 1 : xa < ya ? -1 : 0);
      return rev ? -d : d;
    });
    if (uniq) {
      var seen = {}, keep = [];
      for (i = 0; i < lines.length; i++) {
        if (seen[lines[i]]) continue;
        seen[lines[i]] = 1; keep.push(lines[i]);
      }
      lines = keep;
    }
    return { o: lines.join('\n') };
  };

  CMDS.uniq = function (sh, a, stdin) {
    var cnt = false, files = [], i;
    for (i = 0; i < a.length; i++) { if (a[i] === '-c') cnt = true; else files.push(a[i]); }
    var r = srcOf(sh, files, stdin);
    if (r.e) return r;
    var lines = splitLines(r.o), out = [], prev = null, n = 0;
    for (i = 0; i < lines.length; i++) {
      if (lines[i] === prev) { n++; continue; }
      if (prev !== null) out.push(cnt ? (('      ' + n).slice(-6) + ' ' + prev) : prev);
      prev = lines[i]; n = 1;
    }
    if (prev !== null) out.push(cnt ? (('      ' + n).slice(-6) + ' ' + prev) : prev);
    return { o: out.join('\n') };
  };

  CMDS.cut = function (sh, a, stdin) {
    var d = '\t', flds = [0], files = [], i;
    for (i = 0; i < a.length; i++) {
      if (a[i] === '-d') { d = a[++i]; continue; }
      if (a[i] === '-f') { flds = a[++i].split(',').map(function (x) { return parseInt(x, 10) - 1; }); continue; }
      if (/^-d./.test(a[i])) { d = a[i].slice(2); continue; }
      if (/^-f[\d,]+$/.test(a[i])) { flds = a[i].slice(2).split(',').map(function (x) { return parseInt(x, 10) - 1; }); continue; }
      files.push(a[i]);
    }
    var r = srcOf(sh, files, stdin);
    if (r.e) return r;
    var lines = splitLines(r.o);
    return {
      o: lines.map(function (l) {
        var p = l.split(d);
        return flds.map(function (k) { return p[k] === undefined ? '' : p[k]; }).join(d);
      }).join('\n')
    };
  };

  CMDS.tr = function (sh, a, stdin) {
    if (a.length < 2) return { e: 'tr: missing operand', c: 1 };
    var from = a[0], to = a[1];
    var r = srcOf(sh, a.slice(2), stdin);
    if (r.e) return r;
    var src = r.o;
    if (/^a-z$/.test(from) && /^A-Z$/.test(to)) return { o: src.toUpperCase() };
    if (/^A-Z$/.test(from) && /^a-z$/.test(to)) return { o: src.toLowerCase() };
    var out = '', map = {};
    for (var i = 0; i < from.length; i++) map[from.charAt(i)] = to.charAt(i) || to.charAt(to.length - 1);
    for (i = 0; i < src.length; i++) {
      var ch = src.charAt(i);
      out += map[ch] !== undefined ? map[ch] : ch;
    }
    return { o: out };
  };

  CMDS.echo = function (sh, a) {
    return { o: a.join(' ') };
  };
  CMDS.printf = CMDS.echo;

  CMDS.mkdir = function (sh, a) {
    var p = false, files = [], i;
    for (i = 0; i < a.length; i++) { if (a[i] === '-p') p = true; else files.push(a[i]); }
    if (!files.length) return { e: 'mkdir: missing operand', c: 1 };
    for (i = 0; i < files.length; i++) {
      var segs = segsOf(sh.cwd, files[i]);
      if (!segs.length) return { e: "mkdir: cannot create directory '" + files[i] + "': File exists", c: 1 };
      if (p) {
        var cur = ROOT, okPath = true;
        for (var k = 0; k < segs.length; k++) {
          if (!cur.c) { okPath = false; break; }
          if (!cur.c[segs[k]]) cur.c[segs[k]] = dir();
          cur = cur.c[segs[k]];
          if (cur.t !== 'd') { okPath = false; break; }
        }
        if (okPath) continue;
      }
      var parent = nodeAt(sh, segs.slice(0, -1));
      if (!parent || parent.t !== 'd') return { e: "mkdir: cannot create directory '" + files[i] + "': No such file or directory", c: 1 };
      if (parent.c[segs[segs.length - 1]]) {
        return { e: "mkdir: cannot create directory '" + files[i] + "': File exists", c: 1 };
      }
      parent.c[segs[segs.length - 1]] = dir();
    }
    return {};
  };

  CMDS.touch = function (sh, a) {
    if (!a.length) return { e: 'touch: missing file operand', c: 1 };
    for (var i = 0; i < a.length; i++) {
      var segs = segsOf(sh.cwd, a[i]);
      var parent = nodeAt(sh, segs.slice(0, -1));
      if (!parent) return { e: "touch: cannot touch '" + a[i] + "': No such file or directory", c: 1 };
      if (!parent.c[segs[segs.length - 1]]) parent.c[segs[segs.length - 1]] = file('');
    }
    return {};
  };

  CMDS.cp = function (sh, a) {
    var rec = false, items = [], i;
    for (i = 0; i < a.length; i++) { if (a[i] === '-r' || a[i] === '-R') rec = true; else items.push(a[i]); }
    if (items.length < 2) return { e: 'cp: missing destination file operand', c: 1 };
    var dst = items.pop();
    var dsegs = segsOf(sh.cwd, dst), dn = nodeAt(sh, dsegs);
    for (i = 0; i < items.length; i++) {
      var ssegs = segsOf(sh.cwd, items[i]), sn = nodeAt(sh, ssegs);
      if (!sn) return { e: "cp: cannot stat '" + items[i] + "': No such file or directory", c: 1 };
      if (sn.t === 'd' && !rec) return { e: "cp: -r not specified; omitting directory '" + items[i] + "'", c: 1 };
      if (dn && dn.t === 'd') dn.c[ssegs[ssegs.length - 1]] = JSON.parse(JSON.stringify(sn));
      else {
        var dp = nodeAt(sh, dsegs.slice(0, -1));
        if (!dp) return { e: "cp: cannot create regular file '" + dst + "': No such file or directory", c: 1 };
        dp.c[dsegs[dsegs.length - 1]] = JSON.parse(JSON.stringify(sn));
      }
    }
    return {};
  };

  CMDS.mv = function (sh, a) {
    var r = CMDS.cp(sh, a.concat(a.length > 2 ? [] : []));
    if (r.e) return r;
    if (a.length < 2) return { e: 'mv: missing destination file operand', c: 1 };
    var dst = a[a.length - 1];
    for (var i = 0; i < a.length - 1; i++) CMDS.rm(sh, ['-f'].concat([a[i]]));
    return {};
  };

  CMDS.rm = function (sh, a) {
    var rec = false, force = false, items = [], i;
    for (i = 0; i < a.length; i++) {
      var x = a[i];
      if (x.charAt(0) === '-' && x.length > 1) {
        if (x.indexOf('r') > 0) rec = true;
        if (x.indexOf('f') > 0) force = true;
      } else items.push(x);
    }
    if (!items.length) return { e: 'rm: missing operand', c: 1 };
    for (i = 0; i < items.length; i++) {
      var segs = segsOf(sh.cwd, items[i]);
      var parent = nodeAt(sh, segs.slice(0, -1));
      var name = segs[segs.length - 1];
      if (!parent || !parent.c[name]) {
        if (force) continue;
        return { e: "rm: cannot remove '" + items[i] + "': No such file or directory", c: 1 };
      }
      if (parent.c[name].t === 'd' && !rec) {
        return { e: "rm: cannot remove '" + items[i] + "': Is a directory", c: 1 };
      }
      delete parent.c[name];
    }
    return {};
  };

  CMDS.chmod = function (sh, a) {
    if (a.length < 2) return { e: 'chmod: missing operand', c: 1 };
    var mode = a[0], n = nodeAt(sh, segsOf(sh.cwd, a[1]));
    if (!n) return { e: "chmod: cannot access '" + a[1] + "': No such file or directory", c: 1 };
    if (/^[0-7]{3}$/.test(mode)) n.mode = mode;
    else if (/^\+x$/.test(mode)) n.mode = n.mode.charAt(0) + '55' + (parseInt(n.mode.charAt(2), 10) | 1);
    else if (/^-x$/.test(mode)) n.mode = n.mode.slice(0, 2) + (parseInt(n.mode.charAt(2), 10) & 6);
    return {};
  };

  CMDS.find = function (sh, a) {
    var start = '.', name = null, type = null, i;
    for (i = 0; i < a.length; i++) {
      if (a[i] === '-name') name = a[++i];
      else if (a[i] === '-type') type = a[++i];
      else if (a[i].charAt(0) !== '-') start = a[i];
    }
    var segs = segsOf(sh.cwd, start), n = nodeAt(sh, segs);
    if (!n) return { e: "find: '" + start + "': No such file or directory", c: 1 };
    var out = [], re = name ? rx(name.replace(/\./g, '\\.').replace(/\*/g, '.*').replace(/\?/g, '.')) : null;
    function typeOk(node) {
      if (!type) return true;
      return type === 'd' ? node.t === 'd' : (type === 'f' ? node.t === 'f' : true);
    }
    // 真 find 会把起点自己也列出来（find backend_lab -type d → 第一行就是 backend_lab）
    if (!name && type && typeOk(n)) out.push(start);
    (function walk(node, path) {
      for (var k in node.c) if (Object.prototype.hasOwnProperty.call(node.c, k)) {
        var p = (path === '/' ? '' : path) + '/' + k;
        if ((!re || re.test(k)) && typeOk(node.c[k])) out.push(p);
        if (node.c[k].t === 'd') walk(node.c[k], p);
      }
    })(n, start.replace(/\/+$/, ''));
    return { o: out.join('\n') };
  };

  CMDS.du = function (sh, a) {
    var target = null, human = false, i;
    for (i = 0; i < a.length; i++) {
      if (a[i] === '--') continue;
      if (a[i].charAt(0) === '-' && a[i].length > 1) { if (a[i].indexOf('h') > 0) human = true; continue; }
      if (target === null) target = a[i];
    }
    if (target === null) target = '.';
    var segs = segsOf(sh.cwd, target), n = nodeAt(sh, segs);
    if (!n) return { e: "du: cannot access '" + target + "': No such file or directory", c: 1 };
    var total = 0;
    (function walk(node) {
      for (var k in node.c) if (Object.prototype.hasOwnProperty.call(node.c, k)) {
        total += 4;
        if (node.c[k].t === 'd') walk(node.c[k]);
        else total += Math.ceil(node.c[k].s.length / 1024);
      }
    })(n);
    // 内部单位是 KB；-h 换算成 K/M，和真 du -sh 的观感一致
    var sz = String(total);
    if (human) sz = total >= 1024 ? (total / 1024).toFixed(1) + 'M' : total + 'K';
    return { o: sz + '\t' + target };
  };

  CMDS.df = function () {
    return { o: ['Filesystem      Size  Used Avail Use% Mounted on',
      '/dev/sda3        50G   18G   30G  38% /',
      '/dev/sda1       976M  180M  746M  20% /boot'].join('\n') };
  };

  CMDS.whoami = function () { return { o: 'autumn' }; };
  CMDS.hostname = function () { return { o: 'eda' }; };
  CMDS.id = function () { return { o: 'uid=1000(autumn) gid=1000(autumn) groups=1000(autumn)' }; };

  CMDS.date = function () {
    var d = new Date();
    var wd = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][d.getDay()];
    var mo = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][d.getMonth()];
    function p(x) { return (x < 10 ? '0' : '') + x; }
    return { o: wd + ' ' + mo + ' ' + d.getDate() + ' ' + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds()) + ' CST ' + d.getFullYear() };
  };

  CMDS.env = function (sh) {
    var out = [];
    for (var k in sh.env) if (Object.prototype.hasOwnProperty.call(sh.env, k)) out.push(k + '=' + sh.env[k]);
    return { o: out.join('\n') };
  };

  CMDS['export'] = function (sh, a) {
    for (var i = 0; i < a.length; i++) {
      var m = a[i].match(/^(\w+)=(.*)$/);
      if (m) sh.env[m[1]] = m[2];
    }
    return {};
  };
  CMDS.setenv = CMDS['export'];

  CMDS.unset = function (sh, a) {
    for (var i = 0; i < a.length; i++) delete sh.env[a[i]];
    return {};
  };

  CMDS.alias = function (sh, a) {
    if (!a.length) {
      var out = [];
      for (var k in sh.alias) out.push('alias ' + k + '=' + sh.alias[k]);
      return { o: out.join('\n') };
    }
    var m = a[0].match(/^(\w+)=['"]?(.*?)['"]?$/);
    if (m) sh.alias[m[1]] = m[2];
    return {};
  };

  CMDS.which = function (sh, a) {
    var out = [];
    for (var i = 0; i < a.length; i++) {
      if (CMDS[a[i]]) out.push('/usr/bin/' + a[i]);
      else out.push('which: no ' + a[i] + ' in (/usr/local/bin:/usr/bin:/bin)');
    }
    return { o: out.join('\n') };
  };
  CMDS.type = CMDS.which;

  CMDS.ps = function () {
    return {
      o: ['  PID TTY          TIME CMD',
        ' 1201 pts/0    00:00:00 bash',
        ' 1288 pts/0    02:41:12 dc_shell',
        ' 1402 pts/0    18:03:44 icc2_shell',
        ' 1503 pts/1    00:00:00 vim',
        ' 1610 pts/0    00:00:00 ps'].join('\n')
    };
  };

  CMDS.kill = function (sh, a) {
    if (!a.length) return { e: 'kill: usage: kill [-s sigspec] pid ...', c: 1 };
    return { o: '' };
  };

  CMDS.history = function (sh) {
    return { o: sh.hist.map(function (h, i) { return '  ' + (i + 1) + '  ' + h; }).join('\n') };
  };

  CMDS.clear = function () { return { clear: true }; };

  CMDS.exit = function () { return { o: '退出模拟终端：刷新页面可以重来。' }; };

  CMDS.help = function () {
    return {
      o: ['可用命令（模拟环境，够练阶段一）:',
        '  目录   pwd  ls [-la]  cd  mkdir [-p]  find . -name "*.v"  find . -type d  tree',
        '  文件   cat  head -n 5  tail -n 5  cp  mv  rm [-rf]  touch  chmod 755',
        '  文本   grep [-invc]  sed "s/a/b/g"  sed -n "2,4p"  awk "{print $2}"  wc -l  sort [-nr] [-u]  uniq -c  cut -d: -f1  tr a-z A-Z',
        '  通配   ls *.txt   rm -f asd*   cp pdk/*.lef .    （* 不跨目录，也不匹配隐藏文件）',
        '  管道   cat x | grep y | wc -l      重定向  echo hi > f   echo hi >> f',
        '  环境   env  export A=1  setenv A 1  echo $A  which ls  alias ll="ls -l"',
        '  进程   ps  kill 9999  df  du -sh',
        '  脚本   bash run.sh    ./run.sh    history    clear'].join('\n')
    };
  };

  CMDS.tree = function (sh, a) {
    var segs = segsOf(sh.cwd, a[0] || '.'), n = nodeAt(sh, segs);
    if (!n) return { e: "tree: '" + (a[0] || '.') + "': No such file or directory", c: 1 };
    var out = [a[0] || '.'];
    (function walk(node, prefix) {
      var keys = [];
      for (var k in node.c) if (Object.prototype.hasOwnProperty.call(node.c, k)) {
        if (k.charAt(0) === '.' && k !== '.bashrc') continue;
        keys.push(k);
      }
      keys.sort();
      for (var i = 0; i < keys.length; i++) {
        var last = i === keys.length - 1;
        out.push(prefix + (last ? '└── ' : '├── ') + keys[i]);
        if (node.c[keys[i]].t === 'd') walk(node.c[keys[i]], prefix + (last ? '    ' : '│   '));
      }
    })(n, '');
    return { o: out.join('\n') };
  };

  CMDS.bash = function (sh, a) { return runScript(sh, a); };
  CMDS.sh = CMDS.bash;
  CMDS.source = function (sh, a) { return runScript(sh, a, true); };

  function runScript(sh, a, quiet) {
    var f = a[0];
    if (!f) return { e: 'bash: no script file given', c: 1 };
    var n = nodeAt(sh, segsOf(sh.cwd, f));
    if (!n) return { e: 'bash: ' + f + ': No such file or directory', c: 127 };
    if (n.t === 'd') return { e: 'bash: ' + f + ': Is a directory', c: 126 };
    var lines = splitLines(n.s), out = [];
    for (var i = 0; i < lines.length; i++) {
      var ln = lines[i].trim();
      if (!ln || ln.charAt(0) === '#') continue;
      if (/^set -e/.test(ln)) continue;
      if (/^set\s/.test(ln)) continue;
      var r = sh.exec(ln, true);
      if (r) out.push(r);
    }
    return { o: out.join('\n') };
  }

  /* ============================================================ Shell */
  function Shell(el, preset) {
    this.el = el || null;
    this.preset = preset || 'basic';
    this.cwd = ['home', 'autumn'];
    this.env = {
      USER: 'autumn', HOME: '/home/autumn', SHELL: '/bin/bash',
      PDK_ROOT: '/home/autumn/pdk/nangate45', TERM: 'xterm-256color',
      PATH: '/usr/local/bin:/usr/bin:/bin'
    };
    this.alias = { ll: 'ls -l' };
    this.hist = [];
    this.hi = -1;
    this.buf = [];
    if (this.preset === 'text') this.cwd = ['home', 'autumn', 'backend_lab', 'soc', 'pnr', 'reports'];
    if (this.preset === 'proc') this.cwd = ['home', 'autumn', 'logs'];
    if (el) this.attach();
  }

  Shell.prototype.pwd = function () { return '/' + this.cwd.join('/'); };

  Shell.prototype.ps1 = function () {
    var p = this.pwd();
    if (p === '/home/autumn') p = '~';
    else if (p.indexOf('/home/autumn/') === 0) p = '~/' + p.slice(13);
    return '[autumn@eda ' + p + ']$';
  };

  Shell.prototype.print = function (text, cls) {
    var s = text === undefined || text === null ? '' : String(text);
    this.buf.push(s);
    if (!this.el) return;
    var box = this.el.querySelector('.sbx-out');
    var lines = s.split('\n');
    for (var i = 0; i < lines.length; i++) {
      var d = document.createElement('div');
      d.className = 'sbx-l' + (cls ? ' ' + cls : '');
      d.textContent = lines[i] || '\u00a0';
      box.appendChild(d);
    }
    box.scrollTop = box.scrollHeight;
  };

  /**
   * 往终端里"喂"一行命令：先回显 提示符+命令（注释灰色），再执行。
   * 练习场的「跑整段 / 执行下一行」就是逐行调它，跟人手敲完全等价。
   */
  Shell.prototype.feed = function (line) {
    var t = (line || '').replace(/\s+$/, '');
    if (!t.trim()) return;
    if (!this.el) { this.exec(t); return; }
    var box = this.el.querySelector('.sbx-out');
    var parts = splitLineNote(t.trim());
    var d = document.createElement('div');
    d.className = 'sbx-l cmd';
    d.appendChild(document.createTextNode(this.ps1() + ' ' + parts.cmd));
    if (parts.note) {
      var sp = document.createElement('span');
      sp.className = 'cmt';
      sp.textContent = '   # ' + parts.note;
      d.appendChild(sp);
    }
    box.appendChild(d);
    this.exec(t);
    var ps1 = this.el.querySelector('.sbx-ps1');
    if (ps1) ps1.textContent = this.ps1();
    box.scrollTop = box.scrollHeight;
  };

  /** 只清屏幕，不动文件系统 */
  Shell.prototype.clear = function () {
    this.buf = [];
    if (!this.el) return;
    var box = this.el.querySelector('.sbx-out');
    if (box) box.innerHTML = '';
    var ps1 = this.el.querySelector('.sbx-ps1');
    if (ps1) ps1.textContent = this.ps1();
  };

  /** 重置：freshFs 为真时文件系统也回到初始状态 */
  Shell.prototype.reset = function (freshFs) {
    if (freshFs) resetFs();
    this.cwd = ['home', 'autumn'];
    this.hist = [];
    this.hi = -1;
    this.clear();
    this.print('—— 环境已重置' + (freshFs ? '（文件系统回到初始状态）' : '') + ' ——', 'dim');
  };

  Shell.prototype.exec = function (line, silent) {
    line = (line || '').trim();
    if (!line) return '';
    if (this.hist[this.hist.length - 1] !== line) this.hist.push(line);
    var tok = lex(line);
    if (!tok.length) return '';

    var pipes = [[]];
    for (var i = 0; i < tok.length; i++) {
      if (tok[i] === '|') pipes.push([]);
      else if (tok[i] === ';' || tok[i] === '&') { if (pipes[pipes.length - 1].length) pipes.push([]); }
      else pipes[pipes.length - 1].push(tok[i]);
    }
    pipes = pipes.filter(function (p) { return p.length; });

    var stdin = '', whole = [];
    for (var p = 0; p < pipes.length; p++) {
      var seg = [], argi, one, gl;
      for (argi = 0; argi < pipes[p].length; argi++) {
        one = expand(pipes[p][argi], this);
        gl = globOne(one, this);
        if (Object.prototype.toString.call(gl) === '[object Array]') seg = seg.concat(gl);
        else seg.push(gl);
      }
      var redirect = null, append = false, toks = [];
      for (i = 0; i < seg.length; i++) {
        if (seg[i] === '>') { redirect = seg[i + 1]; i++; continue; }
        if (seg[i] === '>>') { redirect = seg[i + 1]; append = true; i++; continue; }
        if (seg[i] === '<') { stdin = (nodeAt(this, segsOf(this.cwd, seg[i + 1])) || { s: '' }).s || ''; i++; continue; }
        toks.push(seg[i]);
      }
      if (!toks.length) continue;
      var name = toks[0], args = toks.slice(1);
      if (this.alias[name]) {
        var ex = lex(this.alias[name]);
        name = ex[0]; args = ex.slice(1).concat(args);
      }
      var fn = CMDS[name];
      if (!fn) {
        // ./run.sh 形式
        if (name.indexOf('./') === 0 || name.indexOf('/') === 0) {
          var node = nodeAt(this, segsOf(this.cwd, name));
          if (node && node.t === 'f') {
            if (!(parseInt(node.mode, 10) & 1)) {
              whole.push('-bash: ' + name + ': Permission denied');
              break;
            }
            fn = function (sh, aa) { return runScript(sh, [name]); };
          }
        }
      }
      if (!fn) {
        whole.push('-bash: ' + name + ': command not found');
        break;
      }
      var r = fn(this, args, stdin) || {};
      if (r.clear) { if (this.el) this.el.querySelector('.sbx-out').innerHTML = ''; this.buf = []; continue; }
      if (r.e) whole.push(r.e);
      stdin = r.o || '';
      if (redirect) {
        var segs = segsOf(this.cwd, redirect);
        var parent = nodeAt(this, segs.slice(0, -1));
        if (!parent || parent.t !== 'd') whole.push('-bash: ' + redirect + ': No such file or directory');
        else {
          var nm = segs[segs.length - 1];
          var prev = append && parent.c[nm] ? parent.c[nm].s + '\n' : '';
          parent.c[nm] = file(prev + stdin);
        }
        stdin = '';
      }
    }
    var text = whole.join('\n');
    if (!silent) {
      if (this.el) { /* 输出在下面统一打印 */ }
      if (stdin) text = (text ? text + '\n' : '') + stdin;
      this.print(text);
    }
    return (text ? text + '\n' : '') + (silent ? stdin : '');
  };

  /** 供测试用：执行并返回输出（不带提示符） */
  Shell.prototype.run = function (line) {
    var before = this.buf.length;
    this.exec(line);
    return this.buf.slice(before).join('\n');
  };

  Shell.prototype.attach = function () {
    var self = this;
    var input = this.el.querySelector('.sbx-in');
    var ps1 = this.el.querySelector('.sbx-ps1');
    var rst = this.el.querySelector('.sbx-rst');
    if (ps1) ps1.textContent = this.ps1();

    function prompt() { if (ps1) ps1.textContent = self.ps1(); }

    this.print('IC 后端学院 · 模拟终端（' + this.preset + '）');
    this.print('这是练习用的环境，目录和真实工程一样。输入 help 看能用哪些命令，Tab 可以补全。', 'dim');

    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        var line = input.value;
        input.value = '';
        self.print(self.ps1() + ' ' + line, 'cmd');
        self.exec(line);
        prompt();
        e.preventDefault();
        return;
      }
      if (e.key === 'ArrowUp') {
        if (self.hist.length) {
          self.hi = self.hi < 0 ? self.hist.length - 1 : Math.max(0, self.hi - 1);
          input.value = self.hist[self.hi] || '';
        }
        e.preventDefault();
        return;
      }
      if (e.key === 'ArrowDown') {
        if (self.hi >= 0) {
          self.hi = Math.min(self.hist.length - 1, self.hi + 1);
          input.value = self.hist[self.hi] || '';
        }
        e.preventDefault();
        return;
      }
      if (e.key === 'Tab') {
        e.preventDefault();
        self.complete(input);
      }
      if (e.key === 'l' && e.ctrlKey) {
        e.preventDefault();
        self.el.querySelector('.sbx-out').innerHTML = '';
      }
    });

    this.el.addEventListener('click', function (ev) {
      if (ev.target.tagName !== 'BUTTON') input.focus();
    });

    if (rst) rst.addEventListener('click', function () {
      self.el.querySelector('.sbx-out').innerHTML = '';
      self.cwd = ['home', 'autumn'];
      self.buf = [];
      self.print('已重置到 ~（/home/autumn）。', 'dim');
      prompt();
      input.focus();
    });
  };

  Shell.prototype.complete = function (input) {
    var v = input.value;
    var parts = v.split(/\s+/);
    var last = parts[parts.length - 1] || '';
    var pool = [];
    if (parts.length <= 1) {
      pool = Object.keys(CMDS).filter(function (c) { return c.indexOf(last) === 0; }).sort();
    } else {
      var n = nodeAt(this, segsOf(this.cwd, last.indexOf('/') >= 0 ? last.replace(/[^/]*$/, '') || '/' : '.'));
      if (n && n.t === 'd') {
        var base = last.indexOf('/') >= 0 ? last.replace(/[^/]*$/, '') : '';
        pool = Object.keys(n.c).filter(function (k) { return k.indexOf(last.slice(base.length)) === 0; })
          .map(function (k) { return base + k; }).sort();
      }
    }
    if (!pool.length) return;
    if (pool.length === 1) {
      parts[parts.length - 1] = pool[0] + (pool[0].slice(-1) === '/' ? '' : ' ');
      input.value = parts.join(' ');
    } else {
      this.print(pool.join('  '), 'dim');
    }
  };

  /* ============================================================ 挂载 */
  function mountAll() {
    var nodes = document.querySelectorAll('.sbx[data-preset]'), list = [];
    for (var i = 0; i < nodes.length; i++) {
      if (nodes[i].getAttribute('data-ready')) { list.push(nodes[i].__sh || null); continue; }
      nodes[i].setAttribute('data-ready', '1');
      // 实例挂到节点上，页面脚本可以接着往里喂命令（练习场用）
      nodes[i].__sh = new Shell(nodes[i], nodes[i].getAttribute('data-preset'));
      list.push(nodes[i].__sh);
    }
    return list;
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', mountAll);
    } else {
      mountAll();
    }
  }

  var api = { Shell: Shell, mountAll: mountAll, resetFs: resetFs, splitLineNote: splitLineNote };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  global.MiniShell = api;
})(typeof window !== 'undefined' ? window : globalThis);
