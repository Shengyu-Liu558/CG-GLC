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
{"candidate_id": "LLM07551", "doc_id": "NCT02974686_inc", "case_bucket": "or", "source_criterion": "Kidney transplant recipients at Washington University/Barnes-Jewish Hospital Experiencing GI toxicity from MPA as determined by the treating physician within 12 months post-renal transplant On standard immunosuppression with tacrolimus and prednisone", "candidate_expression": "((GI toxicity) AND (Kidney transplant) AND (MPA) AND (Washington University/Barnes-Jewish Hospital) AND (standard immunosuppression) AND ((prednison) OR (tacrolimus)))"}
{"candidate_id": "LLM07552", "doc_id": "NCT02687178_inc", "case_bucket": "or", "source_criterion": "Caucasian patients affected by uncomplicated, essential hypertension, not well controlled by concomitant administration of ACE-I or ARBs and diuretics at the maximum dosage.", "candidate_expression": "((Caucasian) AND (diuretics) AND (essential hypertension) AND (maximum dosage) AND (not well controlled) AND (uncomplicated) AND ((ACE-I) OR (ARBs)))"}
{"candidate_id": "LLM07553", "doc_id": "NCT03380429_exc", "case_bucket": "or", "source_criterion": "Subjects with a known or suspected alcohol or drug abuse which in the opinion of the investigator could interfere with the subject's proper completion of the protocol requirement. History of life threatening asthma: Defined as an asthma episode that required intubation and/or was associated with hypercapnea, respiratory arrest or hypoxic seizures within the last 6 months. A lower respiratory tract infection within 7 days of the screening visit. Concurrent diagnosis of chronic obstructive pulmonary disease (COPD) or other respiratory disorders including active tuberculosis, lung cancer, bronchiectasis, sarcoidosis, lung fibrosis, pulmonary hypertension, interstitial lung diseases or other active pulmonary diseases. History of hypersensitivity/intolerance to any components of the study inhalers (example, lactose, magnesium stearate). In addition, subjects with a history of severe milk protein allergy that, in the opinion of the study physician, contraindicates participation will also be excluded. Historical or current evidence of clinically significant or rapidly progressing or unstable cardiovascular, neurological, cardiovascular, neurological, renal, hepatic, immunological, endocrine (including uncontrolled diabetes or thyroid disease) or hematological abnormalities that are uncontrolled. Significant is defined as any disease that, in the opinion of the investigator, would put the safety of the subject at risk through participation, or which would affect the analysis if the disease/condition exacerbated during the study. Subjects who have ever received treatment with biological based therapy example, omalizumab, mepolizumab, for asthma. Subjects who have received an investigational drug and/or medical device within 30 days of entry into this study (Screening), or within five drug half-lives of the investigational drug, whichever is longer. A subject will not be eligible for this study if he/she is an immediate family member of the participating investigator, sub-investigator, study coordinator, employee of the participating investigator, or any family member of a Propeller Health employee.", "candidate_expression": "((Historical) AND (Subjects who have received an investigational drug and/or medical device within 30 days of entry into this study (Screening), or within five drug half-lives of the investigational drug, whichever is longer.) AND (Subjects with a known or suspected alcohol or drug abuse which in the opinion of the investigator could interfere with the subject's proper completion of the protocol requirement.) AND (active) AND (allergy) AND (asthma) AND (asthma episode) AND (bronchiectasis) AND (cardiovascular abnormalities) AND (chronic obstructive pulmonary disease (COPD)) AND (clinically significant) AND (components of the study inhalers) AND (contraindicates participation) AND (current) AND (diabetes) AND (endocrine abnormalities) AND (hematological abnormalities) AND (hepatic abnormalities) AND (history) AND (hypercapnea) AND (hypersensitivity) AND (hypoxic seizures) AND (immunological abnormalities) AND (interstitial lung diseases) AND (intolerance) AND (intubation) AND (lactose) AND (life threatening) AND (lower respiratory tract infection) AND (lung cancer) AND (lung fibrosis) AND (magnesium stearate) AND (mepolizumab) AND (milk protein) AND (neurological abnormalities) AND (omalizumab) AND (other) AND (pulmonary diseases) AND (pulmonary hypertension) AND (rapidly progressing) AND (renal abnormalities) AND (required intubation) AND (respiratory arrest) AND (respiratory disorders) AND (sarcoidosis) AND (screening visit) AND (severe) AND (thyroid disease) AND (treatment) AND (tuberculosis) AND (uncontrolled) AND (unstable) AND (within 7 days of the screening visit) AND (within the last 6 months))"}
{"candidate_id": "LLM07554", "doc_id": "NCT03320057_inc", "case_bucket": "or", "source_criterion": "Women seeking medication abortion through 70 days gestation Eligible for Mifeprex(r) at a study clinical site English or Spanish speaking Willing and able to participate in the study, including willing to go to the study pharmacy to obtain mifepristone", "candidate_expression": "((English speaking) AND (Mifeprex(r) Eligible for) AND (Spanish speaking) AND (Willing and able to participate in the study) AND (Women) AND (medication abortion through 70 days gestation) AND (mifepristone to obtain) AND (study clinical site) AND (willing to go to the study pharmacy))"}
{"candidate_id": "LLM07555", "doc_id": "NCT02645474_inc", "case_bucket": "or", "source_criterion": "adult patients ASA class 1 to 3 patients patients scheduled for elective breast mastectomy or quadrantectomy", "candidate_expression": "((1 to 3) AND (ASA class) AND (adult) AND (elective) AND ((breast quadrantectomy) OR (mastectomy)))"}
{"candidate_id": "LLM07556", "doc_id": "NCT02489045_inc", "case_bucket": "other", "source_criterion": "Be scheduled for trans-jugular liver biopsy the day of the ultrasound procedure. Be at least 21 years of age. Be medically stable. If a female of child-bearing potential, must have a negative pregnancy test. Be conscious and able to comply with study procedures. Have read and signed the IRB-approved Informed Consent form for participating in the study.", "candidate_expression": "((Have read and signed the IRB-approved Informed Consent form for participating in the study.) AND (age at least 21 years) AND (child-bearing potential) AND (female) AND (medically stable) AND (negative) AND (pregnancy test) AND (trans-jugular liver biopsy the day of the ultrasound procedure) AND (ultrasound procedure))"}
{"candidate_id": "LLM07557", "doc_id": "NCT02678663_inc", "case_bucket": "other", "source_criterion": "Subjects over the age of 18 years who agree informed consent and who have at least one polyp of eligible size (6-10mm)", "candidate_expression": "((18 years over) AND (6-10mm) AND (age) AND (agree informed consent) AND (at least one) AND (eligible size) AND (polyp))"}
{"candidate_id": "LLM07558", "doc_id": "NCT01774019_exc", "case_bucket": "or", "source_criterion": "Biliary strictures caused by confirmed benign tumors Biliary strictures caused by malignancies other than pancreatic cancer, distal CBD cholangiocarcinoma and other periampullary cancers Surgically altered biliary tract anatomy, not including prior cholecystectomy Neoadjuvant chemotherapy for current malignancy Palliative indication due to reasons other than surgical candidate status Previous biliary drainage by ERCP/PTC Patients for whom endoscopic techniques are contraindicated Participation in another investigational trial within 90 days Pregnancy", "candidate_expression": "((Biliary strictures) AND (Neoadjuvant chemotherapy) AND (Pregnancy) AND (Surgically altered biliary tract anatomy) AND (benign tumors confirmed) AND (biliary drainage by ERCP/PTC Previous) AND (contraindicated) AND (endoscopic techniques) AND (malignancies) AND (malignancy) AND NOT (cholecystectomy prior) AND ((distal CBD cholangiocarcinoma) OR (other periampullary cancers) OR (pancreatic cancer)))"}
{"candidate_id": "LLM07559", "doc_id": "NCT03519568_inc", "case_bucket": "or", "source_criterion": "aged = 6 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures the subjects have completed the basic immunization of 2 needle recombinant hepatitis B vaccine, there is no inoculation history of EV71 vaccine, and no history of EV71 infection the last vaccination intervals = 14 days temperature = 37<U+2103> aged = 6 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures there is no inoculation history of EV71 vaccine, and there is no history of EV71 infection the last vaccination intervals = 14 days temperature = 37<U+2103> aged = 8 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures there is no inoculation history of EV71 vaccine, and there is no history of EV71 infection the last vaccination intervals = 14 days and the last attenuated live vaccine intervals=28days temperature = 37<U+2103> aged = 8 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures there is no inoculation history of EV71 vaccine, and there is no history of EV71 infection the last vaccination intervals = 14 days and the last attenuated live vaccine intervals = 28 days temperature = 37<U+2103>", "candidate_expression": "((EV71 infection history) AND (EV71 vaccine) AND (aged = 6 months) AND (aged = 8 months) AND (last attenuated live vaccine intervals = 28 days) AND (last attenuated live vaccine intervals =28days) AND (last vaccination intervals = 14 days) AND (needle recombinant hepatitis B vaccine 2) AND (sign the informed consent form) AND (temperature = 37<U+2103>) AND (the legal guardians participate in all the planned follow-up and be able to comply with all research procedures) AND NOT (inoculation history) AND NOT (EV71 infection history))"}
{"candidate_id": "LLM07560", "doc_id": "NCT02862314_inc", "case_bucket": "other", "source_criterion": "aged 18 or older, have undergone oro-tracheal intubation for a coma (Glasgow Coma Score below or equal to 8), with mechanical ventilation initiated in the first 48 hours following hospital admission", "candidate_expression": "((Glasgow Coma Score below or equal to 8)) AND (aged 18 or older) AND (coma) AND (mechanical ventilation first 48 hours following hospital admission) AND (oro-tracheal intubation))"}
{"candidate_id": "LLM07561", "doc_id": "NCT01680081_exc", "case_bucket": "or", "source_criterion": "Contraindication of CT Known allergy to iodinated contrast media or history of contrast-induced nephropathy Decreased renal function: elevated serum creatinine(>1.5mg/dl) Contraindication to beta-blockers Severe arrhythmia: arterial fibrillation or uncontrolled tachyarrhythmia, or advanced atrioventricular block (second or third degree heart block) Contraindication of MRI Claustrophobia Metallic hazards Pacemaker implant eGFR<30 ml/min Unstable or uncooperative patients Limited life expectancy due to cancer or end-stage renal or liver disease Evidence of severe symptomatic heart failure (NYHA Class III or IV) Previous myocardial infarction, coronary artery intervention, coronary artery bypass surgery, or other cardiac surgery", "candidate_expression": "((<30 ml/min) AND (>1.5mg/dl) AND (Class III or IV) AND (Contraindication) AND (Contraindication of CT) AND (Decreased) AND (Limited) AND (MRI) AND (NYHA) AND (Previous) AND (Severe) AND (Unstable patients) AND (arrhythmia) AND (beta-blockers) AND (elevated) AND (heart failure) AND (iodinated contrast media) AND (life expectancy) AND (renal function) AND (serum creatinine) AND (severe) AND (symptomatic) AND (uncooperative patients) AND ((advanced atrioventricular block) OR (arterial fibrillation) OR (uncontrolled tachyarrhythmia)) AND ((second degree heart block) OR (third degree heart block)) AND ((Known allergy) OR (contrast-induced nephropathy)) AND ((Claustrophobia) OR (Metallic hazards) OR (Pacemaker implant) OR (eGFR)) AND ((cancer) OR (end-stage renal disease) OR (liver disease)) AND ((coronary artery bypass surgery) OR (coronary artery intervention) OR (myocardial infarction) OR (other cardiac surgery)))"}
{"candidate_id": "LLM07562", "doc_id": "NCT02364648_inc", "case_bucket": "other", "source_criterion": "Stage 3 - 5 Chronic Kidney Disease", "candidate_expression": "((Chronic Kidney Disease) AND (Stage 3 - 5))"}
{"candidate_id": "LLM07563", "doc_id": "NCT02638935_inc", "case_bucket": "or", "source_criterion": "Female Age ≥18 years Patients with a lesion > 0.5 cm in largest diameter size, initially scored BI-RADS® 3, 4a, 4b or 4c in B-mode ultrasound Informed consent about histological examination (core cut biopsy (CCB), vacuum-assisted biopsy (VAB), fine needle aspiration (FNA) or surgery) has already been given in the course of clinical routine Signed informed consent of study participation", "candidate_expression": "((Age ≥18 years) AND (B-mode ultrasound) AND (BI-RADS® 3, 4a, 4b or 4c) AND (Female) AND (Informed consent) AND (Signed informed consent of study participation) AND (core cut biopsy (CCB)) AND (fine needle aspiration (FNA)) AND (histological examination) AND (largest diameter size > 0.5 cm) AND (lesion) AND (surgery) AND (vacuum-assisted biopsy (VAB)))"}
{"candidate_id": "LLM07564", "doc_id": "NCT02907554_inc", "case_bucket": "or", "source_criterion": "Male and females aged 18 to 70 years Brain death Male and females aged 18 to 70 years Indication of kidney transplantation Informed consent", "candidate_expression": "((18 to 70 years) AND (Brain death) AND (Indication) AND (Informed consent) AND (Male) AND (aged) AND (females) AND (kidney transplantation))"}
{"candidate_id": "LLM07565", "doc_id": "NCT00931983_inc", "case_bucket": "or", "source_criterion": "Children between the ages of 4-18 with incomplete ASIA C or D spinal cord injuries at least 12 months before study enrolment Non-ambulatory or 'exercise only' ambulators with or without assistive devices Normal motor and cognitive development up to time of injury Medical Stability", "candidate_expression": "(('exercise only' ambulators) AND (4-18) AND (ASIA) AND (C or D) AND (Children) AND (Medical Stability) AND (Non-ambulatory) AND (Normal) AND (ages) AND (assistive devices) AND (at least 12 months before study enrolment) AND (cognitive development) AND (incomplete) AND (motor development) AND (spinal cord injuries) AND (study enrolment) AND (time of injury) AND (up to time of injury))"}
{"candidate_id": "LLM07566", "doc_id": "NCT02557386_exc", "case_bucket": "other", "source_criterion": "Chronic pain more than 3 months Drug abuse Chronic use of analgesic drugs (more than 3 months) Psychiatric illness Peripheral neuropathy Drug allergy Severe gastroesophageal reflux disease", "candidate_expression": "((Chronic pain more than 3 months) AND (Drug) AND (Drug abuse) AND (Peripheral neuropathy) AND (Psychiatric illness) AND (allergy) AND (analgesic drugs Chronic more than 3 months) AND (gastroesophageal reflux disease Severe))"}
{"candidate_id": "LLM07567", "doc_id": "NCT01604187_exc", "case_bucket": "or", "source_criterion": "A previous history of intolerance to the study drug or related compounds and additives History of alcoholism, drug abuse, psychiatric, psychological or other emotional problems that are likely to invalidate informed consent Sleep apnoea Chronic obstructive pulmonary disease BMI = 35 or weight < 50 kg SpO2 < 90 % Concomitant drug therapy known to cause significant enzyme induction or inhibition of CYP 3A4. Pregnancy or nursing.", "candidate_expression": "((< 50 kg) AND (< 90 %) AND (= 35) AND (Chronic obstructive pulmonary disease) AND (Concomitant) AND (Sleep apnoea) AND (SpO2) AND (alcoholism) AND (drug abuse) AND (drug therapy) AND (intolerance) AND (previous history) AND ((emotional problems) OR (psychiatric problems) OR (psychological problems)) AND ((BMI) OR (weight)) AND ((enzyme induction of CYP 3A4) OR (enzyme inhibition of CYP 3A4)) AND ((Pregnancy) OR (nursing)) AND ((related compounds) OR (study drug)))"}
{"candidate_id": "LLM07568", "doc_id": "NCT03315975_inc", "case_bucket": "or", "source_criterion": "adults capable of providing consent have a diagnosis of locally advanced or metastatic melanoma", "candidate_expression": "((adults) AND (capable of providing consent) AND (melanoma) AND ((locally advanced) OR (metastatic)))"}
{"candidate_id": "LLM07569", "doc_id": "NCT02573168_inc", "case_bucket": "or", "source_criterion": "18 years of age or older; Suffer from schizophrenia/schizoaffective disorder meeting Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, Text Revision (DSM-IV-TR) criteria; Have a total baseline score on the Brief Psychiatric Rating Scale (BPRS) = 45; Be capable and willing to provide written informed consent to participate in this study; Agree to abide by the study protocol and its restrictions and be able to complete all aspects of the study, including all visits and tests", "candidate_expression": "((Agree to abide by the study protocol and its restrictions and be able to complete all aspects of the study, including all visits and tests) AND (BPRS) AND (Be capable and willing to provide written informed consent to participate in this study) AND (Brief Psychiatric Rating Scale = 45) AND (DSM-IV-TR) AND (Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, Text Revision) AND (age 18 years or older) AND ((schizoaffective disorder) OR (schizophrenia)))"}
{"candidate_id": "LLM07570", "doc_id": "NCT03560310_exc", "case_bucket": "or", "source_criterion": "Previously enrolled in this study (i.e. patient now at repeat encounter) Concomitant surgical procedure other than CABG Anticoagulant treatment after the operation (e.g. warfarin, direct thrombin inhibitors (dabigatran), FXa inhibitors (rivaroxaban, apixaban, heparin, low-molecular weight heparin, fondaparinux) Discharge from the operating hospital to an ICU at another hospital Pregnancy or lactation Known intolerance or contraindication to ticagrelor or ASA Any disorder that may interfere with drug absorption Any condition other than coronary artery disease with a life expectancy <12 months Known chronic liver disease, renal disease requiring dialysis or bleeding disorder Atrioventricular block II and III in patients without pacemaker Any other indication for dual antiplatelet therapy, i.e. recent stent implantation Debilitating stroke within 90 days before inclusion Previous intracranial bleeding Treatment with immunosuppressants (e.g. cyclosporine and tacrolimus) Treatment with strong CYP3A4-inhibitors (e.g. ketoconazole, clarithromycin, nefazodone, ritonavir or atazanavir) Any condition that in the opinion of the investigator may interfere with adherence to trial protocol", "candidate_expression": "((ASA) AND (Anticoagulant treatment after the operation) AND (Atrioventricular block II) AND (Atrioventricular block III) AND (CABG other than) AND (Debilitating) AND (Discharge) AND (FXa inhibitors) AND (ICU) AND (Pregnancy) AND (apixaban) AND (atazanavir) AND (bleeding disorder) AND (chronic liver disease) AND (clarithromycin) AND (condition life expectancy) AND (contraindication) AND (cyclosporine) AND (dabigatran) AND (dialysis requiring) AND (direct thrombin inhibitors) AND (disorder may interfere with drug absorption) AND (dual antiplatelet therapy) AND (enrolled in this study Previously) AND (fondaparinux) AND (heparin) AND (hospital another) AND (immunosuppressants) AND (indication) AND (intolerance) AND (intracranial bleeding Previous) AND (ketoconazole) AND (lactation) AND (low-molecular weight heparin) AND (nefazodone) AND (operating hospital) AND (operation) AND (renal disease) AND (ritonavir) AND (rivaroxaban) AND (stent implantation recent) AND (stroke within 90 days before inclusion) AND (strong CYP3A4-inhibitors) AND (surgical procedure Concomitant) AND (tacrolimus) AND (ticagrelor) AND (warfarin) AND NOT (coronary artery disease) AND NOT (pacemaker))"}
{"candidate_id": "LLM07571", "doc_id": "NCT02609048_exc", "case_bucket": "or", "source_criterion": "1. A medical condition, other than PBC, that in the investigator's opinion would preclude full participation in the study or confound its results (e.g., cancer on active treatment) 2. AST or ALT > 3 × ULN 3. Total bilirubin > 2 × ULN 4. Auto-immune hepatitis 5. Primary sclerosing cholangitis 6. Known history of alpha-1-Antitrypsin deficiency 7. Known history of chronic viral hepatitis 8. Creatine kinase above ULN 9. Serum creatinine above ULN 10. For females, pregnancy or breast-feeding 11. Use of colchicine, methotrexate, azathioprine, or systemic steroids in the two months preceding screening 12. Current use of fibrates, including fenofibrates, or simvastatin 13. Use of an experimental treatment for PBC 14. Use of experimental or unapproved immunosuppressant 15. Any other condition(s) that would compromise the safety of the subject or compromise the quality of the clinical study, as judged by the Investigator", "candidate_expression": "((> 2 × ULN) AND (> 3 × ULN) AND (A medical condition, other than PBC, that in the investigator's opinion would preclude full participation in the study or confound its results (e.g., cancer on active treatment)) AND (ALT) AND (AST) AND (Any other condition(s) that would compromise the safety of the subject or compromise the quality of the clinical study, as judged by the Investigator) AND (Auto-immune hepatitis) AND (Creatine kinase) AND (Current) AND (PBC) AND (Primary sclerosing cholangitis) AND (Serum creatinine) AND (Total bilirubin) AND (above ULN) AND (alpha-1-Antitrypsin deficiency) AND (azathioprine) AND (breast-feeding) AND (chronic) AND (colchicine) AND (experimental) AND (experimental treatment for PBC) AND (females) AND (fenofibrates) AND (fibrates) AND (history) AND (immunosuppressant) AND (in the investigator's opinion) AND (in the two months preceding screening) AND (medical condition) AND (methotrexate) AND (other than) AND (pregnancy) AND (screening) AND (simvastatin) AND (systemic steroids) AND (unapproved) AND (viral hepatitis))"}
{"candidate_id": "LLM07572", "doc_id": "NCT03034733_inc", "case_bucket": "other", "source_criterion": "primary total knee replacement surgery ASA (american society of anesthesiologists) class 1-3", "candidate_expression": "((1-3) AND (ASA class) AND (american society of anesthesiologists) AND (primary) AND (total knee replacement surgery))"}
{"candidate_id": "LLM07573", "doc_id": "NCT02997215_exc", "case_bucket": "or", "source_criterion": "Open surgery; Patients allergic to lidocaine or other local anesthetics; Drug abuser.", "candidate_expression": "((Drug abuser) AND (Open surgery) AND (allergic) AND (lidocaine) AND (local anesthetics) AND (other))"}
{"candidate_id": "LLM07574", "doc_id": "NCT03209687_exc", "case_bucket": "or", "source_criterion": "Females who have high response (estradiol at time of ovulation trigger is > 5000 pg/ml or more than 15 oocytes are retrieved)", "candidate_expression": "((Females) AND (estradiol at time of ovulation trigger > 5000 pg/ml) AND (high response) AND (oocytes retrieved more than 15))"}
{"candidate_id": "LLM07575", "doc_id": "NCT02321202_exc", "case_bucket": "or", "source_criterion": "Contraindication for hepatectomy, including gastrointestinal hemorrhage, severe hemorrhagic disorders, explicit acute nonspecific infectious lesion, overt ascites, Child-Pugh Score C, indocyanine green retention rate at 15min (ICGR15)＞30%(12), serum hepatitis B virus (HBV)-DNA＞126 copies/ml and serum alanine aminotransferase (ALT) ＞ 2×ULN, serum triglycerides＞2.0 mmol/L, circulatory shock, stroke, acute myocardial infarction, renal failure, coma of unknown cause Pregnancy Age of＜18y or＞75y Performed intraoperative ablation Unresectable tumor during operation Allergic reactions against fish or egg proteins", "candidate_expression": "((Age ＜18y or＞75y) AND (Allergic reactions) AND (Child-Pugh Score C) AND (Contraindication for hepatectomy) AND (Pregnancy) AND (Unresectable tumor) AND (acute myocardial infarction) AND (ascites overt) AND (circulatory shock) AND (coma unknown cause) AND (egg proteins) AND (fish proteins) AND (gastrointestinal hemorrhage) AND (hemorrhagic disorders severe) AND (hepatectomy) AND (indocyanine green retention rate at 15min (ICGR15) ＞30%) AND (infectious lesion acute nonspecific) AND (intraoperative ablation) AND (renal failure) AND (serum alanine aminotransferase (ALT) ＞ 2×ULN) AND (serum hepatitis B virus (HBV)-DNA ＞126 copies/ml) AND (serum triglycerides ＞2.0 mmol/L) AND (stroke))"}
```
