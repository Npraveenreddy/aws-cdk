import yaml
from aws_cdk import App, Environment
from stacks.data_stack import DataStack

def load_config(env_name: str):
    filename = f"{env_name}_config.yaml"
    with open(filename, "r") as f:
        return yaml.safe_load(f)

app = App()

tenant = app.node.try_get_context("tenant")
env_name = app.node.try_get_context("env")

# Load the config file based on env
config = load_config(env_name)

if tenant not in config:
    raise ValueError(f"Tenant '{tenant}' not found in {env_name}_config.yaml")

tenant_env_config = config[tenant]

# Create only one stack (DataStack) per tenant-env
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
