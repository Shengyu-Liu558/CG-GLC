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
{"candidate_id": "LLM03526", "doc_id": "NCT02968342_exc", "case_bucket": "or", "source_criterion": "Medical history of chronic psychiatric disease Medical conditions associated with female sexual dysfunction; cardiovascular disease, uncontrolled chronic HT (hypertension) ,DM (diabetes mellitus), History of gynecologic surgery, female gynecological cancer ( breast, ovarian, uterine, cervical) Medications associated with female sexual dysfunction; Antidepressants opiates, beta blockers, Antiepileptics ( gabapentin, topiramate,phenytoin) benzodiazepines", "candidate_expression": "((Antidepressants) AND (Antiepileptics) AND (DM) AND (HT uncontrolled chronic) AND (Medical conditions associated with female sexual dysfunction) AND (Medications associated with female sexual dysfunction) AND (benzodiazepines) AND (beta blockers) AND (breast) AND (cardiovascular disease) AND (cervical) AND (chronic psychiatric disease history) AND (diabetes mellitus) AND (female gynecological cancer) AND (female sexual dysfunction) AND (gabapentin) AND (gynecologic surgery History) AND (hypertension) AND (opiates) AND (ovarian) AND (phenytoin) AND (topiramate) AND (uterine))"}
{"candidate_id": "LLM03527", "doc_id": "NCT02935855_exc", "case_bucket": "other", "source_criterion": "patients with cancer patients with chronic inflammation diseases", "candidate_expression": "((cancer) AND (chronic inflammation diseases))"}
{"candidate_id": "LLM03528", "doc_id": "NCT02573168_exc", "case_bucket": "or", "source_criterion": "Patients posing a serious suicidal risk and/or violence as judged by the investigator; Delirium Dementia Amnestic and other cognitive disorder; Patients with a history of hypothyroidism unless taking a stable dose of thyroid medication and asymptomatic or euthyroid for 6 months; Patients who meet DSM-IV-TR criteria for any significant current substance abuse; hepatic insufficiency (three times the upper limit of normal (ULN) for aspartate aminotransferase (AST) and/or alanine aminotransferase (ALT)); liver transplant recipient; cirrhosis of the liver; malignancy (except basal cell carcinoma) and/or chemotherapy within 1 year prior to screening; malignancy more than 1 year prior to screening must have been local and without metastasis and/or recurrence, and if treated with chemotherapy, without nervous system complications; significant unstable medical condition or life threatening disease with anticipated survival of less than 6 months; need for therapies that may obscure the results of treatment and/or of the study Participation in another clinical trial within 30 days of the screening visit; Anticipated inability to attend scheduled study visits; Patients who in the judgment of the Investigator may be unreliable or uncooperative with the evaluation procedure outlined in this protocol; Patients with a history of prior pharmacogenomic testing; Any change in psychotropic medication (including change in dosage) between screening and baseline; Patients who are known to be pregnant or lactating; Patients with a history of gastric bypass surgery.", "candidate_expression": "((ALT) AND (AST) AND (Amnestic disorder) AND (Anticipated inability to attend scheduled study visits) AND (DSM-IV-TR) AND (Delirium) AND (Dementia) AND (Participation in another clinical trial within 30 days of the screening visit) AND (Patients who are known to be pregnant or lactating) AND (Patients with a history of prior pharmacogenomic testing) AND (alanine aminotransferase) AND (anticipated survival) AND (aspartate aminotransferase) AND (basal cell carcinoma) AND (chemotherapy) AND (cirrhosis of the liver) AND (cognitive disorder) AND (except) AND (gastric bypass surgery) AND (hepatic insufficiency) AND (hypothyroidism) AND (less than 6 months) AND (life threatening disease) AND (liver transplant) AND (local) AND (malignancy) AND (medical condition) AND (metastasis) AND (more than 1 year) AND (psychotropic medication) AND (recurrence) AND (screening) AND (substance abuse) AND (suicidal risk) AND (three times the upper limit of normal) AND (thyroid medication) AND (unless) AND (unstable) AND (violence) AND (within 1 year prior to screening) AND (without))"}
{"candidate_id": "LLM03529", "doc_id": "NCT01824537_exc", "case_bucket": "or", "source_criterion": "Volunteers must not have been vaccinated against HPV-Gardasil-9 (both partners) Any history of cervical, penile, oral or anal cancers Being pregnant or plan on immediately becoming pregnant", "candidate_expression": "((Any history) AND (HPV-Gardasil-9) AND (have been) AND (not) AND (plan on immediately becoming) AND (vaccinated) AND ((pregnant)) AND ((anal cancers) OR (cancers cervical) OR (oral cancers) OR (penile cancers)))"}
{"candidate_id": "LLM03530", "doc_id": "NCT03216967_inc", "case_bucket": "other", "source_criterion": "Adult patients Kidney transplant recipients Patients treated by a calcineurin inhibitor and mycophenolic acid Viremia >= 3 log UI/ml Patients who have given written informed consent Negative pregnancy test (blood ß-HCG dosage)", "candidate_expression": "((>= 3 log UI/ml) AND (Adult) AND (Kidney transplant) AND (Negative) AND (Patients who have given written informed consent) AND (Viremia) AND (blood ß-HCG dosage) AND (calcineurin inhibitor) AND (mycophenolic acid) AND (pregnancy test))"}
{"candidate_id": "LLM03531", "doc_id": "NCT03176316_exc", "case_bucket": "or", "source_criterion": "Pregnancy, age < 18, nursing, or documented allergy to naloxone", "candidate_expression": "((< 18) AND (naloxone) AND ((Pregnancy) OR (age) OR (allergy) OR (nursing)))"}
{"candidate_id": "LLM03532", "doc_id": "NCT00404495_exc", "case_bucket": "other", "source_criterion": "Diagnosis of brainstem glioma Concurrent administration of any other anti-tumor therapy Pre-existing uncontrolled diarrhea", "candidate_expression": "((anti-tumor therapy Concurrent any other) AND (brainstem glioma) AND (uncontrolled diarrhea))"}
{"candidate_id": "LLM03533", "doc_id": "NCT01711801_inc", "case_bucket": "or", "source_criterion": "Healthy male volunteers, 18 to 45 years of age, inclusive. Healthy status is defined by absence of evidence of any active or chronic disease following a detailed medical and surgical history, a complete physical examination including vital signs, 12-lead ECG, hematology, blood chemistry, serology and urinalysis Body mass index (BMI) 18 to 30 kg/m2 inclusive Male subjects (whether surgically sterilized or not) with female partners of child-bearing potential must use two forms of contraception, one of which must be a barrier method, for the duration of the study and for 77 days after the last dose", "candidate_expression": "((12-lead ECG) AND (18 to 30 kg/m2 inclusive) AND (18 to 45 years , inclusive) AND (Body mass index (BMI)) AND (Healthy) AND (Male) AND (absence) AND (age) AND (barrier method) AND (blood chemistry) AND (child-bearing potential) AND (evidence of any active or chronic disease) AND (female) AND (for 77 days after the last dose) AND (for the duration of the study) AND (forms of contraception) AND (hematology) AND (male) AND (medical history) AND (not) AND (physical examination) AND (serology) AND (surgical history) AND (surgically sterilized) AND (the last dose) AND (the study) AND (two) AND (urinalysis) AND (vital signs))"}
{"candidate_id": "LLM03534", "doc_id": "NCT02464813_inc", "case_bucket": "or", "source_criterion": "Adolescent (10-21 years) undergoing spinal fusion for idiopathic scoliosis, spondylolisthesis or Scheuermann kyphosis. Posterior spinal fusion No contraindication for Pregabalin use ASA I-III Written informed consent", "candidate_expression": "((ASA I-III) AND (Adolescent) AND (Posterior spinal fusion) AND (Pregabalin) AND (Written informed consent) AND (spinal fusion) AND (years 10-21 years) AND NOT (contraindication) AND ((Scheuermann kyphosis) OR (idiopathic scoliosis) OR (spondylolisthesis)))"}
{"candidate_id": "LLM03535", "doc_id": "NCT01856491_exc", "case_bucket": "or", "source_criterion": "Known or suspected sensitivity to Dexamethasone Acetate (DXA) Mechanical tricuspid heart valve Subject is enrolled in any other concurrent study without prior written approval from Boston Scientific (BSC), with the exception of local mandatory governmental registries and observational studies/registries that are not in conflict and do not affect the following: Schedule of procedures for the RELIANCE 4-Front Study (i.e. should not cause additional or missed visits); RELIANCE 4-Front Study outcome (i.e. involve medications that could affect the heart rate of the subject); Conduct of the RELIANCE 4-Front Study per Good Clinical Practice (GCP)/ International Organization for Standardization (ISO) 14155:2011/ 21 CFR 812/ local regulations Currently on the active heart transplant list Documented life expectancy of less than 12 months Women of childbearing potential who are or might be pregnant at the time of study enrollment (method of assessment upon physician discretion) Currently requiring chronic dialysis", "candidate_expression": "((Dexamethasone Acetate (DXA)) AND (Mechanical tricuspid heart valve) AND (Women) AND (active heart transplant list) AND (childbearing potential) AND (chronic dialysis) AND (life expectancy less than 12 months) AND (pregnant are or might be at the time of study enrollment) AND (requiring chronic dialysis Currently) AND (sensitivity to Dexamethasone Acetate (DXA)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM03536", "doc_id": "NCT02798237_exc", "case_bucket": "or", "source_criterion": "cognitive impairment (Mini-Mental Status Examination score: illiterate 13 points; elementary and middle school 18 points; and high-school 26 points; or inability to respond to verbal command); inability to walk independently for at least 10 minutes, with or without walking devices; pain or other disorders precluding their participation.", "candidate_expression": "((Mini-Mental Status Examination score) AND (cognitive impairment) AND (elementary) AND (high-school 26 points) AND (illiterate 13 points) AND (inability to respond to verbal command) AND (inability to walk independently at least 10 minutes) AND (middle school) AND (other disorders) AND (pain) AND (pain or other disorders precluding their participation) AND (walking devices))"}
{"candidate_id": "LLM03537", "doc_id": "NCT03355326_inc", "case_bucket": "other", "source_criterion": "Diagnosis of uncomplicated gastroschisis Gestational age >33 weeks at time of delivery Weight >1900g at time of delivery Transfer of patient to Riley Hospital for Children prior to any abdominal surgery", "candidate_expression": "((Gestational age >33 weeks at time of delivery) AND (Riley Hospital for Children) AND (Transfer prior to any abdominal surgery) AND (Weight >1900g at time of delivery) AND (abdominal surgery) AND (gastroschisis uncomplicated))"}
{"candidate_id": "LLM03538", "doc_id": "NCT02509949_inc", "case_bucket": "other", "source_criterion": "age > 17 and < 60 years; American Society of Anesthesiology (ASA) I-III; admitted for living donor renal transplantation.", "candidate_expression": "((> 17 and < 60 years) AND (American Society of Anesthesiology (ASA)) AND (I-III) AND (admitted for) AND (age) AND (living donor renal transplantation))"}
{"candidate_id": "LLM03539", "doc_id": "NCT02242188_inc", "case_bucket": "or", "source_criterion": "Term singleton infants (>37 weeks gestational age) Birth weight > 2500g Healthy at inclusion Breastfed exclusively or predominantly (>50% meals) at inclusion No previous iron supplementation No previous blood transfusion Informed consent given", "candidate_expression": "((Birth weight > 2500g) AND (Breastfed at inclusion >50% meals) AND (Healthy at inclusion) AND (Informed consent given) AND (gestational age >37 weeks) AND NOT (iron supplementation previous) AND NOT (blood transfusion previous) AND ((exclusively) OR (predominantly)) AND ((Term infants) OR (singleton infants)))"}
{"candidate_id": "LLM03540", "doc_id": "NCT03140423_inc", "case_bucket": "other", "source_criterion": "Inclusion criteria includes all U.S. HCA hospitals with an adult ICU; Note: Unit of randomization is the hospital, but the participants are hospital adult ICUs All patients within adult ICUs are included, including rare patients <18 years and >=12 years.", "candidate_expression": "((<18 years and >=12 years) AND (HCA hospitals) AND (U.S.) AND (adult) AND (adult ICU) AND (adult ICUs) AND (rare patients) AND (year))"}
{"candidate_id": "LLM03541", "doc_id": "NCT03380429_inc", "case_bucket": "or", "source_criterion": "Subjects aged 18 years or older, at the time of signing the informed consent. Subjects with documented physician diagnosis of asthma as their primary respiratory disease. ACT score <20 at screening visit. Non-smokers (never smoked or not smoking for >6 months with <10 pack years history (Pack years = [cigarettes per day smoked/20] multiplied by number of years smoked). Male or female subjects will be included. A female subject is eligible to participate if she is not pregnant, not breastfeeding, and at least one of the following conditions applies: (i) Not a woman of childbearing potential (WOCBP). (ii) A WOCBP who agrees to follow the contraceptive guidance during the treatment period and for at least 5 days] after the last dose of study treatment. Capable of giving signed informed consent which includes compliance with the requirements and restrictions listed in the consent form and protocol. Subject understands and is willing, able, and likely to comply with study procedures and restrictions. Subject must be able to read in a language supported by the smart phone app in their region. Subject must have been on maintenance therapy (Fixed dose combination ICS/LABA) for 3 months, cannot have changed dose in the month prior to screening and be able to change to an equivalent dose of RELVAR/BREO for the duration of the study. Other background asthma medication such as anti-leukotrienes and oral corticosteroids are permitted provided the dose has been stable for 1 month prior to screening. Subject must be able to change to Salbutamol/Albuterol MDI rescue for the duration of the study and judged capable of withholding albuterol/salbutamol for at least 6 hours prior to study visits. Subject must have their own Android or iPhone operating system (IOS) smart phone and a data package suitable for the installation and running of the app and sending and receiving data. Data used by the CIS is approximately 1 megabyte (MB) per month as a maximum; this is less data than a 1 minute video streamed from YouTube (2MB). Subjects must be willing and able to download the app on their personal smart phone and keep it turned on for the duration of the study. This will also require Bluetooth to be turned on for duration of the study. Subjects will also have to turn on mobile data for the app for the duration of study; unless travelling and when extra data roaming costs could be incurred. ACT score <20 at randomization visit (visit 2).", "candidate_expression": "((A female subject is eligible to participate if she is not pregnant, not breastfeeding, and at least one of the following conditions applies: (i) Not a woman of childbearing potential (WOCBP). (ii) A WOCBP who agrees to follow the contraceptive guidance during the treatment period and for at least 5 days] after the last dose of study treatment.) AND (ACT score <20 at randomization visit) AND (ACT score <20 at screening visit) AND (Albuterol) AND (Capable of giving signed informed consent which includes compliance with the requirements and restrictions listed in the consent form and protocol.) AND (MDI rescue the duration of the study) AND (Non-smokers) AND (Salbutamol) AND (aged 18 years or older at the time of signing the informed consent) AND (albuterol) AND (asthma primary respiratory disease) AND (capable of withholding for at least 6 hours prior to study visits) AND (change able to for the duration of the study) AND (combination ICS/LABA Fixed dose) AND (maintenance therapy for 3 months changed dose) AND (pack years <10) AND (salbutamol) AND ((never smoked) OR (not smoking for >6 months)) AND ((Male) OR (female)))"}
{"candidate_id": "LLM03542", "doc_id": "NCT02601157_exc", "case_bucket": "or", "source_criterion": "1. High risk profiles for ischemic adverse events such as A. ST-segment elevation myocardial infarction (STEMI) B. Patients with cardiogenic shock or concomitant severe decompensated heart failure C. Myocardial infarction or stent thrombosis in spite of the maintenance of antiplatelet therapy D. Restenosis in stented segments or previous sites of balloon angioplasty 2. Patients who cannot follow allocated DAPT schedule due to the planned surgery or elective procedure within 3 months after the stenting 3. Recent history of major surgery or evident events of gastrointestinal bleeding within 1 month from the procedure 4. Patients on anticoagulation therapy with warfarin or other anticoagulants 5. Life expectancy less than 1 year (such as malignancies or other chronic systemic diseases) 6. Pregnant women 7. Past history of allergy or other contraindications for the following medications/materials: aspirin, clopidogrel, heparin, cobalt chromium, sirolimus", "candidate_expression": "((High risk profiles) AND (Life expectancy) AND (Pregnant) AND (allergy) AND (anticoagulation therapy) AND (antiplatelet therapy) AND (cannot follow allocated DAPT schedule) AND (contraindications) AND (decompensated) AND (elective) AND (ischemic adverse events) AND (less than 1 year) AND (other) AND (planned) AND (severe) AND (within 1 month from the procedure) AND (within 3 months after the stenting) AND (women) AND ((Myocardial infarction) OR (stent thrombosis)) AND ((Restenosis) OR (ST-segment elevation myocardial infarction (STEMI)) OR (cardiogenic shock) OR (heart failure)) AND ((procedure) OR (surgery)) AND ((events of gastrointestinal bleeding) OR (major surgery)) AND ((anticoagulants) OR (warfarin)) AND ((chronic systemic diseases) OR (malignancies)) AND ((aspirin) OR (clopidogrel) OR (cobalt chromium) OR (heparin) OR (sirolimus)))"}
{"candidate_id": "LLM03543", "doc_id": "NCT01483118_inc", "case_bucket": "or", "source_criterion": "Patients aged greater than 18 years of age Ability to understand and willingness to comply with the study protocol Written informed consent Patients meeting the Rotterdam PCOS workshop criteria for polycystic ovary syndrome, defined by oligomenorrhea or amenorrhea and at least one of the following two signs: clinical or biochemical evidence of hyperandrogenism or ultrasound finding of polycystic appearing ovaries.", "candidate_expression": "((Ability to understand and willingness to comply with the study protocol) AND (Rotterdam PCOS workshop criteria for polycystic ovary syndrome) AND (Written informed consent) AND (age) AND (aged) AND (amenorrhea) AND (at least one) AND (greater than 18 years) AND (hyperandrogenism) AND (meeting) AND (oligomenorrhea) AND (polycystic ovaries) AND (ultrasound))"}
{"candidate_id": "LLM03544", "doc_id": "NCT03491059_inc", "case_bucket": "or", "source_criterion": "males and females greater than or equal to 18 years of age current regular user of e-cigarettes (use at least once daily for the past 30 days) with nicotine strength > 6mg/ml health medical history abstinent from any tobacco/nicotine use for 4 hours prior to imaging", "candidate_expression": "((abstinent for 4 hours prior to imaging) AND (age greater than or equal to 18 years) AND (females) AND (males) AND (medical history health) AND (nicotine) AND (nicotine strength > 6mg/ml) AND (tobacco) AND (user regular e-cigarettes))"}
{"candidate_id": "LLM03545", "doc_id": "NCT03171987_inc", "case_bucket": "scope", "source_criterion": "All subjects underwent a detailed history and systemic physical examination including neurologic and musculoskeletal evaluations. To rule out any confounding etiologies, basic diagnostic laboratory tests including complete blood count and acute phase reactants (erythrocyte sedimentation rate and C-reactive protein) were performed. The patients diagnosed as having acute non-specific low back pain according to history and physical examinations were invited to participate and will be informed about the purpose and course of the study. A primary complaint of pain in the area between the 12th rib and buttock crease without leg pain Female or male, 20 - 80 years of age Low back pain of less than six weeks' duration; and at least moderate pain intensity (NRS<U+2267>4)", "candidate_expression": "((C-reactive protein) AND (Female) AND (Low back pain less than six weeks' duration) AND (NRS 4) AND (acute phase reactants) AND (age 20 - 80 years) AND (complete blood count) AND (diagnostic laboratory tests) AND (erythrocyte sedimentation rate) AND (history) AND (male) AND (non-specific low back pain acute) AND (pain area between the 12th rib and buttock crease) AND (pain intensity at least moderate) AND (physical examinations) AND NOT (leg pain))"}
{"candidate_id": "LLM03546", "doc_id": "NCT02256956_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03547", "doc_id": "NCT02759861_inc", "case_bucket": "or", "source_criterion": "The subject must be willingly and able to provide written informed consent Age 19 years of age or older (The age of consent in Nebraska) HCV treatment-naïve, as defined as no prior exposure to any Interferon (IFN), RBV, or other FDA approved or experimental HCV-specific direct-acting antiviral agent HCV RNA level at most 6 months prior to the Baseline/Day 1 visit. HCV genotyping 1a, 1b, or mixed 1a/ab. Any non-definitive results will exclude the subject from study participation. Alcohol misuse as defined by the Alcohol Use Disorders Identification Test (AUDIT) score subjects must score > 8 (associated with harmful or hazardous drinking) History of a liver biopsy showing cirrhosis (e.g. Metavir score = 4 or Ishak score > 5) Fibroscan showing cirrhosis or results > 12.5 kPa FIBRO Spect II index consistent with F3 or F4 AND an AST : platelet ration index (APRI) of > 2 during Screening Liver biopsy within 2 years of Screening showing absence of cirrhosis Fibroscan within 6 months of Baseline/Day1 with a result of = 12.5 kPa FIBRO Spect II Index consistent with F0- F2 AND APRI of = 1 during Screening Liver imaging within 6 months of Baseline/Day 1 to exclude hepatocellular carcinoma HCC) is required ALT < 10 x the upper limit of normal (ULN) AST < 10 x ULN Direct bilirubin < 2.0 x ULN Platelets > 50,000 HbA1c < 8.5% Creatinine clearance (CLcr) = 60 mL /min, as calculated by the Cockcroft-Gault equation Hemoglobin = 11 g/dL for female subjects; = 12 g/dL for male subjects. Albumin = 2.5 g/dL INR = 1.5 x ULN unless subject has known hemophilia or is stable on an anticoagulant regimen affecting INR. Subject has not been treated with any investigational drug or device within 30 days of the screening visit.", "candidate_expression": "((19 years of age or older) AND (1a, 1b, or mixed 1a/ab) AND (< 10 x ULN) AND (< 10 x the upper limit of normal (ULN)) AND (< 2.0 x ULN) AND (< 8.5%) AND (= 1) AND (= 1.5 x ULN) AND (= 11 g/dL) AND (= 12 g/dL) AND (= 12.5 kPa) AND (= 2.5 g/dL) AND (= 4) AND (= 60 mL /min) AND (> 12.5 kPa) AND (> 2) AND (> 5) AND (> 50,000) AND (> 8) AND (ALT) AND (APRI) AND (AST) AND (Age) AND (Albumin) AND (Alcohol Use Disorders Identification Test (AUDIT) score) AND (Alcohol misuse) AND (Cockcroft-Gault equation) AND (Creatinine clearance (CLcr)) AND (Direct bilirubin) AND (F0- F2) AND (F3 or F4) AND (FIBRO Spect II Index) AND (FIBRO Spect II index) AND (Fibroscan) AND (HCV) AND (HCV RNA level) AND (HCV genotyping) AND (HbA1c) AND (Hemoglobin) AND (INR) AND (Interferon (IFN)) AND (Ishak score) AND (Liver biopsy) AND (Liver imaging) AND (Metavir score) AND (Platelets) AND (RBV) AND (The subject must be willingly and able to provide written informed consent) AND (absence) AND (at most 6 months prior to the Baseline/Day 1 visit) AND (cirrhosis) AND (during Screening) AND (exclude) AND (female) AND (hemophilia) AND (hepatocellular carcinoma HCC)) AND (liver biopsy) AND (male) AND (naïve) AND (no) AND (platelet ration index (APRI)) AND (prior) AND (stable on an anticoagulant regimen affecting INR) AND (the Baseline/Day 1 visit) AND (treatment) AND (unless) AND (within 2 years of Screening) AND (within 6 months of Baseline/Day 1) AND (within 6 months of Baseline/Day1))"}
{"candidate_id": "LLM03548", "doc_id": "NCT02969187_exc", "case_bucket": "or", "source_criterion": "BMI <35 and > 60 kg/m2 Inability to walk (bed-bound or wheelchair dependence) open abdominal surgeries except simple appendectomy and common OB/GYN procedures in the pelvis (hysterectomy, C-section, and oophorectomy, tubal ligation) laparoscopic bowel or solid organ resection except laparoscopic cholecystectomy ventral hernia repair with mesh Preoperative chronic opiate use for chronic pain defined as opiate usage at least 60 mg/day of morphine equivalent for = 3 months (as defined by International Association for the Study of Pain22) in the one year period prior to the bariatric surgery The American Society of Anesthesiologists (ASA) score > 3 History of hypersensitivity or adverse reaction to bupivacaine or narcotics Inability to speak English ventral hernia repair Cholecystectomy hiatal hernia repair with posterior cruroplasty extensive lysis of adhesions other procedures that mandate addition of \"trocar(s)\" or \"feeding tube\" Addition of trocar(s) or conversion of surgery to hand-assisted or open", "candidate_expression": "((American Society of Anesthesiologists (ASA) score > 3) AND (BMI <35 and > 60 kg/m2) AND (Cholecystectomy) AND (Inability to walk) AND (bariatric surgery the bariatric surgery) AND (chronic pain) AND (common OB/GYN procedures pelvis) AND (hiatal hernia) AND (lysis of adhesions extensive) AND (open abdominal surgeries) AND (opiate Preoperative chronic) AND (opiate at least 60 mg/day of morphine equivalent for = 3 months in the one year period prior to the bariatric surgery) AND (posterior cruroplasty) AND (repair) AND (repair with mesh) AND (simple appendectomy) AND (surgery) AND (ventral hernia) AND NOT (laparoscopic cholecystectomy) AND ((C-section) OR (hysterectomy) OR (oophorectomy) OR (tubal ligation)) AND ((laparoscopic bowel resection) OR (solid organ resection)) AND ((adverse reaction) OR (hypersensitivity)) AND ((bupivacaine) OR (narcotics)) AND ((bed-bound) OR (wheelchair dependence)) AND ((conversion of surgery) OR (trocar Addition of)) AND ((hand-assisted) OR (open)))"}
{"candidate_id": "LLM03549", "doc_id": "NCT02961582_exc", "case_bucket": "or", "source_criterion": "Obstructed outlet syndrome (objectified by defeacography) Irritable bowel syndrome (Rome-IV criteria for irritable bowel syndrome) Congenital or organic bowel pathology Rectal prolapse Anatomical limitations preventing placement of an electrode Skin and perineal disease with risk of infection Previous large bowel/rectal surgery Stoma Coexisting neurological disease Significant psychological co-morbidity as assessed subjectively by the investigator Being or attempting to become pregnant during study follow-up", "candidate_expression": "((Anatomical limitations) AND (Being or attempting to become pregnant during study follow-up) AND (Irritable bowel syndrome) AND (Obstructed outlet syndrome) AND (Rectal prolapse) AND (Rome-IV criteria) AND (Stoma) AND (as assessed subjectively by the investigator) AND (defeacography) AND (irritable bowel syndrome) AND (neurological disease) AND (psychological co-morbidity Significant) AND (risk of infection) AND NOT (placement of an electrode) AND ((Skin disease) OR (perineal disease)) AND ((large bowel surgery) OR (rectal surgery)) AND ((Congenital bowel pathology) OR (organic bowel pathology)))"}
{"candidate_id": "LLM03550", "doc_id": "NCT02312960_exc", "case_bucket": "other", "source_criterion": "Not applicable to this follow up study", "candidate_expression": "(EMPTY)"}
```
