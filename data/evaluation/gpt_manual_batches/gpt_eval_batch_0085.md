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
{"candidate_id": "LLM02101", "doc_id": "NCT03199560_exc", "case_bucket": "or", "source_criterion": "Women under the age of 18, Clinically positive axillary nodes Neoadjuvant therapy for current breast cancer diagnosis Women with previous SLNBx or axillary node dissection Pregnant women Women with previous radiation above the diaphragm, and below the neck", "candidate_expression": "((18 under) AND (Neoadjuvant therapy) AND (Pregnant women) AND (SLNBx) AND (Women) AND (above the diaphragm) AND (age) AND (axillary node dissection) AND (axillary nodes) AND (below the neck) AND (breast cancer) AND (positive) AND (previous) AND (radiation))"}
{"candidate_id": "LLM02102", "doc_id": "NCT01701219_exc", "case_bucket": "or", "source_criterion": "1. For subjects in Cohort A: previous therapy for more than 48 hours with any parenteral antibiotic with activity against S. aureus within 72 hours of positive blood culture results. 2. For subjects in Cohort B: previous therapy for more than 48 hours with any parenteral antibiotic with activity against MRSA, except vancomycin and/or daptomycin, within 72 hours of positive blood culture results confirming persistence. 3. Previous episode of S. aureus bacteremia within 3 months. 4. Known left-sided endocarditis or prosthetic heart valve. 5. Osteomyelitis or prosthetic joint infection except new onset nonhardware-associated vertebral osteomyelitis. 6. History of any hypersensitivity or allergic reaction to any β-lactam antibacterial agent. 7. Evidence of significant hepatic, hematologic, or immunologic impairment. 8. Pregnant or nursing females.", "candidate_expression": "((Cohort A) AND (Cohort B) AND (MRSA) AND (Osteomyelitis) AND (Pregnant) AND (S. aureus) AND (S. aureus S. aureus) AND (S. aureus bacteremia within 3 months) AND (allergic reaction) AND (blood culture positive results) AND (females) AND (hematologic impairment) AND (hepatic impairment) AND (hypersensitivity) AND (immunologic impairment) AND (left-sided endocarditis left-sided) AND (nursing) AND (parenteral antibiotic with activity against MRSA with activity against MRSA) AND (parenteral antibiotic with activity against S. aureus with activity against S. aureus within 72 hours of positive blood culture results) AND (prosthetic heart valve) AND (prosthetic joint infection) AND (therapy previous for more than 48 hours parenteral) AND (β-lactam antibacterial agent) AND NOT (vancomycin) AND NOT (daptomycin positive blood culture results) AND NOT (vertebral osteomyelitis new onset nonhardware-associated))"}
{"candidate_id": "LLM02103", "doc_id": "NCT01801072_exc", "case_bucket": "or", "source_criterion": "History of seizures within last 10 years History of epilepsy History of prior stroke Currently prescribed medication with anti-epileptic activity (keppra, dilantin, tegretol, lamictal, topamax, etc.) Brain tumor Pregnant or nursing woman Known levetiracetam allergy", "candidate_expression": "((Brain tumor) AND (allergy) AND (anti-epileptic activity) AND (epilepsy) AND (levetiracetam) AND (medication) AND (prior) AND (seizures) AND (stroke) AND (within last 10 years) AND (woman) AND ((Pregnant) OR (nursing)) AND ((dilantin) OR (keppra) OR (lamictal) OR (tegretol) OR (topamax)))"}
{"candidate_id": "LLM02104", "doc_id": "NCT02536976_inc", "case_bucket": "or", "source_criterion": "Aged 25-80 at screening. Subjects older than 80 will be allowed at the discretion of the PI. Ambulatory (defined as able to ambulate at least 10 meters, with or without assistance). Clinical Diagnosis of PD based on the United Kingdom Brain Bank diagnostic criteria for PD. At least 8 micturitions per 24 hours and At least 3 urgency episodes per 3-day diary. A MoCA score between 19 and 28 (inclusive) at screening. For those on cognitive enhancers (donepezil, rivastigmine, memantine, galantamine) a MoCA score between 19 and 29 (inclusive) at screening. Provide informed consent to participate in the study and understand that they may withdraw their consent at any time without prejudice to their future medical care. Be cognitively capable, in the opinion of investigator, to understand and provide such informed consent. Be cognitively capable to complete the required questionnaires and assessments, OR have a care partner who is willing and capable to assist them in the completion of these tasks. Be on a stable regimen of antiparkinson's medications at least 30 days prior to screening, and be expected to remain on a stable dose for the duration of the study. If taking cognitive enhancers (donepezil, rivastigmine, memantine, galantamine), must be on stable dose at least 30 days prior to screening, and be expected to remain on a stable dose for the duration of the study.", "candidate_expression": "((25-80) AND (Aged) AND (Ambulatory) AND (At least 3 per 3-day diary.) AND (At least 8 per 24 hours) AND (Be cognitively capable to complete the required questionnaires and assessments, OR have a care partner who is willing and capable to assist them in the completion of these tasks) AND (Be cognitively capable, in the opinion of investigator, to understand and provide such informed consent) AND (MoCA score) AND (PD) AND (Provide informed consent to participate in the study and understand that they may withdraw their consent at any time without prejudice to their future medical care) AND (United Kingdom Brain Bank diagnostic criteria) AND (antiparkinson's medications) AND (at least 30 days prior to screening) AND (between 19 and 28) AND (between 19 and 29) AND (cognitive enhancers) AND (micturitions) AND (screening) AND (stable dose) AND (urgency episodes) AND ((donepezil) OR (galantamine) OR (memantine) OR (rivastigmine)))"}
{"candidate_id": "LLM02105", "doc_id": "NCT03513757_exc", "case_bucket": "or", "source_criterion": "Inpatient status, airway abnormalities, allergy to any study medications, eggs and soy, and mitochondrial disorders. All subjects with any cardiac disease or history of cardiac arrhythmias will be excluded.", "candidate_expression": "((Inpatient status) AND (airway abnormalities) AND (allergy) AND (cardiac arrhythmias) AND (cardiac disease) AND (eggs) AND (history) AND (mitochondrial disorders) AND (soy) AND (study medications))"}
{"candidate_id": "LLM02106", "doc_id": "NCT02695992_inc", "case_bucket": "scope", "source_criterion": "Above 18 years of age Symptomatic, permanent AF of at least three months duration Resting heart rate =80 bpm Signed informed consent", "candidate_expression": "((=80 bpm) AND (AF) AND (Above 18 years) AND (Resting heart rate) AND (Signed informed consent) AND (Symptomatic) AND (age) AND (at least three months duration) AND (permanent))"}
{"candidate_id": "LLM02107", "doc_id": "NCT00846703_inc", "case_bucket": "or", "source_criterion": "Cytologically proven acute lymphoblastic leukemia (ALL) No relapse of a previously unrecognized ALL Patients must meet one of the following risk criteria: Standard-risk (SR) group meeting all of the following criteria: Blasts < 1,000/µL in peripheral blood (PB) on day 8 Aged 1 to < 6 years Initial WBC < 20,000/µL M1 (5%) or M2 (= 5% to < 25%) blasts in bone marrow on day 15; M1 marrow on day 33. Aged < 1 or = 6 years and/or WBC = 20,000/µL Blasts < 1,000/µL in PB on day 8 M1 or M2 marrow on day 15 M3 (= 25%) marrow on day 15 OR meets SR criteria but M3 marrow on day 15 and *M1 marrow on day 33. Meets IR criteria and M3 marrow on day 15 (not SR and M3 on day 15) Blasts = 1,000/µL in PB on day 8 M2 or M3 marrow on day 33 Translocation t(9;22) [BCR/ABL+] (Philadelphia chromosome-positive) or t(4;11) [MLL/AF4+].", "candidate_expression": "((ALL) AND (ALL previously unrecognized) AND (Aged 1 to < 6 years PB) AND (Blasts < 1,000/µL on day 8) AND (Blasts = 1,000/µL PB on day 8) AND (Blasts peripheral blood on day 8 < 1,000/µL) AND (IR criteria Meets) AND (M1 marrow on day 33) AND (M3 marrow = 25% on day 15) AND (M3 marrow on day 15) AND (M3 on day 15) AND (PB) AND (Philadelphia chromosome positive) AND (SR) AND (SR criteria meets) AND (SR not) AND (Standard-risk) AND (Translocation t(9;22)) AND (WBC Initial < 20,000/µL) AND (acute lymphoblastic leukemia Cytologically proven) AND (criteria all) AND (t(4;11)) AND NOT (relapse) AND ((M1 blasts (5%) OR (M2 blasts = 5% to < 25%)) AND ((Aged < 1 or = 6 years) OR (WBC = 20,000/µL)) AND ((M1 marrow) OR (M2 marrow)) AND ((M2 marrow) OR (M3 marrow)) AND ((BCR/ABL +) OR (MLL/AF4 +)))"}
{"candidate_id": "LLM02108", "doc_id": "NCT01944800_inc", "case_bucket": "or", "source_criterion": "intolerance of or allergy to ticagrelor or prasugrel history of any stroke, transient ischemic attack or intracranial bleeding known intracranial neoplasm, intracranial arteriovenous malformation or intracranial aneurysm active bleeding, clinical findings, that in the judgement of the investigator are associated with an increased risk of bleeding fibrin-specific fibrinolytic therapy less than 24 h before randomization, non-fibrin-specific fibrinolytic therapy less than 48 h before randomization known platelet count < 100.000/µL at the time of screening known anemia (hemoglobin <10 g/dL) at the time of screening oral anticoagulation that cannot be safely discontinued for the duration of the study INR known to be greater than 1.5 at the time of screening chronic renal insufficiency requiring dialysis moderate or severe hepatic dysfunction (Child Pugh B or C) increased risk of bradycardia events (Sick Sinus, AV block grade II or III, bradycardia-induced syncope) index event is an acute complication (< 30 days) of PCI concomitant medical illness that in the opinion of the investigator is associated with a life expectancy < 1 year concomitant oral or i.v. therapy with strong CYP3A Inhibitors (e.g. ketoconazole, itraconazole, voriconazole, telithromycin, clarithromycin, nefazodone, ritonavir, saquinavir, nelfinavir, indinavir, atazanavir, grapefruit juice > 1 L/d), CYP3A substrates with narrow therapeutic indices (e.g. cyclosporine, quinidine), or strong CYP3A inducers (e.g. rifampin/rifampicin, phenytoin, carbamazepine, dexamethason, phenobarbital ) that cannot be safely discontinued =1 doses of ticagrelor or prasugrel within 5 days before randomisation no written informed consent participation in another investigational drug study previous enrolment in this study for women of childbearing potential no negative pregnancy test and no agree to use reliable method of birth control during the study Pregnancy, giving birth within the last 90 days, or lactation inability to cooperate with protocol requirements", "candidate_expression": "((AV block) AND (CYP3A substrates with narrow therapeutic indices) AND (Child Pugh B or C) AND (INR greater than 1.5 at the time of screening) AND (Pregnancy, giving birth within the last 90 days, or lactation) AND (Sick Sinus) AND (allergy) AND (anemia at the time of screening) AND (atazanavir) AND (bleeding) AND (bradycardia events increased risk) AND (bradycardia-induced syncope) AND (carbamazepine) AND (chronic renal insufficiency) AND (clarithromycin) AND (clinical findings, that in the judgement of the investigator are associated with an increased risk of bleeding) AND (complication of PCI acute < 30 days) AND (concomitant medical illness is associated with a life expectancy < 1 year) AND (cyclosporine) AND (dexamethason) AND (dialysis moderate severe) AND (fibrinolytic therapy fibrin-specific less than 24 h before randomization) AND (fibrinolytic therapy non-fibrin-specific less than 48 h before randomization) AND (for women of childbearing potential no negative pregnancy test and no agree to use reliable method of birth control during the study) AND (grade II or III) AND (grapefruit juice > 1 L/d) AND (hemoglobin <10 g/dL) AND (hepatic dysfunction) AND (i.v. therapy) AND (indinavir) AND (intolerance) AND (intracranial aneurysm) AND (intracranial arteriovenous malformation) AND (intracranial bleeding) AND (intracranial neoplasm) AND (itraconazole) AND (ketoconazole) AND (nefazodone) AND (nelfinavir) AND (oral anticoagulation cannot be safely discontinued for the duration of the study) AND (oral therapy) AND (participation in another investigational drug study) AND (phenobarbital) AND (phenytoin) AND (platelet count < 100.000/µL at the time of screening) AND (prasugrel) AND (prasugrel within 5 days before randomisation) AND (quinidine) AND (rifampicin) AND (rifampin) AND (ritonavir) AND (saquinavir) AND (stroke) AND (strong CYP3A Inhibitors) AND (strong CYP3A inducers) AND (telithromycin) AND (ticagrelor) AND (transient ischemic attack) AND (voriconazole))"}
{"candidate_id": "LLM02109", "doc_id": "NCT03149887_exc", "case_bucket": "or", "source_criterion": "Pregnancy, coagulopathy, allergy to bupivacaine, renal failure, hepatic insufficiency, and/or inappropriate candidate for usual therapy (specifically, if unable to receive the usual preoperative interscalene nerve block: preexisting nerve injury on side of surgery, refusal of nerve block, infection at site of nerve block).", "candidate_expression": "((Pregnancy) AND (allergy) AND (bupivacaine) AND (coagulopathy) AND (hepatic insufficiency) AND (inappropriate candidate) AND (infection site of nerve block) AND (nerve injury preexisting side of surgery) AND (preoperative interscalene nerve block unable to receive) AND (refusal of nerve block) AND (renal failure) AND (usual therapy))"}
{"candidate_id": "LLM02110", "doc_id": "NCT02903407_inc", "case_bucket": "other", "source_criterion": "All patients admitted to the Duke CICU, who require intubation and sedation for mechanical ventilation that is expected to be >24 hours in duration will be included, unless they meet the specified exclusion criteria. Patients intubated within one hour prior to care transition to the CICU will also be screened for inclusion.", "candidate_expression": "((Duke CICU) AND (admitted) AND (care transition) AND (intubated within one hour prior to care transition) AND (intubation) AND (mechanical ventilation >24 hours in duration) AND (sedation))"}
{"candidate_id": "LLM02111", "doc_id": "NCT02695992_inc", "case_bucket": "scope", "source_criterion": "Above 18 years of age Symptomatic, permanent AF of at least three months duration Resting heart rate =80 bpm Signed informed consent", "candidate_expression": "((=80 bpm) AND (AF) AND (Above 18 years) AND (Resting heart rate) AND (Signed informed consent) AND (Symptomatic) AND (age) AND (at least three months duration) AND (permanent))"}
{"candidate_id": "LLM02112", "doc_id": "NCT02473809_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes Treatment with insulin Body weight > 140 kg HbA1c > 75 mmol/mol Treatment with GLP-1 analogues, Dipeptidyl peptidase-4 inhibitors, or glitazones Chronic kidney disease Hepatic disease Pancreatitis Inflammatory bowel disease Osteoporosis Family or personal history of medullary thyroid carcinoma Treatment with glucocorticoids Hormone replacement therapy Diabetic gastroparesis Pregnancy or lactation", "candidate_expression": "((> 140 kg) AND (> 75 mmol/mol) AND (Body weight) AND (Chronic kidney disease) AND (Diabetic gastroparesis) AND (HbA1c) AND (Hepatic disease) AND (Hormone replacement therapy) AND (Inflammatory bowel disease) AND (Osteoporosis) AND (Pancreatitis) AND (Treatment) AND (Type 1 diabetes) AND (glucocorticoids) AND (insulin) AND (medullary thyroid carcinoma) AND ((Family) OR (personal history)) AND ((Pregnancy) OR (lactation)) AND ((Dipeptidyl peptidase-4 inhibitors) OR (GLP-1 analogues) OR (glitazones)))"}
{"candidate_id": "LLM02113", "doc_id": "NCT02876484_exc", "case_bucket": "or", "source_criterion": "Fasting plasma glucose > 7,0 mM, HbA1c > 48 mmol/mol 3 months after RYGB. Dysregulated thyroid diseases, use of antithyroid treatment. Late diabetic complications as retinopathy, renal insufficiency, neuropathy or previous pancreatitis. Complications to RYGB. Documented reactive hypoglycaemia, severe dumping (vomiting, diarrhea, severe abdominal pain after food intake). Cholecystectomy", "candidate_expression": "((3 months after RYGB) AND (> 48 mmol/mol) AND (> 7,0 mM) AND (Cholecystectomy) AND (Complications) AND (Dysregulated) AND (Fasting plasma glucose) AND (HbA1c) AND (Late diabetic complications) AND (RYGB) AND (abdominal pain) AND (after food intake) AND (antithyroid treatment) AND (diarrhea) AND (dumping) AND (food intake) AND (neuropathy) AND (pancreatitis) AND (previous) AND (reactive hypoglycaemia) AND (renal insufficiency) AND (retinopathy) AND (severe) AND (thyroid diseases) AND (vomiting))"}
{"candidate_id": "LLM02114", "doc_id": "NCT03506477_inc", "case_bucket": "or", "source_criterion": "Provide written, signed and dated informed consent prior to initiating any study-related activities. Male or female >18 years of age at the time of screening Fitzpatrick Skin phototype IV-VI, non-white race/ethnicity, including but not limited to - --African Americans, Asians, Pacific Islanders and Hispanics. Clinical diagnosis of chronic plaque-type psoriasis of the body Plaque psoriasis with =2% Body Surface Area (BSA) involvement (may include scalp involvement), PASI Score = 2, IGA mod 2011 score of 2 or greater (based on scale of 0-4) Females of childbearing potential (FCBP) must have a negative pregnancy test at Screening and Baseline. While using investigational product and for at least 28 days after last application of investigational product, FCBP who engage in activity in which conception is possible must use one of the approved contraceptive options d Must be in general good health as judged by the Investigator, based on medical history and physical examination.", "candidate_expression": "((2 or greater) AND (= 2) AND (=2% Body Surface Area (BSA)) AND (>18 years of age) AND (Females of childbearing potential (FCBP) must have a negative pregnancy test at Screening and Baseline. While using investigational product and for at least 28 days after last application of investigational product, FCBP who engage in activity in which conception is possible must use one of the approved contraceptive options d) AND (Fitzpatrick Skin phototype) AND (IV-VI) AND (Plaque psoriasis) AND (Provide written, signed and dated informed consent prior to initiating any study-related activities.) AND (age) AND (at the time of screening) AND (chronic) AND (involvement) AND (non-white race/ethnicity) AND (plaque-type) AND (psoriasis of the body) AND (scale of 0-4) AND (the time of screening) AND ((African Americans) OR (Asians) OR (Hispanics) OR (Pacific Islanders)) AND ((Male) OR (female)) AND ((IGA mod 2011 score) OR (PASI Score)))"}
{"candidate_id": "LLM02115", "doc_id": "NCT02766530_exc", "case_bucket": "or", "source_criterion": "Estimated GFR (eGFR) < 60 mL/min/1.73 m2 and blood glucose > 135 mg/dl; Past or present history of acute renal failure, renal dialysis, diabetes mellitus. Women who received metallic fixation, coronary artery stent in recent 3 months; or women who received mechanical valve replacement that is not compatible with MR magnet; or women with aneurysmal clips, pacemakers. Past history of claustrophobia. Women who are pregnant or who are planning to be pregnant, or who are lactating (though the possibility in our target population should be very low) Past history of breast cancer within recent 5 years before the currently diagnosed breast cancer. Women who received chemotherapy for other disease entity in recent 1 year. Women who cannot cooperate with the examinations.", "candidate_expression": "((< 60 mL/min/1.73 m2) AND (> 135 mg/dl) AND (Estimated GFR) AND (Women) AND (Women who are pregnant or who are planning to be pregnant, or who are lactating (though the possibility in our target population should be very low)) AND (Women who cannot cooperate with the examinations) AND (acute renal failure) AND (aneurysmal clips) AND (blood glucose) AND (breast cancer) AND (chemotherapy) AND (claustrophobia) AND (coronary artery stent) AND (currently diagnosed breast cancer.) AND (diabetes mellitus) AND (eGFR) AND (mechanical valve replacement) AND (metallic fixation) AND (pacemakers) AND (recent 1 year) AND (recent 3 months) AND (recent 5 years before the currently diagnosed breast cancer) AND (renal dialysis) AND (women))"}
{"candidate_id": "LLM02116", "doc_id": "NCT02621489_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes (autoantibody positive). Any history of receiving GLP-1 analogues or dipeptidyl peptidase inhibitors within 6 months Known severe heart failure, classified as NYHA 4. Active myocarditis; malfunctioning artificial heart valve. History of ventricular tachycardia within 3 months before study entry; second- or third-degree atrioventricular block. Supine systolic blood pressure <85 mm Hg or >200 mm Hg at screening. Primary renal impairment, creatinine clearance < 45 ml/min if treated with metformin. Uncorrected hypokalemia or hyperkalemia (potassium <3.5 mmol/l or >5.5 mmol/l). Significant anemia (Hb < 90 g/l) Severe gastrointestinal disease, including gastroparesis. As judged by the Investigator. Body mass index (BMI) > 45 kg/m2. Malignant neoplasm requiring chemotherapy, surgery, radiation or palliative therapy in the previous 5 years. Patients with intraepithelial squamous cell carcinoma of the skin treated with topical 5FU and subjects with basal cell skin cancer are allowed to enter the trial. Females of child bearing potential who are pregnant, breast-feeding or intend to become pregnant. Current drug and alcohol abuse. History of acute or chronic pancreatitis Subjects considered by the Investigator to be unsuitable for the study.", "candidate_expression": "((4) AND (< 45 ml/min) AND (< 90 g/l) AND (> 45 kg/m2) AND (BMI) AND (Body mass index) AND (Females of child bearing potential who are pregnant, breast-feeding or intend to become pregnant) AND (Hb) AND (Malignant neoplasm) AND (NYHA) AND (Primary renal impairment) AND (Severe) AND (Significant) AND (Supine) AND (Type 1 diabetes) AND (allowed) AND (anemia) AND (autoantibody) AND (creatinine clearance) AND (gastrointestinal disease) AND (gastroparesis) AND (heart failure) AND (malfunctioning) AND (metformin) AND (positive) AND (potassium) AND (previous 5 years.) AND (severe) AND (skin) AND (systolic blood pressure) AND (topical 5FU) AND (within 3 months) AND (within 6 months) AND ((Active myocarditis) OR (artificial heart valve)) AND ((second- degree atrioventricular block) OR (third-degree atrioventricular block) OR (ventricular tachycardia)) AND ((<85 mm Hg) OR (>200 mm Hg)) AND ((hyperkalemia) OR (hypokalemia)) AND ((<3.5 mmol/l) OR (>5.5 mmol/l)) AND ((GLP-1 analogues) OR (dipeptidyl peptidase inhibitors)) AND ((chemotherapy) OR (palliative therapy) OR (radiation) OR (surgery)) AND ((basal cell skin cancer) OR (intraepithelial squamous cell carcinoma)) AND ((alcohol abuse) OR (drug abuse)) AND ((acute pancreatitis) OR (chronic pancreatitis)))"}
{"candidate_id": "LLM02117", "doc_id": "NCT02267616_inc", "case_bucket": "other", "source_criterion": "Women age 18-45 Within 6 months of expiration or beyond the end of the FDA-approved duration of use of the levonorgestrel intrauterine device (LNG-IUD = 5 years) OR the etonogestrel-releasing subdermal implant (ENG implant = 3 years) Able to consent in English or Spanish. Not pregnant at the time of enrollment", "candidate_expression": "((18-45) AND (Able to consent in English or Spanish) AND (Not) AND (Women) AND (age) AND (at the time of enrollment) AND (pregnant))"}
{"candidate_id": "LLM02118", "doc_id": "NCT03360981_exc", "case_bucket": "or", "source_criterion": "acute myocardial infarction, heart failure, neoplastic disease, chronic diseases that may affect the inflammatory profile both systemic and epicardial (cancer, chronic intestinal inflammation, hepatitis, AIDS); life expectancy < 6 months, previous CABG and/or other open heart surgery intervention, acute coronary syndrome", "candidate_expression": "((chronic diseases may affect the inflammatory profile) AND ((AIDS) OR (cancer) OR (chronic intestinal inflammation) OR (hepatitis)) AND ((CABG previous) OR (acute coronary syndrome) OR (acute myocardial infarction) OR (heart failure) OR (life expectancy < 6 months) OR (neoplastic disease) OR (open heart surgery intervention other)) AND ((epicardial) OR (systemic)))"}
{"candidate_id": "LLM02119", "doc_id": "NCT01184638_inc", "case_bucket": "or", "source_criterion": "Patients with informed consents Without basal disorders of neurology and psychiatrics", "candidate_expression": "((Patients with informed consents) AND (Without) AND ((basal disorders of neurology) OR (basal disorders of psychiatrics)))"}
{"candidate_id": "LLM02120", "doc_id": "NCT01884337_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant or breastfeeding Known or suspected, acquired or bleeding or coagulation disorder in the subject or a first degree relative Active bleeding or at high risk for bleeding. Brain, spinal, ophthalmologic, or major surgery or trauma within the past 90 days other than the elective knee/hip surgery Active hepatobiliary disease Hemoglobin <9 g/dL Platelet count <100,000/mm3 Creatinine clearance <30 mL/min", "candidate_expression": "((Creatinine clearance <30 mL/min) AND (Hemoglobin <9 g/dL) AND (Platelet count <100,000/mm3) AND (Women) AND (hepatobiliary disease Active) AND ((first degree relative) OR (in the subject)) AND ((bleeding Active) OR (bleeding at high risk for)) AND ((surgery) OR (trauma)) AND ((Brain) OR (major) OR (ophthalmologic) OR (spinal)) AND ((elective hip surgery) OR (elective knee surgery)) AND ((breastfeeding) OR (pregnant)) AND ((Known) OR (suspected)) AND ((acquired disorder) OR (bleeding disorder) OR (coagulation disorder)))"}
{"candidate_id": "LLM02121", "doc_id": "NCT02483715_inc", "case_bucket": "other", "source_criterion": "Participants having H. pylori related chronic gastritis with/without peptic ulcers who are aged greater than 20 years old and are willing to received eradication therapy.", "candidate_expression": "((aged greater than 20 years old) AND (chronic gastritis H. pylori related) AND (eradication therapy willing to receive) AND (peptic ulcers))"}
{"candidate_id": "LLM02122", "doc_id": "NCT02350439_inc", "case_bucket": "scope", "source_criterion": "1. Age 18-80 years 2. Patients with at least 1 ≥50% stenosis in a coronary vessel, subjected to FFR assessment, who exhibit variation in Pd / Pa ratio ≥ 0.05 (e.g. difference of max Pd/Pa minus min Pd/Pa) during steady state hyperaemia (determined by visual assessment). 3. Written informed consent", "candidate_expression": "((18-80 years) AND (Age) AND (FFR assessment) AND (Pd / Pa ratio) AND (at least 1) AND (hyperaemia) AND (max Pd/Pa) AND (min Pd/Pa) AND (steady state) AND (stenosis in a coronary vessel) AND (variation in Pd / Pa ratio) AND (visual assessment) AND (≥ 0.05) AND (≥50%))"}
{"candidate_id": "LLM02123", "doc_id": "NCT02593409_exc", "case_bucket": "or", "source_criterion": "HIV infection at screening participation in previous or concurrent HIV vaccine trials lactating, pregnant or planning pregnancy renal function impairment (serum creatinine >1.5 mg/dl), Fanconi syndrome abnormal liver function tests (AST/ALT > 43 U/L), liver disease, viral hepatitis, hepatitis B virus (HBV) infection serum phosphorus <2.2mg/dl, osteoporosis known sensitivity to components of the Truvada® formulation any immunosuppressive treatment, such as systemic corticosteroids assumption of medication that interacts with Truvada® high likelihood of poor adherence to PREP and clinic attendance any condition that in the opinion of the attending physician could endanger the health of the participant or render her unsuitable to participate in the trial", "candidate_expression": "((Fanconi syndrome) AND (HIV infection) AND (Truvada) AND (actating, pregnant or planning pregnancy) AND (high likelihood of poor adherence to PREP and clinic attendanc) AND (immunosuppressive treatment) AND (osteoporosis) AND (participation in previous or concurrent HIV vaccine trials) AND (renal function impairment) AND (sensitivity) AND (serum creatinine >1.5 mg/dl) AND (serum phosphorus <2.2mg/dl) AND (systemic corticosteroids) AND ((ALT) OR (AST)) AND ((hepatitis B virus (HBV) infection) OR (liver disease) OR (liver function tests abnormal) OR (viral hepatitis)))"}
{"candidate_id": "LLM02124", "doc_id": "NCT02944604_inc", "case_bucket": "or", "source_criterion": "Severe or uncontrolled infection. Sensitive to the product or other genetically engineered biological products from Escherichia coli strains. Mental or nervous system disorders. Severe heart, lung and central nervous system disorders. Pregnant or lactating women. TBIL(total bilirubin ), ALT(alanine aminotransferase),AST(glutamic-oxalacetic transaminase) > 2.5×ULN(upper limit of normal); if it were caused by liver metastases, TBIL, ALT,AST >5×ULN. Cr(creatinine) >1.5×ULN.", "candidate_expression": "((Cr >1.5×ULN) AND (Sensitive) AND (alanine aminotransferase) AND (creatinine) AND (genetically engineered biological products Escherichia coli strains) AND (glutamic-oxalacetic transaminase) AND (infection) AND (liver metastases) AND (the product other) AND (total bilirubin) AND (women) AND ((Severe) OR (uncontrolled)) AND ((Mental disorders) OR (nervous system disorders)) AND ((entral nervous system disorders) OR (heart disorders) OR (lung disorders)) AND ((Pregnant) OR (lactating)) AND ((ALT > 2.5×ULN) OR (AST > 2.5×ULN) OR (TBIL > 2.5×ULN)) AND ((ALT >5×ULN) OR (AST >5×ULN) OR (TBIL >5×ULN)))"}
{"candidate_id": "LLM02125", "doc_id": "NCT02055053_inc", "case_bucket": "or", "source_criterion": "Age 18 or older with unilateral or bilateral inguinal herna for laparoscopic repair American Society of Anesthesiology (ASA) Class I and II", "candidate_expression": "((Age 18 or older unilateral) AND (American Society of Anesthesiology (ASA) Class I and II) AND (inguinal herna for laparoscopic repair bilateral) AND (laparoscopic repair))"}
```
