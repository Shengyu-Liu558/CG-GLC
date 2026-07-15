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
{"candidate_id": "LLM06426", "doc_id": "NCT01944800_inc", "case_bucket": "or", "source_criterion": "intolerance of or allergy to ticagrelor or prasugrel history of any stroke, transient ischemic attack or intracranial bleeding known intracranial neoplasm, intracranial arteriovenous malformation or intracranial aneurysm active bleeding, clinical findings, that in the judgement of the investigator are associated with an increased risk of bleeding fibrin-specific fibrinolytic therapy less than 24 h before randomization, non-fibrin-specific fibrinolytic therapy less than 48 h before randomization known platelet count < 100.000/µL at the time of screening known anemia (hemoglobin <10 g/dL) at the time of screening oral anticoagulation that cannot be safely discontinued for the duration of the study INR known to be greater than 1.5 at the time of screening chronic renal insufficiency requiring dialysis moderate or severe hepatic dysfunction (Child Pugh B or C) increased risk of bradycardia events (Sick Sinus, AV block grade II or III, bradycardia-induced syncope) index event is an acute complication (< 30 days) of PCI concomitant medical illness that in the opinion of the investigator is associated with a life expectancy < 1 year concomitant oral or i.v. therapy with strong CYP3A Inhibitors (e.g. ketoconazole, itraconazole, voriconazole, telithromycin, clarithromycin, nefazodone, ritonavir, saquinavir, nelfinavir, indinavir, atazanavir, grapefruit juice > 1 L/d), CYP3A substrates with narrow therapeutic indices (e.g. cyclosporine, quinidine), or strong CYP3A inducers (e.g. rifampin/rifampicin, phenytoin, carbamazepine, dexamethason, phenobarbital ) that cannot be safely discontinued =1 doses of ticagrelor or prasugrel within 5 days before randomisation no written informed consent participation in another investigational drug study previous enrolment in this study for women of childbearing potential no negative pregnancy test and no agree to use reliable method of birth control during the study Pregnancy, giving birth within the last 90 days, or lactation inability to cooperate with protocol requirements", "candidate_expression": "((< 100.000/µL) AND (< 30 days) AND (<10 g/dL) AND (=1 doses) AND (> 1 L/d) AND (AV block) AND (B or C) AND (CYP3A substrates with narrow therapeutic indices) AND (Child Pugh) AND (II or III) AND (INR) AND (Pregnancy, giving birth within the last 90 days, or lactation) AND (Sick Sinus) AND (active) AND (acute) AND (allergy) AND (anemia) AND (at the time of screening) AND (atazanavir) AND (bleeding) AND (bradycardia events) AND (bradycardia-induced syncope) AND (cannot be safely discontinued) AND (carbamazepine) AND (chronic renal insufficiency) AND (clarithromycin) AND (clinical findings, that in the judgement of the investigator are associated with an increased risk of bleeding) AND (complication of PCI) AND (concomitant medical illness) AND (cyclosporine) AND (dexamethason) AND (dialysis) AND (fibrin-specific) AND (fibrinolytic therapy) AND (for the duration of the study) AND (for women of childbearing potential no negative pregnancy test and no agree to use reliable method of birth control during the study) AND (grade) AND (grapefruit juice) AND (greater than 1.5) AND (hemoglobin) AND (hepatic dysfunction) AND (i.v. therapy) AND (increased risk) AND (indinavir) AND (intolerance) AND (intracranial aneurysm) AND (intracranial arteriovenous malformation) AND (intracranial bleeding) AND (intracranial neoplasm) AND (is associated with a life expectancy < 1 year) AND (itraconazole) AND (ketoconazole) AND (less than 24 h before randomization) AND (less than 48 h before randomization) AND (moderate) AND (nefazodone) AND (nelfinavir) AND (non-fibrin-specific) AND (oral anticoagulation) AND (oral therapy) AND (participation in another investigational drug study) AND (phenobarbital) AND (phenytoin) AND (platelet count) AND (prasugrel) AND (quinidine) AND (randomisation) AND (randomization) AND (rifampicin) AND (rifampin) AND (ritonavir) AND (saquinavir) AND (severe) AND (stroke) AND (strong CYP3A Inhibitors) AND (strong CYP3A inducers) AND (telithromycin) AND (the study) AND (the time of screening) AND (ticagrelor) AND (transient ischemic attack) AND (voriconazole) AND (within 5 days before randomisation))"}
{"candidate_id": "LLM06427", "doc_id": "NCT02571179_inc", "case_bucket": "other", "source_criterion": "healthy parturients with uncomplicated, single gestation pregnancies, full term (38-42 weeks of gestation) pregnancy, agreed to participate", "candidate_expression": "((agreed to participate) AND (healthy) AND (parturients) AND (pregnancies uncomplicated single gestation) AND (pregnancy full term) AND (weeks of gestation 38-42))"}
{"candidate_id": "LLM06428", "doc_id": "NCT02186782_inc", "case_bucket": "or", "source_criterion": "Infertile women with eugonadotrophic anovulation/oligoovulation. Unexplained infertility.", "candidate_expression": "((Infertile) AND (anovulation) AND (infertility Unexplained) AND (oligoovulation) AND (women))"}
{"candidate_id": "LLM06429", "doc_id": "NCT03080493_inc", "case_bucket": "other", "source_criterion": "15 weeks 0 days gestational age - 23 weeks 5 days gestational age at time of dilator insertion Able to read and write in English Active cell phone with text messaging capability Ride home from dilator insertion clinic appointment", "candidate_expression": "((15 weeks 0 days - 23 weeks 5 days) AND (Able to read and write in English) AND (Active cell phone with text messaging capability) AND (Ride home) AND (at time of dilator insertion) AND (dilator insertion) AND (gestational age))"}
{"candidate_id": "LLM06430", "doc_id": "NCT03663387_inc", "case_bucket": "or", "source_criterion": "Male and female subjects between 40-85 years old will be enrolled. Younger subjects are not included as the risk for brain amyloid lesions is too low All subjects will speak English as their first language or demonstrate proficiency in English (defined as reaching a scaled score of > 11 on the WAIS vocabulary test). All subjects will have normal cognition at baseline: a Clinical Dementia Rating CDR=0, Global Deterioration Scale GDS<2. All subjects will be in good general health and able to participate in the LP and imaging exams. This determination is made by the study neurologist and reviewed at a consensus meeting for each subject.", "candidate_expression": "((Clinical Dementia Rating CDR =0) AND (Global Deterioration Scale GDS <2) AND (LP) AND (WAIS vocabulary test > 11) AND (able to participate) AND (good general health) AND (imaging exams) AND (normal cognition at baseline) AND (old between 40-85 years) AND ((Male) OR (female)) AND ((proficiency in English) OR (speak English first language)))"}
{"candidate_id": "LLM06431", "doc_id": "NCT02312089_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities. Myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Myoma) AND (Uterine abnormalities) AND (endometriosis) AND (uterine surgery) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM06432", "doc_id": "NCT02822001_exc", "case_bucket": "or", "source_criterion": "Patients unable to give informed consent. Any patient whose condition will not allow for placement of the electrode PadSet. Patients whose tracheas were not extubated in OR or PACU. Patients with Impaired Renal Function with a have a known estimated CrCl<30 ml/min Patients using oral contraception.", "candidate_expression": "((<30 ml/min) AND (Impaired Renal Function) AND (OR) AND (PACU) AND (Patients unable to give informed consent) AND (allow) AND (condition) AND (electrode PadSet) AND (estimated CrCl) AND (extubated) AND (not) AND (oral contraception) AND (placement) AND (tracheas))"}
{"candidate_id": "LLM06433", "doc_id": "NCT01228279_exc", "case_bucket": "or", "source_criterion": "Diabetes Mellitus Acute coronary syndrome in the past 6 months Cardiac arrhythmias (2nd and 3rd degree heart block or premature ventricular complexes in Lown classes 4 or 5) Symptoms suggestive of obstructive or central sleep apnea (with a score of > 10 on Epworth sleepiness scale) Patients taking Clonidine Body mass index (BMI) > 34 Patients unable to give consent Pregnant women Patients with leg injury involving nerve damage Patients taking anticoagulant medication Patients with significant bleeding disorder or liver disorder Hemoglobin <1.05 g/dl at the time of initiation of therapy patients with unilateral or bilateral nephrectomy Planned kidney transplant in the next 4 months Life expectancy under 6 months Oliguria (urine output less than 400 ml per day)", "candidate_expression": "((2nd degree heart block) AND (3rd degree heart block) AND (<1.05 g/dl) AND (> 34) AND (Acute coronary syndrome) AND (BMI) AND (Body mass index) AND (Cardiac arrhythmia) AND (Clonidine) AND (Diabetes Mellitus) AND (Epworth sleepiness scale) AND (Hemoglobin) AND (Life expectancy) AND (Lown classes 4) AND (Lown classes 5) AND (Oliguria) AND (Patients unable to give consent) AND (Planned) AND (Pregnant women) AND (anticoagulant) AND (at the time of initiation of therapy) AND (bilateral) AND (bleeding disorder) AND (central sleep apnea) AND (in the next 4 months) AND (in the past 6 months) AND (initiation of therapy) AND (kidney transplant) AND (leg injury) AND (less than 400 ml per day) AND (liver disorder) AND (nephrectomy) AND (nerve damage) AND (obstructive sleep apnea) AND (premature ventricular complexes) AND (score of > 10) AND (significant) AND (under 6 months) AND (unilateral) AND (urine output))"}
{"candidate_id": "LLM06434", "doc_id": "NCT02984475_exc", "case_bucket": "or", "source_criterion": "Patients with renal impairment (serum creatinine more than twice the upper limit of normal). Patients with heart failure. Patients with sepsis or active infection. Patients with diabetes mellitus (either primary or secondary to thalassemia). regular consumption of medication with potential hepatotoxicity. regular herbal medicine or antioxidant supplementation. patients with gastrointestinal conditions preventing adsorption of oral medication.", "candidate_expression": "((diabetes mellitus) AND (heart failure) AND (hepatotoxicity) AND (medication) AND (renal impairment) AND (serum creatinine more than twice the upper limit of normal) AND ((antioxidant supplementation) OR (herbal medicine)) AND ((active infection) OR (sepsis)) AND ((primary) OR (secondary to thalassemia)))"}
{"candidate_id": "LLM06435", "doc_id": "NCT02570321_inc", "case_bucket": "or", "source_criterion": "Corneal ulcer that is smear positive for either bacteria or filamentous fungus Pinhole visual acuity worse than 20/70 in the affected eye Not treated already with antimicrobial medications at presentation Age over 18 years Basic understanding of the study as determined by the physician Commitment to return for follow up visits", "candidate_expression": "((Age over 18 years) AND (Commitment to return for follow up visits) AND (Corneal ulcer) AND (Pinhole visual acuity worse than 20/70) AND (antimicrobial medications) AND (smear positive) AND ((bacteria) OR (filamentous fungus)))"}
{"candidate_id": "LLM06436", "doc_id": "NCT02056626_inc", "case_bucket": "other", "source_criterion": "systolic blood pressure between 140-160 mmHG between 18-80 years old", "candidate_expression": "((between 140-160 mmHG) AND (between 18-80 years) AND (old) AND (systolic blood pressure))"}
{"candidate_id": "LLM06437", "doc_id": "NCT03637946_inc", "case_bucket": "or", "source_criterion": "Over 18 years of age; Systemically healthy; Non-smoking; With good oral hygiene; Absent irreversible pulpal alteration; With the presence of a non-carious cervical lesion (LCNCs) that needs to be restored. This lesion should be non-carious, non-retentive, with at least 1 mm and up to 3 mm depth, should involve both enamel and dentin of vital teeth without mobility, and present hypersensitivity; Presence a natural tooth of the same position of the restored tooth, but in the opposite arch of the same jaw to be considered for the positive control; Periodontal parameters : Depth Probing (PS), Visible Plaque Index (IPV), Gingival Index (GI) and Probing Bleed Index (SS). The normal included were: PS = 1 to 3 mm, GI = 0, IPV = score 0 e SS = score 0.", "candidate_expression": "((Non-smoking) AND (PS = 1 to 3 mm) AND (Systemically healthy) AND (age Over 18 years) AND (depth at least 1 mm and up to 3 mm) AND (good oral hygiene) AND (hypersensitivity) AND (lesion non-carious non-retentive involve both enamel and dentin) AND NOT (irreversible pulpal alteration) AND ((Depth Probing (PS)) OR (Gingival Index (GI)) OR (Probing Bleed Index (SS)) OR (Visible Plaque Index (IPV))) AND ((GI = 0) OR (IPV score 0) OR (SS score 0)) AND ((non-carious cervical lesion (LCNCs)) OR (restored needs to be)))"}
{"candidate_id": "LLM06438", "doc_id": "NCT03420638_inc", "case_bucket": "other", "source_criterion": "Scheduled to undergo bilateral palatine tonsillectomy as the only procedure", "candidate_expression": "((Scheduled to undergo) AND (bilateral) AND (only procedure) AND (palatine tonsillectomy) AND (procedure))"}
{"candidate_id": "LLM06439", "doc_id": "NCT02944292_exc", "case_bucket": "other", "source_criterion": "Contraindication for propofol administration Contraindication for IAP measurement in supine position with head-of-bed at 0° Other intervention for reduction of IAP planned Previous propofol infusion rate >4 mg/kg/h", "candidate_expression": "((Contraindication) AND (IAP measurement supine position head-of-bed at 0°) AND (intervention for reduction of IAP Other planned) AND (propofol) AND (propofol infusion rate Previous >4 mg/kg/h))"}
{"candidate_id": "LLM06440", "doc_id": "NCT02416869_inc", "case_bucket": "other", "source_criterion": "Healthy patients (ASA I) Bilateral symmetrically impacted lower third molars according to Pel-Gregory's and Winter's classification", "candidate_expression": "((ASA) AND (Bilateral symmetrically impacted lower third molars) AND (Healthy patients) AND (I) AND (Pel-Gregory's and Winter's classification))"}
{"candidate_id": "LLM06441", "doc_id": "NCT02957305_inc", "case_bucket": "other", "source_criterion": "All patients admitted at the Gynecological emergency Unit at Hospital de Clínicas de Porto Alegre scheduled for uterine evacuation with <12 weeks of gestation.", "candidate_expression": "((Gynecological emergency Unit at Hospital de Clínicas de Porto Alegre) AND (gestation <12 weeks) AND (uterine evacuation))"}
{"candidate_id": "LLM06442", "doc_id": "NCT02764476_exc", "case_bucket": "or", "source_criterion": "Nonfluency or inability to communicate in English spoken language Inability to participate or attend biweekly 30 minute session over 14 weeks Frank psychosis Active self harm urges Serious medical illness Active substance or alcohol use or dependence that could interfere with participation Diagnoses of mental retardation, dementia or delirium Pregnant women", "candidate_expression": "((Active) AND (Frank) AND (Pregnant) AND (Serious) AND (alcohol use or dependence) AND (delirium) AND (dementia) AND (medical illness) AND (mental retardation) AND (psychosis) AND (self harm urges) AND (substance use or dependence) AND (that could interfere with participation) AND (women))"}
{"candidate_id": "LLM06443", "doc_id": "NCT03318393_inc", "case_bucket": "or", "source_criterion": "Age 1 day to less than 18 years Cared for in the pediatric intensive care unit or pediatric cardiac intensive care unit receiving venovenous or venoarterial ECMO", "candidate_expression": "((1 day to less than 18 years) AND (Age) AND ((pediatric cardiac intensive care unit) OR (pediatric intensive care unit)) AND ((venoarterial ECMO) OR (venovenous ECMO)))"}
{"candidate_id": "LLM06444", "doc_id": "NCT03539718_exc", "case_bucket": "other", "source_criterion": "Patients with intercurrent infections. Patients with sepsis. Patients receiving drugs affecting immune system like immunosuppressive drugs. Patients on antibiotics.", "candidate_expression": "((antibiotics) AND (drugs affecting immune system) AND (immunosuppressive drugs) AND (intercurrent infections) AND (sepsis))"}
{"candidate_id": "LLM06445", "doc_id": "NCT02339974_inc", "case_bucket": "scope", "source_criterion": "Patients must be at least 21 years old. The patient must have severe, symptomatic (ACC/AHA Stage D symptoms) tricuspid regurgitation (TR) as assessed by 2D echocardiogram with evidence of peripheral and central venous congestion (specifically lower extremity edema and abdominal ascites requiring diuretics.) The patient must be evaluated by a \"heart team\" of physicians including an interventional cardiologist, cardiothoracic surgeon, heart failure specialist, and imaging specialist, and presented for review at a local multi-disciplinary conference. By consensus, the heart team must agree (and verify in the case review process) that valve implantation will likely benefit the patient. The heart team must agree that medical factors preclude operation, based on a conclusion that the probability of death or serious, irreversible morbidity exceeds the probability of meaningful improvement. Also, other factors which may increase the patients perceived surgical risk for inclusion in the trial will be clearly delineated if they are present. These include, but are not limited to the following as defined by VARC 2: Frailty, Hostile chest, porcelain aorta, IMA or other critical conduit crossing the midline or adherent to the posterior table of sternum, severe right ventricular (RV) dysfunction. The surgeons' consultation notes shall specify the medical or anatomic factors leading to that conclusion. At least one of the cardiac surgeon assessors must have interviewed and examined the patient. The study patient provides informed consent and agrees to comply with all required post-procedure follow-up visits, including annual visits up to 5 years.", "candidate_expression": "((2D echocardiogram) AND (ACC/AHA Stage D) AND (TR) AND (The study patient provides informed consent and agrees to comply with all required post-procedure follow-up visits, including annual visits up to 5 years.) AND (abdominal ascites) AND (central venous congestion) AND (diuretics) AND (lower extremity edema) AND (old at least 21 years) AND (peripheral venous congestion) AND (tricuspid regurgitation severe symptomatic))"}
{"candidate_id": "LLM06446", "doc_id": "NCT03355469_inc", "case_bucket": "or", "source_criterion": "Male or female >40 and <70 years old. Has a body mass index >27 and <47 kg/m2. Not diagnosed with Type 2 diabetes. Not currently engaged in > 60 min/wk of exercise Meet at least 3 of 5 National Cholesterol Education Adult Treatment Panel III Increased waist circumference (=102 cm in men; =88 cm in women) Elevated triglycerides (=150 mg/dl), or on medication for treating the condition Reduced HDL-cholesterol (<40mg/dl in men, <50 mg/dl in women), or on medication for treating the condition High blood pressure (=130 mmHg systolic or =85mmHg diastolic), or on medication for treating the condition Elevated fasting glucose (=100 mg/dl), or on medication for treating the condition", "candidate_expression": "((<40mg/dl) AND (<50 mg/dl) AND (=100 mg/dl) AND (=102 cm) AND (=150 mg/dl) AND (=88 cm) AND (> 60 min/wk) AND (>27 and <47 kg/m2) AND (>40 and <70 years) AND (Elevated) AND (Elevated fasting glucose) AND (HDL-cholesterol) AND (High) AND (High blood pressure) AND (Increased) AND (National Cholesterol Education Adult Treatment Panel III) AND (Not) AND (Reduced) AND (Type 2 diabetes) AND (at least 3 of 5) AND (blood pressure) AND (body mass index) AND (currently) AND (engaged in exercise) AND (fasting glucose) AND (medication for treating) AND (old) AND (triglycerides) AND (waist circumference) AND ((Male) OR (female)) AND ((men) OR (women)) AND ((=130 mmHg systolic) OR (=85mmHg diastolic)))"}
{"candidate_id": "LLM06447", "doc_id": "NCT03434951_exc", "case_bucket": "or", "source_criterion": "rearthroplasty ASA IV-V inadequate spoken finnish for reliable pain assessment Dementia or otherwise impaired cognition contraindication for any medication or substance used in survey protocol weight <50kg or BMI =35 kg/m2 preoperative SpO2 less than 93% clinical suspicion that subject can not use PCA adequately history of substance abuse or current excessive use of alcohol preoperative use of either pregabalin, gabapentin or strong opiates", "candidate_expression": "((ASA IV-V) AND (BMI =35 kg/m2) AND (Dementia) AND (SpO2 preoperative less than 93%) AND (contraindication) AND (excessive use of alcohol current) AND (gabapentin) AND (impaired cognition) AND (inadequate spoken finnish) AND (medication used in survey protocol) AND (pregabalin) AND (rearthroplasty) AND (reliable pain assessment) AND (strong opiates) AND (subject can not use PCA adequately clinical suspicion) AND (substance abuse history) AND (substance used in survey protocol) AND (weight <50kg))"}
{"candidate_id": "LLM06448", "doc_id": "NCT02968602_inc", "case_bucket": "or", "source_criterion": "DSM-IV or DSM-5 diagnosis of schizophrenia or schizoaffective disorder Male or Female Age: 18 to 65 years Caucasian or Non-Caucasian Smoke at least 10 cigarettes daily Urine cotinine level ? 100 ng/ml (NicAlert(r) reading ? 3) Agrees to wear a head mounted display (HMD) for up to 45 minutes Able to complete the Evaluation to Sign Consent (ESC) with minimum score of 80%", "candidate_expression": "((Age 18 to 65 years) AND (Agrees to wear for up to 45 minutes) AND (Evaluation to Sign Consent (ESC) Able to complete minimum score of 80%) AND (NicAlert(r) ? 3) AND (Smoke at least 10 cigarettes daily) AND (Urine cotinine level ? 100 ng/ml) AND (head mounted display (HMD)) AND ((Caucasian) OR (Non-Caucasian)) AND ((DSM-5) OR (DSM-IV)) AND ((schizoaffective disorder) OR (schizophrenia)) AND ((Female) OR (Male)))"}
{"candidate_id": "LLM06449", "doc_id": "NCT02637453_inc", "case_bucket": "other", "source_criterion": "No response to more than one antiarrhythmic drug, or unwilling to receive long-term drug treatment. Can provide informed consent form expressing willingness to participate in the study and comply with follow-up tests and evaluation procedures. Aged 18-80 years.", "candidate_expression": "((Aged 18-80 years) AND (Can provide informed consent form expressing willingness to participate in the study and comply with follow-up tests and evaluation procedures.) AND (antiarrhythmic drug more than one) AND NOT (response))"}
{"candidate_id": "LLM06450", "doc_id": "NCT02406885_exc", "case_bucket": "or", "source_criterion": "History of documented clotting/coagulation disorder History of cancer (within the last year) Any diagnosis requiring anti-coagulation History of hypersensitivity reaction to apixaban Active clinically significant bleeding Creatinine > 1.5 mg/dL Participants currently receiving any type of anticoagulation or blood thinning medications, including heparin, low molecular weight heparins, Plavix, aspirin, NSAIDS Combined P-glycoprotein and strong cytochrome P450 (CYP) 3A4 inhibitor Combined P-glycoprotein and moderate CYP 3A4 inhibitor Combined P-glycoprotein inducer and strong CYP 3A4 inducer Inducers of p-glycoprotein Strong inducers of CYP 3A4", "candidate_expression": "((> 1.5 mg/dL) AND (Active) AND (CYP 3A4 inducer) AND (CYP 3A4 inhibitor) AND (Creatinine) AND (Inducers of p-glycoprotein) AND (P-glycoprotein inducer) AND (P-glycoprotein inhibitor) AND (Strong) AND (anti-coagulation) AND (apixaban) AND (bleeding) AND (cancer) AND (cytochrome P450 3A4 inhibitor) AND (hypersensitivity) AND (inducers of CYP 3A4) AND (last year) AND (moderate) AND (significant) AND (strong) AND ((anticoagulation) OR (blood thinning medications)) AND ((NSAIDS) OR (Plavix) OR (aspirin) OR (heparin) OR (low molecular weight heparins)) AND ((clotting disorder) OR (coagulation disorder)))"}
```
