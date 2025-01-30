#!/usr/bin/env python3
import os
from aws_cdk import App, Environment
from app_runner_stack import AppRunnerStack
from codepipeline_stack import CodePipelineStack

app = App()

env = Environment(
    account=os.environ.get('CDK_DEFAULT_ACCOUNT'),
    region=os.environ.get('CDK_DEFAULT_REGION', 'ap-northeast-1')
)

AppRunnerStack(app, "FortuneAppRunnerStack", env=env)
CodePipelineStack(app, "FortuneCodePipelineStack", env=env)

app.synth()
