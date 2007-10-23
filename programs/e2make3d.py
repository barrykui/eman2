#!/usr/bin/env python

#
# Author: Steven Ludtke, 04/10/2003 (sludtke@bcm.edu), 
# David Woolford 05/14/2007 (woolford@bcm.edu)
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  2111-1307 USA
#
#

# initial version of make3d

from EMAN2 import *
from optparse import OptionParser
from copy import deepcopy
from math import ceil
import os
import sys
import math
import random

# python debugging
import pdb

CONTRIBUTING_PARTICLE_LIMIT = 1000000

def print_usage():
	progname = os.path.basename(sys.argv[0])
	usage = progname + " <inputfile> [options]"
	
	print "usage " + usage;
	print "Please run '" + progname + " -h' for detailed options"

def main():

	parser=OptionParser(usage="%prog <input file> [options]", version="%prog 2.0a")
	parser.add_option("--out", dest="outfile", default="", help="Output 3D MRC file")
	parser.add_option("--sym", dest="sym", default="UNKNOWN", help="Set the symmetry; if no value is given then the model is assumed to have no symmetry.\nChoices are: i, c, d, tet, icos, or oct")
	parser.add_option("--pad", type=int, dest="pad", help="To reduce Fourier artifacts, the model is typically padded by ~25% - only applies to Fourier reconstruction")
	parser.add_option("--recon", dest="recon_type", default="fourier", help="Reconstructor to use see e2help.py reconstructors -v")
	parser.add_option("--verbose", "-v",dest="verbose",default=False, action="store_true",help="Toggle verbose mode - prints extra infromation to the command line while executing")
	parser.add_option("--keep", type=float, dest="keep", help="The percentage of slices to keep, based on quality scores")
	parser.add_option("--keepsig", type=float, dest="keepsig", help="The standard deviation alternative to the --keep argument")
	
	parser.add_option("--no_wt", action="store_true", dest="no_wt", default=False, help="Turn weighting off")
	parser.add_option("--iter", type=int, dest="iter", default=3, help="Set the number of iterations (default is 3)")
	parser.add_option("--mask", type=int, dest="mask", help="Real-space mask radius")
	parser.add_option("--force", "-f",dest="force",default=False, action="store_true",help="Force overwrite the output file if it exists")
	parser.add_option("--nofilecheck",action="store_true",help="Turns file checking off in the check functionality - used by e2refine.py.",default=False)
	parser.add_option("--check","-c",action="store_true",help="Performs a command line argument check only.",default=False)


#	options that don't work and need to be verified for inclusion in EMAN2
#	parser.add_option("--snrfile", dest="snrfile", default="", help="Use a SNR file (as generated by classalignall) for proper 3D Wiener filtration")
#	parser.add_option("--fftmerge", dest="fftmerge", default="", help="Fourier model to merge with real model")
#	parser.add_option("--savenorm", action="store_true", dest="savenorm", default=False, help="Saves the normalization map to norm.mrc")
#	parser.add_option("--keep", type=float, dest="sigm", default=3.0, help="An alternative to 'hard'")
#	parser.add_option("--resmap", dest="resmap", default="", help="Generates a 'resolution map' in another 3D MRC file")

#	parser.add_option("--goodbad", action="store_true", dest="goodbad", default=False, help="Saves the used and unused class averages in 2 files")
#	parser.add_option("--apix", type=float, dest="apix", default=-1, help="Set the sampling (angstrom/pixel)")

	(options, args) = parser.parse_args()
	
	if options.nofilecheck: options.check = True
	
	# make sure that the user has atleast specified an input file
	if len(args) <1:
		parser.error("No input file specified")
	
	options.datafile = args[0]
	
	if (options.check): options.verbose = True # turn verbose on if the user is only checking...
	
	error = check(options,True)
	
	if (options.verbose):
		if (error):
			print "e2make3d.py command line arguments test.... FAILED"
		else:
			print "e2make3d.py command line arguments test.... PASSED"
		
	if error : exit(1)
	if options.check: exit(0)

	logger=E2init(sys.argv)
	# just remove the file - if the user didn't specify force then the error should have been found in the check function
	if os.path.exists(options.outfile):
		if options.force:
			remove_file(options.outfile)

	options.input_file = args[0]
	total_images=EMUtil.get_image_count(options.input_file)
	# if weighting is being used, this code checks to make sure atleast one image has an attribute "ptcl_repr" that is
	# greater than zero. If this is not the case, the insertion code will think there is nothing to insert...
	if ( options.no_wt == False ):
		ptcl_repr = False;
		# A sanity test
		for i in xrange(0,total_images):
			image = EMData()
			read_header_only = True
			image.read_image(options.input_file, i, True)
			num_img=image.get_attr("ptcl_repr") 
			if (num_img > 0):
				ptcl_repr = True;
				break
		
		if (ptcl_repr == False):
			print "Error - no image ptcl_repr attribute encountered that was greater than 0 - nothing done"
			print "Specify --no_wt to override this behaviour and give all inserted slices an equal weighting"
			exit(1)
	
		
	# Make sure the symmetry is valid
	options.sym=options.sym.lower()
	if options.sym.rstrip("0123456789") not in ["i","c","d","tet","icos","oct"]:
		sys.stderr.write("WARNING: '%s' is an unsupported symmetry type - assuming no symmetry\n" % (options.sym))
		options.sym=""      #needed??
	elif (options.sym[0] in ["c","d"]):
		if (options.sym.__len__()<2) or not(options.sym[1].isdigit()):
			sys.stderr.write("WARNING: '%s' must be follwed by a number - assuming 1 axis of symmetry\n" % options.sym[0])
			options.sym=options.sym[0]+"1"
	else:
		options.sym=options.sym.rstrip("0123456789")

	

	#if (options.goodbad):
		#try:
			#os.unlink("3dgood.hed")
			#os.unlink("3dbad.hed")
			#os.unlink("3dgood.img")
			#os.unlink("3dbad.img")
		#except:
			#pass
			
	recon_type = (parsemodopt(options.recon_type))[0]
	
	if recon_type=="fourier" or recon_type=="nn4":
		output=fourier_reconstruction(options)
	elif recon_type=="back_projection":
		output=back_projection_reconstruction(options)
	elif recon_type=="pawel_back_projection":
		output=pawel_back_projection_reconstruction(images, options)
	elif recon_type=="reverse_gridding":
		output=reverse_gridding_reconstructor(images, options) 
	elif recon_type=="wiener_fourier":
		output=wiener_fourier_reconstructor(images, options)
	else:
		# this point should never be reached
		sys.stderr.write("%s reconstuctor is not supported" % options.recon_type)
		exit(1)

	if ( options.mask):	
		output.process_inplace("mask.ringmean",{"ring_width":options.mask})

	if (options.outfile==""):
		output.write_image("threed.mrc")
		if not(options.verbose):
			print "Output File: threed.mrc"
	else:
		output.write_image(options.outfile)
		if not(options.verbose):
			print "Output File: "+options.outfile

	E2end(logger)
	
	print "Exiting"
#-----------------------------------------
# Not finished
def wiener_fourier_reconstructor(images, options):
	recon=Reconstructors.get("wiener_fourier",{"mode":options.mode,
											"padratio":1, # isn't right
											"size":images[0].get_xsize(),
											"snr":[] #isn't right
											})


#-----------------------------------------
# Doesn't work / not finished
# "npad" needs to be added to "Reverse_gridding_constructor::get_param_types()"
# maybe add ('s to insert_slice check #2; "!=" is evaled after the "||"
# where is vnx assigned to anything?
def reverse_gridding_reconstructor(images, options):
	if not(options.verbose):
		print "Setting up the reconstructor"
	recon=Reconstructors.get("reverse_gridding",{"weight":1.0,   # options.noweight, 
												"size":images[0].get_xsize(),
												"npad":1.0})
	recon.setup()

	for i in xrange(len(images)):
		d=images[i]
		d.process_inplace("normalize")
#        d.do_fft_inplace()
		recon.insert_slice(d, Transform3D(d.get_attr("euler_az"),
										d.get_attr("euler_alt"), #**2,
										d.get_attr("euler_phi")))

		if not(options.verbose):
			sys.stdout.write( "%2d/%d  %3d\t%5.1f  %5.1f  %5.1f\t\t%6.2g %6.2g\n" %
							(i+1,len(images),d.get_attr("IMAGIC.imgnum"),
							d.get_attr("euler_alt")*180.0/math.pi,
							d.get_attr("euler_az")*180.0/math.pi,
							d.get_attr("euler_phi")*180.0/math.pi,
							d.get_attr("maximum"),d.get_attr("minimum")))
		
	
	output = recon.finish()
	return output


#-----------------------------------------  should work
def pawel_back_projection_reconstruction(images, options):
	if not(options.verbose):
		print "Initializing the reconstructor"
	if (options.pad == 0):
		options.pad = 1;
	recon=Reconstructors.get("pawel_back_projection" ,{"npad":options.pad,
													"size":images[0].get_xsize(),
													"symmetry":options.sym})
	recon.setup()

	for i in xrange(len(images)):
		if (options.lowmem):
			d=EMData().read_images(options.input_file, [i])[0]
		else:
			d=images[i]
		d.process_inplace("normalize")           #is this needed? so other normalization?
		recon.insert_slice(d, Transform3D(d.get_attr("euler_az"),
										d.get_attr("euler_alt"),
										d.get_attr("euler_phi")))
		
		if not(options.verbose):
			sys.stdout.write( "%2d/%d  %3d\t%5.1f  %5.1f  %5.1f\t\t%6.2g %6.2g\n" %
							(i+1,len(images),d.get_attr("IMAGIC.imgnum"),
							d.get_attr("euler_alt")*180.0/math.pi,
							d.get_attr("euler_az")*180.0/math.pi,
							d.get_attr("euler_phi")*180.0/math.pi,
							d.get_attr("maximum"),d.get_attr("minimum")))
		
	output=recon.finish()

	# need to apply symmetry??

	return output


def back_projection_reconstruction(options):
	
	if not(options.verbose):
		print "Initializing the reconstructor"

	a = parsemodopt(options.recon_type)

	recon=Reconstructors.get(a[0], a[1])

	params = recon.get_params()
	(xsize, ysize ) = gimme_image_dimensions2D( options.input_file );
	if ( xsize != ysize ):
		print "Error, back space projection currently only works for images with uniform dimensions"
		exit(1)
		
	params["size"] = xsize;
	params["sym"] = options.sym

	recon.insert_params(params)

	recon.setup()

	total_images=EMUtil.get_image_count(options.input_file)
	
	for i in xrange(total_images):
		d=EMData().read_images(options.input_file, [i])[0]
		
		num_img=d.get_attr("ptcl_repr") 
		if ( num_img<=0 and options.no_wt == False):
			continue
		else:
			num_img = 1
		
		if ( options.no_wt == False ):
			weight = float (num_img)
		
		param = {}
		param["weight"] = weight
		recon.insert_params(param)
		
		t = Transform3D(d.get_attr("euler_az"), d.get_attr("euler_alt"), d.get_attr("euler_phi"))
		recon.insert_slice(d, t)

		if not(options.verbose):
			print "%2d/%d  %3d\t%5.1f  %5.1f  %5.1f\t\t%6.2g %6.2g" %(
					(i+1,total_images,d.get_attr("IMAGIC.imgnum"),
					d.get_attr("euler_alt"),
					d.get_attr("euler_az"),
					d.get_attr("euler_phi"),
					d.get_attr("maximum"),d.get_attr("minimum")))
		
	output=recon.finish()
	#tmp.process_inplace("normalize")
#    output.process_inplace("math.sqrt")  #right processor?

	
	## merging steps
	#if (options.fftmerge):
		#print "Merging Models"
		#ny = out.get_ysize()

		#d0=EMData().read_images(options.fftmerge,[0])
		#f0=d0.do_fft()
		#f1=output.do_fft()
	
		#for k in xrange(-ny/2,ny/2):
			#g=k
			#for j in xrange(-ny/2,ny/2):
				#for i in xrange(ny/2+1):
					#r=(k**2+j**2+i**2)**.5
					#if r==0 or r>ny/2:
						#f0.set_value_at(g,0)
						#continue
					#f0.set_value_at(g, f0.get_value_at(g)*r*2/ny+f1.get_value_at(g)*(1.0-r*2/ny))
					#g=g+2

		#output2=f0.do_ift()
		#output2.write_image(options.fftmerge)
		
	return output
		
#----------------------------------------- works
def fourier_reconstruction(options):
	if (options.verbose):
		print "Initializing the reconstructor ..."
	
	# Get the reconstructor and initialize it correctly
	a = parsemodopt(options.recon_type)
	recon=Reconstructors.get(a[0], a[1])
	params = recon.get_params()
	(xsize, ysize ) = gimme_image_dimensions2D( options.input_file );
	params["x_in"] = xsize;
	params["y_in"] = ysize;
	params["sym"] = options.sym
	if options.pad:
		if ( options.pad < params["x_in"] or options.pad < params["y_in"] ):
			print "You specified a padding of %d which is less than the image dimensions size %d x %d, so no action is taken" %(options.pad, params["x_in"], params["y_in"])
			exit(1)
		else:
			params["pad"] = options.pad
	recon.insert_params(params)
	recon.setup()
	
	total_images=EMUtil.get_image_count(options.input_file)
	
	#SNR=[]
	#if(options.snrfile):
		#for i in xrange(0,len(dataf)):
			#d=dataf[i]
			#tmp=EMData()
			#try:
				#tmp.read_image(options.snrfile,d.unum4)
			#except:
				#sys.stderr.write("Error reading SNR data from %s\n"%options.snrfile)
				#exit(1)
				##            SNR[0:]=[tmp.get_data()]  python won't call funcs that return float*
				#SNR=SNR+[tmp]

	if (options.verbose):
		print "Inserting Slices"
	
	for j in xrange(0,options.iter): #4):     #change back when the thr issue solved
		
		removed = 0;
		
		if ( j > 0 ):
			print "Determining slice agreement"
			for i in xrange(0,total_images):
				image = EMData()
				image.read_image(options.input_file, i)
				
				num_img=image.get_attr("ptcl_repr") 
				if (num_img<=0 and options.no_wt == False):
					continue
				else:
					num_img = 1
				
				weight = 1;
				if ( options.no_wt == False ):
					weight = float (num_img)
				
				param = {}
				param["weight"] = weight
				recon.insert_params(param) # this inserts the incoming parameter, but doesn't do anything to parameters already stored
				
				transform = Transform3D(EULER_EMAN,image.get_attr("euler_az"),image.get_attr("euler_alt"),image.get_attr("euler_phi"))
				#transform = Transform3D(EULER_EMAN,image.get_attr("euler_alt"),image.get_attr("euler_az"),image.get_attr("euler_phi"))
				
				recon.determine_slice_agreement(image,transform,num_img)
				sys.stdout.write(".")
				sys.stdout.flush()
	
			
			if ( options.keep != 1.0 or options.keepsig == True ):
				idx = 0
				fsc_scores = []
				hard = 0.0
				for i in xrange(0,total_images):
					if (image.get_attr("ptcl_repr")<=0 and options.no_wt == False):
						continue
					fsc_scores.append(-recon.get_score(idx))
					
					idx += 1
					
				if ( options.keepsig ):
					a = Util.get_stats_cstyle(fsc_scores)
					mean = a["mean"]
					std_dev = a["std_dev"]
					hard  = -(mean + options.keepsig*std_dev)
				else:
					b = deepcopy(fsc_scores)
					b.sort()
					# The ceil reflects a conservative policy. If the user specified keep=0.93
					# and there were 10 particles, then they would all be kept. If floor were
					# used instead of ceil, the last particle would be thrown away (in the
					# class average)
					idx = int(ceil(options.keep*len(b))-1)
					hard  = -b[idx]
				param = {}
				param["hard"] = hard
				recon.insert_params(param)
				
				print "using new hard parameter %f" %hard
			else:
				param = {}
				param["hard"] = 0.0
				recon.insert_params(param)
				print "using hard parameter 0.0"
			print " Done"
		
		
			
		idx = 0	
		for i in xrange(0,total_images):
			
			image = EMData()
			image.read_image(options.input_file, i)

			if (image.get_attr("ptcl_repr")<=0 and options.no_wt == False):
				continue
			
			weight = 1
			if ( options.no_wt == False ):
				weight = float (image.get_attr("ptcl_repr"))
			
			param = {}
			param["weight"] = weight
			recon.insert_params(param) # this inserts the incoming parameter, but doesn't do anything to parameters already stored
			
			
			#print "using weight %d" %(weight)
			#if (j==3 and recon.get_params()["dlog"]):
				#image.process_inplace("math.log")

			transform = Transform3D(EULER_EMAN,image.get_attr("euler_az"),image.get_attr("euler_alt"),image.get_attr("euler_phi"))
			#transform = Transform3D(EULER_EMAN,image.get_attr("euler_alt"),image.get_attr("euler_az"),image.get_attr("euler_phi"))
			failure = recon.insert_slice(image,transform)
			
			if (options.verbose):
				sys.stdout.write( "%2d/%d  %3d\t%5.1f  %5.1f  %5.1f\t\t%6.2f %6.2f" %
								(i+1,total_images, image.get_attr("IMAGIC.imgnum"),
								image.get_attr("euler_az"),
								image.get_attr("euler_alt"),
								image.get_attr("euler_phi"),
								image.get_attr("maximum"),image.get_attr("minimum")))
				if ( j > 0):
					sys.stdout.write("\t%f %f" %(recon.get_norm(idx), recon.get_score(idx) ))
					
				if ( failure ):
					sys.stdout.write( " X" )
					removed += 1
				
				sys.stdout.write("\n")

			#if (options.goodbad):
				#if g:
					#pass  #Should be writing to 3dgood
				#else:
					#pass #should be writing to 3dbad"
				
			idx += 1
			
		print "Iteration %d excluded %d images " %(j,removed)

	#if (options.goodbad):
		#print "print log msgs"

	if (options.verbose):
		print "Inverting 3D Fourier volume to generate the real space reconstruction"
	output = recon.finish()
	if (options.verbose):
		print "Finished Reconstruction"
		
	#if(options.savenorm):   # need to alter reconstructor class to get access to this
		#nm=EMData()
		#nm.set_size(out2.get_xsize(),out2.get_ysize(), out2.get_zsize())
		#for i in xrange(0,out2.get_xsize()*out2.get_ysize()*out2.get_zsize(),2):
			#nm.set_value_at_fast(i/2,out2.get_value_at(i,0,0))
		#nm.write_image("norm.mrc")
		#for i in xrange(0,out2.get_xsize()*out2.get_ysize()*out2.get_zsize(),2):
			#nm.set_value_at_fast(i/2,math.hypot(out2.get_value_at(i,0,0),out2.get_value_at(i+1,0,0)))
		#nm.write_image("map.mrc")
					
	if(recon.get_params()["dlog"]):
		output.process_inplace("math.exp")
			
	#if(options.resmap): #doesn't work
		#out=EMData()
		#ny2=output.get_ysize()
		#out.set_size(ny2,ny2,ny2)
		#out.to_zero()
		#for i in xrange(0,ny2):
			#for j in xrange(0,ny2):
				#for k in xrange(ny2/2,ny2):
					#sys.stdout.write("i=%g   j=%g   k=%g []=%g\n"%(i,j,k,(k-ny2/2)*2+j*(ny2+2)+i*(ny2+2)*ny2))
					##                   try:
					#out.set_value_at_fast(k+j*ny2+i*ny2*ny2,
										#(output.get_value_at((k-ny2/2)*2+j*(ny2+2)+i*(ny2+2)*ny2))**.5)
					#if (k<>ny2/2 and i<>0 and j<>0):
						#out.set_value_at_fast((ny2-k)+(ny2-j)*ny2+(ny2-i)*ny2*ny2,
											#(output.get_value_at((k-ny2/2)*2+j*(ny2+2)+i*(ny2+2)*ny2))**.5)
						#                  except ValueError:
						#                     print repr((k-ny2/2)*2+j*(ny2+2)+i*(ny2+2)*ny2)+" < 0"
		#out.write_image(options.resmap)
											
	# LOG message: LOG(Ref,resmap,LOG_INFILE,NULL)
		
	#if(SNR):  # doesn't work
		#out=EMData()
		#for i in xrange(0,ny2*ny2*(ny2+2),2):
			#temp=1./(1.+(1./output.get_value_at(i)))
			#out.set_value_at_fast(i,temp)
			#out.set_value_at_fast(i+1,temp)
		#out.write_image("filter3d.mrc")
		
	return output
	
def check(options,verbose=False):
	
	error = False
	
	if ( not options.sym ):
		if verbose:
			print  "Error: you must specify the sym argument"
		error = True
	
	if ( options.iter < 1 ):
		if verbose:
			print  "Error, --iter must be greater than or equal to 1"
		error = True
	
	if ( options.recon_type == None or options.recon_type == ""):
		if (verbose):
			print "Error: the --recon argument must be specified"
		error = True
	else:
		if ( check_eman2_type(options.recon_type,Reconstructors,"Reconstructor") == False ):
			error = True
	
	if ( options.keep and options.keepsig ):
		if verbose:
			print  "Error: --keep and --keepsig are mutually exclusive"
		error = True
	
	if (options.keep and ( options.keep > 1 or options.keep <= 0)):
		if verbose:
			print "Error: the --keep option is a percentage expressed as a fraction - it must be between 0 and 1"
		error = True
	
	if ( options.nofilecheck == False ):
		if not os.path.exists(options.datafile):
			if verbose:
				print  "Error: the 2D image data file (%s) does not exist, cannot run e2make3d.py" %(options.datafile)
			error = True
		else:
			if ( options.pad != 0 and options.pad != None):
				print options.pad
				(xsize, ysize ) = gimme_image_dimensions2D(options.datafile);
				if ( options.pad < xsize or options.pad < options.ysize):
					if verbose:
						print  "Error, you specified a padding size (%d) that was smaller than the image dimensions (%dx%d)"%(options.pad,xsize,ysize)
					error = True;
			
		if ( os.path.exists(options.outfile )):
			if ( not options.force ):
				if verbose:
					print  "Error: The output file exists and will not be written over. Use -f to overwrite"
				error = True
			
				
	if options.sym:
		options.sym=options.sym.lower()
		if (options.sym[0] in ["c","d", "h"]):
			if not(options.sym[1:].isdigit()):
				if verbose:
					print "Error: %s is an invalid symmetry type. You must specify the --sym argument"%options.sym
				error = True
		else :
			if not (options.sym in ["tet","oct","icos"]):
				if verbose:
					print "Error: %s is an invalid symmetry type. You must specify the --sym argument"%options.sym
				error = True
	
	return error

if __name__=="__main__":
	main()
