## Puppet rules
The Puppet rules are present in the init file. The purpose of this script is to append /java/bin to the environment variable $PATH, so that scripts in that directory can be executed without writing the full path.

### issue detection

```
echo $PATH
```
```
Oops, something is wrong; the main directories used for executing binaries in Linux (/bin and /usr/bin) are missing.
```

* Commands like ls, cd, mkdir, rm, and others are just small programs that usually live inside a directory on our systems called /usr/bin.

```
export PATH=/bin:/usr/bin
```
By running this command, you manually add the directories that contain executing binaries (/bin and /usr/bin) to the environment variable $PATH.


Alright, now that we have a working PATH, let's look at the rule responsible for this breakage. It's located in the profile module of Puppet's production environment. To look at it, go to the manifests/ directory that contains the Puppet rules by using the following command:
```
cd /etc/puppet/code/environments/production/modules/profile/manifests

cat init.pp
```

Use cat to check out the contents of the init.pp file:


```
class profile {
        file { '/etc/profile.d/append-path.sh':
                owner   => 'root',
                group   => 'root',
                mode    => '0646',
                content => "PATH=/java/bin\n",
        }
}
```

This rule is creating a script under /etc/profile.d/. Scripts in this path will perform startup tasks, including setting up a user's own environment variables. The files under /etc/profile.d/ should only be editable by root.


* The class definition starts with the "class" keyword, followed by the name of the class. In this case, "profile".
* The contents of the class are defined between curly braces and generally contain at least one resource declaration. In this case, a "file" resource.

There could be other resources in this class, but for now it has only one file resource. Let's look at what it's doing. The file defined by this resource is '/etc/profile.d/append-path.sh', and the Puppet rule is using some of the available "file" attributes
* It sets both the owner and group of the file to "root".
* It then sets the "mode" of the file to "0646". This number represents the permissions the file will have.
* You might remember that every file and directory on a Linux system is assigned permissions for three groups of people: the owner, the group and the others.. And for each group, the permissions refer to the possibility of reading, writing and executing the file.
* It's common to use numbers to represent the permissions: 4 for read, 2 for write and 1 for execute. The sum of the permissions given to each of the groups is then a part of the final number. For example, a permission of 6 means read and write, a permission of 5 means read and execute, and a permission of 7 means read, write and execute.
* Finally, it sets the actual contents of the file. Here, the content is being set to"PATH=/java/bin\n".


### Fix problem
Before fixing the issue, let's learn a bit more about the PATH variable. This is an environment variable that contains an ordered list of paths that Linux will search for executables when running a command. Using these paths implies that we don't have to specify the absolute path for each command we want to run.

The PATH variable typically contains a few different paths, which are separated by colons. The goal of the Puppet rule that we saw was to add one specific directory to the list of paths, but unfortunately it's currently completely overwriting the contents
* We need to change the Puppet rule to append the directory without overwriting the other paths in the variable.

```
sudo nano init.pp
```
should be changed to content => "PATH=\$PATH:/java/bin\n". since we want to append /java/bin to the environment variable $PATH, and not completely replace the current content in $PATH.

* The extra backslash before the $ is necessary because Puppet also uses $ to indicate variables. But in this case, we want the dollar sign in the contents of the file.

#### files in the /etc/profile.d directory should only be editable by the root user. 

*  In other words, the mode should be 0644 not 0646.

### After that, you can trigger a manual run of the Puppet agent by running the following command:
```
sudo puppet agent -v --test
echo $PATH
```



