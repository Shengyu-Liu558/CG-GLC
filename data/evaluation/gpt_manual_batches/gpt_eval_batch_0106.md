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
{"candidate_id": "LLM02626", "doc_id": "NCT03329456_inc", "case_bucket": "other", "source_criterion": ". Inclusion criteria are American Society of Anesthesiologists (ASA) physical status I-III, age between 18 and 70 years and body mass index (BMI) between 20 and 35 kg/m2.", "candidate_expression": "((ASA) AND (American Society of Anesthesiologists physical status I-III) AND (BMI) AND (age between 18 and 70 years) AND (body mass index between 20 and 35 kg/m2))"}
{"candidate_id": "LLM02627", "doc_id": "NCT03506477_exc", "case_bucket": "or", "source_criterion": "Form of diagnosed psoriasis other than chronic plaque psoriasis (i.e. guttate, erythrodermic, pustular) Diagnosis of other active, ongoing skin diseases or skin infections that may interfere with examination of psoriasis lesions Ongoing use of other psoriasis treatment including but not limited to topical or systemic corticosteroids, other topical medications (i.e. coal tar), oral or biologic medications for the treatment of psoriasis, and UV therapy. The following washout periods will be required: 2 weeks for topical therapy; 2 weeks for phototherapy; 12 weeks for biologic or targeted therapies; 4 weeks for other systemic therapies Use of oral estrogen therapy, excluding oral contraceptive pills Women who are pregnant, nursing, or of child-bearing potential who are unwilling to use appropriate method(s) of contraception. Patients unwilling to limit exposure to UV light Current significant medical problems that, in the discretion of the investigator, would put the patient at significant risk Patients with disorders of calcium metabolism and/or hypercalcemia Use of any investigational drug within 4 weeks prior to randomization, or 5 pharmacokinetic/pharmacodynamics half-lives, if known (whichever is longer) History of allergy to any component of the IP", "candidate_expression": "((Ongoing) AND (Use of any investigational drug within 4 weeks prior to randomization, or 5 pharmacokinetic/pharmacodynamics half-lives, if known (whichever is longer)) AND (Women who are pregnant, nursing, or of child-bearing potential who are unwilling to use appropriate method(s) of contraception.) AND (active) AND (allergy) AND (any component of the IP) AND (chronic plaque psoriasis) AND (coal tar) AND (excluding) AND (limit exposure to UV light) AND (ongoing) AND (oral contraceptive pills) AND (oral estrogen therapy) AND (other than) AND (psoriasis) AND (treatment) AND (unwilling) AND ((skin diseases) OR (skin infections)) AND ((UV therapy) OR (biologic medications) OR (oral medications) OR (systemic corticosteroids) OR (topical corticosteroids) OR (topical medications)) AND ((disorders of calcium metabolism) OR (hypercalcemia)) AND ((erythrodermic) OR (guttate) OR (pustular)))"}
{"candidate_id": "LLM02628", "doc_id": "NCT02256956_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02629", "doc_id": "NCT02269137_inc", "case_bucket": "or", "source_criterion": "30 min or more of (1) continuous clinical seizure activities or (2) recurrent seizure activities without recovery(returning to baseline)between seizures; clinical data is complete.", "candidate_expression": "((30 min or more) AND (seizure recurrent) AND ((seizure continuous) OR (without recovery)))"}
{"candidate_id": "LLM02630", "doc_id": "NCT02984475_exc", "case_bucket": "or", "source_criterion": "Patients with renal impairment (serum creatinine more than twice the upper limit of normal). Patients with heart failure. Patients with sepsis or active infection. Patients with diabetes mellitus (either primary or secondary to thalassemia). regular consumption of medication with potential hepatotoxicity. regular herbal medicine or antioxidant supplementation. patients with gastrointestinal conditions preventing adsorption of oral medication.", "candidate_expression": "((active infection) AND (antioxidant supplementation) AND (diabetes mellitus primary secondary to thalassemia) AND (heart failure) AND (hepatotoxicity) AND (herbal medicine) AND (medication) AND (renal impairment) AND (sepsis) AND (serum creatinine more than twice the upper limit of normal))"}
{"candidate_id": "LLM02631", "doc_id": "NCT00728156_exc", "case_bucket": "or", "source_criterion": "Contraindication to Clopidogrel Smoking (current smokers and patients who quit smoking less than six months) Malignancy(diagnosed or under investigation) Haematological disorders (Anaemia, malignancy, bleeding disorders) Women of child-bearing potential Use of corticosteroids/other antithrombotic agents(warfarin) Chronic liver disease (Cirrhosis, malignancy and patients with more than twice the upper limit of liver function tests) Unable to consent. Use of other investigational study drugs within 1 year prior to study entry Previous participation in this study", "candidate_expression": "((Anaemia) AND (Chronic liver disease) AND (Cirrhosis) AND (Clopidogrel) AND (Contraindication) AND (Haematological disorders) AND (Malignancy) AND (Previous) AND (Smoking) AND (Unable to consent.) AND (Women) AND (antithrombotic agents) AND (bleeding disorders) AND (child-bearing potential) AND (corticosteroids) AND (current) AND (diagnosed) AND (investigational study drugs) AND (less than six months) AND (liver function tests) AND (malignancy) AND (more than twice the upper limit) AND (participation in this study) AND (quit smoking) AND (smokers) AND (under investigation) AND (warfarin) AND (within 1 year prior to study entry))"}
{"candidate_id": "LLM02632", "doc_id": "NCT03352869_exc", "case_bucket": "or", "source_criterion": "Except for serious complications (cardiovascular events and recent significant liver, kidney or lung disease within 3 months) high blood pressure (>160/100mmHg) active infection secondary diabetes pregnancy alcohol abuse allergic to GLP-1 receptor agonist", "candidate_expression": "((>160/100mmHg) AND (GLP-1 receptor agonist) AND (active infection) AND (alcohol abuse) AND (allergic) AND (blood pressure) AND (cardiovascular events) AND (diabetes) AND (disease kidney) AND (disease liver) AND (high blood pressure) AND (lung disease) AND (pregnancy) AND (secondary) AND (serious complications) AND (significant) AND (within 3 months))"}
{"candidate_id": "LLM02633", "doc_id": "NCT02969187_inc", "case_bucket": "or", "source_criterion": "Fulfills NIH criteria for bariatric surgery Planned operation of laparoscopic Roux-en Y gastric bypass (LRYGB) or laparoscopic sleeve gastrectomy (LSG) as primary bariatric procedure", "candidate_expression": "((Fulfills) AND (NIH criteria) AND (bariatric surgery) AND (primary) AND ((laparoscopic Roux-en Y gastric bypass (LRYGB)) OR (laparoscopic sleeve gastrectomy (LSG))))"}
{"candidate_id": "LLM02634", "doc_id": "NCT02334631_inc", "case_bucket": "other", "source_criterion": "Patients undergoing small bowel video capsule endoscopy", "candidate_expression": "(small bowel video capsule endoscopy)"}
{"candidate_id": "LLM02635", "doc_id": "NCT00425789_exc", "case_bucket": "or", "source_criterion": "Patients will be excluded if they have known middle ear disease, chronic lung disease or claustrophobia", "candidate_expression": "((chronic lung disease) AND (claustrophobia) AND (middle ear disease))"}
{"candidate_id": "LLM02636", "doc_id": "NCT01581749_inc", "case_bucket": "or", "source_criterion": "histologically proven prostate adenocarcinoma within 1 year of enrollment Low risk: Gleason <or=6 & PSA <or=10 & Clinical Stage T1b-T2a,Nx or N0, Mx or M0 Intermediate risk:Gleason <or=6 & PSA<or=10 & Clinical Stage T2b OR Gleason=7 & PSA<or=10 & Clinical Stage T1b-T2b OR Gleason <or=6 & PSA > 10 & < or =20 & Clinical Stage T1b- T2b, Nx or NO, Mx or M0 ECOG Performance Status 0-1 No prior prostate radiation or other definitive therapy", "candidate_expression": "((Clinical Stage T1b- T2b) AND (Clinical Stage T1b-T2a) AND (Clinical Stage T1b-T2b) AND (Clinical Stage T2b) AND (ECOG Performance Status 0-1) AND (Gleason <or=6) AND (Gleason =7) AND (Intermediate risk) AND (Low risk) AND (PSA <or=10) AND (PSA > 10 & < or =20) AND (prostate adenocarcinoma histologically proven within 1 year of enrollment) AND ((M0) OR (Mx)) AND ((N0) OR (Nx)) AND ((NO) OR (Nx)) AND ((definitive therapy) OR (prostate radiation)))"}
{"candidate_id": "LLM02637", "doc_id": "NCT02301962_exc", "case_bucket": "or", "source_criterion": "History or known presence of central nervous system metastases. History of another malignancy except: Malignancy treated with curative intent and with no known active disease present for >=5 years prior to enrolment and felt to be at low risk for recurrence by the treating physician; Adequately treated non-melanomatous skin cancer or lentigo maligna without evidence of disease; Adequately treated cervical carcinoma in situ without evidence of disease; Prostatic intraepithelial neoplasia without evidence of prostate cancer. Known immediate or delayed hypersensitivity reaction or idiosyncrasy to drugs chemically related to panitumumab or excipients that contraindicates their participation. Prior anti-epidermal growth factor receptor (EGFr) antibody therapy (e.g., panitumumab or cetuximab) or treatment with small molecule EGFr inhibitors (e.g., gefitinib, erlotinib, lapatinib). Antitumor therapy (e.g., chemotherapy, hormonal therapy, immunotherapy, antibody therapy, radiotherapy), or investigational agent or therapy <=30 days before first dose of study treatment or not recovered from any acute toxicity. Other investigational procedure <=30 days before study entry. History of interstitial lung disease (ILD) e.g., interstitial pneumonitis, pulmonary fibrosis or evidence of ILD on baseline chest computer tomography. Subject previously enrolled to this study. History of keratitis, ulcerative keratitis or severe dry eye. Major surgery (e.g., requiring general anesthesia) <=30 days before first dose of study treatment. Subjects must have recovered from any surgery related toxicities. Minor surgical procedure (e.g., open biopsy) <=7 days before first dose of study treatment, or not yet recovered from prior minor surgery Note: uncomplicated placement of vascular access device, fine needle aspiration, thoracocentesis or paracentesis >=3 days prior to first dose of study treatment is acceptable. Clinically significant cardiovascular disease (including myocardial infarction, unstable angina, symptomatic congestive heart failure, serious uncontrolled cardiac arrhythmia) <=6 months prior to enrolment. History of any medical or psychiatric condition or laboratory abnormality that in the opinion of the investigator may increase the risk associated with the study participation or investigational product administration, compliance with the study procedures or may interfere with the interpretation of the results. Unstable pulmonary embolism, deep vein thrombosis, or other significant arterial/venous thromboembolic event <=30 days before first dose of study treatment. If on anticoagulation, subject must be on stable therapeutic dose prior to first dose of study treatment. Subject who is pregnant or breast feeding, or planning to become pregnant during treatment and within 2 months after the discontinuation of study treatment. Known positive test(s) for human immunodeficiency virus infection (testing is not required in the absence of clinical suspicion). Active infection requiring systemic treatment or any uncontrolled infection <=14 days prior to first dose of study treatment (with the exception of uncomplicated urinary tract infection or upper respiratory tract infection). Subject has any kind of disorder that compromises the ability of the subject to give written informed consent and/or to comply with study procedures or is unwilling or unable to comply with study requirements.", "candidate_expression": "((EGFr) AND (History of any medical or psychiatric condition or laboratory abnormality that in the opinion of the investigator may increase the risk associated with the study participation or investigational product administration, compliance with the study procedures or may interfere with the interpretation of the results.) AND (ILD) AND (ILD evidence of) AND (Major surgery <=30 days before first dose of study treatment) AND (Subject has any kind of disorder that compromises the ability of the subject to give written informed consent and/or to comply with study procedures or is unwilling or unable to comply with study requirements.) AND (anticoagulation therapeutic dose prior to first dose of study treatment first dose of study treatment) AND (central nervous system metastases) AND (during treatment treatment) AND (general anesthesia) AND (idiosyncrasy) AND (interstitial lung disease) AND (investigational procedure Other <=30 days before study entry) AND (malignancy another) AND (minor surgery prior) AND (not recovered from any acute toxicity) AND (open biopsy) AND (recurrence felt to be at low risk) AND (systemic treatment) AND (test(s) for human immunodeficiency virus infection positive) AND (treated Adequately) AND (treated with curative intent) AND (within 2 months after the discontinuation of study treatment the discontinuation of study treatment) AND NOT (evidence of disease) AND NOT (disease evidence of) AND NOT (prostate cancer evidence of) AND NOT (active disease for >=5 years prior to enrolment) AND ((deep vein thrombosis) OR (pulmonary embolism Unstable)) AND ((arterial thromboembolic event) OR (venous thromboembolic event)) AND ((become pregnant planning to) OR (breast feeding) OR (pregnant)) AND ((infection Active) OR (uncontrolled infection any)) AND ((upper respiratory tract infection uncomplicated) OR (urinary tract infection uncomplicated)) AND ((lentigo maligna) OR (non-melanomatous skin cancer)) AND ((Prostatic intraepithelial neoplasia) OR (cervical carcinoma in situ)) AND ((delayed hypersensitivity reaction) OR (immediate hypersensitivity reaction)) AND ((drugs chemically related to panitumumab) OR (drugs chemically related to panitumumab excipients)) AND ((anti-epidermal growth factor receptor antibody therapy) OR (treatment with small molecule EGFr inhibitors)) AND ((cetuximab) OR (panitumumab)) AND ((Malignancy) OR (treated Adequately)) AND ((erlotinib) OR (gefitinib) OR (lapatinib)) AND ((Antitumor therapy) OR (investigational agent) OR (therapy)) AND ((antibody therapy) OR (chemotherapy) OR (hormonal therapy) OR (immunotherapy) OR (radiotherapy)) AND ((chest computer tomography baseline) OR (interstitial pneumonitis) OR (pulmonary fibrosis)) AND ((dry eye severe) OR (keratitis) OR (ulcerative keratitis)) AND ((Minor surgical procedure <=7 days before first dose of study treatment) OR NOT (recovered)) AND ((Clinically significant) OR (cardiovascular disease)) AND ((cardiac arrhythmia serious uncontrolled) OR (congestive heart failure symptomatic) OR (myocardial infarction) OR (unstable angina)))"}
{"candidate_id": "LLM02638", "doc_id": "NCT02904785_inc", "case_bucket": "or", "source_criterion": "Clinical and radiologic diagnosis of primary knee osteoarthritis (Kellgren & Lawrence I, II or III); Capability to understand the Informed Consent Form; Chronic pain for at least 3 months prior to inclusion, measured by VAS. (VAS 4 or above); Absence of skin injures, infections or tumor in the target knee; Availability to comply with the visits.", "candidate_expression": "((Availability to comply with the visits) AND (Capability to understand the Informed Consent Form;) AND (Chronic pain at least 3 months prior measured by VAS) AND (Kellgren & Lawrence I, II or III) AND (VAS) AND (VAS 4 or above) AND (primary knee osteoarthritis Clinical diagnosis radiologic diagnosis) AND ((infections target knee) OR (tumor target knee) OR NOT (skin injures)))"}
{"candidate_id": "LLM02639", "doc_id": "NCT01991743_exc", "case_bucket": "or", "source_criterion": "Refusal Contraindication to neuraxial (coagulopathy, anticoagulant use, local infection, sepsis etc) .Rupture of membranes. Drop-out: Patients may choose to drop-out of the study at any time. The physicians involved in this study may choose to end a patient's involvement in the study at their discretion.", "candidate_expression": "((Contraindication) AND (Rupture of membranes) AND (neuraxial) AND ((anticoagulant) OR (coagulopathy) OR (local infection) OR (sepsis)))"}
{"candidate_id": "LLM02640", "doc_id": "NCT02488057_inc", "case_bucket": "other", "source_criterion": "Mexican-american Female BMI 30-42 willingness to complete protocol pre-diabetic English or Spanish literate", "candidate_expression": "((30-42) AND (BMI) AND (Female) AND (Mexican-american) AND (pre-diabetic) AND (willingness to complete protocol))"}
{"candidate_id": "LLM02641", "doc_id": "NCT02992028_exc", "case_bucket": "or", "source_criterion": "age <45 or >80 allergies to medications used in the study history of renal diseases, a coagulation abnormality, a hepatic disease, or drug abuse definite radiographic evidence of osteoarthritis of the glenohumeral joint inflammatory arthritis including rheumatoid arthritis a history of acute trauma systemic conditions associated with chronic pain a history of infection an inability to understand the questionnaires", "candidate_expression": "((acute trauma) AND (age <45 or >80) AND (allergies) AND (chronic pain) AND (history) AND (inability to understand the questionnaires) AND (infection history) AND (inflammatory arthritis) AND (medications used in the study) AND (osteoarthritis radiographic evidence glenohumeral joint) AND (radiographic) AND (rheumatoid arthritis) AND (systemic conditions associated with chronic pain) AND ((coagulation abnormality) OR (drug abuse) OR (hepatic disease) OR (renal diseases)))"}
{"candidate_id": "LLM02642", "doc_id": "NCT03648021_inc", "case_bucket": "or", "source_criterion": "18-year or older patients Patient hospitalized in neuro-critical care for: Arachnoid hemorrhage Intra parenchymatous hematoma stroke Acute brain Severe injury Post-operative complication of an act of neurosurgery or programmed neuroradiology Sedation and mechanical ventilation planned > 2 days Monitoring of intracranial temperature and pressure by intraparenchymal sensor (Sophysa®) Brain temperature > 38.5°C for more than 30 minutes", "candidate_expression": "((18-year or older) AND (> 2 days) AND (> 38.5°C) AND (Acute brain Severe injury) AND (Arachnoid hemorrhage) AND (Brain temperature) AND (Intra parenchymatous) AND (Post-operative complication) AND (Sedation) AND (Sophysa®) AND (for more than 30 minutes) AND (hematoma) AND (hospitalized) AND (intracranial pressure) AND (intracranial temperature) AND (intraparenchymal sensor) AND (mechanical ventilation) AND (neuro-critical care) AND (neuroradiology) AND (neurosurgery) AND (of an act of neurosurgery) AND (of an act of programmed neuroradiology) AND (old) AND (planned) AND (stroke))"}
{"candidate_id": "LLM02643", "doc_id": "NCT03318393_exc", "case_bucket": "or", "source_criterion": "Patients with known or suspected heparin induced thrombocytopenia prior to consent Patients with hepatic failure defined as coagulopathy with elevated transaminases more than three times normal values Patients with plan to decannulate from ECMO within 48 hours Known or suspected pregnant women Previous enrollment in this study Primary language spoken that is not English or Spanish", "candidate_expression": "((Previous enrollment in this study) AND (coagulopathy) AND (consent) AND (decannulate from ECMO) AND (elevated more than three times normal values) AND (heparin) AND (heparin induced) AND (hepatic failure) AND (pregnant) AND (prior to consent) AND (thrombocytopenia) AND (transaminases) AND (within 48 hours) AND (women) AND ((Known) OR (suspected)) AND ((known) OR (suspected)))"}
{"candidate_id": "LLM02644", "doc_id": "NCT02283996_exc", "case_bucket": "other", "source_criterion": "Non-English speaking patients Pregnant women (women of childbearing potential will be advised to undergo regular pregnancy testing) Patients who had previously undergone operative therapy for the condition", "candidate_expression": "((Patients who had previously undergone operative therapy for the condition) AND (Pregnant women (women of childbearing potential will be advised to undergo regular pregnancy testing)))"}
{"candidate_id": "LLM02645", "doc_id": "NCT00480129_inc", "case_bucket": "or", "source_criterion": "Clinical diagnosis of allergic rhinitis based on sneeze attacks, runny/blocked/itchy nose in the absence of a common cold during the previous 12 months. History of positive skin prick test or blood radio-allergosorbent test (RAST) to grass and/or ragweed pollen", "candidate_expression": "((allergic rhinitis) AND (blocked nose) AND (blood radio-allergosorbent test (RAST) positive grass ragweed pollen) AND (itchy nose) AND (runny nose) AND (skin prick test positive) AND (sneeze attacks) AND NOT (common cold during the previous 12 months))"}
{"candidate_id": "LLM02646", "doc_id": "NCT02399033_inc", "case_bucket": "or", "source_criterion": "Age: 20-70 years old; Gender: male or female; clinical or pathological diagnosis of hepatocellular carcinoma (HCC) in previously untreated patients; The expected survival> 3 months; Child-Pugh grade in A-level; KPS score with 50-100 points; BCLC stage of 0-B; conform to the indications of hepatectomy; Viable tumor resection confirmed by two highly qualified surgical doctors; No other surgical contraindications. women in the reproductive period must be completely contraception in 28 days before treatment, during the treatment process and in 28 days after treatment; Men must be completely contraception and prohibited donation and sperm donation during the treatment process and in 28 days after treatment; All patients must be prohibited donation during the treatment process and in 28 days after treatment; In addition to the subjects, prohibitting other people taking this product. patients have a good understanding and could coordinate with investigators for the trial. Patients enrolled in the trial should sign an informed consent form, to indicate understanding the purpose and procedure of the trial, and patients volunteering to participate in the trial.", "candidate_expression": "((Age 20-70 years old) AND (BCLC stage 0-B) AND (Child-Pugh grade A) AND (Gender male female) AND (HCC) AND (KPS score 50-100 points) AND (Men in 28 days after treatment) AND (Patients enrolled in the trial should sign an informed consent form, to indicate understanding the purpose and procedure of the trial, and patients volunteering to participate in the trial) AND (Viable tumor resection confirmed by two highly qualified surgical doctors) AND (contraception) AND (contraception during the treatment process in 28 days before treatment) AND (expected survival > 3 months) AND (hepatectomy) AND (hepatocellular carcinoma clinical or pathological diagnosis untreated) AND (indications of hepatectomy) AND (patients have a good understanding and could coordinate with investigators for the trial) AND (reproductive period) AND (women) AND NOT (other surgical contraindications) AND NOT (sperm donation during the treatment process in 28 days after treatment) AND NOT (donation) AND NOT (donation during the treatment process in 28 days after treatmen))"}
{"candidate_id": "LLM02647", "doc_id": "NCT02606565_exc", "case_bucket": "other", "source_criterion": "Newborns with severe congenital anomalies Newborns with infection of the umbilical cord at birth", "candidate_expression": "((Newborns) AND (at birth) AND (infection of the umbilical cord) AND (severe congenital anomalies))"}
{"candidate_id": "LLM02648", "doc_id": "NCT03446885_exc", "case_bucket": "or", "source_criterion": "any medical condition that would contraindicate use of stimulant medication any prior adverse response to lisdexamfetamine dimesylate or other stimulant medication use of concurrent,non-stimulant psychoactive medication diagnosis of schizophrenia or presence of thought disorder symptoms autism spectrum disorder", "candidate_expression": "((adverse response prior) AND (autism spectrum disorder) AND (contraindicate) AND (medical condition) AND (non-stimulant psychoactive medication concurrent) AND (stimulant medication) AND ((schizophrenia) OR (thought disorder symptoms)) AND ((lisdexamfetamine dimesylate) OR (stimulant medication other)))"}
{"candidate_id": "LLM02649", "doc_id": "NCT03389061_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02650", "doc_id": "NCT02735577_exc", "case_bucket": "or", "source_criterion": "Risk of severe alcohol withdrawal (e.g. history of seizures or delirium tremens) Current Moderate or Severe Substance Use Disorder, other than Alcohol, Nicotine or Caffeine Use Disorders Lifetime history of Bipolar Disorder, Schizophrenia or Schizoaffective Disorder Any current psychiatric disorder, other than Alcohol Use Disorder, that, in the judgment of the investigator, will require treatment that will interfere with study participation. Current severe depression (HAM-D >24) or anxiety (HAM-A >24) Significant suicide or violence risk Currently taking any psychotropic medications Legally mandated to participate in treatment History of prior treatment with disulfiram Sufficiently socially unstable as to preclude participation (e.g. homeless) Contraindications to disulfiram treatment (liver disease, kidney disease, cardiac disease, seizure disorder, hypothyroidism, diabetes mellitus, pregnancy or lactation, allergy to disulfiram or thiuran derivatives) Neurological or medical conditions that would interfere with MRI scanning (e.g. history of stroke, seizure, brain tumor, brain infection, traumatic brain injury, multiple sclerosis, dementia, metal device in body, pregnancy, claustrophobia, color blindness, severe hearing impairment, weight>300 lbs., wheelchair-bound) Currently taking medications containing alcohol, metronidazole, isoniazid, paraldehyde, phenytoin, warfarin, or theophylline. Significant alcohol withdrawal (CIWA>8) at screening, after confirming a blood alcohol level of zero.", "candidate_expression": "((>24) AND (>300 lbs.) AND (>8) AND (Alcohol Use Disorder) AND (Alcohol Use Disorders) AND (Bipolar Disorder) AND (CIWA) AND (Caffeine Use Disorders) AND (Contraindications) AND (Current) AND (Currently) AND (HAM-A) AND (HAM-D) AND (History of prior treatment) AND (Lifetime history) AND (MRI scanning) AND (Moderate) AND (Nicotine Use Disorders) AND (Risk of) AND (Schizoaffective Disorder) AND (Schizophrenia) AND (Severe) AND (Significant) AND (Substance Use Disorder) AND (Sufficiently) AND (alcohol) AND (alcohol withdrawal) AND (allergy) AND (anxiety) AND (at screening) AND (blood alcohol level) AND (brain infection) AND (brain tumor) AND (cardiac disease) AND (claustrophobia) AND (color blindness) AND (conditions Neurological) AND (current) AND (delirium tremens) AND (dementia) AND (depression) AND (diabetes mellitus) AND (disulfiram) AND (hearing impairment) AND (history) AND (hypothyroidism) AND (interfere) AND (isoniazid) AND (kidney disease) AND (lactation) AND (liver disease) AND (medical conditions) AND (metal device in body) AND (metronidazole) AND (multiple sclerosis) AND (other than) AND (paraldehyde) AND (phenytoin) AND (pregnancy) AND (psychiatric disorder) AND (psychotropic medications) AND (seizure) AND (seizure disorder) AND (seizures) AND (severe) AND (socially unstable) AND (stroke) AND (suicide risk) AND (theophylline) AND (thiuran derivatives) AND (traumatic brain injury) AND (violence risk) AND (warfarin) AND (weight) AND (wheelchair-bound) AND (zero))"}
```
