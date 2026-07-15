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
{"candidate_id": "LLM02026", "doc_id": "NCT02726009_exc", "case_bucket": "or", "source_criterion": "Previous or concurrent hormonal management of prostate cancer Contraindication for prescription of Firmagon® Concurrent treatment with a 5-a-reductase inhibitor Considered as a candidate for curative therapy History of severe untreated asthma, anaphylactic reactions or severe urticaria and/or angioedema QTc interval over 450 msec or risk factors for torsades de pointes or on Class IA and Class III anti arrhythmic medications Cancer within the last 5 years except prostate cancer and surgically removed basal or squamous cell carcinoma of the skin Known or suspected hepatic, symptomatic biliary disease (this includes moderate to severe chronic hepatic impairment) Patients with clinically significant laboratory abnormalities / disorders other than prostate cancer Patient with Hepatitis B Virus (HBV), Hepatitis C Virus (HCV) and Human Immunodeficiency Virus (HIV) infections", "candidate_expression": "((5-a-reductase inhibitor) AND (Cancer last 5 years) AND (Contraindication) AND (Firmagon) AND (HBV) AND (HCV) AND (HIV) AND (chronic hepatic impairment) AND (curative therapy) AND (hormonal management) AND (prostate cancer) AND (surgically) AND ((anaphylactic reactions) OR (angioedema) OR (asthma severe untreated) OR (urticaria severe)) AND ((Class IA anti arrhythmic medications) OR (Class III anti arrhythmic medications) OR (QTc interval over 450 msec) OR (risk factors for torsades de pointes)) AND ((basal cell carcinoma of the skin) OR (squamous cell carcinoma of the skin)) AND ((biliary disease) OR (hepatic disease)) AND ((moderate) OR (severe)) AND ((Hepatitis B Virus infections) OR (Hepatitis C Virus infections) OR (Human Immunodeficiency Virus infections)))"}
{"candidate_id": "LLM02027", "doc_id": "NCT02385045_exc", "case_bucket": "or", "source_criterion": "Patients attending for a therapeutic endoscopic procedure e.g. variceal banding, stent insertion, balloon dilatation. Patients with a known diagnosis e.g. upper gastrointestinal cancer Patients previously treated with HP eradication therapy Patients who had taken PPI, H2 receptor antagonists and antibiotics within 4 weeks Patients with acute gastrointestinal bleeding Patients who'd had previous gastric surgery Patients with chronic liver disease Patients with abnormal coagulation or any other contra-indication to use of standard biopsy in routine diagnostic endoscopic procedures Patients who are unable or unwilling to give informed consent Patients under the age of 18 years", "candidate_expression": "((HP eradication therapy) AND (age under 18 years) AND (diagnostic endoscopic procedures) AND (gastric surgery previous) AND (gastrointestinal bleeding acute) AND (known diagnosis) AND (liver disease chronic) AND (standard biopsy) AND (therapeutic endoscopic procedure) AND (upper gastrointestinal cancer) AND ((H2 receptor antagonists) OR (PPI) OR (antibiotics)) AND ((abnormal coagulation) OR (contra-indication)) AND ((balloon dilatation) OR (stent insertion) OR (variceal banding)))"}
{"candidate_id": "LLM02028", "doc_id": "NCT03177837_exc", "case_bucket": "or", "source_criterion": "COPD exacerbation, very severe COPD with hypoxemia at low altitude (FEV1/FVC <0.7, FEV1 <40% predicted, oxygen saturation on room air <92% at 750 m). Comorbidities such as uncontrolled cardiovascular disease, i.e., unstable systemic arterial hypertension, coronary artery disease; previous stroke; OSA; pneumothorax in the last 2 months. Internal, neurologic, rheumatologic or psychiatric disease including current heavy smoking (>20 cigarettes per day) Known renal failure or allergy to acetazolamide and other sulfonamides", "candidate_expression": "((750 m) AND (<0.7) AND (<40% predicted) AND (<92%) AND (>20) AND (Comorbidities) AND (FEV1) AND (FEV1/FVC) AND (cigarettes per day) AND (current) AND (disease) AND (heavy) AND (hypoxemia) AND (in the last 2 months) AND (low altitude) AND (oxygen saturation) AND (previous) AND (room air) AND (smoking) AND (uncontrolled) AND (unstable) AND (very severe) AND ((OSA) OR (cardiovascular disease) OR (coronary artery disease) OR (pneumothorax) OR (stroke) OR (systemic arterial hypertension)) AND ((Internal) OR (neurologic) OR (psychiatric) OR (rheumatologic)) AND ((COPD) OR (COPD exacerbation)) AND ((allergy) OR (renal failure)) AND ((acetazolamide) OR (other) OR (sulfonamides)))"}
{"candidate_id": "LLM02029", "doc_id": "NCT02872090_exc", "case_bucket": "other", "source_criterion": "beta blocker supraventricular rhythm disorder previous history of respiratory disease other than COPD diabetes autonomic dysfunction dysautonomia renal failure long-term oxygen therapy history of psychiatric illness", "candidate_expression": "((COPD) AND (autonomic dysfunction) AND (beta blocker) AND (diabetes) AND (dysautonomia) AND (history) AND (long-term oxygen therapy) AND (other than) AND (previous history) AND (psychiatric illness) AND (renal failure) AND (respiratory disease) AND (supraventricular rhythm disorder))"}
{"candidate_id": "LLM02030", "doc_id": "NCT03479502_inc", "case_bucket": "other", "source_criterion": "18 years of age and older, diagnosis of stage II adhesive capsulitis as determined by clinical examination of the treating physician, and absence of abnormal findings on X-ray.", "candidate_expression": "((18 years and older) AND (X-ray) AND (abnormal findings) AND (absence of) AND (adhesive capsulitis) AND (age) AND (as determined by clinical examination) AND (clinical examination) AND (stage II))"}
{"candidate_id": "LLM02031", "doc_id": "NCT02312960_exc", "case_bucket": "other", "source_criterion": "Not applicable to this follow up study", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02032", "doc_id": "NCT03497598_inc", "case_bucket": "or", "source_criterion": "Women = 3 UTIs within the last 12 months or = 2 UTIs within the last 6 months; Laboratory urine culture: <103 CFUs Age > 18 years", "candidate_expression": "((<103 CFUs) AND (= 2) AND (= 3) AND (> 18 years) AND (Age) AND (Laboratory urine culture) AND (UTIs) AND (Women) AND (within the last 12 months) AND (within the last 6 months))"}
{"candidate_id": "LLM02033", "doc_id": "NCT02344888_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Body mass index (BMI) < 18.5 kg/m2 or > 25 kg/m2. Presence of any infertility factor other than anovulatory PCOS. Previous history of ovarian surgery or surgical removal of one ovary. Previous exposure to cytotoxic drugs or pelvic irradiation. Oral hypoglycemic or hormonal therapy either currently or in the preceding 3 months. Metabolic or hormonal abnormalities", "candidate_expression": "((Age < 20 or > 35 years) AND (BMI) AND (Body mass index < 18.5 kg/m2 or > 25 kg/m2) AND (exposure) AND (infertility factor) AND NOT (anovulatory PCOS) AND ((cytotoxic drugs) OR (pelvic irradiation)) AND ((hormonal therapy) OR (hypoglycemic therapy)) AND ((Metabolic abnormalities) OR (hormonal abnormalities)) AND ((ovarian surgery) OR (surgical removal ovary)))"}
{"candidate_id": "LLM02034", "doc_id": "NCT02056626_inc", "case_bucket": "other", "source_criterion": "systolic blood pressure between 140-160 mmHG between 18-80 years old", "candidate_expression": "((old between 18-80 years) AND (systolic blood pressure between 140-160 mmHG))"}
{"candidate_id": "LLM02035", "doc_id": "NCT02481518_exc", "case_bucket": "other", "source_criterion": "Prior treatment with cisplatin before randomization Uncontrolled concurrent disease Pregnancy", "candidate_expression": "((Pregnancy) AND (cisplatin before randomization) AND (concurrent disease Uncontrolled))"}
{"candidate_id": "LLM02036", "doc_id": "NCT02954029_inc", "case_bucket": "or", "source_criterion": "age 18 years or older patients undergoing invasive procedures via the radial or femoral arteries", "candidate_expression": "((18 years or older) AND (age) AND (invasive procedures) AND (undergoing) AND ((femoral arteries) OR (radial arteries)))"}
{"candidate_id": "LLM02037", "doc_id": "NCT00061308_exc", "case_bucket": "or", "source_criterion": "Women of child-bearing potential that do not practice adequate contraception. Pregnant or lactating. Received more than one primary chemotherapy regimen. Concomitant or previous malignancies with the exception of adequately treated basal cell or squamous cell skin cancer, in situ cervical cancer, incidental carcinoid, or other cancer from which the patient has been disease free for 5 years. Active uncontrolled infection requiring antibiotics. Concurrent severe medical problems unrelated to the malignancy which would limit full compliance with the study. Received radiation to more than 10% of bone. Prior treatment with topotecan or gemcitabine. Hypersensitivity to camptothecin or nucleoside analogues. Use of an investigational agent within 30 days.", "candidate_expression": "((Hypersensitivity) AND (Pregnant) AND (Women) AND (antibiotics) AND (basal cell skin cancer) AND (camptothecin) AND (child-bearing potential) AND (gemcitabine) AND (in situ cervical cancer) AND (incidental carcinoid) AND (infection Active uncontrolled) AND (investigational agent within 30 days) AND (lactating) AND (malignancies) AND (malignancy) AND (medical problems Concurrent severe unrelated to the malignancy limit full compliance with the study) AND (nucleoside analogues) AND (other cancer) AND (primary chemotherapy regimen more than one Concomitant previous) AND (radiation bone) AND (squamous cell skin cancer) AND (topotecan) AND (treatment Prior) AND NOT (adequate contraception))"}
{"candidate_id": "LLM02038", "doc_id": "NCT03106389_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02039", "doc_id": "NCT02118467_exc", "case_bucket": "other", "source_criterion": "Cardiopulmonary arrest Pregnancy Severe right heart failure", "candidate_expression": "((Cardiopulmonary arrest) AND (Pregnancy) AND (right heart failure Severe))"}
{"candidate_id": "LLM02040", "doc_id": "NCT02872090_inc", "case_bucket": "other", "source_criterion": "patients with FEV1 / FVC <70%", "candidate_expression": "(FEV1 / FVC <70%)"}
{"candidate_id": "LLM02041", "doc_id": "NCT02361905_exc", "case_bucket": "other", "source_criterion": "submucosal leiomyoma, endometrial hyperplasia with atypia, history of uterine surgery", "candidate_expression": "((endometrial hyperplasia) AND (history) AND (submucosal leiomyoma) AND (uterine surgery) AND (with atypia))"}
{"candidate_id": "LLM02042", "doc_id": "NCT02167022_inc", "case_bucket": "other", "source_criterion": "1. Age: 12 to 36 months of age (The diagnosis of CP is often uncertain under the age of 12 months. The cutoff at 36 months is to have a population of young children when the brain is most \"plastic\" and most susceptible to reorganization). 2. Diagnosis: Diagnosis of spastic CP confirmed by a pediatric neurologist or pediatric rehabilitation specialist. 3. Etiology: The insult to the central nervous system that caused the motor dysfunction must have occurred during gestation or within one year after birth independent of gestational age. 4. Disease severity level: Gross Motor Function Classification System (GMFCS) levels I, II and III.", "candidate_expression": "((12 to 36 months of age) AND (Age) AND (Gross Motor Function Classification System (GMFCS)) AND (levels I, II and III) AND (one year after birth) AND (spastic CP))"}
{"candidate_id": "LLM02043", "doc_id": "NCT02968602_exc", "case_bucket": "or", "source_criterion": "History of organic brain disease DSM-IV diagnosis of Alcohol or Substance Dependence within the last six months (except nicotine) or DSM-5 diagnosis of Substance Use Disorder in the last six months (except nicotine) DSM-IV diagnosis of Alcohol or Substance Abuse within the last one month (except nicotine) or DSM-5 diagnosis of Substance Use Disorder in the last six months (except nicotine) Pregnancy or lactation Severe liver dysfunction (LFT 3X upper limit of normal) Previous known hypersensitivity to tetracyclines Current treatment with tetracycline or derivative Treatment with oral contraceptives (unless a second form of birth control is used and documented) Treatment with cholestyramine or colestipol Treatment with Urinary alkalinizers (e.g., sodium lactate, potassium citrate) Treatment with warfarin Treatment with bupropion, varenicline, or nicotine replacement products in the month prior to study inclusion Less than two months treatment of adjunctive medications AND less than one month on same dose: beta blockers, antidepressants, mood stabilizers, antianxiety medications. Medical condition whose pathology or treatment would significantly increase the risk associated with the proposed protocol. History of head injury, seizures, or stroke Positive urine toxicology screen for substances of non-therapeutic use prior to craving assessments", "candidate_expression": "((3X upper limit of normal) AND (Current) AND (DSM-5) AND (DSM-IV) AND (History) AND (History of) AND (LFT) AND (Less than two months) AND (Medical condition) AND (Positive) AND (Previous) AND (Severe) AND (Substance Use Disorder) AND (Treatment) AND (Urinary alkalinizers) AND (adjunctive medications) AND (birth control) AND (craving assessments) AND (except) AND (hypersensitivity) AND (in the last six months) AND (in the month prior to study inclusion) AND (less than one month) AND (liver dysfunction) AND (nicotine) AND (oral contraceptives) AND (organic brain disease) AND (prior to craving assessments) AND (same dose) AND (second form) AND (study inclusion) AND (substances of non-therapeutic use) AND (tetracyclines) AND (treatment) AND (unless) AND (urine toxicology screen) AND (warfarin) AND (within the last one month) AND (within the last six months) AND (would significantly increase the risk associated with the proposed protocol) AND ((Alcohol Abuse) OR (Substance Abuse)) AND ((Pregnancy) OR (lactation)) AND ((Alcohol Dependence) OR (Substance Dependence)) AND ((tetracycline) OR (tetracycline derivative)) AND ((cholestyramine) OR (colestipol)) AND ((potassium citrate) OR (sodium lactate)) AND ((bupropion) OR (nicotine replacement products) OR (varenicline)) AND ((antianxiety medications) OR (antidepressants) OR (beta blockers) OR (mood stabilizers)) AND ((head injury) OR (seizures) OR (stroke)))"}
{"candidate_id": "LLM02044", "doc_id": "NCT03115320_inc", "case_bucket": "other", "source_criterion": "- Patient with IVF cycle and therefore having frozen-thawed embryos Regular menstruation cycle Patient's willingness to participate in the study", "candidate_expression": "((IVF cycle) AND (Patient's willingness to participate in the study) AND (Regular menstruation cycle) AND (frozen-thawed embryos))"}
{"candidate_id": "LLM02045", "doc_id": "NCT03589105_inc", "case_bucket": "or", "source_criterion": "Age >/=18 years at screening Patients with relapsing forms of multiple sclerosis (RMS) with active disease defined by clinical or imaging features: (i) at least one clinical relapse over a 6-month period prior to screening; (ii) AND/OR at least one T1 gadolinium-enhancing lesion or new and/or enlarging T2 lesion as detected by brain Magnetic Resonance Imaging (MRI) performed over a 3 months period prior to screening with no change of Disease-Modifying Treatment(s) (DMT) compared to a previous MRI performed within 24 months before screening For women of childbearing potential: agreement to use an acceptable birth control method during the treatment period and for at least 12 months after the last dose of ocrelizumab Participants should be beneficiary of healthcare coverage under the social security system", "candidate_expression": "((>/=18 years) AND (Age) AND (Disease-Modifying Treatment(s) (DMT)) AND (For women of childbearing potential: agreement to use an acceptable birth control method during the treatment period and for at least 12 months after the last dose of ocrelizumab) AND (T1 gadolinium-enhancing lesion) AND (T2 lesion) AND (active disease) AND (at least one over a 3 months period) AND (at least one over a 6-month period) AND (at screening) AND (beneficiary of healthcare coverage) AND (brain Magnetic Resonance Imaging (MRI)) AND (change of) AND (clinical features) AND (clinical relapse) AND (enlarging) AND (imaging features) AND (multiple sclerosis (RMS)) AND (new) AND (no) AND (prior to screening) AND (relapsing forms))"}
{"candidate_id": "LLM02046", "doc_id": "NCT02550080_inc", "case_bucket": "or", "source_criterion": "Diagnosed with cutaneous vasculitis, urticaria, psoriasis, acne, bullous skin diseases, sterile pustulosis, leprosy, pneumocystis pneumonia and any other patients who need dapsone administration. Subjects are dapsone-naive. All subjects must have a clinical need for treatment with dapsone that precedes the decision to participate in the study. All subjects are willing to complete the 6-weeks period clinical trial. All subjects are written informed consent.", "candidate_expression": "((All subjects are willing to complete the 6-weeks period clinical trial) AND (All subjects are written informed consent) AND (dapsone) AND (naive) AND ((acne) OR (bullous skin diseases) OR (cutaneous vasculitis) OR (dapsone) OR (leprosy) OR (pneumocystis pneumonia) OR (psoriasis) OR (sterile pustulosis) OR (urticaria)))"}
{"candidate_id": "LLM02047", "doc_id": "NCT02924090_inc", "case_bucket": "or", "source_criterion": "Adults patients aged 18 to 85 years Diagnosed with Major Depressive Disorder, unipolar or bipolar depression Undergoing ECT for treatment of their symptoms Currently residing in Manitoba", "candidate_expression": "((18 to 85 years) AND (Adults) AND (Currently residing) AND (ECT) AND (Manitoba) AND (Undergoing) AND (aged) AND ((Major Depressive Disorder) OR (bipolar depression) OR (unipolar depression)))"}
{"candidate_id": "LLM02048", "doc_id": "NCT03256864_inc", "case_bucket": "other", "source_criterion": "Liver Transplant Recipients have received liver transplantations for at least 6+1 months prior to enrollment Liver Transplant Recipients have no acute rejection episodes within 3 months prior to the enrollment and are clinically stable Liver Transplant Recipients have been treated with twice-daily regimen of tacrolimus(TAC) plus everolimus(EVR) and TAC and EVR trough levels have stayed within targeted ranges for at least 6 weeks prior to enrollment Provide written informed consent prior to inclusion. Liver transplant recipients who are 18-65 years of age of a primary liver transplant Allograft functioning at an acceptable level as defined by the AST, ALT, Total Bilirubin levels =3 times ULN prior to enrollment. Abbreviated MDRD eGFR = 30 mL/min/1.73m2.", "candidate_expression": "((ALT) AND (AST) AND (Allograft functioning acceptable level) AND (EVR trough levels) AND (Liver Transplant Recipients) AND (Liver transplant recipients) AND (MDRD eGFR = 30 mL/min/1.73m2) AND (TAC trough levels) AND (Total Bilirubin) AND (age 18-65 years) AND (clinically stable) AND (everolimus(EVR)) AND (liver transplantations for at least 6+1 months prior to enrollment) AND (primary liver transplant) AND (tacrolimus(TAC)) AND (written informed consent prior to inclusion) AND NOT (rejection episodes acute within 3 months prior to the enrollment))"}
{"candidate_id": "LLM02049", "doc_id": "NCT01888965_inc", "case_bucket": "or", "source_criterion": "Patients with a confirmed diagnosis of: 1. Stage 4 colon cancer either s/p metastasectomy or post-initial chemotherapy or maintenance \"standard of care\", either involving 5-fluorouracil/leucovorin (5-FU/LV) alone or continual bevacizumab alone. Patients in maintenance cohort must have had 2 consecutive CT scans showing stable disease and not be experiencing significant prior treatment-related toxicity above Grade 1. 2. Pancreas cancer, either s/p resection and adjuvant chemotherapy or locally advanced pancreas cancer s/p chemotherapy and radiation. Initial chemotherapy or radiation therapy may have been stopped between 2 weeks and 2 months prior to study start, and patients must have recovered from prior treatment related toxicity to grade 1 or less. Prior surgery, including tumor resection or metastasectomy must have been performed at least 4 weeks prior to study enrollment. No concomitant anti-cancer treatment is allowed Age >/= 18 years Performance status of 0-1 Adequate hepatic, bone marrow, and renal function Partial thromboplastin time (PTT) must be </= 1.5 x upper normal limit of institution's normal range and INR (International Normalized Ratio) < 1.5. Life expectancy >/= 4 months for maintenance cohorts and >/= 6 months for adjuvant cohorts Women of childbearing potential must have a negative serum pregnancy test within 14 days prior to initiation of treatment and must not be lactating. Subject is capable of understanding and complying with protocol demands and able to sign and date the informed consent", "candidate_expression": "((0-1) AND (2) AND (5-fluorouracil/leucovorin (5-FU/LV)) AND (< 1.5) AND (</= 1.5 x upper normal limit) AND (>/= 18 years) AND (>/= 4 months) AND (>/= 6 months) AND (Adequate) AND (Age) AND (CT scans) AND (INR (International Normalized Ratio)) AND (Life expectancy) AND (No concomitant anti-cancer treatment is allowed) AND (Pancreas cancer) AND (Partial thromboplastin time (PTT)) AND (Performance status) AND (Prior) AND (Stage 4) AND (Subject is capable of understanding and complying with protocol demands and able to sign and date the informed consent) AND (Women) AND (adjuvant chemotherapy) AND (adjuvant cohorts) AND (at least 4 weeks prior to study enrollment) AND (between 2 weeks and 2 months prior to study start) AND (bevacizumab) AND (bone marrow function) AND (chemotherapy) AND (childbearing potential) AND (colon cancer) AND (disease) AND (function hepatic) AND (initiation of treatment) AND (lactating) AND (locally advanced) AND (maintenance \"standard of care\") AND (maintenance cohorts) AND (may have been stopped) AND (metastasectomy) AND (negative) AND (not) AND (pancreas cancer) AND (post-initial chemotherapy) AND (prior) AND (radiation) AND (radiation therapy) AND (recovered from prior treatment) AND (renal function) AND (resection) AND (s/p adjuvant chemotherapy) AND (s/p chemotherapy) AND (s/p metastasectomy) AND (s/p radiation) AND (s/p resection) AND (serum pregnancy test) AND (stable) AND (study enrollment) AND (study start) AND (surgery) AND (treatment) AND (treatment-related toxicity) AND (tumor resection) AND (within 14 days prior to initiation of treatment))"}
{"candidate_id": "LLM02050", "doc_id": "NCT01664507_exc", "case_bucket": "or", "source_criterion": "underlying lung or heart disase contra indication to dexamethasone immune deficient state preterm birth previous intubation or apnea history", "candidate_expression": "((contra indication) AND (dexamethasone) AND (history) AND (immune deficient state) AND (preterm birth) AND (previous) AND ((heart disase) OR (lung disase)) AND ((apnea) OR (intubation)))"}
```
