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
{"candidate_id": "LLM07801", "doc_id": "NCT00480129_exc", "case_bucket": "other", "source_criterion": "Ongoing allergen immunotherapy upper respiratory tract infection Pregnancy Clinical history of lactose-intolerance or allergies to cow-milk", "candidate_expression": "((Pregnancy) AND (allergen immunotherapy) AND (allergies to cow-milk) AND (lactose-intolerance) AND (upper respiratory tract infection))"}
{"candidate_id": "LLM07802", "doc_id": "NCT03350815_inc", "case_bucket": "or", "source_criterion": "Understand and communicate with the investigator, comply with the requirements of the study and give a written, signed and dated informed consent Male or non-pregnant, non-lactating female patients at least 18 years of age Diagnosis of moderate to severe Ankylosing Spondylitis (AS) with prior documented radiologic evidence fulfilling the Modified New York criteria for AS Active AS assessed by total Bath Ankylosing Spondylitis Disease Activity index (BASDAI) = 4 (0-10) at baseline Spinal pain as measured by BASDAI question #2 = 4 cm (0-10 cm) at baseline Total back pain as measured by visual analog scale (VAS) = 40 mm (0-100 mm) at baseline Patients should have been on non-steroidal anti-inflammatory drugs (NSAIDs) at the maximum tolerated dose for at least 4 weeks prior to their Baseline Visit, with an inadequate response or for less than 4 weeks if withdrawn for intolerance, toxicity or contraindications Stable dose of NSAIDs including Cyclooxygenase-1 (COX-1) or Cyclooxygenase-2 (COX-2) inhibitors for at least 2 weeks before their Baseline Visit Patients who have been on a tumor necrosis factor alpha (TNFa) inhibitor (not more than one) must have experienced an inadequate response to previous or current treatment given at an approved dose for at least 3 months prior to baseline or had been intolerant upon administration of an anti-TNFa agent Total ankylosis of the spine Use of other investigational drugs within 5 half-lives of enrollment, or within 4 weeks before the Baseline Visit, whichever is longer. History of hypersensitivity to any of the study drugs or its excipients or to drugs of similar chemical classes. Chest x-ray, computerized tomography (CT) scan, or chest magnetic resonance imaging (MRI) with evidence of ongoing infectious or malignant process, obtained within 3 months prior to screening and evaluated by a qualified physician. Previous exposure to secukinumab or any other biologic drug directly targeting Interleukin-17 (IL-17), Interleukin-12/23 (IL-12/23), or the IL-17 receptor, or any other biologic immunomodulating agent, except those targeting TNFa Patients who have taken more than one anti-TNFa agent Any intramuscular or intravenous corticosteroid injection within 2 weeks before baseline Any therapy by intra-articular injections (e.g. corticosteroid) within 4 weeks before baseline Previous treatment with any cell-depleting therapies Patients taking high potency opioid analgesics (e.g., methadone, hydromorphone, morphine)", "candidate_expression": "((= 4) AND (= 4 cm) AND (= 40 mm) AND (AS) AND (Active) AND (Ankylosing Spondylitis (AS)) AND (BASDAI question #2) AND (Male or non-pregnant, non-lactating female patients at least 18 years of age) AND (Modified New York criteria for AS) AND (Previous) AND (Spinal pain) AND (TNFa) AND (Total ankylosis of the spine) AND (Total back pain) AND (Understand and communicate with the investigator, comply with the requirements of the study and give a written, signed and dated informed consent) AND (Use of other investigational drugs within 5 half-lives of enrollment, or within 4 weeks before the Baseline Visit, whichever is longer.) AND (anti-TNFa agent) AND (approved dose) AND (at baseline) AND (baseline) AND (cell-depleting therapies) AND (corticosteroid) AND (corticosteroid injection) AND (except) AND (excipients) AND (for at least 2 weeks before their Baseline Visit) AND (for at least 3 months prior to baseline) AND (for at least 4 weeks prior to their Baseline Visit) AND (for less than 4 weeks) AND (fulfilling) AND (high potency opioid analgesics) AND (hypersensitivity) AND (inadequate response) AND (intra-articular injections) AND (maximum tolerated dose) AND (more than one) AND (non-steroidal anti-inflammatory drugs (NSAIDs)) AND (not more than one) AND (ongoing) AND (other) AND (prior) AND (radiologic) AND (radiologic evidence) AND (targeting) AND (their Baseline Visit) AND (total Bath Ankylosing Spondylitis Disease Activity index (BASDAI)) AND (treatment) AND (tumor necrosis factor alpha (TNFa) inhibitor) AND (visual analog scale (VAS)) AND (within 2 weeks before baseline) AND (within 3 months prior to screening) AND (within 4 weeks before baseline) AND ((moderate) OR (severe)) AND ((contraindications) OR (withdrawn for intolerance) OR (withdrawn for toxicity)) AND ((Cyclooxygenase-2 (COX-2) inhibitors) OR (NSAIDs) OR (inhibitors Cyclooxygenase-1 (COX-1))) AND ((inadequate response) OR (intolerant)) AND ((current) OR (previous)) AND ((drugs of similar chemical classes) OR (study drugs)) AND ((Chest x-ray) OR (chest magnetic resonance imaging (MRI)) OR (computerized tomography (CT) scan)) AND ((infectious) OR (malignant process)) AND ((biologic drug) OR (secukinumab)) AND ((IL-17 receptor) OR (Interleukin-12/23 (IL-12/23)) OR (Interleukin-17 (IL-17)) OR (biologic immunomodulating agent)) AND ((intramuscular) OR (intravenous)) AND ((hydromorphone) OR (methadone) OR (morphine)))"}
{"candidate_id": "LLM07803", "doc_id": "NCT02904785_inc", "case_bucket": "or", "source_criterion": "Clinical and radiologic diagnosis of primary knee osteoarthritis (Kellgren & Lawrence I, II or III); Capability to understand the Informed Consent Form; Chronic pain for at least 3 months prior to inclusion, measured by VAS. (VAS 4 or above); Absence of skin injures, infections or tumor in the target knee; Availability to comply with the visits.", "candidate_expression": "((4 or above) AND (Absence) AND (Availability to comply with the visits) AND (Capability to understand the Informed Consent Form;) AND (Chronic pain) AND (Clinical diagnosis) AND (I, II or III) AND (Kellgren & Lawrence) AND (VAS) AND (at least 3 months prior) AND (inclusion) AND (infections) AND (measured by VAS) AND (primary knee osteoarthritis) AND (radiologic diagnosis) AND (skin injures) AND (target knee) AND (tumor))"}
{"candidate_id": "LLM07804", "doc_id": "NCT02565277_inc", "case_bucket": "other", "source_criterion": "Subjects who the investigator believes can and will comply with the requirements of the protocol (i.e. return for follow-up visits, and able to converse with study personnel) Age 18 years or older Undergoing major cardiac surgery using cardiopulmonary bypass", "candidate_expression": "((18 years or older) AND (Age) AND (Subjects who the investigator believes can and will comply with the requirements of the protocol (i.e. return for follow-up visits, and able to converse with study personnel) AND (cardiopulmonary bypass) AND (major cardiac surgery))"}
{"candidate_id": "LLM07805", "doc_id": "NCT03390933_exc", "case_bucket": "or", "source_criterion": "on hemodialysis for less than 3 months comorbid psychotic, bipolar, substance use dependence, Alzheimer's or dementia", "candidate_expression": "((Alzheimer's) AND (bipolar) AND (dementia) AND (hemodialysis for less than 3 months) AND (psychotic) AND (substance use dependence))"}
{"candidate_id": "LLM07806", "doc_id": "NCT02950558_inc", "case_bucket": "other", "source_criterion": "Referred for surgery for open reduction and internal fixation for ankle fracture", "candidate_expression": "((ankle fracture) AND (open reduction and internal fixation) AND (surgery))"}
{"candidate_id": "LLM07807", "doc_id": "NCT03113253_inc", "case_bucket": "or", "source_criterion": "Subjects undergoing burn excision surgery for standard of care purposes Male or female >= 18 years of age Subject or subject's medical decision maker agrees to participate in this study and provides informed consent", "candidate_expression": "((Subject or subject's medical decision maker agrees to participate in this study and provides informed consent) AND (age >= 18 years) AND (burn excision surgery undergoing) AND ((Male) OR (female)))"}
{"candidate_id": "LLM07808", "doc_id": "NCT01352598_inc", "case_bucket": "or", "source_criterion": "Patient age >= 18 years Zubrod performance status of 0-3 T1-3 N0 M0 adenocarcinoma of the prostate Prostate volume = 100 cc Signed study-specific consent form Extension of local tumor to involve adjacent organs other than seminal vesicles (T4) Prostate volume > 100 cc Nodal involvement Metastatic disease Prior pelvic radiotherapy except as part of combination therapy for prostate cancer History of scleroderma Patients with psychiatric or addictive disorder that would preclude obtaining informed consent", "candidate_expression": "((0) AND (0-3) AND (1-3) AND (= 100 cc) AND (> 100 cc) AND (>= 18 years) AND (Extension of local tumor) AND (History) AND (M) AND (Metastatic disease) AND (N) AND (Nodal involvement) AND (Patient age) AND (Prior) AND (Prostate volume) AND (Signed study-specific consent form) AND (T) AND (Zubrod performance status) AND (addictive disorder) AND (adenocarcinoma) AND (adjacent organs) AND (combination therapy) AND (except) AND (other than) AND (pelvic) AND (prostate) AND (prostate cancer) AND (psychiatric disorder) AND (radiotherapy) AND (scleroderma) AND (seminal vesicles))"}
{"candidate_id": "LLM07809", "doc_id": "NCT03228654_exc", "case_bucket": "or", "source_criterion": "Suspected or known gynecological malignancy. uterine size >12 weeks. Endometriosis Presence of adnexal mass. cervix flushed with the vagina. presence of significant scarring in the pelvic area from previous surgery.", "candidate_expression": "((>12 weeks) AND (Endometriosis) AND (Suspected) AND (adnexal mass) AND (cervix flushed with the vagina) AND (from previous surgery) AND (gynecological malignancy) AND (known) AND (pelvic area) AND (previous) AND (significant scarring) AND (surgery) AND (uterine size))"}
{"candidate_id": "LLM07810", "doc_id": "NCT03416413_exc", "case_bucket": "or", "source_criterion": "Current DVT Recurrent varicose veins Arterial disease (ABPI<0.8) Vein diameter < 3mm Preference for one of the treatment options Patient who are unwilling to participate Inability or unwillingness to complete questionnaires Inability to attend follow-up appointments Patient currently included in a study of varicose vein treatment", "candidate_expression": "((< 3mm) AND (<0.8) AND (ABPI) AND (Arterial disease) AND (Current) AND (DVT) AND (Inability to attend follow-up appointments) AND (Inability to complete questionnaires) AND (Patient currently included in a study of varicose vein treatment) AND (Recurrent) AND (Vein diameter) AND (unwilling to participate) AND (unwillingness to complete questionnaires) AND (varicose veins))"}
{"candidate_id": "LLM07811", "doc_id": "NCT01088750_inc", "case_bucket": "other", "source_criterion": "Stage IA or IIA disease Not specified No prior therapy", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07812", "doc_id": "NCT02222272_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07813", "doc_id": "NCT03282006_inc", "case_bucket": "or", "source_criterion": "E.coli in blood culture AND identical isolate in urine sample (>= 1.000 CFU) OR relevant clinical signs of UTI", "candidate_expression": "((CFU >= 1.000) AND (UTI clinical signs) AND (blood culture E.coli) AND (urine sample identical isolate))"}
{"candidate_id": "LLM07814", "doc_id": "NCT02964715_exc", "case_bucket": "or", "source_criterion": "eGFR <45 ml/min structural and functional urogenital abnormalities, that predispose for urogenital infections Investigational product use in the last 6 months SGLT2 inhibitor, TZD, DPP4 inhibitor and GLP1 RA use within the past 6 months DKA(Diabetic Ketoacidosis) or HHS(Hyperosmoloar Hyperglycaemic Syndrome) within the last 6 months Pregnancy Presence of major contraindications to magnetic resonance imaging (cardiac pacemakers, claustrophobia, foreign bodies and implanted medical devices with ferromagnetic properties). Liver cirrhosis Type 1 diabetes Severe uncorrected insulin insufficiency Significant alcohol intake HIV infection Use of Traditional Chinese Medication or alternative therapies Coexisting causes of chronic liver disease - chronic viral hepatitis(B & C), autoimmune liver disease, hemochromatosis, Wilson's etc. Use of medications associated with steatosis eg. Methotrexate, anticonvulsants, antiretroviral therapy etc. h/o stroke Steroid therapy Endogenous Cushing's Familial hypertriglyceridemia", "candidate_expression": "((Cushing's Endogenous) AND (DKA) AND (DPP4 inhibitor) AND (Diabetic Ketoacidosis) AND (Familial hypertriglyceridemi) AND (GLP1 RA) AND (HHS) AND (HIV infection) AND (Hyperosmoloar Hyperglycaemic Syndrome) AND (Investigational product use in the last 6 months) AND (Liver cirrhosis) AND (Methotrexate) AND (Pregnancy) AND (SGLT2 inhibitor) AND (Steroid therapy) AND (TZD) AND (Traditional Chinese Medication) AND (Type 1 diabetes Severe uncorrected) AND (Wilson's) AND (alcohol intake Significant) AND (alternative therapies) AND (anticonvulsants) AND (antiretroviral therapy) AND (autoimmune liver disease) AND (cardiac pacemakers) AND (chronic liver disease) AND (chronic viral hepatitis B) AND (chronic viral hepatitis C) AND (claustrophobia) AND (eGFR <45 ml/min structural functional) AND (foreign bodies) AND (hemochromatosis) AND (implanted medical devices ferromagnetic properties) AND (insulin insufficiency) AND (magnetic resonance imaging) AND (major contraindications) AND (medications) AND (predispose for urogenital infections) AND (steatosis) AND (stroke) AND (urogenital abnormalities) AND (urogenital infections))"}
{"candidate_id": "LLM07815", "doc_id": "NCT02321839_inc", "case_bucket": "or", "source_criterion": "Signed informed consent form Male or female of aged 50 years or older Typical AMD and PCV patients BCVA of 24 letters or over", "candidate_expression": "((24 letters or over) AND (50 years or older) AND (AMD) AND (BCVA) AND (Male) AND (PCV patients) AND (Signed informed consent form) AND (aged) AND (female))"}
{"candidate_id": "LLM07816", "doc_id": "NCT02303171_exc", "case_bucket": "other", "source_criterion": "Women with systemic lupus erythematosus (SLE) Women with active thromboembolic disorders Women with history of previous thromboembolic disorders", "candidate_expression": "((Women) AND (systemic lupus erythematosus (SLE)) AND (thromboembolic disorders active) AND (thromboembolic disorders history previous))"}
{"candidate_id": "LLM07817", "doc_id": "NCT02432404_inc", "case_bucket": "or", "source_criterion": "=18-40 year old women BV+ by Amsel criteria and Nugent score OR history of BV in the prior 6 months Willing to use the NuvaRing as directed Not intending or wishing to become pregnant over the course of the study Capable of providing written informed consent", "candidate_expression": "((Amsel criteria) AND (BV) AND (BV in the prior 6 months) AND (Capable of providing written informed consent) AND (Not intending or wishing to become pregnant over the course of the study) AND (Nugent score) AND (NuvaRing) AND (Willing to use) AND (old 18-40 year) AND (women) AND (written informed consent))"}
{"candidate_id": "LLM07818", "doc_id": "NCT03400735_exc", "case_bucket": "or", "source_criterion": "Pregnancy or breastfeeding Allergy against to penicillin or cephalosporins Renal impairment Active hepatic disease Antibiotic use except study drugs Immunosuppressive therapy before 6 months of study initiation Use of probenecid like drugs", "candidate_expression": "((Active) AND (Allergy) AND (Antibiotic) AND (Immunosuppressive therapy) AND (Renal impairment) AND (before 6 months of study initiation) AND (except) AND (hepatic disease) AND (probenecid) AND (probenecid like) AND (probenecid like drugs) AND (study drugs) AND (study initiation) AND ((Pregnancy) OR (breastfeeding)) AND ((cephalosporins) OR (penicillin)))"}
{"candidate_id": "LLM07819", "doc_id": "NCT02704754_exc", "case_bucket": "or", "source_criterion": "Psychiatric disorders other than insomnia, PTSD and specific phobias; including bipolar and psychotic disorders and meeting criteria for DSM-5 moderate alcohol or drug use disorders within the past year. Diagnosis of a sleep disorder other than insomnia including PSG findings of apnea/hypopnea or periodic limb movement indices > 10/hour; Medical conditions that require consistent use of medication or compromise sleep; History of moderate to severe traumatic brain injury or mild traumatic brain injury with ongoing post-concussive symptoms; Suicidal ideation with intent to act or with specific plan and intent in the past 6 months (Type 4 - 5 ideation on the Columbia Suicide Severity Rating Scale) or a concerning history of prior suicidal behavior. Caffeine use exceeding 5 cups of coffee per day or its equivalent; Habitual bedtimes after 3 AM, habitual rise times after 10 AM, or habitual napping > 1hour/day; Pregnancy or breastfeeding, or expecting to conceive while in study; Positive urine toxicology.", "candidate_expression": "((> 10/hour) AND (Caffeine) AND (Columbia Suicide Severity Rating Scale) AND (DSM-5) AND (PSG) AND (PTSD) AND (Positive) AND (Pregnancy or breastfeeding, or expecting to conceive while in study) AND (Psychiatric disorders) AND (Suicidal ideation) AND (Type 4 ideation) AND (Type 5 ideation) AND (alcohol use disorders) AND (apnea) AND (bipolar) AND (drug use disorders) AND (hypopnea) AND (insomnia) AND (mild) AND (moderate) AND (other) AND (past 6 months) AND (past year) AND (periodic limb movement indices) AND (phobias) AND (post-concussive symptoms) AND (psychotic disorders) AND (severe) AND (sleep disorder) AND (suicidal behavior.) AND (traumatic brain injury) AND (urine toxicology))"}
{"candidate_id": "LLM07820", "doc_id": "NCT00609531_exc", "case_bucket": "or", "source_criterion": "Age less than 10 years or greater than 55 years, at time of consent Estimated IQ < 70 Uncontrolled epilepsy (seizure within 6 months prior to consent) 4. Presence of medical conditions that might interfere with participation, or where participation would be contraindicated History of neurological injury: head trauma, poorly-controlled seizure disorder (seizure within the preceding six months), stroke, prior neurosurgery, or under the care of a neurologist or neurosurgeon as determined by interview History of claustrophobia Implanted or irremovable metal in the body (including certain tattoos and permanent make-up) Current pregnancy (as verified by testing prior to both initial dose administration of citalopram or placebo and prior to magnetic resonance imaging) due to the risk that may be associated with SSRI treatment and magnetic resonance imaging on fetal health Medical contraindications to SSRI therapy as determined by history (including induction of mania or hypomania during SSRI therapy, or known drug allergy) Concomitant medication that would interfere with study participation Prior history of citalopram treatment failure at appropriate doses and duration Prior history of treatment failure to two previous SSRI trials at appropriate doses and duration Ongoing need for psychoactive medication other than study medication [excepting stable doses (greater than three months duration) of anticonvulsant medication for seizure disorder, or diphenhydramine (Benadryl®)for sleep]", "candidate_expression": "((Age at time of consent less than 10 years greater than 55 years) AND (Estimated IQ < 70) AND (Implanted metal in the body) AND (SSRI therapy) AND (Uncontrolled epilepsy) AND (citalopram) AND (claustrophobia History) AND (consent) AND (contraindications to SSRI therapy history) AND (diphenhydramine) AND (drug allergy) AND (head trauma) AND (history) AND (hypomania) AND (irremovable metal in the body) AND (mania) AND (neurological injury History) AND (neurosurgery prior) AND (pregnancy Current) AND (psychoactive medication) AND (seizure disorder) AND (seizure disorder poorly-controlled) AND (seizure within 6 months prior to consent) AND (seizure within the preceding six months) AND (stable doses greater than three months) AND (stroke) AND (treatment Prior failure) AND (under the care of a neurologist) AND (under the care of a neurosurgeon) AND NOT (study medication) AND NOT (anticonvulsant medication))"}
{"candidate_id": "LLM07821", "doc_id": "NCT02650388_inc", "case_bucket": "or", "source_criterion": "Age = 75 years, Severe, symptomatic aortic stenosis, High risk for cardiac surgery (STS and logistic Euroscore ), According multidisciplinary (heart) team decision TAVI is preferable, Willing to participate", "candidate_expression": "((Age = 75 years) AND (Willing to participate) AND (aortic stenosis Severe symptomatic) AND (cardiac surgery High risk STS logistic Euroscore))"}
{"candidate_id": "LLM07822", "doc_id": "NCT02837783_inc", "case_bucket": "other", "source_criterion": "Patient meets protocol criteria for diagnosis of IBS-C, abdominal pain, abdominal bloating and abdominal girth", "candidate_expression": "((IBS-C) AND (abdominal bloating) AND (abdominal girth) AND (abdominal pain) AND (protocol criteria))"}
{"candidate_id": "LLM07823", "doc_id": "NCT03347513_inc", "case_bucket": "other", "source_criterion": "Diagnosed Iron deficiency anemia. H-pylori positive cases. Second trimester pregnancy.", "candidate_expression": "((H-pylori positive) AND (Iron deficiency anemia) AND (Second trimester) AND (pregnancy))"}
{"candidate_id": "LLM07824", "doc_id": "NCT03064568_inc", "case_bucket": "other", "source_criterion": "Female age 20-50 y/o who plan to undergo abdominal myomectomy for symptomatic myomatous uterus", "candidate_expression": "((20-50 y/o) AND (Female) AND (abdominal myomectomy) AND (age) AND (myomatous uterus) AND (plan to undergo) AND (symptomatic))"}
{"candidate_id": "LLM07825", "doc_id": "NCT02109081_exc", "case_bucket": "or", "source_criterion": "1) preoperative diagnosis of delirium or dementia; 2) MMSE score of = 20 out of 30 on preoperative testing (more than mild cognitive impairment) or delirium on preoperative CAM testing; 3) language barriers that would preclude testing; 4) preoperative steroid use within 3 days of surgery; or 5) anticipation of postoperative intubation.", "candidate_expression": "((CAM testing preoperative) AND (MMSE score = 20 out of 30) AND (cognitive impairment more than mild) AND (delirium) AND (intubation anticipation postoperative) AND (language barriers) AND (steroid preoperative within 3 days of surgery) AND (surgery) AND ((delirium) OR (dementia)))"}
```
