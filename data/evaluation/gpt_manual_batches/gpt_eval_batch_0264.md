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
{"candidate_id": "LLM06576", "doc_id": "NCT02804646_exc", "case_bucket": "or", "source_criterion": "1) pregnancy, breast-feeding women, or female patients of childbearing potential but did not take contraceptive measures;2) existing severe acute infection and is not controlled; or purulent and chronic infection, delayed healing wounds; 3) the original severe heart disease, including congestive heart failure, uncontrolled high-risk arrhythmias, unstable angina, myocardial infarction, severe heart valve disease and resistant hypertension; 4) suffering from neurological and psychiatric diseases or mental disorders is not easy to control, poor compliance, and can not be described with treatment responders; primary brain or central nervous metastasis disease has not been controlled, with significant cranial hypertension or neuropsychiatric symptoms; 5) have bleeding tendencies; 6) other researchers believe that patients should not participate in the present trial.", "candidate_expression": "((acute) AND (bleeding tendencies) AND (chronic) AND (controlled) AND (delayed healing wounds) AND (heart disease) AND (high-risk) AND (infection) AND (not) AND (not controlled) AND (pregnancy, breast-feeding women, or female patients of childbearing potential but did not take contraceptive measures;) AND (purulent) AND (resistant) AND (severe) AND (significant) AND (uncontrolled) AND ((arrhythmias) OR (congestive heart failure) OR (heart valve disease) OR (hypertension) OR (myocardial infarction) OR (unstable angina)) AND ((mental disorders) OR (neurological diseases) OR (poor compliance) OR (psychiatric diseases)) AND ((central nervous metastasis disease) OR (primary brain disease)) AND ((cranial hypertension) OR (neuropsychiatric symptoms)))"}
{"candidate_id": "LLM06577", "doc_id": "NCT02106598_inc", "case_bucket": "or", "source_criterion": "18 years of age or older Histologically confirmed diagnosis of melanoma, breast cancer or gynecologic cancer at MSKCC Have one of the following disease histories: Newly-diagnosed or recurrent (local, regional, metastatic) malignant melanoma or breast cancer patients in whom SLN mapping is indicated Residual clinically or radiographically evident tumor, including primary cutaneous and mucosal melanomas Prior radiation therapy, chemotherapy, or surgery in patients requiring flap reconstruction in the head and neck region. Newly diagnosed patients with previous excisional biopsy. OR Newly-diagnosed gynecologic cancer patients in whom SLN mapping and surgical excision is indicated OR Normal baseline cardiac function based upon pre-operative evaluation At the discretion of the operating surgeon, ANC>1000/mcl and platelets>100,000/mcl. At the discretion of the operating surgeon, Bilirubin level of < 2.0 mg/dl in the absence of a history of Gilbert's disease (or pattern consistent with Gilbert's). For melanoma patients, If patients have a history of malignancy other than melanoma, and other skin cancers in the past five years, their inclusion is up to the discretion of the physician. All patients of childbearing and child-creating age must be using an acceptable form of birth control Women who are pre-menopausal must have a negative serum pregnancy test", "candidate_expression": "((18 years or older) AND (< 2.0 mg/dl) AND (>100,000/mcl) AND (>1000/mcl) AND (ANC) AND (All patients of childbearing and child-creating age must be using an acceptable form of birth control) AND (At the discretion of the operating surgeon) AND (Bilirubin level) AND (Gilbert's disease) AND (Histologically) AND (MSKCC) AND (Normal) AND (Prior) AND (Residual) AND (SLN mapping) AND (SLN mapping is indicated) AND (Women) AND (age) AND (baseline) AND (cardiac function) AND (confirmed) AND (evident) AND (excisional biopsy) AND (flap reconstruction) AND (gynecologic cancer) AND (head and neck region) AND (history) AND (in the absence of) AND (in the past five years) AND (melanoma) AND (negative) AND (other than) AND (platelets) AND (pre-menopausal) AND (pre-operative) AND (pre-operative evaluation) AND (previous) AND (requiring flap reconstruction) AND (serum pregnancy test) AND (surgical excision) AND (surgical excision is indicated) AND (tumor) AND (up to the discretion of the physician) AND ((breast cancer) OR (malignant melanoma)) AND ((local) OR (metastatic) OR (regional)) AND ((Newly-diagnosed) OR (recurrent)) AND ((clinically) OR (radiographically)) AND ((mucosal melanomas) OR (primary cutaneous)) AND ((chemotherapy) OR (radiation therapy) OR (surgery)) AND ((breast cancer) OR (gynecologic cancer) OR (melanoma)) AND ((malignancy) OR (skin cancers)))"}
{"candidate_id": "LLM06578", "doc_id": "NCT03026088_inc", "case_bucket": "or", "source_criterion": "18-80 year, male or female. Chronic Heart failure subjects with medical history of cardiac disease or other related cardiovascular disease. Left ventricular ejection fraction (LVEF) less than or equal to (=<) 40 percent (%). New York Heart Association (NYHA) class of II - IV NYHA II : Slight limitation of physical activity. Comfortable at rest, but ordinary physical activity results in undue breathlessness, fatigue or palpitation. NYHA III:Marked limitation of physical activity. Comfortable at rest, but less than ordinary activity causes undue breathlessness, fatigue or palpitation. NYHA IV:Unable to carry on any physical activity without discomfort. Symptoms at rest can be present. If any physical activity is undertaken, discomfort increased. Signed Informed Consent Form (ICF).", "candidate_expression": "((Chronic Heart failure) AND (LVEF) AND (Left ventricular ejection fraction less than or equal to 40 percent) AND (NYHA) AND (New York Heart Association class II - IV) AND (Signed Informed Consent Form (ICF)) AND (cardiac disease) AND (cardiovascular disease related) AND (female) AND (male) AND (year 18-80))"}
{"candidate_id": "LLM06579", "doc_id": "NCT03519568_exc", "case_bucket": "or", "source_criterion": "the history or family history of anaphylaxis, convulsion, epilepsy, encephalopathy and psychosis the history of severe inoculation allergies patients with immunodeficiency and malignant tumors during the treatment period, receiving immunosuppressive therapy (oral steroid) or HIV due to low immunity, or family members have congenital immune disease Nonspecific immunoglobulin was injected within one month temperature=37.1<U+2103> and infectious diseases the history of thrombocytopenia or other thrombocytopenia with a definite diagnosis respiratory disease, acute infection or chronic disease activity period severe cardiovascular disease, liver and kidney disease, and complications of diabetes infectious, suppurative and allergic dermatosis other conditions that may affect the evaluation of the trail any serious adverse events that have a causal relationship with the inoculation of the upper dose of the vaccine the abnormality of 4 levels (local, systemic adverse reactions and vital signs) was judged to be related to vaccination other new standards of exclusion criteria for first needle other conditions that may affect the evaluation of the trail", "candidate_expression": "((=37.1<U+2103>) AND (HIV) AND (Nonspecific immunoglobulin) AND (acute infection) AND (adverse events) AND (allergic dermatosis) AND (anaphylaxis) AND (cardiovascular disease) AND (chronic disease activity period) AND (complications) AND (congenital immune disease) AND (convulsion) AND (diabetes) AND (during the treatment period) AND (encephalopathy) AND (epilepsy) AND (family history) AND (family members) AND (history) AND (immunodeficiency) AND (immunosuppressive therapy) AND (infectious dermatosis) AND (infectious diseases) AND (inoculation allergies) AND (inoculation of the upper dose of the vaccine) AND (kidney disease) AND (liver disease) AND (malignant tumors) AND (oral steroid) AND (other) AND (psychosis) AND (respiratory disease) AND (serious) AND (severe) AND (suppurative dermatosis) AND (temperature) AND (thrombocytopenia) AND (within one month))"}
{"candidate_id": "LLM06580", "doc_id": "NCT00235170_inc", "case_bucket": "or", "source_criterion": "1. Patients with stable (Canadian Cardiovascular Society 1, 2, 3 or 4) or unstable (Braunwald class IB, IC, IIB, IIC, IIIB, IIIC) angina pectoris and ischemia, or patients with atypical chest pain or even those who are asymptomatic provided they have documented myocardial ischaemia (e.g. treadmill exercise test, radionuclide scintigraphy, stress echocardiography, Holter tape); 2. Patients who are eligible for coronary revascularization (angioplasty or CABG); 3. At least 2 lesions (located in different vessels and in different territories) potentially amenable to stent implantation; 4. de novo native vessels; 5. Multivessel disease with at least one significant stenosis in LAD and with treatment of the lesion in another major epicardial coronary artery. A two-vessel disease or a three-vessel disease may be viewed as a combination of a side branch and a main epicardial vessel provided they supply different territories; left anterior descending, left circumflex and right coronary artery); 6. Total occluded vessels. One total occluded major epicardial vessel or side branch can be included and targeted as long as one other major vessel has a significant stenosis amenable for SA, provided the age of occlusion is less than one month e.g. recent instability, infarction with ECG changes in the area subtended by the occluded vessel. Patients with total occluded vessels of unknown duration or existing longer than one month and a reference over 1.50 mm should not be included, not even as a third or fourth vessel to be dilated; 7. Significant stenosis has been defined as a stenosis of more than 50% in luminal diameter (in at least one view, on visual interpretation or preferably by QCA); 8. Left ventricular ejection fraction should be at least 30%.", "candidate_expression": "((1, 2, 3 or 4) AND (At least 2) AND (Braunwald class) AND (CABG) AND (Canadian Cardiovascular Society) AND (Holter tape) AND (IB) AND (IC) AND (IIB) AND (IIC) AND (IIIB) AND (IIIC) AND (Left ventricular ejection fraction) AND (Multivessel disease) AND (One) AND (Significant stenosis) AND (Total occluded vessels) AND (angina pectoris) AND (angioplasty) AND (asymptomatic) AND (at least 30%) AND (at least one) AND (atypical chest pain) AND (coronary revascularization) AND (de novo) AND (documented) AND (eligible for) AND (in another major epicardial coronary artery) AND (ischemia) AND (lesions) AND (located in different territories) AND (located in different vessels) AND (longer than one month) AND (more than 50% in luminal diameter) AND (myocardial ischaemia) AND (native vessels) AND (over 1.50 mm) AND (potentially amenable) AND (radionuclide scintigraphy) AND (reference) AND (significant stenosis in LAD) AND (stable) AND (stenosis) AND (stent implantation) AND (stress echocardiography) AND (total occluded major epicardial vessel) AND (total occluded side branch) AND (total occluded vessels) AND (treadmill exercise test) AND (treatment of the lesion) AND (unknown duration) AND (unstable))"}
{"candidate_id": "LLM06581", "doc_id": "NCT03118232_inc", "case_bucket": "or", "source_criterion": "Nursing homes will be eligible to participate if they meet the following criteria: Licensed nursing home in Orange County or Southern Los Angeles County serving adults Minimal use of chlorhexidine bathing* Minimal use of nasal decolonization* *Minimal use defined as <15% of residents receiving at least one chlorhexidine bath or nasal decolonization treatment during their nursing home stay.", "candidate_expression": "((Nursing homes) AND (chlorhexidine) AND (chlorhexidine bath at least one) AND (chlorhexidine bathing Minimal use) AND (nasal decolonization Minimal use) AND (nasal decolonization treatment during their nursing home stay) AND (residents receiving at least one chlorhexidine bath <15%) AND ((Licensed nursing home) OR (Orange County) OR (Southern Los Angeles County)))"}
{"candidate_id": "LLM06582", "doc_id": "NCT02754583_inc", "case_bucket": "other", "source_criterion": "Community in a school district that is within the study area Area within each school district that is in need of a well", "candidate_expression": "((school district that is in need of a well) AND (school district that is within the study area))"}
{"candidate_id": "LLM06583", "doc_id": "NCT01807897_inc", "case_bucket": "or", "source_criterion": "Veteran receiving care within the Veterans Health Administration healthcare system Age 18 years Physician diagnosis of chronic heart failure, American Heart Association Stage C-D LVEF <45% No change in active cardiac medications for 4 weeks prior to randomization Ability to provide informed consent Moderate to severe central or mixed central and obstructive sleep apnea, defined as an apnea-hypopnea index (AHI) 15 events per hour, with a central AHI >5 events/hour", "candidate_expression": "((AHI) AND (Ability to provide informed consent) AND (Age 18 years) AND (American Heart Association Stage C-D) AND (LVEF <45%) AND (Veteran) AND (Veterans Health Administration healthcare system) AND (apnea-hypopnea index 15 events per hour,) AND (cardiac medications change for 4 weeks prior to randomization) AND (central AHI >5 events/hour) AND (chronic heart failure) AND ((central sleep apnea) OR (mixed central sleep apnea) OR (obstructive sleep apnea)) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM06584", "doc_id": "NCT02735902_exc", "case_bucket": "or", "source_criterion": "The patient is participating in another study The patient is in an exclusion period determined by a previous study The patient or his/her representative refuses to sign the consent It is impossible to correctly inform the patient or his/her representative The patient is pregnant or breastfeeding The patient has a contraindication (or an incompatible drug association) for a treatment used in this study The patient had a coronary stent for less than 12 months The patient does not require treatment with aspirin or any other antiplatelet agent The patient has a history of aspirin allergy High bleeding risk; such as platelets <50,000 / mm3 during screening, Hb <8.5 g / dL, history of intracranial hemorrhage or subdural hematoma, major surgery, parenchymal organ biopsy or severe trauma within 30 days before inclusion, active gastrointestinal ulcer in the last 3 months; History of Stroke in the last 3 months; Moderate or severe liver affection associated with coagulopathy Active infectious endocarditis Active tumor treated at the time of inclusion associated with expected survival less than one year", "candidate_expression": "((<50,000 / mm3) AND (<8.5 g / dL) AND (Active) AND (High) AND (History of) AND (It is impossible to correctly inform the patient or his/her representative) AND (Stroke) AND (The patient is participating in another study) AND (The patient is pregnant or breastfeeding) AND (The patient or his/her representative refuses to sign the consent) AND (active) AND (allergy) AND (aspirin) AND (associated with coagulopathy) AND (at the time of inclusion) AND (bleeding risk) AND (coagulopathy) AND (contraindication) AND (coronary stent) AND (expected survival) AND (history of) AND (in the last 3 months) AND (infectious endocarditis) AND (last 3 months) AND (less than 12 months) AND (less than one year) AND (liver affection) AND (not) AND (other) AND (require) AND (severe) AND (treated) AND (treatment) AND (tumor) AND (within 30 days) AND ((Hb) OR (gastrointestinal ulcer) OR (platelets)) AND ((intracranial hemorrhage) OR (major surgery,) OR (parenchymal organ biopsy) OR (subdural hematoma) OR (trauma)) AND ((antiplatelet agent) OR (aspirin)) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM06585", "doc_id": "NCT02760251_exc", "case_bucket": "or", "source_criterion": "Adults older than 45 and children younger than 18 years Platelet count higher than 30x109/l at time of screening Suspicion of secondary ITP Positive family history for ITP Presence or history of autoimmune disease as judged by the investigator Hepatosplenomegaly Presence or history of relevant hepatic disease as judged by the investigator Presence or history of thromboembolic disease as judged by the investigator Patients with splenectomy Women who are pregnant or breast feeding Intention to become pregnant during the course of the study Lack of safe double contraception (see 7.1) Any vaccination 2 weeks prior start of the study Drugs with a known impact on the immune system or on platelet function must be recorded and an exclusion of the study should be discussed with the study center Known or suspected non-compliance, drug or alcohol abuse Inability to follow the procedures of the study, e.g. due to language problems, psychological disorders, dementia of the study subject Participation in another study with investigational drug within the 30 days preceding and during the present study Previous enrolment into the current study Previous treatment with romiplostim or eltrombopag Hypersensitivity to the active substance or to any of the excipients or to E. coli derived proteins Enrolment of the investigator, his/her family members, employees and other dependent persons", "candidate_expression": "((Adults older than 45) AND (Drugs with a known impact on the immune system or on platelet function must be recorded and an exclusion of the study should be discussed with the study center) AND (Hepatosplenomegaly) AND (Hypersensitivity) AND (Inability to follow the procedures of the study, e.g. due to language problems, psychological disorders, dementia of the study subject) AND (Intention to become pregnant during the course of the study) AND (Lack of safe double contraception (see 7.1)) AND (Platelet count higher than 30x109/l at time of screening) AND (Women who are pregnant or breast feeding) AND (as judged by the investigator) AND (autoimmune disease) AND (children younger than 18 years) AND (family history for ITP) AND (hepatic disease relevant) AND (secondary ITP) AND (splenectomy) AND (thromboembolic disease) AND (vaccination 2 weeks prior start of the study) AND ((alcohol abuse) OR (drug abuse)) AND ((eltrombopag) OR (romiplostim)))"}
{"candidate_id": "LLM06586", "doc_id": "NCT03029078_exc", "case_bucket": "or", "source_criterion": "Pregnant woman or breastfeeding immunosuppression including AIDS, corticosteroids over 60mg/day ongoing antibiotic treatment at the day of inclusion impossibility to obtain a signed consent form.", "candidate_expression": "((AIDS) AND (Pregnant) AND (antibiotic) AND (at the day of inclusion) AND (breastfeeding) AND (corticosteroids) AND (day of inclusion) AND (immunosuppression) AND (impossibility to obtain) AND (over 60mg/day) AND (signed consent form) AND (treatment) AND (woman))"}
{"candidate_id": "LLM06587", "doc_id": "NCT02631512_exc", "case_bucket": "or", "source_criterion": "Ulcers due to non-diabetic etiology. Uncontrolled diabetes defined as HbA1c above 70 mmol/mol and insufficient nutritional status. Ulcers older than 1 year. Any of gangrene, osteomyelitis, cellulitis, or Charcot osteoarthropathy.", "candidate_expression": "((Any of) AND (Charcot osteoarthropathy) AND (HbA1c) AND (Ulcers) AND (Uncontrolled diabetes) AND (above 70 mmol/mol) AND (cellulitis) AND (gangrene) AND (insufficient nutritional status) AND (non-diabetic) AND (older than 1 year) AND (osteomyelitis))"}
{"candidate_id": "LLM06588", "doc_id": "NCT02773173_inc", "case_bucket": "other", "source_criterion": "Patients older than 18 years Classification of the American Society of Anesthesiologists (ASA I-III) No cognitive deficits Signed informed consent prior to surgery", "candidate_expression": "((ASA) AND (Classification of the American Society of Anesthesiologists) AND (I-III) AND (No) AND (Signed informed consent prior to surgery) AND (cognitive deficits) AND (older than 18) AND (years))"}
{"candidate_id": "LLM06589", "doc_id": "NCT02284737_exc", "case_bucket": "or", "source_criterion": "Pregnancy and breast feeding mother; Estimated life expectancy <12 months; Scheduled major surgery in the next 6 months; Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk; Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 30 days. WHO group II, III, IV, V PH Severe Renal dysfunction (Ccr<30 ml/min) Blood platelet count<100,000/L Expected life span<6-month Systematical inflammation Malignant cancer(s) Tricuspid valve stenosis, Supra-pulmonary valve stenosis Allergic to studied drugs or metal materials.", "candidate_expression": "((Allergic) AND (Blood platelet count <100,000/L) AND (Ccr <30 ml/min) AND (Estimated life expectancy <12 months) AND (Expected life span <6-month) AND (Malignant cancer) AND (PH) AND (Renal dysfunction Severe) AND (Systematical inflammation) AND (WHO group II, III, IV, V) AND (investigational drug) AND (major surgery Scheduled in the next 6 months) AND ((Pregnancy) OR (breast feeding)) AND ((Supra-pulmonary valve stenosis) OR (Tricuspid valve stenosis)) AND ((studied drugs) OR (studied metal materials)) AND ((device Previous) OR (enrolment in this study Previous) OR (treatment with an investigational drug Previous)) AND ((Inability to comply with follow-up requirements) OR (Inability to follow the protocol)))"}
{"candidate_id": "LLM06590", "doc_id": "NCT02704234_exc", "case_bucket": "other", "source_criterion": "pregnancy menopause interstitial cystitis irritable bowel syndrome untreated vaginitis cervicitis pelvic inflammatory disease any other pelvic pathology causing pain concomitant physical therapy concomitant biofeedback concomitant massage additional acupuncture", "candidate_expression": "((acupuncture) AND (biofeedback) AND (causing pain) AND (cervicitis) AND (concomitant) AND (interstitial cystitis) AND (irritable bowel syndrome) AND (massage) AND (menopause) AND (pelvic inflammatory disease) AND (pelvic pathology) AND (physical therapy) AND (pregnancy) AND (untreated vaginitis))"}
{"candidate_id": "LLM06591", "doc_id": "NCT00931983_exc", "case_bucket": "other", "source_criterion": "Other neuromuscular disease Contraindication to weight bearing on lower extremities Pressure sores where harness would be applied Uncontrollable hypotension when upright Lower limb contractures impeding range of motion necessary for ambulation Prior enrolment in a BWATT program Unable to commit to intervention for duration of protocol", "candidate_expression": "((Contraindication) AND (Lower limb contractures) AND (Pressure sores) AND (Unable to commit to intervention for duration of protocol) AND (Uncontrollable) AND (harness) AND (hypotension) AND (impeding) AND (neuromuscular disease) AND (range of motion necessary for ambulation) AND (weight bearing on lower extremities) AND (when upright))"}
{"candidate_id": "LLM06592", "doc_id": "NCT01084993_exc", "case_bucket": "or", "source_criterion": "Intolerance or allergy to ASA, clopidogrel or ticlopidine precluding treatment for 12 months Concurrent participation in other investigational study Femoral sheath (artery)", "candidate_expression": "((ASA) AND (Concurrent participation in other investigational study) AND (Femoral sheath (artery)) AND (Intolerance) AND (allergy) AND (clopidogrel) AND (ticlopidine) AND NOT (treatment for 12 months))"}
{"candidate_id": "LLM06593", "doc_id": "NCT02515773_exc", "case_bucket": "or", "source_criterion": "Patients will be excluded if they have had exposure to a total daily dose of MET 1000 mg bid for at least 2 weeks in the past 3 months; Patients will be excluded if they could not tolerate MET during the recommended titration schedule outlined in the protocol; Major neurological or medical illnesses that affect weight gain (e.g., unstable thyroid disease) or require a systemic medication that might impact weight or glucose regulation (e.g., diabetes mellitus [insulin], chronic renal failure [steroids]); Fasting glucose = 126 mg/dL on 2 occasions during screening indicating need for prompt treatment; If lab results are available in the last 6 months, then a serum creatinine =1.3 mg/dL on 2 occasions during screening and/or follow-up, indicating potential impairment of renal functioning; Pregnant or breast feeding; Children and caregivers who are unable to complete assessments for any reason;", "candidate_expression": "((Children and caregivers who are unable to complete assessments for any reason) AND (Fasting glucose = 126 mg/dL 2 o) AND (MET) AND (MET 1000 mg bid at least 2 weeks in the past 3 months) AND (Pregnant or breast feeding) AND (not tolerate) AND (serum creatinine =1.3 mg/dL 2) AND ((chronic renal failure) OR (diabetes mellitus) OR (insulin) OR (steroids) OR (thyroid disease unstable)))"}
{"candidate_id": "LLM06594", "doc_id": "NCT01098383_inc", "case_bucket": "or", "source_criterion": "A formal diagnosis of Autism or Pervasive Developmental Disorder not otherwise specified (PDD-NOS), given by a child neurologist. Age: 10-18 years. A signed parental consent form.", "candidate_expression": "((A signed parental consent form) AND (Age 10-18 years) AND (PDD-NOS) AND ((Autism) OR (Pervasive Developmental Disorder not otherwise specified)))"}
{"candidate_id": "LLM06595", "doc_id": "NCT02862912_inc", "case_bucket": "or", "source_criterion": "ASA I and II women 18-45 yrs old Singleton pregnancy Cervical cerclage 1st or 2nd trimester of pregnancy undergoing with spinal anesthesia Height 150 - 180 cm BMI = 40 kg/m2.", "candidate_expression": "((ASA I and II) AND (BMI = 40 kg/m2) AND (Cervical cerclage 1st trimester 2nd trimester) AND (Height 150 - 180 cm) AND (Singleton pregnancy) AND (old 18-45 yrs) AND (pregnancy) AND (spinal anesthesia) AND (women))"}
{"candidate_id": "LLM06596", "doc_id": "NCT02897856_inc", "case_bucket": "or", "source_criterion": "Children 6 month to 14 years who will be presented to the pediatric emergency or attended by emergency medical service who have active seizure and had no intravenous access would be eligible for the study.", "candidate_expression": "((Children) AND (attended by emergency medical service) AND (pediatric emergency) AND (seizure active) AND (years 6 month to 14 years) AND NOT (intravenous access))"}
{"candidate_id": "LLM06597", "doc_id": "NCT01218737_inc", "case_bucket": "or", "source_criterion": "Patient is indicated to have an ocular refractive surgery performed (myopia, astigmatism, hypermetropy) by the Lasik method. Patient presents a normal eye fundus. Patient has intraocular pressure (IOP) ≤ 20 mmHg.", "candidate_expression": "((Lasik method) AND (eye fundus) AND (indicated to have an ocular refractive surgery performed) AND (intraocular pressure (IOP)) AND (normal) AND (normal eye fundus) AND (ocular refractive surgery) AND (≤ 20 mmHg) AND ((astigmatism) OR (hypermetropy) OR (myopia)))"}
{"candidate_id": "LLM06598", "doc_id": "NCT03233880_exc", "case_bucket": "or", "source_criterion": "Women with multi-fetal pregnancy, diabetes mellitus, chronic hypertension, or chronic renal disease", "candidate_expression": "((Women) AND ((chronic hypertension) OR (chronic renal disease) OR (diabetes mellitus) OR (multi-fetal pregnancy)))"}
{"candidate_id": "LLM06599", "doc_id": "NCT02323399_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06600", "doc_id": "NCT03131050_exc", "case_bucket": "or", "source_criterion": "Currently enrolled in, or discontinued within the last 30 days from, a clinical trial involving an off-label use of an investigational drug. Current Axis I primary psychiatric diagnosis other than major depressive disorder. Organic mental disease, including mental retardation. History of clinically significant disease, including any cardiovascular, hepatic, renal, respiratory, hematologic, endocrinologic, or neurologic disease, or clinically significant laboratory abnormality that is not stabilized or is anticipated to require treatment during the study. Subjects receiving an investigational agent (including different formulation and generic agents of investigational drug) in the previous 3 months prior to screening. Women in pregnancy or lactation, or female of child bearing potential without appropriate birth control measures. Use of antipsychotics or mood stabilizers within 5 days prior to screening. Has received depot antipsychotic medication within one cycle prior to screening. Known allergy or lack of response to mirtazapine. Has received ECT or MECT within 3 months prior to screening. History of anticholinergic drug allergy or complications (allergic reaction, skin rash, urticaria and other allergic reactions which caused by drugs). Smokers. Significant risk of suicidal and/or self-harm behaviors", "candidate_expression": "((Axis I) AND (Currently enrolled in, or discontinued within the last 30 days from, a clinical trial involving an off-label use of an investigational drug.) AND (ECT) AND (MECT) AND (Organic mental disease) AND (Smokers) AND (Subjects receiving an investigational agent (including different formulation and generic agents of investigational drug) in the previous 3 months prior to screening.) AND (Women in pregnancy or lactation, or female of child bearing potential without appropriate birth control measures.) AND (allergic reaction) AND (allergic reactions) AND (allergy) AND (anticholinergic drug) AND (anticipated to require) AND (antipsychotics) AND (cardiovascular disease) AND (clinically significant) AND (depot antipsychotic medication) AND (disease) AND (drugs) AND (during the study) AND (endocrinologic disease) AND (hematologic disease) AND (hepatic disease) AND (laboratory abnormality) AND (lack of response) AND (major depressive disorder) AND (mental retardation) AND (mirtazapine) AND (mood stabilizers) AND (neurologic disease) AND (not) AND (other) AND (other than) AND (primary) AND (psychiatric diagnosis) AND (renal disease) AND (respiratory disease) AND (risk of) AND (screening) AND (self-harm behaviors) AND (skin rash) AND (stabilized) AND (suicidal behaviors) AND (treatment) AND (urticaria) AND (within 3 months prior to screening) AND (within 5 days prior to screening) AND (within one cycle prior to screening))"}
```
