# AWS
In order to use Clusterous, you must have some basic familiarity with Amazon Web Services (AWS). The AWS website has a [guide for getting](https://aws.amazon.com/what-is-aws/) started with AWS.

You provide your own AWS account, which Clusterous uses to run your cluster. Clusterous does not use any central server, so your AWS account credentials stay on the machine you use; Clusterous only talks to the AWS API,

AWS is a cloud computing platform that offers computing resources that you can pay for by the hour. It consists of a number of different services, but Clusterous primarily uses [EC2](https://aws.amazon.com/ec2/). EC2 (for Elastic Cloud Compute) is a service that allows renting virtual machines, known as "instances", by the hour. A Clusterous cluster consists of a number of EC2 instances.

Clusterous uses the [EBS](https://aws.amazon.com/ebs/) (Elastic Block Store) feature for enabling the shared volume. In addition, Clusterous makes use of [S3](https://aws.amazon.com/s3/)] (for storing Docker images) [VPCs](https://aws.amazon.com/vpc/) (to enable networking).

Amazon maintains a number of physical data centers in that run all the actual hardware that powers all the services. These data centers are grouped by "[regions](https://aws.amazon.com/about-aws/global-infrastructure/)", of which Amazon has a number spread across the world. Clusterous users generally pick a region that is geographically close to them in order to reduce network latency between themselves and the compute cluster.

## Accounts and Billing
To get started with AWS, you first need an account. Depending on how your AWS costs are paid for, you may use an account that you personally create and maintain, or your organisation may provide you with an account.

AWS bills you only for usage: you do not pay an upfront or subscription fee. Instead, you are billed for the hour (or month, depending on the service). Different AWS resources have different prices.

## Resources
In the case of EC2, there are a [number of different instance types](https://aws.amazon.com/ec2/pricing/) on offer, catering to wide range of needs. The instance types range from tiny single core machines to 40-core machines with many gigabytes of memory, all priced according to power. When creating a cluster, you need to choose which types you want your cluster to be made of, depending on the needs of your application and your budget.

## Using AWS with Clusterous
As described in the [Quick Start Guide](02_Quick_start.md), you need to run the Clusterous `setup` command to configure Clusterous to use your AWS account. As a first step, the setup wizard will ask you for your AWS Access Key ID and Secret Access Key, which will be in the form:

    Access Key ID: AKIAIOSFODNN7EXAMPLE
    Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

To obtain such keys, ask your account administrator to create the keys for you. In the case of a self-managed account, you need to create yourself an IAM role (e.g. using the AWS Web Console), an action which will generate the keys for you. You need to ensure that your IAM role has adequate permissions to create EC2 instances, subnets etc; if possible, permit all actions on EC2, S3 and VPC.

In addition, Clusterous requires an EC2 Key Pair, which is a cryptographic key required by Clusterous to establish SSH connections with EC2 instances. The setup wizard will give you the option of creating one, which is useful if you do not already have one. If you are sharing clusters with others on the same account, it is necessary for you and your collaborators to use the same Key Pair.
