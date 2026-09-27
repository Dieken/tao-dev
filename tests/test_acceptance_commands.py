from acceptance import commands


def test_cli_executable_preserves_windows_command_shim(monkeypatch):
    monkeypatch.setattr(commands.shutil, 'which', lambda name: 'C:\\npm\\' + name + '.cmd')
    assert commands.cli_executable('claude') == r'C:\npm\claude.cmd'
    assert commands.cli_executable('codex') == r'C:\npm\codex.cmd'
