import json
import multiprocessing
import pandas as pd
from tqdm import tqdm
import time
import os
import re

vowels = ['a', 'e', 'i', 'o', 'u']
func_words = ['The', 'of', 'the', 'on', 'from', 'to']
word_to_abbr = {}
title_to_abbr = {}
issn_word_to_abbr = None
old_source_to_new = {}

def load_data():
    print("load plos data")
    df_source = pd.read_csv('data/refer_source.csv')
    sources = df_source['Refer_Source'].tolist()
    sources = list(set(sources))

    new_sources = []
    old_to_new = {}
    for source in sources:
        if type(source) != str:
            continue
        if "rxiv" in source.lower():
            continue
        if source.count(".") == 1:
            source = source[:source.find(".")]
        if source.count(":") == 1:
            source = source[:source.find(":")]
        source.replace("&", "and")
        result = re.sub(r'\.|\(.*?\)|\"', '', source)
        new_sources.append(result.strip())
        old_to_new[source] = result.strip()

    print("load wos data")
    df = pd.read_csv("data/standard_journals.csv")
    standard_journal_titles = df['Source'].tolist()

    print("load issn data")
    raw_word_to_abbr = {}
    with open("data/issn_ltwa/ltwa_current.csv", 'r', encoding='utf-8') as f:
        datas = f.readlines()
    for data in datas:
        elems = data.split('\t')
        raw_word_to_abbr[elems[0]] = elems[1]

    return new_sources, standard_journal_titles, raw_word_to_abbr, old_to_new


def generate_abbreviation(title):
    # 首字母缩写： British Medical Journal   BMJ
    result = None
    try:
        words = title.strip().split(" ")
        if len(words) == 1:
            result = title
        else:
            # 根据ISSN表对标题中的词语进行缩写
            issn_words = []
            for word in words:
                if word in issn_word_to_abbr:
                    issn_words.append(issn_word_to_abbr[word])
                elif word.lower() in issn_word_to_abbr:
                    issn_words.append(issn_word_to_abbr[word.lower()])
                elif word[0].upper() + word[1:] in issn_word_to_abbr:
                    issn_words.append(issn_word_to_abbr[word[0].upper() + word[1:]])
                else:
                    issn_words.append(word)
            abbr_0 = " ".join(issn_words)

            # 首字母缩写
            word_list = [word[0] for word in words]
            abbr_1 = "".join(word_list)

            # 去掉虚词后的首字母缩写
            new_word_list = []
            for word in words:
                if word in func_words:
                    continue
                else:
                    new_word_list.append(word[0])
            abbr_2 = "".join(new_word_list)

            # 去掉虚词并将词语部分缩写
            new_word_list = []
            for word in words:
                if word in func_words or len(word) <= 5:
                    new_word_list.append(word)
                    continue
                if word in word_to_abbr:
                    new_word_list.append(word_to_abbr[word])
                elif word[-3:] == 'ogy' or word[-3:] == 'ics':
                    new_word_list.append(word[:-3])
                    word_to_abbr[word] = word[:-3]
                elif word[-3:] == 'try':
                    new_word_list.append(word[:-5])
                    word_to_abbr[word] = word[:-5]
                else:
                    min_idx = 100
                    for vowel in vowels:
                        idx = word.find(vowel)
                        if idx != -1 and idx != 0 and idx < min_idx:
                            min_idx = idx
                    new_word_list.append(word[:min_idx])
                    word_to_abbr[word] = word[:min_idx]

            abbr_3 = " ".join(new_word_list)

            abbr_4 = title.replace("and", "&")
            abbr_5 = title.replace("&", "and")

            abbr_6 = "Journal of " + title

            result = [abbr_0, abbr_1, abbr_2, abbr_3, abbr_4, abbr_5, abbr_6]
    except Exception as e:
        print(f"{e}")

    return result


def generate_abbreviation_based_nlm():
    """
        1. 从nlm官网上爬取了每种标准期刊对应的缩写名称，所以可根据原始名称和缩写名称同时去standard journals寻找匹配
        2. 根据边际距离匹配了每一名称对应的最近的缩写，如果一种名称找不到对应的，可能是因为拼写错误问题，此时可基于
           边际距离匹配与其最近邻的名称对应的期刊 （这个应该在norm_refer的过程中使用，不是在此处）
    """
    path = 'data/nlm/results.json'
    with open(path, 'r') as f:
        datas = json.load(f)
    
    new_datas = {}
    for raw_title in datas:
        new_datas[raw_title] = [raw_title, datas[raw_title]]
    
    new_datas = json.dumps(new_datas, indent=4)
    with open('data/abbreviation_nlm.json', 'w') as f:
        f.write(new_datas)


def check_data(unstan_sources, stan_sources):
    stan_sources = set(stan_sources)
    results = []
    for source in tqdm(unstan_sources):
        if source in stan_sources:
            results.append(True)
        else:
            results.append(False)

    assert len(results) == len(unstan_sources)
    print(results.count(True))


def check_un_unique_data(sub_a, b_set):
    return sum(1 for elem in sub_a if elem in b_set)


def check_data_aug_edit_distance(unstan_sources, stan_sources):
    with open('data/close_form_journal.json', 'r') as f:
        word_to_close_form = json.load(f)

    stan_sources = set(stan_sources)
    results = []
    for source in tqdm(unstan_sources):
        if source in stan_sources:
            results.append(True)
        elif source in word_to_close_form and len(word_to_close_form[source]) != 0:
            close_forms = word_to_close_form[source]
            for form in close_forms:
                if form in stan_sources:
                    results.append(True)
                    break
        else:
            results.append(False)
    
    print(results.count(True))
            

def check_un_unique_data_aug_edit_distance(sub_a, b_set):
    with open('data/close_form_journal.json', 'r') as f:
        word_to_close_form = json.load(f)

    results = []
    for source in tqdm(sub_a):
        if source in b_set:
            results.append(True)
        elif source in word_to_close_form and len(word_to_close_form[source]) != 0:
            close_forms = word_to_close_form[source]
            for form in close_forms:
                if form in b_set:
                    results.append(True)
                    break
        else:
            results.append(False)
    
    return results.count(True)


def remove_low_freq(res_dict, unstan_sources):
    transfer_journals = []
    unstand_to_stand = {}
    error_journals = []
    match_journals = []

    for res in res_dict:
        if res_dict[res] is not None:
            for value in res_dict[res]:
                unstand_to_stand[value] = res
            unstand_to_stand[res] = res

    unstan_sources = list(set(unstan_sources))

    for source in tqdm(unstan_sources):
        old_source = source
        # if len(source.split()) >= 10:
        #     continue
        if source not in unstand_to_stand:
            error_journals.append(source)
        else:
            match_journals.append(old_source)
            transfer_journals.append(unstand_to_stand[source])

    df = pd.DataFrame()
    df['Error Source'] = list(set(error_journals))
    df.to_csv("data/error_journal.csv", index=False)

    df = pd.DataFrame()
    df['MATCH Source'] = list(set(match_journals))
    df.to_csv("data/match_journal.csv", index=False)

    print(len(unstan_sources))
    print(len(error_journals))


def init_pool_processes(shared_dict_instance):
    global issn_word_to_abbr
    issn_word_to_abbr = shared_dict_instance


def init_pool_processes_check(shared_dict_instance):
    global old_source_to_new
    old_source_to_new = shared_dict_instance


if __name__ == '__main__':
    print("-------------------load data-----------------")
    unstandard_sources, standard_journals, raw_word_to_abbr, old_to_new = load_data()

    print("-------------------check data----------------")
    check_data(unstandard_sources, standard_journals)

    print("-------------------norm data-----------------")
    # with multiprocessing.Manager() as manager:
    #     res_dict = {}
    #     issn_word_to_abbr = manager.dict(raw_word_to_abbr)
    #     pool = multiprocessing.Pool(processes=multiprocessing.cpu_count(),
    #                                 initializer=init_pool_processes,
    #                                 initargs=(issn_word_to_abbr,))
    #     results = pool.map(generate_abbreviation, standard_journals)

    #     pool.close()
    #     pool.join()

    # for idx, source in enumerate(standard_journals):
    #     res_dict[source] = results[idx]

    # res_dict = json.dumps(res_dict, indent=4)
    # with open("data/abbreviation.json", "w") as f:
    #     f.write(res_dict)

    # generate_abbreviation_based_nlm()

    print("------------------check data-----------------")
    res_dict = {}
    if os.path.exists("data/abbreviation_nlm.json"):
        with open("data/abbreviation_nlm.json", "r") as f:
            res_dict = json.load(f)
    for res in res_dict:
        if res_dict[res] is not None and res_dict[res] != res:
            standard_journals.extend(res_dict[res])

    check_data(unstandard_sources, standard_journals)
    
    if os.path.exists("data/abbreviation.json"):
        with open("data/abbreviation.json", "r") as f:
            res_dict = json.load(f)
    for res in res_dict:
        if res_dict[res] is not None and res_dict[res] != res:
            standard_journals.extend(res_dict[res])

    check_data(unstandard_sources, standard_journals)
    check_data_aug_edit_distance(unstandard_sources, standard_journals)

    print("------------------check data-----------------")
    b_set = set(standard_journals)
    df = pd.read_csv('data/refer_source.csv')
    sources = df['Refer_Source'].tolist()

    num_workers = multiprocessing.cpu_count()
    chunk_size = int(len(sources)/num_workers)
    chunks = []
    for i in range(num_workers):
        if (i+1)*chunk_size > len(sources):
            chunks.append(sources[i * chunk_size:])
            break
        else:
            chunks.append(sources[i * chunk_size:(i + 1) * chunk_size])

    with multiprocessing.Manager() as manager:
        old_source_to_new = manager.dict(old_to_new)
        pool = multiprocessing.Pool(processes=num_workers,
                                    initializer=init_pool_processes_check,
                                    initargs=(old_source_to_new,))
        
        # results = pool.starmap(check_un_unique_data_aug_edit_distance, [(chunk, b_set) for chunk in chunks])
        results = pool.starmap(check_un_unique_data, [(chunk, b_set) for chunk in chunks])

    cnt = sum(results)
    print(f'number: {cnt}  percentage: {cnt/len(sources)}')

    # print("----------remove low frequency data---------")
    # remove_low_freq(res_dict, unstandard_sources)
