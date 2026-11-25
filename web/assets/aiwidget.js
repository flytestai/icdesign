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
  var NOTEBOOK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M9.5 7.5h6"/><path d="M9.5 11.5h6"/></svg>';
  var BOOKMARK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>';
  var COPY = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
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
    "transition:background .15s;position:relative}",
    ".aiw-nb{position:absolute;top:-4px;right:-5px;min-width:16px;height:16px;border-radius:8px;",
    "background:#ef4444;color:#fff;font-size:10px;font-weight:700;line-height:16px;text-align:center;",
    "padding:0 4px;display:none;box-shadow:0 1px 3px rgba(0,0,0,.3)}",
    ".aiw-nb.on{display:block}",
    ".aiw-link{color:" + ACCENT + ";cursor:pointer;text-decoration:underline}",
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
    ".aiw-acts{display:flex;gap:14px;margin:-9px 0 13px 34px}",
    ".aiw-acts button{background:none;border:none;color:#98a1b8;font-size:11.5px;cursor:pointer;",
    "padding:0;display:flex;align-items:center;gap:4px;font-family:inherit;transition:color .15s}",
    ".aiw-acts button:hover{color:" + ACCENT + "}",
    ".aiw-acts button:disabled{color:#22c55e;cursor:default}",
    ".aiw-acts button.fail{color:#c2453e}",
    ".aiw-acts svg{width:12px;height:12px}",
    /* ---- Markdown 渲染样式 ---- */
    ".aiw-msg .aiw-p{margin:0 0 6px;line-height:1.65}",
    ".aiw-msg .aiw-p:last-child{margin-bottom:0}",
    ".aiw-msg .aiw-h{font-weight:700;font-size:13.5px;margin:8px 0 4px;line-height:1.5}",
    ".aiw-msg ul,.aiw-msg ol{margin:4px 0 8px;padding-left:20px}",
    ".aiw-msg ul:last-child,.aiw-msg ol:last-child{margin-bottom:0}",
    ".aiw-msg li{margin:2px 0;line-height:1.6}",
    ".aiw-msg code{background:#eef1fa;border-radius:4px;padding:1px 5px;font-size:12px;",
    "font-family:Consolas,Menlo,monospace}",
    ".aiw-msg pre{background:#eef1fa;border:1px solid #e0e5f4;border-radius:8px;padding:8px 11px;",
    "overflow-x:auto;margin:6px 0}",
    ".aiw-msg pre:last-child{margin-bottom:0}",
    ".aiw-msg pre code{background:none;border:none;padding:0;font-size:12px;line-height:1.55}",
    ".aiw-msg a{color:inherit;text-decoration:underline}",
    ".aiw-math{white-space:nowrap}",
    ".aiw-msg sub,.aiw-msg sup{font-size:.72em}",
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
    "font-weight:600;margin-top:14px;transition:opacity .15s,transform .15s;",
    "display:flex;align-items:center;justify-content:center;gap:7px}",
    ".aiw-btn svg{width:15px;height:15px;flex:0 0 auto}",
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
    /* ---- 问答笔记页 ---- */
    ".aiw-notes{flex:1;overflow-y:auto;background:#f7f8fd;display:none;flex-direction:column}",
    ".aiw-notes.on{display:flex}",
    ".aiw-notes-h{flex:0 0 auto;display:flex;align-items:center;gap:8px;padding:12px 14px;background:#fff;",
    "border-bottom:1px solid #e8ebf5;font-size:14.5px;font-weight:700}",
    ".aiw-notes-h button{width:28px;height:28px;border:1px solid #dde2f0;background:#fff;border-radius:8px;",
    "cursor:pointer;display:flex;align-items:center;justify-content:center;color:#5a657a}",
    ".aiw-notes-h button svg{width:15px;height:15px}",
    ".aiw-notes-h .cnt{font-size:12px;font-weight:400;color:#98a1b8}",
    ".aiw-notes-b{flex:1;overflow-y:auto;padding:12px}",
    ".aiw-ni{background:#fff;border:1px solid #e6eaf5;border-radius:12px;padding:10px 12px;margin-bottom:10px;",
    "box-shadow:0 1px 3px rgba(30,50,120,.05)}",
    ".aiw-ni-meta{display:flex;align-items:center;gap:8px;font-size:11px;color:#98a1b8;margin-bottom:6px}",
    ".aiw-ni-meta a{color:" + ACCENT + ";text-decoration:none;font-weight:600}",
    ".aiw-ni-meta .sp{flex:1}",
    ".aiw-ni-meta button{background:none;border:none;color:#b6bdcf;cursor:pointer;padding:0;display:flex}",
    ".aiw-ni-meta button:hover{color:#c2453e}",
    ".aiw-ni-meta button svg{width:13px;height:13px}",
    ".aiw-ni-q{font-size:13px;font-weight:600;line-height:1.55;word-break:break-word;color:#2a3650}",
    ".aiw-ni-a{font-size:12.5px;color:#5a657a;line-height:1.65;margin-top:6px;white-space:pre-wrap;",
    "word-break:break-word;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;",
    "overflow:hidden;cursor:pointer}",
    ".aiw-ni-a.open{-webkit-line-clamp:unset;display:block}",
    ".aiw-ni-hint{color:#98a1b8;font-size:12px;text-align:center;padding:16px 10px;line-height:1.8}",
    /* ---- 课程页内嵌「本课 AI 问答」展开块 ---- */
    ".aiw-lsec{margin:20px 0 0;border:1px solid #dfe4ff;border-radius:14px;background:#fff;overflow:hidden}",
    ".aiw-ln-h{display:flex;align-items:center;gap:10px;padding:13px 18px;cursor:pointer;user-select:none;",
    "background:linear-gradient(135deg,#eef1ff,#f6efff);font-size:14px;font-weight:600;color:#3a4668}",
    ".aiw-ln-h:hover{background:linear-gradient(135deg,#e6eaff,#f0e6ff)}",
    ".aiw-ln-h .cnt{font-size:11.5px;font-weight:600;color:" + ACCENT + ";background:#e4e7ff;",
    "border-radius:10px;padding:2px 9px}",
    ".aiw-ln-h .sub{font-size:11px;font-weight:400;color:#98a1b8}",
    ".aiw-ln-h .arr{margin-left:auto;color:#8a94ad;transition:transform .2s;font-size:12px}",
    ".aiw-ln-h.open .arr{transform:rotate(180deg)}",
    ".aiw-ln-b{border-top:1px solid #e6eaf5;background:#fbfcff;padding:6px 18px;display:none}",
    ".aiw-ln-b.open{display:block}",
    ".aiw-lni{padding:12px 0;border-bottom:1px dashed #e3e8f5}",
    ".aiw-lni:last-child{border-bottom:none}",
    ".aiw-lni .m{font-size:11px;color:#98a1b8;margin-bottom:5px}",
    ".aiw-lni .q{font-size:13.5px;font-weight:600;color:#2a3650;line-height:1.6;word-break:break-word}",
    ".aiw-lni .a{font-size:13px;color:#4a5470;line-height:1.7;margin-top:6px;word-break:break-word}",
    ".aiw-lni .a p{margin:0 0 6px}",
    ".aiw-ln-empty{color:#98a1b8;font-size:12.5px;text-align:center;padding:16px 0}",
    /* ---- 常驻快捷入口栏（对话视图底部） ---- */
    ".aiw-quickbar{flex:0 0 auto;display:flex;gap:18px;padding:8px 14px;background:#f2f4fb;",
    "border-top:1px solid #e8ebf5;font-size:12px}",
    ".aiw-qb{color:#5a657a;cursor:pointer;display:flex;align-items:center;gap:4px;",
    "font-family:inherit;background:none;border:none;padding:0;font-size:12px}",
    ".aiw-qb:hover{color:" + ACCENT + "}",
    ".aiw-qb b{color:" + ACCENT + "}",
    ".aiw-flash{outline:3px solid " + ACCENT + " !important;outline-offset:2px;border-radius:6px}",
    /* ---- 拖拽调尺寸把手 ---- */
    ".aiw-rz{position:absolute;z-index:30}",
    ".aiw-rz-c{left:0;top:0;width:20px;height:20px;cursor:nwse-resize}",
    ".aiw-rz-c::after{content:\"\";position:absolute;left:5px;top:5px;width:9px;height:9px;",
    "border-left:3px solid #c9d0e6;border-top:3px solid #c9d0e6;border-top-left-radius:4px;",
    "transition:border-color .15s}",
    ".aiw-rz-c:hover::after{border-color:" + ACCENT + "}",
    ".aiw-rz-l{left:-2px;top:10px;bottom:10px;width:7px;cursor:ew-resize}",
    ".aiw-rz-t{top:-2px;left:24px;right:10px;height:7px;cursor:ns-resize}",
    "@media(max-width:520px){.aiw-rz{display:none}}",
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
  var cfgEl = null, noteEl = null, statusDot = null, statusTxt = null;

  function esc(t) {
    return String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function refreshStatus() {
    if (!statusDot) return;
    statusDot.classList.toggle("off", configured !== true);
    statusTxt.textContent = configured === true ? "在线" : "未配置";
  }

  /* 笔记数量角标 */
  function refreshBadge() {
    if (!panel) return;
    fetch("/api/ai/notes", { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var n = (j.notes || []).length;
        var nb = panel.querySelector("#aiw-nb");
        if (nb) {
          nb.textContent = n > 99 ? "99+" : String(n);
          nb.classList.toggle("on", n > 0);
        }
        var qb = panel.querySelector("#aiw-qb-n");
        if (qb) qb.textContent = String(n);
      })
      .catch(function () {});
  }

  /* 跳到页面底部的课程笔记框并高亮 */
  function scrollToNote() {
    var box = document.getElementById("note-box");
    if (!box) return;
    if (panel) closePanel();
    box.scrollIntoView({ behavior: "smooth", block: "center" });
    box.classList.add("aiw-flash");
    setTimeout(function () { box.classList.remove("aiw-flash"); }, 2500);
  }

  /* ---------------- 课程页内嵌「本课 AI 问答」展开块 ---------------- */
  function initLessonQa() {
    var lesson = (document.body && document.body.dataset && document.body.dataset.lesson) || "";
    if (!lesson) return;
    var notes = document.getElementById("notes");
    if (!notes || document.getElementById("aiw-lsec")) return;
    var sec = document.createElement("section");
    sec.className = "aiw-lsec";
    sec.id = "aiw-lsec";
    sec.innerHTML =
      '<div class="aiw-ln-h" id="aiw-ln-h">' +
        '<span>🤖 本课 AI 问答</span>' +
        '<span class="cnt" id="aiw-ln-cnt">…</span>' +
        '<span class="sub">自动保存 · 点击展开查看</span>' +
        '<span class="arr" id="aiw-ln-arr">▾</span>' +
      "</div>" +
      '<div class="aiw-ln-b" id="aiw-ln-b"></div>';
    notes.parentNode.insertBefore(sec, notes);
    sec.querySelector("#aiw-ln-h").addEventListener("click", function () {
      var b = sec.querySelector("#aiw-ln-b");
      var h = sec.querySelector("#aiw-ln-h");
      var open = b.classList.toggle("open");
      h.classList.toggle("open", open);
      if (open) loadLessonQa();
    });
    refreshLessonQa();
  }

  function refreshLessonQa() {
    var cnt = document.getElementById("aiw-ln-cnt");
    if (!cnt) return;
    var lesson = document.body.dataset.lesson || "";
    fetch("/api/ai/notes", { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var items = (j.notes || []).filter(function (n) { return n.lesson === lesson; });
        cnt.textContent = items.length + " 条";
        var qb = panel && panel.querySelector("#aiw-qb-n");
        if (qb) qb.textContent = String((j.notes || []).length);
        var b = document.getElementById("aiw-ln-b");
        if (b && b.classList.contains("open")) renderLessonQa(items, b);
      })
      .catch(function () {
        cnt.textContent = "";
      });
  }

  function loadLessonQa() {
    var b = document.getElementById("aiw-ln-b");
    if (!b) return;
    b.innerHTML = '<div class="aiw-ln-empty">加载中…</div>';
    var lesson = document.body.dataset.lesson || "";
    fetch("/api/ai/notes", { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        var items = (j.notes || []).filter(function (n) { return n.lesson === lesson; });
        renderLessonQa(items, b);
      })
      .catch(function () {
        b.innerHTML = '<div class="aiw-ln-empty">加载失败，请稍后重试。</div>';
      });
  }

  function renderLessonQa(items, b) {
    if (!items.length) {
      b.innerHTML = '<div class="aiw-ln-empty">本课还没有 AI 问答记录。<br>在对话里提问后，问答会自动保存在这里。</div>';
      return;
    }
    b.innerHTML = items.map(function (n) {
      return '<div class="aiw-lni">' +
        '<div class="m">' + fmtTs(n.ts) + "</div>" +
        '<div class="q">Q：' + esc(n.question) + "</div>" +
        '<div class="a">A：' + mdToHtml(n.answer) + "</div></div>";
    }).join("");
  }

  function scrollToQa() {
    var sec = document.getElementById("aiw-lsec");
    if (!sec) { openNotes(); return; }
    if (panel) closePanel();
    var b = sec.querySelector("#aiw-ln-b");
    var h = sec.querySelector("#aiw-ln-h");
    if (b && !b.classList.contains("open")) {
      b.classList.add("open");
      h.classList.add("open");
      loadLessonQa();
    }
    sec.scrollIntoView({ behavior: "smooth", block: "start" });
    h.classList.add("aiw-flash");
    setTimeout(function () { h.classList.remove("aiw-flash"); }, 2500);
  }

  function showChat() {
    if (cfgEl) cfgEl.classList.remove("on");
    if (noteEl) noteEl.classList.remove("on");
    panel.querySelector(".aiw-view").style.display = "";
  }

  function showCfg() {
    if (noteEl) noteEl.classList.remove("on");
    panel.querySelector(".aiw-view").style.display = "none";
    if (!cfgEl) cfgEl = buildCfg();
    cfgEl.classList.add("on");
  }

  function showNotes() {
    if (cfgEl) cfgEl.classList.remove("on");
    panel.querySelector(".aiw-view").style.display = "none";
    if (!noteEl) noteEl = buildNotes();
    noteEl.classList.add("on");
    renderNotes();
  }

  function openNotes() {
    if (!panel) openPanel();
    showNotes();
  }

  /* ---------------- 问答笔记页 ---------------- */
  function buildNotes() {
    var nv = document.createElement("div");
    nv.className = "aiw-notes";
    nv.innerHTML =
      '<div class="aiw-notes-h">' +
        '<button type="button" id="aiw-notes-back" title="返回对话">' + BACK + "</button> AI 问答笔记" +
        '<span class="cnt" id="aiw-notes-cnt"></span>' +
      "</div>" +
      '<div class="aiw-notes-b" id="aiw-notes-list"></div>';
    panel.appendChild(nv);
    nv.querySelector("#aiw-notes-back").addEventListener("click", showChat);
    return nv;
  }

  function fmtTs(ts) {
    var d = new Date(ts * 1000);
    var p = function (n) { return (n < 10 ? "0" : "") + n; };
    return (d.getMonth() + 1) + "-" + p(d.getDate()) + " " + p(d.getHours()) + ":" + p(d.getMinutes());
  }

  function renderNotes() {
    var list = noteEl.querySelector("#aiw-notes-list");
    var cnt = noteEl.querySelector("#aiw-notes-cnt");
    list.innerHTML = '<div class="aiw-ni-hint">加载中…</div>';
    fetch("/api/ai/notes", { credentials: "same-origin" })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (!res.ok) {
          list.innerHTML = '<div class="aiw-ni-hint">' + esc(res.j.detail || "加载失败") + "</div>";
          return;
        }
        var notes = res.j.notes || [];
        cnt.textContent = notes.length ? "共 " + notes.length + " 条" : "";
        var nb = panel && panel.querySelector("#aiw-nb");
        if (nb) {
          nb.textContent = notes.length > 99 ? "99+" : String(notes.length);
          nb.classList.toggle("on", notes.length > 0);
        }
        if (!notes.length) {
          list.innerHTML = '<div class="aiw-ni-hint">还没有 AI 问答记录。<br>课程页提问后自动保存，<br>也可在各课底部的「🤖 本课 AI 问答」展开查看。</div>';
          return;
        }
        list.innerHTML = notes.map(function (n) {
          var src = n.lesson
            ? '<a href="/lesson/' + esc(n.lesson) + '/" target="_blank" rel="noopener">' + esc(n.lesson) + "</a>"
            : "站内提问";
          return '<div class="aiw-ni" data-id="' + n.id + '">' +
            '<div class="aiw-ni-meta"><span>' + src + "</span><span>" + fmtTs(n.ts) + '</span><span class="sp"></span>' +
            '<button type="button" data-del="' + n.id + '" title="删除">' + TRASH + "</button></div>" +
            '<div class="aiw-ni-q">Q：' + esc(n.question) + "</div>" +
            '<div class="aiw-ni-a">A：' + mdToHtml(n.answer) + "</div></div>";
        }).join("");
        list.querySelectorAll(".aiw-ni-a").forEach(function (el) {
          el.addEventListener("click", function () { el.classList.toggle("open"); });
        });
        list.querySelectorAll("[data-del]").forEach(function (el) {
          el.addEventListener("click", function () { delNote(el.getAttribute("data-del")); });
        });
      })
      .catch(function () {
        list.innerHTML = '<div class="aiw-ni-hint">加载失败，请稍后重试。</div>';
      });
  }

  function delNote(id) {
    if (!window.confirm("确定删除这条问答笔记吗？")) return;
    fetch("/api/ai/notes/" + id, { method: "DELETE", credentials: "same-origin" })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        if (res.ok) renderNotes();
      })
      .catch(function () {});
  }

  /* ---------------- 面板骨架 ---------------- */
  var SIZE_KEY = "aiw.size";           // 记住用户拖出来的窗口尺寸

  function clampW(w) { return Math.min(Math.max(320, w), window.innerWidth - 24); }
  function clampH(h) { return Math.min(Math.max(380, h), window.innerHeight - 110); }

  function applySize() {
    try {
      var s = JSON.parse(localStorage.getItem(SIZE_KEY) || "null");
      if (s && s.w && s.h) {
        panel.style.width = clampW(s.w) + "px";
        panel.style.height = clampH(s.h) + "px";
      }
    } catch (e) {}
  }

  function saveSize() {
    try {
      localStorage.setItem(SIZE_KEY, JSON.stringify({ w: panel.offsetWidth, h: panel.offsetHeight }));
    } catch (e) {}
  }

  /* 左边缘 / 上边缘 / 左上角把手：向左上拖 = 放大（面板锚定右下角） */
  function addResize(p) {
    ["c", "l", "t"].forEach(function (k) {
      var h = document.createElement("div");
      h.className = "aiw-rz aiw-rz-" + k;
      if (k === "c") h.title = "拖拽调整窗口大小，双击恢复默认";
      p.appendChild(h);
      var startDrag = function (sx, sy) {
        var sw = p.offsetWidth, sh = p.offsetHeight, mode = k;
        document.body.style.userSelect = "none";
        p.style.transition = "none";
        function move(dx, dy) {
          if (mode !== "t") p.style.width = clampW(sw - dx) + "px";
          if (mode !== "l") p.style.height = clampH(sh - dy) + "px";
        }
        function end() {
          document.removeEventListener("mousemove", mm);
          document.removeEventListener("mouseup", me);
          document.removeEventListener("touchmove", tm);
          document.removeEventListener("touchend", te);
          document.body.style.userSelect = "";
          p.style.transition = "";
          saveSize();
        }
        function mm(e) { move(e.clientX - sx, e.clientY - sy); }
        function me() { end(); }
        function tm(e) {
          var t = e.touches[0];
          move(t.clientX - sx, t.clientY - sy);
          e.preventDefault();
        }
        function te() { end(); }
        document.addEventListener("mousemove", mm);
        document.addEventListener("mouseup", me);
        document.addEventListener("touchmove", tm, { passive: false });
        document.addEventListener("touchend", te);
      };
      h.addEventListener("mousedown", function (e) {
        if (e.button !== 0) return;
        e.preventDefault();
        startDrag(e.clientX, e.clientY);
      });
      h.addEventListener("touchstart", function (e) {
        var t = e.touches[0];
        startDrag(t.clientX, t.clientY);
      });
      if (k === "c") {
        h.addEventListener("dblclick", function () {
          p.style.width = "";
          p.style.height = "";
          try { localStorage.removeItem(SIZE_KEY); } catch (e) {}
        });
      }
    });
  }

  function openPanel() {
    if (panel) return;
    panel = document.createElement("div");
    panel.className = "aiw-panel";
    panel.innerHTML =
      '<div class="aiw-head">' +
        '<div class="aiw-ava">' + ROBOT + "</div>" +
        '<div class="aiw-tt"><b>AI 助手</b><i><span class="aiw-dot" id="aiw-dot"></span><span id="aiw-dot-t">…</span></i></div>' +
        '<button class="aiw-hbtn" type="button" data-act="cfg" title="AI 设置">' + GEAR + "</button>" +
        '<button class="aiw-hbtn" type="button" data-act="notes" title="问答笔记">' + NOTEBOOK +
        '<span class="aiw-nb" id="aiw-nb">0</span></button>' +
        '<button class="aiw-hbtn" type="button" data-act="clear" title="清空会话">' + ERASER + "</button>" +
        '<button class="aiw-hbtn" type="button" data-act="close" title="收起">' + MINUS + "</button>" +
      "</div>" +
      '<div class="aiw-view">' +
        '<div class="aiw-body" id="aiw-body"></div>' +
        '<div class="aiw-quickbar">' +
          '<button class="aiw-qb" type="button" data-qb="notes">📒 问答笔记 <b id="aiw-qb-n">0</b> 条</button>' +
          (document.body.dataset && document.body.dataset.lesson
            ? '<button class="aiw-qb" type="button" data-qb="qa">🤖 本课 AI 问答</button>' +
              '<button class="aiw-qb" type="button" data-qb="note">📝 课程笔记</button>' : "") +
        "</div>" +
        '<div class="aiw-foot"><textarea id="aiw-input" placeholder="输入问题，Enter 发送 · Shift+Enter 换行"></textarea>' +
        '<button class="aiw-send" id="aiw-send" type="button" title="发送">' + SEND + "</button></div>" +
      "</div>";
    document.body.appendChild(panel);
    applySize();
    addResize(panel);
    bodyEl = panel.querySelector("#aiw-body");
    inputEl = panel.querySelector("#aiw-input");
    sendEl = panel.querySelector("#aiw-send");
    statusDot = panel.querySelector("#aiw-dot");
    statusTxt = panel.querySelector("#aiw-dot-t");
    refreshStatus();
    panel.querySelector('[data-act="close"]').addEventListener("click", closePanel);
    panel.querySelector('[data-act="cfg"]').addEventListener("click", function () { openConfig(); });
    panel.querySelector('[data-act="notes"]').addEventListener("click", function () { openNotes(); });
    panel.querySelectorAll("[data-qb]").forEach(function (el) {
      el.addEventListener("click", function () {
        var k = el.getAttribute("data-qb");
        if (k === "notes") openNotes();
        else if (k === "qa") scrollToQa();
        else scrollToNote();
      });
    });
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
        '<br>右上角 ⚙ 可随时配置你的大模型。</div>' +
        '<div class="aiw-hint"><span class="aiw-link" id="aiw-open-notes">📖 查看我的问答笔记</span></div>';
      bodyEl.querySelector("#aiw-open-notes").addEventListener("click", openNotes);
      refreshBadge();
    } else {
      var lastQ = "";
      HISTORY.forEach(function (m) {
        if (m.role === "user") { lastQ = m.content; bubble("u", m.content); }
        else bubble("b", m.content, false, lastQ);
      });
      bodyEl.scrollTop = bodyEl.scrollHeight;
    }
    inputEl.focus();
  }

  function closePanel() {
    if (panel) { panel.remove(); panel = null; cfgEl = null; noteEl = null; }
    statusDot = statusTxt = null;
  }

  ball.addEventListener("click", function () {
    if (panel) closePanel(); else openPanel();
  });

  /* ---------------- 气泡与发送 ---------------- */
  /* 与 app.js 相同的设备 uid（课程笔记按设备存储） */
  function lsUid() {
    var u = localStorage.getItem("icl.uid");
    if (!u) {
      u = "u" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
      localStorage.setItem("icl.uid", u);
    }
    return u;
  }

  /* 把 AI 问答追加写入当前课程的「课程笔记」 */
  function appendLessonNote(lesson, q, a) {
    var uid = lsUid();
    return fetch("/api/notes/" + uid + "/" + lesson, { credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (d) { return (d && d.body) || ""; })
      .catch(function () { return ""; })
      .then(function (body) {
        var d = new Date();
        var p = function (n) { return (n < 10 ? "0" : "") + n; };
        var stamp = (d.getMonth() + 1) + "-" + p(d.getDate()) + " " + p(d.getHours()) + ":" + p(d.getMinutes());
        var nb = (body ? body.replace(/\s+$/, "") : "") +
          "\n\n—— AI 问答 · " + stamp + "\n【问】" + q + "\n【答】" + a + "\n";
        return fetch("/api/notes", {
          method: "PUT",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ uid: uid, lesson: lesson, body: nb })
        }).then(function (r) {
          if (!r.ok) return false;
          try { localStorage.setItem("icl.note." + lesson, nb); } catch (e) {}
          /* 页面底部笔记框若是打开状态，实时同步 */
          var box = document.getElementById("note-box");
          if (box) box.value = nb;
          var st = document.getElementById("note-state");
          if (st) st.textContent = "AI 问答已写入课程笔记";
          return true;
        }).catch(function () { return false; });
      });
  }

  /* 课程页：问答自动存档 + 写入课程笔记 */
  function autoSaveQA(q, a) {
    var lesson = document.body.dataset.lesson || "";
    var archP = fetch("/api/ai/notes", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, answer: a, lesson: lesson }),
    }).then(function (r) { return r.ok; }).catch(function () { return false; });
    Promise.all([archP, appendLessonNote(lesson, q, a)])
      .then(function (rs) {
        if (rs[0] === true && rs[1] === true) {
          var hint = document.createElement("div");
          hint.className = "aiw-hint";
          hint.innerHTML = '✅ 已自动存入本课 · <span class="aiw-link" data-goto-qa>🤖 本课 AI 问答</span>（页面底部，点击展开）';
          bodyEl.appendChild(hint);
          bodyEl.scrollTop = bodyEl.scrollHeight;
          hint.querySelector("[data-goto-qa]").addEventListener("click", scrollToQa);
          refreshBadge();
          refreshLessonQa();
        } else {
          var warn = document.createElement("div");
          warn.className = "aiw-hint";
          warn.textContent = "⚠️ 自动保存课程笔记失败（笔记内容仍在会话中，可手动复制）";
          bodyEl.appendChild(warn);
          bodyEl.scrollTop = bodyEl.scrollHeight;
        }
      })
      .catch(function () {});
  }

  /* AI 回答下方的小操作条：复制 /（非课程页）保存为笔记 */
  function addActs(row, q, a) {
    var lesson = (document.body.dataset && document.body.dataset.lesson) || "";
    var acts = document.createElement("div");
    acts.className = "aiw-acts";
    acts.innerHTML =
      '<button type="button" data-act="copy">' + COPY + " 复制</button>" +
      (lesson ? "" : '<button type="button" data-act="save">' + BOOKMARK + " 保存为笔记</button>");
    row.parentNode.insertBefore(acts, row.nextSibling);
    var copyBtn = acts.querySelector('[data-act="copy"]');
    var saveBtn = acts.querySelector('[data-act="save"]');
    copyBtn.addEventListener("click", function () {
      var text = "问：" + q + "\n\n答：" + a + "\n\n—— 来自 ic.feice.net AI 助手";
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          copyBtn.innerHTML = COPY + " 已复制";
          setTimeout(function () { copyBtn.innerHTML = COPY + " 复制"; }, 1800);
        }).catch(function () {});
      }
    });
    if (!saveBtn) return;
    saveBtn.addEventListener("click", function () {
      saveBtn.disabled = true;
      saveBtn.innerHTML = BOOKMARK + " 保存中…";
      fetch("/api/ai/notes", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, answer: a, lesson: lesson }),
      })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (res) {
          if (res.ok) {
            saveBtn.innerHTML = BOOKMARK + " 已保存";
            var hint = document.createElement("div");
            hint.className = "aiw-hint";
            hint.innerHTML = "✅ 已存入问答归档；打开对应课程页提问，问答会自动写入该课的「课程笔记」";
            bodyEl.appendChild(hint);
            bodyEl.scrollTop = bodyEl.scrollHeight;
            refreshBadge();
          } else {
            failSave();
          }
        })
        .catch(failSave);
      function failSave() {
        saveBtn.disabled = false;
        saveBtn.classList.add("fail");
        saveBtn.innerHTML = BOOKMARK + " 保存失败";
        setTimeout(function () {
          saveBtn.classList.remove("fail");
          saveBtn.innerHTML = BOOKMARK + " 保存为笔记";
        }, 2200);
      }
    });
  }

  /* ---------------- 轻量 Markdown 渲染（安全：先转义再生成标签） ---------------- */
  /* LaTeX 命令 → 符号/文本 对照表（覆盖常见数学符号、箭头、希腊字母、函数名） */
  var LATEX_SYM = {
    /* 箭头 */
    rightarrow: "→", longrightarrow: "→", to: "→", leftarrow: "←", longleftarrow: "←",
    leftrightarrow: "↔", longleftrightarrow: "↔", Rightarrow: "⇒", longRightarrow: "⇒",
    Leftarrow: "⇐", Longleftarrow: "⇐", Leftrightarrow: "⇔", Longleftrightarrow: "⇔",
    mapsto: "↦", uparrow: "↑", downarrow: "↓", nearrow: "↗", searrow: "↘",
    /* 二元运算与关系 */
    div: "÷", times: "×", cdot: "·", ast: "∗", star: "★", circ: "∘", bullet: "•",
    pm: "±", mp: "∓", leq: "≤", le: "≤", geq: "≥", ge: "≥", neq: "≠", ne: "≠",
    approx: "≈", sim: "∼", simeq: "≃", equiv: "≡", propto: "∝", cong: "≅",
    ll: "≪", gg: "≫", asymp: "≍",
    /* 集合与逻辑 */
    in: "∈", notin: "∉", ni: "∋", subset: "⊂", subseteq: "⊆", supset: "⊃", supseteq: "⊇",
    cup: "∪", cap: "∩", emptyset: "∅", varnothing: "∅", forall: "∀", exists: "∃",
    nexists: "∄", neg: "¬", lnot: "¬", land: "∧", lor: "∨",
    /* 其它数学符号 */
    infty: "∞", partial: "∂", nabla: "∇", sum: "Σ", prod: "∏", coprod: "∐", int: "∫",
    oint: "∮", surd: "√", perp: "⊥", parallel: "∥", angle: "∠", triangle: "△",
    square: "□", langle: "⟨", rangle: "⟩", lbrace: "{", rbrace: "}", lbrack: "[", rbrack: "]",
    cdots: "⋯", ldots: "…", dots: "…", vdots: "⋮", ddots: "⋱", dotsb: "…", dotsc: "…",
    prime: "′", degree: "°", ell: "ℓ", hbar: "ℏ", aleph: "ℵ", wp: "℘", Re: "ℜ", Im: "ℑ",
    quad: " ", qquad: "  ", displaystyle: "", limits: "", nolimits: "",
    /* 希腊字母 */
    alpha: "α", beta: "β", gamma: "γ", delta: "δ", epsilon: "ε", varepsilon: "ε",
    zeta: "ζ", eta: "η", theta: "θ", vartheta: "ϑ", iota: "ι", kappa: "κ",
    lambda: "λ", mu: "μ", nu: "ν", xi: "ξ", pi: "π", rho: "ρ", sigma: "σ",
    varsigma: "ς", tau: "τ", upsilon: "υ", phi: "φ", varphi: "φ", chi: "χ",
    psi: "ψ", omega: "ω", digamma: "ϝ",
    Gamma: "Γ", Delta: "Δ", Theta: "Θ", Lambda: "Λ", Xi: "Ξ", Pi: "Π",
    Sigma: "Σ", Upsilon: "Υ", Phi: "Φ", Psi: "Ψ", Omega: "Ω",
    /* 函数名（去反斜杠即为正体写法） */
    log: "log", ln: "ln", lg: "lg", exp: "exp", sin: "sin", cos: "cos", tan: "tan",
    cot: "cot", sec: "sec", csc: "csc", arcsin: "arcsin", arccos: "arccos",
    arctan: "arctan", sinh: "sinh", cosh: "cosh", tanh: "tanh", max: "max",
    min: "min", sup: "sup", inf: "inf", lim: "lim", det: "det", gcd: "gcd",
    dim: "dim", ker: "ker", deg: "deg", hom: "Hom"
  };

  /* LaTeX → 可读文本：带参数命令 → 括注/加粗，裸命令查表，未知命令去反斜杠 */
  function latexCmds(t) {
    var rep = [
      /* 字体/强调命令 */
      [/\\mathbf\s*\{([^{}]*)\}/g, "<b>$1</b>"],
      [/\\boldsymbol\s*\{([^{}]*)\}/g, "<b>$1</b>"],
      [/\\bm\s*\{([^{}]*)\}/g, "<b>$1</b>"],
      [/\\mathbb\s*\{([^{}]*)\}/g, "$1"],
      [/\\mathcal\s*\{([^{}]*)\}/g, "$1"],
      [/\\mathfrak\s*\{([^{}]*)\}/g, "$1"],
      [/\\mathit\s*\{([^{}]*)\}/g, "$1"],
      [/\\mathsf\s*\{([^{}]*)\}/g, "$1"],
      [/\\mathtt\s*\{([^{}]*)\}/g, "$1"],
      [/\\text\s*\{([^{}]*)\}/g, "$1"],
      [/\\textrm\s*\{([^{}]*)\}/g, "$1"],
      [/\\textbf\s*\{([^{}]*)\}/g, "<b>$1</b>"],
      [/\\texttt\s*\{([^{}]*)\}/g, "$1"],
      [/\\mathrm\s*\{([^{}]*)\}/g, "$1"],
      /* 装饰符号（组合字符） */
      [/\\overline\s*\{([^{}]*)\}/g, "$1\u0305"],
      [/\\bar\s*\{([^{}]*)\}/g, "$1\u0304"],
      [/\\hat\s*\{([^{}]*)\}/g, "$1\u0302"],
      [/\\tilde\s*\{([^{}]*)\}/g, "$1\u0303"],
      [/\\widehat\s*\{([^{}]*)\}/g, "$1\u0302"],
      [/\\widetilde\s*\{([^{}]*)\}/g, "$1\u0303"],
      [/\\vec\s*\{([^{}]*)\}/g, "$1\u20D7"],
      [/\\dot\s*\{([^{}]*)\}/g, "$1\u0307"],
      [/\\ddot\s*\{([^{}]*)\}/g, "$1\u0308"],
      /* 根号与分式 */
      [/\\sqrt\s*\[([^\]]*)\]\s*\{([^{}]*)\}/g, "√$1($2)"],
      [/\\sqrt\s*\{([^{}]*)\}/g, "√($1)"],
      [/\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}/g, "($1)/($2)"],
      [/\\dfrac\s*\{([^{}]+)\}\s*\{([^{}]+)\}/g, "($1)/($2)"],
      [/\\tfrac\s*\{([^{}]+)\}\s*\{([^{}]+)\}/g, "($1)/($2)"],
      [/\\tfrac|\\dfrac/g, ""],
      /* 上下标里的 °（度） */
      [/\^\{\\circ\}/g, "°"],
      [/\^\\circ\b/g, "°"],
      /* 定界符命令与空隙（负向断言防止吞掉 \rightarrow 等长命令的前缀） */
      [/\\left(?![A-Za-z])\s*/g, ""],
      [/\\right(?![A-Za-z])\s*/g, ""],
      [/\\[,;!]/g, " "],
      [/\\\{/g, "{"],
      [/\\\}/g, "}"],
      [/\\%/g, "%"], [/\\\$/g, "$"], [/\\#/g, "#"], [/\\_/g, "_"]
    ];
    rep.forEach(function (r) { t = t.replace(r[0], r[1]); });
    /* 裸命令查表；未知命令去掉反斜杠原样保留 */
    t = t.replace(/\\([A-Za-z]+)/g, function (m, name) {
      return LATEX_SYM.hasOwnProperty(name) ? LATEX_SYM[name] : name;
    });
    return t;
  }

  /* 符号与文本类 LaTeX 命令（可用于全局兜底） */
  function mdSym(t) {
    return latexCmds(t);
  }

  /* 数学片段：符号 + 上下标 + 残余花括号清理 */
  function mdTex(t) {
    /* 先把 _\text{xx} / ^\text{xx} 合并成 _{xx} / ^{xx}，避免括号丢失 */
    t = t.replace(/(_|\^)\s*(?:\\text|\\mathrm|\\mathbf)\{([^{}]+)\}/g, "$1{$2}");
    t = latexCmds(t);
    var rep = [
      [/_\{([^{}]+)\}/g, "<sub>$1</sub>"],
      [/_([A-Za-z0-9])\b/g, "<sub>$1</sub>"],
      [/\^\{([^{}]+)\}/g, "<sup>$1</sup>"],
      [/\^(-?[A-Za-z0-9]+)\b/g, "<sup>$1</sup>"]
    ];
    rep.forEach(function (r) { t = t.replace(r[0], r[1]); });
    /* 数学片段内残余的花括号清理 */
    t = t.replace(/[{}]/g, "");
    return t;
  }

  function mdInline(s) {
    return s
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>")
      .replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener">$1</a>');
  }

  function mdToHtml(src) {
    var s = String(src).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    var codes = [], inls = [];
    s = s.replace(/```[a-zA-Z0-9_+-]*\r?\n?([\s\S]*?)```/g, function (m, c) {
      codes.push(c.replace(/\n$/, ""));
      return "\u0000C" + (codes.length - 1) + "\u0000";
    });
    s = s.replace(/`([^`\n]+)`/g, function (m, c) {
      inls.push(c);
      return "\u0000I" + (inls.length - 1) + "\u0000";
    });
    /* 数学：$...$ 与 \( ... \) 先按行内公式转换 */
    s = s.replace(/\$\$([^$]+)\$\$/g, "\u0000M$1\u0000M");   // 块级公式先按行内处理
    s = s.replace(/\u0000M([^M]+)\u0000M/g, function (m, t) { return mdTex(t); });
    s = s.replace(/\$([^$\n]+)\$/g, function (m, t) { return mdTex(t); });
    s = s.replace(/\\\((.+?)\\\)/g, function (m, t) { return mdTex(t); });
    /* 兜底：未包 $ 的裸 LaTeX 命令也转换（不含上下标，避免误伤正文下划线） */
    s = mdSym(s);
    /* 行内语法 */
    s = mdInline(s);
    /* 块级结构 */
    var out = [], list = null, buf = [];
    function closeList() { if (list) { out.push("</" + list + ">"); list = null; } }
    function flushBuf() {
      if (buf.length) { out.push('<div class="aiw-p">' + buf.join("<br>") + "</div>"); buf = []; }
    }
    s.split(/\r?\n/).forEach(function (line) {
      var m;
      if (/^\s*$/.test(line)) { flushBuf(); closeList(); return; }
      if ((m = line.match(/^\u0000C(\d+)\u0000\s*$/))) {
        flushBuf(); closeList();
        out.push("<pre><code>" + codes[+m[1]] + "</code></pre>");
        return;
      }
      if ((m = line.match(/^\s{0,3}#{1,4}\s+(.+?)\s*#*\s*$/))) {
        flushBuf(); closeList();
        out.push('<div class="aiw-h">' + m[1] + "</div>");
        return;
      }
      if ((m = line.match(/^\s*[-*•]\s+(.+)$/))) {
        flushBuf();
        if (list !== "ul") { closeList(); out.push("<ul>"); list = "ul"; }
        out.push("<li>" + m[1] + "</li>");
        return;
      }
      if ((m = line.match(/^\s*\d+[.)]\s+(.+)$/))) {
        flushBuf();
        if (list !== "ol") { closeList(); out.push("<ol>"); list = "ol"; }
        out.push("<li>" + m[1] + "</li>");
        return;
      }
      closeList();
      buf.push(line);
    });
    flushBuf(); closeList();
    var html = out.join("");
    /* 恢复代码占位 */
    html = html.replace(/\u0000I(\d+)\u0000/g, function (m, i) {
      return "<code>" + inls[+i] + "</code>";
    });
    html = html.replace(/\u0000C(\d+)\u0000/g, function (m, i) {
      return "<pre><code>" + codes[+i] + "</code></pre>";
    });
    return html;
  }

  function bubble(kind, text, isErr, q) {
    var row = document.createElement("div");
    row.className = "aiw-row " + kind;
    if (kind === "b") row.innerHTML = '<div class="aiw-mava">' + ROBOT + "</div>";
    var d = document.createElement("div");
    d.className = "aiw-msg" + (isErr ? " err" : "");
    if (kind === "b" && !isErr) d.innerHTML = mdToHtml(text);   // AI 回答渲染 Markdown
    else d.textContent = text;
    row.appendChild(d);
    bodyEl.appendChild(row);
    if (kind === "b" && !isErr && q) addActs(row, q, text);
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
        bubble("b", res.j.reply, false, q);
        if (document.body.dataset && document.body.dataset.lesson) {
          autoSaveQA(q, res.j.reply);   // 课程页：自动存入本课 AI 问答 + 课程笔记
        }
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

  /* ---------------- 初始化：课程页注入问答块 + 探测是否已配置 ---------------- */
  initLessonQa();

  fetch("/api/ai/settings", { credentials: "same-origin" })
    .then(function (r) { return r.json(); })
    .then(function (s) { configured = !!s.configured; refreshStatus(); })
    .catch(function () { configured = false; });
})();
