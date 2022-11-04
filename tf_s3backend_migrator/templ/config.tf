locals {

  aws_accounts = {
    test         = "???"
    stage        = "???"
    prod         = "???"
  }
  localuser_provider_role_fmt = "arn:aws:iam::%s:role/admin"

  # USEFUL shortcut
  this = local.wrkspc_config[terraform.workspace]

  # -----------------------------------------------------------------------------------
  # Workspace spesific config here
  # -----------------------------------------------------------------------------------

  wrkspc_config = {
    ###block###
  }

}

