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
{"candidate_id": "LLM05376", "doc_id": "NCT02419378_inc", "case_bucket": "or", "source_criterion": "Signed informed consent form (ICF) Age 18 to 55 years old (inclusive) as of the date the ICF is signed Diagnosis of MS according to the McDonald criteria 2010 and cranial MRI scan demonstrating white matter lesions attributable to MS within 10 years before Screening Onset of MS symptoms (as determined by a neurologist, either at present or retrospectively) within 10 years of the date the ICF is signed EDSS score 0.0 to 5.0 (inclusive) at Screening Patients with (highly) active RRMS disease course indicated to receive alemtuzumab according to the following conditions (at least 1 out of 3 conditions has to be fulfilled): 1. =2 MS relapses within 24 months, 2. clinical (=1 relapse) or MRI (new gadolinium enhancing lesions) disease activity under therapy with other diseasemodifying therapies, 3. severe relapse with high disease activity (=9 T2 hyperintense Lesions and =1 gadolinium enhancing lesion) on MRI. Completion of all vaccinations required by the applicable immunization guidelines published by \"ständige Impfkommission\" (STIKO) History of chickenpox or positive test for antibodies against varicella zoster virus (VZV)", "candidate_expression": "((0.0 to 5.0) AND (18 to 55 years old () AND (=1) AND (=2) AND (=9) AND (Age) AND (EDSS score) AND (Lesions) AND (MRI) AND (MS) AND (MS relapses) AND (MS symptoms) AND (McDonald criteria 2010) AND (RRMS) AND (Signed informed consent form (ICF)) AND (T2 hyperintense) AND (VZV) AND (active) AND (alemtuzumab) AND (cranial MRI scan) AND (gadolinium enhancing) AND (lesion) AND (lesions) AND (new) AND (positive) AND (relapse) AND (severe) AND (varicella zoster virus) AND (within 10 years) AND (within 10 years before Screening) AND (within 24 months,) AND ((MRI) OR (relapse)) AND ((chickenpox) OR (test for antibodies)))"}
{"candidate_id": "LLM05377", "doc_id": "NCT03424733_inc", "case_bucket": "or", "source_criterion": "diagnosed any form of MS (relapsing remitting, primary progressive, secondary progressive), any EDSS (expanded stability status scale) score", "candidate_expression": "((MS any form relapsing remitting primary progressive secondary progressive) AND (expanded stability status scale) AND (score EDSS any))"}
{"candidate_id": "LLM05378", "doc_id": "NCT03062358_inc", "case_bucket": "or", "source_criterion": "Has a HCC diagnosis confirmed by radiology, histology, or cytology (fibrolamellar, and mixed hepatocellular/cholangiocarcinoma subtypes are not eligible) Has Barcelona Clinic Liver Cancer (BCLC) Stage C disease or BCLC Stage B disease not amenable to locoregional therapy or refractory to locoregional therapy and not amenable to a curative treatment approach Has a Child-Pugh A liver score within 7 days prior to first dose of study medication Has a life expectancy of >3 months Has at least one measurable lesion based on RECIST version 1.1 as determined by investigator Has Eastern Cooperative Oncology Group (ECOG) performance status of 0 or 1 performed within 7 days prior to receiving the first dose of study medication Has documented objective radiographic progression during or after treatment with sorafenib or oxaliplatin-based chemotherapy, or else intolerance to sorafenib or oxaliplatin-based chemotherapy Female participants of childbearing potential must have a negative urine or serum pregnancy test within 72 hours prior to receiving the first dose of study therapy Female and male participants of reproductive potential must agree to use adequate contraception starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication", "candidate_expression": "((BCLC Stage B) AND (Barcelona Clinic Liver Cancer (BCLC) Stage C) AND (Child-Pugh liver score A within 7 days prior) AND (Eastern Cooperative Oncology Group (ECOG) performance status 0 or 1 within 7 days prior) AND (Female) AND (Female and male participants of reproductive potential must agree to use adequate contraception starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication) AND (Female participants of childbearing potential must have a negative urine or serum pregnancy test within 72 hours prior to receiving the first dose of study therapy) AND (HCC) AND (RECIST version 1.1 measurable) AND (adequate contraception) AND (chemotherapy sorafenib or oxaliplatin-based) AND (childbearing potential) AND (cytology) AND (disease) AND (disease amenable to a curative treatment approach amenable to locoregional therapy refractory to locoregional therapy) AND (histology) AND (intolerance) AND (lesion at least one) AND (life expectancy >3 months) AND (male) AND (not) AND (oxaliplatin) AND (pregnancy test urine) AND (radiographic objective progression during or after) AND (radiology) AND (reproductive potential) AND (serum pregnancy test) AND (sorafenib) AND NOT (subtype fibrolamellar) AND NOT (mixed hepatocellular/cholangiocarcinoma subtype))"}
{"candidate_id": "LLM05379", "doc_id": "NCT00718952_inc", "case_bucket": "or", "source_criterion": "Subjects aged 12-65. Confirmed idiopathic pulmonary hypertension, connective tissue disease associated pulmonary hypertension, congenital heart disease(with Eisenmenger syndrome) associated pulmonary hypertension. Baseline 6-minutes walking distance 150m-550m. WHO pulmonary hypertension function II-III with non-responder to calcium channel blockers. Documented written informed consent.", "candidate_expression": "((6-minutes walking distance Baseline 150m-550m) AND (Eisenmenger syndrome congenital heart disease) AND (WHO pulmonary hypertension function II-III) AND (aged 12-65) AND (calcium channel blockers) AND (non-responder to calcium channel blockers) AND (written informed consent) AND ((idiopathic pulmonary hypertension) OR (pulmonary hypertension) OR (pulmonary hypertension connective tissue disease associated)))"}
{"candidate_id": "LLM05380", "doc_id": "NCT03355469_inc", "case_bucket": "or", "source_criterion": "Male or female >40 and <70 years old. Has a body mass index >27 and <47 kg/m2. Not diagnosed with Type 2 diabetes. Not currently engaged in > 60 min/wk of exercise Meet at least 3 of 5 National Cholesterol Education Adult Treatment Panel III Increased waist circumference (=102 cm in men; =88 cm in women) Elevated triglycerides (=150 mg/dl), or on medication for treating the condition Reduced HDL-cholesterol (<40mg/dl in men, <50 mg/dl in women), or on medication for treating the condition High blood pressure (=130 mmHg systolic or =85mmHg diastolic), or on medication for treating the condition Elevated fasting glucose (=100 mg/dl), or on medication for treating the condition", "candidate_expression": "((Elevated fasting glucose =100 mg/dl) AND (HDL-cholesterol Reduced) AND (High blood pressure =130 mmHg systolic =85mmHg diastolic) AND (Male) AND (National Cholesterol Education Adult Treatment Panel III at least 3 of 5) AND (blood pressure) AND (body mass index >27 and <47 kg/m2) AND (fasting glucose Elevated) AND (female) AND (medication for treating) AND (medication for treating HDL-cholesterol High) AND (medication for treating triglycerides) AND (men <40mg/dl) AND (men =102 cm) AND (old >40 and <70 years) AND (triglycerides Elevated =150 mg/dl) AND (waist circumference Increased) AND (women <50 mg/dl) AND (women =88 cm) AND NOT (engaged in exercise currently > 60 min/wk) AND NOT (Type 2 diabetes))"}
{"candidate_id": "LLM05381", "doc_id": "NCT00483106_inc", "case_bucket": "other", "source_criterion": "ADHD", "candidate_expression": "(ADHD)"}
{"candidate_id": "LLM05382", "doc_id": "NCT02823808_inc", "case_bucket": "other", "source_criterion": "Type 2 Diabetes Mellitus patients Patient who had been diagnosed within the previous 12 months with HbA1c levels of 8.0-12.0%, did not have a medical history related to diabetes, and did not display proliferative retinopathy", "candidate_expression": "((HbA1c previous 12 months 8.0-12.0%) AND (Type 2 Diabetes Mellitus) AND NOT (proliferative retinopathy) AND NOT (medical history related to diabetes))"}
{"candidate_id": "LLM05383", "doc_id": "NCT02939872_inc", "case_bucket": "or", "source_criterion": "Age 19 and more On dual or triple antiplatelet therapy and between 12months and 14months from Bioresorbable Vascular Scaffold implantation No history of death, serious myocardial infarction, stroke, repeat revascularization, or major bleeding", "candidate_expression": "((Age 19 and more) AND (Bioresorbable Vascular Scaffold) AND (implantation) AND ((bleeding major) OR (death) OR (myocardial infarction serious) OR (revascularization repeat) OR (stroke)) AND ((dual antiplatelet therapy) OR (triple antiplatelet therapy)))"}
{"candidate_id": "LLM05384", "doc_id": "NCT02245256_exc", "case_bucket": "or", "source_criterion": "Pediatric patients (under 18 years) Pregnancy Patients who are unresponsive at baseline, who have neurologic deficits at baseline, or who are allergic to dexmedetomidine", "candidate_expression": "((Pediatric) AND (Pregnancy) AND (allergic) AND (dexmedetomidine) AND (neurologic deficits at baseline) AND (unresponsive at baseline) AND (years under 18 years))"}
{"candidate_id": "LLM05385", "doc_id": "NCT02650024_exc", "case_bucket": "or", "source_criterion": "Amiodarone P-glycoprotein (P-gp) inducers (e.g., rifampin, St. John's wort) Liver biopsy at any time showing mHAI stage 4 or higher fibrosis OR FibroScan within 12 months demonstrating liver stiffness of =9.5 kilo Pascal or AST to platelet ratio index (APRI) =2.0 and Fibrosis-4 (FIB-4) =3.25 NOTE: If APRI and FIB-4 are discordant one of the other forms of fibrosis staging must be used. Known allergy/sensitivity or any hypersensitivity to components of study drugs or their formulation. Hemochromatosis Alpha-1 antitrypsin deficiency Wilson's disease Autoimmune hepatitis Alcoholic liver disease Drug-related liver disease Severe NC confounding conditions (stroke, head injury, or developmental learning disability). Regular use of anti-inflammatory drugs. Current or recent treatment with pegylated interferon (PEG-IFN). Other active inflammatory process (major infection, malignancy, rheumatoid arthritis/autoimmune disorder) within the prior 28 days. Contraindications to magnetic resonance imaging (MRI). Bleeding diathesis, thrombocytopenia, or use of anticoagulants that would contraindicate lumbar puncture. Uncontrolled or active depression or other psychiatric disorder that in the opinion of the site investigator might preclude adherence to study requirements or impact NC functioning and assessments. Active drug or alcohol use or dependence that, in the opinion of the site investigator, would interfere with adherence to study requirements. Presence of active or acute AIDS-defining opportunistic infections within 12 weeks prior to study entry.", "candidate_expression": "((AIDS-defining opportunistic infections within 12 weeks prior to study entry) AND (Alcoholic liver disease) AND (Alpha-1 antitrypsin deficiency) AND (Amiodarone) AND (Autoimmune hepatitis) AND (Contraindications) AND (Drug-related liver disease) AND (FibroScan within 12 months) AND (Hemochromatosis) AND (Liver biopsy any time) AND (NC confounding conditions) AND (P-glycoprotein (P-gp) inducers) AND (PEG-IFN) AND (Wilson's disease) AND (active inflammatory process Other within the prior 28 days) AND (anti-inflammatory drugs) AND (components of study drugs) AND (contraindicate) AND (liver stiffness =9.5 kilo Pascal) AND (lumbar puncture) AND (mHAI stage 4 or higher) AND (magnetic resonance imaging (MRI)) AND (pegylated interferon) AND (treatment) AND ((AST to platelet ratio index (APRI) =2.0) OR (Fibrosis-4 (FIB-4) =3.25)) AND ((allergy) OR (hypersensitivity) OR (sensitivity)) AND ((developmental learning disability) OR (head injury) OR (stroke)) AND ((St. John's wort) OR (rifampin)) AND ((Current) OR (recent)) AND ((autoimmune disorder) OR (major infection) OR (malignancy) OR (rheumatoid arthritis)) AND ((Bleeding diathesis) OR (anticoagulants) OR (thrombocytopenia)) AND ((Uncontrolled) OR (active)) AND ((depression) OR (psychiatric disorder other)) AND ((alcohol use or dependence) OR (drug use or dependence)) AND ((active) OR (acute)))"}
{"candidate_id": "LLM05386", "doc_id": "NCT02944604_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05387", "doc_id": "NCT00625742_exc", "case_bucket": "or", "source_criterion": "1. Have dementia or delirium (as determined by the palliative care specialist) at study entry. 2. Are pregnant 3. Have been taking corticosteroids for longer than 48 hours. 4. Have pulmonary edema, ascites or pitting edema on clinical examination. 5. Are unable to walk. 6. Have a history of serious adverse gastrointestinal events (i.e., bleeding or perforation),history of a coagulopathy or current anti-coagulant use. 7. Have an ALT/AST>3x upper limit of normal. 8. Patients on methotrexate. 9. Patients taking melatonin receptor agonists (such as Rozerem® [ramelteon]).", "candidate_expression": "((ALT/AST >3x upper limit of normal) AND (Rozerem) AND (corticosteroids longer than 48 hours) AND (melatonin receptor agonists) AND (methotrexate) AND (pregnant) AND (ramelteon) AND (unable to walk) AND ((adverse gastrointestinal events history serious) OR (anti-coagulant current) OR (coagulopathy history)) AND ((bleeding) OR (perforation)) AND ((delirium) OR (dementia)) AND ((ascites) OR (pitting edema) OR (pulmonary edema)))"}
{"candidate_id": "LLM05388", "doc_id": "NCT03091881_inc", "case_bucket": "other", "source_criterion": "Type I diabetic patients Parturients presented for Cesarean section", "candidate_expression": "((Cesarean section) AND (Parturients) AND (Type I diabetic))"}
{"candidate_id": "LLM05389", "doc_id": "NCT02203019_inc", "case_bucket": "or", "source_criterion": "Men and women 18-89 years old with the diagnosis of sepsis (as specified below) within the previous 24 hours who require mechanical ventilation, and provide informed consent either personally or by an authorized representative.", "candidate_expression": "((18-89 years) AND (Men) AND (mechanical ventilation) AND (old) AND (provide informed consent either personally or by an authorized representative) AND (sepsis) AND (within the previous 24 hours) AND (women))"}
{"candidate_id": "LLM05390", "doc_id": "NCT02593409_exc", "case_bucket": "or", "source_criterion": "HIV infection at screening participation in previous or concurrent HIV vaccine trials lactating, pregnant or planning pregnancy renal function impairment (serum creatinine >1.5 mg/dl), Fanconi syndrome abnormal liver function tests (AST/ALT > 43 U/L), liver disease, viral hepatitis, hepatitis B virus (HBV) infection serum phosphorus <2.2mg/dl, osteoporosis known sensitivity to components of the Truvada® formulation any immunosuppressive treatment, such as systemic corticosteroids assumption of medication that interacts with Truvada® high likelihood of poor adherence to PREP and clinic attendance any condition that in the opinion of the attending physician could endanger the health of the participant or render her unsuitable to participate in the trial", "candidate_expression": "((ALT) AND (AST) AND (Fanconi syndrome) AND (HIV infection) AND (Truvada) AND (actating, pregnant or planning pregnancy) AND (hepatitis B virus (HBV) infection) AND (high likelihood of poor adherence to PREP and clinic attendanc) AND (immunosuppressive treatment) AND (liver disease) AND (liver function tests abnormal) AND (osteoporosis) AND (participation in previous or concurrent HIV vaccine trials) AND (renal function impairment) AND (sensitivity) AND (serum creatinine >1.5 mg/dl) AND (serum phosphorus <2.2mg/dl) AND (systemic corticosteroids) AND (viral hepatitis))"}
{"candidate_id": "LLM05391", "doc_id": "NCT00728156_exc", "case_bucket": "or", "source_criterion": "Contraindication to Clopidogrel Smoking (current smokers and patients who quit smoking less than six months) Malignancy(diagnosed or under investigation) Haematological disorders (Anaemia, malignancy, bleeding disorders) Women of child-bearing potential Use of corticosteroids/other antithrombotic agents(warfarin) Chronic liver disease (Cirrhosis, malignancy and patients with more than twice the upper limit of liver function tests) Unable to consent. Use of other investigational study drugs within 1 year prior to study entry Previous participation in this study", "candidate_expression": "((Chronic liver disease) AND (Clopidogrel) AND (Contraindication) AND (Haematological disorders) AND (Malignancy) AND (Smoking) AND (Unable to consent.) AND (Women) AND (child-bearing potential) AND (investigational study drugs within 1 year prior to study entry) AND (participation in this study Previous) AND (quit smoking less than six months) AND (smokers current) AND (warfarin) AND ((Anaemia) OR (bleeding disorders) OR (malignancy)) AND ((antithrombotic agents) OR (corticosteroids)) AND ((Cirrhosis) OR (liver function tests more than twice the upper limit) OR (malignancy)) AND ((diagnosed) OR (under investigation)))"}
{"candidate_id": "LLM05392", "doc_id": "NCT03154931_exc", "case_bucket": "or", "source_criterion": "Suicidal patients and/or severe automutilation behavior and/or psychotic symptoms and/or lack of event memory.", "candidate_expression": "((Suicidal) OR (automutilation behavior severe) OR (lack of event memory) OR (psychotic symptoms))"}
{"candidate_id": "LLM05393", "doc_id": "NCT02429765_exc", "case_bucket": "other", "source_criterion": "A diagnosis of sleep disordered breathing; Nocturnal oxygen therapy.", "candidate_expression": "((Nocturnal oxygen therapy) AND (sleep disordered breathing))"}
{"candidate_id": "LLM05394", "doc_id": "NCT03335436_exc", "case_bucket": "or", "source_criterion": "use illicit drugs or relapse during the last trimester of pregnancy positive drug screen at the time of delivery allergies to any medications used in the study taking prescribed gabapentin at the time of admission for CD contraindications to neuraxial anesthesia or require general anesthesia for CD designated ASA physical status 4 or above", "candidate_expression": "((4 or above) AND (ASA physical status) AND (CD) AND (admission) AND (admission for CD) AND (allergies) AND (at the time of admission for CD) AND (at the time of delivery) AND (delivery) AND (drug screen) AND (during the last trimester of pregnancy) AND (gabapentin) AND (last trimester) AND (medications used in the study) AND (neuraxial anesthesia) AND (positive) AND (pregnancy) AND (prescribed) AND (require) AND (the last trimester of pregnancy) AND (the time of delivery) AND ((illicit drugs) OR (relapse)) AND ((contraindications) OR (general anesthesia)))"}
{"candidate_id": "LLM05395", "doc_id": "NCT02944929_exc", "case_bucket": "other", "source_criterion": "Patients who are unwilling to participate in the study. For the one under guardianship, the refusal of the patient will be the final decision even if the guardian is willing to participate. Subjects who are unlikely to adhere to the study an/or poor adherence anticipated by the investigator. Un-controlled progressive pathology. Osteoarticular lesion which contraindicates part of the rehabilitation involved in the study. Patients with other interventions planned prior to the end of the study period (orthosis, surgery etc.). Surgery to the treated limb less than 6 months previously. Pregnant woman.", "candidate_expression": "((Osteoarticular lesion) AND (Patients who are unwilling to participate in the study. For the one under guardianship, the refusal of the patient will be the final decision even if the guardian is willing to participate) AND (Pregnant woman) AND (Subjects who are unlikely to adhere to the study an/or poor adherence anticipated by the investigator) AND (Surgery treated limb less than 6 months))"}
{"candidate_id": "LLM05396", "doc_id": "NCT02499185_inc", "case_bucket": "other", "source_criterion": "= 18 years High risk patients: General Surgery AKI Risk Index Class III, IV or V Major abdominal surgery", "candidate_expression": "((= 18 years = 18 years) AND (General Surgery AKI Risk Index Class III, IV or V) AND (High risk) AND (Major abdominal surgery))"}
{"candidate_id": "LLM05397", "doc_id": "NCT01908465_inc", "case_bucket": "or", "source_criterion": "Irritable Bowel Syndrome (IBS) (ROME III criteria): subtype with diarrhea or mixed form age 18-65 years", "candidate_expression": "((18-65 years) AND (Irritable Bowel Syndrome (IBS)) AND (ROME III criteria) AND (age) AND (diarrhea) AND (mixed form))"}
{"candidate_id": "LLM05398", "doc_id": "NCT00319748_inc", "case_bucket": "or", "source_criterion": "Adequate performance status: Breast - Karnofsky score > 50; Ovarian, endometrial or cervical - Gynecologic Oncology Group (GOG) performance score ≤2 If female and of childbearing potential, are willing to use adequate contraception (hormonal, barrier method, abstinence) prior to study entry and for the duration of study participation. Normal organ function within 14 days of study entry Diagnosis of one of the following malignancies: Metastatic breast cancer (BR) Metastatic ovarian cancer (OV) Metastatic endometrial cancer (EM) Metastatic cervical cancer (CX) Measurable metastatic disease (>1cm) in at least one site other than bone-only Progression on or failure to respond to at least one previous chemotherapy regimen for metastatic disease Progression on prior therapy with a hormonal agent if estrogen receptor or progesterone receptor positive, and/or with trastuzumab if HER2-neu positive. If patient has progressed through hormone or trastuzumab therapy only, must have received one chemotherapy regimen. Measurable metastatic disease as defined by Response Evaluation Criteria in Solid Tumors (RECIST) Primary tumor must have been diagnosed histologically as either epithelial ovarian cancer, fallopian tube cancer, or primary peritoneal cancer (not borderline or low malignant potential epithelial carcinoma). Subjects must have failed at least two previous chemotherapy regimens. Paclitaxel must have been a component of one or both regimens and cisplatin or carboplatin must have been a component of one or both regimens. Measurable metastatic disease Histologically proven recurrent or persistent endometrial cancer that is not amenable to curative treatment with surgery and/or radiation therapy AND has failed 2 previous treatment regimens Measurable metastatic disease Histologically proven recurrent or persistent squamous cell carcinoma, adenosquamous carcinoma, or adenocarcinoma of the cervix that is not amenable to curative treatment with surgery and/or radiation therapy AND has failed 2 previous treatment regimens.", "candidate_expression": "((Breast - Karnofsky score > 50) AND (Gynecologic Oncology Group (GOG) performance score ≤2) AND (HER2-neu positive) AND (Histologically proven) AND (Metastatic breast cancer) AND (Metastatic cervical cancer) AND (Metastatic endometrial cancer) AND (Metastatic ovarian cancer) AND (Normal organ function within 14 days of study entry) AND (Paclitaxel) AND (Response Evaluation Criteria in Solid Tumors (RECIST)) AND (adenocarcinoma of the cervix) AND (adenosquamous carcinoma) AND (chemotherapy regimen) AND (chemotherapy regimen previous) AND (chemotherapy regimens failed previous) AND (childbearing potential) AND (contraception prior to study entry for the duration of study participation) AND (endometrial cancer) AND (female) AND (histologically Primary tumor) AND (metastatic disease) AND (metastatic disease Measurable) AND (metastatic disease Measurable >1cm at least one) AND (performance status Adequate) AND (squamous cell carcinoma) AND (therapy with a hormonal agent prior) AND (therapy with trastuzumab prior) AND (treatment regimens failed previous 2) AND (treatment regimens previous 2) AND NOT (epithelial carcinoma at least two) AND ((Ovarian) OR (cervical) OR (endometrial)) AND ((abstinence) OR (barrier method) OR (hormonal)) AND ((Progression on) OR (failure to respond)) AND ((estrogen receptor positive) OR (progesterone receptor positive)) AND ((hormone therapy progressed through) OR (trastuzumab therapy progressed through)) AND ((epithelial ovarian cancer) OR (fallopian tube cancer) OR (primary peritoneal cancer)) AND ((borderline) OR (low malignant potential)) AND ((carboplatin) OR (cisplatin)) AND ((radiation therapy) OR (surgery)) AND ((persistent) OR (recurrent)))"}
{"candidate_id": "LLM05399", "doc_id": "NCT02916342_exc", "case_bucket": "or", "source_criterion": "indication for catheter insertion; contraindications to brachial plexus block (e.g., allergy to local anaesthetics, malignancy or infection in the area); existing neurological deficit in the area to be blocked; pregnancy; history of neck surgery or radiotherapy; severe respiratory disease; chest deformity; inability to understand the informed consent and demands of the study; patient refusal.", "candidate_expression": "((area to be blocked) AND (brachial plexus block) AND (catheter insertion) AND (chest deformity) AND (contraindications) AND (existing) AND (history) AND (in the area) AND (inability to understand the informed consent and demands of the study;) AND (indication) AND (local anaesthetics) AND (neurological deficit) AND (patient refusal) AND (pregnancy) AND (respiratory disease) AND (severe) AND ((neck surgery) OR (radiotherapy)) AND ((allergy) OR (infection) OR (malignancy)))"}
{"candidate_id": "LLM05400", "doc_id": "NCT03228498_inc", "case_bucket": "or", "source_criterion": "1. Cognitive impairment from mild to moderate degree defined by a Clinical Deterioration Rating (CDR) score range between 0.5 and 2.0. 2. Evidence on brain MRI of white matter hyperintensities (leukoaraiosis of moderate or severe degree according to the modified Fazekas visual scale and/or presence of lacunar infarcts). 3. Consent to participation in the study.", "candidate_expression": "((Clinical Deterioration Rating (CDR) score range between 0.5 and 2.0) AND (Cognitive impairment mild to moderate) AND (brain MRI white matter hyperintensities) AND (leukoaraiosis) AND ((lacunar infarcts) OR (modified Fazekas visual scale moderate or severe degree)))"}
```
