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
{"candidate_id": "LLM00601", "doc_id": "NCT03043495_exc", "case_bucket": "or", "source_criterion": "Coagulopathies (with prothrombin concentration less than 60% or INR more than 1.5) In-ability to postpone anti-coagulation medications. Infection or injury or a lesion at the block site. Suspected cervical vertebral column injury necessitating using a neck collar. A compromised lung on the contralateral side of the block (Pneumothorax, hemothorax or Pneumonectomy). Traumatic vascular injuries or operative interventions (Surgical harvesting) involving arteries of the upper limb on the operative side. Patients with communication difficulties. Hypersensitivity to local anesthetics and/or Dexamethasone. Patients on perioperative intravenous (IV) steroids.", "candidate_expression": "((Coagulopathies) AND (Dexamethasone) AND (Hypersensitivity) AND (INR more than 1.5) AND (Infection) AND (Pneumonectomy) AND (Pneumothorax) AND (Surgical harvesting) AND (Traumatic vascular injuries) AND (anti-coagulation medications In-ability to postpone) AND (cervical vertebral column injury Suspected) AND (communication difficulties) AND (compromised lung contralateral side of the block) AND (hemothorax) AND (injury) AND (intravenous (IV) steroids perioperative) AND (lesion) AND (local anesthetics) AND (operative interventions) AND (prothrombin concentration less than 60%))"}
{"candidate_id": "LLM00602", "doc_id": "NCT01642875_inc", "case_bucket": "or", "source_criterion": "Primary periampullary tumor R0, R1 resection Chronic pancreatitis requiring pancreatoduodenectomy", "candidate_expression": "((Chronic pancreatitis) AND (Primary) AND (R0 resection) AND (R1 resection) AND (pancreatoduodenectomy) AND (periampullary tumor) AND (requiring))"}
{"candidate_id": "LLM00603", "doc_id": "NCT02959580_inc", "case_bucket": "other", "source_criterion": "Idiopathic Granulomatous Mastitis", "candidate_expression": "(Idiopathic Granulomatous Mastitis)"}
{"candidate_id": "LLM00604", "doc_id": "NCT02964715_inc", "case_bucket": "or", "source_criterion": "biopsy proven NASH Type 2 DM HbA1c :>6.5% BMI < 45kg/m2 Any anti-diabetic agent except SGLT2 inhibitors, TZDs(thiazolidinediones), DPP4(Dipeptidyl peptidase4) inhibitors and GLP1 RAs(Glucagon-like Peptide 1-Receptor Agonists)", "candidate_expression": "((< 45kg/m2) AND (>6.5%) AND (BMI) AND (Dipeptidyl peptidase4 inhibitors) AND (Glucagon-like Peptide 1-Receptor Agonists) AND (HbA1c) AND (NASH) AND (Type 2 DM) AND (anti-diabetic agent) AND (biopsy) AND (except) AND (thiazolidinediones) AND ((DPP4 inhibitors) OR (GLP1 RAs) OR (SGLT2 inhibitors) OR (TZDs)))"}
{"candidate_id": "LLM00605", "doc_id": "NCT03500211_inc", "case_bucket": "or", "source_criterion": "Pregnant patients who require a scheduled or non-urgent cesarean birth Patient able to receive neuraxial analgesia Patient able to give verbal and written consent for both cesarean birth and study", "candidate_expression": "((Patient able to give verbal and written consent for both cesarean birth and study) AND (Pregnant scheduled) AND (cesarean birth non-urgent) AND (neuraxial analgesia able to receive))"}
{"candidate_id": "LLM00606", "doc_id": "NCT02831166_exc", "case_bucket": "or", "source_criterion": "Less than 18 years of age; Pregnancy; Chronic use of vitamin K antagonists or direct thrombin inhibitors, or oral Xa-factor antagonists; Hypersensitivity to antiplatelet and/or anticoagulant drugs; Active bleeding or high bleeding risk (severe liver failure, active peptic ulcer, creatinine clearance < 30 mL/min, platelets count < 100.000 mm3); Uncontrolled systemic hypertension; Cardiogenic shock; Previous myocardial revascularization surgery with = 1 internal mammary or radial artery graft; Documented chronic peripheral arterial disease preventing the use of the femoral technique; Severe concomitant disease with life expectancy below 12 months; Participation in drug or devices investigative clinical trials in the last 30 days; Medical, geographic or social conditions impairing the participation in the study or inability to understand and sign the informed consent term.", "candidate_expression": "((< 100.000 mm3) AND (< 30 mL/min) AND (= 1) AND (Active) AND (Cardiogenic shock) AND (Chronic) AND (Hypersensitivity) AND (Less than 18 years) AND (Medical, geographic or social conditions impairing the participation in the study or inability to understand and sign the informed consent term.) AND (Pregnancy) AND (Previous) AND (Severe) AND (Uncontrolled) AND (active) AND (age) AND (anticoagulant drugs) AND (antiplatelet drugs) AND (below 12 months) AND (bleeding) AND (chronic) AND (concomitant) AND (creatinine clearance) AND (direct thrombin inhibitors) AND (disease) AND (femoral technique) AND (high bleeding risk) AND (internal mammary graft) AND (life expectancy) AND (liver failure) AND (myocardial revascularization surgery) AND (oral Xa-factor antagonists) AND (peptic ulcer) AND (peripheral arterial disease) AND (platelets count) AND (preventing) AND (radial artery graft) AND (severe) AND (systemic hypertension) AND (vitamin K antagonists))"}
{"candidate_id": "LLM00607", "doc_id": "NCT02721017_inc", "case_bucket": "other", "source_criterion": "scheduled for Nuss procedure for pectus excavatum correction at least 13 years old at the time of the procedure", "candidate_expression": "((Nuss procedure) AND (at least 13 years) AND (at the time of the procedure) AND (old) AND (pectus excavatum) AND (scheduled))"}
{"candidate_id": "LLM00608", "doc_id": "NCT02845427_inc", "case_bucket": "other", "source_criterion": "Primary total hip arthroplasty (THA)", "candidate_expression": "((THA) AND (total hip arthroplasty Primary))"}
{"candidate_id": "LLM00609", "doc_id": "NCT02893228_inc", "case_bucket": "or", "source_criterion": "Patients undergoing surgery on shoulder, humerus, or clavicle", "candidate_expression": "((surgery) AND ((clavicle) OR (humerus) OR (shoulder)))"}
{"candidate_id": "LLM00610", "doc_id": "NCT02781610_exc", "case_bucket": "or", "source_criterion": "Previous randomization in this study Treatment with IV antibiotics in the 6 weeks prior to Visit 1 Admission to the intensive care unit for current pulmonary exacerbation in the two weeks prior to Visit 2, unless admission was due to a desensitization protocol Pneumothorax in the two weeks prior to Visit 2 Primary diagnosis for current hospitalization is unrelated to worsening lower respiratory symptoms (e.g., pulmonary clean out, distal intestinal obstruction syndrome (DIOS), sinusitis) Massive hemoptysis defined as > 250 cc in a 24 hour period or 100 cc/day over 4 consecutive days occurring in the two weeks prior to Visit 2 Current pulmonary exacerbation thought to be due to allergic bronchopulmonary aspergillosis (ABPA) At Visit 1, receiving ongoing treatment with a duration of more than 2 weeks with prednisone equivalent to >10mg/day History of solid organ transplantation Receiving antimicrobial therapy to treat non-tuberculous mycobacterium (e.g., M. abscessus, M. avium complex) in the two weeks prior to Visit 2", "candidate_expression": "((ABPA) AND (Admission to the intensive care unit) AND (DIOS) AND (IV antibiotics in the 6 weeks prior to Visit 1) AND (Pneumothorax in the two weeks prior to Visit 2) AND (Primary diagnosis current hospitalization) AND (allergic bronchopulmonary aspergillosis) AND (antimicrobial therapy non-tuberculous mycobacterium in the two weeks prior to Visit 2 M. abscessus M. avium complex) AND (distal intestinal obstruction syndrome) AND (hemoptysis Massive in the two weeks prior to Visit 2 > 250 cc in a 24 hour period 100 cc/day over 4 consecutive days) AND (intensive care unit) AND (lower respiratory symptoms worsening) AND (prednisone At Visit 1 more than 2 weeks >10mg/day) AND (pulmonary clean out) AND (pulmonary exacerbation) AND (pulmonary exacerbation in the two weeks prior to Visit 2) AND (sinusitis) AND (solid organ transplantation) AND (unrelated) AND NOT (desensitization protocol))"}
{"candidate_id": "LLM00611", "doc_id": "NCT01959425_inc", "case_bucket": "or", "source_criterion": "Successful cardiac ablation for AF Documented freedom from AF recurrence (symptomatic or asymptomatic arrhythmic recurrences lasting longer than 30 seconds) 3 months after successful cardiac ablation (AF recurrence during 3-month blanking period is excluded). Patient must have been on a commercially approved anticoagulation therapy for at least two (2) months prior to randomization in the OAT Study. CHADS2 score = 2 or CHA2DS2-VASc score (=3) Left ventricular ejection fraction > 25% LA size < 65 High risk for thromboembolic events (i.e., CHADS2 score = 2 or CHA2DS2-VASc score = 3) and require OAT before undergoing cardiac ablation Able and willing to comply with all pre- and follow-up testing and requirements Signed informed consent form Age 18 years or older", "candidate_expression": "((AF) AND (Age 18 years or older) AND (CHA2DS2-VASc score = 3) AND (CHA2DS2-VASc score =3) AND (CHADS2 score = 2) AND (LA size < 65) AND (Left ventricular ejection fraction > 25%) AND (OAT before undergoing cardiac ablation) AND (Signed informed consent form) AND (anticoagulation therapy at least two (2) months prior to randomization) AND (arrhythmic recurrences longer than 30 seconds) AND (ble and willing to comply with all pre- and follow-up testing and requirements) AND (cardiac ablation Successful) AND (risk for thromboembolic events High) AND NOT (AF recurrence 3 months after successful cardiac ablation))"}
{"candidate_id": "LLM00612", "doc_id": "NCT02868437_exc", "case_bucket": "or", "source_criterion": "History of curettage or other intrauterine surgery History of post-abortion complication or infection", "candidate_expression": "((curettage) AND (intrauterine surgery) AND (post-abortion complication) AND (post-abortion infection))"}
{"candidate_id": "LLM00613", "doc_id": "NCT00970866_exc", "case_bucket": "or", "source_criterion": "Known asthmatic or history of allergy towards peanut or milk products Concurrent participation in another clinical trial Severe illness warranting hospital referral", "candidate_expression": "((Severe) AND (history) AND (hospital referral) AND (illness) AND (participation in another clinical trial) AND (warranting) AND ((allergy) OR (asthmatic)) AND ((milk products) OR (peanut)))"}
{"candidate_id": "LLM00614", "doc_id": "NCT02833623_inc", "case_bucket": "or", "source_criterion": "outpatients aged 18-70 years confirmed diagnosis of H. pylori infection by at least one of the following methods: 13C-urea breath test, histology, rapid urease test or bacterial culture an intention of H. pylori eradication treatment and have written inform consent ability to read short messages on the mobile phone", "candidate_expression": "((18-70 years) AND (H. pylori infection) AND (ability to read short messages on the mobile phone) AND (aged) AND (an intention of H. pylori eradication treatment and have written inform consent) AND (outpatients) AND ((13C-urea breath test) OR (bacterial culture) OR (histology) OR (rapid urease test)))"}
{"candidate_id": "LLM00615", "doc_id": "NCT02186782_inc", "case_bucket": "or", "source_criterion": "Infertile women with eugonadotrophic anovulation/oligoovulation. Unexplained infertility.", "candidate_expression": "((Infertile) AND (Unexplained) AND (anovulation) AND (eugonadotrophic) AND (infertility) AND (oligoovulation) AND (women))"}
{"candidate_id": "LLM00616", "doc_id": "NCT01757717_exc", "case_bucket": "or", "source_criterion": "Patients who may receive therapeutically effective doses via an external beam approach to the lesion of interest as specified by MSKCC Radiation Oncology Department dose constraint criteria. Patients with kyphoplasty cement or hardware that would preclude effective catheter placement. Patients with paraspinal extension of disease with visceral involvement. Abnormal complete blood count. Any of the following: Platelet count < 75,000/ml Hb level < 9gm/dl WBC < 3.5/ml Abnormal coagulation profile: INR > 2.5 and/or PTT > 80 Patients who are on anticoagulation medication that may not be safely held for the procedure (≥ 5 days for antiplatelet agents and warfarin; ≥ 24 hours for low-molecular weight heparin formulations) will be excluded. Contraindications to general anesthesia", "candidate_expression": "((< 3.5/ml) AND (< 75,000/ml) AND (< 9gm/dl) AND (> 2.5) AND (> 80) AND (Abnormal) AND (Abnormal coagulation profile) AND (Abnormal complete blood count) AND (Contraindications to general anesthesia) AND (Hb level) AND (INR) AND (MSKCC Radiation Oncology Department dose constraint criteria) AND (PTT) AND (Platelet count) AND (WBC) AND (anticoagulation medication) AND (antiplatelet agents) AND (coagulation profile) AND (complete blood count) AND (doses) AND (external beam) AND (general anesthesia) AND (kyphoplasty cement) AND (kyphoplasty hardware) AND (low-molecular weight heparin) AND (may not be safely held for the procedure) AND (may receive therapeutically effective doses via an external beam approach to the lesion of interest) AND (paraspinal extension of disease) AND (preclude effective catheter placement) AND (therapeutically effective) AND (visceral involvement) AND (warfarin) AND (≥ 24 hours) AND (≥ 5 days))"}
{"candidate_id": "LLM00617", "doc_id": "NCT02687178_inc", "case_bucket": "or", "source_criterion": "Caucasian patients affected by uncomplicated, essential hypertension, not well controlled by concomitant administration of ACE-I or ARBs and diuretics at the maximum dosage.", "candidate_expression": "((ACE-I) AND (ARBs) AND (Caucasian) AND (diuretics) AND (essential hypertension) AND (maximum dosage) AND (not well controlled) AND (uncomplicated))"}
{"candidate_id": "LLM00618", "doc_id": "NCT02744976_inc", "case_bucket": "other", "source_criterion": "age =18 and <75 years; patients with stable coronary artery disease referred to PCI in an artery suitable for IVUS pullback; signed informed consent before PCI.", "candidate_expression": "((PCI referred to artery suitable for IVUS pullback) AND (age =18 and <75 years) AND (coronary artery disease stable) AND (signed informed consent before PCI))"}
{"candidate_id": "LLM00619", "doc_id": "NCT02851888_inc", "case_bucket": "scope", "source_criterion": "Scheduled for arthroscopic labral repair with or without osteoplasty of the hip. 18 to 50 years old American Society of Anesthesiologists Physical Status (ASA PS) score of I or II.", "candidate_expression": "((ASA PS) AND (American Society of Anesthesiologists Physical Status score I or II) AND (arthroscopic labral repair Scheduled) AND (old 18 to 50 years) AND (osteoplasty hip))"}
{"candidate_id": "LLM00620", "doc_id": "NCT02225548_inc", "case_bucket": "other", "source_criterion": "Diagnosis of idiopathic Parkinson's disease that is optimally treated (motor fluctuations <20% of subject's awake time). Subjects may be on levodopa therapy but must be stable at the time of entry into the study Sexually active (i.e. =1 attempt/week) males, 40 - 64 years of age (inclusive) at time of screening Diagnosis of moderate erectile dysfunction (defined according to the NIH Consensus Development Panel on Impotence) for more than 6 months and demonstrating and incomplete response to tadalafil alone Subject demonstrating an IIEF-5 drug-free baseline score that is = 10 but = 16, and an IIEF-5 tadalafil-alone baseline score that is = 18 Subject in a stable heterosexual relationship for at least 6 months. (2) Subject motivated to seek treatment for erectile dysfunction. Subject with a total serum testosterone level = 300 ng/dL, with or without supplementation Hoehn and Yahr Scale score of 1 - 3 Patient able to consent and comply with protocol requirements", "candidate_expression": "((1 - 3) AND (40 - 64 years) AND (<20% of subject's awake time) AND (= 10 but = 16) AND (= 18) AND (= 300 ng/dL) AND (=1 attempt/week) AND (Hoehn and Yahr Scale score) AND (IIEF-5 drug-free baseline score) AND (IIEF-5 tadalafil-alone baseline score) AND (Patient able to consent and comply with protocol requirements) AND (Sexually active) AND (Subject motivated to seek treatment for erectile dysfunction) AND (age) AND (at least 6 months) AND (erectile dysfunction) AND (for more than 6 months) AND (heterosexual relationship) AND (idiopathic Parkinson's disease) AND (incomplete) AND (males) AND (moderate) AND (motor fluctuations) AND (response) AND (stable) AND (tadalafil) AND (total serum testosterone level) AND (treated) AND (treatment))"}
{"candidate_id": "LLM00621", "doc_id": "NCT00785213_inc", "case_bucket": "or", "source_criterion": "Healthy adults 18-45 years of age Non-smoking Non-pregnant (post-menopausal, surgically sterile or using effective contraceptive measures) Body mass index (BMI) less than or equal to 32 Medically healthy on the basis of medical history and physical examination Hemoglobin > or = to 11.5g/dL Completion of the screening process within 28 days prior to dosing Provision of voluntary written informed consent", "candidate_expression": "((Body mass index (BMI) less than or equal to 32) AND (Healthy) AND (Hemoglobin > or = to 11.5g/dL) AND (Medically healthy) AND (Provision of voluntary written informed consent) AND (adults) AND (contraceptive measures effective) AND (medical history) AND (of age 18-45 years of age) AND (physical examination) AND (post-menopausal) AND (screening process within 28 days prior to dosing) AND (surgically) AND (surgically sterile) AND NOT (smoking) AND NOT (pregnant))"}
{"candidate_id": "LLM00622", "doc_id": "NCT02498483_exc", "case_bucket": "other", "source_criterion": "Newborns of substance abusing mothers. Newborns with any contraindications to routine circumcision, anatomical or hematologic.", "candidate_expression": "((Newborns) AND (circumcision) AND (contraindications) AND (mothers) AND (substance abusing))"}
{"candidate_id": "LLM00623", "doc_id": "NCT02982577_exc", "case_bucket": "other", "source_criterion": "Sensitivity to pilocarpine Secondary Sjögren's syndrome; Type II diabetes mellitus; AIDS; pregnant or lactating women; Glaucoma; Uncontrolled asthma; Chronic obstructive pulmonary disease; Renal diseases; Severe cardiovascular diseases; Gastrointestinal disorders; Hepatic insufficiency.", "candidate_expression": "((AIDS) AND (Chronic obstructive pulmonary disease) AND (Gastrointestinal disorders) AND (Glaucoma) AND (Hepatic insufficiency) AND (Renal diseases) AND (Secondary) AND (Sensitivity) AND (Severe) AND (Sjögren's syndrome) AND (Type II diabetes mellitus) AND (Uncontrolled) AND (asthma) AND (cardiovascular diseases) AND (pilocarpine) AND (pregnant or lactating women))"}
{"candidate_id": "LLM00624", "doc_id": "NCT03305666_inc", "case_bucket": "other", "source_criterion": "Patients undergoing SSRF at Denver Health Medical Center", "candidate_expression": "((Denver Health Medical Center) AND (SSRF))"}
{"candidate_id": "LLM00625", "doc_id": "NCT02731794_inc", "case_bucket": "other", "source_criterion": "patients with severe left ventricle dysfunction with an ejection fraction (EF)=40%, being scheduled for revascularization.", "candidate_expression": "((being scheduled for) AND (ejection fraction (EF) =40%) AND (left ventricle dysfunction severe) AND (revascularization))"}
```
