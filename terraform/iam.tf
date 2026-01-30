# ECSタスク実行ロールの作成
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "exchange-rate-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

# 管理ポリシー（AmazonECSTaskExecutionRolePolicy）のアタッチ
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# S3へのアクセス権限を定義
resource "aws_iam_policy" "s3_access" {
  name        = "exchange-rate-s3-access"
  description = "Allow ECS task to access S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:s3:::takaken94-exchange-rate-fetcher",
          "arn:aws:s3:::takaken94-exchange-rate-fetcher/*"
        ]
      }
    ]
  })
}

# --- ECSタスクロール (アプリがAWSサービスを操作するためのロール) ---
resource "aws_iam_role" "ecs_task_role" {
  name = "exchange-rate-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

# ロールにポリシーをアタッチ
resource "aws_iam_role_policy_attachment" "s3_access_attach" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.s3_access.arn
}