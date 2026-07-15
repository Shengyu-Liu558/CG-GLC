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
{"candidate_id": "LLM05201", "doc_id": "NCT03134378_exc", "case_bucket": "or", "source_criterion": "Patients refuse to follow the research Patient has had previous eradication therapy of Helicobacter pylori infection. The patient is pregnant or breastfeeding Patients have a history of allergy to one component of triple therapy regimen (proton pump inhibitor, penicillin, and / or macrolide) before. Patients are known to have impaired liver function, evidenced by ALT values within normal limits, and no previous liver disease. Patients were found to have arrhythmias or obtained QT wave elongation on electrocardiographic", "candidate_expression": "((ALT values) AND (Helicobacter pylori infection) AND (QT wave elongation) AND (allergy) AND (arrhythmias) AND (breastfeeding) AND (component of triple therapy regimen) AND (electrocardiographic) AND (eradication therapy) AND (history) AND (impaired) AND (liver disease) AND (liver function) AND (macrolide) AND (no) AND (penicillin) AND (pregnant) AND (previous) AND (proton pump inhibitor) AND (refuse to follow the research) AND (within normal limits))"}
{"candidate_id": "LLM05202", "doc_id": "NCT02552459_exc", "case_bucket": "or", "source_criterion": "long-term use of analgesics,sedatives or non steroidal anti-inflammatory drugs history. known for dexmedetomidine or other drugs allergy in this study. cannot communicate. preoperative systolic blood pressure <90 mmHg, or the heart rate <50/min.", "candidate_expression": "((<50/min) AND (<90 mmHg) AND (allergy) AND (cannot communicate) AND (history) AND (long-term use) AND (non steroidal anti-inflammatory drugs) AND (other) AND ((heart rate) OR (preoperative systolic blood pressure)) AND ((analgesics) OR (sedatives)) AND ((dexmedetomidine) OR (drugs)))"}
{"candidate_id": "LLM05203", "doc_id": "NCT02733159_inc", "case_bucket": "other", "source_criterion": "Histologically confirmed PD-L1 status defined NSCLC. Biopsy must be within 70 days of first treatment with pembrolizumab. ECOG performance status 2. Life expectancy > 12 weeks. Uni-dimensionally measurable disease according to Response Evaluation Criteria in Solid Tumours (RECIST) v1.1 Computerised Tomography (CT) scan of chest and abdomen within 28 days of starting pembrolizumab. Adequate haematological function: Platelet count ≥100 x 109 /L. Neutrophils ≥1.5 x 109/L. Haemoglobin ≥ 9g/dL. Adequate hepatic function: Serum bilirubin ≤1.5 x upper limit of normal (ULN). Serum transaminases ≤2.5 x ULN. Adequate renal function: Creatinine clearance <1.5 times ULN concurrent with creatinine clearance >50 ml/min. Provision of signed and dated, written informed consent prior to any study specific procedures, sampling and analyses.", "candidate_expression": "((Biopsy within 70 days of first treatment) AND (Computerised Tomography (CT) scan of chest and abdomen within 28 days of starting pembrolizumab) AND (Creatinine clearance <1.5 times ULN concurrent) AND (ECOG performance status 2) AND (Haemoglobin ≥ 9g/dL) AND (Life expectancy) AND (NSCLC PD-L1 status) AND (Neutrophils ≥1.5 x 109/L) AND (Platelet count ≥100 x 109 /L) AND (Provision of signed and dated, written informed consent prior to any study specific procedures, sampling and analyses.) AND (Response Evaluation Criteria in Solid Tumours (RECIST) v1.1 Uni-dimensionally measurable) AND (Serum bilirubin ≤1.5 x upper limit of normal (ULN)) AND (Serum transaminases ≤2.5 x ULN) AND (creatinine clearance concurrent >50 ml/min) AND (disease) AND (pembrolizumab) AND (renal function Adequate))"}
{"candidate_id": "LLM05204", "doc_id": "NCT03318393_inc", "case_bucket": "or", "source_criterion": "Age 1 day to less than 18 years Cared for in the pediatric intensive care unit or pediatric cardiac intensive care unit receiving venovenous or venoarterial ECMO", "candidate_expression": "((1 day to less than 18 years) AND (Age) AND (pediatric cardiac intensive care unit) AND (pediatric intensive care unit) AND (venoarterial ECMO) AND (venovenous ECMO))"}
{"candidate_id": "LLM05205", "doc_id": "NCT02256943_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05206", "doc_id": "NCT02394158_exc", "case_bucket": "or", "source_criterion": "Established pre-existing diabetes (including unrecognised diabetes defined as a fasting plasma glucose = 7.0mmol/L and/ or HbA1c = 48mmol/mol); Contraindications to metformin therapy (creatinine = 130µmol/L/ alanine transaminase = 2.0 x upper limit normal/ previous intolerance to metformin) Planned continued antenatal care/ delivery at centre not included in trial Planned fast for cultural/ religious reasons e.g. Ramadan", "candidate_expression": "((= 130µmol/L/) AND (= 2.0 x upper limit normal) AND (= 48mmol/mol)) AND (= 7.0mmol/L) AND (Contraindications) AND (HbA1c) AND (Planned continued antenatal care/ delivery at centre not included in trial) AND (alanine transaminase) AND (creatinine) AND (diabetes) AND (fasting plasma glucose) AND (intolerance) AND (metformin))"}
{"candidate_id": "LLM05207", "doc_id": "NCT02858180_inc", "case_bucket": "or", "source_criterion": "Chronic HCV Infection of Genotype 1, 4, 5, or 6 HCV RNA > 103 IU/mL at screening 18 years of age or older Diagnosis of chronic HCV infection, defined as positive HCV antibody or HCV RNA more than 6 months prior to screening OR an assessment of fibrosis F2 or greater prior to screening. NYHA Class III: Subjects with cardiac disease resulting in marked limitation of physical activity. They are comfortable at rest. Less than ordinary physical activity causes fatigue, palpitation, dyspnea, or anginal pain. NYHA Class IV: Patient with cardiac disease resulting in inability to carry on any physical activity without discomfort. Symptoms of cardiac insufficiency or of the anginal syndrome may be present even at rest. If any physical activity is undertaken, discomfort is increased. ejection fraction = 30% hospitalized for heart failure in last 12 months ILD criteria: diagnosis of interstitial lung disease with chronic supplemental oxygen requirement at rest and/or with exertion. Forced expiratory volume (FEV1)< 30% predicted OR any FEV1 with chronic supplemental oxygen requirement at rest and/or with exertion OR any FEV1 with chronic hypercapnia (baseline partial pressure of arterial carbon dioxide [PaCO2] > 45)", "candidate_expression": "((< 30% predicted) AND (= 30%) AND (> 103 IU/mL) AND (> 45) AND (Chronic HCV Infection) AND (Class III) AND (Class IV) AND (F2 or greater) AND (FEV1) AND (Forced expiratory volume) AND (Genotype 1) AND (Genotype 4) AND (Genotype 5) AND (Genotype 6) AND (HCV RNA) AND (HCV antibody) AND (ILD criteria) AND (NYHA) AND (PaCO2) AND (age) AND (assessment of fibrosis) AND (at rest) AND (at screening) AND (chronic HCV infection) AND (chronic hypercapnia) AND (chronic supplemental oxygen requirement) AND (ejection fraction) AND (heart failure) AND (hospitalized) AND (in last 12 months) AND (interstitial lung disease) AND (more than 6 months prior to screening) AND (older 18 years) AND (partial pressure of arterial carbon dioxide) AND (positive) AND (prior to screening) AND (screening) AND (with exertion))"}
{"candidate_id": "LLM05208", "doc_id": "NCT03476850_exc", "case_bucket": "or", "source_criterion": "Chronic pain or narcotic usage during the preceding 30 days Infection at or near the intended needle insertion site Complex or altered abdominal wall anatomy Weight <45kg", "candidate_expression": "((Infection intended needle insertion site) AND (Weight <45kg) AND ((Chronic pain) OR (narcotic)) AND ((Complex abdominal wall anatomy) OR (altered abdominal wall anatomy)))"}
{"candidate_id": "LLM05209", "doc_id": "NCT02515773_inc", "case_bucket": "or", "source_criterion": "Inpatient or outpatient age 8-19 years inclusive; participants must live with a parent, guardian, or caregiver; Fluent in English; Diagnosed or told by a clinician that they have any of the following bipolar spectrum disorders (BSD): bipolar I, bipolar II, unspecified bipolar and related disorders, Disruptive Mood Dysregulation Disorder (DMDD), cyclothymic disorder, other specified bipolar and related disorders, as well as mood disorder not otherwise specified (if diagnosed in the past as per DSM-IV); Body mass index >85%ile for age and sex by standard growth charts; Received a new or ongoing prescription for at least one SGA (i.e., olanzapine, clozapine, risperidone, quetiapine, aripiprazole, ziprasidone, iloperidone, lurasidone, paliperidone, brexpiprazole or cariprazine) that is not prescribed as a PRN medication;", "candidate_expression": "((8-19 years) AND (>85%ile) AND (BSD) AND (Body mass index) AND (DMDD) AND (Disruptive Mood Dysregulation Disorder) AND (Inpatient) AND (SGA) AND (age) AND (aripiprazole) AND (at least one) AND (bipolar I) AND (bipolar II) AND (bipolar spectrum disorders) AND (brexpiprazole) AND (cariprazine) AND (clozapine) AND (cyclothymic disorder) AND (iloperidone) AND (lurasidone) AND (mood disorder not otherwise specified) AND (olanzapine) AND (other specified bipolar and related disorders) AND (outpatient) AND (paliperidone) AND (quetiapine) AND (risperidone) AND (unspecified bipolar and related disorders) AND (ziprasidone))"}
{"candidate_id": "LLM05210", "doc_id": "NCT02334631_exc", "case_bucket": "or", "source_criterion": "Patients with a contraindication to VCE (small bowel strictures, oropharyngeal dysphagia, pregnancy, patients who are not surgical candidates) Endoscopic insertion of video capsule endoscope Inpatient procedures for active GI bleeding Patients with fluid restriction or who are unable to drink up to 900 ml of fluid within 10 minutes prior to the VCE", "candidate_expression": "((Endoscopic insertion) AND (GI bleeding active) AND (Inpatient procedures) AND (VCE) AND (contraindication) AND (fluid restriction) AND (oropharyngeal dysphagia) AND (pregnancy) AND (small bowel strictures) AND (unable to drink) AND (video capsule endoscope) AND NOT (surgical candidates))"}
{"candidate_id": "LLM05211", "doc_id": "NCT02443844_inc", "case_bucket": "other", "source_criterion": "Patients who have non muscle invasive bladder cancer male patients patients between 40-80 years old", "candidate_expression": "((between 40-80 years) AND (male) AND (non muscle invasive bladder cancer) AND (old))"}
{"candidate_id": "LLM05212", "doc_id": "NCT02827487_exc", "case_bucket": "other", "source_criterion": "Previous vaginal delivery. Submucous myoma. Uterine anomalies. Undiagnosed vaginal bleeding. Pelvic inflammatory disease.", "candidate_expression": "((Pelvic inflammatory disease) AND (Submucous myoma) AND (Uterine anomalies) AND (vaginal bleeding Undiagnosed) AND (vaginal delivery Previous))"}
{"candidate_id": "LLM05213", "doc_id": "NCT02918409_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05214", "doc_id": "NCT01314898_inc", "case_bucket": "or", "source_criterion": "Male and/or female healthy volunteers, age 18 to 55 years. Females must be of non-childbearing potential. Body Mass Index (BMI) of 17.5 to 30.5 kg/m2; and a total body weight >50 kg (110 lbs). Subjects who are willing and able to comply with scheduled visits, treatment plan, laboratory tests, diet restrictions and other trial procedures.", "candidate_expression": "((Body Mass Index (BMI) 17.5 to 30.5 kg/m2) AND (Females) AND (Male) AND (Subjects who are willing and able to comply with scheduled visits, treatment plan, laboratory tests, diet restrictions and other trial procedures.) AND (age 18 to 55 years) AND (female) AND (healthy) AND (total body weight >50 kg (110 lbs)) AND NOT (childbearing potential))"}
{"candidate_id": "LLM05215", "doc_id": "NCT02689089_inc", "case_bucket": "or", "source_criterion": "Males or non-pregnant, non-nursing females between the ages of 2-65 years LTBI diagnosis as per Canadian TB Standards using either the Tuberculin Skin Test (TST) or the Interferon Gamma Release Assay (IGRA) Children 2-5 years with negative TSTs who have been in close contact with a case of active TB disease recently Able and willing to provide fully informed consent or parent/guardian able to provide consent", "candidate_expression": "((Able and willing to provide fully informed consent or parent/guardian able to provide consent) AND (Children) AND (IGRA) AND (LTBI) AND (TST) AND (TSTs negative) AND (ages 2-65 years) AND (non-pregnant, non-nursing) AND (years 2-5) AND ((Males) OR (females)) AND ((Interferon Gamma Release Assay) OR (Tuberculin Skin Test)))"}
{"candidate_id": "LLM05216", "doc_id": "NCT03228017_exc", "case_bucket": "or", "source_criterion": "Unable to speak Spanish or English Active smoking (within the past year) Autoimmune, rheumatologic or inflammatory disease which are not psoriasis or psoriatic arthritis Known active cancer receiving treatment Pregnancy Anemia (hemoglobin < 9 mg/dl) or thrombocytopenia (Platelet count <75), or thrombocytosis (Platelet count >600) A history of severe bleeding or bleeding disorders Current medication use which interact with either aspirin or atorvastatin Chronic kidney disease (CrCl < 30ml/min) Congestive heart failure Currently taking aspirin or a statin. NSAID use within the past 48 hours", "candidate_expression": "((Anemia) AND (Chronic kidney disease) AND (Congestive heart failure) AND (CrCl < 30ml/min) AND (NSAID within the past 48 hours) AND (Platelet count <75) AND (Platelet count >600) AND (Pregnancy) AND (aspirin) AND (atorvastatin) AND (bleeding disorders) AND (bleeding severe) AND (cancer active) AND (disease Autoimmune) AND (disease rheumatologic) AND (hemoglobin < 9 mg/dl) AND (inflammatory disease) AND (interact) AND (medication Current) AND (psoriasis) AND (psoriatic arthritis) AND (smoking Active within the past year) AND (statin) AND (thrombocytopenia) AND (thrombocytosis) AND (treatment))"}
{"candidate_id": "LLM05217", "doc_id": "NCT01715584_inc", "case_bucket": "other", "source_criterion": "age over 40 composite head and neck tumor resection treated hypertension hypertension medications taken on morning of surgery (except diuretics)", "candidate_expression": "((age over 40) AND (composite head and neck tumor resection) AND (hypertension medications on morning of surgery) AND (hypertension treated) AND NOT (diuretics))"}
{"candidate_id": "LLM05218", "doc_id": "NCT02773173_exc", "case_bucket": "or", "source_criterion": "Emergency surgery Pregnancy or lactation Immune disorders Kidney or liver disease or advanced-stage cardiopulmonary Patient refusal to participate in the study Patients under 18 years or inability to consent Associated neuromuscular disorders, contraindication for the use of rocuronium/ sugammadex, allergy or hypersensitivity to rocuronium / sugammadex", "candidate_expression": "((Emergency surgery) AND (Immune disorders) AND (Patient refusal to participate in the study) AND (contraindication) AND (inability to consent) AND (neuromuscular disorders) AND (under 18) AND ((inability to consent) OR (years)) AND ((rocuronium) OR (sugammadex)) AND ((allergy) OR (hypersensitivity)) AND ((Pregnancy) OR (lactation)) AND ((Kidney disease) OR (advanced-stage cardiopulmonary) OR (liver disease)))"}
{"candidate_id": "LLM05219", "doc_id": "NCT02573168_inc", "case_bucket": "or", "source_criterion": "18 years of age or older; Suffer from schizophrenia/schizoaffective disorder meeting Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, Text Revision (DSM-IV-TR) criteria; Have a total baseline score on the Brief Psychiatric Rating Scale (BPRS) = 45; Be capable and willing to provide written informed consent to participate in this study; Agree to abide by the study protocol and its restrictions and be able to complete all aspects of the study, including all visits and tests", "candidate_expression": "((18 years or older) AND (= 45) AND (Agree to abide by the study protocol and its restrictions and be able to complete all aspects of the study, including all visits and tests) AND (BPRS) AND (Be capable and willing to provide written informed consent to participate in this study) AND (Brief Psychiatric Rating Scale) AND (DSM-IV-TR) AND (Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, Text Revision) AND (age) AND ((schizoaffective disorder) OR (schizophrenia)))"}
{"candidate_id": "LLM05220", "doc_id": "NCT03140488_inc", "case_bucket": "other", "source_criterion": "Singleton pregnancy = 37 weeks gestation Patient presented for induction of labor who is determined to be a candidate for oxytocin Cephalic presentation Reassuring fetal health assessment (no abnormal findings in fetal assessment, see below) Meeting one of the following BMI category:", "candidate_expression": "((= 37 weeks) AND (Cephalic presentation) AND (Reassuring) AND (Singleton pregnancy) AND (abnormal findings) AND (candidate for oxytocin) AND (fetal assessment) AND (fetal health assessment) AND (gestation) AND (induction of labor) AND (no) AND (oxytocin) AND (presented for))"}
{"candidate_id": "LLM05221", "doc_id": "NCT02974686_inc", "case_bucket": "or", "source_criterion": "Kidney transplant recipients at Washington University/Barnes-Jewish Hospital Experiencing GI toxicity from MPA as determined by the treating physician within 12 months post-renal transplant On standard immunosuppression with tacrolimus and prednisone", "candidate_expression": "((GI toxicity) AND (Kidney transplant) AND (MPA) AND (Washington University/Barnes-Jewish Hospital) AND (prednison) AND (standard immunosuppression) AND (tacrolimus))"}
{"candidate_id": "LLM05222", "doc_id": "NCT01768195_exc", "case_bucket": "or", "source_criterion": "younger than 18 years old HBsAg negative at baseline pregnant or lactating women", "candidate_expression": "((HBsAg negative) AND (at baseline) AND (old) AND (women) AND (younger than 18 years) AND ((lactating) OR (pregnant)))"}
{"candidate_id": "LLM05223", "doc_id": "NCT02035800_inc", "case_bucket": "other", "source_criterion": "Patients aged of 18 and over, Satisfying the 1987 American College of Rheumatology (ACR) criteria for RA Receiving a prescription of Adalimumab 40 mg subcutaneous every two weeks.", "candidate_expression": "((18 and over) AND (1987 American College of Rheumatology (ACR) criteria) AND (40 mg every two weeks) AND (Adalimumab) AND (RA) AND (aged) AND (subcutaneous))"}
{"candidate_id": "LLM05224", "doc_id": "NCT00426751_inc", "case_bucket": "or", "source_criterion": "Women must be postmenopausal (i.e.12 months without menstrual period), or surgically sterile, i.e. women of child bearing potential are not allowed to be included into the study. In cases of doubt a pregnancy test should be performed. (NB -post menopausal women currently receiving hormone replacement are permissible) Acute myocardial infarction < 12 h defined as: 1. Angina or equivalent symptoms > 20 min and 2. ST elevation in 2 contiguous ECG leads (= 2 mm precordial lead, = 1 mm limb lead). This ECG recording serves as baseline ECG, i.e. ECG I. Planned primary percutaneous coronary intervention The subject has given written informed, dated consent to participate in the study", "candidate_expression": "((1 mm) AND (12 months) AND (2) AND (2 mm) AND (< 12 h) AND (> 20 min) AND (Acute myocardial infarction) AND (Planned) AND (ST elevation) AND (Women) AND (child bearing potential) AND (contiguous ECG leads) AND (doubt) AND (given written informed consent) AND (limb lead) AND (menstrual period) AND (not) AND (postmenopausal) AND (precordial lead) AND (pregnancy test) AND (primary percutaneous coronary intervention) AND (surgically sterile) AND (without) AND (women) AND ((Angina) OR (Angina symptoms)))"}
{"candidate_id": "LLM05225", "doc_id": "NCT02692651_exc", "case_bucket": "or", "source_criterion": "Patients with severe-complicated disease that would compromise oral therapy (hypotenstion or shock, ileus or bowel obstruction, megacolon). Patients with an allergy to oral vancomycin or fidaxomicin. Patients anticipated to receive metronidazole after enrollment. Patients who already received oral vancomycin or metronidazole (either oral or intravenous) for > 24 hours within the preceding 72 hours at the time of enrollment. Patients anticipated to receive adjunctive C. difficile therapy (rifaxamin, nitazoxanide, tigecycline) after enrollment.", "candidate_expression": "((> 24 hours) AND (C. difficile therapy) AND (allergy) AND (anticipated) AND (enrollment) AND (metronidazole) AND (oral) AND (preceding 72 hours at the time of enrollment.) AND ((metronidazole) OR (vancomycin)) AND ((nitazoxanide) OR (rifaxamin) OR (tigecycline)) AND ((bowel obstruction) OR (hypotenstion) OR (ileus) OR (megacolon) OR (shock)) AND ((fidaxomicin) OR (vancomycin)))"}
```
