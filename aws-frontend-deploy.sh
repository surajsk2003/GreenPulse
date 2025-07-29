#!/bin/bash

# AWS S3 + CloudFront Frontend Deployment Script for GreenPulse
# This script deploys the Angular frontend to AWS S3 with CloudFront CDN

echo "🚀 AWS Frontend Deployment for GreenPulse"
echo "========================================"

# Configuration
BUCKET_NAME="greenpulse-frontend-$(date +%s)"  # Unique bucket name
REGION="us-east-1"  # Use us-east-1 for CloudFront compatibility
CLOUDFRONT_COMMENT="GreenPulse Frontend Distribution"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    echo "   brew install awscli"
    exit 1
fi

# Check if Angular CLI is installed
if ! command -v ng &> /dev/null; then
    echo "❌ Angular CLI not found. Installing..."
    npm install -g @angular/cli
fi

echo "📦 Building Angular application for production..."
cd frontend/greenpulse-dashboard

# Update environment with AWS backend URL
echo "🔧 Updating production environment..."
cat > src/environments/environment.prod.ts << EOF
export const environment = {
  production: true,
  apiUrl: 'https://your-eb-app.region.elasticbeanstalk.com/api'
};
EOF

# Build the application
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Angular build failed"
    exit 1
fi

echo "✅ Angular build completed"

# Create S3 bucket
echo "🪣 Creating S3 bucket: $BUCKET_NAME"
aws s3api create-bucket \
    --bucket $BUCKET_NAME \
    --region $REGION

# Configure bucket for static website hosting
aws s3api put-bucket-website \
    --bucket $BUCKET_NAME \
    --website-configuration '{
        "IndexDocument": {"Suffix": "index.html"},
        "ErrorDocument": {"Key": "index.html"}
    }'

# Set bucket policy for public read access
aws s3api put-bucket-policy \
    --bucket $BUCKET_NAME \
    --policy '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::'$BUCKET_NAME'/*"
            }
        ]
    }'

# Upload built files to S3
echo "📤 Uploading files to S3..."
aws s3 sync dist/greenpulse-dashboard/ s3://$BUCKET_NAME \
    --delete \
    --cache-control "max-age=86400" \
    --metadata-directive REPLACE

# Set cache control for index.html (no caching)
aws s3 cp s3://$BUCKET_NAME/index.html s3://$BUCKET_NAME/index.html \
    --cache-control "no-cache, no-store, must-revalidate" \
    --metadata-directive REPLACE

echo "✅ Files uploaded to S3"

# Create CloudFront distribution
echo "🌐 Creating CloudFront distribution..."
DISTRIBUTION_CONFIG='{
    "CallerReference": "'$(date +%s)'",
    "Comment": "'$CLOUDFRONT_COMMENT'",
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "'$BUCKET_NAME'",
                "DomainName": "'$BUCKET_NAME'.s3-website-'$REGION'.amazonaws.com",
                "CustomOriginConfig": {
                    "HTTPPort": 80,
                    "HTTPSPort": 443,
                    "OriginProtocolPolicy": "http-only"
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "'$BUCKET_NAME'",
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
        },
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000
    },
    "CustomErrorResponses": {
        "Quantity": 1,
        "Items": [
            {
                "ErrorCode": 404,
                "ResponsePagePath": "/index.html",
                "ResponseCode": "200",
                "ErrorCachingMinTTL": 300
            }
        ]
    },
    "Enabled": true,
    "PriceClass": "PriceClass_100"
}'

# Create distribution
DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config "$DISTRIBUTION_CONFIG" \
    --query 'Distribution.Id' \
    --output text)

if [ $? -eq 0 ]; then
    echo "✅ CloudFront distribution created: $DISTRIBUTION_ID"
    
    # Get CloudFront domain name
    CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
        --id $DISTRIBUTION_ID \
        --query 'Distribution.DomainName' \
        --output text)
    
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📋 Deployment Details:"
    echo "   S3 Bucket: $BUCKET_NAME"
    echo "   CloudFront ID: $DISTRIBUTION_ID"
    echo "   CloudFront URL: https://$CLOUDFRONT_DOMAIN"
    echo ""
    echo "⏳ Note: CloudFront distribution deployment may take 15-20 minutes"
    echo "🔗 Your frontend will be available at: https://$CLOUDFRONT_DOMAIN"
    
    # Save deployment info
    cat > ../../aws-deployment-info.txt << EOF
AWS GreenPulse Deployment Information
====================================
Frontend S3 Bucket: $BUCKET_NAME
CloudFront Distribution ID: $DISTRIBUTION_ID
CloudFront URL: https://$CLOUDFRONT_DOMAIN
Region: $REGION
Deployment Date: $(date)

Next Steps:
1. Update backend CORS settings to include: https://$CLOUDFRONT_DOMAIN
2. Update frontend environment.prod.ts with actual backend URL
3. Wait for CloudFront deployment to complete (~15-20 minutes)
EOF
    
else
    echo "❌ Failed to create CloudFront distribution"
    exit 1
fi