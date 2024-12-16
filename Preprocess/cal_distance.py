import multiprocessing
import pandas as pd
import re
from tqdm import tqdm
import Levenshtein

journal_pairs = []


def cal_edit_distance(journal):
    distance_dict = {}
    if type(journal) == float:
        pass
    else:
        for jdx, pair_j in enumerate(journal_pairs):
            if journal != pair_j:
                distance = Levenshtein.distance(journal, pair_j)
                distance_dict[jdx] = distance
    sorted_dict = sorted(distance_dict.items(), key=lambda item: item[1])

    return journal, sorted_dict[0], sorted_dict[1]


def init_pool_process(shared_pairs):
    global journal_pairs
    journal_pairs = shared_pairs


def load_data():
    df = pd.read_csv("data/refer_source.csv")
    sources = df['Refer_Source'].tolist()
    sources = list(set(sources))

    new_sources = []
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

    return list(set(new_sources))


if __name__ == '__main__':
    sources = load_data()
    sources = sources[600000:]
    min_pos = []

    print("start calculate edit distance")

    with multiprocessing.Manager() as manager:
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count(),
                                    initializer=init_pool_process,
                                    initargs=(sources,))
        with tqdm(total=len(sources)) as progress_bar:
            for result in pool.imap_unordered(cal_edit_distance, sources):
                min_pos.append(result)
                progress_bar.update(1)

        pool.close()
        pool.join()

    raw_sources, pair_distances, pair_sources, second_pair_distances, second_pair_sources = [], [], [], [], []
    for pos in min_pos:
        raw_sources.append(pos[0])
        pair_distances.append(pos[1][1])
        pair_sources.append(sources[pos[1][0]])
        second_pair_distances.append(pos[2][1])
        second_pair_sources.append(sources[pos[2][0]])

    df = pd.DataFrame()
    df['Raw J'] = raw_sources
    df['New D'] = pair_distances
    df['New J'] = pair_sources
    df['New D Second'] = second_pair_distances
    df['New J Second'] = second_pair_sources
    df.to_csv("data/abbr_2.csv", index=False)
