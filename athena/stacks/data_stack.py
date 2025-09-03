from aws_cdk import (
    Stack,
    RemovalPolicy,
    Tags,
    aws_s3 as s3,
    aws_glue as glue,
    aws_athena as athena
)
from constructs import Construct

class DataStack(Stack):
    def __init__(self, scope: Construct, id: str, config: dict, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Determine if auto-delete should be enabled (avoid in prod)
        auto_delete = config["tags"]["Environment"].lower() != "prod"

        # S3 Bucket
        bucket_name = f"{id}-bucket{config['s3_bucket_suffix']}"
        bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=bucket_name,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=auto_delete
        )

        # Glue Database
        glue_db = glue.CfnDatabase(
            self,
            "GlueDatabase",
            catalog_id=self.account,
            database_input={
                "name": config["glue_database"]
            }
        )

        # Athena Workgroup
        athena_workgroup = athena.CfnWorkGroup(
            self,
            "AthenaWorkgroup",
            name=config["athena_workgroup"],
            work_group_configuration={
                "resultConfiguration": {
                    "outputLocation": f"s3://{bucket.bucket_name}/athena-results/"
                }
            }
        )

        # Apply Tags to all resources in the stack
        for key, value in config["tags"].items():
            Tags.of(self).add(key, value)

