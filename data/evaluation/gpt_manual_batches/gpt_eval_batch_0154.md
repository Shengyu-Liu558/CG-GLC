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
{"candidate_id": "LLM03826", "doc_id": "NCT01084993_inc", "case_bucket": "or", "source_criterion": "At least two of the following additional criteria At least 70 yrs old Female gender Diabetes Creatinine clearance <60mL/min History of gastro-intestinal or other organ bleeding Baseline anemia Current treatment with glycoproteins IIb-IIIa inhibitors", "candidate_expression": "((Creatinine clearance <60mL/min) AND (Diabetes) AND (Female) AND (anemia Baseline) AND (glycoproteins IIb-IIIa inhibitors) AND (old At least 70 yrs At least two) AND (treatment Current) AND ((gastro-intestinal bleeding) OR (organ bleeding other)))"}
{"candidate_id": "LLM03827", "doc_id": "NCT02339974_inc", "case_bucket": "scope", "source_criterion": "Patients must be at least 21 years old. The patient must have severe, symptomatic (ACC/AHA Stage D symptoms) tricuspid regurgitation (TR) as assessed by 2D echocardiogram with evidence of peripheral and central venous congestion (specifically lower extremity edema and abdominal ascites requiring diuretics.) The patient must be evaluated by a \"heart team\" of physicians including an interventional cardiologist, cardiothoracic surgeon, heart failure specialist, and imaging specialist, and presented for review at a local multi-disciplinary conference. By consensus, the heart team must agree (and verify in the case review process) that valve implantation will likely benefit the patient. The heart team must agree that medical factors preclude operation, based on a conclusion that the probability of death or serious, irreversible morbidity exceeds the probability of meaningful improvement. Also, other factors which may increase the patients perceived surgical risk for inclusion in the trial will be clearly delineated if they are present. These include, but are not limited to the following as defined by VARC 2: Frailty, Hostile chest, porcelain aorta, IMA or other critical conduit crossing the midline or adherent to the posterior table of sternum, severe right ventricular (RV) dysfunction. The surgeons' consultation notes shall specify the medical or anatomic factors leading to that conclusion. At least one of the cardiac surgeon assessors must have interviewed and examined the patient. The study patient provides informed consent and agrees to comply with all required post-procedure follow-up visits, including annual visits up to 5 years.", "candidate_expression": "((2D echocardiogram) AND (ACC/AHA) AND (Stage D) AND (TR) AND (The study patient provides informed consent and agrees to comply with all required post-procedure follow-up visits, including annual visits up to 5 years.) AND (abdominal ascites) AND (at least 21 years) AND (central venous congestion) AND (diuretics) AND (lower extremity edema) AND (old) AND (peripheral venous congestion) AND (severe) AND (symptomatic) AND (tricuspid regurgitation))"}
{"candidate_id": "LLM03828", "doc_id": "NCT02431559_inc", "case_bucket": "or", "source_criterion": "1. Subjects must have recurrent or persistent platinum-resistant epithelial ovarian, fallopian tube, or primary peritoneal carcinoma with measureable disease (as defined by RECIST 1.1.) after first or second line platinum-based chemotherapy, for which treatment with PLD is indicated. Platinum-based therapy is defined as treatment with carboplatin, cisplatin or another organoplatinum compound. Platinum-resistant is defined as having a platinum-free interval (PFI) of < 12 months after first- or second-line platinum-based chemotherapy, or having disease progression while receiving second-line platinum-based chemotherapy. Subjects are allowed to have received, but are not required to have received: one additional cytotoxic regimen and/or PARP inhibitor for management of recurrent or persistent disease. biologic therapy (e.g., bevacizumab) as part of their primary treatment regimen or part of their treatment for management of recurrent or persistent disease. 2. Histologic documentation of the original primary tumor. 3. Documented radiographic disease progression < 12 months after the last dose of first- or second-line platinum-based chemotherapy. 4. Subjects in Phase 2 must have disease amenable to biopsy and must be willing to undergo pre- and post-treatment tumor biopsies. Optional for Phase 1. Note: archival tissue will be requested for all subjects preferably from primary tumor site prior to cancer treatment; however, archival tissue is not a requirement for study entry. 5. ECOG performance status of 0 or 1. 6. Laboratory parameters for vital functions should be in the normal range. Laboratory abnormalities that are not clinically significant are generally permitted, except for the following laboratory parameters, which must be within the ranges specified, regardless of clinical significance: Hemoglobin: ≥ 9 g/dL Neutrophil count: ≥ 1.5 x 109/L Platelet count: ≥ 100,000/mm3 Serum creatinine, ≤ 1.5x Institutional Upper Limit of Normal (ULN), or Creatinine Clearance ≥ 50 mL/min (by Cockcroft-Gault formula) Serum bilirubin: ≤ 1.2 mg/dL AST/ALT: ≤ 2.5 x ULN Alkaline phosphatase: ≤ 2.5 x ULN 7. Age ≥18 years. 8. Able and willing to give valid written informed consent. 9. Body weight > 30 kg", "candidate_expression": "((0 or 1) AND (< 12 months after first- or second-line platinum-based chemotherapy) AND (< 12 months after the last dose of first- or second-line platinum-based chemotherapy) AND (> 30 kg) AND (AST/ALT) AND (Able and willing to give valid written informed consent.) AND (Age) AND (Alkaline phosphatase) AND (Body weight) AND (Cockcroft-Gault formula) AND (Creatinine Clearance) AND (ECOG performance status) AND (Hemoglobin) AND (Histologic) AND (Laboratory parameters for vital functions) AND (Neutrophil count) AND (PLD) AND (Platelet count) AND (Platinum-based therapy) AND (Platinum-resistant) AND (Serum bilirubin) AND (Serum creatinine) AND (bevacizumab) AND (biologic therapy) AND (disease) AND (disease amenable to biopsy) AND (disease progression) AND (documentation) AND (first line platinum-based chemotherapy) AND (first- or second-line platinum-based chemotherapy) AND (indicated) AND (measureable disease) AND (normal range) AND (one additional) AND (original primary tumor) AND (platinum-free interval (PFI)) AND (platinum-resistant) AND (primary treatment regimen) AND (radiographic) AND (second line platinum-based chemotherapy) AND (second-line platinum-based chemotherapy) AND (the last dose of first- or second-line platinum-based chemotherapy) AND (treatment) AND (treatment with PLD) AND (willing to undergo pre- and post-treatment tumor biopsies) AND (≤ 1.2 mg/dL) AND (≤ 1.5x Institutional Upper Limit of Normal (ULN)) AND (≤ 2.5 x ULN) AND (≥ 1.5 x 109/L) AND (≥ 100,000/mm3) AND (≥ 50 mL/min) AND (≥ 9 g/dL) AND (≥18 years) AND ((carcinoma epithelial ovarian) OR (carcinoma fallopian tube) OR (primary peritoneal carcinoma)) AND ((persistent) OR (recurrent)) AND ((after first line platinum-based chemotherapy) OR (after second line platinum-based chemotherapy)) AND ((another organoplatinum compound) OR (carboplatin) OR (cisplatin)) AND ((PARP inhibitor) OR (cytotoxic regimen)))"}
{"candidate_id": "LLM03829", "doc_id": "NCT03199560_inc", "case_bucket": "or", "source_criterion": "Women above 18 years of age with biopsy proven, clinically stage 1 or 2 breast cancer who will be undergoing partial mastectomy with SLNBx at Memorial Health", "candidate_expression": "((SLNBx) AND (Women above 18 years) AND (age) AND (at Memorial Health) AND (biopsy stage 1 stage 2) AND (breast cancer) AND (partial mastectomy will be undergoing))"}
{"candidate_id": "LLM03830", "doc_id": "NCT01715714_exc", "case_bucket": "or", "source_criterion": "Any concomitant cardiovascular procedure to CABG (i.e. valve, aortic or carotid surgery) Acute ST-segment-elevation myocardial infarction (STEMI) NSTE-ACS with cardiogenic shock warranting emergent salvage surgery within 12 hrs from hospital admission History of atrial fibrillation or muscle disease (myopathy) Current renal (creatinine>2x upper limit of normal (ULN), dialysis, kidney transplant) or hepatic dysfunction (AST/ALT>2x ULN, liver transplant or neoplasm) Inability of oral drug intake", "candidate_expression": "((Acute ST-segment-elevation myocardial infarction) AND (CABG concomitant) AND (Inability) AND (NSTE-ACS) AND (STEMI) AND (cardiogenic shock) AND (cardiovascular procedure concomitant) AND (myopathy) AND (oral drug) AND (oral drug intake Inability of) AND (salvage surgery warranting) AND ((atrial fibrillation) OR (muscle disease)) AND ((creatinine >2x upper limit of normal (ULN)) OR (dialysis) OR (kidney transplant)) AND ((hepatic dysfunction) OR (renal dysfunction)) AND ((ALT >2x ULN) OR (AST >2x ULN)) AND ((liver transplant) OR (neoplasm)) AND ((aortic surgery) OR (carotid surgery) OR (valve surgery)))"}
{"candidate_id": "LLM03831", "doc_id": "NCT02315287_exc", "case_bucket": "or", "source_criterion": "Contraindication to sitagliptin or metformin or thiazolidinedione Pregnant or breast feeding women Type 1 diabetes, gestational diabetes, or secondary forms of diabetes Not appropriate for oral antidiabetic agent Medication which affect glycemic control Disease which affect efficacy and safety of drugs Any major illness (Liver disease, Renal failure, Heart disease, Cancer, etc)", "candidate_expression": "((Contraindication) AND (Disease) AND (Medication) AND (Not) AND (affect glycemic control) AND (appropriate) AND (major illness) AND (oral antidiabetic agent) AND ((affect efficacy) OR (safety of drugs)) AND ((metformin) OR (sitagliptin) OR (thiazolidinedione)) AND ((Cancer) OR (Heart disease) OR (Liver disease) OR (Renal failure)) AND ((Pregnant) OR (breast)) AND ((Type 1 diabetes) OR (gestational diabetes) OR (secondary forms of diabetes)))"}
{"candidate_id": "LLM03832", "doc_id": "NCT02868437_exc", "case_bucket": "or", "source_criterion": "History of curettage or other intrauterine surgery History of post-abortion complication or infection", "candidate_expression": "((History) AND (curettage) AND (intrauterine surgery) AND (post-abortion complication) AND (post-abortion infection))"}
{"candidate_id": "LLM03833", "doc_id": "NCT02984228_inc", "case_bucket": "other", "source_criterion": "English speaking/literate Age 18-100 years Visual analog score pain >= 5 Greater than or equal to 3 months of pain after onset of symptoms that has failed conservative treatments Confirmation of glenohumeral OA via imaging Transient relief of symptoms after diagnostic intra-articular injection into the glenohumeral joint", "candidate_expression": "((18-100 years) AND (>= 5) AND (Age) AND (English speaking/literate) AND (Greater than or equal to 3 months) AND (Transient) AND (Visual analog score pain) AND (after onset of symptoms) AND (conservative treatments) AND (failed) AND (glenohumeral OA) AND (glenohumeral joint) AND (imaging) AND (intra-articular injection) AND (onset of symptoms) AND (pain) AND (relief of symptoms))"}
{"candidate_id": "LLM03834", "doc_id": "NCT03192020_inc", "case_bucket": "or", "source_criterion": "patients with =20° passive extension deficit (PED) in metacarpophalangeal (MP) or proximal interphalangeal (PIP) joint, or TPED of =30° in MP and PIP joints of finger/fingers II-V age > 18 years palpable cord provision of informed consent ability to fill the Finnish versions of questionnaires.", "candidate_expression": "((TPED =30° MP PIP joints finger/fingers II-V) AND (age > 18 years) AND (palpable cord) AND (passive extension deficit (PED) =20°) AND (provision of informed consent) AND ((joint metacarpophalangeal (MP)) OR (proximal interphalangeal (PIP) joint)))"}
{"candidate_id": "LLM03835", "doc_id": "NCT02105090_exc", "case_bucket": "or", "source_criterion": "amide and/or esther local anaesthetic allergy paraben allergy Child-Pugh grade B/C liver failure renal insufficiency (calculated glomerular filtration rate under 60 ml/min/1.73 m2 according to Cockcroft-Gault scale ) dementia those presenting with swallowing problem chronic pain condition chronic use of pain medication pregnancy lactation", "candidate_expression": "((Child-Pugh grade) AND (Cockcroft-Gault scale) AND (allergy) AND (calculated glomerular filtration rate) AND (chronic pain condition) AND (chronic use) AND (dementia) AND (lactation) AND (liver failure) AND (pain medication) AND (paraben) AND (pregnancy) AND (renal insufficiency) AND (swallowing problem) AND (under 60 ml/min/1.73 m2) AND ((amide local anaesthetic) OR (esther local anaesthetic)) AND ((B) OR (C)))"}
{"candidate_id": "LLM03836", "doc_id": "NCT03134378_inc", "case_bucket": "or", "source_criterion": "18 years or older patients who are proven to be infected by Helicobacter pylori based on positive in Urea Breath Test or positive in histopathologic examination of biopsy in antrum and corpus of gaster through esophagoduodenoscopy.", "candidate_expression": "((18 years or older) AND (Urea Breath Test) AND (antrum of gaster) AND (corpus of gaster) AND (esophagoduodenoscopy) AND (histopathologic examination of biopsy) AND (infected by Helicobacter pylori) AND (old) AND (positive))"}
{"candidate_id": "LLM03837", "doc_id": "NCT01997112_inc", "case_bucket": "or", "source_criterion": "=18 years old, men or post-menopausal women (women with no periods for 12 months or more, or those who have had a surgical menopause) Treated hypertensive patients with an average daytime ambulatory blood pressure measurement (ABPM) <150/95mmHg on stable doses of one or more antihypertensive medication (at least one of which should be; an ACE inhibitor, angiotensin receptor blocker or diuretic) for 3 months, or untreated hypertensive patients with an average daytime ABPM =135/85 but <150/95.", "candidate_expression": "((antihypertensive medication stable doses one or more) AND (average daytime ABPM =135/85 but <150/95) AND (average daytime ambulatory blood pressure measurement (ABPM) <150/95mmHg) AND (hypertensive Treated) AND (hypertensive patients untreated) AND (post-menopausal) AND (surgical) AND (years old =18) AND ((ACE inhibitor) OR (angiotensin receptor blocker) OR (diuretic)) AND ((men) OR (women)) AND ((menopause) OR (no periods for 12 months or more)))"}
{"candidate_id": "LLM03838", "doc_id": "NCT03103204_inc", "case_bucket": "or", "source_criterion": "Moderate to advanced generalized chronic periodontitis Body mass index: > 18.5 kg/m2 Minimum of 12 natural teeth Smokers, non-smokers or former-smokers", "candidate_expression": "((> 18.5 kg/m2) AND (Body mass index) AND (Minimum of 12) AND (Moderate to advanced) AND (Smokers) AND (former-smokers) AND (generalized chronic periodontitis) AND (natural teeth) AND (non-smokers))"}
{"candidate_id": "LLM03839", "doc_id": "NCT02844907_inc", "case_bucket": "or", "source_criterion": "Body Mass Index (BMI) = 35 kg/m2 HbA1c = 5.7% Ability to speak and understand English", "candidate_expression": "((Body Mass Index (BMI) = 35 kg/m2) AND (HbA1c = 5.7%) AND ((Ability to speak English) OR (Ability to understand English)))"}
{"candidate_id": "LLM03840", "doc_id": "NCT00445029_exc", "case_bucket": "or", "source_criterion": "Pregnant or lactating women. Evolutive skin disease on the testing zone (lower back). Patients with a clinically significant disease (chronic, recurrent or active). Systemic corticotherapy or immunosuppressive treatment during the previous month, or local corticoid treatment the week before the patch testing. Local or systemic drug use which interacts with the outcome measures. Exposure to sun or UV radiations, 15 days before the patch testing. Patients deprived of their civic rights, in custody, or subject to a tutorial, judiciary or administrative decision. Patients subject to a protection measure. Patients in a critical medical situation. Patients with a personal situation judged by the investigator as unlikely to be compatible with optimal participation in the study, or which could constitute a risk for the patient. Linguistic barrier or psychological profile preventing the patient from signing the consent form. Patient still in an exclusion period following the participation in another clinical trial. Patients having earned more than 4500€ in indemnities for participation in clinical trials during the previous 12 months, including this study.", "candidate_expression": "((15 days before the patch testing) AND (Evolutive skin disease) AND (Exposure to UV radiations) AND (Exposure to sun) AND (Linguistic barrier) AND (Local) AND (Pregnant) AND (Systemic corticotherapy) AND (active) AND (chronic) AND (clinically significant) AND (critical medical situation) AND (deprived of their civic rights) AND (disease) AND (drug) AND (during the previous 12 months) AND (during the previous month) AND (earned more than 4500€ in indemnities) AND (immunosuppressive treatment) AND (in custody) AND (interacts with the outcome measures) AND (lactating) AND (local corticoid treatment) AND (lower back) AND (participation in another clinical trial) AND (participation in clinical trials) AND (personal situation) AND (preventing) AND (psychological profile) AND (recurrent) AND (signing the consent form) AND (still in an exclusion period following) AND (subject to a judiciary decision) AND (subject to a protection measure) AND (subject to a tutorial) AND (subject to administrative decision) AND (systemic) AND (testing zone) AND (the patch testing) AND (the previous 12 months) AND (the week before) AND (women))"}
{"candidate_id": "LLM03841", "doc_id": "NCT02606565_exc", "case_bucket": "other", "source_criterion": "Newborns with severe congenital anomalies Newborns with infection of the umbilical cord at birth", "candidate_expression": "((Newborns) AND (at birth) AND (infection of the umbilical cord) AND (severe congenital anomalies))"}
{"candidate_id": "LLM03842", "doc_id": "NCT02918851_exc", "case_bucket": "or", "source_criterion": "Any significant acute or chronic medical illness or problem, including, but not limited to, diabetes, hypertension, cardiac disease, asthma, chronic obstructive lung disease Current or recent (last 60 days) tobacco or nicotine use History of sickle cell trait or disease or any other acquired or hereditary hematological abnormality History of fainting or other significant adverse reaction during phlebotomy or donation of blood Known prolonged QTc (or evidence of such at screening) on electrocardiogram defined as >470 ms Known or suspected illicit drug or alcohol abuse Known or suspected HIV, Hepatitis B, or Hepatitis C infection History of thrombophilia or anticoagulant therapy Pregnancy Obesity defined as BMI>30 Recent history of blood donation: a) Single whole blood unit donation within the past 8 weeks; b) Double RBC donation by apheresis within the past 16 weeks; or c) Plasma donation by apheresis within the past 4 weeks Inadequate RBC mass based on TBV <4500 ml (above) or screening Hb <14 g/dL", "candidate_expression": "((BMI >30) AND (HIV infection) AND (Hb <14 g/dL) AND (Hepatitis B infection) AND (Hepatitis C infection) AND (Obesity) AND (Pregnancy) AND (QTc >470 ms) AND (RBC mass Inadequate) AND (TBV <4500 ml) AND (acquired hematological abnormality) AND (adverse reaction) AND (alcohol abuse) AND (anticoagulant therapy) AND (asthma) AND (blood donation) AND (cardiac disease) AND (chronic obstructive lung disease) AND (diabetes) AND (donation of blood) AND (electrocardiogram) AND (fainting) AND (hereditary hematological abnormality) AND (hypertension) AND (illicit drug abuse) AND (medical illness acute chronic) AND (nicotine use) AND (phlebotomy) AND (sickle cell disease) AND (sickle cell trait) AND (thrombophilia) AND (tobacco use))"}
{"candidate_id": "LLM03843", "doc_id": "NCT00959569_exc", "case_bucket": "other", "source_criterion": "previous unusual response to esmolol inclusion in other randomized studies esmolol administration in the previous 30 days emergency operation", "candidate_expression": "((emergency) AND (esmolol) AND (in the previous 30 days) AND (inclusion in other randomized studies) AND (operation) AND (unusual response))"}
{"candidate_id": "LLM03844", "doc_id": "NCT03561753_exc", "case_bucket": "or", "source_criterion": "Tuberculosis resistant to any of the study drugs (isoniazid, rifampin, EMB, PZA, CFZ, Pto) Unable to take oral medications. History of allergy or intolerance to any of the study drugs Serum aminotransferase (AST or ALT) 3x upper limit of normal or higher Pregnant or nursing females, or plan to become pregnant or nurse during the study period Males planning to conceive a child during the study or within 6 months of cessation of treatment. Any treatment directed against active tuberculosis within 6 months preceding initiation of study drugs. Suspected or documented tuberculosis involving the central nervous system and/or bones and/or joints, and/or miliary tuberculosis and/or pericardial tuberculosis. HIV infected HBV infected or HCV infected (these increase the risk of TB-drug induced hepatotoxicity) Weight less than 40.0 kg. Known allergy or intolerance to any of the study medications. Individuals will be excluded from enrollment if, at the time of enrollment, their M. tuberculosis isolate is already known to be resistant to any of the study drugs. QTcF > 500 msec Other medical conditions, that, in the investigator's judgment, make study participation not in the individual's best interest. Current or planned incarceration or other involuntary detention Having participated in other clinical studies with dosing of investigational agents within 8 weeks prior to trial start or currently enrolled in an investigational study that includes treatment with medicinal agents. Subjects who are participating in observational studies or who are in a follow up period of a trial that included drug therapy may be considered for inclusion.", "candidate_expression": "((ALT) AND (AST) AND (CFZ) AND (EMB) AND (HBV infected) AND (HCV infected) AND (HIV infected miliary tuberculosis pericardial tuberculosis) AND (M. tuberculosis isolate resistant to any of the study drugs) AND (Males) AND (PZA) AND (Pregnant) AND (Pto) AND (QTcF > 500 msec) AND (Serum aminotransferase) AND (Tuberculosis resistant to) AND (Unable to take oral medications) AND (Weight less than 40.0 kg) AND (allergy) AND (become pregnant) AND (conceive a child planning to during the study within 6 months of cessation of treatment) AND (enrolled in an investigational study currently) AND (females) AND (incarceration Current planned) AND (intolerance) AND (investigational agents) AND (involuntary detention) AND (isoniazid) AND (medicinal agents) AND (nurse) AND (nursing) AND (participated in other clinical studies within 8 weeks prior to trial start) AND (rifampin) AND (study drugs) AND (study medications) AND (treatment) AND (tuberculosis Suspected documented central nervous system bones joints) AND (tuberculosis active within 6 months preceding initiation of study drugs))"}
{"candidate_id": "LLM03845", "doc_id": "NCT02579928_inc", "case_bucket": "or", "source_criterion": "MDD Cohort: Meet DSM-5 criteria for Major Depressive Disorder by structured interview (MINI-KID); CDRS-R score >40; Failure to achieve remission with at least 1 adequate prior antidepressant trial (e.g. SSRI, SNRI, or TCA), meaning at least 8 weeks at therapeutic dosing, including at least 4 weeks of stable dosing. Anxiety Cohort: Meet DSM-5 criteria for any of the following anxiety disorders: Social Anxiety Disorders, Generalized Anxiety Disorder, Separation Anxiety Disorder and/or Panic Disorder by structured interview (MINI-KID); ADIS Clinical Severity Rating ≥4 (moderately severe) for any of the 4 included anxiety disorders; Failure to achieve remission with at least 1 adequate prior anxiolytic medication trial (e.g. SSRI, SNRI, or TCA), meaning at least 8 weeks at therapeutic dosing, including at least 4 weeks of stable dosing; Failure to achieve remission with previous CBT or subject declines current CBT therapy Stable psychiatric medications and doses for the month prior to enrollment. Subjects may continue to engage in any ongoing psychotherapy. Medically and neurologically healthy on the basis of physical examination and medical history. Parents able to provide written informed consent and adolescents must additionally provide assent.", "candidate_expression": "((ADIS Clinical Severity Rating ≥4 moderately severe) AND (Anxiety Cohort) AND (CBT therapy current) AND (CBT therapy previous) AND (CDRS-R score >40) AND (Generalized Anxiety Disorder) AND (MDD Cohort) AND (MINI-KID) AND (Major Depressive Disorder DSM-5 criteria) AND (Medically healthy) AND (Panic Disorder) AND (Parents provide written informed consent) AND (SNRI) AND (SSRI) AND (Separation Anxiety Disorder) AND (Social Anxiety Disorders) AND (TCA) AND (adolescents provide assent) AND (antidepressant) AND (antidepressant trial at least 1 adequate prior) AND (anxiety disorders) AND (anxiety disorders DSM-5 criteria) AND (anxiolytic medication) AND (anxiolytic medication trial at least 1 adequate prior) AND (medical history) AND (neurologically healthy) AND (physical examination) AND (psychiatric medications Stable doses Stable for the month prior to enrollment) AND (stable dosing at least 4 weeks) AND (structured interview) AND (subject declines) AND (therapeutic dosing at least 8 weeks) AND NOT (remission))"}
{"candidate_id": "LLM03846", "doc_id": "NCT03475589_inc", "case_bucket": "or", "source_criterion": "Age of 18 and over, male or female; Patients with histologically confirmed advanced (stage IV) gastric cancer, NSCLC, breast cancer or ovarian cancer, who choose monotherapy of oral vascular targeting drug (apatinib) due to intolerability or inappropriateness of other therapies; Presence of measurable lesions (=10mm on spiral CT scan) subject to RECIST 1.1; Blood pressured controlled at 150/100 mHg following drug administration; An ECOG PS score of between 0 and 1; A life expectancy of at least 3 months; Subjects who volunteer to participate in this study and have signed the Informed Consent Form (ICF), with good compliance with treatment and follow-up.", "candidate_expression": "((Age 18 and over) AND (Blood pressured controlled 150/100 mHg) AND (ECOG PS between 0 and 1) AND (NSCLC) AND (Subjects who volunteer to participate in this study and have signed the Informed Consent Form (ICF), with good compliance with treatment and follow-up.) AND (apatinib) AND (breast cancer) AND (female) AND (gastric cancer) AND (histologically stage IV) AND (life expectancy at least 3 months) AND (male) AND (measurable lesions RECIST 1.1) AND (monotherapy) AND (oral vascular targeting drug) AND (ovarian cancer) AND (spiral CT scan =10mm))"}
{"candidate_id": "LLM03847", "doc_id": "NCT02152696_inc", "case_bucket": "or", "source_criterion": "Female with a persisting pregnancy of unknown location: A pregnancy of unknown location is defined as a pregnancy in a woman with a positive pregnancy test but no definitive signs of pregnancy in the uterus or adnexa on ultrasound imaging. A definitive sign of gestation includes ultrasound visualization of a gestational sac with a yolk sac (with or without an embryo) in the uterus or in the adnexa. Ultrasound must be performed within 7 days prior to randomization. Persistence of hCG is defined as at least 2 serial hCG values (over 2-14 days), showing < 15% rise per day, or < 50% fall between the first and last value. Patient is hemodynamically stable, hemoglobin >10 mg/dL Greater than or 18 years of age", "candidate_expression": "((Female) AND (Persistence of hCG at least 2) AND (Ultrasound within 7 days prior to randomization) AND (age Greater than or 18 years) AND (hCG over 2-14 days < 15% rise per day < 50% fall between the first and last value.) AND (hemodynamically stable) AND (hemoglobin >10 mg/dL) AND (pregnancy) AND (pregnancy test positive) AND (pregnancy unknown location) AND (woman))"}
{"candidate_id": "LLM03848", "doc_id": "NCT00917891_exc", "case_bucket": "or", "source_criterion": "1. Currently pregnant or last pregnancy outcome within 3 months prior to enrolment 2. Currently breast-feeding 3. Participated in any other research study within 60 days prior to screening 4. Previously participated in any HIV vaccine study 5. Untreated urogenital infections (either symptomatic or asymptomatic) within 2 weeks prior to enrollment 6. Presence of abnormal physical finding on the vulva, vaginal walls or cervix during pelvic/speculum examination and/or colposcopy 7. History of significant urogenital or uterine prolapse, undiagnosed vaginal bleeding, urethral obstruction 8. Pap smear result at screening that requires cryotherapy, biopsy, treatment (other than for infection), or further evaluation 9. Any Grade 2, 3 or 4 baseline haematology, chemistry or urinalysis laboratory abnormality according to the DAIDS Table for Grading Adverse Experiences 10. Unexplained, undiagnosed abnormal bleeding per vagina, bleeding per vagina during or following vaginal intercourse, or gynaecologic surgery within 90 days prior to enrollment 11. Any history of anaphylaxis or severe allergy resulting in angioedema; or a history of sensitivity/allergy to latex 12. Any serious acute, chronic or progressive disease 13. Any condition(s) that, in the opinion of the investigator, might interfere with adherence to study requirements or evaluation of the study objectives", "candidate_expression": "((Any condition(s) that, in the opinion of the investigator, might interfere with adherence to study requirements or evaluation of the study objectives) AND (Any serious acute, chronic or progressive disease) AND (Currently) AND (DAIDS Table for Grading Adverse Experiences) AND (Grade 2, 3 or 4) AND (History) AND (Pap smear) AND (Unexplained) AND (Untreated) AND (abnormal) AND (abnormal physical finding on the cervix) AND (abnormal physical finding on the vaginal walls) AND (abnormal physical finding on the vulva) AND (acute) AND (allergy) AND (allergy to latex) AND (anaphylaxis) AND (angioedema) AND (asymptomatic) AND (at screening) AND (baseline) AND (biopsy) AND (bleeding per vagina) AND (breast-feeding) AND (chemistry) AND (chemistry abnormality) AND (chronic) AND (colposcopy) AND (cryotherapy) AND (disease) AND (during vaginal intercourse) AND (enrollment) AND (enrolment) AND (following vaginal intercourse) AND (further evaluation) AND (gynaecologic surgery) AND (haematology) AND (haematology abnormality) AND (history) AND (laboratory) AND (laboratory abnormality) AND (last) AND (pelvic examination) AND (pregnancy outcome) AND (pregnant) AND (progressive) AND (requires biopsy) AND (requires cryotherapy) AND (requires further evaluation) AND (requires treatment) AND (sensitivity to latex) AND (serious) AND (severe) AND (significant) AND (speculum examination) AND (symptomatic) AND (treatment) AND (undiagnosed) AND (urethral obstruction) AND (urinalysis) AND (urinalysis abnormality) AND (urogenital infections) AND (urogenital prolapse) AND (uterine prolapse) AND (vaginal bleeding) AND (within 2 weeks prior to enrollment) AND (within 3 months prior to enrolment) AND (within 90 days prior to enrollment))"}
{"candidate_id": "LLM03849", "doc_id": "NCT03129555_exc", "case_bucket": "or", "source_criterion": "A prescription of a NOAC within 90 days prior to hospitalization or outpatient clinic visit for VTE. Patients with NOAC preference apart from preference consistent with current cluster randomized NOAC. Other contraindications mentioned in the \"Summary of Product Characteristics\" for the respective NOAC.", "candidate_expression": "((NOAC) AND (NOAC preference) AND (Other) AND (Summary of Product Characteristics) AND (VTE) AND (contraindications) AND (hospitalization) AND (hospitalization or outpatient clinic visit for VTE) AND (outpatient clinic) AND (within 90 days prior to hospitalization or outpatient clinic visit for VTE) AND ((hospitalization) OR (outpatient clinic visit)))"}
{"candidate_id": "LLM03850", "doc_id": "NCT03631355_exc", "case_bucket": "or", "source_criterion": "Legally incompetent or mentally impaired (e.g., minors, Alzheimer's subjects, dementia, etc.) Younger than 18 years of age Any patient considered a vulnerable subject Have bleeding or clotting disorder Preoperative anticoagulation therapy Abnormal coagulation profile Renal disorder or insufficiency Sickle cell disease", "candidate_expression": "((Abnormal) AND (Abnormal coagulation profile) AND (Preoperative) AND (Sickle cell disease) AND (Younger than 18 years) AND (age) AND (anticoagulation) AND (anticoagulation therapy) AND (coagulation profile) AND (vulnerable subject) AND ((Legally incompetent) OR (mentally impaired)) AND ((bleeding disorder) OR (clotting disorder)) AND ((Renal disorder) OR (Renal insufficiency)) AND ((Alzheimer's) OR (dementia) OR (minors)))"}
```
