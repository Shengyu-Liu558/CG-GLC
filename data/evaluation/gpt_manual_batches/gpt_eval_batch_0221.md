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
{"candidate_id": "LLM05501", "doc_id": "NCT01684501_exc", "case_bucket": "or", "source_criterion": "score level D on the SIGAM mobility grade have experienced 1 or more falls in the last month before the study have a residual limb length which does not allow for seven inches clearance of bracket attachment for the PowerFoot the residual limb must be stable in volume (no change in socket or socket padding in last 6 months) and without pain that limits function the sound-side (contralateral) lower extremity must be free of impediments that affect gait, range of motion, or limb muscle activity Any diagnosed cardiovascular, pulmonary, neurological, and/ or orthopedic conditions that would interfere with subject participation", "candidate_expression": "((1 or more) AND (SIGAM mobility grade) AND (does not) AND (does not allow for seven inches clearance of bracket attachment) AND (falls) AND (free) AND (in the last month before the study) AND (interfere with subject participation) AND (last month before the study) AND (level D) AND (lower extremity) AND (residual limb length) AND ((impediments that affect gait) OR (impediments that affect limb muscle activity) OR (impediments that affect range of motion)) AND ((cardiovascular conditions) OR (neurological conditions) OR (orthopedic conditions) OR (pulmonary conditions)))"}
{"candidate_id": "LLM05502", "doc_id": "NCT02580630_exc", "case_bucket": "or", "source_criterion": "Earlier operations in the foot and leg, that is judged to complicate training known arthritis. known diabetes Leg ulcerations or infections in the foot. Judged unable to comply with the training protocol. Daily use of pain killers Glucocorticosteroid injection to the diseased achilles tendon within the last 6 months. Earlier allergic reactions to glucocorticosteroid or local anesthetic. Pregnancy or planning to become pregnant BMI above 30.", "candidate_expression": "((BMI above 30) AND (Glucocorticosteroid) AND (Judged unable to comply with the training protocol.) AND (allergic reactions Earlier) AND (arthritis) AND (diabetes) AND (diseased achilles tendon) AND (injection within the last 6 months) AND (pain killers Daily) AND ((glucocorticosteroid) OR (local anesthetic)) AND ((Pregnancy) OR (pregnant planning to become)) AND ((Leg ulcerations) OR (infections in the foot)))"}
{"candidate_id": "LLM05503", "doc_id": "NCT01650792_inc", "case_bucket": "other", "source_criterion": "Diagnosis of heart failure according to Framingham criteria Informed consent Age 18 years or above", "candidate_expression": "((18 years or above) AND (Age) AND (Framingham criteria) AND (Informed consent) AND (heart failure))"}
{"candidate_id": "LLM05504", "doc_id": "NCT03615508_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05505", "doc_id": "NCT02420015_inc", "case_bucket": "other", "source_criterion": "Currently smoke at least ten cigarettes a day Have been smoking for at least one year Meet criteria for schizophrenia, schizoaffective disorder, or another psychotic disorder based on structured clinical interview Can speak and write fluent conversational English Are between 18 and 70 years of age Are willing to make a smoking cessation attempt Score 26 or higher on the Montreal Cognitive Assessment", "candidate_expression": "((26 or higher) AND (Are willing to make a smoking cessation attempt) AND (Montreal Cognitive Assessment) AND (age) AND (at least one year) AND (at least ten cigarettes a day) AND (between 18 and 70 years) AND (psychotic disorder) AND (schizoaffective disorder) AND (schizophrenia) AND (smoke) AND (smoking))"}
{"candidate_id": "LLM05506", "doc_id": "NCT02365870_exc", "case_bucket": "other", "source_criterion": "Unstable medical disease of comorbid psychiatric disease Dementia Subjects with less than one year duration of Parkinson's Current treatment with a dopamine agonist", "candidate_expression": "((Current) AND (Dementia) AND (Parkinson's) AND (Unstable medical disease) AND (comorbid psychiatric disease) AND (dopamine agonist) AND (less than one year duration))"}
{"candidate_id": "LLM05507", "doc_id": "NCT02935855_inc", "case_bucket": "or", "source_criterion": "non-valvular atrial fibrillation nondiabetic patients type 1 and 2 diabetic patients", "candidate_expression": "((atrial fibrillation) AND (diabetic) AND (non) AND (non-valvular) AND (type 1) AND (type 2))"}
{"candidate_id": "LLM05508", "doc_id": "NCT03124329_exc", "case_bucket": "or", "source_criterion": "Molar teeth Milller Class 4 recession defects Pregnancy (Self-reported) Smoking Uncontrolled local or systemic diseases that affects wound healing (diabetes, autoimmune or inflammatory disorders) Past history of systemic steroid use over 2 weeks within the last 2 years Poor oral hygiene on a non-compliant individual Ibuprofen Allergy/interlerance Anticoagulant therapy (e.g. Warfarin, Plavix, etc.), will not be automatic exclusion but patients will be required to have INR test performed and have values between 2.0 to 3. Physician consultation will be requested to determine whether anticoagulant therapy can be discontinued for 3 days prior to surgery. Objection to blood draw or application of blood products Students and staff from USC Ostrow school of Dentistry will not be recruited for this study", "candidate_expression": "((Allergy) AND (Anticoagulant therapy) AND (Class 4) AND (INR test) AND (Ibuprofen) AND (Milller) AND (Molar teeth) AND (Past history) AND (Plavix) AND (Poor oral hygiene) AND (Pregnancy) AND (Smoking) AND (Uncontrolled) AND (Warfarin) AND (anticoagulant therapy) AND (autoimmune disorders) AND (between 2.0 to 3) AND (diabetes) AND (diseases local) AND (inflammatory disorders) AND (interlerance) AND (non-compliant) AND (over 2 weeks) AND (recession defects) AND (systemic diseases) AND (systemic steroid) AND (that affects wound healing) AND (within the last 2 years))"}
{"candidate_id": "LLM05509", "doc_id": "NCT03472508_inc", "case_bucket": "or", "source_criterion": "(1)= 45 years old; (2)A diagnosis or previous diagnosis of essential hypertension, including anyone currently taking antihypertensive drugs; or for those who have not taken antihypertensive drugs within the last 2 weeks, two consecutive examinations were conducted at least one day apart, and both sitting blood pressure (mean value of 3 measurements) met the following criteria: diastolic blood pressure (DBP) =90 mmHg or systolic blood pressure (SBP) =140 mmHg (the second blood pressure was measured at V1); (3)If a study participant is a woman of childbearing age, she agrees to use a reliable contraceptive method during the trial; (4)Voluntarily participates and has signed an informed consent form. (1)Completed MTHFR C677T gene polymorphism detection in run-in period or MTHFR C677T genotype already known in advance; (2)Exhibited good tolerance to enalapril and good overall medication compliance (>80%) in run-in period or previously exhibited good tolerance and adherence to ACEI drugs in previous medication history. (3)Voluntarily continues to participate in this study.", "candidate_expression": "((ACEI drugs) AND (Voluntarily participates) AND (antihypertensive drugs currently) AND (childbearing age) AND (continues to participate in this study Voluntarily) AND (enalapril) AND (essential hypertension) AND (good adherence to ACEI drugs) AND (good tolerance to ACEI drugs) AND (good tolerance to enalapril) AND (old = 45 years) AND (overall medication compliance good >80%) AND (signed an informed consent) AND (sitting blood pressure two consecutive at least one day apart) AND (woman) AND NOT (antihypertensive drugs within the last 2 weeks) AND ((diastolic blood pressure (DBP) =90 mmHg) OR (systolic blood pressure (SBP) =140 mmHg)) AND ((gene polymorphism detection MTHFR C677T) OR (genotype already known MTHFR C677T)) AND ((diagnosis) OR (previous)))"}
{"candidate_id": "LLM05510", "doc_id": "NCT03177811_inc", "case_bucket": "or", "source_criterion": "Male and female patients, age 18-75 yrs. COPD diagnosed according to GOLD, FEV1 40-80% predicted, SpO2 =92% at 750 m. Born, raised and currently living at low altitude (<800m). Written informed consent.", "candidate_expression": "((COPD) AND (FEV1 40-80% predicted) AND (GOLD) AND (Male) AND (SpO2 =92% at 750 m) AND (Written informed consent) AND (age 18-75 yrs) AND (female))"}
{"candidate_id": "LLM05511", "doc_id": "NCT02983214_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure, history of ventricular tachycardia, ventricular fibrillation or multifocal ventricular extrasystoles or QTc prolongation. Patients with atrial fibrillation taking any anticoagulant therapy or patients with a history of cardioembolic ischemic stroke or hemorrhagic stroke. Patients with a history (= 12 months) of acute coronary syndrome receiving dual antiplatelet therapy, or patients receiving monotherapy with aspirin. Patients with hepatic impairment (child-Pugh staging, calibration = 5) or renal impairment (creatinine clearance = 30ml / min), recent peptic ulcer, a history of hypersensitivity to cilostazol, cancer patients undergoing treatment.", "candidate_expression": "((= 12 months) AND (= 30ml / min) AND (Congestive heart failure) AND (QTc prolongation) AND (acute coronary syndrome) AND (anticoagulant therapy) AND (aspirin) AND (atrial fibrillation) AND (calibration = 5) AND (cancer) AND (cardioembolic) AND (child-Pugh staging) AND (cilostazol) AND (creatinine clearance) AND (dual antiplatelet therapy) AND (hemorrhagic stroke) AND (hepatic impairment) AND (history) AND (history of) AND (hypersensitivity) AND (ischemic stroke) AND (monotherapy) AND (multifocal ventricular extrasystoles) AND (peptic ulcer) AND (recent) AND (renal impairment) AND (treatment) AND (ventricular fibrillation) AND (ventricular tachycardia))"}
{"candidate_id": "LLM05512", "doc_id": "NCT03233880_inc", "case_bucket": "other", "source_criterion": "primigravida, singleton pregnancy, maternal age 18-35 years, and pregnancy duration 16-20 weeks at the time of study inclusion.", "candidate_expression": "((16-20 weeks) AND (18-35 years) AND (at the time of study inclusion) AND (maternal age) AND (pregnancy duration) AND (primigravida) AND (singleton pregnancy))"}
{"candidate_id": "LLM05513", "doc_id": "NCT02525991_exc", "case_bucket": "or", "source_criterion": "Patient diagnosed with dementia. Patients with serious and unstable illnesses including current hepatic, renal, gastroenterologic, respiratory, cardiovascular (including ischemic heart disease and congestive heart failure), endocrinologic, neurologic (including stroke, transient ischemic attack, subarachnoidal bleeding, brain tumor, encephalopathy, and meningitis). Patients with a history of allergic reactions to loxapine or amoxapine Patients who have received an investigational drug within 30 days prior to the current agitation episode must be excluded. Patients who are considered by the investigator, for any reason, to be unable to self-administer the inhalation device.", "candidate_expression": "((Patients who are considered by the investigator, for any reason, to be unable to self-administer the inhalation device) AND (Patients who have received an investigational drug within 30 days prior to the current agitation episode must be excluded) AND (allergic reactions) AND (dementia serious unstable) AND ((congestive heart failure) OR (ischemic heart disease)) AND ((brain tumor) OR (encephalopathy) OR (meningitis) OR (stroke) OR (subarachnoidal bleeding) OR (transient ischemic attack)) AND ((amoxapine) OR (loxapine)) AND ((cardiovascular) OR (endocrinologic) OR (gastroenterologic) OR (hepatic) OR (neurologic) OR (renal) OR (respiratory)))"}
{"candidate_id": "LLM05514", "doc_id": "NCT00917891_exc", "case_bucket": "or", "source_criterion": "1. Currently pregnant or last pregnancy outcome within 3 months prior to enrolment 2. Currently breast-feeding 3. Participated in any other research study within 60 days prior to screening 4. Previously participated in any HIV vaccine study 5. Untreated urogenital infections (either symptomatic or asymptomatic) within 2 weeks prior to enrollment 6. Presence of abnormal physical finding on the vulva, vaginal walls or cervix during pelvic/speculum examination and/or colposcopy 7. History of significant urogenital or uterine prolapse, undiagnosed vaginal bleeding, urethral obstruction 8. Pap smear result at screening that requires cryotherapy, biopsy, treatment (other than for infection), or further evaluation 9. Any Grade 2, 3 or 4 baseline haematology, chemistry or urinalysis laboratory abnormality according to the DAIDS Table for Grading Adverse Experiences 10. Unexplained, undiagnosed abnormal bleeding per vagina, bleeding per vagina during or following vaginal intercourse, or gynaecologic surgery within 90 days prior to enrollment 11. Any history of anaphylaxis or severe allergy resulting in angioedema; or a history of sensitivity/allergy to latex 12. Any serious acute, chronic or progressive disease 13. Any condition(s) that, in the opinion of the investigator, might interfere with adherence to study requirements or evaluation of the study objectives", "candidate_expression": "((Any condition(s) that, in the opinion of the investigator, might interfere with adherence to study requirements or evaluation of the study objectives) AND (Any serious acute, chronic or progressive disease) AND (DAIDS Table for Grading Adverse Experiences Grade 2, 3 or 4 baseline Unexplained undiagnosed abnormal) AND (Pap smear at screening) AND (angioedema) AND (biopsy) AND (breast-feeding Currently enrolment) AND (chemistry) AND (cryotherapy) AND (disease) AND (further evaluation) AND (haematology) AND (laboratory) AND (laboratory abnormality) AND (last) AND (significant) AND (treatment) AND (urinalysis) AND (urogenital infections Untreated within 2 weeks prior to enrollment) AND ((asymptomatic) OR (symptomatic)) AND ((pregnancy outcome last within 3 months prior to enrolment) OR (pregnant Currently)) AND ((abnormal physical finding on the cervix) OR (abnormal physical finding on the vaginal walls) OR (abnormal physical finding on the vulva)) AND ((colposcopy) OR (pelvic examination) OR (speculum examination)) AND ((urogenital prolapse) OR (uterine prolapse)) AND ((urethral obstruction) OR (vaginal bleeding undiagnosed)) AND ((requires biopsy) OR (requires cryotherapy) OR (requires further evaluation) OR (requires treatment)) AND ((chemistry abnormality) OR (haematology abnormality) OR (urinalysis abnormality)) AND ((bleeding per vagina) OR (gynaecologic surgery within 90 days prior to enrollment)) AND ((during vaginal intercourse) OR (following vaginal intercourse)) AND ((allergy severe) OR (anaphylaxis)) AND ((allergy to latex) OR (sensitivity to latex)) AND ((acute) OR (chronic) OR (progressive) OR (serious)))"}
{"candidate_id": "LLM05515", "doc_id": "NCT02035904_exc", "case_bucket": "or", "source_criterion": "preexisting pectoral, axillar, thoracic homolateral pain habitual opioid consumption; drug-alcoholics addiction ; ICU postoperative recovery; kidney failure (creatinin > 2 g/dl, creatinin <clearance 30 ml/h) and/or hepatic failure (cholinesterase < 2000 UI); cardiac arrhythmias o; Epilepsy; Psychiatric, cognitive disorders, mental retardation; Coagulopathies (INR > 2, activated partial thromboplastin time - aPTT>44 sec); platelet count less than 100.000/mm3; BMI > 30; Allergies to study drugs.", "candidate_expression": "((Allergies) AND (BMI > 30) AND (Coagulopathies) AND (Epilepsy) AND (ICU postoperative recovery) AND (INR > 2) AND (Psychiatric, cognitive disorders) AND (activated partial thromboplastin time - aPTT >44 sec) AND (addiction drug) AND (alcoholics addiction) AND (axillar pain) AND (cardiac arrhythmias) AND (cholinesterase < 2000 UI) AND (creatinin <clearance 30 ml/h) AND (creatinin > 2 g/dl) AND (hepatic failure) AND (kidney failure) AND (mental retardation) AND (opioid consumption habitual) AND (pectoral pain) AND (platelet count less than 100.000/mm3) AND (study drugs) AND (thoracic pain))"}
{"candidate_id": "LLM05516", "doc_id": "NCT03366779_exc", "case_bucket": "or", "source_criterion": "Spondylolisthesis Grade II or higher. Subject requires uni or bilateral facetectomy to treat leg/back pain. Subject has back or non-radicular leg pain of unknown etiology. Prior surgery at the index lumbar level. Subject requiring a spine DEXA (i.e., patients with SCORE of = 6) with a T Score less than -2.0 at the index level. For patients with a herniation at L5/S1, the average T score of L1-L4 shall be used. Subject has clinically compromised vertebral bodies at the index level(s) due to any traumatic, neoplastic, metabolic, or infectious pathology. Subject has sustained pathologic fractures of the vertebra or multiple fractures of the vertebra or hip. Subject has scoliosis of greater than ten (10) degrees (both angular and rotational). Any metabolic disease bone disease that has not been stabilized for at least three months (e.g., Paget's disease, osteomalacia, osteogenesis imperfecta, thyroid and/or parathyroid gland disorder, etc.). Subject has an active infection either systemic or local. Subject has cauda equina syndrome or neurogenic bowel/bladder dysfunction. Subject has severe arterial insufficiency of the legs (Screening on physical examination= patients with diminution or absence of dorsalis pedis or posterior tibialis pulses. If diminished or absent by palpation, then an arterial ultrasound is required with vascular plethysmography. If the absolute arterial pressure is below 50mm of Hg at the calf or ankle level, then the patient is to be excluded) or other peripheral vascular disease). Subject has significant peripheral neuropathy, patient defined as a patient with Type I or Type II diabetes or similar systemic metabolic condition causing decreased sensation in a stocking-like or non-radicular and non-dermatomal distribution in the lower extremities. Subject has insulin-dependent diabetes mellitus. Subject is morbidly obese (defined as a body mass index >40, or weighs more than 100 lbs over ideal body weight). Subject has been diagnosed with active hepatitis, AIDS, or HIV. Subject has been diagnosed with rheumatoid arthritis or other autoimmune disease. Subject has a known allergy to titanium, polyethylene or polyester materials. Subject is pregnant or interested in becoming pregnant in the next two (2) years. Subject has active tuberculosis or has had tuberculosis in the past three (3) years. Subject has a history of active malignancy: A patient with a history of any invasive malignancy (except non-melanoma skin cancer), unless he/she has been treated with curative intent and there have been no signs or symptoms of the malignancy for at least two (2) years. Subject is immunologically suppressed, received steroids >1 month over the past year. Currently taking anticoagulants, other than aspirin, unless the patient can be taken off the anticoagulant for surgery. Subject has a current chemical/alcohol dependency or significant psychosocial disturbance. Subject has a life expectancy of less than three (3) years. Subject is currently involved in another investigational study. Subject is incarcerated.", "candidate_expression": "((= 6) AND (>1 month) AND (>40) AND (Grade) AND (II or higher) AND (L1-L4) AND (L5/S1) AND (Prior) AND (SCORE) AND (Screening on physical examination) AND (Spondylolisthesis) AND (Subject is currently involved in another investigational study.) AND (T Score) AND (absolute arterial pressure) AND (active) AND (active malignancy) AND (allergy) AND (anticoagulants) AND (arterial insufficiency) AND (arterial ultrasound) AND (aspirin) AND (average T score) AND (been stabilized) AND (below 50mm of Hg) AND (clinically compromised vertebral bodies) AND (decreased sensation) AND (diabetes mellitus) AND (except) AND (excluded) AND (facetectomy) AND (for at least three months) AND (for at least two (2) years) AND (fractures of the vertebra) AND (greater than ten (10) degrees) AND (herniation) AND (history) AND (in the next two (2) years) AND (incarcerated) AND (index level) AND (index level(s)) AND (index lumbar level) AND (infection) AND (insulin-dependent) AND (interested in becoming) AND (invasive) AND (legs) AND (less than -2.0) AND (less than three (3) years) AND (life expectancy) AND (lower extremities) AND (malignancy) AND (morbidly obese) AND (more than 100 lbs over ideal body weight) AND (multiple) AND (no) AND (non-melanoma skin cancer) AND (not) AND (other) AND (other than) AND (over the past year) AND (palpation) AND (pathologic) AND (peripheral neuropathy) AND (peripheral vascular disease) AND (requiring) AND (scoliosis) AND (severe) AND (significant) AND (signs or symptoms of the malignancy) AND (similar) AND (spine DEXA) AND (surgery) AND (treated with curative intent) AND (unknown etiology) AND (vascular plethysmography) AND ((non-dermatomal distribution) OR (non-radicular distribution) OR (stocking-like distribution)) AND ((body mass index) OR (weighs)) AND ((AIDS) OR (HIV) OR (hepatitis)) AND ((back pain) OR (non-radicular leg pain)) AND ((autoimmune disease) OR (rheumatoid arthritis)) AND ((polyester) OR (polyethylene) OR (titanium)) AND ((pregnant)) AND ((in the past three (3) years) OR (tuberculosis)) AND ((immunologically suppressed) OR (steroids)) AND ((alcohol dependency) OR (chemical dependency) OR (psychosocial disturbance)) AND ((infectious pathology) OR (metabolic pathology) OR (neoplastic pathology) OR (traumatic pathology)) AND ((bilateral) OR (uni)) AND ((fractures of the hip) OR (fractures of the vertebra)) AND ((angular) OR (rotational)) AND ((Paget's disease) OR (osteogenesis imperfecta) OR (osteomalacia) OR (parathyroid gland disorder) OR (thyroid)) AND ((bone disease) OR (metabolic disease)) AND ((local) OR (systemic)) AND ((cauda equina syndrome) OR (neurogenic bladder dysfunction) OR (neurogenic bowel dysfunction)) AND ((back pain) OR (pain leg)) AND ((diminution or absence of dorsalis pedis) OR (diminution or absence of posterior tibialis pulses)) AND ((ankle level) OR (calf level)) AND ((absent) OR (diminished)) AND ((Type I) OR (Type II)) AND ((diabetes) OR (systemic metabolic condition)))"}
{"candidate_id": "LLM05517", "doc_id": "NCT02607319_exc", "case_bucket": "or", "source_criterion": "Evidence of low ovarian reserve by at least one of the following: AMH = 1,5 ng/mL and/or basal CD 3 FSH = 10 mIU/mL and/or basal CD 3 Estradiol = 60 ng/mL and/or previous egg collection yield = 3 oocytes. Preexisting medical condition (thyroid disease, diabetes mellitus, hypertension, pulmonary conditions, cardiac condition…). Severe male factor infertility (Total motile sperm count < 5 million/ml and/or normal WHO morphology <20%). Hypersensitivity to Heparin or its derivatives. Acquired thrombophilia. Active hemorrhage or increased risk of bleeding due to impairment of homeostasis. Severe impairment of liver or pancreatic function. Severe renal insufficiency (Creatinine Clearance < 30 ml/min). Injuries to or operations on the central nervous system, eyes and ears within the last 2 months. Disseminated Intravascular Coagulation (DIC) attributable to heparin-induced thrombocytopenia. Acute bacterial endocarditis and endocarditis lenta. Any organic lesion with high risk of bleeding (e.g.: active peptic ulcer, hemorrhagic stroke, cerebral aneurysm or cerebral neoplasms).", "candidate_expression": "((Creatinine Clearance < 30 ml/min) AND (DIC) AND (Disseminated Intravascular Coagulation) AND (Heparin) AND (Hypersensitivity) AND (heparin-induced thrombocytopenia) AND (impairment of homeostasis) AND (low ovarian reserve) AND (male factor infertility Severe) AND (organic lesion risk of bleeding) AND (renal insufficiency Severe) AND (thrombophilia Acquired) AND ((cardiac condition) OR (diabetes mellitus) OR (hypertension) OR (pulmonary conditions) OR (thyroid disease)) AND ((Total motile sperm count < 5 million/ml) OR (normal WHO morphology <20%)) AND ((Active hemorrhage) OR (risk of bleeding increased)) AND ((AMH = 1,5 ng/mL) OR (basal CD 3 Estradiol = 60 ng/mL) OR (basal CD 3 FSH = 10 mIU/mL) OR (egg collection yield = 3 oocytes)) AND ((impairment of liver) OR (impairment of pancreatic function)) AND ((Injuries) OR (operations)) AND ((central nervous system) OR (ears) OR (eyes)) AND ((Acute bacterial endocarditis) OR (endocarditis lenta)) AND ((active peptic ulcer) OR (cerebral aneurysm) OR (cerebral neoplasms) OR (hemorrhagic stroke)))"}
{"candidate_id": "LLM05518", "doc_id": "NCT02269137_inc", "case_bucket": "or", "source_criterion": "30 min or more of (1) continuous clinical seizure activities or (2) recurrent seizure activities without recovery(returning to baseline)between seizures; clinical data is complete.", "candidate_expression": "((30 min or more) AND (continuous) AND (recurrent) AND (seizure) AND (without recovery))"}
{"candidate_id": "LLM05519", "doc_id": "NCT02299947_exc", "case_bucket": "or", "source_criterion": "Prior trombosis or myocardial infarction, congenital coagulation disorder, use of anti-coagulants prior to surgery, prior thoracic surgery, pregnancy, pre-operative fibrinogen concentration <1g/L", "candidate_expression": "((anti-coagulants prior to surgery) OR (congenital coagulation disorder) OR (fibrinogen concentration pre-operative <1g/L) OR (myocardial infarction) OR (pregnancy) OR (thoracic surgery prior) OR (trombosis Prior))"}
{"candidate_id": "LLM05520", "doc_id": "NCT02196285_exc", "case_bucket": "or", "source_criterion": "Serious adverse reaction to any vaccination, as respiratory difficulty, angioedema and anaphylaxis; Acute or chronic disease, as diabetes, heart disease, systemic arterial hypertension; Use of anti-allergic with antigen injections in a maximum timeline of 14 days before the vaccination; Use of immunoglobulin in the past 12 months before the study vaccination; Use of blood products within 12 months before the vaccination; Use of any vaccine type within 30 days before the vaccination of the study; Chronic use of any medication, except homeopathy, and trivial ones, as nasal physiologic solution and vitamins; Previous immunosuppressive or cytotoxic medication, in the last 6 months. Individuals who have made use of this kind of medication in non-immunosuppressant doses, as nasal corticosteroid for allergic rhinitis of topic corticosteroid for non-complicated dermatitis, for more than 14 days, are allowed to be included in the study. Use of any kind of medication under investigation within one year before the vaccination. Unstable asthma or which may have required urgent care, hospitalization or intubation within the last 2 years, or which requires use of oral or intravenous corticosteroid. Coagulopathies diagnosed by a physician or report of capillary fragility (ex: bruises or bleedings without justifiable cause; Convulsions, except the ones caused by fever, before 2 years old; Psychiatric disease which difficults the adherence to the protocol, such as psychosis, obsessive-compulsive disorders, bipolar disease under treatment, diseases which require treatment with lithium and suicidal ideas in the last 5 years from the inclusion; Active malignant (p.e. any kind of cancer) or treated disease, to which the individual may relapse during the study; Asplenia (absence of spleen or its removal); Positive HIV in the screening examination of history of any immunosuppressant disease; Positive serology for C hepatitis in the screening evaluation; Positive Antigen HBs in the screening evaluation; Alcoholism (CAGE criteria), used for detection of abusive drinkers or alcoholic, validated in the Brazilian population with sensibility of 88% and specificity of 83%, if two or more answers, among four possible, are afirmative(Mansur and Monteiro, 1983), or according to medical decision; Abuse of illicit drugs, according to medical decision; Acquired or congenital immunodeficiency; Allergy to the vaccine compounds, as egg, neomycin and gelatin.", "candidate_expression": "((2 years old) AND (Abuse of illicit drugs) AND (Active) AND (Alcoholism) AND (Allergy to the vaccine compounds) AND (Antigen HBs) AND (Asplenia) AND (CAGE criteria) AND (Chronic use) AND (Coagulopathies) AND (Convulsions) AND (Positive) AND (Psychiatric disease) AND (Unstable asthma) AND (absence of) AND (according to medical decision) AND (adverse reaction) AND (anaphylaxis) AND (angioedema) AND (anti-allergic) AND (antigen injections) AND (any kind) AND (any medication) AND (any vaccine type) AND (before 2 years old) AND (bipolar disease) AND (blood products) AND (cancer) AND (capillary fragility) AND (caused by fever) AND (difficults the adherence to the protocol) AND (diseases which require treatment with lithium) AND (during the study) AND (except) AND (fever) AND (homeopathy) AND (hospitalization) AND (immunoglobulin) AND (in the last 5 years from the inclusion) AND (in the last 6 months) AND (in the past 12 months before the study vaccination) AND (in the screening evaluation) AND (in the screening examination) AND (intravenous corticosteroid) AND (intubation) AND (lithium) AND (malignant) AND (maximum timeline of 14 days before the vaccination) AND (medication under investigation) AND (obsessive-compulsive disorders) AND (oral corticosteroid) AND (psychosis) AND (respiratory difficulty) AND (screening evaluation) AND (screening examination) AND (serology for C hepatitis) AND (suicidal ideas) AND (the inclusion) AND (the study) AND (the study vaccination) AND (the vaccination) AND (the vaccination of the study) AND (to which the individual may relapse) AND (to which the individual may relapse during the study) AND (treated) AND (treatment) AND (treatment with lithium) AND (trivial ones) AND (under treatment) AND (urgent care) AND (vaccination) AND (vaccine compounds) AND (within 12 months before the vaccination) AND (within 30 days before the vaccination of the study) AND (within one year before the vaccination) AND (within the last 2 years) AND (without justifiable cause) AND ((diabetes) OR (heart disease) OR (systemic arterial hypertension)) AND ((spleen) OR (spleen removal)) AND ((HIV) OR (immunosuppressant disease)) AND ((Acute disease) OR (chronic disease)) AND ((Acquired immunodeficiency) OR (congenital immunodeficiency)) AND ((egg) OR (gelatin) OR (neomycin)) AND ((nasal physiologic solution) OR (vitamins)) AND ((cytotoxic medication) OR (immunosuppressive medication)) AND ((required hospitalization) OR (required intubation) OR (required urgent care)) AND ((requires use of intravenous corticosteroid) OR (requires use of oral corticosteroid)) AND ((bleedings) OR (bruises)) AND ((malignant disease) OR (treated disease)))"}
{"candidate_id": "LLM05521", "doc_id": "NCT02152696_exc", "case_bucket": "or", "source_criterion": "Hemodynamically unstable in need of acute treatment Most recent hCG > 5000 mIU/mL Patient obtaining care in relation to a recently completed pregnancy (delivery, spontaneous or elective abortion) Diagnosis of gestational trophoblastic disease Subject unwilling or unable to comply with study procedures Known hypersensitivity to MTX Presence of clinical contraindications for treatment with MTX Prior medical or surgical management of this gestation Subject unwilling to accept a blood transfusion", "candidate_expression": "((> 5000 mIU/mL) AND (Hemodynamically unstable) AND (MTX) AND (Most recent) AND (Subject unwilling to accept a blood transfusion) AND (gestation) AND (gestational trophoblastic disease) AND (hCG) AND (hypersensitivity to MTX) AND ((medical management) OR (surgical management)))"}
{"candidate_id": "LLM05522", "doc_id": "NCT02528604_inc", "case_bucket": "other", "source_criterion": "Patients with symptomatic persistent atrial fibrillation of less than 1-year duration. Patients must be over 65 years old. Patients give informed consent prior to participating in this study.", "candidate_expression": "((Patients give informed consent prior to participating in this study) AND (atrial fibrillation symptomatic persistent less than 1-year) AND (old over 65 years))"}
{"candidate_id": "LLM05523", "doc_id": "NCT02590315_exc", "case_bucket": "other", "source_criterion": "Personal history of breast cancer A terminal illness Patients who are unable to give informed consent Breast implants", "candidate_expression": "((Breast implants) AND (Personal history) AND (breast cancer) AND (terminal illness) AND (unable to give informed consent))"}
{"candidate_id": "LLM05524", "doc_id": "NCT03195153_inc", "case_bucket": "or", "source_criterion": "diabetic patient; therapy with aspirin and insulin; patient well responders", "candidate_expression": "((aspirin) AND (diabetic) AND (insulin) AND (well responders))"}
{"candidate_id": "LLM05525", "doc_id": "NCT02399033_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
```
