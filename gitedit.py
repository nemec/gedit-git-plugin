import os.path
from gi.repository import GObject, Gedit, Gtk
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
    self.widget = GitWidget()
    panel = self.window.get_bottom_panel()
    icon = Gtk.Image.new_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.MENU)
    panel.add_item(self.widget, "Git Integration", "Git Integration", icon)

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

  def __init__(self):
    Gtk.Notebook.__init__(self)
    self.pages = {}
    self.pages["init"] = self.append_page(InitBox(), None)
    self.pages["repo"] = self.append_page(RepoBox(), None)
    self.pages["error"] = self.append_page(ErrorBox(), None)
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
  def __init__(self):
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
  def __init__(self):
    Gtk.Box.__init__(self)
    self.label = Gtk.Label("Init")
    self.pack_start(self.label, True, True, 0)
    self.show_all()

  def update(self, **kwargs):
    """InitBox does not have context-sensitive contents, so this is a no-op."""
    pass

class RepoBox(Gtk.Box):
  def __init__(self):
    Gtk.Box.__init__(self)
    self.last_repo = None
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

    add = Gtk.Button("Add Files")
    add.connect("clicked", self.add_files)
    untracked_box.pack_start(add, False, False, 1)
    
    self.pack_start(untracked_box, True, True, 0)
    self.show_all()

  def update(self, **kwargs):
    """
    Update the RepoBox widgets with information
    from the given repository.

    """
    repo = kwargs.get('repo', None)
    if repo:
      untracked_list = Gtk.ListStore(bool, str)
      for untracked in repo.untracked_files:
        untracked_list.append((False, untracked))
      self.untracked_view.set_model(untracked_list)
      #self.text.get_buffer().set_text(text or "No untracked files.")
      self.last_repo = repo

  def add_files(self, btn):
    """
    Add selected untracked files to be tracked with Git,
    then update the view.

    """
    for row in self.untracked_view.get_model():
      if row[0]:
        print row[1]
    self.update(repo=last_repo)
