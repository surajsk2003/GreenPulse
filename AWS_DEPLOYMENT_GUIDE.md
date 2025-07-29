# 🚀 AWS Free Tier Deployment Guide for GreenPulse

## 📋 Prerequisites

- AWS Account with Free Tier access
- AWS CLI installed and configured
- Node.js and Angular CLI
- Python 3.11+

## 🏗️ Architecture Overview

**Free Tier Services Used:**
- **Backend**: AWS Elastic Beanstalk (t2.micro)
- **Database**: RDS PostgreSQL (db.t3.micro, 20GB)
- **Frontend**: S3 + CloudFront
- **Total Monthly Cost**: $0 (within free tier limits)

## 🎯 Step-by-Step Deployment

### **1. Setup AWS CLI**

```bash
# Install AWS CLI (if not already installed)
brew install awscli  # macOS
# or
pip install awscli

# Configure AWS credentials
aws configure
# Enter your AWS Access Key ID, Secret, Region (us-east-1), and output format (json)
```

### **2. Create RDS PostgreSQL Database**

```bash
# Create RDS subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name greenpulse-subnet-group \
    --db-subnet-group-description "GreenPulse RDS subnet group" \
    --subnet-ids subnet-xxxxxx subnet-yyyyyy  # Replace with your VPC subnet IDs

# Create RDS PostgreSQL instance (Free Tier)
aws rds create-db-instance \
    --db-instance-identifier greenpulse-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 13.13 \
    --master-username postgres \
    --master-user-password YourSecurePassword123! \
    --allocated-storage 20 \
    --db-name greenpulse \
    --vpc-security-group-ids sg-xxxxxxxx \
    --db-subnet-group-name greenpulse-subnet-group \
    --backup-retention-period 7 \
    --storage-encrypted \
    --publicly-accessible
```

**Wait 10-15 minutes for RDS instance to be available**

### **3. Deploy Backend to Elastic Beanstalk**

```bash
# Install EB CLI
pip install awsebcli

# Initialize Elastic Beanstalk application
cd /path/to/GreenPulse
eb init greenpulse-backend --platform python-3.11 --region us-east-1

# Create environment (Free Tier t2.micro)
eb create greenpulse-env \
    --instance-type t2.micro \
    --platform-version "3.4.24" \
    --single-instance

# Set environment variables
eb setenv \
    DATABASE_URL="postgresql://postgres:YourSecurePassword123!@your-rds-endpoint.amazonaws.com:5432/greenpulse" \
    PROJECT_NAME="GreenPulse" \
    SECRET_KEY="your-production-secret-key"

# Deploy the application
eb deploy
```

### **4. Setup Database Tables**

```bash
# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier greenpulse-db \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

# Update and run database setup
export RDS_ENDPOINT=$RDS_ENDPOINT
export RDS_USERNAME=postgres
export RDS_PASSWORD=YourSecurePassword123!
export RDS_DATABASE=greenpulse

python aws_db_setup.py
```

### **5. Deploy Frontend to S3 + CloudFront**

```bash
# Make deployment script executable
chmod +x aws-frontend-deploy.sh

# Update backend URL in the script first:
# Edit aws-frontend-deploy.sh and replace 'your-eb-app.region.elasticbeanstalk.com' 
# with your actual Elastic Beanstalk URL

# Run frontend deployment
./aws-frontend-deploy.sh
```

### **6. Configure Security Groups**

```bash
# Allow inbound traffic to RDS from Elastic Beanstalk
# Get EB security group ID
EB_SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=awseb-*" \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

# Allow EB to access RDS
aws ec2 authorize-security-group-ingress \
    --group-id your-rds-security-group-id \
    --protocol tcp \
    --port 5432 \
    --source-group $EB_SG_ID
```

## 🧪 Testing Deployment

### **Backend Testing**
```bash
# Get EB URL
EB_URL=$(eb status | grep "CNAME" | awk '{print $2}')

# Test endpoints
curl https://$EB_URL/health
curl https://$EB_URL/api/buildings
curl https://$EB_URL/
```

### **Frontend Testing**
```bash
# Get CloudFront URL from aws-deployment-info.txt
CLOUDFRONT_URL=$(grep "CloudFront URL" aws-deployment-info.txt | cut -d' ' -f3)

# Open in browser (after 15-20 minutes for CloudFront deployment)
open $CLOUDFRONT_URL
```

## 💰 Free Tier Limits

**Monthly Limits (Stay within these):**
- **EC2**: 750 hours of t2.micro instances
- **RDS**: 750 hours of db.t3.micro + 20GB storage
- **S3**: 5GB storage + 20,000 GET requests
- **CloudFront**: 50GB data transfer out
- **Data Transfer**: 15GB total

## 🔧 Environment Variables Summary

**Elastic Beanstalk Environment Variables:**
```
DATABASE_URL=postgresql://postgres:password@rds-endpoint:5432/greenpulse
PROJECT_NAME=GreenPulse
SECRET_KEY=your-production-secret-key
ALLOWED_ORIGINS=https://your-cloudfront-domain.cloudfront.net
```

## 🔒 Security Checklist

- [ ] RDS instance in private subnet
- [ ] Security groups properly configured
- [ ] Strong database password
- [ ] HTTPS enforced on CloudFront
- [ ] CORS properly configured
- [ ] Environment variables set securely

## 🚨 Troubleshooting

### **Common Issues:**

1. **EB Deployment Fails**
   ```bash
   eb logs
   # Check logs for Python import errors or missing dependencies
   ```

2. **Database Connection Issues**
   ```bash
   # Verify RDS endpoint and security groups
   aws rds describe-db-instances --db-instance-identifier greenpulse-db
   ```

3. **Frontend Not Loading**
   ```bash
   # Check CloudFront distribution status
   aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID
   ```

## 🎉 Final URLs

After successful deployment:
- **Backend API**: `https://greenpulse-env.region.elasticbeanstalk.com`
- **Frontend**: `https://your-distribution.cloudfront.net`
- **Database**: RDS PostgreSQL in private subnet

## 📱 Demo Ready!

Your GreenPulse platform is now running on AWS Free Tier with:
- ✅ Scalable backend with database
- ✅ Global CDN for fast frontend delivery
- ✅ Real-time WebSocket support
- ✅ ML analytics and insights
- ✅ Professional glassmorphism UI
- ✅ $0 monthly cost (within free tier)