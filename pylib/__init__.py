import rasterio
import rasterio.mask
from joblib import Parallel, delayed
from tqdm.notebook import tqdm
import numpy as np 
import pandas as pd
import h5py

# Load a year of rasters, masked and cropped to a geometry
# See the rasterio documentation for more examples: 
# https://rasterio.readthedocs.io/en/latest/topics/masking-by-shapefile.html
def load_ntl(pkg, year, shapes=None):
    
    ref = pkg.reference(f'ntl{year}').resolved_url.get_resource().get_target()
    
    with rasterio.open(str(ref.fspath)) as src:
        
        if shapes is not None:
            img, transform = rasterio.mask.mask(src, shapes, crop=True)
        else:
            img =  src.read()
            transform = None
            
        meta = src.meta
      

        return img, meta, transform
    
def mp_ntl_mask(ntl_p, df, col='geometry', desc = ''):
    """Run a multi-process masking operation to return numpy arrays extracted from the 
    NTL datasets in the ntl_p packages according to each of the geometries in the df GeoDataFrame, using the 
    geometry column col """
    tasks = [  (year, r.unique_id, r[col]) for idx,r in df.iterrows() for year in list(range(1992, 2018+1))]

    # Run the extraction tasks in parallel
    # First, define the function we will run in parallel
    def _f(year, sez_id, geo):
        try:
            return (year, sez_id, load_ntl(ntl_p, year, [geo])[0])
        except Exception as e:
            return (year, sez_id, e)

    # Second, run the tasks
    patches = Parallel(prefer='threads')(delayed(_f)(*t) for t in tqdm(tasks, desc=col+' '+desc))

    exc = [(year, sez_id,  e) for year, sez_id,  e in patches if isinstance(e, Exception)]

    return patches, exc, tasks


def make_rings(df, r1, r2=None):
    """Return geometries for rings around the points ( or other geometry ) in df. If not specified, 
    r2 is selected so the area of the ring is equal to the area of the circle described by r1, 
    r2 = sqrt(2)*r1"""

    if r2 is None:
        r2 = np.sqrt(2)*r1
    
    buf_r1 = df.to_crs(3395).buffer(r1)
    buf_r2 = df.to_crs(3395).buffer(r2)

    ring = buf_r2.difference(buf_r1)
    
    # Check that relative difference is close to zero --> areas are equal
    rel_diff = ((buf_r1.area - ring.area)/buf_r1.area).round(8)
    #print('!!!!',rel_diff.sum(), r1, r2, buf_r1.area, ring.area)
    assert rel_diff.sum() == 0, (r1, r2, rel_diff.sum())
    
    return ring

def build_ring_sums(ntl_p, sez_df, radius):
    import geopandas as gpd 
    
    sez_rings = make_rings(sez_df, radius)

    sr = gpd.GeoDataFrame(sez_rings.to_frame('ring'), geometry='ring')
    sr['ring_area'] = sez_rings.area
    
    sez_df = sez_df.join(sr.to_crs(4326))

    patches, exc, tasks = mp_ntl_mask(ntl_p, sez_df.to_crs(4326), 'ring', desc=f'ring {radius}')

    rows = [ (e[0],e[1], np.nansum(e[2]), np.count_nonzero(~np.isnan(e[2]))) for e in patches ]

    return (sez_df, patches, exc,
            pd.DataFrame(rows, columns=['year','unique_id','ring_pix_sum', 'ring_pix_count']) )
