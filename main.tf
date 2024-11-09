provider "aws" {
  region = "ap-southeast-1"  
}

variable "vpc_id" {}
variable "subnet_ids" {
  type = list(string)
}

# Create an ECS Cluster
resource "aws_ecs_cluster" "games_api_cluster" {
  name = "games-api-cluster"
}

# Security Group for the Load Balancer
resource "aws_security_group" "lb_security_group" {
  name        = "lb_security_group"
  description = "Allow inbound HTTP/HTTPS traffic"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
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

# Security Group for ECS Task
resource "aws_security_group" "ecs_security_group" {
  name        = "ecs_security_group"
  description = "Allow traffic from load balancer only"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 6000
    to_port         = 6000
    protocol        = "tcp"
    security_groups = [aws_security_group.lb_security_group.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Application Load Balancer
resource "aws_lb" "games_api_lb" {
  name               = "games-api-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb_security_group.id]
  subnets            = var.subnet_ids
}

# Target Group
resource "aws_lb_target_group" "games_api_target_group" {
  name        = "games-api-target-group"
  port        = 6000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
}

# Listener for Load Balancer
resource "aws_lb_listener" "games_api_listener" {
  load_balancer_arn = aws_lb.games_api_lb.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.games_api_target_group.arn
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "games_api_task" {
  family                   = "games-api-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "games-api-container"
      image     = "ajiayidebug/gamesapi:latest"
      portMappings = [
        {
          containerPort = 6000
          hostPort      = 6000
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/games-api"
          "awslogs-region"        = "ap-southeast-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# ECS Service
resource "aws_ecs_service" "games_api_service" {
  name            = "games-api-service"
  cluster         = aws_ecs_cluster.games_api_cluster.id
  task_definition = aws_ecs_task_definition.games_api_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = [aws_security_group.ecs_security_group.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.games_api_target_group.arn
    container_name   = "games-api-container"
    container_port   = 6000
  }

  depends_on = [aws_lb_listener.games_api_listener]
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecs_task_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
  ]
}

# EventBridge Rule for Scheduled Trigger
resource "aws_cloudwatch_event_rule" "games_api_schedule_rule" {
  name                = "games-api-schedule-rule"
  description         = "Triggers ECS task based on schedule"
  schedule_expression = "rate(1 hour)"  # Adjust this schedule as needed
}

# IAM Policy for EventBridge to start ECS tasks
resource "aws_iam_role_policy" "eventbridge_ecs_task_policy" {
  name = "eventbridge-ecs-task-policy"
  role = aws_iam_role.ecs_task_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ecs:RunTask",
          "ecs:StartTask"
        ]
        Effect   = "Allow"
        Resource = aws_ecs_task_definition.games_api_task.arn
      },
      {
        Action = "iam:PassRole"
        Effect = "Allow"
        Resource = aws_iam_role.ecs_task_execution_role.arn
      }
    ]
  })
}

# EventBridge Target to Run the ECS Task
resource "aws_cloudwatch_event_target" "games_api_event_target" {
  rule       = aws_cloudwatch_event_rule.games_api_schedule_rule.name
  arn        = aws_ecs_cluster.games_api_cluster.arn
  target_id  = "gamesApiTarget"

  ecs_target {
    task_definition_arn = aws_ecs_task_definition.games_api_task.arn
    task_count          = 1
    launch_type         = "FARGATE"

    network_configuration {
      subnets         = var.subnet_ids
      security_groups = [aws_security_group.ecs_security_group.id]
      assign_public_ip = true
    }
  }
}

# Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs_log_group" {
  name              = "/ecs/games-api"
  retention_in_days = 7
}