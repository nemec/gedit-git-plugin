**Note:** this repository is not being maintained and does not work in the latest Gedit. Feel free to try [dvhart's fork](https://github.com/dvhart/gedit-git-plugin) or fork it yourself.


GitEdit
=======

GitEdit is a Gedit plugin that provides Git integration.

It is in no way intended to be a feature-complete implementation of Git,
rather it represents a very simple Git workflow; enough for a beginner but
providing enough avenues for monitoring a repository to be useful to a
more advanced Git user.


Requirements
------------

* GitPython-3.X+ (correct version not presently in the Ubuntu repositories,
    must install separately
    from https://github.com/gitpython-developers/GitPython)
* Gedit-3.X+ - This plugin is built for Gnome3, will not work in Gnome2


Install
-------

Copy the files gitedit.py and gitedit.plugin to
~/.local/share/gedit/plugins (or a subdirectory thereof) and restart Gedit.


Usage
-----

Select the plugin in Edit->Preferences->Plugins and switch to the Git tab
on the bottom panel.


Features
--------

* Click the `Refresh` button to refresh the bottom page.
* Upon switching to a new tab, repository information for the current
  file is displayed.
* If the file is not part of a repository, provides options to Initialize
  a new repository or Checkout from a remote repository.
* Unstaged files are displayed, with indicators as to whether the file has
  been Added, Deleted, Renamed, or Modified.
* Untracked files are listed, with an option to Track or Ignore the files.
  Ignored filenames are appended to the .gitignore file in the root directory
  of the repository. gitignore file is created if it does not exist.
* Commit staged changes.

<center>
<img src="https://github.com/nemec/gedit-git-plugin/raw/master/screenshot.png"\>
</center>


Planned Features
----------------

* Push changes to a branch to a specified remote repository.
* Pull changes to a branch from a specified remote repository.
* Manage remote repositories.

Known Issues
------------

* Plugin does not display repository data when first enabled
  (Workaround: switch tabs, then switch back)

