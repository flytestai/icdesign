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
    /* 刷题进度：本地记录已作答过的题目（去重），并上报服务器用于排行榜 */
    var LS_ANSWERED = 'icl.answered', LS_CORRECT = 'icl.correct';
    var answered = load(LS_ANSWERED, '[]'), correctList = load(LS_CORRECT, '[]');
    function pushQuizStats() {
      fetch('/api/quiz-stats', {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answered: answered.length, correct: correctList.length }),
      }).catch(function () {});
    }
    function markAnswered(id, ok) {
      var ch = false;
      if (answered.indexOf(id) < 0) { answered.push(id); ch = true; }
      if (ok) {
        if (correctList.indexOf(id) < 0) { correctList.push(id); ch = true; }
        wrong = wrong.filter(function (x) { return x !== id; });
        save(LS_WRONG, wrong);
      } else if (correctList.indexOf(id) >= 0) {
        correctList = correctList.filter(function (x) { return x !== id; }); ch = true;
      }
      if (ch) { save(LS_ANSWERED, answered); save(LS_CORRECT, correctList); pushQuizStats(); }
    }

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
          markAnswered(id, true);
        });
        if (no) no.addEventListener('click', function () {
          if (wrong.indexOf(id) < 0) wrong.push(id);
          save(LS_WRONG, wrong); paintWrongCount();
          no.textContent = '✓ 已记下'; no.classList.add('no');
          markAnswered(id, false);
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
          exBadge(s.no) +
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

  /* ==================================================== 阶段验收 */
  var LS_EXAM = 'icl.exam.';
  function examKey(s) { return LS_EXAM + s; }
  function examResult(s) { return load(examKey(s), 'null'); }
  function exBadge(s) {
    var r = examResult(s);
    if (!r) return '<a class="pex" href="/exam/#stage-' + s + '">未验收 · 去做验收卷</a>';
    return '<a class="pex pass" href="/exam/#stage-' + s + '">已验收 ' + r.score + ' 分</a>';
  }

  function initExam() {
    var list = q('#x-stages'), panel = q('#x-panel');
    var PASS = 0.8;
    var cat = null, quiz = null, run = null;   // run = {stage, items, right, graded}

    function stageMeta() {
      var m = {};
      (cat.lessons || []).forEach(function (L) {
        m[L.stage] = m[L.stage] || { stage: L.stage, name: '', lessons: 0, qs: 0 };
        m[L.stage].lessons++;
      });
      (cat.stages || []).forEach(function (s) {
        if (m[s.no]) m[s.no].name = s.name;
      });
      (quiz || []).forEach(function (x) { if (m[x.stage]) m[x.stage].qs++; });
      return (cat.stages || []).map(function (s) { return m[s.no]; }).filter(Boolean);
    }

    function cardList(items) {
      return items.map(function (item, i) {
        return '<div class="qcard2" data-i="' + i + '">' +
          '<div class="qmeta"><span>' + esc(item.no) + '</span>' +
          '<a href="/lesson/' + esc(item.lesson) + '/#' + esc(item.ch) + '">' + esc(item.lessonTitle) + '</a>' +
          '<span>' + esc(item.stageName) + '</span></div>' +
          '<div class="qq">' + (i + 1) + '. ' + esc(item.q) + '</div>' +
          '<div class="qacts"><button class="qshow" type="button">看答案</button>' +
          '<button class="qok" type="button">我答对了</button><button class="qno" type="button">我答错了</button></div>' +
          '<div class="qa">' + esc(item.a) + '</div></div>';
      }).join('');
    }

    function bindGrades(root, onAll) {
      var graded = 0;
      qa('.qcard2', root).forEach(function (c) {
        var show = q('.qshow', c), ok = q('.qok', c), no = q('.qno', c);
        function pick(cls) {
          return function () {
            if (c.getAttribute('data-done')) return;
            c.setAttribute('data-done', '1');
            c.classList.add('open');
            c.classList.add(cls);
            ok.disabled = no.disabled = true;
            if (cls === 'g-ok') run.right++;
            graded++;
            if (graded === run.items.length && onAll) onAll();
          };
        }
        show.addEventListener('click', function () { c.classList.add('open'); });
        ok.addEventListener('click', pick('g-ok'));
        no.addEventListener('click', pick('g-no'));
      });
    }

    function finish() {
      var t = run.items.length, n = run.right, score = Math.round(n / t * 100);
      var pass = score >= 80;
      if (pass) {
        var prev = examResult(run.stage);
        if (!prev || score > prev.score) {
          save(examKey(run.stage), { score: score, right: n, total: t, date: Date.now() });
        }
      }
      /* 上报验收成绩到排行榜（通过阶段数 / 最高分） */
      (function () {
        var passed = 0, best = 0;
        for (var s = 1; s <= 9; s++) {
          var r = examResult(s);
          if (r && r.score >= 80) { passed++; if (r.score > best) best = r.score; }
        }
        if (pass && score > best) best = score;
        var a = load('icl.answered', '[]'), c = load('icl.correct', '[]');
        fetch('/api/quiz-stats', {
          method: 'POST', credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            answered: a.length, correct: c.length,
            exam_passed: pass ? Math.max(passed, 1) : passed, best_exam: best,
          }),
        }).catch(function () {});
      })();
      panel.innerHTML =
        '<div class="xres' + (pass ? ' pass' : ' fail') + '">' +
        '<b>' + score + ' 分 · ' + (pass ? '过关！' : '还差一点') + '</b>' +
        '<span>答对 ' + n + ' / ' + t + '，过关线 80 分' +
        (pass ? '' : '。标红的题对应课程都列在下面，回去把那一节再看一遍，明天再验一次。') + '</span></div>' +
        '<div class="xacts"><button class="pri" id="x-again" type="button">再抽一套</button>' +
        '<button class="ghost" id="x-back" type="button">返回阶段列表</button></div>' +
        '<div class="xnote">本次抽到的题：答错的课建议优先复习。</div>' +
        cardList(run.items);
      bindGrades(panel, null);   // 已评过的题不会再计分，只保留展开
      q('#x-back').addEventListener('click', back);
      q('#x-again').addEventListener('click', function () { start(run.stage); });
      window.scrollTo(0, 0);
    }

    function start(stage) {
      var items = shuffle((quiz || []).filter(function (x) { return x.stage === stage; }));
      items = items.slice(0, Math.min(20, Math.max(items.length, 8)));
      if (!items.length) { panel.innerHTML = '<p class="qempty">这个阶段还没有题目。</p>'; return; }
      run = { stage: stage, items: items, right: 0, graded: 0 };
      list.hidden = true;
      panel.hidden = false;
      var meta = stageMeta().filter(function (m) { return m.stage === stage; })[0];
      panel.innerHTML = '<div class="xhead"><h2>' + esc(meta ? meta.name : '') + ' · 验收卷</h2>' +
        '<span>' + items.length + ' 题 · 自评计分 · 80 分过关</span>' +
        '<button class="ghost" id="x-quit" type="button">放弃</button></div>' +
        cardList(items);
      bindGrades(panel, finish);
      q('#x-quit').addEventListener('click', back);
      window.scrollTo(0, 0);
    }

    function back() {
      panel.hidden = true; panel.innerHTML = '';
      list.hidden = false;
      drawList();
    }

    function drawList() {
      var ms = stageMeta();
      list.innerHTML = ms.map(function (m) {
        var r = examResult(m.stage);
        var n = Math.min(20, Math.max(m.qs, 8));
        return '<div class="xcard" id="stage-' + m.stage + '">' +
          '<div class="xcl"><h3>' + esc(m.name) + '</h3>' +
          '<span>' + m.lessons + ' 门课 · ' + m.qs + ' 题可选</span></div>' +
          '<div class="xcr">' + (r
            ? '<span class="xtag pass">已验收 ' + r.score + ' 分</span>'
            : '<span class="xtag">未验收</span>') +
          '<button class="pri" data-stage="' + m.stage + '" type="button">开始验收（' + n + ' 题）</button></div></div>';
      }).join('');
      qa('button[data-stage]', list).forEach(function (b) {
        b.addEventListener('click', function () { start(Number(b.getAttribute('data-stage'))); });
      });
    }

    Promise.all([getJSON('/data/catalog.json'), getJSON('/data/quiz.json')]).then(function (r) {
      cat = r[0]; quiz = r[1];
      drawList();
      var m = location.hash.match(/^#stage-(\d+)/);
      if (m) {
        var st = Number(m[1]);
        if ((quiz || []).some(function (x) { return x.stage === st; })) start(st);
      }
    }).catch(function () {
      list.innerHTML = '<p class="qempty">数据没加载出来，刷新试试。</p>';
    });
  }

  /* ---------------- 排行榜 ---------------- */
  function initLeaderboard() {
    var box = q('#lb-rows');
    if (!box) return;
    function fmtTime(sec) {
      if (!sec || sec < 60) return (sec || 0) + ' 秒';
      var m = Math.round(sec / 60);
      if (m < 60) return m + ' 分钟';
      return Math.floor(m / 60) + ' 小时 ' + (m % 60) + ' 分';
    }
    fetch('/api/leaderboard', { credentials: 'same-origin' })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) {
          box.innerHTML = '<p class="qempty">' + (res.j.detail === 'not logged in'
            ? '登录后查看排行榜' : '数据加载失败') + '</p>';
          return;
        }
        var rows = res.j.rows || [];
        if (!rows.length) { box.innerHTML = '<p class="qempty">还没有数据</p>'; return; }
        /* 认领历史设备的学习记录 */
    function loadDevices() {
      var wrap = q('#lb-claim'), list = q('#lc-list'), nEl = q('#lc-n');
      if (!wrap || !list) return;
      fetch('/api/my-devices', { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          var devs = (j.devices || []).filter(function (d) { return !d.linked; });
          if (!devs.length) { wrap.hidden = true; return; }
          wrap.hidden = false;
          if (nEl) nEl.textContent = '（' + devs.length + ' 个）';
          list.innerHTML = devs.map(function (d) {
            var dt = new Date(d.last * 1000);
            var p = function (n) { return (n < 10 ? '0' : '') + n; };
            return '<div class="lc-item"><span class="lc-n2"><b>' + d.chapters +
              '</b> 章已完成</span><span class="lc-d">最近 ' + (dt.getMonth() + 1) + '-' +
              p(dt.getDate()) + ' ' + p(dt.getHours()) + ':' + p(dt.getMinutes()) + '</span>' +
              '<button class="lc-btn" type="button" data-token="' + esc(d.claim_token || '') + '">认领到我的账号</button></div>';
          }).join('');
          list.querySelectorAll('.lc-btn').forEach(function (b) {
            b.addEventListener('click', function () {
              var token = b.getAttribute('data-token');
              b.disabled = true; b.textContent = '认领中…';
              fetch('/api/claim-device', {
                method: 'POST', credentials: 'same-origin',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token }),
              }).then(function (r) { return r.json().then(function (j2) { return { ok: r.ok, j: j2 }; }); })
                .then(function (res) {
                  if (res.ok) { b.textContent = '✓ 已认领 ' + res.j.chapters + ' 章'; setTimeout(loadDevices, 900); }
                  else { b.disabled = false; b.textContent = res.j.detail || '认领失败'; }
                })
                .catch(function () { b.disabled = false; b.textContent = '认领失败，重试'; });
            });
          });
        })
        .catch(function () { if (wrap) wrap.hidden = true; });
    }

    var medal = ['🥇', '🥈', '🥉'];
        box.innerHTML = rows.map(function (r) {
          var rk = r.rank <= 3 ? medal[r.rank - 1] : r.rank;
          var pct = Math.min(100, r.progress_pct || 0);
          var qpct = Math.min(100, r.quiz_pct || 0);
          return '<div class="lb-row' + (r.is_me ? ' me' : '') + '">' +
            '<span class="c-rk">' + rk + '</span>' +
            '<span class="c-nm">' + esc(r.name) + (r.is_me ? '<b class="lb-you">我</b>' : '') +
            (r.role === 'admin' ? '<i class="lb-adm">管理员</i>' : '') + '</span>' +
            '<span class="c-pg"><b>' + r.done + '</b>/' + r.total +
            '<i class="lb-mini"><s style="width:' + pct + '%"></s></i></span>' +
            '<span class="c-qz"><b>' + r.answered + '</b>/' + r.total_quizzes +
            (r.exam_passed ? '<em class="lb-ex">验收 ' + r.exam_passed + ' 阶段</em>' : '') +
            '<i class="lb-mini q"><s style="width:' + qpct + '%"></s></i></span>' +
            '<span class="c-tm">' + fmtTime(r.seconds) + '</span>' +
            '<span class="c-sc">' + r.score + '</span>' +
            '</div>';
        }).join('');
        var mine = rows.filter(function (r) { return r.is_me; })[0];
        var me = q('#lb-me');
        if (mine && me) {
          me.hidden = false;
          me.innerHTML = '我的排名：第 <b>' + mine.rank + '</b> / ' + rows.length +
            ' 名 · 综合分 <b>' + mine.score + '</b> · 完成 ' + mine.done + ' 章 · 刷题 ' +
            mine.answered + ' 道（正确 ' + mine.correct + '）· 学习 ' + fmtTime(mine.seconds);
        }
      })
      .catch(function () { box.innerHTML = '<p class="qempty">数据没加载出来，刷新试试。</p>'; });
    loadDevices();
  }

  if (page === 'quiz') initQuiz();
  if (page === 'exam') initExam();
  if (page === 'glossary') initGloss();
  if (page === 'search') initSearch();
  if (page === 'progress') initProgress();
  if (page === 'leaderboard') initLeaderboard();
})();
