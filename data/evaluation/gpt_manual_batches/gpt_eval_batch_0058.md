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
{"candidate_id": "LLM01426", "doc_id": "NCT01911650_exc", "case_bucket": "or", "source_criterion": "1. bilateral AT 2. insertional AT 3. local steroid injection within 6 weeks or physical therapy within 4 weeks 4. inability to comply with follow-up criteria 5. history of surgery on the Achilles tendon or systemic diseases (general inflammatory diseases such as rheumatologic disorders and diabetes) 6. daily use of opioids for pain 7. anticoagulation or immunosuppressive therapy 8. intent to use NSAIDs or steroids 9. self-reported pregnancy", "candidate_expression": "((NSAIDs) AND (anticoagulation therapy) AND (bilateral AT) AND (diabetes) AND (general inflammatory diseases) AND (immunosuppressive therapy) AND (inability to comply with follow-up criteria) AND (insertional AT) AND (local steroid injection within 6 weeks) AND (opioids daily) AND (pain) AND (physical therapy within 4 weeks) AND (pregnancy) AND (rheumatologic disorders) AND (steroids) AND (surgery on the Achilles tendon history) AND (systemic diseases))"}
{"candidate_id": "LLM01427", "doc_id": "NCT02225548_inc", "case_bucket": "other", "source_criterion": "Diagnosis of idiopathic Parkinson's disease that is optimally treated (motor fluctuations <20% of subject's awake time). Subjects may be on levodopa therapy but must be stable at the time of entry into the study Sexually active (i.e. =1 attempt/week) males, 40 - 64 years of age (inclusive) at time of screening Diagnosis of moderate erectile dysfunction (defined according to the NIH Consensus Development Panel on Impotence) for more than 6 months and demonstrating and incomplete response to tadalafil alone Subject demonstrating an IIEF-5 drug-free baseline score that is = 10 but = 16, and an IIEF-5 tadalafil-alone baseline score that is = 18 Subject in a stable heterosexual relationship for at least 6 months. (2) Subject motivated to seek treatment for erectile dysfunction. Subject with a total serum testosterone level = 300 ng/dL, with or without supplementation Hoehn and Yahr Scale score of 1 - 3 Patient able to consent and comply with protocol requirements", "candidate_expression": "((Hoehn and Yahr Scale score 1 - 3) AND (IIEF-5 drug-free baseline score = 10 but = 16) AND (IIEF-5 tadalafil-alone baseline score = 18) AND (Patient able to consent and comply with protocol requirements) AND (Sexually active =1 attempt/week) AND (Subject motivated to seek treatment for erectile dysfunction) AND (age 40 - 64 years) AND (erectile dysfunction) AND (erectile dysfunction moderate for more than 6 months) AND (heterosexual relationship stable at least 6 months) AND (idiopathic Parkinson's disease treated) AND (males) AND (motor fluctuations <20% of subject's awake time) AND (response incomplete) AND (tadalafil) AND (total serum testosterone level = 300 ng/dL) AND (treatment))"}
{"candidate_id": "LLM01428", "doc_id": "NCT02867618_exc", "case_bucket": "or", "source_criterion": "1. Prior Therapy Exposure to chemotherapy or radiotherapy within 2 weeks prior to entering the study or those who have not recovered from adverse events due to agents administered more than 2 weeks earlier. Systemic steroids that have not been stabilized (≥ 5 days) to the equivalent of ≤10 mg/day prednisone prior to the start of the study drugs. No other investigational agents are allowed. 2. History of allergic reactions to TGR-1202 or carfilzomib 3. Uncontrolled inter-current illness 4. Pregnant women 5. Nursing women 6. Current malignancy or history of a prior malignancy 7. Patient known to be Human Immunodeficiency Virus (HIV)-positive 8. Active Hepatitis A, Hepatitis B, or Hepatitis C infection", "candidate_expression": "((Current) AND (Hepatitis A) AND (Hepatitis B) AND (Hepatitis C) AND (History) AND (Human Immunodeficiency Virus (HIV)) AND (Nursing) AND (Pregnant) AND (Prior) AND (Systemic steroids) AND (TGR-1202) AND (Uncontrolled) AND (adverse events) AND (agents) AND (allergic reactions) AND (carfilzomib) AND (chemotherapy) AND (due to) AND (entering the study) AND (history of a prior) AND (inter-current) AND (inter-current illness) AND (malignancy) AND (more than 2 weeks earlier) AND (not) AND (other investigational agents) AND (positive) AND (prednisone) AND (prior to) AND (radiotherapy) AND (recovered) AND (stabilized) AND (start of the study drugs) AND (within 2 weeks prior) AND (women) AND (≤10 mg/day) AND (≥ 5 days))"}
{"candidate_id": "LLM01429", "doc_id": "NCT03029078_exc", "case_bucket": "or", "source_criterion": "Pregnant woman or breastfeeding immunosuppression including AIDS, corticosteroids over 60mg/day ongoing antibiotic treatment at the day of inclusion impossibility to obtain a signed consent form.", "candidate_expression": "((AIDS) AND (Pregnant) AND (antibiotic) AND (breastfeeding) AND (corticosteroids over 60mg/day) AND (immunosuppression) AND (impossibility to obtain signed consent form) AND (treatment at the day of inclusion) AND (woman))"}
{"candidate_id": "LLM01430", "doc_id": "NCT02301039_exc", "case_bucket": "or", "source_criterion": "Prior systemic therapy targeting PD-1: PD-L1 axis. Patients who are curable by conventional multidisciplinary management. Patients with severe and/or uncontrolled concurrent medical disease that in the opinion of the investigator could cause unacceptable safety risks or compromise compliance with the protocol. Patients who have received wide field radiotherapy ≤ 4 weeks or limited field radiation for palliation < 2 weeks prior to screening or who have not recovered adequately from side effects of such therapy. Patients who have active infections requiring therapy. Patients that are known to be positive for Human Immunodeficiency Virus (HIV) (HIV 1/2 antibodies), active Hepatitis B (HBsAg reactive), or Hepatitis C (HCV RNA [qualitative] is detected); patients with negative Hepatitis C antibody testing may not need RNA testing. Patients that have a known psychiatric or substance abuse disorder that would interfere with cooperation with the requirements of the trial. Patients who received systemic anti-cancer treatment prior to the first dose of study drug within the following time frames: Patients with active autoimmune disease or a documented history of autoimmune disease or syndrome that requires systemic steroids or immunosuppressive agents. Patients with vitiligo or resolved childhood asthma/atopy would be exception to this rule. Patients that require inhaled steroids or local steroid injections would not be excluded from the study. Patients with hypothyroidism not from autoimmune disease that is stable on hormone replacement will not be excluded from the study. Women who are pregnant or nursing/breastfeeding. Known hypersensitivity to pembrolizumab or another mAb. Has a history of (non-infectious) pneumonitis that required steroids or current pneumonitis. Patients with untreated central nervous system disease. Patients with controlled treated CNS lesions who have undergone surgery or stereotactic radiosurgery and stable for 4 weeks are eligible. Inability to comply with protocol required procedures. Patients with medical conditions that require chronic systemic corticosteroid therapy or require any other form of immunosuppressive medication. However, patients using physiologic replacement doses of hydrocortisone, or its equivalent, will be considered eligible for this study: up to 20 mg hydrocortisone (or 5 mg of prednisone) in the morning and 10 mg hydrocortisone (or 2.5 mg prednisone) in the evening. Patients with the risk factors for bowel obstruction or bowel perforation (examples include but not limited to a history of acute diverticulitis, intra-abdominal abscess, abdominal carcinomatosis). Patients who have received a live vaccine within 30 days prior to the first dose of trial treatment.", "candidate_expression": "((10 mg) AND (2.5 mg) AND (5 mg) AND (< 2 weeks prior to screening) AND (CNS lesions) AND (HBsAg) AND (HCV RNA [qualitative]) AND (HIV 1/2 antibodies) AND (Hepatitis C antibody) AND (Inability to comply with protocol required procedures.) AND (Patients that have a known psychiatric or substance abuse disorder that would interfere with cooperation with the requirements of the trial.) AND (Women) AND (active) AND (adequately) AND (autoimmune disease) AND (bowel obstruction) AND (bowel perforation) AND (central nervous system disease) AND (chronic) AND (concurrent) AND (controlled) AND (conventional multidisciplinary management) AND (curable) AND (current) AND (detected) AND (for 4 weeks) AND (history) AND (hormone replacement) AND (hydrocortisone) AND (hypothyroidism) AND (immunosuppressive agents) AND (immunosuppressive medication) AND (in the evening) AND (in the morning) AND (in the opinion of the investigator) AND (infections) AND (live vaccine) AND (mAb) AND (medical conditions) AND (medical disease) AND (negative) AND (not) AND (pembrolizumab) AND (physiologic replacement doses) AND (positive) AND (prior to the first dose of study drug) AND (reactive) AND (required steroids) AND (requiring therapy) AND (resolved) AND (screening) AND (side effects of such therapy) AND (stable) AND (stable on hormone replacement) AND (steroids) AND (such therapy) AND (systemic anti-cancer treatment) AND (systemic corticosteroid therapy) AND (systemic steroids) AND (systemic therapy targeting PD-1: PD-L1 axis) AND (the first dose of study drug) AND (the first dose of trial treatment) AND (therapy) AND (treated) AND (untreated) AND (up to 20 mg) AND (within 30 days prior to the first dose of trial treatment) AND (≤ 4 weeks) AND ((require chronic systemic corticosteroid therapy) OR (require immunosuppressive medication)) AND ((hydrocortisone) OR (prednisone)) AND ((risk factors for bowel obstruction) OR (risk factors for bowel perforation)) AND ((abdominal carcinomatosis) OR (acute diverticulitis) OR (intra-abdominal abscess)) AND ((limited field radiation for palliation) OR (recovered) OR (wide field radiotherapy)) AND ((Hepatitis C) OR (Human Immunodeficiency Virus (HIV)) OR (active Hepatitis B)) AND ((psychiatric disorder) OR (substance abuse disorder)) AND ((autoimmune disease) OR (syndrome that requires immunosuppressive agents) OR (syndrome that requires systemic steroids)) AND ((atopy) OR (childhood asthma) OR (vitiligo)) AND ((breastfeeding) OR (nursing) OR (pregnant)) AND ((hypersensitivity to mAb) OR (hypersensitivity to pembrolizumab)) AND ((pneumonitis)) AND ((stereotactic radiosurgery) OR (surgery)) AND ((severe) OR (uncontrolled)))"}
{"candidate_id": "LLM01431", "doc_id": "NCT03530124_inc", "case_bucket": "other", "source_criterion": "=32 weeks gestational age at birth =6 weeks postnatal age at randomization Remains hospitalized after birth (has never been discharged home) Treating clinician deems infant eligible to receive 2-month vaccines English- or Spanish-speaking parent(s)/legally authorized representative(s) (LAR(s)) Not planned for discharge within 60 hours of study entry The parent/guardian must be willing and capable of providing permission for their child to participate through the written informed consent process", "candidate_expression": "((2-month vaccines) AND (=32 weeks) AND (=6 weeks) AND (Not) AND (The parent/guardian must be willing and capable of providing permission for their child to participate through the written informed consent process) AND (after birth) AND (at randomization) AND (birth) AND (discharge) AND (eligible) AND (gestational age at birth) AND (hospitalized) AND (planned) AND (postnatal age) AND (study entry) AND (within 60 hours of study entry))"}
{"candidate_id": "LLM01432", "doc_id": "NCT03480607_inc", "case_bucket": "other", "source_criterion": "American society of anesthesiologist (ASA) physical status I or II", "candidate_expression": "((ASA) AND (American society of anesthesiologist physical status I or II))"}
{"candidate_id": "LLM01433", "doc_id": "NCT00397215_inc", "case_bucket": "or", "source_criterion": "Subjects who the investigator believes that they can and will comply with the requirements of the protocol should be enrolled in the study. A male or female aged 61 years or above at the time of the first vaccination. Written informed consent obtained from the subject. Healthy subjects or subjects with well controlled underlying disease.", "candidate_expression": "((Healthy) AND (Written informed consent) AND (aged 61 years or above) AND (can and will comply with the requirements of the protocol) AND (female) AND (male) AND (underlying disease well controlled))"}
{"candidate_id": "LLM01434", "doc_id": "NCT02883400_inc", "case_bucket": "other", "source_criterion": "liver transplant", "candidate_expression": "(liver transplant)"}
{"candidate_id": "LLM01435", "doc_id": "NCT03120728_exc", "case_bucket": "or", "source_criterion": "Currently pregnant or breastfeeding Severe pelvic organ prolapse or prolapse to any degree that may prevent retention of the vaginal ring after insertion Use of oral contraceptive pills, patches, implants or hormonal intrauterine contraception in the month prior to screening Use of depo medroxyprogesterone within 6 months of screening Use of medications that interact with contraceptive steroid hormones: anti-epileptic medications, rifampin, rifabutin, fosamprenavir, etc Medical condition with safety deemed to be category 3 or 4 when using a combined hormonal contraceptive, as determined by the Center for Disease Control Medical Eligibility Criteria: current or past history of breast cancer, severe decompensated cirrhosis, history of deep vein thrombosis or pulmonary embolus, diabetes with nephropathy/retinopathy/neuropathy or other vascular disease diagnosed more than 20 years ago, current symptomatic gallbladder disease, hypertension, ischemic heart disease, known thrombogenic mutations, hepatocellular adenoma, malignant hepatoma, multiple risk factors for atherosclerotic cardiovascular disease, multiple sclerosis with prolonged immobility, history of peripartum cardiomyopathy, cigarette smoking and =35yo, history of complicated solid organ transplant, history of stroke, history of superficial venous thrombosis not associated with catheter, systemic lupus erythematosus with positive antiphospholipid antibodies, valvular heart disease complicated by pulmonary hypertension or atrial fibrillation or bacterial endocarditis, and acute viral hepatitis", "candidate_expression": "((3 or 4) AND (=35yo) AND (Center for Disease Control Medical Eligibility Criteria) AND (Currently) AND (Medical condition) AND (Severe) AND (acute viral hepatitis) AND (anti-epileptic medications) AND (antiphospholipid antibodies) AND (atherosclerotic cardiovascular disease) AND (atrial fibrillation) AND (bacterial endocarditis) AND (breast cancer) AND (breastfeeding) AND (catheter) AND (cigarette smoking) AND (cirrhosis) AND (combined hormonal contraceptive) AND (complicated solid organ transplant) AND (contraceptive steroid hormones) AND (current) AND (decompensated) AND (deep vein thrombosis) AND (depo medroxyprogesterone) AND (diabetes) AND (fosamprenavir) AND (gallbladder disease) AND (hepatocellular adenoma) AND (history) AND (hormonal intrauterine contraception) AND (hypertension) AND (implants) AND (in the month prior to screening) AND (interact with) AND (ischemic heart disease) AND (malignant hepatoma) AND (may prevent retention of the vaginal ring after insertion) AND (medications) AND (more than 20 years ago) AND (multiple) AND (multiple sclerosis) AND (nephropathy) AND (neuropathy) AND (not associated) AND (oral contraceptive pills) AND (other) AND (past) AND (patches) AND (pelvic organ prolapse) AND (peripartum cardiomyopathy) AND (positive) AND (pregnant) AND (prolapse) AND (prolonged immobility) AND (pulmonary embolus) AND (pulmonary hypertension) AND (retinopathy) AND (rifabutin) AND (rifampin) AND (risk factors) AND (safety category) AND (screening) AND (severe) AND (stroke) AND (superficial venous thrombosis) AND (symptomatic) AND (systemic lupus erythematosus) AND (thrombogenic mutations) AND (valvular heart disease) AND (vascular disease) AND (within 6 months of screening) AND (yo))"}
{"candidate_id": "LLM01436", "doc_id": "NCT02299063_inc", "case_bucket": "other", "source_criterion": "aged between 3 - 36 months having primary corrective heart surgery", "candidate_expression": "((aged between 3 - 36 months) AND (corrective heart surgery primary))"}
{"candidate_id": "LLM01437", "doc_id": "NCT03045562_inc", "case_bucket": "other", "source_criterion": "Informed consent must be obtained prior to any study procedure. Age>18 years. Subjects of STEMI who underwent primary PCI within the first 12 hours.", "candidate_expression": "((>18 years.) AND (Age) AND (Informed consent must be obtained prior to any study procedure) AND (STEMI) AND (primary PCI) AND (within the first 12 hours.))"}
{"candidate_id": "LLM01438", "doc_id": "NCT03380429_inc", "case_bucket": "or", "source_criterion": "Subjects aged 18 years or older, at the time of signing the informed consent. Subjects with documented physician diagnosis of asthma as their primary respiratory disease. ACT score <20 at screening visit. Non-smokers (never smoked or not smoking for >6 months with <10 pack years history (Pack years = [cigarettes per day smoked/20] multiplied by number of years smoked). Male or female subjects will be included. A female subject is eligible to participate if she is not pregnant, not breastfeeding, and at least one of the following conditions applies: (i) Not a woman of childbearing potential (WOCBP). (ii) A WOCBP who agrees to follow the contraceptive guidance during the treatment period and for at least 5 days] after the last dose of study treatment. Capable of giving signed informed consent which includes compliance with the requirements and restrictions listed in the consent form and protocol. Subject understands and is willing, able, and likely to comply with study procedures and restrictions. Subject must be able to read in a language supported by the smart phone app in their region. Subject must have been on maintenance therapy (Fixed dose combination ICS/LABA) for 3 months, cannot have changed dose in the month prior to screening and be able to change to an equivalent dose of RELVAR/BREO for the duration of the study. Other background asthma medication such as anti-leukotrienes and oral corticosteroids are permitted provided the dose has been stable for 1 month prior to screening. Subject must be able to change to Salbutamol/Albuterol MDI rescue for the duration of the study and judged capable of withholding albuterol/salbutamol for at least 6 hours prior to study visits. Subject must have their own Android or iPhone operating system (IOS) smart phone and a data package suitable for the installation and running of the app and sending and receiving data. Data used by the CIS is approximately 1 megabyte (MB) per month as a maximum; this is less data than a 1 minute video streamed from YouTube (2MB). Subjects must be willing and able to download the app on their personal smart phone and keep it turned on for the duration of the study. This will also require Bluetooth to be turned on for duration of the study. Subjects will also have to turn on mobile data for the app for the duration of study; unless travelling and when extra data roaming costs could be incurred. ACT score <20 at randomization visit (visit 2).", "candidate_expression": "((A female subject is eligible to participate if she is not pregnant, not breastfeeding, and at least one of the following conditions applies: (i) Not a woman of childbearing potential (WOCBP). (ii) A WOCBP who agrees to follow the contraceptive guidance during the treatment period and for at least 5 days] after the last dose of study treatment.) AND (ACT score <20 at randomization visit) AND (ACT score <20 at screening visit) AND (Albuterol) AND (Capable of giving signed informed consent which includes compliance with the requirements and restrictions listed in the consent form and protocol.) AND (MDI rescue the duration of the study) AND (Male) AND (Non-smokers) AND (Salbutamol) AND (aged 18 years or older at the time of signing the informed consent) AND (albuterol) AND (asthma primary respiratory disease) AND (capable of withholding for at least 6 hours prior to study visits) AND (change able to for the duration of the study) AND (combination ICS/LABA Fixed dose) AND (female) AND (maintenance therapy for 3 months changed dose) AND (never smoked) AND (not smoking for >6 months) AND (pack years <10) AND (salbutamol))"}
{"candidate_id": "LLM01439", "doc_id": "NCT02528136_exc", "case_bucket": "or", "source_criterion": "Patients with placenta pathology such as praevia, acreta, pre-eclampsia Patients with bleeding disorders including vonWillebrand disease type I. Known intolerance to one of the two drugs. Patients with prolonged QT-time or other serious cardiac diseases. Liver or kidney failure. Epilepsy. Any medical reason why, in the opinion of the investigator, the patient should not participate", "candidate_expression": "((Any medical reason why, in the opinion of the investigator, the patient should not participate) AND (Epilepsy) AND (bleeding disorders) AND (drugs) AND (intolerance) AND (one of the two) AND (other) AND (placenta pathology) AND (vonWillebrand disease type I) AND ((prolonged QT-time) OR (serious cardiac diseases)) AND ((Liver failure) OR (kidney failure)) AND ((acreta) OR (praevia) OR (pre-eclampsia)))"}
{"candidate_id": "LLM01440", "doc_id": "NCT02337764_inc", "case_bucket": "other", "source_criterion": "The participant has a diagnosis of Parkinson's disease according to the diagnostic criteria of the UK Parkinson's Disease Society Brain Bank. The participant has received a levodopa combination drug for >= 1 month and has either of the following. Wearing off phenomenon Decreased response to levodopa combination drugs The participant has received a levodopa combination drug without change in the dose regimen. The participant is an outpatient of either sex aged >= 30 and < 80 years.", "candidate_expression": "((Decreased response) AND (Parkinson's disease) AND (UK Parkinson's Disease Society Brain Bank) AND (Wearing off phenomenon) AND (aged >= 30 and < 80 years) AND (evodopa combination drugs) AND (levodopa combination >= 1 month) AND (levodopa combination drug without change in the dose regimen))"}
{"candidate_id": "LLM01441", "doc_id": "NCT02419378_inc", "case_bucket": "or", "source_criterion": "Signed informed consent form (ICF) Age 18 to 55 years old (inclusive) as of the date the ICF is signed Diagnosis of MS according to the McDonald criteria 2010 and cranial MRI scan demonstrating white matter lesions attributable to MS within 10 years before Screening Onset of MS symptoms (as determined by a neurologist, either at present or retrospectively) within 10 years of the date the ICF is signed EDSS score 0.0 to 5.0 (inclusive) at Screening Patients with (highly) active RRMS disease course indicated to receive alemtuzumab according to the following conditions (at least 1 out of 3 conditions has to be fulfilled): 1. =2 MS relapses within 24 months, 2. clinical (=1 relapse) or MRI (new gadolinium enhancing lesions) disease activity under therapy with other diseasemodifying therapies, 3. severe relapse with high disease activity (=9 T2 hyperintense Lesions and =1 gadolinium enhancing lesion) on MRI. Completion of all vaccinations required by the applicable immunization guidelines published by \"ständige Impfkommission\" (STIKO) History of chickenpox or positive test for antibodies against varicella zoster virus (VZV)", "candidate_expression": "((Age 18 to 55 years old () AND (EDSS score 0.0 to 5.0) AND (Lesions =9 T2 hyperintense) AND (MRI) AND (MS relapses =2 within 24 months,) AND (MS symptoms within 10 years) AND (MS within 10 years before Screening) AND (McDonald criteria 2010) AND (RRMS active) AND (Signed informed consent form (ICF)) AND (alemtuzumab) AND (chickenpox) AND (cranial MRI scan) AND (lesion =1 gadolinium enhancing) AND (lesions new gadolinium enhancing) AND (relapse =1) AND (relapse severe) AND (test for antibodies positive varicella zoster virus VZV))"}
{"candidate_id": "LLM01442", "doc_id": "NCT03129555_exc", "case_bucket": "or", "source_criterion": "A prescription of a NOAC within 90 days prior to hospitalization or outpatient clinic visit for VTE. Patients with NOAC preference apart from preference consistent with current cluster randomized NOAC. Other contraindications mentioned in the \"Summary of Product Characteristics\" for the respective NOAC.", "candidate_expression": "((NOAC) AND (NOAC preference) AND (NOAC within 90 days prior to hospitalization or outpatient clinic visit for VTE) AND (VTE) AND (contraindications Other Summary of Product Characteristics) AND (hospitalization) AND (outpatient clinic) AND (outpatient clinic visit))"}
{"candidate_id": "LLM01443", "doc_id": "NCT03018171_inc", "case_bucket": "other", "source_criterion": "Written maternal informed consent Singleton pregnancy Gestational age = 37 weeks, ASA I BMI < 30 fetus in cephalic presentation", "candidate_expression": "((< 30) AND (= 37 weeks) AND (ASA) AND (BMI) AND (Gestational age) AND (I) AND (Singleton pregnancy) AND (Written maternal informed consent) AND (cephalic presentatio))"}
{"candidate_id": "LLM01444", "doc_id": "NCT01735955_inc", "case_bucket": "other", "source_criterion": "Patient is currently enrolled in a Novartis-sponsored, Oncology Clinical Development & Medical Affairs study receiving nilotinib and has fulfilled all their requirements in the parent study Patient is currently benefiting from the treatment with nilotinib, as determined by the investigator Patient has demonstrated compliance, as assessed by the investigator, with the parent study protocol requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures Written informed consent obtained prior to enrolling in roll-over study", "candidate_expression": "((Novartis-sponsored) AND (Willingness to comply with scheduled visits) AND (Willingness to comply with treatment plans) AND (Written informed consent) AND (ability to comply with scheduled visits) AND (compliance with the parent study protocol requirements) AND (currently) AND (enrolled in a Oncology Clinical Development & Medical Affairs study) AND (enrolling in roll-over study) AND (nilotinib) AND (prior to enrolling in roll-over study) AND (treatment))"}
{"candidate_id": "LLM01445", "doc_id": "NCT02821819_exc", "case_bucket": "other", "source_criterion": "PCOS patients Allergy to gonadotrophins Concomitant participation in other trial", "candidate_expression": "((Allergy) AND (Concomitant participation in other trial) AND (PCOS) AND (gonadotrophins))"}
{"candidate_id": "LLM01446", "doc_id": "NCT03029078_exc", "case_bucket": "or", "source_criterion": "Pregnant woman or breastfeeding immunosuppression including AIDS, corticosteroids over 60mg/day ongoing antibiotic treatment at the day of inclusion impossibility to obtain a signed consent form.", "candidate_expression": "((antibiotic) AND (immunosuppression) AND (impossibility to obtain signed consent form) AND (treatment at the day of inclusion) AND (woman) AND ((Pregnant) OR (breastfeeding)) AND ((AIDS) OR (corticosteroids over 60mg/day)))"}
{"candidate_id": "LLM01447", "doc_id": "NCT02686021_inc", "case_bucket": "scope", "source_criterion": "planned sequential both-sided lower third molar extraction (split-mouth) with osteotomy (with or without upper molar extraction in local anesthesia) able to understand the study and the NRS scale", "candidate_expression": "((able to understand the study) AND (local anesthesia) AND (lower third molar extraction planned sequential both-sided split-mouth) AND (osteotomy) AND (upper molar extraction))"}
{"candidate_id": "LLM01448", "doc_id": "NCT02798237_inc", "case_bucket": "or", "source_criterion": "= 20years of age; diagnosis of stroke (>6months); sedentary or insufficiently active; have a writing medical permission to participate in the training program.", "candidate_expression": "((age = 20years) AND (stroke >6months) AND ((insufficiently active) OR (sedentary)))"}
{"candidate_id": "LLM01449", "doc_id": "NCT02624908_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes Known peripheral artery disease Liver enzymes equal or more than 1.5 times the upper limit of normal Chronic heart failure NYHA class III or IV Current haemodialysis or peritoneal dialysis End stage liver disease, defined as acute or chronic liver disease and recent history of one of the following: ascites, encephalopathy, variceal bleeding, bilirubin equal or greater than 2.0 mg/dL, albumin equal or less than 3.5 g/ dL, prothrombin time greater or equal to 4 seconds, INR greater than or equal to 1.7 or prior liver transplant Known or suspected hypersensitivity to trial products or related products Female of child-bearing potential who is pregnant, breast-feeding or intends to become pregnant or is not using adequate contraceptive methods as required by law or local practice. Expected simultaneous participation in any other clinical trial of an investigational medicinal product. Receipt of any investigational medicinal product within 30 days before randomization Current or past (within the last 5 years) malignant neoplasms (except basal cell and squamous cell skin carcinoma) Any condition that in the investigator's opinion would make the subject unable to adhere to the trial visit schedule and procedures Known history of non-compliance to treatment.", "candidate_expression": "((Any condition that in the investigator's opinion would make the subject unable to adhere to the trial visit schedule and procedures) AND (Chronic heart failure) AND (Current) AND (End stage liver disease) AND (Female of child-bearing potential who is pregnant, breast-feeding or intends to become pregnant or is not using adequate contraceptive methods as required by law or local practice.) AND (INR) AND (Known) AND (Liver enzymes) AND (NYHA) AND (Type 1 diabetes) AND (acute liver disease) AND (albumin) AND (ascites) AND (basal cell carcinoma) AND (bilirubin) AND (chronic liver disease) AND (class III or IV) AND (encephalopathy) AND (equal or greater than 2.0 mg/dL) AND (equal or less than 3.5 g/ dL) AND (equal or more than 1.5 times the upper limit of normal) AND (except) AND (greater or equal to 4 seconds) AND (greater than or equal to 1.7) AND (haemodialysis) AND (hypersensitivity) AND (liver transplant) AND (malignant neoplasms) AND (past) AND (peripheral artery disease) AND (peritoneal dialysis) AND (prior) AND (prothrombin time) AND (recent) AND (related products) AND (squamous cell skin carcinoma) AND (suspected) AND (trial products) AND (variceal bleeding) AND (within the last 5 years))"}
{"candidate_id": "LLM01450", "doc_id": "NCT02958072_inc", "case_bucket": "or", "source_criterion": "Diabetes mellitus Foot ulcer at the malleoli area between 0,25 cm² and 5,0 cm² Foot ulcer duration more than 6 weeks Ankle-brachial index above 0,40 or presence of palpable pulses in arteria dorsalis pedes and/or arteria tibialis posterior informed consent", "candidate_expression": "((Diabetes mellitus) AND (Foot ulcer malleoli area between 0,25 cm² and 5,0 cm²) AND (Foot ulcer more than 6 weeks) AND (informed consent) AND ((arteria dorsalis pedes) OR (arteria tibialis posterior)) AND ((Ankle-brachial index above 0,40) OR (palpable pulses)))"}
```
