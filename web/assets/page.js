/* IC 后端学院 · 子页面脚本：题库 / 术语表 / 搜索 / 进度看板 */
(function () {
  'use strict';
  var API = '/api';
  var page = document.body.getAttribute('data-page') || '';
  var LS_UID = 'icl.uid', LS_DONE = 'icl.done', LS_WRONG = 'icl.wrong';

  function q(s, r) { return (r || document).querySelector(s); }
  function qa(s, r) { return [].slice.call((r || document).querySelectorAll(s)); }
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function uid() {
    var u = localStorage.getItem(LS_UID);
    if (!u) {
      u = 'u' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
      localStorage.setItem(LS_UID, u);
    }
    return u;
  }
  function load(k, def) {
    try { return JSON.parse(localStorage.getItem(k) || def); } catch (e) { return JSON.parse(def); }
  }
  function save(k, v) { localStorage.setItem(k, JSON.stringify(v)); }
  function getJSON(url) {
    return fetch(url, { credentials: 'same-origin' }).then(function (r) {
      if (!r.ok) throw new Error(url + ' ' + r.status);
      return r.json();
    });
  }
  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  /* ==================================================== 题库 */
  function initQuiz() {
    var all = [], wrong = load(LS_WRONG, '[]'), stage = '', mode = 'draw', round = [];
    var panel = q('#quiz-panel'), sel = q('#q-stage'), cnt = q('#wrong-n');

    function paintWrongCount() { if (cnt) cnt.textContent = wrong.length; }

    function pool() {
      return stage ? all.filter(function (x) { return String(x.stage) === stage; }) : all.slice();
    }

    function card(item, i) {
      var open = mode === 'wrong';
      return '<div class="qcard2' + (open ? ' open' : '') + '" data-id="' + esc(item.id) + '">' +
        '<div class="qmeta"><span>' + esc(item.no) + '</span>' +
        '<a href="/lesson/' + esc(item.lesson) + '/#' + esc(item.ch) + '">' + esc(item.lessonTitle) + '</a>' +
        '<span>' + esc(item.stageName) + '</span></div>' +
        '<div class="qq">' + (i + 1) + '. ' + esc(item.q) + '</div>' +
        '<div class="qacts"><button class="qshow" type="button">看答案</button>' +
        '<button class="qok" type="button">我会了</button><button class="qno" type="button">不会，记下来</button></div>' +
        '<div class="qa">' + esc(item.a) + '</div></div>';
    }

    function render(list, note) {
      if (!list.length) {
        panel.innerHTML = '<p class="qempty">' + (note || '这一组还没有题。') + '</p>';
        return;
      }
      var sum = '<div class="qsum"><span>本轮 <b>' + list.length + '</b> 题</span>' +
        '<span>点"看答案"再自评，答错的进错题本</span></div>';
      panel.innerHTML = sum + list.map(card).join('');
      bind();
    }

    function bind() {
      qa('.qcard2', panel).forEach(function (c) {
        var id = c.getAttribute('data-id');
        var show = q('.qshow', c), ok = q('.qok', c), no = q('.qno', c);
        if (show) show.addEventListener('click', function () {
          c.classList.add('open');
          show.style.display = 'none';
        });
        if (ok) ok.addEventListener('click', function () {
          wrong = wrong.filter(function (x) { return x !== id; });
          save(LS_WRONG, wrong); paintWrongCount();
          ok.textContent = '✓ 会了'; ok.classList.add('ok');
        });
        if (no) no.addEventListener('click', function () {
          if (wrong.indexOf(id) < 0) wrong.push(id);
          save(LS_WRONG, wrong); paintWrongCount();
          no.textContent = '✓ 已记下'; no.classList.add('no');
        });
      });
    }

    function startRound() {
      var p = pool();
      round = shuffle(p.slice()).slice(0, Math.min(10, p.length));
      mode = 'draw';
      setTab('draw');
      render(round, '没有题目，检查题库是否生成。');
    }

    function setTab(name) {
      qa('.tab').forEach(function (t) { t.classList.toggle('on', t.getAttribute('data-tab') === name); });
    }

    qa('.tab').forEach(function (t) {
      t.addEventListener('click', function () {
        mode = t.getAttribute('data-tab');
        setTab(mode);
        if (mode === 'draw') {
          render(round, '点右上角"开始 10 题"随机抽题。');
        } else if (mode === 'wrong') {
          var list = all.filter(function (x) { return wrong.indexOf(x.id) >= 0; });
          render(list, '错题本是空的。先去随机抽题，答错的会自动进来。');
        } else {
          var list2 = pool();
          render(list2.slice(0, 60), '没有题目。');
        }
      });
    });

    var btn = q('#q-start');
    if (btn) btn.addEventListener('click', startRound);

    if (sel) sel.addEventListener('change', function () {
      stage = sel.value;
      if (mode === 'draw') startRound();
      else if (mode === 'wrong') {
        var list = all.filter(function (x) { return wrong.indexOf(x.id) >= 0 && (!stage || String(x.stage) === stage); });
        render(list, '这一阶段没有错题。');
      } else {
        render(pool().slice(0, 60));
      }
    });

    getJSON('/data/quiz.json').then(function (data) {
      all = data || [];
      var stages = [];
      all.forEach(function (x) { if (stages.indexOf(x.stage) < 0) stages.push(x.stage); });
      stages.sort();
      if (sel) stages.forEach(function (s) {
        var name = (all.filter(function (x) { return x.stage === s; })[0] || {}).stageName || ('阶段 ' + s);
        var o = document.createElement('option');
        o.value = String(s); o.textContent = name;
        sel.appendChild(o);
      });
      paintWrongCount();
      render([], '共 ' + all.length + ' 道题。点右上角"开始 10 题"，随机抽 10 道；答完点"看答案"自评，答错的会自动进错题本。');
    }).catch(function () {
      panel.innerHTML = '<p class="qempty">题库没加载出来，刷新一次试试。</p>';
    });
  }

  /* ==================================================== 术语表 */
  function initGloss() {
    var all = [], kw = '', stage = '';
    var list = q('#g-list'), input = q('#g-q'), sel = q('#g-stage'), n = q('#g-n');

    function draw() {
      var k = kw.toLowerCase();
      var hits = all.filter(function (x) {
        if (stage && String(x.stage) !== stage) return false;
        if (!k) return true;
        return (x.en + ' ' + x.zh + ' ' + x.def).toLowerCase().indexOf(k) >= 0;
      });
      if (n) n.textContent = hits.length + ' / ' + all.length + ' 条';
      if (!hits.length) {
        list.innerHTML = '<div class="gempty">没有匹配的术语，换个词试试（可以搜中文）。</div>';
        return;
      }
      list.innerHTML = hits.map(function (x) {
        return '<div class="gitem"><div><span class="ge">' + esc(x.en) + '</span>' +
          (x.zh && x.zh !== x.en ? '<span class="gz">' + esc(x.zh) + '</span>' : '') + '</div>' +
          '<div class="gd">' + esc(x.def) + '</div>' +
          '<div class="gs">出自 <a href="/lesson/' + esc(x.lesson) + '/#' + esc(x.ch) + '">' +
          esc(x.no) + ' ' + esc(x.lessonTitle) + '</a> · ' + esc(x.chTitle) + '</div></div>';
      }).join('');
    }

    if (input) input.addEventListener('input', function () { kw = input.value.trim(); draw(); });
    if (sel) sel.addEventListener('change', function () { stage = sel.value; draw(); });

    getJSON('/data/glossary.json').then(function (data) {
      all = (data || []).slice().sort(function (a, b) { return a.en.localeCompare(b.en); });
      var stages = [];
      all.forEach(function (x) { if (stages.indexOf(x.stage) < 0) stages.push(x.stage); });
      stages.sort();
      if (sel) stages.forEach(function (s) {
        var name = (all.filter(function (x) { return x.stage === s; })[0] || {}).stageName || ('阶段 ' + s);
        var o = document.createElement('option');
        o.value = String(s); o.textContent = name;
        sel.appendChild(o);
      });
      draw();
    }).catch(function () {
      list.innerHTML = '<div class="gempty">术语表没加载出来，刷新一次试试。</div>';
    });
  }

  /* ==================================================== 搜索 */
  function initSearch() {
    var index = [], input = q('#s-q'), list = q('#s-list'), n = q('#s-n'), hint = q('#s-hint');

    function snippet(text, terms) {
      var low = text.toLowerCase(), at = -1;
      for (var i = 0; i < terms.length; i++) {
        var p = low.indexOf(terms[i]);
        if (p >= 0) { at = p; break; }
      }
      if (at < 0) at = 0;
      var s = Math.max(0, at - 70);
      var out = (s > 0 ? '…' : '') + text.slice(s, s + 220) + (s + 220 < text.length ? '…' : '');
      return esc(out).replace(new RegExp('(' + terms.map(function (t) {
        return t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      }).join('|') + ')', 'gi'), '<mark>$1</mark>');
    }

    function run() {
      var raw = (input.value || '').trim();
      if (!raw) {
        list.innerHTML = '';
        hint.style.display = '';
        if (n) n.textContent = '';
        return;
      }
      hint.style.display = 'none';
      var terms = raw.toLowerCase().split(/\s+/).filter(Boolean);
      var hits = [];
      index.forEach(function (c) {
        var hay = (c.title + ' ' + c.chTitle + ' ' + c.text).toLowerCase();
        var okAll = terms.every(function (t) { return hay.indexOf(t) >= 0; });
        if (!okAll) return;
        var score = 0;
        if (c.chTitle.toLowerCase().indexOf(terms[0]) >= 0) score += 5;
        if (c.title.toLowerCase().indexOf(terms[0]) >= 0) score += 3;
        if (c.text.toLowerCase().indexOf(raw.toLowerCase()) >= 0) score += 4;
        hits.push({ c: c, score: score });
      });
      hits.sort(function (a, b) { return b.score - a.score; });
      if (n) n.textContent = hits.length + ' 个章节命中';
      if (!hits.length) {
        list.innerHTML = '<p class="qempty">没找到。试试更短的词，或换个说法（比如"拥塞"换成 "congestion"）。</p>';
        return;
      }
      list.innerHTML = hits.slice(0, 40).map(function (h) {
        var c = h.c;
        return '<div class="sitem"><div class="st"><a href="/lesson/' + esc(c.lesson) + '/#' + esc(c.ch) + '">' +
          esc(c.chTitle) + '</a></div><div class="sm">' + esc(c.no) + ' · ' + esc(c.title) + ' · ' + esc(c.stageName) +
          '</div><div class="sx">' + snippet(c.text, terms) + '</div></div>';
      }).join('');
    }

    var timer = null;
    if (input) input.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(run, 220);
    });
    if (input) input.addEventListener('keydown', function (e) { if (e.key === 'Enter') run(); });

    getJSON('/data/search.json').then(function (data) {
      index = data || [];
      var m = location.search.match(/[?&]q=([^&]+)/);
      if (m && input) { input.value = decodeURIComponent(m[1].replace(/\+/g, ' ')); run(); }
    }).catch(function () { list.innerHTML = '<p class="qempty">搜索索引没加载出来。</p>'; });
  }

  /* ==================================================== 进度看板 */
  function initProgress() {
    var done = load(LS_DONE, '{}');
    var cat = null;

    function isDone(lesson, ch) { return !!done[lesson + '/' + ch]; }

    function draw() {
      var stages = cat.stages || [];
      var lessons = cat.lessons || [];
      var total = 0, got = 0, nextLesson = null, nextCh = null;
      var byStage = {};

      lessons.forEach(function (L) {
        var s = L.stage;
        byStage[s] = byStage[s] || { lessons: [], doneCh: 0, allCh: 0 };
        var d = 0;
        L.chapters.forEach(function (c) {
          total++;
          if (isDone(L.id, c.id)) { d++; got++; byStage[s].doneCh++; }
          else if (!nextCh && !nextLesson) { nextLesson = L; nextCh = c; }
        });
        byStage[s].allCh += L.chapters.length;
        byStage[s].lessons.push({ L: L, done: d });
      });

      var pct = total ? Math.round(got / total * 100) : 0;
      q('#p-pct').textContent = pct + '%';
      q('#p-ch').textContent = got + '/' + total;
      q('#p-fill').style.width = pct + '%';
      var nx = q('#p-next');
      nx.textContent = nextLesson ? ('第 ' + nextLesson.no + ' 课') : '全部学完';
      nx.title = nextLesson ? nextLesson.title : '';
      var nxSub = q('#p-next-sub');
      if (nxSub) nxSub.textContent = nextLesson ? nextLesson.title : '可以回去复习或开始做项目';

      var html = stages.map(function (s) {
        var g = byStage[s.no];
        if (!g) return '';
        var sp = g.allCh ? Math.round(g.doneCh / g.allCh * 100) : 0;
        var rows = g.lessons.map(function (x) {
          var dl = x.L.chapters.length;
          var fin = dl && x.done === dl;
          return '<a class="prow' + (fin ? ' done' : '') + '" href="/lesson/' + esc(x.L.id) + '/">' +
            '<span class="pn">' + esc(x.L.no) + '</span><span class="pt">' + esc(x.L.title) + '</span>' +
            '<span class="pc">' + x.done + '/' + dl + '</span></a>';
        }).join('');
        return '<div class="pstage" style="--c:' + esc(s.color) + '"><div class="psh"><h3>' + esc(s.name) + '</h3>' +
          '<span class="pct">' + g.doneCh + '/' + g.allCh + ' 章 · ' + sp + '%</span></div>' +
          '<div class="pmini"><i style="width:' + sp + '%"></i></div>' +
          '<div class="plist">' + rows + '</div></div>';
      }).join('');
      q('#p-stages').innerHTML = html;

      if (nextLesson) {
        var btn = q('#p-next');
        btn.style.cursor = 'pointer';
        btn.title = '点这里继续：' + nextCh.title;
        btn.addEventListener('click', function () {
          location.href = '/lesson/' + nextLesson.id + '/#' + nextCh.id;
        });
      }
    }

    getJSON('/data/catalog.json').then(function (data) {
      cat = data;
      draw();
      // 合并服务器进度（换浏览器后可恢复）
      return getJSON(API + '/progress/' + uid()).then(function (d) {
        (d.items || []).forEach(function (it) {
          if (it.done) done[it.lesson + '/' + it.chapter] = 1;
        });
        save(LS_DONE, done);
        draw();
      }).catch(function () { });
    }).catch(function () {
      q('#p-stages').innerHTML = '<p class="qempty">课程目录没加载出来。</p>';
    });
  }

  if (page === 'quiz') initQuiz();
  if (page === 'glossary') initGloss();
  if (page === 'search') initSearch();
  if (page === 'progress') initProgress();
})();
