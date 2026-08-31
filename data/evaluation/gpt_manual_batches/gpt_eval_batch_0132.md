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
{"candidate_id": "LLM03276", "doc_id": "NCT02337764_inc", "case_bucket": "other", "source_criterion": "The participant has a diagnosis of Parkinson's disease according to the diagnostic criteria of the UK Parkinson's Disease Society Brain Bank. The participant has received a levodopa combination drug for >= 1 month and has either of the following. Wearing off phenomenon Decreased response to levodopa combination drugs The participant has received a levodopa combination drug without change in the dose regimen. The participant is an outpatient of either sex aged >= 30 and < 80 years.", "candidate_expression": "((>= 1 month) AND (>= 30 and < 80 years) AND (Decreased response) AND (Parkinson's disease) AND (UK Parkinson's Disease Society Brain Bank) AND (Wearing off phenomenon) AND (aged) AND (evodopa combination drugs) AND (levodopa combination) AND (levodopa combination drug) AND (without change in the dose regimen))"}
{"candidate_id": "LLM03277", "doc_id": "NCT00094861_exc", "case_bucket": "or", "source_criterion": "Metastatic disease (M1)/stage 4 NSCLC Pleural or pericardial effusion greater than 100 ml in volume as documented by appropriate imaging (positron emission tomography [PET], computed tomography [CT] scan or ultrasound). If an effusion greater than 100 ml is documented by cytology to be free from malignancy and the investigator feels the patient is capable of receiving chemo/radiotherapy for their primary disease/ NSCLC, the investigator should discuss the patient with the study physician at Amgen. Effusions smaller than 100 ml would be acceptable, unless the investigator suspects that the effusion is malignant, in which case the effusions should be evaluated by cytology. Sponsor approval must be obtained before patient is randomized. Plan to remove the tumor surgically before completing the protocol chemo/radiotherapy course Shielding of any part of the esophagus during radiotherapy (including posterior spinal cord shielding) Prior chemotherapy, radiotherapy, or surgery for NSCLC Prior invasive malignancy during the past 3 years other than non-melanomatous skin cancer. Note: Patients with prior surgically-cured malignancies [eg, stage I breast cancer or prostate cancer, in-situ carcinoma of the cervix, etc] are not excluded; however, sponsor approval must be obtained before patient is randomized. Presence or history of dysphagia or conditions predisposing to dysphagia (eg, uncontrolled gastroesophageal reflux disease [GERD], dyspepsia, etc) History of pancreatitis Four weeks or less since completion of treatment using an investigational product/device in another clinical study or presence of any unresolved toxicity from previous treatment Previous treatment on this study or with a fibroblast growth factor Known to be sero-positive for human immunodeficiency virus (HIV), hepatitis C virus (HCV), or hepatitis B virus (HBV) Pregnant or breastfeeding women Known sensitivity to E. coli derived products Compromised ability of the patient to give written informed consent and/or to comply with study procedures Refusal to sign an informed consent form to participate in this study, and sign the hospital information release form, if applicable Unwilling or unable to complete the patient reported outcome (PRO) questionnaires Psychological, social, familial, or geographical reasons that would prevent regular follow-up", "candidate_expression": "(((M1)/stage 4) AND (CT) AND (Compromised ability) AND (E. coli derived) AND (Four weeks or less since completion of treatment) AND (GERD) AND (History of) AND (Metastatic disease NSCLC) AND (NSCLC) AND (PET) AND (Plan to remove the tumor surgically) AND (Previous) AND (Prior) AND (Refusal to) AND (Shielding) AND (another clinical study) AND (any part of) AND (are not) AND (before completing the protocol chemo/radiotherapy course) AND (completion of treatment) AND (during the past 3 years) AND (esophagus) AND (fibroblast growth factor) AND (give written informed consent) AND (greater than 100 ml in volume) AND (hepatitis B virus (HBV)) AND (hepatitis C virus (HCV)) AND (history of) AND (human immunodeficiency virus (HIV)) AND (invasive) AND (malignancy) AND (non-melanomatous skin cancer) AND (other than) AND (pancreatitis) AND (posterior spinal cord shielding) AND (previous) AND (products) AND (radiotherapy) AND (sensitivity) AND (sero-positive) AND (surgically-cured malignancies) AND (toxicity) AND (treatment) AND (uncontrolled) AND (unresolved) AND (women) AND ((chemotherapy) OR (radiotherapy) OR (surgery)) AND ((Pleural effusion) OR (pericardial effusion)) AND ((conditions predisposing to dysphagia) OR (dysphagia)) AND ((dyspepsia) OR (gastroesophageal reflux disease)) AND ((investigational device) OR (investigational product)) AND ((sero-positive for hepatitis B virus (HBV)) OR (sero-positive for hepatitis C virus (HCV)) OR (sero-positive for human immunodeficiency virus (HIV))) AND ((Pregnant) OR (breastfeeding)) AND ((computed tomography scan) OR (positron emission tomography) OR (ultrasound)) AND ((sign an informed consent form) OR (sign the hospital information release form)))"}
{"candidate_id": "LLM03278", "doc_id": "NCT00926523_exc", "case_bucket": "other", "source_criterion": "Subject are pregnant Subject is unable to perform tasks associated with study", "candidate_expression": "((Subject is unable to perform tasks associated with study) AND (pregnant))"}
{"candidate_id": "LLM03279", "doc_id": "NCT03337581_inc", "case_bucket": "or", "source_criterion": "selective operation of inguinal hernia repair<U+3001>orthopedics operation or general surgery operation in children aged 3-9 years ASA I - II enter the operating room by himself without parents normal liver and kidney function no history of anesthesia medication allergy.", "candidate_expression": "((ASA I - II) AND (aged 3-9 years) AND (anesthesia medication) AND (children) AND (normal kidney function) AND (normal liver function) AND NOT (allergy history) AND ((general surgery operation) OR (inguinal hernia repair) OR (orthopedics operation)))"}
{"candidate_id": "LLM03280", "doc_id": "NCT00926523_inc", "case_bucket": "other", "source_criterion": "Subject are at least 18 years of age Subject has confirmed Pulmonary Hypertension and Interstitial Lung Disease Subject are able to complete study procedures, such as spirometry, and Pulmonary Exercise test.", "candidate_expression": "((Interstitial Lung Disease) AND (Pulmonary Exercise test) AND (Pulmonary Hypertension) AND (age) AND (at least 18 years) AND (confirmed) AND (spirometry) AND (study procedures))"}
{"candidate_id": "LLM03281", "doc_id": "NCT02627560_exc", "case_bucket": "or", "source_criterion": "pregnant or breastfeeding known thromboembolic disease or with high risk of thromboembolism, warranting extra anticoagulation in connection with the procedure known allergy to tranexamic acid/Cyklokapron®", "candidate_expression": "((Cyklokapron) AND (allergy) AND (extra anticoagulation) AND (tranexamic acid) AND ((breastfeeding) OR (pregnant)) AND ((thromboembolic disease) OR (thromboembolism high risk of)))"}
{"candidate_id": "LLM03282", "doc_id": "NCT02105090_inc", "case_bucket": "or", "source_criterion": "elective procedure weight over 40 kg American Society of Anesthesiology class I-III first upper GI endoscopy procedure finnish or/and swedish speaking", "candidate_expression": "((American Society of Anesthesiology class I-III) AND (elective procedure) AND (endoscopy procedure first upper GI) AND (finnish speaking) AND (swedish speaking) AND (weight over 40 kg))"}
{"candidate_id": "LLM03283", "doc_id": "NCT01177891_exc", "case_bucket": "or", "source_criterion": "Blood donation of more than 450ml in the previous three months. Subject with an abnormal karyotype in favor of Turner syndrome or having a premutation of the FMR1 gene or a syndromic form Subject exclusion period in another study without direct individual benefit Subject refusing to sign the consent form", "candidate_expression": "((Blood donation of more than 450ml in the previous three months) AND (Subject exclusion period in another study without direct individual benefit) AND (Subject refusing to sign the consent form) AND (Turner syndrome) AND (abnormal karyotype) AND (premutation of the FMR1 gene) AND (syndromic form))"}
{"candidate_id": "LLM03284", "doc_id": "NCT03115320_inc", "case_bucket": "other", "source_criterion": "- Patient with IVF cycle and therefore having frozen-thawed embryos Regular menstruation cycle Patient's willingness to participate in the study", "candidate_expression": "((IVF cycle) AND (Patient's willingness to participate in the study) AND (Regular menstruation cycle) AND (frozen-thawed embryos))"}
{"candidate_id": "LLM03285", "doc_id": "NCT03029078_inc", "case_bucket": "or", "source_criterion": "Patient harboring a GRE or CRE bacteria Colonization confirmed by our microbiology department, including at least 3 positives swabs in the last month", "candidate_expression": "((Colonization confirmed by our microbiology department) AND (swabs at least 3 positives in the last mont) AND ((CRE bacteria) OR (GRE bacteria)))"}
{"candidate_id": "LLM03286", "doc_id": "NCT03247738_exc", "case_bucket": "or", "source_criterion": "Inability to provide written informed consent Known history of prior intracranial bleeding On treatment with a P2Y12 receptor antagonist (ticlopidine, clopidogrel, prasugrel, ticagrelor) in the prior 10 days Known allergies to aspirin, ticagrelor or cangrelor On treatment with oral anticoagulant Treatment with glycoprotein IIb/IIIa inhibitors Fibrinolytics within 24 hours Active bleeding High risk of bleeding Known platelet count <80x106/mL Known hemoglobin <10 g/dL Intubated patients (prior to randomization) Known creatinine clearance <30 mL/minute or on hemodialysis. Known severe hepatic dysfunction Patients with sick sinus syndrome (SSS) or high degree AV block without pacemaker protection Current treatment with drugs interfering with CYP3A4 metabolism (to avoid interaction with ticagrelor): Ketoconazole, itraconazole, voriconazole, clarithromycin, nefazodone, ritonavir, saquinavir, nelfinavir, indinavir, atazanavir, and telithromizycin. Pregnant or lactating females.", "candidate_expression": "((Active bleeding) AND (CYP3A4 metabolism interfering with) AND (Fibrinolytics within 24 hours) AND (Inability to provide written informed consent) AND (Intubated prior to randomization) AND (P2Y12 receptor antagonist prior 10 days) AND (SSS) AND (allergies) AND (anticoagulant oral) AND (bleeding High risk) AND (drugs) AND (females) AND (glycoprotein IIb/IIIa inhibitors) AND (hemoglobin <10 g/dL) AND (hepatic dysfunction severe) AND (intracranial bleeding prior) AND (platelet count <80x106/mL) AND (ticagrelor) AND NOT (pacemaker) AND ((aspirin) OR (cangrelor) OR (ticagrelor)) AND ((creatinine clearance <30 mL/minute) OR (hemodialysis)) AND ((AV block high degree) OR (sick sinus syndrome)) AND ((Ketoconazole) OR (atazanavir) OR (clarithromycin) OR (indinavir) OR (itraconazole) OR (nefazodone) OR (nelfinavir) OR (ritonavir) OR (saquinavir) OR (telithromizycin) OR (voriconazole)) AND ((Pregnant) OR (lactating)) AND ((clopidogrel) OR (prasugrel) OR (ticagrelor) OR (ticlopidine)))"}
{"candidate_id": "LLM03287", "doc_id": "NCT03117608_inc", "case_bucket": "or", "source_criterion": "Patients provided written informed consent; Patients aged between 18 and 75 years; Knee symptomatic OA (Kellgren-Lawrence grade 1-4) Failure of conservative treatment for at least 3 months; Patients agreed to actively participate in the rehabilitation protocol and follow-up program; Male or female patients; Women of childbearing age had to use a proven method to prevent pregnancy, before the surgical treatment.", "candidate_expression": "((1-4) AND (Failure) AND (Kellgren-Lawrence grade) AND (Male) AND (OA Knee) AND (Women) AND (aged) AND (agreed to actively participate in the follow-up program) AND (agreed to actively participate in the rehabilitation protocol) AND (before the surgical treatment) AND (between 18 and 75 years) AND (childbearing age) AND (conservative treatment) AND (female) AND (for at least 3 months) AND (method to prevent pregnancy) AND (provided written informed consent) AND (surgical treatment) AND (symptomatic) AND (the surgical treatment))"}
{"candidate_id": "LLM03288", "doc_id": "NCT02990403_exc", "case_bucket": "or", "source_criterion": "having experienced severe allergies, trauma history and/or operation history within 3 months. with a history of mental illness and/or family history of mental illness limb disabled. taking medicine within one month. suffering major events or having mood swings. having internal and surgical disease(after having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine) chromosome aberrations in anyone of the couple. patients who have drugs contraindications", "candidate_expression": "((after having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine) AND (allergies) AND (anyone of the couple) AND (blood routine) AND (chromosome aberrations) AND (contraindications) AND (drugs) AND (electrocardiogram) AND (family history) AND (having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine) AND (hepatic function) AND (history) AND (internal disease) AND (limb disabled) AND (major events) AND (medicine) AND (mental illness) AND (mood swings) AND (operation) AND (physical examination) AND (renal function) AND (severe) AND (surgical) AND (surgical disease) AND (trauma) AND (urine routine) AND (within 3 months) AND (within one month))"}
{"candidate_id": "LLM03289", "doc_id": "NCT02918851_inc", "case_bucket": "other", "source_criterion": "Habitual exerciser defined as = 30 minutes of at least moderate or high intensity exercise = 3 times per week. After consent, and at the subsequent screening visit, a VO2 max test will be performed, and subjects with a low value (< 35 mL/kg/min) will be excluded (screen failure). Based on our previous experience, we anticipate that <10% of the subjects will fall into this category Men: (0.006012 x H3) + (14.6 x W) + 604 = TBV Women: (0.005835 x H3) + (15 x W) + 183 = TBV [H=height in inches; W=weight in pounds] Has access to transportation to visit the blood collection facility and to return to Stony Brook for all study visits.", "candidate_expression": "((Men) AND (TBV (0.005835 x H3) + (15 x W) + 183) AND (TBV (0.006012 x H3) + (14.6 x W) + 604 =) AND (Women))"}
{"candidate_id": "LLM03290", "doc_id": "NCT02546856_inc", "case_bucket": "other", "source_criterion": "Patient with \"de novo\" heart Failure and LVEF <= 40% admitted in hospital, without contraindications for BB prescription with cardiologist up-titration prescription and without having achieved BB target dose previous discharge and signing informed consent.", "candidate_expression": "((BB) AND (LVEF <= 40%) AND (admitted) AND (heart Failure de novo) AND (hospital) AND NOT (contraindications))"}
{"candidate_id": "LLM03291", "doc_id": "NCT02897856_exc", "case_bucket": "or", "source_criterion": "Cardiac arrest Head trauma Drowning Congenital heart disease Inborn errors of metabolism Electrolyte imbalance (hypocalcaemia, hyponatremia and hypoglycemia) Hemodynamic instability Allergy to benzodiazepines Focal seizures with preserved level of consciousness", "candidate_expression": "((Allergy) AND (Cardiac arrest) AND (Congenital heart disease) AND (Drowning) AND (Electrolyte imbalance) AND (Focal seizures) AND (Head trauma) AND (Hemodynamic instability) AND (Inborn errors of metabolism) AND (benzodiazepines) AND (hypocalcaemia) AND (hypoglycemia) AND (hyponatremia) AND (preserved level of consciousness))"}
{"candidate_id": "LLM03292", "doc_id": "NCT01497639_exc", "case_bucket": "other", "source_criterion": "previous brain surgery; cognitive impairment (< 120 points on the Mattis Dementia Rating Scale) moderate-to-severe depression (> 25 points on the Beck Depression Inventory) marked brain atrophy as detected by magnetic resonance imaging other medical or psychiatric coexisting disorders that could increase the surgical risk or interfere with completion of the trial", "candidate_expression": "((< 120 points) AND (> 25 points) AND (Beck Depression Inventory) AND (Mattis Dementia Rating Scale) AND (brain atrophy) AND (brain surgery) AND (cognitive impairment) AND (depression) AND (magnetic resonance imaging) AND (moderate-to-severe) AND (other medical or psychiatric coexisting disorders that could increase the surgical risk or interfere with completion of the trial) AND (previous))"}
{"candidate_id": "LLM03293", "doc_id": "NCT02053246_exc", "case_bucket": "or", "source_criterion": "Other causes of heart failure other than diastolic dysfunction, such as restrictive cardiomyopathy or infiltrative cardiomyopathy Women who are pregnant or nursing Liver cirrhosis, Primary valvular disease Acute coronary syndrome Causes of PH other than that of heart failure, such as: chronic thromboembolic PH, sickle-cell disease, or sarcoidosis Severe bradycardia or greater than 1st degree heart block Decompensated heart failure Current use of a third generation beta-blocker (nebivolol, carvedilol, or labetalol) or high dose of any beta-blockers (greater than 100 mg daily of metoprolol, or equivalent)", "candidate_expression": "((Acute coronary syndrome) AND (Causes of PH) AND (Liver cirrhosis) AND (Primary valvular disease) AND (Women) AND (any beta-blockers high dose) AND (heart failure) AND (heart failure Decompensated) AND (metoprolol greater than 100 mg daily) AND (third generation beta-blocker) AND NOT (heart failure) AND NOT (diastolic dysfunction) AND ((nursing) OR (pregnant)) AND ((chronic thromboembolic PH) OR (sarcoidosis) OR (sickle-cell disease)) AND ((bradycardia Severe) OR (heart block greater than 1st degree)) AND ((carvedilol) OR (labetalol) OR (nebivolol)) AND ((infiltrative cardiomyopathy) OR (restrictive cardiomyopathy)))"}
{"candidate_id": "LLM03294", "doc_id": "NCT02205502_exc", "case_bucket": "or", "source_criterion": "contraindication to ketamine and lidocaine patients involved to other studies more or equal to American Society of Anesthesiologist (ASA) class III not alert", "candidate_expression": "((American Society of Anesthesiologist (ASA) class) AND (III more or equal to) AND (contraindication) AND (not alert) AND (patients involved to other studies) AND ((ketamine) OR (lidocaine)))"}
{"candidate_id": "LLM03295", "doc_id": "NCT02924090_exc", "case_bucket": "or", "source_criterion": "Relative contraindications to ECT therapy (recent MI or CVA, increased intracranial pressure, intracranial mass lesion, intracranial aneurysm, epilepsy, known cardiac arrhythmia, pheochromocytoma, pregnancy) Contraindications to etomidate (sepsis, primary or secondary adrenal insufficiency, porphyria) DSM-V diagnosis of a lifetime history of psychotic spectrum disorder Drug or alcohol dependence, or abuse within the past 3 months, soy-bean oil allergy", "candidate_expression": "((Contraindications) AND (ECT therapy) AND (Relative contraindications) AND (adrenal insufficiency) AND (etomidate) AND (porphyria) AND (psychotic spectrum disorder DSM-V lifetime history) AND (sepsis) AND (soy-bean oil allergy) AND ((cardiac arrhythmia) OR (epilepsy) OR (intracranial aneurysm) OR (intracranial mass lesion) OR (intracranial pressure increased) OR (pheochromocytoma) OR (pregnancy)) AND ((primary) OR (secondary)) AND ((Drug abuse) OR (Drug dependence) OR (alcohol abuse) OR (alcohol dependence)) AND ((CVA) OR (MI)))"}
{"candidate_id": "LLM03296", "doc_id": "NCT03344887_inc", "case_bucket": "other", "source_criterion": "All patients (excluding neonates) requiring one or more allogeneic RBC transfusions for the treatment of anemia will be included.", "candidate_expression": "((RBC transfusions requiring one or more allogeneic) AND (anemia) AND (treatment) AND NOT (neonates))"}
{"candidate_id": "LLM03297", "doc_id": "NCT03304496_inc", "case_bucket": "or", "source_criterion": "Men and women older than 18 years, scheduled consecutively to perform a coronary procedure in the department of hemodynamics of the National Institute of Cardiology \"Ignacio Chavez\". Patients may have any of the following indications for cardiac catheterization: Thoracic pain under study. Stable chronic coronary disease. Acute myocardial infarction with ST segment elevation, not perfused (without timely reperfusion therapy) with less than 4 weeks of evolution. Acute myocardial infarction with ST-segment elevation, successful thrombolytic therapy, which will undergo drug-invasive therapy. Acute myocardial infarction without ST segment elevation. Unstable angina. Any acute coronary syndrome, to intervene non-infarct-related artery. Disease of any heart valve. Myocarditis or pericarditis. Dilated cardiomyopathy. Patients in renal or cardiac transplantation protocol for any etiology. Congenital heart disease that requires knowing the coronary anatomy prior to surgical correction. The planned procedure can be any of the following: For diagnostic purposes (coronary angiography only, left catheterization, left and right catheterization). For therapeutic purposes: percutaneous coronary intervention (PCI), with or without stent placement. A priori access must be right or left radial artery. Radial arterial pulse may be present or absent by palpation. Modified Allen or Barbeau test should be positive (presence of collateral palmar flow).", "candidate_expression": "((Acute myocardial infarction) AND (Barbeau test) AND (Congenital heart disease knowing the coronary anatomy prior to surgical correction.) AND (Disease heart valve) AND (Men) AND (Modified Allen test) AND (Myocarditis) AND (PCI) AND (ST segment elevation) AND (ST-segment elevation) AND (Thoracic pain) AND (Unstable angina) AND (access priori right radial artery left radial artery) AND (acute coronary syndrome) AND (cardiac catheterization) AND (cardiac transplantation) AND (cardiomyopathy Dilated) AND (chronic coronary disease Stable) AND (collateral palmar flow presence) AND (coronary angiography) AND (coronary angiography only) AND (coronary procedure scheduled) AND (department of hemodynamics) AND (drug-invasive therapy will undergo) AND (indications) AND (intervene artery) AND (left catheterization) AND (palpation) AND (percutaneous coronary intervention therapeutic) AND (pericarditis) AND (procedure) AND (pulse Radial arterial present absent) AND (renal transplantation) AND (right catheterization) AND (stent placement) AND (the National Institute of Cardiology \"Ignacio Chavez\") AND (thrombolytic therapy successful) AND (women) AND (years older than 18) AND NOT (reperfusion therapy timely with less than 4 weeks of evolution) AND NOT (ST segment elevation))"}
{"candidate_id": "LLM03298", "doc_id": "NCT02340169_exc", "case_bucket": "or", "source_criterion": "Has other dermatological conditions that may interfere with clinical assessments Allergy or sensitivity to corticosteroids or any drug hypersensitivity or intolerance that would compromise patient safety or study results History of an adverse reaction to Cortrosyn™ or similar test reagents Chronic infectious disease, system or organ disorder or other medical condition that would place patient at undue risk by study participation", "candidate_expression": "((Allergy) AND (Chronic infectious disease, system or organ disorder or other medical condition that would place patient at undue risk by study participation) AND (Cortrosyn) AND (Has other dermatological conditions that may interfere with clinical assessments) AND (adverse reaction) AND (corticosteroids) AND (hat would compromise patient safety or study results) AND (sensitivity) AND (similar) AND (test reagents) AND ((Cortrosyn) OR (similar test reagents)) AND ((drug hypersensitivity) OR (drug intolerance)))"}
{"candidate_id": "LLM03299", "doc_id": "NCT02748330_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03300", "doc_id": "NCT02121145_exc", "case_bucket": "or", "source_criterion": "Primary groups: Vaccination against typhoid fever within 5 years before dosing. History of clinical typhoid fever, clinical paratyphoid A or B fever. Immunization with any other vaccine (oral or parenteral) within 4 weeks prior to study start or planned vaccination during the study Current intake of antibiotics or end of antibiotic therapy <8 days before first IMP administration Chronic (longer than 14 days) administration of immunosuppressants or other immune-modifying drugs within 6 months before the first dose of investigational vaccine; oral corticosteroids in dosages of =0.5 mg/kg/d prednisolone or equivalent are excluded; inhaled or topical steroids are allowed Acute or chronic clinically significant gastrointestinal disease", "candidate_expression": "((<8 days before first IMP administration) AND (=0.5 mg/kg/d) AND (Chronic administration) AND (Current) AND (History) AND (Primary groups) AND (Vaccination against typhoid fever) AND (any other) AND (clinically significant) AND (dosages) AND (dosing) AND (during the study) AND (end of) AND (excluded) AND (first IMP administration) AND (gastrointestinal disease) AND (investigational vaccine) AND (longer than 14 days) AND (oral corticosteroids) AND (other) AND (planned) AND (prednisolone or equivalent) AND (study start) AND (the first dose of investigational vaccine) AND (the study) AND (typhoid fever) AND (within 4 weeks prior to study start) AND (within 5 years before dosing) AND (within 6 months before the first dose of investigational vaccine) AND ((oral) OR (parenteral)) AND ((Immunization with vaccine) OR (vaccination)) AND ((antibiotic therapy) OR (antibiotics)) AND ((immune-modifying drugs) OR (immunosuppressants)) AND ((Acute) OR (chronic)) AND ((clinical paratyphoid A fever) OR (clinical paratyphoid B fever) OR (clinical typhoid fever)))"}
```
