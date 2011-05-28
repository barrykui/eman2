#!/usr/bin/env python

#
# Author: Steven Ludtke  3/4/2011
# Copyright (c) 2011- Baylor College of Medicine
#
# This software is issued under a joint BSD/GNU license. You may use the
# source code in this file under either license. However, note that the
# complete EMAN2 and SPARX software packages have some GPL dependencies,
# so you are responsible for compliance with the licenses of these packages
# if you opt to use BSD licensing. The warranty disclaimer below holds
# in either instance.
#
# This complete copyright notice must be included in any revised version of the
# source code. Additional authorship citations may be added, but existing
# author citations must be preserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston MA 02111-1307 USA
#

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from optparse import OptionParser
import sys
import os
import weakref
import threading

from EMAN2 import *
from emapplication import get_application, EMApp
from emimage2d import EMImage2DWidget
from emimagemx import EMImageMXWidget
from emimage3d import EMImage3DWidget
from emshape import EMShape
from valslider import *

def main():
	progname = os.path.basename(sys.argv[0])
	usage = """%prog [options] <image file>

	Provides a GUI interface for applying a sequence of filters to an image, stack of images or a volume."""

	parser = OptionParser(usage=usage,version=EMANVERSION)

#	parser.add_option("--boxsize","-B",type="int",help="Box size in pixels",default=64)
#	parser.add_option("--shrink",type="int",help="Shrink factor for full-frame view, default=0 (auto)",default=0)
	parser.add_option("--apix",type="float",help="Override the A/pix value stored in the file header",default=0.0)
	parser.add_option("--verbose", "-v", dest="verbose", action="store", metavar="n", type="int", default=0, help="verbose level [0-9], higner number means higher level of verboseness")
	
	(options, args) = parser.parse_args()
		
	if len(args) != 1: parser.error("You must specify a single data file on the command-line.")
	if not file_exists(args[0]): parser.error("%s does not exist" %args[0])
#	if options.boxsize < 2: parser.error("The boxsize you specified is too small")
#	# The program will not run very rapidly at such large box sizes anyhow
#	if options.boxsize > 2048: parser.error("The boxsize you specified is too large.\nCurrently there is a hard coded max which is 2048.\nPlease contact developers if this is a problem.")
	
#	logid=E2init(sys.argv)
	
	app = EMApp()
	
	control=EMFilterTool(datafile=args[0],apix=options.apix,verbose=options.verbose)
	control.show()
	app.execute()
#	E2end(logid)

def filtchange(name,value):
	return {}

class EMProcessorWidget(QtGui.QWidget):
	"""A single processor with parameters"""
	
	plist=dump_processors_list()
	
	# Sorted list of the stuff before the first '.'
	cats=set([i.split(".")[0] for i in plist.keys()])
	cats=list(cats)
	cats.sort()
	
	# For some parameters we will try to assign sensible default values and ranges. This information should probably be a part
	# of the processor objects themselves, but isn't at present.
	# (start enabled, range, default value, change callback)
	parmdefault= {
		"cutoff_abs":(1,(0,.5),.1,filtchange),
		"cutoff_freq":(0,(0,1.0),None,filtchange),
		"cutoff_pixels":(0,(0,128),None,filtchange),
		"cutoff_resolv":(0,(0,1.0),None,filtchange),
		"apix":(0,(0.2,10.0),2.0,None)
	}
	
	def __init__(self,parent=None):
		app=QtGui.qApp
		
		QtGui.QWidget.__init__(self,parent)
		self.gbl = QtGui.QGridLayout(self)
		self.gbl.setColumnStretch(0,0)
		self.gbl.setColumnStretch(1,0)
		self.gbl.setColumnStretch(2,1)
		self.gbl.setColumnStretch(3,3)
		
		# Enable checkbox
		self.wenable=QtGui.QCheckBox(self)
		self.wenable.setChecked(True)
		self.gbl.addWidget(self.wenable,0,1)
		
		# List of processor categories
		self.wcat=QtGui.QComboBox(self)
		self.wcat.addItem("")
		for i in self.cats: self.wcat.addItem(i)
#		self.wcat.setCurrentindex(self.wcat.findText("filter"))
		self.gbl.addWidget(self.wcat,0,2)
		
		# List of processor subcategories
		self.wsubcat=QtGui.QComboBox(self)
		self.gbl.addWidget(self.wsubcat,0,3)
#		self.update_subcat()

		#button grid
		self.gbl2=QtGui.QGridLayout()
		self.gbl.addLayout(self.gbl2,0,0,1,1)
		self.gbl2.setSpacing(1)
		
		self.gbl2.setColumnStretch(0,1)
		self.gbl2.setColumnStretch(1,1)
		
#		self.wup = QtGui.QPushButton(app.style().standardIcon(QtGui.QStyle.SP_ArrowUp),"")
		self.wup = QtGui.QPushButton(pix_up,"",self)
		self.wup.setMaximumSize(QtCore.QSize(17, 17))
#		self.wup.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
		self.gbl2.addWidget(self.wup,0,0)
		
		self.wdown = QtGui.QPushButton(pix_down,"",self)
		self.wdown.setMaximumSize(QtCore.QSize(17, 17))
		self.gbl2.addWidget(self.wdown,1,0)
		
		self.wplus = QtGui.QPushButton(pix_plus,"",self)
		self.wplus.setMaximumSize(QtCore.QSize(17, 17))
		self.gbl2.addWidget(self.wplus,1,1)
		
		self.wminus= QtGui.QPushButton(pix_minus,"",self)
		self.wminus.setMaximumSize(QtCore.QSize(17, 17))
		self.gbl2.addWidget(self.wminus,0,1)
		
		
		QtCore.QObject.connect(self.wcat,QtCore.SIGNAL("currentIndexChanged(int)"),self.event_cat_sel)
		QtCore.QObject.connect(self.wsubcat,QtCore.SIGNAL("currentIndexChanged(int)"),self.event_subcat_sel)
		
		self.parmw=[]

	def event_cat_sel(self,idx):
		cat=str(self.wcat.currentText())
		scats=[i.split('.',1)[1] for i in self.plist if i.split(".")[0]==cat]
		scats.sort()
		self.wsubcat.clear()
		self.wsubcat.addItem("")
		if len(scats)>0 : self.wsubcat.addItems(scats)

	def event_subcat_sel(self,idx):
		cat=str(self.wcat.currentText())
		scat=str(self.wsubcat.currentText())
		proc=cat+"."+scat
		
		try: parms=self.plist[proc]
		except: parms=["Please select a processor"]
		
		self.wsubcat.setToolTip(parms[0])
		
		# Remove old parameter widgets
		for w in self.parmw:
			self.gbl.removeWidget(w)
			w.close()				# get it off the screen
			w.setParent(None)		# do this before we can actually delete the widget
			del(w)					# finally, get it deleted (may not take effect until parmw=[] below
		
		# Iterate over the parameters
		# parms[i] - name of the parameter
		# parms[i+1] - type of parameter
		# parms[i+2] - helpstring for parameter
		self.parmw=[]
		self.ninput=0
		for i in range(1,len(parms),3):
			self.ninput+=1  
			try: dflt=self.parmdefault[parms[i]]		# contains (start enabled, range, default value, change callback)
			except: dflt=(1,(0,1.0),None,None)			# default parameter settings if we don't have anything predefined
			
			self.parmw.append(ValSlider(self,dflt[1],parms[i],dflt[2],100,dflt[0]))
#			self.parmw[-1].hboxlayout.setContentsMargins ( 11.0,5.0,5.0,5.0 )
			self.parmw[-1].setToolTip(parms[i+2])
			self.gbl.addWidget(self.parmw[-1],self.ninput,1,1,4)
	
class EMFilterTool(QtGui.QMainWindow):
	"""This class represents the EMTomoBoxer application instance.  """
	
	def __init__(self,data=None,apix=0.0,verbose=0):
		QtGui.QWidget.__init__(self)
		
		app=QtGui.qApp
		self.apix=apix
		self.setWindowTitle("e2filtertool.py")
		
		# Menu Bar
		self.mfile=self.menuBar().addMenu("File")
		self.mfile_save_processed=self.mfile.addAction("Save processed data")
		self.mfile_quit=self.mfile.addAction("Quit")

		self.setCentralWidget(QtGui.QWidget())
		self.gbl = QtGui.QGridLayout(self.centralWidget())

		# relative stretch factors
		#self.gbl.setColumnStretch(0,1)
		#self.gbl.setColumnStretch(1,4)
		#self.gbl.setColumnStretch(2,0)
		#self.gbl.setRowStretch(1,1)
		#self.gbl.setRowStretch(0,4)
		
		#self.xyview = EMImage2DWidget()
		#self.gbl.addWidget(self.xyview,0,1)

		
		# file menu
		QtCore.QObject.connect(self.mfile_save_processed,QtCore.SIGNAL("triggered(bool)")  ,self.menu_file_save_processed  )
		QtCore.QObject.connect(self.mfile_quit,QtCore.SIGNAL("triggered(bool)")  ,self.menu_file_quit)

		# all other widgets
		#QtCore.QObject.connect(self.wdepth,QtCore.SIGNAL("valueChanged(int)"),self.event_depth)
		#QtCore.QObject.connect(self.wnlayers,QtCore.SIGNAL("valueChanged(int)"),self.event_nlayers)
		#QtCore.QObject.connect(self.wboxsize,QtCore.SIGNAL("valueChanged"),self.event_boxsize)
		#QtCore.QObject.connect(self.wmaxmean,QtCore.SIGNAL("clicked(bool)"),self.event_projmode)
		#QtCore.QObject.connect(self.wscale,QtCore.SIGNAL("valueChanged")  ,self.event_scale  )
		#QtCore.QObject.connect(self.wfilt,QtCore.SIGNAL("valueChanged")  ,self.event_filter  )
		#QtCore.QObject.connect(self.wlocalbox,QtCore.SIGNAL("stateChanged(int)")  ,self.event_localbox  )
		
		#QtCore.QObject.connect(self.xyview,QtCore.SIGNAL("mousedown"),self.xy_down)
		#QtCore.QObject.connect(self.xyview,QtCore.SIGNAL("mousedrag"),self.xy_drag)
		#QtCore.QObject.connect(self.xyview,QtCore.SIGNAL("mouseup"),self.xy_up  )
		#QtCore.QObject.connect(self.xyview,QtCore.SIGNAL("mousewheel"),self.xy_wheel  )
		#QtCore.QObject.connect(self.xyview,QtCore.SIGNAL("set_scale"),self.xy_scale)
		#QtCore.QObject.connect(self.xyview,QtCore.SIGNAL("origin_update"),self.xy_origin)

		self.viewer=None			# viewer window for data
		self.filters=[]				# list of filter specifications (name,dict)
		self.origdata=[]
		self.filtdata=[]
		self.nx=0
		self.ny=0
		self.nz=0

		if data!=None : self.set_data(data)
		
		
#		QtCore.QObject.connect(self.boxesviewer,QtCore.SIGNAL("mx_image_selected"),self.img_selected)
		
	def set_data(self,data):
		if data==None :
			self.data=None
			return
		
		elif isinstance(data,str) :
			self.datafile=data
			self.nimg=EMUtil.get_image_count(data)
			
			self.origdata=self.read_image(data,0)
			
			if self.nz==1:
				if self.n>20 : 
					self.origdata=EMData.read_images(data,range(20))
				elif self.n>1 :
					self.origdata=EMData.read_images(data,range(self.n))
				else: self.origdata=[self.origdata]
			else :
				self.origdata=[self.origdata]
		
		else :
			self.datafile=None
			if isinstance(data,EMData) : self.origdata=[data]
			else : self.origdata=data
			
			self.nx=self.origdata["nx"]
			self.ny=self.origdata["ny"]
			self.nz=self.origdata["nz"]


	def menu_file_save_processed(self):
		"incomplete"
		
	def menu_file_quit(self):
		self.close()
		
	def closeEvent(self,event):
		print "Exiting"
		if self.viewer!=None : self.viewer.close()
		event.accept()
		#self.app().close_specific(self)
		self.emit(QtCore.SIGNAL("module_closed")) # this signal is important when e2ctf is being used by a program running its own event loop

	#def closeEvent(self,event):
		#self.target().done()


pix_plus=QtGui.QIcon(QtGui.QPixmap(["15 15 3 1",
" 	c None",
".	c black",
"X	c grey",
"               ",
"               ",
"               ",
"               ",
"       .       ",
"       .X      ",
"       .X      ",
"    .......    ",
"     XX.XXXX   ",
"       .X      ",
"       .X      ",
"        X      ",
"               ",
"               ",
"               "
]))

pix_up=QtGui.QIcon(QtGui.QPixmap(["15 15 3 1",
" 	c None",
".	c black",
"X	c grey",
"               ",
"               ",
"               ",
"       .       ",
"      ...      ",
"     .....     ",
"    .......    ",
"    XXX.XXXX   ",
"       .X      ",
"       .X      ",
"       .X      ",
"       .X      ",
"        X      ",
"               ",
"               "
]))

pix_down=QtGui.QIcon(QtGui.QPixmap(["15 15 3 1",
" 	c None",
".	c black",
"X	c grey",
"               ",
"               ",
"               ",
"       .       ",
"       .X      ",
"       .X      ",
"       .X      ",
"       .X      ",
"    .......    ",
"     .....X    ",
"      ...X     ",
"       .X      ",
"               ",
"               ",
"               "
]))

pix_minus=QtGui.QIcon(QtGui.QPixmap(["15 15 3 1",
" 	c None",
".	c black",
"X	c grey",
"               ",
"               ",
"               ",
"               ",
"               ",
"               ",
"               ",
"   .........   ",
"    XXXXXXXXX  ",
"               ",
"               ",
"               ",
"               ",
"               ",
"               "
]))

if __name__ == "__main__":
	main()
		
		
		
