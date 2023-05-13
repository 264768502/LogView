# -*- coding: utf-8 -*-
ERROR_KEYWORDS = (
    u'fault addr',                                  # Process crash
    u'CRC check failed, Bootcode loading is not correct',
    u'(Cannot allocate memory)',
    u'Out of memory',
    u'cannot locate symbol',
    u'Failed to start audio',                       # Marvell
    u'memory_engine_allocate failed',               # Marvell
    u'ion_dump_backtrace',                          # Marvell
    u'kernel MV_SHM_Base_Malloc malloc shm fail',   # Marvell
    u'shm_lowmem_killer send sigkill',              # Marvell
    u'memory_engine_allocate failed',               # Marvell
    u'Resolution of curr and next frames are not equal',
    u'Received Error interrupt',                    # Marvell
    u'Failed to construct surface',                 # Marvell
    u'assert fail',                                 # Marvell
    u'message from agent devices, pe agent',        # Marvell
    u'couldn\'t set app parameters',                # Marvell
    u'MV_PE_StreamBufAllocate',                     # Marvell
    u'PQService: Cannot read the file',             # Marvell
    u'Vdec Assert',                                 # Marvell
    u'mb error happens',                            # Marvell
    u'VDEC:BUFDIS Reuse invalid display BD',        # Marvell
    #u'Report one video loss event',
    u'ADEC !!! ASSERT FAIL !!!',                    # Marvell
    u'SetState to VDEC_STATE_WAIT_OUTPUT_BUFFER',   # Marvell
    u'TA VPP ERROR',                                # Marvell
    u'@err>>',                                      # Marvell
    u'ADEC Decoder outbuf overflow',                # Marvell
    u'DRMSRV Failed',                               # Marvell
    u'DRM_E_FAIL',                                  # Marvell
    u'AMP function call return an error',           # Marvell
    u'Amp1',                                        # Marvell
    u'Amp0',                                        # Marvell
    u'WARNING: at',                                 # Marvell
    u'BUG: at',                                     # Marvell
    u'I/DEBUG',                                     # Android Fatal logging
    # u'F DEBUG',                                     # Android Fatal logging
    # u' F ',                                         # Android Fatal logging
    # u' F/',                                         # Android Fatal logging
    u'ANR',                                         # Android
    u'binderDied',                                  # Android
    u'Throwing OutOfMemoryError',                   # Android
    u'died',                                        # Normal Error Keyword
    u'fatal',                                       # Normal Error Keyword
    u'FATAL',                                       # Normal Error Keyword
    u'Exception',                                   # Normal Error Keyword
    u'Segment fault',                               # Normal Error Keyword
    u'kernel panic',                                # Normal Error Keyword
    u'destroyed',                                   # Normal Error Keyword
    u'OVERFLOW',                                    # Normal Error Keyword
    u'system no response',
    u'FAIL case',
    u'system.err',
    u'Fail',
)
