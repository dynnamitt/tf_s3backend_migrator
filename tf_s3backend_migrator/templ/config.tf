locals {


  aws_accounts = {
    test         = "822152007605"
    stage        = "739805770819"
    prod         = "905279427843"
    team_cmp     = "337896910382"
    ruterbastion = "028715740751"
    master       = "067137084833"

  }
  localuser_provider_role_fmt = "arn:aws:iam::%s:role/bfadmin"

  # USEFUL shortcut
  this = local.wrkspc_config[terraform.workspace]

  # -----------------------------------------------------------------------------------
  # Workspace spesific config here
  # -----------------------------------------------------------------------------------

  wrkspc_config = {
    ###block###
  }

}

