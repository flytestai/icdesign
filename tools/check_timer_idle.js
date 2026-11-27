// 计时规则真实回归（阈值缩到 4 秒的隔离副本）。
// 重点断言：超时那段「一秒都不计」，不会白得一个阈值。
//
// 用法：node tools/check_timer_idle.js <cdpPort> <baseUrl>

const PORT = process.argv[2] || '9334';
const BASE = process.argv[3] || 'http://127.0.0.1:8787';
const IDLE = 4;                     // 秒，与测试副本一致
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const fails = [];
const ok = (n, c, d) => { c ? console.log('  ok   ' + n) : (fails.push(n + ' ' + d), console.log('  FAIL ' + n + ' ' + d)); };

async function target() {
  const l = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  return l.find((t) => t.type === 'page').webSocketDebuggerUrl;
}
class CDP {
  constructor(ws) { this.ws = ws; this.i = 0; this.w = new Map();
    ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && this.w.has(m.id)) { const { r } = this.w.get(m.id); this.w.delete(m.id); r(m.result); } }; }
  send(method, params = {}) { const id = ++this.i; return new Promise((r) => { this.w.set(id, { r }); this.ws.send(JSON.stringify({ id, method, params })); }); }
  async ev(x) { const r = await this.send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true }); return r.result.value; }
}
const cdp = new CDP(await (async () => { const ws = new WebSocket(await target()); await new Promise((r) => (ws.onopen = r)); return ws; })());
await cdp.send('Page.enable'); await cdp.send('Runtime.enable');
await cdp.send('Emulation.setFocusEmulationEnabled', { enabled: true });
await cdp.send('Page.bringToFront');

async function goto(url) {
  await cdp.send('Page.navigate', { url });
  await sleep(1800);
  await cdp.ev('window.__reset && window.__reset()');
  // reset 后立刻操作一次，把「最后一次操作」的基线定在此刻；
  // 否则第一次滚动会把 reset 到那次滚动之间的等待也结算进去。
  await move(300, 300);
  await sleep(120);
  await cdp.ev('window.__reset && window.__reset()');
}
const wheel = () => cdp.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: 400, y: 400, deltaX: 0, deltaY: 120 });
const move = (x, y) => cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y, buttons: 0 });
// 读累计前先做一次真实操作：credit 只在操作到来时结算上一段，
// 停止操作后最后一段还悬着，必须再动一下才能读准。
async function accNow() { await move(310 + Math.random() * 40, 310); await sleep(80); return (await cdp.ev('window.__acc()')) / 1000; }

console.log(`阈值 ${IDLE}s（测试副本）。核心断言：超时那段不计入。\n`);

// ---- 1. 关键用例：静置 12 秒（3 倍阈值），累计必须≈0，而不是≈IDLE ----
console.log('用例1：前台静置 12 秒（阈值 4 秒）');
await goto(BASE + '/lesson/03-05-floorplan/index.html');
await sleep(12000);
let acc = await cdp.ev('window.__acc()') / 1000;
ok(`静置 12 秒累计应≈0（不能白送 ${IDLE}s）`, acc <= 1.0, `实际 ${acc.toFixed(2)}s`);
console.log('   → 旧实现这里会得 ~4s，新实现应为 0');

// ---- 2. 正常阅读：每 2 秒操作一次，持续 10 秒 ----
console.log('\n用例2：每 2 秒操作一次，持续 10 秒');
await goto(BASE + '/lesson/03-05-floorplan/index.html');
for (let i = 0; i < 5; i++) { await wheel(); await sleep(2000); }
acc = await accNow();
ok('持续操作时正常累计', acc >= 9 && acc <= 12.5, `实际 ${acc.toFixed(2)}s`);

// ---- 3. 超时后恢复：静置 8 秒再操作，空档不计 ----
console.log('\n用例3：操作 2 秒 → 静置 8 秒 → 再操作');
await goto(BASE + '/lesson/03-05-floorplan/index.html');
await wheel(); await sleep(2000);
const afterFirst = await accNow();
await sleep(8000);                   // 超时空档
const afterGap = await accNow();     // 恢复操作，同时结算
ok('恢复操作不追补空档', afterGap - afterFirst <= 1.5, `空档后多算了 ${(afterGap - afterFirst).toFixed(2)}s`);
ok('超时前的真实阅读被保留', afterFirst >= 1.0, `超时前仅 ${afterFirst.toFixed(2)}s`);

// ---- 4. 失焦立即停，不等阈值 ----
console.log('\n用例4：失焦 5 秒（阈值 4 秒），应完全不计');
await goto(BASE + '/lesson/03-05-floorplan/index.html');
await cdp.send('Emulation.setFocusEmulationEnabled', { enabled: false });
await sleep(300);
const b0 = await cdp.ev('window.__acc()');
await sleep(5000);
const b1 = await cdp.ev('window.__acc()');
ok('失焦期间零增长（不必等 10 分钟）', (b1 - b0) / 1000 <= 0.5, `增长 ${((b1 - b0) / 1000).toFixed(2)}s`);

// ---- 5. 非课程页也计时：题库 ----
console.log('\n用例5：题库页也计学习时长');
await cdp.send('Emulation.setFocusEmulationEnabled', { enabled: true });
await cdp.send('Page.bringToFront');
await goto(BASE + '/quiz/index.html');
const hasTimer = await cdp.ev('!!document.getElementById("lp-time")');
ok('题库页有计时显示', hasTimer === true, String(hasTimer));
for (let i = 0; i < 3; i++) { await wheel(); await sleep(2000); }
const qacc = await accNow();
ok('题库页正常累计', qacc >= 5, `实际 ${qacc}s`);

console.log('\n' + (fails.length ? 'FAILED:\n - ' + fails.join('\n - ') : '全部通过'));
process.exit(fails.length ? 1 : 0);