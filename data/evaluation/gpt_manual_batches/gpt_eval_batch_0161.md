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
{"candidate_id": "LLM04001", "doc_id": "NCT00846703_exc", "case_bucket": "other", "source_criterion": "No Down syndrome No other major disease that prohibits study treatment (e.g., severe congenital heart disease) Not requiring significant therapy modification owing to study therapy associated complications No complications due to other interventions No one with missing data that are needed for the differential diagnosis, or for selection of the proper therapy arm", "candidate_expression": "((No) AND (Not) AND (complications) AND (congenital heart disease severe) AND (interventions other) AND (study therapy) AND NOT (complications) AND NOT (Down syndrome) AND NOT (major disease other))"}
{"candidate_id": "LLM04002", "doc_id": "NCT01320579_inc", "case_bucket": "or", "source_criterion": "Informed consent obtained prior to any screening procedure Caucasian male or female patient At least 18 years of age Weight at least 45 kg Patient with moderate or severe chronic atopic dermatitis Good general health ascertained by medical history, physical examination and laboratory determinations, showing no signs of clinically significant findings, except chronic atopic dermatitis Negative pregnancy test (premenopausal female patient) at screening and use of adequate contraceptive measures (both male and female patients) throughout the study and 30 days after the last cis-UCA dose", "candidate_expression": "((At least 18 years) AND (Caucasian) AND (Good general health) AND (Informed consent obtained prior to any screening procedure) AND (Negative) AND (Negative pregnancy test (premenopausal female patient) at screening and use of adequate contraceptive measures (both male and female patients) throughout the study and 30 days after the last cis-UCA dose) AND (Weight) AND (age) AND (ascertained by medical history, physical examination and laboratory determinations) AND (at least 45 kg) AND (chronic atopic dermatitis) AND (clinically significant) AND (except) AND (female) AND (laboratory determinations) AND (male) AND (medical history) AND (moderate) AND (no) AND (physical examination) AND (pregnancy test) AND (premenopausal) AND (severe) AND (signs of clinically significant findings))"}
{"candidate_id": "LLM04003", "doc_id": "NCT02570347_inc", "case_bucket": "other", "source_criterion": "Age 18-65 years History of snake bite with features of local envenomation with/without systemic features Less than 24 hours since bite, AND No prior antibiotic treatment", "candidate_expression": "((18-65 years) AND (Age) AND (Less than 24 hours since bite) AND (No) AND (antibiotic treatment) AND (bite) AND (features of) AND (local envenomation) AND (prior) AND (snake bite) AND (systemic features))"}
{"candidate_id": "LLM04004", "doc_id": "NCT03168555_exc", "case_bucket": "or", "source_criterion": "small bowel resection right sided hemicolectomy known chronic diarrheal disease (celiac disease, lactose malabsorption, Inflammatory bowel diseases, incl microscopic colitis) pregnancy wish for pregnancy within next three months allergy to eggs allergy to constituents in Xenbilox (capsules with chenodeoxycholic acid) acute cholecystitis within two months chronic cholecystitis cirrhosis of the liver suspected obstructive choledocholithiasis icterus", "candidate_expression": "((acute cholecystitis) AND (allergy) AND (chenodeoxycholic acid) AND (chronic cholecystitis) AND (chronic diarrheal disease) AND (cirrhosis of the liver) AND (constituents in Xenbilox) AND (eggs) AND (icterus) AND (obstructive choledocholithiasis) AND (pregnancy) AND (right sided hemicolectomy) AND (small bowel resection) AND (suspected) AND (wish for) AND (within next three months) AND (within two months) AND ((Inflammatory bowel diseases) OR (celiac disease) OR (lactose malabsorption) OR (microscopic colitis)))"}
{"candidate_id": "LLM04005", "doc_id": "NCT02394158_inc", "case_bucket": "other", "source_criterion": "Singleton pregnancy; 8-22 weeks gestation Previous pregnancy complicated by gestational diabetes", "candidate_expression": "((8-22 weeks) AND (Singleton pregnancy) AND (gestation) AND (gestational diabetes) AND (pregnancy))"}
{"candidate_id": "LLM04006", "doc_id": "NCT02957305_inc", "case_bucket": "other", "source_criterion": "All patients admitted at the Gynecological emergency Unit at Hospital de Clínicas de Porto Alegre scheduled for uterine evacuation with <12 weeks of gestation.", "candidate_expression": "((<12 weeks) AND (Gynecological emergency Unit at Hospital de Clínicas de Porto Alegre) AND (gestation) AND (uterine evacuation))"}
{"candidate_id": "LLM04007", "doc_id": "NCT03088904_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04008", "doc_id": "NCT02396420_inc", "case_bucket": "or", "source_criterion": "Patient has provided signed informed consent Patient is aged greater than or equal to 40 and less than or equal to 89 years of age Patient has a prostate size between 90g and 200g, as determined by MRI Patient has experienced lower urinary tract symptoms (LUTS) for at least 6 months prior to study enrollment Patient has an IPSS score of at least 13 at baseline Patient is either: refractory to medical treatment, contraindicated to medical treatment, OR refuses medical treatment Patient either: refuses surgical treatment OR is contraindicated for surgical treatment Patient meets ONE of the following criteria: baseline PSA < 4.0ng/mL (no prostate biopsy required) OR baseline PSA >/= 4 ng/mL AND a negative prostate biopsy (minimum 12 core biopsy) within the prior 12 months", "candidate_expression": "((< 4.0ng/mL) AND (>/= 4 ng/mL) AND (IPSS score) AND (MRI) AND (PSA) AND (aged) AND (at baseline) AND (at least 13) AND (at least 6 months prior to study enrollment) AND (baseline) AND (between 90g and 200g) AND (contraindicated for surgical treatment) AND (contraindicated to medical treatment) AND (core biopsy) AND (greater than or equal to 40) AND (less than or equal to 89 years) AND (lower urinary tract symptoms (LUTS)) AND (minimum 12) AND (negative) AND (prostate biopsy) AND (prostate size) AND (refractory to medical treatment) AND (refuses medical treatment) AND (refuses surgical treatment) AND (signed informed consent) AND (study enrollment) AND (within the prior 12 months))"}
{"candidate_id": "LLM04009", "doc_id": "NCT03479502_exc", "case_bucket": "or", "source_criterion": "allergy to Doxycycline or Methylprednisolone, pregnancy, diagnosis, Inflammatory arthritis or diabetes, secondary adhesive capsulitis (history of significant trauma, rotator cuff tear injury, stroke) evidence of arthritis on x-ray, current infectious disease, and any previous treatment for the for adhesive capsulitis of the affected shoulder.", "candidate_expression": "((Doxycycline) AND (Inflammatory arthritis) AND (Methylprednisolone) AND (adhesive capsulitis) AND (affected shoulder) AND (allergy) AND (any) AND (arthritis) AND (current) AND (diabetes) AND (diagnosis) AND (evidence of) AND (history) AND (infectious disease) AND (pregnancy) AND (previous) AND (rotator cuff tear injury) AND (secondary) AND (significant) AND (stroke) AND (trauma) AND (treatment) AND (x-ray))"}
{"candidate_id": "LLM04010", "doc_id": "NCT02763007_inc", "case_bucket": "or", "source_criterion": "Completed \"ALO-IIT-012(PEAK study)\", without major protocol deviations. Male, or female, 19 years to 75 years. Female with childbearing potential who has a negative urine pregnancy test result at study start and willing to continue practice appropriate birth control during the entire duration of study Subjects completed PEAK can be included within 30 days after End Of the Study Subjects completed PEAK can be included if their treatment is the same as randomized even after 30 days of End Of the Study.", "candidate_expression": "((Completed \"ALO-IIT-012(PEAK study)\", without major protocol deviations) AND (Female with childbearing potential who has a negative urine pregnancy test result at study start and willing to continue practice appropriate birth control during the entire duration of study) AND (Subjects completed PEAK can be included if their treatment is the same as randomized even after 30 days of End Of the Study) AND (Subjects completed PEAK can be included within 30 days after End Of the Study) AND (years 19 years to 75) AND ((Male) OR (female)))"}
{"candidate_id": "LLM04011", "doc_id": "NCT02425774_exc", "case_bucket": "or", "source_criterion": "adjuvant radiotherapy evident intra-abdominal inflammation (diagnosed by imaging and/or laboratory results, including an abscess or cholecystitis) chronic pancreatitis pancreatic polypeptide producing endocrine tumor American Society of Anesthesiologists physical-health status classification (ASA-PS)>3 Poorly regulated diabetes (>200 mg/dl (=11 mmol/l))", "candidate_expression": "((>200 mg/dl (=11 mmol/l)) AND (>3) AND (American Society of Anesthesiologists physical-health status classification (ASA-PS)) AND (Poorly regulated) AND (adjuvant radiotherapy) AND (chronic) AND (chronic pancreatitis) AND (diabetes) AND (intra-abdominal inflammation) AND (pancreatic polypeptide producing endocrine tumor) AND (pancreatitis) AND ((imaging) OR (laboratory)) AND ((abscess) OR (cholecystitis)))"}
{"candidate_id": "LLM04012", "doc_id": "NCT02901106_exc", "case_bucket": "other", "source_criterion": "pregnant or breastfeeding woman patient with a measure of legal protection subject unaffiliated insurance", "candidate_expression": "((patient with a measure of legal protection) AND (pregnant or breastfeeding woman))"}
{"candidate_id": "LLM04013", "doc_id": "NCT02425774_exc", "case_bucket": "or", "source_criterion": "adjuvant radiotherapy evident intra-abdominal inflammation (diagnosed by imaging and/or laboratory results, including an abscess or cholecystitis) chronic pancreatitis pancreatic polypeptide producing endocrine tumor American Society of Anesthesiologists physical-health status classification (ASA-PS)>3 Poorly regulated diabetes (>200 mg/dl (=11 mmol/l))", "candidate_expression": "((American Society of Anesthesiologists physical-health status classification (ASA-PS) >3) AND (adjuvant radiotherapy) AND (chronic pancreatitis) AND (diabetes Poorly regulated >200 mg/dl (=11 mmol/l)) AND (intra-abdominal inflammation) AND (pancreatic polypeptide producing endocrine tumor) AND (pancreatitis chronic) AND ((imaging) OR (laboratory)) AND ((abscess) OR (cholecystitis)))"}
{"candidate_id": "LLM04014", "doc_id": "NCT02209545_exc", "case_bucket": "or", "source_criterion": "Patients who have had a prior abdominal myomectomy Post-menopausal women Patients with known bleeding/clotting disorders Patients with a history of gynecologic malignancy History of allergic reactions attributed to compounds of similar chemical or biologic composition to misoprostol Any cases converted to abdominal hysterectomy or other additional elective surgical procedures performed at time of abdominal myomectomy will be excluded from data analysis Uncontrolled intercurrent illness including, but not limited to, ongoing or active infection, symptomatic congestive heart failure, unstable angina pectoris, cardiac arrhythmia, or psychiatric illness/social situations that would limit compliance with study requirements.", "candidate_expression": "((Post-menopausal) AND (abdominal myomectomy) AND (abdominal myomectomy prior) AND (allergic reactions History) AND (compounds of similar chemical or biologic composition to misoprostol) AND (gynecologic malignancy history) AND (intercurrent illness Uncontrolled) AND (misoprostol) AND (women) AND ((abdominal hysterectomy converted to) OR (surgical procedures other additional elective at time of abdominal myomectomy)) AND ((active) OR (ongoing)) AND ((cardiac arrhythmia) OR (congestive heart failure symptomatic) OR (infection) OR (psychiatric illness) OR (social situations that would limit compliance with study requirements) OR (unstable angina pectoris)) AND ((clotting disorders) OR (disorders bleeding)))"}
{"candidate_id": "LLM04015", "doc_id": "NCT03282006_inc", "case_bucket": "or", "source_criterion": "E.coli in blood culture AND identical isolate in urine sample (>= 1.000 CFU) OR relevant clinical signs of UTI", "candidate_expression": "((>= 1.000) AND (CFU) AND (E.coli) AND (blood culture) AND (clinical signs) AND (identical isolate) AND ((UTI) OR (urine sample)))"}
{"candidate_id": "LLM04016", "doc_id": "NCT02739295_exc", "case_bucket": "or", "source_criterion": "Toxic epidermal necrolysis with SCORTEN 6 or 7 at admission Hypercoagulable state Cardiac or peripheral arterial disease Active malignancy Myelodysplastic syndrome or hematological malignancy Fructose intolerance Pregnancy Patient refusal", "candidate_expression": "((Fructose) AND (Fructose intolerance) AND (Hypercoagulable state) AND (Patient refusal) AND (Pregnancy) AND (SCORTEN 6 or 7 at admission) AND (Toxic epidermal necrolysis) AND (malignancy Active) AND ((Myelodysplastic syndrome) OR (hematological malignancy)) AND ((disease Cardiac) OR (peripheral arterial disease)))"}
{"candidate_id": "LLM04017", "doc_id": "NCT02566928_inc", "case_bucket": "or", "source_criterion": "between 7 to 70 years of age fluent in English or Spanish plans to receive care in the Community Health Center during the next year presents with signs and symptoms of a SSTI willing/able to provide informed consent", "candidate_expression": "((Community Health Center) AND (SSTI) AND (age between 7 to 70 years) AND (fluent in English) AND (fluent in Spanish) AND (receive care plans to during the next year) AND (signs) AND (symptoms) AND (willing/able to provide informed consent))"}
{"candidate_id": "LLM04018", "doc_id": "NCT02890719_inc", "case_bucket": "or", "source_criterion": "Age between 18 and 78 year-old. Previous liver transplantation(more than 6 month). Genotype 1 and 4 infection. Hepatitis C recurrence defined by the presence of abnormal liver function test, positive HCV-RNA, histological signs of hepatitis C recurrence. Viral load ≥10000UI/mL. Immunosuppression with tacrolimus and/or mycophenolate (Prednisone use is allowed at low dose, ≤10 mg/d). Treatment naïve or treatment experienced (Peg-RBV or triple therapy).", "candidate_expression": "((Age between 18 and 78 year-old) AND (Genotype 1 and 4) AND (HCV-RNA positive) AND (Hepatitis C recurrence) AND (Immunosuppression ≤10 mg/d) AND (Viral load ≥10000UI/mL) AND (hepatitis C recurrence) AND (histological) AND (histological signs of hepatitis C recurrence) AND (infection) AND (liver function test abnormal) AND (liver transplantation Previous more than 6 month) AND ((Prednisone low dose) OR (mycophenolate) OR (tacrolimus)) AND ((Treatment naïve) OR (treatment experienced)) AND ((Peg-RBV) OR (triple therapy)))"}
{"candidate_id": "LLM04019", "doc_id": "NCT03513757_exc", "case_bucket": "or", "source_criterion": "Inpatient status, airway abnormalities, allergy to any study medications, eggs and soy, and mitochondrial disorders. All subjects with any cardiac disease or history of cardiac arrhythmias will be excluded.", "candidate_expression": "((history) AND ((Inpatient status) OR (airway abnormalities) OR (allergy) OR (mitochondrial disorders)) AND ((cardiac arrhythmias) OR (cardiac disease)) AND ((eggs) OR (soy) OR (study medications)))"}
{"candidate_id": "LLM04020", "doc_id": "NCT03511521_exc", "case_bucket": "or", "source_criterion": "Patients with 2 or more doses of methylprednisolone/prednisone per day Steroids other than methylprednisolone or prednisone Pregnancy estimated glomerular filtration rate (eGFR) < 45 ml/min/1.73m2", "candidate_expression": "((2 or more doses per day) AND (< 45 ml/min/1.73m2) AND (Pregnancy) AND (Steroids) AND (estimated glomerular filtration rate (eGFR)) AND (other than) AND ((methylprednisolone) OR (prednisone)))"}
{"candidate_id": "LLM04021", "doc_id": "NCT02579733_inc", "case_bucket": "other", "source_criterion": "Ulcerative colitis patients with moderate to severe activity who achieved a clinical remission by the first course of corticosteroids Newly diagnosed or without steroid use during last 1 year Endoscopic Mayo subscore >0", "candidate_expression": "((Endoscopic Mayo subscore >0) AND (Ulcerative colitis moderate to severe) AND (clinical remission by the first course of corticosteroids) AND (corticosteroids first course) AND NOT (steroid during last 1 year))"}
{"candidate_id": "LLM04022", "doc_id": "NCT02894268_exc", "case_bucket": "or", "source_criterion": "Bismuth compounds, acid inhibitor, or antibiotics during 4 weeks before the patient is enrolled Allergic to the medications Upper gastrointestinal surgery history Serious heart insufficiency, liver insufficiency, renal insufficiency and other serious medical problems Evidence of blood dyscrasia Pregnant and lactating women Can't express his complain correctly and can't cooperate with the researcher", "candidate_expression": "((Allergic) AND (Bismuth compounds) AND (Pregnant) AND (Upper gastrointestinal surgery history) AND (acid inhibitor) AND (antibiotics) AND (blood dyscrasia Evidence) AND (heart insufficiency Serious) AND (lactating) AND (liver insufficiency) AND (medications) AND (renal insufficiency) AND (serious medical problems other) AND (women))"}
{"candidate_id": "LLM04023", "doc_id": "NCT01757717_inc", "case_bucket": "other", "source_criterion": "Patients must have histologic proof of a malignancy suitable for radiation therapy. Patients must have received prior external beam radiation therapy to the region proposed for HDR brachytherapy treatment; evaluation of doses previously delivered to spinal cord/cauda equine, pelvis, and other critical structures (bowel, kidneys, rectum) will be taken into consideration. If repeat irradiation would exceed any normal tissue constraint set by MSKCC Radiation Oncology Department dose constraint criteria, the patient will potentially be eligible. If the total prior radiation dose to the cord or pelvis exceeds 100 Gy BED equivalent, the patient will be potentially eligible, where a total of 100 BED Gy equivalent is determined by the biological equivalent dose (BED) calculation; BED = nd(1 + d/α/β), where n = number of fractions and d = dose per fraction; α/β is the constant for spinal cord late effect and equals 2. [Rades 2005, Nieder 2005, Sahgal 2012] KPS ≥ 60 Age ≥ 18 years old", "candidate_expression": "((Age) AND (HDR brachytherapy) AND (KPS) AND (MSKCC Radiation Oncology Department dose constraint criteria) AND (exceed any normal tissue constraint) AND (external beam radiation therapy) AND (histologic) AND (malignancy) AND (prior) AND (proof) AND (radiation therapy) AND (repeat irradiation) AND (suitable for radiation therapy) AND (to the region proposed for HDR brachytherapy treatment) AND (≥ 18 years old) AND (≥ 60))"}
{"candidate_id": "LLM04024", "doc_id": "NCT01944800_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04025", "doc_id": "NCT03434951_inc", "case_bucket": "other", "source_criterion": "elective primary total knee arthroplasty ASA I-III written consent", "candidate_expression": "((ASA I-III) AND (total knee arthroplasty elective primary) AND (written consent))"}
```
