// 计时规则真实回归（隔离副本，阈值已缩到 4 秒以便快速验证）。
// 用 CDP 驱动无头 Chrome，三个场景各自断言累计秒数。
//
// 用法：node tools/check_study_timer_e2e.js <cdpPort> <pageUrl>

const PORT = process.argv[2] || '9333';
const URL = process.argv[3] || 'http://127.0.0.1:8788/lesson/03-05-floorplan/index.html';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let fails = [];

function check(name, cond, detail) {
  if (cond) console.log('  ok   ' + name);
  else { fails.push(name + ' ' + (detail || '')); console.log('  FAIL ' + name + ' ' + (detail || '')); }
}

async function pageWs() {
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  const p = list.find((t) => t.type === 'page');
  if (!p) throw new Error('no page target');
  return p.webSocketDebuggerUrl;
}

class CDP {
  constructor(ws) {
    this.ws = ws; this.id = 0; this.wait = new Map();
    ws.onmessage = (e) => {
      const m = JSON.parse(e.data);
      if (m.id && this.wait.has(m.id)) {
        const { res, rej } = this.wait.get(m.id); this.wait.delete(m.id);
        m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result);
      }
    };
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((res, rej) => { this.wait.set(id, { res, rej }); this.ws.send(JSON.stringify({ id, method, params })); });
  }
  async ev(expr) {
    const r = await this.send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 200));
    return r.result.value;
  }
}


// 真实输入：CDP 派发的事件 isTrusted=true，与用户操作等价。
// 合成事件（dispatchEvent）会被页面的 isTrusted 校验过滤掉，不能用来测。
async function realScroll(cdp) {
  await cdp.send('Input.dispatchMouseEvent', {
    type: 'mouseWheel', x: 400, y: 400, deltaX: 0, deltaY: 120,
  }).catch(() => {});
}
async function realMove(cdp, x, y) {
  await cdp.send('Input.dispatchMouseEvent', {
    type: 'mouseMoved', x, y, buttons: 0,
  }).catch(() => {});
}

// 让页面获得焦点：无头模式下 hasFocus 默认为 true，这里只确保不隐藏
async function load(cdp) {
  await cdp.send('Page.navigate', { url: URL });
  await sleep(2200);
  const ok = await cdp.ev('typeof window.__acc === "function"');
  // 清零累计量，后续断言只看「场景内新增」，避免把加载等待算进去
  if (ok && typeof (await cdp.ev('typeof window.__reset')) === 'string') {
    await cdp.ev('window.__reset && window.__reset()');
  }
  return ok;
}

(async () => {
  const ws = new WebSocket(await pageWs());
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = () => j(new Error('cdp fail')); });
  const cdp = new CDP(ws);
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  // 无头浏览器默认 hidden 且无焦点，会让计时器一直处于「不在前台」。
  // 打开焦点模拟并把页面置前，才等价于用户真的在看着这一页。
  await cdp.send('Emulation.setFocusEmulationEnabled', { enabled: true }).catch(() => {});
  await cdp.send('Page.bringToFront').catch(() => {});

  console.log('阈值已缩到 4 秒（测试副本），下列时间为真实秒数。\n');

  // ---------- 场景 A：前台 + 持续无操作 ----------
  console.log('场景 A：前台静置 10 秒，空闲阈值 4 秒');
  if (!(await load(cdp))) { console.log('  !! 页面未暴露 __acc，跳过'); }
  else {
    await sleep(10000);
    const acc = await cdp.ev('window.__acc()');
    const sec = acc / 1000;
    check('无操作时只累计到阈值附近', sec >= 3.0 && sec <= 5.5, `实际 ${sec.toFixed(2)}s`);
    const txt = await cdp.ev(`document.getElementById('lp-time').textContent`);
    check('状态提示显示「10 分钟无操作」类文案', /无操作|暂停/.test(txt), txt);
  }

  // ---------- 场景 B：前台 + 每 2 秒滚动一次 ----------
  console.log('\n场景 B：前台持续操作 10 秒（每 2 秒滚一次）');
  await load(cdp);
  for (let i = 0; i < 5; i++) {
    await realScroll(cdp);
    await sleep(2000);
  }
  const accB = await cdp.ev('window.__acc()') / 1000;
  check('持续操作时接近全程累计', accB >= 9.0 && accB <= 12.0, `实际 ${accB.toFixed(2)}s`);

  // ---------- 场景 C：静置超阈值后，恢复操作继续 ----------
  console.log('\n场景 C：静置 8 秒（超阈值）后再滚动，检查是否从恢复点继续');
  await load(cdp);
  await sleep(8000);
  const accIdle = await cdp.ev('window.__acc()') / 1000;
  await realMove(cdp, 300 + Math.random() * 100, 300);         // 恢复：真实鼠标移动
  await realScroll(cdp);
  await sleep(3000);                                            // 恢复后继续 3 秒
  const accResume = await cdp.ev('window.__acc()') / 1000;
  const gained = accResume - accIdle;
  check('恢复操作后重新开始累计', gained >= 2.0 && gained <= 4.5, `恢复后新增 ${gained.toFixed(2)}s`);
  check('静置期间没有补算空档', accIdle <= 5.5, `静置期累计 ${accIdle.toFixed(2)}s`);

  // ---------- 场景 D：tab 隐藏立刻停 ----------
  console.log('\n场景 D：切走 tab（隐藏）12 秒，应完全不累计');
  await load(cdp);
  // 直接模拟「窗口失焦」：blur 事件 + hasFocus 返回 false，
  // 这是 user 说的「鼠标句柄不在课程内容」的场景。
  await cdp.send('Emulation.setFocusEmulationEnabled', { enabled: false }).catch(() => {});
  await cdp.ev('window.dispatchEvent(new Event("blur"))');
  const accBefore = await cdp.ev('window.__acc()');
  await sleep(6000);
  const accMid = await cdp.ev('window.__acc()');
  const grow = (accMid - accBefore) / 1000;
  check('失焦期间不再累计', grow <= 1.0, `实际增长 ${grow.toFixed(2)}s`);

  // 恢复焦点后应继续。注意不能用合成 focus 事件：页面用 hasFocus()
  // 重新判定，合成事件里 hasFocus 仍为 false。要真的开焦点模拟 + 置前，
  // 再发一次真实鼠标移动，等价于用户点回这个窗口。
  await cdp.send('Emulation.setFocusEmulationEnabled', { enabled: true }).catch(() => {});
  await cdp.send('Page.bringToFront').catch(() => {});
  await sleep(300);
  await realMove(cdp, 420, 320);
  const accResume0 = await cdp.ev('window.__acc()');
  await sleep(3000);
  await realMove(cdp, 440, 340);
  const accEnd = await cdp.ev('window.__acc()');
  const back = (accEnd - accResume0) / 1000;
  check('回焦后继续累计', back >= 2.0, `恢复后新增 ${back.toFixed(2)}s`);

  console.log('\n' + (fails.length ? 'FAILED:\n - ' + fails.join('\n - ') : '全部场景通过'));
  ws.close();
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error('FAIL', e.message); process.exit(1); });