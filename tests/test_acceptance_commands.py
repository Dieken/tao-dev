from acceptance import commands


def test_cli_executable_preserves_windows_command_shim(monkeypatch):
    monkeypatch.setattr(commands.shutil, 'which', lambda name: 'C:\\npm\\' + name + '.cmd')
    assert commands.cli_executable('claude') == r'C:\npm\claude.cmd'
    assert commands.cli_executable('codex') == r'C:\npm\codex.cmd'


def test_recovery_command_executes_literal_spaced_paths(tmp_path):
    import json
    import os
    import subprocess
    import sys
    import pytest
    if os.name != 'posix':
        pytest.skip('Authenticated acceptance prompts are POSIX-only')
    folder=tmp_path/'local plugins';folder.mkdir()
    entry=folder/"tao 'quoted'.py"
    entry.write_text('import json,sys; print(json.dumps(sys.argv[1:]))')
    project=tmp_path/'project $literal spaces';project.mkdir()
    command=commands.tao_invocation(sys.executable,entry,project)
    result=subprocess.run(command+' status',shell=True,capture_output=True,text=True,timeout=10)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)==['--project',str(project),'--format','json','status']
