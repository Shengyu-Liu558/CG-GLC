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
{"candidate_id": "LLM06701", "doc_id": "NCT00317148_exc", "case_bucket": "or", "source_criterion": "Body mass index (BMI) of 35 kg/m2 or more. Significant metabolic and endocrine diseases. Diagnosis of cancer. Use of steroids or drugs that interfere with the metabolism of estrogen. Use of any systemic estrogen, progestin, or DHEA in the eight weeks prior to randomization. Use of alternative therapies or natural products to treat postmenopausal symptoms in the four weeks prior to randomization. Palpable fibroids or uterine prolapse: Grade 2 or 3. Cigarette smoking", "candidate_expression": "((2 or 3) AND (35 kg/m2 or more) AND (Body mass index (BMI)) AND (Cigarette smoking) AND (Grade) AND (cancer) AND (in the eight weeks prior to randomization) AND (in the four weeks prior to randomization) AND (postmenopausal symptoms) AND ((DHEA) OR (systemic estrogen) OR (systemic progestin)) AND ((alternative therapies) OR (natural products)) AND ((Palpable fibroids) OR (uterine prolapse)) AND ((endocrine diseases) OR (metabolic diseases)) AND ((drugs that interfere with the metabolism of estrogen) OR (steroids)))"}
{"candidate_id": "LLM06702", "doc_id": "NCT01261832_exc", "case_bucket": "or", "source_criterion": "The patient has a known hypersensitivity or contraindication to any of the following medications: Heparin, Aspirin, Clopidogrel, Cilostazol Uncontrolled hypertension History of bleeding diathesis or known coagulopathy (including heparin-induced thrombocytopenia), or refuses blood transfusions. Baseline hemogram with Hb<10g/dL or PLT count<100,000/μL Patients already taking warfarin, cilostazol or any other type of anti-platelet agents except aspirin and clopidogrel Gastrointestinal or genitourinary bleeding within the prior 3 months, or major surgery within 2 months. Pregnancy", "candidate_expression": "((<100,000/μL) AND (<10g/dL) AND (Aspirin) AND (Baseline) AND (Cilostazol) AND (Clopidogrel) AND (Gastrointestinal bleeding) AND (Hb) AND (Heparin) AND (History) AND (PLT count) AND (Pregnancy) AND (Uncontrolled) AND (anti-platelet agents) AND (aspirin) AND (bleeding diathesis) AND (blood transfusions) AND (cilostazol) AND (clopidogrel) AND (coagulopathy) AND (contraindication) AND (except) AND (genitourinary bleeding) AND (hemogram) AND (heparin-induced thrombocytopenia) AND (hypersensitivity) AND (hypertension) AND (major surgery) AND (refuses blood transfusions) AND (warfarin) AND (within 2 months) AND (within the prior 3 months))"}
{"candidate_id": "LLM06703", "doc_id": "NCT02797548_inc", "case_bucket": "or", "source_criterion": "Planned non-cardiac surgery at least after 12 months of implantation of drug eluting stent Low or intermediate risk level surgery Written informed consent", "candidate_expression": "((Written informed consent) AND (drug eluting stent) AND (implantation) AND (intermediate risk level surgery) AND (non-cardiac surgery Planned at least after 12 months of implantation of drug eluting stent) AND (risk level surgery Low))"}
{"candidate_id": "LLM06704", "doc_id": "NCT02247128_exc", "case_bucket": "or", "source_criterion": "Need for long-term oral anticoagulation; Drug-eluting stent implantation within 3 months prior to TAVI procedure; Bare-metal stent implantation within 1 month prior to TAVI procedure; Allergy or intolerance to aspirin or clopidogrel. Drug-eluting stent implantation within 3 months prior to TAVI procedure; Bare-metal stent implantation within 1 month prior to TAVI procedure; Allergy or intolerance to (N)OAC or clopidogrel.", "candidate_expression": "((Bare-metal stent) AND (Drug-eluting stent) AND (TAVI procedure) AND (TAVI procedure TAVI procedure) AND (implantation within 1 month prior to TAVI procedure) AND (implantation within 3 months prior to TAVI procedure) AND (long-term oral anticoagulation Need for) AND ((Allergy) OR (intolerance)) AND ((aspirin) OR (clopidogrel)) AND (((N)OAC) OR (clopidogrel)))"}
{"candidate_id": "LLM06705", "doc_id": "NCT02042287_inc", "case_bucket": "other", "source_criterion": "> 18 years old Acute symptomatic BV Signed informed consent Insufficient knowledge of German Illiteracy Pregnancy Acute illness Known allergies against ingredients of the investigational products", "candidate_expression": "((Acute illness) AND (BV Acute symptomatic) AND (Illiteracy) AND (Insufficient knowledge of German) AND (Pregnancy) AND (Signed informed consent) AND (allergies) AND (ingredients of the investigational products) AND (old 18 years))"}
{"candidate_id": "LLM06706", "doc_id": "NCT01446094_inc", "case_bucket": "other", "source_criterion": "Aged 18 years or older Scheduled for invasive coronary angiography", "candidate_expression": "((18 years or older) AND (Aged) AND (Scheduled) AND (invasive coronary angiography))"}
{"candidate_id": "LLM06707", "doc_id": "NCT02825290_exc", "case_bucket": "other", "source_criterion": "PGD patients More than 4 previous embryo transfers", "candidate_expression": "((More than 4) AND (PGD) AND (embryo transfers) AND (previous))"}
{"candidate_id": "LLM06708", "doc_id": "NCT02219880_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06709", "doc_id": "NCT03360214_inc", "case_bucket": "or", "source_criterion": "Subjects must be female Subjects must be 18 years or older Subjects must be undergoing unilateral or bilateral mastectomy with tissue expander reconstruction", "candidate_expression": "((female) AND (mastectomy undergoing) AND (older 18 years or older) AND (tissue expander reconstruction) AND ((bilateral) OR (unilateral)))"}
{"candidate_id": "LLM06710", "doc_id": "NCT02797548_exc", "case_bucket": "or", "source_criterion": "Acute coronary syndrome within 1 month Heart failure NYHA III to IV Contraindication to Aspirin On anticoagulant therapy Emergent surgery Cardiac surgery High bleeding risk surgeries, e.g., Intra-cranial surgery, Intra-spinal surgery, Retinal surgery Pregnancy or breast-feeding Life expectancy less than 1year", "candidate_expression": "((Acute coronary syndrome) AND (Aspirin) AND (Cardiac surgery) AND (Contraindication) AND (Emergent surgery) AND (Heart failure) AND (High bleeding risk surgeries) AND (III to IV) AND (Intra-cranial surgery) AND (Intra-spinal surgery) AND (Life expectancy) AND (NYHA) AND (Pregnancy) AND (Retinal surgery) AND (anticoagulant therapy) AND (breast-feeding) AND (less than 1year) AND (within 1 month))"}
{"candidate_id": "LLM06711", "doc_id": "NCT01032109_exc", "case_bucket": "or", "source_criterion": "choroidal neovascularization caused by other eye diseases ocular surgery within the past 3 mouths history of uveitis intraocular pressure higher than 25 mmHg, or glaucoma history of systemic or ocular thromboembolic events.", "candidate_expression": "((choroidal neovascularization) AND (glaucoma) AND (higher than 25 mmHg) AND (history) AND (intraocular pressure) AND (ocular) AND (ocular surgery) AND (other) AND (other eye diseases) AND (systemic) AND (thromboembolic events) AND (uveitis) AND (within the past 3 mouths))"}
{"candidate_id": "LLM06712", "doc_id": "NCT01711801_exc", "case_bucket": "or", "source_criterion": "History or presence of any clinically significant disease or disorder Any condition or disease that would render the subject unsuitable for the study, place the subject at undue risk or interfere with the ability of the subject to complete the study in the opinion of the investigator History of clinically significant hypersensitivity or allergic drug reactions Any suspicion or history of alcohol abuse and/or consumption of other drugs of abuse Regular smoker (> 5 cigarettes, > 1 pipeful or > 1 cigar per day) Positive for hepatitis B, hepatitis C or HIV infection Dietary restrictions that would prohibit the consumption of standardized meals Participation in an investigational drug or device study within 90 days prior to screening, as calculated from the follow-up from the previous study", "candidate_expression": "((Any condition or disease that would render the subject unsuitable for the study, place the subject at undue risk or interfere with the ability of the subject to complete the study in the opinion of the investigator) AND (Dietary restrictions would prohibit the consumption of standardized meals) AND (HIV infection) AND (Regular smoker) AND (alcohol abuse) AND (allergic drug reactions) AND (cigar > 1 per day) AND (cigarettes > 5) AND (clinically significant) AND (clinically significant disease History clinically significant) AND (clinically significant disease or disorder) AND (clinically significant disorder History clinically significant) AND (consumption of other drugs of abuse) AND (hepatitis B Positive) AND (hepatitis C Positive) AND (history) AND (hypersensitivity clinically significant) AND (pipeful > 1) AND (suspicion) AND (would prohibit the consumption of standardized meals))"}
{"candidate_id": "LLM06713", "doc_id": "NCT03329456_exc", "case_bucket": "or", "source_criterion": "Exclusion criteria are pregnancy, patients with contraindications to regional anesthesia, allergy to LAs, patients taking opioids regularly due to chronic pain, use of anticoagulation drugs other than acetylsalicylic acid or dipyridamole, atrioventricular block, diabetes.", "candidate_expression": "((LAs) AND (chronic pain) AND (other than) AND (regional anesthesia) AND (regularly) AND ((acetylsalicylic acid) OR (dipyridamole)) AND ((allergy) OR (anticoagulation drugs) OR (atrioventricular block) OR (contraindications) OR (diabetes) OR (opioids) OR (pregnancy)))"}
{"candidate_id": "LLM06714", "doc_id": "NCT02542956_exc", "case_bucket": "other", "source_criterion": "A medical condition that could interfere with study participation Body weight less than 50 kg Participating in another study involving an investigational medication", "candidate_expression": "((Body weight) AND (Participating in another study involving an investigational medication) AND (less than 50 kg))"}
{"candidate_id": "LLM06715", "doc_id": "NCT02552459_inc", "case_bucket": "other", "source_criterion": "patients undergoing venous malformation embolization operation through general anesthesia. aged 18-65 years old. operating time varies 1-4h,and extubation after the operation.", "candidate_expression": "((aged 18-65 years old) AND (extubation after the operation) AND (general anesthesia) AND (operating time 1-4h) AND (operation) AND (venous malformation embolization operation))"}
{"candidate_id": "LLM06716", "doc_id": "NCT00867958_exc", "case_bucket": "or", "source_criterion": "1. Patient has an allergy to nickel. 2. Patient has a diagnosis of bowel obstruction, bowel strangulation, peritonitis, bowel perforation, local or systemic infection, ischemic bowel, carcinomatosis or extensively spread inflammatory bowel disease. 3. Patient is participating in another clinical trial which may affect this study's outcomes. 4. Patient has been taking regular steroid medication. 5. Patient has contraindications to general anesthesia. 6. Patient has preexisting sphincter problems or evidence of extensive local disease in the pelvis.", "candidate_expression": "((Patient is participating in another clinical trial which may affect this study's outcomes.) AND (allergy to nickel) AND (bowel obstruction) AND (bowel perforation) AND (bowel strangulation) AND (carcinomatosis) AND (contraindications to general anesthesia) AND (evidence of) AND (extensive) AND (extensively spread) AND (general anesthesia) AND (inflammatory bowel disease) AND (ischemic bowel) AND (local disease in the pelvis) AND (local infection) AND (nickel) AND (peritonitis) AND (regular) AND (sphincter problems) AND (steroid medication) AND (systemic infection))"}
{"candidate_id": "LLM06717", "doc_id": "NCT01518946_inc", "case_bucket": "or", "source_criterion": "1. Male and female subjects must be 18 years of age or older and ambulatory. 2. Females of child-bearing potential (FOCP) must have a negative serum beta human chorionic gonadotropin (HCG) pregnancy test. 3. A documented history of severe Symptomatic Orthostatic Hypotension (SOH) that, in the judgment of the treating physician, has required treatment with midodrine HCl , and has been at a stable dose for at least 3 months. 4. The subject has manifested at least 1 of the following symptoms while standing or had a medical history of 1 of the following when not treated for orthostatic hypotension (OH): dizziness, lightheadedness, feeling faint, or feeling like they might black out.", "candidate_expression": "((Females) AND (Male) AND (Symptomatic Orthostatic Hypotension (SOH) severe) AND (age 18 years or older) AND (ambulatory) AND (at least 1) AND (child-bearing potential) AND (dizziness) AND (feeling faint) AND (feeling like they might black out) AND (female) AND (lightheadedness) AND (midodrine HCl stable dose) AND (orthostatic hypotension (OH)) AND (serum beta human chorionic gonadotropin (HCG) pregnancy test negative) AND NOT (treated))"}
{"candidate_id": "LLM06718", "doc_id": "NCT02844907_exc", "case_bucket": "or", "source_criterion": "Rheumatoid arthritis Diabetes or immediate family history of diabetes Coronary artery disease Congestive heart failure Pulmonary disorders, including COPD and asthma Malabsorptive GI disease, such as celiac disease, or gastric bypass Significant hepatic disease Renal insufficiency (eGFR < 60 mL/kg/min) Anemia (hematocrit < 34%) as measured at screening visit Pregnant females Consumption of daily medications that alter glucose metabolism of GI function (glucocorticoids, psychotropics, narcotics, metoclopramide) Consumption or injection of insulin Apparent sensitivity to any of the study peptides as determined by the skin test Diagnosis or h/o PTSD, depression, substance use, mental health problems, sleep disorders, HPA disruption and/or TBI", "candidate_expression": "((Anemia) AND (COPD) AND (Congestive heart failure) AND (Coronary artery disease) AND (Diabetes) AND (HPA disruption) AND (Malabsorptive GI disease) AND (PTSD) AND (Pregnant) AND (Pulmonary disorders) AND (Renal insufficiency) AND (Rheumatoid arthritis) AND (TBI) AND (asthma) AND (celiac disease) AND (depression) AND (diabetes immediate family history) AND (eGFR < 60 mL/kg/min) AND (females) AND (gastric bypass) AND (glucocorticoids) AND (hematocrit < 34%) AND (hepatic disease Significant) AND (injection) AND (insulin) AND (medications daily that alter glucose metabolism of GI function) AND (mental health problems) AND (metoclopramide) AND (narcotics) AND (psychotropics) AND (screening visit) AND (sensitivity) AND (skin test) AND (sleep disorders) AND (study peptides) AND (substance use))"}
{"candidate_id": "LLM06719", "doc_id": "NCT03413891_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for dental extraction and treated with edoxaban, apixaban, rivaroxaban or dabigatran Not having taken the direct oral anticoagulant on the day of the extraction Provision of signed and dated informed consent form Stated willingness to comply with all study procedures and availability for the duration of the study", "candidate_expression": "((Not) AND (Provision of signed and dated informed consent form) AND (Stated willingness to comply with all study procedures and availability for the duration of the study) AND (anticoagulant) AND (apixaban) AND (dabigatran) AND (dental extraction) AND (edoxaban) AND (extraction) AND (on the day of the extraction) AND (oral) AND (rivaroxaban) AND (scheduled for))"}
{"candidate_id": "LLM06720", "doc_id": "NCT02946892_inc", "case_bucket": "or", "source_criterion": "Informed consent of parent(s) or legal guardian; informed consent or assent of subject as applicable. Male or female children between the ages of 10 and 35 years with congenital heart disease that has been palliated with a Fontan circulation. Ability of perform a maximal exercise test as defined by a respiratory exchange ratio (RER) greater than 1.0 at the time of maximal exercise", "candidate_expression": "((Ability of perform) AND (Fontan circulation) AND (Informed consent of legal guardian) AND (Informed consent of parent) AND (Male) AND (ages between 10 and 35 years) AND (children) AND (congenital heart disease) AND (female) AND (informed assent of subject) AND (informed consent of subject) AND (maximal exercise test) AND (respiratory exchange ratio (RER) greater than 1.0 at the time of maximal exercise))"}
{"candidate_id": "LLM06721", "doc_id": "NCT02408120_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06722", "doc_id": "NCT03416413_inc", "case_bucket": "or", "source_criterion": "Adults over 18 years of age Symptomatic GSV or SSV vein reflux > 0.5 seconds on colour Duplex Varicose vein tributary requiring treatment", "candidate_expression": "((> 0.5 seconds) AND (Adults) AND (Varicose vein tributary) AND (age) AND (colour Duplex) AND (over 18 years of age) AND (requiring) AND (treatment) AND ((GSV vein reflux) OR (SSV vein reflux)))"}
{"candidate_id": "LLM06723", "doc_id": "NCT01518946_exc", "case_bucket": "or", "source_criterion": "1. The subject is a pregnant or lactating female. 2. The subject has pre-existing sustained supine hypertension greater than 180mmHg systolic and 110mmHg diastolic BP or had these measurements at the Screening Visit. Sustained is defined as persistently greater at 2 separate measurements at least 5 minutes apart with the subject supine and at rest for the 5 minutes. 3. Subjects taking concomitant medications of interest are excluded unless those medications are reviewed and discussed with the Medical Monitor or Study Physician and documented prior to enrolling the subject. If agreement is reached between the Investigator and Sponsor for the subject to continue in the study, all allowed medications should be maintained at a constant dose throughout the study. 4. The Principal Investigator deems any clinical laboratory test (at the Screening Visit) abnormality to be clinically significant 5. The subject has participated in other studies of investigational drugs or devices within 30 days prior to enrollment in this study (other than Study SPD426-406). 6. Current or relevant history of physical or psychiatric illness, any medical disorder that may require treatment or make the subject unlikely to fully comply with the requirements of the study or complete the study, or any condition that presents undue risk from the investigational product or study procedures. 7. The subject has a concurrent chronic or acute illness, disability, or other condition (including significant unexpected laboratory or electrocardiogram [ECG] findings) that might confound the results of the tests and/or measurements administered in this study, or that might have increased the risk to the subject. 8. Known or suspected intolerance or hypersensitivity to the investigational product(s), closely-related compounds, or any of the stated ingredients. 9. Prior enrollment failure or randomization in this study. 10. History of alcohol abuse or other substance abuse within the last year.", "candidate_expression": "((110mmHg diastolic) AND (2 separate at least 5 minutes apart) AND (BP) AND (Current or relevant history of physical or psychiatric illness, any medical disorder that may require treatment or make the subject unlikely to fully comply with the requirements of the study or complete the study, or any condition that presents undue risk from the investigational product or study procedures.) AND (Screening Visit) AND (The Principal Investigator deems any clinical laboratory test (at the Screening Visit) abnormality to be clinically significant) AND (The subject has participated in other studies of investigational drugs or devices within 30 days prior to enrollment in this study (other than Study SPD426-406).) AND (concomitant) AND (electrocardiogram [ECG]) AND (electrocardiogram [ECG] findings) AND (enrollment failure) AND (female) AND (greater) AND (greater than 180mmHg systolic) AND (laboratory findings) AND (measurements) AND (medications of interest) AND (persistently) AND (pre-existing) AND (supine hypertension) AND (within the last year) AND ((lactating) OR (pregnant)) AND ((acute illness) OR (chronic illness) OR (disability) OR (other condition)) AND ((alcohol abuse) OR (substance abuse)) AND ((at the Screening Visit) OR (sustained)))"}
{"candidate_id": "LLM06724", "doc_id": "NCT01501201_inc", "case_bucket": "or", "source_criterion": "Type 2 diabetes mellitus with HbA1c > 7.5 % Body mass index > 35 and < 50 kg/m2 Candidate for Gastric By-Pass Treatment with GLP1 (glucagon-like peptide) analogue or insulin", "candidate_expression": "((Body mass index > 35 and < 50 kg/m2) AND (Gastric By-Pass Candidate) AND (HbA1c > 7.5 %) AND (Treatment) AND (Type 2 diabetes mellitus) AND ((GLP1 (glucagon-like peptide) analogue) OR (insulin)))"}
{"candidate_id": "LLM06725", "doc_id": "NCT02877485_exc", "case_bucket": "or", "source_criterion": "Intranasal steroid use within the last three months Current systemic steroid use Prior septal surgery Individuals who are pregnant or actively breastfeeding", "candidate_expression": "((Intranasal steroid use within the last three months) AND (septal surgery Prior) AND (steroid Intranasal) AND (steroid systemic) AND (systemic steroid use Current) AND ((breastfeeding actively) OR (pregnant)))"}
```
