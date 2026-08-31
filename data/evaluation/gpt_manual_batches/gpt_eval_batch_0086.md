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
{"candidate_id": "LLM02126", "doc_id": "NCT01501201_exc", "case_bucket": "other", "source_criterion": "Contraindication to bariatric surgery Pregnancy Affiliation of health care assurance Psychiatric disorders", "candidate_expression": "((Affiliation of health care assurance) AND (Contraindication) AND (Pregnancy) AND (Psychiatric disorders) AND (bariatric surgery))"}
{"candidate_id": "LLM02127", "doc_id": "NCT03351608_exc", "case_bucket": "or", "source_criterion": "Has any clinically significant condition or situation (eg, anatomical malformation that complicates intubation) other than the condition being studied that, in the opinion of the investigator, would interfere with the trial evaluations or optimal participation in the trial. Has a neuromuscular disorder that may affect NMB and/or trial assessments. Is dialysis-dependent or has (or is suspected of having) severe renal insufficiency (defined as estimated glomerular filtration rate (eGFR) <30 ml/min). Has or is suspected of having a family or personal history of malignant hyperthermia. Has or is suspected of having an allergy to study treatments or its/their excipients, to opioids/opiates, muscle relaxants or their excipients, or other medication(s) used during general anesthesia. Has received or is planned to receive toremifene and/or fusidic acid via IV administration within 24 hours before or within 24 hours after administration of study treatment. Has been previously treated with sugammadex or has participated in a sugammadex clinical trial. Is currently participating in or has participated in an interventional clinical trial with an investigational compound or device within 30 days of signing the informed consent/assent for this current trial.", "candidate_expression": "((<30 ml/min) AND (IV administration) AND (administration of study treatment) AND (allergy) AND (anatomical malformation) AND (clinically significant) AND (during general anesthesia) AND (estimated glomerular filtration rate (eGFR)) AND (general anesthesia) AND (malignant hyperthermia) AND (neuromuscular disorder) AND (other) AND (other than) AND (planned to) AND (previously) AND (signing the informed assent) AND (signing the informed consent) AND (sugammadex) AND (the condition being studied) AND ((affect NMB) OR (affect trial assessments)) AND ((dialysis-dependent) OR (severe renal insufficiency)) AND ((condition) OR (situation)) AND ((family) OR (personal history)) AND ((excipients) OR (medication) OR (muscle relaxants) OR (opiates) OR (opioids) OR (study treatments)) AND ((fusidic acid) OR (toremifene)) AND ((within 24 hours after administration of study treatment) OR (within 24 hours before administration of study treatment)) AND ((participated in clinical trial) OR (sugammadex)) AND ((currently participating in an interventional clinical trial) OR (has participated in an interventional clinical trial)) AND ((device) OR (investigational compound)) AND ((within 30 days of signing the informed assent) OR (within 30 days of signing the informed consent)) AND ((interfere with optimal participation) OR (interfere with the trial evaluations)))"}
{"candidate_id": "LLM02128", "doc_id": "NCT02476461_exc", "case_bucket": "other", "source_criterion": "previous treated dupuytrens contracture same hand more than tree fingers involvement we will not include thumbs other things affecting hand function ASA>3 expected to live under five years Tetracycline treatment within two weeks pregnancy nursing allergy to clostridium histolyticum participant in other trial", "candidate_expression": "((ASA >3) AND (Tetracycline within two weeks) AND (allergy clostridium histolyticum) AND (dupuytrens contracture previous treated same hand) AND (expected to live under five years) AND (fingers involvement more than tree) AND (nursing) AND (other things affecting hand function) AND (participant in other trial) AND (pregnancy))"}
{"candidate_id": "LLM02129", "doc_id": "NCT03253796_exc", "case_bucket": "or", "source_criterion": "Has bilateral sacroiliitis Grade 2 or unilateral sacroiliitis Grade 3 or Grade 4 Is a nursing or pregnant female, or intends to become pregnant within 6 months after receiving trial medication Intends to donate eggs (female participants) or sperm (male participants) while receiving trial medication or within 6 months after trial medication Has any clinically significant condition or situation that would interfere with the trial evaluations or participation in the trial Has ever received any cytotoxic drugs, including chlorambucil, cyclophosphamide, nitrogen mustard, or other alkylating agents • Disease-modifying anti-rheumatic drugs (30 days off drug) • Live vaccinations (3 months off drug) • Investigational medications (30 days or 5 half-lives off drug, whichever is longer) • Bacille Calmette-Guerin (BCG) vaccination (12 months off drug) Has any systemic inflammatory condition, including psoriatic arthritis, active Lyme disease, systemic lupus erythematosus, infectious arthritis, vasculitis, parvovirus infection, rheumatoid arthritis, active uveitis, or active IBD Has a history of latent or active granulomatous infection prior to Screening Had a nontuberculous mycobacterial infection or opportunistic infection within 6 months prior to Screening Has a history of an infected joint prosthesis, or has received antibiotics for a suspected infection of a joint prosthesis, if that prosthesis has not been removed or replaced Had a serious infection, has been hospitalized for an infection, or has been treated with IV antibiotics for an infection within 2 months prior to Baseline Had a history of, or ongoing, chronic or recurrent infectious disease Is known to be infected with human immunodeficiency virus (HIV) or seropositive for hepatitis C virus (HCV) Has had a chest x-ray within 2 months prior to Screening that shows an abnormality suggestive of a current active infection or malignancy Has a history of lymphoproliferative disease Has had a malignancy within 5 years before screening (exceptions are squamous and basal cell carcinomas of the skin and carcinoma in situ of cervix that has been surgically cured) Has a history of known demyelinating diseases such as multiple sclerosis or optic neuritis Has a history of or concurrent congestive heart failure of any grade Has a transplanted organ (with the exception of a corneal transplant performed >= 3 months prior to baseline) Has current signs or symptoms of significant medical illness which could interfere with the trial, or require treatment that might interfere with the trial Is a user of recreational or illicit drugs or has or had a substance abuse (drug or alcohol) problem within the previous 2 years", "candidate_expression": "((12 months off drug) AND (3 months off drug) AND (30 days off drug) AND (>= 3 months prior to baseline) AND (Bacille Calmette-Guerin (BCG) vaccination) AND (Disease-modifying anti-rheumatic drugs) AND (Grade 2) AND (Has any clinically significant condition or situation that would interfere with the trial evaluations or participation in the trial) AND (Investigational medications) AND (Is a user of recreational or illicit drugs or has or had a substance abuse (drug or alcohol) problem within the previous 2 years) AND (Live vaccinations) AND (Screening) AND (abnormality) AND (active) AND (antibiotics) AND (bilateral) AND (cervix) AND (chest x-ray) AND (congestive heart failure) AND (corneal transplant) AND (current) AND (cytotoxic drugs) AND (demyelinating diseases) AND (donate eggs) AND (donate sperm) AND (exception of) AND (exceptions) AND (female) AND (granulomatous infection) AND (history) AND (infection) AND (infectious disease) AND (inflammatory condition) AND (intends to become) AND (interfere with the trial) AND (joint prosthesis) AND (lymphoproliferative disease) AND (malignancy) AND (medical illness) AND (pregnant) AND (prior to Screening) AND (require) AND (screening) AND (significant) AND (suggestive) AND (surgically) AND (surgically cured) AND (suspected) AND (transplanted organ) AND (trial medication) AND (unilateral) AND (within 2 months prior to Baseline) AND (within 2 months prior to Screening) AND (within 5 years before screening) AND (within 6 months after receiving trial medication) AND (within 6 months prior to Screening) AND ((basal cell carcinomas of the skin) OR (carcinoma in situ) OR (squamous carcinomas of the skin)) AND ((multiple sclerosis) OR (optic neuritis)) AND ((concurrent) OR (history)) AND ((interfere with the trial) OR (treatment)) AND ((female) OR (male)) AND ((while receiving trial medication) OR (within 6 months after trial medication)) AND ((sacroiliitis)) AND ((alkylating agents) OR (chlorambucil) OR (cyclophosphamide) OR (nitrogen mustard)) AND ((30 days off drug) OR (5 half-lives off drug)) AND ((Lyme disease) OR (active IBD) OR (active uveitis) OR (infectious arthritis) OR (parvovirus infection) OR (psoriatic arthritis) OR (rheumatoid arthritis) OR (systemic lupus erythematosus) OR (vasculitis)) AND ((active) OR (latent)) AND ((Grade 3) OR (Grade 4)) AND ((nontuberculous mycobacterial infection) OR (opportunistic infection)) AND ((infected) OR (infection)) AND ((IV antibiotics) OR (hospitalized) OR (serious infection)) AND ((chronic) OR (recurrent)) AND ((history) OR (ongoing)) AND ((human immunodeficiency virus (HIV)) OR (seropositive for hepatitis C virus (HCV))) AND ((nursing) OR (pregnant)) AND ((infection) OR (malignancy)))"}
{"candidate_id": "LLM02130", "doc_id": "NCT01895946_exc", "case_bucket": "or", "source_criterion": "Clinically significant abnormalities of glucose metabolism Spinal cord compression or brain metastases unless asymptomatic, treated and stable (not requiring steroids) Evidence of severe or uncontrolled systemic diseases, including active bleeding diatheses or active infections including hepatitis B, C and Human Immunodeficiency Virus (HIV) Evidence of clinically significant cardiac abnormalities, uncontrolled hypotension, left ventricular ejection fraction below the lower limit of normal for the site or experience of significant cardiac interventional procedures A bad reaction to AZD5363 or any drugs similar to it in structure or class", "candidate_expression": "((AZD5363) AND (abnormalities of glucose metabolism Clinically significant) AND (asymptomatic treated stable) AND (bad reaction to AZD5363) AND (significant) AND (systemic diseases) AND NOT (steroids) AND ((severe) OR (uncontrolled)) AND ((active bleeding diatheses) OR (active infections)) AND ((Human Immunodeficiency Virus (HIV)) OR (hepatitis B) OR (hepatitis C)) AND ((cardiac abnormalities clinically significant) OR (cardiac interventional procedures significant) OR (left ventricular ejection fraction below the lower limit of normal) OR (uncontrolled hypotension)) AND ((Spinal cord compression) OR (brain metastases)))"}
{"candidate_id": "LLM02131", "doc_id": "NCT03029078_inc", "case_bucket": "or", "source_criterion": "Patient harboring a GRE or CRE bacteria Colonization confirmed by our microbiology department, including at least 3 positives swabs in the last month", "candidate_expression": "((Colonization) AND (at least 3) AND (confirmed by our microbiology department) AND (in the last mont) AND (positives) AND (swabs) AND ((CRE bacteria) OR (GRE bacteria)))"}
{"candidate_id": "LLM02132", "doc_id": "NCT02430740_exc", "case_bucket": "other", "source_criterion": "polycystic ovaries untreated thyroid pathology hypogonadotropic hypogonadism untreaed hyperprolactinemia study drug hypersensitivity previous OHSS unilateral ovariectomy genital malformation BMI>40", "candidate_expression": "((BMI >40) AND (OHSS previous) AND (genital malformation) AND (hyperprolactinemia untreaed) AND (hypersensitivity) AND (hypogonadotropic hypogonadism) AND (ovariectomy unilateral) AND (polycystic ovaries) AND (study drug) AND (thyroid pathology untreated))"}
{"candidate_id": "LLM02133", "doc_id": "NCT01579604_inc", "case_bucket": "or", "source_criterion": "Cervical spine injury with functional loss in the upper extremity Greater than 4 months out from C-spine injury Stable motor recovery Medically stable International Classification for Surgery of the Hand in Tetraplegia of 0-5 at 6 months Grade 0 finger/thumb extension at 6 months Subjects fluent in English or when not fluent, an appropriate translator is present", "candidate_expression": "((C-spine injury Greater than 4 month) AND (Cervical spine injury functional loss) AND (International Classification for Surgery of the Hand in Tetraplegia 0-5 at 6 months) AND (Subjects fluent in English or when not fluent, an appropriate translator is present) AND (extension Grade 0 at 6 months) AND (motor recovery Stable) AND (stable Medically) AND ((finger) OR (thumb)))"}
{"candidate_id": "LLM02134", "doc_id": "NCT03299517_exc", "case_bucket": "or", "source_criterion": "Pregnancy Hemodynamic instability Body mass index greater than 40 kg / m2 Use of intravenous amiodarone or lidocaine in the last 24 hours Acute coronary syndrome Presence of tachycardia with irregular or supraventricular RR Contraindications to study drugs", "candidate_expression": "((Acute coronary syndrome) AND (Body mass index greater than 40 kg / m2) AND (Contraindications) AND (Hemodynamic instability) AND (Pregnancy) AND (amiodarone) AND (irregular RR) AND (lidocaine) AND (study drugs) AND (supraventricular RR) AND (tachycardia))"}
{"candidate_id": "LLM02135", "doc_id": "NCT01907230_exc", "case_bucket": "or", "source_criterion": "HCV, HIV, or HDV coinfection. HCC or other malignancy within 3 years. Decompensated liver cirrhosis (CTP score = 7). Uremia patients under hemodialysis or continuous ambulatory peritoneal dialysis or patients with Ccr < 50 mL/min Pregnant or breastfeeding women. Women of child-bearing potential (WOCBP) who are unwilling or unable to use an acceptable method of contraception to avoid pregnancy throughout the study and for up to 4 weeks after the last dose of study drug.", "candidate_expression": "((< 50 mL/min) AND (= 7) AND (CTP score) AND (Ccr) AND (Decompensated liver cirrhosis) AND (Pregnant or breastfeeding women) AND (Uremia) AND (Women of child-bearing potential (WOCBP) who are unwilling or unable to use an acceptable method of contraception to avoid pregnancy throughout the study and for up to 4 weeks after the last dose of study drug) AND (within 3 years) AND ((HCV coinfection) OR (HDV coinfection) OR (coinfection HIV)) AND ((continuous ambulatory peritoneal dialysis) OR (hemodialysis)) AND ((HCC) OR (malignancy)))"}
{"candidate_id": "LLM02136", "doc_id": "NCT03513757_inc", "case_bucket": "other", "source_criterion": "All children scheduled for outpatient MRI scans with expected duration of scan between 30 minutes and 75 minutes.", "candidate_expression": "((MRI scans outpatient) AND (expected duration of scan between 30 minutes and 75 minutes))"}
{"candidate_id": "LLM02137", "doc_id": "NCT00502567_exc", "case_bucket": "other", "source_criterion": "Inadequate bone marrow reserve history of poorly controlled hypertension", "candidate_expression": "((Inadequate bone marrow reserve) AND (history) AND (poorly controlled hypertension))"}
{"candidate_id": "LLM02138", "doc_id": "NCT02673359_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Congenital uterine malformation. Multifetal pregnancy. Known major fetal structural or chromosomal abnormality. Known allergy or contraindication (relative or absolute) to progesterone therapy. Presence of contraindication to cervical cerclage. Medical conditions complicating pregnancy. Vaginal bleeding.", "candidate_expression": "((Age) AND (Congenital uterine malformation) AND (Medical conditions) AND (Multifetal pregnancy) AND (Vaginal bleeding) AND (cervical cerclage) AND (complicating pregnancy) AND (contraindication) AND (major) AND (progesterone therapy) AND ((allergy) OR (contraindication)) AND ((absolute) OR (relative)) AND ((< 20) OR (> 35 years)) AND ((chromosomal abnormality) OR (fetal structural)))"}
{"candidate_id": "LLM02139", "doc_id": "NCT03091881_inc", "case_bucket": "other", "source_criterion": "Type I diabetic patients Parturients presented for Cesarean section", "candidate_expression": "((Cesarean section) AND (Parturients) AND (Type I diabetic))"}
{"candidate_id": "LLM02140", "doc_id": "NCT02560766_inc", "case_bucket": "or", "source_criterion": "Male and female adolescent patients, aged 13 to 17 years, diagnosed with RLS based on the IRLSSG consensus criteria (Allen RP 2014) (Appendix 2). Total RLS severity score of 15 or greater on the IRLS rating scale at Visit 1 (screening) and at Visit 2 (baseline) (Appendix 8). RLS symptoms for at least 4 of 7 consecutive evenings/nights during the screening period. Body weight greater than 33.4 kg and a healthy weight using age-based body mass index (BMI) range 5th-85th percentile at screening and baseline. Appendix 3 contains BMI-for-age charts that can be consulted. Estimated creatinine clearance of at least 60 mL/min (using the Cockcroft-Gault equation) at screening only. Signed patient and parent Institutional Review Board (IRB)-approved informed consent/assent form (as applicable) before any study-related procedures are performed.", "candidate_expression": "((BMI) AND (Body weight greater than 33.4 kg) AND (Estimated creatinine clearance at least 60 mL/min) AND (IRLSSG consensus criteria) AND (Male) AND (RLS) AND (RLS symptoms at least 4 of 7 consecutive evenings/nights) AND (Signed patient and parent Institutional Review Board (IRB)-approved informed consent/assent form (as applicable) before any study-related procedures are performed) AND (Total RLS severity score 15 or greater) AND (adolescent) AND (aged 13 to 17 years) AND (body mass index 5th-85th percentile) AND (female))"}
{"candidate_id": "LLM02141", "doc_id": "NCT02022709_exc", "case_bucket": "or", "source_criterion": "Having significant medical illnesses that would interfere with the conduct of the study Clinically significant abnormal laboratory finding Having comorbid psychiatric conditions according to the criteria set forth in the DSM-IV(administered by the Mini-International Neuropsychiatric Interview (MINI)) The current OCD symptoms are too severe that the patient cannot finish the evaluation or receive the ERP Being currently at risk for suicide Being pregnant or having the intention to be pregnant before the end of the study A history of having inadequate response to adequate SSRIs or CBT treatment Subjects who are unable to undergo the MRI", "candidate_expression": "((Being pregnant or having the intention to be pregnant before the end of the study) AND (DSM-IV) AND (MRI) AND (OCD symptoms) AND (comorbid) AND (inadequate) AND (psychiatric conditions) AND (response) AND (risk for suicide) AND (severe) AND (unable to) AND ((CBT) OR (SSRIs)))"}
{"candidate_id": "LLM02142", "doc_id": "NCT02162433_inc", "case_bucket": "or", "source_criterion": "Patients between 3 to 16 years of age undergoing adenotonsillectomy, with or without myringotomy or myringoplasty ASA 1 & 2", "candidate_expression": "((ASA 1 & 2) AND (adenotonsillectomy undergoing) AND (age between 3 to 16 years) AND (myringoplasty) AND (myringotomy))"}
{"candidate_id": "LLM02143", "doc_id": "NCT03518034_exc", "case_bucket": "or", "source_criterion": "Participants with congenital or acquired hypogonadism for whom long-term therapy with placebo would not be medically appropriate Participants with prostate specific antigen (PSA) > 3.0 ng/mL (or 1.5 if on 5-alpha reductase inhibitors) Participants who have been treated with testosterone in the past 6 months and for whom testosterone therapy is contraindicated Confirmed testosterone < 100 ng/dL Body Mass Index (BMI) > 50 Hemoglobin A1c (HbA1C) > 11% Hematocrit (Hct) > 50% Estimated Glomerular Filtration Rate (eGFR) < 30 ml/min History of deep vein thrombosis or pulmonary embolism or prostate cancer or heart failure (Class III and IV).", "candidate_expression": "((1.5) AND (5-alpha reductase inhibitors) AND (< 100 ng/dL) AND (< 30 ml/min) AND (> 11%) AND (> 3.0 ng/mL) AND (> 50) AND (> 50%) AND (Body Mass Index (BMI)) AND (Class III) AND (Class IV) AND (Confirmed testosterone) AND (Estimated Glomerular Filtration Rate (eGFR)) AND (Hematocrit (Hct)) AND (Hemoglobin A1c (HbA1C)) AND (acquired hypogonadism) AND (congenital hypogonadism) AND (contraindicated) AND (deep vein thrombosis) AND (heart failure) AND (in the past 6 months) AND (prostate cancer) AND (prostate specific antigen (PSA)) AND (pulmonary embolism) AND (testosterone) AND (testosterone therapy))"}
{"candidate_id": "LLM02144", "doc_id": "NCT03025620_exc", "case_bucket": "other", "source_criterion": "Patients unable to understand the objectives of the dietary intervention Patients in paliative care Patients receiving supplement diets", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02145", "doc_id": "NCT03472495_exc", "case_bucket": "or", "source_criterion": "Limited English proficiency (LEP) Pregnant Prisoners Wolff Parkinson White syndrome Administration of electrical or chemical cardioversion before screening Administration of other antiarrhythmics for acute heart rate control (excluding adenosine) History of allergy or idiosyncratic reaction to diltiazem Unable to take oral medications Heart rate <60 beats/min", "candidate_expression": "((Heart rate <60 beats/min) AND (LEP) AND (Limited English proficiency) AND (Pregnant) AND (Prisoners) AND (Unable to take) AND (Wolff Parkinson White syndrome) AND (antiarrhythmics) AND (diltiazem) AND (heart rate control acute) AND (oral medications) AND NOT (adenosine) AND ((allergy) OR (idiosyncratic reaction)) AND ((chemical cardioversion) OR (electrical cardioversion)))"}
{"candidate_id": "LLM02146", "doc_id": "NCT02553226_inc", "case_bucket": "other", "source_criterion": "Women stimulated with Syntocinon® infusion for induction of labour (with or without cervical priming by prostaglandin)", "candidate_expression": "((Syntocinon®) AND (Syntocinon® infusion) AND (Women) AND (cervical priming) AND (induction of labour) AND (prostaglandin))"}
{"candidate_id": "LLM02147", "doc_id": "NCT02527512_exc", "case_bucket": "or", "source_criterion": "Documented renal failure documented allergy to iodine or shellfish previous spine fusion surgery undergoing elective posterior spine single-level instrumentation surgery undergoing anterior spine multi-level instrumentation surgery current antibiotic use.", "candidate_expression": "((allergy) AND (anterior spine) AND (antibiotic use) AND (current) AND (elective) AND (iodine) AND (multi-level instrumentation surgery) AND (posterior spine) AND (previous) AND (renal failure) AND (shellfish) AND (single-level instrumentation surgery) AND (spine fusion surgery) AND (undergoing))"}
{"candidate_id": "LLM02148", "doc_id": "NCT02584140_inc", "case_bucket": "or", "source_criterion": "Female at birth and identifies as female gender Age 18 years or older Able to understand and provide consent in English or Spanish HIV negative by 4th generation test (Ag/Ab test) or combination of enzymeimmunoassay (EIA) and HIV RNA Creatinine clearance = 60 ml/min (via Cockcroft-Gault formula) Condomless sex in the last 3 months with one or more male partners of unknown HIV status known to be at substantial risk of HIV infection (IDU, bisexual, sex for goods, recently incarcerated, from a country with HIV prevalence >1%, interpersonal Partner Violence); STI (rectal or vaginal gonorrhea or syphilis) diagnosis during the last 6 months. Previous post-exposure prophylaxis (PEP) use during the last 12 months. Has at least one HIV-infected sexual partner for =4 weeks. Sex for exchange of money, goods or services", "candidate_expression": "((Able to understand and provide consent in English or Spanish) AND (Ag/Ab test) AND (Age 18 years or older) AND (Cockcroft-Gault formula) AND (Condomless sex in the last 3 months) AND (Creatinine clearance = 60 ml/min) AND (EIA) AND (Female at birth) AND (HIV 4th generation test negative) AND (HIV RNA) AND (HIV infection) AND (HIV-infected) AND (IDU) AND (PEP) AND (STI during the last 6 months) AND (Sex for exchange of money, goods or services) AND (bisexual) AND (enzymeimmunoassay) AND (from a country with HIV prevalence >1%) AND (gender female) AND (interpersonal Partner Violence) AND (male partners one or more) AND (post-exposure prophylaxis use during the last 12 months) AND (recently incarcerated) AND (sex for goods) AND (sexual partner at least one =4 weeks) AND (unknown HIV status substantial risk of HIV infection) AND ((rectal gonorrhea) OR (syphilis) OR (vaginal gonorrhea)))"}
{"candidate_id": "LLM02149", "doc_id": "NCT02464865_inc", "case_bucket": "other", "source_criterion": "obese : weight for height > median + 3 standard deviations simple obesity", "candidate_expression": "((> median + 3 standard deviations) AND (obese) AND (simple obesity) AND (weight for height))"}
{"candidate_id": "LLM02150", "doc_id": "NCT01991743_inc", "case_bucket": "other", "source_criterion": "Healthy patients age 18 and older Breech presentation Singleton gestation .scheduled for ECV desiring CSE.", "candidate_expression": "((Breech presentation) AND (CSE desiring) AND (ECV scheduled for) AND (Healthy) AND (Singleton gestation) AND (age 18 and older))"}
```
