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
{"candidate_id": "LLM04401", "doc_id": "NCT01846507_inc", "case_bucket": "or", "source_criterion": "1. Menstruating females 10-19 years of age 2. Non-smoker 3. Physician and patient have agreed to initiate Lysteda 4. Diagnosis of HMB based on the medical judgment of the principal or site investigator 5. Subjects must report menstrual periods occurring within 21-60 days from the start of one period to the start of the next menstrual period 6. Negative pregnancy test 7. Informed consent obtained and signed 8. Informed assent obtained and signed 9. Understanding of study procedures 10. Ability to comply with study procedures for the entire length of the study 11. Subjects should be either sexually inactive (abstinent) or agree to use a barrier method with spermicide in the event of sexual activity throughout the study period", "candidate_expression": "((Ability to comply with study procedures for the entire length of the study) AND (HMB) AND (Informed assent obtained and signed) AND (Informed consent obtained and signed) AND (Lysteda) AND (Menstruating) AND (Non-smoker) AND (Understanding of study procedures) AND (age 10-19 years) AND (based on the medical judgment of the principal or site investigator) AND (females) AND (menstrual periods within 21-60 days from the start of one period the start of one period) AND (pregnancy test Negative) AND (sexually abstinent) AND ((barrier method with spermicide agree to use) OR (sexually inactive)))"}
{"candidate_id": "LLM04402", "doc_id": "NCT02437084_exc", "case_bucket": "or", "source_criterion": "Less than 30 yrs of age or > 65 yrs of age Any significant co-morbidities, such as active heart, kidney, or liver diseases, accelerated or malignant hypertension, heart failure, severe anemia.", "candidate_expression": "((age > 65 yrs) AND (age Less than 30 yrs) AND (co-morbidities significant) AND (diseases heart accelerated malignant) AND (diseases kidney) AND (heart failure) AND (hypertension) AND (liver diseases) AND (severe anemia))"}
{"candidate_id": "LLM04403", "doc_id": "NCT02805504_inc", "case_bucket": "other", "source_criterion": "Patients undergoing urologic surgery.", "candidate_expression": "(urologic surgery)"}
{"candidate_id": "LLM04404", "doc_id": "NCT03083197_inc", "case_bucket": "or", "source_criterion": "Age = 15 years old Hospitalization with acute undifferentiated fever (temperature > 37.5 C, tympanic) =14 days or patients admitted to hospital with a history of fever = 14 days who subsequently develop fever within 24 hours of admission Clinically suspected scrub typhus: defined as acute undifferentiated fever with no clear focus of infection and negative malaria blood smear and/or negative malaria RDT. Patients may have one, none, or a combination of other clinical findings such as eschar, rash, lymphadenopathy, headache, myalgia, cough, nausea and abdominal discomfort. A positive scrub typhus RDT (Scrub Typhus IgM RDT, InBios International, Seattle, WA, USA) and/or positive PCR-based detection of O. tsutsugamushi DNA from the admission blood sample Written informed consent and/or, written informed assent as required Able to take oral medication", "candidate_expression": "((= 14 days) AND (= 15 years old) AND (=14 days) AND (> 37.5 C) AND (Able to take oral medication) AND (Age) AND (Hospitalization) AND (O. tsutsugamushi DNA) AND (PCR) AND (Scrub Typhus IgM RDT) AND (Written informed consent) AND (a combination of) AND (abdominal discomfort) AND (acute undifferentiated fever) AND (admission) AND (admission blood sample) AND (admitted to hospital) AND (cough) AND (eschar) AND (fever) AND (focus of infection) AND (headache) AND (history) AND (lymphadenopathy) AND (malaria RDT) AND (malaria blood smear) AND (myalgia) AND (nausea) AND (negative) AND (no clear) AND (none) AND (one) AND (oral medication) AND (positive) AND (rash) AND (scrub typhus) AND (scrub typhus RDT) AND (temperature) AND (tympanic) AND (within 24 hours of admission) AND (written informed assent))"}
{"candidate_id": "LLM04405", "doc_id": "NCT03465397_inc", "case_bucket": "or", "source_criterion": "Adult men and women (=18 years). Receptors of a first kidney transplant from an incompatible HLA living donor (at least 1 mismatch HLA at any antigenic level). AB0 compatible transplant. Patients with a calculated PRA of 0% by solid phase technique and absence of anti-HLA class I and class II antibodies by single antigen test (Luminex®). Patients who agree to participate in the Trial by signing the Specific Informed Consent of this study. Potentially fertile women should use high reliability contraceptive methods (Pearl-Index <1) in order to avoid pregnancy during the entire duration of the study and up to 6 weeks after the end of their treatment with Mycophenolate Mofetil (MMF). Potentially Fertile Women include any woman who has experienced menarche and who has not undergone successful surgical sterilization (hysterectomy, bilateral tubal ligation or bilateral oophorectomy) or who is not post-menopausal (defined as amenorrhea = 12 consecutive months, or women who are receiving hormone replacement therapy with a documented level of follicle stimulating hormone (FSH)> 35 mlU / ml). Potentially fertile women must have a pregnancy test with a negative result in the 72 hours prior to the start of the trial. Sexually active males (including vasectomized males) who are being treated with MMF must accept the use of barrier contraceptive methods during MMF treatment and for 90 days thereafter. Potentially fertile partners of these patients should use a reliable contraceptive method during the same period, in order to minimize the risk of pregnancy. Patients must agree not to donate blood during treatment with MMF and during the 6 subsequent weeks. Males should not make a sperm donation during MMF treatment and up to 90 days after completion.", "candidate_expression": "((0%) AND (=18 years) AND (AB0 compatible) AND (Adult) AND (Patients who agree to participate in the Trial by signing the Specific Informed Consent of this study.) AND (Potentially fertile women should use high reliability contraceptive methods (Pearl-Index <1) in order to avoid pregnancy during the entire duration of the study and up to 6 weeks after the end of their treatment with Mycophenolate Mofetil (MMF). Potentially Fertile Women include any woman who has experienced menarche and who has not undergone successful surgical sterilization (hysterectomy, bilateral tubal ligation or bilateral oophorectomy) or who is not post-menopausal (defined as amenorrhea = 12 consecutive months, or women who are receiving hormone replacement therapy with a documented level of follicle stimulating hormone (FSH)> 35 mlU / ml). Potentially fertile women must have a pregnancy test with a negative result in the 72 hours prior to the start of the trial.) AND (Sexually active males (including vasectomized males) who are being treated with MMF must accept the use of barrier contraceptive methods during MMF treatment and for 90 days thereafter. Potentially fertile partners of these patients should use a reliable contraceptive method during the same period, in order to minimize the risk of pregnancy.) AND (absence of anti-HLA class I) AND (absence of class II) AND (at least 1) AND (calculated PRA) AND (first kidney transplant) AND (incompatible HLA) AND (living donor) AND (men) AND (mismatch HLA) AND (single antigen test (Luminex®)) AND (solid phase technique) AND (transplant) AND (women) AND (years))"}
{"candidate_id": "LLM04406", "doc_id": "NCT02600000_inc", "case_bucket": "scope", "source_criterion": "Diagnosis of Heart Failure; Lower left ventricular ejection fraction 45% (LVEF <45%) assessed by simple and recent echocardiogram; Functional Class II and III by the New York Heart Association (NYHA) Clinically stable; Ex-smokers over five years; Maximal inspiratory pressure (MIP) <70% of predicted; Forced expiratory volume/Forced vital capacity (FEV1 / FVC) > 70% of predicted;", "candidate_expression": "((Clinically stable) AND (Ex-smokers over five years) AND (Forced expiratory volume/Forced vital capacity (FEV1 / FVC) > 70% of predicted) AND (Heart Failure) AND (LVEF <45%) AND (Lower left ventricular ejection fraction 45%) AND (Maximal inspiratory pressure (MIP) <70% of predicted) AND (New York Heart Association (NYHA) Class II and III) AND (echocardiogram recent))"}
{"candidate_id": "LLM04407", "doc_id": "NCT02083991_inc", "case_bucket": "or", "source_criterion": "First or second single kidney (cadaveric or living donors) transplant recipients. Considered for a standard immunosuppressive protocol. Must be capable of giving written informed connect for participation in the study for 24 months.", "candidate_expression": "((Considered for) AND (First single kidney transplant) AND (Must be capable of giving written informed connect for participation in the study for 24 months.) AND (cadaveric donors) AND (living donors) AND (standard immunosuppressive protocol) AND (transplant second single kidney))"}
{"candidate_id": "LLM04408", "doc_id": "NCT01803828_inc", "case_bucket": "or", "source_criterion": "age 35-75 years; Diagnosis of Type 2 Diabetes from at least 3 years; HbA1c < 10%; normal blood pressure or controlled hypertension; BMI < 40;", "candidate_expression": "((BMI < 40) AND (HbA1c < 10%) AND (Type 2 Diabetes at least 3 years) AND (age 35-75 years) AND (controlled hypertension) AND (normal blood pressure))"}
{"candidate_id": "LLM04409", "doc_id": "NCT02573168_inc", "case_bucket": "or", "source_criterion": "18 years of age or older; Suffer from schizophrenia/schizoaffective disorder meeting Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, Text Revision (DSM-IV-TR) criteria; Have a total baseline score on the Brief Psychiatric Rating Scale (BPRS) = 45; Be capable and willing to provide written informed consent to participate in this study; Agree to abide by the study protocol and its restrictions and be able to complete all aspects of the study, including all visits and tests", "candidate_expression": "((18 years or older) AND (= 45) AND (Agree to abide by the study protocol and its restrictions and be able to complete all aspects of the study, including all visits and tests) AND (BPRS) AND (Be capable and willing to provide written informed consent to participate in this study) AND (Brief Psychiatric Rating Scale) AND (DSM-IV-TR) AND (Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, Text Revision) AND (age) AND (schizoaffective disorder) AND (schizophrenia))"}
{"candidate_id": "LLM04410", "doc_id": "NCT03637946_exc", "case_bucket": "or", "source_criterion": "With severe systemic alteration; In the use of antibiotics and anti-inflammatories in the last three months; With periodontium with periodontal parameters different from those established in the inclusion criteria. Individuals with clinical signs of parafunctional habits; Smoking; Individuals who have performed other restorations in the last 12 months; Pregnant women and infants; Periodontal sites that presented bleeding during crevicular fluid collection or sites that prevent proper collection of clinical parameters.", "candidate_expression": "((Pregnant) AND (Smoking) AND (clinical signs of parafunctional habits) AND (infants) AND (other restorations in the last 12 months) AND (systemic alteration severe) AND (women) AND ((anti-inflammatories) OR (antibiotics)))"}
{"candidate_id": "LLM04411", "doc_id": "NCT03460002_exc", "case_bucket": "or", "source_criterion": "the child has temperature > 39.0◦C or a severe acute illness as defined by the examining nurse the child has as a mid upper arm circumference < 110 mm and is older than 6 months (most feasible local indicator of AIDS and chronic immunosuppressive disease) the child has experienced a severe allergic reaction after previous vaccination, drug or food. the child is enrolled in an ongoing study of Bacillus Calmette Guerin vaccine and is < 2 months old For the RECAMP-MV trial: the child is enrolled in RECAMP-OPV", "candidate_expression": "((< 110 mm) AND (> 39.0◦C) AND (RECAMP-MV trial) AND (acute illness) AND (after previous vaccination, drug or food) AND (as defined by the examining nurse) AND (child) AND (enrolled in RECAMP-OPV) AND (is older than 6 months) AND (mid upper arm circumference) AND (old) AND (previous) AND (previous vaccination, drug or food) AND (severe) AND (severe allergic reaction) AND (temperature) AND (the child is enrolled in an ongoing study of Bacillus Calmette Guerin vaccine and is < 2 months old) AND ((drug) OR (food) OR (vaccination)))"}
{"candidate_id": "LLM04412", "doc_id": "NCT03499639_exc", "case_bucket": "or", "source_criterion": "Patients with combined HCV/HBV co-infection hepatocellular carcinoma (HCC) decompensated liver cirrhosis (Child-Pugh score above 6) non-genotype 4", "candidate_expression": "((Child-Pugh score) AND (HBV infection) AND (HCV infection) AND (above 6) AND (decompensated) AND (genotype 4) AND (hepatocellular carcinoma (HCC)) AND (liver cirrhosis) AND (non))"}
{"candidate_id": "LLM04413", "doc_id": "NCT02083991_exc", "case_bucket": "or", "source_criterion": "Diabetes mellitus or plasma glucose >11,1 at admission. Receiving steroids at the time of transplantation or likely to need steroids after transplantation. Multiorgan transplants and/or previously transplanted with any other organ than kidney. Panel reacting antibodies(PRA) >25% in most recent test or considered to be of high risk for rejection which requires an enhanced immunosuppression. Renal transplants from HLA-identical sibling. Hypersensitivity to, or disability to take immunosuppressive drugs. Blood group(ABO)-incompatible transplants. Unlikely to comply with the study requirements. Transplant from donor positive for HIV, HBsAg, Hepatitis C. Female of childbearing potential planing/being pregnant or unwilling to use contraception.", "candidate_expression": "((Diabetes mellitus) AND (Female of childbearing potential planing/being pregnant or unwilling to use contraception.) AND (Hypersensitivity) AND (Multiorgan transplants) AND (Panel reacting antibodies(PRA) >25% most recent test) AND (Receiving at the time of transplantation) AND (Renal transplants HLA-identical sibling) AND (Transplant donor) AND (disability) AND (enhanced immunosuppression) AND (immunosuppressive drugs) AND (plasma glucose >11,1 at admission) AND (positive for HBsAg) AND (positive for HIV) AND (positive for Hepatitis C) AND (rejection considered to be of high risk) AND (steroids) AND (steroids likely to need after transplantation) AND (transplanted with any other organ than kidney previously) AND (transplants Blood group(ABO)-incompatible))"}
{"candidate_id": "LLM04414", "doc_id": "NCT02868437_inc", "case_bucket": "other", "source_criterion": "Subject has curettage for retained product after second trimester abortion", "candidate_expression": "((abortion second trimester) AND (curettage) AND (retained product))"}
{"candidate_id": "LLM04415", "doc_id": "NCT00312429_inc", "case_bucket": "or", "source_criterion": "Diagnosis reviewed at transplant center and confirmed to fit the criterion for high risk blood disease or cancer, as defined for the study Estimated life expectancy of at least 6 weeks following study entry Cancer and Leukemia Group B (CALGB) performance status less than or equal to 2 White blood cell count, platelet, hematocrit, tuberculosis, aspartate aminotransferase (AST), alanine aminotransferase (ALT), alkaline phosphatase, creatinine, and HIV test results reviewed by transplant center Multiple gated acquisition (MUGA), echocardiogram, cardiac MRI, and/or pulmonary function tests (PFT) performed and reviewed by transplant center (for individuals with an ejection fraction and diffusing capacity [DLCO] of 40-50%, the appropriate cardiology or pulmonary consultations should be considered if the individual has severe heart or lung disease at the initiation of therapy) Sufficient number of umbilical cord blood units available for transplantation If female, willing to use contraception throughout the study", "candidate_expression": "((Cancer and Leukemia Group B (CALGB) performance status less than or equal to 2) AND (Estimated life expectancy at least 6 weeks following study entry) AND (HIV test results) AND (Multiple gated acquisition (MUGA)) AND (White blood cell count) AND (alanine aminotransferase (ALT)) AND (alkaline phosphatase) AND (aspartate aminotransferase (AST)) AND (cancer) AND (cardiac MRI) AND (contraception throughout the study) AND (creatinine) AND (echocardiogram) AND (female) AND (hematocrit) AND (high risk blood disease) AND (platelet) AND (pulmonary function tests (PFT)) AND (transplantation) AND (tuberculosis) AND (umbilical cord blood units available Sufficient number for transplantation))"}
{"candidate_id": "LLM04416", "doc_id": "NCT03639519_inc", "case_bucket": "other", "source_criterion": "Elective Cardiac surgery American Society of Anesthesiologists physical status class I-III", "candidate_expression": "((American Society of Anesthesiologists physical status class I-III) AND (Elective Cardiac surgery))"}
{"candidate_id": "LLM04417", "doc_id": "NCT02966236_inc", "case_bucket": "scope", "source_criterion": "Complex kidney stone (staghorn calculi GUYS III and IV)", "candidate_expression": "((Complex kidney stone) AND (GUYS) AND (III and IV) AND (staghorn calculi))"}
{"candidate_id": "LLM04418", "doc_id": "NCT03209011_exc", "case_bucket": "or", "source_criterion": "Active consumption of alcohol and/or drugs Co-infection with human immunodeficiency virus, hepatitis C virus, or hepatitis D virus History of autoimmune hepatitis Psychiatric disease Evidence of neoplastic diseases of the liver", "candidate_expression": "((Psychiatric disease) AND (autoimmune hepatitis History) AND (consumption of alcohol) AND (drugs consumption of) AND (hepatitis C virus) AND (hepatitis D virus) AND (human immunodeficiency virus) AND (neoplastic diseases Evidence of liver))"}
{"candidate_id": "LLM04419", "doc_id": "NCT02607748_inc", "case_bucket": "or", "source_criterion": "Acute Coronary Syndrome group: 40 patients with type 1 myocardial infarction within 21 days prior to the imaging visit and invasive coronary angiography with angiographic evidence of at least a 50% stenosis in one or more coronary arteries. Only patients undergoing PCI will be included in the study. Stable Ischemic Heart Disease group: 40 patients who have undergone invasive coronary angiography within 21 days prior to the imaging visit, with history of typical angina prior to the angiogram, but no prior myocardial infarction or coronary revascularization. have no prior CAD associated event (no prior myocardial infarction, acute coronary syndrome, coronary angiogram, or PCI), have CAC between 10 to <1000, and match to patients in the ACS group by gender, age by decile, and CAC category (using CAC categories of 10 to <100, 100 to <400, 400 to <1000).", "candidate_expression": "((Acute Coronary Syndrome) AND (CAC between 10 to <1000) AND (PCI) AND (acute coronary syndrome) AND (coronary angiogram) AND (myocardial infarction) AND NOT (CAD))"}
{"candidate_id": "LLM04420", "doc_id": "NCT01650792_exc", "case_bucket": "or", "source_criterion": "Patients with a history of an untreated malignancy (except local skin cancers) Ischemic stroke (determined using the Questionnaire for Verifying Stroke-Free Status (QVSFS) Patients on renal dialysis or with end-stage hepatic dysfunction Acute infection/inflammation (Temperature > 101.5 F, and/or WBC> 15, 000) Inability to obtain informed consent from patient or next of kin Anticoagulant use (warfarin or heparin)", "candidate_expression": "((Anticoagulant) AND (Inability to obtain informed consent from patient or next of kin) AND (Ischemic stroke Questionnaire for Verifying Stroke-Free Status (QVSFS)) AND (Temperature > 101.5 F) AND (WBC > 15, 000) AND (end-stage hepatic dysfunction) AND (heparin) AND (infection) AND (inflammation) AND (malignancy untreated) AND (renal dialysis) AND (warfarin) AND NOT (local skin cancers))"}
{"candidate_id": "LLM04421", "doc_id": "NCT02456532_exc", "case_bucket": "or", "source_criterion": "acute or unstable medical disease, current or past history of psychiatric disease, alcoholism or drug abuse, and other primary sleep disorders", "candidate_expression": "((medical disease) AND ((acute) OR (unstable)) AND ((alcoholism) OR (drug abuse) OR (primary sleep disorders) OR (psychiatric disease)))"}
{"candidate_id": "LLM04422", "doc_id": "NCT03355157_inc", "case_bucket": "or", "source_criterion": "Written informed consent prior to beginning specific protocol procedures, including expected cooperation of the patients for the treatment and follow-up, willingness and ability to complete collection of data via wearable device and study mobile must be obtained and documented according to the local regulatory requirements. Female or male patients. Age = 18 years old. Metastatic invasive hormone receptor positive and HER2 negative breast cancer (histologically confirmed). Patients who in the opinion of the treating physician are candidates suitable for randomization for mono-chemotherapy treatment, that has either an approved label in Europe and/or is supported by guidelines for the treatment of first-line advanced BC, which are based on evidence on safety and efficacy in this setting. Symptomatic or asymptomatic metastatic breast cancer. Resolution of all acute toxic effects of prior anti-cancer therapy or surgical procedures to NCI CTCAE version 4.0 grade = 1 (except alopecia or other toxicities not considered a safety risk for the patient at investigator's discretion). Life-expectancy > 6 months. For female patients: The patients need to be either A) of non-childbearing potential (documented postmenopausal or post hysterectomy) B) childbearing potential with negative serum or urinary pregnancy test (in this case patients need to use highly effective non-hormonal contraceptive methods).", "candidate_expression": "((= 18 years old) AND (> 6 months) AND (Age) AND (Female) AND (HER2 negative) AND (Life-expectancy) AND (Metastatic) AND (NCI CTCAE version 4.0) AND (Resolution) AND (Symptomatic) AND (acute toxic effects) AND (alopecia) AND (anti-cancer therapy) AND (asymptomatic) AND (breast cancer) AND (except) AND (grade = 1) AND (hormone receptor positive) AND (invasive) AND (male) AND (metastatic breast cancer) AND (or female patients: The patients need to be either A) of non-childbearing potential (documented postmenopausal or post hysterectomy) B) childbearing potential with negative serum or urinary pregnancy test (in this case patients need to use highly effective non-hormonal contraceptive methods).) AND (prior) AND (surgical procedure))"}
{"candidate_id": "LLM04423", "doc_id": "NCT03344887_exc", "case_bucket": "other", "source_criterion": "Patients that do not have a valid Ontario Health Insurance Plan (OHIP) number at time of first transfusion Patients that require emergent release of a RBC transfusion and in whom emergency randomization could not be completed Patients with complex antibody profile in which it is impossible to match RBC units", "candidate_expression": "((RBC transfusion) AND (at time of first transfusion) AND (complex antibody profile) AND (could not be completed) AND (emergency randomization) AND (emergent release) AND (first) AND (first transfusion) AND (have a valid Ontario Health Insurance Plan (OHIP) number) AND (impossible to match RBC units) AND (not) AND (require) AND (transfusion))"}
{"candidate_id": "LLM04424", "doc_id": "NCT02667730_exc", "case_bucket": "or", "source_criterion": "Diagnosis of ankle fracture or ligament rupture Has planned release from the Canadian Armed Forces within one year; Documented restrictions on military duties Has known intolerance or documented adverse reaction to acetaminophen or naproxen or celecoxib Documented history of liver or kidney problems pregnant or breastfeeding", "candidate_expression": "((acetaminophen) AND (adverse reaction) AND (ankle fracture) AND (breastfeeding) AND (celecoxib) AND (history) AND (intolerance) AND (kidney problems) AND (ligament rupture) AND (liver problems) AND (naproxen) AND (pregnant) AND (release from the Canadian Armed Forces) AND (restrictions on military duties) AND (within one year))"}
{"candidate_id": "LLM04425", "doc_id": "NCT02691793_exc", "case_bucket": "or", "source_criterion": "Patients with second primary cancer, except:adequately treated non-melanoma skin cancer, curatively treated in-situ cancer of the cervix, or other solid tumor curatively treated with no evidence of disease for <= 5 years. Has known active central nervous system(CNS) metastases Has an active infection requiring systemic therapy Pregnancy or breast feeding Patients with cardiac problem Any previous treatment with sunitinib", "candidate_expression": "((CNS) AND (Pregnancy or breast feeding) AND (active infection) AND (cardiac problem) AND (central nervous system) AND (except) AND (metastases) AND (primary cancer,) AND (second) AND (solid tumor) AND (sunitinib) AND (treated) AND ((in-situ cancer of the cervix) OR (non-melanoma skin cancer)))"}
```
