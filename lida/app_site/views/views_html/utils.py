class Column:
    def __init__(
        self,
        heading,
        model_field,
        index,
        visible=True,
        searchable=False,
        individual_search=False,
        placeholder=None,
    ):
        self.heading = heading
        self.model_field = model_field
        self.index = index
        self.visible = visible
        self.searchable = searchable
        self.individual_search = individual_search
        self.placeholder = placeholder if placeholder is not None else heading


class Order:
    def __init__(self, index, direction="asc"):
        self.index = index
        self.dir = direction
