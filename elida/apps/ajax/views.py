from django.views import View
from django.http import JsonResponse
import operator
from django.db.models import Q
from functools import reduce

from elida.apps.state.models import State


class DataTablesServer(object):
    def __init__(self, request, queryset):

        self.request = request
        # memo for all the received parameters already processed/parsed
        self.parameters_processed_memo = set()
        # all the parameters received structured in a nested nested dict
        self.parameters_received = self._parse_parameters_received()

        self.queryset = queryset

        self.fields = [column_parameters['name'] for column_parameters in self.parameters_received['columns']]
        self.columns_num_to_field = {
            col_params['data']: col_params['name'] for col_params in self.parameters_received['columns']
        }

    def _draw_request_value(self, key):
        request_value = self.request.GET[key]
        self.parameters_processed_memo.add(key)
        return request_value

    @staticmethod
    def _bool(str_value):
        if str_value == 'false':
            return False
        else:
            return True

    def _parse_parameters_received(self):
        nested_values = {
            'draw': int(self._draw_request_value('draw')),
            'start': int(self._draw_request_value('start')),
            'length': int(self._draw_request_value('length')),
            'search': {},
            'order': [],
            'columns': [],
        }
        try:
            nested_values['search']['value'] = self._draw_request_value('search[value]')
            nested_values['search']['regex'] = self._bool(self._draw_request_value('search[regex]'))
        except KeyError:
            pass
        for key_raw, val in self.request.GET.items():
            if key_raw not in self.parameters_processed_memo:
                if key_raw.startswith('order'):
                    i, _ = key_raw[6:].split(']', 1)
                    nested_values['order'].append(
                        {'column': int(self._draw_request_value(f'order[{i}][column]')),
                         'dir': self._draw_request_value(f'order[{i}][dir]')}
                    )
                elif key_raw.startswith('columns'):
                    i, _ = key_raw[8:].split(']', 1)
                    nested_values['columns'].append(
                        {'data': int(self._draw_request_value(f'columns[{i}][data]')),
                         'name': self._draw_request_value(f'columns[{i}][name]'),
                         'searchable': self._bool(self._draw_request_value(f'columns[{i}][searchable]')),
                         'orderable': self._bool(self._draw_request_value(f'columns[{i}][orderable]')),
                         'search': {
                             'value': self._draw_request_value(f'columns[{i}][search][value]'),
                             'regex': self._bool(self._draw_request_value(f'columns[{i}][search][regex]'))
                         }}
                    )
        # TODO: validate that there are no individual columns searches and no regex search!
        return nested_values

    def _filter_queryset(self, queryset):
        if not self.parameters_received['search']:
            # searching is not even enabled
            return queryset
        if not self.parameters_received['search']['value']:
            # searching is enabled, but the search field is empty
            return queryset
        search_val = self.parameters_received['search']['value']
        query_filters = []
        for column_params in self.parameters_received['columns']:
            if column_params['searchable']:
                field_name = column_params['name']
                query_filters.append(Q((f'{field_name}__contains', search_val)))
        return queryset.filter(reduce(operator.or_, query_filters))

    def _sort_queryset(self, queryset):
        order_by_params = []
        for order_params in self.parameters_received['order']:
            column_num = order_params['column']
            field_name = self.columns_num_to_field[column_num]
            order_dir = order_params['dir']
            order_by = field_name if order_dir == 'asc' else f'-{field_name}'
            order_by_params.append(order_by)
        if not order_by_params:
            return queryset
        return queryset.order_by(*order_by_params)

    def _slice_queryset(self, queryset):
        start = self.parameters_received['start']
        length = self.parameters_received['length']
        return queryset[start:start + length]

    def serve_data(self):
        records_total = self.queryset.count()
        queryset_filtered = self._filter_queryset(self.queryset)
        records_filtered = queryset_filtered.count()
        queryset_sorted = self._sort_queryset(queryset_filtered)
        queryset_sliced = self._slice_queryset(queryset_sorted)

        data_to_return = {
            'draw': str(self.parameters_received['draw']),
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': [
                [getattr(row, field) for field in self.fields]
                for row in queryset_sliced.all()
            ]
        }
        return data_to_return


class StateListAjaxView(View):

    def get(self, request, *args, **kwargs):
        dt_server = DataTablesServer(request, self.queryset)
        data_served = dt_server.serve_data()
        return JsonResponse(data_served)

    @property
    def queryset(self):
        return State.objects.filter(isotopologue__molecule__slug=self.kwargs['mol_slug']).all()
