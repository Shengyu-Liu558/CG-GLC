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
{"candidate_id": "LLM03376", "doc_id": "NCT02601157_inc", "case_bucket": "other", "source_criterion": "Patients with de novo stenotic lesions who are suitable for coronary stenting with drug-eluting stent", "candidate_expression": "((coronary stenting suitable) AND (drug-eluting stent) AND (stenotic lesions de novo))"}
{"candidate_id": "LLM03377", "doc_id": "NCT02647788_inc", "case_bucket": "scope", "source_criterion": "Patients undergoing ambulatory hand surgery for carpal tunnel and trigger finger, under local anesthesia with or without sedation.", "candidate_expression": "((ambulatory) AND (carpal tunnel) AND (hand surgery) AND (local anesthesia) AND (trigger finger))"}
{"candidate_id": "LLM03378", "doc_id": "NCT01078051_inc", "case_bucket": "or", "source_criterion": "Patients with angina or silent ischemia and documented ischemia Patients who are eligible for intracoronary stenting Age > 18 years De novo lesion CTO Reference vessel size 2.5 mm by visual estimation At least one CTO lesions located in proximal or mid epicardial coronary artery. (If the patient has two CTO lesions, one CTO lesion should be located in proximal or mid epicardial coronary artery) Angiographically defined total occlusion over 3 months If no definite symptom with total occlusion, two experienced operators decide CTO in consideration of angiographical morphology (degree of calcification, bridging collaterals, non-tapered stump, angiographic filling from collaterals)", "candidate_expression": "((Age > 18 years) AND (CTO De novo lesion) AND (CTO lesions At least one in proximal coronary artery mid epicardial coronary artery) AND (If no definite symptom with total occlusion, two experienced operators decide CTO in consideration of angiographical morphology (degree of calcification, bridging collaterals, non-tapered stump, angiographic filling from collaterals)) AND (Reference vessel size by visual estimation 2.5 mm) AND (angina) AND (coronary artery) AND (intracoronary stenting) AND (ischemia documented) AND (ischemia silent) AND (total occlusion Angiographically defined 3 months))"}
{"candidate_id": "LLM03379", "doc_id": "NCT01217671_exc", "case_bucket": "or", "source_criterion": "FEV1 >= 80% or FEV1 < 20% of predicted value post-bronchodilator. FEV1/SVC>=70% History of lung transplant. Any lung surgery within the past two years. On any thoracic surgery waiting list. End of last exacerbation less than 6 weeks prior to screening/re-screening visit. Clinically significant intercurrent illnesses (except for respiratory or liver disease secondary to AAT deficiency), including: cardiac, hepatic, renal, endocrine, neurological, hematological, neoplastic, immunological, skeletal or other) that in the opinion of the investigator, could interfere with the safety, compliance or other aspects of this study. Patients with well-controlled, chronic diseases could possibly be included after consultation with the treating physician and the sponsor. Active smoking during the last 12 months from screening date. Pregnancy or lactation. Woman of child-bearing potential not taking adequate contraception deemed reliable by the investigator. Presence of psychiatric/ mental disorder or any other medical disorder which might impair the patient's ability to give informed consent or to comply with the requirements of the study protocol. Evidence of ongoing viral infection with HCV, HBV and/or HIV. Evidence of alcohol abuse or history of alcohol abuse or illegal and/or legally prescribed drugs. IgA Deficiency History of life threatening allergy, anaphylactic reaction, or systemic response to human plasma derived products. Participation in another clinical trial within 30 days prior to baseline visit. Inability to attend scheduled clinic visits and/or comply with the study protocol. Any other factor that, in the opinion of the investigator, would prevent the patient from complying with the requirements of the protocol.", "candidate_expression": "((AAT deficiency) AND (Active smoking Active during the last 12 months from screening date) AND (Any other factor that, in the opinion of the investigator, would prevent the patient from complying with the requirements of the protocol.) AND (Clinically significant) AND (Clinically significant intercurrent illnesses (except for respiratory or liver disease secondary to AAT deficiency), including: cardiac, hepatic, renal, endocrine, neurological, hematological, neoplastic, immunological, skeletal or other) that in the opinion of the investigator, could interfere with the safety, compliance or other aspects of this study. Patients with well-controlled, chronic diseases could possibly be included after consultation with the treating physician and the sponsor.) AND (FEV1 < 20% of predicted value post-bronchodilator) AND (FEV1 >= 80%) AND (FEV1/SVC >=70%) AND (HBV) AND (HCV) AND (HIV) AND (IgA Deficiency) AND (Inability to attend scheduled clinic visits and/or comply with the study protocol.) AND (Pregnancy) AND (Presence of psychiatric/ mental disorder or any other medical disorder which might impair the patient's ability to give informed consent or to comply with the requirements of the study protocol.) AND (Woman) AND (Woman of child-bearing potential not taking adequate contraception deemed reliable by the investigator.) AND (abuse illegal drugs) AND (abuse legally prescribed drugs) AND (adequate) AND (alcohol abuse) AND (anaphylactic reaction) AND (bronchodilator) AND (cardiac) AND (child-bearing potential) AND (deemed reliable by the investigator) AND (endocrine) AND (exacerbation less than 6 weeks prior to screening/re-screening visit) AND (hematological) AND (hepatic) AND (immunological) AND (in the opinion of the investigator) AND (intercurrent illnesses Clinically significant) AND (lactation) AND (life threatening allergy life threatening) AND (liver disease) AND (lung surgery within the past two years) AND (lung transplant History) AND (mental disorder) AND (neoplastic) AND (neurological) AND (other) AND (other medical disorder) AND (products human plasma derived) AND (psychiatric disorder) AND (renal) AND (respiratory disease) AND (skeletal) AND (systemic response to human plasma derived products) AND (thoracic surgery) AND (thoracic surgery waiting list) AND (viral infection ongoing) AND NOT (contraception adequate deemed reliable by the investigator))"}
{"candidate_id": "LLM03380", "doc_id": "NCT02384850_exc", "case_bucket": "or", "source_criterion": "adequately controlled with appropriate therapy or would compromise the patient's ability to tolerate this therapy; 2. Treatment with any systemic anticancer therapy ≤ 3 weeks prior to cycle 1 day 1 3. Uncontrolled active infection (Hepatitis B and C infection are NOT exclusion criteria) and/or known HIV infection; 4. Renal failure requiring haemodialysis or peritoneal dialysis; 5. Patients who are pregnant or breast-feeding; 6. Patients with significantly diseased or obstructed gastrointestinal tract, malabsorption, uncontrolled vomiting or diarrhea resulting in inability to swallow oral medications; 7. Presence of symptomatic CNS metastasis 8. Unresolved toxicity from previous anti-cancer therapy or incomplete recovery from surgery, in particular oxaliplatin-induced peripheral neuropathy > grade 1. 9. Any of the following within the 12 months prior to study drug administration: myocardial infarction, severe/unstable angina, coronary/peripheral artery bypass graft, symptomatic congestive heart failure, cerebrovascular accident or transient ischemic attack, pulmonary embolism, deep vein thrombosis, or other thromboembolic event.", "candidate_expression": "((CNS metastasis) AND (HIV infection) AND (Hepatitis B infection) AND (Hepatitis C infection) AND (NOT) AND (Renal failure) AND (Uncontrolled) AND (Unresolved toxicity) AND (active) AND (adequately controlled with appropriate therapy or would compromise the patient's ability to tolerate this therapy; 2.) AND (anti-cancer therapy) AND (breast-feeding) AND (cerebrovascular accident) AND (coronary artery bypass graft) AND (cycle 1) AND (deep vein thrombosis) AND (diarrhea) AND (diseased gastrointestinal tract) AND (haemodialysis) AND (inability to swallow oral medications) AND (incomplete recovery) AND (infection) AND (malabsorption) AND (myocardial infarction) AND (obstructed gastrointestinal tract) AND (other thromboembolic event) AND (oxaliplatin) AND (oxaliplatin-induced) AND (peripheral artery bypass graft) AND (peripheral neuropathy) AND (peritoneal dialysis) AND (pregnant) AND (previous) AND (pulmonary embolism) AND (severe angina) AND (significantly) AND (study drug administration) AND (surgery) AND (symptomatic) AND (symptomatic congestive heart failure) AND (systemic anticancer therapy) AND (transient ischemic attack) AND (uncontrolled) AND (unstable angina) AND (vomiting) AND (within the 12 months prior to study drug administration) AND (≤ 3 weeks prior to cycle 1))"}
{"candidate_id": "LLM03381", "doc_id": "NCT02529475_exc", "case_bucket": "or", "source_criterion": "Patients minors Patients on a legal protection regime type guardianship Respiratory pathologies, cardiovascular, renal, diabetes Claustrophobia Contraindications to exposure to a magnetic field Contraindications to injecting Dotarem ®", "candidate_expression": "((Claustrophobia) AND (Contraindications) AND (Dotarem) AND (legal protection regime type guardianship) AND (magnetic field) AND (minors) AND ((Respiratory pathologies) OR (cardiovascular) OR (diabetes) OR (renal)))"}
{"candidate_id": "LLM03382", "doc_id": "NCT01701219_inc", "case_bucket": "or", "source_criterion": "1. Presence of bacteremia due solely to: S. aureus on at least 1 blood culture within 72 hours of beginning study drug (Cohort A) OR MRSA on a baseline blood culture and on at least 1 additional blood culture after at least 72 hours of vancomycin and/or daptomycin treatment (Cohort B). 2. Male or female ≥ 18 years of age. 3. If female of childbearing potential must be willing to practice sexual abstinence or dual methods of contraception during treatment and for at least 30 days after the last dose of study drug. 4. Expectation of survival for at least 2 months.", "candidate_expression": "((Expectation) AND (MRSA) AND (Male) AND (S. aureus) AND (after at least 72 hours of vancomycin and/or daptomycin treatment) AND (age) AND (at least 1) AND (at least 1 additional) AND (bacteremia) AND (baseline) AND (beginning study drug) AND (blood culture) AND (childbearing potential) AND (daptomycin) AND (daptomycin treatment) AND (dual) AND (during treatment) AND (female) AND (for at least 2 months) AND (for at least 30 days after the last dose of study drug) AND (methods of contraception) AND (practice sexual abstinence) AND (survival) AND (the last dose of study drug) AND (vancomycin) AND (vancomycin and/or daptomycin treatment) AND (vancomycin treatment) AND (willing) AND (within 72 hours of beginning study drug) AND (≥ 18 years))"}
{"candidate_id": "LLM03383", "doc_id": "NCT02384850_exc", "case_bucket": "or", "source_criterion": "adequately controlled with appropriate therapy or would compromise the patient's ability to tolerate this therapy; 2. Treatment with any systemic anticancer therapy ≤ 3 weeks prior to cycle 1 day 1 3. Uncontrolled active infection (Hepatitis B and C infection are NOT exclusion criteria) and/or known HIV infection; 4. Renal failure requiring haemodialysis or peritoneal dialysis; 5. Patients who are pregnant or breast-feeding; 6. Patients with significantly diseased or obstructed gastrointestinal tract, malabsorption, uncontrolled vomiting or diarrhea resulting in inability to swallow oral medications; 7. Presence of symptomatic CNS metastasis 8. Unresolved toxicity from previous anti-cancer therapy or incomplete recovery from surgery, in particular oxaliplatin-induced peripheral neuropathy > grade 1. 9. Any of the following within the 12 months prior to study drug administration: myocardial infarction, severe/unstable angina, coronary/peripheral artery bypass graft, symptomatic congestive heart failure, cerebrovascular accident or transient ischemic attack, pulmonary embolism, deep vein thrombosis, or other thromboembolic event.", "candidate_expression": "((CNS metastasis) AND (HIV infection) AND (Hepatitis B infection) AND (Hepatitis C infection) AND (NOT) AND (Renal failure) AND (Uncontrolled) AND (active) AND (adequately controlled with appropriate therapy or would compromise the patient's ability to tolerate this therapy; 2.) AND (anti-cancer therapy) AND (cycle 1) AND (inability to swallow oral medications) AND (infection) AND (oxaliplatin) AND (oxaliplatin-induced) AND (peripheral neuropathy) AND (previous) AND (significantly) AND (surgery) AND (symptomatic) AND (systemic anticancer therapy) AND (uncontrolled) AND (≤ 3 weeks prior to cycle 1) AND ((haemodialysis) OR (peritoneal dialysis)) AND ((breast-feeding) OR (pregnant)) AND ((diseased gastrointestinal tract) OR (obstructed gastrointestinal tract)) AND ((diarrhea) OR (malabsorption) OR (vomiting)) AND ((Unresolved toxicity) OR (incomplete recovery)) AND ((study drug administration) OR (within the 12 months prior to study drug administration)) AND ((cerebrovascular accident) OR (coronary artery bypass graft) OR (deep vein thrombosis) OR (myocardial infarction) OR (other thromboembolic event) OR (peripheral artery bypass graft) OR (pulmonary embolism) OR (severe angina) OR (symptomatic congestive heart failure) OR (transient ischemic attack) OR (unstable angina)))"}
{"candidate_id": "LLM03384", "doc_id": "NCT02652572_inc", "case_bucket": "or", "source_criterion": "1. Age 18 years or older 2. Diagnosis of venous leg ulcer(s), as clinically determined by the investigator by a positive venous reflux test (venous refilling <20 seconds) using Doppler ultrasound for at least 4 weeks prior to screening day, which have not adequately responded to conventional ulcer therapy. 3. Designated venous leg ulcer meets the following criteria at both the screening and baseline visits. If the patient has multiple ulcers, at least one ulcer must meet the following criteria at both the screening and baseline visits: 1. Present for at least 4 weeks 2. CEAP Classification Stage 6 3. Surface ulcer with an area > 15cm2 post debridement 4. Viable, granulating wound (investigator discretion) 4. Ulcers that extend through the epidermis but not through the muscle, tendon, or bone (Stage II or III ulcers as defined by the IAET). 5. Female patients of childbearing potential must have a negative pregnancy test at screening and must agree to use hormonal contraceptive, intrauterine device, diaphragm with spermicide, condom with spermicide, or abstinence throughout until 2 weeks after the last administration of study drug 6. Signed informed consent", "candidate_expression": "((18 years or older) AND (<20 seconds) AND (> 15cm2) AND (Age) AND (CEAP Classification) AND (Doppler ultrasound) AND (Female) AND (IAET) AND (Present) AND (Signed informed consent) AND (Stage 6) AND (Stage II or III) AND (Surface ulcer) AND (Ulcers) AND (Viable) AND (adequately) AND (area post debridement) AND (at least 4 weeks) AND (at least 4 weeks prior to screening day) AND (at least one) AND (at screening) AND (childbearing potential) AND (conventional ulcer therapy) AND (granulating) AND (investigator discretion) AND (last administration of study drug) AND (multiple) AND (negative) AND (not) AND (positive) AND (responded) AND (screening) AND (screening day) AND (throughout until 2 weeks after the last administration of study drug) AND (ulcer) AND (ulcers) AND (venous leg ulcer) AND (venous leg ulcer(s)) AND (venous refilling) AND (venous reflux test) AND (wound) AND ((extend through the bone) OR (extend through the epidermis) OR (extend through the muscle) OR (extend through the tendon)) AND ((abstinence) OR (condom with spermicide) OR (diaphragm with spermicide) OR (hormonal contraceptive) OR (intrauterine device) OR (pregnancy test)))"}
{"candidate_id": "LLM03385", "doc_id": "NCT03380429_inc", "case_bucket": "or", "source_criterion": "Subjects aged 18 years or older, at the time of signing the informed consent. Subjects with documented physician diagnosis of asthma as their primary respiratory disease. ACT score <20 at screening visit. Non-smokers (never smoked or not smoking for >6 months with <10 pack years history (Pack years = [cigarettes per day smoked/20] multiplied by number of years smoked). Male or female subjects will be included. A female subject is eligible to participate if she is not pregnant, not breastfeeding, and at least one of the following conditions applies: (i) Not a woman of childbearing potential (WOCBP). (ii) A WOCBP who agrees to follow the contraceptive guidance during the treatment period and for at least 5 days] after the last dose of study treatment. Capable of giving signed informed consent which includes compliance with the requirements and restrictions listed in the consent form and protocol. Subject understands and is willing, able, and likely to comply with study procedures and restrictions. Subject must be able to read in a language supported by the smart phone app in their region. Subject must have been on maintenance therapy (Fixed dose combination ICS/LABA) for 3 months, cannot have changed dose in the month prior to screening and be able to change to an equivalent dose of RELVAR/BREO for the duration of the study. Other background asthma medication such as anti-leukotrienes and oral corticosteroids are permitted provided the dose has been stable for 1 month prior to screening. Subject must be able to change to Salbutamol/Albuterol MDI rescue for the duration of the study and judged capable of withholding albuterol/salbutamol for at least 6 hours prior to study visits. Subject must have their own Android or iPhone operating system (IOS) smart phone and a data package suitable for the installation and running of the app and sending and receiving data. Data used by the CIS is approximately 1 megabyte (MB) per month as a maximum; this is less data than a 1 minute video streamed from YouTube (2MB). Subjects must be willing and able to download the app on their personal smart phone and keep it turned on for the duration of the study. This will also require Bluetooth to be turned on for duration of the study. Subjects will also have to turn on mobile data for the app for the duration of study; unless travelling and when extra data roaming costs could be incurred. ACT score <20 at randomization visit (visit 2).", "candidate_expression": "((18 years or older) AND (<10) AND (<20) AND (A female subject is eligible to participate if she is not pregnant, not breastfeeding, and at least one of the following conditions applies: (i) Not a woman of childbearing potential (WOCBP). (ii) A WOCBP who agrees to follow the contraceptive guidance during the treatment period and for at least 5 days] after the last dose of study treatment.) AND (ACT score) AND (Albuterol) AND (Capable of giving signed informed consent which includes compliance with the requirements and restrictions listed in the consent form and protocol.) AND (Fixed dose) AND (MDI rescue) AND (Male) AND (Non-smokers) AND (Salbutamol) AND (able to) AND (aged) AND (albuterol) AND (asthma) AND (at randomization visit) AND (at screening visit) AND (at the time of signing the informed consent) AND (cannot) AND (capable of withholding) AND (change) AND (changed dose) AND (combination ICS/LABA) AND (female) AND (for 3 months) AND (for >6 months) AND (for at least 6 hours) AND (for the duration of the study) AND (in the month prior to screening) AND (maintenance therapy) AND (never smoked) AND (not smoking) AND (pack years) AND (primary respiratory disease) AND (prior to study visits) AND (salbutamol) AND (signing the informed consent) AND (the duration of the study) AND (the month prior to screening))"}
{"candidate_id": "LLM03386", "doc_id": "NCT02579928_exc", "case_bucket": "or", "source_criterion": "Current inpatient hospitalization or active suicidal ideation requiring referral for inpatient hospitalization for safety. History of psychotic disorder or manic episode diagnosed by MINI-KID History of substance dependence diagnosis by MINI-KID (excluding tobacco) or positive urine toxicology. Pregnancy (urine pregnancy tests on the day of scans for menstruating girls). Inability to provide written informed consent according to the Yale Human Investigation Committee (HIC) guidelines in English.", "candidate_expression": "((Current) AND (History) AND (Inability to provide) AND (MINI-KID) AND (Pregnancy) AND (Yale Human Investigation Committee (HIC) guidelines) AND (active) AND (excluding) AND (in English) AND (inpatient) AND (inpatient hospitalization) AND (menstruating girls) AND (on the day of scans) AND (positive) AND (referral) AND (requiring) AND (tobacco) AND (urine pregnancy tests) AND (written informed consent) AND ((manic episode) OR (psychotic disorder)) AND ((substance dependence) OR (urine toxicology)) AND ((hospitalization) OR (suicidal ideation)))"}
{"candidate_id": "LLM03387", "doc_id": "NCT02046395_exc", "case_bucket": "or", "source_criterion": "Pregnancy Patients with chronic kidney disease stage with eGFR < 30 ml/min (CKD stage IV and V) Nephrotic range proteinuria (urinary protein > 3.5 gm/day) History or renal transplantation History of multiple myeloma Known history of hypersensitivity reaction or intolerability to Ace Inh or ARB.", "candidate_expression": "((ARB) AND (Ace Inh) AND (CKD stage IV stage V) AND (Pregnancy) AND (chronic kidney disease) AND (eGFR < 30 ml/min) AND (hypersensitivity reaction) AND (intolerability) AND (multiple myeloma History) AND (proteinuria Nephrotic range) AND (renal transplantation History) AND (urinary protein > 3.5 gm/day))"}
{"candidate_id": "LLM03388", "doc_id": "NCT00785213_inc", "case_bucket": "or", "source_criterion": "Healthy adults 18-45 years of age Non-smoking Non-pregnant (post-menopausal, surgically sterile or using effective contraceptive measures) Body mass index (BMI) less than or equal to 32 Medically healthy on the basis of medical history and physical examination Hemoglobin > or = to 11.5g/dL Completion of the screening process within 28 days prior to dosing Provision of voluntary written informed consent", "candidate_expression": "((18-45 years of age) AND (> or = to 11.5g/dL) AND (Body mass index (BMI)) AND (Healthy) AND (Hemoglobin) AND (Medically healthy) AND (Non) AND (Provision of voluntary written informed consent) AND (adults) AND (contraceptive measures) AND (dosing) AND (effective) AND (less than or equal to 32) AND (medical history) AND (of age) AND (physical examination) AND (post-menopausal) AND (pregnant) AND (screening process) AND (smoking) AND (surgically) AND (surgically sterile) AND (within 28 days prior to dosing))"}
{"candidate_id": "LLM03389", "doc_id": "NCT03011476_exc", "case_bucket": "other", "source_criterion": "Significant motor complication affecting daily activities Drugs related to acetylcholine metabolism", "candidate_expression": "((Drugs) AND (Significant) AND (acetylcholine) AND (motor complication) AND (related to acetylcholine metabolis))"}
{"candidate_id": "LLM03390", "doc_id": "NCT02364648_exc", "case_bucket": "other", "source_criterion": "History of cardiovascular disease; Current pregnancy; Uncontrolled hypertension; Uncontrolled hyperlipidemia; Current hormone replacement therapy; Current use of tobacco products; Elevated liver enzymes; Current autoimmune disease; Daily use of of antioxidants >300mg", "candidate_expression": "((Elevated liver enzymes) AND (History) AND (antioxidants Daily use >300mg) AND (autoimmune disease Current) AND (cardiovascular disease) AND (hormone replacement therapy Current) AND (hyperlipidemia Uncontrolled) AND (hypertension Uncontrolled) AND (pregnancy Current) AND (use of tobacco products Current))"}
{"candidate_id": "LLM03391", "doc_id": "NCT01978028_exc", "case_bucket": "or", "source_criterion": "Hemochromatosis, iron overload, defined as TSAT > 45% Known hypersensitivity to Ferinject®. Known active infection, CRP>20 mg/L, clinically significant bleeding, active malignancy. Chronic liver disease and/or screening alanine transaminase (ALT) or aspartate transaminase (AST) above three times the upper limit of the normal range. Immunosuppressive therapy or renal dialysis (current or planned within the next 6 months). History of erythropoietin, i. v. or oral iron therapy, and blood transfusion in previous 12 weeks and/or such therapy planned within the next 6 months. Unstable angina pectoris as judged by the investigator, clinically significant uncorrected valvular disease or left ventricular outflow obstruction, obstructive cardiomyopathy, poorly controlled fast atrial fibrillation or flutter, poorly controlled symptomatic brady- or tachyarrhythmias. Acute myocardial infarction or acute coronary syndrome, transient ischemic attack or stroke within the last 3 months. Coronary-artery bypass graft, percutaneous intervention (e.g. cardiac, cerebrovascular, aortic; diagnostic catheters are allowed) or major surgery, including thoracic and cardiac surgery, within the last 3 months. Participation in a CHF training program. Known HIV/AIDS. Inability to fully comprehend and/or perform study procedures in the investigator's opinion. Vitamin B12 and/or serum folate deficiency according to the laboratory (re-screening is possible after substitution therapy). Pregnancy or lactation. Participation in another clinical trial within previous 30 days and/or anticipated participation in another trial during this study. Anticoagulation", "candidate_expression": "((> 45%) AND (>20 mg/L) AND (AIDS) AND (Anticoagulation) AND (CRP) AND (Chronic liver disease) AND (Ferinject®) AND (Hemochromatosis) AND (Inability to fully comprehend and/or perform study procedures in the investigator's opinion) AND (Known HIV) AND (Participation in another clinical trial within previous 30 days and/or anticipated participation in another trial during this study.) AND (TSAT) AND (Unstable angina pectoris) AND (above three times the upper limit of the normal range) AND (active) AND (clinically significant) AND (hypersensitivity) AND (iron overload) AND (planned) AND (poorly controlled) AND (symptomatic) AND (the last 3 months) AND (the next 6 months) AND (within the last 3 months) AND (within the next 6 months) AND ((alanine transaminase (ALT)) OR (aspartate transaminase (AST))) AND ((Immunosuppressive therapy) OR (renal dialysis)) AND ((current) OR (planned)) AND ((blood transfusion) OR (erythropoietin) OR (i. v. iron therapy) OR (oral iron therapy)) AND ((in previous 12 weeks) OR (within the next 6 months)) AND ((left ventricular outflow obstruction) OR (obstructive cardiomyopathy) OR (valvular disease)) AND ((fast atrial fibrillation) OR (fast atrial flutter)) AND ((brady-) OR (tachyarrhythmias)) AND ((Acute myocardial infarction) OR (acute coronary syndrome) OR (stroke) OR (transient ischemic attack)) AND ((Coronary-artery bypass graft) OR (major surgery) OR (percutaneous intervention)) AND ((cardiac surgery) OR (thoracic surgery)) AND ((Vitamin B12 deficiency) OR (serum folate deficiency)) AND ((Pregnancy) OR (lactation)) AND ((active infection) OR (bleeding) OR (malignancy)))"}
{"candidate_id": "LLM03392", "doc_id": "NCT02462317_exc", "case_bucket": "or", "source_criterion": "Previous antispastic drugs Contraindication for baclofen or toxin Antecedent of epileptic seizure Psychiatric antecedent", "candidate_expression": "((Contraindication) AND (Psychiatric antecedent) AND (antispastic drugs Previous) AND (epileptic seizure Antecedent) AND ((baclofen) OR (toxin)))"}
{"candidate_id": "LLM03393", "doc_id": "NCT03639545_inc", "case_bucket": "other", "source_criterion": "diabetes mellitus type 1", "candidate_expression": "(diabetes mellitus type 1)"}
{"candidate_id": "LLM03394", "doc_id": "NCT02783859_inc", "case_bucket": "or", "source_criterion": "Hospitalised children aged 3-mo to 5-yrs (in Darwin, children have to be Indigenous) Have features of severe pneumonia on admission (temperature >37.5 celsius or a history of fever at home or observed at the referring clinic, age-adjusted tachypnoea [respiratory rate>50 if <12-months; respiratory rate>40 if >12-months] with chest wall recession and/or oxygen saturation <92% in air), and consolidation on chest X-ray as diagnosed by treating clinician After 1-3 days of IV antibiotics, are afebrile, with improved respiratory symptoms and signs, oxygen saturation>90% in air and are ready to be switched to oral amoxicillin-clavulanate, and Have symptoms of no longer than 7 days at point of hospitalisation.", "candidate_expression": "((Hospitalised) AND (aged 3-mo to 5-yrs) AND (chest X-ray) AND (children) AND (consolidation) AND (pneumonia severe) AND (respiratory rate >40) AND (respiratory rate >50) AND (symptoms no longer than 7 days at point of hospitalisation) AND (tachypnoea) AND (temperature >37.5 celsius) AND ((age <12-months) OR (age >12-months)) AND ((chest wall recession) OR (oxygen saturation <92% in air)))"}
{"candidate_id": "LLM03395", "doc_id": "NCT02797548_inc", "case_bucket": "or", "source_criterion": "Planned non-cardiac surgery at least after 12 months of implantation of drug eluting stent Low or intermediate risk level surgery Written informed consent", "candidate_expression": "((Written informed consent) AND (drug eluting stent) AND (implantation) AND (non-cardiac surgery Planned at least after 12 months of implantation of drug eluting stent) AND ((intermediate risk level surgery) OR (risk level surgery Low)))"}
{"candidate_id": "LLM03396", "doc_id": "NCT02489045_inc", "case_bucket": "other", "source_criterion": "Be scheduled for trans-jugular liver biopsy the day of the ultrasound procedure. Be at least 21 years of age. Be medically stable. If a female of child-bearing potential, must have a negative pregnancy test. Be conscious and able to comply with study procedures. Have read and signed the IRB-approved Informed Consent form for participating in the study.", "candidate_expression": "((Have read and signed the IRB-approved Informed Consent form for participating in the study.) AND (age) AND (at least 21 years) AND (child-bearing potential) AND (female) AND (medically stable) AND (negative) AND (pregnancy test) AND (the day of the ultrasound procedure) AND (trans-jugular liver biopsy) AND (ultrasound procedure))"}
{"candidate_id": "LLM03397", "doc_id": "NCT00752310_exc", "case_bucket": "or", "source_criterion": "No positive HIV 1 or HIV 2 test at screening no history of significant skin disease such as, but not limited to rash or eruptions, drug allergies, food allergy, dermatitis, eczema, psoriasis, or urticaria no history of allergy to drugs such as, but not limited to, sulphonamides and penicillins no previously demonstrated clinically significant allergy or hypersensitivity to any of the excipients of the investigational medication administered in this trial no female subject of childbearing potential without use of effective nonhormonal birth control methods, or not willing to continue practicing these birth control methods for at least 30 days after the end of the treatment period no positive pregnancy test or breast feeding at screening", "candidate_expression": "((HIV 1 test screening) AND (HIV 2 test) AND (allergy) AND (allergy history) AND (birth control methods willing to continue practicing for at least 30 days after the end of the treatment period) AND (breast feeding) AND (childbearing potential) AND (dermatitis) AND (drug allergies) AND (eczema) AND (eruptions) AND (excipients of the investigational medication) AND (female) AND (food allergy) AND (hypersensitivity) AND (penicillins) AND (pregnancy test positive) AND (psoriasis) AND (rash) AND (skin disease history significant) AND (sulphonamides) AND (urticaria) AND NOT (nonhormonal birth control effective))"}
{"candidate_id": "LLM03398", "doc_id": "NCT01410890_exc", "case_bucket": "other", "source_criterion": "The patient is participating in another clinical study using an investigational product. The patient, in the opinion of the Investigator, is unable to adhere to the requirements of the study.", "candidate_expression": "(The patient is participating in another clinical study using an investigational product)"}
{"candidate_id": "LLM03399", "doc_id": "NCT02654912_exc", "case_bucket": "or", "source_criterion": "contraindications from manufacturer for medications including currently taking haloperidol, artane, Phenergan (Promethazine), chlorpromazine, erythromycin, Azithromycin, clarithromycin, Ketoconazole, fluconazole, mefloquine (as prophylaxis), lumefantrine (in Coartem), quinine, Septrin anyone seriously ill currently taking antimalarial medicines allergy to artemisinin drugs pregnant women in first trimester children under 3 months of age reported heart condition", "candidate_expression": "((Coartem) AND (Promethazine) AND (age) AND (allergy) AND (antimalarial medicines) AND (artemisinin drugs) AND (children) AND (contraindications) AND (first trimester) AND (heart condition) AND (pregnant) AND (seriously ill) AND (under 3 months) AND (women) AND ((Azithromycin) OR (Ketoconazole) OR (Phenergan) OR (Septrin) OR (artane) OR (chlorpromazine) OR (clarithromycin) OR (erythromycin) OR (fluconazole) OR (haloperidol) OR (lumefantrine) OR (mefloquine) OR (quinine)))"}
{"candidate_id": "LLM03400", "doc_id": "NCT02862314_exc", "case_bucket": "or", "source_criterion": "pregnancy, patients under legal custody, patients without health insurance, patients included in another interventional clinical study involving infections or antibiotics and having the same primary parameter, moribund patients, situation in which the procalcitonin concentration could be increased without correlation to an infectious process (poly-traumatised patients, surgical interventions within the last 4 days, cardiorespiratory arrest, administration of anti-thymocyte globulin, immunodepressed patients (bone marrow transplant patients, patients with severe neutropenia), patients with an absolute indication for administration of antibiotics at the moment of ICU admission (meningitis, pneumonia) or a chronic infection for which long-term antibiotic treatment is necessary (endocarditis, osteo-articular infections, mediastinitis, deep abscesses, pneumocystis infection, toxoplasmosis, tuberculosis) patients with haemodynamic instability of septic origin or a respiratory insufficiency (defined by a ratio Pa02/Fi02 = 200 mmHg and PEP = 5 cmH2O)", "candidate_expression": "((ICU) AND (PEP = 5 cmH2O) AND (Pa02/Fi02 = 200 mmHg) AND (anti-thymocyte globulin) AND (antibiotic treatment long-term) AND (antibiotics) AND (cardiorespiratory arrest) AND (chronic infection) AND (deep abscesses) AND (endocarditis) AND (immunodepressed) AND (indication) AND (legal custody) AND (mediastinitis) AND (moribund) AND (osteo-articular infections) AND (patients included in another interventional clinical study involving infections or antibiotics and having the same primary parameter) AND (pneumocystis infection) AND (poly-traumatised) AND (pregnancy) AND (procalcitonin concentration increased) AND (septic) AND (surgical interventions last 4 days) AND (toxoplasmosis) AND (tuberculosis) AND NOT (health insurance) AND ((bone marrow transplant) OR (severe neutropenia)) AND ((meningitis) OR (pneumonia)) AND ((espiratory insufficiency) OR (haemodynamic instability)))"}
```
