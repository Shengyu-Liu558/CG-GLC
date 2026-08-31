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
{"candidate_id": "LLM05301", "doc_id": "NCT02822001_inc", "case_bucket": "other", "source_criterion": "Patients undergoing surgery with general anesthesia, Patients weighing = 80 pounds who are not -intubated prior to surgery, Patients who are able to give informed consent.", "candidate_expression": "((= 80 pounds) AND (Patients who are able to give informed consent) AND (general anesthesia) AND (intubated) AND (not) AND (prior to surgery) AND (surgery) AND (undergoing) AND (weighing))"}
{"candidate_id": "LLM05302", "doc_id": "NCT02476461_exc", "case_bucket": "other", "source_criterion": "previous treated dupuytrens contracture same hand more than tree fingers involvement we will not include thumbs other things affecting hand function ASA>3 expected to live under five years Tetracycline treatment within two weeks pregnancy nursing allergy to clostridium histolyticum participant in other trial", "candidate_expression": "((>3) AND (ASA) AND (Tetracycline) AND (affecting hand function) AND (allergy) AND (clostridium histolyticum) AND (dupuytrens contracture) AND (expected to live) AND (fingers involvement) AND (more than tree) AND (nursing) AND (other things) AND (participant in other trial) AND (pregnancy) AND (previous) AND (same hand) AND (treated) AND (under five years) AND (within two weeks))"}
{"candidate_id": "LLM05303", "doc_id": "NCT02692651_exc", "case_bucket": "or", "source_criterion": "Patients with severe-complicated disease that would compromise oral therapy (hypotenstion or shock, ileus or bowel obstruction, megacolon). Patients with an allergy to oral vancomycin or fidaxomicin. Patients anticipated to receive metronidazole after enrollment. Patients who already received oral vancomycin or metronidazole (either oral or intravenous) for > 24 hours within the preceding 72 hours at the time of enrollment. Patients anticipated to receive adjunctive C. difficile therapy (rifaxamin, nitazoxanide, tigecycline) after enrollment.", "candidate_expression": "((C. difficile therapy anticipated) AND (allergy) AND (metronidazole anticipated) AND (preceding 72 hours at the time of enrollment. enrollment) AND ((metronidazole) OR (vancomycin oral)) AND ((nitazoxanide) OR (rifaxamin) OR (tigecycline)) AND ((bowel obstruction) OR (hypotenstion) OR (ileus) OR (megacolon) OR (shock)) AND ((fidaxomicin) OR (vancomycin oral)))"}
{"candidate_id": "LLM05304", "doc_id": "NCT00749112_exc", "case_bucket": "or", "source_criterion": "Current viral or bacterial infection. Positive serology for HIV, HCV, HBV.", "candidate_expression": "((Current) AND (Positive) AND ((bacterial infection) OR (infection viral)) AND ((serology for HBV) OR (serology for HCV) OR (serology for HIV)))"}
{"candidate_id": "LLM05305", "doc_id": "NCT00728156_inc", "case_bucket": "or", "source_criterion": "Patients with T2DM and CAS as defined below: Clinical definitions T2DM: Diagnosed according to the WHO criteria [53]. CAD:Presence of any one of the following: Angina plus positive exercise tolerance test, enzyme and/or Q wave positive myocardial infarction, angiographic evidence ( >50% stenosis of one vessel), percutaneous or surgical coronary revascularisation. Aged between 18 and 75 Provided written consent for participation in the trial prior to any study-specific procedures or requirements.", "candidate_expression": "((Aged between 18 and 75) AND (Angina) AND (CAD) AND (CAS) AND (T2DM) AND (T2DM WHO criteria) AND (exercise tolerance test positive) AND (stenosis of one vessel >50%) AND (written consent for participation in the trial prior to any study-specific procedures or requirements) AND ((Q wave positive) OR (enzyme positive)) AND ((angiographic evidence) OR (coronary revascularisation) OR (myocardial infarction)) AND ((percutaneous) OR (surgical)))"}
{"candidate_id": "LLM05306", "doc_id": "NCT02419378_exc", "case_bucket": "or", "source_criterion": "Participation in another clinical trial at present or within 4 weeks of study entry. There may be exceptions at the discretion of the Investigator. Has any progressive form of MS Hypersensitivity to the active substance, or to any of the excipients of Lemtrada® Medical, psychiatric, cognitive, or other conditions that, in the Investigator's opinion, compromise the patient's ability to understand the patient information, to give informed consent, to comply with the trial protocol, or to complete the study Any disability acquired from trauma or another illness that could interfere with evaluation of disability due to MS Major systemic disease or other illness that would, in the opinion of the Investigator, compromise patient safety or interfere with the interpretation of study results, e.g., current peptic ulcer disease or other conditions that may predispose to hemorrhage Known bleeding disorder (e.g,. dysfibrinogenemia, factor IX deficiency, hemophilia, Von Willebrand's disease, disseminated intravascular coagulation (DIC), fibrinogen deficiency, or clotting factor deficiency) Significant autoimmune disease including but not limited to immune cytopenias, rheumatoid arthritis, systemic lupus erythematosus, other connective tissue disorders, vasculitis, inflammatory bowel disease, severe psoriasis History of malignancy, except basal skin cell carcinoma Major psychiatric disorder that is not adequately controlled by treatment Epileptic seizures that are not adequately controlled by Treatment Active infection, e.g., deep-tissue infection, that the Investigator considers sufficiently serious to preclude study participation In the Investigator's opinion, is at high risk for infection (e.g., indwelling catheter, dysphagia with aspiration, decubitus ulcer, history of prior aspiration pneumonia or recurrent urinary tract infection) Seropositivity for human immunodeficiency virus (HIV) Infection with hepatitis C Virus Past or present hepatitis B infection (positive hepatitis B serology) Active infection with human cytomegaly virus (HCMV), Epstein-Barr virus (EBV), varicella-zoster virus (VZV) Latent tuberculosis unless effective anti-tuberculosis therapy has been completed, or active tuberculosis. Invasive fungal infections in history and at present Cervical cytology other than PAP I or PAP II (Papanicolaou) or cervical high risk human papillomavirus (HPV) positivity Any other illness or infection (latent or active) that, in the Investigator's opinion, could be exacerbated by study medication Differential blood count < lower limit of normal (LLN) at Screening Confirmed platelet count < the LLN of the evaluating laboratory at Screening or documented at <100,000/µL within the past year on a sample without platelet clumping Presence (i.e., above the ULN) of anti-thyroid stimulating hormone receptor antibodies (anti-TSHR) and anti-thyroid peroxidase antibody (anti-TPO) Vaccination less than 6 weeks prior to treatment with Lemtrada. Treatment with antineoplastic or immunosuppressive drugs within 8 weeks prior to study inclusion Intolerance of pulsed corticosteroids, especially a history of steroid psychosis Inability to undergo MRI with gadolinium administration Of childbearing potential with a positive serum pregnancy test, pregnant or lactating Female patients of childbearing potential: Unwilling to agree to use a reliable and acceptable contraceptive method (Pearl index <1) throughout the study period. These methods include: hormone releasing intrauterine device (IUD), hormonal-based contraception, surgical sterilization, abstinence, or double-barrier contraception (condom and occlusive cap [diaphragm or cervical cap combined with spermicide]).", "candidate_expression": "((< lower limit of normal (LLN)) AND (< the LLN of the evaluating laboratory) AND (<100,000/µL) AND (Active) AND (Any disability acquired from trauma or another illness that could interfere with evaluation of disability due to MS) AND (Cervical cytology) AND (Confirmed) AND (DIC) AND (Differential blood count) AND (EBV) AND (Epileptic seizures) AND (Epstein-Barr virus) AND (Female) AND (HCMV) AND (HIV) AND (HPV) AND (Hypersensitivity) AND (Inability to) AND (Inability to undergo MRI) AND (Infection) AND (Intolerance) AND (Invasive) AND (Latent tuberculosis) AND (Lemtrada) AND (MRI) AND (MS) AND (Major) AND (Major systemic disease or other illness that would, in the opinion of the Investigator, compromise patient safety or interfere with the interpretation of study results, e.g., current peptic ulcer disease or other conditions that may predispose to hemorrhage) AND (Medical, psychiatric, cognitive, or other conditions that, in the Investigator's opinion, compromise the patient's ability to understand the patient information, to give informed consent, to comply with the trial protocol, or to complete the study) AND (PAP I) AND (PAP II) AND (Papanicolaou) AND (Participation) AND (Presence) AND (Seropositivity) AND (Treatment) AND (Unwilling to agree to use a reliable and acceptable contraceptive method (Pearl index <1) throughout the study period. These methods include: hormone releasing intrauterine device (IUD), hormonal-based contraception, surgical sterilization, abstinence, or double-barrier contraception (condom and occlusive cap [diaphragm or cervical cap combined with spermicide])) AND (VZV) AND (Vaccination) AND (Von Willebrand's disease) AND (above the ULN) AND (active) AND (active tuberculosis) AND (adequately controlled) AND (anti-thyroid peroxidase antibody (anti-TPO)) AND (anti-thyroid stimulating hormone receptor antibodies (anti-TSHR)) AND (anti-tuberculosis therapy) AND (antineoplastic drugs) AND (articipation in another clinical trial at present or within 4 weeks of study entry. There may be exceptions at the discretion of the Investigator) AND (aspiration) AND (aspiration pneumonia) AND (at Screening) AND (autoimmune disease) AND (basal skin cell carcinoma) AND (bleeding disorder) AND (cervical high risk) AND (childbearing potential) AND (clotting factor deficiency) AND (completed) AND (connective tissue disorders) AND (decubitus ulcer) AND (deep-tissue infection) AND (disseminated intravascular coagulation) AND (dysfibrinogenemia) AND (dysphagia) AND (exacerbated by study medication) AND (except) AND (factor IX deficiency) AND (fibrinogen deficiency) AND (fungal infections) AND (gadolinium) AND (hemophilia) AND (hepatitis B infection) AND (hepatitis B serology) AND (hepatitis C Virus) AND (high) AND (history of) AND (human cytomegaly virus) AND (human immunodeficiency virus) AND (human papillomavirus) AND (illness) AND (immune cytopenias,) AND (immunosuppressive drugs) AND (indwelling catheter) AND (infection) AND (inflammatory bowel disease) AND (lactating) AND (latent) AND (less than 6 weeks prior to treatment with Lemtrada) AND (malignancy) AND (not) AND (other) AND (platelet count) AND (positive) AND (positivity) AND (pregnant) AND (progressive) AND (psoriasis) AND (psychiatric disorder) AND (pulsed corticosteroids) AND (recurrent) AND (rheumatoid arthritis,) AND (risk for infection) AND (sample without platelet clumping) AND (serum pregnancy test) AND (severe) AND (steroid psychosis) AND (study inclusion) AND (study medication) AND (systemic lupus erythematosus) AND (treatment) AND (treatment with Lemtrada) AND (unless) AND (urinary tract infection) AND (varicella-zoster virus) AND (vasculitis) AND (within 8 weeks prior to study inclusion) AND (within the past year))"}
{"candidate_id": "LLM05307", "doc_id": "NCT02637453_inc", "case_bucket": "other", "source_criterion": "No response to more than one antiarrhythmic drug, or unwilling to receive long-term drug treatment. Can provide informed consent form expressing willingness to participate in the study and comply with follow-up tests and evaluation procedures. Aged 18-80 years.", "candidate_expression": "((18-80 years) AND (Aged) AND (Can provide informed consent form expressing willingness to participate in the study and comply with follow-up tests and evaluation procedures.) AND (No) AND (antiarrhythmic drug) AND (more than one) AND (response))"}
{"candidate_id": "LLM05308", "doc_id": "NCT01959061_exc", "case_bucket": "or", "source_criterion": "Pregnant or lactating women Patients with severe organ dysfunction or failure With severe cardiovascular disease, or mental Extraliver metastases", "candidate_expression": "((Extraliver) AND (Extraliver metastases) AND (metastases) AND (severe) AND (women) AND ((Pregnant) OR (lactating)) AND ((organ dysfunction) OR (organ failure)) AND ((cardiovascular disease) OR (disease mental)))"}
{"candidate_id": "LLM05309", "doc_id": "NCT02202369_exc", "case_bucket": "or", "source_criterion": "Patients with liver disease (documented liver function test abnormality) Patients with renal disease (documented glomerular filtration rate < 60mL/min/1.73m2) Patients with a baseline (pre-operative) opioid use greater than 30 mg of morphine equivalents/day. Patients with active alcohol dependence Patients with active illicit drug dependence Patients < 18 years of age and >70 years of age Patients allergic to any medication given in either arm (list medications) Patients who have a seizure disorder", "candidate_expression": "((< 18 years) AND (< 60mL/min/1.73m2) AND (>70 years) AND (abnormality) AND (alcohol dependence) AND (allergic) AND (baseline) AND (glomerular filtration rate) AND (greater than 30 mg of morphine equivalents/day) AND (illicit drug dependence) AND (liver disease) AND (liver function test) AND (medication) AND (opioid) AND (pre-operative) AND (renal disease) AND (seizure disorder) AND ((age)))"}
{"candidate_id": "LLM05310", "doc_id": "NCT02456532_inc", "case_bucket": "other", "source_criterion": "DSM-5 diagnosis of insomnia", "candidate_expression": "((DSM-5) AND (insomnia))"}
{"candidate_id": "LLM05311", "doc_id": "NCT03356834_inc", "case_bucket": "other", "source_criterion": "Chronic hepatitis B, Antiviral experienced, Currently on long term TDF anti-HBV treatment, HBV DNA < 6 log IU/ml (LLOD) Able to sign the consent form of anticipating in the study", "candidate_expression": "((< 6 log IU/ml) AND (Able to sign the consent form of anticipating in the study) AND (Antiviral) AND (Chronic hepatitis B) AND (HBV) AND (HBV DNA) AND (LLOD) AND (TDF) AND (TDF anti-HBV treatment) AND (experienced) AND (long term))"}
{"candidate_id": "LLM05312", "doc_id": "NCT01774019_inc", "case_bucket": "or", "source_criterion": "Age 18 or older Willing and able to comply with the study procedures and provide written informed consent to participate in the study Diagnosis of probable pancreatic cancer, distal common bile duct (CBD) cholangiocarcinoma and other periampullary cancers (histology not required) Biliary obstructive symptoms or signs Bilirubin level at/above 100 umol per liter (5.8 mg/dL) Distal biliary obstruction consistent with pancreatic cancer, distal CBD cholangiocarcinoma or other periampullary malignancy Location of distal biliary obstruction is such that it would allow the proximal end of a stent to be positioned at least 2cm from the hilum Patients deemed as resectable by pancreatic protocol CT or MRI Surgical candidate per pancreatobiliary surgeon after multi-disciplinary discussion Surgery intent within 4 weeks Endoscopic and surgical treatment to be provided by same team", "candidate_expression": "((Age 18 or older) AND (Bilirubin level at/above 100 umol per liter at/above 5.8 mg/dL) AND (Distal biliary obstruction) AND (Surgery intent within 4 weeks) AND (Surgical candidate per pancreatobiliary surgeon) AND (deemed as resectable) AND (distal biliary obstruction) AND (stent would allow at least 2cm from the hilum) AND ((Biliary obstructive signs) OR (Biliary obstructive symptoms)) AND ((distal CBD cholangiocarcinoma) OR (pancreatic cancer) OR (periampullary malignancy other)) AND ((pancreatic protocol CT) OR (pancreatic protocol MRI)) AND ((Endoscopic treatment) OR (surgical treatment)) AND ((distal common bile duct (CBD) cholangiocarcinoma) OR (pancreatic cancer) OR (periampullary cancers other)))"}
{"candidate_id": "LLM05313", "doc_id": "NCT03639545_exc", "case_bucket": "or", "source_criterion": "diagnosed advanced heart, kidney or liver failure benign prostatic hyperplasia prostatic carcinoma frequent urinary tract infections non-type 1 diabetes mellitus", "candidate_expression": "((advanced heart failure) AND (benign prostatic hyperplasia) AND (frequent) AND (kidney failure) AND (liver failure) AND (non-type 1 diabetes mellitus) AND (prostatic carcinoma) AND (urinary tract infections))"}
{"candidate_id": "LLM05314", "doc_id": "NCT03356834_exc", "case_bucket": "or", "source_criterion": "Co-infected with HCV, HIV or other viral hepatitis, Diagnosis of HCC", "candidate_expression": "((HCC) AND ((HCV) OR (HIV) OR (viral hepatitis other)))"}
{"candidate_id": "LLM05315", "doc_id": "NCT03329456_exc", "case_bucket": "or", "source_criterion": "Exclusion criteria are pregnancy, patients with contraindications to regional anesthesia, allergy to LAs, patients taking opioids regularly due to chronic pain, use of anticoagulation drugs other than acetylsalicylic acid or dipyridamole, atrioventricular block, diabetes.", "candidate_expression": "((LAs) AND (chronic pain) AND (regional anesthesia) AND ((acetylsalicylic acid) OR (dipyridamole)) AND ((allergy) OR (anticoagulation drugs) OR (atrioventricular block) OR (contraindications) OR (diabetes) OR (opioids regularly) OR (pregnancy)))"}
{"candidate_id": "LLM05316", "doc_id": "NCT02371200_exc", "case_bucket": "other", "source_criterion": "1. Does not have a documented history of generalized seizures. 2. Has not had a GTC seizure within the last year AND is not expected to have a reduction of anti-epileptic drugs during their hospital admission. 3. Intracranial EEG electrodes are being used 4. The subject's upper arm circumference not adequate for proper fit of the EMG monitor (less than 14cm). 5. Pregnant female. 6. Subject/Caregiver is unable to provide consent.", "candidate_expression": "((Intracranial EEG electrodes) AND (Pregnant less than 14cm) AND (Subject/Caregiver is unable to provide consent.) AND (anti-epileptic drugs) AND (female) AND (upper arm circumference adequate for proper fit of the EMG monitor) AND NOT (GTC seizure within the last year) AND NOT (reduction of anti-epileptic drugs during their hospital admission) AND NOT (generalized seizures history))"}
{"candidate_id": "LLM05317", "doc_id": "NCT02323399_inc", "case_bucket": "or", "source_criterion": "Subject's age is between =12 and 16 years, inclusive Subject is scheduled for a procedure that requires general or neuraxial anesthesia Subjects must have normal or clinically acceptable physical exam Subjects with controlled diabetes prior to entry must have a mean systolic/diastolic office blood pressure =128/78 mmHg (sitting, after 5 minutes of rest) Females must have a urine or serum pregnancy test (Human Chorionic Gonadotropin) that is negative at Screening and Day 1 Subject's parent or legal guardian gives informed consent and subject gives assent.", "candidate_expression": "((Human Chorionic Gonadotropin at Screening Day 1) AND (Subject's parent or legal guardian gives informed consent and subject gives assent.) AND (age between =12 and 16 years) AND (diabetes controlled prior to entry) AND (mean diastolic blood pressure 78 mmHg) AND (mean systolic blood pressure 128 mmHg) AND (physical exam) AND (procedure) AND (scheduled for a procedure) AND ((clinically acceptable) OR (normal)) AND ((serum pregnancy test) OR (urine pregnancy test)) AND ((general t) OR (neuraxial anesthesia)))"}
{"candidate_id": "LLM05318", "doc_id": "NCT00994786_inc", "case_bucket": "scope", "source_criterion": "Must be an outpatient with a primary DSM-IV Obsessive-Compulsive Disorder. Patients must have a score of greater than 20 on the Yale-Brown Obsessive Compulsive Scale (Y-BOCS; Goodman et al., 1989b). Diagnosis of comorbid DSM-IV major depressive episode will be allowed in the study provided that the diagnosis is secondary to OCD, they have a baseline Montgomery Depression Rating Scale (MADRS) score of less than or equal to 19, and the onset of OCD predates the onset of the current episode of depression by five or more years. The ability to comprehend and comply with protocol requirements. Written consent must be provided prior to study entry. All women of childbearing potential (WOCBP) must be practicing a medically acceptable method of birth control All female subjects of childbearing potential (WOCBP), including those who are practicing a medically acceptable method of birth control, must have a negative serum pregnancy test within 72 hours prior to the start of study medication.", "candidate_expression": "((All female subjects of childbearing potential (WOCBP), including those who are practicing a medically acceptable method of birth control, must have a negative serum pregnancy test within 72 hours prior to the start of study medication) AND (DSM-IV) AND (MADRS) AND (Montgomery Depression Rating Scale) AND (OCD) AND (Obsessive-Compulsive Disorder) AND (The ability to comprehend and comply with protocol requirements) AND (WOCBP) AND (Written consent must be provided prior to study entry.) AND (Y-BOCS) AND (Yale-Brown Obsessive Compulsive Scale) AND (baseline) AND (birth control) AND (childbearing potential) AND (comorbid) AND (major depressive episode) AND (medically acceptable) AND (onset of OCD) AND (onset of the current episode of depression) AND (outpatient) AND (predates the onset of the current episode of depression by five or more years) AND (primary) AND (score of greater than 20) AND (score of less than or equal to 19) AND (women))"}
{"candidate_id": "LLM05319", "doc_id": "NCT03033745_exc", "case_bucket": "other", "source_criterion": "Ongoing serious bacterial infections at the time of screening. Other significant medical conditions that could increase the risk to the subject. Females who are pregnant, breast feeding, or planning a pregnancy during the course study. Participation in a study with an Investigational Medicinal Product (IMP) other than IgPro20 within three months prior to enrollment.", "candidate_expression": "((Females who are pregnant, breast feeding, or planning a pregnancy during the course study.) AND (at the time of screening) AND (bacterial infections) AND (screening) AND (serious))"}
{"candidate_id": "LLM05320", "doc_id": "NCT02606565_exc", "case_bucket": "other", "source_criterion": "Newborns with severe congenital anomalies Newborns with infection of the umbilical cord at birth", "candidate_expression": "((Newborns) AND (infection of the umbilical cord at birth) AND (severe congenital anomalies))"}
{"candidate_id": "LLM05321", "doc_id": "NCT02552459_inc", "case_bucket": "other", "source_criterion": "patients undergoing venous malformation embolization operation through general anesthesia. aged 18-65 years old. operating time varies 1-4h,and extubation after the operation.", "candidate_expression": "((1-4h) AND (18-65 years old) AND (after the operation) AND (aged) AND (extubation) AND (general anesthesia) AND (operating time) AND (operation) AND (the operation) AND (venous malformation embolization operation))"}
{"candidate_id": "LLM05322", "doc_id": "NCT02918851_exc", "case_bucket": "or", "source_criterion": "Any significant acute or chronic medical illness or problem, including, but not limited to, diabetes, hypertension, cardiac disease, asthma, chronic obstructive lung disease Current or recent (last 60 days) tobacco or nicotine use History of sickle cell trait or disease or any other acquired or hereditary hematological abnormality History of fainting or other significant adverse reaction during phlebotomy or donation of blood Known prolonged QTc (or evidence of such at screening) on electrocardiogram defined as >470 ms Known or suspected illicit drug or alcohol abuse Known or suspected HIV, Hepatitis B, or Hepatitis C infection History of thrombophilia or anticoagulant therapy Pregnancy Obesity defined as BMI>30 Recent history of blood donation: a) Single whole blood unit donation within the past 8 weeks; b) Double RBC donation by apheresis within the past 16 weeks; or c) Plasma donation by apheresis within the past 4 weeks Inadequate RBC mass based on TBV <4500 ml (above) or screening Hb <14 g/dL", "candidate_expression": "((BMI >30) AND (Obesity) AND (Pregnancy) AND (QTc >470 ms) AND (RBC mass Inadequate) AND (blood donation) AND (electrocardiogram) AND (medical illness) AND ((nicotine use) OR (tobacco use)) AND ((acquired hematological abnormality) OR (hereditary hematological abnormality) OR (sickle cell disease) OR (sickle cell trait)) AND ((adverse reaction) OR (fainting)) AND ((donation of blood) OR (phlebotomy)) AND ((alcohol abuse) OR (illicit drug abuse)) AND ((HIV infection) OR (Hepatitis B infection) OR (Hepatitis C infection)) AND ((anticoagulant therapy) OR (thrombophilia)) AND ((asthma) OR (cardiac disease) OR (chronic obstructive lung disease) OR (diabetes) OR (hypertension)) AND ((Hb <14 g/dL) OR (TBV <4500 ml)) AND ((acute) OR (chronic)))"}
{"candidate_id": "LLM05323", "doc_id": "NCT02844907_inc", "case_bucket": "or", "source_criterion": "Body Mass Index (BMI) = 35 kg/m2 HbA1c = 5.7% Ability to speak and understand English", "candidate_expression": "((= 35 kg/m2) AND (= 5.7%) AND (Ability to speak English) AND (Ability to understand English) AND (Body Mass Index (BMI)) AND (HbA1c))"}
{"candidate_id": "LLM05324", "doc_id": "NCT02759861_exc", "case_bucket": "or", "source_criterion": "Pregnant women and nursing mothers are ineligible due to the possible risk of adverse effects in the newborn. Eligible patients of reproductive potential should use adequate contraception if sexually active. Serious concurrent medical illness which would jeopardize the ability of the subject to receive the therapy as outlined in this protocol with reasonable safety. Malignancy diagnosed or treated within 5 years (recent localized treatment of squamous or non-invasive basal cell skin cancers is permitted; cervical carcinoma in situ is allowed if appropriately treated prior to screening); subjects under evaluation for a malignancy are not eligible. Infection with hepatitis B virus (HBV) or human immunodeficiency virus (HIV) Use of any prohibited concomitant medications within 30 days of the Baseline/Day 1 visit. Known hypersensitivity to LDV/SOF", "candidate_expression": "((Malignancy within 5 years) AND (Pregnant women and nursing mothers are ineligible due to the possible risk of adverse effects in the newborn. Eligible patients of reproductive potential should use adequate contraception if sexually active.) AND (Serious concurrent medical illness which would jeopardize the ability of the subject to receive the therapy as outlined in this protocol with reasonable safety.) AND (Use of any prohibited concomitant medications within 30 days of the Baseline/Day 1 visit.) AND (hypersensitivity) AND (treated appropriately prior to screening) AND NOT (cervical carcinoma in situ) AND NOT (treatment localized recent) AND ((hepatitis B virus (HBV)) OR (human immunodeficiency virus (HIV))) AND ((LDV) OR (SOF)) AND ((non-invasive basal cell skin cancer) OR (squamous cell skin cancer)))"}
{"candidate_id": "LLM05325", "doc_id": "NCT03113253_exc", "case_bucket": "or", "source_criterion": "Subjects with a history of hypercoagulopathy, deep vein thrombosis (DVT), pulmonary embolism Renal impairment Subjects with known hypersensitivity to tranexamic acid Consecutive fibrinolytic states to coagulopathy History of convulsions", "candidate_expression": "((DVT) AND (History) AND (Renal impairment) AND (coagulopathy) AND (convulsions) AND (deep vein thrombosis) AND (fibrinolytic states) AND (history) AND (hypercoagulopathy) AND (hypersensitivity) AND (pulmonary embolism) AND (tranexamic acid))"}
```
