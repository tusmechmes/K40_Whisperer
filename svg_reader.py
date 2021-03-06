#!/usr/bin/env python
'''
Copyright (C) 2017 Scorch www.scorchworks.com
Derived from dxf_outlines.py by Aaron Spike and Alvin Penner

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''
# pylint: disable=line-too-long
# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=unused-wildcard-import
# pylint: disable=wildcard-import
# pylint: disable=bare-except
# pylint: disable=no-self-use
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-statements
# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
# pylint: disable=too-many-public-methods
# pylint: disable=too-many-branches

# standard library
import os
import tempfile
import shutil
from subprocess import Popen, PIPE
import re
from threading import Timer

# local library
from globals import *
import inkex
import simplestyle
import simpletransform
import cubicsuperpath
import cspsubdiv

from PIL import Image

try:
    inkex.localize()
except:
    print "localize failed"

## Subprocess timout stuff ######
def run_external(cmd, timeout_sec):
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
    kill_proc = lambda p: p.kill()
    timer = Timer(timeout_sec, kill_proc, [proc])
    try:
        timer.start()
        proc.communicate()
    finally:
        timer.cancel()
##################################

class SVG_TEXT_EXCEPTION(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class SVG_READER(inkex.Effect):
#class SVG_READER:
    def __init__(self, settings):
        inkex.Effect.__init__(self)
        self.flatness = 0.01
        self.image_dpi = 1000
        self.inscape_exe_list = []
        self.inscape_exe_list.append("C:\\Program Files\\Inkscape\\inkscape.exe")
        self.inscape_exe_list.append("C:\\Program Files (x86)\\Inkscape\\inkscape.exe")
        self.inscape_exe_list.append("/usr/bin/inkscape")
        self.inscape_exe_list.append("/usr/local/bin/inkscape")
        self.inscape_exe_list.append("/Applications/Inkscape.app/Contents/Resources/bin/inkscape")
        self.inscape_exe = None
        self.lines = []
        self.Cut_Type = {}
        self.Xsize = 40
        self.Ysize = 40
        self.raster = True

        self.raster_PIL = None
        self.cut_lines = []
        self.eng_lines = []

        self.png_area = "--export-area-page"
        self.timout = 60 #timeout time for external calls to Inkscape in seconds

        self.layers = ['0']
        self.layer = '0'
        self.layernames = []
        self.txt2paths = False
        self.groupmat = []

        self.settings = settings
        self.set_inkscape_path(settings.inkscape_path.get())

        # TODO: add a "use_depth_info" to the settings, if it is set use a different color conversion
        self.use_depth_info = USE_DEPTH_INFO

    def set_inkscape_path(self, PATH):
        if PATH != None:
            self.inscape_exe_list.insert(0, PATH)
        for location in self.inscape_exe_list:
            if os.path.isfile(location):
                self.inscape_exe = location
                break

    def px_to_mm(self, node):
        sval = str(node)
        if sval[(len(sval)-2):(len(sval))] == 'px':
            nval = float(sval[0:(len(sval)-2)])
            nval = nval * float(self.settings.px2mm.get())
            node._parent.set(node.attrname, str(nval) + 'mm')

    def fix_svg_coords(self):
        # x y width height
        self.px_to_mm(self.document.getroot().xpath('@x', namespaces=inkex.NSS)[0])
        self.px_to_mm(self.document.getroot().xpath('@y', namespaces=inkex.NSS)[0])
        self.px_to_mm(self.document.getroot().xpath('@width', namespaces=inkex.NSS)[0])
        self.px_to_mm(self.document.getroot().xpath('@height', namespaces=inkex.NSS)[0])

    def colmod(self, r, g, b, path_id):
        if self.use_depth_info:
            if (r == 0) and (g == 0) and (b == 0):
                self.Cut_Type[path_id] = "raster"
            if (g == 0) and (b == 0):
                # limit the range of gradients to 100
                if r < 100:
                    r = 100 # can't engrave less than 0% mm
                if r > 200:
                    r = 255 # minimum speed!
                self.Cut_Type[path_id] = "cut"
            elif (r == 0) and (g == 0):
                # limit the range of gradients to 100
                if b < 100:
                    b = 100 # can't engrave less than 0% mm
                if b > 200:
                    b = 255 # minimum speed!
                self.Cut_Type[path_id] = "engrave"
            else:
                self.Cut_Type[path_id] = "raster"
        else:
            delta = 10
            #if (r,g,b) ==(255,0,0):
            if (r >= 255-delta) and (g <= delta) and (b <= delta):
                self.Cut_Type[path_id] = "cut"
                (r, g, b) = (255, 0, 0)
            #elif (r,g,b)==(0,0,255):
            elif (r <= delta) and (g <= delta) and (b >= 255-delta):
                self.Cut_Type[path_id] = "engrave"
                (r, g, b) = (0, 0, 255)
            else:
                self.Cut_Type[path_id] = "raster"

        return '%02x%02x%02x' % (r, g, b)

    def process_shape(self, node, mat):
        rgb = "000000"

        # set default id if it's not specified, this fixes a bug where all elements resulted with the latest cut_type found
        path_id = node.get('id', str(node.__hash__()))
        style = node.get('style')
        self.Cut_Type[path_id] = "raster" # Set default type to raster

        #color_props_fill = ('fill', 'stop-color', 'flood-color', 'lighting-color')
        #color_props_stroke = ('stroke',)
        #color_props = color_props_fill + color_props_stroke

        #####################################################
        ## The following is ripped off from Coloreffect.py ##
        #####################################################
        if style:
            declarations = style.split(';')
            i_sw = -1
            sw_flag = False
            sw_prop = 'stroke-width'
            for i, decl in enumerate(declarations):
                parts = decl.split(':', 2)
                if len(parts) == 2:
                    (prop, col) = parts
                    prop = prop.strip().lower()
                    #if prop in color_props:
                    if prop == sw_prop:
                        i_sw = i
                    if prop == 'stroke':
                        col = col.strip()
                        if simplestyle.isColor(col):
                            c = simplestyle.parseColor(col)
                            rgb = self.colmod(c[0], c[1], c[2], path_id)
                            new_val = '#' + rgb
                        else:
                            new_val = col
                        if new_val != col:
                            declarations[i] = prop + ':' + new_val
                            sw_flag = True
            if sw_flag is True:
                if node.tag == inkex.addNS('text', 'svg'):
                    if self.txt2paths is False:
                        raise SVG_TEXT_EXCEPTION("SVG File with Color Coded Text Outlines Found: (i.e. Blue: engrave/ Red: cut)")
                    else:
                        line1 = "SVG File with color coded text outlines found (i.e. Blue: engrave/ Red: cut)."
                        line2 = "Automatic conversion to paths failed: Try upgrading to Inkscape .90 or later"
                        line3 = "To convert manually in Inkscape: select the text then select \"Path\"-\"Object to Path\" in the menu bar."

                        raise StandardError("%s\n\n%s\n\n%s" %(line1, line2, line3))

                if i_sw != -1:
                    declarations[i_sw] = sw_prop + ':' + "0.0"
                else:
                    declarations.append(sw_prop + ':' + "0.0")
            node.set('style', ';'.join(declarations))

        #####################################################

        if node.tag == inkex.addNS('path', 'svg'):
            d = node.get('d')
            if not d:
                return
            p = cubicsuperpath.parsePath(d)

        elif node.tag == inkex.addNS('line', 'svg'):
            x1 = 0.0
            y1 = 0.0
            x2 = 0.0
            y2 = 0.0
            if node.get('x1'):
                x1 = float(node.get('x1'))
            if node.get('y1'):
                y1 = float(node.get('y1'))
            if node.get('x2'):
                x2 = float(node.get('x2'))
            if node.get('y2'):
                y2 = float(node.get('y2'))

            d = "M {0},{1} {2},{3}".format(x1, y1, x2, y2)
            p = cubicsuperpath.parsePath(d)

        elif node.tag == inkex.addNS('rect', 'svg'):
            # note: x and y could be implicitly set to the top left of the canvas and then they are not added as attributes.
            x = 0.0
            y = 0.0
            if node.get('x'):
                x = float(node.get('x'))
            if node.get('y'):
                y = float(node.get('y'))
            width = float(node.get('width'))
            height = float(node.get('height'))
            #d = "M %f,%f %f,%f %f,%f %f,%f Z" %(x,y, x+width,y,  x+width,y+height, x,y+height)
            #p = cubicsuperpath.parsePath(d)
            rx = 0.0
            ry = 0.0
            if node.get('rx'):
                rx = float(node.get('rx'))
            if node.get('ry'):
                ry = float(node.get('ry'))

            if max(rx, ry) > 0.0:
                if rx == 0.0 or ry == 0.0:
                    rx = max(rx, ry)
                    ry = rx
                # pylint: disable=C0326
                L1 = "M %f,%f %f,%f "      %(x+rx       , y          , x+width-rx , y          )
                C1 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x+width    , y+ry       )
                L2 = "M %f,%f %f,%f "      %(x+width    , y+ry       , x+width    , y+height-ry)
                C2 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x+width-rx , y+height   )
                L3 = "M %f,%f %f,%f "      %(x+width-rx , y+height   , x+rx       , y+height   )
                C3 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x          , y+height-ry)
                L4 = "M %f,%f %f,%f "      %(x          , y+height-ry, x          , y+ry       )
                C4 = "A %f,%f 0 0 1 %f,%f" %(rx         , ry         , x+rx       , y          )
                d = L1 + C1 + L2 + C2 + L3 + C3 + L4 + C4
            else:
                d = "M %f,%f %f,%f %f,%f %f,%f Z" %(x, y, x+width, y, x+width, y+height, x, y+height)
            p = cubicsuperpath.parsePath(d)

        elif node.tag == inkex.addNS('circle', 'svg'):
            cx = float(node.get('cx'))
            cy = float(node.get('cy'))
            r = float(node.get('r'))
            d = "M %f,%f A   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f Z" %(cx+r, cy, r, r, cx, cy+r, r, r, cx-r, cy, r, r, cx, cy-r, r, r, cx+r, cy)
            p = cubicsuperpath.parsePath(d)

        elif node.tag == inkex.addNS('ellipse', 'svg'):
            cx = float(node.get('cx'))
            cy = float(node.get('cy'))
            rx = float(node.get('rx'))
            ry = float(node.get('ry'))
            d = "M %f,%f A   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f   %f,%f 0 0 1 %f,%f Z" %(cx+rx, cy, rx, ry, cx, cy+ry, rx, ry, cx-rx, cy, rx, ry, cx, cy-ry, rx, ry, cx+rx, cy)
            p = cubicsuperpath.parsePath(d)

        elif (node.tag == inkex.addNS('polygon', 'svg')) or (node.tag == inkex.addNS('polyline', 'svg')):
            points = node.get('points')
            if not points:
                return
            points = points.strip().split(" ")
            points = map(lambda x: x.split(","), points)
            d = "M "
            for point in points:
                if point[0] != '' and point[1] != '':
                    x = float(point[0])
                    y = float(point[1])
                    d = d + "%f,%f " %(x, y)

            #Close the loop if it is a ploygon
            if node.tag == inkex.addNS('polygon', 'svg'):
                d = d + "Z"
            p = cubicsuperpath.parsePath(d)

        else:
            return

        trans = node.get('transform')
        if trans:
            mat = simpletransform.composeTransform(mat, simpletransform.parseTransform(trans))
        simpletransform.applyTransformToPath(mat, p)

        ###################################################
        ## Break Curves down into small lines
        ###################################################
        f = self.flatness
        is_flat = 0
        while is_flat < 1:
            try:
                cspsubdiv.cspsubdiv(p, f)
                is_flat = 1
            except IndexError:
                break
            except:
                f += 0.1
                if f > 2:
                    break
                    #something has gone very wrong.
        ###################################################
        for sub in p:
            for i in range(len(sub)-1):
                x1 = sub[i][1][0]
                y1 = sub[i][1][1]
                x2 = sub[i+1][1][0]
                y2 = sub[i+1][1][1]
                self.lines.append([x1, y1, x2, y2, int(rgb, 16), path_id])

    def process_clone(self, node):
        trans = node.get('transform')
        x = node.get('x')
        y = node.get('y')
        mat = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
        if trans:
            mat = simpletransform.composeTransform(mat, simpletransform.parseTransform(trans))
        if x:
            mat = simpletransform.composeTransform(mat, [[1.0, 0.0, float(x)], [0.0, 1.0, 0.0]])
        if y:
            mat = simpletransform.composeTransform(mat, [[1.0, 0.0, 0.0], [0.0, 1.0, float(y)]])
        # push transform
        if trans or x or y:
            self.groupmat.append(simpletransform.composeTransform(self.groupmat[-1], mat))
        # get referenced node
        refid = node.get(inkex.addNS('href', 'xlink'))
        refnode = self.getElementById(refid[1:])
        if refnode is not None:
            if refnode.tag == inkex.addNS('g', 'svg'):
                self.process_group(refnode)
            elif refnode.tag == inkex.addNS('use', 'svg'):
                self.process_clone(refnode)
            else:
                self.process_shape(refnode, self.groupmat[-1])
        # pop transform
        if trans or x or y:
            self.groupmat.pop()

    def process_group(self, group):
        if group.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
            style = group.get('style')
            if style:
                style = simplestyle.parseStyle(style)
                if style.has_key('display'):
                    if style['display'] == 'none':
                        return
            layer = group.get(inkex.addNS('label', 'inkscape'))

            layer = layer.replace(' ', '_')
            if layer in self.layers:
                self.layer = layer
        trans = group.get('transform')
        if trans:
            self.groupmat.append(simpletransform.composeTransform(self.groupmat[-1], simpletransform.parseTransform(trans)))
        for node in group:
            if node.tag == inkex.addNS('g', 'svg'):
                self.process_group(node)
            elif node.tag == inkex.addNS('use', 'svg'):
                self.process_clone(node)
            else:
                self.process_shape(node, self.groupmat[-1])
        if trans:
            self.groupmat.pop()

    def unit2mm(self, string):
        # Returns mm given a string representation of units in another system
        # a dictionary of unit to user unit conversion factors
        uuconv = {'in': 25.4,
                  'pt': 25.4 / 72.0,
                  #'px': 25.4 / self.inkscape_dpi,
                  'mm': 1.0,
                  'cm': 10.0,
                  'm' : 1000.0,
                  'km': 1000.0 * 1000.0,
                  'pc': 25.4 / 6.0,
                  'yd': 25.4 * 12 * 3,
                  'ft': 25.4 * 12}

        unit = re.compile('(%s)$' % '|'.join(uuconv.keys()))
        param = re.compile(r'(([-+]?[0-9]+(\.[0-9]*)?|[-+]?\.[0-9]+)([eE][-+]?[0-9]+)?)')

        p = param.match(string)
        u = unit.search(string)
        if p:
            retval = float(p.string[p.start():p.end()])
        else:
            inkex.errormsg("Size was not determined returning zero value")
            retval = 0.0
        if u:
            retunit = u.string[u.start():u.end()]
        else:
            raise StandardError

        try:
            return retval * uuconv[retunit]
        except KeyError:
            return retval

    def Make_PNG(self):
        #create OS temp folder
        tmp_dir = tempfile.mkdtemp()

        if self.inscape_exe != None:
            try:
                svg_temp_file = os.path.join(tmp_dir, "k40w_temp.svg")
                png_temp_file = os.path.join(tmp_dir, "k40w_image.png")

                dpi = "%d" %(self.image_dpi)
                self.document.write(svg_temp_file)
                cmd = [self.inscape_exe, self.png_area, "--export-dpi", dpi, \
                        "--export-background", "rgb(255, 255, 255)", "--export-background-opacity", \
                        "255", "--export-png", png_temp_file, svg_temp_file]
                run_external(cmd, self.timout)
            except:
                raise StandardError("Inkscape Execution Failed.")
            self.raster_PIL = Image.open(png_temp_file)
            self.raster_PIL = self.raster_PIL.convert("L")
        else:
            raise StandardError("Inkscape Not found.")
        try:
            shutil.rmtree(tmp_dir)
        except:
            raise StandardError("Temp dir failed to delete:\n%s" %(tmp_dir))

    def convert_text2paths(self):
        #create OS temp folder
        tmp_dir = tempfile.mkdtemp()
        if self.inscape_exe != None:
            try:
                svg_temp_file = os.path.join(tmp_dir, "k40w_temp.svg")
                txt2path_file = os.path.join(tmp_dir, "txt2path.svg")
                self.document.write(svg_temp_file)
                cmd = [self.inscape_exe, "--export-text-to-path", "--export-plain-svg", txt2path_file, svg_temp_file]
                run_external(cmd, self.timout)
                self.document.parse(txt2path_file)
            except:
                raise StandardError("Inkscape Execution Failed.")
        else:
            raise StandardError("Inkscape Not found.")
        try:
            shutil.rmtree(tmp_dir)
        except:
            raise StandardError("Temp dir failed to delete:\n%s" %(tmp_dir))

    def make_paths(self, txt2paths=False):
        self.txt2paths = txt2paths

##        self.inkscape_dpi = None
##        try:
##            Inkscape_Version = self.document.getroot().xpath('@inkscape:version', namespaces=inkex.NSS)[0].split(" ")[0]
##        except:
##            Inkscape_Version = None
##
##        if Inkscape_Version <= .91:
##            self.inkscape_dpi = 90.0
##        else:
##            self.inkscape_dpi = 96.0

        if self.txt2paths:
            try:
                self.convert_text2paths()
            except:
                raise StandardError("Convert Text to Path Failed")

        try:
            h_mm = self.unit2mm(self.document.getroot().xpath('@height', namespaces=inkex.NSS)[0])
            w_mm = self.unit2mm(self.document.getroot().xpath('@width', namespaces=inkex.NSS)[0])
        except:
            line1 = "Units not set in SVG File.\n"
            line2 = "In Inkscape select 'File'-'Document Properties'."
            line3 = "In the 'Custom Size' region on the 'Page' tab set the 'Units' to 'mm' or 'in')"
            raise StandardError("%s\n%s\n%s" %(line1, line2, line3))

        try:
            view_box_str = self.document.getroot().xpath('@viewBox', namespaces=inkex.NSS)[0]
            view_box_list = view_box_str.split(' ')
            Wpix = float(view_box_list[2])
            Hpix = float(view_box_list[3])
            scale_h = h_mm/Hpix
            scale_w = w_mm/Wpix
            Dx = float(view_box_list[0]) * scale_w
            Dy = float(view_box_list[1]) * scale_h
        except:
            line1 = "Cannot determine SVG scale (SVG Viewox Missing).\n"
            line2 = "In Inkscape (v0.92) select 'File'-'Document Properties'."
            line3 = "In the 'Scale' region on the 'Page' tab change the 'Scale x:' value"
            line4 = "and press enter. Changing the value will add the Viewbox attribute."
            line5 = "The 'Scale x:' can then be changed back to the original value."
            ##if self.inkscape_dpi==None:
            raise StandardError("%s\n%s\n%s\n%s\n%s" %(line1, line2, line3, line4, line5))

##            print "Using guessed dpi value of: ",self.inkscape_dpi
##            scale_h = 25.4/self.inkscape_dpi
##            scale_w = 25.4/self.inkscape_dpi
##            Dx = 0
##            Dy = 0

        if abs(1.0-scale_h/scale_w) > 0.01:
            line1 = "SVG Files with different scales in X and Y are not supported.\n"
            line2 = "In Inkscape (v0.92): 'File'-'Document Properties'"
            line3 = "on the 'Page' tab adjust 'Scale x:' in the 'Scale' section"
            raise StandardError("%s\n%s\n%s" %(line1, line2, line3))

        for node in self.document.getroot().xpath('//svg:g', namespaces=inkex.NSS):
            if node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer':
                layer = node.get(inkex.addNS('label', 'inkscape'))
                self.layernames.append(layer.lower())
                layer = layer.replace(' ', '_')
                if layer and not layer in self.layers:
                    self.layers.append(layer)

        # pylint: disable=C0326
        self.groupmat = [[[scale_w,    0.0,  0.0-Dx],
                          [0.0  , -scale_h, h_mm+Dy]]]
        #doc = self.document.getroot()
        self.process_group(self.document.getroot())

        #################################################
        #msg = msg + "Height(mm)= %f\n" %(h_mm)
        #msg = msg + "Width (mm)= %f\n" %(w_mm)
        #inkex.errormsg(_(msg))

##        if not self.raster:
##            xmin= self.lines[0][0]+0.0
##            xmax= self.lines[0][0]+0.0
##            ymin= self.lines[0][1]+0.0
##            ymax= self.lines[0][1]+0.0
##            for line in self.lines:
##                x1= line[0]
##                y1= line[1]
##                x2= line[2]
##                y2= line[3]
##                xmin = min(min(xmin,x1),x2)
##                ymin = min(min(ymin,y1),y2)
##                xmax = max(max(xmax,x1),x2)
##                ymax = max(max(ymax,y1),y2)
##        else:
        xmin = 0.0
        xmax = w_mm
        ymin = -h_mm
        ymax = 0.0
        self.Make_PNG()

        self.Xsize = xmax-xmin
        self.Ysize = ymax-ymin
        Xcorner = xmin
        Ycorner = ymax
        for ii in range(len(self.lines)):
            self.lines[ii][0] = self.lines[ii][0]-Xcorner
            self.lines[ii][1] = self.lines[ii][1]-Ycorner
            self.lines[ii][2] = self.lines[ii][2]-Xcorner
            self.lines[ii][3] = self.lines[ii][3]-Ycorner

        self.cut_lines = []
        self.eng_lines = []
        for line in self.lines:
            rgb = line[4]
            ID = line[5]
            if self.Cut_Type[ID] == "engrave":
                # for the color take only the blue component (engrave)
                depth = rgb & 0x0000FF
                self.eng_lines.append([line[0], line[1], line[2], line[3], depth])
            elif self.Cut_Type[ID] == "cut":
                # for the color take only the red component (cut)
                depth = rgb >> 16
                self.cut_lines.append([line[0], line[1], line[2], line[3], depth])
            else:
                pass

if __name__ == '__main__':
    svg_reader = SVG_READER(0.1)
    #svg_reader.parse("test.svg")
    #svg_reader.make_paths()
