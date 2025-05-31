/* General Resource Variables */

variable "project_id" {
    type = string
    description = "The ID of the project that owns the resources. Defaults to preprod project"
    default = "mguzmans-dev"
}

variable "location" {
    type = string
    description = "The default region to manage the resources inm ie 'us-central1'."
    default = "us-central1"
}

variable "namespace_prefix" {
    type = string
    description = "Namespace prefix for the resources."
    default = "preprod"
}

/* Artifact Registry Variables */

variable "repository_id" {
    type = string
    description = "The ID of the Artifact Registry repository."
    default = "ai-agents"
}

/* Cloud Storage Variables */

variable "bucket_name" {
    type = string
    description = "Cloud Storage bucket name."
    default = "ai-agents-d"
}
