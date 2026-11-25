/* IC 后端学院 · 前端交互：进度同步 / 目录 / 术语卡 / 自测 / 代码复制 */
(function () {
  'use strict';
  var API = '/api';
  var LS_UID = 'icl.uid', LS_DONE = 'icl.done', LS_QUEUE = 'icl.queue';

  function uid() {
    var u = localStorage.getItem(LS_UID);
    if (!u) {
      u = 'u' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
      localStorage.setItem(LS_UID, u);
    }
    return u;
  }
  function loadDone() {
    try { return JSON.parse(localStorage.getItem(LS_DONE) || '{}'); } catch (e) { return {}; }
  }
  function saveDone(d) { localStorage.setItem(LS_DONE, JSON.stringify(d)); }

  var done = loadDone();
  var lessonId = document.body.getAttribute('data-lesson') || '';
  var isLesson = lessonId !== 'home' && lessonId !== '';
  var sections = [].slice.call(document.querySelectorAll('section.ch'));
  var below = {};                        // 章 → 底边是否已在视口 65% 线上方（跨越检测基线）
  var reanchor = null;                   // 服务器进度回填后校正落点（课程页赋值）

  /* ---------------- 进度（滚动自动记录，无需手动标记） ---------------- */
  function key(ch) { return lessonId + '/' + ch; }
  function isDone(ch) { return !!done[key(ch)]; }

  function paint() {
    var total = sections.length, n = 0;
    sections.forEach(function (s) {
      var ch = s.getAttribute('data-ch');
      if (isDone(ch)) n++;
      var link = document.querySelector('.toc nav a[data-ch="' + ch + '"]');
      if (link) link.classList.toggle('done', isDone(ch));
    });
    var pct = total ? Math.round(n / total * 100) : 0;
    var bar = document.getElementById('lp-bar'), txt = document.getElementById('lp-txt');
    if (bar) bar.style.width = pct + '%';
    if (txt) txt.textContent = pct === 100 ? '100% ✓' : pct + '%';
  }

  function queue(payload) {
    var q = [];
    try { q = JSON.parse(localStorage.getItem(LS_QUEUE) || '[]'); } catch (e) { }
    q.push(payload);
    localStorage.setItem(LS_QUEUE, JSON.stringify(q.slice(-200)));
  }

  function push(items) {
    if (!isLesson || !items.length) return;
    var body = { uid: uid(), items: items };
    fetch(API + '/progress', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    }).catch(function () { queue(body); });
  }

  function setDone(ch, val) {
    done[key(ch)] = val ? 1 : 0;
    if (!val) delete done[key(ch)];
    saveDone(done);
    paint();
    push([{ lesson: lessonId, chapter: ch, done: !!val }]);
  }

  var btnReset = document.getElementById('btn-reset');
  if (btnReset) btnReset.addEventListener('click', function () {
    if (!confirm('清除本课的学习进度？\n清除后重新滚动阅读会再次自动记录。')) return;
    Object.keys(done).forEach(function (k) {
      if (k.indexOf(lessonId + '/') === 0) delete done[k];
    });
    saveDone(done);
    /* 重新基线：当前位置已在线上方的章不瞬间重记，重新滚过才记录 */
    below = {};
    var line = window.innerHeight * 0.65;
    sections.forEach(function (s) {
      below[s.getAttribute('data-ch')] = s.getBoundingClientRect().bottom < line;
    });
    paint();
    fetch(API + '/progress/' + uid() + '/' + lessonId, { method: 'DELETE' }).catch(function () { });
  });

  /* 与服务端合并（换浏览器 / 清缓存后可恢复） */
  if (isLesson) {
    fetch(API + '/progress/' + uid()).then(function (r) { return r.json(); }).then(function (d) {
      (d.items || []).forEach(function (it) {
        if (it.lesson === lessonId && it.done) done[key(it.chapter)] = 1;
      });
      saveDone(done); paint();
      /* 服务器进度到位后再校正落点：本地无位置记录时按进度推导 */
      if (typeof reanchor === 'function') reanchor();
    }).catch(function () { });
  }

  /* 离线队列补传 */
  (function flush() {
    var q = [];
    try { q = JSON.parse(localStorage.getItem(LS_QUEUE) || '[]'); } catch (e) { return; }
    if (!q.length) return;
    localStorage.removeItem(LS_QUEUE);
    q.forEach(function (b) {
      fetch(API + '/progress', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b)
      }).catch(function () { queue(b); });
    });
  })();

  /* ---------------- 阅读进度条 + 滚动自动记录 + 位置记忆 ---------------- */
  if (isLesson && sections.length) {
    var readbar = document.createElement('div');
    readbar.className = 'readbar';
    readbar.innerHTML = '<i></i>';
    document.body.appendChild(readbar);
    var rbi = readbar.querySelector('i');
    var LS_POS = 'icl.pos.' + lessonId;
    var lastPosSave = 0;

    function curSection() {
      var y = window.scrollY + 140, cur = sections[0];
      sections.forEach(function (s) { if (s.offsetTop <= y) cur = s; });
      return cur;
    }
    function savePos() {
      var now = Date.now();
      if (now - lastPosSave < 800) return;
      lastPosSave = now;
      var s = curSection();
      if (s) { try { localStorage.setItem(LS_POS, s.getAttribute('data-ch')); } catch (e) { } }
    }
    function showToast(msg) {
      var t = document.createElement('div');
      t.className = 'aiw-toast';
      t.textContent = msg;
      document.body.appendChild(t);
      setTimeout(function () { t.classList.add('show'); }, 10);
      setTimeout(function () { t.classList.remove('show'); setTimeout(function () { t.remove(); }, 400); }, 2800);
    }
    /* 定位目标：优先本地位置记录；没有（换设备/清缓存）则按进度推导 =
       第一个未完成的章节；全部完成则停在最后一章。 */
    function targetIdx() {
      var rec = null;
      try { rec = localStorage.getItem(LS_POS); } catch (e) { }
      if (rec) {
        for (var i = 0; i < sections.length; i++) {
          if (sections[i].getAttribute('data-ch') === rec) {
            if (i > 0) return i;
            break;                                  // 记在第一章：按进度重新推导
          }
        }
      }
      for (var j = 0; j < sections.length; j++) {
        if (!isDone(sections[j].getAttribute('data-ch'))) return j;   // 第一个未学
      }
      return sections.length - 1;                   // 全学完：停最后一章
    }

    var anchored = false;
    function anchorTo(idx, notify) {
      if (idx <= 0 || !sections[idx]) return false;
      var y = Math.max(0, sections[idx].offsetTop - 80);
      if (Math.abs(window.scrollY - y) < 160 && anchored) return false;
      window.scrollTo(0, y);
      anchored = true;
      if (notify) {
        var no = (idx + 1 < 10 ? '0' : '') + (idx + 1);
        var h2 = sections[idx].querySelector('h2');
        var pct = Math.round(sections.filter(function (s) {
          return isDone(s.getAttribute('data-ch'));
        }).length / sections.length * 100);
        showToast('↩ 已定位到学习位置：' + no + ' · ' + (h2 ? h2.textContent : '') +
          '（本课进度 ' + pct + '%）');
      }
      return true;
    }

    function restorePos() {
      anchorTo(targetIdx(), true);
    }

    /* 服务器进度回填后调用：若之前按空进度落在第 1 章，则按真实进度重新定位 */
    reanchor = function () {
      if (!anchored) { anchorTo(targetIdx(), true); return; }
      var cur = curSection();
      var curIdx = sections.indexOf(cur);
      var ti = targetIdx();
      if (curIdx <= 0 && ti > 0) anchorTo(ti, true);
    };
    /* 图片加载后布局会变化，load 后再校准一次（保持同一目标章节，不弹提示） */
    window.addEventListener('load', function () {
      if (!anchored) return;
      var ti = targetIdx();
      if (ti <= 0) return;
      window.scrollTo(0, Math.max(0, sections[ti].offsetTop - 80));
    });

    function autoTrack() {
      /* 顶部阅读进度条 */
      var y = window.scrollY;
      var dy = y - lastY;
      lastY = y;
      var h = document.documentElement.scrollHeight - window.innerHeight;
      rbi.style.width = (h > 0 ? Math.min(100, Math.round(y / h * 100)) : 0) + '%';
      savePos();
      /* 跨越检测：章节底边向下越过视口 65% 线的那一刻记为已学。
         只在向下滚动时触发 —— 清除进度后停在中部不会瞬间全部重记，
         重新滚过才会再次记录。 */
      var line = window.innerHeight * 0.65;
      var items = [];
      sections.forEach(function (s) {
        var ch = s.getAttribute('data-ch');
        var isBelow = s.getBoundingClientRect().bottom < line;
        var was = below[ch];
        below[ch] = isBelow;
        if (dy > 0 && isBelow && !was && !isDone(ch)) {
          done[key(ch)] = 1;
          items.push({ lesson: lessonId, chapter: ch, done: true });
        }
      });
      if (items.length) { saveDone(done); paint(); push(items); }
    }
    var lastY = window.scrollY || 0;
    window.addEventListener('scroll', autoTrack, { passive: true });
    window.addEventListener('resize', autoTrack, { passive: true });
    autoTrack();
    restorePos();
  }

  /* ---------------- 目录 + 滚动高亮 ---------------- */
  var nav = document.getElementById('toc-nav');
  if (nav && sections.length) {
    var html = sections.map(function (s, i) {
      var ch = s.getAttribute('data-ch');
      return '<a href="#' + ch + '" data-ch="' + ch + '"><span class="n">' + (i + 1 < 10 ? '0' : '') + (i + 1) +
        '</span>' + s.querySelector('h2').textContent + '</a>';
    }).join('');
    nav.innerHTML = html;
    var cnt = document.getElementById('toc-count');
    if (cnt) cnt.textContent = sections.length + ' 章';
  }

  var links = [].slice.call(document.querySelectorAll('.toc nav a'));
  function spy() {
    var y = window.scrollY + 120, cur = sections[0];
    sections.forEach(function (s) { if (s.offsetTop <= y) cur = s; });
    links.forEach(function (a) { a.classList.toggle('on', cur && a.getAttribute('data-ch') === cur.getAttribute('data-ch')); });
  }
  if (sections.length) { window.addEventListener('scroll', spy, { passive: true }); spy(); }

  /* ---------------- 首页目录：课程完成标识 ---------------- */
  if (!isLesson && document.querySelector('.lrow')) {
    (function () {
      function paintCatalog(cat) {
        var perStage = {};
        (cat.lessons || []).forEach(function (L) {
          var total = (L.chapters || []).length, n = 0;
          (L.chapters || []).forEach(function (c) { if (done[L.id + '/' + c.id]) n++; });
          var row = document.querySelector('.lrow[href="/lesson/' + L.id + '/"]');
          if (!row) return;
          var full = total > 0 && n === total;
          row.classList.toggle('done', full);
          row.classList.toggle('partial', !full && n > 0);
          var lno = row.querySelector('.lno');
          if (lno) {
            lno.textContent = full ? '✓' : lno.textContent;
          }
          if (full && !row.querySelector('.ldone')) {
            var lh = row.querySelector('.lh');
            if (lh) lh.insertAdjacentHTML('beforebegin', '<span class="ldone">✓ 已完成</span>');
          }
          if (!full && n > 0 && !row.querySelector('.lpart')) {
            var lh2 = row.querySelector('.lh');
            if (lh2) lh2.insertAdjacentHTML('beforebegin', '<span class="lpart">' + n + '/' + total + '</span>');
          }
          var stage = row.closest('.stage');
          if (stage) {
            var agg = perStage[stage.id] || (perStage[stage.id] = [0, 0, stage]);
            agg[0] += n; agg[1] += total;
          }
        });
        Object.keys(perStage).forEach(function (sid) {
          var dn = perStage[sid][0], tt = perStage[sid][1], stage = perStage[sid][2];
          if (!tt) return;
          var pct = Math.round(dn / tt * 100);
          var r = stage.querySelector('.stage-r');
          if (!r) return;
          var el = stage.querySelector('.stage-prog');
          if (!el) {
            el = document.createElement('div');
            el.className = 'stage-prog';
            r.insertBefore(el, r.querySelector('.lrows'));
          }
          el.innerHTML = '<div class="sp-bar"><i style="width:' + pct + '%"></i></div>' +
            '<span>' + dn + '/' + tt + ' 章已完成' + (pct === 100 ? ' 🎉' : '') + '</span>';
        });
      }

      function startCatalog() {
        fetch('/data/catalog.json').then(function (r) { return r.json(); }).then(paintCatalog).catch(function () { });
      }
      /* 与服务器进度合并后绘制（换设备也能看到完成标识） */
      fetch(API + '/progress/' + uid()).then(function (r) { return r.json(); }).then(function (d) {
        (d.items || []).forEach(function (it) { if (it.done) done[it.lesson + '/' + it.chapter] = 1; });
        saveDone(done);
        startCatalog();
      }).catch(startCatalog);
    })();
  }

  /* ---------------- 术语卡 ---------------- */
  document.querySelectorAll('.term').forEach(function (t) {
    function toggle() { t.classList.toggle('open'); }
    t.addEventListener('click', toggle);
    t.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(); } });
  });

  /* ---------------- 自测答案 ---------------- */
  document.querySelectorAll('.q-item').forEach(function (q, i) {
    var btn = q.querySelector('.q-show');
    if (btn) btn.addEventListener('click', function () { q.classList.add('open'); });
    var no = q.querySelector('.q-no');
    if (no) no.textContent = (i + 1 < 10 ? '0' : '') + (i + 1);
  });

  /* ---------------- 复制代码 ---------------- */
  document.querySelectorAll('.code').forEach(function (box) {
    var btn = box.querySelector('.copy');
    var code = box.querySelector('code');
    if (!btn || !code) return;
    btn.addEventListener('click', function () {
      var text = code.innerText.replace(/\n{3,}/g, '\n\n');
      var ok = function () { btn.textContent = '已复制'; setTimeout(function () { btn.textContent = '复制'; }, 1400); };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(ok).catch(function () { fallback(text, ok); });
      else fallback(text, ok);
    });
  });
  function fallback(text, cb) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); cb(); } catch (e) { }
    document.body.removeChild(ta);
  }


  /* ---------------- 我的笔记 ---------------- */
  (function notes() {
    var box = document.getElementById('note-box');
    var save = document.getElementById('note-save');
    var msg = document.getElementById('note-msg');
    var state = document.getElementById('note-state');
    if (!box || !save || !isLesson) return;
    var LS_NOTE = 'icl.note.' + lessonId;
    var local = localStorage.getItem(LS_NOTE) || '';

    function saved(text, cls, note) {
      msg.textContent = text;
      msg.className = cls || '';
      if (note) state.textContent = note;
    }

    fetch(API + '/notes/' + uid() + '/' + lessonId).then(function (r) { return r.json(); }).then(function (d) {
      if (d && d.body) {
        box.value = d.body;
        localStorage.setItem(LS_NOTE, d.body);
        if (d.ts) saved('', '', '已从服务器恢复上次保存的内容');
      } else if (local) {
        box.value = local;
      }
    }).catch(function () {
      if (local) { box.value = local; saved('离线：显示本机缓存', 'err'); }
    });

    save.addEventListener('click', function () {
      var body = box.value;
      localStorage.setItem(LS_NOTE, body);
      saved('保存中…');
      fetch(API + '/notes', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uid: uid(), lesson: lessonId, body: body })
      }).then(function (r) {
        if (!r.ok) throw new Error('bad');
        return r.json();
      }).then(function () {
        saved('已保存 · ' + new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
      }).catch(function () {
        saved('服务器没连上，已存在本机', 'err');
      });
    });

    box.addEventListener('input', function () {
      localStorage.setItem(LS_NOTE, box.value);
    });
  })();

  paint();
})();

/* ---------- 配图放大（灯箱） ---------- */
(function () {
  if (typeof document === 'undefined') return;
  function boot() {
    var links = document.querySelectorAll('.fig-img .fig-a');
    if (!links.length) return;
    var lb = document.createElement('div');
    lb.id = 'lb';
    lb.innerHTML = '<span class="lb-x" role="button" aria-label="关闭">×</span><img alt=""><div class="lb-t"></div>';
    document.body.appendChild(lb);
    var img = lb.querySelector('img'), tip = lb.querySelector('.lb-t');
    function close() { lb.classList.remove('on'); document.body.style.overflow = ''; }
    lb.addEventListener('click', function (e) { if (e.target.tagName !== 'IMG') close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
    for (var i = 0; i < links.length; i++) {
      links[i].addEventListener('click', function (e) {
        e.preventDefault();
        var a = this, cap = a.parentNode.querySelector('figcaption');
        img.src = a.getAttribute('href');
        tip.textContent = cap ? cap.textContent : '';
        lb.classList.add('on');
        document.body.style.overflow = 'hidden';
      });
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();

/* ---------- 学习导航：阅读进度条 / 上一课·下一课 / 首页续学 ---------- */
(function () {
  if (typeof document === 'undefined') return;
  var body = document.body;
  var page = body.getAttribute('data-page') || '';

  /* 1) 课程页：顶部阅读进度条（万字长课读到哪，一眼可见） */
  if (page === 'lesson') {
    var bar = document.createElement('div');
    bar.id = 'rbar';
    document.body.appendChild(bar);
    var paint = function () {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 0 ? Math.min(100, Math.round(window.scrollY / h * 100)) : 0) + '%';
    };
    window.addEventListener('scroll', paint, { passive: true });
    window.addEventListener('resize', paint);
    paint();
  }

  /* 2) 与 3) 都依赖课程目录 */
  var LS_DONE = 'icl.done';
  function loadJSON(k, def) {
    try { return JSON.parse(localStorage.getItem(k) || def); } catch (e) { return JSON.parse(def); }
  }
  fetch('/data/catalog.json', { credentials: 'same-origin' }).then(function (r) {
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }).then(function (cat) {
    var lessons = (cat.lessons || []).slice().sort(function (a, b) { return a.no - b.no; });

    /* 2) 课程页：上一课 / 下一课 */
    if (page === 'lesson') {
      var id = body.getAttribute('data-lesson') || '';
      var i = -1;
      for (var k = 0; k < lessons.length; k++) if (lessons[k].id === id) { i = k; break; }
      if (i >= 0) {
        var main = document.querySelector('.main');
        if (main) {
          var prev = lessons[i - 1], next = lessons[i + 1];
          var nav = document.createElement('div');
          nav.className = 'pnnav';
          nav.innerHTML =
            '<a class="pn' + (prev ? '' : ' empty') + '" href="' + (prev ? '/lesson/' + prev.id + '/' : '#') + '">' +
            '<span>← 上一课</span><b>' + (prev ? '第 ' + prev.no + ' 课 · ' + prev.title : '已经是第一课') + '</b></a>' +
            '<a class="pn next' + (next ? '' : ' empty') + '" href="' + (next ? '/lesson/' + next.id + '/' : '/progress/') + '">' +
            '<span>' + (next ? '下一课 →' : '全部学完 →') + '</span><b>' +
            (next ? '第 ' + next.no + ' 课 · ' + next.title : '去进度看板回顾') + '</b></a>';
          main.appendChild(nav);
        }
      }
    }

    /* 3) 首页：续学卡（老学员接着学，新学员直接开始） */
    if (page === 'home') {
      var done = loadJSON(LS_DONE, '{}');
      var nDone = 0, nAll = 0, target = null;
      lessons.forEach(function (L) {
        (L.chapters || []).forEach(function (c) {
          nAll++;
          if (done[L.id + '/' + c.id]) nDone++;
        });
      });
      for (var j = 0; j < lessons.length && !target; j++) {
        var chs = lessons[j].chapters || [];
        for (var c2 = 0; c2 < chs.length; c2++) {
          if (!done[lessons[j].id + '/' + chs[c2].id]) { target = { L: lessons[j], c: chs[c2] }; break; }
        }
      }
      var anchor = document.querySelector('.stages');
      if (anchor) {
        var card = document.createElement('div');
        card.className = 'resumecard';
        if (nDone === 0) {
          card.innerHTML = '<span class="rc-t">第一次来？</span><b>从第 1 课开始，按顺序学，每课都有实战和自测</b>' +
            '<a class="pri" href="/lesson/' + lessons[0].id + '/">开始学习 →</a>' +
            '<a class="ghost" href="/lesson/00-02-howto/">先看使用说明</a>';
        } else if (target) {
          card.innerHTML = '<span class="rc-t">继续学习</span><b>上次学到：第 ' + target.L.no + ' 课 · ' +
            esc2(target.L.title) + '</b><span class="rc-p">' + nDone + '/' + nAll + ' 章已完成</span>' +
            '<a class="pri" href="/lesson/' + target.L.id + '/#' + target.c.id + '">接着学 →</a>';
        } else {
          card.innerHTML = '<span class="rc-t">全部学完 🎉</span><b>' + nAll + ' 章全部完成，去做各阶段验收卷</b>' +
            '<a class="pri" href="/exam/">去验收</a><a class="ghost" href="/progress/">看进度</a>';
        }
        anchor.parentNode.insertBefore(card, anchor);
      }
    }
  }).catch(function () { /* 目录加载失败时静默：页面其余功能不受影响 */ });

  function esc2(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
})();
