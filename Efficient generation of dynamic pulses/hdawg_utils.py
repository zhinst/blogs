# Copyright (C) 2021 Zurich Instruments
#
# This software may be modified and distributed under the terms
# of the MIT license. See the LICENSE file for details.

import zhinst.utils
import zhinst.ziPython as zi
import json, time
from packaging import version
from types import SimpleNamespace

class HDAWG_Core():
    ziPython_min = version.parse("21.8.20085")
    labone_min = version.parse("21.8.20085")
    hdawg_fw_min = version.parse("67742")

    def __init__(self, daq, device, awg_index):
        """Configure the device. Mode of 2 channels grouped
        
        Parameters
        ----------
        daq : ziDAQServer 
            The DAQ connection
        device : str
            The serial of the HDAWG
        awg_index: int
            The index of the AWG core
        """

        self.daq = daq
        self.device = device
        self.awg_index = awg_index

        self.daq.connectDevice(device, '1gbe')

        self.reset_parameters()

        #Check versions
        self._check_versions()

        # Configure 2x4 mode
        self.daq.setString(f'/{self.device}/system/awg/channelgrouping', 'groups_of_2')

        # Setup AWG module
        self.awg_module = daq.awgModule()
        self.awg_module.set('device', device)
        self.awg_module.set('index', awg_index)
        # Execute commands
        self.awg_module.execute()

    def reset_parameters(self):
        #add a space for constants
        self.constants = SimpleNamespace()
        self.registers = SimpleNamespace()

    #Verify that all the components have the right version
    def _check_versions(self):
        ziPython_ver = version.parse(zi.__version__)
        
        labone_ver_raw = self.daq.getInt('/zi/about/revision')
        labone_ver = version.parse(f'{labone_ver_raw//10**7}.{labone_ver_raw//10**5%100}.{labone_ver_raw%10**5}')

        hdawg_fw_ver = version.parse(str(self.daq.getInt(f'/{self.device:s}/system/fwrevision')))

        if ziPython_ver < HDAWG_Core.ziPython_min:
            raise Exception(f"The zhinst package needs to be updated to version {HDAWG_Core.ziPython_min.public:s} or above!\n"
                            f"You can do that with 'pip install -U zhinst=={HDAWG_Core.ziPython_min.public:s}'")
        if labone_ver < HDAWG_Core.labone_min:
            raise Exception(f"The LabOne installation needs to be updated to version {HDAWG_Core.labone_min.public:s} or above!\n"
                            "Please follow the instructions in the User Manual to perform the upgrade")
        if hdawg_fw_ver < HDAWG_Core.hdawg_fw_min:
            raise Exception(f"The FW on device {self.device:s} needs to be updated!\n"
                            "Please follow the instructions in the User Manual to perform the FW upgrade")

    def config(self, program, ct=None, waves=None):
        """Configure the device
        
        Parameters
        ----------
        program: str
            The seqc program
        ct: dict
            The Command Table, as dictionary
        waves: list
            List of the waveforms
        """
        
        ## Configure AWG
        # Stop AWG
        self.daq.setInt(f'/{self.device}/awgs/{self.awg_index}/enable', 0)

        # Send sequence
        self.compile_seqc(program)

        # Run AWG program only once
        self.daq.setInt(f'/{self.device}/awgs/{self.awg_index}/single', 1)

        # Enable channel outputs
        self.daq.setInt(f'/{self.device}/sigouts/{self.awg_index*2}/on', 1)
        self.daq.setInt(f'/{self.device}/sigouts/{self.awg_index*2+1}/on', 1)

        #send AWG waves
        if waves is not None:
            for i, wave in enumerate(waves):
                wave_raw = zhinst.utils.convert_awg_waveform(wave[0],wave[1])
                self.daq.setVector(f'/{self.device}/awgs/{self.awg_index}/waveform/waves/{i}', wave_raw)

        #load the command table
        if ct is not None:
            self.load_ct(ct)

    def load_ct(self, ct):
        """Load a command table
        
        Parameters
        ----------
        ct: dict
            The Command Table, as dictonary
        """
        
        #Create CT  and send it to the device
        ct_all = {'header':{'version':'0.2'}, 'table':ct}
        node = f"/{self.device:s}/awgs/{self.awg_index}/commandtable/data"
        self.daq.setVector(node, json.dumps(ct_all))

    def _setUserRegs(self):
        #if no registers are defined, skip this phase
        if not bool(self.registers.__dict__):
            return

        set_cmd = []
        for i,value in enumerate(self.registers.__dict__.values()):
            node = f'/{self.device:s}/awgs/{self.awg_index:d}/userregs/{i:d}'
            set_cmd.append((node, value))
        
        self.daq.set(set_cmd)

    def setHold(self, hold):
        self.daq.setInt(f'/{self.device:s}/awgs/{self.awg_index}/outputs/0/hold', hold)
        self.daq.setInt(f'/{self.device:s}/awgs/{self.awg_index}/outputs/1/hold', hold)

    def oscControl(self, enable):
        self.daq.setInt(f'/{self.device:s}/system/awg/oscillatorcontrol', enable)

    def frequency(self, freq, osc=0):
        self.daq.setDouble(f'/{self.device:s}/oscs/{osc}/freq', freq)

    def modulation(self, mode):
        self.daq.set(f'/{self.device:s}/awgs/{self.awg_index}/outputs/0/modulation/mode', mode)
        self.daq.set(f'/{self.device:s}/awgs/{self.awg_index}/outputs/1/modulation/mode', mode)

    def run(self, block=True):
        self._setUserRegs()
        node = f'/{self.device:s}/awgs/{self.awg_index}/enable'
        self.daq.syncSetInt(node, 1)
        if block:
            while(self.daq.getInt(node) == 1):
                time.sleep(0.005)

    def _const2seqc(self):
        """Transform the constants into
        valid seqc code
        """
        
        #if no constants are defined, return an empty string
        if not bool(self.constants.__dict__):
            return ""

        seqc = "//Constants definition\n"
            
        for name, value in self.constants.__dict__.items():
            seqc += f"const {name:s} = {value};\n"

        seqc += '\n'
        return seqc

    def _regs2seqc(self):
        """Transform the registers into
        valid seqc code
        """

        #if no registers are defined, return an empty string
        if not bool(self.registers.__dict__):
            return ""
        
        seqc = "//User registers\n"
            
        for i,name in enumerate(self.registers.__dict__.keys()):
            seqc += f"var {name:s} = getUserReg({i:d});\n"

        seqc += '\n'
        return seqc

    def compile_seqc(self, program):
        """Compile and send a sequence to the device
        
        Parameters
        ----------
        program: str
            The seqc program
        """

        #Add constants definitions
        constants = self._const2seqc()
        registers = self._regs2seqc()
        program = constants + registers + program

        # Compile program
        self.awg_module.set('compiler/sourcestring', program)
        while self.awg_module.getInt('compiler/status') == -1:
            time.sleep(0.1)
        if self.awg_module.getInt('compiler/status') == 1:
            msg = "Failed to compile program. Error message:\n"
            msg += self.awg_module.getString("compiler/statusstring")
            raise Exception(msg)
        if self.awg_module.getInt('compiler/status') == 2:
            msg = "Compilation successful with warnings. Warning message:\n"
            msg += self.awg_module.getString("compiler/statusstring")
            raise Warning(msg)

        # Upload program
        while (self.awg_module.getDouble('progress') < 1.0) and (self.awg_module.getInt('elf/status') != 1):
            time.sleep(0.5)
        if self.awg_module.getInt('elf/status') == 1:
            raise Exception("Failed to upload program.")
