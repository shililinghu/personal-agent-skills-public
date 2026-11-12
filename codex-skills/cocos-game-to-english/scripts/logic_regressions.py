#!/usr/bin/env python3
"""Evidence requirements learned from real reviews; does not operate a game.

Static findings are suspects. Runtime rows are tester observations with hashed
artifacts and a current source/data binding, never proof inferred from a regex.
"""
import hashlib
from pathlib import Path
import re
import button_state_check
from input_owner_inventory import inspect_sources

CASES = [
    ('R01', '循环列表与边界', 'L-CYCLIC', ('browser_touch',),
     ('inventory', 'reverse_cycles', 'forward_cycles', 'empty_singleton_boundaries', 'controls_remain_usable')),
    ('R02', '坏存档与迁移恢复', 'L-SAVE-RECOVERY', ('browser_fault',),
     ('malformed_json', 'missing_fields', 'wrong_types_and_ranges', 'valid_fields_preserved', 'retry_or_recovery_works', 'native_missing_key_semantics', 'actual_reward_ledger_and_adapter', 'storage_failure_diagnostics')),
    ('R03', '挂起加载与真实重试', 'L-LOAD-RETRY', ('browser_fault', 'mixed_runtime'),
     ('held_real_transport', 'held_callback_and_timer', 'frame_recovery', 'fresh_underlying_request',
      'late_result_isolated', 'ready_then_input', 'explicit_failure_and_normal_controls')),
    ('R04', '资源扣除与实际消费者', 'L-CONSUMER', ('browser_touch', 'browser_fault'),
     ('consuming_entries', 'non_play_pages_no_spend', 'active_consumer_effect', 'close_leave_duplicate_safety')),
    ('R05', '失败与暂停标准控件', 'L-EXIT', ('browser_touch',),
     ('failure_home_retry', 'optional_ad_separate', 'pause_resume_restart_home', 'destinations_and_costs', 'two_aspect_ratios')),
    ('R06', '按钮按状态产生业务反馈', 'L-BUTTON-EFFECT', ('browser_touch',),
     ('page_state_inventory', 'visible_button_outcomes', 'mode_specific_tools', 'close_restores_input', 'legitimate_noop_feedback', 'nonfunctional_legacy_entries_removed', 'disabled_state_outcomes')),
    ('R07', '触点归属与取消', 'L-POINTER', ('browser_touch',),
     ('input_policy', 'second_contact_ownership', 'secondary_cancel_safety', 'primary_cancel_no_commit', 'next_gesture_works')),
    ('R08', '当前运行数据与测试绑定', 'L-RUNTIME-DATA', ('production_data_replay', 'mixed_runtime'),
     ('runtime_data_paths', 'actual_counts', 'all_runtime_configurations', 'suite_targets_match_runtime', 'ui_sampling_scope')),
]


def source_digest(project):
    """Bind observations to scripts/configs in assets, not prior report counts."""
    skip = {'node_modules', 'library', 'temp', 'build', '.git'}
    digest = hashlib.sha256()
    for p in sorted((Path(project) / 'assets').rglob('*')):
        rel = p.relative_to(project).as_posix()
        if not p.is_file() or p.suffix not in {'.js', '.ts', '.json'} or skip & set(p.parts):
            continue
        digest.update(rel.encode('utf-8') + b'\0' + hashlib.sha256(p.read_bytes()).digest())
    return digest.hexdigest()


def templates():
    return [{'id': ident, 'title': title, 'status': 'untested', 'layer': '',
             'observations': {}, 'evidence': [], 'note': ''} for ident, title, *_ in CASES]


def static_suspects(files):
    found = []
    for rel, code in files:
        # JS remainder retains the dividend sign: adding one length is not
        # sufficient for an unbounded backwards cursor. Fully normalized modulo
        # does not match; a bounded cursor still needs human triage.
        pattern = r'\(\s*(?:index|idx|cursor|page|selected\w*)\s*\+\s*(?P<n>[\w.]+(?:\.length)?)\s*\)\s*%\s*(?P=n)\b'
        for m in re.finditer(pattern, code):
            tail = code[m.end():m.end() + len(m['n']) * 2 + 30]
            if re.match(r'\s*\+\s*' + re.escape(m['n']) + r'\s*\)\s*%\s*' + re.escape(m['n']) + r'\b', tail):
                continue  # ((index + n) % n + n) % n
            found.append({'rule': 'L-CYCLIC', 'severity': 'fail', 'file': rel,
                          'line': code.count('\n', 0, m.start()) + 1,
                          'message': 'signed remainder after adding one length can become negative after repeated reverse navigation; inspect cursor bounds and test >=3 full cycles (R01); use normalized modulo if unbounded'})
        if re.search(r'JSON\.parse\s*\(', code) and re.search(r'getItem\s*\(', code):
            found.append({'rule': 'L-SAVE-RECOVERY', 'severity': 'hint', 'file': rel, 'line': 1,
                          'message': 'saved JSON is parsed: run R02 against malformed/partial/type/range records and verify a usable recovery path; try/catch or a Retry label alone does not prove recovery'})
        if re.search(r'setInterval\s*\(', code) and re.search(r'loadBundle|resources\.load|loadResource', code):
            found.append({'rule': 'L-LOAD-RETRY', 'severity': 'hint', 'file': rel, 'line': 1,
                          'message': 'loading uses an interval: R03 must hold the real transport and original watchdog together, then verify a fresh underlying request and playable input; never infer retry success from a button'})
    return found



def input_owner_sources(project):
    """Conservative inventory for explicit contact ownership; not a bug verdict."""
    sources = [p.resolve() for p in sorted((Path(project) / 'assets').rglob('*'))
               if p.is_file() and p.suffix in {'.js', '.ts', '.cjs', '.mjs'} and
               not {'node_modules', 'library', 'temp', 'build', '.git'} & set(p.parts)]
    # Unknown executable input must be covered, not declared absent.
    return [p for p, inventory in zip(sources, inspect_sources(sources)) if inventory['status'] != 'none']



def validate(document, project, digest):
    """Check completeness/integrity; cannot decide if observation text is true."""
    records = document.get('regressions', [])
    records = records if isinstance(records, list) else []
    rows, problems = [], []
    for ident, title, rule, layers, required in CASES:
        matches = [r for r in records if isinstance(r, dict) and r.get('id') == ident]
        rec = matches[0] if len(matches) == 1 else {}
        row = dict(rec, id=ident, title=title, rule=rule)
        status = rec.get('status', 'missing')
        row['status'] = status
        errors = []
        if len(matches) > 1:
            errors.append('duplicate regression id')
        if status == 'n/a':
            if not str(rec.get('note') or '').strip():
                errors.append('n/a requires the actual missing feature or explicit scope reason')
            if ident == 'R06':
                errors.append('R06 button coverage cannot use n/a; scope the affected control inventory instead')
        elif status == 'pass':
            if document.get('regression_binding') != {'source_sha256': digest}:
                errors.append('stale/missing current script and runtime-data binding; rerun affected cases')
            if rec.get('layer') not in layers:
                errors.append('required observation layer: ' + ', '.join(layers))
            obs = rec.get('observations')
            if not isinstance(obs, dict):
                obs = {}
            missing = [key for key in required if not isinstance(obs.get(key), str) or
                       obs[key].strip().lower() in {'', 'pass', 'true', 'ok', 'tested', '通过', '已测'}]
            if missing:
                errors.append('concrete observations missing: ' + ', '.join(missing))
            refs = rec.get('evidence')
            if not isinstance(refs, list) or not refs:
                errors.append('nonempty hashed evidence files required')
                refs = []
            for ref in refs:
                try:
                    p = Path(project) / ref['path']
                    if not p.is_file() or p.stat().st_size == 0 or hashlib.sha256(p.read_bytes()).hexdigest() != ref.get('sha256'):
                        errors.append('evidence missing, empty or changed: ' + str(p))
                except (TypeError, KeyError, OSError):
                    errors.append('invalid evidence reference')
            if ident == 'R06':
                root = Path(rec.get('button_check_root', project)).resolve()
                if (not Path(project).resolve().is_relative_to(root) or
                        not button_state_check.current_report(root, rec.get('button_check'))):
                    errors.append('R06 requires a current scoped button_state_check report; prose cannot replace per-control/state outcomes')
                else:
                    # Full baseline must not omit the production owner from the
                    # hand-written button plan and then claim non-applicability.
                    owners = input_owner_sources(project)
                    if owners:
                        try:
                            report = button_state_check.read_ref(root, rec['button_check'], True)
                            plan = button_state_check.read_ref(root, report['inputs']['plan'], True)
                            bound = {button_state_check.read_ref(root, ref).resolve() for ref in plan['business_sources']}
                            if plan.get('input_lifecycle', {}).get('applicable') is not True:
                                errors.append('R06 production touch owners require input lifecycle coverage')
                            missing_owners = [p.relative_to(Path(project).resolve()).as_posix() for p in owners if p not in bound]
                            if missing_owners:
                                errors.append('R06 omitted production input owner source binding: ' + ', '.join(missing_owners))
                        except (KeyError, TypeError, ValueError, OSError):
                            errors.append('R06 invalid production input owner coverage')

        else:
            errors.append({'missing': 'case missing; run --init to append without resetting prior results',
                           'untested': 'not tested; cannot pass', 'fail': 'reproduced failure; fix and rerun'}.get(status, 'unknown status'))
        if errors:
            row['problem'] = '; '.join(errors)
            problems.append(row)
        rows.append(row)
    return rows, problems


def current_report(report, base):
    """Main gate must not accept pre-regression or subsequently edited evidence."""
    digest = report.get('current_source_sha256', '')
    if (report.get('mode') != 'build' or report.get('regression_version') != 1 or
            report.get('regression_problems') != 0 or not isinstance(digest, str) or
            re.fullmatch(r'[0-9a-f]{64}', digest) is None or
            report.get('regression_binding') != {'source_sha256': digest}):
        return False
    _, errors = validate(report, base, digest)
    return not errors
