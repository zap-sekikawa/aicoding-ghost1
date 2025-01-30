from aws_cdk import (
    Stack,
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_iam as iam,
)
from constructs import Construct

class CodePipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # CodeCommitリポジトリ
        repository = codecommit.Repository(
            self, "FortuneRepository",
            repository_name="fortune-repository",
            description="Fortune API repository"
        )

        # パイプライン作成
        pipeline = codepipeline.Pipeline(
            self, "FortunePipeline",
            pipeline_name="fortune-pipeline"
        )

        # ソースステージ
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.CodeCommitSourceAction(
            action_name="CodeCommit_Source",
            repository=repository,
            branch="main",
            output=source_output,
        )
        pipeline.add_stage(
            stage_name="Source",
            actions=[source_action]
        )

        # ビルドステージ
        build_project = codebuild.PipelineProject(
            self, "FortuneBuild",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.11"
                        },
                        "commands": [
                            "pip install -r requirements.txt"
                        ]
                    },
                    "build": {
                        "commands": [
                            "pytest"
                        ]
                    }
                }
            })
        )

        build_output = codepipeline.Artifact()
        build_action = codepipeline_actions.CodeBuildAction(
            action_name="Build",
            project=build_project,
            input=source_output,
            outputs=[build_output],
        )

        pipeline.add_stage(
            stage_name="Build",
            actions=[build_action]
        )
