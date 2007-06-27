#!/usr/bin/env python

#
# Author: Steven Ludtke, 06/27/2007 (sludtke@bcm.edu)
# Copyright (c) 2000-2007 Baylor College of Medicine
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  2111-1307 USA
#
#

# e2resolution.py  06/27/2007	Steven Ludtke
# This program computes a similarity matrix between two sets of images

from EMAN2 import *
from optparse import OptionParser
from math import *
import os
import sys

def main():
	progname = os.path.basename(sys.argv[0])
	usage = """%prog [options] <volume> <mask> <output>
	This will compute an FSC resolution curve from a single structure by
	comparing the power spectrum of the noise region to the power spectrum
	of the reconstructed particle. The 'mask' input should mask out the particle,
	and should be a 'soft' mask. Sharp edges on the mask may ruin the results.
	proc3d (EMAN1) with the automask2 option can produce appropriate masks. The
	3rd parameter (in automask2) should be about 10% of the box size. This will not
	work with particles that have been tightly masked already. If doing an EMAN1
	reconstruction with the amask= option, you must also use the refmaskali option
	(in the refine command). Note that the resultant curve is guarenteed to go
	to zero at near Nyquist because it assumes that the SNR is zero near Nyquist.
	If your data is undersampled, the resulting curve may also be inaccurate.
	Models should also not be heavily low-pass filtered
	"""
	parser = OptionParser(usage=usage,version=EMANVERSION)

	parser.add_option("--apix", "-A", type="float", help="A/voxel", default=-1.0)
	#parser.add_option("--box", "-B", type="string", help="Box size in pixels, <xyz> or <x>,<y>,<z>")
	#parser.add_option("--het", action="store_true", help="Include HET atoms in the map", default=False)
	(options, args) = parser.parse_args()
	
	if len(args)<3 : parser.error("Input and output files required")
	
	E2n=E2init(sys.argv)
	
	#options.align=parsemodopt(options.align)

	data=EMData(args[0])
	mask=EMData(args[1])

	# inverted mask
	maski=mask.copy()
	maski*=-1.0
	maski+=1.0

	noise=data.copy()
	noise*=maski

	data*=mask

	dataf=data.do_fft()
	noisef=noise.do_fft()

	datapow=dataf.calc_radial_dist(dataf.get_ysize()/2-1,1,1,1)
	noisepow=noisef.calc_radial_dist(noisef.get_ysize()/2-1,1,1,1)

	# normalize noise near Nyquist
	s=0
	for i in range(len(noisepow)-8,len(noisepow)-2):
		s+=datapow[i]/noisepow[i]
	s/=6.0

	noisepow=[i*s for i in noisepow]

	# compute signal to noise ratio
	snr=[]
	for i in range(len(datapow)):
		try: snr.append((datapow[i]-noisepow[i])/noisepow[i])
		except: snr.append(0)
	
	# convert to FSC
	fsc=[i/(2.0+i) for i in snr]

	x=range(1,len(fsc))
	if options.apix>0:
		x=[i/(len(fsc)*options.apix*2.0) for i in x]

	out=args[2]
	for i in range(len(fsc)): out.write("%f\t%f\n"%(x[i],fsc[i]))
	out.close()
	
	E2end(E2n)
	

				
if __name__ == "__main__":
    main()
