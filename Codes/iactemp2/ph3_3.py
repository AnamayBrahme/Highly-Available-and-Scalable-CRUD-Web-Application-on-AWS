from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct

class Phase3Step3(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import existing VPC by ID
        vpc = ec2.Vpc.from_lookup(self, "ExistingVPC", vpc_id="vpc-054eb5eece4f19c11")

        # Create Security Group for EC2 in the existing VPC
        ec2_sg = ec2.SecurityGroup(
            self, "EC2SecurityGroup",
            vpc=vpc,
            description="Allow HTTP and SSH",
            allow_all_outbound=True
        )
        ec2_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP")
        ec2_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow SSH")

        # IAM Role for EC2 - imported from existing role ARN
        role = iam.Role.from_role_arn(
            self, "ImportedLambdaRole",
            role_arn="arn:aws:iam::528316341503:role/LabRole",
            mutable=False
        )

        # EC2 instance in existing VPC public subnet
        instance = ec2.Instance(
            self, "Project2-Phase3_Step3",
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.MachineImage.generic_linux({
                "us-east-1": "ami-020cba7c55df1f615"
            }),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=ec2_sg,
            role=role,
            key_name="Project2"
        )
        rds_sg = ec2.SecurityGroup.from_security_group_id(self, "RDSSecurityGroup", "sg-029af30866459c533")
        rds_sg.add_ingress_rule(
            peer=ec2_sg,
            connection=ec2.Port.tcp(3306),
            description="Allow EC2 instance to connect to RDS MySQL"
        )


        # User data (same as before)
        instance.user_data.add_commands(
            "sudo apt update -y",
            "sudo apt install -y curl unzip",
            "aws s3 cp s3://task2-lambda-bucket-s3/UserdataScript-phase-3.sh . --region us-east-1",
            "chmod +x UserdataScript-phase-3.sh",
            "sudo ./UserdataScript-phase-3.sh > userdata.log 2>&1",
            "tail -n 50 userdata.log"
        )
