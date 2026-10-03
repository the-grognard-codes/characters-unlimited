"""Validate accountable content ownership without accepting any rule mechanics."""

from copy import deepcopy
import re

from .option_audit import text_list


def with_content_tickets(coverage, manifest):
    if (not isinstance(manifest, dict) or type(manifest.get('schema_version')) is not int
            or manifest['schema_version'] != 1 or not isinstance(manifest.get('tickets'), list)):
        raise ValueError('Unsupported content ticket manifest')
    prerequisites = text_list(manifest.get('prerequisite_tickets'), 'prerequisite tickets')
    tickets = deepcopy(manifest['tickets'])
    by_id = {}
    owners = {}
    options = {entry['id']: entry for entry in coverage['options']}
    for ticket in tickets:
        if not isinstance(ticket, dict):
            raise ValueError('Content tickets must be records')
        identifier = ticket.get('id')
        if (not isinstance(identifier, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', identifier)
                or identifier in by_id):
            raise ValueError('Content ticket IDs must be unique stable slugs')
        if not isinstance(ticket.get('title'), str) or not ticket['title'].strip():
            raise ValueError('Content tickets require titles')
        if ticket.get('path') != f'.scratch/character-creator/issues/{identifier}.md':
            raise ValueError('Content ticket path must match its repository issue ID')
        members = text_list(ticket.get('option_ids'), 'ticket options')
        dependencies = text_list(ticket.get('dependencies'), 'ticket dependencies')
        if not members or len(members) > 12:
            raise ValueError('Content tickets must own between one and twelve audited identities')
        if len(set(dependencies)) != len(dependencies) or identifier in dependencies:
            raise ValueError('Content ticket dependencies must be distinct and exclude itself')
        for member in members:
            if member not in options or member in owners:
                raise ValueError('Each known canonical option must have exactly one owning content ticket')
            if options[member]['tickets'] != [identifier]:
                raise ValueError('Canonical option ticket assignment disagrees with its owner')
            owners[member] = identifier
        if len({options[member]['book_id'] for member in members}) != 1:
            raise ValueError('An owning content batch must remain within one source book')
        by_id[identifier] = ticket
    if set(owners) != set(options):
        raise ValueError('Content ticket manifest leaves canonical options unassigned')
    if len(set(prerequisites)) != len(prerequisites) or set(prerequisites) & set(by_id):
        raise ValueError('External prerequisites must be distinct from owning content tickets')
    known_tickets = set(by_id) | set(prerequisites)
    for ticket in tickets:
        if set(ticket['dependencies']) - known_tickets:
            raise ValueError('Content ticket prerequisite is unresolved')
        needed = {owners[dependency] for member in ticket['option_ids']
                  for dependency in options[member]['dependencies']} - {ticket['id']}
        if needed - set(ticket['dependencies']):
            raise ValueError('Content ticket omits a known source dependency owner')
    result = deepcopy(coverage)
    result['content_tickets'] = tickets
    result['prerequisite_tickets'] = deepcopy(prerequisites)
    result['summary']['content_tickets'] = len(tickets)
    return result
