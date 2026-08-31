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
{"candidate_id": "LLM00326", "doc_id": "NCT00480129_inc", "case_bucket": "or", "source_criterion": "Clinical diagnosis of allergic rhinitis based on sneeze attacks, runny/blocked/itchy nose in the absence of a common cold during the previous 12 months. History of positive skin prick test or blood radio-allergosorbent test (RAST) to grass and/or ragweed pollen", "candidate_expression": "((absence) AND (allergic rhinitis) AND (blood radio-allergosorbent test (RAST)) AND (during the previous 12 months) AND (itchy nose) AND (positive) AND (runny nose) AND (skin prick test) AND (sneeze attacks) AND ((grass) OR (ragweed pollen)) AND ((blocked nose) OR (common cold)))"}
{"candidate_id": "LLM00327", "doc_id": "NCT01684501_exc", "case_bucket": "or", "source_criterion": "score level D on the SIGAM mobility grade have experienced 1 or more falls in the last month before the study have a residual limb length which does not allow for seven inches clearance of bracket attachment for the PowerFoot the residual limb must be stable in volume (no change in socket or socket padding in last 6 months) and without pain that limits function the sound-side (contralateral) lower extremity must be free of impediments that affect gait, range of motion, or limb muscle activity Any diagnosed cardiovascular, pulmonary, neurological, and/ or orthopedic conditions that would interfere with subject participation", "candidate_expression": "((SIGAM mobility grade level D) AND (does not) AND (falls 1 or more in the last month before the study) AND (interfere with subject participation) AND (residual limb length does not allow for seven inches clearance of bracket attachment) AND ((impediments that affect gait) OR (impediments that affect limb muscle activity) OR (impediments that affect range of motion)) AND ((cardiovascular conditions) OR (neurological conditions) OR (orthopedic conditions) OR (pulmonary conditions)))"}
{"candidate_id": "LLM00328", "doc_id": "NCT01993836_exc", "case_bucket": "or", "source_criterion": "Inmate of a correctional facility (i.e. prisoners). Pregnancy Documented or suspected family or personal history of malignant hyperthermia. Patient unable to receive either propofol or isoflurane due to allergy or other specific contraindication.", "candidate_expression": "((Inmate of a correctional facility) AND (Pregnancy) AND (allergy) AND (history family) AND (isoflurane) AND (malignant hyperthermia) AND (personal history) AND (prisoners) AND (propofol) AND (unable to receive))"}
{"candidate_id": "LLM00329", "doc_id": "NCT02964715_exc", "case_bucket": "or", "source_criterion": "eGFR <45 ml/min structural and functional urogenital abnormalities, that predispose for urogenital infections Investigational product use in the last 6 months SGLT2 inhibitor, TZD, DPP4 inhibitor and GLP1 RA use within the past 6 months DKA(Diabetic Ketoacidosis) or HHS(Hyperosmoloar Hyperglycaemic Syndrome) within the last 6 months Pregnancy Presence of major contraindications to magnetic resonance imaging (cardiac pacemakers, claustrophobia, foreign bodies and implanted medical devices with ferromagnetic properties). Liver cirrhosis Type 1 diabetes Severe uncorrected insulin insufficiency Significant alcohol intake HIV infection Use of Traditional Chinese Medication or alternative therapies Coexisting causes of chronic liver disease - chronic viral hepatitis(B & C), autoimmune liver disease, hemochromatosis, Wilson's etc. Use of medications associated with steatosis eg. Methotrexate, anticonvulsants, antiretroviral therapy etc. h/o stroke Steroid therapy Endogenous Cushing's Familial hypertriglyceridemia", "candidate_expression": "((<45 ml/min) AND (Cushing's) AND (Diabetic Ketoacidosis) AND (Endogenous) AND (Familial hypertriglyceridemi) AND (HIV infection) AND (Hyperosmoloar Hyperglycaemic Syndrome) AND (Investigational product use) AND (Liver cirrhosis) AND (Pregnancy) AND (Severe) AND (Significant) AND (Steroid therapy) AND (Type 1 diabetes) AND (alcohol intake) AND (cardiac pacemakers) AND (chronic liver disease) AND (claustrophobia) AND (eGFR) AND (ferromagnetic properties) AND (foreign bodies) AND (implanted medical devices) AND (in the last 6 months) AND (insulin insufficiency) AND (magnetic resonance imaging) AND (major contraindications) AND (medications) AND (predispose for urogenital infections) AND (steatosis) AND (stroke) AND (uncorrected) AND (urogenital abnormalities) AND (urogenital infections) AND (within the last 6 months) AND (within the past 6 months) AND ((DPP4 inhibitor) OR (GLP1 RA) OR (SGLT2 inhibitor) OR (TZD)) AND ((DKA) OR (HHS)) AND ((Traditional Chinese Medication) OR (alternative therapies)) AND ((Wilson's) OR (autoimmune liver disease) OR (chronic viral hepatitis B) OR (chronic viral hepatitis C) OR (hemochromatosis)) AND ((functional) OR (structural)) AND ((Methotrexate) OR (anticonvulsants) OR (antiretroviral therapy)))"}
{"candidate_id": "LLM00330", "doc_id": "NCT03388840_inc", "case_bucket": "other", "source_criterion": "male patients with androgenetic alopecia between 18 years and 60 years", "candidate_expression": "((androgenetic alopecia) AND (male) AND (years between 18 years and 60 years))"}
{"candidate_id": "LLM00331", "doc_id": "NCT02973035_inc", "case_bucket": "or", "source_criterion": "Controlled hypertension: systolic BP < 150 and diastolic BP < 90 mmHg in persons aged 60 years or older, systolic BP < 140 and diastolic BP < 90 mmHg in persons 40 through 59 years according to the JNC 8th guideline Evidence of diastolic dysfunction showing E/E' > 10 The patient agrees to the study protocol and the schedule of clinical and echocardiographic follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site", "candidate_expression": "((40 through 59) AND (60 years or older) AND (< 140) AND (< 150) AND (< 90 mmHg) AND (> 10) AND (Controlled) AND (E/E') AND (JNC 8th guideline) AND (The patient agrees to the study protocol and the schedule of clinical and echocardiographic follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site) AND (aged) AND (diastolic BP) AND (diastolic dysfunction) AND (hypertension) AND (systolic BP) AND (years))"}
{"candidate_id": "LLM00332", "doc_id": "NCT02701777_inc", "case_bucket": "or", "source_criterion": "Male and females between ages 18-85 years Right handed Able to complete precision grips with both hands Able to complete full wrist flexion-extension bilaterally Able to walk unassisted Able to complete full ankle flexion-extension bilaterally Male and females between ages 18-85 years SCI ( 2 months of injury) Spinal Cord injury at or above L5 The ability to produce a visible precision grip force with one hand Able to perform some small wrist flexion and extension The ability to perform a small visible contraction with dorsiflexion and hip flexor muscles No subjects will be excluded based on their race, religion, ethnicity, gender or HIV status. ASIA A,B,C, or D", "candidate_expression": "((2 months of injury) AND (A,B,C, or D) AND (ASIA) AND (Able to) AND (Male) AND (Right handed) AND (SCI) AND (Spinal Cord injury) AND (The ability to) AND (ages) AND (at or above L5) AND (between 18-85 years) AND (complete full ankle flexion-extension bilaterally) AND (complete full wrist flexion-extension bilaterally) AND (complete precision grips with both hands) AND (females) AND (produce a visible precision grip force with one hand) AND (small visible contraction with dorsiflexion and hip flexor muscles) AND (small wrist flexion and extension) AND (walk unassisted))"}
{"candidate_id": "LLM00333", "doc_id": "NCT02339844_exc", "case_bucket": "or", "source_criterion": "Exclusion Criteria patients: Substance abuse on a daily basis during the last 3 month or patients fulfilling the criteria of ongoing substance abuse due to ICD-10/DSM-IV/V, Treatment with antidepressant during the last 30 days, Head injury with more than 5 minutes of unconsciousness, Patients involuntarily admitted or treated, Components of metal implanted by operation, Pacemaker, Pregnancy, Severe physical illness Exclusion criteria controls: First degree relatives with psychiatric disease, Substance abuse during the last 3 month or positive screening of drugs in urine-sample, Head injury with more than 5 minutes of unconsciousness, Components of metal implanted by operation, Pacemaker, Pregnancy, Severe physical illness", "candidate_expression": "((Components of metal) AND (Head injury) AND (Pacemaker) AND (Pregnancy) AND (Severe physical illness) AND (Substance abuse daily basis during the last 3 month) AND (Substance abuse during the last 3 month) AND (antidepressant during the last 30 days) AND (controls) AND (involuntarily admitted) AND (involuntarily treated) AND (patients) AND (psychiatric disease First degree relatives) AND (screening of drugs positive urine-sample) AND (substance abuse ongoing ICD-10/DSM-IV/V) AND (unconsciousness more than 5 minutes))"}
{"candidate_id": "LLM00334", "doc_id": "NCT01680081_inc", "case_bucket": "or", "source_criterion": "Men and women patients, with age ranging 40-80. Suspected coronary artery disease who are supposed to undergo invasive coronary angiography with appropriate clinical indications Patients who are willing to sign the informed consent form", "candidate_expression": "((Men) AND (Patients who are willing to sign the informed consent form) AND (Suspected) AND (age) AND (coronary artery disease) AND (invasive coronary angiography) AND (ranging 40-80) AND (supposed to undergo) AND (women))"}
{"candidate_id": "LLM00335", "doc_id": "NCT01991743_exc", "case_bucket": "or", "source_criterion": "Refusal Contraindication to neuraxial (coagulopathy, anticoagulant use, local infection, sepsis etc) .Rupture of membranes. Drop-out: Patients may choose to drop-out of the study at any time. The physicians involved in this study may choose to end a patient's involvement in the study at their discretion.", "candidate_expression": "((Contraindication) AND (Rupture of membranes) AND (neuraxial) AND ((anticoagulant) OR (coagulopathy) OR (local infection) OR (sepsis)))"}
{"candidate_id": "LLM00336", "doc_id": "NCT02334722_exc", "case_bucket": "or", "source_criterion": "No known history of seizure activity. Pregnant or breastfeeding. Renal dysfunction (CrCl < 30ml/min). Beck's Depression Inventory (BDI) =14 Allergy to levetiracetam.", "candidate_expression": "((Allergy) AND (Beck's Depression Inventory (BDI) =14) AND (CrCl < 30ml/min) AND (Renal dysfunction) AND (levetiracetam) AND (seizure activity history) AND ((Pregnant) OR (breastfeeding)))"}
{"candidate_id": "LLM00337", "doc_id": "NCT02596555_inc", "case_bucket": "or", "source_criterion": "Age =18 years Objectively confirmed diagnosis of acute PE by multidetector CT angiography, ventilation/perfusion lung scan, or selective invasive pulmonary angiography, according to established diagnostic criteria, with or without symptomatic deep vein thrombosis Absence of hemodynamic collapse, or decompensation, at presentation; Hemodynamic collapse or decompensation At least one sign of RV pressure overload/dysfunction on CT angiography or echocardiography Signs of myocardial injury as indicated by elevated troponin levels Signs of (RV) failure as indicated by NT-proBNP levels >600 pg/ml at baseline. Ability of the subject to understand the character and individual consequences of the clinical trial; signed and dated informed consent of the subject available before the start of any specific trial procedures", "candidate_expression": "((=18 years) AND (>600 pg/ml) AND (Ability of the subject to understand the character and individual consequences of the clinical trial; signed and dated informed consent of the subject available before the start of any specific trial procedures) AND (Absence) AND (Age) AND (At least one) AND (CT angiography) AND (NT-proBNP levels) AND (PE) AND (RV) failure) AND (acute) AND (deep vein thrombosis) AND (echocardiography) AND (elevated) AND (hemodynamic collapse) AND (hemodynamic decompensation) AND (invasive pulmonary angiography,) AND (myocardial injury) AND (sign of RV pressure dysfunction) AND (sign of RV pressure overload) AND (troponin levels) AND (ventilation/perfusion lung scan))"}
{"candidate_id": "LLM00338", "doc_id": "NCT01116882_exc", "case_bucket": "or", "source_criterion": "1. The patient is pregnant or breastfeeding. 2. Evidence of STEMI within 72 hours of the intended treatment on infarct related or non-infarct related artery. 3. Cardiogenic shock on presentation or during current hospitalization. 4. Left ventricular ejection fraction less than 20%. 5. Known allergies to: aspirin, clopidogrel (Plavix) and ticlopidine (Ticlid), heparin, bivalirudin, stainless steel, or contrast agent (which cannot be adequately premedicated). 6. A platelet count less than 75,000 cells/mm3 or greater than 700,000 cells/mm3 or a WBC less than 3,000 cells/mm3. 7. Acute or chronic renal dysfunction (creatinine greater than 2.5 mg/dl or less than 150µmol/L). 8. Subject is currently participating in an investigational drug or device study that has not completed the primary endpoint or that clinically interferes with the current study endpoints. (Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials). 9. Prior participation in this study. 10. Within 30 days prior to the index study procedure, the subject has undergone a previous coronary interventional procedure of any kind. Note: This exclusion criterion does not apply to post-STEMI patients. 11. Stroke or transient ischemic attack within the prior 3 months. 12. Active peptic ulcer or upper gastrointestinal bleeding within the prior 3 months. 13. Subject has active sepsis. 14. Unprotected left main coronary artery disease (stenosis greater than 50%). 15. In the investigator's opinion, subject has a co-morbid condition(s) that could limit the life expectancy to less than one year, or limit the subject's ability to participate in the study or comply with follow-up requirements or impact the scientific integrity of the study. 16. Subject has normal or insignificant coronaries (i.e. coronary lesion(s) less than 50% stenosis). 17. Any target vessel has evidence of: excessive thrombus (e.g. requires target vessel thrombectomy) tortuousity (greater than 60 degree angle) that makes it unsuitable for proper stent delivery and deployment, heavy calcification. 18. Any target lesion requires treatment with a device other than percutaneous transluminal coronary angioplasty (PTCA) prior to stent placement (e.g. but not limited to, directional coronary atherectomy, excimer laser, rotational atherectomy, etc.). 19. Any lesion that is located in a saphenous vein graft, however, lesions located within the native vessel but accessed through the graft are eligible. 20. The target vessel is in a \"last remaining\" epicardial vessel (e.g. greater than 2 non-target epicardial vessels and the bypass grafts to these territories [if present] are totally occluded).", "candidate_expression": "((Acute renal dysfunction) AND (Cardiogenic shock) AND (In the investigator's opinion) AND (In the investigator's opinion, subject has a co-morbid condition(s) that could limit the life expectancy to less than one year, or limit the subject's ability to participate in the study or comply with follow-up requirements or impact the scientific integrity of the study.) AND (Left ventricular ejection fraction less than 20%) AND (Plavix) AND (STEMI within 72 hours) AND (Stroke) AND (Subject is currently participating in an investigational drug or device study that has not completed the primary endpoint or that clinically interferes with the current study endpoints. (Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials).) AND (Ticlid) AND (WBC less than 3,000 cells/mm3) AND (allergies) AND (angle greater than 60 degree) AND (aspirin) AND (bivalirudin) AND (breastfeeding) AND (calcification heavy) AND (chronic renal dysfunction) AND (clopidogrel) AND (contrast agent) AND (coronary interventional procedure Within 30 days prior to the index study procedure previous) AND (coronary lesion) AND (coronary lesion less than 50% stenosis) AND (creatinine greater than 2.5 mg/dl less than 150µmol/L) AND (device other than percutaneous transluminal coronary angioplasty (PTCA) stent placement) AND (directional coronary atherectomy) AND (excimer laser) AND (heparin) AND (hospitalization current) AND (left main coronary artery disease Unprotected) AND (lesion located in a saphenous vein graft) AND (life expectancy) AND (life expectancy less than one year) AND (peptic ulcer) AND (platelet count less than 75,000 cells/mm3 greater than 700,000 cells/mm3) AND (pregnant) AND (rotational atherectomy) AND (saphenous vein graft within the native vessel accessed through the graft) AND (sepsis active) AND (stainless steel) AND (stenosis) AND (stenosis greater than 50%) AND (stent delivery and deployment unsuitable for proper) AND (stent placement) AND (target lesion) AND (target vessel thrombectomy) AND (the index study procedure) AND (thrombus) AND (ticlopidine) AND (tortuousity) AND (transient ischemic attack) AND (treatment infarct related artery non-infarct related artery) AND (treatment requires prior to stent placement) AND (unsuitable for proper) AND (upper gastrointestinal bleeding) AND NOT (STEMI) AND NOT (percutaneous transluminal coronary angioplasty (PTCA)))"}
{"candidate_id": "LLM00339", "doc_id": "NCT02912182_exc", "case_bucket": "or", "source_criterion": "tinnitus or hearing loss with same debut as vertigo history of bleeding peptic ulcer glaucoma pregnancy or non-acceptance to use anticonception measures during 13 days after debut high blood pressure >180 systolic, 105, diastolic ketoacidosis with a Base Excess >=2 psychic disorder (not including mild depression) serious infection (neutropenia, tuberculosis) chronic otitis history of vertiginous disease; Ménière, Vertiginous migraine, atypical BPPV", "candidate_expression": "((105) AND (>180) AND (>=2) AND (Base Excess) AND (bleeding) AND (blood pressure diastolic) AND (blood pressure systolic) AND (chronic otitis) AND (glaucoma) AND (infection) AND (ketoacidosis) AND (mild depression) AND (not) AND (peptic ulcer) AND (pregnancy or non-acceptance to use anticonception measures during 13 days after debut) AND (psychic disorder) AND (serious) AND (vertigo) AND ((hearing loss) OR (tinnitus)) AND ((neutropenia) OR (tuberculosis)) AND ((Ménière) OR (Vertiginous migraine) OR (atypical BPPV) OR (vertiginous disease)))"}
{"candidate_id": "LLM00340", "doc_id": "NCT00806936_inc", "case_bucket": "other", "source_criterion": "After the investigator has taken the decision to use human insulin or insulin analogues to treat the subject, any type 2 diabetic previously inadequately controlled with two or more OADs is eligible for the study The selection of the subjects will be at the discretion of the individual investigator", "candidate_expression": "((OADs) AND (inadequately controlled) AND (previously) AND (two or more) AND (type 2 diabetic))"}
{"candidate_id": "LLM00341", "doc_id": "NCT02885909_inc", "case_bucket": "or", "source_criterion": "Type 2 diabetic inpatient Fasting glucose >140 mg/dl or random glucose >180 mg/dl", "candidate_expression": "((Fasting glucose >140 mg/dl) AND (Type 2 diabetic) AND (inpatient) AND (random glucose >180 mg/dl))"}
{"candidate_id": "LLM00342", "doc_id": "NCT02797548_exc", "case_bucket": "or", "source_criterion": "Acute coronary syndrome within 1 month Heart failure NYHA III to IV Contraindication to Aspirin On anticoagulant therapy Emergent surgery Cardiac surgery High bleeding risk surgeries, e.g., Intra-cranial surgery, Intra-spinal surgery, Retinal surgery Pregnancy or breast-feeding Life expectancy less than 1year", "candidate_expression": "((Acute coronary syndrome within 1 month) AND (Aspirin) AND (Cardiac surgery) AND (Contraindication) AND (Emergent surgery) AND (Heart failure) AND (High bleeding risk surgeries) AND (Intra-cranial surgery) AND (Intra-spinal surgery) AND (Life expectancy less than 1year) AND (NYHA III to IV) AND (Pregnancy) AND (Retinal surgery) AND (anticoagulant therapy) AND (breast-feeding))"}
{"candidate_id": "LLM00343", "doc_id": "NCT03561753_exc", "case_bucket": "or", "source_criterion": "Tuberculosis resistant to any of the study drugs (isoniazid, rifampin, EMB, PZA, CFZ, Pto) Unable to take oral medications. History of allergy or intolerance to any of the study drugs Serum aminotransferase (AST or ALT) 3x upper limit of normal or higher Pregnant or nursing females, or plan to become pregnant or nurse during the study period Males planning to conceive a child during the study or within 6 months of cessation of treatment. Any treatment directed against active tuberculosis within 6 months preceding initiation of study drugs. Suspected or documented tuberculosis involving the central nervous system and/or bones and/or joints, and/or miliary tuberculosis and/or pericardial tuberculosis. HIV infected HBV infected or HCV infected (these increase the risk of TB-drug induced hepatotoxicity) Weight less than 40.0 kg. Known allergy or intolerance to any of the study medications. Individuals will be excluded from enrollment if, at the time of enrollment, their M. tuberculosis isolate is already known to be resistant to any of the study drugs. QTcF > 500 msec Other medical conditions, that, in the investigator's judgment, make study participation not in the individual's best interest. Current or planned incarceration or other involuntary detention Having participated in other clinical studies with dosing of investigational agents within 8 weeks prior to trial start or currently enrolled in an investigational study that includes treatment with medicinal agents. Subjects who are participating in observational studies or who are in a follow up period of a trial that included drug therapy may be considered for inclusion.", "candidate_expression": "((HIV infected) AND (M. tuberculosis isolate resistant to any of the study drugs) AND (Males) AND (QTcF > 500 msec) AND (Serum aminotransferase) AND (Tuberculosis resistant to) AND (Unable to take oral medications) AND (Weight less than 40.0 kg) AND (conceive a child planning to) AND (enrolled in an investigational study currently) AND (females) AND (investigational agents) AND (medicinal agents) AND (participated in other clinical studies within 8 weeks prior to trial start) AND (study drugs) AND (study medications) AND (treatment) AND (tuberculosis) AND (tuberculosis active within 6 months preceding initiation of study drugs) AND ((allergy) OR (intolerance)) AND ((ALT) OR (AST)) AND ((Pregnant) OR (nursing)) AND ((become pregnant) OR (nurse)) AND ((during the study the study) OR (within 6 months of cessation of treatment cessation of treatment)) AND ((bones) OR (central nervous system) OR (joints) OR (miliary tuberculosis) OR (pericardial tuberculosis)) AND ((Suspected) OR (documented)) AND ((HBV infected) OR (HCV infected)) AND ((Current) OR (planned)) AND ((incarceration) OR (involuntary detention)) AND ((CFZ) OR (EMB) OR (PZA) OR (Pto) OR (isoniazid) OR (rifampin)))"}
{"candidate_id": "LLM00344", "doc_id": "NCT01116882_exc", "case_bucket": "or", "source_criterion": "1. The patient is pregnant or breastfeeding. 2. Evidence of STEMI within 72 hours of the intended treatment on infarct related or non-infarct related artery. 3. Cardiogenic shock on presentation or during current hospitalization. 4. Left ventricular ejection fraction less than 20%. 5. Known allergies to: aspirin, clopidogrel (Plavix) and ticlopidine (Ticlid), heparin, bivalirudin, stainless steel, or contrast agent (which cannot be adequately premedicated). 6. A platelet count less than 75,000 cells/mm3 or greater than 700,000 cells/mm3 or a WBC less than 3,000 cells/mm3. 7. Acute or chronic renal dysfunction (creatinine greater than 2.5 mg/dl or less than 150µmol/L). 8. Subject is currently participating in an investigational drug or device study that has not completed the primary endpoint or that clinically interferes with the current study endpoints. (Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials). 9. Prior participation in this study. 10. Within 30 days prior to the index study procedure, the subject has undergone a previous coronary interventional procedure of any kind. Note: This exclusion criterion does not apply to post-STEMI patients. 11. Stroke or transient ischemic attack within the prior 3 months. 12. Active peptic ulcer or upper gastrointestinal bleeding within the prior 3 months. 13. Subject has active sepsis. 14. Unprotected left main coronary artery disease (stenosis greater than 50%). 15. In the investigator's opinion, subject has a co-morbid condition(s) that could limit the life expectancy to less than one year, or limit the subject's ability to participate in the study or comply with follow-up requirements or impact the scientific integrity of the study. 16. Subject has normal or insignificant coronaries (i.e. coronary lesion(s) less than 50% stenosis). 17. Any target vessel has evidence of: excessive thrombus (e.g. requires target vessel thrombectomy) tortuousity (greater than 60 degree angle) that makes it unsuitable for proper stent delivery and deployment, heavy calcification. 18. Any target lesion requires treatment with a device other than percutaneous transluminal coronary angioplasty (PTCA) prior to stent placement (e.g. but not limited to, directional coronary atherectomy, excimer laser, rotational atherectomy, etc.). 19. Any lesion that is located in a saphenous vein graft, however, lesions located within the native vessel but accessed through the graft are eligible. 20. The target vessel is in a \"last remaining\" epicardial vessel (e.g. greater than 2 non-target epicardial vessels and the bypass grafts to these territories [if present] are totally occluded).", "candidate_expression": "((Active) AND (Acute renal dysfunction) AND (Cardiogenic shock) AND (In the investigator's opinion) AND (In the investigator's opinion, subject has a co-morbid condition(s) that could limit the life expectancy to less than one year, or limit the subject's ability to participate in the study or comply with follow-up requirements or impact the scientific integrity of the study.) AND (Left ventricular ejection fraction) AND (Plavix) AND (STEMI) AND (Stroke) AND (Subject is currently participating in an investigational drug or device study that has not completed the primary endpoint or that clinically interferes with the current study endpoints. (Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials).) AND (Ticlid) AND (Unprotected) AND (WBC) AND (Within 30 days prior to the index study procedure) AND (accessed through the graft) AND (active) AND (allergies) AND (angle) AND (aspirin) AND (bivalirudin) AND (breastfeeding) AND (calcification) AND (chronic renal dysfunction) AND (clopidogrel) AND (contrast agent) AND (coronary interventional procedure) AND (coronary lesion) AND (creatinine) AND (current) AND (device other than percutaneous transluminal coronary angioplasty (PTCA)) AND (directional coronary atherectomy) AND (excimer laser) AND (greater than 2.5 mg/dl) AND (greater than 50%) AND (greater than 60 degree) AND (greater than 700,000 cells/mm3) AND (heavy) AND (heparin) AND (hospitalization) AND (infarct related artery) AND (left main coronary artery disease) AND (lesion) AND (less than 150µmol/L) AND (less than 20%) AND (less than 3,000 cells/mm3) AND (less than 50% stenosis) AND (less than 75,000 cells/mm3) AND (less than one year) AND (life expectancy) AND (located in a saphenous vein graft) AND (non-infarct related artery) AND (not) AND (other than) AND (peptic ulcer) AND (percutaneous transluminal coronary angioplasty (PTCA)) AND (platelet count) AND (pregnant) AND (previous) AND (prior to stent placement) AND (requires) AND (rotational atherectomy) AND (saphenous vein graft) AND (sepsis) AND (stainless steel) AND (stenosis) AND (stent delivery and deployment) AND (stent placement) AND (target lesion) AND (target vessel thrombectomy) AND (the index study procedure) AND (thrombus) AND (ticlopidine) AND (tortuousity) AND (transient ischemic attack) AND (treatment) AND (unsuitable for proper) AND (upper gastrointestinal bleeding) AND (within 72 hours) AND (within the native vessel) AND (within the prior 3 months))"}
{"candidate_id": "LLM00345", "doc_id": "NCT02733159_exc", "case_bucket": "or", "source_criterion": "Untreated symptomatic brain or leptomeningeal metastatic disease. Medical or psychiatric conditions comprising informed consent. Any medical condition which in the opinion of the investigator would compromise the ability of the patient to participate in the trial or which would jeopardise compliance with the protocol. Radiotherapy within 4 weeks of trial entry. Active autoimmune disease that has required systemic treatment in past 2 years Chronic usage of steroids or other immunosuppressant medication. Previous history of pneumonitis. Any evidence of clinical autoimmunity.", "candidate_expression": "((Active) AND (Any medical condition which in the opinion of the investigator would compromise the ability of the patient to participate in the trial or which would jeopardise compliance with the protocol.) AND (Chronic usage) AND (Medical or psychiatric conditions comprising informed consent) AND (Radiotherapy) AND (Untreated) AND (autoimmune disease) AND (history) AND (in past 2 years) AND (pneumonitis) AND (systemic treatment) AND (trial entry) AND (within 4 weeks of trial entry) AND ((symptomatic brain metastatic disease) OR (symptomatic leptomeningeal metastatic disease)) AND ((immunosuppressant medication) OR (steroids)) AND ((Any evidence of clinical autoimmunity) OR (autoimmunity)) AND ((Medical conditions) OR (psychiatric conditions)))"}
{"candidate_id": "LLM00346", "doc_id": "NCT02340169_exc", "case_bucket": "or", "source_criterion": "Has other dermatological conditions that may interfere with clinical assessments Allergy or sensitivity to corticosteroids or any drug hypersensitivity or intolerance that would compromise patient safety or study results History of an adverse reaction to Cortrosyn™ or similar test reagents Chronic infectious disease, system or organ disorder or other medical condition that would place patient at undue risk by study participation", "candidate_expression": "((Allergy) AND (Chronic infectious disease, system or organ disorder or other medical condition that would place patient at undue risk by study participation) AND (Cortrosyn similar test reagents) AND (Has other dermatological conditions that may interfere with clinical assessments) AND (adverse reaction Cortrosyn) AND (corticosteroids) AND (drug hypersensitivity) AND (drug intolerance) AND (hat would compromise patient safety or study results) AND (sensitivity) AND (test reagents similar))"}
{"candidate_id": "LLM00347", "doc_id": "NCT03615508_inc", "case_bucket": "or", "source_criterion": "Horner's Syndrome History of taking an alpha blocker (tamsulosin/ terazosin/doxazosin/alfuzosin/silodosin) medication", "candidate_expression": "((Horner's Syndrome) AND (alpha blocker) AND ((alfuzosin) OR (doxazosin) OR (silodosin) OR (tamsulosin) OR (terazosin)))"}
{"candidate_id": "LLM00348", "doc_id": "NCT01993836_exc", "case_bucket": "or", "source_criterion": "Inmate of a correctional facility (i.e. prisoners). Pregnancy Documented or suspected family or personal history of malignant hyperthermia. Patient unable to receive either propofol or isoflurane due to allergy or other specific contraindication.", "candidate_expression": "((Inmate of a correctional facility) AND (Pregnancy) AND (allergy) AND (malignant hyperthermia) AND (prisoners) AND (unable to receive) AND ((history family) OR (personal history)) AND ((isoflurane) OR (propofol)))"}
{"candidate_id": "LLM00349", "doc_id": "NCT02705222_inc", "case_bucket": "or", "source_criterion": "Perimenopausal women complaining of abnormal uterine bleeding (menorrhagia, metrorrhagia, polymenorrhoea or polymenorrhagia) without local gynecological cause. Failure of medical treatment for at least 3 months.", "candidate_expression": "((Failure) AND (Perimenopausal) AND (abnormal uterine bleeding) AND (for at least 3 months) AND (local gynecological cause) AND (medical treatment) AND (without) AND (women) AND ((menorrhagia) OR (metrorrhagia) OR (polymenorrhagia) OR (polymenorrhoea)))"}
{"candidate_id": "LLM00350", "doc_id": "NCT02164734_inc", "case_bucket": "other", "source_criterion": "Mild-to-moderate RDS; Postnatal age 2 to 48 hours; Gestational age 27 0/7 to 36 6/7 weeks; Treated with nasal CPAP modalities = 5 cm H2O and FiO2 between 0.30 and 0.60 for at least 2 hours to maintain SpO2 90-95%; Informed consent", "candidate_expression": "((FiO2 between 0.30 and 0.60) AND (Gestational age 27 0/7 to 36 6/7 weeks) AND (Informed consent) AND (Postnatal age 2 to 48 hours) AND (RDS Mild-to-moderate) AND (SpO2 90-95%) AND (nasal CPAP = 5 cm H2O for at least 2 hours))"}
```
