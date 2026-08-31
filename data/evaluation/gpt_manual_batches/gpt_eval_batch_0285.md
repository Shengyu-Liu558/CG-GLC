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
{"candidate_id": "LLM07101", "doc_id": "NCT01801072_exc", "case_bucket": "or", "source_criterion": "History of seizures within last 10 years History of epilepsy History of prior stroke Currently prescribed medication with anti-epileptic activity (keppra, dilantin, tegretol, lamictal, topamax, etc.) Brain tumor Pregnant or nursing woman Known levetiracetam allergy", "candidate_expression": "((Brain tumor) AND (allergy) AND (epilepsy) AND (levetiracetam) AND (medication anti-epileptic activity) AND (seizures within last 10 years) AND (stroke prior) AND (woman) AND ((Pregnant) OR (nursing)) AND ((dilantin) OR (keppra) OR (lamictal) OR (tegretol) OR (topamax)))"}
{"candidate_id": "LLM07102", "doc_id": "NCT02924870_exc", "case_bucket": "or", "source_criterion": "osteoarticular, neuromuscular or cognitive limitation that prevents ambulation previous diagnosis of active neoplastic disease institutionalized patients; alcohol consumption >60 g/day patient belonging to another health sector in the Community of Madrid or other community participation in another study within 6 months prior.", "candidate_expression": "((alcohol consumption >60 g/day) AND (institutionalized) AND (neoplastic disease) AND (participation in another study within 6 months prior.) AND NOT (ambulation) AND ((cognitive limitation) OR (neuromuscular limitation) OR (osteoarticular limitation)))"}
{"candidate_id": "LLM07103", "doc_id": "NCT03256864_inc", "case_bucket": "other", "source_criterion": "Liver Transplant Recipients have received liver transplantations for at least 6+1 months prior to enrollment Liver Transplant Recipients have no acute rejection episodes within 3 months prior to the enrollment and are clinically stable Liver Transplant Recipients have been treated with twice-daily regimen of tacrolimus(TAC) plus everolimus(EVR) and TAC and EVR trough levels have stayed within targeted ranges for at least 6 weeks prior to enrollment Provide written informed consent prior to inclusion. Liver transplant recipients who are 18-65 years of age of a primary liver transplant Allograft functioning at an acceptable level as defined by the AST, ALT, Total Bilirubin levels =3 times ULN prior to enrollment. Abbreviated MDRD eGFR = 30 mL/min/1.73m2.", "candidate_expression": "((ALT) AND (AST) AND (Allograft functioning acceptable level) AND (EVR trough levels) AND (Liver Transplant Recipients) AND (Liver transplant recipients) AND (MDRD eGFR = 30 mL/min/1.73m2) AND (TAC trough levels) AND (Total Bilirubin) AND (age 18-65 years) AND (clinically stable) AND (everolimus(EVR)) AND (liver transplantations for at least 6+1 months prior to enrollment) AND (primary liver transplant) AND (tacrolimus(TAC)) AND (written informed consent prior to inclusion) AND NOT (rejection episodes acute within 3 months prior to the enrollment))"}
{"candidate_id": "LLM07104", "doc_id": "NCT02528604_exc", "case_bucket": "or", "source_criterion": "Paroxysmal atrial fibrillation. Long-standing persistent or permanent atrial fibrillation. Previous pacemaker implantation. Previous atrial ablation. Patient is unable to take warfarin or other oral anti-coagulant medication. Patient is suffering with unstable angina in last one week. Patient has had a myocardial infarction within last two months. Patient is expecting or has had major cardiac surgery within last two months. Patient is participating in a conflicting study. Patient is unable to perform exercise testing. Patient is mentally incapacitated and cannot consent or comply with follow-up. Patient has New York Heart Association (NYHA) class III/IV heart failure. Patient has left ventricular ejection fraction (LVEF) less than 35% not secondary to tachycardia. Pregnancy. Patient suffers with other cardiac rhythm disorders. Recent coronary artery intervention or other factors suggesting clinical instability (ECG, clinical or laboratory findings).", "candidate_expression": "((LVEF) AND (NYHA) AND (New York Heart Association class III/IV) AND (Paroxysmal atrial fibrillation) AND (Patient is mentally incapacitated and cannot consent or comply with follow-up) AND (Patient is participating in a conflicting study) AND (Patient is unable to perform exercise testing) AND (Pregnancy) AND (atrial ablation) AND (atrial fibrillation) AND (cardiac rhythm disorders other) AND (coronary artery intervention) AND (heart failure) AND (left ventricular ejection fraction less than 35%) AND (major cardiac surgery last two months) AND (myocardial infarction last two months) AND (pacemaker implantation) AND (tachycardia not secondary to) AND (unstable angina last one week) AND ((oral anti-coagulant medication) OR (warfarin)) AND ((permanent) OR (persistent)))"}
{"candidate_id": "LLM07105", "doc_id": "NCT03315975_exc", "case_bucket": "or", "source_criterion": "are allergic to influenza vaccination have received influenza vaccination within the past 6 months require prednisone, methotrexate, or other immunosuppressing medications have HIV infection have a history of solid organ or bone marrow transplant require combination immunotherapy are on other studies requiring blood draws that might exceed 450 mL total during the period of the influenza vaccine study", "candidate_expression": "((HIV infection) AND (allergic) AND (are on other studies requiring blood draws that might exceed 450 mL total during the period of the influenza vaccine study) AND (combination immunotherapy) AND (history) AND (influenza vaccination) AND (other) AND (require) AND (within the past 6 months) AND ((bone marrow transplant) OR (solid organ transplant)) AND ((immunosuppressing medications) OR (methotrexate) OR (prednisone)))"}
{"candidate_id": "LLM07106", "doc_id": "NCT03195153_inc", "case_bucket": "or", "source_criterion": "diabetic patient; therapy with aspirin and insulin; patient well responders", "candidate_expression": "((diabetic) AND (well responders) AND ((aspirin) OR (insulin)))"}
{"candidate_id": "LLM07107", "doc_id": "NCT02414399_exc", "case_bucket": "other", "source_criterion": "Contraindication to azithromycin use and other prophylactic antibiotic use", "candidate_expression": "((Contraindication) AND (azithromycin) AND (other) AND (prophylactic antibiotic use))"}
{"candidate_id": "LLM07108", "doc_id": "NCT02892968_exc", "case_bucket": "or", "source_criterion": "ED physicians who work casually (less than 0.25 Full Time Equivalent) ED Physicians who are routinely using U/S guided RA for hip fracture patients, or decline participation in the trial. Patients' age less than 65 years; Patients who are delirious on initial assessment by ED physician or severe dementia Patients with communication problems (critically ill, unconscious, language barrier despite use of secure telephone-based translation service) Patients with allergies to narcotics or local anesthetic; or anticoagulant use (e.g. warfarin, dabigatran, rivaroxaban). Patients with hip fractures not requiring surgery (e.g. greater trochanter avulsion) will also be excluded.", "candidate_expression": "((age) AND (communication problems) AND (greater trochanter avulsion) AND (hip fractures) AND (initial assessment) AND (less than 65 years) AND (local anesthetic) AND (narcotics) AND (not) AND (on initial assessment) AND (requiring surgery) AND (severe) AND (surgery) AND ((critically ill) OR (language barrier) OR (unconscious)) AND ((allergies) OR (anticoagulant)) AND ((dabigatran) OR (rivaroxaban) OR (warfarin)) AND ((delirious) OR (dementia)))"}
{"candidate_id": "LLM07109", "doc_id": "NCT02509949_inc", "case_bucket": "other", "source_criterion": "age > 17 and < 60 years; American Society of Anesthesiology (ASA) I-III; admitted for living donor renal transplantation.", "candidate_expression": "((American Society of Anesthesiology (ASA) I-III) AND (age > 17 and < 60 years) AND (living donor renal transplantation admitted for))"}
{"candidate_id": "LLM07110", "doc_id": "NCT02529475_exc", "case_bucket": "or", "source_criterion": "Patients minors Patients on a legal protection regime type guardianship Respiratory pathologies, cardiovascular, renal, diabetes Claustrophobia Contraindications to exposure to a magnetic field Contraindications to injecting Dotarem ®", "candidate_expression": "((Claustrophobia) AND (Contraindications) AND (Dotarem) AND (Respiratory pathologies) AND (cardiovascular) AND (diabetes) AND (legal protection regime type guardianship) AND (magnetic field) AND (minors) AND (renal))"}
{"candidate_id": "LLM07111", "doc_id": "NCT02416869_exc", "case_bucket": "or", "source_criterion": "Heavy tobacco smokers Drug and / or alcohol abusers", "candidate_expression": "((Drug abusers) AND (Heavy tobacco smokers) AND (alcohol abusers))"}
{"candidate_id": "LLM07112", "doc_id": "NCT01742117_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07113", "doc_id": "NCT02550080_inc", "case_bucket": "or", "source_criterion": "Diagnosed with cutaneous vasculitis, urticaria, psoriasis, acne, bullous skin diseases, sterile pustulosis, leprosy, pneumocystis pneumonia and any other patients who need dapsone administration. Subjects are dapsone-naive. All subjects must have a clinical need for treatment with dapsone that precedes the decision to participate in the study. All subjects are willing to complete the 6-weeks period clinical trial. All subjects are written informed consent.", "candidate_expression": "((All subjects are willing to complete the 6-weeks period clinical trial) AND (All subjects are written informed consent) AND (acne) AND (bullous skin diseases) AND (cutaneous vasculitis) AND (dapsone) AND (leprosy) AND (naive) AND (pneumocystis pneumonia) AND (psoriasis) AND (sterile pustulosis) AND (urticaria))"}
{"candidate_id": "LLM07114", "doc_id": "NCT02990403_inc", "case_bucket": "other", "source_criterion": "Woman who had 2 miscarriage before 12(th) week of gestation.The patient who is diagnosed as thrombophilia with recurrent pregnancy loss. Signed consent form.", "candidate_expression": "((Signed consent form.) AND (Woman) AND (miscarriage 2 before 12(th) week of gestation before 12(th) week of gestation) AND (pregnancy loss recurrent) AND (thrombophilia))"}
{"candidate_id": "LLM07115", "doc_id": "NCT03297021_inc", "case_bucket": "or", "source_criterion": "ASA I, II, III presenting for ambulatory surgery to be performed under general anesthesia", "candidate_expression": "((ASA) AND (ambulatory surgery under general anesthesia) AND (general anesthesia) AND ((I) OR (II) OR (III)))"}
{"candidate_id": "LLM07116", "doc_id": "NCT02537899_exc", "case_bucket": "or", "source_criterion": "Non survivable injury Multiple significant trauma (i.e. significant intracranial and extracranial injuries including limb fractures) that would limit observation of recovery from spinal cord injury Other conditions that would limit clinical assessment of outcomes (e.g. dementia, demyelinating disease, autoimmune disease, etc) Refusal of treatment or contraindication to NeuroAiD", "candidate_expression": "((NeuroAiD) AND (autoimmune disease) AND (contraindication) AND (dementia) AND (demyelinating disease) AND (extracranial injuries) AND (injury Non survivable) AND (intracranial injuries) AND (limb fractures) AND (trauma Multiple significant))"}
{"candidate_id": "LLM07117", "doc_id": "NCT02425774_inc", "case_bucket": "or", "source_criterion": "patients undergoing partial or full resection of the pancreas due to a benign or malignant tumor", "candidate_expression": "((full resection of the pancreas) AND (partial resection of the pancreas) AND ((benign tumor) OR (malignant tumor)))"}
{"candidate_id": "LLM07118", "doc_id": "NCT02934269_exc", "case_bucket": "or", "source_criterion": "Exposure/treatment to an investigational (new chemical entity) or marketed drug or biologic within 30 days preceding the first dose administration, or five half-lives of that investigational drug or biologic, if known (whichever is longer). Donation blood or serum within 8 weeks before the first dose administration to a blood bank or blood donation center. History of alcohol or drug abuse (as defined by the current version of the DSM) within 2 years before the first dose administration, or positive alcohol or drug screen. Vaccination within 30 days prior to the first dose administration or has plans to receive a vaccination during the course of the study (including the follow phone call on Day 105).", "candidate_expression": "((Donation blood within 8 weeks before) AND (Donation serum within 8 weeks before) AND (Vaccination within 30 days prior) AND (alcohol abuse) AND (alcohol screen positive) AND (current version of the DSM) AND (drug abuse) AND (drug screen positive) AND (vaccination plans during the course))"}
{"candidate_id": "LLM07119", "doc_id": "NCT01650792_inc", "case_bucket": "other", "source_criterion": "Diagnosis of heart failure according to Framingham criteria Informed consent Age 18 years or above", "candidate_expression": "((Age 18 years or above) AND (Informed consent) AND (heart failure Framingham criteria))"}
{"candidate_id": "LLM07120", "doc_id": "NCT02805504_exc", "case_bucket": "or", "source_criterion": "Pregnant and/or nursing mothers. Allergy to bupivacaine. History of drug/alcohol abuse. Severe cardiovascular, hepatic, renal disease or neurological impairment.", "candidate_expression": "((Allergy) AND (Pregnant) AND (bupivacaine) AND (disease cardiovascular) AND (drug/alcohol abuse History) AND (hepatic disease) AND (neurological impairment) AND (nursing) AND (renal disease))"}
{"candidate_id": "LLM07121", "doc_id": "NCT03146390_exc", "case_bucket": "or", "source_criterion": "Smoker or former smoker. Presence of dental prostheses. Presence of orthodontic devices. Antibiotic treatment or routine use of oral antiseptics in the previous 3 months. Presence of any systemic disease that could alter the production or composition of saliva.", "candidate_expression": "((Antibiotic) AND (dental prostheses) AND (oral antiseptics routine use in the previous 3 months) AND (orthodontic devices) AND (systemic disease could alter the production or composition of saliva) AND ((Smoker) OR (former smoker)))"}
{"candidate_id": "LLM07122", "doc_id": "NCT02443623_exc", "case_bucket": "or", "source_criterion": "History of severe related adverse event(s) from previous participation in VA-001 or VA-006 trials or to any smallpox vaccination. Eczema, history of eczema, exfoliative skin conditions, wounds, burns, or other skin conditions at the investigator's discretion. A history of immunodeficiency. Currently or has recently received radiotherapy or chemotherapy, adrenocorticotropic hormone (ACTH), corticosteroids, or immunosuppressive drugs. Eye disease treated with topical steroids. Known or suspected disorders of immunoglobulin synthesis. Leukemia, lymphomas of any type, melanoma, or other malignant neoplasms affecting the bone marrow or lymphatic systems. Has been diagnosed with cancer and who will be undergoing chemotherapy or radiation therapy during the vaccination healing time. Is a transplant recipient (except for corneal transplant). Is pregnant, planning pregnancy or breast feeding (female subjects of childbearing potential must have negative pregnancy test prior to vaccination). Household or other close/intimate contact(s) under the age of 12 months. History of allergies to phenol, any of the antibiotics listed in the vaccine content, or any other component of ACAM2000 or its diluents. Subjects with kidney disease (except kidney stones). Subjects with abnormal EKG at screening (if applicable). To mitigate the risk of enrolling at risk subjects and potentially jeopardizing subject safety an EKG will be performed prior to vaccination with ACAM2000 smallpox vaccine in all potential subjects =50 years old and for all potential subjects <50 with two cardiac risk factors as listed immediately below including; severely or morbidly obese or higher obesity classification (BMI =36); high blood pressure; high blood cholesterol; diabetes or high blood sugar; a first degree relative who had a heart condition before the age of 50; and current tobacco smokers. Severely or morbidly obese or higher obesity classification (BMI =36) High blood pressure diagnosed by a doctor High blood cholesterol diagnosed by a doctor Diabetes or high blood sugar diagnosed by a doctor A first degree relative (for example, mother, father, brother, sister) who had a heart condition before the age of 50 Currently smokes tobacco (cigarettes) Arrhythmia Syncope related to cardiac disease Previous myocardial infarction Angina Coronary artery disease Congestive heart failure Cardiomyopathy Stroke or transient ischemic attack Myocarditis Pericarditis Chest pain or shortness of breath with activity (such as climbing stairs), peripheral edema, heart palpitations, dry cough, irregular heartbeat, excessive fatigue, unexplained syncope Other heart conditions being treated by a physician", "candidate_expression": "((A first degree relative) AND (ACAM2000) AND (ACAM2000 diluents) AND (ACTH) AND (Angina) AND (Arrhythmia) AND (BMI =36) AND (Cardiomyopathy) AND (Chest pain) AND (Congestive heart failure) AND (Coronary artery disease) AND (Diabetes) AND (EKG abnormal at screening) AND (Eczema) AND (Eye disease) AND (High blood cholesterol) AND (High blood pressure) AND (Household) AND (Leukemia) AND (Myocarditis) AND (Other heart conditions) AND (Pericarditis) AND (Previous myocardial infarction) AND (Stroke) AND (Syncope) AND (adrenocorticotropic hormone) AND (adverse event) AND (age 50) AND (age under 12 months) AND (allergies) AND (antibiotics listed in the vaccine content) AND (at the investigator's discretion) AND (bone marrow) AND (breast feeding) AND (brother) AND (burns) AND (cardiac disease) AND (chemotherapy) AND (childbearing potential) AND (close/intimate contact(s)) AND (corticosteroids) AND (diagnosed with cancer) AND (disorders of immunoglobulin synthesis) AND (dry cough) AND (excessive fatigue) AND (exfoliative skin conditions) AND (father) AND (female) AND (heart condition before the age of 50) AND (heart palpitations) AND (high blood sugar) AND (higher obesity classification) AND (history of eczema) AND (history of immunodeficiency) AND (immunosuppressive drugs) AND (irregular heartbeat) AND (kidney disease) AND (lymphatic systems) AND (lymphomas) AND (malignant neoplasms affecting the bone marrow affecting lymphatic systems) AND (melanoma) AND (mother) AND (obese Severely morbidly) AND (other skin conditions) AND (peripheral edema) AND (phenol) AND (planning pregnancy) AND (pregnancy test negative prior to vaccination vaccination) AND (pregnant) AND (radiation therapy) AND (radiotherapy) AND (shortness of breath with activity) AND (sister) AND (smallpox vaccination) AND (smokes cigarettes) AND (smokes tobacco) AND (syncope) AND (topical steroids Known suspected) AND (transient ischemic attack) AND (transplant recipient) AND (vaccination) AND (vaccine) AND (wounds) AND NOT (corneal transplant) AND NOT (kidney stones))"}
{"candidate_id": "LLM07123", "doc_id": "NCT02621489_inc", "case_bucket": "or", "source_criterion": "Patients eligible for PCI with application of DES, due to ACS. Patients with known or newly diagnosed T2D (type 2 diabetes is diagnosed according to current WHO criteria or by the use of anti-diabetic drugs) Male and female subjects 18-80 years. HbA1c (accordingly to IFCC) 47 mmol/mol - 110 mmol/mol. Signed informed consent form.", "candidate_expression": "((18-80) AND (47 mmol/mol - 110 mmol/mol) AND (ACS) AND (DES) AND (HbA1c) AND (Male) AND (PCI) AND (Signed informed consent form) AND (T2D) AND (female) AND (years))"}
{"candidate_id": "LLM07124", "doc_id": "NCT02827487_exc", "case_bucket": "other", "source_criterion": "Previous vaginal delivery. Submucous myoma. Uterine anomalies. Undiagnosed vaginal bleeding. Pelvic inflammatory disease.", "candidate_expression": "((Pelvic inflammatory disease) AND (Previous) AND (Submucous myoma) AND (Undiagnosed) AND (Uterine anomalies) AND (vaginal bleeding) AND (vaginal delivery))"}
{"candidate_id": "LLM07125", "doc_id": "NCT02105090_exc", "case_bucket": "or", "source_criterion": "amide and/or esther local anaesthetic allergy paraben allergy Child-Pugh grade B/C liver failure renal insufficiency (calculated glomerular filtration rate under 60 ml/min/1.73 m2 according to Cockcroft-Gault scale ) dementia those presenting with swallowing problem chronic pain condition chronic use of pain medication pregnancy lactation", "candidate_expression": "((B) AND (C) AND (Child-Pugh grade) AND (Cockcroft-Gault scale) AND (allergy) AND (amide local anaesthetic) AND (calculated glomerular filtration rate) AND (chronic pain condition) AND (chronic use) AND (dementia) AND (esther local anaesthetic) AND (lactation) AND (liver failure) AND (pain medication) AND (paraben) AND (pregnancy) AND (renal insufficiency) AND (swallowing problem) AND (under 60 ml/min/1.73 m2))"}
```
