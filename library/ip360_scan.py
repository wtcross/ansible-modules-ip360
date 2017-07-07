#!/usr/bin/env python

import xmlrpclib


def create_session(api_url, username, password):
    # Connect to the server and login
    server = xmlrpclib.ServerProxy(api_url)
    session = server.login(2, 0, username, password)
    return (server, session)


def close_session(server, session):
    server.logout(session)


def create_scan(server, session, device_profiler_instance, scan_profile_instance, network_instance, iprange):
    params = {'scanProfile': str(scan_profile_instance), 'network': network_instance, 'range': iprange}
    scan = server.call(session, device_profiler_instance, 'startScan', params)
    return scan


def device_profiler_search(server, session, device_profiler):
    search_params = dict(query="name = '%s'" % device_profiler)
    device_profiler_list = server.call(session, 'class.DP', 'search', search_params)
    return device_profiler_list


def scan_profile_search(server, session, scan_profile):
    params = dict(query="name = '%s'" % scan_profile)
    scan_profile_list = server.call(session, 'class.ScanProfile', 'search', params)
    return scan_profile_list


def network_search(server, session, network):
    params = dict(query="name = '%s'" % network)
    network_list = server.call(session, 'class.Network', 'search', params)
    return network_list


def main():
    module = AnsibleModule(
        argument_spec = dict(
           api_url = dict(required=True, default=None),
           username = dict(required=True, default=None),
           password = dict(required=True, default=None, no_log=True),
           device_profiler = dict(required=True),
           scan_profile = dict(required=True),
           network = dict(required=True),
           range = dict(required=False),
           wait_for_start = dict(required=False, default=None),
           start_timeout = dict(required=False, default=30)
        ),
        required_together = [['username', 'password']],
        supports_check_mode = False,
    )

    api_url = module.params['api_url']
    username = module.params['username']
    password = module.params['password']
    iprange = module.params['range']
    device_profiler = module.params['device_profiler']
    scan_profile = module.params['scan_profile']
    network = module.params['network']
    wait_for_start = module.params['wait_for_start']
    start_timeout = module.params['start_timeout']

    try:
        # Create a session with the IP360 XML-RPC API.
        server, session = create_session(api_url, username, password)

        # Search for a Device Profiler using the specified query.
        device_profiler_list = device_profiler_search(server, session, device_profiler)
        if not device_profiler_list:
            module.fail_json(
                msg='Could not find Device Profiler with specified query.')

        device_profiler_instance = device_profiler_list[0]

        # Search for the Scan Profile to use in the scan using the specified query.
        scan_profile_list = scan_profile_search(server, session, scan_profile)
        if not scan_profile_list:
            module.fail_json(
                msg='Could not find Scan Profile with specified query.')

        scan_profile_instance = scan_profile_list[0]

        # Search for the Network to scan using the specified query.
        network_list = network_search(server, session, network)
        if not network_list:
            module.fail_json(
                msg='Could not find Network with specified query.')
        network_instance = network_list[0]

        # Invoke IP360 API method call to start the Scan On Demand.
        scan = create_scan(server, session, device_profiler_instance, scan_profile_instance, network_instance, iprange)

        close_session(server, session)

        module.exit_json(changed=True, scan=scan)
    except xmlrpclib.Fault, fault:
        module.fail_json(
            msg='xmlrpclib fault: {0} {1}'.format(fault.faultCode, fault.faultString))
    except xmlrpclib.ProtocolError, error:
        module.fail_json(
            msg='xmlrpclib protocol error: {0} {1}'.format(error.errcode, error.errmsg))


from ansible.module_utils.basic import *
if __name__ == '__main__':
  main()
