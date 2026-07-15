# GPT Evaluation Batch

请先阅读并遵循以下评估指南，然后评价本批候选。只输出 JSONL 评分结果。

## Evaluation Guide

# GPT 评估指南

本指南用于让大模型对临床试验纳排标准的候选布尔表达式进行盲化语义评估。GPT 评分不是金标准，也不是对隐藏答案的匹配；它只是在固定 rubric 下，根据原始纳排标准文本判断候选表达式的忠实性、完整性和可用性。

## 评估角色

请作为独立评估者，逐条评价候选布尔表达式。每条样本只允许使用以下信息：

- 原始纳排标准文本。
- 一个候选布尔表达式。
- 本指南中的评分细则。

请不要推测候选表达式由哪种方法生成，不要使用任何隐藏参考答案，不要根据表达式长短直接加分或扣分。评价重点是候选表达式是否保留原文临床含义。

## 输入字段

每条候选通常包含：

- `candidate_id`：盲化候选编号。
- `doc_id`：原始纳排标准编译单元编号。
- `case_bucket`：样本类型，可能为 `or`、`scope` 或 `other`。
- `source_criterion`：原始纳排标准文本。
- `candidate_expression`：候选布尔表达式。

`candidate_id` 是唯一需要在输出中保留的样本键。不要输出方法名。

## 评分流程

对每条候选按以下顺序评估：

1. 阅读 `source_criterion`，识别关键临床条件、数值、时间、限定词、否定、并列关系和局部分组。
2. 阅读 `candidate_expression`，判断它是否表达了相同临床含义。
3. 分别给五个维度打 0、1、2 分。
4. 选择适用的 `error_flags`。
5. 写一句非常简短的 `brief_rationale`，说明主要扣分原因或为什么基本正确。

不同候选之间不要相互比较；每条候选都只与自己的原始文本比较。

## 评分维度

每个维度均为 0、1、2 分。

### 1. predicate_completeness

评价关键临床谓词是否完整。

- 2：疾病、药物、检查、数值、时间、限定词、否定等关键信息基本完整，并整合为清晰谓词。
- 1：主要谓词存在，但部分数值、时间、限定词、修饰语或谓词归属缺失或碎片化。
- 0：关键谓词大量缺失、严重碎片化、空输出或不可理解。

### 2. logical_correctness

评价 AND、OR、NOT 是否保留原文逻辑。

- 2：合取、析取和否定关系基本正确。
- 1：主体逻辑部分正确，但至少一个重要 AND、OR 或 NOT 关系错误或模糊。
- 0：布尔逻辑显著改变原文含义。

### 3. grouping_correctness

评价并列项、共享修饰语、局部分组和层级结构。

- 2：替代项、共享修饰语、局部条件组和嵌套结构清晰。
- 1：部分分组正确，但替代项归属或共享修饰语作用范围有错误。
- 0：分组缺失或严重误导。

### 4. faithfulness

评价候选表达式是否忠实于原文。

- 2：没有临床重要的新增条件或遗漏。
- 1：总体忠实，但存在需要人工修正的重要细节。
- 0：新增原文不支持的条件、遗漏核心条件或与原文矛盾。

### 5. downstream_usability

评价是否可作为队列查询或患者筛选的中间表示。

- 2：基本可用于后续查询生成或患者筛选，只需少量人工修正。
- 1：部分可用，但需要明显人工修复。
- 0：难以下游使用。

## 错误标签

从以下标签中选择 1 个或多个：

- `missing_key_condition`：遗漏关键条件。
- `extra_condition`：新增原文不支持的条件。
- `wrong_or_logic`：析取条件遗漏或被错误表示为 AND。
- `wrong_and_logic`：必须同时满足的条件遗漏或被错误表示为 OR。
- `wrong_negation`：否定缺失、误加或作用范围错误。
- `wrong_scope_or_grouping`：分组、嵌套或共享修饰语作用范围错误。
- `predicate_fragmentation`：同一临床谓词被拆成混乱片段。
- `overly_verbose`：表达过度冗长并影响可用性。
- `empty_or_unusable`：空输出或不可用。
- `none`：无明显错误标签。

如果没有明显错误，`error_flags` 只能填写 `["none"]`。如果存在其他错误标签，不要同时填写 `none`。

## 输出格式

请严格输出 JSONL。每个候选只输出一行 JSON，不要输出 Markdown 表格，不要输出额外解释文字。

输出字段必须为：

- `candidate_id`
- `predicate_completeness`
- `logical_correctness`
- `grouping_correctness`
- `faithfulness`
- `downstream_usability`
- `total_score`
- `error_flags`
- `brief_rationale`

示例：

```json
{"candidate_id":"EXAMPLE_ID","predicate_completeness":2,"logical_correctness":2,"grouping_correctness":1,"faithfulness":2,"downstream_usability":1,"total_score":8,"error_flags":["wrong_scope_or_grouping"],"brief_rationale":"Main predicates and logic are preserved, but one local grouping is ambiguous."}
```

`total_score` 必须等于五个维度分数之和，范围为 0-10。

## 推荐投喂方式

全量评估约有 8000 个候选，不建议一次性输入。建议每批 20-50 个候选。

可用以下命令导出批次文件：

```powershell
python src/criteria_boolean/export_gpt_eval_batches.py --batch-size 25
```

批次文件位于：

```text
data/evaluation/gpt_manual_batches/
```

每批评估步骤：

1. 粘贴本评估指南。
2. 粘贴一批候选 JSONL。
3. 要求模型只输出同样数量的 JSONL 评分结果。
4. 检查输出行数是否与输入候选数一致。
5. 将输出追加保存到 `results/llm_eval/llm_judge_results.jsonl`。

全部批次保存后运行：

```powershell
python src/criteria_boolean/summarize_llm_judge.py
```

## 给 Codex 或 GPT 的输入模板

如果使用 Codex 直接读取本项目文件，可以输入：

```text
请按照 docs/gpt_manual_evaluation_guide.md 的评分标准，
评估 data/evaluation/gpt_manual_batches/gpt_eval_batch_0001.md 中的所有候选。

要求：
1. 只根据每条样本的 source_criterion 和 candidate_expression 评分。
2. 不要读取或使用 data/evaluation/llm_judge/llm_eval_key.csv。
3. 不要推测方法名。
4. 每个 candidate_id 输出一行 JSONL。
5. 输出字段必须包含 candidate_id、五个维度分数、total_score、error_flags、brief_rationale。
6. 不输出 Markdown 表格，不输出额外解释文字。
```

如果需要 Codex 直接写入结果文件，可以输入：

```text
请按照 docs/gpt_manual_evaluation_guide.md 的评分标准，
评估 data/evaluation/gpt_manual_batches/gpt_eval_batch_0001.md，
并把 JSONL 结果追加保存到 results/llm_eval/llm_judge_results.jsonl。

注意：
- 不要读取 data/evaluation/llm_judge/llm_eval_key.csv。
- 如果结果文件不存在，请创建它。
- 如果输出行数不是 25 行，请停止并说明原因。
```

评估下一批时，只需要把文件名改成 `gpt_eval_batch_0002.md`、`gpt_eval_batch_0003.md`，依次类推。所有批次完成后，再运行汇总脚本。

## Candidate Items

```jsonl
{"candidate_id": "LLM06501", "doc_id": "NCT01980680_exc", "case_bucket": "other", "source_criterion": "Patients with >14 follicles on day of trigger Previous hyperresponse with OHSS development Previous low response (less than 3 oocytes on a high dose of FSH stimulation) Endocrine disorders", "candidate_expression": "((>14) AND (Endocrine disorders) AND (OHSS development) AND (Previous) AND (day of trigger) AND (follicles) AND (high dose of FSH stimulation) AND (hyperresponse) AND (less than 3) AND (low response) AND (on day of trigger) AND (oocytes))"}
{"candidate_id": "LLM06502", "doc_id": "NCT02937779_inc", "case_bucket": "other", "source_criterion": ">= 18 years old the day of inclusion Pregnancy Positive HBs Ag Informed consent obtained with information sheet given and explained and the consent form signed by the participant of the project investigator at the latest the day of the inclusion", "candidate_expression": "((>= 18 years) AND (HBs Ag) AND (Informed consent obtained with information sheet given and explained and the consent form signed by the participant of the project investigator at the latest the day of the inclusio) AND (Positive) AND (Pregnancy) AND (old))"}
{"candidate_id": "LLM06503", "doc_id": "NCT01994382_inc", "case_bucket": "or", "source_criterion": "Phase 1 Specific Patient at least 18yrs of age with histologically confirmed CLL/SLL or B-cell Non-Hodgkin lymphoma (DLBCL, FL, MCL, MZL, lymphoplasmacytic lymphoma). Phase 2a Inclusion Histological evidence: FL Grade 1-3A/iNHL, with relapsed or refractory disease (iNHL includes LPL/WM, MZL); aNHL, defined as DLBCL, FL Grade 3B, MCL, and transformed NHL with relapsed disease; CLL/SLL, PTCL, or CTCL (with MF/SS) with relapsed or refractory. Received BCR and/or BCL2 inhibitors were intolerant or had relapsed/refractory disease afterwards. Prior treatment for lymphoid malignancy for progressive /refractory disease ≥ 1 prior regimen (min 2 cycles) with antibody conjugate, cytotoxic chemotherapy, or TKI alone or in combination. Measureable disease defined as: ≥ 1 lesion ≥ 1.5 cm single dimension via CT, CT/PET with nodal or mass lesions; Quantifiable circulating tumor cells; or for Waldenström's macroglobulinemia presence of IgM l > 2X ULN; For CTCL: mSWAT > 0 Ability to provide diagnostic reports General Inclusion ECOG Score of 0 or 1. Hematologic ANC > 1000/uL and platelet > 75,000/uL, Serum creatinine of < 1.5 ULN or calculated CrCl of > 50 mL/min Bilirubin < 20.0mg/dL (if Gilberts then < 2.5 mg/dL) and AST/AST < 2.5 ULN", "candidate_expression": "((0 or 1) AND (1-3A) AND (3B) AND (< 1.5 ULN) AND (< 2.5 ULN) AND (< 2.5 mg/dL) AND (< 20.0mg/dL) AND (> 0) AND (> 1000/uL) AND (> 2X ULN) AND (> 50 mL/min) AND (> 75,000/uL) AND (AST/AST) AND (B-cell Non-Hodgkin lymphoma) AND (BCL2 inhibitors) AND (BCR inhibitors) AND (Bilirubin) AND (CLL) AND (CT) AND (CT/PET) AND (CTCL) AND (DLBCL) AND (ECOG Score) AND (FL) AND (Gilberts) AND (Grade) AND (Hematologic ANC) AND (Histological) AND (IgM l) AND (LPL) AND (MCL) AND (MF) AND (MZL) AND (Measureable disease) AND (PTCL) AND (Prior) AND (SLL) AND (SS) AND (Serum creatinine) AND (TKI) AND (WM) AND (Waldenström's macroglobulinemia) AND (aNHL) AND (afterwards) AND (age) AND (antibody conjugate) AND (at least 18yrs) AND (calculated CrCl) AND (circulating tumor cells) AND (confirmed) AND (cytotoxic chemotherapy) AND (histologically) AND (iNHL) AND (intolerant) AND (lymphoid malignancy) AND (lymphoplasmacytic lymphoma) AND (mSWAT) AND (mass lesions) AND (min 2 cycles) AND (nodal lesions) AND (platelet) AND (progressive disease) AND (refractory disease) AND (relapsed) AND (relapsed disease) AND (transformed NHL) AND (treatment) AND (≥ 1 lesion) AND (≥ 1 prior regimen) AND (≥ 1.5 cm) AND (≥ 1.5 cm single dimension))"}
{"candidate_id": "LLM06504", "doc_id": "NCT03088280_exc", "case_bucket": "other", "source_criterion": "PRA > 50% DSA > 1500 MFI Retransplantation Patients who are planning to receive mycophenolate instead of everolimus Patients who have planning for follow-up in another center", "candidate_expression": "((> 1500 MFI) AND (> 50%) AND (DSA) AND (PRA) AND (Retransplantation) AND (another center) AND (everolimus) AND (follow-up) AND (instead of) AND (mycophenolate) AND (planning for) AND (planning to))"}
{"candidate_id": "LLM06505", "doc_id": "NCT01446094_inc", "case_bucket": "other", "source_criterion": "Aged 18 years or older Scheduled for invasive coronary angiography", "candidate_expression": "((18 years or older) AND (Aged) AND (Scheduled) AND (invasive coronary angiography))"}
{"candidate_id": "LLM06506", "doc_id": "NCT02607163_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06507", "doc_id": "NCT02379156_exc", "case_bucket": "or", "source_criterion": "Evidence of sympathetic integrity below the lesion level by the skin axon-reflex vasodilatation (SkARV) test; Known allergies to midodrine hydrochloride; PMH of diagnosed heart, kidney, peripheral vascular, or cerebral vascular disease, or diabetes mellitus; Hypertension (BP>140/90 mmHg); Untreated thyroid disease; Acute illness or infection; Current smoker; Pregnancy.", "candidate_expression": "((>140/90 mmHg) AND (Acute) AND (BP) AND (Hypertension) AND (Pregnancy) AND (SkARV) AND (Untreated) AND (allergies) AND (below the lesion level) AND (cerebral vascular disease) AND (diabetes mellitus) AND (heart disease) AND (illness) AND (infection) AND (kidney disease) AND (midodrine hydrochloride) AND (peripheral vascular, disease) AND (smoker) AND (sympathetic integrity) AND (test skin axon-reflex vasodilatation) AND (thyroid disease))"}
{"candidate_id": "LLM06508", "doc_id": "NCT00502567_exc", "case_bucket": "other", "source_criterion": "Inadequate bone marrow reserve history of poorly controlled hypertension", "candidate_expression": "((Inadequate bone marrow reserve) AND (history) AND (poorly controlled hypertension))"}
{"candidate_id": "LLM06509", "doc_id": "NCT03047538_exc", "case_bucket": "or", "source_criterion": "hypersensitivity to perindopril or to other ACE inhibitors, amlodipine, atorvastatin, dihydropyridines or to or statins angioneurotic edema in medical history (hereditary / idiopathic or associated with prior treatment with ACE inhibitors) severe hypotension, shock, including cardiogenic shock hemodynamically unstable heart failure Active liver disease or unexplained persistent elevations of serum transaminases more than three times normal Women of childbearing age without reliable contraception pregnancy breastfeeding Patients with contraindications listed in the currently valid SP", "candidate_expression": "((ACE inhibitors) AND (ACE inhibitors other) AND (Women) AND (amlodipine) AND (angioneurotic edema hereditary idiopathic) AND (atorvastatin) AND (breastfeeding) AND (cardiogenic shock) AND (childbearing age reliable) AND (contraindications listed in the currently valid SP) AND (dihydropyridines) AND (heart failure hemodynamically unstable) AND (hypersensitivity) AND (hypotension) AND (liver disease) AND (perindopril) AND (pregnancy) AND (serum transaminases unexplained persistent elevations more than three times normal) AND (shock) AND (statins) AND (treatment prior associated) AND NOT (contraception))"}
{"candidate_id": "LLM06510", "doc_id": "NCT01228279_exc", "case_bucket": "or", "source_criterion": "Diabetes Mellitus Acute coronary syndrome in the past 6 months Cardiac arrhythmias (2nd and 3rd degree heart block or premature ventricular complexes in Lown classes 4 or 5) Symptoms suggestive of obstructive or central sleep apnea (with a score of > 10 on Epworth sleepiness scale) Patients taking Clonidine Body mass index (BMI) > 34 Patients unable to give consent Pregnant women Patients with leg injury involving nerve damage Patients taking anticoagulant medication Patients with significant bleeding disorder or liver disorder Hemoglobin <1.05 g/dl at the time of initiation of therapy patients with unilateral or bilateral nephrectomy Planned kidney transplant in the next 4 months Life expectancy under 6 months Oliguria (urine output less than 400 ml per day)", "candidate_expression": "((<1.05 g/dl) AND (> 34) AND (Acute coronary syndrome) AND (BMI) AND (Body mass index) AND (Cardiac arrhythmia) AND (Clonidine) AND (Diabetes Mellitus) AND (Epworth sleepiness scale) AND (Hemoglobin) AND (Life expectancy) AND (Oliguria) AND (Patients unable to give consent) AND (Planned) AND (Pregnant women) AND (anticoagulant) AND (at the time of initiation of therapy) AND (in the next 4 months) AND (in the past 6 months) AND (initiation of therapy) AND (kidney transplant) AND (leg injury) AND (less than 400 ml per day) AND (nephrectomy) AND (nerve damage) AND (premature ventricular complexes) AND (score of > 10) AND (significant) AND (under 6 months) AND (urine output) AND ((central sleep apnea) OR (obstructive sleep apnea)) AND ((bleeding disorder) OR (liver disorder)) AND ((bilateral) OR (unilateral)) AND ((2nd degree heart block) OR (3rd degree heart block)) AND ((Lown classes 4) OR (Lown classes 5)))"}
{"candidate_id": "LLM06511", "doc_id": "NCT02260206_exc", "case_bucket": "other", "source_criterion": "Hypersensitivity on Colchicine The existence of intra-cardiac thrombus on trans-esophageal echocardiography Pregnancy", "candidate_expression": "((Colchicine) AND (Hypersensitivity) AND (Pregnancy) AND (intra-cardiac thrombus) AND (trans-esophageal echocardiography))"}
{"candidate_id": "LLM06512", "doc_id": "NCT03134196_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06513", "doc_id": "NCT02687724_inc", "case_bucket": "or", "source_criterion": "Patients = 18 years of age Subjects must be able and willing to give written informed consent and to comply with the requirements of this study protocol Established diagnosis of UC and moderate-to-severe disease activity, defined as a Mayo score of 6-12, with an endoscopic subscore =2. Patients had an inadequate response to, or had failed to tolerate, 1 or more of the following conventional therapies: oral 5-aminosalicylates, oral corticosteroids, azathioprine (AZA), and/or 6-mercaptopurine (6MP); or corticosteroid dependent (ie, an inability to taper corticosteroids without recurrence of UC symptoms). Patients concurrently treated with oral 5-aminosalicylates or corticosteroids were to receive a stable dose for at least 2 weeks before baseline, and patients receiving AZA and/or 6MP were to receive a stable dose for at least 4 weeks before baseline. Patients were required to maintain stable doses of their concomitant UC medications during the study. Female subjects of child bearing potential must be willing to ensure that they or their partner use effective contraception during the study and for 6 months thereafter OR Surgical sterilized female patients with documentation of prior hysterectomy, tubal ligation or complete bilateral oophorectomy OR Postmenopausal women with postmenopausal defined as permanent cessation >1 year of previously occurring menses. Female subjects' serum pregnancy test performed at the screening visit and urine pregnancy test performed at the baseline visit must be negative. Subjects have following investigations within 1 month prior to enrolment. Routine bloods including U&E, FBC, LFTs, inflammatory markers (CRP) and albumin will be measured. Medical history, concomitant medications Intradermal reaction to Tuberculin (PPD skin test) or Mycobacterium tuberculosis antigenspecific interferon-gamma release assay (IGRA) TB screening: chest X-Ray unless performed in the last 6 months Stool examination for enteric pathogens including Clostridium difficile Inclusion/exclusion criteria Informed consent Mayo score (including sigmoidoscopy unless performed in previous 3 months) Patient's weight and height and abdominal circumference", "candidate_expression": "((1 or more) AND (6-12) AND (6-mercaptopurine (6MP)) AND (6MP) AND (= 18 years) AND (=2) AND (AZA) AND (FBC) AND (Female subjects of child bearing potential must be willing to ensure that they or their partner use effective contraception during the study and for 6 months thereafter OR) AND (Female subjects' serum pregnancy test performed at the screening visit and urine pregnancy test performed at the baseline visit must be negative.) AND (Intradermal reaction to Tuberculin (PPD skin test)) AND (LFTs) AND (Mayo score) AND (Mycobacterium tuberculosis antigenspecific interferon-gamma release assay (IGRA)) AND (Postmenopausal women with postmenopausal defined as permanent cessation >1 year of previously occurring menses.) AND (Routine bloods) AND (Stool examination) AND (Surgical sterilized female patients with documentation of prior hysterectomy, tubal ligation or complete bilateral oophorectomy OR) AND (TB screening) AND (U&E) AND (UC) AND (abdominal circumference) AND (age) AND (albumin) AND (azathioprine (AZA)) AND (chest X-Ray) AND (corticosteroid) AND (corticosteroids) AND (dependent) AND (endoscopic subscore) AND (failed to tolerate) AND (for at least 2 weeks before baseline) AND (for at least 4 weeks before baseline) AND (for enteric pathogens including Clostridium difficile) AND (height) AND (inadequate response) AND (inflammatory markers (CRP)) AND (moderate-to-severe) AND (oral 5-aminosalicylates) AND (oral corticosteroids) AND (sigmoidoscopy) AND (stable dose) AND (treated) AND (weight) AND (within 1 month prior to enrolment))"}
{"candidate_id": "LLM06514", "doc_id": "NCT03058835_inc", "case_bucket": "or", "source_criterion": "18 - 64 years old Able to give consent unprotected sex (in past 6 months) with 1 or more men of unknown HIV status evaluated for an STI within 6 months prior to screening sex in last 6 months with an HIV-infected partner IDU with report of using previously used or shared needles in past 6 months or has been in a methadone, buprenorphine, or suboxone treatment program in past 6 months or engaging in high-risk sexual behaviors individuals engaging in transactional sex (i.e sex for money, drugs, or housing) Infrequently uses condoms during sex with 1 or more partners of unknown HIV status who are known to be at substantial risk of HIV infection (IDU or bisexual male partner) CrCl = 60 ml/min HIV- uninfected women desiring PrEP", "candidate_expression": "((1 or more) AND (18 - 64 years) AND (= 60 ml/min) AND (CrCl) AND (HIV- uninfected) AND (HIV-infected partner) AND (IDU) AND (Infrequently uses condoms during sex) AND (PrEP) AND (at substantial risk of HIV infection) AND (bisexual male partner) AND (buprenorphine) AND (desiring) AND (engaging in high-risk sexual behaviors) AND (evaluated for an STI) AND (in last 6 months) AND (in past 6 months) AND (men of unknown HIV status) AND (methadone) AND (old) AND (partners of unknown HIV status) AND (screening) AND (sex) AND (sex for drugs) AND (sex for housing) AND (sex for money) AND (suboxone) AND (transactional sex) AND (treatment program) AND (unprotected sex) AND (using previously used or shared needles) AND (within 6 months prior to screening) AND (women))"}
{"candidate_id": "LLM06515", "doc_id": "NCT02298504_exc", "case_bucket": "or", "source_criterion": "Teeth with clinical symptoms of irriversible pulpitis or pulp necrosis or acute dental infection Children with systemic illness that contraindicated vital pulp treatment such a sickle cell disease Teeth that are not restorable", "candidate_expression": "((Teeth that are not restorable) AND (acute dental infection) AND (contraindicated) AND (irriversible pulpitis Teeth) AND (pulp necrosis Teeth) AND (sickle cell disease) AND (systemic illness) AND (vital pulp treatment))"}
{"candidate_id": "LLM06516", "doc_id": "NCT02630628_inc", "case_bucket": "or", "source_criterion": "Biopsy-proven LN Class III/IV±V (ISN/RPS 2003), with biopsy performed within 12 weeks of randomization. Positive anti-dsDNA. Active LN with proteinuria (urine protein/creatinine ratio >1.0 or 24-hr urine protein >1.0 g at baseline), with or without hematuria. Both 'incident' (i.e. new) patients and 'flare' patients can be included.", "candidate_expression": "((>1.0) AND (>1.0 g) AND (Active) AND (Class III/IV±V) AND (LN) AND (Positive) AND (anti-dsDNA) AND (biopsy) AND (hematuria) AND (proteinuria) AND (within 12 weeks) AND ((24-hr urine protein) OR (urine protein/creatinine ratio)))"}
{"candidate_id": "LLM06517", "doc_id": "NCT02117986_inc", "case_bucket": "other", "source_criterion": "patient hospitalized in critical care units patient infected by multi drug resistant Gram negative bacteria susceptibly only to colistin source of infection: blood, respiratory, intra abdominal or urinary", "candidate_expression": "((Gram negative bacteria) AND (colistin) AND (critical care units) AND (hospitalized) AND (multi drug resistant) AND (only) AND (susceptibly))"}
{"candidate_id": "LLM06518", "doc_id": "NCT02473809_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes Treatment with insulin Body weight > 140 kg HbA1c > 75 mmol/mol Treatment with GLP-1 analogues, Dipeptidyl peptidase-4 inhibitors, or glitazones Chronic kidney disease Hepatic disease Pancreatitis Inflammatory bowel disease Osteoporosis Family or personal history of medullary thyroid carcinoma Treatment with glucocorticoids Hormone replacement therapy Diabetic gastroparesis Pregnancy or lactation", "candidate_expression": "((Body weight > 140 kg) AND (Chronic kidney disease) AND (Diabetic gastroparesis) AND (HbA1c > 75 mmol/mol) AND (Hepatic disease) AND (Hormone replacement therapy) AND (Inflammatory bowel disease) AND (Osteoporosis) AND (Pancreatitis) AND (Treatment) AND (Type 1 diabetes) AND (glucocorticoids) AND (insulin) AND (medullary thyroid carcinoma) AND ((Family) OR (personal history)) AND ((Pregnancy) OR (lactation)) AND ((Dipeptidyl peptidase-4 inhibitors) OR (GLP-1 analogues) OR (glitazones)))"}
{"candidate_id": "LLM06519", "doc_id": "NCT03124329_inc", "case_bucket": "or", "source_criterion": "Male and female individuals between ages of 18 to 70 years old Multiple contiguous gingival recession defects on a minimum of two adjacent teeth, exhibiting 3mm or more recession on at least one of those teeth No prior surgical treatment in the sites planned for therapy Minimum of 2 mm of keratinized gingiva Absence of cervical restorations extending to the CEJ Miller class 1, 2 and 3 recession defects will be included Availability to undergo treatment and return for follow up visits at specified post-operative intervals", "candidate_expression": "((ages between 18 to 70 years old) AND (gingival recession defects Multiple minimum of two) AND (keratinized gingiva Minimum of 2 mm) AND (recession 3mm or more at least one) AND (recession defects) AND NOT (cervical restorations extending to the CEJ) AND NOT (surgical treatment) AND ((Miller) OR (class 1, 2 and 3)))"}
{"candidate_id": "LLM06520", "doc_id": "NCT02247128_inc", "case_bucket": "other", "source_criterion": "Need for long-term oral anticoagulation; Patient has provided written informed consent.", "candidate_expression": "((Need for) AND (Patient has provided written informed consent) AND (long-term oral anticoagulation))"}
{"candidate_id": "LLM06521", "doc_id": "NCT02385448_exc", "case_bucket": "or", "source_criterion": "Operative findings not suggestive of endometriotic cyst Contraindications to progestogens or oral contraceptive pills Unwillingness to tolerate menstrual irregularity Planning pregnancy within 2 years of study Cannot understand English, Cantonese or Putonghua", "candidate_expression": "((Contraindications) AND (Operative findings) AND (Planning) AND (Unwillingness to tolerate) AND (endometriotic cyst) AND (menstrual irregularity) AND (not) AND (pregnancy) AND (suggestive) AND (within 2 years of study) AND ((oral contraceptive pills) OR (progestogens)))"}
{"candidate_id": "LLM06522", "doc_id": "NCT02687178_exc", "case_bucket": "other", "source_criterion": "diabetes mellitus secondary hypertension pregnancy", "candidate_expression": "((diabetes mellitus) AND (pregnancy) AND (secondary hypertension))"}
{"candidate_id": "LLM06523", "doc_id": "NCT03631355_inc", "case_bucket": "other", "source_criterion": "Patients undergoing a high tibial osteotomy (HTO) Patients undergoing tibial tubercle osteotomy (TTO) with or without medial patello-femoral ligament (MPFL) reconstruction", "candidate_expression": "((high tibial osteotomy (HTO)) AND (medial patello-femoral ligament (MPFL) reconstruction) AND (tibial tubercle osteotomy (TTO)) AND (undergoing))"}
{"candidate_id": "LLM06524", "doc_id": "NCT03096613_exc", "case_bucket": "or", "source_criterion": "Acute heart failure or acute exacerbation of chronic heart failure within the past 2 weeks. Scheduled cardiac resynchronization therapy or heart transplantation. History of malignant tumor or life expectancy under 12 months. Already on medications that may affect thyroid function (L-T4, carbimazole, propylthiouracil, amiodarone, lithium). Pregnancy and lactation period. Participation in another clinical trial within the past 30 days. Contraindication or intolerance to evidence-based therapy for CHF, such as beta-blocker, angiotensin-converting enzyme inhibitor or angiotensin receptor blocker. Known hypersensitivity to the trial treatment(s) or diluents (when applicable), including placebo or other comparator drug(s). Untreated adrenal insufficiency. Untreated pituitary insufficiency. Untreated thyrotoxicosis. Treatment with levothyroxine must not be initiated in patients with acute myocardial infarction, acute myocarditis, or acute pancarditis. Severe renal dysfunction (eGFR=30 ml/min/1.73m2). Significant hepatic impairment (Serum GPT > 120 U/L). Any disorder which, in the opinion of the investigator, might jeopardise subject's safety or compliance with the protocol.", "candidate_expression": "((Any disorder which, in the opinion of the investigator, might jeopardise subject's safety or compliance with the protocol.) AND (CHF) AND (Pregnancy) AND (Serum GPT > 120 U/L) AND (adrenal insufficiency Untreated) AND (eGFR =30 ml/min/1.73m2) AND (evidence-based therapy) AND (exacerbation acute) AND (hepatic impairment Significant) AND (hypersensitivity) AND (lactation period) AND (levothyroxine) AND (medications) AND (pituitary insufficiency Untreated) AND (renal dysfunction Severe) AND (thyroid function affect) AND (thyrotoxicosis Untreated) AND NOT (Treatment) AND ((Acute heart failure) OR (chronic heart failure)) AND ((life expectancy under 12 months) OR (malignant tumor)) AND ((L-T4) OR (amiodarone) OR (carbimazole) OR (lithium) OR (propylthiouracil)) AND ((Contraindication) OR (intolerance)) AND ((angiotensin receptor blocker) OR (angiotensin-converting enzyme inhibitor) OR (beta-blocker)) AND ((trial diluents) OR (trial treatment(s))) AND ((comparator drug(s) other) OR (placebo)) AND ((acute myocardial infarction) OR (acute myocarditis) OR (acute pancarditis)) AND ((cardiac resynchronization therapy) OR (heart transplantation)))"}
{"candidate_id": "LLM06525", "doc_id": "NCT02796378_exc", "case_bucket": "or", "source_criterion": "Cholesterol-lowering drugs Diabetes Mellitus Cardiovascular disease such as arrythmia, ischaemic heart disease. Musculoskeletal disorders preventing the subject to perform physical training Mental disorders preventing the subject to understand the project description.", "candidate_expression": "((Cardiovascular disease) AND (Cholesterol-lowering drugs) AND (Diabetes Mellitus) AND (Mental disorders) AND (Musculoskeletal disorders) AND (arrythmia) AND (ischaemic heart disease) AND (preventing the subject to perform physical training) AND (preventing the subject to understand the project description))"}
```
