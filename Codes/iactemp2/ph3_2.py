from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    Fn
)
from constructs import Construct

class Phase3RdsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import private subnet IDs exported from VPC stack
        private_subnet_ids = [
            Fn.import_value("subnet-02528be29bfc47e09"),
            Fn.import_value("subnet-016b9ad6ef00ba3d7"),
        ]

        # Create SubnetSelection for RDS to place it in private subnets
        private_subnet_selection = ec2.SubnetSelection(subnets=[
            ec2.Subnet.from_subnet_id(self, "ImportedSubnet1", private_subnet_ids[0]),
            ec2.Subnet.from_subnet_id(self, "ImportedSubnet2", private_subnet_ids[1]),
        ])

        # Create or import existing secret for RDS credentials (optional)
        db_secret = secretsmanager.Secret(self, "DBSecret",
        generate_secret_string=secretsmanager.SecretStringGenerator(
            secret_string_template='{"username":"mysql"}',
            generate_string_key="mysql",
            exclude_punctuation=True,
            password_length=16
        )
        )

        # Create RDS instance inside imported private subnets
        rds_instance = rds.DatabaseInstance(
            self, "MyRDSInstance",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0_28
            ),
            vpc=ec2.Vpc.from_lookup(self,"Phase3_Step1_VPC",vpc_id="vpc-04b181f2af261668f"),  # Optional: if you want to import entire VPC by ID
            vpc_subnets=private_subnet_selection,
            credentials=rds.Credentials.from_secret(db_secret),
            multi_az=True,
            allocated_storage=20,
            max_allocated_storage=100,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO
            ),
            publicly_accessible=False,
            deletion_protection=False
        )
