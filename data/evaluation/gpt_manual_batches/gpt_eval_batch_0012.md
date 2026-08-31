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
{"candidate_id": "LLM00276", "doc_id": "NCT01720394_inc", "case_bucket": "or", "source_criterion": "medical indication for induction of labor 18 years of age signed informed consent cephalic presentation no PROM 37+0 - 42+0 weeks of gestation Bishop-Score = 6 no contra-indication for medical induction of labor no clinical signs of infection", "candidate_expression": "((18 years) AND (= 6) AND (Bishop-Score) AND (PROM) AND (age) AND (cephalic presentation) AND (clinical signs of) AND (contra-indication) AND (induction of labor) AND (infection) AND (medical indication) AND (medical induction of labor) AND (no) AND (signed informed consent) AND (weeks of gestation) AND ((37+0) OR (42+0)))"}
{"candidate_id": "LLM00277", "doc_id": "NCT02645474_exc", "case_bucket": "or", "source_criterion": "patients' refusal contraindication to regional anaesthesia (coagulopathies, concurrent anticoagulant therapy, allergy to local anaesthetics, infection at puncture site)", "candidate_expression": "((allergy) AND (anticoagulant therapy) AND (coagulopathies) AND (contraindication) AND (infection) AND (local anaesthetics) AND (patients' refusal) AND (puncture site) AND (regional anaesthesia ())"}
{"candidate_id": "LLM00278", "doc_id": "NCT02837783_inc", "case_bucket": "other", "source_criterion": "Patient meets protocol criteria for diagnosis of IBS-C, abdominal pain, abdominal bloating and abdominal girth", "candidate_expression": "((IBS-C protocol criteria) AND (abdominal bloating) AND (abdominal girth) AND (abdominal pain))"}
{"candidate_id": "LLM00279", "doc_id": "NCT02894372_inc", "case_bucket": "or", "source_criterion": "Patients after throat surgeries: tonsillectomy, adenotonsillectomy, uvulopalatoplasty, uvulopalatopharyngoplasty Patients with acute throat diseases: pharyngitis, tonsillitis, pharyngotonsillitis", "candidate_expression": "((acute throat diseases) AND (adenotonsillectomy) AND (pharyngitis) AND (pharyngotonsillitis) AND (throat surgeries) AND (tonsillectomy) AND (tonsillitis) AND (uvulopalatopharyngoplasty) AND (uvulopalatoplasty))"}
{"candidate_id": "LLM00280", "doc_id": "NCT01602081_inc", "case_bucket": "or", "source_criterion": "Persistent primary or recurrent trans-sphincteric anal fistula", "candidate_expression": "((trans-sphincteric anal fistula) AND ((primary) OR (recurrent)))"}
{"candidate_id": "LLM00281", "doc_id": "NCT02935855_inc", "case_bucket": "or", "source_criterion": "non-valvular atrial fibrillation nondiabetic patients type 1 and 2 diabetic patients", "candidate_expression": "((atrial fibrillation) AND (diabetic) AND (non) AND (non-valvular) AND ((type 1) OR (type 2)))"}
{"candidate_id": "LLM00282", "doc_id": "NCT01669369_exc", "case_bucket": "or", "source_criterion": "a history of non-standard treatment(chemotherapy or surgery) secondary osteosarcoma or well-differentiated parosteal osteosarcoma evident dysfunction of cardia,liver and kidney, or pregnant women or women during lactation", "candidate_expression": "((history) AND (non-standard treatment) AND ((chemotherapy) OR (surgery)) AND ((parosteal osteosarcoma well-differentiated) OR (secondary osteosarcoma)) AND ((dysfunction of cardia) OR (dysfunction of kidney) OR (dysfunction of liver) OR (lactation) OR (pregnant)))"}
{"candidate_id": "LLM00283", "doc_id": "NCT01117181_inc", "case_bucket": "or", "source_criterion": "Possible or probable Alzheimer's disease (National Institute of Neurological and Communicative Disorders and Stroke - Alzheimer's Disease and Related Disorders Association (NINCDS-ADRDA) criteria), with Mini-Mental State Exam (MMSE) score of 10-26 inclusive; MMSE scores above 26 in those who nevertheless meet criteria for AD may be allowed with Steering Committee approval on a case by case basis Clinically significant apathy for at least four weeks for which either 1) the frequency of apathy as assessed by the Neuropsychiatric Inventory (NPI) is 'Very frequently', or 2) the frequency of apathy as assessed by the NPI is 'Frequently' or 'Often' AND the severity of apathy as assessed by the NPI is 'Moderate' or 'Marked' A medication for apathy is appropriate, in the opinion of the study physician Provision of informed consent for participation in the study by patient or surrogate (if the patient is unable to provide informed consent) and caregiver Availability of primary caregiver, who spends greater than ten hours a week with the patient and supervises his/her care, to accompany the patient to study visits and to participate in the study Sufficient fluency, of both the patient and caregiver, in written and spoken English to participate in study visits, physical exams, and outcome assessments No change to AD medications within the month preceding randomization, including starting, stopping, or dosage modifications Treatment with stable doses of selective serotonin reuptake inhibitor antidepressants(SSRIs) is appropriate if stable for 3 months prior to randomization. Other psychotropics(with the exclusion of antipsychotics), if stable for 3 months, may be allowed only with Steering Committee approval on a case by case basis.", "candidate_expression": "((A medication for apathy is appropriate, in the opinion of the study physician) AND (AD) AND (AD medications) AND (Alzheimer's disease) AND (Availability of primary caregiver, who spends greater than ten hours a week with the patient and supervises his/her care, to accompany the patient to study visits and to participate in the study) AND (NPI) AND (National Institute of Neurological and Communicative Disorders and Stroke - Alzheimer's Disease and Related Disorders Association (NINCDS-ADRDA) criteria) AND (Neuropsychiatric Inventory (NPI)) AND (No) AND (Provision of informed consent for participation in the study by patient or surrogate (if the patient is unable to provide informed consent) and caregiver) AND (Sufficient fluency, of both the patient and caregiver, in written and spoken English to participate in study visits, physical exams, and outcome assessments) AND (Treatment) AND (Very frequently) AND (apathy) AND (at least four weeks) AND (change to AD medications) AND (frequency of apathy) AND (medication for apathy) AND (randomization) AND (score of 10-26 inclusive) AND (scores above 26) AND (selective serotonin reuptake inhibitor antidepressants(SSRIs)) AND (severity of apathy) AND (stable doses) AND (within the month preceding randomization) AND ((Frequently) OR (Often)) AND ((Marked) OR (Moderate)) AND ((Possible) OR (probable)) AND ((MMSE) OR (Mini-Mental State Exam (MMSE))))"}
{"candidate_id": "LLM00284", "doc_id": "NCT03217409_inc", "case_bucket": "or", "source_criterion": "Subjects = 19 or = 75 years of age Subjects undergoing treatment for type 2 diabetes Subjects undergoing treatment of statin for hypercholesterolemia Fasting LDL-C = 250mg/dL at the screening visit Fasting LDL-C =70mg/dL or = 160mg/dL at the randomization visit Fasting TG<500mg/dL", "candidate_expression": "((Fasting LDL-C = 250mg/dL at the screening visit) AND (Fasting LDL-C at the randomization visit at the randomization visit =70mg/dL = 160mg/dL) AND (Fasting TG <500mg/dL) AND (age = 19 or = 75 years) AND (hypercholesterolemia) AND (statin) AND (treatment) AND (type 2 diabetes))"}
{"candidate_id": "LLM00285", "doc_id": "NCT02584140_inc", "case_bucket": "or", "source_criterion": "Female at birth and identifies as female gender Age 18 years or older Able to understand and provide consent in English or Spanish HIV negative by 4th generation test (Ag/Ab test) or combination of enzymeimmunoassay (EIA) and HIV RNA Creatinine clearance = 60 ml/min (via Cockcroft-Gault formula) Condomless sex in the last 3 months with one or more male partners of unknown HIV status known to be at substantial risk of HIV infection (IDU, bisexual, sex for goods, recently incarcerated, from a country with HIV prevalence >1%, interpersonal Partner Violence); STI (rectal or vaginal gonorrhea or syphilis) diagnosis during the last 6 months. Previous post-exposure prophylaxis (PEP) use during the last 12 months. Has at least one HIV-infected sexual partner for =4 weeks. Sex for exchange of money, goods or services", "candidate_expression": "((18 years or older) AND (= 60 ml/min) AND (=4 weeks) AND (Able to understand and provide consent in English or Spanish) AND (Ag/Ab test) AND (Age) AND (Cockcroft-Gault formula) AND (Condomless sex) AND (Creatinine clearance) AND (EIA) AND (Female) AND (HIV 4th generation test) AND (HIV RNA) AND (HIV infection) AND (HIV-infected) AND (IDU) AND (PEP) AND (STI) AND (Sex for exchange of money, goods or services) AND (at birth) AND (at least one) AND (birth) AND (bisexual) AND (during the last 12 months) AND (during the last 6 months) AND (enzymeimmunoassay) AND (female) AND (from a country with HIV prevalence >1%) AND (gender) AND (in the last 3 months) AND (interpersonal Partner Violence) AND (male partners) AND (negative) AND (one or more) AND (post-exposure prophylaxis use) AND (recently incarcerated) AND (rectal gonorrhea) AND (sex for goods) AND (sexual partner) AND (substantial risk of HIV infection) AND (syphilis) AND (unknown HIV status) AND (vaginal gonorrhea))"}
{"candidate_id": "LLM00286", "doc_id": "NCT02871206_inc", "case_bucket": "other", "source_criterion": "Healthy children aged 6 months to 72 months", "candidate_expression": "((Healthy) AND (aged 6 months to 72 months) AND (children))"}
{"candidate_id": "LLM00287", "doc_id": "NCT02254668_exc", "case_bucket": "or", "source_criterion": "Renal insufficiency (> 265 µmol/l) Incapability to give informed consent Cardiogenic shock of patient with KILLIP III or IV pregnant or breast feeding females insufficient contraception (only for substudy 3)", "candidate_expression": "((Cardiogenic shock) AND (Incapability to give informed consent) AND (KILLIP III or IV) AND (Renal insufficiency) AND (contraception insufficient) AND (females) AND ((breast feeding) OR (pregnant)))"}
{"candidate_id": "LLM00288", "doc_id": "NCT02907554_exc", "case_bucket": "or", "source_criterion": "Contra-indication for multiorgan procurement (infections, cancer, etc) Preexistent chronic renal failure. Refusal for organ procurement by the donor (confirmed by the French national register or reported by the next-of-kin). Need for a double kidney transplantation. Need for a multiorgan transplantation", "candidate_expression": "((Contra-indication) AND (Need for) AND (Preexistent) AND (Refusal by the donor) AND (chronic renal failure) AND (double kidney transplantation) AND (multiorgan procurement) AND (multiorgan transplantation) AND (organ procurement) AND ((French national register) OR (reported by the next-of-kin)) AND ((cancer) OR (infections)))"}
{"candidate_id": "LLM00289", "doc_id": "NCT02807857_inc", "case_bucket": "other", "source_criterion": "Willing and able to provide written informed consent and accept study procedures and time schedule. Age = 18 years. Patients suffering from chronic heart failure (the heart failure diagnosis must have been made or confirmed by a cardiologist and/or hospital physician at any time in the patient's medical history). Patients with reduced ejection fraction (= 40%) as confirmed at any time point in the patient's medical history.", "candidate_expression": "((Age = 18 years) AND (Willing and able to provide written informed consent and accept study procedures and time schedule.) AND (chronic heart failure) AND (ejection fraction = 40%))"}
{"candidate_id": "LLM00290", "doc_id": "NCT00324363_inc", "case_bucket": "or", "source_criterion": "Treated with a stable dose of one of the following for at least 3 months prior to screening: * >=1000 mg/day immediate-release metformin; or metformin >=1000 mg/day and sulfonylurea; or sulfonylurea/metformin combination therapy. HbA1c between 7.1% and 11.0%, inclusive. Body Mass Index (BMI) >21 kg/m^2 and <35 kg/m^2.", "candidate_expression": "((Body Mass Index (BMI) >21 kg/m^2 and <35 kg/m^2) AND (HbA1c between 7.1% and 11.0%, inclusive) AND (metformin) AND (metformin >=1000 mg/day >=1000 mg/day) AND (sulfonylurea) AND ((combination therapy) OR (immediate-release metformin)))"}
{"candidate_id": "LLM00291", "doc_id": "NCT02571881_exc", "case_bucket": "or", "source_criterion": "age less than 18 years allergy to study drugs substance misuse other contraindication to used study drugs no informed consent", "candidate_expression": "((age less than 18 years) AND (allergy) AND (study drugs) AND ((contraindication) OR (substance misuse)))"}
{"candidate_id": "LLM00292", "doc_id": "NCT03471117_exc", "case_bucket": "or", "source_criterion": "Allergy to Glitazones Myocardial infarction Heart failure Angina History of kidney stones Liver disease (abnormal liver enzymes) Anemia (hemoglobin <8 g/dl) Cancer with current treatment Previous organ transplantation Immunosuppressant therapy Human immunodeficiency virus infection Pregnancy or lactating Current tobacco use Dilantin and oral contraceptive usage due to potential drug interaction with glitazones Self-identified history of hypoglycemia", "candidate_expression": "((Allergy) AND (Anemia) AND (Angina) AND (Cancer) AND (Dilantin) AND (Glitazones) AND (Heart failure) AND (Human immunodeficiency virus infection) AND (Immunosuppressant therapy) AND (Liver disease) AND (Myocardial infarction) AND (Pregnancy) AND (drug interaction potential) AND (glitazones) AND (hemoglobin <8 g/dl) AND (hypoglycemia Self-identified history) AND (kidney stones History) AND (lactating) AND (liver enzymes abnormal) AND (oral contraceptive) AND (organ transplantation Previous) AND (tobacco use Current) AND (treatment current))"}
{"candidate_id": "LLM00293", "doc_id": "NCT03115320_exc", "case_bucket": "or", "source_criterion": "- Irregular menstrual cycle demanding preparing endometrium with hormones for frozen-thawed embryo No frozen embryos after IVF cycle Allergy to Pregnyl® or some of its ingredients in the medication or other contraindications due to Pregnyl®", "candidate_expression": "((Allergy) AND (IVF cycle frozen embryos) AND (Irregular menstrual cycle) AND (Pregnyl) AND (contraindications) AND (preparing endometrium with hormones for frozen-thawed embryo) AND (some of its ingredients))"}
{"candidate_id": "LLM00294", "doc_id": "NCT02015494_exc", "case_bucket": "or", "source_criterion": "Use of any investigational or non-registered drug or vaccine product within 30 days preceding the administration of the study vaccine or planned use within the first six weeks of the study period Has received any licensed or other investigational influenza vaccine within 3 months prior to enrollment in this study or expected receipt of any influenza vaccination before the Day 21 blood collection History of excessive alcohol use, drug abuse or significant psychiatric illness Tobacco use within 3 months of enrollment and throughout first 6 months of the study Has a chronic illness (e.g., liver or kidney disease), receiving a concomitant therapy or have any other condition that could interfere with the subject's participation in the study or in the interpretation of the study results Clinically significant abnormal liver function tests at screening Positive serology for HBsAg, HCV or HIV antibodies Pregnant or lactating female Having cancer or have received treatment for cancer within three years (persons with a history of cancer who are disease-free without treatment for three years or more are eligible), excluding minor skin cancers, which are allowed unless located at the vaccination site Persons with impaired immune responsiveness (of any cause), including diabetes mellitus and autoimmune disorders Persons presently receiving or having a recent history of receiving (within the past six months) any medication or therapeutic modality that affects the immune system such as allergy shots, immune globulin, interferon, immunomodulators, radiation therapy, cytotoxic drugs or drugs known to be frequently associated with significant major organ toxicity, or systemic corticosteroids (oral or injectable). Inhaled and topical corticosteroids are allowed. Persons with a history of severe allergic reaction after previous vaccinations or hypersensitivity to any seasonal influenza vaccine component Persons with a history of Guillain-Barré Syndrome Receipt of blood or blood products 8 weeks prior to vaccination or planned administration during the three week study period following vaccination Donation of blood or blood products within 8 weeks prior to vaccination or during the three week study period following An oral temperature >100.4° or acute disease within 72 hours prior to vaccination, defined as the presence of a moderate or severe illness (as determined by the investigator through medical history and physical examination; for example, those requiring an absence from work) with or without fever. Body Mass Index >29.9 Any disorder of coagulation A clinical diagnosis of influenza within the previous 12 months Any other condition or circumstance which, in the opinion of the Principal Investigator, poses an unacceptable risk for participation in the study", "candidate_expression": "((Any other condition or circumstance which, in the opinion of the Principal Investigator, poses an unacceptable risk for participation in the study) AND (Body Mass Index >29.9) AND (Clinically significant) AND (Guillain-Barré Syndrome) AND (Tobacco use within 3 months of enrollment throughout first 6 months of the study) AND (any other condition could interfere with the subject's participation in the study) AND (cancer) AND (cancer history) AND (chronic illness) AND (disease-free) AND (disorder of coagulation) AND (female) AND (impaired immune responsiveness) AND (influenza within the previous 12 months) AND (liver function tests Clinically significant abnormal at screening) AND (seasonal influenza vaccine component) AND (therapy concomitant) AND NOT (treatment for three years or more) AND ((drug) OR (vaccine product)) AND ((Receipt of blood) OR (Receipt of blood products)) AND ((8 weeks prior to vaccination vaccination) OR (planned administration during the three week study period following vaccination)) AND ((Donation of blood) OR (Donation of blood products)) AND ((during the three week study period the three week study period) OR (within 8 weeks prior to vaccination vaccination)) AND ((acute disease) OR (oral temperature >100.4°)) AND ((moderate illness) OR (severe illness)) AND ((licensed) OR (other investigational)) AND ((any influenza vaccination expected receipt before the Day 21) OR (influenza vaccine within 3 months prior to enrollment in this study)) AND ((drug abuse) OR (excessive alcohol use) OR (psychiatric illness significant)) AND ((investigational) OR (non-registered)) AND ((kidney disease) OR (liver disease)) AND ((HBsAg antibodies) OR (HCV antibodies) OR (HIV antibodies)) AND ((Pregnant) OR (lactating)) AND ((within 30 days preceding the administration of the study vaccine the administration of the study vaccine) OR (within the first six weeks of the study period planned use the study period)) AND ((cancer) OR (treatment for cancer)) AND ((autoimmune disorders) OR (diabetes mellitus)) AND ((any medication) OR (therapeutic modality)) AND ((allergy shots) OR (cytotoxic drugs) OR (drugs known to be frequently associated with significant major organ toxicity known to be frequently associated with significant major organ toxicity) OR (immune globulin) OR (immunomodulators) OR (interferon) OR (radiation therapy) OR (systemic corticosteroids)) AND ((injectable) OR (oral)) AND ((allergic reaction history severe after previous vaccinations) OR (hypersensitivity to any seasonal influenza vaccine component)))"}
{"candidate_id": "LLM00295", "doc_id": "NCT02566226_exc", "case_bucket": "other", "source_criterion": "planned surgical duration more than 3 hours contraindication to spinal anaesthesia severe respiratory disease patient known and treated for sleep apnea syndrome", "candidate_expression": "((contraindication) AND (more than 3 hours) AND (planned surgical duration) AND (respiratory disease) AND (severe) AND (sleep apnea syndrome) AND (spinal anaesthesia) AND (treated))"}
{"candidate_id": "LLM00296", "doc_id": "NCT00943865_inc", "case_bucket": "or", "source_criterion": "men and women 30-55 years with BMI 30-40 and waist 95 cm or more normal OGTT normal treadmill stress test plus 2 of 4: 1. low serum levels of HDL cholesterol (<40 mg⁄dL for men or < 50 mg ⁄dL for women); 2. hypertriglyceridemia (triglyceride levels of 150 mg⁄dL or greater); 3. impaired glucose homeostasis (fasting plasma glucose concentration of 110 mg⁄dL or greater or glucose of 140 mg⁄dL or greater after OGTT or 4. hypertension (systolic blood pressure ≥ 140 or diastolic blood pressure ≥90 mmHg or treatment with antihypertensive drugs).", "candidate_expression": "((30-55 years 30-55 years) AND (BMI 30-40) AND (OGTT after OGTT OGTT) AND (OGTT normal) AND (antihypertensive drugs) AND (diastolic blood pressure ≥90 mmHg) AND (fasting plasma glucose concentration 110 mg⁄dL or greater) AND (glucose 140 mg⁄dL or greater after OGTT) AND (hypertension) AND (hypertriglyceridemia) AND (impaired glucose homeostasis) AND (men) AND (men <40 mg⁄dL) AND (serum levels of HDL cholesterol low) AND (systolic blood pressure ≥ 140) AND (treadmill stress test normal 2 of 4) AND (treatment) AND (triglyceride levels 150 mg⁄dL or greater) AND (waist 95 cm or more) AND (women) AND (women < 50 mg ⁄dL))"}
{"candidate_id": "LLM00297", "doc_id": "NCT02704754_exc", "case_bucket": "or", "source_criterion": "Psychiatric disorders other than insomnia, PTSD and specific phobias; including bipolar and psychotic disorders and meeting criteria for DSM-5 moderate alcohol or drug use disorders within the past year. Diagnosis of a sleep disorder other than insomnia including PSG findings of apnea/hypopnea or periodic limb movement indices > 10/hour; Medical conditions that require consistent use of medication or compromise sleep; History of moderate to severe traumatic brain injury or mild traumatic brain injury with ongoing post-concussive symptoms; Suicidal ideation with intent to act or with specific plan and intent in the past 6 months (Type 4 - 5 ideation on the Columbia Suicide Severity Rating Scale) or a concerning history of prior suicidal behavior. Caffeine use exceeding 5 cups of coffee per day or its equivalent; Habitual bedtimes after 3 AM, habitual rise times after 10 AM, or habitual napping > 1hour/day; Pregnancy or breastfeeding, or expecting to conceive while in study; Positive urine toxicology.", "candidate_expression": "((Caffeine) AND (Columbia Suicide Severity Rating Scale Type 5 ideation Type 4 ideation) AND (PSG) AND (PTSD) AND (Pregnancy or breastfeeding, or expecting to conceive while in study) AND (Psychiatric disorders) AND (Suicidal ideation past 6 months) AND (alcohol use disorders) AND (apnea) AND (bipolar) AND (drug use disorders) AND (hypopnea) AND (insomnia) AND (periodic limb movement indices > 10/hour) AND (phobias) AND (post-concussive symptoms) AND (psychotic disorders) AND (sleep disorder) AND (suicidal behavior.) AND (traumatic brain injury mild) AND (traumatic brain injury moderate severe) AND (urine toxicology Positive) AND NOT (insomnia))"}
{"candidate_id": "LLM00298", "doc_id": "NCT03397914_exc", "case_bucket": "or", "source_criterion": "Age less than one year or over 18 years Patients with renal impairment Colistin use less than 72 hours", "candidate_expression": "((Age) AND (Colistin less than 72 hours) AND (renal impairment) AND ((less than one year) OR (over 18 years)))"}
{"candidate_id": "LLM00299", "doc_id": "NCT02731794_inc", "case_bucket": "other", "source_criterion": "patients with severe left ventricle dysfunction with an ejection fraction (EF)=40%, being scheduled for revascularization.", "candidate_expression": "((=40%) AND (being scheduled for) AND (ejection fraction (EF)) AND (left ventricle dysfunction) AND (revascularization) AND (severe))"}
{"candidate_id": "LLM00300", "doc_id": "NCT03288428_exc", "case_bucket": "other", "source_criterion": "can't understand patient controlled analgesia device refuse trial", "candidate_expression": "(can't understand patient controlled analgesia device refuse trial)"}
```
