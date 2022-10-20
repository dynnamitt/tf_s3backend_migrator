#
#   ONLY For local testing of what the gitlab-ci.yaml does
#

.PHONY: validate init plan apply destroy clean

VAR_DIR=VAR_DIR

# n: make hack 
# https://stackoverflow.com/questions/17055773
define n


endef

err_msg = $n$n\
 Sanity-check : $n\
 -------------- $n\
 $$AWS_SESSION_TOKEN not set, $n\
 this Makefile is a local executor and $n\
 should NOT rely on HARDCODED $n\
 AWS-PROVIDER credentials/role/profile $n

ifndef AWS_SESSION_TOKEN
$(warning $(err_msg))
endif

validate: tf-code/.terraform
	cd tf-code ;\
	terraform validate

# alias
plan: plan.out plan.txt

# alias
init: tf-code/.terraform

tf-code/.terraform:
	cd tf-code ;\
	terraform init -backend-config ../$(VAR_DIR)/init.tfvars


plan.out: tf-code/.terraform
	cd tf-code ;\
	terraform plan -compact-warnings \
	 -var-file ../$(VAR_DIR)/input.tfvars \
	 -out=../$@

plan.txt:
	@echo "Using VARs set from dir [[$(VAR_DIR)]]" > $@

apply: ./plan.out ./plan.txt tf-code/.terraform
	@echo "***"
	@cat ./plan.txt
	@echo "***"
	cd tf-code ;\
	 terraform apply -compact-warnings ../plan.out

destroy: tf-code/.terraform
	cd tf-code ;\
	terraform destroy \
	  -var-file ../$(VAR_DIR)/input.tfvars \

clean:
	rm -rf tf-code/.terraform ./plan.*
