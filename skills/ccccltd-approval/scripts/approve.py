import time
import json

"""中交财务云报销单审批批量工具（ccccltd-approval skill）。
用法（browser_exec code 里，jsfn 传预置的 js 函数）：
  submit_only('孙鑫', js)            # 规则0: 直接提交
  approve_pass('刘世杰', js)          # 规则1: 通过→黄仁兵
  approve_pass('刘世杰', '黄仁兵', js)
  transfer('罗荣强', '徐敬恩', js)     # 规则2: 移交→徐敬恩
  transfer('王振', '刘语', js)         # 规则3: 移交→刘语
"""

def _in_task_form(fn, jsfn):
    return jsfn(f"""
(() => {{ const frames = Array.from(document.querySelectorAll('iframe'));
  const f = frames.find(x => (x.src||'').includes('task-form'));
  if (!f) return 'NO_TASK_FORM';
  const d = f.contentDocument;
  {fn}
}})()
""")

def open_ticket(summary_keyword, jsfn):
    clicked = jsfn("""
(() => {
  const f = document.querySelector('iframe');
  const d = f.contentDocument;
  const kw = %s;
  const cands = Array.from(d.querySelectorAll('div, li, tr')).filter(e => {
    const t = e.textContent || '';
    return t.includes('的通用报销单') && t.includes(kw) && t.length < 2000;
  });
  cands.sort((a,b) => a.textContent.length - b.textContent.length);
  if (!cands.length) return 'NOT_FOUND';
  const item = cands[0];
  const title = Array.from(item.querySelectorAll('div,span,a,p')).find(e => (e.textContent||'').trim().endsWith('的通用报销单_公有'));
  (title || item).click();
  return 'CLICKED';
})()
""" % json.dumps(summary_keyword, ensure_ascii=False))
    return clicked

def pick_person(name, jsfn):
    """加号 → 弹窗选 name → 确定。返回 {'person':..., 'confirm':...}。"""
    plus = _in_task_form("""
const icon = d.querySelector('i.f-icon-plus-circle');
if (!icon) return 'NO_PLUS';
let tg = icon.parentElement && icon.parentElement.tagName === 'BUTTON' ? icon.parentElement : icon;
tg.click(); return 'PLUS_CLICKED';
""", jsfn)
    if plus != 'PLUS_CLICKED':
        return {'plus': plus}
    time.sleep(4)
    sel = _in_task_form("""
const els = Array.from(d.querySelectorAll('*'));
const p2 = els.find(e => {
  const txt = (e.textContent||'').trim();
  return e.children.length === 0 && txt.includes(%s) && txt.length < 40 && txt.startsWith('[');
});
if (!p2) return 'NO_PERSON';
const radio = p2.closest('lib-select-control') || p2.closest('.custom-control');
if (!radio) return 'NO_RADIO';
const label = radio.querySelector('.custom-control-label') || radio;
const input = radio.querySelector('input');
if (input) input.click();
label.click();
const ctr = Array.from(d.querySelectorAll('*')).find(e => (e.textContent||'').trim().startsWith('已选') && (e.textContent||'').trim().length < 20);
return (p2.textContent||'').trim() + ' => ' + (ctr ? ctr.textContent.trim() : '?');
""" % json.dumps(name, ensure_ascii=False), jsfn)
    time.sleep(2)
    confirm = _in_task_form("""
const btn = Array.from(d.querySelectorAll('input.btn')).find(b => {
  const r = b.getBoundingClientRect();
  return r.width > 0 && ((b.value||'').includes('确定') || (b.value||'').includes('确认'));
});
if (!btn) return 'NO_CONFIRM';
btn.click(); btn.blur(); return 'CONFIRMED';
""", jsfn)
    return {'person': sel, 'confirm': confirm}

def _submit(jsfn):
    return _in_task_form("""
const btn = Array.from(d.querySelectorAll('button, input, a, span')).find(b => {
  const t = (b.textContent||'').trim() || (b.value||'');
  const r = b.getBoundingClientRect();
  return t === '提交' && r.width > 0;
});
if (!btn) return 'NO_SUBMIT';
btn.click(); return 'SUBMITTED';
""", jsfn)

def verify_gone(summary_keyword, jsfn):
    return jsfn("""
(() => {
  const f = document.querySelector('iframe');
  const d = f ? f.contentDocument : null;
  const t = d ? d.body.innerText : '';
  return t.includes(%s) ? 'STILL_PRESENT' : 'GONE';
})()
""" % json.dumps(summary_keyword, ensure_ascii=False))

def submit_only(summary_keyword, jsfn):
    """规则0：打开→直接提交→验证。"""
    r = {'kw': summary_keyword, 'open': open_ticket(summary_keyword, jsfn)}
    if r['open'] != 'CLICKED':
        return r
    time.sleep(6)
    r['submit'] = _submit(jsfn)
    time.sleep(6)
    r['verify'] = verify_gone(summary_keyword, jsfn)
    return r

def approve_pass(summary_keyword, person='黄仁兵', jsfn=None):
    """规则1：通过(默认)→办理人员选 person→提交。"""
    r = {'kw': summary_keyword, 'open': open_ticket(summary_keyword, jsfn)}
    if r['open'] != 'CLICKED':
        return r
    time.sleep(6)
    r['pick'] = pick_person(person, jsfn)
    r['submit'] = _submit(jsfn)
    time.sleep(6)
    r['verify'] = verify_gone(summary_keyword, jsfn)
    return r

def transfer(summary_keyword, person='徐敬恩', jsfn=None):
    """规则2/3：改选「移交」→接受人员选 person→提交。"""
    r = {'kw': summary_keyword, 'open': open_ticket(summary_keyword, jsfn)}
    if r['open'] != 'CLICKED':
        return r
    time.sleep(6)
    r['misyao'] = _in_task_form("""
const els = Array.from(d.querySelectorAll('*')).filter(e => e.children.length === 0 && (e.textContent||'').trim() === '移交');
if (!els.length) return 'NO_MISYAO';
els[0].click(); return 'MISYAO_CLICKED';
""", jsfn)
    time.sleep(2)
    r['pick'] = pick_person(person, jsfn)
    r['submit'] = _submit(jsfn)
    time.sleep(6)
    r['verify'] = verify_gone(summary_keyword, jsfn)
    return r
