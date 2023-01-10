from django.core.paginator import Paginator


def get_paginator(value, request, paginator_page_number=10):
    paginator = Paginator(value, paginator_page_number)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }
