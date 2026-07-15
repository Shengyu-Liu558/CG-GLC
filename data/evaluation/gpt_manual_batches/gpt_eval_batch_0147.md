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
{"candidate_id": "LLM03651", "doc_id": "NCT03068897_inc", "case_bucket": "or", "source_criterion": "Present to ED primary for management of LBP, defined as pain originating between the lower border of the scapulae and the upper gluteal folds. Flank pain, that is pain originating from tissues lateral to the paraspinal muscles, will not be included. Musculoskeletal etiology of low back. Patients with non-musculoskeletal etiologies such as urinary tract infection, ovarian cysts, or influenza like illness will be excluded. The primary clinical diagnosis, at the conclusion of the ED visit, must be a diagnosis consistent with non-traumatic, non-radicular, musculoskeletal LBP. Patient is to be discharged home. Patients admitted to the hospital are more likely to be treated with parenteral medication and therefore are not appropriate for this study. Age 18-64 Enrollment will be limited to adults younger than 65 years because of the increased risk of adverse medication effects in the elderly. Non-radicular pain. Patients will be excluded if the pain radiates below the gluteal folds in a radicular pattern. Pain duration <2 weeks (336 hours). Patients with more than two weeks of pain are at increased risk of poor pain and functional outcomes.(9) Prior to the acute attack of LBP, back pain cannot occur more frequently than once per month. Patients with more frequent back pain are at increased risk of poor pain and functional outcomes.(9) Non-traumatic LBP: no substantial and direct trauma to the back within the previous month Functionally impairing back pain: A baseline score of > 5 on the Roland-Morris Disability Questionnaire", "candidate_expression": "((18-64) AND (Age) AND (ED) AND (Flank pain) AND (Functionally impairing) AND (LBP) AND (Musculoskeletal) AND (Non) AND (Non-traumatic) AND (Pain) AND (Present) AND (Prior to the acute attack of LBP) AND (Roland-Morris Disability Questionnaire) AND (acute) AND (acute attack of LBP) AND (adults) AND (adverse effects) AND (attack of LBP) AND (back) AND (back pain) AND (baseline) AND (below the gluteal folds in a radicular pattern) AND (between the lower border of the scapulae and the upper gluteal folds) AND (cannot) AND (direct) AND (duration 336 hours) AND (duration <2 weeks) AND (elderly) AND (etiologies) AND (etiology) AND (excluded) AND (increased risk) AND (influenza like illness) AND (low back) AND (medication) AND (more frequently than once per month) AND (musculoskeletal) AND (no) AND (non) AND (non-radicular) AND (non-traumatic) AND (not) AND (ovarian cysts) AND (pain) AND (radicular) AND (score of > 5) AND (substantial) AND (tissues lateral to the paraspinal muscles) AND (trauma) AND (urinary tract infection) AND (within the previous month) AND (younger than 65 years))"}
{"candidate_id": "LLM03652", "doc_id": "NCT02205502_inc", "case_bucket": "other", "source_criterion": "patients who need suturing for laceration under procedural anesthesia using ketamine", "candidate_expression": "((ketamine) AND (laceration) AND (procedural anesthesia) AND (suturing))"}
{"candidate_id": "LLM03653", "doc_id": "NCT03446885_inc", "case_bucket": "or", "source_criterion": "diagnosis of ADHD parental permission and/or teen consent/assent as appropriate between 16-25 years of age IQ greater than or equal to 70 permit or license to drive ability to read and understand English", "candidate_expression": "((ADHD) AND (IQ greater than or equal to 70) AND (age 16-25 years) AND (parental permission and/or teen consent/assent as appropriate) AND ((license to drive) OR (permit to drive)) AND ((ability to read English) OR (ability to understand English)))"}
{"candidate_id": "LLM03654", "doc_id": "NCT00886158_exc", "case_bucket": "other", "source_criterion": "Lack of consent", "candidate_expression": "(Lack of consent)"}
{"candidate_id": "LLM03655", "doc_id": "NCT01715714_inc", "case_bucket": "or", "source_criterion": "Patients on chronic statin treatment (>30 days) scheduled for isolated CABG, including on- or off-pump or repeat (redo's) revascularisation procedures Stable or unstable angina, including non ST-segment-elevation acute coronary syndrome (NSTE-ACS) Age = 18 years Written informed consent", "candidate_expression": "((= 18 years) AND (>30 days) AND (Age) AND (CABG) AND (NSTE-ACS) AND (chronic) AND (isolated) AND (non ST-segment-elevation acute coronary syndrome) AND (on- or off-pump or repeat) AND (redo's) AND (revascularisation procedures) AND (scheduled) AND (statin) AND (treatment) AND ((Stable angina) OR (unstable angina)))"}
{"candidate_id": "LLM03656", "doc_id": "NCT03025620_inc", "case_bucket": "or", "source_criterion": "Elderly patients over 65 years old exhibiting clinical indices of cardiovascular disease Male or female Subjects who were hospitalized in the Geriatric Unit of the Emile Roux Hospital (AP-HP) MMSE (Mini Mental State Examination)score > or = 15 Supervision available for study medication Able to ingest oral diet", "candidate_expression": "((Able to ingest oral diet) AND (Elderly) AND (Geriatric Unit of the Emile Roux Hospital (AP-HP)) AND (MMSE (Mini Mental State Examination) score > or = 15) AND (Male) AND (female) AND (old over 65 years))"}
{"candidate_id": "LLM03657", "doc_id": "NCT02851303_inc", "case_bucket": "or", "source_criterion": "Born at University of New Mexico Hospital Greater than 34 weeks gestation Primary in-utero drug exposure was opioids other than buprenorphine Maternal or infant urine drug screen positive for methadone and/or opioids on admission", "candidate_expression": "((Born) AND (University of New Mexico Hospital) AND (drug exposure in-utero) AND (gestation Greater than 34 weeks) AND (opioids) AND (urine drug screen positive methadone opioids) AND NOT (buprenorphine Maternal infant))"}
{"candidate_id": "LLM03658", "doc_id": "NCT02430740_exc", "case_bucket": "other", "source_criterion": "polycystic ovaries untreated thyroid pathology hypogonadotropic hypogonadism untreaed hyperprolactinemia study drug hypersensitivity previous OHSS unilateral ovariectomy genital malformation BMI>40", "candidate_expression": "((BMI >40) AND (OHSS previous) AND (genital malformation) AND (hyperprolactinemia untreaed) AND (hypersensitivity) AND (hypogonadotropic hypogonadism) AND (ovariectomy unilateral) AND (polycystic ovaries) AND (study drug) AND (thyroid pathology untreated))"}
{"candidate_id": "LLM03659", "doc_id": "NCT02974660_inc", "case_bucket": "other", "source_criterion": "patients who underwent successful TAVI with any approved TAVI device via transfemoral access with use of any of the approved vascular closure devices provided written informed consent", "candidate_expression": "((TAVI device) AND (TAVI successful) AND (provided written informed consent) AND (transfemoral access) AND (vascular closure devices))"}
{"candidate_id": "LLM03660", "doc_id": "NCT03228017_inc", "case_bucket": "or", "source_criterion": "Subjects with a history of moderate to severe psoriatic disease Group 2: Healthy subjects without known psoriatic disease or cardiovascular disease", "candidate_expression": "((Healthy) AND (cardiovascular disease) AND (history) AND (moderate) AND (psoriatic disease) AND (severe) AND (without))"}
{"candidate_id": "LLM03661", "doc_id": "NCT02042287_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03662", "doc_id": "NCT01717911_inc", "case_bucket": "other", "source_criterion": "Recently diagnosed type 2 diabetic patients. Fasting plasma glucose between 200-300 mg/dl (A1C level between 7% and 10%). Those who age between 30 and 80 years old and can inject insulin by themselves.", "candidate_expression": "((A1C level between 7% and 10%) AND (Fasting plasma glucose between 200-300 mg/dl) AND (age between 30 and 80 years old) AND (inject insulin can) AND (type 2 diabetic Recently diagnosed))"}
{"candidate_id": "LLM03663", "doc_id": "NCT02301962_exc", "case_bucket": "or", "source_criterion": "History or known presence of central nervous system metastases. History of another malignancy except: Malignancy treated with curative intent and with no known active disease present for >=5 years prior to enrolment and felt to be at low risk for recurrence by the treating physician; Adequately treated non-melanomatous skin cancer or lentigo maligna without evidence of disease; Adequately treated cervical carcinoma in situ without evidence of disease; Prostatic intraepithelial neoplasia without evidence of prostate cancer. Known immediate or delayed hypersensitivity reaction or idiosyncrasy to drugs chemically related to panitumumab or excipients that contraindicates their participation. Prior anti-epidermal growth factor receptor (EGFr) antibody therapy (e.g., panitumumab or cetuximab) or treatment with small molecule EGFr inhibitors (e.g., gefitinib, erlotinib, lapatinib). Antitumor therapy (e.g., chemotherapy, hormonal therapy, immunotherapy, antibody therapy, radiotherapy), or investigational agent or therapy <=30 days before first dose of study treatment or not recovered from any acute toxicity. Other investigational procedure <=30 days before study entry. History of interstitial lung disease (ILD) e.g., interstitial pneumonitis, pulmonary fibrosis or evidence of ILD on baseline chest computer tomography. Subject previously enrolled to this study. History of keratitis, ulcerative keratitis or severe dry eye. Major surgery (e.g., requiring general anesthesia) <=30 days before first dose of study treatment. Subjects must have recovered from any surgery related toxicities. Minor surgical procedure (e.g., open biopsy) <=7 days before first dose of study treatment, or not yet recovered from prior minor surgery Note: uncomplicated placement of vascular access device, fine needle aspiration, thoracocentesis or paracentesis >=3 days prior to first dose of study treatment is acceptable. Clinically significant cardiovascular disease (including myocardial infarction, unstable angina, symptomatic congestive heart failure, serious uncontrolled cardiac arrhythmia) <=6 months prior to enrolment. History of any medical or psychiatric condition or laboratory abnormality that in the opinion of the investigator may increase the risk associated with the study participation or investigational product administration, compliance with the study procedures or may interfere with the interpretation of the results. Unstable pulmonary embolism, deep vein thrombosis, or other significant arterial/venous thromboembolic event <=30 days before first dose of study treatment. If on anticoagulation, subject must be on stable therapeutic dose prior to first dose of study treatment. Subject who is pregnant or breast feeding, or planning to become pregnant during treatment and within 2 months after the discontinuation of study treatment. Known positive test(s) for human immunodeficiency virus infection (testing is not required in the absence of clinical suspicion). Active infection requiring systemic treatment or any uncontrolled infection <=14 days prior to first dose of study treatment (with the exception of uncomplicated urinary tract infection or upper respiratory tract infection). Subject has any kind of disorder that compromises the ability of the subject to give written informed consent and/or to comply with study procedures or is unwilling or unable to comply with study requirements.", "candidate_expression": "((Antitumor therapy) AND (EGFr) AND (History of any medical or psychiatric condition or laboratory abnormality that in the opinion of the investigator may increase the risk associated with the study participation or investigational product administration, compliance with the study procedures or may interfere with the interpretation of the results.) AND (ILD) AND (ILD evidence of) AND (Major surgery <=30 days before first dose of study treatment) AND (Malignancy) AND (Minor surgical procedure <=7 days before first dose of study treatment) AND (Prostatic intraepithelial neoplasia) AND (Subject has any kind of disorder that compromises the ability of the subject to give written informed consent and/or to comply with study procedures or is unwilling or unable to comply with study requirements.) AND (anti-epidermal growth factor receptor antibody therapy) AND (antibody therapy) AND (anticoagulation therapeutic dose prior to first dose of study treatment first dose of study treatment) AND (arterial thromboembolic event) AND (become pregnant planning to during treatment within 2 months after the discontinuation of study treatment) AND (breast feeding) AND (cardiac arrhythmia serious uncontrolled) AND (cardiovascular disease Clinically significant) AND (central nervous system metastases) AND (cervical carcinoma in situ) AND (cetuximab) AND (chemotherapy) AND (chest computer tomography baseline) AND (congestive heart failure symptomatic) AND (deep vein thrombosis) AND (delayed hypersensitivity reaction) AND (drugs chemically related to panitumumab) AND (drugs chemically related to panitumumab excipients) AND (dry eye severe) AND (erlotinib) AND (gefitinib) AND (general anesthesia) AND (hormonal therapy) AND (idiosyncrasy) AND (immediate hypersensitivity reaction) AND (immunotherapy) AND (infection Active) AND (interstitial lung disease) AND (interstitial pneumonitis) AND (investigational agent) AND (investigational procedure Other <=30 days before study entry) AND (keratitis) AND (lapatinib) AND (lentigo maligna) AND (malignancy another) AND (minor surgery prior) AND (myocardial infarction) AND (non-melanomatous skin cancer) AND (not recovered from any acute toxicity) AND (open biopsy) AND (panitumumab) AND (pregnant) AND (pulmonary embolism Unstable) AND (pulmonary fibrosis) AND (radiotherapy) AND (recurrence felt to be at low risk) AND (systemic treatment) AND (test(s) for human immunodeficiency virus infection positive) AND (therapy) AND (treated Adequately) AND (treated with curative intent) AND (treatment with small molecule EGFr inhibitors) AND (ulcerative keratitis) AND (uncontrolled infection any) AND (unstable angina) AND (upper respiratory tract infection uncomplicated) AND (urinary tract infection uncomplicated) AND (venous thromboembolic event) AND NOT (evidence of disease) AND NOT (disease evidence of) AND NOT (prostate cancer evidence of) AND NOT (active disease for >=5 years prior to enrolment) AND NOT (recovered))"}
{"candidate_id": "LLM03664", "doc_id": "NCT03388840_exc", "case_bucket": "or", "source_criterion": "Patients with Non-androgenetic causes of hair loss. Female patients with androgenetic alopecia. Patients who received anti-hair loss treatment within the past six months. Patients with history of bleeding disorders or on anticoagulant therapy. Patients with history of chronic liver disease, cancer or connective tissue disorders. Patients with current scalp infection.", "candidate_expression": "((Female) AND (Non-androgenetic causes of hair loss) AND (androgenetic alopecia) AND (anti-hair loss treatment within the past six months) AND (scalp infection current) AND ((anticoagulant therapy) OR (bleeding disorders)) AND ((cancer) OR (chronic liver disease) OR (connective tissue disorders)))"}
{"candidate_id": "LLM03665", "doc_id": "NCT02112734_inc", "case_bucket": "other", "source_criterion": "Healthy, term, breastfeeding infants who will be predominately breastfed for at least 6-months. This will be determined by answering yes/no to question 'do you intend to breastfeed until your infant is at least 6 months of age.'", "candidate_expression": "((Healthy) AND (breastfeeding) AND (for at least 6-months) AND (infants) AND (predominately breastfed) AND (term))"}
{"candidate_id": "LLM03666", "doc_id": "NCT02704754_inc", "case_bucket": "other", "source_criterion": "Physically healthy adults age 18-55 who meet DSM-5 criteria for insomnia and Criterion A (exposure to a traumatic event) for PTSD. The index trauma must have occurred within the past 5 years and at least 3 months before enrolling, and insomnia symptoms must have started or worsened after the exposure to the index trauma", "candidate_expression": "((18-55) AND (Criterion A) AND (DSM-5) AND (PTSD) AND (adults) AND (age) AND (healthy) AND (index) AND (insomnia) AND (the past 5 years and at least 3 months) AND (trauma))"}
{"candidate_id": "LLM03667", "doc_id": "NCT02062489_exc", "case_bucket": "or", "source_criterion": "The patients have other cancers at the same time or have the history of other cancers except controlled skin basal cell carcinoma or skin squamous cell carcinoma or carcinoma in situ of cervix uterus; The patients have active infections that were not suitable for chemotherapy; The patients have severe non-cancerous diseases. The patients have history of neoadjuvant hormone therapy. The patients have bilateral breast cancers or DCIS or metastatic breast cancers. The patients are undergoing current administration of anti-cancer therapies, or are attending other clinical trials. The patients are pregnant or lactational, or they refuse to practice contraception during the whole trial. The patients are in some special conditions that they can't understand the written informed consent, such as they are demented or hawkish. The patients have allergic history or contraindication of tamoxifen.", "candidate_expression": "((DCIS) AND (The patients are in some special conditions that they can't understand the written informed consent, such as they are demented or hawkish.) AND (allergic) AND (anti-cancer therapies) AND (attending other clinical trials) AND (bilateral breast cancers) AND (carcinoma in situ of cervix uterus) AND (contraindication) AND (controlled skin basal cell carcinoma) AND (infections active suitable for chemotherapy) AND (lactational) AND (metastatic breast cancers) AND (neoadjuvant hormone therapy) AND (non-cancerous diseases severe) AND (other cancers) AND (other cancers at the same time) AND (pregnant) AND (skin squamous cell carcinoma) AND (tamoxifen) AND NOT (contraception during the whole trial))"}
{"candidate_id": "LLM03668", "doc_id": "NCT02369211_exc", "case_bucket": "or", "source_criterion": "Chronic opiate use Liver disease (known history of hepatitis B or C, cirrhosis, nonalcoholic steatohepatitis, history of alcoholism, ALT/AST greater than 3 times upper limit of normal in the past 3 months) Allergy/hypersensitivity to acetaminophen Patients with baseline dementia Chronic diathesis Chronic kidney disease", "candidate_expression": "((ALT/AST greater than 3 times upper limit of normal in the past 3 months) AND (Allergy) AND (Liver disease) AND (acetaminophen) AND (alcoholism history) AND (cirrhosis) AND (dementia baseline) AND (diathesis Chronic) AND (hepatitis B) AND (hepatitis C) AND (hypersensitivity) AND (kidney disease Chronic) AND (nonalcoholic steatohepatitis) AND (opiate Chronic))"}
{"candidate_id": "LLM03669", "doc_id": "NCT02735902_inc", "case_bucket": "other", "source_criterion": "The patient or his/her representative must have given free and informed consent and signed the consent The patient must be insured or beneficiary of a health insurance plan The patient is available for 12 months of follow-up The patient underwent a successful transcutaneous implant procedure for an aortic valve within the past 24 hours The patient was receiving anti-vitamin K (AVK) treatment before percutaneous implantation of the aortic valve", "candidate_expression": "((AVK) AND (The patient is available for 12 months of follow-up) AND (The patient or his/her representative must have given free and informed consent and signed the consent) AND (anti-vitamin K before percutaneous implantation of the aortic valve) AND (aortic valve) AND (transcutaneous implant procedure past 24 hours))"}
{"candidate_id": "LLM03670", "doc_id": "NCT03467750_inc", "case_bucket": "or", "source_criterion": "Diagnosis of sleep disordered breathing or obstructive sleep apnea Children undergoing elective tonsillectomy or adenotonsillectomy at Children's Healthcare of Atlanta Egleston location Parent or legal guardian willing to participate, and able to understand and sign the provided informed consent", "candidate_expression": "((Children) AND (Children's Healthcare of Atlanta Egleston) AND (Parent or legal guardian willing to participate, and able to understand and sign the provided informed consent) AND (adenotonsillectomy) AND (elective) AND (obstructive sleep apnea) AND (sleep disordered breathing) AND (tonsillectomy))"}
{"candidate_id": "LLM03671", "doc_id": "NCT02954029_inc", "case_bucket": "or", "source_criterion": "age 18 years or older patients undergoing invasive procedures via the radial or femoral arteries", "candidate_expression": "((age 18 years or older) AND (invasive procedures undergoing radial arteries femoral arteries))"}
{"candidate_id": "LLM03672", "doc_id": "NCT00609531_inc", "case_bucket": "or", "source_criterion": "Ambulatory status (outpatient) at time of consent Age 10-55 years Clinical diagnosis of Autism Spectrum Disorder IQ greater than or equal to 70 Score greater than 8 on Children's Yale-Brown Obsessive Compulsive Scale Free of psychoactive medication for at least: one month for fluoxetine; two weeks for other SSRIs and neuroleptics; and five days for stimulants prior to MRI scanning [excepting stable doses (greater than three months duration) of anticonvulsant medication for seizure disorder]", "candidate_expression": "((Age 10-55 years) AND (Ambulatory status at time of consent) AND (Autism Spectrum Disorder Clinical diagnosis) AND (Children's Yale-Brown Obsessive Compulsive Scale greater than 8) AND (IQ greater than or equal to 70) AND (outpatient) AND (seizure disorder) AND NOT (psychoactive medication) AND NOT (anticonvulsant medication stable doses greater than three months) AND ((fluoxetine at least one month) OR (stimulants at least five days)) AND ((SSRIs) OR (neuroleptics)))"}
{"candidate_id": "LLM03673", "doc_id": "NCT03225469_inc", "case_bucket": "other", "source_criterion": "1. Individuals scheduled for undergoing colonoscopy at the Endoscopy Center of Wuxi people's Hospital in China 2. Greater than the age of 18 3. Individuals living with other family members 4. Outpatients", "candidate_expression": "((Endoscopy Center of Wuxi people's Hospital in China) AND (Outpatients) AND (age Greater than 18) AND (colonoscopy))"}
{"candidate_id": "LLM03674", "doc_id": "NCT03623789_exc", "case_bucket": "or", "source_criterion": "Preoperative Hemoglobin <U+2266>11 g/dl History of infection or intraarticular fracture of the affective hip Renal function deficiency (GFR <30 ml/min/1.73m2) Elevated liver enzyme (aspartate transaminase (AST)/ alanine transaminase(ALT) level are more than twice normal range) , history of liver cirrhosis, impaired liver function(elevated total bilirubin level) and coagulopathy (including long-term use anticoagulant) History of deep vein thrombosis, ischemic heart disease or stroke Contraindications of tranexamic acid, floseal, or rivaroxaban Allergy to tranexamic acid, floseal, rivaroxaban, or the excipients History of heparin-induced thrombocytopenia (HIT) Coagulopathy or bleeding tendency caused by organ dysfunction, such as cirrhosis, bone marrow suppression etc. Patient who have active bleeding disorder, such as intracranial hemorrhage, upper gastrointestinal bleeding, hematuria. Patients with known allergies to materials of bovine origin.", "candidate_expression": "((Allergy) AND (Contraindications) AND (GFR <30 ml/min/1.73m2) AND (Hemoglobin Preoperative <U+2266>11 g/dl) AND (Renal function deficiency) AND (allergies) AND (anticoagulant long-term use) AND (aspartate transaminase (AST)/ alanine transaminase(ALT) level more than twice normal range) AND (bleeding disorder active) AND (coagulopathy) AND (heparin-induced thrombocytopenia (HIT) History) AND (history) AND (impaired liver function) AND (liver cirrhosis) AND (liver enzyme Elevated) AND (materials of bovine origin) AND (organ dysfunction) AND (total bilirubin level elevated) AND ((deep vein thrombosis) OR (ischemic heart disease) OR (stroke)) AND ((floseal) OR (rivaroxaban) OR (tranexamic acid)) AND ((excipients) OR (floseal) OR (rivaroxaban) OR (tranexamic acid)) AND ((infection) OR (intraarticular fracture)) AND ((Coagulopathy) OR (bleeding tendency)) AND ((bone marrow suppression) OR (cirrhosis)) AND ((hematuria) OR (intracranial hemorrhage) OR (upper gastrointestinal bleeding)))"}
{"candidate_id": "LLM03675", "doc_id": "NCT02788045_exc", "case_bucket": "or", "source_criterion": "Has chronic hepatitis B (measured by hepatitis B surface antigen test) or active hepatitis C (measured by hepatitis C virus [HCV] Ab test; if positive, HCV ribonucleic acid [RNA] PCR test will be used to confirm active versus past HCV infection), active syphilis infection, chlamydia, gonorrhea, or trichomonas . Active syphilis documented by serology unless positive serology is due to past treated infection Has had a thyroidectomy or active thyroid disease requiring medication during the last 12 months (not excluded: a stable thyroid supplementation) Has had major psychiatric illness and/or substance abuse problems during the past 12 months (including hospitalization or periods of work disability) that in the opinion of the investigator would preclude participation Has been in receipt of any licensed vaccine within 14 days prior to the first dose of study vaccine/placebo, plans to receive within 14 days after the first study vaccination, or plans to receive within 14 days before or after the second, third or fourth vaccination Is a recipient of a prophylactic or therapeutic HIV vaccine candidate at any time, or a recipient of other experimental vaccine(s) within the last 12 months. For participants who received an experimental vaccine (except HIV vaccine) more than 12 months ago, documentation of the identity of the experimental vaccine must be provided to the sponsor, who will determine eligibility on a case-by-case basis", "candidate_expression": "((HCV ribonucleic acid [RNA] PCR test) AND (case-by-case basis) AND (experimental vaccine more than 12 months ago) AND (hepatitis B surface antigen test) AND (hepatitis C virus [HCV] Ab test positive) AND (in the opinion of the investigator) AND (licensed vaccine) AND (medication during the last 12 months) AND (placebo) AND (psychiatric illness major) AND (study vaccination first study vaccination) AND (study vaccine) AND (substance abuse) AND (treated infection) AND (vaccination) AND NOT (thyroid supplementation stable) AND NOT (HIV vaccine) AND ((serology) OR NOT (serology positive)) AND ((thyroid disease active) OR (thyroidectomy)) AND ((active hepatitis C) OR (chlamydia) OR (chronic hepatitis B) OR (gonorrhea) OR (syphilis Active) OR (syphilis infection active) OR (trichomonas)) AND ((hospitalization) OR (work disability)) AND ((within 14 days after) OR (within 14 days before or after second, third or fourth vaccination) OR (within 14 days prior the first dose of study vaccine/placebo)) AND ((HIV vaccine candidate at any time) OR (other experimental vaccine(s) within the last 12 months)) AND ((prophylactic) OR (therapeutic)))"}
```
