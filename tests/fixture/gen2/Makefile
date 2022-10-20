# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#                   S  T  A  T  E
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
s_region  = eu-west-1
s_bucket  = foo-tf-backend-$(ENV)
s_table   = foo-tf-backend-lock-$(ENV)
s_key     = my_project/$(SRC).tfstate
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

vars_file = input-$(ENV).tfvars

# CONSTANTs
SRC_default = tf-code


ifndef ENV
$(error ENV must be set ($(ENV_alternatives)), matching AWS_PROFILE)
endif

# ifneq ($(tf_ver_actual),$(tf_ver_lock))
#  $(error Wrong terraform client version! Respect the .terraform-version file )
# endif

ifndef AWS_PROFILE
$(warning $$AWS_PROFILE not set, not important when executor is cicd)
endif

ifndef SRC
$(warning SRC not set, defaulting to "$(SRC_default)/" )
endif

SRC ?= $(SRC_default)
PLAN_FILE = plan.$(SRC).out
PLAN_DESCR = $(PLAN_FILE).txt

define status_doc
===============
aws identity:  $(shell aws sts get-caller-identity --output text --query Arn)
state.bucket:  $(s_bucket)
state.table:   $(s_table)
state.key:     $(s_key)
SRC directory: $(SRC)/
PLAN file:     $(PLAN_FILE)
tfvars file:   $(vars_file)
env tfvars:    $(shell env | grep TF_VAR | cut -d= -f1)
tf ver:        $(tf_ver_actual)
===============
endef

STATUS_DOC = $(status_doc)
$(info $(STATUS_DOC))

.PHONY: validate init plan apply destroy clean


# default target
# alias
init: $(SRC)/.terraform

validate: $(SRC)/.terraform
	cd $(SRC) ;\
	terraform validate

# alias
plan: $(PLAN_FILE) $(PLAN_DESCR)
backup: /tmp/backup_$(ENV)_$(s_key)

$(SRC)/.terraform:
	tfenv install
	cd $(SRC) && \
	terraform init \
	-backend-config=region=$(s_region) \
	-backend-config=bucket=$(s_bucket) \
	-backend-config=dynamodb_table=$(s_table) \
	-backend-config=key=$(s_key)

/tmp/backup_$(ENV)_$(s_key):
	aws s3 cp --region=$(s_region) \
	s3://$(s_bucket)/$(s_key) $@

$(PLAN_FILE): $(SRC)/.terraform $(vars_file)
	cd $(SRC) && \
	terraform refresh -var-file ../$(vars_file) > /dev/null && \
	terraform plan -refresh=false -compact-warnings \
	 -var-file ../$(vars_file) -out=../$@

export DESCR=$(STATUS_DOC)
$(PLAN_DESCR):
	printf "$$DESCR" > $@

refresh: $(SRC)/.terraform $(vars_file)
	@echo
	cd $(SRC) && \
	 terraform refresh -var-file ../$(vars_file)

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
	-rm -rf $(SRC)/.terraform
	-rm $(PLAN_FILE) $(PLAN_DESCR)


import:
	echo "cd into $(SRC) (after init) and do the imports"
