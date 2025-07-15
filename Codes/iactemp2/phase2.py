# phase2_single_vm_stack.py
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct

class Phase2SingleVMStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC with a single public subnet
        vpc = ec2.Vpc(
            self, "Pro2_Phase1",
            cidr="10.0.0.0/16",
            max_azs=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ],
            nat_gateways=0,
            restrict_default_security_group=False
        )

        # Create Security Group for EC2
        ec2_sg = ec2.SecurityGroup(
            self, "EC2SecurityGroup",
            vpc=vpc,
            description="Allow HTTP and SSH",
            allow_all_outbound=True
        )

        ec2_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP"
        )
        ec2_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH"
        )


        # IAM Role for EC2
        role = iam.Role.from_role_arn(
            self, "ImportedLambdaRole",
            role_arn="arn:aws:iam::528316341503:role/LabRole",
            mutable=False  # set to True if you plan to modify the role with CDK
        )

        # EC2 instance
        instance = ec2.Instance(
            self, "Project2-Phase1",
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage.generic_linux({
                "us-east-1": "ami-020cba7c55df1f615"
            }),
            vpc=vpc,
            vpc_subnets={"subnet_type": ec2.SubnetType.PUBLIC},
            security_group=ec2_sg,
            role=role,
            key_name="Project2"
        )

        # User data to install the application and database from script
        instance.user_data.add_commands(
        "sudo apt update -y",
        "sudo apt install -y curl unzip",

        "curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -",
        "sudo apt install -y nodejs",

        "curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'",
        "unzip awscliv2.zip",
        "sudo ./aws/install",

        "aws s3 cp s3://task2-lambda-bucket-s3/UserdataScript-phase-2.sh . --region us-east-1",
        "chmod +x UserdataScript-phase-2.sh",
        "sudo ./UserdataScript-phase-2.sh > userdata.log 2>&1",
        "tail -n 50 userdata.log"
    )


