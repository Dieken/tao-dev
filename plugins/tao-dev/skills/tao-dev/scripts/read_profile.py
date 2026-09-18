"""Read one document contract and localize its template without writing files."""
import argparse
import json
from pathlib import Path
import re

ASSETS = Path(__file__).resolve().parents[1] / 'assets'


def read_profile(profile, locale, variant=None):
    registry = json.loads((ASSETS / 'document-profiles.json').read_text(encoding='utf-8'))
    schema = profile if profile.startswith('tao.project.') else f'tao.project.{profile}/v0.1'
    if schema not in registry['profiles']:
        raise ValueError('Unknown document profile: ' + profile)
    rule = registry['profiles'][schema]
    if locale not in ('en', 'zh-Hans'):
        raise ValueError('Unsupported template locale: ' + locale)
    labels = json.loads((ASSETS / f'locales/{locale}.json').read_text(encoding='utf-8'))
    template = rule['template']
    if variant is not None:
        if variant not in rule.get('alternate_templates', {}):
            raise ValueError('Unknown template variant for this profile: ' + variant)
        template = rule['alternate_templates'][variant]
    source = (ASSETS / template).read_text(encoding='utf-8')
    localized = re.sub(r'\{\{((?:heading|label)\.[^}]+)\}\}', lambda match: labels[match[1]], source)
    result = {key: registry[key] for key in (
        'base_metadata', 'structure', 'id', 'reference_role', 'entities_outside_registered_sections')}
    result.update(schema=schema, profile=rule, template=localized)
    entities = {kind: value for kind, value in registry['entities'].items()
                if set(registry['entity_sections'][kind]) & set(rule['sections'])}
    if entities:
        result['entities'] = entities
        result['entity_sections'] = {kind: [section for section in registry['entity_sections'][kind]
                                            if section in rule['sections']] for kind in entities}
    if 'tasks' in rule['sections']:
        result['tasks'] = registry['tasks']
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', help='Profile name, e.g. evidence, or its full schema')
    parser.add_argument('--locale', required=True, choices=('en', 'zh-Hans'))
    parser.add_argument('--template', help='Alternate writing template, e.g. review')
    args = parser.parse_args()
    try:
        result = read_profile(args.profile, args.locale, args.template)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
