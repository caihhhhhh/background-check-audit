<p align="center">
  <img src="docs/images/hero.png" alt="背调-proof 简历审计：每一句简历，都经得起背调" width="100%" />
</p>

# 背调-proof 简历审计

> 你简历里的每一句，都经得起背调吗？

大厂背调越来越严。第三方背调公司会逐项核对你的公司、职位、在职时间、薪资——offer 到手了也能作废，进黑名单。

这个 skill 站在**背调员的视角**，把你的简历逐句过一遍，提前找出会被问住的地方。

先说清楚：它不教你造假。它帮你找到风险，然后诚实地修掉——删掉，改成真的，或者提前准备好证据。

## 它查什么

- **时间线**：起止年月对不对？有没有时间打架的两段经历？空窗期是不是此地无银？
- **Title**：专员写成主管？前公司组织架构一拉就穿帮。
- **数字**：每个业绩数字，你能说出证据在哪吗？"提升 300%"——从 1 到 4 也是 300%。
- **证书技能**："精通"的东西，真被问到答得上来吗？证书在有效期内吗？
- **薪资**：虚报 20% 以上，银行流水直接挂。这里只做风险提示。

## 怎么用

```bash
# 1. 新建一次审计
python scripts/bg_audit.py new --resume resume.pdf --name my-audit

# 2. 时间线检查（机器自动：重叠、空窗、日期模糊）
python scripts/bg_audit.py timeline my-audit/

# 3. AI 像背调员一样逐条审计，写入 audit-ledger.json

# 4. 出报告
python scripts/bg_audit.py report my-audit/ --output audit-report.md
```

## 报告长什么样

每条风险带四样东西：原文句子、背调会怎么核、风险在哪、怎么修。按风险等级排好。

最后只有一句话检验：

> 如果前公司的直属上级坐在对面，你简历里的每一句都敢当面念出来吗？

敢，就是背调-proof。

## 适合谁

- 正在求职、不想在背调环节翻车的人
- 帮别人改简历的顾问、职业咨询师
- 用 AI 写简历、但不确定哪些话站得住脚的人

## 和 ResumeProof Match 的关系

`resume-proof-match` 管"写得真"（每条 claim 都有证据链），这个管"查得严"（每条 claim 都经得起背调）。两个一起用，从写简历到过背调全闭环。

## 安装

```bash
npx skills add caihhhhhh/background-check-audit -g
```

然后对 AI 说：

> 用 background-check-audit 审计我的简历，像背调员一样逐条过，告诉我哪些地方有风险。

## 原则

- 只做风险提示和诚实修复建议，不教任何通过背调的灰色技巧。
- 风险等级是分类，不是概率——不编"背调通过率"。
- 你的简历只在本地处理，不上传任何地方。

---

开源 MIT · English: [README.md](README.md)
