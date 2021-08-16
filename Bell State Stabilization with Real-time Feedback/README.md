## Bell State Stabilization of Superconducting Qubits with Real-time Feedback

The contents of this folder belong to the blog post [Bell State Stabilization of Superconducting Qubits with Real-time Feedback](https://blogs.zhinst.com/bahadir/2021/08/18/bell-state-stabilization-of-superconducting-qubits-with-real-time-feedback/).

The Juyter notebook [Bell_State_Stabilization_w_Realtime_Feedback.ipynb](Bell_State_Stabilization_w_Realtime_Feedback.ipynb) describes how to use the Zurich Instruments QCCS to realize Bell state stabilization. It requires a PQSC for coordination and feedback processing, a UHFQA for readout and two HDAWGs for control.

The file [experimental_setup.svg](experimental_setup.svg) describe the experimental setup and its wiring. The file [channel_assignments.svg](channel_assignments.svg) indicates the assignments of the devices for certain tasks such as qubit control and readout. The file [PQSC_lut_decoder_diagram.svg](PQSC_lut_decoder_diagram.svg) shows the Block diagram of the PQSC LUT decoder.

Please refer to the [PQSC User manual](https://docs.zhinst.com) for more details.
