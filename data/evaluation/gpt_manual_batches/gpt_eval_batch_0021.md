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
{"candidate_id": "LLM00501", "doc_id": "NCT02713087_exc", "case_bucket": "or", "source_criterion": "Age younger than 18 yrs. or older than 75 yrs. Pregnancy or nursing (negative pregnancy blood test) History of allergic reactions to phenylephrine or ephedrine eGFR < 60ml/min/1.73m2", "candidate_expression": "((< 60ml/min/1.73m2) AND (Age) AND (History) AND (Pregnancy) AND (allergic reactions) AND (eGFR) AND (ephedrine) AND (negative) AND (nursing) AND (phenylephrine) AND (pregnancy blood test) AND (younger than 18 yrs. or older than 75 yrs.))"}
{"candidate_id": "LLM00502", "doc_id": "NCT03560310_inc", "case_bucket": "or", "source_criterion": "Written informed consent Age =18 years Has undergone first time isolated CABG due to an episode of acute coronary syndrome (STEMI, NSTEMI, unstable angina) within 6 weeks before surgery", "candidate_expression": "((Age =18 years) AND (Written informed consent) AND (acute coronary syndrome within 6 weeks before surgery) AND (isolated CABG first time) AND ((NSTEMI) OR (STEMI) OR (unstable angina)))"}
{"candidate_id": "LLM00503", "doc_id": "NCT02774317_exc", "case_bucket": "or", "source_criterion": "Patients who are being prepared for surgery, or during or after surgery. Patients with congenital anomalies, chromosomal anomalies, or heart defects. Patients whose parents refuse to consent.", "candidate_expression": "((chromosomal anomalies) AND (congenital anomalies) AND (heart defects) AND (surgery being prepared for during surgery after surgery))"}
{"candidate_id": "LLM00504", "doc_id": "NCT02565277_inc", "case_bucket": "other", "source_criterion": "Subjects who the investigator believes can and will comply with the requirements of the protocol (i.e. return for follow-up visits, and able to converse with study personnel) Age 18 years or older Undergoing major cardiac surgery using cardiopulmonary bypass", "candidate_expression": "((Age 18 years or older) AND (Subjects who the investigator believes can and will comply with the requirements of the protocol (i.e. return for follow-up visits, and able to converse with study personnel) AND (cardiopulmonary bypass) AND (major cardiac surgery))"}
{"candidate_id": "LLM00505", "doc_id": "NCT01942109_inc", "case_bucket": "other", "source_criterion": "heart failure NYHA II-IV previous treatment with diuretics age>18 years", "candidate_expression": "((>18 years) AND (II-IV) AND (NYHA) AND (age) AND (diuretics) AND (heart failure) AND (previous) AND (treatment))"}
{"candidate_id": "LLM00506", "doc_id": "NCT02726009_inc", "case_bucket": "other", "source_criterion": "Has given written informed consent before any study-related activity is performed Advanced hormone-dependent prostate cancer for which androgen deprivation therapy is indicated, and independently from this trial, Firmagon® is intended to be used for treatment Age greater than or equal to 18 years and less than 80 years Advanced hormone-dependent prostate cancer without any other clinically significant disorder Easten Cooperative Oncology Group score = 2 PSA = 2 ng/mL at screening Life expectancy of at least 12 months as per the investigator's judgement", "candidate_expression": "((Age greater than or equal to 18 years and less than 80 years) AND (Easten Cooperative Oncology Group score = 2) AND (Firmagon intended) AND (Has given written informed consent before any study-related activity is performed) AND (Life expectancy at least 12 months) AND (PSA = 2 ng/mL) AND (androgen deprivation therapy) AND (prostate cancer Advanced hormone-dependent))"}
{"candidate_id": "LLM00507", "doc_id": "NCT03296488_exc", "case_bucket": "or", "source_criterion": "Body mass index less than 18 kg/m2 or greater than 30 kg/m2. History of previous open-laparotomy. Surgery with major complication, or need blood transfusion. History of hypersensitivity or adverse reaction to local anesthetics, opioid, or any ingredient of the medications administered in this study. Severe comorbidity. Chronic preoperative opioid consumption. Pregnant or breastfeeding. Inability to use the PCA device.", "candidate_expression": "((Body mass index) AND (Chronic) AND (History) AND (Inability) AND (Pregnant) AND (Severe) AND (Surgery) AND (adverse reaction) AND (blood transfusion) AND (breastfeeding) AND (comorbidity) AND (greater than 30 kg/m2) AND (hypersensitivity) AND (ingredient of the medications administered in this study) AND (less than 18 kg/m2) AND (local anesthetics) AND (major complication) AND (need) AND (open-laparotomy) AND (opioid) AND (preoperative) AND (previous) AND (use the PCA))"}
{"candidate_id": "LLM00508", "doc_id": "NCT02951832_exc", "case_bucket": "or", "source_criterion": "Having experienced severe allergies, trauma history and/or operation history within 3 months; With a history of mental illness and/or family history of mental illness; Limb disabled; Taking medicine within one month; Suffering major events or having mood swings.", "candidate_expression": "((Limb disabled) AND (family history) AND (history) AND (major events) AND (medicine) AND (within 3 months) AND (within one month) AND ((major events) OR (mood swings)) AND ((operation) OR (severe allergies) OR (trauma)) AND ((mental illness)))"}
{"candidate_id": "LLM00509", "doc_id": "NCT03637946_inc", "case_bucket": "or", "source_criterion": "Over 18 years of age; Systemically healthy; Non-smoking; With good oral hygiene; Absent irreversible pulpal alteration; With the presence of a non-carious cervical lesion (LCNCs) that needs to be restored. This lesion should be non-carious, non-retentive, with at least 1 mm and up to 3 mm depth, should involve both enamel and dentin of vital teeth without mobility, and present hypersensitivity; Presence a natural tooth of the same position of the restored tooth, but in the opposite arch of the same jaw to be considered for the positive control; Periodontal parameters : Depth Probing (PS), Visible Plaque Index (IPV), Gingival Index (GI) and Probing Bleed Index (SS). The normal included were: PS = 1 to 3 mm, GI = 0, IPV = score 0 e SS = score 0.", "candidate_expression": "((= 0) AND (= 1 to 3 mm) AND (Absent) AND (Depth Probing (PS)) AND (GI) AND (Gingival Index (GI)) AND (IPV) AND (Non-smoking) AND (Over 18 years) AND (PS) AND (Probing Bleed Index (SS)) AND (SS) AND (Systemically healthy) AND (Visible Plaque Index (IPV)) AND (age) AND (at least 1 mm and up to 3 mm) AND (depth) AND (good oral hygiene) AND (hypersensitivity) AND (involve both enamel and dentin) AND (irreversible pulpal alteration) AND (lesion) AND (needs to be) AND (non-carious) AND (non-carious cervical lesion (LCNCs)) AND (non-retentive) AND (restored) AND (score 0))"}
{"candidate_id": "LLM00510", "doc_id": "NCT02509949_exc", "case_bucket": "or", "source_criterion": "Patients with a history of drug abuse; preoperative history of schizophrenia, epilepsy, parkinsonism, use of cholinesterase inhibitor, inability to communicate in the preoperative period (coma, profound dementia, or language barrier).", "candidate_expression": "((cholinesterase inhibitor) AND (drug abuse history preoperative) AND (epilepsy) AND (history) AND (inability to communicate) AND (language barrier) AND (parkinsonism) AND (schizophrenia) AND ((coma) OR (profound dementia)))"}
{"candidate_id": "LLM00511", "doc_id": "NCT02833623_inc", "case_bucket": "or", "source_criterion": "outpatients aged 18-70 years confirmed diagnosis of H. pylori infection by at least one of the following methods: 13C-urea breath test, histology, rapid urease test or bacterial culture an intention of H. pylori eradication treatment and have written inform consent ability to read short messages on the mobile phone", "candidate_expression": "((13C-urea breath test) AND (H. pylori infection) AND (ability to read short messages on the mobile phone) AND (aged 18-70 years) AND (an intention of H. pylori eradication treatment and have written inform consent) AND (bacterial culture) AND (histology) AND (outpatients) AND (rapid urease test))"}
{"candidate_id": "LLM00512", "doc_id": "NCT02606565_inc", "case_bucket": "other", "source_criterion": "Newborns weighing 1.5kg or more at birth", "candidate_expression": "((1.5kg or more) AND (Newborns) AND (at birth) AND (weighing))"}
{"candidate_id": "LLM00513", "doc_id": "NCT03228017_exc", "case_bucket": "or", "source_criterion": "Unable to speak Spanish or English Active smoking (within the past year) Autoimmune, rheumatologic or inflammatory disease which are not psoriasis or psoriatic arthritis Known active cancer receiving treatment Pregnancy Anemia (hemoglobin < 9 mg/dl) or thrombocytopenia (Platelet count <75), or thrombocytosis (Platelet count >600) A history of severe bleeding or bleeding disorders Current medication use which interact with either aspirin or atorvastatin Chronic kidney disease (CrCl < 30ml/min) Congestive heart failure Currently taking aspirin or a statin. NSAID use within the past 48 hours", "candidate_expression": "((< 30ml/min) AND (< 9 mg/dl) AND (<75) AND (>600) AND (Active) AND (Chronic kidney disease) AND (Congestive heart failure) AND (CrCl) AND (Current) AND (NSAID) AND (Platelet count) AND (Pregnancy) AND (active) AND (aspirin) AND (bleeding) AND (bleeding disorders) AND (cancer) AND (hemoglobin) AND (history) AND (interact) AND (medication) AND (not) AND (severe) AND (smoking) AND (statin) AND (treatment) AND (within the past 48 hours) AND (within the past year) AND ((Anemia) OR (thrombocytopenia) OR (thrombocytosis)) AND ((aspirin) OR (atorvastatin)) AND ((disease Autoimmune) OR (disease rheumatologic) OR (inflammatory disease)) AND ((psoriasis) OR (psoriatic arthritis)))"}
{"candidate_id": "LLM00514", "doc_id": "NCT03506477_inc", "case_bucket": "or", "source_criterion": "Provide written, signed and dated informed consent prior to initiating any study-related activities. Male or female >18 years of age at the time of screening Fitzpatrick Skin phototype IV-VI, non-white race/ethnicity, including but not limited to - --African Americans, Asians, Pacific Islanders and Hispanics. Clinical diagnosis of chronic plaque-type psoriasis of the body Plaque psoriasis with =2% Body Surface Area (BSA) involvement (may include scalp involvement), PASI Score = 2, IGA mod 2011 score of 2 or greater (based on scale of 0-4) Females of childbearing potential (FCBP) must have a negative pregnancy test at Screening and Baseline. While using investigational product and for at least 28 days after last application of investigational product, FCBP who engage in activity in which conception is possible must use one of the approved contraceptive options d Must be in general good health as judged by the Investigator, based on medical history and physical examination.", "candidate_expression": "((Females of childbearing potential (FCBP) must have a negative pregnancy test at Screening and Baseline. While using investigational product and for at least 28 days after last application of investigational product, FCBP who engage in activity in which conception is possible must use one of the approved contraceptive options d) AND (Fitzpatrick Skin phototype IV-VI) AND (Plaque psoriasis) AND (Provide written, signed and dated informed consent prior to initiating any study-related activities.) AND (age >18 years of age) AND (involvement =2% Body Surface Area (BSA)) AND (non-white race/ethnicity) AND (psoriasis of the body chronic plaque-type) AND (scale of 0-4) AND ((African Americans) OR (Asians) OR (Hispanics) OR (Pacific Islanders)) AND ((Male) OR (female)) AND ((IGA mod 2011 score 2 or greater) OR (PASI Score = 2)))"}
{"candidate_id": "LLM00515", "doc_id": "NCT02965027_inc", "case_bucket": "or", "source_criterion": "Male and female Active-duty SMs or Veterans aged 18 or older who are in good general health. History of blast and/or impact head trauma mTBI meeting Defense and Veterans Brain Injury Center (DVBIC) mTBI criteria, which define mTBI as an injury to the head causing at least one of the following: alteration in consciousness (for up to 24 hours after the injury), loss of consciousness 0-30 minutes, and/or post-traumatic amnesia up to 1 day post-injury. If available, the Glasgow Coma Scale score must be 13-15, and head imaging findings (if imaging was performed) must be negative. Frequent HAs that started within 3months after a head injury. The HAs either 1) must last 4 or more hours a day and reach a moderate to severe intensity at any point during the headache, or 2) may be of any severity or duration if the participant takes a triptan or ergotamine. HAs meeting these criteria must have been present on average at least 8 days per 4-week period, starting within 30 days after head injury and occurring by self-report for at least 3 months prior to the Initial Screening Visit. The 4-week HA frequency/severity criteria must be confirmed during the Preliminary Screening Period. Women of childbearing potential must agree to abstain from sexual relations that could result in pregnancy or use an effective method of birth control acceptable to both participant and the clinician prescriber during the study. Men are not required to use contraception during the study. Participants must have English fluency sufficient to complete study measures.", "candidate_expression": "((0-30 minutes) AND (13-15) AND (18 or older) AND (Active-duty SMs) AND (Defense and Veterans Brain Injury Center (DVBIC) mTBI criteria) AND (Frequent) AND (Glasgow Coma Scale) AND (HAs) AND (History of) AND (Male) AND (Veterans) AND (Women of childbearing potential must agree to abstain from sexual relations that could result in pregnancy or use an effective method of birth control acceptable to both participant and the clinician prescriber during the study. Men are not required to use contraception during the study.) AND (a head injury) AND (aged) AND (alteration in consciousness) AND (at least 3 months prior to the Initial Screening Visit) AND (at least 8 days per 4-week period) AND (blast) AND (ergotamine) AND (female) AND (findings) AND (for up to 24 hours after the injury) AND (good general health) AND (head imaging) AND (impact head trauma) AND (last 4 or more hours a day) AND (loss of consciousness) AND (meeting) AND (moderate to severe intensity) AND (negative) AND (post-traumatic amnesia) AND (the Initial Screening Visit) AND (the injury) AND (triptan) AND (up to 1 day post-injury) AND (within 30 days after head injury) AND (within 3months after a head injury))"}
{"candidate_id": "LLM00516", "doc_id": "NCT03472495_inc", "case_bucket": "or", "source_criterion": ">/= 18 years old Atrial fibrillation or flutter on electrocardiogram Heart rate >110 beats/min Systolic blood pressure >/= 90 mmHg", "candidate_expression": "((>/= 18 years old) AND (>/= 90 mmHg) AND (>110 beats/min) AND (Heart rate) AND (Systolic blood pressure) AND (electrocardiogram) AND (old) AND ((Atrial fibrillation) OR (Atrial flutter)))"}
{"candidate_id": "LLM00517", "doc_id": "NCT03555526_inc", "case_bucket": "other", "source_criterion": "H pylori infection failed after at least two eradication therapies aged 20 years or greater willingness to receive rescue therapy", "candidate_expression": "((20 years or greater) AND (H pylori infection) AND (aged) AND (at least two) AND (eradication therapies) AND (failed) AND (rescue therapy) AND (willingness))"}
{"candidate_id": "LLM00518", "doc_id": "NCT02156999_exc", "case_bucket": "or", "source_criterion": "Kidney, parathyroid, congenital bone metabolic disease", "candidate_expression": "((Kidney) AND (bone) AND (congenital) AND (disease) AND (metabolic) AND (parathyroid))"}
{"candidate_id": "LLM00519", "doc_id": "NCT02732080_exc", "case_bucket": "or", "source_criterion": "Recanalized (TIMI I-III flow) IRA at coronary angiography. Patients in whom TIMI-3 flow was not able to be established after wire crossing, balloon angioplasty or thrombectomy. STEMI due to bypass-graft occlusion Severe heart failure or cardiogenic shock", "candidate_expression": "((IRA) AND (Recanalized) AND (STEMI) AND (Severe) AND (TIMI I-III flow) AND (bypass-graft) AND (coronary angiography) AND (occlusion) AND ((cardiogenic shock) OR (heart failure)))"}
{"candidate_id": "LLM00520", "doc_id": "NCT01084993_inc", "case_bucket": "or", "source_criterion": "At least two of the following additional criteria At least 70 yrs old Female gender Diabetes Creatinine clearance <60mL/min History of gastro-intestinal or other organ bleeding Baseline anemia Current treatment with glycoproteins IIb-IIIa inhibitors", "candidate_expression": "((<60mL/min) AND (At least 70 yrs) AND (At least two) AND (Baseline) AND (Creatinine clearance) AND (Current) AND (Diabetes) AND (Female) AND (History) AND (anemia) AND (gastro-intestinal bleeding) AND (glycoproteins IIb-IIIa inhibitors) AND (old) AND (organ bleeding) AND (other) AND (treatment))"}
{"candidate_id": "LLM00521", "doc_id": "NCT02340169_inc", "case_bucket": "or", "source_criterion": "Patients aged 7 years and older must have provided written assent accompanied by written informed consent from patient's representative Clinical diagnosis of stable plaque psoriasis with involvement of = 10% body surface area (excluding face and scalp) Physicians Global Assessment score of 3 or 4 at baseline", "candidate_expression": "((Physicians Global Assessment score at baseline) AND (aged 7 years and older) AND (body surface area = 10%) AND (must have provided written assent accompanied by written informed consent from patient's representative) AND (plaque psoriasis stable) AND ((3) OR (4)) AND ((face) OR (scalp)))"}
{"candidate_id": "LLM00522", "doc_id": "NCT02745704_exc", "case_bucket": "or", "source_criterion": "Patients with liver cirrhosis, Hepatocellular Carcinoma or other malignancies. Patients with other factors causing liver diseases. Pregnant and lactating women. Patients with concomitant HIV infection or congenital immune deficiency diseases. Patients with diabetes, autoimmune diseases. Patients with important organ dysfunctions. Patients with serious complications (e.g., infection, hepatic encephalopathy, hepatorenal syndrome, gastrointestinal bleeding.) Patients who receive antineoplastic or immunomodulatory therapy in the past 12 months. Patients who can't come back to clinic for follow-up on schedule.", "candidate_expression": "((HIV infection concomitant) AND (Hepatocellular Carcinoma) AND (Patients who can't come back to clinic for follow-up on schedule) AND (Pregnant and lactating women) AND (antineoplastic therapy) AND (autoimmune diseases) AND (complications serious) AND (congenital immune deficiency diseases.) AND (diabetes) AND (gastrointestinal bleeding) AND (hepatic encephalopathy) AND (hepatorenal syndrome) AND (immunomodulatory therapy) AND (infection) AND (liver cirrhosis) AND (malignancies) AND (organ dysfunctions))"}
{"candidate_id": "LLM00523", "doc_id": "NCT00401245_inc", "case_bucket": "or", "source_criterion": "Generally healthy, postmenopausal woman who seeks treatment for hot flushes. Meets 1 of the following: At least 12 months of spontaneous amenorrhea; At least 6 months of spontaneous amenorrhea with serum follicle-stimulating hormone (FSH) levels > 40 mIU/mL; At least 6 weeks postsurgical bilateral oophorectomy (with or without hysterectomy). Hysterectomized without bilateral oophorectomy and with serum FSH levels >40 mIU/mL.", "candidate_expression": "((Hysterectomized) AND (bilateral oophorectomy) AND (healthy) AND (hot flushes Meets 1 of the following) AND (postmenopausal) AND (serum FSH levels >40 mIU/mL) AND (serum follicle-stimulating hormone (FSH) levels > 40 mIU/mL) AND (spontaneous amenorrhea At least 12 months) AND (spontaneous amenorrhea At least 6 months) AND (woman) AND NOT (bilateral oophorectomy) AND ((bilateral oophorectomy with hysterectomy) OR (bilateral oophorectomy without hysterectomy)))"}
{"candidate_id": "LLM00524", "doc_id": "NCT01497639_exc", "case_bucket": "other", "source_criterion": "previous brain surgery; cognitive impairment (< 120 points on the Mattis Dementia Rating Scale) moderate-to-severe depression (> 25 points on the Beck Depression Inventory) marked brain atrophy as detected by magnetic resonance imaging other medical or psychiatric coexisting disorders that could increase the surgical risk or interfere with completion of the trial", "candidate_expression": "((Beck Depression Inventory > 25 points) AND (Mattis Dementia Rating Scale < 120 points) AND (brain atrophy) AND (brain surgery previous) AND (cognitive impairment) AND (depression moderate-to-severe) AND (magnetic resonance imaging) AND (other medical or psychiatric coexisting disorders that could increase the surgical risk or interfere with completion of the trial))"}
{"candidate_id": "LLM00525", "doc_id": "NCT03252249_inc", "case_bucket": "other", "source_criterion": "Aged =18 years Clinical diagnosis of acute coronary syndrome In the opinion of the attending clinician requires dual anti-platelet therapy with aspirin and a P2Y12 receptor antagonist Resident in Scotland with a Community Health Index (CHI) number The attending clinician has equipoise regarding the duration of therapy Provision of informed consent", "candidate_expression": "((Aged =18 years) AND (P2Y12 receptor antagonist) AND (Provision of informed consent) AND (Resident) AND (Scotland) AND (acute coronary syndrome) AND (aspirin) AND (dual anti-platelet therapy requires))"}
```
