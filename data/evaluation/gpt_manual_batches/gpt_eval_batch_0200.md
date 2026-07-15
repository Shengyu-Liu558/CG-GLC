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
{"candidate_id": "LLM04976", "doc_id": "NCT02535299_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes mellitus,presence of autoimmune diabetes indicated by antibodies to insulin, islet cells, and GAD; Gestational diabetes; patients with heart, liver, or renal function impairment;presence of severe infections or cerebrovascular disease;", "candidate_expression": "((Gestational diabetes) AND (Type 1 diabetes mellitus) AND (antibodies) AND (autoimmune diabetes) AND (severe) AND ((heart function impairment) OR (liver function impairment) OR (renal function impairment)) AND ((cerebrovascular disease) OR (infections)) AND ((GAD) OR (insulin) OR (islet cells)))"}
{"candidate_id": "LLM04977", "doc_id": "NCT02283905_inc", "case_bucket": "scope", "source_criterion": "All adult patients 18 years of age or older admitted to the intensive care units of St. Boniface General Hospital with a diagnosis of acute pulmonary blastomycosis requiring mechanical ventilation.", "candidate_expression": "((18 years or older) AND (St. Boniface General Hospital) AND (acute pulmonary blastomycosis) AND (admitted) AND (adult) AND (age) AND (intensive care units) AND (mechanical ventilation))"}
{"candidate_id": "LLM04978", "doc_id": "NCT02763007_inc", "case_bucket": "or", "source_criterion": "Completed \"ALO-IIT-012(PEAK study)\", without major protocol deviations. Male, or female, 19 years to 75 years. Female with childbearing potential who has a negative urine pregnancy test result at study start and willing to continue practice appropriate birth control during the entire duration of study Subjects completed PEAK can be included within 30 days after End Of the Study Subjects completed PEAK can be included if their treatment is the same as randomized even after 30 days of End Of the Study.", "candidate_expression": "((19 years to 75) AND (Completed \"ALO-IIT-012(PEAK study)\", without major protocol deviations) AND (Female with childbearing potential who has a negative urine pregnancy test result at study start and willing to continue practice appropriate birth control during the entire duration of study) AND (Subjects completed PEAK can be included if their treatment is the same as randomized even after 30 days of End Of the Study) AND (Subjects completed PEAK can be included within 30 days after End Of the Study) AND (years) AND ((Male) OR (female)))"}
{"candidate_id": "LLM04979", "doc_id": "NCT03318393_exc", "case_bucket": "or", "source_criterion": "Patients with known or suspected heparin induced thrombocytopenia prior to consent Patients with hepatic failure defined as coagulopathy with elevated transaminases more than three times normal values Patients with plan to decannulate from ECMO within 48 hours Known or suspected pregnant women Previous enrollment in this study Primary language spoken that is not English or Spanish", "candidate_expression": "((Known) AND (Previous enrollment in this study) AND (coagulopathy) AND (consent) AND (decannulate from ECMO) AND (elevated more than three times normal values) AND (heparin) AND (heparin induced) AND (hepatic failure) AND (known) AND (pregnant) AND (prior to consent) AND (suspected) AND (thrombocytopenia) AND (transaminases) AND (within 48 hours) AND (women))"}
{"candidate_id": "LLM04980", "doc_id": "NCT03241368_inc", "case_bucket": "or", "source_criterion": "Subject has provided informed consent. Subject is ≥ 18 years of age Subject is willing and able to comply with all aspects of treatment and evaluation schedule. Subject has known CD and a recent history (within last 2 years) of mucosal disease (diagnosis based on radiologic, endoscopic, or histological evidence).", "candidate_expression": "((age) AND (mucosal disease) AND (recent history) AND (within last 2 years) AND (≥ 18 years) AND ((endoscopic evidence) OR (histological evidence) OR (radiologic evidence)))"}
{"candidate_id": "LLM04981", "doc_id": "NCT02298504_inc", "case_bucket": "other", "source_criterion": "Pediatric patients with deep dental decay in primary molars Teeth with signs and symptoms of reversible pulpitis", "candidate_expression": "((Pediatric) AND (Teeth) AND (deep dental decay) AND (primary molars) AND (reversible pulpitis))"}
{"candidate_id": "LLM04982", "doc_id": "NCT02566863_inc", "case_bucket": "other", "source_criterion": "patients classified with American Society of Anesthesiologists Physical Status Classification System as 1 or 2 status planned eye surgery under sedation", "candidate_expression": "((eye surgery planned under sedation) AND (sedation) AND (status American Society of Anesthesiologists Physical Status Classification System 1 or 2))"}
{"candidate_id": "LLM04983", "doc_id": "NCT03473132_inc", "case_bucket": "other", "source_criterion": "LVAD on warfarin requiring temporary interruption of anticoagulation for procedures", "candidate_expression": "((LVAD) AND (warfarin requiring temporary interruption of anticoagulation for procedures))"}
{"candidate_id": "LLM04984", "doc_id": "NCT01912651_exc", "case_bucket": "or", "source_criterion": "current or recent (within one week of surgery) systemic antibiotic use, intolerance to both clindamycin and cephalexin, discovery of a persistent cutaneous malignancy at the site of the defect following the reconstructive procedure and previous reconstruction at the site of the skin/soft-tissue defect.", "candidate_expression": "((antibiotic) AND (cephalexin) AND (clindamycin) AND (current) AND (following the reconstructive procedure) AND (intolerance) AND (persistent cutaneous malignancy) AND (recent) AND (reconstructive procedure) AND (site of the defect) AND (the reconstructive procedure) AND (within one week of surgery))"}
{"candidate_id": "LLM04985", "doc_id": "NCT02735577_exc", "case_bucket": "or", "source_criterion": "Risk of severe alcohol withdrawal (e.g. history of seizures or delirium tremens) Current Moderate or Severe Substance Use Disorder, other than Alcohol, Nicotine or Caffeine Use Disorders Lifetime history of Bipolar Disorder, Schizophrenia or Schizoaffective Disorder Any current psychiatric disorder, other than Alcohol Use Disorder, that, in the judgment of the investigator, will require treatment that will interfere with study participation. Current severe depression (HAM-D >24) or anxiety (HAM-A >24) Significant suicide or violence risk Currently taking any psychotropic medications Legally mandated to participate in treatment History of prior treatment with disulfiram Sufficiently socially unstable as to preclude participation (e.g. homeless) Contraindications to disulfiram treatment (liver disease, kidney disease, cardiac disease, seizure disorder, hypothyroidism, diabetes mellitus, pregnancy or lactation, allergy to disulfiram or thiuran derivatives) Neurological or medical conditions that would interfere with MRI scanning (e.g. history of stroke, seizure, brain tumor, brain infection, traumatic brain injury, multiple sclerosis, dementia, metal device in body, pregnancy, claustrophobia, color blindness, severe hearing impairment, weight>300 lbs., wheelchair-bound) Currently taking medications containing alcohol, metronidazole, isoniazid, paraldehyde, phenytoin, warfarin, or theophylline. Significant alcohol withdrawal (CIWA>8) at screening, after confirming a blood alcohol level of zero.", "candidate_expression": "((CIWA >8) AND (Contraindications) AND (HAM-A >24) AND (HAM-D >24 severe) AND (MRI scanning) AND (Substance Use Disorder Current) AND (alcohol withdrawal Risk of severe) AND (alcohol withdrawal Significant at screening) AND (blood alcohol level zero) AND (brain infection) AND (brain tumor) AND (claustrophobia) AND (color blindness) AND (dementia) AND (disulfiram) AND (disulfiram History of prior treatment) AND (hearing impairment severe) AND (interfere) AND (metal device in body) AND (multiple sclerosis) AND (pregnancy) AND (psychiatric disorder current) AND (psychotropic medications Currently) AND (seizure) AND (socially unstable Sufficiently) AND (stroke) AND (traumatic brain injury) AND (weight >300 lbs.) AND (wheelchair-bound) AND NOT (Alcohol Use Disorder) AND ((Alcohol Use Disorders) OR (Caffeine Use Disorders) OR (Nicotine Use Disorders)) AND ((Bipolar Disorder) OR (Schizoaffective Disorder) OR (Schizophrenia)) AND ((anxiety) OR (depression severe)) AND ((suicide risk) OR (violence risk)) AND ((allergy) OR (cardiac disease) OR (diabetes mellitus) OR (hypothyroidism) OR (kidney disease) OR (lactation) OR (liver disease) OR (pregnancy) OR (seizure disorder)) AND ((delirium tremens) OR (seizures)) AND ((disulfiram) OR (thiuran derivatives)) AND ((conditions Neurological) OR (medical conditions)) AND ((alcohol) OR (isoniazid) OR (metronidazole) OR (paraldehyde) OR (phenytoin) OR (theophylline) OR (warfarin)) AND ((Moderate) OR (Severe)))"}
{"candidate_id": "LLM04986", "doc_id": "NCT02121145_inc", "case_bucket": "or", "source_criterion": "Male or female subjects aged =18 to =65 years General good health as established by medical history and physical examination Written informed consent Females of childbearing potential must agree to use an efficacious hormonal or barrier method of birth control during the study. Abstinence is acceptable. Available for all visits scheduled in this study.", "candidate_expression": "((=18 to =65 years) AND (Available for all visits) AND (Females) AND (General good health) AND (Written informed consent) AND (aged) AND (agree to use) AND (childbearing potential) AND (during the study) AND (efficacious) AND (established by medical history) AND (physical examination) AND (scheduled in this study) AND ((Male) OR (female)) AND ((barrier method) OR (hormonal method)) AND ((Abstinence) OR (birth control)))"}
{"candidate_id": "LLM04987", "doc_id": "NCT02939209_inc", "case_bucket": "scope", "source_criterion": "Age 18-65 scheduled to receive ISB and general anesthesia as a day surgery patient for rotator cuff repair and acromioplasty, as a part of planned routine care", "candidate_expression": "((Age 18-65) AND (ISB) AND (acromioplasty) AND (general anesthesia) AND (rotator cuff repair))"}
{"candidate_id": "LLM04988", "doc_id": "NCT02904785_exc", "case_bucket": "or", "source_criterion": "History of spinal cord stenosis or clinical symptoms of lumbar radiculopathy; History or onset neurological diseases; Generalized pain or fibromyalgia; Inability to walk; History of knee surgery in the target knee; Secondary causes of osteoarthritis; Use of statins and quinolones in the previous year; Uncontrolled and ongoing psychiatric diseases; Invasive knee treatments with hyaluronic acid infusion, corticosteroids and anaesthetics, in the target knee, up to 6 months previous to study inclusion.", "candidate_expression": "((History) AND (Inability to walk) AND (Invasive knee treatments) AND (Secondary causes) AND (Uncontrolled) AND (anaesthetics) AND (corticosteroids) AND (hyaluronic acid) AND (hyaluronic acid infusion) AND (in the previous year) AND (knee surgery) AND (lumbar radiculopathy) AND (neurological diseases) AND (ongoing) AND (osteoarthritis) AND (psychiatric diseases) AND (quinolones) AND (statins) AND (study inclusion) AND (target knee) AND (up to 6 months previous) AND ((clinical symptoms) OR (spinal cord stenosis)) AND ((History) OR (onset)) AND ((Generalized pain) OR (fibromyalgia)))"}
{"candidate_id": "LLM04989", "doc_id": "NCT02528604_exc", "case_bucket": "or", "source_criterion": "Paroxysmal atrial fibrillation. Long-standing persistent or permanent atrial fibrillation. Previous pacemaker implantation. Previous atrial ablation. Patient is unable to take warfarin or other oral anti-coagulant medication. Patient is suffering with unstable angina in last one week. Patient has had a myocardial infarction within last two months. Patient is expecting or has had major cardiac surgery within last two months. Patient is participating in a conflicting study. Patient is unable to perform exercise testing. Patient is mentally incapacitated and cannot consent or comply with follow-up. Patient has New York Heart Association (NYHA) class III/IV heart failure. Patient has left ventricular ejection fraction (LVEF) less than 35% not secondary to tachycardia. Pregnancy. Patient suffers with other cardiac rhythm disorders. Recent coronary artery intervention or other factors suggesting clinical instability (ECG, clinical or laboratory findings).", "candidate_expression": "((LVEF) AND (NYHA) AND (New York Heart Association) AND (Paroxysmal atrial fibrillation) AND (Patient is mentally incapacitated and cannot consent or comply with follow-up) AND (Patient is participating in a conflicting study) AND (Patient is unable to perform exercise testing) AND (Pregnancy) AND (atrial ablation) AND (atrial fibrillation) AND (cardiac rhythm disorders) AND (class III/IV) AND (coronary artery intervention) AND (heart failure) AND (last one week) AND (last two months) AND (left ventricular ejection fraction) AND (less than 35%) AND (major cardiac surgery) AND (myocardial infarction) AND (not secondary to) AND (other) AND (pacemaker implantation) AND (tachycardia) AND (unable to take) AND (unstable angina) AND ((oral anti-coagulant medication) OR (warfarin)) AND ((permanent) OR (persistent)))"}
{"candidate_id": "LLM04990", "doc_id": "NCT02876484_inc", "case_bucket": "or", "source_criterion": "Uncomplicated RYGB performed minimum 3 months prior to the study. Fasting plasma glucose < 7,0 mM, HbA1c < 48 mmol/mol 3 months after RYGB", "candidate_expression": "((RYGB) AND (RYGB Uncomplicated minimum 3 months prior to the study) AND ((Fasting plasma glucose < 7,0 mM) OR (HbA1c < 48 mmol/mol 3 months after RYGB)))"}
{"candidate_id": "LLM04991", "doc_id": "NCT03068897_inc", "case_bucket": "or", "source_criterion": "Present to ED primary for management of LBP, defined as pain originating between the lower border of the scapulae and the upper gluteal folds. Flank pain, that is pain originating from tissues lateral to the paraspinal muscles, will not be included. Musculoskeletal etiology of low back. Patients with non-musculoskeletal etiologies such as urinary tract infection, ovarian cysts, or influenza like illness will be excluded. The primary clinical diagnosis, at the conclusion of the ED visit, must be a diagnosis consistent with non-traumatic, non-radicular, musculoskeletal LBP. Patient is to be discharged home. Patients admitted to the hospital are more likely to be treated with parenteral medication and therefore are not appropriate for this study. Age 18-64 Enrollment will be limited to adults younger than 65 years because of the increased risk of adverse medication effects in the elderly. Non-radicular pain. Patients will be excluded if the pain radiates below the gluteal folds in a radicular pattern. Pain duration <2 weeks (336 hours). Patients with more than two weeks of pain are at increased risk of poor pain and functional outcomes.(9) Prior to the acute attack of LBP, back pain cannot occur more frequently than once per month. Patients with more frequent back pain are at increased risk of poor pain and functional outcomes.(9) Non-traumatic LBP: no substantial and direct trauma to the back within the previous month Functionally impairing back pain: A baseline score of > 5 on the Roland-Morris Disability Questionnaire", "candidate_expression": "((Age 18-64) AND (ED) AND (LBP) AND (LBP Non-traumatic) AND (LBP non-traumatic non-radicular musculoskeletal) AND (Pain) AND (Present) AND (Roland-Morris Disability Questionnaire baseline score of > 5) AND (adults younger than 65 years) AND (adverse effects increased risk) AND (attack of LBP acute) AND (back pain Functionally impairing) AND (back pain Prior to the acute attack of LBP more frequently than once per month) AND (elderly) AND (etiologies musculoskeletal) AND (etiology Musculoskeletal low back) AND (medication) AND (no) AND (pain between the lower border of the scapulae and the upper gluteal folds) AND (pain radicular) AND (pain tissues lateral to the paraspinal muscles) AND (trauma back within the previous month) AND NOT (pain below the gluteal folds in a radicular pattern) AND NOT (Flank pain) AND ((influenza like illness) OR (ovarian cysts) OR (urinary tract infection)) AND ((duration 336 hours) OR (duration <2 weeks)) AND ((direct) OR (substantial)))"}
{"candidate_id": "LLM04992", "doc_id": "NCT02796378_exc", "case_bucket": "or", "source_criterion": "Cholesterol-lowering drugs Diabetes Mellitus Cardiovascular disease such as arrythmia, ischaemic heart disease. Musculoskeletal disorders preventing the subject to perform physical training Mental disorders preventing the subject to understand the project description.", "candidate_expression": "((Cardiovascular disease) AND (Cholesterol-lowering drugs) AND (Diabetes Mellitus) AND (Mental disorders preventing the subject to understand the project description) AND (Musculoskeletal disorders preventing the subject to perform physical training) AND ((arrythmia) OR (ischaemic heart disease)))"}
{"candidate_id": "LLM04993", "doc_id": "NCT01959425_exc", "case_bucket": "or", "source_criterion": "OAT required for reasons not related to AF (i.e., prosthetic valve, PV stenosis, previous pulmonary embolism, presence of spontaneous echo contrast [SEC] at standard echo performed at 3-months follow-up). Any cardiac surgery within the past 60 days (2 months) or valvular cardiac surgical procedure at any time (i.e., ventriculotomy, atriotomy, and valve repair or replacement and presence of a prosthetic valve) Previous myocardial infarction (MI) or a percutaneous coronary intervention PCI within the past 3 months Awaiting cardiac transplantation or other cardiac surgery within the next 365 days (12 months) Documented left atrial thrombus Significant pulmonary disease, (e.g., restrictive pulmonary disease, constrictive or COPD) or any other disease or malfunction of the lungs or respiratory system that produces chronic symptoms Significant medical problem that in the opinion of the investigator would preclude enrollment in this study Women who are pregnant (as evidenced by pregnancy test if pre-menopausal) Acute illness or active systemic infection or sepsis Unstable angina Contraindication to anticoagulation (i.e., heparin, warfarin or another commercially available anticoagulation medication) History of blood clotting or bleeding abnormalities Life expectancy less than 360 days (12 months) Uncontrolled Heart Failure or NYHA Class III or IV heart failure Enrollment in a clinical study evaluating another device or drug, within the past 6 months Unable or unwilling to comply with protocol requirements", "candidate_expression": "((2 months) AND (3-months follow-up) AND (AF) AND (Awaiting) AND (COPD) AND (Contraindication) AND (Enrollment in a clinical study evaluating another device or drug, within the past 6 months) AND (Heart Failure) AND (Life expectancy) AND (MI) AND (NYHA Class III) AND (NYHA Class IV) AND (OAT) AND (PCI) AND (PV stenosis) AND (SEC) AND (Significant) AND (Unable or unwilling to comply with protocol requirements) AND (Uncontrolled) AND (Unstable angina) AND (Women who are pregnant (as evidenced by pregnancy test if pre-menopausal)) AND (anticoagulation) AND (atriotomy) AND (bleeding abnormalities) AND (blood clotting abnormalities) AND (cardiac surgery) AND (cardiac transplantation) AND (follow-up) AND (heart failure) AND (heparin) AND (left atrial thrombus) AND (less than 12 months) AND (less than 360 days) AND (myocardial infarction) AND (not) AND (percutaneous coronary intervention) AND (prosthetic valve) AND (prosthetic valve)) AND (pulmonary disease) AND (pulmonary embolism) AND (restrictive pulmonary disease) AND (sepsis) AND (spontaneous echo contrast) AND (standard echo) AND (systemic infection) AND (valve repair) AND (valve replacement) AND (valvular cardiac surgical) AND (ventriculotomy) AND (warfarin) AND (within 12 months) AND (within the next 365 days) AND (within the past 3 months) AND (within the past 60 days))"}
{"candidate_id": "LLM04994", "doc_id": "NCT02650024_exc", "case_bucket": "or", "source_criterion": "Amiodarone P-glycoprotein (P-gp) inducers (e.g., rifampin, St. John's wort) Liver biopsy at any time showing mHAI stage 4 or higher fibrosis OR FibroScan within 12 months demonstrating liver stiffness of =9.5 kilo Pascal or AST to platelet ratio index (APRI) =2.0 and Fibrosis-4 (FIB-4) =3.25 NOTE: If APRI and FIB-4 are discordant one of the other forms of fibrosis staging must be used. Known allergy/sensitivity or any hypersensitivity to components of study drugs or their formulation. Hemochromatosis Alpha-1 antitrypsin deficiency Wilson's disease Autoimmune hepatitis Alcoholic liver disease Drug-related liver disease Severe NC confounding conditions (stroke, head injury, or developmental learning disability). Regular use of anti-inflammatory drugs. Current or recent treatment with pegylated interferon (PEG-IFN). Other active inflammatory process (major infection, malignancy, rheumatoid arthritis/autoimmune disorder) within the prior 28 days. Contraindications to magnetic resonance imaging (MRI). Bleeding diathesis, thrombocytopenia, or use of anticoagulants that would contraindicate lumbar puncture. Uncontrolled or active depression or other psychiatric disorder that in the opinion of the site investigator might preclude adherence to study requirements or impact NC functioning and assessments. Active drug or alcohol use or dependence that, in the opinion of the site investigator, would interfere with adherence to study requirements. Presence of active or acute AIDS-defining opportunistic infections within 12 weeks prior to study entry.", "candidate_expression": "((AIDS-defining opportunistic infections within 12 weeks prior to study entry active acute) AND (AST to platelet ratio index (APRI) =2.0) AND (Alcoholic liver disease) AND (Alpha-1 antitrypsin deficiency) AND (Amiodarone) AND (Autoimmune hepatitis) AND (Bleeding diathesis) AND (Contraindications) AND (Drug-related liver disease) AND (FibroScan within 12 months) AND (Fibrosis-4 (FIB-4) =3.25) AND (Hemochromatosis) AND (Liver biopsy any time) AND (NC confounding conditions) AND (P-glycoprotein (P-gp) inducers) AND (PEG-IFN) AND (St. John's wort) AND (Wilson's disease) AND (active inflammatory process Other within the prior 28 days) AND (alcohol use or dependence) AND (allergy) AND (anti-inflammatory drugs Current recent) AND (anticoagulants) AND (autoimmune disorder) AND (components of study drugs) AND (contraindicate) AND (depression active) AND (developmental learning disability) AND (drug use or dependence) AND (head injury) AND (hypersensitivity) AND (liver stiffness =9.5 kilo Pascal) AND (lumbar puncture Uncontrolled) AND (mHAI stage 4 or higher) AND (magnetic resonance imaging (MRI)) AND (major infection) AND (malignancy) AND (pegylated interferon) AND (psychiatric disorder other) AND (rheumatoid arthritis) AND (rifampin) AND (sensitivity) AND (stroke) AND (thrombocytopenia) AND (treatment))"}
{"candidate_id": "LLM04995", "doc_id": "NCT02441179_exc", "case_bucket": "or", "source_criterion": "1. Orthopedic injuries that are unstable 2. Osteoporosis with high risk of pathological fracture 3. Cutaneous lesions and/or pressure ulcers 4. Joint contractures 5. Cardiopulmonary diseases 6. Body weight exceeding 150 Kg", "candidate_expression": "((Body weight) AND (Cardiopulmonary diseases) AND (Cutaneous lesions) AND (Joint contractures) AND (Orthopedic injuries) AND (Osteoporosis) AND (exceeding 150 Kg) AND (high risk of pathological fracture) AND (pressure ulcers) AND (unstable))"}
{"candidate_id": "LLM04996", "doc_id": "NCT02678663_inc", "case_bucket": "other", "source_criterion": "Subjects over the age of 18 years who agree informed consent and who have at least one polyp of eligible size (6-10mm)", "candidate_expression": "((age 18 years over) AND (agree informed consent) AND (polyp at least one eligible size 6-10mm))"}
{"candidate_id": "LLM04997", "doc_id": "NCT03304496_inc", "case_bucket": "or", "source_criterion": "Men and women older than 18 years, scheduled consecutively to perform a coronary procedure in the department of hemodynamics of the National Institute of Cardiology \"Ignacio Chavez\". Patients may have any of the following indications for cardiac catheterization: Thoracic pain under study. Stable chronic coronary disease. Acute myocardial infarction with ST segment elevation, not perfused (without timely reperfusion therapy) with less than 4 weeks of evolution. Acute myocardial infarction with ST-segment elevation, successful thrombolytic therapy, which will undergo drug-invasive therapy. Acute myocardial infarction without ST segment elevation. Unstable angina. Any acute coronary syndrome, to intervene non-infarct-related artery. Disease of any heart valve. Myocarditis or pericarditis. Dilated cardiomyopathy. Patients in renal or cardiac transplantation protocol for any etiology. Congenital heart disease that requires knowing the coronary anatomy prior to surgical correction. The planned procedure can be any of the following: For diagnostic purposes (coronary angiography only, left catheterization, left and right catheterization). For therapeutic purposes: percutaneous coronary intervention (PCI), with or without stent placement. A priori access must be right or left radial artery. Radial arterial pulse may be present or absent by palpation. Modified Allen or Barbeau test should be positive (presence of collateral palmar flow).", "candidate_expression": "((Acute myocardial infarction) AND (Barbeau test) AND (Congenital heart disease) AND (Dilated) AND (Disease) AND (Men) AND (Modified Allen test) AND (Myocarditis) AND (PCI) AND (Radial arterial) AND (ST segment elevation) AND (ST-segment elevation) AND (Stable) AND (Thoracic pain) AND (Unstable angina) AND (absent) AND (access) AND (acute coronary syndrome) AND (artery) AND (cardiac catheterization) AND (cardiac transplantation) AND (cardiomyopathy) AND (chronic coronary disease) AND (collateral palmar flow) AND (coronary angiography) AND (coronary procedure) AND (department of hemodynamics) AND (diagnostic) AND (drug-invasive therapy) AND (evolution) AND (heart valve) AND (indications) AND (intervene) AND (knowing the coronary anatomy) AND (left catheterization) AND (left radial artery) AND (non-infarct-related) AND (older than 18) AND (only) AND (palpation) AND (percutaneous coronary intervention) AND (pericarditis) AND (positive) AND (presence) AND (present) AND (prior to surgical correction.) AND (priori) AND (procedure) AND (pulse) AND (renal transplantation) AND (reperfusion therapy) AND (right catheterization) AND (right radial artery) AND (scheduled) AND (stent placement) AND (successful) AND (surgical correction) AND (the National Institute of Cardiology \"Ignacio Chavez\") AND (therapeutic) AND (thrombolytic therapy) AND (timely) AND (will undergo) AND (with less than 4 weeks of evolution) AND (without) AND (women) AND (years))"}
{"candidate_id": "LLM04998", "doc_id": "NCT02164734_inc", "case_bucket": "other", "source_criterion": "Mild-to-moderate RDS; Postnatal age 2 to 48 hours; Gestational age 27 0/7 to 36 6/7 weeks; Treated with nasal CPAP modalities = 5 cm H2O and FiO2 between 0.30 and 0.60 for at least 2 hours to maintain SpO2 90-95%; Informed consent", "candidate_expression": "((FiO2 between 0.30 and 0.60) AND (Gestational age 27 0/7 to 36 6/7 weeks) AND (Informed consent) AND (Postnatal age 2 to 48 hours) AND (RDS Mild-to-moderate) AND (SpO2 90-95%) AND (nasal CPAP = 5 cm H2O for at least 2 hours))"}
{"candidate_id": "LLM04999", "doc_id": "NCT03123562_exc", "case_bucket": "or", "source_criterion": "Epilepsy Hydrocephalus with ventricular drain Coagulation disorders Allergy to anesthetic agents Severe health conditions such as cancer, failure of heart, lung, liver or kidney Active infections", "candidate_expression": "((Allergy) AND (Coagulation disorders) AND (Epilepsy) AND (Hydrocephalus) AND (Severe health conditions) AND (anesthetic agents) AND (cancer) AND (failure of heart) AND (failure of kidney) AND (failure of liver) AND (failure of lung) AND (infections Active) AND (ventricular drain))"}
{"candidate_id": "LLM05000", "doc_id": "NCT03056287_inc", "case_bucket": "or", "source_criterion": "1) age 50-70 2) stroke within the past 6 to 60 months, 3) major depressive disorder (PHQ-9 > 10) and diagnosed using the Structured Clinical Interview for Depression (SCID) according to the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV), 4) residual paresis in the lower extremity (Fugl-Meyer LE motor score <34), 5) ability to walk without assistance and without an AFO on the treadmill ≥ 30 seconds at speeds ranging from 0.2-0.8 m/s, 6) no antidepressant medications or clinically able to discontinue medications, 7) HRSD question #9 regarding suicide <2, 8) provision of informed consent. In addition, all subjects who meet criteria for the training portion must complete an exercise tolerance test and be cleared for participation by the study cardiologist.", "candidate_expression": "((Fugl-Meyer LE motor score <34) AND (HRSD question #9 <2) AND (In addition, all subjects who meet criteria for the training portion must complete an exercise tolerance test and be cleared for participation by the study cardiologist.) AND (PHQ-9 > 10) AND (Structured Clinical Interview for Depression (SCID) according to the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV)) AND (ability to walk without assistance) AND (age 50-70) AND (clinically able to discontinue medications) AND (major depressive disorder) AND (residual paresis lower extremity) AND (stroke within the past 6 to 60 months) AND NOT (AFO on the treadmill ≥ 30 seconds speeds) AND NOT (antidepressant))"}
```
