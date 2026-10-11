# 这次发布了什么

一个站在背调员视角的简历审计 skill。

## 它做什么

把你的简历逐句过一遍，找出背调时会被问住的地方：

- **时间线**：起止年月对不对？有没有打架的两段经历？空窗期藏得住吗？
- **Title**：专员写成主管？组织架构一拉就穿帮。
- **数字**：每个业绩数字，证据在哪？
- **证书技能**："精通"的东西真答得上来吗？
- **薪资**：虚报 20%+，银行流水直接挂——只做风险提示。

## 怎么用

```bash
python scripts/bg_audit.py new --resume resume.pdf --name my-audit
python scripts/bg_audit.py timeline my-audit/     # 机器自动：重叠、空窗、模糊日期
# AI 逐条审计，写入 audit-ledger.json
python scripts/bg_audit.py report my-audit/ --output audit-report.md
```

每条风险带：原文句子、背调会怎么核、风险在哪、怎么修。最后只有一句话检验：如果前公司的直属上级坐在对面，你简历里的每一句都敢当面念出来吗？

## 原则

不教造假。所有修复建议只能是：删掉、改成真的、准备真实证据。风险等级是分类不是概率，不编"背调通过率"。

---

# What this release is

A skill that audits your resume the way a background-check investigator would.

## What it checks

- **Timeline**: are the dates right? Any overlapping jobs? Any gap you're hoping nobody notices?
- **Titles**: "Specialist" inflated to "Manager"? One org-chart pull exposes it.
- **Numbers**: for every metric, where's the evidence?
- **Skills & certs**: the things you claim to "master" — could you answer a deep question?
- **Salary**: inflate by 20%+ and the bank statement kills it. Risk flag only.

## Usage

```bash
python scripts/bg_audit.py new --resume resume.pdf --name my-audit
python scripts/bg_audit.py timeline my-audit/     # automatic: overlaps, gaps, fuzzy dates
# the agent audits claim by claim into audit-ledger.json
python scripts/bg_audit.py report my-audit/ --output audit-report.md
```

Every risk comes with: the original sentence, how a check would verify it, where the risk is, how to fix it. It ends with one test: if your former manager sat across from you, could you read every line out loud?

## Principles

No deception coaching. Every fix is one of: delete it, rewrite it truthfully, prepare real evidence. Risk levels are categories, not probabilities — no made-up pass rates.
