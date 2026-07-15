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
{"candidate_id": "LLM01501", "doc_id": "NCT02894645_exc", "case_bucket": "or", "source_criterion": "Age less than one year or age greater than/equals to 18 years Previous treatment with cytotoxic agents or high-dose steroids Mixed phenotype acute leukemia (MPAL) ALL as secondary malignancy Abnormal renal or liver function Doubtful compliance or unable to afford full course of therapy", "candidate_expression": "((ALL) AND (Abnormal liver function) AND (Abnormal renal function) AND (Age) AND (Doubtful compliance) AND (MPAL) AND (Mixed phenotype acute leukemia) AND (Previous) AND (age) AND (cytotoxic agents) AND (greater than/equals to 18 years) AND (high-dose steroids) AND (less than one year) AND (malignancy) AND (secondary) AND (treatment) AND (unable to afford full course of therapy))"}
{"candidate_id": "LLM01502", "doc_id": "NCT02754583_exc", "case_bucket": "other", "source_criterion": "School districts that are too difficult to reach (more than a 3-hour walk from the farthest place reachable by a four-wheel drive vehicle) School districts in the 2 urban regions of the study area Refusal of village chief All residents residing near to the well sites that are randomly selected for this study. Refusal of participant [or parent/guardian]", "candidate_expression": "((Refusal of participant [or parent/guardian]) AND (School districts in the 2 urban regions of the study area) AND (School districts that are too difficult to reach) AND (more than a 3-hour) AND (near to the well sites) AND (residing) AND (walk from the farthest place reachable by a four-wheel drive vehicle))"}
{"candidate_id": "LLM01503", "doc_id": "NCT02916342_inc", "case_bucket": "other", "source_criterion": "ASA physical status I-III; 18-85 years of age, inclusive; surgery less than 3 hours.", "candidate_expression": "((ASA physical status I-III) AND (age 18-85 years , inclusive) AND (surgery less than 3 hours))"}
{"candidate_id": "LLM01504", "doc_id": "NCT03124329_inc", "case_bucket": "or", "source_criterion": "Male and female individuals between ages of 18 to 70 years old Multiple contiguous gingival recession defects on a minimum of two adjacent teeth, exhibiting 3mm or more recession on at least one of those teeth No prior surgical treatment in the sites planned for therapy Minimum of 2 mm of keratinized gingiva Absence of cervical restorations extending to the CEJ Miller class 1, 2 and 3 recession defects will be included Availability to undergo treatment and return for follow up visits at specified post-operative intervals", "candidate_expression": "((3mm or more) AND (Absence) AND (Miller) AND (Minimum of 2 mm) AND (Multiple) AND (No) AND (ages) AND (at least one) AND (between 18 to 70 years old) AND (cervical restorations extending to the CEJ) AND (class 1, 2 and 3) AND (gingival recession defects) AND (keratinized gingiva) AND (minimum of two) AND (recession) AND (recession defects) AND (surgical treatment))"}
{"candidate_id": "LLM01505", "doc_id": "NCT02361905_inc", "case_bucket": "other", "source_criterion": "hypoechoic uterine leiomyoma (echogenicity <3), intramural leiomyomas with an ultrasonographic size <20 cm but >4cm, indication to surgery (symptoms of menometrorrhagia, menstrual disorder, infertility, pelvic pain or pelvic pressure", "candidate_expression": "((echogenicity <3) AND (infertility) AND (intramural leiomyomas) AND (menometrorrhagia) AND (menstrual disorder) AND (pelvic pain) AND (pelvic pressure) AND (surgery indication to) AND (ultrasonographic size <20 cm but >4cm) AND (uterine leiomyoma hypoechoic))"}
{"candidate_id": "LLM01506", "doc_id": "NCT03465397_inc", "case_bucket": "or", "source_criterion": "Adult men and women (=18 years). Receptors of a first kidney transplant from an incompatible HLA living donor (at least 1 mismatch HLA at any antigenic level). AB0 compatible transplant. Patients with a calculated PRA of 0% by solid phase technique and absence of anti-HLA class I and class II antibodies by single antigen test (Luminex®). Patients who agree to participate in the Trial by signing the Specific Informed Consent of this study. Potentially fertile women should use high reliability contraceptive methods (Pearl-Index <1) in order to avoid pregnancy during the entire duration of the study and up to 6 weeks after the end of their treatment with Mycophenolate Mofetil (MMF). Potentially Fertile Women include any woman who has experienced menarche and who has not undergone successful surgical sterilization (hysterectomy, bilateral tubal ligation or bilateral oophorectomy) or who is not post-menopausal (defined as amenorrhea = 12 consecutive months, or women who are receiving hormone replacement therapy with a documented level of follicle stimulating hormone (FSH)> 35 mlU / ml). Potentially fertile women must have a pregnancy test with a negative result in the 72 hours prior to the start of the trial. Sexually active males (including vasectomized males) who are being treated with MMF must accept the use of barrier contraceptive methods during MMF treatment and for 90 days thereafter. Potentially fertile partners of these patients should use a reliable contraceptive method during the same period, in order to minimize the risk of pregnancy. Patients must agree not to donate blood during treatment with MMF and during the 6 subsequent weeks. Males should not make a sperm donation during MMF treatment and up to 90 days after completion.", "candidate_expression": "((0%) AND (=18 years) AND (AB0 compatible) AND (Adult) AND (Patients who agree to participate in the Trial by signing the Specific Informed Consent of this study.) AND (Potentially fertile women should use high reliability contraceptive methods (Pearl-Index <1) in order to avoid pregnancy during the entire duration of the study and up to 6 weeks after the end of their treatment with Mycophenolate Mofetil (MMF). Potentially Fertile Women include any woman who has experienced menarche and who has not undergone successful surgical sterilization (hysterectomy, bilateral tubal ligation or bilateral oophorectomy) or who is not post-menopausal (defined as amenorrhea = 12 consecutive months, or women who are receiving hormone replacement therapy with a documented level of follicle stimulating hormone (FSH)> 35 mlU / ml). Potentially fertile women must have a pregnancy test with a negative result in the 72 hours prior to the start of the trial.) AND (Sexually active males (including vasectomized males) who are being treated with MMF must accept the use of barrier contraceptive methods during MMF treatment and for 90 days thereafter. Potentially fertile partners of these patients should use a reliable contraceptive method during the same period, in order to minimize the risk of pregnancy.) AND (absence of anti-HLA class I) AND (absence of class II) AND (at least 1) AND (calculated PRA) AND (first kidney transplant) AND (incompatible HLA) AND (living donor) AND (mismatch HLA) AND (single antigen test (Luminex®)) AND (solid phase technique) AND (transplant) AND (years) AND ((men) OR (women)))"}
{"candidate_id": "LLM01507", "doc_id": "NCT02056301_exc", "case_bucket": "other", "source_criterion": "1) Refusal of epidural catheter 2) Pregnancy 3) Bleeding History 4) Inability to understand how to use the PCA device 5) Medication interfering with blood coagulation 6) Patients allergic to local anesthetics 7) Patient refusal to participate in study 8) Developmental delay", "candidate_expression": "((Bleeding History) AND (Developmental delay) AND (Medication interfering with blood coagulation) AND (Pregnancy) AND (allergic) AND (epidural catheter Refusal) AND (local anesthetics))"}
{"candidate_id": "LLM01508", "doc_id": "NCT02437084_inc", "case_bucket": "other", "source_criterion": "Healthy adults 30- 65 years old, BMI 25-35 kg/m2, nondiabetic as defined by fasting plasma glucose <126 mg/dL Lipids: one group with an LDL =/>130 and Triglycerides < 150 mg/dL The 2nd group will have and LDL=/>130 mg/dL and Triglycerides =/>150 mg/dL but less than 400 mg/dL.", "candidate_expression": "((25-35 kg/m2) AND (30- 65 years old) AND (< 150 mg/dL) AND (<126 mg/dL) AND (=/>130) AND (BMI) AND (Healthy) AND (LDL) AND (Triglycerides) AND (adults) AND (fasting plasma glucose) AND (nondiabetic) AND (old))"}
{"candidate_id": "LLM01509", "doc_id": "NCT02827526_exc", "case_bucket": "or", "source_criterion": "Preoperative renal failure (defined as a serum creatinine > 2.0 mg/dL.) American Society of Anesthesiologists Physical Status IV or V Pulmonary disease necessitating home oxygen therapy Allergy to methadone, hydromorphone, or ketamine Preoperative recent history of opioid or alcohol abuse Significant liver disease Inability to use a PCA device or speak the English language", "candidate_expression": "((> 2.0 mg/dL) AND (American Society of Anesthesiologists Physical Status) AND (IV or V) AND (PCA device) AND (Preoperative) AND (Pulmonary disease) AND (Significant) AND (history) AND (home oxygen therapy) AND (hydromorphone) AND (ketamine) AND (liver disease) AND (methadone) AND (recent) AND (renal failure) AND (serum creatinine) AND ((alcohol abuse) OR (opioid abuse)) AND ((Inability to speak the English language) OR (Inability to use)))"}
{"candidate_id": "LLM01510", "doc_id": "NCT03255044_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to statin Treatment with statins during the past month prior to study. Serum creatinine > 3 mg/dl Significant liver disease: liver enzymes 2.5 folds the upper normal limit Malignancy Pregnancy or lactation", "candidate_expression": "((2.5 folds the upper normal limit) AND (> 3 mg/dl) AND (Malignancy) AND (Serum creatinine) AND (Significant) AND (during the past month prior to study) AND (hypersensitivity) AND (liver disease) AND (liver enzymes) AND (statin) AND (statins) AND (the past month prior to study) AND ((Pregnancy) OR (lactation)))"}
{"candidate_id": "LLM01511", "doc_id": "NCT02900443_inc", "case_bucket": "other", "source_criterion": "Probable or definite diagnosis of autoimmune hepatitis according to the International Autoimmune Hepatitis Study Group criteria First presentation of AIH requiring treatment according to the current EASL guidelines Age = 18 years Must provide informed consent and agree to comply with the trial protocol", "candidate_expression": "((= 18 years) AND (AIH) AND (Age) AND (EASL guidelines) AND (International Autoimmune Hepatitis Study Group criteria) AND (Must provide informed consent and agree to comply with the trial protocol) AND (autoimmune hepatitis) AND (treatment))"}
{"candidate_id": "LLM01512", "doc_id": "NCT02923700_inc", "case_bucket": "or", "source_criterion": "patients affected by mono-lateral symptomatic knee articular degenerative pathology with history of chronic (for at least 4 months) pain or swelling; imaging findings of degenerative changes of the joint (osteoarthritis or chondropathy with Kellgren Lawrence Score from 0 to 3 at X-ray evaluation).", "candidate_expression": "((Kellgren Lawrence Score from 0 to 3) AND (X-ray) AND (degenerative changes) AND (imaging) AND (knee articular degenerative pathology mono-lateral symptomatic for at least 4 months) AND ((chondropathy) OR (osteoarthritis)) AND ((pain) OR (swelling)))"}
{"candidate_id": "LLM01513", "doc_id": "NCT03169127_exc", "case_bucket": "or", "source_criterion": "Presence of systemic diseases; Presence of local inflammation and/or infection; Any history of allergic reaction to local anesthetics, gastrointestinal bleeding or ulceration; Cardiovascular, kidney or hepatic diseases; Patients who are making use of antidepressants, diuretics or anticoagulants; Asthma and allergy to aspirin, ibuprofen or any other nonsteroidal antiinflammatory drug; Regular use of any nonsteroidal antiinflammatory drug, Pregnancy or breast feeding.", "candidate_expression": "((local anesthetics) AND (nonsteroidal antiinflammatory drug Regular use) AND (systemic diseases) AND ((Cardiovascular diseases) OR (hepatic diseases) OR (kidney diseases)) AND ((anticoagulants) OR (antidepressants) OR (diuretics)) AND ((Asthma) OR (allergy)) AND ((aspirin) OR (ibuprofen) OR (nonsteroidal antiinflammatory drug any other)) AND ((Pregnancy) OR (breast feeding)) AND ((local infection) OR (local inflammation)) AND ((allergic reaction) OR (gastrointestinal bleeding) OR (gastrointestinal ulceration)))"}
{"candidate_id": "LLM01514", "doc_id": "NCT02748330_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01515", "doc_id": "NCT03233880_exc", "case_bucket": "or", "source_criterion": "Women with multi-fetal pregnancy, diabetes mellitus, chronic hypertension, or chronic renal disease", "candidate_expression": "((Women) AND (chronic hypertension) AND (chronic renal disease) AND (diabetes mellitus) AND (multi-fetal pregnancy))"}
{"candidate_id": "LLM01516", "doc_id": "NCT02890719_inc", "case_bucket": "or", "source_criterion": "Age between 18 and 78 year-old. Previous liver transplantation(more than 6 month). Genotype 1 and 4 infection. Hepatitis C recurrence defined by the presence of abnormal liver function test, positive HCV-RNA, histological signs of hepatitis C recurrence. Viral load ≥10000UI/mL. Immunosuppression with tacrolimus and/or mycophenolate (Prednisone use is allowed at low dose, ≤10 mg/d). Treatment naïve or treatment experienced (Peg-RBV or triple therapy).", "candidate_expression": "((Age between 18 and 78 year-old) AND (Genotype 1 and 4) AND (HCV-RNA positive) AND (Hepatitis C recurrence) AND (Immunosuppression) AND (Peg-RBV) AND (Prednisone low dose) AND (Treatment naïve ≤10 mg/d) AND (Viral load ≥10000UI/mL) AND (hepatitis C recurrence) AND (histological) AND (histological signs of hepatitis C recurrence) AND (infection) AND (liver function test abnormal) AND (liver transplantation Previous more than 6 month) AND (mycophenolate) AND (tacrolimus) AND (treatment experienced) AND (triple therapy))"}
{"candidate_id": "LLM01517", "doc_id": "NCT01483118_inc", "case_bucket": "or", "source_criterion": "Patients aged greater than 18 years of age Ability to understand and willingness to comply with the study protocol Written informed consent Patients meeting the Rotterdam PCOS workshop criteria for polycystic ovary syndrome, defined by oligomenorrhea or amenorrhea and at least one of the following two signs: clinical or biochemical evidence of hyperandrogenism or ultrasound finding of polycystic appearing ovaries.", "candidate_expression": "((Ability to understand and willingness to comply with the study protocol) AND (Rotterdam PCOS workshop criteria for polycystic ovary syndrome) AND (Written informed consent) AND (at least one) AND (greater than 18 years) AND (meeting) AND (polycystic ovaries) AND ((amenorrhea) OR (oligomenorrhea)) AND ((hyperandrogenism) OR (ultrasound)) AND ((age) OR (aged)))"}
{"candidate_id": "LLM01518", "doc_id": "NCT02318446_exc", "case_bucket": "or", "source_criterion": "Pregnancy and lactation Patients with diabetes, Ischemic heart disease (IHD), stroke, malignancy and psychiatric diseases are excluded from study. The patients receiving vitamin supplements or who had clinical evidence for an acute illness, renal dysfunction, thyroid dysfunction, chronic inflammatory diseases, inborn errors of homocysteine, cobalamin or folate metabolism, or any other condition known to interfere with homocysteine metabolism will be excluded Patients who are already involved in any other trial. Patients not willing to fill consent/ assent form are also excluded from study.", "candidate_expression": "((Ischemic heart disease (IHD)) AND (Patients not willing to fill consent/ assent form are also excluded from study.) AND (Pregnancy) AND (acute illness) AND (chronic inflammatory diseases) AND (clinical evidence for an acute illness) AND (condition known to interfere with homocysteine metabolism) AND (diabetes) AND (inborn errors of cobalamin metabolism) AND (inborn errors of folate metabolism) AND (inborn errors of homocysteine metabolism) AND (lactation) AND (malignancy) AND (psychiatric diseases) AND (renal dysfunction) AND (stroke) AND (thyroid dysfunction) AND (vitamin supplements))"}
{"candidate_id": "LLM01519", "doc_id": "NCT02777580_exc", "case_bucket": "or", "source_criterion": "1. Expected performance of PCI < 60 minutes from diagnosis (qualifying ECG) or inability to arrive at the catheterisation laboratory within 3 hours Previous CABG Left bundle branch block or ventricular pacing Patients with cardiogenic shock - Killip Class 4 Patients with a body weight < 55 kg (known or estimated) Uncontrolled hypertension, defined as sustained blood pressure = 180/110 mm Hg (systolic BP = 180 mm Hg and/or diastolic BP = 110 mm Hg) prior to randomisation Known prior stroke or TIA Recent administration of any i.v. or s.c. anticoagulation within 12 hours, including unfractionated heparin, enoxaparin, and/or bivalirudin or current use of oral anticoagulation (i.e. warfarin or a NOACs) Active bleeding or known bleeding disorder/diathesis Known history of central nervous system damage (i.e. neoplasm, aneurysm, intracranial or spinal surgery) or recent trauma to the head or cranium (i.e. < 3 months) Major surgery, biopsy of a parenchymal organ, or significant trauma within the past 2 months (this includes any trauma associated with the current myocardial infarction) Clinical diagnosis associated with increased risk of bleeding including known active peptic ulceration and/or neoplasm with increased bleeding risk Prolonged cardiopulmonary resuscitation (> 2 minutes) within the past 2 weeks Known acute pericarditis and/or subacute bacterial endocarditis Known acute pancreatitis or known severe hepatic dysfunction, including hepatic failure, cirrhosis, portal hypertension (oesophageal varices) and active hepatitis Dementia Known severe renal insufficiency Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 7 days Known allergic reactions to tenecteplase, clopidogrel, enoxaparin and aspirin Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk if the investigational therapy is initiated.", "candidate_expression": "((4) AND (< 3 months) AND (< 55 kg) AND (< 60 minutes from diagnosis) AND (= 110 mm Hg) AND (= 180 mm Hg) AND (= 180/110 mm Hg) AND (Active bleeding) AND (CABG) AND (Dementia) AND (Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk if the investigational therapy is initiated) AND (Killip Class) AND (Left bundle branch block) AND (Major surgery) AND (NOACs) AND (PCI) AND (Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 7 days) AND (Prolonged) AND (TIA) AND (Uncontrolled) AND (active) AND (active hepatitis) AND (acute pancreatitis) AND (acute pericarditis) AND (allergic reactions) AND (aneurysm) AND (anticoagulation) AND (aspirin) AND (biopsy) AND (bivalirudin) AND (bleeding disorder) AND (blood pressure) AND (body weight) AND (cardiogenic shock) AND (cardiopulmonary resuscitation) AND (central nervous system damage) AND (cirrhosis) AND (clopidogrel) AND (cranium) AND (diagnosis) AND (diastolic BP) AND (diathesis) AND (enoxaparin) AND (head) AND (hepatic dysfunction) AND (hepatic failure) AND (hypertension) AND (increased) AND (intracranial surgery) AND (myocardial infarction) AND (neoplasm) AND (oesophageal varices) AND (oral anticoagulation) AND (parenchymal organ) AND (past 2 months) AND (past 2 weeks) AND (peptic ulceration) AND (portal hypertension) AND (renal insufficiency) AND (risk of bleeding) AND (severe) AND (significant) AND (spinal surgery) AND (stroke) AND (subacute bacterial endocarditis) AND (systolic BP) AND (tenecteplase) AND (trauma) AND (unfractionated heparin) AND (ventricular pacing) AND (warfarin) AND (within 12 hours))"}
{"candidate_id": "LLM01520", "doc_id": "NCT03208244_inc", "case_bucket": "scope", "source_criterion": "Recipient is Age = 18 years Serum ALT within normal limits with no history of liver disease Lack of sensitization (i.e. PRA < 20%) that would be expected to result in a high likelihood of needing aggressive immunosuppression to treat rejection", "candidate_expression": "((Age = 18 years) AND (PRA < 20%) AND (Serum ALT within normal limits) AND (sensitization) AND NOT (liver disease history))"}
{"candidate_id": "LLM01521", "doc_id": "NCT02968602_exc", "case_bucket": "or", "source_criterion": "History of organic brain disease DSM-IV diagnosis of Alcohol or Substance Dependence within the last six months (except nicotine) or DSM-5 diagnosis of Substance Use Disorder in the last six months (except nicotine) DSM-IV diagnosis of Alcohol or Substance Abuse within the last one month (except nicotine) or DSM-5 diagnosis of Substance Use Disorder in the last six months (except nicotine) Pregnancy or lactation Severe liver dysfunction (LFT 3X upper limit of normal) Previous known hypersensitivity to tetracyclines Current treatment with tetracycline or derivative Treatment with oral contraceptives (unless a second form of birth control is used and documented) Treatment with cholestyramine or colestipol Treatment with Urinary alkalinizers (e.g., sodium lactate, potassium citrate) Treatment with warfarin Treatment with bupropion, varenicline, or nicotine replacement products in the month prior to study inclusion Less than two months treatment of adjunctive medications AND less than one month on same dose: beta blockers, antidepressants, mood stabilizers, antianxiety medications. Medical condition whose pathology or treatment would significantly increase the risk associated with the proposed protocol. History of head injury, seizures, or stroke Positive urine toxicology screen for substances of non-therapeutic use prior to craving assessments", "candidate_expression": "((LFT 3X upper limit of normal) AND (Medical condition would significantly increase the risk associated with the proposed protocol) AND (Substance Use Disorder DSM-5 in the last six months) AND (Treatment) AND (Treatment birth control) AND (Urinary alkalinizers) AND (adjunctive medications) AND (hypersensitivity Previous) AND (liver dysfunction Severe) AND (oral contraceptives) AND (organic brain disease History of) AND (tetracyclines) AND (treatment Current) AND (treatment Less than two months same dose) AND (urine toxicology screen Positive substances of non-therapeutic use prior to craving assessments) AND (warfarin) AND NOT (Substance Use Disorder DSM-5 in the last six months) AND NOT (nicotine) AND ((Alcohol Abuse) OR (Substance Abuse)) AND ((Pregnancy) OR (lactation)) AND ((Alcohol Dependence) OR (Substance Dependence)) AND ((tetracycline) OR (tetracycline derivative)) AND ((cholestyramine) OR (colestipol)) AND ((potassium citrate) OR (sodium lactate)) AND ((bupropion) OR (nicotine replacement products) OR (varenicline)) AND ((antianxiety medications) OR (antidepressants) OR (beta blockers) OR (mood stabilizers)) AND ((head injury) OR (seizures) OR (stroke)))"}
{"candidate_id": "LLM01522", "doc_id": "NCT02406495_exc", "case_bucket": "or", "source_criterion": "Is not a habitual wearer of Avaira sphere lenses Has a CL prescription outside the range of the available parameters of the study lenses. Has a spectacle cylinder ≥1.00D of cylinder in either eye. Has a history of not achieving comfortable CL wear (5 days per week; > 8 hours/day) Has contact lens best corrected distance vision worse than 20/25 (0.10 logMAR) in either eye. Presence of clinically significant (grade 2-4) anterior segment abnormalities Presence of ocular or systemic disease or need of medications which might interfere with contact lens wear. Slit lamp findings that would contraindicate contact lens wear such as: Pathological dry eye or associated findings Pterygium, pinguecula, or corneal scars within the visual axis Neovascularization > 0.75 mm in from of the limbus Giant papillary conjunctivitis (GCP) worse than grade 1 Anterior uveitis or iritis (past or present) Seborrheic eczema, Seborrheic conjunctivitis History of corneal ulcers or fungal infections Poor personal hygiene Has a known history of corneal hypoesthesia (reduced corneal sensitivity) Has aphakia, keratoconus or a highly irregular cornea. Has Presbyopia or has dependence on spectacles for near work over the contact lenses. Has undergone corneal refractive surgery. Is participating in any other type of eye related clinical or research study", "candidate_expression": "((2-4) AND (5 days per week) AND (> 0.75 mm in from of the limbus) AND (> 8 hours/day) AND (Avaira sphere lenses) AND (CL prescription) AND (Giant papillary conjunctivitis (GCP)) AND (History) AND (Neovascularization) AND (Poor personal hygiene) AND (Seborrheic conjunctivitis) AND (Seborrheic eczema) AND (Slit lamp) AND (anterior segment abnormalities) AND (clinically significant) AND (comfortable CL wear) AND (contact lens best corrected distance vision) AND (contraindicate contact lens) AND (corneal hypoesthesia) AND (corneal refractive surgery) AND (corneal ulcers) AND (findings) AND (fungal infections) AND (grade 2-4) AND (history) AND (might interfere with contact lens wear) AND (need of medications) AND (not) AND (outside the range of the available parameters of the study lenses) AND (reduced corneal sensitivity) AND (spectacle cylinder) AND (within the visual axis) AND (worse than 0.10 logMAR in either eye) AND (worse than 20/25 in either eye) AND (worse than grade 1) AND (≥1.00D) AND ((need of medications) OR (ocular disease) OR (systemic disease)) AND ((Pathological dry eye) OR (associated findings)) AND ((Pterygium) OR (corneal scars) OR (pinguecula)) AND ((Anterior uveitis) OR (iritis)) AND ((past) OR (present)) AND ((aphakia) OR (highly irregular cornea) OR (keratoconus)) AND ((Presbyopia) OR (dependence on spectacles for near work)))"}
{"candidate_id": "LLM01523", "doc_id": "NCT00235170_exc", "case_bucket": "or", "source_criterion": "1. Congestive heart failure; 2. CABG or Percutaneous Coronary Intervention (PCI) procedure; 3. Planned need for major surgery (e.g. valve surgery or resection of aortic or left ventricular aneurysm, carotid end-arterectomy, abdominal aortic aneurysm surgery etc.); 4. Congenital heart disease; 5. Transmural myocardial infarction within the previous seven days and CK has not returned to normal; 6. Chest pain lasting longer than 30 minutes within 12 hours pre-procedure, if CK enzymes positive (≥ 2x the normal upper limit). 7. History of any cerebrovascular accident; 8. Left main stenosis of 50% or more; 9. Intention to treat more than 1 totally occluded major epicardial vessel; 10. Single vessel (single territory) disease.", "candidate_expression": "((50% or more) AND (CABG) AND (CK) AND (CK enzymes) AND (Chest pain) AND (Congenital heart disease) AND (Congestive heart failure) AND (History of) AND (Intention to) AND (Left main stenosis) AND (Percutaneous Coronary Intervention (PCI)) AND (Single vessel disease) AND (Transmural myocardial infarction) AND (abdominal aortic aneurysm surgery) AND (any cerebrovascular accident) AND (carotid end-arterectomy) AND (has not returned) AND (lasting longer than 30 minutes) AND (major surgery) AND (more than 1) AND (normal) AND (positive) AND (resection of aortic aneurysm) AND (resection of left ventricular aneurysm) AND (single territory disease) AND (totally occluded major epicardial vessel) AND (treat) AND (valve surgery) AND (within 12 hours pre-procedure) AND (within the previous seven days) AND (≥ 2x the normal upper limit))"}
{"candidate_id": "LLM01524", "doc_id": "NCT02589691_exc", "case_bucket": "or", "source_criterion": "contra-indication to inhalational induction (full stomach) contra-indication to the use of rocuronium American Society of Anesthesiologists score (ASA) III or IV intracranial surgery parental refusal absence of affiliation to social security", "candidate_expression": "((American Society of Anesthesiologists score (ASA) III IV) AND (contra-indication) AND (inhalational induction full stomach) AND (intracranial surgery) AND (parental refusal) AND (rocuronium) AND NOT (affiliation to social security))"}
{"candidate_id": "LLM01525", "doc_id": "NCT03317197_inc", "case_bucket": "other", "source_criterion": "The group of patients who participated in the study included adults aged at least 19 years among the atraumatic CA outpatients who came to the ER and received CPR.", "candidate_expression": "((CPR) AND (ER) AND (adults) AND (aged at least 19 years) AND (atraumatic CA) AND (outpatients))"}
```
