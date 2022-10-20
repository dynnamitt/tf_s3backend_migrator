terraform {
  backend "s3" {
    key = "foo/kafka/buckets.tfstate"
  }
}

