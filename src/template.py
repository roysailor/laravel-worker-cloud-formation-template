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
                        "php7.2-fpm":[],
                        "php7.2-cli":[],
                        "php7.2-pgsql":[],
                        "php7.2-sqlite3":[],
                        "php7.2-gd":[],
                        "php7.2-curl":[],
                        "php7.2-memcached":[],
                        "php7.2-imap":[],
                        "php7.2-mysql":[],
                        "php7.2-mbstring":[],
                        "php7.2-xml":[],
                        "php7.2-zip":[],
                        "php7.2-bcmath":[],
                        "php7.2-soap":[],
                        "php7.2-intl":[],
                        "php7.2-readline":[],
                        "php-msgpack":[],
                        "php-igbinary":[]
                    }
                },
                files=cloudformation.InitFiles({
                    "/etc/nginx/sites-available/default": cloudformation.InitFile(
                        content=Join('', [
                            "server {\n",
                            "   listen 80 default_server;\n",
                            "   root /var/www/html/public;\n",
                            "   index index.html index.htm index.php;\n",
                            "   server_name _;\n",
                            "   charset utf-8;\n",
                            "   location = /favicon.ico { log_not_found off; access_log off; }\n",
                            "   location = /robots.txt  { log_not_found off; access_log off; }\n",
                            "   location / {\n",
                            "       try_files $uri $uri/ /index.php$is_args$args;\n",
                            "   }\n",
                            "   location ~ \.php$ {\n",
                            "       include snippets/fastcgi-php.conf;\n",
                            "       fastcgi_pass unix:/run/php/php7.2-fpm.sock;\n",
                            "   }\n",
                            "   error_page 404 /index.php;\n",
                            "}\n"
                        ])
                    ),
                    "/etc/supervisor/conf.d/supervisord.conf": cloudformation.InitFile(
                        content=Join('',[
                            "[supervisord]\n",
                            "nodaemon=true\n",
                            "[program:nginx]\n",
                            "command=nginx\n",
                            "stdout_logfile=/dev/stdout\n",
                            "stdout_logfile_maxbytes=0\n",
                            "stderr_logfile=/dev/stderr\n",
                            "stderr_logfile_maxbytes=0\n",
                            "[program:php-fpm]\n",
                            "command=php-fpm7.2\n",
                            "stdout_logfile=/dev/stdout\n",
                            "stdout_logfile_maxbytes=0\n",
                            "stderr_logfile=/dev/stderr\n",
                            "stderr_logfile_maxbytes=0\n",
                            "[program:horizon]\n",
                            "process_name=%(program_name)s\n",
                            "command=php /var/www/html/artisan horizon\n",
                            "autostart=true\n",
                            "autorestart=true\n",
                            "user=root\n",
                            "redirect_stderr=true\n",
                            "stdout_logfile=/var/www/html/storage/logs/horizon.log\n",
                        ])
                    ),
                    "/etc/php/7.2/fpm/php-fpm.conf": cloudformation.InitFile(
                        content=Join('',[
                            "[global]\n",
                            "pid = /run/php/php7.2-fpm.pid\n",
                            "error_log = /proc/self/fd/2\n",
                            "include=/etc/php/7.2/fpm/pool.d/*.conf\n"
                        ])
                    )
                })
            )
        ),
    ),
    UserData=Base64(Join('', [
        "#!/bin/bash -xe\n",
        "apt-get update -y\n",
        "apt-get install -y language-pack-en-base\n",
        "export LC_ALL=en_US.UTF-8\n",
        "export LANG=en_US.UTF-8\n",
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
        " --region ", Ref("AWS::Region"), "\n"
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