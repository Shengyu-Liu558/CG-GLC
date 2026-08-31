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
{"candidate_id": "LLM03151", "doc_id": "NCT03097068_exc", "case_bucket": "or", "source_criterion": "History of anti-vascular endothelial growth factor treatment in the past 12 months Any diabetic macular edema treatment in the past 4 months Heart attack, stroke, transient ischemic attack or acute congestive heart failure within 4 months", "candidate_expression": "((Heart attack) AND (acute congestive heart failure) AND (anti-vascular endothelial growth factor) AND (diabetic macular edema) AND (in the past 12 months) AND (in the past 4 months) AND (stroke) AND (transient ischemic attack) AND (treatment) AND (within 4 months))"}
{"candidate_id": "LLM03152", "doc_id": "NCT02652637_exc", "case_bucket": "or", "source_criterion": "Emergency surgery needed Bowel obstruction Colonoscopy scheduled to be undertaken peroperatively Other reason indicating mechanical preparation or contradicting it Allergy to used drugs (PEG, neomycin, metronidazole)", "candidate_expression": "((Allergy) AND (Bowel obstruction) AND (Colonoscopy) AND (Emergency surgery) AND (PEG) AND (contradicting) AND (drugs) AND (mechanical preparation) AND (metronidazole) AND (needed) AND (neomycin) AND (peroperatively) AND (scheduled) AND (undertaken))"}
{"candidate_id": "LLM03153", "doc_id": "NCT03336801_exc", "case_bucket": "or", "source_criterion": "American Association of Anesthesiology class 1-3 American Heart Association class >3 BMI >37 Insulin treated diabetes Pregnancy or breast feeding Sensistivity/allergy against anesthetic agents Inadequate understanding about the study Depressed kidney function and/or AKI Depressed liver function Genetic malignant hyperthermia", "candidate_expression": "((American Association of Anesthesiology class 1-3) AND (American Heart Association class >3) AND (BMI >37) AND (Depressed liver function) AND (Inadequate understanding about the study) AND (Insulin) AND (anesthetic agents) AND (diabetes Insulin treated) AND (kidney function Depressed) AND (liver function Depressed) AND (malignant hyperthermia Genetic) AND ((Pregnancy) OR (breast feeding)) AND ((Sensistivity) OR (allergy)) AND ((AKI) OR (Depressed kidney function)))"}
{"candidate_id": "LLM03154", "doc_id": "NCT02537899_exc", "case_bucket": "or", "source_criterion": "Non survivable injury Multiple significant trauma (i.e. significant intracranial and extracranial injuries including limb fractures) that would limit observation of recovery from spinal cord injury Other conditions that would limit clinical assessment of outcomes (e.g. dementia, demyelinating disease, autoimmune disease, etc) Refusal of treatment or contraindication to NeuroAiD", "candidate_expression": "((Multiple) AND (NeuroAiD) AND (Non survivable) AND (autoimmune disease) AND (contraindication) AND (dementia) AND (demyelinating disease) AND (extracranial injuries) AND (injury) AND (intracranial injuries) AND (limb fractures) AND (significant) AND (trauma))"}
{"candidate_id": "LLM03155", "doc_id": "NCT02226887_exc", "case_bucket": "or", "source_criterion": "Patients under 18 Pregnancy and Lactation Patients allergic to polyglycolic / trimethylene carbonate Carrier of prosthetic mesh in the ostomy Patients presenting midline hernia. Patients affected by inflammatory bowel disease", "candidate_expression": "((allergic) AND (inflammatory bowel disease) AND (midline hernia) AND (ostomy) AND (polyglycolic carbonate) AND (prosthetic mesh) AND (trimethylene carbonate) AND (under 18 under 18) AND ((Lactation) OR (Pregnancy)))"}
{"candidate_id": "LLM03156", "doc_id": "NCT02777424_inc", "case_bucket": "or", "source_criterion": "Patient with spontaneous intracranial hemorrhage or traumatic intracranial hemorrhage or patient requiring neurological surgery Coagulation disorder defined by PT less than 60%", "candidate_expression": "((Coagulation disorder) AND (PT) AND (less than 60%) AND (requiring) AND ((neurological surgery) OR (spontaneous intracranial hemorrhage) OR (traumatic intracranial hemorrhage)))"}
{"candidate_id": "LLM03157", "doc_id": "NCT02621541_inc", "case_bucket": "or", "source_criterion": "suspicion of nonfunctional P-NET on primary CT (i.e hypervascularity) or MRI signed informed consent", "candidate_expression": "((hypervascularity) AND (nonfunctional P-NET) AND (signed informed consent) AND (suspicion) AND ((MRI) OR (primary CT)))"}
{"candidate_id": "LLM03158", "doc_id": "NCT03416413_exc", "case_bucket": "or", "source_criterion": "Current DVT Recurrent varicose veins Arterial disease (ABPI<0.8) Vein diameter < 3mm Preference for one of the treatment options Patient who are unwilling to participate Inability or unwillingness to complete questionnaires Inability to attend follow-up appointments Patient currently included in a study of varicose vein treatment", "candidate_expression": "((< 3mm) AND (<0.8) AND (ABPI) AND (Arterial disease) AND (Current) AND (DVT) AND (Inability to attend follow-up appointments) AND (Patient currently included in a study of varicose vein treatment) AND (Recurrent) AND (Vein diameter) AND (unwilling to participate) AND (varicose veins) AND ((Inability to complete questionnaires) OR (unwillingness to complete questionnaires)))"}
{"candidate_id": "LLM03159", "doc_id": "NCT02924870_inc", "case_bucket": "or", "source_criterion": "subjects older than 35 years diagnosis of moderate to very severe COPD (FEV1 <80% predicted), according to the GesEPOC criteria, established at least 3 months current or former smoker with an accumulated consumption >10 packs x year hospital admission for COPD exacerbation", "candidate_expression": "((COPD at least 3 months very severe) AND (COPD exacerbation) AND (FEV1 <80% predicted) AND (GesEPOC criteria,) AND (admission) AND (consumption >10 packs x year) AND (smoker) AND (years older than 35 moderate))"}
{"candidate_id": "LLM03160", "doc_id": "NCT01604187_exc", "case_bucket": "or", "source_criterion": "A previous history of intolerance to the study drug or related compounds and additives History of alcoholism, drug abuse, psychiatric, psychological or other emotional problems that are likely to invalidate informed consent Sleep apnoea Chronic obstructive pulmonary disease BMI = 35 or weight < 50 kg SpO2 < 90 % Concomitant drug therapy known to cause significant enzyme induction or inhibition of CYP 3A4. Pregnancy or nursing.", "candidate_expression": "((< 50 kg) AND (< 90 %) AND (= 35) AND (BMI) AND (Chronic obstructive pulmonary disease) AND (Concomitant) AND (Pregnancy) AND (Sleep apnoea) AND (SpO2) AND (alcoholism) AND (drug abuse) AND (drug therapy) AND (emotional problems) AND (enzyme induction of CYP 3A4) AND (enzyme inhibition of CYP 3A4) AND (intolerance) AND (nursing) AND (previous history) AND (psychiatric problems) AND (psychological problems) AND (related compounds) AND (study drug) AND (weight))"}
{"candidate_id": "LLM03161", "doc_id": "NCT01664507_inc", "case_bucket": "other", "source_criterion": "croup children between 6 month and 5 years old Westley croup score between 3 and 11", "candidate_expression": "((Westley croup score) AND (between 3 and 11) AND (between 6 month and 5 years) AND (children) AND (old))"}
{"candidate_id": "LLM03162", "doc_id": "NCT03317197_inc", "case_bucket": "other", "source_criterion": "The group of patients who participated in the study included adults aged at least 19 years among the atraumatic CA outpatients who came to the ER and received CPR.", "candidate_expression": "((CPR) AND (ER) AND (adults) AND (aged at least 19 years) AND (atraumatic CA) AND (outpatients))"}
{"candidate_id": "LLM03163", "doc_id": "NCT02613039_exc", "case_bucket": "or", "source_criterion": "Participation in another clinical trial. Known or suspected (or history of) malignancy or chronic illness. Serious organic or mental disease diagnosed by a psychiatrist (e.g., major depression currently treated with antidepressant medication) suspected on the basis of the medical history and/or clinical examination. Conditions that may affect the compliance to the study. Contraindications to therapy with the study drug or hypersensitivity to the study drug (active ingredient or excipients of the formulation).", "candidate_expression": "((Conditions that may affect the compliance to the study.) AND (Contraindications to therapy with the study drug or hypersensitivity to the study drug (active ingredient or excipients of the formulation).) AND (Known) AND (antidepressant medication) AND (chronic illness) AND (clinical examination) AND (currently) AND (diagnosed by a psychiatrist) AND (history of) AND (major depression) AND (malignancy) AND (medical history) AND (mental disease) AND (organic disease) AND (suspected) AND (treated))"}
{"candidate_id": "LLM03164", "doc_id": "NCT02202369_inc", "case_bucket": "other", "source_criterion": "Subjects undergoing a single level lumbar decompression and fusion > 18 years of age and < 70 years of age The subject is willing and able to understand, sign and date the study specific patient informed consent and HIPAA authorization to volunteer participation in the study", "candidate_expression": "((> 18 years and < 70 years) AND (The subject is willing and able to understand, sign and date the study specific patient informed consent and HIPAA authorization to volunteer participation in the study) AND (age) AND (lumbar decompression) AND (lumbar fusion) AND (single level))"}
{"candidate_id": "LLM03165", "doc_id": "NCT02951520_inc", "case_bucket": "other", "source_criterion": "Adult patients scheduled for arthroscopic knee ligament reconstruction", "candidate_expression": "((Adult) AND (arthroscopic knee ligament reconstruction scheduled))"}
{"candidate_id": "LLM03166", "doc_id": "NCT03472495_exc", "case_bucket": "or", "source_criterion": "Limited English proficiency (LEP) Pregnant Prisoners Wolff Parkinson White syndrome Administration of electrical or chemical cardioversion before screening Administration of other antiarrhythmics for acute heart rate control (excluding adenosine) History of allergy or idiosyncratic reaction to diltiazem Unable to take oral medications Heart rate <60 beats/min", "candidate_expression": "((<60 beats/min) AND (Heart rate) AND (LEP) AND (Limited English proficiency) AND (Pregnant) AND (Prisoners) AND (Unable to take) AND (Wolff Parkinson White syndrome) AND (acute) AND (adenosine) AND (allergy) AND (antiarrhythmics) AND (before screening) AND (chemical cardioversion) AND (diltiazem) AND (electrical cardioversion) AND (excluding) AND (heart rate control) AND (idiosyncratic reaction) AND (oral medications) AND (screening))"}
{"candidate_id": "LLM03167", "doc_id": "NCT03256864_inc", "case_bucket": "other", "source_criterion": "Liver Transplant Recipients have received liver transplantations for at least 6+1 months prior to enrollment Liver Transplant Recipients have no acute rejection episodes within 3 months prior to the enrollment and are clinically stable Liver Transplant Recipients have been treated with twice-daily regimen of tacrolimus(TAC) plus everolimus(EVR) and TAC and EVR trough levels have stayed within targeted ranges for at least 6 weeks prior to enrollment Provide written informed consent prior to inclusion. Liver transplant recipients who are 18-65 years of age of a primary liver transplant Allograft functioning at an acceptable level as defined by the AST, ALT, Total Bilirubin levels =3 times ULN prior to enrollment. Abbreviated MDRD eGFR = 30 mL/min/1.73m2.", "candidate_expression": "((18-65 years) AND (= 30 mL/min/1.73m2) AND (=3 times ULN) AND (ALT) AND (AST) AND (Allograft functioning) AND (EVR trough levels) AND (Liver Transplant Recipients) AND (Liver transplant recipients) AND (MDRD eGFR) AND (TAC trough levels) AND (Total Bilirubin) AND (acceptable level) AND (acute) AND (age) AND (clinically stable) AND (enrollment) AND (everolimus(EVR)) AND (for at least 6 weeks prior to enrollment) AND (for at least 6+1 months prior to enrollment) AND (inclusion) AND (liver transplantations) AND (no) AND (primary liver transplant) AND (prior to enrollment) AND (prior to inclusion) AND (rejection episodes) AND (tacrolimus(TAC)) AND (the enrollment) AND (twice-daily) AND (within 3 months prior to the enrollment) AND (within targeted ranges) AND (written informed consent))"}
{"candidate_id": "LLM03168", "doc_id": "NCT02092467_exc", "case_bucket": "or", "source_criterion": "Current or recent infection Clinically significant laboratory abnormalities Pregnancy", "candidate_expression": "((Clinically significant) AND (Current) AND (Pregnancy) AND (infection) AND (laboratory) AND (laboratory abnormalities) AND (recent))"}
{"candidate_id": "LLM03169", "doc_id": "NCT02745704_exc", "case_bucket": "or", "source_criterion": "Patients with liver cirrhosis, Hepatocellular Carcinoma or other malignancies. Patients with other factors causing liver diseases. Pregnant and lactating women. Patients with concomitant HIV infection or congenital immune deficiency diseases. Patients with diabetes, autoimmune diseases. Patients with important organ dysfunctions. Patients with serious complications (e.g., infection, hepatic encephalopathy, hepatorenal syndrome, gastrointestinal bleeding.) Patients who receive antineoplastic or immunomodulatory therapy in the past 12 months. Patients who can't come back to clinic for follow-up on schedule.", "candidate_expression": "((Patients who can't come back to clinic for follow-up on schedule) AND (Pregnant and lactating women) AND (antineoplastic therapy) AND (complications) AND (concomitant) AND (immunomodulatory therapy) AND (organ dysfunctions) AND (past 12 months) AND (serious) AND ((autoimmune diseases) OR (diabetes)) AND ((gastrointestinal bleeding) OR (hepatic encephalopathy) OR (hepatorenal syndrome) OR (infection)) AND ((Hepatocellular Carcinoma) OR (liver cirrhosis) OR (malignancies)) AND ((HIV infection) OR (congenital immune deficiency diseases.)))"}
{"candidate_id": "LLM03170", "doc_id": "NCT02083991_inc", "case_bucket": "or", "source_criterion": "First or second single kidney (cadaveric or living donors) transplant recipients. Considered for a standard immunosuppressive protocol. Must be capable of giving written informed connect for participation in the study for 24 months.", "candidate_expression": "((Considered for) AND (Must be capable of giving written informed connect for participation in the study for 24 months.) AND (standard immunosuppressive protocol) AND ((First single kidney transplant) OR (transplant second single kidney)) AND ((cadaveric donors) OR (living donors)))"}
{"candidate_id": "LLM03171", "doc_id": "NCT02877485_exc", "case_bucket": "or", "source_criterion": "Intranasal steroid use within the last three months Current systemic steroid use Prior septal surgery Individuals who are pregnant or actively breastfeeding", "candidate_expression": "((Intranasal steroid use within the last three months) AND (breastfeeding actively) AND (pregnant) AND (septal surgery Prior) AND (steroid Intranasal) AND (steroid systemic) AND (systemic steroid use Current))"}
{"candidate_id": "LLM03172", "doc_id": "NCT02573597_exc", "case_bucket": "or", "source_criterion": "<37 weeks gestation, H/o Cesarean Section, Multiple Gestation, Pre-eclampsia, Narcotics within 3 hours prior to labor epidural placement, Chronic Pain (as defined by chronic opiate consumption), Women who are participating in another study that will impact protocol", "candidate_expression": "((Cesarean Section) AND (Chronic Pain) AND (Multiple Gestation) AND (Narcotics within 3 hours prior to labor epidural placement) AND (Pre-eclampsia) AND (Women who are participating in another study that will impact protocol) AND (gestation <37 weeks) AND (labor epidural placement) AND (opiate chronic))"}
{"candidate_id": "LLM03173", "doc_id": "NCT00317148_inc", "case_bucket": "other", "source_criterion": "Healthy postmenopausal women with 50 or more moderate to severe hot flushes. Women between 40 to 70 years of age.", "candidate_expression": "((Healthy) AND (Women) AND (age between 40 to 70 years) AND (moderate to severe hot flushes) AND (postmenopausal) AND (women 50 or more))"}
{"candidate_id": "LLM03174", "doc_id": "NCT03360214_inc", "case_bucket": "or", "source_criterion": "Subjects must be female Subjects must be 18 years or older Subjects must be undergoing unilateral or bilateral mastectomy with tissue expander reconstruction", "candidate_expression": "((18 years or older) AND (bilateral) AND (female) AND (mastectomy) AND (older) AND (tissue expander reconstruction) AND (undergoing) AND (unilateral))"}
{"candidate_id": "LLM03175", "doc_id": "NCT03347513_exc", "case_bucket": "or", "source_criterion": "Severe Iron deficiency anemia (hemoglobin < 8.0 g/dL). Parasitic worm infection e.g. schistosomiasis, and hook worm by stool analysis. Any cases giving clinical symptoms of gastritis e.g. nausea, vomiting, dull aching pain or soreness in the epigastrium. Cases with history of gastric ulcer diagnosed by upper endoscopy. Cases complaining of hematemesis.", "candidate_expression": "((Iron deficiency anemia Severe) AND (Parasitic worm infection) AND (dull aching pain) AND (gastric ulcer history) AND (gastritis clinical symptoms) AND (hematemesis) AND (hemoglobin < 8.0 g/dL) AND (hook worm) AND (nausea) AND (schistosomiasis) AND (soreness in the epigastrium) AND (stool analysis) AND (upper endoscopy) AND (vomiting))"}
```
