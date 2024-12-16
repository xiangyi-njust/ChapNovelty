import os
import re
from tqdm import tqdm
import pickle
import numpy as np
import pandas as pd
from random import sample
from sklearn import preprocessing
from itertools import combinations
from scipy import sparse
from scipy.sparse import triu, lil_matrix
from ..utils.run_indicator_tools import create_output
import threading
import multiprocessing

"""
    threading 多线程 适合I/O密集型任务
    mutiprocessing 多进程 适合CPU密集型任务
"""

pd.options.mode.chained_assignment = None

adjacency_unique_items = None
adjacency_adj_mat = None


def init_get_adjacency_matrix_parallel(unique_items, adj_mat):
    global adjacency_unique_items, adjacency_adj_mat
    adjacency_unique_items = unique_items
    adjacency_adj_mat = adj_mat


def get_adjacency_matrix_parallel(sub_items):
    for old_item in sub_items:
        new_item = []
        for item in old_item:
            if type(item) == str:
                new_item.append(item)
        item = new_item

        for combi in list(combinations(item, r=2)):
            combi = sorted(combi)
            ind_1 = adjacency_unique_items[combi[0]]
            ind_2 = adjacency_unique_items[combi[1]]
            adjacency_adj_mat[ind_1, ind_2] += 1
            if ind_1 != ind_2:
                adjacency_adj_mat[ind_2, ind_1] += 1


def get_adjacency_matrix(unique_items,
                         items_list,
                         unique_pairwise,
                         keep_diag):
    if unique_pairwise:
        lb = preprocessing.MultiLabelBinarizer(classes=sorted(list(unique_items.keys())))
        dtm_mat = lil_matrix(lb.fit_transform(items_list))
        adj_mat = dtm_mat.T.dot(dtm_mat)
    else:
        adj_mat = lil_matrix((len(unique_items.keys()), len(unique_items.keys())), dtype=np.uint32)

        # 2024/10/15 multiprocess code
        # num_workers = multiprocessing.cpu_count()
        # chunk_size = int(len(items_list) / num_workers)
        # chunks = []
        # for i in range(num_workers):
        #     start = i * chunk_size
        #     end = start + chunk_size
        #     if end > len(items_list):
        #         chunks.append(items_list[start:])
        #     else:
        #         chunks.append(items_list[start:end])
        #
        # with multiprocessing.Manager() as manager:
        #     pool = multiprocessing.Pool(processes=num_workers,
        #                                 initializer=init_get_adjacency_matrix_parallel,
        #                                 initargs=(unique_items, adj_mat))
        #     pool.starmap(get_adjacency_matrix_parallel, [chunk for chunk in chunks])

        # source code
        for old_item in items_list:
            new_item = []
            for item in old_item:
                if type(item) == str:
                    new_item.append(item)
            item = new_item

            for combi in list(combinations(item, r=2)):
                combi = sorted(combi)
                ind_1 = unique_items[combi[0]]
                ind_2 = unique_items[combi[1]]
                adj_mat[ind_1, ind_2] += 1
                if ind_1 != ind_2:
                    adj_mat[ind_2, ind_1] += 1

    adj_mat = lil_matrix(adj_mat)
    if not keep_diag:
        adj_mat.setdiag(0)
    adj_mat = adj_mat.tocsr()
    adj_mat = triu(adj_mat, format='csr')
    adj_mat.eliminate_zeros()
    return adj_mat


def shuffle_network(current_items, sub_variable):
    lst = []
    for idx in current_items:
        for item in current_items[idx]:
            try:
                lst.append({'idx': idx,
                            'item': item["item"],
                            'year': item['year']})
            except:
                continue

    df = pd.DataFrame(lst)
    print('start sampling')
    years = set(df.year)
    # random shuffle of the citation from the same year
    for year in years:
        journals_y = list(df.item[df.year == year])
        df.item[df.year == year] = sample(journals_y, k=len(journals_y))

    random_network = list(df.groupby('idx')['item'].apply(list))

    return random_network


class Uzzi2013(create_output):

    def __init__(self,
                 collection_name,
                 id_variable,
                 year_variable,
                 variable,
                 sub_variable,
                 focal_year,
                 client_name=None,
                 db_name=None,
                 nb_sample=20,
                 density=False,
                 list_ids=None):

        self.nb_sample = nb_sample
        self.indicator = "uzzi"

        create_output.__init__(self,
                               client_name=client_name,
                               db_name=db_name,
                               collection_name=collection_name,
                               id_variable=id_variable,
                               year_variable=year_variable,
                               variable=variable,
                               sub_variable=sub_variable,
                               focal_year=focal_year,
                               density=density,
                               list_ids=list_ids)

        self.path_sample = "../../Data/cooc_sample_sec/{}/".format(self.variable)
        self.path_score = "../../Data/score/fast_uzzi_sec/{}".format(self.variable)
        if not os.path.exists(self.path_sample):
            os.makedirs(self.path_sample)
        if not os.path.exists(self.path_score):
            os.makedirs(self.path_score)
        if not os.path.exists(self.path_score + "/iteration"):
            os.makedirs(self.path_score + "/iteration")

    def sample_network(self):
        already_computed = [
            f for f in os.listdir(self.path_sample)
            if re.match(r'sample_[0-9]+_{}'.format(self.focal_year), f)
        ]

        for i in tqdm(range(self.nb_sample), desc='Create sample network'):
            filename = "sample_{}_{}.p".format(i, self.focal_year)
            if filename not in already_computed:
                sampled_current_items = shuffle_network(self.papers_items, self.sub_variable)
                sampled_current_adj = get_adjacency_matrix(self.name2index,
                                                           sampled_current_items,
                                                           unique_pairwise=False,
                                                           keep_diag=True)
                pickle.dump(
                    sampled_current_adj,
                    open(self.path_sample + filename, "wb")
                )

    def get_mean_sd_parrllel(self, value):
        self.mean_comb[value[0], value[1]] = np.mean(self.count_dict[value])
        self.sd_comb[value[0], value[1]] = np.std(self.count_dict[value])

    def get_unique_values(self, idx):
        with open(self.path_sample + "sample_{}_{}.p".format(idx, self.focal_year), "rb") as f:
            sampled_current_adj_freq = pickle.load(f)

        i_list = sampled_current_adj_freq.nonzero()[0].tolist()
        j_list = sampled_current_adj_freq.nonzero()[1].tolist()
        for i, j in zip(i_list, j_list):
            self.tuple_set.update([(i, j)])

        return sampled_current_adj_freq.shape[0]

    def compute_comb_score_one_by_one(self, ):
        for idx in tqdm(range(self.nb_sample)):
            self.tuple_set = set()
            dimension = self.get_unique_values(idx)
        # self.unique_values = sorted(list(self.tuple_set))
        self.unique_values = list(self.tuple_set)

        # 释放内存
        self.tuple_set = None
        self.count_dict = {}
        for value in self.unique_values:
            self.count_dict[value] = []

        for idx in tqdm(range(self.nb_sample)):
            with open(self.path_sample + "sample_{}_{}.p".format(idx, self.focal_year), "rb") as f:
                self.sampled_current_adj_freq = pickle.load(f)

            print("start No.{} sample network calculate".format(idx))
            for value in self.unique_values:
                self.count_dict[value].append(self.sampled_current_adj_freq[value[0], value[1]])

            self.sampled_current_adj_freq = None

        self.mean_comb = lil_matrix((dimension, dimension))
        self.sd_comb = lil_matrix((dimension, dimension))
        for value in self.unique_values:
            self.get_mean_sd_parrllel(value)

        # 释放内存
        self.count_dict = None
        self.unique_values = None

        # array1 = self.current_adj - self.mean_comb
        # array2 = self.sd_comb
        #
        # chunk_size = 10
        # comb_scores = lil_matrix((dimension, dimension))
        # for i in tqdm(range(0, array1.shape[0], chunk_size)):
        #     # for j in range(0, array1.shape[1], chunk_size):
        #     sub_arr1 = array1[i:i + chunk_size, :]
        #     sub_arr2 = array2[i:i + chunk_size, :]
        #     comb_scores[i:i + chunk_size, :] = sub_arr1 / sub_arr2

        comb_scores = (self.current_adj - self.mean_comb) / self.sd_comb
        comb_scores[np.isinf(comb_scores)] = None
        comb_scores[np.isnan(comb_scores)] = None
        comb_scores = triu(comb_scores, format='csr')
        comb_scores.eliminate_zeros()

        pickle.dump(comb_scores,
                    open(self.path_score + "/{}.p".format(self.focal_year), "wb"))

    def get_indicator(self):
        self.get_data()
        print("Creating sample ...")
        self.sample_network()
        print('Getting score per year ...')
        self.compute_comb_score_one_by_one()
        print('Getting score per paper ...')
        self.update_paper_values()
