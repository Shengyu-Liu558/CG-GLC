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
{"candidate_id": "LLM06801", "doc_id": "NCT01214096_inc", "case_bucket": "or", "source_criterion": "1. Age: 18-75 years old, no limitation in gender; 2. Left ventricular ejection fraction (LVEF) ≤ 40% (ECHO); 3. Patients with chronic heart failure (NYHA class II or III); 4. In the past one month, the clinical condition (including history, clinical symptoms and signs) was relatively stable; 5. Patients on standard treatment of chronic heart failure at the target dose or maximum tolerance dose for over 1 month ,or unchanged dose in last 1 month; 6. Understand and sign the informed consent form;", "candidate_expression": "((18-75 years) AND (Age) AND (ECHO) AND (In the past one month) AND (Left ventricular ejection fraction (LVEF)) AND (NYHA) AND (Understand and sign the informed consent form;) AND (chronic heart failure) AND (class II or III) AND (clinical signs) AND (clinical symptoms) AND (for over 1 month) AND (history) AND (in last 1 month) AND (maximum tolerance dose) AND (relatively stable) AND (target dose) AND (treatment of chronic heart failure) AND (unchanged dose) AND (≤ 40%))"}
{"candidate_id": "LLM06802", "doc_id": "NCT03337503_exc", "case_bucket": "or", "source_criterion": "Acute pain (less than 3 months in duration) Previous serious adverse event or hypersensitivity to cannabis or cannabinoids Inability to understand and comply with the instructions of the study Presence of significant cardiac disease (history of unstable ischemic heart disease, heart failure, severe and uncontrolled hypertension) that, in the opinion of the investigator, would put the patient at risk of a clinically significant arrhythmia or myocardial infarction Current substance use disorder according to the Diagnostic and Statistical Manual of Mental Disorders Fifth Edition (DSM 5) Life-time history of dependence on cannabis or diagnosis of cannabis use disorder (CUD) according to the DSM 5 Life-time history of DSM 5 schizophrenia, bipolar disorder, or previous psychosis with or intolerance to cannabinoids Current or history of suicidal ideation Pregnant, breast-feeding or female patients of child-bearing potential and male patients whose partner is of child-bearing potential, unless willing to ensure that they or their partner use effective contraception Hepatic impairment (aspartate aminotransferase more than three times normal) or renal function impairment (serum creatinine level >133 µmol/L, Estimated Glomerular Filtration Rate (eGFR) <60) Cognitive impairment according to MiniCog The patient is currently using or has used cannabinoid based medications within 90 days of study entry and is unwilling to abstain for the duration of the study Positive urine drug screen for cannabinoids and other potential abuse substances (e.g. alcohol, cocaine, amphetamines and methamphetamines, unprescribed opioids) Participation in another clinical trial within 30 days of enrolment in our trial", "candidate_expression": "((Cognitive impairment) AND (MiniCog) AND (Participation in another clinical trial within 30 days of enrolment in our trial) AND (Pregnant, breast-feeding or female patients of child-bearing potential and male patients whose partner is of child-bearing potential, unless willing to ensure that they or their partner use effective contraception) AND (aspartate aminotransferase more than three times normal) AND (cannabinoid based medications within 90 days of study entry) AND (cannabinoids) AND (cardiac disease significant) AND (duration less than 3 months) AND (pain Acute) AND (substance use disorder Diagnostic and Statistical Manual of Mental Disorders Fifth Edition (DSM 5)) AND (suicidal ideation) AND (urine drug screen Positive) AND ((adverse event serious) OR (hypersensitivity)) AND ((heart failure) OR (hypertension severe uncontrolled) OR (unstable ischemic heart disease)) AND ((arrhythmia) OR (myocardial infarction)) AND ((cannabis use disorder (CUD) DSM 5) OR (dependence on cannabis)) AND ((bipolar disorder) OR (intolerance) OR (psychosis) OR (schizophrenia DSM 5)) AND ((Current) OR (history)) AND ((Hepatic impairment) OR (renal function impairment)) AND ((Estimated Glomerular Filtration Rate (eGFR) <60) OR (serum creatinine level >133 µmol/L)) AND ((alcohol) OR (amphetamines) OR (cannabinoids) OR (cocaine) OR (methamphetamines) OR (opioids unprescribed)) AND ((cannabinoids) OR (cannabis)))"}
{"candidate_id": "LLM06803", "doc_id": "NCT01944800_inc", "case_bucket": "or", "source_criterion": "intolerance of or allergy to ticagrelor or prasugrel history of any stroke, transient ischemic attack or intracranial bleeding known intracranial neoplasm, intracranial arteriovenous malformation or intracranial aneurysm active bleeding, clinical findings, that in the judgement of the investigator are associated with an increased risk of bleeding fibrin-specific fibrinolytic therapy less than 24 h before randomization, non-fibrin-specific fibrinolytic therapy less than 48 h before randomization known platelet count < 100.000/µL at the time of screening known anemia (hemoglobin <10 g/dL) at the time of screening oral anticoagulation that cannot be safely discontinued for the duration of the study INR known to be greater than 1.5 at the time of screening chronic renal insufficiency requiring dialysis moderate or severe hepatic dysfunction (Child Pugh B or C) increased risk of bradycardia events (Sick Sinus, AV block grade II or III, bradycardia-induced syncope) index event is an acute complication (< 30 days) of PCI concomitant medical illness that in the opinion of the investigator is associated with a life expectancy < 1 year concomitant oral or i.v. therapy with strong CYP3A Inhibitors (e.g. ketoconazole, itraconazole, voriconazole, telithromycin, clarithromycin, nefazodone, ritonavir, saquinavir, nelfinavir, indinavir, atazanavir, grapefruit juice > 1 L/d), CYP3A substrates with narrow therapeutic indices (e.g. cyclosporine, quinidine), or strong CYP3A inducers (e.g. rifampin/rifampicin, phenytoin, carbamazepine, dexamethason, phenobarbital ) that cannot be safely discontinued =1 doses of ticagrelor or prasugrel within 5 days before randomisation no written informed consent participation in another investigational drug study previous enrolment in this study for women of childbearing potential no negative pregnancy test and no agree to use reliable method of birth control during the study Pregnancy, giving birth within the last 90 days, or lactation inability to cooperate with protocol requirements", "candidate_expression": "((< 100.000/µL) AND (< 30 days) AND (<10 g/dL) AND (=1 doses) AND (> 1 L/d) AND (B or C) AND (CYP3A substrates with narrow therapeutic indices) AND (Child Pugh) AND (II or III) AND (INR) AND (Pregnancy, giving birth within the last 90 days, or lactation) AND (active) AND (acute) AND (anemia) AND (at the time of screening) AND (bradycardia events) AND (cannot be safely discontinued) AND (chronic renal insufficiency) AND (complication of PCI) AND (concomitant medical illness) AND (dialysis) AND (fibrin-specific) AND (for the duration of the study) AND (for women of childbearing potential no negative pregnancy test and no agree to use reliable method of birth control during the study) AND (grade) AND (greater than 1.5) AND (hemoglobin) AND (hepatic dysfunction) AND (increased risk) AND (intracranial aneurysm) AND (intracranial arteriovenous malformation) AND (intracranial neoplasm) AND (is associated with a life expectancy < 1 year) AND (less than 24 h before randomization) AND (less than 48 h before randomization) AND (non-fibrin-specific) AND (oral anticoagulation) AND (participation in another investigational drug study) AND (platelet count) AND (randomisation) AND (randomization) AND (strong CYP3A Inhibitors) AND (strong CYP3A inducers) AND (the study) AND (the time of screening) AND (within 5 days before randomisation) AND ((carbamazepine) OR (dexamethason) OR (phenobarbital) OR (phenytoin) OR (rifampicin) OR (rifampin)) AND ((bleeding) OR (clinical findings, that in the judgement of the investigator are associated with an increased risk of bleeding)) AND ((fibrinolytic therapy)) AND ((allergy) OR (intolerance)) AND ((prasugrel) OR (ticagrelor)) AND ((moderate) OR (severe)) AND ((AV block) OR (Sick Sinus) OR (bradycardia-induced syncope)) AND ((i.v. therapy) OR (oral therapy)) AND ((atazanavir) OR (clarithromycin) OR (grapefruit juice) OR (indinavir) OR (itraconazole) OR (ketoconazole) OR (nefazodone) OR (nelfinavir) OR (ritonavir) OR (saquinavir) OR (telithromycin) OR (voriconazole)) AND ((intracranial bleeding) OR (stroke) OR (transient ischemic attack)) AND ((cyclosporine) OR (quinidine)))"}
{"candidate_id": "LLM06804", "doc_id": "NCT01064752_exc", "case_bucket": "or", "source_criterion": "1. Taking a tetracycline within 6 months or history of adverse reaction to minocycline or another tetracycline. 2. Enhanced risk from lumbar puncture, including documented or suspected cerebral mass lesion predisposing to brain herniation or bleeding diathesis. 3. Pregnancy or expectation of pregnancy during the study. 4. Active opportunistic infection or active neurological disease that might confound evaluation. 5. ADC Stage > 1. 6. Hemoglobin < 10 Gms/dL. 7. BUN or creatine above the normal limits. 8. Taking other drugs known to reduce the metabolism of minocycline and thus increase the probability of toxicity.", "candidate_expression": "((< 10 Gms/dL) AND (> 1) AND (ADC Stage) AND (Active) AND (BUN) AND (Enhanced risk) AND (Hemoglobin) AND (Pregnancy) AND (above the normal limits) AND (active) AND (adverse reaction) AND (bleeding diathesis) AND (brain herniation) AND (cerebral mass lesion) AND (creatine) AND (documented) AND (during the study) AND (expectation) AND (history) AND (lumbar puncture) AND (minocycline) AND (neurological disease) AND (opportunistic) AND (opportunistic infection) AND (predisposing to) AND (predisposing to brain herniation or bleeding diathesis) AND (pregnancy) AND (suspected) AND (tetracycline) AND (within 6 months))"}
{"candidate_id": "LLM06805", "doc_id": "NCT03397914_exc", "case_bucket": "or", "source_criterion": "Age less than one year or over 18 years Patients with renal impairment Colistin use less than 72 hours", "candidate_expression": "((Age) AND (Colistin) AND (less than 72 hours) AND (less than one year) AND (over 18 years) AND (renal impairment))"}
{"candidate_id": "LLM06806", "doc_id": "NCT03372265_exc", "case_bucket": "or", "source_criterion": "Allergy to LA Infection in or near insertion site of the peripheral nerve catheter Anatomical abnormalities preventing successful peripheral catheter insertion Habitual use of opioids Pregnancy or breastfeeding (disproved by a negative pregnancy test before trial inclusion)", "candidate_expression": "((Allergy) AND (Anatomical abnormalities) AND (LA) AND (insertion preventing successful) AND (opioids Habitual use) AND (peripheral catheter) AND (peripheral nerve catheter) AND (preventing) AND NOT (pregnancy test negative before trial inclusion) AND ((Pregnancy) OR (breastfeeding)) AND ((in insertion site) OR (near insertion site)))"}
{"candidate_id": "LLM06807", "doc_id": "NCT02935855_exc", "case_bucket": "other", "source_criterion": "patients with cancer patients with chronic inflammation diseases", "candidate_expression": "((cancer) AND (chronic inflammation diseases))"}
{"candidate_id": "LLM06808", "doc_id": "NCT02868437_exc", "case_bucket": "or", "source_criterion": "History of curettage or other intrauterine surgery History of post-abortion complication or infection", "candidate_expression": "((curettage) AND (intrauterine surgery) AND ((post-abortion complication) OR (post-abortion infection)))"}
{"candidate_id": "LLM06809", "doc_id": "NCT03315975_exc", "case_bucket": "or", "source_criterion": "are allergic to influenza vaccination have received influenza vaccination within the past 6 months require prednisone, methotrexate, or other immunosuppressing medications have HIV infection have a history of solid organ or bone marrow transplant require combination immunotherapy are on other studies requiring blood draws that might exceed 450 mL total during the period of the influenza vaccine study", "candidate_expression": "((HIV infection) AND (allergic) AND (are on other studies requiring blood draws that might exceed 450 mL total during the period of the influenza vaccine study) AND (bone marrow transplant) AND (combination immunotherapy require) AND (immunosuppressing medications other) AND (influenza vaccination) AND (influenza vaccination within the past 6 months) AND (methotrexate) AND (prednisone) AND (solid organ transplant))"}
{"candidate_id": "LLM06810", "doc_id": "NCT02106624_inc", "case_bucket": "or", "source_criterion": "need mechanical ventilation for more than 2 days mean blood pressure more than 60mmHg predicted ICU stay more than 7 days tolerance of parenteral or enteral nutrition", "candidate_expression": "((ICU) AND (enteral nutrition) AND (mean blood pressure more than 60mmHg) AND (mechanical ventilation need for more than 2 days) AND (parenteral nutrition) AND (predicted ICU stay more than 7 days) AND (tolerance))"}
{"candidate_id": "LLM06811", "doc_id": "NCT03176316_inc", "case_bucket": "other", "source_criterion": "Patients will be included if they are having an in-patient spinal fusion procedure, are 18 years or older, post and post-operative pain control plan includes opioid medications.", "candidate_expression": "((in-patient) AND (opioid) AND (pain control plan post-operative) AND (spinal fusion procedure) AND (years 18 years or older))"}
{"candidate_id": "LLM06812", "doc_id": "NCT01993836_inc", "case_bucket": "other", "source_criterion": "Surgical patients 60 years of age or older Surgery scheduled to last at least 2 hours (including time for anesthesia induction, etc) English speaking ability. Ability to give informed consent", "candidate_expression": "((60 years or older) AND (Ability to give informed consent) AND (English speaking ability) AND (Surgery) AND (age) AND (scheduled to last at least 2 hours))"}
{"candidate_id": "LLM06813", "doc_id": "NCT00455663_exc", "case_bucket": "or", "source_criterion": "History of significant head trauma, seizure disorder, or mental retardation History of alcohol or drug abuse or dependence within 1 month prior to study entry History of violence within 6 months prior to study entry", "candidate_expression": "((History) AND (violence) AND (within 1 month prior) AND (within 6 months prior) AND ((head trauma) OR (mental retardation) OR (seizure disorder)) AND ((abuse alcohol) OR (dependence alcohol) OR (dependence drug) OR (drug abuse)))"}
{"candidate_id": "LLM06814", "doc_id": "NCT01352598_inc", "case_bucket": "or", "source_criterion": "Patient age >= 18 years Zubrod performance status of 0-3 T1-3 N0 M0 adenocarcinoma of the prostate Prostate volume = 100 cc Signed study-specific consent form Extension of local tumor to involve adjacent organs other than seminal vesicles (T4) Prostate volume > 100 cc Nodal involvement Metastatic disease Prior pelvic radiotherapy except as part of combination therapy for prostate cancer History of scleroderma Patients with psychiatric or addictive disorder that would preclude obtaining informed consent", "candidate_expression": "((Extension of local tumor adjacent organs) AND (M 0) AND (Metastatic disease) AND (N 0) AND (Nodal involvement) AND (Patient age >= 18 years) AND (Prostate volume = 100 cc) AND (Prostate volume > 100 cc seminal vesicles) AND (Signed study-specific consent form) AND (T 1-3) AND (Zubrod performance status 0-3) AND (addictive disorder) AND (adenocarcinoma prostate) AND (prostate cancer) AND (psychiatric disorder) AND (radiotherapy Prior pelvic) AND (scleroderma History) AND NOT (combination therapy))"}
{"candidate_id": "LLM06815", "doc_id": "NCT03082573_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06816", "doc_id": "NCT00440245_exc", "case_bucket": "or", "source_criterion": "asthma and COPD", "candidate_expression": "((COPD) OR (asthma))"}
{"candidate_id": "LLM06817", "doc_id": "NCT03147599_exc", "case_bucket": "or", "source_criterion": "Upper urinary tract deterioration Uncontrolled diabetes mellitus Evident local or pelvic recurrence Adjuvant chemotherapy Chronic retention Pouch stones Urethral stricture or urethro-ileal maldirection Sensitivity to Mebeverine Untreated chronic constipation Active symptomatic urinary infection", "candidate_expression": "((Adjuvant chemotherapy) AND (Chronic retention) AND (Mebeverine) AND (Pouch stones) AND (Sensitivity) AND (Upper urinary tract deterioration) AND (Urethral stricture) AND (chronic constipation Untreated Active) AND (diabetes mellitus Uncontrolled) AND (urethro-ileal maldirection) AND (urinary infection symptomatic) AND ((local recurrence) OR (pelvic recurrence)))"}
{"candidate_id": "LLM06818", "doc_id": "NCT02827526_exc", "case_bucket": "or", "source_criterion": "Preoperative renal failure (defined as a serum creatinine > 2.0 mg/dL.) American Society of Anesthesiologists Physical Status IV or V Pulmonary disease necessitating home oxygen therapy Allergy to methadone, hydromorphone, or ketamine Preoperative recent history of opioid or alcohol abuse Significant liver disease Inability to use a PCA device or speak the English language", "candidate_expression": "((American Society of Anesthesiologists Physical Status IV or V) AND (Inability to speak the English language) AND (Inability to use) AND (PCA device) AND (Pulmonary disease) AND (alcohol abuse) AND (home oxygen therapy) AND (hydromorphone) AND (ketamine) AND (liver disease Significant) AND (methadone) AND (opioid abuse) AND (renal failure Preoperative) AND (serum creatinine > 2.0 mg/dL))"}
{"candidate_id": "LLM06819", "doc_id": "NCT02765035_exc", "case_bucket": "or", "source_criterion": "Person is under 18 years of age. Person who weighs more than 136kg. Person who weighs less than 50kg. Person who is pregnant. Person has a history of chronic skin breakdown on the residual limb. Person has conditions that would prevent participation and pose increased risk (e.g. unstable cardiovascular conditions that preclude physical activity such as walking). Person falls = once a week due to the reasons that could not be corrected by the new prosthesis (for ex. problems with vestibular system). Person is using under arm axillary crutches or walker. Person in an emergency, life threatening situation. Person is unwilling/unable to follow instructions. Person who is not available to follow the entire study protocol. Person who is participating in another study or intends to participate in another study during this study duration. Person who cannot personally provide their consent. Person who is not wearing prosthesis 8hours/day on average. Person who has a score on 10m walk test less than 3km/h (~0.8m/s) (based on 10m walk test conducted during recruiting). Person who walks on average less than 1km per day. Person who is not able to walk on level ground in a step over step manner.", "candidate_expression": "((0.8m/s)) AND (10m walk test) AND (8hours/day) AND (Person is unwilling/unable to follow instruction) AND (Person who cannot personally provide their consent) AND (Person who is not available to follow the entire study protocol) AND (Person who is participating in another study or intends to participate in another study during this study duration.) AND (age) AND (chronic) AND (emergency situation) AND (ess than 1km per day) AND (falls) AND (less than 3km/h) AND (less than 50kg) AND (life threatening situation) AND (more than 136kg) AND (not) AND (once a week) AND (pregnant) AND (prosthesis) AND (residual limb) AND (skin breakdown) AND (under 18 years) AND (under arm axillary crutches) AND (walker) AND (walks) AND (weighs))"}
{"candidate_id": "LLM06820", "doc_id": "NCT02323399_inc", "case_bucket": "or", "source_criterion": "Subject's age is between =12 and 16 years, inclusive Subject is scheduled for a procedure that requires general or neuraxial anesthesia Subjects must have normal or clinically acceptable physical exam Subjects with controlled diabetes prior to entry must have a mean systolic/diastolic office blood pressure =128/78 mmHg (sitting, after 5 minutes of rest) Females must have a urine or serum pregnancy test (Human Chorionic Gonadotropin) that is negative at Screening and Day 1 Subject's parent or legal guardian gives informed consent and subject gives assent.", "candidate_expression": "((128 mmHg) AND (78 mmHg) AND (Day 1) AND (Human Chorionic Gonadotropin) AND (Subject's parent or legal guardian gives informed consent and subject gives assent.) AND (after 5 minutes of rest) AND (age) AND (at Screening) AND (between =12 and 16 years) AND (controlled) AND (diabetes) AND (entry) AND (mean diastolic blood pressure) AND (mean systolic blood pressure) AND (negative) AND (physical exam) AND (prior to entry) AND (procedure) AND (rest) AND (scheduled for a procedure) AND (sitting) AND ((clinically acceptable) OR (normal)) AND ((serum pregnancy test) OR (urine pregnancy test)) AND ((general t) OR (neuraxial anesthesia)))"}
{"candidate_id": "LLM06821", "doc_id": "NCT02299947_inc", "case_bucket": "other", "source_criterion": "Elective surgery for thoracic aneurysm", "candidate_expression": "((Elective surgery) AND (thoracic aneurysm))"}
{"candidate_id": "LLM06822", "doc_id": "NCT03046108_exc", "case_bucket": "or", "source_criterion": "Contraindication for the use of corticosteroids or local anesthetics Presence of inflammatory arthropathy or neuropathy Skin lesions in the area diabetes mellitus Infiltration or previous surgery in the area Refusal to participate in the study", "candidate_expression": "((Contraindication) AND (Infiltration) AND (Refusal to participate in the stud) AND (Skin lesions) AND (corticosteroids) AND (diabetes mellitus) AND (inflammatory arthropathy) AND (local anesthetics) AND (neuropathy inflammatory) AND (previous surgery))"}
{"candidate_id": "LLM06823", "doc_id": "NCT02890719_exc", "case_bucket": "or", "source_criterion": "Genotype 2, 3, 5 or 6 infection. Decompensated cirrhosis defined by the presence of actual or previous history of clinical decompensation including ascites, hepatic encephalopathy, variceal bleeding or spontaneous bacterial peritonitis, or a Child-Pugh B or C. Hepatocellular carcinoma after liver transplantation. Total bilirubin > 3 mg/dL. Immunosuppression with cyclosporine or an mTOR inhibitor (everolimus or sirolimus). Severe extrahepatic diseases: cardiovascular, respiratory, cerebrovascular and poorly controlled diabetes. Platelets < 75 x 109 cells/L. Neutrophil count < 0.5 x 109 cells/L. Hemoglobin < 9 g/dL. Albumin < 3g/dL. HIV infection. Hepatitis B infection. Active intake of toxic amounts of alcohol or recreational drugs. Females who are pregnant, become to be pregnant or breastfeeding or males whose partners are pregnant, become to be pregnant or breastfeeding. Intake of disallowed medications including(but not limited to): 1. Antibiotics: clarithromycin, erythromycin, telithromycin, nafcillin, rifampin 2. Antifungals: itraconazole, ketoconazole, voriconazole 3. Antihypertensives: nifedipine 4. Anticonvulsants: carbamazepine, phenytoin, phenobarbital 5. Bosentan 6. Modafinil 7. St.Jonh's Wort 8. Immunosuppressants: cyclosporin, everolimus, sirolimus 9. Diabetes agents: glibenclamide, glyburide 10. Lipid lowering agents: gemfibrozil 11. Eltrombopag 12. Lapatinib 13. HIV medications: efavirenz, etravirine, all ritonavir boosted and unboosted HIV protease inhibitors 14. Statins: simvastatin, fluvastatin, rosuvastatin at doses greater than 10 mg/d, atorvastatin at doses greater than 10 mg/d.", "candidate_expression": "((Albumin < 3g/dL) AND (Bosentan) AND (Child-Pugh B or C) AND (Eltrombopag) AND (Females) AND (Genotype 2, 3, 5 or 6) AND (HIV infection) AND (HIV protease inhibitors) AND (Hemoglobin < 9 g/dL) AND (Hepatitis B infection) AND (Hepatocellular carcinoma after liver transplantation) AND (Immunosuppression) AND (Lapatinib) AND (Modafinil) AND (Neutrophil count < 0.5 x 109 cells/L) AND (Platelets < 75 x 109 cells/L) AND (Severe) AND (St.Jonh's Wort) AND (Total bilirubin > 3 mg/dL) AND (alcohol Active intake toxic amounts) AND (ascites) AND (atorvastatin doses greater than 10 mg/d) AND (breastfeeding) AND (carbamazepine) AND (cardiovascular) AND (cerebrovascular) AND (cirrhosis Decompensated actual previous) AND (clarithromycin) AND (clinical decompensation) AND (cyclosporin) AND (cyclosporine) AND (diabetes poorly controlled) AND (disallowed medications) AND (efavirenz) AND (erythromycin) AND (etravirine ritonavir boosted ritonavir unboosted) AND (everolimus) AND (extrahepatic diseases Severe) AND (fluvastatin) AND (gemfibrozil) AND (glibenclamide) AND (glyburide) AND (hepatic encephalopathy) AND (infection) AND (itraconazole) AND (ketoconazole) AND (liver transplantation) AND (mTOR inhibitor) AND (males) AND (nafcillin) AND (nifedipine) AND (phenobarbital) AND (phenytoin) AND (pregnant) AND (pregnant become) AND (recreational drugs Active intake) AND (respiratory) AND (rifampin) AND (ritonavir) AND (rosuvastatin doses greater than 10 mg/d) AND (simvastatin) AND (sirolimus) AND (spontaneous bacterial peritonitis) AND (telithromycin) AND (variceal bleeding) AND (voriconazole))"}
{"candidate_id": "LLM06824", "doc_id": "NCT03027115_inc", "case_bucket": "other", "source_criterion": "Male 18 years of age Presenting with hernia requiring surgical intervention", "candidate_expression": "((18 years) AND (Male) AND (age) AND (hernia) AND (requiring) AND (surgical intervention))"}
{"candidate_id": "LLM06825", "doc_id": "NCT00397215_inc", "case_bucket": "or", "source_criterion": "Subjects who the investigator believes that they can and will comply with the requirements of the protocol should be enrolled in the study. A male or female aged 61 years or above at the time of the first vaccination. Written informed consent obtained from the subject. Healthy subjects or subjects with well controlled underlying disease.", "candidate_expression": "((61 years or above) AND (Healthy) AND (Written informed consent) AND (aged) AND (can and will comply with the requirements of the protocol) AND (female) AND (male) AND (underlying disease) AND (well controlled))"}
```
