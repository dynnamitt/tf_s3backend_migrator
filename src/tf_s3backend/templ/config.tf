locals {

  localuser_provider_role_fmt = "arn:aws:iam::%s:role/admin"

  # USEFUL shortcut
  this = local.wrkspc_config[terraform.workspace]

  # COMMON CONSTs (new feat, can also be var-with-default)
  ###constants###

  # -----------------------------------------------------------------------------------
  # Workspace spesific config here
  #   (use local.this.__PROP__ to get value)
  # -----------------------------------------------------------------------------------

  wrkspc_config = {
    ###wrkspc_config###
  }
}
