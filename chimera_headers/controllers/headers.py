# This is an example of an simple instrument.
from math import pi, cos, sin

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ObjectNotFoundException, ChimeraException
from chimera.util.image import ImageUtil
import datetime


class Headers(ChimeraObject):

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
        Returns the modified metadata for a camera instrument.
        '''
        extra_header_info = self.instrument.get_extra_header_info()
        md = [('DATE-OBS', ImageUtil.formatDate(extra_header_info.get("frame_start_time",
                                                                                        datetime.datetime.utcnow())),
               'Custom. Date exposure started'),
              ("EXPTIME", float(request['exptime']) or -1, "Custom. exposure time in seconds"),
              ('IMAGETYP', request['type'].strip(), 'Custom. Image type'),
              ('SHUTTER', str(request['shutter']), 'Custom. Requested shutter state'),
              ('INSTRUME', str(self.instrument['camera_model']), 'Custom. Name of instrument'),
              ('CCD',    str(self.instrument['ccd_model']), 'Custom. CCD Model'),
              ('CCD_DIMX', self.instrument.getPhysicalSize()[0], 'Custom. CCD X Dimension Size'),
              ('CCD_DIMY', self.instrument.getPhysicalSize()[1], 'Custom. CCD Y Dimension Size'),
              ('CCDPXSZX', self.instrument.getPixelSize()[0], 'Custom. CCD X Pixel Size [micrometer]'),
              ('CCDPXSZY', self.instrument.getPixelSize()[1], 'Custom. CCD Y Pixel Size [micrometer]')]

        if "frame_temperature" in extra_header_info.keys():
              md += [('CCD-TEMP', extra_header_info["frame_temperature"],
                      'Custom. CCD Temperature at Exposure Start [deg. C]')]

        focal_length = self.instrument["telescope_focal_length"]
        if focal_length is not None:  # If there is no telescope_focal_length defined, don't store WCS
            mode, binning, top, left, width, height = self.instrument._getReadoutModeInfo(request["binning"], request["window"])
            binFactor = extra_header_info.get("binning_factor", 1.0)
            pix_w, pix_h = self.instrument.getPixelSize()
            focal_length = self.instrument["telescope_focal_length"]

            scale_x = binFactor * (((180 / pi) / focal_length) * (pix_w * 0.001))
            scale_y = binFactor * (((180 / pi) / focal_length) * (pix_h * 0.001))

            full_width, full_height = self.instrument.getPhysicalSize()
            CRPIX1 = ((int(full_width / 2.0)) - left) - 1
            CRPIX2 = ((int(full_height / 2.0)) - top) - 1

            # Adding WCS coordinates according to FITS standard.
            # Quick sheet: http://www.astro.iag.usp.br/~moser/notes/GAi_FITSimgs.html
            # http://adsabs.harvard.edu/abs/2002A%26A...395.1061G
            # http://adsabs.harvard.edu/abs/2002A%26A...395.1077C
            md += [("CRPIX1", CRPIX1, "Custom. coordinate system reference pixel"),
                   ("CRPIX2", CRPIX2, "Custom. coordinate system reference pixel"),
                   ("CD1_1",  scale_x * cos(self.instrument["rotation"]*pi/180.), "Custom. transformation matrix element (1,1)"),
                   ("CD1_2", -scale_y * sin(self.instrument["rotation"]*pi/180.), "Custom. transformation matrix element (1,2)"),
                   ("CD2_1", scale_x * sin(self.instrument["rotation"]*pi/180.), "Custom. transformation matrix element (2,1)"),
                   ("CD2_2", scale_y * cos(self.instrument["rotation"]*pi/180.), "Custom. transformation matrix element (2,2)")]

        return md


    def getMetadataFocuser(self, request):
        '''
        Returns the modified metadata for a focuser instrument.
        '''
        return [('FOCUSER', str(self.instrument['model']), 'Custom. Focuser Model.'),
                ('FOCUS', self.instrument.getPosition(), 'Custom. Focuser position used for this observation.')]
                # ('FOCUSTEM', self.focuser.getTemperature(), 'Focuser Temperature at Exposure End [deg. C]']

    def getMetadataDome(self, request):
        '''
        Returns the modified metadata for a dome instrument.
        '''
        if self.instrument.isSlitOpen():
            slit = 'Open'
        else:
            slit = 'Closed'

        return [('DOME_MDL', str(self.instrument['model']), 'Custom. Dome Model'),
                ('DOME_TYP', str(self.instrument['style']), 'Custom. Dome Type'),
                ('DOME_TRK', str(self.instrument['mode']), 'Custom. Dome Tracking/Standing'),
                ('DOME_SLT', str(slit), 'Custom. Dome slit status')]

    def getMetadataTelescope(self, request):
        '''
        Returns the modified metadata for a telescope instrument.
        '''
        return [('TELESCOP', self.instrument['model'], 'Custom. Telescope Model'),
                ('OPTICS',   self.instrument['optics'], 'Custom. Telescope Optics Type'),
                ('MOUNT', self.instrument['mount'], 'Custom. Telescope Mount Type'),
                ('APERTURE', self.instrument['aperture'], 'Custom. Telescope aperture size [mm]'),
                ('F_LENGTH', self.instrument['focal_length'], 'Custom. Telescope focal length [mm]'),
                ('F_REDUCT', self.instrument['focal_reduction'], 'Custom. Telescope focal reduction'),
                # TODO: Convert coordinates to proper equinox
                # TODO: How to get ra,dec at start of exposure (not end)
                ('RA', self.instrument.getRa().toHMS().__str__(), 'Custom. Right ascension of the observed object'),
                ('DEC', self.instrument.getDec().toDMS().__str__(), 'Custom. Declination of the observed object'),
                ("EQUINOX", 2000.0, "Custom. coordinate epoch"),
                ('ALT', self.instrument.getAlt().toDMS().__str__(), 'Custom. Altitude of the observed object'),
                ('AZ', self.instrument.getAz().toDMS().__str__(), 'Custom. Azimuth of the observed object'),
                ("WCSAXES", 2, "Custom. wcs dimensionality"),
                ("RADESYS", "ICRS", "Custom. frame of reference"),
                ("CRVAL1", self.instrument.getTargetRaDec().ra.D, "Custom. coordinate system value at reference pixel"),
                ("CRVAL2", self.instrument.getTargetRaDec().dec.D, "Custom. coordinate system value at reference pixel"),
                ("CTYPE1", 'RA---TAN', "Custom. name of the coordinate axis"),
                ("CTYPE2", 'DEC--TAN', "Custom. name of the coordinate axis"),
                ("CUNIT1", 'deg', "Custom. units of coordinate value"),
                ("CUNIT2", 'deg', "Custom. units of coordinate value")]


    def getMetadataWeatherStation(self, request):
        return []  #FIXME

    def getMetadataSite(self, request):
        return [('SITE', self.instrument['name'], 'Custom. Site name (in config)'),
                ('LATITUDE', str(self.instrument['latitude']), 'Custom. Site latitude'),
                ('LONGITUD', str(self.instrument['longitude']), 'Custom. Site longitude'),
                ('ALTITUDE', str(self.instrument['altitude']), 'Custom. Site altitude')]
