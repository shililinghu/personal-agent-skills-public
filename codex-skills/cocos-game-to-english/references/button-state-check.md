# 按钮状态轻量核对

涉及按钮交互、透明度/禁用外观、点击区域时使用；范围限本轮受影响共享调用方。局部维护与完整 R06 共用 `scripts/button_state_check.py`，不重跑无关 CI。

## 无响应故障的最短定位

仅在反馈“点了没用”、修改公共点击代码或底部适配时加载；沿用本轮范围和现有检查器。 扩测按[短检查分流](testing-scope-and-stop.md#用短检查决定是否扩测)；触发异常先扩大相关模块，短检通过且本轮必要项已齐即停止，不自动全量。

1. **先核运行版本**：首次输入前读回实际加载的业务 bundle 身份，以及修改函数或控件位置。服务文件、构建成功、新 URL 均不证明运行版本；遇缓存先保留 origin/存档，禁用缓存重载并核实际资源链，不靠反复换 URL 猜。
2. **先做最短对照**：同组有免费、无库存前提的动作（如重开），优先实点。它也失败时，不把全部无效归因于广告或库存；记录一次 `start → end/cancel → handler → 业务前后/拒绝原因/首错`，据断点查输入、遮挡、守卫或异步回调。
3. **核完整点击区域**：按压不缩小命中节点；中心与控件内偏心松手分别观察。底部完整点击矩形须避让目标运行时安全区，缺数据采用有依据的回退；按同帧相机/视口换算，DPR只处理一次。某游戏的44/46px不能直接变成所有设备的固定标准；真实取消不执行业务。
4. **只测受影响分支**：有库存须读回实际消费与棋盘/托盘变化；零库存须核广告成功后的兑现，以及不可用/取消时不发奖、不扣费并恢复操作；免费重开须清空旧局并重新进入可玩。暂停恢复、双比例及公共调用方按本次改动补测，音效、变色、监听和方法替身不能代替结果，不扩无关CI。
5. **校准结论**：同一判据核准确旧版与新字节。区分“复现原手机症状”与“检出布局等确定缺陷”；后者即使修复，也不能证明手机完整根因。Web能用而Native失败时，保留目标运行层待复验，交明确标版的候选，不把推测写成已解决。

**系统打断的缺失终止事件**：仅在公共输入/前后台逻辑改动或恢复后失灵时，补“按住→后台/失焦→不送旧end/cancel→返回→新触点操作”的短反例；旧触点迟到松手不得提交，新触点须能完成业务。触点归属在后台、控件禁用/复用及销毁时清理并核监听注销。正常点暂停再继续不覆盖此条件；方法/受控事件反例与真实系统切换分开记录，不能由前者声称手机唯一根因。先核棋盘一次操作和免费重开，正常则不展开无关广告矩阵。

**减少重复操作**：先看一份紧凑差量（版本、目标、输入阶段、处理器、资源/局状态与首错），详细日志落项目。每个测试页串行控制，禁止另一轮CLI同时重置其视口；每次模拟参数重设后等布局稳定，再从同帧算触点。自然获得的测试库存/进度沿用原origin，提前安排消费顺序，避免因换端口、盲重载或旧代码反复刷资源；只有新改动、失败或疑点才重测。游戏经过与证据留项目，Skill只保留本节规则。

## 计划与检查命令

**机器必核（policy_version 2）**：每份计划必须有 `input_lifecycle` 适用声明，缺失即拒绝。当前游戏存在自定义触点归属时，首次完整输入基线及公共输入/前后台改动、恢复后失灵的局部审查必须覆盖；已有同代码、依赖和检查器版本的有效结果可复用。按实际共用绑定分组，一组跑一次，不乘以关卡数；各受影响业务入口仍需真实结果。声明不适用必须给源码依据；已绑定源码明显含触点归属时，不能仅用文字排除。 完整R06还从实际assets脚本识别常见显式触点归属，要求声明适用并绑定这些源文件，防止只选无关业务文件绕过；该静态清点不是缺陷结论；两处消费者共用随Skill提供的词法/结构识别，注释、说明字符串、正则和未使用名字不算实际owner，首次候选批量解析、相同源码与工具指纹复用。疑似动态输入或不支持语法保留为未解析，不能据此声明没有owner；仍须绑定受影响源码并完成原生命周期证据。

适用组须绑定生产源/编译模块指纹与原始计数轨迹，含 `missing_terminal`、`late_terminal`、`cancel`、`disable_reenable`；新触点有效end之前提交数始终为0，最后恰为1。另引用恢复后的 `browser_touch` 业务case（`input.after_interruption: true`，预期为effect），不能用普通点击、音效、paused=false或全通过标记代替。报告回读重新校验轨迹/源码，旧报告缺项不自动追认为通过。

计划字段：`input_lifecycle: {applicable: true, groups: [{id, controls: [控件ID], trace: {path, sha256}, recovery_cases: [caseID]}]}`；无自定义输入且本轮不涉输入恢复时用 `applicable: false, reason: 具体源码与范围依据`。轨迹JSON：`schema: input-lifecycle-run.v1`、与计划一致的 `business_sources`、实际 `layer`（native_module/isolated_production/browser_touch）、`scenarios`。每场景为有序 `{type, finger, commits}`，finger为old/new或生命周期事件的null。序列分别为：start(old)→hide→show→start(new)→end(new)；start(old)→hide→show→end(old)→start(new)→end(new)；start(old)→cancel(old)→end(old)→start(new)→end(new)；start(old)→disable→enable→end(old)→start(new)→end(new)。commits须由实际生产处理器计数读取，不能从预期生成。

检查器能拒缺项、错误序列、错误结果和陈旧字节，但不能认证记录真实性，也不能穷尽自动识别全部输入实现；人工核对源码调用方与分组仍必需。受控缺事件轨迹不能冒充手机系统原始切换；手机故障未同层复现时不得写已彻底解决。只测本次风险，不据此放宽原范围/出包门禁。

1. 从业务条件/配置及运行界面人工建立 `button-plan.json`：控件稳定 ID、页面、适用状态、业务来源哈希及受保护业务域 `business_domains`。清单是否完整须对照源码调用方与实际页面；脚本只核相对于此计划的覆盖。普通导航等范围外控件逐项说明；条件出现的控件用 `visible_when` 按业务数据声明。预期从余额、星数、领取标记、阈值推导，不能抄 `button.enabled/reason`。
2. 真实操作后保存 `button-run.json`：每个控件/状态各一条，含页面全部可见控件 ID（保留 disabled）、输入、业务前后值、实际提示全文、原始证据哈希。缺状态保留未测；不能以 `n/a` 或概括文字代替。难到达状态可在计划中明确 `isolated_production` 和理由，真实运行生产方法后单列，不能写成触摸通过。
3. 执行下面同一个命令。计划内缺/多/重复目标、空清单、未测、错误条件、无关/旧提示均拒绝；受保护域仅允许 `expect.after` 及 `allow_changes` 中逐字段声明的变更，其他变更失败。提示可读性仍实际看图；检查器不认证触摸或图像真实性。旧故障版失败、正常禁用态和修复版通过后保留报告。完整 R06 的 `button_check` 引用报告相对路径与 SHA-256，门禁重读原输入及业务来源；文字总结不能代替，R06不能用泛化 `n/a` 绕过。本轮无控件改动时无需另启动这项局部检查。

```sh
python3 <skills>/cocos-game-to-english/scripts/button_state_check.py \
  --project <工程> --plan <工程>/docs/logic/button-plan.json \
  --run <工程>/docs/logic/button-run.json --out <工程>/docs/logic/button-report.json
```

文件结构示例（金额阈值仅为示例，换成当前业务规则）：

```json
{
  "schema": "button-state-plan.v1",
  "business_sources": [{"path":"assets/shop.json","sha256":"实际哈希"}],
  "business_domains": ["store"],
  "controls": [{"id":"shop.buy","page":"shop","states":{
    "locked": {
      "when":{"lt":[{"path":"before.store.coins"},10]},
      "expect":{"kind":"blocked","unchanged":["store"],
        "message":{"template":"Need {n} more coins.",
          "values":{"n":{"sub":[10,{"path":"before.store.coins"}]}}}}
    },
    "ready": {
      "when":{"ge":[{"path":"before.store.coins"},10]},
      "expect":{"kind":"effect","after":{
        "store.coins":{"sub":[{"path":"before.store.coins"},10]},
        "store.items":{"add":[{"path":"before.store.items"},1]}}}
    }
  }}],
  "excluded_controls":[{"id":"shop.close","page":"shop","why":"本次只修购买状态；返回功能已有同版有效记录"}]
}
```

`run` 使用 `schema: button-state-run.v1`、同一 `business_sources`、非空 `cases`。每条：

```json
{
  "id":"shop.buy::locked","page":"shop","control":"shop.buy","state":"locked",
  "status":"tested","layer":"browser_touch","input":{"performed":true},
  "visible_controls":["shop.buy","shop.close"],
  "before":{"store":{"coins":4,"items":0}},"after":{"store":{"coins":4,"items":0}},
  "feedback":{"before_id":"原提示ID","after_id":"新提示ID","text":"Need 6 more coins."},
  "evidence":[{"path":"docs/evidence/raw-input.json","sha256":"实际哈希"}]
}
```

必须同时提供计划中的 `ready` 条目。`when` 与 `after` 右侧只读 before，禁止用执行后的实际值作为自身预期。表达式支持 `path/default`、eq/ne/lt/le/gt/ge/in、all/any/not、add/sub/mul/div/floor/min/max；随机奖励可在 `allow_changes` 逐字段开放并用 `expect.assert` 对 after 断言合法集合。`expect.unchanged` 可增加保护；禁用态整个业务域不得变更。提示全文精确匹配独立业务预期，新提示ID本身不算成功。证据及规则文件限工程内；文件变化需重验。自测：`scripts/test_button_state_check.py`。
