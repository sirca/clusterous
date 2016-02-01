# Baking Clusterous AMIs

These scripts are used for building the AMIs used by Clusterous. There are three AMIs needed: for the controller, the nodes, and the central logging instance. Each AMI has a particular set of software and configuration.

To bake each AMI, the scripts launch an instance with the base OS, install and configure the software, and then create an AMI. All this is achieved primarily via Ansible playbooks.

## Steps

First, create a variables file containing information needed by the Ansible scripts. The file `baking_vars.template` is a template for this; just create a copy (say `baking_vars.yml`) and fill in the values. The comments in the template file provide a guide to the values for the fields.

Before running the playbooks, a few environment variables need to be defined:

```
$ export export AWS_ACCESS_KEY_ID=AKIA1234567
$ export AWS_SECRET_ACCESS_KEY="ABCD1234"
$ export ANSIBLE_HOST_KEY_CHECKING=False
```

Substitute the appropriate values for the AWS keys.

Next, run the baking scripts. Assuming that you have put all the baking variables in `baking_vars.yml`, run:

```
$ ansible-playbook -v -i hosts --extra-vars '@baking_vars.yml' 1_create_sg.yml
$ ansible-playbook -v -i hosts --extra-vars '@baking_vars.yml' 2_make_controller_ami.yml
$ ansible-playbook -v -i hosts --extra-vars '@baking_vars.yml' 2_make_node_ami.yml
$ ansible-playbook -v -i hosts --extra-vars '@baking_vars.yml' 2_make_logging_ami.yml
```

These will create the three AMIs in ap-southeast-2, each bearing the version number specified in baking_vars.yml. If the "production" tag is set, the AMIs will be made public.

Next, once you have verified that Clusterous works with the above AMIs, run the copy script to create copies in all AWS regions. Ensure that the destination regions are set under `other_regions` (note that the list should not include the source AMI).

```
$ ansible-playbook -v -i hosts --extra-vars '@baking_vars.yml' 3_copy_amis.yml
```

This process may take several hours. The list of copied AMI IDs is output to `output_file`, which must be set in the baking variables. To update Clusterous such that it uses these newly generated AMIs, add the IDs to `clusterous/scripts/machine_images.yml`

Note that currently the scripts assume that ap-southeast-2 is the primary region. This can be changed, if needed, in vars/global_vars.yml.
