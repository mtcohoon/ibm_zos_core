# -*- coding: utf-8 -*-

# Copyright (c) IBM Corporation 2019, 2020
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION =r'''
---
module: zos_operator_action_query
short_description: Display outstanding messages requiring operator action.
description:
    - Get a list of outstanding messages requiring operator action given one or more conditions.
author: Ping Xiao <xiaoping@cn.ibm.com>
options:
  system:
    description:
        Return outstanding messages requiring operator action awaiting a reply for a particular system. 
        If the system name is not specified, all outstanding messages for that system and for 
        the local systems attached to it are returned. Wildcards are unsupported.
    type: str
    required: false
  message_id:
    description:
        Return outstanding messages requiring operator action awaiting a reply for a particular message 
        identifier. A trailing asterisk (*) wildcard is supported. 
    type: str
    required: false
  job_name:
    description:
      - Return outstanding messages requiring operator action awaiting a reply for a particular job name .
    type: str
    required: false
seealso: 
- module: zos_operator
'''

EXAMPLES =r'''
- name: Display all outstanding messages issued on system MV2H
  zos_operator_outstanding_action:
      system: mv2h

- name: Display all outstanding messages whose job name begin with im5
  zos_operator_outstanding_action:
      job_name: im5*

- name: Display all outstanding messages whose message id begin with dsi*
  zos_operator_outstanding_action:
      message_id: dsi*

- name: Display all outstanding messages given job_name, message_id, system
  zos_operator_outstanding_action:
      job_name: mq*
      message_id: dsi*
      system: mv29
'''

RETURN = r'''
changed: 
      description: Indicates if any changes were made during module operation. Given operator 
      action commands query for messages, True is always returned unless either a module or 
      command failure has occurred. 
    returned: always
    type: bool
count:
    description: The total number of outstanding messages.
    returned: success
    type: int
actions:
    description: The list of the outstanding messages
    returned: success
    type: list[dict]
    contains:
        number:
            description: The message identification number
            returned: success
            type: int
            sample: 001
        type:
            description: The action type,'R' means request
            returned: success
            type: str
            sample: R
        system:
            description: System on which the outstanding message requiring operator action awaiting a reply.
            returned: success
            type: str
            sample: MV27
        job_id: 
            description: Job identifier for the outstanding message requiring operator action awaiting a reply.
            returned: success
            type: str
            sample: STC01537
        message_text:
            description: Job identifier for outstanding message requiring operator action awaiting a reply.
            returned: success
            type: str
            sample: *399 HWSC0000I *IMS CONNECT READY* IM5HCONN
        job_name: 
            description: Job name for outstanding message requiring operator action awaiting a reply.
            returned: success
            type: str
            sample: IM5HCONN
        message_id: 
            description: Message identifier for outstanding message requiring operator action awaiting a reply.
            returned: success
            type: str
            sample: HWSC0000I
    sample:
        {
            "actions": 
            [
                {
                    "number": '001',
                    "type": 'R',
                    "system": 'MV27',
                    "job_id": 'STC01537',
                    "message_text": '*399 HWSC0000I *IMS CONNECT READY* IM5HCONN',
                    "job_name": 'IM5HCONN',
                    "message_id": 'HWSC0000I'
                    },
                    {
                    "number": '002',
                    "type": 'R',
                    "system": 'MV27',
                    "job_id": 'STC01533',
                    "message_text": '*400 DFS3139I IMS INITIALIZED, AUTOMATIC RESTART PROCEEDING IM5H',
                    "job_name": 'IM5HCTRL',
                    "message_id": 'DFS3139I'
                }
            ]
        }
'''

from ansible.module_utils.basic import AnsibleModule
import argparse
import re
from traceback import format_exc
from ansible_collections.ibm.ibm_zos_core.plugins.module_utils.better_arg_parser import BetterArgParser
from zoautil_py import OperatorCmd

def run_module():
    module_args = dict(
        system=dict(type='str',required=False),
        message_id=dict(type='str',required=False),
        job_name=dict(type='str',required=False)
    )

    result = dict(
        changed=False
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    try:
        new_params = parse_params(module.params)
        requests = find_required_request(new_params)
        if requests:
            result['count'] = len(requests)
    except Error as e:
        module.fail_json(msg=e.msg, **result)
    except Exception as e:
        trace = format_exc()
        module.fail_json(msg='An unexpected error occurred: {0}'.format(trace), **result)
    result['actions'] = requests
    module.exit_json(**result)

def parse_params(params):
    arg_defs=dict(
        system=dict(
            arg_type=system_type,
            required=False
        ),
        message_id=dict(
            arg_type=message_id_type,
            required=False
        ),
        job_name=dict(
            arg_type=job_name_type,
            required=False
        )
    )
    parser = BetterArgParser(arg_defs)
    new_params = parser.parse_args(params)
    return new_params

    parser = BetterArgParser(arg_defs)
def system_type(arg_val, params):
    if arg_val and arg_val!='*':
        arg_val = arg_val.strip('*')
    value=arg_val
    regex='^[a-zA-Z0-9]{1,8}$'
    validate_parameters_based_on_regex(value,regex)
    return arg_val

def message_id_type(arg_val, params):
    if arg_val and arg_val!='*':
        arg_val = arg_val.strip('*')
    value=arg_val
    regex='^[a-zA-Z0-9]{1,8}$'
    validate_parameters_based_on_regex(value,regex)
    return arg_val

def job_name_type(arg_val, params):
    if arg_val and arg_val!='*':
        arg_val = arg_val.strip('*')
    value=arg_val
    regex='^[a-zA-Z0-9]{1,8}$'
    validate_parameters_based_on_regex(value,regex)
    return arg_val

def validate_parameters_based_on_regex(value,regex):
    pattern = re.compile(regex)
    if pattern.search(value):
        pass
    else:
        raise ValidationError(str(value))
    return value


def find_required_request(params):
    """find the request given the options provided."""
    merged_list = create_merge_list()
    requests = filter_requests(merged_list,params)
    if requests:
        pass
    else:
        message='There is no such request given the condition, check your command or update your options.'
        raise OperatorCmdError(message)
    return requests

def create_merge_list():
    """merge the return lists that execute both 'd r,a,s' and 'd r,a,jn'
    'd r,a,s' response like: "742 R MV28     JOB57578 &742 ARC0055A REPLY 'GO' OR 'CANCEL'"
    'd r,a,jn' response like:"742 R FVFNT29H &742 ARC0055A REPLY 'GO' OR 'CANCEL'"
    so we need merge the result so that to get a full list of information given a condition"""
    operator_cmd_a = 'd r,a,s'
    operator_cmd_b = 'd r,a,jn'
    message_a = execute_command(operator_cmd_a)
    message_b = execute_command(operator_cmd_b)
    list_a = parse_result_a(message_a)
    list_b = parse_result_b(message_b)
    merged_list = merge_list(list_a,list_b)
    return merged_list

def filter_requests(merged_list,params):
    """filter the request given the params provided."""
    system = params.get('system')
    message_id = params.get('message_id')
    job_name = params.get('job_name')
    newlist = merged_list
    if system:
        newlist = handle_conditions(newlist,'system',system.upper().strip('*'))
    if job_name:
        newlist = handle_conditions(newlist,'job_name',job_name.upper().strip('*'))
    if message_id:
        newlist = handle_conditions(newlist,'message_id',message_id.upper().strip('*'))
    return newlist

def handle_conditions(list,condition_type,condition_values):
    regex = re.compile(condition_values)
    newlist = []
    for dict in list:
        exist = regex.search(dict.get(condition_type))
        if exist:
            newlist.append(dict)
    return newlist

def execute_command(operator_cmd):
    rc_message = OperatorCmd.execute(operator_cmd)
    rc = rc_message.get('rc')
    message = rc_message.get('message')
    if rc > 0:
        raise OperatorCmdError(message)
    return message

def parse_result_a(result):
    """parsing the result that coming from command 'd r,a,s', there are usually two format:
    line with job_id: 810 R MV2D     JOB58389 &810 ARC0055A REPLY 'GO' OR 'CANCEL'  or
    line without job_id: 574 R MV28              *574 IXG312E OFFLOAD DELAYED FOR..
    also some of the request contains multiple lines, we need to handle that as well"""
    dict_temp = {}
    list = []
    request_temp=''
    end_flag = False
    lines = result.split('\n')
    regex = re.compile(r'\s+')

    for index,line in enumerate(lines):
        line = line.strip()
        #handle pattern"742 R FVFNT29H &742 ARC0055A REPLY 'GO' OR 'CANCEL'"
        pattern_without_job_id = re.compile(r'\s*[0-9]{2,}\s[A-Z]{1}\s[a-zA-Z0-9]{1,8}')
        # handle pattern "742 R MV28     JOB57578 &742 ARC0055A REPLY 'GO' OR 'CANCEL'"
        pattern_with_job_id = re.compile(r'\s*[0-9]{2,}\s[A-Z]{1}\s[A-Z0-9]{1,8}\s+[A-Z0-9]{1,8}\s')
        m = pattern_without_job_id.search(line)
        n = pattern_with_job_id.search(line)

        if index == (len(lines)-1):
            endflag = True
        if n or m or end_flag:
            if request_temp:
                dict_temp['message_text']=request_temp
                list.append(dict_temp)
                request_temp=''
                dict_temp = {}
            if n:
                elements = regex.split(line,4)
                dict_temp = {'number':elements[0],'type':elements[1],'system':elements[2],'job_id':elements[3]}
                request_temp = elements[4].strip()
                continue
            if m:
                elements = line.split(' ',3)
                dict_temp = {'number':elements[0],'type':elements[1],'system':elements[2]}
                request_temp = elements[3].strip()
                continue
        else:
            if request_temp:
                request_temp = request_temp +' '+line
    return list


def parse_result_b(result):
    """parsing the result that coming from command 'd r,a,jn' the main purpose to use this command is 
    to get the job_name and message id, which is not included in 'd r,a,s' """
    dict_temp = {}
    list = []
    lines = result.split('\n')
    regex = re.compile(r'\s+')
    for index,line in enumerate(lines):
        line = line.strip()
        pattern_with_job_name = re.compile(r'\s*[0-9]{2,}\s[A-Z]{1}\s[A-Z0-9]{1,8}\s+')
        m = pattern_with_job_name.search(line)
        if m:
            elements = regex.split(line,5)
            # 215 R IM5GCONN *215 HWSC0000I *IMS CONNECT READY*  IM5GCONN
            dict_temp = {'number':elements[0],'job_name':elements[2],'message_id':elements[4]}
            list.append(dict_temp)
            continue
    return list

def merge_list(list_a,list_b):
    merged_list = []
    for dict_a in list_a:
        for dict_b in list_b:
            if dict_a.get('number') == dict_b.get('number'):
                dict_z = dict_a.copy()
                dict_z.update(dict_b)
                merged_list.append(dict_z)
    return merged_list


class Error(Exception):
    pass

class ValidationError(Error):
    def __init__(self, message):
        self.msg = 'An error occurred during validate the input parameters: "{0}"'.format(message)

class OperatorCmdError(Error):
    def __init__(self, message):
        self.msg = 'An error occurred during issue the operator command, the response is "{0}"'.format(message)

def main():
    run_module()

if __name__ == '__main__':
    main()