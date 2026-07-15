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
{"candidate_id": "LLM04176", "doc_id": "NCT03382106_exc", "case_bucket": "or", "source_criterion": "Women only: Cannot be pregnant or nursing at baseline or plan to become pregnant during the course of the study Body Mass Index (BMI) > 32 Weight > 220 pounds Allergies to shell fish, seafood, eggs or iodine Heart disease, kidney disease or diabetes Diagnosis of asthma Any metal in or on the body (that cannot be removed) between the nose and the abdomen Any major organ system disease (by judgment of the study medical team) A glomerular filtration rate of 60 cc per minute or less. Nitroglycerin usage or nitrates and use of phosphodiesterase 5 (PDE5) inhibitors Prior history of hypersensitivity to sildenafil Currently prescribed a phosphodiesterase (PDE) inhibitors medication (ex: Viagra, Cialis, etc) Known Pulmonary Hypertension Has used e-cigarettes and marijuana <1 years", "candidate_expression": "((Allergies) AND (Body Mass Index (BMI) > 32) AND (Cannot be pregnant or nursing at baseline or plan to become pregnant during the course of the study) AND (Cialis) AND (Heart disease) AND (Nitroglycerin) AND (Pulmonary Hypertension) AND (Viagra) AND (Weight > 220 pounds) AND (Women) AND (asthma) AND (diabetes) AND (eggs) AND (glomerular filtration rate 60 cc per minute or less) AND (hypersensitivity Prior history) AND (iodine) AND (kidney disease) AND (major organ system disease) AND (metal in the body) AND (metal on the body) AND (nitrates) AND (phosphodiesterase (PDE) inhibitors) AND (phosphodiesterase 5 (PDE5) inhibitors) AND (seafood) AND (shell fish) AND (sildenafil) AND (used e-cigarettes) AND (used marijuana))"}
{"candidate_id": "LLM04177", "doc_id": "NCT02779374_exc", "case_bucket": "or", "source_criterion": "Abnormal karyotype Previous pelvic or abdominal radiotherapy Previous surgical management of ovarian pathology Chronic disease: renal, liver, cardiac, malignancy", "candidate_expression": "((Abnormal karyotype) AND (Chronic disease) AND (abdominal radiotherapy) AND (cardiac malignancy) AND (liver malignancy) AND (ovarian pathology) AND (pelvic radiotherapy) AND (renal malignancy) AND (surgical management Previous))"}
{"candidate_id": "LLM04178", "doc_id": "NCT02337764_inc", "case_bucket": "other", "source_criterion": "The participant has a diagnosis of Parkinson's disease according to the diagnostic criteria of the UK Parkinson's Disease Society Brain Bank. The participant has received a levodopa combination drug for >= 1 month and has either of the following. Wearing off phenomenon Decreased response to levodopa combination drugs The participant has received a levodopa combination drug without change in the dose regimen. The participant is an outpatient of either sex aged >= 30 and < 80 years.", "candidate_expression": "((>= 1 month) AND (>= 30 and < 80 years) AND (Decreased response) AND (Parkinson's disease) AND (UK Parkinson's Disease Society Brain Bank) AND (Wearing off phenomenon) AND (aged) AND (evodopa combination drugs) AND (levodopa combination) AND (levodopa combination drug) AND (without change in the dose regimen))"}
{"candidate_id": "LLM04179", "doc_id": "NCT03404804_inc", "case_bucket": "other", "source_criterion": "Children aged 3-16 with a parent/guardian (hereafter termed parent) reported history of allergy to a penicillin antibiotic in which the reported allergic reaction occurred at least six months prior to the current PED visit. Only children well enough to be discharged to home at the conclusion of the PED visit are eligible.", "candidate_expression": "((3-16) AND (Children) AND (PED) AND (aged) AND (allergic reaction) AND (allergy) AND (at least six months prior to the current PED visit) AND (at the conclusion of the PED visit) AND (penicillin antibiotic) AND (the conclusion of the PED visit) AND (well enough to be discharged to home))"}
{"candidate_id": "LLM04180", "doc_id": "NCT03513757_inc", "case_bucket": "other", "source_criterion": "All children scheduled for outpatient MRI scans with expected duration of scan between 30 minutes and 75 minutes.", "candidate_expression": "((MRI scans outpatient) AND (expected duration of scan between 30 minutes and 75 minutes))"}
{"candidate_id": "LLM04181", "doc_id": "NCT02888704_exc", "case_bucket": "or", "source_criterion": "Subjects who have systemic infection Subjects who have human Immunodeficiency virus (HIV), hepatitis B virus (HBV), and hepatitis C virus (HCV) Subjects who need to take the medicine which is prohibited during this study Subjects who have asthma Subjects who can not stop treatment with topical steroids (group 1~5), oral antibiotics, whole body photochemotherapy, immunosuppressive drug within 4 weeks before the treatment visit Pregnant, breast-feeding women or women who plan to become pregnant during this study (Females of childbearing potential must have a negative urine pregnancy test) Subjects who currently participate in other clinical trial or participated in other clinical trial within 30 days Subjects who had a serious adverse events during stem cell therapy Subjects who had a hypersensitivity to antibiotics or antimycotics Subjects who creatinine value is more than two times of the upper limit of the normal range at screening test Subjects who aspartate transaminase/alkaline transaminase (AST/ALT) value is more than three times of the upper limit of the normal range at screening test Subjects who have any other condition which the investigator judges would make patients unsuitable for study participation", "candidate_expression": "((Females) AND (Pregnant) AND (antibiotics) AND (antimycotics) AND (any other condition) AND (aspartate transaminase/alkaline transaminase (AST/ALT)) AND (asthma) AND (at screening test) AND (breast-feeding) AND (childbearing potential) AND (creatinine) AND (during) AND (during this study) AND (hepatitis B virus (HBV)) AND (hepatitis C virus (HCV)) AND (human Immunodeficiency virus (HIV)) AND (hypersensitivity) AND (immunosuppressive drug) AND (more than three times of the upper limit of the normal range) AND (more than two times of the upper limit of the normal range) AND (negative) AND (oral antibiotics) AND (pregnant) AND (screening test) AND (serious adverse events) AND (stem cell therapy) AND (systemic infection) AND (the investigator judges would make patients unsuitable for study participation) AND (topical steroids) AND (treatment visit) AND (urine pregnancy test) AND (whole body photochemotherapy) AND (within 4 weeks before) AND (women))"}
{"candidate_id": "LLM04182", "doc_id": "NCT02528136_inc", "case_bucket": "other", "source_criterion": "Healthy pregnant women age 18 to 50 Singleton pregnancy at gestational age 36 weeks or more Able to read and understand Norwegian.", "candidate_expression": "((18 to 50) AND (36 weeks or more) AND (Able to read and understand Norwegian) AND (Healthy) AND (Singleton pregnancy) AND (age) AND (gestational age) AND (pregnant) AND (women))"}
{"candidate_id": "LLM04183", "doc_id": "NCT02565277_inc", "case_bucket": "other", "source_criterion": "Subjects who the investigator believes can and will comply with the requirements of the protocol (i.e. return for follow-up visits, and able to converse with study personnel) Age 18 years or older Undergoing major cardiac surgery using cardiopulmonary bypass", "candidate_expression": "((18 years or older) AND (Age) AND (Subjects who the investigator believes can and will comply with the requirements of the protocol (i.e. return for follow-up visits, and able to converse with study personnel) AND (cardiopulmonary bypass) AND (major cardiac surgery))"}
{"candidate_id": "LLM04184", "doc_id": "NCT02868437_inc", "case_bucket": "other", "source_criterion": "Subject has curettage for retained product after second trimester abortion", "candidate_expression": "((abortion) AND (curettage) AND (retained product) AND (second trimester))"}
{"candidate_id": "LLM04185", "doc_id": "NCT01312012_inc", "case_bucket": "other", "source_criterion": "pregnant women in 30 to 32 weeks of gestation, with positive HBsAg and HBeAg,serum viral load above 8log10 copies per mL", "candidate_expression": "((30 to 32 weeks) AND (HBeAg) AND (HBsAg) AND (above 8log10 copies per mL) AND (gestation) AND (positive) AND (pregnant) AND (serum viral load) AND (women))"}
{"candidate_id": "LLM04186", "doc_id": "NCT00455663_inc", "case_bucket": "or", "source_criterion": "Diagnosis of schizophrenia or schizoaffective disorder If entering the study as an inpatient, hospitalization was recent Currently receiving treatment with an atypical antipsychotic and continuation on the medication has been recommended Assumes primary responsibility for taking medication Currently living in a stable environment", "candidate_expression": "((Currently) AND (atypical antipsychotic) AND (continuation on the medication) AND (hospitalization) AND (inpatient) AND (living in a stable environment) AND (recent) AND (recommended) AND (treatment) AND ((schizoaffective disorder) OR (schizophrenia)))"}
{"candidate_id": "LLM04187", "doc_id": "NCT02877485_inc", "case_bucket": "other", "source_criterion": "Age greater than 18 NOSE score greater than 55 Nasal septal deviation on exam", "candidate_expression": "((Age) AND (NOSE score) AND (Nasal septal deviation) AND (greater than 18) AND (greater than 55))"}
{"candidate_id": "LLM04188", "doc_id": "NCT02951754_exc", "case_bucket": "or", "source_criterion": "Contraindication for IR-MPH use Current stimulant treatment Evidence of a clinically significant neurological disease that might affect cognition (e.g., delirium, dementia, epilepsy, head trauma, and multiple sclerosis) Current or past history of psychosis Estimated intelligence quotient score lower than 70", "candidate_expression": "((Contraindication) AND (Current) AND (Estimated intelligence quotient score) AND (Evidence) AND (IR-MPH) AND (clinically significant) AND (history) AND (lower than 70) AND (might affect cognition) AND (neurological disease) AND (psychosis) AND (stimulant treatment) AND ((Current) OR (past)) AND ((delirium) OR (dementia) OR (epilepsy) OR (head trauma) OR (multiple sclerosis)))"}
{"candidate_id": "LLM04189", "doc_id": "NCT02466113_inc", "case_bucket": "other", "source_criterion": "The informed consent has been obtained from the patient. With confirmed diagnosis of stage II colon cancer. With moderate/good ECOG health rating (PS): 0-1 score. The patient receive no anti-cancer treatment before primary surgery. The patient receive radical operation for colon cancer with negative margin.", "candidate_expression": "((0-1 score) AND (ECOG health rating (PS)) AND (The informed consent has been obtained from the patient.) AND (anti-cancer treatment) AND (before primary surgery) AND (colon cancer) AND (moderate/good) AND (no) AND (primary surgery) AND (radical operation negative margin) AND (stage II))"}
{"candidate_id": "LLM04190", "doc_id": "NCT02427295_inc", "case_bucket": "other", "source_criterion": "Age 18 or older. Patients diagnosed with acromegaly with GH-secreting pituitary adenoma on sellar MRI, meeting the biochemical criteria outlined above (refer to 1. Diagnosis of acromegaly) and with typical acromegalic features. No prior use of somatostatin analogues. Adequate hepatic and renal function Provision of a signed written informed consent", "candidate_expression": "((Adequate hepatic function) AND (Adequate renal function) AND (Age 18 or older) AND (GH-secreting pituitary adenoma) AND (Provision of a signed written informed consent) AND (acromegalic features typical) AND (acromegaly biochemical criteria outlined above) AND (sellar MRI) AND NOT (somatostatin analogues prior))"}
{"candidate_id": "LLM04191", "doc_id": "NCT02883400_exc", "case_bucket": "other", "source_criterion": "dual organ transplant", "candidate_expression": "(organ transplant dual)"}
{"candidate_id": "LLM04192", "doc_id": "NCT01799681_exc", "case_bucket": "or", "source_criterion": "any neurological conditions other than PD; significant musculoskeletal or cardiopulmonary diseases; other disorders that may affect balance or locomotion; taken any structured behavioral or exercise programs in the past 3 months or they are receiving regular physical rehabilitation at present; unstable condition on anti-parkinsonian medications; surgical interventions for PD; communication or cognitive deficits with mini-mental state examination, (MMSE) <24/30 (Folstein et al., 1975); a history of more than two falls in the previous 12 months.", "candidate_expression": "((PD) AND (anti-parkinsonian medications) AND (cardiopulmonary diseases) AND (cognitive deficits) AND (communication deficits) AND (disorders that may affect balance or locomotion) AND (falls history more than two in the previous 12 months) AND (mini-mental state examination, (MMSE) <24/30) AND (musculoskeletal diseases) AND (neurological conditions) AND (regular physical rehabilitation at present) AND (significant) AND (structured behavioral programs) AND (structured exercise programs) AND (surgical interventions for PD) AND (unstable condition) AND NOT (PD))"}
{"candidate_id": "LLM04193", "doc_id": "NCT02731794_exc", "case_bucket": "other", "source_criterion": "myocardial infarction within the preceding 4 weeks severe valve disease requiring valve replacement cardiac reoperations", "candidate_expression": "((cardiac reoperations) AND (myocardial infarction) AND (requiring valve replacement) AND (severe) AND (the preceding 4 weeks) AND (valve disease) AND (valve replacement) AND (within the preceding 4 weeks))"}
{"candidate_id": "LLM04194", "doc_id": "NCT02905890_inc", "case_bucket": "other", "source_criterion": "BV positive by Nugent score HIV negative Capable of providing written informed consent", "candidate_expression": "((BV) AND (Capable of providing written informed consent) AND (HIV) AND (Nugent score) AND (negative) AND (positive))"}
{"candidate_id": "LLM04195", "doc_id": "NCT03511521_inc", "case_bucket": "or", "source_criterion": "Patients receiving once daily dosing of methylprednisolone or prednisone in a dose of 10 mg/day or greater Hyperglycemic (Glucose level > 126 mg/dL) Diabetic and nondiabetic patients Expected duration of hospital stay and time on steroids >= 3 days Patient of appropriate caregiver able to give Informed Consent", "candidate_expression": "((10 mg/day or greater) AND (> 126 mg/dL) AND (>= 3 days) AND (Expected duration of hospital stay) AND (Glucose level) AND (Hyperglycemic) AND (Patient of appropriate caregiver able to give Informed Consent) AND (once daily) AND (time on steroids) AND ((Diabetic) OR (nondiabetic)) AND ((methylprednisolone) OR (prednisone)))"}
{"candidate_id": "LLM04196", "doc_id": "NCT02974686_exc", "case_bucket": "or", "source_criterion": "Dual organ or kidney after another solid organ transplant Presence of a preexisting significant GI condition that does not have a presumed causal relationship with MPA Evidence of any GI disorder induced by an infection, underlying medical condition, or concomitant medication other than MPA eGFR<40 ml/min at time of possible conversion Proteinuria >1 gram/day at time of possible conversion Hemoglobin <10 g/dL WBC <3 K/cumm Platelets <100 K/cumm Wound healing issues at time of possible conversion (eg, wound dehiscence, wound infection, incisional hernia, lymphocele, seroma) Elevated total cholesterol (>350 mg/dL) and/or triglycerides (>500 ng/dL) at time of possible conversion Hypersensitivity to everolimus, sirolimus, or other rapamycin deriviatives", "candidate_expression": "((<10 g/dL) AND (<100 K/cumm) AND (<3 K/cumm) AND (<40 ml/min) AND (>1 gram/day) AND (>350 mg/dL) AND (>500 ng/dL) AND (Elevated) AND (GI condition) AND (Hemoglobin) AND (Hypersensitivity) AND (MPA) AND (Platelets) AND (Proteinuria) AND (WBC) AND (Wound healing issues) AND (at time of possible conversion) AND (eGFR) AND (induced by an infection) AND (infection) AND (other than) AND (preexisting) AND (significant) AND (solid organ transplant) AND (total cholesterol) AND (triglycerides) AND ((Dual kidney) OR (Dual organ)) AND ((incisional hernia) OR (lymphocele) OR (seroma) OR (wound dehiscence) OR (wound infection)) AND ((everolimus) OR (rapamycin) OR (sirolimus)) AND ((GI disorder) OR (medication) OR (underlying medical condition)))"}
{"candidate_id": "LLM04197", "doc_id": "NCT00500500_inc", "case_bucket": "other", "source_criterion": "female or male of 50 to 85 years old with a care giver Mini Mental Status (MMS) test between 16 to 26 inclusive Clinical Dementia Rating (CDR) test inferior or equal to 1 National Institute of Neurological and Communicative Disorders and Stroke / Alzheimer's Disease and Related Disorders Association (NINCDS/ADRDA) test positive for an Alzheimer's disease Diagnostic and Statistical Manual of Mental Disorders, 4th Edition (DSM IV) test positive for dementia", "candidate_expression": "((Clinical Dementia Rating (CDR) test inferior or equal to 1) AND (Diagnostic and Statistical Manual of Mental Disorders, 4th Edition (DSM IV) test positive) AND (Mini Mental Status (MMS) tes between 16 to 26 inclusive) AND (National Institute of Neurological and Communicative Disorders and Stroke / Alzheimer's Disease and Related Disorders Association (NINCDS/ADRDA) test positive) AND (old 50 to 85 years))"}
{"candidate_id": "LLM04198", "doc_id": "NCT03387059_exc", "case_bucket": "or", "source_criterion": "Clinically significant systemic disease (such as diabetes, metabolic syndrome, immunological diseases, diagnosed thrombophilia, porphyria, or any other medical condition requiring the use of low-molecular weight heparin therapy) Polycystic ovary syndrome (PCOS) according to Rotterdam Consensus Criteria (European Society of Human Reproduction and Embryology [ESHRE]/American Society for Reproductive Medicine [ASRM], 2003) Poor ovarian response (POR) according to the European Society of Human Reproduction and Embryology (ESHRE) Criteria RIF (repeated implantation failure), defined as greater than or equals to (>=) 2 previous failed embryo transfers Endometriosis III-IV stage or adenomyosis Clinically significant findings on exam or ultrasound, such as salpingitis, hydrosalpynx or evidence of ovarian cysts Known hypersensitivity to any of the components of the solution Known hypersensitivity to vaginal progesterone or its excipients Other protocol defined exclusion criteria could apply", "candidate_expression": "((Clinically significant) AND (Endometriosis) AND (European Society of Human Reproduction and Embryology (ESHRE) Criteria) AND (European Society of Human Reproduction and Embryology [ESHRE]/American Society for Reproductive Medicine [ASRM], 2003) AND (III-IV stage) AND (Polycystic ovary syndrome (PCOS)) AND (Poor ovarian response (POR)) AND (RIF (repeated implantation failure)) AND (Rotterdam Consensus Criteria) AND (adenomyosis) AND (components of the solution) AND (diabetes) AND (diagnosed thrombophilia) AND (evidence) AND (exam) AND (excipients) AND (findings) AND (greater than or equals to (>=) 2) AND (hydrosalpynx) AND (hypersensitivity) AND (immunological diseases) AND (low-molecular weight heparin) AND (medical condition) AND (metabolic syndrome) AND (ovarian cysts) AND (porphyria) AND (previous failed embryo transfers) AND (salpingitis) AND (systemic disease) AND (ultrasound) AND (vaginal progesterone))"}
{"candidate_id": "LLM04199", "doc_id": "NCT01205334_inc", "case_bucket": "or", "source_criterion": "Histopathological verification of glioblastoma multiforme (GBM: WHO grade IV) in remission (Group A) or with active disease (Group B). CMV-positive GBM CMV seropositive Life expectancy 6 weeks or greater Karnofsky/Lansky score 50 or greater Patient or parent/guardian capable of providing informed consent Bilirubin less than 1.5x upper limit of normal, AST less than 3x upper limit of normal, serum creatinine less than 1.5x normal and Hgb 8.0 g/dL or greater Pulse oximetry of 90% or greater on room air Sexually active patients must be willing to utilize one of the more effective birth control methods for 6 months after the CTL infusion. The male partner should use a condom. Patients should have been off other investigational antineoplastic therapy for one month prior to entry in this study. Informed consent explained to, understood by and signed by patient/guardian. Patient/guardian given copy of informed consent.", "candidate_expression": "((AST less than 3x upper limit of normal) AND (Bilirubin less than 1.5x upper limit of normal) AND (CMV active Group B) AND (CMV seropositive) AND (GBM) AND (GBM CMV-positive) AND (Histopathological) AND (Histopathological verification) AND (Informed consent explained to, understood by and signed by patient/guardian. Patient/guardian given copy of informed consent.) AND (Karnofsky/Lansky score 50 or greater) AND (Life expectancy 6 weeks or greater) AND (Patient or parent/guardian capable of providing informed consent) AND (Patients should have been off other investigational antineoplastic therapy for one month prior to entry in this study.) AND (Pulse oximetry 90% or greater on room air) AND (Sexually active patients must be willing to utilize one of the more effective birth control methods for 6 months after the CTL infusion. The male partner should use a condom.) AND (WHO grade IV Group A) AND (glioblastoma multiforme) AND NOT (antineoplastic therapy for one month prior to entry in this study))"}
{"candidate_id": "LLM04200", "doc_id": "NCT02760251_inc", "case_bucket": "or", "source_criterion": "Informed consent as documented by signature (see informed consent form) Primary ITP according to the definition of Rodeghiero et al. (52) and a platelet count of <30x109/l Age range: 18-45 years Previously treated patients, with failure or intolerance to first-line therapy, or relapse after first-line therapy, i.e. corticosteroids, intravenous immunoglobulin (IVIG), or anti-D immunoglobulins", "candidate_expression": "((Age 18-45 years) AND (IVIG) AND (Informed consent as documented by signature (see informed consent form)) AND (Previously treated) AND (Primary ITP) AND (definition of Rodeghiero) AND (first-line therapy) AND (platelet count <30x109/l) AND ((first-line therapy failure intolerance) OR (relapse after first-line therapy)) AND ((anti-D immunoglobulins) OR (corticosteroids) OR (intravenous immunoglobulin)))"}
```
