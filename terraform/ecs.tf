resource "aws_ecs_cluster" "main" {
  name = "exchange-rate-cluster"
}

resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/exchange-rate-viewer"
  retention_in_days = 7 # ログの保持期間
}

resource "aws_ecs_task_definition" "main" {
  family                   = "exchange-rate-task"
  cpu                      = "256"
  memory                   = "512"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  # タスク実行ロール
  execution_role_arn = aws_iam_role.ecs_task_execution_role.arn
  # タスクロール
  task_role_arn = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "exchange-rate-container"
      image     = "369073369620.dkr.ecr.ap-northeast-1.amazonaws.com/exchange-rate-viewer:prod" # ECR リポジトリ URI
      essential = true

      # 環境変数を定義
      environment = [
        { name = "S3_BUCKET_NAME", value = "takaken94-exchange-rate-fetcher" },
        { name = "S3_PREFIX", value = "rates-data" }
      ],
      # ポート設定
      portMappings = [
        {
          containerPort = 8000 # コンテナのポート
          hostPort      = 8000
        }
      ],
      # ログ設定
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = "ap-northeast-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "main" {
  name            = "exchange-rate-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_1a.id, aws_subnet.public_1c.id]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true # Public Subnetで動かす場合は true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main.arn
    container_name   = "exchange-rate-container"
    container_port   = 8000
  }
}