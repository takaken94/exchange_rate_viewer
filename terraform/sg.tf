# ALB用のセキュリティグループ
resource "aws_security_group" "alb_sg" {
  name   = "exchange-rate-alb-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ECSタスク用のセキュリティグループ
resource "aws_security_group" "ecs_sg" {
  name   = "exchange-rate-ecs-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 8000 # アプリがリッスンしているポートに合わせて変更してください
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id] # ALBからのみ許可
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}