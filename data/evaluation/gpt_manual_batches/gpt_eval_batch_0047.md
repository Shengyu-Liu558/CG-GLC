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
{"candidate_id": "LLM01151", "doc_id": "NCT03338296_inc", "case_bucket": "or", "source_criterion": "Healthy male or female adolescents, age 12 to 17 years (inclusive) at Screening, with a body mass index (BMI) that is greater than or equal to the United States-weighted mean of the 95th percentile based on age and sex with a body weight greater than 60 kilograms (kg). Participants with Type 2 diabetes mellitus (T2DM) may have a pre-existing or new diagnosis of T2DM. HbA1c =6.5% fasting plasma glucose (FPG) =126 mg/dL (7.0 mmol/L) Participants and their families not planning to move away from the area for the duration of the study Participants able and willing to comply with all aspects of the study, including a standardized, reduced calorie diet and an age appropriate, increased physical activity program Participants considered in stable health in the opinion of the investigator Able and willing to support and supervise study participation in the opinion of the investigator, including consideration of any existing physical, medical, or mental condition that prevents compliance with the protocol Able and willing to personally comply with and execute all aspects of the study requirements for the caregivers or guardians", "candidate_expression": "((12 to 17 years) AND (7.0 mmol/L) AND (=126 mg/dL) AND (=6.5%) AND (Able to personally comply) AND (HbA1c) AND (Healthy) AND (able to comply) AND (adolescents) AND (age) AND (age appropriate) AND (at Screening) AND (based on age) AND (based on sex) AND (body mass index (BMI)) AND (body weight) AND (caregivers) AND (fasting plasma glucose (FPG)) AND (female) AND (for the duration of the study) AND (greater than 60 kilograms (kg)) AND (greater than or equal to the 95th percentile) AND (greater than or equal to the United States-weighted mean of the 95th percentile) AND (guardians) AND (increased physical activity program) AND (male) AND (not) AND (planning to move away) AND (reduced calorie diet) AND (stable health) AND (standardized) AND (the study) AND (willing to comply) AND (willing to personally comply))"}
{"candidate_id": "LLM01152", "doc_id": "NCT01581749_inc", "case_bucket": "or", "source_criterion": "histologically proven prostate adenocarcinoma within 1 year of enrollment Low risk: Gleason <or=6 & PSA <or=10 & Clinical Stage T1b-T2a,Nx or N0, Mx or M0 Intermediate risk:Gleason <or=6 & PSA<or=10 & Clinical Stage T2b OR Gleason=7 & PSA<or=10 & Clinical Stage T1b-T2b OR Gleason <or=6 & PSA > 10 & < or =20 & Clinical Stage T1b- T2b, Nx or NO, Mx or M0 ECOG Performance Status 0-1 No prior prostate radiation or other definitive therapy", "candidate_expression": "((0-1) AND (<or=10) AND (<or=6) AND (=7) AND (> 10 & < or =20) AND (Clinical Stage) AND (ECOG Performance Status) AND (Gleason) AND (Intermediate risk) AND (Low risk) AND (M0) AND (Mx) AND (N0) AND (NO) AND (No) AND (Nx) AND (PSA) AND (T1b- T2b) AND (T1b-T2a) AND (T1b-T2b) AND (T2b) AND (definitive therapy) AND (enrollment) AND (histologically proven) AND (prostate adenocarcinoma) AND (prostate radiation) AND (within 1 year of enrollment))"}
{"candidate_id": "LLM01153", "doc_id": "NCT01866800_exc", "case_bucket": "or", "source_criterion": "History of acute coronary syndrome in the past 30 days. History of congesting heart failure with left ventricular ejection fraction <30% or exacerbation in the past 30 days. Current dialysis treatment. Known furosemide hypersensitivity. Contraindications to placement of a Foley catheter in the bladder.", "candidate_expression": "((<30%) AND (Contraindications) AND (Current) AND (acute coronary syndrome) AND (bladder) AND (congesting heart failure) AND (dialysis treatment) AND (exacerbation) AND (furosemide) AND (hypersensitivity) AND (in the past 30 days) AND (left ventricular ejection fraction) AND (placement of a Foley catheter))"}
{"candidate_id": "LLM01154", "doc_id": "NCT01959425_exc", "case_bucket": "or", "source_criterion": "OAT required for reasons not related to AF (i.e., prosthetic valve, PV stenosis, previous pulmonary embolism, presence of spontaneous echo contrast [SEC] at standard echo performed at 3-months follow-up). Any cardiac surgery within the past 60 days (2 months) or valvular cardiac surgical procedure at any time (i.e., ventriculotomy, atriotomy, and valve repair or replacement and presence of a prosthetic valve) Previous myocardial infarction (MI) or a percutaneous coronary intervention PCI within the past 3 months Awaiting cardiac transplantation or other cardiac surgery within the next 365 days (12 months) Documented left atrial thrombus Significant pulmonary disease, (e.g., restrictive pulmonary disease, constrictive or COPD) or any other disease or malfunction of the lungs or respiratory system that produces chronic symptoms Significant medical problem that in the opinion of the investigator would preclude enrollment in this study Women who are pregnant (as evidenced by pregnancy test if pre-menopausal) Acute illness or active systemic infection or sepsis Unstable angina Contraindication to anticoagulation (i.e., heparin, warfarin or another commercially available anticoagulation medication) History of blood clotting or bleeding abnormalities Life expectancy less than 360 days (12 months) Uncontrolled Heart Failure or NYHA Class III or IV heart failure Enrollment in a clinical study evaluating another device or drug, within the past 6 months Unable or unwilling to comply with protocol requirements", "candidate_expression": "((2 months) AND (Contraindication) AND (Enrollment in a clinical study evaluating another device or drug, within the past 6 months) AND (Life expectancy less than 360 days less than 12 months) AND (MI) AND (OAT AF) AND (PCI within the past 3 months) AND (SEC) AND (Unable or unwilling to comply with protocol requirements) AND (Unstable angina) AND (Women who are pregnant (as evidenced by pregnancy test if pre-menopausal)) AND (anticoagulation) AND (left atrial thrombus within 12 months) AND (pulmonary disease Significant) AND ((cardiac surgery within the past 60 days) OR (valvular cardiac surgical)) AND ((atriotomy) OR (prosthetic valve)) OR (valve repair) OR (valve replacement) OR (ventriculotomy)) AND ((myocardial infarction) OR (percutaneous coronary intervention)) AND ((cardiac surgery) OR (cardiac transplantation)) AND ((COPD) OR (restrictive pulmonary disease)) AND ((sepsis) OR (systemic infection)) AND ((PV stenosis) OR (prosthetic valve) OR (pulmonary embolism) OR (standard echo spontaneous echo contrast 3-months follow-up)) AND ((heparin) OR (warfarin)) AND ((bleeding abnormalities) OR (blood clotting abnormalities)) AND ((Heart Failure Uncontrolled) OR (heart failure)) AND ((NYHA Class III) OR (NYHA Class IV)))"}
{"candidate_id": "LLM01155", "doc_id": "NCT02627521_exc", "case_bucket": "or", "source_criterion": "Anticoagulation therapy Prior CABG. Active bleeding or at high risk of bleeding Severe liver or renal disease. Hypersensitivity to ticagrelor History of intracranial hemorrhage", "candidate_expression": "((Active) AND (Anticoagulation therapy) AND (CABG) AND (History) AND (Hypersensitivity) AND (Prior) AND (Severe) AND (at high risk) AND (bleeding) AND (disease liver) AND (intracranial hemorrhage) AND (renal disease) AND (ticagrelor))"}
{"candidate_id": "LLM01156", "doc_id": "NCT02746900_inc", "case_bucket": "other", "source_criterion": "18-50 ages Singleton pregnancy Cervical length <=25mm between 18(0) and 23(6) weeks", "candidate_expression": "((Cervical length <=25mm between 18(0) and 23(6) weeks) AND (Singleton pregnancy) AND (ages 18-50))"}
{"candidate_id": "LLM01157", "doc_id": "NCT03624517_inc", "case_bucket": "or", "source_criterion": "Adult males and females who are 18 years of age or older. Evidence or suspicion of upper gastrointestinal bleed (GIB) Patient with known or suspected cirrhosis Upper GIB secondary to bleeding esophageal varices as show by esophageal endoscopy, requiring endoscopic band ligation (EBL) at presentation Willing and able to provide informed consent for study, or have a Legally authorized representative (LAR) provide consent if the patient is unable to do so", "candidate_expression": "((18 years of age or older) AND (Adult) AND (Upper GIB) AND (Willing and able to provide informed consent for study, or have a Legally authorized representative (LAR) provide consent if the patient is unable to do so) AND (at presentation) AND (bleeding) AND (cirrhosis) AND (endoscopic band ligation (EBL)) AND (esophageal endoscopy) AND (esophageal varices) AND (requiring) AND (secondary) AND (upper gastrointestinal bleed (GIB)) AND ((known) OR (suspected)) AND ((females) OR (males)) AND ((Evidence) OR (suspicion)))"}
{"candidate_id": "LLM01158", "doc_id": "NCT02842424_inc", "case_bucket": "or", "source_criterion": "A positive history of chronic claudication, Exercise-limiting claudication established by history and direct observation during a screening walking test administered by the evaluating vascular surgeon, Arterial occlusive disease per ankle Brachial index measurements and/or other imaging modalities, Stable blood pressure regimen, stable lipid regimen, stable diabetes regimen and risk factor control for 6 weeks.", "candidate_expression": "((Arterial occlusive disease) AND (Exercise-limiting claudication) AND (ankle Brachial index measurements) AND (blood pressure regimen Stable) AND (chronic claudication positive history) AND (diabetes regimen stable) AND (direct observation) AND (history) AND (imaging modalities) AND (lipid regimen stable) AND (risk factor control) AND (screening walking test))"}
{"candidate_id": "LLM01159", "doc_id": "NCT02105090_exc", "case_bucket": "or", "source_criterion": "amide and/or esther local anaesthetic allergy paraben allergy Child-Pugh grade B/C liver failure renal insufficiency (calculated glomerular filtration rate under 60 ml/min/1.73 m2 according to Cockcroft-Gault scale ) dementia those presenting with swallowing problem chronic pain condition chronic use of pain medication pregnancy lactation", "candidate_expression": "((Child-Pugh grade) AND (allergy) AND (calculated glomerular filtration rate under 60 ml/min/1.73 m2 Cockcroft-Gault scale) AND (chronic pain condition) AND (dementia) AND (lactation) AND (liver failure) AND (pain medication chronic use) AND (paraben) AND (pregnancy) AND (renal insufficiency) AND (swallowing problem) AND ((amide local anaesthetic) OR (esther local anaesthetic)) AND ((B) OR (C)))"}
{"candidate_id": "LLM01160", "doc_id": "NCT00122070_inc", "case_bucket": "other", "source_criterion": "Provide written informed consent before beginning any study related activities Be between age 18 and 55 years Be able to speak, read and write English and follow simple instructions for completing self-rated scales Meet DSM-IV criteria for BPD as assessed by the Structured Clinical Interview for DSM-IV Personality Disorders (SCID-II).", "candidate_expression": "((BPD Meet DSM-IV criteria) AND (Structured Clinical Interview for DSM-IV Personality Disorders (SCID-II)) AND (able to follow simple instructions) AND (able to speak, read and write English) AND (age between 18 and 55 years) AND (written informed consent before beginning any study related activities))"}
{"candidate_id": "LLM01161", "doc_id": "NCT02760251_exc", "case_bucket": "or", "source_criterion": "Adults older than 45 and children younger than 18 years Platelet count higher than 30x109/l at time of screening Suspicion of secondary ITP Positive family history for ITP Presence or history of autoimmune disease as judged by the investigator Hepatosplenomegaly Presence or history of relevant hepatic disease as judged by the investigator Presence or history of thromboembolic disease as judged by the investigator Patients with splenectomy Women who are pregnant or breast feeding Intention to become pregnant during the course of the study Lack of safe double contraception (see 7.1) Any vaccination 2 weeks prior start of the study Drugs with a known impact on the immune system or on platelet function must be recorded and an exclusion of the study should be discussed with the study center Known or suspected non-compliance, drug or alcohol abuse Inability to follow the procedures of the study, e.g. due to language problems, psychological disorders, dementia of the study subject Participation in another study with investigational drug within the 30 days preceding and during the present study Previous enrolment into the current study Previous treatment with romiplostim or eltrombopag Hypersensitivity to the active substance or to any of the excipients or to E. coli derived proteins Enrolment of the investigator, his/her family members, employees and other dependent persons", "candidate_expression": "((2 weeks prior start of the study) AND (Adults) AND (Drugs with a known impact on the immune system or on platelet function must be recorded and an exclusion of the study should be discussed with the study center) AND (Hepatosplenomegaly) AND (Hypersensitivity) AND (Inability to follow the procedures of the study, e.g. due to language problems, psychological disorders, dementia of the study subject) AND (Intention to become pregnant during the course of the study) AND (Lack of safe double contraception (see 7.1)) AND (Platelet count) AND (Women who are pregnant or breast feeding) AND (as judged by the investigator) AND (at time of screening) AND (autoimmune disease) AND (children) AND (family history for ITP) AND (hepatic disease) AND (higher than 30x109/l) AND (non-compliance) AND (older than 45) AND (relevant) AND (screening) AND (secondary ITP) AND (splenectomy) AND (start of the study) AND (thromboembolic disease) AND (vaccination) AND (younger than 18 years) AND ((alcohol abuse) OR (drug abuse)) AND ((eltrombopag) OR (romiplostim)))"}
{"candidate_id": "LLM01162", "doc_id": "NCT02466113_inc", "case_bucket": "other", "source_criterion": "The informed consent has been obtained from the patient. With confirmed diagnosis of stage II colon cancer. With moderate/good ECOG health rating (PS): 0-1 score. The patient receive no anti-cancer treatment before primary surgery. The patient receive radical operation for colon cancer with negative margin.", "candidate_expression": "((ECOG health rating (PS) moderate/good 0-1 score) AND (The informed consent has been obtained from the patient.) AND (colon cancer) AND (colon cancer stage II) AND (primary surgery) AND (radical operation negative margin) AND NOT (anti-cancer treatment before primary surgery))"}
{"candidate_id": "LLM01163", "doc_id": "NCT02748330_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01164", "doc_id": "NCT02992028_inc", "case_bucket": "other", "source_criterion": "Rotator cuff tear patients undergoing arthroscopic rotator cuff tear", "candidate_expression": "((Rotator cuff tear) AND (arthroscopic rotator cuff tear))"}
{"candidate_id": "LLM01165", "doc_id": "NCT02760459_inc", "case_bucket": "other", "source_criterion": "Age > 40 years (45) Primary knee osteoarthritis diagnosed using the American College of Rheumatology criteria (46) Undergoing elective, primary and unilateral total knee arthroplasty American Society of Anesthesiology (ASA) physical status class 1-3 BMI < 40 kg/m2", "candidate_expression": "((1-3) AND (< 40 kg/m2) AND (> 40 years) AND (ASA) AND (Age) AND (American College of Rheumatology criteria) AND (American Society of Anesthesiology physical status class) AND (BMI) AND (Primary knee osteoarthritis) AND (elective) AND (primary) AND (total knee arthroplasty) AND (unilateral))"}
{"candidate_id": "LLM01166", "doc_id": "NCT02667730_inc", "case_bucket": "or", "source_criterion": "Acquired acute ankle injury (injured less than 48 hours ago); Clinical diagnosis of a Grade I or II ankle sprain Is eligible to receive comprehensive medical care from Garrison Petawawa", "candidate_expression": "((acute ankle injury Acquired less than 48 hours ago) AND (ankle sprain Grade I Grade II))"}
{"candidate_id": "LLM01167", "doc_id": "NCT02961582_exc", "case_bucket": "or", "source_criterion": "Obstructed outlet syndrome (objectified by defeacography) Irritable bowel syndrome (Rome-IV criteria for irritable bowel syndrome) Congenital or organic bowel pathology Rectal prolapse Anatomical limitations preventing placement of an electrode Skin and perineal disease with risk of infection Previous large bowel/rectal surgery Stoma Coexisting neurological disease Significant psychological co-morbidity as assessed subjectively by the investigator Being or attempting to become pregnant during study follow-up", "candidate_expression": "((Anatomical limitations) AND (Being or attempting to become pregnant during study follow-up) AND (Congenital bowel pathology) AND (Irritable bowel syndrome) AND (Obstructed outlet syndrome) AND (Rectal prolapse) AND (Rome-IV criteria) AND (Significant) AND (Skin disease) AND (Stoma) AND (as assessed subjectively by the investigator) AND (defeacography) AND (irritable bowel syndrome) AND (large bowel surgery) AND (neurological disease) AND (organic bowel pathology) AND (perineal disease) AND (placement of an electrode) AND (preventing) AND (psychological co-morbidity) AND (rectal surgery) AND (risk of infection))"}
{"candidate_id": "LLM01168", "doc_id": "NCT01856491_inc", "case_bucket": "or", "source_criterion": "Willing and capable of providing informed consent Has an indication for implantation of a single or dual chamber ICD or CRT-D system in their respective geography Subjects planned to be implanted with the RELIANCE 4-FRONT Passive Fixation Lead Willing and capable of participating in all testing/ visits associated with this clinical study at an approved clinical study center and at the intervals defined by this protocol Age 18 or above, or of legal age to give informed consent specific to state and national law", "candidate_expression": "((Age) AND (RELIANCE 4-FRONT Passive Fixation Lead) AND (Willing and capable of providing informed consent) AND (implanted with the RELIANCE 4-FRONT Passive Fixation Lead) AND (planned) AND ((18 or above) OR (of legal age)) AND ((CRT-D system implantation of a) OR (chamber ICD implantation of a single) OR (dual chamber ICD implantation of a)))"}
{"candidate_id": "LLM01169", "doc_id": "NCT02842424_exc", "case_bucket": "or", "source_criterion": "Rest pain or tissue loss due to PAD (Fontaine stage III and IV), acute lower extremity ischemic event secondary to thromboembolic disease or acute trauma, Walking capacity significantly limited by conditions other than claudication including leg (joint/musculoskeletal, neurologic) and systemic (heart, lung disease) pathology, Current use of either ACE inhibitors or angiotensin II receptor blockers, Chronic kidney disease with estimated Glomerular Filtration Rate < 30 ml/min/1.73 m2, History of bilateral severe renal artery stenosis and 7) History of angioedema related to previous ACE-inhibitor treatment or known hypersensitivity to ramipril or other ACE inhibitors.", "candidate_expression": "((< 30 ml/min/1.73 m2) AND (ACE-inhibitor) AND (Chronic kidney disease) AND (Current use) AND (Fontaine stage) AND (History) AND (PAD) AND (Walking capacity) AND (acute) AND (acute trauma) AND (bilateral) AND (claudication) AND (conditions other than claudication) AND (estimated Glomerular Filtration Rate) AND (ischemic event) AND (known) AND (lower extremity) AND (other than) AND (other than claudication) AND (previous) AND (severe) AND (significantly limited) AND (thromboembolic disease) AND ((Rest pain) OR (tissue loss)) AND ((secondary to acute trauma) OR (secondary to thromboembolic disease)) AND ((leg pathology) OR (systemic pathology)) AND ((joint) OR (musculoskeletal) OR (neurologic)) AND ((heart disease) OR (lung disease)) AND ((ACE inhibitors) OR (angiotensin II receptor blockers)) AND ((angioedema) OR (renal artery stenosis)) AND ((ACE-inhibitor treatment) OR (hypersensitivity)) AND ((III) OR (IV)) AND ((ACE inhibitors) OR (ramipril)))"}
{"candidate_id": "LLM01170", "doc_id": "NCT02529475_inc", "case_bucket": "other", "source_criterion": "Major subjects of over 40 years (mean age of Meniere's disease 40 to 50 years) Informed consent signed Medical examination performed prior to participation in research Patients without history of inner ear disease Recipient of a French social security scheme", "candidate_expression": "((Medical examination prior to participation in research) AND (years over 40 years) AND NOT (inner ear disease history))"}
{"candidate_id": "LLM01171", "doc_id": "NCT00904202_exc", "case_bucket": "or", "source_criterion": "1. Had a neurological condition other than that associated with their pain diagnosis which, in the opinion of the investigator, would interfere with their ability to participate in the study 2. Were taking a lidocaine-containing product that could not be discontinued while receiving lidocaine 3. Were taking class 1 anti-arrhythmic drugs (e.g., mexiletine, tocainide)", "candidate_expression": "((associated with their pain diagnosis) AND (class 1 anti-arrhythmic drugs) AND (could not be discontinued) AND (lidocaine) AND (lidocaine-containing product) AND (neurological condition) AND (other than) AND (pain diagnosis) AND (receiving lidocaine) AND (while receiving lidocaine) AND ((mexiletine) OR (tocainide)))"}
{"candidate_id": "LLM01172", "doc_id": "NCT00965900_inc", "case_bucket": "or", "source_criterion": "Liver cirrhosis Age between 18 and 70 years Esophageal varices with high bleeding risk: more than F2 and red color sign No previous history of upper gastrointestinal bleeding No previous history of endoscopic, radiologic, or surgical therapy for varices or ascites Do not take beta-blocker, ACE inhibitor, or nitrate Child-Pugh score <12", "candidate_expression": "((ACE inhibitor) AND (Age between 18 and 70 years) AND (Child-Pugh score <12) AND (Esophageal varices high bleeding risk) AND (F2 more than) AND (Liver cirrhosis) AND (ascites) AND (beta-blocker) AND (endoscopic therapy) AND (nitrate) AND (radiologic therapy) AND (red color sign) AND (surgical therapy) AND (varices) AND NOT (upper gastrointestinal bleeding))"}
{"candidate_id": "LLM01173", "doc_id": "NCT01768195_exc", "case_bucket": "or", "source_criterion": "younger than 18 years old HBsAg negative at baseline pregnant or lactating women", "candidate_expression": "((HBsAg negative) AND (at baseline) AND (lactating) AND (old) AND (pregnant) AND (women) AND (younger than 18 years))"}
{"candidate_id": "LLM01174", "doc_id": "NCT02455921_exc", "case_bucket": "other", "source_criterion": "Parents refusal Cognitive impairment Difficulty in communication due to language issues Psychiatric disorder Severe systematic disorder Known allergy to any drug used", "candidate_expression": "((Cognitive impairment) AND (Difficulty in communication) AND (Known allergy) AND (Parents refusal) AND (Psychiatric disorder) AND (Severe systematic disorder) AND (any drug used) AND (language issues))"}
{"candidate_id": "LLM01175", "doc_id": "NCT03252249_inc", "case_bucket": "other", "source_criterion": "Aged =18 years Clinical diagnosis of acute coronary syndrome In the opinion of the attending clinician requires dual anti-platelet therapy with aspirin and a P2Y12 receptor antagonist Resident in Scotland with a Community Health Index (CHI) number The attending clinician has equipoise regarding the duration of therapy Provision of informed consent", "candidate_expression": "((=18 years) AND (Aged) AND (P2Y12 receptor antagonist) AND (Provision of informed consent) AND (Resident) AND (Scotland) AND (acute coronary syndrome) AND (aspirin) AND (dual anti-platelet therapy) AND (requires))"}
```
