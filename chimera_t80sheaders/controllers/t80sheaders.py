from math import pi, cos, sin

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ObjectNotFoundException, ChimeraException



#####
#####  T80S Header controller. This is valid only for the T80S telescope.
#####
from chimera.util.image import ImageUtil
import datetime


class T80SHeaders(ChimeraObject):

    # Configuration.
    #
    #        This controller admits only one instrument to be controlled at time. If you need more, please add more
    #    instances of this controller on chimera.config.
    #

    __config__ = {"camera": None,
                  "dome": None,
                  "focuser": None,
                  "site": None,
                  "telescope": None,
                  "weatherstation": None}

    def __init__(self):
        ChimeraObject.__init__(self)

    def __start__(self):
        # Define a dictionary where each type of instrument is associated to one metadata function.
        # This will be used on getMetadata()
        self._metadata_function = {"camera": self.getMetadataCamera,
                                   "dome": self.getMetadataDome,
                                   "focuser": self.getMetadataFocuser,
                                   "telescope": self.getMetadataTelescope,
                                   "site": self.getMetadataSite,
                                   "weatherstation": self.getMetadataWeatherStation,
                                   }
        # Get instrument type and location
        self.instrument_type, self.instrument_location = self._get_instrument_name()
        self.instrument = self.getInstument()
        self.log.info("Overriding %s instrument metadata methods to the ones from %s" % (self.instrument_location,
                                                                                         self.getLocation()))
        # Set the instrument getMetadata location to this class.
        self.instrument.setMetadataMethod(self.getLocation())

    def _get_instrument_name(self):
        '''
        This controller admits only one instrument to be controlled at time. If you need more, please add more
        instances of this controller on chimera.config.

        :return instrument_type: Type of the instrument. E.g. telescope, focuser, ...
        :return instrument_location: Location of the instrument. E.g. /Telescope/0 or /FakeTelescope/fake
        '''

        # Get instrument locations
        keys = list(self.__config__.keys())
        values = [self[k] for k in keys]
        config_dict = dict(zip(keys, values))
        instrument = [[k, v] for k, v in config_dict.iteritems() if v is not None]

        # Check if there is more than one instrument on the configuration
        if len(instrument) != 1:
            self.log.error("Number of instruments different of one at %s: %s" % (self.getLocation(), instrument))
            if len(instrument) > 1:
                raise ChimeraException(
                    "%s controller configuration must have only ONE type of instrument!" % self.getLocation())
            else:
                raise ChimeraException(
                    "%s controller configuration must have at least ONE type of instrument!" % self.getLocation())
        else:
            return instrument[0][0], instrument[0][1]  # type, location

    def getInstument(self):
        '''
        :return: Instrument class.
        '''
        try:
            p = self.getManager().getProxy(self.instrument_location, lazy=True)
            if not p.ping():
                return False
            else:
                return p
        except ObjectNotFoundException:
            return False

    def getMetadata(self, request):
        return self._metadata_function[self.instrument_type](request)


    #### METADATA FUNCTIONS ####

    def getMetadataCamera(self, request):
        '''
        Returns the modified metadata for a camera instrument. On T80CamS most of the header metadata is included
        by the camera driver itself, directly during readout operation. Here we just gather info about the filterwheel.
        '''

        return [('FILTER', str(self.instrument.getFilter()), 'Filter used for this observation')]


    def getMetadataFocuser(self, request):
        '''
        Returns the modified metadata for a focuser instrument.
        '''
        x, y, z, u, v = self.getRealPosition()
        dx, dy, dz, du, dv = self.getOffset()

        return [('HIERARCH T80S TEL FOCU HEX X', ' %f '%x, ' Current hexapod position in x (mm) '),
                ('HIERARCH T80S TEL FOCU HEX Y', ' %f '%y, ' Current hexapod position in y (mm) '),
                ('HIERARCH T80S TEL FOCU HEX Z', ' %f '%z, ' Current hexapod position in z (mm) '),
                ('HIERARCH T80S TEL FOCU HEX U', ' %f '%u, ' Current hexapod position in U (degree) '),
                ('HIERARCH T80S TEL FOCU HEX V', ' %f '%v, ' Current hexapod position in V (degree) '),
                ('HIERARCH T80S TEL FOCU HEX DX', ' %f '%dx, ' Current hexapod offset in x (mm) '),
                ('HIERARCH T80S TEL FOCU HEX DY', ' %f '%dy, ' Current hexapod offset in y (mm) '),
                ('HIERARCH T80S TEL FOCU HEX DZ', ' %f '%dz, ' Current hexapod offset in z (mm) '),
                ('HIERARCH T80S TEL FOCU HEX DU', ' %f '%du, ' Current hexapod offset in U (degree) '),
                ('HIERARCH T80S TEL FOCU HEX DV', ' %f '%dv, ' Current hexapod offset in V (degree) '),
                ('HIERARCH T80S TEL FOCU LEN', ' %f '%z, ' Current focus position (mm) '),
                ('HIERARCH T80S TEL FOCU SCALE', ' 55.56', ' Focus scale (arcsec/mm) '),  #TODO
                ('HIERARCH T80S TEL FOCU VALUE', ' %f '%dz, ' Current focus offset (mm) '),
                ]


    def getMetadataDome(self, request):
        '''
        Returns the modified metadata for a dome instrument.
        '''
        if self.instrument.isSlitOpen():
            slit = 'Open'
        else:
            slit = 'Closed'

        return [('DOME_MDL', str(self.instrument['model']), 'Dome Model'),
                ('DOME_TYP', str(self.instrument['style']), 'Dome Type'),
                ('DOME_TRK', str(self.instrument['mode']), 'Dome Tracking/Standing'),
                ('DOME_SLT', str(slit), 'Dome slit status'),
                ('HIERARCH OAJ TEL DOME AZ', str(self.instrument.getAz().D), 'dome azimuth'),]

    def getMetadataTelescope(self, request):
        '''
        Returns the modified metadata for a telescope instrument.
        '''
        # return [('TELESCOP', self.instrument['model'], 'Custom. Telescope Model'),
        #         ('OPTICS',   self.instrument['optics'], 'Custom. Telescope Optics Type'),
        #         ('MOUNT', self.instrument['mount'], 'Custom. Telescope Mount Type'),
        #         ('APERTURE', self.instrument['aperture'], 'Custom. Telescope aperture size [mm]'),
        #         ('F_LENGTH', self.instrument['focal_length'], 'Custom. Telescope focal length [mm]'),
        #         ('F_REDUCT', self.instrument['focal_reduction'], 'Custom. Telescope focal reduction'),
        #         # TODO: Convert coordinates to proper equinox
        #         # TODO: How to get ra,dec at start of exposure (not end)
        #         ('RA', self.instrument.getRa().toHMS().__str__(), 'Custom. Right ascension of the observed object'),
        #         ('DEC', self.instrument.getDec().toDMS().__str__(), 'Custom. Declination of the observed object'),
        #         ("EQUINOX", 2000.0, "Custom. coordinate epoch"),
        sensors = self.instrument.getSensors()
        TM1 = ' INDEF '
        TM2 = ' INDEF '
        TFR = ' INDEF '
        TTR = ' INDEF '
        for entry in sensors:
            if "TM1" in entry[0]:
                TM1 = entry[1]
                continue
            elif "TM2" in entry[0]:
                TM2 = entry[1]
                continue
            elif "FrontRing" in entry[0]:
                TFR = entry[1]
                continue
            elif "TubeRod" in entry[0]:
                TTR = entry[1]
                continue

        return [('TELESCOP', self.instrument['model'], 'Telescope Model'),
                ('RA', self.instrument.getRa().toHMS().__str__(), 'Right ascension of the observed object'),
                ('DEC', self.instrument.getDec().toDMS().__str__(), 'Declination of the observed object'),
                ('ALT', self.instrument.getAlt().toDMS().__str__(), 'Custom. Altitude of the observed object'),
                ('AZ', self.instrument.getAz().toDMS().__str__(), 'Custom. Azimuth of the observed object'),
                ('AIRMASS', 1 / cos(pi / 2 - self.instrument.getAlt().R), 'air mass at the end of observation'),
                ("WCSAXES", 2, "wcs dimensionality"),
                ("RADESYS", "ICRS", "frame of reference"),
                ("CRVAL1", self.instrument.getTargetRaDec().ra.D, "coordinate system value at reference pixel"),
                ("CRVAL2", self.instrument.getTargetRaDec().dec.D, "coordinate system value at reference pixel"),
                ("CTYPE1", 'RA---TAN', "name of the coordinate axis"),
                ("CTYPE2", 'DEC--TAN', "name of the coordinate axis"),
                ("CUNIT1", 'deg', "units of coordinate value"),
                ("CUNIT2", 'deg', "units of coordinate value"),
                ("EQUINOX", 2000.0, "coordinate epoch"),
                ('HIERARCH T80S TEL OPER', 'CHIMERA'),
                ('HIERARCH T80S TEL FOCU LEN', self.instrument['focal_length'], ' Focal length (mm)'),
                ('HIERARCH T80S TEL EL START', self.instrument.getAlt().toD().__str__()),
                ('HIERARCH T80S TEL AZ START', self.instrument.getAz().toD().__str__()),
                ('HIERARCH T80S TEL PARANG START', self.instrument.getParallacticAngle().toD().__str__(), ' Parallactic angle at start (deg)'),
                ('HIERARCH T80S TEL TRAK STATUS', 'TRACKING GOOD', ' Tracking status'),  # TODO:
                ('HIERARCH T80S TEL AIRM START', 1 / cos(pi / 2 - self.instrument.getAlt().R), ' Airmass at start of exposure'),
                ('HIERARCH T80S TEL MIRR S1 TEMP', TM1, ' Primary mirror surface temperature'),
                ('HIERARCH T80S TEL MIRR S2 TEMP', TM2, ' Secondary mirror surface temperature'),
                ('HIERARCH T80S TEL FRONT RING TEMP', TFR, ' Telescope front ring temperature'),
                ('HIERARCH T80S TEL TUBE ROD TEMP', TTR, ' Telescope tube rod temperature'),
                ('HIERARCH T80S TEL POINT MODE', self.instrument.getPSOrientation()[1]),
                ('HIERARCH T80S DPR CATG', 'SCIENCE' if request.type == 'object' else 'CALIBRATION'),  # TODO:
                ('HIERARCH T80S DPR TYPE', request.type)]


    def getMetadataWeatherStation(self, request):
        # TODO: Weather station metadata.
        return [('HIERARCH T80S GEN AMBI WIND SPDMEAN', ' 4.90'),
                ('HIERARCH T80S GEN AMBI WIND SPDRMS', ' 4.92'),
                ('HIERARCH T80S GEN AMBI WIND DIRMEAN', ' 17.1'),
                ('HIERARCH T80S GEN AMBI WIND DIRRMS', ' 60.5'),
                ('HIERARCH T80S GEN AMBI RHUMMEAN', ' 10.4'),
                ('HIERARCH T80S GEN AMBI RHUMRMS', ' 10.4'),
                ('HIERARCH T80S GEN AMBI PRESMEAN', ' 811.66'),
                ('HIERARCH T80S GEN AMBI PRESRMS', ' 811.66'),
                ('HIERARCH T80S GEN AMBI TEMPMEAN', ' 7.402'),
                ('HIERARCH T80S GEN AMBI TEMPRMS', ' 7.414')]

    def getMetadataSite(self, request):
        return [('ORIGIN', self.instrument['name'], 'Site name (in config)'),
                ('LATITUDE', str(self.instrument['latitude']), 'Site latitude'),
                ('LONGITUD', str(self.instrument['longitude']), 'Site longitude'),
                ('ALTITUDE', str(self.instrument['altitude']), 'Site altitude'),
                ('HIERARCH T80S TEL GEOELEV', str(self.instrument['altitude'])),
                ('HIERARCH T80S TEL GEOLAT', str(self.instrument['latitude'].D)),
                ('HIERARCH T80S TEL GEOLON', str(self.instrument['longitude'].D))]