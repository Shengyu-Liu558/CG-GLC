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
{"candidate_id": "LLM00351", "doc_id": "NCT02842424_inc", "case_bucket": "or", "source_criterion": "A positive history of chronic claudication, Exercise-limiting claudication established by history and direct observation during a screening walking test administered by the evaluating vascular surgeon, Arterial occlusive disease per ankle Brachial index measurements and/or other imaging modalities, Stable blood pressure regimen, stable lipid regimen, stable diabetes regimen and risk factor control for 6 weeks.", "candidate_expression": "((Arterial occlusive disease) AND (Exercise-limiting claudication) AND (Stable) AND (ankle Brachial index measurements) AND (blood pressure regimen) AND (chronic claudication) AND (diabetes regimen) AND (direct observation) AND (for 6 weeks) AND (history) AND (imaging modalities) AND (lipid regimen) AND (positive history) AND (risk factor control) AND (screening walking test) AND (stable))"}
{"candidate_id": "LLM00352", "doc_id": "NCT02490839_exc", "case_bucket": "or", "source_criterion": "pregnant or nursing woman serious concomitant illness and malignant tumor of any kind history of hypersensitivity to test drugs serious bleeding during the course of the ulcer previous gastric surgery receiving bismuth salts, PPIs, or antibiotics in the previous month.", "candidate_expression": "((bleeding serious during the course of the ulcer) AND (gastric surgery previous) AND (hypersensitivity history) AND (illness serious concomitant) AND (malignant tumor any kind) AND (test drugs) AND (ulcer) AND (woman) AND ((nursing) OR (pregnant)) AND ((PPIs) OR (antibiotics) OR (bismuth salts)))"}
{"candidate_id": "LLM00353", "doc_id": "NCT02357654_inc", "case_bucket": "or", "source_criterion": "women undergoing IVF/ICSI or frozen embryo transfers (FET) that less than 40 years old.", "candidate_expression": "((less than 40 years) AND (old) AND (women) AND ((ICSI) OR (IVF) OR (frozen embryo transfers (FET))))"}
{"candidate_id": "LLM00354", "doc_id": "NCT02979561_exc", "case_bucket": "or", "source_criterion": "Signs of hemodynamic instability (i.e. systolic blood pressure <100 mm Hg.St. or episode of systolic blood pressure fall for =40 mm Hg. / or heart rate > 110 lasting more than 15 min) or need for ventilatory support within 12 hours prior to randomisation. The indication for oral anticoagulation, associated with others disease. malignant neoplasm of any location Contraindications to warfarin or pradaxa according to Russian Instructions for medical use of these drugs Indications for concomitant treatment with antiplatelet agents Any stroke within 6 months before randomization Intracranial hemorrhage in anamnesis Active bleeding, bleeding diathesis. Clinically significant bleeding within the last 30 days. Trauma or extensive surgery within 1 month before randomization or surgery planned in the next 6 months after randomization. Intracranial pathology: tumor, arteriovenous fistula or aneurysm. Gastrointestinal bleeding in the previous 3 months. Gastric ulcer or duodenal ulcer with clinical manifestations or endoscopically identified acute ulcer without signs of scarring during previous 30 days. Uncontrolled hypertension (systolic blood pressure> 180 mm Hg. and / or diastolic blood pressure> 100 mm.hg in patients receiving antihypertensive drugs). Pregnancy, lactation. Life expectancy <6 months. Clinically significant liver disease. Creatinine clearance (estimated by Cockcroft-Gault) <30 ml / min. hemoglobin level <90 g/l), thrombocytopenia <100x10^9 / L. Patients who, in the opinion of the researcher, are not suitable for inclusion in the study, for example, due to the low likelihood of doctor's recommendations following. Long-term use of NSAIDs Current participation in another clinical study. Allergic to contrast substance or radioisotope drugs used in procedures to assess endpoints of the study, which according to researchers, may be a contraindication to the implementation of these research methods.", "candidate_expression": "((Allergic) AND (Contraindications Russian Instructions for medical use) AND (Creatinine clearance Cockcroft-Gault <30 ml / min) AND (Gastrointestinal bleeding in the previous 3 months) AND (Intracranial hemorrhage) AND (Intracranial pathology) AND (Life expectancy <6 months) AND (NSAIDs Long-term use) AND (Pregnancy) AND (anamnesis) AND (antihypertensive drugs) AND (antiplatelet agents Indications concomitant) AND (bleeding Clinically significant within the last 30 days) AND (clinical manifestations) AND (endoscopically) AND (hemoglobin level <90 g/l) AND (hypertension Uncontrolled) AND (lactation) AND (liver disease Clinically significant) AND (neoplasm malignant) AND (oral anticoagulation indication for) AND (stroke within 6 months before randomization) AND (surgery planned in the next 6 months after randomization) AND (thrombocytopenia <100x10^9 / L) AND NOT (signs of scarring) AND ((hemodynamic instability) OR (ventilatory support need for within 12 hours prior to randomisation)) AND ((pradaxa) OR (warfarin)) AND ((bleeding Active) OR (bleeding diathesis)) AND ((Trauma) OR (extensive surgery)) AND ((aneurysm) OR (arteriovenous fistula) OR (tumor)) AND ((Gastric ulcer) OR (acute ulcer endoscopically identified during previous 30 days) OR (duodenal ulcer)) AND ((heart rate > 110 lasting more than 15 min) OR (systolic blood pressure <100 mm Hg.St.) OR (systolic blood pressure fall =40 mm Hg)) AND ((diastolic blood pressure > 100 mm.hg) OR (systolic blood pressure > 180 mm Hg)) AND ((contrast substance) OR (radioisotope drugs)))"}
{"candidate_id": "LLM00355", "doc_id": "NCT01236417_exc", "case_bucket": "or", "source_criterion": "Inability to comply with study requirements. Metastatic breast cancer. Patients with orthopedic or neuromuscular disorders that preclude participation in exercise. Rheumatoid arthritis. History of MI, angina or congestive heart failure. Pregnant or lactating females. Patients that are high risk for moderate exercise based on ACSM risk classification. Patients who exceed minimal physical activity recommendations from the US Surgeon General's Report: Accumulation of 30 minutes or more of moderate physical activity on most days of the week. Morbidly obese with BMI ≥ 40", "candidate_expression": "((ACSM risk classification) AND (BMI) AND (History) AND (Inability to comply with study requirements.) AND (MI) AND (Metastatic) AND (Morbidly obese) AND (Pregnant) AND (Pregnant or lactating females.) AND (Rheumatoid arthritis) AND (angina) AND (breast cancer) AND (congestive heart failure) AND (disorders orthopedic) AND (exceed minimal physical activity recommendations) AND (females) AND (high) AND (lactating) AND (neuromuscular disorders) AND (risk for moderate exercise) AND (≥ 40))"}
{"candidate_id": "LLM00356", "doc_id": "NCT00279552_inc", "case_bucket": "other", "source_criterion": "Patients suspected to have vitamin B12 deficiency defined as a plasma vitamin B12 below the reference interval (<200 pmol/L).", "candidate_expression": "((plasma vitamin B12 below the reference interval <200 pmol/L) AND (vitamin B12 deficiency suspected))"}
{"candidate_id": "LLM00357", "doc_id": "NCT02732080_inc", "case_bucket": "or", "source_criterion": "Patients presenting with ST-elevation acute myocardial infarction (STEMI) within 12 hours of their symptom onset in whom TIMI-3 flow was established in infarct related artery (IRA) after balloon angioplasty or thrombectomy.", "candidate_expression": "((ST-elevation acute myocardial infarction (STEMI) within 12 hours of their symptom onset) AND (TIMI-3 flow was established infarct related artery (IRA) after balloon angioplasty or thrombectomy) AND ((balloon angioplasty) OR (thrombectomy)))"}
{"candidate_id": "LLM00358", "doc_id": "NCT03177811_inc", "case_bucket": "or", "source_criterion": "Male and female patients, age 18-75 yrs. COPD diagnosed according to GOLD, FEV1 40-80% predicted, SpO2 =92% at 750 m. Born, raised and currently living at low altitude (<800m). Written informed consent.", "candidate_expression": "((18-75 yrs) AND (40-80% predicted) AND (=92% at 750 m) AND (COPD) AND (FEV1) AND (GOLD) AND (SpO2) AND (Written informed consent) AND (age) AND ((Male) OR (female)))"}
{"candidate_id": "LLM00359", "doc_id": "NCT03461679_exc", "case_bucket": "other", "source_criterion": "Unable to consent Chronic opioid consumption Allergy to study medication Lower limb surgery preceding year Unable to complete baseline testing, pre-existing neurological deficit Contraindication to spinal anaesthesia", "candidate_expression": "((Allergy) AND (Contraindication) AND (Lower limb surgery) AND (Unable to consent) AND (neurological deficit pre-existing) AND (opioid consumption Chronic) AND (spinal anaesthesia) AND (study medication))"}
{"candidate_id": "LLM00360", "doc_id": "NCT00625742_inc", "case_bucket": "other", "source_criterion": "1. Are referred to the Cachexia Clinic with involuntary weight loss of >5% of their premorbid weight within the previous 6 months. 2. Are 18 years of age or older 3. Have a Karnofsky performance score of 60 or higher. 4. Can maintain oral food intake during the study 5. Can understand the study procedures and can sign an informed consent form. 6. Are not currently taking melatonin. 7. Are taking megestrol acetate and continue to lose weight despite at least 2 weeks of therapy. 8. Have a calculated creatinine clearance of >/= 60 cc/min.", "candidate_expression": "((18 years or older) AND (60 or higher) AND (>/= 60 cc/min) AND (>5% of their premorbid weight) AND (Are taking) AND (Cachexia Clinic) AND (Karnofsky performance score) AND (at least 2 weeks) AND (calculated creatinine clearance) AND (continue) AND (currently) AND (involuntary weight loss) AND (lose weight) AND (megestrol acetate) AND (melatonin) AND (not) AND (of age) AND (therapy) AND (within the previous 6 months))"}
{"candidate_id": "LLM00361", "doc_id": "NCT02034019_exc", "case_bucket": "other", "source_criterion": "Any intraocular inflammation in the study eye present during the screening slit lamp examination Score greater than \"0\" on the Ocular Pain Assessment in the study eye at Screening Any intraocular inflammation in the study eye present during the screening slit lamp examination", "candidate_expression": "((Ocular Pain Assessment) AND (at Screening) AND (during the screening slit lamp examination) AND (greater than \"0\") AND (intraocular inflammation) AND (slit lamp examination) AND (the screening slit lamp examination))"}
{"candidate_id": "LLM00362", "doc_id": "NCT00317148_inc", "case_bucket": "other", "source_criterion": "Healthy postmenopausal women with 50 or more moderate to severe hot flushes. Women between 40 to 70 years of age.", "candidate_expression": "((50 or more) AND (Healthy) AND (Women) AND (age) AND (between 40 to 70 years) AND (moderate to severe hot flushes) AND (postmenopausal) AND (women))"}
{"candidate_id": "LLM00363", "doc_id": "NCT02691793_exc", "case_bucket": "or", "source_criterion": "Patients with second primary cancer, except:adequately treated non-melanoma skin cancer, curatively treated in-situ cancer of the cervix, or other solid tumor curatively treated with no evidence of disease for <= 5 years. Has known active central nervous system(CNS) metastases Has an active infection requiring systemic therapy Pregnancy or breast feeding Patients with cardiac problem Any previous treatment with sunitinib", "candidate_expression": "((Pregnancy or breast feeding) AND (active infection) AND (cardiac problem) AND (metastases central nervous system CNS) AND (primary cancer, second) AND (solid tumor) AND (sunitinib) AND ((in-situ cancer of the cervix treated) OR (non-melanoma skin cancer treated)))"}
{"candidate_id": "LLM00364", "doc_id": "NCT01117181_exc", "case_bucket": "or", "source_criterion": "Meets criteria for Major Depressive Episode, by Diagnostic Statistical Manual of Mental Disorder - IV (TR) criteria Clinically significant agitation /aggression for which either 1) the frequency of agitation /aggression as assessed by the NPI is 'Very frequently', or 2) the frequency of agitation /aggression as assessed by the NPI is 'Frequently' AND the severity of the agitation as assessed by the NPI is 'Moderate', or 'Marked' Clinically significant delusions for which either 1) the frequency of delusions as assessed by the NPI is 'Very frequently', or 2) the frequency of delusions as assessed by the NPI is 'Frequently' AND the severity of the delusions as assessed by the NPI is 'Moderate', or 'Marked' Clinically significant hallucinations for which either 1) the frequency of hallucinations as assessed by the NPI is 'Very frequently', or 2) the frequency of hallucinations as assessed by the NPI is 'Frequently' AND the severity of the hallucinations as assessed by the NPI is 'Moderate', or 'Marked' Treatment with psychotropic medications in the 2 weeks prior to randomization with the exception of approved treatments for dementia (ChEIs and memantine), selective serotonin reuptake inhibitor antidepressants, and trazodone (if used as an aid to facilitate sleep and not as an antidepressant); other psychotropics (with the exclusion of antipsychotics), if stable for 3 months, may be allowed only with Steering Committee approval on a case by case basis. Note that antipsychotics are expressly prohibited. Treatment with methylphenidate is contraindicated in the opinion of the study physician Failure of treatment with methylphenidate in the past for apathy after convincing evidence of an adequate trial as judged by study physician Treatment with a medication that would prohibit the safe concurrent use of methylphenidate such as monoamine oxidase inhibitors and tricyclic antidepressants Need for acute psychiatric hospitalization or is suicidal Uncontrolled hypertension (medication non-compliance or past 3 months with a diastolic reading of 105 as verified by compartment pressure of the rectus sheath (CPRS)) Symptomatic coronary artery disease deemed to be significant by study physician at the time of screening Lack of appetite that results in significant unintentional weight loss as determined by the study physician in the last three months Significant communicative impairments Current participation in a clinical trial or in any study that may add significant burden or affect study outcomes Hyperthyroidism, advanced arteriosclerosis, symptomatic cardiovascular disease, serious structural cardiac abnormalities, cardiomyopathy, serious heart rhythm abnormalities, or a family history of sudden death or death related to heart problems Glaucoma, pheochromocytoma, or known or suspected hypersensitivity to methylphenidate or its excipients Central Nervous System (CNS) abnormalities (e.g., cerebral aneurysm) and/or other vascular abnormalities such as vasculitis or pre-existing stroke, motor tics or a family history or diagnosis of Tourette's syndrome, seizures (convulsions, epilepsy), or abnormal EEGs Any condition that, in the opinion of the study physician, makes it medically inappropriate or risky for the patient to enroll in the trial", "candidate_expression": "((Any condition that, in the opinion of the study physician, makes it medically inappropriate or risky for the patient to enroll in the trial) AND (ChEIs) AND (Current participation in a clinical trial or in any study that may add significant burden or affect study outcomes) AND (Diagnostic Statistical Manual of Mental Disorder - IV (TR) criteria Meets) AND (Lack of appetite in the last three months at the time of screening) AND (Major Depressive Episode) AND (NPI) AND (NPI Frequently) AND (NPI Very frequently) AND (Uncontrolled hypertension Uncontrolled) AND (agitation) AND (agitation /aggression) AND (agitation /aggression Clinically significant) AND (as judged by study physician) AND (cerebral aneurysm) AND (communicative impairments Significant) AND (compartment pressure of the rectus sheath (CPRS)) AND (coronary artery disease Symptomatic) AND (delusions) AND (delusions Clinically significant) AND (dementia) AND (diastolic reading 105 as verified by compartment pressure of the rectus sheath (CPRS)) AND (hallucinations) AND (hallucinations Clinically significant frequency of hallucinations) AND (medication non-compliance past 3 months) AND (medication that would prohibit the safe concurrent use of methylphenidate) AND (memantine) AND (methylphenidate) AND (methylphenidate prohibit concurrent) AND (unintentional weight loss significant as determined by the study physician) AND (vasculitis) AND NOT (antipsychotics) AND ((Hyperthyroidism) OR (arteriosclerosis advanced) OR (cardiomyopathy) OR (cardiovascular disease symptomatic) OR (heart rhythm abnormalities serious) OR (structural cardiac abnormalities serious)) AND ((death related to heart problems related to heart problems) OR (sudden death)) AND ((Glaucoma) OR (hypersensitivity) OR (pheochromocytoma)) AND ((its excipients) OR (methylphenidate or its excipients)) AND ((known) OR (suspected)) AND ((Central Nervous System (CNS) abnormalities) OR (EEGs abnormal) OR (Tourette's syndrome) OR (motor tics) OR (seizures) OR (stroke pre-existing) OR (vascular abnormalities)) AND ((convulsions) OR (epilepsy)) AND ((diagnosis) OR (family history)) AND ((Marked) OR (Moderate)) AND ((frequency of delusions) OR (severity of the delusions)) AND ((frequency of hallucinations) OR (severity of the hallucinations)) AND ((selective serotonin reuptake inhibitor antidepressants) OR (trazodone) OR (treatments for dementia)) AND ((other psychotropics stable) OR (psychotropic medications in the 2 weeks prior to randomization)) AND ((frequency of agitation /aggression) OR (severity of the agitation)) AND ((monoamine oxidase inhibitors) OR (tricyclic antidepressants)) AND ((psychiatric hospitalization Need for acute) OR (suicidal)))"}
{"candidate_id": "LLM00365", "doc_id": "NCT02950558_inc", "case_bucket": "other", "source_criterion": "Referred for surgery for open reduction and internal fixation for ankle fracture", "candidate_expression": "((ankle fracture) AND (open reduction and internal fixation) AND (surgery))"}
{"candidate_id": "LLM00366", "doc_id": "NCT03154931_inc", "case_bucket": "other", "source_criterion": "Clinical Administered PTSD Scale 5 Monthly version Criteria A and >30 points", "candidate_expression": "((>30 points) AND (Clinical Administered PTSD Scale) AND (Criteria A))"}
{"candidate_id": "LLM00367", "doc_id": "NCT01205334_exc", "case_bucket": "or", "source_criterion": "Severe intercurrent infection Known HIV positivity Pregnant or lactating History of hypersensitivity reactions to murine protein-containing products.", "candidate_expression": "((HIV positivity) AND (Severe) AND (hypersensitivity reactions) AND (infection) AND (intercurrent) AND (murine) AND (murine protein-containing products) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM00368", "doc_id": "NCT02570230_inc", "case_bucket": "other", "source_criterion": "ASA physical status 1-3 elective thoracotomy can operate patient-controlled analgesia (PCA) machine", "candidate_expression": "((ASA physical status 1-3) AND (thoracotomy elective))"}
{"candidate_id": "LLM00369", "doc_id": "NCT03407625_exc", "case_bucket": "other", "source_criterion": "latex allergy non-reassuring fetal status HIV active herpes outbreak Prior uterine scar Contraindication to prostaglandins according to current Parkland protocol Contraindication to vaginal delivery", "candidate_expression": "((Contraindication) AND (HIV) AND (Parkland protocol) AND (active) AND (allergy) AND (fetal status) AND (herpes) AND (latex) AND (non-reassuring) AND (prostaglandins) AND (uterine scar) AND (vaginal delivery))"}
{"candidate_id": "LLM00370", "doc_id": "NCT03467750_inc", "case_bucket": "or", "source_criterion": "Diagnosis of sleep disordered breathing or obstructive sleep apnea Children undergoing elective tonsillectomy or adenotonsillectomy at Children's Healthcare of Atlanta Egleston location Parent or legal guardian willing to participate, and able to understand and sign the provided informed consent", "candidate_expression": "((Children) AND (Children's Healthcare of Atlanta Egleston) AND (Parent or legal guardian willing to participate, and able to understand and sign the provided informed consent) AND ((obstructive sleep apnea) OR (sleep disordered breathing)) AND ((adenotonsillectomy) OR (tonsillectomy)))"}
{"candidate_id": "LLM00371", "doc_id": "NCT02692651_inc", "case_bucket": "other", "source_criterion": "Patients 18 years of age or older with >3 unformed stools/24 hours with positive stool test for C. difficile. Patients receiving = 1 high or medium risk antibiotic for treatment of an infection other than CDI, for an anticipated duration of = 5 days from the time of enrollment.", "candidate_expression": "((24 hours) AND (>3) AND (C. difficile) AND (age) AND (or older 18 years) AND (positive) AND (stool test) AND (unformed stools))"}
{"candidate_id": "LLM00372", "doc_id": "NCT02958072_exc", "case_bucket": "or", "source_criterion": "Hemoglobin concentration under 6.5 mmol/l screening HBA1c more than 108 mmol/l Non-compliant with blood-letting Clinically infected ulcer Patient planned for or has had a revascularization procedure in the affected leg within the last 8 weeks The ulcer have been treated with growth factors in the last 8 weeks History of deep venous insufficiency, chronic venous leg ulcer or stasis dermatitis Breast-feeding women or fertile women not agreeing to use an effective method of contraception Participation in another clinical ulcer-healing study within the last 4 weeks Patient has previously been randomized in this study Judgement by the investigator that the patient is not able to participate in the study", "candidate_expression": "((Breast-feeding) AND (HBA1c more than 108 mmol/l) AND (Hemoglobin concentration under 6.5 mmol/l) AND (Judgement by the investigator that the patient is not able to participate in the study) AND (Non-compliant) AND (blood-letting) AND (chronic venous leg ulcer) AND (deep venous insufficiency) AND (fertile) AND (growth factors) AND (has had) AND (infected ulcer) AND (planned) AND (revascularization procedure affected leg within the last 8 weeks) AND (stasis dermatitis) AND (treated in the last 8 weeks) AND (ulcer) AND (women) AND (women agreeing to use an effective method of contraception))"}
{"candidate_id": "LLM00373", "doc_id": "NCT02557412_exc", "case_bucket": "or", "source_criterion": "Apnea-hypopnea index of less than 5 h-1 or greater than 30 h-1. Predominance of central apneas and hypopneas, defined as more than 25% of all respiratory events. Professional drivers, risk profession or respiratory failure (according to criteria of the clinical pathway for diagnosis and treatment of sleep-disordered breathing). Very excessive daytime sleepiness (Epworth Sleepiness Scale> 18). Morbid obesity (BMI> 40 kg / m2). Prior treatment with CPAP.", "candidate_expression": "((Apnea-hypopnea index less than 5 h-1 or greater than 30 h-1) AND (BMI > 40 kg / m2) AND (CPAP Prior) AND (Epworth Sleepiness Scale > 18) AND (Morbid obesity) AND (Predominance) AND (Professional drivers) AND (all respiratory events more than 25%) AND (central apneas and hypopneas) AND (criteria of the clinical pathway for diagnosis and treatment of sleep-disordered breathing) AND (daytime sleepiness Very excessive) AND (respiratory failure) AND (risk profession))"}
{"candidate_id": "LLM00374", "doc_id": "NCT03560310_inc", "case_bucket": "or", "source_criterion": "Written informed consent Age =18 years Has undergone first time isolated CABG due to an episode of acute coronary syndrome (STEMI, NSTEMI, unstable angina) within 6 weeks before surgery", "candidate_expression": "((=18 years) AND (Age) AND (Written informed consent) AND (acute coronary syndrome) AND (first time) AND (isolated CABG) AND (surgery) AND (within 6 weeks before surgery) AND ((NSTEMI) OR (STEMI) OR (unstable angina)))"}
{"candidate_id": "LLM00375", "doc_id": "NCT02692651_exc", "case_bucket": "or", "source_criterion": "Patients with severe-complicated disease that would compromise oral therapy (hypotenstion or shock, ileus or bowel obstruction, megacolon). Patients with an allergy to oral vancomycin or fidaxomicin. Patients anticipated to receive metronidazole after enrollment. Patients who already received oral vancomycin or metronidazole (either oral or intravenous) for > 24 hours within the preceding 72 hours at the time of enrollment. Patients anticipated to receive adjunctive C. difficile therapy (rifaxamin, nitazoxanide, tigecycline) after enrollment.", "candidate_expression": "((C. difficile therapy anticipated) AND (allergy) AND (bowel obstruction) AND (fidaxomicin) AND (hypotenstion) AND (ileus) AND (megacolon) AND (metronidazole anticipated) AND (metronidazole preceding 72 hours at the time of enrollment.) AND (nitazoxanide) AND (rifaxamin) AND (shock) AND (tigecycline) AND (vancomycin oral))"}
```
