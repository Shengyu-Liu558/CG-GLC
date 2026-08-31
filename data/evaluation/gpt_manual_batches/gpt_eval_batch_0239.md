# GPT-5.5 Evaluation Batch

请先阅读并遵循以下评估指南，然后评价本批候选。只输出 JSONL 评分结果。

## Evaluation Guide

# GPT-5.5 评估指南

本指南用于让 GPT-5.5 对临床试验纳排标准的候选布尔表达式进行盲化语义评估。GPT-5.5 评分不是金标准，也不是对隐藏答案的匹配；它只是在固定 rubric 下，根据原始纳排标准文本判断候选表达式的忠实性、完整性和可用性。

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

## 给 Codex 或 GPT-5.5 的输入模板

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
- 如果输出行数不是25行，请停止并说明原因。
```

评估下一批时，只需要把文件名改成 `gpt_eval_batch_0002.md`、`gpt_eval_batch_0003.md`，依次类推。所有批次完成后，再运行汇总脚本。

## Candidate Items

```jsonl
{"candidate_id": "LLM05951", "doc_id": "NCT02209545_inc", "case_bucket": "or", "source_criterion": "Patients presenting for abdominal myomectomy with documented uterine fibroids on pelvic imaging (pelvic ultrasound or MRI) within in last 12 months Age = 18 years and = 50 years Pre-operative hemoglobin >8 g/dl Willing to have buccal administration of misoprostol or a placebo at least one hour pre-procedure. Ability to understand and the willingness to sign a written informed consent. Admissible medical/surgical history Can be previously treated with Depo-Lupron, Depo-Provera, or Oral Contraceptive pills Intraoperative use of vasopressin and uterine tourniquet is permissible Can have had prior Cesarean delivery", "candidate_expression": "((Ability to understand a written informed consent) AND (Age = 18 years and = 50 years) AND (Depo-Lupron) AND (Depo-Provera) AND (MRI pelvic) AND (Oral Contraceptive pills) AND (abdominal myomectomy) AND (buccal administration Willing to have at least one hour pre-procedure buccal administration) AND (hemoglobin Pre-operative >8 g/dl) AND (medical history Admissible) AND (misoprostol) AND (operative operative) AND (pelvic imaging) AND (pelvic ultrasound) AND (placebo) AND (surgical history Admissible) AND (treated previously) AND (uterine fibroids) AND (willingness to sign a written informed consent))"}
{"candidate_id": "LLM05952", "doc_id": "NCT02443844_inc", "case_bucket": "other", "source_criterion": "Patients who have non muscle invasive bladder cancer male patients patients between 40-80 years old", "candidate_expression": "((male) AND (non muscle invasive bladder cancer) AND (old between 40-80 years))"}
{"candidate_id": "LLM05953", "doc_id": "NCT02687178_inc", "case_bucket": "or", "source_criterion": "Caucasian patients affected by uncomplicated, essential hypertension, not well controlled by concomitant administration of ACE-I or ARBs and diuretics at the maximum dosage.", "candidate_expression": "((ACE-I maximum dosage) AND (ARBs maximum dosage) AND (Caucasian) AND (diuretics maximum dosage) AND (essential hypertension uncomplicated not well controlled))"}
{"candidate_id": "LLM05954", "doc_id": "NCT02838810_exc", "case_bucket": "or", "source_criterion": "Patients with liver cirrhosis, Hepatocellular Carcinoma or AFP >2 ULN or other malignancies. Patients with other factors causing liver diseases. Pregnant and lactating women. Patients with concomitant HIV infection or congenital immune deficiency diseases. Patients with diabetes, autoimmune diseases. Patients with important organ dysfunctions. Patients with serious complications (e.g., infection, hepatic encephalopathy, hepatorenal syndrome, gastrointestinal bleeding.) Patients who receive antineoplastic or immunomodulatory therapy in the past 12 months. Patients with a previous use of IFN anti hepatitis B virus treatment or have NAs drug resistance. Patients who can't come back to clinic for follow-up on schedule.", "candidate_expression": "((>2 ULN) AND (NAs drug) AND (Patients who can't come back to clinic for follow-up on schedule) AND (Pregnant and lactating women) AND (anti hepatitis B virus) AND (complications) AND (concomitant) AND (important) AND (liver diseases) AND (organ dysfunctions) AND (past 12 months) AND (serious) AND ((autoimmune diseases) OR (diabetes)) AND ((gastrointestinal bleeding) OR (hepatic encephalopathy) OR (hepatorenal syndrome) OR (infection)) AND ((antineoplastic therapy) OR (immunomodulatory therapy)) AND ((IFN) OR (resistance)) AND ((AFP) OR (Hepatocellular Carcinoma) OR (liver cirrhosis) OR (malignancies)) AND ((HIV infection) OR (congenital immune deficiency diseases)))"}
{"candidate_id": "LLM05955", "doc_id": "NCT02284737_inc", "case_bucket": "or", "source_criterion": "Provision of informed consent prior to any study specific procedures; Men and women 18 years and older; Group I PAH, defined as a mPAP=25mmHg, PCWP<15mmHg and PVR[The PVR =(mPAP-PCWP)/CO]>3.0 Woods unit.", "candidate_expression": "(((mPAP-PCWP)/CO) AND (PAH Group I) AND (PCWP <15mmHg) AND (PVR) AND (mPAP =25mmHg) AND (years 18 years and older) AND ((Men) OR (women)))"}
{"candidate_id": "LLM05956", "doc_id": "NCT02632760_inc", "case_bucket": "or", "source_criterion": "Patients with anaemia (males Hb <130 g/L, females <120 g/L) undergoing elective cardiac surgery, and available to receive trial drug 1- 10 weeks prior to surgery", "candidate_expression": "((Hb) AND (anaemia) AND (cardiac surgery elective) AND (females <120 g/L) AND (males <130 g/L) AND (surgery) AND (trial drug available to receive 1- 10 weeks prior to surgery))"}
{"candidate_id": "LLM05957", "doc_id": "NCT00586898_inc", "case_bucket": "or", "source_criterion": "-Patients residing in the following clinical states wit! be considered: A. Rising PSA: Patients with a history of localized disease who have undergone definitive radiation or surgery. These patients must demonstrate progression of disease biochemically as outlined below. Patients in this group may not have radiographically evident disease. B. Non-castrate metastatic: Patients must present with radiographic evidence of metastatic disease at the time of diagnosis or after treatment for localized disease. These patients must show newly detected disease or progressing disease in bone or in soft tissue. Biochemical progression is defined as: minimum no. of determinations: 3 Interval: >2 weeks Minimal Baseline PSA value (ng/ml): 2 Minimal % increase in range of values: 50% Diagnosis of prostate adenocarcinoma histologically confirmed at MSKCC. Patient must have level of serum testosterone above the lower limit of normal. Karnofskcy performance status (KPS) >_70%. Patients must have adequate organ function as defined by the following laboratory criteria: WBC >_3500/mm3, platelet count >_100,000/mm3. Bilirubin <2.0 mg/dl or SGOT <3.0 X the upper limit of normal. Creatinine <_1.6 mg/dl or creatinine clearance >_60 cc/min. Prior hormonal therapy is allowed as: 1. Neoadjuvant treatment prior to radiation therapy or radical prostatectomy, provided that the total duration of exposure does not exceed 10 months. 2. One cycle of intermittent therapy up to a maximum exposure of 10 months. Patients must be at least 18 years of age. Patients must have signed an informed consent document stating that they understand the investigational nature of the proposed treatment", "candidate_expression": "(((ng/ml): 2) AND (10 months) AND (3) AND (50%) AND (<2.0 mg/dl) AND (<3.0 X the upper limit of normal) AND (<_1.6 mg/dl) AND (>2 weeks) AND (>_100,000/mm3) AND (>_3500/mm3) AND (>_60 cc/min) AND (>_70%) AND (Bilirubin) AND (Biochemical progression) AND (Creatinine) AND (Interval) AND (Karnofskcy performance status (KPS)) AND (Minimal % increase in range of values) AND (Minimal Baseline PSA value) AND (Neoadjuvant treatment) AND (Non-castrate) AND (One cycle) AND (PSA) AND (Prior) AND (Rising) AND (SGOT) AND (WBC) AND (above the lower limit of normal) AND (adequate) AND (adequate organ function) AND (after treatment for localized disease) AND (age) AND (at least 18 years) AND (at the time of diagnosis) AND (biochemically) AND (confirmed) AND (creatinine clearance) AND (definitive) AND (disease) AND (disease in bone) AND (disease in soft tissue) AND (does not exceed 10 months) AND (histologically) AND (histologically confirmed) AND (history of) AND (hormonal therapy) AND (intermittent therapy) AND (is allowed) AND (level of serum testosterone) AND (localized disease) AND (maximum exposure) AND (metastatic) AND (metastatic disease) AND (minimum no. of determinations) AND (newly detected) AND (organ function) AND (platelet count) AND (prior to radiation therapy or radical prostatectomy) AND (progressing disease in bone) AND (progressing disease in soft tissue) AND (progression of disease) AND (prostate adenocarcinoma) AND (radiation) AND (radiation therapy) AND (radiation therapy or radical prostatectomy) AND (radical prostatectomy) AND (radiographic) AND (radiographic evidence) AND (radiographically evident) AND (signed an informed consent document) AND (surgery) AND (the time of diagnosis) AND (total duration of exposure) AND (treatment) AND (treatment for localized disease))"}
{"candidate_id": "LLM05958", "doc_id": "NCT01768195_exc", "case_bucket": "or", "source_criterion": "younger than 18 years old HBsAg negative at baseline pregnant or lactating women", "candidate_expression": "((HBsAg negative at baseline) AND (lactating) AND (old younger than 18 years) AND (pregnant) AND (women))"}
{"candidate_id": "LLM05959", "doc_id": "NCT02762851_inc", "case_bucket": "other", "source_criterion": "Age = 18 years and NYHA (New York Heart Association) functional class II, III and IV", "candidate_expression": "((= 18 years) AND (Age) AND (II, III and IV) AND (NYHA (New York Heart Association) functional class))"}
{"candidate_id": "LLM05960", "doc_id": "NCT02859480_exc", "case_bucket": "or", "source_criterion": "Taking other drugs which can influence the lipid profile (eg. Niacin, Fibrates; Serum creatinine level > 2.0 mg/dL Serum aspartate transaminase > 3 times upper limit of normal Serum alanine transaminase > 3 times upper limit of normal Having anaphylactic reaction for Rosuvastatin; Having the other contraindications for Rosuvastatin; Having plan to be pregnant; Having life expectancy less than 1 year", "candidate_expression": "((> 2.0 mg/dL) AND (> 3 times upper limit of normal) AND (Fibrates) AND (Niacin) AND (Rosuvastatin) AND (Serum alanine transaminase) AND (Serum aspartate transaminase) AND (Serum creatinine level) AND (anaphylactic reaction) AND (can influence the lipid profile) AND (contraindications) AND (drugs) AND (less than 1 year) AND (life expectancy) AND (lipid profile) AND (other) AND (plan) AND (pregnant))"}
{"candidate_id": "LLM05961", "doc_id": "NCT03088280_inc", "case_bucket": "other", "source_criterion": "Primary kidney transplant recipients, adults", "candidate_expression": "((adults) AND (kidney transplant Primary))"}
{"candidate_id": "LLM05962", "doc_id": "NCT02969876_inc", "case_bucket": "or", "source_criterion": "Meets Diagnostic and Statistical Manual of Mental Disorders (Versions 4 and 5) criteria for and Major Depressive Disorder. Hamilton Depression Rating Scale-17 score greater than 18. Men and women between ages >=18 and 65.", "candidate_expression": "((Diagnostic and Statistical Manual of Mental Disorders criteria) AND (Hamilton Depression Rating Scale) AND (Major Depressive Disorder) AND (Men) AND (Versions 4) AND (Versions 5) AND (ages) AND (between 18 and 65) AND (greater than 18) AND (women))"}
{"candidate_id": "LLM05963", "doc_id": "NCT00989261_inc", "case_bucket": "or", "source_criterion": "1. Males and females age ≥18 years in second relapse or refractory. 2. Males and females age ≥60 years in first relapse or refractory. 3. Must have baseline bone marrow sample taken. 4. Morphologically documented primary AML or AML secondary to myelodysplastic syndrome (MDS with ≥20% bone marrow or peripheral blasts), as defined by the World Health Organization (WHO) criteria, confirmed by pathology review at treating institution. 5. Able to swallow the liquid study drug. 6. ECOG performance status of 0 to 2 7. In the absence of rapidly progressing disease, the interval from prior treatment to time of AC220 administration will be at least 2 weeks for cytotoxic agents or at least 5 half-lives for noncytotoxic agents. The use of chemotherapeutic or antileukemic agents other than hydroxyurea is not permitted during the study with the possible exception of intrathecal (IT) therapy at the discretion of the Investigator and with the agreement of the Sponsor. 8. Persistent chronic clinically significant non-hematological toxicities from prior treatment must be ≤Grade 1. 9. Prior therapy with FLT3 inhibitors is permitted, except previous treatment with AC220. 10. Serum creatinine ≤1.5 × ULN and glomerular filtration rate (GFR) > 30 mL/min 11. Serum potassium, magnesium, and calcium levels should be at least within institutional normal limits. 12. Total serum bilirubin ≤1.5 × ULN 13. Serum aspartate transaminase (AST) and/or alanine transaminase (ALT) ≤2.5 × ULN 14. Females of childbearing potential must have a negative pregnancy test (urine β-hCG). 15. Females of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study. 16. Written informed consent must be provided.", "candidate_expression": "((AC220) AND (Able to swallow the liquid study drug.) AND (ECOG performance status 0 to 2) AND (FLT3 inhibitors) AND (Females) AND (Females of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study.) AND (Females of childbearing potential must have a negative pregnancy test (urine β-hCG).) AND (MDS) AND (Males) AND (Serum calcium) AND (Serum creatinine ≤1.5 × ULN) AND (Serum magnesium) AND (Serum potassium) AND (Total serum bilirubin ≤1.5 × ULN) AND (World Health Organization (WHO) criteria) AND (Written informed consent must be provided.) AND (age ≥18 years) AND (age ≥60 years) AND (bone marrow sample baseline) AND (childbearing potential) AND (females) AND (glomerular filtration rate (GFR) > 30 mL/min) AND (myelodysplastic syndrome) AND (pathology review) AND (pregnancy test negative) AND (therapy permitted) AND (toxicities clinically significant non-hematological from prior treatment ≤Grade 1) AND (treatment prior ≤Grade 1) AND (urine β-hCG) AND NOT (treatment) AND ((Males) OR (females)) AND ((AML Morphologically documented primary)) AND ((bone marrow) OR (peripheral blasts)) AND ((refractory) OR (relapse)) AND ((Serum aspartate transaminase (AST) ≤2.5 × ULN) OR (alanine transaminase (ALT) ≤2.5 × ULN)))"}
{"candidate_id": "LLM05964", "doc_id": "NCT02952963_inc", "case_bucket": "or", "source_criterion": "Uncomplicated RYGB performed minimum 3 months prior to the study. Fasting glucose < 7,0 mM, HbA1c < 48 mmol/mol 3 months after RYGB", "candidate_expression": "((RYGB) AND (RYGB Uncomplicated minimum 3 months prior to the study) AND ((Fasting glucose < 7,0 mM) OR (HbA1c < 48 mmol/mol)))"}
{"candidate_id": "LLM05965", "doc_id": "NCT02830360_exc", "case_bucket": "or", "source_criterion": "Unable or unwilling to provide informed consent. Active ischemia (acute thrombus diagnosed by coronary angiography, or dynamic ST segment changes demonstrated on ECG) or another reversible cause of VT (e.g. drug-induced arrhythmia), had recent acute coronary syndrome within 30 days, coronary revascularization (<90 days bypass surgery, <30 days percutaneous coronary intervention), or have CCS functional class IV angina. Note that biomarker level elevation alone after ventricular arrhythmias does not denote acute coronary syndrome or active ischemia. Are ineligible to take the antiarrhythmic drug to which they would be assigned due to allergy, intolerance or contraindication Are known to have protruding left ventricular thrombus or mechanical aortic and mitral valves Have had a prior catheter ablation procedure for VT Are in renal failure (Creatinine clearance <15 mL/min), have NYHA Functional class IV heart failure, or a systemic illness likely to limit survival to <1 year Have had recent ST elevation myocardial infarction or non-ST elevation MI (< 30 days); note that biomarker elevation alone after ventricular arrhythmias does not denote MI. Are pregnant.", "candidate_expression": "((< 30 days) AND (<1 year) AND (<15 mL/min) AND (<30 days) AND (<90 days) AND (Active) AND (CCS functional class) AND (Creatinine clearance) AND (ECG) AND (IV) AND (NYHA Functional class) AND (ST elevation myocardial infarction) AND (ST segment changes) AND (Unable or unwilling to provide informed consent) AND (VT) AND (acute coronary syndrome) AND (acute thrombus) AND (allergy) AND (angina) AND (antiarrhythmic drug) AND (bypass surgery) AND (catheter ablation procedure) AND (contraindication) AND (coronary angiography) AND (coronary revascularization) AND (drug-induced arrhythmia) AND (heart failure) AND (intolerance) AND (ischemia) AND (left ventricular thrombus) AND (mechanical aortic valves) AND (mechanical mitral valves) AND (non-ST elevation MI) AND (percutaneous coronary intervention) AND (pregnant) AND (renal failure) AND (reversible) AND (survival) AND (systemic illness) AND (within 30 days,))"}
{"candidate_id": "LLM05966", "doc_id": "NCT02777580_inc", "case_bucket": "other", "source_criterion": "Age equal or greater than 70 years Onset of symptoms < 3 hours prior to randomisation = 2 mm ST-elevation across 2 contiguous precordial leads (V1-V6) or leads I and aVL for a minimum combined total of = 4 mm ST-elevation or = 2 mm ST-elevation in 2 contiguous inferior leads (II, III, aVF) for a minimum combined total of = 4 mm ST-elevation Informed consent received", "candidate_expression": "((< 3 hours prior to randomisation) AND (Age) AND (Informed consent received) AND (Onset of symptoms) AND (equal or greater than 70 years) AND (randomisation))"}
{"candidate_id": "LLM05967", "doc_id": "NCT02825290_exc", "case_bucket": "other", "source_criterion": "PGD patients More than 4 previous embryo transfers", "candidate_expression": "((PGD) AND (embryo transfers More than 4 previous))"}
{"candidate_id": "LLM05968", "doc_id": "NCT02282319_inc", "case_bucket": "other", "source_criterion": "ASA (American Society of Anesthesiologists) class 1 & 2, undergoing day-case knee arthroscopy", "candidate_expression": "((ASA class 1 & 2) AND (knee arthroscopy))"}
{"candidate_id": "LLM05969", "doc_id": "NCT02205502_inc", "case_bucket": "other", "source_criterion": "patients who need suturing for laceration under procedural anesthesia using ketamine", "candidate_expression": "((ketamine) AND (laceration) AND (procedural anesthesia) AND (suturing))"}
{"candidate_id": "LLM05970", "doc_id": "NCT02788045_inc", "case_bucket": "scope", "source_criterion": "Are negative for human immunodeficiency virus (HIV) infection at screening Is healthy on the basis of physical examination, medical history, electrocardiogram (ECG), and vital signs measurement performed at screening Are willing/able to adhere to the prohibitions and restrictions specified in the protocol and study procedures Female participants of childbearing potential must have a negative serum pregnancy test (beta human chorionic gonadotropin [beta hCG]) at the Screening visit, and a negative urine pregnancy test pre-dose on Day 1 Are assessed by the clinic staff as being at low risk for HIV infection", "candidate_expression": "((Are willing/able to adhere to the prohibitions and restrictions specified in the protocol and study procedures) AND (Day 1) AND (Female) AND (HIV infection) AND (Screening visit) AND (at screening) AND (at the Screening visit) AND (beta human chorionic gonadotropin [beta hCG]) AND (childbearing potential) AND (electrocardiogram (ECG)) AND (healthy) AND (human immunodeficiency virus (HIV)) AND (low risk) AND (medical history) AND (negative) AND (physical examination) AND (pre-dose on Day 1) AND (serum pregnancy test) AND (urine pregnancy test) AND (vital signs measurement))"}
{"candidate_id": "LLM05971", "doc_id": "NCT01000155_inc", "case_bucket": "or", "source_criterion": "Diagnosis of sickle cell disease Clinically significant disease defined as at least 1 painful episode per year averaged over the previous 3 years or a history of priapism, stroke, acute chest syndrome, avascular necrosis, multi-organ failure or the need for chronic narcotic medications for pain from sickle cell disease Must have failed a previous attempt at treatment with hydroxyurea defined as the inability to achieve a significant absolute increase in % fetal hemoglobin or the inability to tolerate hydroxyurea treatment due to severe side effects such as but not limited to myelosuppression, gastrointestinal symptoms, edema or hepatic enzyme elevations or have contraindications to hydroxyurea 18 years of age or older Hematologic laboratory values as outlined in the protocol Non-hematologic laboratory values as outlined in the protocol Must agree not to donate blood or other bodily fluid while taking the study drug and for 28 days thereafter Women of child-bearing potential (WCBP) must have a negative serum pregnancy test 72 hours or less prior to starting treatment Women of child-bearing potential and men must agree to use 2 forms of adequate contraception prior to study entry and for the duration of study participation", "candidate_expression": "((18 years or older) AND (2 forms) AND (72 hours or less prior to starting treatment) AND (Clinically significant) AND (Clinically significant disease) AND (Diagnosis) AND (Must agree to) AND (WCBP) AND (Women) AND (Women of child-bearing potential (WCBP) must have a negative serum pregnancy test 72 hours or less prior to starting treatment) AND (acute chest syndrome) AND (adequate) AND (age) AND (avascular necrosis) AND (averaged over the previous 3 years) AND (child-bearing potential) AND (chronic) AND (contraception) AND (donate blood) AND (donate bodily fluid) AND (for 28 days thereafter) AND (for the duration of study participation) AND (history) AND (men) AND (multi-organ failure) AND (must agree to) AND (narcotic medications) AND (need for) AND (negative) AND (not) AND (pain) AND (painful episode) AND (per year averaged over the previous 3 years at least 1) AND (priapism) AND (prior to study entry) AND (serum pregnancy test) AND (sickle cell disease) AND (starting treatment) AND (stroke) AND (study drug) AND (study entry) AND (study participation) AND (taking the study drug) AND (the previous 3 years) AND (treatment) AND (while taking the study drug))"}
{"candidate_id": "LLM05972", "doc_id": "NCT02462317_exc", "case_bucket": "or", "source_criterion": "Previous antispastic drugs Contraindication for baclofen or toxin Antecedent of epileptic seizure Psychiatric antecedent", "candidate_expression": "((Antecedent) AND (Contraindication) AND (Previous) AND (Psychiatric) AND (antecedent) AND (antispastic drugs) AND (baclofen) AND (epileptic seizure) AND (toxin))"}
{"candidate_id": "LLM05973", "doc_id": "NCT03228498_exc", "case_bucket": "or", "source_criterion": "1. Absence of objectionable cognitive impairment or presence of dementia of severe degree defined by CDR score > 2.0. 2. Unavailability of brain MRI (in case of absolute contraindications, the use of cranial CT is allowed). 3. Expected poor compliance with the study protocol. 4. Past diagnosis of major depression, schizophrenia, major anxiety syndrome, or manic- depressive illness. 5. Diagnosis of degenerative cognitive impairment based on clinical and/or neuroradiological findings (i.e., patients with prevailing memory impairment, or with medial temporal atrophy on brain MRI in absence of evident vascular abnormalities; i.e., Alzheimer disease as defined using the National Institute of Neurological and Communicative Disorders and Stroke/Alzheimer's Disease and Related Disorders Association criteria, Parkinson disease, Huntington disease, frontotemporal dementia). 6. Diagnosis of cognitive impairment from other causes (i.e., vitamine B12 and folic acid deficiency, thyroid disorders, metabolic diseases, head trauma, tumor or infections of the central nervous system, normal pressure hydrocephalus). 7. Medical conditions expected to progress, recur, or change to such a degree to interfere with the assessment of the clinical and mental status. 8. Clinically relevant cardiac or pulmonary insufficiency. 9. Relevant electrocardiograph abnormalities; bradycardia (50 bpm) or tachycardia (120 bpm) under resting conditions. 10. Myocardial infarction within the past 6 months. 11. Stroke still requiring neurological rehabilitation. 12. Severe/untreated blood pressure (systolic 180 mm Hg, diastolic 95 mm Hg). 13. Clinically relevant liver function impairment. 14. Insulin-dependent diabetes mellitus. 15. Idiopathic epilepsy and anti-epileptic treatment. 16. Severe anemia (Hb <10 mg/dL). 17. Severe gastrointestinal disease. 18. Cancer. 19. Known intolerance to study drugs. 20. Coexistent serious illnesses that would imply a drop-out before the end of the trial.", "candidate_expression": "((120 bpm) AND (50 bpm) AND (CDR score > 2.0 severe degree) AND (Cancer) AND (Clinically relevant) AND (Hb <10 mg/dL) AND (Idiopathic epilepsy) AND (Insulin-dependent diabetes mellitus) AND (Medical conditions expected to progress, recur, or change to such a degree to interfere with the assessment of the clinical and mental status.) AND (Myocardial infarction within the past 6 months) AND (National Institute of Neurological and Communicative Disorders and Stroke/Alzheimer's Disease and Related Disorders Association criteria) AND (Past diagnosis) AND (Severe) AND (Stroke) AND (Unavailability) AND (abnormalities Relevant) AND (absolute contraindications) AND (anemia Severe) AND (anti-epileptic treatment) AND (blood pressure) AND (brain MRI) AND (clinical and/or neuroradiological findings) AND (cognitive impairment other causes) AND (degenerative cognitive impairment) AND (diastolic 95 mm Hg) AND (electrocardiograph) AND (evident) AND (gastrointestinal disease Severe) AND (intolerance) AND (liver function impairment Clinically relevant) AND (neurological rehabilitation requiring) AND (objectionable) AND (requiring) AND (study drugs) AND (systolic 180 mm Hg) AND NOT (vascular abnormalities) AND ((Severe) OR (untreated)) AND ((cognitive impairment objectionable) OR (dementia)) AND ((cranial CT) OR NOT (brain MRI)) AND ((major anxiety syndrome) OR (major depression) OR (manic- depressive illness) OR (schizophrenia)) AND ((medial temporal atrophy) OR (memory impairment)) AND ((Alzheimer disease) OR (Huntington disease) OR (Parkinson disease) OR (frontotemporal dementia)) AND ((folic acid deficiency) OR (head trauma) OR (infections of the central nervous system) OR (metabolic diseases) OR (normal pressure hydrocephalus) OR (thyroid disorders) OR (tumor of the central nervous system) OR (vitamine B12 deficiency)) AND ((cardiac insufficiency) OR (pulmonary insufficiency)) AND ((bradycardia) OR (tachycardia)))"}
{"candidate_id": "LLM05974", "doc_id": "NCT02277067_inc", "case_bucket": "other", "source_criterion": "Women with a singleton pregnancy undergoing cesarean section after 37 weeks of gestation.", "candidate_expression": "((Women) AND (cesarean section) AND (gestation after 37 weeks) AND (singleton pregnancy))"}
{"candidate_id": "LLM05975", "doc_id": "NCT02859480_inc", "case_bucket": "other", "source_criterion": "Patients underwent percutaneous coronary intervention with drug-eluting stent;", "candidate_expression": "((drug-eluting stent) AND (percutaneous coronary intervention))"}
```
