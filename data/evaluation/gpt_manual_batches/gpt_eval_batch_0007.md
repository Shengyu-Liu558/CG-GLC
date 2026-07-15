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
{"candidate_id": "LLM00151", "doc_id": "NCT03070847_exc", "case_bucket": "or", "source_criterion": "pregnancy known allergies for tranexamic acid or any other substance in Exacyl deep vein thrombosis Hormone Replacement Therapy or oral contraceptive usage anticoagulants usage obesity - BMI (body mass index) >30 kg/m2 renal disease, as glomerular filtration rate (GFR) <60 ml/min/1,73 m*m seizures or epilepsy in the past", "candidate_expression": "((<60 ml/min/1,73 m*m) AND (>30 kg/m2) AND (BMI) AND (Exacyl) AND (GFR) AND (Hormone Replacement Therapy) AND (allergies) AND (anticoagulants) AND (body mass index) AND (deep vein thrombosis) AND (epilepsy) AND (glomerular filtration rate) AND (in the past) AND (obesity) AND (oral contraceptive) AND (pregnancy) AND (renal disease) AND (seizures) AND (tranexamic acid))"}
{"candidate_id": "LLM00152", "doc_id": "NCT02419378_inc", "case_bucket": "or", "source_criterion": "Signed informed consent form (ICF) Age 18 to 55 years old (inclusive) as of the date the ICF is signed Diagnosis of MS according to the McDonald criteria 2010 and cranial MRI scan demonstrating white matter lesions attributable to MS within 10 years before Screening Onset of MS symptoms (as determined by a neurologist, either at present or retrospectively) within 10 years of the date the ICF is signed EDSS score 0.0 to 5.0 (inclusive) at Screening Patients with (highly) active RRMS disease course indicated to receive alemtuzumab according to the following conditions (at least 1 out of 3 conditions has to be fulfilled): 1. =2 MS relapses within 24 months, 2. clinical (=1 relapse) or MRI (new gadolinium enhancing lesions) disease activity under therapy with other diseasemodifying therapies, 3. severe relapse with high disease activity (=9 T2 hyperintense Lesions and =1 gadolinium enhancing lesion) on MRI. Completion of all vaccinations required by the applicable immunization guidelines published by \"ständige Impfkommission\" (STIKO) History of chickenpox or positive test for antibodies against varicella zoster virus (VZV)", "candidate_expression": "((Age 18 to 55 years old () AND (EDSS score 0.0 to 5.0) AND (Lesions =9 T2 hyperintense) AND (MRI) AND (MS relapses =2 within 24 months,) AND (MS symptoms within 10 years) AND (MS within 10 years before Screening) AND (McDonald criteria 2010) AND (RRMS active) AND (Signed informed consent form (ICF)) AND (VZV) AND (alemtuzumab) AND (cranial MRI scan) AND (lesion =1 gadolinium enhancing) AND (lesions new gadolinium enhancing) AND (relapse severe) AND ((MRI) OR (relapse =1)) AND ((chickenpox) OR (test for antibodies positive varicella zoster virus)))"}
{"candidate_id": "LLM00153", "doc_id": "NCT02015923_inc", "case_bucket": "or", "source_criterion": "colorectal cancer above to 12 cm from the anal verge unresectable synchronous metastases no contraindications for chemotherapy absence of peritoneal carcinomatosis, central nervous system o bone metastasis. performance status ECOG = 2 (Eastern Cooperative Oncology Group) uncontrolled concomitant medical conditions that may compromise to chemotherapy significant symptomatic cardiac disease not pregnancy or breastfeeding", "candidate_expression": "((= 2) AND (ECOG) AND (Eastern Cooperative Oncology Group) AND (above to 12 cm from the anal verge) AND (absence) AND (bone metastasis) AND (breastfeeding) AND (cardiac disease) AND (central nervous system metastasis) AND (chemotherapy) AND (colorectal cancer) AND (concomitant) AND (contraindications) AND (medical conditions that may compromise to chemotherapy) AND (metastases) AND (no) AND (not) AND (performance status) AND (peritoneal carcinomatosis) AND (pregnancy) AND (significant) AND (symptomatic) AND (synchronous) AND (uncontrolled) AND (unresectable))"}
{"candidate_id": "LLM00154", "doc_id": "NCT02732080_exc", "case_bucket": "or", "source_criterion": "Recanalized (TIMI I-III flow) IRA at coronary angiography. Patients in whom TIMI-3 flow was not able to be established after wire crossing, balloon angioplasty or thrombectomy. STEMI due to bypass-graft occlusion Severe heart failure or cardiogenic shock", "candidate_expression": "((IRA) AND (Recanalized TIMI I-III flow) AND (STEMI) AND (bypass-graft) AND (coronary angiography) AND (occlusion) AND ((cardiogenic shock) OR (heart failure)))"}
{"candidate_id": "LLM00155", "doc_id": "NCT03249272_inc", "case_bucket": "or", "source_criterion": "Men or women aged 18 years or older Patients presenting for CMR with the clinical diagnosis of hypertrophic cardiomyopathy based on left ventricular wall thickness of at least =15 mm in the absence of any other cardiac or systemic cause of hypertrophy Patients presenting for CMR with the clinical diagnosis of idiopathic dilated cardiomyopathy based upon left ventricular ejection fraction =40%, LV end-diastolic diameter =55 mm or left ventricular end-systolic diameter =45 mm, and the absence of coronary stenoses on angiography. Patients presenting for CMR evaluation of chest pain but without evidence of obstructive coronary artery disease either by coronary angiography or stress testing.", "candidate_expression": "((18 years or older) AND (=40%) AND (=45 mm) AND (=55 mm) AND (Men) AND (absence) AND (aged) AND (angiography) AND (at least =15 mm) AND (chest pain) AND (coronary stenoses) AND (hypertrophic cardiomyopathy) AND (idiopathic dilated cardiomyopathy) AND (left ventricular wall thickness) AND (obstructive coronary artery disease) AND (without) AND (women) AND ((cardiac cause of hypertrophy) OR (systemic cause of hypertrophy)) AND ((LV end-diastolic diameter) OR (left ventricular ejection fraction) OR (left ventricular end-systolic diameter)) AND ((coronary angiography) OR (stress testing)))"}
{"candidate_id": "LLM00156", "doc_id": "NCT02301962_exc", "case_bucket": "or", "source_criterion": "History or known presence of central nervous system metastases. History of another malignancy except: Malignancy treated with curative intent and with no known active disease present for >=5 years prior to enrolment and felt to be at low risk for recurrence by the treating physician; Adequately treated non-melanomatous skin cancer or lentigo maligna without evidence of disease; Adequately treated cervical carcinoma in situ without evidence of disease; Prostatic intraepithelial neoplasia without evidence of prostate cancer. Known immediate or delayed hypersensitivity reaction or idiosyncrasy to drugs chemically related to panitumumab or excipients that contraindicates their participation. Prior anti-epidermal growth factor receptor (EGFr) antibody therapy (e.g., panitumumab or cetuximab) or treatment with small molecule EGFr inhibitors (e.g., gefitinib, erlotinib, lapatinib). Antitumor therapy (e.g., chemotherapy, hormonal therapy, immunotherapy, antibody therapy, radiotherapy), or investigational agent or therapy <=30 days before first dose of study treatment or not recovered from any acute toxicity. Other investigational procedure <=30 days before study entry. History of interstitial lung disease (ILD) e.g., interstitial pneumonitis, pulmonary fibrosis or evidence of ILD on baseline chest computer tomography. Subject previously enrolled to this study. History of keratitis, ulcerative keratitis or severe dry eye. Major surgery (e.g., requiring general anesthesia) <=30 days before first dose of study treatment. Subjects must have recovered from any surgery related toxicities. Minor surgical procedure (e.g., open biopsy) <=7 days before first dose of study treatment, or not yet recovered from prior minor surgery Note: uncomplicated placement of vascular access device, fine needle aspiration, thoracocentesis or paracentesis >=3 days prior to first dose of study treatment is acceptable. Clinically significant cardiovascular disease (including myocardial infarction, unstable angina, symptomatic congestive heart failure, serious uncontrolled cardiac arrhythmia) <=6 months prior to enrolment. History of any medical or psychiatric condition or laboratory abnormality that in the opinion of the investigator may increase the risk associated with the study participation or investigational product administration, compliance with the study procedures or may interfere with the interpretation of the results. Unstable pulmonary embolism, deep vein thrombosis, or other significant arterial/venous thromboembolic event <=30 days before first dose of study treatment. If on anticoagulation, subject must be on stable therapeutic dose prior to first dose of study treatment. Subject who is pregnant or breast feeding, or planning to become pregnant during treatment and within 2 months after the discontinuation of study treatment. Known positive test(s) for human immunodeficiency virus infection (testing is not required in the absence of clinical suspicion). Active infection requiring systemic treatment or any uncontrolled infection <=14 days prior to first dose of study treatment (with the exception of uncomplicated urinary tract infection or upper respiratory tract infection). Subject has any kind of disorder that compromises the ability of the subject to give written informed consent and/or to comply with study procedures or is unwilling or unable to comply with study requirements.", "candidate_expression": "((<=14 days prior to first dose of study treatment) AND (<=30 days before first dose of study treatment) AND (<=30 days before study entry) AND (<=6 months prior to enrolment) AND (<=7 days before first dose of study treatment) AND (Active) AND (Adequately) AND (Antitumor therapy) AND (Clinically significant) AND (EGFr) AND (History of any medical or psychiatric condition or laboratory abnormality that in the opinion of the investigator may increase the risk associated with the study participation or investigational product administration, compliance with the study procedures or may interfere with the interpretation of the results.) AND (ILD) AND (Major surgery) AND (Malignancy) AND (Minor surgical procedure) AND (Other) AND (Prostatic intraepithelial neoplasia) AND (Subject has any kind of disorder that compromises the ability of the subject to give written informed consent and/or to comply with study procedures or is unwilling or unable to comply with study requirements.) AND (Unstable) AND (active disease) AND (another) AND (anti-epidermal growth factor receptor antibody therapy) AND (antibody therapy) AND (anticoagulation) AND (any) AND (arterial thromboembolic event) AND (baseline) AND (become pregnant) AND (breast feeding) AND (cardiac arrhythmia) AND (cardiovascular disease) AND (central nervous system metastases) AND (cervical carcinoma in situ) AND (cetuximab) AND (chemotherapy) AND (chest computer tomography) AND (congestive heart failure) AND (deep vein thrombosis) AND (delayed hypersensitivity reaction) AND (disease) AND (drugs chemically related to panitumumab) AND (drugs chemically related to panitumumab excipients) AND (dry eye) AND (during treatment) AND (enrolment) AND (erlotinib) AND (evidence of) AND (evidence of disease) AND (except) AND (felt to be at low risk) AND (first dose of study treatment) AND (for >=5 years prior to enrolment) AND (gefitinib) AND (general anesthesia) AND (hormonal therapy) AND (idiosyncrasy) AND (immediate hypersensitivity reaction) AND (immunotherapy) AND (infection) AND (interstitial lung disease) AND (interstitial pneumonitis) AND (investigational agent) AND (investigational procedure) AND (keratitis) AND (lapatinib) AND (lentigo maligna) AND (malignancy) AND (minor surgery) AND (myocardial infarction) AND (no) AND (non-melanomatous skin cancer) AND (not recovered from any acute toxicity) AND (not yet) AND (open biopsy) AND (other) AND (panitumumab) AND (planning to) AND (positive) AND (pregnant) AND (prior) AND (prior to first dose of study treatment) AND (prostate cancer) AND (pulmonary embolism) AND (pulmonary fibrosis) AND (radiotherapy) AND (recovered) AND (recurrence) AND (serious) AND (severe) AND (significant) AND (stable) AND (symptomatic) AND (systemic treatment) AND (test(s) for human immunodeficiency virus infection) AND (the discontinuation of study treatment) AND (therapeutic dose) AND (therapy) AND (treated) AND (treated with curative intent) AND (treatment) AND (treatment with small molecule EGFr inhibitors) AND (ulcerative keratitis) AND (uncomplicated) AND (uncontrolled) AND (uncontrolled infection) AND (unstable angina) AND (upper respiratory tract infection) AND (urinary tract infection) AND (venous thromboembolic event) AND (with the exception of) AND (within 2 months after the discontinuation of study treatment) AND (without))"}
{"candidate_id": "LLM00157", "doc_id": "NCT03480607_exc", "case_bucket": "or", "source_criterion": "known allergy to any of drugs used coagulopathy any wound or infection related to puncture site major illness failure to gain consent of parents.", "candidate_expression": "((allergy) AND (coagulopathy) AND (drugs used) AND (failure to gain consent of parents) AND (illness major) AND (infection) AND (wound) AND NOT (consent of parents))"}
{"candidate_id": "LLM00158", "doc_id": "NCT02068365_inc", "case_bucket": "or", "source_criterion": "Male & female patients >= 18 and < 70 years of age Positive HBeAg before starting NA treatment Treated by a single NA (lamivudine, adefovir, entecavir or tenofovir) for 6 months to 5 years Developed HBeAg seroconversion (HBeAg negative and ant-HBe negative) with undetectable HBV DNA by PCR based assay on NA treatment. Negative urine or serum pregnancy test (for women of childbearing potential) documented within the 24-hour period prior to the first dose of test drug. Additionally, all females must be using reliable contraception during the study and for 3 months after treatment completion", "candidate_expression": "((Additionally, all females must be using reliable contraception during the study and for 3 months after treatment completion) AND (HBV DNA undetectable) AND (HBeAg Positive before starting NA treatment) AND (NA) AND (NA single) AND (PCR based assay) AND (Treated for 6 months to 5 years) AND (age >= 18 and < 70 years) AND (childbearing potential) AND (treatment) AND (women) AND ((Male) OR (female)) AND ((adefovir) OR (entecavir) OR (lamivudine) OR (tenofovir)) AND ((HBeAg) OR (seroconversion)) AND ((HBeAg) OR (negative)) AND ((ant-HBe) OR (negative)) AND ((serum pregnancy test) OR (urine pregnancy test)))"}
{"candidate_id": "LLM00159", "doc_id": "NCT02396732_inc", "case_bucket": "or", "source_criterion": "Age 18 years or older Blunt or penetrating trauma Requires VTE thromboprophylaxis High-risk for VTE", "candidate_expression": "((18 years or older) AND (Age) AND (Blunt trauma) AND (High-risk) AND (VTE) AND (penetrating trauma) AND (thromboprophylaxis))"}
{"candidate_id": "LLM00160", "doc_id": "NCT03511521_inc", "case_bucket": "or", "source_criterion": "Patients receiving once daily dosing of methylprednisolone or prednisone in a dose of 10 mg/day or greater Hyperglycemic (Glucose level > 126 mg/dL) Diabetic and nondiabetic patients Expected duration of hospital stay and time on steroids >= 3 days Patient of appropriate caregiver able to give Informed Consent", "candidate_expression": "((Expected duration of hospital stay >= 3 days) AND (Glucose level > 126 mg/dL) AND (Hyperglycemic) AND (Patient of appropriate caregiver able to give Informed Consent) AND (time on steroids >= 3 days) AND ((Diabetic) OR (nondiabetic)) AND ((methylprednisolone) OR (prednisone)))"}
{"candidate_id": "LLM00161", "doc_id": "NCT02986659_inc", "case_bucket": "or", "source_criterion": "Age 65 - 79 History of coronary artery disease (MI/heart attack, stroke, heart failure, or peripheral artery disease) Cancer, with no active treatment in the last year MCI (MoCA >18<26 -inclusive of 1 point if <12 years of education Group 2 Decline physical function (walking speed < 1 m/s) Group 3 (Either or both) Abdominal obesity (>88cm women, >102cm men) AND hypertension (treated or resting blood pressure >140/90 Abdominal obesity (>88cm women, >102cm men) AND hyperlipidemia (treated or fasting total cholesterol >240 English literacy Willing to provide informed consent", "candidate_expression": "((Abdominal) AND (Abdominal obesity) AND (Age 65 - 79) AND (Cancer) AND (Decline physical function) AND (English literacy) AND (MCI) AND (MI) AND (MoCA >18<26) AND (coronary artery disease History) AND (fasting total cholesterol >240) AND (heart attack) AND (heart failure) AND (hyperlipidemia) AND (hypertension) AND (men >102cm) AND (peripheral artery disease) AND (provide informed consent Willing to) AND (resting blood pressure >140/90) AND (stroke) AND (treated) AND (walking speed < 1 m/s) AND (women >88cm) AND NOT (active treatment in the last year))"}
{"candidate_id": "LLM00162", "doc_id": "NCT02652572_exc", "case_bucket": "or", "source_criterion": "1. Decrease in size of the designated target ulcer(s) by ≥ 30% during the 7-day screening period 2. Cannot tolerate or comply with compression therapy. 3. An ulcer which shows signs of severe clinical infection, defined as pus oozing from the ulcer site 4. An ulcer positive for β-hemolytic streptococci upon culture 5. The ulcer has > 50% slough, significant necrotic tissue, bone, tendon, or capsule exposure or avascular ulcer beds 6. Is highly exuding (i.e. requires daily change of dressing) 7. Ankle brachial pressure index <0.65 8. Patients with active systemic infections 9. Patients with clinically significant medical conditions as determined by the investigator including renal, hepatic, hematologic, neurologic or immune disease. Examples include but are not limited to: 1. Renal insufficiency as an estimated GFR which is < 30 mL/min/1.7m2 2. Abnormal blood biochemistry defined as 3 times that of the upper limit of the normal range. 3. Hepatic insufficiency defined as total bilirubin > 2 mg/dL or serum albumin < 25 g/L 4. HbA1c > 9% 5. Hemoglobin < 10 g/dL 6. Hematocrit < 0.30 7. Platelet count < 100,000 10. Presence of an active systemic or local cancer or tumor of any kind (with the exception of non-melanoma skin cancer) 11. Patients with severe rheumatoid arthritis (with more than 20 persistently inflamed joints, or below lower normal limit blood albumin level, or evidence of bone and cartilage damage on x-ray, or inflammation in tissues other than joints) and other collagen vascular diseases. 12. Patients with active connective tissue disease 13. Treatment with systemic corticosteroids (>15 mg/day), or current immunosuppressive agents 14. Previous or current radiation therapy or likelihood to receive this therapy during study participation 15. Pregnant or nursing patients 16. Known prior inability or unavailability to complete required study visits during study participation 17. Significant peripheral edema as per investigator's discretion 18. A psychiatric condition (e.g., suicidal ideation) or chronic alcohol or drug abuse problem, determined from the patient's medical history, which, in the opinion of the investigator, may pose a threat to patient compliance 19. Use of a platelet-derived growth factor within 28 days before screening 20. Use of any investigational drug or therapy within 28 days before screening 21. Has any other factor which may, in the opinion of the investigator, compromise participation and/or follow-up in the study", "candidate_expression": "((3 times that of the upper limit of the normal range) AND (< 0.30) AND (< 10 g/dL) AND (< 100,000) AND (< 25 g/L) AND (< 30 mL/min/1.7m2) AND (<0.65) AND (> 2 mg/dL) AND (> 50%) AND (> 9%) AND (>15 mg/day) AND (Abnormal) AND (Ankle brachial pressure index) AND (Cannot tolerate or comply with) AND (Decrease in size) AND (Has any other factor which may, in the opinion of the investigator, compromise participation and/or follow-up in the study) AND (HbA1c) AND (Hematocrit) AND (Hemoglobin) AND (Hepatic insufficiency) AND (Platelet count) AND (Renal insufficiency) AND (Significant) AND (active) AND (as determined by the investigator) AND (as per investigator's discretion) AND (below lower normal limit) AND (blood albumin level) AND (blood biochemistry) AND (bone and cartilage damage) AND (change of dressing) AND (clinically significant) AND (compression therapy) AND (connective tissue disease) AND (current) AND (daily) AND (during the 7-day screening period) AND (estimated GFR) AND (highly exuding) AND (in the opinion of the investigator) AND (inflamed joints) AND (inflammation in tissues other than joints) AND (likelihood to) AND (may pose a threat to patient compliance) AND (medical conditions) AND (more than 20) AND (non-melanoma skin cancer) AND (peripheral edema) AND (persistently) AND (platelet-derived growth factor) AND (pose a threat) AND (positive for β-hemolytic streptococci) AND (pus) AND (radiation therapy) AND (screening) AND (severe) AND (severe clinical infection) AND (shows signs of severe clinical infection) AND (slough) AND (suicidal ideation) AND (systemic corticosteroids) AND (systemic infections) AND (target ulcer) AND (ulcer) AND (with the exception of) AND (within 28 days before screening) AND (x-ray) AND (≥ 30%) AND ((collagen vascular diseases) OR (rheumatoid arthritis)) AND ((Treatment) OR (immunosuppressive agents)) AND ((Previous) OR (current)) AND ((Pregnant) OR (nursing)) AND ((alcohol abuse problem) OR (drug abuse problem) OR (psychiatric condition)) AND ((investigational drug) OR (investigational therapy)) AND ((avascular ulcer beds) OR (bone exposure) OR (capsule exposure) OR (necrotic tissue) OR (tendon exposure)) AND ((hematologic disease) OR (hepatic disease) OR (immune disease) OR (neurologic disease) OR (renal disease)) AND ((serum albumin) OR (total bilirubin)) AND ((local cancer) OR (systemic cancer) OR (tumor of any kind)))"}
{"candidate_id": "LLM00163", "doc_id": "NCT02109081_exc", "case_bucket": "or", "source_criterion": "1) preoperative diagnosis of delirium or dementia; 2) MMSE score of = 20 out of 30 on preoperative testing (more than mild cognitive impairment) or delirium on preoperative CAM testing; 3) language barriers that would preclude testing; 4) preoperative steroid use within 3 days of surgery; or 5) anticipation of postoperative intubation.", "candidate_expression": "((= 20 out of 30) AND (CAM testing) AND (MMSE score) AND (anticipation) AND (cognitive impairment) AND (delirium) AND (dementia) AND (intubation) AND (language barriers) AND (more than mild) AND (postoperative) AND (preoperative) AND (steroid) AND (surgery) AND (within 3 days of surgery))"}
{"candidate_id": "LLM00164", "doc_id": "NCT01497639_inc", "case_bucket": "or", "source_criterion": "ages of 7 and 75 years marked disability owing to primary generalized or segmental dystonia, despite optimal pharmacologic treatment disease duration of at least 5 years.", "candidate_expression": "((ages 7 and 75 years) AND (disability) AND (disease duration at least 5 years) AND (dystonia primary) AND (pharmacologic treatment optimal) AND ((generalized) OR (segmental)))"}
{"candidate_id": "LLM00165", "doc_id": "NCT02827487_inc", "case_bucket": "or", "source_criterion": "Women with expected difficult IUD insertion like nulliparous women and women with previous cesarean section.", "candidate_expression": "((IUD insertion) AND (Women) AND (cesarean section) AND (difficult) AND (expected) AND (nulliparous) AND (previous) AND (women))"}
{"candidate_id": "LLM00166", "doc_id": "NCT02105090_inc", "case_bucket": "or", "source_criterion": "elective procedure weight over 40 kg American Society of Anesthesiology class I-III first upper GI endoscopy procedure finnish or/and swedish speaking", "candidate_expression": "((American Society of Anesthesiology class) AND (I-III) AND (elective procedure) AND (endoscopy procedure) AND (finnish speaking) AND (first) AND (over 40 kg) AND (swedish speaking) AND (upper GI) AND (weight))"}
{"candidate_id": "LLM00167", "doc_id": "NCT03350659_inc", "case_bucket": "or", "source_criterion": "Age >=19 patients who complained of dizziness Orthostatic hypotension after 3-minute standing (systolic blood pressure drop >=20 or diastolic blood pressure drop >=10", "candidate_expression": "((>=10) AND (>=19) AND (>=20) AND (Age) AND (Orthostatic hypotension) AND (after 3-minute standing) AND (diastolic blood pressure drop) AND (dizziness) AND (systolic blood pressure drop))"}
{"candidate_id": "LLM00168", "doc_id": "NCT00305097_inc", "case_bucket": "other", "source_criterion": "Aged at least 18 years with an ability and willingness to give written informed consent. Body mass index 25-35 kg/m2 Users of at least 2 cups of caffeinated coffee per day who are willing to be randomized to any of the interventions. Non-smoking", "candidate_expression": "((Aged at least 18 years) AND (Body mass index 25-35 kg/m2) AND (Non-smoking) AND (ability to give written informed consent) AND (caffeinated coffee at least 2 cups per day) AND (willing to be randomized) AND (willingness to give written informed consent))"}
{"candidate_id": "LLM00169", "doc_id": "NCT03299517_inc", "case_bucket": "or", "source_criterion": "Adult men and women> 18 years old Presence of sustained ventricular tachycardia with HR> 120 bpm Systolic blood pressure> 90 mmHg No signs of poor peripheral perfusion Absence of dyspnea Absence of severe angina Signed consent form", "candidate_expression": "((Adult) AND (HR > 120 bpm) AND (Signed consent form) AND (Systolic blood pressure > 90 mmHg) AND (men) AND (old > 18 years old) AND (ventricular tachycardia sustained) AND (women) AND NOT (poor peripheral perfusion signs of) AND NOT (dyspnea) AND NOT (angina severe))"}
{"candidate_id": "LLM00170", "doc_id": "NCT02958072_inc", "case_bucket": "or", "source_criterion": "Diabetes mellitus Foot ulcer at the malleoli area between 0,25 cm² and 5,0 cm² Foot ulcer duration more than 6 weeks Ankle-brachial index above 0,40 or presence of palpable pulses in arteria dorsalis pedes and/or arteria tibialis posterior informed consent", "candidate_expression": "((Diabetes mellitus) AND (Foot ulcer) AND (above 0,40) AND (between 0,25 cm² and 5,0 cm²) AND (informed consent) AND (malleoli area) AND (more than 6 weeks) AND ((arteria dorsalis pedes) OR (arteria tibialis posterior)) AND ((Ankle-brachial index) OR (palpable pulses)))"}
{"candidate_id": "LLM00171", "doc_id": "NCT02571179_inc", "case_bucket": "other", "source_criterion": "healthy parturients with uncomplicated, single gestation pregnancies, full term (38-42 weeks of gestation) pregnancy, agreed to participate", "candidate_expression": "((38-42) AND (agreed to participate) AND (full term) AND (healthy) AND (parturients) AND (pregnancies) AND (pregnancy) AND (single gestation) AND (uncomplicated) AND (weeks of gestation))"}
{"candidate_id": "LLM00172", "doc_id": "NCT01815580_exc", "case_bucket": "or", "source_criterion": "Prior receipt of investigational anti-HIV vaccine Ongoing therapy with any of the following: Systemic corticosteroids. Short course less than or equal to 21 days of corticosteroids is allowed; Systemic chemotherapeutic agents; Nephrotoxic systemic agents, including aminoglycosides, amphotericin B, cidofovir, cisplatin, foscarnet, pentamidine; Immunomodulatory treatments including Interleukin-2; Investigational agents Known allergy/sensitivity or any hypersensitivity to components of study drugs (ART) or their formulations Active drug or alcohol use or dependence that would interfere with adherence to study requirements Serious medical or psychiatric illness that would interfere with the ability to adhere to study requirements Chronic or acute hepatitis B infection Use of female hormonal products based on estrogen or derivatives", "candidate_expression": "((ART) AND (Active) AND (Chronic hepatitis B infection) AND (Interleukin-2) AND (Ongoing) AND (Prior) AND (Serious) AND (Short course) AND (acute hepatitis B infection) AND (anti-HIV vaccine) AND (corticosteroids) AND (female hormonal products) AND (investigational) AND (is allowed) AND (less than or equal to 21 days) AND (therapy) AND (would interfere with adherence to study requirements) AND (would interfere with the ability to adhere to study requirements) AND ((Immunomodulatory treatments) OR (Investigational agents) OR (Nephrotoxic systemic agents) OR (Systemic chemotherapeutic agents) OR (Systemic corticosteroids) OR (aminoglycosides) OR (amphotericin B) OR (cidofovir) OR (cisplatin) OR (foscarnet) OR (pentamidine)) AND ((allergy) OR (hypersensitivity) OR (sensitivity)) AND ((components of study drugs) OR (or their formulations)) AND ((alcohol dependence) OR (alcohol use) OR (drug dependence) OR (use)) AND ((medical illness) OR (psychiatric illness)) AND ((estrogen) OR (estrogen derivatives)))"}
{"candidate_id": "LLM00173", "doc_id": "NCT03297021_exc", "case_bucket": "or", "source_criterion": "Patients with allergies or contraindications to study medications", "candidate_expression": "((study medications) AND ((allergies) OR (contraindications)))"}
{"candidate_id": "LLM00174", "doc_id": "NCT03225469_inc", "case_bucket": "other", "source_criterion": "1. Individuals scheduled for undergoing colonoscopy at the Endoscopy Center of Wuxi people's Hospital in China 2. Greater than the age of 18 3. Individuals living with other family members 4. Outpatients", "candidate_expression": "((Endoscopy Center of Wuxi people's Hospital in China) AND (Outpatients) AND (age Greater than 18) AND (colonoscopy))"}
{"candidate_id": "LLM00175", "doc_id": "NCT01850147_inc", "case_bucket": "or", "source_criterion": "Histologic or cytologic diagnosis of stage IIIB/IV NSCLC ECOG PS: 0,1 Unidimensional or bi-dimensional measurable disease Receive prior treatment including first-line platinum-based chemotherapy, standard second-line chemotherapy and 1 EGF/EGFR inhibitor Evidence of disease progression Life expectancy >12 weeks Neutrophils > 1.5 109/l, Platelets > 100 109/l, Hemoglobin > 9g/dl, Total bilirubin < 1.5 UNL, AST (SGOT) and ALT (SGPT) < 2.5 UNL, Alkaline phosphatases < 5 UNL, Creatinine < 1 UNL", "candidate_expression": "((ALT (SGPT) < 2.5 UNL) AND (AST (SGOT) < 2.5 UNL) AND (Alkaline phosphatases < 5 UNL) AND (Creatinine < 1 UNL) AND (ECOG PS 0,1 measurable) AND (Evidence) AND (Evidence of disease progression) AND (Hemoglobin > 9g/dl) AND (Histologic) AND (Life expectancy >12 weeks) AND (NSCLC stage IIIB/IV) AND (Neutrophils > 1.5 109/l) AND (Platelets > 100 109/l) AND (Total bilirubin < 1.5 UNL) AND (cytologic) AND (disease progression) AND (measurable) AND (treatment) AND ((1 EGF/EGFR inhibitor) OR (platinum-based chemotherapy) OR (second-line chemotherapy standard)))"}
```
