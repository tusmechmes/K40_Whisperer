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
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=missing-docstring
# pylint: disable=bare-except
# pylint: disable=unused-argument
# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-statements
# pylint: disable=too-many-arguments
# pylint: disable=no-self-use
# pylint: disable=too-many-locals
# pylint: disable=too-many-public-methods
# TODO: too-many-branches

import os
from globals import *
from messages import *

class Settings(object):
    """ General Settings inluding UI support and serilaization """
    def __init__(self):
        self.HOME_DIR = os.path.expanduser("~")
        if not os.path.isdir(self.HOME_DIR):
            self.HOME_DIR = ""
        self.DESIGN_FILE = (self.HOME_DIR + "/None")
        self.units_scale = 1.0
        self.BezierCanvas = None
        self.raster_settings = None

        self.__create_ui_vars__()
        self.__set_default_values__()
        self.__update_derived_variables__()

    def __set_default_values__(self):
        """ Initialize with default values
            if you want to change a default setting this is the place to do it
        """
        self.include_Reng.set(1)
        self.include_Veng.set(1)
        self.include_Vcut.set(1)
        self.halftone.set(0)
        self.HomeUR.set(0)
        self.units.set("mm") # Options are "in" and "mm"
        self.px2mm.set("0.1")
        self.t_timeout.set("2000")
        self.n_timeouts.set("30")
        self.jog_step.set("10.0")
        self.rast_step.set("0.002")
        self.ht_size.set(500)
        self.Reng_feed.set("100")
        self.Veng_feed.set("20")
        self.Vcut_feed.set("10")
        self.bezier_weight.set("3.5")
        self.bezier_M1.set("2.5")
        self.bezier_M2.set("0.50")
        self.bezier_weight_default = float(self.bezier_weight.get())
        # Board options are
        #    "LASER-M2",
        #    "LASER-M1",
        #    "LASER-M",
        #    "LASER-B2",
        #    "LASER-B1",
        #    "LASER-B",
        #    "LASER-A"
        self.board_name.set("LASER-M2")
        self.LaserXsize.set("325")
        self.LaserYsize.set("220")
        self.gotoX.set("0.0")
        self.gotoY.set("0.0")

    def __update_derived_variables__(self):
        ''' Update any derived variables '''
        self.bezier_M1_default = float(self.bezier_M1.get())
        self.bezier_M2_default = float(self.bezier_M2.get())

        if self.units.get() == 'in':
            self.funits.set('in/min')
            self.units_scale = 1.0
        else:
            self.units.set('mm')
            self.funits.set('mm/s')
            self.units_scale = 25.4

    def __create_ui_vars__(self):
        self.include_Reng = BooleanVar()
        self.include_Veng = BooleanVar()
        self.include_Vcut = BooleanVar()
        self.halftone = BooleanVar()
        self.HomeUR = BooleanVar()
        self.board_name = StringVar()
        self.units = StringVar()
        self.funits = StringVar()
        self.px2mm = StringVar()
        self.jog_step = StringVar()
        self.rast_step = StringVar()
        self.ht_size = StringVar()
        self.Reng_feed = StringVar()
        self.Veng_feed = StringVar()
        self.Vcut_feed = StringVar()
        self.bezier_M1 = StringVar()
        self.bezier_M2 = StringVar()
        self.bezier_weight = StringVar()
        self.LaserXsize = StringVar()
        self.LaserYsize = StringVar()
        self.gotoX = StringVar()
        self.gotoY = StringVar()
        self.inkscape_path = StringVar()
        self.t_timeout = StringVar()
        self.n_timeouts = StringVar()

    def save(self, filename):
        """ Save settings to file """
        #if (self.Check_All_Variables() > 0):
        #    return
        if filename == '' or filename == ():
            return

        if os.path.isfile(filename):
            if not message_ask_ok_cancel("Replace", "Replace Exiting Configuration File?\n"+filename):
                self.__show_window__()
                return

        # open the file for write
        try:
            fout = open(filename, 'w')
        except:
            message_status_bar("Unable to open file for writing: %s" %(filename), 'red')
            return

        # serialize the data and write to file
        config_data = self.serialize()
        for line in config_data:
            try:
                fout.write(line+'\n')
            except:
                fout.write('(skipping line)\n')
                debug_message(traceback.format_exc())
        fout.close()

        message_status_bar("Configuration File Saved: %s" %(filename), 'white')

    def load(self, filename):
        if filename == '' or filename == ():
            return

        try:
            fin = open(filename, 'r')
        except:
            fmessage("Unable to open file: %s" %(filename))
            return

        # deserialize the settings from file
        self.deserialize(fin)
        self.__update_derived_variables__()
        fin.close()

    def serialize(self):
        header = []
        header.append('( K40 Whisperer Settings: '+WHISPERER_VERSION+' )')
        header.append('( by Scorch - 2017 )')
        header.append("(=========================================================)")
        # BOOL
        header.append('(k40_whisperer_set include_Reng  %s )' %(int(self.include_Reng.get())))
        header.append('(k40_whisperer_set include_Veng  %s )' %(int(self.include_Veng.get())))
        header.append('(k40_whisperer_set include_Vcut  %s )' %(int(self.include_Vcut.get())))
        header.append('(k40_whisperer_set halftone      %s )' %(int(self.halftone.get())))
        header.append('(k40_whisperer_set HomeUR        %s )' %(int(self.HomeUR.get())))
        # STRING.get()
        header.append('(k40_whisperer_set board_name    %s )' %(self.board_name.get()))
        header.append('(k40_whisperer_set units         %s )' %(self.units.get()))
        header.append('(k40_whisperer_set px2mm         %s )' %(self.px2mm.get()))
        header.append('(k40_whisperer_set Reng_feed     %s )' %(self.Reng_feed.get()))
        header.append('(k40_whisperer_set Veng_feed     %s )' %(self.Veng_feed.get()))
        header.append('(k40_whisperer_set Vcut_feed     %s )' %(self.Vcut_feed.get()))
        header.append('(k40_whisperer_set jog_step      %s )' %(self.jog_step.get()))
        header.append('(k40_whisperer_set rast_step     %s )' %(self.rast_step.get()))
        header.append('(k40_whisperer_set ht_size       %s )' %(self.ht_size.get()))
        header.append('(k40_whisperer_set LaserXsize    %s )' %(self.LaserXsize.get()))
        header.append('(k40_whisperer_set LaserYsize    %s )' %(self.LaserYsize.get()))
        header.append('(k40_whisperer_set gotoX         %s )' %(self.gotoX.get()))
        header.append('(k40_whisperer_set gotoY         %s )' %(self.gotoY.get()))
        header.append('(k40_whisperer_set bezier_M1     %s )' %(self.bezier_M1.get()))
        header.append('(k40_whisperer_set bezier_M2     %s )' %(self.bezier_M2.get()))
        header.append('(k40_whisperer_set bezier_weight %s )' %(self.bezier_weight.get()))
        header.append('(k40_whisperer_set t_timeout     %s )' %(self.t_timeout.get()))
        header.append('(k40_whisperer_set n_timeouts    %s )' %(self.n_timeouts.get()))
        header.append('(k40_whisperer_set jog_step      %s )' %(self.jog_step.get()))
        header.append('(k40_whisperer_set designfile    \042%s\042 )' %(self.DESIGN_FILE))
        header.append('(k40_whisperer_set inkscape_path \042%s\042 )' %(self.inkscape_path.get()))
        header.append("(=========================================================)")

        return header

    def deserialize(self, fin):
        """ Deserialize settings from a file """
        ident = "k40_whisperer_set"
        for line in fin:
            if ident in line:
                # BOOL
                if "include_Reng" in line:
                    self.include_Reng.set(line[line.find("include_Reng"):].split()[1])
                elif "include_Veng" in line:
                    self.include_Veng.set(line[line.find("include_Veng"):].split()[1])
                elif "include_Vcut" in line:
                    self.include_Vcut.set(line[line.find("include_Vcut"):].split()[1])
                elif "halftone" in line:
                    self.halftone.set(line[line.find("halftone"):].split()[1])
                elif "HomeUR" in line:
                    self.HomeUR.set(line[line.find("HomeUR"):].split()[1])

                # STRING.set()
                elif "board_name" in line:
                    self.board_name.set(line[line.find("board_name"):].split()[1])
                elif "units" in line:
                    self.units.set(line[line.find("units"):].split()[1])
                elif "px2mm" in line:
                    self.px2mm.set(line[line.find("px2mm"):].split()[1])
                elif "Reng_feed" in line:
                    self.Reng_feed.set(line[line.find("Reng_feed"):].split()[1])
                elif "Veng_feed" in line:
                    self.Veng_feed.set(line[line.find("Veng_feed"):].split()[1])
                elif "Vcut_feed" in line:
                    self.Vcut_feed.set(line[line.find("Vcut_feed"):].split()[1])
                elif "jog_step" in line:
                    self.jog_step.set(line[line.find("jog_step"):].split()[1])

                elif "rast_step" in line:
                    self.rast_step.set(line[line.find("rast_step"):].split()[1])
                elif "ht_size" in line:
                    self.ht_size.set(line[line.find("ht_size"):].split()[1])

                elif "LaserXsize" in line:
                    self.LaserXsize.set(line[line.find("LaserXsize"):].split()[1])
                elif "LaserYsize" in line:
                    self.LaserYsize.set(line[line.find("LaserYsize"):].split()[1])
                elif "gotoX" in line:
                    self.gotoX.set(line[line.find("gotoX"):].split()[1])
                elif "gotoY" in line:
                    self.gotoY.set(line[line.find("gotoY"):].split()[1])

                elif "bezier_M1" in line:
                    self.bezier_M1.set(line[line.find("bezier_M1"):].split()[1])
                elif "bezier_M2" in line:
                    self.bezier_M2.set(line[line.find("bezier_M2"):].split()[1])
                elif "bezier_weight" in line:
                    self.bezier_weight.set(line[line.find("bezier_weight"):].split()[1])

                elif "t_timeout" in line:
                    self.t_timeout.set(line[line.find("t_timeout"):].split()[1])
                elif "n_timeouts" in line:
                    self.n_timeouts.set(line[line.find("n_timeouts"):].split()[1])

                elif "designfile" in line:
                    self.DESIGN_FILE = (line[line.find("designfile"):].split("\042")[1])
                elif "inkscape_path" in line:
                    self.inkscape_path.set(line[line.find("inkscape_path"):].split("\042")[1])


    def show_general_settings_dialog(self):
        gen_settings = Toplevel(width=560, height=320)
        # Use grab_set to prevent user input in the main window during calculations
        gen_settings.grab_set()
        gen_settings.resizable(0, 0)
        gen_settings.title('Settings')
        gen_settings.iconname("Settings")

        try:
            gen_settings.iconbitmap(bitmap="@emblem64")
        except:
            debug_message(traceback.format_exc())

        D_Yloc = 6
        D_dY = 26
        xd_label_L = 12

        w_label = 130
        w_entry = 40
        w_units = 35
        xd_entry_L = xd_label_L+w_label+10
        xd_units_L = xd_entry_L+w_entry+5

        #Radio Button
        # units
        D_Yloc = D_Yloc+D_dY
        Label_Units = Label(gen_settings, text="Units")
        Label_Units.place(x=xd_label_L, y=D_Yloc, width=113, height=21)
        Radio_Units_IN = Radiobutton(gen_settings, text="inch", value="in", width="100", anchor=W)
        Radio_Units_IN.place(x=w_label+22, y=D_Yloc, width=75, height=23)
        Radio_Units_IN.configure(variable=self.units, command=self.Entry_units_var_Callback)
        Radio_Units_MM = Radiobutton(gen_settings, text="mm", value="mm", width="100", anchor=W)
        Radio_Units_MM.place(x=w_label+110, y=D_Yloc, width=75, height=23)
        Radio_Units_MM.configure(variable=self.units, command=self.Entry_units_var_Callback)

        # px to mm
        D_Yloc = D_Yloc+D_dY
        Label_px2mm = Label(gen_settings, text="px to mm ratio")
        Label_px2mm.place(x=xd_label_L, y=D_Yloc, width=113, height=21)
        Entry_px2mm = Entry(gen_settings, width="15")
        Entry_px2mm.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        Entry_px2mm.configure(textvariable=self.px2mm)
        self.px2mm.trace_variable("w", lambda v, i, n, uie=Entry_px2mm, func=self.Entry_px2mm_Check: self.entry_callback(uie, func, v, i, n))
        self.entry_set(Entry_px2mm, self.Entry_px2mm_Check(), 2)


        # timeout
        D_Yloc = D_Yloc+D_dY
        Label_Timeout = Label(gen_settings, text="USB Timeout")
        Label_Timeout.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        Label_Timeout_u = Label(gen_settings, text="ms", anchor=W)
        Label_Timeout_u.place(x=xd_units_L, y=D_Yloc, width=w_units, height=21)
        Entry_Timeout = Entry(gen_settings, width="15")
        Entry_Timeout.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        Entry_Timeout.configure(textvariable=self.t_timeout)
        self.t_timeout.trace_variable("w", lambda v, i, n, uie=Entry_Timeout, func=self.Entry_Timeout_Check: self.entry_callback(uie, func, v, i, n))
        self.entry_set(Entry_Timeout, self.Entry_Timeout_Check(), 2)

        # number of timeouts
        D_Yloc = D_Yloc+D_dY
        Label_N_Timeouts = Label(gen_settings, text="Number of Timeouts")
        Label_N_Timeouts.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        Entry_N_Timeouts = Entry(gen_settings, width="15")
        Entry_N_Timeouts.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        Entry_N_Timeouts.configure(textvariable=self.n_timeouts)
        self.n_timeouts.trace_variable("w", lambda v, i, n, uie=Entry_N_Timeouts, func=self.Entry_N_Timeouts_Check: self.entry_callback(uie, func, v, i, n))
        self.entry_set(Entry_N_Timeouts, self.Entry_N_Timeouts_Check(), 2)

        # Inskscape path
        D_Yloc = D_Yloc+D_dY
        font_entry_width = 215
        Label_Inkscape_Path = Label(gen_settings, text="Inkscape Executable")
        Label_Inkscape_Path.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        Entry_Inkscape_Path = Entry(gen_settings, width="15")
        Entry_Inkscape_Path.place(x=xd_entry_L, y=D_Yloc, width=font_entry_width, height=23)
        Entry_Inkscape_Path.configure(textvariable=self.inkscape_path)
        Inkscape_Path = Button(gen_settings, text="Find Inkscape")
        Inkscape_Path.place(x=xd_entry_L+font_entry_width+10, y=D_Yloc, width=110, height=23)
        Inkscape_Path.bind("<ButtonRelease-1>", self.Inkscape_Path_Click)

        # home location (TL, BR)
        D_Yloc = D_Yloc+D_dY
        Label_no_com = Label(gen_settings, text="Home in Upper Right")
        Label_no_com.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        Checkbutton_no_com = Checkbutton(gen_settings, text="", anchor=W)
        Checkbutton_no_com.place(x=xd_entry_L, y=D_Yloc, width=75, height=23)
        Checkbutton_no_com.configure(variable=self.HomeUR)
        self.HomeUR.trace_variable("w", self.menu_View_Refresh_Callback)

        # board name
        D_Yloc = D_Yloc+D_dY
        Label_Board_Name = Label(gen_settings, text="Board Name", anchor=CENTER)
        Board_Name_OptionMenu = OptionMenu(gen_settings, self.board_name, "LASER-M2", "LASER-M1", "LASER-M", "LASER-B2", "LASER-B1", "LASER-B", "LASER-A")
        Label_Board_Name.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        Board_Name_OptionMenu.place(x=xd_entry_L, y=D_Yloc, width=w_entry*3, height=23)

        Board_Name_OptionMenu['menu'].entryconfigure("LASER-M1", state="disabled")
        Board_Name_OptionMenu['menu'].entryconfigure("LASER-M", state="disabled")
        Board_Name_OptionMenu['menu'].entryconfigure("LASER-B2", state="disabled")
        Board_Name_OptionMenu['menu'].entryconfigure("LASER-B1", state="disabled")
        Board_Name_OptionMenu['menu'].entryconfigure("LASER-B", state="disabled")
        Board_Name_OptionMenu['menu'].entryconfigure("LASER-A", state="disabled")

        # laser area (width)
        D_Yloc = D_Yloc+D_dY
        Label_Laser_Area_Width = Label(gen_settings, text="Laser Area Width")
        Label_Laser_Area_Width.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        Label_Laser_Area_Width_u = Label(gen_settings, textvariable=self.units, anchor=W)
        Label_Laser_Area_Width_u.place(x=xd_units_L, y=D_Yloc, width=w_units, height=21)
        Entry_Laser_Area_Width = Entry(gen_settings, width="15")
        Entry_Laser_Area_Width.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        Entry_Laser_Area_Width.configure(textvariable=self.LaserXsize)
        self.LaserXsize.trace_variable("w", lambda v, i, n, uie=Entry_Laser_Area_Width, func=self.Entry_Laser_Area_Width_Check: self.entry_callback(uie, func, v, i, n))
        self.entry_set(Entry_Laser_Area_Width, self.Entry_Laser_Area_Width_Check(), 2)

        # laser area (height)
        D_Yloc = D_Yloc+D_dY
        Label_Laser_Area_Height = Label(gen_settings, text="Laser Area Height")
        Label_Laser_Area_Height.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        Label_Laser_Area_Height_u = Label(gen_settings, textvariable=self.units, anchor=W)
        Label_Laser_Area_Height_u.place(x=xd_units_L, y=D_Yloc, width=w_units, height=21)
        Entry_Laser_Area_Height = Entry(gen_settings, width="15")
        Entry_Laser_Area_Height.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        Entry_Laser_Area_Height.configure(textvariable=self.LaserYsize)
        self.LaserYsize.trace_variable("w", lambda v, i, n, uie=Entry_Laser_Area_Height, func=self.Entry_Laser_Area_Height_Check: self.entry_callback(uie, func, v, i, n))
        self.entry_set(Entry_Laser_Area_Height, self.Entry_Laser_Area_Height_Check(), 2)

        # save button
        D_Yloc = D_Yloc+D_dY+10
        Label_SaveConfig = Label(gen_settings, text="Configuration File")
        Label_SaveConfig.place(x=xd_label_L, y=D_Yloc, width=113, height=21)
        GEN_SaveConfig = Button(gen_settings, text="Save")
        GEN_SaveConfig.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=21, anchor="nw")
        GEN_SaveConfig.bind("<ButtonRelease-1>", self.Write_Config_File)

        ## Buttons ##
        gen_settings.update_idletasks()
        Ybut = int(gen_settings.winfo_height())-30
        Xbut = int(gen_settings.winfo_width()/2)
        GEN_Close = Button(gen_settings, text="Close", command=self.__close_window__)
        GEN_Close.place(x=Xbut, y=Ybut, width=130, height=30, anchor="center")

    def show_raster_settings_dialog(self):
        Wset = 425+280
        Hset = 330 #260
        self.raster_settings = Toplevel(width=Wset, height=Hset, name="raster_settings")
        self.raster_settings.grab_set() # Use grab_set to prevent user input in the main window during calculations
        self.raster_settings.resizable(0, 0)
        self.raster_settings.title('Raster Settings')
        self.raster_settings.iconname("Raster Settings")

        try:
            self.raster_settings.iconbitmap(bitmap="@emblem64")
        except:
            debug_message(traceback.format_exc())

        D_Yloc = 6
        D_dY = 24
        xd_label_L = 12
        w_label = 155
        w_entry = 60
        w_units = 35
        xd_entry_L = xd_label_L+w_label+10
        xd_units_L = xd_entry_L+w_entry+5

        D_Yloc = D_Yloc+D_dY
        label_Rstep = Label(self.raster_settings, text="Scanline Step", anchor=CENTER, name="label_Rstep")
        label_Rstep.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        label_Rstep_u = Label(self.raster_settings, text="in", anchor=W)
        label_Rstep_u.place(x=xd_units_L, y=D_Yloc, width=w_units, height=21)
        Entry_Rstep = Entry(self.raster_settings, width="15")
        Entry_Rstep.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        Entry_Rstep.configure(textvariable=self.rast_step)
        self.rast_step.trace_variable("w", lambda v, i, n, uie=Entry_Rstep, func=self.Entry_Rstep_Check: self.entry_callback(uie, func, v, i, n))

        D_Yloc = D_Yloc+D_dY
        label_Halftone = Label(self.raster_settings, text="Halftone")
        label_Halftone.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        Checkbutton_Halftone = Checkbutton(self.raster_settings, text=" ", anchor=W, command=self.Set_Input_States_RASTER)
        Checkbutton_Halftone.place(x=w_label+22, y=D_Yloc, width=75, height=23)
        Checkbutton_Halftone.configure(variable=self.halftone)
        self.halftone.trace_variable("w", self.Halftone_Callback)

        ############
        # group some UI elements so we can bulk show/hide them later on
        ############
        D_Yloc = D_Yloc+D_dY
        group = LabelFrame(self.raster_settings, name="group", borderwidth=0, relief="flat")
        group.place(x=0, y=D_Yloc, width=Wset-280-20, height=200)
        #group.pack(padx=10)

        ############
        D_Yloc = 0 #D_Yloc+D_dY
        label_Halftone_DPI = Label(group, name="label_Halftone_DPI", text="Halftone Resolution", anchor=CENTER)
        label_Halftone_DPI.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        halftone_DPI_OptionMenu = OptionMenu(group, self.ht_size, "1000", "500", "333", "250", "200", "167", "143", "125")
        halftone_DPI_OptionMenu.place(x=xd_entry_L, y=D_Yloc, width=w_entry+30, height=23)

        label_Halftone_u = Label(group, name="label_Halftone_u", text="dpi", anchor=W)
        label_Halftone_u.place(x=xd_units_L+30, y=D_Yloc, width=w_units, height=21)

        #D_Yloc=D_Yloc+D_dY+5
        #self.Label_bezier_weight.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        #self.Entry_bezier_weight   = Entry(raster_settings,width="15")
        #self.Entry_bezier_weight.place(x=xd_entry_L, y=D_Yloc, width=w_entry, height=23)
        #self.Entry_bezier_weight.configure(textvariable=self.bezier_weight)
        #self.bezier_weight.trace_variable("w", self.Entry_bezier_weight_Callback)

        ############
        D_Yloc = D_Yloc+D_dY+5
        label_bezier_M1 = Label(group, name="label_bezier_M1", text="Slope, Black (%.1f)"%(self.bezier_M1_default), anchor=CENTER)
        bezier_M1_Slider = Scale(group, name="bezier_M1_Slider", from_=1, to=50, resolution=0.1, orient=HORIZONTAL, variable=self.bezier_M1)
        bezier_M1_Slider.place(x=xd_entry_L, y=D_Yloc, width=(Wset-xd_entry_L-25-280))
        D_Yloc = D_Yloc+21
        label_bezier_M1.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.bezier_M1.trace_variable("w", self.bezier_M1_Callback)

        D_Yloc = D_Yloc+D_dY-8
        label_bezier_M2 = Label(group, name="label_bezier_M2", text="Slope, White (%.2f)"%(self.bezier_M2_default), anchor=CENTER)
        bezier_M2_Slider = Scale(group, name="bezier_M2_Slider", from_=0.0, to=1, orient=HORIZONTAL, resolution=0.01, variable=self.bezier_M2)
        bezier_M2_Slider.place(x=xd_entry_L, y=D_Yloc, width=(Wset-xd_entry_L-25-280))
        D_Yloc = D_Yloc+21
        label_bezier_M2.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.bezier_M2.trace_variable("w", self.bezier_M2_Callback)

        D_Yloc = D_Yloc+D_dY-8
        label_bezier_weight = Label(group, name="label_bezier_weight", text="Transition (%.1f)"%(self.bezier_M1_default), anchor=CENTER)
        bezier_weight_Slider = Scale(group, name="bezier_weight_Slider", from_=0, to=10, resolution=0.1, orient=HORIZONTAL, variable=self.bezier_weight)
        bezier_weight_Slider.place(x=xd_entry_L, y=D_Yloc, width=(Wset-xd_entry_L-25-280))
        D_Yloc = D_Yloc+21
        label_bezier_weight.place(x=xd_label_L, y=D_Yloc, width=w_label, height=21)
        self.bezier_weight.trace_variable("w", self.bezier_weight_Callback)


        # Bezier Canvas
        Bezier_frame = Frame(self.raster_settings, bd=1, relief=SUNKEN)
        Bezier_frame.place(x=Wset-280, y=10, height=265, width=265)
        self.BezierCanvas = Canvas(Bezier_frame, background="white")
        self.BezierCanvas.pack(side=LEFT, fill=BOTH, expand=1)
        self.BezierCanvas.create_line(5, 260-0, 260, 260-255, fill="grey", capstyle="round", width=2, tags='perm')

        M1 = self.bezier_M1_default
        M2 = self.bezier_M2_default
        w = self.bezier_weight_default
        num = 10
        x, y = self.generate_bezier(M1, M2, w, n=num)
        for i in range(0, num):
            self.BezierCanvas.create_line(5+x[i], 260-y[i], 5+x[i+1], 260-y[i+1], fill="lightgrey", stipple='gray25', capstyle="round", width=2, tags='perm')

        ## Buttons ##
        self.raster_settings.update_idletasks()
        Ybut = int(self.raster_settings.winfo_height())-30
        Xbut = int(self.raster_settings.winfo_width()/2)

        RASTER_Close = Button(self.raster_settings, text="Close", command=self.__close_window__)
        RASTER_Close.place(x=Xbut, y=Ybut, width=130, height=30, anchor="center")

        self.bezier_M1_Callback()
        self.Set_Input_States_RASTER()

    ##########################################################################
    # UI Events
    ##########################################################################
    def Write_Config_File(self, event):
        config_file = "k40_whisperer.txt"
        configname_full = self.HOME_DIR + "/" + config_file
        self.save(configname_full)

    #############################
    def Inkscape_Path_Click(self, event):
        newfontdir = askopenfilename(filetypes=[("Executable Files", ("inkscape.exe", "*inkscape*")), ("All Files", "*")], initialdir=self.inkscape_path.get())
        if newfontdir != "" and newfontdir != ():
            self.inkscape_path.set(newfontdir.encode("utf-8"))
        self.__show_window__()

    #############################
    def Entry_units_var_Callback(self):
        if (self.units.get() == 'in') and (self.funits.get() == 'mm/s'):
            self.Scale_Linear_Inputs('in')
            self.funits.set('in/min')
        elif (self.units.get() == 'mm') and (self.funits.get() == 'in/min'):
            self.Scale_Linear_Inputs('mm')
            self.funits.set('mm/s')

    def Scale_Linear_Inputs(self, new_units=None):
        if new_units == 'in':
            self.units_scale = 1.0
            factor = 1/25.4
            vfactor = 60.0/25.4
        elif new_units == 'mm':
            factor = 25.4
            vfactor = 25.4/60.0
            self.units_scale = 25.4
        else:
            return

        self.LaserXsize.set('%.3f' %(float(self.LaserXsize.get())*factor))
        self.LaserYsize.set('%.3f' %(float(self.LaserYsize.get())*factor))
        self.jog_step.set('%.3g' %(float(self.jog_step.get())*factor))
        self.gotoX.set('%.3f' %(float(self.gotoX.get())*factor))
        self.gotoY.set('%.3f' %(float(self.gotoY.get())*factor))
        self.Reng_feed.set('%.3g' %(float(self.Reng_feed.get())*vfactor))
        self.Veng_feed.set('%.3g' %(float(self.Veng_feed.get())*vfactor))
        self.Vcut_feed.set('%.3g' %(float(self.Vcut_feed.get())*vfactor))

    #############################
    def menu_View_Refresh_Callback(self, varName, index, mode):
        pass
    def Entry_px2mm_Check(self):
        return self.entry_check_var_float_greater_than_0(self.px2mm, "px to mm")
    def Entry_Timeout_Check(self):
        return self.entry_check_var_float_greater_than_0(self.t_timeout, "Timeout")
    def Entry_N_Timeouts_Check(self):
        return self.entry_check_var_float_greater_than_0(self.n_timeouts, "N_Timeouts")
    def Entry_Laser_Area_Width_Check(self):
        return self.entry_check_var_float_greater_than_0(self.LaserXsize, "Width")
    def Entry_Laser_Area_Height_Check(self):
        return self.entry_check_var_float_greater_than_0(self.LaserYsize, "Height")
    def Entry_Rstep_Check(self):
        return self.entry_check_number_limits(self.get_raster_step_1000in(), "Step", limit1=0.0, expr1=">=", limit2="63", expr2="<=")
    def Halftone_Callback(self, varName, index, mode):
        # TODO: verify this is not needed (SCALE=0)
        #self.SCALE = 0
        pass
    def bezier_weight_Callback(self, varName=None, index=None, mode=None):
        self.bezier_plot()
    def bezier_M1_Callback(self, varName=None, index=None, mode=None):
        self.bezier_plot()
    def bezier_M2_Callback(self, varName=None, index=None, mode=None):
        self.bezier_plot()
    def Entry_Reng_feed_Check(self):
        return self.entry_check_var_float_greater_than_0(self.Reng_feed, "Feed Rate")
    def Entry_Veng_feed_Check(self):
        return self.entry_check_var_float_greater_than_0(self.Veng_feed, "Feed Rate")
    def Entry_Vcut_feed_Check(self):
        return self.entry_check_var_float_greater_than_0(self.Vcut_feed, "Feed Rate")
    def Entry_Step_Check(self):
        return self.entry_check_var_float_greater_than_0(self.jog_step, "Step")
    def Entry_GoToX_Check(self):
        if self.HomeUR.get():
            return self.entry_check_var_limits(self.gotoX, "Value", valtype="float", limit1=0.0, expr1="<=")
        #else:
        return self.entry_check_var_limits(self.gotoX, "Value", valtype="float", limit1=0.0, expr1=">=")
    def Entry_GoToY_Check(self):
        return self.entry_check_var_limits(self.gotoY, "Value", valtype="float", limit1=0.0, expr1="<=")

    ##########################################################################


    ##########################################################################
    # Helper functions
    ##########################################################################
    __expr_to_str__ = {
        "<" : " should be less than ",
        "<=" : " should be less than or equal to ",
        ">" : " should be greater than ",
        ">=" : " should be greater than or equal to ",
        "==" : " should be equal to ",
        "!=" : " should be not equal to "
    }

    def entry_check_number_limits(self, val, friendly_name, limit1=0.0, expr1=">", limit2=sys.maxint, expr2="<"):
        try:
            #ast.literal_eval?
            if eval(str(val) + " " + expr1 + " " + str(limit1)) is False:
                message_status_bar(" " + friendly_name + self.__expr_to_str__[expr1] + str(limit1) + " ", 'red')
                return 2 # Value is invalid number
            if eval(str(val) + " " + expr2 + " " + str(limit2)) is False:
                message_status_bar(" " + friendly_name + self.__expr_to_str__[expr2] + str(limit2) + " ", 'red')
                return 2 # Value is invalid number
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number

    def entry_check_var_limits(self, var, friendly_name, valtype="float", limit1=0.0, expr1=">", limit2=sys.maxint, expr2="<"):
        try:
            val = eval(valtype+'('+var.get()+')')
            return self.entry_check_number_limits(val, friendly_name, limit1, expr1, limit2, expr2)
        except:
            return 3     # Value not a number
        return 0         # Value is a valid number

    def entry_check_var_float_greater_than_0(self, var, var_friendly_name):
        return self.entry_check_var_limits(var, var_friendly_name, valtype="float", limit1=0.0, expr1=">")

    def entry_callback(self, uielement, check_function, varName, index, mode):
        return self.entry_set(uielement, check_function(), new=1)

    def entry_set(self, val2, calc_flag=0, new=0):
        if calc_flag == 0 and new == 0:
            try:
                val2.configure(bg='yellow')
                message_status_bar(" Recalculation required.", 'yellow')
            except:
                pass
        elif calc_flag == 3:
            try:
                val2.configure(bg='red')
                message_status_bar(" Value should be a number. ", 'red')
            except:
                pass
        elif calc_flag == 2:
            try:
                val2.configure(bg='red')
                message_status_bar(" ", 'red')
            except:
                pass
        elif (calc_flag == 0 or calc_flag == 1) and new == 1:
            try:
                val2.configure(bg='white')
                message_status_bar(" ", 'white')
            except:
                pass
        elif (calc_flag == 1) and new == 0:
            try:
                val2.configure(bg='white')
                message_status_bar(" ", 'white')
            except:
                pass
        elif (calc_flag == 0 or calc_flag == 1) and new == 2:
            return 0
        return 1

    def bezier_plot(self):
        if self.BezierCanvas.winfo_exists() == 0:
            return

        self.BezierCanvas.delete('bez')

        #self.BezierCanvas.create_line( 5,260-0,260,260-255,fill="black", capstyle="round", width = 2, tags='bez')
        M1 = float(self.bezier_M1.get())
        M2 = float(self.bezier_M2.get())
        w = float(self.bezier_weight.get())
        num = 10
        x, y = self.generate_bezier(M1, M2, w, n=num)
        for i in range(0, num):
            self.BezierCanvas.create_line(5+x[i], 260-y[i], 5+x[i+1], 260-y[i+1], fill="black", capstyle="round", width=2, tags='bez')
        self.BezierCanvas.create_text(128, 0, text="Output Level vs. Input Level", anchor="n", tags='bez')

    def get_raster_step_1000in(self):
        val_in = float(self.rast_step.get())
        value = int(round(val_in*1000.0, 1))
        return value

    def generate_bezier(self, M1, M2, w, n=100):
        if M1 == M2:
            x1 = 0
            y1 = 0
        else:
            x1 = 255*(1-M2)/(M1-M2)
            y1 = M1*x1
        x = []
        y = []
        # Calculate Bezier Curve
        for step in range(0, n+1):
            t = float(step)/float(n)
            Ct = 1 / (pow(1-t, 2) + 2 * (1-t) * t * w + pow(t, 2))
            #x0 = 0
            #y0 = 0
            #x2 = 255
            #y2 = 255
            #x.append( Ct*( pow(1-t,2)*x0+2*(1-t)*t*w*x1+pow(t,2)*x2) )
            #y.append( Ct*( pow(1-t,2)*y0+2*(1-t)*t*w*y1+pow(t,2)*y2) )
            x.append(Ct*(2 * (1-t) * t * w * x1 + pow(t, 2) * 255))
            y.append(Ct*(2 * (1-t) * t * w * y1 + pow(t, 2) * 255))
        return x, y

    # def Set_Input_States(self):
    #     pass

    # def Set_Input_States_Event(self, event):
    #     self.Set_Input_States()

    def Set_Input_States_RASTER(self):
        if self.halftone.get():
            newstate = "normal"
        else:
            newstate = "disabled"

        group = self.raster_settings.nametowidget("group")
        for c in group.winfo_children():
            try:
                c.configure(state=newstate)
            except:
                pass

    # def Set_Input_States_RASTER_Event(self, event):
    #     self.Set_Input_States_RASTER()

    def __show_window__(self):
        try:
            win_id = get_app().grab_current()
            win_id.withdraw()
            win_id.deiconify()
        except:
            pass

    def __close_window__(self):
        win_id = get_app().grab_current()
        win_id.destroy()
