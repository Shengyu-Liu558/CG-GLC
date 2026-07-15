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
{"candidate_id": "LLM07526", "doc_id": "NCT02287259_exc", "case_bucket": "or", "source_criterion": "don't have Diabetes and abnormal metabolism of sugar not noticed as bipolar disorder have an organic brain disease pregnant or breastfeeding women don't have heart disease have actively suicidal thought(Suicidal ideation score of MADRS is 6) who are judged by the investigator to should be excluded from the study", "candidate_expression": "((Diabetes) AND (Suicidal ideation score of MADRS 6) AND (abnormal metabolism of sugar) AND (actively suicidal thought) AND (breastfeeding) AND (judged by the investigator to should be excluded from the study) AND (organic brain disease) AND (pregnant) AND (women) AND NOT (heart disease) AND NOT (bipolar disorder noticed))"}
{"candidate_id": "LLM07527", "doc_id": "NCT01373684_exc", "case_bucket": "or", "source_criterion": "Treatment with any investigational drug within 30 days of entry to this protocol Current treatment with Telbivudine Severe hepatitis activity as documented by ALT>10 x ULN History of decompensated cirrhosis (defined as jaundice in the presence of cirrhosis, ascites, bleeding gastric or esophageal varices or encephalopathy) Pre-existent neutropenia (neutrophils <1,500/mm3) or thrombocytopenia (platelets < 90,000/mm3) Co-infection with hepatitis C virus, hepatitis D virus or human immunodeficiency virus (HIV) Other acquired or inherited causes of liver disease: alcoholic liver disease, obesity induced liver disease, drug related liver disease, auto-immune hepatitis, hemochromatosis, Wilson's disease or alpha-1 antitrypsin deficiency Alpha fetoprotein > 50 ng/ml Hyper- or hypothyroidism (subjects requiring medication to maintain TSH levels in the normal range are eligible if all other inclusion/exclusion criteria are met) Immune suppressive treatment within the previous 6 months Contra-indications for alfa-interferon therapy like suspected hypersensitivity to interferon or Peginterferon or any known pre-existing medical condition that could interfere with the patient's participation in and completion of the study. Pregnancy, breast-feeding Other significant medical illness that might interfere with this study: significant pulmonary dysfunction in the previous 6 months, malignancy other than skin basocellular carcinoma in previous 5 years, immunodeficiency syndromes (e.g. HIV positivity, auto-immune diseases, organ transplants other than cornea and hair transplant) Any medical condition requiring, or likely to require chronic systemic administration of steroids, during the course of the study Substance abuse, such as alcohol (>80 g/day), I.V. drugs and inhaled drugs in the past 2 years. Any other condition which in the opinion of the investigator would make the patient unsuitable for enrollment, or could interfere with the patient participating in and completing the study", "candidate_expression": "((< 90,000/mm3) AND (<1,500/mm3) AND (> 50 ng/ml) AND (>10 x ULN) AND (>80 g/day) AND (ALT) AND (Alpha fetoprotein) AND (Co-infection) AND (Contra-indications) AND (HIV) AND (HIV positivity) AND (Hyper thyroidism) AND (I.V. drugs) AND (Immune suppressive treatment) AND (Peginterferon) AND (Pre-existent) AND (Pregnancy, breast-feeding) AND (Severe) AND (Substance abuse) AND (Telbivudine) AND (Treatment with any investigational drug within 30 days of entry to this protocol) AND (Wilson's disease) AND (acquired) AND (alcohol) AND (alcoholic liver disease) AND (alfa-interferon therapy) AND (alpha-1 antitrypsin deficiency) AND (ascites) AND (auto-immune diseases) AND (auto-immune hepatitis) AND (bleeding gastric) AND (chronic) AND (cirrhosis) AND (cornea transplant) AND (course of the study) AND (decompensated) AND (drug related liver disease) AND (during the course of the study) AND (encephalopathy) AND (esophageal varices) AND (hair transplant) AND (hemochromatosis) AND (hepatitis) AND (hepatitis C virus) AND (hepatitis D virus) AND (human immunodeficiency virus) AND (hypersensitivity) AND (hypothyroidism) AND (immunodeficiency syndromes) AND (in previous 5 years) AND (in the past 2 years.) AND (in the previous 6 months) AND (inhaled drugs) AND (inherited) AND (interferon) AND (jaundice) AND (liver disease) AND (malignancy) AND (medical illness) AND (medication) AND (neutropenia) AND (neutrophils) AND (obesity induced liver disease) AND (organ transplants) AND (other than) AND (platelets) AND (pulmonary dysfunction) AND (significant) AND (skin basocellular carcinoma) AND (systemic steroids) AND (thrombocytopenia) AND (within the previous 6 months))"}
{"candidate_id": "LLM07528", "doc_id": "NCT03335436_exc", "case_bucket": "or", "source_criterion": "use illicit drugs or relapse during the last trimester of pregnancy positive drug screen at the time of delivery allergies to any medications used in the study taking prescribed gabapentin at the time of admission for CD contraindications to neuraxial anesthesia or require general anesthesia for CD designated ASA physical status 4 or above", "candidate_expression": "((ASA physical status 4 or above) AND (CD) AND (admission) AND (allergies) AND (contraindications) AND (delivery) AND (drug screen positive at the time of delivery) AND (gabapentin prescribed at the time of admission for CD) AND (general anesthesia require) AND (illicit drugs) AND (medications used in the study) AND (neuraxial anesthesia) AND (pregnancy last trimester) AND (relapse))"}
{"candidate_id": "LLM07529", "doc_id": "NCT02760251_inc", "case_bucket": "or", "source_criterion": "Informed consent as documented by signature (see informed consent form) Primary ITP according to the definition of Rodeghiero et al. (52) and a platelet count of <30x109/l Age range: 18-45 years Previously treated patients, with failure or intolerance to first-line therapy, or relapse after first-line therapy, i.e. corticosteroids, intravenous immunoglobulin (IVIG), or anti-D immunoglobulins", "candidate_expression": "((18-45 years) AND (<30x109/l) AND (Age) AND (IVIG) AND (Informed consent as documented by signature (see informed consent form)) AND (Previously treated) AND (Primary ITP) AND (after first-line therapy) AND (definition of Rodeghiero) AND (failure) AND (first-line therapy) AND (intolerance) AND (platelet count) AND ((first-line therapy) OR (relapse)) AND ((anti-D immunoglobulins) OR (corticosteroids) OR (intravenous immunoglobulin)))"}
{"candidate_id": "LLM07530", "doc_id": "NCT02348918_inc", "case_bucket": "or", "source_criterion": "Male or female, 18 years of age or older. Study eye with clinically significant diabetic macular edema (DME) with central subfield thickness ≥ 350µm on spectral domain OCT Best corrected visual acuity (BCVA) of 20/50 to 20/320 ETDRS equivalent (65 letters to 23 letters) in the study eye, with BCVA decrement primarily attributable to DME. Treatment naïve, i.e., no previous anti-VEGF treatment in the study eye or no anti-VEGF treatment in the 45 days prior to study enrollment. In the investigator's opinion, the subject still has significant intraretinal fluid with room for improvement in both macular edema and BCVA. Intra-Ocular Pressure (IOP) is under control (i.e., IOP ≤ 25 mm in the study eye) and study eye is not receiving any IOP lowering drops. Willing and able to return for all study visits. Able to meet the extensive post-op evaluation regimen. Understands and signs the informed consent form.", "candidate_expression": "((18 years or older) AND (20/50 to 20/320 ETDRS equivalent) AND (65 letters to 23 letters) AND (Able to meet the extensive post-op evaluation regimen.) AND (BCVA) AND (Best corrected visual acuity (BCVA)) AND (IOP) AND (IOP lowering drops) AND (Intra-Ocular Pressure (IOP)) AND (Treatment naïve) AND (Understands and signs the informed consent form.) AND (Willing and able to return for all study visits.) AND (age) AND (central subfield thickness) AND (clinically significant) AND (diabetic macular edema (DME)) AND (in the 45 days prior to study enrollment) AND (in the study eye) AND (intraretinal fluid) AND (macular edema) AND (no) AND (not) AND (previous) AND (significant) AND (spectral domain OCT) AND (study enrollment) AND (study eye) AND (under control) AND (with room for improvement) AND (≤ 25 mm) AND (≥ 350µm) AND ((Male) OR (female)) AND ((anti-VEGF treatment)))"}
{"candidate_id": "LLM07531", "doc_id": "NCT03404479_inc", "case_bucket": "other", "source_criterion": "Subjects who voluntarily consented, after listening enough explanation for this study and investigational product. Adult over 50 years of age. At least one of the knee pain VAS score is 40mm or more. Patients who require medication for more than 12 weeks due to osteoarthritis symptoms. Those who are able to follow the requirements of this clinical trial, such as being able to trace during the clinical trial period and to read and write the VAS questionnaire. Those who weigh more than 40kg", "candidate_expression": "((Adult) AND (Subjects who voluntarily consented, after listening enough explanation for this study and investigational product.) AND (VAS score 40mm or more) AND (age over 50 years) AND (knee pain At least one) AND (medication more than 12 weeks) AND (osteoarthritis symptoms) AND (weigh more than 40kg))"}
{"candidate_id": "LLM07532", "doc_id": "NCT02965027_exc", "case_bucket": "or", "source_criterion": "Participation in other interventional research. History of penetrating head injury History of TBI more severe than mild by DVBIC criteria Diagnosis of a primary or secondary HA disorder other than PTHA Lifetime history of 5 or more migraine or probable migraine headaches pre-dating mTBI HAs of any kind of moderate or severe intensity on an average of more than 2 days per month preceding the concussive trauma Continuous HAs of any kind (i.e., persistent daily HAs with no HA-free period less than 8 hours between attacks) Acute or serious medical illness or unstable chronic medical illness (e.g., unstable angina, myocardial infarction within 6 months, congestive heart failure, clinically significant or concerning cardiac arrhythmias; preexisting hypotension [systolic blood pressure<110] or orthostatic hypotension [systolic drop >20 mm Hg after 2 min standing accompanied by lightheadedness], chronic renal or hepatic failure, acute pancreatitis, Meniere's disease, or diagnosed but untreated sleep apnea). The eligibility of potential participants having acute serious and/or chronic medical illnesses other than those listed will be evaluated on a case-by-case basis by a study physician, PA-C, or ARNP. Use of prazosin or other alpha-1 antagonist (including but not limited to alfuzosin, doxazosin, silodosin, tamsulosin, terazosin) for any purpose in the 2 weeks prior to initial screen (P1) visit and prohibited throughout the study Allergy or previous adverse reaction to prazosin or other alpha-1 antagonist Active psychosis or psychotic disorder, severe depression (as determined per clinician prescriber judgment), severe psychiatric instability or severe situational life crisis (including evidence of being actively suicidal or homicidal). Meets Diagnostic and Statistical Manual of Mental Disorders, 5th Edition (DSM-5) criteria for any Substance Use Disorder except caffeine-related disorders, or tobacco-related disorders. History of delirium within the prior 3 months, epilepsy, stroke, dementia, psychotic disorder, or bipolar disorder Structural brain abnormalities on any prior imaging with associated clinically evident manifestations Current participation in transcranial magnetic stimulation studies Women of childbearing potential must not be pregnant, planning to become pregnant during the study period, or nursing. Participation in a HA support group or other activity such as meditation or yoga intended to mitigate HA or other chronic pain must be stable at least 4 weeks prior to beginning the initial screen (P1) visit and may not be started during the study Failure to record HA data for at least 80% of days during the Screening Period Not suitable for study per clinician judgement. The use of HA rescue or symptom-relieving medications will be allowed during the study. This includes triptans, ergotamines, opioids, simple analgesics (e.g. acetaminophen, aspirin, or non-steroidal anti-inflammatories [NSAIDS], and combination analgesics. Their use will be recorded on the concurrent medication CRF during the Preliminary Screening Period (P1) and throughout the remainder of the study. Randomization of participants will be stratified based on whether their use of HA medications meets ICHD-3 beta criteria for overuse of these medications, as described in section 5.5 below. Opioid Medications: Use of opioids for treatment of HA or non-HA-related pain or for any other purpose is allowed during the study. Any opioid use would ideally be excluded due to potential confounding effects on interpretation of response to treatment. However, in this population, particularly in Veterans with chronic pain or undergoing minor orthopedic or dental procedures, opioid use is common. Use of opioids, including frequency and dose, will be recorded on the concurrent medication CRF. Other Medications: Participants who are taking other medications on a routine basis must be on a stable dose for at least 4 weeks prior to the Preliminary Screening Period (P1), and must intend to continue the medication at the same regimen for the duration of the trial unless lack of efficacy, safety, or tolerability dictates otherwise. The following medications are not excluded: Psychoactive drugs (for example, anticonvulsants, benzodiazepines, antidepressants, sedative/hypnotics), Antihypertensive medications (including beta-blockers, calcium channel blockers, angiotensin converting enzyme [ACE] inhibitors, and angiotensin receptor blockers), The use of magnesium in any dose that is prescribed for the purpose of HA prevention or treatment must be stable for at least 4 weeks. The incidental use of magnesium in multi-vitamins, laxatives, etc. is permissible but must be documented. Hormones (for example, testosterone, estrogen, or progesterone) in any form. The \"as-needed\" (prn) use of psychoactive and other drugs such as antibiotics is not excluded; however, such use must be discussed with a clinician prescriber and documented. The use of butalbital in any form within 4 weeks of beginning the Preliminary Screening Period (P1) through the end of the participant's study involvement is exclusionary. Participants who have been taking trazodone will undergo a 2-week washout period before the Preliminary Screening Period (P1 visit). Combining prazosin and trazodone may increase the risk of priapism. We have decided to begin the washout period before the Preliminary Screening Period in order to remove any confounding variables while on the headache log and actigraphy. Sildenafil (Viagra), tadalafil (Cialis), vardenafil (Levitra), and avanafil (Stendra) will not be permitted during the study drug dose Titration Period, because of increased risk of hypotension in combination with alpha-1 blockers, but will be allowed at half the usual starting dose following the study drug dose Titration Period, per VA prescribing guidelines. Use of supplements containing nitrates and supplements containing stimulants (such as ephedra) are exclusionary in the two weeks prior to initial screen (P1) visit and prohibited throughout the study. Participants who take these supplements will be asked to discontinue them for a minimum of two weeks before the Preliminary Screening Period (P1 visit).. Use of prescribed stimulants (such as amphetamine or dextroamphetamine containing medications) is exclusionary in the 2 weeks prior to the initial screen (P1) visit and prohibited throughout the study. Participants who take these medications will be asked to discontinue them for a minimum of 2 weeks before the Preliminary Screening Period.", "candidate_expression": "((5 or more) AND (<110) AND (>20 mm Hg) AND (Active) AND (Acute) AND (Allergy) AND (Cialis) AND (Continuous) AND (Current) AND (DVBIC criteria) AND (Diagnostic and Statistical Manual of Mental Disorders, 5th Edition (DSM-5) criteria) AND (Failure to record HA data) AND (HA disorder) AND (HA-free period between attacks) AND (HAs) AND (Levitra) AND (Lifetime history) AND (Meets) AND (Meniere's disease) AND (PTHA) AND (Participation in a HA support group) AND (Sildenafil) AND (Stendra) AND (Structural brain abnormalities) AND (Substance Use Disorder) AND (TBI) AND (Viagra) AND (Women) AND (acute pancreatitis) AND (adverse reaction) AND (after 2 min standing) AND (alfuzosin) AND (alpha-1 antagonist) AND (amphetamine) AND (any) AND (avanafil) AND (average of more than 2 days per month) AND (bipolar disorder) AND (butalbital) AND (caffeine-related disorders) AND (cardiac arrhythmias) AND (childbearing potential) AND (chronic medical illness) AND (chronic renal failure) AND (clinically evident) AND (clinically significant) AND (concerning) AND (congestive heart failure) AND (daily) AND (delirium) AND (dementia) AND (dextroamphetamine) AND (doxazosin) AND (during the Screening Period) AND (during the study drug dose Titration Period) AND (during the study period) AND (ephedra) AND (epilepsy) AND (except) AND (for at least 4 weeks prior to the Preliminary Screening Period (P1)) AND (for at least 80% of days) AND (hepatic failure) AND (homicidal) AND (hypotension) AND (imaging) AND (in the 2 weeks prior to initial screen (P1) visit) AND (in the 2 weeks prior to the initial screen (P1) visit) AND (in the two weeks prior to initial screen (P1) visit) AND (initial screen (P1) visit) AND (less than 8 hours) AND (lightheadedness) AND (mTBI) AND (manifestations) AND (medical illness) AND (medications) AND (meditation) AND (migraine) AND (moderate or severe intensity) AND (more severe than mild) AND (myocardial infarction) AND (nitrates) AND (no) AND (not be) AND (nursing) AND (on a routine basis) AND (orthostatic hypotension) AND (other) AND (other than) AND (penetrating head injury) AND (persistent) AND (planning to become) AND (prazosin) AND (pre-dating mTBI) AND (preceding the concussive trauma) AND (preexisting) AND (pregnant) AND (prescribed stimulants) AND (previous) AND (primary) AND (prior) AND (probable) AND (psychiatric instability) AND (psychosis) AND (psychotic disorder) AND (secondary) AND (serious) AND (severe) AND (severe depression) AND (silodosin) AND (situational life crisis) AND (sleep apnea) AND (stable dose) AND (stimulants) AND (stroke) AND (suicidal) AND (systolic blood pressure) AND (systolic drop) AND (tadalafil) AND (tamsulosin) AND (terazosin) AND (tobacco-related disorders) AND (transcranial magnetic stimulation studies) AND (unstable) AND (unstable angina) AND (untreated) AND (vardenafil) AND (within 4 weeks of beginning the Preliminary Screening Period (P1)) AND (within 6 months) AND (within the prior 3 months) AND (yoga))"}
{"candidate_id": "LLM07533", "doc_id": "NCT02570321_exc", "case_bucket": "or", "source_criterion": "Evidence of concomitant infection on exam or gram stain (i.e. herpes, both bacteria and acanthamoeba on gram stain) Impending or frank perforation at recruitment Involvement of sclera at presentation Non-infectious or autoimmune keratitis History of corneal transplantation or recent intraocular surgery No light perception in the affected eye Pinhole visual acuity worse than 20/200 in the unaffected eye Participants who are decisionally and/or cognitively impaired", "candidate_expression": "((Involvement of sclera) AND (No) AND (Non-infectious keratitis) AND (Pinhole visual acuity) AND (autoimmune keratitis) AND (cognitively impaired) AND (concomitant infection) AND (corneal transplantation) AND (intraocular surgery) AND (light perception) AND (perforation) AND (worse than 20/200))"}
{"candidate_id": "LLM07534", "doc_id": "NCT02445339_inc", "case_bucket": "or", "source_criterion": "English or Spanish speaking* Emergency Department patient Aged 18-80 Have had >4 emergency department visits within 12 months for 2 consecutive 12-month periods. Period of time can be extended by up to 6 months if incarcerated or institutionalized for ≥ 6 months. Meet Diagnostic and Statistical Manual version IV (DSM-IV) criteria for alcohol dependence or & DSM-V criteria for alcohol use disorder, severe. Have ≥2 days/week of heavy drinking (>4 drinks/day) Capable of giving informed consent.", "candidate_expression": "((12-month periods) AND (18-80) AND (2 consecutive) AND (>4) AND (Aged) AND (Capable of giving) AND (DSM-V criteria) AND (Diagnostic and Statistical Manual version IV (DSM-IV) criteria) AND (Emergency Department) AND (English speaking) AND (Spanish speaking) AND (alcohol dependence) AND (alcohol use disorder) AND (drinks/day) AND (emergency department visits) AND (extended by up to 6 months) AND (heavy drinking) AND (incarcerated) AND (informed consent) AND (institutionalized) AND (severe) AND (within 12 months) AND (≥2 days/week))"}
{"candidate_id": "LLM07535", "doc_id": "NCT02985710_exc", "case_bucket": "or", "source_criterion": "Subjects with cognitive, psychiatric, or other problems that preclude informed consent. Patients with history of glucose intolerance or diabetes. Patient on chemotherapy People with any open or bleeding wounds at any sensor plate contact surface location People with any type of implantable device People with missing hand(s) and/or leg(s) Pregnant women or women who are uncertain about a possible pregnancy Patients sensitive to chemicals used to induce sweating Patients with heat intolerance Patients with bleeding disorders Patients on current anticoagulant therapy Patients with keloids on the intended biopsy site People with hypersensitivity to local amide-type anesthetics", "candidate_expression": "((anticoagulant therapy current) AND (bleeding disorders) AND (chemotherapy) AND (heat intolerance) AND (hypersensitivity) AND (implantable device) AND (keloids on the intended biopsy site) AND (local amide-type anesthetics) AND (other problems that preclude informed consent) AND (sensitive to chemicals used to induce sweating) AND ((cognitive problems) OR (other problems that preclude informed consent) OR (psychiatric problems)) AND ((bleeding wounds at any sensor plate contact surface location) OR (open wounds at any sensor plate contact surface location)) AND ((missing hand) OR (missing leg)) AND ((Pregnant) OR (possible pregnancy)) AND ((diabetes history) OR (glucose intolerance history)))"}
{"candidate_id": "LLM07536", "doc_id": "NCT02885909_inc", "case_bucket": "or", "source_criterion": "Type 2 diabetic inpatient Fasting glucose >140 mg/dl or random glucose >180 mg/dl", "candidate_expression": "((>140 mg/dl) AND (>180 mg/dl) AND (Type 2 diabetic) AND (inpatient) AND ((Fasting glucose) OR (random glucose)))"}
{"candidate_id": "LLM07537", "doc_id": "NCT02339974_exc", "case_bucket": "or", "source_criterion": "Heart Team assessment of operability (the heart team considers the patient to be a good surgical candidate). Evidence of an acute myocardial infarction = 1 month (30 days) before the intended treatment [defined as: Q wave MI, or non-Q wave MI with total CK elevation of CK-MB = twice normal in the presence of MB elevation and/or troponin level elevation (WHO definition)]. Untreated, severe, left sided valvular heart disease including mitral regurgitation or stenosis, and aortic regurgitation or stenosis. Mean pulmonary artery pressures =40mmHG and PVR >4 woods units as assessed by right heart catheterization. Any therapeutic invasive cardiac procedure resulting in a permanent implant that is performed within 30 days of the index procedure. Examples of permanent implant would include any new heart valve. Implantation of a permanent pacemaker is excluded. Patients with planned concomitant surgical or transcatheter ablation for Atrial Fibrillation. Leukopenia (WBC < 3000 cell/mL), acute anemia (Hgb < 9 g/dL), Thrombocytopenia (Plt < 50,000 cell/mL). Hemodynamic or respiratory instability requiring inotropic support, mechanical ventilation or mechanical heart assistance within 30 days of screening evaluation. Need for emergency surgery for any reason. Left ventricular ejection fraction <40%. Echocardiographic evidence of intracardiac mass, thrombus or vegetation. Active upper GI bleeding within 3 months (90 days) prior to procedure. A known contraindication or hypersensitivity to all anticoagulation regimens, or inability to be anticoagulated for the study procedure. Recent CVA clinically confirmed (by neurologist) or neuroimaging confirmed stroke or transient ischemic attack (TIA) within 6 months (180 days) of the procedure. Estimated life expectancy < 1 year from conditions other than TR. Expectation that patient will not improve despite treatment of tricuspid regurgitation Currently participating in another investigational cardiac device study or any other clinical trial, including drugs or biologics. Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials. Active bacterial endocarditis within 6 months (180 days) of procedure. Patients with signs or symptoms of SVC syndrome, or hepatic cirrhosis not felt due to passive congestion from TR.", "candidate_expression": "((Atrial Fibrillation) AND (CVA clinically confirmed (by neurologist)) AND (Echocardiographic) AND (Estimated life expectancy < 1 year) AND (Heart Team assessment of operability) AND (Hemodynamic instability) AND (Hgb < 9 g/dL) AND (Left ventricular ejection fraction <40%) AND (Leukopenia) AND (Mean pulmonary artery pressures =40mmHG) AND (PVR >4 woods units) AND (Plt < 50,000 cell/mL) AND (SVC syndrome) AND (Thrombocytopenia) AND (WBC < 3000 cell/mL) AND (acute anemia) AND (acute myocardial infarction = 1 month (30 days) before the intended treatment) AND (anticoagulated) AND (anticoagulation regimens) AND (aortic regurgitation) AND (aortic stenosis) AND (bacterial endocarditis Active within 6 months (180 days) of procedure) AND (cardiac procedure therapeutic invasive within 30 days of the index procedure) AND (contraindication) AND (emergency surgery Need for) AND (heart team considers the patient to be a good surgical candidate) AND (heart valve) AND (hepatic cirrhosis) AND (hypersensitivity) AND (inability for the study procedure) AND (inotropic support) AND (intracardiac mass) AND (intracardiac thrombus) AND (intracardiac vegetation) AND (mechanical heart assistance) AND (mechanical ventilation) AND (mitral regurgitation) AND (mitral stenosis) AND (neuroimaging confirmed) AND (passive congestion from TR) AND (permanent implant) AND (respiratory instability) AND (right heart catheterization) AND (stroke) AND (surgical ablation) AND (transcatheter ablation) AND (transient ischemic attack (TIA) within 6 months (180 days) of the procedure) AND (upper GI bleeding Active within 3 months (90 days) prior to procedure) AND (valvular heart disease Untreated severe left sided) AND NOT (permanent pacemaker))"}
{"candidate_id": "LLM07538", "doc_id": "NCT02414399_inc", "case_bucket": "other", "source_criterion": "Age 1-59 months, Plan to remain in study area greater than 6 months Discharged from hospital following non-trauma related admission", "candidate_expression": "((1-59 months) AND (Age) AND (Discharged from hospital) AND (Plan) AND (greater than 6 months) AND (hospital) AND (non-trauma related admission) AND (remain in study area))"}
{"candidate_id": "LLM07539", "doc_id": "NCT02231892_inc", "case_bucket": "or", "source_criterion": "Subjects must: 1. Be able to give valid informed consent 2. Be 18 55 years of age. 1. Justification: Many neural processes change with age, and these changes could introduce unwanted variability in both behavioral and MRI signals. In addition, the risk of difficult-to-detect medical abnormalities such as silent cerebral infarcts increases with age. 2. Screening tool: History. Government-issued forms of identification (e.g. driver s license, birth certificate) will be required when participant appears to be out of age range. 3. Be in good health. 1. Justification: Many illnesses may alter neural functioning as well as fMRI signals. 2. Screening tools: Medical Assessment, Medical History and Physical Examination. Medical assessments include: Vital Signs, EKG, oral HIV test, height/weight measurements, urinalysis and blood sample. Tests on the blood sample include CBC, complete metabolic profile, TSH, ESR, STS and HIV (if needed to confirm a positive salivary test for HIV). The following individual laboratory results will independently disqualify individuals: Cholesterol >250 mg/dl, Hemoglobin < 10.5 g/dl, WBC < 2400/microl, LFTs > 3Xnormal, HCG positive, Casual serum glucose > 200 mg/dl, Urine protein > 1+. The MAI will retain discretion to exclude at less extreme values, depending on the clinical presentation. (Serum glucose over 140 mg/dl will be followed up with a fasting serum glucose assessment. Those with fasting glucose below 100 mg/dl may be considered for the protocol. Others will be rejected and referred for work-up.) MAI will make the final judgment on any questionable lab results. 4. Right-handed. 1. Justification: Using right-handed individuals will reduce variability in BOLD MRI data. 2. Screening tool: Edinburgh Handedness Inventory. 5. Estimated IQ greater than or equal to 85 1. Justification: Subjects must be able to perform a cognitively challenging task to a high standard. 2. Screening tool: Wechsler Abbreviated Scale of Intelligence.", "candidate_expression": "((Be able to give valid informed consent) AND (CBC) AND (Cholesterol >250 mg/dl) AND (EKG) AND (ESR) AND (Edinburgh Handedness Inventory) AND (Estimated IQ greater than or equal to 85) AND (HCG positive) AND (HIV) AND (Hemoglobin < 10.5 g/dl) AND (History) AND (LFTs > 3Xnormal) AND (Medical Assessment) AND (Medical History) AND (Physical Examination) AND (Right-handed) AND (STS) AND (Serum glucose over 140 mg/dl) AND (TSH) AND (The MAI will retain discretion to exclude at less extreme values, depending on the clinical presentation.) AND (Urine protein > 1+) AND (Vital Signs) AND (WBC < 2400/microl) AND (Wechsler Abbreviated Scale of Intelligence) AND (age 18 55 years) AND (blood sample) AND (complete metabolic profile) AND (fasting serum glucose assessment) AND (good health) AND (height measurement) AND (oral HIV test) AND (salivary test for HIV positive) AND (serum glucose > 200 mg/dl) AND (urinalysis) AND (weight measurement))"}
{"candidate_id": "LLM07540", "doc_id": "NCT01912651_inc", "case_bucket": "or", "source_criterion": "all adult patients with a nasal or facial skin/soft tissue defect requiring reconstruction limited to or including a full-thickness skin graft", "candidate_expression": "((full-thickness skin graft) AND (reconstruction requiring) AND ((facial skin/soft tissue defect) OR (nasal skin/soft tissue defect)))"}
{"candidate_id": "LLM07541", "doc_id": "NCT03506009_inc", "case_bucket": "other", "source_criterion": "18-80 years old; Diagnosis of posterior circulation ischemic stroke; Time from onset to treatment =6 hours; NIHSS: 4-25; Signed informed consent by patient self or legally authorized representatives.", "candidate_expression": "((NIHSS 4-25) AND (Signed informed consent by patient self or legally authorized representatives.) AND (Time from onset to treatment =6 hours) AND (old 18-80 years old) AND (posterior circulation ischemic stroke))"}
{"candidate_id": "LLM07542", "doc_id": "NCT02831166_inc", "case_bucket": "or", "source_criterion": "ST-segment elevation acute myocardial infarction patients during the first 12 hours of sympton onset; Intention to perform primary percutaneous coronary intervention; Signed informed consent; Patient eligible for transradial and transfemoral primary percutaneous coronary intervention, being pre-requisites: (a) familiarity of the operator with the radial and femoral techniques using vascular closure devices, (b) agreement of the operator to use the access route determined by the randomization process.", "candidate_expression": "((acute myocardial infarction ST-segment elevation during the first 12 hours of sympton onset) AND (percutaneous coronary intervention Intention to perform primary transradial) AND (percutaneous coronary intervention eligible for primary transfemoral))"}
{"candidate_id": "LLM07543", "doc_id": "NCT02958566_inc", "case_bucket": "or", "source_criterion": "Males or females above the age of 18 Patients undergoing laparoscopic or robotic colorectal resections", "candidate_expression": "((Males) AND (above the age of 18) AND (age) AND (colorectal resections) AND (females) AND (laparoscopic) AND (robotic))"}
{"candidate_id": "LLM07544", "doc_id": "NCT03194074_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for laser laryngeal surgery under general anesthesia with either Propofol or desflurane based technique.", "candidate_expression": "((Propofol) AND (desflurane) AND (general anesthesia) AND (laser laryngeal surgery scheduled))"}
{"candidate_id": "LLM07545", "doc_id": "NCT00279552_exc", "case_bucket": "or", "source_criterion": "Patients who were pregnant, nursing or not able to give written informed consent were excluded.", "candidate_expression": "((nursing able to give written informed consent) OR (pregnant))"}
{"candidate_id": "LLM07546", "doc_id": "NCT03339284_inc", "case_bucket": "other", "source_criterion": "patients with renal cancer coming to the laparoscopic radical nephrectomy", "candidate_expression": "((laparoscopic) AND (radical nephrectomy) AND (renal cancer))"}
{"candidate_id": "LLM07547", "doc_id": "NCT03619707_exc", "case_bucket": "or", "source_criterion": "Preexisting untreated medical condition (thyroid disease, diabetes mellitus, hypertension, pulmonary conditions, cardiac condition…) History of three or more consecutively failed In Vitro Fertilization (IVF) cycles after embryo transfer History of three or more miscarriages Previous allergy reactions to progesterone products", "candidate_expression": "((IVF) AND (In Vitro Fertilization three or more consecutively failed after embryo transfer) AND (allergy) AND (cardiac condition) AND (diabetes mellitus) AND (embryo transfer) AND (hypertension) AND (medical condition Preexisting untreated) AND (miscarriages three or more) AND (progesterone products) AND (pulmonary conditions) AND (thyroid disease))"}
{"candidate_id": "LLM07548", "doc_id": "NCT02443623_inc", "case_bucket": "other", "source_criterion": "Signed written informed consent. Age 18 to 65. Normal and healthy (immune competent) as determined by medical history, physical exam, vital signs and clinical laboratory tests during the screening period. If all lab results for quantitative IgA immunoglobulin level are lower than 15% below normal range, the subject may not proceed further in the screening process. Subject must meet all required subject suitability criteria that pertain to normal source plasma donors. Negative HIV serology during screening period. Subject must have been previously immunized for smallpox, at =3 years prior to commencement of screening assessments, and vaccination history must be confirmed by oral or written history and the presence of a visible pathognomonic smallpox vaccination scar. Female subjects of childbearing potential must agree to use highly effective birth control methods.", "candidate_expression": "((18 to 65) AND (3 years prior to commencement of screening assessments) AND (Age) AND (Female) AND (HIV serology) AND (Negative) AND (Normal) AND (Signed written informed consent) AND (birth control methods) AND (childbearing potential) AND (clinical laboratory tests) AND (commencement of screening assessments) AND (during screening period) AND (during the screening period) AND (healthy) AND (immunized) AND (lower than 15% below normal range) AND (medical history) AND (physical exam) AND (quantitative IgA immunoglobulin level) AND (screening period) AND (smallpox) AND (vital signs))"}
{"candidate_id": "LLM07549", "doc_id": "NCT03619707_inc", "case_bucket": "or", "source_criterion": "Normal uterine cavity Normal Hormonal investigation: TSH,PRL,FBS Frozen embryo transfer cycles: at least 2 embryos Primary or secondary infertility: tubal occlusion, male factor, unexplained, endometriosis, ovarian factors… Body mass index (BMI) =18 to =30 kg/m2", "candidate_expression": "((BMI) AND (Body mass index =18 to =30 kg/m2) AND (FBS) AND (Frozen embryo transfer cycles) AND (Hormonal investigation Normal) AND (PRL) AND (TSH) AND (embryos at least 2) AND (uterine cavity Normal) AND ((Primary infertility) OR (secondary infertility)) AND ((endometriosis) OR (male factor) OR (ovarian factors) OR (tubal occlusion) OR (unexplained factors)))"}
{"candidate_id": "LLM07550", "doc_id": "NCT03062358_inc", "case_bucket": "or", "source_criterion": "Has a HCC diagnosis confirmed by radiology, histology, or cytology (fibrolamellar, and mixed hepatocellular/cholangiocarcinoma subtypes are not eligible) Has Barcelona Clinic Liver Cancer (BCLC) Stage C disease or BCLC Stage B disease not amenable to locoregional therapy or refractory to locoregional therapy and not amenable to a curative treatment approach Has a Child-Pugh A liver score within 7 days prior to first dose of study medication Has a life expectancy of >3 months Has at least one measurable lesion based on RECIST version 1.1 as determined by investigator Has Eastern Cooperative Oncology Group (ECOG) performance status of 0 or 1 performed within 7 days prior to receiving the first dose of study medication Has documented objective radiographic progression during or after treatment with sorafenib or oxaliplatin-based chemotherapy, or else intolerance to sorafenib or oxaliplatin-based chemotherapy Female participants of childbearing potential must have a negative urine or serum pregnancy test within 72 hours prior to receiving the first dose of study therapy Female and male participants of reproductive potential must agree to use adequate contraception starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication", "candidate_expression": "((BCLC Stage B) AND (Barcelona Clinic Liver Cancer (BCLC) Stage C) AND (Child-Pugh liver score A within 7 days prior) AND (Eastern Cooperative Oncology Group (ECOG) performance status 0 or 1 within 7 days prior) AND (Female) AND (Female and male participants of reproductive potential must agree to use adequate contraception starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication) AND (Female participants of childbearing potential must have a negative urine or serum pregnancy test within 72 hours prior to receiving the first dose of study therapy) AND (HCC) AND (RECIST version 1.1 measurable) AND (adequate contraception) AND (chemotherapy sorafenib or oxaliplatin-based) AND (childbearing potential) AND (lesion at least one) AND (life expectancy >3 months) AND (not) AND (oxaliplatin) AND (reproductive potential) AND (sorafenib) AND NOT (subtype fibrolamellar) AND NOT (mixed hepatocellular/cholangiocarcinoma subtype) AND ((disease) OR (disease amenable to a curative treatment approach)) AND ((amenable to locoregional therapy) OR (refractory to locoregional therapy)) AND ((cytology) OR (histology) OR (radiology)) AND ((intolerance) OR (radiographic objective progression during or after)) AND ((pregnancy test urine) OR (serum pregnancy test)) AND ((Female) OR (male)))"}
```
