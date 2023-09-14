#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2023, JIHUN KIM <jihunkimkw@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: codedeploy_application
version_added: 6.4.0
short_description: Manage applications in AWS CodeDeploy
description:
  - The M(community.aws.codedeploy_application) module allows you to create, update, and delete of CodeDeploy applications.
author:
  - JIHUN KIM (@shblue21)
options:
  application_name:
    description: The name of the application.
    required: true
    type: str
  new_application_name:
    description: The new name of the application.
    required: false
    type: str
  state:
    description: Create (C(present)) or delete (C(absent)) application.
    required: true
    choices: ['present', 'absent']
    type: str
extends_documentation_fragment:
  - amazon.aws.common.modules
  - amazon.aws.region.modules
  - amazon.aws.boto3
"""

EXAMPLES = r"""
# Create a new codedeploy application
- community.aws.codedeploy_application:
    application_name: codedeploy-app
    state: present

# Update a codedeploy application name
- community.aws.codedeploy_application:
    application_name: codedeploy-app
    new_application_name: codedeploy-app-new
    state: present

# Delete a codedeploy application
- community.aws.codedeploy_application:
    application_name: codedeploy-app
    state: absent
"""

RETURN = r"""
application:
  description: Returns information about the application.
  returned: When I(state) is C(present)
  type: complex
  contains:
    application_id:
      description: The application ID.
      type: str
      returned: always
    application_name:
      description: The application name.
      type: str
      returned: always
    compute_platform:
      description: The destination platform type for deployment of the application.
      type: str
      returned: always
    create_time:
      description: The time at which the application was created.
      type: str
      returned: always
    github_account_name:
      description: The name for a connection to a GitHub account.
      type: str
      returned: when I(compute_platform) is C(Server)
    linked_to_git_hub:
      description: True if the user has authenticated with GitHub for the specified application.
      type: bool
      returned: always
"""

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError

from ansible_collections.community.aws.plugins.module_utils.modules import AnsibleCommunityAWSModule as AnsibleAWSModule
from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict


class CodeDeployAnsibleAWSError(AnsibleAWSError):
    pass


def _create_application(client, module):
    try:
        response = client.create_application(
            applicationName=module.params["application_name"],
            computePlatform=module.params["compute_platform"],
        )
        return response
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        CodeDeployAnsibleAWSError(exception=e, message="couldn't create application")


def _update_application(client, module):
    try:
        response = client.update_application(
            applicationName=module.params["application_name"],
            newApplicationName=module.params["new_application_name"],
        )
        return response  # It'll be None
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        CodeDeployAnsibleAWSError(exception=e, message="couldn't update application")


def _delete_application(client, module):
    try:
        response = client.delete_application(applicationName=module.params["application_name"])
        return response  # It'll be None
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        CodeDeployAnsibleAWSError(exception=e, message="couldn't delete application")


def _get_application(client, applicationName):
    try:
        response = client.get_application(applicationName=applicationName)
        return response
    except is_boto3_error_code("ApplicationDoesNotExistException"):
        return None
    except (botocore.exceptions.BotoCoreError, botocore.exceptions.ClientError) as e:
        CodeDeployAnsibleAWSError(exception=e, message="couldn't get application")


def ensure_application_present(client, module):
    application_name = module.params["application_name"]
    changed = False
    if _get_application(client, module.params["application_name"]) is None:
        if not module.check_mode:
            _response = _create_application(client, module)
        changed = True
    else:
        if not module.check_mode:
            _response = _update_application(client, module)
            application_name = module.params["new_application_name"]
        changed = True
    result = {"changed": changed}

    application = _get_application(client, application_name)
    if application is None:
        result["application"] = None
        return result
    else:
        application_result = camel_dict_to_snake_dict(application)
        result.update(application_result)
        return result


def ensure_application_absent(client, module):
    changed = False
    if _get_application(client, module.params["application_name"]) is None:
        return {"changed": changed}
    else:
        if not module.check_mode:
            _response = _delete_application(client, module)
        changed = True
    return {"changed": changed}


def main():
    argument_spec = dict(
        application_name=dict(type="str", required=True),
        new_application_name=dict(type="str", required=False),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        compute_platform=dict(type="str", required=False, choices=["Lambda", "Server", "ECS"]),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True)

    client = module.client("codedeploy")

    try:
        if module.params["state"] == "present":
            result = ensure_application_present(client, module)
        elif module.params["state"] == "absent":
            result = ensure_application_absent(client, module)
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
