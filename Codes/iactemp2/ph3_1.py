from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

class Phase3CombinedStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # --- STEP 1: Create VPC with Public + Private Subnets ---
        vpc = ec2.Vpc(
            self, "Phase3VPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            nat_gateways=1,
            restrict_default_security_group=False,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # --- STEP 2: Create Security Group for RDS ---
        rds_sg = ec2.SecurityGroup(
            self, "RDSSecurityGroup",
            vpc=vpc,
            description="Allow MySQL access from migration EC2",
            allow_all_outbound=True
        )

        rds_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("10.0.0.164/32"),  # Replace with your EC2's public IP
            connection=ec2.Port.tcp(3306),
            description="Allow MySQL access from EC2"
        )

        # --- STEP 3: Create RDS Secret for Credentials ---
        db_secret = secretsmanager.Secret(self, "DBSecret34",
                                          generate_secret_string=secretsmanager.SecretStringGenerator(
            secret_string_template='{"username":"admin"}',
            generate_string_key="password",
            exclude_punctuation=True,
            password_length=16
        ))
        # --- STEP 4: Deploy RDS in Public Subnets for temporary migration ---
        rds.DatabaseInstance(
            self, "MyRDSInstance",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0_34
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            credentials=rds.Credentials.from_secret(db_secret),
            multi_az=False,  # Keep it simple for migration
            allocated_storage=20,
            max_allocated_storage=100,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO
            ),
            security_groups=[rds_sg],
            publicly_accessible=True,
            deletion_protection=False
        )
