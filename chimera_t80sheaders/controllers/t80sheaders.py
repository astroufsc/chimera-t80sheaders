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
        Returns the modified metadata for a camera instrument.
        '''
        extra_header_info = self.instrument.get_extra_header_info()
        md = [('DATE-OBS', ImageUtil.formatDate(extra_header_info.get("frame_start_time", datetime.datetime.utcnow())),
               'Date exposure started'),
              # ('FILENAME', ImageUtil.makeFilename(request["filename"])),
              ('EXPTIME', float(request['exptime']), "exposure time in seconds"),
              ('INSTRUME', str(self.instrument['camera_model']), 'Custom. Name of instrument'),]
        #       ('IMAGETYP', request['type'].strip(), 'Custom. Image type'),
        #       ('SHUTTER', str(request['shutter']), 'Custom. Requested shutter state'),
        #
        #       ('CCD',    str(self.instrument['ccd_model']), 'Custom. CCD Model'),
        #       ('CCD_DIMX', self.instrument.getPhysicalSize()[0], 'Custom. CCD X Dimension Size'),
        #       ('CCD_DIMY', self.instrument.getPhysicalSize()[1], 'Custom. CCD Y Dimension Size'),
        #       ('CCDPXSZX', self.instrument.getPixelSize()[0], 'Custom. CCD X Pixel Size [micrometer]'),
        #       ('CCDPXSZY', self.instrument.getPixelSize()[1], 'Custom. CCD Y Pixel Size [micrometer]')]
        #
        if "frame_temperature" in extra_header_info.keys():
            md += [('HIERARCH T80S DET TEMP', extra_header_info["frame_temperature"], ' Chip temperature (C) '),]
            # md += [('HIERARCH T80S INS TEMP', extra_header_info["frame_temperature"],
            #         'Instrument temperature (C) at end of exposure.')]

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
            md += [("CRPIX1", CRPIX1, "coordinate system reference pixel"),
                   ("CRPIX2", CRPIX2, "coordinate system reference pixel"),
                   ("CD1_1",  scale_x * cos(self.instrument["rotation"]*pi/180.), "transformation matrix element (1,1)"),
                   ("CD1_2", -scale_y * sin(self.instrument["rotation"]*pi/180.), "transformation matrix element (1,2)"),
                   ("CD2_1", scale_x * sin(self.instrument["rotation"]*pi/180.), "transformation matrix element (2,1)"),
                   ("CD2_2", scale_y * cos(self.instrument["rotation"]*pi/180.), "transformation matrix element (2,2)")]

        md += [ ('BUNIT', 'adu', 'physical units of the array values '),        #TODO:
                ('BLANK', -32768),        #TODO:
                ('BZERO', '0.0'),        #TODO:
                ('HIERARCH T80S INS OPER', 'CHIMERA'),
                ('HIERARCH T80S INS PIXSCALE', ' 0.7400', 'Pixel scale (arcsec)'),   #TODO: convert using self.instrument.getPixelSize()[0] and focal_lenght
                ('HIERARCH OAJ INS TEMP', ' -999', 'Instrument temperature'),
                ('HIERARCH T80S DET NAME', self.instrument["ccd_model"], 'Name of detector system '),        #TODO:
                ('HIERARCH T80S DET CCDS', ' 1 ', ' Number of CCDs in the mosaic'),        #TODO:
                ('HIERARCH T80S DET CHIPID', ' 0 ', ' Detector CCD identification'),        #TODO:
                ('HIERARCH T80S DET NX', self.instrument.getPhysicalSize()[0], ' Number of pixels along X '),
                ('HIERARCH T80S DET NY', self.instrument.getPhysicalSize()[1], ' Number of pixels along Y'),
                ('HIERARCH T80S DET PSZX', self.instrument.getPixelSize()[0], ' Size of pixel in X (mu) '),
                ('HIERARCH T80S DET PSZY', self.instrument.getPixelSize()[1], ' Size of pixel in Y (mu) '),
                ('HIERARCH T80S DET EXP TYPE', 'LIGHT', ' Type of exp as known to the CCD SW '),        #TODO:
                ('HIERARCH T80S DET READ MODE', 'SLOW', ' Readout method'),        #TODO:
                ('HIERARCH T80S DET READ SPEED', '1 MHz', ' Readout speed'),        #TODO:
                ('HIERARCH T80S DET READ CLOCK', 'DSI 68, High Gain, 1x1', ' Type of exp as known to the CCD SW'),        #TODO:
                ('HIERARCH T80S DET OUTPUTS', ' 2 ', 'Number of output ports used on chip'),        #TODO:
                ('HIERARCH T80S DET REQTIM', float(request['exptime']), 'Requested exposure time (sec)')]

        for i_output in range(1, 17):
            md += [
            ('HIERARCH T80S DET OUT%i ID' % i_output, ' 00 ', ' Identification for OUT1 readout port '),        #TODO:
            ('HIERARCH T80S DET OUT%i X' % i_output, ' 1 ', ' X location of output in the chip. (lower left pixel)'),        #TODO:
            ('HIERARCH T80S DET OUT%i Y' % i_output, ' 1 ', ' Y location of output in the chip. (lower left pixel)'),        #TODO:
            ('HIERARCH T80S DET OUT%i NX' % i_output, ' 512',        #TODO:
             ' Number of image pixels read to port 1 in X. Not including pre or overscan'),        #TODO:
            ('HIERARCH T80S DET OUT%i NY' % i_output, ' 1024 ',        #TODO:
             ' Number of image pixels read to port 1 in Y. Not including pre or overscan'),        #TODO:
            ('HIERARCH T80S DET OUT%i IMSC' % i_output, ' [1:512,1:1024] ',        #TODO:
             ' Image region for OUT%i in format [xmin:xmax,ymin:ymax] '),        #TODO:
            ('HIERARCH T80S DET OUT%i PRSCX' % i_output, ''),
            ('HIERARCH T80S DET OUT%i PRSCY' % i_output, ''),
            ('HIERARCH T80S DET OUT%i OVSCX' % i_output, ''),
            ('HIERARCH T80S DET OUT%i OVSCY' % i_output,''),
            ('HIERARCH T80S DET OUT%i GAIN' % i_output, ' 1.12 ', ' Gain for output. Conversion from ADU to electron (e-/ADU)'),        #TODO:
            ('HIERARCH T80S DET OUT%i RON' % i_output, ' 9.8900 ', ' Readout-noise of OUT1 at selected Gain (e-)'),        #TODO:
            ('HIERARCH T80S DET OUT%i SATUR' % i_output, ' 100000.0 ', ' Saturation of OUT1 (e-)')        #TODO:
            ]
        md += [('FILTER', str(self.instrument.getFilter()), 'Filter used for this observation')]

        return md


    def getMetadataFocuser(self, request):
        '''
        Returns the modified metadata for a focuser instrument.
        '''
        return [('HIERARCH T80S TEL FOCU SCALE', ' 57.30', ' Focus scale (arcsec/mm)'),  #TODO
                ('HIERARCH T80S TEL FOCU VALUE', self.instrument.getPosition(), ' M2 setting (mm) ')] #TODO: Check if it is mm


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
                ('HIERARCH T80S TEL EL START', ' 69.62205 '),  # TODO:
                ('HIERARCH T80S TEL EL END', ' 69.49747 '),  # TODO:
                ('HIERARCH T80S TEL AZ START', ' 334.61893'),  # TODO:
                ('HIERARCH T80S TEL AZ END', ' 334.16395'),  # TODO:
                ('HIERARCH T80S TEL PARANG START', ' 142.27750', ' Parallactic angle at start (deg)'),  # TODO:
                ('HIERARCH T80S TEL PARANG END', ' 141.53369', ' Parallactic angle at end (deg) '),  # TODO:
                ('HIERARCH T80S TEL TRAK STATUS', 'TRACKING GOOD', ' Tracking status'),  # TODO:
                ('HIERARCH T80S TEL AIRM START', '1.06672 ', ' Airmass at start of exposure'),  # TODO:
                ('HIERARCH T80S TEL AIRM END', ' 1.06758 ', ' Airmass at end of exposure'),  # TODO:
                ('HIERARCH T80S TEL MIRR S1 TEMP', ' 16.06000 ', ' Mirror surface temperature'),  # TODO:
                ('HIERARCH T80S TEL POINT MODE', 'NORMAL'),  # TODO:
                ('HIERARCH T80S DPR CATG', 'SCIENCE'),  # TODO:
                ('HIERARCH T80S DPR TYPE', 'OBJECT')]  # TODO:


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