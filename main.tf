provider "aws" {
  region = "us-east-1"  
}

# Create an ECS Cluster
resource "aws_ecs_cluster" "games_api_cluster" {
  name = "games-api-cluster"
}

# Security Group for the Load Balancer (allows inbound HTTP/HTTPS traffic)
resource "aws_security_group" "lb_security_group" {
  name        = "lb_security_group"
  description = "Allow inbound HTTP/HTTPS traffic"
  vpc_id      = "vpc-12345678"  # Replace with the correct VPC ID

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

# Security Group for ECS Task (allows traffic only from the load balancer)
resource "aws_security_group" "ecs_security_group" {
  name        = "ecs_security_group"
  description = "Allow traffic from load balancer only"
  vpc_id      = "vpc-12345678"  # Replace with your VPC ID

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

# Create an Application Load Balancer
resource "aws_lb" "games_api_lb" {
  name               = "games-api-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb_security_group.id]
  subnets            = ["subnet-12345678", "subnet-87654321"]  # Replace with your subnet IDs
}

# Target Group for the Load Balancer
resource "aws_lb_target_group" "games_api_target_group" {
  name        = "games-api-target-group"
  port        = 6000
  protocol    = "HTTP"
  vpc_id      = "vpc-12345678"  # Replace with your VPC ID
  target_type = "ip"
}

# Listener for the Load Balancer (HTTP on port 80)
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
      image     = "ajiayidebug/gamesapi:latest"  # DockerHub image
      portMappings = [
        {
          containerPort = 6000
          hostPort      = 6000
        }
      ]
    }
  ])
}

# ECS Service to Run the Task
resource "aws_ecs_service" "games_api_service" {
  name            = "games-api-service"
  cluster         = aws_ecs_cluster.games_api_cluster.id
  task_definition = aws_ecs_task_definition.games_api_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = ["subnet-12345678", "subnet-87654321"]  # Replace with your subnet IDs
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