import numpy as np


class HeatIndex():

    def __init__(self):
        self.name = "Heat Index Function"
        self.description = ("This function combines ambient air temperature and relative humidity "
                            "to return apparent temperature in degrees Fahrenheit.")
        self.units = 'f'

    def getParameterInfo(self):
        return [
            {
                'name': 'temperature',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Temperature Raster",
                'description': "A single-band raster where pixel values represent ambient air temperature in Fahrenheit."
            },
            {
                'name': 'units',
                'dataType': 'string',
                'value': 'Fahrenheit',
                'required': True,
                'domain': ('Celsius', 'Fahrenheit', 'Kelvin'),
                'displayName': "Temperature Measured In",
                'description': "The unit of measurement associated with the input temperature raster. Output is always in Fahrenheit."
            },
            {
                'name': 'rh',
                'dataType': 'raster',
                'value': None,
                'required': True,
                'displayName': "Relative Humidity Raster",
                'description': ("A single-band raster where pixel values represent relative humidity as "
                                "a percentage value between 0 and 100.")
            },
        ]

    def getConfiguration(self, **scalars):
        return {
          'inheritProperties': 4 | 8,               # inherit all but the pixel type and NoData from the input raster
          'invalidateProperties': 2 | 4 | 8,        # invalidate statistics & histogram on the parent dataset because we modify pixel values. 
          'inputMask': False                        # Don't need input raster mask in .updatePixels(). Simply use the inherited NoData. 
        }

    def updateRasterInfo(self, **kwargs):
        kwargs['output_info']['bandCount'] = 1      # output is a single band raster
        kwargs['output_info']['statistics'] = ({'minimum': 0.0, 'maximum': 180}, )  # we know something about the stats of the outgoing HeatIndex raster. 
        kwargs['output_info']['histogram'] = ()     # we know nothing about the histogram of the outgoing raster.
        kwargs['output_info']['pixelType'] = 'f4'   # bit-depth of the outgoing HeatIndex raster based on user-specified parameters

        self.units = kwargs.get('units', 'Fahrenheit').lower()[0]
        return kwargs

    def updatePixels(self, tlc, shape, props, **pixelBlocks):
        t = np.array(pixelBlocks['temperature_pixels'], dtype='f4', copy=False)
        r = np.array(pixelBlocks['rh_pixels'], dtype='f4', copy=False)

        if self.units == 'k':
            t = (9./5. * (t - 273.15)) + 32.
        elif self.units == 'c':
            t = (9./5. * t) + 32.

        tr = t * r
        rr = r * r
        tt = t * t
        ttr = tt * r
        trr = t * rr
        ttrr = ttr * r

        outBlock = (-42.379 + (2.04901523 * t) + (10.14333127 * r) - (0.22475541 * tr) 
                    - (6.83783e-3 * tt) - (5.481717e-2 * rr) + (1.22874e-3 * ttr) 
                    + (8.5282e-4 * trr) - (1.99e-6 * ttrr))

        pixelBlocks['output_pixels'] = outBlock.astype(props['pixelType'], copy=False)
        return pixelBlocks

    def updateKeyMetadata(self, names, bandIndex, **keyMetadata):
        if bandIndex == -1:                                     # update dataset-level key metadata
            keyMetadata['datatype'] = 'Scientific'
            keyMetadata['variable'] = 'HeatIndex'
        elif bandIndex == 0:
            keyMetadata['wavelengthmin'] = None                 # reset inapplicable band-specific key metadata 
            keyMetadata['wavelengthmax'] = None
            keyMetadata['bandname'] = 'HeatIndex'
        return keyMetadata

# ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ## ----- ##

"""
References:

    [1] Steadman, Robert G. "The assessment of sultriness. Part I: 
        A temperature-humidity index based on human physiology and clothing science." 
        Journal of Applied Meteorology 18.7 (1979): 861-873.

    [2] Steadman, Robert G. "The assessment of sultriness. Part II: 
        effects of wind, extra radiation and barometric pressure on apparent temperature." 
        Journal of Applied Meteorology 18.7 (1979): 874-885.

    [3] National Weather Service. "NWS Heat Index."
        http://www.nws.noaa.gov/om/heat/heat_index.shtml
"""
