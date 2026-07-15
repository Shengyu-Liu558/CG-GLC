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
{"candidate_id": "LLM04201", "doc_id": "NCT03464552_exc", "case_bucket": "or", "source_criterion": "A known allergy to Celecoxib, aspirin or another NSAID. Active peptic ulceration or gastrointestinal bleeding. Inflammatory bowel disease. Congestive heart failure (NYHA II-IV). Established ischemic heart disease, peripheral arterial disease and/or cerebrovascular disease. History of neurologic deficit. Known hepatic or renal impairment. Pregnancy. Breast-feeding. Post-hysterectomy. Bleeding disorders. Drug abuse. Cervical and vaginal infection.", "candidate_expression": "((Active) AND (Bleeding disorders) AND (Breast-feeding) AND (Celecoxib) AND (Cervical infection) AND (Congestive heart failure) AND (Drug abuse) AND (History) AND (II-IV) AND (Inflammatory bowel disease) AND (NSAID) AND (NYHA) AND (Post) AND (Pregnancy) AND (allergy) AND (another) AND (aspirin) AND (cerebrovascular disease) AND (gastrointestinal bleeding) AND (hepatic impairment) AND (hysterectomy) AND (ischemic heart disease) AND (neurologic deficit) AND (peptic ulceration) AND (peripheral arterial disease) AND (renal impairment) AND (vaginal infection))"}
{"candidate_id": "LLM04202", "doc_id": "NCT02885909_inc", "case_bucket": "or", "source_criterion": "Type 2 diabetic inpatient Fasting glucose >140 mg/dl or random glucose >180 mg/dl", "candidate_expression": "((>140 mg/dl) AND (>180 mg/dl) AND (Fasting glucose) AND (Type 2 diabetic) AND (inpatient) AND (random glucose))"}
{"candidate_id": "LLM04203", "doc_id": "NCT03077204_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04204", "doc_id": "NCT03260790_inc", "case_bucket": "other", "source_criterion": "Diagnosis of asthma", "candidate_expression": "(asthma)"}
{"candidate_id": "LLM04205", "doc_id": "NCT02571881_inc", "case_bucket": "other", "source_criterion": "normal full term single pregnancy age 18 years or more BMI 20 - 35 kg/m2 written informed consent obtained", "candidate_expression": "((BMI 20 - 35 kg/m2) AND (age 18 years or more) AND (pregnancy normal full term single) AND (written informed consent obtained))"}
{"candidate_id": "LLM04206", "doc_id": "NCT03119766_inc", "case_bucket": "or", "source_criterion": "Men and women aged 18-45 years. Diagnosis of functional dyspepsia, based on the Rome IV criteria (2016). GIS score of at least 6. Negative H. pylori test . Availability of a signed patient information sheet (Informed Consent form) for participation in the clinical trial. Patients who agree to use an effective method of contraception throughout the clinical trial.", "candidate_expression": "((18-45 years) AND (Availability of a signed patient information sheet (Informed Consent form) for participation in the clinical trial) AND (GIS score) AND (H. pylori test) AND (Men) AND (Negative) AND (Patients who agree to use an effective method of contraception throughout the clinical trial.) AND (Rome IV criteria (2016)) AND (aged) AND (at least 6) AND (functional dyspepsia) AND (women))"}
{"candidate_id": "LLM04207", "doc_id": "NCT03513874_exc", "case_bucket": "or", "source_criterion": "History of any malignancy or other severe diseases Female patients who are pregnant or breastfeeding before or during the three-year follow-up Poor compliance or refusal to participate.", "candidate_expression": "((Female patients who are pregnant or breastfeeding before or during the three-year follow-up) AND ((malignancy) OR (severe diseases)) AND ((Poor compliance) OR (refusal to participate)))"}
{"candidate_id": "LLM04208", "doc_id": "NCT02416765_exc", "case_bucket": "or", "source_criterion": "1. Clinically significant microvascular complications: nephropathy (estimated glomerular filtration rate below 40 ml/min), neuropathy (especially diagnosed gastroparesis) or severe proliferative retinopathy as judged by the investigator. 2. Recent (< 3 months) acute macrovascular event e.g. acute coronary syndrome or cardiac surgery. 3. Ongoing pregnancy. 4. Severe hypoglycemic episode within 1 month of screening. 5. Agents affecting gastric emptying (Motilium®, Prandase®, Victoza®, Byetta® and Symlin®) as well as oral anti-diabetic agents (Metformin, SGLT-2 inhibitors and DPP-4 inhibitors) if not at a stable dose for 3 months. Otherwise, these medications are acceptable and will be kept stable during the entire protocol. 6. Oral steroids unless patients present a low stable dose (e.g. 10 mg or less of prednisone per day or physiological doses, less than 35 mg/day, of hydrocortisone Cortef®). Inhale steroids at stable dose in the last month are acceptable. 7. Other serious medical illness likely to interfere with study participation or with the ability to complete the trial by the judgment of the investigator (e.g. unstable psychiatric condition). 8. Failure to comply with team's recommendations (e.g. not willing to change pump parameters, follow algorithm's suggestions, etc). 9. Living or planned travel outside Montreal (> 1h of driving) area during closed-loop procedures.", "candidate_expression": "((Agents affecting gastric emptying) AND (Byetta) AND (Cortef) AND (DPP-4 inhibitors stable dose) AND (Inhale steroids stable dose in the last month) AND (Metformin) AND (Motilium) AND (Oral steroids low dose stable dose) AND (Other medical illness serious) AND (Prandase) AND (SGLT-2 inhibitors) AND (Symlin) AND (Victoza) AND (acute coronary syndrome) AND (acute macrovascular event Recent < 3 months) AND (as judged by the investigator) AND (by the judgment of the investigator) AND (cardiac surgery) AND (closed-loop procedures during closed-loop procedures) AND (estimated glomerular filtration rate below 40 ml/min) AND (gastroparesis) AND (hydrocortisone physiological doses) AND (hypoglycemic episode Severe within 1 month of screening) AND (microvascular complications as judged by the investigator) AND (nephropathy) AND (neuropathy) AND (oral anti-diabetic agents) AND (prednisone 10 mg or less per day less than 35 mg/day) AND (pregnancy Ongoing) AND (psychiatric condition unstable) AND (serious) AND (severe proliferative retinopathy))"}
{"candidate_id": "LLM04209", "doc_id": "NCT02844907_inc", "case_bucket": "or", "source_criterion": "Body Mass Index (BMI) = 35 kg/m2 HbA1c = 5.7% Ability to speak and understand English", "candidate_expression": "((= 35 kg/m2) AND (= 5.7%) AND (Body Mass Index (BMI)) AND (HbA1c) AND ((Ability to speak English) OR (Ability to understand English)))"}
{"candidate_id": "LLM04210", "doc_id": "NCT02667730_inc", "case_bucket": "or", "source_criterion": "Acquired acute ankle injury (injured less than 48 hours ago); Clinical diagnosis of a Grade I or II ankle sprain Is eligible to receive comprehensive medical care from Garrison Petawawa", "candidate_expression": "((Acquired) AND (acute ankle injury) AND (ankle sprain) AND (less than 48 hours ago) AND ((Grade I) OR (Grade II)))"}
{"candidate_id": "LLM04211", "doc_id": "NCT00312429_inc", "case_bucket": "or", "source_criterion": "Diagnosis reviewed at transplant center and confirmed to fit the criterion for high risk blood disease or cancer, as defined for the study Estimated life expectancy of at least 6 weeks following study entry Cancer and Leukemia Group B (CALGB) performance status less than or equal to 2 White blood cell count, platelet, hematocrit, tuberculosis, aspartate aminotransferase (AST), alanine aminotransferase (ALT), alkaline phosphatase, creatinine, and HIV test results reviewed by transplant center Multiple gated acquisition (MUGA), echocardiogram, cardiac MRI, and/or pulmonary function tests (PFT) performed and reviewed by transplant center (for individuals with an ejection fraction and diffusing capacity [DLCO] of 40-50%, the appropriate cardiology or pulmonary consultations should be considered if the individual has severe heart or lung disease at the initiation of therapy) Sufficient number of umbilical cord blood units available for transplantation If female, willing to use contraception throughout the study", "candidate_expression": "((Cancer and Leukemia Group B (CALGB) performance status less than or equal to 2) AND (Estimated life expectancy at least 6 weeks following study entry) AND (HIV test results) AND (White blood cell count) AND (alanine aminotransferase (ALT)) AND (alkaline phosphatase) AND (aspartate aminotransferase (AST)) AND (contraception throughout the study) AND (creatinine) AND (female) AND (hematocrit) AND (platelet) AND (transplantation) AND (tuberculosis) AND (umbilical cord blood units available Sufficient number for transplantation) AND ((Multiple gated acquisition (MUGA)) OR (cardiac MRI) OR (echocardiogram) OR (pulmonary function tests (PFT))) AND ((cancer) OR (high risk blood disease)))"}
{"candidate_id": "LLM04212", "doc_id": "NCT02714725_exc", "case_bucket": "or", "source_criterion": "Patient refusal. Emergency surgeries Redo surgeries Pregnancy Vasculitis Inflammation or infection at the study site History of allergic reaction to study medications", "candidate_expression": "((Emergency surgeries) AND (Inflammation) AND (Patient refusal) AND (Pregnancy) AND (Redo surgeries) AND (Vasculitis) AND (allergic) AND (infection) AND (study site))"}
{"candidate_id": "LLM04213", "doc_id": "NCT03044561_exc", "case_bucket": "or", "source_criterion": "(1) Uterine abnormalities (e.g. septate, bicornuate and fibroid uterus, Asherman Syndrome). Concurrent use of organic nitrites and nitrates. Severe hepatic impairment. Severe renal impairment. Hypotension. Recent stroke or heart attack.", "candidate_expression": "((Asherman Syndrome) AND (Concurrent) AND (Hypotension) AND (Recent) AND (Severe) AND (Uterine abnormalities) AND (bicornuate uterus) AND (fibroid uterus) AND (heart attack) AND (hepatic impairment) AND (nitrates) AND (organic nitrites) AND (renal impairment) AND (septate uterus) AND (stroke))"}
{"candidate_id": "LLM04214", "doc_id": "NCT00962364_exc", "case_bucket": "other", "source_criterion": "none, all patients meeting the inclusion criteria will be eligible.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04215", "doc_id": "NCT03363295_exc", "case_bucket": "or", "source_criterion": "Diabetic patients Patients with any macular changes prior to the surgery (epiretinal membranes, age macular disease, macular edema...) Patients who had any complication during phacoemulsification surgery", "candidate_expression": "((Diabetic) AND (any) AND (complication) AND (during phacoemulsification surgery) AND (macular changes) AND (phacoemulsification surgery) AND (prior to the surgery) AND (surgery) AND (the surgery) AND ((age macular disease) OR (epiretinal membranes) OR (macular edema)))"}
{"candidate_id": "LLM04216", "doc_id": "NCT02678962_exc", "case_bucket": "or", "source_criterion": "Preexisting ocular diseases or conditions other than age related cataracts, have contraindications for cataract surgery; Preexisting systemic diseases or conditions that may confound the results of the study; Previous ocular surgery history or ocular trauma that may confound the results of the study; Require combined surgery that may confound the results of the study; Previous participation in other clinical trial within 30 days of this study start; Systemic or ocular medications that may confound the outcome of the intervention Pregnant, lactating, or planning to become pregnant during the course of the trial;", "candidate_expression": "((Pregnant) AND (Systemic medications) AND (cataract surgery) AND (combined surgery Require may confound the results of the study) AND (conditions) AND (conditions may confound the results of the study) AND (contraindications) AND (lactating) AND (ocular diseases Preexisting) AND (ocular medications) AND (ocular surgery Previous) AND (ocular trauma) AND (pregnant planning to become) AND (systemic diseases Preexisting) AND NOT (cataracts age related))"}
{"candidate_id": "LLM04217", "doc_id": "NCT01373684_inc", "case_bucket": "other", "source_criterion": "Chronic hepatitis B (HBsAg positive > 6 months) HBeAg negative within six months prior to initiation of peginterferon alfa-2a HBV DNA < 200 IU/ml during nucleos(t)ide analogue (except Telbivudine) treatment within one month prior to initiation of peginterferon alfa-2a Compensated liver disease Age > 18 years Written informed consent", "candidate_expression": "((< 200 IU/ml) AND (> 18 years) AND (> 6 months) AND (Age) AND (Chronic hepatitis B) AND (Compensated) AND (HBV DNA) AND (HBeAg) AND (HBsAg) AND (Telbivudine) AND (Written informed consent) AND (during nucleos(t)ide analogue (except Telbivudine) treatment) AND (except) AND (initiation of peginterferon alfa-2a) AND (liver disease) AND (negative) AND (nucleos(t)ide analogue) AND (nucleos(t)ide analogue (except Telbivudine) treatment) AND (peginterferon alfa-2a) AND (positive) AND (within one month prior to initiation of peginterferon alfa-2a) AND (within six months prior to initiation of peginterferon alfa-2a))"}
{"candidate_id": "LLM04218", "doc_id": "NCT02816762_inc", "case_bucket": "or", "source_criterion": "Subjects aged 18 to 80 years old Overweight or obesity (BMI =25 kg/m2) Previous diagnosis of type 2 diabetes, fulfilling at least one of the following criteria: 1) current treatment with oral antidiabetic drugs and/or insulin; 2) a fasting glucose value above 126 mg/dl on at least 2 occasions; 3) blood glucose level at 2 hours after an oral glucose tolerance test is equal to or more than 200 mg/dl; or 4) a glycated hemoglobin (HbA1c) level > 6.5 % Clinical diagnosis of diabetic nephropathy, with a urinary albumin/creatinine ratio >30 mg/g and an estimated glomerular filtration rate more than 20 ml/min per 1.73 m2. Treatment with stable doses of angiotensin-converting enzyme inhibitors, angiotensin II receptor blockers or anti-aldosterone agents in the last four weeks.", "candidate_expression": "((18 to 80 years old) AND (=25 kg/m2) AND (> 6.5 %) AND (>30 mg/g) AND (BMI) AND (Overweight) AND (Previous) AND (above 126 mg/dl) AND (aged) AND (an oral glucose tolerance test) AND (angiotensin II receptor blockers) AND (angiotensin-converting enzyme inhibitors) AND (anti-aldosterone agents) AND (at 2 hours after an oral glucose tolerance test) AND (at least one) AND (blood glucose level) AND (current) AND (diabetic nephropathy) AND (equal to or more than 200 mg/dl) AND (estimated glomerular filtration rate) AND (fasting glucose) AND (glycated hemoglobin (HbA1c) level) AND (in the last four weeks) AND (insulin) AND (more than 20 ml/min per 1.73 m2) AND (obesity) AND (on at least 2 occasions) AND (oral antidiabetic drugs) AND (oral glucose tolerance test) AND (stable doses) AND (type 2 diabetes) AND (urinary albumin/creatinine ratio))"}
{"candidate_id": "LLM04219", "doc_id": "NCT02668978_exc", "case_bucket": "or", "source_criterion": "Traumatic pulmonary contusion or laceration Lung reduction surgery Planned removal of more than 10 lung lesions Pneumonectomy Known hypersensitivity to bovine protein Known hypersensitivity to Brilliant Blue FCF (E133) Presence of active infection", "candidate_expression": "((Brilliant Blue FCF (E133)) AND (Lung reduction surgery) AND (Planned) AND (Pneumonectomy) AND (Traumatic) AND (active infection) AND (bovine protein) AND (hypersensitivity) AND (laceration) AND (lung lesions) AND (more than 10) AND (pulmonary contusion) AND (removal))"}
{"candidate_id": "LLM04220", "doc_id": "NCT02858804_exc", "case_bucket": "or", "source_criterion": "with centre neural system involvement serious complications such as uncontrolled diabetes, gastric ulcer or other serious angiocardiopathy determined by the physician HIV positive or active HBV infection or other uncontrolled systematic infection clinical central nervous dysfunction serious surgery within 30 days pregnancy or baby nursing period or un-contracepted child bearing period woman.", "candidate_expression": "((central nervous dysfunction) AND (centre neural system involvement) AND (complications serious) AND (determined by the physician) AND (surgery serious within 30 days) AND (woman) AND NOT (contracepted) AND ((HIV positive) OR (active HBV infection) OR (systematic infection uncontrolled)) AND ((baby nursing period) OR (child bearing period) OR (pregnancy)) AND ((angiocardiopathy serious) OR (diabetes uncontrolled) OR (gastric ulcer)))"}
{"candidate_id": "LLM04221", "doc_id": "NCT02563535_exc", "case_bucket": "or", "source_criterion": "need for major amputation known before intervention allergy to Paclitaxel contraindication for combined antiplatelet treatment life expectancy <1 year hypersensitivity or contraindication to one of the study drugs lack of consent", "candidate_expression": "((Paclitaxel) AND (allergy) AND (combined antiplatelet treatment) AND (contraindication) AND (hypersensitivity) AND (lack of consent) AND (life expectancy <1 year) AND (major amputation) AND (study drugs one of))"}
{"candidate_id": "LLM04222", "doc_id": "NCT02986659_exc", "case_bucket": "or", "source_criterion": "eGFR <45 Type 2 diabetes (HbA1c>6.5) or type 1 diabetes Any tobacco or nicotine product use in the past year Low vitamin B12 Levels (< 300 pg/mL) Self-reported severe difficulty or inability to walk 400m or climb 10 steps (from Q 2 and 19 on PAT-D) Self-reported difficulty or inability to perform basic ADL functions (from Q 10, 13, 14, 16 on PAT-D) Excessive alcohol use (>14 drinks/week) Cancer requiring treatment in past year (except skin) Dementia - diagnosed and/or MoCA score <18 Parkinson's or other neurological disease Chronic liver disease or cirrhosis End stage renal disease or on dialysis Rheumatic conditions (Rheumatoid arthritis, lupus, and any other autoimmune disease the -PI deems them to be ineligible for) Thyroid problems the PI deems them to be ineligible for Gout Involved in another interventional study Hemoglobin <8 or diagnosed with anemia Recent unintentional weight change (+/- 10 lbs. in the last 12 months) BMI <18.5 Likely to not follow the protocol PI deems unfit to participate Already taking Metformin or any other drug intended to treat diabetes", "candidate_expression": "((BMI <18.5) AND (Cancer past year) AND (Chronic liver disease) AND (Dementia) AND (End stage renal disease) AND (Gout) AND (HbA1c >6.5) AND (Hemoglobin <8) AND (Involved in another interventional study) AND (Likely to not follow the protocol) AND (Metformin) AND (MoCA score <18) AND (Parkinson's) AND (Rheumatic conditions) AND (Rheumatoid arthritis) AND (Thyroid problems) AND (Type 2 diabetes) AND (alcohol use >14 drinks/week) AND (anemia) AND (autoimmune disease) AND (cirrhosis) AND (dialysis) AND (drug diabetes) AND (eGFR <45) AND (lupus) AND (neurological disease) AND (nicotine product use) AND (tobacco) AND (treatment) AND (type 1 diabetes) AND (vitamin B12 Levels < 300 pg/mL) AND (weight +/- 10 lbs. last 12 months))"}
{"candidate_id": "LLM04223", "doc_id": "NCT00943865_inc", "case_bucket": "or", "source_criterion": "men and women 30-55 years with BMI 30-40 and waist 95 cm or more normal OGTT normal treadmill stress test plus 2 of 4: 1. low serum levels of HDL cholesterol (<40 mg⁄dL for men or < 50 mg ⁄dL for women); 2. hypertriglyceridemia (triglyceride levels of 150 mg⁄dL or greater); 3. impaired glucose homeostasis (fasting plasma glucose concentration of 110 mg⁄dL or greater or glucose of 140 mg⁄dL or greater after OGTT or 4. hypertension (systolic blood pressure ≥ 140 or diastolic blood pressure ≥90 mmHg or treatment with antihypertensive drugs).", "candidate_expression": "((110 mg⁄dL or greater) AND (140 mg⁄dL or greater) AND (150 mg⁄dL or greater) AND (2 of 4) AND (30-40) AND (30-55 years) AND (95 cm or more) AND (< 50 mg ⁄dL) AND (<40 mg⁄dL) AND (BMI) AND (OGTT) AND (after OGTT) AND (antihypertensive drugs) AND (hypertension) AND (hypertriglyceridemia) AND (impaired glucose homeostasis) AND (low) AND (men) AND (normal) AND (serum levels of HDL cholesterol) AND (treadmill stress test) AND (triglyceride levels) AND (waist) AND (women) AND (≥ 140) AND (≥90 mmHg) AND ((men) OR (women)) AND ((fasting plasma glucose concentration) OR (glucose)) AND ((diastolic blood pressure) OR (systolic blood pressure) OR (treatment)))"}
{"candidate_id": "LLM04224", "doc_id": "NCT02121145_inc", "case_bucket": "or", "source_criterion": "Male or female subjects aged =18 to =65 years General good health as established by medical history and physical examination Written informed consent Females of childbearing potential must agree to use an efficacious hormonal or barrier method of birth control during the study. Abstinence is acceptable. Available for all visits scheduled in this study.", "candidate_expression": "((Available for all visits scheduled in this study) AND (Females) AND (General good health established by medical history) AND (Written informed consent) AND (aged =18 to =65 years) AND (childbearing potential) AND (physical examination) AND ((Male) OR (female)) AND ((barrier method) OR (hormonal method)) AND ((Abstinence) OR (birth control agree to use efficacious during the study)))"}
{"candidate_id": "LLM04225", "doc_id": "NCT02315287_exc", "case_bucket": "or", "source_criterion": "Contraindication to sitagliptin or metformin or thiazolidinedione Pregnant or breast feeding women Type 1 diabetes, gestational diabetes, or secondary forms of diabetes Not appropriate for oral antidiabetic agent Medication which affect glycemic control Disease which affect efficacy and safety of drugs Any major illness (Liver disease, Renal failure, Heart disease, Cancer, etc)", "candidate_expression": "((Cancer) AND (Contraindication) AND (Disease) AND (Heart disease) AND (Liver disease) AND (Medication) AND (Not) AND (Pregnant) AND (Renal failure) AND (Type 1 diabetes) AND (affect efficacy) AND (affect glycemic control) AND (appropriate) AND (breast) AND (gestational diabetes) AND (major illness) AND (metformin) AND (oral antidiabetic agent) AND (safety of drugs) AND (secondary forms of diabetes) AND (sitagliptin) AND (thiazolidinedione))"}
```
