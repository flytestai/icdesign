/* ============================================================
   IC 后端学院 · 平台外壳
   目录 / 进度 / 搜索 / iframe 章节桥
   ============================================================ */
(function () {
  'use strict';

  var API = (location.protocol === 'file:') ? '' : '/api';
  var LS_UID = 'icl.uid', LS_PROG = 'icl.prog', LS_LAST = 'icl.last';
  var CATALOG = window.__CATALOG__ || { lessons: [] };

  /* ---------- 工具 ---------- */
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function uid() {
    var u = localStorage.getItem(LS_UID);
    if (!u) {
      u = 'u_' + Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);
      localStorage.setItem(LS_UID, u);
    }
    return u;
  }
  var UID = uid();

  /* ---------- 进度存储 ---------- */
  var Prog = {
    data: {},
    load: function () {
      try { this.data = JSON.parse(localStorage.getItem(LS_PROG) || '{}'); } catch (e) { this.data = {}; }
      return this;
    },
    save: function () {
      try { localStorage.setItem(LS_PROG, JSON.stringify(this.data)); } catch (e) {}
    },
    isDone: function (lesson, chapter) {
      return !!(this.data[lesson] && this.data[lesson][chapter]);
    },
    set: function (lesson, chapter, on) {
      if (!this.data[lesson]) this.data[lesson] = {};
      if (on) this.data[lesson][chapter] = 1; else delete this.data[lesson][chapter];
      this.save();
      Sync.push(lesson, chapter, on);
    },
    lessonDone: function (lesson) {
      var m = this.data[lesson] || {}, n = 0;
      for (var k in m) if (m[k]) n++;
      return n;
    },
    totalDone: function () {
      var n = 0;
      for (var k in this.data) n += this.lessonDone(k);
      return n;
    },
    reset: function () {
      this.data = {}; this.save();
      fetch(API + '/progress/' + UID, { method: 'DELETE' }).catch(function () {});
    },
    merge: function (serverItems) {
      var changed = false;
      (serverItems || []).forEach(function (it) {
        if (!it || !it.lesson || !it.chapter) return;
        if (!Prog.data[it.lesson]) Prog.data[it.lesson] = {};
        if (it.done && !Prog.data[it.lesson][it.chapter]) { Prog.data[it.lesson][it.chapter] = 1; changed = true; }
      });
      if (changed) this.save();
      return changed;
    }
  };

  /* ---------- 同步 ---------- */
  var Sync = {
    dot: null,
    pending: [],
    timer: null,
    mark: function (s, title) {
      if (!this.dot) return;
      this.dot.className = 'sync ' + (s || '');
      this.dot.title = title || '';
      var t = document.getElementById('sync-text');
      if (t) t.textContent = title || (s === 'ok' ? '已同步' : '同步中…');
    },
    push: function (lesson, chapter, done) {
      if (!API) return;
      this.pending.push({ lesson: lesson, chapter: chapter, done: !!done });
      this.mark('', '同步中…');
      var self = this;
      clearTimeout(this.timer);
      this.timer = setTimeout(function () { self.flush(); }, 900);
    },
    flush: function () {
      if (!API || !this.pending.length) return;
      var batch = this.pending.splice(0, this.pending.length);
      fetch(API + '/progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uid: UID, items: batch })
      }).then(function (r) { if (!r.ok) throw 0; Sync.mark('ok', '已同步到云端'); })
        .catch(function () {
          Sync.pending = batch.concat(Sync.pending);
          Sync.mark('err', '离线：进度已存在本地');
        });
    },
    pull: function () {
      if (!API) { this.mark('', '本地模式'); return Promise.resolve(); }
      var self = this;
      return fetch(API + '/progress/' + UID)
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (j && j.items) { Prog.merge(j.items); self.mark('ok', '已连接云端'); }
          return j;
        })
        .catch(function () { self.mark('err', '离线模式'); });
    }
  };

  /* ---------- 目录渲染 ---------- */
  function chaptersOf(lesson) { return (lesson && lesson.chapters) || []; }

  function renderRail(activeLesson, activeChapter) {
    var box = $('#rail-courses');
    if (!box) return;
    box.innerHTML = CATALOG.lessons.map(function (L) {
      var isActive = L.id === activeLesson;
      var isOpen = isActive || L.forceOpen;
      var total = chaptersOf(L).length;
      var done = Prog.lessonDone(L.id);
      var pctTxt = total ? done + '/' + total : (L.status === 'soon' ? '筹备中' : '');
      var chaps = chaptersOf(L).map(function (c) {
        var d = Prog.isDone(L.id, c.id);
        var on = isActive && c.id === activeChapter;
        return '<div class="chap' + (on ? ' on' : '') + (d ? ' done' : '') + (L.status === 'soon' ? ' locked' : '') +
          '" data-lesson="' + esc(L.id) + '" data-chap="' + esc(c.id) + '">' +
          '<span class="ct">' + esc(c.title) + '</span><i class="dot"></i></div>';
      }).join('');
      return '<div class="course' + (isOpen ? ' open' : '') + (isActive ? ' active' : '') + '" data-lesson="' + esc(L.id) + '">' +
        '<div class="course-head" data-lesson="' + esc(L.id) + '">' +
          '<span class="course-no">' + esc(L.no) + '</span>' +
          '<span class="course-tt"><span class="t">' + esc(L.title) + '</span>' +
            '<span class="s"><span class="chip ' + (L.status === 'soon' ? 'soon' : 'live') + '">' + (L.status === 'soon' ? '即将上线' : total + ' 章') + '</span>' +
            (pctTxt && L.status !== 'soon' ? '<span>' + pctTxt + ' 已完成</span>' : '') + '</span></span>' +
          '<svg class="chev" viewBox="0 0 16 16" fill="none"><path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>' +
        '</div>' +
        (total ? '<div class="chapters">' + chaps + '</div>' : '') +
      '</div>';
    }).join('');
  }

  function bindRail(onChapter) {
    var box = $('#rail-courses');
    if (!box) return;
    box.addEventListener('click', function (e) {
      var ch = e.target.closest('.chap');
      if (ch) {
        if (ch.classList.contains('locked')) { toast('这一课还在制作中'); return; }
        e.stopPropagation();
        onChapter(ch.dataset.lesson, ch.dataset.chap);
        return;
      }
      var head = e.target.closest('.course-head');
      if (head) {
        var card = head.parentNode;
        var id = head.dataset.lesson;
        var L = CATALOG.lessons.filter(function (x) { return x.id === id; })[0];
        if (L && L.status === 'soon') { toast('第 ' + L.no + ' 课正在制作中，敬请期待'); return; }
        if (card.classList.contains('active') && card.classList.contains('open')) {
          card.classList.remove('open');
        } else if (location.pathname.indexOf('/lesson/') === -1 || !card.classList.contains('active')) {
          location.href = '/lesson/' + id + '/';
        } else {
          card.classList.toggle('open');
        }
      }
    });
  }

  function markChapter(lesson, chapter, on) {
    Prog.set(lesson, chapter, on);
    var el = $('.chap[data-lesson="' + lesson + '"][data-chap="' + chapter + '"]');
    if (el) el.classList.toggle('done', !!on);
    updateProgressUI();
  }

  function updateProgressUI() {
    var total = 0;
    CATALOG.lessons.forEach(function (L) { if (L.status !== 'soon') total += chaptersOf(L).length; });
    var done = 0;
    CATALOG.lessons.forEach(function (L) { if (L.status !== 'soon') done += Prog.lessonDone(L.id); });
    var pct = total ? done / total : 0;

    var t = $('#prog-text'); if (t) t.textContent = done + ' / ' + total;
    var b = $('#prog-bar'); if (b) b.style.width = (pct * 100).toFixed(1) + '%';
    $$('.mini-bar i').forEach(function (i) {
      var id = i.dataset.lesson, L = CATALOG.lessons.filter(function (x) { return x.id === id; })[0];
      var n = chaptersOf(L || {}).length || 1;
      i.style.width = (Prog.lessonDone(id) / n * 100).toFixed(0) + '%';
    });
    var c = $('#ring-c');
    if (c) {
      var r = +c.getAttribute('r'), len = 2 * Math.PI * r;
      c.setAttribute('stroke-dasharray', len);
      c.setAttribute('stroke-dashoffset', len * (1 - pct));
    }
    var rt = $('#ring-text'); if (rt) rt.textContent = Math.round(pct * 100) + '%';
    // 课程卡进度
    $$('.lcard[data-lesson]').forEach(function (card) {
      var id = card.dataset.lesson, L = CATALOG.lessons.filter(function (x) { return x.id === id; })[0];
      if (!L || L.status === 'soon') return;
      var n = chaptersOf(L).length || 1, d = Prog.lessonDone(id);
      var m = $('.mini-bar i', card); if (m) m.style.width = (d / n * 100).toFixed(0) + '%';
      var nn = $('.foot .n', card); if (nn) nn.textContent = d + ' / ' + n + ' 章';
    });
  }

  /* ---------- 搜索 ---------- */
  var Search = {
    items: [],
    sel: 0,
    build: function () {
      var out = [];
      CATALOG.lessons.forEach(function (L) {
        out.push({ kind: 'lesson', id: L.id, title: L.title, meta: '第 ' + L.no + ' 课', no: L.no });
        chaptersOf(L).forEach(function (c, i) {
          out.push({ kind: 'chap', id: L.id, chap: c.id, title: c.title, meta: '第 ' + L.no + ' 课 · ' + (i + 1), no: L.no });
        });
      });
      this.items = out;
    },
    open: function () {
      var p = $('#cmdk'); if (!p) return;
      p.classList.add('on');
      var inp = $('#cmdk-input'); inp.value = ''; inp.focus();
      this.render('');
    },
    close: function () { var p = $('#cmdk'); if (p) p.classList.remove('on'); },
    render: function (q) {
      q = (q || '').trim().toLowerCase();
      var list = this.items.filter(function (it) {
        return !q || (it.title + ' ' + it.meta).toLowerCase().indexOf(q) >= 0;
      }).slice(0, 40);
      this.shown = list; this.sel = 0;
      var box = $('#cmdk-list');
      if (!list.length) { box.innerHTML = '<div class="cmdk-item" style="color:#5d7186">没有匹配的内容</div>'; return; }
      box.innerHTML = list.map(function (it, i) {
        return '<div class="cmdk-item' + (i === 0 ? ' sel' : '') + '" data-i="' + i + '">' +
          '<span>' + esc(it.title) + '</span><span class="c">' + esc(it.meta) + '</span>' +
          '<span class="m">' + (it.kind === 'chap' ? '章节' : '课程') + '</span></div>';
      }).join('');
      $$('#cmdk-list .cmdk-item').forEach(function (el) {
        el.onclick = function () { Search.pick(+el.dataset.i); };
      });
    },
    move: function (d) {
      if (!this.shown || !this.shown.length) return;
      this.sel = (this.sel + d + this.shown.length) % this.shown.length;
      $$('#cmdk-list .cmdk-item').forEach(function (el, i) { el.classList.toggle('sel', i === Search.sel); });
      var cur = $('#cmdk-list .cmdk-item.sel');
      if (cur) cur.scrollIntoView({ block: 'nearest' });
    },
    pick: function (i) {
      var it = this.shown[i]; if (!it) return;
      this.close();
      if (it.kind === 'chap') location.href = '/lesson/' + it.id + '/#' + it.chap;
      else location.href = '/lesson/' + it.id + '/';
    }
  };

  /* ---------- 提示 ---------- */
  var toastTimer;
  function toast(msg) {
    var t = $('#toast');
    if (!t) { t = document.createElement('div'); t.id = 'toast'; t.className = 'toast'; document.body.appendChild(t); }
    t.textContent = msg; t.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove('on'); }, 2200);
  }

  /* ---------- 课程页 ---------- */
  function initLesson() {
    var body = document.body;
    var lessonId = body.dataset.lesson;
    var L = CATALOG.lessons.filter(function (x) { return x.id === lessonId; })[0] || { chapters: [] };
    var hash = decodeURIComponent(location.hash.replace('#', ''));
    var active = hash || (chaptersOf(L)[0] || {}).id;
    var frame = $('#view-frame');

    document.title = L.title + ' · IC 后端学院';
    var crumb = $('#crumb');
    if (crumb) crumb.innerHTML = '<span>第 ' + esc(L.no) + ' 课</span><span class="sep">/</span><b id="crumb-ch">' + esc(chName(active)) + '</b>';

    function chName(id) {
      var c = chaptersOf(L).filter(function (x) { return x.id === id; })[0];
      return c ? c.title : '';
    }

    renderRail(lessonId, active);
    bindRail(function (lid, cid) {
      if (lid === lessonId) gotoChapter(cid);
      else location.href = '/lesson/' + lid + '/#' + cid;
    });
    updateProgressUI();

    function setActiveUI(cid) {
      active = cid;
      $$('.chap').forEach(function (el) {
        el.classList.toggle('on', el.dataset.lesson === lessonId && el.dataset.chap === cid);
      });
      var b = $('#crumb-ch'); if (b) b.textContent = chName(cid);
      if (history.replaceState) history.replaceState(null, '', '#' + cid);
    }

    function gotoChapter(cid) {
      setActiveUI(cid);
      if (!frame) return;
      try {
        var W = frame.contentWindow;
        if (W && W.ICLAB && typeof W.ICLAB.go === 'function') { W.ICLAB.go(cid); return; }
      } catch (e) {}
      frame.contentWindow.location.hash = cid;
    }

    if (frame) {
      var handshake = function () {
        var W, tries = 0;
        try { W = frame.contentWindow; } catch (e) { return; }
        try {
          var doc = W.document;
          if (doc && doc.documentElement) doc.documentElement.classList.add('icl-embedded');
        } catch (e) {}
        (function poll() {
          tries++;
          try {
            if (W.ICLAB && W.ICLAB.ready && typeof W.ICLAB.go === 'function') {
              if (active) W.ICLAB.go(active);
              return;
            }
          } catch (e) {}
          if (tries < 60) setTimeout(poll, 80);
        })();
      };
      frame.addEventListener('load', handshake);
      // iframe 可能在本脚本执行前就已加载完成（同源、命中缓存），补一次
      if (frame.contentDocument && frame.contentDocument.readyState === 'complete') setTimeout(handshake, 0);

      var sib = $('#sidebar-toggle');
      if (sib) sib.onclick = function () { $('.rail').classList.toggle('open'); $('#scrim').classList.toggle('on'); };
      var scrim = $('#scrim');
      if (scrim) scrim.onclick = function () { $('.rail').classList.remove('open'); scrim.classList.remove('on'); };
    }

    window.addEventListener('message', function (e) {
      var m = e.data;
      if (!m || !m.type) return;
      if (m.type === 'icl:chapter') {
        if (m.id) setActiveUI(m.id);
        if (m.done && m.id) markChapter(lessonId, m.id, true);
      }
      if (m.type === 'icl:progress' && Array.isArray(m.done)) {
        m.done.forEach(function (cid) { if (!Prog.isDone(lessonId, cid)) Prog.set(lessonId, cid, true); });
        renderRail(lessonId, active);
        updateProgressUI();
      }
    });

    localStorage.setItem(LS_LAST, lessonId);
    Sync.pull().then(function () { renderRail(lessonId, active); updateProgressUI(); });
  }

  /* ---------- 首页 ---------- */
  function initHome() {
    var wrap = $('#home-cards');
    if (!wrap) return;
    wrap.innerHTML = CATALOG.lessons.map(function (L) {
      var soon = L.status === 'soon';
      var total = chaptersOf(L).length;
      var c1 = L.color ? L.color[0] : '#3ea8ff', c2 = L.color ? L.color[1] : '#28d9a4';
      return '<a class="lcard' + (soon ? ' soon' : '') + '" data-lesson="' + esc(L.id) + '" ' +
        (soon ? 'href="javascript:void 0"' : 'href="/lesson/' + esc(L.id) + '/"') +
        ' style="--c1:' + c1 + ';--c2:' + c2 + '">' +
        (soon ? '<span class="soon-tag">筹备中</span>' : '') +
        '<span class="no">LESSON ' + esc(L.no) + '</span>' +
        '<h4>' + esc(L.title) + '</h4>' +
        '<p class="desc">' + esc(L.desc) + '</p>' +
        '<div class="tags">' + (L.tags || []).map(function (t) { return '<span>' + esc(t) + '</span>'; }).join('') + '</div>' +
        '<div class="foot"><span class="n">' + (soon ? '即将开放' : '0 / ' + total + ' 章') + '</span>' +
        '<span class="mini-bar"><i data-lesson="' + esc(L.id) + '"></i></span></div>' +
      '</a>';
    }).join('');

    $$('.lcard.soon').forEach(function (c) {
      c.addEventListener('click', function () { toast('这一课正在制作中，敬请期待'); });
    });

    updateProgressUI();

    // 继续学习
    var last = localStorage.getItem(LS_LAST);
    if (last && CATALOG.lessons.some(function (L) { return L.id === last && L.status !== 'soon'; })) {
      var btn = $('#btn-continue');
      if (btn) { btn.href = '/lesson/' + last + '/'; btn.style.display = ''; }
    }

    if (API) {
      fetch(API + '/stats').then(function (r) { return r.json(); }).then(function (j) {
        var a = $('#stat-learners'), b = $('#stat-done');
        if (a && j.learners != null) a.textContent = j.learners;
        if (b && j.completions != null) b.textContent = j.completions;
      }).catch(function () {});
    }
  }

  /* ---------- 启动 ---------- */
  function boot() {
    Prog.load();

    // 搜索面板
    if (!$('#cmdk')) {
      var d = document.createElement('div');
      d.id = 'cmdk'; d.className = 'cmdk';
      d.innerHTML = '<div class="cmdk-box"><div class="inp">' +
        '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#5d7186" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>' +
        '<input id="cmdk-input" placeholder="搜索课程、章节、命令…"><kbd>ESC</kbd></div><div class="cmdk-list" id="cmdk-list"></div></div>';
      document.body.appendChild(d);
      d.addEventListener('click', function (e) { if (e.target === d) Search.close(); });
      var inp = $('#cmdk-input');
      inp.addEventListener('input', function () { Search.render(inp.value); });
      inp.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowDown') { e.preventDefault(); Search.move(1); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); Search.move(-1); }
        else if (e.key === 'Enter') { e.preventDefault(); Search.pick(Search.sel); }
        else if (e.key === 'Escape') { Search.close(); }
      });
    }

    Search.build();

    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); Search.open(); }
      if (e.key === 'Escape') Search.close();
    });
    $$('[data-search]').forEach(function (b) { b.onclick = function () { Search.open(); }; });

    // 同步状态点
    Sync.dot = $('.sync');

    if (document.body.dataset.page === 'lesson') initLesson();
    else initHome();

    var rb = $('#reset-progress');
    if (rb) rb.onclick = function () {
      if (!confirm('清空本机与云端的全部学习进度？')) return;
      Prog.reset();
      location.reload();
    };
    var sb = $('#sidebar-toggle');
    if (sb) sb.onclick = function () { $('.rail').classList.toggle('open'); var s = $('#scrim'); if (s) s.classList.toggle('on'); };
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
