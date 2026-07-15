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
{"candidate_id": "LLM03501", "doc_id": "NCT03555526_exc", "case_bucket": "or", "source_criterion": "aged less than 20 years history of gastric resection surgery history of allergy to study drugs pregnancy or lactating women severe underlying illness, such as end stage renal disease, decompensated liver cirrhosis, or non-curative malignancy", "candidate_expression": "((aged less than 20 years) AND (allergy) AND (gastric resection surgery) AND (severe underlying illness) AND (study drugs) AND (women) AND ((end stage renal disease) OR (liver cirrhosis decompensated) OR (malignancy non-curative)) AND ((lactating) OR (pregnancy)))"}
{"candidate_id": "LLM03502", "doc_id": "NCT03013790_exc", "case_bucket": "or", "source_criterion": "Patients with head trauma or Neurosurgical intervention Patients <65 years of age Patients with an expected life expectancy <48 hours Blind patients Patients with a seizure history Patients with uncontrolled hypertension Patients with a supratheraputic (>3.0) INR Patients on strong CYP1A2 inhibitors: ciprofloxacin, fluvoxamine, methoxsalen, ofloxacin, primaquine Patients who do not speak English or Spanish", "candidate_expression": "((<48 hours) AND (<65 years) AND (>3.0) AND (Blind) AND (INR) AND (Neurosurgical intervention) AND (age) AND (ciprofloxacin) AND (expected life expectancy) AND (fluvoxamine) AND (head trauma) AND (history) AND (methoxsalen) AND (not) AND (ofloxacin) AND (primaquine) AND (seizure) AND (speak English) AND (speak Spanish) AND (strong CYP1A2 inhibitors) AND (supratheraputic) AND (uncontrolled hypertension))"}
{"candidate_id": "LLM03503", "doc_id": "NCT02056288_exc", "case_bucket": "or", "source_criterion": "Pulseless extremity Compromised neurologic status on exam (specifically assessment of radial, ulnar, and median nerve) Known allergy to local anesthetics (7) Not scheduled for closed reduction with percutaneous pinning under general anesthesia Bleeding diathesis American Society of Anesthesiologist (ASA) status 4 or higher. Sleep apnea by polysomnography", "candidate_expression": "((American Society of Anesthesiologist (ASA) status 4 or higher) AND (Bleeding diathesis) AND (Compromised neurologic status) AND (Pulseless extremity) AND (Sleep apnea) AND (allergy) AND (closed reduction with percutaneous pinning scheduled for) AND (general anesthesia) AND (local anesthetics) AND (polysomnography) AND ((median nerve) OR (nerve radial) OR (nerve ulnar)))"}
{"candidate_id": "LLM03504", "doc_id": "NCT03484091_inc", "case_bucket": "other", "source_criterion": "Symptomatic primary knee osteoarthritis with failed conservative treatment at least 3 months Kellgren-Lawrence grade I-III Gave informed consent Can do questionnaires", "candidate_expression": "((Can do questionnaires) AND (Gave informed consent) AND (Kellgren-Lawrence grade I-III) AND (conservative treatment failed at least 3 months) AND (osteoarthritis Symptomatic primary knee))"}
{"candidate_id": "LLM03505", "doc_id": "NCT03045562_inc", "case_bucket": "other", "source_criterion": "Informed consent must be obtained prior to any study procedure. Age>18 years. Subjects of STEMI who underwent primary PCI within the first 12 hours.", "candidate_expression": "((>18 years.) AND (Age) AND (Informed consent must be obtained prior to any study procedure) AND (STEMI) AND (primary PCI) AND (within the first 12 hours.))"}
{"candidate_id": "LLM03506", "doc_id": "NCT03297021_inc", "case_bucket": "or", "source_criterion": "ASA I, II, III presenting for ambulatory surgery to be performed under general anesthesia", "candidate_expression": "((ASA) AND (ambulatory surgery) AND (general anesthesia) AND (under general anesthesia) AND ((I) OR (II) OR (III)))"}
{"candidate_id": "LLM03507", "doc_id": "NCT03034837_exc", "case_bucket": "other", "source_criterion": "Can not cooperate with the treatment Can not obtain the child's parental consent", "candidate_expression": "((Can not obtain the child's parental consent) AND (child's parental consent) AND (cooperate with the treatment) AND (not))"}
{"candidate_id": "LLM03508", "doc_id": "NCT03058835_exc", "case_bucket": "or", "source_criterion": "Active alcohol or drug use or dependence which may interfere with adherence to study requirements HIV-infected at screening or enrollment Estimated CrCl < 60 mL/min Past participation in an HIV vaccine study Positive Hepatitis B surface antigen test Underlying medical condition with survival unlikely during follow-up period Any condition that in the opinion of study staff would make participation in the study unsafe or interfere with achieving study objectives Pregnant or breast feeding Actively trying to achieve pregnancy", "candidate_expression": "((Active alcohol or drug use or dependence which may interfere with adherence to study requirements) AND (Actively trying to achieve pregnanc) AND (Estimated CrCl < 60 mL/min) AND (HIV-infected at screening at enrollment) AND (Hepatitis B surface antigen test Positive) AND (Pregnant interfere with achieving study objectives) AND (breast feeding) AND (condition make participation in the study unsafe) AND (medical condition) AND (survival unlikely))"}
{"candidate_id": "LLM03509", "doc_id": "NCT01314898_inc", "case_bucket": "or", "source_criterion": "Male and/or female healthy volunteers, age 18 to 55 years. Females must be of non-childbearing potential. Body Mass Index (BMI) of 17.5 to 30.5 kg/m2; and a total body weight >50 kg (110 lbs). Subjects who are willing and able to comply with scheduled visits, treatment plan, laboratory tests, diet restrictions and other trial procedures.", "candidate_expression": "((17.5 to 30.5 kg/m2) AND (18 to 55 years) AND (>50 kg (110 lbs)) AND (Body Mass Index (BMI)) AND (Females) AND (Subjects who are willing and able to comply with scheduled visits, treatment plan, laboratory tests, diet restrictions and other trial procedures.) AND (age) AND (childbearing potential) AND (healthy) AND (non) AND (total body weight) AND ((Male) OR (female)))"}
{"candidate_id": "LLM03510", "doc_id": "NCT03011177_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03511", "doc_id": "NCT00397215_exc", "case_bucket": "or", "source_criterion": "Administration of the licensed MF59-containing vaccines, e.g. Fluad™ or Addigrip™ or virosome-based influenza vaccines such as Inflexal V™, InfectoVac Flu™ or Invivac™ during the 2006-2007 influenza season. Administration of licensed vaccines within 2 weeks (for inactivated vaccines) or 4 weeks (for live vaccines) prior to enrolment in this study. Planned administration of a vaccine not foreseen by the study protocol up to 30 days after the second vaccination with H5N1 vaccine. Chronic administration (defined as more than 14 days) of immunosuppressants or other immune-modifying drugs within six months prior to the first administration of the study vaccine. Any confirmed or suspected immunosuppressive or immunodeficient condition, based on medical history and physical examination (no laboratory testing required). History of chronic alcohol consumption and/or drug abuse. History of hypersensitivity to vaccines. History of allergic disease or reactions likely to be exacerbated by any component of the vaccine (including egg and thiomersal allergy). Acute clinically significant pulmonary, cardiovascular, hepatic or renal functional abnormality, as determined by physical examination or laboratory screening tests. Acute disease at the time of enrolment. Serious chronic disease including any medically significant chronic pulmonary, cardiovascular, renal, neurological, psychiatric or metabolic disorder, as determined by medical history and physical examination. Administration of immunoglobulins and/or any blood products within the three months preceding the first vaccination or during the study. Use of any investigational or non-registered product (drug or vaccine) other than the study vaccine(s) within 30 days prior to the first vaccination, or planned use during the study period. Any condition which, in the opinion of the investigator, prevents the subject from participation in the study.", "candidate_expression": "((Acute disease) AND (Addigrip) AND (Chronic) AND (Fluad) AND (H5N1 vaccine) AND (History) AND (InfectoVac Flu) AND (Inflexal V) AND (Invivac) AND (MF59-containing vaccines) AND (Serious) AND (allergic disease) AND (allergic reactions) AND (any blood products) AND (at the time of enrolment) AND (cardiovascular functional abnormality) AND (chronic alcohol consumption) AND (chronic cardiovascular disorder) AND (chronic disease) AND (chronic metabolic disorder) AND (chronic neurological disorder) AND (chronic psychiatric disorder) AND (chronic pulmonary disorder) AND (chronic renal disorder) AND (condition) AND (confirmed) AND (drug) AND (drug abuse) AND (during the 2006-2007 influenza season) AND (during the study) AND (during the study period) AND (egg allergy) AND (first) AND (foreseen by the study protocol) AND (hepatic functional abnormality) AND (hypersensitivity to vaccines) AND (immunodeficient condition) AND (immunoglobulins) AND (immunosuppressants) AND (immunosuppressive condition) AND (inactivated vaccines) AND (investigational) AND (licensed vaccines) AND (live vaccines) AND (more than 14 days) AND (non-registered) AND (not) AND (other immune-modifying drugs) AND (other than) AND (other than the study vaccine(s)) AND (planned) AND (product) AND (pulmonary functional abnormality) AND (renal functional abnormality) AND (second) AND (study vaccine(s)) AND (suspected) AND (the first vaccination) AND (the study) AND (thiomersal allergy) AND (up to 30 days) AND (use) AND (vaccination) AND (vaccine) AND (virosome-based influenza vaccines) AND (which prevents the subject from participation in the study) AND (within 2 weeks prior to enrolment in this study) AND (within 30 days prior to the first vaccination) AND (within 4 weeks prior to enrolment in this study) AND (within six months prior) AND (within the three months preceding the first vaccination))"}
{"candidate_id": "LLM03512", "doc_id": "NCT02552459_exc", "case_bucket": "or", "source_criterion": "long-term use of analgesics,sedatives or non steroidal anti-inflammatory drugs history. known for dexmedetomidine or other drugs allergy in this study. cannot communicate. preoperative systolic blood pressure <90 mmHg, or the heart rate <50/min.", "candidate_expression": "((<50/min) AND (<90 mmHg) AND (allergy) AND (analgesics) AND (cannot communicate) AND (dexmedetomidine) AND (drugs) AND (heart rate) AND (history) AND (long-term use) AND (non steroidal anti-inflammatory drugs) AND (other) AND (preoperative systolic blood pressure) AND (sedatives))"}
{"candidate_id": "LLM03513", "doc_id": "NCT01742117_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03514", "doc_id": "NCT02537899_inc", "case_bucket": "or", "source_criterion": "Male or female Age 18 to 65 years Diagnosed with spinal cord injury between 3 days and 4 weeks American Spinal Injury Association Impairment Scale A or B Informed consent for inclusion into the database is obtained", "candidate_expression": "((Age 18 to 65 years) AND (American Spinal Injury Association Impairment Scale A or B) AND (Informed consent for inclusion into the database is obtained) AND (Male) AND (female) AND (spinal cord injury between 3 days and 4 weeks))"}
{"candidate_id": "LLM03515", "doc_id": "NCT02150590_exc", "case_bucket": "or", "source_criterion": "unstable condition, COPD exacerbation mild (GOLD 1) or very severe COPD (GOLD 4) requirement for oxygen therapy at low altitude residence hypoventilation pulmonary hypertension more than mild or unstable cardiovascular disease use of drugs that affect respiratory center drive internal, neurologic or psychiatric disease that interfere with protocol compliance including current heavy smoking (>20 cigarettes per day), inability to perform 6 min walk test. previous intolerance to moderate altitude (<2600m). exposure to altitudes >1500m for >2 days within the last 4 weeks before the study. pregnant or nursing patients", "candidate_expression": "((1)) AND (4) AND (6 min walk test) AND (<2600m) AND (>20 cigarettes per day) AND (COPD) AND (COPD exacerbation) AND (GOLD) AND (altitude) AND (cardiovascular disease) AND (condition) AND (heavy) AND (hypoventilation) AND (inability) AND (internal disease) AND (intolerance) AND (mild) AND (moderate) AND (more than mild) AND (neurologic disease) AND (oxygen therapy) AND (pregnant or nursing patients) AND (psychiatric disease) AND (pulmonary hypertension) AND (smoking) AND (unstable) AND (very severe))"}
{"candidate_id": "LLM03516", "doc_id": "NCT03011476_exc", "case_bucket": "other", "source_criterion": "Significant motor complication affecting daily activities Drugs related to acetylcholine metabolism", "candidate_expression": "((Drugs related to acetylcholine metabolis) AND (acetylcholine) AND (motor complication Significant))"}
{"candidate_id": "LLM03517", "doc_id": "NCT03070847_inc", "case_bucket": "other", "source_criterion": "age > 18 y.o. American Society of Anesthesiologists Physical Status Classification (ASA) 1-2 signed informed consent form after reading the information about the study and talking with one of the investigators", "candidate_expression": "((1-2) AND (> 18 y.o) AND (ASA) AND (American Society of Anesthesiologists Physical Status Classification) AND (age) AND (signed informed consent form after reading the information about the study and talking with one of the investigators))"}
{"candidate_id": "LLM03518", "doc_id": "NCT02968342_inc", "case_bucket": "other", "source_criterion": "Menopausal status Sexually active", "candidate_expression": "((Menopausal) AND (Sexually active))"}
{"candidate_id": "LLM03519", "doc_id": "NCT03216447_exc", "case_bucket": "or", "source_criterion": "Patient has previously received or is receiving an organ transplant other than a liver. Patient currently requires dialysis Recipient or donor is known to be seropositive for human immunodeficiency virus (HIV) Patient has received a liver transplant from a non-heart beating donor Patient who is HCV negative has received an HCV positive (HCV RNA by PCR or HCV antibody) donor liver Patient who is HbsAg negative has received an HbsAg positive (HBV DNA by PCR or HBV antibody) donor liver Patient has received a liver transplant from a decrease donor > 70 years of age Patient has a current malignancy or a history of malignancy (within the past 5 years), except hepatocellular carcinoma within UCSF Criteria and basal or non-metastatic squamous cell carcinoma of skin that has been treated successfully. Patient is hemodynamically unstable on POD 15", "candidate_expression": "((HBV DNA) AND (HCV negative) AND (HCV positive) AND (HIV) AND (HbsAg negative) AND (HbsAg positive) AND (PCR) AND (POD 15) AND (UCSF Criteria) AND (age > 70 years) AND (dialysis) AND (donor) AND (donor heart beating) AND (donor liver) AND (hemodynamically unstable) AND (hepatocellular carcinoma) AND (human immunodeficiency virus seropositive) AND (liver transplant) AND (organ transplant liver) AND ((HCV RNA) OR (HCV antibody)) AND ((HBV antibody) OR (PCR)) AND ((history of malignancy within the past 5 years) OR (malignancy)) AND ((basal cell carcinoma of skin) OR (squamous cell carcinoma of skin non-metastatic)) AND ((Recipient) OR (donor)))"}
{"candidate_id": "LLM03520", "doc_id": "NCT02695992_inc", "case_bucket": "scope", "source_criterion": "Above 18 years of age Symptomatic, permanent AF of at least three months duration Resting heart rate =80 bpm Signed informed consent", "candidate_expression": "((AF at least three months duration permanent) AND (Resting heart rate =80 bpm) AND (Signed informed consent) AND (age Above 18 years Symptomatic))"}
{"candidate_id": "LLM03521", "doc_id": "NCT03264911_inc", "case_bucket": "other", "source_criterion": "3 -15 years old Clinical symptoms suggestive of pharyngitis with MC Isaac score =3 Rapid-antigen detection test (RADT) positive for GAS- Signed informed parental/patient consent form", "candidate_expression": "((3 -15 years) AND (=3) AND (Clinical symptoms suggestive of) AND (GAS-) AND (MC Isaac score) AND (RADT) AND (Rapid-antigen detection test) AND (Signed informed parental/patient consent form) AND (old) AND (pharyngitis) AND (positive))"}
{"candidate_id": "LLM03522", "doc_id": "NCT03297125_inc", "case_bucket": "other", "source_criterion": "Newly diagnosed glioblastoma (GBM), WHO grade IV.", "candidate_expression": "((GBM) AND (Newly diagnosed) AND (WHO) AND (glioblastoma) AND (grade IV))"}
{"candidate_id": "LLM03523", "doc_id": "NCT02818816_inc", "case_bucket": "other", "source_criterion": "Males aged 18 years and above Patients with a diagnosis of prostatic carcinoma requiring prostate surgery", "candidate_expression": "((Males) AND (aged 18 years and above) AND (prostate surgery) AND (prostatic carcinoma))"}
{"candidate_id": "LLM03524", "doc_id": "NCT02573597_exc", "case_bucket": "or", "source_criterion": "<37 weeks gestation, H/o Cesarean Section, Multiple Gestation, Pre-eclampsia, Narcotics within 3 hours prior to labor epidural placement, Chronic Pain (as defined by chronic opiate consumption), Women who are participating in another study that will impact protocol", "candidate_expression": "((Women who are participating in another study that will impact protocol) AND (gestation <37 weeks) AND (labor epidural placement) AND (opiate chronic) AND ((Cesarean Section) OR (Chronic Pain) OR (Multiple Gestation) OR (Narcotics within 3 hours prior to labor epidural placement) OR (Pre-eclampsia)))"}
{"candidate_id": "LLM03525", "doc_id": "NCT00445029_inc", "case_bucket": "other", "source_criterion": "For both groups: Patients aged from 18 to 65 years old. Both genders eligible for study. Female participants must use a contraceptive method. Feasibility of patch testing. Participants must be able to understand and sign the Informed Consent, and comply with all aspects of the protocol. Patients must be registered in a social security system or with a health insurance coverage  First group: allergic patients Patients with allergic contact dermatitis to para-phenylenediamine (PPD) based on a history of PPD contact dermatitis and positive PPD patch tests.  Second group : healthy volunteers No history of PPD allergic contact dermatitis, with a negative PPD patch test.", "candidate_expression": "((Both genders) AND (Feasibility of) AND (Female) AND (No) AND (PPD) AND (PPD patch test) AND (PPD patch tests) AND (aged) AND (allergic) AND (allergic contact dermatitis) AND (be able to) AND (comply with all aspects of the protocol) AND (contact dermatitis) AND (contraceptive method) AND (from 18 to 65 years old) AND (health insurance coverage) AND (healthy) AND (negative) AND (para-phenylenediamine (PPD)) AND (patch testing) AND (positive) AND (registered in a social security system) AND (understand and sign the Informed Consent))"}
```
