from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_autoscaling as autoscaling,
    aws_iam as iam,
    CfnOutput,
    Duration
)
from constructs import Construct

class Phase4Step1(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, "ExistingVPC", vpc_id="vpc-054eb5eece4f19c11")

        # 🔐 Security Group for EC2
        app_sg = ec2.SecurityGroup.from_security_group_id(
            self,
            "ImportedAppSG",
            security_group_id="sg-048c2c9a1ea4b33e0"  # Replace with your actual SG ID
        )
        # 🔐 Security Group for ALB
        alb_sg = ec2.SecurityGroup(self, "ALBSecurityGroup",
            vpc=vpc,
            description="Allow internet HTTP access",
            allow_all_outbound=True,
        )
        alb_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow public HTTP")

        # User data script to start Node app
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            'cd ~/resources/codebase_partner',  # update path
            'sudo APP_PORT=80 npm start'
        ) 

        # 🖼️ AMI (Amazon Linux 2 or your custom AMI)
        ami = ec2.MachineImage.generic_linux({
            "us-east-1": "ami-05a0d251a74e33f91"  # replace with your AMI
        })

        # 🚀 Auto Scaling Group
        asg = autoscaling.AutoScalingGroup(self, "AppASG",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ami,
            min_capacity=2,
            max_capacity=4,
            desired_capacity=2,
            security_group=app_sg,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            user_data=user_data
        )

        # 🖥️ Application Load Balancer
        alb = elbv2.ApplicationLoadBalancer(self, "Project2_ALB",
            vpc=vpc,
            internet_facing=True,
            security_group=alb_sg,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )

        listener = alb.add_listener("Project2_Listener",
            port=80,
            open=True
        )

        listener.add_targets("Project2_Fleet",
            port=80,
            targets=[asg],
            health_check=elbv2.HealthCheck(
                path="/",
                interval=Duration.seconds(30)
            )
        )

        # 🔁 CPU-based auto scaling
        asg.scale_on_cpu_utilization("CpuScaling",
            target_utilization_percent=50
        )

        # 📤 Output
        CfnOutput(self, "ALBDNS",
            value=alb.load_balancer_dns_name,
            description="DNS name of the load balancer"
        )
