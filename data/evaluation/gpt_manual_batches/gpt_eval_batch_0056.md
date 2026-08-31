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
{"candidate_id": "LLM01376", "doc_id": "NCT02062489_exc", "case_bucket": "or", "source_criterion": "The patients have other cancers at the same time or have the history of other cancers except controlled skin basal cell carcinoma or skin squamous cell carcinoma or carcinoma in situ of cervix uterus; The patients have active infections that were not suitable for chemotherapy; The patients have severe non-cancerous diseases. The patients have history of neoadjuvant hormone therapy. The patients have bilateral breast cancers or DCIS or metastatic breast cancers. The patients are undergoing current administration of anti-cancer therapies, or are attending other clinical trials. The patients are pregnant or lactational, or they refuse to practice contraception during the whole trial. The patients are in some special conditions that they can't understand the written informed consent, such as they are demented or hawkish. The patients have allergic history or contraindication of tamoxifen.", "candidate_expression": "((The patients are in some special conditions that they can't understand the written informed consent, such as they are demented or hawkish.) AND (infections active suitable for chemotherapy) AND (neoadjuvant hormone therapy) AND (non-cancerous diseases severe) AND (tamoxifen) AND ((DCIS) OR (bilateral breast cancers) OR (metastatic breast cancers)) AND ((anti-cancer therapies) OR (attending other clinical trials)) AND ((lactational) OR (pregnant) OR NOT (contraception during the whole trial)) AND ((allergic) OR (contraindication)) AND ((other cancers) OR (other cancers at the same time)) AND ((carcinoma in situ of cervix uterus) OR (controlled skin basal cell carcinoma) OR (skin squamous cell carcinoma)))"}
{"candidate_id": "LLM01377", "doc_id": "NCT02965027_exc", "case_bucket": "or", "source_criterion": "Participation in other interventional research. History of penetrating head injury History of TBI more severe than mild by DVBIC criteria Diagnosis of a primary or secondary HA disorder other than PTHA Lifetime history of 5 or more migraine or probable migraine headaches pre-dating mTBI HAs of any kind of moderate or severe intensity on an average of more than 2 days per month preceding the concussive trauma Continuous HAs of any kind (i.e., persistent daily HAs with no HA-free period less than 8 hours between attacks) Acute or serious medical illness or unstable chronic medical illness (e.g., unstable angina, myocardial infarction within 6 months, congestive heart failure, clinically significant or concerning cardiac arrhythmias; preexisting hypotension [systolic blood pressure<110] or orthostatic hypotension [systolic drop >20 mm Hg after 2 min standing accompanied by lightheadedness], chronic renal or hepatic failure, acute pancreatitis, Meniere's disease, or diagnosed but untreated sleep apnea). The eligibility of potential participants having acute serious and/or chronic medical illnesses other than those listed will be evaluated on a case-by-case basis by a study physician, PA-C, or ARNP. Use of prazosin or other alpha-1 antagonist (including but not limited to alfuzosin, doxazosin, silodosin, tamsulosin, terazosin) for any purpose in the 2 weeks prior to initial screen (P1) visit and prohibited throughout the study Allergy or previous adverse reaction to prazosin or other alpha-1 antagonist Active psychosis or psychotic disorder, severe depression (as determined per clinician prescriber judgment), severe psychiatric instability or severe situational life crisis (including evidence of being actively suicidal or homicidal). Meets Diagnostic and Statistical Manual of Mental Disorders, 5th Edition (DSM-5) criteria for any Substance Use Disorder except caffeine-related disorders, or tobacco-related disorders. History of delirium within the prior 3 months, epilepsy, stroke, dementia, psychotic disorder, or bipolar disorder Structural brain abnormalities on any prior imaging with associated clinically evident manifestations Current participation in transcranial magnetic stimulation studies Women of childbearing potential must not be pregnant, planning to become pregnant during the study period, or nursing. Participation in a HA support group or other activity such as meditation or yoga intended to mitigate HA or other chronic pain must be stable at least 4 weeks prior to beginning the initial screen (P1) visit and may not be started during the study Failure to record HA data for at least 80% of days during the Screening Period Not suitable for study per clinician judgement. The use of HA rescue or symptom-relieving medications will be allowed during the study. This includes triptans, ergotamines, opioids, simple analgesics (e.g. acetaminophen, aspirin, or non-steroidal anti-inflammatories [NSAIDS], and combination analgesics. Their use will be recorded on the concurrent medication CRF during the Preliminary Screening Period (P1) and throughout the remainder of the study. Randomization of participants will be stratified based on whether their use of HA medications meets ICHD-3 beta criteria for overuse of these medications, as described in section 5.5 below. Opioid Medications: Use of opioids for treatment of HA or non-HA-related pain or for any other purpose is allowed during the study. Any opioid use would ideally be excluded due to potential confounding effects on interpretation of response to treatment. However, in this population, particularly in Veterans with chronic pain or undergoing minor orthopedic or dental procedures, opioid use is common. Use of opioids, including frequency and dose, will be recorded on the concurrent medication CRF. Other Medications: Participants who are taking other medications on a routine basis must be on a stable dose for at least 4 weeks prior to the Preliminary Screening Period (P1), and must intend to continue the medication at the same regimen for the duration of the trial unless lack of efficacy, safety, or tolerability dictates otherwise. The following medications are not excluded: Psychoactive drugs (for example, anticonvulsants, benzodiazepines, antidepressants, sedative/hypnotics), Antihypertensive medications (including beta-blockers, calcium channel blockers, angiotensin converting enzyme [ACE] inhibitors, and angiotensin receptor blockers), The use of magnesium in any dose that is prescribed for the purpose of HA prevention or treatment must be stable for at least 4 weeks. The incidental use of magnesium in multi-vitamins, laxatives, etc. is permissible but must be documented. Hormones (for example, testosterone, estrogen, or progesterone) in any form. The \"as-needed\" (prn) use of psychoactive and other drugs such as antibiotics is not excluded; however, such use must be discussed with a clinician prescriber and documented. The use of butalbital in any form within 4 weeks of beginning the Preliminary Screening Period (P1) through the end of the participant's study involvement is exclusionary. Participants who have been taking trazodone will undergo a 2-week washout period before the Preliminary Screening Period (P1 visit). Combining prazosin and trazodone may increase the risk of priapism. We have decided to begin the washout period before the Preliminary Screening Period in order to remove any confounding variables while on the headache log and actigraphy. Sildenafil (Viagra), tadalafil (Cialis), vardenafil (Levitra), and avanafil (Stendra) will not be permitted during the study drug dose Titration Period, because of increased risk of hypotension in combination with alpha-1 blockers, but will be allowed at half the usual starting dose following the study drug dose Titration Period, per VA prescribing guidelines. Use of supplements containing nitrates and supplements containing stimulants (such as ephedra) are exclusionary in the two weeks prior to initial screen (P1) visit and prohibited throughout the study. Participants who take these supplements will be asked to discontinue them for a minimum of two weeks before the Preliminary Screening Period (P1 visit).. Use of prescribed stimulants (such as amphetamine or dextroamphetamine containing medications) is exclusionary in the 2 weeks prior to the initial screen (P1) visit and prohibited throughout the study. Participants who take these medications will be asked to discontinue them for a minimum of 2 weeks before the Preliminary Screening Period.", "candidate_expression": "((Cialis) AND (DVBIC criteria more severe than mild) AND (Diagnostic and Statistical Manual of Mental Disorders, 5th Edition (DSM-5) criteria Meets) AND (Failure to record HA data for at least 80% of days during the Screening Period) AND (HA disorder) AND (HAs Continuous) AND (HAs moderate or severe intensity average of more than 2 days per month preceding the concussive trauma) AND (HAs persistent daily) AND (Levitra) AND (Participation in a HA support group) AND (Stendra) AND (Structural brain abnormalities) AND (Substance Use Disorder) AND (TBI) AND (Viagra) AND (Women) AND (butalbital within 4 weeks of beginning the Preliminary Screening Period (P1)) AND (childbearing potential) AND (ephedra) AND (imaging any prior) AND (lightheadedness) AND (mTBI) AND (manifestations clinically evident) AND (medications other on a routine basis) AND (meditation) AND (penetrating head injury) AND (prescribed stimulants in the 2 weeks prior to the initial screen (P1) visit) AND (systolic blood pressure <110) AND (systolic drop >20 mm Hg after 2 min standing) AND (transcranial magnetic stimulation studies Current) AND (yoga) AND NOT (HA-free period between attacks less than 8 hours) AND NOT (PTHA) AND ((bipolar disorder) OR (delirium within the prior 3 months) OR (dementia) OR (epilepsy) OR (psychotic disorder) OR (stroke)) AND ((nursing during the study period) OR (pregnant) OR (pregnant planning to become)) AND ((migraine) OR (migraine probable)) AND ((Sildenafil) OR (avanafil) OR (tadalafil) OR (vardenafil)) AND ((nitrates) OR (stimulants)) AND ((amphetamine) OR (dextroamphetamine)) AND ((Acute) OR (serious)) AND ((chronic medical illness unstable) OR (medical illness)) AND ((clinically significant) OR (concerning)) AND ((Meniere's disease) OR (acute pancreatitis) OR (cardiac arrhythmias) OR (chronic renal failure) OR (congestive heart failure) OR (hepatic failure) OR (hypotension preexisting) OR (myocardial infarction within 6 months) OR (orthostatic hypotension) OR (sleep apnea untreated) OR (unstable angina)) AND ((primary) OR (secondary)) AND ((alpha-1 antagonist other) OR (prazosin)) AND ((alfuzosin) OR (doxazosin) OR (silodosin) OR (tamsulosin) OR (terazosin)) AND ((Allergy) OR (adverse reaction previous)) AND ((psychiatric instability severe) OR (psychosis Active) OR (psychotic disorder) OR (severe depression) OR (situational life crisis severe)) AND ((homicidal) OR (suicidal)) AND ((caffeine-related disorders) OR (tobacco-related disorders)))"}
{"candidate_id": "LLM01378", "doc_id": "NCT02782702_inc", "case_bucket": "or", "source_criterion": "Confirmed diagnosis (clinical and histological features) of Hailey Hailey or Darier diseases. Moderate to very severe lesions located in large folds Patient aged 18 ans or more Patient with health coverage Patient who have signed the consent form Patient proficient into filling out the questionnaires.", "candidate_expression": "((18 ans or more) AND (Patient proficient into filling out the questionnaires.) AND (Patient who have signed the consent form) AND (aged) AND (health coverage) AND (histological) AND (lesions) AND (very severe) AND ((Darier disease) OR (Hailey Hailey disease)))"}
{"candidate_id": "LLM01379", "doc_id": "NCT02455921_inc", "case_bucket": "other", "source_criterion": "Children undergoing ENT surgery under general anaesthesia.", "candidate_expression": "((Children) AND (ENT surgery) AND (general anaesthesia) AND (undergoing))"}
{"candidate_id": "LLM01380", "doc_id": "NCT01912677_exc", "case_bucket": "or", "source_criterion": "Indication for emergent cesarean or known fetal anomaly Anti-hypertensive therapy received in the past 12 hours History of eclampsia or other adverse CNS complication (e.g., stroke or PRES) in this pregnancy Actively wheezing at time of enrollment or history of asthma complications Known coronary artery disease or type I DM with microvascular complications or signs of heart failure or clinical dissection of the aorta", "candidate_expression": "((Anti-hypertensive therapy past 12 hours) AND (CNS complication) AND (Indication) AND (PRES) AND (asthma complications) AND (coronary artery disease) AND (dissection of the aorta) AND (eclampsia) AND (emergent cesarean) AND (fetal anomaly) AND (heart failure) AND (microvascular complications) AND (stroke) AND (type I DM) AND (wheezing at time of enrollment enrollment))"}
{"candidate_id": "LLM01381", "doc_id": "NCT02425774_exc", "case_bucket": "or", "source_criterion": "adjuvant radiotherapy evident intra-abdominal inflammation (diagnosed by imaging and/or laboratory results, including an abscess or cholecystitis) chronic pancreatitis pancreatic polypeptide producing endocrine tumor American Society of Anesthesiologists physical-health status classification (ASA-PS)>3 Poorly regulated diabetes (>200 mg/dl (=11 mmol/l))", "candidate_expression": "((American Society of Anesthesiologists physical-health status classification (ASA-PS) >3) AND (abscess) AND (adjuvant radiotherapy) AND (cholecystitis) AND (chronic pancreatitis) AND (diabetes Poorly regulated >200 mg/dl (=11 mmol/l)) AND (imaging) AND (intra-abdominal inflammation) AND (laboratory) AND (pancreatic polypeptide producing endocrine tumor) AND (pancreatitis chronic))"}
{"candidate_id": "LLM01382", "doc_id": "NCT01701219_exc", "case_bucket": "or", "source_criterion": "1. For subjects in Cohort A: previous therapy for more than 48 hours with any parenteral antibiotic with activity against S. aureus within 72 hours of positive blood culture results. 2. For subjects in Cohort B: previous therapy for more than 48 hours with any parenteral antibiotic with activity against MRSA, except vancomycin and/or daptomycin, within 72 hours of positive blood culture results confirming persistence. 3. Previous episode of S. aureus bacteremia within 3 months. 4. Known left-sided endocarditis or prosthetic heart valve. 5. Osteomyelitis or prosthetic joint infection except new onset nonhardware-associated vertebral osteomyelitis. 6. History of any hypersensitivity or allergic reaction to any β-lactam antibacterial agent. 7. Evidence of significant hepatic, hematologic, or immunologic impairment. 8. Pregnant or nursing females.", "candidate_expression": "((Cohort A) AND (Cohort B) AND (MRSA) AND (S. aureus) AND (S. aureus S. aureus) AND (S. aureus bacteremia within 3 months left-sided) AND (blood culture positive results) AND (females) AND (parenteral antibiotic with activity against MRSA with activity against MRSA) AND (parenteral antibiotic with activity against S. aureus with activity against S. aureus within 72 hours of positive blood culture results) AND (therapy previous for more than 48 hours parenteral) AND (β-lactam antibacterial agent) AND NOT (vancomycin) AND NOT (daptomycin positive blood culture results) AND NOT (vertebral osteomyelitis new onset nonhardware-associated) AND ((left-sided endocarditis) OR (prosthetic heart valve)) AND ((Osteomyelitis) OR (prosthetic joint infection)) AND ((allergic reaction) OR (hypersensitivity)) AND ((hematologic impairment) OR (hepatic impairment) OR (immunologic impairment)) AND ((Pregnant) OR (nursing)))"}
{"candidate_id": "LLM01383", "doc_id": "NCT02707809_inc", "case_bucket": "other", "source_criterion": "kidney transplant recipient", "candidate_expression": "(kidney transplant)"}
{"candidate_id": "LLM01384", "doc_id": "NCT01943812_exc", "case_bucket": "or", "source_criterion": "endometrial thickness < 7 mm or no triple layer endometrium and/or functional follicles Uterine abnormality Chronic medical disease oocyte donation cycles", "candidate_expression": "((< 7 mm) AND (Chronic medical disease) AND (Uterine abnormality) AND (endometrial thickness) AND (functional follicles) AND (no) AND (oocyte donation cycles) AND (triple layer endometrium))"}
{"candidate_id": "LLM01385", "doc_id": "NCT03495557_exc", "case_bucket": "other", "source_criterion": "Conversion to laparotomy Emergent re intervention Immunosuppression Umbilical hernia", "candidate_expression": "((Conversion to) AND (Immunosuppression) AND (Umbilical hernia) AND (laparotomy) AND (re intervention Emergent))"}
{"candidate_id": "LLM01386", "doc_id": "NCT02348918_inc", "case_bucket": "or", "source_criterion": "Male or female, 18 years of age or older. Study eye with clinically significant diabetic macular edema (DME) with central subfield thickness ≥ 350µm on spectral domain OCT Best corrected visual acuity (BCVA) of 20/50 to 20/320 ETDRS equivalent (65 letters to 23 letters) in the study eye, with BCVA decrement primarily attributable to DME. Treatment naïve, i.e., no previous anti-VEGF treatment in the study eye or no anti-VEGF treatment in the 45 days prior to study enrollment. In the investigator's opinion, the subject still has significant intraretinal fluid with room for improvement in both macular edema and BCVA. Intra-Ocular Pressure (IOP) is under control (i.e., IOP ≤ 25 mm in the study eye) and study eye is not receiving any IOP lowering drops. Willing and able to return for all study visits. Able to meet the extensive post-op evaluation regimen. Understands and signs the informed consent form.", "candidate_expression": "((Able to meet the extensive post-op evaluation regimen.) AND (BCVA) AND (Best corrected visual acuity (BCVA) 20/50 to 20/320 ETDRS equivalent in the study eye 65 letters to 23 letters) AND (IOP ≤ 25 mm in the study eye) AND (Intra-Ocular Pressure (IOP) under control) AND (Male) AND (Treatment naïve) AND (Understands and signs the informed consent form.) AND (Willing and able to return for all study visits.) AND (age 18 years or older) AND (central subfield thickness ≥ 350µm) AND (diabetic macular edema (DME) clinically significant) AND (female) AND (intraretinal fluid significant with room for improvement) AND (macular edema) AND (spectral domain OCT) AND NOT (anti-VEGF treatment previous in the study eye) AND NOT (anti-VEGF treatment in the 45 days prior to study enrollment) AND NOT (IOP lowering drops study eye))"}
{"candidate_id": "LLM01387", "doc_id": "NCT01978028_inc", "case_bucket": "or", "source_criterion": "Patients with chronic heart failure of New York Heart Association Class II or III, a left ventricular ejection fraction of = 40% for patients in NYHA class II or = 45% for patients in NYHA class III, a hemoglobin level at the screening visit between 9.5-13.5 g/dl, and iron deficiency, which is defined as serum ferritin level < 100µg/l or between 100 and 299 µg/l, when transferring saturation is < 20%. Age =18 years Obtained informed consent Stable pharmacological therapy during the last 4 weeks (with the exception of diuretics)", "candidate_expression": "((< 100µg/l) AND (< 20%) AND (= 40%) AND (= 45%) AND (=18 years) AND (Age) AND (Class II or III) AND (NYHA) AND (New York Heart Association) AND (Obtained informed consent) AND (Stable) AND (at the screening visit) AND (between 100 and 299 µg/l) AND (between 9.5-13.5 g/dl) AND (chronic heart failure) AND (class II) AND (class III) AND (diuretics) AND (during the last 4 weeks) AND (hemoglobin level) AND (iron deficiency) AND (last 4 weeks) AND (left ventricular ejection fraction) AND (pharmacological therapy) AND (serum ferritin level) AND (the screening visit) AND (transferring saturation) AND (with the exception of))"}
{"candidate_id": "LLM01388", "doc_id": "NCT03159507_inc", "case_bucket": "other", "source_criterion": "Participant aged 19 or over Available for the entire duration of the study and willing to participate on the basis of the information provided in the FIU duly read and signed.", "candidate_expression": "((Available for the entire duration of the study and willing to participate on the basis of the information provided in the FIU duly read and signed.) AND (aged 19 or over))"}
{"candidate_id": "LLM01389", "doc_id": "NCT02117986_inc", "case_bucket": "other", "source_criterion": "patient hospitalized in critical care units patient infected by multi drug resistant Gram negative bacteria susceptibly only to colistin source of infection: blood, respiratory, intra abdominal or urinary", "candidate_expression": "((Gram negative bacteria multi drug resistant susceptibly) AND (colistin only) AND (critical care units) AND (hospitalized))"}
{"candidate_id": "LLM01390", "doc_id": "NCT02851888_exc", "case_bucket": "or", "source_criterion": "Current or planned pregnancy History of neuropathic pain, chronic pain syndrome, or preoperative use of narcotic or neuropathic pain medicine Radiographic signs of osteoarthritis (> Tonis grade 1) Inability to attend follow up visits Documented allergy to local anesthetic", "candidate_expression": "((> 1) AND (History) AND (Inability) AND (Radiographic) AND (Radiographic signs) AND (Tonis grade) AND (allergy) AND (attend follow up visits) AND (local anesthetic) AND (osteoarthritis) AND (pregnancy) AND (preoperative) AND ((Current) OR (planned)) AND ((chronic pain syndrome) OR (neuropathic pain)) AND ((narcotic medicine) OR (neuropathic pain medicine)))"}
{"candidate_id": "LLM01391", "doc_id": "NCT01684501_exc", "case_bucket": "or", "source_criterion": "score level D on the SIGAM mobility grade have experienced 1 or more falls in the last month before the study have a residual limb length which does not allow for seven inches clearance of bracket attachment for the PowerFoot the residual limb must be stable in volume (no change in socket or socket padding in last 6 months) and without pain that limits function the sound-side (contralateral) lower extremity must be free of impediments that affect gait, range of motion, or limb muscle activity Any diagnosed cardiovascular, pulmonary, neurological, and/ or orthopedic conditions that would interfere with subject participation", "candidate_expression": "((SIGAM mobility grade level D) AND (cardiovascular conditions) AND (does not) AND (falls 1 or more in the last month before the study) AND (impediments that affect gait) AND (impediments that affect limb muscle activity) AND (impediments that affect range of motion) AND (interfere with subject participation) AND (neurological conditions) AND (orthopedic conditions) AND (pulmonary conditions) AND (residual limb length does not allow for seven inches clearance of bracket attachment))"}
{"candidate_id": "LLM01392", "doc_id": "NCT01401335_inc", "case_bucket": "other", "source_criterion": "100 orphans/vulnerable youth aged 15 to 25 will be recruited through their participation at the day care center, on a voluntary basis.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01393", "doc_id": "NCT00994786_inc", "case_bucket": "scope", "source_criterion": "Must be an outpatient with a primary DSM-IV Obsessive-Compulsive Disorder. Patients must have a score of greater than 20 on the Yale-Brown Obsessive Compulsive Scale (Y-BOCS; Goodman et al., 1989b). Diagnosis of comorbid DSM-IV major depressive episode will be allowed in the study provided that the diagnosis is secondary to OCD, they have a baseline Montgomery Depression Rating Scale (MADRS) score of less than or equal to 19, and the onset of OCD predates the onset of the current episode of depression by five or more years. The ability to comprehend and comply with protocol requirements. Written consent must be provided prior to study entry. All women of childbearing potential (WOCBP) must be practicing a medically acceptable method of birth control All female subjects of childbearing potential (WOCBP), including those who are practicing a medically acceptable method of birth control, must have a negative serum pregnancy test within 72 hours prior to the start of study medication.", "candidate_expression": "((All female subjects of childbearing potential (WOCBP), including those who are practicing a medically acceptable method of birth control, must have a negative serum pregnancy test within 72 hours prior to the start of study medication) AND (MADRS) AND (Montgomery Depression Rating Scale baseline score of less than or equal to 19) AND (OCD) AND (Obsessive-Compulsive Disorder) AND (The ability to comprehend and comply with protocol requirements) AND (WOCBP) AND (Written consent must be provided prior to study entry.) AND (Y-BOCS comorbid) AND (Yale-Brown Obsessive Compulsive Scale score of greater than 20) AND (birth control medically acceptable) AND (childbearing potential) AND (major depressive episode DSM-IV) AND (onset of OCD predates the onset of the current episode of depression by five or more years) AND (outpatient primary DSM-IV) AND (women))"}
{"candidate_id": "LLM01394", "doc_id": "NCT03335904_inc", "case_bucket": "or", "source_criterion": "normotensive forced expiratory volume in 1s : forced vital capacity ratio > 0.75 no medical history of cardiovascular and respiratory disease not taking medications other than oral contraceptives free from sleep apnea body mass index less than 30 kg/m2", "candidate_expression": "((> 0.75) AND (body mass index) AND (cardiovascular disease) AND (forced expiratory volume in 1s : forced vital capacity ratio) AND (free from) AND (less than 30 kg/m2) AND (medical history) AND (medications) AND (no) AND (normotensive) AND (not) AND (oral contraceptives) AND (other than) AND (respiratory disease) AND (sleep apnea))"}
{"candidate_id": "LLM01395", "doc_id": "NCT01602081_inc", "case_bucket": "or", "source_criterion": "Persistent primary or recurrent trans-sphincteric anal fistula", "candidate_expression": "((trans-sphincteric anal fistula) AND ((primary) OR (recurrent)))"}
{"candidate_id": "LLM01396", "doc_id": "NCT02707874_inc", "case_bucket": "other", "source_criterion": "Inpatients having major foot and ankle surgery that will benefit from continuous popliteal sciatic nerve block with an indwelling catheter American Society Anesthesiologists (ASA) physical status I-III 18-85 years of age, inclusive 40-120 kg, inclusive 150 cm of height or greater", "candidate_expression": "((ASA) AND (American Society Anesthesiologists physical status I-III) AND (Inpatients) AND (age 18-85 years) AND (height 150 cm or greater) AND (indwelling catheter) AND (kg 40-120) AND (major foot and ankle surgery) AND (popliteal sciatic nerve block continuous))"}
{"candidate_id": "LLM01397", "doc_id": "NCT03424993_inc", "case_bucket": "other", "source_criterion": "Habitual dietary sodium intake > 3400mg per day", "candidate_expression": "((> 3400mg per day) AND (dietary sodium intake))"}
{"candidate_id": "LLM01398", "doc_id": "NCT02414399_inc", "case_bucket": "other", "source_criterion": "Age 1-59 months, Plan to remain in study area greater than 6 months Discharged from hospital following non-trauma related admission", "candidate_expression": "((1-59 months) AND (Age) AND (Discharged from hospital) AND (Plan) AND (greater than 6 months) AND (hospital) AND (non-trauma related admission) AND (remain in study area))"}
{"candidate_id": "LLM01399", "doc_id": "NCT03004261_exc", "case_bucket": "or", "source_criterion": "Patients receiving prednisone = 1mg/kg/d for the treatment of acute GVHD or mild, severe chronic GVHD. Recipient < 14years of age Donor is sero-positive in HBV/HCV/HIV or RPR.", "candidate_expression": "((< 14years) AND (= 1mg/kg/d) AND (age) AND (chronic) AND (prednisone) AND ((sero-positive in HBV) OR (sero-positive in HCV) OR (sero-positive in HIV) OR (sero-positive in RPR)) AND ((mild) OR (severe)) AND ((GVHD) OR (acute GVHD)))"}
{"candidate_id": "LLM01400", "doc_id": "NCT00050349_exc", "case_bucket": "or", "source_criterion": "Patients with symptomatic CNS metastases or leptomeningeal involvement Patients with known brain metastases, unless these metastases have been treated and/or have been stable for at least six months prior to study start. Subjects with a history of brain metastases must have a head CT with contrast to document either response or progression. Patients with bone metastases as the only site(s) of measurable disease Patients with hepatic artery chemoembolization within the last 6 months (one month if there are other sites of measurable disease) Patients who have been previously treated with radioactive directed therapies Patients who have been previously treated with epothilone Patients with any peripheral neuropathy or unresolved diarrhea greater than Grade 1 Patients with severe cardiac insufficiency patients taking Coumadin or other warfarin-containing agents with the exception of low dose warfarin (1 mg or less) for the maintenance of in-dwelling lines or ports Patients taking any experimental therapies history of another malignancy within 5 years prior to study entry except curatively treated non-melanoma skin cancer, prostate cancer, or cervical cancer in situ Patients with active or suspected acute or chronic uncontrolled infection including abcesses or fistulae Patients with a medical or psychiatric illness that would preclude study or informed consent and/or history of noncompliance to medical regimens or inability or unwillingness to return for all scheduled visits HIV+ patients Pregnant or lactating females.", "candidate_expression": "((CNS metastases symptomatic) AND (Coumadin) AND (Grade greater than 1) AND (HIV +) AND (HIV+) AND (Pregnant) AND (abcesses) AND (another malignancy history of within 5 years prior to study entry) AND (bone metastases only site(s) of measurable disease) AND (brain metastases) AND (cervical cancer in situ active suspected acute) AND (epothilone previously) AND (fistulae) AND (head CT with contrast) AND (hepatic artery chemoembolization within the last 6 months one month) AND (history of) AND (in-dwelling lines) AND (in-dwelling ports) AND (inability to return for all scheduled visits) AND (informed consent) AND (lactating) AND (leptomeningeal involvement symptomatic) AND (medical illness) AND (non-melanoma skin cancer) AND (noncompliance to medical regimens) AND (peripheral neuropathy) AND (preclude study) AND (prostate cancer) AND (psychiatric illness) AND (radioactive directed therapies previously) AND (severe cardiac insufficiency) AND (uncontrolled infection chronic) AND (unresolved diarrhea) AND (unwillingness to return for all scheduled visit) AND (warfarin-containing agents) AND NOT (warfarin low dose 1 mg or less) AND NOT (treated been stable for))"}
```
