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
{"candidate_id": "LLM04851", "doc_id": "NCT03124329_inc", "case_bucket": "or", "source_criterion": "Male and female individuals between ages of 18 to 70 years old Multiple contiguous gingival recession defects on a minimum of two adjacent teeth, exhibiting 3mm or more recession on at least one of those teeth No prior surgical treatment in the sites planned for therapy Minimum of 2 mm of keratinized gingiva Absence of cervical restorations extending to the CEJ Miller class 1, 2 and 3 recession defects will be included Availability to undergo treatment and return for follow up visits at specified post-operative intervals", "candidate_expression": "((Miller class 1, 2 and 3) AND (ages between 18 to 70 years old) AND (gingival recession defects Multiple minimum of two) AND (keratinized gingiva Minimum of 2 mm) AND (recession 3mm or more at least one) AND (recession defects) AND NOT (cervical restorations extending to the CEJ) AND NOT (surgical treatment))"}
{"candidate_id": "LLM04852", "doc_id": "NCT03198910_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04853", "doc_id": "NCT02593409_inc", "case_bucket": "other", "source_criterion": "age =18 at screening not intending to move away from the clinic's catchment area for the next 2 years HIV-1 antibody negative reports commercial sex work contact information is provided written informed consent", "candidate_expression": "((HIV-1 antibody negative) AND (age =18) AND (commercial sex work) AND (contact information is provided) AND (written informed consent))"}
{"candidate_id": "LLM04854", "doc_id": "NCT02876484_exc", "case_bucket": "or", "source_criterion": "Fasting plasma glucose > 7,0 mM, HbA1c > 48 mmol/mol 3 months after RYGB. Dysregulated thyroid diseases, use of antithyroid treatment. Late diabetic complications as retinopathy, renal insufficiency, neuropathy or previous pancreatitis. Complications to RYGB. Documented reactive hypoglycaemia, severe dumping (vomiting, diarrhea, severe abdominal pain after food intake). Cholecystectomy", "candidate_expression": "((Cholecystectomy) AND (Complications) AND (Fasting plasma glucose > 7,0 mM) AND (HbA1c > 48 mmol/mol) AND (Late diabetic complications) AND (RYGB) AND (abdominal pain severe after food intake) AND (antithyroid treatment) AND (diarrhea) AND (dumping severe) AND (neuropathy) AND (pancreatitis previous) AND (reactive hypoglycaemia) AND (renal insufficiency) AND (retinopathy) AND (thyroid diseases Dysregulated) AND (vomiting))"}
{"candidate_id": "LLM04855", "doc_id": "NCT02969876_inc", "case_bucket": "or", "source_criterion": "Meets Diagnostic and Statistical Manual of Mental Disorders (Versions 4 and 5) criteria for and Major Depressive Disorder. Hamilton Depression Rating Scale-17 score greater than 18. Men and women between ages >=18 and 65.", "candidate_expression": "((Diagnostic and Statistical Manual of Mental Disorders criteria Versions 4 Versions 5) AND (Hamilton Depression Rating Scale greater than 18) AND (Major Depressive Disorder) AND (Men) AND (ages between 18 and 65) AND (women))"}
{"candidate_id": "LLM04856", "doc_id": "NCT00931983_inc", "case_bucket": "or", "source_criterion": "Children between the ages of 4-18 with incomplete ASIA C or D spinal cord injuries at least 12 months before study enrolment Non-ambulatory or 'exercise only' ambulators with or without assistive devices Normal motor and cognitive development up to time of injury Medical Stability", "candidate_expression": "(('exercise only' ambulators) AND (ASIA C or D) AND (Children) AND (Medical Stability) AND (Non-ambulatory) AND (ages 4-18) AND (assistive devices) AND (cognitive development) AND (motor development time of injury) AND (spinal cord injuries incomplete at least 12 months before study enrolment study enrolment))"}
{"candidate_id": "LLM04857", "doc_id": "NCT01774019_exc", "case_bucket": "or", "source_criterion": "Biliary strictures caused by confirmed benign tumors Biliary strictures caused by malignancies other than pancreatic cancer, distal CBD cholangiocarcinoma and other periampullary cancers Surgically altered biliary tract anatomy, not including prior cholecystectomy Neoadjuvant chemotherapy for current malignancy Palliative indication due to reasons other than surgical candidate status Previous biliary drainage by ERCP/PTC Patients for whom endoscopic techniques are contraindicated Participation in another investigational trial within 90 days Pregnancy", "candidate_expression": "((Biliary strictures) AND (Neoadjuvant chemotherapy) AND (Pregnancy) AND (Surgically altered biliary tract anatomy) AND (benign tumors confirmed) AND (biliary drainage by ERCP/PTC Previous) AND (contraindicated) AND (distal CBD cholangiocarcinoma) AND (endoscopic techniques) AND (malignancies) AND (malignancy) AND (other periampullary cancers) AND (pancreatic cancer) AND NOT (cholecystectomy prior))"}
{"candidate_id": "LLM04858", "doc_id": "NCT02721017_exc", "case_bucket": "or", "source_criterion": "age less than 13 years at time of procedure use of pain medication prior to procedure pectus carinatum, Poland's syndrome, or any chest wall anomaly other than pectus excavatum previous repair of pectus excavatum by any technique previous thoracic surgery congenital heart disease bleeding dyscrasia major anesthetic risk factors or history of previous problem with anesthesia pregnancy inability to communicate in English", "candidate_expression": "((Poland's syndrome) AND (age) AND (anesthetic risk factors) AND (at time of procedure) AND (bleeding dyscrasia) AND (chest wall anomaly) AND (congenital heart disease) AND (inability to communicate in English) AND (less than 13 years) AND (major) AND (other than) AND (pain medication) AND (pectus carinatum) AND (pectus excavatum) AND (pregnancy) AND (previous) AND (prior to procedure) AND (problem with anesthesia) AND (repair of pectus excavatum) AND (thoracic surgery))"}
{"candidate_id": "LLM04859", "doc_id": "NCT02167022_inc", "case_bucket": "other", "source_criterion": "1. Age: 12 to 36 months of age (The diagnosis of CP is often uncertain under the age of 12 months. The cutoff at 36 months is to have a population of young children when the brain is most \"plastic\" and most susceptible to reorganization). 2. Diagnosis: Diagnosis of spastic CP confirmed by a pediatric neurologist or pediatric rehabilitation specialist. 3. Etiology: The insult to the central nervous system that caused the motor dysfunction must have occurred during gestation or within one year after birth independent of gestational age. 4. Disease severity level: Gross Motor Function Classification System (GMFCS) levels I, II and III.", "candidate_expression": "((Age 12 to 36 months of age) AND (Gross Motor Function Classification System (GMFCS) levels I, II and III) AND (one year after birth) AND (spastic CP))"}
{"candidate_id": "LLM04860", "doc_id": "NCT02707874_exc", "case_bucket": "or", "source_criterion": "Patients who undergo iliac crest bone graft harvesting as part of their surgery Preexisting neurological deficits or peripheral neuropathy in the distribution of the sciatic nerve Local infection Contraindication to regional anesthesia e.g. bleeding diathesis, coagulopathy Chronic pain disorders History of use of over 30mg oxycodone or equivalent per day Allergy to local anesthetics History of significant psychiatric conditions that may affect patient assessment Pregnancy Inability to provide informed consent", "candidate_expression": "((Allergy) AND (Chronic pain) AND (Contraindication) AND (Inability to provide informed consent) AND (Local infection) AND (Pregnancy) AND (iliac crest bone graft harvesting) AND (local anesthetics) AND (over 30mg per day) AND (regional anesthesia) AND (sciatic nerve) AND ((oxycodone) OR (oxycodone equivalent)) AND ((neurological deficits) OR (peripheral neuropathy)) AND ((bleeding diathesis) OR (coagulopathy)))"}
{"candidate_id": "LLM04861", "doc_id": "NCT02399033_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04862", "doc_id": "NCT02689089_exc", "case_bucket": "or", "source_criterion": "Suspected or confirmed active TB disease Known allergies to any of the study medications by participant self-report have a positive pregnancy test at screening, or are not willing to use a reliable method of barrier contraception during the study, or are breastfeeding hormonal contraception HIV infected participants who are on anti-retroviral drugs other drugs that interact with 3HP (see Table 1) Known contact with an INH or rifampin resistant case Weight < 10 kg Evidence of possible liver damage defined by an aspartate transaminase (AST) level that is more than 3x the upper limit of normal in an asymptomatic patient Porphyria reported by patient Inability to adhere to protocol. Patients may be excluded from the study for other reasons, at the investigator's discretion with detailed documentation.", "candidate_expression": "((AST) AND (HIV infected) AND (Inability to adhere to protocol) AND (Porphyria) AND (Weight < 10 kg) AND (active TB) AND (allergies) AND (anti-retroviral drugs) AND (are breastfeeding) AND (are not willing to use a reliable method of barrier contraception during the study) AND (aspartate transaminase more than 3x the upper limit of normal) AND (have a positive pregnancy test at screening) AND (hormonal contraception) AND (liver damage) AND (resistant) AND ((INH) OR (rifampin)))"}
{"candidate_id": "LLM04863", "doc_id": "NCT02632266_inc", "case_bucket": "or", "source_criterion": "Inborn preterm infants born between 28 0/7 and 34 0/7 weeks gestation and fed either mother's own milk or donor human milk", "candidate_expression": "((Inborn) AND (gestation between 28 0/7 and 34 0/7 weeks) AND (infants) AND (preterm) AND ((donor human milk fed) OR (fed mother's own milk)))"}
{"candidate_id": "LLM04864", "doc_id": "NCT02560389_inc", "case_bucket": "or", "source_criterion": "25-50 years of age PTSD related to physical or sexual assault Medically healthy English speaking", "candidate_expression": "((25-50 years) AND (English speaking) AND (Medically healthy) AND (PTSD) AND (age) AND (physical assault) AND (sexual assault))"}
{"candidate_id": "LLM04865", "doc_id": "NCT01483118_exc", "case_bucket": "or", "source_criterion": "Current pregnancy or lactation Liver disease or elevated liver enzymes Established diagnosis of diabetes mellitus Abnormal serum glucose levels either at fasting or after the 2-hr oral glucose tolerance test meeting criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association. Insulin sensitizing treatment within 3 months prior to or during the eight week study period. Hormonal treatment involving estrogen or progesterone 3 months prior to or during the study period, with the exception of medroxyprogesterone acetate for withdrawal bleeding. Systemic or inhaled corticosteroids. Known hypersensitive reaction to cinnamon. Patients with seizure disorders, known cardiovascular disease, or cerebrovascular disease. Body mass index (BMI)range 20-50 (excluding all women with BMI under 20 or over 50).", "candidate_expression": "((2-hr oral glucose tolerance test) AND (3 months prior to the study period) AND (Abnormal) AND (Abnormal serum glucose levels) AND (Body mass index (BMI)) AND (Insulin sensitizing treatment) AND (Liver disease) AND (Systemic) AND (Systemic corticosteroids) AND (after the 2-hr oral glucose tolerance test) AND (at fasting) AND (cardiovascular disease) AND (cerebrovascular disease) AND (cinnamon) AND (criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association) AND (diabetes mellitus) AND (during the eight week study period) AND (during the study period) AND (elevated) AND (elevated liver enzymes) AND (estrogen) AND (exception) AND (fasting) AND (hypersensitive reaction to cinnamon) AND (inhaled) AND (inhaled corticosteroids) AND (lactation) AND (liver enzymes) AND (medroxyprogesterone acetate) AND (meeting) AND (meeting criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association) AND (pregnancy) AND (progesterone) AND (range 20-50) AND (seizure disorders) AND (serum glucose levels) AND (the 2-hr oral glucose tolerance test) AND (withdrawal bleeding) AND (within 3 months prior to eight week study period))"}
{"candidate_id": "LLM04866", "doc_id": "NCT02652572_inc", "case_bucket": "or", "source_criterion": "1. Age 18 years or older 2. Diagnosis of venous leg ulcer(s), as clinically determined by the investigator by a positive venous reflux test (venous refilling <20 seconds) using Doppler ultrasound for at least 4 weeks prior to screening day, which have not adequately responded to conventional ulcer therapy. 3. Designated venous leg ulcer meets the following criteria at both the screening and baseline visits. If the patient has multiple ulcers, at least one ulcer must meet the following criteria at both the screening and baseline visits: 1. Present for at least 4 weeks 2. CEAP Classification Stage 6 3. Surface ulcer with an area > 15cm2 post debridement 4. Viable, granulating wound (investigator discretion) 4. Ulcers that extend through the epidermis but not through the muscle, tendon, or bone (Stage II or III ulcers as defined by the IAET). 5. Female patients of childbearing potential must have a negative pregnancy test at screening and must agree to use hormonal contraceptive, intrauterine device, diaphragm with spermicide, condom with spermicide, or abstinence throughout until 2 weeks after the last administration of study drug 6. Signed informed consent", "candidate_expression": "((Age 18 years or older) AND (CEAP Classification Stage 6 Present) AND (Doppler ultrasound at least 4 weeks prior to screening day) AND (Female) AND (IAET Stage II or III) AND (Signed informed consent) AND (Surface ulcer) AND (Ulcers extend through the epidermis extend through the muscle extend through the tendon extend through the bone) AND (abstinence) AND (area post debridement > 15cm2) AND (childbearing potential) AND (condom with spermicide) AND (conventional ulcer therapy responded) AND (diaphragm with spermicide) AND (hormonal contraceptive) AND (intrauterine device) AND (investigator discretion) AND (pregnancy test negative at screening) AND (ulcer at least one) AND (ulcers) AND (ulcers multiple) AND (venous leg ulcer) AND (venous leg ulcer(s)) AND (venous refilling <20 seconds) AND (venous reflux test positive) AND (wound Viable granulating))"}
{"candidate_id": "LLM04867", "doc_id": "NCT02959580_inc", "case_bucket": "other", "source_criterion": "Idiopathic Granulomatous Mastitis", "candidate_expression": "(Idiopathic Granulomatous Mastitis)"}
{"candidate_id": "LLM04868", "doc_id": "NCT03164304_exc", "case_bucket": "or", "source_criterion": "Women with Non-proteinuric hypertension severe renal impairment Myasthenia gravis High amount of magnesium in blood Low or high amount of calcium in blood Myocardial damage, diabetic coma, heart block", "candidate_expression": "((High amount) AND (Low amount) AND (Myasthenia gravis) AND (Myocardial damage) AND (Non-proteinuric hypertension) AND (Women) AND (calcium in blood) AND (diabetic coma) AND (heart block) AND (high amount) AND (magnesium in blood) AND (renal impairment) AND (severe))"}
{"candidate_id": "LLM04869", "doc_id": "NCT00391690_inc", "case_bucket": "or", "source_criterion": "Patients with histologically confirmed diagnosis of prostate cancer who have not yet developed bone metastases Prostate cancer patients with a rise in PSA under hormone therapy. PSA criteria: Patients who have undergone prostatectomy: any rise in PSA or Patients without prostatectomy: 2 consecutive rises in PSA levels relative to a previous reference value, separated by one month. The first measurement must occur one month after the reference value and must be above the reference value. The second confirmatory measurement taken one month after the first measurement must be greater than the first measurement. Previous chemotherapy or radiotherapy must have been performed ≥ 8 weeks prior to study entry. Eastern Cooperative Oncology Group (ECOG) score of 0, 1 or 2 (patients that spend less than 50% of time in bed during the day) Adequate liver function - serum total bilirubin concentration less than 1.5 x upper limit of normal value Age: ≥ 18 years Patient has given written informed consent prior to any study-specific procedures. Patients with psychiatric or addictive disorders which prevent them from giving their informed consent must not enter the study.", "candidate_expression": "((0, 1 or 2) AND (2) AND (Adequate) AND (Age) AND (Eastern Cooperative Oncology Group (ECOG) score) AND (PSA) AND (PSA levels) AND (Previous) AND (Prostate cancer) AND (above the reference value) AND (addictive disorders) AND (bone metastases) AND (chemotherapy) AND (confirmed) AND (consecutive) AND (first) AND (giving informed consent) AND (greater than the first measurement) AND (histologically) AND (hormone therapy) AND (less than 1.5 x upper limit of normal value) AND (less than 50%) AND (liver function) AND (measurement) AND (one month after the first measurement) AND (one month after the reference value) AND (prevent) AND (prostate cancer) AND (prostatectomy) AND (psychiatric disorders) AND (radiotherapy) AND (rise) AND (rises) AND (second) AND (separated by one month) AND (serum total bilirubin concentration) AND (spend time in bed during the day) AND (without) AND (≥ 18 years) AND (≥ 8 weeks prior to study entry))"}
{"candidate_id": "LLM04870", "doc_id": "NCT02744976_inc", "case_bucket": "other", "source_criterion": "age =18 and <75 years; patients with stable coronary artery disease referred to PCI in an artery suitable for IVUS pullback; signed informed consent before PCI.", "candidate_expression": "((PCI referred to artery suitable for IVUS pullback) AND (age =18 and <75 years) AND (coronary artery disease stable) AND (signed informed consent before PCI))"}
{"candidate_id": "LLM04871", "doc_id": "NCT02627560_exc", "case_bucket": "or", "source_criterion": "pregnant or breastfeeding known thromboembolic disease or with high risk of thromboembolism, warranting extra anticoagulation in connection with the procedure known allergy to tranexamic acid/Cyklokapron®", "candidate_expression": "((Cyklokapron) AND (allergy) AND (extra anticoagulation) AND (high risk of) AND (tranexamic acid) AND ((breastfeeding) OR (pregnant)) AND ((thromboembolic disease) OR (thromboembolism)))"}
{"candidate_id": "LLM04872", "doc_id": "NCT03338296_exc", "case_bucket": "or", "source_criterion": "Clinically significant new illness within 1 month before randomization that may affect the participant's ability to fulfill the study requirements or significantly confound the assessments Participants who cannot swallow investigational products Participants with T2DM who have hypoglycemia unawareness Aortic regurgitation mild or greater Mitral regurgitation moderate or greater Mitral or aortic valve stenosis greater than mild (ie, aortic stenosis: jet >3.0 meters per second [m/s], mean gradient >25 millimeters of mercury [mmHg], and aortic valve area <1.5 centimeters squared [cm^2]; mitral stenosis: mean gradient >5 mmHg and mitral valve area <1.5 cm^2) Systolic pulmonary artery pressure (SPAP) >40 mmHg (and/or tricuspid regurgitation [TR] jet velocity >2.9 m/s) In cases where an actual SPAP value is not measurable due to lack of adequate TR jet, the pulmonary flow acceleration time measured at the right ventricular outflow tract (RVOTAT) will be used to assess eligibility. Participants with a RVOTAT =100 milliseconds (msec) will be excluded, suggesting an elevated mean SPAP; eligibility for the those participants with RVOTAT between 100 and 120 msec will be determined based on combined assessment of the TR jet, septal motion, and right ventricular size. Left ventricular ejection fraction <45% Intracardiac mass, tumor, or thrombus Evidence of congenital heart disease Clinically significant pericardial effusion (eg, moderate or larger or with hemodynamic compromise) Significant renal or hepatic disease as evidenced by a serum creatinine greater than 1.5× upper limit of normal (ULN), serum transaminases greater than 3× ULN, or total bilirubin greater than 1.5× ULN in absence of Gilbert's syndrome Any suicidal ideation with intent with or without a plan, at the time of or within 6 months of Screening, as indicated by answering \"Yes\" to questions 4 or 5 on the Suicidal Ideation section of the Columbia-Suicide Severity Rating Scale (C-SSRS) Any suicidal behavior in the past based on the C-SSRS Any history of anorexia or bulimia within 2 years before Screening, Attention Deficit Hyperactivity Disorder, any Diagnostic and Statistical Manual of Mental Disorders, 5th Edition depressive disorder, bipolar disorder, or schizophrenia Known secondary causes (genetic, endocrine, or metabolic) for obesity (eg, Prader-Willi syndrome, Bardet Biedl syndrome, Down's Syndrome, untreated hypothyroidism, Cushing's syndrome, daily systemic corticosteroid exposure for longer than 30 days, history of significant exposure to corticosteroids for chronic illness during the past year; inhaled steroids will be allowed) Use of other products intended for weight loss including prescription drugs, over-the-counter (OTC) drugs, and herbal preparations within 1 month before Screening selective serotonin reuptake inhibitors serotonin norepinephrine reuptake inhibitors tricyclic antidepressants bupropion triptans St. John's Wort tryptophan linezolid dextromethorphan in any form (eg, OTC cold medicines) lithium tramadol antipsychotics or other dopamine antagonists antiseizure medications including valproic acid, zonisamide, topiramate, and lamotrigine oral steroids (topical and inhaled steroids are acceptable) stimulant medications (eg, Ritalin, Concerta, Biphetamine, and Dexedrine) benzodiazepines Use of drugs known to increase the risk for cardiac valvulopathy within 6 months before Screening, including but not limited to pergolide, ergotamine, methysergide, and cabergoline History or evidence of clinically significant disease (eg, malignancy; cardiac, respiratory, gastrointestinal, renal, or psychiatric disease) other than prediabetes (impaired fasting glucose or impaired glucose tolerance), type 2 diabetes treated with oral anti-diabetic agents (excluding sulfonylurea) or non-insulin injectable antidiabetic agents, obstructive sleep apnea, dyslipidemia, and nonalcoholic fatty liver disease Use of Belviq XR within 6 months before Screening or hypersensitivity to Belviq XR or any of the excipients Significant change in diet or level of physical activity within 1 month before dosing or change in weight of more than 5 kg within 3 months before Screening Any use of a very-low-calorie (<1000 calories/day) weight loss diet within 6 months before Screening History of alcohol or drug dependence or abuse Recreational drug use within 2 years before Screening Known to be human immunodeficiency virus positive Known to have active viral hepatitis (B or C) Malignancy within 5 years before Screening Unable to attend scheduled visits (eg, lack of transportation) or lack of a caregiver or guardian to supervise study participation Special needs participants who are unable to comprehend study-related instructions (eg, mild to profound mental retardation [intelligence quotient <70], moderate to severe cognitive developmental delay, pervasive development disorders, autism) Ongoing epilepsy or other seizure disorder, or use of medications for a seizure disorder within 6 months of screening or any time between screening and randomization Participants with a blood pressure in the 95th percentile or greater for age, sex, and height on 2 separate readings recorded on 2 separate days. Those participants who had uncontrolled hypertension at Screening can be rescreened more than 1 month after initiation or adjustment of antihypertensive therapy 1 time. Currently enrolled in another clinical study or has used any investigational drug or device within 30 days before providing informed consent Planned bariatric surgery during the study or prior bariatric surgical procedures Not suitable to participate in the study in the opinion of the investigator, including consideration of any existing physical, medical, or mental condition that prevents compliance with the protocol Female participants who are breastfeeding or pregnant at Screening or Baseline (as documented by a positive beta-human chorionic gonadotropin test). A separate Baseline assessment is required if a negative screening pregnancy test was obtained more than 72 hours before the first dose of study drug. Had unprotected sexual intercourse within 30 days before study entry and who do not agree to use a highly effective method of contraception (eg, total abstinence, an intrauterine device, a double-barrier method [such as condom plus diaphragm with spermicide], a contraceptive implant, an oral contraceptive, or have a vasectomized partner with confirmed azoospermia) throughout the entire study period and for 28 days after study drug discontinuation Are currently abstinent and do not agree to use a double-barrier method (as described above) or refrain from sexual activity during the study period and for 28 days after study drug discontinuation Are using hormonal contraceptives, but are not on a stable dose of the same hormonal contraceptive product for at least 4 weeks before dosing and who do not agree to use the same contraceptive during the study and for 28 days after study drug discontinuation (Note: All female participants will be considered to be of childbearing potential unless they have been sterilized surgically [ie, bilateral tubal ligation, total hysterectomy, or bilateral oophorectomy, all with surgery at least 1 month before dosing]).", "candidate_expression": "((2 separate days) AND (2 separate readings) AND (95th percentile or greater) AND (<1.5 centimeters squared [cm^2]) AND (<1.5 cm^2) AND (<1000 calories/day) AND (<45%) AND (<70) AND (=100 milliseconds (msec)) AND (>2.9 m/s) AND (>25 millimeters of mercury [mmHg]) AND (>3.0 meters per second [m/s]) AND (>40 mmHg) AND (>5 mmHg) AND (Aortic regurgitation) AND (Attention Deficit Hyperactivity Disorder) AND (B) AND (Bardet Biedl syndrome) AND (Baseline assessment) AND (Belviq XR) AND (Biphetamine) AND (C) AND (C-SSRS) AND (Clinically significant) AND (Concerta) AND (Currently) AND (Cushing's syndrome) AND (Dexedrine) AND (Diagnostic and Statistical Manual of Mental Disorders, 5th Edition) AND (Down's Syndrome) AND (Evidence of) AND (Female) AND (Gilbert's syndrome) AND (History) AND (Intracardiac mass) AND (Left ventricular ejection fraction) AND (Malignancy) AND (Mitral regurgitation) AND (Mitral valve stenosis) AND (Ongoing) AND (Planned) AND (Prader-Willi syndrome) AND (RVOTAT) AND (Recreational drug use) AND (Ritalin) AND (Screening) AND (Significant) AND (Special needs) AND (St. John's Wort) AND (Suicidal Ideation section of the Columbia-Suicide Severity Rating Scale (C-SSRS)) AND (Systolic pulmonary artery pressure (SPAP)) AND (T2DM) AND (Unable to attend scheduled visits) AND (Yes) AND (absence of) AND (abstinence) AND (abstinent) AND (acceptable) AND (active) AND (alcohol abuse) AND (alcohol dependence) AND (anorexia) AND (another) AND (antidiabetic agents) AND (antipsychotics) AND (antiseizure medications) AND (any form) AND (any time between screening and randomization) AND (aortic stenosis) AND (aortic valve area) AND (aortic valve stenosis) AND (at Baseline) AND (at Screening) AND (at the time of Screening) AND (autism) AND (azoospermia) AND (bariatric surgery) AND (bariatric surgical procedures) AND (benzodiazepines) AND (beta-human chorionic gonadotropin test) AND (bipolar disorder) AND (blood pressure) AND (breastfeeding) AND (bulimia) AND (bupropion) AND (cabergoline) AND (cannot swallow) AND (cardiac) AND (cardiac valvulopathy) AND (change in diet) AND (change in level of physical activity) AND (change in weight) AND (chronic illness) AND (clinically significant) AND (cognitive developmental delay) AND (condom) AND (congenital heart disease) AND (contraceptive) AND (contraceptive implant) AND (corticosteroids) AND (currently) AND (daily) AND (depressive disorder) AND (device) AND (dextromethorphan) AND (diaphragm with spermicide) AND (disease) AND (do not agree) AND (dopamine antagonists) AND (dosing) AND (double-barrier method) AND (drug abuse) AND (drug dependence) AND (drugs) AND (during the past year) AND (during the study) AND (during the study period) AND (dyslipidemia) AND (endocrine) AND (enrolled in clinical study) AND (epilepsy) AND (ergotamine) AND (excluding) AND (fasting glucose) AND (for 28 days after study drug discontinuation) AND (for age) AND (for at least 4 weeks before dosing) AND (for height) AND (for longer than 30 days) AND (for sex) AND (gastrointestinal) AND (genetic) AND (greater than 1.5× ULN) AND (greater than 1.5× upper limit of normal (ULN)) AND (greater than 3× ULN) AND (greater than mild) AND (hemodynamic compromise) AND (hepatic disease) AND (herbal) AND (highly effective) AND (history) AND (hormonal contraceptive) AND (hormonal contraceptives) AND (human immunodeficiency virus) AND (human immunodeficiency virus positive) AND (hypersensitivity) AND (hypoglycemia unawareness) AND (illness) AND (impaired) AND (impaired fasting glucose) AND (impaired glucose tolerance) AND (in the past) AND (inhaled steroids) AND (injectable) AND (intelligence quotient) AND (intrauterine device) AND (investigational drug) AND (investigational products) AND (jet) AND (known to increase the risk for cardiac valvulopathy) AND (lack of a caregiver) AND (lack of guardian) AND (lack of transportation) AND (lamotrigine) AND (linezolid) AND (lithium) AND (malignancy) AND (may affect the participant's ability to fulfill the study requirements) AND (mean gradient) AND (medications) AND (mental retardation) AND (metabolic) AND (method of contraception) AND (methysergide) AND (mild or greater) AND (mild to profound) AND (mitral stenosis) AND (mitral valve area) AND (moderate or greater) AND (moderate or larger) AND (moderate to severe) AND (more than 5 kg) AND (more than 72 hours before the first dose of study drug) AND (negative) AND (new) AND (non-insulin) AND (nonalcoholic fatty liver disease) AND (not) AND (obstructive sleep apnea) AND (or any of the excipients) AND (oral anti-diabetic agents) AND (oral contraceptive) AND (oral steroids) AND (other) AND (other than) AND (over-the-counter (OTC)) AND (partner) AND (pergolide) AND (pericardial effusion) AND (pervasive development disorders) AND (positive) AND (prediabetes) AND (pregnant) AND (prescription) AND (prior) AND (products intended for weight loss) AND (psychiatric) AND (questions 4) AND (questions 5) AND (randomization) AND (refrain) AND (renal) AND (renal disease) AND (respiratory) AND (schizophrenia) AND (screening) AND (screening pregnancy test) AND (secondary causes for obesity) AND (seizure disorder) AND (selective serotonin reuptake inhibitors) AND (separate) AND (serotonin norepinephrine reuptake inhibitors) AND (serum creatinine) AND (serum transaminases) AND (sexual activity) AND (significant exposure) AND (significantly confound the assessments may) AND (stable dose) AND (stimulant medications) AND (study drug) AND (study drug discontinuation) AND (study entry) AND (study-related) AND (suicidal behavior) AND (suicidal ideation) AND (sulfonylurea) AND (systemic corticosteroid) AND (the entire study period) AND (the first dose of study drug) AND (the same) AND (the study) AND (the study period) AND (thrombus) AND (throughout the entire study period) AND (topical steroids) AND (topiramate) AND (total) AND (total bilirubin) AND (tramadol) AND (tricuspid regurgitation [TR] jet velocity) AND (tricyclic antidepressants) AND (triptans) AND (tryptophan) AND (tumor) AND (type 2 diabetes) AND (unable to comprehend instructions) AND (unprotected sexual intercourse) AND (untreated hypothyroidism) AND (valproic acid) AND (vasectomized) AND (very-low-calorie weight loss diet) AND (viral hepatitis) AND (with a plan) AND (with intent) AND (within 1 month before Screening) AND (within 1 month before dosing) AND (within 1 month before randomization) AND (within 2 years before Screening) AND (within 3 months before Screening) AND (within 30 days before providing informed consent) AND (within 30 days before study entry) AND (within 5 years before Screening) AND (within 6 months before Screening) AND (within 6 months of Screening) AND (within 6 months of screening) AND (without a plan) AND (zonisamide))"}
{"candidate_id": "LLM04873", "doc_id": "NCT01991743_exc", "case_bucket": "or", "source_criterion": "Refusal Contraindication to neuraxial (coagulopathy, anticoagulant use, local infection, sepsis etc) .Rupture of membranes. Drop-out: Patients may choose to drop-out of the study at any time. The physicians involved in this study may choose to end a patient's involvement in the study at their discretion.", "candidate_expression": "((Contraindication) AND (Rupture of membranes) AND (anticoagulant) AND (coagulopathy) AND (local infection) AND (neuraxial) AND (sepsis))"}
{"candidate_id": "LLM04874", "doc_id": "NCT01009359_exc", "case_bucket": "or", "source_criterion": "Current unstable medical condition (e.g. unstable angina, myocardial infarction or coronary revascularization in the preceding 12 months, cardiac failure, chronic renal failure, chronic hepatic disease, severe pulmonary disease, blood disorders, poorly controlled diabetes, chronic infection)", "candidate_expression": "((Current) AND (chronic) AND (controlled) AND (in the preceding 12 months) AND (poorly) AND (severe) AND (unstable) AND (unstable medical condition) AND ((blood disorders) OR (cardiac failure) OR (chronic hepatic disease) OR (chronic infection) OR (chronic renal failure) OR (coronary revascularization) OR (diabetes) OR (myocardial infarction) OR (pulmonary disease) OR (unstable angina)))"}
{"candidate_id": "LLM04875", "doc_id": "NCT00970866_exc", "case_bucket": "or", "source_criterion": "Known asthmatic or history of allergy towards peanut or milk products Concurrent participation in another clinical trial Severe illness warranting hospital referral", "candidate_expression": "((hospital referral warranting) AND (illness Severe) AND (participation in another clinical trial) AND ((allergy history) OR (asthmatic)) AND ((milk products) OR (peanut)))"}
```
