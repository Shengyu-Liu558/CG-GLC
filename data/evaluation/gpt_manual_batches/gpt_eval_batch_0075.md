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
{"candidate_id": "LLM01851", "doc_id": "NCT02590315_exc", "case_bucket": "other", "source_criterion": "Personal history of breast cancer A terminal illness Patients who are unable to give informed consent Breast implants", "candidate_expression": "((Breast implants) AND (Personal history) AND (breast cancer) AND (terminal illness) AND (unable to give informed consent))"}
{"candidate_id": "LLM01852", "doc_id": "NCT02322203_exc", "case_bucket": "or", "source_criterion": "Subjects taking any lipid modification therapy, including but not limited to statins, fibrates and bile acid sequestrants. Subjects taking fish oil or any other supplements, which in the investigator s opinion may interfere with the study. Subjects with acute liver disease or active peptic ulcer disease. Subjects with elevated uric acid levels greater than 10 mg/dL or gout Pregnancy or women currently breastfeeding. Female subjects taking hormonal contraceptives or hormone replacement therapy may be included in this study only if they have been on a stable dose for at least 3 months. BMI less than 18.5 Subjects with weight that varies greater than 20% over the past 3 months. Subjects taking the following medications for at least six weeks, which may interfere with the study, will be excluded: BAS, antibiotics, anticoagulants, anticonvulsants, antiarrhythmic, Cyclosporine, Mycophenolate and Synthroid. Subjects with chronic diarrhea, gastric bypass or lap band procedures, ostomies, bowel motility problems, or other conditions that could affect intestinal fat absorption. Subjects initiating new medications or patients on multiple medications may also be excluded. Inability to swallow capsules Patients with a history of type I or type II diabetes or HbA1c greater than 6.5%. Volunteers may also be excluded, if in the opinion of the study investigators, they have some other condition or disorder that may adversely affect the outcome of the study or the safety of the volunteer.", "candidate_expression": "((BMI) AND (Female) AND (Inability to swallow capsules) AND (Subjects taking fish oil or any other supplements, which in the investigator s opinion may interfere with the study.) AND (Volunteers may also be excluded, if in the opinion of the study investigators, they have some other condition or disorder that may adversely affect the outcome of the study or the safety of the volunteer.) AND (active) AND (acute liver disease) AND (elevated) AND (fish oil) AND (for at least 3 months) AND (for at least six weeks) AND (greater than 10 mg/dL) AND (greater than 6.5%) AND (history) AND (less than 18.5) AND (lipid modification therapy) AND (over the past 3 months) AND (peptic ulcer disease) AND (stable dose) AND (varies greater than 20%) AND (weight) AND (women) AND ((gout) OR (uric acid levels)) AND ((Pregnancy) OR (breastfeeding)) AND ((hormonal contraceptives) OR (hormone replacement therapy)) AND ((BAS) OR (Cyclosporine) OR (Mycophenolate) OR (Synthroid) OR (antiarrhythmic) OR (antibiotics) OR (anticoagulants) OR (anticonvulsants)) AND ((bile acid sequestrants) OR (fibrates) OR (statins)) AND ((bowel motility problems) OR (chronic diarrhea) OR (conditions that could affect intestinal fat absorption) OR (gastric bypass) OR (lap band procedures) OR (ostomies)) AND ((HbA1c) OR (type I diabetes) OR (type II diabetes)))"}
{"candidate_id": "LLM01853", "doc_id": "NCT02974660_exc", "case_bucket": "or", "source_criterion": "no consent periprocedural complications requiring continuation of heparin or administration of protamine sulfate alergy to fish, protamine, protamine derivates, history of Humulin N, Novolin N, Novolin NPH, Gensulin N, SciLin N, NPH Iletin II and isophane insulin intake", "candidate_expression": "((Gensulin N) AND (Humulin N) AND (NPH Iletin II) AND (Novolin N) AND (Novolin NPH) AND (SciLin N) AND (alergy) AND (fish) AND (heparin) AND (history) AND (isophane insulin) AND (no consent) AND (periprocedural complications) AND (protamine) AND (protamine derivates) AND (protamine sulfate) AND (requiring))"}
{"candidate_id": "LLM01854", "doc_id": "NCT03082573_inc", "case_bucket": "other", "source_criterion": "Fluent in reading and writing in English language. = 21 years of age at the time of participation.", "candidate_expression": "((= 21 years) AND (age) AND (at the time of participation) AND (participation))"}
{"candidate_id": "LLM01855", "doc_id": "NCT02675153_exc", "case_bucket": "or", "source_criterion": "Allergic to sirolimus or serious side effects Need emergency surgery Accompanied with other severe disease (involve C.diff infection) Follow-up less than 1 year", "candidate_expression": "((C.diff infection) AND (Follow-up) AND (Need) AND (emergency surgery) AND (less than 1 year) AND (serious) AND (severe disease) AND (sirolimus) AND ((Allergic) OR (side effects)))"}
{"candidate_id": "LLM01856", "doc_id": "NCT02882113_inc", "case_bucket": "other", "source_criterion": "19 years old and above. Patients who previously have received a liver transplant over the last six months and within last three years. Patients who are on Tacrolimus immunosuppressive therapy twice a day for at least two weeks. Patients who have normal liver function and renal function. Patients who have been monitored without complication such as acute rejection. Patients willing to sign his/her consent.", "candidate_expression": "((Patients willing to sign his/her consent) AND (Tacrolimus twice a day at least two weeks) AND (acute rejection) AND (liver function normal) AND (liver transplant last six months and within last three years) AND (old 19 years and above) AND (renal function normal) AND NOT (complication))"}
{"candidate_id": "LLM01857", "doc_id": "NCT03484091_exc", "case_bucket": "or", "source_criterion": "Severe deformity (varus or values from mechanical axis more than 5 degrees Allergy to hyaluronic acid Pain on hip or ankle Post-traumatic or post surgery of lower extremity Post infection of knee Previous hyaluronic acid injection within 6 months Pregnancy or lactation Underlying Rheumatoid arthritis, stroke, malignancy, venous occlusion", "candidate_expression": "((Allergy) AND (Pain) AND (deformity Severe) AND (hyaluronic acid) AND (hyaluronic acid injection Previous within 6 months) AND (infection of knee Post) AND ((ankle) OR (hip)) AND ((Post-traumatic of lower extremity) OR (post surgery of lower extremity)) AND ((Pregnancy) OR (lactation)) AND ((Rheumatoid arthritis) OR (malignancy) OR (stroke) OR (venous occlusion)) AND ((values from mechanical axis more than 5 degrees) OR (varus)))"}
{"candidate_id": "LLM01858", "doc_id": "NCT03064568_exc", "case_bucket": "or", "source_criterion": "Patient with contraindication to misoprostol or vasopressin, personal history or cardiac or pulmonary disease, history of prior myomectomy", "candidate_expression": "((myomectomy) AND (prior) AND ((misoprostol) OR (vasopressin)) AND ((contraindication) OR (history) OR (personal history)) AND ((disease cardiac) OR (pulmonary disease)))"}
{"candidate_id": "LLM01859", "doc_id": "NCT02489045_exc", "case_bucket": "or", "source_criterion": "Females who are pregnant or nursing. Patients not scheduled for trans-jugular liver biopsy Patients who have received an investigational drug in the 30 days before study drug administration, or will receive one within 72 h afterwards,. Patients with known or suspected right-to-left, bi-directional, or transient right-to-left cardiac shunts Patients with pulmonary hypertension or unstable cardiopulmonary conditions Patients currently on chemotherapy or with other primary cancers requiring systemic or hepatic loco-regional treatment. Patients who are medically unstable, patients who are seriously or terminally ill, and patients whose clinical course is unpredictable. For example: Patients on life support or in a critical care unit. Patients with unstable occlusive disease (e.g., crescendo angina) Patients with clinically unstable cardiac arrhythmias, such as recurrent ventricular tachycardia. Patients with uncontrolled congestive heart failure (NYHA Class IV) Patients with recent cerebral hemorrhage. Patients who have undergone surgery within 24 hours prior to the study sonographic examination. Patients with a history of anaphylactic allergy to eggs or egg products, manifested by one or more of the following symptoms: generalized urticaria, difficulty in breathing, swelling of the mouth and throat, hypotension, or shock. (Subjects with nonanaphylactic allergies to eggs or egg products may be enrolled in the study, but must be watched carefully for 1 h following the administration of SONAZOID). Patients with congenital heart defects. Patients with severe emphysema, pulmonary vasculitis, or a history of pulmonary emboli. Patients with respiratory distress syndrome Patients with thrombosis within the hepatic, portal, or mesenteric veins.", "candidate_expression": "((Class IV) AND (Females) AND (NYHA) AND (anaphylactic allergy) AND (cardiac arrhythmias) AND (cerebral hemorrhage) AND (clinically unstable) AND (congenital heart defects) AND (congestive heart failure) AND (critical care unit) AND (currently) AND (life support) AND (not) AND (other) AND (recent) AND (recurrent) AND (respiratory distress syndrome) AND (scheduled) AND (severe) AND (sonographic examination) AND (surgery) AND (the study sonographic examination) AND (thrombosis) AND (trans-jugular liver biopsy) AND (uncontrolled) AND (unstable occlusive disease) AND (ventricular tachycardia) AND (within 24 hours prior to the study sonographic examination) AND ((known) OR (suspected)) AND ((pulmonary hypertension) OR (unstable cardiopulmonary conditions)) AND ((chemotherapy) OR (primary cancers)) AND ((hepatic loco-regional treatment) OR (systemic loco-regional treatment)) AND ((clinical course is unpredictable) OR (medically unstable) OR (seriously ill) OR (terminally ill)) AND ((nursing) OR (pregnant)) AND ((egg products) OR (eggs)) AND ((difficulty in breathing) OR (generalized urticaria) OR (hypotension) OR (shock) OR (swelling of the mouth) OR (swelling of the throat)) AND ((emphysema) OR (pulmonary emboli) OR (pulmonary vasculitis)) AND ((hepatic veins) OR (mesenteric veins) OR (portal veins)) AND ((bi-directional cardiac shunts) OR (right-to-left cardiac shunts) OR (transient right-to-left cardiac shunts)))"}
{"candidate_id": "LLM01860", "doc_id": "NCT03084588_inc", "case_bucket": "other", "source_criterion": "All patients presenting for elective shoulder arthroscopic procedures will be eligible for enrollment.", "candidate_expression": "(shoulder arthroscopic procedures elective)"}
{"candidate_id": "LLM01861", "doc_id": "NCT03027115_inc", "case_bucket": "other", "source_criterion": "Male 18 years of age Presenting with hernia requiring surgical intervention", "candidate_expression": "((18 years) AND (Male) AND (age) AND (hernia) AND (requiring) AND (surgical intervention))"}
{"candidate_id": "LLM01862", "doc_id": "NCT02299063_exc", "case_bucket": "or", "source_criterion": "recent surgery (< 3 months) previous chemotherapy previous transfusion of blood products neurodevelopmental disorders (including Trisomy 21) supplemental oxygen requirement (< 3 months) asthma requiring regular therapy obstructive sleep apnea the presence of concurrent infection or inflammation a known allergy to dexmedetomidine hydrochloride", "candidate_expression": "((Trisomy 21) AND (allergy) AND (asthma) AND (chemotherapy previous) AND (dexmedetomidine hydrochloride) AND (neurodevelopmental disorders) AND (obstructive sleep apnea) AND (regular therapy) AND (supplemental oxygen requirement < 3 months) AND (surgery recent < 3 months) AND (transfusion of blood products previous) AND ((infection) OR (inflammation)))"}
{"candidate_id": "LLM01863", "doc_id": "NCT02790593_inc", "case_bucket": "or", "source_criterion": "Age >18 years old 1cm squared surface area Venous incompetence confirmed by clinical assessment and duplex ultrasound scan No evidence of arterial disease (Arterial Duplex or Ankle Brachial Pressure Index >0.9) Patients able to complete trial procedures Patients with a life expectancy of greater than 1 year", "candidate_expression": "((1cm squared) AND (>0.9) AND (>18 years old) AND (Age) AND (Ankle Brachial Pressure Index) AND (Arterial Duplex) AND (No) AND (Patients able to complete trial procedures) AND (Venous incompetence) AND (arterial disease) AND (clinical assessment) AND (duplex ultrasound scan) AND (greater than 1 year) AND (life expectancy) AND (surface area))"}
{"candidate_id": "LLM01864", "doc_id": "NCT03062358_exc", "case_bucket": "or", "source_criterion": "Is currently participating or has participated in a study with an investigational agent or using an investigational device within 4 weeks of the first dose of study medication Has received sorafenib or oxaliplatin-based chemotherapy within 14 days of first dose of study medication Has had esophageal or gastric variceal bleeding within the last 6 months Has clinically apparent ascites on physical examination Has portal vein invasion at the main portal branch (Vp4), inferior vena cava, or cardiac involvement of HCC based on imaging Has had clinically diagnosed hepatic encephalopathy in the last 6 months Has had a solid organ or hematologic transplant Has had prior systemic therapy for HCC in the advanced (incurable) setting other than sorafenib or oxaliplatin-based chemotherapy, prior to start of study medication Has an active autoimmune disease that has required systemic treatment in the past 2 years. Replacement therapy is not considered a form of systemic treatment. Has a diagnosis of immunodeficiency or is receiving systemic steroid therapy or any other form of immunosuppressive therapy within 7 days prior to the first dose of study medication Has received locoregional therapy to liver (transcatheter chemoembolization [TACE], transcatheter embolization [TAE], hepatic arterial infusion [HAI], radiation, radioembolization, or ablation) or other site within 4 weeks prior to the first dose of study medication Has had major surgery to liver or other site within 4 weeks prior to the first dose of study medication Has had a minor surgery ≤7 days prior to the first dose of study medication Has not recovered adequately (i.e., Grade ≤1 or baseline) from the toxicity and/or complications from any intervention prior to study start Has a diagnosed additional malignancy within 3 years prior to first dose of study medication with the exception of curatively treated basal cell carcinoma of the skin, squamous cell carcinoma of the skin and/or curatively resected in situ cancers Has a known history of, or any evidence of, central nervous system (CNS) metastases and/or carcinomatous meningitis Has a history of (non-infectious) pneumonitis that required steroids or current pneumonitis Has an active infection requiring systemic therapy Is pregnant or breast feeding or expecting to conceive or father starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication Has received prior immunotherapy with an anti-Programmed Cell Death Receptor 1 (PD-1), Programmed Cell Death Receptor Ligand 1 (anti-PD-L1), or anti- Programmed Cell Death Receptor Ligand 2 (PD-L2) or has previously participated in clinical studies with pembrolizumab Has a known history of human immunodeficiency virus (HIV) Has untreated active Hepatitis B Has hepatitis C in which participants received therapy for HCV <4 weeks prior to receiving pembrolizumab Has received a live vaccine within 30 days prior to the first dose of study therapy", "candidate_expression": "((HCC) AND (Hepatitis B untreated active) AND (ablation other site) AND (ascites) AND (autoimmune disease active in the past 2 years) AND (chemotherapy sorafenib or oxaliplatin-based within 14 days) AND (for up to 120 days after the last dose of study medication the last dose of study medication) AND (hepatic arterial infusion [HAI]) AND (hepatic encephalopathy in the last 6 months) AND (hepatitis C) AND (human immunodeficiency virus (HIV) history) AND (imaging) AND (immunodeficiency) AND (infection active requiring systemic therapy) AND (live vaccine 30 days prior) AND (locoregional therapy liver within 4 weeks prior) AND (major surgery liver within 4 weeks prior other site) AND (malignancy additional within 3 years prior to first dose of study medication) AND (minor surgery ≤7 days prior) AND (non-infectious) pneumonitis history) AND (oxaliplatin) AND (pembrolizumab) AND (radiation) AND (radioembolization) AND (recovered adequately) AND (resected curatively) AND (sorafenib) AND (systemic therapy) AND (systemic therapy starting from the first dose of study medication) AND (systemic treatment) AND (therapy for HCV <4 weeks prior) AND (throughout the study period the study period) AND (transcatheter chemoembolization [TACE]) AND (transcatheter embolization [TAE]) AND (treated curatively) AND NOT (chemotherapy sorafenib or oxaliplatin-based) AND ((Programmed Cell Death Receptor Ligand 1 (anti-PD-L1)) OR (anti- Programmed Cell Death Receptor Ligand 2 (PD-L2)) OR (anti-Programmed Cell Death Receptor 1 (PD-1))) AND ((inferior vena cava) OR (main portal branch (Vp4))) AND ((cardiac involvement) OR (portal vein invasion)) AND ((hematologic transplant) OR (solid organ transplant)) AND ((immunosuppressive therapy) OR (systemic steroid therapy)) AND ((basal cell carcinoma of the skin curatively treated) OR (in situ cancers curatively resected) OR (squamous cell carcinoma of the skin)) AND ((esophageal variceal bleeding) OR (gastric variceal bleeding)) AND ((carcinomatous meningitis) OR (central nervous system (CNS) metastases)) AND ((pneumonitis current) OR (steroids)) AND ((breast feeding) OR (expecting to conceive) OR (expecting to father) OR (pregnant)) AND ((immunotherapy) OR (participated in clinical studies with pembrolizumab)))"}
{"candidate_id": "LLM01865", "doc_id": "NCT02787070_exc", "case_bucket": "other", "source_criterion": "General danger signs or symptoms of severe malaria Anaemia, defined as Hb <9g/dl G6PD deficiency (as determined by FST) Pregnant women as determined by Urine ß-HCG pregnancy test Known hypersensitivity to any of the drugs given", "candidate_expression": "((Anaemia) AND (G6PD deficiency) AND (Hb <9g/dl) AND (Pregnant women as determined by Urine ß-HCG pregnancy test) AND (drugs) AND (hypersensitivity) AND (malaria severe))"}
{"candidate_id": "LLM01866", "doc_id": "NCT02816762_inc", "case_bucket": "or", "source_criterion": "Subjects aged 18 to 80 years old Overweight or obesity (BMI =25 kg/m2) Previous diagnosis of type 2 diabetes, fulfilling at least one of the following criteria: 1) current treatment with oral antidiabetic drugs and/or insulin; 2) a fasting glucose value above 126 mg/dl on at least 2 occasions; 3) blood glucose level at 2 hours after an oral glucose tolerance test is equal to or more than 200 mg/dl; or 4) a glycated hemoglobin (HbA1c) level > 6.5 % Clinical diagnosis of diabetic nephropathy, with a urinary albumin/creatinine ratio >30 mg/g and an estimated glomerular filtration rate more than 20 ml/min per 1.73 m2. Treatment with stable doses of angiotensin-converting enzyme inhibitors, angiotensin II receptor blockers or anti-aldosterone agents in the last four weeks.", "candidate_expression": "((18 to 80 years old) AND (=25 kg/m2) AND (> 6.5 %) AND (>30 mg/g) AND (BMI) AND (Previous) AND (above 126 mg/dl) AND (aged) AND (an oral glucose tolerance test) AND (at 2 hours after an oral glucose tolerance test) AND (at least one) AND (current) AND (diabetic nephropathy) AND (equal to or more than 200 mg/dl) AND (estimated glomerular filtration rate) AND (in the last four weeks) AND (more than 20 ml/min per 1.73 m2) AND (on at least 2 occasions) AND (oral glucose tolerance test) AND (stable doses) AND (type 2 diabetes) AND (urinary albumin/creatinine ratio) AND ((insulin) OR (oral antidiabetic drugs)) AND ((blood glucose level) OR (fasting glucose) OR (glycated hemoglobin (HbA1c) level)) AND ((angiotensin II receptor blockers) OR (angiotensin-converting enzyme inhibitors) OR (anti-aldosterone agents)) AND ((Overweight) OR (obesity)))"}
{"candidate_id": "LLM01867", "doc_id": "NCT03315975_inc", "case_bucket": "or", "source_criterion": "adults capable of providing consent have a diagnosis of locally advanced or metastatic melanoma", "candidate_expression": "((adults) AND (capable of providing consent) AND (melanoma) AND ((locally advanced) OR (metastatic)))"}
{"candidate_id": "LLM01868", "doc_id": "NCT03555526_exc", "case_bucket": "or", "source_criterion": "aged less than 20 years history of gastric resection surgery history of allergy to study drugs pregnancy or lactating women severe underlying illness, such as end stage renal disease, decompensated liver cirrhosis, or non-curative malignancy", "candidate_expression": "((aged) AND (allergy) AND (decompensated) AND (gastric resection surgery) AND (less than 20 years) AND (non-curative) AND (severe underlying illness) AND (study drugs) AND (women) AND ((end stage renal disease) OR (liver cirrhosis) OR (malignancy)) AND ((lactating) OR (pregnancy)))"}
{"candidate_id": "LLM01869", "doc_id": "NCT02600000_inc", "case_bucket": "scope", "source_criterion": "Diagnosis of Heart Failure; Lower left ventricular ejection fraction 45% (LVEF <45%) assessed by simple and recent echocardiogram; Functional Class II and III by the New York Heart Association (NYHA) Clinically stable; Ex-smokers over five years; Maximal inspiratory pressure (MIP) <70% of predicted; Forced expiratory volume/Forced vital capacity (FEV1 / FVC) > 70% of predicted;", "candidate_expression": "((45%) AND (<45%) AND (<70% of predicted) AND (> 70% of predicted) AND (Class II and III) AND (Clinically stable) AND (Ex-smokers) AND (Forced expiratory volume/Forced vital capacity (FEV1 / FVC)) AND (Heart Failure) AND (LVEF) AND (Lower left ventricular ejection fraction) AND (Maximal inspiratory pressure (MIP)) AND (New York Heart Association (NYHA)) AND (echocardiogram) AND (over five years) AND (recent))"}
{"candidate_id": "LLM01870", "doc_id": "NCT02862912_exc", "case_bucket": "or", "source_criterion": "Any contraindication to neuraxial anesthesia (history of neurologic disease (e.g., multiple sclerosis, spinal stenosis, central or peripheral neuropathy) Pre-existing/chronic back pain Ester local anesthetic allergy, PABA allergy History of atypical cholinesterase (CP is metabolized by cholinesterase)", "candidate_expression": "((Ester local anesthetic) AND (History) AND (PABA) AND (Pre-existing) AND (allergy) AND (atypical cholinesterase) AND (back pain) AND (central neuropathy) AND (chronic) AND (contraindication) AND (history) AND (multiple sclerosis) AND (neuraxial anesthesia) AND (neurologic disease) AND (peripheral neuropathy) AND (spinal stenosis))"}
{"candidate_id": "LLM01871", "doc_id": "NCT01009359_inc", "case_bucket": "or", "source_criterion": "Able to give fully informed consent in writing Males or females aged >/= 50 years No significant disease or drug use Absence of any sign of dementia/cognitive impairment in neuropsychological examinationsPatients for brain imaging: Patient and designee capable of giving fully informed consent in writing Patient fulfils DSM-IV and NINCDS-ADRA criteria for probable Alzheimers disease", "candidate_expression": "((>/= 50 years) AND (Able to give fully informed consent in writing) AND (Absence of) AND (Alzheimers disease) AND (DSM-IV criteria) AND (Males) AND (NINCDS-ADRA criteria) AND (No) AND (Patient and designee capable of giving fully informed consent in writing) AND (aged) AND (cognitive impairment) AND (dementia) AND (disease) AND (drug use) AND (females) AND (fulfils) AND (neuropsychological examinations) AND (probable) AND (sign of cognitive impairment) AND (sign of dementia) AND (significant))"}
{"candidate_id": "LLM01872", "doc_id": "NCT02851303_inc", "case_bucket": "or", "source_criterion": "Born at University of New Mexico Hospital Greater than 34 weeks gestation Primary in-utero drug exposure was opioids other than buprenorphine Maternal or infant urine drug screen positive for methadone and/or opioids on admission", "candidate_expression": "((Born) AND (University of New Mexico Hospital) AND (drug exposure in-utero) AND (gestation Greater than 34 weeks) AND (opioids) AND (urine drug screen positive) AND NOT (buprenorphine) AND ((Maternal) OR (infant)) AND ((methadone) OR (opioids)))"}
{"candidate_id": "LLM01873", "doc_id": "NCT02137369_inc", "case_bucket": "or", "source_criterion": "Men or women aged 18-60 years. Primary psychiatric diagnosis of Major Depressive Disorder, without psychotic features, confirmed via SCID-IV structured diagnostic interview. Screening Hamilton Depression Rating Scale (HAMD) = 18; and Baseline HAMD = 15. If the patient is a woman of child-bearing potential, she must agree to use an acceptable form of birth control for duration of study participation. Able to understand and provide informed consent for participation.", "candidate_expression": "((Able to understand and provide informed consent for participation) AND (HAMD) AND (HAMD Baseline = 15) AND (If the patient is a woman of child-bearing potential, she must agree to use an acceptable form of birth control for duration of study participation) AND (Major Depressive Disorder Primary) AND (Men) AND (Men or women aged 18-60 years.) AND (Screening Hamilton Depression Rating Scale = 18) AND (aged 18-60 years) AND (women) AND NOT (psychotic features))"}
{"candidate_id": "LLM01874", "doc_id": "NCT02462317_exc", "case_bucket": "or", "source_criterion": "Previous antispastic drugs Contraindication for baclofen or toxin Antecedent of epileptic seizure Psychiatric antecedent", "candidate_expression": "((Antecedent) AND (Contraindication) AND (Previous) AND (Psychiatric) AND (antecedent) AND (antispastic drugs) AND (epileptic seizure) AND ((baclofen) OR (toxin)))"}
{"candidate_id": "LLM01875", "doc_id": "NCT01064752_inc", "case_bucket": "other", "source_criterion": "1. HIV infection with plasma and CSF HIV RNA concentrations (using Roche Amplicor assay) > 1,000 copies/ mL (available after baseline LP). 2. Off antiretroviral therapy (ART) for > 6 weeks before the study and no plans to begin treatment for the study duration. (The decision of whether or not a subject takes antiretroviral therapy will be made by the subject in consultation with his/her primary care provider prior to screening for this study.) 3. Predicted adherence to the medication. 4. Capable of providing informed consent. 5. > 18 years old 6. CD4 cell counts >150 cells/μL (though likely most, if not all, will be >250 cells/μL). 7. When available, subjects will be screened for stability of blood CD4 and HIV RNA levels.", "candidate_expression": "((CD4 cell counts >150 cells/μL >250 cells/μL) AND (CSF HIV RNA concentration > 1,000 copies/ mL) AND (Capable of providing informed consent.) AND (HIV infection) AND (Off antiretroviral therapy (ART) > 6 weeks before the study) AND (Roche Amplicor assay) AND (antiretroviral therapy (ART)) AND (old 18 years) AND (plasma concentration > 1,000 copies/ mL) AND (treatment plans to begin for the study duration study))"}
```
