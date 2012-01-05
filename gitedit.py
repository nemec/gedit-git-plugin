import os.path
from threading import Lock
from gi.repository import GObject, Gedit, Gtk, Gio
try:
  from git import Repo
  from git.exc import InvalidGitRepositoryError
except:
  pass


class GitEdit(GObject.Object, Gedit.WindowActivatable):
  __gtype_name__ = "GitEdit"
  window = GObject.property(type=Gedit.Window)
  
  def __init__(self):
    GObject.Object.__init__(self)
    self.widget = None

  def build_widget(self):
    self.widget = GitWidget(self.window)
    panel = self.window.get_bottom_panel()
    icon = Gtk.Image.new_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.MENU)
    panel.add_item(self.widget, "Git", "Git", icon)

  def do_activate(self):
    self.window.connect("active-tab-changed", self.on_active_tab_changed)
    self.window.connect("tab-added", self.on_tab_added)
    self.on_active_tab_changed(None, self.window.get_active_tab())
    self.build_widget()
  
  def on_active_tab_changed(self, window, tab):
    """When the active tab is changed, set the view to the current file."""
    if self.widget:
      path = os.path.dirname(tab.get_document().get_uri_for_display())
      self.widget.display_for_path(path)

  def on_tab_added(self, win, tab):
    """Listen for save on the added tab."""
    tab.get_document().connect("saved", self.on_document_saved)

  def on_document_saved(self, doc, err):
    """Take the path of the saved document and update the display."""
    if not err:
      if self.widget:
        path = os.path.dirname(doc.get_uri_for_display())
        self.widget.display_for_path(path)
    else:
      print "error saving: ", err


class GitWidget(Gtk.Notebook):

  def __init__(self, window):
    Gtk.Notebook.__init__(self)
    self.pages = {}
    self.pages["init"] = self.append_page(InitBox(window), None)
    self.pages["repo"] = self.append_page(RepoBox(window), None)
    self.pages["error"] = self.append_page(ErrorBox(window), None)
    self.set_show_tabs(False)
    
    self.set_page("repo")
    self.show_all()

  def set_page(self, name, **kwargs):
    """Set the page in the notebook by name."""
    page = self.pages[name]
    self.set_current_page(page)
    self.get_nth_page(page).update(**kwargs)

  def display_for_path(self, path):
    """
    If the current file is in a version controlled folder, display the
    repository view, otherwise display an option to initialize a new one.

    """
    try:
      try:
        repo = Repo(path)
        self.set_page("repo", repo=repo)
      except InvalidGitRepositoryError:
        self.set_page("init")
    except NameError:
      self.set_page("error", error="python-git not installed")


class ErrorBox(Gtk.Label):
  """ErrorBox is the view displayed when an error occurs with the plugin."""
  def __init__(self, window):
    Gtk.Label.__init__(self)
    self.show_all()

  def update(self, **kwargs):
    """Display the error."""
    self.set_text(kwargs.get('error', "Unknown error encountered."))


class InitBox(Gtk.Box):
  """
  InitBox is the view displayed when the current file is not version
  controlled. It provides buttons to initialize a new git repository.

  """
  def __init__(self, window):
    Gtk.Box.__init__(self)
    self.label = Gtk.Label("Init")
    self.pack_start(self.label, True, True, 0)
    self.show_all()

  def update(self, **kwargs):
    """InitBox does not have context-sensitive contents, so this is a no-op."""
    pass

class RepoBox(Gtk.Box):
  def __init__(self, window):
    Gtk.Box.__init__(self)
    self.window = window
    self.current_repo = None

    self.commit_lock = Lock()

    dobuttons = Gtk.Box()
    dobuttons.set_orientation(Gtk.Orientation.VERTICAL)
    self.refresh = Gtk.Button("Refresh")
    self.refresh.connect("clicked",
      lambda x: self.update(repo=self.current_repo))
    dobuttons.pack_start(self.refresh, False, False, 1)
    commit = Gtk.Button("Commit")
    commit.connect("clicked", self.commit_files)
    dobuttons.pack_start(commit, False, False, 1)
    self.pack_start(dobuttons, False, False, 1)
    
    # Section for Unstaged Files
    unstaged_box = Gtk.Box()
    unstaged_box.set_orientation(Gtk.Orientation.VERTICAL)
    scroll = Gtk.ScrolledWindow()
    self.unstaged_view = Gtk.TreeView()
    scroll.add(self.unstaged_view)
    self.unstaged_view.get_selection().set_mode(Gtk.SelectionMode.NONE)
    unstaged_toggle = Gtk.CellRendererToggle()
    def on_unstaged_toggle(widget, path):
      store = self.unstaged_view.get_model()
      store[path][0] = not store[path][0]
    unstaged_toggle.connect("toggled", on_unstaged_toggle)
    unstaged_column_toggle = Gtk.TreeViewColumn("", unstaged_toggle, active=0)
    self.unstaged_view.append_column(unstaged_column_toggle)
    unstaged_type = Gtk.CellRendererText()
    unstaged_column_type = Gtk.TreeViewColumn("",
      unstaged_type, text=1)
    self.unstaged_view.append_column(unstaged_column_type)
    unstaged_text = Gtk.CellRendererText()
    unstaged_column_text = Gtk.TreeViewColumn("Unstaged Files",
      unstaged_text, text=2)
    self.unstaged_view.append_column(unstaged_column_text)
    unstaged_box.pack_start(scroll, True, True, 0)
    self.pack_start(unstaged_box, False, False, 1)

    unstaged_button_box = Gtk.Box()
    add = Gtk.Button("Stage Files")
    add.connect("clicked", self.stage_files)
    unstaged_button_box.pack_start(add, False, False, 1)
    ignore = Gtk.Button("Stage All")
    ignore.connect("clicked", self.stage_files, True)
    unstaged_button_box.pack_start(ignore, False, False, 1)
    unstaged_box.pack_start(unstaged_button_box, False, False, 0)

    # Section for Untracked Files
    untracked_box = Gtk.Box()
    untracked_box.set_orientation(Gtk.Orientation.VERTICAL)
    scroll = Gtk.ScrolledWindow()
    self.untracked_view = Gtk.TreeView()
    scroll.add(self.untracked_view)
    self.untracked_view.get_selection().set_mode(Gtk.SelectionMode.NONE)
    untracked_toggle = Gtk.CellRendererToggle()
    def on_untracked_toggle(widget, path):
      store = self.untracked_view.get_model()
      store[path][0] = not store[path][0]
    untracked_toggle.connect("toggled", on_untracked_toggle)
    untracked_column_toggle = Gtk.TreeViewColumn("", untracked_toggle, active=0)
    self.untracked_view.append_column(untracked_column_toggle)
    untracked_text = Gtk.CellRendererText()
    untracked_column_text = Gtk.TreeViewColumn("Untracked Files",
      untracked_text, text=1)
    self.untracked_view.append_column(untracked_column_text)
    untracked_box.pack_start(scroll, True, True, 0)


    untracked_button_box = Gtk.Box()
    add = Gtk.Button("Track Files")
    add.connect("clicked", self.track_files)
    untracked_button_box.pack_start(add, False, False, 1)
    ignore = Gtk.Button("Ignore Files")
    ignore.connect("clicked", self.ignore_files)
    untracked_button_box.pack_start(ignore, False, False, 1)
    untracked_box.pack_start(untracked_button_box, False, False, 0)
    self.pack_start(untracked_box, False, False, 1)

    self.show_all()

  def update(self, **kwargs):
    """
    Update the RepoBox widgets with information
    from the given repository.

    """
    repo = kwargs.get('repo', None)
    if repo:
      # Set Untracked Files
      untracked_list = Gtk.ListStore(bool, str)
      for untracked in repo.untracked_files:
        untracked_list.append((False, untracked))
      self.untracked_view.set_model(untracked_list)

      # Set Unstaged Files
      unstaged_list = Gtk.ListStore(bool, str, str)
      if repo.is_dirty():
        self.refresh.set_sensitive(True)
        diffs = repo.index.diff(None)
        # Get stats for each diff in Added, Deleted, Modified, Renamed
        for diff in diffs.iter_change_type('A'):
          unstaged_list.append((False, 'A', diff.b_blob.name))
        for diff in diffs.iter_change_type('D'):
          unstaged_list.append((False, 'D', diff.a_blob.name))
        for diff in diffs.iter_change_type('M'):
          unstaged_list.append((False, 'M', diff.b_blob.name))
        for diff in diffs.iter_change_type('R'):
          unstaged_list.append((False, 'R', "{0} -> {1}".format(
            diff.a_blob.name, diff.b_blob_name)))
      else:
        self.refresh.set_sensitive(False)
      self.unstaged_view.set_model(unstaged_list)

      self.current_repo = repo


  def stage_files(self, btn, stage_all=False):
    """
    Add selected untracked files to be tracked with Git,
    then update the view.

    """
    self.current_repo.index.add(
      [row[2] for row in self.unstaged_view.get_model() if
        stage_all or row[0]])
    self.update(repo=self.current_repo)

  def track_files(self, btn):
    """
    Add selected untracked files to be tracked with Git,
    then update the view.

    """
    self.current_repo.index.add(
      [row[1] for row in self.untracked_view.get_model() if row[0]])
    self.update(repo=self.current_repo)

  def ignore_files(self, btn):
    """
    Add selected files to the bottom of the .gitignore file. No special
    heuristics are performed, each filename is inserted manually.

    """
    with open(os.path.join(self.current_repo.working_dir,
        ".gitignore"), 'a+') as ignore:
      ignore.seek(0, 2)
      if ignore.read(1) != '\n':
        ignore.write('\n')
      for row in self.untracked_view.get_model():
        if row[0]:
          ignore.write(row[1] + '\n')
    self.update(repo=self.current_repo)

  def commit_files(self, btn):
    """Commit all changes to the branch specified in HEAD."""
    commit_msg = Gio.file_new_for_path(os.path.join(
      self.current_repo.git_dir, "COMMIT_EDITMSG"))
    commit_tab = self.window.create_tab_from_location(
      commit_msg, None, 0, 0, True, True)
    # Use a lock to ensure the file isn't closed and committed before the
    # handler_id is created. Seems to be the only easy solution to sending
    # the signal handler_id to the handler itself.
    handler_id = []
    self.commit_lock.acquire()
    hid = self.window.connect("tab-removed", self.commit,
      commit_tab, handler_id, self.current_repo)
    handler_id.append(hid)
    self.commit_lock.release()

  def commit(self, window, tab, commit_tab, handler_id, repo):
    if tab == commit_tab:
      self.commit_lock.acquire()
      doc = tab.get_document()
      msg = doc.get_text(doc.get_start_iter(), doc.get_end_iter(), False)
      msg = "\n".join([line.strip() for line in msg.split('\n') if
        len(line.strip()) > 0 and not line.strip().startswith("#")])
      print msg
      print repo.index.commit(msg)
      print repo.head.commit
      if len(handler_id) > 0:
        self.window.disconnect(handler_id[0])
      self.commit_lock.release()
