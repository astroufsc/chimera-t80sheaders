from math import pi, cos, sin

from astropy import units
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ObjectNotFoundException, ChimeraException
from chimera.interfaces.focuser import FocuserAxis


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
                  "weatherstation": None,
                  "seeingmonitor": None}

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
                                   "seeingmonitor": self.getMetadataSeeingMonitor
                                   }
        # Get instrument type and location
        self.instrument_type, self.instrument_location = self._get_instrument_name()
        self.instrument = self.getInstument()
        self.log.info("Overriding %s instrument metadata methods to the ones from %s" % (self.instrument_location,
                                                                                         self.getLocation()))
        # Set the instrument getMetadata location to this class.
        # This should include the ip and port, for the case the instrument is on a remote computer.
        # E.g.: 192.168.10.10:7666/Headers/mytelescope
        manager = self.getManager()
        self.instrument.setMetadataMethod('%s:%s%s' % (manager.getHostname(), manager.getPort(), self.getLocation()))

    def __stop__(self):
        # Unset the instrument getMetadata location to this class.
        self.instrument.setMetadataMethod(None)


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
        self.log.debug('Getting CAMERA HEADER')
        return [('FILTER', str(self.instrument.getFilter()), 'Filter used for this observation')]


    def getMetadataFocuser(self, request):
        '''
        Returns the modified metadata for a focuser instrument.
        '''
        # x, y, z, u, v = self.getPosition()
        # dx, dy, dz, du, dv = self.getOffset()
        self.log.debug('Getting FOCUSER HEADER')

        return [('HIERARCH T80S TEL FOCU HEX X', ' %f '%self.instrument.getPosition(FocuserAxis.X),
                 ' Current hexapod position in x (mm) '),
                ('HIERARCH T80S TEL FOCU HEX Y', ' %f '%self.instrument.getPosition(FocuserAxis.Y), ' Current hexapod position in y (mm) '),
                ('HIERARCH T80S TEL FOCU HEX Z', ' %f '%self.instrument.getPosition(FocuserAxis.Z), ' Current hexapod position in z (mm) '),
                ('HIERARCH T80S TEL FOCU HEX U', ' %f '%self.instrument.getPosition(FocuserAxis.U), ' Current hexapod position in U (degree) '),
                ('HIERARCH T80S TEL FOCU HEX V', ' %f '%self.instrument.getPosition(FocuserAxis.V), ' Current hexapod position in V (degree) '),
                ('HIERARCH T80S TEL FOCU HEX DX', ' %f '%self.instrument.getOffset(FocuserAxis.X), ' Current hexapod offset in x (mm) '),
                ('HIERARCH T80S TEL FOCU HEX DY', ' %f '%self.instrument.getOffset(FocuserAxis.Y), ' Current hexapod offset in y (mm) '),
                ('HIERARCH T80S TEL FOCU HEX DZ', ' %f '%self.instrument.getOffset(FocuserAxis.Z), ' Current hexapod offset in z (mm) '),
                ('HIERARCH T80S TEL FOCU HEX DU', ' %f '%self.instrument.getOffset(FocuserAxis.U), ' Current hexapod offset in U (degree) '),
                ('HIERARCH T80S TEL FOCU HEX DV', ' %f '%self.instrument.getOffset(FocuserAxis.V), ' Current hexapod offset in V (degree) '),
                ('HIERARCH T80S TEL FOCU LEN', ' %f '%self.instrument.getPosition(FocuserAxis.Z), ' Current focus position (mm) '),
                # ('HIERARCH T80S TEL FOCU SCALE', ' 55.56', ' Focus scale (arcsec/mm) '),  #TODO
                ('HIERARCH T80S TEL FOCU VALUE', ' %f '%self.instrument.getOffset(FocuserAxis.Z), ' Current focus offset (mm) '),
                ]


    def getMetadataDome(self, request):
        '''
        Returns the modified metadata for a dome instrument.
        '''
        self.log.debug('Getting DOME HEADER')
        if self.instrument.isSlitOpen():
            slit = 'Open'
        else:
            slit = 'Closed'

        return [
                # ('DOME_MDL', str(self.instrument['model']), 'Dome Model'), # TODO:
                # ('DOME_TYP', str(self.instrument['style']), 'Dome Type'),  #TODO:
                ('DOME_TRK', str(self.instrument.getMode()), 'Dome Tracking/Standing'),
                ('DOME_SLT', str(slit), 'Dome slit status'),
                ('HIERARCH T80S TEL DOME AZ', str(self.instrument.getAz().D), 'dome azimuth'),]

    def getMetadataTelescope(self, request):
        '''
        Returns the modified metadata for a telescope instrument.
        '''
        self.log.debug('Getting TELESCOPE HEADER')
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

        self.log.debug('Getting RA')
        ra = self.instrument.getRa()
        self.log.debug('Getting Dec')
        dec = self.instrument.getDec()
        self.log.debug('Getting Alt')
        alt = self.instrument.getAlt()
        self.log.debug('Getting Az')
        az = self.instrument.getAz()
        self.log.debug('All getters done...')
        return [('TELESCOP', self.instrument['model'], 'Telescope Model'),
                ('RA', ra.toHMS().__str__(), 'Right ascension of the observed object'),
                ('DEC', dec.toDMS().__str__(), 'Declination of the observed object'),
                ('ALT', alt.toDMS().__str__(), 'Custom. Altitude of the observed object'),
                ('AZ', az.toDMS().__str__(), 'Custom. Azimuth of the observed object'),
                ('AIRMASS', 1 / cos(pi / 2 - alt.R), 'air mass at the end of observation'),
                ("WCSAXES", 2, "wcs dimensionality"),
                ("RADESYS", "ICRS", "frame of reference"),
                ("CRVAL1", ra.D, "coordinate system value at reference pixel"),
                ("CRVAL2", dec.D, "coordinate system value at reference pixel"),
                ("CTYPE1", 'RA---TAN', "name of the coordinate axis"),
                ("CTYPE2", 'DEC--TAN', "name of the coordinate axis"),
                ("CUNIT1", 'deg', "units of coordinate value"),
                ("CUNIT2", 'deg', "units of coordinate value"),
                ("EQUINOX", 2000.0, "coordinate epoch"),
                ('HIERARCH T80S TEL OPER', 'CHIMERA'),
                ('HIERARCH T80S TEL FOCU LEN', self.instrument['focal_length'], ' Focal length (mm)'),
                ('HIERARCH T80S TEL EL START', alt.toD().__str__()),
                ('HIERARCH T80S TEL AZ START', az.toD().__str__()),
                ('HIERARCH T80S TEL PARANG START', self.instrument.getParallacticAngle().toD().__str__(), ' Parallactic angle at start (deg)'),
                # ('HIERARCH T80S TEL TRAK STATUS', 'TRACKING GOOD', ' Tracking status'),  # TODO:
                ('HIERARCH T80S TEL AIRM START', 1 / cos(pi / 2 - alt.R), ' Airmass at start of exposure'),
                ('HIERARCH T80S TEL MIRR S1 TEMP', TM1, ' Primary mirror surface temperature'),
                ('HIERARCH T80S TEL MIRR S2 TEMP', TM2, ' Secondary mirror surface temperature'),
                ('HIERARCH T80S TEL FRONT RING TEMP', TFR, ' Telescope front ring temperature'),
                ('HIERARCH T80S TEL TUBE ROD TEMP', TTR, ' Telescope tube rod temperature'),
                ('HIERARCH T80S TEL POINT MODE', self.instrument.getPSOrientation()[1]),
                ('HIERARCH T80S DPR CATG', 'SCIENCE' if request["type"] == 'object' else 'CALIBRATION'),  # TODO:
                ('HIERARCH T80S DPR TYPE', request["type"])]


    def getMetadataWeatherStation(self, request):
        # TODO: Weather station metadata.
        self.log.debug('Getting WEATHER STATION HEADER')
        return [('HIERARCH T80S GEN AMBI WIND SPDMEAN', self.instrument.wind_speed().value),
                ('HIERARCH T80S GEN AMBI WIND DIRMEAN', self.instrument.wind_dir().value),
                ('HIERARCH T80S GEN AMBI RHUMMEAN', self.instrument.humidity().value),
                ('HIERARCH T80S GEN AMBI PRESMEAN', self.instrument.pressure().value),
                ('HIERARCH T80S GEN AMBI TEMPMEAN', self.instrument.temperature().value),
                ]

    def getMetadataSeeingMonitor(self, request):
        self.log.debug('Getting SEEING MONITOR HEADER')
        return [('SEEMOD', str(self.instrument['model']), 'Seeing monitor Model'),
                ('SEETYP', str(self.instrument['type']), 'Seeing monitor type'),
                ('SEEVAL', self.instrument.seeing(unit=units.arcsec).value, '[arcsec] Seeing value'),
                ('SEEFLU', self.instrument.flux(unit=units.count).value, '[counts] Star flux value'),
                ('SEEDAT', self.instrument.obs_time().strftime("%Y-%m-%dT%H:%M:%S.%f"), 'UT time of the seeing observation')
                ]

    def getMetadataSite(self, request):
        self.log.debug('Getting SITE HEADER')
        return [('ORIGIN', self.instrument['name'], 'Site name (in config)'),
                ('LATITUDE', str(self.instrument['latitude']), 'Site latitude'),
                ('LONGITUD', str(self.instrument['longitude']), 'Site longitude'),
                ('ALTITUDE', str(self.instrument['altitude']), 'Site altitude'),
                ('TIMESYS', 'UTC'),
                ('HIERARCH T80S TEL GEOELEV', str(self.instrument['altitude'])),
                ('HIERARCH T80S TEL GEOLAT', str(self.instrument['latitude'].D)),
                ('HIERARCH T80S TEL GEOLON', str(self.instrument['longitude'].D))]