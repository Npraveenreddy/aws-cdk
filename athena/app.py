import yaml
from aws_cdk import App, Environment
from stacks.data_stack import DataStack

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

app = App()

tenant = app.node.try_get_context("tenant")
env_name = app.node.try_get_context("env")

config = load_config()
tenant_env_config = config[tenant][env_name]

DataStack(
    app,
    f"{tenant}-{env_name}-data-stack",
    config=tenant_env_config,
    env=Environment(
        account=tenant_env_config["account_id"],
        region=tenant_env_config["region"]
    )
)

app.synth()

