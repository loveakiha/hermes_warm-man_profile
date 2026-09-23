---
name: ccccltd-approval
description: Use when approving 报销单 in 中交财务云 (ccccnfc). 门户SSO登录与审批点击流程.
---

# 中交财务云报销单审批（ccccnfc）

## 前提
- 用户说已登录；若 `curl http://127.0.0.1:9222/json/version` 不通，**后台**启动调试 Edge（terminal `background=true`——前台命令超时会连 Edge 进程一起杀）：
  `"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --remote-debugging-port=9222 --user-data-dir=C:/Users/18601/.hermes/edge-debug --no-first-run --no-default-browser-check "https://portal.ccccltd.cn/"`
- browser_exec session 固定 `cw`；若报 `PermissionError ... bu-cw.port` → `rm -f ~/.config/browser-harness/runtime/bu-cw.*` 后重试
- 直连 `https://ccccnfc.ccccltd.cn/...` 会弹「用户登录信息已失效」——必须经门户 SSO 入口进
- 登录态持久化在调试 profile；「登录信息已失效」弹窗 → 让用户在调试窗口重新扫码。凭证/cookies 绝不贴进聊天

## 登录入口（每次调试窗口重启后都要走）
1. `goto_url` 门户工作台：`https://sdc.ccccltd.cn/wps/myportal/sdc/cccchome_ywtb/staffwork_x/!ut/p/z1/04_Sj9CPykssy0xPLMnMz0vMAfIjo8zifQ293Q0tTYz8DdxcjAzM3L18PPxNjY3d3U30wwkpiAJKG-AAjgZA_VFgJXAT_A3czQ0Czf2C_E1cjIyDvcygCvCYUZAbYZDpqKgIAMtBAIk!/dz/d5/L2dBISEvZ0FBIS9nQSEh/`
2. `goto_url` 财务云 SSO 票据：`http://sso.ccccltd.cn:7788/sso12c?rd=http%3A%2F%2Fsso.ccccltd.cn%3A8777%2Foamfed%2Fidp%2Finitiatesso%3Fproviderid%3Dhttp%3A%2F%2F4alogin.ccccltd.cn%2Foam%2Ffed%26returnurl%3Dhttp%253A%252F%252F4alogin.ccccltd.cn%252Foauth2%252Frest%252Fauthz%253Fclient_id%253DCCCCLTD_CWY%2526response_type%253Dcode%2526domain%253DCcccltdDomain%2526redirect_uri%253Dhttp%253A%252F%252Fccccnfc.ccccltd.cn%252Fapi%252Fruntime%252Fsys%252Fv1.0%252FrouterRedirect%2526scope%253DCustomerResProfile.Info%2526state%253DsourceSystem%25253DportalOAuth`
3. 落地页标题含「🐴 企业数字化云平台」、右上角显示 许诺 = 成功

## 审批规则（先试提交，被拦再按规则补选）
0. **默认策略：进表单先直接点「提交」**——办理人员有默认人选的单直通成功；成功即下一单，被拦（表单还开着）再按 1-4 补选（用户原话："直接就点提交，成功就下一单，不成功就按我们的规则来"）
1. 摘要含「体检」「健康证」等 → **通过**（默认选中），办理人选 **黄仁兵 [2016153800]**
2. 摘要含「伙食/餐费/餐饮」等 → **移交**，接受人选 **徐敬恩 [2016154656]**
3. 摘要含「培训」字样 → **移交**，接受人选 **刘语 [2019022098]**
4. 其余看业务科目：**职工福利费** → 加号选 **朱情华**；**管理费用** → **申义**
5. 规则未覆盖 → 逐张向用户确认

## 页面结构（同层同源 iframe，无需切 frame）
- 工作台 = `document.querySelector('iframe')`（含「我的待办」）
- 待办项：textContent 以 `XXX的通用报销单_公有` 结尾的 `<div>` → 点击打开审批表单（iframe src 含 `task-form`）
- **task-form iframe 只含审批区（~300 字符），费用分摊/业务科目不在里面**——规则4需要看科目时须从待办列表进单据详情页的「费用分摊」页签「*业务科目」列
- 验证：提交后 task-form iframe 消失 + 待办列表该单消失（`body.innerText` 计数 0）；表单还开着 = 提交被拦

## 审批操作（全在 task-form 的 contentDocument 执行）
- 「通过」默认已选中，无需点
- 「提交」：可见 `<button>`，textContent 精确「提交」且 `getBoundingClientRect().width > 0`
- 改选「移交」：审批操作区 textContent 精确「移交」的叶子元素（通过/驳回/移交/评论 四个平级选项）click
- 选办理人员/接受人员（三步固定套路）：
  1. `i.f-icon-plus-circle` → click（或父 BUTTON）→ 弹「人员选择」modal
  2. modal 里找 textContent 为 `[工号]姓名` 的叶子元素（children=0）→ `.closest('.custom-control')` → 其 `.custom-control-label` click → 出现「已选1人」
  3. modal「确定」是 `<input class="btn btn-primary" value="确定">`（**input 不是 button**，文案在 value 属性）→ click
- 办理人员默认值：`input[name="input-group-value"]` 的 `ng-reflect-model` 属性；占位符「相关职能部门负责人」**不是**真实默认（提交不拦 = 单据自带下一环节人选，直通即可）

## 批量工具
`scripts/approve.py`（随 skill 自带，自动导入；`jsfn` 传 browser_exec 的 `js` 函数）：
- `submit_only(摘要关键字, js)` → 规则0
- `approve_pass(摘要关键字, js)` / `approve_pass(关键字, '黄仁兵', js)` → 规则1
- `transfer(摘要关键字, '徐敬恩'|'刘语', js)` → 规则2/3

## 已知人选
黄仁兵 [2016153800] / 徐敬恩 [2016154656] / 刘语 [2019022098]（工号以「人员选择」弹窗列表为准）
