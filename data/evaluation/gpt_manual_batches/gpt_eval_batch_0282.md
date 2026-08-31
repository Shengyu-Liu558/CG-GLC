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
{"candidate_id": "LLM07026", "doc_id": "NCT03541980_inc", "case_bucket": "other", "source_criterion": "Any patient age 4-16 years with sickle cell disease who presents the Pediatric ER with acute sickle cell pain crisis with a pain of 6/10 or higher", "candidate_expression": "((Pediatric ER) AND (acute sickle cell pain crisis) AND (age 4-16 years) AND (pain 6/10 or higher) AND (sickle cell disease))"}
{"candidate_id": "LLM07027", "doc_id": "NCT02560766_exc", "case_bucket": "or", "source_criterion": "History of a primary sleep disorder other than RLS that may significantly affect the symptoms of RLS. Serum ferritin level < 20 ng/mL at screening. History of allergy, hypersensitivity, or intolerance to HORIZANT or any other gabapentin products (eg, Neurontin®, Gralise®). Suffering from a movement disorder that could mimic or confound the accurate diagnosis of RLS (eg, Tourette's syndrome, tic disorder, periodic limb movement disorder [PLMD], sleep disorders). Currently meet Diagnostic and Statistical Manual of Mental Disorders - Fifth Edition (DSM-5) criteria for substance use disorder, or history thereof, within 12 months before dosing. Current or past history of any significant psychiatric disorder including, but not limited to, depression (treatment with antidepressants), bipolar disorder, or schizophrenia. Diagnosis of attention-deficit hyperactivity disorder (ADHD) is allowed, provided the patient is not receiving medication(s) known to affect the assessment of RLS. History of suicidal behavior or suicidal ideation as indicated by the C-SSRS, administered at screening (the questionnaire is provided in Appendix 4), and as per investigator's judgment. History of seizure disorder or at increased risk for development of a seizure disorder including, but not limited to, complicated febrile seizure and history of significant head injury. Medical condition or disorder that would interfere with the action, absorption, distribution, metabolism, or excretion of gabapentin enacarbil, or, in the investigator's judgment is considered to be clinically significant and may pose a safety concern, or, could interfere with the accurate assessment of safety or efficacy, or could potentially affect a patient's safety or study outcome. Clinically significant abnormal laboratory result or physical examination finding not resolved by the time of baseline assessments.", "candidate_expression": "((< 20 ng/mL) AND (ADHD) AND (DSM-5) AND (Diagnostic and Statistical Manual of Mental Disorders - Fifth Edition) AND (PLMD) AND (RLS) AND (Serum ferritin) AND (allowed) AND (antidepressants) AND (attention-deficit hyperactivity disorder) AND (movement disorder) AND (other) AND (primary sleep disorder) AND (psychiatric disorder) AND (seizure disorder) AND (significant) AND (substance use disorder) AND (within 12 months) AND ((HORIZANT) OR (gabapentin)) AND ((Gralise) OR (Neurontin)) AND ((Tourette's syndrome) OR (periodic limb movement disorder) OR (sleep disorders) OR (tic disorder)) AND ((bipolar disorder) OR (depression) OR (schizophrenia)) AND ((suicidal behavior) OR (suicidal ideation)) AND ((complicated febrile seizure) OR (head injury)) AND ((allergy) OR (hypersensitivity) OR (intolerance)))"}
{"candidate_id": "LLM07028", "doc_id": "NCT02270970_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07029", "doc_id": "NCT00305097_inc", "case_bucket": "other", "source_criterion": "Aged at least 18 years with an ability and willingness to give written informed consent. Body mass index 25-35 kg/m2 Users of at least 2 cups of caffeinated coffee per day who are willing to be randomized to any of the interventions. Non-smoking", "candidate_expression": "((Aged at least 18 years) AND (Body mass index 25-35 kg/m2) AND (Non-smoking) AND (ability to give written informed consent) AND (caffeinated coffee at least 2 cups per day) AND (willing to be randomized) AND (willingness to give written informed consent))"}
{"candidate_id": "LLM07030", "doc_id": "NCT02552459_exc", "case_bucket": "or", "source_criterion": "long-term use of analgesics,sedatives or non steroidal anti-inflammatory drugs history. known for dexmedetomidine or other drugs allergy in this study. cannot communicate. preoperative systolic blood pressure <90 mmHg, or the heart rate <50/min.", "candidate_expression": "((allergy) AND (analgesics) AND (cannot communicate) AND (dexmedetomidine) AND (drugs other) AND (heart rate <50/min) AND (non steroidal anti-inflammatory drugs history) AND (preoperative systolic blood pressure <90 mmHg) AND (sedatives))"}
{"candidate_id": "LLM07031", "doc_id": "NCT03151603_inc", "case_bucket": "or", "source_criterion": "Women (18-75 years) with suspected UTI at least two symptoms of UTI (dysuria, urgency of micturition, frequency, lower abdominal pain) Written informed consent", "candidate_expression": "((18-75) AND (UTI) AND (Women) AND (Written informed consent) AND (at least two) AND (suspected) AND (symptoms of UTI) AND (years) AND ((dysuria) OR (frequency) OR (lower abdominal pain) OR (urgency of micturition)))"}
{"candidate_id": "LLM07032", "doc_id": "NCT03151603_exc", "case_bucket": "or", "source_criterion": "signs of complicated UTI (e. g. temperature > 38°C, loin tenderness) conditions that may lead to complicated infections (i.e. renal diseases, patients with urinary catheter) pregnancy/ breastfeeding current self-medication with UU preparations e.g. z.B. Cystinol®, Uvalysat®, Arctuvan® antibiotic use in the last 7 days previous UTI in the past 2 weeks history of pyelonephritis contraindications for trial drugs serious diseases inability to understand trial Information current participation in another clinical trial or participation in another clinical trial within the last 4 weeks", "candidate_expression": "((> 38°C) AND (UTI) AND (UU preparations) AND (antibiotic) AND (complicated UTI) AND (complicated infections) AND (conditions) AND (contraindications for) AND (diseases) AND (drugs) AND (inability to understand trial Information) AND (last 7 days) AND (past 2 weeks) AND (pregnancy/ breastfeeding) AND (pyelonephritis) AND (self-medication) AND (serious) AND (trial) AND (urinary catheter) AND ((patients) OR (renal diseases)) AND ((Arctuvan®) OR (Uvalysat®) OR (z.B. Cystinol®)) AND ((loin tenderness) OR (temperature)))"}
{"candidate_id": "LLM07033", "doc_id": "NCT02607319_inc", "case_bucket": "or", "source_criterion": "History of three or more consecutively failed In Vitro Fertilization (IVF) cycles after embryo transfer. Normal uterine cavity (as assessed by hysteroscopy or HSG). Normal hormonal investigation: TSH, PRL, FBS. Normal acquired/inherited thrombophilia profile: LAC, ACA IgG/IgM, Prot S, Antithrombin III, beta-2 glycoprotein, Factors V, II, MTHFR. Normal semen analysis and mild/moderate male factor (Total motile sperm count > 5 million/ml and/or normal WHO morphology >20%. Patient provides written informed consent.", "candidate_expression": "((ACA IgG) AND (ACA IgM) AND (Antithrombin III) AND (FBS) AND (Factors II) AND (Factors V) AND (IVF) AND (In Vitro Fertilization three or more consecutively failed after embryo transfer) AND (LAC) AND (MTHFR) AND (PRL) AND (Patient provides written informed consent) AND (Prot S) AND (TSH) AND (beta-2 glycoprotein) AND (hormonal investigation: Normal) AND (male factor) AND (semen analysis) AND (thrombophilia profile Normal) AND ((HSG) OR (hysteroscopy)) AND ((mild) OR (moderate)) AND ((Total motile sperm count > 5 million/ml) OR (normal WHO morphology >20%)))"}
{"candidate_id": "LLM07034", "doc_id": "NCT02652637_inc", "case_bucket": "other", "source_criterion": "Patients undergoing colon resection", "candidate_expression": "(colon resection undergoing)"}
{"candidate_id": "LLM07035", "doc_id": "NCT02321839_inc", "case_bucket": "or", "source_criterion": "Signed informed consent form Male or female of aged 50 years or older Typical AMD and PCV patients BCVA of 24 letters or over", "candidate_expression": "((AMD) AND (BCVA 24 letters or over) AND (Male) AND (PCV patients) AND (Signed informed consent form) AND (aged 50 years or older) AND (female))"}
{"candidate_id": "LLM07036", "doc_id": "NCT02385448_inc", "case_bucket": "or", "source_criterion": "Good general health Older than the age of legal consent (i.e. 18 years old) Sonographic diagnosis of ovarian endometrioma with diameter at least 4cm on 2 separate scans at least 6 weeks apart No contraindication to use of progesterone or combined oral contraceptive pills Not attempting to conceive either at the time of study entry or for at least 2 years after surgery Willing and able to participate after the study has been explained", "candidate_expression": "((18 years old) AND (2 separate scans) AND (Good general health) AND (No) AND (Not) AND (Older than the age of legal consent) AND (Sonographic) AND (age) AND (at least 6 weeks apart) AND (at the time of study entry) AND (attempting) AND (combined oral contraceptive pills) AND (conceive) AND (contraindication) AND (diameter at least 4cm) AND (for at least 2 years after surgery) AND (ovarian endometrioma) AND (progesterone))"}
{"candidate_id": "LLM07037", "doc_id": "NCT03077204_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07038", "doc_id": "NCT02370069_exc", "case_bucket": "or", "source_criterion": "immunization with PPV23 within the last year any confirmed or suspected immunodeficiency condition, including human immunodeficiency virus (HIV) infection, haematological malignancy, or a congenital immunodeficiency history of allergic disease or reactions likely to be exacerbated by any component of the vaccine history of allergic disease likely to be stimulated by the vaccination history or records of immunosuppressive therapy (with the exception of topical corticosteroids) for more than 14 days and within 6 months of vaccination history or evidence of administration of immunoglobulins and/or any blood products during the study period or within the three months preceding the study vaccine use of any other investigational or non-registered drug or vaccine during the study period or within 30 days preceding the study vaccine administration of a vaccine during the period starting one month before the dose of vaccine and ending one month after pregnancy", "candidate_expression": "((HIV) AND (PPV23 within the last year confirmed) AND (allergic disease stimulated by the vaccination) AND (for more than 14 days of vaccination vaccination) AND (immunization) AND (immunodeficiency condition suspected) AND (pregnancy) AND (vaccination) AND (vaccine) AND (vaccine during the period starting one month before the dose of vaccine and ending one month after) AND (within 6 months of vaccination vaccination) AND ((immunosuppressive therapy) AND NOT (topical corticosteroids)) AND ((congenital immunodeficiency) OR (haematological malignancy) OR (human immunodeficiency virus infection)) AND ((allergic disease) OR (allergic reactions)) AND ((blood products) OR (immunoglobulins)) AND ((during the study period study period) OR (within the three months preceding the study vaccine study vaccine)) AND ((drug) OR (vaccine)) AND ((investigational) OR (non-registered)) AND ((during the study period study period) OR (within 30 days preceding the study vaccine study vaccine)))"}
{"candidate_id": "LLM07039", "doc_id": "NCT02035800_inc", "case_bucket": "other", "source_criterion": "Patients aged of 18 and over, Satisfying the 1987 American College of Rheumatology (ACR) criteria for RA Receiving a prescription of Adalimumab 40 mg subcutaneous every two weeks.", "candidate_expression": "((Adalimumab 40 mg every two weeks subcutaneous) AND (RA 1987 American College of Rheumatology (ACR) criteria) AND (aged 18 and over))"}
{"candidate_id": "LLM07040", "doc_id": "NCT02558504_exc", "case_bucket": "or", "source_criterion": "Aged under 18, Lack of informed consent signed, Radiofrequency treatment history, on going neoplastic history with a short prognosis, Concomitant participation in another clinical study Contraindication to general anesthesia, Patient with an esophageal location of scleroderma Presence of a cardiac pacemaker or stimulator Pregnant women or likely to be in the absence of effective contraception, Esophageal stenosis preventing the passage of an endoscope, Histology other than glandular neoplasia, History of or current history of esophageal cancer invading the submucosal layer of the esophagus or more, Surgical treatment history (except anti-reflux treatment) or esophageal radiotherapy, previous esophageal treatment by another method ablation: photodynamic therapy, argon plasma coagulation, laser, .... Esophageal varices observed in endoscopy, Coagulopathy or taking anticoagulants responsible an INR> 1.3 or a platelet count <75,000 per microL, Life expectancy of less than 3 years, due to intercurrent disease, especially neoplastic, Liver cirrhosis (Child-Pugh all stages) Respiratory failure: Renal failure (Cl Cr < 60 mL /min /1,73m), Heart attack within the last six months or progressive coronary artery disease, Severe distal arteriopathie > stage II of Leriche and Fontaine", "candidate_expression": "((< 60 mL /min /1,73m) AND (<75,000 per microL) AND (> 1.3) AND (> II) AND (Aged) AND (Child-Pugh) AND (Cl Cr) AND (Coagulopathy) AND (Concomitant) AND (Contraindication) AND (Esophageal stenosis) AND (Esophageal varices) AND (Heart attack) AND (Histology) AND (History) AND (INR) AND (Lack of) AND (Life expectancy) AND (Liver cirrhosis) AND (Pregnant) AND (Radiofrequency treatment) AND (Renal failure) AND (Respiratory failure) AND (Severe) AND (Surgical treatment) AND (ablation) AND (all stages) AND (another method) AND (anti-reflux treatment) AND (anticoagulants) AND (argon plasma coagulation) AND (cardiac pacemaker) AND (cardiac stimulator) AND (current) AND (distal arteriopathie) AND (endoscope) AND (endoscopy) AND (esophageal cancer) AND (esophageal location) AND (esophageal radiotherapy) AND (esophageal treatment) AND (except) AND (general anesthesia) AND (glandular neoplasia) AND (history) AND (in the absence of effective contraception) AND (informed consent signed) AND (intercurrent disease) AND (invading the submucosal layer of the esophagus) AND (laser) AND (less than 3 years) AND (likely to be) AND (neoplastic) AND (on going) AND (other than) AND (participation in another clinical study) AND (passage of an endoscope) AND (photodynamic therapy) AND (platelet count) AND (preventing the) AND (previous) AND (prognosis) AND (progressive coronary artery disease) AND (scleroderma) AND (short) AND (stage of Leriche and Fontaine) AND (the last six months) AND (under 18) AND (within the last six months) AND (women))"}
{"candidate_id": "LLM07041", "doc_id": "NCT03062358_inc", "case_bucket": "or", "source_criterion": "Has a HCC diagnosis confirmed by radiology, histology, or cytology (fibrolamellar, and mixed hepatocellular/cholangiocarcinoma subtypes are not eligible) Has Barcelona Clinic Liver Cancer (BCLC) Stage C disease or BCLC Stage B disease not amenable to locoregional therapy or refractory to locoregional therapy and not amenable to a curative treatment approach Has a Child-Pugh A liver score within 7 days prior to first dose of study medication Has a life expectancy of >3 months Has at least one measurable lesion based on RECIST version 1.1 as determined by investigator Has Eastern Cooperative Oncology Group (ECOG) performance status of 0 or 1 performed within 7 days prior to receiving the first dose of study medication Has documented objective radiographic progression during or after treatment with sorafenib or oxaliplatin-based chemotherapy, or else intolerance to sorafenib or oxaliplatin-based chemotherapy Female participants of childbearing potential must have a negative urine or serum pregnancy test within 72 hours prior to receiving the first dose of study therapy Female and male participants of reproductive potential must agree to use adequate contraception starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication", "candidate_expression": "((0 or 1) AND (>3 months) AND (A) AND (BCLC) AND (Barcelona Clinic Liver Cancer (BCLC)) AND (Child-Pugh liver score) AND (Eastern Cooperative Oncology Group (ECOG) performance status) AND (Female) AND (Female and male participants of reproductive potential must agree to use adequate contraception starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication) AND (Female participants of childbearing potential must have a negative urine or serum pregnancy test within 72 hours prior to receiving the first dose of study therapy) AND (HCC) AND (RECIST version 1.1) AND (Stage B) AND (Stage C) AND (adequate contraception) AND (amenable to a curative treatment approach) AND (at least one) AND (chemotherapy) AND (childbearing potential) AND (during or after) AND (first dose of study medication) AND (lesion) AND (life expectancy) AND (measurable) AND (mixed hepatocellular/cholangiocarcinoma subtype) AND (negative) AND (not) AND (not eligible) AND (objective progression) AND (oxaliplatin) AND (receiving the first dose of study medication) AND (receiving the first dose of study therapy) AND (reproductive potential) AND (sorafenib) AND (sorafenib or oxaliplatin-based) AND (subtype fibrolamellar) AND (treatment with sorafenib or oxaliplatin-based chemotherapy) AND (within 7 days prior) AND (within 72 hours prior) AND ((disease)) AND ((amenable to locoregional therapy) OR (refractory to locoregional therapy)) AND ((cytology) OR (histology) OR (radiology)) AND ((intolerance) OR (radiographic)) AND ((pregnancy test urine) OR (serum pregnancy test)) AND ((Female) OR (male)))"}
{"candidate_id": "LLM07042", "doc_id": "NCT02787863_exc", "case_bucket": "or", "source_criterion": "Vaccination against pneumococcal infection in anamnesis; Application of preparations of immune globulin or blood transfusion within last three months prior to clinical studies; Prolonged use (more than 14 days) immunosuppressants or other immunosuppressive drugs within 6 months prior to the start of the study; Any confirmed or suspected immunosuppressive or immunodeficient condition, including HIV infection; A history or currently hematologic and other cancers; A positive reaction for HIV infection, viral hepatitis B and hepatitis C; The presence of respiratory, cardio-vascular insufficiency, impaired liver and kidney function, established during a physical examination at visit number 1; Pronounced congenital defects or serious chronic diseases in the acute stage, including any clinically important exacerbation of chronic diseases of the liver, kidney, cardiovascular, nervous system, mental diseases or metabolic disorders, confirmed by the history or objective examination (pulmonary: cystic fibrosis, lung abscess, empyema, active tuberculosis; extra-pulmonary: congestive heart failure, malabsorption, chronic renal and hepatic failure, cirrhosis, malignancy, immunodeficiency, cirrhosis of the liver); Severe allergic reactions in anamnesis of autoimmune disease; The presence of acute infectious and/or communicable illnesses within 1 month prior to study; History of chronic alcohol abuse and/or drug use; Exacerbation of chronic diseases; Breastfeeding; Pregnancy; Participation in any other clinical study within the last 3 months.", "candidate_expression": "((Breastfeeding) AND (Exacerbation) AND (HIV infection) AND (Participation in clinical study any other within the last 3 months) AND (Pregnancy) AND (Vaccination) AND (allergic reactions Severe) AND (chronic diseases) AND (communicable illnesses) AND (diseases of the cardiovascular system) AND (diseases of the kidney) AND (diseases of the liver) AND (diseases of the nervous system) AND (hepatic failure) AND (infectious illnesses) AND (more than 14 days) AND (pneumococcal infection) AND (renal failure) AND ((immunodeficient condition) OR (immunosuppressive condition)) AND ((reaction for HIV infection) OR (reaction for hepatitis C) OR (reaction for viral hepatitis B)) AND ((cardio-vascular insufficiency) OR (impaired kidney function) OR (impaired liver) OR (respiratory insufficiency)) AND ((chronic diseases serious acute stage) OR (congenital defects)) AND ((exacerbation) OR (mental diseases) OR (metabolic disorders)) AND ((blood transfusion) OR (preparations of immune globulin)) AND ((cirrhosis) OR (cirrhosis of the liver) OR (congestive heart failure) OR (cystic fibrosis) OR (empyema) OR (immunodeficiency) OR (lung abscess) OR (malabsorption) OR (malignancy) OR (tuberculosis active)) AND ((alcohol abuse) OR (drug use)) AND ((immunosuppressants) OR (immunosuppressive drugs other)))"}
{"candidate_id": "LLM07043", "doc_id": "NCT02056288_inc", "case_bucket": "other", "source_criterion": "Supracondylar fracture Age 2-17 years American Society of Anesthesiologists Status 1 -3 Scheduled for closed reduction with percutaneous pinning under general anesthesia", "candidate_expression": "((1 -3) AND (2-17 years) AND (Age) AND (American Society of Anesthesiologists Status) AND (Scheduled for) AND (Supracondylar fracture) AND (closed reduction with percutaneous pinning) AND (general anesthesia))"}
{"candidate_id": "LLM07044", "doc_id": "NCT03360981_exc", "case_bucket": "or", "source_criterion": "acute myocardial infarction, heart failure, neoplastic disease, chronic diseases that may affect the inflammatory profile both systemic and epicardial (cancer, chronic intestinal inflammation, hepatitis, AIDS); life expectancy < 6 months, previous CABG and/or other open heart surgery intervention, acute coronary syndrome", "candidate_expression": "((AIDS) AND (CABG previous) AND (acute coronary syndrome) AND (acute myocardial infarction) AND (cancer systemic epicardial) AND (chronic diseases may affect the inflammatory profile) AND (chronic intestinal inflammation) AND (heart failure) AND (hepatitis) AND (life expectancy < 6 months) AND (neoplastic disease) AND (open heart surgery intervention other))"}
{"candidate_id": "LLM07045", "doc_id": "NCT02567214_inc", "case_bucket": "other", "source_criterion": "Age > 50 years Smoking history > 10 packs/year FEV1 30 - 79% of predicted and FEV1/FVC < 70% (GOLD 2-3) FRC > 120 % predicted Borg dyspnea score > 3 during the 3-min constant rate shuttle walking test at V3", "candidate_expression": "((Age > 50 years) AND (Borg dyspnea score > 3 3-min constant rate shuttle walking test) AND (FEV1 30 - 79% of predicted) AND (FEV1/FVC < 70%) AND (FRC > 120 % predicted) AND (GOLD 2-3) AND (Smoking history > 10 packs/year))"}
{"candidate_id": "LLM07046", "doc_id": "NCT02687724_exc", "case_bucket": "or", "source_criterion": "Female subjects who are pregnant or breast-feeding or considering becoming pregnant during the study Patients aged <18 years of age Patients who cannot give informed consent, Pregnant patients or those who are breastfeeding will be deemed ineligible. Prior treatment with any anti-TNF agent Contra-indication to use of GLM (Hypersensitivity to the active substance or to any of the excipients; Active tuberculosis (TB), acute or chronic Hepatitis B infection or other severe infections such as sepsis and/or opportunistic infections including HIV infection; Moderate or severe heart failure (NYHA class III/IV) Have symptoms or signs suggestive of current active or latent TB upon medical history, physical examination and/or chest radiograph, or positive Mycobacterium tuberculosis antigen-specific interferon-gamma release assay (IGRA) Patients with a history of, or at imminent risk for, colectomy; who required gastrointestinal surgery within 2 months before screening; History of colonic mucosal dysplasia or adenomatous colonic polyps that were not removed Screening stool study positive for enteric pathogens or Clostridium difficile toxin. Oral corticosteroids at a dose >40 mg prednisone or its equivalent per day; receipt of cyclosporine, tacrolimus, sirolimus, or mycophenolate mofetil within 8 weeks before the first study agent injection; or use of an investigational agent within 5 half-lives of that agent before the first study agent injection. Patients in recent receipt of live vaccinations within 4 weeks prior to enrolment", "candidate_expression": "((<18 years of age) AND (>40 mg prednisone per day) AND (Active) AND (Contra-indication) AND (Female subjects who are pregnant or breast-feeding or considering becoming pregnant during the study) AND (GLM) AND (HIV infection) AND (Mycobacterium tuberculosis antigen-specific interferon-gamma release assay (IGRA)) AND (NYHA) AND (Pregnant patients or those who are breastfeeding will be deemed ineligible) AND (Prior) AND (TB) AND (aged) AND (anti-TNF agent) AND (before the first study agent injection) AND (class III/IV) AND (colectomy) AND (current) AND (gastrointestinal surgery) AND (live vaccinations) AND (not) AND (positive) AND (removed) AND (sepsis) AND (stool study) AND (treatment) AND (within 2 months before screening) AND (within 4 weeks prior to enrolment) AND (within 5 half-lives) AND (within 8 weeks before the first study agent injection) AND ((active substance) OR (excipients)) AND ((acute) OR (chronic)) AND ((Hepatitis B infection) OR (Hypersensitivity) OR (heart failure) OR (opportunistic infections) OR (severe infections) OR (tuberculosis (TB))) AND ((Moderate) OR (severe)) AND ((active) OR (latent)) AND ((chest radiograph) OR (medical history) OR (physical examination)) AND ((history of) OR (imminent risk for)) AND ((adenomatous colonic polyps) OR (colonic mucosal dysplasia)) AND ((Clostridium difficile toxin) OR (enteric pathogens)) AND ((Oral corticosteroids) OR (investigational agent)) AND ((cyclosporine) OR (mycophenolate mofetil) OR (sirolimus) OR (tacrolimus)))"}
{"candidate_id": "LLM07047", "doc_id": "NCT02871206_exc", "case_bucket": "or", "source_criterion": "Anaphylactic reaction to a previous dose of influenza vaccine or to any of its components Known Immunoglobulin E (IgE)-mediated hypersensitivity to eggs manifested as hives, swelling of the mouth and throat, difficulty in breathing, hypotension, or shock Guillain- Barré syndrome within eight weeks of a previous influenza vaccine Use of aspirin or salicylate- containing products within 30 days before enrollment Household members of children in Group A", "candidate_expression": "((Anaphylactic reaction) AND (Group A) AND (Guillain- Barré syndrome within eight weeks of a previous influenza vaccine) AND (Household members) AND (Immunoglobulin E (IgE)-mediated hypersensitivity) AND (children) AND (eggs) AND (influenza vaccine previous) AND ((difficulty in breathing) OR (hives) OR (hypotension) OR (shock) OR (swelling of the mouth) OR (swelling of the throat)) AND ((aspirin) OR (salicylate- containing products)) AND ((influenza vaccine) OR (its components)))"}
{"candidate_id": "LLM07048", "doc_id": "NCT02464865_exc", "case_bucket": "or", "source_criterion": "pathological obesity chronic diseases e.g. cerebral palsy, metabolic disease, etc. diseases of red blood cells on medication e.g. steroid, multivitamins, thiamine-containing vitamins, diuretic drugs hemodialysis or peritoneal dialysis bariatric surgery", "candidate_expression": "((bariatric surgery) AND (chronic diseases) AND (diseases of red blood cells) AND (pathological obesity) AND ((diuretic drugs) OR (multivitamins) OR (steroid) OR (thiamine-containing vitamins)) AND ((hemodialysis) OR (peritoneal dialysis)) AND ((cerebral palsy) OR (metabolic disease)))"}
{"candidate_id": "LLM07049", "doc_id": "NCT03255044_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to statin Treatment with statins during the past month prior to study. Serum creatinine > 3 mg/dl Significant liver disease: liver enzymes 2.5 folds the upper normal limit Malignancy Pregnancy or lactation", "candidate_expression": "((Malignancy) AND (Serum creatinine > 3 mg/dl) AND (hypersensitivity) AND (liver disease Significant) AND (liver enzymes 2.5 folds the upper normal limit) AND (statin) AND (statins during the past month prior to study) AND ((Pregnancy) OR (lactation)))"}
{"candidate_id": "LLM07050", "doc_id": "NCT02542956_exc", "case_bucket": "other", "source_criterion": "A medical condition that could interfere with study participation Body weight less than 50 kg Participating in another study involving an investigational medication", "candidate_expression": "((Body weight less than 50 kg) AND (Participating in another study involving an investigational medication))"}
```
