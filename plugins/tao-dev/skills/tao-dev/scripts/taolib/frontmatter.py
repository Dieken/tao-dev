"""One line-delimited YAML envelope for validation and workflow consumers."""
import yaml
from tao_messages import Message


def split_frontmatter(source):
    lines = source.splitlines(keepends=True)
    if not lines or lines[0].rstrip('\r\n') != '---':
        raise ValueError('YAML frontmatter must start the file.')
    end = next((i for i in range(1, len(lines)) if lines[i].rstrip('\r\n') == '---'), None)
    if end is None:
        raise ValueError('Unclosed YAML frontmatter.')
    return ''.join(lines[1:end]), end


class UniqueLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        keys = set()
        for key, _ in node.value:
            if not isinstance(key, yaml.ScalarNode) or key.tag != 'tag:yaml.org,2002:str':
                raise ValueError('Metadata keys must be strings.')
            if key.value in keys:
                raise ValueError(Message('Duplicate metadata: {arg0}.', key.value))
            keys.add(key.value)
        return super().construct_mapping(node, deep=deep)


def load_frontmatter(source):
    text, _ = split_frontmatter(source)
    if any(isinstance(t, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken, yaml.tokens.TagToken)) for t in yaml.scan(text)):
        raise ValueError('Explicit YAML tags are not allowed.')
    value = yaml.load(text, Loader=UniqueLoader)
    if not isinstance(value, dict):
        raise ValueError('Frontmatter must be a mapping.')
    return value
