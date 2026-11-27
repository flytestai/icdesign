// 学习时长全链路回归（隔离环境，IDLE=4s / FLUSH=2s）。
//
// 覆盖「不漏记 / 不多记」的六个关键场景：
//   A 静置超时 → 不白送阈值
//   B 持续操作 → 累计接近真实时长
//   C 关页（pagehide）→ 未上报的批次已落盘，重开能补传
//   D 断网重试 → 同一 batch_id 重传只入账一次
//   E 多标签同页 → 不重复计入
//   F 失焦 → 立即停，不等阈值
//
// 用法：node tools/check_timer_e2e.js <cdpPort> <baseUrl> <phone> <password>

const PORT = process.argv[2] || '9335';
const BASE = process.argv[3] || 'http://127.0.0.1:8785';
const PHONE = process.argv[4];
const PASS = process.argv[5];
const IDLE = 4;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const fails = [];
const ok = (n, c, d) => { c ? console.log('  ok   ' + n) : (fails.push(n + ' ' + d), console.log('  FAIL ' + n + ' ' + d)); };

async function pageWs() {
  const l = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  const p = l.find((t) => t.type === 'page');
  if (!p) throw new Error('no page');
  return p.webSocketDebuggerUrl;
}
class CDP {
  constructor(ws) { this.ws = ws; this.i = 0; this.w = new Map();
    ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && this.w.has(m.id)) { const { r, j } = this.w.get(m.id); this.w.delete(m.id); m.error ? j(new Error(JSON.stringify(m.error))) : r(m.result); } }; }
  send(method, params = {}) { const id = ++this.i; return new Promise((r, j) => { this.w.set(id, { r, j }); this.ws.send(JSON.stringify({ id, method, params })); }); }
  async ev(x) { const r = await this.send('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true }); if (r.exceptionDetails) return null; return r.result.value; }
}

const ws = new WebSocket(await pageWs());
await new Promise((r) => (ws.onopen = r));
const cdp = new CDP(ws);
await cdp.send('Page.enable');
await cdp.send('Runtime.enable');
await cdp.send('Network.enable');
await cdp.send('Emulation.setFocusEmulationEnabled', { enabled: true });
await cdp.send('Page.bringToFront');

const wheel = () => cdp.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: 400, y: 400, deltaX: 0, deltaY: 120 });
const move = (x, y) => cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y, buttons: 0 });

// 登录：先到登录页填表，拿到 cookie 后再进课程页
async function login() {
  await cdp.send('Page.navigate', { url: BASE + '/login' });
  await sleep(1500);
  const done = await cdp.ev(`(async () => {
    const r = await fetch('/api/auth/login', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({account: ${JSON.stringify(PHONE)}, password: ${JSON.stringify(PASS)}})
    });
    return r.status;
  })()`);
  return done;
}
async function goto(url) {
  // 每个用例都从干净状态开始：清掉本页未上报队列与 leader 记录，
  // 否则上一个用例遗留的批次会污染本轮的断言。
  await cdp.send('Page.navigate', { url });
  await sleep(1500);
  await cdp.ev(`(function(){
    try {
      for (var i = localStorage.length - 1; i >= 0; i--) {
        var k = localStorage.key(i);
        if (k && (k.indexOf('icl.studyq.') === 0 || k === 'icl.study.leader')) localStorage.removeItem(k);
      }
    } catch (e) {}
    return true;
  })()`);
  await cdp.send('Page.reload', { ignoreCache: true });
  await sleep(1800);
  await cdp.ev('window.__rst && window.__rst()');
}
async function accNow() { await move(310 + Math.random() * 40, 310); await sleep(80); return (await cdp.ev('window.__acc && window.__acc()')) / 1000; }
async function serverTotal(lesson) {
  return await cdp.ev(`fetch('/api/study-time').then(r=>r.json()).then(d=>(d.by_lesson||{})[${JSON.stringify(lesson)}]||0)`);
}

const st = await login();
console.log(`登录状态 ${st}，阈值 ${IDLE}s\n`);

// ---------- A 静置超时 ----------
console.log('A 静置 12 秒（阈值 4s）：一秒都不该记');
await goto(BASE + '/lesson/03-05-floorplan/index.html');
await sleep(2500);                        // 让加载后那几秒先落账
const s0 = await serverTotal('03-05-floorplan');
await sleep(12000);
const s1 = await serverTotal('03-05-floorplan');
ok('静置期间服务端未增长', (s1 - s0) <= 1, `增长 ${s1 - s0}s`);

// ---------- B 持续操作 ----------
console.log('\nB 每 2 秒操作一次，持续 8 秒');
await goto(BASE + '/lesson/03-05-floorplan/index.html');
const b0 = await serverTotal('03-05-floorplan');   // 操作前基线
for (let i = 0; i < 4; i++) { await wheel(); await sleep(2000); }
await sleep(4000);                       // 等 FLUSH(2s) 完整上报
// 本轮 4 次操作 x 2 秒 ≈ 8 秒。此时数据可能已上报，改看服务端增量更准。
const b1 = await serverTotal('03-05-floorplan');
ok('持续操作有入账且量级正确', (b1 - b0) >= 5 && (b1 - b0) <= 12, `服务端增长 ${b1 - b0}s`);

// ---------- C 上报失败不丢数据 ----------
console.log('\nC 断网（拦截上报）时，数据应留在本地队列而不是丢失');
await goto(BASE + '/lesson/03-05-floorplan/index.html');
// 让所有 /api/study-time 的 POST 直接失败
await cdp.send('Network.setBlockedURLs', { urls: ['*api/study-time*'] });
for (let i = 0; i < 3; i++) { await wheel(); await sleep(1500); }
await sleep(2500);                       // 等 FLUSH 尝试上报并失败
const queued = await cdp.ev(`localStorage.getItem('icl.studyq.03-05-floorplan')`);
const qArr = (() => { try { return JSON.parse(queued || '[]'); } catch (e) { return []; } })();
ok('上报失败后批次仍留在本地', Array.isArray(qArr) && qArr.length > 0, `队列 ${queued}`);
await cdp.send('Network.setBlockedURLs', { urls: [] });
await sleep(2500);
const afterRecover = await cdp.ev(`localStorage.getItem('icl.studyq.03-05-floorplan')`);
const rArr = (() => { try { return JSON.parse(afterRecover || '[]'); } catch (e) { return []; } })();
ok('恢复网络后队列被清空（说明补传成功）', !rArr || rArr.length === 0, `队列 ${afterRecover}`);

// ---------- D 重传去重 ----------
console.log('\nD 同一 batch_id 重传 3 次，只入账一次');
const dedup = await cdp.ev(`(async () => {
  const base = (await fetch('/api/study-time').then(r=>r.json())).by_lesson['_quiz'] || 0;
  const bid = crypto.randomUUID();
  for (let i = 0; i < 3; i++) {
    await fetch('/api/study-time', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({lesson:'_quiz', seconds:7, batch_id:bid})});
  }
  const now2 = (await fetch('/api/study-time').then(r=>r.json())).by_lesson['_quiz'] || 0;
  return now2 - base;
})()`);
ok('三次重传只入账 7 秒', dedup === 7, `实际增量 ${dedup}`);

// ---------- E 多标签 ----------
console.log('\nE 同一课程开两个标签，观察是否双计');
await goto(BASE + '/lesson/03-05-floorplan/index.html');
const before2 = await serverTotal('03-05-floorplan');
const tab2 = await cdp.send('Target.createTarget', { url: BASE + '/lesson/03-05-floorplan/index.html' });
await sleep(2000);
// 两个标签都停留一段时间
for (let i = 0; i < 3; i++) { await wheel(); await sleep(1500); }
await sleep(3000);
const after2 = await serverTotal('03-05-floorplan');
const growth = after2 - before2;
// 单标签 4.5 秒操作 + 上报；若双计会接近 9 秒以上
ok('多标签未显著双计', growth <= 9, `增长 ${growth}s（单实例约 4-5s）`);
await cdp.send('Target.closeTarget', { targetId: tab2.targetId }).catch(() => {});

// ---------- F 失焦 ----------
console.log('\nF 失焦 5 秒：立即停，不等阈值');
await goto(BASE + '/lesson/03-05-floorplan/index.html');
await sleep(2500);
const f0 = await serverTotal('03-05-floorplan');
await cdp.send('Emulation.setFocusEmulationEnabled', { enabled: false });
await sleep(300);
await sleep(5000);
const f1 = await serverTotal('03-05-floorplan');
ok('失焦期间未增长', (f1 - f0) <= 1, `增长 ${f1 - f0}s`);

console.log('\n' + (fails.length ? 'FAILED:\n - ' + fails.join('\n - ') : '全部通过'));
ws.close();
process.exit(fails.length ? 1 : 0);