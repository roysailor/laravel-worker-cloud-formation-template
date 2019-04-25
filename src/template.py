from troposphere import Base64, Join
from troposphere import Parameter, Ref, Template, Tags
from troposphere import cloudformation, autoscaling
from troposphere.autoscaling import AutoScalingGroup, Tag
from troposphere.autoscaling import LaunchConfiguration
from troposphere.policies import (
    AutoScalingReplacingUpdate, AutoScalingRollingUpdate, UpdatePolicy
)
import troposphere.ec2 as ec2


def template():

    t = Template()

    keyname_param = t.add_parameter(Parameter(
        "KeyName",
        Description="Name of an existing EC2 KeyPair to enable SSH access to the instance",
        Type="String"
    ))

    image_id_param = t.add_parameter(Parameter(
        "ImageId",
        Description="ImageId of the EC2 instance",
        Type="String"
    ))

    instance_type_param = t.add_parameter(Parameter(
        "InstanceType",
        Description="Type of the EC2 instance",
        Type="String"
    ))

    ScaleCapacity = t.add_parameter(Parameter(
    "ScaleCapacity",
    Default="1",
    Type="String",
    Description="Number of api servers to run",
    ))

    VPCAvailabilityZone2 = t.add_parameter(Parameter(
        "VPCAvailabilityZone2",
        MinLength="1",
        Type="String",
        Description="Second availability zone",
        MaxLength="255",
    ))

    VPCAvailabilityZone1 = t.add_parameter(Parameter(
        "VPCAvailabilityZone1",
        MinLength="1",
        Type="String",
        Description="First availability zone",
        MaxLength="255",
    ))

    SecurityGroup = t.add_parameter(Parameter(
    "SecurityGroup",
    Type="String",
    Description="Security group.",
    ))

    RootStackName = t.add_parameter(Parameter(
        "RootStackName",
        Type="String",
        Description="The root stack name",
    ))

    ApiSubnet2 = t.add_parameter(Parameter(
        "ApiSubnet2",
        Type="String",
        Description="Second private VPC subnet ID for the api app.",
    ))

    ApiSubnet1 = t.add_parameter(Parameter(
        "ApiSubnet1",
        Type="String",
        Description="First private VPC subnet ID for the api app.",
    ))


    #####################################################
    # Launch Configuration
    #####################################################
    LaunchConfig = t.add_resource(LaunchConfiguration(
    "LaunchConfiguration",
    Metadata=autoscaling.Metadata(
        cloudformation.Init(
            cloudformation.InitConfigSets(
                InstallAndRun=['Install']
            ),
            Install=cloudformation.InitConfig(
                packages={
                    "apt" : {
                        "curl": [],
                        "zip": [],
                        "unzip": [],
                        "git": [],
                        "supervisor": [],
                        "sqlite3": [],
                        "nginx": [],
                        "php7.2-fpm": []
                    }
                },
                files=cloudformation.InitFiles({
                    "/etc/nginx/sites-available/default": cloudformation.InitFile(
                        content=Join('', [
                            "server {",
                            "   listen 80 default_server;",
                            "   root /var/www/html/public;",
                            "   index index.html index.htm index.php;",
                            "   server_name _;",
                            "   charset utf-8;",
                            "   location = /favicon.ico { log_not_found off; access_log off; }",
                            "   location = /robots.txt  { log_not_found off; access_log off; }",
                            "   location / {",
                            "       try_files $uri $uri/ /index.php$is_args$args;",
                            "   }",
                            "   location ~ \.php$ {",
                            "       include snippets/fastcgi-php.conf;",
                            "       fastcgi_pass unix:/run/php/php7.2-fpm.sock;",
                            "   }",
                            "   error_page 404 /index.php;",
                            "}"
                        ])
                    ),
                    "/etc/supervisor/conf.d/supervisord.conf": cloudformation.InitFile(
                        content=Join('',[
                            "[supervisord]",
                            "nodaemon=true",
                            "[program:nginx]",
                            "command=nginx",
                            "stdout_logfile=/dev/stdout",
                            "stdout_logfile_maxbytes=0",
                            "stderr_logfile=/dev/stderr",
                            "stderr_logfile_maxbytes=0",
                            "[program:php-fpm]",
                            "command=php-fpm7.2",
                            "stdout_logfile=/dev/stdout",
                            "stdout_logfile_maxbytes=0",
                            "stderr_logfile=/dev/stderr",
                            "stderr_logfile_maxbytes=0",
                            "[program:horizon]",
                            "process_name=%(program_name)s",
                            "command=php /var/www/html/artisan horizon",
                            "autostart=true",
                            "autorestart=true",
                            "user=root",
                            "redirect_stderr=true",
                            "stdout_logfile=/var/www/html/storage/logs/horizon.log",
                        ])
                    ),
                    "/etc/php/7.2/fpm/php-fpm.conf": cloudformation.InitFile(
                        content=Join('',[
                            "[global]",
                            "pid = /run/php/php7.2-fpm.pid",
                            "error_log = /proc/self/fd/2",
                            "include=/etc/php/7.2/fpm/pool.d/*.conf"
                        ])
                    )
                })
            )
        ),
    ),
    UserData=Base64(Join('', [
        "#!/bin/bash -xe\n",
        "apt-get update -y\n",
        "apt-get install -y ruby\n",
        "wget https://aws-codedeploy-ap-south-1.s3.amazonaws.com/latest/install\n",
        "chmod +x ./install\n",
        "./install auto\n",
        "service codedeploy-agent start\n",
        "apt-get install -y software-properties-common python-software-properties\n",
        "add-apt-repository -y ppa:ondrej/php\n",
        "apt-get update -y\n",
        "apt-get install -y python-setuptools\n",
        "mkdir -p /opt/aws/bin\n",
        "wget https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz\n",
        "easy_install --script-dir /opt/aws/bin aws-cfn-bootstrap-latest.tar.gz\n",
        "# Install the files and packages from the metadata\n",
        "/opt/aws/bin/cfn-init -v ",
        " --stack ", Ref("AWS::StackName"),
        " --resource LaunchConfiguration",
        " --configsets InstallAndRun ",
        " --region ", Ref("AWS::Region"), "\n",
        "# Signal the status from cfn-init\n",
        "cfn-signal -e 0",
        "    --resource AutoscalingGroup",
        "    --stack ", Ref("AWS::StackName"),
        "    --region ", Ref("AWS::Region"), "\n"
    ])),
    ImageId=Ref("ImageId"),
    KeyName=Ref(keyname_param),
    BlockDeviceMappings=[
        ec2.BlockDeviceMapping(
            DeviceName="/dev/sda1",
            Ebs=ec2.EBSBlockDevice(
                VolumeSize="8"
            )
        ),
    ],
    InstanceType=Ref("InstanceType"),
    IamInstanceProfile="CodeDeployDemo-EC2-Instance-Profile",
    SecurityGroups=[Ref(SecurityGroup)]
    ))

    #####################################################
    # AutoScaling Groups
    #####################################################
    AutoscalingGroup = t.add_resource(AutoScalingGroup(
    "AutoscalingGroup",
    DesiredCapacity=Ref(ScaleCapacity),
    Tags=[
        Tag("App","cc-worker",True),
        Tag("Name","cc-worker", True)
    ],
    LaunchConfigurationName=Ref(LaunchConfig),
    MinSize=Ref(ScaleCapacity),
    MaxSize=Ref(ScaleCapacity),
    VPCZoneIdentifier=[Ref(ApiSubnet1), Ref(ApiSubnet2)],
    AvailabilityZones=[Ref(VPCAvailabilityZone1), Ref(VPCAvailabilityZone2)],
    HealthCheckType="EC2",
    UpdatePolicy=UpdatePolicy(
        AutoScalingReplacingUpdate=AutoScalingReplacingUpdate(
            WillReplace=True,
        ),
        AutoScalingRollingUpdate=AutoScalingRollingUpdate(
            PauseTime='PT5M',
            MinInstancesInService="1",
            MaxBatchSize='1',
            WaitOnResourceSignals=True
        )
    )
    ))

    return t.to_json()