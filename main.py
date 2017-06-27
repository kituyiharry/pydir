#!/usr/bin/env python3

"""
Simple File Directory Browser that i wrote as a Weekend project 
"""

import urwid
import os


class FileWalker(object):

    """Provides a Model for creating a List of current Directory 
        Structure"""

    def __init__(self):
        """TODO: to be defined1. """
        self.curdir = os.getcwd();

    def chdir_into(self,new_dir):
        if os.path.isdir(new_dir):
            os.chdir(new_dir)
            self.curdir = os.getcwd()
            return True
        return False

    def get_dir_list(self):
        dir_list = os.listdir(self.curdir)
        dir_list.insert(0,".")
        dir_list.insert(1,"..")
        return dir_list


class PaletteInflator(object):

    """An abstraction The Global palette and various operations
        such as Perhaps Loading from a config file or whatever :P"""

    def __init__(self):
        """TODO: to be defined1. """
        self._palette=[]

    @property
    def palette(self):
        """
        Returns Current active palette
        """
        return self._palette

    @palette.setter
    def palette(self,palette_list):
        """Sets Currents active Palette"""
        self._palette = palette_list


class ViewBuilder(object):

    """Sets up the Required View"""

    def __init__(self):
        """Constructor """
        self.file_walker = FileWalker()
        self.header = self.setup_header()
        self.body = self.setup_body()
        self.frame = None

    def setup_header(self,header_align="left"):
        """
        Creates a Header 
        TODO: Filter text with Ellipsizing long names
        """
        base_dir = self.file_walker.curdir

        self.header = urwid.AttrMap(urwid.Columns(
            [
                urwid.Text(item ,align=header_align) for item in base_dir.split(os.path.sep) 
            ],1
            ),"header")
        return self.header

    def gen_walker(self):
        """Creates a SimpleFocusListWalker
        :returns: TODO

        """
        return  urwid.MonitoredList([
                    urwid.AttrMap(
                        PopupableListItemButton(choice,self.SignalHandler),
                        None,focus_map="reversed") 
                    for choice in self.file_walker.get_dir_list()
                    ])

    def setup_body(self):
        """
        Body that Will be wrapped in a Frame
        """
        # return urwid.AttrMap(urwid.SolidFill(),"body")
        # for b in list_items:
            # urwid.connect_signal(b.base_widget,'click',self.SignalHandler)
        # insert a divider top pseudo-padding
        # list_items.insert(0,urwid.Divider())
        return  urwid.AttrWrap(
                urwid.Padding(                                                  #Padd left and right edges
                        urwid.Columns([                                         #Column of Entries
                            urwid.ListBox(urwid.SimpleFocusListWalker(self.gen_walker())), #Our ListBox of Items
                            urwid.Filler(urwid.Divider(div_char="="))               #TODO:replace placeholder
                        ],1),left=2,right=2) 
                    ,"body")

    def SignalHandler(self,key):
        #TODO: Open popup with this key
        if self.file_walker.chdir_into(os.path.join(self.file_walker.curdir,key.get_label())):
            self.frame.body.base_widget[0].body.clear() 
            self.frame.body.base_widget[0].body.extend(self.gen_walker())
            self.frame.body.base_widget[0].body.set_focus(0)
            #self.frame.base_widget.contents['body'][0].base_widget._invalidate()
            #self.frame.body.base_widget[0].body._modified()
            self.frame.footer = urwid.AttrMap(urwid.Text(["Changed!!" , self.file_walker.cur_dir]),'footer')
        

    def get_frame(self):
        """
        Returns TopMostFrame
        """
        if self.frame == None:
            self.frame=urwid.Frame(self.body,self.header)
        return self.frame

class PopupItemInstance(urwid.WidgetWrap):
    signals = ['close']

    def __init__(self):
        close_b = urwid.Button("Popup!!")
        urwid.connect_signal(close_b,"click",lambda stub:self._emit("close"))
        filler = urwid.Filler(close_b)
        super(PopupItemInstance,self).__init__(urwid.AttrWrap(filler,'popupbg'))


class PopupableListItemButton(urwid.PopUpLauncher):
    """
    Attached to any Button which when clicked

    TODO: Inflate some sort of button and watch out for its click signal
    """

    def __init__(self,choice_item,handler_func):
        super(PopupableListItemButton,self).__init__(ListItemButton(choice_item).attach_to_handler(handler_func).create_pop_up_bridge(self))

    def create_pop_up(self):
        """Inflate a new list with items desired 
        :returns: TODO
        """
        popup = PopupItemInstance()
        urwid.connect_signal(popup,'close',lambda stub :self.close_pop_up())
        return popup

    def get_pop_up_parameters(self):
        """
        return dict with parameters for new pop up renderinng -- see ref
        """
        return {'left':4,'top':1,'overlay_width':32,'overlay_height':7}

class ListItemButton(urwid.Button):

    """Customized Button for the Listwidget able to respond to various input"""

    def create_pop_up_bridge(self,bridge):
        self.pop_up_bridge = bridge
        return self


    def attach_to_handler(self,handler_func):
        urwid.connect_signal(self,'click',handler_func)
        return self

    def keypress(self, size, key):
        """Set Customized Actions for diff Keys e.g, Chdir or POpup

        :size: TODO
        :key: TODO
        :returns: TODO

        """
        if key in ('p' or 'P'):
            #TODO:Inflate some sort of submenu here!!
            self.pop_up_bridge.open_pop_up()
        else:
            return super(ListItemButton,self).keypress(size,key)


class PyTree(object):

    """Main Entry point for the Application, Sets up the Loop
    and inflates the Widgets"""

    def __init__(self,view_holder,paletteInflator):
        """TODO: to be defined1. 
        Retrieve our palette, Build our View
        """
        self.palette = paletteInflator.palette
        self.view = view_holder

    def exit_handler(self,keybutton):
        if keybutton in ('q','Q'):
            raise urwid.ExitMainLoop()


    def run(self):
        loop = urwid.MainLoop(self.view,self.palette,pop_ups=True,unhandled_input=self.exit_handler)
        loop.run()

if __name__ == "__main__":
    paletteInflator = PaletteInflator();
    paletteInflator.palette = [
        ('header','black','white','bold'),
        ('body','white','dark blue','bold'),
        ('reversed','standout',''),
        ('footer','black','dark red','underline'),
        ('popupbg','black','dark red','')
        ]
    tree = PyTree(ViewBuilder().get_frame(),paletteInflator)
    tree.run()
