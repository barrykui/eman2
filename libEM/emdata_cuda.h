/*
 * Author: Steven Ludtke, 04/10/2003 (sludtke@bcm.edu)
 * Copyright (c) 2000-2006 Baylor College of Medicine
 *
 * This software is issued under a joint BSD/GNU license. You may use the
 * source code in this file under either license. However, note that the
 * complete EMAN2 and SPARX software packages have some GPL dependencies,
 * so you are responsible for compliance with the licenses of these packages
 * if you opt to use BSD licensing. The warranty disclaimer below holds
 * in either instance.
 *
 * This complete copyright notice must be included in any revised version of the
 * source code. Additional authorship citations may be added, but existing
 * author citations must be preserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 *
 * */

#ifndef eman__emdatacuda_h__
#define eman__emdatacuda_h__ 1

#ifdef EMAN2_USING_CUDA

public:
	/** Called externally if the associated cuda array is freed
	 */
	inline void reset_cuda_array_handle() { cuda_array_handle = -1; }
	

// 	void bind_cuda_array();
	
	void bind_cuda_texture();
	
	// This should never be set by anything other than something that knows what it's doing
	inline void set_cuda_array_handle(const int idx) { cuda_array_handle = idx; }
	
	
	
	/** Get the cuda device pointer to the raw data
	 * May cause an allocation, reflecting the lazy strategy employed in EMAN2
	 * Will copy the CPU rdata pointer if it is up to date.
	 * @return a cuda device allocated float pointer
	 */
	float* get_cuda_data() const;
	
	/** A convenient way to get the EMData object as an EMDataForCuda struct
	 * @return an EMDataForCuda struct storing vital information
	 */
	EMDataForCuda get_data_struct_for_cuda() { 
		EMDataForCuda tmp = {get_cuda_data(),nx,ny,nz};
		return tmp;
	}
	
	/** Calc the correlation of this EMData with another using the CUDA device
	 * Does this using Fourier methods
	 * @param image the image to perform the correlation operation with
	 * @return a real space correlation image
	 */
	EMData* calc_ccf_cuda(EMData* image );
	
	/** Multiply the image by a constant value using the CUDA device
	 * @param val the amount by which to multiply each pixel in the image
	 */
	void mult_cuda(const float& val);
	
	/** Explicitly register that the raw data on the GPU has changed in some/any way.
	 * An important part of the EMAN2 device/host framework.
	 * This will set a flag telling the EMData object that both the CPU raw data pointer and
	 * read only array on the CUDA device are out of date and need to be updated at a later point.
	 * Also sets a flag dictating that the cached statistics of the image need to be updated.
	 */
	void gpu_update();
	
	bool gpu_rw_is_current() const;
private:
	
	/** Free the read only CUDA array on the device
	 */
	void free_cuda_array() const;
	
	/** Free the read-write CUDA float pointer on the device
	 */
	void free_cuda_memory() const;
	
	mutable int cuda_array_handle;
	
	/// A handle which may used to retrieve the device float pointer from the CudaDeviceEMDataCache using its [] operator
	mutable int cuda_cache_handle;
	
	/** CudaDeviceEMDataCache stores the CUDA device pointers of EMData objects
	 * This is a "snake cache" that eats its own tail once the available slots are all taken. 
	 * In the event of a random slot becoming free it is simply left that way, waiting empty until the snake head devours it.
	 * @author David Woolford
	 * @date February 2009
	*/
	class CudaDeviceEMDataCache {
	public:
		/** Constructor
		 * @param size the size of the cache
		 */
		CudaDeviceEMDataCache(const unsigned int size);
		
		/** Destructor, frees any non zero CUDA memory 
		 */
		~CudaDeviceEMDataCache();
		
		/** Cache the data of the EMData and return in index reflecting its position in the cache
		 * @param emdata the EMData object making the call
		 * @param data the raw data pointer of the EMData object which is making the call
		 * @param nx the length of the x dimension of the raw data pointer
		 * @param ny the length of the y dimension of the raw data pointer
		 * @param nz the length of the z dimension of the raw data pointer
		 * @return the index of the cached CUDA device pointer, as stored by this object
		 */
		unsigned int cache_rw_data(const EMData* const emdata, const float* const data,const int nx, const int ny, const int nz);
		
		unsigned int cache_ro_data(const EMData* const emdata, const float* const data,const int nx, const int ny, const int nz);
		
		/** Operator[] access to the cache
		 * Should be called using the return value of the cache_data function
		 * @param idx the index of the stored CUDA device pointer
		 * @return a CUDA device float pointer
		 */
		inline float* operator[](const unsigned int idx) const { return rw_cache[idx]; }
		
		inline float* get_rw_data(const unsigned int idx) const { return rw_cache[idx]; }
		inline cudaArray* get_ro_data(const unsigned int idx) const { return ro_cache[idx]; }
		
		inline bool has_rw_data(const unsigned int idx) const { return (rw_cache[idx] != 0); }
		inline bool has_ro_data(const unsigned int idx) const { return (ro_cache[idx] != 0); }
		
		/** Clear a cache slot at a given index
		 * Performs device memory freeing if stored data is non zero
		 * @param idx the index of the stored CUDA device pointer
		 */
		void clear_item(const unsigned int idx);
		
		/** Clear the rw data from a cache slot whilst simultaneously determining the current ro data is up to date
		 */
// 		int copy_ro_to_rw_data(const unsigned int idx);
		
		
		void copy_rw_to_ro(const unsigned idx);
		
		inline unsigned int get_ndim(const unsigned int idx) {
			return caller_cache[idx]->get_ndim();
		}
	private:
		
		float* alloc_rw_data(const int nx, const int ny, const int nz);
		
		/// The size of the cache
		unsigned int cache_size;
		/// The current position of the "snake head" in terms of the cache_size
		unsigned int current_insert_idx;
		
		/// The CUDA device rw pointer cache
		float** rw_cache;
		/// A cache of the objects that called the cache_data function, so EMData::cuda_cache_lost_imminently can be called if necessary
		const EMData** caller_cache;
		/// The CUDA  read only cache
		cudaArray ** ro_cache;
	};
	
	/// CudaDeviceEMDataCache is a friend because it calls cuda_cache_lost_imminently, a specialized function that should not be made public.
	friend class CudaDeviceEMDataCache;
	
	/** Called by the CudaDeviceEMDataCache just before it frees the associated cuda device pointer
	 * Internally the EMData object will update its CPU version of the raw data if it is out of data as a result of GPU processing.
	 * Currently based loosely on the assumption that the host will always have more memory than the device, this may change, but works for the time being
	 */
	void cuda_cache_lost_imminently() const;
	
	/// Cuda device pointer cache
	static CudaDeviceEMDataCache cuda_cache;
	
#endif // EMAN2_USING_CUDA
	
#endif //eman__emdatacuda_h__ 1

