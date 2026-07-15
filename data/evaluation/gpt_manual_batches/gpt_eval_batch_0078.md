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
{"candidate_id": "LLM01926", "doc_id": "NCT01401335_exc", "case_bucket": "or", "source_criterion": "Age less than 15 or greater than 25 and not participating in the day care center", "candidate_expression": "((Age) AND NOT (participating in the day care center) AND ((greater than 25) OR (less than 15)))"}
{"candidate_id": "LLM01927", "doc_id": "NCT00926523_inc", "case_bucket": "other", "source_criterion": "Subject are at least 18 years of age Subject has confirmed Pulmonary Hypertension and Interstitial Lung Disease Subject are able to complete study procedures, such as spirometry, and Pulmonary Exercise test.", "candidate_expression": "((Interstitial Lung Disease confirmed) AND (Pulmonary Exercise test) AND (Pulmonary Hypertension confirmed) AND (age at least 18 years) AND (spirometry) AND (study procedures))"}
{"candidate_id": "LLM01928", "doc_id": "NCT02762851_exc", "case_bucket": "or", "source_criterion": "Anaphylactic reaction to a previous dose of TIV(trivalent influenza vaccine) Known IgE( Immunoglobulin E)-mediated hypersensitivity to eggs manifested as hives, swelling of the mouth and throat, difficulty in breathing, hypotension, or shock Guillain-Barré syndrome within eight weeks of a previous influenza vaccine Anaphylactic reaction to neomycin Patients who have had influenza vaccine in two of the three previous years", "candidate_expression": "((Anaphylactic reaction) AND (Guillain-Barré syndrome) AND (IgE( Immunoglobulin E)-mediated hypersensitivity) AND (TIV) AND (a previous influenza vaccine) AND (eggs) AND (in two of the three previous years) AND (influenza vaccine) AND (neomycin) AND (previous) AND (trivalent influenza vaccine) AND (within eight weeks of a previous influenza vaccine) AND ((difficulty in breathing) OR (hives) OR (hypotension) OR (shock) OR (swelling of the mouth and throat)))"}
{"candidate_id": "LLM01929", "doc_id": "NCT02118467_inc", "case_bucket": "other", "source_criterion": "Age greater than or equal to 18 years old Requirement for vasoactive drugs via a central venous catheter for the treatment of shock. Shock will be defined as mean arterial pressure less than 70 mmHg or systolic blood pressure less than 100 mmHg despite administration of at least 1000 mL of crystalloid or 500 mL of colloid, unless there is an elevation in the central venous pressure to > 12 mmHg or in the pulmonary artery occlusion pressure to > 14 mmHg coupled with signs of tissue hypoperfusion (e.g. altered mental state, mottled skin, urine output < 0.5 mL/kg body weight for one hour, or a serum lactate level of > 2 mmol per liter).", "candidate_expression": "((Age) AND (central venous catheter) AND (greater than or equal to 18 years old) AND (less than 100 mmHg) AND (less than 70 mmHg) AND (mean arterial pressure) AND (shock) AND (systolic blood pressure) AND (vasoactive drugs))"}
{"candidate_id": "LLM01930", "doc_id": "NCT02689024_exc", "case_bucket": "or", "source_criterion": "multiple injuries (polytrauma patients) previous adverse reaction or known allergy to local anaesthetics or opioids or paracetamol skin infection in proximity of injection site delirious state at presentation in the ED", "candidate_expression": "((delirious) AND (multiple injuries) AND (polytrauma) AND (skin infection injection site) AND ((adverse reaction) OR (allergy)) AND ((local anaesthetics) OR (opioids) OR (paracetamol)))"}
{"candidate_id": "LLM01931", "doc_id": "NCT03648021_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to paracetamol or mannitol (excipient with known effect) Severe hepatocellular insufficiency (ASAT or ALAT > 5N, or bilirubin > 2N) Pharmacological intervention (administration of corticosteroids, NSAIDs or paracetamol) or physical intervention (external cooling technique) that may influence temperature in the last 6 hours. Pregnant or breastfeeding women Previous participation in this study", "candidate_expression": "((> 2N) AND (> 5N) AND (ALAT) AND (ASAT) AND (NSAIDs) AND (Pharmacological) AND (Pharmacological intervention) AND (Pregnant) AND (Previous participation in this study) AND (bilirubin) AND (breastfeeding) AND (corticosteroids) AND (external cooling technique) AND (hepatocellular insufficiency) AND (hypersensitivity) AND (in the last 6 hours) AND (mannitol) AND (paracetamol) AND (physical intervention) AND (temperature) AND (that may influence temperature) AND (women))"}
{"candidate_id": "LLM01932", "doc_id": "NCT00401245_exc", "case_bucket": "or", "source_criterion": "History of a seizure disorder other than a single childhood febrile seizure. History or presence of clinically important hepatic or renal disease or other medical disease. Presence or recent history of major depressive disorder, bipolar disorder, psychotic disorder, or generalized anxiety disorder requiring therapy.", "candidate_expression": "((bipolar disorder) AND (clinically important hepatic disease) AND (clinically important other medical disease) AND (clinically important renal disease) AND (generalized anxiety disorder) AND (major depressive disorder) AND (psychotic disorder) AND (seizure disorder History) AND NOT (childhood febrile seizure single))"}
{"candidate_id": "LLM01933", "doc_id": "NCT02689024_inc", "case_bucket": "other", "source_criterion": "adult patients aged = 55 years with a radiographically confirmed hip fracture", "candidate_expression": "((= 55 years) AND (adult) AND (aged) AND (hip fracture) AND (radiographically))"}
{"candidate_id": "LLM01934", "doc_id": "NCT02790593_exc", "case_bucket": "or", "source_criterion": "Age less than 18 years Significant arterial disease (Ankle Brachial Pressure Index <0•9 or evidence on Arterial Duplex) Acute Deep Vein Thrombosis Patient unable or unwilling to have high compression (30mmHg minimum) Patients with dexterity insufficiency of hands Patients with peripheral neuropathy Leg ulcers of another underlying cause Leg ulcers of greater than 1 year duration Patients unable or unwilling to provide written, informed consent", "candidate_expression": "((Acute Deep Vein Thrombosis) AND (Age less than 18 year) AND (Leg ulcers) AND (Leg ulcers greater than 1 year duration) AND (Patient unable or unwilling to have high compression (30mmHg minimum)) AND (Patients unable or unwilling to provide written, informed consent) AND (arterial disease Significant) AND (dexterity insufficiency of hands) AND (peripheral neuropathy) AND (underlying cause another) AND ((Ankle Brachial Pressure Index <0•9) OR (Arterial Duplex)))"}
{"candidate_id": "LLM01935", "doc_id": "NCT02961582_exc", "case_bucket": "or", "source_criterion": "Obstructed outlet syndrome (objectified by defeacography) Irritable bowel syndrome (Rome-IV criteria for irritable bowel syndrome) Congenital or organic bowel pathology Rectal prolapse Anatomical limitations preventing placement of an electrode Skin and perineal disease with risk of infection Previous large bowel/rectal surgery Stoma Coexisting neurological disease Significant psychological co-morbidity as assessed subjectively by the investigator Being or attempting to become pregnant during study follow-up", "candidate_expression": "((Anatomical limitations) AND (Being or attempting to become pregnant during study follow-up) AND (Irritable bowel syndrome) AND (Obstructed outlet syndrome) AND (Rectal prolapse) AND (Rome-IV criteria) AND (Significant) AND (Stoma) AND (as assessed subjectively by the investigator) AND (defeacography) AND (irritable bowel syndrome) AND (neurological disease) AND (placement of an electrode) AND (preventing) AND (psychological co-morbidity) AND (risk of infection) AND ((Skin disease) OR (perineal disease)) AND ((large bowel surgery) OR (rectal surgery)) AND ((Congenital bowel pathology) OR (organic bowel pathology)))"}
{"candidate_id": "LLM01936", "doc_id": "NCT03347513_inc", "case_bucket": "other", "source_criterion": "Diagnosed Iron deficiency anemia. H-pylori positive cases. Second trimester pregnancy.", "candidate_expression": "((H-pylori positive Second trimester) AND (Iron deficiency anemia) AND (pregnancy Second trimester))"}
{"candidate_id": "LLM01937", "doc_id": "NCT01184638_exc", "case_bucket": "other", "source_criterion": "With the history of cognitive disorders With chronic neurological disorders Cannot communicate with investigators Cannot stand general anesthesia", "candidate_expression": "((Cannot communicate) AND (Cannot stand) AND (chronic neurological disorders) AND (cognitive disorders) AND (general anesthesia))"}
{"candidate_id": "LLM01938", "doc_id": "NCT02627560_exc", "case_bucket": "or", "source_criterion": "pregnant or breastfeeding known thromboembolic disease or with high risk of thromboembolism, warranting extra anticoagulation in connection with the procedure known allergy to tranexamic acid/Cyklokapron®", "candidate_expression": "((Cyklokapron) AND (allergy) AND (breastfeeding) AND (extra anticoagulation) AND (high risk of) AND (pregnant) AND (thromboembolic disease) AND (thromboembolism) AND (tranexamic acid))"}
{"candidate_id": "LLM01939", "doc_id": "NCT00379366_inc", "case_bucket": "other", "source_criterion": "over 18 years successful angioplasty (residual stenosis < 30%) on a significant stenosis (maximal systolic speed 3 times > from basal maximal systolic speed, stenosis > 70% on angiography) on the venous-prosthesis anastomosis or on the venous segment 5 cm after the anastomosis of a prosthetic haemodialysis vascular access (at least 1 month old) social security affiliation signed informed consent", "candidate_expression": "((angiography) AND (maximal systolic speed 3 times > from basal) AND (on the venous segment 5 cm after the anastomosis angioplasty) AND (on the venous-prosthesis anastomosis angioplasty successful) AND (over 18 years over 18 years) AND (residual stenosis < 30%) AND (signed informed consent) AND (social security affiliation) AND (stenosis > 70%) AND (stenosis significant))"}
{"candidate_id": "LLM01940", "doc_id": "NCT02579200_inc", "case_bucket": "or", "source_criterion": "Previous diagnoses of COPD and HF under optimized clinical treatment as judged by the accompanying physician Reduced left ventricular ejection fraction (<50%) Non-reversible airway obstruction (post-bronchodilator FEV1/FVC < 0.7 and FEV1 < 80 %) Respiratory muscle weakness (Pi,max < 70cmH2O) Persistent dyspnea on daily life (Baseline Dyspnea Index focal score <or= 8).", "candidate_expression": "((< 0.7) AND (< 70cmH2O) AND (< 80 %) AND (<50%) AND (<or= 8) AND (Baseline) AND (Dyspnea Index focal score) AND (FEV1) AND (FEV1/FVC) AND (Non-reversible) AND (Persistent) AND (Pi,max) AND (Reduced) AND (Respiratory muscle weakness) AND (airway obstruction) AND (clinical treatment) AND (dyspnea on daily life) AND (left ventricular ejection fraction) AND (optimized) AND (post-bronchodilator) AND ((COPD) OR (HF)))"}
{"candidate_id": "LLM01941", "doc_id": "NCT02678962_inc", "case_bucket": "other", "source_criterion": "Age from 40 to 80 years old, either gender; Patients with bilateral age related cataracts, require bilateral cataract phacoemulsification combined Intraocular Lens implantation; Willing to undergo second eye surgery within 7 days after first eye surgery; The potential postoperative visual acuity of 20/40 or better in both eyes; Preoperative measurement of corneal astigmatism indicate the subjects are suitable for multifocal intraocular lenses implantation; Capability to understand the informed consent and willing and able to attend study", "candidate_expression": "((Age from 40 to 80 years old) AND (Capability to understand the informed consent and willing and able to attend study) AND (Intraocular Lens implantation) AND (cataract phacoemulsification) AND (cataracts bilateral age related) AND (measurement of corneal astigmatism Preoperative suitable) AND (multifocal intraocular lenses implantation))"}
{"candidate_id": "LLM01942", "doc_id": "NCT00639795_exc", "case_bucket": "or", "source_criterion": "Age less than 18 Clinical or laboratory evidence of systemic infection Current pregnancy as assessed by preoperative urine HCG test Serious, uncontrolled, non-malignant illness Malignant illness requiring systemic chemotherapy in the last 6 months Documented allergy to oxycodone, morphine sulfate or acetaminophen Contraindication to peripheral nerve blockade or general anesthesia including: 1. patient refusal 2. active infection at site of planned block 3. documented allergy to any local or general anesthetic medications 4. significant coagulopathy( prothrombin time >15 seconds, INR>1.5 5. pre-existing neuropathy and medical conditions or deformities which would compromise block or anesthetic safety Planned pleurodesis Current use of high dose inhaled or systemic steroids Current use of Amiodarone (Cordarone) Morbid obesity (BMI=40kg/m2) Patients with clinically significant mental health issues such as psychosis requiring treatment with antipsychotic medications. Patients unable to consent Patients with active infections requiring antibiotics within one month of registration Participation in other clinical trials that may interfere with this study", "candidate_expression": "((Age less than 18) AND (Amiodarone Current) AND (BMI 40kg/m2) AND (Cordarone) AND (INR >1.5) AND (Malignant illness) AND (Morbid obesity) AND (allergy) AND (antibiotics) AND (antipsychotic medications) AND (coagulopathy significant) AND (infections active within one month of registration) AND (mental health issues clinically significant) AND (neuropathy pre-existing) AND (non-malignant illness Serious uncontrolled) AND (pleurodesis) AND (pregnancy preoperative) AND (prothrombin time >15 seconds) AND (psychosis) AND (steroids Current high dose) AND (systemic chemotherapy in the last 6 months) AND (treatment) AND (urine HCG test pregnancy) AND ((acetaminophen) OR (morphine sulfate) OR (oxycodone)) AND ((Contraindication to general anesthesia) OR (Contraindication to peripheral nerve blockade)) AND ((inhaled) OR (systemic)))"}
{"candidate_id": "LLM01943", "doc_id": "NCT01799681_exc", "case_bucket": "or", "source_criterion": "any neurological conditions other than PD; significant musculoskeletal or cardiopulmonary diseases; other disorders that may affect balance or locomotion; taken any structured behavioral or exercise programs in the past 3 months or they are receiving regular physical rehabilitation at present; unstable condition on anti-parkinsonian medications; surgical interventions for PD; communication or cognitive deficits with mini-mental state examination, (MMSE) <24/30 (Folstein et al., 1975); a history of more than two falls in the previous 12 months.", "candidate_expression": "((PD) AND (anti-parkinsonian medications) AND (disorders that may affect balance or locomotion) AND (falls history more than two in the previous 12 months) AND (mini-mental state examination, (MMSE) <24/30) AND (neurological conditions) AND (regular physical rehabilitation at present) AND (significant) AND (surgical interventions for PD) AND (unstable condition) AND NOT (PD) AND ((structured behavioral programs) OR (structured exercise programs)) AND ((cognitive deficits) OR (communication deficits)) AND ((cardiopulmonary diseases) OR (musculoskeletal diseases)))"}
{"candidate_id": "LLM01944", "doc_id": "NCT02056301_exc", "case_bucket": "other", "source_criterion": "1) Refusal of epidural catheter 2) Pregnancy 3) Bleeding History 4) Inability to understand how to use the PCA device 5) Medication interfering with blood coagulation 6) Patients allergic to local anesthetics 7) Patient refusal to participate in study 8) Developmental delay", "candidate_expression": "((Bleeding) AND (Developmental delay) AND (History) AND (Medication) AND (Pregnancy) AND (Refusal) AND (allergic) AND (epidural catheter) AND (interfering with blood coagulation) AND (local anesthetics))"}
{"candidate_id": "LLM01945", "doc_id": "NCT02607748_exc", "case_bucket": "or", "source_criterion": "Age < 18 years Creatinine > 1.5 mg/dL History of severe allergy to Iodine contrast agents Pregnancy Active atrial fibrillation Multiple premature ventricular or atrial contractions Ejection fraction <35% Class III congestive heart failure", "candidate_expression": "((Age < 18 years) AND (Creatinine > 1.5 mg/dL) AND (Ejection fraction <35%) AND (Iodine contrast agents) AND (Pregnancy) AND (allergy) AND (atrial fibrillation) AND (congestive heart failure Class III) AND ((Multiple premature atrial contractions) OR (Multiple premature ventricular contractions)))"}
{"candidate_id": "LLM01946", "doc_id": "NCT03004209_inc", "case_bucket": "or", "source_criterion": "Clinically diagnosed autoimmune encephalitis Ineffective 1st line treatment (e.g. steroid IV, IVIg) and 2nd line treatment (e.g. Rituximab or cyclophosphamide)", "candidate_expression": "((1st line treatment) AND (2nd line treatment) AND (Clinically diagnosed) AND (Ineffective) AND (autoimmune encephalitis) AND ((IVIg) OR (steroid IV)) AND ((Rituximab) OR (cyclophosphamide)))"}
{"candidate_id": "LLM01947", "doc_id": "NCT02765035_inc", "case_bucket": "other", "source_criterion": "Person is >18 years old. Person is a unilateral transfemoral or knee-disarticulation amputee with stabilized residual limb. Person is a K2, K3 or K4 ambulator based on Medicare Functional Classification Level (MFCL). Person is currently fitted with a prosthesis using a non-microprocessor controlled prosthetic knee for at least 6 months. Person was never fitted with microprocessor controlled prosthetic knee joint. Person is willing and able to independently provide informed consent. Person is willing to comply with study procedures. Person wears prosthesis daily and = 8 hours/day. Person is walking on average 1km/day. Person is walking not slower than 3km/h (~0.8m/s) (based on 10m walk test conducted during recruiting). Person is walking on level ground in a step over step manner.", "candidate_expression": "((MFCL) AND (Medicare Functional Classification Level K2, K3 or K4) AND (Person is willing and able to independently provide informed consent) AND (Person is willing to comply with study procedures) AND (old >18 years) AND (prosthesis) AND (prosthesis daily and = 8 hours/day) AND (prosthetic knee non-microprocessor controlled at least 6 months) AND (walking) AND (walking 1km/day) AND (walking not slower than 3km/h) AND NOT (prosthetic knee joint microprocessor controlled))"}
{"candidate_id": "LLM01948", "doc_id": "NCT03120533_inc", "case_bucket": "other", "source_criterion": "Healthy Volunteers: Age of at least 18 years Existence of a contraceptive method for women of child-bearing age Person affiliated to social security or beneficiary of such a scheme Signed consent form Systemic sclerosis patients: Systemic sclerosis meeting the EULAR criteria. Presence of at least 2 ischemic digital cutaneous ulcerations on two different fingers, with digital ulcers classified as \"active ulcers\" according to the North American working group definition: epithelial denudation is clearly Visible at one place and the bed of de-epithelialized ulcer can be seen; Ulcerations distal to the proximal interphalangeal joint, not associated with calcinosis or bony relief. Ulcers whose major axis measured with the electronic caliper is ≥ 2 mm Age greater than or equal to 18 years Existence of a contraceptive method for women of reproductive age A person who is or is a beneficiary of social security Informed and signed consent signed by the patient or his / her legal representative.", "candidate_expression": "((Age at least 18 years) AND (Age greater than or equal to 18 years) AND (EULAR criteria meeting) AND (North American working group definition epithelial denudation is clearly Visible at one place and the bed of de-epithelialized ulcer can be seen; Ulcerations distal to the proximal interphalangeal joint, not associated with calcinosis or bony relief) AND (Systemic sclerosis) AND (Ulcers) AND (age child-bearing) AND (age reproductive) AND (contraceptive) AND (contraceptive method) AND (digital ulcers active) AND (ischemic digital cutaneous ulcerations at least 2 on two different fingers) AND (major axis measured with the electronic caliper ≥ 2 mm) AND (women))"}
{"candidate_id": "LLM01949", "doc_id": "NCT03344042_inc", "case_bucket": "or", "source_criterion": "parturient in labour without cervical dilation and regular uterine contractions", "candidate_expression": "((cervical dilation) AND (labour) AND (parturient) AND (regular uterine contractions) AND (without))"}
{"candidate_id": "LLM01950", "doc_id": "NCT02072811_inc", "case_bucket": "other", "source_criterion": "Adult acute myeloid leukemia Age: ≥18 and ≤ 60 Clinical condition of the patient allows to carry out induction therapy: ECOG performance status: ≤ 2 and the Hematopoietic Cell Transplant-Co-morbidity Index (HCT-I): ≤3 Informed consent to participate in the study (ICF signed) The second early induction start criteria is in addition to the listed above, the percentage of the blasts on the level >10% on 7th day.", "candidate_expression": "((Adult acute myeloid leukemia) AND (Age ≥18 and ≤ 60) AND (ECOG performance status ≤ 2) AND (Hematopoietic Cell Transplant-Co-morbidity Index (HCT-I) ≤3) AND (Informed consent to participate in the study (ICF signed)) AND (percentage of the blasts >10% on 7th day))"}
```
