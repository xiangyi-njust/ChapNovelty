from lib.novelpy.indicators import Wang2017
from lib.novelpy.utils import cooc_utils
from tqdm import tqdm


def construct_cooc():
    """
        In the method of using uzzi's way to calculate novelty
        we construct the combination matrix, don't consider all occurence journal, just for journal occur in this year
        In this way, cause that the time complex is relatively small, we can consider all of occurence journal
    """

    ref_cooc = cooc_utils.create_cooc(
        collection_name='paper_level_nomarlize_remove_unmatch',
        year_var='year',
        var='reference',
        sub_var='source',
        weighted_network=False,
        self_loop=False
    )
    ref_cooc.main()


if __name__ == '__main__':
    # construct_cooc

    for year in tqdm(range(2006, 2025)):
        wang_novelty = Wang2017(collection_name='paper_level_nomarlize_remove_unmatch',
                                id_variable='doi',
                                year_variable='year',
                                variable='reference',
                                focal_year=year,
                                sub_variable='source',
                                n_reutilisation=1,
                                time_window_cooc=3,
                                keep_item_percentile=50,
                                density=True)

        wang_novelty.get_indicator()
