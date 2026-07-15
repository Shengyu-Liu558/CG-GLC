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
{"candidate_id": "LLM00626", "doc_id": "NCT02939209_inc", "case_bucket": "scope", "source_criterion": "Age 18-65 scheduled to receive ISB and general anesthesia as a day surgery patient for rotator cuff repair and acromioplasty, as a part of planned routine care", "candidate_expression": "((18-65) AND (Age) AND (ISB) AND (acromioplasty) AND (day surgery) AND (general anesthesia) AND (rotator cuff repair))"}
{"candidate_id": "LLM00627", "doc_id": "NCT02746900_exc", "case_bucket": "or", "source_criterion": "Multiple pregnancy Prior spontaneous preterm birth or second trimester losses between 16(0) and 36(6) weeks Cerclage in situ Painful regular uterine contraction and/or preterm labor Ruptured membranes Major fetal defects Active vaginal bleeding Placenda previa and/or accreta Cervical dilation >1.5 cm and/or visible membranes by pelvic exam Suspicion of chorioamnionitis", "candidate_expression": "((>1.5 cm) AND (Active vaginal bleeding) AND (Cerclage in situ) AND (Cervical dilation) AND (Major fetal defects) AND (Multiple pregnancy) AND (Painful regular uterine contraction) AND (Placenda previa) AND (Prior) AND (Ruptured membranes) AND (Suspicion of) AND (accreta) AND (between 16(0) and 36(6) weeks) AND (chorioamnionitis) AND (losses) AND (pelvic exam) AND (preterm labor) AND (second trimester) AND (spontaneous preterm birth) AND (visible membranes))"}
{"candidate_id": "LLM00628", "doc_id": "NCT02427295_inc", "case_bucket": "other", "source_criterion": "Age 18 or older. Patients diagnosed with acromegaly with GH-secreting pituitary adenoma on sellar MRI, meeting the biochemical criteria outlined above (refer to 1. Diagnosis of acromegaly) and with typical acromegalic features. No prior use of somatostatin analogues. Adequate hepatic and renal function Provision of a signed written informed consent", "candidate_expression": "((18 or older) AND (Adequate hepatic function) AND (Adequate renal function) AND (Age) AND (GH-secreting pituitary adenoma) AND (No) AND (Provision of a signed written informed consent) AND (acromegalic features) AND (acromegaly) AND (biochemical criteria outlined above) AND (prior) AND (sellar MRI) AND (somatostatin analogues) AND (typical))"}
{"candidate_id": "LLM00629", "doc_id": "NCT03117608_inc", "case_bucket": "or", "source_criterion": "Patients provided written informed consent; Patients aged between 18 and 75 years; Knee symptomatic OA (Kellgren-Lawrence grade 1-4) Failure of conservative treatment for at least 3 months; Patients agreed to actively participate in the rehabilitation protocol and follow-up program; Male or female patients; Women of childbearing age had to use a proven method to prevent pregnancy, before the surgical treatment.", "candidate_expression": "((Kellgren-Lawrence grade 1-4) AND (Male) AND (OA Knee symptomatic) AND (Women) AND (aged between 18 and 75 years) AND (agreed to actively participate in the follow-up program) AND (agreed to actively participate in the rehabilitation protocol) AND (childbearing age) AND (conservative treatment Failure) AND (female) AND (provided written informed consent) AND (surgical treatment))"}
{"candidate_id": "LLM00630", "doc_id": "NCT02462590_exc", "case_bucket": "or", "source_criterion": "Invasively mechanically ventilated >72 hours at the time of screening; Patients at potential increased risk of iatrogenic probiotic infection (see Section 2.6 for detailed explanation) including specific immunocompromised populations (HIV <200 CD4 cells/µL, those receiving chronic immunosuppressive medications (e.g., azathioprine, cyclosporine, cyclophosphamide, tacrolimus, methotrexate, mycofenolate, Anti-IL2), previous transplantation (including stem cell) at any time, malignancy requiring chemotherapy in the last 3 months, neutropenia [absolute neutrophil count < 500]). However, patients receiving corticosteroids previously or presently or projected to receive corticosteroids are not excluded; Patients at risk for endovascular infection (previously documented rheumatic heart disease, congenital valve disease, surgically repaired congenital heart disease, unrepaired cyanotic congenital heart disease, any intracardiac repair with prosthetic material [mechanical or bio-prosthetic cardiac valves], previous or current endocarditis, permanent endovascular devices (e.g., endovascular grafts [e.g., aortic aneurysm repair, stents involving large arteries such as aorta, femorals and carotids], inferior vena cava filters, dialysis vascular grafts), tunnelled (not short-term) hemodialysis catheters, pacemakers or defibrillators. Patients with temporary central venous catheters, central venous dialysis catheters or peripherally inserted central catheters (PICCs) are not excluded and patients with coronary artery stents, coronary artery bypass grafts (CABG) or neurovascular coils are not excluded; patients with mitral valve prolapse or bicuspid aortic valve are not excluded providing they have no other exclusion criteria; Patients with a primary diagnosis of severe acute pancreatitis, without reference to a Ranson score [Ranson 1974]). However, patients with mild or moderate pancreatitis are not excluded; Patients with percutaneous gastric or jejunal feeding tubes already in situ as per Health Canada guidance; Strict contraindication or inability to receive enteral medications; Intent to withdraw advanced life support as per the ICU physician; Previous enrolment in this or current enrolment in a potentially confounding tria", "candidate_expression": "((< 500]) AND (<200 cells/µL) AND (>72 hours) AND (Anti-IL2) AND (CD4) AND (HIV) AND (PICCs) AND (Previous enrolment in this or current enrolment in a potentially confounding tria) AND (Ranson score) AND (absolute neutrophil count) AND (acute pancreatitis) AND (aortic aneurysm repair) AND (azathioprine) AND (bicuspid aortic valve) AND (bio-prosthetic cardiac valves]) AND (central venous catheters) AND (central venous dialysis catheters) AND (chemotherapy) AND (chronic) AND (congenital heart disease) AND (congenital valve disease) AND (contraindication) AND (coronary artery bypass grafts) AND (coronary artery stents) AND (cyanotic congenital heart disease) AND (cyclophosphamide) AND (cyclosporine) AND (dialysis vascular grafts) AND (endocarditis) AND (endovascular devices) AND (endovascular grafts) AND (enteral medications) AND (gastric feeding tubes) AND (hemodialysis catheters) AND (immunocompromised) AND (immunosuppressive medications) AND (inferior vena cava filters) AND (intracardiac repair) AND (jejunal feeding tubes) AND (large arteries) AND (last 3 months) AND (mechanical cardiac valves) AND (mechanically ventilated) AND (methotrexate) AND (mild) AND (mitral valve prolapse) AND (moderate) AND (mycofenolate) AND (neurovascular coils) AND (neutropenia) AND (not) AND (pacemakers) AND (pancreatitis) AND (peripherally inserted central catheters) AND (permanent) AND (prosthetic material) AND (rheumatic heart disease) AND (risk for endovascular infection) AND (risk of iatrogenic probiotic infection) AND (severe) AND (stents) AND (surgically repaired) AND (tacrolimus) AND (transplantation) AND (unrepaired) AND (without))"}
{"candidate_id": "LLM00631", "doc_id": "NCT01993836_inc", "case_bucket": "other", "source_criterion": "Surgical patients 60 years of age or older Surgery scheduled to last at least 2 hours (including time for anesthesia induction, etc) English speaking ability. Ability to give informed consent", "candidate_expression": "((Ability to give informed consent) AND (English speaking ability) AND (Surgery scheduled to last at least 2 hours) AND (age 60 years or older))"}
{"candidate_id": "LLM00632", "doc_id": "NCT01116882_inc", "case_bucket": "or", "source_criterion": "1. Subject is at least 18 years old. 2. Subject requires single- or multi-vessel percutaneous coronary intervention (PCI) of de novo or restenotic target lesion (including in-stent restenotic lesions). 3. Subject's lesion(s) is (are) amenable to stent treatment with currently available FDA-approved bare metal or drug eluting stents. 4. Subject is an acceptable candidate for elective, urgent or emergency coronary artery bypass graft (CABG). 5. Subject has clinical evidence of ischemic heart disease in terms of a positive functional study, or documented symptoms. 6. Documented stable angina pectoris [Canadian Cardiovascular Society Classification (CCS) 1, 2, 3, or 4], unstable angina pectoris with documented ischemia (Braunwald Class IB-C, IIB-C, or IIIB-C), non-ST segment elevation myocardial infarction, or documented silent ischemia. 7. Subject is willing and able to undergo percutaneous intervention at SOS hospital, if randomized to SOS study arm. 8. Subject and the treating physician agree that the subject will comply with all follow-up evaluations. 9. Subject has been informed of the nature of the study and agrees to its provisions and has provided written informed consent as approved by the Institutional Review Board/Ethics Committee of the respective clinical site. 10. The target lesion(s) is (are) de novo or restenotic (including in-stent restenotic) native coronary artery lesion(s) with greater than 50 and less than 100% stenosis (visual estimate), or the target lesion is an acute (less than 1 month) total occlusion as evidenced by clinical symptoms. 11. Target lesions(s) is (are) located in an infarct (if not treated with primary PCI) or non-infarct-related artery with a 70% or greater stenosis (by visual estimate) more than 72 hours following the ST segment elevation myocardial infarction (STEMI). Lesions treated with PCI more than 72 hours following STEMI would be subject to the same protocol inclusion/exclusion criteria listed above and below with the exception that a target lesion of 70% or greater stenosis may be treated with or without symptoms or abnormal stress test).", "candidate_expression": "((1, 2, 3, or 4) AND (70% or greater) AND (Braunwald Class) AND (Canadian Cardiovascular Society Classification (CCS)) AND (IB-C, IIB-C, or IIIB-C) AND (SOS hospital) AND (ST segment elevation myocardial infarction (STEMI)) AND (Subject and the treating physician agree that the subject will comply with all follow-up evaluations.) AND (Subject has been informed of the nature of the study and agrees to its provisions and has provided written informed consent as approved by the Institutional Review Board/Ethics Committee of the respective clinical site.) AND (Subject is willing and able to undergo percutaneous intervention at SOS hospital, if randomized to SOS study arm.) AND (Target lesions) AND (able) AND (acute) AND (amenable to stent treatment) AND (at least 18 years) AND (clinical evidence) AND (clinical symptoms) AND (coronary artery bypass graft (CABG)) AND (coronary artery lesion) AND (documented) AND (functional study) AND (greater than 50 and less than 100%) AND (in-stent) AND (in-stent restenotic) AND (in-stent restenotic lesions) AND (infarct) AND (ischemia) AND (ischemic heart disease) AND (less than 1 month) AND (more than 72 hours following the ST segment elevation myocardial infarction (STEMI)) AND (not) AND (old) AND (percutaneous coronary intervention (PCI)) AND (percutaneous intervention) AND (positive) AND (primary PCI) AND (restenotic) AND (silent) AND (stable) AND (stenosis) AND (target lesion) AND (the ST segment elevation myocardial infarction (STEMI)) AND (total occlusion) AND (unstable) AND (willing) AND ((de novo) OR (restenotic)) AND ((bare metal stents) OR (drug eluting stents)) AND ((elective) OR (emergency) OR (urgent)) AND ((non-ST segment elevation myocardial infarction) OR (silent ischemia) OR (stable angina pectoris) OR (unstable angina pectoris)) AND ((multi-vessel) OR (single- vessel)) AND ((target lesion)) AND ((in an infarct -related artery) OR (non-infarct-related artery)))"}
{"candidate_id": "LLM00633", "doc_id": "NCT02876484_exc", "case_bucket": "or", "source_criterion": "Fasting plasma glucose > 7,0 mM, HbA1c > 48 mmol/mol 3 months after RYGB. Dysregulated thyroid diseases, use of antithyroid treatment. Late diabetic complications as retinopathy, renal insufficiency, neuropathy or previous pancreatitis. Complications to RYGB. Documented reactive hypoglycaemia, severe dumping (vomiting, diarrhea, severe abdominal pain after food intake). Cholecystectomy", "candidate_expression": "((3 months after RYGB) AND (> 48 mmol/mol) AND (> 7,0 mM) AND (Cholecystectomy) AND (Complications) AND (Dysregulated) AND (RYGB) AND (after food intake) AND (dumping) AND (food intake) AND (previous) AND (reactive hypoglycaemia) AND (severe) AND ((Fasting plasma glucose) OR (HbA1c)) AND ((antithyroid treatment) OR (thyroid diseases)) AND ((Late diabetic complications) OR (pancreatitis)) AND ((neuropathy) OR (renal insufficiency) OR (retinopathy)) AND ((abdominal pain) OR (diarrhea) OR (vomiting)))"}
{"candidate_id": "LLM00634", "doc_id": "NCT02851303_exc", "case_bucket": "other", "source_criterion": "Born prior to 34 weeks Neonatal intensive care unit admission Serious medical comorbidities Primary substance exposure in-utero was buprenorphine, or was not opioids", "candidate_expression": "((Born) AND (Neonatal intensive care unit) AND (Serious) AND (buprenorphine) AND (in-utero) AND (medical comorbidities) AND (not) AND (opioids) AND (prior to 34 weeks) AND (substance exposure))"}
{"candidate_id": "LLM00635", "doc_id": "NCT02714725_exc", "case_bucket": "or", "source_criterion": "Patient refusal. Emergency surgeries Redo surgeries Pregnancy Vasculitis Inflammation or infection at the study site History of allergic reaction to study medications", "candidate_expression": "((Emergency surgeries) AND (Inflammation) AND (Patient refusal) AND (Pregnancy) AND (Redo surgeries) AND (Vasculitis) AND (allergic) AND (infection))"}
{"candidate_id": "LLM00636", "doc_id": "NCT01664507_exc", "case_bucket": "or", "source_criterion": "underlying lung or heart disase contra indication to dexamethasone immune deficient state preterm birth previous intubation or apnea history", "candidate_expression": "((apnea) AND (contra indication) AND (dexamethasone) AND (heart disase) AND (history) AND (immune deficient state) AND (intubation) AND (lung disase) AND (preterm birth) AND (previous))"}
{"candidate_id": "LLM00637", "doc_id": "NCT03004209_inc", "case_bucket": "or", "source_criterion": "Clinically diagnosed autoimmune encephalitis Ineffective 1st line treatment (e.g. steroid IV, IVIg) and 2nd line treatment (e.g. Rituximab or cyclophosphamide)", "candidate_expression": "((1st line treatment) AND (2nd line treatment) AND (Clinically diagnosed) AND (IVIg) AND (Ineffective) AND (Rituximab) AND (autoimmune encephalitis) AND (cyclophosphamide) AND (steroid IV))"}
{"candidate_id": "LLM00638", "doc_id": "NCT02774317_exc", "case_bucket": "or", "source_criterion": "Patients who are being prepared for surgery, or during or after surgery. Patients with congenital anomalies, chromosomal anomalies, or heart defects. Patients whose parents refuse to consent.", "candidate_expression": "((after surgery) AND (being prepared for) AND (chromosomal anomalies) AND (congenital anomalies) AND (during surgery) AND (heart defects) AND (surgery))"}
{"candidate_id": "LLM00639", "doc_id": "NCT00846703_inc", "case_bucket": "or", "source_criterion": "Cytologically proven acute lymphoblastic leukemia (ALL) No relapse of a previously unrecognized ALL Patients must meet one of the following risk criteria: Standard-risk (SR) group meeting all of the following criteria: Blasts < 1,000/µL in peripheral blood (PB) on day 8 Aged 1 to < 6 years Initial WBC < 20,000/µL M1 (5%) or M2 (= 5% to < 25%) blasts in bone marrow on day 15; M1 marrow on day 33. Aged < 1 or = 6 years and/or WBC = 20,000/µL Blasts < 1,000/µL in PB on day 8 M1 or M2 marrow on day 15 M3 (= 25%) marrow on day 15 OR meets SR criteria but M3 marrow on day 15 and *M1 marrow on day 33. Meets IR criteria and M3 marrow on day 15 (not SR and M3 on day 15) Blasts = 1,000/µL in PB on day 8 M2 or M3 marrow on day 33 Translocation t(9;22) [BCR/ABL+] (Philadelphia chromosome-positive) or t(4;11) [MLL/AF4+].", "candidate_expression": "((ALL) AND (ALL previously unrecognized) AND (Aged 1 to < 6 years PB) AND (Aged < 1 or = 6 years) AND (BCR/ABL +) AND (Blasts < 1,000/µL on day 8) AND (Blasts = 1,000/µL PB on day 8) AND (Blasts peripheral blood on day 8 < 1,000/µL) AND (IR criteria Meets) AND (M1 blasts (5%) AND (M1 marrow) AND (M1 marrow on day 33) AND (M2 blasts = 5% to < 25%) AND (M2 marrow) AND (M3 marrow) AND (M3 marrow = 25% on day 15) AND (M3 marrow on day 15) AND (M3 on day 15) AND (MLL/AF4 +) AND (PB) AND (Philadelphia chromosome positive) AND (SR) AND (SR criteria meets) AND (SR not) AND (Standard-risk) AND (Translocation t(9;22)) AND (WBC = 20,000/µL) AND (WBC Initial < 20,000/µL) AND (acute lymphoblastic leukemia Cytologically proven) AND (criteria all) AND (t(4;11)) AND NOT (relapse))"}
{"candidate_id": "LLM00640", "doc_id": "NCT03461679_exc", "case_bucket": "other", "source_criterion": "Unable to consent Chronic opioid consumption Allergy to study medication Lower limb surgery preceding year Unable to complete baseline testing, pre-existing neurological deficit Contraindication to spinal anaesthesia", "candidate_expression": "((Allergy) AND (Contraindication) AND (Lower limb surgery) AND (Unable to consent) AND (neurological deficit pre-existing) AND (opioid consumption Chronic) AND (spinal anaesthesia) AND (study medication))"}
{"candidate_id": "LLM00641", "doc_id": "NCT03140423_inc", "case_bucket": "other", "source_criterion": "Inclusion criteria includes all U.S. HCA hospitals with an adult ICU; Note: Unit of randomization is the hospital, but the participants are hospital adult ICUs All patients within adult ICUs are included, including rare patients <18 years and >=12 years.", "candidate_expression": "((HCA hospitals) AND (U.S.) AND (adult) AND (adult ICU) AND (adult ICUs) AND (rare patients) AND (year <18 years and >=12 years))"}
{"candidate_id": "LLM00642", "doc_id": "NCT03506009_exc", "case_bucket": "or", "source_criterion": "mRS=2; History of stroke within 3 months; History of intracranial hemorrhage; Suspected subarachnoid hemorrhage; Intracranial tumour, vascular malformation or arterial aneurysm; Major surgery within 1 month; Systolic pressure =180 mmHg or diastolic pressure =110 mmHg; Platelet count < 105/mm3; Heparin therapy or oral anticoagulation therapy within 48 hours; Abnormal APTT; Thrombin or Xa factor inhibitor; Severe disease with a life expectancy of less than 3 months; Blood glucose < 50 mg/dL (2.7mmol/L); Patients who have received any other investigational drug or device within 3 months; Pregnancy; Researchers consider patients inappropriate to participate in the registry.", "candidate_expression": "((APTT Abnormal) AND (Blood glucose < 50 mg/dL 2.7mmol/L) AND (Heparin) AND (Major surgery within 1 month) AND (Patients who have received any other investigational drug or device within 3 months;) AND (Platelet count < 105/mm3) AND (Pregnancy) AND (disease Severe life expectancy) AND (intracranial hemorrhage) AND (mRS =2) AND (stroke within 3 months) AND (subarachnoid hemorrhage) AND ((Systolic pressure =180 mmHg) OR (diastolic pressure =110 mmHg)) AND ((oral anticoagulation therapy) OR (therapy)) AND ((Thrombin) OR (Xa factor inhibitor)) AND ((Intracranial tumour) OR (arterial aneurysm) OR (vascular malformation)))"}
{"candidate_id": "LLM00643", "doc_id": "NCT02787070_inc", "case_bucket": "or", "source_criterion": "Infection with Plasmodium falciparum or P. vivax either alone or mixed Age >12 months Weight >5kg Living in the study clusters", "candidate_expression": "((>12 months) AND (>5kg) AND (Age) AND (Infection) AND (P. vivax) AND (Plasmodium falciparum) AND (Weight))"}
{"candidate_id": "LLM00644", "doc_id": "NCT02979561_inc", "case_bucket": "or", "source_criterion": "Men and women aged > 18 years Angiographically confirmed acute massive pulmonary embolism with involvement of Central pulmonary arteries. endovascular mechanical thrombus fragmentation + thrombolytic therapy (using recombinant tissue activator of plasminogen), performed for treatment of the above-mentioned pulmonary embolism in less than 48 hours before randomization. The patient should be randomized no earlier than 24 hours after procedures endovascular mechanical thrombus fragmentation + thrombolytic therapy Written informed consent signed by patient.", "candidate_expression": "((> 18 years) AND (Angiographically) AND (Angiographically confirmed) AND (acute) AND (aged) AND (endovascular mechanical thrombus fragmentation) AND (in less than 48 hours before randomization) AND (involvement of Central pulmonary arteries) AND (massive) AND (pulmonary embolism) AND (recombinant tissue activator of plasminogen) AND (ritten informed consent signed by patient) AND (thrombolytic therapy) AND (treatment) AND ((Men) OR (women)))"}
{"candidate_id": "LLM00645", "doc_id": "NCT03278548_inc", "case_bucket": "or", "source_criterion": "Patients undergoing elective abdominal surgery with an expected blood loss of = 500 ml ASA Physical Status II - III Signed written informed consent form Body weight = 140 kg Sepsis Burns Renal impairment (AKIN stage = 1) or acute and/or chronic renal replacement therapy Intracranial or cerebral haemorrhage Critically ill patients (typically admitted to the intensive care unit) Hyperhydration Pulmonary oedema Dehydration Hyperkalaemia Severe hypernatraemia Severe hyperchloraemia Severely impaired hepatic function Congestive heart failure Severe coagulopathy Organ transplant patients Metabolic alkalosis Simultaneous participation in another interventional clinical trial (drugs or medical devices studies)", "candidate_expression": "((AKIN stage = 1 acute chronic) AND (ASA Physical Status II - III) AND (Body weight = 140 kg) AND (Burns) AND (Congestive heart failure) AND (Critically ill) AND (Dehydration) AND (Hyperhydration) AND (Hyperkalaemia) AND (Intracranial haemorrhage) AND (Metabolic alkalosis) AND (Organ transplant) AND (Pulmonary oedema) AND (Renal impairment) AND (Sepsis) AND (Signed written informed consent form) AND (Simultaneous participation in another interventional clinical trial (drugs or medical devices studies)) AND (abdominal surgery elective) AND (admitted typically) AND (cerebral haemorrhage) AND (coagulopathy Severe) AND (expected blood loss = 500 ml) AND (hyperchloraemia Severe) AND (hypernatraemia Severe) AND (impaired hepatic function Severely) AND (intensive care unit) AND (renal replacement therapy))"}
{"candidate_id": "LLM00646", "doc_id": "NCT03120533_exc", "case_bucket": "or", "source_criterion": "Healthy Volunteers Treprostinil contraindications: Known hypersensitivity to treprostinil or any of the excipients, Pulmonary arterial hypertension related to veno-occlusive disease, Congestive heart failure due to severe left ventricular dysfunction, Severe hepatic insufficiency (Child-Pugh stage C), Evolving gastrointestinal ulcer, intracranial hemorrhage, recent trauma or other clinical condition that may lead to bleeding, Congenital or acquired valvular abnormalities with cardiac repercussions, Severe ischemic heart disease or unstable angina; Myocardial infarction in the last six months; Decompensated cardiac insufficiency not medically controlled; Severe arrhythmias; Cerebrovascular lesions (such as transient ischemic attack, stroke) that occurred within the last three months. Persons referred to in Articles L1121-5 to L1121-8 of the French Public health Code: pregnant woman, parturient, nursing mother, person deprived of liberty by judicial or administrative decision, person subject to a legal protection measure, can not Be included in clinical trials. Subject in an exclusion period from another study, Subject who would receive more than 4500 euros of compensation due to his participation in other biomedical research in the 12 months preceding this study Systemic sclerosis patients: Iloprost cure carried out in the previous month or planned in the following month. Initiation or change of dosage of bosentan, sildenafil or calcium channel blockers in the previous month or in the following month Digital Sympathectomy or botulinum toxin injection planned in the following month. Clinically superinfected digital ulcers Treprostinil contraindications: Known hypersensitivity to treprostinil or any of the excipients, Pulmonary arterial hypertension related to veno-occlusive disease, Congestive heart failure due to severe left ventricular dysfunction, Severe hepatic insufficiency (Child-Pugh stage C), Evolving gastrointestinal ulcer, intracranial hemorrhage, recent trauma or other clinical condition that may lead to bleeding, Congenital or acquired valvular abnormalities with cardiac repercussions, Severe ischemic heart disease or unstable angina; Myocardial infarction in the last six months; Decompensated cardiac insufficiency not medically controlled; Severe arrhythmias; Cerebrovascular lesions (such as transient ischemic attack, stroke) that occurred within the last three months. Persons referred to in Articles L1121-5 to L1121-8 of the French Public health Code: pregnant woman, parturient, nursing mother, person deprived of liberty by judicial or administrative decision, person subject to a legal protection measure, can not Be included in clinical trials. Subject in an exclusion period from another study, Subject who would receive more than 4500 euros of compensation due to his participation in other biomedical research in the 12 months preceding this study", "candidate_expression": "((Child-Pugh) AND (Congestive heart failure) AND (Evolving) AND (Pulmonary arterial hypertension) AND (Severe) AND (Systemic sclerosis) AND (Treprostinil) AND (any of the excipients) AND (arrhythmias) AND (bosentan) AND (calcium channel blockers) AND (contraindications) AND (digital ulcers) AND (gastrointestinal ulcer) AND (hypersensitivity) AND (in the following month) AND (in the last six months) AND (in the previous month) AND (intracranial hemorrhage) AND (not medically controlled) AND (planned) AND (pregnant) AND (recent) AND (severe) AND (sildenafil) AND (stage C) AND (superinfected) AND (trauma) AND (treprostinil) AND (veno-occlusive disease) AND (with cardiac repercussions) AND (within the last three months) AND (woman) AND ((Cerebrovascular lesions) OR (Congenital valvular abnormalities) OR (Decompensated cardiac insufficiency) OR (Myocardial infarction) OR (acquired valvular abnormalities) OR (arrhythmias) OR (clinical condition that may lead to bleeding) OR (ischemic heart disease) OR (unstable angina)) AND ((hepatic insufficiency) OR (left ventricular dysfunction)) AND ((deprived of liberty) OR (nursing) OR (parturient) OR (subject to a legal protection) OR (woman)) AND ((Cerebrovascular lesions) OR (Congenital valvular abnormalities) OR (Decompensated cardiac insufficiency) OR (Myocardial infarction) OR (acquired valvular abnormalities) OR (clinical condition that may lead to bleeding) OR (ischemic heart disease) OR (unstable angina)) AND ((stroke) OR (transient ischemic attack)) AND ((deprived of liberty) OR (nursing) OR (parturient) OR (pregnant)) AND ((Iloprost)) AND ((in the following month) OR (in the previous month)) AND ((Digital Sympathectomy) OR (botulinum toxin injection)) AND ((any of the excipients) OR (treprostinil)) AND ((Congestive heart failure) OR (Pulmonary arterial hypertension) OR (gastrointestinal ulcer) OR (hepatic insufficiency) OR (intracranial hemorrhage) OR (left ventricular dysfunction)))"}
{"candidate_id": "LLM00647", "doc_id": "NCT01440296_exc", "case_bucket": "other", "source_criterion": "any condition that would contra-indicate Magnetic Resonance Imaging or administration of contrast agent", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00648", "doc_id": "NCT03336801_inc", "case_bucket": "other", "source_criterion": "Scheduled back surgery", "candidate_expression": "((Scheduled) AND (back surgery))"}
{"candidate_id": "LLM00649", "doc_id": "NCT02804646_exc", "case_bucket": "or", "source_criterion": "1) pregnancy, breast-feeding women, or female patients of childbearing potential but did not take contraceptive measures;2) existing severe acute infection and is not controlled; or purulent and chronic infection, delayed healing wounds; 3) the original severe heart disease, including congestive heart failure, uncontrolled high-risk arrhythmias, unstable angina, myocardial infarction, severe heart valve disease and resistant hypertension; 4) suffering from neurological and psychiatric diseases or mental disorders is not easy to control, poor compliance, and can not be described with treatment responders; primary brain or central nervous metastasis disease has not been controlled, with significant cranial hypertension or neuropsychiatric symptoms; 5) have bleeding tendencies; 6) other researchers believe that patients should not participate in the present trial.", "candidate_expression": "((arrhythmias uncontrolled high-risk) AND (bleeding tendencies) AND (central nervous metastasis disease) AND (congestive heart failure) AND (cranial hypertension) AND (delayed healing wounds) AND (heart disease severe) AND (heart valve disease severe) AND (hypertension resistant) AND (infection purulent chronic) AND (infection severe acute not controlled) AND (mental disorders) AND (myocardial infarction) AND (neurological diseases) AND (neuropsychiatric symptoms) AND (poor compliance) AND (pregnancy, breast-feeding women, or female patients of childbearing potential but did not take contraceptive measures;) AND (primary brain disease) AND (psychiatric diseases) AND (unstable angina))"}
{"candidate_id": "LLM00650", "doc_id": "NCT02282319_exc", "case_bucket": "other", "source_criterion": "micturition problems, neurological history or previous lower abdominal surgery with an abnormal micturition", "candidate_expression": "((abnormal) AND (lower abdominal surgery) AND (micturition) AND (neurological history))"}
```
