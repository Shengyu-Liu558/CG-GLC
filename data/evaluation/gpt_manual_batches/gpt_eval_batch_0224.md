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
{"candidate_id": "LLM05576", "doc_id": "NCT02467686_exc", "case_bucket": "or", "source_criterion": "Women did not have breast cancer do not use tamoxifen or aromatase inhibitor not in menopause and not have hot flashes", "candidate_expression": "((breast cancer) AND (not) AND ((hot flashes) OR (menopause)) AND ((aromatase inhibitor) OR (tamoxifen)))"}
{"candidate_id": "LLM05577", "doc_id": "NCT02260206_inc", "case_bucket": "or", "source_criterion": "Patients needed to pericardiocentesis during RFCA for paroxysmal or persistent atrial fibrillation.", "candidate_expression": "((RFCA) AND (atrial fibrillation) AND (during RFCA) AND (pericardiocentesis) AND ((paroxysmal) OR (persistent)))"}
{"candidate_id": "LLM05578", "doc_id": "NCT03196843_inc", "case_bucket": "or", "source_criterion": "Before participate in the study, patients must understand the treatment plan and willing to participate in the study. Patients must have signed an approved informed consent. Histopathologic confirmed squamous cell carcinoma of head and neck ,including oral cavity, oropharynx, larynx, or hypopharynx. Ages=65 years,Not limited to gender. ECOG performance status =2. Patients with surgical contraindication or reject to surgery. Postoperative TNM(primary tumor,regional nodes,metastasis) staging III~IV, positive surgical margin. without evidence of distant metastases. No contraindication to chemoradiotherapy. Life expectancy > 3 months. Available Organ function: white blood cell=3.5×109/L, Neutrophils =1.5×109/L, Hemoglobin =80g/L, Blood platelet>100×109/L; Alanine aminotransferase (ALT) and Aspartate aminotransferase (AST)= 2.5 upper limit of normal(ULN); Total bilirubin (TBIL) <1.5 ULN;serum creatinine=1.5 ULN; creatinine clearance of = 50ml/min", "candidate_expression": "((Ages =65 years) AND (Alanine aminotransferase (ALT) = 2.5 upper limit of normal(ULN)) AND (Aspartate aminotransferase (AST) = 2.5 upper limit of normal(ULN)) AND (Before participate in the study, patients must understand the treatment plan and willing to participate in the study. Patients must have signed an approved informed consent.) AND (Blood platelet >100×109/L) AND (ECOG performance status =2) AND (Hemoglobin =80g/L) AND (Histopathologic) AND (Life expectancy > 3 months) AND (Neutrophils =1.5×109/L) AND (TNM staging Postoperative III~IV,) AND (Total bilirubin (TBIL) <1.5 ULN) AND (chemoradiotherapy) AND (creatinine clearance = 50ml/min) AND (serum creatinine =1.5 ULN) AND (squamous cell carcinoma Histopathologic confirmed head and neck) AND (surgery) AND (surgical) AND (surgical margin positive) AND (white blood cell =3.5×109/L) AND NOT (distant metastases evidence) AND NOT (contraindication) AND ((contraindication) OR (reject)) AND ((hypopharynx) OR (larynx) OR (oral cavity) OR (oropharynx)))"}
{"candidate_id": "LLM05579", "doc_id": "NCT01701219_inc", "case_bucket": "or", "source_criterion": "1. Presence of bacteremia due solely to: S. aureus on at least 1 blood culture within 72 hours of beginning study drug (Cohort A) OR MRSA on a baseline blood culture and on at least 1 additional blood culture after at least 72 hours of vancomycin and/or daptomycin treatment (Cohort B). 2. Male or female ≥ 18 years of age. 3. If female of childbearing potential must be willing to practice sexual abstinence or dual methods of contraception during treatment and for at least 30 days after the last dose of study drug. 4. Expectation of survival for at least 2 months.", "candidate_expression": "((age ≥ 18 years) AND (bacteremia) AND (blood culture MRSA baseline) AND (blood culture S. aureus at least 1 within 72 hours of beginning study drug) AND (blood culture at least 1 additional after at least 72 hours of vancomycin and/or daptomycin treatment) AND (childbearing potential) AND (daptomycin) AND (female) AND (survival Expectation for at least 2 months the last dose of study drug) AND (vancomycin vancomycin and/or daptomycin treatment) AND ((daptomycin treatment) OR (vancomycin treatment)) AND ((Male) OR (female)) AND ((methods of contraception dual) OR (practice sexual abstinence)))"}
{"candidate_id": "LLM05580", "doc_id": "NCT01815580_exc", "case_bucket": "or", "source_criterion": "Prior receipt of investigational anti-HIV vaccine Ongoing therapy with any of the following: Systemic corticosteroids. Short course less than or equal to 21 days of corticosteroids is allowed; Systemic chemotherapeutic agents; Nephrotoxic systemic agents, including aminoglycosides, amphotericin B, cidofovir, cisplatin, foscarnet, pentamidine; Immunomodulatory treatments including Interleukin-2; Investigational agents Known allergy/sensitivity or any hypersensitivity to components of study drugs (ART) or their formulations Active drug or alcohol use or dependence that would interfere with adherence to study requirements Serious medical or psychiatric illness that would interfere with the ability to adhere to study requirements Chronic or acute hepatitis B infection Use of female hormonal products based on estrogen or derivatives", "candidate_expression": "((ART) AND (Chronic hepatitis B infection) AND (Interleukin-2) AND (acute hepatitis B infection) AND (anti-HIV vaccine Prior investigational) AND (female hormonal products) AND (therapy Ongoing) AND NOT (corticosteroids Short course less than or equal to 21 days) AND ((Immunomodulatory treatments) OR (Investigational agents) OR (Nephrotoxic systemic agents) OR (Systemic chemotherapeutic agents) OR (Systemic corticosteroids) OR (aminoglycosides) OR (amphotericin B) OR (cidofovir) OR (cisplatin) OR (foscarnet) OR (pentamidine)) AND ((allergy) OR (hypersensitivity) OR (sensitivity)) AND ((components of study drugs) OR (or their formulations)) AND ((alcohol dependence) OR (alcohol use) OR (drug dependence) OR (use)) AND ((medical illness) OR (psychiatric illness)) AND ((estrogen) OR (estrogen derivatives)))"}
{"candidate_id": "LLM05581", "doc_id": "NCT02570230_inc", "case_bucket": "other", "source_criterion": "ASA physical status 1-3 elective thoracotomy can operate patient-controlled analgesia (PCA) machine", "candidate_expression": "((1-3) AND (ASA physical status) AND (elective) AND (thoracotomy))"}
{"candidate_id": "LLM05582", "doc_id": "NCT00926523_exc", "case_bucket": "other", "source_criterion": "Subject are pregnant Subject is unable to perform tasks associated with study", "candidate_expression": "((Subject is unable to perform tasks associated with study) AND (pregnant))"}
{"candidate_id": "LLM05583", "doc_id": "NCT02072811_exc", "case_bucket": "other", "source_criterion": "No informed consent for participation in the study, mental illness, which don't allow to obtain informed consent and conduct the treatment according to the protocol Pregnancy HIV infection Active cancer Active hepatitis virus infection", "candidate_expression": "((HIV infection) AND (Pregnancy) AND (cancer Active) AND (hepatitis virus infection Active))"}
{"candidate_id": "LLM05584", "doc_id": "NCT01602081_exc", "case_bucket": "or", "source_criterion": "Patients with prior fistulotomy, fistulectomy, LIFT, cutting seton or advancement flap procedure Fistula with multiple tracts Recto-vaginal fistula Active infection in the anal fistula Physical allergies or cultural objections to porcine products Patient is not medically fit to undergo the LIFT procedure as judged by the treating physician Previous diagnosis of collagen disorder History of Crohn's Disease, Irritable Bowel Syndrome, radiation therapy in the rectoanal region", "candidate_expression": "((Fistula multiple tracts) AND (LIFT) AND (Patient is not medically fit to undergo the LIFT procedure as judged by the treating physician) AND (Recto-vaginal fistula) AND (advancement flap procedure) AND (anal fistula) AND (collagen disorder) AND (cutting seton) AND (fistulectomy) AND (fistulotomy) AND (infection in the anal fistula) AND ((Crohn's Disease) OR (Irritable Bowel Syndrome) OR (radiation therapy rectoanal region)))"}
{"candidate_id": "LLM05585", "doc_id": "NCT02408120_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05586", "doc_id": "NCT02092467_exc", "case_bucket": "or", "source_criterion": "Current or recent infection Clinically significant laboratory abnormalities Pregnancy", "candidate_expression": "((Pregnancy) AND (infection Current recent) AND (laboratory) AND (laboratory abnormalities Clinically significant))"}
{"candidate_id": "LLM05587", "doc_id": "NCT01314898_exc", "case_bucket": "or", "source_criterion": "Subjects with a supine BP >140 mm Hg systolic or >90 mm Hg diastolic or <100 mm Hg systolic or <60 mm Hg diastolic based on the average of the triplicate Serum potassium >=5.1 mmol/L or <3.5 mmol/L at screening, confirmed by a single repeat if deemed necessary. Estimated GFR <60 mL/min/1.73 m2 using the Cockcroft-Gault formula measurement of the individual parameters following at least 5 minutes of rest at Screening.", "candidate_expression": "((Estimated GFR <60 mL/min/1.73 m2 Cockcroft-Gault formula) AND (Serum potassium at screening) AND (supine BP) AND ((<100 mm Hg systolic) OR (<60 mm Hg diastolic) OR (>140 mm Hg systolic) OR (>90 mm Hg diastolic)) AND ((<3.5 mmol/L) OR (>=5.1 mmol/L)))"}
{"candidate_id": "LLM05588", "doc_id": "NCT02874092_exc", "case_bucket": "or", "source_criterion": "History of sensitivity to study medications or any of their excipients RA cohort: Previous intolerance to MTX Current treatment with antiplatelet therapy Absolute indication for anti-platelet therapy Need for chronic oral anticoagulant therapy Severe hepatic impairment (eg, ascites and/or clinical signs of coagulopathy) Renal failure (eGFR <30 or requiring dialysis) A known bleeding diathesis, hemostatic or coagulation disorder, or prior major bleeding Prior stroke Active pathological bleeding History of intracranial haemorrhage Life expectancy <12 months based on investigator's judgement Patients considered to be at risk of bradycardic events (e.g., known sick sinus syndrome or second or third degree atrioventricular [AV)] block) unless already treated with a permanent pacemaker Anemia (hematocrit < 27%) Platelet count < 100,000/ml Concomitant use of strong CYP 3A inhibitors or inducers History of thrombocytopenia or neutropenia Pregnant or nursing women, or females with a positive pregnancy test at screening Females of child bearing potential not using acceptable method of birth control prior to or during study Concern for inability of the patient to comply with study procedures and/or follow up (eg, alcohol or drug abuse)", "candidate_expression": "((< 100,000/ml) AND (< 27%) AND (<12 months) AND (<30) AND (Absolute indication for) AND (Active) AND (Anemia) AND (Concern for) AND (Current) AND (Females) AND (History) AND (Life expectancy) AND (MTX) AND (Need for) AND (Platelet count) AND (Pregnant) AND (Prior) AND (RA) AND (Renal failure) AND (Severe hepatic impairment) AND (acceptable) AND (alcohol abuse) AND (anti-platelet therapy) AND (antiplatelet therapy) AND (ascites) AND (at risk of) AND (at screening) AND (bleeding diathesis) AND (bradycardic events) AND (child bearing potential) AND (chronic oral anticoagulant therapy) AND (clinical signs of) AND (coagulation disorder) AND (coagulopathy) AND (dialysis) AND (drug abuse) AND (during study) AND (eGFR) AND (females) AND (hematocrit) AND (hemostatic disorder) AND (inability to comply with follow up) AND (inability to comply with study procedures) AND (intolerance) AND (intracranial haemorrhage) AND (major bleeding) AND (method of birth control) AND (neutropenia) AND (not) AND (nursing) AND (pathological bleeding) AND (permanent pacemaker) AND (positive) AND (pregnancy test) AND (prior) AND (prior to study) AND (requiring) AND (screening) AND (second degree atrioventricular [AV)] block) AND (sensitivity) AND (sick sinus syndrome) AND (stroke) AND (strong CYP 3A inducers) AND (strong CYP 3A inhibitors) AND (study medications) AND (third degree atrioventricular [AV)] block) AND (thrombocytopenia) AND (unless) AND (women))"}
{"candidate_id": "LLM05589", "doc_id": "NCT00401245_exc", "case_bucket": "or", "source_criterion": "History of a seizure disorder other than a single childhood febrile seizure. History or presence of clinically important hepatic or renal disease or other medical disease. Presence or recent history of major depressive disorder, bipolar disorder, psychotic disorder, or generalized anxiety disorder requiring therapy.", "candidate_expression": "((seizure disorder History) AND NOT (childhood febrile seizure single) AND ((bipolar disorder) OR (generalized anxiety disorder) OR (major depressive disorder) OR (psychotic disorder)) AND ((clinically important hepatic disease) OR (clinically important other medical disease) OR (clinically important renal disease)))"}
{"candidate_id": "LLM05590", "doc_id": "NCT02227992_inc", "case_bucket": "or", "source_criterion": "Paediatric subjects aged =28 days (= 1 month) to <18 years, requiring non-emergent open hepatic, abdominal, retroperitoneal, pelvic or thoracic (non-cardiac) surgical procedures. i) The first 36 subjects to be enrolled will be subjects aged =1 years to <18 years. ii) The next 4 subjects to be enrolled will be subjects aged =28 days to <1 year. The subject's parent/legal guardian must be willing to give permission for the subject to participate in the trial, and provide written informed consent for the subject. In addition, assent must be obtained from paediatric subjects who possess the intellectual and emotional ability to comprehend the concepts involved in the trial. If the paediatric subject is not able to provide assent (due to age, maturity and/or inability to intellectually and/or emotionally comprehend the trial), the parent/legal guardian's written Informed Consent for the subject will be acceptable for the subject to be included in the study. Presence of an appropriate mild or moderate bleeding soft tissue or hepatic parenchyma Target Bleeding Site (TBS) identified intra-operatively by the surgeon; Ability to firmly press trial treatment at TBS until 4 minutes after randomisation", "candidate_expression": "((Ability to firmly press trial treatment at TBS until 4 minutes after randomisation) AND (The subject's parent/legal guardian must be willing to give permission for the subject to participate in the trial, and provide written informed consent for the subject. In addition, assent must be obtained from paediatric subjects who possess the intellectual and emotional ability to comprehend the concepts involved in the trial. If the paediatric subject is not able to provide assent (due to age, maturity and/or inability to intellectually and/or emotionally comprehend the trial), the parent/legal guardian's written Informed Consent for the subject will be acceptable for the subject to be included in the study) AND (aged =28 days (= 1 month) to <18 years hepatic abdominal) AND (surgical procedures non-emergent open retroperitoneal pelvic thoracic non-cardiac))"}
{"candidate_id": "LLM05591", "doc_id": "NCT02918851_inc", "case_bucket": "other", "source_criterion": "Habitual exerciser defined as = 30 minutes of at least moderate or high intensity exercise = 3 times per week. After consent, and at the subsequent screening visit, a VO2 max test will be performed, and subjects with a low value (< 35 mL/kg/min) will be excluded (screen failure). Based on our previous experience, we anticipate that <10% of the subjects will fall into this category Men: (0.006012 x H3) + (14.6 x W) + 604 = TBV Women: (0.005835 x H3) + (15 x W) + 183 = TBV [H=height in inches; W=weight in pounds] Has access to transportation to visit the blood collection facility and to return to Stony Brook for all study visits.", "candidate_expression": "(((0.005835 x H3) + (15 x W) + 183) AND ((0.006012 x H3) + (14.6 x W) + 604 =) AND (Men) AND (TBV) AND (Women))"}
{"candidate_id": "LLM05592", "doc_id": "NCT03046108_inc", "case_bucket": "other", "source_criterion": "Clinical suspicion of Morton neuroma confirmed in ultrasound scan Symptoms present more than six months The thickness of the nerve must be at least 2 mm in short axis and at least 5 mm in the longitudinal axis.", "candidate_expression": "((Clinical suspicion) AND (Morton neuroma) AND (Symptoms) AND (at least 2 mm) AND (at least 5 mm) AND (more than six months) AND (thickness of the nerve in short axis) AND (thickness of the nerve in the longitudinal axis) AND (ultrasound scan))"}
{"candidate_id": "LLM05593", "doc_id": "NCT02260700_exc", "case_bucket": "or", "source_criterion": "Participant has a clinically significant abnormal physical examination, vital signs or 12 lead ECG (including QTc greater than (>) 450msec, Left Bundle Branch Block, permanent pacemaker or implantable cardioverter defibrillator) at Screening or admission Participant has a history of or current liver or renal insufficiency; significant cardiac, vascular, pulmonary, gastrointestinal, endocrine, neurologic, hematologic, rheumatologic, psychiatric, or metabolic disturbances Use of any prescription or over-the-counter medication, herbal medication, vitamins, or mineral supplements within 14 days prior to study drug administration (not including paracetamol). Medication for chronic use in age related disease will be allowed after approval by both the investigator and to the sponsor. No change in dose or regimen will be permitted during the study that is, from the Screening visit until the follow-up visit Participant has a history of spontaneous, prolonged or severe bleeding of unclear origin Participant has a history of epilepsy or fits or unexplained black-outs other than vasovagal collapse", "candidate_expression": "((Left Bundle Branch Block) AND (Medication) AND (QTc) AND (Screening) AND (abnormal 12 lead ECG) AND (abnormal physical examination) AND (abnormal vital signs) AND (admission) AND (age related disease) AND (any prescription) AND (approval by both the investigator and to the sponsor) AND (at Screening or admission) AND (black-outs) AND (bleeding) AND (cardiac disturbances) AND (chronic use) AND (clinically significant) AND (endocrine disturbances) AND (epilepsy) AND (fits) AND (gastrointestinal disturbances) AND (greater than (>) 450msec) AND (hematologic disturbances) AND (herbal medication) AND (history) AND (implantable cardioverter defibrillator) AND (liver insufficiency) AND (metabolic disturbances) AND (mineral supplements) AND (neurologic disturbances) AND (not) AND (other than) AND (over-the-counter medication) AND (paracetamol) AND (permanent pacemaker) AND (prolonged) AND (psychiatric disturbances) AND (pulmonary disturbances) AND (renal insufficiency) AND (rheumatologic disturbances) AND (severe) AND (significant) AND (spontaneous) AND (study drug administration) AND (unclear origin) AND (unexplained) AND (vascular disturbances) AND (vasovagal collapse) AND (vitamins) AND (within 14 days prior to study drug administration))"}
{"candidate_id": "LLM05594", "doc_id": "NCT03278548_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05595", "doc_id": "NCT00994786_exc", "case_bucket": "or", "source_criterion": "Patients with any other primary DSM-IV psychiatric diagnosis in addition to Obsessive Compulsive Disorder. Patients who currently fulfil criteria for DSM-IV eating disorder, body dysmorphic disorder, current alcohol or substance abuse, or who have a lifetime history of bipolar disorder. Patients with a history of Schizophrenia and other psychotic disorders, Delirium, Dementia, and Amnestic and other cognitive disorders. Subjects with a concurrent Axis II Cluster A Personality Disorder Borderline or Antisocial Personality Disorder. Subjects who based on history or mental status examination have a significant risk of committing suicide, in the investigator's opinion. Subjects with a history of more than three adequate trials with an SSRI. Subjects who have had an adequate trial of pregabalin. Subjects who have initiated psychotherapy in the last 4 months prior to the first visit. Subjects who, during the course of the study, would be likely to require treatment with prohibited concomitant therapy . Prior use of or a known allergy or hypersensitivity to pregabalin. Subjects who have participated in any clinical trial within 30 days prior to entering the study, or in a clinical trial involving a psychotropic medication within the 6 months prior to entering the study. Any subject who has been taking benzodiazepines before entering the study who: 1) cannot tolerate being free of benzodiazepines for 4 weeks, or 2) has signs or symptoms of benzodiazepine withdrawal or rebound at the end of those 4 weeks. Should a patient entering the study, who is currently on benzodiazepines develop discontinuation symptoms with discontinuation of their benzodiazepine, we will treat these symptoms with a more gradual benzodiazepine taper. Study will be delayed until the patient is able to tolerate the discontinuation for 4 weeks. Patients with a current seizure disorder, organic brain disorder or a history of seizure disorders (except for febrile seizures in childhood). Patients with thyroid pathology, the treatment of which has not been stabilized for at least three months. Patients on neuroleptic drugs in the two months prior to study entry or cognitive behavioural therapy specific to OCD within four weeks of study entry Pregnant or lactating females, or if sexually active and of childbearing potential, not using adequate methods of birth control. Patients with a history or evidence of a medical condition that would expose them to an increased risk of a significant adverse event or interfere with assessments of safety and efficacy during the trial. Patients receiving psychotropics of any kind, including betablockers and other anticonvulsants. Sleep medication such as oral chloral-hydrate or zopiclone are acceptable. Patients using any herbal psychoactive treatments, e.g. St John's Wort, Valerian, Kava Kava, L-tryptophan. Patients with any condition or on any therapy that, in the investigator's opinion, or as indicated in the pregabalin product label, may pose a risk to the subject. Patients who have had a major life event in the past three months, which in the judgement of the investigator is influencing their current condition. Patients having clinically significant abnormal laboratory, or ECG findings not resolved by further examinations.", "candidate_expression": "((OCD) AND (Personality Disorder Axis II Cluster A) AND (Pregnant or lactating females, or if sexually active and of childbearing potential, not using adequate methods of birth control) AND (Subjects who have had an adequate trial of pregabalin) AND (Subjects who have participated in any clinical trial within 30 days prior to entering the study, or in a clinical trial involving a psychotropic medication within the 6 months prior to entering the study.) AND (Subjects with a history of more than three adequate trials with an SSRI) AND (herbal psychoactive treatments) AND (mental status examination) AND (pregabalin) AND (psychiatric diagnosis any other primary DSM-IV) AND (psychotherapy in the last 4 months prior to the first visit) AND (psychotropics) AND (risk of committing suicide significant) AND (thyroid pathology) AND (treatment stabilized at least three months) AND NOT (Obsessive Compulsive Disorder) AND NOT (febrile seizures childhood) AND NOT (Sleep medication) AND ((alcohol abuse) OR (body dysmorphic disorder) OR (eating disorder) OR (substance abuse)) AND ((Amnestic) OR (Delirium) OR (Dementia) OR (Schizophrenia) OR (bipolar disorder) OR (cognitive disorders other) OR (psychotic disorders other)) AND ((Antisocial Personality Disorder) OR (Borderline Personality Disorder)) AND ((allergy) OR (hypersensitivity)) AND ((history of seizure disorders) OR (organic brain disorder) OR (seizure disorder)) AND ((cognitive behavioural therapy within four weeks of study entry) OR (neuroleptic drugs in the two months prior to study entry)) AND ((anticonvulsants) OR (betablockers)) AND ((chloral-hydrate oral) OR (zopiclone)) AND ((Kava Kava) OR (L-tryptophan) OR (St John's Wort) OR (Valerian)) AND ((ECG findings) OR (laboratory findings)))"}
{"candidate_id": "LLM05596", "doc_id": "NCT02678728_inc", "case_bucket": "other", "source_criterion": "Patients undergoing thoracic aorta surgery with hypothermic circulatory arrest, over 20-of age", "candidate_expression": "((age over 20) AND (hypothermic circulatory arrest) AND (surgery thoracic aorta))"}
{"candidate_id": "LLM05597", "doc_id": "NCT03073603_inc", "case_bucket": "or", "source_criterion": "Patients with either Relapsing-remitting MS (RRMS), Secondary progressive MS (SPMS), or Primary progressive MS (PPMS) by McDonald 2010 criteria. Patients defined by subtype based on 2013 updated phenotypic criteria. prospectively with an EDSS change of at least 1.0 points over the last two years, or retrospectively, with any significant change in motor function over at least one year, unrelated to relapse. 55 years of age or older at time of randomization; No evidence of recent new inflammatory disease activity (inactive by the Lublin criteria16) with no new relapse for at least five years and no new MRI lesion for at least three years interferon ß-1a, interferon ß-1b, glatiramer acetate, natalizumab, fingolimod, dimethyl fumarate, or teriflunomide; continuously for no less than 5 years. Taking most recent DMT continuously* for no less than two years. Willing to be randomized per this protocol; each patient will be questioned as to their willingness to stay in the trial regardless of the group to which group they are randomized. Willing to follow the protocol Continuously will be defined as no less than 75% of all prescribed doses, with no time of greater than four weeks from last intended dose to have missed a dose (8 weeks for natalizumab, i.e. one missed dose).", "candidate_expression": "((DMT continuously for no less than two years) AND (EDSS change at least 1.0 points over the last two years) AND (Lublin criteria inactive) AND (MRI) AND (Primary progressive MS (PPMS)) AND (Relapsing-remitting MS (RRMS)) AND (Secondary progressive MS (SPMS)) AND (Willing to be randomized per this protocol; each patient will be questioned as to their willingness to stay in the trial regardless of the group to which group they are randomized.) AND (Willing to follow the protocol) AND (age 55 years or older at time of randomization) AND (change in motor function significant over at least one year unrelated to relapse) AND (dimethyl fumarate) AND (fingolimod) AND (glatiramer acetate) AND (interferon ß-1a) AND (interferon ß-1b) AND (natalizumab) AND (teriflunomide continuously for no less than 5 years) AND NOT (inflammatory disease new) AND NOT (relapse new for at least five years) AND NOT (lesion new for at least three years))"}
{"candidate_id": "LLM05598", "doc_id": "NCT02833623_exc", "case_bucket": "or", "source_criterion": "advanced chronic disease that would not allow the patient to complete the treatment or follow-up or attend visits allergy to any of the drugs used in this study previous Helicobacter Pylori eradication treatment pregnancy or breastfeeding (female participants with childbearing potential were required to use medically accepted contraception for the duration of the study) taking antibiotics or PPIs or bismuth salts within four weeks previous gastrointestinal surgery", "candidate_expression": "((Helicobacter Pylori eradication treatment) AND (PPIs) AND (antibiotics) AND (bismuth salts) AND (gastrointestinal surgery) AND (pregnancy or breastfeeding (female participants with childbearing potential were required to use medically accepted contraception for the duration of the study)))"}
{"candidate_id": "LLM05599", "doc_id": "NCT02774317_exc", "case_bucket": "or", "source_criterion": "Patients who are being prepared for surgery, or during or after surgery. Patients with congenital anomalies, chromosomal anomalies, or heart defects. Patients whose parents refuse to consent.", "candidate_expression": "(((after surgery) OR (during surgery) OR (surgery being prepared for)) AND ((chromosomal anomalies) OR (congenital anomalies) OR (heart defects)))"}
{"candidate_id": "LLM05600", "doc_id": "NCT01943409_inc", "case_bucket": "or", "source_criterion": "Patients with PN during their hospitalization Patients hospitalized in medical, surgical or ICU wards Signed informed consent either from the patient, their legally authorized representative or a direct family member", "candidate_expression": "((ICU wards) AND (PN) AND (Signed informed consent either from the patient, their legally authorized representative or a direct family member) AND (during their hospitalization) AND (hospitalization) AND (hospitalized) AND (medical wards) AND (surgical wards) AND (their hospitalization))"}
```
