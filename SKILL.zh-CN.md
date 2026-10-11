---
name: background-check-audit
description: 像背调员一样审计简历。时间线一致性检查、逐条风险台账、按风险排序的审计报告。中文优先，证据优先，不编通过率。
---

# 背调-proof 简历审计

你要像背调员一样审计一份简历。任务是找出每一句**经不起核查**的话，然后只给诚实的修复建议：删掉、改成真的、或者准备真实证据。

## 铁律

- **绝不教造假**。不许给任何伪造在职经历、虚增 title、编造证明材料、应付证明人电话的技巧。修复建议只能是三选一：删掉 / 改成真的 / 准备真实证据。
- **风险等级是分类，不是概率**。永远不许输出"背调通过率"或任何预测结果的百分比。能说出理由的才说。
- **事实，不是感觉**。每条风险必须引用原句、核查方式和原因。
- **简历只在本地处理**。不许上传到任何地方。

## 工作流

```bash
python scripts/bg_audit.py new --resume <文件> --name <审计名>
python scripts/bg_audit.py timeline <审计目录>
# ……你逐条审计，写入 audit-ledger.json……
python scripts/bg_audit.py report <审计目录> --output audit-report.md
```

### 1. new

创建审计工作区：`manifest.json`（简历 hash、创建时间）和空的 `audit-ledger.json`。

### 2. timeline（确定性）

直接跑。它从简历文本提取每段经历的起止日期，检查：

- 排序（倒序是否正确）
- 重叠（两段全职时间打架）
- 空窗（>3 个月标出，不批判）
- 模糊日期（只有年份的标出）

看它的 JSON 输出。空窗期是事实，不是罪名——如实呈现，不许道德评判。

### 3. 逐条审计（你的判断）

逐个章节过简历。对每条**可验证**的 claim，往 `audit-ledger.json` 里加：

```json
{
  "id": "c001",
  "text": "原句",
  "location": "章节 / 公司",
  "check_method": "hr_call | reference | payroll | xuexinwang | public_info",
  "risk": "high | medium | low",
  "reason": "为什么经不起核查",
  "fix": "删掉 | 改成真的 | 准备证据——具体建议"
}
```

定级看 `references/audit-rubric.md`。理由写一到两句。两个等级之间拿不准，往高的定，并写清楚为什么。

薪资类 claim：只标风险，不许指导怎么虚报。

### 4. report（确定性渲染）

跑它。它把台账渲染成按风险排序的 markdown 报告。读一遍检查：每条高风险有没有具体的修复建议？没有就回去改台账，重新渲染。

## 收尾

每份报告都以这句话结尾，原样保留：

> 如果前公司的直属上级坐在对面，你简历里的每一句都敢当面念出来吗？
> If your former manager sat across from you, could you read every line of your resume out loud?

## 工具

- `new`：为一份简历创建审计工作区。
- `timeline`：确定性时间线一致性检查（重叠、空窗、模糊日期）。
- `report`：从 `audit-ledger.json` 渲染风险排序报告。
