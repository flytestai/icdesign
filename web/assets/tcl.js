/**
 * tcl.js — 浏览器内置 Tcl 解释器（课程练习用）
 * 覆盖：set/puts/append/incr/expr/unset/array(dict get)/list 全家桶/
 *       if·while·foreach·for/break·continue/proc(默认参数+args)/global/return/
 *       gets stdin/rand()；报错文案对齐真实 tclsh。
 *
 * 挂载点（由 build.py 生成）：
 *   .tsbx[data-code]  —— :::tclrun 预置代码块（含"运行这段代码"按钮）
 *   .tsbx             —— :::tclsh 空终端，自由敲命令
 *   #pg-code/#pg-run… —— /playground/ 练习场页面
 */
(function () {
'use strict';

/* ================================================================
 * 一、解释器核心
 * ================================================================ */

function TclError(msg) { this.msg = msg; }
TclError.prototype = Object.create(Error.prototype);
function BreakSig() {}
function ContinueSig() {}
function ReturnSig(value) { this.value = value; }

function Interp() {
  this.vars = Object.create(null);    // 顶层标量
  this.arrays = Object.create(null);  // 顶层数组 name -> {key:val}
  this.procs = Object.create(null);   // proc 名 -> {params:[{name,default}], body}
  this.frames = [];                   // proc 调用栈（局部变量）
  this.stdin = [];                    // gets stdin 的输入队列
  this.out = '';
}
Interp.prototype.write = function (s) { this.out += s; };

/* ---------- 变量读写（含 proc 局部作用域 / global） ---------- */
Interp.prototype.getVar = function (name) {
  if (this.frames.length) {
    var f = this.frames[this.frames.length - 1];
    if (name in f.globals) {
      if (name in this.vars) return this.vars[name];
      throw new TclError('can\'t read "' + name + '": no such variable');
    }
    if (name in f.vars) return f.vars[name];
    throw new TclError('can\'t read "' + name + '": no such variable');
  }
  if (name in this.vars) return this.vars[name];
  throw new TclError('can\'t read "' + name + '": no such variable');
};
Interp.prototype.setVar = function (name, val) {
  if (this.frames.length) {
    var f = this.frames[this.frames.length - 1];
    if (name in f.globals) { this.vars[name] = val; return val; }
    f.vars[name] = val; return val;
  }
  this.vars[name] = val; return val;
};
Interp.prototype.getArrayElem = function (arr, key) {
  var table;
  if (this.frames.length) {
    var f = this.frames[this.frames.length - 1];
    table = (arr in f.globals) ? this.arrays : f.arrays;
  } else table = this.arrays;
  if (!(arr in table)) {
    if (this.frames.length) {
      var g = this.frames[this.frames.length - 1].globals;
      if (arr in g && arr in this.arrays) table = this.arrays;
      else throw new TclError('can\'t read "' + arr + '": no such array');
    } else throw new TclError('can\'t read "' + arr + '": no such array');
  }
  if (!(key in table[arr]))
    throw new TclError('can\'t read "' + arr + '(' + key + ')": no such element in array');
  return table[arr][key];
};
Interp.prototype.setArrayElem = function (arr, key, val) {
  var table;
  if (this.frames.length) {
    var f = this.frames[this.frames.length - 1];
    table = (arr in f.globals) ? this.arrays : f.arrays;
  } else table = this.arrays;
  if (!(arr in table)) table[arr] = Object.create(null);
  table[arr][key] = val; return val;
};
Interp.prototype.unsetName = function (name) {
  var m = /^([^()]+)\((.*)\)$/.exec(name);
  if (m) {
    var arr = m[1], key = m[2];
    var table = this.frames.length
      ? ((arr in this.frames[this.frames.length - 1].globals) ? this.arrays : this.frames[this.frames.length - 1].arrays)
      : this.arrays;
    if (!(arr in table) || !(key in table[arr]))
      throw new TclError('can\'t unset "' + name + '": no such element in array');
    delete table[arr][key];
    return;
  }
  var table = this.frames.length
    ? ((name in this.frames[this.frames.length - 1].globals) ? this.vars : this.frames[this.frames.length - 1].vars)
    : this.vars;
  if (name in table) { delete table[name]; return; }
  if (name in this.arrays) { delete this.arrays[name]; return; }
  throw new TclError('can\'t unset "' + name + '": no such variable');
};

/* ---------- 词法：把一条命令拆成 words ---------- */
function splitCommands(src) {
  var cmds = [], cur = '', i = 0, n = src.length;
  var brace = 0, brack = 0, inq = false, atStart = true;
  while (i < n) {
    var c = src[i];
    if (atStart && cur.trim() === '' && c === '#') {           // 行首注释
      while (i < n && src[i] !== '\n') i++;
      atStart = true; continue;
    }
    if (inq) {
      if (c === '\\' && i + 1 < n) { cur += c + src[i + 1]; i += 2; continue; }
      if (c === '"') { inq = false; cur += c; i++; continue; }
      cur += c; i++; continue;
    }
    if (c === '"') { inq = true; cur += c; atStart = false; i++; continue; }
    if (c === '{') { brace++; cur += c; atStart = false; i++; continue; }
    if (c === '}') { brace--; cur += c; i++; continue; }
    if (c === '[') { brack++; cur += c; atStart = false; i++; continue; }
    if (c === ']') { brack--; cur += c; i++; continue; }
    if ((c === ';' || c === '\n') && brace === 0 && brack === 0) {
      if (cur.trim() !== '') cmds.push(cur);
      cur = ''; atStart = true; i++; continue;
    }
    if (c !== ' ' && c !== '\t') atStart = false;
    cur += c; i++;
  }
  if (cur.trim() !== '') cmds.push(cur);
  return cmds;
}

/* 读取 $var / ${var} / $arr(key)：返回 {text, arrKey|null, next} */
function readVarRef(s, i) {
  if (s[i] !== '$') return null;
  if (s[i + 1] === '{') {
    var j = s.indexOf('}', i + 2);
    if (j < 0) return null;
    return { text: s.slice(i + 2, j), arrKey: null, next: j + 1 };
  }
  var k = i + 1;
  while (k < s.length && /[A-Za-z0-9_]/.test(s[k])) k++;
  if (k === i + 1) return null;
  var name = s.slice(i + 1, k);
  if (s[k] === '(') {
    var p = s.indexOf(')', k + 1);
    if (p < 0) return null;
    return { text: name, arrKey: s.slice(k + 1, p), next: p + 1 };
  }
  return { text: name, arrKey: null, next: k };
}

/* 把一条命令字符串拆成 words：{k:'group',v} | {k:'quote'|'bare',segs} */
function parseWords(cmd) {
  var words = [], i = 0, n = cmd.length;
  while (i < n) {
    var c = cmd[i];
    if (c === ' ' || c === '\t' || c === '\n' || c === ';') { i++; continue; }
    if (c === '#') break;                                     // 词首 # 注释
    if (c === '{') {
      var d = 0, j = i, buf = '';
      while (j < n) {
        var ch = cmd[j];
        if (ch === '{') { d++; if (d > 1) buf += ch; j++; continue; }
        if (ch === '}') { d--; if (d === 0) { j++; break; } buf += ch; j++; continue; }
        buf += ch; j++;
      }
      words.push({ k: 'group', v: buf });
      i = j; continue;
    }
    if (c === '"') {
      var j = i + 1, segs = [], lit = '';
      while (j < n && cmd[j] !== '"') {
        var ch = cmd[j];
        if (ch === '\\' && j + 1 < n) {
          var nx = cmd[j + 1];
          lit += (nx === 'n') ? '\n' : (nx === 't') ? '\t' : nx;
          j += 2; continue;
        }
        if (ch === '[') {
          var dd = 0, k = j;
          while (k < n) { if (cmd[k] === '[') dd++; else if (cmd[k] === ']') { dd--; if (dd === 0) break; } k++; }
          if (lit) { segs.push({ t: 'lit', v: lit }); lit = ''; }
          segs.push({ t: 'cmd', v: cmd.slice(j + 1, k) });
          j = k + 1; continue;
        }
        if (ch === '$') {
          var r = readVarRef(cmd, j);
          if (r) { if (lit) { segs.push({ t: 'lit', v: lit }); lit = ''; }
            segs.push({ t: 'var', v: r.text, arrKey: r.arrKey }); j = r.next; continue; }
        }
        lit += ch; j++;
      }
      if (lit) segs.push({ t: 'lit', v: lit });
      words.push({ k: 'quote', segs: segs });
      i = j + 1; continue;
    }
    var segs = [], lit = '';
    while (i < n && cmd[i] !== ' ' && cmd[i] !== '\t' && cmd[i] !== '\n' && cmd[i] !== ';') {
      var ch = cmd[i];
      if (ch === '\\' && i + 1 < n) { lit += cmd[i + 1]; i += 2; continue; }
      if (ch === '[') {
        var dd = 0, k = i;
        while (k < n) { if (cmd[k] === '[') dd++; else if (cmd[k] === ']') { dd--; if (dd === 0) break; } k++; }
        if (lit) { segs.push({ t: 'lit', v: lit }); lit = ''; }
        segs.push({ t: 'cmd', v: cmd.slice(i + 1, k) });
        i = k + 1; continue;
      }
      if (ch === '$') {
        var r = readVarRef(cmd, i);
        if (r) { if (lit) { segs.push({ t: 'lit', v: lit }); lit = ''; }
          segs.push({ t: 'var', v: r.text, arrKey: r.arrKey }); i = r.next; continue; }
      }
      lit += ch; i++;
    }
    if (lit) segs.push({ t: 'lit', v: lit });
    words.push({ k: 'bare', segs: segs });
  }
  return words;
}

/* ---------- 列表解析 ---------- */
function splitList(s) {
  s = String(s);
  var elems = [], i = 0, n = s.length;
  while (i < n) {
    while (i < n && /\s/.test(s[i])) i++;
    if (i >= n) break;
    if (s[i] === '{') {
      var d = 0, j = i, inner = '';
      while (j < n) {
        if (s[j] === '{') { d++; if (d > 1) inner += '{'; j++; continue; }
        if (s[j] === '}') { d--; if (d === 0) { j++; break; } inner += '}'; j++; continue; }
        inner += s[j]; j++;
      }
      elems.push(inner); i = j;
    } else if (s[i] === '"') {
      var j = i + 1, inner = '';
      while (j < n && s[j] !== '"') {
        if (s[j] === '\\' && j + 1 < n) { inner += s[j + 1]; j += 2; continue; }
        inner += s[j]; j++;
      }
      elems.push(inner); i = j + 1;
    } else {
      var k = i;
      while (k < n && !/\s/.test(s[k])) k++;
      elems.push(s.slice(i, k)); i = k;
    }
  }
  return elems;
}
function splitListKeep(s) {
  s = String(s);
  var out = [], i = 0, n = s.length;
  while (i < n) {
    while (i < n && /\s/.test(s[i])) i++;
    if (i >= n) break;
    if (s[i] === '{') {
      var d = 0, j = i, inner = '';
      while (j < n) {
        if (s[j] === '{') { d++; if (d > 1) inner += '{'; j++; continue; }
        if (s[j] === '}') { d--; if (d === 0) { j++; break; } inner += '}'; j++; continue; }
        inner += s[j]; j++;
      }
      out.push({ v: inner, braced: true }); i = j;
    } else if (s[i] === '"') {
      var j = i + 1, inner = '';
      while (j < n && s[j] !== '"') {
        if (s[j] === '\\' && j + 1 < n) { inner += s[j + 1]; j += 2; continue; }
        inner += s[j]; j++;
      }
      out.push({ v: inner, braced: false }); i = j + 1;
    } else {
      var k = i;
      while (k < n && !/\s/.test(s[k])) k++;
      out.push({ v: s.slice(i, k), braced: false }); i = k;
    }
  }
  return out;
}
function listify(v) {
  v = String(v);
  if (v === '' || /[\s]/.test(v)) return '{' + v + '}';
  return v;
}
function indexNorm(idx, len) {
  var m = /^end(-(\d+))?$/.exec(String(idx));
  if (m) return len - 1 - (m[2] ? +m[2] : 0);
  return parseInt(idx, 10);
}

/* ---------- expr 表达式求值 ---------- */
function preSubst(ip, text) {
  var out = '', i = 0, n = text.length;
  while (i < n) {
    var c = text[i];
    if (c === '\\') { out += c + (text[i + 1] || ''); i += 2; continue; }
    if (c === '[') {
      var d = 0, k = i;
      while (k < n) { if (text[k] === '[') d++; else if (text[k] === ']') { d--; if (d === 0) break; } k++; }
      var val = ip.evalScript(text.slice(i + 1, k));
      out += (val === undefined ? '' : String(val));
      i = k + 1; continue;
    }
    if (c === '$') {
      var r = readVarRef(text, i);
      if (r) {
        var v = r.arrKey !== null
          ? ip.getArrayElem(r.text, preSubst(ip, r.arrKey))
          : ip.getVar(r.text);
        out += v; i = r.next; continue;
      }
    }
    out += c; i++;
  }
  return out;
}

function ExprParser(src) {
  this.s = src; this.i = 0;
}
ExprParser.prototype.ws = function () { while (this.i < this.s.length && /\s/.test(this.s[this.i])) this.i++; };
ExprParser.prototype.peek = function () { this.ws(); return this.s.substr(this.i, 2); };
ExprParser.prototype.num = function () {
  this.ws();
  var m = /^(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?/.exec(this.s.slice(this.i));
  if (!m) throw new TclError('expected integer but got "' + this.s.slice(this.i, this.i + 8) + '"');
  this.i += m[0].length;
  return { v: parseFloat(m[0]), isInt: !/[.eE]/.test(m[0]) };
};
ExprParser.prototype.primary = function (ip) {
  this.ws();
  if (this.i >= this.s.length) throw new TclError('unexpected end of subexpression');
  var c = this.s[this.i];
  if (c === '(') { this.i++; var v = this.expr(ip); this.ws(); if (this.s[this.i] === ')') this.i++; return v; }
  if (c === '-' || c === '+' || c === '!') {
    this.i++; var v = this.primary(ip);
    if (c === '!') return { v: this.truthy(v) ? 0 : 1, isInt: true };
    var nv = c === '-' ? -v.v : v.v;
    return { v: nv, isInt: v.isInt };
  }
  if (c === '"' || c === '{') {
    var end = c === '"' ? '"' : '}';
    var j = this.i + 1, buf = '';
    while (j < this.s.length && this.s[j] !== end) { buf += this.s[j]; j++; }
    this.i = j + 1;
    return { v: buf, isInt: false, str: true };
  }
  var m = /^[A-Za-z_][A-Za-z0-9_]*/.exec(this.s.slice(this.i));
  if (m) {
    var fn = m[0]; this.i += fn.length;
    this.ws();
    if (this.s[this.i] === '(') {
      this.i++;
      var args = [];
      while (true) {
        this.ws();
        if (this.s[this.i] === ')') { this.i++; break; }
        args.push(this.expr(ip));
        this.ws();
        if (this.s[this.i] === ',') { this.i++; continue; }
        if (this.s[this.i] === ')') { this.i++; break; }
        throw new TclError('syntax error in expression "' + this.s + '"');
      }
      return { v: applyFn(fn, args, ip), isInt: isIntRet(fn, args) };
    }
    // 裸布尔词 true/false
    if (fn === 'true') return { v: 1, isInt: true };
    if (fn === 'false') return { v: 0, isInt: true };
    throw new TclError('invalid bareword "' + fn + '"');
  }
  return this.num();
};
ExprParser.prototype.expr = function (ip) { return this.or(ip); };
ExprParser.prototype.or = function (ip) {
  var l = this.and(ip);
  while (this.peek() === '||') { this.i += 2; var r = this.and(ip);
    l = { v: (this._t(l) || this._t(r)) ? 1 : 0, isInt: true }; }
  return l;
};
ExprParser.prototype._t = function (x) { return this.truthy(x); };
ExprParser.prototype.truthy = function (x) {
  if (x.str) return x.v !== '' && x.v !== '0' && x.v !== 'false';
  return x.v !== 0;
};
ExprParser.prototype.and = function (ip) {
  var l = this.cmp(ip);
  while (this.peek() === '&&') { this.i += 2; var r = this.cmp(ip);
    l = { v: (this._t(l) && this._t(r)) ? 1 : 0, isInt: true }; }
  return l;
};
ExprParser.prototype.cmp = function (ip) {
  var l = this.add(ip);
  this.ws();
  var two = this.s.substr(this.i, 2);
  var op = null;
  if (['==', '!=', '<=', '>='].indexOf(two) >= 0) { op = two; this.i += 2; }
  else if ('<>='.indexOf(this.s[this.i]) >= 0 && this.s[this.i] !== undefined &&
           '=+'.indexOf(this.s[this.i + 1] || '') < 0) { op = this.s[this.i]; this.i++; }
  if (!op) return l;
  var r = this.add(ip);
  var res;
  var ln = parseFloat(l.v), rn = parseFloat(r.v);
  var numOp = !l.str && !r.str && !isNaN(ln) && !isNaN(rn);
  switch (op) {
    case '==': res = numOp ? ln === rn : String(l.v) === String(r.v); break;
    case '!=': res = numOp ? ln !== rn : String(l.v) !== String(r.v); break;
    case '<': res = numOp ? ln < rn : String(l.v) < String(r.v); break;
    case '>': res = numOp ? ln > rn : String(l.v) > String(r.v); break;
    case '<=': res = numOp ? ln <= rn : String(l.v) <= String(r.v); break;
    case '>=': res = numOp ? ln >= rn : String(l.v) >= String(r.v); break;
  }
  return { v: res ? 1 : 0, isInt: true };
};
ExprParser.prototype.add = function (ip) {
  var l = this.mul(ip);
  while (true) {
    this.ws();
    var c = this.s[this.i];
    if (c === '+' || c === '-') { this.i++; var r = this.mul(ip);
      l = { v: l.v + (c === '+' ? r.v : -r.v), isInt: l.isInt && r.isInt }; }
    else break;
  }
  return l;
};
ExprParser.prototype.mul = function (ip) {
  var l = this.unary(ip);
  while (true) {
    this.ws();
    var c = this.s[this.i];
    if (c === '*' || c === '/' || c === '%') {
      this.i++; var r = this.unary(ip);
      if (c === '*') l = { v: l.v * r.v, isInt: l.isInt && r.isInt };
      else if (c === '%') {
        if (!(l.isInt && r.isInt)) throw new TclError('expected integer');
        if (r.v === 0) throw new TclError('divide by zero');
        l = { v: ((l.v % r.v) + r.v) % r.v, isInt: true };
      } else {
        if (r.v === 0) throw new TclError('divide by zero');
        if (l.isInt && r.isInt) l = { v: Math.trunc(l.v / r.v), isInt: true };
        else l = { v: l.v / r.v, isInt: false };
      }
    } else break;
  }
  return l;
};
ExprParser.prototype.unary = function (ip) { return this.primary(ip); };

function applyFn(fn, args, ip) {
  var a = args.map(function (x) { return x.v; });
  switch (fn) {
    case 'int': return Math.trunc(a[0]);
    case 'double': case 'wide': return a[0];
    case 'abs': return Math.abs(a[0]);
    case 'round': return Math.round(a[0]);
    case 'floor': return Math.floor(a[0]);
    case 'ceil': return Math.ceil(a[0]);
    case 'sqrt': return Math.sqrt(a[0]);
    case 'pow': return Math.pow(a[0], a[1]);
    case 'max': return Math.max.apply(null, a);
    case 'min': return Math.min.apply(null, a);
    case 'rand': return Math.random();
    default: throw new TclError('unknown function "' + fn + '()" in expression');
  }
}
function isIntRet(fn, args) {
  if (fn === 'int' || fn === 'round' || fn === 'floor' || fn === 'ceil') return true;
  if (fn === 'max' || fn === 'min' || fn === 'abs') return args.every(function (x) { return x.isInt; });
  return false;
}

Interp.prototype.evalExprText = function (text) {
  var p = new ExprParser(preSubst(this, text));
  var r = p.expr(this);
  if (p.i < p.s.length && p.s.substr(p.i).trim() !== '')
    throw new TclError('invalid expression "' + text + '": extra tokens after expression');
  if (r.isInt) return String(Math.trunc(r.v));
  return String(r.v);
};

/* ---------- 命令求值 ---------- */
Interp.prototype.evalWord = function (w) {
  if (w.k === 'group') return w.v;
  var out = '';
  for (var i = 0; i < w.segs.length; i++) {
    var s = w.segs[i];
    if (s.t === 'lit') out += s.v;
    else if (s.t === 'var') {
      out += (s.arrKey !== null)
        ? this.getArrayElem(s.v, preSubst(this, s.arrKey))
        : this.getVar(s.v);
    } else if (s.t === 'cmd') {
      var v = this.evalScript(s.v);
      out += (v === undefined ? '' : String(v));
    }
  }
  return out;
};

Interp.prototype.rawArg = function (words, i) {
  var w = words[i];
  if (!w) throw new TclError('wrong # args: missing argument');
  return w.k === 'group' ? w.v : this.evalWord(w);
};

Interp.prototype.evalCommand = function (words) {
  if (!words.length) return undefined;
  var name = this.evalWord(words[0]);
  var R = this.rawArg.bind(this);
  var self = this;

  switch (name) {
    /* ---------- 变量 ---------- */
    case 'set': {
      if (words.length === 2) return this.readTarget(this.evalWord(words[1]));
      if (words.length !== 3) throw new TclError('wrong # args: should be "set varName ?newValue?"');
      var target = this.evalWord(words[1]);
      var val = this.evalWord(words[2]);
      var m = /^([^()]+)\((.*)\)$/.exec(target);
      if (m) return this.setArrayElem(m[1], preSubst(this, m[2]), val);
      return this.setVar(target, val);
    }
    case 'unset': {
      if (words.length < 2) throw new TclError('wrong # args: should be "unset ?-nocomplain? name ?name ...?"');
      for (var i2 = 1; i2 < words.length; i2++) this.unsetName(this.evalWord(words[i2]));
      return '';
    }
    case 'append': {
      if (words.length < 2) throw new TclError('wrong # args: should be "append varName ?value ...?"');
      var vn = this.evalWord(words[1]);
      var cur;
      try { cur = this.getVar(vn); } catch (e) { cur = ''; }
      var parts = [];
      for (var i3 = 2; i3 < words.length; i3++) parts.push(this.evalWord(words[i3]));
      return this.setVar(vn, cur + parts.join(''));
    }
    case 'incr': {
      if (words.length < 2 || words.length > 3)
        throw new TclError('wrong # args: should be "incr varName ?amount?"');
      var vn = this.evalWord(words[1]);
      var step = words.length === 3 ? this.evalWord(words[2]) : '1';
      if (!/^[+-]?\d+$/.test(step)) throw new TclError('expected integer but got "' + step + '"');
      var cur = this.readTarget(vn);
      if (!/^[+-]?\d+$/.test(cur)) throw new TclError('expected integer but got "' + cur + '"');
      return this.writeTarget(vn, String(parseInt(cur, 10) + parseInt(step, 10)));
    }
    case 'expr': {
      if (words.length < 2) throw new TclError('wrong # args: should be "expr arg ?arg ...?"');
      if (words.length === 2 && words[1].k === 'group') return this.evalExprText(words[1].v);
      var parts = [];
      for (var i4 = 1; i4 < words.length; i4++) parts.push(this.evalWord(words[i4]));
      return this.evalExprText(parts.join(' '));
    }
    /* ---------- 数组 / 字典 ---------- */
    case 'array': {
      if (words.length < 3) throw new TclError('wrong # args: should be "array subcommand arrayName ?arg ...?"');
      var sub = this.evalWord(words[1]);
      var an = this.evalWord(words[2]);
      if (/\(/.test(an)) throw new TclError('array subcommand: first argument "' + an + '" must be a plain array name (no key)');
      var table = this.arrayTable(an);
      if (sub === 'set') {
        if (words.length !== 4) throw new TclError('wrong # args: should be "array set arrayName list"');
        var flat = splitList(this.evalWord(words[3]));
        if (flat.length % 2) throw new TclError('list must have an even number of elements');
        if (!(an in table)) table[an] = Object.create(null);
        for (var i5 = 0; i5 < flat.length; i5 += 2) table[an][flat[i5]] = flat[i5 + 1];
        return '';
      }
      if (!(an in table)) table[an] = Object.create(null);
      var keys = Object.keys(table[an]);
      if (sub === 'names') {
        var pat = words.length > 3 ? this.evalWord(words[3]) : null;
        if (pat) keys = keys.filter(globMatch.bind(null, pat));
        return keys.join(' ');
      }
      if (sub === 'get') {
        var out = [];
        for (var i6 = 0; i6 < keys.length; i6++) out.push(keys[i6], table[an][keys[i6]]);
        return out.map(listify).join(' ');
      }
      if (sub === 'size') return String(keys.length);
      if (sub === 'exists') return (an in table) ? '1' : '0';
      throw new TclError('unknown or ambiguous subcommand "' + sub + '": must be exists, get, names, set, size, unset');
    }
    case 'dict': {
      if (words.length < 3) throw new TclError('wrong # args: should be "dict subcommand ?arg ...?"');
      var dsub = this.evalWord(words[1]);
      if (dsub !== 'get') throw new TclError('练习场只支持 dict get（课程范围内够用）');
      var dv = this.evalWord(words[2]);
      var pairs = splitList(dv);
      var keys = [];
      for (var i7 = 3; i7 < words.length; i7++) keys.push(this.evalWord(words[i7]));
      var cur = pairs;
      for (var i8 = 0; i8 < keys.length; i8++) {
        var found = null;
        for (var j2 = 0; j2 + 1 < cur.length; j2 += 2)
          if (cur[j2] === keys[i8]) { found = cur[j2 + 1]; break; }
        if (found === null) throw new TclError('key "' + keys[i8] + '" not found in dictionary');
        if (i8 === keys.length - 1) return found;
        cur = splitList(found);
      }
      return '';
    }
    /* ---------- 列表 ---------- */
    case 'list': {
      var els = [];
      for (var i9 = 1; i9 < words.length; i9++) els.push(this.evalWord(words[i9]));
      return els.map(listify).join(' ');
    }
    case 'lindex': {
      if (words.length < 2) throw new TclError('wrong # args: should be "lindex list ?index ...?"');
      var elems = splitList(this.evalWord(words[1]));
      for (var i10 = 2; i10 < words.length; i10++) {
        var idx = indexNorm(this.evalWord(words[i10]), elems.length);
        var got = (idx >= 0 && idx < elems.length) ? elems[idx] : '';
        elems = (i10 + 1 < words.length) ? splitList(got) : [got];
      }
      return elems.length ? elems[0] : '';
    }
    case 'llength': return String(splitList(this.evalWord(words[1])).length);
    case 'lappend': {
      if (words.length < 2) throw new TclError('wrong # args: should be "lappend varName ?element ...?"');
      var vn2 = this.evalWord(words[1]);
      var curList;
      try { curList = this.getVar(vn2); } catch (e) { curList = ''; }
      var els2 = splitList(curList);
      for (var i11 = 2; i11 < words.length; i11++) els2.push(this.evalWord(words[i11]));
      return this.writeTarget(vn2, els2.map(listify).join(' '));
    }
    case 'lreplace': {
      if (words.length < 4) throw new TclError('wrong # args: should be "lreplace list first last ?element ...?"');
      var els3 = splitList(this.evalWord(words[1]));
      var f = indexNorm(this.evalWord(words[2]), els3.length);
      var l2 = indexNorm(this.evalWord(words[3]), els3.length);
      var news = [];
      for (var i12 = 4; i12 < words.length; i12++) news.push(this.evalWord(words[i12]));
      var head = els3.slice(0, Math.max(0, f));
      var tail = els3.slice(Math.min(l2 + 1, els3.length));
      return head.concat(news, tail).map(listify).join(' ');
    }
    case 'lsearch': {
      if (words.length < 3) throw new TclError('wrong # args: should be "lsearch list pattern"');
      var els4 = splitList(this.evalWord(words[1]));
      var pat = this.evalWord(words[2]);
      for (var i13 = 0; i13 < els4.length; i13++)
        if (els4[i13] === pat) return String(i13);
      return '-1';
    }
    case 'lsort': {
      var flags = { integer: false, dec: false };
      var start = 1;
      while (start < words.length && /^-/.test(words[start].segs ? words[start].segs.map(function (x) { return x.v; }).join('') : words[start].v)) {
        var fl = this.evalWord(words[start]);
        if (fl === '-integer' || fl === '-real') flags.integer = true;
        else if (fl === '-decreasing') flags.dec = true;
        else if (fl === '-increasing' || fl === '-ascii') { /* 默认 */ }
        else throw new TclError('bad option "' + fl + '": must be -ascii, -decreasing, -increasing, -integer, -real');
        start++;
      }
      if (words.length - start < 1) throw new TclError('wrong # args: should be "lsort ?option...? list"');
      var els5 = splitList(this.evalWord(words[start]));
      var sorted = els5.slice().sort(function (x, y) {
        if (flags.integer) return (parseFloat(x) - parseFloat(y));
        return x < y ? -1 : x > y ? 1 : 0;
      });
      if (flags.dec) sorted.reverse();
      return sorted.map(listify).join(' ');
    }
    case 'concat': {
      var all = [];
      for (var i14 = 1; i14 < words.length; i14++) all = all.concat(splitList(this.evalWord(words[i14])));
      return all.map(listify).join(' ');
    }
    case 'split': {
      if (words.length < 2) throw new TclError('wrong # args: should be "split string ?splitChars?"');
      var str = this.evalWord(words[1]);
      var seps = words.length > 2 ? this.evalWord(words[2]) : ' \t\n';
      if (seps === '') return [str].map(listify).join(' ');
      var outEls = [], buf = '';
      for (var i15 = 0; i15 < str.length; i15++) {
        if (seps.indexOf(str[i15]) >= 0) { outEls.push(buf); buf = ''; }
        else buf += str[i15];
      }
      outEls.push(buf);
      return outEls.map(listify).join(' ');
    }
    case 'join': {
      if (words.length < 2) throw new TclError('wrong # args: should be "join list ?joinString?"');
      var els6 = splitList(this.evalWord(words[1]));
      var sep = words.length > 2 ? this.evalWord(words[2]) : ' ';
      return els6.join(sep);
    }
    /* ---------- 流程控制 ---------- */
    case 'if': return this.cmdIf(words);
    case 'while': {
      if (words.length !== 3) throw new TclError('wrong # args: should be "while test command"');
      var guard = 0;
      while (parseInt(this.evalExprText(R(words, 1)), 10) !== 0) {
        if (++guard > 200000) throw new TclError('死循环保护：while 跑了 20 万次还没停，检查是不是忘了"更新"');
        try { this.evalScript(R(words, 2)); }
        catch (e) { if (e instanceof BreakSig) break; if (!(e instanceof ContinueSig)) throw e; }
      }
      return '';
    }
    case 'for': {
      if (words.length !== 5) throw new TclError('wrong # args: should be "for start test next command"');
      this.evalScript(R(words, 1));
      var guard2 = 0;
      while (parseInt(this.evalExprText(R(words, 2)), 10) !== 0) {
        if (++guard2 > 200000) throw new TclError('死循环保护：for 跑了 20 万次还没停，检查条件或步进');
        try { this.evalScript(R(words, 4)); }
        catch (e) { if (e instanceof BreakSig) break; if (!(e instanceof ContinueSig)) throw e; }
        this.evalScript(R(words, 3));
      }
      return '';
    }
    case 'foreach': {
      if (words.length !== 4) throw new TclError('wrong # args: should be "foreach varList list command"');
      var varNames = splitList(R(words, 1));
      var items = splitList(this.evalWord(words[2]));
      var step = varNames.length;
      for (var i16 = 0; i16 < items.length; i16 += step) {
        for (var j3 = 0; j3 < step; j3++) {
          this.writeTarget(varNames[j3], (i16 + j3 < items.length) ? items[i16 + j3] : '');
        }
        try { this.evalScript(R(words, 3)); }
        catch (e) { if (e instanceof BreakSig) break; if (!(e instanceof ContinueSig)) throw e; }
      }
      return '';
    }
    case 'break': throw new BreakSig();
    case 'continue': throw new ContinueSig();
    case 'return': {
      if (words.length > 2) throw new TclError('wrong # args: should be "return ?-code c? ?-errorinfo i? ?-errorcode e? ?msg?"');
      throw new ReturnSig(words.length === 2 ? this.evalWord(words[1]) : '');
    }
    case 'proc': {
      if (words.length !== 4) throw new TclError('wrong # args: should be "proc name args body"');
      var pname = this.evalWord(words[1]);
      var paramItems = splitListKeep(R(words, 2));
      var params = [];
      for (var i17 = 0; i17 < paramItems.length; i17++) {
        var pw = paramItems[i17];
        if (pw.braced) {
          var kv = splitList(pw.v);
          if (kv.length !== 2) throw new TclError('bad default parameter "' + pw.v + '"');
          params.push({ name: kv[0], def: kv[1] });
        } else {
          if (params.length && params[params.length - 1].def !== undefined)
            throw new TclError('非默认参数不能排在默认参数后面');
          params.push({ name: pw.v, def: undefined });
        }
      }
      this.procs[pname] = { params: params, body: R(words, 3) };
      return '';
    }
    case 'global': {
      if (!this.frames.length) return '';
      var f = this.frames[this.frames.length - 1];
      for (var i18 = 1; i18 < words.length; i18++) f.globals[this.evalWord(words[i18])] = true;
      return '';
    }
    /* ---------- 输入输出 ---------- */
    case 'puts': {
      var nl = true, start2 = 1;
      if (words[start2] && this.evalWord(words[start2]) === '-nonewline') { nl = false; start2++; }
      if (words[start2] && this.evalWord(words[start2]) === 'stderr') start2++;
      if (words.length < start2 + 1 || words.length > start2 + 2)
        throw new TclError('wrong # args: should be "puts ?-nonewline? ?channelId? string"');
      this.write(this.evalWord(words[start2]) + (nl ? '\n' : ''));
      return '';
    }
    case 'gets': {
      if (words.length < 3) throw new TclError('wrong # args: should be "gets channelId ?varName?"');
      var ch = this.evalWord(words[1]);
      if (ch !== 'stdin') throw new TclError('can\'t find channel named "' + ch + '"');
      var line = this.stdin.length ? this.stdin.shift() : '';
      var vn3 = this.evalWord(words[2]);
      this.writeTarget(vn3, line);
      return String(line.length);
    }
    case 'source': throw new TclError('练习场不支持 source：把脚本内容直接粘进来即可');
    case 'info': return '练习场简化版（完整 info 子命令不在此列）';
    case 'string': {
      if (words.length < 3) throw new TclError('wrong # args: should be "string subcommand string ?arg...?"');
      var ssub = this.evalWord(words[1]);
      var sv = this.evalWord(words[2]);
      if (ssub === 'length') return String(sv.length);
      if (ssub === 'trim') return sv.trim();
      if (ssub === 'toupper') return sv.toUpperCase();
      if (ssub === 'tolower') return sv.toLowerCase();
      if (ssub === 'index') return sv[parseInt(this.evalWord(words[3]), 10)] || '';
      if (ssub === 'range') {
        var a = indexNorm(this.evalWord(words[3]), sv.length), b = indexNorm(this.evalWord(words[4]), sv.length);
        return sv.slice(a, b + 1);
      }
      throw new TclError('unknown or ambiguous subcommand "' + ssub + '"');
    }
    default:
      if (name in this.procs) return this.callProc(name, words.slice(1));
      if (name in EDA_STUBS) return edaStub(this, name, words.slice(1));
      throw new TclError('invalid command name "' + name + '"');
  }
};

/* set/incr 等用的"读/写目标"工具（兼容 arr(key) 与标量） */
Interp.prototype.readTarget = function (target) {
  var m = /^([^()]+)\((.*)\)$/.exec(target);
  if (m) return this.getArrayElem(m[1], preSubst(this, m[2]));
  return this.getVar(target);
};
Interp.prototype.writeTarget = function (target, val) {
  var m = /^([^()]+)\((.*)\)$/.exec(target);
  if (m) return this.setArrayElem(m[1], preSubst(this, m[2]), val);
  return this.setVar(target, val);
};
Interp.prototype.arrayTable = function (an) {
  if (this.frames.length) {
    var f = this.frames[this.frames.length - 1];
    return (an in f.globals) ? this.arrays : f.arrays;
  }
  return this.arrays;
};
function splitListListLen(x) { return x.length; }
function globMatch(pat, s) {
  var rx = '^' + pat.replace(/[.+^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*').replace(/\?/g, '.') + '$';
  return new RegExp(rx).test(s);
}


/* EDA 工具命令桩：课程示例里出现的 Innovus/ICC2 命令，练习台按"假装执行"处理 */
var EDA_STUBS = {
  'get_cells': 'get', 'get_ports': 'get', 'get_pins': 'get', 'get_nets': 'get', 'get_clocks': 'get',
  'change_selection': 'act', 'deselect_all': 'act', 'select_objects': 'act',
  'move_objects': 'act', 'zoom_fit': 'act', 'fit_view': 'act', 'clear_selection': 'act',
  'place_design': 'act', 'cts_design': 'act', 'route_design': 'act', 'set_clock': 'act',
  'report_timing': 'act', 'report_area': 'act', 'report_power': 'act', 'place_opt_design': 'act'
};
function edaStub(ip, name, argWords) {
  var args = [];
  for (var i = 0; i < argWords.length; i++) args.push(ip.evalWord(argWords[i]));
  if (EDA_STUBS[name] === 'get') return args.join(' ');   // get_* 返回查到的对象名
  return '';                                              // 动作类命令静默执行
}


Interp.prototype.cmdIf = function (words) {
  var i = 1;
  while (true) {
    if (i + 1 >= words.length && words[i] && this.evalWord(words[i]) === 'else')
      throw new TclError('wrong # args: no body after else');
    if (i >= words.length) throw new TclError('wrong # args: should be "if condition body ?elseif...? ?else?"');
    var cond = this.rawArg(words, i);
    var body = this.rawArg(words, i + 1);
    if (parseInt(this.evalExprText(cond), 10) !== 0) return this.evalScript(body);
    i += 2;
    if (i >= words.length) return '';
    var kw = this.evalWord(words[i]);
    if (kw === 'elseif') { i++; continue; }
    if (kw === 'else') { return this.evalScript(this.rawArg(words, i + 1)); }
    throw new TclError('wrong # args: expected "elseif" or "else" but got "' + kw + '"');
  }
};

Interp.prototype.callProc = function (name, argWords) {
  var p = this.procs[name];
  var args = [];
  for (var i = 0; i < argWords.length; i++) args.push(this.evalWord(argWords[i]));
  var locals = Object.create(null);
  var nFixed = 0;
  for (var j = 0; j < p.params.length; j++) {
    if (p.params[j].def === undefined) nFixed++;
    else break;
  }
  if (args.length < nFixed)
    throw new TclError('wrong # args: should be "' + name + ' ' + p.params.map(function (x) { return x.name; }).join(' ') + '"');
  var varargs = p.params.length && p.params[p.params.length - 1].name === 'args';
  if (!varargs && args.length > p.params.length && p.params[p.params.length - 1].def === undefined)
    throw new TclError('wrong # args: should be "' + name + ' ' + p.params.map(function (x) { return x.name; }).join(' ') + '"');
  for (var k2 = 0; k2 < p.params.length; k2++) {
    var pm = p.params[k2];
    if (pm.name === 'args') { locals['args'] = args.slice(k2).map(listify).join(' '); break; }
    if (k2 < args.length) locals[pm.name] = args[k2];
    else locals[pm.name] = pm.def;
  }
  this.frames.push({ vars: locals, arrays: Object.create(null), globals: Object.create(null) });
  try {
    return this.evalScript(p.body);
  } catch (e) {
    if (e instanceof ReturnSig) return e.value;
    throw e;
  } finally {
    this.frames.pop();
  }
};

/* 整段脚本求值：返回最后一条命令的结果 */
Interp.prototype.evalScript = function (src) {
  var result;
  var cmds = splitCommands(String(src));
  for (var i = 0; i < cmds.length; i++) {
    var words = parseWords(cmds[i]);
    if (!words.length) continue;
    result = this.evalCommand(words);
  }
  return result;
};

/* 判断脚本是否"没写完"（花括号/方括号/引号不平衡）→ 续行 */
function isComplete(src) {
  var brace = 0, brack = 0, inq = false, i = 0, n = src.length;
  while (i < n) {
    var c = src[i];
    if (inq) {
      if (c === '\\') { i += 2; continue; }
      if (c === '"') inq = false;
      i++; continue;
    }
    if (c === '"') { inq = true; i++; continue; }
    if (c === '{') brace++;
    else if (c === '}') brace--;
    else if (c === '[') brack++;
    else if (c === ']') brack--;
    else if (c === '\\') { i++; }
    i++;
  }
  return brace <= 0 && brack <= 0 && !inq;
}

/* ================================================================
 * 二、界面挂载
 * ================================================================ */

function escHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
function fmtErr(e) {
  return (e instanceof TclError) ? e.msg : (e.message || String(e));
}

function Console(outEl, ip) {
  this.el = outEl; this.ip = ip;
}
Console.prototype.print = function (text, cls) {
  var div = document.createElement('div');
  div.className = 'sbx-l' + (cls ? ' ' + cls : '');
  div.innerHTML = escHtml(text).replace(/\n/g, '<br>') || '&nbsp;';
  this.el.appendChild(div);
  this.el.scrollTop = this.el.scrollHeight;
};
Console.prototype.runScript = function (code) {
  var ip = this.ip;
  try {
    ip.evalScript(code);
    if (ip.out) { this.print(ip.out); ip.out = ''; }
  } catch (e) {
    if (ip.out) { this.print(ip.out); ip.out = ''; }
    if (e instanceof BreakSig) this.print('% break 出现在循环外', 'err');
    else if (e instanceof ContinueSig) this.print('% continue 出现在循环外', 'err');
    else this.print('% ' + fmtErr(e), 'err');
  }
};

/* ---------- 课程内练习台 .tsbx ---------- */
function mountTsbx(root) {
  var outEl = root.querySelector('.sbx-out');
  var input = root.querySelector('.sbx-in');
  var ps1 = root.querySelector('.sbx-ps1');
  var rst = root.querySelector('.sbx-rst');
  var goBtn = root.querySelector('.tcl-go');
  var ip = new Interp();
  var con = new Console(outEl, ip);
  var buf = '';

  function fresh() { ip = new Interp(); con.ip = ip; buf = ''; outEl.innerHTML = ''; }
  rst.addEventListener('click', function () { fresh(); con.print('—— 已重置 ——', 'dim'); });

  if (goBtn && root.dataset.code) {
    goBtn.addEventListener('click', function () {
      con.runScript(root.dataset.code);
      con.print('', '');
    });
  }

  function submit() {
    var line = input.value;
    con.print((buf ? '...> ' : 'tclsh> ') + line, 'in');
    var combined = buf ? buf + '\n' + line : line;
    if (!isComplete(combined)) { buf = combined; input.value = ''; if (ps1) ps1.textContent = '...>'; return; }
    buf = '';
    if (ps1) ps1.textContent = 'tclsh>%';
    con.runScript(combined);
    input.value = '';
  }
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); submit(); }
  });
  root.addEventListener('click', function (e) {
    if (e.target === outEl) input.focus();
  });
}

/* ---------- 练习场 /playground/ ---------- */
var EXAMPLES = [
  { name: '① 变量与 puts（第 1-2 课）', code:
'puts "Hello, TCL!"\n' +
'set name "Zhang San"   ;# 字符串变量\n' +
'set age 25             ;# 数值变量\n' +
'set score 98.5         ;# 浮点型变量\n' +
'puts "姓名：$name，年龄：$age，成绩：$score"\n' +
'\n' +
'set a.1 100\n' +
'puts ${a.1}            ;# 特殊变量名要用 \\${} 包裹\n' +
'\n' +
'set info {age 20 name zhangsan}\n' +
'puts [dict get $info age]' },
  { name: '② 三剑客 append/incr/expr（第 3 课）', code:
'set str "Hello"\n' +
'append str " " "World" "!"\n' +
'puts $str\n' +
'\n' +
'set num1 10\n' +
'incr num1      ;# +1\n' +
'incr num1 5    ;# +5\n' +
'incr num1 -3   ;# -3\n' +
'puts "num1最终值：$num1"\n' +
'\n' +
'set a 3\n' +
'set b 5\n' +
'puts [expr {$b / $a}]    ;# 整数除法：5/3=1\n' +
'puts [expr {5.0 / $a}]   ;# 浮点除法' },
  { name: '③ 数组与遍历（第 4 课）', code:
'set student(001) "Xiao Ming"\n' +
'set student(002) "Xiao Fang"\n' +
'set student(class) "三年级2班"\n' +
'puts "学号001：$student(001)"\n' +
'\n' +
'array set product {id001 手机 id002 电脑 id003 平板}\n' +
'foreach key [array names product] {\n' +
'    puts "产品$key：$product($key)"\n' +
'}\n' +
'foreach {k v} [array get product] {\n' +
'    puts "key=$k val=$v"\n' +
'}\n' +
'unset product(id002)\n' +
'puts "还剩 [array size product] 个产品：[array get product]"' },
  { name: '④ 列表全家桶（第 5-6 课）', code:
'set num_list [list 1 2 3 4 5]\n' +
'puts "列表：$num_list"\n' +
'puts "第3个元素：[lindex $num_list 2]，长度：[llength $num_list]"\n' +
'\n' +
'lappend num_list 6 7        ;# 修改源数据\n' +
'puts "lappend 后：$num_list"\n' +
'\n' +
'set new_list [lreplace $num_list 1 2 apple]  ;# 不改源数据\n' +
'puts "lreplace 后新列表：$new_list"\n' +
'puts "源列表没变：$num_list"\n' +
'\n' +
'puts "找到 3 的索引：[lsearch $num_list 3]"\n' +
'puts "数字排序：[lsort -integer {10 9 2 100}]"\n' +
'puts "字符串排序：[lsort {10 9 2 100}]  ;# 字典序陷阱！"\n' +
'puts "拼接：[concat {1 2} {3 4}]"\n' +
'puts "split：[split "woaixuexi" x]  join：[join {a b c} -]"\n' +
'\n' +
'set class_list {\n' +
'    {001 "Xiao Ming" 95}\n' +
'    {002 "Xiao Fang" 92}\n' +
'}\n' +
'puts "嵌套取值：[lindex $class_list 1 1]"' },
  { name: '⑤ 条件判断 + gets 输入（第 7 课，先在 stdin 框写 85）', code:
'puts "Please enter the score："\n' +
'gets stdin score\n' +
'if {$score >= 90} {\n' +
'    puts "成绩等级：A（优秀）"\n' +
'} elseif {$score >= 80} {\n' +
'    puts "成绩等级：B（良好）"\n' +
'} elseif {$score >= 60} {\n' +
'    puts "成绩等级：C（及格）"\n' +
'} else {\n' +
'    puts "成绩等级：D（不及格）"\n' +
'}\n' +
'puts "再来个随机数：[expr {rand()}]"' },
  { name: '⑥ 三种循环（第 8 课）', code:
'# while 三要素：初始化→判断→更新\n' +
'set i 0\n' +
'while {$i < 5} {\n' +
'    puts "i = $i"\n' +
'    incr i\n' +
'}\n' +
'\n' +
'# 倒序复制列表\n' +
'set source_list {100 200 300 400 500}\n' +
'set target_list ""\n' +
'set i [expr {[llength $source_list] - 1}]\n' +
'while {$i >= 0} {\n' +
'    lappend target_list [lindex $source_list $i]\n' +
'    incr i -1\n' +
'}\n' +
'puts "倒序列表：$target_list"\n' +
'\n' +
'# foreach 求和 / for 计数\n' +
'set num_list {1 2 3 4 5}\n' +
'set sum 0\n' +
'foreach num $num_list {\n' +
'    set sum [expr {$sum + $num}]\n' +
'}\n' +
'puts "列表元素总和：$sum"\n' +
'\n' +
'for {set j 0} {$j < 3} {incr j} {\n' +
'    puts "for 第 $j 轮"\n' +
'}' },
  { name: '⑦ 函数 proc（第 9 课）', code:
'proc sayHello {} {\n' +
'    puts "Hello, Tcl!"\n' +
'}\n' +
'sayHello\n' +
'\n' +
'proc add {a b} {\n' +
'    return [expr {$a + $b}]\n' +
'}\n' +
'puts "10 + 20 = [add 10 20]"\n' +
'\n' +
'proc addDefault {a {b 5}} {\n' +
'    return [expr {$a + $b}]\n' +
'}\n' +
'puts "[addDefault 3]  /  [addDefault 3 7]"\n' +
'\n' +
'proc sumAll {args} {\n' +
'    set total 0\n' +
'    foreach num $args {\n' +
'        set total [expr {$total + $num}]\n' +
'    }\n' +
'    return $total\n' +
'}\n' +
'puts "sumAll 1..5 = [sumAll 1 2 3 4 5]"\n' +
'\n' +
'set globalVal 100\n' +
'proc testGlobal {} {\n' +
'    global globalVal\n' +
'    set localVal 200\n' +
'    puts "全局 $globalVal / 局部 $localVal"\n' +
'}\n' +
'testGlobal' },
  { name: '⑧ EDA 风格综合（第 10 课）', code:
'# 模拟版图工具里批量处理内存单元\n' +
'set mem_list {\n' +
'    I_CONTEXT_MEM/I_CONTEXT_RAM_0_4\n' +
'    I_CONTEXT_MEM/I_CONTEXT_RAM_0_3\n' +
'    I_CONTEXT_MEM/I_CONTEXT_RAM_0_2\n' +
'}\n' +
'proc report {mem idx total} {\n' +
'    puts "进度：$idx / $total —— 正在处理：$mem"\n' +
'}\n' +
'set total [llength $mem_list]\n' +
'set idx 0\n' +
'foreach mem $mem_list {\n' +
'    incr idx\n' +
'    report $mem $idx $total\n' +
'    puts "  change_selection [get_cells $mem]"   ;# 工具命令这里用 puts 模拟\n' +
'    puts "  move_objects -delta {-50 0}"\n' +
'}\n' +
'puts "全部 $total 个单元处理完毕"' },
  { name: '⑨ 猜数字游戏（把 3 次猜测写进 stdin 框）', code:
'set answer [expr {int(rand()*100)}]\n' +
'set times 0\n' +
'while {1} {\n' +
'    incr times\n' +
'    puts "第 $times 次猜：请输入 0-99 的数字"\n' +
'    gets stdin guess\n' +
'    if {$guess == $answer} {\n' +
'        puts "猜对了！答案是 $answer"\n' +
'        break\n' +
'    } elseif {$guess > $answer} {\n' +
'        puts "大了"\n' +
'    } else {\n' +
'        puts "小了"\n' +
'    }\n' +
'}' }
];

function mountPlayground() {
  var codeEl = document.getElementById('pg-code');
  if (!codeEl) return;
  var outEl = document.getElementById('pg-out');
  var stdinEl = document.getElementById('pg-stdin');
  var sel = document.getElementById('pg-example');
  var KEY = 'tcl_pg_code_v1';
  try {
    var saved = localStorage.getItem(KEY);
    if (saved) codeEl.value = saved;
  } catch (e) {}

  EXAMPLES.forEach(function (ex, i) {
    var o = document.createElement('option');
    o.value = String(i); o.textContent = ex.name;
    sel.appendChild(o);
  });
  sel.addEventListener('change', function () {
    if (sel.value === '') return;
    codeEl.value = EXAMPLES[+sel.value].code;
    save();
  });
  function save() { try { localStorage.setItem(KEY, codeEl.value); } catch (e) {} }
  function run() {
    var ip = new Interp();
    ip.stdin = stdinEl.value.split('\n').filter(function (x) { return x !== ''; });
    var con = new Console(outEl, ip);
    con.print('% tclsh 运行开始', 'dim');
    con.runScript(codeEl.value);
    if (ip.stdin.length) con.print('% stdin 还有 ' + ip.stdin.length + ' 行没被读走（gets stdin 没用到？）', 'dim');
    con.print('% 运行结束', 'dim');
    save();
  }
  document.getElementById('pg-run').addEventListener('click', run);
  document.getElementById('pg-clear').addEventListener('click', function () { outEl.innerHTML = ''; });
  document.getElementById('pg-reset').addEventListener('click', function () {
    codeEl.value = EXAMPLES[0].code; stdinEl.value = ''; outEl.innerHTML = '';
    try { localStorage.removeItem(KEY); } catch (e) {}
  });
  codeEl.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); run(); }
    if (e.key === 'Tab') {
      e.preventDefault();
      var s = codeEl.selectionStart;
      codeEl.value = codeEl.value.slice(0, s) + '    ' + codeEl.value.slice(codeEl.selectionEnd);
      codeEl.selectionStart = codeEl.selectionEnd = s + 4;
    }
  });
}

function mountAll() {
  var nodes = document.querySelectorAll('.tsbx');
  for (var i = 0; i < nodes.length; i++) mountTsbx(nodes[i]);
  mountPlayground();
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mountAll);
  else mountAll();
}

/* ================================================================
 * 三、Node 环境自测导出（浏览器里无副作用）
 * ================================================================ */
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { Interp: Interp, TclError: TclError, splitList: splitList, isComplete: isComplete, splitListKeep: splitListKeep };
}
})();
