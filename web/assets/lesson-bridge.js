/* ============================================================
   课程页 ↔ 平台外壳 桥接
   任意课程页只要引入本文件，即可被平台目录导航、进度同步
   ============================================================ */
(function () {
  'use strict';
  var embedded = (window.parent && window.parent !== window);
  if (embedded && document.documentElement) document.documentElement.classList.add('icl-embedded');

  function post(m) { if (embedded) { try { window.parent.postMessage(m, '*'); } catch (e) {} } }

  function navItems() {
    return Array.prototype.slice.call(document.querySelectorAll('#nav a[data-go]'));
  }

  var chapters = navItems().map(function (a) {
    var t = a.textContent.replace(/^\s*\d+\s*/, '').replace(/\s+/g, ' ').trim();
    return { id: a.getAttribute('data-go'), title: t };
  });

  function report() {
    var done = Array.prototype.slice.call(document.querySelectorAll('#nav a.done'))
      .map(function (a) { return a.getAttribute('data-go'); });
    post({ type: 'icl:progress', done: done, total: chapters.length });
  }

  window.ICLAB = {
    chapters: chapters,
    ready: false,
    go: function (id) {
      if (typeof window.go === 'function') { window.go(id); }
      else { location.hash = id; }
    }
  };

  window.addEventListener('message', function (e) {
    var d = e.data;
    if (d && d.type === 'icl:go' && d.id && window.ICLAB) window.ICLAB.go(d.id);
  });

  function boot() {
    chapters = navItems().map(function (a) {
      return {
        id: a.getAttribute('data-go'),
        title: a.textContent.replace(/^\s*\d+\s*/, '').replace(/\s+/g, ' ').trim()
      };
    });
    window.ICLAB.chapters = chapters;
    window.ICLAB.ready = true;
    post({ type: 'icl:ready', chapters: chapters });
    report();

    var nav = document.getElementById('nav');
    if (nav && window.MutationObserver) {
      var t = null;
      new MutationObserver(function () {
        clearTimeout(t); t = setTimeout(report, 120);
      }).observe(nav, { subtree: true, attributes: true, attributeFilter: ['class'] });
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
