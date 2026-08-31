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
{"candidate_id": "LLM01576", "doc_id": "NCT02509949_inc", "case_bucket": "other", "source_criterion": "age > 17 and < 60 years; American Society of Anesthesiology (ASA) I-III; admitted for living donor renal transplantation.", "candidate_expression": "((> 17 and < 60 years) AND (American Society of Anesthesiology (ASA)) AND (I-III) AND (admitted for) AND (age) AND (living donor renal transplantation))"}
{"candidate_id": "LLM01577", "doc_id": "NCT03297944_exc", "case_bucket": "or", "source_criterion": "using daily medication for chronic condition acute narrow angle glaucoma previous adverse experience with study drugs experiences motion sickness in response to driving simulator BMI > 30 women who are pregnant, lactating, or planning on becoming pregnant regular use of tobacco products current substance use disorder clinically significant ECG current ongoing psychiatric disorder", "candidate_expression": "((BMI > 30) AND (ECG clinically significant) AND (adverse experience previous) AND (chronic condition) AND (lactating) AND (medication daily) AND (motion sickness) AND (narrow angle glaucoma acute) AND (pregnant) AND (pregnant planning on becoming) AND (psychiatric disorder current ongoing) AND (study drugs) AND (substance use disorder current) AND (use of tobacco products regular) AND (women))"}
{"candidate_id": "LLM01578", "doc_id": "NCT02678728_exc", "case_bucket": "other", "source_criterion": "Unstable vital sign before surgery Severe pulmonary disease requiring consistent treatment Illiterate Pregnancy", "candidate_expression": "((Illiterate) AND (Pregnancy) AND (Severe) AND (Unstable) AND (before surgery) AND (consistent treatment) AND (pulmonary disease) AND (requiring) AND (surgery) AND (vital sign))"}
{"candidate_id": "LLM01579", "doc_id": "NCT02369211_inc", "case_bucket": "other", "source_criterion": "Patients undergoing robotic-assisted laparoscopic prostatectomy =18 years old males ASA class 1-4", "candidate_expression": "((ASA class 1-4) AND (males) AND (obotic-assisted laparoscopic prostatectomy) AND (years =18 years old))"}
{"candidate_id": "LLM01580", "doc_id": "NCT02543710_inc", "case_bucket": "or", "source_criterion": "All patients referred to a participating research centre with suspicion of or confirmed endometrial cancer. Patients with endometrial or epithelial ovarian cancer who following routine clinical guidelines are offered weekly taxane (paclitaxel) treatment. This will often be a third or fourth line treatment, i.e. patients with advanced disease. Technical possibility to obtain a new tissue biopsy to determine stathmin level in the tumour recurrence.", "candidate_expression": "((Technical possibility to obtain) AND (confirmed) AND (endometrial cancer) AND (endometrial ovarian cancer) AND (epithelial ovarian cancer) AND (paclitaxel) AND (participating research centre) AND (suspicion of) AND (taxane) AND (tissue biopsy) AND (treatment) AND (tumour recurrence) AND (weekly))"}
{"candidate_id": "LLM01581", "doc_id": "NCT02698969_exc", "case_bucket": "or", "source_criterion": "Clinical diagnosis of hepatic or renal disease Clinical diagnosis of chronic or acute alcoholism History of allergy or hypersensitivity to Sugammadex and/or atropine or Neostigmine Current medications with CNS effects History of neurologic disease Diaphragmatic palsy Pregnancy or nursing History of malignant arrhythmias", "candidate_expression": "((CNS effects) AND (Clinical diagnosis) AND (Diaphragmatic palsy) AND (History) AND (alcoholism) AND (malignant arrhythmias) AND (medications) AND (neurologic disease) AND ((Neostigmine) OR (Sugammadex) OR (atropine)) AND ((hepatic disease) OR (renal disease)) AND ((Pregnancy) OR (nursing)) AND ((acute) OR (chronic)) AND ((allergy) OR (hypersensitivity)))"}
{"candidate_id": "LLM01582", "doc_id": "NCT03376763_inc", "case_bucket": "or", "source_criterion": "Subjects must be capable of providing signed and dated written informed consent by date of Visit 0 (-2 week). Male and female aged =19 and < 65 years. Subjects diagnosed of schizophrenia as defined by Diagnostic and Statistical Manual of Mental Disorders, 4th edition text revision or 5th edition (DSM-<U+2163>-TR or 5) criteria, and a history of illness for at least for 3 years prior to screening. Subjects who take atypical antipsychotic drugs, and should be maintained on current antipsychotic drugs (including atypical antipsychotic drugs) and dose for at least 4 weeks prior to the screening. Subjects who need antipsychotic treatment (other than clozapine), and would be stable when switching to long-acting injectable aripiprazole in the investigator's judgement. Subjects must exhibit willingness, physiologic capability, and an educational level sufficient to comply with all protocol procedures.", "candidate_expression": "((=19 and < 65 years) AND (Diagnostic and Statistical Manual of Mental Disorders, 4th edition text revision or 5th edition (DSM-<U+2163>-TR or 5) criteria) AND (Male) AND (Subjects must be capable of providing signed and dated written informed consent by date of Visit 0 (-2 week).) AND (Subjects must exhibit willingness, physiologic capability, and an educational level sufficient to comply with all protocol procedures.) AND (aged) AND (atypical antipsychotic drugs) AND (female) AND (for at least for 3 years) AND (history of illness) AND (prior to screening) AND (schizophrenia))"}
{"candidate_id": "LLM01583", "doc_id": "NCT02590822_inc", "case_bucket": "or", "source_criterion": "Capacity to provide informed consent before any trial-related activities Established T2DM (=3months) HbA1c = 9% if on triple therapy or = 10% on diet & exercise or monotherapy or dual therapy Current glucose lowering therapy either mono, dual or triple of any combination of metformin, sulphonylurea, DPP-IV inhibitor, GLP-1 therapy or an SGLT2 +/- diet and exercise Poorly managed diet controlled diabetes (with HbA1c > 6.5% , not currently taking any glucose lowering therapy, meeting BMI inclusion range) Body mass index > 30Kg/m2 or > 27.5 Kg/m2 (South Asian), Diagnosis of T2DM before the age of 60 years of age Age =18 and = 65 years", "candidate_expression": "((Age =18 and = 65 years) AND (Body mass index) AND (Capacity to provide informed consent before any trial-related activities) AND (HbA1c) AND (HbA1c > 6.5%) AND (T2DM) AND (T2DM =3months) AND (age before 60 years of age) AND (diabetes) AND (glucose lowering therapy) AND NOT (glucose lowering therapy) AND ((DPP-IV inhibitor,) OR (GLP-1 therapy) OR (SGLT2) OR (diet) OR (exercise) OR (metformin) OR (sulphonylurea)) AND ((> 27.5 Kg/m2) OR (> 30Kg/m2)) AND ((= 10%) OR (= 9%)))"}
{"candidate_id": "LLM01584", "doc_id": "NCT03236246_inc", "case_bucket": "or", "source_criterion": "Estimated glomerular filtration rate =20 mL/min and <60 mL/min Hgb =8.5 g/dL and =11.5 g/dL Serum ferritin =500 ng/mL and transferrin saturation (TSAT) =25% Serum intact parathyroid hormone =600 pg/mL", "candidate_expression": "((=20 mL/min and <60 mL/min) AND (=25%) AND (=500 ng/mL) AND (=600 pg/mL) AND (=8.5 g/dL and =11.5 g/dL) AND (Estimated glomerular filtration rate) AND (Hgb) AND (Serum intact parathyroid hormone) AND (TSAT) AND ((Serum ferritin) OR (transferrin saturation)))"}
{"candidate_id": "LLM01585", "doc_id": "NCT02550769_inc", "case_bucket": "or", "source_criterion": "Age over 18 years Patients with rectal cancer stage: cT1-2-3, cN0-1, cM0. Tumor equal or below 10 cm from the anal verge, candidates to (ETM) low anterior resection and anastomosis, with or without preoperative chemo-radiotherapy. Adenocarcinoma of low or moderate differentiation ASA I, II, III.", "candidate_expression": "((ASA I, II, III) AND (Adenocarcinoma low or moderate differentiation) AND (Age over 18 years) AND (Tumor equal or below 10 cm from the anal verge) AND (chemo-radiotherapy preoperative) AND (rectal cancer stage) AND ((low anterior anastomosis) OR (low anterior resection)) AND ((cM 0) OR (cN 0-1) OR (cT 1-2-3)))"}
{"candidate_id": "LLM01586", "doc_id": "NCT01491295_exc", "case_bucket": "or", "source_criterion": "HCV, HIV, HDV coinfection. Uncontrolled HCC, malignancy or decompensated liver cirrhosis (CTP score = 7). Uremia patients or Creatinine = 2 mg/dl.", "candidate_expression": "((= 2 mg/dl) AND (= 7) AND (CTP score) AND (Creatinine) AND (HCC) AND (HCV coinfection) AND (HDV coinfection) AND (Uncontrolled) AND (Uremia) AND (coinfection HIV) AND (decompensated) AND (liver cirrhosis) AND (malignancy))"}
{"candidate_id": "LLM01587", "doc_id": "NCT03044093_exc", "case_bucket": "other", "source_criterion": "hematology diseases clotting factor deficiency", "candidate_expression": "((clotting factor deficiency) AND (hematology diseases))"}
{"candidate_id": "LLM01588", "doc_id": "NCT02254668_exc", "case_bucket": "or", "source_criterion": "Renal insufficiency (> 265 µmol/l) Incapability to give informed consent Cardiogenic shock of patient with KILLIP III or IV pregnant or breast feeding females insufficient contraception (only for substudy 3)", "candidate_expression": "((Cardiogenic shock) AND (Incapability to give informed consent) AND (KILLIP III or IV) AND (Renal insufficiency) AND (breast feeding) AND (contraception insufficient) AND (females) AND (pregnant))"}
{"candidate_id": "LLM01589", "doc_id": "NCT02789111_inc", "case_bucket": "other", "source_criterion": "Major spine surgery scheduled as part of clinical care 18-80 years", "candidate_expression": "((18-80) AND (Major spine surgery) AND (years))"}
{"candidate_id": "LLM01590", "doc_id": "NCT00650312_inc", "case_bucket": "or", "source_criterion": "1. Age: 18 years and older. 2. Sex: Male and non-pregnant, non-lactating female 1. Women of childbearing potential must have negative serum (Beta HCG) pregnancy tests performed within 14 days prior to the start of the study and on the evening prior to each dose administration. If dosing is scheduled on Sunday or Monday, the HCG pregnancy test should be given within 48 hours prior to dosing of each study period. An additional serum (Beta HCG) pregnancy test will be performed upon completion of the study. 2. Women of childbearing potential must practice abstinence or be using an acceptable form of contraception throughout the duration of the study. Acceptable forms of contraception include the following: (1) intrauterine device in place for at least 3 months prior to the start of the study and remaining in place during the study period, or (2) barrier methods containing or used in conjunction with a spermicidal agent, or (3) postmenopausal accompanied with a documented postmenopausal course of at least one year or surgical sterility (tubal ligation, oophorectomy or hysterectomy). 3. During the course of the study, from study screen until study exit - including the washout period, women of childbearing potential must use a spermicide containing barrier method of contraception in addition to their current contraceptive device. This advice should be documented in the informed consent form. 3. Weight: At least 60 kg (132 lbs) for man and 48 kg (106 lbs) for women and within 15% of Ideal Body Weight (IBW), as referenced by the Table of \"\"Desirable Weights of Adults\"\" Metropolitan Life Insurance Company, 1999 (See Part II ADMINISTRATIVE ASPECTS OF BIOEQUIVALENCE PROTOCOLS). 4. All subjects should be judged normal and healthy during a pre-study medical evaluation (physical examination, laboratory evaluation, 12-lead ECG, hepatitis B and hepatitis C tests, HIV test, and urine drug screen including amphetamine, barbiturates, benzodiazepine, cannabinoid, cocaine, opiates, phencyclidine, and methadone) performed within 14 days of the initial dose of study medication.", "candidate_expression": "((12-lead ECG) AND (18 years and older) AND (Age) AND (At least 106 lbs) AND (At least 132 lbs) AND (At least 48 kg) AND (At least 60 kg) AND (Beta HCG) AND (During the course of the study) AND (HIV test) AND (Male) AND (Weight) AND (Women) AND (abstinence) AND (acceptable form) AND (amphetamine) AND (at least one year) AND (barbiturates) AND (barrier methods) AND (benzodiazepine) AND (cannabinoid) AND (childbearing potential) AND (cocaine) AND (contraception) AND (contraceptive device) AND (current) AND (each dose administration) AND (female) AND (for at least 3 months prior to the start of the study) AND (healthy) AND (hepatitis B tests) AND (hepatitis C tests) AND (hysterectomy) AND (in addition to) AND (in place during the study period) AND (intrauterine device) AND (laboratory evaluation) AND (lactating) AND (man) AND (methadone) AND (negative) AND (non) AND (normal) AND (on the evening prior to each dose administration) AND (oophorectomy) AND (opiates) AND (phencyclidine) AND (physical examination) AND (postmenopausal) AND (pre-study medical evaluation) AND (pregnant) AND (serum pregnancy tests) AND (spermicidal agent) AND (spermicide containing barrier method of contraception) AND (surgical sterility) AND (the initial dose of study medication) AND (the start of the study) AND (the study period) AND (throughout the duration of the study) AND (tubal ligation) AND (urine drug screen) AND (within 14 days of the initial dose of study medication) AND (within 14 days prior to the start of the study) AND (within 15% of Ideal Body Weight (IBW)) AND (women))"}
{"candidate_id": "LLM01591", "doc_id": "NCT03495557_exc", "case_bucket": "other", "source_criterion": "Conversion to laparotomy Emergent re intervention Immunosuppression Umbilical hernia", "candidate_expression": "((Conversion to) AND (Emergent) AND (Immunosuppression) AND (Umbilical hernia) AND (laparotomy) AND (re intervention))"}
{"candidate_id": "LLM01592", "doc_id": "NCT02227992_exc", "case_bucket": "or", "source_criterion": "Subjects with known intolerance to blood products or to one of the components of the study product or is unwilling to receive blood products; Female subjects, who are of childbearing age (i.e. adolescent), who are pregnant or nursing; Subject is currently participating or plans to participate in any other investigational device or drug without prior approval from the Sponsor; Subjects who are known, current alcohol and/or drug abusers Subjects admitted for trauma surgery Subjects with any pre or intra-operative findings identified by the surgeon that may preclude conduct of the study procedure. Subject with TBS in an actively infected field (Class III Contaminated or Class IV Dirty or Infected) TBS is from large defects in arteries or veins where the injured vascular wall requires repair with maintenance of vessel patency and which would result in persistent exposure of the EVARREST™ or SURGICEL® to blood flow and pressure during healing and absorption of the product; TBS with major arterial bleeding requiring suture or mechanical ligation; Bleeding site is in, around, or in proximity to foramina in bone, or areas of bony confine.", "candidate_expression": "((Female subjects, who are of childbearing age (i.e. adolescent), who are pregnant or nursing) AND (Subject is currently participating or plans to participate in any other investigational device or drug without prior approval from the Sponsor) AND (TBS) AND (blood products) AND (intolerance) AND (major arterial bleeding) AND (trauma surgery) AND ((Class III Contaminated) OR (Class IV Dirty or Infected)) AND ((mechanical ligation) OR (suture)) AND ((alcohol abusers) OR (drug abusers)))"}
{"candidate_id": "LLM01593", "doc_id": "NCT03067740_inc", "case_bucket": "other", "source_criterion": "Patients are of American Society of Anesthesiologists (ASA) physical status I and II, aged 8-14 years old, of both gender, with suspected acute appendicitis scheduled for laparoscopic appendicectomy.", "candidate_expression": "((ASA) AND (American Society of Anesthesiologists physical status I and II) AND (acute appendicitis suspected) AND (aged 8-14 years old) AND (both gender) AND (laparoscopic appendicectomy scheduled for))"}
{"candidate_id": "LLM01594", "doc_id": "NCT02224040_inc", "case_bucket": "or", "source_criterion": "Blood culture-proven typhoid fever (S. typhi or S. paratyphi) Signed informed consent to participate in the study.", "candidate_expression": "((Blood culture proven) AND (Signed informed consent to participate in the study.) AND (typhoid fever) AND ((S. paratyphi) OR (S. typhi)))"}
{"candidate_id": "LLM01595", "doc_id": "NCT03115320_inc", "case_bucket": "other", "source_criterion": "- Patient with IVF cycle and therefore having frozen-thawed embryos Regular menstruation cycle Patient's willingness to participate in the study", "candidate_expression": "((IVF cycle) AND (Patient's willingness to participate in the study) AND (Regular menstruation cycle) AND (frozen-thawed embryos))"}
{"candidate_id": "LLM01596", "doc_id": "NCT02370069_exc", "case_bucket": "or", "source_criterion": "immunization with PPV23 within the last year any confirmed or suspected immunodeficiency condition, including human immunodeficiency virus (HIV) infection, haematological malignancy, or a congenital immunodeficiency history of allergic disease or reactions likely to be exacerbated by any component of the vaccine history of allergic disease likely to be stimulated by the vaccination history or records of immunosuppressive therapy (with the exception of topical corticosteroids) for more than 14 days and within 6 months of vaccination history or evidence of administration of immunoglobulins and/or any blood products during the study period or within the three months preceding the study vaccine use of any other investigational or non-registered drug or vaccine during the study period or within 30 days preceding the study vaccine administration of a vaccine during the period starting one month before the dose of vaccine and ending one month after pregnancy", "candidate_expression": "((HIV) AND (PPV23 within the last year confirmed) AND (allergic disease) AND (allergic disease stimulated by the vaccination) AND (allergic reactions) AND (blood products during the study period within the three months preceding the study vaccine) AND (congenital immunodeficiency) AND (drug investigational non-registered) AND (haematological malignancy) AND (human immunodeficiency virus infection) AND (immunization) AND (immunodeficiency condition suspected) AND (immunoglobulins) AND (immunosuppressive therapy) AND (pregnancy) AND (vaccination) AND (vaccine) AND (vaccine during the period starting one month before the dose of vaccine and ending one month after) AND (vaccine during the study period within 30 days preceding the study vaccine) AND NOT (topical corticosteroids for more than 14 days of vaccination within 6 months of vaccination))"}
{"candidate_id": "LLM01597", "doc_id": "NCT02822001_inc", "case_bucket": "other", "source_criterion": "Patients undergoing surgery with general anesthesia, Patients weighing = 80 pounds who are not -intubated prior to surgery, Patients who are able to give informed consent.", "candidate_expression": "((= 80 pounds) AND (Patients who are able to give informed consent) AND (general anesthesia) AND (intubated) AND (not) AND (prior to surgery) AND (surgery) AND (undergoing) AND (weighing))"}
{"candidate_id": "LLM01598", "doc_id": "NCT03479502_exc", "case_bucket": "or", "source_criterion": "allergy to Doxycycline or Methylprednisolone, pregnancy, diagnosis, Inflammatory arthritis or diabetes, secondary adhesive capsulitis (history of significant trauma, rotator cuff tear injury, stroke) evidence of arthritis on x-ray, current infectious disease, and any previous treatment for the for adhesive capsulitis of the affected shoulder.", "candidate_expression": "((Doxycycline) AND (Inflammatory arthritis) AND (Methylprednisolone) AND (adhesive capsulitis affected shoulder) AND (adhesive capsulitis secondary) AND (allergy) AND (arthritis evidence of) AND (diabetes) AND (diagnosis) AND (infectious disease current) AND (pregnancy) AND (rotator cuff tear injury) AND (stroke) AND (trauma significant) AND (treatment any previous) AND (x-ray))"}
{"candidate_id": "LLM01599", "doc_id": "NCT03047538_inc", "case_bucket": "or", "source_criterion": "a very high cardiovascular risk and LDL-cholesterol> 1.8 mmol / l a high cardiovascular risk and LDL-cholesterol> 2.5 mmol / l Patient with a high or very high cardiovascular risk treated by lipidlowering therapy with statin", "candidate_expression": "((LDL-cholesterol > 1.8 mmol / l) AND (LDL-cholesterol > 2.5 mmol / l) AND (cardiovascular risk) AND (cardiovascular risk high) AND (cardiovascular risk very high) AND (lipidlowering therapy) AND (stati) AND ((high) OR (very high)))"}
{"candidate_id": "LLM01600", "doc_id": "NCT01807897_exc", "case_bucket": "or", "source_criterion": "Hospitalization for acute decompensated HF within previous 30 days Hospitalization for myocardial infarction or cardiac surgery within previous 90 days Presence of a left ventricular assist device History of heart transplantation Poorly controlled hypertension (>170/>110) Poorly controlled diabetes (HbA1c > 9.0) Severe renal failure with estimated glomerular filtration rate <30 ml/min Prior stroke with functional impairment or other severe, uncontrolled medical problems that may impair ability to participate in the study exams, based on medical history and review of medical records Severe chronic insomnia, with reported usual sleep duration <4 hours Severe daytime sleepiness, defined as Epworth Sleepiness Scale score 18 or higher or a report of falling asleep driving during the previous year, and deemed a safety risk by study physician Awake resting oxyhemoglobin saturation <89% Pregnancy Smoking by subject or other person in the subject's bedroom, or other open flame in bedroom Current use of a positive airway pressure device (including continuous or bi-level positive airway pressure or adaptive servo-ventilation) or supplemental oxygen therapy", "candidate_expression": "((<30 ml/min) AND (<4 hours) AND (<89%) AND (> 9.0) AND (Awake) AND (Epworth Sleepiness Scale) AND (HbA1c) AND (Hospitalization) AND (Poorly controlled) AND (Pregnancy) AND (Severe) AND (acute decompensated HF) AND (adaptive servo-ventilation) AND (bi-level positive airway pressure) AND (cardiac surgery) AND (chronic insomnia) AND (continuous airway pressure) AND (daytime sleepiness) AND (diabetes) AND (estimated glomerular filtration rate) AND (functional impairment) AND (heart transplantation) AND (hypertension) AND (left ventricular assist device) AND (myocardial infarction) AND (oxyhemoglobin saturation) AND (positive airway pressure device) AND (renal failure) AND (resting) AND (score 18 or higher) AND (sleep duration) AND (stroke) AND (supplemental oxygen therapy) AND (within previous 30 days) AND (within previous 90 days))"}
```
