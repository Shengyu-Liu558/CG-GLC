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
{"candidate_id": "LLM01801", "doc_id": "NCT02764476_inc", "case_bucket": "or", "source_criterion": "Adults 18-65 years, who are diagnosed with functional neurologic symptom or conversion disorder. If diagnosis of seizure type then video EEG with diagnosis confirmed by board-certified neurologist with subspecialty training in epilepsy and clinical neurophysiology using the criteria of the International Classification of the Epilepsies is required. If diagnosis of motor type, documented and clinically established levels of diagnostic certainty (Williams,1995) confirmed by 2 neurologists is required. Participants must have at least one symptom per month in the month prior to enrollment Fluency in English spoken language", "candidate_expression": "((18-65 years) AND (Adults) AND (at least one per month) AND (criteria of the International Classification of the Epilepsies) AND (in the month prior to enrollment) AND (motor type) AND (seizure type) AND (symptom) AND (to enrollment) AND (video EEG) AND ((conversion disorder) OR (functional neurologic symptom)))"}
{"candidate_id": "LLM01802", "doc_id": "NCT02022709_exc", "case_bucket": "or", "source_criterion": "Having significant medical illnesses that would interfere with the conduct of the study Clinically significant abnormal laboratory finding Having comorbid psychiatric conditions according to the criteria set forth in the DSM-IV(administered by the Mini-International Neuropsychiatric Interview (MINI)) The current OCD symptoms are too severe that the patient cannot finish the evaluation or receive the ERP Being currently at risk for suicide Being pregnant or having the intention to be pregnant before the end of the study A history of having inadequate response to adequate SSRIs or CBT treatment Subjects who are unable to undergo the MRI", "candidate_expression": "((Being pregnant or having the intention to be pregnant before the end of the study) AND (MRI unable to) AND (OCD symptoms severe) AND (psychiatric conditions comorbid DSM-IV) AND (response inadequate) AND (risk for suicide) AND ((CBT) OR (SSRIs)))"}
{"candidate_id": "LLM01803", "doc_id": "NCT02874092_inc", "case_bucket": "scope", "source_criterion": "RA cohort: Receiving MTX at stable doses of 10 to 25 mg weekly for at least 12 weeks, Have a DAS28 of 3.2 or higher (The level of disease activity is considered to be low if the DAS28 is 3.2 or less) (Prevoo et al., 1995) OA cohort: Diagnosis of osteoarthritis made by physician.", "candidate_expression": "((DAS28 3.2 or higher) AND (MTX stable doses 10 to 25 mg weekly for at least 12 weeks) AND (OA) AND (RA) AND (osteoarthritis made by physician))"}
{"candidate_id": "LLM01804", "doc_id": "NCT01236417_inc", "case_bucket": "or", "source_criterion": "Post menopausal women with a history of estrogen positive breast cancer who are receiving aromatase inhibitors for at least one month. Patients must complain of mild to moderate arthralgia. Ability to understand and sign informed consent. Patients meet criteria for low to moderate risk for moderate exercise based oon the ACSM guidelines.", "candidate_expression": "((ACSM guidelines) AND (Ability to understand and sign informed consent.) AND (Post menopausal) AND (aromatase inhibitors for at least one month) AND (arthralgia mild moderate) AND (breast cancer history estrogen positive) AND (risk for moderate exercise low moderate) AND (women))"}
{"candidate_id": "LLM01805", "doc_id": "NCT03187639_inc", "case_bucket": "other", "source_criterion": "Aged over 18 Primary symptom of chest pain No contraindication to CTA Willing and able to provide written informed consent", "candidate_expression": "((Aged over 18) AND (CTA) AND (Willing and able to provide written informed consent) AND (chest pain Primary symptom) AND NOT (contraindication))"}
{"candidate_id": "LLM01806", "doc_id": "NCT03356834_inc", "case_bucket": "other", "source_criterion": "Chronic hepatitis B, Antiviral experienced, Currently on long term TDF anti-HBV treatment, HBV DNA < 6 log IU/ml (LLOD) Able to sign the consent form of anticipating in the study", "candidate_expression": "((Able to sign the consent form of anticipating in the study) AND (Antiviral experienced) AND (Chronic hepatitis B) AND (HBV) AND (HBV DNA < 6 log IU/ml LLOD) AND (TDF anti-HBV treatment) AND (TDF long term) AND (experienced))"}
{"candidate_id": "LLM01807", "doc_id": "NCT02959580_exc", "case_bucket": "other", "source_criterion": "Breast Carcinoma", "candidate_expression": "(Breast Carcinoma)"}
{"candidate_id": "LLM01808", "doc_id": "NCT02476461_exc", "case_bucket": "other", "source_criterion": "previous treated dupuytrens contracture same hand more than tree fingers involvement we will not include thumbs other things affecting hand function ASA>3 expected to live under five years Tetracycline treatment within two weeks pregnancy nursing allergy to clostridium histolyticum participant in other trial", "candidate_expression": "((ASA >3) AND (Tetracycline within two weeks) AND (allergy clostridium histolyticum) AND (dupuytrens contracture previous treated same hand) AND (expected to live under five years) AND (fingers involvement more than tree) AND (nursing) AND (other things affecting hand function) AND (participant in other trial) AND (pregnancy))"}
{"candidate_id": "LLM01809", "doc_id": "NCT02731794_exc", "case_bucket": "other", "source_criterion": "myocardial infarction within the preceding 4 weeks severe valve disease requiring valve replacement cardiac reoperations", "candidate_expression": "((cardiac reoperations) AND (myocardial infarction within the preceding 4 weeks) AND (valve disease severe requiring valve replacement) AND (valve replacement))"}
{"candidate_id": "LLM01810", "doc_id": "NCT02072811_exc", "case_bucket": "other", "source_criterion": "No informed consent for participation in the study, mental illness, which don't allow to obtain informed consent and conduct the treatment according to the protocol Pregnancy HIV infection Active cancer Active hepatitis virus infection", "candidate_expression": "((Active) AND (HIV infection) AND (Pregnancy) AND (cancer) AND (hepatitis virus infection))"}
{"candidate_id": "LLM01811", "doc_id": "NCT02656394_exc", "case_bucket": "or", "source_criterion": "1. Comorbidity with other severe or chronic eye conditions that in the judgment of the investigator will interfere with study assessments, such as corneal opacities and scars, dystrophies, epithelial scarring, infections, blood clots, etc. 2. Best corrected visual acuity (BCVA) at baseline <20/200. 3. Has a condition or history that, in the opinion of the investigator, may interfere significantly with the subject's participation in the study. 4. A woman who is pregnant, nursing an infant, or planning a pregnancy. 5. Has a known adverse reaction and/or sensitivity to the study drug or its components. 6. Routine use (more than twice a week) of a chlorinated swimming pool. 7. Unwilling or unable to cease using the following medications during the study period: Topical ocular cyclosporine (e.g. Restasis®), anti-histamines, antipsychotics, or eye gels. 8. Currently enrolled in an investigational drug or device study or have used an investigational drug or device within 30 days prior to Visit 1.", "candidate_expression": "((Best corrected visual acuity (BCVA) at baseline <20/200) AND (Restasis®) AND (Unwilling or unable) AND (chlorinated swimming pool Routine use more than twice a week) AND (eye conditions will interfere with study assessments) AND (in the judgment of the investigator) AND (in the opinion of the investigator) AND (may interfere significantly) AND (woman) AND ((blood clots) OR (corneal opacities) OR (corneal scars) OR (dystrophies) OR (epithelial scarring) OR (infections)) AND ((nursing) OR (pregnancy) OR (pregnant)) AND ((adverse reaction to the study drug or its components) OR (sensitivity to the study drug or its components)) AND ((Topical ocular cyclosporine) OR (anti-histamines) OR (antipsychotics) OR (eye gels)) AND ((investigational device) OR (investigational drug)))"}
{"candidate_id": "LLM01812", "doc_id": "NCT03589105_inc", "case_bucket": "or", "source_criterion": "Age >/=18 years at screening Patients with relapsing forms of multiple sclerosis (RMS) with active disease defined by clinical or imaging features: (i) at least one clinical relapse over a 6-month period prior to screening; (ii) AND/OR at least one T1 gadolinium-enhancing lesion or new and/or enlarging T2 lesion as detected by brain Magnetic Resonance Imaging (MRI) performed over a 3 months period prior to screening with no change of Disease-Modifying Treatment(s) (DMT) compared to a previous MRI performed within 24 months before screening For women of childbearing potential: agreement to use an acceptable birth control method during the treatment period and for at least 12 months after the last dose of ocrelizumab Participants should be beneficiary of healthcare coverage under the social security system", "candidate_expression": "((Age >/=18 years at screening) AND (Disease-Modifying Treatment(s) (DMT) change of) AND (For women of childbearing potential: agreement to use an acceptable birth control method during the treatment period and for at least 12 months after the last dose of ocrelizumab) AND (T1 gadolinium-enhancing lesion new enlarging) AND (T2 lesion) AND (beneficiary of healthcare coverage) AND (brain Magnetic Resonance Imaging (MRI)) AND (clinical features) AND (clinical relapse at least one over a 6-month period prior to screening) AND (imaging features) AND (multiple sclerosis (RMS) relapsing forms active disease))"}
{"candidate_id": "LLM01813", "doc_id": "NCT02357654_inc", "case_bucket": "or", "source_criterion": "women undergoing IVF/ICSI or frozen embryo transfers (FET) that less than 40 years old.", "candidate_expression": "((ICSI) AND (IVF) AND (frozen embryo transfers (FET)) AND (less than 40 years) AND (old) AND (women))"}
{"candidate_id": "LLM01814", "doc_id": "NCT03317197_inc", "case_bucket": "other", "source_criterion": "The group of patients who participated in the study included adults aged at least 19 years among the atraumatic CA outpatients who came to the ER and received CPR.", "candidate_expression": "((CPR) AND (ER) AND (adults) AND (aged) AND (at least 19 years) AND (atraumatic CA) AND (outpatients))"}
{"candidate_id": "LLM01815", "doc_id": "NCT02959801_exc", "case_bucket": "or", "source_criterion": "presence of subacute or chronic DVT more than 21 days in duration, inability to lie in the prone position required for intervention, terminal systemic disease requiring palliative treatment, active bleeding (from a gastric/duodenal ulcer or the cerebrovascular system), a haemorrhagic stroke within the previous year, an impaired bleeding-clotting profile, and any haemophilic disorder, or pregnancy.", "candidate_expression": "((DVT more than 21 days in duration subacute chronic) AND (bleeding active) AND (duodenal ulcer) AND (gastric ulcer cerebrovascular system) AND (haemophilic disorder) AND (haemorrhagic stroke within the previous year) AND (impaired bleeding-clotting profile) AND (inability to lie in the prone position) AND (palliative treatment requiring) AND (pregnancy) AND (terminal systemic disease))"}
{"candidate_id": "LLM01816", "doc_id": "NCT02041299_inc", "case_bucket": "or", "source_criterion": "Male or female = 2 years of age; Have sickle cell disease (confirmed by Hb electrophoresis or more specific tests) or other conditions with iron overload from repeated blood transfusions (see exclusion criteria for exceptions); Baseline LIC >7 mg/g dw (measured by MRI); Patients who have received no less than 20 transfusions of RBCs; Patients who have received at least 1 transfusion per year in the last 2 years and who are expected to have a continuing requirement (based on Investigator's judgement) during the duration of the trial", "candidate_expression": "((= 2 years) AND (>7 mg/g) AND (Baseline LIC) AND (Hb electrophoresis) AND (MRI) AND (Male) AND (age) AND (at least 1 per year) AND (blood transfusions) AND (during the duration of the trial) AND (expected to have a continuing requirement) AND (female) AND (in the last 2 years) AND (more specific tests) AND (no less than 20) AND (other conditions with iron overload) AND (repeated) AND (sickle cell disease) AND (transfusion) AND (transfusions of RBCs))"}
{"candidate_id": "LLM01817", "doc_id": "NCT03249272_inc", "case_bucket": "or", "source_criterion": "Men or women aged 18 years or older Patients presenting for CMR with the clinical diagnosis of hypertrophic cardiomyopathy based on left ventricular wall thickness of at least =15 mm in the absence of any other cardiac or systemic cause of hypertrophy Patients presenting for CMR with the clinical diagnosis of idiopathic dilated cardiomyopathy based upon left ventricular ejection fraction =40%, LV end-diastolic diameter =55 mm or left ventricular end-systolic diameter =45 mm, and the absence of coronary stenoses on angiography. Patients presenting for CMR evaluation of chest pain but without evidence of obstructive coronary artery disease either by coronary angiography or stress testing.", "candidate_expression": "((18 years or older) AND (=40%) AND (=45 mm) AND (=55 mm) AND (LV end-diastolic diameter) AND (Men) AND (absence) AND (aged) AND (angiography) AND (at least =15 mm) AND (cardiac cause of hypertrophy) AND (chest pain) AND (coronary angiography) AND (coronary stenoses) AND (hypertrophic cardiomyopathy) AND (idiopathic dilated cardiomyopathy) AND (left ventricular ejection fraction) AND (left ventricular end-systolic diameter) AND (left ventricular wall thickness) AND (obstructive coronary artery disease) AND (stress testing) AND (systemic cause of hypertrophy) AND (without) AND (women))"}
{"candidate_id": "LLM01818", "doc_id": "NCT02984475_inc", "case_bucket": "scope", "source_criterion": "Diagnosed with Beta-Thalassemia Major and receiving regular blood transfusion and on iron chelating therapy. Weight: equal to or over 35 kg. Normal renal function.", "candidate_expression": "((Beta-Thalassemia Major) AND (Weight equal to or over 35 kg) AND (blood transfusion) AND (iron chelating therapy) AND (renal function Normal))"}
{"candidate_id": "LLM01819", "doc_id": "NCT00586898_inc", "case_bucket": "or", "source_criterion": "-Patients residing in the following clinical states wit! be considered: A. Rising PSA: Patients with a history of localized disease who have undergone definitive radiation or surgery. These patients must demonstrate progression of disease biochemically as outlined below. Patients in this group may not have radiographically evident disease. B. Non-castrate metastatic: Patients must present with radiographic evidence of metastatic disease at the time of diagnosis or after treatment for localized disease. These patients must show newly detected disease or progressing disease in bone or in soft tissue. Biochemical progression is defined as: minimum no. of determinations: 3 Interval: >2 weeks Minimal Baseline PSA value (ng/ml): 2 Minimal % increase in range of values: 50% Diagnosis of prostate adenocarcinoma histologically confirmed at MSKCC. Patient must have level of serum testosterone above the lower limit of normal. Karnofskcy performance status (KPS) >_70%. Patients must have adequate organ function as defined by the following laboratory criteria: WBC >_3500/mm3, platelet count >_100,000/mm3. Bilirubin <2.0 mg/dl or SGOT <3.0 X the upper limit of normal. Creatinine <_1.6 mg/dl or creatinine clearance >_60 cc/min. Prior hormonal therapy is allowed as: 1. Neoadjuvant treatment prior to radiation therapy or radical prostatectomy, provided that the total duration of exposure does not exceed 10 months. 2. One cycle of intermittent therapy up to a maximum exposure of 10 months. Patients must be at least 18 years of age. Patients must have signed an informed consent document stating that they understand the investigational nature of the proposed treatment", "candidate_expression": "((Bilirubin <2.0 mg/dl) AND (Creatinine <_1.6 mg/dl) AND (Interval >2 weeks) AND (Karnofskcy performance status (KPS) >_70%) AND (Minimal % increase in range of values 50%) AND (Minimal Baseline PSA value (ng/ml): 2) AND (Neoadjuvant treatment prior to radiation therapy or radical prostatectomy) AND (PSA Rising) AND (SGOT <3.0 X the upper limit of normal) AND (WBC >_3500/mm3) AND (adequate organ function) AND (age at least 18 years) AND (creatinine clearance >_60 cc/min) AND (disease in bone) AND (disease in soft tissue) AND (disease radiographically evident Non-castrate metastatic) AND (histologically confirmed) AND (hormonal therapy Prior is allowed) AND (intermittent therapy One cycle) AND (level of serum testosterone above the lower limit of normal) AND (localized disease) AND (localized disease history of) AND (maximum exposure 10 months) AND (metastatic disease at the time of diagnosis) AND (minimum no. of determinations 3) AND (organ function adequate) AND (platelet count >_100,000/mm3) AND (progressing disease in bone Biochemical progression) AND (progressing disease in soft tissue Biochemical progression) AND (progression of disease biochemically) AND (prostate adenocarcinoma histologically confirmed) AND (radiation) AND (radiation therapy) AND (radical prostatectomy) AND (radiographic radiographic evidence) AND (signed an informed consent document) AND (surgery) AND (total duration of exposure does not exceed 10 months) AND (treatment after treatment for localized disease treatment for localized disease))"}
{"candidate_id": "LLM01820", "doc_id": "NCT02224040_exc", "case_bucket": "or", "source_criterion": "Allergy to ceftriaxone or macrolides Major typhoid fever-associated complications Inability to swallow oral medication Underlying illness Pregnancy Lactation Treatment within the past 4 days with an antibiotic that may be effective against typhoid fever", "candidate_expression": "((Allergy) AND (Inability to swallow oral medication) AND (Lactation) AND (Major) AND (Pregnancy) AND (Underlying illness) AND (antibiotic) AND (complications) AND (effective against typhoid fever) AND (oral medication) AND (typhoid fever) AND (typhoid fever-associated) AND (within the past 4 days) AND ((ceftriaxone) OR (macrolides)))"}
{"candidate_id": "LLM01821", "doc_id": "NCT01895946_exc", "case_bucket": "or", "source_criterion": "Clinically significant abnormalities of glucose metabolism Spinal cord compression or brain metastases unless asymptomatic, treated and stable (not requiring steroids) Evidence of severe or uncontrolled systemic diseases, including active bleeding diatheses or active infections including hepatitis B, C and Human Immunodeficiency Virus (HIV) Evidence of clinically significant cardiac abnormalities, uncontrolled hypotension, left ventricular ejection fraction below the lower limit of normal for the site or experience of significant cardiac interventional procedures A bad reaction to AZD5363 or any drugs similar to it in structure or class", "candidate_expression": "((AZD5363) AND (Clinically significant) AND (Human Immunodeficiency Virus (HIV)) AND (Spinal cord compression) AND (abnormalities of glucose metabolism) AND (active bleeding diatheses) AND (active infections) AND (asymptomatic) AND (bad reaction to AZD5363) AND (below the lower limit of normal) AND (brain metastases) AND (cardiac abnormalities) AND (cardiac interventional procedures) AND (clinically significant) AND (hepatitis B) AND (hepatitis C) AND (left ventricular ejection fraction) AND (not) AND (severe) AND (significant) AND (stable) AND (steroids) AND (systemic diseases) AND (treated) AND (uncontrolled) AND (uncontrolled hypotension) AND (unless))"}
{"candidate_id": "LLM01822", "doc_id": "NCT02340169_inc", "case_bucket": "or", "source_criterion": "Patients aged 7 years and older must have provided written assent accompanied by written informed consent from patient's representative Clinical diagnosis of stable plaque psoriasis with involvement of = 10% body surface area (excluding face and scalp) Physicians Global Assessment score of 3 or 4 at baseline", "candidate_expression": "((3) AND (4) AND (7 years and older) AND (= 10%) AND (Physicians Global Assessment score) AND (aged) AND (at baseline) AND (body surface area) AND (excluding) AND (face) AND (must have provided written assent accompanied by written informed consent from patient's representative) AND (plaque psoriasis) AND (scalp) AND (stable))"}
{"candidate_id": "LLM01823", "doc_id": "NCT03104816_inc", "case_bucket": "or", "source_criterion": "ASA I-III patients scheduled for elective one or two level minimally invasive lumbar fusions", "candidate_expression": "((ASA) AND (I-III) AND (elective) AND (minimally invasive lumbar fusions) AND (one level) AND (scheduled) AND (two level))"}
{"candidate_id": "LLM01824", "doc_id": "NCT02528136_inc", "case_bucket": "other", "source_criterion": "Healthy pregnant women age 18 to 50 Singleton pregnancy at gestational age 36 weeks or more Able to read and understand Norwegian.", "candidate_expression": "((Able to read and understand Norwegian) AND (Healthy) AND (Singleton pregnancy) AND (age 18 to 50) AND (gestational age 36 weeks or more) AND (pregnant) AND (women))"}
{"candidate_id": "LLM01825", "doc_id": "NCT02546856_exc", "case_bucket": "or", "source_criterion": "Contraindications for BB. Living in a nursing home. Life expectancy < 6 months. Unable to self-care or mental disease without caregiver. Unable to weight Without phone Unable to go to clinic visit.", "candidate_expression": "((BB) AND (Contraindications) AND (Life expectancy < 6 months) AND (Living) AND (Unable) AND (go to clinic visit Unable) AND (nursing home) AND (weight) AND NOT (phone) AND ((Unable to self-care) OR (mental disease without caregiver)))"}
```
