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
{"candidate_id": "LLM02826", "doc_id": "NCT01978028_exc", "case_bucket": "or", "source_criterion": "Hemochromatosis, iron overload, defined as TSAT > 45% Known hypersensitivity to Ferinject®. Known active infection, CRP>20 mg/L, clinically significant bleeding, active malignancy. Chronic liver disease and/or screening alanine transaminase (ALT) or aspartate transaminase (AST) above three times the upper limit of the normal range. Immunosuppressive therapy or renal dialysis (current or planned within the next 6 months). History of erythropoietin, i. v. or oral iron therapy, and blood transfusion in previous 12 weeks and/or such therapy planned within the next 6 months. Unstable angina pectoris as judged by the investigator, clinically significant uncorrected valvular disease or left ventricular outflow obstruction, obstructive cardiomyopathy, poorly controlled fast atrial fibrillation or flutter, poorly controlled symptomatic brady- or tachyarrhythmias. Acute myocardial infarction or acute coronary syndrome, transient ischemic attack or stroke within the last 3 months. Coronary-artery bypass graft, percutaneous intervention (e.g. cardiac, cerebrovascular, aortic; diagnostic catheters are allowed) or major surgery, including thoracic and cardiac surgery, within the last 3 months. Participation in a CHF training program. Known HIV/AIDS. Inability to fully comprehend and/or perform study procedures in the investigator's opinion. Vitamin B12 and/or serum folate deficiency according to the laboratory (re-screening is possible after substitution therapy). Pregnancy or lactation. Participation in another clinical trial within previous 30 days and/or anticipated participation in another trial during this study. Anticoagulation", "candidate_expression": "((> 45%) AND (>20 mg/L) AND (AIDS) AND (Acute myocardial infarction) AND (Anticoagulation) AND (CRP) AND (Chronic liver disease) AND (Coronary-artery bypass graft) AND (Ferinject®) AND (Hemochromatosis) AND (Immunosuppressive therapy) AND (Inability to fully comprehend and/or perform study procedures in the investigator's opinion) AND (Known HIV) AND (Participation in another clinical trial within previous 30 days and/or anticipated participation in another trial during this study.) AND (Pregnancy) AND (TSAT) AND (Unstable angina pectoris) AND (Vitamin B12 deficiency) AND (above three times the upper limit of the normal range) AND (active) AND (active infection) AND (acute coronary syndrome) AND (alanine transaminase (ALT)) AND (aspartate transaminase (AST)) AND (bleeding) AND (blood transfusion) AND (brady-) AND (cardiac surgery) AND (clinically significant) AND (current) AND (erythropoietin) AND (fast atrial fibrillation) AND (fast atrial flutter) AND (hypersensitivity) AND (i. v. iron therapy) AND (in previous 12 weeks) AND (iron overload) AND (lactation) AND (left ventricular outflow obstruction) AND (major surgery) AND (malignancy) AND (obstructive cardiomyopathy) AND (oral iron therapy) AND (percutaneous intervention) AND (planned) AND (poorly controlled) AND (renal dialysis) AND (serum folate deficiency) AND (stroke) AND (symptomatic) AND (tachyarrhythmias) AND (the last 3 months) AND (the next 6 months) AND (thoracic surgery) AND (transient ischemic attack) AND (valvular disease) AND (within the last 3 months) AND (within the next 6 months))"}
{"candidate_id": "LLM02827", "doc_id": "NCT01701219_exc", "case_bucket": "or", "source_criterion": "1. For subjects in Cohort A: previous therapy for more than 48 hours with any parenteral antibiotic with activity against S. aureus within 72 hours of positive blood culture results. 2. For subjects in Cohort B: previous therapy for more than 48 hours with any parenteral antibiotic with activity against MRSA, except vancomycin and/or daptomycin, within 72 hours of positive blood culture results confirming persistence. 3. Previous episode of S. aureus bacteremia within 3 months. 4. Known left-sided endocarditis or prosthetic heart valve. 5. Osteomyelitis or prosthetic joint infection except new onset nonhardware-associated vertebral osteomyelitis. 6. History of any hypersensitivity or allergic reaction to any β-lactam antibacterial agent. 7. Evidence of significant hepatic, hematologic, or immunologic impairment. 8. Pregnant or nursing females.", "candidate_expression": "((Cohort A) AND (Cohort B) AND (History) AND (MRSA) AND (Osteomyelitis) AND (Pregnant) AND (S. aureus) AND (S. aureus bacteremia) AND (allergic reaction) AND (blood culture) AND (daptomycin) AND (except) AND (females) AND (for more than 48 hours) AND (hematologic impairment) AND (hepatic impairment) AND (hypersensitivity) AND (immunologic impairment) AND (left-sided) AND (left-sided endocarditis) AND (new onset) AND (nonhardware-associated) AND (nursing) AND (parenteral) AND (parenteral antibiotic with activity against MRSA) AND (parenteral antibiotic with activity against S. aureus) AND (positive blood culture results) AND (positive results) AND (previous) AND (prosthetic heart valve) AND (prosthetic joint infection) AND (therapy) AND (vancomycin) AND (vertebral osteomyelitis) AND (with activity against MRSA) AND (with activity against S. aureus) AND (within 3 months) AND (within 72 hours of positive blood culture results) AND (β-lactam antibacterial agent))"}
{"candidate_id": "LLM02828", "doc_id": "NCT03382106_exc", "case_bucket": "or", "source_criterion": "Women only: Cannot be pregnant or nursing at baseline or plan to become pregnant during the course of the study Body Mass Index (BMI) > 32 Weight > 220 pounds Allergies to shell fish, seafood, eggs or iodine Heart disease, kidney disease or diabetes Diagnosis of asthma Any metal in or on the body (that cannot be removed) between the nose and the abdomen Any major organ system disease (by judgment of the study medical team) A glomerular filtration rate of 60 cc per minute or less. Nitroglycerin usage or nitrates and use of phosphodiesterase 5 (PDE5) inhibitors Prior history of hypersensitivity to sildenafil Currently prescribed a phosphodiesterase (PDE) inhibitors medication (ex: Viagra, Cialis, etc) Known Pulmonary Hypertension Has used e-cigarettes and marijuana <1 years", "candidate_expression": "((60 cc per minute or less) AND (<1 years) AND (> 220 pounds) AND (> 32) AND (Allergies) AND (Body Mass Index (BMI)) AND (Cannot be pregnant or nursing at baseline or plan to become pregnant during the course of the study) AND (Cialis) AND (Heart disease) AND (Nitroglycerin) AND (Prior history) AND (Pulmonary Hypertension) AND (Viagra) AND (Weight) AND (Women) AND (asthma) AND (between the nose and the abdomen) AND (diabetes) AND (eggs) AND (glomerular filtration rate) AND (hypersensitivity) AND (iodine) AND (kidney disease) AND (major organ system disease) AND (metal in the body) AND (metal on the body) AND (nitrates) AND (phosphodiesterase (PDE) inhibitors) AND (phosphodiesterase 5 (PDE5) inhibitors) AND (seafood) AND (shell fish) AND (sildenafil) AND (used e-cigarettes) AND (used marijuana))"}
{"candidate_id": "LLM02829", "doc_id": "NCT03173092_exc", "case_bucket": "or", "source_criterion": "Failure to have fully recovered (that is, less than or equal to [<=] Grade 1 toxicity) from the reversible effects of prior chemotherapy. Major surgery within 14 days before enrollment. Radiotherapy within 14 days before enrollment (if the involved field is small, 7 days will be considered a sufficient interval between treatment and administration of the ixazomib.) Central nervous system involvement. Infection requiring systemic antibiotic therapy or other serious infection within 14 days before study enrollment. Evidence of current uncontrolled cardiovascular conditions, including uncontrolled hypertension, uncontrolled cardiac arrhythmias, symptomatic congestive heart failure, unstable angina, or myocardial infarction within the past 6 months. Systemic treatment, within 14 days before the first dose of ixazomib, with strong cytochrome P450 3A (CYP3A) inducers (rifampin, rifapentine, rifabutin, carbamazepine, phenytoin, phenobarbital), or use of Ginkgo biloba or St. John's wort. Ongoing or active systemic infection, active hepatitis B or C virus infection, or known human immunodeficiency virus positive. Diagnosed or treated for another malignancy within 2 years before study enrollment or previously diagnosed with another malignancy and have any evidence of residual disease. Participants with non-melanoma skin cancer or carcinoma in situ of any type are not excluded if they have undergone complete resection. Has greater than or equal to (>=) Grade 2 peripheral neuropathy, or Grade 1 with pain on clinical examination during the screening period. PD on first-line therapy. Participation in other interventional clinical trials, including those with other investigational agents not included in this trial, within 30 days of the start of this trial and throughout the duration of this trial. Non-interventional trials (that is, observational trials) are permitted at any time point.", "candidate_expression": "((Central nervous system involvement) AND (Major surgery within 14 days before enrollment) AND (PD first-line therapy) AND (Participation in other interventional clinical trials) AND (Radiotherapy) AND (Systemic treatment within 14 days before the first dose of ixazomib) AND (cardiovascular conditions current uncontrolled) AND (chemotherapy) AND (ixazomib) AND (pain) AND (peripheral neuropathy greater than or equal to (>=) Grade 2 Grade 1) AND (residual disease any evidence of) AND (systemic antibiotic therapy) AND (toxicity less than or equal to [<=] Grade 1) AND NOT (fully recovered) AND NOT (complete resection) AND ((involved field is small 7 days) OR (within 14 days before enrollment)) AND ((Infection) OR (infection other serious within 14 days before study enrollment)) AND ((cardiac arrhythmias uncontrolled) OR (congestive heart failure symptomatic) OR (hypertension uncontrolled) OR (myocardial infarction within the past 6 months) OR (unstable angina)) AND ((carbamazepine) OR (phenobarbital) OR (phenytoin) OR (rifabutin) OR (rifampin) OR (rifapentine)) AND ((Ginkgo biloba) OR (St. John's wort) OR (strong cytochrome P450 3A (CYP3A) inducers)) AND ((Ongoing) OR (active)) AND ((C virus infection) OR (hepatitis B virus infection)) AND ((human immunodeficiency virus positive) OR (systemic infection)) AND ((malignancy previously another) OR (malignancy within 2 years before study enrollment)) AND ((carcinoma in situ any type) OR (non-melanoma skin cancer)) AND ((throughout the duration of this trial the duration of this trial) OR (within 30 days of the start of this trial the start of this trial)))"}
{"candidate_id": "LLM02830", "doc_id": "NCT01717911_exc", "case_bucket": "or", "source_criterion": "Previous treated with anti-diabetic medication Pregnant or nursing women. Impaired liver function (ALT > 120 U/L) Impaired renal function (Serum creatinine >1.5 mg/dL in male, >1.4 mg/dL in female ) Recently suffered from MI or CVA. Patients are acute intercurrent illness. 2-hour C-peptide level < 1.8 ng/mL.", "candidate_expression": "((2-hour C-peptide level) AND (< 1.8 ng/mL) AND (> 120 U/L) AND (>1.4 mg/dL) AND (>1.5 mg/dL) AND (ALT) AND (Impaired liver function) AND (Impaired renal function) AND (Previous) AND (Recently) AND (Serum creatinine) AND (acute intercurrent illness) AND (anti-diabetic medication) AND (treated) AND (women) AND ((female) OR (male)) AND ((CVA) OR (MI)) AND ((Pregnant) OR (nursing)))"}
{"candidate_id": "LLM02831", "doc_id": "NCT02041299_exc", "case_bucket": "or", "source_criterion": "Thalassemia syndromes; Myelodysplastic syndrome (MDS) or myelofibrosis; Diamond Blackfan anemia; Primary bone marrow failure; Baseline LIC >30 mg/g dw (measured by MRI); Unable or unwilling to undergo a 7 day washout period if currently being treated with deferiprone or deferoxamine or deferasirox; Previous discontinuation of treatment with deferiprone or deferoxamine due to adverse events; History or presence of hypersensitivity or idiosyncratic reaction to deferiprone or deferoxamine; Treated with hydroxyurea within 30 days; History of malignancy; Evidence of abnormal liver function (serum ALT level(s) > 5 times upper limit of normal at screening or creatinine levels >2 times upper limit of normal at screening); A serious, unstable illness, as judged by the Investigator, during the past 3 months before screening/baseline visit including but not limited to: hepatic, renal, gastro-enterologic, respiratory, cardiovascular, endocrinologic, neurologic or immunologic disease; Clinically significant abnormal 12-lead ECG findings; Cardiac MRI T2* <10ms; Myocardial infarction, cardiac arrest or cardiac failure within 1 year before screening/baseline visit; Unable to undergo MRI Presence of metallic objects such as artificial joints, inner ear (cochlear) implants, brain aneurysm clips, pacemakers, and metallic foreign bodies in the eye or other body areas that would prevent use of MRI imaging", "candidate_expression": "((12-lead ECG) AND (Cardiac MRI T2* <10ms) AND (Diamond Blackfan anemia) AND (LIC Baseline >30 mg/g) AND (MRI) AND (MRI measured by) AND (Presence of metallic objects such as artificial joints, inner ear (cochlear) implants, brain aneurysm clips, pacemakers, and metallic foreign bodies in the eye or other body areas that would prevent use of MRI imaging) AND (Primary bone marrow failure) AND (Thalassemia syndromes) AND (Unable or unwilling to undergo a 7 day washout period if currently being treated with deferiprone or deferoxamine or deferasirox) AND (Unable to undergo) AND (discontinuation of treatment) AND (findings Clinically significant abnormal) AND (hydroxyurea within 30 days) AND (liver function abnormal) AND (malignancy) AND (unstable illness serious during the past 3 months before screening/baseline visit) AND ((deferiprone) OR (deferoxamine)) AND ((hypersensitivity) OR (idiosyncratic reaction)) AND ((Myelodysplastic syndrome (MDS)) OR (myelofibrosis)) AND ((creatinine levels >2 times upper limit of normal at screening) OR (serum ALT level(s) > 5 times upper limit of normal at screening)) AND ((cardiovascular disease) OR (endocrinologic disease) OR (gastro-enterologic disease) OR (hepatic disease) OR (immunologic disease) OR (neurologic disease) OR (renal disease) OR (respiratory disease)) AND ((Myocardial infarction) OR (cardiac arrest) OR (cardiac failure)))"}
{"candidate_id": "LLM02832", "doc_id": "NCT02443623_exc", "case_bucket": "or", "source_criterion": "History of severe related adverse event(s) from previous participation in VA-001 or VA-006 trials or to any smallpox vaccination. Eczema, history of eczema, exfoliative skin conditions, wounds, burns, or other skin conditions at the investigator's discretion. A history of immunodeficiency. Currently or has recently received radiotherapy or chemotherapy, adrenocorticotropic hormone (ACTH), corticosteroids, or immunosuppressive drugs. Eye disease treated with topical steroids. Known or suspected disorders of immunoglobulin synthesis. Leukemia, lymphomas of any type, melanoma, or other malignant neoplasms affecting the bone marrow or lymphatic systems. Has been diagnosed with cancer and who will be undergoing chemotherapy or radiation therapy during the vaccination healing time. Is a transplant recipient (except for corneal transplant). Is pregnant, planning pregnancy or breast feeding (female subjects of childbearing potential must have negative pregnancy test prior to vaccination). Household or other close/intimate contact(s) under the age of 12 months. History of allergies to phenol, any of the antibiotics listed in the vaccine content, or any other component of ACAM2000 or its diluents. Subjects with kidney disease (except kidney stones). Subjects with abnormal EKG at screening (if applicable). To mitigate the risk of enrolling at risk subjects and potentially jeopardizing subject safety an EKG will be performed prior to vaccination with ACAM2000 smallpox vaccine in all potential subjects =50 years old and for all potential subjects <50 with two cardiac risk factors as listed immediately below including; severely or morbidly obese or higher obesity classification (BMI =36); high blood pressure; high blood cholesterol; diabetes or high blood sugar; a first degree relative who had a heart condition before the age of 50; and current tobacco smokers. Severely or morbidly obese or higher obesity classification (BMI =36) High blood pressure diagnosed by a doctor High blood cholesterol diagnosed by a doctor Diabetes or high blood sugar diagnosed by a doctor A first degree relative (for example, mother, father, brother, sister) who had a heart condition before the age of 50 Currently smokes tobacco (cigarettes) Arrhythmia Syncope related to cardiac disease Previous myocardial infarction Angina Coronary artery disease Congestive heart failure Cardiomyopathy Stroke or transient ischemic attack Myocarditis Pericarditis Chest pain or shortness of breath with activity (such as climbing stairs), peripheral edema, heart palpitations, dry cough, irregular heartbeat, excessive fatigue, unexplained syncope Other heart conditions being treated by a physician", "candidate_expression": "((50) AND (=36) AND (A first degree relative) AND (ACAM2000) AND (ACAM2000 diluents) AND (ACTH) AND (Angina) AND (Arrhythmia) AND (BMI) AND (Cardiomyopathy) AND (Chest pain) AND (Congestive heart failure) AND (Coronary artery disease) AND (Diabetes) AND (EKG) AND (Eczema) AND (Eye disease) AND (High blood cholesterol) AND (High blood pressure) AND (Household) AND (Known) AND (Leukemia) AND (Myocarditis) AND (Other heart conditions) AND (Pericarditis) AND (Previous myocardial infarction) AND (Severely) AND (Stroke) AND (Syncope) AND (abnormal) AND (adrenocorticotropic hormone) AND (adverse event) AND (affecting lymphatic systems) AND (affecting the bone marrow) AND (age) AND (age of 50) AND (allergies) AND (antibiotics) AND (at screening) AND (at the investigator's discretion) AND (before the age of 50) AND (bone marrow) AND (breast feeding) AND (brother) AND (burns) AND (cardiac disease) AND (chemotherapy) AND (childbearing potential) AND (close/intimate contact(s)) AND (corneal transplant) AND (corticosteroids) AND (diagnosed with cancer) AND (disorders of immunoglobulin synthesis) AND (dry cough) AND (during the vaccination healing time) AND (except) AND (excessive fatigue) AND (exfoliative skin conditions) AND (father) AND (female) AND (heart condition) AND (heart palpitations) AND (high blood sugar) AND (higher obesity classification) AND (history of eczema) AND (history of immunodeficiency) AND (immunosuppressive drugs) AND (irregular heartbeat) AND (kidney disease) AND (kidney stones) AND (listed in the vaccine content) AND (lymphatic systems) AND (lymphomas) AND (malignant neoplasms) AND (melanoma) AND (morbidly) AND (mother) AND (negative) AND (obese) AND (other skin conditions) AND (peripheral edema) AND (phenol) AND (planning pregnancy) AND (pregnancy test) AND (pregnant) AND (prior to vaccination) AND (radiation therapy) AND (radiotherapy) AND (recently) AND (screening) AND (shortness of breath with activity) AND (sister) AND (smallpox vaccination) AND (smokes cigarettes) AND (smokes tobacco) AND (suspected) AND (syncope) AND (topical steroids) AND (transient ischemic attack) AND (transplant recipient) AND (under 12 months) AND (vaccination) AND (vaccination healing time) AND (vaccine) AND (wounds))"}
{"candidate_id": "LLM02833", "doc_id": "NCT03132259_exc", "case_bucket": "or", "source_criterion": "GCS less than 15 Preoperative Heart Rate less than 50 beat/min No Beta-Blockers Pregnant patients Take any Alpha-Methyldopa, Clonodine, Other Alpha-2 Adrenergic Agonist Hemodynamic unstable Systolic BP more than 160mmHg CAD Renal insuffuciency Allergy in dexmedethomidine and opioid BMI more than 30 Denied consent", "candidate_expression": "((Allergy) AND (BMI) AND (Beta-Blockers) AND (CAD) AND (Denied consent) AND (GCS) AND (Hemodynamic unstable) AND (No) AND (Other) AND (Pregnant) AND (Preoperative Heart Rate) AND (Renal insuffuciency) AND (Systolic BP) AND (less than 15) AND (less than 50 beat/min) AND (more than 160mmHg) AND (more than 30) AND ((Alpha-2 Adrenergic Agonist) OR (Alpha-Methyldopa) OR (Clonodine)) AND ((dexmedethomidine) OR (opioid)))"}
{"candidate_id": "LLM02834", "doc_id": "NCT00050349_exc", "case_bucket": "or", "source_criterion": "Patients with symptomatic CNS metastases or leptomeningeal involvement Patients with known brain metastases, unless these metastases have been treated and/or have been stable for at least six months prior to study start. Subjects with a history of brain metastases must have a head CT with contrast to document either response or progression. Patients with bone metastases as the only site(s) of measurable disease Patients with hepatic artery chemoembolization within the last 6 months (one month if there are other sites of measurable disease) Patients who have been previously treated with radioactive directed therapies Patients who have been previously treated with epothilone Patients with any peripheral neuropathy or unresolved diarrhea greater than Grade 1 Patients with severe cardiac insufficiency patients taking Coumadin or other warfarin-containing agents with the exception of low dose warfarin (1 mg or less) for the maintenance of in-dwelling lines or ports Patients taking any experimental therapies history of another malignancy within 5 years prior to study entry except curatively treated non-melanoma skin cancer, prostate cancer, or cervical cancer in situ Patients with active or suspected acute or chronic uncontrolled infection including abcesses or fistulae Patients with a medical or psychiatric illness that would preclude study or informed consent and/or history of noncompliance to medical regimens or inability or unwillingness to return for all scheduled visits HIV+ patients Pregnant or lactating females.", "candidate_expression": "((+) AND (1 mg or less) AND (CNS metastases) AND (Coumadin) AND (Grade) AND (HIV) AND (HIV+) AND (Pregnant) AND (abcesses) AND (active) AND (acute) AND (another malignancy) AND (at least six months prior to study start) AND (been stable for) AND (bone metastases) AND (brain metastases) AND (cervical cancer in situ) AND (chronic) AND (curatively treated) AND (epothilone) AND (except) AND (fistulae) AND (greater than 1) AND (head CT with contrast) AND (hepatic artery chemoembolization) AND (history of) AND (in-dwelling lines) AND (in-dwelling ports) AND (inability to return for all scheduled visits) AND (informed consent) AND (lactating) AND (leptomeningeal involvement) AND (low dose) AND (medical illness) AND (non-melanoma skin cancer) AND (noncompliance to medical regimens) AND (one month) AND (only site(s) of measurable disease) AND (other sites of measurable disease) AND (peripheral neuropathy) AND (preclude study) AND (previously) AND (prostate cancer) AND (psychiatric illness) AND (radioactive directed therapies) AND (severe cardiac insufficiency) AND (suspected) AND (symptomatic) AND (treated) AND (uncontrolled infection) AND (unless) AND (unresolved diarrhea) AND (unwillingness to return for all scheduled visit) AND (warfarin) AND (warfarin-containing agents) AND (with the exception of) AND (within 5 years prior to study entry) AND (within the last 6 months))"}
{"candidate_id": "LLM02835", "doc_id": "NCT01959061_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed colorectal adenocarcinoma Disease limited to the liver Unresectable disease by surgery or other local therapies Age >18 years ECOG performance status 0-2,Child pugh A or B Expected survival = 3 months Adequate hematological, hepatic, and renal function", "candidate_expression": "((0-2) AND (= 3 months) AND (>18 years) AND (Adequate) AND (Age) AND (Child pugh) AND (ECOG performance status) AND (Expected survival) AND (Histologically) AND (Histologically confirmed) AND (colorectal adenocarcinoma) AND (other) AND ((A) OR (B)) AND ((hematological function) OR (hepatic function) OR (renal function)) AND ((Disease limited to the liver) OR (Unresectable disease)) AND ((local therapies) OR (surgery)))"}
{"candidate_id": "LLM02836", "doc_id": "NCT01391780_inc", "case_bucket": "or", "source_criterion": "presence of stress urinary or urgency incontinence", "candidate_expression": "((stress urinary incontinence) AND (urgency incontinence))"}
{"candidate_id": "LLM02837", "doc_id": "NCT03344042_exc", "case_bucket": "scope", "source_criterion": "no consent known allergy to administered opioid contraindications to epidural analgesia coagulopathies including platelet count of less than 100,000 spine surgery in past", "candidate_expression": "((allergy) AND (coagulopathies) AND (contraindications) AND (epidural analgesia) AND (in past) AND (less than 100,000) AND (no consent) AND (opioid) AND (platelet count) AND (spine surgery))"}
{"candidate_id": "LLM02838", "doc_id": "NCT02196285_exc", "case_bucket": "or", "source_criterion": "Serious adverse reaction to any vaccination, as respiratory difficulty, angioedema and anaphylaxis; Acute or chronic disease, as diabetes, heart disease, systemic arterial hypertension; Use of anti-allergic with antigen injections in a maximum timeline of 14 days before the vaccination; Use of immunoglobulin in the past 12 months before the study vaccination; Use of blood products within 12 months before the vaccination; Use of any vaccine type within 30 days before the vaccination of the study; Chronic use of any medication, except homeopathy, and trivial ones, as nasal physiologic solution and vitamins; Previous immunosuppressive or cytotoxic medication, in the last 6 months. Individuals who have made use of this kind of medication in non-immunosuppressant doses, as nasal corticosteroid for allergic rhinitis of topic corticosteroid for non-complicated dermatitis, for more than 14 days, are allowed to be included in the study. Use of any kind of medication under investigation within one year before the vaccination. Unstable asthma or which may have required urgent care, hospitalization or intubation within the last 2 years, or which requires use of oral or intravenous corticosteroid. Coagulopathies diagnosed by a physician or report of capillary fragility (ex: bruises or bleedings without justifiable cause; Convulsions, except the ones caused by fever, before 2 years old; Psychiatric disease which difficults the adherence to the protocol, such as psychosis, obsessive-compulsive disorders, bipolar disease under treatment, diseases which require treatment with lithium and suicidal ideas in the last 5 years from the inclusion; Active malignant (p.e. any kind of cancer) or treated disease, to which the individual may relapse during the study; Asplenia (absence of spleen or its removal); Positive HIV in the screening examination of history of any immunosuppressant disease; Positive serology for C hepatitis in the screening evaluation; Positive Antigen HBs in the screening evaluation; Alcoholism (CAGE criteria), used for detection of abusive drinkers or alcoholic, validated in the Brazilian population with sensibility of 88% and specificity of 83%, if two or more answers, among four possible, are afirmative(Mansur and Monteiro, 1983), or according to medical decision; Abuse of illicit drugs, according to medical decision; Acquired or congenital immunodeficiency; Allergy to the vaccine compounds, as egg, neomycin and gelatin.", "candidate_expression": "((2 years old) AND (Abuse of illicit drugs) AND (Acquired immunodeficiency) AND (Active) AND (Acute disease) AND (Alcoholism) AND (Allergy to the vaccine compounds) AND (Antigen HBs) AND (Asplenia) AND (CAGE criteria) AND (Chronic use) AND (Coagulopathies) AND (Convulsions) AND (HIV) AND (Positive) AND (Psychiatric disease) AND (Unstable asthma) AND (absence of) AND (according to medical decision) AND (adverse reaction) AND (anaphylaxis) AND (angioedema) AND (anti-allergic) AND (antigen injections) AND (any kind) AND (any medication) AND (any vaccine type) AND (before 2 years old) AND (bipolar disease) AND (bleedings) AND (blood products) AND (bruises) AND (cancer) AND (capillary fragility) AND (caused by fever) AND (chronic disease) AND (congenital immunodeficiency) AND (cytotoxic medication) AND (diabetes) AND (difficults the adherence to the protocol) AND (diseases which require treatment with lithium) AND (during the study) AND (egg) AND (except) AND (fever) AND (gelatin) AND (heart disease) AND (homeopathy) AND (hospitalization) AND (immunoglobulin) AND (immunosuppressant disease) AND (immunosuppressive medication) AND (in the last 5 years from the inclusion) AND (in the last 6 months) AND (in the past 12 months before the study vaccination) AND (in the screening evaluation) AND (in the screening examination) AND (intravenous corticosteroid) AND (intubation) AND (lithium) AND (malignant) AND (malignant disease) AND (maximum timeline of 14 days before the vaccination) AND (medication under investigation) AND (nasal physiologic solution) AND (neomycin) AND (obsessive-compulsive disorders) AND (oral corticosteroid) AND (psychosis) AND (required hospitalization) AND (required intubation) AND (required urgent care) AND (requires use of intravenous corticosteroid) AND (requires use of oral corticosteroid) AND (respiratory difficulty) AND (screening evaluation) AND (screening examination) AND (serology for C hepatitis) AND (spleen) AND (spleen removal) AND (suicidal ideas) AND (systemic arterial hypertension) AND (the inclusion) AND (the study) AND (the study vaccination) AND (the vaccination) AND (the vaccination of the study) AND (to which the individual may relapse) AND (to which the individual may relapse during the study) AND (treated) AND (treated disease) AND (treatment) AND (treatment with lithium) AND (trivial ones) AND (under treatment) AND (urgent care) AND (vaccination) AND (vaccine compounds) AND (vitamins) AND (within 12 months before the vaccination) AND (within 30 days before the vaccination of the study) AND (within one year before the vaccination) AND (within the last 2 years) AND (without justifiable cause))"}
{"candidate_id": "LLM02839", "doc_id": "NCT02600000_exc", "case_bucket": "or", "source_criterion": "Unstable angina; Myocardial infarction and heart surgery up to three months before the survey; Chronic respiratory diseases; Hemodynamic instability; Trauma recent face, nausea and vomiting. Orthopedic and neurological diseases that may preclude the achievement of the cardiopulmonary test and Cardiac Rehabilitation exercises; Psychological and / or cognitive impairments that restrict them to respond to questionnaires;", "candidate_expression": "((Chronic respiratory diseases) AND (Hemodynamic instability) AND (Myocardial infarction) AND (Orthopedic) AND (Psychological impairments) AND (Trauma) AND (Unstable angina) AND (cognitive impairments) AND (heart surgery) AND (nausea) AND (neurological diseases) AND (preclude the achievement of the cardiopulmonary test and Cardiac Rehabilitation exercises) AND (restrict them to respond to questionnaires) AND (up to three months before the survey) AND (vomiting))"}
{"candidate_id": "LLM02840", "doc_id": "NCT02774317_inc", "case_bucket": "or", "source_criterion": "Nonsurgical neonates and babies up to age 6 months with INR 1.5 or more who are deemed clinically to need plasma infusion.", "candidate_expression": "((INR 1.5 or more) AND (Nonsurgical) AND (age up to age 6 months) AND (need) AND (plasma infusion) AND ((babies) OR (neonates)))"}
{"candidate_id": "LLM02841", "doc_id": "NCT03233880_exc", "case_bucket": "or", "source_criterion": "Women with multi-fetal pregnancy, diabetes mellitus, chronic hypertension, or chronic renal disease", "candidate_expression": "((Women) AND ((chronic hypertension) OR (chronic renal disease) OR (diabetes mellitus) OR (multi-fetal pregnancy)))"}
{"candidate_id": "LLM02842", "doc_id": "NCT02905890_inc", "case_bucket": "other", "source_criterion": "BV positive by Nugent score HIV negative Capable of providing written informed consent", "candidate_expression": "((BV positive) AND (Capable of providing written informed consent) AND (HIV negative) AND (Nugent score))"}
{"candidate_id": "LLM02843", "doc_id": "NCT01822262_inc", "case_bucket": "other", "source_criterion": "Clinical diagnosis of calculous cholecystitis.", "candidate_expression": "(calculous cholecystitis Clinical diagnosis)"}
{"candidate_id": "LLM02844", "doc_id": "NCT03431831_exc", "case_bucket": "or", "source_criterion": "Inability to understand and read English. Women pregnant or lactating. persons with terminal illness", "candidate_expression": "((Inability to understand and read English) AND (Women) AND (terminal illness) AND ((lactating) OR (pregnant)))"}
{"candidate_id": "LLM02845", "doc_id": "NCT02312960_inc", "case_bucket": "other", "source_criterion": "Subject was previously enrolled in a selected company sponsored feeder trial, and has received at least 1 dose of radium 223 dichloride or placebo in the feeder trial", "candidate_expression": "(Subject was previously enrolled in a selected company sponsored feeder trial, and has received at least 1 dose of radium 223 dichloride or placebo in the feeder trial)"}
{"candidate_id": "LLM02846", "doc_id": "NCT01630954_exc", "case_bucket": "or", "source_criterion": "Partial mole History of treatment for molar pregnancy like prior evacuation or chemotherapy Women requiring hysterectomy for treatment of H Mole", "candidate_expression": "((H Mole) AND (Partial mole) AND (Women) AND (hysterectomy) AND (molar pregnancy) AND (treatment) AND ((chemotherapy) OR (evacuation)))"}
{"candidate_id": "LLM02847", "doc_id": "NCT02798237_inc", "case_bucket": "or", "source_criterion": "= 20years of age; diagnosis of stroke (>6months); sedentary or insufficiently active; have a writing medical permission to participate in the training program.", "candidate_expression": "((= 20years) AND (>6months) AND (age) AND (insufficiently active) AND (sedentary) AND (stroke))"}
{"candidate_id": "LLM02848", "doc_id": "NCT03118232_inc", "case_bucket": "or", "source_criterion": "Nursing homes will be eligible to participate if they meet the following criteria: Licensed nursing home in Orange County or Southern Los Angeles County serving adults Minimal use of chlorhexidine bathing* Minimal use of nasal decolonization* *Minimal use defined as <15% of residents receiving at least one chlorhexidine bath or nasal decolonization treatment during their nursing home stay.", "candidate_expression": "((<15%) AND (Minimal use) AND (Nursing homes) AND (at least one) AND (chlorhexidine) AND (chlorhexidine bath) AND (chlorhexidine bathing) AND (during their nursing home stay) AND (nasal decolonization) AND (nasal decolonization treatment) AND (residents receiving at least one chlorhexidine bath) AND (serving adults) AND ((Licensed nursing home) OR (Orange County) OR (Southern Los Angeles County)))"}
{"candidate_id": "LLM02849", "doc_id": "NCT00396734_inc", "case_bucket": "scope", "source_criterion": "Methadone-maintained cocaine-dependent patients use between 1g to 2g a day; 1 to 3 times a week", "candidate_expression": "((1 to 3 times a week) AND (1g to 2g a day) AND (Methadone) AND (Methadone-maintained) AND (cocaine-dependent))"}
{"candidate_id": "LLM02850", "doc_id": "NCT03444142_inc", "case_bucket": "other", "source_criterion": "Patients both sexes Age between 31 and 60 years Diagnosis of diabetes according ADA criteria:", "candidate_expression": "((ADA criteria) AND (Age) AND (between 31 and 60 years) AND (both sexes) AND (diabetes))"}
```
