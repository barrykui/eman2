#!/usr/bin/env python
from __future__ import print_function

# Author: Muthu Alagappan, m.alagappan901@gmail.com, 07/22/09
# Copyright (c) 2000-2006 Baylor College of Medicine
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
#

from EMAN2 import *
from PyQt5 import QtCore
from emfoldhunterstat import *
from emapplication import get_application
from empdbvaltool import EMPDBValWidget
from emplot3d import *
import os

class E2ValidateMed():
	
	def __init__(self):
		self.em_val = None #will become the empdbvaltool module
		self.plot3d =  None #will become the emplot3d module
		self.fh_stat = E2FoldHunterStat()

	def start(self): #program starts here, inits the empdbvaltool module
		if self.em_val == None:
			self.__init_em_val()
		
		get_application().show()

	def __init_em_val(self): #formally creates the empdbvaltool module, waits for a signal to validate or close
		if self.em_val == None: 
			self.em_val = EMPDBValWidget()
			self.em_val.run_validate.connect(self.on_em_validate_requested)
			self.em_val.module_closed.connect(self.on_em_val_closed)
	
	def on_em_val_closed(self):
		self.em_val = None

	def __init_plot3d(self):
		if self.plot3d == None: 
			self.plot3d = EMPlot3DWidget()
			self.plot3d.plot_model.view_transform.connect(self.on_view_transform_requested)
			self.plot3d.plot_model.module_closed.connect(self.on_plot3d_closed)

	def on_view_transform_requested(self, new_pdb_file):
		if self.em_val == None:
			self.__init_em_val()
			get_application().show()
		self.em_val.set_pdb_file(str(new_pdb_file))
		os.remove(str(new_pdb_file))

	def on_plot3d_closed(self):
		self.plot3d = None

	def on_em_validate_requested(self, mrc_file, pdb_file, trans, iso_thresh): #if signal given to validate, creates emplot3d and displays graph

		vals = {}
		rotList = []
		data = []
		initPoint = []

		try: #block user from view transforms from files that don't exist
			f = open(pdb_file)
			f.close()
		except IOError:	
			print("Sorry, this pdb is only in temporary memory. Please write the transform to the hard drive to validate.")
			return

	
		print(" ") 
		print(" ") 
		print("This process can take a few minutes depending on the number of transformations requested")

		vals, rotList, b, data, initPoint = self.fh_stat.gen_data(mrc_file, pdb_file, trans, iso_thresh)
	
		if self.plot3d:	get_application().close_specific(self.plot3d)
		self.plot3d = None

		if self.plot3d == None: #creates the emplot3d module after the data has been generated by fh_stat
			self.__init_plot3d()

		print("Note: The original probe is displayed by a cube")
		print(" ") 

		get_application().show()
		self.plot3d.plot_model.set_Vals(vals)
		self.plot3d.plot_model.set_Rotations(rotList)
		self.plot3d.plot_model.set_Probe(b)
		self.plot3d.plot_model.set_data(data,"Results for Fit Validation")
		self.plot3d.plot_model.set_data(initPoint, "Original Probe",shape="Cube") #note: original probe is displayed with a cube
		
		self.plot2d(vals["score_1"], vals["score_2"], vals["score_3"], rotList)

	def plot2d(self, s1, s2, s3, rotList):
		'''
		@s1: an array of all the transformations for the first scoring function (real space correlation)
		@s2: an array of the scores of every transformation in the second function (atom inclusion)
		@s3: an array of scores from the third function  (volume inclusion)
		@rotList: a list of all the random transformations
		In all the graphs, it graphs all the random transformations as green dots, and the target probe as a red dot, so the user knows how 
		the target probe fares relative to the random transformations. 
		'''
		from pylab import scatter, subplot, show, figure, colorbar
		########  Graphing 1  - graph of 2 of the 3 scoring functions plotted against each other
		
		g1 = figure(1)
		g1a = subplot(311)
		g1a.clear()
		g1a.scatter(s1,s2, marker ="o", color ="green")
		g1a.scatter(s1[:1],s2[:1],color="red")
		g1a.set_xlabel("Real space correlation")
		g1a.set_ylabel("Atom Inclusion Percentage")
		
		g1b = subplot(312)
		g1b.clear()
		g1b.scatter(s3,s2, marker = "o", color="green")
		g1b.scatter(s3[:1],s2[:1],color="red")
		g1b.set_xlabel("Volume Overlap")
		g1b.set_ylabel("Atom Inclusion Percentage")
		
		g1c=subplot(313)
		g1c.clear()
		g1c.scatter(s3,s1, marker = "o", color="green")
		g1c.scatter(s3[:1],s1[:1],color="red")
		g1c.set_xlabel("Volume Overlap")
		g1c.set_ylabel("Real space correlation")
#		show()
		####################################################
		
		######### Graphing 2 - individual line grpahs for each scoring function
		
		g2 = figure(2)
		g2a = subplot(311)
		g2a.clear()
		blank = []
		for i in range(0,len(s1)):
			blank.append(0)
		g2a.scatter(s1,blank, marker ="o", color ="green")
		g2a.scatter(s1[:1],blank[:1],color="red")
		g2a.set_xlabel("Real space correlation")
		g2a.set_ylabel(" ")
		
		g2b = subplot(312)
		g2b.clear()
		g2b.scatter(s2,blank, marker = "o", color="green")
		g2b.scatter(s2[:1],blank[:1],color="red")
		g2b.set_xlabel("Atom Inclusion Percentage")
		g2b.set_ylabel(" ")
		
		g2c=subplot(313)
		g2c.clear()
		g2c.scatter(s3,blank, marker = "o", color="green")
		g2c.scatter(s3[:1],blank[:1],color="red")
		g2c.set_xlabel("Volume Overlap")
		g2c.set_ylabel(" ")
#		show()
		
		###################################################
		
		########## Graphing 3 - line graph for cumulative z-score
		
		g3 = figure(3)
		g3a = subplot(111)
		g3a.clear()
		
		blank = []
		s4 =[]
		for i in range(0,len(s1)):
			blank.append(0)
			te = s1[i] + s2[i] + s3[i]
			s4.append(te)
		
		s4_s=0
		val = 0
		for i in range(0, len(s4)):
			if (s4[i]>s4_s): 
				s4_s = s4[i]
				val = i
		valT = Transform(rotList[val].get_params("eman"))
		
		g3a.scatter(s4,blank, marker ="o", color ="green")
		g3a.scatter(s4[:1],blank[:1],color="red")
		g3a.set_xlabel("Total z score")
		g3a.set_ylabel(" ")
#		show()
		
		##################################################
		
		
		######## Graphimg 4 - histogram for each scoring function
		
		g4 = figure(4)
		g4a = subplot(311)
		g4a.clear()
		g4a.hist(s1,50, histtype='bar')
		g4a.scatter(s1[:1],blank[:1],color="red")
		g4a.set_xlabel("Real space correlation")
		
		g4b = subplot(312)
		g4b.clear()
		g4b.hist(s2,50, histtype='bar')
		g4b.scatter(s2[:1], blank[:1],color="red")
		g4b.set_xlabel("Atom Inclusion Percentage")
		
		g4c = subplot(313)
		g4c.clear()
		g4c.hist(s3,50, histtype='bar')
		g4c.scatter(s3[:1], blank[:1],color="red")
		g4c.set_xlabel("Volume inclusion")
		show()
		#################################################

if __name__ == '__main__':
	from emapplication import EMApp
	em_app = EMApp()
	window = E2ValidateMed()
	window.start()
	#em_app.show()
	em_app.execute()

		
		
