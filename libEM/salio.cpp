/**
 * $Id$
 */
#include "salio.h"
#include "log.h"
#include "emutil.h"
#include "util.h"
#include "geometry.h"

#ifndef WIN32
#include <sys/param.h>
#endif
#include <limits.h>


using namespace EMAN;

const char *SalIO::HDR_EXT = ".hdr";
const char *SalIO::IMG_EXT = ".img";
const char *SalIO::MAGIC = " IDENTIFICATION";


SalIO::SalIO(string file, IOMode rw)
:	filename(file), rw_mode(rw), sal_file(0), initialized(false)
{
	nx = 0;
	ny = 0;
	record_length = 512;
	scan_mode = NON_RASTER_SCAN;
	pixel = 4.6667f;
}

SalIO::~SalIO()
{
	if (sal_file) {
		fclose(sal_file);
		sal_file = 0;
	}
}

int SalIO::init()
{
	ENTERFUNC;
	
	static int err = 0;
	if (initialized) {
		return err;
	}

	initialized = true;

	string hdr_filename = Util::get_filename_by_ext(filename, HDR_EXT);
	string img_filename = Util::get_filename_by_ext(filename, IMG_EXT);

	bool is_new_file = false;
	sal_file = sfopen(hdr_filename, rw_mode, &is_new_file);
	if (!sal_file) {
		err = 1;
		return err;
	}


	char scan_type[MAXPATHLEN];

	ScanAxis axis = X_SCAN_AXIS;

	if (!is_new_file) {
		char buf[MAXPATHLEN];
		if (fgets(buf, MAXPATHLEN, sal_file)) {
			if (!is_valid(buf)) {
				LOGERR("'%s' is not a valid SAL file", filename.c_str());
				err = 1;
				return err;
			}
		}

		while (fgets(buf, MAXPATHLEN, sal_file)) {
			const char *buf1 = buf + 1;

			if (Util::sstrncmp(buf1, "NXP")) {
				sscanf(strchr(buf, '=') + 1, " %d", &nx);
			}
			else if (Util::sstrncmp(buf1, "NYP")) {
				sscanf(strchr(buf, '=') + 1, " %d", &ny);
			}
			else if (Util::sstrncmp(buf1, "AXSCAN")) {
				char *t = strrchr(buf, '\'');
				if (t[-1] == 'Y') {
					axis = Y_SCAN_AXIS;
				}
			}
			else if (Util::sstrncmp(buf1, "FILE REC LEN")) {
				sscanf(strchr(buf, '=') + 1, " %d", &record_length);
			}
			else if (Util::sstrncmp(buf1, "SCAN TYPE")) {
				sscanf(strchr(buf, '\'') + 1, " %s", scan_type);
				if (scan_type[0] == 'R') {
					scan_mode = RASTER_SCAN;
				}
			}
			else if (Util::sstrncmp(buf1, "DELTAX")) {
				sscanf(strchr(buf, '=') + 1, " %f", &pixel);
				pixel /= 3.0;
			}
		}


		if (axis == Y_SCAN_AXIS) {
			int t = nx;
			nx = ny;
			ny = t;
		}
	}
	fclose(sal_file);
	sal_file = sfopen(img_filename, rw_mode);
	if (!sal_file) {
		err = 1;
		return err;
	}
	EXITFUNC;
	return 0;
}

bool SalIO::is_valid(const void *first_block)
{
	ENTERFUNC;
	bool result = false;
	
	if (!first_block) {
		result = false;
	}
	result = Util::check_file_by_magic(first_block, MAGIC);
	EXITFUNC;
	return result;
}

int SalIO::read_header(Dict & dict, int image_index, const Region * area, bool)
{
	ENTERFUNC;
	int err = 0;
	
	if (check_read_access(image_index) != 0) {
		err = 1;
	}
	else {
		if (check_region(area, IntSize(nx, ny)) != 0) {
			err = 1;
		}
		else {
			int xlen = 0, ylen = 0;
			EMUtil::get_region_dims(area, nx, &xlen, ny, &ylen);

			dict["nx"] = xlen;
			dict["ny"] = ylen;
			dict["nz"] = 1;
			dict["datatype"] = EMUtil::EM_SHORT;
			dict["pixel"] = pixel;
		}
	}
	EXITFUNC;
	return err;
}

int SalIO::write_header(const Dict &, int, const Region* area, bool)
{
	ENTERFUNC;
	LOGWARN("SAL write is not supported.");
	EXITFUNC;
	return 1;
}

int SalIO::read_data(float *data, int image_index, const Region * area, bool)
{
	ENTERFUNC;

	if (check_read_access(image_index, data) != 0) {
		return 1;
	}
	if (check_region(area, IntSize(nx, ny)) != 0) {
		return 1;
	}

	if (scan_mode != NON_RASTER_SCAN) {
		LOGERR("only NON_RASTER_SCAN scan mode is supported in a SAL image");
		return 1;
	}
	
	rewind(sal_file);

	size_t mode_size = sizeof(short);
	unsigned char *cdata = (unsigned char *) data;
	short *sdata = (short *) data;
	size_t row_size = nx * mode_size;
	size_t block_size = (((row_size - 1) / record_length) + 1) * record_length;
	size_t post_row = block_size - row_size;

	EMUtil::process_region_io(cdata, sal_file, READ_ONLY, image_index, 
							  mode_size, nx, ny, 1, area, false, 0, post_row);

#if 0
	int row_size = nx * mode_size;
	int block_size = (((row_size - 1) / record_length) + 1) * record_length;

	for (int j = 0; j < ny; j++) {
		if (fread(&cdata[j * row_size], block_size, 1, sal_file) != 1) {
			LOGERR("Incomplete SAL data read %d/%d blocks", j, ny);
			return 1;
		}
	}
#endif

	int xlen = 0, ylen = 0;
	EMUtil::get_region_dims(area, nx, &xlen, ny, &ylen);

	if (scan_mode == NON_RASTER_SCAN) {
		become_host_endian(sdata, xlen * ylen);

		for (int i = 0; i < ylen; i += 2) {
			for (int j = 0; j < xlen / 2; j++) {
				short sw = sdata[i * xlen + j];
				sdata[i * xlen + j] = sdata[i * xlen + xlen - j - 1];
				sdata[i * xlen + xlen - j - 1] = sw;
			}
		}
	}

	for (int i = xlen * ylen - 1; i >= 0; i--) {
		data[i] = static_cast < float >((cdata[i * 2 + 1] * UCHAR_MAX) + cdata[i * 2]);
	}
	EXITFUNC;
	return 0;
}

int SalIO::write_data(float *, int, const Region* area, bool)
{
	ENTERFUNC;
	LOGWARN("SAL write is not supported.");
	EXITFUNC;
	return 1;
}

void SalIO::flush()
{
}


bool SalIO::is_complex_mode()
{
	return false;
}

bool SalIO::is_image_big_endian()
{
	return false;
}

