---
trigger: model_decision
description: Outlines architectural principles for the MSS platform, covering IaC, AWS structure, networking, security, and more, based on documented ADRs
---

# MSS Architecture Guidelines

This document outlines the high-level architecture principles and decisions for the Managed Security Services (MSS) platform. All engineering efforts must adhere to these guidelines to ensure consistency, security, and operational excellence. Each rule is informed by one or more Architecture Decision Records (ADRs), which provide detailed context and rationale.

## 1. Infrastructure as Code (IaC)

### Rule 1.1: OpenTofu for IaC
All infrastructure will be defined and managed using OpenTofu. Direct modifications to the infrastructure via the AWS Console are strictly prohibited unless for emergency break-glass scenarios. **Note:** The migration to OpenTofu is currently in a "Proposed" state.

- **Rationale:** Ensures infrastructure is version-controlled, repeatable, and documented.
- **Reference:** [`ADR-0064-opentofu-migration`](../../docs/adr/0064-opentofu-migration.md)

### Rule 1.2: Monorepo for Infrastructure
All infrastructure code is managed in a single monorepo named [infra](https://github.com/1898andCo/infra).

- **Reference:** [`ADR-0018-infrastructure-repository-strategy`](../../docs/adr/0018-infrastructure-repository-strategy.md)

### Rule 1.3: Terraform State Backend
A single S3 bucket per AWS Organization must be used for the Terraform state backend.

- **Reference:** [`ADR-0031-terraform-state-backend-architecture`](../../docs/adr/0031-terraform-state-backend-architecture.md)

## 2. AWS Organization and Account Structure

### Rule 2.1: Independent Organizational Units
The platform operates across multiple, independent AWS Organizations for `dev`, `stage`, and `prod` environments to ensure strict isolation and independent lifecycle management.

- **Reference:** [`ADR-0029-aws-organization-strategy`](../../docs/adr/0029-aws-organization-strategy.md)

### Rule 2.2: Standardized OU and Account Flavors
A standardized set of Organizational Units (OUs) and account "flavors" must be used to enforce separation of duties and isolate workloads. Key OUs include **gov** (for governance and management services) and **soc** (for security operations). Accounts such as **dss** (shared services) and **net** (networking) are located within the **gov** OU.

- **Reference:** [`ADR-0020-aws-accounts-flavors-and-organizational-units`](../../docs/adr/0020-aws-accounts-flavors-and-organizational-units.md)

## 3. Networking

### Rule 3.1: Organization Supernet
All VPCs must use CIDR blocks allocated from the organization's `10.0.0.0/8` supernet.

- **Reference:** [`ADR-0027-organization-supernet-cidr-ranges`](../../docs/adr/0027-organization-supernet-cidr-ranges.md)

### Rule 3.2: VPC and Subnet CIDR Strategy
VPC CIDR blocks must be manually allocated according to the strategy defined in the reference ADR to prevent overlaps and ensure long-term scalability.

- **Reference:** [`ADR-0004-aws-account-vpc-subnet-cidr-strategy`](../../docs/adr/0004-aws-account-vpc-subnet-cidr-strategy.md)

### Rule 3.3: VPC Traffic Isolation
Network traffic isolation must be enforced using distinct subnet strategies. `gov` and `dss` accounts will use a public/private subnet model, while `soc` accounts will use custom strategies with only private subnets to enhance security.

- **Reference:** [`ADR-0007-vpc-network-traffic-isolation-policy`](../../docs/adr/0007-vpc-network-traffic-isolation-policy.md)

### Rule 3.4: Security Groups for Service Isolation
Security Groups are the primary mechanism for enforcing network access controls. Each service or application tier must have its own dedicated security group with rules that restrict traffic to only what is explicitly required.

- **Reference:** [`ADR-0033-security-group-strategy`](../../docs/adr/0033-security-group-strategy.md)

### Rule 3.5: Network ACLs (NACLs)
Network ACLs are currently deprecated and not deployed. However, a future rollout is planned and they may be reconsidered for stateless, broad-level network filtering at the subnet boundary.

- **Reference:** [`ADR-0034-nacl-strategy`](../../docs/adr/0034-nacl-strategy.md)

## 4. AWS Regions

### Rule 4.1: Primary AWS Region
The primary operational region for all AWS deployments is `us-east-1`.

- **Reference:** [`ADR-0058-primary-aws-region`](../../docs/adr/0058-primary-aws-region.md)

### Rule 4.2: Approved Operational Regions
Operations are restricted to the following AWS regions: `us-east-1`, `us-west-2`, `eu-west-1`, and `ap-southeast-1`. **Note:** This selection is currently in a "Proposed" state.

- **Reference:** [`ADR-0057-operational-aws-regions`](../../docs/adr/0057-operational-aws-regions.md)

## 5. Containerization

### Rule 5.1: EKS for Container Orchestration
Amazon EKS is the standard for all containerized workloads.

- **Reference:** [`ADR-0025-eks-or-ecs`](../../docs/adr/0025-eks-or-ecs.md)

## 6. Naming Conventions

### Rule 6.1: Hostname and Naming Scheme
All resources must follow a consistent naming convention. Hostnames for service discovery must use the format: `host.<region-abbr>.<account>.<ou>.<stage-service-domain>`. Regional naming must use the four-character abbreviation (e.g., `use1` for `us-east-1`).

- **Reference:** [`ADR-0012-hostname-scheme-for-service-discovery`](../../docs/adr/0012-hostname-scheme-for-service-discovery.md), [`ADR-0024-regional-naming-scheme`](../../docs/adr/0024-regional-naming-scheme.md)

## 7. Security and Compliance

### Rule 7.1: Root Account MFA
AWS root accounts must be secured using Hardware MFA Security Keys (U2F/FIDO2).

- **Reference:** [`ADR-0013-mfa-solution-for-aws-root-accounts`](../../docs/adr/0013-mfa-solution-for-aws-root-accounts.md)
