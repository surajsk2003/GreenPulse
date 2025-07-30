#!/bin/bash

# 🚀 AWS Free Tier Deployment Script for GreenPulse
# Deploys backend to EC2 and frontend to S3 + CloudFront

echo "🌱 GreenPulse AWS Deployment"
echo "============================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install it first:"
    echo "  brew install awscli  # macOS"
    echo "  pip install awscli  # Linux/Windows"
    exit 1
fi

# Check if AWS is configured
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS CLI not configured. Please run:"
    echo "  aws configure"
    exit 1
fi

print_success "AWS CLI configured and ready"

# Variables
REGION="us-east-1"
KEY_NAME="greenpulse-key"
SECURITY_GROUP="greenpulse-sg"
INSTANCE_NAME="greenpulse-backend"
S3_BUCKET="greenpulse-frontend-$(date +%s)"
DB_IDENTIFIER="greenpulse-db"

print_step "Setting up AWS infrastructure..."

# 1. Create Key Pair (if doesn't exist)
print_step "Creating EC2 Key Pair..."
if ! aws ec2 describe-key-pairs --key-names $KEY_NAME --region $REGION &> /dev/null; then
    aws ec2 create-key-pair --key-name $KEY_NAME --region $REGION --query 'KeyMaterial' --output text > ${KEY_NAME}.pem
    chmod 400 ${KEY_NAME}.pem
    print_success "Key pair created: ${KEY_NAME}.pem"
else
    print_warning "Key pair $KEY_NAME already exists"
fi

# 2. Create Security Group
print_step "Creating Security Group..."
if ! aws ec2 describe-security-groups --group-names $SECURITY_GROUP --region $REGION &> /dev/null; then
    SECURITY_GROUP_ID=$(aws ec2 create-security-group \
        --group-name $SECURITY_GROUP \
        --description "GreenPulse Security Group" \
        --region $REGION \
        --query 'GroupId' --output text)
    
    # Allow HTTP (80), HTTPS (443), SSH (22), and FastAPI (8000)
    aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 --region $REGION
    aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $REGION
    aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $REGION
    aws ec2 authorize-security-group-ingress --group-id $SECURITY_GROUP_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $REGION
    
    print_success "Security group created: $SECURITY_GROUP_ID"
else
    SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --group-names $SECURITY_GROUP --region $REGION --query 'SecurityGroups[0].GroupId' --output text)
    print_warning "Security group $SECURITY_GROUP already exists: $SECURITY_GROUP_ID"
fi

# 3. Create RDS PostgreSQL Instance
print_step "Creating RDS PostgreSQL instance..."
if ! aws rds describe-db-instances --db-instance-identifier $DB_IDENTIFIER --region $REGION &> /dev/null; then
    aws rds create-db-instance \
        --db-instance-identifier $DB_IDENTIFIER \
        --db-instance-class db.t3.micro \
        --engine postgres \
        --master-username postgres \
        --master-user-password GreenPulse2024! \
        --allocated-storage 20 \
        --db-name greenpulse \
        --vpc-security-group-ids $SECURITY_GROUP_ID \
        --region $REGION \
        --no-publicly-accessible
    
    print_success "RDS instance creation initiated. This will take 5-10 minutes..."
else
    print_warning "RDS instance $DB_IDENTIFIER already exists"
fi

# 4. Launch EC2 Instance
print_step "Launching EC2 instance..."

# User data script for EC2 instance
USER_DATA=$(cat << 'EOF'
#!/bin/bash
yum update -y
yum install -y python3 python3-pip git nginx

# Install Node.js for any frontend builds if needed
curl -sL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# Clone the repository
cd /home/ec2-user
git clone https://github.com/surajsk2003/GreenPulse.git
cd GreenPulse

# Install Python dependencies
pip3 install -r requirements.txt

# Set up environment variables
cat > .env << ENVEOF
DATABASE_URL=postgresql://postgres:GreenPulse2024!@your-rds-endpoint:5432/greenpulse
SECRET_KEY=aws-production-secret-key-change-me
PROJECT_NAME=GreenPulse
ALLOWED_ORIGINS=https://your-cloudfront-domain.cloudfront.net
ENVEOF

# Start the application
cd /home/ec2-user/GreenPulse
nohup python3 app.py > app.log 2>&1 &

# Set up nginx reverse proxy
cat > /etc/nginx/conf.d/greenpulse.conf << NGINXEOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
NGINXEOF

systemctl start nginx
systemctl enable nginx
EOF
)

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t2.micro \
    --key-name $KEY_NAME \
    --security-groups $SECURITY_GROUP \
    --user-data "$USER_DATA" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --region $REGION \
    --query 'Instances[0].InstanceId' \
    --output text)

print_success "EC2 instance launched: $INSTANCE_ID"

# 5. Create S3 bucket for frontend
print_step "Creating S3 bucket for frontend..."
aws s3 mb s3://$S3_BUCKET --region $REGION

# Configure for static website hosting
aws s3 website s3://$S3_BUCKET --index-document index.html --error-document index.html

# Set bucket policy for public access
BUCKET_POLICY=$(cat << POLICYEOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::$S3_BUCKET/*"
        }
    ]
}
POLICYEOF
)

echo "$BUCKET_POLICY" > bucket-policy.json
aws s3api put-bucket-policy --bucket $S3_BUCKET --policy file://bucket-policy.json
rm bucket-policy.json

print_success "S3 bucket created and configured: $S3_BUCKET"

# 6. Build and upload frontend
print_step "Building and uploading frontend..."
cd frontend/greenpulse-dashboard
npm install
npm run build
aws s3 sync dist/greenpulse-dashboard/ s3://$S3_BUCKET --delete

print_success "Frontend uploaded to S3"

# 7. Create CloudFront distribution
print_step "Creating CloudFront distribution..."
DISTRIBUTION_CONFIG=$(cat << DISTEOF
{
    "CallerReference": "$(date +%s)",
    "Comment": "GreenPulse Frontend Distribution",
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "$S3_BUCKET",
                "DomainName": "$S3_BUCKET.s3-website-$REGION.amazonaws.com",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only"
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "$S3_BUCKET",
        "ViewerProtocolPolicy": "redirect-to-https",
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {
                "Forward": "none"
            }
        }
    },
    "Enabled": true,
    "PriceClass": "PriceClass_100"
}
DISTEOF
)

DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config "$DISTRIBUTION_CONFIG" \
    --query 'Distribution.Id' \
    --output text)

print_success "CloudFront distribution created: $DISTRIBUTION_ID"

# Get instance public IP
print_step "Getting instance details..."
sleep 30  # Wait for instance to start
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

# Get CloudFront domain
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
    --id $DISTRIBUTION_ID \
    --query 'Distribution.DomainName' \
    --output text)

# Get RDS endpoint (may take time to be available)
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_IDENTIFIER \
    --region $REGION \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text 2>/dev/null || echo "RDS still initializing...")

print_success "🎉 Deployment Summary"
echo "=========================="
echo "✅ Backend EC2: http://$PUBLIC_IP:8000"
echo "✅ Frontend S3: http://$S3_BUCKET.s3-website-$REGION.amazonaws.com"
echo "✅ Frontend CloudFront: https://$CLOUDFRONT_DOMAIN"
echo "✅ Database: $RDS_ENDPOINT (when ready)"
echo ""
echo "📋 Next Steps:"
echo "1. Wait 5-10 minutes for RDS to be ready"
echo "2. Update EC2 environment variables with RDS endpoint"
echo "3. Update frontend CORS settings with CloudFront domain"
echo "4. SSH to EC2: ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo ""
echo "🔑 Key Files:"
echo "- EC2 Key: ${KEY_NAME}.pem"
echo "- Instance ID: $INSTANCE_ID"
echo "- Security Group: $SECURITY_GROUP_ID"
echo ""
echo "💰 All resources are using AWS Free Tier!"

# Save deployment info
cat > aws-deployment-info.txt << INFOEOF
GreenPulse AWS Deployment Information
====================================
Deployment Date: $(date)
Region: $REGION

Resources:
- EC2 Instance ID: $INSTANCE_ID
- Public IP: $PUBLIC_IP
- Security Group: $SECURITY_GROUP_ID
- Key Pair: $KEY_NAME
- S3 Bucket: $S3_BUCKET
- CloudFront Distribution: $DISTRIBUTION_ID
- CloudFront Domain: $CLOUDFRONT_DOMAIN
- RDS Instance: $DB_IDENTIFIER
- RDS Endpoint: $RDS_ENDPOINT

URLs:
- Backend API: http://$PUBLIC_IP:8000
- Frontend S3: http://$S3_BUCKET.s3-website-$REGION.amazonaws.com  
- Frontend CDN: https://$CLOUDFRONT_DOMAIN

SSH Access:
ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP

Database Connection:
postgresql://postgres:GreenPulse2024!@$RDS_ENDPOINT:5432/greenpulse
INFOEOF

print_success "Deployment info saved to aws-deployment-info.txt"
echo ""
echo "🚀 Your GreenPulse platform is deploying on AWS Free Tier!"
echo "Check the EC2 instance in about 5 minutes at: http://$PUBLIC_IP:8000"