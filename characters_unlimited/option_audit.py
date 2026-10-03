"""Source-bound option identities; identity review never accepts mechanics."""

from copy import deepcopy
import re


def text_list(value, field):
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f'Canonical option {field} must contain nonblank text')
    return value


def audited_coverage(inventory, catalog):
    if not isinstance(catalog, dict) or type(catalog.get('schema_version')) is not int or catalog['schema_version'] != 1 or not isinstance(catalog.get('entries'), list):
        raise ValueError('Unsupported canonical option catalog')
    text_list(catalog.get('findings'), 'findings')
    books = {book['id']: book for book in inventory['books']}
    candidates = {candidate['id']: candidate for candidate in inventory['candidates']}
    entries = deepcopy(catalog['entries'])
    identifiers = set()
    identities = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Canonical options must be records')
        identifier = entry.get('id')
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', identifier) or identifier in identifiers:
            raise ValueError('Canonical option IDs must be unique stable slugs')
        identifiers.add(identifier)
        if not isinstance(entry.get('name'), str) or not entry['name'].strip():
            raise ValueError('Canonical option names must be nonblank text')
        if entry.get('kind') not in ('occ', 'rcc', 'race', 'skill', 'power-category', 'power', 'spell', 'psionic', 'equipment', 'construction', 'rule', 'option-family'):
            raise ValueError('Unsupported canonical option kind')
        if not isinstance(entry.get('book_id'), str):
            raise ValueError('Canonical option source book ID must be text')
        book = books.get(entry['book_id'])
        source = entry.get('source')
        if book is None or not isinstance(source, dict):
            raise ValueError('Canonical option source book is unavailable')
        identity = (book['id'], entry['kind'], ' '.join(entry['name'].split()).casefold())
        if identity in identities:
            raise ValueError('Canonical option identities must be unique within their source book')
        identities.add(identity)
        if source.get('markdown_sha256') != book['sha256'] or source.get('pdf_sha256') != book['pdf_sha256'] or not book['pdf_sha256']:
            raise ValueError('Canonical option source fingerprint changed; re-review its identity')
        for field in ('printed_pages', 'pdf_pages'):
            pages = source.get(field)
            if not isinstance(pages, list) or not pages or any(type(page) is not int or page < 1 for page in pages):
                raise ValueError('Canonical option evidence needs positive printed and PDF pages')
        for field in ('aliases', 'candidate_ids', 'tickets', 'dependencies', 'findings'):
            text_list(entry.get(field), field)
        for candidate_id in entry['candidate_ids']:
            candidate = candidates.get(candidate_id)
            if not candidate or candidate['book_id'] != book['id'] or candidate['source_sha256'] != book['sha256']:
                raise ValueError('Canonical option candidate belongs to a different or missing source')
        if entry.get('identity_review') not in ('pending', 'confirmed'):
            raise ValueError('Unsupported canonical identity review state')
        if entry['identity_review'] == 'confirmed' and not entry['candidate_ids']:
            raise ValueError('Confirmed canonical identities require candidate source evidence')
        # This identity-only contract cannot certify rule calculations or release acceptance.
        if entry.get('mechanical_review') != 'pending' or entry.get('dependency_review') != 'pending':
            raise ValueError('This catalog requires separate mechanical and dependency review')
        if entry.get('automation') not in ('not-implemented', 'partial'):
            raise ValueError('This identity catalog cannot claim full automation')
        if not entry['findings']:
            raise ValueError('Record the remaining mechanical/dependency review findings')
        entry['game'] = book['game']
    by_id = {entry['id']: entry for entry in entries}
    for entry in entries:
        if set(entry['dependencies']) - identifiers:
            raise ValueError('Canonical option dependency is missing; record unresolved dependencies in findings')
        if any(by_id[dependency]['game'] != entry['game'] for dependency in entry['dependencies']):
            raise ValueError('Canonical dependencies must remain within their own game')
    result = deepcopy(inventory)
    result['options'] = entries
    result['audit_findings'] = deepcopy(catalog['findings'])
    result['summary'].update(canonical_options=len(entries), identity_confirmed=sum(entry['identity_review'] == 'confirmed' for entry in entries),
                             mechanically_reviewed=0, unassigned_options=sum(not entry['tickets'] for entry in entries))
    return result
