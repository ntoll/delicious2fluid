delicious2fluid
===============

A simple script to import delicious tags into FluidDB.

Usage
+++++

You need to have an account on both delicious.com and FluidDB. To sign up for
Fluidinfo visit: https://fluidinfo.com/accounts/new/

Once installed simply run the following command and answer the questions::

    $ delicious2fluid

Your username and password for both services are *not* stored in any way shape
or form. If you encounter a problem you can find the log in the d2f.log file.

*NOTE* private bookmarks are ignored. The tags attached to them are created
within FluidDB but the object representing the private bookmark is not created.
Obviously, I don't this script to leak inadvertantly potentially private
information.

For more information about FluidDB please see: https://fluidinfo.com/

When running the script you'll be asked for your username and password for
both delicious and FluidDB.

The following tags will be created in FluidDB::

    USERNAME/delicious/url
    USERNAME/delicious/hash
    USERNAME/delicious/description
    USERNAME/delicious/time
    USERNAME/delicious/extended
    USERNAME/delicious/meta
    USERNAME/delicious/tag

Given the tags above, FluidDB will store the tag values as a collection of
strings in the "tag" tag. In addition each tag in delicious will be created
in FluidDB under the following namespace::

    USERNAME/delicious/tags
