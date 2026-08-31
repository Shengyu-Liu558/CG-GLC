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
{"candidate_id": "LLM07176", "doc_id": "NCT03004261_inc", "case_bucket": "or", "source_criterion": "Any allogeneic stem cell transplant recipient = 14 years of age and = 60 years of age Bilirubin/ SGOT/SGPT < 5 × upper normal limits. Creatinine < 2 × upper normal limits. Ejection fraction = 50%, no severe arrhythmia. Estimated life expectancy = 6 months. Patients' CMV-DNA = 1000cp/ml in treatment group and being negative in prophylactic group.", "candidate_expression": "((< 2 × upper normal limits) AND (< 5 × upper normal limits) AND (= 1000cp/ml) AND (= 14 years) AND (= 50%) AND (= 6 months) AND (= 60 years) AND (Bilirubin) AND (CMV-DNA) AND (Creatinine) AND (Ejection fraction) AND (Estimated life expectancy) AND (SGOT) AND (SGPT) AND (age) AND (allogeneic stem cell transplant) AND (arrhythmia) AND (negative) AND (no) AND (prophylactic group) AND (severe) AND (treatment group))"}
{"candidate_id": "LLM07177", "doc_id": "NCT02573168_exc", "case_bucket": "or", "source_criterion": "Patients posing a serious suicidal risk and/or violence as judged by the investigator; Delirium Dementia Amnestic and other cognitive disorder; Patients with a history of hypothyroidism unless taking a stable dose of thyroid medication and asymptomatic or euthyroid for 6 months; Patients who meet DSM-IV-TR criteria for any significant current substance abuse; hepatic insufficiency (three times the upper limit of normal (ULN) for aspartate aminotransferase (AST) and/or alanine aminotransferase (ALT)); liver transplant recipient; cirrhosis of the liver; malignancy (except basal cell carcinoma) and/or chemotherapy within 1 year prior to screening; malignancy more than 1 year prior to screening must have been local and without metastasis and/or recurrence, and if treated with chemotherapy, without nervous system complications; significant unstable medical condition or life threatening disease with anticipated survival of less than 6 months; need for therapies that may obscure the results of treatment and/or of the study Participation in another clinical trial within 30 days of the screening visit; Anticipated inability to attend scheduled study visits; Patients who in the judgment of the Investigator may be unreliable or uncooperative with the evaluation procedure outlined in this protocol; Patients with a history of prior pharmacogenomic testing; Any change in psychotropic medication (including change in dosage) between screening and baseline; Patients who are known to be pregnant or lactating; Patients with a history of gastric bypass surgery.", "candidate_expression": "((ALT) AND (AST) AND (Anticipated inability to attend scheduled study visits) AND (DSM-IV-TR) AND (Delirium) AND (Dementia) AND (Participation in another clinical trial within 30 days of the screening visit) AND (Patients who are known to be pregnant or lactating) AND (Patients with a history of prior pharmacogenomic testing) AND (anticipated survival) AND (basal cell carcinoma) AND (except) AND (gastric bypass surgery) AND (hypothyroidism) AND (less than 6 months) AND (local) AND (more than 1 year) AND (psychotropic medication) AND (screening) AND (substance abuse) AND (three times the upper limit of normal) AND (thyroid medication) AND (unless) AND (unstable) AND (within 1 year prior to screening) AND (without) AND ((suicidal risk) OR (violence)) AND ((alanine aminotransferase) OR (aspartate aminotransferase)) AND ((cirrhosis of the liver) OR (hepatic insufficiency) OR (liver transplant)) AND ((chemotherapy) OR (malignancy)) AND ((metastasis) OR (recurrence)) AND ((life threatening disease) OR (medical condition)) AND ((Amnestic disorder) OR (cognitive disorder)))"}
{"candidate_id": "LLM07178", "doc_id": "NCT03140488_exc", "case_bucket": "or", "source_criterion": "Non-reassuring fetal assessment at the time of recruitment Previous cervical ripening agents (cytotec, cervidil, cervical Foley Balloon) <18 years of age Prisoners Any patients contraindicated for vaginal delivery Multiple gestations History of previous cesarean delivery Patients with history of significant cardiac disease Fetal demise Estimated fetal weight greater than 4500 grams in diabetic and 5000 grams in non-diabetic mother Ruptured membranes Spontaneous labor (latent or active phase) Augmentation of labor (latent or active phase)", "candidate_expression": "((Augmentation of labor latent phase active phase) AND (Estimated fetal weight) AND (Fetal demise) AND (Multiple gestations) AND (Prisoners) AND (Ruptured membranes) AND (Spontaneous labor latent phase active phase) AND (age <18 years) AND (cardiac disease history significant) AND (cervical Foley Balloon) AND (cervical ripening agents Previous) AND (cervidil) AND (cesarean delivery History previous) AND (contraindicated) AND (cytotec) AND (diabetic greater than 4500 grams) AND (fetal assessment Non-reassuring at the time of recruitment) AND (vaginal delivery) AND NOT (diabetic 5000 grams))"}
{"candidate_id": "LLM07179", "doc_id": "NCT02644629_exc", "case_bucket": "or", "source_criterion": "Active or past psychotic disorder, including a history of psychotic affective state Mental Retardation or Autistic Spectrum Disorder Prominent personality disorder Cardiac or neurologic active medical condition, including past CVA/TIA (Cardiovascular Accident/Transient Ischemic Attack) or any other unstable medical condition. Chronic nasal congestion Active or recent drug or alcohol abuse Substantial suicidality in a patient requiring admission but refuses to do so, and signs an \"against medical advice\" release form as part of clinical evaluation, and does not answer the terms for involuntary admission.", "candidate_expression": "((Autistic Spectrum Disorder) AND (CVA) AND (Cardiac active medical condition) AND (Cardiovascular Accident) AND (Mental Retardation) AND (Prominent personality disorder) AND (TIA) AND (Transient Ischemic Attack) AND (admission) AND (alcohol abuse) AND (drug abuse) AND (medical condition unstable) AND (nasal congestion Chronic Active recent) AND (neurologic active medical condition) AND (psychotic affective state) AND (psychotic disorder Active past) AND (suicidality Substantial))"}
{"candidate_id": "LLM07180", "doc_id": "NCT01709981_exc", "case_bucket": "or", "source_criterion": "Plan for diagnostic-only coronary angiography On colchicine chronically History of intolerance to colchicine Glomerular filtration rate <30mL/minute or on dialysis Active malignancy or infection History of myelodysplasia High-dose statin load <24 hours prior to procedure Use of oral steroids or non-steroidal anti-inflammatory agents other than aspirin within 72 hours or 3 times the agent's half-life (whichever is longer) Use of strong CYP3A4/P-glycoprotein inhibitors (specifically ritonavir, ketoconazole, clarithromycin, cyclosporine, diltiazem and verapamil) Unable to consent Participating in a competing study", "candidate_expression": "((Glomerular filtration rate <30mL/minute) AND (High-dose statin <24 hours prior to procedure) AND (clarithromycin) AND (colchicine) AND (colchicine chronically) AND (coronary angiography diagnostic-only) AND (cyclosporine) AND (dialysis) AND (diltiazem) AND (infection) AND (intolerance) AND (ketoconazole) AND (malignancy Active) AND (myelodysplasia) AND (non-steroidal anti-inflammatory agents) AND (oral steroids) AND (ritonavir) AND (strong CYP3A4/P-glycoprotein inhibitors) AND (verapamil) AND NOT (aspirin within 72 hours within 3 times the agent's half-life))"}
{"candidate_id": "LLM07181", "doc_id": "NCT02783859_exc", "case_bucket": "or", "source_criterion": "Current wheeze Underlying chronic illness other than asthma (e.g. bronchiectasis, cyanotic congenital heart disease or cardiac failure, neuromuscular disorders, immunodeficiency) that could potentially influence the current illness Severe malnutrition (weight-for-height Z-score <-3) Complicated (effusion, empyema or abscess) pneumonia, including tuberculosis Extra-pulmonary infection requiring antibiotic therapy (e.g. meningitis) Beta-lactam allergy Previously enrolled Lack a mobile phone and/or unable to return for follow-up clinic visits during the next 24 months", "candidate_expression": "((Beta-lactam) AND (Complicated pneumonia) AND (Lack a mobile phone and/or unable to return for follow-up clinic visits during the next 24 months) AND (Previously enrolled) AND (allergy) AND (antibiotic therapy) AND (chronic illness) AND (infection Extra-pulmonary) AND (malnutrition Severe) AND (meningitis) AND (tuberculosis) AND (weight-for-height Z-score <-3) AND (wheeze) AND NOT (asthma) AND ((abscess) OR (effusion) OR (empyema)) AND ((bronchiectasis) OR (cardiac failure) OR (cyanotic congenital heart disease) OR (immunodeficiency) OR (neuromuscular disorders)))"}
{"candidate_id": "LLM07182", "doc_id": "NCT03363295_inc", "case_bucket": "other", "source_criterion": "Any patients that will be submitted to phacoemulsification surgery in the Hospital de Clinicas of State University of Campinas (BRAZIL) Patients over 18 years old Patients who are able to perform SD-OCT Patients who sign the consent form", "candidate_expression": "((Hospital de Clinicas of State University of Campinas (BRAZIL)) AND (Patients who sign the consent form) AND (SD-OCT able to perform) AND (old over 18 years) AND (phacoemulsification surgery will be submitted to))"}
{"candidate_id": "LLM07183", "doc_id": "NCT00440245_inc", "case_bucket": "or", "source_criterion": "asthma or COPD", "candidate_expression": "((COPD) AND (asthma))"}
{"candidate_id": "LLM07184", "doc_id": "NCT02613039_inc", "case_bucket": "other", "source_criterion": "Female subjects aged =/> 18 years and of reproductive age. Capacity to give consent for study participation, after being adequately informed of the aims, benefits, risks, time and motion of the study.", "candidate_expression": "((=/> 18 years) AND (Female) AND (aged) AND (reproductive age))"}
{"candidate_id": "LLM07185", "doc_id": "NCT03177837_inc", "case_bucket": "or", "source_criterion": "Male and female patients, age 18-75 yrs. COPD diagnosed according to GOLD, FEV1 40-80% predicted, SpO2 =92% at 750 m. Born, raised and currently living at low altitude (<800m). Written informed consent.", "candidate_expression": "((COPD GOLD) AND (FEV1 40-80% predicted) AND (SpO2 =92% 750 m) AND (Written informed consent.) AND (age 18-75 yrs) AND (living at low altitude <800m) AND ((Male) OR (female)))"}
{"candidate_id": "LLM07186", "doc_id": "NCT03495609_inc", "case_bucket": "other", "source_criterion": "premenopausal women BRCA1 carrier", "candidate_expression": "((BRCA1 carrier) AND (premenopausal) AND (women))"}
{"candidate_id": "LLM07187", "doc_id": "NCT01684501_inc", "case_bucket": "other", "source_criterion": "weigh more than 200 lbs are high level ambulators corresponding to levels E to F of the Special Interest Group of Amputee Medicine (SIGAM) mobility grade have the ability to follow multi-step commands.", "candidate_expression": "((Special Interest Group of Amputee Medicine (SIGAM) mobility grade levels E to F) AND (ability to follow multi-step commands) AND (high level ambulators) AND (weigh more than 200 lbs))"}
{"candidate_id": "LLM07188", "doc_id": "NCT02299947_exc", "case_bucket": "or", "source_criterion": "Prior trombosis or myocardial infarction, congenital coagulation disorder, use of anti-coagulants prior to surgery, prior thoracic surgery, pregnancy, pre-operative fibrinogen concentration <1g/L", "candidate_expression": "((<1g/L) AND (Prior) AND (anti-coagulants) AND (congenital coagulation disorder) AND (fibrinogen concentration) AND (myocardial infarction) AND (pre-operative) AND (pregnancy) AND (prior) AND (prior to surgery) AND (thoracic surgery) AND (trombosis))"}
{"candidate_id": "LLM07189", "doc_id": "NCT02635893_inc", "case_bucket": "or", "source_criterion": "Male and females between ages 18-85 years of age SCI ( =1 month of injury) ASIA A, B,C and D SCI above L5 Able to perform a visible contraction with dorsiflexor and hip flexor muscles (allowing testing of largely impaired patients) Able to ambulate a few steps with or without an assistive device Male and females between ages 18-85 years of age Able to walk and complete lower-limb tests with both legs", "candidate_expression": "((=1 month of injury) AND (A, B,C and D) AND (ASIA) AND (Able to ambulate a few steps) AND (SCI) AND (above L5) AND (ages) AND (between 18-85 years of age) AND (with both legs) AND ((Male) OR (females)) AND ((females) OR (l)) AND ((with assistive device) OR (without an assistive device)) AND ((Able to complete lower-limb tests) OR (Able to walk)))"}
{"candidate_id": "LLM07190", "doc_id": "NCT02330757_inc", "case_bucket": "scope", "source_criterion": "Women without PCOS as defined by the Rotterdam criteria. Presence of at least 2 cryopreserved good quality cleavage-stage embryo (good quality cleavage-stage embryos display stage-specific cell division, have blastomeres of fairly equal size with few to no cytoplasmic fragments).", "candidate_expression": "((cleavage-stage embryo at least 2 cryopreserved good quality) AND (cleavage-stage embryos good quality stage-specific cell division have blastomeres of fairly equal size) AND (few to no cytoplasmic fragments) AND NOT (PCOS Rotterdam criteria))"}
{"candidate_id": "LLM07191", "doc_id": "NCT03624881_inc", "case_bucket": "or", "source_criterion": "Symptomatic paroxysmal AF who had at least one AF episode electrocardiographically documented within one (1) year prior to enrollment. Documentation may include electrocardiogram (ECG); Transtelephonic monitoring (TTM), Holter monitor or telemetry strip Failed at least one antiarrhythmic drug (AAD) (Class I or III antiarrhythmic drugs) as evidenced by recurrent symptomatic AF, or intolerable to the AAD Age 18 years or older Signed Patient Informed Consent Form (ICF) Able and willing to comply with all pre-, post-, and follow-up testing and requirements", "candidate_expression": "((AAD) AND (AF episode at least one electrocardiographically documented within one (1) year prior to enrollment) AND (Age 18 years or older) AND (Class I antiarrhythmic drugs) AND (Holter monitor) AND (III antiarrhythmic drugs) AND (Signed Patient Informed Consent Form (ICF)) AND (Transtelephonic monitoring (TTM)) AND (antiarrhythmic drug (AAD) at least one) AND (electrocardiogram (ECG)) AND (electrocardiographically) AND (intolerable) AND (paroxysmal AF Symptomatic) AND (recurrent symptomatic AF) AND (telemetry strip))"}
{"candidate_id": "LLM07192", "doc_id": "NCT03497598_exc", "case_bucket": "or", "source_criterion": "UTIs = 12 within 1 year Pregnancy or Lactation Immune disease Lactose intolerance Urinary tract anomaly Systemic infection Newly started hormone therapy within the last 6 months Antibiotic prophylaxis within the last 6 months a-D-mannose intake within the last month Use of catheters Diabetes mellitus Participation to other studies", "candidate_expression": "((12 within 1 year) AND (Antibiotic) AND (Antibiotic prophylaxis) AND (Diabetes mellitus) AND (Immune disease) AND (Lactose) AND (Lactose intolerance) AND (Newly started) AND (Participation to other studies) AND (Systemic infection) AND (UTIs) AND (Urinary tract anomaly) AND (a-D-mannose) AND (catheters) AND (hormone therapy) AND (intolerance) AND (within 1 year) AND (within the last 6 months) AND (within the last month) AND ((Lactation) OR (Pregnancy)))"}
{"candidate_id": "LLM07193", "doc_id": "NCT02019628_inc", "case_bucket": "or", "source_criterion": "1. Women and men ages 18 years and over. 2. Interest in participating in a novel nutritional supplement program. 3. Willingness to follow recommendations.", "candidate_expression": "((Interest in participating in a novel nutritional supplement program.) AND (Willingness to follow recommendations.) AND (Women) AND (ages 18 years and over) AND (men))"}
{"candidate_id": "LLM07194", "doc_id": "NCT03089086_inc", "case_bucket": "or", "source_criterion": "South Australian secondary school students in years 10, 11, and 12 in 2017 Written parental consent for those under the age of 18 Written student consent assent for those under the age of 18 (or if 18 years old and older consent for themselves) Available at school for at least the first pharyngeal swab and willing to comply with study procedures", "candidate_expression": "((South Australian) AND (Written parental consent for those under the age of 18) AND (Written student consent assent for those under the age of 18 (or if 18 years old and older consent for themselves)) AND (comply with study procedures willing to) AND (pharyngeal swab first) AND (secondary school students in 2017 years 10 years 11 years 12))"}
{"candidate_id": "LLM07195", "doc_id": "NCT02783859_exc", "case_bucket": "or", "source_criterion": "Current wheeze Underlying chronic illness other than asthma (e.g. bronchiectasis, cyanotic congenital heart disease or cardiac failure, neuromuscular disorders, immunodeficiency) that could potentially influence the current illness Severe malnutrition (weight-for-height Z-score <-3) Complicated (effusion, empyema or abscess) pneumonia, including tuberculosis Extra-pulmonary infection requiring antibiotic therapy (e.g. meningitis) Beta-lactam allergy Previously enrolled Lack a mobile phone and/or unable to return for follow-up clinic visits during the next 24 months", "candidate_expression": "((<-3) AND (Beta-lactam) AND (Complicated pneumonia) AND (Extra-pulmonary) AND (Lack a mobile phone and/or unable to return for follow-up clinic visits during the next 24 months) AND (Previously enrolled) AND (Severe) AND (allergy) AND (antibiotic therapy) AND (asthma) AND (chronic illness) AND (infection) AND (malnutrition) AND (meningitis) AND (other) AND (tuberculosis) AND (weight-for-height Z-score) AND (wheeze) AND ((abscess) OR (effusion) OR (empyema)) AND ((bronchiectasis) OR (cardiac failure) OR (cyanotic congenital heart disease) OR (immunodeficiency) OR (neuromuscular disorders)))"}
{"candidate_id": "LLM07196", "doc_id": "NCT03536520_inc", "case_bucket": "or", "source_criterion": "Healthy men and women, age 40-75 yrs, without any disease and need of medication. Born, raised and currently living at low altitude (<800m). Written informed consent. Kyrgyz ethnicity", "candidate_expression": "((Written informed consent) AND (age 40-75 yr 40-75 yr) AND NOT (disease any) AND NOT (medication) AND ((men) OR (women)))"}
{"candidate_id": "LLM07197", "doc_id": "NCT03297021_exc", "case_bucket": "or", "source_criterion": "Patients with allergies or contraindications to study medications", "candidate_expression": "((allergies) AND (contraindications) AND (study medications))"}
{"candidate_id": "LLM07198", "doc_id": "NCT01907230_exc", "case_bucket": "or", "source_criterion": "HCV, HIV, or HDV coinfection. HCC or other malignancy within 3 years. Decompensated liver cirrhosis (CTP score = 7). Uremia patients under hemodialysis or continuous ambulatory peritoneal dialysis or patients with Ccr < 50 mL/min Pregnant or breastfeeding women. Women of child-bearing potential (WOCBP) who are unwilling or unable to use an acceptable method of contraception to avoid pregnancy throughout the study and for up to 4 weeks after the last dose of study drug.", "candidate_expression": "((CTP score = 7) AND (Ccr < 50 mL/min) AND (Decompensated liver cirrhosis) AND (Pregnant or breastfeeding women) AND (Uremia) AND (Women of child-bearing potential (WOCBP) who are unwilling or unable to use an acceptable method of contraception to avoid pregnancy throughout the study and for up to 4 weeks after the last dose of study drug) AND ((HCV coinfection) OR (HDV coinfection) OR (coinfection HIV)) AND ((continuous ambulatory peritoneal dialysis) OR (hemodialysis)) AND ((HCC) OR (malignancy)))"}
{"candidate_id": "LLM07199", "doc_id": "NCT02473809_inc", "case_bucket": "other", "source_criterion": "Informed consent Diagnosis of type 2 diabetes (HbA1c > 48 mmol/mol) Age older than 30 years", "candidate_expression": "((Age older than 30 years) AND (HbA1c > 48 mmol/mol) AND (Informed consent) AND (type 2 diabetes))"}
{"candidate_id": "LLM07200", "doc_id": "NCT01446094_exc", "case_bucket": "other", "source_criterion": "Inability to give informed consent Possible pregnancy (confirmed by urine test) Women who are breastfeeding Severe claustrophobia Inability to lie flat for 20-30 minutes (the anticipated amount of time to complete the MRI procedure) Individuals with cochlear implants Individuals with non-MRI compatible aneurysm clips Potential contraindications to regadenoson use due to: Contraindication to administration of Gadolinium (Gd) based contrast agents (GBCA):", "candidate_expression": "((Contraindication) AND (Gadolinium (Gd) based contrast agents (GBCA)) AND (Inability to give informed consent) AND (Inability to lie flat 20-30 minutes amount of time to complete the MRI procedure) AND (Women) AND (aneurysm clips MRI compatible) AND (breastfeeding) AND (claustrophobia Severe) AND (cochlear implants) AND (pregnancy Possible) AND (urine test confirmed))"}
```
