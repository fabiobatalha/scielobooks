# coding: utf-8
import urllib

import couchdbkit
from pyramid import exceptions

from scielobooks.staff import models


APP_DOMAIN = 'http://books.scielo.org'


def _prepare_response(data, request):
    """This is a function to help us to format a book as json
    """
    book = models.Monograph(**data)

    if getattr(book, 'pdf_file', None):
        pdf_file_url = APP_DOMAIN + request.route_path(
            'catalog.pdf_file', sbid=book._id, part=book.shortname)
    else:
        pdf_file_url = ''

    if getattr(book, 'epub_file', None):
        epub_file_url = APP_DOMAIN + request.route_path(
            'catalog.epub_file', sbid=book._id, part=book.shortname)
    else:
        epub_file_url = ''

    if getattr(book, 'cover', None):
        cover_url = APP_DOMAIN + request.route_path('catalog.cover', sbid=book._id)
    else:
        cover_url = ''

    if getattr(book, 'cover_thumbnail', None):
        cover_thumb_url = APP_DOMAIN + request.route_path('catalog.cover_thumbnail', sbid=book._id)
    else:
        cover_thumb_url = ''

    resp = {
        'publisher': data.get('publisher', ''),
        '_id': data.get('_id', ''),
        'pisbn': data.get('isbn', ''),
        'eisbn': data.get('eisbn', ''),
        'language': data.get('language', ''),
        'updated': data.get('creation_date', '2012-03-31 00:00:00.000000'),  # 2012-04-01 is the launching date.
        'cover_thumbnail': {
            'type': 'image/jpeg',
            'uri': cover_thumb_url,
        },
        'cover': {
            'type': 'image/jpeg',
            'uri': cover_url,
        },
        'synopsis': data.get('synopsis', ''),
        'year': data.get('year', ''),
        'title': data.get('title', ''),
        'creators': book._creators_by_roles(),
    }

    if pdf_file_url:
        resp.update({'pdf_file': {
            'type': 'application/pdf',
            'uri': pdf_file_url,
        }})

    if epub_file_url:
        resp.update({'epub_file': {
            'type': 'application/epub+zip',
            'uri': epub_file_url,
        }})

    return resp


def list_publishers(request):

    def _prepare_response(data):
        resp = {
            'total_items': data['value'],
            'title': data['key'],
            '_id': urllib.quote(data['key']),
        }

        return resp

    try:
        publishers = [_prepare_response(pub) for pub in request.db.view('scielobooks/publishers', group=True)]
    except couchdbkit.ResourceNotFound:
        raise exceptions.NotFound()

    return publishers


def list_alphasum(request):

    def _prepare_response(data):
        resp = {
            'total_items': data['value'],
            'title': data['key'],
            '_id': data['key'],
        }

        return resp

    try:
        letters = [_prepare_response(letter) for letter in request.db.view('scielobooks/alphabetical', group=True)]
    except couchdbkit.ResourceNotFound:
        raise exceptions.NotFound()

    return letters


def list_books(request):

    _couch_viewname = 'scielobooks/books_by_alpha'

    kwargs = {}
    filter_initial = request.params.get('filter_initial', None)
    filter_publisher = request.params.get('filter_publisher', None)

    if filter_initial:
        kwargs['key'] = filter_initial.upper()

    if filter_publisher:
        kwargs['key'] = filter_publisher.upper()
        _couch_viewname = 'scielobooks/books_by_publisher'

    try:
        books = [_prepare_response(book['doc'], request) for book in request.db.view(_couch_viewname, include_docs=True, **kwargs)]
    except couchdbkit.ResourceNotFound:
        raise exceptions.NotFound()

    return books


def list_changes(request):
    consumer = couchdbkit.Consumer(request.db)
    return consumer.fetch(since=request.params.get('since', 0))


def show_book(request):
    book = request.db.get(request.matchdict['id'])
    return _prepare_response(book, request)

