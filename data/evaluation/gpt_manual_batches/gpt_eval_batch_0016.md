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
{"candidate_id": "LLM00376", "doc_id": "NCT02874092_inc", "case_bucket": "scope", "source_criterion": "RA cohort: Receiving MTX at stable doses of 10 to 25 mg weekly for at least 12 weeks, Have a DAS28 of 3.2 or higher (The level of disease activity is considered to be low if the DAS28 is 3.2 or less) (Prevoo et al., 1995) OA cohort: Diagnosis of osteoarthritis made by physician.", "candidate_expression": "((DAS28 3.2 or higher) AND (MTX stable doses 10 to 25 mg weekly for at least 12 weeks) AND (OA) AND (RA) AND (osteoarthritis made by physician))"}
{"candidate_id": "LLM00377", "doc_id": "NCT00931983_exc", "case_bucket": "other", "source_criterion": "Other neuromuscular disease Contraindication to weight bearing on lower extremities Pressure sores where harness would be applied Uncontrollable hypotension when upright Lower limb contractures impeding range of motion necessary for ambulation Prior enrolment in a BWATT program Unable to commit to intervention for duration of protocol", "candidate_expression": "((Contraindication weight bearing on lower extremities) AND (Lower limb contractures range of motion necessary for ambulation) AND (Pressure sores) AND (Unable to commit to intervention for duration of protocol) AND (harness) AND (hypotension Uncontrollable when upright) AND (neuromuscular disease))"}
{"candidate_id": "LLM00378", "doc_id": "NCT02361905_exc", "case_bucket": "other", "source_criterion": "submucosal leiomyoma, endometrial hyperplasia with atypia, history of uterine surgery", "candidate_expression": "((endometrial hyperplasia) AND (history) AND (submucosal leiomyoma) AND (uterine surgery) AND (with atypia))"}
{"candidate_id": "LLM00379", "doc_id": "NCT02323399_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00380", "doc_id": "NCT03019562_inc", "case_bucket": "other", "source_criterion": "19-65 years of age ASA physical status classification I or II Scheduled for total hip replacement surgery", "candidate_expression": "((19-65 years) AND (ASA physical status classification) AND (I or II) AND (Scheduled for) AND (age) AND (total hip replacement surger))"}
{"candidate_id": "LLM00381", "doc_id": "NCT01440296_exc", "case_bucket": "other", "source_criterion": "any condition that would contra-indicate Magnetic Resonance Imaging or administration of contrast agent", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00382", "doc_id": "NCT03228654_exc", "case_bucket": "or", "source_criterion": "Suspected or known gynecological malignancy. uterine size >12 weeks. Endometriosis Presence of adnexal mass. cervix flushed with the vagina. presence of significant scarring in the pelvic area from previous surgery.", "candidate_expression": "((>12 weeks) AND (Endometriosis) AND (adnexal mass) AND (cervix flushed with the vagina) AND (from previous surgery) AND (gynecological malignancy) AND (pelvic area) AND (previous) AND (significant scarring) AND (surgery) AND (uterine size) AND ((Suspected) OR (known)))"}
{"candidate_id": "LLM00383", "doc_id": "NCT03091881_inc", "case_bucket": "other", "source_criterion": "Type I diabetic patients Parturients presented for Cesarean section", "candidate_expression": "((Cesarean section) AND (Parturients) AND (Type I diabetic))"}
{"candidate_id": "LLM00384", "doc_id": "NCT03216967_exc", "case_bucket": "or", "source_criterion": "Known proved BKV nephropathy Hypersensitivity to everolimus, sirolimus or excipient Concomitant treatment by leflunomide, cidofovir, sirolimus, Millepertuis (Hypericum Perforatum) Pregnant or lactating women Women of child bearing potential unless they are using a birth control method", "candidate_expression": "((BKV nephropathy) AND (Concomitant) AND (Hypericum Perforatum) AND (Hypersensitivity) AND (Millepertuis) AND (Pregnant) AND (Women) AND (birth control method) AND (child bearing potential) AND (cidofovir) AND (everolimus) AND (excipient) AND (lactating) AND (leflunomide) AND (proved) AND (sirolimus) AND (unless) AND (women))"}
{"candidate_id": "LLM00385", "doc_id": "NCT02427295_inc", "case_bucket": "other", "source_criterion": "Age 18 or older. Patients diagnosed with acromegaly with GH-secreting pituitary adenoma on sellar MRI, meeting the biochemical criteria outlined above (refer to 1. Diagnosis of acromegaly) and with typical acromegalic features. No prior use of somatostatin analogues. Adequate hepatic and renal function Provision of a signed written informed consent", "candidate_expression": "((18 or older) AND (Adequate hepatic function) AND (Adequate renal function) AND (Age) AND (GH-secreting pituitary adenoma) AND (No) AND (Provision of a signed written informed consent) AND (acromegalic features) AND (acromegaly) AND (biochemical criteria outlined above) AND (prior) AND (sellar MRI) AND (somatostatin analogues) AND (typical))"}
{"candidate_id": "LLM00386", "doc_id": "NCT02555163_exc", "case_bucket": "other", "source_criterion": "Non papillary gross features of the tumor Anteriorly located tumor Patients criteria Poor performance status History of BCG sepsis History of bladder irradiation Contracted bladder", "candidate_expression": "((BCG) AND (Contracted bladder) AND (Non papillary gross features) AND (bladder irradiation History) AND (performance status Poor) AND (sepsis History) AND (tumor) AND (tumor Anteriorly located))"}
{"candidate_id": "LLM00387", "doc_id": "NCT02678377_inc", "case_bucket": "or", "source_criterion": "Undergoing mid-urethral sling surgery Have symptoms of both stress and urgency urinary incontinence Able to consent, fill out study documents, and complete all study procedures and follow-up visits At least 18 years of age English speaking Be able and willing to learn clean intermittent self catheterization technique", "candidate_expression": "((Able to consent, fill out study documents, and complete all study procedures and follow-up visits) AND (At least 18 years) AND (age) AND (mid-urethral sling surgery) AND ((stress urinary incontinence) OR (urgency urinary incontinence)))"}
{"candidate_id": "LLM00388", "doc_id": "NCT03091881_inc", "case_bucket": "other", "source_criterion": "Type I diabetic patients Parturients presented for Cesarean section", "candidate_expression": "((Cesarean section) AND (Parturients) AND (Type I diabetic))"}
{"candidate_id": "LLM00389", "doc_id": "NCT03336801_exc", "case_bucket": "or", "source_criterion": "American Association of Anesthesiology class 1-3 American Heart Association class >3 BMI >37 Insulin treated diabetes Pregnancy or breast feeding Sensistivity/allergy against anesthetic agents Inadequate understanding about the study Depressed kidney function and/or AKI Depressed liver function Genetic malignant hyperthermia", "candidate_expression": "((1-3) AND (>3) AND (>37) AND (American Association of Anesthesiology class) AND (American Heart Association class) AND (BMI) AND (Depressed) AND (Depressed liver function) AND (Genetic) AND (Inadequate understanding about the study) AND (Insulin) AND (Insulin treated) AND (anesthetic agents) AND (diabetes) AND (kidney function) AND (liver function) AND (malignant hyperthermia) AND ((Pregnancy) OR (breast feeding)) AND ((Sensistivity) OR (allergy)) AND ((AKI) OR (Depressed kidney function)))"}
{"candidate_id": "LLM00390", "doc_id": "NCT00894712_inc", "case_bucket": "or", "source_criterion": "Must have pathologically confirmed invasive adenocarcinoma or ductal carcinoma in situ of the breast. Patients must have undergone segmental mastectomy (i.e., lumpectomy). Patients must not have received prior radiation therapy to the breast. Patients must not have active local-regional disease prior to registration. Patients must not be pregnant because of the potential for fetal harm as a result of radiation treatment. Women of child-bearing age will be given a serum pregnancy test prior to study entry to ensure they are not pregnant. They will also be counseled on the importance of avoiding pregnancy and hormonal contraception while undergoing radiation therapy. Patients must not have a serious medical or psychiatric illness which prevents informed consent or compliance with treatment. All patients must be informed of the investigational nature of this study and give written informed consent in accordance with institutional and federal guidelines.", "candidate_expression": "((All patients must be informed of the investigational nature of this study and give written informed consent in accordance with institutional and federal guidelines.) AND (Patients must not be pregnant because of the potential for fetal harm as a result of radiation treatment. Women of child-bearing age will be given a serum pregnancy test prior to study entry to ensure they are not pregnant. They will also be counseled on the importance of avoiding pregnancy and hormonal contraception while undergoing radiation therapy.) AND (Patients must not have a serious medical or psychiatric illness which prevents informed consent or compliance with treatment.) AND (active) AND (confirmed) AND (local-regional disease) AND (lumpectomy) AND (not) AND (of the breast) AND (pathologically) AND (radiation therapy) AND (segmental mastectomy) AND ((ductal carcinoma in situ) OR (invasive adenocarcinoma)))"}
{"candidate_id": "LLM00391", "doc_id": "NCT02905890_inc", "case_bucket": "other", "source_criterion": "BV positive by Nugent score HIV negative Capable of providing written informed consent", "candidate_expression": "((BV positive) AND (Capable of providing written informed consent) AND (HIV negative) AND (Nugent score))"}
{"candidate_id": "LLM00392", "doc_id": "NCT00122070_exc", "case_bucket": "or", "source_criterion": "Are pregnant or lactating. Have participated in any other studies involving investigational products within 30 days prior to entry into this study. Are undergoing an acute withdrawal syndrome from drugs or alcohol. Have an Axis I diagnosis of Schizophrenia, Schizoaffective Disorder, Schizophreniform Disorder or Bipolar I Disorder as diagnosed by the Structured Clinical Interview for DSM-IV Axis I Disorders (SCID-I), and pertinent subsequent for ruling out exclusionary diagnoses. Have an unstable medical disorder as determined by physical examination or laboratory testing. The primary investigator will be responsible for making this judgment based on the above. Had an unsatisfactory response to a previous adequate trial of quetiapine as judged by a study investigator. Patients cannot begin psychotherapy during the study period, but may continue if started prior to the study. Patients who are currently receiving quetiapine therapy may not undergo a washout period and then restart quetiapine in the study.", "candidate_expression": "((Bipolar I Disorder) AND (Have participated in any other studies involving investigational products) AND (Schizoaffective Disorder) AND (Schizophrenia) AND (Schizophreniform Disorder) AND (Structured Clinical Interview for DSM-IV Axis I Disorders (SCID-I)) AND (acute withdrawal syndrome) AND (alcohol) AND (drugs) AND (entry into this stud) AND (lactating) AND (pregnant) AND (within 30 days prior to entry into this study))"}
{"candidate_id": "LLM00393", "doc_id": "NCT02330757_exc", "case_bucket": "or", "source_criterion": "PCOS or polycystic ovary on ultrasound scan. Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities or myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Previous) AND (endometriosis) AND (ultrasound scan) AND (uterine surgery) AND ((PCOS) OR (polycystic ovary)) AND ((Uterine abnormalities) OR (myoma)) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM00394", "doc_id": "NCT02225548_exc", "case_bucket": "or", "source_criterion": "Subject unwilling to cease use of any treatment for erectile dysfunction during the study, including oral medication, vacuum devices, constrictive devices, injections, urethral suppositories, gels, any over-the-counter or nonprescription medications, and products purchased via the internet Subject receiving dopamine agonists, nitrates, alpha-receptor blocking agents, or antihypertensive medication (see other exclusionary medications listed below) Subject with a history of syncope within the last 6 months prior to screening Subject with symptomatic postural hypotension (severe dizziness or fainting Subject with hypotension and a resting systolic blood pressure of < 90 mmHG or hypertension with a resting systolic blood pressure > 170 mmHG or a resting diastolic blood pressure > 110 mmHG Subject with any underlying cardiovascular condition, including unstable angina pectoris, which preclude sexual activity Subject with a history of myocardial infarction, stroke or life-threatening arrhythmia within 6 months prior to screening Subject with uncontrolled atrial fibrillation/flutter at screening (defined as ventricular response rate = 100 bpm) Subject with a bleeding disorder Subject with a history of prostatectomy because of prostate cancer, including nerve sparing techniques. Subjects with a history of surgical procedures for the treatment of benign prostate hypertrophy are permitted, with the exception of cryosurgery, cryotherapy or cryoablation Subject with hereditary degenerative retinal disorders such as retinitis pigmentosa Subject with a history of loss of vision because of non-arteritic anterior ischemic optic neuropathy (NAION), history of temporary or permanent loss of vision, including unilateral loss of vision Subject with a history of congenital QT prolongation Subject with a penile anatomical abnormality (e.g., penile fibrosis, fractures, or Peyronie's disease) which, in the investigator's opinion, could significantly impair sexual performance. This will be based on subject's reported medical history (penile exam not required) Subject with primary hypoactive sexual desire. Subject with a spinal cord injury Subject with a severe chronic or acute liver disease, history of moderate (Child-Pugh B), or severe (Child-Pugh C) hepatic impairment Subject with clinically significant chronic hematological disease which could lead to priapism such as sickle cell anemia, multiple myeloma, and leukemia Subject with active peptic ulceration Subject with a history of malignancy within the past 5 years (other than squamous or basal cell skin cancer) Subject with a history of a positive test for Hepatitis B surface antigen (HbsAg) or Hepatitis C Subject with a known hypersensitivity to any component of the investigational medications, monoamine oxidase inhibitors, phosphodiesterase type 5 inhibitors or phenylethylamines Subjects with a history of drug or alcohol abuse within the past 6 months Subjects currently consuming =5 units of alcohol per day Subject who is illiterate or unable to understand the Informed Consent Form, questionnaires or subject diary Subject who, in the opinion of the investigator, will be noncompliant with the visit schedule or study procedures Subject with any unstable medical, psychiatric, or substance abuse disorder that in the opinion of the investigator is likely to affect the subject's ability to complete the study or preclude the subject's participation in the study Diagnosis of any other neurologic disease Uncontrolled Diabetes (Hemoglobin A1C > 7.5)", "candidate_expression": "((< 90 mmHG) AND (= 100 bpm) AND (=5 units) AND (> 110 mmHG) AND (> 170 mmHG) AND (> 7.5) AND (B) AND (C) AND (Child-Pugh) AND (Diabetes) AND (Hemoglobin A1C) AND (NAION) AND (Peyronie's disease)) AND (Uncontrolled) AND (active) AND (acute liver disease) AND (alcohol abuse) AND (alpha-receptor blocking agents) AND (antihypertensive medication) AND (any other) AND (arrhythmia) AND (at screening) AND (atrial fibrillation) AND (atrial flutter) AND (basal cell skin cancer) AND (benign prostate hypertrophy) AND (bleeding disorder) AND (cardiovascular condition) AND (cease use of) AND (chronic) AND (chronic liver disease) AND (clinically significant) AND (congenital QT prolongation) AND (constrictive devices) AND (consuming alcohol per day) AND (could lead to priapism) AND (could significantly impair sexual performance) AND (cryoablation) AND (cryosurgery) AND (cryotherapy) AND (currently) AND (diastolic blood pressure) AND (dizziness) AND (dopamine agonists) AND (drug abuse) AND (during the study) AND (erectile dysfunction) AND (fainting) AND (gels) AND (hematological disease) AND (hepatic impairment) AND (hereditary degenerative retinal disorders) AND (history of) AND (hypersensitivity) AND (hypertension) AND (hypotension) AND (illiterate) AND (impair sexual performance) AND (injections) AND (investigational) AND (leukemia) AND (life-threatening) AND (likely to affect the subject's ability to complete the study) AND (loss of vision) AND (malignancy) AND (medical disorder) AND (medications) AND (moderate) AND (monoamine oxidase inhibitors) AND (multiple myeloma) AND (myocardial infarction) AND (nerve sparing techniques) AND (neurologic disease) AND (nitrates) AND (non-arteritic anterior ischemic optic neuropathy) AND (noncompliant with the visit schedule or study procedure) AND (nonprescription) AND (oral medication) AND (other than) AND (over-the-counter) AND (penile anatomical abnormality) AND (penile exam) AND (penile fibrosis) AND (penile fractures) AND (peptic ulceration) AND (permanent) AND (permitted) AND (phenylethylamines) AND (phosphodiesterase type 5 inhibitors) AND (positive) AND (postural hypotension) AND (preclude) AND (preclude the subject's participation in the study) AND (priapism) AND (primary hypoactive sexual desire) AND (prostate cancer) AND (prostatectomy) AND (psychiatric disorder) AND (retinitis pigmentosa) AND (screening) AND (severe) AND (sexual activity) AND (sickle cell anemia) AND (spinal cord injury) AND (squamous skin cancer) AND (stroke) AND (substance abuse disorder) AND (surgical procedures) AND (symptomatic) AND (syncope) AND (systolic blood pressure) AND (temporary) AND (test for Hepatitis B surface antigen (HbsAg)) AND (test for Hepatitis C) AND (the past 6 months) AND (treatment) AND (unable to) AND (uncontrolled) AND (understand the Informed Consent Form) AND (understand the questionnaires) AND (understand the subject diary) AND (unilateral) AND (unstable) AND (unstable angina pectoris) AND (unwilling) AND (urethral suppositories) AND (vacuum devices) AND (ventricular response rate) AND (with the exception of) AND (within 6 months prior to screening) AND (within the last 6 months prior to screening) AND (within the past 5 years) AND (within the past 6 months))"}
{"candidate_id": "LLM00395", "doc_id": "NCT01084993_inc", "case_bucket": "or", "source_criterion": "At least two of the following additional criteria At least 70 yrs old Female gender Diabetes Creatinine clearance <60mL/min History of gastro-intestinal or other organ bleeding Baseline anemia Current treatment with glycoproteins IIb-IIIa inhibitors", "candidate_expression": "((<60mL/min) AND (At least 70 yrs) AND (At least two) AND (Baseline) AND (Creatinine clearance) AND (Current) AND (Diabetes) AND (Female) AND (History) AND (anemia) AND (glycoproteins IIb-IIIa inhibitors) AND (old) AND (other) AND (treatment) AND ((gastro-intestinal bleeding) OR (organ bleeding)))"}
{"candidate_id": "LLM00396", "doc_id": "NCT02827526_inc", "case_bucket": "or", "source_criterion": "Patients presenting for elective posterior spinal fusion surgery (lower thoracic, lumbar, sacral) Ages 18-80", "candidate_expression": "((Ages 18-80 sacral) AND (posterior spinal fusion surgery elective lower thoracic lumbar))"}
{"candidate_id": "LLM00397", "doc_id": "NCT00235170_exc", "case_bucket": "or", "source_criterion": "1. Congestive heart failure; 2. CABG or Percutaneous Coronary Intervention (PCI) procedure; 3. Planned need for major surgery (e.g. valve surgery or resection of aortic or left ventricular aneurysm, carotid end-arterectomy, abdominal aortic aneurysm surgery etc.); 4. Congenital heart disease; 5. Transmural myocardial infarction within the previous seven days and CK has not returned to normal; 6. Chest pain lasting longer than 30 minutes within 12 hours pre-procedure, if CK enzymes positive (≥ 2x the normal upper limit). 7. History of any cerebrovascular accident; 8. Left main stenosis of 50% or more; 9. Intention to treat more than 1 totally occluded major epicardial vessel; 10. Single vessel (single territory) disease.", "candidate_expression": "((CK enzymes positive ≥ 2x the normal upper limit) AND (CK normal) AND (Chest pain lasting longer than 30 minutes within 12 hours pre-procedure) AND (Congenital heart disease) AND (Congestive heart failure) AND (History of) AND (Left main stenosis 50% or more) AND (Single vessel disease) AND (Transmural myocardial infarction within the previous seven days) AND (any cerebrovascular accident) AND (single territory disease) AND (treat Intention to totally occluded major epicardial vessel) AND ((CABG) OR (Percutaneous Coronary Intervention (PCI))) AND ((abdominal aortic aneurysm surgery) OR (carotid end-arterectomy) OR (major surgery) OR (resection of aortic aneurysm) OR (resection of left ventricular aneurysm) OR (valve surgery)))"}
{"candidate_id": "LLM00398", "doc_id": "NCT02541955_exc", "case_bucket": "or", "source_criterion": "Prior treatment with Acthar in the past 2mos Meet one of the above RA flare requirements Subjects who have received live or live attenuated vaccines within 6 weeks prior to the first dose of study drug (or the zoster vaccine)", "candidate_expression": "((Acthar in the past 2mos) AND (RA flare requirements one of) AND (study drug first dose) AND (treatment Prior) AND (zoster vaccine) AND ((live attenuated vaccines) OR (live vaccines)))"}
{"candidate_id": "LLM00399", "doc_id": "NCT01346436_inc", "case_bucket": "other", "source_criterion": "women proven pelvic floor dysfunction informed consent", "candidate_expression": "((nformed consent) AND (pelvic floor dysfunction) AND (women))"}
{"candidate_id": "LLM00400", "doc_id": "NCT02437084_exc", "case_bucket": "or", "source_criterion": "Less than 30 yrs of age or > 65 yrs of age Any significant co-morbidities, such as active heart, kidney, or liver diseases, accelerated or malignant hypertension, heart failure, severe anemia.", "candidate_expression": "((age > 65 yrs) AND (age Less than 30 yrs) AND (co-morbidities significant) AND ((accelerated) OR (malignant)) AND ((diseases heart) OR (diseases kidney) OR (heart failure) OR (hypertension) OR (liver diseases) OR (severe anemia)))"}
```
