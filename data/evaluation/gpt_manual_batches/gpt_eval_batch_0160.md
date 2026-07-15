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
{"candidate_id": "LLM03976", "doc_id": "NCT01997112_exc", "case_bucket": "or", "source_criterion": "History of ischaemic heart disease, cardiac failure, cerebrovascular disease, liver impairment (ALT/AST>50IU/L) or stage 3-5 chronic kidney disease. History of overdose or suicidal ideation Patients weighing <55kgs. Patients with chronic pain requiring treatment, with a known allergy to paracetamol, or concomitant use of non-steroidal anti-inflammatories , oral anticoagulants or corticosteroids.", "candidate_expression": "((chronic kidney disease) AND (chronic pain requiring treatment) AND (known allergy) AND (paracetamol) AND (weighing <55kgs) AND ((overdose) OR (suicidal ideation)) AND ((cardiac failure) OR (cerebrovascular disease) OR (ischaemic heart disease) OR (liver impairment) OR (stage 3-5)) AND ((corticosteroids) OR (non-steroidal anti-inflammatories) OR (oral anticoagulants)) AND ((ALT >50IU/L) OR (AST >50IU/L)))"}
{"candidate_id": "LLM03977", "doc_id": "NCT00749112_exc", "case_bucket": "or", "source_criterion": "Current viral or bacterial infection. Positive serology for HIV, HCV, HBV.", "candidate_expression": "(((bacterial infection) OR (infection viral)) AND ((serology for HBV) OR (serology for HCV) OR (serology for HIV)))"}
{"candidate_id": "LLM03978", "doc_id": "NCT02429583_exc", "case_bucket": "or", "source_criterion": "Received any vaccine within a month prior to study vaccine Positive serum antibody against Hep B surface antigen and/or core Hep B core antigen HIV positive For HCV-negative, healthy volunteers: History of HCV infection or positive HCV antibody test Participation in another clinical study of an investigational product currently or within the past 90 days, or expected participation during this study In the opinion of the investigator, the volunteer is unlikely to comply with the study protocol Any clinically significant abnormality or medical history or physical examination including history of immunodeficiency or autoimmune disease (in addition to HCV infection, for HCV group) Currently taking systemic steroids or other immunomodulatory medications including anticancer medications and antiviral medications Any clinically significant acute or chronic medical condition requiring care by a primary care provider (e.g., diabetes, coronary artery disease, rheumatologic illness, malignancy, substance abuse) that, in the opinion of the investigator, would preclude participation Unable to continue participation for 156 weeks History of previous Hepatitis B vaccination(s) Male or female < 18 and > 62 years of age Is pregnant or lactating History of Hepatitis B infection Clinical, laboratory, or biopsy evidence of cirrhosis", "candidate_expression": "((< 18 and > 62 years) AND (HCV) AND (HCV infection) AND (HIV) AND (Hep B surface antige) AND (Hepatitis B infection) AND (Hepatitis B vaccination) AND (History of HCV infection) AND (In the opinion of the investigator, the volunteer is unlikely to comply with the study protocol) AND (Is pregnant or lactating) AND (Male) AND (Participation in another clinical study of an investigational product currently or within the past 90 days, or expected participation during this study) AND (Positive) AND (Unable to continue participation for 156 weeks) AND (age) AND (anticancer medications) AND (antiviral medications) AND (autoimmune disease) AND (cirrhosis) AND (core Hep B core antigen) AND (coronary artery disease) AND (diabetes) AND (female) AND (immunodeficiency) AND (immunomodulatory medications) AND (in addition to) AND (malignancy) AND (negative) AND (positive) AND (rheumatologic illness) AND (serum antibody) AND (study vaccine) AND (substance abuse) AND (systemic steroids) AND (vaccine) AND (within a month prior to study vaccine))"}
{"candidate_id": "LLM03979", "doc_id": "NCT02015923_inc", "case_bucket": "or", "source_criterion": "colorectal cancer above to 12 cm from the anal verge unresectable synchronous metastases no contraindications for chemotherapy absence of peritoneal carcinomatosis, central nervous system o bone metastasis. performance status ECOG = 2 (Eastern Cooperative Oncology Group) uncontrolled concomitant medical conditions that may compromise to chemotherapy significant symptomatic cardiac disease not pregnancy or breastfeeding", "candidate_expression": "((ECOG = 2) AND (Eastern Cooperative Oncology Group) AND (bone metastasis) AND (breastfeeding) AND (cardiac disease significant symptomatic) AND (central nervous system metastasis) AND (chemotherapy) AND (colorectal cancer above to 12 cm from the anal verge) AND (medical conditions that may compromise to chemotherapy uncontrolled concomitant) AND (metastases unresectable synchronous) AND (performance status) AND (peritoneal carcinomatosis) AND (pregnancy) AND NOT (contraindications))"}
{"candidate_id": "LLM03980", "doc_id": "NCT02526823_exc", "case_bucket": "or", "source_criterion": "Patients with severe complications or severe infection; Invasion of central nervous system; Patients with severe heart disease history, including ventricular tachycardia (VT), atrial fibrillation (AF), heart block, myocardial infarction (MI), congestive heart failure (CHF), coronary heart disease patients needed therapy; patients with severe allergic constitution, or those who are allergic to or intolerant of drug composition in chemotherapy regimens; with other malignant tumors in the past 5 years; patients received doxorubicin therapy, total cumulative dose of adriamycin was more than 300 mg/m2, total cumulative dose of epirubicin was more than 450 mg/m2; Patients participate in other clinical studies; Other patients who are not suitable for the study.", "candidate_expression": "((AF) AND (CHF) AND (Invasion) AND (MI) AND (Patients) AND (Patients participate in other clinical studies) AND (VT) AND (adriamycin) AND (allergic) AND (atrial fibrillation) AND (central nervous system) AND (chemotherapy regimens) AND (complications) AND (congestive heart failure) AND (coronary heart disease) AND (doxorubicin) AND (epirubicin) AND (heart block) AND (heart disease) AND (infection) AND (intolerant) AND (malignant tumors) AND (more than 300 mg/m2) AND (more than 450 mg/m2) AND (myocardial infarction) AND (other) AND (past 5 years) AND (severe) AND (total cumulative dose) AND (ventricular tachycardia))"}
{"candidate_id": "LLM03981", "doc_id": "NCT02509091_exc", "case_bucket": "or", "source_criterion": "Active bleeding without control; Receiving nasal or facial surgery recently; With severe cardio-pulmonary dysfunction, such as left heart failure, unstable arrhythmia, etc. With other respiratory diseases: such as active pulmonary tuberculosis, non-tuberculosis mycobacteria (NTM) pulmonary disease, pulmonary aspergillosis, etc. Be allergic to amikacin", "candidate_expression": "((Active) AND (NTM) AND (active) AND (allergic) AND (amikacin) AND (arrhythmia) AND (bleeding) AND (cardio-pulmonary dysfunction) AND (facial surgery) AND (left heart failure) AND (nasal surgery) AND (non-tuberculosis mycobacteria pulmonary disease) AND (pulmonary aspergillosis) AND (pulmonary tuberculosis) AND (respiratory diseases) AND (severe) AND (unstable))"}
{"candidate_id": "LLM03982", "doc_id": "NCT03080493_inc", "case_bucket": "other", "source_criterion": "15 weeks 0 days gestational age - 23 weeks 5 days gestational age at time of dilator insertion Able to read and write in English Active cell phone with text messaging capability Ride home from dilator insertion clinic appointment", "candidate_expression": "((Able to read and write in English) AND (Active cell phone with text messaging capability) AND (Ride home) AND (dilator insertion) AND (gestational age 15 weeks 0 days - 23 weeks 5 days at time of dilator insertion))"}
{"candidate_id": "LLM03983", "doc_id": "NCT02668016_inc", "case_bucket": "or", "source_criterion": "Aged 18 years or older Previously taken one or more statins Withdrawn from statins because of perceived side effects Developed side effects within 2 weeks of initiation Clinical indication for statins for primary or secondary prevention of cardiovascular disease or dyslipidaemia, on either no medication or non-statin lipid lowering therapy (e.g, ezetimibe)", "candidate_expression": "((Aged 18 years or older) AND (dyslipidaemia) AND (indication) AND (prevention of cardiovascular disease) AND (side effects within 2 weeks of initiation) AND (statins one or more) AND (statins primary secondary))"}
{"candidate_id": "LLM03984", "doc_id": "NCT02242188_inc", "case_bucket": "or", "source_criterion": "Term singleton infants (>37 weeks gestational age) Birth weight > 2500g Healthy at inclusion Breastfed exclusively or predominantly (>50% meals) at inclusion No previous iron supplementation No previous blood transfusion Informed consent given", "candidate_expression": "((> 2500g) AND (>37 weeks) AND (>50% meals) AND (Birth weight) AND (Breastfed) AND (Healthy) AND (Informed consent given) AND (No) AND (Term infants) AND (at inclusion) AND (blood transfusion) AND (exclusively) AND (gestational age) AND (iron supplementation) AND (predominantly) AND (previous) AND (singleton infants))"}
{"candidate_id": "LLM03985", "doc_id": "NCT03221231_inc", "case_bucket": "other", "source_criterion": "Current DSM-IV diagnosis of cannabis dependence, >1 week detoxified and abstinent; Able to provide written informed consent and to comply with study procedures. Dutch speaking (Dutch as primary language).", "candidate_expression": "((abstinent) AND (cannabis dependence DSM-IV) AND (detoxified))"}
{"candidate_id": "LLM03986", "doc_id": "NCT03016741_exc", "case_bucket": "or", "source_criterion": "Prior treatment with enzalutamide or abiraterone acetate for > 14 days prior to enrollment and completion of baseline tests. Receipt of chemotherapy for prostate or other cancer within the past 12 months with residual cognitive deficits, or receipt of chemotherapy for mCRPC. Patients/physicians planning treatment with chemotherapy during the 12 month period of the investigation are also ineligible. History of cognitive impairment or dysfunction, including a history of dementia, Alzheimer's disease, stroke with residual cognitive deficits, cognitive dysfunction related to alcohol or substance abuse, or cognitive dysfunction related to prior treatment for any cancer. Patients with a seizure history, history of recurrent falls, or known brain metastases are excluded from this clinical trial because of their poor prognosis and because of their heightened risk of seizure or progressive cognitive and/or neurologic dysfunction that would confound the evaluation. Uncontrolled intercurrent illness including, but not limited to, uncontrolled diabetes, ongoing or active infection, symptomatic congestive heart failure (New York Heart Association Class III and IV heart failure), unstable angina pectoris, cardiac arrhythmia, or psychiatric illness/social situations/substance abuse that would limit compliance with study requirements. Patients with a \"currently active\" second malignancy other than non-melanoma skin cancers are not eligible. Patients are not considered to have a \"currently active\" malignancy if they have completed all therapy and are now considered without evidence of disease for 1 year. Patients with cognitive dysfunction related to treatment of another malignancy, including a history of \"chemo-brain\", are ineligible. Patients taking psychotropic medications or illicit drugs that may alter cognition, concentration, or behavior. Appropriate treatment by a licensed provider with medications for depression or anxiety, including but not limited to SSRIs, SNRIs, and standard dose benzodiazepines at a stable dose, is permitted", "candidate_expression": "((New York Heart Association Class III and IV) AND (cancer any) AND (congestive heart failure symptomatic) AND (heart failure) AND (intercurrent illness Uncontrolled) AND (mCRPC) AND (malignancy another) AND (residual cognitive deficits) AND (treatment) AND (treatment for > 14 days prior to enrollment) AND (treatment prior) AND NOT (non-melanoma skin cancers) AND ((cancer other) OR (prostate cancer)) AND ((chemotherapy) OR (chemotherapy within the past 12 months)) AND ((cognitive dysfunction) OR (cognitive impairment)) AND ((abiraterone acetate) OR (enzalutamide)) AND ((Alzheimer's disease) OR (alcohol abuse) OR (cognitive dysfunction) OR (dementia) OR (stroke) OR (substance abuse)) AND ((brain metastases) OR (recurrent falls history of) OR (seizure history)) AND ((active) OR (ongoing)) AND ((cardiac arrhythmia) OR (diabetes uncontrolled) OR (infection) OR (psychiatric illness) OR (social situations) OR (substance abuse) OR (unstable angina pectoris)) AND ((cognitive dysfunction) OR (malignancy currently active second)) AND ((illicit drugs) OR (psychotropic medications)) AND ((alter behavior) OR (alter cognition) OR (alter concentration)))"}
{"candidate_id": "LLM03987", "doc_id": "NCT03434951_exc", "case_bucket": "or", "source_criterion": "rearthroplasty ASA IV-V inadequate spoken finnish for reliable pain assessment Dementia or otherwise impaired cognition contraindication for any medication or substance used in survey protocol weight <50kg or BMI =35 kg/m2 preoperative SpO2 less than 93% clinical suspicion that subject can not use PCA adequately history of substance abuse or current excessive use of alcohol preoperative use of either pregabalin, gabapentin or strong opiates", "candidate_expression": "((<50kg) AND (=35 kg/m2) AND (ASA) AND (BMI) AND (Dementia) AND (IV-V) AND (SpO2) AND (clinical suspicion) AND (contraindication) AND (current) AND (excessive use of alcohol) AND (gabapentin) AND (history) AND (impaired cognition) AND (inadequate spoken finnish) AND (less than 93%) AND (medication used in survey protocol) AND (pregabalin) AND (preoperative) AND (rearthroplasty) AND (reliable pain assessment) AND (strong opiates) AND (subject can not use PCA adequately) AND (substance abuse) AND (substance used in survey protocol) AND (weight))"}
{"candidate_id": "LLM03988", "doc_id": "NCT03187379_exc", "case_bucket": "other", "source_criterion": "age <18 years previous history of roux-en-y gastric bypass patients undergoing other bariatric procedures pre-operative opioid analgesics", "candidate_expression": "((<18 years) AND (age) AND (bariatric procedures) AND (history) AND (opioid analgesics) AND (other) AND (pre-operative) AND (previous) AND (roux-en-y gastric bypass) AND (undergoing))"}
{"candidate_id": "LLM03989", "doc_id": "NCT03129555_inc", "case_bucket": "or", "source_criterion": "A diagnosis of VTE in outpatient clinic or as discharge diagnosis after hospitalization. A claimed prescription of a NOAC from a Danish pharmacy within 14 days of discharge or outpatient clinic visit.", "candidate_expression": "((NOAC Danish pharmacy within 14 days of discharge or outpatient clinic visit) AND (VTE) AND (hospitalization) AND (outpatient clinic) AND (prescription claimed) AND ((discharge) OR (outpatient clinic visit)) AND ((discharge diagnosis after hospitalization) OR (outpatient clinic)))"}
{"candidate_id": "LLM03990", "doc_id": "NCT03187379_exc", "case_bucket": "other", "source_criterion": "age <18 years previous history of roux-en-y gastric bypass patients undergoing other bariatric procedures pre-operative opioid analgesics", "candidate_expression": "((age <18 years) AND (bariatric procedures undergoing other) AND (opioid analgesics pre-operative) AND (roux-en-y gastric bypass previous history))"}
{"candidate_id": "LLM03991", "doc_id": "NCT03044561_exc", "case_bucket": "or", "source_criterion": "(1) Uterine abnormalities (e.g. septate, bicornuate and fibroid uterus, Asherman Syndrome). Concurrent use of organic nitrites and nitrates. Severe hepatic impairment. Severe renal impairment. Hypotension. Recent stroke or heart attack.", "candidate_expression": "((Concurrent) AND (Hypotension) AND (Recent) AND (Severe) AND (Uterine abnormalities) AND (hepatic impairment) AND (nitrates) AND (organic nitrites) AND (renal impairment) AND ((heart attack) OR (stroke)) AND ((Asherman Syndrome) OR (bicornuate uterus) OR (fibroid uterus) OR (septate uterus)))"}
{"candidate_id": "LLM03992", "doc_id": "NCT02385448_exc", "case_bucket": "or", "source_criterion": "Operative findings not suggestive of endometriotic cyst Contraindications to progestogens or oral contraceptive pills Unwillingness to tolerate menstrual irregularity Planning pregnancy within 2 years of study Cannot understand English, Cantonese or Putonghua", "candidate_expression": "((Contraindications) AND (Operative findings) AND (endometriotic cyst suggestive) AND (menstrual irregularity Unwillingness to tolerate) AND (pregnancy Planning within 2 years of study) AND ((oral contraceptive pills) OR (progestogens)))"}
{"candidate_id": "LLM03993", "doc_id": "NCT00305097_inc", "case_bucket": "other", "source_criterion": "Aged at least 18 years with an ability and willingness to give written informed consent. Body mass index 25-35 kg/m2 Users of at least 2 cups of caffeinated coffee per day who are willing to be randomized to any of the interventions. Non-smoking", "candidate_expression": "((25-35 kg/m2) AND (Aged) AND (Body mass index) AND (Non-smoking) AND (ability to give written informed consent) AND (at least 18 years) AND (at least 2 cups per day) AND (caffeinated coffee) AND (willing to be randomized) AND (willingness to give written informed consent))"}
{"candidate_id": "LLM03994", "doc_id": "NCT01806558_inc", "case_bucket": "or", "source_criterion": "1. Have a finding of a mass lesion on mammography or breast MRI (BIRADS 0, 4 or 5) that is >0.5 cm and < 2 cm in size and has had or will have additional workup with focused ultrasound. 2. Have a finding of a mass lesion on ultrasound (BIRADS 0, 4 or 5) that is > 0.5 cm and < 2 cm in size. 3. Have a positive finding on MBI that is < 2 cm in size and requires additional diagnostic workup with focused ultrasound.", "candidate_expression": "((0, 4 or 5) AND (< 2 cm) AND (> 0.5 cm and < 2 cm) AND (>0.5 cm and < 2 cm) AND (BIRADS) AND (MBI) AND (mass lesion) AND (positive finding) AND (requires additional diagnostic workup with focused ultrasound) AND (size) AND (ultrasound) AND ((breast MRI) OR (mammography)))"}
{"candidate_id": "LLM03995", "doc_id": "NCT02837783_exc", "case_bucket": "or", "source_criterion": "Patient has history of loose or watery stools Patient has both clinically significant findings and unexplained clinically significant alarm symptoms Patient has symptoms of or been diagnosed with a medical condition that may contribute to abdominal pain Patient has any protocol-excluded or clinically significant medical or surgical history that could confound the study assessments", "candidate_expression": "((Patient has any protocol-excluded or clinically significant medical or surgical history that could confound the study assessments) AND (abdominal pain) AND (clinically significant) AND (clinically significant alarm symptoms) AND (clinically significant findings) AND (could confound the study assessments) AND (history of) AND (loose stools) AND (may contribute to abdominal pain) AND (medical condition) AND (medical history) AND (protocol-excluded) AND (surgical history) AND (unexplained) AND (watery stools))"}
{"candidate_id": "LLM03996", "doc_id": "NCT02431559_exc", "case_bucket": "or", "source_criterion": "1. Prior exposure to doxorubicin, PLD or any other anthracycline, motolimod and other TLR agonists, MEDI4736 or checkpoint inhibitors, such as anti-CTLA4 and anti-PD1/anti-PD-L1 antibodies. 2. Subjects with platinum-refractory disease, defined as disease progression while receiving first line platinum-based therapy. 3. Clinically significant persistent immune-related adverse events following prior therapy. 4. Subjects with history or evidence upon physical examination of CNS disease, including primary brain tumor, seizures not controlled with standard medical therapy, any brain metastases, or, within six months prior to Day 1 of this study, history of cerebrovascular accident (CVA, stroke), transient ischemic attack (TIA) or subarachnoid hemorrhage. 5. Subjects with clinically significant cardiovascular disease. This includes: 1. Resisted hypertension 2. Myocardial infarction or unstable angina within 6 months prior to Day 1 of the study. 3. History of serious ventricular arrhythmia (i.e., ventricular tachycardia or ventricular fibrillation) or cardiac arrhythmias requiring anti-arrhythmic medications, except for atrial fibrillation that is well controlled with anti-arrhythmic medication. 4. Baseline ejection fraction ≤ 50% as assessed by echocardiogram or MUGA. 5. New York Heart Association (NYHA) Class II or higher congestive heart failure. 6. Grade 2 or higher peripheral ischemia, except for brief (< 24 hrs) episodes of ischemia managed non-surgically and without permanent deficit. 6. History of pneumonitis or interstitial lung disease. 7. Active, suspected or prior documented autoimmune disease (including inflammatory bowel disease, celiac disease, Wegner's granulomatosis, active Hashimoto's thyroiditis, rheumatoid arthritis, lupus, scleroderma and its variants, multiple sclerosis, myasthenia gravis). Vitiligo, type I diabetes mellitus, residual hypothyroidism due to autoimmune condition only requiring hormone replacement, psoriasis not requiring systemic treatment, or conditions not expected to recur in the absence of an external trigger are permitted. 8. Other malignancy within 2 years prior to Day 1 of the study, except for those treated with surgical intervention only. 9. Subjects with clinical symptoms or signs of gastrointestinal obstruction and/or who require drainage gastrostomy tube and/or parenteral hydration or nutrition. 10. Known immunodeficiency or HIV, Hepatitis B or Hepatitis C positivity. 11. History of severe allergic reactions to any unknown allergens or components of the study drugs. 12. Other serious illnesses (e.g., serious infections requiring antibiotics, bleeding disorders). 13. Prior treatment in any other interventional clinical trial within 4 weeks prior to Day 1 of the study. 14. Mental impairment that may compromise compliance with the requirements of the study. 15. Lack of availability for immunological and clinical follow-up assessment. 16. Women who are breastfeeding or pregnant as evidenced by positive serum pregnancy test 17. Subjects unwilling to use acceptable methods of contraception. -Female subjects should refrain from breastfeeding throughout this period. 18. Any condition that, in the clinical judgment of the treating physician, is likely to prevent the subject from complying with any aspect of the protocol or that may put the subject at unacceptable risk. 19. Subjects must not donate blood while on study and for at least 90 days following the last MEDI4736 treatment. 20. History of allogeneic organ transplant", "candidate_expression": "((CNS disease) AND (Clinically significant) AND (Female breastfeeding) AND (Mental impairment compromise compliance) AND (New York Heart Association (NYHA) Class II or higher) AND (Resisted hypertension) AND (Women) AND (allergic reactions History severe) AND (allogeneic organ transplant History) AND (anti-arrhythmic medication) AND (anti-arrhythmic medications) AND (autoimmune disease) AND (cardiovascular disease clinically significant) AND (clinically significant) AND (congestive heart failure) AND (contraception acceptable) AND (disease progression while receiving first line platinum-based therapy) AND (ejection fraction Baseline ≤ 50%) AND (hormone replacement) AND (illnesses serious) AND (immune-related adverse events Clinically significant persistent following prior therapy) AND (ischemia brief) AND (malignancy within 2 years prior to Day 1 of the study) AND (not expected to recur) AND (peripheral ischemia Grade 2 or higher < 24 hrs) AND (platinum-refractory disease) AND (serious) AND (serum pregnancy test positive) AND (standard medical therapy) AND (systemic treatment) AND (those) AND (to any unknown allergens or components of the study drugs) AND (treatment Prior) AND (unwilling) AND NOT (surgically) AND NOT (permanent deficit) AND NOT (surgical intervention) AND NOT (donate blood while on study for at least 90 days following the last MEDI4736 treatment) AND NOT (atrial fibrillation well controlled with anti-arrhythmic medication) AND ((interstitial lung disease History) OR (pneumonitis History)) AND ((Hashimoto's thyroiditis) OR (Wegner's granulomatosis) OR (celiac disease) OR (inflammatory bowel disease) OR (lupus) OR (multiple sclerosis) OR (myasthenia gravis) OR (rheumatoid arthritis) OR (scleroderma) OR (scleroderma variants)) AND ((Vitiligo) OR (residual hypothyroidism due to autoimmune condition) OR (type I diabetes mellitus)) AND ((autoimmune condition requiring hormone replacement) OR (conditions not expected to recur) OR (psoriasis requiring systemic treatment)) AND ((clinical symptoms of gastrointestinal obstruction) OR (drainage gastrostomy tube) OR (parenteral hydration) OR (parenteral nutrition) OR (signs of gastrointestinal obstruction)) AND ((HIV) OR (Hepatitis B) OR (Hepatitis C) OR (immunodeficiency)) AND ((bleeding disorders) OR (infections requiring antibiotics serious)) AND ((breastfeeding) OR (pregnant)) AND ((clinical follow-up assessment) OR (immunological follow-up assessment)) AND ((MEDI4736) OR (PLD) OR (TLR agonists) OR (anthracycline) OR (checkpoint inhibitors) OR (doxorubicin) OR (motolimod)) AND ((anti-CTLA4) OR (anti-PD-L1 antibodies) OR (anti-PD1 antibodies)) AND ((brain metastases) OR (primary brain tumor) OR (seizures controlled)) AND ((cerebrovascular accident) OR (subarachnoid hemorrhage) OR (transient ischemic attack (TIA))) AND ((CVA) OR (stroke)) AND ((Myocardial infarction) OR (unstable angina)) AND ((ventricular fibrillation) OR (ventricular tachycardia)) AND ((cardiac arrhythmias History requiring anti-arrhythmic medications) OR (ventricular arrhythmia History serious)) AND ((MUGA) OR (echocardiogram)))"}
{"candidate_id": "LLM03997", "doc_id": "NCT02905734_exc", "case_bucket": "other", "source_criterion": "Lack of understanding of the study contra-indication to nicotine replacement therapy health status incompatible with detention in police cells serious mental disorder usual place of residence outside Seine-Saint-Denis", "candidate_expression": "((Lack of understanding of the study) AND (contra-indication) AND (incompatible with detention in police cells) AND (nicotine replacement therapy) AND (place of residence outside Seine-Saint-Denis) AND (serious mental disorder))"}
{"candidate_id": "LLM03998", "doc_id": "NCT00236340_exc", "case_bucket": "other", "source_criterion": "Multiple pregnancy (more than 3 fetuses) Maternal history of placental abruptio Fetus with IUGR Pregnancy complicated with pre-eclampsia Unability to give informed consent", "candidate_expression": "((Fetus) AND (IUGR) AND (Maternal history of) AND (Multiple pregnancy) AND (Pregnancy) AND (fetuses more than 3) AND (placental abruptio) AND (pre-eclampsia) AND NOT (give informed consent))"}
{"candidate_id": "LLM03999", "doc_id": "NCT01912651_inc", "case_bucket": "or", "source_criterion": "all adult patients with a nasal or facial skin/soft tissue defect requiring reconstruction limited to or including a full-thickness skin graft", "candidate_expression": "((full-thickness skin graft) AND (reconstruction) AND (requiring) AND ((facial skin/soft tissue defect) OR (nasal skin/soft tissue defect)))"}
{"candidate_id": "LLM04000", "doc_id": "NCT01815580_inc", "case_bucket": "or", "source_criterion": "Adult men who have sex with men, and transgender women Unaware of HIV status at enrollment in follow-up cohort High risk for HIV infection Willing to test for HIV No prior ART, including prior administration of pre- and post-exposure prophylaxis in the last 30 days Willing to provide informed consent", "candidate_expression": "((ART) AND (Adult) AND (HIV infection) AND (HIV status) AND (High risk for) AND (No) AND (Unaware) AND (Unaware of HIV status) AND (Willing to) AND (Willing to provide) AND (administration) AND (at enrollment in follow-up cohort) AND (enrollment in follow-up cohort) AND (in the last 30 days) AND (informed consent) AND (men who have sex with men) AND (post-exposure prophylaxis) AND (pre- exposure prophylaxis) AND (prior) AND (test for HIV) AND (transgender women))"}
```
