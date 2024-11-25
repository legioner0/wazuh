# Copyright (C) 2015, Wazuh Inc.
# Created by Wazuh, Inc. <info@wazuh.com>.
# This program is free software; you can redistribute it and/or modify it under the terms of GPLv2

import datetime

from wazuh.core import common
from wazuh.core import exception
from wazuh.core.agent import Agent, get_agents_info, get_rbac_filters, WazuhDBQueryAgents
from wazuh.core.cluster.cluster import get_node
from wazuh.core.exception import WazuhException
from wazuh.core.results import AffectedItemsWazuhResult
from wazuh.core.stats import get_daemons_stats_, get_daemons_stats_socket, hourly_, totals_, weekly_
from wazuh.rbac.decorators import expose_resources

node_id = get_node().get('node')


@expose_resources(actions=['cluster:read'],
                  resources=[f'node:id:{node_id}'])
def totals(date: datetime.date) -> AffectedItemsWazuhResult:
    """Retrieve statistical information for the current or specified date.

    Parameters
    ----------
    date : datetime.date
        Date object with the date value of the stats.

    Returns
    -------
    AffectedItemsWazuhResult
        Array of dictionaries. Each dictionary represents an hour.
    """
    result = AffectedItemsWazuhResult(all_msg='Statistical information for each node was successfully read',
                                      some_msg='Could not read statistical information for some nodes',
                                      none_msg='Could not read statistical information for any node'
                                      )
    affected = totals_(date)
    result.affected_items = affected
    result.total_affected_items = len(result.affected_items)

    return result


@expose_resources(actions=['cluster:read'],
                  resources=[f'node:id:{node_id}'])
def hourly() -> AffectedItemsWazuhResult:
    """Compute hourly averages.

    Returns
    -------
    AffectedItemsWazuhResult
        Dictionary with averages and interactions.
    """
    result = AffectedItemsWazuhResult(all_msg='Statistical information per hour for each node was successfully read',
                                      some_msg='Could not read statistical information per hour for some nodes',
                                      none_msg='Could not read statistical information per hour for any node'
                                      )
    result.affected_items = hourly_()
    result.total_affected_items = len(result.affected_items)

    return result


@expose_resources(actions=['cluster:read'],
                  resources=[f'node:id:{node_id}'])
def weekly() -> AffectedItemsWazuhResult:
    """Compute weekly averages.

    Returns
    -------
    AffectedItemsWazuhResult
        Dictionary for each week day.
    """
    result = AffectedItemsWazuhResult(all_msg='Statistical information per week for each node was successfully read',
                                      some_msg='Could not read statistical information per week for some nodes',
                                      none_msg='Could not read statistical information per week for any node'
                                      )
    result.affected_items = weekly_()
    result.total_affected_items = len(result.affected_items)

    return result


@expose_resources(actions=['cluster:read'],
                  resources=[f'node:id:{node_id}'])
async def get_daemons_stats(daemons_list: list = None) -> AffectedItemsWazuhResult:
    """Get statistical information from the specified daemons.
    If the list is empty, the stats from all daemons will be retrieved.

    Parameters
    ----------
    daemons_list : list
        List of the daemons to get statistical information from.

    Returns
    -------
    AffectedItemsWazuhResult
        Dictionary with the stats of the input file.
    """
    daemon_socket_mapping = {'wazuh-remoted': common.REMOTED_SOCKET,
                             'wazuh-analysisd': common.ANALYSISD_SOCKET,
                             'wazuh-db': common.WDB_SOCKET}
    result = AffectedItemsWazuhResult(all_msg='Statistical information for each daemon was successfully read',
                                      some_msg='Could not read statistical information for some daemons',
                                      none_msg='Could not read statistical information for any daemon')

    for daemon in daemons_list or daemon_socket_mapping.keys():
        try:
            res = await get_daemons_stats_socket(daemon_socket_mapping[daemon])
            result.affected_items.append(res)
        except WazuhException as e:
            result.add_failed_item(id_=daemon, error=e)

    result.total_affected_items = len(result.affected_items)
    return result


@expose_resources(actions=['cluster:read'],
                  resources=[f'node:id:{node_id}'])
def deprecated_get_daemons_stats(filename):
    """Get daemons stats from an input file.

    Parameters
    ----------
    filename: str
        Full path of the file to get information.

    Returns
    -------
    AffectedItemsWazuhResult
        Dictionary with the stats of the input file.
    """
    result = AffectedItemsWazuhResult(
        all_msg='Statistical information for each node was successfully read',
        some_msg='Could not read statistical information for some nodes',
        none_msg='Could not read statistical information for any node'
    )
    result.affected_items = get_daemons_stats_(filename)
    result.total_affected_items = len(result.affected_items)

    return result
