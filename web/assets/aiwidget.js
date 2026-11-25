/* AI 浮窗助手：全站右下角 AI 机器人悬浮球，点开与自己的大模型对话。
 * - 课程页自动把当前课程内容作为上下文（服务端读取并注入 system）
 * - 每个用户在「AI 设置」里配置接口地址 / API Key / 模型（Key 只存服务器）
 *   支持输入 URL + Key 后一键获取模型列表，下拉选择；可随时编辑或删除配置
 * - 未配置时点开聊天 → 提示先去设置
 * 依赖站点登录态（全站本就有登录墙）；登录/注册/审核页不显示。 */
(function () {
  if (/(^\/(login|register|pending))/.test(location.pathname)) return;

  var ACCENT = "#5b6cff", ACCENT2 = "#9b5cff";
  var ROBOT = '<svg viewBox="0 0 48 48" aria-hidden="true">' +
    '<circle cx="24" cy="6.5" r="3" fill="#fff"/>' +
    '<rect x="22.6" y="9" width="2.8" height="4.6" rx="1.4" fill="#fff"/>' +
    '<rect x="8" y="13.6" width="32" height="24" rx="9.5" fill="rgba(255,255,255,.2)" stroke="#fff" stroke-width="2.6"/>' +
    '<circle cx="17.2" cy="24.6" r="3.3" fill="#fff"/>' +
    '<circle cx="30.8" cy="24.6" r="3.3" fill="#fff"/>' +
    '<path d="M19.5 31.6q4.5 3.2 9 0" stroke="#fff" stroke-width="2.3" fill="none" stroke-linecap="round"/>' +
    '<rect x="2.2" y="21.6" width="4.2" height="8.6" rx="2.1" fill="#fff"/>' +
    '<rect x="41.6" y="21.6" width="4.2" height="8.6" rx="2.1" fill="#fff"/></svg>';

  var GEAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>';
  var TRASH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>';
  var BACK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>';
  var SEND = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/></svg>';
  var CLOSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12"/><path d="M18 6L6 18"/></svg>';
  var MINUS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M5 12h14"/></svg>';
  var ERASER = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 20H8.5L3 14.5a2 2 0 0 1 0-2.8L11.7 3a2 2 0 0 1 2.8 0l6.5 6.5a2 2 0 0 1 0 2.8L14 19.3"/><path d="M8 11l5 5"/></svg>';
  var REFRESH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/></svg>';

  var CSS = [
    /* ---- 悬浮球 ---- */
    ".aiw-ball{position:fixed;right:20px;bottom:20px;width:58px;height:58px;border-radius:50%;",
    "background:linear-gradient(135deg," + ACCENT + "," + ACCENT2 + ");border:none;cursor:pointer;padding:0;",
    "box-shadow:0 8px 24px rgba(91,108,255,.45),0 2px 6px rgba(91,108,255,.3);z-index:9000;",
    "display:flex;align-items:center;justify-content:center;transition:transform .18s,box-shadow .18s}",
    ".aiw-ball:hover{transform:scale(1.07) translateY(-2px);box-shadow:0 12px 30px rgba(91,108,255,.55)}",
    ".aiw-ball:active{transform:scale(.96)}",
    ".aiw-ball .rb{width:34px;height:34px;display:block}",
    ".aiw-ball::before{content:\"\";position:absolute;inset:-5px;border-radius:50%;",
    "border:2px solid rgba(91,108,255,.35);animation:aiwpulse 2.4s ease-out infinite;pointer-events:none}",
    "@keyframes aiwpulse{0%{transform:scale(.85);opacity:1}70%{transform:scale(1.35);opacity:0}100%{opacity:0}}",
    ".aiw-badge{position:absolute;right:-2px;bottom:-2px;width:20px;height:20px;border-radius:50%;",
    "background:linear-gradient(135deg,#22c1dc,#3b82f6);color:#fff;font-size:10.5px;font-weight:700;",
    "display:flex;align-items:center;justify-content:center;letter-spacing:.5px;",
    "border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.25);font-family:Arial,sans-serif}",
    /* ---- 面板 ---- */
    ".aiw-panel{position:fixed;right:20px;bottom:92px;width:400px;max-width:calc(100vw - 24px);",
    "height:580px;max-height:calc(100vh - 120px);background:#fff;border-radius:18px;",
    "box-shadow:0 24px 70px rgba(20,30,80,.32),0 4px 14px rgba(20,30,80,.14);z-index:9001;",
    "display:flex;flex-direction:column;overflow:hidden;font-size:14px;color:#243044;",
    "transform-origin:100% 100%;animation:aiwin .22s cubic-bezier(.2,.9,.3,1.2)}",
    "@keyframes aiwin{from{transform:scale(.86) translateY(14px);opacity:0}to{transform:scale(1) translateY(0);opacity:1}}",
    ".aiw-head{display:flex;align-items:center;gap:10px;padding:13px 14px;flex:0 0 auto;",
    "background:linear-gradient(135deg," + ACCENT + "," + ACCENT2 + ");color:#fff;position:relative}",
    ".aiw-head::after{content:\"\";position:absolute;left:0;right:0;bottom:0;height:3px;",
    "background:linear-gradient(90deg,#22c1dc,#8b5cf6,#5b6cff);opacity:.85}",
    ".aiw-ava{width:34px;height:34px;border-radius:10px;background:rgba(255,255,255,.18);",
    "display:flex;align-items:center;justify-content:center;flex:0 0 auto}",
    ".aiw-ava svg{width:24px;height:24px}",
    ".aiw-tt{flex:1;min-width:0}",
    ".aiw-tt b{display:block;font-size:15px;letter-spacing:.3px}",
    ".aiw-tt i{display:block;font-style:normal;font-size:11px;opacity:.85;margin-top:1px;",
    "display:flex;align-items:center;gap:4px}",
    ".aiw-dot{width:7px;height:7px;border-radius:50%;background:#4ade80;box-shadow:0 0 0 3px rgba(74,222,128,.25);flex:0 0 auto}",
    ".aiw-dot.off{background:#fbbf24;box-shadow:0 0 0 3px rgba(251,191,36,.25)}",
    ".aiw-hbtn{width:30px;height:30px;border-radius:8px;border:none;cursor:pointer;flex:0 0 auto;",
    "background:rgba(255,255,255,.16);color:#fff;display:flex;align-items:center;justify-content:center;",
    "transition:background .15s}",
    ".aiw-hbtn:hover{background:rgba(255,255,255,.32)}",
    ".aiw-hbtn svg{width:16px;height:16px}",
    /* ---- 聊天 ---- */
    ".aiw-view{flex:1;display:flex;flex-direction:column;min-height:0}",
    ".aiw-body{flex:1;overflow-y:auto;padding:16px 14px;background:linear-gradient(180deg,#f7f8fd,#f2f4fb)}",
    ".aiw-body::-webkit-scrollbar{width:6px}",
    ".aiw-body::-webkit-scrollbar-thumb{background:#ccd3e8;border-radius:3px}",
    ".aiw-row{display:flex;gap:8px;margin:0 0 14px;align-items:flex-end}",
    ".aiw-row.u{flex-direction:row-reverse}",
    ".aiw-mava{width:26px;height:26px;border-radius:8px;flex:0 0 auto;display:flex;align-items:center;justify-content:center;",
    "background:linear-gradient(135deg," + ACCENT + "," + ACCENT2 + ")}",
    ".aiw-mava svg{width:18px;height:18px}",
    ".aiw-msg{max-width:78%;padding:10px 13px;border-radius:14px;line-height:1.65;font-size:13.5px;",
    "word-break:break-word;white-space:pre-wrap}",
    ".aiw-row.b .aiw-msg{background:#fff;border:1px solid #e6eaf5;border-bottom-left-radius:4px;",
    "box-shadow:0 1px 4px rgba(30,50,120,.06)}",
    ".aiw-row.u .aiw-msg{background:linear-gradient(135deg," + ACCENT + "," + ACCENT2 + ");color:#fff;",
    "border-bottom-right-radius:4px;box-shadow:0 3px 10px rgba(91,108,255,.3)}",
    ".aiw-msg.err{background:#fef2f2!important;color:#c2453e;border:1px solid #f5cbc6!important}",
    ".aiw-hint{color:#8a94ad;font-size:12.5px;text-align:center;line-height:1.7;padding:10px 8px}",
    ".aiw-hint b{color:" + ACCENT + "}",
    ".aiw-typing{display:inline-flex;gap:4px;align-items:center;padding:10px 14px;background:#fff;",
    "border:1px solid #e6eaf5;border-radius:14px;border-bottom-left-radius:4px}",
    ".aiw-typing s{width:6px;height:6px;border-radius:50%;background:#a5b0d0;display:block;",
    "animation:aiwb 1.2s infinite}",
    ".aiw-typing s:nth-child(2){animation-delay:.15s}.aiw-typing s:nth-child(3){animation-delay:.3s}",
    "@keyframes aiwb{0%,60%,100%{transform:translateY(0);opacity:.5}30%{transform:translateY(-5px);opacity:1}}",
    /* ---- 输入区 ---- */
    ".aiw-foot{flex:0 0 auto;display:flex;gap:9px;align-items:flex-end;padding:11px 13px;",
    "border-top:1px solid #e8ebf5;background:#fff}",
    ".aiw-foot textarea{flex:1;resize:none;height:46px;border:1.5px solid #d4daea;border-radius:12px;",
    "padding:11px 13px;font-size:13.5px;font-family:inherit;line-height:1.5;outline:none;",
    "transition:border-color .15s,box-shadow .15s;background:#f8f9fd}",
    ".aiw-foot textarea:focus{border-color:" + ACCENT + ";background:#fff;",
    "box-shadow:0 0 0 3px rgba(91,108,255,.14)}",
    ".aiw-send{flex:0 0 auto;width:46px;height:46px;border:none;border-radius:12px;cursor:pointer;",
    "background:linear-gradient(135deg," + ACCENT + "," + ACCENT2 + ");color:#fff;",
    "display:flex;align-items:center;justify-content:center;transition:opacity .15s,transform .15s}",
    ".aiw-send svg{width:19px;height:19px}",
    ".aiw-send:hover{transform:translateY(-1px)}",
    ".aiw-send:disabled{opacity:.45;cursor:default;transform:none}",
    /* ---- 设置页 ---- */
    ".aiw-cfg{flex:1;overflow-y:auto;background:#f7f8fd;display:none;flex-direction:column}",
    ".aiw-cfg.on{display:flex}",
    ".aiw-cfg-h{flex:0 0 auto;display:flex;align-items:center;gap:8px;padding:12px 14px;background:#fff;",
    "border-bottom:1px solid #e8ebf5;font-size:14.5px;font-weight:700}",
    ".aiw-cfg-h button{width:28px;height:28px;border:1px solid #dde2f0;background:#fff;border-radius:8px;",
    "cursor:pointer;display:flex;align-items:center;justify-content:center;color:#5a657a}",
    ".aiw-cfg-h button svg{width:15px;height:15px}",
    ".aiw-cfg-b{flex:1;overflow-y:auto;padding:14px}",
    ".aiw-tip{background:#fffbe8;border:1px solid #ecdf9e;color:#8a6a1a;border-radius:10px;",
    "padding:10px 13px;font-size:12.5px;margin-bottom:12px;line-height:1.65}",
    ".aiw-cfg label{display:block;font-size:12px;color:#5a657a;margin:13px 0 5px;font-weight:600;letter-spacing:.3px}",
    ".aiw-cfg input,.aiw-cfg select{width:100%;box-sizing:border-box;font-size:13.5px;padding:9px 12px;",
    "border:1.5px solid #d4daea;border-radius:10px;font-family:inherit;outline:none;background:#fff;",
    "transition:border-color .15s,box-shadow .15s}",
    ".aiw-cfg input:focus,.aiw-cfg select:focus{border-color:" + ACCENT + ";",
    "box-shadow:0 0 0 3px rgba(91,108,255,.14)}",
    ".aiw-cfg .note{font-size:11.5px;color:#98a1b8;margin-top:4px;line-height:1.5}",
    ".aiw-btn{width:100%;border:none;border-radius:11px;padding:11px;font-size:14px;cursor:pointer;",
    "font-weight:600;margin-top:14px;transition:opacity .15s,transform .15s}",
    ".aiw-btn:hover{transform:translateY(-1px)}",
    ".aiw-btn:disabled{opacity:.5;cursor:default;transform:none}",
    ".aiw-btn.pri{background:linear-gradient(135deg," + ACCENT + "," + ACCENT2 + ");color:#fff}",
    ".aiw-btn.ghost{background:#fff;color:" + ACCENT + ";border:1.5px solid #c8cef5}",
    ".aiw-btn.danger{background:#fff;color:#d9534f;border:1.5px solid #f0c4c2}",
    ".aiw-frow{display:flex;gap:8px;margin-top:16px}",
    ".aiw-frow .aiw-btn{margin-top:0}",
    ".aiw-cfg-err{color:#c2453e;font-size:12.5px;margin-top:10px;min-height:17px;line-height:1.5}",
    ".aiw-cfg-ok{color:#16a34a;font-size:12.5px;margin-top:10px;min-height:17px}",
    ".aiw-mrow{display:flex;gap:7px;align-items:center}",
    ".aiw-mrow select{flex:1;min-width:0}",
    ".aiw-mrow .mini{flex:0 0 auto;width:38px;height:38px;border:1.5px solid #c8cef5;background:#fff;",
    "border-radius:10px;color:" + ACCENT + ";cursor:pointer;display:flex;align-items:center;justify-content:center}",
    ".aiw-mrow .mini svg{width:16px;height:16px}",
    ".aiw-mrow .mini:disabled{opacity:.45;cursor:default}",
    "@media (max-width:520px){.aiw-panel{right:10px;left:10px;width:auto;bottom:86px}}",
    "@media (prefers-reduced-motion:reduce){.aiw-panel{animation:none}.aiw-ball::before{animation:none}}"
  ].join("");
  var st = document.createElement("style");
  st.textContent = CSS;
  document.head.appendChild(st);

  var HISTORY = [];                      // [{role, content}]
  var configured = null;                 // null=未知 true/false
  var cfgCache = null;

  /* ---------------- 悬浮球 ---------------- */
  var ball = document.createElement("button");
  ball.className = "aiw-ball";
  ball.type = "button";
  ball.title = "AI 助手";
  ball.innerHTML = '<span class="rb">' + ROBOT + "</span>" +
    '<span class="aiw-badge">AI</span>';
  document.body.appendChild(ball);

  var panel = null, bodyEl = null, inputEl = null, sendEl = null;
  var cfgEl = null, statusDot = null, statusTxt = null;

  function esc(t) {
    return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function refreshStatus() {
    if (!statusDot) return;
    statusDot.classList.toggle("off", configured !== true);
    statusTxt.textContent = configured === true ? "在线" : "未配置";
  }

  function showChat() {
    if (cfgEl) cfgEl.classList.remove("on");
    panel.querySelector(".aiw-view").style.display = "";
  }

  function showCfg() {
    panel.querySelector(".aiw-view").style.display = "none";
    if (!cfgEl) cfgEl = buildCfg();
    cfgEl.classList.add("on");
  }

  /* ---------------- 面板骨架 ---------------- */
  function openPanel() {
    if (panel) return;
    panel = document.createElement("div");
    panel.className = "aiw-panel";
    panel.innerHTML =
      '<div class="aiw-head">' +
        '<div class="aiw-ava">' + ROBOT + "</div>" +
        '<div class="aiw-tt"><b>AI 助手</b><i><span class="aiw-dot" id="aiw-dot"></span><span id="aiw-dot-t">…</span></i></div>' +
        '<button class="aiw-hbtn" type="button" data-act="cfg" title="AI 设置">' + GEAR + "</button>" +
        '<button class="aiw-hbtn" type="button" data-act="clear" title="清空会话">' + ERASER + "</button>" +
        '<button class="aiw-hbtn" type="button" data-act="close" title="收起">' + MINUS + "</button>" +
      "</div>" +
      '<div class="aiw-view">' +
        '<div class="aiw-body" id="aiw-body"></div>' +
        '<div class="aiw-foot"><textarea id="aiw-input" placeholder="输入问题，Enter 发送 · Shift+Enter 换行"></textarea>' +
        '<button class="aiw-send" id="aiw-send" type="button" title="发送">' + SEND + "</button></div>" +
      "</div>";
    document.body.appendChild(panel);
    bodyEl = panel.querySelector("#aiw-body");
    inputEl = panel.querySelector("#aiw-input");
    sendEl = panel.querySelector("#aiw-send");
    statusDot = panel.querySelector("#aiw-dot");
    statusTxt = panel.querySelector("#aiw-dot-t");
    refreshStatus();
    panel.querySelector('[data-act="close"]').addEventListener("click", closePanel);
    panel.querySelector('[data-act="cfg"]').addEventListener("click", function () { openConfig(); });
    panel.querySelector('[data-act="clear"]').addEventListener("click", function () {
      HISTORY = [];
      bodyEl.innerHTML = '<div class="aiw-hint">会话已清空。</div>';
    });
    sendEl.addEventListener("click", send);
    inputEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
    });
    if (!HISTORY.length) {
      bodyEl.innerHTML = '<div class="aiw-hint">你好，我是 <b>AI 助手</b> 🤖<br>' +
        (document.body.dataset.lesson
          ? "我会结合<b>本页课程内容</b>回答你的问题。"
          : "有任何 IC 后端的问题都可以问我。") +
        '<br>右上角 ⚙ 可随时配置你的大模型。</div>';
    } else {
      HISTORY.forEach(function (m) { bubble(m.role === "user" ? "u" : "b", m.content); });
      bodyEl.scrollTop = bodyEl.scrollHeight;
    }
    inputEl.focus();
  }

  function closePanel() {
    if (panel) { panel.remove(); panel = null; cfgEl = null; }
    statusDot = statusTxt = null;
  }

  ball.addEventListener("click", function () {
    if (panel) closePanel(); else openPanel();
  });

  /* ---------------- 气泡与发送 ---------------- */
  function bubble(kind, text, isErr) {
    var row = document.createElement("div");
    row.className = "aiw-row " + kind;
    if (kind === "b") row.innerHTML = '<div class="aiw-mava">' + ROBOT + "</div>";
    var d = document.createElement("div");
    d.className = "aiw-msg" + (isErr ? " err" : "");
    d.textContent = text;
    row.appendChild(d);
    bodyEl.appendChild(row);
    bodyEl.scrollTop = bodyEl.scrollHeight;
    return d;
  }

  function send() {
    var q = (inputEl.value || "").trim();
    if (!q) return;
    if (configured === false) { openConfig("请先配置你自己的大模型接口，配置好就能提问了。"); return; }
    inputEl.value = "";
    bubble("u", q);
    HISTORY.push({ role: "user", content: q });
    var tip = document.createElement("div");
    tip.className = "aiw-row b";
    tip.innerHTML = '<div class="aiw-mava">' + ROBOT + "</div>" +
      '<div class="aiw-typing"><s></s><s></s><s></s></div>';
    bodyEl.appendChild(tip);
    bodyEl.scrollTop = bodyEl.scrollHeight;
    sendEl.disabled = true;
    fetch("/api/ai/chat", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: HISTORY,
        lesson: (document.body.dataset && document.body.dataset.lesson) || null,
      }),
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        tip.remove();
        sendEl.disabled = false;
        if (!res.ok) {
          var detail = res.j.detail || "请求失败";
          if (detail === "NO_AI_CONFIG") { configured = false; refreshStatus(); openConfig("请先配置你自己的大模型接口，配置好就能提问了。"); return; }
          bubble("b", "✗ " + detail, true);
          HISTORY.pop();               // 失败的这轮不进上下文
          return;
        }
        configured = true; refreshStatus();
        HISTORY.push({ role: "assistant", content: res.j.reply });
        bubble("b", res.j.reply);
      })
      .catch(function (ex) {
        tip.remove();
        sendEl.disabled = false;
        bubble("b", "✗ 网络异常：" + String(ex.message || ex).slice(0, 60), true);
      });
  }

  /* ---------------- 设置页 ---------------- */
  function openConfig(tipText) {
    if (!panel) openPanel();
    showCfg();
    var tipEl = cfgEl.querySelector("#aiw-cfg-tip");
    tipEl.textContent = tipText || "";
    tipEl.style.display = tipText ? "" : "none";
    var errEl = cfgEl.querySelector("#aiw-cfg-err");
    errEl.textContent = "";
    loadCfg();
  }

  function buildCfg() {
    var cfg = document.createElement("div");
    cfg.className = "aiw-cfg";
    cfg.innerHTML =
      '<div class="aiw-cfg-h">' +
        '<button type="button" id="aiw-cfg-back" title="返回对话">' + BACK + "</button> AI 设置" +
      "</div>" +
      '<div class="aiw-cfg-b">' +
        '<div class="aiw-tip" id="aiw-cfg-tip" style="display:none"></div>' +
        "<label>接口类型</label>" +
        '<select id="aiw-p">' +
          '<option value="openai">OpenAI 兼容（OpenAI / DeepSeek / 智谱 / 通义 / Kimi / 中转站等）</option>' +
          '<option value="anthropic">Anthropic Claude 官方接口</option>' +
        "</select>" +
        '<div class="note">主流厂商和自定义大模型都支持：填好地址和 Key 后点「获取模型列表」即可下拉选择。</div>' +
        "<label>接口地址 Base URL</label>" +
        '<input id="aiw-url" type="text" placeholder="例如 https://api.deepseek.com/v1" autocomplete="off" spellcheck="false">' +
        "<label>API Key</label>" +
        '<input id="aiw-key" type="password" placeholder="sk-..." autocomplete="new-password">' +
        '<div class="note">Key 只保存在本站服务器，不会暴露给浏览器之外的任何页面。</div>' +
        '<button class="aiw-btn ghost" id="aiw-fetch" type="button">↻ 获取模型列表</button>' +
        "<label>模型名称</label>" +
        '<div class="aiw-mrow">' +
          '<select id="aiw-model" disabled><option value="">请先获取模型列表</option></select>' +
          '<button class="mini" type="button" id="aiw-refetch" title="重新获取">' + REFRESH + "</button>" +
        "</div>" +
        '<div class="note">列表为空或接口不提供 /models？<a href="javascript:void(0)" id="aiw-manual">点此手动输入模型名</a></div>' +
        '<div class="aiw-cfg-err" id="aiw-cfg-err"></div>' +
        '<div class="aiw-frow">' +
          '<button class="aiw-btn pri" id="aiw-cfg-save" type="button">保存配置</button>' +
          '<button class="aiw-btn danger" id="aiw-cfg-del" type="button" style="display:none">' + TRASH + " 删除配置</button>" +
        "</div>" +
      "</div>";
    panel.appendChild(cfg);

    cfg.querySelector("#aiw-cfg-back").addEventListener("click", showChat);
    cfg.querySelector("#aiw-fetch").addEventListener("click", function () { fetchModels(cfg, false); });
    cfg.querySelector("#aiw-refetch").addEventListener("click", function () { fetchModels(cfg, false); });
    cfg.querySelector("#aiw-manual").addEventListener("click", function () { manualModel(cfg); });
    cfg.querySelector("#aiw-cfg-save").addEventListener("click", function () { saveCfg(cfg); });
    cfg.querySelector("#aiw-cfg-del").addEventListener("click", function () { delCfg(cfg); });
    cfg.querySelector("#aiw-p").addEventListener("change", function () {
      var p = cfgCache && cfgCache.providers && cfgCache.providers[cfg.querySelector("#aiw-p").value];
      if (p) {
        cfg.querySelector("#aiw-url").value = p.base;
        resetModels(cfg);
      }
    });
    return cfg;
  }

  function resetModels(cfg) {
    var sel = cfg.querySelector("#aiw-model");
    sel.innerHTML = '<option value="">请先获取模型列表</option>';
    sel.disabled = true;
  }

  /* 获取失败时降级为手动输入（select → input） */
  function manualModel(cfg) {
    var wrap = cfg.querySelector(".aiw-mrow");
    var sel = cfg.querySelector("#aiw-model");
    if (sel.tagName === "INPUT") return;
    var inp = document.createElement("input");
    inp.id = "aiw-model";
    inp.type = "text";
    inp.placeholder = "手动输入模型名，例如 deepseek-chat / gpt-4o-mini";
    inp.autocomplete = "off";
    inp.spellcheck = false;
    if (sel.value) inp.value = sel.value;
    sel.replaceWith(inp);
    var note = cfg.querySelector("#aiw-manual").parentNode;
    note.innerHTML = "已切换为手动输入模式。";
  }

  function fetchModels(cfg, silent) {
    var errEl = cfg.querySelector("#aiw-cfg-err");
    var btn = cfg.querySelector("#aiw-fetch");
    var sel = cfg.querySelector("#aiw-model");
    var url = cfg.querySelector("#aiw-url").value.trim();
    var key = cfg.querySelector("#aiw-key").value;
    if (!url) { errEl.textContent = "请先填写接口地址 Base URL"; return; }
    var cur = sel.value;
    btn.disabled = true;
    if (sel.tagName === "SELECT") sel.disabled = true;
    errEl.textContent = "正在获取模型列表…";
    fetch("/api/ai/models", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ provider: cfg.querySelector("#aiw-p").value, base_url: url, api_key: key }),
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        btn.disabled = false;
        if (!res.ok) {
          errEl.textContent = res.j.detail || "获取失败";
          if (sel.tagName === "SELECT" && cur) sel.disabled = false;
          return;
        }
        errEl.textContent = "";
        var ids = res.j.models || [];
        if (sel.tagName !== "SELECT") {   // 之前手动输入过，换回下拉
          var ns = document.createElement("select");
          ns.id = "aiw-model";
          sel.replaceWith(ns);
          sel = ns;
          cfg.querySelector("#aiw-manual").parentNode.innerHTML =
            '列表为空或接口不提供 /models？<a href="javascript:void(0)" id="aiw-manual">点此手动输入模型名</a>';
          cfg.querySelector("#aiw-manual").addEventListener("click", function () { manualModel(cfg); });
        }
        sel.innerHTML = ids.map(function (m) {
          return '<option value="' + esc(m) + '">' + esc(m) + "</option>";
        }).join("");
        sel.disabled = false;
        if (cur && ids.indexOf(cur) >= 0) sel.value = cur;
        else if (cfgCache && cfgCache.model && ids.indexOf(cfgCache.model) >= 0) sel.value = cfgCache.model;
        errEl.textContent = "✓ 已获取 " + ids.length + " 个模型，请在下方选择";
      })
      .catch(function (ex) {
        btn.disabled = false;
        errEl.textContent = "获取失败：" + String(ex.message || ex).slice(0, 60);
      });
  }

  function loadCfg() {
    var cfg = cfgEl;
    if (!cfg) return;
    fetch("/api/ai/settings", { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (s) {
        cfgCache = s;
        if (s.provider) cfg.querySelector("#aiw-p").value = s.provider;
        if (s.base_url) cfg.querySelector("#aiw-url").value = s.base_url;
        if (s.api_key_masked) cfg.querySelector("#aiw-key").placeholder = "已保存（" + s.api_key_masked + "），留空表示不修改";
        var delBtn = cfg.querySelector("#aiw-cfg-del");
        delBtn.style.display = s.configured ? "" : "none";
        if (s.model) {
          var sel = cfg.querySelector("#aiw-model");
          if (sel.tagName === "SELECT") {
            sel.innerHTML = '<option value="' + esc(s.model) + '">' + esc(s.model) + "（当前）</option>";
            sel.disabled = false;
          } else if (!sel.value) {
            sel.value = s.model;
          }
        }
      })
      .catch(function () {});
  }

  function saveCfg(cfg) {
    var errEl = cfg.querySelector("#aiw-cfg-err");
    var modelEl = cfg.querySelector("#aiw-model");
    errEl.textContent = "";
    var payload = {
      provider: cfg.querySelector("#aiw-p").value,
      base_url: cfg.querySelector("#aiw-url").value.trim(),
      model: (modelEl.value || "").trim(),
      api_key: cfg.querySelector("#aiw-key").value,
    };
    if (!payload.model) { errEl.textContent = "请先获取模型列表并选择模型（或点下方手动输入）"; return; }
    fetch("/api/ai/settings", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { errEl.textContent = res.j.detail || "保存失败"; return; }
        configured = true; refreshStatus();
        cfgCache = null;
        showChat();
        bodyEl.innerHTML = '<div class="aiw-hint">✅ AI 配置已保存，现在可以提问了。</div>';
        inputEl.focus();
      })
      .catch(function (ex) { errEl.textContent = "保存失败：" + String(ex.message || ex).slice(0, 60); });
  }

  function delCfg(cfg) {
    var errEl = cfg.querySelector("#aiw-cfg-err");
    if (!window.confirm("确定删除当前 AI 配置吗？删除后需要重新配置才能提问。")) return;
    fetch("/api/ai/settings", { method: "DELETE", credentials: "same-origin" })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) { errEl.textContent = res.j.detail || "删除失败"; return; }
        configured = false; refreshStatus();
        cfgCache = null;
        var url = cfg.querySelector("#aiw-url"), key = cfg.querySelector("#aiw-key");
        url.value = ""; key.value = "";
        key.placeholder = "sk-...";
        cfg.querySelector("#aiw-cfg-del").style.display = "none";
        resetModels(cfg);
        errEl.textContent = "✓ 配置已删除";
      })
      .catch(function (ex) { errEl.textContent = "删除失败：" + String(ex.message || ex).slice(0, 60); });
  }

  /* ---------------- 初始化：探测是否已配置 ---------------- */
  fetch("/api/ai/settings", { credentials: "same-origin" })
    .then(function (r) { return r.json(); })
    .then(function (s) { configured = !!s.configured; refreshStatus(); })
    .catch(function () { configured = false; });
})();
