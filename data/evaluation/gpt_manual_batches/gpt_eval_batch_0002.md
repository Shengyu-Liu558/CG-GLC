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
{"candidate_id": "LLM00026", "doc_id": "NCT03495557_exc", "case_bucket": "other", "source_criterion": "Conversion to laparotomy Emergent re intervention Immunosuppression Umbilical hernia", "candidate_expression": "((Conversion to) AND (Emergent) AND (Immunosuppression) AND (Umbilical hernia) AND (laparotomy) AND (re intervention))"}
{"candidate_id": "LLM00027", "doc_id": "NCT03008005_exc", "case_bucket": "or", "source_criterion": "clinically significant medical or neurologic condition or neurocognitive dysfunction that would affect function and/or task performance and/or interfere with the study protocol any current (or within past 2 months) medical condition requiring medication that would interact with dronabinol or interfere with the study protocol risk of harm to self or others that requires immediate intervention presence of contraindications, current or past allergic or adverse reaction, or known sensitivity to cannabinoid-like substances (dronabinol/marijuana/cannabis/THC, cannabinoid oil, sesame oil, gelatin, glycerin, and titanium dioxide) lack of fluency in English positive drug screen or alcohol breathalyzer unwilling/unable to sign informed consent document currently pregnant (positive pregnancy test), planning pregnancy, or lactating (women) under 18 or over 50 years of age traumatic brain injury (as defined by The American Congress of Rehabilitation as a person who has had a traumatically induced physiological disruption of brain function (i.e., the head being struck, the head striking an object, and/or the brain undergoing an acceleration/deceleration movement (i.e., whiplash) without direct external trauma to the head), as manifested by at least one of the following: any loss of consciousness; any loss of memory for events immediately before or after the injury; any alteration in mental status at the time of the incident; or focal neurological deficits that may or may not be transient) inability to tolerate small, enclosed spaces without anxiety (e.g. claustrophobia), as determined by self-report and/or a preliminary session in a mock scanner left-handed; presence of ferrous-containing metals within the body (e.g., aneurysm clips, shrapnel/retained particles) anticipation of a required drug test in the 4 weeks following the study. current diagnosis of a mood, anxiety, or other disorder that is more clinically salient than PTSD current moderate or severe alcohol/drug use disorder or in the past 8 weeks current or past diagnosis of bipolar and other related disorders, schizophrenia spectrum, or other psychotic disorders concomitant treatments with medication known to have drug interactions with dronabinol, such as, central nervous system depressants (barbiturates, benzodiazepines, buspirone, lithium, etc) and anticholinergic agents (atropine, scopolamine, antihistamines, etc).", "candidate_expression": "((PTSD moderate severe) AND (THC) AND (adverse reaction) AND (age under 18 or over 50 years) AND (alcohol breathalyzer) AND (alcohol use disorder) AND (allergic reaction) AND (aneurysm clips) AND (anticholinergic agents) AND (antihistamines) AND (anxiety disorder) AND (atropine) AND (barbiturates) AND (benzodiazepines) AND (bipolar) AND (buspirone) AND (cannabinoid oil) AND (cannabinoid-like substances) AND (cannabis) AND (central nervous system depressants) AND (claustrophobia) AND (contraindications current past) AND (disorder other) AND (dronabinol) AND (dronabinol would interact with interfere with the study protocol) AND (drug interactions) AND (drug screen) AND (drug test anticipation of in the 4 weeks following the study) AND (drug use disorder) AND (ferrous-containing metals) AND (gelatin) AND (glycerin) AND (lactating) AND (left-handed) AND (lithium) AND (marijuana) AND (medical condition) AND (medical condition current within past 2 months) AND (medication) AND (mood disorder) AND (neurocognitive dysfunction) AND (neurologic condition) AND (pregnancy planning) AND (pregnancy test positive) AND (pregnant currently) AND (psychotic disorders) AND (related disorders other) AND (retained particles) AND (schizophrenia spectrum) AND (scopolamine) AND (self-report) AND (sensitivity) AND (sesame oil) AND (shrapnel) AND (titanium dioxide) AND (traumatic brain injury) AND (treatments) AND (unwilling/unable to sign informed consent document) AND NOT (tolerate small, enclosed spaces without anxiety inability))"}
{"candidate_id": "LLM00028", "doc_id": "NCT01214096_exc", "case_bucket": "or", "source_criterion": "1. Atrial fibrillation; 2. Subject underwent cardiac pacemaker treatment; 3. Subject underwent metal graft treatment; 4. Claustrophobia; 5. Acute myocardial infarction, cardiac ischemia indicated by 6-minute walk test, hypertrophic cardiomyopathy, constrictive pericarditis, significant valve disease or congenital heart disease, severe pulmonary hypertension; 6. Ischemic heart failure without the revascularization or undergone the revascularization within last 6 months; 7. Subject underwent cardiac surgery or cerebrovascular events within the previous six months; 8. Subjects who plan to have cardiac transplantation; 9. Severe hepatic and renal insufficiency (serum creatinine>2.0 mg /dl, AST or ALT is five times higher than the upper limit of normal range); 10. Subject needs mechanical ventilation; 11. Systolic blood pressure < 90mmHg, or > 160mmHg; 12. Chronic heart failure complicated with acute hemodynamic disturbance or acute decompensation within last 1 month; 13. Mobitz Type II or III° atrial ventricular block，severe ventricular arrhythmia (polymorphic and frequent premature ventricular beats, frequent non-sustained ventricular tachycardia); 14. Serum potassium<3.2mmol/L, or>5.5mmol/L; 15. Female subject is pregnant or plan to become pregnant 16. Childbearing-aged female subject who is unmarried or dose not bear child; 17. Subject with life expectancy less than 6 months as assessed by investigators; 18. Subject participated in any other clinical trial within the previous three months; 19. Subject with previous history of tumor, or current tumor patient, or subject with pre-cancerous disease manifested by pathological examination (such as ductal carcinoma in situ or cervical epithelial dysplasia) 20. Examinations (physical examination, X-ray examination, type-B ultrasonic detection or other methods) reveal that the subject has malignant mass, gland hyperplasia or adenoma with endocrine activity, or impact on heart, or endocrine function (such as pheochromocytoma, thyroid enlargement); 21. The Investigator deemed for whatever reason that the subject is not likely to complete the study or comply with the study procedures (due to administration or any other reason).", "candidate_expression": "((>2.0 mg /dl) AND (Atrial fibrillation) AND (Chronic heart failure) AND (Claustrophobia) AND (Examinations) AND (Female) AND (Ischemic heart failure) AND (Mobitz) AND (Serum potassium) AND (The Investigator deemed for whatever reason that the subject is not likely to complete the study or comply with the study procedures (due to administration or any other reason).) AND (Type II or III) AND (bear child) AND (blood pressure) AND (cardiac pacemaker) AND (cardiac pacemaker treatment) AND (cardiac transplantation) AND (congenital) AND (current) AND (female) AND (five times higher than the upper limit of normal range) AND (frequent) AND (less than 6 months) AND (life expectancy) AND (mechanical ventilation) AND (metal graft) AND (metal graft treatment) AND (non-sustained) AND (not) AND (pathological examination) AND (plan) AND (polymorphic) AND (premature ventricular beats) AND (previous history) AND (serum creatinine) AND (severe) AND (significant) AND (unmarried) AND (ventricular tachycardia) AND (with endocrine activity) AND (within last 1 month) AND (within last 6 months) AND (within the previous six months) AND (without) AND ((impact on endocrine function) OR (impact on heart)) AND ((revascularization)) AND ((cardiac surgery) OR (cerebrovascular events)) AND ((hepatic insufficiency) OR (renal insufficiency)) AND ((ALT) OR (AST)) AND ((< 90mmHg) OR (> 160mmHg)) AND ((acute decompensation) OR (acute hemodynamic disturbance)) AND ((atrial ventricular block) OR (ventricular arrhythmia)) AND ((<3.2mmol/L) OR (>5.5mmol/L)) AND ((pregnant)) AND ((Acute myocardial infarction) OR (cardiac ischemia)) AND ((pre-cancerous disease) OR (tumor)) AND ((cervical epithelial dysplasia) OR (ductal carcinoma in situ)) AND ((X-ray examination) OR (other methods) OR (physical examination) OR (type-B ultrasonic detection)) AND ((6-minute walk test) OR (congenital heart disease) OR (constrictive pericarditis) OR (hypertrophic cardiomyopathy) OR (severe pulmonary hypertension) OR (valve disease)) AND ((adenoma) OR (endocrine activity) OR (gland hyperplasia) OR (malignant mass)) AND ((pheochromocytoma) OR (thyroid enlargement)))"}
{"candidate_id": "LLM00029", "doc_id": "NCT01715714_inc", "case_bucket": "or", "source_criterion": "Patients on chronic statin treatment (>30 days) scheduled for isolated CABG, including on- or off-pump or repeat (redo's) revascularisation procedures Stable or unstable angina, including non ST-segment-elevation acute coronary syndrome (NSTE-ACS) Age = 18 years Written informed consent", "candidate_expression": "((Age = 18 years) AND (CABG scheduled isolated) AND (NSTE-ACS) AND (Stable angina) AND (non ST-segment-elevation acute coronary syndrome) AND (revascularisation procedures on- or off-pump or repeat redo's) AND (statin) AND (treatment chronic >30 days) AND (unstable angina))"}
{"candidate_id": "LLM00030", "doc_id": "NCT03025620_exc", "case_bucket": "other", "source_criterion": "Patients unable to understand the objectives of the dietary intervention Patients in paliative care Patients receiving supplement diets", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00031", "doc_id": "NCT03146390_exc", "case_bucket": "or", "source_criterion": "Smoker or former smoker. Presence of dental prostheses. Presence of orthodontic devices. Antibiotic treatment or routine use of oral antiseptics in the previous 3 months. Presence of any systemic disease that could alter the production or composition of saliva.", "candidate_expression": "((Antibiotic) AND (Smoker) AND (dental prostheses) AND (former smoker) AND (oral antiseptics routine use in the previous 3 months) AND (orthodontic devices) AND (systemic disease could alter the production or composition of saliva))"}
{"candidate_id": "LLM00032", "doc_id": "NCT02904785_exc", "case_bucket": "or", "source_criterion": "History of spinal cord stenosis or clinical symptoms of lumbar radiculopathy; History or onset neurological diseases; Generalized pain or fibromyalgia; Inability to walk; History of knee surgery in the target knee; Secondary causes of osteoarthritis; Use of statins and quinolones in the previous year; Uncontrolled and ongoing psychiatric diseases; Invasive knee treatments with hyaluronic acid infusion, corticosteroids and anaesthetics, in the target knee, up to 6 months previous to study inclusion.", "candidate_expression": "((Generalized pain) AND (History onset) AND (Inability to walk) AND (Invasive knee treatments) AND (Secondary causes) AND (anaesthetics) AND (clinical symptoms) AND (corticosteroids) AND (fibromyalgia) AND (hyaluronic acid) AND (hyaluronic acid infusion) AND (knee surgery History target knee) AND (lumbar radiculopathy) AND (neurological diseases) AND (osteoarthritis) AND (psychiatric diseases Uncontrolled ongoing) AND (quinolones in the previous year) AND (spinal cord stenosis History) AND (statins in the previous year))"}
{"candidate_id": "LLM00033", "doc_id": "NCT02643381_inc", "case_bucket": "or", "source_criterion": "Adult patient (male or female) requiring emergency endotracheal intubation.", "candidate_expression": "((Adult) AND (emergency endotracheal intubation) AND (female) AND (male))"}
{"candidate_id": "LLM00034", "doc_id": "NCT00904202_inc", "case_bucket": "or", "source_criterion": "1. Had a diagnosis of PHN, DN, CRPS, carpal tunnel syndrome, HIV neuropathy, idiopathic sensory neuropathy, or other peripheral neuropathy (upon mutual agreement of the sponsor and investigator) 2. Patients with PHN must have had pain >3 months after rash healing 3. Patients with DN must have had Type I or II diabetes and painful distal symmetric sensorimotor polyneuropathy with or without dynamic allodynia of the lower extremities 4. Patients with CRPS must have met current IASP (International Association for the Study of Pain) diagnostic criteria 5. Patients with carpal tunnel syndrome must have had a diagnosis by combination clinical neurological examination (e.g., Phalen's and Tinel's signs), electrodiagnostic testing, and daily painful symptoms of at least 3 months' duration 6. Patients with HIV neuropathy must have had HIV, subjective symptoms of painful peripheral neuropathy, and daily painful symptoms of at least 3 months' duration 7. Patients with idiopathic sensory neuropathy must have had pain of at least 3 months' duration 8. Reached an average daily pain rating during the baseline week of pain ratings greater than 4 on the 0-to-10 numerical pain rating scale (Question 5 of the BPI) 9. Had never received an analgesic regimen that contained lidocaine or gabapentin", "candidate_expression": "((0-to-10 numerical pain rating scale) AND (>3 months) AND (CRPS) AND (DN) AND (HIV) AND (HIV neuropathy) AND (IASP (International Association for the Study of Pain) diagnostic criteria) AND (PHN) AND (Phalen's signs) AND (Tinel's signs) AND (Type I diabetes) AND (Type II diabetes) AND (after rash healing) AND (analgesic regimen) AND (at least 3 months' duration) AND (average) AND (baseline week) AND (carpal tunnel syndrome) AND (clinical neurological examination) AND (daily) AND (daily pain rating) AND (distal) AND (during the baseline week) AND (dynamic allodynia) AND (electrodiagnostic) AND (greater than 4) AND (idiopathic) AND (idiopathic sensory neuropathy) AND (met) AND (neuropathy) AND (pain) AND (painful) AND (painful symptoms) AND (peripheral neuropathy) AND (rash healing) AND (sensorimotor polyneuropathy) AND (subjective symptoms) AND (symmetric) AND (upon mutual agreement of the sponsor and investigator) AND ((CRPS) OR (DN) OR (HIV neuropathy) OR (PHN) OR (carpal tunnel syndrome) OR (peripheral neuropathy) OR (sensory neuropathy)) AND ((gabapentin) OR (lidocaine)))"}
{"candidate_id": "LLM00035", "doc_id": "NCT01912677_inc", "case_bucket": "or", "source_criterion": "Pregnant gestational age >= 28 weeks Systolic blood pressure >=160 mm Hg OR a diastolic blood pressure of >=110 mm Hg measured twice more than 15 minutes apart Able to swallow pills >= 18 years", "candidate_expression": "((Able to swallow pills) AND (gestational age >= 28 weeks) AND (years >= 18) AND ((Systolic blood pressure >=160 mm Hg) OR (diastolic blood pressure >=110 mm Hg)))"}
{"candidate_id": "LLM00036", "doc_id": "NCT02827526_inc", "case_bucket": "or", "source_criterion": "Patients presenting for elective posterior spinal fusion surgery (lower thoracic, lumbar, sacral) Ages 18-80", "candidate_expression": "((Ages 18-80) AND (posterior spinal fusion surgery elective) AND ((lower thoracic) OR (lumbar) OR (sacral)))"}
{"candidate_id": "LLM00037", "doc_id": "NCT01720394_exc", "case_bucket": "other", "source_criterion": "fetal anomalies contra-indications for medical induction of labor placental pathologies St.p. surgery with opening the uterine cavity (incl. caesarean section) PROM multiple gestations < 37-0 weeks of gestation St.p. cervical tear", "candidate_expression": "((PROM) AND (St.p.) AND (caesarean section) AND (cervical tear) AND (contra-indications) AND (fetal anomalies) AND (gestation < 37-0 weeks) AND (medical induction of labor) AND (multiple gestations) AND (placental pathologies) AND (surgery with opening the uterine cavity))"}
{"candidate_id": "LLM00038", "doc_id": "NCT02371200_inc", "case_bucket": "or", "source_criterion": "1. Subject has a history of GTC seizures, either primary GTC or partial onset seizures with secondary generalization. 2. Is being admitted to a hospital for routine vEEG monitoring related to seizures. 3. Male or female between the ages of 2-99. 4. Has an upper arm circumference which is adequate for proper fit of the EMG monitor (at least 14cm). 5. If female and of childbearing potential, has a negative pregnancy test. 6. Can understand and sign written informed consent, or will have a parent or a legally authorized representative (LAR) who can do so, prior to the performance of any study assessments. 7. Subject and/or Primary Caregiver must be competent to follow all study procedures. 8. Is able to read, speak, and understand English.", "candidate_expression": "((Can understand and sign written informed consent, or will have a parent or a legally authorized representative (LAR) who can do so, prior to the performance of any study assessments.) AND (GTC seizures) AND (Subject and/or Primary Caregiver must be competent to follow all study procedures.) AND (adequate for proper fit of the EMG monitor) AND (admitted to a hospital) AND (at least 14cm) AND (between 2-99) AND (childbearing potential) AND (female) AND (history) AND (negative) AND (pregnancy test) AND (secondary generalization) AND (seizures) AND (the ages) AND (upper arm circumference) AND (vEEG monitoring) AND ((partial onset seizures) OR (primary GTC)) AND ((Male) OR (female)))"}
{"candidate_id": "LLM00039", "doc_id": "NCT02408120_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00040", "doc_id": "NCT03335436_inc", "case_bucket": "other", "source_criterion": "singleton, term pregnancy currently on buprenorphine maintenance therapy scheduled for elective CD under spinal anesthesia", "candidate_expression": "((CD) AND (buprenorphine) AND (buprenorphine maintenance therapy) AND (currently) AND (elective) AND (pregnancy) AND (scheduled for) AND (singleton) AND (spinal anesthesia) AND (term))"}
{"candidate_id": "LLM00041", "doc_id": "NCT01051414_exc", "case_bucket": "or", "source_criterion": "Subjects with evidence of liver cirrhosis Evidence of HCC Co-infection with hepatitis B virus, HIV", "candidate_expression": "((HCC Evidence) AND (liver cirrhosis evidence) AND ((HIV) OR (hepatitis B virus)))"}
{"candidate_id": "LLM00042", "doc_id": "NCT03262038_inc", "case_bucket": "or", "source_criterion": "3-17 years weight </= 100kg scheduled for urologic or orthopedic procedure necessitating intrathecal morphine ability to use verbal or pictorial pain assessment tools and techniques informed consent and (if applicable) assent", "candidate_expression": "((3-17 years) AND (</= 100kg) AND (ability) AND (informed consent and (if applicable) assent) AND (intrathecal) AND (morphine) AND (orthopedic procedure) AND (pictorial pain assessment tools and techniques) AND (urologic procedure) AND (verbal pain assessment tools and techniques) AND (weight))"}
{"candidate_id": "LLM00043", "doc_id": "NCT03016741_exc", "case_bucket": "or", "source_criterion": "Prior treatment with enzalutamide or abiraterone acetate for > 14 days prior to enrollment and completion of baseline tests. Receipt of chemotherapy for prostate or other cancer within the past 12 months with residual cognitive deficits, or receipt of chemotherapy for mCRPC. Patients/physicians planning treatment with chemotherapy during the 12 month period of the investigation are also ineligible. History of cognitive impairment or dysfunction, including a history of dementia, Alzheimer's disease, stroke with residual cognitive deficits, cognitive dysfunction related to alcohol or substance abuse, or cognitive dysfunction related to prior treatment for any cancer. Patients with a seizure history, history of recurrent falls, or known brain metastases are excluded from this clinical trial because of their poor prognosis and because of their heightened risk of seizure or progressive cognitive and/or neurologic dysfunction that would confound the evaluation. Uncontrolled intercurrent illness including, but not limited to, uncontrolled diabetes, ongoing or active infection, symptomatic congestive heart failure (New York Heart Association Class III and IV heart failure), unstable angina pectoris, cardiac arrhythmia, or psychiatric illness/social situations/substance abuse that would limit compliance with study requirements. Patients with a \"currently active\" second malignancy other than non-melanoma skin cancers are not eligible. Patients are not considered to have a \"currently active\" malignancy if they have completed all therapy and are now considered without evidence of disease for 1 year. Patients with cognitive dysfunction related to treatment of another malignancy, including a history of \"chemo-brain\", are ineligible. Patients taking psychotropic medications or illicit drugs that may alter cognition, concentration, or behavior. Appropriate treatment by a licensed provider with medications for depression or anxiety, including but not limited to SSRIs, SNRIs, and standard dose benzodiazepines at a stable dose, is permitted", "candidate_expression": "((Alzheimer's disease) AND (New York Heart Association Class III and IV) AND (abiraterone acetate) AND (alcohol abuse) AND (alter behavior) AND (alter cognition) AND (alter concentration) AND (brain metastases) AND (cancer any) AND (cancer other) AND (cardiac arrhythmia) AND (chemotherapy) AND (chemotherapy within the past 12 months) AND (cognitive dysfunction) AND (cognitive impairment) AND (congestive heart failure symptomatic) AND (dementia) AND (diabetes uncontrolled ongoing active) AND (enzalutamide) AND (heart failure) AND (illicit drugs) AND (infection) AND (intercurrent illness Uncontrolled) AND (mCRPC) AND (malignancy another) AND (malignancy currently active second) AND (prostate cancer) AND (psychiatric illness) AND (psychotropic medications) AND (recurrent falls history of) AND (residual cognitive deficits) AND (seizure history) AND (social situations) AND (stroke) AND (substance abuse) AND (treatment) AND (treatment for > 14 days prior to enrollment) AND (treatment prior) AND (unstable angina pectoris) AND NOT (non-melanoma skin cancers))"}
{"candidate_id": "LLM00044", "doc_id": "NCT02456532_exc", "case_bucket": "or", "source_criterion": "acute or unstable medical disease, current or past history of psychiatric disease, alcoholism or drug abuse, and other primary sleep disorders", "candidate_expression": "((medical disease) AND ((acute) OR (unstable)) AND ((alcoholism) OR (drug abuse) OR (primary sleep disorders) OR (psychiatric disease)))"}
{"candidate_id": "LLM00045", "doc_id": "NCT02747940_inc", "case_bucket": "or", "source_criterion": "Control: devoid of any systemic or neurological diseases Chronic migraine: by ICHD-III (International Classification of Headache Disorder) criteria Fibromyalgia: by ACR (American College of Rheumatology) 2010 criteria", "candidate_expression": "((ACR 2010 criteria) AND (American College of Rheumatology) AND (Chronic migraine) AND (Fibromyalgia) AND (ICHD-III) AND (International Classification of Headache Disorder) AND (devoid) AND (neurological diseases) AND (systemic diseases))"}
{"candidate_id": "LLM00046", "doc_id": "NCT02137538_exc", "case_bucket": "other", "source_criterion": "Bone age reading more than 14.0 years Follicle stimulating hormone > 20 IU/L", "candidate_expression": "((> 20 IU/L) AND (Bone age) AND (Follicle stimulating hormone) AND (more than 14.0 years))"}
{"candidate_id": "LLM00047", "doc_id": "NCT02997215_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologist (ASA) status I-II adult patients undergoing elective laparoscopic cholecystectomy.", "candidate_expression": "((American Society of Anesthesiologist (ASA) status I-II) AND (adult) AND (laparoscopic cholecystectomy elective))"}
{"candidate_id": "LLM00048", "doc_id": "NCT02208739_exc", "case_bucket": "or", "source_criterion": "Patients who had history of systemic antibiotic usage over the previous 4 months Patients who were pregnant Patients who had received non-surgical periodontal treatment within the past 6 months Patients who had received surgical periodontal treatment within the past 12 months Patients who were smokers Patients with a history of stroke or an acute cardiovascular event over the previous 12 months.", "candidate_expression": "((acute cardiovascular event) AND (history) AND (non-surgical periodontal treatment) AND (over the previous 12 months) AND (over the previous 4 months) AND (pregnant) AND (smokers) AND (stroke) AND (surgical periodontal treatment) AND (systemic antibiotic) AND (within the past 12 months) AND (within the past 6 months))"}
{"candidate_id": "LLM00049", "doc_id": "NCT01944800_inc", "case_bucket": "or", "source_criterion": "intolerance of or allergy to ticagrelor or prasugrel history of any stroke, transient ischemic attack or intracranial bleeding known intracranial neoplasm, intracranial arteriovenous malformation or intracranial aneurysm active bleeding, clinical findings, that in the judgement of the investigator are associated with an increased risk of bleeding fibrin-specific fibrinolytic therapy less than 24 h before randomization, non-fibrin-specific fibrinolytic therapy less than 48 h before randomization known platelet count < 100.000/µL at the time of screening known anemia (hemoglobin <10 g/dL) at the time of screening oral anticoagulation that cannot be safely discontinued for the duration of the study INR known to be greater than 1.5 at the time of screening chronic renal insufficiency requiring dialysis moderate or severe hepatic dysfunction (Child Pugh B or C) increased risk of bradycardia events (Sick Sinus, AV block grade II or III, bradycardia-induced syncope) index event is an acute complication (< 30 days) of PCI concomitant medical illness that in the opinion of the investigator is associated with a life expectancy < 1 year concomitant oral or i.v. therapy with strong CYP3A Inhibitors (e.g. ketoconazole, itraconazole, voriconazole, telithromycin, clarithromycin, nefazodone, ritonavir, saquinavir, nelfinavir, indinavir, atazanavir, grapefruit juice > 1 L/d), CYP3A substrates with narrow therapeutic indices (e.g. cyclosporine, quinidine), or strong CYP3A inducers (e.g. rifampin/rifampicin, phenytoin, carbamazepine, dexamethason, phenobarbital ) that cannot be safely discontinued =1 doses of ticagrelor or prasugrel within 5 days before randomisation no written informed consent participation in another investigational drug study previous enrolment in this study for women of childbearing potential no negative pregnancy test and no agree to use reliable method of birth control during the study Pregnancy, giving birth within the last 90 days, or lactation inability to cooperate with protocol requirements", "candidate_expression": "((CYP3A substrates with narrow therapeutic indices) AND (Child Pugh B or C) AND (INR greater than 1.5 at the time of screening) AND (Pregnancy, giving birth within the last 90 days, or lactation) AND (anemia at the time of screening) AND (bradycardia events increased risk) AND (chronic renal insufficiency) AND (complication of PCI acute < 30 days) AND (concomitant medical illness is associated with a life expectancy < 1 year) AND (dialysis) AND (for women of childbearing potential no negative pregnancy test and no agree to use reliable method of birth control during the study) AND (grade II or III) AND (hemoglobin <10 g/dL) AND (hepatic dysfunction) AND (intracranial aneurysm) AND (intracranial arteriovenous malformation) AND (intracranial neoplasm) AND (oral anticoagulation cannot be safely discontinued for the duration of the study) AND (participation in another investigational drug study) AND (platelet count < 100.000/µL at the time of screening) AND (strong CYP3A Inhibitors) AND (strong CYP3A inducers) AND (within 5 days before randomisation randomisation) AND ((carbamazepine) OR (dexamethason) OR (phenobarbital) OR (phenytoin) OR (rifampicin) OR (rifampin)) AND ((bleeding) OR (clinical findings, that in the judgement of the investigator are associated with an increased risk of bleeding)) AND ((fibrinolytic therapy fibrin-specific less than 24 h before randomization) OR (fibrinolytic therapy non-fibrin-specific less than 48 h before randomization)) AND ((allergy) OR (intolerance)) AND ((prasugrel) OR (ticagrelor)) AND ((moderate) OR (severe)) AND ((AV block) OR (Sick Sinus) OR (bradycardia-induced syncope)) AND ((i.v. therapy) OR (oral therapy)) AND ((atazanavir) OR (clarithromycin) OR (grapefruit juice > 1 L/d) OR (indinavir) OR (itraconazole) OR (ketoconazole) OR (nefazodone) OR (nelfinavir) OR (ritonavir) OR (saquinavir) OR (telithromycin) OR (voriconazole)) AND ((intracranial bleeding) OR (stroke) OR (transient ischemic attack)) AND ((cyclosporine) OR (quinidine)))"}
{"candidate_id": "LLM00050", "doc_id": "NCT00752310_inc", "case_bucket": "or", "source_criterion": "Non-smoking, or smoking no more than 10 cigarettes, or 2 cigars, or 2 pipes per day for at least 3 months prior to selection Normal weight as defined by a Body Mass Index (BMI, weight in kg divided by the square of height in meters) of 18.0 to 30.0 kg/m2, extremes included Able to comply with protocol requirements. Healthy on the basis of a medical evaluation that reveals the absence of any clinically relevant abnormality and includes a physical examination, medical history, electrocardiogram (ECG), vital signs, and the results of blood biochemistry, blood coagulation, and hematology tests and a urinalysis carried out at screening.", "candidate_expression": "((18.0 to 30.0 kg/m2, extremes included) AND (Able to comply with protocol requirements) AND (BMI) AND (Body Mass Index) AND (ECG) AND (Healthy) AND (Non) AND (Normal weight) AND (abnormality) AND (absence) AND (at screening) AND (blood biochemistry tests) AND (blood coagulation tests) AND (cigarettes) AND (cigars) AND (clinically relevant) AND (electrocardiogram) AND (for at least 3 months prior to selection) AND (hematology tests) AND (medical evaluation) AND (medical history) AND (no more than 10 per day) AND (no more than 2 per day) AND (physical examination) AND (pipes) AND (screening) AND (selection) AND (smoking) AND (urinalysis) AND (vital signs) AND (weight in kg divided by the square of height in meters))"}
```
