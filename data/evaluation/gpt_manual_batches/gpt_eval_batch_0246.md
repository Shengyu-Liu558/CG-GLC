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
{"candidate_id": "LLM06126", "doc_id": "NCT02924870_exc", "case_bucket": "or", "source_criterion": "osteoarticular, neuromuscular or cognitive limitation that prevents ambulation previous diagnosis of active neoplastic disease institutionalized patients; alcohol consumption >60 g/day patient belonging to another health sector in the Community of Madrid or other community participation in another study within 6 months prior.", "candidate_expression": "((alcohol consumption >60 g/day) AND (cognitive limitation) AND (institutionalized) AND (neoplastic disease) AND (neuromuscular limitation) AND (osteoarticular limitation) AND (participation in another study within 6 months prior.) AND NOT (ambulation))"}
{"candidate_id": "LLM06127", "doc_id": "NCT03495609_exc", "case_bucket": "or", "source_criterion": "History of allergic reaction to compounds of similar chemical or biologic composition to hCG receiving medication that could interfere with the study protocol objectives (hormonal contraceptives, androgens, prednisone, thyroid hormones, insulin) previous treatment with follicle stimulating hormone for assisted reproduction uncontrolled intercurrent illness Heart disease Severe cognitive decline Psychiatric desease HIV positive Hepatitis B or C infection", "candidate_expression": "((HIV positive) AND (Heart disease) AND (Hepatitis B infection) AND (Hepatitis C infection) AND (Psychiatric desease) AND (allergic reaction History) AND (androgens) AND (assisted reproduction) AND (cognitive decline Severe) AND (compounds of similar chemical or biologic composition to hCG) AND (follicle stimulating hormone) AND (hCG) AND (hormonal contraceptives) AND (insulin) AND (intercurrent illness uncontrolled) AND (medication receiving could interfere with the study protocol objectives) AND (prednisone) AND (thyroid hormones) AND (treatment previous))"}
{"candidate_id": "LLM06128", "doc_id": "NCT03491059_inc", "case_bucket": "or", "source_criterion": "males and females greater than or equal to 18 years of age current regular user of e-cigarettes (use at least once daily for the past 30 days) with nicotine strength > 6mg/ml health medical history abstinent from any tobacco/nicotine use for 4 hours prior to imaging", "candidate_expression": "((> 6mg/ml) AND (abstinent) AND (age) AND (at least once daily) AND (e-cigarettes) AND (females) AND (for 4 hours prior to imaging) AND (for the past 30 days) AND (greater than or equal to 18 years) AND (health) AND (imaging) AND (males) AND (medical history) AND (nicotine) AND (nicotine strength) AND (regular) AND (tobacco) AND (user))"}
{"candidate_id": "LLM06129", "doc_id": "NCT03376763_inc", "case_bucket": "or", "source_criterion": "Subjects must be capable of providing signed and dated written informed consent by date of Visit 0 (-2 week). Male and female aged =19 and < 65 years. Subjects diagnosed of schizophrenia as defined by Diagnostic and Statistical Manual of Mental Disorders, 4th edition text revision or 5th edition (DSM-<U+2163>-TR or 5) criteria, and a history of illness for at least for 3 years prior to screening. Subjects who take atypical antipsychotic drugs, and should be maintained on current antipsychotic drugs (including atypical antipsychotic drugs) and dose for at least 4 weeks prior to the screening. Subjects who need antipsychotic treatment (other than clozapine), and would be stable when switching to long-acting injectable aripiprazole in the investigator's judgement. Subjects must exhibit willingness, physiologic capability, and an educational level sufficient to comply with all protocol procedures.", "candidate_expression": "((Male) AND (Subjects must be capable of providing signed and dated written informed consent by date of Visit 0 (-2 week).) AND (Subjects must exhibit willingness, physiologic capability, and an educational level sufficient to comply with all protocol procedures.) AND (aged =19 and < 65 years) AND (atypical antipsychotic drugs) AND (female) AND (schizophrenia Diagnostic and Statistical Manual of Mental Disorders, 4th edition text revision or 5th edition (DSM-<U+2163>-TR or 5) criteria history of illness))"}
{"candidate_id": "LLM06130", "doc_id": "NCT00720031_exc", "case_bucket": "or", "source_criterion": "Cardio-vascular pathologies, evoluting and uncontrolled, (severe HTA), cardiac deficiency, severe angor, severe arrhythmia. Infectious pathologies evoluting and requiring antibiotherapy. Patients HIV+. Transplanted patients or patients suffering from severe auto-immune disease. Psychiatric troubles that do not allow the protocol follow-up. Pregnant or breast-feeding women. No contraception.", "candidate_expression": "((HIV +) AND (HIV+) AND (Infectious pathologies) AND (Psychiatric troubles do not allow the protocol follow-up) AND (antibiotherapy) AND (women) AND NOT (contraception) AND ((Cardio-vascular pathologies) OR (HTA severe) OR (angor severe) OR (arrhythmia severe) OR (cardiac deficiency)) AND ((evoluting) OR (requiring antibiotherapy)) AND ((Transplanted) OR (severe auto-immune disease)) AND ((Pregnant) OR (breast-feeding)) AND ((evoluting) OR (uncontrolled)))"}
{"candidate_id": "LLM06131", "doc_id": "NCT02156999_exc", "case_bucket": "or", "source_criterion": "Kidney, parathyroid, congenital bone metabolic disease", "candidate_expression": "(disease Kidney parathyroid congenital bone metabolic)"}
{"candidate_id": "LLM06132", "doc_id": "NCT02630628_exc", "case_bucket": "or", "source_criterion": "Renal disease unrelated to SLE (e.g. diabetes mellitus, other glomerular or tubulointerstitial disease, renovascular disease), or transplanted kidney. Estimated glomerular filtration rate (eGFR by MDRD) =20 mL/min per 1.73 m2 or serum creatinine >300 micromol/L (3.39 mg/dL) at screening. Renal biopsy showing cellular or fibrocellular crescent in more than 25% of glomeruli. CNS or other severe organ manifestation of lupus that necessitate aggressive immunosuppressive therapy on its own. Co-morbidities that require corticosteroid therapy (e.g. asthma, inflammatory bowel disease). Treatment with prednisolone (or prednisone, or equivalent) at >20 mg/D for over 4 weeks within the past 3 months. Treatment with MMF at >1.5 g/D for over 4 weeks within the past 3 months. Known hypersensitivity or intolerability to prednisolone (or prednisone, or equivalent), TAC, or MMF at a dose of 1.25 g or below per day. Subjects who are already on treatment with TAC, cyclosporine or any other calcineurin inhibitor for over 4 weeks within the past 12 months. Treatment with cyclophosphamide, leflunomide, or methotrexate for over 2 weeks, or use of biological agent(s) regardless of duration, within the past 6 months (Note: prior use of azathioprine, mizoribine, intravenous immunoglobulins and anti-malarials is allowed). Uncontrolled hypertension with systolic BP >160 mmHg or diastolic BP >95 mmHg. Women who are pregnant or breastfeeding. Women with childbearing potential or their male partners, who refuse to use an effective birth control method", "candidate_expression": "((1.25 g or below per day) AND (2 weeks) AND (3.39 mg/dL) AND (=20 mL/min per 1.73 m2) AND (>1.5 g/D for over 4 weeks) AND (>160 mmHg) AND (>20 mg/D for over 4 weeks) AND (>300 micromol/L) AND (>95 mmHg) AND (Co-morbidities) AND (MMF) AND (Renal biopsy) AND (SLE) AND (Uncontrolled) AND (Women who are pregnant or breastfeeding) AND (Women with childbearing potential or their male partners, who refuse to use an effective birth control method) AND (allowed) AND (biological agent) AND (corticosteroid therapy) AND (eGFR) AND (hypertension) AND (immunosuppressive therapy) AND (lupus) AND (more than 25% of glomeruli) AND (over 4 weeks) AND (past 12 months.) AND (past 3 months) AND (past 6 months) AND (unrelated) AND ((Renal disease) OR (transplanted kidney)) AND ((Estimated glomerular filtration rate) OR (serum creatinine)) AND ((cellular crescent) OR (fibrocellular crescent)) AND ((CNS) OR (organ manifestation)) AND ((asthma) OR (inflammatory bowel disease)) AND ((prednisolone) OR (prednisone) OR (prednisone equivalent)) AND ((diabetes mellitus) OR (glomerular disease) OR (renovascular disease) OR (tubulointerstitial disease)) AND ((hypersensitivity) OR (intolerability)) AND ((MMF) OR (TAC) OR (prednisolone) OR (prednisone) OR (prednisone equivalent)) AND ((TAC) OR (calcineurin inhibitor) OR (cyclosporine)) AND ((cyclophosphamide) OR (leflunomide) OR (methotrexate)) AND ((anti-malarials) OR (azathioprine) OR (immunoglobulins) OR (mizoribine)) AND ((diastolic BP) OR (systolic BP)))"}
{"candidate_id": "LLM06133", "doc_id": "NCT00720031_exc", "case_bucket": "or", "source_criterion": "Cardio-vascular pathologies, evoluting and uncontrolled, (severe HTA), cardiac deficiency, severe angor, severe arrhythmia. Infectious pathologies evoluting and requiring antibiotherapy. Patients HIV+. Transplanted patients or patients suffering from severe auto-immune disease. Psychiatric troubles that do not allow the protocol follow-up. Pregnant or breast-feeding women. No contraception.", "candidate_expression": "((+) AND (HIV) AND (HIV+) AND (Infectious pathologies) AND (No) AND (Psychiatric troubles) AND (antibiotherapy) AND (contraception) AND (do not allow the protocol follow-up) AND (severe) AND (women) AND ((Cardio-vascular pathologies) OR (HTA) OR (angor) OR (arrhythmia) OR (cardiac deficiency)) AND ((evoluting) OR (requiring antibiotherapy)) AND ((Transplanted) OR (severe auto-immune disease)) AND ((Pregnant) OR (breast-feeding)) AND ((evoluting) OR (uncontrolled)))"}
{"candidate_id": "LLM06134", "doc_id": "NCT03063866_inc", "case_bucket": "or", "source_criterion": "Patients aged between 40 and 60 years old. With Child score B or C Presented for elective gastrointestinal endoscopy", "candidate_expression": "((B) AND (C) AND (Child score) AND (aged) AND (between 40 and 60 years old) AND (elective) AND (gastrointestinal endoscopy))"}
{"candidate_id": "LLM06135", "doc_id": "NCT02321839_inc", "case_bucket": "or", "source_criterion": "Signed informed consent form Male or female of aged 50 years or older Typical AMD and PCV patients BCVA of 24 letters or over", "candidate_expression": "((24 letters or over) AND (50 years or older) AND (BCVA) AND (Signed informed consent form) AND (aged) AND ((Male) OR (female)) AND ((AMD) OR (PCV patients)))"}
{"candidate_id": "LLM06136", "doc_id": "NCT03351972_exc", "case_bucket": "other", "source_criterion": "dysphagia severe gastroparesis requiring endoscopic placement of capsule small bowel obstruction pregnancy", "candidate_expression": "((capsule) AND (dysphagia) AND (endoscopic placement) AND (gastroparesis) AND (pregnancy) AND (requiring) AND (severe) AND (small bowel obstruction))"}
{"candidate_id": "LLM06137", "doc_id": "NCT03491059_exc", "case_bucket": "or", "source_criterion": "not a regular user of e-cigarettes pregnant or lactating (only excluded from imaging study) prisoner incapable of giving informed consent unable to lie flat on the scanner for extended periods of time unstable medical condition like heart disease, uncontrolled hypertension, thyroid disease, diabetes, renal or liver impairment, or glaucoma prostatic hypertrophy, stroke, or ulcer in past year psychiatric conditions such as schizophrenia, adult ADHD, or bipolar disorder current or regular use of psychiatric medications such as tranquilizers, antipsychotics, and/or antidepressants use of medications that are inducers of CYP2A6 (a nicotine metabolizing enzyme) such as rifampicin, dexamethasone, phenobarbital, and other anti-convulsant drugs unable to communicate in English current use of smokeless tobacco, tobacco cigarettes (5 and fewer a day) occasional use of pipes is permitted if subject abstains for the week prior to the study older than 80 years", "candidate_expression": "((5 and fewer a day) AND (adult ADHD) AND (anti-convulsant drugs) AND (antidepressants) AND (antipsychotics) AND (bipolar disorder) AND (dexamethasone) AND (diabetes) AND (e-cigarettes) AND (glaucoma) AND (heart disease) AND (hypertension) AND (incapable of giving informed consent) AND (inducers of CYP2A6) AND (liver impairment) AND (medical condition) AND (medications) AND (nicotine metabolizing enzyme) AND (not) AND (older than 80) AND (phenobarbital) AND (pregnant or lactating (only excluded from imaging study)) AND (prisoner) AND (prostatic hypertrophy) AND (psychiatric conditions) AND (psychiatric medications) AND (regular user) AND (renal impairment) AND (rifampicin) AND (schizophrenia) AND (smokeless tobacco) AND (stroke) AND (thyroid disease) AND (tobacco cigarettes) AND (tranquilizers) AND (ulcer) AND (unable to lie flat on the scanner for extended periods of time) AND (uncontrolled) AND (unstable) AND (years))"}
{"candidate_id": "LLM06138", "doc_id": "NCT00862446_exc", "case_bucket": "other", "source_criterion": "Enrollment in another trial Lack of consent", "candidate_expression": "((Enrollment in another trial) AND (Lack of consent))"}
{"candidate_id": "LLM06139", "doc_id": "NCT02742233_inc", "case_bucket": "or", "source_criterion": "Diagnosis of diabetes mellitus according to World Health Organization criteria ( treatment with insulin or an oral hypoglycemic agent, twice random glucose measurements major than 200 mg/dl, or a fasting glucose major than 140 mg/dl) Ulcer located on the legs or feet, stage III or IV (Wagner Classification System) The subject agrees to comply with study protocol requirements and all follow up visit requirements.", "candidate_expression": "((The subject agrees to comply with study protocol requirements and all follow up visit requirements) AND (diabetes mellitus World Health Organization criteria) AND ((Ulcer) OR (stage III or IV Wagner Classification System)) AND ((feet) OR (legs)) AND ((insulin) OR (oral hypoglycemic agent)) AND ((fasting glucose major than 140 mg/dl) OR (random glucose measurements twice major than 200 mg/dl) OR (treatment)))"}
{"candidate_id": "LLM06140", "doc_id": "NCT03259243_exc", "case_bucket": "or", "source_criterion": "Patient with history of allergy in any kind anesthetic drug Patient who pregnant Patient who sign for single port gynecologic laparoscopic surgery or NOTE surgery Patient whom the surgery is withhold or canceled Patient whom the surgery is converted to laparotomy", "candidate_expression": "((NOTE surgery) AND (allergy history) AND (anesthetic drug any kind) AND (canceled) AND (gynecologic laparoscopic surgery single port) AND (laparotomy) AND (pregnant) AND (surgery) AND (surgery converted to) AND (withhold))"}
{"candidate_id": "LLM06141", "doc_id": "NCT02689817_exc", "case_bucket": "or", "source_criterion": "Existing sacral pressure ulcer, undergoing a cardiac procedure, or inability to provide informed consent.", "candidate_expression": "((inability to provide informed consent) AND ((cardiac procedure) OR (inability to provide informed consent) OR (sacral pressure ulcer)))"}
{"candidate_id": "LLM06142", "doc_id": "NCT01665417_inc", "case_bucket": "or", "source_criterion": "Pathologic confirmation of lung adenocarcinoma with measurable disease, defined as at least one lesion that can be accurately measured in at least one dimension (longest diameter to be recorded on CT); Patients must have previously untreated locally advanced or metastatic NSCLC; Patients must have lung cancer with a documented EGFR activating mutation (exon 19 deletion, L858R).", "candidate_expression": "((NSCLC) AND (Pathologic) AND (at least one) AND (can be accurately measured in at least one dimension) AND (confirmation) AND (lesion) AND (lung adenocarcinoma) AND (lung cancer) AND (untreated) AND (with EGFR activating mutation) AND (with measurable disease) AND ((L858R) OR (exon 19 deletion)) AND ((locally advanced) OR (metastatic)))"}
{"candidate_id": "LLM06143", "doc_id": "NCT03333655_inc", "case_bucket": "or", "source_criterion": "Response assessment of complete response (CR), partial response (PR), long stable disease (SD) for >3 months with a cancer immunotherapy treatment for metastatic cancer or hematologic malignancies either through a marketed CPI or through participation in a Roche/Genentech CPI clinical trial. Availability of tumor biopsy material extracted and preserved by the investigating site.", "candidate_expression": "((Response assessment) AND (cancer) AND (for >3 months) AND (immunotherapy treatment) AND ((hematologic malignancies) OR (metastatic cancer)) AND ((marketed CPI) OR (participation in a Roche/Genentech CPI clinical trial)) AND ((complete response (CR)) OR (long stable disease (SD)) OR (partial response (PR))))"}
{"candidate_id": "LLM06144", "doc_id": "NCT02607319_exc", "case_bucket": "or", "source_criterion": "Evidence of low ovarian reserve by at least one of the following: AMH = 1,5 ng/mL and/or basal CD 3 FSH = 10 mIU/mL and/or basal CD 3 Estradiol = 60 ng/mL and/or previous egg collection yield = 3 oocytes. Preexisting medical condition (thyroid disease, diabetes mellitus, hypertension, pulmonary conditions, cardiac condition…). Severe male factor infertility (Total motile sperm count < 5 million/ml and/or normal WHO morphology <20%). Hypersensitivity to Heparin or its derivatives. Acquired thrombophilia. Active hemorrhage or increased risk of bleeding due to impairment of homeostasis. Severe impairment of liver or pancreatic function. Severe renal insufficiency (Creatinine Clearance < 30 ml/min). Injuries to or operations on the central nervous system, eyes and ears within the last 2 months. Disseminated Intravascular Coagulation (DIC) attributable to heparin-induced thrombocytopenia. Acute bacterial endocarditis and endocarditis lenta. Any organic lesion with high risk of bleeding (e.g.: active peptic ulcer, hemorrhagic stroke, cerebral aneurysm or cerebral neoplasms).", "candidate_expression": "((< 30 ml/min) AND (< 5 million/ml) AND (<20%) AND (= 1,5 ng/mL) AND (= 10 mIU/mL) AND (= 3 oocytes) AND (= 60 ng/mL) AND (Acquired) AND (Creatinine Clearance) AND (DIC) AND (Disseminated Intravascular Coagulation) AND (Heparin) AND (Hypersensitivity) AND (Severe) AND (heparin-induced thrombocytopenia) AND (high) AND (impairment of homeostasis) AND (increased) AND (last 2 months) AND (low ovarian reserve) AND (male factor infertility) AND (organic lesion) AND (renal insufficiency) AND (risk of bleeding) AND (thrombophilia) AND ((cardiac condition) OR (diabetes mellitus) OR (hypertension) OR (pulmonary conditions) OR (thyroid disease)) AND ((Total motile sperm count) OR (normal WHO morphology)) AND ((Active hemorrhage) OR (risk of bleeding)) AND ((AMH) OR (basal CD 3 Estradiol) OR (basal CD 3 FSH) OR (egg collection yield)) AND ((impairment of liver) OR (impairment of pancreatic function)) AND ((Injuries) OR (operations)) AND ((central nervous system) OR (ears) OR (eyes)) AND ((Acute bacterial endocarditis) OR (endocarditis lenta)) AND ((active peptic ulcer) OR (cerebral aneurysm) OR (cerebral neoplasms) OR (hemorrhagic stroke)))"}
{"candidate_id": "LLM06145", "doc_id": "NCT03318393_exc", "case_bucket": "or", "source_criterion": "Patients with known or suspected heparin induced thrombocytopenia prior to consent Patients with hepatic failure defined as coagulopathy with elevated transaminases more than three times normal values Patients with plan to decannulate from ECMO within 48 hours Known or suspected pregnant women Previous enrollment in this study Primary language spoken that is not English or Spanish", "candidate_expression": "((Previous enrollment in this study) AND (coagulopathy) AND (decannulate from ECMO within 48 hours Known) AND (heparin known suspected) AND (hepatic failure) AND (pregnant suspected) AND (thrombocytopenia heparin induced prior to consent) AND (transaminases elevated more than three times normal values) AND (women))"}
{"candidate_id": "LLM06146", "doc_id": "NCT02077556_exc", "case_bucket": "or", "source_criterion": "Pregnancy Tuberculosis Hepatitis B or C carrier status Human immunodeficiency virus-positive status Retransplantation or multiorgan transplantation History of rheumatoid arthritis Use of drugs that might have enhanced or inhibited CYP3A4 or P-gp activity", "candidate_expression": "((Hepatitis B carrier) AND (Hepatitis C carrier) AND (Human immunodeficiency virus positive) AND (Pregnancy) AND (Retransplantation) AND (Tuberculosis) AND (rheumatoid arthritis) AND (transplantation multiorgan))"}
{"candidate_id": "LLM06147", "doc_id": "NCT03185130_inc", "case_bucket": "or", "source_criterion": "Age 10 to 65 years Temperature less than 100.4 F Normal neurologic exam and normal mental status", "candidate_expression": "((Age 10 to 65 years) AND (Temperature less than 100.4 F) AND (neurologic exam Normal) AND ((mental status) OR (normal)))"}
{"candidate_id": "LLM06148", "doc_id": "NCT03340740_exc", "case_bucket": "other", "source_criterion": "Use of antihistamine within the past 72 hours Chronic Pulmonary Condition other than asthma Other contraindication to cetirizine Severe asthma exacerbation requiring resuscitation", "candidate_expression": "((Chronic Pulmonary Condition) AND (antihistamine within the past 72 hours) AND (asthma exacerbation Severe) AND (cetirizine) AND (contraindication) AND (resuscitation) AND NOT (asthma))"}
{"candidate_id": "LLM06149", "doc_id": "NCT03639519_inc", "case_bucket": "other", "source_criterion": "Elective Cardiac surgery American Society of Anesthesiologists physical status class I-III", "candidate_expression": "((American Society of Anesthesiologists physical status class I-III) AND (Elective Cardiac surgery))"}
{"candidate_id": "LLM06150", "doc_id": "NCT02141061_inc", "case_bucket": "other", "source_criterion": "1. Speak, read, and understand English or Spanish and is willing and able to provide written informed consent on an IRB-approved form prior to the initiation of any study procedures; 2. Healthy, premenopausal female age 18-47; 3. History of menstrual events that occur in regular cycles 4. Agreement not to attempt to become pregnant 5. Agrees to use double-barrier contraception during the study and for 30 days after discontinuation of study medication. Acceptable double-barrier methods are: male condom with spermicide; male condom with diaphragm; diaphragm containing spermicide plus additional intra-vaginal spermicide; 6. Has a negative pregnancy test at the Screening visit. An exception for the pregnancy test requirement will be granted for subjects reporting surgical sterilization in medical history 7. Normal laboratory values or clinically insignificant findings at screening as determined by the Investigator; 8. Subject is willing to remain in the clinic overnight for PK assessment on Days 0 and 8 9. Ability to complete the study procedures in compliance with the protocol.", "candidate_expression": "((Ability to complete the study procedures in compliance with the protocol.) AND (Acceptable double-barrier methods are: male condom with spermicide; male condom with diaphragm; diaphragm containing spermicide plus additional intra-vaginal spermicide;) AND (Agreement not to attempt to become pregnant) AND (Agrees to use double-barrier contraception during the study and for 30 days after discontinuation of study medication.) AND (Healthy) AND (History) AND (Normal laboratory values) AND (age 18-47) AND (as determined by the Investigator) AND (clinically insignificant) AND (female) AND (findings clinically insignificant at screening screening) AND (laboratory) AND (laboratory Normal) AND (menstrual events that occur in regular cycles) AND (pregnancy test negative at the Screening visit) AND (premenopausal))"}
```
