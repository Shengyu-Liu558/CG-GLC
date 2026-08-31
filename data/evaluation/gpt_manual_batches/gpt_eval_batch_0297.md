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
{"candidate_id": "LLM07401", "doc_id": "NCT03120533_inc", "case_bucket": "other", "source_criterion": "Healthy Volunteers: Age of at least 18 years Existence of a contraceptive method for women of child-bearing age Person affiliated to social security or beneficiary of such a scheme Signed consent form Systemic sclerosis patients: Systemic sclerosis meeting the EULAR criteria. Presence of at least 2 ischemic digital cutaneous ulcerations on two different fingers, with digital ulcers classified as \"active ulcers\" according to the North American working group definition: epithelial denudation is clearly Visible at one place and the bed of de-epithelialized ulcer can be seen; Ulcerations distal to the proximal interphalangeal joint, not associated with calcinosis or bony relief. Ulcers whose major axis measured with the electronic caliper is ≥ 2 mm Age greater than or equal to 18 years Existence of a contraceptive method for women of reproductive age A person who is or is a beneficiary of social security Informed and signed consent signed by the patient or his / her legal representative.", "candidate_expression": "((Age at least 18 years) AND (Age greater than or equal to 18 years) AND (EULAR criteria meeting) AND (North American working group definition epithelial denudation is clearly Visible at one place and the bed of de-epithelialized ulcer can be seen; Ulcerations distal to the proximal interphalangeal joint, not associated with calcinosis or bony relief) AND (Systemic sclerosis) AND (Ulcers) AND (age child-bearing) AND (age reproductive) AND (contraceptive) AND (contraceptive method) AND (digital ulcers active) AND (ischemic digital cutaneous ulcerations at least 2 on two different fingers) AND (major axis measured with the electronic caliper ≥ 2 mm) AND (women))"}
{"candidate_id": "LLM07402", "doc_id": "NCT01490034_inc", "case_bucket": "or", "source_criterion": "Weight stable (<3 kg weight change within last 3 months) Constant habitual activity patterns (no deviation > 1x/wk at 30 min/session within last 3 months) Constant habitual diet patterns within last 3 months Willingness to eat a chocolate-flavored snack at test sessions and two week training period No allergies to any test foods Not planning to change use of medications known to influence appetite or metabolism Not diabetic No history of GI pathology Non-smoker for one year or more", "candidate_expression": "((<3 kg weight change) AND (Constant habitual activity patterns) AND (Constant habitual diet patterns) AND (GI pathology) AND (No) AND (Non) AND (Not) AND (Weight) AND (Willingness to eat a chocolate-flavored snack) AND (allergies) AND (at test sessions) AND (at two week training period) AND (diabetic) AND (for one year or more) AND (history) AND (no deviation > 1x/wk at 30 min/session within last 3 months) AND (planning to change) AND (smoker) AND (stable) AND (test foods) AND (within last 3 months) AND ((medications known to influence appetite) OR (medications known to influence metabolism)))"}
{"candidate_id": "LLM07403", "doc_id": "NCT03390933_exc", "case_bucket": "or", "source_criterion": "on hemodialysis for less than 3 months comorbid psychotic, bipolar, substance use dependence, Alzheimer's or dementia", "candidate_expression": "((Alzheimer's) AND (bipolar) AND (comorbid) AND (dementia) AND (for less than 3 months) AND (hemodialysis) AND (psychotic) AND (substance use dependence))"}
{"candidate_id": "LLM07404", "doc_id": "NCT02312076_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities. Myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Moderate) AND (Myoma) AND (Previous) AND (Uterine abnormalities) AND (endometriosis) AND (severe) AND (uterine surgery))"}
{"candidate_id": "LLM07405", "doc_id": "NCT02606565_exc", "case_bucket": "other", "source_criterion": "Newborns with severe congenital anomalies Newborns with infection of the umbilical cord at birth", "candidate_expression": "((Newborns) AND (infection of the umbilical cord at birth) AND (severe congenital anomalies))"}
{"candidate_id": "LLM07406", "doc_id": "NCT00324363_exc", "case_bucket": "or", "source_criterion": "Have participated in this study previously, or any other study using exenatide or GLP-1 analogs. Have participated in an interventional, medical, surgical, or pharmaceutical study within 30 days of screening. Have characteristics contraindicating metformin or sulfonylurea use. Have been treated with exogenous insulin for more than 1 week within the 3 months prior to screening. Have used drugs for weight loss within 1 month of screening.", "candidate_expression": "((GLP-1 analogs) AND (any other study) AND (characteristics contraindicating) AND (drugs for weight loss) AND (exenatide) AND (exogenous insulin) AND (for more than 1 week) AND (interventional study) AND (medical study) AND (metformin) AND (pharmaceutical study) AND (screening) AND (sulfonylurea) AND (surgical study) AND (this study) AND (within 1 month of screening) AND (within 30 days of screening) AND (within the 3 months prior to screening))"}
{"candidate_id": "LLM07407", "doc_id": "NCT02990403_exc", "case_bucket": "or", "source_criterion": "having experienced severe allergies, trauma history and/or operation history within 3 months. with a history of mental illness and/or family history of mental illness limb disabled. taking medicine within one month. suffering major events or having mood swings. having internal and surgical disease(after having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine) chromosome aberrations in anyone of the couple. patients who have drugs contraindications", "candidate_expression": "((blood routine) AND (chromosome aberrations anyone of the couple anyone of the couple) AND (contraindications) AND (drugs) AND (electrocardiogram) AND (hepatic function) AND (medicine within one month) AND (physical examination) AND (renal function) AND (surgical) AND (urine routine) AND ((mental illness family history limb disabled) OR (mental illness history limb disabled)) AND ((major events) OR (mood swings)) AND ((allergies severe) OR (operation history) OR (trauma history)) AND ((internal disease) OR (surgical disease)))"}
{"candidate_id": "LLM07408", "doc_id": "NCT02749617_exc", "case_bucket": "or", "source_criterion": "Concomitant antiplatelet or anticoagulant use Calculated creatinine clearance < 30 mL/min by Cockcroft-Gault formula Alanine aminotransferase (ALT) or aspartate aminotransferase (AST) > 3 times upper limit of normal (ULN) Total bilirubin > 2 x ULN Thrombocytopenia < 50 x 10 gigalitres (Gl) High bleeding risk or spontaneously prolonged prothrombin time or activated partial thromboplastin time > 1.5 x ULN Body weight <50 or >120 kg Concomitant use of CYP3A4 or p-glycoprotein inducers or inhibitors Use of Ginkgo biloba or St. John's Wort within 14 days before first dose of study drug Dexamethasone use within last 3 months Women of Childbearing potential without proper contraceptive measures, pregnancy or breast feeding Life expectancy less than 3 months Inability to swallow or issues with malabsorption Any other medical, social, logistical, geographical or psychological factors, which in the opinion of the investigator, would prohibit follow-up, compliance and study completion", "candidate_expression": "((Alanine aminotransferase (ALT) > 3 times upper limit of normal (ULN)) AND (Any other medical, social, logistical, geographical or psychological factors, which in the opinion of the investigator, would prohibit follow-up, compliance and study completion) AND (Body weight <50 kg >120 kg) AND (CYP3A4 Concomitant) AND (Calculated creatinine clearance < 30 mL/min) AND (Childbearing potential) AND (Cockcroft-Gault formula) AND (Dexamethasone within last 3 months) AND (Ginkgo biloba) AND (High bleeding risk) AND (Inability to swallow) AND (Life expectancy less than 3 months) AND (St. John's Wort) AND (Thrombocytopenia < 50 x 10 gigalitres (Gl)) AND (Total bilirubin > 2 x ULN) AND (Women) AND (activated partial thromboplastin time > 1.5 x ULN) AND (anticoagulant Concomitant) AND (antiplatelet Concomitant) AND (aspartate aminotransferase (AST) > 3 times upper limit of normal (ULN)) AND (breast feeding) AND (issues with malabsorption) AND (p-glycoprotein inducers Concomitant) AND (p-glycoprotein inhibitors Concomitant) AND (pregnancy) AND (prolonged prothrombin time spontaneously) AND (study drug first dose) AND NOT (contraceptive measures))"}
{"candidate_id": "LLM07409", "doc_id": "NCT02386800_inc", "case_bucket": "other", "source_criterion": "Patient is currently enrolled in a Novartis OGD or GMA-sponsored or Incyte-sponsored clinical study (where Incyte can delegate the sponsorship to a preferred CRO, if applicable) that is approved to enroll into this rollover study, is receiving ruxolitinib and has fulfilled all of the requirements of the parent protocol. Patient is currently benefiting from the treatment with ruxolitinib, as determined by the investigator Patient has demonstrated compliance, as assessed by the investigator, with the parent study protocol requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures Patient currently has no evidence of progressive disease, as determined by the investigator, following previous treatment with ruxolitinib Written informed consent obtained prior to enrolling in roll-over study and receiving study medication. If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness.", "candidate_expression": "((Patient has demonstrated compliance, as assessed by the investigator, with the parent study protocol requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures) AND (Patient is currently enrolled in a Novartis OGD or GMA-sponsored or Incyte-sponsored clinical study (where Incyte can delegate the sponsorship to a preferred CRO, if applicable) that is approved to enroll into this rollover study, is receiving ruxolitinib and has fulfilled all of the requirements of the parent protocol.) AND (Written informed consent obtained prior to enrolling in roll-over study and receiving study medication. If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness) AND (progressive disease) AND (ruxolitinib))"}
{"candidate_id": "LLM07410", "doc_id": "NCT03264911_exc", "case_bucket": "or", "source_criterion": "Hypersensitivity to B-lactams concomitant disease which must be treated with antibiotics chronic disease-Immunocompromised Antibiotics within 72 h history of ARF,scarlet fever,impetigo,acute glomerulonephritis Family history of ARF Complicated pharyngitis", "candidate_expression": "((ARF) AND (Antibiotics) AND (B-lactams) AND (Complicated) AND (Family history) AND (Hypersensitivity) AND (Immunocompromised) AND (acute glomerulonephritis) AND (antibiotics) AND (concomitant) AND (disease) AND (history) AND (impetigo) AND (pharyngitis) AND (scarlet fever) AND (treated) AND (within 72 h))"}
{"candidate_id": "LLM07411", "doc_id": "NCT01909934_exc", "case_bucket": "or", "source_criterion": "Previous treatment with brentuximab vedotin. Previously received an allogeneic transplant. Patients with current diagnosis of primary cutaneous ALCL (patients whose ALCL has transformed to sALCL are eligible). Known cerebral/meningeal disease including signs or symptoms of progressive multifocal leukoencephalopathy (PML) Female patients who are lactating and breastfeeding or pregnant Known human immunodeficiency virus (HIV) positive Known hepatitis B surface antigen-positive, or known or suspected active hepatitis C infection", "candidate_expression": "((Female patients who are lactating and breastfeeding or pregnant) AND (HIV) AND (PML) AND (allogeneic transplant) AND (brentuximab) AND (human immunodeficiency virus positive) AND (progressive multifocal leukoencephalopathy) AND ((hepatitis B surface antigen positive) OR (hepatitis C infection active)) AND ((primary cutaneous ALCL) OR (sALCL)) AND ((cerebral disease) OR (meningeal disease)))"}
{"candidate_id": "LLM07412", "doc_id": "NCT01907230_exc", "case_bucket": "or", "source_criterion": "HCV, HIV, or HDV coinfection. HCC or other malignancy within 3 years. Decompensated liver cirrhosis (CTP score = 7). Uremia patients under hemodialysis or continuous ambulatory peritoneal dialysis or patients with Ccr < 50 mL/min Pregnant or breastfeeding women. Women of child-bearing potential (WOCBP) who are unwilling or unable to use an acceptable method of contraception to avoid pregnancy throughout the study and for up to 4 weeks after the last dose of study drug.", "candidate_expression": "((< 50 mL/min) AND (= 7) AND (CTP score) AND (Ccr) AND (Decompensated liver cirrhosis) AND (HCC) AND (HCV coinfection) AND (HDV coinfection) AND (Pregnant or breastfeeding women) AND (Uremia) AND (Women of child-bearing potential (WOCBP) who are unwilling or unable to use an acceptable method of contraception to avoid pregnancy throughout the study and for up to 4 weeks after the last dose of study drug) AND (coinfection HIV) AND (continuous ambulatory peritoneal dialysis) AND (hemodialysis) AND (malignancy) AND (within 3 years))"}
{"candidate_id": "LLM07413", "doc_id": "NCT03228238_inc", "case_bucket": "scope", "source_criterion": "Subject must be at least 30 years of age. Subject is able to verbally confirm understandings of risks, benefits and treatment alternatives of receiving the Vitamin C+E or Statin or Dual, and he/she or his/her legally authorized representative provides written informed consent prior to any study related procedure. Subject must have symptoms that are consistent with vasospastic angina with planned Coronary angiography and Provocation test.", "candidate_expression": "((Coronary angiography) AND (Provocation test) AND (Subject is able to verbally confirm understandings of risks, benefits and treatment alternatives of receiving the Vitamin C+E or Statin or Dual, and he/she or his/her legally authorized representative provides written informed consent prior to any study related procedure) AND (age at least 30 years) AND (symptoms) AND (vasospastic angina))"}
{"candidate_id": "LLM07414", "doc_id": "NCT01891383_inc", "case_bucket": "or", "source_criterion": "Cases (with a history of TBI): 1. Ages 50-95 years 2. History of traumatic brain injury of sufficient severity to have resulted in medical attention (ascertained via the Ohio State University TBI Identification Questionnaire—OSU TBI-ID, and based on DoD/VA criteria) 3. Residence in AFRH-Washington D.C. or the Veterans Home of California-Yountville 4. MMSE score ≥ 20 5. Capacity to provide consent to participate in research (assessment made by study physician) 6. Ability to read and write English Controls (without a history of TBI): 1. Ages 50-95 years 2. No history of traumatic brain injury of sufficient severity to have resulted in medical attention (ascertained via the Ohio State University TBI Identification Questionnaire—OSU TBI-ID) 3. Residence in AFRH-Washington or the Veterans Home of California-Yountville 4. MMSE score ≥ 20 5. Capacity to provide consent or assent to participate in research 6. Ability to read and write English -", "candidate_expression": "((Ability to read and write English) AND (Ability to read and write English -) AND (Ages 50-95 years) AND (Capacity to provide consent or assent to participate in research) AND (Capacity to provide consent to participate in research (assessment made by study physician)) AND (MMSE score ≥ 20) AND (Ohio State University TBI Identification Questionnaire—OSU TBI-ID sufficient severity) AND (sufficient severity) AND (traumatic brain injury History sufficient severity) AND NOT (traumatic brain injury history sufficient severity) AND ((AFRH-Washington D.C.) OR (Veterans Home of California-Yountville)) AND ((AFRH-Washington) OR (Veterans Home of California-Yountville)))"}
{"candidate_id": "LLM07415", "doc_id": "NCT02205502_exc", "case_bucket": "or", "source_criterion": "contraindication to ketamine and lidocaine patients involved to other studies more or equal to American Society of Anesthesiologist (ASA) class III not alert", "candidate_expression": "((American Society of Anesthesiologist (ASA) class III more or equal to) AND (contraindication) AND (ketamine) AND (lidocaine) AND (not alert) AND (patients involved to other studies))"}
{"candidate_id": "LLM07416", "doc_id": "NCT01501201_exc", "case_bucket": "other", "source_criterion": "Contraindication to bariatric surgery Pregnancy Affiliation of health care assurance Psychiatric disorders", "candidate_expression": "((Affiliation of health care assurance) AND (Contraindication) AND (Pregnancy) AND (Psychiatric disorders) AND (bariatric surgery))"}
{"candidate_id": "LLM07417", "doc_id": "NCT02083991_exc", "case_bucket": "or", "source_criterion": "Diabetes mellitus or plasma glucose >11,1 at admission. Receiving steroids at the time of transplantation or likely to need steroids after transplantation. Multiorgan transplants and/or previously transplanted with any other organ than kidney. Panel reacting antibodies(PRA) >25% in most recent test or considered to be of high risk for rejection which requires an enhanced immunosuppression. Renal transplants from HLA-identical sibling. Hypersensitivity to, or disability to take immunosuppressive drugs. Blood group(ABO)-incompatible transplants. Unlikely to comply with the study requirements. Transplant from donor positive for HIV, HBsAg, Hepatitis C. Female of childbearing potential planing/being pregnant or unwilling to use contraception.", "candidate_expression": "((>11,1) AND (>25%) AND (Blood group(ABO)-incompatible) AND (Diabetes mellitus) AND (Female of childbearing potential planing/being pregnant or unwilling to use contraception.) AND (HLA-identical sibling) AND (Hypersensitivity) AND (Multiorgan transplants) AND (Panel reacting antibodies(PRA)) AND (Receiving) AND (Renal transplants) AND (Transplant) AND (after transplantation) AND (at admission) AND (at the time of transplantation) AND (considered to be of high risk) AND (disability) AND (donor) AND (enhanced immunosuppression) AND (immunosuppressive drugs) AND (likely to need) AND (most recent test) AND (plasma glucose) AND (positive for HBsAg) AND (positive for HIV) AND (positive for Hepatitis C) AND (previously) AND (rejection) AND (steroids) AND (transplantation) AND (transplanted with any other organ than kidney) AND (transplants))"}
{"candidate_id": "LLM07418", "doc_id": "NCT02739295_inc", "case_bucket": "other", "source_criterion": "Toxic epidermal necrolysis with SCORTEN 1 to 5 at admission", "candidate_expression": "((1 to 5) AND (SCORTEN) AND (Toxic epidermal necrolysis) AND (admission) AND (at admission))"}
{"candidate_id": "LLM07419", "doc_id": "NCT03389061_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07420", "doc_id": "NCT02257580_inc", "case_bucket": "scope", "source_criterion": "Scheduled for bilateral varus rotational osteotomy (VRO) with or without associated soft tissue and osseous procedures", "candidate_expression": "((VRO) AND (osseous procedures) AND (procedures soft tissue) AND (varus rotational osteotomy Scheduled for bilateral))"}
{"candidate_id": "LLM07421", "doc_id": "NCT03226080_inc", "case_bucket": "other", "source_criterion": "ASA I-IV Age 55 or older Scheduled for operative repair of isolated intertrochanteric hip fracture", "candidate_expression": "((55 or older) AND (ASA) AND (Age) AND (I-IV) AND (Scheduled for) AND (intertrochanteric hip fracture) AND (isolated) AND (operative repair))"}
{"candidate_id": "LLM07422", "doc_id": "NCT02219880_inc", "case_bucket": "or", "source_criterion": "Aged between 18-70 years Meets the Diagnostic and Statistical Manual (DSM) IV and DSM-V diagnostic criteria for generalised anxiety disorder (GAD) based on structured interview (Mini International Neuropsychiatric Interview-Plus 6 [MINI-Plus 6]. Note that while the MINI-Plus 6 uses the DSM-IV criteria, the same criteria are used in the DSM-V). Presents with anxiety (Hamilton Anxiety Rating Scale = 18) at the time of study entry Fluent in written and spoken English Provides a signed copy of the consent form Primary diagnosis other than GAD Presentation of moderate to severe depressive symptoms (Montgomery-Asberg Rating Scale: MADRS = 18 at time of study entry or = 24 at any time during study) Presentation of suicidal ideation (= 3 on MADRS suicidal thoughts domain at time of study entry or at any time during study) Current diagnosis of bipolar disorder or schizophrenia on structured interview (MINI Plus) Current substance/alcohol use disorder on structured interview (MINI Plus) Page 21 of 39 Commercial-in-Confidence Currently taking an antidepressant, mood stabiliser, antipsychotic, anticonvulsant, warfarin or thyroxin, or current regular use (more than 2 days per week) of a benzodiazepine or opioid-based analgesic Current use of a psychotropic nutraceutical (e.g. St John's wort) Previous intolerance to kava Three or more failed trials of pharmacotherapy for the current GAD episode Recently commenced psychotherapy (within four weeks of study entry) Known or suspected clinically unstable systemic medical disorder Diagnosed hepato-biliary disease/inflammation Elevated liver enzymes at baseline blood test Pregnancy or breastfeeding, or trying to conceive Not using medically approved contraception (including abstinence) if female and of childbearing age Unable to participate in all scheduled visits, treatment plan, or other trial procedures according to the protocol (except for the optional genetic component)", "candidate_expression": "((= 18) AND (= 24) AND (= 3) AND (Aged) AND (Current) AND (Currently) AND (Diagnostic and Statistical Manual (DSM) IV and DSM-V diagnostic criteria) AND (Elevated) AND (GAD) AND (GAD episode) AND (Hamilton Anxiety Rating Scale) AND (Known) AND (MADRS) AND (MADRS suicidal thoughts domain) AND (MINI Plus) AND (Mini International Neuropsychiatric Interview-Plus 6 [MINI-Plus 6]) AND (Montgomery-Asberg Rating Scale) AND (Not) AND (Pregnancy) AND (Previous) AND (Primary diagnosis) AND (Recently) AND (St John's wort) AND (Three or more) AND (Unable to participate) AND (abstinence) AND (age) AND (alcohol use disorder) AND (anticonvulsant) AND (antidepressant) AND (antipsychotic) AND (anxiety) AND (at any time during study) AND (at the time of study entry) AND (at time of study entry) AND (baseline) AND (benzodiazepine) AND (between 18-70 years) AND (bipolar disorder) AND (blood test) AND (breastfeeding) AND (childbearing) AND (childbearing age) AND (clinically unstable) AND (contraception) AND (current) AND (depressive symptoms) AND (except for) AND (failed) AND (female) AND (generalised anxiety disorder) AND (genetic component) AND (hepato-biliary disease) AND (hepato-biliary inflammation) AND (intolerance) AND (kava) AND (liver enzymes) AND (medical disorder) AND (medically approved) AND (moderate to severe) AND (mood stabiliser) AND (more than 2 days per week) AND (opioid-based analgesic) AND (other than) AND (psychotherapy) AND (psychotropic nutraceutical) AND (regular) AND (scheduled visits) AND (schizophrenia) AND (structured interview) AND (substance use disorder) AND (suicidal ideation) AND (suspected) AND (systemic) AND (taking) AND (thyroxin) AND (time of study entry) AND (treatment plan) AND (trial procedures) AND (trials of pharmacotherapy) AND (trying to conceive) AND (use) AND (warfarin) AND (within four weeks of study entry))"}
{"candidate_id": "LLM07423", "doc_id": "NCT01994382_inc", "case_bucket": "or", "source_criterion": "Phase 1 Specific Patient at least 18yrs of age with histologically confirmed CLL/SLL or B-cell Non-Hodgkin lymphoma (DLBCL, FL, MCL, MZL, lymphoplasmacytic lymphoma). Phase 2a Inclusion Histological evidence: FL Grade 1-3A/iNHL, with relapsed or refractory disease (iNHL includes LPL/WM, MZL); aNHL, defined as DLBCL, FL Grade 3B, MCL, and transformed NHL with relapsed disease; CLL/SLL, PTCL, or CTCL (with MF/SS) with relapsed or refractory. Received BCR and/or BCL2 inhibitors were intolerant or had relapsed/refractory disease afterwards. Prior treatment for lymphoid malignancy for progressive /refractory disease ≥ 1 prior regimen (min 2 cycles) with antibody conjugate, cytotoxic chemotherapy, or TKI alone or in combination. Measureable disease defined as: ≥ 1 lesion ≥ 1.5 cm single dimension via CT, CT/PET with nodal or mass lesions; Quantifiable circulating tumor cells; or for Waldenström's macroglobulinemia presence of IgM l > 2X ULN; For CTCL: mSWAT > 0 Ability to provide diagnostic reports General Inclusion ECOG Score of 0 or 1. Hematologic ANC > 1000/uL and platelet > 75,000/uL, Serum creatinine of < 1.5 ULN or calculated CrCl of > 50 mL/min Bilirubin < 20.0mg/dL (if Gilberts then < 2.5 mg/dL) and AST/AST < 2.5 ULN", "candidate_expression": "((0 or 1) AND (1-3A) AND (3B) AND (< 1.5 ULN) AND (< 2.5 ULN) AND (< 2.5 mg/dL) AND (> 0) AND (> 1000/uL) AND (> 2X ULN) AND (> 50 mL/min) AND (> 75,000/uL) AND (AST/AST) AND (Bilirubin) AND (DLBCL) AND (ECOG Score) AND (FL) AND (Grade) AND (Hematologic ANC) AND (Histological) AND (IgM l) AND (MCL) AND (MZL) AND (Measureable disease) AND (afterwards) AND (age) AND (at least 18yrs) AND (confirmed) AND (histologically) AND (intolerant) AND (lymphoid malignancy) AND (lymphoplasmacytic lymphoma) AND (mSWAT) AND (min 2 cycles) AND (platelet) AND (relapsed disease) AND (≥ 1 lesion) AND (≥ 1 prior regimen) AND (≥ 1.5 cm) AND (≥ 1.5 cm single dimension) AND ((FL) OR (iNHL)) AND ((refractory disease) OR (relapsed disease)) AND ((LPL) OR (MZL) OR (WM)) AND ((B-cell Non-Hodgkin lymphoma) OR (CLL) OR (SLL)) AND ((DLBCL) OR (FL) OR (Grade) OR (MCL) OR (transformed NHL)) AND ((CLL) OR (CTCL) OR (PTCL) OR (SLL) OR (aNHL) OR (iNHL)) AND ((MF) OR (SS)) AND ((BCL2 inhibitors) OR (BCR inhibitors)) AND ((refractory disease) OR (relapsed)) AND ((Prior) OR (treatment)) AND ((progressive disease) OR (refractory disease)) AND ((TKI) OR (antibody conjugate) OR (cytotoxic chemotherapy)) AND ((CT) OR (CT/PET)) AND ((mass lesions) OR (nodal lesions)) AND ((CTCL) OR (Waldenström's macroglobulinemia) OR (circulating tumor cells)) AND ((Serum creatinine) OR (calculated CrCl)) AND ((< 20.0mg/dL) OR (Gilberts)))"}
{"candidate_id": "LLM07424", "doc_id": "NCT02478346_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07425", "doc_id": "NCT02627521_exc", "case_bucket": "or", "source_criterion": "Anticoagulation therapy Prior CABG. Active bleeding or at high risk of bleeding Severe liver or renal disease. Hypersensitivity to ticagrelor History of intracranial hemorrhage", "candidate_expression": "((Anticoagulation therapy) AND (CABG Prior) AND (Hypersensitivity) AND (intracranial hemorrhage History) AND (ticagrelor) AND ((bleeding Active) OR (bleeding at high risk)) AND ((disease liver) OR (renal disease)))"}
```
