from Tkinter import *
import ttk
from widgets import create_container, TableWidget, ListWidget

def FILLER(*args):
    return 1


class GUI(object):
    """main class for drawing the GUI of the manga downloader"""

    def __init__(self):
        #main window
        root = Tk()
        root.title("Manga Downloader")
        self.set_theme()

        #set up main frame with resizing
        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        #manga source combobox
        manga_src = StringVar()
        manga_src_combobox = ttk.Combobox(mainframe, textvariable=manga_src)
        manga_src_combobox.grid(column=0, row=0)
        manga_src_combobox["values"] = [str(x) for x in range(20)]

        self.create_search_box(mainframe)

        #main manga list
        manga_table = TableWidget(mainframe)
        manga_table.grid(column=0, row=2)
        manga_table.heading('fav')
        manga_table.heading('name')

        #TODO: sample rows, replace with real info
        for i in range(20):
            manga_name = "Manga %s" % (str(i + 1).zfill(2))
            manga_table.append({'name': manga_name})
        # from see import see
        # t = manga_table.widget
        # import ipdb; ipdb.set_trace()


        #TODO: replace with manga name
        manga_title_label = ttk.Label(mainframe, text="Manga Name")
        manga_title_label.grid(column=1, row=0)

        #TODO: sample rows, replace with real info
        chapter_list = ["Chapter %s" % (str(i + 1).zfill(2)) \
                        for i in range(300)]
        chapter_list.reverse()

        chapter_listbox = ListWidget(mainframe)
        chapter_listbox.grid(column=1, row=1)
        chapter_listbox.extend(chapter_list)

        #show the window
        root.mainloop()

    def set_theme(self):
        """sets the theme for Linux so it looks nice"""
        import platform
        if platform.system().lower() != "linux":
            return

        s = ttk.Style()
        if 'clam' in s.theme_names():
            s.theme_use('clam')

    def create_search_box(self, parent):
        #search text box
        self.search_query = StringVar()
        search_frame = create_container(parent)
        search_frame.grid(column=0, row=1)

        search_entry = ttk.Entry(search_frame, textvariable=self.search_query)
        search_entry.grid(column=0, row=0)

        #search button
        ttk.Button(search_frame, text="Search", command=FILLER).\
                grid(column=1, row=0)

        #update button
        ttk.Button(search_frame, text="Update", command=FILLER).\
                grid(column=2, row=0)


if __name__ == "__main__":
    gui = GUI()
