from tqdm import tqdm
import threading
import os
import json
import pandas as pd

refer_id_to_source = {}


def get_refer_info(filename):
    with open(filename, 'r') as f:
        datas = json.load(f)

    refer_list = datas['reference']
    for refer in refer_list:
        if refer['id'] not in refer_id_to_source:
            refer_id_to_source[refer['id']] = []
        refer_id_to_source[refer['id']].append(refer['source'])


def call_parse(names, part_name):
    for name in tqdm(names, desc=part_name):
        get_refer_info(name)


def split_filenames(files, k):
    file_parts = {}
    part_length = int(len(files) / k)
    for i in range(k + 1):
        part_name = 'part_{}'.format(i)
        if (i + 1) * part_length > len(files):
            part_files = files[i * part_length:]
        else:
            part_files = files[i * part_length:(i + 1) * part_length]
        file_parts[part_name] = part_files

    return file_parts


def process_in_threads(file_dicts):
    threads = []

    for part_name in file_dicts.keys():
        thread = threading.Thread(target=call_parse, args=(file_dicts[part_name], part_name))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == '__main__':
    input_path = '../../data/plos'
    filenames = os.listdir(input_path)
    filenames = [os.path.join(input_path, filename) for filename in filenames]

    part_filenames = split_filenames(filenames, 8)

    process_in_threads(part_filenames)

    ids = list(refer_id_to_source.keys())
    multi_sources = list(refer_id_to_source.values())
    sources = [source[0] for source in multi_sources]

    df = pd.DataFrame()
    df['Refer_ID'] = ids
    df['Refer_Source'] = sources
    df.to_csv('data/refer_source.csv', index=False)

    with open('data/refer_id_to_source.json', 'w') as f:
        json.dump(refer_id_to_source, f)
