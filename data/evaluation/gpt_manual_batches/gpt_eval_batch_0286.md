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
{"candidate_id": "LLM07126", "doc_id": "NCT02966236_inc", "case_bucket": "scope", "source_criterion": "Complex kidney stone (staghorn calculi GUYS III and IV)", "candidate_expression": "((Complex kidney stone) AND (GUYS III and IV) AND (staghorn calculi))"}
{"candidate_id": "LLM07127", "doc_id": "NCT02357654_exc", "case_bucket": "other", "source_criterion": "day 3 transfers", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07128", "doc_id": "NCT01313676_inc", "case_bucket": "or", "source_criterion": "Type of subject: outpatient. Informed consent: Subjects must give their signed and dated written informed consent to participate. Gender: Male or female. Female subjects must be post-menopausal or using a highly effective method for avoidance of pregnancy. The decision to include or exclude women of childbearing potential may be made at the discretion of the investigator in accordance with local practice in relation to adequate contraception. Age: >=40 and <=80 years of age at Screening (Visit 1). Tobacco use: Subjects with a current or prior history of >=10 pack-years of cigarette smoking at screening (Visit 1). Previous smokers are defined as those who have stopped smoking for at least 6 months prior to Visit 1. Airflow Obstruction: Subjects with a measured post-albuterol/salbutamol forced expiratory volume in 1 second (FEV1)/(forced vital capacity)FVC ratio of <=0.70 at Screening (Visit 1). Subjects with a measured post-albuterol/salbutamol FEV1 >=50 and <=70% of predicted normal values calculated using NHANES III reference equations [Hankinson, 1999; Hankinson, 2010] at Screening (Visit 1). Post-bronchodilator spirometry will be performed approximately 15 minutes after the subject has self-administered 4 inhalations (i.e., total 400mcg) of albuterol/salbutamol via a metered dose inhaler (MDI )with a valved-holding chamber. The FEV1/FVC ratio and FEV1 percent predicted values will be calculated. Symptoms of COPD: Subjects must score 2 or higher on the modified Medical Research Council Dyspnea scale (Visit 1) Cardiovascular disease: For patients >= 40 years of age: any one of the following: Established (i.e. by clinical signs or imaging studies) coronary artery disease (CAD) Established (i.e. by clinical signs or imaging studies) peripheral vascular disease (PVD) Previous stroke Previous MI Diabetes mellitus with target organ disease OR For patients >=60 years of age: any 2 of the following: Being treated for hypercholesterolemia Being treated for hypertension Being treated for diabetes mellitus Being treated for peripheral vascular disease", "candidate_expression": "((4) AND (400mcg) AND (<=0.70) AND (>= 40 years) AND (>=10 pack-years) AND (>=40 and <=80 years) AND (>=50 and <=70% of predicted normal values) AND (>=60 years) AND (Age) AND (Diabetes mellitus) AND (Established) AND (FEV1) AND (Female subjects must be post-menopausal or using a highly effective method for avoidance of pregnancy. The decision to include or exclude women of childbearing potential may be made at the discretion of the investigator in accordance with local practice in relation to adequate contraception.) AND (Informed consent: Subjects must give their signed and dated written informed consent to participate.) AND (MI) AND (Male) AND (Post-bronchodilator) AND (Previous) AND (Previous smokers) AND (Screening) AND (Symptoms of COPD) AND (Visit 1) AND (age) AND (albuterol) AND (albuterol/salbutamol) AND (approximately 15 minutes after) AND (at Screening) AND (at screening) AND (bronchodilator) AND (cigarette smoking) AND (clinical signs) AND (coronary artery disease (CAD)) AND (current) AND (diabetes mellitus) AND (female) AND (for at least 6 months prior to Visit 1) AND (forced expiratory volume in 1 second (FEV1)/(forced vital capacity)FVC ratio) AND (history) AND (hypercholesterolemia) AND (hypertension) AND (imaging studies) AND (inhalations) AND (metered dose inhaler (MDI )) AND (modified Medical Research Council Dyspnea scale) AND (outpatient) AND (peripheral vascular disease) AND (peripheral vascular disease (PVD)) AND (post-albuterol/salbutamol) AND (prior) AND (salbutamol) AND (score 2 or higher) AND (self-administered) AND (spirometry) AND (stopped smoking) AND (stroke) AND (target organ disease) AND (treated for diabetes mellitus) AND (treated for hypercholesterolemia) AND (treated for hypertension) AND (treated for peripheral vascular disease) AND (using NHANES III reference equations) AND (with a valved-holding chamber))"}
{"candidate_id": "LLM07129", "doc_id": "NCT02589977_exc", "case_bucket": "or", "source_criterion": "Exclusion Criteria: coronary artery disease, diabetes mellitus, contraindications to cardiac magnetic resonance imaging (CMR), weight >350 lbs, inability to lie flat for imaging, anemia, contraindications to regadenoson or aminophylline HEALTHY: known cardiovascular disease, cardiac risk factors or use of cardiac medications HYPERTENSIVE: known cardiovascular disease or risk factors aside from hypertension or use of cardiac medications HFpEF: prior history of LVEF below 50%, acute decompensated HF, moderate or greater valvular disease, significant cardiac arrhythmias, pericardial disease, congenital heart disease, primary pulmonary hypertension", "candidate_expression": "((>350 lbs) AND (HEALTHY) AND (HFpEF) AND (HYPERTENSIVE) AND (LVEF) AND (acute) AND (aminophylline) AND (anemia) AND (aside from) AND (below 50%) AND (cardiac arrhythmias) AND (cardiac magnetic resonance imaging (CMR)) AND (cardiac medications) AND (cardiac risk factors) AND (cardiovascular disease) AND (cardiovascular risk factors) AND (cardiovascular risk factors from hypertension) AND (congenital heart disease) AND (contraindications) AND (coronary artery disease) AND (decompensated HF) AND (diabetes mellitus) AND (greater) AND (inability to lie flat for imaging) AND (moderate) AND (pericardial disease) AND (primary pulmonary hypertension) AND (prior history of) AND (regadenoson) AND (significant) AND (valvular disease) AND (weight))"}
{"candidate_id": "LLM07130", "doc_id": "NCT01410890_exc", "case_bucket": "other", "source_criterion": "The patient is participating in another clinical study using an investigational product. The patient, in the opinion of the Investigator, is unable to adhere to the requirements of the study.", "candidate_expression": "(The patient is participating in another clinical study using an investigational product)"}
{"candidate_id": "LLM07131", "doc_id": "NCT02612181_inc", "case_bucket": "other", "source_criterion": "Septic shock patients despite early goal directed therapy Agree to participate this study", "candidate_expression": "((Agree to participate this study) AND (Septic shock) AND (early goal directed therapy))"}
{"candidate_id": "LLM07132", "doc_id": "NCT03234816_inc", "case_bucket": "other", "source_criterion": "full term singleton pregnant women Scheduled for elective Cesarean Delivery Aged between 18 and 40 years", "candidate_expression": "((Aged between 18 and 40 years) AND (Cesarean Delivery Scheduled for elective) AND (pregnant full term singleton) AND (women))"}
{"candidate_id": "LLM07133", "doc_id": "NCT02557386_exc", "case_bucket": "other", "source_criterion": "Chronic pain more than 3 months Drug abuse Chronic use of analgesic drugs (more than 3 months) Psychiatric illness Peripheral neuropathy Drug allergy Severe gastroesophageal reflux disease", "candidate_expression": "((Chronic) AND (Chronic pain) AND (Drug) AND (Drug abuse) AND (Peripheral neuropathy) AND (Psychiatric illness) AND (Severe) AND (allergy) AND (analgesic drugs) AND (gastroesophageal reflux disease) AND (more than 3 months))"}
{"candidate_id": "LLM07134", "doc_id": "NCT03120728_inc", "case_bucket": "or", "source_criterion": "Healthy, women ages 18 to 39yo with BMI <30 Regular menstrual cycles with duration between 24-35 days Completion of screening visit where ovulation will be assessed with blood draw for progesterone level (must be 5ng/mL or greater) Not seeking pregnancy during the study period Use of a non-hormonal form of contraception, such as: sterilization (tubal ligation, Essure), copper IUD (intrauterine device), barrier methods or abstinence Must speak English or Spanish", "candidate_expression": "((BMI <30) AND (Healthy) AND (Not seeking pregnancy during the study period) AND (Regular menstrual cycles) AND (ages 18 to 39yo) AND (duration between 24-35 days) AND (intrauterine device) AND (non-hormonal form of contraception) AND (progesterone level 5ng/mL or greater) AND (women) AND ((Essure) OR (tubal ligation)) AND ((abstinence) OR (barrier methods) OR (copper IUD) OR (sterilization)))"}
{"candidate_id": "LLM07135", "doc_id": "NCT03364036_inc", "case_bucket": "or", "source_criterion": "Highly active RMS as defined by: One relapse in the previous year and at least 1 T1 Gadolinium (Gd)+ lesion or 9 or more T2 lesions, while on therapy with other disease modifying drugs (DMDs) Two or more relapses in the previous year, whether on DMD treatment or not. Expanded Disability Status Scale (EDSS) score less than equals to (<=) 5.0. Other protocol defined inclusion criteria could apply.", "candidate_expression": "((9 or more) AND (Expanded Disability Status Scale (EDSS) score) AND (Highly active) AND (One) AND (Other protocol defined inclusion criteria could apply.) AND (RMS) AND (T1 Gadolinium (Gd)+) AND (Two or more) AND (at least 1) AND (disease modifying drugs (DMDs)) AND (in the previous year) AND (less than equals to (<=) 5.0) AND (other) AND (relapse) AND (relapses) AND (therapy) AND (while on therapy) AND ((T2 lesions) OR (lesion)))"}
{"candidate_id": "LLM07136", "doc_id": "NCT00122070_exc", "case_bucket": "or", "source_criterion": "Are pregnant or lactating. Have participated in any other studies involving investigational products within 30 days prior to entry into this study. Are undergoing an acute withdrawal syndrome from drugs or alcohol. Have an Axis I diagnosis of Schizophrenia, Schizoaffective Disorder, Schizophreniform Disorder or Bipolar I Disorder as diagnosed by the Structured Clinical Interview for DSM-IV Axis I Disorders (SCID-I), and pertinent subsequent for ruling out exclusionary diagnoses. Have an unstable medical disorder as determined by physical examination or laboratory testing. The primary investigator will be responsible for making this judgment based on the above. Had an unsatisfactory response to a previous adequate trial of quetiapine as judged by a study investigator. Patients cannot begin psychotherapy during the study period, but may continue if started prior to the study. Patients who are currently receiving quetiapine therapy may not undergo a washout period and then restart quetiapine in the study.", "candidate_expression": "((Have participated in any other studies involving investigational products) AND (Structured Clinical Interview for DSM-IV Axis I Disorders (SCID-I)) AND (acute withdrawal syndrome) AND (entry into this stud) AND (within 30 days prior to entry into this study) AND ((Bipolar I Disorder) OR (Schizoaffective Disorder) OR (Schizophrenia) OR (Schizophreniform Disorder)) AND ((lactating) OR (pregnant)) AND ((alcohol) OR (drugs)))"}
{"candidate_id": "LLM07137", "doc_id": "NCT02537899_exc", "case_bucket": "or", "source_criterion": "Non survivable injury Multiple significant trauma (i.e. significant intracranial and extracranial injuries including limb fractures) that would limit observation of recovery from spinal cord injury Other conditions that would limit clinical assessment of outcomes (e.g. dementia, demyelinating disease, autoimmune disease, etc) Refusal of treatment or contraindication to NeuroAiD", "candidate_expression": "((Multiple) AND (NeuroAiD) AND (Non survivable) AND (contraindication) AND (extracranial injuries) AND (injury) AND (intracranial injuries) AND (limb fractures) AND (significant) AND (trauma) AND ((autoimmune disease) OR (dementia) OR (demyelinating disease)))"}
{"candidate_id": "LLM07138", "doc_id": "NCT03034096_inc", "case_bucket": "or", "source_criterion": "Lobectomy or pneumonectomy Esophagectomy Radical (total) cystectomy Pancreatectomy Partial hepatectomy Hyperthermic intraperitoneal chemotherapy (HIPEC) Gastrectomy (subtotal or total) Cholecystectomy or bile duct resection", "candidate_expression": "((Esophagectomy) AND (Gastrectomy) AND (HIPEC) AND (Hyperthermic intraperitoneal chemotherapy) AND (Pancreatectomy) AND (Partial hepatectomy) AND (Radical cystectomy) AND (total cystectomy) AND ((Lobectomy) OR (pneumonectomy)) AND ((subtotal) OR (total)) AND ((Cholecystectomy) OR (bile duct resection)))"}
{"candidate_id": "LLM07139", "doc_id": "NCT01604187_inc", "case_bucket": "other", "source_criterion": "ASA I-III Colonoscopy Written informed consent from participating subject", "candidate_expression": "((ASA I-III) AND (Colonoscopy) AND (Written informed consent from participating subject))"}
{"candidate_id": "LLM07140", "doc_id": "NCT02673359_inc", "case_bucket": "or", "source_criterion": "Women with singleton pregnancy. History of preterm labor and/or midtrimester miscarriage in a previous pregnancy. Cervical length of 15-25 mm by transvaginal sonography (TVS) at 16-24 weeks of gestation.", "candidate_expression": "((15-25 mm) AND (16-24 weeks) AND (16-24 weeks of gestation) AND (Cervical length) AND (Women) AND (at 16-24 weeks of gestation) AND (gestation) AND (midtrimester miscarriage) AND (pregnancy) AND (preterm labor) AND (previous) AND (singleton pregnancy) AND (transvaginal sonography (TVS)))"}
{"candidate_id": "LLM07141", "doc_id": "NCT02469610_inc", "case_bucket": "other", "source_criterion": "Thoracoscopic surgery candidate. Over 18 years old. No known allergy to Bupivacaine. Patient is able to read understand and singe an inform consent.", "candidate_expression": "((Bupivacaine) AND (No) AND (Over 18 years old) AND (Thoracoscopic surgery) AND (able to read) AND (allergy) AND (candidate) AND (old) AND (singe) AND (understand))"}
{"candidate_id": "LLM07142", "doc_id": "NCT02536976_exc", "case_bucket": "or", "source_criterion": "Known or suspected alcohol or substance abuse in the preceding 12 months. Women who are pregnant or breastfeeding. Women of childbearing potential (WOCP) who are not using at least one method of contraception. Patients with severe renal impairment (CLcr = 29 mL/min, or eGFR = 29 mL/min/1.73 m2), or moderate or severe hepatic impairment (Child-Pugh classes B or C). Patients with bladder outlet obstruction (BOO) that, in the opinion of the study urologist, would expose them to risk of urinary retention during treatment with mirabegron. Patients treated with drugs metabolized by the CYP2D6 pathway. Patients with supine systolic blood pressure (SBP) = 180 mm Hg, or diastolic blood pressure (DBP) = 110 mm Hg. Clinically significant, uncontrolled cardiac arrhythmia, unstable angina, congestive heart failure (NYHA Class 3 or 4), or history of myocardial infarction in the preceding 2 years. History of cancer in the preceding 2 years other than successfully treated, non-metastatic, squamous cell or basal cell carcinoma, or cervical cancer in situ. Any major urological procedure in the preceding 90 days. Any major surgical procedure in the preceding 30 days. Previously treated with mirabegron within 60 days prior to the baseline visit (Visit 2), or previously having failed treatment with mirabegron regardless of duration and timing of treatment. Current or previous, within the 60 days preceding the baseline visit (Visit 2), treatment with antimuscarinic agents for OAB symptoms; and, willingness to not use antimuscarinic agents for the duration of the study. Currently receiving any other investigational drug or having received an investigational drug within the 60 days preceding the baseline visit (Visit 2). Any condition or laboratory test result, which, in the opinion of the Investigator or the Study Urologist, might result in an increased risk to the patient, or would affect their participation in the study. Any patient who, in the opinion of the Investigator, is not a good candidate for the study or will not be able to follow study procedures.", "candidate_expression": "((= 110 mm Hg) AND (= 180 mm Hg) AND (= 29 mL/min) AND (= 29 mL/min/1.73 m2) AND (BOO) AND (Child-Pugh classes) AND (Currently receiving any other investigational drug or having received an investigational drug within the 60 days preceding the baseline visit (Visit 2)) AND (DBP) AND (NYHA Class) AND (OAB symptoms) AND (SBP) AND (Women of childbearing potential (WOCP) who are not using at least one method of contraception) AND (Women who are pregnant or breastfeeding) AND (antimuscarinic agents) AND (baseline visit) AND (bladder outlet obstruction) AND (cancer) AND (major surgical procedure) AND (major urological procedure) AND (mirabegron) AND (non-metastatic) AND (other) AND (preceding 12 months) AND (preceding 2 years) AND (preceding 30 days) AND (preceding 90 days) AND (risk of urinary retention) AND (severe) AND (successfully treated) AND (supine) AND (uncontrolled) AND (willingness to not use antimuscarinic agents for the duration of the study) AND (within 60 days prior to the baseline visit) AND (within the 60 days preceding the baseline visit) AND ((hepatic impairment) OR (renal impairment)) AND ((moderate) OR (severe)) AND ((B) OR (C)) AND ((alcohol abuse) OR (substance abuse)) AND ((diastolic blood pressure) OR (systolic blood pressure)) AND ((cardiac arrhythmia) OR (congestive heart failure) OR (myocardial infarction) OR (unstable angina)) AND ((3) OR (4)) AND ((basal cell carcinoma) OR (carcinoma squamous cell) OR (cervical cancer in situ)) AND ((CLcr) OR (eGFR)))"}
{"candidate_id": "LLM07143", "doc_id": "NCT02531724_inc", "case_bucket": "other", "source_criterion": "Patients in the cardiothoracic intensive care after cardiac surgery with cardiopulmonary bypass Acute kidney injury, defined as increase in S-creatinine 50% or 27 mol/L Normal S-creatinine before surgery", "candidate_expression": "((50% or 27 mol/L) AND (Acute kidney injury) AND (Normal) AND (S-creatinine) AND (after cardiac surgery with cardiopulmonary bypass) AND (before surgery) AND (cardiac surgery) AND (cardiac surgery with cardiopulmonary bypass) AND (cardiopulmonary bypass) AND (cardiothoracic intensive care) AND (increase in S-creatinine) AND (surgery))"}
{"candidate_id": "LLM07144", "doc_id": "NCT02394158_inc", "case_bucket": "other", "source_criterion": "Singleton pregnancy; 8-22 weeks gestation Previous pregnancy complicated by gestational diabetes", "candidate_expression": "((8-22 weeks) AND (Singleton pregnancy) AND (gestation) AND (gestational diabetes) AND (pregnancy))"}
{"candidate_id": "LLM07145", "doc_id": "NCT03495557_exc", "case_bucket": "other", "source_criterion": "Conversion to laparotomy Emergent re intervention Immunosuppression Umbilical hernia", "candidate_expression": "((Conversion to) AND (Immunosuppression) AND (Umbilical hernia) AND (laparotomy) AND (re intervention Emergent))"}
{"candidate_id": "LLM07146", "doc_id": "NCT02985710_exc", "case_bucket": "or", "source_criterion": "Subjects with cognitive, psychiatric, or other problems that preclude informed consent. Patients with history of glucose intolerance or diabetes. Patient on chemotherapy People with any open or bleeding wounds at any sensor plate contact surface location People with any type of implantable device People with missing hand(s) and/or leg(s) Pregnant women or women who are uncertain about a possible pregnancy Patients sensitive to chemicals used to induce sweating Patients with heat intolerance Patients with bleeding disorders Patients on current anticoagulant therapy Patients with keloids on the intended biopsy site People with hypersensitivity to local amide-type anesthetics", "candidate_expression": "((anticoagulant therapy) AND (at any sensor plate contact surface location) AND (bleeding disorders) AND (chemotherapy) AND (current) AND (heat intolerance) AND (history) AND (hypersensitivity) AND (implantable device) AND (keloids) AND (local amide-type anesthetics) AND (on the intended biopsy site) AND (other problems that preclude informed consent) AND (sensitive to chemicals used to induce sweating) AND ((cognitive problems) OR (other problems that preclude informed consent) OR (psychiatric problems)) AND ((bleeding wounds) OR (open wounds)) AND ((missing hand) OR (missing leg)) AND ((Pregnant) OR (possible pregnancy)) AND ((diabetes) OR (glucose intolerance)))"}
{"candidate_id": "LLM07147", "doc_id": "NCT03228017_inc", "case_bucket": "or", "source_criterion": "Subjects with a history of moderate to severe psoriatic disease Group 2: Healthy subjects without known psoriatic disease or cardiovascular disease", "candidate_expression": "((Healthy) AND (cardiovascular disease) AND (psoriatic disease) AND (psoriatic disease history moderate severe))"}
{"candidate_id": "LLM07148", "doc_id": "NCT02667730_inc", "case_bucket": "or", "source_criterion": "Acquired acute ankle injury (injured less than 48 hours ago); Clinical diagnosis of a Grade I or II ankle sprain Is eligible to receive comprehensive medical care from Garrison Petawawa", "candidate_expression": "((acute ankle injury Acquired less than 48 hours ago) AND (ankle sprain) AND ((Grade I) OR (Grade II)))"}
{"candidate_id": "LLM07149", "doc_id": "NCT02838810_inc", "case_bucket": "other", "source_criterion": "CHB patients who had received single NAs for more than 12 months. Hepatitis B e antigen (HBeAg)-negative. Hepatitis B surface antigen (HBsAg) positive and <1000 IU/mL. Hepatitis B virus DNA <100 IU/mL.", "candidate_expression": "((<100 IU/mL) AND (<1000 IU/mL) AND (CHB) AND (HBeAg) AND (HBsAg) AND (Hepatitis B e antigen) AND (Hepatitis B surface antigen) AND (Hepatitis B virus DNA) AND (NAs) AND (more than 12 months) AND (negative) AND (positive) AND (single))"}
{"candidate_id": "LLM07150", "doc_id": "NCT03044561_exc", "case_bucket": "or", "source_criterion": "(1) Uterine abnormalities (e.g. septate, bicornuate and fibroid uterus, Asherman Syndrome). Concurrent use of organic nitrites and nitrates. Severe hepatic impairment. Severe renal impairment. Hypotension. Recent stroke or heart attack.", "candidate_expression": "((Asherman Syndrome) AND (Hypotension) AND (Uterine abnormalities) AND (bicornuate uterus) AND (fibroid uterus) AND (heart attack) AND (hepatic impairment Severe) AND (nitrates Concurrent) AND (organic nitrites Concurrent) AND (renal impairment Severe) AND (septate uterus) AND (stroke))"}
```
