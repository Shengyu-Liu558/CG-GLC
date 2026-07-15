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
{"candidate_id": "LLM05626", "doc_id": "NCT02431559_inc", "case_bucket": "or", "source_criterion": "1. Subjects must have recurrent or persistent platinum-resistant epithelial ovarian, fallopian tube, or primary peritoneal carcinoma with measureable disease (as defined by RECIST 1.1.) after first or second line platinum-based chemotherapy, for which treatment with PLD is indicated. Platinum-based therapy is defined as treatment with carboplatin, cisplatin or another organoplatinum compound. Platinum-resistant is defined as having a platinum-free interval (PFI) of < 12 months after first- or second-line platinum-based chemotherapy, or having disease progression while receiving second-line platinum-based chemotherapy. Subjects are allowed to have received, but are not required to have received: one additional cytotoxic regimen and/or PARP inhibitor for management of recurrent or persistent disease. biologic therapy (e.g., bevacizumab) as part of their primary treatment regimen or part of their treatment for management of recurrent or persistent disease. 2. Histologic documentation of the original primary tumor. 3. Documented radiographic disease progression < 12 months after the last dose of first- or second-line platinum-based chemotherapy. 4. Subjects in Phase 2 must have disease amenable to biopsy and must be willing to undergo pre- and post-treatment tumor biopsies. Optional for Phase 1. Note: archival tissue will be requested for all subjects preferably from primary tumor site prior to cancer treatment; however, archival tissue is not a requirement for study entry. 5. ECOG performance status of 0 or 1. 6. Laboratory parameters for vital functions should be in the normal range. Laboratory abnormalities that are not clinically significant are generally permitted, except for the following laboratory parameters, which must be within the ranges specified, regardless of clinical significance: Hemoglobin: ≥ 9 g/dL Neutrophil count: ≥ 1.5 x 109/L Platelet count: ≥ 100,000/mm3 Serum creatinine, ≤ 1.5x Institutional Upper Limit of Normal (ULN), or Creatinine Clearance ≥ 50 mL/min (by Cockcroft-Gault formula) Serum bilirubin: ≤ 1.2 mg/dL AST/ALT: ≤ 2.5 x ULN Alkaline phosphatase: ≤ 2.5 x ULN 7. Age ≥18 years. 8. Able and willing to give valid written informed consent. 9. Body weight > 30 kg", "candidate_expression": "((AST/ALT ≤ 2.5 x ULN) AND (Able and willing to give valid written informed consent.) AND (Age ≥18 years) AND (Alkaline phosphatase ≤ 2.5 x ULN) AND (Body weight > 30 kg) AND (Creatinine Clearance ≥ 50 mL/min Cockcroft-Gault formula) AND (ECOG performance status 0 or 1) AND (Hemoglobin ≥ 9 g/dL) AND (Histologic documentation) AND (Laboratory parameters for vital functions normal range) AND (Neutrophil count ≥ 1.5 x 109/L) AND (PLD) AND (Platelet count ≥ 100,000/mm3) AND (Platinum-based therapy) AND (Platinum-resistant) AND (Serum bilirubin ≤ 1.2 mg/dL) AND (Serum creatinine ≤ 1.5x Institutional Upper Limit of Normal (ULN)) AND (bevacizumab) AND (biologic therapy) AND (disease) AND (disease amenable to biopsy) AND (disease progression) AND (disease progression < 12 months after the last dose of first- or second-line platinum-based chemotherapy) AND (indicated) AND (measureable disease) AND (original primary tumor) AND (platinum-free interval (PFI) < 12 months after first- or second-line platinum-based chemotherapy) AND (primary treatment regimen) AND (radiographic) AND (second-line platinum-based chemotherapy) AND (treatment) AND (treatment with PLD indicated) AND (willing to undergo pre- and post-treatment tumor biopsies) AND ((carcinoma epithelial ovarian) OR (carcinoma fallopian tube) OR (primary peritoneal carcinoma)) AND ((persistent) OR (recurrent)) AND ((after first line platinum-based chemotherapy first line platinum-based chemotherapy) OR (after second line platinum-based chemotherapy second line platinum-based chemotherapy)) AND ((another organoplatinum compound) OR (carboplatin) OR (cisplatin)) AND ((PARP inhibitor) OR (cytotoxic regimen)))"}
{"candidate_id": "LLM05627", "doc_id": "NCT01912677_exc", "case_bucket": "or", "source_criterion": "Indication for emergent cesarean or known fetal anomaly Anti-hypertensive therapy received in the past 12 hours History of eclampsia or other adverse CNS complication (e.g., stroke or PRES) in this pregnancy Actively wheezing at time of enrollment or history of asthma complications Known coronary artery disease or type I DM with microvascular complications or signs of heart failure or clinical dissection of the aorta", "candidate_expression": "((Anti-hypertensive therapy past 12 hours) AND (emergent cesarean) AND (enrollment) AND (microvascular complications) AND ((Indication) OR (fetal anomaly)) AND ((asthma complications) OR (wheezing at time of enrollment)) AND ((coronary artery disease) OR (dissection of the aorta) OR (heart failure) OR (type I DM)) AND ((CNS complication) OR (eclampsia)) AND ((PRES) OR (stroke)))"}
{"candidate_id": "LLM05628", "doc_id": "NCT02566928_exc", "case_bucket": "or", "source_criterion": "The patient is unwilling to provide informed consent acutely sick (for example, crying, wheezing, bleeding, screaming or shaken) unable to participate in a discussion about the study", "candidate_expression": "((The patient is unwilling to provide informed consent) AND (acutely sick) AND (bleeding) AND (crying) AND (screaming) AND (shaken) AND (wheezing))"}
{"candidate_id": "LLM05629", "doc_id": "NCT02046395_inc", "case_bucket": "or", "source_criterion": "Type 2 Diabetes Hypertension Estimated glomerular filtration rate (eGFR) > 30 ml/min Use of Ace Inh and ARB for control of blood pressure who are willing to be placed on alternate drug(s) in the washout period for blood pressure control", "candidate_expression": "((> 30 ml/min) AND (Estimated glomerular filtration rate (eGFR)) AND (Hypertension) AND (Type 2 Diabetes) AND (control of blood pressure) AND (willing to be placed on alternate drug(s) in the washout period for blood pressure control) AND ((ARB) OR (Ace Inh)))"}
{"candidate_id": "LLM05630", "doc_id": "NCT02678377_inc", "case_bucket": "or", "source_criterion": "Undergoing mid-urethral sling surgery Have symptoms of both stress and urgency urinary incontinence Able to consent, fill out study documents, and complete all study procedures and follow-up visits At least 18 years of age English speaking Be able and willing to learn clean intermittent self catheterization technique", "candidate_expression": "((Able to consent, fill out study documents, and complete all study procedures and follow-up visits) AND (age At least 18 years) AND (mid-urethral sling surgery) AND ((stress urinary incontinence) OR (urgency urinary incontinence)))"}
{"candidate_id": "LLM05631", "doc_id": "NCT02457442_inc", "case_bucket": "or", "source_criterion": "ASA physical status 1 or 2 Written informed consent Cardiovascular disease Pulmonary disease Liver disease CNS disease Alcohol or drug abuse Chronic intake of CNS active drugs Body mass index > 35 Diabetes mellitus Hypersensitivity or allergy to one of the study drugs", "candidate_expression": "((> 35) AND (ASA physical status) AND (Alcohol abuse) AND (Body mass index) AND (CNS active drugs) AND (CNS disease) AND (Cardiovascular disease) AND (Chronic intake) AND (Diabetes mellitus) AND (Liver disease) AND (Pulmonary disease) AND (Written informed consent) AND (drug abuse) AND (study drugs) AND ((Hypersensitivity) OR (allergy)) AND ((1) OR (2)))"}
{"candidate_id": "LLM05632", "doc_id": "NCT03560310_exc", "case_bucket": "or", "source_criterion": "Previously enrolled in this study (i.e. patient now at repeat encounter) Concomitant surgical procedure other than CABG Anticoagulant treatment after the operation (e.g. warfarin, direct thrombin inhibitors (dabigatran), FXa inhibitors (rivaroxaban, apixaban, heparin, low-molecular weight heparin, fondaparinux) Discharge from the operating hospital to an ICU at another hospital Pregnancy or lactation Known intolerance or contraindication to ticagrelor or ASA Any disorder that may interfere with drug absorption Any condition other than coronary artery disease with a life expectancy <12 months Known chronic liver disease, renal disease requiring dialysis or bleeding disorder Atrioventricular block II and III in patients without pacemaker Any other indication for dual antiplatelet therapy, i.e. recent stent implantation Debilitating stroke within 90 days before inclusion Previous intracranial bleeding Treatment with immunosuppressants (e.g. cyclosporine and tacrolimus) Treatment with strong CYP3A4-inhibitors (e.g. ketoconazole, clarithromycin, nefazodone, ritonavir or atazanavir) Any condition that in the opinion of the investigator may interfere with adherence to trial protocol", "candidate_expression": "((Anticoagulant treatment after the operation) AND (CABG other than) AND (Debilitating) AND (Discharge) AND (ICU) AND (Pregnancy) AND (condition life expectancy) AND (dabigatran) AND (dialysis requiring) AND (disorder may interfere with drug absorption) AND (dual antiplatelet therapy) AND (enrolled in this study Previously) AND (hospital another) AND (immunosuppressants) AND (indication) AND (intracranial bleeding Previous) AND (lactation) AND (operating hospital) AND (operation) AND (stent implantation recent) AND (stroke within 90 days before inclusion) AND (strong CYP3A4-inhibitors) AND (surgical procedure Concomitant) AND NOT (coronary artery disease) AND NOT (pacemaker) AND ((FXa inhibitors) OR (direct thrombin inhibitors) OR (warfarin)) AND ((apixaban) OR (fondaparinux) OR (heparin) OR (low-molecular weight heparin) OR (rivaroxaban)) AND ((contraindication) OR (intolerance)) AND ((ASA) OR (ticagrelor)) AND ((bleeding disorder) OR (chronic liver disease) OR (renal disease)) AND ((Atrioventricular block II) OR (Atrioventricular block III)) AND ((cyclosporine) OR (tacrolimus)) AND ((atazanavir) OR (clarithromycin) OR (ketoconazole) OR (nefazodone) OR (ritonavir)))"}
{"candidate_id": "LLM05633", "doc_id": "NCT01261832_inc", "case_bucket": "other", "source_criterion": "Acute Myocardial Infarction Undergoing Primary percutaneous coronary intervention.", "candidate_expression": "((Acute Myocardial Infarction) AND (Primary percutaneous coronary intervention))"}
{"candidate_id": "LLM05634", "doc_id": "NCT02041299_inc", "case_bucket": "or", "source_criterion": "Male or female = 2 years of age; Have sickle cell disease (confirmed by Hb electrophoresis or more specific tests) or other conditions with iron overload from repeated blood transfusions (see exclusion criteria for exceptions); Baseline LIC >7 mg/g dw (measured by MRI); Patients who have received no less than 20 transfusions of RBCs; Patients who have received at least 1 transfusion per year in the last 2 years and who are expected to have a continuing requirement (based on Investigator's judgement) during the duration of the trial", "candidate_expression": "((Baseline LIC >7 mg/g) AND (Hb electrophoresis) AND (MRI) AND (Male) AND (age = 2 years) AND (blood transfusions repeated) AND (expected to have a continuing requirement during the duration of the trial) AND (female) AND (more specific tests) AND (other conditions with iron overload) AND (sickle cell disease) AND (transfusion at least 1 per year in the last 2 years) AND (transfusions of RBCs no less than 20))"}
{"candidate_id": "LLM05635", "doc_id": "NCT02874092_inc", "case_bucket": "scope", "source_criterion": "RA cohort: Receiving MTX at stable doses of 10 to 25 mg weekly for at least 12 weeks, Have a DAS28 of 3.2 or higher (The level of disease activity is considered to be low if the DAS28 is 3.2 or less) (Prevoo et al., 1995) OA cohort: Diagnosis of osteoarthritis made by physician.", "candidate_expression": "((10 to 25 mg weekly) AND (3.2 or higher) AND (DAS28) AND (MTX) AND (OA) AND (RA) AND (for at least 12 weeks) AND (made by physician) AND (osteoarthritis) AND (stable doses))"}
{"candidate_id": "LLM05636", "doc_id": "NCT02526823_exc", "case_bucket": "or", "source_criterion": "Patients with severe complications or severe infection; Invasion of central nervous system; Patients with severe heart disease history, including ventricular tachycardia (VT), atrial fibrillation (AF), heart block, myocardial infarction (MI), congestive heart failure (CHF), coronary heart disease patients needed therapy; patients with severe allergic constitution, or those who are allergic to or intolerant of drug composition in chemotherapy regimens; with other malignant tumors in the past 5 years; patients received doxorubicin therapy, total cumulative dose of adriamycin was more than 300 mg/m2, total cumulative dose of epirubicin was more than 450 mg/m2; Patients participate in other clinical studies; Other patients who are not suitable for the study.", "candidate_expression": "((AF) AND (CHF) AND (Invasion central nervous system) AND (MI) AND (Patients) AND (Patients participate in other clinical studies) AND (VT) AND (adriamycin total cumulative dose more than 300 mg/m2) AND (allergic) AND (allergic severe) AND (atrial fibrillation) AND (chemotherapy regimens) AND (complications severe) AND (congestive heart failure) AND (coronary heart disease) AND (doxorubicin) AND (epirubicin total cumulative dose more than 450 mg/m2) AND (heart block) AND (heart disease severe) AND (infection severe) AND (intolerant) AND (malignant tumors other past 5 years) AND (myocardial infarction) AND (ventricular tachycardia))"}
{"candidate_id": "LLM05637", "doc_id": "NCT03164096_exc", "case_bucket": "or", "source_criterion": "Patients with coagulopathy or under anti-coagulation therapy. Gastrointestinal disease, motion sickness. diabetes mellitus. Patients with preeclampsia,", "candidate_expression": "((Gastrointestinal disease) AND (anti-coagulation therapy) AND (coagulopathy) AND (diabetes mellitus) AND (motion sickness) AND (preeclampsia))"}
{"candidate_id": "LLM05638", "doc_id": "NCT02937779_inc", "case_bucket": "other", "source_criterion": ">= 18 years old the day of inclusion Pregnancy Positive HBs Ag Informed consent obtained with information sheet given and explained and the consent form signed by the participant of the project investigator at the latest the day of the inclusion", "candidate_expression": "((HBs Ag Positive) AND (Informed consent obtained with information sheet given and explained and the consent form signed by the participant of the project investigator at the latest the day of the inclusio) AND (Pregnancy) AND (old >= 18 years))"}
{"candidate_id": "LLM05639", "doc_id": "NCT02225548_exc", "case_bucket": "or", "source_criterion": "Subject unwilling to cease use of any treatment for erectile dysfunction during the study, including oral medication, vacuum devices, constrictive devices, injections, urethral suppositories, gels, any over-the-counter or nonprescription medications, and products purchased via the internet Subject receiving dopamine agonists, nitrates, alpha-receptor blocking agents, or antihypertensive medication (see other exclusionary medications listed below) Subject with a history of syncope within the last 6 months prior to screening Subject with symptomatic postural hypotension (severe dizziness or fainting Subject with hypotension and a resting systolic blood pressure of < 90 mmHG or hypertension with a resting systolic blood pressure > 170 mmHG or a resting diastolic blood pressure > 110 mmHG Subject with any underlying cardiovascular condition, including unstable angina pectoris, which preclude sexual activity Subject with a history of myocardial infarction, stroke or life-threatening arrhythmia within 6 months prior to screening Subject with uncontrolled atrial fibrillation/flutter at screening (defined as ventricular response rate = 100 bpm) Subject with a bleeding disorder Subject with a history of prostatectomy because of prostate cancer, including nerve sparing techniques. Subjects with a history of surgical procedures for the treatment of benign prostate hypertrophy are permitted, with the exception of cryosurgery, cryotherapy or cryoablation Subject with hereditary degenerative retinal disorders such as retinitis pigmentosa Subject with a history of loss of vision because of non-arteritic anterior ischemic optic neuropathy (NAION), history of temporary or permanent loss of vision, including unilateral loss of vision Subject with a history of congenital QT prolongation Subject with a penile anatomical abnormality (e.g., penile fibrosis, fractures, or Peyronie's disease) which, in the investigator's opinion, could significantly impair sexual performance. This will be based on subject's reported medical history (penile exam not required) Subject with primary hypoactive sexual desire. Subject with a spinal cord injury Subject with a severe chronic or acute liver disease, history of moderate (Child-Pugh B), or severe (Child-Pugh C) hepatic impairment Subject with clinically significant chronic hematological disease which could lead to priapism such as sickle cell anemia, multiple myeloma, and leukemia Subject with active peptic ulceration Subject with a history of malignancy within the past 5 years (other than squamous or basal cell skin cancer) Subject with a history of a positive test for Hepatitis B surface antigen (HbsAg) or Hepatitis C Subject with a known hypersensitivity to any component of the investigational medications, monoamine oxidase inhibitors, phosphodiesterase type 5 inhibitors or phenylethylamines Subjects with a history of drug or alcohol abuse within the past 6 months Subjects currently consuming =5 units of alcohol per day Subject who is illiterate or unable to understand the Informed Consent Form, questionnaires or subject diary Subject who, in the opinion of the investigator, will be noncompliant with the visit schedule or study procedures Subject with any unstable medical, psychiatric, or substance abuse disorder that in the opinion of the investigator is likely to affect the subject's ability to complete the study or preclude the subject's participation in the study Diagnosis of any other neurologic disease Uncontrolled Diabetes (Hemoglobin A1C > 7.5)", "candidate_expression": "((< 90 mmHG) AND (= 100 bpm) AND (=5 units) AND (> 110 mmHG) AND (> 170 mmHG) AND (> 7.5) AND (B) AND (C) AND (Child-Pugh) AND (Diabetes) AND (Hemoglobin A1C) AND (NAION) AND (Uncontrolled) AND (active) AND (any other) AND (at screening) AND (benign prostate hypertrophy) AND (bleeding disorder) AND (cardiovascular condition) AND (cease use of) AND (chronic) AND (clinically significant) AND (congenital QT prolongation) AND (consuming alcohol per day) AND (could lead to priapism) AND (could significantly impair sexual performance) AND (currently) AND (during the study) AND (erectile dysfunction) AND (hematological disease) AND (hepatic impairment) AND (hereditary degenerative retinal disorders) AND (history of) AND (hypersensitivity) AND (hypertension) AND (hypotension) AND (illiterate) AND (impair sexual performance) AND (investigational) AND (life-threatening) AND (loss of vision) AND (malignancy) AND (moderate) AND (nerve sparing techniques) AND (neurologic disease) AND (non-arteritic anterior ischemic optic neuropathy) AND (noncompliant with the visit schedule or study procedure) AND (other than) AND (penile anatomical abnormality) AND (penile exam) AND (peptic ulceration) AND (permitted) AND (positive) AND (postural hypotension) AND (preclude) AND (priapism) AND (primary hypoactive sexual desire) AND (prostate cancer) AND (prostatectomy) AND (retinitis pigmentosa) AND (screening) AND (severe) AND (sexual activity) AND (spinal cord injury) AND (surgical procedures) AND (symptomatic) AND (syncope) AND (systolic blood pressure) AND (the past 6 months) AND (treatment) AND (unable to) AND (uncontrolled) AND (unilateral) AND (unstable) AND (unstable angina pectoris) AND (unwilling) AND (ventricular response rate) AND (with the exception of) AND (within 6 months prior to screening) AND (within the last 6 months prior to screening) AND (within the past 5 years) AND (within the past 6 months) AND ((nonprescription) OR (over-the-counter)) AND ((leukemia) OR (multiple myeloma) OR (sickle cell anemia)) AND ((basal cell skin cancer) OR (squamous skin cancer)) AND ((test for Hepatitis B surface antigen (HbsAg)) OR (test for Hepatitis C)) AND ((medications) OR (monoamine oxidase inhibitors) OR (phenylethylamines) OR (phosphodiesterase type 5 inhibitors)) AND ((alcohol abuse) OR (drug abuse)) AND ((understand the Informed Consent Form) OR (understand the questionnaires) OR (understand the subject diary)) AND ((medical disorder) OR (psychiatric disorder) OR (substance abuse disorder)) AND ((likely to affect the subject's ability to complete the study) OR (preclude the subject's participation in the study)) AND ((alpha-receptor blocking agents) OR (antihypertensive medication) OR (dopamine agonists) OR (nitrates)) AND ((dizziness) OR (fainting)) AND ((diastolic blood pressure) OR (systolic blood pressure)) AND ((arrhythmia) OR (myocardial infarction) OR (stroke)) AND ((atrial fibrillation) OR (atrial flutter)) AND ((constrictive devices) OR (gels) OR (injections) OR (medications) OR (oral medication) OR (urethral suppositories) OR (vacuum devices)) AND ((cryoablation) OR (cryosurgery) OR (cryotherapy)) AND ((loss of vision)) AND ((permanent) OR (temporary)) AND ((Peyronie's disease)) OR (penile fibrosis) OR (penile fractures)) AND ((acute liver disease) OR (chronic liver disease)))"}
{"candidate_id": "LLM05640", "doc_id": "NCT02055053_inc", "case_bucket": "or", "source_criterion": "Age 18 or older with unilateral or bilateral inguinal herna for laparoscopic repair American Society of Anesthesiology (ASA) Class I and II", "candidate_expression": "((18 or older) AND (Age) AND (American Society of Anesthesiology (ASA) Class) AND (I and II) AND (bilateral) AND (for laparoscopic repair) AND (inguinal herna) AND (laparoscopic repair) AND (unilateral))"}
{"candidate_id": "LLM05641", "doc_id": "NCT02318446_exc", "case_bucket": "or", "source_criterion": "Pregnancy and lactation Patients with diabetes, Ischemic heart disease (IHD), stroke, malignancy and psychiatric diseases are excluded from study. The patients receiving vitamin supplements or who had clinical evidence for an acute illness, renal dysfunction, thyroid dysfunction, chronic inflammatory diseases, inborn errors of homocysteine, cobalamin or folate metabolism, or any other condition known to interfere with homocysteine metabolism will be excluded Patients who are already involved in any other trial. Patients not willing to fill consent/ assent form are also excluded from study.", "candidate_expression": "((Patients not willing to fill consent/ assent form are also excluded from study.) AND (acute illness) AND ((Pregnancy) OR (lactation)) AND ((chronic inflammatory diseases) OR (clinical evidence for an acute illness) OR (renal dysfunction) OR (thyroid dysfunction) OR (vitamin supplements)) AND ((condition known to interfere with homocysteine metabolism) OR (inborn errors of cobalamin metabolism) OR (inborn errors of folate metabolism) OR (inborn errors of homocysteine metabolism)) AND ((Ischemic heart disease (IHD)) OR (diabetes) OR (malignancy) OR (psychiatric diseases) OR (stroke)))"}
{"candidate_id": "LLM05642", "doc_id": "NCT03026465_exc", "case_bucket": "or", "source_criterion": "Target lesion located in the left main stem STEMI Restenosis Cardiogenic shock Malignancies or other comorbid conditions with life expectancy less than 12 months or that may result in protocol noncompliance Known allergy to the study medications (probucol, sirolimus, zotarolimus) Pregnancy (present, suspected, or planned)", "candidate_expression": "((Cardiogenic shock) AND (Pregnancy) AND (Restenosis) AND (STEMI) AND (Target lesion left main stem) AND (allergy) AND (study medications) AND ((probucol) OR (sirolimus) OR (zotarolimus)) AND ((planned) OR (present) OR (suspected)) AND ((Malignancies) OR (comorbid conditions other)) AND ((life expectancy less than 12 months) OR (protocol noncompliance may)))"}
{"candidate_id": "LLM05643", "doc_id": "NCT01728194_inc", "case_bucket": "or", "source_criterion": "Age: 60-85 years, right-handed; Diagnosis: Major depression, unipolar (by Structured Clinical Interview for Diagnostic and Statistical Manual (DSM)IV (SCID-R) and DSM-IV criteria); Age of onset of first episode = 50 years with up to three depressive episodes; Severity of depression: A 24-Item Hamilton Depression Rating Scale (HDRS) = 20.", "candidate_expression": "((24-Item Hamilton Depression Rating Scale) AND (60-85 years) AND (= 20) AND (= 50 years) AND (Age) AND (DSM) AND (DSM-IV criteria)) AND (HDRS) AND (IV Structured Clinical Interview for Diagnostic and Statistical Manual) AND (Major depression) AND (SCID) AND (depression) AND (depressive episodes) AND (onset of first episode) AND (right-handed) AND (three) AND (unipolar))"}
{"candidate_id": "LLM05644", "doc_id": "NCT01236417_inc", "case_bucket": "or", "source_criterion": "Post menopausal women with a history of estrogen positive breast cancer who are receiving aromatase inhibitors for at least one month. Patients must complain of mild to moderate arthralgia. Ability to understand and sign informed consent. Patients meet criteria for low to moderate risk for moderate exercise based oon the ACSM guidelines.", "candidate_expression": "((ACSM guidelines) AND (Ability to understand and sign informed consent.) AND (Post menopausal) AND (aromatase inhibitors) AND (arthralgia) AND (breast cancer) AND (estrogen positive) AND (for at least one month) AND (history) AND (risk for moderate exercise) AND (women) AND ((mild) OR (moderate)) AND ((low) OR (moderate)))"}
{"candidate_id": "LLM05645", "doc_id": "NCT01352598_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05646", "doc_id": "NCT02818816_inc", "case_bucket": "other", "source_criterion": "Males aged 18 years and above Patients with a diagnosis of prostatic carcinoma requiring prostate surgery", "candidate_expression": "((18 years and above) AND (Males) AND (aged) AND (prostate surgery) AND (prostatic carcinoma))"}
{"candidate_id": "LLM05647", "doc_id": "NCT02822001_exc", "case_bucket": "or", "source_criterion": "Patients unable to give informed consent. Any patient whose condition will not allow for placement of the electrode PadSet. Patients whose tracheas were not extubated in OR or PACU. Patients with Impaired Renal Function with a have a known estimated CrCl<30 ml/min Patients using oral contraception.", "candidate_expression": "((<30 ml/min) AND (Impaired Renal Function) AND (Patients unable to give informed consent) AND (allow) AND (condition) AND (electrode PadSet) AND (estimated CrCl) AND (extubated) AND (not) AND (oral contraception) AND (placement) AND (tracheas) AND ((OR) OR (PACU)))"}
{"candidate_id": "LLM05648", "doc_id": "NCT02920177_exc", "case_bucket": "or", "source_criterion": "Established Osteoarthritis (Kellgren-Lawrence > 3) Minimum joint space > 2 mm as measured on AP radiograph Hip dysplasia (center edge angle < 20° on AP radiograph) Patients with clinically significant cardiovascular, renal, hepatic, endocrine disease, cancer or diabetes Patients with ongoing infection including HIV and Hepatitis Patient with history of osteomyelitis/septic arthritis Anticoagulation therapy Patients who are pregnant or breast feeding Patients with systemic, rheumatic or inflammatory disease of the knee or chondrocalcinosis, hemochromatosis, inflammatory arthritis, arthropathy of the knee associated with juxta-articular Paget's disease of the femur or tibia, hemophilic arthropathy, infectious arthritis, Charcot's knee joint, villonodular synovitis, and synovial chondromatosis Patients taking immunosuppressant medication Patients with abnormal hematology or serum chemistry lab results Patients receiving injection to treatment knee within 2 months of study enrollment BMI greater than 35 or less than 20", "candidate_expression": "((< 20°) AND (> 2 mm) AND (> 3) AND (AP radiograph) AND (Anticoagulation therapy) AND (BMI) AND (Hip dysplasia) AND (Kellgren-Lawrence) AND (Minimum joint space) AND (Osteoarthritis) AND (Paget's disease) AND (Patients who are pregnant or breast feeding) AND (abnormal) AND (arthropathy of the knee) AND (center edge angle) AND (immunosuppressant medication) AND (infection) AND (injection) AND (juxta-articular) AND (knee) AND (ongoing) AND (significant) AND (study enrollment) AND (within 2 months of study enrollment) AND ((cancer) OR (cardiovascular disease) OR (diabetes) OR (endocrine disease) OR (hepatic disease) OR (renal disease)) AND ((HIV) OR (Hepatitis)) AND ((osteomyelitis) OR (septic arthritis)) AND ((Charcot's knee joint) OR (chondrocalcinosis) OR (hemochromatosis) OR (hemophilic arthropathy) OR (infectious arthritis) OR (inflammatory arthritis) OR (synovial chondromatosis) OR (villonodular synovitis)) AND ((femur) OR (tibia)) AND ((inflammatory disease) OR (rheumatic disease) OR (systemic disease)) AND ((hematology lab) OR (serum chemistry lab)) AND ((greater than 35) OR (less than 20)))"}
{"candidate_id": "LLM05649", "doc_id": "NCT03120728_exc", "case_bucket": "or", "source_criterion": "Currently pregnant or breastfeeding Severe pelvic organ prolapse or prolapse to any degree that may prevent retention of the vaginal ring after insertion Use of oral contraceptive pills, patches, implants or hormonal intrauterine contraception in the month prior to screening Use of depo medroxyprogesterone within 6 months of screening Use of medications that interact with contraceptive steroid hormones: anti-epileptic medications, rifampin, rifabutin, fosamprenavir, etc Medical condition with safety deemed to be category 3 or 4 when using a combined hormonal contraceptive, as determined by the Center for Disease Control Medical Eligibility Criteria: current or past history of breast cancer, severe decompensated cirrhosis, history of deep vein thrombosis or pulmonary embolus, diabetes with nephropathy/retinopathy/neuropathy or other vascular disease diagnosed more than 20 years ago, current symptomatic gallbladder disease, hypertension, ischemic heart disease, known thrombogenic mutations, hepatocellular adenoma, malignant hepatoma, multiple risk factors for atherosclerotic cardiovascular disease, multiple sclerosis with prolonged immobility, history of peripartum cardiomyopathy, cigarette smoking and =35yo, history of complicated solid organ transplant, history of stroke, history of superficial venous thrombosis not associated with catheter, systemic lupus erythematosus with positive antiphospholipid antibodies, valvular heart disease complicated by pulmonary hypertension or atrial fibrillation or bacterial endocarditis, and acute viral hepatitis", "candidate_expression": "((3 or 4) AND (=35yo) AND (Center for Disease Control Medical Eligibility Criteria) AND (Currently) AND (Medical condition) AND (Severe) AND (antiphospholipid antibodies) AND (breast cancer) AND (catheter) AND (cigarette smoking) AND (cirrhosis) AND (combined hormonal contraceptive) AND (contraceptive steroid hormones) AND (current) AND (decompensated) AND (deep vein thrombosis) AND (depo medroxyprogesterone) AND (diabetes) AND (history) AND (in the month prior to screening) AND (interact with) AND (may prevent retention of the vaginal ring after insertion) AND (medications) AND (more than 20 years ago) AND (multiple) AND (not associated) AND (positive) AND (prolonged immobility) AND (pulmonary embolus) AND (risk factors) AND (safety category) AND (screening) AND (severe) AND (symptomatic) AND (valvular heart disease) AND (within 6 months of screening) AND (yo) AND ((hormonal intrauterine contraception) OR (implants) OR (oral contraceptive pills) OR (patches)) AND ((anti-epileptic medications) OR (fosamprenavir) OR (rifabutin) OR (rifampin)) AND ((current) OR (past)) AND ((breastfeeding) OR (pregnant)) AND ((nephropathy) OR (neuropathy) OR (other) OR (retinopathy) OR (vascular disease)) AND ((gallbladder disease) OR (hypertension) OR (ischemic heart disease)) AND ((pelvic organ prolapse) OR (prolapse)) AND ((atrial fibrillation) OR (bacterial endocarditis) OR (pulmonary hypertension)) AND ((acute viral hepatitis) OR (atherosclerotic cardiovascular disease) OR (complicated solid organ transplant) OR (hepatocellular adenoma) OR (malignant hepatoma) OR (multiple sclerosis) OR (peripartum cardiomyopathy) OR (stroke) OR (superficial venous thrombosis) OR (systemic lupus erythematosus) OR (thrombogenic mutations)))"}
{"candidate_id": "LLM05650", "doc_id": "NCT02295202_exc", "case_bucket": "other", "source_criterion": "Smokers Patients under chronic use of medications Neurological diseases Coronary artery disease Acute heart failure Chronic renal failure (GFR < 30 ml/min) Chronic obstructive pulmonary disease Mild OSA and patients with BMI over 40 kg/m2.", "candidate_expression": "((< 30 ml/min) AND (Acute heart failure) AND (BMI) AND (Chronic) AND (Coronary artery disease) AND (GFR) AND (Mild OSA) AND (Neurological diseases) AND (Smokers) AND (chronic use) AND (medications) AND (obstructive pulmonary disease) AND (over 40 kg/m2) AND (renal failure))"}
```
