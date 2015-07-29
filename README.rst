chimera-headers controller plugin template
==========================================

This is a template plugin for the chimera observatory control system https://github.com/astroufsc/chimera.

This plugin is intended to be a starting point for a header metadata change. Observatories sometimes haves header
standard requirements which are not met by chimera standard headers, so one way to circumvent this is to have a
controller which defines new ``getMetadata()`` methods for all instruments. This plugin is an example of how it could be
done. An advanced knowledge of Python and the chimera inner workings could be necessary to create an usable plugin out
of this template. In case of doubts on how to do it, please contact us trough one of the options on the end of this page.

*NOTE:* These keywords are fixed on the code and cannot be changed using this method: ``SIMPLE``, ``BITPIX``, ``NAXIS``,
``NAXIS1``, ``NAXIS2``, ``EXTEND``, ``BZERO``, ``DATE``, ``AUTHOR``, ``OBJECT``, ``CHECKSUM``, ``DATASUM`` and ``CHM_ID``

Usage
-----

Clone this template to another repository and change the ``chimera_headers`` directory to another appropriate name. Use
fake instruments to begin testing the changes on the controller (``controllers/headers.py``), then go on with tests on
real hardware. A good starting point to understand how chimera objects works is the chimera documentation for developers:
https://github.com/astroufsc/chimera/blob/master/docs/site/chimerafordevs.rst#chimera-objects

Installation
------------

::

    pip install -U git+https://github.com/astroufsc/chimera-headers.git


Configuration Example
---------------------

Even having all the code on one controller, you have to instantiate a chimera controller for each Instrument (or Site)
you want to override the ``getMetadata()`` method.

::

    controllers:
      - type: Headers
        name: focuser
        focuser: /FakeFocuser/fake

      - type: Headers
        name: telescope
        telescope: /FakeTelescope/fake

      - type: Headers
        name: dome
        dome: /FakeDome/fake

      - type: Headers
        name: camera
        camera: /FakeCamera/fake

      - type: Headers
        name: site
        site: /Site/MyObservatory

*NOTE:* ``chimera-headers`` does not checks if the location of the object is of the type to be configured, so if you do
``dome: /FakeCamera/fake`` you won't be alerted by your mistake.

Modified header example
-----------------------

Below an example of two test image headers. The leftmost is without this plugin configured, the rightmost is with it
configured for all the fake instruments. The header keywords modified by this controller haves "Custom. " added to their
comments.

::

    SIMPLE  =                    T / conforms to FITS standard                      	SIMPLE  =                    T / conforms to FITS standard
    BITPIX  =                   16 / array data type                                	BITPIX  =                   16 / array data type
    NAXIS   =                    2 / number of array dimensions                     	NAXIS   =                    2 / number of array dimensions
    NAXIS1  =                  512                                                  	NAXIS1  =                  512
    NAXIS2  =                  512                                                  	NAXIS2  =                  512
    EXTEND  =                    T                                                  	EXTEND  =                    T
    BZERO   =                32768                                                  	BZERO   =                32768
    DATE    = '2015-07-29T16:00:28.382240' / date of file creation                  	DATE    = '2015-07-29T15:15:22.233742' / date of file creation
    AUTHOR  = 'chimera '           / Observatory Automation System                  	AUTHOR  = 'chimera '           / Observatory Automation System
    OBJECT  = 'object  '           / name of observed object                        	OBJECT  = 'object  '           / name of observed object
    SITE    = 'T80S    '           / Site name (in config)                          	SITE    = 'T80S    '           / Custom. Site name (in config)
    LATITUDE= '-70:48:20.480'      / Site latitude                                  	LATITUDE= '-70:48:20.480'      / Custom. Site latitude
    LONGITUD= '-30:10:04.310'      / Site longitude                                 	LONGITUD= '-30:10:04.310'      / Custom. Site longitude
    ALTITUDE= '2187    '           / Site altitude                                  	ALTITUDE= '2187    '           / Custom. Site altitude
    DATE-OBS= '2015-07-29T16:00:27.182012' / Date exposure started                  	DATE-OBS= '2015-07-29T15:15:21.082973' / Custom. Date exposure started
    EXPTIME =                  1.0 / exposure time in seconds                       	EXPTIME =                  1.0 / Custom. exposure time in seconds
    IMAGETYP= 'object  '           / Image type                                     	IMAGETYP= 'object  '           / Custom. Image type
    SHUTTER = 'OPEN    '           / Requested shutter state                        	SHUTTER = 'OPEN    '           / Custom. Requested shutter state
    INSTRUME= 'Fake Cameras Inc.'  / Name of instrument                             	INSTRUME= 'Fake Cameras Inc.'  / Custom. Name of instrument
    CCD     = 'Fake CCDs Inc.'     / CCD Model                                      	CCD     = 'Fake CCDs Inc.'     / Custom. CCD Model
    CCD_DIMX=                  512 / CCD X Dimension Size                           	CCD_DIMX=                  512 / Custom. CCD X Dimension Size
    CCD_DIMY=                  512 / CCD Y Dimension Size                           	CCD_DIMY=                  512 / Custom. CCD Y Dimension Size
    CCDPXSZX=                    9 / CCD X Pixel Size [micrometer]                  	CCDPXSZX=                    9 / Custom. CCD X Pixel Size [micrometer]
    CCDPXSZY=                    9 / CCD Y Pixel Size [micrometer]                  	CCDPXSZY=                    9 / Custom. CCD Y Pixel Size [micrometer]
    CRPIX1  =                  255 / coordinate system reference pixel              	CRPIX1  =                  255 / Custom. coordinate system reference pixel
    CRPIX2  =                  255 / coordinate system reference pixel              	CRPIX2  =                  255 / Custom. coordinate system reference pixel
    CD1_1   = 0.000515662015617741 / transformation matrix element (1,1)            	CD1_1   = 0.000515662015617741 / Custom. transformation matrix element (1,1)
    CD1_2   =                 -0.0 / transformation matrix element (1,2)            	CD1_2   =                 -0.0 / Custom. transformation matrix element (1,2)
    CD2_1   =                  0.0 / transformation matrix element (2,1)            	CD2_1   =                  0.0 / Custom. transformation matrix element (2,1)
    CD2_2   = 0.000515662015617741 / transformation matrix element (2,2)            	CD2_2   = 0.000515662015617741 / Custom. transformation matrix element (2,2)
    DOME_MDL= 'Fake Domes Inc.'    / Dome Model                                     	DOME_MDL= 'Fake Domes Inc.'    / Custom. Dome Model
    DOME_TYP= 'Classic '           / Dome Type                                      	DOME_TYP= 'Classic '           / Custom. Dome Type
    DOME_TRK= 'Track   '           / Dome Tracking/Standing                         	DOME_TRK= 'Track   '           / Custom. Dome Tracking/Standing
    DOME_SLT= 'Closed  '           / Dome slit status                               	DOME_SLT= 'Closed  '           / Custom. Dome slit status
    FOCUSER = 'Fake Focus v.1'     / Focuser Model                                  	FOCUSER = 'Fake Focus v.1'     / Custom. Focuser Model.
    FOCUS   =                 3500 / Focuser position used for this observation     	FOCUS   =                 3500 / Custom. Focuser position used for this observat
    TELESCOP= 'Fake Telescopes Inc.' / Telescope Model                              	TELESCOP= 'Fake Telescopes Inc.' / Custom. Telescope Model
    OPTICS  = 'Newtonian'          / Telescope Optics Type                          	OPTICS  = 'Newtonian'          / Custom. Telescope Optics Type
    MOUNT   = 'Mount type Inc.'    / Telescope Mount Type                           	MOUNT   = 'Mount type Inc.'    / Custom. Telescope Mount Type
    APERTURE=                100.0 / Telescope aperture size [mm]                   	APERTURE=                100.0 / Custom. Telescope aperture size [mm]
    F_LENGTH=               1000.0 / Telescope focal length [mm]                    	F_LENGTH=               1000.0 / Custom. Telescope focal length [mm]
    F_REDUCT=                  1.0 / Telescope focal reduction                      	F_REDUCT=                  1.0 / Custom. Telescope focal reduction
    RA      = '09:14:03.315'       / Right ascension of the observed object         	RA      = '08:29:03.740'       / Custom. Right ascension of the observed object
    DEC     = '-03:00:00.000'      / Declination of the observed object             	DEC     = '-03:00:00.000'      / Custom. Declination of the observed object
    EQUINOX =               2000.0 / coordinate epoch                               	EQUINOX =               2000.0 / Custom. coordinate epoch
    ALT     = '+21:09:31.122'      / Altitude of the observed object                	ALT     = '+21:09:51.623'      / Custom. Altitude of the observed object
    AZ      = '+340:14:14.936'     / Azimuth of the observed object                 	AZ      = '+340:17:31.456'     / Custom. Azimuth of the observed object
    WCSAXES =                    2 / wcs dimensionality                             	WCSAXES =                    2 / Custom. wcs dimensionality
    RADESYS = 'ICRS    '           / frame of reference                             	RADESYS = 'ICRS    '           / Custom. frame of reference
    CRVAL1  =    138.5138112503431 / coordinate system value at reference pixel     	CRVAL1  =    127.2655845654916 / Custom. coordinate system value at reference pi
    CRVAL2  =   -3.000000000000017 / coordinate system value at reference pixel     	CRVAL2  =   -3.000000000000017 / Custom. coordinate system value at reference pi
    CTYPE1  = 'RA---TAN'           / name of the coordinate axis                    	CTYPE1  = 'RA---TAN'           / Custom. name of the coordinate axis
    CTYPE2  = 'DEC--TAN'           / name of the coordinate axis                    	CTYPE2  = 'DEC--TAN'           / Custom. name of the coordinate axis
    CUNIT1  = 'deg     '           / units of coordinate value                      	CUNIT1  = 'deg     '           / Custom. units of coordinate value
    CUNIT2  = 'deg     '           / units of coordinate value                      	CUNIT2  = 'deg     '           / Custom. units of coordinate value
    CHECKSUM= 'ZhTQdeQPZeQPdeQP'   / HDU checksum updated 2015-07-29T18:00:29       	CHECKSUM= 'U8a3U5Z3U5a3U5Y3'   / HDU checksum updated 2015-07-29T17:15:23
    DATASUM = '215090118'          / data unit checksum updated 2015-07-29T18:00:29 	DATASUM = '192873200'          / data unit checksum updated 2015-07-29T17:15:23
    CCD-TEMP=    20.11741179427901 / CCD Temperature at Exposure Start [deg. C]     	CCD-TEMP=    20.30499427111227 / Custom. CCD Temperature at Exposure Start [deg.
    CHM_ID  = '0ab51b1a2faf217c411d32dbbafcf4a7f6'                                  	CHM_ID  = '0ab51b1a2599217c3cfc2e650621477d2c'
    END                                                                             	END


Contact
-------

For more information, contact us on chimera's discussion list:
https://groups.google.com/forum/#!forum/chimera-discuss

Bug reports and patches are welcome and can be sent over our GitHub page:
https://github.com/astroufsc/chimera-headers/