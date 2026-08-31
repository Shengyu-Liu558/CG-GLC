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
{"candidate_id": "LLM06851", "doc_id": "NCT02816164_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed primary breast cancer Planned to start docetaxel component of FEC-D or AC-D, or first cycle of; dose-dense AC-T, TC, FEC-D or TAC chemotherapy =19 years of age Able to provide verbal consent", "candidate_expression": "((=19 years) AND (Able to provide verbal consent) AND (Histologically) AND (Histologically confirmed) AND (Planned to start) AND (age) AND (primary breast cancer) AND ((FEC-D) OR (TAC chemotherapy) OR (TC) OR (dose-dense AC-T)) AND ((docetaxel) OR (first cycle of)) AND ((AC-D) OR (FEC-D)))"}
{"candidate_id": "LLM06852", "doc_id": "NCT02570347_exc", "case_bucket": "or", "source_criterion": "Upper limb bites Multiple (> 1) bites Wound manipulation Extensive local necrosis or blebs Seriously-ill patients with hypotension/capillary leak/life threatening bleeding. Suspected cobra bite, OR Pregnant/breast-feeding women", "candidate_expression": "((> 1) AND (Extensive local blebs) AND (Extensive local necrosis) AND (Multiple) AND (Pregnant) AND (Seriously-ill) AND (Suspected) AND (Upper limb) AND (Wound manipulation) AND (bites) AND (bleeding) AND (breast-feeding) AND (capillary leak) AND (cobra bite) AND (hypotension) AND (life threatening) AND (women))"}
{"candidate_id": "LLM06853", "doc_id": "NCT02558504_exc", "case_bucket": "or", "source_criterion": "Aged under 18, Lack of informed consent signed, Radiofrequency treatment history, on going neoplastic history with a short prognosis, Concomitant participation in another clinical study Contraindication to general anesthesia, Patient with an esophageal location of scleroderma Presence of a cardiac pacemaker or stimulator Pregnant women or likely to be in the absence of effective contraception, Esophageal stenosis preventing the passage of an endoscope, Histology other than glandular neoplasia, History of or current history of esophageal cancer invading the submucosal layer of the esophagus or more, Surgical treatment history (except anti-reflux treatment) or esophageal radiotherapy, previous esophageal treatment by another method ablation: photodynamic therapy, argon plasma coagulation, laser, .... Esophageal varices observed in endoscopy, Coagulopathy or taking anticoagulants responsible an INR> 1.3 or a platelet count <75,000 per microL, Life expectancy of less than 3 years, due to intercurrent disease, especially neoplastic, Liver cirrhosis (Child-Pugh all stages) Respiratory failure: Renal failure (Cl Cr < 60 mL /min /1,73m), Heart attack within the last six months or progressive coronary artery disease, Severe distal arteriopathie > stage II of Leriche and Fontaine", "candidate_expression": "((Aged under 18) AND (Child-Pugh all stages) AND (Cl Cr < 60 mL /min /1,73m) AND (Coagulopathy) AND (Contraindication) AND (Esophageal stenosis) AND (Esophageal varices) AND (Heart attack within the last six months) AND (Histology) AND (History current) AND (INR > 1.3) AND (Life expectancy less than 3 years) AND (Liver cirrhosis) AND (Pregnant) AND (Pregnant likely to be in the absence of effective contraception) AND (Radiofrequency treatment history) AND (Renal failure) AND (Respiratory failure) AND (Surgical treatment history) AND (ablation another method) AND (anticoagulants) AND (argon plasma coagulation) AND (cardiac pacemaker) AND (cardiac stimulator) AND (distal arteriopathie Severe) AND (endoscope) AND (endoscopy) AND (esophageal cancer invading the submucosal layer of the esophagus) AND (esophageal radiotherapy) AND (esophageal treatment previous) AND (general anesthesia) AND (glandular neoplasia other than) AND (intercurrent disease) AND (laser) AND (neoplastic) AND (neoplastic on going history) AND (participation in another clinical study Concomitant) AND (passage of an endoscope preventing the) AND (photodynamic therapy) AND (platelet count <75,000 per microL) AND (prognosis short) AND (progressive coronary artery disease) AND (scleroderma esophageal location) AND (stage of Leriche and Fontaine > II) AND (women) AND NOT (anti-reflux treatment) AND NOT (informed consent signed))"}
{"candidate_id": "LLM06854", "doc_id": "NCT02822001_inc", "case_bucket": "other", "source_criterion": "Patients undergoing surgery with general anesthesia, Patients weighing = 80 pounds who are not -intubated prior to surgery, Patients who are able to give informed consent.", "candidate_expression": "((Patients who are able to give informed consent) AND (general anesthesia) AND (surgery) AND (surgery undergoing general anesthesia) AND (weighing = 80 pounds) AND NOT (intubated prior to surgery))"}
{"candidate_id": "LLM06855", "doc_id": "NCT02926235_exc", "case_bucket": "other", "source_criterion": "All patients who were wheelchair bound preoperatively All patients who cannot participate in an outpatient physical therapy program for 3 days per week after surgery", "candidate_expression": "((outpatient) AND (wheelchair bound preoperatively) AND NOT (physical therapy for 3 days per week after surgery))"}
{"candidate_id": "LLM06856", "doc_id": "NCT02314559_exc", "case_bucket": "other", "source_criterion": "Dementia. Gastroscopy planned at the same time. Allergies to propofol All cases were a 'full stomach' is suspected (gastric banding) Pregnancy", "candidate_expression": "((Allergies) AND (Dementia) AND (Gastroscopy) AND (Pregnancy) AND (at the same time) AND (planned) AND (propofol))"}
{"candidate_id": "LLM06857", "doc_id": "NCT03472846_exc", "case_bucket": "or", "source_criterion": "Diabetes mellitus type 1 renal insufficiency III-V ° Cirrhosis hepatis (Child B or higher) Chronic alcohol abuse rheumatic disease (RA, SpA, SLE) Malignancies (<5 years) Eating Disorder (anorexia nervosa, bulimia) bone-specific pretreatment (DMAB, TPTD, strontium ranelate, SERMs) Bisphosphonate treatment is allowed", "candidate_expression": "((<5 years) AND (B or higher) AND (Child) AND (Child B or higher) AND (Chronic) AND (Cirrhosis hepatis) AND (DMAB) AND (Diabetes mellitus type 1) AND (Eating Disorder) AND (III-V °) AND (Malignancies) AND (RA) AND (SERMs) AND (SLE) AND (SpA) AND (TPTD) AND (alcohol abuse) AND (anorexia nervosa) AND (bone-specific pretreatment) AND (bulimia) AND (renal insufficiency) AND (rheumatic disease) AND (strontium ranelate))"}
{"candidate_id": "LLM06858", "doc_id": "NCT02609048_inc", "case_bucket": "or", "source_criterion": "1. Must have given written informed consent (signed and dated) and any authorizations required by local law 2. 18 to 75 years old (inclusive) 3. Male or female with a diagnosis of PBC, by at least two of the following criteria: History of AP above ULN for at least six months Positive Anti-Mitochondrial Antibodies (AMA) titers (>1/40 on immunofluorescence or M2 positive by enzyme linked immunosorbent assay (ELISA) or positive PBC-specific antinuclear antibodies Documented liver biopsy result consistent with PBC 4. On a stable and recommended dose of UDCA for the past twelve months 5. AP ≥ 1.67 × ULN 6. For females of reproductive potential, use of at least one barrier contraceptive and a second effective birth control method during the study and for at least two weeks after the last dose. For male subjects, use of appropriate contraception (e.g., condoms), so their female partners of reproductive potential do not become pregnant during the study and for at least two weeks after the last dose", "candidate_expression": "((AP above ULN for at least six months) AND (AP ≥ 1.67 × ULN) AND (For male subjects, use of appropriate contraception (e.g., condoms), so their female partners of reproductive potential do not become pregnant during the study and for at least two weeks after the last dose) AND (Male) AND (Must have given written informed consent (signed and dated) and any authorizations required by local law) AND (PBC) AND (PBC-specific antinuclear antibodies positive) AND (Positive Anti-Mitochondrial Antibodies (AMA) titers) AND (UDCA stable dose recommended dose for the past twelve months) AND (appropriate) AND (barrier contraceptive at least one) AND (birth control method second effective during the study for at least two weeks after the last dose) AND (condoms) AND (contraception appropriate) AND (effective) AND (enzyme linked immunosorbent assay (ELISA) M2 positive) AND (female) AND (females) AND (following criteria at least two) AND (immunofluorescence >1/40) AND (liver biopsy) AND (male) AND (reproductive potential) AND (years old 18 to 75 years old (inclusive)) AND NOT (pregnant during the study for at least two weeks after the last dose))"}
{"candidate_id": "LLM06859", "doc_id": "NCT01567605_exc", "case_bucket": "or", "source_criterion": "cauda equina or conus lesion currently use ventilator colostomy, or do not perform regular bowel care for any reason any skin breakdown (pressure sores) do not speak English are under 19 years old are pregnant or think you might be pregnant medical/psychiatric condition or substance abuse that is likely to affect your ability to complete this study currently using medications containing lidocaine allergy to lidocaine", "candidate_expression": "((allergy) AND (colostomy) AND (lesion cauda equina conus) AND (lidocaine) AND (medical condition) AND (medications containing lidocaine currently) AND (old under 19 years) AND (pregnant) AND (pregnant think you might be) AND (pressure sores) AND (psychiatric condition) AND (skin breakdown) AND (substance abuse) AND (ventilator currently) AND NOT (speak English) AND NOT (regular bowel care))"}
{"candidate_id": "LLM06860", "doc_id": "NCT03104816_inc", "case_bucket": "or", "source_criterion": "ASA I-III patients scheduled for elective one or two level minimally invasive lumbar fusions", "candidate_expression": "((ASA I-III) AND (minimally invasive lumbar fusions scheduled elective) AND ((one level) OR (two level)))"}
{"candidate_id": "LLM06861", "doc_id": "NCT02443844_exc", "case_bucket": "other", "source_criterion": "Patients who have previous prostate surgery Patients who have muscle invasive bladder cancer", "candidate_expression": "((bladder cancer) AND (muscle invasive) AND (previous) AND (prostate surgery))"}
{"candidate_id": "LLM06862", "doc_id": "NCT02924870_inc", "case_bucket": "or", "source_criterion": "subjects older than 35 years diagnosis of moderate to very severe COPD (FEV1 <80% predicted), according to the GesEPOC criteria, established at least 3 months current or former smoker with an accumulated consumption >10 packs x year hospital admission for COPD exacerbation", "candidate_expression": "((<80% predicted) AND (>10 packs x year) AND (COPD) AND (COPD exacerbation) AND (FEV1) AND (GesEPOC criteria,) AND (admission) AND (at least 3 months) AND (consumption) AND (moderate) AND (older than 35) AND (smoker) AND (very severe) AND (years))"}
{"candidate_id": "LLM06863", "doc_id": "NCT03402945_exc", "case_bucket": "or", "source_criterion": "On systemic antibiotics or with an active bacterial infection at the time of surgery Patients previously enrolled in this trial Patients known to be colonized with Methicillin-resistant S. aureus (MRSA)(unethical not to administer glycopeptides), beta-lactam or vancomycin allergy precluding the use of cefazolin or vancomycin, respectively, or to silver precluding the use of Prevena Participation in other studies that may interfere with this trial", "candidate_expression": "((Methicillin-resistant S. aureus (MRSA)) AND (Participation in other studies that may interfere with this trial) AND (active) AND (allergy) AND (at the time of surgery) AND (colonized) AND (previously enrolled in this trial) AND (surgery) AND (the time of surgery) AND ((beta-lactam) OR (cefazolin) OR (silver) OR (vancomycin)) AND ((bacterial infection) OR (systemic antibiotics)))"}
{"candidate_id": "LLM06864", "doc_id": "NCT03147599_inc", "case_bucket": "other", "source_criterion": "Men 18 years or older ONB within 1 year post-surgery.", "candidate_expression": "((18 years or older) AND (Men) AND (ONB) AND (surgery) AND (within 1 year post-surgery))"}
{"candidate_id": "LLM06865", "doc_id": "NCT03125057_inc", "case_bucket": "other", "source_criterion": "Children with clinical diagnosis of PWS; Age range: 7 to 14 years-old; Voluntarily participated and Written informed consent signed", "candidate_expression": "((Age 7 to 14 years-old) AND (Children) AND (PWS clinical diagnosis) AND (Voluntarily participated) AND (Written informed consent signed))"}
{"candidate_id": "LLM06866", "doc_id": "NCT01793831_exc", "case_bucket": "or", "source_criterion": "Diagnosis as CD first time or first year. No history of using 5-ASA, biological or immunomodulatory therapy", "candidate_expression": "((CD) AND (No) AND (history) AND ((first time) OR (first year)) AND ((5-ASA) OR (immunomodulatory therapy) OR (therapy biological)))"}
{"candidate_id": "LLM06867", "doc_id": "NCT02481518_inc", "case_bucket": "or", "source_criterion": "Age > 18 years Eastern Cooperative Oncology Group score 0-2 First Diagnosed Head and neck cancer and plan for treatment with cisplatin Serum creatinine =1.5 mg/dl or eGFR=60(ml/min/1.73 m2)", "candidate_expression": "((Age > 18 years) AND (Eastern Cooperative Oncology Group score 0-2) AND (Head and neck cancer) AND (Serum creatinine =1.5 mg/dl) AND (cisplatin plan) AND (eGFR =60(ml/min/1.73 m2)))"}
{"candidate_id": "LLM06868", "doc_id": "NCT01084993_exc", "case_bucket": "or", "source_criterion": "Intolerance or allergy to ASA, clopidogrel or ticlopidine precluding treatment for 12 months Concurrent participation in other investigational study Femoral sheath (artery)", "candidate_expression": "((ASA) AND (Concurrent participation in other investigational study) AND (Femoral sheath (artery)) AND (Intolerance) AND (allergy) AND (clopidogrel) AND (for 12 months) AND (precluding) AND (ticlopidine) AND (treatment))"}
{"candidate_id": "LLM06869", "doc_id": "NCT02273791_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities or myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (endometriosis) AND (uterine surgery) AND ((Moderate) OR (severe)) AND ((Uterine abnormalities) OR (myoma)))"}
{"candidate_id": "LLM06870", "doc_id": "NCT02689089_exc", "case_bucket": "or", "source_criterion": "Suspected or confirmed active TB disease Known allergies to any of the study medications by participant self-report have a positive pregnancy test at screening, or are not willing to use a reliable method of barrier contraception during the study, or are breastfeeding hormonal contraception HIV infected participants who are on anti-retroviral drugs other drugs that interact with 3HP (see Table 1) Known contact with an INH or rifampin resistant case Weight < 10 kg Evidence of possible liver damage defined by an aspartate transaminase (AST) level that is more than 3x the upper limit of normal in an asymptomatic patient Porphyria reported by patient Inability to adhere to protocol. Patients may be excluded from the study for other reasons, at the investigator's discretion with detailed documentation.", "candidate_expression": "((AST) AND (HIV infected) AND (INH) AND (Inability to adhere to protocol) AND (Porphyria) AND (Weight < 10 kg) AND (active TB) AND (allergies) AND (anti-retroviral drugs) AND (are breastfeeding) AND (are not willing to use a reliable method of barrier contraception during the study) AND (aspartate transaminase more than 3x the upper limit of normal) AND (have a positive pregnancy test at screening) AND (hormonal contraception) AND (liver damage) AND (resistant) AND (rifampin))"}
{"candidate_id": "LLM06871", "doc_id": "NCT01567605_inc", "case_bucket": "other", "source_criterion": "traumatic spinal cord injury at least one year ago regular bowel care routine (at least four weeks)", "candidate_expression": "((at least four weeks) AND (at least one year ago) AND (regular bowel care routine) AND (traumatic spinal cord injury))"}
{"candidate_id": "LLM06872", "doc_id": "NCT02952365_exc", "case_bucket": "or", "source_criterion": "Subjects under the age of 21. Subjects with excessively thin corneas. Subjects with topographic evidence of keratoconus. Subjects with ectatic eye disorders. Subjects with autoimmune diseases. Subjects who are pregnant or nursing.", "candidate_expression": "((age under the age of 21) AND (autoimmune diseases) AND (ectatic eye disorders) AND (excessively thin corneas) AND (keratoconus) AND (topographic evidence) AND ((nursing) OR (pregnant)))"}
{"candidate_id": "LLM06873", "doc_id": "NCT02678728_exc", "case_bucket": "other", "source_criterion": "Unstable vital sign before surgery Severe pulmonary disease requiring consistent treatment Illiterate Pregnancy", "candidate_expression": "((Illiterate) AND (Pregnancy) AND (consistent treatment requiring) AND (pulmonary disease Severe) AND (surgery) AND (vital sign Unstable before surgery))"}
{"candidate_id": "LLM06874", "doc_id": "NCT03434951_inc", "case_bucket": "other", "source_criterion": "elective primary total knee arthroplasty ASA I-III written consent", "candidate_expression": "((ASA I-III) AND (total knee arthroplasty elective primary) AND (written consent))"}
{"candidate_id": "LLM06875", "doc_id": "NCT03282006_exc", "case_bucket": "or", "source_criterion": "Bacterial infection origin from another organ (e.g. pneumonia) Severe sepsis with multiorgan failure Perinephritic abscess Pyonephrosis requiring drainage Allergy to pivmecillinam E.coli isolate resistant to pivmecillinam Pregnancy/breastfeeding Severe neutropenia Prostatitis Severe kidney failure (eGFR<15 ml/min) Using valproate", "candidate_expression": "((<15 ml/min) AND (Allergy) AND (Bacterial infection) AND (E.coli isolate) AND (Perinephritic abscess) AND (Prostatitis) AND (Pyonephrosis) AND (Severe) AND (Severe sepsis) AND (another organ) AND (drainage) AND (eGFR) AND (kidney failure) AND (multiorgan failure) AND (neutropenia) AND (pivmecillinam) AND (pneumonia) AND (requiring) AND (resistant to pivmecillinam) AND (valproate) AND ((Pregnancy) OR (breastfeeding)))"}
```
