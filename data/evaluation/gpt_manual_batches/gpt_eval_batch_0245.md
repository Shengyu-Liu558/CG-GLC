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
{"candidate_id": "LLM06101", "doc_id": "NCT02323399_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06102", "doc_id": "NCT03212352_exc", "case_bucket": "or", "source_criterion": "Patient does not meet inclusion criteria, discovered after randomization Inability to give informed consent Known clotting disorder or use of anticoagulants Known risk factors for, or presence of, a cardiovascular disease Language barrier", "candidate_expression": "((Inability to give informed consent) AND (Patient does not meet inclusion criteria, discovered after randomization) AND (anticoagulants) AND (cardiovascular disease) AND (clotting disorder) AND (risk factors cardiovascular disease))"}
{"candidate_id": "LLM06103", "doc_id": "NCT00324363_exc", "case_bucket": "or", "source_criterion": "Have participated in this study previously, or any other study using exenatide or GLP-1 analogs. Have participated in an interventional, medical, surgical, or pharmaceutical study within 30 days of screening. Have characteristics contraindicating metformin or sulfonylurea use. Have been treated with exogenous insulin for more than 1 week within the 3 months prior to screening. Have used drugs for weight loss within 1 month of screening.", "candidate_expression": "((characteristics contraindicating) AND (drugs for weight loss within 1 month of screening) AND (exogenous insulin for more than 1 week within the 3 months prior to screening) AND ((GLP-1 analogs) OR (exenatide)) AND ((metformin) OR (sulfonylurea)) AND ((any other study) OR (this study)) AND ((interventional study) OR (medical study) OR (pharmaceutical study) OR (surgical study)))"}
{"candidate_id": "LLM06104", "doc_id": "NCT02789111_inc", "case_bucket": "other", "source_criterion": "Major spine surgery scheduled as part of clinical care 18-80 years", "candidate_expression": "((18-80) AND (Major spine surgery) AND (years))"}
{"candidate_id": "LLM06105", "doc_id": "NCT02579733_inc", "case_bucket": "other", "source_criterion": "Ulcerative colitis patients with moderate to severe activity who achieved a clinical remission by the first course of corticosteroids Newly diagnosed or without steroid use during last 1 year Endoscopic Mayo subscore >0", "candidate_expression": "((>0) AND (Endoscopic Mayo subscore) AND (Ulcerative colitis) AND (by the first course of corticosteroids) AND (clinical remission) AND (corticosteroids) AND (during last 1 year) AND (first course) AND (first course of corticosteroids) AND (moderate to severe) AND (steroid) AND (without))"}
{"candidate_id": "LLM06106", "doc_id": "NCT02340169_inc", "case_bucket": "or", "source_criterion": "Patients aged 7 years and older must have provided written assent accompanied by written informed consent from patient's representative Clinical diagnosis of stable plaque psoriasis with involvement of = 10% body surface area (excluding face and scalp) Physicians Global Assessment score of 3 or 4 at baseline", "candidate_expression": "((Physicians Global Assessment score at baseline 3 4) AND (aged 7 years and older) AND (body surface area = 10%) AND (face) AND (must have provided written assent accompanied by written informed consent from patient's representative) AND (plaque psoriasis stable) AND (scalp))"}
{"candidate_id": "LLM06107", "doc_id": "NCT02413970_inc", "case_bucket": "or", "source_criterion": "Likely suffer moderate-to-severe OSA based on history and physical or have an established diagnosis of OSA (20=AHI=65) based on a prior in-lab Polysomnography Documentation the subject not effectively treated with CPAP therapy. (Examples include non-compliance, discomfort, undesirable side effects, symptoms persist despite use). Subjects who have been prescribed, but refuse to try CPAP would be considered intolerant. Age 22 or above Willing and capable to have stimulation hardware permanently implanted, and to use the patient remote to activate the stimulation Willing and capable to return for all follow-up visits and conduct sleep studies at home, including the evaluation procedures and filling out questionnaires Willing and capable of providing informed consent", "candidate_expression": "((AHI 20 =65) AND (Age 22 or above) AND (OSA) AND (OSA moderate severe) AND (Willing and capable of providing informed consent) AND (Willing and capable to have stimulation hardware permanently implanted, and to use the patient remote to activate the stimulation) AND (Willing and capable to return for all follow-up visits and conduct sleep studies at home, including the evaluation procedures and filling out questionnaires) AND NOT (CPAP therapy))"}
{"candidate_id": "LLM06108", "doc_id": "NCT02590822_exc", "case_bucket": "or", "source_criterion": "• Diabetes duration >12 years Currently taking more than three glucose lowering therapies Weight-loss of >5kg in the preceding 6 months Stage 4 or 5 chronic kidney disease (eGFR< 30ml/min/1.73m2), Current therapy with Insulin, thiazolidinediones, steroids or atypical antipsychotic medication Untreated thyroid disease Known macrovascular disease including coronary artery disease, stroke/TIA or peripheral vascular disease Presence of arrhythmia (including atrial fibrillation, atrial flutter, or 2nd or 3rd degree atrioventricular block) Known heart failure Other clinically relevant heart disease Inability to exercise or undertake a MRP Absolute contraindication to CMR Cardiovascular symptoms (angina, limiting dyspnoea during normal physical activity) Inflammatory condition e.g. Connective tissue disorder, Rheumatoid arthritis", "candidate_expression": "((< 30ml/min/1.73m2) AND (>12 years) AND (>5kg) AND (CMR) AND (Cardiovascular symptoms) AND (Diabetes) AND (Inability) AND (Inflammatory) AND (Stage 4 or 5) AND (Untreated) AND (Weight-loss) AND (arrhythmia) AND (chronic kidney disease) AND (contraindication) AND (eGFR) AND (glucose lowering therapies) AND (heart disease) AND (heart failure) AND (macrovascular disease) AND (more than three) AND (preceding 6 months) AND (thyroid disease) AND ((Insulin) OR (atypical antipsychotic medication) OR (steroids) OR (thiazolidinediones)) AND ((TIA) OR (coronary artery disease) OR (peripheral vascular disease) OR (stroke)) AND ((2nd degree atrioventricular block) OR (3rd degree atrioventricular block) OR (atrial fibrillation) OR (atrial flutter)) AND ((MRP) OR (exercise)) AND ((angina) OR (dyspnoea)) AND ((Connective tissue disorder,) OR (Rheumatoid arthritis)))"}
{"candidate_id": "LLM06109", "doc_id": "NCT02926235_inc", "case_bucket": "other", "source_criterion": "All patients will be undergoing a primary unilateral total knee arthroplasty for a diagnosis of osteoarthritis", "candidate_expression": "((osteoarthritis) AND (unilateral total knee arthroplasty primary))"}
{"candidate_id": "LLM06110", "doc_id": "NCT02109081_inc", "case_bucket": "other", "source_criterion": "patients = 70 years of age, undergoing a noncardiac surgical procedure under general anesthesia, with an anticipated duration of postoperative admission of at least 2 days.", "candidate_expression": "((= 70 years) AND (admission) AND (age) AND (anticipated) AND (at least 2 days) AND (duration of postoperative admission) AND (general anesthesia) AND (noncardiac surgical procedure) AND (postoperative))"}
{"candidate_id": "LLM06111", "doc_id": "NCT03147599_inc", "case_bucket": "other", "source_criterion": "Men 18 years or older ONB within 1 year post-surgery.", "candidate_expression": "((18 years or older 18 years or older) AND (Men) AND (ONB within 1 year post-surgery) AND (surgery))"}
{"candidate_id": "LLM06112", "doc_id": "NCT03011177_inc", "case_bucket": "other", "source_criterion": "Patients who are 19 years or older on screening Patients with type 2 diabetes mellitus Patients with 7.0% = HbA1c = 11.0% at the screening visit Patients with Fasting Plasma Glucose <15mmol/L(270mg/dL) on screening", "candidate_expression": "((19 or older) AND (270mg/dL) AND (7.0% 11.0%) AND (<15mmol/L) AND (Fasting Plasma Glucose) AND (HbA1c) AND (at the screening visit) AND (on screening) AND (screening) AND (type 2 diabetes mellitus) AND (years))"}
{"candidate_id": "LLM06113", "doc_id": "NCT02565277_exc", "case_bucket": "or", "source_criterion": "Have not received influenza vaccination in the past or cannot be vaccinated due to previous severe reaction to influenza vaccine, egg, latex, or thimerosol allergies, or refusal of vaccination Participant has received a community available influenza vaccine within <6 months History of Guillain-Barré syndrome Immunosuppressive disorders or medications (including oral prednisone >10 mg daily, recent chemotherapy treatment) Emergency cases as determined by the investigator or physician", "candidate_expression": "((Guillain-Barré syndrome) AND (Immunosuppressive disorders) AND (Immunosuppressive medications) AND (chemotherapy) AND (influenza vaccine within <6 months) AND (oral prednisone >10 mg daily) AND NOT (influenza vaccination))"}
{"candidate_id": "LLM06114", "doc_id": "NCT02413970_exc", "case_bucket": "or", "source_criterion": "Central + mixed apneas > 25% of the total apnea-hypopnea index (AHI) Any anatomical finding that would compromise the performance of upper airway stimulation, such as the presence of complete concentric collapse of the soft palate Any condition or procedure that has compromised neurological control of the upper airway Patients who are unable or do not have the necessary assistance to operate the patient remote Patients who are pregnant or plan to become pregnant Patients who will require magnetic resonance imaging (MRI) Patients with an implantable device that may be susceptible to unintended interaction with the Inspire system. Body Mass Index (BMI) of > 32 Any chronic medical illness or condition that contraindicates a surgical procedure under general anesthesia, as judged by the clinical study Investigator Has a terminal illness with life expectancy < 12 months Active psychiatric disease (psychotic illness, major depression, or acute anxiety attacks) which prevents subject compliance with the requirements of the investigational study testing Any other reason the investigator deems subject is unfit for participation in the study", "candidate_expression": "((< 12 months) AND (> 25%) AND (> 32) AND (AHI) AND (BMI) AND (Body Mass Index) AND (Central apneas) AND (MRI) AND (Patients who are pregnant or plan to become pregnant) AND (acute anxiety attacks) AND (contraindicates) AND (general anesthesia) AND (life expectancy) AND (magnetic resonance imaging) AND (major depression) AND (mixed apneas) AND (psychiatric disease) AND (psychotic illness) AND (surgical procedure) AND (total apnea-hypopnea index))"}
{"candidate_id": "LLM06115", "doc_id": "NCT00812344_inc", "case_bucket": "other", "source_criterion": "body mass index (BMI) between 19 to 30 kg/m2 and body weight between 50 to 100 kg inclusive", "candidate_expression": "((50 to 100 kg inclusive) AND (between 19 to 30 kg/m2) AND (body mass index (BMI)) AND (body weight))"}
{"candidate_id": "LLM06116", "doc_id": "NCT03171987_exc", "case_bucket": "or", "source_criterion": "Known or suspected serious spinal pathology and spinal implants Lumbar spinal surgery within the preceding six months Serious comorbidities preventing prescription of paracetamol Alternative treatment for low back pain in previous two weeks Chronic neurological lesion Chronic musculoskeletal lesion Active cancer Pregnancy Use of pain medication (except paracetamol) within 3 days Treatment site has active skin lesion or inflammation Known allergy to skin patch", "candidate_expression": "((Active) AND (Alternative) AND (Chronic musculoskeletal lesion) AND (Chronic neurological lesion) AND (Known) AND (Known or suspected) AND (Lumbar spinal surgery) AND (Pregnancy) AND (Serious) AND (active) AND (allergy) AND (cancer) AND (comorbidities) AND (except) AND (in previous two weeks) AND (inflammation) AND (low back pain) AND (pain medication) AND (paracetamol) AND (preventing) AND (serious) AND (skin lesion) AND (skin patch) AND (spinal implants) AND (spinal pathology) AND (suspected) AND (treatment) AND (within 3 days) AND (within the preceding six months))"}
{"candidate_id": "LLM06117", "doc_id": "NCT02420015_exc", "case_bucket": "other", "source_criterion": "Have a history of myocardial infarction in the past 6 months Have a contraindication to NRT with no medical clearance from the primary care provider or study physician Use and unwillingness to stop use of other forms of nicotine such as cigars, pipes, or chewing tobacco Are pregnant Meet criteria for a current manic episode based on structured clinical interview Are currently enrolled in another smoking cessation trial Are currently imprisoned or in psychiatric hospitalization", "candidate_expression": "((Are currently enrolled in another smoking cessation trial) AND (NRT) AND (Use and unwillingness to stop use of other forms of nicotine such as cigars, pipes, or chewing tobacco) AND (contraindication) AND (imprisoned) AND (manic episode) AND (myocardial infarction i) AND (past 6 months) AND (pregnant) AND (psychiatric hospitalization))"}
{"candidate_id": "LLM06118", "doc_id": "NCT01793831_inc", "case_bucket": "or", "source_criterion": "Moderate to severe CD define as HBI score > 4. Montreal classification: no limitation, except age> 6.", "candidate_expression": "((CD) AND (HBI score > 4) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM06119", "doc_id": "NCT03402945_exc", "case_bucket": "or", "source_criterion": "On systemic antibiotics or with an active bacterial infection at the time of surgery Patients previously enrolled in this trial Patients known to be colonized with Methicillin-resistant S. aureus (MRSA)(unethical not to administer glycopeptides), beta-lactam or vancomycin allergy precluding the use of cefazolin or vancomycin, respectively, or to silver precluding the use of Prevena Participation in other studies that may interfere with this trial", "candidate_expression": "((Participation in other studies that may interfere with this trial) AND (allergy) AND (bacterial infection active at the time of surgery) AND (beta-lactam) AND (cefazolin) AND (colonized Methicillin-resistant S. aureus (MRSA)) AND (previously enrolled in this trial) AND (silver) AND (surgery) AND (systemic antibiotics) AND (vancomycin))"}
{"candidate_id": "LLM06120", "doc_id": "NCT01715714_inc", "case_bucket": "or", "source_criterion": "Patients on chronic statin treatment (>30 days) scheduled for isolated CABG, including on- or off-pump or repeat (redo's) revascularisation procedures Stable or unstable angina, including non ST-segment-elevation acute coronary syndrome (NSTE-ACS) Age = 18 years Written informed consent", "candidate_expression": "((Age = 18 years) AND (CABG scheduled isolated) AND (NSTE-ACS) AND (non ST-segment-elevation acute coronary syndrome) AND (revascularisation procedures on- or off-pump or repeat redo's) AND (statin) AND (treatment chronic >30 days) AND ((Stable angina) OR (unstable angina)))"}
{"candidate_id": "LLM06121", "doc_id": "NCT03389061_inc", "case_bucket": "other", "source_criterion": "Patients with SOF/VEL treatment for the treatment of chronic HCV genotype 1 through 6. Patient is at least 18 at the day of screening. Patient is able and willing to sign the Informed Consent Form. Patient is able and willing to follow protocol requirements.", "candidate_expression": "((HCV genotype chronic 1 through 6 at least 18 at the day of screening) AND (Patient is able and willing to follow protocol requirements) AND (Patient is able and willing to sign the Informed Consent Form) AND (SOF/VEL treatment))"}
{"candidate_id": "LLM06122", "doc_id": "NCT00806273_exc", "case_bucket": "other", "source_criterion": "ASA 3+ No current treatment plan at OHSU Severely carious teeth resulting in inability to isolate for procedure Unable to understand or sign consent form", "candidate_expression": "((ASA 3+) AND (OHSU) AND (Unable to understand or sign consent form) AND (carious teeth Severely) AND (inability to isolate for procedure) AND NOT (treatment plan current))"}
{"candidate_id": "LLM06123", "doc_id": "NCT02062489_inc", "case_bucket": "or", "source_criterion": "The patients signed the written informed consent The patients present with operable unilateral invasive breast cancers without distant metastasis(stage I, II, and III) The breast tumor's positive ER/PR rate is <1%, and positive ER-beta1 rate is =10% by IHC. The patients have no history of neoadjuvant hormone therapy. The patients have normal cardiac functions by echocardiography. The patients' ECOG scores are =0-2. Female patient who is = 18yrs, and = 65yrs. The patients are non-pregnant, and disposed to practice contraception during the whole trial. The patients underwent neoadjuvant chemotherapy plus surgery or directly modified radical mastectomy or breast-conserving surgery (plus sentinel lymph node biopsy or axillary lymph node dissection) after diagnosis of breast cancer. The patients underwent chemotherapy, radiation therapy or targeted therapy(herceptin) after surgery according to the 2013 NCCN guideline. The results of patients' blood tests are as follows:", "candidate_expression": "((ECOG scores =0-2) AND (Female = 18yrs = 65yrs) AND (IHC) AND (The patients are non-pregnant, and disposed to practice contraception during the whole trial.) AND (axillary lymph node dissection) AND (breast cancers operable unilateral invasive) AND (breast tumor) AND (breast-conserving surgery) AND (chemotherapy) AND (echocardiography) AND (herceptin) AND (neoadjuvant chemotherapy) AND (normal cardiac functions) AND (positive ER-beta1 rate =10%) AND (positive ER/PR rate <1%) AND (radiation therapy) AND (radical mastectomy directly modified) AND (sentinel lymph node biopsy) AND (stage I, II, and III) AND (surgery) AND (targeted therapy) AND NOT (neoadjuvant hormone therapy) AND NOT (distant metastasis))"}
{"candidate_id": "LLM06124", "doc_id": "NCT03475589_inc", "case_bucket": "or", "source_criterion": "Age of 18 and over, male or female; Patients with histologically confirmed advanced (stage IV) gastric cancer, NSCLC, breast cancer or ovarian cancer, who choose monotherapy of oral vascular targeting drug (apatinib) due to intolerability or inappropriateness of other therapies; Presence of measurable lesions (=10mm on spiral CT scan) subject to RECIST 1.1; Blood pressured controlled at 150/100 mHg following drug administration; An ECOG PS score of between 0 and 1; A life expectancy of at least 3 months; Subjects who volunteer to participate in this study and have signed the Informed Consent Form (ICF), with good compliance with treatment and follow-up.", "candidate_expression": "((150/100 mHg) AND (18 and over) AND (=10mm) AND (Age) AND (Blood pressured) AND (ECOG PS) AND (RECIST 1.1) AND (Subjects who volunteer to participate in this study and have signed the Informed Consent Form (ICF), with good compliance with treatment and follow-up.) AND (advanced) AND (apatinib) AND (at least 3 months) AND (between 0 and 1) AND (controlled) AND (histologically) AND (histologically confirmed) AND (life expectancy) AND (measurable lesions) AND (monotherapy) AND (oral vascular targeting drug) AND (spiral CT scan) AND (stage IV) AND ((NSCLC) OR (breast cancer) OR (gastric cancer) OR (ovarian cancer)) AND ((female) OR (male)))"}
{"candidate_id": "LLM06125", "doc_id": "NCT02531971_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant, lactating or breast feeding or have a positive serum pregnancy test at enrollment or positive urine pregnancy test on the morning of the first day of any study session Smokers (current use or use over the previous 2 months of nicotine-containing substances, including tobacco products (e.g. cigarettes, cigars, chewing tobacco, gum, patch or electronic cigarettes) Participation in any ongoing investigational drug trial/study or clinical drug trial/study History of chronic obstructive pulmonary disease or cor pulmonale, or substantially decreased respiratory reserve, hypoxia, hypercapnia or pre-existing respiratory depression Active positive Hepatitis B, C and HIV serologies Positive urine drug screening test Use of any prescription medication during the session 0 to 30 days or over-the counter medication e.g. antihistamines or topical corticosteroids (vitamin, herbal supplements and birth control medications not included) during the session 0 to 3 days before entry to the study Use of medications or treatments that would significantly influence or exaggerate responses to the test product or that would alter inflammatory or immune response to the product or agents deemed to be immunosuppressive as determined by physician investigator with 72 hours prior to dosing (e.g. antihistamines, systemic or topical corticosteroids (within 3 weeks prior to dosing), cyclosporine, tacrolimus, cytotoxic drugs, immune globulin, Bacillus Calmette-Guerin (BCG), monoclonal antibodies, radiation therapy) Use of monoamine oxidase inhibitors 21 days prior to study Current use of mixed agonist/antagonist (such as pentazocine, nalbuphine or butorphanol) and partial agonist (buprenorphine) analgesics Current use of anticholinergics or other medications with anticholinergic activity Consumption of beverages containing alcohol, grapefruit juice, Seville oranges, or quinine (e.g. tonic water) or foods containing poppy seeds in the last 72 hours. Donation or loss of greater than one pint of blood within 60 days of entry to the study Any prior serious adverse reaction or hypersensitivity to fentanyl, morphine, codeine, hydrocodone, hydromorphone, oxycodone, oxymorphone, naltrexone or naloxone or any of the inactive ingredients in the TDDS (polyester/ethyl vinyl acetate, polyacrylate adhesive, silicone adhesive, dimethicone NF, or polyolefin) Have a diagnosis of schizophrenia or other major psychiatric diagnosis or mental illness (e.g. major depression) Medical history of personal drug or alcohol addiction or abuse Any condition that would, in the opinion of the MAI, place the subject at an unacceptable risk of injury or render the subject unable to meet the requirements of the protocol Inability to communicate or cooperate with the investigators Subject has an obvious difference in skin color between arms or the presence of a skin condition, excessive hair at the application site (upper arm), sunburn, raised moles and scars, open sore, scar tissue, tattoo, or coloration that would interfere with placement of test articles, skin assessment, or reactions to drug Failure to pass opioid dependence challenge test on the first day study day of any study session (i.e., before taking the first dose of naltrexone hydrochloride). Each subject will be injected subcutaneously with naloxone hydrochloride (0.8 mg injection) and will be observed for 45 minutes for signs and symptoms of opioid withdrawal. Within 4 weeks prior to dosing, use of medications or treatments that would significantly influence or exaggerate responses to the test product or that would alter inflammatory or immune response to the product or agents deemed to be immunosuppressive as determined by physician investigator", "candidate_expression": "((Inability to communicate or cooperate with the investigators) AND (Participation in any ongoing investigational drug trial/study or clinical drug trial/study) AND (Smokers) AND (Women who are pregnant, lactating or breast feeding or have a positive serum pregnancy test at enrollment or positive urine pregnancy test on the morning of the first day of any study session) AND (anticholinergics) AND (hypersensitivity) AND (major depression) AND (monoamine oxidase inhibitors 21 days prior to study) AND (urine drug screening test Positive) AND ((HIV serologies) OR (Hepatitis B serologies) OR (Hepatitis C serologies)) AND ((buprenorphine) OR (butorphanol) OR (nalbuphine) OR (pentazocine)) AND ((TDDS) OR (codeine) OR (fentanyl) OR (hydrocodone) OR (hydromorphone) OR (morphine) OR (naloxone) OR (naltrexone) OR (oxycodone) OR (oxymorphone)) AND ((chronic obstructive pulmonary disease) OR (cor pulmonale,) OR (decreased respiratory reserve) OR (hypercapnia) OR (hypoxia) OR (respiratory depression)) AND ((dimethicone NF) OR (polyacrylate adhesive) OR (polyester/ethyl vinyl acetate) OR (polyolefin) OR (silicone adhesive)) AND ((major psychiatric diagnosis) OR (mental illness) OR (schizophrenia)) AND ((abuse) OR (addiction)) AND ((alcohol) OR (drug)))"}
```
