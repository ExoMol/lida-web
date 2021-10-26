from django.db import models


class ModelMixin:
    id = models.AutoField(primary_key=True)
    time_added = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)

    def str_to_repr(self, text):
        # noinspection PyUnresolvedReferences
        return f'{self.id}:{self._meta.object_name}({text})'

    def __repr__(self):
        return self.str_to_repr(str(self))

    @property
    def model_name(self):
        return self._meta.model.__name__
