from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_ecr_assets as ecr_assets,
)
from aws_cdk.aws_apprunner_alpha import Service, Source, ImageConfiguration
from constructs import Construct

class AppRunnerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # App Runner用のIAMロールを作成
        instance_role = iam.Role(
            self, "AppRunnerInstanceRole",
            assumed_by=iam.ServicePrincipal("tasks.apprunner.amazonaws.com")
        )

        # ECRにプッシュするDockerイメージをビルド
        docker_image = ecr_assets.DockerImageAsset(
            self, "FortuneImage",
            directory="../",  # プロジェクトのルートディレクトリ
            file="Dockerfile",  # 使用するDockerfile
            exclude=["cdk.out", "node_modules", ".git"]  # 除外するディレクトリ
        )

        # イメージの設定（ポート、起動コマンドなど）
        image_config = ImageConfiguration(
            port=8000,
            start_command="python -m uvicorn app.src.main:app --host 0.0.0.0 --port 8000"
        )

        # App Runner Service
        service = Service(
            self, "FortuneService",
            source=Source.from_asset(
                asset=docker_image,
                image_configuration=image_config
            ),
            instance_role=instance_role,
        )
