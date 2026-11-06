from taolib.cli import simplified_status


def test_simplified_status_preserves_actions_and_bounds_review_history():
    report = {
        'workflows': [{
            'change': 'CHG_20261106_0000000000000001',
            'phase': 'implement',
            'lifecycle': 'active',
            'revision': 12,
            'project': '/work/project with spaces',
            'plan_path': 'docs/plans/change.md',
            'next_action': 'continue',
            'blockers': ['Required review is stale.'],
            'stale_approvals': ['plan'],
            'recovery_commands': [['tao', 'workflow', 'recover', 'CHG_20261106_0000000000000001']],
            'candidate_sources': [{'path': '/work/project with spaces/.tao/workflows/state.json'}],
            'reviews': {'code': {
                'batch': 'batch-1', 'phase': 'implement', 'used': 4, 'limit': 5,
                'decision': 'Authorized five review attempts.',
                'limits': {'timeout_seconds': 1200, 'cost_limit_usd': None},
                'runs': [{'summary': 'large historical report'}] * 500,
            }},
            'review_history': {'code': [{'report': 'large historical report'}] * 500},
        }],
        'tasks': [{'id': 'TASK_1', 'status': 'pending', 'path': 'docs/plan.md', 'line': 10}],
        'evidence_reusability': 'stale',
        'evidence': {
            'state': 'stale', 'logs_available': True, 'expired_checks': ['python-tests'],
            'receipt': 'tmp/tao/verification/latest.json', 'saved': {'large': 'x' * 10000},
        },
        'reviews': [{'requirement': 'independent-review', 'state': 'stale'}],
        'validation': 'source diagnostics and receipt freshness only; no checks rerun',
    }

    result = simplified_status(report)
    workflow = result['workflows'][0]

    assert workflow['blockers'] == ['Required review is stale.']
    assert workflow['recovery_commands'] == report['workflows'][0]['recovery_commands']
    assert workflow['candidate_sources'] == report['workflows'][0]['candidate_sources']
    assert workflow['review_controls']['code']['used'] == 4
    assert workflow['review_history_count'] == 500
    assert workflow['review_history_counts'] == {'code': 500}
    assert 'runs' not in workflow['review_controls']['code']
    assert result['tasks'] == report['tasks']
    assert result['evidence'] == {
        'state': 'stale', 'logs_available': True, 'expired_checks': ['python-tests'],
        'receipt': 'tmp/tao/verification/latest.json',
    }
    assert result['reviews'] == report['reviews']
    assert len(str(result)) < len(str(report)) / 10
