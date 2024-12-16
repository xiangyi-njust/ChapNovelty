import os
import json
import pandas as pd
from tqdm import tqdm
import threading


doi_miss_refer = []
file_miss_refer = []
doi_miss_mesh = []
file_miss_mesh = []


def call_parse(path, names, part_name):
    for name in tqdm(names, desc=part_name):
        # check_refer(name, path)
        check_mesh(name, path)


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


def process_in_threads(file_dicts, path):
    threads = []

    for part_name in file_dicts.keys():
        thread = threading.Thread(target=call_parse, args=(path, file_dicts[part_name], part_name))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


def check_refer(name, path):
    file = os.path.join(path, name)
    if os.path.exists(file):
        with open(file, 'r') as f:
            data = json.load(f)

        references = data['reference']
        if len(references) == 0:
            os.remove(file)
            doi_miss_refer.append(data['doi'])
            file_miss_refer.append(name)


def check_mesh(name, path):
    file = os.path.join(path, name)
    if os.path.exists(file):
        with open(file, 'r') as f:
            data = json.load(f)

        references = data['mesh']
        if len(references) == 0:
            os.remove(file)
            doi_miss_refer.append(data['doi'])
            file_miss_refer.append(name)    


if __name__ == '__main__':
    # in_path = '../../data/plos/'
    in_path = '../../data/plos_mesh/'
    filenames = os.listdir(in_path)

    part_files = split_filenames(filenames, 10)
    process_in_threads(part_files, in_path)

    df = pd.DataFrame()
    # df['DOI'] = doi_miss_refer
    # df['FILE_NAME'] = file_miss_refer
    # df.to_csv("../../data/plos_miss_refer.csv", index=False)
    df['DOI'] = doi_miss_mesh
    df['FILE_NAME'] = file_miss_mesh
    df.to_csv("../../data/plos_miss_mesh.csv", index=False)
