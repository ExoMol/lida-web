from django.db import models


class ProvenanceMixin:
    time_added = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)


class ReprMixin:
    def __repr__(self):
        # noinspection PyUnresolvedReferences
        return f'{self.id}:{self.__name__}({self})'
