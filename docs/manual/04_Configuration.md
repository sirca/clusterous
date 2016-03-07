# Configuring Clusterous

After you install Clusterous, you need to configure it with your AWS account credentials before you can begin using it.

## `setup`
The `setup` command launches an interactive wizard to guide you through configuring Clusterous and preparing your AWS account for use. Once you have entered all your configuration information and choices, the wizard will ask you to name your "configuration profile".

The cloud configuration information is stored in your home directory under "~/.clusterous.yml". Under normal operation, you should not have to refer to or modify this file.

## Multiple configuration profiles
Under some circumstances, it is useful to have multiple configurations. For example, in AWS, you may want to run clusters on different regions; since each region will need different resources (such as VPCs and Key Pairs), you create a different profile for each region.

To create a new configuration profile, simply run `setup` again.

    clusterous setup

The `setup` command will never overwrite your existing configuration; it will simply create a new one.

Once you have more than one configuration profile, you can use the `profile` command to manage them. The `profile` command itself accepts four different subcommands.

To list the profiles you have configured so far, and see which is the current profile, use `ls`:

    clusterous profile ls

To switch to another profile, use `use`. If, say, the profile you want to switch to is named "my-other-profile":

   clusterous use my-other-profile

Note that you should `destroy` any currently running profile before switching profiles.

You may also display the contents of an existing profile using `show`. This is useful if you want to share your configuration information with other Clusterous users on your team.

To delete an existing profile, use `rm`:

    clusterous rm my-old-profile

Note that you cannot delete the current profile.

## Profile resources
When setting up a new configuration profile, the `setup` command offers to create certain AWS resources for you. These include a VPC, a Key Pair and an S3 bucket. Clusterous will not delete or destroy any AWS resources created during the `setup` step.

If you want to delete these resources (if say you are not using Clusterous any more), you must do so manually via the AWS Console or with other tools.
