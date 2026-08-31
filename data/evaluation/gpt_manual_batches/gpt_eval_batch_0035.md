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
{"candidate_id": "LLM00851", "doc_id": "NCT03259243_exc", "case_bucket": "or", "source_criterion": "Patient with history of allergy in any kind anesthetic drug Patient who pregnant Patient who sign for single port gynecologic laparoscopic surgery or NOTE surgery Patient whom the surgery is withhold or canceled Patient whom the surgery is converted to laparotomy", "candidate_expression": "((allergy history) AND (anesthetic drug any kind) AND (laparotomy) AND (pregnant) AND (surgery) AND (surgery converted to) AND ((canceled) OR (withhold)) AND ((NOTE surgery) OR (gynecologic laparoscopic surgery single port)))"}
{"candidate_id": "LLM00852", "doc_id": "NCT02393287_inc", "case_bucket": "or", "source_criterion": "1. Age ≥ 18 years 2. Patient with breast cancer, histologically proven, metastatic or locally advanced 3. Patient treated by Eribulin between January and October 2014 (for the retrospective part) or between November 2014 and September 2015 (for the prospective part). 4. Patient with at least an assessment of the response to Eribulin", "candidate_expression": "((Age) AND (Eribulin) AND (assessment of the response) AND (between January and October 2014) AND (between November 2014 and September 2015) AND (breast cancer) AND (histologically) AND (locally advanced) AND (metastatic) AND (proven) AND (≥ 18 years))"}
{"candidate_id": "LLM00853", "doc_id": "NCT03217409_inc", "case_bucket": "or", "source_criterion": "Subjects = 19 or = 75 years of age Subjects undergoing treatment for type 2 diabetes Subjects undergoing treatment of statin for hypercholesterolemia Fasting LDL-C = 250mg/dL at the screening visit Fasting LDL-C =70mg/dL or = 160mg/dL at the randomization visit Fasting TG<500mg/dL", "candidate_expression": "((Fasting LDL-C = 250mg/dL at the screening visit) AND (Fasting LDL-C at the randomization visit at the randomization visit) AND (Fasting TG <500mg/dL) AND (age = 19 or = 75 years) AND (hypercholesterolemia) AND (statin) AND (treatment) AND (type 2 diabetes) AND ((= 160mg/dL) OR (=70mg/dL)))"}
{"candidate_id": "LLM00854", "doc_id": "NCT02765217_inc", "case_bucket": "or", "source_criterion": "Children receiving amoxicilline-clavulanic acid (50-90 mg/kg/day, twice daily) due to acute otitis media or acute sinusitis", "candidate_expression": "((Children) AND (amoxicilline-clavulanic acid 50-90 mg/kg/day twice daily) AND ((acute otitis media) OR (acute sinusitis)))"}
{"candidate_id": "LLM00855", "doc_id": "NCT02668978_inc", "case_bucket": "or", "source_criterion": "Patients over the age of 18 years who are able to give their informed consent Lobar and sublobar resections Open, video-assisted thoracoscopic or robotic surgeries Diagnostic or therapeutic procedures", "candidate_expression": "((able to give their informed consent) AND (over the age of 18 years) AND ((Diagnostic procedures) OR (therapeutic procedures)) AND ((Lobar resections) OR (sublobar resections)) AND ((robotic surgeries) OR (thoracoscopic surgeries)))"}
{"candidate_id": "LLM00856", "doc_id": "NCT03043495_inc", "case_bucket": "or", "source_criterion": "Patients undergoing surgeries in the upper limb (arm, forearm or hand)", "candidate_expression": "((arm) AND (forearm) AND (hand) AND (surgeries) AND (upper limb))"}
{"candidate_id": "LLM00857", "doc_id": "NCT00183885_exc", "case_bucket": "or", "source_criterion": "Patients who have received prior chemotherapy for unresectable disease Patients with any active or uncontrolled infection, including known HIV infection. (Patients with active hepatitis B will be placed on lamivudine. Patients with active hepatitis C will be eligible if liver tests qualify (5.1.9) Patients with psychiatric disorders that would interfere with consent or follow-up. Pregnant or lactating women. Men and women of reproductive potential may not participate unless they have agreed to use an effective contraceptive method. Patients with any other severe concurrent disease, which in the judgment of the investigator, would make the patient inappropriate for entry into this study.", "candidate_expression": "((HIV infection) AND (Pregnant) AND (active) AND (chemotherapy) AND (concurrent disease) AND (effective contraceptive method) AND (entry into this study) AND (hepatitis B) AND (hepatitis C) AND (inappropriate for) AND (infection) AND (interfere with consent) AND (interfere with follow-up) AND (lactating) AND (lamivudine) AND (liver tests) AND (psychiatric disorders) AND (qualify) AND (reproductive potential) AND (severe) AND (uncontrolled) AND (unresectable disease) AND (women))"}
{"candidate_id": "LLM00858", "doc_id": "NCT00440245_inc", "case_bucket": "or", "source_criterion": "asthma or COPD", "candidate_expression": "((COPD) AND (asthma))"}
{"candidate_id": "LLM00859", "doc_id": "NCT03424733_inc", "case_bucket": "or", "source_criterion": "diagnosed any form of MS (relapsing remitting, primary progressive, secondary progressive), any EDSS (expanded stability status scale) score", "candidate_expression": "((MS any form) AND (expanded stability status scale) AND (score EDSS any) AND ((primary progressive) OR (relapsing remitting) OR (secondary progressive)))"}
{"candidate_id": "LLM00860", "doc_id": "NCT02645474_exc", "case_bucket": "or", "source_criterion": "patients' refusal contraindication to regional anaesthesia (coagulopathies, concurrent anticoagulant therapy, allergy to local anaesthetics, infection at puncture site)", "candidate_expression": "((contraindication) AND (local anaesthetics) AND (patients' refusal) AND (regional anaesthesia () AND ((allergy) OR (anticoagulant therapy) OR (coagulopathies) OR (infection puncture site)))"}
{"candidate_id": "LLM00861", "doc_id": "NCT02918851_exc", "case_bucket": "or", "source_criterion": "Any significant acute or chronic medical illness or problem, including, but not limited to, diabetes, hypertension, cardiac disease, asthma, chronic obstructive lung disease Current or recent (last 60 days) tobacco or nicotine use History of sickle cell trait or disease or any other acquired or hereditary hematological abnormality History of fainting or other significant adverse reaction during phlebotomy or donation of blood Known prolonged QTc (or evidence of such at screening) on electrocardiogram defined as >470 ms Known or suspected illicit drug or alcohol abuse Known or suspected HIV, Hepatitis B, or Hepatitis C infection History of thrombophilia or anticoagulant therapy Pregnancy Obesity defined as BMI>30 Recent history of blood donation: a) Single whole blood unit donation within the past 8 weeks; b) Double RBC donation by apheresis within the past 16 weeks; or c) Plasma donation by apheresis within the past 4 weeks Inadequate RBC mass based on TBV <4500 ml (above) or screening Hb <14 g/dL", "candidate_expression": "((<14 g/dL) AND (<4500 ml) AND (>30) AND (>470 ms) AND (BMI) AND (Inadequate) AND (Obesity) AND (Pregnancy) AND (QTc) AND (RBC mass) AND (blood donation) AND (electrocardiogram) AND (last 60 days) AND (medical illness) AND ((nicotine use) OR (tobacco use)) AND ((acquired hematological abnormality) OR (hereditary hematological abnormality) OR (sickle cell disease) OR (sickle cell trait)) AND ((adverse reaction) OR (fainting)) AND ((donation of blood) OR (phlebotomy)) AND ((alcohol abuse) OR (illicit drug abuse)) AND ((HIV infection) OR (Hepatitis B infection) OR (Hepatitis C infection)) AND ((anticoagulant therapy) OR (thrombophilia)) AND ((asthma) OR (cardiac disease) OR (chronic obstructive lung disease) OR (diabetes) OR (hypertension)) AND ((Hb) OR (TBV)) AND ((acute) OR (chronic)))"}
{"candidate_id": "LLM00862", "doc_id": "NCT02872090_exc", "case_bucket": "other", "source_criterion": "beta blocker supraventricular rhythm disorder previous history of respiratory disease other than COPD diabetes autonomic dysfunction dysautonomia renal failure long-term oxygen therapy history of psychiatric illness", "candidate_expression": "((COPD) AND (autonomic dysfunction) AND (beta blocker) AND (diabetes) AND (dysautonomia) AND (history) AND (long-term oxygen therapy) AND (other than) AND (previous history) AND (psychiatric illness) AND (renal failure) AND (respiratory disease) AND (supraventricular rhythm disorder))"}
{"candidate_id": "LLM00863", "doc_id": "NCT01929434_exc", "case_bucket": "or", "source_criterion": "Intracranial infection. Severe respiratory and circulatory system diseases. Hematologic malignancies. Positive serological tests such as AIDS, hepatitis B virus, hepatitis C virus and syphilis （antigen or antibody）. Tumors. Genetic and metabolic diseases.", "candidate_expression": "((Hematologic malignancies) AND (Intracranial infection) AND (Severe) AND (Tumors) AND ((Genetic diseases) OR (metabolic diseases)) AND ((circulatory system disease) OR (respiratory system disease)) AND ((AIDS) OR (hepatitis B virus) OR (hepatitis C virus) OR (syphilis)))"}
{"candidate_id": "LLM00864", "doc_id": "NCT02890719_exc", "case_bucket": "or", "source_criterion": "Genotype 2, 3, 5 or 6 infection. Decompensated cirrhosis defined by the presence of actual or previous history of clinical decompensation including ascites, hepatic encephalopathy, variceal bleeding or spontaneous bacterial peritonitis, or a Child-Pugh B or C. Hepatocellular carcinoma after liver transplantation. Total bilirubin > 3 mg/dL. Immunosuppression with cyclosporine or an mTOR inhibitor (everolimus or sirolimus). Severe extrahepatic diseases: cardiovascular, respiratory, cerebrovascular and poorly controlled diabetes. Platelets < 75 x 109 cells/L. Neutrophil count < 0.5 x 109 cells/L. Hemoglobin < 9 g/dL. Albumin < 3g/dL. HIV infection. Hepatitis B infection. Active intake of toxic amounts of alcohol or recreational drugs. Females who are pregnant, become to be pregnant or breastfeeding or males whose partners are pregnant, become to be pregnant or breastfeeding. Intake of disallowed medications including(but not limited to): 1. Antibiotics: clarithromycin, erythromycin, telithromycin, nafcillin, rifampin 2. Antifungals: itraconazole, ketoconazole, voriconazole 3. Antihypertensives: nifedipine 4. Anticonvulsants: carbamazepine, phenytoin, phenobarbital 5. Bosentan 6. Modafinil 7. St.Jonh's Wort 8. Immunosuppressants: cyclosporin, everolimus, sirolimus 9. Diabetes agents: glibenclamide, glyburide 10. Lipid lowering agents: gemfibrozil 11. Eltrombopag 12. Lapatinib 13. HIV medications: efavirenz, etravirine, all ritonavir boosted and unboosted HIV protease inhibitors 14. Statins: simvastatin, fluvastatin, rosuvastatin at doses greater than 10 mg/d, atorvastatin at doses greater than 10 mg/d.", "candidate_expression": "((2, 3, 5 or 6) AND (< 0.5 x 109 cells/L) AND (< 3g/dL) AND (< 75 x 109 cells/L) AND (< 9 g/dL) AND (> 3 mg/dL) AND (Active intake) AND (Albumin) AND (B or C) AND (Bosentan) AND (Child-Pugh) AND (Decompensated) AND (Eltrombopag) AND (Females) AND (Genotype) AND (HIV infection) AND (HIV protease inhibitors) AND (Hemoglobin) AND (Hepatitis B infection) AND (Hepatocellular carcinoma) AND (Immunosuppression) AND (Lapatinib) AND (Modafinil) AND (Neutrophil count) AND (Platelets) AND (Severe) AND (St.Jonh's Wort) AND (Total bilirubin) AND (actual) AND (after liver transplantation) AND (alcohol) AND (ascites) AND (atorvastatin) AND (become) AND (breastfeeding) AND (carbamazepine) AND (cardiovascular) AND (cerebrovascular) AND (cirrhosis) AND (clarithromycin) AND (clinical decompensation) AND (cyclosporin) AND (cyclosporine) AND (diabetes) AND (disallowed medications) AND (doses greater than 10 mg/d) AND (efavirenz) AND (erythromycin) AND (etravirine) AND (everolimus) AND (extrahepatic diseases) AND (fluvastatin) AND (gemfibrozil) AND (glibenclamide) AND (glyburide) AND (hepatic encephalopathy) AND (infection) AND (itraconazole) AND (ketoconazole) AND (liver transplantation) AND (mTOR inhibitor) AND (males) AND (nafcillin) AND (nifedipine) AND (phenobarbital) AND (phenytoin) AND (poorly controlled) AND (pregnant) AND (previous) AND (recreational drugs) AND (respiratory) AND (rifampin) AND (ritonavir) AND (ritonavir boosted) AND (ritonavir unboosted) AND (rosuvastatin) AND (simvastatin) AND (sirolimus) AND (spontaneous bacterial peritonitis) AND (telithromycin) AND (toxic amounts) AND (variceal bleeding) AND (voriconazole))"}
{"candidate_id": "LLM00865", "doc_id": "NCT03619707_inc", "case_bucket": "or", "source_criterion": "Normal uterine cavity Normal Hormonal investigation: TSH,PRL,FBS Frozen embryo transfer cycles: at least 2 embryos Primary or secondary infertility: tubal occlusion, male factor, unexplained, endometriosis, ovarian factors… Body mass index (BMI) =18 to =30 kg/m2", "candidate_expression": "((BMI) AND (Body mass index =18 to =30 kg/m2) AND (FBS) AND (Frozen embryo transfer cycles) AND (Hormonal investigation Normal) AND (PRL) AND (Primary infertility) AND (TSH) AND (embryos at least 2) AND (endometriosis) AND (male factor) AND (ovarian factors) AND (secondary infertility) AND (tubal occlusion) AND (unexplained factors) AND (uterine cavity Normal))"}
{"candidate_id": "LLM00866", "doc_id": "NCT03255044_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to statin Treatment with statins during the past month prior to study. Serum creatinine > 3 mg/dl Significant liver disease: liver enzymes 2.5 folds the upper normal limit Malignancy Pregnancy or lactation", "candidate_expression": "((Malignancy) AND (Pregnancy) AND (Serum creatinine > 3 mg/dl) AND (hypersensitivity) AND (lactation) AND (liver disease Significant) AND (liver enzymes 2.5 folds the upper normal limit) AND (statin) AND (statins during the past month prior to study))"}
{"candidate_id": "LLM00867", "doc_id": "NCT03118232_exc", "case_bucket": "other", "source_criterion": "Nursing homes will not be eligible to participate if they meet the following criteria: Facilities routinely using decolonization Dedicated psychiatric nursing homes Facilities with a resident population with >=20% combative patients Pediatric facilities", "candidate_expression": "((Nursing homes) AND (Pediatric facilities) AND (combative patients) AND (decolonization routinely) AND (psychiatric nursing homes) AND (resident population >=20%))"}
{"candidate_id": "LLM00868", "doc_id": "NCT01491763_inc", "case_bucket": "or", "source_criterion": "Patients with Ph (BCR/ABL) positive de novo < 55 years old (it is advisable to include patients over 55 years LAL07OPH protocol). Performance status 0-2 (Appendix B) may include patients with performance status > 2 attributable to LAL. Patients without functional impairment of organs: liver function: total bilirubin, AST, ALT, alfa-GT and alkaline phosphatase less than 3 times the upper limit of normal laboratory renal function: serum creatinine < 2 mg/dL or clearance creatinine > 30 ml/min (except renal function attributable to LAL) cardiac function (Appendix B) normal: ventricular EF > 50%, absence of severe chronic respiratory disease. In the event that alterations are secondary to the disease is at the discretion of the investigator to determine if the patient can be included in the trial.", "candidate_expression": "((0-2) AND (< 2 mg/dL) AND (< 55 years) AND (> 30 ml/min) AND (> 50%) AND (ALT) AND (AST) AND (Performance status) AND (Ph (BCR/ABL)) AND (absence of) AND (alfa-GT) AND (alkaline phosphatase) AND (cardiac function) AND (de novo) AND (functional impairment of organs) AND (less than 3 times the upper limit of normal) AND (normal) AND (old) AND (positive) AND (severe chronic respiratory disease) AND (total bilirubin) AND (ventricular EF) AND (without) AND ((clearance creatinine) OR (serum creatinine)))"}
{"candidate_id": "LLM00869", "doc_id": "NCT03639519_exc", "case_bucket": "or", "source_criterion": "Allergy to ascorbic acid Asthma COPD Allergy to opioids Previous history of chemical dependence Prior cardiac surgery Known hyperoxaluria History of renal calculi History of allergic or hypersensitivity reaction to ascorbic acid products Currently taking 1 g or more of ascorbic acid supplementation daily", "candidate_expression": "((1 g or more) AND (Allergy) AND (Asthma) AND (COPD) AND (History) AND (Previous) AND (Prior) AND (ascorbic acid) AND (cardiac surgery) AND (chemical dependence) AND (history) AND (hyperoxaluria) AND (opioids) AND (renal calculi) AND ((allergic) OR (hypersensitivity)))"}
{"candidate_id": "LLM00870", "doc_id": "NCT01911650_exc", "case_bucket": "or", "source_criterion": "1. bilateral AT 2. insertional AT 3. local steroid injection within 6 weeks or physical therapy within 4 weeks 4. inability to comply with follow-up criteria 5. history of surgery on the Achilles tendon or systemic diseases (general inflammatory diseases such as rheumatologic disorders and diabetes) 6. daily use of opioids for pain 7. anticoagulation or immunosuppressive therapy 8. intent to use NSAIDs or steroids 9. self-reported pregnancy", "candidate_expression": "((bilateral AT) AND (daily) AND (general inflammatory diseases) AND (history) AND (inability to comply with follow-up criteria) AND (insertional AT) AND (opioids) AND (pain) AND (pregnancy) AND (surgery on the Achilles tendon) AND (systemic diseases) AND (within 4 weeks) AND (within 6 weeks) AND ((diabetes) OR (rheumatologic disorders)) AND ((anticoagulation therapy) OR (immunosuppressive therapy)) AND ((NSAIDs) OR (steroids)) AND ((local steroid injection) OR (physical therapy)))"}
{"candidate_id": "LLM00871", "doc_id": "NCT02022709_exc", "case_bucket": "or", "source_criterion": "Having significant medical illnesses that would interfere with the conduct of the study Clinically significant abnormal laboratory finding Having comorbid psychiatric conditions according to the criteria set forth in the DSM-IV(administered by the Mini-International Neuropsychiatric Interview (MINI)) The current OCD symptoms are too severe that the patient cannot finish the evaluation or receive the ERP Being currently at risk for suicide Being pregnant or having the intention to be pregnant before the end of the study A history of having inadequate response to adequate SSRIs or CBT treatment Subjects who are unable to undergo the MRI", "candidate_expression": "((Being pregnant or having the intention to be pregnant before the end of the study) AND (CBT) AND (MRI unable to) AND (OCD symptoms severe) AND (SSRIs) AND (psychiatric conditions comorbid DSM-IV) AND (response inadequate) AND (risk for suicide))"}
{"candidate_id": "LLM00872", "doc_id": "NCT03208127_inc", "case_bucket": "other", "source_criterion": "Recipient is Age = 18 years Met MGH transplant center criteria, listed for liver transplant HCV naive Able to sign informed consent", "candidate_expression": "((= 18 years) AND (Able to sign informed consent) AND (Age) AND (HCV) AND (HCV naive) AND (MGH transplant center criteria) AND (liver transplant) AND (naive))"}
{"candidate_id": "LLM00873", "doc_id": "NCT02360631_inc", "case_bucket": "other", "source_criterion": "Self-identified African American Smokes = 1 cigarette per day (cpd) Smoke on = 25 days of the past 30 days Functioning telephone Interested in quitting smoking Interested in taking 3 months of varenicline Willing to complete all study visits", "candidate_expression": "((= 1 cigarette per day) AND (= 25 days of the past 30 days) AND (African American) AND (Interested) AND (Interested in quitting smoking) AND (Interested in taking 3 months of varenicline) AND (Smoke) AND (Smokes) AND (Willing to complete all study visits) AND (quitting smoking))"}
{"candidate_id": "LLM00874", "doc_id": "NCT03047538_exc", "case_bucket": "or", "source_criterion": "hypersensitivity to perindopril or to other ACE inhibitors, amlodipine, atorvastatin, dihydropyridines or to or statins angioneurotic edema in medical history (hereditary / idiopathic or associated with prior treatment with ACE inhibitors) severe hypotension, shock, including cardiogenic shock hemodynamically unstable heart failure Active liver disease or unexplained persistent elevations of serum transaminases more than three times normal Women of childbearing age without reliable contraception pregnancy breastfeeding Patients with contraindications listed in the currently valid SP", "candidate_expression": "((ACE inhibitors) AND (Women) AND (amlodipine) AND (angioneurotic edema) AND (associated) AND (atorvastatin) AND (breastfeeding) AND (cardiogenic shock) AND (childbearing age) AND (contraception) AND (contraindications) AND (dihydropyridines) AND (elevations) AND (heart failure) AND (hemodynamically unstable) AND (hereditary) AND (hypersensitivity) AND (hypotension) AND (idiopathic) AND (listed in the currently valid SP) AND (liver disease) AND (more than three times normal) AND (other) AND (perindopril) AND (persistent) AND (pregnancy) AND (prior) AND (reliable) AND (serum transaminases) AND (severe) AND (shock) AND (statins) AND (treatment) AND (unexplained) AND (without))"}
{"candidate_id": "LLM00875", "doc_id": "NCT03147599_exc", "case_bucket": "or", "source_criterion": "Upper urinary tract deterioration Uncontrolled diabetes mellitus Evident local or pelvic recurrence Adjuvant chemotherapy Chronic retention Pouch stones Urethral stricture or urethro-ileal maldirection Sensitivity to Mebeverine Untreated chronic constipation Active symptomatic urinary infection", "candidate_expression": "((Active) AND (Adjuvant chemotherapy) AND (Chronic retention) AND (Mebeverine) AND (Pouch stones) AND (Sensitivity) AND (Uncontrolled) AND (Untreated) AND (Upper urinary tract deterioration) AND (Urethral stricture) AND (chronic constipation) AND (diabetes mellitus) AND (symptomatic) AND (urethro-ileal maldirection) AND (urinary infection) AND ((local recurrence) OR (pelvic recurrence)))"}
```
