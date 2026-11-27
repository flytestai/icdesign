/* IC 后端学院 · 前端交互：进度同步 / 目录 / 术语卡 / 自测 / 代码复制 */
(function () {
  'use strict';
  var API = '/api';
  /* HTML 转义（放在最前面，供全文件使用；避免依赖文件末尾定义的顺序问题） */
  function esc2(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
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
  var isLesson = document.body.getAttribute('data-page') === 'lesson' && !!lessonId;
  var sections = [].slice.call(document.querySelectorAll('section.ch'));
  var below = {};                        // 章 → 底边是否已在视口 65% 线上方（跨越检测基线）
  var reanchor = null;                   // 服务器进度回填后校正落点（课程页赋值）

  /* ---------------- 共享工具：当前所在章 / 轻提示 ---------------- */
  function curSection() {
    if (!sections.length) return null;
    var y = window.scrollY + 140, cur = sections[0];
    sections.forEach(function (s) { if (s.offsetTop <= y) cur = s; });
    return cur;
  }
  function showToast(msg) {
    var t = document.createElement('div');
    t.className = 'aiw-toast';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(function () { t.classList.add('show'); }, 10);
    setTimeout(function () { t.classList.remove('show'); setTimeout(function () { t.remove(); }, 400); }, 2800);
  }

  /* ---------------- 整课预计时长 + 打卡防刷分（课级 1/5 规则） ----------------
     每课在构建时估算一个总预计学习分钟数（article 的 data-est-min）。
     校验：打卡第 k/N 章时，本课累计有效学习秒数须 ≥ 预计×60/5 × k/N，
     即学完整课至少要花预计时长的 1/5；刷太快，后面的章不计分。
     只认服务器已确认的课级秒数（known），前后端口径一致，避免上报竞态。 */
  var artEl = document.getElementById('article');
  function lessonEstMin() {
    var v = artEl ? parseInt(artEl.getAttribute('data-est-min'), 10) : 0;
    return v > 0 ? v : Math.max(2, sections.length * 2);   // 兜底：每章约 2 分钟
  }
  var known = 0;               // 本课服务器已确认的累计秒数（studyTimer 维护）
  var lastBlockAt = 0;         // 上次"学太快"提示时间（节流 10 秒）
  function markNeed(ch) {
    var n = Math.max(1, sections.length), idx = 1;
    for (var i = 0; i < sections.length; i++) {
      if (sections[i].getAttribute('data-ch') === ch) { idx = i + 1; break; }
    }
    return Math.max(10, Math.round(lessonEstMin() * 60 / 5 * idx / n));
  }
  function canMark(ch) { return known >= markNeed(ch); }
  function fmtSec(s) { return s >= 60 ? Math.round(s / 60 * 10) / 10 + ' 分钟' : s + ' 秒'; }
  function blockToast(ch, need, have) {
    var now = Date.now();
    if (now - lastBlockAt < 10000) return;
    lastBlockAt = now;
    showToast('本课预计学习 ' + lessonEstMin() + ' 分钟，学到这里至少需累计 ' + fmtSec(need) +
      '，当前已学 ' + fmtSec(have) + ' —— 时间不够暂不计分，正常看完就够啦');
  }

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
    var body = { items: items };
    fetch(API + '/progress', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
      if (!d || !d.rejected || !d.rejected.length) return;
      /* 服务端校验未通过（本章有效学习时长不足）：回滚本地打卡并提示 */
      var touched = false;
      d.rejected.forEach(function (x) {
        if (x.lesson !== lessonId) return;
        if (isDone(x.chapter)) { delete done[key(x.chapter)]; touched = true; }
        blockToast(x.chapter, x.need, x.have);
      });
      if (touched) { saveDone(done); paint(); }
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
    fetch(API + '/progress/' + lessonId, { method: 'DELETE' }).catch(function () { });
  });

  /* 全站：登录后立刻把当前设备 uid 登记到账号名下（排行榜按账号汇总进度）。
     这一步必须放在所有页面，否则用户只浏览首页/题库时不建立关联，
     排行榜里就看不到他的进度。 */
  /* 与服务端合并（换浏览器 / 清缓存后可恢复） */
  if (isLesson) {
    fetch(API + '/progress').then(function (r) { return r.json(); }).then(function (d) {
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

  function formatStudyTime(seconds) {
    var s = Math.max(0, Math.floor(Number(seconds) || 0));
    var h = Math.floor(s / 3600), m = Math.floor(s / 60) % 60;
    return h ? h + ' 小时' + (m ? ' ' + m + ' 分钟' : '') : m + ' 分钟';
  }

  /* ============================================================
     学习时长：只在「本页在前台」且「真的在学」时累计。

     设计要点（每条都是为了不漏记、不多记）：

     1) 心跳式累计，不是跳段式
        每 TICK 采样一次，按「真实流逝时间」累加，而不是按「两次操作
        的间隔」累加。间隔式会漏掉「用户停手后到切走之间」的那段；
        心跳式每秒结算一次，误差不超过一个 TICK。

     2) 超时整段不计，但不白送
        last 只在真实操作时更新。某次 tick 发现 now-last > IDLE_MS，
        说明人已经走了 —— 这一 tick 一秒都不加，并且从这一刻起停表。
        既不把 IDLE 白送出去，也不继续累积。

     3) 批次持久化
        flush 出来的批次立刻写 localStorage。页面被关掉、浏览器崩了，
        下次打开还能补传。receipt 表按 (user, batch_id) 去重，重复补传
        不会多记。

     4) 多标签页只让一个页面上报
        同一个页面开多个 tab 时，用 BroadcastChannel + localStorage
        选一个 leader 负责上报，其他 tab 只累计自己那份并在切到前台时
        把额度转给 leader。避免同一段时间被 N 个 tab 各记一遍。
     ============================================================ */
  var PAGE_STUDY = {
    lesson: 1, playground: 1, quiz: 1, exam: 1, glossary: 1, abbr: 1,
    cheatsheet: 1, search: 1, progress: 1, leaderboard: 1
  };
  var studyKey = isLesson && sections.length ? lessonId :
    (PAGE_STUDY[document.body.getAttribute('data-page')] ? '_' + document.body.getAttribute('data-page') : '');
  if (studyKey) {
    (function studyTimer() {
      var IDLE_MS = 600000;   // 10 分钟无操作 → 判挂机
      var TICK_MS = 1000;     // 采样周期
      var FLUSH_MS = 15000;   // 上报周期
      var MAX_BATCH = 60;     // 单批上限，与服务端校验一致
      var LS_BATCH = 'icl.studyq.' + studyKey;   // 未上报批次（按页隔离）
      var LS_LEADER = 'icl.study.leader';

      var accMs = 0;          // 已累计但还没切成批次的毫秒
      var last = performance.now();
      var lastTick = last;
      var away = false;
      var stopped = false;
      var foreground = active();
      var batches = loadQueue();
      var posted = false;
      var hasServerTotal = false;
      var timeEl = document.getElementById('lp-time');
      var paused = '';        // 暂停原因，用于文案

      /* ---------- 批次持久化 ---------- */
      function loadQueue() {
        try {
          var q = JSON.parse(localStorage.getItem(LS_BATCH) || '[]');
          return Array.isArray(q) ? q.filter(function (b) {
            return b && typeof b.id === 'string' && typeof b.seconds === 'number' && b.seconds > 0;
          }) : [];
        } catch (e) { return []; }
      }
      function saveQueue() {
        try {
          // 只保留未确认的批次；上限防止 localStorage 被写爆
          localStorage.setItem(LS_BATCH, JSON.stringify(batches.slice(0, 200)));
        } catch (e) { }
      }

      function fmt(sec) {
        if (!sec) return '';
        if (sec < 60) return sec + ' 秒';
        var m = Math.floor(sec / 60);
        if (m < 60) return m + ' 分钟';
        return Math.floor(m / 60) + ' 时 ' + (m % 60) + ' 分';
      }
      function paintTime() {
        if (!timeEl) return;
        var pending = batches.length || accMs >= 1000;
        var state = stopped ? '登录已失效，请重新登录' :
          paused === 'away' ? '已暂停：本页不在前台，切回继续计时' :
          paused === 'idle' ? '已暂停：10 分钟无操作，动一下鼠标或滚动继续' :
          batches.some(function (b) { return b.failed; }) ? '上报未成功，正在重试' :
          pending ? '计时中，待同步' : '计时中';
        timeEl.textContent = '⏱ ' + (known ? '已记录 ' + fmt(known) + ' · ' : '') + state;
      }

      fetch(API + '/study-time').then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
        if (!d || (posted && !hasServerTotal)) return;
        known = Math.max(known, (d.by_lesson || {})[studyKey] || 0);
        paintTime();
      }).catch(function () { });

      /* ---------- 计时状态 ---------- */
      function active() { return !away && !document.hidden && document.hasFocus(); }

      // 每秒结算：按真实流逝时间累加，但不超过空闲截止点。
      // winAcc：自上次真实操作以来累计了多少毫秒。判定挂机时整段退回，
      // 保证「人走了之后」这段时间一秒都不留在账上。
      var winAcc = 0;
      var pendingBack = 0;   // 需要向服务端追减的秒数（已上报的部分）
      function markIdle() {
        // 要退回的这段可能已经变成了待发批次（甚至已发出），所以按顺序扣：
        //   1) 先从本地未切批的 accMs 扣；
        //   2) 不够就撤掉还没发出去的批次；
        //   3) 还不够说明已经上报了，那就记进 pendingBack，下一次上报时
        //      作为负向修正发给服务端（服务端只减不增，且有下限保护）。
        var need = winAcc;
        winAcc = 0;
        if (need <= 0) { paused = 'idle'; return; }
        if (accMs >= need) { accMs -= need; paused = 'idle'; return; }
        need -= accMs; accMs = 0;
        for (var i = batches.length - 1; i >= 0 && need > 0; i--) {
          if (batches[i].sending) continue;            // 正在发的动不了
          var bsec = batches[i].seconds * 1000;
          if (bsec <= need) { need -= bsec; batches.splice(i, 1); }
          else {
            batches[i].seconds -= Math.ceil(need / 1000);
            need = 0;
            if (batches[i].seconds <= 0) batches.splice(i, 1);
          }
        }
        saveQueue();
        if (need > 0) pendingBack += Math.ceil(need / 1000);
        paused = 'idle';
      }
      function tick() {
        var now = performance.now();
        if (stopped) { lastTick = now; return; }
        if (!foreground) { lastTick = now; paused = 'away'; return; }
        var gap = now - lastTick;      // 距上一次采样（≈TICK_MS）
        lastTick = now;
        if (gap <= 0) return;
        // 关键：判「是否已经离开」要看距**最后一次真实操作**有多久，
        // 而不是距上一次采样。lastTick 每秒都在动，用它永远判不出空闲。
        if (now - last > IDLE_MS) {
          markIdle();                  // 人已经走了：把这一窗口内已记的整段退回
          return;
        }
        // 累计这一 tick，同时记下它落在哪个「活动窗口」里。
        // 一旦后面判定超时，这个窗口内的累计要整段退回 —— 见 markIdle()。
        accMs += gap;
        winAcc += gap;
        paused = '';
      }

      function markActive() {
        var now = performance.now();
        last = now;                 // 只有真实操作才推进「最后一次活动」时刻
        winAcc = 0;                 // 新窗口开始，之前的累计已经"兑现"，不再退回
        if (foreground && !stopped) paused = '';
        lastTick = Math.min(lastTick, now);
        paintTime();
      }

      ['scroll', 'keydown', 'input', 'pointerdown', 'touchstart', 'wheel']
        .forEach(function (ev) {
          window.addEventListener(ev, function (e) {
            if (!e.isTrusted) return;
            markActive();
          }, { passive: true, capture: true });
        });
      var lastMove = 0;
      document.addEventListener('mousemove', function (e) {
        if (!e.isTrusted) return;
        var now = performance.now();
        if (now - lastMove < 2000) return;   // 只用于判定「还在」，无需毫秒精度
        lastMove = now;
        markActive();
      }, { passive: true, capture: true });

      /* ---------- 上报 ---------- */
      function batchId() {
        if (window.crypto.randomUUID) return window.crypto.randomUUID();
        var b = window.crypto.getRandomValues(new Uint8Array(16));
        b[6] = (b[6] & 15) | 64;
        b[8] = (b[8] & 63) | 128;
        return Array.from(b, function (x) { return ('0' + x.toString(16)).slice(-2); })
          .join('').replace(/^(........)(....)(....)(....)/, '$1-$2-$3-$4-');
      }

      // 只有一个 tab 拥有上报权：避免多标签重复计入同一段时间。
      // 用 localStorage 里带时间戳的「leader 记录」做选举：先到先得，
      // leader 每 10 秒续约，超过 25 秒没续约就允许别的 tab 接管。
      var tabId = batchId();
      var isLeader = true;
      (function electLeader() {
        try {
          var cur = localStorage.getItem(LS_LEADER);
          var now = Date.now();
          var rec = cur ? JSON.parse(cur) : null;
          // 心跳续约：leader 每 10 秒刷新时间戳；超过 25 秒视为已死
          if (!rec || rec.id === tabId || now - rec.at > 25000) {
            localStorage.setItem(LS_LEADER, JSON.stringify({ id: tabId, at: now }));
            isLeader = true;
          } else {
            isLeader = false;
          }
        } catch (e) { isLeader = true; }
      })();

      function send(batch, drain) {
        batch.sending = true;
        posted = true;
        fetch(API + '/study-time', {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, keepalive: true,
          body: JSON.stringify({
            lesson: studyKey, seconds: batch.seconds, batch_id: batch.id
          })
        }).then(function (r) {
          if (r.ok) return r.json();
          if (r.status >= 400 && r.status < 500 &&
              r.status !== 408 && r.status !== 425 && r.status !== 429) {
            return { rejected: r.status };
          }
          throw new Error('学习时长上报暂时失败');
        }).then(function (d) {
          if (stopped) return;
          if (!d) throw new Error('缺少学习时长回执');
          var i = batches.indexOf(batch);
          if (i >= 0) batches.splice(i, 1);
          saveQueue();                 // 确认后立即从持久化队列里移除
          if (d.rejected) {
            if (d.rejected === 401 || d.rejected === 403) {
              stopped = true;
              batches.length = 0;
              accMs = 0;
              saveQueue();
            }
          } else if (Number.isFinite(d.lesson_seconds)) {
            hasServerTotal = true;
            known = Math.max(known, d.lesson_seconds);
          } else if (!hasServerTotal) {
            known += Number.isFinite(d.added) ? d.added : batch.seconds;
          }
          paintTime();
          if (drain) sendNext();
        }).catch(function () {
          batch.sending = false;
          batch.failed = true;
          saveQueue();
          paintTime();
        }); // 保留同一批次与 UUID，下次重试（服务端按 UUID 去重，重传不会多记）
      }

      function sendNext() {
        if (away || stopped || !isLeader) return;
        for (var i = 0; i < batches.length; i++) {
          if (!batches[i].sending) { send(batches[i], true); return; }
        }
      }

      function flush(leaving) {
        if (stopped) return;
        var s;
        while ((s = Math.min(MAX_BATCH, Math.floor(accMs / 1000))) > 0) {
          batches.push({ id: batchId(), seconds: s, sending: false });
          accMs -= s * 1000;
        }
        saveQueue();                     // 先落盘，再发；关页也不会丢
        if (!isLeader) { paintTime(); return; }   // 非 leader 不占上报通道
        if (leaving) {
          batches.forEach(function (b) { if (!b.sending) send(b, false); });
        } else {
          sendNext();
        }
        paintTime();
      }

      function setForeground(next) {
        var now = performance.now();
        var leaving = foreground && !next;
        // 离开前台前结算最后一段（tick 已覆盖大部分，这里补边界）
        tick();
        foreground = next;
        paused = next ? '' : 'away';
        if (leaving) flush(true);
        if (!next) last = now;    // 离开时冻结 last，回来不会把离开时长算进去
        paintTime();
      }

      // 结算 + 刷新提示
      setInterval(function () {
        if (away || stopped) return;
        tick();
        paintTime();
      }, TICK_MS);

      // 定期上报
      setInterval(function () {
        if (away || stopped) return;
        // 续约 leader
        if (isLeader) {
          try { localStorage.setItem(LS_LEADER, JSON.stringify({ id: tabId, at: Date.now() })); } catch (e) { }
        } else {
          electLeader();
        }
        flush(false);
      }, FLUSH_MS);

      window.addEventListener('online', function () { flush(false); });
      window.addEventListener('blur', function () { setForeground(false); });
      window.addEventListener('focus', function () { setForeground(active()); });
      document.addEventListener('visibilitychange', function () { setForeground(active()); });
      window.addEventListener('pagehide', function () {
        tick();
        away = true;
        foreground = false;
        flush(true);
      });
      window.addEventListener('pageshow', function () {
        if (!away) return;
        away = false;
        lastTick = performance.now();
        last = performance.now();
        foreground = active();
        flush(false);
      });

      // 页面加载时若还有上次没传完的批次，立刻补传
      if (batches.length) setTimeout(function () { flush(false); }, 1200);
    })();
  }

  /* ============================================================
     每小节的「AI 讲解」按钮。

     两种模式：
       简单 —— 小学生也能懂（多打比方、拆开缩写）
       工作 —— 按真实工作场景讲（上游给什么、这步产出什么、坑在哪）

     点击后打开站内 AI 对话框，直接把整理好的提示词发出去，
     用户不需要自己再组织语言。正文从 DOM 现取，管理员改过的内容
     也能立刻反映进来。
     ============================================================ */
  (function aiExplain() {
    var secs = [].slice.call(document.querySelectorAll('section.ch[data-ch]'));
    if (!secs.length) return;

    // 去掉不该喂给模型的交互件：完成按钮、上下章按钮、AI 按钮自身
    var DROP = '.ch-done,.ch-next,.ch-ai,.fig-gallery';

    function sectionText(sec) {
      var clone = sec.cloneNode(true);
      var h = clone.querySelector('.ch-h');
      var title = h ? (h.querySelector('h2') || {}).textContent || '' : '';
      [].slice.call(clone.querySelectorAll(DROP)).forEach(function (n) { n.remove(); });
      if (h) h.remove();
      var text = (clone.textContent || '')
        .replace(/\n{3,}/g, '\n\n')
        .replace(/[ \t]{2,}/g, ' ')
        .trim();
      return { title: title.trim(), text: text };
    }

    document.addEventListener('click', function (e) {
      var btn = e.target.closest ? e.target.closest('.ch-ai-btn') : null;
      if (!btn) return;
      e.preventDefault();
      var sec = btn.closest('section.ch');
      if (!sec) return;
      if (!window.ICL_AI || !window.ICL_AI.explain) {
        showToast('AI 组件还没加载好，稍等一秒再点');
        return;
      }
      var info = sectionText(sec);
      window.ICL_AI.explain(btn.getAttribute('data-mode') || 'simple', info);
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

    function savePos() {
      var now = Date.now();
      if (now - lastPosSave < 800) return;
      lastPosSave = now;
      var s = curSection();
      if (s) { try { localStorage.setItem(LS_POS, s.getAttribute('data-ch')); } catch (e) { } }
    }
    /* 定位目标：优先本地位置记录；没有（换设备/清缓存）则按进度推导 =
       第一个未完成的章节；全部完成则停在最后一章。 */
    function targetIdx() {
      /* URL 里带 #chapter 锚点（从「继续学习」或「下一章」跳转而来）时优先用它 */
      var hash = (location.hash || '').replace(/^#/, '');
      if (hash) {
        for (var h = 0; h < sections.length; h++) {
          if (sections[h].getAttribute('data-ch') === hash) return h;
        }
      }
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
          /* 防刷分：本课有效学习时长不足时不打卡（基线归位，滚回来重读后可再触发） */
          if (canMark(ch)) {
            done[key(ch)] = 1;
            items.push({ lesson: lessonId, chapter: ch, done: true });
          } else {
            below[ch] = false;
            blockToast(ch, markNeed(ch), known);
          }
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
      fetch(API + '/progress').then(function (r) { return r.json(); }).then(function (d) {
        (d.items || []).forEach(function (it) { if (it.done) done[it.lesson + '/' + it.chapter] = 1; });
        saveDone(done);
        startCatalog();
      }).catch(startCatalog);
    })();

    /* 首页学习排行榜预览：我的排名 + TOP5 */
    (function homeLeaderboard() {
      var list = document.getElementById('hlb-list');
      var me = document.getElementById('hlb-me');
      if (!list) return;
      var loading = false, loaded = false;
      function refresh() {
        if (document.hidden || loading) return;
        loading = true;
        fetch(API + '/leaderboard', { cache: 'no-store' }).then(function (r) {
        return r.json().then(function (j) { return { ok: r.ok, j: j }; });
      }).then(function (res) {
        if (!res.ok) {
          list.innerHTML = '<div class="hlb-empty">登录后查看排行榜</div>';
          return;
        }
        loaded = true;
        var rows = res.j.rows || [];
        if (!rows.length) { list.innerHTML = '<div class="hlb-empty">还没有数据</div>'; return; }
        var medal = ['🥇', '🥈', '🥉'];
        list.innerHTML = rows.slice(0, 5).map(function (r) {
          var rk = r.rank <= 3 ? medal[r.rank - 1] : r.rank;
          return '<a class="hlb-row' + (r.is_me ? ' me' : '') + '" href="/leaderboard/">' +
            '<span class="h-rk">' + rk + '</span>' +
            '<span class="h-nm">' + esc2(r.name) + (r.is_me ? '<b class="h-you">我</b>' : '') + '</span>' +
            '<span class="h-tm">' + formatStudyTime(r.seconds) + '</span></a>';
        }).join('');
        var mine = rows.filter(function (r) { return r.is_me; })[0];
        if (mine && me) {
          me.hidden = false;
          me.innerHTML = '我的排名 <b>第 ' + mine.rank + ' 名</b> / 共 ' + rows.length +
            ' 人 · 学习时长 <b>' + formatStudyTime(mine.seconds) + '</b>';
        }
      }).catch(function (e) {
        if (!loaded) list.innerHTML = '<div class="hlb-empty">排行榜加载失败，稍后自动重试</div>';
        if (window.console) console.warn('[排行榜]', e);
      }).finally(function () { loading = false; });
      }
      refresh();
      window.addEventListener('focus', refresh);
      window.addEventListener('pageshow', refresh);
      document.addEventListener('visibilitychange', refresh);
      setInterval(refresh, 15000);
    })();

    /* 首页主按钮改为「继续学习」：按账号真实进度决定去哪 */
    (function continueBtn() {
      var btn = document.getElementById('hh-continue');
      var sub = document.getElementById('hh-sub');
      if (!btn) return;
      fetch(API + '/next').then(function (r) { return r.json(); }).then(function (d) {
        if (!d || !d.lesson) return;
        var href = '/lesson/' + d.lesson + '/';
        if (d.chapter) href += '#' + d.chapter;
        btn.href = href;
        if (d.reason === 'anonymous' || d.reason === 'next-undone' && !d.chapter) {
          btn.textContent = '从第一课开始 →';
          return;
        }
        if (d.reason === 'all-done') {
          btn.textContent = '全部学完 · 去复习 →';
          if (sub) sub.textContent = '恭喜，主线课程都学过了';
          return;
        }
        btn.textContent = '继续学习 →';
        if (sub) {
          sub.textContent = d.reason === 'resume' ? '接着上次的位置' : '下一门没学完的课';
        }
      }).catch(function () { });
    })();
  }

  /* ---------------- 每章底部「继续下一章」 ---------------- */
  document.querySelectorAll('.ch-next-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      /* 当前章未打卡时先尝试打卡（防刷分：时长不够则提示且不计分） */
      var sec = btn.closest('section.ch');
      var ch = sec && sec.getAttribute('data-ch');
      if (ch && !isDone(ch)) {
        if (canMark(ch)) {
          setDone(ch, true);
        } else {
          blockToast(ch, markNeed(ch), known);
        }
      }

      /* 参考页末节带 data-go：固定回本模块主课，不走主线续学位置 */
      var go = btn.getAttribute('data-go');
      if (go) { location.href = go; return; }

      var nextCh = btn.getAttribute('data-next');
      if (nextCh) {
        var target = document.getElementById(nextCh);
        if (target) {
          window.scrollTo({ top: Math.max(0, target.offsetTop - 80), behavior: 'smooth' });
          return;
        }
      }
      /* 本课最后一章：问服务端下一门该学什么（主线续学位置） */
      fetch(API + '/next').then(function (r) { return r.json(); }).then(function (d) {
        if (d && d.lesson && d.lesson !== lessonId) {
          location.href = '/lesson/' + d.lesson + '/' + (d.chapter ? '#' + d.chapter : '');
        } else {
          var nav = document.querySelector('.end-nav .nav-btn:last-child');
          if (nav) location.href = nav.getAttribute('href');
        }
      }).catch(function () {
        var nav = document.querySelector('.end-nav .nav-btn:last-child');
        if (nav) location.href = nav.getAttribute('href');
      });
    });
  });

  /* ---------------- 阶段折叠（默认展开，状态记忆） ---------------- */
  (function stageCollapse() {
    var LS_STG = 'icl.stageCollapsed';
    function loadCollapsed() {
      try { return JSON.parse(localStorage.getItem(LS_STG) || '{}'); } catch (e) { return {}; }
    }
    function saveCollapsed(o) {
      try { localStorage.setItem(LS_STG, JSON.stringify(o)); } catch (e) { }
    }
    var collapsed = loadCollapsed();
    var toggles = [].slice.call(document.querySelectorAll('.stage-toggle'));
    if (!toggles.length) return;

    function apply(t, stage) {
      var stageEl = t.closest('.stage');
      if (!stageEl) return;
      var isCollapsed = !!collapsed[stage];
      stageEl.classList.toggle('collapsed', isCollapsed);
      t.setAttribute('aria-expanded', isCollapsed ? 'false' : 'true');
    }
    toggles.forEach(function (t) {
      var stage = t.getAttribute('data-stage');
      apply(t, stage);                              // 初始化：按记忆状态渲染
      t.addEventListener('click', function () {
        collapsed[stage] = !collapsed[stage];
        saveCollapsed(collapsed);
        apply(t, stage);
      });
      t.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); t.click(); }
      });
    });
  })();

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

    fetch(API + '/notes/' + lessonId).then(function (r) { return r.json(); }).then(function (d) {
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
        body: JSON.stringify({ lesson: lessonId, body: body })
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
    var all = cat.lessons || [];
    var byId = {};
    all.forEach(function (L) { byId[L.id] = L; });
    /* 学习顺序以 catalog.route 为准（课表主线）；没有 route 才退回课号排序 */
    var route = (cat.route || []).map(function (id) { return byId[id]; }).filter(Boolean);
    var lessons = route.length ? route : all.slice().sort(function (a, b) {
      return String(a.no).localeCompare(String(b.no), 'zh-Hans-CN', { numeric: true });
    });

    /* 2) 课程页：底部「上一课 / 下一课」已由构建器按主线渲染，这里不再追加
       第二套导航，避免同页出现两条顺序不同的翻页。 */

    /* 3) 首页：续学卡（按主线顺序找下一章没学完的位置） */
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
            '<a class="ghost" href="/#plan">先看学习路线</a>';
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

})();
