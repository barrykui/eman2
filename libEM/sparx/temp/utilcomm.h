#ifndef UTILCOMM_H
#define UTILCOMM_H

#include "mpi.h"
#include "stdlib.h"
#include "emdata.h"
#include "alignoptions.h"

using namespace EMAN;

int ReadVandBcast(MPI_Comm comm, EMData *volume, char *volfname);
int ReadStackandDist(MPI_Comm comm, EMData ***images2D, char *stackfname, int *nloc);
int CleanStack(MPI_Comm comm, EMData ** image_stack, int nloc, int ri, Vec3i volsize, Vec3i origin);
int setpart(MPI_Comm comm, int nima, int *psize, int *nbase);
int ParseAlignOptions(MPI_Comm comm, AlignOptions& options, char* optionsfname, int nvoxels, EMData*& mask3D);

#endif // UTILCOMM_H
