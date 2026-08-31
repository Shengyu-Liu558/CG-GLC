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
{"candidate_id": "LLM04101", "doc_id": "NCT02208739_inc", "case_bucket": "or", "source_criterion": "Patients should have at least 12 teeth present Patients with Moderate to Advanced Chronic periodontitis Patients with 2 or more interproximal sites (not on same tooth) with probing pocket depths of 5mm or more and 2 or more interproximal sites (not on same tooth)of probing attachment loss of 4mm or more which bled on probing.", "candidate_expression": "((2 or more) AND (4mm or more) AND (5mm or more) AND (Chronic periodontitis) AND (at least 12) AND (bled on probing) AND (interproximal sites of probing attachment loss of 4mm or more) AND (interproximal sites with probing pocket depths of 5mm or more) AND (probing) AND (teeth present) AND ((Advanced) OR (Moderate)))"}
{"candidate_id": "LLM04102", "doc_id": "NCT03044561_inc", "case_bucket": "other", "source_criterion": "(1) cases of infertility, older than 20 years of age and not older than 40 years. (2) Body mass index (BMI):20-29. (3) women have experienced two or more implantation failure attributed to inadequate endometrial development.", "candidate_expression": "((20-29) AND (BMI) AND (Body mass index) AND (age) AND (attributed to) AND (failure) AND (implantation) AND (inadequate endometrial development) AND (infertility) AND (not older than 40 years) AND (older than 20 years) AND (two or more) AND (women))"}
{"candidate_id": "LLM04103", "doc_id": "NCT02713087_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for supine-positioned elective craniotomy for supratentorial malignant and non-malignant brain tumors 3 cm or larger (measured as the largest diameter in any plane on MR images) ASA (American Society of Anesthesiologist) status 1-3 (27) Written informed consent from participating patients", "candidate_expression": "((1-3) AND (27) AND (3 cm or larger) AND (ASA status) AND (American Society of Anesthesiologist status) AND (MR) AND (Written informed consent from participating patients) AND (brain tumors) AND (largest diameter in any plane) AND (non) AND (scheduled) AND (supine-positioned elective craniotomy) AND (supratentorial) AND ((malignant)))"}
{"candidate_id": "LLM04104", "doc_id": "NCT03264911_exc", "case_bucket": "or", "source_criterion": "Hypersensitivity to B-lactams concomitant disease which must be treated with antibiotics chronic disease-Immunocompromised Antibiotics within 72 h history of ARF,scarlet fever,impetigo,acute glomerulonephritis Family history of ARF Complicated pharyngitis", "candidate_expression": "((ARF) AND (ARF Family history) AND (Antibiotics within 72 h) AND (B-lactams) AND (Hypersensitivity) AND (Immunocompromised) AND (acute glomerulonephritis) AND (antibiotics) AND (disease concomitant) AND (impetigo) AND (pharyngitis Complicated) AND (scarlet fever) AND (treated))"}
{"candidate_id": "LLM04105", "doc_id": "NCT02102243_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure or coronary artery disease Blood pressure averaging > 159/99 mmHg Serum creatinine > 1.5 mg/dL Diabetes mellitus or other systemic illness Left ventricular hypertrophy by echocardiography or ECG Pregnancy Hypersensitivity to spironolactone, chlorthalidone, amlodipine, human recombinant insulin or Definity Any history of substance abuse (other than tobacco) History of gouty arthritis Patients with right-to-left, bi-directional, or transient right-to-left cardiac shunts Hypersensitivity to perflutren, blood, blood products or albumin", "candidate_expression": "((Blood pressure > 159/99 mmHg) AND (ECG) AND (Hypersensitivity) AND (Left ventricular hypertrophy) AND (Pregnancy) AND (Serum creatinine > 1.5 mg/dL) AND (cardiac shunts transient right-to-left) AND (echocardiography) AND (gouty arthritis) AND (substance abuse) AND NOT (tobacco) AND ((Congestive heart failure) OR (coronary artery disease)) AND ((amlodipine) OR (chlorthalidone) OR (human recombinant insulin) OR (spironolactone)) AND ((bi-directional) OR (right-to-left,)) AND ((albumin) OR (blood) OR (blood products) OR (perflutren)) AND ((Diabetes mellitus) OR (systemic illness)))"}
{"candidate_id": "LLM04106", "doc_id": "NCT00343668_exc", "case_bucket": "or", "source_criterion": "Other tumor type than adenocarcinoma Central nervous system (CNS) metastases or prior radiation for CNS metastases Gastric outlet obstruction or intestinal obstruction Evidence of gastrointestinal bleeding The patient has bony lesions as the sole evaluable disease. Past or concurrent history of neoplasm other than stomach cancer, except for curatively treated non-melanoma skin cancer or in situ carcinoma of the cervix uteri Pregnant or lactating women, women of childbearing potential not employing adequate contraception Other serious illness or medical conditions Unstable cardiac disease despite treatment, myocardial infarction within 6 months prior to study entry History of significant neurologic or psychiatric disorders including dementia or seizures Active uncontrolled infection Other serious underlying medical conditions which could impair the ability of the patient to participate in the study Concomitant administration of any other experimental drug under investigation, or concomitant chemotherapy, hormonal therapy, or immunotherapy concomitant drug medication; The following drugs cause drug interaction with S-1. i. Warfarin, phenprocoumon: increase bleeding tendency ii. Increase blood concentration of phenytoin iii. sorivudine: inhibit DPD -> increase toxicity according to fluoropyrimidine iv. allopurinol : decrease activity of S-1", "candidate_expression": "((CNS metastases) AND (Evidence of) AND (History) AND (ability of the patient to participate) AND (bleeding tendency increase) AND (blood concentration of phenytoin Increase) AND (bony lesions the sole) AND (childbearing potential) AND (experimental drug Concomitant) AND (gastrointestinal bleeding) AND (history of) AND (infection Active uncontrolled) AND (neoplasm) AND (serious medical conditions) AND (treatment) AND (tumor) AND (women) AND NOT (adenocarcinoma) AND NOT (stomach cancer) AND NOT (treated curatively) AND NOT (contraception) AND ((in situ carcinoma of the cervix uteri) OR (non-melanoma skin cancer)) AND ((Pregnant) OR (lactating)) AND ((medical conditions) OR (serious illness)) AND ((Central nervous system (CNS) metastases) OR (radiation)) AND ((Unstable cardiac disease) OR (myocardial infarction within 6 months prior to study entry)) AND ((neurologic disorders) OR (psychiatric disorders)) AND ((dementia) OR (seizures)) AND ((chemotherapy) OR (hormonal therapy) OR (immunotherapy)) AND ((drug) OR (medication)) AND ((Warfarin) OR (phenprocoumon)) AND ((Gastric outlet obstruction) OR (intestinal obstruction)) AND ((allopurinol) OR (fluoropyrimidine) OR (sorivudine)))"}
{"candidate_id": "LLM04107", "doc_id": "NCT02284737_exc", "case_bucket": "or", "source_criterion": "Pregnancy and breast feeding mother; Estimated life expectancy <12 months; Scheduled major surgery in the next 6 months; Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk; Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 30 days. WHO group II, III, IV, V PH Severe Renal dysfunction (Ccr<30 ml/min) Blood platelet count<100,000/L Expected life span<6-month Systematical inflammation Malignant cancer(s) Tricuspid valve stenosis, Supra-pulmonary valve stenosis Allergic to studied drugs or metal materials.", "candidate_expression": "((<100,000/L) AND (<12 months) AND (<30 ml/min) AND (<6-month) AND (Allergic) AND (Blood platelet count) AND (Ccr) AND (Estimated life expectancy) AND (Expected life span) AND (Inability to comply with follow-up requirements) AND (Inability to follow the protocol) AND (Malignant cancer) AND (PH) AND (Pregnancy) AND (Previous) AND (Renal dysfunction) AND (Scheduled) AND (Severe) AND (Supra-pulmonary valve stenosis) AND (Systematical inflammation) AND (Tricuspid valve stenosis) AND (WHO) AND (breast feeding) AND (device) AND (enrolment in this study) AND (group II, III, IV, V) AND (in the next 6 months) AND (investigational drug) AND (major surgery) AND (studied drugs) AND (studied metal materials) AND (treatment with an investigational drug))"}
{"candidate_id": "LLM04108", "doc_id": "NCT01391780_exc", "case_bucket": "or", "source_criterion": "neurological diseases previous pelvic surgeries diabetes cognitive difficulties vaginal and urinary infection", "candidate_expression": "((cognitive difficulties) AND (diabetes) AND (neurological diseases) AND (pelvic surgeries) AND (previous) AND ((infection vaginal) OR (urinary infection)))"}
{"candidate_id": "LLM04109", "doc_id": "NCT02055053_inc", "case_bucket": "or", "source_criterion": "Age 18 or older with unilateral or bilateral inguinal herna for laparoscopic repair American Society of Anesthesiology (ASA) Class I and II", "candidate_expression": "((Age 18 or older) AND (American Society of Anesthesiology (ASA) Class I and II) AND (inguinal herna for laparoscopic repair) AND (laparoscopic repair) AND ((bilateral) OR (unilateral)))"}
{"candidate_id": "LLM04110", "doc_id": "NCT02528136_exc", "case_bucket": "or", "source_criterion": "Patients with placenta pathology such as praevia, acreta, pre-eclampsia Patients with bleeding disorders including vonWillebrand disease type I. Known intolerance to one of the two drugs. Patients with prolonged QT-time or other serious cardiac diseases. Liver or kidney failure. Epilepsy. Any medical reason why, in the opinion of the investigator, the patient should not participate", "candidate_expression": "((Any medical reason why, in the opinion of the investigator, the patient should not participate) AND (Epilepsy) AND (bleeding disorders) AND (drugs one of the two) AND (intolerance) AND (placenta pathology) AND (vonWillebrand disease type I) AND ((prolonged QT-time) OR (serious cardiac diseases other)) AND ((Liver failure) OR (kidney failure)) AND ((acreta) OR (praevia) OR (pre-eclampsia)))"}
{"candidate_id": "LLM04111", "doc_id": "NCT03131050_inc", "case_bucket": "or", "source_criterion": "Has given written informed consent. Male or female outpatients aged at least 18 years and not more than 45 years. Has a diagnosis of major depressive disorder by Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV) criteria. Current HAMD-17 score = 20 and the duration of the index episode is greater than or equal to four weeks.", "candidate_expression": "((HAMD-17 Current score = 20) AND (Has given written informed consent.) AND (aged at least 18 years and not more than 45 years) AND (index episode greater than or equal to four weeks) AND (major depressive disorder Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV) criteria) AND (outpatients) AND ((Male) OR (female)))"}
{"candidate_id": "LLM04112", "doc_id": "NCT02092467_exc", "case_bucket": "or", "source_criterion": "Current or recent infection Clinically significant laboratory abnormalities Pregnancy", "candidate_expression": "((Clinically significant) AND (Pregnancy) AND (infection) AND (laboratory) AND (laboratory abnormalities) AND ((Current) OR (recent)))"}
{"candidate_id": "LLM04113", "doc_id": "NCT00440245_exc", "case_bucket": "or", "source_criterion": "asthma and COPD", "candidate_expression": "((COPD) AND (asthma))"}
{"candidate_id": "LLM04114", "doc_id": "NCT01794793_inc", "case_bucket": "other", "source_criterion": "Patient is currently participating in a Novartis Oncology sponsored study receiving pasireotide (LAR and/or s.c.) and has fulfilled all required assessments in the parent study (unless the study is being terminated) and patients that are benefiting from the study drug have no other alternatives Patient is currently benefiting from the treatment with pasireotide, as determined by the investigator Patient has demonstrated compliance, as assessed by the investigator, with the parent study requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures Written informed consent obtained prior to enrolling in roll-over study and receiving study medication • If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness", "candidate_expression": "((Patient is currently participating in a Novartis Oncology sponsored study receiving pasireotide (LAR and/or s.c.) and has fulfilled all required assessments in the parent study (unless the study is being terminated) and patients that are benefiting from the study drug have no other alternatives) AND (Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures) AND (Written informed consent obtained prior to enrolling in roll-over study and receiving study medication • If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness))"}
{"candidate_id": "LLM04115", "doc_id": "NCT00954850_exc", "case_bucket": "or", "source_criterion": "Malignancy and other significant medical conditions that will impact follow up within this program. Those less than 18 years of age. Concomitant interstitial lung disease, sarcoidosis, other significant lung disease. Those who have had a transplant. Significant travel with work. Unable to make appointments (every three to six months over 2 years). Those residing in another country or planned absence for more than one month.", "candidate_expression": "((Concomitant) AND (Unable to make appointments (every three to six months over 2 years).) AND (age) AND (less than 18 years) AND (significant) AND (transplant) AND ((Malignancy) OR (medical conditions)) AND ((interstitial lung disease) OR (lung disease) OR (sarcoidosis)))"}
{"candidate_id": "LLM04116", "doc_id": "NCT01491295_inc", "case_bucket": "or", "source_criterion": "HBsAg-positive for more than 6 months (HBeAg-positive or HBeAg-negative). Age > 20 y/o. Under lamivudine/adefovir treatment for more than 1 year due to previous lamivudine resistance (LAM-R), current HBV DNA is undetectable (< 20 IU/ml) during enrollment.", "candidate_expression": "((< 20 IU/ml) AND (> 20 y/o) AND (Age) AND (HBV DNA) AND (HBsAg) AND (LAM-R) AND (adefovir) AND (during enrollment) AND (enrollment) AND (lamivudine) AND (lamivudine resistance) AND (more than 1 year) AND (more than 6 months) AND (negative) AND (positive) AND (undetectable) AND ((HBeAg)))"}
{"candidate_id": "LLM04117", "doc_id": "NCT03008005_inc", "case_bucket": "other", "source_criterion": "Able to give informed consent Right-handed Age between 18-50 years old, Physically and neurologically healthy [confirmed by a comprehensive medical history] Current PTSD diagnosis", "candidate_expression": "((Able to give informed consent) AND (Age between 18-50 years old) AND (PTSD Current) AND (Right-handed) AND (comprehensive medical history) AND (healthy Physically) AND (neurologically healthy))"}
{"candidate_id": "LLM04118", "doc_id": "NCT02106598_inc", "case_bucket": "or", "source_criterion": "18 years of age or older Histologically confirmed diagnosis of melanoma, breast cancer or gynecologic cancer at MSKCC Have one of the following disease histories: Newly-diagnosed or recurrent (local, regional, metastatic) malignant melanoma or breast cancer patients in whom SLN mapping is indicated Residual clinically or radiographically evident tumor, including primary cutaneous and mucosal melanomas Prior radiation therapy, chemotherapy, or surgery in patients requiring flap reconstruction in the head and neck region. Newly diagnosed patients with previous excisional biopsy. OR Newly-diagnosed gynecologic cancer patients in whom SLN mapping and surgical excision is indicated OR Normal baseline cardiac function based upon pre-operative evaluation At the discretion of the operating surgeon, ANC>1000/mcl and platelets>100,000/mcl. At the discretion of the operating surgeon, Bilirubin level of < 2.0 mg/dl in the absence of a history of Gilbert's disease (or pattern consistent with Gilbert's). For melanoma patients, If patients have a history of malignancy other than melanoma, and other skin cancers in the past five years, their inclusion is up to the discretion of the physician. All patients of childbearing and child-creating age must be using an acceptable form of birth control Women who are pre-menopausal must have a negative serum pregnancy test", "candidate_expression": "((ANC >1000/mcl) AND (All patients of childbearing and child-creating age must be using an acceptable form of birth control) AND (At the discretion of the operating surgeon) AND (Bilirubin level < 2.0 mg/dl) AND (Histologically confirmed) AND (MSKCC Newly-diagnosed) AND (SLN mapping) AND (SLN mapping is indicated) AND (Women) AND (age 18 years or older) AND (baseline) AND (breast cancer) AND (cardiac function Normal) AND (chemotherapy) AND (clinically Residual) AND (excisional biopsy previous) AND (flap reconstruction head and neck region) AND (gynecologic cancer) AND (malignancy history) AND (malignant melanoma recurrent local regional metastatic) AND (melanoma) AND (mucosal melanomas Prior) AND (platelets >100,000/mcl) AND (pre-menopausal) AND (pre-operative evaluation pre-operative) AND (primary cutaneous) AND (radiation therapy) AND (radiographically evident) AND (requiring flap reconstruction) AND (serum pregnancy test negative) AND (skin cancers history in the past five years) AND (surgery) AND (surgical excision) AND (surgical excision is indicated) AND (tumor) AND (up to the discretion of the physician) AND NOT (Gilbert's disease history) AND NOT (melanoma))"}
{"candidate_id": "LLM04119", "doc_id": "NCT02257580_exc", "case_bucket": "or", "source_criterion": "Preoperative use of an anticoagulant (Plavix, warfarin, lovenox, etc.) History of hypersensitivity to EACA History of thromboembolic event (e.g., PE or DVT) History of renal insufficiency or failure Congenital or acquired coagulopathy as evidence by INR >1.4 or PTT > 1.4 times normal, or Platelets <150,000/mm3 on preoperative laboratory testing Use of hormone replacement therapy or hormonal contraceptive agents within days prior to surgery Use of acetylsalicylic acid (ASA), antiplatelet agents within 7 days prior to surgery Pregnant Breastfeeding Not received neuraxial anesthesia", "candidate_expression": "((<150,000/mm3) AND (> 1.4 times normal) AND (>1.4 times normal) AND (ASA) AND (Breastfeeding) AND (EACA) AND (Not received) AND (Pregnant) AND (Preoperative) AND (anticoagulant) AND (hypersensitivity) AND (neuraxial anesthesia) AND (preoperative laboratory testing) AND (surgery) AND (thromboembolic event) AND (within 7 days prior to surgery) AND (within days prior to surgery) AND ((DVT) OR (PE)) AND ((renal failure) OR (renal insufficiency)) AND ((Congenital) OR (acquired)) AND ((INR) OR (PTT)) AND ((Platelets) OR (coagulopathy)) AND ((hormonal contraceptive agents) OR (hormone replacement therapy)) AND ((Plavix) OR (lovenox) OR (warfarin)) AND ((acetylsalicylic acid) OR (antiplatelet agents)))"}
{"candidate_id": "LLM04120", "doc_id": "NCT00250640_inc", "case_bucket": "or", "source_criterion": "The treating physician has chosen Ventavis as a suitable long-term treatment for the patient Patient with primary pulmonary hypertension (i.e. Idiopathic Pulmonary Arterial Hypertension or Familial Pulmonary Arterial Hypertension) and classified as NYHA functional class III (NYHA = New York Heart Association) No prior treatment with Ventavis or other active treatments for primary pulmonary hypertension within 6 weeks of date of study inclusion (unless otherwise advised by Bayer Schering Pharma)", "candidate_expression": "((Familial Pulmonary Arterial Hypertension) AND (III) AND (Idiopathic Pulmonary Arterial Hypertension) AND (NYHA functional class) AND (No) AND (Ventavis) AND (for primary pulmonary hypertension) AND (long-term) AND (primary pulmonary hypertension) AND (treatment with Ventavis) AND (treatments) AND (within 6 weeks of date of study inclusion))"}
{"candidate_id": "LLM04121", "doc_id": "NCT03044093_inc", "case_bucket": "other", "source_criterion": "healthy no allergy known to these drugs second trimester abortion", "candidate_expression": "((abortion) AND (allergy) AND (healthy) AND (no) AND (second trimester) AND (these drugs))"}
{"candidate_id": "LLM04122", "doc_id": "NCT02966236_exc", "case_bucket": "or", "source_criterion": "Coronary artery disease - stent Severe chronic renal failure Congenital or acquired thrombophilia/thrombosis event Known or suspected allergy", "candidate_expression": "((allergy) AND (renal failure Severe chronic) AND ((Coronary artery disease) OR (stent)) AND ((Known) OR (suspected)) AND ((Congenital) OR (acquired)) AND ((thrombophilia) OR (thrombosis event)))"}
{"candidate_id": "LLM04123", "doc_id": "NCT01809041_exc", "case_bucket": "or", "source_criterion": "Patients are not expected to be alive for longer than 3 months. Mini-mental State Examination (MMSE) [18] score = 23. history of dementia, psychiatric illness or any diseases of central nervous system. current use of sedatives or antidepressant. alcoholism and drug dependence. patients previously included in this study (for patients who have second intra-abdominal surgery during the study period). difficult to follow up or patients with poor compliance. uncontrolled hypertension (> 180/100 mmHg)", "candidate_expression": "((Mini-mental State Examination (MMSE) = 23) AND (dementia) AND (diseases of central nervous system) AND (psychiatric illness) AND (uncontrolled hypertension > 180/100 mmHg) AND NOT (expected to be alive longer than 3 months) AND ((antidepressant) OR (sedatives)) AND ((alcoholism) OR (drug dependence)))"}
{"candidate_id": "LLM04124", "doc_id": "NCT02420015_inc", "case_bucket": "other", "source_criterion": "Currently smoke at least ten cigarettes a day Have been smoking for at least one year Meet criteria for schizophrenia, schizoaffective disorder, or another psychotic disorder based on structured clinical interview Can speak and write fluent conversational English Are between 18 and 70 years of age Are willing to make a smoking cessation attempt Score 26 or higher on the Montreal Cognitive Assessment", "candidate_expression": "((26 or higher) AND (Are willing to make a smoking cessation attempt) AND (Montreal Cognitive Assessment) AND (age) AND (at least one year) AND (at least ten cigarettes a day) AND (between 18 and 70 years) AND (psychotic disorder) AND (schizoaffective disorder) AND (schizophrenia) AND (smoke) AND (smoking))"}
{"candidate_id": "LLM04125", "doc_id": "NCT03376763_exc", "case_bucket": "or", "source_criterion": "Subject who showed medically significant adverse events or intolerance with aripiprazole during screening period or as prior experiences. Subjects with a current DSM-<U+2163>-TR or 5 diagnosis other than schizophrenia, including schizoaffective disorder, major depressive disorder, bipolar disorder, delirium, dementia, amnesia, Borderline, Paranoid, Histrionic, Schizotypal, Schizoid, Antisocial or other cognitive or personality disorders. Subjects with diseases of the central nervous system that may impact the assessment of the psychotic symptoms as per investigator's opinion. Subjects who have been treated with clozapine or long-acting injectable antipsychotic drugs within 3 months prior to the screening. Subjects who have been treated over maximum maintenance dose (as specified in each label) of oral antipsychotics at screening. (e.g. Aripiprazole>30mg/day, Olanzapine>20mg/day, Risperidone > 6mg/day, Quetiapine > 750mg/day) Subjects with a significant risk of violent behaviour or a significant risk of committing suicide based on history or investigator's judgment. Subjects had a history of seizures, neuroleptic malignant syndrome, clinically significant tardive dyskinesia, or other medical condition that would expose them to undue risk or interfere with study assessments. Significant history of drug abuse disorder (including alcohol, as defined in DSM-5 substance use disorder or in the opinion of the investigator) within the last 6 months prior to screening. Subjects participating another interventional clinical trial within 30 days prior to screening. Women who are pregnant, nursing, or who plan to become pregnant while in the trial. Subjects having any other clinically significant finding of the physical examination or laboratory value that make investigator consider that it would be inappropriate to participate in this study.", "candidate_expression": "((> 6mg/day) AND (> 750mg/day) AND (>20mg/day) AND (>30mg/day) AND (Antisocial disorders) AND (Aripiprazole) AND (Borderline disorders) AND (DSM- 5) AND (DSM-<U+2163>-TR) AND (Histrionic disorders) AND (Olanzapine) AND (Paranoid disorders) AND (Quetiapine) AND (Risperidone) AND (Schizoid disorders) AND (Schizotypal disorders) AND (Significant history of drug abuse disorder (including alcohol, as defined in DSM-5 substance use disorder or in the opinion of the investigator) within the last 6 months prior to screening.) AND (Subjects having any other clinically significant finding of the physical examination or laboratory value that make investigator consider that it would be inappropriate to participate in this study.) AND (Subjects participating another interventional clinical trial within 30 days prior to screening.) AND (Subjects with diseases of the central nervous system that may impact the assessment of the psychotic symptoms as per investigator's opinion.) AND (Women who are pregnant, nursing, or who plan to become pregnant while in the trial.) AND (adverse events) AND (amnesia) AND (aripiprazole) AND (as prior experiences) AND (at screening) AND (bipolar disorder) AND (clinically significant) AND (clozapine) AND (cognitive disorders) AND (committing suicide) AND (delirium) AND (dementia) AND (during screening period) AND (history) AND (intolerance) AND (long-acting injectable antipsychotic drugs) AND (major depressive disorder) AND (maximum maintenance dose) AND (medically significant) AND (neuroleptic malignant syndrome) AND (oral antipsychotics) AND (other) AND (other than) AND (personality disorders) AND (schizoaffective disorder) AND (schizophrenia) AND (seizures) AND (significant risk) AND (tardive dyskinesia) AND (the screening) AND (violent behaviour) AND (within 3 months prior to the screening))"}
```
