# Copyright (C) 2015, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import sys
from datetime import date
from json import dumps
from unittest.mock import call, MagicMock, patch

import pytest

with patch('wazuh.core.common.wazuh_uid'):
    with patch('wazuh.core.common.wazuh_gid'):
        with patch('wazuh.core.utils.load_wazuh_xml'):
            sys.modules['wazuh.rbac.orm'] = MagicMock()
            import wazuh.rbac.decorators
            from wazuh.tests.util import RBAC_bypasser

            del sys.modules['wazuh.rbac.orm']
            wazuh.rbac.decorators.expose_resources = RBAC_bypasser

            import wazuh.stats as stats
            from wazuh.core.results import AffectedItemsWazuhResult
            from api.util import remove_nones_to_dict
            from wazuh.core.tests.test_agent import InitAgent

SOCKET_PATH_DAEMONS_MAPPING = {'/var/ossec/queue/sockets/remote': 'wazuh-remoted',
                               '/var/ossec/queue/sockets/analysis': 'wazuh-analysisd'}
DAEMON_SOCKET_PATHS_MAPPING = {'wazuh-remoted': '/var/ossec/queue/sockets/remote',
                               'wazuh-analysisd': '/var/ossec/queue/sockets/analysis'}

test_data = InitAgent()


def send_msg_to_wdb(msg, raw=False):
    query = ' '.join(msg.split(' ')[2:])
    result = list(map(remove_nones_to_dict, map(dict, test_data.cur.execute(query).fetchall())))
    return ['ok', dumps(result)] if raw else result


def test_totals():
    """Verify totals() function works and returns correct data"""
    with patch('wazuh.stats.totals_', return_value=({})):
        response = stats.totals(date(2019, 8, 13))
        assert response.total_affected_items == len(response.affected_items)
        assert isinstance(response, AffectedItemsWazuhResult), 'The result is not WazuhResult type'


def test_hourly():
    """Makes sure hourly() fit with the expected."""
    response = stats.hourly()
    assert isinstance(response, AffectedItemsWazuhResult), 'The result is not WazuhResult type'
    assert response.total_affected_items == len(response.affected_items)


def test_weekly():
    """Makes sure weekly() fit with the expected."""
    response = stats.weekly()
    assert isinstance(response, AffectedItemsWazuhResult), 'The result is not WazuhResult type'
    assert response.total_affected_items == len(response.affected_items)


@pytest.mark.asyncio
@patch('wazuh.core.common.REMOTED_SOCKET', '/var/ossec/queue/sockets/remote')
@patch('wazuh.core.common.ANALYSISD_SOCKET', '/var/ossec/queue/sockets/analysis')
@patch('wazuh.core.common.WDB_SOCKET', '/var/ossec/queue/db/wdb')
@patch('wazuh.stats.get_daemons_stats_socket')
async def test_get_daemons_stats(mock_get_daemons_stats_socket):
    """Makes sure get_daemons_stats() fit with the expected."""
    response = await stats.get_daemons_stats(['wazuh-remoted', 'wazuh-analysisd', 'wazuh-db'])

    calls = [call('/var/ossec/queue/sockets/remote'), call('/var/ossec/queue/sockets/analysis'),
             call('/var/ossec/queue/db/wdb')]
    mock_get_daemons_stats_socket.assert_has_calls(calls)
    assert isinstance(response, AffectedItemsWazuhResult), \
            'The result is not AffectedItemsWazuhResult type'
    assert response.total_affected_items == len(response.affected_items)


@pytest.mark.asyncio
@patch('wazuh.core.common.REMOTED_SOCKET', '/var/ossec/queue/sockets/wrong_socket_name')
async def test_get_daemons_stats_ko():
    """Makes sure get_daemons_stats() fit with the expected."""
    response = await stats.get_daemons_stats(['wazuh-remoted'])

    assert isinstance(response, AffectedItemsWazuhResult), \
        'The result is not AffectedItemsWazuhResult type'

    assert response.render()['data']['failed_items'][0]['error']['code'] == 1121, \
        'Expected error code was not returned'


def side_effect_test_get_daemons_stats(daemon_path, agents_list):
    return {'name': SOCKET_PATH_DAEMONS_MAPPING[daemon_path], 'agents': [{'id': a} for a in agents_list]}


def side_effect_test_get_daemons_stats_all(daemon_path, agents_list, last_id):
    # side_effect used to return a response with 10 items and 'due' the first time that get_daemons_stats_socket is
    # called, and a response with 10 items and 'ok' the second time
    if last_id:
        last_id += 1
    return {'data': {'name': SOCKET_PATH_DAEMONS_MAPPING[daemon_path],
                     'agents': [{'id': i} for i in range(last_id, last_id + 10)]},
            'message': 'due' if last_id == 0 else 'ok',
            'error': 1 if last_id == 0 else 0}


@patch('wazuh.stats.get_daemons_stats_', return_value=[{"events_decoded": 1.0}])
def test_deprecated_get_daemons_stats(mock_daemons_stats_):
    """Makes sure deprecated_get_daemons_stats() fit with the expected."""
    response = stats.deprecated_get_daemons_stats('filename')
    assert isinstance(response, AffectedItemsWazuhResult), 'The result is not WazuhResult type'
    assert response.total_affected_items == len(response.affected_items)
