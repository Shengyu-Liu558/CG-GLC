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
{"candidate_id": "LLM02426", "doc_id": "NCT02842424_exc", "case_bucket": "or", "source_criterion": "Rest pain or tissue loss due to PAD (Fontaine stage III and IV), acute lower extremity ischemic event secondary to thromboembolic disease or acute trauma, Walking capacity significantly limited by conditions other than claudication including leg (joint/musculoskeletal, neurologic) and systemic (heart, lung disease) pathology, Current use of either ACE inhibitors or angiotensin II receptor blockers, Chronic kidney disease with estimated Glomerular Filtration Rate < 30 ml/min/1.73 m2, History of bilateral severe renal artery stenosis and 7) History of angioedema related to previous ACE-inhibitor treatment or known hypersensitivity to ramipril or other ACE inhibitors.", "candidate_expression": "((ACE inhibitors) AND (ACE-inhibitor) AND (ACE-inhibitor treatment previous) AND (Chronic kidney disease) AND (Fontaine stage III IV) AND (PAD) AND (Rest pain) AND (Walking capacity significantly limited) AND (acute trauma) AND (angioedema History) AND (angiotensin II receptor blockers) AND (conditions other than claudication other than claudication joint musculoskeletal neurologic) AND (estimated Glomerular Filtration Rate < 30 ml/min/1.73 m2) AND (heart disease) AND (hypersensitivity known) AND (ischemic event acute lower extremity secondary to thromboembolic disease secondary to acute trauma) AND (leg pathology) AND (lung disease) AND (ramipril) AND (renal artery stenosis History bilateral severe) AND (systemic pathology) AND (thromboembolic disease) AND (tissue loss) AND NOT (claudication))"}
{"candidate_id": "LLM02427", "doc_id": "NCT00862446_inc", "case_bucket": "other", "source_criterion": "Infants in the newborn intensive care unit TPN cholestasis of at least 2.5 mg/dl Anticipated TPN treatment for at least one month signed informed consent", "candidate_expression": "((Infants) AND (TPN cholestasis at least 2.5 mg/dl) AND (TPN treatment for at least one month) AND (newborn intensive care unit) AND (signed informed consent))"}
{"candidate_id": "LLM02428", "doc_id": "NCT01709981_inc", "case_bucket": "other", "source_criterion": "Patients must be more than 18 years of age and referred for coronary angiography", "candidate_expression": "((age more than 18 years) AND (coronary angiography referred for))"}
{"candidate_id": "LLM02429", "doc_id": "NCT02558504_inc", "case_bucket": "or", "source_criterion": "Age over 18 years, General Condition WHO 0, 1 or 2, ASA Class I and II, eligible for endoscopic or surgical treatment with curative intent, Histological diagnosis of high grade glandular epithelial neoplasia (Vienna 4-1 to 4-46), possibly multifocal or stage 0 (Tis, N0, M0), Endoscopic and histological confirmed diagnosis of intestinal metaplasia, Histological diagnosis confirmed by two endoscopies with biopsies and two pathological readings; biopsies should be carried out according to the protocol of the SFED (four-quadrant biopsies every cm) with at least once acetic acid for staining. Operators describe Barrett's esophagus using he SFED planimetric model. The final exam will be no more than two months before the date of treatment and should have been achieved in investigator establishment, Minimum 1 cm, Maximum 12 cm. the resected lesion must have been well differentiated and confined to the mucosa (m2 maximum) on histological analysis, resection should be more than two months, resection must have been macroscopically complete laterally, resection must have been histologically complete in depth, resection must have been histologically complete laterally with regard to the microinvasive cancer, that is to say with a clear margin of safety (margin may be high-grade dysplasia provided that the latter has not macroscopic translation), At least one endoscopic and histologic follow-up should be conducted with dye in a period of less than two months before the date of treatment, and at the investigator establishment. Patient may take an inhibitor of proton pump equivalent to 2 times 40 mg of esomeprazole, No mediastinal or celiac, or suspected metastatic lymph nodes by EUS, Affiliation to a social security system or similar, Lack of participation in another clinical study, Informed consent signed.", "candidate_expression": "((0) AND (4-1 to 4-46) AND (ASA Class) AND (Affiliation to a social security system) AND (Age) AND (EUS) AND (Endoscopic) AND (General Condition WHO) AND (Histological) AND (Histological diagnosis) AND (Informed consent signed) AND (Lack of) AND (M) AND (N) AND (No) AND (T) AND (Vienna) AND (another) AND (biopsies) AND (celiac) AND (complete in depth) AND (complete laterally) AND (confined to the mucosa) AND (diagnosis) AND (eligible for) AND (endoscopies) AND (glandular epithelial neoplasia) AND (high grade) AND (histological) AND (histological analysis) AND (histologically) AND (intestinal metaplasia) AND (is) AND (lymph nodes) AND (m2 maximum) AND (macroscopically complete laterally) AND (mediastinal) AND (metastatic) AND (microinvasive cancer) AND (more than two months) AND (multifocal) AND (over 18 years) AND (participation in clinical study) AND (pathological readings) AND (resected lesion) AND (resection) AND (stage) AND (two) AND (well differentiated) AND (with curative intent) AND ((surgical treatment) OR (treatment endoscopic)) AND ((Endoscopic confirmed) OR (histological confirmed)) AND ((0) OR (1) OR (2)) AND ((I) OR (II)))"}
{"candidate_id": "LLM02430", "doc_id": "NCT02790593_exc", "case_bucket": "or", "source_criterion": "Age less than 18 years Significant arterial disease (Ankle Brachial Pressure Index <0•9 or evidence on Arterial Duplex) Acute Deep Vein Thrombosis Patient unable or unwilling to have high compression (30mmHg minimum) Patients with dexterity insufficiency of hands Patients with peripheral neuropathy Leg ulcers of another underlying cause Leg ulcers of greater than 1 year duration Patients unable or unwilling to provide written, informed consent", "candidate_expression": "((Acute Deep Vein Thrombosis) AND (Age less than 18 year) AND (Ankle Brachial Pressure Index <0•9) AND (Arterial Duplex) AND (Leg ulcers) AND (Leg ulcers greater than 1 year duration) AND (Patient unable or unwilling to have high compression (30mmHg minimum)) AND (Patients unable or unwilling to provide written, informed consent) AND (arterial disease Significant) AND (dexterity insufficiency of hands) AND (peripheral neuropathy) AND (underlying cause another))"}
{"candidate_id": "LLM02431", "doc_id": "NCT01000155_inc", "case_bucket": "or", "source_criterion": "Diagnosis of sickle cell disease Clinically significant disease defined as at least 1 painful episode per year averaged over the previous 3 years or a history of priapism, stroke, acute chest syndrome, avascular necrosis, multi-organ failure or the need for chronic narcotic medications for pain from sickle cell disease Must have failed a previous attempt at treatment with hydroxyurea defined as the inability to achieve a significant absolute increase in % fetal hemoglobin or the inability to tolerate hydroxyurea treatment due to severe side effects such as but not limited to myelosuppression, gastrointestinal symptoms, edema or hepatic enzyme elevations or have contraindications to hydroxyurea 18 years of age or older Hematologic laboratory values as outlined in the protocol Non-hematologic laboratory values as outlined in the protocol Must agree not to donate blood or other bodily fluid while taking the study drug and for 28 days thereafter Women of child-bearing potential (WCBP) must have a negative serum pregnancy test 72 hours or less prior to starting treatment Women of child-bearing potential and men must agree to use 2 forms of adequate contraception prior to study entry and for the duration of study participation", "candidate_expression": "((Clinically significant disease averaged over the previous 3 years the previous 3 years) AND (WCBP) AND (Women) AND (Women of child-bearing potential (WCBP) must have a negative serum pregnancy test 72 hours or less prior to starting treatment) AND (age 18 years or older) AND (child-bearing potential) AND (contraception must agree to 2 forms adequate prior to study entry for the duration of study participation study entry study participation) AND (donate blood Must agree to) AND (donate bodily fluid Must agree to while taking the study drug taking the study drug) AND (pain need for chronic) AND (serum pregnancy test negative 72 hours or less prior to starting treatment) AND (sickle cell disease) AND (sickle cell disease Diagnosis Clinically significant) AND (study drug for 28 days thereafter) AND (treatment starting treatment) AND ((acute chest syndrome) OR (avascular necrosis) OR (multi-organ failure) OR (narcotic medications chronic) OR (painful episode per year averaged over the previous 3 years at least 1) OR (priapism history) OR (stroke)) AND ((Women) OR (men)))"}
{"candidate_id": "LLM02432", "doc_id": "NCT02606565_inc", "case_bucket": "other", "source_criterion": "Newborns weighing 1.5kg or more at birth", "candidate_expression": "((Newborns) AND (weighing 1.5kg or more at birth))"}
{"candidate_id": "LLM02433", "doc_id": "NCT03015818_inc", "case_bucket": "or", "source_criterion": "age > 18 written informed consent SVD defined on echocardiography by an alteration of bioprosthesis leaflets function with a mean transvalvular gradient > 20 mmHg and maximal velocity = 3 m/s and effective orifice area =1.2 cm², and/or an aortic regurgitation more or equal to grade 2 on 4.", "candidate_expression": "((SVD) AND (age > 18) AND (echocardiography) AND (effective orifice area =1.2 cm²) AND (grade more or equal to 2 on 4) AND (maximal velocity = 3 m/s) AND (mean transvalvular gradient > 20 mmHg) AND (written informed consent) AND ((alteration of bioprosthesis leaflets function) OR (aortic regurgitation)))"}
{"candidate_id": "LLM02434", "doc_id": "NCT02678377_inc", "case_bucket": "or", "source_criterion": "Undergoing mid-urethral sling surgery Have symptoms of both stress and urgency urinary incontinence Able to consent, fill out study documents, and complete all study procedures and follow-up visits At least 18 years of age English speaking Be able and willing to learn clean intermittent self catheterization technique", "candidate_expression": "((Able to consent, fill out study documents, and complete all study procedures and follow-up visits) AND (age At least 18 years) AND (mid-urethral sling surgery) AND (stress urinary incontinence) AND (urgency urinary incontinence))"}
{"candidate_id": "LLM02435", "doc_id": "NCT00962364_exc", "case_bucket": "other", "source_criterion": "none, all patients meeting the inclusion criteria will be eligible.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02436", "doc_id": "NCT03305666_exc", "case_bucket": "or", "source_criterion": "Allergy or hypersensitivity to bupivacaine Pregnancy Incarceration Age < 18 years Indwelling continuous thoracic epidural analgesia", "candidate_expression": "((Age < 18 years) AND (Incarceration) AND (Pregnancy) AND (bupivacaine) AND (thoracic epidural analgesia Indwelling continuous) AND ((Allergy) OR (hypersensitivity)))"}
{"candidate_id": "LLM02437", "doc_id": "NCT03169127_inc", "case_bucket": "other", "source_criterion": "Need of lower third molar surgeries", "candidate_expression": "((lower third molar) AND (surgeries))"}
{"candidate_id": "LLM02438", "doc_id": "NCT02970773_exc", "case_bucket": "or", "source_criterion": "Any anti-coagulation therapy (apart from rivaroxaban for second objective) Hypersensitivity or allergy to factor Xa inhibitors Acute bacterial endocarditis Bleeding disorder Clinically relevant active bleeding Gastrointestinal ulcer or tumor Hepatic dysfunction with increased bleeding risk Renal failure / patients undergoing dialysis Pregnancy and breast feeding Gastrectomy, biliopancreatic diversion, resection or re-routing of small intestines Feeding tube Recent blood donation Abnormalities of laboratory values: alanine-aminotransferase (ALAT), aspartate-aminotransferase (ASAT), gamma-glutamyl transferase (gammaGT), alkalic phosphatase (AP), bilirubin, amylase, lipase, cystatin C, creatinine, white blood cell count, haemoglobin, platelet count, prothrombin time, aPTT, fibrinogen, thrombin time, factors II,V,VII and X Use of therapeutic or recreational drugs influencing plasmatic coagulation", "candidate_expression": "((ALAT) AND (AP) AND (ASAT) AND (Acute bacterial endocarditis) AND (Bleeding disorder) AND (Feeding tube) AND (Hepatic dysfunction) AND (Pregnancy and breast feeding) AND (active bleeding) AND (anti-coagulation therapy) AND (bleeding risk increased) AND (blood donation) AND (factor Xa inhibitors) AND (gammaGT) AND (white blood cell count) AND NOT (rivaroxaban) AND ((Gastrointestinal tumor) OR (Gastrointestinal ulcer)) AND ((Renal failure) OR (dialysis)) AND ((Gastrectomy) OR (biliopancreatic diversion)) AND ((re-routing) OR (resection)) AND ((Hypersensitivity) OR (allergy)) AND ((aPTT) OR (alanine-aminotransferase) OR (alkalic phosphatase) OR (amylase) OR (aspartate-aminotransferase) OR (bilirubin) OR (creatinine) OR (cystatin C) OR (factors II) OR (factors V) OR (factors VII) OR (factors X) OR (fibrinogen) OR (gamma-glutamyl transferase) OR (haemoglobin) OR (lipase) OR (platelet count) OR (prothrombin time,) OR (thrombin time)))"}
{"candidate_id": "LLM02439", "doc_id": "NCT02654912_exc", "case_bucket": "or", "source_criterion": "contraindications from manufacturer for medications including currently taking haloperidol, artane, Phenergan (Promethazine), chlorpromazine, erythromycin, Azithromycin, clarithromycin, Ketoconazole, fluconazole, mefloquine (as prophylaxis), lumefantrine (in Coartem), quinine, Septrin anyone seriously ill currently taking antimalarial medicines allergy to artemisinin drugs pregnant women in first trimester children under 3 months of age reported heart condition", "candidate_expression": "((Azithromycin) AND (Coartem) AND (Ketoconazole) AND (Phenergan) AND (Promethazine) AND (Septrin) AND (age under 3 months) AND (allergy) AND (antimalarial medicines) AND (artane) AND (artemisinin drugs) AND (children) AND (chlorpromazine) AND (clarithromycin) AND (contraindications) AND (erythromycin) AND (first trimester) AND (fluconazole) AND (haloperidol) AND (heart condition) AND (lumefantrine) AND (mefloquine) AND (pregnant first trimester) AND (quinine) AND (seriously ill) AND (women))"}
{"candidate_id": "LLM02440", "doc_id": "NCT02560389_inc", "case_bucket": "or", "source_criterion": "25-50 years of age PTSD related to physical or sexual assault Medically healthy English speaking", "candidate_expression": "((English speaking) AND (Medically healthy) AND (PTSD) AND (age 25-50 years) AND ((physical assault) OR (sexual assault)))"}
{"candidate_id": "LLM02441", "doc_id": "NCT01715584_exc", "case_bucket": "or", "source_criterion": "patient refusal age less than 40 or over 80 years combined surgical procedures emergency surgery Left ventricular ejection fraction less than 50 per cent calculated creatinine clearance less than 60 mL per minute", "candidate_expression": "((Left ventricular ejection fraction less than 50 per cent) AND (age) AND (calculated creatinine clearance less than 60 mL per minute) AND (combined surgical procedures) AND (emergency surgery) AND (patient refusal) AND ((less than 40) OR (over 80 years)))"}
{"candidate_id": "LLM02442", "doc_id": "NCT03011177_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02443", "doc_id": "NCT02445339_exc", "case_bucket": "or", "source_criterion": "Active opioid dependence Acute or chronic pain requiring opioid treatment Acute liver injury (liver aminotransferase concentrations >5 times the upper limit of normal) Health condition considered unsafe for inclusion (at discretion of PI and/or attending physician) Lack of capacity or willingness to consent Currently prescribed pharmacotherapy for alcohol dependence (not including treatment of acute alcohol withdrawal syndrome) Previous significant adverse reaction to naltrexone or diluent Pregnant, nursing, or not using effective methods of birth control Prisoners (as defined by Office of Human Research Protection) at the time of enrollment ARE NOT ELIGIBLE for study entry. However, subjects who become prisoners after being enrolled will be included and not be withdrawn from the study. Patients on parole or probation are eligible for enrollment.", "candidate_expression": "((>5 times the upper limit of normal) AND (Active) AND (Acute) AND (Acute liver injury) AND (Currently) AND (Health condition) AND (Lack of) AND (Office of Human Research Protection) AND (Pregnant) AND (Previous) AND (Prisoners) AND (acute alcohol withdrawal syndrome) AND (adverse reaction) AND (alcohol dependence) AND (at the time of enrollment) AND (birth control) AND (capacity to consent) AND (chronic) AND (considered unsafe for inclusion) AND (diluent) AND (effective methods) AND (liver aminotransferase concentrations) AND (naltrexone) AND (not) AND (not including) AND (nursing) AND (opioid dependence) AND (opioid treatment) AND (pain) AND (pharmacotherapy) AND (significant) AND (the time of enrollment) AND (treatment) AND (willingness to consent))"}
{"candidate_id": "LLM02444", "doc_id": "NCT01051414_inc", "case_bucket": "other", "source_criterion": "Subjects chronically infected with HCV Genotype 1 HCV RNA viral load of ≥ 10*5* IU/mL (100,000 IU/mL) at screening", "candidate_expression": "((HCV RNA viral load ≥ 10*5* IU/mL at screening 100,000 IU/mL screening) AND (HCV chronically Genotype 1 chronically))"}
{"candidate_id": "LLM02445", "doc_id": "NCT03350659_exc", "case_bucket": "or", "source_criterion": "Drug-induced hypotension, if necessary, evaluate patient after discontinuing the causative drug for one month Heart failure or Chronic renal failure Severe supine hypertension (Systolic Blood Pressure >180 or Diastolic Blood Pressure>110mmHg) Pregnant women, breast-feeding Unable to perform questionnaire", "candidate_expression": "((>110mmHg) AND (>180) AND (Drug-induced) AND (Severe) AND (Unable to perform questionnaire) AND (hypotension) AND (supine hypertension) AND (women) AND ((Pregnant) OR (breast-feeding)) AND ((Chronic renal failure) OR (Heart failure)) AND ((Diastolic Blood Pressure) OR (Systolic Blood Pressure)))"}
{"candidate_id": "LLM02446", "doc_id": "NCT03296488_inc", "case_bucket": "or", "source_criterion": "Male or female who is among 20 to 80 years of age at screening. Scheduled to electively undergo open-laparotomy. American Society of Anesthesiology Physical Class 1-3. Ability and willingness to provide informed consent", "candidate_expression": "((1-3) AND (20 to 80 years) AND (Ability and willingness to provide informed consent) AND (American Society of Anesthesiology Physical Class) AND (Scheduled) AND (age) AND (at screening) AND (electively) AND (open-laparotomy) AND ((Male) OR (female)))"}
{"candidate_id": "LLM02447", "doc_id": "NCT02923700_exc", "case_bucket": "or", "source_criterion": "age > 80 years; Kellgren-Lawrence score at X-ray evaluation > 3; major axial deviation (varus >5° , valgus > 5°), systemic disorders such as diabetes, rheumatoid arthritis, haematological diseases (coagulopathy), severe cardiovascular diseases, infections, immunodepression; patients in therapy with anticoagulants or antiaggregants; use of NSAIDs in the 5 days before blood donation; patients with Hb values < 11 g/dl and platelet values < 150,000/mmc.", "candidate_expression": "((Kellgren-Lawrence score > 3) AND (NSAIDs in the 5 days before blood donation) AND (X-ray evaluation) AND (age > 80 years) AND (coagulopathy) AND (major axial deviation) AND (systemic disorders) AND (therapy) AND ((cardiovascular diseases severe) OR (diabetes) OR (haematological diseases) OR (immunodepression) OR (infections) OR (rheumatoid arthritis)) AND ((antiaggregants) OR (anticoagulants)) AND ((Hb < 11 g/dl) OR (platelet < 150,000/mmc)) AND ((valgus > 5°) OR (varus >5°)))"}
{"candidate_id": "LLM02448", "doc_id": "NCT03280017_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologist physical status 1-3 Scheduled for elective video-assisted thoracic surgery Able to operate a patient-controlled analgesia device (PCA)", "candidate_expression": "((American Society of Anesthesiologist physical status 1-3) AND (PCA) AND (patient-controlled analgesia device) AND (video-assisted thoracic surgery Scheduled for elective))"}
{"candidate_id": "LLM02449", "doc_id": "NCT03430284_exc", "case_bucket": "or", "source_criterion": "type 1 diabetes,specific types of diabetes,gestational diabetes or pregestational diabetes; acute cardiovascular or cerebrovascular accidents within past 3 months; severe hepatic or renal dysfunction; malignant tumor; allergic history or contraindication for any drugs in trials; taking part in other clinical trials; obviously poor compliance.", "candidate_expression": "((accidents cardiovascular) AND (allergic history) AND (cerebrovascular accidents) AND (contraindication) AND (diabetes specific types) AND (drugs in trials any) AND (gestational diabetes) AND (hepatic dysfunction) AND (malignant tumor) AND (poor compliance obviously) AND (pregestational diabetes) AND (renal dysfunction) AND (taking part in other clinical trials) AND (type 1 diabetes))"}
{"candidate_id": "LLM02450", "doc_id": "NCT02257580_inc", "case_bucket": "scope", "source_criterion": "Scheduled for bilateral varus rotational osteotomy (VRO) with or without associated soft tissue and osseous procedures", "candidate_expression": "((VRO) AND (osseous procedures) AND (procedures soft tissue) AND (varus rotational osteotomy Scheduled for bilateral))"}
```
