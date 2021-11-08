from collections import namedtuple

Column = namedtuple('Column', 'heading model_field index visible searchable individual_search placeholder')
Order = namedtuple('Order', 'index dir')
