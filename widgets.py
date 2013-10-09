from Tkinter import *
import ttk


def create_container(parent):
    """utility to create a container frame within the given parent"""

    frame = ttk.Frame(parent)
    frame.grid(column=0, row=0, sticky=(N, W, E, S))
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    return frame


class ScrollableWidget(object):
    """
    wraps another widget in a frame so the other widget is scrollable
    this widget is NOT to be use directly
    """
    widget_attr = None

    def __init__(self, parent, *args, **kwargs):
        #create a frame to encompass the table and the scrollbar
        self.root = create_container(parent)

        #widget widget
        self.widget = self.init_widget(*args, **kwargs)
        self.widget.grid(column=0, row=0)
        if self.widget_attr is not None:
            setattr(self, self.widget_attr, self.widget)

        #scrollbar
        scrollbar = ttk.Scrollbar(self.root, orient=VERTICAL,
                                  command=self.widget.yview)
        scrollbar.grid(column=1, row=0, sticky=(N, S))
        self.widget['yscrollcommand'] = scrollbar.set

    def init_widget(self, *args, **kwargs):
        """init code for the widget to be widget goes here"""
        raise NotImplementedError

    def grid(self, *args, **kwargs):
        """delegates to root of widget"""
        self.root.grid(*args, **kwargs)


class AbstractTreeWidget(ScrollableWidget):
    """
    Abstract tree for implementing other widgets, meant to be inherited from,
    but not used directly
    """
    widget_attr = "tree"

    def init_widget(self, *args, **kwargs):
        """init code for the table"""
        return ttk.Treeview(self.root, *args, **kwargs)

    # @property
    # def columns(self):
    #     return self.widget["columns"]

    # @columns.setter
    # def columns(self, value):
    #     self.widget["columns"] = value

    def heading(self, name, **kwargs):
        """
        delegates to table of widget
        if the text kwarg is not provided, it defaults to name capitalized
        """
        #create the column corresponding to the name of heading
        cols = list(self.widget["columns"])
        cols.append(name)
        self.widget["columns"] = cols

        #create the heading itself
        if kwargs.pop("text", None) is None:
            kwargs["text"] = name.capitalize()
        self.widget.heading(name, **kwargs)

    def append(self, val):
        """inserts a row at the end of the table"""
        raise NotImplementedError

    def extend(self, vals):
        """
        inserts the given vals as rows at the end of the table, like
        list.extend
        """
        for v in vals:
            self.append(v)


class TableWidget(AbstractTreeWidget):
    """
    creates a fake table widget using the TreeView from ttk
    the first column of the tree is hidden as it doesn't allow us to set a
    header
    """
    widget_attr = "table"

    def append(self, val):
        """inserts a row at the end of the table"""
        print self.widget["columns"]
        data = []
        if isinstance(val, (list, tuple)):
            data = val
        elif isinstance(val, dict):
            for col in self.table["columns"]:
                data.append(val.get(col, ""))

        #use id automatically created by tk
        self.table.insert('', 'end', text='', values=data)


class ListWidget(AbstractTreeWidget):
    """creates a list widget using the Listbox from ttk"""
    widget_attr = "listview"

    def __init__(self, parent, *args, **kwargs):
        super(ListWidget, self).__init__(parent, *args, **kwargs)
        #hide the headers
        self.listview["show"] = "tree"

    def append(self, val):
        """inserts a row at the end of the table"""
        #use id automatically created by tk
        self.listview.insert('', 'end', text=val)
