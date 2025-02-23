This is the code of this paper **Quantifying Novelty in Scientific Research Paper: A Logistical Structure-Based Approach**

	Project Structure
	├─ Analyse                 Novelty measurement effect verification
	│    ├─ EDA.ipynb          Descriptive statistics of data distribution
	│    ├─ Preprocess.ipynb   Adjust and process the format of novelty measurement results and gold standard data
	│    ├─ RobustCheck.ipynb  Robustness analysis of research conclusions
	│    ├─ Validate.ipynb     Verify the effectiveness of the proposed method
	│    ├─ base_data          The novelty score data of the papers under various methods after processing
	│    │    ├─ compare_sec
	│    │    ├─ compare_specific_sec
	│    │    └─ overview
	│    ├─ gold_standard       Gold standard dataset (only the final processing results are retained)
	│    ├─ robust              Results of the robustness test
	├─ CalNovelty               Calculating the novelty of papers
	│    ├─ construct_cooc.py   Obtaining journal combinations in papers using the Uzzi method
	│    ├─ fast_uzzi_novel.py  Calculating the novelty of papers using the Uzzi's method
	│    ├─ lib                 Novelty calculation library (modified from novelpy library)
	│    │    └─ fastnovelpy
	│    ├─ norm_sec.ipynb      Calculate novelty of specific sections in a paper
	│    └─ self_wang_novel.py  Calculating the novelty of papers using the Wang's method
	├─ Preprocess
	│    ├─ cal_distance.py     Standardization of journal names--based on edit distance algorithm
	│    ├─ crawl_abbr.py       Standardization of journal names--crawl the abbreviations corresponding to journals
	│    ├─ data                Data generated during the process of journal name standardization
	│    │    ├─ close_form_journal.csv
	│    │    ├─ close_form_journal.json
	│    │    └─ standard_journals.csv
	│    ├─ get_refer_name.py   Get the journal names of all references
	│    ├─ norm_refer.py       Standardization of journal names
	│    ├─ norm_refer_check.py Check the effect of the journal name standardization process
	│    ├─ norm_sec.ipynb      Standardize chapter names in papers
	│    ├─ parse.py            Parse the XML file in plos to obtain the specific content information of the paper
	│    └─ preprocess_refer.py Construct journal combination data within papers both at the paper level and the chapter level, and store them by year.
	└─ readme.MD

Novelty is an important dimension for measuring the innovativeness and research value of academic work. Identifying highly novel research from a vast number of academic papers helps to update knowledge and promote scientific and technological development. Existing studies on measuring novelty primarily focus on exploring the use of different knowledge units, such as references and entities, to represent knowledge, and applying various methods to optimize the measurement results. However, they overlook the fact that these knowledge units are embedded within the logical structure of a paper. According to relevant theories in linguistics, such as Rhetorical Structure Theory (RST) and Move Analysis, the way knowledge is organized and connected within a paper is critical for understanding and analyzing the paper itself.

Therefore, this study incorporates the textual structure information of papers into novelty measurement. We treat the journals of references as knowledge units within the paper and construct journal pair combinations based on their co-occurrence in the sections of a paper. Two classic novelty measurement methods (Uzzi and Wang) are then employed to calculate the novelty of journal pairs and papers. The effectiveness of these methods is validated by comparing the results with expert assessments of paper novelty.

The results show that when using the Uzzi method, incorporating the textual structure of papers can accurately distinguish between expert-identified novel and non-novel papers, and the explanatory power of the measurement indicators is stronger compared to when this information is not considered. However, the Wang method fails to accurately identify novel papers both before and after incorporating textual structure information.

We also compared the relationship between the novelty of different sections and the overall novelty of a paper and conducted an in-depth analysis of the evaluation results from the two novelty measurement methods. This provides a basis for selecting appropriate measurement methods according to specific research scenarios in future studies.

## Citation
Please cite the following paper if you use these codes and datasets in your work.

> Yi Xiang, Yi Zhao, Chengzhi Zhang\*. Quantifying Novelty of Scientific Research Publications: An Approach Integrating Discourse Structure. ***Journal of the Association for Information Science and Technology***, 2025.（submitted)  [[Dataset & Source Code]](https://github.com/xiangyi-njust/ChapNovelty)
