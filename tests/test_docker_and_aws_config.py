"""Tests for Docker packaging and AWS deployment configurations."""

import json
from pathlib import Path
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_dockerfile_structure() -> None:
    dockerfile_path = REPO_ROOT / "Dockerfile"
    assert dockerfile_path.exists(), "Dockerfile must exist at repository root"

    content = dockerfile_path.read_text(encoding="utf-8")
    assert "FROM python:3.12" in content, "Dockerfile should use Python 3.12 base image"
    assert "ffmpeg" in content, "Dockerfile must install ffmpeg for in-memory audio decoding"
    assert "libsndfile1" in content, "Dockerfile must install libsndfile1 for soundfile"
    assert "EXPOSE 8000" in content, "Dockerfile must expose port 8000"
    assert "appuser" in content, "Dockerfile must configure non-root user for security"
    assert "HEALTHCHECK" in content, "Dockerfile must define HEALTHCHECK endpoint"
    assert "uvicorn" in content, "Dockerfile default command must run uvicorn server"


def test_dockerignore_rules() -> None:
    dockerignore_path = REPO_ROOT / ".dockerignore"
    assert dockerignore_path.exists(), ".dockerignore must exist at repository root"

    content = dockerignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]

    expected_rules = [".git", "__pycache__", ".env", "data/", "scratch/"]
    for rule in expected_rules:
        assert any(rule in line for line in lines), f".dockerignore should exclude '{rule}'"


def test_docker_compose_structure() -> None:
    compose_path = REPO_ROOT / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist at repository root"

    with open(compose_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "services" in config, "docker-compose.yml must define services"
    services = config["services"]

    assert "api" in services, "Must define 'api' service for FastAPI server"
    api_svc = services["api"]
    assert "8000:8000" in [str(p) for p in api_svc.get("ports", [])] or any("8000" in str(p) for p in api_svc.get("ports", []))
    assert "healthcheck" in api_svc, "'api' service must have a healthcheck"

    assert "bot" in services, "Must define 'bot' service for Telegram bot daemon"
    bot_svc = services["bot"]
    assert "scripts/run_bot.py" in str(bot_svc.get("command", "")), "'bot' service must invoke scripts/run_bot.py"


def test_aws_s3_lifecycle_policy() -> None:
    policy_path = REPO_ROOT / "deploy" / "aws" / "s3_lifecycle_policy.json"
    assert policy_path.exists(), "S3 lifecycle policy file must exist at deploy/aws/s3_lifecycle_policy.json"

    with open(policy_path, "r", encoding="utf-8") as f:
        policy = json.load(f)

    assert "Rules" in policy, "Policy must define 'Rules'"
    rules = policy["Rules"]
    assert len(rules) >= 1, "Must have at least one lifecycle rule"

    rule = rules[0]
    assert rule.get("Status") == "Enabled", "Lifecycle rule must be Enabled"
    assert "Expiration" in rule, "Rule must configure Expiration"
    assert rule["Expiration"].get("Days", 0) <= 1, "Expiration must be <= 1 day to prevent biometric data retention"


def test_aws_iam_policy() -> None:
    iam_path = REPO_ROOT / "deploy" / "aws" / "iam_policy.json"
    assert iam_path.exists(), "IAM policy file must exist at deploy/aws/iam_policy.json"

    with open(iam_path, "r", encoding="utf-8") as f:
        policy = json.load(f)

    assert policy.get("Version") == "2012-10-17", "IAM policy Version must be 2012-10-17"
    assert "Statement" in policy, "IAM policy must have Statements"
    statements = policy["Statement"]
    assert len(statements) >= 1, "Must have at least one Statement"

    # Verify least privilege: no wildcard '*' action
    for stmt in statements:
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        assert "*" not in actions, "IAM policy must not use blanket '*' action (Least Privilege)"


def test_aws_pricing_calculator() -> None:
    calc_path = REPO_ROOT / "deploy" / "aws" / "pricing_calculator_w08.md"
    assert calc_path.exists(), "Pricing calculator document must exist at deploy/aws/pricing_calculator_w08.md"

    content = calc_path.read_text(encoding="utf-8")
    assert "100" in content, "Must estimate cost for 100 users"
    assert any(k in content for k in ["1,000", "1.000", "1000"]), "Must estimate cost for 1,000 users"
    assert any(k in content for k in ["10,000", "10.000", "10000"]), "Must estimate cost for 10,000 users"
    assert "EC2" in content, "Must include EC2 compute cost"
    assert "S3" in content, "Must include S3 storage cost"


def test_aws_deploy_ec2_script() -> None:
    deploy_script = REPO_ROOT / "scripts" / "aws_deploy_ec2.sh"
    assert deploy_script.exists(), "EC2 deploy script must exist at scripts/aws_deploy_ec2.sh"

    content = deploy_script.read_text(encoding="utf-8")
    assert content.startswith("#!/"), "Script must start with shebang"
    assert "set -e" in content or "set -euo pipefail" in content, "Script must have strict error handling"
    assert "docker" in content, "Script must invoke Docker"
