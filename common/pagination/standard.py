"""
Standard API pagination class matching the HMOS specification envelope.
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        request = self.request
        request_id = getattr(request, 'correlation_id', None)

        return Response({
            'success': True,
            'data': data,
            'results': data,
            'meta': {
                'count': self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'current_page': self.page.number,
                'page_size': self.get_page_size(request),
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'request_id': request_id,
            }
        })

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'required': ['success', 'data', 'meta'],
            'properties': {
                'success': {'type': 'boolean'},
                'data': schema,
                'meta': {
                    'type': 'object',
                    'properties': {
                        'count': {'type': 'integer'},
                        'total_pages': {'type': 'integer'},
                        'current_page': {'type': 'integer'},
                        'page_size': {'type': 'integer'},
                        'next': {'type': 'string', 'nullable': True, 'format': 'uri'},
                        'previous': {'type': 'string', 'nullable': True, 'format': 'uri'},
                        'request_id': {'type': 'string', 'nullable': True},
                    }
                }
            }
        }
