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
{"candidate_id": "LLM06251", "doc_id": "NCT03138577_inc", "case_bucket": "other", "source_criterion": "Undergoing right upper extremity surgery with supraclavicular block as the primary anesthetic Age greater than or equal to 18 years of age American Society of Anesthesiologists (ASA) physical status 1 to 3 Able to give informed consent", "candidate_expression": "((1 to 3) AND (Able to give informed consent) AND (Age) AND (American Society of Anesthesiologists (ASA) physical status) AND (Undergoing) AND (greater than or equal to 18 years) AND (primary anesthetic) AND (right upper extremity surgery) AND (supraclavicular block))"}
{"candidate_id": "LLM06252", "doc_id": "NCT02247128_exc", "case_bucket": "or", "source_criterion": "Need for long-term oral anticoagulation; Drug-eluting stent implantation within 3 months prior to TAVI procedure; Bare-metal stent implantation within 1 month prior to TAVI procedure; Allergy or intolerance to aspirin or clopidogrel. Drug-eluting stent implantation within 3 months prior to TAVI procedure; Bare-metal stent implantation within 1 month prior to TAVI procedure; Allergy or intolerance to (N)OAC or clopidogrel.", "candidate_expression": "(((N)OAC) AND (Allergy) AND (Bare-metal stent) AND (Drug-eluting stent) AND (Need for) AND (TAVI procedure) AND (aspirin) AND (clopidogrel) AND (implantation) AND (intolerance) AND (long-term oral anticoagulation) AND (within 1 month prior to TAVI procedure) AND (within 3 months prior to TAVI procedure))"}
{"candidate_id": "LLM06253", "doc_id": "NCT02983214_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure, history of ventricular tachycardia, ventricular fibrillation or multifocal ventricular extrasystoles or QTc prolongation. Patients with atrial fibrillation taking any anticoagulant therapy or patients with a history of cardioembolic ischemic stroke or hemorrhagic stroke. Patients with a history (= 12 months) of acute coronary syndrome receiving dual antiplatelet therapy, or patients receiving monotherapy with aspirin. Patients with hepatic impairment (child-Pugh staging, calibration = 5) or renal impairment (creatinine clearance = 30ml / min), recent peptic ulcer, a history of hypersensitivity to cilostazol, cancer patients undergoing treatment.", "candidate_expression": "((acute coronary syndrome = 12 months) AND (anticoagulant therapy) AND (aspirin) AND (atrial fibrillation) AND (child-Pugh staging calibration = 5) AND (cilostazol) AND (creatinine clearance = 30ml / min) AND (dual antiplatelet therapy) AND (monotherapy) AND (treatment) AND ((Congestive heart failure) OR (QTc prolongation) OR (multifocal ventricular extrasystoles) OR (ventricular fibrillation) OR (ventricular tachycardia history of)) AND ((hemorrhagic stroke) OR (ischemic stroke cardioembolic)) AND ((cancer) OR (hepatic impairment) OR (hypersensitivity history of) OR (peptic ulcer recent) OR (renal impairment)))"}
{"candidate_id": "LLM06254", "doc_id": "NCT02563535_inc", "case_bucket": "other", "source_criterion": "age>18 years critical limb ischemia (Rutherford class 4-6) angiographic stenosis>50% or occlusion of at least one tibial vessel of at least 40mm for which an interventional treatment is scheduled", "candidate_expression": "((4-6) AND (>18 years) AND (>50%) AND (Rutherford class) AND (age) AND (angiographic stenosis) AND (at least 40mm) AND (at least one) AND (critical) AND (interventional treatment) AND (limb ischemia) AND (occlusion) AND (scheduled) AND (tibial vessel))"}
{"candidate_id": "LLM06255", "doc_id": "NCT02498483_exc", "case_bucket": "other", "source_criterion": "Newborns of substance abusing mothers. Newborns with any contraindications to routine circumcision, anatomical or hematologic.", "candidate_expression": "((Newborns) AND (circumcision) AND (contraindications) AND (mothers) AND (substance abusing))"}
{"candidate_id": "LLM06256", "doc_id": "NCT02466113_exc", "case_bucket": "or", "source_criterion": "With severe comorbidities, such as cardiovascular disease, chronic obstructive pulmonary disease, diabetes mellitus, and chronic renal dysfunction. With bad compliance or contraindication to enrollment. Pregnant woman or lactating woman. With contraindication to receive adjuvant chemotherapy.", "candidate_expression": "((Pregnant) AND (adjuvant chemotherapy) AND (bad compliance) AND (comorbidities severe) AND (contraindication) AND (contraindication to enrollment) AND (lactating) AND (woman) AND ((bad compliance) OR (contraindication to enrollment)) AND ((cardiovascular disease) OR (chronic obstructive pulmonary disease) OR (chronic renal dysfunction) OR (diabetes mellitus)))"}
{"candidate_id": "LLM06257", "doc_id": "NCT01696617_inc", "case_bucket": "or", "source_criterion": "Age : 18-65 Patients with major depressive disorder according to DSM-IV criteria that have lasted >8 weeks MADRS total score of 18 or higher Patients who responded inadequately (a score of >18 on the MADRS) to first-line antidepressant treatment of 4 week duration Current use of standard antidepressant treatment in monotherapy or combination of 2 antidepressants : escitalopram (10 - 20mg/d), fluoxetine(20 - 40mg/d), paroxetine CR(25 - 50mg/d), sertraline(100 - 150mg/d), mirtazapine (15 - 45mg/d), duloxetine (30 - 60mg/d) or venlafaxine ER(150-225mg/d)", "candidate_expression": "((Age 18-65) AND (DSM-IV criteria) AND (MADRS score of 18 or higher) AND (MADRS score of >18) AND (antidepressant first-line of 4 week) AND (duloxetine 30 - 60mg/d) AND (escitalopram 10 - 20mg/d) AND (fluoxetine 20 - 40mg/d) AND (major depressive disorder lasted >8 weeks) AND (mirtazapine 15 - 45mg/d) AND (paroxetine CR 25 - 50mg/d) AND (responded inadequately) AND (sertraline 100 - 150mg/d) AND (venlafaxine ER 150-225mg/d) AND ((antidepressant standard monotherapy) OR (antidepressants 2)))"}
{"candidate_id": "LLM06258", "doc_id": "NCT01064752_exc", "case_bucket": "or", "source_criterion": "1. Taking a tetracycline within 6 months or history of adverse reaction to minocycline or another tetracycline. 2. Enhanced risk from lumbar puncture, including documented or suspected cerebral mass lesion predisposing to brain herniation or bleeding diathesis. 3. Pregnancy or expectation of pregnancy during the study. 4. Active opportunistic infection or active neurological disease that might confound evaluation. 5. ADC Stage > 1. 6. Hemoglobin < 10 Gms/dL. 7. BUN or creatine above the normal limits. 8. Taking other drugs known to reduce the metabolism of minocycline and thus increase the probability of toxicity.", "candidate_expression": "((ADC Stage > 1) AND (BUN) AND (Hemoglobin < 10 Gms/dL) AND (Pregnancy) AND (adverse reaction history) AND (bleeding diathesis) AND (brain herniation) AND (cerebral mass lesion predisposing to brain herniation or bleeding diathesis) AND (creatine) AND (lumbar puncture Enhanced risk documented suspected) AND (minocycline) AND (neurological disease active) AND (opportunistic infection Active opportunistic) AND (pregnancy expectation) AND (tetracycline) AND (tetracycline within 6 months))"}
{"candidate_id": "LLM06259", "doc_id": "NCT02175186_inc", "case_bucket": "or", "source_criterion": "Age between 20 and 80 years Patients undergoing percutaneous coronary intervention and need to take dual antiplatelet therapy continuously at least 12weeks Modified Lanza Score grade 0-1 measured by upper gastrointestinal endoscopy mild gastrointestinal symptom Creatinen in blood = 3mg/dl BUN = 50mg/dl Birilubin = 3mg/dl AST and ALT = 80U/L", "candidate_expression": "((0-1) AND (= 3mg/dl) AND (= 50mg/dl) AND (= 80U/L) AND (ALT) AND (AST) AND (Age) AND (BUN) AND (Birilubin) AND (Creatinen) AND (Modified Lanza Score grade) AND (at least 12weeks) AND (between 20 and 80 years) AND (continuously) AND (gastrointestinal symptom) AND (mild) AND (upper gastrointestinal endoscopy) AND ((dual antiplatelet therapy) OR (percutaneous coronary intervention)))"}
{"candidate_id": "LLM06260", "doc_id": "NCT03247413_exc", "case_bucket": "or", "source_criterion": "patient not previously scheduled for radiofrequency ablation of the cervical, thoracic, or lumbar facets, or sacroiliac joints on anticoagulation have a pacemaker age less than 18 years old non-English speaking", "candidate_expression": "((English speaking) AND (age) AND (anticoagulation) AND (cervical facets) AND (less than 18 years old) AND (lumbar facets) AND (non) AND (not) AND (pacemaker) AND (previously) AND (radiofrequency ablation) AND (sacroiliac joints) AND (scheduled for) AND (thoracic facets))"}
{"candidate_id": "LLM06261", "doc_id": "NCT01794793_inc", "case_bucket": "other", "source_criterion": "Patient is currently participating in a Novartis Oncology sponsored study receiving pasireotide (LAR and/or s.c.) and has fulfilled all required assessments in the parent study (unless the study is being terminated) and patients that are benefiting from the study drug have no other alternatives Patient is currently benefiting from the treatment with pasireotide, as determined by the investigator Patient has demonstrated compliance, as assessed by the investigator, with the parent study requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures Written informed consent obtained prior to enrolling in roll-over study and receiving study medication • If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness", "candidate_expression": "((Patient is currently participating in a Novartis Oncology sponsored study receiving pasireotide (LAR and/or s.c.) and has fulfilled all required assessments in the parent study (unless the study is being terminated) and patients that are benefiting from the study drug have no other alternatives) AND (Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures) AND (Written informed consent obtained prior to enrolling in roll-over study and receiving study medication • If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness))"}
{"candidate_id": "LLM06262", "doc_id": "NCT03484091_inc", "case_bucket": "other", "source_criterion": "Symptomatic primary knee osteoarthritis with failed conservative treatment at least 3 months Kellgren-Lawrence grade I-III Gave informed consent Can do questionnaires", "candidate_expression": "((Can do questionnaires) AND (Gave informed consent) AND (Kellgren-Lawrence grade I-III) AND (conservative treatment failed at least 3 months) AND (osteoarthritis Symptomatic primary knee))"}
{"candidate_id": "LLM06263", "doc_id": "NCT02754583_exc", "case_bucket": "other", "source_criterion": "School districts that are too difficult to reach (more than a 3-hour walk from the farthest place reachable by a four-wheel drive vehicle) School districts in the 2 urban regions of the study area Refusal of village chief All residents residing near to the well sites that are randomly selected for this study. Refusal of participant [or parent/guardian]", "candidate_expression": "((Refusal of participant [or parent/guardian]) AND (School districts in the 2 urban regions of the study area) AND (School districts that are too difficult to reach) AND (near to the well sites) AND (residing) AND (walk from the farthest place reachable by a four-wheel drive vehicle more than a 3-hour))"}
{"candidate_id": "LLM06264", "doc_id": "NCT02926989_inc", "case_bucket": "other", "source_criterion": "Acutely ill hospitalised children Need for intravenous fluid therapy", "candidate_expression": "((Acutely ill) AND (children) AND (hospitalised) AND (intravenous fluid therapy Need for))"}
{"candidate_id": "LLM06265", "doc_id": "NCT02385045_inc", "case_bucket": "or", "source_criterion": "• All patients attending for a routine diagnostic endoscopic procedure at St Mary's Hospital NHS Trust for dyspepsia and abdominal pain", "candidate_expression": "((St Mary's Hospital NHS Trust) AND (diagnostic endoscopic procedure) AND ((abdominal pain) OR (dyspepsia)))"}
{"candidate_id": "LLM06266", "doc_id": "NCT02798237_inc", "case_bucket": "or", "source_criterion": "= 20years of age; diagnosis of stroke (>6months); sedentary or insufficiently active; have a writing medical permission to participate in the training program.", "candidate_expression": "((age = 20years) AND (insufficiently active) AND (sedentary) AND (stroke >6months))"}
{"candidate_id": "LLM06267", "doc_id": "NCT02877485_inc", "case_bucket": "other", "source_criterion": "Age greater than 18 NOSE score greater than 55 Nasal septal deviation on exam", "candidate_expression": "((Age greater than 18) AND (NOSE score greater than 55) AND (Nasal septal deviation))"}
{"candidate_id": "LLM06268", "doc_id": "NCT03337581_exc", "case_bucket": "or", "source_criterion": "allergic to dexmedetomidine, similar active ingredients or excipients G-6-PD deficiency a history of arrhythmia, bronchial and cardiovascular diseases, abnormal liver function and so on a history of use of alpha 2 receptor agonists or antagonists.", "candidate_expression": "((G-6-PD deficiency) AND (abnormal liver function) AND (allergic) AND (alpha 2 receptor agonists) AND (alpha 2 receptor antagonists) AND (arrhythmia) AND (bronchial diseases) AND (cardiovascular diseases) AND (dexmedetomidine) AND (excipients) AND (history) AND (similar active ingredients))"}
{"candidate_id": "LLM06269", "doc_id": "NCT03473132_inc", "case_bucket": "other", "source_criterion": "LVAD on warfarin requiring temporary interruption of anticoagulation for procedures", "candidate_expression": "((LVAD) AND (requiring temporary interruption of anticoagulation for procedures) AND (warfarin))"}
{"candidate_id": "LLM06270", "doc_id": "NCT02318446_inc", "case_bucket": "other", "source_criterion": "Diagnosed epileptic patients of either sex with age between 10-19 yrs (<19yrs), coming to the medicine Out Patient /In Patient Departments and undergoing AED therapy for more than 6 months. Epileptics with high homocysteine levels i.e. > 10.9 µmol/L (Normal homocysteine levels are 4.3-9.9 µmol/L for male and 3.3-7.2 µmol/L for female adolescent and a high homocysteine concentration is deaned as at least 11.4 µmol/L for male and at least 10.4 µmol/L for female. Gender mean of high homocysteine concentration is 10.9 µmol/L) [5]", "candidate_expression": "((AED therapy for more than 6 months) AND (In Patient Departments) AND (Out Patient Departments) AND (age between 10-19 yrs <19yrs) AND (epileptic) AND (homocysteine levels high > 10.9 µmol/L))"}
{"candidate_id": "LLM06271", "doc_id": "NCT02787863_inc", "case_bucket": "or", "source_criterion": "Individuals of both sexes from 18 years with a diagnosis of community-acquired pneumonia, COPD or Bronchial Asthma; The presence of signed and dated informed consent to participate in a clinical study; The ability to perform the requirements of the Protocol; For women of childbearing age is a negative result of a pregnancy test before vaccination. community-acquired pneumonia: the presence of radiologically confirmed infiltration of the lung tissue; the presence of at least two of the following clinical signs: acute fever early in the disease (temperature > 38.0°C), cough with sputum, the physical signs of pneumonia (focus of crepitate and/or fine bubble rales, bronchial breathing hard, shortening of percussion sounds), leukocytosis > 10*10 9 /l and/or stab shift > 10%; the occurrence of the disease outside the hospital and the organized groups (such as nursing homes, sanatoriums, etc.). COPD: dyspnea: progressive (worsens over time), increases with exertion, persistent; chronic cough (may appear sporadically and may be unproductive); chronic expectoration; the impact of risk factors in the medical history (Smoking, occupational dust pollutants and chemicals); widespread wheeze on auscultation of the chest and/or distant wheezing in the chest; family history of COPD; spirometric data confirming the presence of fixed bronchial obstruction.", "candidate_expression": "((> 10%) AND (> 10*10 9 /l) AND (> 38.0°C) AND (COPD) AND (For women of childbearing age is a negative result of a pregnancy test before vaccination.) AND (The ability to perform the requirements of the Protocol;) AND (at least two) AND (both sexes) AND (community-acquired pneumonia) AND (early in the disease) AND (family history) AND (fixed bronchial obstruction) AND (from 18 years) AND (increases with exertion) AND (infiltration of the lung tissue) AND (persistent) AND (physical signs) AND (pneumonia) AND (progressive) AND (radiologically) AND (radiologically confirmed) AND (temperature) AND (widespread) AND (worsens over time) AND ((acute fever) OR (cough with sputum)) AND ((bronchial breathing hard) OR (crepitate rales) OR (fine bubble rales) OR (shortening of percussion sounds)) AND ((leukocytosis) OR (stab shift)) AND ((Smoking) OR (occupational dust pollutants and chemicals)) AND ((COPD) OR (chronic cough) OR (chronic expectoration) OR (distant wheezing in the chest) OR (dyspnea) OR (risk factors) OR (spirometric) OR (wheeze on auscultation of the chest)) AND ((Bronchial Asthma) OR (COPD) OR (community-acquired pneumonia)))"}
{"candidate_id": "LLM06272", "doc_id": "NCT02034019_inc", "case_bucket": "other", "source_criterion": "Has a cataract and is expected to undergo clear corneal cataract surgery with phacoemulsification and implantation of a posterior chamber intraocular lens Has a potential post-operative pinhole corrected Snellen VA of at least 20/200 or better in both eyes", "candidate_expression": "((cataract) AND (clear corneal cataract surgery with phacoemulsification implantation of a posterior chamber intraocular lens) AND (pinhole corrected Snellen VA at least 20/200 or better))"}
{"candidate_id": "LLM06273", "doc_id": "NCT02845427_inc", "case_bucket": "other", "source_criterion": "Primary total hip arthroplasty (THA)", "candidate_expression": "((THA) AND (total hip arthroplasty Primary))"}
{"candidate_id": "LLM06274", "doc_id": "NCT02747940_inc", "case_bucket": "or", "source_criterion": "Control: devoid of any systemic or neurological diseases Chronic migraine: by ICHD-III (International Classification of Headache Disorder) criteria Fibromyalgia: by ACR (American College of Rheumatology) 2010 criteria", "candidate_expression": "((Chronic migraine ICHD-III International Classification of Headache Disorder) AND (Fibromyalgia ACR 2010 criteria American College of Rheumatology) AND (neurological diseases) AND (systemic diseases))"}
{"candidate_id": "LLM06275", "doc_id": "NCT02713087_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for supine-positioned elective craniotomy for supratentorial malignant and non-malignant brain tumors 3 cm or larger (measured as the largest diameter in any plane on MR images) ASA (American Society of Anesthesiologist) status 1-3 (27) Written informed consent from participating patients", "candidate_expression": "((1-3) AND (27) AND (3 cm or larger) AND (ASA status) AND (American Society of Anesthesiologist status) AND (MR) AND (Written informed consent from participating patients) AND (brain tumors) AND (largest diameter in any plane) AND (malignant) AND (non) AND (scheduled) AND (supine-positioned elective craniotomy) AND (supratentorial))"}
```
