/**
 * $Id$
 */
#include "sspiderio.h"
#include "geometry.h"
#include "portable_fileio.h"

using namespace EMAN;

SingleSpiderIO::SingleSpiderIO(const string & file, IOMode rw)
:	SpiderIO(file, rw)
{
}

SingleSpiderIO::~SingleSpiderIO()
{
}


int SingleSpiderIO::write_header(const Dict & dict, int , const Region* area,
								 EMUtil::EMDataType filestoragetype, bool use_host_endian)
{
	return write_single_header(dict, area, filestoragetype, use_host_endian);
}

int SingleSpiderIO::write_data(float *data, int , const Region* area,
							   EMUtil::EMDataType filestoragetype, bool use_host_endian)
{
	return write_single_data(data, area, filestoragetype, use_host_endian);
}

bool SingleSpiderIO::is_valid(const void *first_block)
{
	ENTERFUNC;
	bool result = false;
	
	if (!first_block) {
		result = false;
	}

	const float *data = static_cast < const float *>(first_block);
	float nslice = data[0];
	float type = data[4];
	float ny = data[1];
	float istack = data[23];
	bool big_endian = ByteOrder::is_float_big_endian(nslice);
	
	if (big_endian != ByteOrder::is_host_big_endian()) {
		ByteOrder::swap_bytes(&nslice);
		ByteOrder::swap_bytes(&type);
		ByteOrder::swap_bytes(&ny);
		ByteOrder::swap_bytes(&istack);
	}

	if ((int (nslice)) !=nslice) {
		result = false;
	}

	const int max_dim = 1 << 20;
	int itype = static_cast < int >(type);

	if ((itype == IMAGE_2D 
                    || itype == IMAGE_3D
                    || itype == IMAGE_2D_FFT_ODD
                    || itype == IMAGE_2D_FFT_EVEN
                    || itype == IMAGE_3D_FFT_ODD
                    || itype == IMAGE_3D_FFT_EVEN
                    ) && (istack == SINGLE_IMAGE_HEADER) &&
		(nslice > 0 && nslice < max_dim) && (ny > 0 && ny < max_dim)) {
		result = true;
	}

	EXITFUNC;
	return result;
}


bool SingleSpiderIO::is_valid_spider(const void *first_block)
{
	return SingleSpiderIO::is_valid(first_block);
}
