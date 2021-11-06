import operator
from functools import reduce

from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from django.urls import reverse

from elida.apps.state.models import State


class DataTablesServer:
    def __init__(self, request, queryset, value_getters=None):

        self.request = request
        # memo for all the received parameters already processed/parsed
        self.parameters_processed_memo = set()
        # all the parameters received structured in a nested nested dict
        self.parameters_received = self._parse_parameters_received(request)

        self.queryset = queryset

        self.fields = [column_parameters['name'] for column_parameters in self.parameters_received['columns']]
        self.columns_num_to_field = {
            col_params['data']: col_params['name'] for col_params in self.parameters_received['columns']
        }

        self.value_getters = value_getters
        if self.value_getters is None:
            self.value_getters = {}

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

    def _parse_parameters_received(self, request):
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
        for key_raw, val in request.GET.items():
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
        # TODO: validate that there is no regex search enabled!
        return nested_values

    def _filter_queryset(self, queryset):
        global_query_filters = []  # OR filters
        local_query_filters = []  # AND filters
        for column_params in self.parameters_received['columns']:
            field_name = column_params['name']
            if column_params['searchable']:
                if self.parameters_received['search']:
                    global_search_val = self.parameters_received['search']['value']
                    if global_search_val:
                        global_query_filters.append(Q((f'{field_name}__contains', global_search_val)))
            local_search_val = column_params['search']['value']
            if local_search_val:
                local_query_filters.append(Q((f'{field_name}__contains', local_search_val)))
        filtered_queryset = queryset
        # global search filter
        if global_query_filters:
            filtered_queryset = filtered_queryset.filter(reduce(operator.or_, global_query_filters))
        # local search filter:
        if local_query_filters:
            filtered_queryset = filtered_queryset.filter(reduce(operator.and_, local_query_filters))
        return filtered_queryset

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
            'data': []
        }
        for instance in queryset_sliced.all():
            row = []
            for field in self.fields:
                if field in self.value_getters:
                    row.append(self.value_getters[field](instance))
                else:
                    row.append(getattr(instance, field))
            data_to_return['data'].append(row)

        return data_to_return


class StateListAjaxView(View):

    def get(self, request, *args, **kwargs):
        dt_server = DataTablesServer(request, self.queryset, self.value_getters)
        data_served = dt_server.serve_data()
        return JsonResponse(data_served)

    @property
    def queryset(self):
        return State.objects.filter(isotopologue__molecule__slug=self.kwargs['mol_slug']).all()

    @property
    def value_getters(self):
        def number_transitions_from_value(instance):
            val = instance.number_transitions_from
            if not val:
                return ''
            href = reverse('transition-list-from-state', args=[instance.pk])
            cls = 'elida-link'
            return f'<a href="{href}" class="{cls}">{val}</a>'

        def number_transitions_to_value(instance):
            val = instance.number_transitions_to
            if not val:
                return ''
            href = reverse('transition-list-to-state', args=[instance.pk])
            cls = 'elida-link'
            return f'<a href="{href}" class="{cls}">{val}</a>'

        return {
            'energy': lambda instance: f'{instance.energy:.3f}',
            'lifetime': lambda instance: f'{instance.lifetime:.2e}' if instance.lifetime is not None else '∞',
            'number_transitions_from': number_transitions_from_value,
            'number_transitions_to': number_transitions_to_value
        }
