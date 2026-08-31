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
{"candidate_id": "LLM03926", "doc_id": "NCT02560389_inc", "case_bucket": "or", "source_criterion": "25-50 years of age PTSD related to physical or sexual assault Medically healthy English speaking", "candidate_expression": "((25-50 years) AND (English speaking) AND (Medically healthy) AND (PTSD) AND (age) AND ((physical assault) OR (sexual assault)))"}
{"candidate_id": "LLM03927", "doc_id": "NCT03589105_exc", "case_bucket": "or", "source_criterion": "Diagnosis of primary progressive MS Inability to complete an MRI (contraindications for MRI include but are not restricted to weight =140 kg, pacemaker, cochlear implants, presence of foreign substances in the eye, intracranial vascular clips, surgery within 6 weeks of entry into the study, coronary stent implanted within 8 weeks prior to the time of the intended MRI, etc…) Gadolinium intolerance History of ischemic cerebrovascular disorders (e.g., stroke, transient ischemic attack) or ischemia of the spinal cord History or known presence of central nervous system (CNS) or spinal cord tumor (e.g., meningioma, glioma) History or known presence of potential metabolic causes of myelopathy (e.g., untreated vitamin B12 deficiency) History or known presence of infectious causes of myelopathy (e.g., syphilis, Lyme disease, human T-lymphotropic virus 1 (HTLV-1), herpes zoster myelopathy) History of genetically inherited progressive CNS degenerative disorder (e.g., hereditary paraparesis; MELAS [mitochondrial myopathy, encephalopathy, lactic acidosis, stroke] syndrome) Neuromyelitis optica History or known presence of systemic autoimmune disorders potentially causing progressive neurologic disease (e.g., lupus, anti-phospholipid antibody syndrome, Sjogren's syndrome, Behçet's disease, sarcoidosis) History of severe, clinically significant brain or spinal cord trauma (e.g., cerebral contusion, spinal cord compression) Vulnerable patients (Patient referred to in Articles L. 1121-5 to L. 1121-8 and L. 1122-1-2 of the French Public Health Code)", "candidate_expression": "((Gadolinium) AND (MRI) AND (MRI Inability to complete) AND (MRI intended) AND (Neuromyelitis optica) AND (Vulnerable patients Articles L. 1121-5 to L. 1121-8 and L. 1122-1-2 of the French Public Health Code) AND (contraindications) AND (coronary stent) AND (encephalopathy) AND (infectious causes) AND (intolerance) AND (lactic acidosis) AND (metabolic causes) AND (mitochondrial myopathy) AND (myelopathy) AND (progressive CNS degenerative disorder genetically inherited) AND (progressive MS primary) AND (progressive neurologic disease potentially causing) AND (stroke) AND (systemic autoimmune disorders) AND (vitamin B12 deficiency untreated) AND ((cochlear implants) OR (foreign substances in the eye) OR (implanted within 8 weeks prior to the time of the intended MRI) OR (intracranial vascular clips) OR (pacemaker) OR (surgery within 6 weeks of entry into the study) OR (weight =140 kg)) AND ((stroke) OR (transient ischemic attack)) AND ((ischemia of the spinal cord) OR (ischemic cerebrovascular disorders)) AND ((central nervous system (CNS) tumor) OR (spinal cord tumor)) AND ((glioma) OR (meningioma)) AND ((Lyme disease) OR (herpes zoster myelopathy) OR (human T-lymphotropic virus 1 (HTLV-1)) OR (syphilis)) AND ((MELAS syndrome) OR (hereditary paraparesis)) AND ((Behçet's disease) OR (Sjogren's syndrome) OR (anti-phospholipid antibody syndrome) OR (lupus) OR (sarcoidosis)) AND ((brain trauma) OR (spinal cord trauma)) AND ((cerebral contusion) OR (spinal cord compression)))"}
{"candidate_id": "LLM03928", "doc_id": "NCT03217409_exc", "case_bucket": "or", "source_criterion": "Subjects with hypersensitivity reaction to Statin and Ezetimibe Subjects with severe kidney disease Subjects with HIV positive result at the screening Pregnant or breast-feeding subjects Subjects with taking any medication affecting level of LDL (Fenofibrate, Omega 3 fatty aicd etc.) Insulin-treated Subjects Other exclusions applied", "candidate_expression": "((Ezetimibe) AND (Fenofibrate) AND (HIV positive at the screening) AND (Insulin) AND (LDL) AND (Omega 3 fatty aicd) AND (Pregnant) AND (Statin) AND (affecting) AND (breast-feeding) AND (hypersensitivity) AND (kidney disease severe) AND (medication))"}
{"candidate_id": "LLM03929", "doc_id": "NCT00994786_exc", "case_bucket": "or", "source_criterion": "Patients with any other primary DSM-IV psychiatric diagnosis in addition to Obsessive Compulsive Disorder. Patients who currently fulfil criteria for DSM-IV eating disorder, body dysmorphic disorder, current alcohol or substance abuse, or who have a lifetime history of bipolar disorder. Patients with a history of Schizophrenia and other psychotic disorders, Delirium, Dementia, and Amnestic and other cognitive disorders. Subjects with a concurrent Axis II Cluster A Personality Disorder Borderline or Antisocial Personality Disorder. Subjects who based on history or mental status examination have a significant risk of committing suicide, in the investigator's opinion. Subjects with a history of more than three adequate trials with an SSRI. Subjects who have had an adequate trial of pregabalin. Subjects who have initiated psychotherapy in the last 4 months prior to the first visit. Subjects who, during the course of the study, would be likely to require treatment with prohibited concomitant therapy . Prior use of or a known allergy or hypersensitivity to pregabalin. Subjects who have participated in any clinical trial within 30 days prior to entering the study, or in a clinical trial involving a psychotropic medication within the 6 months prior to entering the study. Any subject who has been taking benzodiazepines before entering the study who: 1) cannot tolerate being free of benzodiazepines for 4 weeks, or 2) has signs or symptoms of benzodiazepine withdrawal or rebound at the end of those 4 weeks. Should a patient entering the study, who is currently on benzodiazepines develop discontinuation symptoms with discontinuation of their benzodiazepine, we will treat these symptoms with a more gradual benzodiazepine taper. Study will be delayed until the patient is able to tolerate the discontinuation for 4 weeks. Patients with a current seizure disorder, organic brain disorder or a history of seizure disorders (except for febrile seizures in childhood). Patients with thyroid pathology, the treatment of which has not been stabilized for at least three months. Patients on neuroleptic drugs in the two months prior to study entry or cognitive behavioural therapy specific to OCD within four weeks of study entry Pregnant or lactating females, or if sexually active and of childbearing potential, not using adequate methods of birth control. Patients with a history or evidence of a medical condition that would expose them to an increased risk of a significant adverse event or interfere with assessments of safety and efficacy during the trial. Patients receiving psychotropics of any kind, including betablockers and other anticonvulsants. Sleep medication such as oral chloral-hydrate or zopiclone are acceptable. Patients using any herbal psychoactive treatments, e.g. St John's Wort, Valerian, Kava Kava, L-tryptophan. Patients with any condition or on any therapy that, in the investigator's opinion, or as indicated in the pregabalin product label, may pose a risk to the subject. Patients who have had a major life event in the past three months, which in the judgement of the investigator is influencing their current condition. Patients having clinically significant abnormal laboratory, or ECG findings not resolved by further examinations.", "candidate_expression": "((Amnestic) AND (Antisocial Personality Disorder) AND (Borderline Personality Disorder) AND (Delirium) AND (Dementia) AND (ECG findings) AND (Kava Kava) AND (L-tryptophan) AND (OCD) AND (Personality Disorder Axis II Cluster A) AND (Pregnant or lactating females, or if sexually active and of childbearing potential, not using adequate methods of birth control) AND (Schizophrenia) AND (St John's Wort) AND (Subjects who have had an adequate trial of pregabalin) AND (Subjects who have participated in any clinical trial within 30 days prior to entering the study, or in a clinical trial involving a psychotropic medication within the 6 months prior to entering the study.) AND (Subjects with a history of more than three adequate trials with an SSRI) AND (Valerian) AND (alcohol abuse) AND (allergy) AND (anticonvulsants) AND (betablockers) AND (bipolar disorder) AND (body dysmorphic disorder) AND (chloral-hydrate oral) AND (cognitive behavioural therapy within four weeks of study entry) AND (cognitive disorders other) AND (eating disorder) AND (herbal psychoactive treatments) AND (history of seizure disorders) AND (hypersensitivity) AND (laboratory findings) AND (mental status examination) AND (neuroleptic drugs in the two months prior to study entry) AND (organic brain disorder) AND (pregabalin) AND (psychiatric diagnosis any other primary DSM-IV) AND (psychotherapy in the last 4 months prior to the first visit) AND (psychotic disorders other) AND (psychotropics) AND (risk of committing suicide significant) AND (seizure disorder) AND (substance abuse) AND (thyroid pathology) AND (treatment stabilized at least three months) AND (zopiclone) AND NOT (Obsessive Compulsive Disorder) AND NOT (febrile seizures childhood) AND NOT (Sleep medication))"}
{"candidate_id": "LLM03930", "doc_id": "NCT00094861_inc", "case_bucket": "or", "source_criterion": "Patients with a histologically or cytologically proven diagnosis of NSCLC Unresectable (locally advanced) stage IIIa or IIIb disease Initial radiotherapy field of treatment to encompass greater than or equal to 30% of the esophagus Life expectancy greater than or equal to 6 months Estimated weight loss less than or equal to 10% in the 3 months before study randomization Measurable disease 18 years of age or older Eastern Cooperative Oncology Group (ECOG) performance status of 0 - 2 Hemoglobin (hgb) greater than or equal to 10 g/dL without transfusional support or growth factor use in the 4 weeks before study randomization Absolute neutrophil count (ANC) greater than or equal to 1.5 x 10^9/L without growth factor use in the 2 weeks before study randomization Platelet count greater than or equal to 100 x 10^9/L Serum bilirubin less than or equal to 1.5 x institutional upper limit of normal (ULN) Serum creatinine less than or equal to 2.0 mg/dL (Note: Patients with a serum creatinine greater than or equal to 1.4 and less than or equal to 2.0 mg/dL must demonstrate a 24-hour urinary creatinine clearance greater than or equal to 50 mL/min) Females of childbearing potential: negative serum or urine pregnancy test Patient must give written informed consent before participating in any study-specific procedure, randomization, or receiving investigational product. Patients with reproductive capability must agree to practice adequate contraception methods.", "candidate_expression": "((24-hour urinary creatinine clearance greater than 50 mL/min equal to 50 mL/min) AND (ANC greater than 1.5 x 10^9/L equal to 1.5 x 10^9/L) AND (Absolute neutrophil count in the 2 weeks before study randomization) AND (ECOG) AND (Eastern Cooperative Oncology Group performance status 0 - 2) AND (Estimated weight loss 3 months before study randomization less than 10% equal to 10%) AND (Females) AND (Hemoglobin in the 4 weeks before study randomization) AND (Life expectancy equal to 30% greater than 6 months equal to 6 months) AND (Measurable disease) AND (NSCLC histologically proven cytologically proven locally advanced) AND (Platelet count greater than 100 x 10^9/L equal to 100 x 10^9/L) AND (Serum bilirubin less than 1.5 x institutional upper limit of normal (ULN) equal to 1.5 x institutional upper limit of normal (ULN)) AND (Serum creatinine less than equal to 2.0 mg/dL 2.0 mg/dL) AND (age 18 years or older) AND (childbearing potential) AND (contraception methods adequate) AND (growth factor use) AND (hgb greater than 10 g/dL equal to 10 g/dL) AND (informed consent before participating in any study-specific procedure, randomization, or receiving investigational product participating in any study-specific procedure, randomization, or receiving investigational product) AND (investigational product) AND (procedure study-specific) AND (radiotherapy Initial esophagus greater than 30) AND (randomization) AND (reproductive capability) AND (serum creatinine greater than 1.4 mg/dL equal to 1.4 mg/dL less than 2.0 mg/dL equal to 2.0 mg/dL) AND (serum pregnancy test) AND (stage IIIa disease) AND (stage IIIb disease) AND (transfusional support) AND (urine pregnancy test) AND NOT (growth factor use in the 2 weeks before study randomization))"}
{"candidate_id": "LLM03931", "doc_id": "NCT03262038_exc", "case_bucket": "or", "source_criterion": "Inability to use verbal or pictorial pain scoring scales hypersensitivity to selective 5-HT receptor antagonists diagnosed congenital long QT syndrome severe hepatic impairment pregnancy or nursing mothers", "candidate_expression": "((Inability) AND (congenital long QT syndrome) AND (hepatic impairment) AND (hypersensitivity) AND (selective 5-HT receptor antagonists) AND (severe) AND ((pictorial pain scoring scales) OR (verbal pain scoring scales)) AND ((nursing) OR (pregnancy)))"}
{"candidate_id": "LLM03932", "doc_id": "NCT00455663_exc", "case_bucket": "or", "source_criterion": "History of significant head trauma, seizure disorder, or mental retardation History of alcohol or drug abuse or dependence within 1 month prior to study entry History of violence within 6 months prior to study entry", "candidate_expression": "((History) AND (History violence) AND ((head trauma) OR (mental retardation) OR (seizure disorder)) AND ((abuse alcohol) OR (dependence alcohol) OR (dependence drug) OR (drug abuse)))"}
{"candidate_id": "LLM03933", "doc_id": "NCT03018171_inc", "case_bucket": "other", "source_criterion": "Written maternal informed consent Singleton pregnancy Gestational age = 37 weeks, ASA I BMI < 30 fetus in cephalic presentation", "candidate_expression": "((ASA I) AND (BMI < 30) AND (Gestational age = 37 weeks) AND (Singleton pregnancy) AND (Written maternal informed consent) AND (cephalic presentatio))"}
{"candidate_id": "LLM03934", "doc_id": "NCT00625742_exc", "case_bucket": "or", "source_criterion": "1. Have dementia or delirium (as determined by the palliative care specialist) at study entry. 2. Are pregnant 3. Have been taking corticosteroids for longer than 48 hours. 4. Have pulmonary edema, ascites or pitting edema on clinical examination. 5. Are unable to walk. 6. Have a history of serious adverse gastrointestinal events (i.e., bleeding or perforation),history of a coagulopathy or current anti-coagulant use. 7. Have an ALT/AST>3x upper limit of normal. 8. Patients on methotrexate. 9. Patients taking melatonin receptor agonists (such as Rozerem® [ramelteon]).", "candidate_expression": "((>3x upper limit of normal) AND (ALT/AST) AND (Rozerem) AND (adverse gastrointestinal events) AND (anti-coagulant) AND (ascites) AND (at study entry) AND (bleeding) AND (coagulopathy) AND (corticosteroids) AND (current) AND (delirium) AND (dementia) AND (history) AND (longer than 48 hours) AND (melatonin receptor agonists) AND (methotrexate) AND (perforation) AND (pitting edema) AND (pregnant) AND (pulmonary edema) AND (ramelteon) AND (serious) AND (unable to walk))"}
{"candidate_id": "LLM03935", "doc_id": "NCT03096613_inc", "case_bucket": "or", "source_criterion": "Aged 18 years or older, male or female. Systolic heart failure with New York Heart Association (NYHA) class II-III. Left ventricular ejection fraction (LVEF) less than 40% by echocardiography during screening and randomization. SCH (TSH: upper limits of normal (ULN) -10mIU/L, and FT4 level within reference range). Having received standard HF therapy for at least 2 weeks, having reached target dose or max tolerable dose. Provided informed consent.", "candidate_expression": "((Aged 18 years or older) AND (FT4 level within reference range) AND (Left ventricular ejection fraction (LVEF) less than 40%) AND (New York Heart Association (NYHA) class II-III) AND (SCH) AND (Systolic heart failure) AND (TSH upper limits of normal (ULN) -10mIU/L) AND (echocardiography during screening and randomization) AND (standard HF therapy for at least 2 weeks) AND ((max tolerable dose) OR (target dose)) AND ((female) OR (male)))"}
{"candidate_id": "LLM03936", "doc_id": "NCT00480129_exc", "case_bucket": "other", "source_criterion": "Ongoing allergen immunotherapy upper respiratory tract infection Pregnancy Clinical history of lactose-intolerance or allergies to cow-milk", "candidate_expression": "((Pregnancy) AND (allergen immunotherapy) AND (allergies to cow-milk) AND (lactose-intolerance) AND (upper respiratory tract infection))"}
{"candidate_id": "LLM03937", "doc_id": "NCT02196285_inc", "case_bucket": "other", "source_criterion": "Male Age between 18 and 49 years old; Willing to provide name, address, telephone and other contact information in order to be contacted, whenever needed (example: in case of missing any scheduled visit, contact for confirmation of scheduling a visit, urgent safety notifications); Willing to strictly follow the study protocol; Capacity for understanding and signing in the Informed Consent Form; To understand the impossibility of participating in another clinical trial during the time of participation in the study, until 6 months after its conclusion; Intellectual level which allows to filling in the diaries for registering of symptoms at home; Willing to undergo to serological testing to HIV, HBV and HCV; Being in good health, with no significant medical history; Physical examination at screening period without clinically significant changes; Lab examination at screening period within the normal ranges, determined by the laboratory or abnormal values, grading below 1 or 2, according to medical decision.", "candidate_expression": "((Age) AND (Being in good health, with no significant medical history;) AND (Capacity for understanding and signing in the Informed Consent Form;) AND (Intellectual level which allows to filling in the diaries for registering of symptoms at home;) AND (Lab examination at screening period within the normal ranges, determined by the laboratory or abnormal values, grading below 1 or 2, according to medical decision.) AND (Male) AND (Physical examination) AND (Physical examination at screening period without clinically significant changes;) AND (To understand the impossibility of participating in another clinical trial during the time of participation in the study, until 6 months after its conclusion;) AND (Willing to provide name, address, telephone and other contact information in order to be contacted, whenever needed (example: in case of missing any scheduled visit, contact for confirmation of scheduling a visit, urgent safety notifications);) AND (Willing to strictly follow the study protocol;) AND (Willing to undergo to serological testing to HIV, HBV and HCV;) AND (at screening period) AND (between 18 and 49 years old) AND (good health) AND (screening period) AND (serological testing to HBV) AND (serological testing to HCV) AND (serological testing to HIV))"}
{"candidate_id": "LLM03938", "doc_id": "NCT03335904_exc", "case_bucket": "other", "source_criterion": "history of hypertension known impaired renal function liver disease heart failure myocardial infarction coronary artery disease smoked within the past year apnea hypopnea index > 5 events per hour", "candidate_expression": "((apnea hypopnea index > 5 events per hour) AND (coronary artery disease) AND (heart failure) AND (hypertension history) AND (impaired renal function) AND (liver disease) AND (myocardial infarction) AND (smoked within the past year))"}
{"candidate_id": "LLM03939", "doc_id": "NCT02647788_inc", "case_bucket": "scope", "source_criterion": "Patients undergoing ambulatory hand surgery for carpal tunnel and trigger finger, under local anesthesia with or without sedation.", "candidate_expression": "((carpal tunnel) AND (hand surgery ambulatory) AND (local anesthesia) AND (trigger finger))"}
{"candidate_id": "LLM03940", "doc_id": "NCT02369211_inc", "case_bucket": "other", "source_criterion": "Patients undergoing robotic-assisted laparoscopic prostatectomy =18 years old males ASA class 1-4", "candidate_expression": "((1-4) AND (=18 years old) AND (ASA class) AND (males) AND (obotic-assisted laparoscopic prostatectomy) AND (years))"}
{"candidate_id": "LLM03941", "doc_id": "NCT03372304_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03942", "doc_id": "NCT02072811_exc", "case_bucket": "other", "source_criterion": "No informed consent for participation in the study, mental illness, which don't allow to obtain informed consent and conduct the treatment according to the protocol Pregnancy HIV infection Active cancer Active hepatitis virus infection", "candidate_expression": "((Active) AND (HIV infection) AND (Pregnancy) AND (cancer) AND (hepatitis virus infection))"}
{"candidate_id": "LLM03943", "doc_id": "NCT02478515_exc", "case_bucket": "or", "source_criterion": "Previous treatment with anti-VEGF drugs or corticosteroid or grid laser photocoagulation (study eye) History of vitrectomy surgery, submacular surgery, or other surgical intervention for RVO Ocular disorders in the study eye that may confound interpretation of study results BCVA over 77 letters between screening and Day 0 The pregnant or lactating woman", "candidate_expression": "((BCVA over 77 letters) AND (RVO) AND (The pregnant or lactating woman) AND (anti-VEGF drugs) AND (corticosteroid) AND (grid laser photocoagulation () AND (submacular surgery) AND (surgical intervention) AND (vitrectomy surgery))"}
{"candidate_id": "LLM03944", "doc_id": "NCT02277067_exc", "case_bucket": "other", "source_criterion": "Women undergoing cesarean section with general anesthesia will be excluded, because carbetocin is licensed for use with regional anaesthesia only. women undergoing cesarean section at less than 37 weeks of gestation.", "candidate_expression": "((Women) AND (cesarean section) AND (cesarean section general anesthesia) AND (gestation less than 37 weeks) AND (women))"}
{"candidate_id": "LLM03945", "doc_id": "NCT02961764_exc", "case_bucket": "or", "source_criterion": "Known or suspected gram-negative infections, anaerobic infections, or fungemia Known or suspected infections that are severe, life threatening or are not included in the ABSSSI Food and Drug Administration (FDA) guidance Injection drug users with a fever Severe neurological disorder leading to immobility or confined to a wheelchair Bilateral Lower extremity involvement of the suspected infection.", "candidate_expression": "((Bilateral Lower extremity) AND (Severe) AND (anaerobic) AND (drug users) AND (fever) AND (gram-negative) AND (infection) AND (infections) AND (life threatening) AND (neurological disorder) AND (severe) AND ((immobility) OR (wheelchair)) AND ((fungemia) OR (infections)))"}
{"candidate_id": "LLM03946", "doc_id": "NCT02698969_inc", "case_bucket": "other", "source_criterion": "ASA physical status I-II age between 18-80 years old dNMB with rocuronium during ear nose and throat (ENT) surgery", "candidate_expression": "((ASA physical status I-II) AND (age between 18-80 years) AND (dNMB with rocuronium) AND (ear nose and throat (ENT) surgery))"}
{"candidate_id": "LLM03947", "doc_id": "NCT02528604_inc", "case_bucket": "other", "source_criterion": "Patients with symptomatic persistent atrial fibrillation of less than 1-year duration. Patients must be over 65 years old. Patients give informed consent prior to participating in this study.", "candidate_expression": "((Patients give informed consent prior to participating in this study) AND (atrial fibrillation) AND (less than 1-year) AND (old) AND (over 65 years) AND (persistent) AND (symptomatic))"}
{"candidate_id": "LLM03948", "doc_id": "NCT02650388_exc", "case_bucket": "other", "source_criterion": "Died before TAVI Not willing to participate", "candidate_expression": "((Died) AND (Not willing to participate) AND (before TAVI))"}
{"candidate_id": "LLM03949", "doc_id": "NCT02245256_exc", "case_bucket": "or", "source_criterion": "Pediatric patients (under 18 years) Pregnancy Patients who are unresponsive at baseline, who have neurologic deficits at baseline, or who are allergic to dexmedetomidine", "candidate_expression": "((Pediatric) AND (Pregnancy) AND (dexmedetomidine) AND (years under 18 years) AND ((allergic) OR (neurologic deficits at baseline) OR (unresponsive at baseline)))"}
{"candidate_id": "LLM03950", "doc_id": "NCT03355326_inc", "case_bucket": "other", "source_criterion": "Diagnosis of uncomplicated gastroschisis Gestational age >33 weeks at time of delivery Weight >1900g at time of delivery Transfer of patient to Riley Hospital for Children prior to any abdominal surgery", "candidate_expression": "((>1900g) AND (>33 weeks) AND (Gestational age) AND (Riley Hospital for Children) AND (Transfer) AND (Weight) AND (abdominal surgery) AND (any abdominal surgery) AND (at time of delivery) AND (gastroschisis) AND (prior to any abdominal surgery) AND (uncomplicated))"}
```
