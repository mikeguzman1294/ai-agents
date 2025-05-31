/* 
This file is used to configure the backend for Terraform state management.
Need to manually create a backend bucket folder before first IaC deployment, path should be as follows:
gs://<bucket_name>/terraform/<application_name>/<base|application>

Backend Block Official Terraform Documentation:
https://developer.hashicorp.com/terraform//language/backend
*/

terraform {
    backend "gcs" {
    /*
    Empty arguments are menat to be provided automatically by an automation script running Terraform.
    When some or all of the arguments are omitted, we call this a "partial configuration".
    Please refer to https://developer.hashicorp.com/terraform//language/backend#partial-configuration
    */
        bucket  = ""
        prefix  = "terraform/ai-agents/base"
  }
}