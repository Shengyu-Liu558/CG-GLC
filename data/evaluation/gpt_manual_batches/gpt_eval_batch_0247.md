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
{"candidate_id": "LLM06151", "doc_id": "NCT01497639_exc", "case_bucket": "other", "source_criterion": "previous brain surgery; cognitive impairment (< 120 points on the Mattis Dementia Rating Scale) moderate-to-severe depression (> 25 points on the Beck Depression Inventory) marked brain atrophy as detected by magnetic resonance imaging other medical or psychiatric coexisting disorders that could increase the surgical risk or interfere with completion of the trial", "candidate_expression": "((Beck Depression Inventory > 25 points) AND (Mattis Dementia Rating Scale < 120 points) AND (brain atrophy) AND (brain surgery previous) AND (cognitive impairment) AND (depression moderate-to-severe) AND (magnetic resonance imaging) AND (other medical or psychiatric coexisting disorders that could increase the surgical risk or interfere with completion of the trial))"}
{"candidate_id": "LLM06152", "doc_id": "NCT02746900_exc", "case_bucket": "or", "source_criterion": "Multiple pregnancy Prior spontaneous preterm birth or second trimester losses between 16(0) and 36(6) weeks Cerclage in situ Painful regular uterine contraction and/or preterm labor Ruptured membranes Major fetal defects Active vaginal bleeding Placenda previa and/or accreta Cervical dilation >1.5 cm and/or visible membranes by pelvic exam Suspicion of chorioamnionitis", "candidate_expression": "((Active vaginal bleeding) AND (Cerclage in situ) AND (Cervical dilation >1.5 cm) AND (Major fetal defects) AND (Multiple pregnancy) AND (Painful regular uterine contraction) AND (Placenda previa) AND (Ruptured membranes) AND (accreta) AND (chorioamnionitis Suspicion of) AND (losses second trimester between 16(0) and 36(6) weeks) AND (pelvic exam) AND (preterm labor) AND (spontaneous preterm birth) AND (visible membranes))"}
{"candidate_id": "LLM06153", "doc_id": "NCT01669369_inc", "case_bucket": "or", "source_criterion": "histologically diagnosed primary classical osteosarcoma in extremities staging IIB MRI showing no skip lesion receive standard neo-adjuvant chemotherapy, adjuvant chemotherapy,and standard surgical treatment", "candidate_expression": "((MRI) AND (classical osteosarcoma) AND (histologically) AND (in extremities) AND (no) AND (primary) AND (skip lesion) AND (staging IIB) AND ((adjuvant chemotherapy) OR (standard neo-adjuvant chemotherapy) OR (standard surgical treatment)))"}
{"candidate_id": "LLM06154", "doc_id": "NCT03012984_inc", "case_bucket": "other", "source_criterion": "Age >= 65 years, < 90 years; Scheduled to undergo surgery for primary solid organ cancer under general anesthesia, with an expected duration of surgery >=2 hours; Planned to use patient-controlled intravenous analgesia after surgery; Provide written informed consent.", "candidate_expression": "((>= 65 years, < 90 years) AND (Age) AND (Provide written informed consent) AND (Scheduled) AND (after surgery) AND (general anesthesia) AND (intravenous analgesia) AND (patient-controlled) AND (primary) AND (solid organ cancer) AND (surgery))"}
{"candidate_id": "LLM06155", "doc_id": "NCT02427295_exc", "case_bucket": "or", "source_criterion": "Severe co-morbid illness such as untreatable other malignancy and/or active infections. Pregnant or lactating women Hypersensitivity to Sandostatin or any component of the formulation.", "candidate_expression": "((Hypersensitivity) AND (Pregnant) AND (Sandostatin) AND (Severe) AND (active) AND (co-morbid illness) AND (component of the formulation) AND (infections) AND (lactating) AND (malignancy) AND (other) AND (untreatable) AND (women))"}
{"candidate_id": "LLM06156", "doc_id": "NCT02426944_exc", "case_bucket": "or", "source_criterion": "thrombus in the LA or LAA; mechanical valve prosthesis; mitral stenosis; previous LAA ligation during cardiac surgery; life expectancy less than 2 years; comorbidities other than AF, which present an indication for anticoagulation; patent foramen ovale with atrial septal aneurysm mobile plaque in the aorta; symptomatic atherosclerosis of the carotid artery; pericardial effusion greater than 10 mm; clinically significant bleeding within the 30 days prior to the scheduled procedure; stroke or other cardioembolic event within the 30 days prior to the scheduled procedure; acute coronary syndrome within the 90 days prior to the scheduled procedure, gravidity, significant valvular disease, creatinine clearance less than 30 ml/min", "candidate_expression": "((AF) AND (LAA ligation) AND (acute coronary syndrome) AND (anticoagulation) AND (atherosclerosis) AND (atrial septal aneurysm) AND (bleeding) AND (cardiac surgery) AND (clinically significant) AND (comorbidities) AND (creatinine clearance) AND (gravidity) AND (greater than 10 mm) AND (indication) AND (less than 2 years) AND (less than 30 ml/min) AND (life expectancy) AND (mechanical valve prosthesis) AND (mitral stenosis) AND (mobile plaque in the aorta) AND (of the carotid artery) AND (other) AND (other than) AND (patent foramen ovale) AND (pericardial effusion) AND (significant) AND (symptomatic) AND (the scheduled procedure) AND (thrombus) AND (valvular disease) AND (within the 30 days prior to the scheduled procedure) AND (within the 90 days prior to the scheduled procedure) AND ((LA) OR (LAA)) AND ((cardioembolic event) OR (stroke)))"}
{"candidate_id": "LLM06157", "doc_id": "NCT02550080_inc", "case_bucket": "or", "source_criterion": "Diagnosed with cutaneous vasculitis, urticaria, psoriasis, acne, bullous skin diseases, sterile pustulosis, leprosy, pneumocystis pneumonia and any other patients who need dapsone administration. Subjects are dapsone-naive. All subjects must have a clinical need for treatment with dapsone that precedes the decision to participate in the study. All subjects are willing to complete the 6-weeks period clinical trial. All subjects are written informed consent.", "candidate_expression": "((All subjects are willing to complete the 6-weeks period clinical trial) AND (All subjects are written informed consent) AND (acne) AND (bullous skin diseases) AND (cutaneous vasculitis) AND (dapsone) AND (leprosy) AND (pneumocystis pneumonia) AND (psoriasis) AND (sterile pustulosis) AND (urticaria) AND NOT (dapsone))"}
{"candidate_id": "LLM06158", "doc_id": "NCT00543712_inc", "case_bucket": "or", "source_criterion": "Ability to understand and willingness to sign a written informed consent document Age ≥ 18 years Histologic diagnosis of chondrosarcoma, verifiable after enrollment Measurable disease Previously treated or incurable disease without options for standard of care therapy ECOG performance status of 0-2 Life expectancy of > 3 months For patients of reproductive potential (males and females), use of reliable means for contraception (e.g., contraceptive pill, intrauterine device [IUD], physical barrier) throughout the trial and for 1 year following their final exposure to study treatment", "candidate_expression": "((0-2) AND (> 3 months) AND (Age) AND (ECOG performance status) AND (Histologic) AND (Life expectancy) AND (chondrosarcoma) AND (contraception) AND (contraceptive pill) AND (for 1 year following their final exposure) AND (intrauterine device [IUD]) AND (physical barrier) AND (reproductive potential) AND (throughout the trial) AND (≥ 18 years))"}
{"candidate_id": "LLM06159", "doc_id": "NCT02755701_inc", "case_bucket": "or", "source_criterion": "Age = 19 and = 70 years; Presence of liver cirrhosis Serum albumin level = 3.5g/dl, ultrasound or CT scan confirmed ascites (=Grade 1) No administration of diuretics and BCAA within the past 1 week Voluntary consent to take part in this trial", "candidate_expression": "((Age = 19 and = 70 years) AND (BCAA) AND (CT scan) AND (Serum albumin = 3.5g/dl) AND (Voluntary consent to take part in this trial) AND (ascites Grade 1) AND (diuretics) AND (liver cirrhosis) AND (ultrasound))"}
{"candidate_id": "LLM06160", "doc_id": "NCT00445029_inc", "case_bucket": "other", "source_criterion": "For both groups: Patients aged from 18 to 65 years old. Both genders eligible for study. Female participants must use a contraceptive method. Feasibility of patch testing. Participants must be able to understand and sign the Informed Consent, and comply with all aspects of the protocol. Patients must be registered in a social security system or with a health insurance coverage  First group: allergic patients Patients with allergic contact dermatitis to para-phenylenediamine (PPD) based on a history of PPD contact dermatitis and positive PPD patch tests.  Second group : healthy volunteers No history of PPD allergic contact dermatitis, with a negative PPD patch test.", "candidate_expression": "((Both genders) AND (Female) AND (PPD) AND (PPD patch test negative) AND (PPD patch tests positive) AND (aged from 18 to 65 years old) AND (allergic) AND (allergic contact dermatitis) AND (comply with all aspects of the protocol) AND (contact dermatitis) AND (contraceptive method) AND (health insurance coverage) AND (healthy) AND (para-phenylenediamine (PPD)) AND (patch testing Feasibility of) AND (registered in a social security system) AND (understand and sign the Informed Consent) AND NOT (allergic contact dermatitis))"}
{"candidate_id": "LLM06161", "doc_id": "NCT02542956_exc", "case_bucket": "other", "source_criterion": "A medical condition that could interfere with study participation Body weight less than 50 kg Participating in another study involving an investigational medication", "candidate_expression": "((Body weight) AND (Participating in another study involving an investigational medication) AND (less than 50 kg))"}
{"candidate_id": "LLM06162", "doc_id": "NCT02935855_exc", "case_bucket": "other", "source_criterion": "patients with cancer patients with chronic inflammation diseases", "candidate_expression": "((cancer) AND (chronic inflammation diseases))"}
{"candidate_id": "LLM06163", "doc_id": "NCT02916342_exc", "case_bucket": "or", "source_criterion": "indication for catheter insertion; contraindications to brachial plexus block (e.g., allergy to local anaesthetics, malignancy or infection in the area); existing neurological deficit in the area to be blocked; pregnancy; history of neck surgery or radiotherapy; severe respiratory disease; chest deformity; inability to understand the informed consent and demands of the study; patient refusal.", "candidate_expression": "((allergy) AND (area to be blocked) AND (brachial plexus block) AND (catheter insertion) AND (chest deformity) AND (contraindications) AND (existing) AND (history) AND (in the area) AND (inability to understand the informed consent and demands of the study;) AND (indication) AND (infection) AND (local anaesthetics) AND (malignancy) AND (neck surgery) AND (neurological deficit) AND (patient refusal) AND (pregnancy) AND (radiotherapy) AND (respiratory disease) AND (severe))"}
{"candidate_id": "LLM06164", "doc_id": "NCT02918409_inc", "case_bucket": "or", "source_criterion": "Male or female = 18 years of age at Visit 1. Sweat chloride equal or greater than 60 mEq/L by quantitative pilocarpine iontophoresis test. Two well-characterized mutations in the cystic fibrosis transmembrane conductance regulator (CFTR) gene Abnormal nasal potential difference (NPD) as measured by a change in NPD in response to a low chloride solution and isoproterenol of less than -5 mV. Documentation of the presence of an acute pulmonary exacerbation, based on CF Foundation guidelines, as diagnosed by a faculty member of the Denver Adult CF Program. Respiratory culture(s) demonstrating evidence of Pseudomonas aeruginosa or Achromobacter species airway infection. Subject is able to produce sputum, undergo phlebotomy, and provide written consent. The subject's treating physician has determined that they should receive either tobramycin or colistin intravenously as one of the designated agents for their APE treatment. Subjects who are able to receive either tobramycin or colistin as part of their antibiotic regimen will be randomized into one of three arms. If a treating physician deems that a subject cannot receive tobramycin due to vestibular toxicity, ototoxicity or bacterial resistance, the subject will be randomized to either standard or PK-adjusted colistin.", "candidate_expression": "((= 18 years) AND (Abnormal) AND (Achromobacter species) AND (CF Foundation guidelines) AND (CFTR) AND (Male) AND (NPD) AND (Pseudomonas aeruginosa) AND (Respiratory culture(s)) AND (Subject is able to produce sputum, undergo phlebotomy, and provide written consent.) AND (Sweat chloride) AND (The subject's treating physician has determined that they should receive either tobramycin or colistin intravenously as one of the designated agents for their APE treatment. Subjects who are able to receive either tobramycin or colistin as part of their antibiotic regimen will be randomized into one of three arms. If a treating physician deems that a subject cannot receive tobramycin due to vestibular toxicity, ototoxicity or bacterial resistance, the subject will be randomized to either standard or PK-adjusted colistin) AND (Two) AND (Visit 1) AND (acute pulmonary exacerbation) AND (age) AND (airway infection) AND (at Visit 1.) AND (cystic fibrosis transmembrane conductance regulator gene) AND (equal or greater than 60 mEq/L) AND (female) AND (less than -5 mV) AND (mutations) AND (nasal potential difference) AND (quantitative pilocarpine iontophoresis test))"}
{"candidate_id": "LLM06165", "doc_id": "NCT02607748_exc", "case_bucket": "or", "source_criterion": "Age < 18 years Creatinine > 1.5 mg/dL History of severe allergy to Iodine contrast agents Pregnancy Active atrial fibrillation Multiple premature ventricular or atrial contractions Ejection fraction <35% Class III congestive heart failure", "candidate_expression": "((< 18 years) AND (<35%) AND (> 1.5 mg/dL) AND (Age) AND (Class III) AND (Creatinine) AND (Ejection fraction) AND (Iodine contrast agents) AND (Multiple premature atrial contractions) AND (Multiple premature ventricular contractions) AND (Pregnancy) AND (allergy) AND (atrial fibrillation) AND (congestive heart failure))"}
{"candidate_id": "LLM06166", "doc_id": "NCT02952365_exc", "case_bucket": "or", "source_criterion": "Subjects under the age of 21. Subjects with excessively thin corneas. Subjects with topographic evidence of keratoconus. Subjects with ectatic eye disorders. Subjects with autoimmune diseases. Subjects who are pregnant or nursing.", "candidate_expression": "((age) AND (autoimmune diseases) AND (ectatic eye disorders) AND (excessively thin corneas) AND (keratoconus) AND (topographic evidence) AND (under the age of 21) AND ((nursing) OR (pregnant)))"}
{"candidate_id": "LLM06167", "doc_id": "NCT02112734_exc", "case_bucket": "or", "source_criterion": "Infants who have already received postnatal vitamin D supplementation prematurity (<37 weeks)/low birthweight <2500 g poor health due to a current or past significant disease state or congenital abnormality.", "candidate_expression": "((<2500 g) AND (Infants) AND (birthweight) AND (poor health) AND (postnatal vitamin D supplementation) AND (vitamin D) AND ((congenital abnormality) OR (significant disease state)) AND ((low birthweight) OR (prematurity)) AND ((current) OR (past)))"}
{"candidate_id": "LLM06168", "doc_id": "NCT00324363_inc", "case_bucket": "or", "source_criterion": "Treated with a stable dose of one of the following for at least 3 months prior to screening: * >=1000 mg/day immediate-release metformin; or metformin >=1000 mg/day and sulfonylurea; or sulfonylurea/metformin combination therapy. HbA1c between 7.1% and 11.0%, inclusive. Body Mass Index (BMI) >21 kg/m^2 and <35 kg/m^2.", "candidate_expression": "((>21 kg/m^2 and <35 kg/m^2) AND (>=1000 mg/day) AND (Body Mass Index (BMI)) AND (HbA1c) AND (at least 3 months prior to screening) AND (between 7.1% and 11.0%, inclusive) AND (combination therapy) AND (immediate-release metformin) AND (metformin) AND (one of the following) AND (screening) AND (stable dose) AND (sulfonylurea))"}
{"candidate_id": "LLM06169", "doc_id": "NCT02243553_exc", "case_bucket": "or", "source_criterion": "1. History or presence of allergy to the study drugs or their components or drugs of their class, or a history of drug or other allergy that, in the opinion of the physician responsible, contraindicates their participation 2. Any finding of the medical examination (including blood pressure, pulse rate and electrocardiogram) deviating from normal and of clinical relevance 3. History or diagnosis of any significant medical conditions: Including but not limited to gastrointestinal, hepatic, renal, respiratory, cardiovascular, metabolic, immunologic, hematological, psychiatric, neurological, oncological or hormonal disorders 4. Known elevated liver enzymes in past clinical trials with any compound (experimental or marketed) 5. Clinically relevant laboratory abnormalities (e.g. Hgb<11g/dL, Hct<30g/dL, total cholesterol >240mg/dL, triglycerides >500mg/dL, fasting glucose >130mg/dL, liver function tests >2.5x upper limit of normal, baseline international normalized ratio >1.2) 6. History of evidence of clinically significant hepatic, cardiac, pulmonary, endocrine, immunological, gastrointestinal, hematological, vascular or collagen disease 7. History of alcohol abuse or use of any illicit drugs 8. Unable to abstain from more than one beer or alcohol equivalent per day for the duration of the study 9. Use of tobacco products and/or history of smoking within the past 2 months 10. Pregnant or breast feeding 11. Sexually active women of childbearing age who do not use an acceptable barrier method of birth control 12. Hypersensitivity to caffeine, warfarin, vitamin K, omeprazole, dextromethorphan, midazolam, tipranavir, ritonavir or their excipients 13. Concomitant treatment with other experimental compounds 14. Concomitant administration of any prescription or over the counter medications known to alter P450 enzyme or P-gp activity 15. Concomitant administration of any prescription or over the counter medications known to be highly dependent on P450 or P-gp for clearance for which elevated plasma concentrations are known to be associated with serious toxicity 16. Concomitant administration of any food product known to alter P450 enzyme or P-gp activity such as grapefruit juice, Seville oranges 17. Concomitant administration of any drug that could affect bleeding (e.g., aspirin, clopidogrel, ticlopidine, warfarin, heparin, low-molecular weight heparin) 18. Concomitant administration of oral contraceptives (may be included with 7-day washout period) 19. Concomitant administration of any herbal medications 20. Inadequate venous access 21. Renal or hepatic insufficiency 22. Clinically unacceptable result at the screening physical examination 23. Use of investigational medications within 30 days before study entry 24. HIV-positive 25. Body Mass Index (BMI) > 30 kg/m²", "candidate_expression": "((Any finding of the medical examination (including blood pressure, pulse rate and electrocardiogram) deviating from normal and of clinical relevance) AND (Body Mass Index (BMI) > 30 kg/m²) AND (Clinically relevant) AND (Clinically unacceptable) AND (Clinically unacceptable result Clinically unacceptable at the screening physical examination) AND (HIV positive) AND (Hct <30g/dL) AND (Hgb <11g/dL) AND (History or presence of allergy to the study drugs or their components or drugs of their class, or a history of drug or other allergy that, in the opinion of the physician responsible, contraindicates their participation) AND (Hypersensitivity) AND (Pregnant) AND (Renal insufficiency) AND (Seville oranges) AND (Sexually active) AND (age childbearing) AND (alcohol abuse) AND (allergy) AND (aspirin) AND (breast feeding) AND (caffeine) AND (cardiac disease) AND (cardiovascular disorders) AND (clinically significant) AND (clopidogrel) AND (collagen disease) AND (dextromethorphan) AND (drug that could affect bleeding) AND (endocrine disease) AND (experimental compounds Concomitant) AND (fasting glucose >130mg/dL) AND (food product known to alter P-gp activity) AND (food product known to alter P450 enzyme activity) AND (gastrointestinal disease) AND (gastrointestinal disorders) AND (grapefruit juice) AND (hematological disease) AND (hematological disorders) AND (heparin) AND (hepatic disease) AND (hepatic disorders) AND (hepatic insufficiency) AND (herbal medications Concomitant) AND (hormonal disorders) AND (immunologic disorders) AND (immunological disease) AND (international normalized ratio baseline >1.2) AND (investigational medications within 30 days before study entry) AND (laboratory abnormalities Clinically relevant) AND (liver enzymes elevated) AND (liver function tests >2.5x upper limit of normal) AND (low-molecular weight heparin) AND (medical conditions significant) AND (medications known to alter P-gp activity) AND (medications known to alter P450 enzyme activity) AND (medications known to be highly dependent on P-gp for clearance) AND (medications known to be highly dependent on P450 for clearance) AND (metabolic disorders) AND (midazolam) AND (neurological disorders) AND (omeprazole) AND (oncological disorders) AND (oral contraceptives Concomitant) AND (physical examination) AND (plasma concentrations elevated) AND (psychiatric disorders) AND (pulmonary disease) AND (renal disorders) AND (respiratory disorders) AND (ritonavir) AND (significant) AND (smoking history within the past 2 months) AND (study drugs) AND (ticlopidine) AND (tipranavir) AND (tobacco products) AND (total cholesterol >240mg/dL) AND (toxicity serious) AND (triglycerides >500mg/dL) AND (use of illicit drugs) AND (vascular disease) AND (venous access Inadequate) AND (vitamin K) AND (warfarin) AND (women) AND NOT (barrier method of birth control acceptable))"}
{"candidate_id": "LLM06170", "doc_id": "NCT02366819_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed locally advanced gastric (primary endpoint includes proximal and mid-body stomach) or esophagogastric adenocarcinoma; distal gastric (antral) adenocarcinomas are eligible for enrolment but will not be included in the primary analysis Locally advanced disease as determined by endoscopic ultrasound (EUS) stage > primary tumor (T) 3 and/or any T, lymph nodes (N)+ disease without metastatic disease (Mx) All patients must have diagnostic laparoscopy with diagnostic washings for cytology; both cytology positive and negative patients are eligible for enrolment, but only cytology negative patients will be included in the primary analyses; gross peritoneal disease is not eligible Eastern Cooperative Oncology Group (ECOG) performance status =< 1 Eligible for surgery with curative intent Absolute neutrophil count (ANC) >= 1250/ul Hemoglobin >= 9 g/dL Platelets >= 100,000/ul Total bilirubin < 1.5 x upper limit of normal Serum glutamic oxaloacetic transaminase (SGOT) and serum glutamate pyruvate transaminase (SGPT) < 2.5 x upper limit of normal for patients without liver metastases OR SGOT and SGPT < 5 x upper limit of normal for patients with liver metastases Creatinine =< 1.5 x upper limit of normal Measurable or non-measurable disease by Response Evaluation Criteria in Solid Tumor (RECIST) 1.1 will be allowed Women of child-bearing potential and men must agree to use adequate contraception (hormonal or barrier method of birth control; abstinence) prior to study entry and for the duration of study participation, up until 30 days after final study treatment; should a woman become pregnant or suspect that she is pregnant while participating in this study, she should inform her treating physician immediately Patients taking substrates, inhibitors, or inducers of cytochrome P450, family 3, subfamily A, polypeptide 4 (CYP3A4) should be encouraged to switch to alternative drugs whenever possible, given the potential for drug-drug interactions with irinotecan Signed informed consent", "candidate_expression": "((ANC) AND (Absolute neutrophil count >= 1250/ul) AND (Creatinine =< 1.5 x upper limit of normal) AND (ECOG) AND (EUS) AND (Eastern Cooperative Oncology Group performance status =< 1) AND (Hemoglobin >= 9 g/dL) AND (Platelets >= 100,000/ul) AND (RECIST) AND (Response Evaluation Criteria in Solid Tumor 1.1) AND (SGOT) AND (SGPT) AND (Serum glutamic oxaloacetic transaminase) AND (Signed informed consent) AND (Total bilirubin < 1.5 x upper limit of normal) AND (adenocarcinoma gastric proximal stomach mid-body stomach antral) AND (adenocarcinomas distal gastric) AND (cytology positive negative) AND (disease Locally advanced) AND (endoscopic ultrasound > primary tumor (T) 3 and/or any T, lymph nodes (N)+ disease without metastatic disease (Mx)) AND (esophagogastric adenocarcinoma) AND (laparoscopy diagnostic) AND (liver metastases) AND (omen of child-bearing potential and men must agree to use adequate contraception (hormonal or barrier method of birth control; abstinence) prior to study entry and for the duration of study participation, up until 30 days after final study treatment; should a woman become pregnant or suspect that she is pregnant while participating in this study, she should inform her treating physician immediately) AND (serum glutamate pyruvate transaminase) AND (surgery curative) AND (washings for cytology) AND NOT (liver metastases))"}
{"candidate_id": "LLM06171", "doc_id": "NCT02564471_exc", "case_bucket": "or", "source_criterion": "Subject is pregnant, or lactating, or of childbearing potential (to be considered of non-childbearing potential, a female must be post-menopausal for at least 1 year, surgically sterile, or using an effective method of contraception or abstinence from at least 4 weeks prior to the first vaccination and until at least 4 weeks after the last vaccination. Participation in the 4 weeks preceding the first trial vaccination, or planned participation during the present trial period, in another clinical trial investigating a vaccine, drug, medical device, or medical procedure. Previous history of receiving the rabies vaccine. Previous history of receiving rabies immune globulin. Any major psychiatric disorder, such as severe depression, severe anxiety disorder, psychosis, schizophrenia, other major psychiatric disorders, or seizures. History of mild depression or anxiety disorder that are well controlled are not exclusion criteria. Use of any immunosuppressive drug at the time of the study or 30 days previously. Topical steroids will not be considered an immunosuppressive drug and their use will not be considered an exclusion criteria. Any immunosuppressive disorder, such as HIV infection, common variable immunodeficiency, active cancers or chemotherapy. History of renal insufficiency or requiring dialysis. Have any condition that would, in the opinion of the site investigator, place the subject at an unacceptable risk of injury or render the subject unable to meet the requirements of the protocol. Identified as an employee of the Investigator or study center, with direct involvement in the proposed study or other studies under the direction of that Investigator or study center, as well as family members (i.e., immediate, husband, wife and their children, adopted or natural) of the employee or the Investigator. Previous adverse reaction to any of the antimalarial drugs used in this study.", "candidate_expression": "((30 days previously) AND (HIV infection) AND (Have any condition that would, in the opinion of the site investigator, place the subject at an unacceptable risk of injury or render the subject unable to meet the requirements of the protocol.) AND (History) AND (Identified as an employee of the Investigator or study center, with direct involvement in the proposed study or other studies under the direction of that Investigator or study center, as well as family members (i.e., immediate, husband, wife and their children, adopted or natural) of the employee or the Investigator.) AND (Previous) AND (Previous history) AND (Subject is pregnant, or lactating, or of childbearing potential (to be considered of non-childbearing potential, a female must be post-menopausal for at least 1 year, surgically sterile, or using an effective method of contraception or abstinence from at least 4 weeks prior to the first vaccination and until at least 4 weeks after the last vaccination.) AND (Topical steroids) AND (active) AND (adverse reaction) AND (antimalarial drugs) AND (anxiety disorder) AND (at the time of the study) AND (cancers) AND (chemotherapy) AND (common variable immunodeficiency) AND (depression) AND (dialysis) AND (immunosuppressive disorder) AND (immunosuppressive drug) AND (major psychiatric disorder) AND (major psychiatric disorders) AND (mild) AND (not) AND (other) AND (psychosis) AND (rabies immune globulin) AND (rabies vaccine) AND (renal insufficiency) AND (requiring) AND (schizophrenia) AND (seizures) AND (severe) AND (used in this study) AND (well controlled))"}
{"candidate_id": "LLM06172", "doc_id": "NCT03337503_exc", "case_bucket": "or", "source_criterion": "Acute pain (less than 3 months in duration) Previous serious adverse event or hypersensitivity to cannabis or cannabinoids Inability to understand and comply with the instructions of the study Presence of significant cardiac disease (history of unstable ischemic heart disease, heart failure, severe and uncontrolled hypertension) that, in the opinion of the investigator, would put the patient at risk of a clinically significant arrhythmia or myocardial infarction Current substance use disorder according to the Diagnostic and Statistical Manual of Mental Disorders Fifth Edition (DSM 5) Life-time history of dependence on cannabis or diagnosis of cannabis use disorder (CUD) according to the DSM 5 Life-time history of DSM 5 schizophrenia, bipolar disorder, or previous psychosis with or intolerance to cannabinoids Current or history of suicidal ideation Pregnant, breast-feeding or female patients of child-bearing potential and male patients whose partner is of child-bearing potential, unless willing to ensure that they or their partner use effective contraception Hepatic impairment (aspartate aminotransferase more than three times normal) or renal function impairment (serum creatinine level >133 µmol/L, Estimated Glomerular Filtration Rate (eGFR) <60) Cognitive impairment according to MiniCog The patient is currently using or has used cannabinoid based medications within 90 days of study entry and is unwilling to abstain for the duration of the study Positive urine drug screen for cannabinoids and other potential abuse substances (e.g. alcohol, cocaine, amphetamines and methamphetamines, unprescribed opioids) Participation in another clinical trial within 30 days of enrolment in our trial", "candidate_expression": "((<60) AND (>133 µmol/L) AND (Acute) AND (Cognitive impairment) AND (Current) AND (DSM 5) AND (Diagnostic and Statistical Manual of Mental Disorders Fifth Edition (DSM 5)) AND (Estimated Glomerular Filtration Rate (eGFR)) AND (Hepatic impairment) AND (MiniCog) AND (Participation in another clinical trial within 30 days of enrolment in our trial) AND (Positive) AND (Pregnant, breast-feeding or female patients of child-bearing potential and male patients whose partner is of child-bearing potential, unless willing to ensure that they or their partner use effective contraception) AND (adverse event) AND (alcohol) AND (amphetamines) AND (arrhythmia) AND (aspartate aminotransferase) AND (at risk of) AND (bipolar disorder) AND (cannabinoid based medications) AND (cannabinoids) AND (cannabis) AND (cannabis use disorder (CUD)) AND (cardiac disease) AND (clinically significant) AND (cocaine) AND (dependence on cannabis) AND (duration) AND (heart failure) AND (history) AND (hypersensitivity) AND (hypertension) AND (intolerance) AND (less than 3 months) AND (methamphetamines) AND (more than three times normal) AND (myocardial infarction) AND (opioids) AND (pain) AND (psychosis) AND (renal function impairment) AND (schizophrenia) AND (serious) AND (serum creatinine level) AND (severe) AND (significant) AND (substance use disorder) AND (suicidal ideation) AND (uncontrolled) AND (unprescribed) AND (unstable ischemic heart disease) AND (urine drug screen) AND (within 90 days of study entry))"}
{"candidate_id": "LLM06173", "doc_id": "NCT02195024_exc", "case_bucket": "or", "source_criterion": "Pacing threshold(s) (at 0.4 or 0.5 ms) and/or sensing amplitude(s) and/or impedance(s) are not measurable Meet one or more of the contraindications for MRI including Psychiatric disorders, anxiety, claustrophobia Cardiac disorders that represent a contraindication to MRI Cardiac surgery already scheduled in the next three months Have other medical implants that may interact with MRI, e.g. abandoned implantable cardioverter defibrillator (ICD) leads or pacemaker leads other than MRI conditional, lead extensions, other active medical devices, non-MRI compatible devices, mechanical valve Have other metallic artifacts/components in body that may interact with MRI Subjects for whom a single dose of 1.0 milligram (mg) dexamethasone acetate may be contraindicated Subjects who require a legally authorized representative to obtain consent Subjects who are immediate candidates for an ICD Subjects with medical conditions that preclude the testing required by the protocol or limit study participation Subjects who are enrolled or intend to participate in another clinical trial (of an investigational drug or device, new indication for an approved drug or device, or requirement of additional testing beyond standard clinical practice) during this clinical study Being pregnant Have a life expectancy of less than three months Subjects with exclusion criteria required by local law (e.g. age, breastfeeding)", "candidate_expression": "((Cardiac surgery scheduled in the next three months) AND (ICD immediate candidates for) AND (MRI) AND (Subjects with exclusion criteria required by local law (e.g. age, breastfeeding)) AND (contraindicated) AND (contraindication) AND (contraindications one or more) AND (dexamethasone acetate single dose of 1.0 milligram (mg)) AND (interact) AND (interact with MRI) AND (life expectancy less than three months) AND (medical conditions) AND (medical implants) AND (not measurable) AND (pregnant) AND (testing required by the protoco) AND NOT (MRI conditional) AND ((Pacing threshold at 0.4 or 0.5 ms) OR (impedance) OR (sensing amplitude)) AND ((Cardiac disorders) OR (Psychiatric disorders) OR (anxiety) OR (claustrophobia)) AND ((abandoned implantable cardioverter defibrillator (ICD) leads) OR (active medical devices other) OR (lead extensions) OR (mechanical valve) OR (non-MRI compatible devices) OR (pacemaker leads)) AND ((metallic artifacts) OR (metallic components)) AND ((limit study participation) OR (preclude)))"}
{"candidate_id": "LLM06174", "doc_id": "NCT02299063_exc", "case_bucket": "or", "source_criterion": "recent surgery (< 3 months) previous chemotherapy previous transfusion of blood products neurodevelopmental disorders (including Trisomy 21) supplemental oxygen requirement (< 3 months) asthma requiring regular therapy obstructive sleep apnea the presence of concurrent infection or inflammation a known allergy to dexmedetomidine hydrochloride", "candidate_expression": "((Trisomy 21) AND (allergy) AND (asthma) AND (chemotherapy previous) AND (dexmedetomidine hydrochloride) AND (infection) AND (inflammation) AND (neurodevelopmental disorders) AND (obstructive sleep apnea) AND (regular therapy) AND (supplemental oxygen requirement < 3 months) AND (surgery recent < 3 months) AND (transfusion of blood products previous))"}
{"candidate_id": "LLM06175", "doc_id": "NCT03347513_exc", "case_bucket": "or", "source_criterion": "Severe Iron deficiency anemia (hemoglobin < 8.0 g/dL). Parasitic worm infection e.g. schistosomiasis, and hook worm by stool analysis. Any cases giving clinical symptoms of gastritis e.g. nausea, vomiting, dull aching pain or soreness in the epigastrium. Cases with history of gastric ulcer diagnosed by upper endoscopy. Cases complaining of hematemesis.", "candidate_expression": "((< 8.0 g/dL) AND (Iron deficiency anemia) AND (Parasitic worm infection) AND (Severe) AND (clinical symptoms) AND (gastric ulcer) AND (gastritis) AND (hematemesis) AND (hemoglobin) AND (history) AND (stool analysis) AND (upper endoscopy) AND ((dull aching pain) OR (nausea) OR (soreness in the epigastrium) OR (vomiting)) AND ((hook worm) OR (schistosomiasis)))"}
```
