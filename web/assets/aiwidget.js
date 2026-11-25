/* AI 浮窗助教：全站右下角悬浮球，点开与自己的 AI 对话。
 * - 课程页自动把当前课程内容作为上下文（服务端读取并注入 system）
 * - 每个用户在面板里配置自己的接口地址 / API Key / 模型（Key 只存服务器）
 * - 未配置时点开聊天 → 提示先配置
 * 依赖站点登录态（全站本就有登录墙）；登录/注册/审核页不显示。 */
(function () {
  if (/(^\/(login|register|pending))/.test(location.pathname)) return;

  var CSS = [
    ".aiw-ball{position:fixed;right:18px;bottom:18px;width:54px;height:54px;border-radius:50%;",
    "background:linear-gradient(135deg,#2f7fd0,#18a07a);color:#fff;border:none;cursor:pointer;",
    "box-shadow:0 6px 20px rgba(47,127,208,.4);z-index:9000;display:flex;align-items:center;justify-content:center;",
    "font-size:24px;transition:transform .15s}",
    ".aiw-ball:hover{transform:scale(1.08)}",
    ".aiw-panel{position:fixed;right:18px;bottom:84px;width:390px;max-width:calc(100vw - 24px);",
    "height:540px;max-height:calc(100vh - 110px);background:#fff;border-radius:14px;",
    "box-shadow:0 12px 48px rgba(10,30,60,.28);z-index:9001;display:flex;flex-direction:column;",
    "overflow:hidden;font-size:14px;color:#22303f}",
    ".aiw-head{display:flex;align-items:center;gap:8px;padding:12px 14px;background:linear-gradient(135deg,#2f7fd0,#18a07a);color:#fff;flex:0 0 auto}",
    ".aiw-head b{font-size:15px}",
    ".aiw-head .sp{flex:1}",
    ".aiw-head button{background:rgba(255,255,255,.18);color:#fff;border:none;border-radius:7px;",
    "padding:4px 9px;font-size:12px;cursor:pointer}",
    ".aiw-head button:hover{background:rgba(255,255,255,.3)}",
    ".aiw-body{flex:1;overflow-y:auto;padding:14px;background:#f5f8fc}",
    ".aiw-msg{margin:0 0 12px;max-width:88%;padding:9px 12px;border-radius:11px;line-height:1.65;",
    "word-break:break-word;white-space:pre-wrap}",
    ".aiw-msg.user{background:#2f7fd0;color:#fff;margin-left:auto;border-bottom-right-radius:3px}",
    ".aiw-msg.bot{background:#fff;border:1px solid #e3eaf2;border-bottom-left-radius:3px}",
    ".aiw-msg.err{background:#fdeeee;color:#c2453e;border:1px solid #eec4c0}",
    ".aiw-typing{color:#7a8aa0;font-size:12.5px;padding:4px 10px}",
    ".aiw-foot{flex:0 0 auto;display:flex;gap:8px;padding:10px 12px;border-top:1px solid #e3eaf2;background:#fff}",
    ".aiw-foot textarea{flex:1;resize:none;height:44px;border:1px solid #c9d6e4;border-radius:9px;",
    "padding:9px 11px;font-size:13.5px;font-family:inherit}",
    ".aiw-send{flex:0 0 auto;width:60px;border:none;border-radius:9px;background:#2f7fd0;color:#fff;",
    "font-size:13.5px;cursor:pointer}",
    ".aiw-send:disabled{opacity:.5;cursor:default}",
    ".aiw-hint{color:#7a8aa0;font-size:12.5px;padding:6px 2px 0}",
    ".aiw-cfg{padding:14px;overflow-y:auto;flex:1}",
    ".aiw-cfg label{display:block;font-size:12.5px;color:#55677d;margin:10px 0 4px}",
    ".aiw-cfg input,.aiw-cfg select{width:100%;box-sizing:border-box;font-size:13.5px;padding:8px 10px;",
    "border:1px solid #c9d6e4;border-radius:8px;font-family:inherit}",
    ".aiw-cfg .save{width:100%;margin-top:14px;background:#2f7fd0;color:#fff;border:none;border-radius:9px;",
    "padding:10px;font-size:14px;cursor:pointer}",
    ".aiw-cfg .tip{background:#fff7e0;border:1px solid #ecd9a0;color:#8a6a1a;border-radius:9px;",
    "padding:9px 12px;font-size:12.5px;margin-bottom:8px;line-height:1.6}",
    ".aiw-cfg .err{color:#c2453e;font-size:12.5px;margin-top:8px;min-height:16px}",
    "@media (max-width:520px){.aiw-panel{right:12px;left:12px;width:auto;bottom:80px}}"
  ].join("");
  var st = document.createElement("style");
  st.textContent = CSS;
  document.head.appendChild(st);

  var HISTORY = [];                      // [{role, content}]
  var configured = null;                 // null=未知 true/false
  var cfgCache = null;

  /* ---------------- 悬浮球与面板骨架 ---------------- */
  var ball = document.createElement("button");
  ball.className = "aiw-ball";
  ball.type = "button";
  ball.title = "AI 助教";
  ball.innerHTML = "✦";
  document.body.appendChild(ball);

  var panel = null, bodyEl = null, inputEl = null, sendEl = null;

  function openPanel() {
    if (panel) return;
    panel = document.createElement("div");
    panel.className = "aiw-panel";
    panel.innerHTML =
      '<div class="aiw-head"><b>✦ AI 助教</b><span class="sp"></span>' +
      '<button type="button" data-act="cfg">设置</button>' +
      '<button type="button" data-act="clear">清空</button>' +
      '<button type="button" data-act="close">收起</button></div>' +
      '<div class="aiw-body" id="aiw-body"></div>' +
      '<div class="aiw-foot"><textarea id="aiw-input" placeholder="输入问题，回车发送"></textarea>' +
      '<button class="aiw-send" id="aiw-send" type="button">发送</button></div>';
    document.body.appendChild(panel);
    bodyEl = panel.querySelector("#aiw-body");
    inputEl = panel.querySelector("#aiw-input");
    sendEl = panel.querySelector("#aiw-send");
    panel.querySelector('[data-act="close"]').addEventListener("click", closePanel);
    panel.querySelector('[data-act="cfg"]').addEventListener("click", openConfig);
    panel.querySelector('[data-act="clear"]').addEventListener("click", function () {
      HISTORY = [];
      bodyEl.innerHTML = '<div class="aiw-hint">会话已清空。</div>';
    });
    sendEl.addEventListener("click", send);
    inputEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
    });
    if (!HISTORY.length) {
      bodyEl.innerHTML = '<div class="aiw-hint">你好，我是课程助教 ✦ ' +
        (document.body.dataset.lesson ? "我会结合本页课程内容回答你的问题。" : "有任何 IC 后端的问题都可以问我。") +
        "</div>";
    } else {
      HISTORY.forEach(function (m) { bubble(m.role === "user" ? "user" : "bot", m.content); });
      bodyEl.scrollTop = bodyEl.scrollHeight;
    }
    inputEl.focus();
  }

  function closePanel() {
    if (panel) { panel.remove(); panel = null; }
  }

  ball.addEventListener("click", function () {
    if (panel) closePanel(); else openPanel();
  });

  /* ---------------- 气泡与发送 ---------------- */
  function esc(t) {
    return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function bubble(kind, text) {
    var d = document.createElement("div");
    d.className = "aiw-msg " + kind;
    d.textContent = text;
    bodyEl.appendChild(d);
    bodyEl.scrollTop = bodyEl.scrollHeight;
    return d;
  }

  function send() {
    var q = (inputEl.value || "").trim();
    if (!q) return;
    if (configured === false) { openConfig("请先配置你自己的大模型接口，配置好就能提问了。"); return; }
    inputEl.value = "";
    bubble("user", q);
    HISTORY.push({ role: "user", content: q });
    var tip = document.createElement("div");
    tip.className = "aiw-typing";
    tip.textContent = "✦ AI 思考中…";
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
          if (detail === "NO_AI_CONFIG") { configured = false; openConfig("请先配置你自己的大模型接口，配置好就能提问了。"); return; }
          bubble("err", "✗ " + detail);
          HISTORY.pop();               // 失败的这轮不进上下文
          return;
        }
        configured = true;
        HISTORY.push({ role: "assistant", content: res.j.reply });
        bubble("bot", res.j.reply);
      })
      .catch(function (ex) {
        tip.remove();
        sendEl.disabled = false;
        bubble("err", "✗ 网络异常：" + String(ex.message || ex).slice(0, 60));
      });
  }

  /* ---------------- 设置面板 ---------------- */
  function openConfig(tipText) {
    var old = panel.querySelector(".aiw-cfg");
    if (old) old.remove();
    var cfg = document.createElement("div");
    cfg.className = "aiw-cfg";
    cfg.innerHTML = '<div class="aiw-cfg-inner"></div>';
    var inner = cfg.querySelector(".aiw-cfg-inner");
    if (tipText) inner.innerHTML = '<div class="aiw-tip">' + esc(tipText) + "</div>";
    inner.insertAdjacentHTML("beforeend",
      "<label>接口类型（主流厂商均支持，也可自定义任意 OpenAI 兼容接口）</label>" +
      '<select id="aiw-p"><option value="openai">OpenAI 兼容接口（OpenAI / DeepSeek / 智谱 / 通义 / Kimi / 硅基流动 / 各家中转站）</option>' +
      '<option value="anthropic">Anthropic Claude 官方接口</option></select>' +
      "<label>接口地址 Base URL</label>" +
      '<input id="aiw-url" type="text" placeholder="例如 https://api.deepseek.com/v1">' +
      "<label>模型名称</label>" +
      '<input id="aiw-model" type="text" placeholder="例如 deepseek-chat / gpt-4o-mini">' +
      "<label>API Key</label>" +
      '<input id="aiw-key" type="password" placeholder="sk-...">' +
      '<div class="err" id="aiw-cfg-err"></div>' +
      '<button class="save" id="aiw-cfg-save" type="button">保存配置</button>');
    panel.appendChild(cfg);
    bodyEl.style.display = "none";
    panel.querySelector(".aiw-foot").style.display = "none";

    var sel = cfg.querySelector("#aiw-p"), url = cfg.querySelector("#aiw-url"),
        model = cfg.querySelector("#aiw-model"), key = cfg.querySelector("#aiw-key"),
        err = cfg.querySelector("#aiw-cfg-err");

    fetch("/api/ai/settings", { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (s) {
        if (s.provider) sel.value = s.provider;
        if (s.base_url) url.value = s.base_url;
        if (s.model) model.value = s.model;
        if (s.api_key_masked) key.placeholder = "已保存（" + s.api_key_masked + "），留空表示不修改";
        cfgCache = s;
      })
      .catch(function () {});

    sel.addEventListener("change", function () {
      var p = cfgCache && cfgCache.providers && cfgCache.providers[sel.value];
      if (p && !url.value) url.value = p.base;
      if (p && !model.value) model.value = p.model;
      if (p) { url.value = p.base; model.value = p.model; }   // 切类型自动填默认
    });

    cfg.querySelector("#aiw-cfg-save").addEventListener("click", function () {
      err.textContent = "";
      fetch("/api/ai/settings", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: sel.value, base_url: url.value.trim(), model: model.value.trim(), api_key: key.value }),
      })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (res) {
          if (!res.ok) { err.textContent = res.j.detail || "保存失败"; return; }
          configured = true;
          cfg.remove();
          bodyEl.style.display = "";
          panel.querySelector(".aiw-foot").style.display = "";
          bubble("bot", "✅ AI 配置已保存，现在可以提问了。");
          inputEl.focus();
        })
        .catch(function (ex) { err.textContent = "保存失败：" + String(ex.message || ex).slice(0, 60); });
    });
  }

  /* ---------------- 初始化：探测是否已配置 ---------------- */
  fetch("/api/ai/settings", { credentials: "same-origin" })
    .then(function (r) { return r.json(); })
    .then(function (s) { configured = !!s.configured; })
    .catch(function () { configured = false; });
})();
