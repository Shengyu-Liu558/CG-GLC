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
{"candidate_id": "LLM01226", "doc_id": "NCT02787070_inc", "case_bucket": "or", "source_criterion": "Infection with Plasmodium falciparum or P. vivax either alone or mixed Age >12 months Weight >5kg Living in the study clusters", "candidate_expression": "((>12 months) AND (>5kg) AND (Age) AND (Infection) AND (Weight) AND ((P. vivax) OR (Plasmodium falciparum)))"}
{"candidate_id": "LLM01227", "doc_id": "NCT03233880_exc", "case_bucket": "or", "source_criterion": "Women with multi-fetal pregnancy, diabetes mellitus, chronic hypertension, or chronic renal disease", "candidate_expression": "((Women) AND (chronic hypertension) AND (chronic renal disease) AND (diabetes mellitus) AND (multi-fetal pregnancy))"}
{"candidate_id": "LLM01228", "doc_id": "NCT03402945_inc", "case_bucket": "other", "source_criterion": "≥18 years of age undergoing open-heart surgery (sternotomy, including minimally-invasive sternotomies)", "candidate_expression": "((age) AND (minimally-invasive sternotomies) AND (open-heart surgery) AND (sternotomy) AND (undergoing) AND (≥18 years))"}
{"candidate_id": "LLM01229", "doc_id": "NCT03063866_exc", "case_bucket": "or", "source_criterion": "Emergent condition like hematemesis. Patients with moderate to severe hepatic encephalopathy. Patients with hepatopulmonary syndrome. Patients with known or suspected hypersensitivity to the used medication were also excluded from the study.", "candidate_expression": "((Emergent condition) AND (hematemesis) AND (hepatic encephalopathy) AND (hepatopulmonary syndrome) AND (hypersensitivity) AND (known) AND (moderate) AND (severe) AND (suspected) AND (used medication))"}
{"candidate_id": "LLM01230", "doc_id": "NCT01891383_exc", "case_bucket": "or", "source_criterion": "Cases (with a history of TBI): 1. History of penetrating brain injury 2. History of disabling neurological or psychiatric condition such as epilepsy (besides posttraumatic epilepsy), multiple sclerosis, cortical stroke, hypoxic-ischemic encephalopathy, encephalitis, or schizophrenia Controls (without a history of TBI): History of disabling neurological or psychiatric condition such as epilepsy, multiple sclerosis, cortical stroke, hypoxic-ischemic encephalopathy, encephalitis, or schizophrenia", "candidate_expression": "((History) AND (besides) AND (condition disabling neurological) AND (cortical stroke) AND (disabling neurological condition) AND (disabling psychiatric condition) AND (encephalitis) AND (epilepsy) AND (hypoxic-ischemic encephalopathy) AND (multiple sclerosis) AND (penetrating brain injury) AND (posttraumatic epilepsy) AND (psychiatric condition disabling) AND (schizophrenia))"}
{"candidate_id": "LLM01231", "doc_id": "NCT02321839_inc", "case_bucket": "or", "source_criterion": "Signed informed consent form Male or female of aged 50 years or older Typical AMD and PCV patients BCVA of 24 letters or over", "candidate_expression": "((BCVA 24 letters or over) AND (Signed informed consent form) AND (aged 50 years or older) AND ((Male) OR (female)) AND ((AMD) OR (PCV patients)))"}
{"candidate_id": "LLM01232", "doc_id": "NCT03320057_exc", "case_bucket": "other", "source_criterion": "Not pregnant Not seeking medication abortion Under the age of 15 Contraindications for medication abortion", "candidate_expression": "((Contraindications) AND (Under 15) AND (age) AND (medication abortion) AND (pregnant))"}
{"candidate_id": "LLM01233", "doc_id": "NCT03541980_exc", "case_bucket": "or", "source_criterion": "Patient with fever (38C or 100.4F) Patient less than age 4 years Patient greater than age 16 years Patient with hypersensitivity/allergy to either morphine, NSAIDs, or acetaminophen Patient received acetaminophen within the past 4 hours Patient with known liver disease or renal disease Patient not requiring IV morphine (pain score 5/10 or less) Patient enrolled in the study within the past 72 hours", "candidate_expression": "((IV morphine requiring) AND (NSAIDs) AND (acetaminophen) AND (acetaminophen within the past 4 hours) AND (age greater than 16 years) AND (age less than 4 years) AND (allergy) AND (enrolled in the study within the past 72 hours) AND (fever 38C 100.4F) AND (hypersensitivity) AND (liver disease) AND (morphine) AND (pain score 5/10 or less) AND (renal disease))"}
{"candidate_id": "LLM01234", "doc_id": "NCT02589353_inc", "case_bucket": "other", "source_criterion": "self-reported healthy adults between the ages of 18-60 who are fluent in English.", "candidate_expression": "((adults) AND (ages) AND (between 18-60) AND (fluent in English) AND (healthy) AND (self-reported))"}
{"candidate_id": "LLM01235", "doc_id": "NCT03231982_inc", "case_bucket": "other", "source_criterion": "Adult male and female aged 19 to 75 years Voluntarily consented to participate in the study and signed the informed consent form after receiving the explanation of the objectives, methods and effects of the study.", "candidate_expression": "((19 to 75 years) AND (Voluntarily consented to participate in the study and signed the informed consent form after receiving the explanation of the objectives, methods and effects of the study.) AND (aged) AND (female) AND (male))"}
{"candidate_id": "LLM01236", "doc_id": "NCT03080493_exc", "case_bucket": "or", "source_criterion": "Current use of gabapentin or pregabalin Allergy to gabapentin, acetaminophen, codeine, or ibuprofen Self reported renal disease (severe impaired renal function) Self reported current or chronic narcotic use (typical daily use) Women with any issue that, in the opinion of the investigator, would interfere with study participation or generating accurate study data", "candidate_expression": "((Allergy) AND (Current) AND (Self reported) AND (acetaminophen) AND (chronic) AND (codeine) AND (current) AND (daily use) AND (gabapentin) AND (ibuprofen) AND (impaired renal function) AND (narcotic use) AND (pregabalin) AND (renal disease) AND (severe))"}
{"candidate_id": "LLM01237", "doc_id": "NCT02109081_inc", "case_bucket": "other", "source_criterion": "patients = 70 years of age, undergoing a noncardiac surgical procedure under general anesthesia, with an anticipated duration of postoperative admission of at least 2 days.", "candidate_expression": "((admission postoperative) AND (age = 70 years) AND (duration of postoperative admission anticipated at least 2 days) AND (general anesthesia) AND (noncardiac surgical procedure))"}
{"candidate_id": "LLM01238", "doc_id": "NCT03624881_exc", "case_bucket": "or", "source_criterion": "Previous surgical or catheter ablation for atrial fibrillation Previous cardiac surgery (including CABG) within the past 6 months (180 days) Valvular cardiac surgical/percutaneous procedure (i.e., ventriculotomy, atriotomy, and valve repair or replacement and presence of a prosthetic valve) Any carotid stenting or endarterectomy Documented LA thrombus on imaging LA size > 50 mm (parasternal long axis view) LVEF < 40% Contraindication to anticoagulation (heparin or warfarin) History of blood clotting or bleeding abnormalities PCI/MI within the past 2 months (60 days) Documented thromboembolic event (including TIA) within the past 12 months (365 days) Rheumatic Heart Disease Uncontrolled heart failure or NYHA function class III or IV Severe mitral regurgitation (Regurgitant volume = 60 mL/beat, Regurgitant fraction = 50%, and/or Effective regurgitant orifice area = 0.40cm2) Awaiting cardiac transplantation or other cardiac surgery within the next 12 months (365 days) Unstable angina Acute illness or active systemic infection or sepsis AF secondary to electrolyte imbalance, thyroid disease, or reversible or non-cardiac cause. Presence of implanted ICD/CRT-D. Significant pulmonary disease, (e.g., restrictive pulmonary disease, constrictive or chronic obstructive pulmonary disease) or any other disease or malfunction of the lungs or respiratory system that produces chronic symptoms. Gastroesophageal Reflux Disease (GERD; active requiring significant intervention not including OTC medication) Significant congenital anomaly or medical problem that in the opinion of the investigator would preclude enrollment in this study. Women who are pregnant (as evidenced by pregnancy test if pre-menopausal) Concurrent enrollment in an investigational study evaluating another device, biologic, or drug. Presence of intracardiac thrombus, myxoma, tumor, interatrial baffle or patch or other abnormality that precludes vascular access, or manipulation of the catheter. Life expectancy less than 12 months", "candidate_expression": "((< 40%) AND (= 0.40cm2) AND (= 50%) AND (= 60 mL/beat) AND (> 50 mm) AND (Acute illness) AND (CABG) AND (Concurrent enrollment in an investigational study evaluating another device, biologic, or drug.) AND (Contraindication) AND (GERD) AND (Gastroesophageal Reflux Disease) AND (History) AND (LA size) AND (LA thrombus) AND (LVEF) AND (Life expectancy) AND (MI) AND (NYHA function class) AND (OTC medication) AND (PCI) AND (Previous) AND (Rheumatic Heart Disease) AND (Severe) AND (Significant) AND (TIA) AND (Uncontrolled) AND (Unstable angina) AND (Women) AND (active) AND (anticoagulation) AND (any other) AND (atrial fibrillation) AND (cardiac surgery) AND (chronic symptoms) AND (congenital anomaly) AND (electrolyte imbalance) AND (heart failure) AND (imaging) AND (implanted ICD/CRT-D) AND (less than 12 months) AND (medical problem) AND (mitral regurgitation) AND (not) AND (other) AND (parasternal long axis view) AND (pre-menopausal) AND (precludes) AND (pregnancy test) AND (pregnant) AND (pulmonary disease) AND (reversible) AND (secondary) AND (sepsis) AND (significant intervention) AND (systemic infection) AND (thromboembolic event) AND (within the next 12 months) AND (within the next 365 days) AND (within the past 6 months (180 days)) AND ((Valvular cardiac percutaneous procedure) OR (Valvular cardiac surgical procedure)) AND ((abnormality) OR (interatrial baffle) OR (intracardiac thrombus) OR (myxoma) OR (patch) OR (tumor)) AND ((manipulation of the catheter) OR (vascular access)) AND ((atriotomy) OR (prosthetic valve) OR (valve repair) OR (valve replacement) OR (ventriculotomy)) AND ((carotid stenting) OR (endarterectomy)) AND ((ablation surgical) OR (catheter ablation)) AND ((heparin) OR (warfarin)) AND ((bleeding abnormalities) OR (blood clotting)) AND ((within the past 2 months) OR (within the past 60 days)) AND ((within the past 12 months) OR (within the past 365 days)) AND ((III) OR (IV)) AND ((Effective regurgitant orifice area) OR (Regurgitant fraction) OR (Regurgitant volume)) AND ((cardiac surgery) OR (cardiac transplantation)) AND ((AF) OR (non-cardiac cause) OR (thyroid disease)) AND ((chronic obstructive pulmonary disease) OR (constrictive pulmonary disease) OR (restrictive pulmonary disease)) AND ((disease of the lungs) OR (disease of the respiratory system) OR (malfunction of the lungs)))"}
{"candidate_id": "LLM01239", "doc_id": "NCT03208998_exc", "case_bucket": "or", "source_criterion": "Active consumption of alcohol and/or drugs Co-infection with human immunodeficiency virus, hepatitis C virus, or hepatitis D virus History of autoimmune hepatitis Psychiatric disease Evidence of neoplastic diseases of the liver", "candidate_expression": "((Active) AND (Psychiatric disease) AND (autoimmune hepatitis) AND (liver) AND (neoplastic diseases) AND ((consumption of alcohol) OR (drugs consumption of)) AND ((hepatitis C virus) OR (hepatitis D virus) OR (human immunodeficiency virus)))"}
{"candidate_id": "LLM01240", "doc_id": "NCT02570347_inc", "case_bucket": "other", "source_criterion": "Age 18-65 years History of snake bite with features of local envenomation with/without systemic features Less than 24 hours since bite, AND No prior antibiotic treatment", "candidate_expression": "((Age 18-65 years) AND (bite) AND (local envenomation features of) AND (snake bite) AND (systemic features Less than 24 hours since bite) AND NOT (antibiotic treatment prior))"}
{"candidate_id": "LLM01241", "doc_id": "NCT02152696_exc", "case_bucket": "or", "source_criterion": "Hemodynamically unstable in need of acute treatment Most recent hCG > 5000 mIU/mL Patient obtaining care in relation to a recently completed pregnancy (delivery, spontaneous or elective abortion) Diagnosis of gestational trophoblastic disease Subject unwilling or unable to comply with study procedures Known hypersensitivity to MTX Presence of clinical contraindications for treatment with MTX Prior medical or surgical management of this gestation Subject unwilling to accept a blood transfusion", "candidate_expression": "((Hemodynamically unstable) AND (MTX) AND (Subject unwilling to accept a blood transfusion) AND (gestation) AND (gestational trophoblastic disease) AND (hCG Most recent > 5000 mIU/mL) AND (hypersensitivity to MTX) AND (medical management) AND (surgical management))"}
{"candidate_id": "LLM01242", "doc_id": "NCT03369379_inc", "case_bucket": "or", "source_criterion": "Female patients older than 18 years. Patients who agree to participate in the study. Those that meet the ACR 1990 and 2010 criteria for Fibromyalgia. No previous use of vitamin D. Patients diagnosed with primary or secondary fibromyalgia.", "candidate_expression": "((ACR 1990) AND (ACR 2010) AND (Female) AND (Fibromyalgia) AND (No) AND (Patients who agree to participate in the study.) AND (fibromyalgia) AND (older than 18 years) AND (previous) AND (vitamin D) AND (years) AND ((primary) OR (secondary)))"}
{"candidate_id": "LLM01243", "doc_id": "NCT02019628_inc", "case_bucket": "or", "source_criterion": "1. Women and men ages 18 years and over. 2. Interest in participating in a novel nutritional supplement program. 3. Willingness to follow recommendations.", "candidate_expression": "((18 years and over) AND (Interest in participating in a novel nutritional supplement program.) AND (Willingness to follow recommendations.) AND (ages) AND ((Women) OR (men)))"}
{"candidate_id": "LLM01244", "doc_id": "NCT02863120_inc", "case_bucket": "or", "source_criterion": "Male or non-pregnant female between the ages of 18-65 Patients willing and able to sign the informed consent Patients able to comply with follow-up requirements including self-evaluations Patients requiring a primary total knee replacement Patients with a diagnosis of osteoarthritis, traumatic arthritis, or avascular necrosis", "candidate_expression": "((18-65) AND (Male) AND (Patients willing and able to sign the informed consent) AND (ages) AND (atients able to comply with follow-up requirements including self-evaluations) AND (female) AND (non) AND (pregnant) AND (primary total knee replacement) AND ((avascular necrosis) OR (osteoarthritis) OR (traumatic arthritis)))"}
{"candidate_id": "LLM01245", "doc_id": "NCT01401335_exc", "case_bucket": "or", "source_criterion": "Age less than 15 or greater than 25 and not participating in the day care center", "candidate_expression": "((Age) AND (greater than 25) AND (less than 15) AND (not) AND (participating in the day care center))"}
{"candidate_id": "LLM01246", "doc_id": "NCT02647788_exc", "case_bucket": "or", "source_criterion": "ASA> 3; Coagulopathy; Renal disease, Liver disease, History of recent gastro-intestinal bleeding Pregnancy. Diagnosis of chronic pain currently taking opioid pain medication or with a history of drug abuse. Patients with a self-described allergy to ASA, acetaminophen, NSAIDS and codeine. All patients receiving a brachial plexus block for anesthesia and/or analgesia", "candidate_expression": "((> 3) AND (ASA) AND (Coagulopathy) AND (Liver disease) AND (Pregnancy) AND (Renal disease) AND (allergy) AND (brachial plexus block) AND (gastro-intestinal bleeding) AND (history of) AND (opioid pain medication) AND (recent) AND ((ASA) OR (NSAIDS) OR (acetaminophen) OR (codeine)) AND ((chronic pain) OR (drug abuse)))"}
{"candidate_id": "LLM01247", "doc_id": "NCT02766530_inc", "case_bucket": "other", "source_criterion": "Women aged 25-75 years old. Women with recently diagnosed breast cancer and who will receive NAC to reduce tumor burden before surgery. (including locally advanced breast cancer (LABC) according to clinical assessment; or tumor size > 2cm, that is, at least T2 in TNM staging).", "candidate_expression": "((25-75 years old) AND (NAC) AND (Women) AND (aged) AND (before surgery) AND (breast cancer) AND (reduce tumor burden) AND (surgery))"}
{"candidate_id": "LLM01248", "doc_id": "NCT03221231_exc", "case_bucket": "or", "source_criterion": "Currently dependent on any substance other than cannabis, alcohol or nicotine; History of any major internal disease (including diabetes, cardiovascular disease, lung disease, liver or kidney disease); An active or any history of neurological disorder, including but not limited to seizure disorder, epilepsy, stroke, neurological disease, cognitive impairment, head trauma with prolonged loss of consciousness (>10 minutes), or migraine headaches; An active or a history of a psychiatric disorder including, but not limited to, depression, schizophrenia, bipolar disorder, anxiety, or other psychiatric disorders; Asthma; Known hypersensitivity or allergy to n-acetylcysteine, or receiving chronic therapy with medication that could interact adversely with n-acetylcysteine within 30 days prior to randomization (i.e., nitroglycerin, ACE inhibitors or antihypertensive drugs, anti-coagulants); Exclusion criteria for MRI: having metal in the body and/or having claustrophobia", "candidate_expression": "((>10 minutes) AND (ACE inhibitors) AND (Asthma) AND (Exclusion criteria for MRI) AND (active) AND (alcohol) AND (allergy) AND (anti-coagulants) AND (antihypertensive drugs) AND (anxiety) AND (bipolar disorder) AND (cannabis) AND (cardiovascular disease) AND (chronic therapy) AND (claustrophobia) AND (cognitive impairment) AND (dependent) AND (depression) AND (diabetes) AND (epilepsy) AND (head trauma) AND (history) AND (hypersensitivity) AND (kidney disease) AND (liver disease) AND (lung disease) AND (major internal disease) AND (metal in the body) AND (migraine headaches) AND (n-acetylcysteine) AND (neurological disease) AND (neurological disorder) AND (nicotine) AND (nitroglycerin) AND (other) AND (other than) AND (prolonged loss of consciousness) AND (psychiatric disorder) AND (psychiatric disorders) AND (schizophrenia) AND (seizure disorder) AND (stroke) AND (substance) AND (within 30 days prior to randomization))"}
{"candidate_id": "LLM01249", "doc_id": "NCT02035904_exc", "case_bucket": "or", "source_criterion": "preexisting pectoral, axillar, thoracic homolateral pain habitual opioid consumption; drug-alcoholics addiction ; ICU postoperative recovery; kidney failure (creatinin > 2 g/dl, creatinin <clearance 30 ml/h) and/or hepatic failure (cholinesterase < 2000 UI); cardiac arrhythmias o; Epilepsy; Psychiatric, cognitive disorders, mental retardation; Coagulopathies (INR > 2, activated partial thromboplastin time - aPTT>44 sec); platelet count less than 100.000/mm3; BMI > 30; Allergies to study drugs.", "candidate_expression": "((Allergies) AND (BMI > 30) AND (Coagulopathies) AND (Epilepsy) AND (ICU postoperative recovery) AND (cardiac arrhythmias) AND (cholinesterase < 2000 UI) AND (opioid consumption habitual) AND (platelet count less than 100.000/mm3) AND (study drugs) AND ((creatinin <clearance 30 ml/h) OR (creatinin > 2 g/dl)) AND ((hepatic failure) OR (kidney failure)) AND ((Psychiatric, cognitive disorders) OR (mental retardation)) AND ((INR > 2) OR (activated partial thromboplastin time - aPTT >44 sec)) AND ((axillar pain) OR (pectoral pain) OR (thoracic pain)) AND ((addiction drug) OR (alcoholics addiction)))"}
{"candidate_id": "LLM01250", "doc_id": "NCT02531971_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant, lactating or breast feeding or have a positive serum pregnancy test at enrollment or positive urine pregnancy test on the morning of the first day of any study session Smokers (current use or use over the previous 2 months of nicotine-containing substances, including tobacco products (e.g. cigarettes, cigars, chewing tobacco, gum, patch or electronic cigarettes) Participation in any ongoing investigational drug trial/study or clinical drug trial/study History of chronic obstructive pulmonary disease or cor pulmonale, or substantially decreased respiratory reserve, hypoxia, hypercapnia or pre-existing respiratory depression Active positive Hepatitis B, C and HIV serologies Positive urine drug screening test Use of any prescription medication during the session 0 to 30 days or over-the counter medication e.g. antihistamines or topical corticosteroids (vitamin, herbal supplements and birth control medications not included) during the session 0 to 3 days before entry to the study Use of medications or treatments that would significantly influence or exaggerate responses to the test product or that would alter inflammatory or immune response to the product or agents deemed to be immunosuppressive as determined by physician investigator with 72 hours prior to dosing (e.g. antihistamines, systemic or topical corticosteroids (within 3 weeks prior to dosing), cyclosporine, tacrolimus, cytotoxic drugs, immune globulin, Bacillus Calmette-Guerin (BCG), monoclonal antibodies, radiation therapy) Use of monoamine oxidase inhibitors 21 days prior to study Current use of mixed agonist/antagonist (such as pentazocine, nalbuphine or butorphanol) and partial agonist (buprenorphine) analgesics Current use of anticholinergics or other medications with anticholinergic activity Consumption of beverages containing alcohol, grapefruit juice, Seville oranges, or quinine (e.g. tonic water) or foods containing poppy seeds in the last 72 hours. Donation or loss of greater than one pint of blood within 60 days of entry to the study Any prior serious adverse reaction or hypersensitivity to fentanyl, morphine, codeine, hydrocodone, hydromorphone, oxycodone, oxymorphone, naltrexone or naloxone or any of the inactive ingredients in the TDDS (polyester/ethyl vinyl acetate, polyacrylate adhesive, silicone adhesive, dimethicone NF, or polyolefin) Have a diagnosis of schizophrenia or other major psychiatric diagnosis or mental illness (e.g. major depression) Medical history of personal drug or alcohol addiction or abuse Any condition that would, in the opinion of the MAI, place the subject at an unacceptable risk of injury or render the subject unable to meet the requirements of the protocol Inability to communicate or cooperate with the investigators Subject has an obvious difference in skin color between arms or the presence of a skin condition, excessive hair at the application site (upper arm), sunburn, raised moles and scars, open sore, scar tissue, tattoo, or coloration that would interfere with placement of test articles, skin assessment, or reactions to drug Failure to pass opioid dependence challenge test on the first day study day of any study session (i.e., before taking the first dose of naltrexone hydrochloride). Each subject will be injected subcutaneously with naloxone hydrochloride (0.8 mg injection) and will be observed for 45 minutes for signs and symptoms of opioid withdrawal. Within 4 weeks prior to dosing, use of medications or treatments that would significantly influence or exaggerate responses to the test product or that would alter inflammatory or immune response to the product or agents deemed to be immunosuppressive as determined by physician investigator", "candidate_expression": "((HIV serologies) AND (Hepatitis B serologies) AND (Hepatitis C serologies) AND (Inability to communicate or cooperate with the investigators) AND (Participation in any ongoing investigational drug trial/study or clinical drug trial/study) AND (Smokers) AND (TDDS) AND (Women who are pregnant, lactating or breast feeding or have a positive serum pregnancy test at enrollment or positive urine pregnancy test on the morning of the first day of any study session) AND (abuse) AND (addiction drug alcohol) AND (anticholinergics) AND (buprenorphine) AND (butorphanol) AND (chronic obstructive pulmonary disease) AND (codeine) AND (cor pulmonale,) AND (decreased respiratory reserve) AND (dimethicone NF) AND (fentanyl) AND (hydrocodone) AND (hydromorphone) AND (hypercapnia) AND (hypersensitivity) AND (hypoxia) AND (major depression) AND (major psychiatric diagnosis) AND (mental illness) AND (monoamine oxidase inhibitors 21 days prior to study) AND (morphine) AND (nalbuphine) AND (naloxone) AND (naltrexone) AND (oxycodone) AND (oxymorphone) AND (pentazocine) AND (polyacrylate adhesive) AND (polyester/ethyl vinyl acetate) AND (polyolefin) AND (respiratory depression) AND (schizophrenia) AND (silicone adhesive) AND (urine drug screening test Positive))"}
```
