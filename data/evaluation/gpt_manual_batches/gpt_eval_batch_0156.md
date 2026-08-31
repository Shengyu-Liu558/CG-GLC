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
{"candidate_id": "LLM03876", "doc_id": "NCT02650024_inc", "case_bucket": "or", "source_criterion": "Adult (= 18 years old) subjects with chronic genotype 1 HCV and NCI with a GDS greater than or equal to 0.5 (n=60). Presence of chronic HCV infection based on chart review will be defined as positive for anti-HCV antibody or HCV RNA at least 6 months before screening. For the HIV/HCV co-infected group only, subjects must have HIV. HIV status will be obtained through self report. Self report will be confirmed at screening using a HIV-1 point of care test. In the event that point of care test and self-report are discordant, then HIV status will be confirmed by a licensed Western blot or a second antibody test. HIV/HCV co-infected subjects (n=12) must also have a HIV RNA measurement <50 copies/mL at the pre-treatment visit. Platelets >150,000 Aspartate aminotransferase (AST)/Alanine aminotransferase (ALT) <10x upper limit of normal Creatinine clearance >30 milliliters/minute/1.73 centimeter squared", "candidate_expression": "((<10x upper limit of normal) AND (<50 copies/mL) AND (= 18 years old) AND (>150,000) AND (>30 milliliters/minute/1.73 centimeter squared) AND (Adult) AND (Alanine aminotransferase (ALT)) AND (Aspartate aminotransferase (AST)) AND (Creatinine clearance) AND (GDS) AND (HCV) AND (HCV infection) AND (HIV) AND (HIV RNA measurement) AND (Platelets) AND (at least 6 months before screening) AND (at the pre-treatment visit) AND (chronic) AND (co-infected) AND (genotype 1) AND (greater than or equal to 0.5) AND (old) AND (positive) AND ((HCV RNA) OR (anti-HCV antibody)) AND ((HCV) OR (NCI)))"}
{"candidate_id": "LLM03877", "doc_id": "NCT01888965_inc", "case_bucket": "or", "source_criterion": "Patients with a confirmed diagnosis of: 1. Stage 4 colon cancer either s/p metastasectomy or post-initial chemotherapy or maintenance \"standard of care\", either involving 5-fluorouracil/leucovorin (5-FU/LV) alone or continual bevacizumab alone. Patients in maintenance cohort must have had 2 consecutive CT scans showing stable disease and not be experiencing significant prior treatment-related toxicity above Grade 1. 2. Pancreas cancer, either s/p resection and adjuvant chemotherapy or locally advanced pancreas cancer s/p chemotherapy and radiation. Initial chemotherapy or radiation therapy may have been stopped between 2 weeks and 2 months prior to study start, and patients must have recovered from prior treatment related toxicity to grade 1 or less. Prior surgery, including tumor resection or metastasectomy must have been performed at least 4 weeks prior to study enrollment. No concomitant anti-cancer treatment is allowed Age >/= 18 years Performance status of 0-1 Adequate hepatic, bone marrow, and renal function Partial thromboplastin time (PTT) must be </= 1.5 x upper normal limit of institution's normal range and INR (International Normalized Ratio) < 1.5. Life expectancy >/= 4 months for maintenance cohorts and >/= 6 months for adjuvant cohorts Women of childbearing potential must have a negative serum pregnancy test within 14 days prior to initiation of treatment and must not be lactating. Subject is capable of understanding and complying with protocol demands and able to sign and date the informed consent", "candidate_expression": "((5-fluorouracil/leucovorin (5-FU/LV)) AND (Age >/= 18 years) AND (CT scans 2) AND (INR (International Normalized Ratio) < 1.5) AND (Life expectancy) AND (No concomitant anti-cancer treatment is allowed) AND (Pancreas cancer) AND (Partial thromboplastin time (PTT) </= 1.5 x upper normal limit) AND (Performance status 0-1) AND (Subject is capable of understanding and complying with protocol demands and able to sign and date the informed consent) AND (Women) AND (adjuvant chemotherapy) AND (adjuvant cohorts >/= 6 months) AND (bevacizumab) AND (bone marrow function Adequate) AND (chemotherapy) AND (childbearing potential) AND (colon cancer Stage 4) AND (disease stable) AND (function hepatic Adequate) AND (maintenance \"standard of care\") AND (maintenance cohorts >/= 4 months) AND (metastasectomy) AND (pancreas cancer locally advanced) AND (post-initial chemotherapy) AND (radiation) AND (radiation therapy) AND (recovered from prior treatment) AND (renal function Adequate) AND (resection) AND (s/p adjuvant chemotherapy) AND (s/p chemotherapy) AND (s/p metastasectomy) AND (s/p radiation) AND (s/p resection) AND (serum pregnancy test negative within 14 days prior to initiation of treatment) AND (surgery Prior at least 4 weeks prior to study enrollment) AND (treatment prior) AND (tumor resection) AND NOT (treatment-related toxicity prior) AND NOT (lactating))"}
{"candidate_id": "LLM03878", "doc_id": "NCT03304496_exc", "case_bucket": "or", "source_criterion": "Pregnant. Not have informed consent for the present clinical trial, or do not fully understand the meaning of informed consent. With acute myocardial infarction with ST segment elevation in the first 12 hours from the onset of symptoms. With any acute coronary syndrome complicated with acute pulmonary edema, cardiogenic shock and / or malignant ventricular arrhythmias. In which a cardiac catheterization is planned a priori to be performed via femoral, brachial or ulnar. Patients in whom first attempt of arterial puncture is performed by 2nd year interventional cardiology fellow or by physician in charge. Participating in another clinical trial. Be allergic or have contraindications to nitroglycerin or other nitrates. Any phosphodiesterase 5 inhibitor (sildenafil, tadalafil, avanafil, vardenafil) has been taken within 72 hours prior to the study.", "candidate_expression": "((Not have informed consent for the present clinical trial, or do not fully understand the meaning of informed consent) AND (Pregnant) AND (ST segment elevation) AND (acute coronary syndrome) AND (acute myocardial infarction) AND (acute pulmonary edema) AND (allergic) AND (avanafil) AND (brachial) AND (cardiac catheterization) AND (cardiogenic shock) AND (contraindications) AND (femoral) AND (in the first 12 hours from the onset of symptoms) AND (malignant) AND (nitrates) AND (nitroglycerin) AND (phosphodiesterase 5 inhibitor) AND (sildenafil) AND (study) AND (tadalafil) AND (the onset of symptoms) AND (ulnar) AND (vardenafil) AND (ventricular arrhythmias) AND (within 72 hours prior to the study))"}
{"candidate_id": "LLM03879", "doc_id": "NCT03195153_exc", "case_bucket": "other", "source_criterion": "not diabetic patient; patients in dual antiplatelet therapy; patient with severe renal failure; patient poor responders", "candidate_expression": "((dual antiplatelet therapy) AND (poor responders) AND (renal failure severe) AND NOT (diabetic))"}
{"candidate_id": "LLM03880", "doc_id": "NCT02137369_inc", "case_bucket": "or", "source_criterion": "Men or women aged 18-60 years. Primary psychiatric diagnosis of Major Depressive Disorder, without psychotic features, confirmed via SCID-IV structured diagnostic interview. Screening Hamilton Depression Rating Scale (HAMD) = 18; and Baseline HAMD = 15. If the patient is a woman of child-bearing potential, she must agree to use an acceptable form of birth control for duration of study participation. Able to understand and provide informed consent for participation.", "candidate_expression": "((Able to understand and provide informed consent for participation) AND (HAMD) AND (HAMD Baseline = 15) AND (If the patient is a woman of child-bearing potential, she must agree to use an acceptable form of birth control for duration of study participation) AND (Major Depressive Disorder Primary) AND (Men or women aged 18-60 years.) AND (Screening Hamilton Depression Rating Scale = 18) AND (aged 18-60 years) AND NOT (psychotic features) AND ((Men) OR (women)))"}
{"candidate_id": "LLM03881", "doc_id": "NCT02396732_inc", "case_bucket": "or", "source_criterion": "Age 18 years or older Blunt or penetrating trauma Requires VTE thromboprophylaxis High-risk for VTE", "candidate_expression": "((18 years or older) AND (Age) AND (High-risk) AND (VTE) AND (thromboprophylaxis) AND ((Blunt trauma) OR (penetrating trauma)))"}
{"candidate_id": "LLM03882", "doc_id": "NCT02851888_exc", "case_bucket": "or", "source_criterion": "Current or planned pregnancy History of neuropathic pain, chronic pain syndrome, or preoperative use of narcotic or neuropathic pain medicine Radiographic signs of osteoarthritis (> Tonis grade 1) Inability to attend follow up visits Documented allergy to local anesthetic", "candidate_expression": "((Inability attend follow up visits) AND (Radiographic) AND (Tonis grade > 1) AND (allergy) AND (local anesthetic) AND (osteoarthritis Radiographic signs) AND (pregnancy) AND ((Current) OR (planned)) AND ((chronic pain syndrome) OR (neuropathic pain)) AND ((narcotic medicine) OR (neuropathic pain medicine)))"}
{"candidate_id": "LLM03883", "doc_id": "NCT01715714_exc", "case_bucket": "or", "source_criterion": "Any concomitant cardiovascular procedure to CABG (i.e. valve, aortic or carotid surgery) Acute ST-segment-elevation myocardial infarction (STEMI) NSTE-ACS with cardiogenic shock warranting emergent salvage surgery within 12 hrs from hospital admission History of atrial fibrillation or muscle disease (myopathy) Current renal (creatinine>2x upper limit of normal (ULN), dialysis, kidney transplant) or hepatic dysfunction (AST/ALT>2x ULN, liver transplant or neoplasm) Inability of oral drug intake", "candidate_expression": "((>2x ULN) AND (>2x upper limit of normal (ULN)) AND (ALT) AND (AST) AND (Acute ST-segment-elevation myocardial infarction) AND (CABG) AND (Inability) AND (Inability of) AND (NSTE-ACS) AND (STEMI) AND (aortic surgery) AND (atrial fibrillation) AND (cardiogenic shock) AND (cardiovascular procedure) AND (carotid surgery) AND (concomitant) AND (creatinine) AND (dialysis) AND (hepatic dysfunction) AND (hospital admission) AND (kidney transplant) AND (liver transplant) AND (muscle disease) AND (myopathy) AND (neoplasm) AND (oral drug) AND (oral drug intake) AND (renal dysfunction) AND (salvage surgery) AND (valve surgery) AND (warranting) AND (within 12 hrs from hospital admission))"}
{"candidate_id": "LLM03884", "doc_id": "NCT02748330_inc", "case_bucket": "or", "source_criterion": "Provision of written informed consent (by patient or appropriate designee according to local regulations) prior to any study specific procedures. Aged 18 years or older, male or female. History of stable angina pectoris with angiographic evidence of CAD (diameter stenosis = 50%) in major, i.e., left main, left anterior descending, left circumflex, and right coronary arteries. History of previous myocardial infarction (MI) History of coronary revascularization, i.e., percutaneous coronary intervention (PCI) or coronary artery bypass graft (CABG), not including the elective PCI during the index hospitalization Documented history of type 2 diabetes mellitus. Post-procedural residual diameter stenosis of the treated lesions < 20% in patients with stent implantation or < 50% in those with balloon angioplasty Post-procedural thrombolysis in myocardial infarction (TIMI) grade 3 flow in treated vessels Negative cardiac troponin test before the index elective PCI. Taking Clopidogrel 75 mg daily dose for at least 7 days or taking Clopidogrel 75 mg daily dose for less than 7 days but with 300 to 600 mg Clopidogrel loading dose before PCI. Taking acetylsalicylic acid (ASA) 100 mg daily treatment for at least 7 days or taking ASA 100 mg daily dose for less than 7 days but with 300 mg ASA loading dose before PCI. have a negative urine or blood pregnancy test at enrolment and prior to randomization; currently be using a hormonal contraceptive and agree to continue its use in addition to using double-barrier local contraception (i.e., intra-uterine device plus spermicidal and condom for male partner) from screening through study completion.", "candidate_expression": "((100 mg) AND (18 years or older) AND (3) AND (300 mg) AND (300 to 600 mg) AND (75 mg) AND (< 20%) AND (< 50%) AND (= 50%) AND (ASA) AND (Aged) AND (CABG) AND (CAD) AND (Clopidogrel) AND (MI) AND (Negative) AND (PCI) AND (Post-procedural residual diameter stenosis) AND (Post-procedural thrombolysis) AND (Provision of written informed consent (by patient or appropriate designee according to local regulations) prior to any study specific procedures) AND (TIMI) AND (acetylsalicylic acid) AND (angiographic evidence) AND (balloon angioplasty) AND (before PCI) AND (before the index elective PCI.) AND (cardiac troponin test) AND (coronary revascularization) AND (currently be using a hormonal contraceptive and agree to continue its use in addition to using double-barrier local contraception (i.e., intra-uterine device plus spermicidal and condom for male partner) from screening through study completion) AND (daily) AND (diameter stenosis) AND (during the index hospitalization) AND (elective) AND (for at least 7 days) AND (for less than 7 days) AND (have a negative urine or blood pregnancy test at enrolment and prior to randomization;) AND (index elective PCI) AND (index hospitalization) AND (major coronary arteries) AND (myocardial infarction) AND (myocardial infarction grade) AND (not) AND (stable angina pectoris) AND (stent implantation) AND (treated) AND (treated vessels) AND (type 2 diabetes mellitus) AND ((left anterior descending coronary arteries) OR (left circumflex coronary arteries) OR (left main coronary arteries) OR (right coronary arteries)) AND ((coronary artery bypass graft) OR (percutaneous coronary intervention)) AND ((lesions)) AND ((female) OR (male)))"}
{"candidate_id": "LLM03885", "doc_id": "NCT01891513_inc", "case_bucket": "or", "source_criterion": "Age 65 years and older Hypertension - untreated (Systolic Blood Pressure (SBP) ≥ 140 mm Hg or Diastolic Blood Pressure (DBP) ≥ 90 mm Hg) or treated Physical limitations evidenced by either: Score ≤ 10 on the Short Physical Performance Battery OR Walking speed < 1.2 m/sec during 400 m usual-paced test Sedentary lifestyle, defined as <150 min/wk of moderate physical activity as assessed by CHAMPS questionnaire Willingness to participate in all study procedures", "candidate_expression": "((400 m usual-paced test) AND (Age 65 years and older) AND (CHAMPS questionnaire) AND (Hypertension untreated) AND (treated) AND ((Short Physical Performance Battery Score ≤ 10) OR (Walking speed < 1.2 m/sec)) AND ((Sedentary lifestyle) OR (moderate physical activity <150 min/wk)) AND ((Diastolic Blood Pressure (DBP) ≥ 90 mm Hg) OR (Systolic Blood Pressure (SBP) ≥ 140 mm Hg)))"}
{"candidate_id": "LLM03886", "doc_id": "NCT02416869_inc", "case_bucket": "other", "source_criterion": "Healthy patients (ASA I) Bilateral symmetrically impacted lower third molars according to Pel-Gregory's and Winter's classification", "candidate_expression": "((ASA I) AND (Healthy patients) AND (Pel-Gregory's and Winter's classification Bilateral symmetrically impacted lower third molars))"}
{"candidate_id": "LLM03887", "doc_id": "NCT03256864_exc", "case_bucket": "or", "source_criterion": "Patients who are recipients of multiple solid organ or islet cell tissue transplants, or have previously received an organ or tissue transplant. Patients who have a combined liver-kidney transplant. History of malignancy of any organ system (other than localized basal cell carcinoma of the skin), treated or untreated, within the past 5 years, regardless of whether there is evidence of local recurrence or metastases. Existence of any surgical, medical or mental conditions, other than the current transplantation, which, in the opinion of the investigator, might interfere with the objectives of the study. Pregnant or nursing (lactating) women.", "candidate_expression": "((Pregnant) AND (combined liver-kidney transplant) AND (lactating) AND (malignancy History any organ system within the past 5 years) AND (nursing) AND (women) AND NOT (localized basal cell carcinoma of the skin) AND NOT (transplantation current) AND ((treated) OR (untreated)) AND ((medical conditions) OR (mental conditions) OR (surgical conditions)) AND ((islet cell tissue transplants) OR (solid organ transplants)) AND ((organ transplant) OR (tissue transplant)))"}
{"candidate_id": "LLM03888", "doc_id": "NCT03475589_exc", "case_bucket": "or", "source_criterion": "Confirmed allergy to apatinin and or its excipients; Hypertension (high blood pressure) that can not be controlled by drugs; A history of active hemorragge, ulcer, intestinal perforation, intestinal obstruction, or major surgery no older than 30 days; NYHA III-IV heart function, or severe hepatic or renal insufficiency (Grade 4); Presence of multiple factors that affect oral medications, such as difficulty swallowing, nausea, vomiting, chronic diarrhea and intestinal obstruction; Pregnant or lactating women, or women of child-bearing potential who have planned a pregnancy, or male and female patients who do not agree to practice adequate contraception during this study; Patients who have a history of psychotropics abuse and can not quit, or who have mental disorders; Participation in other drug clinical trial within the last 4 weeks; Prior therapy with VEGFR inhibitors such as sorafenib and sunitinib; Presence of comorbidities that seriously affect the patient's safety or ability to complete the study, in the investigator's judgment; Patients who can not tolerate apatinib treatment as judged by the investigator depending on the their medical history; Patients that are considered ineligible for this study by the investigator.", "candidate_expression": "((Grade 4) AND (Hypertension) AND (III-IV) AND (NYHA) AND (Participation in other drug clinical trial within the last 4 weeks;) AND (Pregnant or lactating women, or women of child-bearing potential who have planned a pregnancy, or male and female patients who do not agree to practice adequate contraception during this study;) AND (VEGFR inhibitors) AND (abuse) AND (active) AND (allergy) AND (apatinib) AND (apatinin) AND (chronic diarrhea) AND (controlled by drugs) AND (difficulty swallowing) AND (drugs) AND (excipients) AND (factors that affect oral medications) AND (heart function) AND (hemorragge) AND (hepatic insufficiency) AND (high blood pressure) AND (history) AND (intestinal obstruction) AND (intestinal perforation) AND (major surgery) AND (mental disorders) AND (nausea) AND (no older than 30 days) AND (not) AND (psychotropics) AND (renal insufficiency) AND (severe) AND (sorafenib) AND (sunitinib) AND (tolerate) AND (ulcer) AND (vomiting))"}
{"candidate_id": "LLM03889", "doc_id": "NCT02790593_exc", "case_bucket": "or", "source_criterion": "Age less than 18 years Significant arterial disease (Ankle Brachial Pressure Index <0•9 or evidence on Arterial Duplex) Acute Deep Vein Thrombosis Patient unable or unwilling to have high compression (30mmHg minimum) Patients with dexterity insufficiency of hands Patients with peripheral neuropathy Leg ulcers of another underlying cause Leg ulcers of greater than 1 year duration Patients unable or unwilling to provide written, informed consent", "candidate_expression": "((<0•9) AND (Acute Deep Vein Thrombosis) AND (Age) AND (Ankle Brachial Pressure Index) AND (Arterial Duplex) AND (Leg ulcers) AND (Patient unable or unwilling to have high compression (30mmHg minimum)) AND (Patients unable or unwilling to provide written, informed consent) AND (Significant) AND (another) AND (arterial disease) AND (dexterity insufficiency of hands) AND (greater than 1 year duration) AND (less than 18 year) AND (peripheral neuropathy) AND (underlying cause))"}
{"candidate_id": "LLM03890", "doc_id": "NCT02851888_inc", "case_bucket": "scope", "source_criterion": "Scheduled for arthroscopic labral repair with or without osteoplasty of the hip. 18 to 50 years old American Society of Anesthesiologists Physical Status (ASA PS) score of I or II.", "candidate_expression": "((18 to 50 years) AND (ASA PS) AND (American Society of Anesthesiologists Physical Status score) AND (I or II) AND (Scheduled) AND (arthroscopic labral repair) AND (hip) AND (old) AND (osteoplasty))"}
{"candidate_id": "LLM03891", "doc_id": "NCT02270970_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03892", "doc_id": "NCT00806273_exc", "case_bucket": "other", "source_criterion": "ASA 3+ No current treatment plan at OHSU Severely carious teeth resulting in inability to isolate for procedure Unable to understand or sign consent form", "candidate_expression": "((ASA 3+) AND (OHSU) AND (Unable to understand or sign consent form) AND (carious teeth Severely) AND (inability to isolate for procedure) AND NOT (treatment plan current))"}
{"candidate_id": "LLM03893", "doc_id": "NCT00962364_exc", "case_bucket": "other", "source_criterion": "none, all patients meeting the inclusion criteria will be eligible.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03894", "doc_id": "NCT02053246_inc", "case_bucket": "other", "source_criterion": "Adults (= 18 years of age) with World Health Organization Group 2 Pulmonary Hypertension (Mean pulmonary artery pressure = 25 mmHg and pulmonary capillary wedge pressure = 15 mmHg) New York Heart Association class II-IV symptoms Left ventricular ejection fraction (LVEF) = 45%", "candidate_expression": "(((Mean pulmonary artery pressure) AND (= 15 mmHg) AND (= 18 years) AND (= 25 mmHg) AND (= 45%) AND (Adults) AND (Left ventricular ejection fraction (LVEF)) AND (New York Heart Association) AND (Pulmonary Hypertension) AND (World Health Organization Group 2) AND (age) AND (class II-IV) AND (pulmonary capillary wedge pressure) AND (symptoms))"}
{"candidate_id": "LLM03895", "doc_id": "NCT02282319_inc", "case_bucket": "other", "source_criterion": "ASA (American Society of Anesthesiologists) class 1 & 2, undergoing day-case knee arthroscopy", "candidate_expression": "((ASA) AND (class 1 & 2) AND (knee arthroscopy))"}
{"candidate_id": "LLM03896", "doc_id": "NCT00728156_inc", "case_bucket": "or", "source_criterion": "Patients with T2DM and CAS as defined below: Clinical definitions T2DM: Diagnosed according to the WHO criteria [53]. CAD:Presence of any one of the following: Angina plus positive exercise tolerance test, enzyme and/or Q wave positive myocardial infarction, angiographic evidence ( >50% stenosis of one vessel), percutaneous or surgical coronary revascularisation. Aged between 18 and 75 Provided written consent for participation in the trial prior to any study-specific procedures or requirements.", "candidate_expression": "((Aged between 18 and 75) AND (Angina) AND (CAD) AND (CAS) AND (T2DM) AND (T2DM WHO criteria) AND (angiographic evidence) AND (coronary revascularisation) AND (exercise tolerance test positive enzyme positive Q wave positive) AND (myocardial infarction) AND (stenosis of one vessel >50% percutaneous surgical) AND (written consent for participation in the trial prior to any study-specific procedures or requirements))"}
{"candidate_id": "LLM03897", "doc_id": "NCT02595190_inc", "case_bucket": "or", "source_criterion": "1. Diagnosed with symptomatic sacral perineurial cysts(e.g., lumbosacral or perineal pain, fecal or urinary functions change, sexual function change, lower limb radiation pain, muscle abate, paresthesia, etc) 2. Visual analog scale more than or equal to 4 3. Signed the informed consent 4. Years, range 18-60 5. Self-rating anxiety scale (SAS) and self-rating depression scale (SDS) scores < 50 6. No Congenital,Mental and other Nervous system diseases 7. No Serious Cardiac,Pulmonary,Hepatic and Nephritic disease 8. No history of drug allergy 9. No pain(including dysmenorrhea) or drug use (e.g., antipyretics,sleeping pills) within the last month 10. MRI finding of sacral perineurial cysts, but without any clinical symptoms, included in the negative control group 11. MRI finding healthy volunteers don't have sacral perineurial cysts, included in the negative control groupblank control group", "candidate_expression": "((18-60) AND (Cardiac,Pulmonary,Hepatic) AND (Congenital diseases) AND (MRI finding healthy volunteers don't have sacral perineurial cysts, included in the negative control groupblank control group) AND (Mental disease) AND (Nervous system diseases) AND (No) AND (SAS) AND (SDS) AND (Self-rating anxiety scale) AND (Signed the informed consent) AND (Visual analog scale) AND (Years) AND (allergy) AND (drug) AND (dysmenorrhea) AND (last month) AND (more than or equal to 4) AND (sacral perineurial cysts() AND (scores < 50) AND (self-rating depression scale) AND (symptomatic) AND ((Cardiac) OR (Hepatic) OR (Nephritic disease) OR (Pulmonary)) AND ((drug) OR (pain)) AND ((functions change, fecal) OR (lower limb radiation pain) OR (lumbosacral pain) OR (muscle abate) OR (paresthesia) OR (perineal pain) OR (sexual function change) OR (urinary functions change)))"}
{"candidate_id": "LLM03898", "doc_id": "NCT02552459_exc", "case_bucket": "or", "source_criterion": "long-term use of analgesics,sedatives or non steroidal anti-inflammatory drugs history. known for dexmedetomidine or other drugs allergy in this study. cannot communicate. preoperative systolic blood pressure <90 mmHg, or the heart rate <50/min.", "candidate_expression": "((allergy) AND (cannot communicate) AND (non steroidal anti-inflammatory drugs history) AND ((heart rate <50/min) OR (preoperative systolic blood pressure <90 mmHg)) AND ((analgesics) OR (sedatives)) AND ((dexmedetomidine) OR (drugs other)))"}
{"candidate_id": "LLM03899", "doc_id": "NCT03323047_exc", "case_bucket": "or", "source_criterion": "Patients Level III or greater on the American Society of Anesthesiologists (ASA) physical status classification system (as determined by the anesthesiologist) Patients with chronic conditions that would limit our ability to develop the study according to objectives, such as neurodevelopmental conditions preventing patients from understanding the Oucher tool Hepatic or renal disease cardiac disease active infection diabetes mellitus sickle cell disease known coagulation disorders pre- operative treatment with anti-emetics, steroids, or analgesics Acetaminophen allergy or already receiving acetaminophen within 24 h of surgery Complicating health factors precluding the use of opioids or acetaminophen any other factors which would interfere with pain assessment and management Patients weighing more than 30 kg that would exceed maximum dexamethasone dose Patients who live without a home telephone patient living without parental supervision.", "candidate_expression": "((Acetaminophen) AND (American Society of Anesthesiologists (ASA) physical status Level III or greater) AND (Complicating health factors) AND (Hepatic disease) AND (acetaminophen) AND (acetaminophen within 24 h of surgery) AND (allergy) AND (analgesics) AND (anti-emetics) AND (cardiac disease) AND (chronic conditions limit our ability to develop the study according to objectives) AND (coagulation disorders) AND (diabetes mellitus) AND (infection active) AND (interfere) AND (management) AND (neurodevelopmental conditions) AND (opioids) AND (other factors) AND (pain assessment) AND (precluding) AND (preventing understanding the Oucher tool) AND (renal disease) AND (sickle cell disease) AND (steroids) AND (treatment pre- operative) AND (weighing more than 30 kg))"}
{"candidate_id": "LLM03900", "doc_id": "NCT02573168_inc", "case_bucket": "or", "source_criterion": "18 years of age or older; Suffer from schizophrenia/schizoaffective disorder meeting Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, Text Revision (DSM-IV-TR) criteria; Have a total baseline score on the Brief Psychiatric Rating Scale (BPRS) = 45; Be capable and willing to provide written informed consent to participate in this study; Agree to abide by the study protocol and its restrictions and be able to complete all aspects of the study, including all visits and tests", "candidate_expression": "((Agree to abide by the study protocol and its restrictions and be able to complete all aspects of the study, including all visits and tests) AND (BPRS) AND (Be capable and willing to provide written informed consent to participate in this study) AND (Brief Psychiatric Rating Scale = 45) AND (DSM-IV-TR) AND (Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, Text Revision) AND (age 18 years or older) AND (schizoaffective disorder) AND (schizophrenia))"}
```
