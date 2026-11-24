/* 管理员课程编辑器：课程页上直接改小节文字（所见即所得）与替换图片。
 * 仅在 window.ICL_ADMIN=true 且页面为课程页时激活。
 * 文字保存走 /api/admin/section/{lesson}/{chapter}（覆盖层，所有人立即可见）；
 * 图片替换走 /api/admin/fig（同名覆写 web/fig/ 下文件，上传即生效）。 */
(function () {
  if (!window.ICL_ADMIN) return;
  var lesson = (document.body && document.body.dataset.lesson) || "";
  if (!lesson || lesson === "home") return;

  var KEPT = ".fig-gallery,figure.fig-ai,figure.fig,label.ch-done";

  function bodyNodes(sec) {
    return [].slice.call(sec.children).filter(function (n) {
      if (n.classList.contains("ch-h")) return false;
      if (n.classList.contains("ch-done")) return false;
      if (n.matches(KEPT)) return false;
      return true;
    });
  }
  function currentBody(sec) {
    var ov = (window.ICL_OVERRIDES || {})[sec.dataset.ch];
    if (ov && ov.body != null) return ov.body;
    return bodyNodes(sec).map(function (n) { return n.outerHTML; }).join("\n");
  }
  function currentTitle(sec) {
    var ov = (window.ICL_OVERRIDES || {})[sec.dataset.ch];
    var h = sec.querySelector(".ch-h h2");
    return (ov && ov.title) || (h ? h.textContent : "");
  }

  /* ---------------- 样式 ---------------- */
  var css = [
    ".icledit{flex:0 0 auto;margin-left:auto;display:inline-flex;align-items:center;justify-content:center;",
    "width:26px;height:26px;border:1px solid #b8c6d8;background:#eef4fb;color:#2f7fd0;border-radius:7px;",
    "cursor:pointer;user-select:none;-webkit-user-select:none;padding:0}",
    ".icledit:hover{background:#dfeaf7;border-color:#9dc3ea}",
    ".icledit svg{display:block;pointer-events:none}",
    ".icl-mask{position:fixed;inset:0;background:rgba(20,30,45,.45);z-index:9998;",
    "display:flex;align-items:flex-start;justify-content:center;padding:4vh 12px;overflow:auto}",
    ".icl-modal{background:#fff;border-radius:12px;max-width:880px;width:100%;padding:18px 20px;",
    "box-shadow:0 12px 48px rgba(0,0,0,.25);font-size:14px;color:#22303f}",
    ".icl-modal h3{margin:0 0 4px;font-size:17px}",
    ".icl-sub{color:#7a8aa0;font-size:12px;margin-bottom:12px}",
    ".icl-modal input[type=text]{width:100%;box-sizing:border-box;font-size:15px;padding:8px 10px;",
    "border:1px solid #c9d6e4;border-radius:8px;margin:6px 0 12px}",
    ".icl-body{border:1px solid #c9d6e4;border-radius:8px;padding:14px;min-height:160px;",
    "max-height:46vh;overflow:auto;background:#fcfdff;line-height:1.7}",
    ".icl-body img{max-width:100%}",
    ".icl-body:focus{outline:2px solid #9dc3ea}",
    ".icl-imgs{margin:12px 0}",
    ".icl-imgs h4{margin:8px 0 6px;font-size:13px;color:#55677d}",
    ".icl-imgrow{display:flex;align-items:center;gap:10px;padding:6px 8px;border:1px solid #e2e9f1;",
    "border-radius:8px;margin-bottom:6px;background:#f7fafd}",
    ".icl-imgrow img{width:84px;height:52px;object-fit:cover;border-radius:5px;border:1px solid #dbe4ee;flex:none}",
    ".icl-imgrow .p{flex:1;font-size:12px;color:#55677d;word-break:break-all}",
    ".icl-imgrow input[type=file]{font-size:12px;max-width:210px}",
    ".icl-imgrow .st{font-size:12px;color:#2c9a6a;min-width:60px;text-align:right}",
    ".icl-imgrow .st.err{color:#c2453e}",
    ".icl-btns{display:flex;gap:10px;margin-top:14px;align-items:center}",
    ".icl-btns .save{background:#2f7fd0;color:#fff;border:none;border-radius:8px;",
    "padding:9px 22px;font-size:14px;cursor:pointer}",
    ".icl-btns .restore{background:#fff;color:#c2453e;border:1px solid #e3b5b2;border-radius:8px;",
    "padding:9px 16px;font-size:13px;cursor:pointer}",
    ".icl-btns .cancel{background:#fff;color:#55677d;border:1px solid #c9d6e4;border-radius:8px;",
    "padding:9px 16px;font-size:13px;cursor:pointer}",
    ".icl-msg{margin-left:auto;font-size:13px;color:#2c9a6a;min-width:80px;text-align:right}",
    ".icl-msg.err{color:#c2453e}",
    ".icl-up{display:inline-block;background:#fff7e0;border:1px dashed #d8a72a;color:#8a6a1a;",
    "border-radius:6px;padding:2px 10px;font-size:12px}",
    ".icl-up.err{background:#fdeeee;border-color:#c2453e;color:#c2453e}"
  ].join("");
  var st = document.createElement("style");
  st.textContent = css;
  document.head.appendChild(st);

  /* ---------------- 每个小节加铅笔编辑按钮 ----------------
   * 按钮挂在 .ch-h 容器上（不进 h2），标题文字永远不会混入图标；
   * user-select:none + pointer-events:none 保证复制内容时不带图标。 */
  var PENCIL_SVG = '<svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true" focusable="false">'
    + '<path fill="currentColor" d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25z"/>'
    + '<path fill="currentColor" d="M20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>'
    + "</svg>";

  document.querySelectorAll("section.ch[data-ch]").forEach(function (sec) {
    var h = sec.querySelector(".ch-h");
    if (!h || h.querySelector(".icledit")) return;   // 防重复：已有按钮的小节跳过
    var b = document.createElement("button");
    b.className = "icledit";
    b.type = "button";
    b.title = "编辑本节";
    b.setAttribute("aria-label", "编辑本节");
    b.innerHTML = PENCIL_SVG;
    b.addEventListener("click", function () { openEditor(sec); });
    h.appendChild(b);
  });

  /* ---------------- 编辑弹窗 ---------------- */
  function esc(t) {
    return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function openEditor(sec) {
    var ch = sec.dataset.ch;
    var mask = document.createElement("div");
    mask.className = "icl-mask";
    mask.innerHTML = [
      '<div class="icl-modal">',
      '  <h3>编辑小节 <span style="color:#7a8aa0;font-weight:normal">#' + esc(ch) + "</span></h3>",
      '  <div class="icl-sub">改完点「保存」立即对所有人生效；「恢复原文」可撤销全部修改；图片选文件后立刻替换生效。</div>',
      '  <label>小节标题</label>',
      '  <input type="text" id="icl-title" value="' + esc(currentTitle(sec)) + '">',
      '  <label>正文（可直接点进去改字、删段落）</label>',
      '  <div class="icl-body" id="icl-body" contenteditable="true"></div>',
      '  <div class="icl-imgs" id="icl-imgs"><h4>图片替换</h4><div id="icl-imglist"></div></div>',
      '  <div class="icl-btns">',
      '    <button class="save" id="icl-save" type="button">保存</button>',
      '    <button class="restore" id="icl-restore" type="button">恢复原文</button>',
      '    <button class="cancel" id="icl-cancel" type="button">取消</button>',
      '    <span class="icl-msg" id="icl-msg"></span>',
      "  </div>",
      "</div>",
    ].join("");
    document.body.appendChild(mask);
    var bodyEl = mask.querySelector("#icl-body");
    bodyEl.innerHTML = currentBody(sec);
    var msg = mask.querySelector("#icl-msg");

    /* ---- 粘贴图片：默认插到本节正文最前面；光标在正文里则按光标位置插入 ---- */
    function pickImageFile(dt) {
      if (!dt) return null;
      var i, f = null;
      if (dt.files && dt.files.length) {
        for (i = 0; i < dt.files.length; i++) {
          if (/^image\//.test(dt.files[i].type)) return dt.files[i];
        }
      }
      if (dt.items) {
        for (i = 0; i < dt.items.length; i++) {
          if (dt.items[i].kind === "file" && /^image\//.test(dt.items[i].type)) {
            f = dt.items[i].getAsFile();
            if (f) return f;
          }
        }
      }
      return null;
    }
    function caretRangeInBody() {
      var sel = window.getSelection();
      if (!sel || !sel.rangeCount) return null;
      var r = sel.getRangeAt(0);
      return bodyEl.contains(r.startContainer) ? r : null;
    }
    function insertLocalImage(rel, ph) {
      var img = document.createElement("img");
      img.src = "/" + rel + "?t=" + Date.now();
      img.alt = "";
      img.loading = "lazy";
      ph.parentNode.insertBefore(img, ph);
      ph.remove();
    }
    function insertPastedImage(file) {
      var ph = document.createElement("span");
      ph.className = "icl-up";
      ph.textContent = "⏳ 图片上传中…";
      var range = caretRangeInBody();
      if (range) { range.deleteContents(); range.insertNode(ph); }
      else { bodyEl.insertBefore(ph, bodyEl.firstChild); }
      // 服务端压缩（PNG→WebP）+ 内容哈希命名，返回本机路径
      fetch("/api/admin/fig-upload", {
        method: "POST",
        body: file,
        credentials: "same-origin",
      })
        .then(function (r) {
          if (!r.ok) return r.json().then(function (j) { throw new Error(j.detail || r.status); });
          return r.json();
        })
        .then(function (j) { insertLocalImage(j.path, ph); })
        .catch(function (ex) {
          ph.className = "icl-up err";
          ph.textContent = "✗ 图片上传失败：" + String(ex.message || ex).slice(0, 40);
        });
    }
    /* 网页上复制的图片：剪贴板里只有外链 HTML，交给服务器抓取转存 */
    function insertFetchedImage(url) {
      var ph = document.createElement("span");
      ph.className = "icl-up";
      ph.textContent = "⏳ 图片转存中…";
      var range = caretRangeInBody();
      if (range) { range.deleteContents(); range.insertNode(ph); }
      else { bodyEl.insertBefore(ph, bodyEl.firstChild); }
      fetch("/api/admin/fig-fetch", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url }),
      })
        .then(function (r) {
          if (!r.ok) return r.json().then(function (j) { throw new Error(j.detail || r.status); });
          return r.json();
        })
        .then(function (j) { insertLocalImage(j.path, ph); })
        .catch(function (ex) {
          ph.className = "icl-up err";
          ph.textContent = "✗ 图片转存失败：" + String(ex.message || ex).slice(0, 40);
        });
    }
    function pickHtmlImgUrls(dt) {
      var html = (dt && dt.getData && dt.getData("text/html")) || "";
      if (!html) return [];
      var out = [], re = /<img\b[^>]*\ssrc="(https?:\/\/[^"]+)"/ig, m;
      while ((m = re.exec(html))) out.push(m[1]);
      return out;
    }
    bodyEl.addEventListener("paste", function (e) {
      var dt = e.clipboardData;
      var file = pickImageFile(dt);
      if (file) {
        e.preventDefault();
        say("检测到粘贴图片，上传中…");
        insertPastedImage(file);
        return;
      }
      var urls = pickHtmlImgUrls(dt);
      if (urls.length) {
        e.preventDefault();
        say("检测到 " + urls.length + " 张网页图片，转存中…");
        urls.forEach(insertFetchedImage);
      }
    });

    function say(t, err) {
      msg.textContent = t;
      msg.className = "icl-msg" + (err ? " err" : "");
    }

    /* 图片行：列出本小节全部 <img>，选文件即上传覆写同名文件 */
    var list = mask.querySelector("#icl-imglist");
    var imgs = [].slice.call(sec.querySelectorAll("img"));
    if (!imgs.length) {
      list.innerHTML = '<div style="color:#8a97a8;font-size:12px">本小节没有图片</div>';
    }
    imgs.forEach(function (img, i) {
      var srcRaw = (img.getAttribute("src") || "").split("?")[0];
      var rel = srcRaw.replace(/^\//, "");
      if (!/^fig\//.test(rel)) return;
      var row = document.createElement("div");
      row.className = "icl-imgrow";
      row.innerHTML =
        '<img src="' + esc(srcRaw) + '" alt="">' +
        '<span class="p">' + esc(rel) + "</span>" +
        '<input type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml">' +
        '<span class="st"></span>';
      var stEl = row.querySelector(".st");
      row.querySelector("input[type=file]").addEventListener("change", function (e) {
        var f = e.target.files && e.target.files[0];
        if (!f) return;
        stEl.textContent = "上传中…";
        stEl.className = "st";
        fetch("/api/admin/fig?path=" + encodeURIComponent(rel), {
          method: "POST",
          body: f,
          credentials: "same-origin",
        })
          .then(function (r) {
            if (!r.ok) return r.json().then(function (j) { throw new Error(j.detail || r.status); });
            return r.json();
          })
          .then(function () {
            var v = "?t=" + Date.now();
            img.setAttribute("src", srcRaw + v);
            row.querySelector("img").setAttribute("src", srcRaw + v);
            stEl.textContent = "✓ 已替换";
          })
          .catch(function (ex) {
            stEl.textContent = "✗ " + String(ex.message || ex).slice(0, 40);
            stEl.className = "st err";
          });
      });
      list.appendChild(row);
    });

    mask.querySelector("#icl-cancel").addEventListener("click", function () { mask.remove(); });
    mask.addEventListener("click", function (e) { if (e.target === mask) mask.remove(); });

    mask.querySelector("#icl-restore").addEventListener("click", function () {
      if (!confirm("恢复这一小节的原始内容？（当前修改会被清除）")) return;
      fetch("/api/admin/section/" + encodeURIComponent(lesson) + "/" + encodeURIComponent(ch), {
        method: "DELETE",
        credentials: "same-origin",
      })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function () { location.reload(); })
        .catch(function (ex) { say("恢复失败：" + String(ex.message || ex).slice(0, 60), true); });
    });

    mask.querySelector("#icl-save").addEventListener("click", function () {
      var title = mask.querySelector("#icl-title").value.trim();
      var body = bodyEl.innerHTML.trim();
      say("保存中…");
      fetch("/api/admin/section/" + encodeURIComponent(lesson) + "/" + encodeURIComponent(ch), {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title, body: body }),
      })
        .then(function (r) {
          if (!r.ok) return r.json().then(function (j) { throw new Error(j.detail || r.status); });
          return r.json();
        })
        .then(function () { location.reload(); })
        .catch(function (ex) { say("保存失败：" + String(ex.message || ex).slice(0, 60), true); });
    });
  }
})();
