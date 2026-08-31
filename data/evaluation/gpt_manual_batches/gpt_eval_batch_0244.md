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
{"candidate_id": "LLM06076", "doc_id": "NCT02322203_inc", "case_bucket": "other", "source_criterion": "Males and females who are at least 18 years of age at time of enrollment. Subject understands the investigational nature of the study and provides written, informed consent.", "candidate_expression": "((Males) AND (Subject understands the investigational nature of the study and provides written, informed consent.) AND (age at time of enrollment) AND (females at least 18 years))"}
{"candidate_id": "LLM06077", "doc_id": "NCT01313676_inc", "case_bucket": "or", "source_criterion": "Type of subject: outpatient. Informed consent: Subjects must give their signed and dated written informed consent to participate. Gender: Male or female. Female subjects must be post-menopausal or using a highly effective method for avoidance of pregnancy. The decision to include or exclude women of childbearing potential may be made at the discretion of the investigator in accordance with local practice in relation to adequate contraception. Age: >=40 and <=80 years of age at Screening (Visit 1). Tobacco use: Subjects with a current or prior history of >=10 pack-years of cigarette smoking at screening (Visit 1). Previous smokers are defined as those who have stopped smoking for at least 6 months prior to Visit 1. Airflow Obstruction: Subjects with a measured post-albuterol/salbutamol forced expiratory volume in 1 second (FEV1)/(forced vital capacity)FVC ratio of <=0.70 at Screening (Visit 1). Subjects with a measured post-albuterol/salbutamol FEV1 >=50 and <=70% of predicted normal values calculated using NHANES III reference equations [Hankinson, 1999; Hankinson, 2010] at Screening (Visit 1). Post-bronchodilator spirometry will be performed approximately 15 minutes after the subject has self-administered 4 inhalations (i.e., total 400mcg) of albuterol/salbutamol via a metered dose inhaler (MDI )with a valved-holding chamber. The FEV1/FVC ratio and FEV1 percent predicted values will be calculated. Symptoms of COPD: Subjects must score 2 or higher on the modified Medical Research Council Dyspnea scale (Visit 1) Cardiovascular disease: For patients >= 40 years of age: any one of the following: Established (i.e. by clinical signs or imaging studies) coronary artery disease (CAD) Established (i.e. by clinical signs or imaging studies) peripheral vascular disease (PVD) Previous stroke Previous MI Diabetes mellitus with target organ disease OR For patients >=60 years of age: any 2 of the following: Being treated for hypercholesterolemia Being treated for hypertension Being treated for diabetes mellitus Being treated for peripheral vascular disease", "candidate_expression": "((4) AND (400mcg) AND (<=0.70) AND (>= 40 years) AND (>=10 pack-years) AND (>=40 and <=80 years) AND (>=50 and <=70% of predicted normal values) AND (>=60 years) AND (Established) AND (FEV1) AND (Female subjects must be post-menopausal or using a highly effective method for avoidance of pregnancy. The decision to include or exclude women of childbearing potential may be made at the discretion of the investigator in accordance with local practice in relation to adequate contraception.) AND (Informed consent: Subjects must give their signed and dated written informed consent to participate.) AND (Post-bronchodilator) AND (Previous) AND (Previous smokers) AND (Screening) AND (Symptoms of COPD) AND (Visit 1) AND (age) AND (albuterol) AND (albuterol/salbutamol) AND (approximately 15 minutes after) AND (at Screening) AND (at screening) AND (bronchodilator) AND (cigarette smoking) AND (diabetes mellitus) AND (for at least 6 months prior to Visit 1) AND (forced expiratory volume in 1 second (FEV1)/(forced vital capacity)FVC ratio) AND (history) AND (hypercholesterolemia) AND (hypertension) AND (inhalations) AND (metered dose inhaler (MDI )) AND (modified Medical Research Council Dyspnea scale) AND (outpatient) AND (peripheral vascular disease) AND (post-albuterol/salbutamol) AND (salbutamol) AND (score 2 or higher) AND (self-administered) AND (spirometry) AND (stopped smoking) AND (target organ disease) AND (using NHANES III reference equations) AND (with a valved-holding chamber) AND ((current) OR (prior)) AND ((Male) OR (female)) AND ((Age) OR (age)) AND ((Diabetes mellitus) OR (MI) OR (coronary artery disease (CAD)) OR (peripheral vascular disease (PVD)) OR (stroke)) AND ((clinical signs) OR (imaging studies)) AND ((treated for diabetes mellitus) OR (treated for hypercholesterolemia) OR (treated for hypertension) OR (treated for peripheral vascular disease)))"}
{"candidate_id": "LLM06078", "doc_id": "NCT02380118_inc", "case_bucket": "other", "source_criterion": "Accident & Emergency Department patients, requiring parenteral drug sedation (as determined by an emergency clinician) will be enrolled.", "candidate_expression": "((Accident & Emergency Department) AND (parenteral drug sedation requiring))"}
{"candidate_id": "LLM06079", "doc_id": "NCT00730301_inc", "case_bucket": "or", "source_criterion": "Patient diagnosed by HRCT Core Lab with eligible heterogeneous disease distribution and at least one complete oblique fissure. Age from 40 to 75 years BMI < 32 kg/m2 FEV1 < 40% of predicted value, FEV1/FVC < 70% TLC > 120% predicted, RV > 150% predicted. Stable with < 20 mg prednisone (or equivalent) qd PaCO2 < 50mm Hg PaO2 > 45 mm Hg on room air 6-min walk of > 50m (without rehabilitation) or > 100m (with rehabilitation) Nonsmoking for 4 months prior to initial interview and throughout screening The patient agrees to all protocol required follow-up intervals. The patient has no child bearing potential The patient is willing and able to complete protocol required baseline assessments and procedures", "candidate_expression": "((6-min walk > 50m > 100m) AND (Age from 40 to 75 years) AND (BMI < 32 kg/m2) AND (FEV1 < 40% of predicted value) AND (FEV1/FVC < 70%) AND (HRCT Core Lab) AND (Nonsmoking for 4 months prior to initial interview throughout screening initial interview) AND (PaCO2 < 50mm Hg) AND (PaO2 > 45 mm Hg) AND (RV > 150% predicted) AND (Stable) AND (TLC > 120% predicted) AND (agrees to all protocol required follow-up intervals) AND (baseline assessments) AND (baseline procedures) AND (complete oblique fissure at least one) AND (follow-up intervals) AND (heterogeneous disease distribution) AND (prednisone < 20 mg qd) AND (willing and able to complete protocol) AND NOT (child bearing potential))"}
{"candidate_id": "LLM06080", "doc_id": "NCT03173092_exc", "case_bucket": "or", "source_criterion": "Failure to have fully recovered (that is, less than or equal to [<=] Grade 1 toxicity) from the reversible effects of prior chemotherapy. Major surgery within 14 days before enrollment. Radiotherapy within 14 days before enrollment (if the involved field is small, 7 days will be considered a sufficient interval between treatment and administration of the ixazomib.) Central nervous system involvement. Infection requiring systemic antibiotic therapy or other serious infection within 14 days before study enrollment. Evidence of current uncontrolled cardiovascular conditions, including uncontrolled hypertension, uncontrolled cardiac arrhythmias, symptomatic congestive heart failure, unstable angina, or myocardial infarction within the past 6 months. Systemic treatment, within 14 days before the first dose of ixazomib, with strong cytochrome P450 3A (CYP3A) inducers (rifampin, rifapentine, rifabutin, carbamazepine, phenytoin, phenobarbital), or use of Ginkgo biloba or St. John's wort. Ongoing or active systemic infection, active hepatitis B or C virus infection, or known human immunodeficiency virus positive. Diagnosed or treated for another malignancy within 2 years before study enrollment or previously diagnosed with another malignancy and have any evidence of residual disease. Participants with non-melanoma skin cancer or carcinoma in situ of any type are not excluded if they have undergone complete resection. Has greater than or equal to (>=) Grade 2 peripheral neuropathy, or Grade 1 with pain on clinical examination during the screening period. PD on first-line therapy. Participation in other interventional clinical trials, including those with other investigational agents not included in this trial, within 30 days of the start of this trial and throughout the duration of this trial. Non-interventional trials (that is, observational trials) are permitted at any time point.", "candidate_expression": "((7 days) AND (C virus infection) AND (Central nervous system involvement) AND (Failure) AND (Ginkgo biloba) AND (Grade 1) AND (Infection) AND (Major surgery) AND (Ongoing) AND (PD) AND (Participation in other interventional clinical trials) AND (Radiotherapy) AND (St. John's wort) AND (Systemic treatment) AND (active) AND (another) AND (any evidence of) AND (any type) AND (carbamazepine) AND (carcinoma in situ) AND (cardiac arrhythmias) AND (cardiovascular conditions) AND (chemotherapy) AND (complete resection) AND (congestive heart failure) AND (current) AND (first-line therapy) AND (fully recovered) AND (greater than or equal to (>=) Grade 2) AND (hepatitis B virus infection) AND (human immunodeficiency virus) AND (hypertension) AND (infection) AND (involved field is small) AND (ixazomib) AND (less than or equal to [<=] Grade 1) AND (malignancy) AND (myocardial infarction) AND (non-melanoma skin cancer) AND (not excluded) AND (other) AND (pain) AND (peripheral neuropathy) AND (phenobarbital) AND (phenytoin) AND (positive) AND (previously) AND (residual disease) AND (rifabutin) AND (rifampin) AND (rifapentine) AND (serious) AND (strong cytochrome P450 3A (CYP3A) inducers) AND (symptomatic) AND (systemic antibiotic therapy) AND (systemic infection) AND (the duration of this trial) AND (the first dose of ixazomib) AND (the start of this trial) AND (throughout the duration of this trial) AND (toxicity) AND (uncontrolled) AND (unstable angina) AND (within 14 days before enrollment) AND (within 14 days before study enrollment) AND (within 14 days before the first dose of ixazomib) AND (within 2 years before study enrollment) AND (within 30 days of the start of this trial) AND (within the past 6 months))"}
{"candidate_id": "LLM06081", "doc_id": "NCT02164734_exc", "case_bucket": "or", "source_criterion": "Weight < 800 g; Airway anomalies; Pulmonary air leaks; Craniofacial or cardiothoracic malformations", "candidate_expression": "((< 800 g) AND (Airway anomalies) AND (Pulmonary air leaks) AND (Weight) AND ((Craniofacial malformations) OR (cardiothoracic malformations)))"}
{"candidate_id": "LLM06082", "doc_id": "NCT02733159_inc", "case_bucket": "other", "source_criterion": "Histologically confirmed PD-L1 status defined NSCLC. Biopsy must be within 70 days of first treatment with pembrolizumab. ECOG performance status 2. Life expectancy > 12 weeks. Uni-dimensionally measurable disease according to Response Evaluation Criteria in Solid Tumours (RECIST) v1.1 Computerised Tomography (CT) scan of chest and abdomen within 28 days of starting pembrolizumab. Adequate haematological function: Platelet count ≥100 x 109 /L. Neutrophils ≥1.5 x 109/L. Haemoglobin ≥ 9g/dL. Adequate hepatic function: Serum bilirubin ≤1.5 x upper limit of normal (ULN). Serum transaminases ≤2.5 x ULN. Adequate renal function: Creatinine clearance <1.5 times ULN concurrent with creatinine clearance >50 ml/min. Provision of signed and dated, written informed consent prior to any study specific procedures, sampling and analyses.", "candidate_expression": "((2) AND (<1.5 times ULN) AND (>50 ml/min) AND (Adequate) AND (Biopsy) AND (Computerised Tomography (CT) scan of chest and abdomen) AND (Creatinine clearance) AND (ECOG performance status) AND (Haemoglobin) AND (Life expectancy) AND (NSCLC) AND (Neutrophils) AND (PD-L1 status) AND (Platelet count) AND (Provision of signed and dated, written informed consent prior to any study specific procedures, sampling and analyses.) AND (Response Evaluation Criteria in Solid Tumours (RECIST) v1.1) AND (Serum bilirubin) AND (Serum transaminases) AND (Uni-dimensionally measurable) AND (concurrent) AND (creatinine clearance) AND (disease) AND (first treatment with pembrolizumab) AND (pembrolizumab) AND (renal function) AND (starting pembrolizumab) AND (within 28 days of starting pembrolizumab) AND (within 70 days of first treatment) AND (≤1.5 x upper limit of normal (ULN)) AND (≤2.5 x ULN) AND (≥ 9g/dL) AND (≥1.5 x 109/L) AND (≥100 x 109 /L))"}
{"candidate_id": "LLM06083", "doc_id": "NCT02908919_inc", "case_bucket": "or", "source_criterion": "Subjects referred to diagnostic or therapeutic colonoscopy.", "candidate_expression": "((colonoscopy) AND (diagnostic) AND (therapeutic))"}
{"candidate_id": "LLM06084", "doc_id": "NCT03249311_exc", "case_bucket": "or", "source_criterion": "Lifetime personal history of diagnosis of major depressive disorder according to the DSM-V (American Psychiatric Association, 2013) using the Structured Clinical Interview for DSM-V Axis I Disorders, Research Version, Non-patient Edition (SCID-5-RV for DSM-V; First et al., 2015) A history of suicidal ideation and behaviour, including self-harm and/or harm to others. A history of substance abuse and/or dependence. A positive drug screen for illicit drugs Substantial alcohol use Current use of Monoamine Oxidase Inhibitors (MAOIs), including the antibiotic linezolid and the thiazine dye methylthioninium chloride (methylene blue) Current use of serotonin-precursors (such as L-tryptophan, oxitriptan) Current use of serotonergic drugs (triptans, certain tricyclic antidepressants, lithium, tramadol, St. John's Wort) Concomitant use of NSAIDS, ASA, and other anticoagulants. Current use of Thioridazine Current use of CYP1A2 Inhibitors Current use of Triptans (5HT1 Agonists) Blood pressure greater than 140/90 and/or a pulse rate greater than 90 bpm Recent history of myocardial infarction, cerebrovascular accident, cardiac arrhythmias, or unstable heart disease. Evidence of significant physical illness contraindicating the use of levomilnacipran and duloxetine found on the physical exam or in the laboratory data obtained during the first week of the study Current use of medication that may affect voiding (ie- anticholinergics) History of obstructive urinary disorders and dysuria, prostatic hypertrophy, prostatitis, and other lower urinary tract obstructive disorders. History of Stevens-Johnson Syndrome and Erythema multiforme. Diabetes Type I and II Fructose intolerance, glucose-galactose malabsorption or sucrose-isomaltase insufficiency. Hepatic Impairment Uncontrolled narrow-angle glaucoma Severe renal impairment History of seizure disorder Anatomically narrow ocular angles. Osteoporosis or major risk for bone fractures.", "candidate_expression": "((5HT1 Agonists) AND (Anatomically narrow ocular angles) AND (Blood pressure) AND (CYP1A2 Inhibitors) AND (Concomitant) AND (Current) AND (DSM-V) AND (Hepatic Impairment) AND (History) AND (Monoamine Oxidase Inhibitors (MAOIs)) AND (Recent) AND (Severe) AND (Structured Clinical Interview for DSM-V Axis I Disorders, Research Version, Non-patient Edition) AND (Substantial alcohol use) AND (Thioridazine) AND (Triptans) AND (Uncontrolled) AND (affect voiding) AND (anticholinergics) AND (contraindicating) AND (drug screen for illicit drugs) AND (during the first week of the study) AND (greater than 140/90) AND (greater than 90 bpm) AND (history) AND (major depressive disorder) AND (major risk) AND (medication) AND (methylene blue) AND (methylthioninium chloride) AND (narrow-angle glaucoma) AND (other) AND (physical illness) AND (positive) AND (pulse rate) AND (renal impairment) AND (seizure disorder) AND (serotonergic drugs) AND (serotonin-precursors) AND ((antibiotic linezolid) OR (thiazine dye)) AND ((L-tryptophan) OR (oxitriptan)) AND ((St. John's Wort) OR (lithium) OR (tramadol) OR (tricyclic antidepressant) OR (triptans)) AND ((ASA) OR (NSAIDS) OR (anticoagulants)) AND ((cardiac arrhythmias) OR (cerebrovascular accident) OR (myocardial infarction) OR (unstable heart disease)) AND ((duloxetine) OR (levomilnacipran)) AND ((laboratory) OR (physical exam)) AND ((dysuria) OR (lower urinary tract obstructive disorders) OR (obstructive urinary disorders) OR (prostatic hypertrophy) OR (prostatitis)) AND ((harm to others) OR (self-harm) OR (suicidal behaviour) OR (suicidal ideation)) AND ((Erythema multiforme) OR (Stevens-Johnson Syndrome)) AND ((Diabetes Type I) OR (Diabetes Type II)) AND ((Fructose intolerance) OR (glucose-galactose malabsorption) OR (sucrose-isomaltase insufficiency)) AND ((substance abuse) OR (substance dependence)) AND ((Osteoporosis) OR (bone fractures)))"}
{"candidate_id": "LLM06085", "doc_id": "NCT02101554_exc", "case_bucket": "or", "source_criterion": "Columbia-Suicide Severity Rating Scale (C-SSRS) for suicidal ideation and behavior in past year. Hypersensitivity to morphine, naltrexone. A life expectancy (assessed by investigator) of less than 6 months or is no longer capable of taking medication orally. Undergone surgery within 3 days prior to the first day of dosing.", "candidate_expression": "((C-SSRS) AND (Columbia-Suicide Severity Rating Scale) AND (Hypersensitivity) AND (first day of dosing) AND (in past year) AND (less than 6 months) AND (life expectancy) AND (morphine) AND (naltrexone) AND (suicidal behavior) AND (suicidal ideation) AND (surgery) AND (within 3 days prior to the first day of dosing))"}
{"candidate_id": "LLM06086", "doc_id": "NCT03138577_exc", "case_bucket": "or", "source_criterion": "Patient refusal for supraclavicular block Inability to give informed consent Allergy to local anesthetics Hemidiaphragmatic dysfunction, suspected or known PNP Neuromuscular disease Obstructive or restrictive pulmonary disease Medical or anatomic contraindication to supraclavicular blockade as judged by clinician Pregnancy", "candidate_expression": "((Allergy) AND (Inability to give informed consent) AND (Neuromuscular disease) AND (Patient refusal) AND (Pregnancy) AND (contraindication) AND (local anesthetics) AND (supraclavicular block) AND (supraclavicular blockade) AND ((Obstructive pulmonary disease) OR (restrictive pulmonary disease)) AND ((Medical) OR (anatomic)) AND ((Hemidiaphragmatic dysfunction) OR (PNP)) AND ((known) OR (suspected)))"}
{"candidate_id": "LLM06087", "doc_id": "NCT02570347_exc", "case_bucket": "or", "source_criterion": "Upper limb bites Multiple (> 1) bites Wound manipulation Extensive local necrosis or blebs Seriously-ill patients with hypotension/capillary leak/life threatening bleeding. Suspected cobra bite, OR Pregnant/breast-feeding women", "candidate_expression": "((Seriously-ill) AND (Wound manipulation) AND (bites Multiple > 1) AND (bites Upper limb) AND (cobra bite Suspected) AND (women) AND ((bleeding life threatening) OR (capillary leak) OR (hypotension)) AND ((Pregnant) OR (breast-feeding)) AND ((Extensive local blebs) OR (Extensive local necrosis)))"}
{"candidate_id": "LLM06088", "doc_id": "NCT02983214_inc", "case_bucket": "other", "source_criterion": "Patients aged =50 years with DM2 and symptomatic PAD diagnosed clinically (according to Fontaine criteria, stage IIa or IIb and III) and by measuring the <U+0391><U+0392><U+0399>.", "candidate_expression": "((=50 years) AND (DM2) AND (Fontaine criteria) AND (PAD) AND (aged) AND (stage IIa or IIb and III) AND (symptomatic))"}
{"candidate_id": "LLM06089", "doc_id": "NCT02946892_exc", "case_bucket": "or", "source_criterion": "The use of beta blockers within 2 months of randomization Patients actively listed for transplantation at time of entry into the study or anticipated to undergo heart transplantation, interventional catheterization, or corrective cardiac surgery during the 7 months following entry into the study Sustained or symptomatic ventricular dysrhythmias uncontrolled by drug therapy or the use of an implantable defibrillator, and/or significant cardiac conduction defects, e.g., 2nd degree or 3rd degree AV block, or sick sinus syndrome, unless a functioning pacemaker is in place Uncorrected obstructive or severe regurgitant valve disease, nondilated cardiomyopathy, or significant systemic ventricular outflow obstruction Known renovascular hypertension or evidence of pulmonary hypertension (pulmonary vascular resistance > 6 Wood units) unresponsive to vasodilator agents such as oxygen, nitroprusside, or nitric oxide History or current clinical evidence of moderate-to-severe fixed obstructive pulmonary disease or severe reactive airway diseases (e.g., asthma) requiring hospitalization within the past 2 years or patient currently using long-term inhaled bronchodilators Renal, hepatic, gastrointestinal, or biliary disorder that could impair absorption, metabolism or excretion of orally administered medication Concurrent terminal illness or other severe disease (e.g., active neoplasm) or other significant laboratory value(s) which, in the opinion of the investigator, could preclude participation or survival Endocrine disorders such as primary aldosteronism, pheochromocytoma, hyper- or hypothyroidism, insulin-dependent diabetes mellitus Unwillingness or inability to cooperate, or for the parents or guardians to give consent, or for the child to give assent, or any condition of sufficient severity to impair cooperation in the study Pregnancy or possible pregnancy at time of randomization, or female of child bearing potential who are lactating, or sexually active and not taking adequate contraceptive precautions (e.g., intrauterine device or oral contraceptives for 3 months prior to entry into the study) Use of an investigational drug within 30 days of randomization, or within 5 half-lives of the investigational drug (the longer period will apply) History of drug sensitivity or allergic reaction to alpha-blockers or beta-blockers Use of any of the following medications within two weeks of randomization: MAO inhibitors, Calcium channel blockers, alpha blockers, beta blockers, disopyramide, flecainide, encainide, moricizine, propafenone, sotalol, or beta adrenergic agonists Hospital admission for protein losing enteropathy or plastic bronchitis within 3 months of randomization Active and/or chronic protein losing enteropathy or plastic bronchitis (on inhaled medication to control the plastic bronchitis). Hypoalbuminemia defined as serum albumin <2.0g/dL Renal dysfunction defined as serum creatinine >2.0mg/dL Hepatic dysfunction defined as serum AST and/or ALT> 3 times upper limit of normal (approximately 120 IU/L however, will vary depending on age), Significant anemia or polycythemia defined as hemoglobin >18gm/dL or hemoglobin <7gm/dL Severely elevated serum BNP defined as BNP>300pg/ml", "candidate_expression": "((BNP >300pg/ml) AND (Endocrine disorders) AND (Hepatic dysfunction approximately 120 IU/L) AND (Hospital admission within 3 months of randomization) AND (Hypoalbuminemia) AND (Renal dysfunction) AND (asthma) AND (beta blockers within 2 months of randomization) AND (cardiac conduction defects significant) AND (child bearing potential) AND (disorder) AND (drug) AND (drug therapy) AND (female) AND (impair absorption) AND (impair excretion) AND (impair metabolism) AND (implantable defibrillator) AND (inhaled medication) AND (investigational drug) AND (laboratory) AND (lactating) AND (listed for transplantation at time of entry into the study) AND (neoplasm active) AND (obstructive pulmonary disease moderate-to-severe fixed) AND (orally administered medication) AND (pulmonary hypertension evidence of) AND (pulmonary vascular resistance > 6 Wood units) AND (reactive airway diseases) AND (renovascular hypertension) AND (serum BNP Severely elevated) AND (serum albumin <2.0g/dL) AND (serum creatinine >2.0mg/dL) AND (sexually active) AND (transplantation) AND (vasodilator agents) AND (ventricular dysrhythmias) AND NOT (contraceptive precautions adequate) AND NOT (pacemaker functioning) AND ((diabetes mellitus insulin-dependent) OR (hyper thyroidism) OR (hypothyroidism) OR (pheochromocytoma) OR (primary aldosteronism)) AND ((corrective cardiac surgery) OR (heart transplantation) OR (interventional catheterization)) AND ((Unwillingness for the guardians to give consent) OR (Unwillingness for the parents to give consent) OR (Unwillingness to cooperate) OR (inability for the guardians to give consent) OR (inability for the parents to give consent) OR (inability to cooperate)) AND ((Pregnancy) OR (pregnancy possible at time of randomization)) AND ((intrauterine device) OR (oral contraceptives for 3 months prior to entry into the study)) AND ((within 30 days of randomization randomization) OR (within 5 half-lives of the investigational drug)) AND ((allergic reaction) OR (drug sensitivity)) AND ((alpha-blockers) OR (beta-blockers)) AND ((Calcium channel blockers) OR (MAO inhibitors) OR (alpha blockers) OR (beta adrenergic agonists) OR (beta blockers) OR (disopyramide) OR (encainide) OR (flecainide) OR (moricizine) OR (propafenone) OR (sotalol)) AND ((Sustained) OR (symptomatic)) AND ((plastic bronchitis) OR (protein losing enteropathy)) AND ((Active) OR (chronic)) AND ((serum ALT) OR (serum AST)) AND ((uncontrolled by drug therapy) OR (uncontrolled by the use of an implantable defibrillator)) AND ((anemia) OR (polycythemia)) AND ((hemoglobin <7gm/dL) OR (hemoglobin >18gm/dL)) AND ((2nd degree AV block) OR (3rd degree AV block) OR (sick sinus syndrome)) AND ((nondilated cardiomyopathy) OR (obstructive valve disease Uncorrected) OR (regurgitant valve disease severe) OR (systemic ventricular outflow obstruction significant)) AND ((nitric oxide) OR (nitroprusside) OR (oxygen)) AND ((History) OR (current)) AND ((hospitalization requiring within the past 2 years) OR (long-term inhaled bronchodilators currently)) AND ((Renal) OR (biliary) OR (gastrointestinal) OR (hepatic)) AND ((severe disease other) OR (significant laboratory value(s)) OR (terminal illness)))"}
{"candidate_id": "LLM06090", "doc_id": "NCT02745704_inc", "case_bucket": "other", "source_criterion": "CHB patients who had received NAs for more than 12 months. Hepatitis B e antigen (HBeAg)-negative and anti-HBeAg positive. Hepatitis B surface antigen (HBsAg) positive and <1500 IU/mL. Hepatitis B virus DNA not detectable(Roche Cobas).", "candidate_expression": "((CHB) AND (HBeAg) AND (HBsAg) AND (Hepatitis B e antigen negative) AND (Hepatitis B surface antigen positive <1500 IU/mL) AND (Hepatitis B virus DNA not detectable) AND (NAs more than 12 months.) AND (anti-HBeAg positive))"}
{"candidate_id": "LLM06091", "doc_id": "NCT01794793_exc", "case_bucket": "or", "source_criterion": "Patient has been permanently discontinued from pasireotide study treatment in the parent study due to unacceptable toxicity, non-compliance to study procedures, withdrawal of consent or any other reason Patient has participated in a Novartis sponsored combination trial where pasireotide was dispensed in combination with another study medication and is still receiving combination therapy. (only patients receiving pasireotide monotherapy can be included) Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test Total abstinence (when this is in line with the preferred and usual lifestyle of the subject. Periodic abstinence (e.g., calendar, ovulation, symptothermal, post-ovulation methods) and withdrawal are not acceptable methods of contraception Female sterilization (have had surgical bilateral oophorectomy with or without hysterectomy) or tubal ligation at least six weeks before taking study treatment. In case of oophorectomy alone, only when the reproductive status of the woman has been confirmed by follow up hormone level assessment Male sterilization (at least 6 months prior to screening). For female subjects on the study the vasectomized male partner should be the sole partner for that subject. Use of oral, injected or implanted hormonal methods of contraception or other forms of hormonal contraception that have comparable efficacy (failure rate <1%), for example hormone vaginal ring or transdermal hormone contraception Placement of an intrauterine device (IUD) or intrauterine system (IUS) Barrier methods of contraception: Condom or Occlusive cap diaphragm or cervical/vault caps) with spermicidal foam/gel/film/cream/vaginal suppository In case of use of oral contraception women should have been stable on the same pill for a minimum of 3 months before taking study treatment Sexually active males unless they use a condom during intercourse while taking drug and for 1 months after pasireotide s.c. last dose and 3 months after pasireotide LAR last dose and should not father a child in this period. A condom is required to be used also by vasectomized men in order to prevent delivery of the drug via seminal fluid If a study patient or partner becomes pregnant or suspects being pregnant during the study or within 1 month after the final dose of pasireotide s.c. or 3 months after the final dose of pasireotide LAR, the Study Doctor needs to be informed immediately and ongoing study treatment with pasireotide has to be stopped immediately For patients taking pasireotide LAR, the future dose injections will be cancelled.", "candidate_expression": "((Condom) AND (Female sterilization) AND (IUD) AND (IUS) AND (Male sterilization at least 6 months prior to screening) AND (Occlusive cap diaphragm) AND (Patient has participated in a Novartis sponsored combination trial where pasireotide was dispensed in combination with another study medication and is still receiving combination therapy. (only patients receiving pasireotide monotherapy can be included)) AND (Total abstinence (when this is in line with the preferred and usual lifestyle of the subject. Periodic abstinence (e.g., calendar, ovulation, symptothermal, post-ovulation methods) and withdrawal are not acceptable methods of contraception) AND (bilateral oophorectomy) AND (cervical caps) AND (contraception) AND (hormone vaginal ring) AND (hysterectomy) AND (intrauterine device) AND (intrauterine system) AND (nant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test) AND (spermicidal foam) AND (transdermal hormone contraception) AND (tubal ligation at least six weeks before taking study treatment) AND (vault caps))"}
{"candidate_id": "LLM06092", "doc_id": "NCT03506750_exc", "case_bucket": "or", "source_criterion": "previous retinal vein occlusion. any intraocular surgery within the previous 12 months. myopia of > or = to 8 diopters. active ocular or periocular infection treatment with an investigational agent for any condition 60 days prior to enrollment. evidence of severe cardiac disease. clinically significant peripheral vascular disease (previous surgery, amputation, or symptoms of claudication) uncontrolled hypertension (treated systolic blood pressure > 155 mmHg or diastolic blood pressure > 95 mmHg) stroke within the preceding 12 months.", "candidate_expression": "((> 155 mmHg) AND (> 95 mmHg) AND (> or = to 8 diopters) AND (active) AND (cardiac disease) AND (clinically significant) AND (evidence of) AND (hypertension) AND (intraocular surgery) AND (myopia) AND (peripheral vascular disease) AND (previous) AND (retinal vein occlusion) AND (severe) AND (stroke) AND (treated) AND (treatment with an investigational agent for any condition 60 days prior to enrollment) AND (uncontrolled) AND (within the preceding 12 months) AND (within the previous 12 months) AND ((amputation) OR (previous surgery) OR (symptoms of claudication)) AND ((diastolic blood pressure) OR (systolic blood pressure)) AND ((ocular infection) OR (periocular infection)))"}
{"candidate_id": "LLM06093", "doc_id": "NCT03400735_inc", "case_bucket": "other", "source_criterion": "The diagnosis of chronic bronchitis The diagnosis of community-acquired pneumoniae FEV1 value = 30-80% The diagnosis of mild-severe acute exacerbation of chronic bronchitis (AECB) Oxygen saturation < 90%", "candidate_expression": "((AECB) AND (FEV1 value = 30-80%) AND (Oxygen saturation < 90%) AND (chronic bronchitis) AND (community-acquired pneumoniae) AND (exacerbation of chronic bronchitis mild-severe acute))"}
{"candidate_id": "LLM06094", "doc_id": "NCT02973035_inc", "case_bucket": "or", "source_criterion": "Controlled hypertension: systolic BP < 150 and diastolic BP < 90 mmHg in persons aged 60 years or older, systolic BP < 140 and diastolic BP < 90 mmHg in persons 40 through 59 years according to the JNC 8th guideline Evidence of diastolic dysfunction showing E/E' > 10 The patient agrees to the study protocol and the schedule of clinical and echocardiographic follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site", "candidate_expression": "((E/E' > 10) AND (The patient agrees to the study protocol and the schedule of clinical and echocardiographic follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site) AND (aged 60 years or older) AND (diastolic BP < 90 mmHg) AND (diastolic dysfunction) AND (hypertension Controlled JNC 8th guideline) AND (systolic BP < 140) AND (systolic BP < 150) AND (years 40 through 59))"}
{"candidate_id": "LLM06095", "doc_id": "NCT02953873_inc", "case_bucket": "other", "source_criterion": "At least 18 years of age Signed informed consent African American race History of a solitary renal transplant Stable tacrolimus dose for at least 2 weeks prior to randomization", "candidate_expression": "((Signed informed consent) AND (age At least 18 years) AND (race African American) AND (renal transplant solitary) AND (tacrolimus Stable dose for at least 2 weeks prior to randomization))"}
{"candidate_id": "LLM06096", "doc_id": "NCT03125057_inc", "case_bucket": "other", "source_criterion": "Children with clinical diagnosis of PWS; Age range: 7 to 14 years-old; Voluntarily participated and Written informed consent signed", "candidate_expression": "((Age 7 to 14 years-old) AND (Children) AND (PWS clinical diagnosis) AND (Voluntarily participated) AND (Written informed consent signed))"}
{"candidate_id": "LLM06097", "doc_id": "NCT02303171_inc", "case_bucket": "other", "source_criterion": "Pregnant women with APS diagnosed according to the revised classification criteria for APS in 2006 in Sydney, Australia Early pregnancy body weight is 50-90 Kg", "candidate_expression": "((50-90 Kg) AND (APS) AND (Early pregnancy) AND (Pregnant) AND (body weight) AND (revised classification criteria for APS in 2006 in Sydney, Australia) AND (women))"}
{"candidate_id": "LLM06098", "doc_id": "NCT02526823_inc", "case_bucket": "or", "source_criterion": "Primary B-NHL, PTCL (ALK+ anaplastic large cell lymphoma and NK(natural killer cell )/T cell lymphoma were excluded) or HL patients confirmed by histopathology; Ages =18 years old, < 80 years old; ECOG (Eastern Cooperative Oncology Group)score: 0-2 At least one measurable lesion; Expected survival time=3 months; Liver function: transaminase=2.5× upper limit of normal value,bilirubin=1.5×upper limit of normal value; Renal function: serum creatinine is 44-133 mmol/L; Routine blood test:WBC=3.0×109/L,Neutrophils=1.5×109/L,Hb=100g/L,Platelet=80×109/L; LVEF=50%; New York Heart Association (NYHA) heart function classification is I-II grade signed informed consent.", "candidate_expression": "((0-2) AND (3 months) AND (44-133 mmol/L) AND (=1.5×109/L) AND (=1.5×upper limit of normal value) AND (=100g/L) AND (=18 years old, < 80 years old) AND (=2.5× upper limit of normal value) AND (=3.0×109/L) AND (=50%) AND (=80×109/L) AND (ALK+ anaplastic large cell lymphoma and NK(natural killer cell )/T cell lymphoma) AND (Ages) AND (At least one) AND (ECOG (Eastern Cooperative Oncology Group)score) AND (Expected survival time=) AND (HL) AND (Hb) AND (I-II grade) AND (LVEF) AND (NYHA) AND (Neutrophils) AND (New York Heart Association heart function classification) AND (PTCL) AND (Platelet) AND (Primary B-NHL) AND (bilirubin) AND (excluded) AND (lesion) AND (serum creatinine) AND (signed informed consent) AND (test:WBC) AND (transaminase))"}
{"candidate_id": "LLM06099", "doc_id": "NCT02609048_inc", "case_bucket": "or", "source_criterion": "1. Must have given written informed consent (signed and dated) and any authorizations required by local law 2. 18 to 75 years old (inclusive) 3. Male or female with a diagnosis of PBC, by at least two of the following criteria: History of AP above ULN for at least six months Positive Anti-Mitochondrial Antibodies (AMA) titers (>1/40 on immunofluorescence or M2 positive by enzyme linked immunosorbent assay (ELISA) or positive PBC-specific antinuclear antibodies Documented liver biopsy result consistent with PBC 4. On a stable and recommended dose of UDCA for the past twelve months 5. AP ≥ 1.67 × ULN 6. For females of reproductive potential, use of at least one barrier contraceptive and a second effective birth control method during the study and for at least two weeks after the last dose. For male subjects, use of appropriate contraception (e.g., condoms), so their female partners of reproductive potential do not become pregnant during the study and for at least two weeks after the last dose", "candidate_expression": "((18 to 75 years old (inclusive)) AND (>1/40) AND (AP) AND (For male subjects, use of appropriate contraception (e.g., condoms), so their female partners of reproductive potential do not become pregnant during the study and for at least two weeks after the last dose) AND (M2 positive) AND (Must have given written informed consent (signed and dated) and any authorizations required by local law) AND (PBC) AND (PBC-specific antinuclear antibodies) AND (Positive Anti-Mitochondrial Antibodies (AMA) titers) AND (UDCA) AND (above ULN) AND (appropriate) AND (at least one) AND (at least two) AND (barrier contraceptive) AND (birth control method) AND (condoms) AND (contraception) AND (during the study) AND (effective) AND (enzyme linked immunosorbent assay (ELISA)) AND (female) AND (females) AND (following criteria) AND (for at least six months) AND (for at least two weeks after the last dose) AND (for the past twelve months) AND (immunofluorescence) AND (liver biopsy) AND (male) AND (not become) AND (positive) AND (pregnant) AND (recommended dose) AND (reproductive potential) AND (second) AND (stable dose) AND (the last dose) AND (years old) AND (≥ 1.67 × ULN) AND ((Male) OR (female)))"}
{"candidate_id": "LLM06100", "doc_id": "NCT02344888_inc", "case_bucket": "other", "source_criterion": "Infertile lean women with PCOS as defined by the Rotterdam criteria. CC resistance (defined as failure of ovulation after receiving 150 mg/day of CC for 5 consecutive days per cycle, for at least 3 consecutive cycles).", "candidate_expression": "((CC) AND (Infertile) AND (PCOS) AND (Rotterdam criteria) AND (resistance) AND (women))"}
```
