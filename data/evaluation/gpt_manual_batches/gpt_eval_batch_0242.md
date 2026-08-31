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
{"candidate_id": "LLM06026", "doc_id": "NCT02579928_inc", "case_bucket": "or", "source_criterion": "MDD Cohort: Meet DSM-5 criteria for Major Depressive Disorder by structured interview (MINI-KID); CDRS-R score >40; Failure to achieve remission with at least 1 adequate prior antidepressant trial (e.g. SSRI, SNRI, or TCA), meaning at least 8 weeks at therapeutic dosing, including at least 4 weeks of stable dosing. Anxiety Cohort: Meet DSM-5 criteria for any of the following anxiety disorders: Social Anxiety Disorders, Generalized Anxiety Disorder, Separation Anxiety Disorder and/or Panic Disorder by structured interview (MINI-KID); ADIS Clinical Severity Rating ≥4 (moderately severe) for any of the 4 included anxiety disorders; Failure to achieve remission with at least 1 adequate prior anxiolytic medication trial (e.g. SSRI, SNRI, or TCA), meaning at least 8 weeks at therapeutic dosing, including at least 4 weeks of stable dosing; Failure to achieve remission with previous CBT or subject declines current CBT therapy Stable psychiatric medications and doses for the month prior to enrollment. Subjects may continue to engage in any ongoing psychotherapy. Medically and neurologically healthy on the basis of physical examination and medical history. Parents able to provide written informed consent and adolescents must additionally provide assent.", "candidate_expression": "((ADIS Clinical Severity Rating ≥4 moderately severe) AND (Anxiety Cohort) AND (CBT therapy current) AND (CDRS-R score >40) AND (MDD Cohort) AND (MINI-KID) AND (Major Depressive Disorder DSM-5 criteria) AND (Medically healthy) AND (Parents provide written informed consent) AND (adolescents provide assent) AND (antidepressant) AND (antidepressant trial at least 1 adequate prior) AND (anxiety disorders) AND (anxiety disorders DSM-5 criteria) AND (anxiolytic medication) AND (anxiolytic medication trial at least 1 adequate prior) AND (medical history) AND (neurologically healthy) AND (physical examination) AND (psychiatric medications Stable doses Stable for the month prior to enrollment) AND (stable dosing at least 4 weeks) AND (structured interview) AND (therapeutic dosing at least 8 weeks) AND NOT (remission) AND ((SNRI) OR (SSRI) OR (TCA)) AND ((Generalized Anxiety Disorder) OR (Panic Disorder) OR (Separation Anxiety Disorder) OR (Social Anxiety Disorders)) AND ((CBT therapy previous) OR (subject declines)))"}
{"candidate_id": "LLM06027", "doc_id": "NCT02621489_inc", "case_bucket": "or", "source_criterion": "Patients eligible for PCI with application of DES, due to ACS. Patients with known or newly diagnosed T2D (type 2 diabetes is diagnosed according to current WHO criteria or by the use of anti-diabetic drugs) Male and female subjects 18-80 years. HbA1c (accordingly to IFCC) 47 mmol/mol - 110 mmol/mol. Signed informed consent form.", "candidate_expression": "((ACS) AND (DES) AND (HbA1c 47 mmol/mol - 110 mmol/mol) AND (Male) AND (PCI) AND (Signed informed consent form) AND (T2D) AND (female) AND (years 18-80))"}
{"candidate_id": "LLM06028", "doc_id": "NCT02739295_inc", "case_bucket": "other", "source_criterion": "Toxic epidermal necrolysis with SCORTEN 1 to 5 at admission", "candidate_expression": "((SCORTEN 1 to 5 at admission) AND (Toxic epidermal necrolysis))"}
{"candidate_id": "LLM06029", "doc_id": "NCT01410890_inc", "case_bucket": "or", "source_criterion": "The patient and/or the patient's parent/legal guardian is willing and able to provide signed informed consent. The patient has a confirmed GAA enzyme deficiency from skin, blood, or muscle tissue and/or 2 confirmed GAA gene mutations. Infant and toddler Pompe disease patients can be included in the study only under condition (minimal body weight) that the trial-related blood loss (including any losses in the maneuver) will not exceed 3 percent of the total blood volume during a period of 4 weeks and will not exceed 1 percent at any single time. The patient, if female and of childbearing potential, must have a negative pregnancy test (urine beta-human chorionic gonadotropin) at screening. Note: All female patients of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study. For patients previously treated with alglucosidase alfa the patient has received alglucosidase alfa for at least 6 months.", "candidate_expression": "((GAA enzyme deficiency skin blood muscle tissue) AND (GAA gene mutations 2) AND (Infant) AND (Pompe disease) AND (The patient and/or the patient's parent/legal guardian is willing and able to provide signed informed consent) AND (The patient, if female and of childbearing potential, must have a negative pregnancy test (urine beta-human chorionic gonadotropin) at screening. Note: All female patients of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study) AND (alglucosidase alfa for at least 6 months) AND (toddler))"}
{"candidate_id": "LLM06030", "doc_id": "NCT03355326_exc", "case_bucket": "or", "source_criterion": "Neurological Congenital malformations and/or those known to impair intestinal motility Additional congenital gastrointestinal abnormalities requiring surgical intervention Congenital Cyanotic heart disease Surgical Closure of abdominal wall defect with prosthetic material (e.g. prosthetic or bio-prosthetic mesh)", "candidate_expression": "((Cyanotic heart disease Congenital) AND (Neurological Congenital malformations) AND (Surgical Closure) AND (abdominal wall defect) AND (bio-prosthetic mesh) AND (gastrointestinal abnormalities Additional congenital) AND (impair intestinal motility) AND (prosthetic material) AND (prosthetic mesh) AND (surgical intervention requiring))"}
{"candidate_id": "LLM06031", "doc_id": "NCT03255044_inc", "case_bucket": "other", "source_criterion": "older than 18 years (of both sexes) diagnosed with stable chronic heart failure NYHA class II-III ejection fraction < 40 % as assessed by 2D echocardiography who have been optimized on Guideline Directed treatment for heart failure for at least a month prior to enrolling.", "candidate_expression": "((2D echocardiography) AND (< 40 %) AND (II-III) AND (NYHA class) AND (both sexes) AND (chronic heart failure) AND (ejection fraction) AND (older than 18) AND (stable) AND (years))"}
{"candidate_id": "LLM06032", "doc_id": "NCT01410890_exc", "case_bucket": "other", "source_criterion": "The patient is participating in another clinical study using an investigational product. The patient, in the opinion of the Investigator, is unable to adhere to the requirements of the study.", "candidate_expression": "(The patient is participating in another clinical study using an investigational product)"}
{"candidate_id": "LLM06033", "doc_id": "NCT02816762_exc", "case_bucket": "or", "source_criterion": "Non diabetic nephropathy (confirmed by biopsy). Dialysis for acute renal failure within the 6 previous months. Evidence in the clinic history of relevant bilateral stenosis of renal artery (> 75%) Urinary albumin/creatinine ratio higher than 3000 mg/g, at the baseline visit. Systolic blood pressure = 180 mmHg or diastolic blood pressure = 110 mm Hg at the baseline visit. Stroke, transient ischemic attack, acute coronary syndrome, or hospitalization for heart failure worsening, within the previous 30 days. Professional drivers, risk profession or respiratory failure. Severe daytime sleepiness (Epworth sleepiness scale >18) Concomitant treatment with high doses of acetylsalicylic acid (> 500 mg/day) or continuous treatment with non-steroidal anti-inflammatory drugs Previous treatment with CPAP Participation in another clinical trial within the 30 days prior to randomization.", "candidate_expression": "((CPAP) AND (Dialysis within the 6 previous months) AND (Epworth sleepiness scale >18) AND (Non diabetic nephropathy confirmed by biopsy) AND (Professional drivers) AND (Stroke) AND (Systolic blood pressure = 180 mmHg) AND (Urinary albumin/creatinine ratio higher than 3000 mg/g at the baseline visit) AND (acetylsalicylic acid high doses > 500 mg/day) AND (acute coronary syndrome) AND (acute renal failure) AND (biopsy) AND (daytime sleepiness Severe) AND (diastolic blood pressure = 110 mm Hg) AND (heart failure worsening) AND (hospitalization) AND (non-steroidal anti-inflammatory drugs) AND (respiratory failure) AND (risk profession) AND (stenosis of renal artery relevant bilateral > 75%) AND (transient ischemic attack) AND (treatment Concomitant) AND (treatment Previous) AND (treatment continuous))"}
{"candidate_id": "LLM06034", "doc_id": "NCT03253796_inc", "case_bucket": "or", "source_criterion": "Is not of reproductive potential, or is of reproductive potential and agrees to avoid becoming pregnant or impregnating a partner while receiving trial medication or within 6 months after the last dose of trial medication Has chronic back pain of =3 months duration by history Has physician-diagnosed active nr-axSpA with disease duration <= 5 years • Inflammatory back pain • Arthritis (physician-diagnosed) • Enthesitis (heel) physician-diagnosed (spontaneous pain or tenderness at examination of the site of the insertion of the Achilles tendon or plantar fascia) • Dactylitis (physician-diagnosed) • Psoriasis (physician-diagnosed) • History of physician-diagnosed inflammatory bowel disease (IBD) • History of uveitis confirmed by an ophthalmologist • Good response to nonsteroidal anti-inflammatory drugs (NSAID) • Family history of SpA (presence of ankylosing spondylitis, psoriasis, acute uveitis, reactive arthritis, or IBD) • Elevated CRP • Human leukocyte antigen B27 (HLA-B27)+ gene Has a HLA-B27+ gene and 2 or more of the SpA characteristics listed above Has elevated CRP at Screening or evidence of active inflammation in the sacroiliac joints on MRI Has an ASDAS >= 2.1 at Screening Shows high disease activity at Screening and Baseline of both a Total Back Pain score of =4 and a Bath Ankylosing Spondylitis Disease Activity Index (BASDAI) score of >= 4 Has an acceptable history of NSAID use Has no history of untreated latent or active tuberculosis (TB) prior to Screening Has had no recent close contact with a person with active TB or, if there has been such contact, will undergo additional evaluations and receive appropriate treatment for latent TB", "candidate_expression": "(((HLA-B27)+) AND (ASDAS >= 2.1 at Screening) AND (Arthritis) AND (Bath Ankylosing Spondylitis Disease Activity Index (BASDAI) score >= 4) AND (CRP Elevated) AND (Dactylitis) AND (Enthesitis heel) AND (Good response) AND (HLA-B27+) AND (Inflammatory back pain) AND (Is not of reproductive potential, or is of reproductive potential and agrees to avoid becoming pregnant or impregnating a partner while receiving trial medication or within 6 months after the last dose of trial medication) AND (MRI) AND (NSAID acceptable history) AND (Psoriasis) AND (SpA 2 or more) AND (SpA Family history) AND (Total Back Pain score =4) AND (chronic back pain =3 months duration history) AND (close contact recent) AND (disease duration <= 5 years) AND (duration =3 months) AND (gene Human leukocyte antigen B27) AND (high disease activity at Screening and Baseline) AND (inflammatory bowel disease (IBD) History) AND (nonsteroidal anti-inflammatory drugs (NSAID)) AND (nr-axSpA active disease duration <= 5 years) AND (person with active TB) AND (tuberculosis (TB) history untreated) AND (uveitis History) AND ((pain) OR (tenderness)) AND ((plantar fascia) OR (site of the insertion of the Achilles tendon)) AND ((IBD) OR (acute uveitis) OR (ankylosing spondylitis) OR (psoriasis) OR (reactive arthritis)) AND ((CRP elevated at Screening) OR (inflammation active sacroiliac joints)) AND ((active) OR (latent)))"}
{"candidate_id": "LLM06035", "doc_id": "NCT03040024_exc", "case_bucket": "or", "source_criterion": "Emergency surgery Monitored Anesthesia Care (i.e., regional anesthesia alone without plans for general anesthesia) Surgery involving the eye, eyebrow, forehead, or frontal scalp near the sensor placement Poor health literacy Allergy, or have experienced any drug reaction to ketamine Pregnant or lactating Currently in active alcohol withdrawal", "candidate_expression": "((Emergency) AND (Emergency surgery) AND (Monitored Anesthesia Care) AND (Poor health literacy) AND (Surgery) AND (alcohol withdrawal Currently active) AND (ketamine) AND (regional anesthesia alone) AND NOT (general anesthesia plans for) AND ((eye) OR (eyebrow) OR (forehead) OR (frontal scalp)) AND ((Allergy) OR (drug reaction)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM06036", "doc_id": "NCT02830360_exc", "case_bucket": "or", "source_criterion": "Unable or unwilling to provide informed consent. Active ischemia (acute thrombus diagnosed by coronary angiography, or dynamic ST segment changes demonstrated on ECG) or another reversible cause of VT (e.g. drug-induced arrhythmia), had recent acute coronary syndrome within 30 days, coronary revascularization (<90 days bypass surgery, <30 days percutaneous coronary intervention), or have CCS functional class IV angina. Note that biomarker level elevation alone after ventricular arrhythmias does not denote acute coronary syndrome or active ischemia. Are ineligible to take the antiarrhythmic drug to which they would be assigned due to allergy, intolerance or contraindication Are known to have protruding left ventricular thrombus or mechanical aortic and mitral valves Have had a prior catheter ablation procedure for VT Are in renal failure (Creatinine clearance <15 mL/min), have NYHA Functional class IV heart failure, or a systemic illness likely to limit survival to <1 year Have had recent ST elevation myocardial infarction or non-ST elevation MI (< 30 days); note that biomarker elevation alone after ventricular arrhythmias does not denote MI. Are pregnant.", "candidate_expression": "((CCS functional class IV) AND (Creatinine clearance <15 mL/min) AND (ECG) AND (NYHA Functional class IV) AND (ST elevation myocardial infarction) AND (ST segment changes) AND (Unable or unwilling to provide informed consent) AND (VT) AND (VT reversible) AND (acute coronary syndrome within 30 days,) AND (acute thrombus) AND (allergy) AND (angina) AND (antiarrhythmic drug) AND (bypass surgery <90 days) AND (catheter ablation procedure) AND (contraindication) AND (coronary angiography) AND (coronary revascularization) AND (drug-induced arrhythmia) AND (heart failure) AND (intolerance) AND (ischemia Active) AND (left ventricular thrombus) AND (mechanical aortic valves) AND (mechanical mitral valves) AND (non-ST elevation MI) AND (percutaneous coronary intervention <30 days) AND (pregnant) AND (renal failure) AND (systemic illness survival))"}
{"candidate_id": "LLM06037", "doc_id": "NCT03404804_inc", "case_bucket": "other", "source_criterion": "Children aged 3-16 with a parent/guardian (hereafter termed parent) reported history of allergy to a penicillin antibiotic in which the reported allergic reaction occurred at least six months prior to the current PED visit. Only children well enough to be discharged to home at the conclusion of the PED visit are eligible.", "candidate_expression": "((Children) AND (PED) AND (aged 3-16) AND (allergic reaction at least six months prior to the current PED visit) AND (allergy) AND (penicillin antibiotic) AND (well enough to be discharged to home at the conclusion of the PED visit))"}
{"candidate_id": "LLM06038", "doc_id": "NCT03506009_inc", "case_bucket": "other", "source_criterion": "18-80 years old; Diagnosis of posterior circulation ischemic stroke; Time from onset to treatment =6 hours; NIHSS: 4-25; Signed informed consent by patient self or legally authorized representatives.", "candidate_expression": "((18-80 years old) AND (4-25) AND (=6 hours) AND (NIHSS) AND (Signed informed consent by patient self or legally authorized representatives.) AND (Time from onset to treatment) AND (old) AND (posterior circulation ischemic stroke))"}
{"candidate_id": "LLM06039", "doc_id": "NCT03351972_inc", "case_bucket": "other", "source_criterion": "Adult outpatients (18 years or older) routinely referred for small bowel video capsule endoscopy (CE)", "candidate_expression": "((18 years or older) AND (Adult) AND (outpatients) AND (routinely referred) AND (small bowel video capsule endoscopy))"}
{"candidate_id": "LLM06040", "doc_id": "NCT03236246_exc", "case_bucket": "other", "source_criterion": "Serum phosphate <3.0 mg/dL Intravenous (IV) iron administered within 4 weeks prior to Screening Erythropoiesis-stimulating agents (ESA) administered within 4 weeks prior to Screening Blood transfusion within 4 weeks prior to Screening", "candidate_expression": "((Blood transfusion within 4 weeks prior to Screening) AND (ESA within 4 weeks prior to Screening) AND (Erythropoiesis-stimulating agents) AND (Serum phosphate <3.0 mg/dL) AND (iron Intravenous within 4 weeks prior to Screening IV))"}
{"candidate_id": "LLM06041", "doc_id": "NCT02334631_inc", "case_bucket": "other", "source_criterion": "Patients undergoing small bowel video capsule endoscopy", "candidate_expression": "(small bowel video capsule endoscopy)"}
{"candidate_id": "LLM06042", "doc_id": "NCT03373669_inc", "case_bucket": "other", "source_criterion": "Age =1 year, stratified into different age groups Living in the Waya Clinic Catchment Area Good health condition, without clinically significant medical history (by participant or guardian, in case of minor) Not pregnant for female subjects. Available to participate for the study duration, including all planned follow-up visits for up to 9 months from screening. Signed informed consent", "candidate_expression": "((=1 year) AND (Age) AND (Available to participate for the study duration, including all planned follow-up visits for up to 9 months from screening.) AND (Good health condition) AND (Living) AND (Not) AND (Signed informed consent) AND (Waya Clinic Catchment Area) AND (clinically significant) AND (female) AND (medical history) AND (pregnant) AND (without))"}
{"candidate_id": "LLM06043", "doc_id": "NCT01261832_exc", "case_bucket": "or", "source_criterion": "The patient has a known hypersensitivity or contraindication to any of the following medications: Heparin, Aspirin, Clopidogrel, Cilostazol Uncontrolled hypertension History of bleeding diathesis or known coagulopathy (including heparin-induced thrombocytopenia), or refuses blood transfusions. Baseline hemogram with Hb<10g/dL or PLT count<100,000/μL Patients already taking warfarin, cilostazol or any other type of anti-platelet agents except aspirin and clopidogrel Gastrointestinal or genitourinary bleeding within the prior 3 months, or major surgery within 2 months. Pregnancy", "candidate_expression": "((Aspirin) AND (Cilostazol) AND (Clopidogrel) AND (Gastrointestinal bleeding) AND (Hb <10g/dL) AND (Heparin) AND (PLT count <100,000/μL) AND (Pregnancy) AND (anti-platelet agents) AND (aspirin) AND (bleeding diathesis History) AND (blood transfusions) AND (cilostazol) AND (clopidogrel) AND (coagulopathy) AND (contraindication) AND (genitourinary bleeding) AND (hemogram Baseline) AND (heparin-induced thrombocytopenia) AND (hypersensitivity) AND (hypertension Uncontrolled) AND (major surgery within 2 months) AND (refuses blood transfusions) AND (warfarin))"}
{"candidate_id": "LLM06044", "doc_id": "NCT02267616_exc", "case_bucket": "other", "source_criterion": "Have history of female sterilization procedure Desire for conception in the next 12 months Not sexually active with a male partner", "candidate_expression": "((Desire) AND (Not) AND (conception) AND (female sterilization procedure) AND (in the next 12 months) AND (male partner) AND (sexually active))"}
{"candidate_id": "LLM06045", "doc_id": "NCT03350815_inc", "case_bucket": "or", "source_criterion": "Understand and communicate with the investigator, comply with the requirements of the study and give a written, signed and dated informed consent Male or non-pregnant, non-lactating female patients at least 18 years of age Diagnosis of moderate to severe Ankylosing Spondylitis (AS) with prior documented radiologic evidence fulfilling the Modified New York criteria for AS Active AS assessed by total Bath Ankylosing Spondylitis Disease Activity index (BASDAI) = 4 (0-10) at baseline Spinal pain as measured by BASDAI question #2 = 4 cm (0-10 cm) at baseline Total back pain as measured by visual analog scale (VAS) = 40 mm (0-100 mm) at baseline Patients should have been on non-steroidal anti-inflammatory drugs (NSAIDs) at the maximum tolerated dose for at least 4 weeks prior to their Baseline Visit, with an inadequate response or for less than 4 weeks if withdrawn for intolerance, toxicity or contraindications Stable dose of NSAIDs including Cyclooxygenase-1 (COX-1) or Cyclooxygenase-2 (COX-2) inhibitors for at least 2 weeks before their Baseline Visit Patients who have been on a tumor necrosis factor alpha (TNFa) inhibitor (not more than one) must have experienced an inadequate response to previous or current treatment given at an approved dose for at least 3 months prior to baseline or had been intolerant upon administration of an anti-TNFa agent Total ankylosis of the spine Use of other investigational drugs within 5 half-lives of enrollment, or within 4 weeks before the Baseline Visit, whichever is longer. History of hypersensitivity to any of the study drugs or its excipients or to drugs of similar chemical classes. Chest x-ray, computerized tomography (CT) scan, or chest magnetic resonance imaging (MRI) with evidence of ongoing infectious or malignant process, obtained within 3 months prior to screening and evaluated by a qualified physician. Previous exposure to secukinumab or any other biologic drug directly targeting Interleukin-17 (IL-17), Interleukin-12/23 (IL-12/23), or the IL-17 receptor, or any other biologic immunomodulating agent, except those targeting TNFa Patients who have taken more than one anti-TNFa agent Any intramuscular or intravenous corticosteroid injection within 2 weeks before baseline Any therapy by intra-articular injections (e.g. corticosteroid) within 4 weeks before baseline Previous treatment with any cell-depleting therapies Patients taking high potency opioid analgesics (e.g., methadone, hydromorphone, morphine)", "candidate_expression": "((= 4) AND (= 4 cm) AND (= 40 mm) AND (AS) AND (Active) AND (Ankylosing Spondylitis (AS)) AND (BASDAI question #2) AND (Chest x-ray) AND (Cyclooxygenase-2 (COX-2) inhibitors) AND (IL-17 receptor) AND (Interleukin-12/23 (IL-12/23)) AND (Interleukin-17 (IL-17)) AND (Male or non-pregnant, non-lactating female patients at least 18 years of age) AND (Modified New York criteria for AS) AND (NSAIDs) AND (Previous) AND (Spinal pain) AND (TNFa) AND (Total ankylosis of the spine) AND (Total back pain) AND (Understand and communicate with the investigator, comply with the requirements of the study and give a written, signed and dated informed consent) AND (Use of other investigational drugs within 5 half-lives of enrollment, or within 4 weeks before the Baseline Visit, whichever is longer.) AND (anti-TNFa agent) AND (approved dose) AND (at baseline) AND (baseline) AND (biologic drug) AND (biologic immunomodulating agent) AND (cell-depleting therapies) AND (chest magnetic resonance imaging (MRI)) AND (computerized tomography (CT) scan) AND (contraindications) AND (corticosteroid) AND (corticosteroid injection) AND (current) AND (drugs of similar chemical classes) AND (except) AND (excipients) AND (for at least 2 weeks before their Baseline Visit) AND (for at least 3 months prior to baseline) AND (for at least 4 weeks prior to their Baseline Visit) AND (for less than 4 weeks) AND (fulfilling) AND (high potency opioid analgesics) AND (hydromorphone) AND (hypersensitivity) AND (inadequate response) AND (infectious) AND (inhibitors Cyclooxygenase-1 (COX-1)) AND (intolerant) AND (intra-articular injections) AND (intramuscular) AND (intravenous) AND (malignant process) AND (maximum tolerated dose) AND (methadone) AND (moderate) AND (more than one) AND (morphine) AND (non-steroidal anti-inflammatory drugs (NSAIDs)) AND (not more than one) AND (ongoing) AND (other) AND (previous) AND (prior) AND (radiologic) AND (radiologic evidence) AND (secukinumab) AND (severe) AND (study drugs) AND (targeting) AND (their Baseline Visit) AND (total Bath Ankylosing Spondylitis Disease Activity index (BASDAI)) AND (treatment) AND (tumor necrosis factor alpha (TNFa) inhibitor) AND (visual analog scale (VAS)) AND (withdrawn for intolerance) AND (withdrawn for toxicity) AND (within 2 weeks before baseline) AND (within 3 months prior to screening) AND (within 4 weeks before baseline))"}
{"candidate_id": "LLM06046", "doc_id": "NCT02542956_inc", "case_bucket": "or", "source_criterion": "Undergoing abdominoplasty or TRAM flap breast reconstruction", "candidate_expression": "((TRAM flap breast reconstruction) OR (abdominoplasty))"}
{"candidate_id": "LLM06047", "doc_id": "NCT02589353_inc", "case_bucket": "other", "source_criterion": "self-reported healthy adults between the ages of 18-60 who are fluent in English.", "candidate_expression": "((adults) AND (ages) AND (between 18-60) AND (fluent in English) AND (healthy) AND (self-reported))"}
{"candidate_id": "LLM06048", "doc_id": "NCT02205931_inc", "case_bucket": "other", "source_criterion": "Age between 1 month and 24 months of age (not beyond second birthday at baseline). Diagnosis of epilepsy confirmed. At least an average of 4 seizures/week in baseline period. Failed response to previous trial of two anti-epileptic drugs. In the case of infantile spasms this could include a trial of corticosteroids. Children with written informed consent from parent/guardian.", "candidate_expression": "((Age between 1 month and 24 months of age) AND (Children with written informed consent from parent/guardian) AND (anti-epileptic drugs two) AND (corticosteroids) AND (epilepsy) AND (response Failed) AND (seizures At least an average of 4 /week))"}
{"candidate_id": "LLM06049", "doc_id": "NCT02200978_exc", "case_bucket": "or", "source_criterion": "Patients who have coma, convulsion or paralysis due to intracranial hemorrhage or central nervous system leukemia at diagnosis.", "candidate_expression": "((at diagnosis) AND (central nervous system) AND (coma) AND (convulsion) AND (intracranial hemorrhage) AND (leukemia) AND (paralysis))"}
{"candidate_id": "LLM06050", "doc_id": "NCT02205931_inc", "case_bucket": "other", "source_criterion": "Age between 1 month and 24 months of age (not beyond second birthday at baseline). Diagnosis of epilepsy confirmed. At least an average of 4 seizures/week in baseline period. Failed response to previous trial of two anti-epileptic drugs. In the case of infantile spasms this could include a trial of corticosteroids. Children with written informed consent from parent/guardian.", "candidate_expression": "((Age) AND (At least an average of 4 /week) AND (Children with written informed consent from parent/guardian) AND (Failed) AND (anti-epileptic drugs) AND (between 1 month and 24 months of age) AND (corticosteroids) AND (epilepsy) AND (response) AND (seizures) AND (two))"}
```
