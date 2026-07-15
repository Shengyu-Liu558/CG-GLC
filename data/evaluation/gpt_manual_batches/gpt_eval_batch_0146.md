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
{"candidate_id": "LLM03626", "doc_id": "NCT02961764_exc", "case_bucket": "or", "source_criterion": "Known or suspected gram-negative infections, anaerobic infections, or fungemia Known or suspected infections that are severe, life threatening or are not included in the ABSSSI Food and Drug Administration (FDA) guidance Injection drug users with a fever Severe neurological disorder leading to immobility or confined to a wheelchair Bilateral Lower extremity involvement of the suspected infection.", "candidate_expression": "((Bilateral Lower extremity) AND (Severe) AND (anaerobic) AND (drug users) AND (fever) AND (fungemia) AND (gram-negative) AND (immobility) AND (infection) AND (infections) AND (life threatening) AND (neurological disorder) AND (severe) AND (wheelchair))"}
{"candidate_id": "LLM03627", "doc_id": "NCT02334631_exc", "case_bucket": "or", "source_criterion": "Patients with a contraindication to VCE (small bowel strictures, oropharyngeal dysphagia, pregnancy, patients who are not surgical candidates) Endoscopic insertion of video capsule endoscope Inpatient procedures for active GI bleeding Patients with fluid restriction or who are unable to drink up to 900 ml of fluid within 10 minutes prior to the VCE", "candidate_expression": "((Endoscopic insertion) AND (GI bleeding) AND (Inpatient procedures) AND (VCE) AND (active) AND (contraindication) AND (fluid restriction) AND (not) AND (oropharyngeal dysphagia) AND (pregnancy) AND (prior to the VCE) AND (small bowel strictures) AND (surgical candidates) AND (the VCE) AND (unable to drink) AND (video capsule endoscope))"}
{"candidate_id": "LLM03628", "doc_id": "NCT03337581_exc", "case_bucket": "or", "source_criterion": "allergic to dexmedetomidine, similar active ingredients or excipients G-6-PD deficiency a history of arrhythmia, bronchial and cardiovascular diseases, abnormal liver function and so on a history of use of alpha 2 receptor agonists or antagonists.", "candidate_expression": "((G-6-PD deficiency) AND (allergic) AND ((dexmedetomidine) OR (excipients) OR (similar active ingredients)) AND ((abnormal liver function) OR (arrhythmia) OR (bronchial diseases) OR (cardiovascular diseases)) AND ((alpha 2 receptor agonists) OR (alpha 2 receptor antagonists)))"}
{"candidate_id": "LLM03629", "doc_id": "NCT02944292_exc", "case_bucket": "other", "source_criterion": "Contraindication for propofol administration Contraindication for IAP measurement in supine position with head-of-bed at 0° Other intervention for reduction of IAP planned Previous propofol infusion rate >4 mg/kg/h", "candidate_expression": "((Contraindication) AND (IAP measurement supine position head-of-bed at 0°) AND (intervention for reduction of IAP Other planned) AND (propofol) AND (propofol infusion rate Previous >4 mg/kg/h))"}
{"candidate_id": "LLM03630", "doc_id": "NCT02035904_exc", "case_bucket": "or", "source_criterion": "preexisting pectoral, axillar, thoracic homolateral pain habitual opioid consumption; drug-alcoholics addiction ; ICU postoperative recovery; kidney failure (creatinin > 2 g/dl, creatinin <clearance 30 ml/h) and/or hepatic failure (cholinesterase < 2000 UI); cardiac arrhythmias o; Epilepsy; Psychiatric, cognitive disorders, mental retardation; Coagulopathies (INR > 2, activated partial thromboplastin time - aPTT>44 sec); platelet count less than 100.000/mm3; BMI > 30; Allergies to study drugs.", "candidate_expression": "((30 ml/h) AND (< 2000 UI) AND (> 2) AND (> 2 g/dl) AND (> 30) AND (>44 sec) AND (Allergies) AND (BMI) AND (Coagulopathies) AND (Epilepsy) AND (ICU postoperative recovery) AND (INR) AND (Psychiatric, cognitive disorders) AND (activated partial thromboplastin time - aPTT) AND (addiction drug) AND (alcoholics addiction) AND (axillar pain) AND (cardiac arrhythmias) AND (cholinesterase) AND (creatinin) AND (creatinin <clearance) AND (habitual) AND (hepatic failure) AND (homolateral) AND (kidney failure) AND (less than 100.000/mm3) AND (mental retardation) AND (opioid consumption) AND (pectoral pain) AND (platelet count) AND (study drugs) AND (thoracic pain))"}
{"candidate_id": "LLM03631", "doc_id": "NCT02760459_exc", "case_bucket": "or", "source_criterion": "History of active rheumatic diseases History of previous musculoskeletal injury of the same knee for excluding patients with secondary knee osteoarthritis History of previous surgery on the same knee History of adverse effects from medications to be used in this study Contraindication to spinal anesthesia History of psychiatric disorders or cognitive impairment Contraindication to corticosteroid agents Poorly controlled diabetes mellitus (HbA1C > 7.5) Poorly controlled hypertension History of ischemic heart disease or peripheral arterial disease or cerebrovascular disease Hepatic insufficiency (Child-Pugh score > 5) Renal insufficiency (Creatinine clearance < 30 mL/min) History of cataracts or glaucoma or ocular hypertension History of steroid or immunosuppressive drug use within 6 months of surgery", "candidate_expression": "((< 30 mL/min) AND (> 5) AND (> 7.5) AND (Child-Pugh score) AND (Contraindication) AND (Creatinine clearance) AND (HbA1C) AND (Hepatic insufficiency) AND (Poorly controlled) AND (Renal insufficiency) AND (active) AND (corticosteroid) AND (diabetes mellitus) AND (hypertension) AND (knee) AND (rheumatic diseases) AND (spinal anesthesia) AND (surgery) AND (within 6 months of surgery) AND ((cognitive impairment) OR (psychiatric disorders)) AND ((cerebrovascular disease) OR (ischemic heart disease) OR (peripheral arterial disease)) AND ((musculoskeletal injury) OR (secondary knee osteoarthritis)) AND ((cataracts) OR (glaucoma) OR (ocular hypertension)) AND ((immunosuppressive drug) OR (steroid)))"}
{"candidate_id": "LLM03632", "doc_id": "NCT02369211_exc", "case_bucket": "or", "source_criterion": "Chronic opiate use Liver disease (known history of hepatitis B or C, cirrhosis, nonalcoholic steatohepatitis, history of alcoholism, ALT/AST greater than 3 times upper limit of normal in the past 3 months) Allergy/hypersensitivity to acetaminophen Patients with baseline dementia Chronic diathesis Chronic kidney disease", "candidate_expression": "((ALT/AST) AND (Allergy) AND (Chronic) AND (Liver disease) AND (acetaminophen) AND (alcoholism) AND (baseline) AND (cirrhosis) AND (dementia) AND (diathesis) AND (greater than 3 times upper limit of normal) AND (hepatitis B) AND (hepatitis C) AND (history) AND (hypersensitivity) AND (in the past 3 months) AND (kidney disease) AND (nonalcoholic steatohepatitis) AND (opiate))"}
{"candidate_id": "LLM03633", "doc_id": "NCT02845427_exc", "case_bucket": "other", "source_criterion": "Revision cases Uncontrolled bleeding tendency (prothrombin conc. Less than 70%) History of deep venous thrombosis Sever liver impairment (liver failure) Sever renal impairment (S. creatinine more than 3)", "candidate_expression": "((History) AND (Less than 70%) AND (Revision cases) AND (Sever) AND (Uncontrolled) AND (bleeding tendency) AND (creatinine) AND (deep venous thrombosis) AND (liver failure) AND (liver impairment) AND (more than 3) AND (prothrombin) AND (renal impairment))"}
{"candidate_id": "LLM03634", "doc_id": "NCT02851888_inc", "case_bucket": "scope", "source_criterion": "Scheduled for arthroscopic labral repair with or without osteoplasty of the hip. 18 to 50 years old American Society of Anesthesiologists Physical Status (ASA PS) score of I or II.", "candidate_expression": "((ASA PS) AND (American Society of Anesthesiologists Physical Status score I or II) AND (arthroscopic labral repair Scheduled) AND (old 18 to 50 years) AND (osteoplasty hip))"}
{"candidate_id": "LLM03635", "doc_id": "NCT02671318_exc", "case_bucket": "or", "source_criterion": "Re-transplant; Patients with any panel reactive antibody (PRA) equal to or above 50%, class I or class II; Acute rejection episode in the last 30 days, or episode > 2A in the Banff criteria; GFR (MDRD) < 40 ml/min; Proteinuria > 0,5 g/l; Hemoglobin < 10 g/l and/or leucocytes < 4000 cels/mm3 and/or platelets < 150.000 cels/mm3; Triglycerides > 500 mg/dl with or without use of fibrate; Cholesterol total > 300 mg/dl with or without use of statin; Hepatic abnormalities; Significant periphery edema; Pulmonary abnormalities or breast x-ray abnormalities; Hyper sensibility to sirolimus formula;", "candidate_expression": "((< 10 g/l) AND (< 150.000 cels/mm3) AND (< 40 ml/min) AND (< 4000 cels/mm3) AND (> 0,5 g/l) AND (> 2A) AND (> 300 mg/dl) AND (> 500 mg/dl) AND (Acute rejection episode) AND (Banff criteria) AND (Cholesterol total) AND (GFR) AND (Hemoglobin) AND (Hepatic abnormalities) AND (Hyper sensibility) AND (PRA) AND (Proteinuria) AND (Pulmonary abnormalities) AND (Re-transplant) AND (Significant) AND (Triglycerides) AND (abnormalities) AND (breast x-ray) AND (class I) AND (class II) AND (equal to or above 50%) AND (fibrate) AND (last 30 days) AND (leucocytes) AND (panel reactive antibody) AND (periphery edema) AND (platelets) AND (sirolimus) AND (statin))"}
{"candidate_id": "LLM03636", "doc_id": "NCT00483106_inc", "case_bucket": "other", "source_criterion": "ADHD", "candidate_expression": "(ADHD)"}
{"candidate_id": "LLM03637", "doc_id": "NCT02825290_exc", "case_bucket": "other", "source_criterion": "PGD patients More than 4 previous embryo transfers", "candidate_expression": "((More than 4) AND (PGD) AND (embryo transfers) AND (previous))"}
{"candidate_id": "LLM03638", "doc_id": "NCT02431559_inc", "case_bucket": "or", "source_criterion": "1. Subjects must have recurrent or persistent platinum-resistant epithelial ovarian, fallopian tube, or primary peritoneal carcinoma with measureable disease (as defined by RECIST 1.1.) after first or second line platinum-based chemotherapy, for which treatment with PLD is indicated. Platinum-based therapy is defined as treatment with carboplatin, cisplatin or another organoplatinum compound. Platinum-resistant is defined as having a platinum-free interval (PFI) of < 12 months after first- or second-line platinum-based chemotherapy, or having disease progression while receiving second-line platinum-based chemotherapy. Subjects are allowed to have received, but are not required to have received: one additional cytotoxic regimen and/or PARP inhibitor for management of recurrent or persistent disease. biologic therapy (e.g., bevacizumab) as part of their primary treatment regimen or part of their treatment for management of recurrent or persistent disease. 2. Histologic documentation of the original primary tumor. 3. Documented radiographic disease progression < 12 months after the last dose of first- or second-line platinum-based chemotherapy. 4. Subjects in Phase 2 must have disease amenable to biopsy and must be willing to undergo pre- and post-treatment tumor biopsies. Optional for Phase 1. Note: archival tissue will be requested for all subjects preferably from primary tumor site prior to cancer treatment; however, archival tissue is not a requirement for study entry. 5. ECOG performance status of 0 or 1. 6. Laboratory parameters for vital functions should be in the normal range. Laboratory abnormalities that are not clinically significant are generally permitted, except for the following laboratory parameters, which must be within the ranges specified, regardless of clinical significance: Hemoglobin: ≥ 9 g/dL Neutrophil count: ≥ 1.5 x 109/L Platelet count: ≥ 100,000/mm3 Serum creatinine, ≤ 1.5x Institutional Upper Limit of Normal (ULN), or Creatinine Clearance ≥ 50 mL/min (by Cockcroft-Gault formula) Serum bilirubin: ≤ 1.2 mg/dL AST/ALT: ≤ 2.5 x ULN Alkaline phosphatase: ≤ 2.5 x ULN 7. Age ≥18 years. 8. Able and willing to give valid written informed consent. 9. Body weight > 30 kg", "candidate_expression": "((AST/ALT ≤ 2.5 x ULN) AND (Able and willing to give valid written informed consent.) AND (Age ≥18 years) AND (Alkaline phosphatase ≤ 2.5 x ULN) AND (Body weight > 30 kg) AND (Creatinine Clearance ≥ 50 mL/min Cockcroft-Gault formula) AND (ECOG performance status 0 or 1) AND (Hemoglobin ≥ 9 g/dL) AND (Histologic documentation) AND (Laboratory parameters for vital functions normal range) AND (Neutrophil count ≥ 1.5 x 109/L) AND (PARP inhibitor recurrent) AND (PLD) AND (Platelet count ≥ 100,000/mm3) AND (Platinum-based therapy) AND (Platinum-resistant) AND (Serum bilirubin ≤ 1.2 mg/dL) AND (Serum creatinine ≤ 1.5x Institutional Upper Limit of Normal (ULN)) AND (another organoplatinum compound) AND (bevacizumab) AND (biologic therapy) AND (carboplatin) AND (carcinoma epithelial ovarian) AND (carcinoma fallopian tube) AND (cisplatin) AND (cytotoxic regimen) AND (disease amenable to biopsy) AND (disease persistent) AND (disease progression) AND (disease progression < 12 months after the last dose of first- or second-line platinum-based chemotherapy) AND (indicated) AND (measureable disease after first line platinum-based chemotherapy after second line platinum-based chemotherapy) AND (original primary tumor) AND (persistent) AND (platinum-free interval (PFI) < 12 months after first- or second-line platinum-based chemotherapy) AND (primary peritoneal carcinoma) AND (primary treatment regimen) AND (radiographic) AND (recurrent) AND (second-line platinum-based chemotherapy) AND (treatment recurrent) AND (treatment with PLD indicated) AND (willing to undergo pre- and post-treatment tumor biopsies))"}
{"candidate_id": "LLM03639", "doc_id": "NCT01997112_exc", "case_bucket": "or", "source_criterion": "History of ischaemic heart disease, cardiac failure, cerebrovascular disease, liver impairment (ALT/AST>50IU/L) or stage 3-5 chronic kidney disease. History of overdose or suicidal ideation Patients weighing <55kgs. Patients with chronic pain requiring treatment, with a known allergy to paracetamol, or concomitant use of non-steroidal anti-inflammatories , oral anticoagulants or corticosteroids.", "candidate_expression": "((ALT >50IU/L) AND (AST >50IU/L) AND (cardiac failure) AND (cerebrovascular disease) AND (chronic kidney disease) AND (chronic pain requiring treatment) AND (corticosteroids) AND (ischaemic heart disease) AND (known allergy) AND (liver impairment) AND (non-steroidal anti-inflammatories) AND (oral anticoagulants) AND (overdose) AND (paracetamol) AND (stage 3-5) AND (suicidal ideation) AND (weighing <55kgs))"}
{"candidate_id": "LLM03640", "doc_id": "NCT02748330_inc", "case_bucket": "or", "source_criterion": "Provision of written informed consent (by patient or appropriate designee according to local regulations) prior to any study specific procedures. Aged 18 years or older, male or female. History of stable angina pectoris with angiographic evidence of CAD (diameter stenosis = 50%) in major, i.e., left main, left anterior descending, left circumflex, and right coronary arteries. History of previous myocardial infarction (MI) History of coronary revascularization, i.e., percutaneous coronary intervention (PCI) or coronary artery bypass graft (CABG), not including the elective PCI during the index hospitalization Documented history of type 2 diabetes mellitus. Post-procedural residual diameter stenosis of the treated lesions < 20% in patients with stent implantation or < 50% in those with balloon angioplasty Post-procedural thrombolysis in myocardial infarction (TIMI) grade 3 flow in treated vessels Negative cardiac troponin test before the index elective PCI. Taking Clopidogrel 75 mg daily dose for at least 7 days or taking Clopidogrel 75 mg daily dose for less than 7 days but with 300 to 600 mg Clopidogrel loading dose before PCI. Taking acetylsalicylic acid (ASA) 100 mg daily treatment for at least 7 days or taking ASA 100 mg daily dose for less than 7 days but with 300 mg ASA loading dose before PCI. have a negative urine or blood pregnancy test at enrolment and prior to randomization; currently be using a hormonal contraceptive and agree to continue its use in addition to using double-barrier local contraception (i.e., intra-uterine device plus spermicidal and condom for male partner) from screening through study completion.", "candidate_expression": "((100 mg) AND (18 years or older) AND (3) AND (300 mg) AND (300 to 600 mg) AND (75 mg) AND (< 20%) AND (< 50%) AND (= 50%) AND (ASA) AND (Aged) AND (CABG) AND (CAD) AND (Clopidogrel) AND (MI) AND (Negative) AND (PCI) AND (Post-procedural residual diameter stenosis) AND (Post-procedural thrombolysis) AND (Provision of written informed consent (by patient or appropriate designee according to local regulations) prior to any study specific procedures) AND (TIMI) AND (acetylsalicylic acid) AND (angiographic evidence) AND (balloon angioplasty) AND (before PCI) AND (before the index elective PCI.) AND (cardiac troponin test) AND (coronary artery bypass graft) AND (coronary revascularization) AND (currently be using a hormonal contraceptive and agree to continue its use in addition to using double-barrier local contraception (i.e., intra-uterine device plus spermicidal and condom for male partner) from screening through study completion) AND (daily) AND (diameter stenosis) AND (during the index hospitalization) AND (elective) AND (female) AND (for at least 7 days) AND (for less than 7 days) AND (have a negative urine or blood pregnancy test at enrolment and prior to randomization;) AND (index elective PCI) AND (index hospitalization) AND (left anterior descending coronary arteries) AND (left circumflex coronary arteries) AND (left main coronary arteries) AND (lesions) AND (major coronary arteries) AND (male) AND (myocardial infarction) AND (myocardial infarction grade) AND (not) AND (percutaneous coronary intervention) AND (right coronary arteries) AND (stable angina pectoris) AND (stent implantation) AND (treated) AND (treated vessels) AND (type 2 diabetes mellitus))"}
{"candidate_id": "LLM03641", "doc_id": "NCT02742233_inc", "case_bucket": "or", "source_criterion": "Diagnosis of diabetes mellitus according to World Health Organization criteria ( treatment with insulin or an oral hypoglycemic agent, twice random glucose measurements major than 200 mg/dl, or a fasting glucose major than 140 mg/dl) Ulcer located on the legs or feet, stage III or IV (Wagner Classification System) The subject agrees to comply with study protocol requirements and all follow up visit requirements.", "candidate_expression": "((III or IV) AND (The subject agrees to comply with study protocol requirements and all follow up visit requirements) AND (Ulcer) AND (Wagner Classification System) AND (World Health Organization criteria) AND (diabetes mellitus) AND (fasting glucose) AND (feet) AND (insulin) AND (legs) AND (major than 140 mg/dl) AND (major than 200 mg/dl) AND (oral hypoglycemic agent) AND (random glucose measurements) AND (stage) AND (treatment) AND (twice))"}
{"candidate_id": "LLM03642", "doc_id": "NCT03615508_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03643", "doc_id": "NCT03209687_exc", "case_bucket": "or", "source_criterion": "Females who have high response (estradiol at time of ovulation trigger is > 5000 pg/ml or more than 15 oocytes are retrieved)", "candidate_expression": "((> 5000 pg/ml) AND (Females) AND (at time of ovulation trigger) AND (estradiol) AND (high response) AND (more than 15) AND (oocytes retrieved) AND (ovulation trigger))"}
{"candidate_id": "LLM03644", "doc_id": "NCT00319748_exc", "case_bucket": "or", "source_criterion": "Had/have the following prior/concurrent therapy: Systemic corticosteroids (oral or injectable) within 7 days of first dose of 852A (topical or inhaled steroids are allowed) Investigational drugs/agents within 14 days of first dose of 852A Immunosuppressive therapy, including cytotoxic agents within 14 days of first dose of 852A (nitrosoureas within 30 days of first dose) Drugs known to induce QT interval prolongation and/or induce Torsades de pointes unless best available drug required to treat life-threatening conditions Radiotherapy within 3 weeks of the first dose of 852A Hematopoietic cell transplantation within 4 weeks of first dose of 852A Evidence of active infection within 3 days of first dose of 852A Active fungal infection or pulmonary infiltrates (prior treated disease stable for 2 weeks is allowable) Cardiac ischemia, cardiac arrhythmias or congestive heart failure uncontrolled by medication History of, or clinical evidence of, a condition which, in the opinion of the investigator, could confound the results of the study or put the subject at undue risk Uncontrolled intercurrent or chronic illness Active autoimmune disease requiring immunosuppressive therapy within 30 days Active coagulation disorder not controlled with medication Pregnant or lactating Concurrent malignancy (if in remission, at least 5 years disease free) except for localized (in-situ) disease, basal carcinomas and cutaneous squamous cell carcinomas that have been adequately treated Any history of brain metastases or any other active central nervous system (CNS) disease", "candidate_expression": "((852A) AND (Drugs known to induce QT interval prolongation) AND (Drugs known to induce Torsades de pointes) AND (Evidence within 3 days of first dose) AND (Hematopoietic cell transplantation within 4 weeks of first dose) AND (Investigational drugs/agents within 14 days of first dose) AND (Radiotherapy within 3 weeks of the first dose) AND (Systemic corticosteroids within 7 days of first dose) AND (active infection) AND (coagulation disorder Active controlled with medication) AND (could confound the results of the study or put the subject at undue risk a condition which Uncontrolled) AND (cytotoxic agents) AND (history of) AND (immunosuppressive therapy) AND (malignancy Concurrent in remission) AND NOT (prior treated disease stable) AND ((Immunosuppressive therapy within 14 days of first dose) OR (nitrosoureas within 30 days of first dose)) AND ((fungal infection) OR (pulmonary infiltrates)) AND ((Cardiac ischemia) OR (cardiac arrhythmias) OR (congestive heart failure uncontrolled by medication)) AND ((History) OR (clinical evidence)) AND ((chronic illness) OR (intercurrent illness)) AND ((autoimmune disease Active) OR (requiring within 30 days)) AND ((inhaled steroids) OR (topical steroids)) AND ((Pregnant) OR (lactating)) AND ((basal carcinomas) OR (cutaneous squamous cell carcinomas) OR (localized (in-situ) disease)) AND ((any other central nervous system (CNS) disease active) OR (brain metastases)) AND ((injectable) OR (oral)))"}
{"candidate_id": "LLM03645", "doc_id": "NCT02413970_inc", "case_bucket": "or", "source_criterion": "Likely suffer moderate-to-severe OSA based on history and physical or have an established diagnosis of OSA (20=AHI=65) based on a prior in-lab Polysomnography Documentation the subject not effectively treated with CPAP therapy. (Examples include non-compliance, discomfort, undesirable side effects, symptoms persist despite use). Subjects who have been prescribed, but refuse to try CPAP would be considered intolerant. Age 22 or above Willing and capable to have stimulation hardware permanently implanted, and to use the patient remote to activate the stimulation Willing and capable to return for all follow-up visits and conduct sleep studies at home, including the evaluation procedures and filling out questionnaires Willing and capable of providing informed consent", "candidate_expression": "((20 =65) AND (22 or above) AND (AHI) AND (Age) AND (CPAP therapy) AND (OSA) AND (Willing and capable of providing informed consent) AND (Willing and capable to have stimulation hardware permanently implanted, and to use the patient remote to activate the stimulation) AND (Willing and capable to return for all follow-up visits and conduct sleep studies at home, including the evaluation procedures and filling out questionnaires) AND (moderate) AND (not) AND (severe))"}
{"candidate_id": "LLM03646", "doc_id": "NCT02678962_inc", "case_bucket": "other", "source_criterion": "Age from 40 to 80 years old, either gender; Patients with bilateral age related cataracts, require bilateral cataract phacoemulsification combined Intraocular Lens implantation; Willing to undergo second eye surgery within 7 days after first eye surgery; The potential postoperative visual acuity of 20/40 or better in both eyes; Preoperative measurement of corneal astigmatism indicate the subjects are suitable for multifocal intraocular lenses implantation; Capability to understand the informed consent and willing and able to attend study", "candidate_expression": "((Age) AND (Capability to understand the informed consent and willing and able to attend study) AND (Intraocular Lens implantation) AND (Preoperative) AND (age related) AND (bilateral) AND (cataract phacoemulsification) AND (cataracts) AND (from 40 to 80 years old) AND (measurement of corneal astigmatism) AND (multifocal intraocular lenses implantation) AND (suitable))"}
{"candidate_id": "LLM03647", "doc_id": "NCT02764476_exc", "case_bucket": "or", "source_criterion": "Nonfluency or inability to communicate in English spoken language Inability to participate or attend biweekly 30 minute session over 14 weeks Frank psychosis Active self harm urges Serious medical illness Active substance or alcohol use or dependence that could interfere with participation Diagnoses of mental retardation, dementia or delirium Pregnant women", "candidate_expression": "((Frank) AND (Pregnant) AND (Serious) AND (medical illness) AND (psychosis) AND (that could interfere with participation) AND (women) AND ((alcohol use or dependence) OR (substance use or dependence)) AND ((delirium) OR (dementia) OR (mental retardation)) AND ((Active) OR (self harm urges)))"}
{"candidate_id": "LLM03648", "doc_id": "NCT02883400_exc", "case_bucket": "other", "source_criterion": "dual organ transplant", "candidate_expression": "(organ transplant dual)"}
{"candidate_id": "LLM03649", "doc_id": "NCT02888704_inc", "case_bucket": "or", "source_criterion": "Of either gender, aged ≥19 and ≤70 years Atopic dermatitis subjects who are coincident with Hanifin and Rajka diagnosis criteria Subacute and chronic atopic subjects who have atopic dermatitis symptoms continually at least 6 months Subjects with over moderate atopic dermatitis (SCORAD score > 20) Subjects who understand and voluntarily sign an informed consent form", "candidate_expression": "((> 20) AND (Atopic dermatitis) AND (Hanifin and Rajka diagnosis criteria) AND (SCORAD score) AND (Subjects who understand and voluntarily sign an informed consent form) AND (aged) AND (atopic dermatitis) AND (continually at least 6 months) AND (dermatitis symptoms) AND (over moderate) AND (≥19 and ≤70 years) AND ((Subacute) OR (chronic)))"}
{"candidate_id": "LLM03650", "doc_id": "NCT02186782_inc", "case_bucket": "or", "source_criterion": "Infertile women with eugonadotrophic anovulation/oligoovulation. Unexplained infertility.", "candidate_expression": "((Infertile) AND (Unexplained) AND (eugonadotrophic) AND (infertility) AND (women) AND ((anovulation) OR (oligoovulation)))"}
```
