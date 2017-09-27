#!/usr/bin/python
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
import sys
from globals import *
from math import *
from egv import egv
from nano_library import K40_CLASS
from dxf import DXF_CLASS
from svg_reader import SVG_READER
from svg_reader import SVG_TEXT_EXCEPTION
from settings import Settings

from interpolate import interpolate

import inkex
import simplestyle
import simpletransform
import cubicsuperpath
import cspsubdiv
import traceback

from messages import *

# TODO: before check in: cmake sure this is set to True
FIRE_LASER = True

LOAD_MSG = ""

if VERSION < 3 and sys.version_info[1] < 6:
    def next(item):
        return item.next()

try:
    import psyco
    psyco.full()
    LOAD_MSG = LOAD_MSG+"\nPsyco Loaded\n"
except:
    pass

import math
from time import time
import os
import re
import binascii
import getopt
import operator
import webbrowser
from PIL import Image
try:
    Image.warnings.simplefilter('ignore', Image.DecompressionBombWarning)
except:
    pass
try:
    from PIL import ImageTk
    from PIL import _imaging
except:
    pass #Don't worry everything will still work

################################################################################
class Application(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.settings = Settings()
        self.w = 780
        self.h = 490
        frame = Frame(master, width=self.w, height=self.h, name="master")
        self.master = master
        self.x = -1
        self.y = -1
        self.createWidgets()

    def createWidgets(self):
        self.initComplete = 0
        self.stop = []
        self.stop.append(False)

        self.k40 = None

        self.master.bind("<Configure>", self.Master_Configure)
        self.master.bind('<Enter>', self.bindConfigure)
        self.master.bind('<F1>', self.KEY_F1)
        self.master.bind('<F5>', self.KEY_F5)

        self.master.bind('<Control-Left>', self.Move_Left)
        self.master.bind('<Control-Right>', self.Move_Right)
        self.master.bind('<Control-Up>', self.Move_Up)
        self.master.bind('<Control-Down>', self.Move_Down)

        # INITILIZE VARIABLES        
        self.aspect_ratio = 0
        self.segID = []
        self.UI_image = None
        self.Reng_image = None
        self.SCALE = 1

        self.Reng = []
        self.Veng = []
        self.Vcut = []

        self.Reng_bounds = (0, 0, 0, 0)
        self.Veng_bounds = (0, 0, 0, 0)
        self.Vcut_bounds = (0, 0, 0, 0)

        self.laserX = 0.0
        self.laserY = 0.0
        self.PlotScale = 1.0

        # PAN and ZOOM STUFF
        self.panx = 0
        self.panx = 0
        self.lastx = 0
        self.lasty = 0
        self.move_start_x = 0
        self.move_start_y = 0

        # Status Bar
        set_master_window(self)

        # Canvas
        lbframe = Frame(self.master)
        self.PreviewCanvas_frame = lbframe
        self.PreviewCanvas = Canvas(lbframe, width=self.w-(220+20), height=self.h-200, background="grey")
        self.PreviewCanvas.pack(side=LEFT, fill=BOTH, expand=1)
        self.PreviewCanvas_frame.place(x=230, y=10)

        self.PreviewCanvas.tag_bind('LaserTag',"<1>"              , self.mousePanStart)
        self.PreviewCanvas.tag_bind('LaserTag',"<B1-Motion>"      , self.mousePan)
        self.PreviewCanvas.tag_bind('LaserTag',"<ButtonRelease-1>", self.mousePanStop)

        # Left Column #
        self.separator1 = Frame(self.master, height=2, bd=1, relief=SUNKEN)
        self.separator2 = Frame(self.master, height=2, bd=1, relief=SUNKEN)
        self.separator3 = Frame(self.master, height=2, bd=1, relief=SUNKEN)
        self.separator4 = Frame(self.master, height=2, bd=1, relief=SUNKEN)
        
        self.Label_Reng_feed_u = Label(self.master, textvariable=self.settings.funits, anchor=W)
        self.Entry_Reng_feed = Entry(self.master, width="15")
        self.Entry_Reng_feed.configure(textvariable=self.settings.Reng_feed, justify='center',fg="black")
        self.Entry_Reng_feed.bind('<Return>', self.Recalculate_Click)
        self.settings.Reng_feed.trace_variable("w", lambda v, i, n, uie=self.Entry_Reng_feed, func=self.settings.Entry_Reng_feed_Check: self.settings.entry_callback(uie, func, v, i, n))
        self.NormalColor = self.Entry_Reng_feed.cget('bg')

        self.Label_Veng_feed_u = Label(self.master, textvariable=self.settings.funits, anchor=W)
        self.Entry_Veng_feed = Entry(self.master, width="15")
        self.Entry_Veng_feed.configure(textvariable=self.settings.Veng_feed, justify='center',fg="blue")
        self.Entry_Veng_feed.bind('<Return>', self.Recalculate_Click)
        self.settings.Veng_feed.trace_variable("w", lambda v, i, n, uie=self.Entry_Veng_feed, func=self.settings.Entry_Veng_feed_Check: self.settings.entry_callback(uie, func, v, i, n))
        self.NormalColor = self.Entry_Veng_feed.cget('bg')

        self.Label_Vcut_feed_u = Label(self.master, textvariable=self.settings.funits, anchor=W)
        self.Entry_Vcut_feed   = Entry(self.master, width="15")
        self.Entry_Vcut_feed.configure(textvariable=self.settings.Vcut_feed, justify='center',fg="red")
        self.Entry_Vcut_feed.bind('<Return>', self.Recalculate_Click)
        self.settings.Vcut_feed.trace_variable("w", lambda v, i, n, uie=self.Entry_Vcut_feed, func=self.settings.Entry_Vcut_feed_Check: self.settings.entry_callback(uie, func, v, i, n))
        self.NormalColor =  self.Entry_Vcut_feed.cget('bg')

        # Buttons
        self.Reng_Button = Button(self.master, text="Raster Engrave", command=self.Raster_Eng)
        self.Veng_Button = Button(self.master, text="Vector Engrave", command=self.Vector_Eng)
        self.Vcut_Button = Button(self.master, text="Vector Cut", command=self.Vector_Cut)
        self.Label_Position_Control = Label(self.master, text="Position Controls:", anchor=W)
        self.Initialize_Button = Button(self.master, text="Initialize Laser Cutter", command=self.Initialize_Laser)
        self.Open_Button = Button(self.master, text="Open\nDesign File", command=self.menu_File_Open_Design)
        self.Reload_Button = Button(self.master, text="Reload\nDesign File", command=self.menu_Reload_Design)
        self.Home_Button = Button(self.master, text="Home", command=self.Home)
        self.UnLock_Button = Button(self.master, text="Unlock Rail", command=self.Unlock)
        self.Stop_Button = Button(self.master, text="Stop", command=self.Stop)

        try:
            self.left_image  = self.Imaging_Free(Image.open("left.png"),bg=None)
            self.right_image = self.Imaging_Free(Image.open("right.png"),bg=None)
            self.up_image    = self.Imaging_Free(Image.open("up.png"),bg=None)
            self.down_image  = self.Imaging_Free(Image.open("down.png"),bg=None)
            
            self.Right_Button   = Button(self.master,image=self.right_image, command=self.Move_Right)
            self.Left_Button    = Button(self.master,image=self.left_image,  command=self.Move_Left)
            self.Up_Button      = Button(self.master,image=self.up_image,    command=self.Move_Up)
            self.Down_Button    = Button(self.master,image=self.down_image,  command=self.Move_Down)

            self.UL_image  = self.Imaging_Free(Image.open("UL.png"),bg=None)
            self.UR_image  = self.Imaging_Free(Image.open("UR.png"),bg=None)
            self.LR_image  = self.Imaging_Free(Image.open("LR.png"),bg=None)
            self.LL_image  = self.Imaging_Free(Image.open("LL.png"),bg=None)
            self.CC_image  = self.Imaging_Free(Image.open("CC.png"),bg=None)
            
            self.UL_Button = Button(self.master,image=self.UL_image, command=self.Move_UL)
            self.UR_Button = Button(self.master,image=self.UR_image, command=self.Move_UR)
            self.LR_Button = Button(self.master,image=self.LR_image, command=self.Move_LR)
            self.LL_Button = Button(self.master,image=self.LL_image, command=self.Move_LL)
            self.CC_Button = Button(self.master,image=self.CC_image, command=self.Move_CC)
            
        except:
            self.Right_Button   = Button(self.master,text=">",          command=self.Move_Right)
            self.Left_Button    = Button(self.master,text="<",          command=self.Move_Left)
            self.Up_Button      = Button(self.master,text="^",          command=self.Move_Up)
            self.Down_Button    = Button(self.master,text="v",          command=self.Move_Down)

            self.UL_Button = Button(self.master,text=" ", command=self.Move_UL)
            self.UR_Button = Button(self.master,text=" ", command=self.Move_UR)
            self.LR_Button = Button(self.master,text=" ", command=self.Move_LR)
            self.LL_Button = Button(self.master,text=" ", command=self.Move_LL)
            self.CC_Button = Button(self.master,text=" ", command=self.Move_CC)

        self.Label_Step = Label(self.master,text="Jog Step", anchor=CENTER )
        self.Label_Step_u = Label(self.master,textvariable=self.settings.units, anchor=W)
        self.Entry_Step = Entry(self.master,width="15")
        self.Entry_Step.configure(textvariable=self.settings.jog_step, justify='center')
        self.settings.jog_step.trace_variable("w", lambda v, i, n, uie=self.Entry_Step, func=self.settings.Entry_Step_Check: self.settings.entry_callback(uie, func, v, i, n)) 

        ###########################################################################
        self.GoTo_Button = Button(self.master, text="Move To", command=self.GoTo)
        
        self.Label_GoToX = Label(self.master, text="X", anchor=CENTER )
        self.Entry_GoToX = Entry(self.master, width="15",justify='center')
        self.Entry_GoToX.configure(textvariable=self.settings.gotoX)
        self.settings.gotoX.trace_variable("w", lambda v, i, n, uie=self.Entry_GoToX, func=self.settings.Entry_GoToX_Check: self.settings.entry_callback(uie, func, v, i, n))
        
        self.Label_GoToY = Label(self.master, text="Y", anchor=CENTER )
        self.Entry_GoToY = Entry(self.master, width="15", justify='center')
        self.Entry_GoToY.configure(textvariable=self.settings.gotoY)
        self.settings.gotoY.trace_variable("w", lambda v, i, n, uie=self.Entry_GoToY, func=self.settings.Entry_GoToY_Check: self.settings.entry_callback(uie, func, v, i, n))    
        ###########################################################################
        
        # End Left Column #
        # Right Column     #
        # End Right Column #

        # GEN Setting Window Entry initializations
        self.Entry_Sspeed    = Entry()
        self.Entry_BoxGap    = Entry()
        self.Entry_ContAngle = Entry()

        # Make Menu Bar
        self.menuBar = Menu(self.master, relief = "raised", bd=2)

        top_File = Menu(self.menuBar, tearoff=0)
        top_File.add("command", label = "Save Settings File", command = self.menu_File_Save_Settings_File)
        top_File.add("command", label = "Read Settings File", command = self.menu_File_Open_Settings_File)

        top_File.add_separator()
        top_File.add("command", label = "Open Design (SVG/DXF)"  , command = self.menu_File_Open_Design)
        top_File.add("command", label = "Reload Design"          , command = self.menu_Reload_Design)

        #top_File.add_separator()
        #top_File.add("command", label = "Open EGV File"     , command = self.menu_File_Open_EGV)
    
        top_File.add_separator()
        top_File.add("command", label = "Exit"              , command = self.menu_File_Quit)
        
        self.menuBar.add("cascade", label="File", menu=top_File)

        #top_Edit = Menu(self.menuBar, tearoff=0)
        #self.menuBar.add("cascade", label="Edit", menu=top_Edit)

        top_View = Menu(self.menuBar, tearoff=0)
        top_View.add("command", label = "Refresh   <F5>", command = self.menu_View_Refresh)
        top_View.add_separator()

        top_View.add_checkbutton(label = "Show Raster Image"  ,  variable=self.settings.include_Reng ,command=self.menu_View_Refresh)
        top_View.add_checkbutton(label = "Show Vector Engrave",  variable=self.settings.include_Veng ,command=self.menu_View_Refresh)
        top_View.add_checkbutton(label = "Show Vector Cut"    ,  variable=self.settings.include_Vcut ,command=self.menu_View_Refresh)

        self.menuBar.add("cascade", label="View", menu=top_View)

        top_USB = Menu(self.menuBar, tearoff=0)
        top_USB.add("command", label = "Reset USB", command = self.Reset)
        top_USB.add("command", label = "Release USB", command = self.Release_USB)
        top_USB.add("command", label = "Initialize Laser", command = self.Initialize_Laser)
        self.menuBar.add("cascade", label="USB", menu=top_USB)
        
        top_Settings = Menu(self.menuBar, tearoff=0)
        top_Settings.add("command", label = "General Settings", command = self.GEN_Settings_Window)
        top_Settings.add("command", label = "Raster Settings", command = self.RASTER_Settings_Window)
        
        self.menuBar.add("cascade", label="Settings", menu=top_Settings)
        
        top_Help = Menu(self.menuBar, tearoff=0)
        top_Help.add("command", label = "About (e-mail)", command = self.menu_Help_About)
        top_Help.add("command", label = "Web Page", command = self.menu_Help_Web)
        self.menuBar.add("cascade", label="Help", menu=top_Help)

        self.master.config(menu=self.menuBar)

        ##########################################################################
        #                  Config File and command line options                  #
        ##########################################################################
        config_file = "k40_whisperer.txt"
        home_config1 = self.settings.HOME_DIR + "/" + config_file
        if ( os.path.isfile(config_file) ):
            self.Open_Settings_File(config_file)
        elif ( os.path.isfile(home_config1) ):
            self.Open_Settings_File(home_config1)

        opts, args = None, None
        try:
            opts, args = getopt.getopt(sys.argv[1:], "ho:",["help", "other_option"])
        except:
            debug_message('Unable interpret command line options')
            sys.exit()
##        for option, value in opts:
##            if option in ('-h','--help'):
##                fmessage(' ')
##                fmessage('Usage: python .py [-g file]')
##                fmessage('-o    : unknown other option (also --other_option)')
##                fmessage('-h    : print this help (also --help)\n')
##                sys.exit()
##            if option in ('-o','--other_option'):
##                pass
        message_status_bar("Welcome to K40 Whisperer")

    ##########################################################################
    # Menu Events
    ##########################################################################
    def menu_Reload_Design(self):
        file_full = self.settings.DESIGN_FILE
        file_name = os.path.basename(file_full)
        if ( os.path.isfile(file_full) ):
            filname = file_full
        elif ( os.path.isfile( file_name ) ):
            filname = file_name
        elif ( os.path.isfile( self.HOME_DIR+"/"+file_name ) ):
            filname = self.HOME_DIR+"/"+file_name
        else:
            message_status_bar("file not found: %s" %(os.path.basename(file_full)), 'red')
            return
        
        Name, fileExtension = os.path.splitext(filname)
        TYPE=fileExtension.upper()
        if TYPE=='.DXF':
            self.Open_DXF(filname)
        else:
            self.Open_SVG(filname)
        self.menu_View_Refresh()
        

    def menu_File_Open_Design(self):
        init_dir = os.path.dirname(self.settings.DESIGN_FILE)
        if ( not os.path.isdir(init_dir) ):
            init_dir = self.HOME_DIR

        fileselect = askopenfilename(filetypes=[("Design Files", ("*.svg","*.dxf")),
                                            ("DXF Files","*.dxf"),\
                                            ("SVG Files","*.svg"),\
                                            ("All Files","*"),\
                                            ("Design Files ", ("*.svg","*.dxf"))],\
                                            initialdir=init_dir)
        
        if ( not os.path.isfile(fileselect) ):
            return
                
        Name, fileExtension = os.path.splitext(fileselect)
        TYPE=fileExtension.upper()
        if TYPE=='.DXF':
            self.Open_DXF(fileselect)
        else:
            self.Open_SVG(fileselect)
        self.settings.DESIGN_FILE = fileselect
        self.menu_View_Refresh()

    def menu_File_Open_EGV(self):
        init_dir = os.path.dirname(self.settings.DESIGN_FILE)
        if ( not os.path.isdir(init_dir) ):
            init_dir = self.HOME_DIR
        fileselect = askopenfilename(filetypes=[("Engraver Files", ("*.egv","*.EGV")),\
                                                    ("All Files","*")],\
                                                     initialdir=init_dir)

        if fileselect != '' and fileselect != ():
            self.settings.DESIGN_FILE = fileselect
            self.Open_EGV(fileselect)
            self.menu_View_Refresh()
    
    def menu_File_Open_Settings_File(self):
        init_dir = os.path.dirname(self.settings.DESIGN_FILE)
        if ( not os.path.isdir(init_dir) ):
            init_dir = self.HOME_DIR
        fileselect = askopenfilename(filetypes=[("Settings Files", "*.txt"), ("All Files","*")], initialdir=init_dir)
        if fileselect != '' and fileselect != ():
            self.Open_Settings_File(fileselect)
            
    def menu_File_Save_Settings_File(self):
        init_dir = os.path.dirname(self.settings.DESIGN_FILE)
        if ( not os.path.isdir(init_dir) ):
            init_dir = self.HOME_DIR
            
        fileName, fileExtension = os.path.splitext(self.settings.DESIGN_FILE)
        init_file=os.path.basename(fileName)

        filename = asksaveasfilename(defaultextension='.txt', \
                                     filetypes=[("Text File", "*.txt")],\
                                     initialdir=init_dir,\
                                     initialfile= init_file )
        
        settings_data = self.settings.save(filename)

            
    def menu_File_Quit(self):
        if message_ask_ok_cancel("Exit", "Exiting...."):
            self.Quit_Click(None)


    def menu_View_Refresh(self):
        dummy_event = Event()
        dummy_event.widget=self.master
        self.Master_Configure(dummy_event,1)
        self.Plot_Data()
        xmin,xmax,ymin,ymax = self.Reng_bounds
        W = xmax-xmin
        H = ymax-ymin

        if self.settings.units.get()=="in":
            X_display = self.laserX
            Y_display = self.laserY
            W_display = W
            H_display = H
            U_display = self.settings.units.get()
        else:
            X_display = self.laserX*self.settings.units_scale
            Y_display = self.laserY*self.settings.units_scale
            W_display = W*self.settings.units_scale
            H_display = H*self.settings.units_scale
            U_display = self.settings.units.get()
        if self.settings.HomeUR.get():
            X_display = -X_display

        statusMessage = str(" Current Position: X=%.3f Y=%.3f    ( W X H )=( %.3f%s X %.3f%s ) " %(X_display, Y_display, W_display, U_display, H_display, U_display))
        message_status_bar(statusMessage)
        
    def menu_Mode_Change_Callback(self, varName, index, mode):
        self.menu_View_Refresh()

    def menu_Mode_Change(self):
        dummy_event = Event()
        dummy_event.widget=self.master
        self.Master_Configure(dummy_event,1)

    def menu_View_Recalculate(self):
        pass

    def menu_Help_About(self):
        about = "K40 Whisperer by Scorch.\n"
        about = about + "\163\143\157\162\143\150\100\163\143\157\162"
        about = about + "\143\150\167\157\162\153\163\056\143\157\155\n"
        about = about + "http://www.scorchworks.com/"
        message_box("About k40_whisperer",about)

    def menu_Help_Web(self):
        webbrowser.open_new(r"http://www.scorchworks.com/K40whisperer/k40whisperer.html")
    ################################################################################

    def Open_Settings_File(self, filename):
        # TODO: consider moving file operations to Settings class
        self.settings.load(filename)

        fileName, fileExtension = os.path.splitext(self.settings.DESIGN_FILE)
        init_file = os.path.basename(fileName)
        
        if init_file != "None":
            if ( os.path.isfile(self.settings.DESIGN_FILE) ):
                pass
                #self.Read_image_file_old(self.IMAGE_FILE)
            else:
                message_status_bar("Image file not found: %s " %(self.settings.DESIGN_FILE), 'red')

        temp_name, fileExtension = os.path.splitext(filename)
        file_base=os.path.basename(temp_name)
            
        if self.initComplete == 1:
            self.menu_Mode_Change()
            self.settings.DESIGN_FILE = filename


    ################################################################################

    def Quit_Click(self, event):
        message_status_bar("Exiting!")
        root.destroy()

    def mousePanStart(self,event):
        self.panx = event.x
        self.pany = event.y
        self.move_start_x = event.x
        self.move_start_y = event.y
        
    def mousePan(self,event):
        all = self.PreviewCanvas.find_all()
        dx = event.x-self.panx
        dy = event.y-self.pany

        self.PreviewCanvas.move('LaserTag', dx, dy)
        self.lastx = self.lastx + dx
        self.lasty = self.lasty + dy
        self.panx = event.x
        self.pany = event.y
        
    def mousePanStop(self,event):
        Xold = round(self.laserX,3)
        Yold = round(self.laserY,3)

        can_dx = event.x-self.move_start_x
        can_dy = -(event.y-self.move_start_y)
        
        dx = can_dx*self.PlotScale
        dy = can_dy*self.PlotScale
        if self.settings.HomeUR.get():
            dx = -dx
        self.laserX,self.laserY = self.XY_in_bounds(dx,dy)

        DXmils = round((self.laserX - Xold)*1000.0,0)

        DYmils = round((self.laserY - Yold)*1000.0,0)
        if self.k40 != None:
            self.k40.rapid_move(DXmils,DYmils)
        self.menu_View_Refresh()

    def LASER_Size(self):
        MINX = 0.0
        MAXY = 0.0
        if self.settings.units.get()=="in":
            MAXX =  float(self.settings.LaserXsize.get())
            MINY = -float(self.settings.LaserYsize.get())
        else:
            MAXX =  float(self.settings.LaserXsize.get())/25.4
            MINY = -float(self.settings.LaserYsize.get())/25.4

        return (MAXX-MINX,MAXY-MINY)

    def XY_in_bounds(self,dx_inches,dy_inches):
        MINX = 0.0
        MAXY = 0.0
        if self.settings.units.get()=="in":
            MAXX =  float(self.settings.LaserXsize.get())
            MINY = -float(self.settings.LaserYsize.get())
        else:
            MAXX =  float(self.settings.LaserXsize.get())/25.4
            MINY = -float(self.settings.LaserYsize.get())/25.4
        
        xmin,xmax,ymin,ymax = self.Reng_bounds
        
        X = self.laserX + dx_inches
        X = min(MAXX-(xmax-xmin),X)
        X = max(MINX,X)
        
        Y = self.laserY + dy_inches
        Y = max(MINY+(ymax-ymin),Y)
        Y = min(MAXY,Y)
        
        X = round(X,3)
        Y = round(Y,3)
        return X,Y

    def Recalculate_Click(self, event):
        pass

    #############################    

    ##########################################################################
    ##########################################################################
    def Check_All_Variables(self):
        pass
       
        # MAIN_error_cnt= \
        # self.entry_set(self.Entry_Yscale, self.Entry_Yscale_Check()    ,2) +\
        # self.entry_set(self.Entry_Toptol, self.Entry_Toptol_Check()    ,2) 

        # GEN_error_cnt= \
        # self.entry_set(self.Entry_ContAngle,self.Entry_ContAngle_Check(),2)

        # ERROR_cnt = MAIN_error_cnt + GEN_error_cnt

        # if (ERROR_cnt > 0):
        #     message_status_bar(" ", 'red')
        # if (GEN_error_cnt > 0):
        #     message_status_bar(" Entry Error Detected: Check Entry Values in General Settings Window ", 'red')
        # if (MAIN_error_cnt > 0):
        #     message_status_bar(" Entry Error Detected: Check Entry Values in Main Window ", 'red')
        # return ERROR_cnt     

    #############################
    def Open_SVG(self, filemname):
        self.Reng_image = None
        self.SCALE = 1
        
        self.Reng = []
        self.Veng = []
        self.Vcut = []
        
        self.Reng_bounds = (0,0,0,0)
        self.Veng_bounds = (0,0,0,0)
        self.Vcut_bounds = (0,0,0,0)
        
        self.SVG_FILE = filemname
        svg_reader = SVG_READER(self.settings)
        try:
            try:
                svg_reader.parse(self.SVG_FILE)
                svg_reader.fix_svg_coords()
                svg_reader.make_paths()
            except SVG_TEXT_EXCEPTION as e:
                message_status_bar("Converting TEXT to PATHS.")
                svg_reader.parse(self.SVG_FILE)
                svg_reader.make_paths(txt2paths=True)
                
        except StandardError as e:
            msg1 = "SVG file load failed: "
            msg2 = "%s" %(e)
            message_status_bar((msg1+msg2).split("\n")[0], 'red')
            message_box(msg1, msg2)
            debug_message(traceback.format_exc())
            return
        except:
            message_status_bar("Unable To open SVG File: %s" %(filemname), 'red')
            debug_message(traceback.format_exc())
            return
        xmax = svg_reader.Xsize/25.4
        ymax = svg_reader.Ysize/25.4
        xmin = 0
        ymin = 0

        self.Reng_bounds = (xmin,xmax,ymin,ymax)
        
        ##########################
        ###   Create ECOORDS   ###
        ##########################
        self.Vcut,self.Vcut_bounds = self.make_ecoords(svg_reader.cut_lines,scale=1/25.4)
        self.Veng,self.Veng_bounds = self.make_ecoords(svg_reader.eng_lines,scale=1/25.4)
        self.Veng_bounds = None
        self.Vcut_bounds = None
        ##########################
        ###   Load Image       ###
        ##########################
        self.Reng_image = svg_reader.raster_PIL
        #self.Reng_image = self.Reng_image.convert("L")
        
        if (self.Reng_image != None):
            self.wim, self.him = self.Reng_image.size
            self.aspect_ratio =  float(self.wim-1) / float(self.him-1)
            #self.make_raster_coords()

    def make_ecoords(self,coords,scale=1):
        xmax, ymax = -1e10, -1e10
        xmin, ymin =  1e10,  1e10
        ecoords=[]
        Acc=.001
        oldx = oldy = -99990.0
        first_stroke = True
        loop=0
        for line in coords:
            XY = line
            x1 = XY[0]*scale
            y1 = XY[1]*scale
            x2 = XY[2]*scale
            y2 = XY[3]*scale
            depth = XY[4]
            dx = oldx - x1
            dy = oldy - y1
            dist = sqrt(dx*dx + dy*dy)
            # check and see if we need to move to a new discontinuous start point
            if (dist > Acc) or first_stroke:
                loop = loop+1
                first_stroke = False
                ecoords.append([x1, y1, loop, depth])
            ecoords.append([x2, y2, loop, depth])
            oldx, oldy = x2, y2
            xmax=max(xmax,x1,x2)
            ymax=max(ymax,y1,y2)
            xmin=min(xmin,x1,x2)
            ymin=min(ymin,y1,y2)
        bounds = (xmin, xmax, ymin, ymax)
        return ecoords, bounds

    # def convert_greyscale(self,image):
    #     image = image.convert('RGB')
    #     x_lim, y_lim = image.size
    #     grey = Image.new("L", image.size, color=255)
        
    #     pixel = image.load()
    #     grey_pixel = grey.load()
        
    #     for y in range(1, y_lim):
    #         message_status_bar("Converting to greyscale: %.1f %%" %( (100.0*y)/y_lim ) )
    #         for x in range(1, x_lim):
    #             value = pixel[x, y]
    #             grey_pixel[x,y] = int( value[0]*.333 + value[1]*.333 +value[2]*.333 )
    #             #grey_pixel[x,y] = int( value[0]*.210 + value[1]*.720 +value[2]*.007 )
    #             grey_pixel[x,y] = int( value[0]*.299 + value[1]*.587 +value[2]*.114 )

    #     grey.save("adjusted_grey.png","PNG")
    #     return grey
 
    #####################################################################
    def make_raster_coords(self):
            ecoords=[]
            if (self.Reng_image != None):
                cutoff=128
                image_temp = self.Reng_image.convert("L")

                if self.settings.halftone.get():
                    #start = time()
                    ht_size_mils =  round( 1000.0 / float(self.settings.ht_size.get()) ,1)
                    npixels = int( round(ht_size_mils,1) )
                    if npixels == 0:
                        return
                    wim,him = image_temp.size
                    # Convert to Halftoning and save
                    nw=int(wim / npixels)
                    nh=int(him / npixels)
                    image_temp = image_temp.resize((nw,nh))
                    
                    image_temp = self.convert_halftoning(image_temp)
                    image_temp = image_temp.resize((wim,him))
                    #print time()-start

                Reng_np = image_temp.load()
                #######################################
                x=0
                y=0
                loop=1

                Raster_step = self.settings.get_raster_step_1000in()
                for i in range(0,self.him,Raster_step):
                    if i%10 == 0:
                        message_status_bar("Raster Engraving: Creating Scan Lines: %.1f %%" %( (100.0*i)/self.him ) )
                    if self.stop[0]==True:
                        raise StandardError("Action stopped by User.")
                    line = []
                    cnt=1
                    for j in range(1,self.wim):
                        if (Reng_np[j,i] == Reng_np[j-1,i]):
                            cnt = cnt+1
                        else:
                            laser = "U" if Reng_np[j-1,i] > cutoff else "D"
                            line.append((cnt,laser))
                            cnt=1
                    laser = "U" if Reng_np[j-1,i] > cutoff else "D"
                    line.append((cnt,laser))
                    
                    y=(self.him-i)/1000.0
                    x=0
                    rng = range(0,len(line),1)
                        
                    for i in rng:
                        seg = line[i]
                        delta = seg[0]/1000.0
                        if seg[1]=="D":
                            loop=loop+1
                            ecoords.append([x      ,y,loop])
                            ecoords.append([x+delta,y,loop])
                        x = x + delta
                        
            self.Reng = ecoords
            if ecoords == []:
                raise UserWarning('failed to generate ecoords for given raster image')
    #######################################################################

    '''This Example opens an Image and transform the image into halftone.  -Isai B. Cicourel'''
    # Create a Half-tone version of the image
    def convert_halftoning(self,image):
        image = image.convert('L')
        x_lim, y_lim = image.size
        pixel = image.load()
        
        M1 = float(self.settings.bezier_M1.get())
        M2 = float(self.settings.bezier_M2.get())
        w  = float(self.settings.bezier_weight.get())
        
        if w > 0:
            x, y = self.settings.generate_bezier(M1, M2, w)
            
            interp = interpolate(x, y) # Set up interpolate class
            val_map=[]
            # Map Bezier Curve to values between 0 and 255
            for val in range(0,256):
                val_out = int(round(interp[val])) # Get the interpolated value at each value
                val_map.append(val_out)
            # Adjust image
            for y in range(1, y_lim):
                message_status_bar("Raster Engraving: Adjusting Image Darkness: %.1f %%" %( (100.0*y)/y_lim ) )
                for x in range(1, x_lim):
                    pixel[x, y] = val_map[ pixel[x, y] ]

        message_status_bar("Raster Engraving: Creating Halftone Image." )
        image = image.convert('1')
     
        # image.save("Z:\\000.png","PNG")
        # junk = image.convert("1")
        # junk.save("Z:\\001.png","PNG")   
        # for y in range(1, y_lim):
        #     message_status_bar("Raster Engraving: Creating Halftone Image: %.1f %%" %( (100.0*y)/y_lim ) )
        #     if self.stop[0]==True:
        #         raise StandardError("Action stopped by User.")
                   
        #     for x in range(1, x_lim):
        #         oldpixel = pixel[x, y]
        #         newpixel = 255*floor(oldpixel/128)
        #         pixel[x,y] = newpixel
        #         perror = oldpixel - newpixel

        #         if x < x_lim - 1:
        #             pixel[x+1, y  ] = pixel[x+1, y  ] + round(perror * 7/16)
        #         if x > 1 and y < y_lim - 1:
        #             pixel[x-1, y+1] = pixel[x-1, y+1] + round(perror * 3/16)
        #         if y < y_lim - 1:
        #             pixel[x  , y+1] = pixel[x  , y+1] + round(perror * 5/16)
        #         if x < x_lim - 1 and y < y_lim - 1:
        #             pixel[x+1, y+1] = pixel[x+1, y+1] + round(perror * 1/16)
        # image.save("Z:\\002.png","PNG") 

        return image

    #######################################################################

    def Open_EGV(self,filemname):
        pass
        EGV_data=[]
        data=""
        with open(filemname) as f:
            while True:
                c = f.read(1)
                if not c:
                  break
                if c=='\n' or c==' ' or c=='\r':
                    pass
                else:
                    data=data+"%c" %c
                    EGV_data.append(ord(c))
        if message_ask_ok_cancel("EGV", "Send EGV Data to Laser...."):
            self.send_egv_data(EGV_data)


    def Open_DXF(self,filemname):
        self.Reng_image = None
        self.SCALE = 1
        
        self.Reng = []
        self.Veng = []
        self.Vcut = []
        
        self.Reng_bounds = (0,0,0,0)
        self.Veng_bounds = (0,0,0,0)
        self.Vcut_bounds = (0,0,0,0)

        
        self.DXF_FILE = filemname
        dxf_import=DXF_CLASS()
        segarc = 5
        try:
            fd = open(self.DXF_FILE)
            dxf_import.GET_DXF_DATA(fd,tol_deg=segarc)
            fd.close()
        except StandardError as e:
            msg1 = "DXF Load Failed:"
            msg2 = "%s" %(e)
            message_status_bar((msg1+msg2).split("\n")[0], 'red')
            message_box(msg1, msg2)
            debug_message(traceback.format_exc())
        except:
            fmessage("Unable To open Drawing Exchange File (DXF) file.")
            debug_message(traceback.format_exc())
            return
        
        new_origin=False
        #dxfcoords=dxf_import.DXF_COORDS_GET(new_origin)
        dxf_engrave_coords = dxf_import.DXF_COORDS_GET_TYPE(engrave=True, new_origin=False)
        dxf_cut_coords     = dxf_import.DXF_COORDS_GET_TYPE(engrave=False,new_origin=False)
        
        dxf_units = dxf_import.units
        if dxf_import.dxf_messages != "":
            message_box("DXF Import:",dxf_import.dxf_messages)
            
        if dxf_units=="Unitless":
            d = UnitsDialog(root)
            dxf_units = d.result

        if dxf_units=="Inches":
            dxf_scale = 1.0
        elif dxf_units=="Feet":
            dxf_scale = 12.0
        elif dxf_units=="Miles":
            dxf_scale = 5280.0*12.0
        elif dxf_units=="Millimeters":
            dxf_scale = 1.0/25.4
        elif dxf_units=="Centimeters":
            dxf_scale = 1.0/2.54
        elif dxf_units=="Meters":
            dxf_scale = 1.0/254.0
        elif dxf_units=="Kilometers":
            dxf_scale = 1.0/254000.0
        elif dxf_units=="Microinches":
            dxf_scale = 1.0/1000000.0
        elif dxf_units=="Mils":
            dxf_scale = 1.0/1000.0
        else:
            return
        
        ##########################
        ###   Create ECOORDS   ###
        ##########################
        #self.Vcut,self.Vcut_bounds = self.make_ecoords(dxfcoords,scale=1.0/25.4)
        #self.Reng_bounds = self.Vcut_bounds

        self.Vcut,self.Vcut_bounds = self.make_ecoords(dxf_cut_coords    , scale=dxf_scale)
        self.Veng,self.Veng_bounds = self.make_ecoords(dxf_engrave_coords, scale=dxf_scale)

        xmin = min(self.Vcut_bounds[0],self.Veng_bounds[0])
        xmax = max(self.Vcut_bounds[1],self.Veng_bounds[1])
        ymin = min(self.Vcut_bounds[2],self.Veng_bounds[2])
        ymax = max(self.Vcut_bounds[3],self.Veng_bounds[3])
        self.Reng_bounds = (xmin,xmax,ymin,ymax)

    ##########################################################################


    ##########################################################################
    def Move_UL(self,dummy=None):
        #if self.k40 != None:
        #    message_box("Upper Left Corner","Press OK to return.")

        xmin,xmax,ymin,ymax = self.Reng_bounds
        if self.settings.HomeUR.get():
            Xnew = self.laserX + (xmax-xmin)
            DX = round((xmax-xmin)*1000.0)
        else:
            Xnew = self.laserX
            DX = 0
            
        (Xsize,Ysize)=self.LASER_Size()
        if Xnew <= Xsize+.001:
            if self.k40 != None:
                self.k40.rapid_move( DX, 0 )
                message_box("Upper Left Corner","Press OK to return.")
                self.k40.rapid_move(-DX, 0 )
        else:
            pass

    def Move_UR(self,dummy=None):
        xmin,xmax,ymin,ymax = self.Reng_bounds
        if self.settings.HomeUR.get():
            Xnew = self.laserX
            DX = 0
        else:
            Xnew = self.laserX + (xmax-xmin) 
            DX = round((xmax-xmin)*1000.0)

        (Xsize,Ysize)=self.LASER_Size()
        if Xnew <= Xsize+.001:
            if self.k40 != None:
                self.k40.rapid_move( DX, 0 )
                message_box("Upper Right Corner","Press OK to return.")
                self.k40.rapid_move(-DX, 0 )
        else:
            pass
    
    def Move_LR(self,dummy=None):
        xmin,xmax,ymin,ymax = self.Reng_bounds
        if self.settings.HomeUR.get():
            Xnew = self.laserX
            DX = 0
        else:
            Xnew = self.laserX + (xmax-xmin) 
            DX = round((xmax-xmin)*1000.0)
            
        Ynew = self.laserY - (ymax-ymin)
        (Xsize,Ysize)=self.LASER_Size()
        if Xnew <= Xsize+.001 and Ynew >= -Ysize-.001:
            if self.k40 != None:
                DY = round((ymax-ymin)*1000.0)
                self.k40.rapid_move( DX,-DY )
                message_box("Lower Right Corner","Press OK to return.")
                self.k40.rapid_move(-DX, DY )
        else:
            pass
    
    def Move_LL(self,dummy=None):
        xmin,xmax,ymin,ymax = self.Reng_bounds
        if self.settings.HomeUR.get():
            Xnew = self.laserX + (xmax-xmin)
            DX = round((xmax-xmin)*1000.0)
        else:
            Xnew = self.laserX
            DX = 0
            
        Ynew = self.laserY - (ymax-ymin)
        (Xsize,Ysize)=self.LASER_Size()
        if Xnew <= Xsize+.001 and Ynew >= -Ysize-.001:
            if self.k40 != None:
                DY = round((ymax-ymin)*1000.0)
                self.k40.rapid_move( DX,-DY )
                message_box("Lower Left Corner","Press OK to return.")
                self.k40.rapid_move(-DX, DY )
        else:
            pass

    def Move_CC(self,dummy=None):
        xmin,xmax,ymin,ymax = self.Reng_bounds
        #Xnew = self.laserX + (xmax-xmin)/2.0
        if self.settings.HomeUR.get():
            Xnew = self.laserX + (xmax-xmin)/2.0 
            DX = round((xmax-xmin)/2.0*1000.0)
        else:
            Xnew = self.laserX + (xmax-xmin)/2.0 
            DX = round((xmax-xmin)/2.0*1000.0)

            
        Ynew = self.laserY - (ymax-ymin)/2.0
        (Xsize,Ysize)=self.LASER_Size()
        if Xnew <= Xsize+.001 and Ynew >= -Ysize-.001:
            if self.k40 != None:
                
                DY = round((ymax-ymin)/2.0*1000.0)
                self.k40.rapid_move( DX,-DY )
                message_box("Center","Press OK to return.")
                self.k40.rapid_move(-DX, DY )
        else:
            pass


    def Move_Right(self,dummy=None):
        JOG_STEP = float( self.settings.jog_step.get() )
        self.Rapid_Move( JOG_STEP,0 )

    def Move_Left(self,dummy=None):
        JOG_STEP = float( self.settings.jog_step.get() )
        self.Rapid_Move( -JOG_STEP,0 )

    def Move_Up(self,dummy=None):
        JOG_STEP = float( self.settings.jog_step.get() )
        self.Rapid_Move( 0,JOG_STEP )

    def Move_Down(self,dummy=None):
        JOG_STEP = float( self.settings.jog_step.get() )
        self.Rapid_Move( 0,-JOG_STEP )

    def Rapid_Move(self,dx,dy):
        if self.settings.units.get()=="in":
            dx_inches = round(dx,3)
            dy_inches = round(dy,3)
        else:
            dx_inches = round(dx/25.4,3)
            dy_inches = round(dy/25.4,3)

        if (self.settings.HomeUR.get()):
            dx_inches = -dx_inches

        Xnew,Ynew = self.XY_in_bounds(dx_inches,dy_inches)
        dxmils = (Xnew - self.laserX)*1000.0
        dymils = (Ynew - self.laserY)*1000.0
        if self.k40 != None:
            self.k40.rapid_move(dxmils,dymils)

        self.laserX  = Xnew
        self.laserY  = Ynew
        self.menu_View_Refresh()

    def update_gui(self, message=None):
        if message != None:
            message_status_bar(message)   

    def set_gui(self,new_state="normal"):
        self.menuBar.entryconfigure("File"    , state=new_state)
        #self.menuBar.entryconfigure("Edit"    , state=new_state)
        self.menuBar.entryconfigure("View"    , state=new_state)
        self.menuBar.entryconfigure("USB"     , state=new_state)
        self.menuBar.entryconfigure("Settings", state=new_state)
        self.menuBar.entryconfigure("Help"    , state=new_state)
        self.PreviewCanvas.configure(state=new_state)
        
        for w in self.master.winfo_children():
            try:
                w.configure(state=new_state)
            except:
                pass
        self.Stop_Button.configure(state="normal")
        message_status_bar(" ")    

    def Vector_Cut(self):
        self.stop[0]=False
        self.set_gui("disabled")
        message_status_bar("Vector Cut: Processing Vector Data.", 'green')
        if self.Vcut!=[]:
            self.send_data("Vector_Cut")
        else:
            message_status_bar("No vector data to cut", 'yellow')
        self.set_gui("normal")
        
    def Vector_Eng(self):
        self.stop[0]=False
        self.set_gui("disabled")
        message_status_bar("Vector Engrave: Processing Vector Data.", 'green')
        if self.Veng!=[]:
            self.send_data("Vector_Eng")
        else:
            message_status_bar("No vector data to engrave", 'yellow')
        self.set_gui("normal")

    def Raster_Eng(self):
        self.stop[0]=False
        self.set_gui("disabled")
        message_status_bar("Raster Engraving: Processing Image Data.", 'green')
        try:
            self.make_raster_coords()
            if self.Reng != []:
                self.send_data("Raster_Eng")
                self.Reng = []    # clear engraving coords
            else:
                message_status_bar("No raster data to engrave", 'yellow')
        except (StandardError, UserWarning) as e:
            msg1 = "Making Raster Data Stopped: "
            msg2 = "%s" %(e)
            message_status_bar((msg1+msg2).split("\n")[0], 'red')
            message_box(msg1, msg2)
            debug_message(traceback.format_exc())
            
        self.set_gui("normal")

    ################################################################################
 
    def Sort_Paths(self,ecoords,i_loop=2):
        ##########################
        ###   find loop ends   ###
        ##########################
        Lbeg=[]
        Lend=[]
        if len(ecoords)>0:
            Lbeg.append(0)
            loop_old=ecoords[0][i_loop]
            for i in range(1,len(ecoords)):
                loop = ecoords[i][i_loop]
                if loop != loop_old:
                    Lbeg.append(i)
                    Lend.append(i-1)
                loop_old=loop
            Lend.append(i)

        #######################################################
        # Find new order based on distance to next beg or end #
        #######################################################
        order_out = []
        use_beg=0
        if len(ecoords)>0:
            order_out.append([Lbeg[0],Lend[0]])
        inext = 0
        total=len(Lbeg)
        for i in range(total-1):
            if use_beg==1:
                ii=Lbeg.pop(inext)
                Lend.pop(inext)
            else:
                ii=Lend.pop(inext)
                Lbeg.pop(inext)

            Xcur = ecoords[ii][0]
            Ycur = ecoords[ii][1]

            dx = Xcur - ecoords[ Lbeg[0] ][0]
            dy = Ycur - ecoords[ Lbeg[0] ][1]
            min_dist = dx*dx + dy*dy

            dxe = Xcur - ecoords[ Lend[0] ][0]
            dye = Ycur - ecoords[ Lend[0] ][1]
            min_diste = dxe*dxe + dye*dye

            inext=0
            inexte=0
            for j in range(1,len(Lbeg)):
                dx = Xcur - ecoords[ Lbeg[j] ][0]
                dy = Ycur - ecoords[ Lbeg[j] ][1]
                dist = dx*dx + dy*dy
                if dist < min_dist:
                    min_dist=dist
                    inext=j
                ###
                dxe = Xcur - ecoords[ Lend[j] ][0]
                dye = Ycur - ecoords[ Lend[j] ][1]
                diste = dxe*dxe + dye*dye
                if diste < min_diste:
                    min_diste=diste
                    inexte=j
                ###
            if min_diste < min_dist:
                inext=inexte
                order_out.append([Lend[inexte],Lbeg[inexte]])
                use_beg=1
            else:
                order_out.append([Lbeg[inext],Lend[inext]])
                use_beg=0
        ###########################################################
        return order_out
    
    #####################################################
    # determine if a point is inside a given polygon or not
    # Polygon is a list of (x,y) pairs.
    # http://www.ariel.com.au/a/python-point-int-poly.html
    #####################################################
    def point_inside_polygon(self,x,y,poly):
        n = len(poly)
        inside = -1
        p1x = poly[0][0]
        p1y = poly[0][1]
        for i in range(n+1):
            p2x = poly[i%n][0]
            p2y = poly[i%n][1]
            if y > min(p1y,p2y):
                if y <= max(p1y,p2y):
                    if x <= max(p1x,p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = inside * -1
            p1x,p1y = p2x,p2y

        return inside

    def optimize_paths(self,ecoords):
        # TODO: pre-sort by depth (small to large) then optimize within each depth group
        order_out = self.Sort_Paths(ecoords)
        lastx=-999
        lasty=-999
        Acc=0.004
        cuts=[]

        for line in order_out:
            temp=line
            if temp[0] > temp[1]:
                step = -1
            else:
                step = 1

            loop_old = -1
            
            for i in range(temp[0],temp[1]+step,step):
                x1    = ecoords[i][0]
                y1    = ecoords[i][1]
                loop  = ecoords[i][2]
                depth = ecoords[i][3]
                # check and see if we need to move to a new discontinuous start point
                if (loop != loop_old):
                    dx = x1-lastx
                    dy = y1-lasty
                    dist = sqrt(dx*dx + dy*dy)
                    if dist > Acc:
                        cuts.append([[x1, y1, depth]])
                    else:
                        cuts[-1].append([x1, y1, depth])
                else:
                    cuts[-1].append([x1, y1, depth])
                lastx = x1
                lasty = y1
                loop_old = loop
        #####################################################
        # For each loop determine if other loops are inside #
        #####################################################
        Nloops=len(cuts)
        self.LoopTree=[]
        for iloop in range(Nloops):
            self.LoopTree.append([])
##            CUR_PCT=float(iloop)/Nloops*100.0
##            if (not self.batch.get()):
##                message_status_bar('Determining Which Side of Loop to Cut: %d of %d' %(iloop+1,Nloops))
            ipoly = cuts[iloop]
            ## Check points in other loops (could just check one) ##
            if ipoly != []:
                for jloop in range(Nloops):
                    if jloop != iloop:
                        inside = 0
                        inside = inside + self.point_inside_polygon(cuts[jloop][0][0],cuts[jloop][0][1],ipoly)
                        if inside > 0:
                            self.LoopTree[iloop].append(jloop)
        #####################################################
        for i in range(Nloops):
            lns=[]
            lns.append(i)
            self.remove_self_references(lns,self.LoopTree[i])

        self.order=[]
        self.loops = range(Nloops)
        for i in range(Nloops):
            if self.LoopTree[i]!=[]:
                self.addlist(self.LoopTree[i])
                self.LoopTree[i]=[]
            if self.loops[i]!=[]:
                self.order.append(self.loops[i])
                self.loops[i]=[]
        ecoords_out = []
        for i in self.order:
            line = cuts[i]
            for coord in line:
                loop_id = i
                depth = coord[2]
                ecoords_out.append([coord[0], coord[1], loop_id, depth])
        return ecoords_out
            
    def remove_self_references(self,loop_numbers,loops):
        for i in range(0,len(loops)):
            for j in range(0,len(loop_numbers)):
                if loops[i]==loop_numbers[j]:
                    loops.pop(i)
                    return
            if self.LoopTree[loops[i]]!=[]:
                loop_numbers.append(loops[i])
                self.remove_self_references(loop_numbers,self.LoopTree[loops[i]])

    def addlist(self,list):
        for i in list:
            if self.LoopTree[i]!=[]:
                self.addlist(self.LoopTree[i])
                self.LoopTree[i]=[]
            if self.loops[i]!=[]:
                self.order.append(self.loops[i])
                self.loops[i]=[]
  
    def send_data(self, operation_type=None):
        try:
            if self.settings.units.get() == 'in':
                feed_factor = 25.4/60.0
            else:
                feed_factor = 1.0
                
            xmin,xmax,ymin,ymax = self.Reng_bounds
            if self.settings.HomeUR.get():
                xmin,xmax,ymin,ymax = self.Reng_bounds
                flipXoffset = xmax-xmin
            else:
                flipXoffset = 0
                        
            # optimize paths and determin the ecoordinates to use
            ecoords = []
            raster_step = 0
            if (operation_type == "Vector_Cut") and (self.Vcut != []):
                feed_Rate = float(self.settings.Vcut_feed.get()) * feed_factor
                message_status_bar("Vector Cut: Determining Cut Order....")
                self.Vcut = self.optimize_paths(self.Vcut)
                ecoords = self.Vcut

            if (operation_type == "Vector_Eng") and (self.Veng != []):
                feed_Rate = float(self.settings.Veng_feed.get()) * feed_factor
                message_status_bar("Vector Engrave: Determining Cut Order....")
                self.Veng = self.optimize_paths(self.Veng)
                ecoords = self.Veng

            if (operation_type == "Raster_Eng") and (self.Reng != []):
                feed_Rate = float(self.settings.Reng_feed.get()) * feed_factor
                ecoords = self.Reng
                raster_step = self.settings.get_raster_step_1000in()

            # generate EGV data
            message_status_bar("Generating EGV data...")
            egv_data = []
            egv_inst = egv(target=lambda s:egv_data.append(s))
            # TODO: read "use_depth_info" from settings and ignore the depth if it is not set
            egv_inst.make_egv_data(ecoords, startX=xmin, startY=ymax, Feed=feed_Rate, board_name=self.settings.board_name.get(), \
                                   Raster_step=raster_step, update_gui=self.update_gui, stop_calc=self.stop, FlipXoffset=flipXoffset, useDepthInfo=USE_DEPTH_INFO)
            self.master.update()
            
            # message_status_bar("Saving Data to File....")
            # self.write_egv_to_file(egv_data)
            # message_status_bar("Done Saving Data to File....")
            # self.set_gui("normal")

            # send data to device
            if FIRE_LASER:
                self.send_egv_data(egv_data)
            self.menu_View_Refresh()

        except MemoryError as e:
            raise StandardError("Memory Error:  Out of Memory.")
            debug_message(traceback.format_exc())
        
        except StandardError as e:
            msg1 = "Sending Data Stopped: "
            msg2 = "%s" %(e)
            if msg2 == "":
                formatted_lines = traceback.format_exc().splitlines()
            message_status_bar((msg1+msg2).split("\n")[0], 'red')
            message_box(msg1, msg2)
            debug_message(traceback.format_exc())

    def send_egv_data(self,data):
        if self.k40 != None:
            self.k40.timeout       = int(self.settings.t_timeout.get())   
            self.k40.n_timeouts    = int(self.settings.n_timeouts.get())
            self.k40.send_data(data, self.update_gui, self.stop)
        else:
            self.k40 = K40_CLASS()
            self.k40.timeout       = int(self.settings.t_timeout.get())   
            self.k40.n_timeouts    = int(self.settings.n_timeouts.get())
            self.k40.send_data(data, self.update_gui, self.stop)
            self.k40 = None
            self.master.update()

        self.menu_View_Refresh()
        
    ##########################################################################
    ##########################################################################
    def write_egv_to_file(self,data):
        try:
            fname = "EGV_DATA.EGV"
            fout = open(fname,'w')
        except:
            message_status_bar("Unable to open file for writing: %s" %(fname), 'red')
            return
        #ctog="B"
        for char_val in data:
            char = chr(char_val)
            if char == "N":
                fout.write("\n")
                fout.write("%s" %(char))
            elif char == "E":
                fout.write("%s" %(char))
                fout.write("\n")
            else:
                fout.write("%s" %(char))
        fout.write("\n")
        fout.close
        
    def Home(self):
        if self.k40 != None:
            self.k40.home_position()
        self.laserX  = 0.0
        self.laserY  = 0.0
        self.menu_View_Refresh()

    def GoTo(self):
        xpos = float(self.settings.gotoX.get())
        ypos = float(self.settings.gotoY.get())
        if self.k40 != None:
            self.k40.home_position()
        self.laserX  = 0.0
        self.laserY  = 0.0
        self.Rapid_Move(xpos,ypos)
        self.menu_View_Refresh()  
        
    def Reset(self):
        if self.k40 != None:
            try:
                self.k40.reset_usb()
                message_status_bar("USB Reset Succeeded", 'green')
            except:
                debug_message(traceback.format_exc())
                pass
            
    def Stop(self,event=None):
        line1 = "The K40 Whisperer is currently Paused."
        line2 = "Press \"OK\" to stop current action."
        line3 = "Press \"Cancel\" to resume."
        if message_ask_ok_cancel("Stop Laser Job.", "%s\n\n%s\n%s" %(line1,line2,line3)):
            self.stop[0]=True

    def Release_USB(self):
        if self.k40 != None:
            try:
                self.k40.release_usb()
                message_status_bar("USB Release Succeeded", 'green')
            except:
                debug_message(traceback.format_exc())
                pass
            self.k40=None
        
    def Initialize_Laser(self,junk=None):
        self.stop[0]=False
        self.Release_USB()
        self.k40=K40_CLASS()
        try:
            self.k40.initialize_device()
            self.k40.read_data()
            self.k40.say_hello()
            self.Home()
        except StandardError as e:
            error_text = "%s" %(e)
            if "BACKEND" in error_text.upper():
                error_text = error_text + " (libUSB driver not installed)"
            message_status_bar("USB Error: %s" %(error_text), 'red')
            self.k40=None
            debug_message(traceback.format_exc())

        except:
            message_status_bar("Unknown USB Error", 'red')
            self.k40=None
            debug_message(traceback.format_exc())
            
    def Unlock(self):
        if self.k40 != None:
            try:
                self.k40.unlock_rail()
                message_status_bar("Rail Unlock Succeeded", 'green')
            except:
                debug_message(traceback.format_exc())
                pass
    
    ##########################################################################
    ##########################################################################

    def KEY_F1(self, event):
        self.menu_Help_About()

    def KEY_F5(self, event):
        self.menu_View_Refresh()

    def bindConfigure(self, event):
        if not self.initComplete:
            self.initComplete = 1
            self.menu_Mode_Change()

    def Master_Configure(self, event, update=0):
        if event.widget != self.master:
            return
        x = int(self.master.winfo_x())
        y = int(self.master.winfo_y())
        w = int(self.master.winfo_width())
        h = int(self.master.winfo_height())
        if (self.x, self.y) == (-1,-1):
            self.x, self.y = x,y
        if abs(self.w-w)>10 or abs(self.h-h)>10 or update==1:
            ###################################################
            #  Form changed Size (resized) adjust as required #
            ###################################################
            self.w=w
            self.h=h

            if 0 == 0:                
                # Left Column #
                w_label=90
                w_entry=45
                w_units=55

                x_label_L=10
                x_entry_L=x_label_L+w_label+20
                x_units_L=x_entry_L+w_entry+2

                Yloc=15
                self.Initialize_Button.place (x=12, y=Yloc, width=100*2, height=23)
                Yloc=Yloc+33

                self.Open_Button.place (x=12, y=Yloc, width=100, height=40)
                self.Reload_Button.place(x=12+100, y=Yloc, width=100, height=40)                

                Yloc=Yloc+50
                self.separator1.place(x=x_label_L, y=Yloc,width=w_label+75+40, height=2)
                Yloc=Yloc+6
                self.Label_Position_Control.place(x=x_label_L, y=Yloc, width=w_label*2, height=21)

                Yloc=Yloc+25
                self.Home_Button.place (x=12, y=Yloc, width=100, height=23)
                self.UnLock_Button.place(x=12+100, y=Yloc, width=100, height=23)

                Yloc=Yloc+33
                self.Label_Step.place(x=x_label_L, y=Yloc, width=w_label, height=21)
                self.Label_Step_u.place(x=x_units_L, y=Yloc, width=w_units, height=21)
                self.Entry_Step.place(x=x_entry_L, y=Yloc, width=w_entry, height=23)

                ###########################################################################
                Yloc=Yloc+30
                bsz=40
                xoffst=35
                self.UL_Button.place    (x=xoffst+12      ,  y=Yloc, width=bsz, height=bsz)
                self.Up_Button.place    (x=xoffst+12+bsz  ,  y=Yloc, width=bsz, height=bsz)
                self.UR_Button.place    (x=xoffst+12+bsz*2,  y=Yloc, width=bsz, height=bsz)
                Yloc=Yloc+bsz
                self.Left_Button.place  (x=xoffst+12      ,y=Yloc, width=bsz, height=bsz)
                self.CC_Button.place    (x=xoffst+12+bsz  ,y=Yloc, width=bsz, height=bsz)
                self.Right_Button.place (x=xoffst+12+bsz*2,y=Yloc, width=bsz, height=bsz)
                Yloc=Yloc+bsz
                self.LL_Button.place    (x=xoffst+12      ,  y=Yloc, width=bsz, height=bsz)
                self.Down_Button.place  (x=xoffst+12+bsz  ,  y=Yloc, width=bsz, height=bsz)
                self.LR_Button.place    (x=xoffst+12+bsz*2,  y=Yloc, width=bsz, height=bsz)
            
                
                Yloc=Yloc+bsz
                ###########################################################################
                self.Label_GoToX.place(x=x_entry_L, y=Yloc, width=w_entry, height=23)
                self.Label_GoToY.place(x=x_units_L, y=Yloc, width=w_entry, height=23)
                Yloc=Yloc+25
                self.GoTo_Button.place (x=12, y=Yloc, width=100, height=23)
                self.Entry_GoToX.place(x=x_entry_L, y=Yloc, width=w_entry, height=23)
                self.Entry_GoToY.place(x=x_units_L, y=Yloc, width=w_entry, height=23)
                ###########################################################################
                            

                #From Bottom up
                Yloc=self.h-70
                self.Stop_Button.place (x=12, y=Yloc, width=100*2, height=30)
                self.Stop_Button.configure(bg='light coral')
                Yloc=Yloc-10

                Yloc=Yloc-30
                self.Vcut_Button.place  (x=12, y=Yloc, width=100, height=23)
                self.Entry_Vcut_feed.place(  x=x_entry_L, y=Yloc, width=w_entry, height=23)
                self.Label_Vcut_feed_u.place(x=x_units_L, y=Yloc, width=w_units, height=23)
                
                Yloc=Yloc-30
                self.Veng_Button.place  (x=12, y=Yloc, width=100, height=23)
                self.Entry_Veng_feed.place(  x=x_entry_L, y=Yloc, width=w_entry, height=23)
                self.Label_Veng_feed_u.place(x=x_units_L, y=Yloc, width=w_units, height=23)

                Yloc=Yloc-30
                self.Reng_Button.place  (x=12, y=Yloc, width=100, height=23)
                self.Entry_Reng_feed.place(  x=x_entry_L, y=Yloc, width=w_entry, height=23)
                self.Label_Reng_feed_u.place(x=x_units_L, y=Yloc, width=w_units, height=23)
                
                Yloc=Yloc-15
                self.separator2.place(x=x_label_L, y=Yloc,width=w_label+75+40, height=2)
                # End Left Column #

                self.PreviewCanvas.configure( width = self.w-(220+20), height = self.h-50 )
                self.PreviewCanvas_frame.place(x=220, y=10)

                self.Set_Input_States()
                
            self.Plot_Data()
            
    def Recalculate_RQD_Click(self, event):
        self.menu_View_Refresh()

    def Set_Input_States(self):
        pass

    def Imaging_Free(self, image_in, bg="#ffffff"):
        image_in = image_in.convert('L')
        wim,him = image_in.size
        image_out=PhotoImage(width=wim,height=him)
        pixel=image_in.load()
        if bg!=None:
            image_out.put(bg, to=(0,0,wim,him))
        for y in range(0,him):
            for x in range(0,wim):
                val=pixel[x,y]
                if val!=255:
                    image_out.put("#%02x%02x%02x" %(val,val,val),(x,y))
        return image_out

    ##########################################
    #        CANVAS PLOTTING STUFF           #
    ##########################################
    def Plot_Data(self):
        self.PreviewCanvas.delete(ALL)
        if (self.Check_All_Variables() > 0):
            return

        for seg in self.segID:
            self.PreviewCanvas.delete(seg)
        self.segID = []
        
        cszw = int(self.PreviewCanvas.cget("width"))
        cszh = int(self.PreviewCanvas.cget("height"))
        buff=10
        wc = float(cszw/2)
        hc = float(cszh/2)        
        
        maxx = float(self.settings.LaserXsize.get()) / self.settings.units_scale
        minx = 0.0
        maxy = 0.0
        miny = -float(self.settings.LaserYsize.get()) / self.settings.units_scale
        midx=(maxx+minx)/2
        midy=(maxy+miny)/2
        
        self.PlotScale = max((maxx-minx)/(cszw-buff), (maxy-miny)/(cszh-buff))
        
        x_lft = cszw/2 + (minx-midx) / self.PlotScale
        x_rgt = cszw/2 + (maxx-midx) / self.PlotScale
        y_bot = cszh/2 + (maxy-midy) / self.PlotScale
        y_top = cszh/2 + (miny-midy) / self.PlotScale
        self.segID.append( self.PreviewCanvas.create_rectangle(
                    x_lft, y_bot, x_rgt, y_top, fill="gray80", outline="gray80", width = 0) )

        xmin,xmax,ymin,ymax = self.Reng_bounds


        if (self.settings.HomeUR.get()):
            XlineShift = maxx - self.laserX - (xmax-xmin)
        else:
            XlineShift = self.laserX
        YlineShift = self.laserY    

        ######################################
        ###       Plot Raster Image        ###
        ######################################
        if self.Reng_image != None:
            if self.settings.include_Reng.get():     
                try:
                    dpi = 1000  # TODO: make this configurable in settings
                    new_SCALE = (1.0/self.PlotScale) / dpi 
                    if new_SCALE != self.SCALE:
                        self.SCALE = new_SCALE
                        nw=int(self.SCALE*self.wim)
                        nh=int(self.SCALE*self.him)
                        #PIL_im = PIL_im.convert("1") #"1"=1BBP, "L"=grey
                        if self.settings.halftone.get() == False:
                            plot_im = self.Reng_image.convert("L")
                            plot_im = plot_im.point(lambda x: 0 if x<128 else 255, '1')
                        else:
                            plot_im = self.Reng_image
                        try:
                            self.UI_image = ImageTk.PhotoImage(plot_im.resize((nw,nh), Image.ANTIALIAS))
                        except:
                            debug_message("Imaging_Free Used.")
                            self.UI_image = self.Imaging_Free(plot_im.resize((nw,nh), Image.ANTIALIAS))
                except:
                    self.SCALE = 1
                    debug_message(traceback.format_exc())
                    
                self.Plot_Raster(self.laserX, self.laserY, x_lft,y_top,self.PlotScale,im=self.UI_image)
        else:
            self.UI_image = None
        ######################################
        ###       Plot Veng Coords         ###
        ######################################
        if self.settings.include_Veng.get():
            loop_old = -1
            scale=1
            for line in self.Veng:
                XY    = line
                x1    = (XY[0]-xmin)*scale
                y1    = (XY[1]-ymax)*scale
                loop  = XY[2]
                color = "blue"
                # check and see if we need to move to a new discontinuous start point
                if (loop == loop_old):
                    self.Plot_Line(xold, yold, x1, y1, x_lft, y_top, XlineShift, YlineShift, self.PlotScale, color)
                loop_old = loop
                xold=x1
                yold=y1

        ######################################
        ###       Plot Vcut Coords         ###
        ######################################
        if self.settings.include_Vcut.get():
            loop_old = -1
            scale=1
            for line in self.Vcut:
                XY    = line
                x1    = (XY[0]-xmin)*scale
                y1    = (XY[1]-ymax)*scale
                loop  = XY[2]
                color = "#{0:02x}{1:02x}{2:02x}".format(XY[3], 0, 0)
                # check and see if we need to move to a new discontinuous start point
                if (loop == loop_old):
                    self.Plot_Line(xold, yold, x1, y1, x_lft, y_top, XlineShift, YlineShift, self.PlotScale, color)
                loop_old = loop
                xold=x1
                yold=y1


        # ######################################
        # ###       Plot Reng Coords         ###
        # ######################################
        # Plot_Reng = False
        # if Plot_Reng and self.Reng!=[]:
        #     loop_old = -1
        #     scale = 1
        #     #xmin,xmax,ymin,ymax = self.Vcut_bounds
        #    for line in self.Reng:
        #        XY    = line
        #        x1    = (XY[0]-xmin)*scale
        #        y1    = (XY[1]-ymax)*scale

        #        loop  = XY[2]
        #        color = "gray20"
        #        # check and see if we need to move to a new discontinuous start point
        #        if (loop == loop_old):
        #            self.Plot_Line(xold, yold, x1, y1, x_lft, y_top, XlineShift, YlineShift, self.PlotScale, color)
        #        loop_old = loop
        #        xold=x1
        #        yold=y1 

            
        ######################################
        dot_col = "grey50"
        self.Plot_circle(self.laserX,self.laserY,x_lft,y_top,self.PlotScale,dot_col,radius=5)

        
    def Plot_Raster(self, XX, YY, Xleft, Ytop, PlotScale, im):
        if (self.settings.HomeUR.get()):
            maxx = float(self.settings.LaserXsize.get()) / self.settings.units_scale
            xmin,xmax,ymin,ymax = self.Reng_bounds
            xplt = Xleft + ( maxx-XX-(xmax-xmin) )/PlotScale
        else:
            xplt = Xleft +  XX/PlotScale
            
        yplt = Ytop  - YY/PlotScale
        self.segID.append(
            self.PreviewCanvas.create_image(xplt, yplt, anchor=NW, image=im,tags='LaserTag')
            )
        
    def Plot_circle(self, XX, YY, Xleft, Ytop, PlotScale, col, radius=0):
        if (self.settings.HomeUR.get()):
            maxx = float(self.settings.LaserXsize.get()) / self.settings.units_scale
            xplt = Xleft + maxx/PlotScale - XX/PlotScale
        else:
            xplt = Xleft + XX/PlotScale
        yplt = Ytop  - YY/PlotScale
        self.segID.append(
            self.PreviewCanvas.create_oval(
                                            xplt-radius,
                                            yplt-radius,
                                            xplt+radius,
                                            yplt+radius,
                                            fill=col, outline=col, width = 0,tags='LaserTag') )

    def Plot_Line(self, XX1, YY1, XX2, YY2, Xleft, Ytop, XlineShift, YlineShift, PlotScale, col, thick=0):
        xplt1 = Xleft + (XX1 + XlineShift )/PlotScale 
        xplt2 = Xleft + (XX2 + XlineShift )/PlotScale
        yplt1 = Ytop  - (YY1 + YlineShift )/PlotScale
        yplt2 = Ytop  - (YY2 + YlineShift )/PlotScale
        
        self.segID.append(
            self.PreviewCanvas.create_line( xplt1,
                                            yplt1,
                                            xplt2,
                                            yplt2,
                                            fill=col, capstyle="round", width = thick, tags='LaserTag') )
        
    
    ################################################################################
    #                         General Settings Window                              #
    ################################################################################
    def GEN_Settings_Window(self):
        self.settings.show_general_settings_dialog()
        self.menu_View_Refresh()

    ################################################################################
    #                          Raster Settings Window                              #
    ################################################################################
    def RASTER_Settings_Window(self):
        self.settings.show_raster_settings_dialog()
        self.menu_View_Refresh()

################################################################################
#                         Choose Units Dialog                                  #
################################################################################
import tkSimpleDialog
class UnitsDialog(tkSimpleDialog.Dialog):
    def body(self, master):
        self.resizable(0,0)
        self.title('Units')
        self.iconname("Units")

        try:
            self.iconbitmap(bitmap="@emblem64")
        except:
            pass
        
        self.uom = StringVar()
        self.uom.set("Millimeters")

        Label(master, text="Select DXF Import Units:").grid(row=0)
        Radio_Units_IN = Radiobutton(master,text="Inches",        value="Inches")
        Radio_Units_MM = Radiobutton(master,text="Millimeters",   value="Millimeters")
        Radio_Units_CM = Radiobutton(master,text="Centimeters",   value="Centimeters")
        
        Radio_Units_IN.grid(row=1, sticky=W)
        Radio_Units_MM.grid(row=2, sticky=W)
        Radio_Units_CM.grid(row=3, sticky=W)

        Radio_Units_IN.configure(variable=self.uom)
        Radio_Units_MM.configure(variable=self.uom)
        Radio_Units_CM.configure(variable=self.uom)

    def apply(self):
        self.result = self.uom.get()
        return 


################################################################################
#                          Startup Application                                 #
################################################################################
    
root = Tk()
app = Application(root)
app.master.title("K40 Whisperer V"+WHISPERER_VERSION)
app.master.iconname("K40")
app.master.minsize(800,560) #800x600 min

try:
    app.master.iconbitmap(bitmap="@emblem64")
except:
    pass

#try:
#    os.chdir(os.path.expanduser("~"))
#except:
#    pass
if LOAD_MSG != "":
    message_box("K40 Whisperer", LOAD_MSG)
debug_message("Debuging is turned on.")

root.mainloop()
