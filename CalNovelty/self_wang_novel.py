import json
import itertools
import numpy as np
from tqdm import tqdm
import os
from collections import Counter
import multiprocessing

paper_directory = 'sec_level_nomarlize_remove_unmatch'
all_combinations, all_journals = [], []
past_combinations, curr_combinations, future_combinations = [], [], []
past_journals = []
combination_to_id = {}
set_past_combinations = None


def get_paper_items(year, window=None, past=False):
    if window is not None:
        if past:
            for past_year in range(year - window, year):
                path = f'../../Data/docs/{paper_directory}/{past_year}.json'
                with open(path, 'r') as f:
                    docs = json.load(f)

            for doc in docs:
                refer_data = doc['reference']
                j_list = [data['source'] for data in refer_data]
                j_list = list(set(j_list))
                past_journals.extend(j_list)
                all_journals.extend(j_list)
                j_combination = itertools.combinations(j_list, r=2)
                past_combinations.extend(list(set(j_combination)))
        else:
            for future_year in range(year, year + window):
                path = f'../../Data/docs/{paper_directory}/{future_year}.json'
                with open(path, 'r') as f:
                    docs = json.load(f)

            for doc in docs:
                refer_data = doc['reference']
                j_list = [data['source'] for data in refer_data]
                j_list = list(set(j_list))
                all_journals.extend(j_list)
                j_combination = itertools.combinations(j_list, r=2)
                future_combinations.extend(list(set(j_combination)))
    else:
        path = f"../../Data/docs/{paper_directory}/{year}.json"
        with open(path, 'r') as f:
            docs = json.load(f)

        paper_combinations = {}
        for doc in docs:
            refer_data = doc['reference']
            j_list = [data['source'] for data in refer_data]
            j_list = list(set(j_list))
            all_journals.extend(j_list)
            j_combination = itertools.combinations(j_list, r=2)
            j_combination = list(set(j_combination))
            paper_combinations[doc['doi']] = {
                'combination': j_combination,
                'combination_index': None
            }
            curr_combinations.extend(j_combination)

        return paper_combinations


def convert_journal_to_id(combinations):
    converted_combinations = []
    for combination in combinations:
        j1, j2 = combination
        if journal_to_id[j1] > journal_to_id[j2]:
            converted_combinations.append((journal_to_id[j2], journal_to_id[j1]))
        else:
            converted_combinations.append((journal_to_id[j1], journal_to_id[j2]))

    return converted_combinations


def construct_history_occur_matrix(dimension):
    journal_vector = np.zeros(shape=(dimension, dimension))
    for journal in past_combinations:
        journal_vector[journal[0], journal[1]] += 1
        journal_vector[journal[1], journal[0]] += 1

    # dot_product = np.dot(journal_vector, journal_vector.T)
    # norms = np.linalg.norm(journal_vector, axis=1)
    # cosine_similarity_matrix = dot_product / np.outer(norms, norms)

    curr_sims = {}
    for combination in curr_combinations:
        j1_idx, j2_idx = combination
        j1_vector = journal_vector[j1_idx, :]
        j2_vector = journal_vector[j2_idx, :]
        if np.linalg.norm(j1_vector) != 0 and np.linalg.norm(j2_vector) != 0:
            sim = np.dot(j1_vector, j2_vector) / (np.linalg.norm(j1_vector) * np.linalg.norm(j2_vector))
            curr_sims[combination] = 1 - sim
        else:
            curr_sims[combination] = 0.0

    return curr_sims


def init_process(shared_comb_to_id, shared_past_combs, shared_future_combs):
    global combination_to_id, past_combinations, future_combinations
    combination_to_id = shared_comb_to_id
    past_combinations = shared_past_combs
    future_combinations = shared_future_combs


def filter_combination(part_combinations):
    filter_part_combinations = {}
    set_past_combinations = set(past_combinations)
    for doi in tqdm(part_combinations):
        combinations = part_combinations[doi]['combination']
        filter_combination_index = []
        for combination in combinations:
            combination_id = combination_to_id[combination]
            # 根据wang的论文，只有在过去年份中出现过一定次数的期刊才能被考虑进来
            # 但当前研究中不像wang那样涵盖了全样本，因此不太适合用该方式
            # if combination_id[0] not in past_journals or combination_id[1] not in past_journals:
            #     continue
            # 根据wang的论文，只有既在过去从未出现，又在未来至少出现一次的组合才计算
            if combination_id not in set_past_combinations and combination_id in future_combinations:
                filter_combination_index.append(combination_id)

        curr_combinations.extend(filter_combination_index)
        filter_part_combinations[doi] = {}
        filter_part_combinations[doi]['combination_index'] = filter_combination_index

    return filter_part_combinations


if __name__ == '__main__':
    time_window = 3
    percentage_j = 0

    for year in tqdm(range(2006, 2022)):
        focal_year = year

        all_combinations, all_journals = [], []
        past_combinations, curr_combinations, future_combinations = [], [], []
        past_journals = []
        combination_to_id = {}
        set_past_combinations = None

        paper_combinations = get_paper_items(focal_year)
        get_paper_items(focal_year, time_window, past=True)
        get_paper_items(focal_year, time_window, past=False)

        journal_to_id = {}
        all_journals = list(set(all_journals))
        for idx, journal in enumerate(all_journals):
            journal_to_id[journal] = idx

        # 期刊名称序号化处理
        past_combinations = convert_journal_to_id(past_combinations)
        future_combinations = set(convert_journal_to_id(future_combinations))
        curr_combinations = list(set(curr_combinations))
        converted_curr_combinations = convert_journal_to_id(curr_combinations)
        combination_to_id = {curr_combinations[i]: converted_curr_combinations[i]
                             for i in range(len(curr_combinations))}

        # 构建在过去n年中出现一定次数的期刊列表
        curr_combinations = []
        past_journal_count = Counter(past_journals)
        j_cnt = [past_journal_count[item] for item in past_journal_count]
        # 默认从小到大排列
        percentile = np.percentile(j_cnt, percentage_j)
        past_journals = [item for item in past_journal_count if past_journal_count[item] >= percentile]
        past_journals = list(set(past_journals))

        doc_combinations = filter_combination(paper_combinations)
        # # 拆分原始字典
        # chunk_size = int(len(paper_combinations)/multiprocessing.cpu_count())
        # remainder = len(paper_combinations) % multiprocessing.cpu_count()
        # it = iter(paper_combinations.items())
        # chunks = []
        # for i in range(multiprocessing.cpu_count()):
        #     current_size = chunk_size + (1 if i < remainder else 0)
        #     current_dict = dict(itertools.islice(it, current_size))
        #     chunks.append(current_dict)
        #
        # # 使用多进程过滤数据
        # with multiprocessing.Manager() as manager:
        #     comb_to_id = manager.dict(combination_to_id)
        #     past_comb = manager.list(past_combinations)
        #     future_comb = manager.list(future_combinations)
        #     pool = multiprocessing.Pool(processes=multiprocessing.cpu_count(),
        #                                 initializer=init_process,
        #                                 initargs=(comb_to_id,
        #                                           past_comb,
        #                                           future_comb
        #                                           ))
        #     results = pool.starmap(filter_combination, chunks)
        # doc_combinations = {}
        # for part_combinations in results:
        #     doc_combinations.update(part_combinations)

        # 计算组合新颖性
        future_combinations, combination_to_id = None, None
        curr_combinations = list(set(curr_combinations))
        curr_sims = construct_history_occur_matrix(len(all_journals))

        # 计算论文新颖性
        doc_novelty = {}
        for doi in doc_combinations:
            combinations = doc_combinations[doi]['combination_index']
            combination_novelty = [curr_sims[combination] for combination in combinations]
            doc_novelty[doi] = np.sum(combination_novelty)

        # save result
        doc_novelty = json.dumps(doc_novelty, indent=4)
        output_path = f'Result/fast_wang_sec/reference'
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        with open(f'{output_path}/{focal_year}.json', 'w') as f:
            f.write(doc_novelty)
