# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#                   S  T  A  T  E
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
s_account_n := $(if $(filter $(ENV),dev),test,$(ENV))
s_region  := eu-west-1
s_bucket  := foobar-tf-backend-$(s_account_n)
s_table   := foo-backend-lock-$(s_account_n)
s_proj_suffix := $(if $(filter $(ENV),dev),__dev)
s_key     = proj101$(s_proj_suffix)/$(SRC).tfstate
# - - - - w - - - - - - - - - - - - - - - - - - - - - - - - - -

vars_file := input-$(ENV).tfvars

# CONSTANTs , don't override
SRC_default = tf-code
ENV_alternatives := test dev stage prod
empty:=
space:= $(empty) $(empty)

ifndef SRC
$(warning SRC not set, defaulting to "$(SRC_default)/" )
endif

SRC ?= $(SRC_default)

# GUARD 1
ifndef ENV
# unless ONLY apply ??? $(if $(filter $(MAKECMDGOALS),apply),?)
$(error ENV must be set [$(subst $(space),|,$(ENV_alternatives))], and matching AWS_PROFILE/cicd-tag)
endif

# GUARD 2
ifneq ($(findstring $(ENV),$(ENV_alternatives)),$(ENV))
# unless ONLY apply ??? $(if $(filter $(MAKECMDGOALS),apply),?)
$(error ENV must be set [$(subst $(space),|,$(ENV_alternatives))], and matching AWS_PROFILE/cicd-tag)
endif


# Version-lock !
tf_ver_actual = $(shell terraform -v | head -n1 | sed 's/[^ ]* v//')
tf_ver_lock = $(shell cat .terraform-version)

ifneq ($(tf_ver_actual),$(tf_ver_lock))
 $(warning Wrong terraform client version! Respect the .terraform-version file )
endif

ifndef AWS_PROFILE
$(warning $$AWS_PROFILE not set, not important when executor is cicd)
endif


PLAN_FILE = plan.$(SRC).out
PLAN_DESCR = $(PLAN_FILE).txt

define status_doc
================================================================================
aws identity:  $(shell aws sts get-caller-identity --output text --query Arn)
state.bucket:  $(s_bucket)
state.table:   $(s_table)
state.key:     $(s_key)
SRC directory: $(SRC)/
PLAN file:     $(PLAN_FILE)
tfvars file:   $(vars_file)
env tfvars:    $(shell env | grep TF_VAR | cut -d= -f1)
tf ver:        $(tf_ver_actual)
================================================================================
endef

STATUS_DOC = $(status_doc)
$(info $(STATUS_DOC))

.PHONY: validate init plan apply destroy clean


# default target
# alias
init: $(SRC)/.terraform

validate: $(SRC)/.terraform
	tfenv install
	cd $(SRC) ;\
	terraform validate

# alias
plan: $(PLAN_FILE) $(PLAN_DESCR)

$(SRC)/.terraform:
	tfenv install
	cd $(SRC) && \
	terraform init \
	-backend-config=region=$(s_region) \
	-backend-config=bucket=$(s_bucket) \
	-backend-config=dynamodb_table=$(s_table) \
	-backend-config=key=$(s_key)

$(PLAN_FILE): $(SRC)/.terraform $(vars_file)
	cd $(SRC) && \
	terraform plan -compact-warnings \
	 -var-file ../$(vars_file) \
	 -out=../$@

export DESCR=$(STATUS_DOC)
$(PLAN_DESCR):
	printf "$$DESCR" > $@

apply: $(PLAN_FILE) $(PLAN_DESCR) $(SRC)/.terraform
	@cat $(PLAN_DESCR)
	@echo
	cd $(SRC) && \
	 terraform apply -compact-warnings ../$<

destroy: $(SRC)/.terraform $(vars_file)
	cd $(SRC) && \
	terraform destroy \
	  -var-file ../$(vars_file) \

clean:
	rm -rf $(SRC)/.terraform
	-rm $(PLAN_FILE) $(PLAN_DESCR)

import:
	echo "cd into $(SRC) (after init) and do the imports"
