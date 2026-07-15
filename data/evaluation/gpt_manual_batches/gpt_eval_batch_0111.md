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
{"candidate_id": "LLM02751", "doc_id": "NCT02596555_exc", "case_bucket": "or", "source_criterion": "Pregnancy (a negative serum or urine pregnancy test should be available for women of child-bearing potential before study inclusion) or lactation Women of childbearing potential who do not practice a medically accepted highly effective contraception during the trial and one month beyond History of hypersensitivity to the investigational medicinal product or to any drug with similar chemical structure or to any excipient present in the pharmaceutical form of the investigational medicinal product Participation in another clinical trial during the present clinical trial or within the last three months Medical or psychological condition that would not permit completion of the trial or signing of informed consent Use of a fibrinolytic agent, surgical thrombectomy, interventional (catheter-directed) thrombus aspiration or lysis, or use of a cava filter to treat the index episode of PE Treatment with any therapeutically dosed anticoagulant for more than 48 hours prior to enrolment Need for long-term treatment with a low molecular weight heparin, vitamin K antagonists or NOAC, for an indication other than the index PE episode, or for antiplatelet agents except acetylsalicylic acid at a dosage =100 mg/day; Active bleeding or known significant bleeding risk (e.g., gastrointestinal ulcer, malignant neoplasms, injuries or recent surgeries of the brain, spinal cord or eyes, recent intracranial bleedings, known or suspected esophagus varices, aneurysms or intraspinal or intracranial vascular abnormalities) Artificial heart valves requiring treatment with an anticoagulant Renal insufficiency with estimated creatinine clearance <30 ml/min/1.73m2 Chronic liver disease with aminotransferase levels two times or more above the local upper limit of normal range Concomitant administration of strong inhibitors of P-glycoprotein like ketoconazole, cyclosporin, itraconazole or dronedarone Unwillingness or inability to adhere to treatment or to the follow-up visits Life expectancy less than 6 months", "candidate_expression": "((<30 ml/min/1.73m2) AND (=100 mg/day;) AND (Active bleeding) AND (Artificial heart valves) AND (Chronic liver disease) AND (Life expectancy) AND (Medical or psychological condition that would not permit completion of the trial or signing of informed consent) AND (NOAC) AND (PE) AND (PE episode) AND (Participation in another clinical trial during the present clinical trial or within the last three months) AND (Pregnancy (a negative serum or urine pregnancy test should be available for women of child-bearing potential before study inclusion) or lactation) AND (Renal insufficiency) AND (Unwillingness or inability to adhere to treatment or to the follow-up visits) AND (Women of childbearing potential who do not practice a medically accepted highly effective contraception during the trial and one month beyond) AND (acetylsalicylic acid) AND (aminotransferase) AND (aneurysms) AND (anticoagulant) AND (antiplatelet agents) AND (bleeding risk) AND (brain) AND (cava filter) AND (cyclosporin) AND (dronedarone) AND (enrolment) AND (esophagus varices) AND (estimated creatinine clearance) AND (except) AND (eyes) AND (fibrinolytic agent) AND (gastrointestinal ulcer) AND (index) AND (inhibitors of P-glycoprotein) AND (injuries) AND (intracranial) AND (intracranial bleedings) AND (intraspinal) AND (itraconazole) AND (ketoconazole) AND (less than 6 months) AND (long-term) AND (low molecular weight heparin) AND (malignant neoplasms) AND (more than 48 hours prior to enrolment) AND (other) AND (significant) AND (spinal cord) AND (surgeries) AND (surgical thrombectomy,) AND (therapeutically) AND (thrombus aspiration) AND (thrombus lysis) AND (two times or more above the local upper limit of normal range) AND (vascular abnormalities)) AND (vitamin K antagonists))"}
{"candidate_id": "LLM02752", "doc_id": "NCT03046108_exc", "case_bucket": "or", "source_criterion": "Contraindication for the use of corticosteroids or local anesthetics Presence of inflammatory arthropathy or neuropathy Skin lesions in the area diabetes mellitus Infiltration or previous surgery in the area Refusal to participate in the study", "candidate_expression": "((Contraindication) AND (Refusal to participate in the stud) AND (Skin lesions) AND (diabetes mellitus) AND ((corticosteroids) OR (local anesthetics)) AND ((Infiltration) OR (previous surgery)) AND ((inflammatory arthropathy) OR (neuropathy inflammatory)))"}
{"candidate_id": "LLM02753", "doc_id": "NCT02550080_exc", "case_bucket": "or", "source_criterion": "Has previously received Dapsone therapy. The subject or any of their healthcare providers is aware of the subjects HLA type. Has been diagnosed with Glucose-6-phosphate dehydrogenase deficiency or methemoglobin reductase deficiency Satisfies any contraindications or restrictions to Dapsone therapy as listed in the product labels. Current severe illness, including heart, liver and renal failure, major organ allograft, malignancy requiring parenteral chemotherapy that can not be discontinued for the duration of the trial, or any other conditions which, in the opinion of the Investigator, would make the patient unsuitable for the study. Any laboratory abnormality at Screening which, in the opinion of the Investigator, should preclude the subject's participation in the study [alanine aminotransferase (ALT), glutamic oxaloacetic transaminase(ALT), et al). Pregnant women or women who are breastfeeding. Subject is, in the opinion of the Investigator, unable to complete the 6 week Observation period and the EPT assessments as required. A positive result for HLA-B*1301 in those subjects randomised to the genetic screening arm.", "candidate_expression": "((Dapsone) AND (HLA-B*1301) AND (chemotherapy) AND (contraindications) AND (positive) AND (regnant women or women who are breastfeeding) AND ((Glucose-6-phosphate dehydrogenase deficiency) OR (methemoglobin reductase deficiency)) AND ((heart failure) OR (liver failure) OR (major organ allograft) OR (malignancy) OR (renal failure)))"}
{"candidate_id": "LLM02754", "doc_id": "NCT02430740_inc", "case_bucket": "other", "source_criterion": "female infertile patients eligible for IVF treatment", "candidate_expression": "((IVF treatment) AND (eligible) AND (female) AND (infertile))"}
{"candidate_id": "LLM02755", "doc_id": "NCT02687724_exc", "case_bucket": "or", "source_criterion": "Female subjects who are pregnant or breast-feeding or considering becoming pregnant during the study Patients aged <18 years of age Patients who cannot give informed consent, Pregnant patients or those who are breastfeeding will be deemed ineligible. Prior treatment with any anti-TNF agent Contra-indication to use of GLM (Hypersensitivity to the active substance or to any of the excipients; Active tuberculosis (TB), acute or chronic Hepatitis B infection or other severe infections such as sepsis and/or opportunistic infections including HIV infection; Moderate or severe heart failure (NYHA class III/IV) Have symptoms or signs suggestive of current active or latent TB upon medical history, physical examination and/or chest radiograph, or positive Mycobacterium tuberculosis antigen-specific interferon-gamma release assay (IGRA) Patients with a history of, or at imminent risk for, colectomy; who required gastrointestinal surgery within 2 months before screening; History of colonic mucosal dysplasia or adenomatous colonic polyps that were not removed Screening stool study positive for enteric pathogens or Clostridium difficile toxin. Oral corticosteroids at a dose >40 mg prednisone or its equivalent per day; receipt of cyclosporine, tacrolimus, sirolimus, or mycophenolate mofetil within 8 weeks before the first study agent injection; or use of an investigational agent within 5 half-lives of that agent before the first study agent injection. Patients in recent receipt of live vaccinations within 4 weeks prior to enrolment", "candidate_expression": "((<18 years of age) AND (>40 mg prednisone per day) AND (Active) AND (Clostridium difficile toxin) AND (Contra-indication) AND (Female subjects who are pregnant or breast-feeding or considering becoming pregnant during the study) AND (GLM) AND (HIV infection) AND (Hepatitis B infection) AND (Hypersensitivity) AND (Moderate) AND (Mycobacterium tuberculosis antigen-specific interferon-gamma release assay (IGRA)) AND (NYHA) AND (Oral corticosteroids) AND (Pregnant patients or those who are breastfeeding will be deemed ineligible) AND (Prior) AND (TB) AND (active) AND (active substance) AND (acute) AND (adenomatous colonic polyps) AND (aged) AND (anti-TNF agent) AND (before the first study agent injection) AND (chest radiograph) AND (chronic) AND (class III/IV) AND (colectomy) AND (colonic mucosal dysplasia) AND (current) AND (cyclosporine) AND (enteric pathogens) AND (excipients) AND (gastrointestinal surgery) AND (heart failure) AND (history of) AND (imminent risk for) AND (investigational agent) AND (latent) AND (live vaccinations) AND (medical history) AND (mycophenolate mofetil) AND (not) AND (opportunistic infections) AND (physical examination) AND (positive) AND (removed) AND (sepsis) AND (severe) AND (severe infections) AND (sirolimus) AND (stool study) AND (tacrolimus) AND (treatment) AND (tuberculosis (TB)) AND (within 2 months before screening) AND (within 4 weeks prior to enrolment) AND (within 5 half-lives) AND (within 8 weeks before the first study agent injection))"}
{"candidate_id": "LLM02756", "doc_id": "NCT02884401_inc", "case_bucket": "or", "source_criterion": "Participants must present a diagnosis of osteoporosis based on DXA measurement of the bone mineral density at the femur neck and/or total hip and/or lumbar spine (T value 2.5 SD or more below the young female adult mean) within the past 24 months. Not in treatment with anti-resorptive agents (like bisphosphonates and denosumab) for more than 4 consecutive years, in order to reduce the risk of medication-related osteonecrosis of the jaws (Lo et al., 2010). = 50 years old. In self-reported menopause, defined as the permanent cessation of ovulation, for at least one year (Soules et al., 2001). Edentulous area involving a maximum of two teeth (wisdom teeth and second molars are excluded) and presenting at least one neighbouring tooth (e.g. gap in the area of a second premolar and first molar, with first premolar in place). Residual alveolar width = 4 mm (Milinkovic and Cordaro, 2014), residual alveolar height >8 mm, enough inter-arch space for a crown (at least 5 mm) and a minimum distance of 7 mm from the adjacent teeth (Shah and Lum, 2008). The width and height will be confirmed after x-ray examination in Visit 2. Possibility to restore a functional occlusion with a minimum of four occlusal units (i.e. pairs of occluding posterior teeth). Willingness to replace the missing tooth/teeth with dental implants Registration with a GDP", "candidate_expression": "((2.5 SD or more below the young female adult mean) AND (= 4 mm) AND (= 50 years) AND (>8 mm) AND (DXA) AND (Not) AND (Possibility to restore a functional occlusion with a minimum of four occlusal units (i.e. pairs of occluding posterior teeth)) AND (Residual alveolar width) AND (T value) AND (Willingness to replace the missing tooth/teeth with dental implants) AND (anti-resorptive agents) AND (at least one year) AND (bone mineral density) AND (cessation of ovulation) AND (menopause) AND (more than 4 consecutive years,) AND (old) AND (osteoporosis) AND (past 24 months) AND (permanent) AND (residual alveolar height) AND ((bisphosphonates) OR (denosumab)) AND ((femur neck) OR (lumbar spine) OR (total hip)))"}
{"candidate_id": "LLM02757", "doc_id": "NCT03363295_exc", "case_bucket": "or", "source_criterion": "Diabetic patients Patients with any macular changes prior to the surgery (epiretinal membranes, age macular disease, macular edema...) Patients who had any complication during phacoemulsification surgery", "candidate_expression": "((Diabetic) AND (age macular disease) AND (complication any during phacoemulsification surgery) AND (epiretinal membranes) AND (macular changes any prior to the surgery) AND (macular edema) AND (phacoemulsification surgery) AND (surgery))"}
{"candidate_id": "LLM02758", "doc_id": "NCT00787254_exc", "case_bucket": "or", "source_criterion": "Endoscopically confirmed gastric and/or duodenal ulcers on Day 1. Endoscopically confirmed active upper gastrointestinal hemorrhage on Day 1. Current or past history of aspirin-induced asthma or hypersensitivity to NSAIDs. Past or planned surgery affecting gastric acid secretion. Clinically significant hepatic or renal disorder. Serious cardiac dysfunction, hypertension, or hematological disorder.", "candidate_expression": "((Clinically significant) AND (Endoscopically) AND (NSAIDs) AND (Serious) AND (aspirin) AND (asthma aspirin-induced) AND (cardiac dysfunction) AND (duodenal ulcers Day 1) AND (gastric) AND (hematological disorder) AND (hepatic disorder) AND (hypersensitivity to NSAIDs Past planned) AND (hypertension) AND (past history) AND (renal disorder) AND (surgery affecting gastric acid secretion) AND (upper gastrointestinal hemorrhage Endoscopically confirmed active on Day 1 Day 1 Current))"}
{"candidate_id": "LLM02759", "doc_id": "NCT02621489_inc", "case_bucket": "or", "source_criterion": "Patients eligible for PCI with application of DES, due to ACS. Patients with known or newly diagnosed T2D (type 2 diabetes is diagnosed according to current WHO criteria or by the use of anti-diabetic drugs) Male and female subjects 18-80 years. HbA1c (accordingly to IFCC) 47 mmol/mol - 110 mmol/mol. Signed informed consent form.", "candidate_expression": "((18-80) AND (47 mmol/mol - 110 mmol/mol) AND (ACS) AND (DES) AND (HbA1c) AND (PCI) AND (Signed informed consent form) AND (T2D) AND (years) AND ((Male) OR (female)))"}
{"candidate_id": "LLM02760", "doc_id": "NCT02429583_inc", "case_bucket": "other", "source_criterion": "Willing to receive three doses of an FDA-approved Hepatitis B vaccine Volunteer chronically infected with HCV (as demonstrated by serology and/or viral load laboratory studies) Healthy volunteer without significant medical problems", "candidate_expression": "((HCV infected) AND (Healthy) AND (Willing to receive three doses of an FDA-approved Hepatitis B vaccine) AND (chronically) AND (volunteer))"}
{"candidate_id": "LLM02761", "doc_id": "NCT02886962_inc", "case_bucket": "or", "source_criterion": "Adult patients (= 18 years) Patient on hemodialysis treatment for at least 1 month Patient with a history of, or presenting a new episode of atrial fibrillation (either permanent or paroxysmal). Patient with a CHADS2VASC score =2 Patient with high risk of bleeding as defined by (1) HASBLED score =3 OR (2) HASBLED = CHADS2VASC score, OR (3) recent history of severe bleeding (type 3a, 3b, 3c), particularly cerebral or gastrointestinal, OR (4) prior recurrent (>2) history of falls. Patient capable of understanding information about the study and of giving his/her consent Patient informed of the preliminary medical exam results Patient with healthcare insurance Written consent signed", "candidate_expression": "((Adult) AND (CHADS2VASC score) AND (CHADS2VASC score =2) AND (HASBLED score =3) AND (Patient capable of understanding information about the study and of giving his/her consent) AND (Patient informed of the preliminary medical exam results) AND (Written consent signed) AND (atrial fibrillation new episode) AND (falls recurrent >2) AND (hemodialysis at least 1 month) AND (risk of bleeding high) AND (severe bleeding type 3a, 3b, 3c) AND (years = 18) AND ((cerebral) OR (gastrointestinal)))"}
{"candidate_id": "LLM02762", "doc_id": "NCT00050349_exc", "case_bucket": "or", "source_criterion": "Patients with symptomatic CNS metastases or leptomeningeal involvement Patients with known brain metastases, unless these metastases have been treated and/or have been stable for at least six months prior to study start. Subjects with a history of brain metastases must have a head CT with contrast to document either response or progression. Patients with bone metastases as the only site(s) of measurable disease Patients with hepatic artery chemoembolization within the last 6 months (one month if there are other sites of measurable disease) Patients who have been previously treated with radioactive directed therapies Patients who have been previously treated with epothilone Patients with any peripheral neuropathy or unresolved diarrhea greater than Grade 1 Patients with severe cardiac insufficiency patients taking Coumadin or other warfarin-containing agents with the exception of low dose warfarin (1 mg or less) for the maintenance of in-dwelling lines or ports Patients taking any experimental therapies history of another malignancy within 5 years prior to study entry except curatively treated non-melanoma skin cancer, prostate cancer, or cervical cancer in situ Patients with active or suspected acute or chronic uncontrolled infection including abcesses or fistulae Patients with a medical or psychiatric illness that would preclude study or informed consent and/or history of noncompliance to medical regimens or inability or unwillingness to return for all scheduled visits HIV+ patients Pregnant or lactating females.", "candidate_expression": "((+) AND (Grade) AND (HIV) AND (HIV+) AND (another malignancy) AND (at least six months prior to study start) AND (bone metastases) AND (brain metastases) AND (curatively treated) AND (epothilone) AND (except) AND (greater than 1) AND (head CT with contrast) AND (hepatic artery chemoembolization) AND (history of) AND (only site(s) of measurable disease) AND (other sites of measurable disease) AND (previously) AND (radioactive directed therapies) AND (severe cardiac insufficiency) AND (symptomatic) AND (uncontrolled infection) AND (unless) AND (warfarin) AND (with the exception of) AND (within 5 years prior to study entry) AND ((CNS metastases) OR (leptomeningeal involvement)) AND ((one month) OR (within the last 6 months)) AND ((peripheral neuropathy) OR (unresolved diarrhea)) AND ((Coumadin) OR (warfarin-containing agents)) AND ((1 mg or less) OR (low dose)) AND ((in-dwelling lines) OR (in-dwelling ports)) AND ((cervical cancer in situ) OR (non-melanoma skin cancer) OR (prostate cancer)) AND ((abcesses) OR (fistulae)) AND ((active) OR (suspected)) AND ((acute) OR (chronic)) AND ((medical illness) OR (psychiatric illness)) AND ((inability to return for all scheduled visits) OR (informed consent) OR (noncompliance to medical regimens) OR (preclude study) OR (unwillingness to return for all scheduled visit)) AND ((been stable for) OR (treated)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM02763", "doc_id": "NCT03117608_exc", "case_bucket": "or", "source_criterion": "Patients incapable to understanding and will; Patients participating in previous, concurrent or not, trials (ongoing or completed within three months); Patients surgically treated for the same defect within one year; Patients affected by malignancy; Patients affected by metabolic or thyroid disorders; Patients used to alcohol or drug (medication) abuse; Patients affected by synovitis; Varus or valgus misalignment exceeding 15°; Body Mass Index > 40; Patients with trauma within 6 months pre-operative.", "candidate_expression": "((> 40) AND (Body Mass Index) AND (Varus misalignment) AND (alcohol abuse) AND (completed) AND (drug abuse) AND (exceeding 15°) AND (incapable to understanding) AND (malignancy) AND (medication abuse) AND (metabolic disorders) AND (ongoing) AND (operative) AND (pre-operative) AND (previous) AND (surgically treated) AND (synovitis) AND (the same defect) AND (thyroid disorders) AND (trauma) AND (trials participating in) AND (valgus misalignment) AND (will incapable to) AND (within 6 months pre-operative) AND (within one year) AND (within three months))"}
{"candidate_id": "LLM02764", "doc_id": "NCT01236417_exc", "case_bucket": "or", "source_criterion": "Inability to comply with study requirements. Metastatic breast cancer. Patients with orthopedic or neuromuscular disorders that preclude participation in exercise. Rheumatoid arthritis. History of MI, angina or congestive heart failure. Pregnant or lactating females. Patients that are high risk for moderate exercise based on ACSM risk classification. Patients who exceed minimal physical activity recommendations from the US Surgeon General's Report: Accumulation of 30 minutes or more of moderate physical activity on most days of the week. Morbidly obese with BMI ≥ 40", "candidate_expression": "((ACSM risk classification) AND (BMI ≥ 40) AND (Inability to comply with study requirements.) AND (Morbidly obese) AND (Pregnant or lactating females.) AND (Rheumatoid arthritis) AND (breast cancer Metastatic) AND (exceed minimal physical activity recommendations) AND (females) AND (risk for moderate exercise high) AND ((Pregnant) OR (lactating)) AND ((disorders orthopedic) OR (neuromuscular disorders)) AND ((MI) OR (angina) OR (congestive heart failure)))"}
{"candidate_id": "LLM02765", "doc_id": "NCT03366779_inc", "case_bucket": "or", "source_criterion": "Age 18 to 75 years old (male or female). Patients with posterior or posterolateral disc herniations at one level between L1 and S1 with radiographic confirmation of neural compression using CT and/or MRI. At least six (6) weeks of failed, conservative treatment prior to surgery, or requires immediate surgery to prevent permanent disability. Minimum posterior disc height of 5mm at the index level(s). Lower back pain and/or sciatica with or without spinal claudication. Oswestry Questionnaire score of at least 40/100 at baseline. VAS leg pain of at least 40/100 at baseline. Psychosocially, mentally and physically able to fully comply with the clinical protocol and willing to adhere to follow-up schedule and requirements.", "candidate_expression": "((18 to 75 years old) AND (Age) AND (At least six (6) weeks) AND (CT) AND (Lower back pain) AND (MRI) AND (Minimum of 5mm) AND (Oswestry Questionnaire score) AND (Psychosocially, mentally and physically able to fully comply with the clinical protocol and willing to adhere to follow-up schedule and requirements.) AND (VAS leg pain) AND (at baseline) AND (at least 40/100) AND (conservative) AND (disc herniations) AND (failed) AND (female) AND (immediate) AND (index level(s)) AND (male) AND (neural compression) AND (one level between L1 and S1) AND (permanent disability) AND (posterior) AND (posterior disc height) AND (posterolateral) AND (prevent) AND (prior to surgery) AND (radiographic) AND (radiographic confirmation) AND (sciatica) AND (spinal claudication) AND (surgery) AND (treatment))"}
{"candidate_id": "LLM02766", "doc_id": "NCT03372304_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02767", "doc_id": "NCT02330705_inc", "case_bucket": "or", "source_criterion": "Mild male factor infertility or unexplained infertility.", "candidate_expression": "((Mild) AND ((male factor infertility) OR (unexplained infertility)))"}
{"candidate_id": "LLM02768", "doc_id": "NCT01665417_exc", "case_bucket": "or", "source_criterion": "Prior chemotherapy Prior treatment with gefitinib, erlotinib, or other drugs that target EGFR Patients must not be receiving any other investigational agents Any evidence of interstitial lung disease", "candidate_expression": "((Patients must not be receiving any other investigational agents) AND (Prior) AND (chemotherapy) AND (drugs that target EGFR) AND (erlotinib) AND (gefitinib) AND (interstitial lung disease) AND (treatment))"}
{"candidate_id": "LLM02769", "doc_id": "NCT00182520_inc", "case_bucket": "or", "source_criterion": "Outpatient with primary DSM- IV OCD Completion of a 14-week open label trial of one the following SRI's: fluoxetine 80 mg/day, paroxetine 60 mg/day, fluvoxamine 300 mg/day, clomipramine 250 mg/day, sertraline 200 mg/day, citalopram 60 mg/day, escitalopram 30 mg/day and demonstrating a non or partial responses to SRI treatment (CGI-I of 3 or 4, Y-BOCS reduction of < 35%) Stable (8 wks or longer) concurrent medications including benzodiazepines, sedative hypnotics, antipsychotics, and antidepressants.", "candidate_expression": "((CGI-I 3 4) AND (OCD primary DSM- IV) AND (Outpatient) AND (SRI treatment) AND (Y-BOCS reduction of < 35%) AND (antidepressants) AND (antipsychotics) AND (benzodiazepines) AND (citalopram 60 mg/day) AND (clomipramine 250 mg/day) AND (escitalopram 30 mg/day) AND (fluoxetine 80 mg/day) AND (fluvoxamine 300 mg/day) AND (medications Stable 8 wks or longer concurrent) AND (paroxetine 60 mg/day) AND (responses to) AND (sedative hypnotics) AND (sertraline 200 mg/day))"}
{"candidate_id": "LLM02770", "doc_id": "NCT02390973_inc", "case_bucket": "or", "source_criterion": "BMI = 35 type 2 diabetes HbA1c = 6,5 % or fasting glycemia =7mmol/l or non-fasting glycemia =11mmol/l able to consent", "candidate_expression": "((BMI = 35) AND (HbA1c = 6,5 %) AND (able to consent) AND (fasting glycemia =7mmol/l) AND (non-fasting glycemia =11mmol/l) AND (type 2 diabetes))"}
{"candidate_id": "LLM02771", "doc_id": "NCT01175044_exc", "case_bucket": "other", "source_criterion": "Inability to provide informed consent or to comply with study assessments (e.g. due to cognitive impairment or geographic distance). Age = 17. Allergy to povidone iodine. Any condition requiring antibiotics 14 days prior to arriving for surgery. Patients with chronic immunosuppression (such as HIV/AIDS). Unable to adhere to follow up schedule and treatment. Patients scheduled to undergo revision total knee arthroplasty for infectious reasons.", "candidate_expression": "((14 days prior to arriving for surgery) AND (= 17) AND (Age) AND (Allergy) AND (HIV/AIDS) AND (Inability to provide informed consent or to comply with study assessments (e.g. due to cognitive impairment or geographic distance).) AND (Unable to adhere to follow up schedule and treatment.) AND (antibiotics) AND (arriving for surgery) AND (chronic) AND (immunosuppression) AND (infectious reasons) AND (povidone iodine) AND (revision total knee arthroplasty) AND (surgery))"}
{"candidate_id": "LLM02772", "doc_id": "NCT02553226_inc", "case_bucket": "other", "source_criterion": "Women stimulated with Syntocinon® infusion for induction of labour (with or without cervical priming by prostaglandin)", "candidate_expression": "((Syntocinon®) AND (Syntocinon® infusion) AND (Women) AND (cervical priming) AND (induction of labour) AND (prostaglandin))"}
{"candidate_id": "LLM02773", "doc_id": "NCT02678663_exc", "case_bucket": "or", "source_criterion": "Anticoagulant therapy during the past 1 week of the procedure Known coagulopathy History of liver cirrhosis, chronic kidney disease, malignancy, inflammatory bowel disease, significant infectious disease, polyposis syndrome", "candidate_expression": "((Anticoagulant) AND (History) AND (coagulopathy) AND (during the past 1 week) AND (procedure) AND ((chronic kidney disease) OR (inflammatory bowel disease) OR (liver cirrhosis) OR (malignancy) OR (polyposis syndrome) OR (significant infectious disease)))"}
{"candidate_id": "LLM02774", "doc_id": "NCT02831166_inc", "case_bucket": "or", "source_criterion": "ST-segment elevation acute myocardial infarction patients during the first 12 hours of sympton onset; Intention to perform primary percutaneous coronary intervention; Signed informed consent; Patient eligible for transradial and transfemoral primary percutaneous coronary intervention, being pre-requisites: (a) familiarity of the operator with the radial and femoral techniques using vascular closure devices, (b) agreement of the operator to use the access route determined by the randomization process.", "candidate_expression": "((acute myocardial infarction ST-segment elevation during the first 12 hours of sympton onset) AND (percutaneous coronary intervention Intention to perform primary) AND (percutaneous coronary intervention eligible for primary) AND ((transfemoral) OR (transradial)))"}
{"candidate_id": "LLM02775", "doc_id": "NCT01088750_inc", "case_bucket": "other", "source_criterion": "Stage IA or IIA disease Not specified No prior therapy", "candidate_expression": "(EMPTY)"}
```
