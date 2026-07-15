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
{"candidate_id": "LLM05326", "doc_id": "NCT02298504_inc", "case_bucket": "other", "source_criterion": "Pediatric patients with deep dental decay in primary molars Teeth with signs and symptoms of reversible pulpitis", "candidate_expression": "((Pediatric) AND (deep dental decay primary molars) AND (reversible pulpitis Teeth))"}
{"candidate_id": "LLM05327", "doc_id": "NCT03147599_exc", "case_bucket": "or", "source_criterion": "Upper urinary tract deterioration Uncontrolled diabetes mellitus Evident local or pelvic recurrence Adjuvant chemotherapy Chronic retention Pouch stones Urethral stricture or urethro-ileal maldirection Sensitivity to Mebeverine Untreated chronic constipation Active symptomatic urinary infection", "candidate_expression": "((Active) AND (Adjuvant chemotherapy) AND (Chronic retention) AND (Mebeverine) AND (Pouch stones) AND (Sensitivity) AND (Uncontrolled) AND (Untreated) AND (Upper urinary tract deterioration) AND (Urethral stricture) AND (chronic constipation) AND (diabetes mellitus) AND (local recurrence) AND (pelvic recurrence) AND (symptomatic) AND (urethro-ileal maldirection) AND (urinary infection))"}
{"candidate_id": "LLM05328", "doc_id": "NCT03044093_exc", "case_bucket": "other", "source_criterion": "hematology diseases clotting factor deficiency", "candidate_expression": "((clotting factor deficiency) AND (hematology diseases))"}
{"candidate_id": "LLM05329", "doc_id": "NCT02019628_exc", "case_bucket": "or", "source_criterion": "1. Currently enrolled in another research trial for investigative nutritional or other therapies thought to have an impact on immune system functioning. 2. Unable to consent to the study. 3. Women who are pregnant or are attempting conception, especially in the presence of a history of recurrent spontaneous abortion. 4. Other medical complications that might preclude one from participating in the study, i.e., recent heart attack or stroke or chronic kidney disease. 5. Currently taking immunomodulatory medication, i.e. interferon. 6. Currently taking other medications thought to have an impact on immune system functioning, i.e., chemotherapeutic agents. 7. Known allergy to rice, rice bran, or related food products. 8. Known allergy to mushrooms or related food products. 9. History of malignancies related to the NK cell line, including: NK cell leukemias and T-cell large granular lymphocyte leukemias, NK-cell lymphoproliferative disease of granular lymphocytes, and NK cell lymphomas, e.g., nasal and nasal-like NK/T-cell lymphomas. 10. Current smoker.", "candidate_expression": "((Currently enrolled in another research trial for investigative nutritional or other therapies thought to have an impact on immune system functioning.) AND (Unable to consent to the study.) AND (Women) AND (allergy to rice) AND (allergy to rice bran) AND (chemotherapeutic agents) AND (immunomodulatory medication) AND (interferon) AND (medical complications Other) AND (medications other impact on immune system functioning) AND (pregnant) AND (rice) AND (rice bran) AND (smoker Current) AND (spontaneous abortion recurrent) AND NOT (participating in the study) AND ((chronic kidney disease) OR (heart attack recent) OR (stroke)) AND ((malignancies) OR (related to the NK cell line)) AND ((NK cell leukemias) OR (NK cell lymphomas) OR (NK-cell lymphoproliferative disease of granular lymphocytes) OR (T-cell large granular lymphocyte leukemias) OR (nasal NK/T-cell lymphomas) OR (nasal-like NK/T-cell lymphomas)) AND ((allergy to food products) OR (allergy to mushrooms)))"}
{"candidate_id": "LLM05330", "doc_id": "NCT02571881_inc", "case_bucket": "other", "source_criterion": "normal full term single pregnancy age 18 years or more BMI 20 - 35 kg/m2 written informed consent obtained", "candidate_expression": "((18 years or more) AND (20 - 35 kg/m2) AND (BMI) AND (age) AND (full term) AND (normal) AND (pregnancy) AND (single) AND (written informed consent obtained))"}
{"candidate_id": "LLM05331", "doc_id": "NCT03063866_inc", "case_bucket": "or", "source_criterion": "Patients aged between 40 and 60 years old. With Child score B or C Presented for elective gastrointestinal endoscopy", "candidate_expression": "((Child score B C) AND (aged between 40 and 60 years old) AND (gastrointestinal endoscopy elective))"}
{"candidate_id": "LLM05332", "doc_id": "NCT00198913_inc", "case_bucket": "other", "source_criterion": "type 2 diabetic, age 18 and over, informed consent,", "candidate_expression": "((age 18 and over) AND (informed consent) AND (type 2 diabetic))"}
{"candidate_id": "LLM05333", "doc_id": "NCT02785549_inc", "case_bucket": "or", "source_criterion": "Patient's written informed consent. Adequate cognitive capacity. Adequate family support No acute diverticulitis episode in the last 3 months mNeff 0 acute diverticulitis (abdominal computed tomography scan) No antibiotic treatment in the last 2 weeks Immunocompetence* No significant comorbidities** Good oral tolerance Good symptom control Maximum one of the following SIRS criteria (* T>38 ºC or <36ºC, L>12,000 or <4000/uL, HR>90 bpm, RR<20 rpm) or CRP>15 mg/dL", "candidate_expression": "((Adequate family support) AND (Immunocompetence) AND (Patient's written informed consent. Adequate cognitive capacity) AND (abdominal computed tomography scan) AND (diverticulitis acute) AND (diverticulitis acute in the last 3 months) AND (mNeff 0) AND (oral tolerance Good) AND (symptom control Good >38 ºC <36ºC >12,000 /uL <4000/uL) AND NOT (antibiotic treatment in the last 2 weeks) AND NOT (comorbidities significant) AND ((HR >90 bpm) OR (L) OR (RR <20 rpm) OR (T)) AND ((CRP >15 mg/dL) OR (SIRS criteria)))"}
{"candidate_id": "LLM05334", "doc_id": "NCT03176316_exc", "case_bucket": "or", "source_criterion": "Pregnancy, age < 18, nursing, or documented allergy to naloxone", "candidate_expression": "((< 18) AND (Pregnancy) AND (age) AND (allergy) AND (naloxone) AND (nursing))"}
{"candidate_id": "LLM05335", "doc_id": "NCT03066440_inc", "case_bucket": "or", "source_criterion": "Age between 0 and 18 years Venous pH less than 7.25 Ketonuria as confirmed on urine point-of-care testing or urinalysis Hyperglycemia (Serum glucose > 200 mg/dl) Serum bicarbonate <15 mmol/L PICU admission", "candidate_expression": "((<15 mmol/L) AND (> 200 mg/dl) AND (Age) AND (Hyperglycemia) AND (Ketonuria) AND (PICU) AND (Serum bicarbonate) AND (Serum glucose) AND (Venous pH) AND (admission) AND (between 0 and 18 years) AND (less than 7.25) AND (urinalysis) AND (urine point-of-care testing))"}
{"candidate_id": "LLM05336", "doc_id": "NCT03344042_inc", "case_bucket": "or", "source_criterion": "parturient in labour without cervical dilation and regular uterine contractions", "candidate_expression": "((cervical dilation) AND (labour) AND (parturient) AND (regular uterine contractions))"}
{"candidate_id": "LLM05337", "doc_id": "NCT01491295_inc", "case_bucket": "or", "source_criterion": "HBsAg-positive for more than 6 months (HBeAg-positive or HBeAg-negative). Age > 20 y/o. Under lamivudine/adefovir treatment for more than 1 year due to previous lamivudine resistance (LAM-R), current HBV DNA is undetectable (< 20 IU/ml) during enrollment.", "candidate_expression": "((Age > 20 y/o) AND (HBV DNA undetectable < 20 IU/ml during enrollment) AND (HBsAg positive more than 6 months) AND (LAM-R) AND (adefovir) AND (lamivudine) AND ((HBeAg negative) OR (HBeAg positive)))"}
{"candidate_id": "LLM05338", "doc_id": "NCT02837783_inc", "case_bucket": "other", "source_criterion": "Patient meets protocol criteria for diagnosis of IBS-C, abdominal pain, abdominal bloating and abdominal girth", "candidate_expression": "((IBS-C) AND (abdominal bloating) AND (abdominal girth) AND (abdominal pain) AND (protocol criteria))"}
{"candidate_id": "LLM05339", "doc_id": "NCT02631512_exc", "case_bucket": "or", "source_criterion": "Ulcers due to non-diabetic etiology. Uncontrolled diabetes defined as HbA1c above 70 mmol/mol and insufficient nutritional status. Ulcers older than 1 year. Any of gangrene, osteomyelitis, cellulitis, or Charcot osteoarthropathy.", "candidate_expression": "((Charcot osteoarthropathy) AND (HbA1c above 70 mmol/mol) AND (Ulcers non-diabetic) AND (Ulcers older than 1 year) AND (Uncontrolled diabetes) AND (cellulitis) AND (gangrene) AND (insufficient nutritional status) AND (osteomyelitis))"}
{"candidate_id": "LLM05340", "doc_id": "NCT02467686_inc", "case_bucket": "or", "source_criterion": "Menopausal women with breast cancer treated and using tamoxifen or aromatase inhibitor. With hot flashes and with or without active sexual life.", "candidate_expression": "((Menopausal) AND (breast cancer) AND (hot flashes) AND (treated) AND (women) AND ((with active sexual life) OR (without active sexual life)) AND ((aromatase inhibitor) OR (tamoxifen)))"}
{"candidate_id": "LLM05341", "doc_id": "NCT02420015_exc", "case_bucket": "other", "source_criterion": "Have a history of myocardial infarction in the past 6 months Have a contraindication to NRT with no medical clearance from the primary care provider or study physician Use and unwillingness to stop use of other forms of nicotine such as cigars, pipes, or chewing tobacco Are pregnant Meet criteria for a current manic episode based on structured clinical interview Are currently enrolled in another smoking cessation trial Are currently imprisoned or in psychiatric hospitalization", "candidate_expression": "((Are currently enrolled in another smoking cessation trial) AND (NRT) AND (Use and unwillingness to stop use of other forms of nicotine such as cigars, pipes, or chewing tobacco) AND (contraindication) AND (imprisoned) AND (manic episode) AND (myocardial infarction i past 6 months) AND (pregnant) AND (psychiatric hospitalization))"}
{"candidate_id": "LLM05342", "doc_id": "NCT03073603_inc", "case_bucket": "or", "source_criterion": "Patients with either Relapsing-remitting MS (RRMS), Secondary progressive MS (SPMS), or Primary progressive MS (PPMS) by McDonald 2010 criteria. Patients defined by subtype based on 2013 updated phenotypic criteria. prospectively with an EDSS change of at least 1.0 points over the last two years, or retrospectively, with any significant change in motor function over at least one year, unrelated to relapse. 55 years of age or older at time of randomization; No evidence of recent new inflammatory disease activity (inactive by the Lublin criteria16) with no new relapse for at least five years and no new MRI lesion for at least three years interferon ß-1a, interferon ß-1b, glatiramer acetate, natalizumab, fingolimod, dimethyl fumarate, or teriflunomide; continuously for no less than 5 years. Taking most recent DMT continuously* for no less than two years. Willing to be randomized per this protocol; each patient will be questioned as to their willingness to stay in the trial regardless of the group to which group they are randomized. Willing to follow the protocol Continuously will be defined as no less than 75% of all prescribed doses, with no time of greater than four weeks from last intended dose to have missed a dose (8 weeks for natalizumab, i.e. one missed dose).", "candidate_expression": "((55 years or older) AND (DMT) AND (EDSS change) AND (Lublin criteria) AND (MRI) AND (No) AND (Primary progressive MS (PPMS)) AND (Relapsing-remitting MS (RRMS)) AND (Secondary progressive MS (SPMS)) AND (Willing to be randomized per this protocol; each patient will be questioned as to their willingness to stay in the trial regardless of the group to which group they are randomized.) AND (Willing to follow the protocol) AND (age) AND (at least 1.0 points) AND (at time of randomization) AND (change in motor function) AND (continuously) AND (dimethyl fumarate) AND (fingolimod) AND (for at least five years) AND (for at least three years) AND (for no less than 5 years) AND (for no less than two years) AND (glatiramer acetate) AND (inactive) AND (inflammatory disease) AND (interferon ß-1a) AND (interferon ß-1b) AND (lesion) AND (natalizumab) AND (new) AND (no) AND (over at least one year) AND (over the last two years) AND (relapse) AND (significant) AND (teriflunomide) AND (unrelated to relapse))"}
{"candidate_id": "LLM05343", "doc_id": "NCT02443844_inc", "case_bucket": "other", "source_criterion": "Patients who have non muscle invasive bladder cancer male patients patients between 40-80 years old", "candidate_expression": "((between 40-80 years) AND (male) AND (non muscle invasive bladder cancer) AND (old))"}
{"candidate_id": "LLM05344", "doc_id": "NCT02571881_inc", "case_bucket": "other", "source_criterion": "normal full term single pregnancy age 18 years or more BMI 20 - 35 kg/m2 written informed consent obtained", "candidate_expression": "((BMI 20 - 35 kg/m2) AND (age 18 years or more) AND (pregnancy normal full term single) AND (written informed consent obtained))"}
{"candidate_id": "LLM05345", "doc_id": "NCT01098383_exc", "case_bucket": "or", "source_criterion": "an underlying infectious disease chromosomal abnormality metabolic disorder specific brain related disorder (such as tuberous sclerosis) history of fetal cytomegalovirus infection birth asphyxia a history of major head injury a chronic use of non-steroidal anti-inflammatory drugs, (NSAID) known brain damage Epilepsy Abnormal Electro-cardiogram (ECG) Epileptiform EEG Use of psychostimulants, anti-depressants, neuroleptics or anti-convulsive agents within the past month. Lack of cooperation in the screening phase", "candidate_expression": "((ECG) AND (EEG Epileptiform) AND (Electro-cardiogram Abnormal) AND (Epilepsy) AND (Lack of cooperation in the screening phase) AND (NSAID) AND (anti-convulsive agents) AND (anti-depressants) AND (birth asphyxia) AND (brain damage) AND (chromosomal abnormality) AND (chronic use) AND (cytomegalovirus infection fetal) AND (disorder brain) AND (infectious disease underlying) AND (major head injury) AND (metabolic disorder) AND (neuroleptics) AND (non-steroidal anti-inflammatory drugs) AND (psychostimulants) AND (tuberous sclerosis))"}
{"candidate_id": "LLM05346", "doc_id": "NCT03297021_inc", "case_bucket": "or", "source_criterion": "ASA I, II, III presenting for ambulatory surgery to be performed under general anesthesia", "candidate_expression": "((ASA) AND (I) AND (II) AND (III) AND (ambulatory surgery) AND (general anesthesia) AND (under general anesthesia))"}
{"candidate_id": "LLM05347", "doc_id": "NCT02607319_inc", "case_bucket": "or", "source_criterion": "History of three or more consecutively failed In Vitro Fertilization (IVF) cycles after embryo transfer. Normal uterine cavity (as assessed by hysteroscopy or HSG). Normal hormonal investigation: TSH, PRL, FBS. Normal acquired/inherited thrombophilia profile: LAC, ACA IgG/IgM, Prot S, Antithrombin III, beta-2 glycoprotein, Factors V, II, MTHFR. Normal semen analysis and mild/moderate male factor (Total motile sperm count > 5 million/ml and/or normal WHO morphology >20%. Patient provides written informed consent.", "candidate_expression": "((ACA IgG) AND (ACA IgM) AND (Antithrombin III) AND (FBS) AND (Factors II) AND (Factors V) AND (HSG) AND (IVF) AND (In Vitro Fertilization three or more consecutively failed after embryo transfer) AND (LAC) AND (MTHFR) AND (PRL) AND (Patient provides written informed consent) AND (Prot S) AND (TSH) AND (Total motile sperm count > 5 million/ml) AND (beta-2 glycoprotein) AND (hormonal investigation: Normal) AND (hysteroscopy) AND (male factor) AND (normal WHO morphology >20%) AND (semen analysis mild moderate) AND (thrombophilia profile Normal))"}
{"candidate_id": "LLM05348", "doc_id": "NCT03589105_exc", "case_bucket": "or", "source_criterion": "Diagnosis of primary progressive MS Inability to complete an MRI (contraindications for MRI include but are not restricted to weight =140 kg, pacemaker, cochlear implants, presence of foreign substances in the eye, intracranial vascular clips, surgery within 6 weeks of entry into the study, coronary stent implanted within 8 weeks prior to the time of the intended MRI, etc…) Gadolinium intolerance History of ischemic cerebrovascular disorders (e.g., stroke, transient ischemic attack) or ischemia of the spinal cord History or known presence of central nervous system (CNS) or spinal cord tumor (e.g., meningioma, glioma) History or known presence of potential metabolic causes of myelopathy (e.g., untreated vitamin B12 deficiency) History or known presence of infectious causes of myelopathy (e.g., syphilis, Lyme disease, human T-lymphotropic virus 1 (HTLV-1), herpes zoster myelopathy) History of genetically inherited progressive CNS degenerative disorder (e.g., hereditary paraparesis; MELAS [mitochondrial myopathy, encephalopathy, lactic acidosis, stroke] syndrome) Neuromyelitis optica History or known presence of systemic autoimmune disorders potentially causing progressive neurologic disease (e.g., lupus, anti-phospholipid antibody syndrome, Sjogren's syndrome, Behçet's disease, sarcoidosis) History of severe, clinically significant brain or spinal cord trauma (e.g., cerebral contusion, spinal cord compression) Vulnerable patients (Patient referred to in Articles L. 1121-5 to L. 1121-8 and L. 1122-1-2 of the French Public Health Code)", "candidate_expression": "((=140 kg) AND (Articles L. 1121-5 to L. 1121-8 and L. 1122-1-2 of the French Public Health Code) AND (Behçet's disease) AND (Gadolinium) AND (History) AND (Inability to complete) AND (Lyme disease) AND (MELAS syndrome) AND (MRI) AND (Neuromyelitis optica) AND (Sjogren's syndrome) AND (Vulnerable patients) AND (anti-phospholipid antibody syndrome) AND (brain trauma) AND (central nervous system (CNS) tumor) AND (cerebral contusion) AND (clinically significant) AND (cochlear implants) AND (contraindications) AND (coronary stent) AND (encephalopathy) AND (entry into the study) AND (foreign substances in the eye) AND (genetically inherited) AND (glioma) AND (hereditary paraparesis) AND (herpes zoster myelopathy) AND (human T-lymphotropic virus 1 (HTLV-1)) AND (implanted) AND (infectious causes) AND (intended) AND (intolerance) AND (intracranial vascular clips) AND (ischemia of the spinal cord) AND (ischemic cerebrovascular disorders) AND (lactic acidosis) AND (lupus) AND (meningioma) AND (metabolic causes) AND (mitochondrial myopathy) AND (myelopathy) AND (pacemaker) AND (potentially causing) AND (primary) AND (progressive CNS degenerative disorder) AND (progressive MS) AND (progressive neurologic disease) AND (sarcoidosis) AND (severe) AND (spinal cord compression) AND (spinal cord trauma) AND (spinal cord tumor) AND (stroke) AND (surgery) AND (syphilis) AND (systemic autoimmune disorders) AND (the time of the intended MRI) AND (transient ischemic attack) AND (untreated) AND (vitamin B12 deficiency) AND (weight) AND (within 6 weeks of entry into the study) AND (within 8 weeks prior to the time of the intended MRI))"}
{"candidate_id": "LLM05349", "doc_id": "NCT02961764_inc", "case_bucket": "other", "source_criterion": "Presents to the Emergency Department (ED) and meets the clinical definition for Acute Bacterial Skin and Skin Structure Infections (ABSSSI) Known or suspected gram-positive infection.", "candidate_expression": "((ABSSSI) AND (Acute Bacterial Skin and Skin Structure Infections) AND (Emergency Department (ED)) AND (gram-positive) AND (infection))"}
{"candidate_id": "LLM05350", "doc_id": "NCT00461136_exc", "case_bucket": "or", "source_criterion": "Severe Hypertension Grade 3 WHO classification (Mean Sitting Diastolic Blood Pressure (MSDBP) 110 mmHg and/or Mean Sitting Systolic Blood Pressure MSSBP 180 mmHg) Acetylsalicyclic acid (ASA) treatment >1g/day or regular use of Non steroidal anti-inflammatory drug (NSAIDs) Kidney disease not caused by diabetes or hypertension Serum potassium < 3.5 or > 5.1 mEq/L GFR < 40 ml/min/1.73m2 as measured by the MDRD formula Serum albumin < 2.0mg/dL History of hypertensive encephalopathy or cerebrovascular accident at any time prior to Visit1. Current diagnosis of heart failure (New York Heart Association (NYHA) Class II-IV) History of myocardial infarction, unstable angina pectoris, coronary bypass surgery, or any percutaneous coronary intervention (PCI) during the 6 months prior to Visit 1 Second or third degree heart block without a pacemaker Concurrent potentially life threatening arrhythmia or symptomatic arrhythmia Clinically significant valvular heart disease Type 1 diabetes mellitus Uncontrolled Type II diabetes mellitus (Hemaglobin subtype A1C (HbA1C) >11 %) History of malignancy including leukemia and lymphoma (but not basal cell skin carcinoma) within the past five years Participation in any clinical investigation within 4 weeks prior to dosing or longer if required by local regulation. Donation or loss of 400 mL or more of blood within 8 weeks prior to dosing. Significant illness within the two weeks prior to dosing. Any surgical or medical condition which might significantly alter the absorption, distribution, metabolism, or excretion of study drugs including, but not limited to, any of the following: History of major gastrointestinal tract surgery such as gastrectomy, gastroenterostomy, or bowel resection -Currently active or previously active inflammatory bowel disease during the 12 months prior to Visit 1 Currently active gastritis, duodenal or gastric ulcers, or gastrointestinal/rectal bleeding during the 3 months prior to Visit 1. Any history of pancreatic injury, pancreatitis or evidence of impaired pancreatic function/injury as indicated by abnormal lipase or amylase Evidence of hepatic disease, a history of hepatic encephalopathy, a history of esophageal varices, or a history of portocaval shunt Current treatment with cholestyramine or cholestipol resins History of immunocompromise, including a positive HIV test result. History of a positive Hepatitis B surface antigen (HBsAg) or Hepatitis C test result. History of drug or alcohol abuse within the 12 months prior to dosing. Persons directly involved in the execution of this protocol. Any condition that in the opinion of the investigator or the Novartis medical monitor would jeopardize the evaluation of efficacy or safety History of noncompliance to medical regimens or unwillingness to comply with the study protocol Known or suspected contraindications to the study medications, including history of allergy to Angiotensin converting enzyme (ACE) inhibitors and/or to thiazide diuretics or other sulfonamide derived drug Any surgical or medical condition, which in the opinion of the investigator, may place the patient at higher risk from his/her participation in the study, or is likely to prevent the patient from complying with the requirements of the study or completing the study Use of any prescription drug or over-the-counter (OTC) medication which is prohibited by the protocol. Patients who previously participated in any Aliskiren study. Pregnant or nursing woman. Other protocol-defined inclusion/exclusion criteria may apply", "candidate_expression": "((Acetylsalicyclic acid (ASA) treatment >1g/day) AND (Aliskiren) AND (Aliskiren study previously) AND (Angiotensin converting enzyme (ACE) inhibitors) AND (Donation of blood 400 mL or more within 8 weeks prior) AND (GFR < 40 ml/min/1.73m2) AND (Grade WHO classification 3) AND (HIV test positive) AND (Hemaglobin subtype A1C (HbA1C) >11 %) AND (Hepatitis B surface antigen (HBsAg) test positive) AND (Hepatitis C test positive) AND (History) AND (Kidney disease) AND (Mean Sitting Diastolic Blood Pressure (MSDBP) 110 mmHg) AND (Mean Sitting Systolic Blood Pressure MSSBP 180 mmHg) AND (New York Heart Association (NYHA) Class II-IV) AND (Non steroidal anti-inflammatory drug (NSAIDs)) AND (Pregnant) AND (Second degree heart block) AND (Serum albumin < 2.0mg/dL) AND (Serum potassium < 3.5 > 5.1 mEq/L) AND (Severe Hypertension) AND (Significant illness within the two weeks prior) AND (Type 1 diabetes mellitus) AND (Type II diabetes mellitus Uncontrolled) AND (alcohol abuse) AND (allergy history of) AND (amylase abnormal) AND (any clinical investigation within 4 weeks prior to dosing) AND (arrhythmia potentially life threatening) AND (arrhythmia symptomatic) AND (basal cell skin carcinoma) AND (bowel resection previously active) AND (cerebrovascular accident) AND (cholestipol resins Current) AND (cholestyramine Current) AND (comply with the study protocol unwillingness to) AND (complying with the requirements of the study likely to prevent the patient from) AND (condition that would jeopardize the evaluation of efficacy that would jeopardize safety) AND (contraindications) AND (coronary bypass surgery) AND (diabetes) AND (drug abuse) AND (duodenal) AND (esophageal varices) AND (gastrectomy) AND (gastric ulcers) AND (gastritis) AND (gastroenterostomy) AND (gastrointestinal bleeding) AND (heart failure) AND (hepatic disease) AND (hepatic encephalopathy) AND (history) AND (hypertension) AND (hypertensive encephalopathy) AND (immunocompromise) AND (inflammatory bowel disease Currently active during the 12 months prior) AND (leukemia) AND (lipase abnormal) AND (loss of blood 400 mL or more within 8 weeks prior) AND (lymphoma) AND (major gastrointestinal tract surgery) AND (malignancy within the past five years) AND (medical condition) AND (myocardial infarction) AND (noncompliance to medical regimens History of) AND (nursing) AND (over-the-counter (OTC) medication) AND (pancreatic function impaired) AND (pancreatic injury) AND (pancreatitis) AND (percutaneous coronary intervention (PCI)) AND (portocaval shunt) AND (prescription drug) AND (prevent) AND (rectal bleeding) AND (study medications) AND (sulfonamide derived drug other) AND (surgical condition) AND (thiazide diuretics) AND (third degree heart block) AND (unstable angina pectoris) AND (valvular heart disease) AND (woman Other protocol-defined) AND NOT (pacemaker))"}
```
