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
{"candidate_id": "LLM07701", "doc_id": "NCT02777580_inc", "case_bucket": "other", "source_criterion": "Age equal or greater than 70 years Onset of symptoms < 3 hours prior to randomisation = 2 mm ST-elevation across 2 contiguous precordial leads (V1-V6) or leads I and aVL for a minimum combined total of = 4 mm ST-elevation or = 2 mm ST-elevation in 2 contiguous inferior leads (II, III, aVF) for a minimum combined total of = 4 mm ST-elevation Informed consent received", "candidate_expression": "((Age equal or greater than 70 years) AND (Informed consent received) AND (Onset of symptoms < 3 hours prior to randomisation))"}
{"candidate_id": "LLM07702", "doc_id": "NCT00676273_inc", "case_bucket": "other", "source_criterion": "Are at least 18 years of age Demonstrate a positive cough stress test during complex multi-channel urodynamic testing Demonstrate impact of stress urinary incontinence on quality of life questionnaire Are able to comprehend and sign a written informed consent Understand and are willing to comply with the study requirements, including agreeing to be available for the follow-up evaluations Are psychologically stable and suitable for interventions determined by the investigator Are ambulatory and able to use a toilet independently", "candidate_expression": "((Understand the study requirements) AND (able to comprehend a written informed consent) AND (able to sign a written informed consent) AND (able to use a toilet independently) AND (age at least 18 years) AND (ambulatory) AND (complex multi-channel urodynamic testing) AND (cough stress test positive) AND (psychologically stable) AND (quality of life questionnaire) AND (stress urinary incontinence) AND (suitable for interventions) AND (willing to comply with the study requirements))"}
{"candidate_id": "LLM07703", "doc_id": "NCT03499639_inc", "case_bucket": "other", "source_criterion": "patients were 18 years old or more, naive to HCV treatment, HCV genotype 4, compensated liver disease.", "candidate_expression": "((HCV genotype 4) AND (liver disease compensated) AND (old 18 years old or more) AND NOT (HCV treatment))"}
{"candidate_id": "LLM07704", "doc_id": "NCT02056301_exc", "case_bucket": "other", "source_criterion": "1) Refusal of epidural catheter 2) Pregnancy 3) Bleeding History 4) Inability to understand how to use the PCA device 5) Medication interfering with blood coagulation 6) Patients allergic to local anesthetics 7) Patient refusal to participate in study 8) Developmental delay", "candidate_expression": "((Bleeding) AND (Developmental delay) AND (History) AND (Medication) AND (Pregnancy) AND (Refusal) AND (allergic) AND (epidural catheter) AND (interfering with blood coagulation) AND (local anesthetics))"}
{"candidate_id": "LLM07705", "doc_id": "NCT03064568_inc", "case_bucket": "other", "source_criterion": "Female age 20-50 y/o who plan to undergo abdominal myomectomy for symptomatic myomatous uterus", "candidate_expression": "((20-50 y/o) AND (Female) AND (abdominal myomectomy) AND (age) AND (myomatous uterus) AND (plan to undergo) AND (symptomatic))"}
{"candidate_id": "LLM07706", "doc_id": "NCT02455921_inc", "case_bucket": "other", "source_criterion": "Children undergoing ENT surgery under general anaesthesia.", "candidate_expression": "((Children) AND (ENT surgery undergoing) AND (general anaesthesia))"}
{"candidate_id": "LLM07707", "doc_id": "NCT01680081_inc", "case_bucket": "or", "source_criterion": "Men and women patients, with age ranging 40-80. Suspected coronary artery disease who are supposed to undergo invasive coronary angiography with appropriate clinical indications Patients who are willing to sign the informed consent form", "candidate_expression": "((Men) AND (Patients who are willing to sign the informed consent form) AND (age ranging 40-80) AND (coronary artery disease Suspected) AND (invasive coronary angiography supposed to undergo) AND (women))"}
{"candidate_id": "LLM07708", "doc_id": "NCT01116973_inc", "case_bucket": "or", "source_criterion": "Subject's ability to lay in a supine position with their hands at their sides during CVP measurements A consent form signed by the patient or patient's representative Subjects that are age 18-90 Subjects that have an indwelling CICC and are transitioning to a PICC for long-term IV access CICC placed in the internal jugular vein or subclavian vein position", "candidate_expression": "((A consent form signed by the patient or patient's representative) AND (CICC placed) AND (CVP measurements) AND (PICC) AND (ability to lay in a supine position with their hands at their sides during CVP measurements) AND (age 18-90) AND (indwelling CICC) AND (transitioning to a PICC) AND ((in the internal jugular vein position) OR (in the subclavian vein position)))"}
{"candidate_id": "LLM07709", "doc_id": "NCT02312089_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities. Myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Myoma) AND (Uterine abnormalities) AND (endometriosis) AND (uterine surgery) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM07710", "doc_id": "NCT02361892_exc", "case_bucket": "or", "source_criterion": "endometrial hyperplasia with atypia, estrogen-progestin therapy in the 2 months before enrollment, autoimmune diseases, chronic, metabolic, systemic and endocrine disorders, including hyperandrogenism, hyperprolactinemia, diabetes mellitus and thyroid disease, hypogonadotropic hypogonadism, majors clinical conditions", "candidate_expression": "((atypia) AND (autoimmune diseases) AND (chronic disorders) AND (endocrine disorders) AND (endometrial hyperplasia) AND (estrogen-progestin therapy) AND (hypogonadotropic hypogonadism) AND (in the 2 months before enrollment) AND (majors clinical conditions) AND (metabolic disorders) AND (systemic disorders) AND ((diabetes mellitus) OR (hyperandrogenism) OR (hyperprolactinemia) OR (thyroid disease)))"}
{"candidate_id": "LLM07711", "doc_id": "NCT02747940_inc", "case_bucket": "or", "source_criterion": "Control: devoid of any systemic or neurological diseases Chronic migraine: by ICHD-III (International Classification of Headache Disorder) criteria Fibromyalgia: by ACR (American College of Rheumatology) 2010 criteria", "candidate_expression": "((ACR 2010 criteria) AND (American College of Rheumatology) AND (Chronic migraine) AND (Fibromyalgia) AND (ICHD-III) AND (International Classification of Headache Disorder) AND (devoid) AND ((neurological diseases) OR (systemic diseases)))"}
{"candidate_id": "LLM07712", "doc_id": "NCT03323047_exc", "case_bucket": "or", "source_criterion": "Patients Level III or greater on the American Society of Anesthesiologists (ASA) physical status classification system (as determined by the anesthesiologist) Patients with chronic conditions that would limit our ability to develop the study according to objectives, such as neurodevelopmental conditions preventing patients from understanding the Oucher tool Hepatic or renal disease cardiac disease active infection diabetes mellitus sickle cell disease known coagulation disorders pre- operative treatment with anti-emetics, steroids, or analgesics Acetaminophen allergy or already receiving acetaminophen within 24 h of surgery Complicating health factors precluding the use of opioids or acetaminophen any other factors which would interfere with pain assessment and management Patients weighing more than 30 kg that would exceed maximum dexamethasone dose Patients who live without a home telephone patient living without parental supervision.", "candidate_expression": "((Acetaminophen) AND (American Society of Anesthesiologists (ASA) physical status) AND (Complicating health factors) AND (Hepatic disease) AND (Level III or greater) AND (acetaminophen) AND (active) AND (allergy) AND (analgesics) AND (anti-emetics) AND (cardiac disease) AND (chronic conditions) AND (coagulation disorders) AND (diabetes mellitus) AND (infection) AND (interfere) AND (limit our ability to develop the study according to objectives) AND (management) AND (more than 30 kg) AND (neurodevelopmental conditions) AND (opioids) AND (other factors) AND (pain assessment) AND (pre- operative) AND (precluding) AND (preventing) AND (renal disease) AND (sickle cell disease) AND (steroids) AND (treatment) AND (understanding the Oucher tool) AND (weighing) AND (within 24 h of surgery))"}
{"candidate_id": "LLM07713", "doc_id": "NCT03036462_exc", "case_bucket": "or", "source_criterion": "Hypersensitivity to the active substance, to FCM or any of its excipients Known serious hypersensitivity to other parenteral iron products Anaemia not attributed to iron deficiency, e.g. other microcytic anaemia Evidence of iron overload or disturbances in the utilisation of iron", "candidate_expression": "((Anaemia) AND (FCM) AND (Hypersensitivity) AND (active substance) AND (disturbances in the utilisation of iron) AND (excipients) AND (hypersensitivity serious) AND (iron) AND (iron overload) AND (microcytic anaemia other) AND (parenteral iron products) AND NOT (iron deficiency attributed to))"}
{"candidate_id": "LLM07714", "doc_id": "NCT03372304_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologists Classification I-III Normal cognitive function in order to sign written, informed consent and to understand trial protocol Agreement to the trial protocol, including the randomized manner", "candidate_expression": "((Agreement to the trial protocol, including the randomized manner) AND (American Society of Anesthesiologists Classification) AND (I-III) AND (ormal cognitive function in order to sign written, informed consent and to understand trial protoco))"}
{"candidate_id": "LLM07715", "doc_id": "NCT02787070_inc", "case_bucket": "or", "source_criterion": "Infection with Plasmodium falciparum or P. vivax either alone or mixed Age >12 months Weight >5kg Living in the study clusters", "candidate_expression": "((Age >12 months) AND (Infection) AND (Weight >5kg) AND ((P. vivax) OR (Plasmodium falciparum)))"}
{"candidate_id": "LLM07716", "doc_id": "NCT02231892_exc", "case_bucket": "or", "source_criterion": "1. Personal history of stroke, brain lesions, previous neurosurgery, any personal history of seizure or fainting episode of unknown cause, or head trauma resulting in loss of consciousness, lasting over 30 minutes or with sequela lasting longer than two days. Justification: Stroke or head trauma can lower the seizure threshold, and are therefore contra-indications for TMS. Fainting episodes or syncope of unknown cause could indicate an undiagnosed condition associated with seizures. Screening tool: TMS adult safety questionnaire, Medical History. 2. First-degree family history of any neurological disorder with a potentially hereditary basis, including migraines, epilepsy, or multiple sclerosis. 1. Justification: Neurological disorders can lower the seizure threshold, and are therefore contra-indications for TMS. First-degree family history of certain neurological disorders with a hereditary component increases the risk of the subject having an undiagnosed condition that is associated with lowered seizure threshold. 2. Screening tool: TMS adult safety screening, Medical History. 3. Cardiac pacemakers, neural stimulators, implantable defibrillator, implanted medication pumps, intracardiac lines, or acute, unstable cardiac disease, with intracranial implants (e.g. aneurysm clips, shunts, stimulators, cochlear implants, or electrodes) or any other metal object within or near the head that precludes MRI scanning. 1. Justification: Any metal around the head is a contraindication for both MRI and TMS, as both methods involve exposure to a relatively strong magnetic field. 2. Screening tool: TMS adult safety screening, MRI safety screening, Medical History. 4. Noise-induced hearing loss or tinnitus. 1. Justification: individuals with noise-induced hearing problems may be particularly vulnerable to the acoustic noise generated by TMS and MRI equipment. 2. Screening tools: TMS adult safety screening. 5. Current use (any use in the past 4 weeks, chronic use within 6 past six months) of any investigational drug or of any medications with psychotropic, anti or pro-convulsive action. 1. Justification: The use of certain medications or drugs can lower seizure threshold and is therefore contra-indicated for TMS. 2. Screening tools: MRI safety screening questionnaire, Medical history, Medical Assessments: Urine toxicology analyzes for presence of a broad range of prescription and nonprescription drugs. 6. Lifetime history of major depressive disorder, schizophrenia, bipolar disorder, mania, or hypomania. 1. Justification: The population of interest here is a healthy control population with no psychiatric disorders. In subjects with depression, bipolar disorder, mania or hypomania, there is a small chance that TMS can trigger (hypo)manic symptoms. 2. Screening tools: SCID Screen Patient Questionnaire. Potential diagnoses will be further evaluated by a counsellor. 7. Meet current DSM V criteria for moderate to severe substance use disorder (excluding nicotine), smoke daily, or urine toxicology positive for any illicit substance inconsistent with history given. 1. Justification: The population of interest here is a healthy control population with no substance use disorder. Current use of illicit substances could impact on seizure threshold and is therefore contra-indicated for TMS. 2. Screening tools: SCID Screen Patient Questionnaire. Potential diagnoses will be further evaluated by a counsellor, Drug Use Survey (DUS), Substance Use Disorder Evaluation, Medical Assessments: urine qualitative drug screen is performed for methadone, benzodiazepines, cocaine, amphetamine/methamphetamine, opiates, barbiturates, and tetrahydrocannabinol. 8. Have met DSM V criteria for moderate to severe substance use disorder (excluding nicotine, alcohol and cannabis) in the past, or have met DSM V criteria for moderate to severe substance use disorder for cannabis or alcohol in the past 5 years. 1. Justification: the population of interest here is a healthy control population with no present or past substance use disorder. 2. Screening tools: SCID Screen Patient Questionnaire. Potential diagnoses will be further evaluated by a counselor. Drug Use Survey (DUS), Substance Use Disorder Evaluation. 9. History of myocardial infarction, angina, congestive heart failure, cardiomyopathy, stroke or transient ischemic attack, or any heart condition currently under medical care. 1. Justifications: the risk of TMS for individuals with a heart condition is unknown. 2. Screening tool: physical assessment (EKG), medical history. 10. Pregnant women or women with reproductive potential who are sexually active and not using an acceptable form of contraception. 1. Justification: it is unknown whether TMS poses a risk to fetuses. 2. Screening tool: Medical assessments (urine pregnancy test) at the beginning of each visit that involves TMS or MRI. 11. History of learning disability or current ADHD 1. Justification: Subjects should be able to perform cognitive tasks to a high degree of accuracy, both in the MRI scanner and outside the scanner. Subjects with ADHD/LD may engage different neural circuitry even if they can perform the tasks. 2. Screening tool: Wechsler Abbreviated Scale of Intelligence, Medical history, Adult ADHD Self-Report Scale. 12. Participation in an rTMS session less than two weeks ago. 1. Justification: in order to limit exposure to TMS, we will not enroll subjects who have received TMS less than two weeks ago. 2. Screening tool: TMS safety screening questionnaire.", "candidate_expression": "((ADHD) AND (Adult ADHD Self-Report Scale) AND (Current use) AND (DSM V criteria) AND (Drug Use Survey (DUS)) AND (First-degree) AND (History) AND (LD) AND (Lifetime history of) AND (MRI) AND (MRI safety screening) AND (MRI safety screening questionnaire) AND (MRI scanning) AND (Medical History) AND (Medical assessments) AND (Medical history) AND (Meet) AND (Potential diagnoses will be further evaluated by a counselor.) AND (Pregnant) AND (SCID Screen Patient Questionnaire) AND (Screening) AND (Substance Use Disorder Evaluation) AND (TMS adult safety questionnaire) AND (TMS adult safety screening) AND (TMS safety screening questionnaire) AND (Urine toxicology analyzes) AND (Wechsler Abbreviated Scale of Intelligence) AND (acceptable form of) AND (acute) AND (alcohol) AND (at the beginning of each visit) AND (cannabis) AND (contraception) AND (current) AND (currently) AND (drugs) AND (excluding) AND (family history of) AND (heart condition) AND (history of) AND (illicit substance) AND (in the past) AND (in the past 4 weeks) AND (in the past 5 years) AND (inconsistent with history) AND (intracranial implants) AND (lasting) AND (less than two weeks ago) AND (longer than two days) AND (met) AND (moderate to severe) AND (neurological disorder) AND (nicotine) AND (not) AND (personal history of) AND (positive) AND (potentially hereditary basis) AND (precludes) AND (precludes MRI scanning) AND (previous) AND (rTMS session) AND (reproductive potential) AND (safety screening questionnaire) AND (sexually active) AND (substance use disorder) AND (the beginning of each visit) AND (transient ischemic attack) AND (under medical care) AND (unknown cause) AND (unstable) AND (urine pregnancy test) AND (within 6 past six months) AND (women) AND ((smoke daily) OR (urine toxicology)) AND ((DSM V criteria) OR (substance use disorder)) AND ((alcohol) OR (cannabis)) AND ((brain lesions) OR (neurosurgery) OR (stroke)) AND ((fainting episode) OR (head trauma resulting in loss of consciousness) OR (seizure)) AND ((lasting over 30 minutes) OR (sequela)) AND ((epilepsy) OR (migraines) OR (multiple sclerosis)) AND ((Cardiac pacemakers) OR (cardiac disease) OR (implantable defibrillator) OR (implanted medication pumps) OR (intracardiac lines) OR (metal object within or near the head) OR (neural stimulators)) AND ((aneurysm clips) OR (cochlear implants) OR (electrodes) OR (shunts) OR (stimulators)) AND ((Noise-induced hearing loss) OR (tinnitus)) AND ((any use) OR (chronic use)) AND ((investigational drug) OR (medications)) AND ((pro-convulsive action) OR (psychotropic action)) AND ((nonprescription) OR (prescription)) AND ((bipolar disorder) OR (hypomania) OR (major depressive disorder) OR (mania) OR (schizophrenia)) AND ((ADHD) OR (learning disability)) AND ((MRI) OR (TMS)) AND ((angina) OR (cardiomyopathy) OR (congestive heart failure) OR (myocardial infarction) OR (stroke)))"}
{"candidate_id": "LLM07717", "doc_id": "NCT03154931_exc", "case_bucket": "or", "source_criterion": "Suicidal patients and/or severe automutilation behavior and/or psychotic symptoms and/or lack of event memory.", "candidate_expression": "((Suicidal) AND (automutilation behavior severe) AND (lack of event memory) AND (psychotic symptoms))"}
{"candidate_id": "LLM07718", "doc_id": "NCT02965027_exc", "case_bucket": "or", "source_criterion": "Participation in other interventional research. History of penetrating head injury History of TBI more severe than mild by DVBIC criteria Diagnosis of a primary or secondary HA disorder other than PTHA Lifetime history of 5 or more migraine or probable migraine headaches pre-dating mTBI HAs of any kind of moderate or severe intensity on an average of more than 2 days per month preceding the concussive trauma Continuous HAs of any kind (i.e., persistent daily HAs with no HA-free period less than 8 hours between attacks) Acute or serious medical illness or unstable chronic medical illness (e.g., unstable angina, myocardial infarction within 6 months, congestive heart failure, clinically significant or concerning cardiac arrhythmias; preexisting hypotension [systolic blood pressure<110] or orthostatic hypotension [systolic drop >20 mm Hg after 2 min standing accompanied by lightheadedness], chronic renal or hepatic failure, acute pancreatitis, Meniere's disease, or diagnosed but untreated sleep apnea). The eligibility of potential participants having acute serious and/or chronic medical illnesses other than those listed will be evaluated on a case-by-case basis by a study physician, PA-C, or ARNP. Use of prazosin or other alpha-1 antagonist (including but not limited to alfuzosin, doxazosin, silodosin, tamsulosin, terazosin) for any purpose in the 2 weeks prior to initial screen (P1) visit and prohibited throughout the study Allergy or previous adverse reaction to prazosin or other alpha-1 antagonist Active psychosis or psychotic disorder, severe depression (as determined per clinician prescriber judgment), severe psychiatric instability or severe situational life crisis (including evidence of being actively suicidal or homicidal). Meets Diagnostic and Statistical Manual of Mental Disorders, 5th Edition (DSM-5) criteria for any Substance Use Disorder except caffeine-related disorders, or tobacco-related disorders. History of delirium within the prior 3 months, epilepsy, stroke, dementia, psychotic disorder, or bipolar disorder Structural brain abnormalities on any prior imaging with associated clinically evident manifestations Current participation in transcranial magnetic stimulation studies Women of childbearing potential must not be pregnant, planning to become pregnant during the study period, or nursing. Participation in a HA support group or other activity such as meditation or yoga intended to mitigate HA or other chronic pain must be stable at least 4 weeks prior to beginning the initial screen (P1) visit and may not be started during the study Failure to record HA data for at least 80% of days during the Screening Period Not suitable for study per clinician judgement. The use of HA rescue or symptom-relieving medications will be allowed during the study. This includes triptans, ergotamines, opioids, simple analgesics (e.g. acetaminophen, aspirin, or non-steroidal anti-inflammatories [NSAIDS], and combination analgesics. Their use will be recorded on the concurrent medication CRF during the Preliminary Screening Period (P1) and throughout the remainder of the study. Randomization of participants will be stratified based on whether their use of HA medications meets ICHD-3 beta criteria for overuse of these medications, as described in section 5.5 below. Opioid Medications: Use of opioids for treatment of HA or non-HA-related pain or for any other purpose is allowed during the study. Any opioid use would ideally be excluded due to potential confounding effects on interpretation of response to treatment. However, in this population, particularly in Veterans with chronic pain or undergoing minor orthopedic or dental procedures, opioid use is common. Use of opioids, including frequency and dose, will be recorded on the concurrent medication CRF. Other Medications: Participants who are taking other medications on a routine basis must be on a stable dose for at least 4 weeks prior to the Preliminary Screening Period (P1), and must intend to continue the medication at the same regimen for the duration of the trial unless lack of efficacy, safety, or tolerability dictates otherwise. The following medications are not excluded: Psychoactive drugs (for example, anticonvulsants, benzodiazepines, antidepressants, sedative/hypnotics), Antihypertensive medications (including beta-blockers, calcium channel blockers, angiotensin converting enzyme [ACE] inhibitors, and angiotensin receptor blockers), The use of magnesium in any dose that is prescribed for the purpose of HA prevention or treatment must be stable for at least 4 weeks. The incidental use of magnesium in multi-vitamins, laxatives, etc. is permissible but must be documented. Hormones (for example, testosterone, estrogen, or progesterone) in any form. The \"as-needed\" (prn) use of psychoactive and other drugs such as antibiotics is not excluded; however, such use must be discussed with a clinician prescriber and documented. The use of butalbital in any form within 4 weeks of beginning the Preliminary Screening Period (P1) through the end of the participant's study involvement is exclusionary. Participants who have been taking trazodone will undergo a 2-week washout period before the Preliminary Screening Period (P1 visit). Combining prazosin and trazodone may increase the risk of priapism. We have decided to begin the washout period before the Preliminary Screening Period in order to remove any confounding variables while on the headache log and actigraphy. Sildenafil (Viagra), tadalafil (Cialis), vardenafil (Levitra), and avanafil (Stendra) will not be permitted during the study drug dose Titration Period, because of increased risk of hypotension in combination with alpha-1 blockers, but will be allowed at half the usual starting dose following the study drug dose Titration Period, per VA prescribing guidelines. Use of supplements containing nitrates and supplements containing stimulants (such as ephedra) are exclusionary in the two weeks prior to initial screen (P1) visit and prohibited throughout the study. Participants who take these supplements will be asked to discontinue them for a minimum of two weeks before the Preliminary Screening Period (P1 visit).. Use of prescribed stimulants (such as amphetamine or dextroamphetamine containing medications) is exclusionary in the 2 weeks prior to the initial screen (P1) visit and prohibited throughout the study. Participants who take these medications will be asked to discontinue them for a minimum of 2 weeks before the Preliminary Screening Period.", "candidate_expression": "((5 or more) AND (<110) AND (>20 mm Hg) AND (Active) AND (Cialis) AND (Continuous) AND (Current) AND (DVBIC criteria) AND (Diagnostic and Statistical Manual of Mental Disorders, 5th Edition (DSM-5) criteria) AND (Failure to record HA data) AND (HA disorder) AND (HA-free period between attacks) AND (HAs) AND (Levitra) AND (Lifetime history) AND (Meets) AND (PTHA) AND (Participation in a HA support group) AND (Stendra) AND (Structural brain abnormalities) AND (Substance Use Disorder) AND (TBI) AND (Viagra) AND (Women) AND (after 2 min standing) AND (any) AND (average of more than 2 days per month) AND (butalbital) AND (childbearing potential) AND (clinically evident) AND (daily) AND (during the Screening Period) AND (during the study drug dose Titration Period) AND (during the study period) AND (ephedra) AND (except) AND (for at least 4 weeks prior to the Preliminary Screening Period (P1)) AND (for at least 80% of days) AND (imaging) AND (in the 2 weeks prior to initial screen (P1) visit) AND (in the 2 weeks prior to the initial screen (P1) visit) AND (in the two weeks prior to initial screen (P1) visit) AND (initial screen (P1) visit) AND (less than 8 hours) AND (lightheadedness) AND (mTBI) AND (manifestations) AND (medications) AND (meditation) AND (moderate or severe intensity) AND (more severe than mild) AND (no) AND (not be) AND (on a routine basis) AND (other) AND (other than) AND (penetrating head injury) AND (persistent) AND (planning to become) AND (pre-dating mTBI) AND (preceding the concussive trauma) AND (preexisting) AND (prescribed stimulants) AND (previous) AND (prior) AND (probable) AND (severe) AND (stable dose) AND (systolic blood pressure) AND (systolic drop) AND (transcranial magnetic stimulation studies) AND (unstable) AND (untreated) AND (within 4 weeks of beginning the Preliminary Screening Period (P1)) AND (within 6 months) AND (within the prior 3 months) AND (yoga) AND ((bipolar disorder) OR (delirium) OR (dementia) OR (epilepsy) OR (psychotic disorder) OR (stroke)) AND ((nursing) OR (pregnant)) AND ((migraine)) AND ((Sildenafil) OR (avanafil) OR (tadalafil) OR (vardenafil)) AND ((nitrates) OR (stimulants)) AND ((amphetamine) OR (dextroamphetamine)) AND ((Acute) OR (serious)) AND ((chronic medical illness) OR (medical illness)) AND ((clinically significant) OR (concerning)) AND ((Meniere's disease) OR (acute pancreatitis) OR (cardiac arrhythmias) OR (chronic renal failure) OR (congestive heart failure) OR (hepatic failure) OR (hypotension) OR (myocardial infarction) OR (orthostatic hypotension) OR (sleep apnea) OR (unstable angina)) AND ((primary) OR (secondary)) AND ((alpha-1 antagonist) OR (prazosin)) AND ((alfuzosin) OR (doxazosin) OR (silodosin) OR (tamsulosin) OR (terazosin)) AND ((Allergy) OR (adverse reaction)) AND ((psychiatric instability) OR (psychosis) OR (psychotic disorder) OR (severe depression) OR (situational life crisis)) AND ((homicidal) OR (suicidal)) AND ((caffeine-related disorders) OR (tobacco-related disorders)))"}
{"candidate_id": "LLM07719", "doc_id": "NCT01822262_exc", "case_bucket": "or", "source_criterion": "Gallbladder's wall >3mm, atrophied gallbladder,gallstone obstruct the Hartmann's pouch. Abdominal ultrasound display the contractibility of gallbladder is poor. The aged patients with bad heart and lung function. Patients who has acute cholecystitis,pancreatitis,pancreaticobiliary diseases, especially choledocholithiasis. Pregnant or lactational women.", "candidate_expression": "((Abdominal ultrasound) AND (Gallbladder's wall >3mm) AND (Pregnant) AND (acute cholecystitis) AND (aged) AND (atrophied gallbladder) AND (bad heart function) AND (bad lung function) AND (choledocholithiasis) AND (contractibility of gallbladder poor) AND (gallstone obstruct Hartmann's pouch) AND (lactational) AND (pancreaticobiliary diseases) AND (pancreatitis) AND (women))"}
{"candidate_id": "LLM07720", "doc_id": "NCT03247413_inc", "case_bucket": "or", "source_criterion": "patients with a diagnosis of either cervical, thoracic, or lumbar facet or sacroiliac joint pain who have responded to medial branch blocks and are already scheduled for bilateral radiofrequency ablations age greater than 18 years old English speaking", "candidate_expression": "((English speaking) AND (age greater than 18 years old) AND (bilateral radiofrequency ablations scheduled for) AND (medial branch blocks) AND ((cervical joint pain) OR (lumbar facet joint pain) OR (sacroiliac joint pain) OR (thoracic joint pain)))"}
{"candidate_id": "LLM07721", "doc_id": "NCT02933671_inc", "case_bucket": "other", "source_criterion": "English speaking between 18 and 75 years old American Society of Anesthesiologists (ASA) 1-3 patients undergoing primary total hip arthroplasty", "candidate_expression": "((1-3) AND (ASA) AND (American Society of Anesthesiologists) AND (between 18 and 75 years) AND (old) AND (primary total hip arthroplasty))"}
{"candidate_id": "LLM07722", "doc_id": "NCT02464813_exc", "case_bucket": "or", "source_criterion": "Other spinal pathology or other associated medical condition Major neurologic developmental delay Need for anterior surgery or for vertebral column resection. Preoperative opioid use Inability to use PCA", "candidate_expression": "((Inability to use) AND (Major neurologic developmental delay) AND (PCA) AND (anterior surgery Need for) AND (associated medical condition) AND (opioid Preoperative) AND (spinal pathology) AND (vertebral column resection))"}
{"candidate_id": "LLM07723", "doc_id": "NCT02654912_inc", "case_bucket": "other", "source_criterion": "anyone not excluded and consenting", "candidate_expression": "(anyone not excluded and consenting)"}
{"candidate_id": "LLM07724", "doc_id": "NCT01803828_exc", "case_bucket": "or", "source_criterion": "congenital or valvular cardiomyopathy; ischemic heart disease; endocrine diseases: male hypogonadism, hyperthyroidism, adrenal diseases, pituitary diseases proliferative retinopathy or autonomic neuropathy; contraindications to sildenafil use or CMR imaging;", "candidate_expression": "((CMR imaging) AND (adrenal diseases) AND (autonomic neuropathy) AND (cardiomyopathy) AND (congenital) AND (contraindications) AND (endocrine diseases) AND (hyperthyroidism) AND (ischemic heart disease) AND (male hypogonadism) AND (pituitary diseases) AND (proliferative retinopathy) AND (sildenafil) AND (valvular))"}
{"candidate_id": "LLM07725", "doc_id": "NCT03648021_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to paracetamol or mannitol (excipient with known effect) Severe hepatocellular insufficiency (ASAT or ALAT > 5N, or bilirubin > 2N) Pharmacological intervention (administration of corticosteroids, NSAIDs or paracetamol) or physical intervention (external cooling technique) that may influence temperature in the last 6 hours. Pregnant or breastfeeding women Previous participation in this study", "candidate_expression": "((ALAT > 5N) AND (ASAT > 5N) AND (NSAIDs) AND (Pharmacological) AND (Pharmacological intervention) AND (Pregnant) AND (Previous participation in this study) AND (bilirubin > 2N) AND (breastfeeding) AND (corticosteroids) AND (external cooling technique) AND (hepatocellular insufficiency) AND (hypersensitivity) AND (mannitol) AND (paracetamol) AND (physical intervention) AND (temperature) AND (women))"}
```
