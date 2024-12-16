from lib.fastnovelpy.utils import cooc_utils

# get combination
ref_cooc = cooc_utils.create_cooc(
    collection_name='sec_level_nomarlize_remove_unmatch',
    year_var='year',
    var='reference',
    sub_var='source',
    weighted_network=True,
    self_loop=True
)

ref_cooc.main()
