import boto3
from template import template
from config import config

client = boto3.client('cloudformation')

body = template()

response = client.update_stack(
    StackName='cc-worker',
    TemplateBody=body,
    Parameters=[
        {
            'ParameterKey': 'KeyName',
            'ParameterValue': config.get('DEFAULT','SSHKeyName')
        },
         {
            'ParameterKey': 'VPCAvailabilityZone1',
            'ParameterValue': config.get('DEFAULT','VPCAvailabilityZone1')
        },
         {
            'ParameterKey': 'VPCAvailabilityZone2',
            'ParameterValue': config.get('DEFAULT','VPCAvailabilityZone2')
        },
         {
            'ParameterKey': 'ApiSubnet1',
            'ParameterValue': config.get('DEFAULT','ApiSubnet1')
        },
         {
            'ParameterKey': 'ApiSubnet2',
            'ParameterValue': config.get('DEFAULT','ApiSubnet2')
        },
         {
            'ParameterKey': 'RootStackName',
            'ParameterValue': config.get('DEFAULT','RootStackName')
        },
         {
            'ParameterKey': 'SecurityGroup',
            'ParameterValue': config.get('DEFAULT','SecurityGroup')
        },
         {
            'ParameterKey': 'ImageId',
            'ParameterValue': config.get('DEFAULT','ImageId')
        },
         {
            'ParameterKey': 'InstanceType',
            'ParameterValue': config.get('DEFAULT','InstanceType')
        }
    ]
)

print(response)