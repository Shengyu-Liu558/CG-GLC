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
{"candidate_id": "LLM07226", "doc_id": "NCT00846703_inc", "case_bucket": "or", "source_criterion": "Cytologically proven acute lymphoblastic leukemia (ALL) No relapse of a previously unrecognized ALL Patients must meet one of the following risk criteria: Standard-risk (SR) group meeting all of the following criteria: Blasts < 1,000/µL in peripheral blood (PB) on day 8 Aged 1 to < 6 years Initial WBC < 20,000/µL M1 (5%) or M2 (= 5% to < 25%) blasts in bone marrow on day 15; M1 marrow on day 33. Aged < 1 or = 6 years and/or WBC = 20,000/µL Blasts < 1,000/µL in PB on day 8 M1 or M2 marrow on day 15 M3 (= 25%) marrow on day 15 OR meets SR criteria but M3 marrow on day 15 and *M1 marrow on day 33. Meets IR criteria and M3 marrow on day 15 (not SR and M3 on day 15) Blasts = 1,000/µL in PB on day 8 M2 or M3 marrow on day 33 Translocation t(9;22) [BCR/ABL+] (Philadelphia chromosome-positive) or t(4;11) [MLL/AF4+].", "candidate_expression": "(((5%) AND (+) AND (1 to < 6 years) AND (< 1 or = 6 years) AND (< 1,000/µL) AND (< 20,000/µL) AND (= 1,000/µL) AND (= 20,000/µL) AND (= 25%) AND (= 5% to < 25%) AND (ALL) AND (Aged) AND (Blasts) AND (Cytologically proven) AND (IR criteria) AND (Initial) AND (M1 marrow) AND (M3) AND (M3 marrow) AND (Meets) AND (No) AND (PB) AND (Philadelphia chromosome) AND (SR) AND (SR criteria) AND (Standard-risk) AND (Translocation t(9;22)) AND (WBC) AND (acute lymphoblastic leukemia) AND (all) AND (bone marrow) AND (criteria) AND (meets) AND (not) AND (on day 15) AND (on day 33) AND (on day 8) AND (peripheral blood) AND (positive) AND (previously unrecognized) AND (relapse) AND (t(4;11)) AND ((M1 blasts) OR (M2 blasts)) AND ((Aged) OR (WBC)) AND ((M1 marrow) OR (M2 marrow)) AND ((M2 marrow) OR (M3 marrow)) AND ((BCR/ABL) OR (MLL/AF4)))"}
{"candidate_id": "LLM07227", "doc_id": "NCT03126214_exc", "case_bucket": "or", "source_criterion": "Uncontrolled hypertension (defined as average SBP = 160 mmHg [2 readings taken at time of screening]). End stage renal disease (CrCl < 15 ml/min) Valvular Heart Disease including those with prosthetic valve, mitral stenosis (moderate to severe) or valve repair. Excess alcohol intake (males: = 28 units/week, females: = 21 units/week. One unit of alcohol = 8 oz beer, 1 oz hard liquor or 4 oz wine). Intracranial bleed at any point. History of \"Major Bleeding\" at any point (defined as overt bleeding at a critical site including intracranial, intraspinal, intraocular, pericardial, or retroperitoneal; or bleed requiring hospitalization). Foreshortened life-expectancy or severe comorbidities precluding study follow-up period Unable to read/understand English Severe cognitive impairment (defined as score = 5 on the Short Portable Mental Status Questionnaire)", "candidate_expression": "((CrCl < 15 ml/min) AND (End stage renal disease) AND (Intracranial bleed at any point) AND (Major Bleeding History at any point) AND (Short Portable Mental Status Questionnaire = 5) AND (alcohol intake Excess) AND (average SBP = 160 mmHg 2 readings at time of screening) AND (cognitive impairment Severe) AND (hospitalization) AND (hypertension Uncontrolled) AND ((Valvular Heart Disease) OR (mitral stenosis) OR (prosthetic valve) OR (valve repair)) AND ((moderate) OR (severe)) AND ((females = 21 units/week) OR (males = 28 units/week)) AND ((intracranial) OR (intraocular) OR (intraspinal) OR (pericardial) OR (retroperitoneal)) AND ((bleed) OR (overt bleeding critical site)) AND ((life-expectancy Foreshortened) OR (severe comorbidities)))"}
{"candidate_id": "LLM07228", "doc_id": "NCT03208465_exc", "case_bucket": "or", "source_criterion": "Contraindications to empagliflozin, Sitagliptin DPP4 inhibitors or Sodium-glucose cotransporter-2(SGLT2) inhibitors within the previous 4 weeks Insulin requiring diabetes Poor glucose control (HbA1C>10 %) Acute coronary syndrome Stent placement within the previous 6 months Previous coronary artery bypass graft surgery within the previous 6 months Planned revascularization within 6 months Heart failure requiring loop diuretics Severe left ventricular hypertrophy (left ventricular septal wall thickness > 13mm) Significant renal disease manifested by creatinine clearance of < 30 ml/min) Hepatic disease or biliary tract obstruction, or significant hepatic enzyme elevation (alanine transaminase or Aspartate Aminotransferase > 3 times upper limit of normal) Radiopaque material implanted in the chest wall (metal, silicone, etc.) Contraindication to adenosine stress test Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study. Patient's pregnant or breast-feeding or child-bearing potential Expected life expectancy < 1 year Unwillingness or inability to comply with the procedures described in this protocol", "candidate_expression": "((< 1 year) AND (< 30 ml/min) AND (> 13mm) AND (> 3 times upper limit of normal) AND (>10 %) AND (Acute coronary syndrome) AND (Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study.) AND (Aspartate Aminotransferase) AND (Contraindication) AND (Contraindications) AND (DPP4 inhibitors) AND (Expected life expectancy) AND (HbA1C) AND (Heart failure) AND (Hepatic disease) AND (Insulin) AND (Planned) AND (Poor glucose control) AND (Previous) AND (Radiopaque material) AND (Severe) AND (Significant) AND (Sitagliptin) AND (Sodium-glucose cotransporter-2(SGLT2) inhibitors) AND (Stent) AND (adenosine stress test) AND (alanine transaminase) AND (biliary tract obstruction) AND (breast-feeding) AND (chest wall) AND (child-bearing potential) AND (coronary artery bypass graft surgery) AND (creatinine clearance) AND (diabetes) AND (empagliflozin) AND (hepatic enzyme elevation) AND (left ventricular hypertrophy) AND (left ventricular septal wall thickness) AND (loop diuretics) AND (placement) AND (pregnant) AND (renal disease) AND (revascularization) AND (significant) AND (within 6 months) AND (within the previous 4 weeks) AND (within the previous 6 months))"}
{"candidate_id": "LLM07229", "doc_id": "NCT01630954_inc", "case_bucket": "other", "source_criterion": "Ultrasound confirmed complete mole", "candidate_expression": "((Ultrasound) AND (complete mole))"}
{"candidate_id": "LLM07230", "doc_id": "NCT02203019_exc", "case_bucket": "or", "source_criterion": "Patients with documented allergies to propofol, dexmedetomidine, fentanyl, eggs or egg products, or soy or soy products. A heart rate less than 50 beats/minute or grade 2 or 3 AV heart block Mean arterial pressure less than 55 mmHg despite appropriate fluid resuscitation and vasopressor support. Current triglyceride level > 400 mg/dl", "candidate_expression": "((> 400 mg/dl) AND (Mean arterial pressure) AND (allergies) AND (fluid resuscitation) AND (less than 50 beats/minute) AND (less than 55 mmHg) AND (triglyceride level) AND (vasopressor) AND ((AV heart block) OR (heart rate)) AND ((grade 2) OR (grade 3)) AND ((dexmedetomidine) OR (egg products) OR (eggs) OR (fentanyl) OR (propofol) OR (soy) OR (soy products)))"}
{"candidate_id": "LLM07231", "doc_id": "NCT01943409_exc", "case_bucket": "other", "source_criterion": "• Patients without PN during their hospitalization", "candidate_expression": "((PN) AND (during their hospitalization) AND (hospitalization) AND (their hospitalization) AND (without))"}
{"candidate_id": "LLM07232", "doc_id": "NCT03424993_inc", "case_bucket": "other", "source_criterion": "Habitual dietary sodium intake > 3400mg per day", "candidate_expression": "(dietary sodium intake > 3400mg per day)"}
{"candidate_id": "LLM07233", "doc_id": "NCT02365870_exc", "case_bucket": "other", "source_criterion": "Unstable medical disease of comorbid psychiatric disease Dementia Subjects with less than one year duration of Parkinson's Current treatment with a dopamine agonist", "candidate_expression": "((Dementia) AND (Parkinson's less than one year duration) AND (Unstable medical disease) AND (comorbid psychiatric disease) AND (dopamine agonist Current))"}
{"candidate_id": "LLM07234", "doc_id": "NCT02399033_inc", "case_bucket": "or", "source_criterion": "Age: 20-70 years old; Gender: male or female; clinical or pathological diagnosis of hepatocellular carcinoma (HCC) in previously untreated patients; The expected survival> 3 months; Child-Pugh grade in A-level; KPS score with 50-100 points; BCLC stage of 0-B; conform to the indications of hepatectomy; Viable tumor resection confirmed by two highly qualified surgical doctors; No other surgical contraindications. women in the reproductive period must be completely contraception in 28 days before treatment, during the treatment process and in 28 days after treatment; Men must be completely contraception and prohibited donation and sperm donation during the treatment process and in 28 days after treatment; All patients must be prohibited donation during the treatment process and in 28 days after treatment; In addition to the subjects, prohibitting other people taking this product. patients have a good understanding and could coordinate with investigators for the trial. Patients enrolled in the trial should sign an informed consent form, to indicate understanding the purpose and procedure of the trial, and patients volunteering to participate in the trial.", "candidate_expression": "((0-B) AND (20-70 years old) AND (50-100 points) AND (> 3 months) AND (A) AND (Age) AND (BCLC stage) AND (Child-Pugh grade) AND (Gender) AND (HCC) AND (KPS score) AND (Men) AND (No) AND (Patients enrolled in the trial should sign an informed consent form, to indicate understanding the purpose and procedure of the trial, and patients volunteering to participate in the trial) AND (Viable tumor resection confirmed by two highly qualified surgical doctors) AND (clinical or pathological diagnosis) AND (contraception) AND (donation) AND (during the treatment process) AND (expected survival) AND (hepatectomy) AND (hepatocellular carcinoma) AND (in 28 days after treatmen) AND (in 28 days after treatment) AND (in 28 days before treatment) AND (indications of hepatectomy) AND (other surgical contraindications) AND (patients have a good understanding and could coordinate with investigators for the trial) AND (prohibited) AND (reproductive period) AND (sperm donation) AND (treatment) AND (untreated) AND (women) AND ((female) OR (male)))"}
{"candidate_id": "LLM07235", "doc_id": "NCT02901106_exc", "case_bucket": "other", "source_criterion": "pregnant or breastfeeding woman patient with a measure of legal protection subject unaffiliated insurance", "candidate_expression": "((patient with a measure of legal protection) AND (pregnant or breastfeeding woman))"}
{"candidate_id": "LLM07236", "doc_id": "NCT02785549_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07237", "doc_id": "NCT03099408_inc", "case_bucket": "or", "source_criterion": "Women be at least 18 years of age Have symptoms of vaginal odor and or/discharge Meet the clinical (Amsel) criteria for BV Willing to participate in research", "candidate_expression": "((BV) AND (Women) AND (age at least 18 years) AND (participate in research Willing to) AND (vaginal discharge criteria clinical Amsel criteria) AND (vaginal odor))"}
{"candidate_id": "LLM07238", "doc_id": "NCT03134378_exc", "case_bucket": "or", "source_criterion": "Patients refuse to follow the research Patient has had previous eradication therapy of Helicobacter pylori infection. The patient is pregnant or breastfeeding Patients have a history of allergy to one component of triple therapy regimen (proton pump inhibitor, penicillin, and / or macrolide) before. Patients are known to have impaired liver function, evidenced by ALT values within normal limits, and no previous liver disease. Patients were found to have arrhythmias or obtained QT wave elongation on electrocardiographic", "candidate_expression": "((ALT values) AND (Helicobacter pylori infection) AND (QT wave elongation) AND (allergy) AND (component of triple therapy regimen) AND (eradication therapy) AND (history) AND (impaired) AND (liver disease) AND (liver function) AND (no) AND (previous) AND (refuse to follow the research) AND (within normal limits) AND ((macrolide) OR (penicillin) OR (proton pump inhibitor)) AND ((arrhythmias) OR (electrocardiographic)) AND ((breastfeeding) OR (pregnant)))"}
{"candidate_id": "LLM07239", "doc_id": "NCT02478515_exc", "case_bucket": "or", "source_criterion": "Previous treatment with anti-VEGF drugs or corticosteroid or grid laser photocoagulation (study eye) History of vitrectomy surgery, submacular surgery, or other surgical intervention for RVO Ocular disorders in the study eye that may confound interpretation of study results BCVA over 77 letters between screening and Day 0 The pregnant or lactating woman", "candidate_expression": "((BCVA) AND (RVO) AND (The pregnant or lactating woman) AND (anti-VEGF drugs) AND (corticosteroid) AND (grid laser photocoagulation () AND (over 77 letters) AND (submacular surgery) AND (surgical intervention) AND (vitrectomy surgery))"}
{"candidate_id": "LLM07240", "doc_id": "NCT03463564_exc", "case_bucket": "or", "source_criterion": "previous use of insulin pump pregnancy or planning to become pregnant in the next 2 years, lack of ability to use the study devices history of severe chronic diseases recent or concomitant use of corticosteroids drug or alcohol abuse psychiatric complaints that interfere with the correct use of the devices", "candidate_expression": "((chronic diseases history severe) AND (corticosteroids) AND (insulin pump) AND (psychiatric complaints correct use of the devices) AND (study devices) AND NOT (ability to use the study devices) AND ((concomitant) OR (recent)) AND ((alcohol abuse) OR (drug abuse)) AND ((pregnancy) OR (pregnant planning to become)))"}
{"candidate_id": "LLM07241", "doc_id": "NCT00391690_inc", "case_bucket": "or", "source_criterion": "Patients with histologically confirmed diagnosis of prostate cancer who have not yet developed bone metastases Prostate cancer patients with a rise in PSA under hormone therapy. PSA criteria: Patients who have undergone prostatectomy: any rise in PSA or Patients without prostatectomy: 2 consecutive rises in PSA levels relative to a previous reference value, separated by one month. The first measurement must occur one month after the reference value and must be above the reference value. The second confirmatory measurement taken one month after the first measurement must be greater than the first measurement. Previous chemotherapy or radiotherapy must have been performed ≥ 8 weeks prior to study entry. Eastern Cooperative Oncology Group (ECOG) score of 0, 1 or 2 (patients that spend less than 50% of time in bed during the day) Adequate liver function - serum total bilirubin concentration less than 1.5 x upper limit of normal value Age: ≥ 18 years Patient has given written informed consent prior to any study-specific procedures. Patients with psychiatric or addictive disorders which prevent them from giving their informed consent must not enter the study.", "candidate_expression": "((Age ≥ 18 years) AND (Eastern Cooperative Oncology Group (ECOG) score 0, 1 or 2) AND (PSA levels rises) AND (PSA rise) AND (Prostate cancer) AND (bone metastases) AND (histologically confirmed) AND (hormone therapy) AND (liver function Adequate) AND (measurement one month after the first measurement greater than the first measurement second) AND (measurement one month after the reference value above the reference value first) AND (prostate cancer) AND (prostatectomy) AND (prostatectomy 2) AND (serum total bilirubin concentration less than 1.5 x upper limit of normal value) AND (spend time in bed during the day less than 50%) AND (without) AND ((chemotherapy) OR (radiotherapy)) AND ((addictive disorders) OR (psychiatric disorders)))"}
{"candidate_id": "LLM07242", "doc_id": "NCT03228238_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07243", "doc_id": "NCT02466113_exc", "case_bucket": "or", "source_criterion": "With severe comorbidities, such as cardiovascular disease, chronic obstructive pulmonary disease, diabetes mellitus, and chronic renal dysfunction. With bad compliance or contraindication to enrollment. Pregnant woman or lactating woman. With contraindication to receive adjuvant chemotherapy.", "candidate_expression": "((Pregnant) AND (adjuvant chemotherapy) AND (bad compliance) AND (comorbidities) AND (contraindication) AND (contraindication to enrollment) AND (lactating) AND (severe) AND (woman) AND ((bad compliance) OR (contraindication to enrollment)) AND ((cardiovascular disease) OR (chronic obstructive pulmonary disease) OR (chronic renal dysfunction) OR (diabetes mellitus)))"}
{"candidate_id": "LLM07244", "doc_id": "NCT01943409_exc", "case_bucket": "other", "source_criterion": "• Patients without PN during their hospitalization", "candidate_expression": "((hospitalization) AND NOT (PN during their hospitalization))"}
{"candidate_id": "LLM07245", "doc_id": "NCT03637946_exc", "case_bucket": "or", "source_criterion": "With severe systemic alteration; In the use of antibiotics and anti-inflammatories in the last three months; With periodontium with periodontal parameters different from those established in the inclusion criteria. Individuals with clinical signs of parafunctional habits; Smoking; Individuals who have performed other restorations in the last 12 months; Pregnant women and infants; Periodontal sites that presented bleeding during crevicular fluid collection or sites that prevent proper collection of clinical parameters.", "candidate_expression": "((Pregnant) AND (Smoking) AND (anti-inflammatories) AND (antibiotics) AND (clinical signs of parafunctional habits) AND (infants) AND (other restorations in the last 12 months) AND (systemic alteration severe) AND (women))"}
{"candidate_id": "LLM07246", "doc_id": "NCT01696617_inc", "case_bucket": "or", "source_criterion": "Age : 18-65 Patients with major depressive disorder according to DSM-IV criteria that have lasted >8 weeks MADRS total score of 18 or higher Patients who responded inadequately (a score of >18 on the MADRS) to first-line antidepressant treatment of 4 week duration Current use of standard antidepressant treatment in monotherapy or combination of 2 antidepressants : escitalopram (10 - 20mg/d), fluoxetine(20 - 40mg/d), paroxetine CR(25 - 50mg/d), sertraline(100 - 150mg/d), mirtazapine (15 - 45mg/d), duloxetine (30 - 60mg/d) or venlafaxine ER(150-225mg/d)", "candidate_expression": "((10 - 20mg/d) AND (100 - 150mg/d) AND (15 - 45mg/d) AND (150-225mg/d) AND (18-65) AND (2) AND (20 - 40mg/d) AND (25 - 50mg/d) AND (30 - 60mg/d) AND (Age) AND (DSM-IV criteria) AND (MADRS) AND (antidepressant) AND (antidepressants) AND (duloxetine) AND (escitalopram) AND (first-line) AND (fluoxetine) AND (lasted >8 weeks) AND (major depressive disorder) AND (mirtazapine) AND (monotherapy) AND (of 4 week) AND (paroxetine CR) AND (responded inadequately) AND (score of 18 or higher) AND (score of >18) AND (sertraline) AND (standard) AND (venlafaxine ER))"}
{"candidate_id": "LLM07247", "doc_id": "NCT02175186_exc", "case_bucket": "or", "source_criterion": "Pregnant or breast feeding History of Stomach or esophagus surgery Peptic ulcer or reflux esophagitis Zollinger-Ellison syndrome or primary esophageal motility disorders Malignant tumor Bleeding tendency or coagulopathy Contraindication of ALBIS Long term use of aspirin or P2Y12 receptor antagonist within 1month Patients who tool medicine such as PPI, APA,H2blocker, Muscarine receptor antagonist, anti-gastic agent, antacid, anticaogulant, Bisphosphonate agents, Cytotoxic drug, NSAID, adrenal cortex hormone agents (topical treatment is allowed) Terminal patient", "candidate_expression": "((ALBIS) AND (APA) AND (Bisphosphonate agents) AND (Bleeding tendency) AND (Contraindication) AND (Cytotoxic drug) AND (H2blocker) AND (Long term) AND (Malignant tumor) AND (Muscarine receptor antagonist) AND (NSAID) AND (P2Y12 receptor antagonist) AND (PPI) AND (Peptic ulcer) AND (Pregnant or breast feeding) AND (Stomach surgery) AND (Terminal) AND (Zollinger-Ellison syndrome) AND (adrenal cortex hormone agents) AND (allowed) AND (antacid) AND (anti-gastic agent) AND (anticaogulant) AND (aspirin) AND (coagulopathy) AND (esophagus surgery) AND (patient) AND (primary esophageal motility disorders) AND (reflux esophagitis) AND (topical treatment) AND (within 1month))"}
{"candidate_id": "LLM07248", "doc_id": "NCT00730301_exc", "case_bucket": "or", "source_criterion": "Prior endobronchial treatment for emphysema Pleural or interstitial disease that precludes surgery. Prior lung transplant, LVRS, median sternotomy, bullectomy or lobectomy. Clinically significant bronchiectasis Pulmonary nodule requiring surgery History of recurrent respiratory infections (> 3 hospitalization in the last year) Clinically significant (> 4 Tablespoons per day) sputum production Fever, elevated white cell count, or other evidence of active infection Dysrhythmia that might pose a risk during exercise or training Congestive heart failure within 6 mo and LVEF < 45% Evidence or history of Cor Pulmonale Resting bradycardia (< 50 beats/min), frequent multifocal PVCs, complex ventricular arrhythmia, sustained SVT History of exercise-related syncope MI within 6 mo and LVEF < 45% Evidence of systemic disease or neoplasia expected to compromise survival during 5-yr period Any disease or condition that interferes with completion of initial or follow-up assessments Patient is currently enrolled in another clinical trial Patient is unable to complete 3 minutes of unloaded peddling on cycle ergometer Alpha-1-Antitrypsin Deficiency", "candidate_expression": "((3 minutes of unloaded peddling on cycle ergometer) AND (< 45%) AND (< 50 beats/min) AND (> 3 in the last year) AND (> 4 Tablespoons per day) AND (Alpha-1-Antitrypsin Deficiency) AND (Clinically significant) AND (Congestive heart failure) AND (Cor Pulmonale) AND (Dysrhythmia) AND (Evidence) AND (Fever) AND (History) AND (LVEF) AND (LVRS) AND (MI) AND (Pleural disease) AND (Prior) AND (Pulmonary nodule) AND (Resting bradycardia) AND (active infection) AND (bronchiectasis) AND (bullectomy) AND (complex ventricular arrhythmia) AND (condition) AND (currently) AND (disease) AND (during 5-yr period) AND (during exercise) AND (during training) AND (elevated) AND (emphysema) AND (endobronchial treatment) AND (enrolled in another clinical trial) AND (evidence) AND (exercise) AND (exercise-related) AND (expected to compromise survival) AND (frequent) AND (history) AND (hospitalization) AND (interferes with completion of initial or follow-up assessments) AND (interstitial disease) AND (lobectomy) AND (lung transplant) AND (median sternotomy) AND (multifocal PVCs) AND (neoplasia) AND (pose a risk) AND (precludes) AND (precludes surgery) AND (recurrent) AND (respiratory infections) AND (sputum production) AND (surgery) AND (sustained SVT) AND (syncope) AND (systemic disease) AND (training) AND (unable to complete) AND (white cell count) AND (within 6 mo))"}
{"candidate_id": "LLM07249", "doc_id": "NCT03376763_inc", "case_bucket": "or", "source_criterion": "Subjects must be capable of providing signed and dated written informed consent by date of Visit 0 (-2 week). Male and female aged =19 and < 65 years. Subjects diagnosed of schizophrenia as defined by Diagnostic and Statistical Manual of Mental Disorders, 4th edition text revision or 5th edition (DSM-<U+2163>-TR or 5) criteria, and a history of illness for at least for 3 years prior to screening. Subjects who take atypical antipsychotic drugs, and should be maintained on current antipsychotic drugs (including atypical antipsychotic drugs) and dose for at least 4 weeks prior to the screening. Subjects who need antipsychotic treatment (other than clozapine), and would be stable when switching to long-acting injectable aripiprazole in the investigator's judgement. Subjects must exhibit willingness, physiologic capability, and an educational level sufficient to comply with all protocol procedures.", "candidate_expression": "((Subjects must be capable of providing signed and dated written informed consent by date of Visit 0 (-2 week).) AND (Subjects must exhibit willingness, physiologic capability, and an educational level sufficient to comply with all protocol procedures.) AND (aged =19 and < 65 years) AND (atypical antipsychotic drugs) AND (schizophrenia Diagnostic and Statistical Manual of Mental Disorders, 4th edition text revision or 5th edition (DSM-<U+2163>-TR or 5) criteria history of illness) AND ((Male) OR (female)))"}
{"candidate_id": "LLM07250", "doc_id": "NCT02916342_inc", "case_bucket": "other", "source_criterion": "ASA physical status I-III; 18-85 years of age, inclusive; surgery less than 3 hours.", "candidate_expression": "((18-85 years , inclusive) AND (ASA physical status) AND (I-III) AND (age) AND (less than 3 hours) AND (surgery))"}
```
