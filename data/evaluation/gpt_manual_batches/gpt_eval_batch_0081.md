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
{"candidate_id": "LLM02001", "doc_id": "NCT02924090_exc", "case_bucket": "or", "source_criterion": "Relative contraindications to ECT therapy (recent MI or CVA, increased intracranial pressure, intracranial mass lesion, intracranial aneurysm, epilepsy, known cardiac arrhythmia, pheochromocytoma, pregnancy) Contraindications to etomidate (sepsis, primary or secondary adrenal insufficiency, porphyria) DSM-V diagnosis of a lifetime history of psychotic spectrum disorder Drug or alcohol dependence, or abuse within the past 3 months, soy-bean oil allergy", "candidate_expression": "((Contraindications) AND (DSM-V) AND (ECT therapy) AND (Relative contraindications) AND (adrenal insufficiency) AND (etomidate) AND (increased) AND (lifetime history) AND (porphyria) AND (psychotic spectrum disorder) AND (recent) AND (sepsis) AND (soy-bean oil allergy) AND (within the past 3 months) AND ((cardiac arrhythmia) OR (epilepsy) OR (intracranial aneurysm) OR (intracranial mass lesion) OR (intracranial pressure) OR (pheochromocytoma) OR (pregnancy)) AND ((primary) OR (secondary)) AND ((Drug abuse) OR (Drug dependence) OR (alcohol abuse) OR (alcohol dependence)) AND ((CVA) OR (MI)))"}
{"candidate_id": "LLM02002", "doc_id": "NCT02789111_exc", "case_bucket": "other", "source_criterion": "More than three doses of any opioid within one week of surgery Pregnancy Prisoners Unable to provide consent Emergency surgery Chronic kidney disease stage 5 (GFR < 15 ml/min) Severe hepatic impairment Recent myocardial infarction (within the last 3 months)", "candidate_expression": "((< 15 ml/min)) AND (Chronic kidney disease) AND (Emergency surgery) AND (GFR) AND (More than three doses) AND (Pregnancy) AND (Prisoners) AND (Severe) AND (Unable to provide consent) AND (hepatic impairment) AND (myocardial infarction) AND (opioid) AND (stage 5) AND (surgery) AND (the last 3 months) AND (within one week of surgery))"}
{"candidate_id": "LLM02003", "doc_id": "NCT02567214_exc", "case_bucket": "or", "source_criterion": "Respiratory exacerbation within the 2 months preceding the study Current diagnostic of asthma Significant O2 desaturation (SpO2 < 85%) at rest or during exercise Presence of another pathology that could influence exercise tolerance Use of home oxygen", "candidate_expression": "((O2 desaturation Significant) AND (Respiratory exacerbation within the 2 months preceding the study) AND (SpO2 < 85% at rest during exercise) AND (diagnostic of asthma Current) AND (home oxygen) AND (pathology another influence exercise tolerance))"}
{"candidate_id": "LLM02004", "doc_id": "NCT02566226_inc", "case_bucket": "other", "source_criterion": "physical status I - III patients scheduled to undergo hip arthroplasty", "candidate_expression": "((I - III) AND (hip arthroplasty) AND (physical status) AND (scheduled to undergo))"}
{"candidate_id": "LLM02005", "doc_id": "NCT03066440_inc", "case_bucket": "or", "source_criterion": "Age between 0 and 18 years Venous pH less than 7.25 Ketonuria as confirmed on urine point-of-care testing or urinalysis Hyperglycemia (Serum glucose > 200 mg/dl) Serum bicarbonate <15 mmol/L PICU admission", "candidate_expression": "((Age between 0 and 18 years) AND (Hyperglycemia) AND (Ketonuria) AND (PICU) AND (Serum bicarbonate <15 mmol/L) AND (Serum glucose > 200 mg/dl) AND (Venous pH less than 7.25) AND (admission) AND (urinalysis) AND (urine point-of-care testing))"}
{"candidate_id": "LLM02006", "doc_id": "NCT00198913_inc", "case_bucket": "other", "source_criterion": "type 2 diabetic, age 18 and over, informed consent,", "candidate_expression": "((age 18 and over) AND (informed consent) AND (type 2 diabetic))"}
{"candidate_id": "LLM02007", "doc_id": "NCT02281643_exc", "case_bucket": "or", "source_criterion": "Known intolerance to the doxycycline Body weight <40 kg Pregnancy or breastfeeding History of severe allergic reaction or anaphylaxis Alcohol or drug abuse", "candidate_expression": "((Alcohol abuse) AND (Body weight <40 kg) AND (Pregnancy) AND (allergic reaction severe) AND (anaphylaxis) AND (breastfeeding) AND (doxycycline) AND (drug abuse) AND (intolerance to the doxycycline))"}
{"candidate_id": "LLM02008", "doc_id": "NCT02589691_inc", "case_bucket": "other", "source_criterion": "age <2 years indication of general anesthesia with tracheal intubation inhalational induction scheduled written informed consent of both parents", "candidate_expression": "((<2 years) AND (age) AND (general anesthesia) AND (indication) AND (inhalational induction) AND (scheduled) AND (tracheal intubation) AND (written informed consent of both parents))"}
{"candidate_id": "LLM02009", "doc_id": "NCT02653131_inc", "case_bucket": "or", "source_criterion": "patients receiving home parenteral nutrition (HPN) because of short bowel syndrome for at least 12 months stable metabolic status benign disease", "candidate_expression": "((benign disease) AND (for at least 12 months) AND (home parenteral nutrition (HPN)) AND (metabolic status) AND (short bowel syndrome) AND (stable))"}
{"candidate_id": "LLM02010", "doc_id": "NCT02830360_exc", "case_bucket": "or", "source_criterion": "Unable or unwilling to provide informed consent. Active ischemia (acute thrombus diagnosed by coronary angiography, or dynamic ST segment changes demonstrated on ECG) or another reversible cause of VT (e.g. drug-induced arrhythmia), had recent acute coronary syndrome within 30 days, coronary revascularization (<90 days bypass surgery, <30 days percutaneous coronary intervention), or have CCS functional class IV angina. Note that biomarker level elevation alone after ventricular arrhythmias does not denote acute coronary syndrome or active ischemia. Are ineligible to take the antiarrhythmic drug to which they would be assigned due to allergy, intolerance or contraindication Are known to have protruding left ventricular thrombus or mechanical aortic and mitral valves Have had a prior catheter ablation procedure for VT Are in renal failure (Creatinine clearance <15 mL/min), have NYHA Functional class IV heart failure, or a systemic illness likely to limit survival to <1 year Have had recent ST elevation myocardial infarction or non-ST elevation MI (< 30 days); note that biomarker elevation alone after ventricular arrhythmias does not denote MI. Are pregnant.", "candidate_expression": "((CCS functional class IV) AND (Creatinine clearance <15 mL/min) AND (ECG) AND (NYHA Functional class IV) AND (ST segment changes) AND (Unable or unwilling to provide informed consent) AND (VT) AND (VT reversible) AND (acute coronary syndrome within 30 days,) AND (acute thrombus) AND (antiarrhythmic drug) AND (bypass surgery <90 days) AND (catheter ablation procedure) AND (coronary angiography) AND (coronary revascularization) AND (drug-induced arrhythmia) AND (percutaneous coronary intervention <30 days) AND (pregnant) AND ((angina) OR (ischemia Active)) AND ((allergy) OR (contraindication) OR (intolerance)) AND ((left ventricular thrombus) OR (mechanical aortic valves) OR (mechanical mitral valves)) AND ((heart failure) OR (renal failure) OR (systemic illness survival)) AND ((ST elevation myocardial infarction) OR (non-ST elevation MI)))"}
{"candidate_id": "LLM02011", "doc_id": "NCT03044561_inc", "case_bucket": "other", "source_criterion": "(1) cases of infertility, older than 20 years of age and not older than 40 years. (2) Body mass index (BMI):20-29. (3) women have experienced two or more implantation failure attributed to inadequate endometrial development.", "candidate_expression": "((20-29) AND (BMI) AND (Body mass index) AND (age) AND (attributed to) AND (failure) AND (implantation) AND (inadequate endometrial development) AND (infertility) AND (not older than 40 years) AND (older than 20 years) AND (two or more) AND (women))"}
{"candidate_id": "LLM02012", "doc_id": "NCT03140423_exc", "case_bucket": "other", "source_criterion": "Exclusion criteria includes ICUs with an average length of stay of less than 2 days; HCA hospitals that are not able to transfer or merge data into the centralized data warehouse for the baseline and intervention periods of the study are also excluded.", "candidate_expression": "((ICUs) AND (average length of stay) AND (less than 2 days))"}
{"candidate_id": "LLM02013", "doc_id": "NCT02903407_exc", "case_bucket": "or", "source_criterion": "Exclusion criteria include patients following resuscitation from cardiac arrest who are treated on the cooling protocol patients who have suffered a neurologic event (seizure, stroke) or who have baseline dementia, both of which could limit delirium assessment patients with child class B and C liver disease patients with known allergy to study medications.", "candidate_expression": "((allergy) AND (baseline dementia) AND (child class B C) AND (liver disease) AND (neurologic event) AND (resuscitation from cardiac arrest cooling protocol) AND (seizure) AND (stroke) AND (study medications))"}
{"candidate_id": "LLM02014", "doc_id": "NCT03537924_exc", "case_bucket": "or", "source_criterion": "Any active respiratory, cardiovascular or other disease requiring regular treatment or being otherwise relevant for tolerance of hypoxia or altitude exposure. Any condition that may interfere with protocol compliance including current heavy smoking (>20 cigarettes per day or >20 pack-years with active smoking during the last 10 years), regular use of alcohol. Allergy to acetazolamide and other sulfonamides.", "candidate_expression": "((Allergy) AND (acetazolamide) AND (active smoking during the last 10 years) AND (altitude exposure) AND (cardiovascular disease) AND (cigarettes per day >20) AND (disease other) AND (heavy smoking) AND (hypoxia) AND (pack-years >20) AND (regular use of alcohol) AND (respiratory disease) AND (sulfonamides other) AND (tolerance relevant being) AND (treatment requiring))"}
{"candidate_id": "LLM02015", "doc_id": "NCT01669369_exc", "case_bucket": "or", "source_criterion": "a history of non-standard treatment(chemotherapy or surgery) secondary osteosarcoma or well-differentiated parosteal osteosarcoma evident dysfunction of cardia,liver and kidney, or pregnant women or women during lactation", "candidate_expression": "((chemotherapy) AND (dysfunction of cardia) AND (dysfunction of kidney) AND (dysfunction of liver) AND (history) AND (lactation) AND (non-standard treatment) AND (parosteal osteosarcoma) AND (pregnant) AND (secondary osteosarcoma) AND (surgery) AND (well-differentiated))"}
{"candidate_id": "LLM02016", "doc_id": "NCT03465397_inc", "case_bucket": "or", "source_criterion": "Adult men and women (=18 years). Receptors of a first kidney transplant from an incompatible HLA living donor (at least 1 mismatch HLA at any antigenic level). AB0 compatible transplant. Patients with a calculated PRA of 0% by solid phase technique and absence of anti-HLA class I and class II antibodies by single antigen test (Luminex®). Patients who agree to participate in the Trial by signing the Specific Informed Consent of this study. Potentially fertile women should use high reliability contraceptive methods (Pearl-Index <1) in order to avoid pregnancy during the entire duration of the study and up to 6 weeks after the end of their treatment with Mycophenolate Mofetil (MMF). Potentially Fertile Women include any woman who has experienced menarche and who has not undergone successful surgical sterilization (hysterectomy, bilateral tubal ligation or bilateral oophorectomy) or who is not post-menopausal (defined as amenorrhea = 12 consecutive months, or women who are receiving hormone replacement therapy with a documented level of follicle stimulating hormone (FSH)> 35 mlU / ml). Potentially fertile women must have a pregnancy test with a negative result in the 72 hours prior to the start of the trial. Sexually active males (including vasectomized males) who are being treated with MMF must accept the use of barrier contraceptive methods during MMF treatment and for 90 days thereafter. Potentially fertile partners of these patients should use a reliable contraceptive method during the same period, in order to minimize the risk of pregnancy. Patients must agree not to donate blood during treatment with MMF and during the 6 subsequent weeks. Males should not make a sperm donation during MMF treatment and up to 90 days after completion.", "candidate_expression": "((Adult) AND (Patients who agree to participate in the Trial by signing the Specific Informed Consent of this study.) AND (Potentially fertile women should use high reliability contraceptive methods (Pearl-Index <1) in order to avoid pregnancy during the entire duration of the study and up to 6 weeks after the end of their treatment with Mycophenolate Mofetil (MMF). Potentially Fertile Women include any woman who has experienced menarche and who has not undergone successful surgical sterilization (hysterectomy, bilateral tubal ligation or bilateral oophorectomy) or who is not post-menopausal (defined as amenorrhea = 12 consecutive months, or women who are receiving hormone replacement therapy with a documented level of follicle stimulating hormone (FSH)> 35 mlU / ml). Potentially fertile women must have a pregnancy test with a negative result in the 72 hours prior to the start of the trial.) AND (Sexually active males (including vasectomized males) who are being treated with MMF must accept the use of barrier contraceptive methods during MMF treatment and for 90 days thereafter. Potentially fertile partners of these patients should use a reliable contraceptive method during the same period, in order to minimize the risk of pregnancy.) AND (absence of anti-HLA class I) AND (absence of class II) AND (calculated PRA 0% solid phase technique) AND (first kidney transplant incompatible HLA living donor mismatch HLA) AND (single antigen test (Luminex®)) AND (transplant AB0 compatible) AND (years =18 years) AND ((men) OR (women)))"}
{"candidate_id": "LLM02017", "doc_id": "NCT03125057_exc", "case_bucket": "or", "source_criterion": "Therapy area located outside of head and neck; Other skin diseases that might interfere with the efficacy evaluation; Therapy area was previously received isotope or PDT or other treatment which might interfere with the efficacy evaluation; Allergy to porphyrins and analogues; Photosensitivity; Porphyria; Allergic constitution; Scar diathesis; Immunocompromised conditions; Electrocardiographic abnormalities or organic heart diseases; Coagulation disorders; Hepatic or renal functions abnormal (alanine aminotransferase or aspartate transaminase or total bilirubin > 1.5 upper limit of normal [ULN], or serum creatinine or blood urea nitrogen > 1.5 ULN); Psychiatric diseases; Severe endocrinopathies; Previous therapy of PWS within the last 4 weeks; Participation in any clinical studies within the last 4 weeks; Be judged not suitable to participate the study by the investigators", "candidate_expression": "((Allergic constitution) AND (Allergy) AND (Coagulation disorders) AND (Electrocardiographic) AND (Electrocardiographic abnormalities) AND (Hepatic functions abnormal) AND (Immunocompromised conditions) AND (PDT) AND (PWS) AND (Participation in any clinical studies within the last 4 weeks) AND (Photosensitivity) AND (Porphyria) AND (Psychiatric diseases) AND (Scar diathesis) AND (alanine aminotransferase) AND (analogues) AND (aspartate transaminase) AND (blood urea nitrogen) AND (endocrinopathies Severe) AND (heart diseases organic) AND (isotope) AND (porphyrins) AND (renal functions abnormal) AND (serum creatinine) AND (skin diseases interfere with the efficacy evaluation) AND (therapy Previous within the last 4 weeks) AND (total bilirubin) AND (treatment might interfere with the efficacy evaluation))"}
{"candidate_id": "LLM02018", "doc_id": "NCT03480607_exc", "case_bucket": "or", "source_criterion": "known allergy to any of drugs used coagulopathy any wound or infection related to puncture site major illness failure to gain consent of parents.", "candidate_expression": "((allergy) AND (coagulopathy) AND (consent of parents) AND (drugs used) AND (failure to gain) AND (failure to gain consent of parents) AND (illness) AND (major) AND (puncture site) AND ((infection) OR (wound)))"}
{"candidate_id": "LLM02019", "doc_id": "NCT01822262_exc", "case_bucket": "or", "source_criterion": "Gallbladder's wall >3mm, atrophied gallbladder,gallstone obstruct the Hartmann's pouch. Abdominal ultrasound display the contractibility of gallbladder is poor. The aged patients with bad heart and lung function. Patients who has acute cholecystitis,pancreatitis,pancreaticobiliary diseases, especially choledocholithiasis. Pregnant or lactational women.", "candidate_expression": "((>3mm) AND (Abdominal ultrasound) AND (Hartmann's pouch) AND (aged) AND (contractibility of gallbladder) AND (poor) AND (women) AND ((Gallbladder's wall) OR (atrophied gallbladder) OR (gallstone obstruct)) AND ((bad heart function) OR (bad lung function)) AND ((acute cholecystitis) OR (choledocholithiasis) OR (pancreaticobiliary diseases) OR (pancreatitis)) AND ((Pregnant) OR (lactational)))"}
{"candidate_id": "LLM02020", "doc_id": "NCT03234816_exc", "case_bucket": "other", "source_criterion": "Cardiac morbidities Hypertensive disorders of pregnancy, Peripartum bleeding Baseline systolic blood pressure (SBP) < 100 mmHg Body mass index > 35", "candidate_expression": "((< 100 mmHg) AND (> 35) AND (Baseline) AND (Body mass index) AND (Cardiac morbidities) AND (Hypertensive disorders of pregnancy) AND (Peripartum bleeding) AND (SBP) AND (systolic blood pressure))"}
{"candidate_id": "LLM02021", "doc_id": "NCT01794793_exc", "case_bucket": "or", "source_criterion": "Patient has been permanently discontinued from pasireotide study treatment in the parent study due to unacceptable toxicity, non-compliance to study procedures, withdrawal of consent or any other reason Patient has participated in a Novartis sponsored combination trial where pasireotide was dispensed in combination with another study medication and is still receiving combination therapy. (only patients receiving pasireotide monotherapy can be included) Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test Total abstinence (when this is in line with the preferred and usual lifestyle of the subject. Periodic abstinence (e.g., calendar, ovulation, symptothermal, post-ovulation methods) and withdrawal are not acceptable methods of contraception Female sterilization (have had surgical bilateral oophorectomy with or without hysterectomy) or tubal ligation at least six weeks before taking study treatment. In case of oophorectomy alone, only when the reproductive status of the woman has been confirmed by follow up hormone level assessment Male sterilization (at least 6 months prior to screening). For female subjects on the study the vasectomized male partner should be the sole partner for that subject. Use of oral, injected or implanted hormonal methods of contraception or other forms of hormonal contraception that have comparable efficacy (failure rate <1%), for example hormone vaginal ring or transdermal hormone contraception Placement of an intrauterine device (IUD) or intrauterine system (IUS) Barrier methods of contraception: Condom or Occlusive cap diaphragm or cervical/vault caps) with spermicidal foam/gel/film/cream/vaginal suppository In case of use of oral contraception women should have been stable on the same pill for a minimum of 3 months before taking study treatment Sexually active males unless they use a condom during intercourse while taking drug and for 1 months after pasireotide s.c. last dose and 3 months after pasireotide LAR last dose and should not father a child in this period. A condom is required to be used also by vasectomized men in order to prevent delivery of the drug via seminal fluid If a study patient or partner becomes pregnant or suspects being pregnant during the study or within 1 month after the final dose of pasireotide s.c. or 3 months after the final dose of pasireotide LAR, the Study Doctor needs to be informed immediately and ongoing study treatment with pasireotide has to be stopped immediately For patients taking pasireotide LAR, the future dose injections will be cancelled.", "candidate_expression": "((Condom) AND (IUD) AND (IUS) AND (Male sterilization) AND (Occlusive cap diaphragm) AND (Patient has participated in a Novartis sponsored combination trial where pasireotide was dispensed in combination with another study medication and is still receiving combination therapy. (only patients receiving pasireotide monotherapy can be included)) AND (Total abstinence (when this is in line with the preferred and usual lifestyle of the subject. Periodic abstinence (e.g., calendar, ovulation, symptothermal, post-ovulation methods) and withdrawal are not acceptable methods of contraception) AND (at least 6 months prior to screening) AND (at least six weeks before taking study treatment) AND (bilateral oophorectomy) AND (cervical caps) AND (contraception) AND (hysterectomy) AND (nant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test) AND (screening) AND (spermicidal foam) AND (taking study treatment) AND (vault caps) AND ((hormone vaginal ring) OR (transdermal hormone contraception)) AND ((intrauterine device) OR (intrauterine system)) AND ((Female sterilization) OR (tubal ligation)))"}
{"candidate_id": "LLM02022", "doc_id": "NCT03026088_inc", "case_bucket": "or", "source_criterion": "18-80 year, male or female. Chronic Heart failure subjects with medical history of cardiac disease or other related cardiovascular disease. Left ventricular ejection fraction (LVEF) less than or equal to (=<) 40 percent (%). New York Heart Association (NYHA) class of II - IV NYHA II : Slight limitation of physical activity. Comfortable at rest, but ordinary physical activity results in undue breathlessness, fatigue or palpitation. NYHA III:Marked limitation of physical activity. Comfortable at rest, but less than ordinary activity causes undue breathlessness, fatigue or palpitation. NYHA IV:Unable to carry on any physical activity without discomfort. Symptoms at rest can be present. If any physical activity is undertaken, discomfort increased. Signed Informed Consent Form (ICF).", "candidate_expression": "((18-80) AND (=< 40 %) AND (Chronic Heart failure) AND (II - IV) AND (LVEF) AND (Left ventricular ejection fraction) AND (NYHA) AND (New York Heart Association class) AND (Signed Informed Consent Form (ICF)) AND (less than or equal to 40 percent) AND (related) AND (year) AND ((female) OR (male)) AND ((cardiac disease) OR (cardiovascular disease)))"}
{"candidate_id": "LLM02023", "doc_id": "NCT02749617_inc", "case_bucket": "other", "source_criterion": "Patients with diagnosis of multiple myeloma according to criteria of the International Myeloma Working Group Patients in whom a LEN-DEX-based treatment regimen is indicated Adult patients ≥ 19 years of age who are able to freely provide informed consent", "candidate_expression": "((Adult) AND (DEX) AND (LEN) AND (able to freely provide informed consent) AND (age ≥ 19 years) AND (criteria of the International Myeloma Working Group) AND (multiple myeloma) AND (treatment regimen LEN-DEX-based is indicated))"}
{"candidate_id": "LLM02024", "doc_id": "NCT02251249_exc", "case_bucket": "or", "source_criterion": "Allergy or contraindication to paracetamol, Prasugrel or Ticagrelor Paracetamol ingestion in the previous 48 hours Patient treated with drugs supposed to alter gastric emptying times (calcium antagonists, Alimentary tract treatments, opioid analgesics, tricyclic antidepressants, antibiotics). Conditions or pathologies supposed to alter gastric emptying times (Thyroid dysfunction, chronic renal failure, Parkinson's disease, scleroderma, amyloidosis, any gastrointestinal disease, any not cured malignancy, and any advanced psychiatric or neurological disease). Presence of vomiting Cardiogenic shock, ventricular arrhythmia or resuscitated cardiac arrest Hepatic insufficiency Severe respiratory disease Pregnant or breastfeeding women", "candidate_expression": "((Alimentary tract treatments) AND (Allergy) AND (Cardiogenic shock) AND (Conditions supposed to alter gastric emptying times) AND (Hepatic insufficiency) AND (Paracetamol in the previous 48 hours) AND (Parkinson's disease) AND (Prasugrel) AND (Pregnant) AND (Thyroid dysfunction) AND (Ticagrelor) AND (amyloidosis) AND (antibiotics) AND (breastfeeding) AND (calcium antagonists) AND (cardiac arrest resuscitated) AND (chronic renal failure) AND (contraindication) AND (drugs supposed to alter gastric emptying times) AND (gastrointestinal disease) AND (malignancy) AND (neurological disease) AND (opioid analgesics) AND (paracetamol) AND (pathologies supposed to alter gastric emptying times) AND (psychiatric disease) AND (respiratory disease Severe) AND (scleroderma) AND (tricyclic antidepressants) AND (ventricular arrhythmia) AND (vomiting) AND (women))"}
{"candidate_id": "LLM02025", "doc_id": "NCT00425789_inc", "case_bucket": "other", "source_criterion": "The study will include 40 post-deep peel women (exoderm), older than 18 years old, treated by the same dermatologist (dr. Landau). The treatment group will receive 5 consecutive daily hyperbaric treatments, 1 hours long each, at 2 ATF, starting from day 7 to peel. Prior to treatment, each patient will be signed on informed consent and will have complete physical examination. The control group will be matched by the following parameters: age, skin color and type, and indication for peeling, and will be picked up by the dermatologist.", "candidate_expression": "((age) AND (control group) AND (deep peel) AND (exoderm) AND (old) AND (older than 18 years) AND (skin color) AND (type) AND (women))"}
```
