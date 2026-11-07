"""Pytest starter: adapt project setup/test runner before use. No live AI."""
import json
import os
from pathlib import Path
import subprocess
import sys


def collect(app):
    out = Path('quality-evidence')
    config = Path(__file__).resolve().parents[1] / 'quality.coveragerc'
    out.mkdir(exist_ok=True)
    if app == 'CHANGE_ME' or not Path(app).exists():
        raise RuntimeError('Set APP_PATH to your application directory, relative to the working directory.')
    (out / 'commit.txt').write_text(os.environ.get('GITHUB_SHA', subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()))
    commands = [
        ('django-check.txt', [sys.executable, 'manage.py', 'check']),
        ('migration-check.txt', [sys.executable, 'manage.py', 'makemigrations', '--check', '--dry-run']),
        ('tests.txt', [sys.executable, '-m', 'pytest', '--cov='+app, '--cov-config='+str(config), '--cov-branch', '--cov-report=json:quality-evidence/coverage.json', '--cov-report=term-missing', '--junitxml=quality-evidence/tests.xml']),
        ('pylint.txt', [sys.executable, '-m', 'pylint', '--load-plugins=pylint_django', '--django-settings-module='+os.environ.get('DJANGO_SETTINGS_MODULE', 'config.quality_test_settings'), '--ignore=tests,migrations', '--ignore-patterns=tests.py,test_.*.py', app]),
        ('radon-cc.txt', [sys.executable, '-m', 'radon', 'cc', '-s', '-a', '-e', '*/migrations/*,*/tests/*,*/tests.py,*/test_*.py', app]),
        ('radon-mi.txt', [sys.executable, '-m', 'radon', 'mi', '-s', '-e', '*/migrations/*,*/tests/*,*/tests.py,*/test_*.py', app]),
    ]
    failed = False
    recorded = []
    for name, command in commands:
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        text = result.stdout
        (out / name).write_text(text + '\nExit status: '+str(result.returncode)+'\n')
        recorded.append(' '.join(command)+' => '+str(result.returncode))
        if name == 'tests.txt':
            (out / 'test-status.txt').write_text('pytest exit status: '+str(result.returncode)+'\n'+text[-2000:])
        # Pylint fatal/usage errors fail; ordinary findings (bits 2/4/8/16) do not.
        bad = (result.returncode < 0 or bool(result.returncode & 33)) if name == 'pylint.txt' else result.returncode != 0
        # Detect common missing tool/configuration cases rather than treating them as findings.
        bad = bad or not text.strip() or 'No module named' in text or 'unrecognized-option' in text
        failed = failed or bad
    (out / 'commands.txt').write_text('\n'.join(recorded)+'\n')
    try:
        totals = json.loads((out / 'coverage.json').read_text())['totals']
        if totals['num_statements'] <= 0 or 'num_branches' not in totals:
            raise ValueError('No measured statements or branch instrumentation')
    except (OSError, ValueError, KeyError, TypeError):
        failed = True
    return int(failed)

if __name__ == '__main__':
    try:
        raise SystemExit(collect(sys.argv[1]))
    except (RuntimeError, IndexError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
