module "artifact_registry" {
/*
This module is taken from the official Google Cloud Platform reusable modules for Artifact Registry:
https://github.com/GoogleCloudPlatform/terraform-google-artifact-registry
*/
  source  = "GoogleCloudPlatform/artifact-registry/google"
  version = "~> 0.3"

  project_id    = var.project_id
  location      = var.location
  repository_id = var.repository_id
  format        = "DOCKER"
}


module "cloud_storage_bucket" {
/*
This module is taken from the official Google Cloud Platform reusable modules for Artifact Registry:
https://github.com/terraform-google-modules/terraform-google-cloud-storage/tree/main/modules/simple_bucket
*/
  source  = "terraform-google-modules/cloud-storage/google//modules/simple_bucket"
  version = "~> 10.0"

  name        = var.bucket_name
  project_id  = var.project_id
  location    = var.location
  force_destroy = var.namespace_prefix == "prod" ? false : true // only for preprod environment
  iam_members = [{
    role   = "roles/storage.admin"
    member = "serviceAccount:sa-developer@${var.project_id}.iam.gserviceaccount.com"
  }]
}