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
{"candidate_id": "LLM04501", "doc_id": "NCT02678728_inc", "case_bucket": "other", "source_criterion": "Patients undergoing thoracic aorta surgery with hypothermic circulatory arrest, over 20-of age", "candidate_expression": "((age over 20) AND (hypothermic circulatory arrest) AND (surgery thoracic aorta))"}
{"candidate_id": "LLM04502", "doc_id": "NCT02893228_inc", "case_bucket": "or", "source_criterion": "Patients undergoing surgery on shoulder, humerus, or clavicle", "candidate_expression": "((clavicle) AND (humerus) AND (shoulder) AND (surgery))"}
{"candidate_id": "LLM04503", "doc_id": "NCT01993836_inc", "case_bucket": "other", "source_criterion": "Surgical patients 60 years of age or older Surgery scheduled to last at least 2 hours (including time for anesthesia induction, etc) English speaking ability. Ability to give informed consent", "candidate_expression": "((60 years or older) AND (Ability to give informed consent) AND (English speaking ability) AND (Surgery) AND (age) AND (scheduled to last at least 2 hours))"}
{"candidate_id": "LLM04504", "doc_id": "NCT03213834_exc", "case_bucket": "or", "source_criterion": "age <18 years; Pregnancy inability to give informed written consent; previous thoracic surgery or thrombolytic therapy for pleural infection; medical thoracoscopy cannot be performed within 48 hours; inability to tolerate procedure due to hemodynamic instability or severe hypoxemia; inability to correct coagulopathy; presence of a homogeneously echogenic effusion on pleural US27 -", "candidate_expression": "((<18 years) AND (Pregnancy) AND (age) AND (cannot) AND (cannot be performed) AND (coagulopathy) AND (correct) AND (hemodynamic instability) AND (homogeneously echogenic effusion) AND (hypoxemia) AND (inability to) AND (inability to give informed written consent;) AND (inability to tolerate) AND (medical thoracoscopy) AND (pleural US) AND (pleural infection) AND (previous) AND (procedure) AND (severe) AND (thoracic surgery) AND (thrombolytic therapy) AND (within 48 hours))"}
{"candidate_id": "LLM04505", "doc_id": "NCT02675153_inc", "case_bucket": "other", "source_criterion": "moderate to severe Crohn's Disease (basic HBI = 7) with stenosis", "candidate_expression": "((= 7) AND (Crohn's Disease) AND (basic HBI) AND (moderate to severe) AND (stenosis))"}
{"candidate_id": "LLM04506", "doc_id": "NCT02961764_exc", "case_bucket": "or", "source_criterion": "Known or suspected gram-negative infections, anaerobic infections, or fungemia Known or suspected infections that are severe, life threatening or are not included in the ABSSSI Food and Drug Administration (FDA) guidance Injection drug users with a fever Severe neurological disorder leading to immobility or confined to a wheelchair Bilateral Lower extremity involvement of the suspected infection.", "candidate_expression": "((drug users) AND (fever) AND (infection Bilateral Lower extremity) AND (infections severe life threatening) AND (neurological disorder Severe) AND ((immobility) OR (wheelchair)) AND ((fungemia) OR (infections anaerobic) OR (infections gram-negative)))"}
{"candidate_id": "LLM04507", "doc_id": "NCT00455663_exc", "case_bucket": "or", "source_criterion": "History of significant head trauma, seizure disorder, or mental retardation History of alcohol or drug abuse or dependence within 1 month prior to study entry History of violence within 6 months prior to study entry", "candidate_expression": "((History) AND (abuse alcohol) AND (dependence alcohol) AND (dependence drug) AND (drug abuse) AND (head trauma) AND (mental retardation) AND (seizure disorder) AND (violence) AND (within 1 month prior) AND (within 6 months prior))"}
{"candidate_id": "LLM04508", "doc_id": "NCT01943812_inc", "case_bucket": "or", "source_criterion": "Endometrial thickness = 7 mm after stimulation 18-45 years IVF/ICSI fertilisation BMI > 18,5 <30 kg/m2 cycle length 25-34 days", "candidate_expression": "((BMI > 18,5 <30 kg/m2) AND (Endometrial thickness = 7 mm after stimulation) AND (ICSI fertilisation) AND (IVF fertilisation) AND (cycle length 25-34 days) AND (stimulation stimulation) AND (years 18-45))"}
{"candidate_id": "LLM04509", "doc_id": "NCT02952365_inc", "case_bucket": "other", "source_criterion": "Subjects age 21 and older Subjects with healthy eyes Subjects who have previously undergone LASIK surgery Subjects with residual refractive error.", "candidate_expression": "((LASIK surgery previously) AND (age 21 and older) AND (healthy eyes) AND (residual refractive error))"}
{"candidate_id": "LLM04510", "doc_id": "NCT02961764_exc", "case_bucket": "or", "source_criterion": "Known or suspected gram-negative infections, anaerobic infections, or fungemia Known or suspected infections that are severe, life threatening or are not included in the ABSSSI Food and Drug Administration (FDA) guidance Injection drug users with a fever Severe neurological disorder leading to immobility or confined to a wheelchair Bilateral Lower extremity involvement of the suspected infection.", "candidate_expression": "((drug users) AND (fever) AND (fungemia) AND (immobility) AND (infection Bilateral Lower extremity) AND (infections anaerobic) AND (infections gram-negative) AND (infections severe life threatening) AND (neurological disorder Severe) AND (wheelchair))"}
{"candidate_id": "LLM04511", "doc_id": "NCT03335904_inc", "case_bucket": "or", "source_criterion": "normotensive forced expiratory volume in 1s : forced vital capacity ratio > 0.75 no medical history of cardiovascular and respiratory disease not taking medications other than oral contraceptives free from sleep apnea body mass index less than 30 kg/m2", "candidate_expression": "((body mass index less than 30 kg/m2) AND (cardiovascular disease) AND (forced expiratory volume in 1s : forced vital capacity ratio > 0.75) AND (medications) AND (normotensive) AND (respiratory disease) AND NOT (oral contraceptives) AND NOT (sleep apnea))"}
{"candidate_id": "LLM04512", "doc_id": "NCT03182114_inc", "case_bucket": "other", "source_criterion": "full term singleton pregnant women scheduled for elective cesarean delivery", "candidate_expression": "((cesarean delivery scheduled for elective) AND (full term singleton) AND (pregnant) AND (women))"}
{"candidate_id": "LLM04513", "doc_id": "NCT00806273_inc", "case_bucket": "other", "source_criterion": "ASA 1 ASA 2 Pts have current treatment plan at OHSU for extraction of some or all of remaining teeth and scheduled for delivery of a removable appliance post extraction Teeth used are able to be isolated with rubber dam Understand and sign consent form", "candidate_expression": "((ASA 1) AND (ASA 2) AND (Understand and sign consent form) AND (treatment plan at OHSU scheduled for))"}
{"candidate_id": "LLM04514", "doc_id": "NCT02396420_inc", "case_bucket": "or", "source_criterion": "Patient has provided signed informed consent Patient is aged greater than or equal to 40 and less than or equal to 89 years of age Patient has a prostate size between 90g and 200g, as determined by MRI Patient has experienced lower urinary tract symptoms (LUTS) for at least 6 months prior to study enrollment Patient has an IPSS score of at least 13 at baseline Patient is either: refractory to medical treatment, contraindicated to medical treatment, OR refuses medical treatment Patient either: refuses surgical treatment OR is contraindicated for surgical treatment Patient meets ONE of the following criteria: baseline PSA < 4.0ng/mL (no prostate biopsy required) OR baseline PSA >/= 4 ng/mL AND a negative prostate biopsy (minimum 12 core biopsy) within the prior 12 months", "candidate_expression": "((IPSS score at least 13 at baseline) AND (MRI) AND (PSA baseline < 4.0ng/mL) AND (PSA baseline >/= 4 ng/mL) AND (aged greater than or equal to 40 less than or equal to 89 years) AND (core biopsy minimum 12) AND (lower urinary tract symptoms (LUTS) at least 6 months prior to study enrollment) AND (prostate biopsy negative) AND (prostate size between 90g and 200g) AND (signed informed consent) AND ((contraindicated to medical treatment) OR (refractory to medical treatment) OR (refuses medical treatment)) AND ((contraindicated for surgical treatment) OR (refuses surgical treatment)))"}
{"candidate_id": "LLM04515", "doc_id": "NCT03539718_exc", "case_bucket": "other", "source_criterion": "Patients with intercurrent infections. Patients with sepsis. Patients receiving drugs affecting immune system like immunosuppressive drugs. Patients on antibiotics.", "candidate_expression": "((antibiotics) AND (drugs affecting immune system) AND (immunosuppressive drugs) AND (intercurrent infections) AND (sepsis))"}
{"candidate_id": "LLM04516", "doc_id": "NCT03225469_inc", "case_bucket": "other", "source_criterion": "1. Individuals scheduled for undergoing colonoscopy at the Endoscopy Center of Wuxi people's Hospital in China 2. Greater than the age of 18 3. Individuals living with other family members 4. Outpatients", "candidate_expression": "((Endoscopy Center of Wuxi people's Hospital in China) AND (Greater than 18) AND (Outpatients) AND (age) AND (colonoscopy))"}
{"candidate_id": "LLM04517", "doc_id": "NCT02344888_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Body mass index (BMI) < 18.5 kg/m2 or > 25 kg/m2. Presence of any infertility factor other than anovulatory PCOS. Previous history of ovarian surgery or surgical removal of one ovary. Previous exposure to cytotoxic drugs or pelvic irradiation. Oral hypoglycemic or hormonal therapy either currently or in the preceding 3 months. Metabolic or hormonal abnormalities", "candidate_expression": "((< 18.5 kg/m2 or > 25 kg/m2) AND (< 20 or > 35 years) AND (Age) AND (BMI) AND (Body mass index) AND (Oral) AND (anovulatory PCOS) AND (exposure) AND (infertility factor) AND (one) AND (other than) AND (ovary) AND (preceding 3 months) AND ((cytotoxic drugs) OR (pelvic irradiation)) AND ((hormonal therapy) OR (hypoglycemic therapy)) AND ((Metabolic abnormalities) OR (hormonal abnormalities)) AND ((ovarian surgery) OR (surgical removal)))"}
{"candidate_id": "LLM04518", "doc_id": "NCT03339284_inc", "case_bucket": "other", "source_criterion": "patients with renal cancer coming to the laparoscopic radical nephrectomy", "candidate_expression": "((radical nephrectomy laparoscopic) AND (renal cancer))"}
{"candidate_id": "LLM04519", "doc_id": "NCT03177811_exc", "case_bucket": "or", "source_criterion": "COPD exacerbation, very severe COPD with hypoxemia at low altitude (FEV1/FVC <0.7, FEV1 <40% predicted, oxygen saturation on room air <92% at 750 m). Comorbidities such as uncontrolled cardiovascular disease, i.e., unstable systemic arterial hypertension, coronary artery disease; previous stroke; OSA; pneumothorax in the last 2 months. Internal, neurologic, rheumatologic or psychiatric disease including current heavy smoking (>20 cigarettes per day) Known renal failure or allergy to acetazolamide and other sulfonamides", "candidate_expression": "((<0.7) AND (<40% predicted) AND (<92% at 750 m) AND (>20 cigarettes per day) AND (COPD) AND (COPD exacerbation) AND (Comorbidities) AND (FEV1) AND (FEV1/FVC) AND (Internal disease) AND (OSA) AND (acetazolamide) AND (allergy) AND (cardiovascular disease) AND (coronary artery disease) AND (heavy smoking) AND (hypoxemia) AND (in the last 2 months) AND (low altitude) AND (neurologic disease) AND (oxygen saturation) AND (pneumothorax) AND (previous) AND (psychiatric disease) AND (renal failure) AND (rheumatologic disease) AND (room air) AND (stroke) AND (sulfonamides) AND (systemic arterial hypertension) AND (uncontrolled) AND (unstable) AND (very severe))"}
{"candidate_id": "LLM04520", "doc_id": "NCT02243553_inc", "case_bucket": "other", "source_criterion": "1. Signed informed consent 2. Healthy subjects aged between 18 years and 45 years inclusive 3. Weighing at least 50 kg 4. Volunteers must be hospitalized on Days 1-4, 7-9, and 17-20 for pharmacokinetic assessments for each biomarker and TPV/r (Days 7-9 and 17-20) 5. Volunteers must be willing to complete all study-related activities 6. Each volunteer must have a valid social security number 7. Each volunteer must have acceptable medical history, physical examination and laboratory test", "candidate_expression": "((Each volunteer must have a valid social security number) AND (Each volunteer must have acceptable medical history, physical examination and laboratory test) AND (Healthy) AND (Signed informed consent) AND (Volunteers must be hospitalized on Days 1-4, 7-9, and 17-20 for pharmacokinetic assessments for each biomarker and TPV/r (Days 7-9 and 17-20)) AND (Volunteers must be willing to complete all study-related activities) AND (Weighing) AND (aged) AND (at least 50 kg) AND (between 18 years and 45 years inclusive) AND (laboratory test) AND (medical history) AND (physical examination))"}
{"candidate_id": "LLM04521", "doc_id": "NCT02632318_exc", "case_bucket": "other", "source_criterion": "Regular cigarette smoker Alcohol abuse Drug abuse", "candidate_expression": "((Alcohol abuse) AND (Drug abuse) AND (Regular cigarette smoker))"}
{"candidate_id": "LLM04522", "doc_id": "NCT03004261_exc", "case_bucket": "or", "source_criterion": "Patients receiving prednisone = 1mg/kg/d for the treatment of acute GVHD or mild, severe chronic GVHD. Recipient < 14years of age Donor is sero-positive in HBV/HCV/HIV or RPR.", "candidate_expression": "((GVHD chronic) AND (acute GVHD mild severe) AND (age < 14years) AND (prednisone = 1mg/kg/d) AND (sero-positive in HBV) AND (sero-positive in HCV) AND (sero-positive in HIV) AND (sero-positive in RPR))"}
{"candidate_id": "LLM04523", "doc_id": "NCT03351608_inc", "case_bucket": "or", "source_criterion": "Be categorized as American Society of Anesthesiologists (ASA) Physical Status Class 1, 2, or 3. Have a planned non-emergent surgical procedure or clinical situation (e.g., intubation) that requires moderate or deep NMB with either rocuronium or vecuronium. Have a planned surgical procedure or clinical situation that would allow objective neuromuscular monitoring techniques to be applied with access to the arm for neuromuscular transmission monitoring. Age between 2 to <17 years at Visit 2. If female, may participate if she is not pregnant, not breastfeeding, and at least one of the following: 1) Not a woman of childbearing potential (WOCBP); or 2) A WOCBP who agrees to follow the study contraceptive guidance during the treatment period and for at least 7 days after the last dose of study treatment.", "candidate_expression": "((Age between 2 to <17 years at Visit 2) AND (American Society of Anesthesiologists (ASA) Physical Status Class 1 2 3) AND (NMB deep) AND (WOCBP) AND (clinical situation) AND (contraceptive guidance during the treatment period for at least 7 days after the last dose of study treatment) AND (female) AND (intubation moderate) AND (objective neuromuscular monitoring techniques) AND (rocuronium) AND (surgical procedure planned) AND (surgical procedure planned non-emergent) AND (vecuronium) AND NOT (pregnant) AND NOT (breastfeeding) AND NOT (woman of childbearing potential (WOCBP)))"}
{"candidate_id": "LLM04524", "doc_id": "NCT02620904_inc", "case_bucket": "other", "source_criterion": "Intrauterine fetal death as confirmed by absence of cardiac motion on ultrasound by Attending physician at the time of admission to the hospital. Estimated gestational age greater than 20 weeks Hemodynamically stable and appropriate for induction of labor as per primary clinical health team in house Women with one prior low transverse cesarean delivery", "candidate_expression": "((Estimated gestational age) AND (Hemodynamically stable) AND (Intrauterine fetal death) AND (Women) AND (absence of cardiac motion) AND (admission to the hospital) AND (at the time of admission to the hospital) AND (greater than 20 weeks) AND (induction of labor) AND (low transverse cesarean delivery) AND (one) AND (ultrasound))"}
{"candidate_id": "LLM04525", "doc_id": "NCT02429583_exc", "case_bucket": "or", "source_criterion": "Received any vaccine within a month prior to study vaccine Positive serum antibody against Hep B surface antigen and/or core Hep B core antigen HIV positive For HCV-negative, healthy volunteers: History of HCV infection or positive HCV antibody test Participation in another clinical study of an investigational product currently or within the past 90 days, or expected participation during this study In the opinion of the investigator, the volunteer is unlikely to comply with the study protocol Any clinically significant abnormality or medical history or physical examination including history of immunodeficiency or autoimmune disease (in addition to HCV infection, for HCV group) Currently taking systemic steroids or other immunomodulatory medications including anticancer medications and antiviral medications Any clinically significant acute or chronic medical condition requiring care by a primary care provider (e.g., diabetes, coronary artery disease, rheumatologic illness, malignancy, substance abuse) that, in the opinion of the investigator, would preclude participation Unable to continue participation for 156 weeks History of previous Hepatitis B vaccination(s) Male or female < 18 and > 62 years of age Is pregnant or lactating History of Hepatitis B infection Clinical, laboratory, or biopsy evidence of cirrhosis", "candidate_expression": "((HCV negative) AND (HIV positive core Hep B core antigen) AND (Hepatitis B infection) AND (Hepatitis B vaccination) AND (History of HCV infection) AND (In the opinion of the investigator, the volunteer is unlikely to comply with the study protocol) AND (Is pregnant or lactating) AND (Male) AND (Participation in another clinical study of an investigational product currently or within the past 90 days, or expected participation during this study) AND (Unable to continue participation for 156 weeks) AND (age < 18 and > 62 years) AND (anticancer medications) AND (antiviral medications) AND (autoimmune disease) AND (cirrhosis) AND (coronary artery disease) AND (diabetes) AND (female) AND (immunodeficiency) AND (immunomodulatory medications) AND (malignancy) AND (rheumatologic illness) AND (serum antibody Positive Hep B surface antige) AND (substance abuse) AND (systemic steroids) AND (vaccine within a month prior to study vaccine) AND NOT (HCV infection))"}
```
