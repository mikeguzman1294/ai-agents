PHONY: all test clean

#############################################################################
############################# VARIABLES SECTION #############################
#############################################################################

# Makefile Variable Assignment Precedence Quick Reference:
#
# | Variable Definition in Makefile | 'make' command           | Environment Variable ('export VAR=...') | Resulting 'VAR' value |
# | :------------------------------ | :----------------------- | :-------------------------------------- | :-------------------- |
# | VAR = default                   | make target              | (unset)                                 | default               |
# | VAR = default                   | make target VAR=prod     | (unset)                                 | prod                  |
# | VAR = default                   | make target              | export VAR=staging                      | default               |
# |                                 |                          |                                         |                       |
# | VAR := default                  | make target              | (unset)                                 | default               |
# | VAR := default                  | make target VAR=prod     | (unset)                                 | prod                  |
# | VAR := default                  | make target              | export VAR=staging                      | default               |
# |                                 |                          |                                         |                       |
# | VAR ?= default                  | make target              | (unset)                                 | default               |
# | VAR ?= default                  | make target VAR=prod     | (unset)                                 | prod                  |
# | VAR ?= default                  | make target              | export VAR=staging                      | staging               |
#
# Key Takeaways:
# 1.  Command-line arguments (e.g., 'make VAR=value') always win, overriding any Makefile definition.
# 2.  '=' (recursive) and ':=' (simply expanded) both override environment variables.
#     	-	':=' evaluates its value immediately (once).
#     	-	'=' evaluates its value each time it's used (lazy).
# 3.  '?=' (conditional) sets a default only if the variable is unset, allowing environment variables to take precedence.

# GCP
PROJECT_ID:=mguzmans-dev
SA_DEVELOPER:=sa-developer@${PROJECT_ID}.iam.gserviceaccount.com

# Terraform
TERRAFORM_BACKEND_BUCKET=bkt-tfstate-mguzmans-d
TERRAFORM_ENVIRONMENT=preprod

############################################################################
############################# COMMANDS SECTION #############################
############################################################################

############################# GCP Authentication #############################

# Developer Service Account Impersonation
gcloud-auth:
	gcloud auth application-default login --impersonate-service-account=${SA_DEVELOPER}
	gcloud auth login
	gcloud config set project ${PROJECT_ID}
	gcloud config set auth/impersonate_service_account ${SA_DEVELOPER}

############################# GCP Authentication #############################

# Terraform Base Setup
terraform-base-setup:
	@echo "Running Terraform command locally to setup base infrastructure"
	@cd terraform/base && \
	terraform init -backend-config="bucket=${TERRAFORM_BACKEND_BUCKET}" && \
	terraform plan -var-file=${TERRAFORM_ENVIRONMENT}.tfvars && \
	terraform apply -var-file=${TERRAFORM_ENVIRONMENT}.tfvars
	@echo "Success!!!"

# Terraform Base Destroy
terraform-base-destroy:
	@echo "Running Terraform command locally to destroy base infrastructure"
	@cd terraform/base && \
	terraform init -backend-config="bucket=${TERRAFORM_BACKEND_BUCKET}" && \
	terraform plan -destroy -var-file=${TERRAFORM_ENVIRONMENT}.tfvars && \
	terraform destroy -var-file=${TERRAFORM_ENVIRONMENT}.tfvars
	@echo "Success!!!"

############################# FastAPI Application #############################

run-api:
	@echo "\n**********Starting app locally**********"
	export BASE_URL=http://localhost:8000/ && \
	uvicorn app.main:app --reload
	@echo "*******************\n"
