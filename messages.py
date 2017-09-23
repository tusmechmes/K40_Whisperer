#!/usr/bin/env python
"""
    K40 Whisperer

    Copyright (C) <2017>  <Scorch>
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# pylint: disable=line-too-long
# pylint: disable=E0401
# pylint: disable=W0614
# pylint: disable=W0702
# pylint: disable=wildcard-import

import sys
import traceback

from globals import *

################################################################################
#                               Message Box                                    #
################################################################################
def message_box(title, message):
    """ Generic Message Box """
    if VERSION == 3:
        tkinter.messagebox.showinfo(title, message)
    else:
        tkMessageBox.showinfo(title, message)

################################################################################
#                          Message Box ask OK/Cancel                           #
################################################################################
def message_ask_ok_cancel(title, mess):
    """ Message Box ask OK/Cancel """
    if VERSION == 3:
        result = tkinter.messagebox.askokcancel(title, mess)
    else:
        result = tkMessageBox.askokcancel(title, mess)
    return result

################################################################################
#                               Message Box                                    #
################################################################################
def debug_message(message):
    """ Debug Message Box """
    if DEBUG:
        title = "Debug Message"
        if VERSION == 3:
            tkinter.messagebox.showinfo(title, message)
        else:
            tkMessageBox.showinfo(title, message)

################################################################################
# Function for outputting messages to different locations                      #
# depending on what options are enabled                                        #
################################################################################
def fmessage(text, newline=True):
    """ Function for outputting messages to different locations
        depending on what options are enabled
    """
    if not QUIET:
        if newline is True:
            try:
                sys.stdout.write(text)
                sys.stdout.write("\n")
                debug_message(traceback.format_exc())
            except:
                debug_message(traceback.format_exc())
        else:
            try:
                sys.stdout.write(text)
                debug_message(traceback.format_exc())
            except:
                debug_message(traceback.format_exc())


################################################################################
# Status Bar
################################################################################
def set_master_window(app):
    """ set the main window (master) of the applicaiton to be used for status bar and generic UI operations """
    set_master_window.app = app
    set_master_window.statusMessage = StringVar()
    set_master_window.statusbar = Label(app.master, textvariable=set_master_window.statusMessage, bd=1, relief=SUNKEN, height=1)
    set_master_window.statusbar.pack(anchor=SW, fill=X, side=BOTTOM)
set_master_window.app = None
set_master_window.statusMessage = None
set_master_window.statusbar = None

def get_app():
    """ gets the master window of the application """
    return set_master_window.app

def message_status_bar(text, bkcolor='white'):
    """ Display a message on the status bar """
    set_master_window.statusMessage.set(text)
    set_master_window.statusbar.configure(bg=bkcolor)
