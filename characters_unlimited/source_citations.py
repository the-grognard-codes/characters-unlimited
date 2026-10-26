"""Minimal descriptive evidence with optional bounded citation page lists."""


def validate_source_citation(source):
    if (not isinstance(source, dict)
            or any(not isinstance(source.get(key), str) or not source[key].strip()
                   for key in ('book', 'section'))):
        raise ValueError('Source citations require book and section evidence')
    for key in ('pages', 'pdf_pages'):
        if key in source and (not isinstance(source[key], list) or len(source[key]) > 1000
                or any(type(page) is not int or not 1 <= page <= 1000000 for page in source[key])):
            raise ValueError('Optional source page lists require bounded positive integers')
