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
{"candidate_id": "LLM07451", "doc_id": "NCT01997580_inc", "case_bucket": "or", "source_criterion": "DSM-IV-TR major depressive disorder aged between 20 and 80 durg-naive or drug-free", "candidate_expression": "((DSM-IV-TR) AND (aged) AND (between 20 and 80) AND (free) AND (major depressive disorder) AND (naive) AND ((drug) OR (durg)))"}
{"candidate_id": "LLM07452", "doc_id": "NCT01742117_inc", "case_bucket": "or", "source_criterion": "Patient >18 years of age Patient presents with acute coronary syndrome (ACS) or stable coronary artery disease (CAD) Patient is eligible for PCI Patient is willing and able to provide informed written consent Patient not able to receive 12 months of dual anti-platelet therapy Failure of index PCI Patient or physician refusal to enroll in the study Patient with known CYP2C19 genotype prior to randomization Planned revascularization of any vessel within 30 days post-index procedure and/or of the target vessel(s) within 12 months post-procedure Anticipated discontinuation of clopidogrel or ticagrelor within the 12 month follow up period, example for elective surgery Serum creatinine >2.5 mg/dL within 7 days of index procedure Platelet count <80,000 or >700,000 cells/mm3, or white blood cell count <3,000 cells/mm3 if persistent (at least 2 abnormal values) within 7 days prior to index procedure. History of intracranial hemorrhage Known hypersensitivity to clopidogrel or ticagrelor or any of its components Patient is participating in an investigational drug or device clinical trial that has not reached its primary endpoint Patient previously enrolled in this study Patient is pregnant, lactating, or planning to become pregnant within 12 months Patient has received an organ transplant or is on a waiting list for an organ transplant Patient is receiving or scheduled to receive chemotherapy within 30 days before or after the procedure Patient is receiving immunosuppressive therapy or has known immunosuppressive or autoimmune disease (e.g., human immunodeficiency virus, systemic lupus erythematous, etc.) Patient is receiving chronic oral anticoagulation therapy (i.e., vitamin K antagonist, direct thrombin inhibitor, Factor Xa inhibitor) Concomitant use of simvastatin/lovastatin > 40 mg qd Concomitant use of potent CYP3A4 inhibitors (atazanavir, clarithromycin, indinavir, itraconazole, ketoconazole, nefazodone, nelfinavir, ritonavir, saquinavir, telithromycin and voriconazole) or inducers (carbamazepine, dexamethasone, phenobarbital, phenytoin, rifampin, and rifapentine) Non-cardiac condition limiting life expectancy to less than one year, per physician judgment (e.g. cancer) Known history of severe hepatic impairment Patient has a history of bleeding diathesis or coagulopathy or will refuse blood transfusions Patient has an active pathological bleeding, such as active gastrointestinal (GI) bleeding Inability to take aspirin at a dosage of 100 mg or less Current substance abuse (e.g., alcohol, cocaine, heroin, etc.)", "candidate_expression": "((ACS) AND (CAD) AND (CYP2C19 genotype prior to randomization) AND (Factor Xa inhibitor) AND (Inability to take) AND (Non-cardiac condition life expectancy) AND (PCI Failure index) AND (PCI eligible) AND (Patient is willing and able to provide informed written consent) AND (Patient or physician refusal to enroll in the study) AND (Platelet count <80,000 or >700,000 cells/mm3) AND (Serum creatinine >2.5 mg/dL within 7 days of index procedure) AND (able to receive) AND (acute coronary syndrome) AND (age >18 years) AND (any of its components) AND (aspirin 100 mg or less) AND (atazanavir) AND (autoimmune disease) AND (bleeding diathesis) AND (blood transfusions will refuse) AND (carbamazepine) AND (chemotherapy) AND (clarithromycin) AND (clopidogrel) AND (coagulopathy) AND (coronary artery disease stable) AND (dexamethasone) AND (direct thrombin inhibitor) AND (dual anti-platelet therapy 12 months) AND (elective surgery example for) AND (gastrointestinal (GI) bleeding active) AND (hepatic impairment severe) AND (human immunodeficiency virus) AND (hypersensitivity) AND (immunosuppressive disease) AND (immunosuppressive therapy) AND (indinavir) AND (intracranial hemorrhage) AND (itraconazole) AND (ketoconazole) AND (lactating) AND (lovastatin Concomitant > 40 mg qd) AND (nefazodone) AND (nelfinavir) AND (oral anticoagulation therapy chronic) AND (organ transplant) AND (organ transplant is on a waiting list is receiving scheduled to receive) AND (pathological bleeding active) AND (phenobarbital) AND (phenytoin) AND (potent CYP3A4 inducers Concomitant) AND (potent CYP3A4 inhibitors Concomitant) AND (pregnant) AND (pregnant planning to become within 12 months) AND (revascularization Planned any vessel of the target vessel(s)) AND (rifampin) AND (rifapentine) AND (ritonavir) AND (saquinavir) AND (simvastatin Concomitant > 40 mg qd) AND (substance abuse) AND (systemic lupus erythematous) AND (telithromycin) AND (ticagrelor) AND (vitamin K antagonist) AND (voriconazole) AND (white blood cell count <3,000 cells/mm3))"}
{"candidate_id": "LLM07453", "doc_id": "NCT02754583_inc", "case_bucket": "other", "source_criterion": "Community in a school district that is within the study area Area within each school district that is in need of a well", "candidate_expression": "((school district that is in need of a well) AND (school district that is within the study area))"}
{"candidate_id": "LLM07454", "doc_id": "NCT01895946_inc", "case_bucket": "or", "source_criterion": "Aged at least 18 years The presence of a solid, malignant tumour, excluding lymphoma, that is resistance to standard therapies or for which no standard therapies exist The presence of at least one lesion that can be accurately assessed at baseline by Computerised Tomography (CT), Magnetic Resonance Imaging (MRI) or plain X-ray and is suitable for repeated assessment Estimated life expectancy of more than 12 weeks", "candidate_expression": "((Aged at least 18 years) AND (Estimated life expectancy more than 12 weeks) AND (lesion at least one accurately assessed at baseline suitable for repeated assessment) AND (solid, malignant tumour) AND NOT (lymphoma) AND ((Computerised Tomography (CT)) OR (Magnetic Resonance Imaging (MRI)) OR (plain X-ray)) AND ((for which no standard therapies exist) OR (resistance to standard therapies)))"}
{"candidate_id": "LLM07455", "doc_id": "NCT03354572_inc", "case_bucket": "other", "source_criterion": "Subjects scheduled for laparoscopic unilateral inguinal hernia repair ASA 1 or2. Age >18 years.", "candidate_expression": "((1 or2) AND (>18 years) AND (ASA) AND (Age) AND (inguinal hernia repair) AND (laparoscopic) AND (scheduled) AND (unilateral))"}
{"candidate_id": "LLM07456", "doc_id": "NCT03413891_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for dental extraction and treated with edoxaban, apixaban, rivaroxaban or dabigatran Not having taken the direct oral anticoagulant on the day of the extraction Provision of signed and dated informed consent form Stated willingness to comply with all study procedures and availability for the duration of the study", "candidate_expression": "((Provision of signed and dated informed consent form) AND (Stated willingness to comply with all study procedures and availability for the duration of the study) AND (dental extraction scheduled for) AND NOT (anticoagulant oral on the day of the extraction) AND ((apixaban) OR (dabigatran) OR (edoxaban) OR (rivaroxaban)))"}
{"candidate_id": "LLM07457", "doc_id": "NCT02283996_exc", "case_bucket": "other", "source_criterion": "Non-English speaking patients Pregnant women (women of childbearing potential will be advised to undergo regular pregnancy testing) Patients who had previously undergone operative therapy for the condition", "candidate_expression": "((Patients who had previously undergone operative therapy for the condition) AND (Pregnant women (women of childbearing potential will be advised to undergo regular pregnancy testing)))"}
{"candidate_id": "LLM07458", "doc_id": "NCT03119766_exc", "case_bucket": "or", "source_criterion": "Organic diseases of the digestive system (gastro-oesophageal reflux disease (GERD), ulcer, chronic pancreatitis, cholelithiasis, fatty liver disease, hepatitis, cirrhosis of liver, etc.) . Diagnosis of other functional diseases of the digestive system, such as dyskinesia of cystic duct or gallbladder, irritable bowel syndrome, etc. Discontinuation of proton pump inhibitors, propulsives, antispasmodics, antacids, or bismuth preparations less than 7 days prior to randomization. H. Pylori eradication within 2 months before study entry. Intestinal infection within 2 months before study entry. Known history of/suspected malignant neoplasm of various sites. Prior diagnosis of a class IV cardiovascular disease (according to the New York Heart Association, 1964), hypothyroidism, diabetes mellitus, chronic kidney disease (С3-5), or disease of liver with portal hypertension and/or severe decompensation (Child-Pugh score > 6). Other severe coexisting morbidity which, in the investigator's opinion, can prevent the patient from participating in the study. Allergy/intolerance to any of the components of medications used in the treatment. Pregnancy, breast-feeding. Patients who, from investigator's point of view, will fail to comply with the observation requirements of the trial or with the dosing regimen of the investigational drugs. Planned hospitalization during the study period, for any diagnostic or treatment procedures. Drug addiction, alcohol use in the amount over 2 units of alcohol a day, mental diseases. Intake of medicines listed in the section 'Prohibited concomitant treatment' for 1 month prior to the enrollment in the trial. Participation in other clinical trials within 3 months to the enrollment in this study. Patient is related to the research staff of the clinical investigative site who are directly involved in the trial or is the immediate family member of the investigator. The immediate family members include husband/wife, parents, children or brothers (or sisters), regardless of whether they are natural or adopted. Patient works for OOO \"NPF \"MATERIA MEDICA HOLDING\" (i.e., is the company's employee, temporary contract worker or appointed official responsible for carrying out the research or their immediate family).", "candidate_expression": "((1 month prior to the enrollment in the trial) AND (3-5) AND (> 6) AND (Allergy) AND (Child-Pugh score) AND (Discontinuation) AND (Drug addiction) AND (H. Pylori eradication) AND (Intestinal infection) AND (New York Heart Association) AND (Organic diseases) AND (Participation in other clinical trials within 3 months to the enrollment in this study.) AND (Planned) AND (Pregnancy) AND (alcohol use) AND (antacids) AND (antispasmodics) AND (appointed official) AND (bismuth preparations) AND (breast-feeding) AND (cardiovascular disease) AND (cholelithiasis) AND (chronic kidney disease) AND (chronic pancreatitis) AND (cirrhosis of liver) AND (class IV) AND (coexisting) AND (company's employee) AND (components of medications used in the treatment) AND (diabetes mellitus) AND (diagnostic procedures) AND (digestive system) AND (disease of liver) AND (during the study period) AND (dyskinesia of cystic duct) AND (dyskinesia of gallbladder) AND (fatty liver disease) AND (functional diseases) AND (gastro-oesophageal reflux disease (GERD)) AND (hepatitis) AND (history of) AND (hospitalization) AND (hypothyroidism) AND (intolerance) AND (irritable bowel syndrome) AND (less than 7 days prior to randomization) AND (listed in the section 'Prohibited concomitant treatment') AND (malignant neoplasm) AND (medicines) AND (mental diseases) AND (morbidity) AND (over 2 units of alcohol a day) AND (portal hypertension) AND (propulsives) AND (proton pump inhibitors) AND (randomization) AND (responsible for carrying out the research or their immediate family) AND (severe decompensation) AND (study entry) AND (suspected) AND (temporary contract worker) AND (the enrollment in the trial) AND (treatment procedures) AND (ulcer) AND (various sites) AND (within 2 months before study entry) AND (works for OOO \"NPF \"MATERIA MEDICA HOLDING\") AND (С))"}
{"candidate_id": "LLM07459", "doc_id": "NCT01391780_inc", "case_bucket": "or", "source_criterion": "presence of stress urinary or urgency incontinence", "candidate_expression": "((stress urinary incontinence) OR (urgency incontinence))"}
{"candidate_id": "LLM07460", "doc_id": "NCT02283996_inc", "case_bucket": "other", "source_criterion": "Patient must be 18 years or older Must meet the following definition for adhesive capsulitis as defined by the American Academy of Orthopedic Surgeons: Self-limiting condition resulting from any inflammatory process about the shoulder in which capsular scar tissue is produced, resulting in pain and limited range of motion; also called frozen shoulder Must be amenable to randomization into either cohort", "candidate_expression": "((American Academy of Orthopedic Surgeons) AND (Must be amenable to randomization into either cohort) AND (adhesive capsulitis) AND (years 18 or older))"}
{"candidate_id": "LLM07461", "doc_id": "NCT02462590_exc", "case_bucket": "or", "source_criterion": "Invasively mechanically ventilated >72 hours at the time of screening; Patients at potential increased risk of iatrogenic probiotic infection (see Section 2.6 for detailed explanation) including specific immunocompromised populations (HIV <200 CD4 cells/µL, those receiving chronic immunosuppressive medications (e.g., azathioprine, cyclosporine, cyclophosphamide, tacrolimus, methotrexate, mycofenolate, Anti-IL2), previous transplantation (including stem cell) at any time, malignancy requiring chemotherapy in the last 3 months, neutropenia [absolute neutrophil count < 500]). However, patients receiving corticosteroids previously or presently or projected to receive corticosteroids are not excluded; Patients at risk for endovascular infection (previously documented rheumatic heart disease, congenital valve disease, surgically repaired congenital heart disease, unrepaired cyanotic congenital heart disease, any intracardiac repair with prosthetic material [mechanical or bio-prosthetic cardiac valves], previous or current endocarditis, permanent endovascular devices (e.g., endovascular grafts [e.g., aortic aneurysm repair, stents involving large arteries such as aorta, femorals and carotids], inferior vena cava filters, dialysis vascular grafts), tunnelled (not short-term) hemodialysis catheters, pacemakers or defibrillators. Patients with temporary central venous catheters, central venous dialysis catheters or peripherally inserted central catheters (PICCs) are not excluded and patients with coronary artery stents, coronary artery bypass grafts (CABG) or neurovascular coils are not excluded; patients with mitral valve prolapse or bicuspid aortic valve are not excluded providing they have no other exclusion criteria; Patients with a primary diagnosis of severe acute pancreatitis, without reference to a Ranson score [Ranson 1974]). However, patients with mild or moderate pancreatitis are not excluded; Patients with percutaneous gastric or jejunal feeding tubes already in situ as per Health Canada guidance; Strict contraindication or inability to receive enteral medications; Intent to withdraw advanced life support as per the ICU physician; Previous enrolment in this or current enrolment in a potentially confounding tria", "candidate_expression": "((< 500]) AND (<200 cells/µL) AND (>72 hours) AND (CD4) AND (HIV) AND (PICCs) AND (Previous enrolment in this or current enrolment in a potentially confounding tria) AND (Ranson score) AND (absolute neutrophil count) AND (acute pancreatitis) AND (chronic) AND (contraindication) AND (endocarditis) AND (enteral medications) AND (gastric feeding tubes) AND (intracardiac repair) AND (jejunal feeding tubes) AND (large arteries) AND (last 3 months) AND (mechanically ventilated) AND (not) AND (pancreatitis) AND (permanent) AND (risk for endovascular infection) AND (risk of iatrogenic probiotic infection) AND (severe) AND (surgically repaired) AND (unrepaired) AND (without) AND ((Anti-IL2) OR (azathioprine) OR (cyclophosphamide) OR (cyclosporine) OR (methotrexate) OR (mycofenolate) OR (tacrolimus)) AND ((chemotherapy) OR (immunocompromised) OR (immunosuppressive medications) OR (neutropenia) OR (transplantation)) AND ((congenital heart disease) OR (congenital valve disease) OR (cyanotic congenital heart disease) OR (endovascular devices) OR (hemodialysis catheters) OR (pacemakers) OR (prosthetic material) OR (rheumatic heart disease)) AND ((bio-prosthetic cardiac valves]) OR (mechanical cardiac valves)) AND ((aortic aneurysm repair) OR (stents)) AND ((dialysis vascular grafts) OR (endovascular grafts) OR (inferior vena cava filters)) AND ((central venous catheters) OR (central venous dialysis catheters) OR (peripherally inserted central catheters)) AND ((coronary artery bypass grafts) OR (coronary artery stents) OR (neurovascular coils)) AND ((bicuspid aortic valve) OR (mitral valve prolapse)) AND ((mild) OR (moderate)))"}
{"candidate_id": "LLM07462", "doc_id": "NCT03356834_inc", "case_bucket": "other", "source_criterion": "Chronic hepatitis B, Antiviral experienced, Currently on long term TDF anti-HBV treatment, HBV DNA < 6 log IU/ml (LLOD) Able to sign the consent form of anticipating in the study", "candidate_expression": "((< 6 log IU/ml) AND (Able to sign the consent form of anticipating in the study) AND (Antiviral) AND (Chronic hepatitis B) AND (HBV) AND (HBV DNA) AND (LLOD) AND (TDF) AND (TDF anti-HBV treatment) AND (experienced) AND (long term))"}
{"candidate_id": "LLM07463", "doc_id": "NCT03555526_inc", "case_bucket": "other", "source_criterion": "H pylori infection failed after at least two eradication therapies aged 20 years or greater willingness to receive rescue therapy", "candidate_expression": "((H pylori infection) AND (aged 20 years or greater) AND (eradication therapies failed at least two) AND (rescue therapy willingness))"}
{"candidate_id": "LLM07464", "doc_id": "NCT01312012_exc", "case_bucket": "or", "source_criterion": "major systemic disease Pregnant woman with infection of human immunodeficiency virus or hepatitis C virus Pregnant woman is receiving any drug with antiviral activity or any form of drug therapy for hepatitis B virus Pregnant woman whose ultrasonographic examination reveals congenital anomaly of the fetus Pregnant woman whose amniocentesis reveals any genetic abnormality", "candidate_expression": "((Pregnant) AND (amniocentesis genetic abnormality) AND (hepatitis B virus) AND (major systemic disease) AND (ultrasonographic examination congenital anomaly of the fetus) AND (woman) AND ((hepatitis C virus) OR (human immunodeficiency virus)) AND ((drug therapy) OR (drug with antiviral activity)))"}
{"candidate_id": "LLM07465", "doc_id": "NCT03336801_inc", "case_bucket": "other", "source_criterion": "Scheduled back surgery", "candidate_expression": "(back surgery Scheduled)"}
{"candidate_id": "LLM07466", "doc_id": "NCT03344887_exc", "case_bucket": "other", "source_criterion": "Patients that do not have a valid Ontario Health Insurance Plan (OHIP) number at time of first transfusion Patients that require emergent release of a RBC transfusion and in whom emergency randomization could not be completed Patients with complex antibody profile in which it is impossible to match RBC units", "candidate_expression": "((RBC transfusion) AND (at time of first transfusion) AND (complex antibody profile) AND (could not be completed) AND (emergency randomization) AND (emergent release) AND (first) AND (first transfusion) AND (have a valid Ontario Health Insurance Plan (OHIP) number) AND (impossible to match RBC units) AND (not) AND (require) AND (transfusion))"}
{"candidate_id": "LLM07467", "doc_id": "NCT01639664_inc", "case_bucket": "other", "source_criterion": "All patients admitted to the ICU in septic shock All patients that develop septic shock while in the ICU", "candidate_expression": "((ICU) AND (admitted) AND (in the ICU) AND (septic shock) AND (while in the ICU))"}
{"candidate_id": "LLM07468", "doc_id": "NCT03325023_inc", "case_bucket": "or", "source_criterion": "Written consent for participation in the clinical trial Age 18 to 45 years Irregular menstruation (> 35 days) or secondary amenorrhea> 3 months", "candidate_expression": "((Age 18 to 45 years > 35 days) AND (Written consent for participation in the clinical trial) AND ((Irregular menstruation) OR (secondary amenorrhea > 3 months)))"}
{"candidate_id": "LLM07469", "doc_id": "NCT02035904_inc", "case_bucket": "or", "source_criterion": "F; age 18 to 70 American Society of Anesthesiologists (ASA) I e II; breast cancer ( DIN 2 e 3, o LIN 2 e 3 sec. Tavassoli) scheduled for nipple-sparing mastectomy, simple mastectomy, skin-sparing mastectomy, skin-reducing mastectomy c, lymphnode biopsy and axillary dissection; immediate sub-pectoral prosthetic reconstruction; signed informed consent.", "candidate_expression": "((18 to 70) AND (2 e 3) AND (2 e 3 sec) AND (American Society of Anesthesiologists (ASA)) AND (DIN) AND (F) AND (I e II) AND (LIN) AND (age) AND (axillary dissection) AND (breast cancer) AND (immediate) AND (lymphnode biopsy) AND (nipple-sparing mastectomy) AND (scheduled for) AND (simple mastectomy) AND (skin-reducing mastectomy) AND (skin-sparing mastectomy) AND (sub-pectoral prosthetic reconstruction))"}
{"candidate_id": "LLM07470", "doc_id": "NCT02838810_inc", "case_bucket": "other", "source_criterion": "CHB patients who had received single NAs for more than 12 months. Hepatitis B e antigen (HBeAg)-negative. Hepatitis B surface antigen (HBsAg) positive and <1000 IU/mL. Hepatitis B virus DNA <100 IU/mL.", "candidate_expression": "((CHB) AND (HBeAg) AND (HBsAg) AND (Hepatitis B e antigen negative) AND (Hepatitis B surface antigen positive <1000 IU/mL) AND (Hepatitis B virus DNA <100 IU/mL) AND (NAs single more than 12 months))"}
{"candidate_id": "LLM07471", "doc_id": "NCT02990403_inc", "case_bucket": "other", "source_criterion": "Woman who had 2 miscarriage before 12(th) week of gestation.The patient who is diagnosed as thrombophilia with recurrent pregnancy loss. Signed consent form.", "candidate_expression": "((12(th) week of gestation) AND (2) AND (Signed consent form.) AND (Woman) AND (before 12(th) week of gestation) AND (miscarriage) AND (pregnancy loss) AND (recurrent) AND (thrombophilia))"}
{"candidate_id": "LLM07472", "doc_id": "NCT03068897_exc", "case_bucket": "or", "source_criterion": "Not available for follow-up Pregnant or breast-feeding Chronic pain syndrome defined as use of any analgesic medication on a daily or near-daily basis Allergic to or intolerant of investigational medications Contra-indications to non-steroidal anti-inflammatory drugs: 1) history of hypersensitivity to NSAIDs or aspirin 2) active or history of peptic ulcer disease, chronic dyspepsia, or active or history of gastrointestinal bleed 3) Severe heart failure (NYHA 2 or worse) 4) hypertension (JNC7 stage 2 or worse) 5) Chronic kidney disease 3 or worse 6) Current use of anti-coagulants 7) Hepatitis 8) Alcoholism Contra-indications to muscle relaxants: 1) Concurrent use of centrally acting opioids; 2) Renal impairment; 3) Liver abnormality including cirrhosis or elevated enzymes 4) Use of any of the following medications: fluvoxamine, fluoroquinolones, amiodarone, mexiletine, propafenone, verapamil, cimetidine, famotidine, acyclovir, ticlopidine, oral contraceptive pills", "candidate_expression": "((2 or worse) AND (Chronic pain syndrome) AND (Concurrent) AND (Contra-indications) AND (Current) AND (JNC7 stage) AND (NYHA) AND (Severe) AND (analgesic medication) AND (any) AND (history) AND (investigational medications) AND (muscle relaxants) AND (non-steroidal anti-inflammatory drugs) AND ((Allergic) OR (intolerant)) AND ((NSAIDs) OR (aspirin)) AND ((Pregnant) OR (breast-feeding)) AND ((active) OR (history)) AND ((chronic dyspepsia) OR (peptic ulcer disease)) AND ((Alcoholism) OR (Chronic kidney disease) OR (Hepatitis) OR (anti-coagulants) OR (gastrointestinal bleed) OR (heart failure) OR (hypersensitivity) OR (hypertension)) AND ((Liver abnormality) OR (Renal impairment) OR (centrally acting opioids)) AND ((cirrhosis) OR (elevated enzymes)) AND ((acyclovir) OR (amiodarone) OR (cimetidine) OR (famotidine) OR (fluoroquinolones) OR (fluvoxamine) OR (mexiletine) OR (oral contraceptive pills) OR (propafenone) OR (ticlopidine) OR (verapamil)) AND ((on a daily basis) OR (on a near-daily basis)))"}
{"candidate_id": "LLM07473", "doc_id": "NCT02164734_exc", "case_bucket": "or", "source_criterion": "Weight < 800 g; Airway anomalies; Pulmonary air leaks; Craniofacial or cardiothoracic malformations", "candidate_expression": "((< 800 g) AND (Airway anomalies) AND (Craniofacial malformations) AND (Pulmonary air leaks) AND (Weight) AND (cardiothoracic malformations))"}
{"candidate_id": "LLM07474", "doc_id": "NCT02227992_exc", "case_bucket": "or", "source_criterion": "Subjects with known intolerance to blood products or to one of the components of the study product or is unwilling to receive blood products; Female subjects, who are of childbearing age (i.e. adolescent), who are pregnant or nursing; Subject is currently participating or plans to participate in any other investigational device or drug without prior approval from the Sponsor; Subjects who are known, current alcohol and/or drug abusers Subjects admitted for trauma surgery Subjects with any pre or intra-operative findings identified by the surgeon that may preclude conduct of the study procedure. Subject with TBS in an actively infected field (Class III Contaminated or Class IV Dirty or Infected) TBS is from large defects in arteries or veins where the injured vascular wall requires repair with maintenance of vessel patency and which would result in persistent exposure of the EVARREST™ or SURGICEL® to blood flow and pressure during healing and absorption of the product; TBS with major arterial bleeding requiring suture or mechanical ligation; Bleeding site is in, around, or in proximity to foramina in bone, or areas of bony confine.", "candidate_expression": "((Female subjects, who are of childbearing age (i.e. adolescent), who are pregnant or nursing) AND (Subject is currently participating or plans to participate in any other investigational device or drug without prior approval from the Sponsor) AND (TBS) AND (blood products) AND (intolerance) AND (major arterial bleeding) AND (trauma surgery) AND ((Class III Contaminated) OR (Class IV Dirty or Infected)) AND ((mechanical ligation) OR (suture)) AND ((alcohol abusers) OR (drug abusers)))"}
{"candidate_id": "LLM07475", "doc_id": "NCT02370069_exc", "case_bucket": "or", "source_criterion": "immunization with PPV23 within the last year any confirmed or suspected immunodeficiency condition, including human immunodeficiency virus (HIV) infection, haematological malignancy, or a congenital immunodeficiency history of allergic disease or reactions likely to be exacerbated by any component of the vaccine history of allergic disease likely to be stimulated by the vaccination history or records of immunosuppressive therapy (with the exception of topical corticosteroids) for more than 14 days and within 6 months of vaccination history or evidence of administration of immunoglobulins and/or any blood products during the study period or within the three months preceding the study vaccine use of any other investigational or non-registered drug or vaccine during the study period or within 30 days preceding the study vaccine administration of a vaccine during the period starting one month before the dose of vaccine and ending one month after pregnancy", "candidate_expression": "((HIV) AND (PPV23) AND (allergic disease) AND (allergic reactions) AND (blood products) AND (confirmed) AND (congenital immunodeficiency) AND (drug) AND (during the period starting one month before the dose of vaccine and ending one month after) AND (during the study period) AND (exacerbated by any component of the vaccine) AND (exception) AND (for more than 14 days of vaccination) AND (haematological malignancy) AND (human immunodeficiency virus infection) AND (immunization) AND (immunodeficiency condition) AND (immunoglobulins) AND (immunosuppressive therapy) AND (investigational) AND (non-registered) AND (pregnancy) AND (stimulated by the vaccination) AND (study period) AND (study vaccine) AND (suspected) AND (the dose of vaccine) AND (topical corticosteroids) AND (vaccination) AND (vaccine) AND (within 30 days preceding the study vaccine) AND (within 6 months of vaccination) AND (within the last year) AND (within the three months preceding the study vaccine))"}
```
