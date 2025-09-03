from aws_cdk import (
    Stack,
    SecretValue,
    RemovalPolicy,
    CfnOutput,
    aws_redshift as redshift,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    aws_s3 as s3
)
from constructs import Construct

class RedshiftStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prefix = f"{config['tenant']}-{config['env']}"

        # VPC
        vpc_config = config["vpc"]
        vpc = ec2.Vpc(
            self,
            f"{prefix}-vpc",
            ip_addresses=ec2.IpAddresses.cidr(vpc_config["cidr"]),
            max_azs=vpc_config["max_azs"],
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name=subnet["name"].replace("Subnet", ""),
                    subnet_type=ec2.SubnetType[subnet["type"]],
                    cidr_mask=subnet["cidr_mask"]
                )
                for subnet in vpc_config["subnets"]
            ]
        )

        # Security Group
        redshift_sg = ec2.SecurityGroup(
            self,
            f"{prefix}-sg",
            vpc=vpc,
            description="Redshift security group",
            allow_all_outbound=True
        )
        redshift_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(5439),
            description="Allow Redshift access"
        )

        # IAM Role
        redshift_role = iam.Role(
            self,
            f"{prefix}-role",
            assumed_by=iam.ServicePrincipal("redshift.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonRedshiftAllCommandsFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite")
            ]
        )

        # S3 Bucket
        sales_bucket = s3.Bucket(
            self,
            f"{prefix}-sales-bucket",
            bucket_name=f"{prefix}-redshift-data",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
        sales_bucket.grant_read(redshift_role)

        # Secrets Manager
        redshift_secret = secretsmanager.Secret(
            self,
            f"{prefix}-secret",
            secret_name=config["redshift"]["secret_name"],
            secret_object_value={
                "username": SecretValue.unsafe_plain_text(config["redshift"]["master_username"]),
                "password": SecretValue.unsafe_plain_text("YourStrongPassword123!"),
                "engine": SecretValue.unsafe_plain_text("redshift"),
                "host": SecretValue.unsafe_plain_text("placeholder-host"),
                "port": SecretValue.unsafe_plain_text("5439"),
                "dbname": SecretValue.unsafe_plain_text(config["redshift"]["database_name"])
            }
        )

        # Subnet Group
        redshift_subnet_group = redshift.CfnClusterSubnetGroup(
            self,
            f"{prefix}-subnet-group",
            description="Redshift subnet group",
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
            tags=[{"key": "Name", "value": f"{prefix}-subnet-group"}]
        )

        # Redshift Cluster
        redshift_cluster = redshift.CfnCluster(
            self,
            f"{prefix}-cluster",
            cluster_identifier=config["redshift"]["cluster_identifier"],
            cluster_type=config["redshift"]["cluster_type"],
            node_type=config["redshift"]["node_type"],
            number_of_nodes=config["redshift"]["number_of_nodes"],
            master_username=config["redshift"]["master_username"],
            master_user_password="YourStrongPassword123!",
            db_name=config["redshift"]["database_name"],
            iam_roles=[redshift_role.role_arn],
            vpc_security_group_ids=[redshift_sg.security_group_id],
            cluster_subnet_group_name=redshift_subnet_group.ref
        )

        # Outputs
        CfnOutput(self, f"{prefix}-bucket-name", value=sales_bucket.bucket_name)
        CfnOutput(self, f"{prefix}-secret-arn", value=redshift_secret.secret_arn)
        CfnOutput(self, f"{prefix}-cluster-id", value=redshift_cluster.cluster_identifier)

