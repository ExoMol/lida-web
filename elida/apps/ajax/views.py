from django.views import View
from django.http import JsonResponse
from collections import namedtuple, OrderedDict
import operator
from django.db.models import Q
from functools import reduce

from elida.apps.state.models import State

order_dict = {'asc': '', 'desc': '-'}


class DataTablesServer(object):
    def __init__(self, request, column_names, qs):
        self.column_names = column_names
        # parse the request values from the raw request.GET dict.
        self.request = request
        self.request_values_processed = set()  # memo for request values parsed already (speed optimization)
        self.request_values = self._parse_request_values()  # structured in nested dict

        # results from the db
        self.result_data = None
        # total in the table after filtering
        self.cardinality_filtered = 0
        # total in the table unfiltered
        self.cardinality = 0
        self.user = request.user
        self.qs = qs
        self.run_queries()

    def _draw_request_value(self, key):
        request_value = self.request.GET[key]
        self.request_values_processed.add(key)
        return request_value

    def _parse_request_values(self):
        nested_values = {
            'draw': str(int(self._draw_request_value('draw'))),
            'start': int(self._draw_request_value('start')),
            'length': int(self._draw_request_value('length')),
            'search': {},
            'order': OrderedDict(),
            'columns': OrderedDict(),
        }
        try:
            nested_values['search']['value'] = self._draw_request_value('search[value]')
            nested_values['search']['regex'] = bool(self._draw_request_value('search[regex]'))
        except KeyError:
            pass
        for key_raw, val in self.request.GET.items():
            if key_raw not in self.request_values_processed:
                if key_raw.startswith('order'):
                    i, _ = key_raw[6:].split(']', 1)
                    nested_values['order'][int(i)] = {
                        'column': int(self._draw_request_value(f'order[{i}][column]')),
                        'dir': self._draw_request_value(f'order[{i}][dir]')
                    }
                elif key_raw.startswith('columns'):
                    i, _ = key_raw[8:].split(']', 1)
                    nested_values['columns'][int(i)] = {
                        'data': int(self._draw_request_value(f'columns[{i}][data]')),
                        'name': self._draw_request_value(f'columns[{i}][name]'),
                        'searchable': bool(self._draw_request_value(f'columns[{i}][searchable]')),
                        'orderable': bool(self._draw_request_value(f'columns[{i}][orderable]')),
                        'search': {
                            'value': self._draw_request_value(f'columns[{i}][search][value]'),
                            'regex': bool(self._draw_request_value(f'columns[{i}][search][regex]'))
                        }
                    }
        # TODO: validate that there are no individual columns searches and no regex search!
        return nested_values

    def output_result(self):
        output = dict()
        output['draw'] = self.request_values['draw']  # used for synchronising the requests, do not change!
        output['recordsTotal'] = str(self.qs.count())  # total number of records before filtering
        output['recordsFiltered'] = str(self.cardinality_filtered)  # total number of records after filtering
        output['data'] = []  # 2D array of (1 page of) displayed data, each row for one record

        for row in self.result_data:
            data_row = []
            for i in range(len(self.column_names)):
                # val = getattr(row, self.columns[i])
                val = row[self.column_names[i]]
                data_row.append(val)
            output['data'].append(data_row)
        return output

    def run_queries(self):
        # pages has 'start' and 'length' attributes
        pages = self.paging()
        # the term you entered into the datatable search
        _filter = self.filtering()
        # the document field you chose to sort
        sorting = self.sorting()
        # custom filter
        qs = self.qs

        if _filter:
            data = qs.filter(
                reduce(operator.or_, _filter)).order_by('%s' % sorting)
            len_data = data.count()
            data = list(data[pages.start:pages.length].values(*self.column_names))
        else:
            data = qs.order_by('%s' % sorting).values(*self.column_names)
            len_data = data.count()
            _index = int(pages.start)
            data = data[_index:_index + (pages.length - pages.start)]

        self.result_data = list(data)

        # length of filtered set
        if _filter:
            self.cardinality_filtered = len_data
        else:
            self.cardinality_filtered = len_data
        self.cardinality = pages.length - pages.start

    def filtering(self):
        # build your filter spec
        or_filter = []

        if self.request_values['search'] and self.request_values['search']['value']:
            for i in range(len(self.column_names)):
                or_filter.append((self.column_names[i] + '__icontains', self.request_values['search']['value']))

        q_list = [Q(x) for x in or_filter]
        return q_list

    def sorting(self):

        order = ''
        if self.request_values['order']:

            for i in self.request_values['order']:
                # column number
                column_number = self.request_values['order'][i]['column']
                # sort direction
                sort_direction = self.request_values['order'][i]['dir']

                order = ('' if order == '' else ',') + order_dict[sort_direction] + self.column_names[column_number]

        return order

    def paging(self):

        pages = namedtuple('pages', ['start', 'length'])

        if (self.request_values['start'] != "") and (self.request_values['length'] != -1):
            pages.start = int(self.request_values['start'])
            pages.length = pages.start + int(self.request_values['length'])

        return pages


class StateListAjaxView(View):

    columns = 'el_state_html vib_state_html energy lifetime number_transitions_from number_transitions_to'.split()

    def get(self, request, *args, **kwargs):
        result = DataTablesServer(request, self.columns, self.queryset).output_result()
        return JsonResponse(result, safe=False)

    @property
    def queryset(self):
        return State.objects.filter(isotopologue__molecule__slug=self.kwargs['mol_slug']).all()
